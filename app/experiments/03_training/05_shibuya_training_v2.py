import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sqlalchemy import text
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from app.core.db import SessionLocal

# 1. データのロード（渋谷限定）
db = SessionLocal()
df = pd.read_sql(text("SELECT * FROM properties"), db.bind) # 全件（渋谷）
db.close()

# 2. 前処理（新宿と同じロジック）
df['total_fee'] = (df['price'] + df['admin_fee']) * 10000
df['log_total_fee'] = np.log1p(df['total_fee'])
df['log_liv_area'] = np.log1p(df['liv_area'])

features = ['age', 'log_liv_area', 'station_distance', 'floor']
X = df[features]
y = df['log_total_fee']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 学習（渋谷専用モデル）
model = LinearRegression()
model.fit(X_train, y_train)

# 4. 評価
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)

print(f"\n【渋谷専用モデルの精度結果】")
print(f"R2 Score: {r2:.4f}")

# 5. モデル保存（新宿版と分ける）
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/shibuya_base_v2.pkl")
print("渋谷モデルを 'models/shibuya_base_v2.pkl' として保存しました。")