"""
Репозиторій для роботи з колекцією transactions у MongoDB.
"""
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection
from typing import Optional, List
from datetime import datetime

from app.core.exceptions import InvalidObjectId
from app.core.logging_config import get_logger
from app.models.transaction_models import TransactionCreate, TransactionInDB

logger = get_logger(__name__)


class TransactionRepository:
    """Репозиторій для CRUD-операцій з транзакціями."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, transaction: TransactionCreate) -> TransactionInDB:
        """Створює нову транзакцію у базі даних."""
        tx_dict = transaction.model_dump()

        try:
            tx_dict["from_account_id"] = ObjectId(tx_dict["from_account_id"])
        except InvalidId:
            raise InvalidObjectId("from_account_id")

        if tx_dict.get("to_account_id"):
            try:
                tx_dict["to_account_id"] = ObjectId(tx_dict["to_account_id"])
            except InvalidId:
                raise InvalidObjectId("to_account_id")

        tx_dict["status"] = "success"
        tx_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(tx_dict)
        logger.info(
            "Створено транзакцію id=%s, тип=%s, сума=%s %s",
            result.inserted_id,
            tx_dict["type"],
            tx_dict["amount"],
            tx_dict["currency"],
        )

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
            created_at=tx_dict["created_at"],
        )

    async def get_by_id(self, tx_id: str) -> Optional[TransactionInDB]:
        """Знаходить транзакцію за ID."""
        try:
            oid = ObjectId(tx_id)
        except InvalidId:
            raise InvalidObjectId("tx_id")

        doc = await self.collection.find_one({"_id": oid})
        if not doc:
            return None

        return self._doc_to_model(doc)

    async def get_by_account(self, account_id: str, limit: int = 50, offset: int = 0) -> List[TransactionInDB]:
        """
        Повертає транзакції рахунку з підтримкою пагінації.

        Args:
            account_id: ObjectId рахунку.
            limit: Максимальна кількість записів.
            offset: Зміщення (для пагінації).
        """
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        cursor = (
            self.collection.find(
                {"$or": [{"from_account_id": oid}, {"to_account_id": oid}]}
            )
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )

        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs]

    @staticmethod
    def _doc_to_model(doc: dict) -> TransactionInDB:
        """Конвертує документ MongoDB у Pydantic-модель."""
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