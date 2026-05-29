@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   API Tree - Build Script
echo ========================================
echo.

REM Check if PyInstaller is available
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller not found.
    echo         Install it with: pip install pyinstaller
    exit /b 1
)

REM Record start time
set START_TIME=%TIME%

REM Clean previous build artifacts
echo [1/3] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

REM Run PyInstaller
echo [2/3] Building executable...
pyinstaller --onefile --name api-tree --clean --noconfirm --icon=icon.ico api-tree.py
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
