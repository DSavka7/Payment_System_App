"""
Сервісний шар для управління запитами на операції з рахунками.
"""
from typing import List, Optional

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.constants import (
    REQUEST_STATUS_APPROVED,
    REQUEST_TYPE_BLOCK,
    REQUEST_TYPE_UNBLOCK,
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_BLOCKED,
)
from app.core.exceptions import RequestNotFound
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.account_models import AccountUpdate
from app.models.request_models import RequestCreate, RequestResponse, RequestUpdate
from app.repositories.account_repository import AccountRepository
from app.repositories.request_repository import RequestRepository

logger = get_logger(__name__)


class RequestService:


    def __init__(self, repo: RequestRepository, account_repo: AccountRepository):
        self.repo = repo
        self.account_repo = account_repo

    async def create_request(self, request: RequestCreate) -> RequestResponse:
        """Створює новий запит від користувача."""
        req_in_db = await self.repo.create(request)
        logger.info(
            "Створено запит id=%s, тип=%s для account_id=%s",
            req_in_db.id, req_in_db.type, req_in_db.account_id,
        )
        return RequestResponse.model_validate(req_in_db)

    async def get_request(self, request_id: str) -> RequestResponse:
        """Повертає запит за ID."""
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise RequestNotFound()
        return RequestResponse.model_validate(req)

    async def get_user_requests(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[RequestResponse]:
        """Повертає всі запити конкретного користувача з пагінацією."""
        requests = await self.repo.get_by_user(user_id, limit=limit, offset=offset)
        return [RequestResponse.model_validate(r) for r in requests]

    async def get_all_requests(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RequestResponse]:

        requests = await self.repo.get_all(
            status_filter=status_filter, limit=limit, offset=offset
        )
        return [RequestResponse.model_validate(r) for r in requests]

    async def update_request_status(
        self, request_id: str, update: RequestUpdate
    ) -> RequestResponse:

        req = await self.repo.update_status(request_id, update)
        if not req:
            raise RequestNotFound()

        if update.status == REQUEST_STATUS_APPROVED:
            await self._apply_approved_action(req.type, req.account_id, request_id)

        logger.info("Адмін оновив статус запиту id=%s → %s", request_id, update.status)
        return RequestResponse.model_validate(req)

    async def _apply_approved_action(
        self, request_type: str, account_id: str, request_id: str
    ) -> None:
        """
        Виконує автоматичну дію над рахунком при схваленні запиту.

        BLOCK   → status = 'blocked'
        UNBLOCK → status = 'active'
        """
        if request_type == REQUEST_TYPE_BLOCK:
            new_status = ACCOUNT_STATUS_BLOCKED
        elif request_type == REQUEST_TYPE_UNBLOCK:
            new_status = ACCOUNT_STATUS_ACTIVE
        else:
            return

        updated = await self.account_repo.update(account_id, AccountUpdate(status=new_status))
        if updated:
            logger.info(
                "Автоматична зміна статусу рахунку id=%s → %s (запит id=%s схвалено)",
                account_id, new_status, request_id,
            )
        else:
            logger.warning(
                "Не вдалося оновити статус рахунку id=%s після схвалення запиту id=%s",
                account_id, request_id,
            )


# ── Dependency Injection ──────────────────────────────────────────────────────

def get_request_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> RequestRepository:
    """DI: повертає екземпляр RequestRepository."""
    return RequestRepository(db.requests)


def get_account_repository_for_requests(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AccountRepository:
    """DI: повертає AccountRepository для використання в RequestService."""
    return AccountRepository(db.accounts)


def get_request_service(
    repo: RequestRepository = Depends(get_request_repository),
    account_repo: AccountRepository = Depends(get_account_repository_for_requests),
) -> RequestService:
    """DI: повертає екземпляр RequestService."""
    return RequestService(repo, account_repo)
