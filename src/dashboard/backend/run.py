"""Launcher for the old dashboard — pre-registers src.config as 'config'."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
src_dir = project_root / "src"
backend_dir = Path(__file__).resolve().parent

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

import src.config
sys.modules["config"] = src.config

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
