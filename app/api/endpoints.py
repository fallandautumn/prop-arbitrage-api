from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.crud import property as crud_property
from app.services.scraper import SuumoScraper
from app.schemas.property import PropertyRead
import logging
from typing import List
from time import sleep
from app.services.analytics import PriceAnalyzer
from app.models.property import Property

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/scrape", response_model=List[PropertyRead])
def run_scraping(pages: int = 60, db: Session = Depends(get_db)):
    # 1. スクレイピング実行（SUUMO版）
    scraper = SuumoScraper()
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
    DB内のデータを用いて回帰モデルを学習し、
    全物件の理論価格と乖離率を更新します。
    """
    analyzer = PriceAnalyzer(db)
    updated_count = analyzer.update_estimated_prices()
    
    if updated_count == 0:
        return {"status": "skipped", "message": "Not enough data to analyze."}
        
    return {
        "status": "success", 
        "updated_count": updated_count,
        "message": f"Successfully updated {updated_count} properties."
    }

@router.get("/bargains", response_model=List[PropertyRead])
def get_bargain_properties(limit: int = 10, db: Session = Depends(get_db)):
    """
    乖離率が低い（お買い得な）物件を順に返します。
    """
    # divergence_rate が NULL でないものを、昇順（安い順）で取得
    return db.query(Property)\
            .filter(Property.divergence_rate != None)\
            .order_by(Property.divergence_rate.asc())\
            .limit(limit)\
            .all()