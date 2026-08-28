# Structured logging configuration for MIRA.

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
    # JSON formatter for structured logging.

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
    # Human-readable text formatter.

    def __init__(self) -> None:
        super().__init__("%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _make_handler(stream=None) -> logging.Handler:
    handler: logging.Handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(_JsonFormatter() if _DEFAULT_FORMAT == "json" else _TextFormatter())
    return handler


def _add_file_handler(logger: logging.Logger, path: str) -> None:
    # Add a rotating file handler to the logger.
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    handler.setFormatter(_JsonFormatter() if _DEFAULT_FORMAT == "json" else _TextFormatter())
    logger.addHandler(handler)


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    effective_level = (level or _DEFAULT_LEVEL).upper()
    try:
        level_val = getattr(logging, effective_level)
    except AttributeError:
        logger.setLevel(logging.INFO)
        logger.warning("Invalid log level '%s', falling back to INFO", effective_level)
    else:
        logger.setLevel(level_val)

    if not logger.handlers:
        logger.addHandler(_make_handler())
        if _LOG_FILE:
            _add_file_handler(logger, _LOG_FILE)

    # Prevent propagation to root logger to avoid duplicate output
    logger.propagate = False
    return logger


# Global root logger for backward compatibility
logger = get_logger("mira")
