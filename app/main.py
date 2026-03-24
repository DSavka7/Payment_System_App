from fastapi import FastAPI
from app.db.database import lifespan

# Імпорт роутерів
from app.routers.user_router import router as user_router
from app.routers.account_router import router as account_router
from app.routers.transaction_router import router as transaction_router
from app.routers.request_router import router as request_router

app = FastAPI(lifespan=lifespan, title="Payment System API")

# Підключення роутерів
app.include_router(user_router)
app.include_router(account_router)
app.include_router(transaction_router)
app.include_router(request_router)

@app.get("/")
async def root():
    return {"message": "Payment System API is running"}