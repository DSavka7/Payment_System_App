
import logging
from fastapi import APIRouter, Depends, status, Query
from typing import Optional, Dict

from app.services.request_service import RequestService, get_request_service
from app.models.request_models import (
    RequestCreate,
    RequestResponse,
    RequestUpdate,
    PaginatedRequests,
)
from app.core.security import require_user, require_admin
from app.core.config import settings

router = APIRouter(prefix="/requests", tags=["requests"])
logger = logging.getLogger(__name__)


# ─── USER ендпоінти ───────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запит до адміністратора",
)
async def create_request(
    request: RequestCreate,
    payload: Dict = Depends(require_user),
    service: RequestService = Depends(get_request_service),
):
    return await service.create_request(user_id=payload["sub"], request=request)


@router.get(
    "/my",
    response_model=PaginatedRequests,
    summary="Мої запити",
)
async def get_my_requests(
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(0, ge=0),
    payload: Dict = Depends(require_user),
    service: RequestService = Depends(get_request_service),
):
    """Пагінований список запитів поточного авторизованого користувача."""
    return await service.get_my_requests(
        user_id=payload["sub"], limit=limit, offset=offset
    )


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    summary="Отримати запит за ID",
)
async def get_request(
    request_id: str,
    payload: Dict = Depends(require_user),
    service: RequestService = Depends(get_request_service),
):
    return await service.get_request(
        request_id=request_id,
        user_id=payload["sub"],
        role=payload["role"],
    )


# ─── ADMIN ендпоінти ──────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=PaginatedRequests,
    summary="[ADMIN] Всі запити",
)
async def get_all_requests(
    status: Optional[str] = Query(
        None,
        pattern=r"^(pending|approved|rejected)$",
        description="Фільтр по статусу",
    ),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(0, ge=0),
    payload: Dict = Depends(require_admin),
    service: RequestService = Depends(get_request_service),
):

    return await service.get_all_requests(
        status=status, limit=limit, offset=offset
    )


@router.patch(
    "/{request_id}/status",
    response_model=RequestResponse,
    summary="[ADMIN] Схвалити або відхилити запит",
)
async def update_request_status(
    request_id: str,
    update: RequestUpdate,
    payload: Dict = Depends(require_admin),
    service: RequestService = Depends(get_request_service),
):
    """
    Адмін схвалює або відхиляє запит.

    При **approved**:
    - UNBLOCK → рахунок автоматично розблоковується
    - LIMIT_CHANGE → добовий ліміт рахунку оновлюється

    При **rejected** — жодних змін на рахунку не відбувається.
    """
    return await service.update_request_status(
        request_id=request_id,
        update=update,
        admin_id=payload["sub"],
    )