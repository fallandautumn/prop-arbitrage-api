import pandas as pd
import numpy as np
import logging
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression
from app.models.property import Property
from app.services.preprocess import load_and_preprocess_data
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class PriceAnalyzerV2:
    def __init__(self, db: Session):
        self.db = db
        self.db_url = os.getenv("DATABASE_URL")

    def analyze_and_update(self):
        # 1. 接続先をDocker内部向けに強制修正
        db_url = self.db_url.replace("localhost", "db")
        df_clean = load_and_preprocess_data(db_url)
        
        features = ['age', 'log_liv_area', 'station_distance', 'floor']
        model = LinearRegression().fit(df_clean[features], df_clean['log_total_fee'])

        all_properties = self.db.query(Property).all()
        
        update_data = []
        for prop in all_properties:
            try:
                # 【重要】画像データに基づき、両方とも「万単位」として扱う
                # 1.5(万) + 15(万) = 16.5(万) -> 円にするため最後に10000を掛ける
                actual_fee_man = (prop.price or 0) + (prop.admin_fee or 0)
                actual_fee = float(actual_fee_man * 10000)

                log_area = np.log1p(prop.liv_area)
                X_pred = pd.DataFrame([[prop.age, log_area, prop.station_distance, prop.floor]], columns=features)
                
                predicted_fee = np.expm1(model.predict(X_pred)[0])
                
                diff_amount = actual_fee - predicted_fee
                div_rate = diff_amount / predicted_fee

                update_data.append({
                    "id": prop.id,
                    "monthly_fee": actual_fee,
                    "estimated_price": float(predicted_fee),
                    "divergence_rate": float(div_rate)
                })
            except Exception as e:
                logger.error(f"Error at id {prop.id}: {e}")
                continue

        if update_data:
            self.db.bulk_update_mappings(Property, update_data)
            self.db.commit()
            
        return len(update_data)


    def get_bargains(self, budget: int = 180000, min_floor: int = 2, max_area: int = 100, limit: int = 20):
        # メソッドの定義に「limit: int = 20」を追加しました
        """API用：現在のDBから「お宝リスト」を抽出して返す"""
        # DBから現在のデータをロード
        query = self.db.query(Property)
        # 修正ポイント：.get_bind() を使用
        df = pd.read_sql(query.statement, self.db.get_bind())

        # 修正ポイント：スペルミスを修正 (estimated_price)
        df['diff_amount'] = df['monthly_fee'] - df['estimated_price']

        # 2. 検閲
        q1 = df['divergence_rate'].quantile(0.25)
        q3 = df['divergence_rate'].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr 

        # ② フィルタリング実行
        valid_bargains = df[
            (df['divergence_rate'] > lower_bound) & 
            (df['diff_amount'] <= -30000) &          
            (df['liv_area'] < 100)                   
        ]
        
        # ...ロジックの最後...
        return valid_bargains.sort_values('diff_amount').head(limit).to_dict(orient="records")


if __name__ == "__main__":
    from app.core.db import SessionLocal
    db = SessionLocal()
    try:
        analyzer = PriceAnalyzerV2(db) # あなたのクラス名に合わせてください
        count = analyzer.analyze_and_update()
        print(f"成功: {count} 件の物件をV2ロジックで更新しました。")
    finally:
        db.close()