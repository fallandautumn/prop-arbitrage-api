import sys
import os
from time import sleep

# ルートパス（/app）をシステムパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.core.db import SessionLocal
from app.crud.property import create_property
from app.services.scraper import SuumoScraper

def main():
    # 1. データベースセッションの確立
    db = SessionLocal()
    
    # 2. 渋谷担当のスクレイパーを起動（インスタンス化）
    # ※scraper.pyの__init__を(self, area_name="shinjuku")に修正済みである前提
    scraper = SuumoScraper(area_name="shibuya")
    
    print("\n" + "="*30)
    print("SHIBUYA AREA DATA COLLECTION START")
    print("="*30)
    
    target_pages = 40  # 渋谷の厚みを確保するため40ページ（約1200〜1400件）を推奨
    
    try:
        for page in range(1, target_pages + 1):
            properties = scraper.fetch_page(page)
            
            if not properties:
                print(f"Page {page}: No data found. Stopping.")
                break
                
            for p in properties:
                # CRUD処理：1件ずつDBへ保存
                create_property(db, p)
                
            print(f"Page {page}/{target_pages} saved. Current batch: {len(properties)} items.")
            
            # 相手サーバーへの礼儀（1秒待機）
            sleep(1)
            
        print("\n" + "!"*30)
        print("渋谷のデータ確保が完了しました。")
        print("!"*30)
        
    except Exception as e:
        print(f"\nError occurred during scraping: {e}")
    finally:
        # セッションを確実に閉じる
        db.close()

if __name__ == "__main__":
    main()