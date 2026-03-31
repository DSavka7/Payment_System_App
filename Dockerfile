FROM python:3.12-slim

LABEL maintainer="Payment System API"
LABEL description="Banking REST API analogous to Monobank"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]