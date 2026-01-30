from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.settings import get_settings
from redis.asyncio import Redis


class Base(DeclarativeBase):
    pass


@lru_cache
def get_session_local():
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
def get_redis_client():
    settings = get_settings()
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client
