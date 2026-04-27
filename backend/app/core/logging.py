"""Structured JSON logging configuration.

WP-1.1: Global structured logging with request_id correlation.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

from app.middleware.request_id import get_request_id


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> None:
    """Configure root logger with structured JSON output."""
    log_level = logging.DEBUG if os.getenv("ENV", "dev") == "dev" else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(log_level)
    # Avoid duplicate handlers if called multiple times
    root.handlers.clear()
    root.addHandler(handler)
