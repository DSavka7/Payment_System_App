"""
Сервісний шар для управління банківськими рахунками.
"""
from typing import List

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import AccountNotFound
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate
from app.repositories.account_repository import AccountRepository

logger = get_logger(__name__)


class AccountService:
    """Сервіс для управління банківськими рахунками."""

    def __init__(self, repo: AccountRepository):
        self.repo = repo

    async def create_account(self, account: AccountCreate) -> AccountResponse:
        """Створює новий банківський рахунок."""
        account_in_db = await self.repo.create(account)
        return AccountResponse.model_validate(account_in_db)

    async def get_account(self, account_id: str) -> AccountResponse:
        """Повертає рахунок за ID."""
        account = await self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)

    async def get_user_accounts(self, user_id: str) -> List[AccountResponse]:
        """Повертає всі рахунки користувача."""
        accounts = await self.repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(acc) for acc in accounts]

    async def update_account(self, account_id: str, update_data: AccountUpdate) -> AccountResponse:
        """Оновлює статус або баланс рахунку."""
        account = await self.repo.update(account_id, update_data)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)


def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    """DI: повертає екземпляр AccountRepository."""
    return AccountRepository(db.accounts)


def get_account_service(repo: AccountRepository = Depends(get_account_repository)) -> AccountService:
    """DI: повертає екземпляр AccountService."""
    return AccountService(repo)