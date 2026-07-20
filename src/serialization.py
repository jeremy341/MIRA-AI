"""Experiment result serialization for reproducibility."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


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


def serialize_result(result: Any, path: str | Path, fmt: str = "json") -> Path:
    """Serialize a result object to JSON or YAML file.

    Handles dataclasses, dicts, lists, Path objects, and datetime.
    Creates parent directories if they don't exist.
    Returns the path to the saved file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(result, "__dataclass_fields__"):
        data = asdict(result)
    elif isinstance(result, dict):
        data = result
    else:
        data = {"value": result}

    if fmt == "yaml":
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    else:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, cls=_MiraEncoder)

    return path


def load_result(path: str | Path) -> dict:
    """Load a serialized result from JSON or YAML file."""
    path = Path(path)
    with open(path) as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        return json.load(f)


def serialize_config(config: Any, path: str | Path) -> Path:
    """Serialize configuration to YAML for reproducibility."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = _dataclass_to_dict(config)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return path


def _detect_git_sha() -> Optional[str]:
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
        head = Path(".git/HEAD").read_text().strip()
        if head.startswith("ref: "):
            ref_path = Path(".git") / head[5:]
            if ref_path.exists():
                return ref_path.read_text().strip()
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


def experiment_metadata(
    command: str,
    args: dict,
    git_sha: Optional[str] = None,
    uncommitted_changes: bool = False,
) -> dict:
    """Generate metadata dict for experiment reproducibility.

    Includes timestamp, command, args, git SHA (auto-detected if available),
    Python version, and platform info.
    """
    if git_sha is None:
        git_sha = _detect_git_sha()
    if not uncommitted_changes:
        uncommitted_changes = _has_uncommitted_changes()

    return {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "args": args,
        "git_sha": git_sha,
        "uncommitted_changes": uncommitted_changes,
        "python_version": sys.version,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
    }
