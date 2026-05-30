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

REM Run PyInstaller via uv
echo [2/3] Building executable...
uv run pyinstaller --onefile --name api-tree --clean --noconfirm --icon=icon.ico api-tree.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    exit /b 1
)

REM Show result
echo [3/3] Build complete.
echo.
echo ---------------------------------------
if exist dist\api-tree.exe (
    for %%F in (dist\api-tree.exe) do (
        set /a SIZE_KB=%%~zF / 1024
        set /a SIZE_MB=%%~zF / 1048576
        echo   Output : dist\api-tree.exe
        echo   Size   : %%~zF bytes ^(approx. !SIZE_MB! MB / !SIZE_KB! KB^)
    )
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
