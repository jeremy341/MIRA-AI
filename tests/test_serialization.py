"""Tests for MIRA experiment result serialization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.serialization import (
    CURRENT_SCHEMA_VERSION,
    ExperimentRecord,
    _MiraEncoder,
    _atomic_write,
    _backup_if_exists,
    _dataclass_to_dict,
    _detect_git_sha,
    _has_uncommitted_changes,
    experiment_metadata,
    serialize_config,
    serialize_result,
)


# ── _MiraEncoder tests ────────────────────────────────────────────────


def test_encoder_handles_path():
    encoder = _MiraEncoder()
    result = encoder.default(Path("/tmp/test"))
    assert result == str(Path("/tmp/test"))


def test_encoder_handles_datetime():
    encoder = _MiraEncoder()
    dt = datetime(2026, 1, 15, 12, 0, 0)
    result = encoder.default(dt)
    assert result == dt.isoformat()


def test_encoder_handles_set():
    encoder = _MiraEncoder()
    result = encoder.default({3, 1, 2})
    assert result == [1, 2, 3]


def test_encoder_handles_dataclass():
    @dataclass
    class Sample:
        x: int = 1
        y: str = "hello"

    encoder = _MiraEncoder()
    result = encoder.default(Sample())
    assert result == {"x": 1, "y": "hello"}


def test_encoder_falls_back_to_super():
    encoder = _MiraEncoder()

    with pytest.raises(TypeError):
        encoder.default(object())


# ── _dataclass_to_dict tests ──────────────────────────────────────────


def test_dataclass_to_dict_simple():
    @dataclass
    class Point:
        x: int
        y: int

    result = _dataclass_to_dict(Point(3, 4))
    assert result == {"x": 3, "y": 4}


def test_dataclass_to_dict_nested():
    @dataclass
    class Inner:
        val: int

    @dataclass
    class Outer:
        inner: Inner
        name: str

    result = _dataclass_to_dict(Outer(Inner(42), "test"))
    assert result == {"inner": {"val": 42}, "name": "test"}


def test_dataclass_to_dict_dict_of_dataclasses():
    @dataclass
    class Item:
        val: int

    result = _dataclass_to_dict({"a": Item(1), "b": Item(2)})
    assert result == {"a": {"val": 1}, "b": {"val": 2}}


def test_dataclass_to_dict_list_of_dataclasses():
    @dataclass
    class Item:
        val: int

    result = _dataclass_to_dict([Item(1), Item(2)])
    assert result == [{"val": 1}, {"val": 2}]


def test_dataclass_to_dict_passthrough_primitive():
    assert _dataclass_to_dict(42) == 42
    assert _dataclass_to_dict("hello") == "hello"


# ── _atomic_write tests ───────────────────────────────────────────────


def test_atomic_write_creates_file(tmp_path):
    target = tmp_path / "output.txt"
    _atomic_write(target, "hello world")
    assert target.read_text() == "hello world"


def test_atomic_write_creates_parent_dirs(tmp_path):
    target = tmp_path / "sub" / "deep" / "file.txt"
    _atomic_write(target, "data")
    assert target.read_text() == "data"


def test_atomic_write_overwrites_existing(tmp_path):
    target = tmp_path / "file.txt"
    _atomic_write(target, "old")
    _atomic_write(target, "new")
    assert target.read_text() == "new"


def test_atomic_write_no_temp_files_left(tmp_path):
    target = tmp_path / "output.txt"
    _atomic_write(target, "content")
    temp_files = [p for p in tmp_path.iterdir() if p.name.startswith(".output.txt")]
    assert len(temp_files) == 0


# ── _backup_if_exists tests ───────────────────────────────────────────


def test_backup_creates_bak_file(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("original content")
    _backup_if_exists(target)
    bak = target.with_suffix(".txt.bak")
    assert bak.exists()
    assert bak.read_text() == "original content"


def test_backup_skips_if_not_exists(tmp_path):
    target = tmp_path / "nonexistent.txt"
    _backup_if_exists(target)
    assert not target.with_suffix(".txt.bak").exists()


# ── serialize_result tests ────────────────────────────────────────────


def test_serialize_result_dict_to_json(tmp_path):
    data = {"name": "test", "value": 42}
    out = tmp_path / "result.json"
    result_path = serialize_result(data, out)
    assert result_path == out
    assert out.exists()
    loaded = json.loads(out.read_text())
    assert loaded["name"] == "test"
    assert loaded["value"] == 42
    assert loaded["__schema_version__"] == CURRENT_SCHEMA_VERSION


def test_serialize_result_dataclass_to_json(tmp_path):
    @dataclass
    class Result:
        name: str
        score: float

    data = Result(name="model_a", score=0.95)
    out = tmp_path / "result.json"
    serialize_result(data, out)
    loaded = json.loads(out.read_text())
    assert loaded["name"] == "model_a"
    assert loaded["score"] == 0.95
    assert loaded["__schema_version__"] == CURRENT_SCHEMA_VERSION


def test_serialize_result_to_yaml(tmp_path):
    data = {"name": "test", "items": [1, 2, 3]}
    out = tmp_path / "result.yaml"
    serialize_result(data, out, fmt="yaml")
    loaded = yaml.safe_load(out.read_text())
    assert loaded["name"] == "test"
    assert loaded["items"] == [1, 2, 3]
    assert loaded["__schema_version__"] == CURRENT_SCHEMA_VERSION


def test_serialize_result_primitive_wraps_in_value(tmp_path):
    out = tmp_path / "result.json"
    serialize_result(42, out)
    loaded = json.loads(out.read_text())
    assert loaded["value"] == 42


def test_serialize_result_backups_existing(tmp_path):
    out = tmp_path / "result.json"
    serialize_result({"v": 1}, out)
    serialize_result({"v": 2}, out)
    bak = out.with_suffix(".json.bak")
    assert bak.exists()
    old = json.loads(bak.read_text())
    assert old["v"] == 1
    new = json.loads(out.read_text())
    assert new["v"] == 2


# ── serialize_config tests ───────────────────────────────────────────


def test_serialize_config_to_yaml(tmp_path):
    @dataclass
    class Cfg:
        lr: float = 0.01
        epochs: int = 100

    out = tmp_path / "config.yaml"
    result = serialize_config(Cfg(), out)
    assert result == out
    loaded = yaml.safe_load(out.read_text())
    assert loaded["lr"] == 0.01
    assert loaded["epochs"] == 100
    assert loaded["__schema_version__"] == CURRENT_SCHEMA_VERSION
    assert "__serialized_at__" in loaded


# ── ExperimentRecord tests ───────────────────────────────────────────


def test_experiment_record_defaults():
    record = ExperimentRecord(command="train")
    assert record.command == "train"
    assert record.args == {}
    assert record.git_sha is None
    assert record.uncommitted_changes is False
    assert record.schema_version == CURRENT_SCHEMA_VERSION
    assert record.python_version  # non-empty; format varies by OS


def test_experiment_record_to_dict():
    record = ExperimentRecord(command="benchmark", args={"model": "test.pt"})
    d = record.to_dict()
    assert d["command"] == "benchmark"
    assert d["args"] == {"model": "test.pt"}
    assert d["__schema_version__"] == CURRENT_SCHEMA_VERSION


def test_experiment_metadata_auto_detects_git_sha():
    with patch("src.serialization._detect_git_sha", return_value="abc123"):
        with patch("src.serialization._has_uncommitted_changes", return_value=False):
            record = experiment_metadata("train", {"epochs": 10})
            assert record.git_sha == "abc123"
            assert record.uncommitted_changes is False


def test_experiment_metadata_explicit_git_sha():
    record = experiment_metadata("train", {}, git_sha="explicit_sha", uncommitted_changes=True)
    assert record.git_sha == "explicit_sha"
    assert record.uncommitted_changes is True


# ── _detect_git_sha tests ────────────────────────────────────────────


def test_detect_git_sha_via_subprocess():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123def456\n")
        sha = _detect_git_sha()
        assert sha == "abc123def456"


def test_detect_git_sha_subprocess_fails_returns_none():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        with patch("pathlib.Path.read_text", side_effect=OSError):
            sha = _detect_git_sha()
            assert sha is None


# ── _has_uncommitted_changes tests ───────────────────────────────────


def test_has_uncommitted_changes_true():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=" M file.py\n")
        assert _has_uncommitted_changes() is True


def test_has_uncommitted_changes_false():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        assert _has_uncommitted_changes() is False
