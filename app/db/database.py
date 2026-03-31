from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import AsyncGenerator

from app.core.config import settings


class Database:
    client: AsyncIOMotorClient
    db: AsyncIOMotorDatabase

    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.client[settings.mongodb_db_name]

    # ==================== Властивості для зручного доступу ====================
    @property
    def users(self):
        return self.db.users

    @property
    def accounts(self):
        return self.db.accounts

    @property
    def transactions(self):
        return self.db.transactions

    @property
    def requests(self):
        return self.db.requests

    # ==================== Безпечне створення індексів ====================
    async def create_indexes(self):

        print("Початок створення/перевірки індексів у MongoDB...")

        try:
            # Унікальні індекси (з dropDuplicates=False за замовчуванням)
            await self.users.create_index("email", unique=True, name="unique_email")
            await self.accounts.create_index(
                [("user_id", pymongo.ASCENDING), ("card_number", pymongo.ASCENDING)],
                unique=True,
                name="unique_user_card"
            )


            indexes = [
                ("users", "role", "idx_user_role"),
                ("accounts", "user_id", "idx_account_user"),
                ("accounts", "status", "idx_account_status"),
                ("transactions", "created_at", "idx_transaction_date"),
                ("transactions", "from_account_id", "idx_from_account"),
                ("transactions", "to_account_id", "idx_to_account"),
                ("requests", [("user_id", pymongo.ASCENDING), ("status", pymongo.ASCENDING)], "idx_request_user_status"),
                ("requests", "created_at", "idx_request_date"),
            ]

            for collection_name, key, name in indexes:
                collection = getattr(self, collection_name)
                try:
                    if isinstance(key, list):
                        await collection.create_index(key, name=name, background=True)
                    else:
                        await collection.create_index(key, name=name, background=True)
                except Exception as e:
                    if "IndexOptionsConflict" in str(e) or "already exists" in str(e):
                        print(f"   ⏭ Індекс {name} вже існує з іншою назвою — пропускаємо")
                    else:
                        print(f"   Помилка при створенні індексу {name}: {e}")

            print("Індекси успішно перевірені / створені")

        except Exception as e:
            print(f"Загальна помилка при створенні індексів: {e}")

    async def close(self):

        if self.client:
            self.client.close()


# Глобальний екземпляр
db = Database()


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # === STARTUP ===
    try:
        await db.client.admin.command('ping')
        print("Успішно підключено до MongoDB")
        await db.create_indexes()

    except Exception as e:
        print(f"Критична помилка підключення до MongoDB: {e}")
        raise

    yield

    # === SHUTDOWN ===
    db.close()
    print("Підключення до MongoDB закрито")


async def get_db() -> AsyncIOMotorDatabase:
    """Dependency Injection для бази даних"""
    return db.db