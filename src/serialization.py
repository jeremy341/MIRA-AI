"""Experiment result serialization for reproducibility.

Provides atomic writes, schema versioning, backward-compatible loading,
and experiment metadata capture.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from logger import get_logger

logger = get_logger(__name__)

# Schema version for backward-compatible loading
CURRENT_SCHEMA_VERSION = "1.0"


class _MiraEncoder(json.JSONEncoder):
    """Custom JSON encoder handling Path, datetime, dataclasses, and sets."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        if isinstance(o, set):
            return sorted(o)
        return super().default(o)


def _dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass (or nested structure) to a plain dict."""
    if hasattr(obj, "__dataclass_fields__"):
        return _dataclass_to_dict(asdict(obj))
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_dataclass_to_dict(item) for item in obj]
    return obj


def _atomic_write(path: Path, data: str) -> None:
    """Write data atomically using a temporary file and rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _backup_if_exists(path: Path) -> None:
    """Create a .bak backup if the file already exists."""
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        try:
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to create backup of {path}: {exc}")


def serialize_result(result: Any, path: str | Path, fmt: str = "json") -> Path:
    """Serialize a result object to JSON or YAML file atomically.

    Handles dataclasses, dicts, lists, Path objects, and datetime.
    Creates parent directories if they don't exist.
    Returns the path to the saved file.
    """
    path = Path(path)

    if hasattr(result, "__dataclass_fields__"):
        data = asdict(result)
    elif isinstance(result, dict):
        data = result
    else:
        data = {"value": result}

    # Inject schema version
    if isinstance(data, dict):
        data["__schema_version__"] = CURRENT_SCHEMA_VERSION

    _backup_if_exists(path)

    if fmt == "yaml":
        _atomic_write(path, yaml.dump(data, default_flow_style=False, sort_keys=False))
    else:
        _atomic_write(path, json.dumps(data, indent=2, cls=_MiraEncoder))

    logger.debug(f"Serialized result to {path}")
    return path


def load_result(path: str | Path) -> dict:
    """Load a serialized result from JSON or YAML file.

    Performs basic schema validation and warns on version mismatch.
    """
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict at {path}, got {type(data).__name__}")

    schema_version = data.get("__schema_version__", "unknown")
    if schema_version != CURRENT_SCHEMA_VERSION:
        warnings.warn(
            f"Schema version mismatch: file has {schema_version}, "
            f"expected {CURRENT_SCHEMA_VERSION}. Backward compatibility not guaranteed.",
            UserWarning,
            stacklevel=2,
        )

    return data


def serialize_config(config: Any, path: str | Path) -> Path:
    """Serialize configuration to YAML for reproducibility."""
    path = Path(path)
    data = _dataclass_to_dict(config)
    if isinstance(data, dict):
        data["__schema_version__"] = CURRENT_SCHEMA_VERSION
        data["__serialized_at__"] = datetime.now(timezone.utc).isoformat()

    _backup_if_exists(path)
    _atomic_write(path, yaml.dump(data, default_flow_style=False, sort_keys=False))
    logger.debug(f"Serialized config to {path}")
    return path


def load_config(path: str | Path) -> dict:
    """Load a serialized config from YAML file."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict at {path}, got {type(data).__name__}")
    return data


def _detect_git_sha() -> str | None:
    """Try to detect the current git SHA. Returns None on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Fallback: read .git/HEAD directly
    try:
        head = Path(".git/HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref_path = Path(".git") / head[5:]
            if ref_path.exists():
                return ref_path.read_text(encoding="utf-8").strip()
        elif len(head) == 40:
            return head
    except Exception:
        pass

    return None


def _has_uncommitted_changes() -> bool:
    """Check whether the working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    except Exception:
        pass
    return False


def compute_file_checksum(path: str | Path, algorithm: str = "sha256") -> str:
    """Compute a checksum for a file."""
    path = Path(path)
    if not path.exists():
        return ""
    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclass
class ExperimentRecord:
    """Standard experiment record with reproducibility metadata."""

    command: str
    args: dict[str, Any] = field(default_factory=dict)
    git_sha: str | None = None
    uncommitted_changes: bool = False
    python_version: str = field(default_factory=lambda: sys.version)
    platform: dict[str, str] = field(default_factory=lambda: {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    })
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = CURRENT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["__schema_version__"] = self.schema_version
        return data


def experiment_metadata(
    command: str,
    args: dict[str, Any],
    git_sha: str | None = None,
    uncommitted_changes: bool = False,
) -> ExperimentRecord:
    """Generate an ExperimentRecord for experiment reproducibility.

    Includes timestamp, command, args, git SHA (auto-detected if available),
    Python version, and platform info.
    """
    if git_sha is None:
        git_sha = _detect_git_sha()
    if not uncommitted_changes:
        uncommitted_changes = _has_uncommitted_changes()

    return ExperimentRecord(
        command=command,
        args=args,
        git_sha=git_sha,
        uncommitted_changes=uncommitted_changes,
    )
