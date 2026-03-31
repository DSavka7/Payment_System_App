
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List, Tuple
from datetime import datetime
from pymongo import ReturnDocument

from app.models.request_models import RequestCreate, RequestInDB, RequestUpdate

logger = logging.getLogger(__name__)


class RequestRepository:

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def _doc_to_model(self, doc: dict) -> RequestInDB:
        """Конвертує MongoDB-документ у Pydantic-модель."""
        return RequestInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            account_id=str(doc["account_id"]),
            type=doc["type"],
            message=doc["message"],
            status=doc["status"],
            admin_comment=doc.get("admin_comment"),
            requested_limit=doc.get("requested_limit"),
            created_at=doc["created_at"],
            resolved_at=doc.get("resolved_at"),
        )

    async def has_pending(self, account_id: str, request_type: str) -> bool:
        """Перевіряє, чи є активний (pending) запит для рахунку."""
        doc = await self.collection.find_one({
            "account_id": ObjectId(account_id),
            "type": request_type,
            "status": "pending",
        })
        return doc is not None

    async def create(self, user_id: str, request: RequestCreate) -> RequestInDB:
        """Створює новий запит від користувача."""
        req_dict = request.model_dump()
        req_dict["user_id"] = ObjectId(user_id)
        req_dict["account_id"] = ObjectId(req_dict["account_id"])
        req_dict["status"] = "pending"
        req_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(req_dict)
        req_dict["_id"] = result.inserted_id

        logger.info("Новий запит %s від користувача %s", result.inserted_id, user_id)
        return self._doc_to_model(req_dict)

    async def get_by_id(self, request_id: str) -> Optional[RequestInDB]:
        """Повертає запит за ID або None."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(request_id)})
        except Exception:
            return None
        return self._doc_to_model(doc) if doc else None

    async def get_by_user(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[RequestInDB], int]:
        """Повертає запити конкретного користувача з пагінацією."""
        query = {"user_id": ObjectId(user_id)}
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs], total

    async def get_all(
        self, status: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> Tuple[List[RequestInDB], int]:
        """Повертає всі запити з пагінацією та фільтром по статусу (для адміна)."""
        query = {"status": status} if status else {}
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs], total

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
        if result:
            logger.info("Запит %s → статус '%s'", request_id, update.status)
        return self._doc_to_model(result) if result else None