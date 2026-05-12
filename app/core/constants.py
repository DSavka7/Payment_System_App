"""Константи ролей, статусів та налаштувань застосунку."""

# Ролі користувачів
USER_ROLE = "USER"
ADMIN_ROLE = "ADMIN"

# Статуси користувачів
USER_STATUS_ACTIVE = "active"
USER_STATUS_BLOCKED = "blocked"

# Статуси рахунків
ACCOUNT_STATUS_ACTIVE = "active"
ACCOUNT_STATUS_BLOCKED = "blocked"

# Статуси запитів
REQUEST_STATUS_PENDING = "pending"
REQUEST_STATUS_APPROVED = "approved"
REQUEST_STATUS_REJECTED = "rejected"

# Типи запитів
REQUEST_TYPE_BLOCK = "BLOCK"
REQUEST_TYPE_UNBLOCK = "UNBLOCK"
REQUEST_TYPE_LIMIT_CHANGE = "LIMIT_CHANGE"

# Валюти
CURRENCIES = ("UAH", "USD", "EUR")

# Типи транзакцій
TRANSACTION_TYPE_TRANSFER = "transfer"
TRANSACTION_TYPE_PAYMENT = "payment"
TRANSACTION_TYPE_INCOME = "income"

# Статуси транзакцій
TRANSACTION_STATUS_SUCCESS = "success"
TRANSACTION_STATUS_PENDING_REVIEW = "pending_review"  # очікує перевірки адміном
TRANSACTION_STATUS_APPROVED = "approved"               # схвалено адміном
TRANSACTION_STATUS_REJECTED = "rejected"               # відхилено адміном

# Поріг підозрілих транзакцій (UAH).
# Перекази на суму вище цього порогу автоматично позначаються як підозрілі
# і потребують схвалення адміністратора.
SUSPICIOUS_TRANSFER_THRESHOLD_UAH = 50_000.0
SUSPICIOUS_TRANSFER_THRESHOLD_USD = 1_500.0
SUSPICIOUS_TRANSFER_THRESHOLD_EUR = 1_400.0

# Порогові значення у словнику для зручного пошуку
SUSPICIOUS_THRESHOLDS: dict[str, float] = {
    "UAH": SUSPICIOUS_TRANSFER_THRESHOLD_UAH,
    "USD": SUSPICIOUS_TRANSFER_THRESHOLD_USD,
    "EUR": SUSPICIOUS_TRANSFER_THRESHOLD_EUR,
}