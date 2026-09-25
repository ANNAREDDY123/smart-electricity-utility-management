from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Electricity Utility Management System"
    app_version: str = "1.0.0"

    database_url: str = "sqlite:///./electricity_utility.db"

    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"

    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()