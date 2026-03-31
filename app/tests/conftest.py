
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.main import app
from app.models.user_models import UserInDB, UserResponse, TokenResponse
from app.models.account_models import AccountInDB, AccountResponse
from app.models.request_models import RequestInDB, RequestResponse


# ─── Тестові дані ─────────────────────────────────────────────────────────────

FAKE_USER_ID = "507f1f77bcf86cd799439011"
FAKE_ACCOUNT_ID = "507f1f77bcf86cd799439022"
FAKE_REQUEST_ID = "507f1f77bcf86cd799439033"
FAKE_ADMIN_ID = "507f1f77bcf86cd799439044"

FAKE_NOW = datetime(2024, 1, 15, 12, 0, 0)

FAKE_USER = UserInDB(
    id=FAKE_USER_ID,
    email="user@test.com",
    phone="+380991234567",
    first_name="Тест",
    last_name="Юзер",
    role="USER",
    password_hash="$2b$12$fake_hash",
    status="active",
    created_at=FAKE_NOW,
)

FAKE_ADMIN = UserInDB(
    id=FAKE_ADMIN_ID,
    email="admin@test.com",
    phone="+380991234568",
    first_name="Адмін",
    last_name="Системний",
    role="ADMIN",
    password_hash="$2b$12$fake_hash",
    status="active",
    created_at=FAKE_NOW,
)

FAKE_ACCOUNT = AccountInDB(
    id=FAKE_ACCOUNT_ID,
    user_id=FAKE_USER_ID,
    card_number="5375 **** **** 1234",
    currency="UAH",
    balance=1000.0,
    status="active",
    daily_limit=None,
    created_at=FAKE_NOW,
)

FAKE_ACCOUNT_BLOCKED = AccountInDB(
    id=FAKE_ACCOUNT_ID,
    user_id=FAKE_USER_ID,
    card_number="5375 **** **** 1234",
    currency="UAH",
    balance=1000.0,
    status="blocked",
    daily_limit=None,
    created_at=FAKE_NOW,
)


# ─── Фікстури клієнта ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """HTTP-клієнт для тестування FastAPI без реального сервера."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


def make_user_token(user_id: str = FAKE_USER_ID, role: str = "USER") -> str:
    """Генерує реальний JWT токен для тестів."""
    from app.core.security import create_access_token
    return create_access_token({"sub": user_id, "role": role})


def make_admin_token() -> str:
    """Генерує реальний JWT токен адміна для тестів."""
    return make_user_token(user_id=FAKE_ADMIN_ID, role="ADMIN")