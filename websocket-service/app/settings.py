import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"config/{os.environ.get('ENV', 'dev')}.env",
        extra="ignore",
    )
    app_host: str = "0.0.0.0"
    app_port: int = 8004
    
    # Infrastructure
    redis_url: str = "redis://localhost:6379"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_message_topic: str = "message_events"
    
    # Security
    public_key: str
    
    log_level: str = Field("info")
    log_format: str = Field("text")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
