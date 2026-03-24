from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.repositories.transaction_repository import TransactionRepository
from app.models.transaction_models import TransactionCreate, TransactionResponse
from app.core.exceptions import TransactionNotFound
from app.db.database import get_db


class TransactionService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    async def create_transaction(self, transaction: TransactionCreate) -> TransactionResponse:
        """Створення нової транзакції"""
        tx_in_db = await self.repo.create(transaction)
        return TransactionResponse.model_validate(tx_in_db)

    async def get_transaction(self, tx_id: str) -> TransactionResponse:
        """Отримання транзакції за ID"""
        tx = await self.repo.get_by_id(tx_id)
        if not tx:
            raise TransactionNotFound()
        return TransactionResponse.model_validate(tx)

    async def get_account_transactions(self, account_id: str, limit: int = 50) -> List[TransactionResponse]:
        """Отримання історії транзакцій по рахунку"""
        transactions = await self.repo.get_by_account(account_id, limit)
        return [TransactionResponse.model_validate(t) for t in transactions]


# Dependency Injection
def get_transaction_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return TransactionRepository(db.transactions)


def get_transaction_service(repo: TransactionRepository = Depends(get_transaction_repository)):
    return TransactionService(repo)