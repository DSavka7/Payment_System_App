from bson import ObjectId
from datetime import datetime
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.exceptions import UserAlreadyExists
from app.core.logging_config import get_logger
from app.core.security import hash_password
from app.models.user_models import UserCreate, UserInDB, UserUpdate

logger = get_logger(__name__)


class UserRepository:
    """Репозиторій для CRUD-операцій над колекцією users."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _doc_to_model(doc: dict) -> UserInDB:
        """Перетворює MongoDB-документ на Pydantic-модель."""
        doc["id"] = str(doc.pop("_id"))
        return UserInDB.model_validate(doc)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, user: UserCreate) -> UserInDB:
        """
        Створює нового користувача.

        Raises:
            UserAlreadyExists: якщо email вже зареєстровано.
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
        user_dict["_id"] = result.inserted_id

        logger.info("Користувача створено: %s", str(result.inserted_id))
        return self._doc_to_model(user_dict)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Повертає користувача за ObjectId або None."""
        doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        return self._doc_to_model(doc) if doc else None

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Повертає користувача за email або None."""
        doc = await self.collection.find_one({"email": email})
        return self._doc_to_model(doc) if doc else None

    async def get_all(self, limit: int = 50, offset: int = 0) -> List[UserInDB]:
        """Повертає список усіх користувачів з пагінацією."""
        cursor = self.collection.find().skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(d) for d in docs]

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, user_id: str, update_data: UserUpdate) -> Optional[UserInDB]:
        """Оновлює дані користувача і повертає оновлену модель."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=True,
        )
        if not result:
            return None
        logger.info("Користувача оновлено: %s", user_id)
        return self._doc_to_model(result)

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, user_id: str) -> bool:
        """Видаляє користувача. Повертає True якщо успішно."""
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        deleted = result.deleted_count > 0
        if deleted:
            logger.info("Користувача видалено: %s", user_id)
        return deleted