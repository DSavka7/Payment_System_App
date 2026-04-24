"""Константи ролей та статусів застосунку."""

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