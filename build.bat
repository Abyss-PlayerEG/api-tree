@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   API Tree - Build Script (uv)
echo ========================================
echo.

REM Check if uv is available
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uv not found.
    echo         Install it from: https://docs.astral.sh/uv/
    exit /b 1
)

REM Ensure dependencies are installed
echo [0/3] Syncing dependencies...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] Failed to sync dependencies.
    exit /b 1
)

REM Record start time
set START_TIME=%TIME%

REM Clean previous build artifacts
echo [1/3] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

REM Run PyInstaller via uv (onedir for fast startup)
echo [2/3] Building executable...
uv run pyinstaller --onedir --name api-tree --clean --noconfirm --strip --icon=icon.ico api-tree.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    exit /b 1
)

REM Show result
echo [3/3] Build complete.
echo.
echo ---------------------------------------
if exist dist\api-tree\api-tree.exe (
    for /f "tokens=*" %%A in ('dir /s /-c dist\api-tree 2^>nul ^| findstr /r "^$" ^| findstr /v "Dir(s)"') do (
        set "LINE=%%A"
    )
    echo   Output : dist\api-tree\api-tree.exe
) else (
    echo [WARNING] Output file not found.
)
echo   Start  : %START_TIME%
echo   End    : %TIME%
echo ---------------------------------------
echo.
echo ========================================
echo   Build Successful!
echo ========================================

endlocal
