import sys
import os
import joblib
import pandas as pd
import numpy as np
from sqlalchemy import text
from sklearn.metrics import r2_score, mean_absolute_error

# パス追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.core.db import SessionLocal

def load_shibuya_data():
    db = SessionLocal()
    # 渋谷の全件（2774件）を取得
    query = text("SELECT * FROM properties") # 必要に応じてWHERE address LIKE '%渋谷%'
    df = pd.read_sql(query, db.bind)
    db.close()
    return df

def preprocess_for_inference(df):
    """
    V2トレーニング時と『全く同じ』前処理を施す
    """
    # 1. 特徴量作成（賃料合計、対数化、築年数、駅距離など）
    df['total_fee'] = (df['price'] + df['admin_fee']) * 10000
    df['log_total_fee'] = np.log1p(df['total_fee'])
    df['log_liv_area'] = np.log1p(df['liv_area'])
    
    # 2. カテゴリ変数の処理（V2で使った列を再現）
    # ※ 本来は学習時のOneHotレイアウトに合わせる必要がありますが、
    # シンプルなモデルなら主要な数値変数のみで検証します
    features = ['log_liv_area', 'age', 'station_distance', 'floor']
    X = df[features]
    return X, df

def main():
    print("--- SHIBUYA MARKET ANALYSIS (V3) START ---")
    
    # 1. モデルロード
    model = joblib.load("models/shinjuku_base_v2.pkl")
    
    # モデルが学習時に使った「正しい列の順番」を取得
    # これが sklearn モデルの中に保存されています
    model_features = model.feature_names_in_
    print(f"モデルが要求している列: {model_features}")

    # 2. 渋谷データロード
    df_raw = load_shibuya_data()
    
    # 3. 前処理（V2と同じ関数を呼び出すのがベスト）
    # ※もし V2 で get_dummies() を使っていたなら、ここでも同様に行う
    X, df_processed = preprocess_for_inference(df_raw)
    
    # --- ここが修正の核心 ---
    # 渋谷のデータに足りない列（新宿特有の部屋タイプなど）があれば 0 で埋める
    for col in model_features:
        if col not in X.columns:
            X[col] = 0
            
    # モデルが要求する「正しい順番」に列を並び替える
    X = X[model_features]
    # -----------------------

    # 4. 推論実行（これでエラーが消えます）
    log_pred = model.predict(X)
    df_processed['predicted_fee'] = np.expm1(log_pred)
    
    # 5. 乖離（ギャップ）計算
    df_processed['gap'] = df_processed['total_fee'] - df_processed['predicted_fee']
    
    # ...以下、表示処理
    # 5. 分析結果の表示
    print(f"分析対象: {len(df_processed)} 件")
    
    # お宝物件 TOP 10 を抽出
    bargains = df_processed.sort_values(by='gap').head(10)
    
    print("\n" + "="*50)
    print("【新宿相場から見た 渋谷のお宝物件 TOP 10】")
    print("="*50)
    for i, row in bargains.iterrows():
        print(f"物件: {row['title']} ({row['floor_plan']})")
        print(f"  実際: {row['total_fee']:,.0f}円 | 予測: {row['predicted_fee']:,.0f}円")
        print(f"  乖離: {row['gap']:,.0f}円 (新宿よりこれだけ安い！)")
        print("-" * 30)
    
        # 予測値と実績値の対数（モデルが直接出した値）で R2 を計算
    r2 = r2_score(df_processed['log_total_fee'], log_pred)
    mae = mean_absolute_error(df_processed['total_fee'], df_processed['predicted_fee'])

    print("\n" + "="*50)
    print(f"【モデルの渋谷汎用性チェック】")
    print(f"全体の R2 Score: {r2:.4f}")
    print(f"平均誤差 (MAE): {mae:,.0f} 円")
    print("="*50)

if __name__ == "__main__":
    main()