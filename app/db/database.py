"""
Модуль підключення до MongoDB через Motor (асинхронний драйвер).
Реалізує патерн Singleton для підключення до бази даних.
"""
import pymongo
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class Database:
    """
    Singleton-клас для управління підключенням до MongoDB.
    Забезпечує єдине підключення протягом всього часу роботи застосунку.
    """

    client: AsyncIOMotorClient
    db: AsyncIOMotorDatabase

    def __init__(self):
        """Ініціалізує підключення до MongoDB з налаштувань конфігурації."""
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.client[settings.mongodb_db_name]

    # ──────────────────────────────────────────────
    # Властивості для зручного доступу до колекцій
    # ──────────────────────────────────────────────

    @property
    def users(self):
        """Колекція користувачів."""
        return self.db.users

    @property
    def accounts(self):
        """Колекція банківських рахунків."""
        return self.db.accounts

    @property
    def transactions(self):
        """Колекція транзакцій."""
        return self.db.transactions

    @property
    def requests(self):
        """Колекція запитів на операції."""
        return self.db.requests

    async def create_indexes(self) -> None:
        """
        Безпечно створює або перевіряє індекси у всіх колекціях.
        При наявності конфлікту — пропускає індекс з попередженням.
        """
        logger.info("Початок створення/перевірки індексів у MongoDB...")

        try:
            await self.users.create_index("email", unique=True, name="unique_email")
            await self.accounts.create_index(
                [("user_id", pymongo.ASCENDING), ("card_number", pymongo.ASCENDING)],
                unique=True,
                name="unique_user_card",
            )

            indexes = [
                ("users", "role", "idx_user_role"),
                ("accounts", "user_id", "idx_account_user"),
                ("accounts", "status", "idx_account_status"),
                ("transactions", "created_at", "idx_transaction_date"),
                ("transactions", "from_account_id", "idx_from_account"),
                ("transactions", "to_account_id", "idx_to_account"),
                (
                    "requests",
                    [("user_id", pymongo.ASCENDING), ("status", pymongo.ASCENDING)],
                    "idx_request_user_status",
                ),
                ("requests", "created_at", "idx_request_date"),
            ]

            for collection_name, key, name in indexes:
                collection = getattr(self, collection_name)
                try:
                    if isinstance(key, list):
                        await collection.create_index(key, name=name, background=True)
                    else:
                        await collection.create_index(key, name=name, background=True)
                except Exception as exc:
                    if "IndexOptionsConflict" in str(exc) or "already exists" in str(exc):
                        logger.debug("Індекс %s вже існує — пропускаємо", name)
                    else:
                        logger.error("Помилка при створенні індексу %s: %s", name, exc)

            logger.info("Індекси успішно перевірені / створені")

        except Exception as exc:
            logger.critical("Загальна помилка при створенні індексів: %s", exc)

    async def close(self) -> None:
        """Закриває підключення до MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Підключення до MongoDB закрито")


# Глобальний Singleton-екземпляр бази даних
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan-менеджер FastAPI.
    Виконує ініціалізацію при старті та очищення при зупинці.
    """
    # === STARTUP ===
    try:
        await db.client.admin.command("ping")
        logger.info("Успішно підключено до MongoDB: %s", settings.mongodb_db_name)
        await db.create_indexes()
    except Exception as exc:
        logger.critical("Критична помилка підключення до MongoDB: %s", exc)
        raise

    yield

    # === SHUTDOWN ===
    await db.close()


async def get_db() -> AsyncIOMotorDatabase:
    """
    Dependency Injection для отримання екземпляра бази даних.

    Returns:
        Асинхронний об'єкт бази даних Motor.
    """
    return db.db