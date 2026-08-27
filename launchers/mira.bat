@echo off
setlocal
rem MIRA Unified Windows CLI Wrapper
rem Prefers the installed console script 'mira' (pip install) with fallback
rem to a repo-relative .venv / python -m src for development checkouts.

rem Prefer installed 'mira' console script when available
where mira >nul 2>&1
if %ERRORLEVEL% equ 0 (
    mira %*
    exit /b %ERRORLEVEL%
)

rem Fallback: development checkout with optional .venv
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
