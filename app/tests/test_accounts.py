
import pytest
from unittest.mock import AsyncMock, patch
from tests.conftest import (
    client, make_user_token, make_admin_token,
    FAKE_USER_ID, FAKE_ACCOUNT_ID, FAKE_ACCOUNT, FAKE_ACCOUNT_BLOCKED,
)


# ─── Self-block ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_self_block_success(client):
    """Користувач успішно блокує свій рахунок."""
    token = make_user_token()
    blocked = FAKE_ACCOUNT.model_copy(update={"status": "blocked"})

    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT,
    ), patch(
        "app.repositories.account_repository.AccountRepository.update",
        new_callable=AsyncMock,
        return_value=blocked,
    ):
        resp = await client.patch(
            f"/accounts/{FAKE_ACCOUNT_ID}/block",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "blocked"


@pytest.mark.asyncio
async def test_self_block_already_blocked(client):
    """Повторне блокування вже заблокованого рахунку — 409."""
    token = make_user_token()
    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT_BLOCKED,
    ):
        resp = await client.patch(
            f"/accounts/{FAKE_ACCOUNT_ID}/block",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_self_block_wrong_owner(client):
    """Спроба заблокувати чужий рахунок — 403."""
    token = make_user_token(user_id="another_user_id")
    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT,
    ):
        resp = await client.patch(
            f"/accounts/{FAKE_ACCOUNT_ID}/block",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_unblock_directly(client):

    token = make_user_token()
    resp = await client.patch(
        f"/accounts/{FAKE_ACCOUNT_ID}/unblock",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ─── ADMIN управління ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_block_account(client):
    """Адмін блокує рахунок напряму."""
    token = make_admin_token()
    blocked = FAKE_ACCOUNT.model_copy(update={"status": "blocked"})

    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT,
    ), patch(
        "app.repositories.account_repository.AccountRepository.update",
        new_callable=AsyncMock,
        return_value=blocked,
    ):
        resp = await client.patch(
            f"/accounts/{FAKE_ACCOUNT_ID}/admin-block",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "blocked"


@pytest.mark.asyncio
async def test_admin_unblock_account(client):
    """Адмін розблоковує рахунок."""
    token = make_admin_token()
    active = FAKE_ACCOUNT_BLOCKED.model_copy(update={"status": "active"})

    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT_BLOCKED,
    ), patch(
        "app.repositories.account_repository.AccountRepository.update",
        new_callable=AsyncMock,
        return_value=active,
    ):
        resp = await client.patch(
            f"/accounts/{FAKE_ACCOUNT_ID}/unblock",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_admin_unblock_already_active(client):
    """Розблокування вже активного рахунку — 409."""
    token = make_admin_token()
    with patch(
        "app.repositories.account_repository.AccountRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_ACCOUNT,
    ):
        resp = await client.patch(
            f"/accounts/{FAKE_ACCOUNT_ID}/unblock",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_user_cannot_create_via_admin_endpoints(client):
    """USER не має доступу до admin ендпоінтів списку рахунків."""
    token = make_user_token()
    resp = await client.get(
        "/accounts/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403