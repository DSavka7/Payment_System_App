
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_access_token          # ← правильна назва
from app.core.exceptions import InvalidToken, PermissionDenied, UserInactive, UserNotFound
from app.core.constants import ADMIN_ROLE
from app.db.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:

    payload = decode_access_token(token)
    if not payload:
        raise InvalidToken()
    return payload


def get_current_user_id(payload: dict = Depends(get_current_user_payload)) -> str:

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidToken()
    return user_id


async def get_active_user(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:

    from bson import ObjectId
    from bson.errors import InvalidId

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidToken()

    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise InvalidToken()

    doc = await db.users.find_one({"_id": oid})
    if not doc:
        raise UserNotFound()

    if doc.get("status") == "blocked":
        raise UserInactive()

    return payload


def require_admin(payload: dict = Depends(get_current_user_payload)) -> dict:

    if payload.get("role") != ADMIN_ROLE:
        raise PermissionDenied()
    return payload


def get_active_user_id(payload: dict = Depends(get_active_user)) -> str:
    return payload.get("sub")