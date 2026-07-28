@echo off
setlocal
rem MIRA Unified Windows CLI Wrapper
rem All paths are relative to the batch file's location

set "PROJECT_DIR=%~dp0..\"

rem Prefer the local venv if it exists, otherwise fall back to system python
if exist "%PROJECT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
) else (
    set PYTHON=python
)

rem Force UTF-8 output for Unicode characters (checkmarks, etc.)
set PYTHONUTF8=1

cd /d "%PROJECT_DIR%"

"%PYTHON%" -m src %*
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
