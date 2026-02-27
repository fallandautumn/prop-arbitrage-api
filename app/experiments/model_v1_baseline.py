import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sklearn.linear_model import LinearRegression
from app.models.property import Property # 実行パスが通っている前提
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()
# --- インポートエラー対策（おまじない） ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

logger = logging.getLogger(__name__)

# --- 【解決策】このファイル内で接続を完結させる ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class PriceAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def update_estimated_prices(self):
        query = self.db.query(Property)
        df = pd.read_sql(query.statement, self.db.bind)

        if len(df) < 5:
            return 0
        

        # 特徴量作成（以前のコードにはなかった重要な1行）
        df['is_mansion'] = df['building_type'].apply(lambda x: 1 if x == 'マンション' else 0)

        X = df[['age', 'liv_area', 'station_distance','floor','is_mansion']]
        y = df['price'] + df['admin_fee']

        model = LinearRegression()
        model.fit(X, y)

        # 統計レポート
        print(f"R2 Score: {model.score(X, y):.4f}")

        df['predicted'] = model.predict(X)
        df['rate'] = (y - df['predicted']) / df['predicted']
        df['total_fee'] = y

        updated_count = 0
        for index, row in df.iterrows():
            prop = self.db.query(Property).filter(Property.id == int(row['id'])).first()
            if prop:
                prop.estimated_price = float(row['predicted'])
                prop.divergence_rate = float(row['rate'])
                prop.monthly_fee = float(row['total_fee'])
                updated_count += 1
        
        self.db.commit()
        return updated_count

# --- 【解決策】ここが単体実行のための着火剤 ---
if __name__ == "__main__":
    db = SessionLocal()
    try:
        analyzer = PriceAnalyzer(db)
        count = analyzer.update_estimated_prices()
        print(f"Success: {count} properties updated.")
    finally:
        db.close()