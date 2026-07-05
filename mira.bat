@echo off
rem MIRA Unified Windows CLI Wrapper

rem Prefer the local venv if it exists, otherwise fall back to system python
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe src\cli.py %*
) else (
    python src\cli.py %*
)