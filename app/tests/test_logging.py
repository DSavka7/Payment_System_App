"""
Юніт-тести для маскування чутливих даних у логах.
"""
import logging
import pytest

from app.core.logging_config import SensitiveDataFilter


@pytest.fixture
def mask_filter():
    return SensitiveDataFilter()


class TestSensitiveDataMasking:
    def _apply(self, mask_filter, message: str) -> str:
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg=message, args=(), exc_info=None,
        )
        mask_filter.filter(record)
        return record.msg

    def test_masks_password_json(self, mask_filter):
        msg = '{"email": "user@example.com", "password": "SuperSecret@1"}'
        result = self._apply(mask_filter, msg)
        assert "SuperSecret@1" not in result
        assert "[MASKED]" in result

    def test_masks_jwt_bearer(self, mask_filter):
        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.abc123"
        result = self._apply(mask_filter, msg)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert "[MASKED" in result

    def test_masks_access_token_json(self, mask_filter):
        msg = '{"access_token": "eyJhbGciOiJIUzI1NiJ9.abc.def"}'
        result = self._apply(mask_filter, msg)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result

    def test_masks_password_hash(self, mask_filter):
        msg = '{"password_hash": "$2b$12$realHashValue"}'
        result = self._apply(mask_filter, msg)
        assert "$2b$12$realHashValue" not in result

    def test_safe_message_unchanged(self, mask_filter):
        msg = "Користувач id=123 успішно увійшов у систему"
        result = self._apply(mask_filter, msg)
        assert result == msg

    def test_masks_jwt_inline(self, mask_filter):
        msg = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMifQ.SflKx"
        result = self._apply(mask_filter, msg)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "[MASKED_JWT]" in result