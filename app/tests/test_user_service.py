
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.user_service import UserService
from app.models.user_models import UserCreate, UserInDB
from app.core.exceptions import InvalidCredentials, UserNotFound
from app.core.security import hash_password


def make_user_in_db(
    user_id: str = "aaa000000000000000000001",
    email: str = "user@example.com",
    password: str = "password123",
    role: str = "USER",
) -> UserInDB:
    return UserInDB(
        id=user_id,
        email=email,
        phone="+380991234567",
        role=role,
        password_hash=hash_password(password),
        status="active",
        created_at=datetime.utcnow(),
    )


def make_service(repo=None, db=None) -> UserService:
    if repo is None:
        repo = MagicMock()
    if db is None:
        db = MagicMock()
        db.refresh_tokens = MagicMock()
        db.refresh_tokens.insert_one = AsyncMock()
        db.refresh_tokens.find_one = AsyncMock(return_value=None)
        db.refresh_tokens.delete_one = AsyncMock()
    return UserService(repo, db)


@pytest.mark.asyncio
class TestUserServiceAuth:

    async def test_authenticate_success(self):
        """Успішна автентифікація повертає access та refresh токени."""
        user = make_user_in_db(password="mypassword")
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=user)

        db = MagicMock()
        db.refresh_tokens = MagicMock()
        db.refresh_tokens.insert_one = AsyncMock()

        service = UserService(repo, db)
        result = await service.authenticate("user@example.com", "mypassword")

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    async def test_authenticate_wrong_password(self):
        """Невірний пароль → InvalidCredentials."""
        user = make_user_in_db(password="correct")
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=user)

        service = make_service(repo)
        with pytest.raises(InvalidCredentials):
            await service.authenticate("user@example.com", "wrong")

    async def test_authenticate_user_not_found(self):
        """Email не існує → InvalidCredentials."""
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=None)

        service = make_service(repo)
        with pytest.raises(InvalidCredentials):
            await service.authenticate("ghost@example.com", "pass")

    async def test_create_user_returns_response(self):
        """create_user повертає UserResponse."""
        user = make_user_in_db()
        repo = MagicMock()
        repo.create = AsyncMock(return_value=user)

        service = make_service(repo)
        result = await service.create_user(UserCreate(
            email="user@example.com",
            phone="+380991234567",
            password="password123",
        ))
        assert result.email == "user@example.com"
        assert result.status == "active"

    async def test_get_user_not_found(self):
        """get_user кидає UserNotFound якщо користувача нема."""
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)

        service = make_service(repo)
        with pytest.raises(UserNotFound):
            await service.get_user("nonexistent")

    async def test_get_user_success(self):
        """get_user повертає UserResponse."""
        user = make_user_in_db()
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=user)

        service = make_service(repo)
        result = await service.get_user(user.id)
        assert result.id == user.id

    async def test_delete_user_not_found(self):
        """delete_user кидає UserNotFound якщо користувача нема."""
        repo = MagicMock()
        repo.delete = AsyncMock(return_value=False)

        service = make_service(repo)
        with pytest.raises(UserNotFound):
            await service.delete_user("nonexistent")

    async def test_logout_deletes_token(self):
        """logout видаляє refresh token з БД."""
        repo = MagicMock()
        db = MagicMock()
        db.refresh_tokens = MagicMock()
        db.refresh_tokens.delete_one = AsyncMock()

        service = UserService(repo, db)
        await service.logout("some.refresh.token")

        db.refresh_tokens.delete_one.assert_called_once_with(
            {"token": "some.refresh.token"}
        )