import pytest
from unittest.mock import AsyncMock, patch
from tests.conftest import (
    client, make_user_token, make_admin_token,
    FAKE_USER, FAKE_USER_ID, FAKE_ADMIN_ID,
)


# ─── Реєстрація ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    """Успішна реєстрація з валідним паролем."""
    with patch(
        "app.repositories.user_repository.UserRepository.create",
        new_callable=AsyncMock,
        return_value=FAKE_USER,
    ):
        resp = await client.post("/users/register", json={
            "email": "newuser@test.com",
            "phone": "+380991234567",
            "first_name": "Іван",
            "last_name": "Петренко",
            "password": "SecurePass1!",
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@test.com"
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_weak_password_no_uppercase(client):
    """Пароль без великої літери — 422."""
    resp = await client.post("/users/register", json={
        "email": "test@test.com",
        "phone": "+380991234567",
        "first_name": "Тест",
        "last_name": "Юзер",
        "password": "weakpass1!",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_no_special(client):
    """Пароль без спеціального символу — 422."""
    resp = await client.post("/users/register", json={
        "email": "test@test.com",
        "phone": "+380991234567",
        "first_name": "Тест",
        "last_name": "Юзер",
        "password": "WeakPass1",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_too_short(client):
    """Пароль менше 8 символів — 422."""
    resp = await client.post("/users/register", json={
        "email": "test@test.com",
        "phone": "+380991234567",
        "first_name": "Тест",
        "last_name": "Юзер",
        "password": "Aa1!",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_phone(client):
    """Невірний формат телефону — 422."""
    resp = await client.post("/users/register", json={
        "email": "test@test.com",
        "phone": "0991234567",
        "first_name": "Тест",
        "last_name": "Юзер",
        "password": "SecurePass1!",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Спроба реєстрації з вже існуючим email — 409."""
    from app.core.exceptions import UserAlreadyExists
    with patch(
        "app.repositories.user_repository.UserRepository.create",
        new_callable=AsyncMock,
        side_effect=UserAlreadyExists(),
    ):
        resp = await client.post("/users/register", json={
            "email": "existing@test.com",
            "phone": "+380991234567",
            "first_name": "Тест",
            "last_name": "Юзер",
            "password": "SecurePass1!",
        })
    assert resp.status_code == 409


# ─── Логін ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    """Успішний логін — отримання access + refresh токенів."""
    from app.core.security import hash_password
    user_with_hash = FAKE_USER.model_copy(
        update={"password_hash": hash_password("SecurePass1!")}
    )
    with patch(
        "app.repositories.user_repository.UserRepository.get_by_email",
        new_callable=AsyncMock,
        return_value=user_with_hash,
    ):
        resp = await client.post("/users/login", data={
            "username": "user@test.com",
            "password": "SecurePass1!",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Невірний пароль — 401."""
    from app.core.security import hash_password
    user_with_hash = FAKE_USER.model_copy(
        update={"password_hash": hash_password("CorrectPass1!")}
    )
    with patch(
        "app.repositories.user_repository.UserRepository.get_by_email",
        new_callable=AsyncMock,
        return_value=user_with_hash,
    ):
        resp = await client.post("/users/login", data={
            "username": "user@test.com",
            "password": "WrongPass1!",
        })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_blocked_user(client):
    """Заблокований користувач не може увійти — 403."""
    from app.core.security import hash_password
    blocked_user = FAKE_USER.model_copy(
        update={
            "password_hash": hash_password("SecurePass1!"),
            "status": "blocked",
        }
    )
    with patch(
        "app.repositories.user_repository.UserRepository.get_by_email",
        new_callable=AsyncMock,
        return_value=blocked_user,
    ):
        resp = await client.post("/users/login", data={
            "username": "user@test.com",
            "password": "SecurePass1!",
        })
    assert resp.status_code == 403


# ─── Захищені ендпоінти ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Без токена — 401."""
    resp = await client.get("/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(client):
    """З валідним токеном — повертає профіль."""
    token = make_user_token()
    with patch(
        "app.repositories.user_repository.UserRepository.get_by_id",
        new_callable=AsyncMock,
        return_value=FAKE_USER,
    ):
        resp = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


@pytest.mark.asyncio
async def test_get_all_users_forbidden_for_user(client):
    """USER не може отримати список всіх юзерів — 403."""
    token = make_user_token()
    resp = await client.get(
        "/users/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_all_users_allowed_for_admin(client):
    """ADMIN може отримати список всіх юзерів."""
    token = make_admin_token()
    with patch(
        "app.repositories.user_repository.UserRepository.get_all",
        new_callable=AsyncMock,
        return_value=[FAKE_USER],
    ), patch(
        "app.repositories.user_repository.UserRepository.count",
        new_callable=AsyncMock,
        return_value=1,
    ):
        resp = await client.get(
            "/users/",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] == 1