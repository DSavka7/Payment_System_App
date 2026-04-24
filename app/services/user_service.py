"""
Сервісний шар для управління користувачами.
Містить бізнес-логіку реєстрації, автентифікації та управління профілем.
"""
from typing import Dict

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import InvalidCredentials, UserNotFound, UserInactive
from app.core.logging_config import get_logger
from app.core.security import verify_password, create_access_token
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
        """
        Args:
            repo: Репозиторій для доступу до даних користувачів.
        """
        self.repo = repo

    async def create_user(self, user: UserCreate) -> UserResponse:
        """
        Реєструє нового користувача в системі.

        Args:
            user: Дані для реєстрації.

        Returns:
            Відповідь з даними створеного користувача.
        """
        user_in_db = await self.repo.create(user)
        logger.info(
            "Зареєстровано нового користувача: email=%s, id=%s",
            user.email,
            user_in_db.id,
        )
        return UserResponse.model_validate(user_in_db)

    async def authenticate(self, email: str, password: str) -> Dict:
        """
        Автентифікує користувача за email та паролем.

        Args:
            email: Email-адреса користувача.
            password: Пароль у відкритому вигляді.

        Returns:
            Словник з access_token та token_type.

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

        token = create_access_token({"sub": user.id, "role": user.role})
        logger.info("Успішний вхід користувача id=%s", user.id)
        return {"access_token": token, "token_type": "bearer"}

    async def get_user(self, user_id: str) -> UserResponse:
        """
        Отримує дані користувача за ID.

        Args:
            user_id: MongoDB ObjectId користувача.

        Returns:
            Відповідь з даними користувача.

        Raises:
            UserNotFound: Якщо користувача не знайдено.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserResponse:
        """
        Оновлює профіль користувача.

        Args:
            user_id: MongoDB ObjectId користувача.
            update_data: Поля для оновлення.

        Returns:
            Оновлена відповідь з даними користувача.

        Raises:
            UserNotFound: Якщо користувача не знайдено.
        """
        user = await self.repo.update(user_id, update_data)
        if not user:
            raise UserNotFound()
        return UserResponse.model_validate(user)


# ──────────────────────────────────────────────
# Dependency Injection
# ──────────────────────────────────────────────

def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    """DI: повертає екземпляр UserRepository."""
    return UserRepository(db.users)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """DI: повертає екземпляр UserService."""
    return UserService(repo)