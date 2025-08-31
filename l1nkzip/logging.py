"""
Structured logging configuration for L1nkZip.

This module provides centralized logging configuration that integrates with the
application's observability goals, supporting both text and JSON formats.
"""

import json
import logging
import sys
from typing import Any, Dict, Union

from l1nkzip.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.default_time_format),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "__dict__"):
            # Add any custom attributes that were set on the record
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "message",
                ]:
                    log_entry[key] = value

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Custom text formatter with consistent formatting."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


def setup_logging() -> None:
    """Configure application-wide logging based on settings."""
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level = level_map.get(settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Create formatter based on log format setting
    formatter: Union[JSONFormatter, TextFormatter]
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Set up specific loggers for different components
    loggers = [
        "l1nkzip.cache",
        "l1nkzip.main",
        "l1nkzip.models",
        "l1nkzip.generator",
        "l1nkzip.phishtank",
        "l1nkzip.metrics",
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        # Inherit handlers from root logger


# Initialize logging when module is imported
setup_logging()

# Create module-level logger
logger = get_logger(__name__)
