"""
Ієрархія виключень предметної області.
Всі класи наслідують HTTPException для зручної інтеграції з FastAPI.
"""
from fastapi import HTTPException, status
from typing import Optional


# ─── Base ────────────────────────────────────────────────────────────────────

class AppException(HTTPException):
    """Базовий клас для всіх доменних виключень застосунку."""
    pass


# ─── User ────────────────────────────────────────────────────────────────────

class UserAlreadyExists(AppException):
    """Користувач з таким email вже зареєстрований."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує / User with this email already exists",
        )


class UserNotFound(AppException):
    """Користувача не знайдено у базі даних."""
    def __init__(self, detail: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or "Користувача не знайдено / User not found",
        )


class InvalidCredentials(AppException):
    """Невірний email або пароль під час входу."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні дані для входу / Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpired(AppException):
    """JWT-токен прострочено."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен прострочено / Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidToken(AppException):
    """JWT-токен недійсний або підроблений."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний токен / Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDenied(AppException):
    """Недостатньо прав для виконання операції."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ заборонено / Permission denied",
        )


# ─── Account ─────────────────────────────────────────────────────────────────

class AccountNotFound(AppException):
    """Рахунок не знайдено у базі даних."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рахунок не знайдено / Account not found",
        )


class AccountBlocked(AppException):
    """Рахунок заблоковано і не може брати участь у операціях."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Рахунок заблоковано / Account is blocked",
        )


class InsufficientFunds(AppException):
    """На рахунку недостатньо коштів для виконання операції."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостатньо коштів на рахунку / Insufficient funds",
        )


class CurrencyMismatch(AppException):
    """Валюти рахунків не збігаються при переказі."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Валюти рахунків не збігаються / Currency mismatch between accounts",
        )


class SelfTransferNotAllowed(AppException):
    """Переказ на той самий рахунок заборонено."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Переказ на той самий рахунок заборонено / Self-transfer is not allowed",
        )


# ─── Transaction ─────────────────────────────────────────────────────────────

class TransactionNotFound(AppException):
    """Транзакцію не знайдено."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакцію не знайдено / Transaction not found",
        )


# ─── Request ─────────────────────────────────────────────────────────────────

class RequestNotFound(AppException):
    """Запит не знайдено."""
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запит не знайдено / Request not found",
        )