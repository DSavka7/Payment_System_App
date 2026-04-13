
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.repositories.user_repository import UserRepository
from app.models.user_models import UserCreate, UserUpdate
from app.core.exceptions import UserAlreadyExists


def make_user_doc(email: str = "test@example.com") -> dict:
    """Створює тестовий документ користувача."""
    oid = ObjectId()
    return {
        "_id": oid,
        "email": email,
        "phone": "+380991234567",
        "role": "USER",
        "password_hash": "$2b$12$fakehash",
        "status": "active",
        "created_at": datetime.utcnow(),
    }


@pytest.mark.asyncio
class TestUserRepository:

    async def test_create_user_success(self, mock_user_collection):
        """Успішне створення користувача."""
        mock_user_collection.find_one = AsyncMock(return_value=None)
        inserted_id = ObjectId()
        mock_user_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=inserted_id)
        )

        repo = UserRepository(mock_user_collection)
        user_create = UserCreate(
            email="new@example.com",
            phone="+380991234567",
            password="password123",
        )
        result = await repo.create(user_create)

        assert result.email == "new@example.com"
        assert result.status == "active"
        assert result.id is not None

    async def test_create_user_already_exists(self, mock_user_collection):
        """Якщо email вже зайнятий — кидає UserAlreadyExists."""
        mock_user_collection.find_one = AsyncMock(
            return_value=make_user_doc("existing@example.com")
        )
        repo = UserRepository(mock_user_collection)
        user_create = UserCreate(
            email="existing@example.com",
            phone="+380991234567",
            password="password123",
        )
        with pytest.raises(UserAlreadyExists):
            await repo.create(user_create)

    async def test_get_by_id_found(self, mock_user_collection):
        """Повертає користувача якщо він існує."""
        doc = make_user_doc()
        mock_user_collection.find_one = AsyncMock(return_value=doc)

        repo = UserRepository(mock_user_collection)
        result = await repo.get_by_id(str(doc["_id"]))

        assert result is not None
        assert result.email == "test@example.com"

    async def test_get_by_id_not_found(self, mock_user_collection):
        """Повертає None якщо користувача не існує."""
        mock_user_collection.find_one = AsyncMock(return_value=None)
        repo = UserRepository(mock_user_collection)
        result = await repo.get_by_id(str(ObjectId()))
        assert result is None

    async def test_get_by_email_found(self, mock_user_collection):
        """Повертає користувача за email."""
        doc = make_user_doc("find@example.com")
        mock_user_collection.find_one = AsyncMock(return_value=doc)

        repo = UserRepository(mock_user_collection)
        result = await repo.get_by_email("find@example.com")

        assert result is not None
        assert result.email == "find@example.com"

    async def test_delete_existing_user(self, mock_user_collection):
        """Видалення існуючого користувача повертає True."""
        mock_user_collection.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=1)
        )
        repo = UserRepository(mock_user_collection)
        result = await repo.delete(str(ObjectId()))
        assert result is True

    async def test_delete_nonexistent_user(self, mock_user_collection):
        """Видалення неіснуючого користувача повертає False."""
        mock_user_collection.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=0)
        )
        repo = UserRepository(mock_user_collection)
        result = await repo.delete(str(ObjectId()))
        assert result is False