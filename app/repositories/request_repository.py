from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List
from datetime import datetime
from pymongo import ReturnDocument

from app.models.request_models import RequestCreate, RequestInDB, RequestUpdate


class RequestRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    # =========================
    # CREATE
    # =========================
    async def create(self, request: RequestCreate) -> RequestInDB:
        req_dict = request.model_dump()


        req_dict["user_id"] = ObjectId(req_dict["user_id"])
        req_dict["account_id"] = ObjectId(req_dict["account_id"])

        req_dict["status"] = "pending"
        req_dict["created_at"] = datetime.utcnow()

        result = await self.collection.insert_one(req_dict)

        return RequestInDB(
            id=str(result.inserted_id),
            user_id=str(req_dict["user_id"]),
            account_id=str(req_dict["account_id"]),
            type=req_dict["type"],
            message=req_dict["message"],
            status=req_dict["status"],
            admin_comment=None,
            created_at=req_dict["created_at"],
            resolved_at=None
        )

    # =========================
    # GET BY ID
    # =========================
    async def get_by_id(self, request_id: str) -> Optional[RequestInDB]:
        doc = await self.collection.find_one({"_id": ObjectId(request_id)})
        if not doc:
            return None

        return RequestInDB(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),
            account_id=str(doc["account_id"]),
            type=doc["type"],
            message=doc["message"],
            status=doc["status"],
            admin_comment=doc.get("admin_comment"),
            created_at=doc["created_at"],
            resolved_at=doc.get("resolved_at")
        )

    # =========================
    # GET BY USER
    # =========================
    async def get_by_user(self, user_id: str) -> List[RequestInDB]:
        cursor = self.collection.find(
            {"user_id": ObjectId(user_id)}
        ).sort("created_at", -1)

        docs = await cursor.to_list(length=100)

        return [
            RequestInDB(
                id=str(doc["_id"]),
                user_id=str(doc["user_id"]),
                account_id=str(doc["account_id"]),
                type=doc["type"],
                message=doc["message"],
                status=doc["status"],
                admin_comment=doc.get("admin_comment"),
                created_at=doc["created_at"],
                resolved_at=doc.get("resolved_at")
            )
            for doc in docs
        ]

    # =========================
    # UPDATE STATUS
    # =========================
    async def update_status(self, request_id: str, update: RequestUpdate) -> Optional[RequestInDB]:
        update_dict = update.model_dump(exclude_unset=True)

        if update.status in ["approved", "rejected"]:
            update_dict["resolved_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(request_id)},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER
        )

        if not result:
            return None

        return RequestInDB(
            id=str(result["_id"]),
            user_id=str(result["user_id"]),
            account_id=str(result["account_id"]),
            type=result["type"],
            message=result["message"],
            status=result["status"],
            admin_comment=result.get("admin_comment"),
            created_at=result["created_at"],
            resolved_at=result.get("resolved_at")
        )