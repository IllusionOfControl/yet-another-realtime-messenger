import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"config/{os.environ.get("ENV")}.env",
        extra="ignore",
    )

    app_host: str = "localhost"
    app_port: int = 8000

    database_url: str

    file_upload_service_url: str

    secret_key: str

    log_level: str = Field("info")
    log_format: str = Field("text")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
