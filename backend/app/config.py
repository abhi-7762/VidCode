from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "VidCode"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "vidcode"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Storage
    storage_backend: str = "local"
    storage_local_path: str = "./storage"
    max_file_size_mb: int = 500

    # AI APIs
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""
    runway_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

