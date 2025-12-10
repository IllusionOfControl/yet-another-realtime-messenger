import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    file_upload_service_url: str


class ProdSettings(Settings):
    model_config = SettingsConfigDict(env_file=".env.prod", extra="ignore")
    ENV: str = "prod"


class DevSettings(Settings):
    model_config = SettingsConfigDict(env_file=".env.dev", extra="ignore")
    ENV: str = "dev"


class TestSettings(Settings):
    model_config = SettingsConfigDict(env_file=".env.test", extra="ignore")
    ENV: str = "test"


environments: dict[str, type[Settings]] = {
    "prod": ProdSettings,
    "dev": DevSettings,
    "test": TestSettings,
}


@lru_cache(1)
def get_settings() -> Settings:
    env = os.environ.get("ENV")
    setting = environments.get(env)
    if not setting:
        raise ValueError(f'Unknown env "{env}"')
    return setting()


settings = get_settings()
