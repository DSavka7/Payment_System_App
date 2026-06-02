"""
Репозиторій для роботи з колекцією users у MongoDB.
Реалізує CRUD-операції без використання ODM-фреймворків.
"""
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Optional, List
from datetime import datetime

from app.core.exceptions import UserAlreadyExists, InvalidObjectId
from app.core.logging_config import get_logger
from app.core.security import hash_password
from app.models.user_models import UserCreate, UserInDB, UserUpdate

logger = get_logger(__name__)


class UserRepository:
    """
    Репозиторій для операцій з користувачами у MongoDB.
    Інкапсулює всю логіку доступу до колекції users.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, user: UserCreate) -> UserInDB:
        """
        Створює нового користувача у базі даних.

        Raises:
            UserAlreadyExists: Якщо email вже зайнятий.
        """
        existing = await self.collection.find_one({"email": user.email})
        if existing:
            logger.warning("Спроба реєстрації з існуючим email: %s", user.email)
            raise UserAlreadyExists()

        user_dict = user.model_dump(exclude={"password"})
        user_dict["password_hash"] = hash_password(user.password)
        user_dict["status"] = "active"
        user_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(user_dict)
        user_dict["id"] = str(result.inserted_id)

        logger.info("Створено нового користувача з id=%s", user_dict["id"])
        return UserInDB.model_validate(user_dict)

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Знаходить користувача за його MongoDB ObjectId."""
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        doc = await self.collection.find_one({"_id": oid})
        if not doc:
            return None

        doc["id"] = str(doc.pop("_id"))
        return UserInDB.model_validate(doc)

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Знаходить користувача за email."""
        doc = await self.collection.find_one({"email": email})
        if not doc:
            return None

        doc["id"] = str(doc.pop("_id"))
        return UserInDB.model_validate(doc)

    async def get_all(self, limit: int = 50, offset: int = 0) -> List[UserInDB]:
        """
        Повертає список усіх користувачів з підтримкою пагінації.

        Args:
            limit: Максимальна кількість записів.
            offset: Зміщення (для пагінації).
        """
        cursor = self.collection.find().sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)

        result = []
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
            result.append(UserInDB.model_validate(doc))

        return result

    async def update(self, user_id: str, update_data: UserUpdate) -> Optional[UserInDB]:
        """Оновлює дані користувача."""
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        # Виключаємо службові поля — вони не зберігаються в колекції напряму
        payload = update_data.model_dump(
            exclude_unset=True,
            exclude={"password", "current_password"},
        )

        # Якщо сервіс передав password_hash — зберігаємо його
        if hasattr(update_data, "password_hash") and update_data.password_hash:
            payload["password_hash"] = update_data.password_hash

        if not payload:
            # Нічого оновлювати — повертаємо поточний документ
            doc = await self.collection.find_one({"_id": oid})
            if not doc:
                return None
            doc["id"] = str(doc.pop("_id"))
            return UserInDB.model_validate(doc)

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": payload},
            return_document=True,
        )
        if not result:
            return None

        result["id"] = str(result.pop("_id"))
        logger.info("Оновлено користувача id=%s", user_id)
        return UserInDB.model_validate(result)

    async def delete(self, user_id: str) -> bool:
        """Видаляє користувача з бази даних."""
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        result = await self.collection.delete_one({"_id": oid})
        deleted = result.deleted_count > 0
        if deleted:
            logger.info("Видалено користувача id=%s", user_id)
        return deleted
