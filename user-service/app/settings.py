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
    file_upload_service_token: str

    log_level: str = Field("info")
    log_format: str = Field("text")


class ProdSettings(Settings):
    model_config = SettingsConfigDict(env_file=".env.prod", extra="ignore")
    ENV: str = "prod"


class DevSettings(Settings):
    model_config = SettingsConfigDict(env_file=".env.dev", extra="ignore")
    ENV: str = "dev"


class TestSettings(Settings):
    model_config = SettingsConfigDict(env_file="f" "", extra="ignore")
    ENV: str = "test"


environments: dict[str, type[Settings]] = {
    "prod": ProdSettings,
    "dev": DevSettings,
    "test": TestSettings,
}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
