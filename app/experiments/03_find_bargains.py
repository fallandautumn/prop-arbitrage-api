import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.services.preprocess import load_and_preprocess_data

DB_URL = os.getenv("DATABASE_URL")

if __name__ == "__main__":
    # 1. データのロード（学習用ではなく、全データを対象にする）
    df = load_and_preprocess_data(DB_URL)
    
    # 2. 特徴量とターゲットの設定
    features = ['age', 'log_liv_area', 'station_distance', 'floor']
    X = df[features]
    y = df['log_total_fee']

    # 3. 再学習（全データを使って、より強固な「物差し」を作る）
    model = LinearRegression()
    model.fit(X, y)

    # 4. 全物件の家賃を予測
    df['predicted_log_fee'] = model.predict(X)
    df['predicted_fee'] = np.expm1(df['predicted_log_fee'])

    # 5. 乖離（かいり）の計算： 実際価格 - 予測価格
    # マイナスが大きいほど、相場より安い「お宝」の可能性が高い
    df['diff_amount'] = df['total_fee'] - df['predicted_fee']

    # 6. お宝物件の抽出
    # 誤差(MAE)が約2万円だったので、それを超える「-3万円以上」を抽出
    bargains = df[df['diff_amount'] <= -30000].sort_values('diff_amount')

    print(f"\n全 {len(df)} 件中、『安すぎる』と判定した物件: {len(bargains)} 件")
    print("\n" + "="*50)
    print("【新宿区・お宝物件ランキング（乖離額トップ10）】")
    print("="*50)
    
    # 見やすいように必要なカラムだけ表示
    display_cols = ['title', 'total_fee', 'predicted_fee', 'diff_amount', 'age', 'liv_area','floor','building_type']
    # print(bargains[display_cols].head(10).to_string(index=False))

    my_budget_list = bargains[(bargains['total_fee'] < 180000) & (bargains['floor']>1)]

# 2. 面積のタイポ（飯田橋事件）を完全に排除したい
    clean_list = my_budget_list[my_budget_list['liv_area'] < 100]

    print(clean_list[display_cols].head(10).to_string(index=False))