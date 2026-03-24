from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List
from datetime import datetime

from app.models.transaction_models import TransactionCreate, TransactionInDB


class TransactionRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    # =========================
    # CREATE
    # =========================
    async def create(self, transaction: TransactionCreate) -> TransactionInDB:
        tx_dict = transaction.model_dump()


        tx_dict["from_account_id"] = ObjectId(tx_dict["from_account_id"])

        if tx_dict.get("to_account_id"):
            tx_dict["to_account_id"] = ObjectId(tx_dict["to_account_id"])

        tx_dict["status"] = "success"
        tx_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(tx_dict)

        return TransactionInDB(
            id=str(result.inserted_id),
            from_account_id=str(tx_dict["from_account_id"]),
            to_account_id=str(tx_dict["to_account_id"]) if tx_dict.get("to_account_id") else None,
            amount=tx_dict["amount"],
            currency=tx_dict["currency"],
            type=tx_dict["type"],
            category=tx_dict["category"],
            merchant_name=tx_dict.get("merchant_name"),
            description=tx_dict.get("description"),
            status=tx_dict["status"],
            is_income=tx_dict.get("is_income", False),
            created_at=tx_dict["created_at"]
        )

    # =========================
    # GET BY ID
    # =========================
    async def get_by_id(self, tx_id: str) -> Optional[TransactionInDB]:
        doc = await self.collection.find_one({"_id": ObjectId(tx_id)})

        if not doc:
            return None

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
            created_at=doc["created_at"]
        )

    # =========================
    # GET BY ACCOUNT
    # =========================
    async def get_by_account(self, account_id: str, limit: int = 50) -> List[TransactionInDB]:
        cursor = self.collection.find(
            {
                "$or": [
                    {"from_account_id": ObjectId(account_id)},
                    {"to_account_id": ObjectId(account_id)},
                ]
            }
        ).sort("created_at", -1).limit(limit)

        docs = await cursor.to_list(length=limit)

        return [
            TransactionInDB(
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
                created_at=doc["created_at"]
            )
            for doc in docs
        ]