#!/usr/bin/env bash
set -euo pipefail
# MIRA Unified Linux/macOS CLI Wrapper
# All paths are relative to the script's location

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
