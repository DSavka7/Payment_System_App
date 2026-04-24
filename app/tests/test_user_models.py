"""
Юніт-тести для моделей користувача та валідації пароля.
"""
import pytest
from pydantic import ValidationError

from app.models.user_models import UserCreate, validate_password_strength


# ──────────────────────────────────────────────
# Тести валідації пароля
# ──────────────────────────────────────────────

class TestPasswordStrength:
    def test_valid_password(self):
        pwd = "Secure@123"
        assert validate_password_strength(pwd) == pwd

    def test_too_short(self):
        with pytest.raises(ValueError, match="мінімум 8 символів"):
            validate_password_strength("Ab1!")

    def test_no_uppercase(self):
        with pytest.raises(ValueError, match="велика літера"):
            validate_password_strength("secure@123")

    def test_no_lowercase(self):
        with pytest.raises(ValueError, match="мала літера"):
            validate_password_strength("SECURE@123")

    def test_no_digit(self):
        with pytest.raises(ValueError, match="цифра"):
            validate_password_strength("Secure@abc")

    def test_no_special_char(self):
        with pytest.raises(ValueError, match="спеціальний символ"):
            validate_password_strength("Secure1234")

    def test_all_requirements_met(self):
        # Усі умови виконано
        assert validate_password_strength("MyP@ssw0rd!") == "MyP@ssw0rd!"


# ──────────────────────────────────────────────
# Тести моделі UserCreate
# ──────────────────────────────────────────────

class TestUserCreate:
    def _valid_payload(self, **overrides) -> dict:
        base = {
            "email": "test@example.com",
            "phone": "+380991234567",
            "first_name": "Іван",
            "last_name": "Петренко",
            "password": "Secure@123",
        }
        base.update(overrides)
        return base

    def test_valid_user(self):
        user = UserCreate(**self._valid_payload())
        assert user.email == "test@example.com"
        assert user.first_name == "Іван"
        assert user.last_name == "Петренко"

    def test_invalid_phone(self):
        with pytest.raises(ValidationError):
            UserCreate(**self._valid_payload(phone="0991234567"))

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(**self._valid_payload(email="not-an-email"))

    def test_weak_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(**self._valid_payload(password="weakpass"))

    def test_short_first_name(self):
        with pytest.raises(ValidationError):
            UserCreate(**self._valid_payload(first_name="А"))

    def test_invalid_first_name_chars(self):
        with pytest.raises(ValidationError):
            UserCreate(**self._valid_payload(first_name="Ivan123"))

    def test_first_name_with_hyphen(self):
        user = UserCreate(**self._valid_payload(first_name="Анна-Марія"))
        assert user.first_name == "Анна-Марія"

    def test_name_stripped(self):
        user = UserCreate(**self._valid_payload(first_name="  Іван  "))
        assert user.first_name == "Іван"

    def test_default_role_is_user(self):
        user = UserCreate(**self._valid_payload())
        assert user.role == "USER"