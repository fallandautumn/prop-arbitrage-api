import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression
from app.models.property import Property
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def update_estimated_prices(self):
        # 1. DBからデータをロード
        query = self.db.query(Property)
        df = pd.read_sql(query.statement, self.db.bind)

        if len(df) < 5:
            logger.warning("分析に必要なデータが不足しています。")
            return 0

        # --- 特徴量エンジニアリング ---
        # 建物種別からマンションフラグを作成（分析精度向上のため）
        df['is_mansion'] = df['building_type'].apply(lambda x: 1 if x == 'マンション' else 0)

        # 2. 特徴量の選択
        features = ['age', 'liv_area', 'station_distance', 'floor', 'is_mansion']
        X = df[features]
        # 目的変数は「実質家賃（賃料+管理費）」
        y = df['price'] + df['admin_fee']

        # 3. 学習
        model = LinearRegression()
        model.fit(X, y)

        # --- 統計データの出力（検定2級レベルのチェック） ---
        r2 = model.score(X, y)
        logger.info(f"【分析レポート】決定係数 (R2): {r2:.4f}")
        
        coef_dict = dict(zip(features, model.coef_))
        logger.info(f"【分析レポート】回帰係数: {coef_dict}")
        logger.info(f"【分析レポート】切片: {model.intercept_:.4f}")

        # 4. 理論価格と乖離率の算出
        df['predicted'] = model.predict(X)
        df['rate'] = (y - df['predicted']) / df['predicted']
        df['total_fee'] = y

        # 5. DBへの更新
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

# --- 単体実行用のエントリーポイント ---
if __name__ == "__main__":
    db_session = SessionLocal()
    try:
        analyzer = PriceAnalyzer(db_session)
        count = analyzer.update_estimated_prices()
        print(f"\nSuccessfully updated {count} properties.")
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        db_session.close()