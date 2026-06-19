@echo off
setlocal

REM Change to project root (parent of script/)
cd /d "%~dp0\.."

echo ========================================
echo   API Tree - Mypy Type Check
echo ========================================
echo.

REM Check if uv is available
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uv not found.
    echo         Install it from: https://docs.astral.sh/uv/
    exit /b 1
)

REM Sync dependencies (ensures mypy is installed)
echo [1/2] Syncing dependencies...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] Failed to sync dependencies.
    exit /b 1
)

REM Run mypy
echo [2/2] Running mypy...
echo.
uv run mypy src/api_tree
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo   Type Check FAILED - review errors above
    echo ========================================
    exit /b 1
)

echo.
echo ========================================
echo   Type Check PASSED - no issues found
echo ========================================

endlocal
