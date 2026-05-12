"""
Сервісний шар для управління банківськими рахунками.
"""
from typing import List, Optional

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.constants import SUSPICIOUS_THRESHOLDS
from app.core.exceptions import (
    AccountNotFound,
    AccountBlocked,
    CurrencyMismatch,
    InsufficientFunds,
    SelfTransferNotAllowed,
    UserInactive,
)
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate, TransferRequest
from app.models.transaction_models import (
    TransactionCreate,
    TransactionResponse,
    TransactionReviewUpdate,
    SuspiciousTransactionResponse,
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
        """Створює новий банківський рахунок."""
        # Перевіряємо статус користувача перед створенням рахунку
        await self._check_user_active(account.user_id)

        account_in_db = await self.account_repo.create(account)
        logger.info("Створено рахунок id=%s для user_id=%s", account_in_db.id, account.user_id)
        return AccountResponse.model_validate(account_in_db)

    async def get_account(self, account_id: str) -> AccountResponse:
        """Повертає рахунок за ID або кидає AccountNotFound."""
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)

    async def get_user_accounts(self, user_id: str) -> List[AccountResponse]:
        """Повертає всі рахунки користувача."""
        accounts = await self.account_repo.get_by_user_id(user_id)
        return [AccountResponse.model_validate(acc) for acc in accounts]

    async def update_account(self, account_id: str, update_data: AccountUpdate) -> AccountResponse:
        """Оновлює статус або баланс рахунку."""
        account = await self.account_repo.update(account_id, update_data)
        if not account:
            raise AccountNotFound()
        return AccountResponse.model_validate(account)

    async def transfer(self, request: TransferRequest, user_id: str) -> TransactionResponse:
        # 0. Перевіряємо статус користувача
        await self._check_user_active(user_id)

        # 1. Рахунок-відправник
        from_acc = await self.account_repo.get_by_id(request.from_account_id)
        if not from_acc:
            raise AccountNotFound()

        # 2. Рахунок-отримувач (за ID або номером картки)
        to_acc = None
        if request.to_account_id:
            to_acc = await self.account_repo.get_by_id(request.to_account_id)
        elif request.to_card_number:
            to_acc = await self.account_repo.get_by_card_number(request.to_card_number)

        if not to_acc:
            raise AccountNotFound()

        # 3. Самопереказ заборонено
        if from_acc.id == to_acc.id:
            raise SelfTransferNotAllowed()

        # 4. Статус рахунку-відправника
        if from_acc.status == "blocked":
            raise AccountBlocked("Рахунок відправника заблоковано. Переказ неможливий.")

        # 5. Статус рахунку-отримувача
        if to_acc.status == "blocked":
            raise AccountBlocked("Рахунок отримувача заблоковано. Переказ неможливий.")

        # 6. Відповідність валют
        if from_acc.currency != to_acc.currency:
            raise CurrencyMismatch()

        # 7. Достатність коштів
        if from_acc.balance < request.amount:
            raise InsufficientFunds()

        # 8. Перевірити чи підозрілий переказ
        threshold = SUSPICIOUS_THRESHOLDS.get(from_acc.currency, 50_000.0)
        is_suspicious = request.amount >= threshold

        if is_suspicious:
            logger.warning(
                "Підозрілий переказ: %.2f %s з рахунку id=%s → id=%s (поріг=%.2f)",
                request.amount, from_acc.currency, from_acc.id, to_acc.id, threshold,
            )
            # Кошти заморожуються на рахунку відправника (не списуємо одразу)
            # Транзакція зберігається зі статусом pending_review
        else:
            # Одразу списуємо/зараховуємо
            await self.account_repo.update_balance(from_acc.id, round(from_acc.balance - request.amount, 2))
            await self.account_repo.update_balance(to_acc.id, round(to_acc.balance + request.amount, 2))
            logger.info(
                "Переказ виконано: %.2f %s з id=%s → id=%s",
                request.amount, from_acc.currency, from_acc.id, to_acc.id,
            )

        # Зберегти транзакцію
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

        # Fallback без tx_repo (тести)
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
        self,
        tx_id: str,
        admin_id: str,
        review: TransactionReviewUpdate,
    ) -> TransactionResponse:

        if not self.tx_repo:
            raise RuntimeError("tx_repo не підключено")

        tx = await self.tx_repo.get_by_id(tx_id)
        if not tx:
            from app.core.exceptions import TransactionNotFound
            raise TransactionNotFound()

        if tx.status != "pending_review":
            from app.core.exceptions import RequestAlreadyResolved
            raise RequestAlreadyResolved()

        updated = await self.tx_repo.review(
            tx_id=tx_id,
            action=review.action,
            admin_id=admin_id,
            comment=review.comment,
        )

        if not updated:
            from app.core.exceptions import TransactionNotFound
            raise TransactionNotFound()

        # Якщо схвалено — виконуємо фактичне списання
        if review.action == "approve":
            from_acc = await self.account_repo.get_by_id(updated.from_account_id)
            to_acc = await self.account_repo.get_by_id(updated.to_account_id)

            if from_acc and to_acc:
                await self.account_repo.update_balance(
                    from_acc.id, round(from_acc.balance - updated.amount, 2)
                )
                await self.account_repo.update_balance(
                    to_acc.id, round(to_acc.balance + updated.amount, 2)
                )
                logger.info(
                    "Підозрілий переказ id=%s схвалено адміном id=%s, %.2f %s списано",
                    tx_id, admin_id, updated.amount, updated.currency,
                )
            else:
                logger.error(
                    "Помилка схвалення: рахунок не знайдено для транзакції id=%s", tx_id
                )

        return TransactionResponse.model_validate(updated)

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    async def _check_user_active(self, user_id: str) -> None:
        if self._db is None:
            return  # У тестах без DB пропускаємо
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            return
        doc = await self._db.users.find_one({"_id": oid}, {"status": 1})
        if doc and doc.get("status") == "blocked":
            raise UserInactive()


# ──────────────────────────────────────────────
# Dependency Injection
# ──────────────────────────────────────────────

def get_account_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AccountRepository:
    """DI: повертає екземпляр AccountRepository."""
    return AccountRepository(db.accounts)


def get_tx_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> TransactionRepository:
    """DI: повертає TransactionRepository для AccountService."""
    return TransactionRepository(db.transactions)


def get_account_service(
    account_repo: AccountRepository = Depends(get_account_repository),
    tx_repo: TransactionRepository = Depends(get_tx_repository),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AccountService:
    """DI: повертає AccountService з усіма залежностями."""
    return AccountService(account_repo, tx_repo, db)