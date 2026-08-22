"""Tests for MIRA structured logging configuration."""

from __future__ import annotations

import json
import logging
import os
from unittest.mock import patch


from src.logger import (
    _JsonFormatter,
    _TextFormatter,
    _make_handler,
    _add_file_handler,
    get_logger,
)




def _make_record(level=logging.INFO, msg="test message", exc_info=None):
    record = logging.LogRecord(
        name="test.logger",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    return record


def test_json_formatter_produces_valid_json():
    formatter = _JsonFormatter()
    record = _make_record(msg="hello world")
    output = formatter.format(record)
    data = json.loads(output)
    assert data["message"] == "hello world"
    assert data["level"] == "INFO"
    assert data["logger"] == "test.logger"
    assert "timestamp" in data


def test_json_formatter_includes_context():
    formatter = _JsonFormatter()
    record = _make_record(msg="ctx test")
    record.context = {"user": "jeremy"}
    output = formatter.format(record)
    data = json.loads(output)
    assert data["context"] == {"user": "jeremy"}


def test_json_formatter_includes_exception():
    formatter = _JsonFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        import sys

        record = _make_record(exc_info=sys.exc_info())
    output = formatter.format(record)
    data = json.loads(output)
    assert "exception" in data
    assert "ValueError" in data["exception"]




def test_text_formatter_format():
    formatter = _TextFormatter()
    record = _make_record(msg="text test")
    output = formatter.format(record)
    assert "text test" in output
    assert "INFO" in output
    assert "test.logger" in output




def test_make_handler_returns_stream_handler():
    handler = _make_handler()
    assert isinstance(handler, logging.StreamHandler)


def test_make_handler_with_custom_stream():
    import io

    stream = io.StringIO()
    handler = _make_handler(stream)
    assert handler.stream is stream


def test_make_handler_text_format_by_default():
    handler = _make_handler()
    assert isinstance(handler.formatter, _TextFormatter)


def test_make_handler_json_format_when_env_set():
    with patch.dict(os.environ, {"MIRA_LOG_FORMAT": "json"}):
        from src import logger as logger_module

        original_format = logger_module._DEFAULT_FORMAT
        logger_module._DEFAULT_FORMAT = "json"
        try:
            handler = logger_module._make_handler()
            assert isinstance(handler.formatter, _JsonFormatter)
        finally:
            logger_module._DEFAULT_FORMAT = original_format




def test_get_logger_returns_logger():
    log = get_logger("test_module_1")
    assert isinstance(log, logging.Logger)
    assert log.name == "test_module_1"


def test_get_logger_sets_level():
    log = get_logger("test_module_2", level="DEBUG")
    assert log.level == logging.DEBUG


def test_get_logger_defaults_to_info():
    log = get_logger("test_module_3")
    assert log.level == logging.INFO


def test_get_logger_no_propagation():
    log = get_logger("test_module_4")
    assert log.propagate is False


def test_get_logger_does_not_duplicate_handlers():
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers.clear()
    try:
        log = get_logger("test_module_5")
        initial_count = len(log.handlers)
        get_logger("test_module_5")
        assert len(log.handlers) == initial_count
    finally:
        root.handlers.extend(saved)


def test_get_logger_invalid_level_falls_back_to_info():
    log = get_logger("test_module_6", level="INVALID_LEVEL")
    assert log.level == logging.INFO




def test_add_file_handler_creates_log_file(tmp_path):
    log = logging.getLogger("test_file_logger")
    log.handlers.clear()
    log_file = tmp_path / "logs" / "test.log"

    _add_file_handler(log, str(log_file))
    assert log_file.parent.exists()
    assert len(log.handlers) == 1
    assert isinstance(log.handlers[-1], logging.handlers.RotatingFileHandler)

    # Clean up
    for h in log.handlers:
        h.close()
    log.handlers.clear()
