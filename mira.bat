@echo off
rem MIRA Unified Windows CLI Wrapper

rem Prefer the local venv if it exists, otherwise fall back to system python
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else (
    set PYTHON=python
)

if "%1"=="ai" (
    set PYTHONPATH=%~dp0src;%~dp0tools
    "%PYTHON%" tools\mira_cli\main.py %2 %3 %4 %5 %6 %7 %8 %9
    goto :eof
)

"%PYTHON%" src\cli.py %*