
import pytest
from fastapi import status

from app.core.exceptions import (
    UserAlreadyExists,
    UserNotFound,
    InvalidCredentials,
    TokenExpired,
    InvalidToken,
    PermissionDenied,
    AccountNotFound,
    AccountBlocked,
    InsufficientFunds,
    CurrencyMismatch,
    SelfTransferNotAllowed,
    TransactionNotFound,
    RequestNotFound,
    AppException,
)


class TestExceptionStatusCodes:

    def test_user_already_exists(self):
        exc = UserAlreadyExists()
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_user_not_found_default(self):
        exc = UserNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_user_not_found_custom_detail(self):
        exc = UserNotFound("Custom message")
        assert exc.detail == "Custom message"

    def test_invalid_credentials(self):
        exc = InvalidCredentials()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert "WWW-Authenticate" in exc.headers

    def test_token_expired(self):
        exc = TokenExpired()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self):
        exc = InvalidToken()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_permission_denied(self):
        exc = PermissionDenied()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_account_not_found(self):
        exc = AccountNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_account_blocked(self):
        exc = AccountBlocked()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_insufficient_funds(self):
        exc = InsufficientFunds()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_currency_mismatch(self):
        exc = CurrencyMismatch()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_self_transfer_not_allowed(self):
        exc = SelfTransferNotAllowed()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_transaction_not_found(self):
        exc = TransactionNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_request_not_found(self):
        exc = RequestNotFound()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_all_are_app_exceptions(self):
        exceptions = [
            UserAlreadyExists(),
            UserNotFound(),
            InvalidCredentials(),
            TokenExpired(),
            InvalidToken(),
            PermissionDenied(),
            AccountNotFound(),
            AccountBlocked(),
            InsufficientFunds(),
            CurrencyMismatch(),
            SelfTransferNotAllowed(),
            TransactionNotFound(),
            RequestNotFound(),
        ]
        for exc in exceptions:
            assert isinstance(exc, AppException), f"{type(exc).__name__} не є AppException"