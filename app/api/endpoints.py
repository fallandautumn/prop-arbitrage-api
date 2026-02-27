from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.crud import property as crud_property
from app.services.scraper_v2 import SuumoScraperV2
from app.schemas.property import PropertyRead
import logging
from typing import List, Optional
from time import sleep
# analytics_v2.py を analytics.py として保存している想定
from app.services.analytics_v2 import PriceAnalyzerV2 
from app.models.property import Property

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/scrape", response_model=List[PropertyRead])
def run_scraping(pages: int = 60, db: Session = Depends(get_db)):
    # 1. スクレイピング実行（SUUMO版）
    scraper = SuumoScraperV2()
    all_properties = []
    
    for p in range(1, pages + 1):
        page_data = scraper.fetch_page(page=p)
        all_properties.extend(page_data)
        sleep(1.5) # サーバーへの礼儀（マナー）
    
    # 2. 一括保存を実行（ここが高速化のポイント）
    if all_properties:
        return crud_property.create_properties_bulk(db, all_properties)
    
    return []

@router.get("/properties", response_model=list[PropertyRead])
def read_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_property.get_properties(db, skip=skip, limit=limit)


@router.post("/analyze")
def run_analysis(db: Session = Depends(get_db)):
    """
    【V2】全データを使って再学習し、DBの理論価格を最新状態に更新します。
    """
    analyzer = PriceAnalyzerV2(db)

    updated_count = analyzer.analyze_and_update() 
    
    if updated_count == 0:
        return {"status": "skipped", "message": "Not enough data to analyze."}
        
    return {
        "status": "success", 
        "updated_count": updated_count,
        "message": f"Successfully updated {updated_count} properties using V2 Logic."
    }

@router.get("/bargains", response_model=List[PropertyRead])
def get_bargain_properties(
    budget: int = Query(180000, description="家賃＋管理費の合計上限"),
    min_floor: int = Query(2, description="最低階数（1階除外など）"),
    max_area: int = Query(100, description="面積上限（タイポ対策）"),
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    【V2】統計的に「安すぎる」と判定された物件を、指定条件でフィルタリングして返します。
    """
    analyzer = PriceAnalyzerV2(db)
    
    # 修正ポイント: 
    # 1. 重複していた呼び出しを1回に統合
    # 2. analytics_v2.py 内で limit まで処理を完結させる
    results = analyzer.get_bargains(
        budget=budget, 
        min_floor=min_floor, 
        max_area=max_area,
        limit=limit
    )
    
    # すでに analytics_v2.py 内で list[dict] になっているのでそのまま返す
    return results