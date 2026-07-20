"""Structured logging configuration for MIRA.

Environment variables:
    MIRA_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO.
    MIRA_LOG_FORMAT: Output format — "text" or "json". Default: text.
    MIRA_LOG_FILE: Optional path to a log file. Enables rotating file handler.

Usage:
    from logger import get_logger
    logger = get_logger(__name__)
    logger.info("Hello, MIRA!")

    with LogContext(request_id="abc", user="bot"):
        logger.info("This record includes context")
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from contextvars import ContextVar
from typing import Any

# Thread-safe / async-safe contextual logging state
_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("mira_log_context", default={})
_ROOT_CONFIGURED: bool = False


class _JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Inject contextual key-value pairs
        ctx = getattr(record, "context", None)
        if ctx:
            log_data["context"] = ctx

        # Inject any user-supplied extra fields
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "asctime", "context",
        }
        for key, value in record.__dict__.items():
            if key not in reserved:
                log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class _ContextFilter(logging.Filter):
    """Injects the current :class:`LogContext` into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.context = _LOG_CONTEXT.get()
        return True


def _setup_root_logger() -> logging.Logger:
    """Configure the root ``mira`` logger exactly once."""
    global _ROOT_CONFIGURED
    if _ROOT_CONFIGURED:
        return logging.getLogger("mira")

    log_level = os.getenv("MIRA_LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("MIRA_LOG_FORMAT", "text").lower()
    log_file = os.getenv("MIRA_LOG_FILE", "")

    root = logging.getLogger("mira")
    root.setLevel(getattr(logging, log_level, logging.INFO))

    # Already configured elsewhere (e.g., test harness) — respect that.
    if root.handlers:
        _ROOT_CONFIGURED = True
        return root

    # Choose formatter
    if log_format == "json":
        formatter: logging.Formatter = _JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Optional rotating file handler
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as exc:
            sys.stderr.write(f"[logger] WARNING: Could not open log file {log_file}: {exc}\n")

    root.addFilter(_ContextFilter())
    _ROOT_CONFIGURED = True
    return root


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a logger nested under the ``mira`` root.

    Backward-compatible with existing ``get_logger("mira")`` calls.
    Child loggers (e.g. ``mira.inference_engine``) propagate to the root,
    so they inherit handlers, filters, and the effective log level.
    """
    _setup_root_logger()

    if not name.startswith("mira"):
        name = f"mira.{name}"

    logger = logging.getLogger(name)

    # Allow per-logger override only when explicitly requested and different
    # from the environment default, preserving backward compatibility.
    env_level = os.getenv("MIRA_LOG_LEVEL", "INFO").upper()
    if level.upper() != env_level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    return logger


# Legacy module-level logger for direct ``from logger import logger`` imports.
logger = get_logger("mira")


class LogContext:
    """Context manager that attaches key-value pairs to every log record.

    Example::

        with LogContext(epoch=3, lr=0.001):
            logger.info("Training step complete")
            # JSON output will include {"epoch": 3, "lr": 0.001}
    """

    def __init__(self, **kwargs: Any) -> None:
        self._updates = kwargs
        self._token: Any = None

    def __enter__(self) -> LogContext:
        current = _LOG_CONTEXT.get().copy()
        current.update(self._updates)
        self._token = _LOG_CONTEXT.set(current)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        _LOG_CONTEXT.reset(self._token)
