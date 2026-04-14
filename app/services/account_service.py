import random
from typing import List

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.constants import ACCOUNT_STATUS_ACTIVE
from app.core.exceptions import (
    AccountBlocked,
    AccountNotFound,
    CurrencyMismatch,
    InsufficientFunds,
    SelfTransferNotAllowed,
)
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.account_models import (
    AccountCreate,
    AccountInDB,
    AccountResponse,
    AccountUpdate,
    TransferRequest,
)
from app.models.transaction_models import TransactionCreate, TransactionResponse
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


def _to_response(acc: AccountInDB) -> AccountResponse:
    return AccountResponse(
        id=acc.id,
        user_id=acc.user_id,
        card_number=acc.card_number,
        card_number_full=acc.card_number_full,
        currency=acc.currency,
        balance=acc.balance,
        status=acc.status,
        created_at=acc.created_at,
    )


class AccountService:
    def __init__(
        self,
        account_repo: AccountRepository,
        tx_repo: TransactionRepository,
    ) -> None:
        self.account_repo = account_repo
        self.tx_repo = tx_repo

    async def create_account(self, account: AccountCreate) -> AccountResponse:
        """Создаёт счёт с автоматически сгенерированным номером карты"""
        card_number_full = await self._generate_unique_card_number()

        acc = await self.account_repo.create_with_card_number(
            account=account,
            card_number_full=card_number_full,
        )
        logger.info(f"Счёт успешно создан | ID: {acc.id} | Валюта: {account.currency}")
        return _to_response(acc)

    async def _generate_unique_card_number(self) -> str:
        """Генерирует уникальный 16-значный номер карты"""
        for attempt in range(15):
            card = ''.join(str(random.randint(1 if i == 0 else 0, 9)) for i in range(16))
            if not await self.account_repo.exists_by_card_number(card):
                return card


        raise Exception("Не вдалося згенерувати унікальний номер карти. Спробуйте ще раз.")

    async def get_account(self, account_id: str) -> AccountResponse:
        acc = await self.account_repo.get_by_id(account_id)
        if not acc:
            raise AccountNotFound()
        return _to_response(acc)

    async def get_user_accounts(self, user_id: str) -> List[AccountResponse]:
        accounts = await self.account_repo.get_by_user_id(user_id)
        return [_to_response(a) for a in accounts]

    async def update_account(self, account_id: str, update_data: AccountUpdate) -> AccountResponse:
        acc = await self.account_repo.update(account_id, update_data)
        if not acc:
            raise AccountNotFound()
        return _to_response(acc)

    async def delete_account(self, account_id: str) -> dict:
        if not await self.account_repo.delete(account_id):
            raise AccountNotFound()
        return {"detail": "Рахунок видалено / Account deleted"}

    async def transfer(self, transfer: TransferRequest) -> TransactionResponse:
        from_account = await self.account_repo.get_by_id(transfer.from_account_id)
        if not from_account:
            raise AccountNotFound()

        to_account = await self.account_repo.get_by_card_number(transfer.to_card_number)
        if not to_account:
            raise AccountNotFound()

        if from_account.id == to_account.id:
            raise SelfTransferNotAllowed()

        if from_account.status != ACCOUNT_STATUS_ACTIVE or to_account.status != ACCOUNT_STATUS_ACTIVE:
            raise AccountBlocked()

        if from_account.currency != to_account.currency:
            raise CurrencyMismatch()

        if from_account.balance < transfer.amount:
            raise InsufficientFunds()

        await self.account_repo.update_balance(
            from_account.id, round(from_account.balance - transfer.amount, 2)
        )
        await self.account_repo.update_balance(
            to_account.id, round(to_account.balance + transfer.amount, 2)
        )

        tx = await self.tx_repo.create(
            TransactionCreate(
                from_account_id=from_account.id,
                to_account_id=to_account.id,
                amount=transfer.amount,
                currency=from_account.currency,
                type="transfer",
                category="transfer",
                description=transfer.description,
                is_income=False,
            )
        )

        logger.info(
            "Переказ: %s → %s | %.2f %s",
            from_account.id, transfer.to_card_number[-4:], transfer.amount, from_account.currency
        )
        return TransactionResponse.model_validate(tx.model_dump())


# ── Dependency Injection ─────────────────────────────────────────────────────
def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    return AccountRepository(db.accounts)


def get_transaction_repository_for_account(db: AsyncIOMotorDatabase = Depends(get_db)) -> TransactionRepository:
    return TransactionRepository(db.transactions)


def get_account_service(
    account_repo: AccountRepository = Depends(get_account_repository),
    tx_repo: TransactionRepository = Depends(get_transaction_repository_for_account),
) -> AccountService:
    return AccountService(account_repo, tx_repo)