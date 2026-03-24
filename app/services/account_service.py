from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.repositories.account_repository import AccountRepository
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate
from app.core.exceptions import AccountNotFound
from app.db.database import get_db


class AccountService:
    def __init__(self, repo: AccountRepository):
        self.repo = repo

    async def create_account(self, account: AccountCreate) -> AccountResponse:
        """Створення нового рахунку"""
        account_in_db = await self.repo.create(account)
        return AccountResponse.model_validate(account_in_db)

    async def get_account(self, account_id: str) -> AccountResponse:
        """Отримання рахунку за ID"""
        account = await self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)

    async def get_user_accounts(self, user_id: str) -> List[AccountResponse]:
        """Отримання всіх рахунків користувача"""
        accounts = await self.repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(acc) for acc in accounts]

    async def update_account(self, account_id: str, update_data: AccountUpdate) -> AccountResponse:
        """Оновлення рахунку (статус, баланс)"""
        account = await self.repo.update(account_id, update_data)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)


# Dependency Injection
def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return AccountRepository(db.accounts)


def get_account_service(repo: AccountRepository = Depends(get_account_repository)):
    return AccountService(repo)