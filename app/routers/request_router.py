"""
Роутер для управління запитами на операції з рахунками.
"""
from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.models.request_models import RequestCreate, RequestResponse, RequestUpdate
from app.services.request_service import RequestService, get_request_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post(
    "/",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового запиту",
)
async def create_request(
    request: RequestCreate,
    service: RequestService = Depends(get_request_service),
) -> RequestResponse:
    """Створює новий запит на операцію з рахунком (блокування/розблокування)."""
    return await service.create_request(request)


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    summary="Отримання запиту за ID",
)
async def get_request(
    request_id: str,
    service: RequestService = Depends(get_request_service),
) -> RequestResponse:
    """Повертає деталі запиту за його ідентифікатором."""
    return await service.get_request(request_id)


@router.get(
    "/user/{user_id}",
    response_model=List[RequestResponse],
    summary="Список запитів користувача з пагінацією",
)
async def get_user_requests(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Кількість записів на сторінку"),
    offset: int = Query(0, ge=0, description="Зміщення для пагінації"),
    service: RequestService = Depends(get_request_service),
) -> List[RequestResponse]:
    """Повертає всі запити користувача з підтримкою пагінації."""
    return await service.get_user_requests(user_id, limit=limit, offset=offset)


@router.patch(
    "/{request_id}/status",
    response_model=RequestResponse,
    summary="Оновлення статусу запиту (адмін)",
)
async def update_request_status(
    request_id: str,
    update: RequestUpdate,
    service: RequestService = Depends(get_request_service),
) -> RequestResponse:
    """Змінює статус запиту (для адміністратора)."""
    return await service.update_request_status(request_id, update)