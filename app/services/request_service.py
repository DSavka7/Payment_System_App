
import logging
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.repositories.request_repository import RequestRepository
from app.repositories.account_repository import AccountRepository
from app.models.request_models import (
    RequestCreate,
    RequestResponse,
    RequestUpdate,
    PaginatedRequests,
)
from app.models.account_models import AccountUpdate
from app.core.exceptions import (
    RequestNotFound,
    AccountNotFound,
    AccountAlreadyActive,
    InvalidAccountOwnership,
    DuplicateRequest,
    UnblockRequiresRequest,
)
from app.db.database import get_db

logger = logging.getLogger(__name__)


class RequestService:
    """
    Сервісний шар для операцій з запитами на зміну стану рахунків.

    Патерн Command: при схваленні запиту автоматично виконується дія на рахунку.
    Патерн Observer: логування кожної зміни статусу.
    """

    def __init__(self, req_repo: RequestRepository, acc_repo: AccountRepository):
        self.req_repo = req_repo
        self.acc_repo = acc_repo

    async def create_request(
        self, user_id: str, request: RequestCreate
    ) -> RequestResponse:
        """
        Створює запит від користувача до адміністратора.

        Перевірки:
          - Рахунок існує та належить користувачу
          - Для UNBLOCK — рахунок дійсно заблоковано
          - Немає вже активного pending-запиту того ж типу для цього рахунку

        Raises:
            AccountNotFound, InvalidAccountOwnership,
            AccountAlreadyActive (UNBLOCK на активний рахунок),
            DuplicateRequest.
        """
        account = await self.acc_repo.get_by_id(request.account_id)
        if not account:
            raise AccountNotFound()
        if account.user_id != user_id:
            raise InvalidAccountOwnership()

        # UNBLOCK-запит можна подати лише для заблокованого рахунку
        if request.type == "UNBLOCK" and account.status == "active":
            raise AccountAlreadyActive()

        if await self.req_repo.has_pending(request.account_id, request.type):
            raise DuplicateRequest()

        req = await self.req_repo.create(user_id, request)
        logger.info(
            "Запит %s від користувача %s для рахунку %s",
            request.type, user_id, request.account_id,
        )
        return RequestResponse.model_validate(req.model_dump())

    async def get_request(
        self, request_id: str, user_id: str, role: str
    ) -> RequestResponse:
        """
        Повертає запит за ID.
        USER бачить лише свої запити; ADMIN — будь-які.
        """
        req = await self.req_repo.get_by_id(request_id)
        if not req:
            raise RequestNotFound()
        # Не розкриваємо існування чужих запитів звичайному користувачу
        if role != "ADMIN" and req.user_id != user_id:
            raise RequestNotFound()
        return RequestResponse.model_validate(req.model_dump())

    async def get_my_requests(
        self, user_id: str, limit: int, offset: int
    ) -> PaginatedRequests:
        """Пагінований список запитів поточного користувача."""
        requests, total = await self.req_repo.get_by_user(
            user_id, limit=limit, offset=offset
        )
        return PaginatedRequests(
            items=[RequestResponse.model_validate(r.model_dump()) for r in requests],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    async def get_all_requests(
        self, status: Optional[str], limit: int, offset: int
    ) -> PaginatedRequests:
        """Адмін: пагінований список всіх запитів з опціональним фільтром по статусу."""
        requests, total = await self.req_repo.get_all(
            status=status, limit=limit, offset=offset
        )
        return PaginatedRequests(
            items=[RequestResponse.model_validate(r.model_dump()) for r in requests],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    async def update_request_status(
        self, request_id: str, update: RequestUpdate, admin_id: str
    ) -> RequestResponse:
        """
        Адмін схвалює або відхиляє запит.
        При схваленні автоматично виконує відповідну дію на рахунку (патерн Command).
        """
        req = await self.req_repo.get_by_id(request_id)
        if not req:
            raise RequestNotFound()

        updated_req = await self.req_repo.update_status(request_id, update)
        if not updated_req:
            raise RequestNotFound()

        if update.status == "approved":
            await self._apply_approved_action(updated_req)

        logger.info(
            "Адмін %s → запит %s: %s", admin_id, request_id, update.status
        )
        return RequestResponse.model_validate(updated_req.model_dump())

    async def _apply_approved_action(self, req) -> None:
        """
        Патерн Command: виконує відповідну дію залежно від типу запиту.

        UNBLOCK      → розблокувати рахунок
        LIMIT_CHANGE → встановити новий добовий ліміт
        """
        if req.type == "UNBLOCK":
            await self.acc_repo.update(req.account_id, AccountUpdate(status="active"))
            logger.info("Рахунок %s розблоковано за запитом UNBLOCK", req.account_id)

        elif req.type == "LIMIT_CHANGE" and req.requested_limit:
            await self.acc_repo.update(
                req.account_id, AccountUpdate(daily_limit=req.requested_limit)
            )
            logger.info(
                "Ліміт рахунку %s змінено на %.2f за запитом",
                req.account_id, req.requested_limit,
            )


# ─── Dependency Injection ──────────────────────────────────────────────────────

def get_request_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RequestRepository:
    return RequestRepository(db.requests)


def get_account_repo_for_requests(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AccountRepository:
    return AccountRepository(db.accounts)


def get_request_service(
    req_repo: RequestRepository = Depends(get_request_repository),
    acc_repo: AccountRepository = Depends(get_account_repo_for_requests),
) -> RequestService:
    return RequestService(req_repo, acc_repo)