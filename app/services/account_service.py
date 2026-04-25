"""
Сервісний шар для управління банківськими рахунками.
"""
from typing import List
from datetime import datetime

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import (
    AccountNotFound, AccountBlocked, InsufficientFunds,
    CurrencyMismatch, SelfTransferNotAllowed
)
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.account_models import (
    AccountCreate, AccountResponse, AccountUpdate,
    TransferRequest, TransactionResponse
)
from app.models.transaction_models import TransactionCreate
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


class AccountService:
    """Сервіс для управління банківськими рахунками."""

    def __init__(self, repo: AccountRepository, tx_repo: TransactionRepository = None):
        self.repo = repo
        self.tx_repo = tx_repo

    async def create_account(self, account: AccountCreate) -> AccountResponse:
        """Створює новий банківський рахунок."""
        account_in_db = await self.repo.create(account)
        return AccountResponse.model_validate(account_in_db.model_dump())

    async def get_account(self, account_id: str) -> AccountResponse:
        """Повертає рахунок за ID."""
        account = await self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account.model_dump())

    async def get_user_accounts(self, user_id: str) -> List[AccountResponse]:
        """Повертає всі рахунки користувача."""
        accounts = await self.repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(acc.model_dump()) for acc in accounts]

    async def update_account(self, account_id: str, update_data: AccountUpdate) -> AccountResponse:
        """Оновлює статус або баланс рахунку."""
        account = await self.repo.update(account_id, update_data)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account.model_dump())

    async def delete_account(self, account_id: str) -> None:
        """Видаляє рахунок."""
        deleted = await self.repo.delete(account_id)
        if not deleted:
            raise AccountNotFound()

    async def transfer(self, transfer_data: TransferRequest) -> TransactionResponse:
        """
        Виконує переказ коштів між рахунками за номером картки отримувача.

        Args:
            transfer_data: Дані переказу (from_account_id, to_card_number, amount).

        Raises:
            AccountNotFound: Якщо рахунок відправника або отримувача не знайдено.
            AccountBlocked: Якщо один з рахунків заблоковано.
            InsufficientFunds: Якщо недостатньо коштів.
            CurrencyMismatch: Якщо валюти рахунків не збігаються.
            SelfTransferNotAllowed: Якщо переказ на той самий рахунок.
        """
        # Отримуємо рахунок відправника
        from_acc = await self.repo.get_by_id(transfer_data.from_account_id)
        if not from_acc:
            raise AccountNotFound()

        # Знаходимо рахунок отримувача за номером картки
        to_acc = await self.repo.get_by_card_number(transfer_data.to_card_number)
        if not to_acc:
            raise AccountNotFound()

        # Перевірки
        if from_acc.id == to_acc.id:
            raise SelfTransferNotAllowed()

        if from_acc.status != "active":
            raise AccountBlocked()

        if to_acc.status != "active":
            raise AccountBlocked()

        if from_acc.currency != to_acc.currency:
            raise CurrencyMismatch()

        if from_acc.balance < transfer_data.amount:
            raise InsufficientFunds()

        # Оновлюємо баланси
        await self.repo.update_balance(from_acc.id, from_acc.balance - transfer_data.amount)
        await self.repo.update_balance(to_acc.id, to_acc.balance + transfer_data.amount)

        logger.info(
            "Переказ %.2f %s з %s на %s",
            transfer_data.amount, from_acc.currency, from_acc.id, to_acc.id
        )

        # Створюємо запис транзакції якщо є репозиторій
        now = datetime.utcnow()
        tx_id = "tx_" + str(int(now.timestamp() * 1000))

        if self.tx_repo:
            tx = await self.tx_repo.create(TransactionCreate(
                from_account_id=from_acc.id,
                to_account_id=to_acc.id,
                amount=transfer_data.amount,
                currency=from_acc.currency,
                type="transfer",
                category="transfer",
                description=transfer_data.description,
                is_income=False,
            ))
            tx_id = tx.id

        return TransactionResponse(
            id=tx_id,
            from_account_id=from_acc.id,
            to_account_id=to_acc.id,
            amount=transfer_data.amount,
            currency=from_acc.currency,
            status="success",
            description=transfer_data.description,
            created_at=now,
        )


def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    """DI: повертає екземпляр AccountRepository."""
    return AccountRepository(db.accounts)


def get_transaction_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TransactionRepository:
    """DI: повертає екземпляр TransactionRepository."""
    return TransactionRepository(db.transactions)


def get_account_service(
    repo: AccountRepository = Depends(get_account_repository),
    tx_repo: TransactionRepository = Depends(get_transaction_repository),
) -> AccountService:
    """DI: повертає екземпляр AccountService."""
    return AccountService(repo, tx_repo)