"""
Сервісний шар для управління користувачами.
Містить бізнес-логіку реєстрації, автентифікації та управління профілем.
"""
from typing import Dict, List

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import InvalidCredentials, InvalidToken, UserNotFound, UserInactive
from app.core.logging_config import get_logger
from app.core.security import verify_password, create_access_token, decode_access_token
from app.db.database import get_db
from app.models.user_models import UserCreate, UserResponse, UserUpdate
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserService:
    """
    Сервіс для управління користувачами.
    Реалізує бізнес-логіку реєстрації, входу та оновлення профілю.
    """

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user: UserCreate) -> UserResponse:
        """Реєструє нового користувача в системі."""
        user_in_db = await self.repo.create(user)
        logger.info("Зареєстровано нового користувача: email=%s, id=%s", user.email, user_in_db.id)
        return UserResponse.model_validate(user_in_db)

    async def authenticate(self, email: str, password: str) -> Dict:
        """
        Автентифікує користувача за email та паролем.

        Returns:
            Словник з access_token, refresh_token та token_type.

        Raises:
            InvalidCredentials: Якщо email або пароль невірні.
            UserInactive: Якщо обліковий запис заблоковано.
        """
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            logger.warning("Невдала спроба входу для email=%s", email)
            raise InvalidCredentials()

        if user.status != "active":
            logger.warning("Спроба входу заблокованого користувача id=%s", user.id)
            raise UserInactive()

        access_token = create_access_token({"sub": user.id, "role": user.role})
        refresh_token = create_access_token(
            {"sub": user.id, "role": user.role, "type": "refresh"},
            expires_delta=__import__("datetime").timedelta(days=7),
        )

        logger.info("Успішний вхід користувача id=%s", user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Видає новий access токен за дійсним refresh токеном (PB-03).

        Raises:
            InvalidToken: Якщо refresh токен недійсний або прострочений.
        """
        if not refresh_token:
            raise InvalidToken()

        payload = decode_access_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise InvalidToken()

        user_id = payload.get("sub")
        role = payload.get("role", "USER")

        new_access_token = create_access_token({"sub": user_id, "role": role})
        logger.info("Видано новий access токен для user_id=%s", user_id)
        return {"access_token": new_access_token, "token_type": "bearer"}

    async def logout(self, refresh_token: str) -> None:
        """
        Інвалідує refresh токен поточного сеансу.
        У поточній реалізації — stateless логаут (токен просто відкидається клієнтом).
        """
        logger.info("Користувач виконав вихід (refresh token invalidated)")

    async def get_user(self, user_id: str) -> UserResponse:
        """Отримує дані користувача за ID."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)

    async def get_all_users(self, limit: int = 50, offset: int = 0) -> List[UserResponse]:
        """
        Повертає список усіх користувачів (для адміністратора).

        Args:
            limit: Максимальна кількість записів.
            offset: Зміщення для пагінації.
        """
        users = await self.repo.get_all(limit=limit, offset=offset)
        return [UserResponse.model_validate(u) for u in users]

    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """Оновлює профіль користувача."""
        user = await self.repo.update(user_id, update_data)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: str) -> None:
        """Видаляє користувача з системи."""
        deleted = await self.repo.delete(user_id)
        if not deleted:
            raise UserNotFound()
        logger.info("Видалено користувача id=%s", user_id)


# ── Dependency Injection ──────────────────────────────────────────────────────

def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    """DI: повертає екземпляр UserRepository."""
    return UserRepository(db.users)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """DI: повертає екземпляр UserService."""
    return UserService(repo)
