
import logging
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict

from app.repositories.transaction_repository import TransactionRepository
from app.repositories.account_repository import AccountRepository
from app.models.transaction_models import (
    TransactionCreate,
    TransactionResponse,
    TransferCreate,
    PaginatedTransactions,
)
from app.models.account_models import AccountUpdate
from app.core.exceptions import (
    TransactionNotFound,
    AccountNotFound,
    AccountBlocked,
    InsufficientFunds,
    InvalidAccountOwnership,
    TransferToSameAccount,
    CurrencyMismatch,
)
from app.db.database import get_db

logger = logging.getLogger(__name__)


class TransactionService:
    """Сервісний шар для операцій з транзакціями."""

    def __init__(self, tx_repo: TransactionRepository, acc_repo: AccountRepository):
        self.tx_repo = tx_repo
        self.acc_repo = acc_repo

    async def make_transfer(
        self, user_id: str, from_account_id: str, transfer: TransferCreate
    ) -> TransactionResponse:

        if from_account_id == transfer.to_account_id:
            raise TransferToSameAccount()

        # Перевіряємо рахунок відправника
        from_account = await self.acc_repo.get_by_id(from_account_id)
        if not from_account:
            raise AccountNotFound()
        if from_account.user_id != user_id:
            raise InvalidAccountOwnership()
        if from_account.status == "blocked":
            raise AccountBlocked()

        # Перевіряємо рахунок отримувача
        to_account = await self.acc_repo.get_by_id(transfer.to_account_id)
        if not to_account:
            raise AccountNotFound()
        if to_account.status == "blocked":
            raise AccountBlocked()

        # Перевіряємо валюти
        if from_account.currency != to_account.currency:
            raise CurrencyMismatch()

        # Перевіряємо баланс
        if from_account.balance < transfer.amount:
            raise InsufficientFunds()

        # Перевіряємо добовий ліміт (якщо встановлено)
        if from_account.daily_limit and transfer.amount > from_account.daily_limit:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Сума перевищує добовий ліміт рахунку ({from_account.daily_limit} {from_account.currency})",
            )

        # Виконуємо переказ — оновлюємо баланси
        new_from_balance = round(from_account.balance - transfer.amount, 2)
        new_to_balance = round(to_account.balance + transfer.amount, 2)

        await self.acc_repo.update_balance(from_account_id, new_from_balance)
        await self.acc_repo.update_balance(transfer.to_account_id, new_to_balance)

        # Зберігаємо транзакцію
        tx = await self.tx_repo.create(
            TransactionCreate(
                from_account_id=from_account_id,
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
            "Переказ %.2f %s: %s → %s",
            transfer.amount, from_account.currency, from_account_id, transfer.to_account_id,
        )
        return TransactionResponse.model_validate(tx.model_dump())

    async def get_transaction(
        self, tx_id: str, user_id: str, role: str
    ) -> TransactionResponse:
        tx = await self.tx_repo.get_by_id(tx_id)
        if not tx:
            raise TransactionNotFound()

        if role != "ADMIN":
            # Перевіряємо, що транзакція пов'язана з рахунком користувача
            user_accounts = await self.acc_repo.get_by_user_id(user_id)
            account_ids = {acc.id for acc in user_accounts}
            if tx.from_account_id not in account_ids and tx.to_account_id not in account_ids:
                raise InvalidAccountOwnership()

        return TransactionResponse.model_validate(tx.model_dump())

    async def get_account_transactions(
        self,
        account_id: str,
        user_id: str,
        role: str,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedTransactions:

        if role != "ADMIN":
            account = await self.acc_repo.get_by_id(account_id)
            if not account:
                raise AccountNotFound()
            if account.user_id != user_id:
                raise InvalidAccountOwnership()

        transactions, total = await self.tx_repo.get_by_account(
            account_id, limit=limit, offset=offset
        )
        return PaginatedTransactions(
            items=[TransactionResponse.model_validate(t.model_dump()) for t in transactions],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    async def get_all_transactions(self, limit: int, offset: int) -> PaginatedTransactions:
        """Адмін: пагінований список усіх транзакцій."""
        transactions, total = await self.tx_repo.get_all(limit=limit, offset=offset)
        return PaginatedTransactions(
            items=[TransactionResponse.model_validate(t.model_dump()) for t in transactions],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )


# ─── Dependency Injection ──────────────────────────────────────────────────────

def get_transaction_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TransactionRepository:
    return TransactionRepository(db.transactions)


def get_account_repository_for_tx(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    return AccountRepository(db.accounts)


def get_transaction_service(
    tx_repo: TransactionRepository = Depends(get_transaction_repository),
    acc_repo: AccountRepository = Depends(get_account_repository_for_tx),
) -> TransactionService:
    return TransactionService(tx_repo, acc_repo)