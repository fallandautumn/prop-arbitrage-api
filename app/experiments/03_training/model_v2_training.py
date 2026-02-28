import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import sys
import os
from dotenv import load_dotenv
import joblib

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from app.services.preprocess import load_and_preprocess_data, get_train_val_test_split

DB_URL = os.getenv("DATABASE_URL")

if __name__ == "__main__":
    # 1. クリーンなデータのロードと分割
    df = load_and_preprocess_data(DB_URL)
    train_df, val_df, test_df = get_train_val_test_split(df)

        # --- 重複チェック ---
    print(f"全件ロード時: {len(df)}件")

    # タイトル、面積、階数、価格がすべて同じものを「重複」とみなす
    duplicate_count = df.duplicated(subset=['title', 'liv_area', 'floor', 'total_fee']).sum()
    print(f"重複している物件数: {duplicate_count}件")

    # 重複を排除した後の件数

    # 2. 特徴量の選択（今回は対数面積を含む基本セット）
    features = ['age', 'log_liv_area', 'station_distance',"floor"]
    target = 'log_total_fee'

    X_train = train_df[features]
    y_train = train_df[target]
    X_val = val_df[features]
    y_val = val_df[target]


    # 3. 学習
    model = LinearRegression()
    model.fit(X_train, y_train) 

    # 4. 予測と逆変換
    # 予測値も「対数」なので、expを使って「円」に戻す必要がある
    # log_pred = model.predict(X_val)
    # y_pred_won = np.expm1(log_pred)  # 円に戻す
    # y_val_won = np.expm1(y_val)     # 実際の値も円に戻す

    # # 5. 評価
    # mae = mean_absolute_error(y_val_won, y_pred_won)
    # r2 = r2_score(y_val, log_pred)

    # print(f"モデルの精度 (R2 Score): {r2:.4f}")
    # print(f"平均的な誤差 (MAE): {mae:.0f} 円")

    # --- ここから追加：最終試験（テスト用データでの評価） ---
    X_test = test_df[features]
    y_test = test_df[target]

    # モデルは学習済みのものを使用
    log_test_pred = model.predict(X_test)
    y_test_pred_won = np.expm1(log_test_pred)
    y_test_won = np.expm1(y_test)

    test_mae = mean_absolute_error(y_test_won, y_test_pred_won)
    test_r2 = r2_score(y_test, log_test_pred)

    print("\n" + "="*30)
    
    print("【最終試験：テスト用データの結果】")
    print(f"最終精度 (R2 Score): {test_r2:.4f}")
    print(f"最終誤差 (MAE): {test_mae:.0f} 円")
    print("="*30)

    # モデルをファイルとして保存（永続化）
    SAVE_DIR = "../../../ml_models"
    os.makedirs(SAVE_DIR, exist_ok=True)
    joblib.dump(model, f"{SAVE_DIR}/shinjuku_base_v2.pkl")

    print("\n" + "!"*30)
    print(f"新宿モデルを '{SAVE_DIR}/shinjuku_base_v2.pkl' に結晶化しました。")