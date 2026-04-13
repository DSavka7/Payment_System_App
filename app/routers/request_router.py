
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user_id, require_admin
from app.models.request_models import RequestCreate, RequestResponse, RequestUpdate
from app.services.request_service import RequestService, get_request_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post(
    "/",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запит / Create request",
)
async def create_request(
    request: RequestCreate,
    service: RequestService = Depends(get_request_service),
    _: str = Depends(get_current_user_id),
) -> RequestResponse:
    """Створює новий запит до адміністратора."""
    return await service.create_request(request)


@router.get(
    "/user/{user_id}",
    response_model=List[RequestResponse],
    summary="Запити користувача / User requests",
)
async def get_user_requests(
    user_id: str,
    service: RequestService = Depends(get_request_service),
    _: str = Depends(get_current_user_id),
) -> List[RequestResponse]:
    """Повертає всі запити вказаного користувача."""
    return await service.get_user_requests(user_id)


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    summary="Отримати запит / Get request",
)
async def get_request(
    request_id: str,
    service: RequestService = Depends(get_request_service),
    _: str = Depends(get_current_user_id),
) -> RequestResponse:
    """Повертає запит за ID."""
    return await service.get_request(request_id)


@router.patch(
    "/{request_id}/status",
    response_model=RequestResponse,
    summary="Оновити статус запиту / Update request status",
)
async def update_request_status(
    request_id: str,
    update: RequestUpdate,
    service: RequestService = Depends(get_request_service),
    _: dict = Depends(require_admin),
) -> RequestResponse:
    """Оновлює статус запиту (тільки для адміністраторів)."""
    return await service.update_request_status(request_id, update)