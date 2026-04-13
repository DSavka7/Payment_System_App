import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.account_service import AccountService
from app.models.account_models import AccountCreate, AccountUpdate, TransferRequest
from app.models.account_models import AccountInDB
from app.core.exceptions import (
    AccountNotFound,
    AccountBlocked,
    CurrencyMismatch,
    InsufficientFunds,
    SelfTransferNotAllowed,
)


def make_account(
    account_id: str = "aaa000000000000000000001",
    user_id: str = "bbb000000000000000000001",
    currency: str = "UAH",
    balance: float = 1000.0,
    status: str = "active",
) -> AccountInDB:
    return AccountInDB(
        id=account_id,
        user_id=user_id,
        card_number="1234 **** **** 5678",
        currency=currency,
        balance=balance,
        status=status,
        created_at=datetime.utcnow(),
    )


def make_service(account_repo=None, tx_repo=None) -> AccountService:
    if account_repo is None:
        account_repo = MagicMock()
    if tx_repo is None:
        tx_repo = MagicMock()
    return AccountService(account_repo, tx_repo)


@pytest.mark.asyncio
class TestTransfer:

    async def test_transfer_success(self):
        """Успішний переказ списує/зараховує кошти і створює транзакцію."""
        from_acc = make_account("acc001", balance=500.0, currency="UAH")
        to_acc = make_account("acc002", balance=100.0, currency="UAH")

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(side_effect=[from_acc, to_acc])
        account_repo.update_balance = AsyncMock(return_value=None)

        tx_repo = MagicMock()
        from app.models.transaction_models import TransactionInDB
        tx_repo.create = AsyncMock(return_value=TransactionInDB(
            id="tx001",
            from_account_id="acc001",
            to_account_id="acc002",
            amount=200.0,
            currency="UAH",
            type="transfer",
            category="transfer",
            status="success",
            is_income=False,
            created_at=datetime.utcnow(),
        ))

        service = make_service(account_repo, tx_repo)
        result = await service.transfer(TransferRequest(
            from_account_id="acc001",
            to_account_id="acc002",
            amount=200.0,
        ))

        assert result.amount == 200.0
        assert result.currency == "UAH"
        account_repo.update_balance.assert_any_call("acc001", 300.0)
        account_repo.update_balance.assert_any_call("acc002", 300.0)

    async def test_transfer_self_not_allowed(self):
        """Переказ на той самий рахунок заборонено."""
        from_acc = make_account("acc001")
        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(side_effect=[from_acc, from_acc])

        service = make_service(account_repo)
        with pytest.raises(SelfTransferNotAllowed):
            await service.transfer(TransferRequest(
                from_account_id="acc001",
                to_account_id="acc001",
                amount=100.0,
            ))

    async def test_transfer_insufficient_funds(self):
        """Переказ більше балансу піднімає InsufficientFunds."""
        from_acc = make_account("acc001", balance=50.0)
        to_acc = make_account("acc002", balance=0.0)

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(side_effect=[from_acc, to_acc])

        service = make_service(account_repo)
        with pytest.raises(InsufficientFunds):
            await service.transfer(TransferRequest(
                from_account_id="acc001",
                to_account_id="acc002",
                amount=200.0,
            ))

    async def test_transfer_currency_mismatch(self):
        """Переказ між рахунками різних валют не дозволяється."""
        from_acc = make_account("acc001", currency="UAH")
        to_acc = make_account("acc002", currency="USD")

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(side_effect=[from_acc, to_acc])

        service = make_service(account_repo)
        with pytest.raises(CurrencyMismatch):
            await service.transfer(TransferRequest(
                from_account_id="acc001",
                to_account_id="acc002",
                amount=100.0,
            ))

    async def test_transfer_blocked_sender(self):
        """Переказ із заблокованого рахунку не дозволяється."""
        from_acc = make_account("acc001", status="blocked")
        to_acc = make_account("acc002")

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(side_effect=[from_acc, to_acc])

        service = make_service(account_repo)
        with pytest.raises(AccountBlocked):
            await service.transfer(TransferRequest(
                from_account_id="acc001",
                to_account_id="acc002",
                amount=100.0,
            ))

    async def test_transfer_blocked_receiver(self):
        """Переказ на заблокований рахунок не дозволяється."""
        from_acc = make_account("acc001", balance=500.0)
        to_acc = make_account("acc002", status="blocked")

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(side_effect=[from_acc, to_acc])

        service = make_service(account_repo)
        with pytest.raises(AccountBlocked):
            await service.transfer(TransferRequest(
                from_account_id="acc001",
                to_account_id="acc002",
                amount=100.0,
            ))

    async def test_transfer_from_account_not_found(self):
        """Якщо рахунок-відправник не існує — AccountNotFound."""
        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(return_value=None)

        service = make_service(account_repo)
        with pytest.raises(AccountNotFound):
            await service.transfer(TransferRequest(
                from_account_id="acc001",
                to_account_id="acc002",
                amount=100.0,
            ))

    async def test_transfer_to_account_not_found(self):
        """Якщо рахунок-отримувач не існує — AccountNotFound."""
        from_acc = make_account("acc001")
        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(side_effect=[from_acc, None])

        service = make_service(account_repo)
        with pytest.raises(AccountNotFound):
            await service.transfer(TransferRequest(
                from_account_id="acc001",
                to_account_id="acc002",
                amount=100.0,
            ))


@pytest.mark.asyncio
class TestAccountCRUD:

    async def test_get_account_not_found(self):
        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(return_value=None)

        service = make_service(account_repo)
        with pytest.raises(AccountNotFound):
            await service.get_account("nonexistent_id")

    async def test_get_account_success(self):
        """get_account повертає AccountResponse."""
        acc = make_account()
        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(return_value=acc)

        service = make_service(account_repo)
        result = await service.get_account(acc.id)
        assert result.id == acc.id
        assert result.currency == "UAH"

    async def test_create_account(self):
        """create_account повертає AccountResponse."""
        created = make_account()
        account_repo = MagicMock()
        account_repo.create = AsyncMock(return_value=created)

        service = make_service(account_repo)
        result = await service.create_account(AccountCreate(
            user_id="bbb000000000000000000001",
            card_number="1234 **** **** 5678",
            currency="UAH",
            balance=0.0,
        ))
        assert result.currency == "UAH"
        assert result.status == "active"