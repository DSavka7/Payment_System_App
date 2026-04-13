from bson import ObjectId
from datetime import datetime
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.core.logging_config import get_logger
from app.models.request_models import RequestCreate, RequestInDB, RequestUpdate

logger = get_logger(__name__)


class RequestRepository:
    """Репозиторій для CRUD-операцій над колекцією requests."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    @staticmethod
    def _doc_to_model(doc: dict) -> RequestInDB:
        """Перетворює MongoDB-документ на Pydantic-модель."""
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

    async def create(self, request: RequestCreate) -> RequestInDB:
        """Створює новий запит."""
        req_dict = request.model_dump()
        req_dict["user_id"] = ObjectId(req_dict["user_id"])
        req_dict["account_id"] = ObjectId(req_dict["account_id"])
        req_dict["status"] = "pending"
        req_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(req_dict)
        req_dict["_id"] = result.inserted_id
        return self._doc_to_model(req_dict)

    async def get_by_id(self, request_id: str) -> Optional[RequestInDB]:
        """Повертає запит за ID або None."""
        doc = await self.collection.find_one({"_id": ObjectId(request_id)})
        return self._doc_to_model(doc) if doc else None

    async def get_by_user(self, user_id: str) -> List[RequestInDB]:
        """Повертає всі запити користувача."""
        cursor = self.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return [self._doc_to_model(d) for d in docs]

    async def update_status(self, request_id: str, update: RequestUpdate) -> Optional[RequestInDB]:
        """Оновлює статус запиту адміністратором."""
        update_dict = update.model_dump(exclude_unset=True)
        if update.status in ("approved", "rejected"):
            update_dict["resolved_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(request_id)},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER,
        )
        return self._doc_to_model(result) if result else None