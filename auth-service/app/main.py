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
    settings = get_settings()

    logger.info("Application startup complete!")
    logger.info(f"Uvicorn running on http://{settings.app_host}:{settings.app_port}")
    yield


def get_app():
    settings = get_settings()

    configure_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title="Auth Service",
        description="Authentication Microservice",
        lifespan=lifespan,
    )
    app.include_router(router)
    app.add_middleware(TraceContextMiddleware)

    return app


app = get_app()
