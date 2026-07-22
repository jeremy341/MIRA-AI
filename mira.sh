#!/usr/bin/env bash
# MIRA Unified Linux/macOS CLI Wrapper
# All paths are relative to the script's location

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer the local venv if it exists, otherwise fall back to system python
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON=python3
fi

# Force UTF-8 output for Unicode characters
export PYTHONUTF8=1

exec "$PYTHON" -m src "$@"
