from fastapi import FastAPI
from app.core.config import settings
from app.api import endpoints
import logging
import sys
from logging.handlers import RotatingFileHandler

# ハンドラーのリストを作成
handlers = [
    logging.StreamHandler(sys.stdout),
    # 5MBごとにバックアップを取り、最大5ファイルまで保持する設定（容量パンク防止）
    RotatingFileHandler("app.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
]
# 1. ログの見た目（フォーマット）を定義
# %(name)s が各ファイルの __name__（app.services.scraper 等）に自動置換されます
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 2. 全体の一括設定
logging.basicConfig(
    level=logging.INFO, # 出力する基準(最低レベル)を設定（本番は ERROR に変えるだけで一括抑制可能）
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout) # コンソールに出力
        # ,logging.FileHandler("app.log", encoding="utf-8") # ファイルにも自動保存
    ]
)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("Application starting...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# ルーターの登録
app.include_router(endpoints.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}", "docs": "/docs"}