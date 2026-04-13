
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
    AccountResponse,
    AccountUpdate,
    TransferRequest,
)
from app.models.transaction_models import TransactionCreate, TransactionResponse
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


class AccountService:

    def __init__(
        self,
        account_repo: AccountRepository,
        tx_repo: TransactionRepository,
    ) -> None:
        self.account_repo = account_repo
        self.tx_repo = tx_repo

    async def create_account(self, account: AccountCreate) -> AccountResponse:
        """Створює новий банківський рахунок."""
        account_in_db = await self.account_repo.create(account)
        return AccountResponse.model_validate(account_in_db.model_dump())

    async def get_account(self, account_id: str) -> AccountResponse:
        """Повертає рахунок за ID."""
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account.model_dump())

    async def get_user_accounts(self, user_id: str) -> List[AccountResponse]:
        """Повертає всі рахунки користувача."""
        accounts = await self.account_repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(a.model_dump()) for a in accounts]

    async def update_account(
        self, account_id: str, update_data: AccountUpdate
    ) -> AccountResponse:
        account = await self.account_repo.update(account_id, update_data)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account.model_dump())

    async def delete_account(self, account_id: str) -> dict:
        deleted = await self.account_repo.delete(account_id)
        if not deleted:
            raise AccountNotFound()
        return {"detail": "Рахунок видалено / Account deleted"}

    async def transfer(
        self, transfer: TransferRequest
    ) -> TransactionResponse:
        # ── Завантаження рахунків ────────────────────────────────────────────
        from_account = await self.account_repo.get_by_id(transfer.from_account_id)
        if not from_account:
            raise AccountNotFound()

        to_account = await self.account_repo.get_by_id(transfer.to_account_id)
        if not to_account:
            raise AccountNotFound()

        # ── Бізнес-перевірки ─────────────────────────────────────────────────
        if transfer.from_account_id == transfer.to_account_id:
            raise SelfTransferNotAllowed()

        if from_account.status != ACCOUNT_STATUS_ACTIVE:
            raise AccountBlocked()

        if to_account.status != ACCOUNT_STATUS_ACTIVE:
            raise AccountBlocked()

        if from_account.currency != to_account.currency:
            raise CurrencyMismatch()

        if from_account.balance < transfer.amount:
            raise InsufficientFunds()

        # ── Оновлення балансів ────────────────────────────────────────────────
        await self.account_repo.update_balance(
            transfer.from_account_id,
            round(from_account.balance - transfer.amount, 2),
        )
        await self.account_repo.update_balance(
            transfer.to_account_id,
            round(to_account.balance + transfer.amount, 2),
        )

        # ── Запис транзакцій ──────────────────────────────────────────────────
        tx = await self.tx_repo.create(
            TransactionCreate(
                from_account_id=transfer.from_account_id,
                to_account_id=transfer.to_account_id,
                amount=transfer.amount,
                currency=from_account.currency,
                type="transfer",
                category="transfer",
                description=transfer.description,
                is_income=False,
            )
        )

        logger.info(
            "Переказ виконано: %s → %s | %.2f %s",
            transfer.from_account_id,
            transfer.to_account_id,
            transfer.amount,
            from_account.currency,
        )
        return TransactionResponse.model_validate(tx.model_dump())


# ── Dependency Injection ───────────────────────────────────────────────────────

def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    return AccountRepository(db.accounts)


def get_transaction_repository_for_account(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TransactionRepository:
    return TransactionRepository(db.transactions)


def get_account_service(
    account_repo: AccountRepository = Depends(get_account_repository),
    tx_repo: TransactionRepository = Depends(get_transaction_repository_for_account),
) -> AccountService:
    return AccountService(account_repo, tx_repo)