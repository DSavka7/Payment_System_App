from bson import ObjectId
from datetime import datetime
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.core.logging_config import get_logger
from app.models.account_models import AccountCreate, AccountInDB, AccountUpdate

logger = get_logger(__name__)


class AccountRepository:

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    @staticmethod
    def _doc_to_model(doc: dict) -> AccountInDB:
        return AccountInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            card_number_full=doc["card_number_full"],
            currency=doc["currency"],
            balance=doc["balance"],
            status=doc["status"],
            created_at=doc["created_at"],
        )

    async def create_with_card_number(self, account: AccountCreate, card_number_full: str) -> AccountInDB:
        """Создаёт новый счёт с указанным номером карты"""
        doc = {
            "user_id": ObjectId(account.user_id),
            "card_number_full": card_number_full,
            "currency": account.currency,
            "balance": account.balance,
            "status": "active",
            "created_at": datetime.utcnow(),
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info("Рахунок створено | номер: %s... | валюта: %s", card_number_full[:6], account.currency)
        return self._doc_to_model(doc)

    async def get_by_id(self, account_id: str) -> Optional[AccountInDB]:
        doc = await self.collection.find_one({"_id": ObjectId(account_id)})
        return self._doc_to_model(doc) if doc else None

    async def get_by_card_number(self, card_number_full: str) -> Optional[AccountInDB]:
        doc = await self.collection.find_one({"card_number_full": card_number_full})
        return self._doc_to_model(doc) if doc else None

    async def get_by_user_id(self, user_id: str) -> List[AccountInDB]:
        cursor = self.collection.find({"user_id": ObjectId(user_id)})
        docs = await cursor.to_list(length=100)
        return [self._doc_to_model(d) for d in docs]

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

    async def delete(self, account_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(account_id)})
        return result.deleted_count > 0

    async def exists_by_card_number(self, card_number_full: str) -> bool:
        count = await self.collection.count_documents({"card_number_full": card_number_full})
        return count > 0