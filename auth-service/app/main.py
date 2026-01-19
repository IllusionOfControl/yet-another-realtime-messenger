import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import router
from app.logger import configure_logging
from app.middlewares import TraceContextMiddleware
from app.settings import get_settings
from app.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)

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
    app.add_middleware(TraceContextMiddleware)

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(router)

    return app


app = get_app()
