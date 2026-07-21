"""Structured logging configuration for MIRA.

Supports console, file, and structured JSON output.
Configure via environment variables:
    MIRA_LOG_LEVEL      — DEBUG, INFO (default), WARNING, ERROR
    MIRA_LOG_FORMAT     — text (default) or json
    MIRA_LOG_FILE       — optional path to log file (enables rotation)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Any


_DEFAULT_LEVEL = os.environ.get("MIRA_LOG_LEVEL", "INFO").upper()
_DEFAULT_FORMAT = os.environ.get("MIRA_LOG_FORMAT", "text").lower()
_LOG_FILE = os.environ.get("MIRA_LOG_FILE", "")


class _JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "context"):
            payload["context"] = record.context  # type: ignore[attr-defined]
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class _TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _make_handler(stream=None) -> logging.Handler:
    handler: logging.Handler = logging.StreamHandler(stream or sys.stdout)
    formatter: logging.Formatter = _JsonFormatter() if _DEFAULT_FORMAT == "json" else _TextFormatter()
    handler.setFormatter(formatter)
    return handler


def _add_file_handler(logger: logging.Logger, path: str) -> None:
    """Add a rotating file handler to the logger."""
    handler = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    formatter: logging.Formatter = _JsonFormatter() if _DEFAULT_FORMAT == "json" else _TextFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__).
        level: Override log level. Defaults to MIRA_LOG_LEVEL env var or INFO.
    """
    logger = logging.getLogger(name)
    effective_level = (level or _DEFAULT_LEVEL).upper()
    logger.setLevel(getattr(logging, effective_level, logging.INFO))

    if not logger.handlers:
        logger.addHandler(_make_handler())
        if _LOG_FILE:
            _add_file_handler(logger, _LOG_FILE)

    # Prevent propagation to root logger to avoid duplicate output
    logger.propagate = False
    return logger


# Global root logger for backward compatibility
logger = get_logger("mira")
