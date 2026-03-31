
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List, Tuple
from datetime import datetime

from app.models.transaction_models import TransactionCreate, TransactionInDB

logger = logging.getLogger(__name__)


class TransactionRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def _doc_to_model(self, doc: dict) -> TransactionInDB:
        """Конвертує MongoDB-документ у Pydantic-модель."""
        return TransactionInDB(
            id=str(doc["_id"]),
            from_account_id=str(doc["from_account_id"]),
            to_account_id=str(doc["to_account_id"]) if doc.get("to_account_id") else None,
            amount=doc["amount"],
            currency=doc["currency"],
            type=doc["type"],
            category=doc["category"],
            merchant_name=doc.get("merchant_name"),
            description=doc.get("description"),
            status=doc["status"],
            is_income=doc.get("is_income", False),
            created_at=doc["created_at"],
        )

    async def create(self, transaction: TransactionCreate) -> TransactionInDB:
        tx_dict = transaction.model_dump()
        tx_dict["from_account_id"] = ObjectId(tx_dict["from_account_id"])
        if tx_dict.get("to_account_id"):
            tx_dict["to_account_id"] = ObjectId(tx_dict["to_account_id"])
        tx_dict["status"] = "success"
        tx_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(tx_dict)
        tx_dict["_id"] = result.inserted_id

        logger.info(
            "Транзакція %s: %.2f %s з %s",
            result.inserted_id,
            tx_dict["amount"],
            tx_dict["currency"],
            tx_dict["from_account_id"],
        )
        return self._doc_to_model(tx_dict)

    async def get_by_id(self, tx_id: str) -> Optional[TransactionInDB]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(tx_id)})
        except Exception:
            return None
        return self._doc_to_model(doc) if doc else None

    async def get_by_account(
        self, account_id: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[TransactionInDB], int]:

        query = {
            "$or": [
                {"from_account_id": ObjectId(account_id)},
                {"to_account_id": ObjectId(account_id)},
            ]
        }
        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs], total

    async def get_all(
        self, limit: int = 20, offset: int = 0
    ) -> Tuple[List[TransactionInDB], int]:
        total = await self.collection.count_documents({})
        cursor = self.collection.find().sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs], total