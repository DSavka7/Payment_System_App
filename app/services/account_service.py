from typing import List, Optional

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.constants import SUSPICIOUS_THRESHOLDS
from app.core.exceptions import (
    AccountNotFound, AccountBlocked, CurrencyMismatch,
    InsufficientFunds, SelfTransferNotAllowed, UserInactive,
)
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate, TransferRequest
from app.models.transaction_models import (
    TransactionCreate, TransactionResponse,
    TransactionReviewUpdate, SuspiciousTransactionResponse,
)
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)


class AccountService:

    def __init__(
        self,
        account_repo: AccountRepository,
        tx_repo: Optional[TransactionRepository] = None,
        db: Optional[AsyncIOMotorDatabase] = None,
    ):
        self.account_repo = account_repo
        self.tx_repo = tx_repo
        self._db = db

    async def create_account(self, account: AccountCreate) -> AccountResponse:
        await self._check_user_active(account.user_id)
        account_in_db = await self.account_repo.create(account)
        logger.info("Created account id=%s for user_id=%s", account_in_db.id, account.user_id)
        return AccountResponse.model_validate(account_in_db)

    async def get_account(self, account_id: str) -> AccountResponse:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)

    async def get_user_accounts(self, user_id: str) -> List[AccountResponse]:
        accounts = await self.account_repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(acc) for acc in accounts]

    async def update_account(self, account_id: str, update_data: AccountUpdate) -> AccountResponse:
        account = await self.account_repo.update(account_id, update_data)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)

    async def transfer(self, request: TransferRequest, user_id: str) -> TransactionResponse:
        await self._check_user_active(user_id)

        from_acc = await self.account_repo.get_by_id(request.from_account_id)
        if not from_acc:
            raise AccountNotFound()

        # Resolve recipient account by ID or card number
        to_acc = None
        if request.to_account_id:
            to_acc = await self.account_repo.get_by_id(request.to_account_id)
        elif request.to_card_number:
            to_acc = await self.account_repo.get_by_card_number(request.to_card_number)

        if not to_acc:
            raise AccountNotFound()

        if from_acc.id == to_acc.id:
            raise SelfTransferNotAllowed()

        if from_acc.status == "blocked":
            raise AccountBlocked("Рахунок відправника заблоковано. Переказ неможливий.")

        if to_acc.status == "blocked":
            raise AccountBlocked("Рахунок отримувача заблоковано. Переказ неможливий.")

        # Перевірка статусу власника рахунку відправника (на випадок розбіжності user_id)
        await self._check_account_owner_active(from_acc.user_id, "відправника")

        # Перевірка статусу власника рахунку отримувача
        await self._check_account_owner_active(to_acc.user_id, "отримувача")

        if from_acc.currency != to_acc.currency:
            raise CurrencyMismatch()

        if from_acc.balance < request.amount:
            raise InsufficientFunds()

        threshold = SUSPICIOUS_THRESHOLDS.get(from_acc.currency, 50_000.0)
        is_suspicious = request.amount >= threshold

        if is_suspicious:
            logger.warning(
                "Suspicious transfer: %.2f %s from id=%s to id=%s (threshold=%.2f)",
                request.amount, from_acc.currency, from_acc.id, to_acc.id, threshold,
            )
        else:
            await self.account_repo.update_balance(from_acc.id, round(from_acc.balance - request.amount, 2))
            await self.account_repo.update_balance(to_acc.id, round(to_acc.balance + request.amount, 2))
            logger.info("Transfer: %.2f %s from id=%s to id=%s", request.amount, from_acc.currency, from_acc.id, to_acc.id)

        if self.tx_repo:
            tx = await self.tx_repo.create(
                TransactionCreate(
                    from_account_id=from_acc.id,
                    to_account_id=to_acc.id,
                    amount=request.amount,
                    currency=from_acc.currency,
                    type="transfer",
                    category="transfer",
                    description=request.description,
                    is_income=False,
                    is_suspicious=is_suspicious,
                )
            )
            return TransactionResponse.model_validate(tx)

        # Fallback for tests without tx_repo
        from datetime import datetime
        return TransactionResponse(
            id="local",
            from_account_id=from_acc.id,
            to_account_id=to_acc.id,
            amount=request.amount,
            currency=from_acc.currency,
            type="transfer",
            category="transfer",
            status="pending_review" if is_suspicious else "success",
            is_income=False,
            is_suspicious=is_suspicious,
            created_at=datetime.utcnow(),
        )

    async def approve_suspicious_transfer(
        self, tx_id: str, admin_id: str, review: TransactionReviewUpdate,
    ) -> TransactionResponse:
        if not self.tx_repo:
            raise RuntimeError("tx_repo is not connected")

        tx = await self.tx_repo.get_by_id(tx_id)
        if not tx:
            from app.core.exceptions import TransactionNotFound
            raise TransactionNotFound()

        if tx.status != "pending_review":
            from app.core.exceptions import RequestAlreadyResolved
            raise RequestAlreadyResolved()

        updated = await self.tx_repo.review(tx_id=tx_id, action=review.action, admin_id=admin_id, comment=review.comment)
        if not updated:
            from app.core.exceptions import TransactionNotFound
            raise TransactionNotFound()

        if review.action == "approve":
            from_acc = await self.account_repo.get_by_id(updated.from_account_id)
            to_acc = await self.account_repo.get_by_id(updated.to_account_id)
            if from_acc and to_acc:
                await self.account_repo.update_balance(from_acc.id, round(from_acc.balance - updated.amount, 2))
                await self.account_repo.update_balance(to_acc.id, round(to_acc.balance + updated.amount, 2))
                logger.info("Suspicious tx id=%s approved by admin id=%s, %.2f %s debited", tx_id, admin_id, updated.amount, updated.currency)
            else:
                logger.error("Approval error: account not found for tx id=%s", tx_id)

        return TransactionResponse.model_validate(updated)

    async def _check_user_active(self, user_id: str) -> None:
        """Raise UserInactive if the user is blocked."""
        if self._db is None:
            return
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            return
        doc = await self._db.users.find_one({"_id": oid}, {"status": 1})
        if doc and doc.get("status") == "blocked":
            raise UserInactive()

    async def _check_account_owner_active(self, account_user_id: str, role: str = "отримувача") -> None:
        """Raise AccountBlocked if the owner of an account is blocked."""
        if self._db is None:
            return
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            oid = ObjectId(account_user_id)
        except InvalidId:
            return
        doc = await self._db.users.find_one({"_id": oid}, {"status": 1})
        if doc and doc.get("status") == "blocked":
            raise AccountBlocked(f"Обліковий запис {role} заблоковано. Переказ неможливий.")


# --- Dependency injection ---

def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    return AccountRepository(db.accounts)


def get_tx_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TransactionRepository:
    return TransactionRepository(db.transactions)


def get_account_service(
    account_repo: AccountRepository = Depends(get_account_repository),
    tx_repo: TransactionRepository = Depends(get_tx_repository),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AccountService:
    return AccountService(account_repo, tx_repo, db)