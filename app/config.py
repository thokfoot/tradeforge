from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "trade-forge"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/tradeforge"
    redis_url: str = "redis://localhost:6379/0"
    data_dir: str = "data"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    alerts_enabled: bool = False
    alert_check_interval_seconds: int = 60


settings = Settings()
