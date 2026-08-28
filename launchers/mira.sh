#!/usr/bin/env bash
set -euo pipefail
# MIRA Unified Linux/macOS CLI Wrapper
# Prefers the installed console script 'mira' (pip install) and falls back
# to a repo-relative .venv / python -m src for development checkouts.

# If an installed 'mira' console script is on PATH, use it directly.
if command -v mira >/dev/null 2>&1; then
    # Avoid exec-loop when this wrapper itself is on PATH as 'mira'
    # (e.g. pipx shim vs. repo launcher): compare resolved paths.
    MIRA_BIN="$(realpath "$(command -v mira)")"
    WRAPPER_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
    if [ "$MIRA_BIN" != "$(realpath "$WRAPPER_PATH")" ]; then
        exec mira "$@"
    fi
fi

# Fallback: development checkout with optional .venv
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1

# Prefer the local venv if it exists, otherwise fall back to system python
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON=python3
fi
if ! command -v "$PYTHON" &>/dev/null; then
    PYTHON=python
fi

# Force UTF-8 output for Unicode characters
export PYTHONUTF8=1

cd "$SCRIPT_DIR" || exit 1

exec "$PYTHON" -m src "$@"
