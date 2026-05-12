"""
Роутер адміністративної панелі.
Всі ендпоінти захищені — доступні тільки користувачам з роллю ADMIN.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import require_admin
from app.models.admin_models import (
    AdminUserResponse,
    AdminUserStatusUpdate,
    AdminAccountStatusUpdate,
    AdminStatsResponse,
    AdminUserListResponse,
    AdminUserDetailsResponse,
    AdminAccountInfo,
)
from app.models.transaction_models import TransactionResponse, TransactionReviewUpdate
from app.services.admin_service import AdminService, get_admin_service

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


# ── Статистика ────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Зведена статистика системи",
)
async def get_stats(
    service: AdminService = Depends(get_admin_service),
) -> AdminStatsResponse:
    return await service.get_stats()


# ── Користувачі ───────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="Список усіх користувачів",
)
async def get_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(
        None, alias="status", pattern=r"^(active|blocked)$"
    ),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserListResponse:
    return await service.get_users(
        limit=limit, offset=offset, search=search, status_filter=status_filter,
    )


@router.get(
    "/users/{user_id}/details",
    response_model=AdminUserDetailsResponse,
    summary="Повні деталі користувача (профіль + рахунки + транзакції)",
    description=(
        "Повертає повну інформацію про користувача:\n"
        "- Профіль та статус\n"
        "- Всі банківські рахунки (можна блокувати через `/admin/accounts/{id}/status`)\n"
        "- Останні 20 транзакцій по всіх рахунках\n"
        "- Загальний баланс UAH"
    ),
)
async def get_user_details(
    user_id: str,
    service: AdminService = Depends(get_admin_service),
) -> AdminUserDetailsResponse:
    return await service.get_user_details(user_id)


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserResponse,
    summary="Заблокувати або розблокувати користувача",
    description=(
        "**Причина обов'язкова** (мінімум 5 символів).\n\n"
        "При блокуванні:\n"
        "- Причина зберігається і показується заблокованому користувачу\n"
        "- Всі подальші API-запити юзера повертають HTTP 403\n"
        "- Не можна заблокувати адміністратора або самого себе"
    ),
    responses={
        200: {"description": "Статус змінено"},
        403: {"description": "Не можна заблокувати адміна або свій акаунт"},
        404: {"description": "Користувача не знайдено"},
        422: {"description": "Причина не вказана або занадто коротка"},
    },
)
async def update_user_status(
    user_id: str,
    update: AdminUserStatusUpdate,
    payload: dict = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminUserResponse:
    return await service.update_user_status(user_id, update, payload.get("sub"))


# ── Рахунки (адмін-блокування) ────────────────────────────────────

@router.patch(
    "/accounts/{account_id}/status",
    response_model=AdminAccountInfo,
    summary="Заблокувати або розблокувати рахунок",
    description="Адміністратор може блокувати/розблоковувати окремі рахунки незалежно від статусу юзера.",
    responses={
        200: {"description": "Статус рахунку змінено"},
        404: {"description": "Рахунок не знайдено"},
    },
)
async def update_account_status(
    account_id: str,
    update: AdminAccountStatusUpdate,
    payload: dict = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> AdminAccountInfo:
    return await service.update_account_status(account_id, update, payload.get("sub"))


# ── Підозрілі транзакції ─────────────────────────────────────────

@router.get(
    "/suspicious",
    summary="Список підозрілих транзакцій",
    description=(
        "Транзакції що перевищують поріг:\n"
        "- UAH ≥ 50 000\n- USD ≥ 1 500\n- EUR ≥ 1 400\n\n"
        "Статус `pending_review` — очікують рішення адміністратора."
    ),
)
async def get_suspicious(
    status_filter: Optional[str] = Query(
        None, alias="status",
        pattern=r"^(pending_review|approved|rejected)$",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
):
    items, total = await service.get_suspicious_transactions(
        status_filter=status_filter, limit=limit, offset=offset,
    )
    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch(
    "/suspicious/{tx_id}/review",
    response_model=TransactionResponse,
    summary="Схвалити або відхилити підозрілу транзакцію",
    description=(
        "**approve** — кошти списуються і зараховуються.\n\n"
        "**reject** — переказ скасовується, кошти у відправника."
    ),
    responses={
        200: {"description": "Рішення прийнято"},
        403: {"description": "Транзакція вже розглянута"},
        404: {"description": "Підозрілу транзакцію не знайдено"},
    },
)
async def review_transaction(
    tx_id: str,
    review: TransactionReviewUpdate,
    payload: dict = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
) -> TransactionResponse:
    return await service.review_transaction(tx_id, review, payload.get("sub"))


# ── Всі запити ───────────────────────────────────────────────────

@router.get(
    "/requests",
    summary="Всі запити від усіх користувачів",
)
async def get_all_requests(
    status_filter: Optional[str] = Query(
        None, alias="status",
        pattern=r"^(pending|approved|rejected)$",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
):
    items, total = await service.get_all_requests(
        status_filter=status_filter, limit=limit, offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}