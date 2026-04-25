"""
Роутер для управління банківськими рахунками.
"""
from typing import List

from fastapi import APIRouter, Depends, status

from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate
from app.models.account_models import TransferRequest, TransactionResponse
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


@router.post(
    "/transfer",
    summary="Переказ коштів між рахунками",
)
async def transfer(
    transfer_data: TransferRequest,
    service: AccountService = Depends(get_account_service),
):
    """Виконує переказ коштів між рахунками."""
    return await service.transfer(transfer_data)


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


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення рахунку",
)
async def delete_account(
    account_id: str,
    service: AccountService = Depends(get_account_service),
):
    """Видаляє банківський рахунок."""
    await service.delete_account(account_id)