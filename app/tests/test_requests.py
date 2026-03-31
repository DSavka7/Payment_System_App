import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from tests.conftest import (
    client, make_user_token, make_admin_token,
    FAKE_USER_ID, FAKE_ACCOUNT_ID, FAKE_REQUEST_ID,
    FAKE_ACCOUNT, FAKE_ACCOUNT_BLOCKED, FAKE_NOW,
)
from app.models.request_models import RequestInDB


FAKE_UNBLOCK_REQUEST = RequestInDB(
    id=FAKE_REQUEST_ID,
    user_id=FAKE_USER_ID,
    account_id=FAKE_ACCOUNT_ID,
    type="UNBLOCK",
    message="Прошу розблокувати рахунок після самостійного блокування",
    status="pending",
    created_at=FAKE_NOW,
)

FAKE_LIMIT_REQUEST = RequestInDB(
    id=FAKE_REQUEST_ID,
    user_id=FAKE_USER_ID,
    account_id=FAKE_ACCOUNT_ID,
    type="LIMIT_CHANGE",
    message="Прошу збільшити добовий ліміт для бізнес-операцій",
    status="pending",
    requested_limit=50000.0,
    created_at=FAKE_NOW,
)


# ─── Створення UNBLOCK запиту ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_unblock_request_for_blocked_account(client):
    """Успішне створення UNBLOCK запиту для заблокованого рахунку."""
    token = make_user_token()
    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT_BLOCKED,
    ), patch(
        "app.repositories.request_repository.RequestRepository.has_pending",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "app.repositories.request_repository.RequestRepository.create",
        new_callable=AsyncMock,
        return_value=FAKE_UNBLOCK_REQUEST,
    ):
        resp = await client.post(
            "/requests/",
            json={
                "account_id": FAKE_ACCOUNT_ID,
                "type": "UNBLOCK",
                "message": "Прошу розблокувати рахунок після самостійного блокування",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 201
    assert resp.json()["type"] == "UNBLOCK"
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_unblock_request_for_active_account_fails(client):
    """UNBLOCK запит для активного рахунку — 409."""
    token = make_user_token()
    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT,  # активний рахунок
    ):
        resp = await client.post(
            "/requests/",
            json={
                "account_id": FAKE_ACCOUNT_ID,
                "type": "UNBLOCK",
                "message": "Спроба розблокувати активний рахунок",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_limit_change_without_limit_fails(client):
    """LIMIT_CHANGE без requested_limit — 422 (валідатор моделі)."""
    token = make_user_token()
    resp = await client.post(
        "/requests/",
        json={
            "account_id": FAKE_ACCOUNT_ID,
            "type": "LIMIT_CHANGE",
            "message": "Прошу змінити ліміт без вказівки нового значення",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_limit_change_success(client):
    """Успішне створення LIMIT_CHANGE запиту."""
    token = make_user_token()
    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT,
    ), patch(
        "app.repositories.request_repository.RequestRepository.has_pending",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "app.repositories.request_repository.RequestRepository.create",
        new_callable=AsyncMock,
        return_value=FAKE_LIMIT_REQUEST,
    ):
        resp = await client.post(
            "/requests/",
            json={
                "account_id": FAKE_ACCOUNT_ID,
                "type": "LIMIT_CHANGE",
                "message": "Прошу збільшити добовий ліміт для бізнес-операцій",
                "requested_limit": 50000.0,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 201
    assert resp.json()["requested_limit"] == 50000.0


@pytest.mark.asyncio
async def test_duplicate_pending_request_fails(client):
    """Дублікат pending-запиту — 409."""
    token = make_user_token()
    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT_BLOCKED,
    ), patch(
        "app.repositories.request_repository.RequestRepository.has_pending",
        new_callable=AsyncMock,
        return_value=True,  # вже є активний запит
    ):
        resp = await client.post(
            "/requests/",
            json={
                "account_id": FAKE_ACCOUNT_ID,
                "type": "UNBLOCK",
                "message": "Другий запит на розблокування",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 409


# ─── Admin: схвалення/відхилення ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_approve_unblock_request(client):
    """Адмін схвалює UNBLOCK запит — рахунок розблоковується."""
    token = make_admin_token()
    approved_req = FAKE_UNBLOCK_REQUEST.model_copy(
        update={"status": "approved", "resolved_at": FAKE_NOW}
    )
    with patch(
        "app.repositories.request_repository.RequestRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_UNBLOCK_REQUEST,
    ), patch(
        "app.repositories.request_repository.RequestRepository.update_status",
        new_callable=AsyncMock,
        return_value=approved_req,
    ), patch(
        "app.repositories.account_repository.AccountRepository.update",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT,
    ):
        resp = await client.patch(
            f"/requests/{FAKE_REQUEST_ID}/status",
            json={"status": "approved", "admin_comment": "Заявку схвалено"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_user_cannot_approve_request(client):
    """USER не може схвалювати запити — 403."""
    token = make_user_token()
    resp = await client.patch(
        f"/requests/{FAKE_REQUEST_ID}/status",
        json={"status": "approved"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_see_all_requests(client):
    """Адмін бачить всі запити."""
    token = make_admin_token()
    with patch(
        "app.repositories.request_repository.RequestRepository.get_all",
        new_callable=AsyncMock,
        return_value=([FAKE_UNBLOCK_REQUEST], 1),
    ):
        resp = await client.get(
            "/requests/?status=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_user_cannot_see_all_requests(client):
    """USER не може отримати список всіх запитів — 403."""
    token = make_user_token()
    resp = await client.get(
        "/requests/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403