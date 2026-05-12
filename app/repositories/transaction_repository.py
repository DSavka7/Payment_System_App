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

        # Статус залежить від прапорця is_suspicious
        if tx_dict.get("is_suspicious"):
            tx_dict["status"] = "pending_review"
        else:
            tx_dict["status"] = "success"

        tx_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(tx_dict)
        logger.info(
            "Створено транзакцію id=%s, тип=%s, сума=%s %s, статус=%s",
            result.inserted_id,
            tx_dict["type"],
            tx_dict["amount"],
            tx_dict["currency"],
            tx_dict["status"],
        )

        return self._build_model(result.inserted_id, tx_dict)

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

    async def get_by_account(
        self,
        account_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[TransactionInDB], int]:
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        query = {"$or": [{"from_account_id": oid}, {"to_account_id": oid}]}
        total = await self.collection.count_documents(query)

        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs], total

    async def get_suspicious(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[TransactionInDB], int]:
        query: dict = {"is_suspicious": True}
        if status:
            query["status"] = status

        total = await self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_model(doc) for doc in docs], total

    async def review(
        self,
        tx_id: str,
        action: str,
        admin_id: str,
        comment: Optional[str] = None,
    ) -> Optional[TransactionInDB]:
        """
        Адміністратор схвалює або відхиляє підозрілу транзакцію.

        Args:
            tx_id: ID транзакції.
            action: 'approve' або 'reject'.
            admin_id: ID адміна, що виконує перевірку.
            comment: Необов'язковий коментар.

        Returns:
            Оновлена TransactionInDB або None якщо не знайдено.
        """
        try:
            oid = ObjectId(tx_id)
        except InvalidId:
            raise InvalidObjectId("tx_id")

        new_status = "approved" if action == "approve" else "rejected"
        update_payload: dict = {
            "status": new_status,
            "reviewed_at": datetime.utcnow(),
            "reviewed_by": admin_id,
        }
        if comment:
            update_payload["review_comment"] = comment

        from pymongo import ReturnDocument
        result = await self.collection.find_one_and_update(
            {"_id": oid, "is_suspicious": True},
            {"$set": update_payload},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None

        logger.info(
            "Транзакцію id=%s %s адміном id=%s",
            tx_id,
            new_status,
            admin_id,
        )
        return self._doc_to_model(result)

    async def count_pending_review(self) -> int:
        """Кількість транзакцій, що очікують на перевірку адміністратором."""
        return await self.collection.count_documents(
            {"is_suspicious": True, "status": "pending_review"}
        )

    # ──────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _build_model(inserted_id, tx_dict: dict) -> TransactionInDB:
        """Будує модель після вставки (ObjectId → str)."""
        return TransactionInDB(
            id=str(inserted_id),
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
            is_suspicious=tx_dict.get("is_suspicious", False),
            review_comment=tx_dict.get("review_comment"),
            reviewed_at=tx_dict.get("reviewed_at"),
            reviewed_by=tx_dict.get("reviewed_by"),
            created_at=tx_dict["created_at"],
        )

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
            is_suspicious=doc.get("is_suspicious", False),
            review_comment=doc.get("review_comment"),
            reviewed_at=doc.get("reviewed_at"),
            reviewed_by=doc.get("reviewed_by"),
            created_at=doc["created_at"],
        )