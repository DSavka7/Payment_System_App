from fastapi import APIRouter, Depends, status, Query
from typing import List

from app.services.transaction_service import TransactionService, get_transaction_service
from app.models.transaction_models import TransactionCreate, TransactionResponse


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    return await service.create_transaction(transaction)


@router.get("/{tx_id}", response_model=TransactionResponse)
async def get_transaction(
    tx_id: str,
    service: TransactionService = Depends(get_transaction_service)
):
    return await service.get_transaction(tx_id)


@router.get("/account/{account_id}", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: str,
    limit: int = Query(50, ge=1, le=100),
    service: TransactionService = Depends(get_transaction_service)
):
    return await service.get_account_transactions(account_id, limit)