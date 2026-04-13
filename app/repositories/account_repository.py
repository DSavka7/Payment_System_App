from bson import ObjectId
from datetime import datetime
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.core.logging_config import get_logger
from app.models.account_models import AccountCreate, AccountInDB, AccountUpdate

logger = get_logger(__name__)


class AccountRepository:
    """Репозиторій для CRUD-операцій над колекцією accounts."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _doc_to_model(doc: dict) -> AccountInDB:
        """Перетворює MongoDB-документ на Pydantic-модель."""
        return AccountInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            card_number=doc["card_number"],
            currency=doc["currency"],
            balance=doc["balance"],
            status=doc["status"],
            created_at=doc["created_at"],
        )

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, account: AccountCreate) -> AccountInDB:
        """Створює новий банківський рахунок."""
        account_dict = account.model_dump()
        account_dict["user_id"] = ObjectId(account_dict["user_id"])
        account_dict["status"] = "active"
        account_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(account_dict)
        account_dict["_id"] = result.inserted_id

        logger.info("Рахунок створено: %s", str(result.inserted_id))
        return self._doc_to_model(account_dict)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, account_id: str) -> Optional[AccountInDB]:
        """Повертає рахунок за ID або None."""
        doc = await self.collection.find_one({"_id": ObjectId(account_id)})
        return self._doc_to_model(doc) if doc else None

    async def get_by_user_id(self, user_id: str) -> List[AccountInDB]:
        """Повертає всі рахунки користувача."""
        cursor = self.collection.find({"user_id": ObjectId(user_id)})
        docs = await cursor.to_list(length=100)
        return [self._doc_to_model(d) for d in docs]

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, account_id: str, update_data: AccountUpdate) -> Optional[AccountInDB]:
        """Оновлює поля рахунку і повертає оновлену модель."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None
        logger.info("Рахунок оновлено: %s", account_id)
        return self._doc_to_model(result)

    async def update_balance(self, account_id: str, new_balance: float) -> Optional[AccountInDB]:
        """Оновлює баланс рахунку атомарно."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$set": {"balance": new_balance}},
            return_document=ReturnDocument.AFTER,
        )
        return self._doc_to_model(result) if result else None

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, account_id: str) -> bool:
        """Видаляє рахунок. Повертає True якщо успішно."""
        result = await self.collection.delete_one({"_id": ObjectId(account_id)})
        return result.deleted_count > 0