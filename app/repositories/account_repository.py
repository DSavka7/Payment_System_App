"""
Репозиторій для роботи з колекцією accounts у MongoDB.
"""
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from typing import Optional, List
from datetime import datetime

from app.core.exceptions import InvalidObjectId
from app.core.logging_config import get_logger
from app.models.account_models import AccountCreate, AccountInDB, AccountUpdate

logger = get_logger(__name__)


class AccountRepository:
    """Репозиторій для CRUD-операцій з банківськими рахунками."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, account: AccountCreate) -> AccountInDB:
        """Створює новий рахунок у базі даних."""
        account_dict = account.model_dump()
        account_dict["user_id"] = ObjectId(account_dict["user_id"])
        account_dict["status"] = "active"
        account_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(account_dict)
        logger.info("Створено рахунок id=%s для user_id=%s", result.inserted_id, account.user_id)

        return AccountInDB(
            id=str(result.inserted_id),
            user_id=str(account_dict["user_id"]),
            card_number=account_dict["card_number"],
            currency=account_dict["currency"],
            balance=account_dict["balance"],
            status=account_dict["status"],
            created_at=account_dict["created_at"],
        )

    async def get_by_id(self, account_id: str) -> Optional[AccountInDB]:
        """Знаходить рахунок за ID."""
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        doc = await self.collection.find_one({"_id": oid})
        if not doc:
            return None

        return AccountInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            card_number=doc["card_number"],
            currency=doc["currency"],
            balance=doc["balance"],
            status=doc["status"],
            created_at=doc["created_at"],
        )

    async def get_by_user_id(self, user_id: str) -> List[AccountInDB]:
        """Повертає всі рахунки користувача."""
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        cursor = self.collection.find({"user_id": oid})
        docs = await cursor.to_list(length=100)

        return [
            AccountInDB(
                id=str(doc["_id"]),
                user_id=str(doc["user_id"]),
                card_number=doc["card_number"],
                currency=doc["currency"],
                balance=doc["balance"],
                status=doc["status"],
                created_at=doc["created_at"],
            )
            for doc in docs
        ]

    async def update(self, account_id: str, update_data: AccountUpdate) -> Optional[AccountInDB]:
        """Оновлює дані рахунку."""
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None

        logger.info("Оновлено рахунок id=%s", account_id)
        return AccountInDB(
            id=str(result["_id"]),
            user_id=str(result["user_id"]),
            card_number=result["card_number"],
            currency=result["currency"],
            balance=result["balance"],
            status=result["status"],
            created_at=result["created_at"],
        )

    async def delete(self, account_id: str) -> bool:
        """Видаляє рахунок."""
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0