
from fastapi import HTTPException, status
from typing import Optional


class BaseAppException(HTTPException):

    def __init__(self, status_code: int, detail: str, headers: Optional[dict] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# ──────────────────────────────────────────────
# Помилки автентифікації / авторизації
# ──────────────────────────────────────────────

class InvalidCredentials(BaseAppException):
    """Невірний email або пароль при вході."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні дані для входу",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidToken(BaseAppException):
    """JWT-токен відсутній або некоректний."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некоректний токен автентифікації",
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDenied(BaseAppException):
    """Недостатньо прав (не адміністратор)."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ заборонено: потрібні права адміністратора",
        )


class TokenExpired(BaseAppException):
    """JWT-токен прострочений."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен прострочений",
            headers={"WWW-Authenticate": "Bearer"},
        )


class Forbidden(BaseAppException):
    """Недостатньо прав для виконання операції."""

    def __init__(self, detail: str = "Доступ заборонено"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


# ──────────────────────────────────────────────
# Помилки користувачів
# ──────────────────────────────────────────────

class UserAlreadyExists(BaseAppException):
    """Користувач з таким email вже зареєстрований."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )


class UserNotFound(BaseAppException):
    """Користувача не знайдено в базі даних."""

    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or "Користувача не знайдено",
        )


class UserInactive(BaseAppException):
    """Обліковий запис користувача заблоковано."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш обліковий запис заблоковано. Подайте запит на розблокування.",
        )


# ──────────────────────────────────────────────
# Помилки рахунків
# ──────────────────────────────────────────────

class AccountNotFound(BaseAppException):
    """Банківський рахунок не знайдено."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рахунок не знайдено",
        )


class AccountBlocked(BaseAppException):
    """Рахунок заблоковано і не може виконувати операції."""

    def __init__(self, detail: str = "Рахунок заблоковано. Переказ неможливий."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class SelfTransferNotAllowed(BaseAppException):
    """Переказ на той самий рахунок заборонено."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Переказ на той самий рахунок не дозволяється",
        )


class CurrencyMismatch(BaseAppException):
    """Переказ між рахунками з різними валютами не підтримується."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Переказ між рахунками різних валют не підтримується",
        )


class InsufficientFunds(BaseAppException):
    """Недостатньо коштів для виконання транзакції."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостатньо коштів на рахунку",
        )


# ──────────────────────────────────────────────
# Помилки транзакцій
# ──────────────────────────────────────────────

class TransactionNotFound(BaseAppException):
    """Транзакцію не знайдено."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакцію не знайдено",
        )


class TransactionPendingReview(BaseAppException):
    """Транзакція очікує на перевірку адміністратором (підозріла сума)."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_202_ACCEPTED,
            detail=(
                "Транзакція відправлена на перевірку адміністратором через велику суму. "
                "Кошти будуть зараховані після схвалення."
            ),
        )


class TransactionRejected(BaseAppException):
    """Транзакцію відхилено адміністратором."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Транзакцію відхилено адміністратором",
        )


class InvalidTransactionAmount(BaseAppException):
    """Некоректна сума транзакції."""

    def __init__(self, detail: str = "Некоректна сума транзакції"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


# ──────────────────────────────────────────────
# Помилки запитів (requests)
# ──────────────────────────────────────────────

class RequestNotFound(BaseAppException):
    """Запит на операцію не знайдено."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запит не знайдено",
        )


class RequestAlreadyResolved(BaseAppException):
    """Запит вже було оброблено адміністратором."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Запит вже було оброблено",
        )


# ──────────────────────────────────────────────
# Помилки валідації
# ──────────────────────────────────────────────

class InvalidObjectId(BaseAppException):
    """Некоректний формат MongoDB ObjectId."""

    def __init__(self, field: str = "id"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Некоректний формат ідентифікатора: {field}",
        )