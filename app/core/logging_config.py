import logging
import re
from typing import Any


# Паттерни для маскування чутливих даних у логах
_SENSITIVE_PATTERNS = [
    (re.compile(r'(Bearer\s+)([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)', re.IGNORECASE),
     r'\1[MASKED_TOKEN]'),
    (re.compile(r'("password"\s*:\s*")[^"]*(")', re.IGNORECASE),
     r'\1[MASKED]\2'),
    (re.compile(r"('password'\s*:\s*')[^']*(')", re.IGNORECASE),
     r'\1[MASKED]\2'),
    (re.compile(r'("password_hash"\s*:\s*")[^"]*(")', re.IGNORECASE),
     r'\1[MASKED]\2'),
    (re.compile(r'("access_token"\s*:\s*")[^"]*(")', re.IGNORECASE),
     r'\1[MASKED_TOKEN]\2'),
    (re.compile(r'\beyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\b'),
     '[MASKED_JWT]'),
    (re.compile(r'(authorization[:\s]+)[^\s,}]+', re.IGNORECASE),
     r'\1[MASKED]'),
]


class SensitiveDataFilter(logging.Filter):
    """
    Фільтр логів, що маскує чутливі дані (паролі, токени, секрети).
    Застосовується тільки до рядкових повідомлень; числові args не чіпає,
    щоб уникнути конфліктів з бібліотеками що використовують %d/%f форматування.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Маскує чутливі дані в повідомленні лога перед записом.
        Безпечно обробляє args різних типів.
        """
        # Маскуємо тільки якщо повідомлення вже є рядком без args,
        # або якщо args містять рядки з чутливими даними
        try:
            record.msg = self._mask_sensitive(str(record.msg))

            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: self._mask_sensitive(str(v)) if isinstance(v, str) else v
                        for k, v in record.args.items()
                    }
                elif isinstance(record.args, (list, tuple)):
                    # Зберігаємо оригінальний тип (int/float), маскуємо тільки str
                    record.args = tuple(
                        self._mask_sensitive(a) if isinstance(a, str) else a
                        for a in record.args
                    )
        except Exception:
            # Якщо щось пішло не так — не блокуємо запис лога
            pass

        return True

    @staticmethod
    def _mask_sensitive(text: str) -> str:
        """Замінює чутливі значення у рядку на маски."""
        for pattern, replacement in _SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


def setup_logging(level: int = logging.INFO) -> None:
    """
    Налаштовує глобальне логування застосунку.

    Формат: дата/час | назва файлу:рядок | рівень | повідомлення

    Args:
        level: Рівень логування (за замовчуванням INFO).
    """
    fmt = "%(asctime)s | %(filename)s:%(lineno)d | %(levelname)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=date_fmt))
    handler.addFilter(SensitiveDataFilter())

    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=date_fmt))
    file_handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.addHandler(file_handler)

    # Приглушуємо зайві логи від сторонніх бібліотек
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # Прибираємо DEBUG логи від python-multipart щоб уникнути шуму
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("python_multipart").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Повертає логер з фільтром маскування чутливих даних.

    Args:
        name: Назва логера (зазвичай __name__ модуля).

    Returns:
        Налаштований логер.
    """
    logger = logging.getLogger(name)
    if not any(isinstance(f, SensitiveDataFilter) for f in logger.filters):
        logger.addFilter(SensitiveDataFilter())
    return logger