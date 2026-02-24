# app/main.py
from fastapi import FastAPI
from app.api import endpoints  # 後で作成するルーティングを読み込む

app = FastAPI(title="Prop-Arbitrage API", version="0.1.0")

# ルーターの登録
app.include_router(endpoints.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Prop-Arbitrage API", "status": "running"}