@echo off
setlocal enabledelayedexpansion

REM Change to project root (parent of script/)
cd /d "%~dp0\.."

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
echo [0/4] Syncing dependencies...
uv sync
if %errorlevel% neq 0 (
    echo [ERROR] Failed to sync dependencies.
    exit /b 1
)

REM Record start time
set START_TIME=%TIME%

REM Clean previous build artifacts
echo [1/4] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

REM Generate version from current date (yy.mm.dd.hhmm)
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "Get-Date -Format 'yy.MM.dd.HHmm'"') do set "VERSION=%%i"
if not defined VERSION set "VERSION=26.05.31.1430"

REM Save numeric version for Inno Setup
set "NUMERIC_VERSION=%VERSION%"

REM Optional version prefix or test-build
if "%1"=="test-build" (
    set "VERSION=01.01.01.0001"
    set "NUMERIC_VERSION=01.01.01.0001"
    echo   Test build mode: version=!VERSION!
    echo.
) else (
    set /p "PREFIX=Version prefix (Enter to skip): "
    if defined PREFIX set "VERSION=!PREFIX!-!VERSION!"
)

REM Generate single-file version from src/app/
echo [1.5/4] Generating single-file api-tree-%VERSION%.py...
uv run python src/api_tree/tools/merge_src.py %VERSION% --tag python-script

REM ── Build 1: win64-zip ──────────────────────────
echo [2/4] Building win64-zip executable...
uv run python src/api_tree/tools/merge_src.py %VERSION% --tag win64-zip --version-only
uv run pyinstaller --onedir --name api-tree --clean --noconfirm --icon=icon.ico src/api_tree/main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    del src\api_tree\_version.py >nul 2>nul
    exit /b 1
)

if exist dist\api-tree\api-tree.exe (
    echo   Output : dist\api-tree\api-tree.exe
) else (
    echo [WARNING] Output file not found.
)

REM Copy install/uninstall scripts to dist for zip distribution
copy src\api_tree\installer\Windows\install.bat dist\api-tree\ >nul
copy src\api_tree\installer\Windows\uninstall.bat dist\api-tree\ >nul

REM Create zip archive
set "ZIP_NAME=api-tree-%VERSION%-win64.zip"
if exist "dist\!ZIP_NAME!" del "dist\!ZIP_NAME!"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\api-tree\*' -DestinationPath 'dist\!ZIP_NAME!' -Force"
if !errorlevel! equ 0 (
    echo   Zip    : dist\!ZIP_NAME!
) else (
    echo [WARNING] Zip creation failed.
)

REM Remove install scripts and zip build output
del dist\api-tree\install.bat >nul 2>nul
del dist\api-tree\uninstall.bat >nul 2>nul

REM ── Build 2: win64-setup ────────────────────────
echo [3/4] Building win64-setup executable...
uv run python src/api_tree/tools/merge_src.py %VERSION% --tag win64-setup --version-only

REM Clean PyInstaller cache for fresh build
if exist build rmdir /s /q build
if exist dist\api-tree rmdir /s /q dist\api-tree
if exist api-tree.spec del api-tree.spec

uv run pyinstaller --onedir --name api-tree --clean --noconfirm --icon=icon.ico src/api_tree/main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Setup build failed!
    del src\api_tree\_version.py >nul 2>nul
    exit /b 1
)

if exist dist\api-tree\api-tree.exe (
    echo   Output : dist\api-tree\api-tree.exe
) else (
    echo [WARNING] Output file not found.
)

REM ── Generate installer with Inno Setup ──────────
echo [4/4] Generating installer...

set ISCC=

REM Check common ISCC paths one by one
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe" & goto :iscc_found
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe" & goto :iscc_found
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" & goto :iscc_found

where iscc >nul 2>nul
if !errorlevel! equ 0 set "ISCC=iscc" & goto :iscc_found

echo   Installer: SKIPPED - Inno Setup not found.
echo   Install it: winget install --id JRSoftware.InnoSetup
goto :done

:iscc_found
echo   Using: !ISCC!
"!ISCC!" /DMyAppVersion=!VERSION! /DMyAppNumericVersion=!NUMERIC_VERSION! setup.iss
if !errorlevel! neq 0 (
    echo   Installer: BUILD FAILED!
    goto :done
)
echo   Installer: dist\api-tree-setup-v*.exe

:done

REM Cleanup build-time version file
del src\api_tree\_version.py >nul 2>nul

echo   Start  : %START_TIME%
echo   End    : %TIME%
echo ---------------------------------------
echo.
echo ========================================
echo   Build Successful!
echo ========================================

endlocal
