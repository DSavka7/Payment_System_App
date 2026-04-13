
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from jose import JWTError, ExpiredSignatureError, jwt

from app.core.config import settings
from app.core.exceptions import TokenExpired, InvalidToken


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def _create_token(data: Dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(data: Dict) -> str:
    return _create_token(
        data,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(data: Dict) -> str:
    payload = {**data, "type": "refresh"}
    return _create_token(
        payload,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> Dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError:
        raise TokenExpired()
    except JWTError:
        raise InvalidToken()


def get_user_id_from_token(token: str) -> str:
    payload = decode_token(token)
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise InvalidToken()
    return user_id