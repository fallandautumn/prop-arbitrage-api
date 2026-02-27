# Real Estate Arbitrage API (Project Bible)
## 統計的裁定機会の検知による不動産価格評価エンジン

不動産市場の情報の非対称性を解消するため、統計学に基づいた「適正価格」と「市場価格」の乖離をリアルタイムで分析・提供するAPIサーバーです。

## 1. 技術スタック (Tech Stack)
- **Framework**: FastAPI (Python 3.13)
- **Database**: PostgreSQL 15, SQLAlchemy (ORM)
- **Analysis**: statsmodels (OLS Regression), pandas
- **Infrastructure**: Docker, Docker Compose
- **Environment**: python-dotenv

## 2. セットアップ手順 (Setup)

### 2.1. 仮想環境の構築
プロジェクトのルートディレクトリで以下のコマンドを実行してください。

```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
# Windows (PowerShell) の場合
.\.venv\Scripts\Activate.ps1

# Mac / Linux の場合
source .venv/bin/activate