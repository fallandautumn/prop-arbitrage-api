from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Prop-Arbitrage API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str | None = None

    # .env内の変数を「受け皿」として定義
    postgres_user: str
    postgres_password: str
    postgres_db: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # 定義外の変数があっても無視する設定（これでエラーを防げます）
    )

settings = Settings()