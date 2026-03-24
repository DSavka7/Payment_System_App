from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.repositories.request_repository import RequestRepository
from app.models.request_models import RequestCreate, RequestResponse, RequestUpdate
from app.core.exceptions import RequestNotFound
from app.db.database import get_db


class RequestService:
    def __init__(self, repo: RequestRepository):
        self.repo = repo

    async def create_request(self, request: RequestCreate) -> RequestResponse:
        """Створення нового запиту (наприклад, на розблокування рахунку)"""
        req_in_db = await self.repo.create(request)
        return RequestResponse.model_validate(req_in_db)

    async def get_request(self, request_id: str) -> RequestResponse:
        """Отримання запиту за ID"""
        req = await self.repo.get_by_id(request_id)
        if not req:
            raise RequestNotFound()
        return RequestResponse.model_validate(req)

    async def get_user_requests(self, user_id: str) -> List[RequestResponse]:
        """Отримання всіх запитів користувача"""
        requests = await self.repo.get_by_user(user_id)
        return [RequestResponse.model_validate(r) for r in requests]

    async def update_request_status(self, request_id: str, update: RequestUpdate) -> RequestResponse:
        """Оновлення статусу запиту адміністратором"""
        req = await self.repo.update_status(request_id, update)
        if not req:
            raise RequestNotFound()
        return RequestResponse.model_validate(req)


# Dependency Injection
def get_request_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return RequestRepository(db.requests)


def get_request_service(repo: RequestRepository = Depends(get_request_repository)):
    return RequestService(repo)