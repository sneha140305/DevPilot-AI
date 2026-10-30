from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):

    APP_NAME: str = "DevPilot AI"

    APP_ENV: str = "development"

    LOG_LEVEL: str = "INFO"

    BACKEND_HOST: str = "127.0.0.1"

    BACKEND_PORT: int = 8000

    MAX_UPLOAD_SIZE_MB: int = 10

    MAX_FILES_PER_PROJECT: int = 100

    ENABLE_AI_REVIEW: bool = False

    GEMINI_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()