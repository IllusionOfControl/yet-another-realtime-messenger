from functools import lru_cache

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.settings import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
async def get_session_local() -> AsyncSession:
    settings = get_settings()

    engine = create_async_engine(settings.database_url, echo=True)
    return async_sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )


async def get_db():
    SessionLocal = get_session_local()
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


@lru_cache
async def get_redis_client():
    settings = get_settings()
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client
