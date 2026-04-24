"""
Сервісний шар для управління запитами на операції з рахунками.
"""
from typing import List

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import RequestNotFound
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.request_models import RequestCreate, RequestResponse, RequestUpdate
from app.repositories.request_repository import RequestRepository

logger = get_logger(__name__)


class RequestService:
    """Сервіс для управління запитами на операції з рахунками."""

    def __init__(self, repo: RequestRepository):
        self.repo = repo

    async def create_request(self, request: RequestCreate) -> RequestResponse:
        """Створює новий запит від користувача."""
        req_in_db = await self.repo.create(request)
        return RequestResponse.model_validate(req_in_db)

    async def get_request(self, request_id: str) -> RequestResponse:
        """Повертає запит за ID."""
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise RequestNotFound()
        return RequestResponse.model_validate(req)

    async def get_user_requests(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RequestResponse]:
        """
        Повертає всі запити користувача з пагінацією.

        Args:
            user_id: ObjectId користувача.
            limit: Максимальна кількість записів.
            offset: Зміщення для пагінації.
        """
        requests = await self.repo.get_by_user(user_id, limit=limit, offset=offset)
        return [RequestResponse.model_validate(r) for r in requests]

    async def update_request_status(
        self,
        request_id: str,
        update: RequestUpdate,
    ) -> RequestResponse:
        """Оновлює статус запиту (для адміністратора)."""
        req = await self.repo.update_status(request_id, update)
        if not req:
            raise RequestNotFound()
        return RequestResponse.model_validate(req)


def get_request_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> RequestRepository:
    """DI: повертає екземпляр RequestRepository."""
    return RequestRepository(db.requests)


def get_request_service(repo: RequestRepository = Depends(get_request_repository)) -> RequestService:
    """DI: повертає екземпляр RequestService."""
    return RequestService(repo)