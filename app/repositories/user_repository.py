from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional
from datetime import datetime

from app.models.user_models import UserCreate, UserInDB, UserUpdate
from app.core.security import hash_password
from app.core.exceptions import UserAlreadyExists


class UserRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, user: UserCreate) -> UserInDB:
        """Створення нового користувача"""

        existing = await self.collection.find_one({"email": user.email})
        if existing:
            raise UserAlreadyExists()

        user_dict = user.model_dump(exclude={"password"})
        user_dict["password_hash"] = hash_password(user.password)
        user_dict["status"] = "active"
        user_dict["created_at"] = datetime.utcnow()


        result = await self.collection.insert_one(user_dict)


        user_dict["_id"] = result.inserted_id
        user_dict["id"] = str(result.inserted_id)

        return UserInDB.model_validate(user_dict)

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        doc = await self.collection.find_one({"_id": ObjectId(user_id)})
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
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=True
        )
        if not result:
            return None
        result["id"] = str(result.pop("_id"))
        return UserInDB.model_validate(result)

    async def delete(self, user_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0