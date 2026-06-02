from fastapi import HTTPException, status
from typing import Optional


class BaseAppException(HTTPException):
    def __init__(self, status_code: int, detail: str, headers: Optional[dict] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# --- Auth ---

class InvalidCredentials(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні дані для входу",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidToken(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалідний або відсутній токен авторизації",
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpired(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен прострочений. Увійдіть знову.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDenied(BaseAppException):
    def __init__(self, detail: str = "Доступ заборонено"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


Forbidden = PermissionDenied


# --- Users ---

class UserAlreadyExists(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )


class UserNotFound(BaseAppException):
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or "Користувача не знайдено",
        )


class UserInactive(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш обліковий запис заблоковано. Подайте запит на розблокування.",
        )


# --- Accounts ---

class AccountNotFound(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Рахунок не знайдено")


class AccountBlocked(BaseAppException):
    def __init__(self, detail: str = "Рахунок заблоковано"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InsufficientFunds(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостатньо коштів на рахунку")


class SelfTransferNotAllowed(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="Не можна переказувати на той самий рахунок")


class CurrencyMismatch(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="Переказ між рахунками різних валют не підтримується")


# --- Transactions ---

class TransactionNotFound(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Транзакцію не знайдено")


class InvalidTransactionAmount(BaseAppException):
    def __init__(self, detail: str = "Некоректна сума транзакції"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# --- Requests ---

class RequestNotFound(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Запит не знайдено")


class RequestAlreadyResolved(BaseAppException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail="Запит вже було оброблено")


# --- Validation ---

class InvalidObjectId(BaseAppException):
    def __init__(self, field: str = "id"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Некоректний формат ідентифікатора: {field}",
        )


class WrongCurrentPassword(BaseAppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невірний поточний пароль",
        )