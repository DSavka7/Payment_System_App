"""
Репозиторій для роботи з колекцією requests у MongoDB.
"""
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from typing import Optional, List
from datetime import datetime

from app.core.exceptions import InvalidObjectId
from app.core.logging_config import get_logger
from app.models.request_models import RequestCreate, RequestInDB, RequestUpdate

logger = get_logger(__name__)


class RequestRepository:
    """Репозиторій для CRUD-операцій із запитами користувачів."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, request: RequestCreate) -> RequestInDB:
        """Створює новий запит у базі даних."""
        try:
            user_oid = ObjectId(request.user_id)
            account_oid = ObjectId(request.account_id)
        except InvalidId as exc:
            raise InvalidObjectId(str(exc))

        req_dict = request.model_dump()
        req_dict["user_id"] = user_oid
        req_dict["account_id"] = account_oid
        req_dict["status"] = "pending"
        req_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(req_dict)
        logger.info(
            "Створено запит id=%s, тип=%s від user_id=%s",
            result.inserted_id,
            request.type,
            request.user_id,
        )

        return RequestInDB(
            id=str(result.inserted_id),
            user_id=str(user_oid),
            account_id=str(account_oid),
            type=req_dict["type"],
            message=req_dict["message"],
            status=req_dict["status"],
            admin_comment=None,
            created_at=req_dict["created_at"],
            resolved_at=None,
        )

    async def get_by_id(self, request_id: str) -> Optional[RequestInDB]:
        """Знаходить запит за ID."""
        try:
            oid = ObjectId(request_id)
        except InvalidId:
            raise InvalidObjectId("request_id")

        doc = await self.collection.find_one({"_id": oid})
        if not doc:
            return None
        return self._doc_to_model(doc)

    async def get_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[RequestInDB]:
        """
        Повертає запити користувача з підтримкою пагінації.

        Args:
            user_id: ObjectId користувача.
            limit: Максимальна кількість записів.
            offset: Зміщення для пагінації.
        """
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        cursor = (
            self.collection.find({"user_id": oid})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs]

    async def update_status(self, request_id: str, update: RequestUpdate) -> Optional[RequestInDB]:
        """
        Оновлює статус запиту адміністратором.

        Args:
            request_id: ObjectId запиту.
            update: Новий статус та коментар адміністратора.
        """
        try:
            oid = ObjectId(request_id)
        except InvalidId:
            raise InvalidObjectId("request_id")

        update_dict = update.model_dump(exclude_unset=True)
        if update.status in ("approved", "rejected"):
            update_dict["resolved_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None

        logger.info("Запит id=%s оновлено до статусу '%s'", request_id, update.status)
        return self._doc_to_model(result)

    @staticmethod
    def _doc_to_model(doc: dict) -> RequestInDB:
        """Конвертує документ MongoDB у Pydantic-модель."""
        return RequestInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            account_id=str(doc["account_id"]),
            type=doc["type"],
            message=doc["message"],
            status=doc["status"],
            admin_comment=doc.get("admin_comment"),
            created_at=doc["created_at"],
            resolved_at=doc.get("resolved_at"),
        )