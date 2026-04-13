from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_token
from app.core.exceptions import InvalidToken, PermissionDenied
from app.core.constants import ADMIN_ROLE

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    return decode_token(token)


def get_current_user_id(payload: dict = Depends(get_current_user_payload)) -> str:
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidToken()
    return user_id


def require_admin(payload: dict = Depends(get_current_user_payload)) -> dict:
    if payload.get("role") != ADMIN_ROLE:
        raise PermissionDenied()
    return payload