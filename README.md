# Payment System API

REST API банківської системи. Реалізовано на FastAPI + MongoDB.

## Технології

- **FastAPI** — веб-фреймворк
- **MongoDB** (motor) — асинхронна NoSQL база даних
- **Pydantic v2** — валідація та серіалізація даних
- **JWT** (python-jose) — аутентифікація (access + refresh токени)
- **bcrypt** — хешування паролів
- **Docker / Docker Compose** — контейнеризація

---

## Запуск через Docker Compose (рекомендовано)

```bash
# 1. Клонувати репозиторій
git clone <url>
cd payment-system

# 2. Запустити контейнери (MongoDB + застосунок)
docker compose up --build

# 3. API доступне за адресою
http://localhost:8000

# 4. Swagger UI (документація)
http://localhost:8000/docs
```

---

## Локальний запуск (без Docker)

```bash
# 1. Створити та активувати virtualenv
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# 2. Встановити залежності
pip install -r requirements.txt

# 3. Налаштувати .env (скопіювати приклад)
cp .env.example .env
# Відредагувати .env — вказати MONGODB_URL та JWT_SECRET_KEY

# 4. Запустити застосунок
uvicorn app.main:app --reload
```

---

## Запуск тестів

```bash
pytest tests/ -v --tb=short

# З відображенням покриття
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```
