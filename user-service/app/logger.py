import logging
import json
from typing import Optional, Any

class JsonFormatter(logging.Formatter):
    """
    Custom JSON Formatter for structured logging.
    """
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record: logging.LogRecord) -> str:
        if not self.is_json:
            return super().format(record)
        
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
        }

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        for key, value in record.__dict__.items():
            if key not in log_record and not key.startswith('_'):
                log_record[key] = value

        return json.dumps(log_record)
    
def configure_logging(log_level: str, log_format: str):
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()

    match log_format:
        case "text":
            formatter = logging.Formatter(
                "[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s"
            )
        case "json":
            formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S%z", is_json=True)
        case _:
            raise ValueError("Unknown log_format \"{log_format}\"")

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
