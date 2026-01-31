import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router
from app.logger import configure_logging
from app.middlewares import TraceContextMiddleware
from app.settings import get_settings
from app.services.kafka_producer import producer_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    await producer_service.start()
    yield
    await producer_service.stop()
    logger.info("Application shutdown...")


def get_app():
    settings = get_settings()

    configure_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title="Chat Service",
        description="Core Chat Management Microservice",
        lifespan=lifespan,
    )
    app.include_router(router)
    app.add_middleware(TraceContextMiddleware)

    return app
