from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.core.exceptions import InvalidToken, PermissionDenied
from app.core.constants import ADMIN_ROLE

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """Decode JWT and return payload dict."""
    payload = decode_access_token(token)
    if not payload:
        raise InvalidToken()
    return payload


def get_current_user_id(payload: dict = Depends(get_current_user_payload)) -> str:
    """Extract user_id (sub) from JWT payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidToken()
    return user_id


# Alias kept for backward compatibility
get_active_user_id = get_current_user_id


def get_active_user(user_id: str = Depends(get_current_user_id)) -> str:
    """Return current authenticated user_id."""
    return user_id


def require_admin(payload: dict = Depends(get_current_user_payload)) -> dict:
    """Require ADMIN role, raise PermissionDenied otherwise."""
    if payload.get("role") != ADMIN_ROLE:
        raise PermissionDenied()
    return payload