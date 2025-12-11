import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.logger import configure_logging
from app.middlewares import TraceContextMiddleware
from app.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup complete!")
    logger.info("Uvicorn running on http://127.0.0.1:8000")
    yield


def get_app():
    settings = get_settings()

    configure_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title="User Service",
        description="User Profile and Contact Management Microservice",
        lifespan=lifespan,
    )
    app.include_router(router)
    app.add_middleware(TraceContextMiddleware)

    return app


app = get_app()
