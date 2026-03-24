from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List
from datetime import datetime
from pymongo import ReturnDocument

from app.models.account_models import AccountCreate, AccountInDB, AccountUpdate


class AccountRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    # =========================
    # CREATE
    # =========================
    async def create(self, account: AccountCreate) -> AccountInDB:
        account_dict = account.model_dump()


        account_dict["user_id"] = ObjectId(account_dict["user_id"])

        account_dict["status"] = "active"
        account_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(account_dict)


        return AccountInDB(
            id=str(result.inserted_id),
            user_id=str(account_dict["user_id"]),
            card_number=account_dict["card_number"],
            currency=account_dict["currency"],
            balance=account_dict["balance"],
            status=account_dict["status"],
            created_at=account_dict["created_at"]
        )

    # =========================
    # GET BY ID
    # =========================
    async def get_by_id(self, account_id: str) -> Optional[AccountInDB]:
        doc = await self.collection.find_one({"_id": ObjectId(account_id)})
        if not doc:
            return None

        return AccountInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            card_number=doc["card_number"],
            currency=doc["currency"],
            balance=doc["balance"],
            status=doc["status"],
            created_at=doc["created_at"]
        )

    # =========================
    # GET BY USER ID
    # =========================
    async def get_by_user_id(self, user_id: str) -> List[AccountInDB]:
        cursor = self.collection.find({"user_id": ObjectId(user_id)})
        docs = await cursor.to_list(length=100)

        return [
            AccountInDB(
                id=str(doc["_id"]),
                user_id=str(doc["user_id"]),
                card_number=doc["card_number"],
                currency=doc["currency"],
                balance=doc["balance"],
                status=doc["status"],
                created_at=doc["created_at"]
            )
            for doc in docs
        ]

    # =========================
    # UPDATE
    # =========================
    async def update(self, account_id: str, update_data: AccountUpdate) -> Optional[AccountInDB]:
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$set": update_data.model_dump(exclude_unset=True)},
            return_document=ReturnDocument.AFTER
        )

        if not result:
            return None

        return AccountInDB(
            id=str(result["_id"]),
            user_id=str(result["user_id"]),
            card_number=result["card_number"],
            currency=result["currency"],
            balance=result["balance"],
            status=result["status"],
            created_at=result["created_at"]
        )

    # =========================
    # DELETE
    # =========================
    async def delete(self, account_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(account_id)})
        return result.deleted_count > 0