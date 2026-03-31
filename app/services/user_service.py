import logging
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, List

from app.repositories.user_repository import UserRepository
from app.models.user_models import UserCreate, UserResponse, UserUpdate, TokenResponse
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import UserNotFound, InvalidCredentials, UserBlocked, InsufficientPermissions
from app.db.database import get_db

logger = logging.getLogger(__name__)


class UserService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user: UserCreate) -> UserResponse:
        """Реєстрація нового користувача з хешуванням пароля."""
        user_in_db = await self.repo.create(user)
        logger.info("Зареєстровано нового користувача: %s", user.email)
        return UserResponse.model_validate(user_in_db.model_dump())

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            logger.warning("Невдала спроба входу для email: %s", email)
            raise InvalidCredentials()

        if user.status != "active":
            logger.warning("Спроба входу заблокованого користувача: %s", email)
            raise UserBlocked()

        token_data = {"sub": user.id, "role": user.role}
        logger.info("Успішний вхід: %s (роль: %s)", email, user.role)

        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        from app.core.exceptions import InvalidCredentials
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidCredentials()

        user = await self.repo.get_by_id(payload["sub"])
        if not user or user.status != "active":
            raise InvalidCredentials()

        token_data = {"sub": user.id, "role": user.role}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def get_user(self, user_id: str) -> UserResponse:
        """Отримати публічний профіль користувача за ID."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user.model_dump())

    async def get_all_users(self, limit: int, offset: int) -> Dict:
        """Повертає пагінований список всіх користувачів (тільки для ADMIN)."""
        users = await self.repo.get_all(limit=limit, offset=offset)
        total = await self.repo.count()
        return {
            "items": [UserResponse.model_validate(u.model_dump()) for u in users],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
        }

    async def block_user(self, admin_id: str, user_id: str) -> UserResponse:
        """Блокує користувача (тільки ADMIN, не може заблокувати себе)."""
        if admin_id == user_id:
            raise InsufficientPermissions()
        updated = await self.repo.update(user_id, UserUpdate(status="blocked"))
        if not updated:
            raise UserNotFound()
        logger.info("Адмін %s заблокував користувача %s", admin_id, user_id)
        return UserResponse.model_validate(updated.model_dump())

    async def unblock_user(self, admin_id: str, user_id: str) -> UserResponse:
        """Розблоковує користувача (тільки ADMIN)."""
        updated = await self.repo.update(user_id, UserUpdate(status="active"))
        if not updated:
            raise UserNotFound()
        logger.info("Адмін %s розблокував користувача %s", admin_id, user_id)
        return UserResponse.model_validate(updated.model_dump())

    async def update_profile(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """Оновлює профіль користувача (тільки безпечні поля)."""
        # Не дозволяємо змінювати статус через цей метод
        safe_update = UserUpdate(
            phone=update_data.phone,
            first_name=update_data.first_name,
            last_name=update_data.last_name,
        )
        updated = await self.repo.update(user_id, safe_update)
        if not updated:
            raise UserNotFound()
        return UserResponse.model_validate(updated.model_dump())


# ─── Dependency Injection ──────────────────────────────────────────────────────

def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db.users)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)