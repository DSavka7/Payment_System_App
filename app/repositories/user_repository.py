
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List
from datetime import datetime

from app.models.user_models import UserCreate, UserInDB, UserUpdate
from app.core.security import hash_password
from app.core.exceptions import UserAlreadyExists

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, user: UserCreate) -> UserInDB:
        existing = await self.collection.find_one({"email": user.email})
        if existing:
            raise UserAlreadyExists()

        user_dict = user.model_dump(exclude={"password"})
        user_dict["password_hash"] = hash_password(user.password)
        user_dict["role"] = "USER"
        user_dict["status"] = "active"
        user_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(user_dict)
        user_dict["id"] = str(result.inserted_id)

        logger.info("Створено нового користувача: %s", user.email)
        return UserInDB.model_validate(user_dict)

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return UserInDB.model_validate(doc)

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        doc = await self.collection.find_one({"email": email})
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return UserInDB.model_validate(doc)

    async def update(self, user_id: str, update_data: UserUpdate) -> Optional[UserInDB]:
        from pymongo import ReturnDocument
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None
        result["id"] = str(result.pop("_id"))
        return UserInDB.model_validate(result)

    async def get_all(self, limit: int = 20, offset: int = 0) -> List[UserInDB]:
        cursor = self.collection.find().skip(offset).limit(limit).sort("created_at", -1)
        docs = await cursor.to_list(length=limit)
        result = []
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            result.append(UserInDB.model_validate(doc))
        return result

    async def count(self) -> int:
        return await self.collection.count_documents({})

    async def delete(self, user_id: str) -> bool:

        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0