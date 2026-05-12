"""Сервісний шар для адміністративних операцій."""
from typing import List, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import (
    InvalidObjectId, UserNotFound, TransactionNotFound,
    RequestAlreadyResolved, AccountNotFound, Forbidden,
)
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.admin_models import (
    AdminUserResponse, AdminUserStatusUpdate, AdminAccountStatusUpdate,
    AdminStatsResponse, AdminUserListResponse,
    AdminUserDetailsResponse, AdminAccountInfo, AdminTransactionInfo,
)
from app.models.transaction_models import (
    TransactionResponse, TransactionReviewUpdate, SuspiciousTransactionResponse,
)
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


class AdminService:
    """Facade для адміністративних операцій."""

    def __init__(self, db: AsyncIOMotorDatabase, account_repo: AccountRepository, tx_repo: TransactionRepository):
        self._db = db
        self._account_repo = account_repo
        self._tx_repo = tx_repo

    # ── Статистика ─────────────────────────────────────────────────────

    async def get_stats(self) -> AdminStatsResponse:
        total_users   = await self._db.users.count_documents({})
        active_users  = await self._db.users.count_documents({"status": "active"})
        blocked_users = await self._db.users.count_documents({"status": "blocked"})
        total_accounts = await self._db.accounts.count_documents({})
        total_tx = await self._db.transactions.count_documents({})
        pending_req = await self._db.requests.count_documents({"status": "pending"})
        suspicious = await self._db.transactions.count_documents({"is_suspicious": True})
        pending_review = await self._db.transactions.count_documents(
            {"is_suspicious": True, "status": "pending_review"}
        )
        return AdminStatsResponse(
            total_users=total_users, active_users=active_users, blocked_users=blocked_users,
            total_accounts=total_accounts, total_transactions=total_tx,
            pending_requests=pending_req, suspicious_transactions=suspicious,
            pending_review_transactions=pending_review,
        )

    # ── Список користувачів ─────────────────────────────────────────────

    async def get_users(self, limit=50, offset=0, search=None, status_filter=None) -> AdminUserListResponse:
        query: dict = {}
        if search:
            query["$or"] = [
                {"email":      {"$regex": search, "$options": "i"}},
                {"phone":      {"$regex": search, "$options": "i"}},
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name":  {"$regex": search, "$options": "i"}},
            ]
        if status_filter:
            query["status"] = status_filter

        total = await self._db.users.count_documents(query)
        cursor = self._db.users.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)

        items = []
        for doc in docs:
            uid = str(doc["_id"])
            acc_count = await self._account_repo.count_by_user_id(uid)
            items.append(AdminUserResponse(
                id=uid, email=doc["email"], phone=doc.get("phone", ""),
                first_name=doc.get("first_name", ""), last_name=doc.get("last_name", ""),
                role=doc.get("role", "USER"), status=doc.get("status", "active"),
                created_at=doc["created_at"], accounts_count=acc_count,
                block_reason=doc.get("block_reason"),
            ))

        return AdminUserListResponse(items=items, total=total, limit=limit, offset=offset)

    # ── Деталі користувача ──────────────────────────────────────────────

    async def get_user_details(self, user_id: str) -> AdminUserDetailsResponse:
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        doc = await self._db.users.find_one({"_id": oid})
        if not doc:
            raise UserNotFound()

        accs_raw = await self._account_repo.get_by_user_id(user_id)
        accounts = [
            AdminAccountInfo(
                id=a.id, card_number=a.card_number, currency=a.currency,
                balance=a.balance, status=a.status, created_at=a.created_at,
                block_reason=a.block_reason,   # ← передаємо причину
            )
            for a in accs_raw
        ]

        all_txs, seen = [], set()
        for acc in accs_raw:
            txs, _ = await self._tx_repo.get_by_account(acc.id, limit=50, offset=0)
            for tx in txs:
                if tx.id not in seen:
                    seen.add(tx.id)
                    all_txs.append(tx)

        all_txs.sort(key=lambda t: t.created_at, reverse=True)
        tx_infos = [
            AdminTransactionInfo(
                id=t.id, from_account_id=t.from_account_id, to_account_id=t.to_account_id,
                amount=t.amount, currency=t.currency, type=t.type, status=t.status,
                is_suspicious=t.is_suspicious, description=t.description, created_at=t.created_at,
            )
            for t in all_txs[:20]
        ]

        total_balance_uah = sum(a.balance for a in accs_raw if a.currency == "UAH")

        return AdminUserDetailsResponse(
            id=str(doc["_id"]), email=doc["email"], phone=doc.get("phone", ""),
            first_name=doc.get("first_name", ""), last_name=doc.get("last_name", ""),
            role=doc.get("role", "USER"), status=doc.get("status", "active"),
            created_at=doc["created_at"], block_reason=doc.get("block_reason"),
            accounts=accounts, recent_transactions=tx_infos,
            total_transactions=len(all_txs), total_balance_uah=total_balance_uah,
        )

    # ── Статус користувача ──────────────────────────────────────────────

    async def update_user_status(self, user_id: str, update: AdminUserStatusUpdate, admin_id: str) -> AdminUserResponse:
        if user_id == admin_id:
            raise Forbidden("Адміністратор не може заблокувати власний акаунт")

        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise InvalidObjectId("user_id")

        target = await self._db.users.find_one({"_id": oid}, {"role": 1})
        if target and target.get("role") == "ADMIN":
            raise Forbidden("Неможливо заблокувати іншого адміністратора")

        from pymongo import ReturnDocument
        payload = {
            "status": update.status,
            "block_reason": update.reason if update.status == "blocked" else None,
        }
        result = await self._db.users.find_one_and_update(
            {"_id": oid}, {"$set": payload}, return_document=ReturnDocument.AFTER,
        )
        if not result:
            raise UserNotFound()

        logger.info("Юзер id=%s → %s. Причина: %s", user_id, update.status, update.reason)
        acc_count = await self._account_repo.count_by_user_id(user_id)

        return AdminUserResponse(
            id=str(result["_id"]), email=result["email"], phone=result.get("phone", ""),
            first_name=result.get("first_name", ""), last_name=result.get("last_name", ""),
            role=result.get("role", "USER"), status=result.get("status", "active"),
            created_at=result["created_at"], accounts_count=acc_count,
            block_reason=result.get("block_reason"),
        )

    # ── Статус рахунку ──────────────────────────────────────────────────

    async def update_account_status(
        self,
        account_id: str,
        update: AdminAccountStatusUpdate,
        admin_id: str,
    ) -> AdminAccountInfo:
        result = await self._account_repo.update_status(
            account_id=account_id,
            status=update.status,
            reason=update.reason,
        )
        if not result:
            raise AccountNotFound()

        return AdminAccountInfo(
            id=result.id, card_number=result.card_number, currency=result.currency,
            balance=result.balance, status=result.status, created_at=result.created_at,
            block_reason=result.block_reason,
        )

    # ── Підозрілі транзакції ────────────────────────────────────────────

    async def get_suspicious_transactions(self, status_filter=None, limit=50, offset=0):
        txs, total = await self._tx_repo.get_suspicious(status=status_filter, limit=limit, offset=offset)
        return [SuspiciousTransactionResponse.model_validate(tx) for tx in txs], total

    async def review_transaction(self, tx_id: str, review: TransactionReviewUpdate, admin_id: str) -> TransactionResponse:
        tx = await self._tx_repo.get_by_id(tx_id)
        if not tx or not tx.is_suspicious:
            raise TransactionNotFound()
        if tx.status != "pending_review":
            raise RequestAlreadyResolved()

        updated = await self._tx_repo.review(tx_id=tx_id, action=review.action, admin_id=admin_id, comment=review.comment)
        if not updated:
            raise TransactionNotFound()

        if review.action == "approve":
            from_acc = await self._account_repo.get_by_id(updated.from_account_id)
            to_acc   = await self._account_repo.get_by_id(updated.to_account_id)
            if from_acc and to_acc and from_acc.balance >= updated.amount:
                await self._account_repo.update_balance(from_acc.id, round(from_acc.balance - updated.amount, 2))
                await self._account_repo.update_balance(to_acc.id,   round(to_acc.balance   + updated.amount, 2))

        return TransactionResponse.model_validate(updated)

    # ── Всі запити ──────────────────────────────────────────────────────

    async def get_all_requests(self, status_filter=None, limit=50, offset=0):
        query: dict = {}
        if status_filter:
            query["status"] = status_filter
        total = await self._db.requests.count_documents(query)
        cursor = self._db.requests.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)

        result = []
        for doc in docs:
            user_email = "—"
            if doc.get("user_id"):
                ud = await self._db.users.find_one({"_id": doc["user_id"]}, {"email": 1})
                if ud:
                    user_email = ud["email"]
            result.append({
                "id": str(doc["_id"]), "user_id": str(doc["user_id"]),
                "user_email": user_email, "account_id": str(doc["account_id"]),
                "type": doc["type"], "message": doc["message"], "status": doc["status"],
                "admin_comment": doc.get("admin_comment"),
                "created_at": doc["created_at"].isoformat(),
                "resolved_at": doc["resolved_at"].isoformat() if doc.get("resolved_at") else None,
            })

        return result, total


def get_admin_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> AdminService:
    return AdminService(
        db=db,
        account_repo=AccountRepository(db.accounts),
        tx_repo=TransactionRepository(db.transactions),
    )