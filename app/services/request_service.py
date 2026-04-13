
from typing import List

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import RequestNotFound
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.request_models import (
    RequestCreate,
    RequestResponse,
    RequestUpdate,
)
from app.repositories.request_repository import RequestRepository

logger = get_logger(__name__)


class RequestService:

    def __init__(self, repo: RequestRepository) -> None:
        self.repo = repo

    async def create_request(self, request: RequestCreate) -> RequestResponse:
        """Створює новий запит."""
        req = await self.repo.create(request)
        logger.info("Запит створено: %s type=%s", req.id, req.type)
        return RequestResponse.model_validate(req.model_dump())

    async def get_request(self, request_id: str) -> RequestResponse:
        """Повертає запит за ID."""
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise RequestNotFound()
        return RequestResponse.model_validate(req.model_dump())

    async def get_user_requests(self, user_id: str) -> List[RequestResponse]:
        """Повертає всі запити користувача."""
        requests = await self.repo.get_by_user(user_id)
        return [RequestResponse.model_validate(r.model_dump()) for r in requests]

    async def update_request_status(
        self, request_id: str, update: RequestUpdate
    ) -> RequestResponse:
        """Оновлює статус запиту (тільки для адміністраторів)."""
        req = await self.repo.update_status(request_id, update)
        if not req:
            raise RequestNotFound()
        logger.info("Статус запиту %s змінено на %s", request_id, update.status)
        return RequestResponse.model_validate(req.model_dump())


# ── Dependency Injection ───────────────────────────────────────────────────────

def get_request_repository(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RequestRepository:
    return RequestRepository(db.requests)


def get_request_service(
    repo: RequestRepository = Depends(get_request_repository),
) -> RequestService:
    return RequestService(repo)