"""
Роутер для управління банківськими рахунками.
Всі операції вимагають активного (не заблокованого) користувача.
"""
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_active_user, get_active_user_id
from app.models.account_models import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    TransferRequest,
)
from app.models.transaction_models import TransactionResponse
from app.services.account_service import AccountService, get_account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового рахунку",
    description="Заблокований користувач не може створювати нові рахунки.",
)
async def create_account(
    account: AccountCreate,
    _: dict = Depends(get_active_user),  # перевірка що юзер не заблокований
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Створює новий банківський рахунок."""
    return await service.create_account(account)


@router.post(
    "/transfer",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Переказ коштів між рахунками",
    description=(
        "Виконує переказ коштів. **Заблокований користувач не може робити перекази.**\n\n"
        "Переказ буде відхилено якщо:\n"
        "- Користувач або рахунок заблоковано (HTTP 403)\n"
        "- Валюти рахунків не збігаються (HTTP 400)\n"
        "- Недостатньо коштів (HTTP 400)\n"
        "- Переказ на той самий рахунок (HTTP 403)\n\n"
        "**Підозрілі перекази** (UAH ≥ 50 000 / USD ≥ 1 500 / EUR ≥ 1 400) "
        "отримують статус `pending_review` і потребують схвалення адміністратора. "
        "Кошти при цьому НЕ списуються одразу."
    ),
    responses={
        200: {"description": "Переказ виконано або відправлено на перевірку"},
        400: {"description": "Недостатньо коштів або невідповідність валют"},
        403: {"description": "Заблоковано: користувач, рахунок або самопереказ"},
        404: {"description": "Рахунок не знайдено"},
    },
)
async def transfer(
    request: TransferRequest,
    payload: dict = Depends(get_active_user),
    service: AccountService = Depends(get_account_service),
) -> TransactionResponse:
    """Переказ коштів (з перевіркою статусу користувача та рахунків)."""
    user_id = payload.get("sub")
    return await service.transfer(request, user_id)


@router.get(
    "/user/{user_id}",
    response_model=List[AccountResponse],
    summary="Список рахунків користувача",
)
async def get_user_accounts(
    user_id: str,
    _: dict = Depends(get_active_user),
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
    _: dict = Depends(get_active_user),
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
    _: dict = Depends(get_active_user),
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Оновлює статус або баланс рахунку."""
    return await service.update_account(account_id, update_data)