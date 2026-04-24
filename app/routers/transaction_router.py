"""
Роутер для управління транзакціями.
"""
from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.models.transaction_models import TransactionCreate, TransactionResponse
from app.services.transaction_service import TransactionService, get_transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової транзакції",
)
async def create_transaction(
    transaction: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Створює нову транзакцію між рахунками."""
    return await service.create_transaction(transaction)


@router.get(
    "/{tx_id}",
    response_model=TransactionResponse,
    summary="Отримання транзакції за ID",
)
async def get_transaction(
    tx_id: str,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    """Повертає деталі транзакції за її ідентифікатором."""
    return await service.get_transaction(tx_id)


@router.get(
    "/account/{account_id}",
    response_model=List[TransactionResponse],
    summary="Список транзакцій рахунку з пагінацією",
)
async def get_account_transactions(
    account_id: str,
    limit: int = Query(50, ge=1, le=100, description="Кількість записів на сторінку"),
    offset: int = Query(0, ge=0, description="Зміщення для пагінації"),
    service: TransactionService = Depends(get_transaction_service),
) -> List[TransactionResponse]:
    """Повертає список транзакцій рахунку з підтримкою пагінації (limit/offset)."""
    return await service.get_account_transactions(account_id, limit=limit, offset=offset)