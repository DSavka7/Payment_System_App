import logging
from fastapi import APIRouter, Depends, status, Query
from typing import List, Dict

from app.services.account_service import AccountService, get_account_service
from app.models.account_models import AccountCreate, AccountResponse, AccountUpdate
from app.core.security import require_user, require_admin
from app.core.config import settings

router = APIRouter(prefix="/accounts", tags=["accounts"])
logger = logging.getLogger(__name__)


# ─── USER ендпоінти ───────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити рахунок",
)
async def create_account(
    account: AccountCreate,
    payload: Dict = Depends(require_user),
    service: AccountService = Depends(get_account_service),
):

    return await service.create_account(user_id=payload["sub"], account=account)


@router.get(
    "/my",
    response_model=List[AccountResponse],
    summary="Мої рахунки",
)
async def get_my_accounts(
    payload: Dict = Depends(require_user),
    service: AccountService = Depends(get_account_service),
):
    """Повертає всі рахунки поточного авторизованого користувача."""
    return await service.get_my_accounts(user_id=payload["sub"])


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Отримати рахунок за ID",
)
async def get_account(
    account_id: str,
    payload: Dict = Depends(require_user),
    service: AccountService = Depends(get_account_service),
):
    """
    Повертає рахунок за ID.
    USER бачить тільки свій рахунок. ADMIN бачить будь-який.
    """
    return await service.get_account(
        account_id=account_id,
        requester_id=payload["sub"],
        requester_role=payload["role"],
    )


@router.patch(
    "/{account_id}/block",
    response_model=AccountResponse,
    summary="Заблокувати свій рахунок (self-block)",
)
async def self_block_account(
    account_id: str,
    payload: Dict = Depends(require_user),
    service: AccountService = Depends(get_account_service),
):
    """
    Користувач самостійно блокує СВІЙ рахунок.

    **Важливо:** після блокування розблокувати рахунок самостійно НЕМОЖЛИВО.
    Для розблокування необхідно подати запит до адміністратора
    через `POST /requests/` з типом `UNBLOCK`.

    Помилки:
    - 403 — рахунок не належить поточному користувачу
    - 409 — рахунок вже заблоковано
    """
    return await service.self_block_account(
        account_id=account_id,
        user_id=payload["sub"],
    )


# ─── ADMIN ендпоінти ──────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="[ADMIN] Список всіх рахунків",
)
async def get_all_accounts(
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    offset: int = Query(0, ge=0),
    payload: Dict = Depends(require_admin),
    service: AccountService = Depends(get_account_service),
):
    """Пагінований список усіх рахунків. Тільки для ADMIN."""
    return await service.get_all_accounts(limit=limit, offset=offset)


@router.get(
    "/user/{user_id}",
    response_model=List[AccountResponse],
    summary="[ADMIN] Рахунки користувача",
)
async def get_user_accounts(
    user_id: str,
    payload: Dict = Depends(require_admin),
    service: AccountService = Depends(get_account_service),
):
    """Повертає рахунки конкретного користувача за user_id. Тільки для ADMIN."""
    return await service.get_user_accounts_admin(user_id=user_id)


@router.patch(
    "/{account_id}/admin-block",
    response_model=AccountResponse,
    summary="[ADMIN] Заблокувати рахунок",
)
async def admin_block_account(
    account_id: str,
    payload: Dict = Depends(require_admin),
    service: AccountService = Depends(get_account_service),
):
    return await service.block_account(account_id)


@router.patch(
    "/{account_id}/unblock",
    response_model=AccountResponse,
    summary="[ADMIN] Розблокувати рахунок",
)
async def unblock_account(
    account_id: str,
    payload: Dict = Depends(require_admin),
    service: AccountService = Depends(get_account_service),
):
    return await service.unblock_account(account_id)


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="[ADMIN] Оновити параметри рахунку",
)
async def update_account(
    account_id: str,
    update_data: AccountUpdate,
    payload: Dict = Depends(require_admin),
    service: AccountService = Depends(get_account_service),
):
    """Оновлює баланс або добовий ліміт рахунку. Тільки для ADMIN."""
    return await service.update_account(account_id, update_data)