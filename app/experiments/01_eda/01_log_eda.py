import seaborn as sns
import matplotlib.pyplot as plt
import sys
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()
# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# 自作した部品をインポート
from app.services.preprocess import load_and_preprocess_data, get_train_val_test_split

# 接続情報はここに置く（あるいは環境変数から取る）
DATABASE_URL = os.getenv("DATABASE_URL")

if __name__ == "__main__":
    # 1. 部品を使ってデータを準備（preprocess.pyのおかげで1行！）
    df = load_and_preprocess_data(DATABASE_URL)
    train_df, _, _ = get_train_val_test_split(df)

    # 2. 可視化（対数変換前後の比較などをここで行う）
    plt.figure(figsize=(10, 5))
    sns.histplot(train_df['log_total_fee'], kde=True, color='green')
    plt.title("Distribution of Log-Transformed Total Fee")
    plt.show()

    # 散布図
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=train_df, x='log_liv_area', y='log_total_fee', alpha=0.5)
    plt.title("Log(Area) vs Log(Total Fee)")
    plt.show()

        # --- 外れ値の特定講義 ---

    # 1. 簡易的な閾値設定（例：家賃300万円以上や、面積10㎡以下など）
    # 散布図で見た「明らかに別世界の物件」を特定する
    outliers = train_df[
        (train_df['total_fee'] > 1000000) |  # 100万円超えの超高級物件
        (train_df['liv_area'] < 10)          # 10㎡未満の極小物件
    ]

    print("除外候補の物件数:", len(outliers))
    print(outliers[['title', 'total_fee', 'liv_area', 'building_type']])

    # 2. 統計的な除外（さっきあなたが言ったIQR法や、標準偏差を使う方法）
    # log_total_fee の平均から 3σ（標準偏差の3倍）以上離れているものを探す
    mean = train_df['log_total_fee'].mean()
    std = train_df['log_total_fee'].std()

    statistical_outliers = train_df[np.abs(train_df['log_total_fee'] - mean) > 3 * std]
    print("統計的外れ値（3σ法）の件数:", len(statistical_outliers))