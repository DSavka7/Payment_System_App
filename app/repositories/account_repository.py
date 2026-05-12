"""Репозиторій для роботи з колекцією accounts у MongoDB."""
import random
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


def _gen_full_card_number() -> str:
    """Генерує повний унікальний 16-значний номер картки."""
    return ''.join(str(random.randint(0, 9)) for _ in range(16))


def _mask_card(full_number: str) -> str:
    """Маскирує номер картки для відображення."""
    return f"{full_number[:4]} **** **** {full_number[-4:]}"


class AccountRepository:

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, account: AccountCreate) -> AccountInDB:
        """Створює новий рахунок з повним номером картки."""
        doc = account.model_dump()
        doc["user_id"] = ObjectId(doc["user_id"])
        doc["status"] = "active"
        doc["created_at"] = datetime.utcnow()

        # Генерація повного номера картки
        full_num = _gen_full_card_number()
        doc["card_number_full"] = full_num
        doc["card_number"] = _mask_card(full_num)

        # Перевірка унікальності (маловірогідно, але надійно)
        while await self.collection.find_one({"card_number_full": full_num}):
            full_num = _gen_full_card_number()
            doc["card_number_full"] = full_num
            doc["card_number"] = _mask_card(full_num)

        result = await self.collection.insert_one(doc)

        logger.info(
            "Створено рахунок id=%s для user_id=%s | картка: %s",
            result.inserted_id, account.user_id, doc["card_number"]
        )

        return self._doc_to_model({**doc, "_id": result.inserted_id})

    async def get_by_id(self, account_id: str) -> Optional[AccountInDB]:
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")
        doc = await self.collection.find_one({"_id": oid})
        return self._doc_to_model(doc) if doc else None

    async def get_by_card_number(self, card_number: str) -> Optional[AccountInDB]:
        """Пошук за повним номером або маскованим."""
        if len(card_number) == 16 and card_number.isdigit():
            doc = await self.collection.find_one({"card_number_full": card_number})
        else:
            doc = await self.collection.find_one({"card_number": card_number})
        return self._doc_to_model(doc) if doc else None

    async def get_by_user_id(self, user_id: str) -> List[AccountInDB]:
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")
        cursor = self.collection.find({"user_id": oid})
        docs = await cursor.to_list(length=100)
        return [self._doc_to_model(d) for d in docs]

    async def count_by_user_id(self, user_id: str) -> int:
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            return 0
        return await self.collection.count_documents({"user_id": oid})

    async def update(self, account_id: str, update_data: AccountUpdate) -> Optional[AccountInDB]:
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")
        result = await self.collection.find_one_and_update(
            {"_id": oid},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=ReturnDocument.AFTER,
        )
        return self._doc_to_model(result) if result else None

    async def update_balance(self, account_id: str, new_balance: float) -> None:
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")
        await self.collection.update_one({"_id": oid}, {"$set": {"balance": new_balance}})

    async def update_status(self, account_id: str, status: str, reason: Optional[str] = None) -> Optional[AccountInDB]:
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        payload = {"status": status}
        if status == "blocked":
            payload["block_reason"] = reason
        else:
            payload["block_reason"] = None

        result = await self.collection.find_one_and_update(
            {"_id": oid}, {"$set": payload}, return_document=ReturnDocument.AFTER
        )
        return self._doc_to_model(result) if result else None

    async def delete(self, account_id: str) -> bool:
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")
        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0

    @staticmethod
    def _doc_to_model(doc: dict) -> AccountInDB:
        return AccountInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            card_number=doc.get("card_number", ""),
            card_number_full=doc.get("card_number_full"),
            currency=doc["currency"],
            balance=doc["balance"],
            status=doc["status"],
            created_at=doc["created_at"],
            block_reason=doc.get("block_reason"),
        )