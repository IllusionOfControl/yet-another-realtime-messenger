import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

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
        response = None
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR

        try:
            response = await call_next(request)
        except Exception as e:
            process_time = time.perf_counter() - start_time

            logger.error(
                f"Request processing failed for {request.method} {request.url} with error: {e}",
                exc_info=True,
            )
            raise
        else:
            process_time = time.perf_counter() - start_time
            status_code = response.status_code
        finally:
            logger.info(
                f"Request finished: {request.method} {request.url} - Status: {status_code} - Duration: {process_time:.4f}s"
            )

            request_uid_context.reset(token)

        if response:
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Trace-Id"] = trace_id

        return response
