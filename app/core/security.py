
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """
    Хешує пароль за допомогою bcrypt.

    Args:
        password: Пароль у відкритому вигляді.

    Returns:
        Хешований пароль у форматі рядка.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Перевіряє відповідність пароля його хешу.

    Args:
        plain_password: Пароль у відкритому вигляді.
        hashed_password: Збережений хеш пароля.

    Returns:
        True якщо пароль відповідає хешу, інакше False.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Створює JWT-токен доступу.

    Args:
        data: Дані для кодування у токен (наприклад, sub, role).
        expires_delta: Час дії токена (за замовчуванням з конфігурації).

    Returns:
        Закодований JWT-токен у форматі рядка.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    token = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    logger.info("Створено JWT-токен для sub=%s", data.get("sub", "unknown"))
    return token


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Декодує та перевіряє JWT-токен.

    Args:
        token: JWT-токен для перевірки.

    Returns:
        Словник з даними токена або None при помилці.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        logger.warning("Помилка декодування JWT: %s", type(exc).__name__)
        return None