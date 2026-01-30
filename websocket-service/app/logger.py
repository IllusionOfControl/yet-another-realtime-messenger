import logging
import json
import logging.config
from typing import Optional

def configure_logging(log_level: str, log_format: str):
    logging.basicConfig(level=log_level.upper())
