@echo off
cd /d "%~dp0\.."

echo Checking uv...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uv not found.
    echo         Install: https://docs.astral.sh/uv/
    exit /b 1
)

echo Creating virtual environment and syncing dependencies...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] Failed to sync dependencies.
    exit /b 1
)

echo.
echo Done. Run with: uv run python src/api_tree/main.py
