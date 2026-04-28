"""
Роутер для управління банківськими рахунками.
"""
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user_id
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import AccountService, get_account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового рахунку",
)
async def create_account(
    account: AccountCreate,
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Створює новий банківський рахунок для користувача."""
    return await service.create_account(account)


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Отримання рахунку за ID",
)
async def get_account(
    account_id: str,
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Повертає дані рахунку за його ідентифікатором."""
    return await service.get_account(account_id)


@router.get(
    "/user/{user_id}",
    response_model=List[AccountResponse],
    summary="Список рахунків користувача",
)
async def get_user_accounts(
    user_id: str,
    service: AccountService = Depends(get_account_service),
) -> List[AccountResponse]:
    """Повертає всі рахунки конкретного користувача."""
    return await service.get_user_accounts(user_id)


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Оновлення рахунку (статус / баланс)",
)
async def update_account(
    account_id: str,
    update_data: AccountUpdate,
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Оновлює статус або баланс рахунку."""
    return await service.update_account(account_id, update_data)


@router.patch(
    "/{account_id}/block",
    response_model=AccountResponse,
    summary="Самостійне блокування рахунку користувачем (PB-06)",
)
async def self_block_account(
    account_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """
    Дозволяє власнику рахунку самостійно заблокувати його.

    Рахунок повинен належати поточному авторизованому користувачу.
    Розблокування можливе лише через запит адміністратору (UNBLOCK request).
    """
    return await service.self_block_account(account_id, current_user_id)
