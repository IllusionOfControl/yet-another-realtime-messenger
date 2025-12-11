import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.logger import request_uid_context

logger = logging.getLogger(__name__)


class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())

        token = request_uid_context.set(trace_id)

        logger.info(
            f"Incoming request: {request.method} {request.url} - Trace ID: {trace_id}"
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request processing failed for {request.method} {request.url} with error: {e}",
                exc_info=True,
            )
            raise
        finally:
            process_time = time.perf_counter() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Trace-Id"] = trace_id

            logger.info(
                f"Request finished: {request.method} {request.url} - Status: {response.status_code} - Duration: {process_time:.4f}s"
            )

            request_uid_context.reset(token)

        return response
