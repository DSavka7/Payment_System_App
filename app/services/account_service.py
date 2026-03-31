import logging
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict

from app.repositories.account_repository import AccountRepository
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate
from app.core.exceptions import (
    AccountNotFound,
    InvalidAccountOwnership,
    AccountBlocked,
    AccountAlreadyBlocked,
    AccountAlreadyActive,
)
from app.db.database import get_db

logger = logging.getLogger(__name__)


class AccountService:
    """Сервісний шар для операцій над банківськими рахунками."""

    def __init__(self, repo: AccountRepository):
        self.repo = repo

    async def create_account(self, user_id: str, account: AccountCreate) -> AccountResponse:
        account_in_db = await self.repo.create(user_id, account)
        logger.info("Користувач %s створив рахунок %s", user_id, account_in_db.id)
        return AccountResponse.model_validate(account_in_db.model_dump())

    async def get_account(
        self, account_id: str, requester_id: str, requester_role: str
    ) -> AccountResponse:
        account = await self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        if requester_role != "ADMIN" and account.user_id != requester_id:
            raise InvalidAccountOwnership()
        return AccountResponse.model_validate(account.model_dump())

    async def get_my_accounts(self, user_id: str) -> List[AccountResponse]:
        """Повертає всі рахунки поточного авторизованого користувача."""
        accounts = await self.repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(a.model_dump()) for a in accounts]

    async def get_user_accounts_admin(self, user_id: str) -> List[AccountResponse]:
        """Адмін отримує рахунки будь-якого користувача за user_id."""
        accounts = await self.repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(a.model_dump()) for a in accounts]

    async def get_all_accounts(self, limit: int, offset: int) -> Dict:
        """Адмін: пагінований список усіх рахунків."""
        accounts = await self.repo.get_all(limit=limit, offset=offset)
        total = await self.repo.count()
        return {
            "items": [AccountResponse.model_validate(a.model_dump()) for a in accounts],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
        }

    # ─── Блокування користувачем (self-block) ─────────────────────────────────

    async def self_block_account(self, account_id: str, user_id: str) -> AccountResponse:

        account = await self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        if account.user_id != user_id:
            raise InvalidAccountOwnership()
        if account.status == "blocked":
            raise AccountAlreadyBlocked()

        updated = await self.repo.update(account_id, AccountUpdate(status="blocked"))
        logger.info(
            "Користувач %s самостійно заблокував рахунок %s", user_id, account_id
        )
        return AccountResponse.model_validate(updated.model_dump())

    # ─── Управління адміністратором ────────────────────────────────────────────

    async def block_account(self, account_id: str) -> AccountResponse:

        account = await self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        if account.status == "blocked":
            raise AccountAlreadyBlocked()

        updated = await self.repo.update(account_id, AccountUpdate(status="blocked"))
        logger.info("Адмін заблокував рахунок %s", account_id)
        return AccountResponse.model_validate(updated.model_dump())

    async def unblock_account(self, account_id: str) -> AccountResponse:

        account = await self.repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        if account.status == "active":
            raise AccountAlreadyActive()

        updated = await self.repo.update(account_id, AccountUpdate(status="active"))
        logger.info("Адмін розблокував рахунок %s", account_id)
        return AccountResponse.model_validate(updated.model_dump())

    async def update_account(
        self, account_id: str, update_data: AccountUpdate
    ) -> AccountResponse:
        """Адмін оновлює параметри рахунку (ліміт, баланс)."""
        account = await self.repo.update(account_id, update_data)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account.model_dump())


# ─── Dependency Injection ──────────────────────────────────────────────────────

def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    return AccountRepository(db.accounts)


def get_account_service(
    repo: AccountRepository = Depends(get_account_repository),
) -> AccountService:
    return AccountService(repo)