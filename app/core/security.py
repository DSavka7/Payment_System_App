
import re
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import InvalidCredentials, InsufficientPermissions

# OAuth2 scheme — точка входу для токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# ─────────────────────────────────────────────
# Константи ролей
# ─────────────────────────────────────────────
ROLE_USER = "USER"
ROLE_ADMIN = "ADMIN"

# ─────────────────────────────────────────────
# Валідація пароля
# ─────────────────────────────────────────────
PASSWORD_POLICY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,}$"
)


def validate_password_strength(password: str) -> None:
    """
    Перевіряє пароль на відповідність вимогам безпеки:
    - Мінімум 8 символів
    - Хоча б одна велика літера
    - Хоча б одна мала літера
    - Хоча б одна цифра
    - Хоча б один спеціальний символ

    Raises:
        HTTPException 422 якщо пароль не відповідає вимогам.
    """
    if not PASSWORD_POLICY_RE.match(password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Пароль має містити мінімум 8 символів, велику та малу літеру, "
                "цифру та спеціальний символ (!@#$%^&* тощо)"
            ),
        )


# ─────────────────────────────────────────────
# Хешування паролів
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Хешує пароль за допомогою bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Порівнює відкритий пароль із хешем."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ─────────────────────────────────────────────
# JWT токени
# ─────────────────────────────────────────────

def create_access_token(data: Dict) -> str:
    """Створює короткоживучий access token (JWT)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: Dict) -> str:
    """Створює довгоживучий refresh token (JWT)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise InvalidCredentials()


# ─────────────────────────────────────────────
# Dependency: поточний користувач із токена
# ─────────────────────────────────────────────

async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> Dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise InvalidCredentials()
    return payload


def require_role(*roles: str):
    async def _dependency(payload: Dict = Depends(get_current_user_payload)) -> Dict:
        if payload.get("role") not in roles:
            raise InsufficientPermissions()
        return payload

    return _dependency


require_user = require_role(ROLE_USER, ROLE_ADMIN)
require_admin = require_role(ROLE_ADMIN)