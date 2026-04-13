
from typing import List

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import TransactionNotFound
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.transaction_models import (
    TransactionCreate,
    TransactionResponse,
    PaginatedTransactions,
)
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


class TransactionService:

    def __init__(self, repo: TransactionRepository) -> None:
        self.repo = repo

    async def create_transaction(
        self, transaction: TransactionCreate
    ) -> TransactionResponse:
        """Створює нову транзакцію."""
        tx = await self.repo.create(transaction)
        return TransactionResponse.model_validate(tx.model_dump())

    async def get_transaction(self, tx_id: str) -> TransactionResponse:
        """Повертає транзакцію за ID."""
        tx = await self.repo.get_by_id(tx_id)
        if not tx:
            raise TransactionNotFound()
        return TransactionResponse.model_validate(tx.model_dump())

    async def get_account_transactions(
        self,
        account_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedTransactions:
        items, total = await self.repo.get_by_account(account_id, limit, offset)
        return PaginatedTransactions(
            items=[TransactionResponse.model_validate(t.model_dump()) for t in items],
            total=total,
            limit=limit,
            offset=offset,
        )


# ── Dependency Injection ───────────────────────────────────────────────────────

def get_transaction_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TransactionRepository:
    return TransactionRepository(db.transactions)


def get_transaction_service(
    repo: TransactionRepository = Depends(get_transaction_repository),
) -> TransactionService:
    return TransactionService(repo)