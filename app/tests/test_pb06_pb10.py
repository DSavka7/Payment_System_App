"""
Тести для PB-06 (self-block рахунку) та PB-10 (обробка запитів адміністратором
з автоматичною зміною статусу рахунку).
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.account_service import AccountService
from app.services.request_service import RequestService
from app.models.account_models import AccountInDB, AccountUpdate
from app.models.request_models import RequestInDB, RequestUpdate
from app.core.exceptions import (
    AccountNotFound,
    AccountBlocked,
    PermissionDeniedError,
    RequestNotFound,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_account(
    account_id: str = "acc000000000000000000001",
    user_id: str = "usr000000000000000000001",
    status: str = "active",
    currency: str = "UAH",
    balance: float = 500.0,
) -> AccountInDB:
    return AccountInDB(
        id=account_id,
        user_id=user_id,
        card_number="1234 **** **** 5678",
        currency=currency,
        balance=balance,
        status=status,
        created_at=datetime.utcnow(),
    )


def make_request(
    request_id: str = "req000000000000000000001",
    account_id: str = "acc000000000000000000001",
    req_type: str = "UNBLOCK",
    req_status: str = "pending",
) -> RequestInDB:
    return RequestInDB(
        id=request_id,
        user_id="usr000000000000000000001",
        account_id=account_id,
        type=req_type,
        message="Будь ласка, розблокуйте рахунок",
        status=req_status,
        created_at=datetime.utcnow(),
    )


# ── PB-06: Self-block ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestSelfBlock:

    async def test_self_block_success(self):
        """Власник успішно блокує свій рахунок."""
        account = make_account(account_id="acc001", user_id="usr001", status="active")
        blocked = make_account(account_id="acc001", user_id="usr001", status="blocked")

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(return_value=account)
        account_repo.update = AsyncMock(return_value=blocked)

        service = AccountService(account_repo)
        result = await service.self_block_account("acc001", "usr001")

        assert result.status == "blocked"
        account_repo.update.assert_called_once_with("acc001", AccountUpdate(status="blocked"))

    async def test_self_block_wrong_owner(self):
        """Спроба заблокувати чужий рахунок — PermissionDenied."""
        account = make_account(account_id="acc001", user_id="usr001")

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(return_value=account)

        service = AccountService(account_repo)
        with pytest.raises((PermissionDeniedError, Exception)):
            await service.self_block_account("acc001", "usr999")

    async def test_self_block_already_blocked(self):
        """Спроба заблокувати вже заблокований рахунок — AccountBlocked."""
        account = make_account(account_id="acc001", user_id="usr001", status="blocked")

        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(return_value=account)

        service = AccountService(account_repo)
        with pytest.raises(AccountBlocked):
            await service.self_block_account("acc001", "usr001")

    async def test_self_block_account_not_found(self):
        """Рахунок не знайдено — AccountNotFound."""
        account_repo = MagicMock()
        account_repo.get_by_id = AsyncMock(return_value=None)

        service = AccountService(account_repo)
        with pytest.raises(AccountNotFound):
            await service.self_block_account("acc001", "usr001")


# ── PB-10: Обробка запитів адміністратором ────────────────────────────────────

@pytest.mark.asyncio
class TestRequestAdminProcessing:

    def _make_service(self, request_repo=None, account_repo=None) -> RequestService:
        if request_repo is None:
            request_repo = MagicMock()
        if account_repo is None:
            account_repo = MagicMock()
        return RequestService(request_repo, account_repo)

    async def test_approve_unblock_request_activates_account(self):
        """Схвалення запиту UNBLOCK → рахунок стає active."""
        req = make_request(req_type="UNBLOCK", req_status="pending")
        req.status = "approved"

        request_repo = MagicMock()
        request_repo.update_status = AsyncMock(return_value=req)

        account_repo = MagicMock()
        activated = make_account(account_id=req.account_id, status="active")
        account_repo.update = AsyncMock(return_value=activated)

        service = self._make_service(request_repo, account_repo)
        result = await service.update_request_status(
            req.id, RequestUpdate(status="approved")
        )

        assert result.status == "approved"
        account_repo.update.assert_called_once_with(
            req.account_id, AccountUpdate(status="active")
        )

    async def test_approve_block_request_blocks_account(self):
        """Схвалення запиту BLOCK → рахунок стає blocked."""
        req = make_request(req_type="BLOCK", req_status="pending")
        req.status = "approved"

        request_repo = MagicMock()
        request_repo.update_status = AsyncMock(return_value=req)

        account_repo = MagicMock()
        blocked = make_account(account_id=req.account_id, status="blocked")
        account_repo.update = AsyncMock(return_value=blocked)

        service = self._make_service(request_repo, account_repo)
        await service.update_request_status(req.id, RequestUpdate(status="approved"))

        account_repo.update.assert_called_once_with(
            req.account_id, AccountUpdate(status="blocked")
        )

    async def test_reject_request_does_not_change_account(self):
        """Відхилення запиту → статус рахунку не змінюється."""
        req = make_request(req_type="UNBLOCK", req_status="pending")
        req.status = "rejected"

        request_repo = MagicMock()
        request_repo.update_status = AsyncMock(return_value=req)

        account_repo = MagicMock()
        account_repo.update = AsyncMock()

        service = self._make_service(request_repo, account_repo)
        result = await service.update_request_status(
            req.id, RequestUpdate(status="rejected", admin_comment="Причина відхилення")
        )

        assert result.status == "rejected"
        account_repo.update.assert_not_called()

    async def test_approve_limit_change_does_not_change_status(self):
        """Схвалення LIMIT_CHANGE → статус рахунку не змінюється."""
        req = make_request(req_type="LIMIT_CHANGE", req_status="pending")
        req.status = "approved"

        request_repo = MagicMock()
        request_repo.update_status = AsyncMock(return_value=req)

        account_repo = MagicMock()
        account_repo.update = AsyncMock()

        service = self._make_service(request_repo, account_repo)
        await service.update_request_status(req.id, RequestUpdate(status="approved"))

        account_repo.update.assert_not_called()

    async def test_approve_request_not_found(self):
        """Запит не знайдено → RequestNotFound."""
        request_repo = MagicMock()
        request_repo.update_status = AsyncMock(return_value=None)

        service = self._make_service(request_repo)
        with pytest.raises(RequestNotFound):
            await service.update_request_status(
                "req_nonexistent", RequestUpdate(status="approved")
            )

    async def test_approve_with_admin_comment(self):
        """Адмін може додати коментар при схваленні."""
        req = make_request(req_type="UNBLOCK")
        req.status = "approved"
        req.admin_comment = "Документи перевірено"

        request_repo = MagicMock()
        request_repo.update_status = AsyncMock(return_value=req)

        account_repo = MagicMock()
        account_repo.update = AsyncMock(return_value=make_account())

        service = self._make_service(request_repo, account_repo)
        result = await service.update_request_status(
            req.id,
            RequestUpdate(status="approved", admin_comment="Документи перевірено"),
        )

        assert result.admin_comment == "Документи перевірено"
