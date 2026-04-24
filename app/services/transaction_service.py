"""
Сервісний шар для управління транзакціями.
"""
from typing import List

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import TransactionNotFound
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.transaction_models import TransactionCreate, TransactionResponse
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


class TransactionService:
    """Сервіс для управління транзакціями."""

    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    async def create_transaction(self, transaction: TransactionCreate) -> TransactionResponse:
        """Створює нову транзакцію."""
        tx_in_db = await self.repo.create(transaction)
        return TransactionResponse.model_validate(tx_in_db)

    async def get_transaction(self, tx_id: str) -> TransactionResponse:
        """Повертає транзакцію за ID."""
        tx = await self.repo.get_by_id(tx_id)
        if not tx:
            raise TransactionNotFound()
        return TransactionResponse.model_validate(tx)

    async def get_account_transactions(
        self,
        account_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TransactionResponse]:
        """
        Повертає транзакції рахунку з пагінацією.

        Args:
            account_id: ObjectId рахунку.
            limit: Максимальна кількість записів.
            offset: Зміщення для пагінації.
        """
        transactions = await self.repo.get_by_account(account_id, limit=limit, offset=offset)
        return [TransactionResponse.model_validate(t) for t in transactions]


def get_transaction_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TransactionRepository:
    """DI: повертає екземпляр TransactionRepository."""
    return TransactionRepository(db.transactions)


def get_transaction_service(
    repo: TransactionRepository = Depends(get_transaction_repository),
) -> TransactionService:
    """DI: повертає екземпляр TransactionService."""
    return TransactionService(repo)