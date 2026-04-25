from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.core.exceptions import InvalidCredentials, Forbidden
from app.core.constants import ADMIN_ROLE

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """Декодує JWT-токен і повертає payload. Кидає 401 якщо токен невалідний."""
    payload = decode_access_token(token)
    if not payload:
        raise InvalidCredentials()
    return payload


def get_current_user_id(payload: dict = Depends(get_current_user_payload)) -> str:
    """Витягує user_id (sub) з payload токена."""
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidCredentials()
    return user_id


def require_admin(payload: dict = Depends(get_current_user_payload)) -> dict:
    """Перевіряє що поточний користувач є адміністратором."""
    if payload.get("role") != ADMIN_ROLE:
        raise Forbidden()
    return payload