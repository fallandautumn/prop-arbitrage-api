# 1. ベース画像（Python 3.11）
FROM python:3.11-slim

# 2. 作業ディレクトリの設定
WORKDIR /app

# 3. 依存ライブラリのインストール
# 先に requirements.txt だけコピーしてキャッシュを効率化
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. コード全体をコピー
COPY . .

# 5. コンテナ起動時のデフォルトコマンド（compose側で上書き可能）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]