"""
Конфігурація застосунку через Pydantic Settings.
Всі змінні середовища завантажуються з .env файлу.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Налаштування застосунку.
    Значення зчитуються з .env файлу або змінних середовища.
    Чутливі дані (паролі, ключі) ніколи не зберігаються у коді.
    """

    # База даних
    mongodb_url: str
    mongodb_db_name: str = "bank_db"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Застосунок
    app_title: str = "Payment System API"
    app_version: str = "1.0.0"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


# Єдиний глобальний екземпляр конфігурації (Singleton через модульну систему Python)
settings = Settings()