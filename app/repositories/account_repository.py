"""
Репозиторій для роботи з колекцією accounts у MongoDB.
"""
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


def _generate_card_number() -> str:
    """Генерує випадковий 16-значний номер картки."""
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])


def _mask_card_number(full: str) -> str:
    """Маскує номер: '1234567890123456' -> '1234 **** **** 5678'."""
    return f"{full[:4]} **** **** {full[12:]}"


class AccountRepository:
    """Репозиторій для CRUD-операцій з банківськими рахунками."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create(self, account: AccountCreate) -> AccountInDB:
        """Створює новий рахунок з автоматично згенерованим номером картки."""
        account_dict = account.model_dump()
        account_dict["user_id"] = ObjectId(account_dict["user_id"])

        full_number = _generate_card_number()
        account_dict["card_number"] = _mask_card_number(full_number)
        account_dict["card_number_full"] = full_number
        account_dict["status"] = "active"
        account_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(account_dict)
        logger.info("Створено рахунок id=%s для user_id=%s", result.inserted_id, account.user_id)

        return AccountInDB(
            id=str(result.inserted_id),
            user_id=str(account_dict["user_id"]),
            card_number=account_dict["card_number"],
            card_number_full=full_number,
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
        return self._doc_to_model(doc)

    async def get_by_card_number(self, card_number: str) -> Optional[AccountInDB]:
        """Знаходить рахунок за повним номером картки."""
        doc = await self.collection.find_one({"card_number_full": card_number})
        if not doc:
            return None
        return self._doc_to_model(doc)

    async def get_by_user_id(self, user_id: str) -> List[AccountInDB]:
        """Повертає всі рахунки користувача."""
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        cursor = self.collection.find({"user_id": oid})
        docs = await cursor.to_list(length=100)
        return [self._doc_to_model(doc) for doc in docs]

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
        return self._doc_to_model(result)

    async def update_balance(self, account_id: str, new_balance: float) -> None:
        """Оновлює баланс рахунку."""
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        await self.collection.update_one(
            {"_id": oid},
            {"$set": {"balance": new_balance}},
        )

    async def delete(self, account_id: str) -> bool:
        """Видаляє рахунок."""
        try:
            oid = ObjectId(account_id)
        except InvalidId:
            raise InvalidObjectId("account_id")

        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0

    @staticmethod
    def _doc_to_model(doc: dict) -> AccountInDB:
        """Конвертує документ MongoDB у Pydantic-модель."""
        return AccountInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            card_number=doc.get("card_number", "**** **** **** ****"),
            card_number_full=doc.get("card_number_full"),
            currency=doc["currency"],
            balance=doc["balance"],
            status=doc["status"],
            created_at=doc["created_at"],
        )