
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List
from datetime import datetime
from pymongo import ReturnDocument

from app.models.account_models import AccountCreate, AccountInDB, AccountUpdate

logger = logging.getLogger(__name__)


class AccountRepository:

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def _doc_to_model(self, doc: dict) -> AccountInDB:
        return AccountInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            card_number=doc["card_number"],
            currency=doc["currency"],
            balance=doc["balance"],
            status=doc["status"],
            daily_limit=doc.get("daily_limit"),
            created_at=doc["created_at"],
        )

    async def create(self, user_id: str, account: AccountCreate) -> AccountInDB:

        account_dict = account.model_dump()
        account_dict["user_id"] = ObjectId(user_id)
        account_dict["status"] = "active"
        account_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(account_dict)
        account_dict["_id"] = result.inserted_id
        account_dict["user_id"] = ObjectId(user_id)

        logger.info("Створено рахунок %s для користувача %s", result.inserted_id, user_id)
        return self._doc_to_model(account_dict)

    async def get_by_id(self, account_id: str) -> Optional[AccountInDB]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(account_id)})
        except Exception:
            return None
        return self._doc_to_model(doc) if doc else None

    async def get_by_user_id(self, user_id: str) -> List[AccountInDB]:
        cursor = self.collection.find({"user_id": ObjectId(user_id)})
        docs = await cursor.to_list(length=100)
        return [self._doc_to_model(doc) for doc in docs]

    async def update(self, account_id: str, update_data: AccountUpdate) -> Optional[AccountInDB]:
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=ReturnDocument.AFTER,
        )
        return self._doc_to_model(result) if result else None

    async def update_balance(self, account_id: str, new_balance: float) -> Optional[AccountInDB]:
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$set": {"balance": new_balance}},
            return_document=ReturnDocument.AFTER,
        )
        return self._doc_to_model(result) if result else None

    async def get_all(self, limit: int = 20, offset: int = 0) -> List[AccountInDB]:
        cursor = self.collection.find().skip(offset).limit(limit).sort("created_at", -1)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs]

    async def count(self) -> int:
        return await self.collection.count_documents({})

    async def delete(self, account_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(account_id)})
        return result.deleted_count > 0