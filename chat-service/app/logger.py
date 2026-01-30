import json
import logging
from contextvars import ContextVar
from typing import Any, Optional

request_uid_context: ContextVar[Optional[str]] = ContextVar("request_uid", default=None)


class JsonFormatter(logging.Formatter):
    """
    Custom JSON Formatter for structured logging.
    """

    def __init__(
        self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style: str = "%"
    ):
        super().__init__(fmt, datefmt, style)

    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
            "module": record.module,
            "funcName": record.funcName,
            "process": record.process,
            "thread": record.thread,
            "request_uid": getattr(record, "request_uid", None),
        }

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key not in log_record and not key.startswith("_"):
                log_record[key] = value

        return json.dumps(log_record)
    

class StringFormatter(logging.Formatter):
    """
    Custom Default Formatter.
    """
    def format(self, record: logging.LogRecord) -> str:
        request_uid = getattr(record, "request_uid", "")
        setattr(record, "request_uid", request_uid.ljust(36))
        return super().format(record)



class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_id = request_uid_context.get()
        record.request_uid = request_id or ""
        return True


def configure_logging(log_level: str, log_format: str):
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()

    match log_format.lower():
        case "text":
            formatter = StringFormatter(
                "[%(levelname)s] [%(asctime)s] [%(request_uid)s] [%(name)s] - %(message)s"
            )
        case "json":
            formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z")
        case _:
            raise ValueError(f'Unknown log_format "{log_format}"')

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if not any(isinstance(f, TraceContextFilter) for f in console_handler.filters):
        console_handler.addFilter(TraceContextFilter())
