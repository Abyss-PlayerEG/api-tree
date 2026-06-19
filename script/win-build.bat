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

REM Optional version prefix
set /p "PREFIX=Version prefix (Enter to skip): "
if defined PREFIX set "VERSION=%PREFIX%-%VERSION%"

REM Generate single-file version from src/app/
echo [1.5/4] Generating single-file api-tree-%VERSION%.py...
uv run python src/api_tree/tools/merge_src.py %VERSION% --tag python-script

REM Regenerate _version.py with win64 tag for PyInstaller
echo [1.6/4] Regenerating _version.py with tag=win64-zip...
uv run python src/api_tree/tools/merge_src.py %VERSION% --tag win64-zip --version-only

REM Run PyInstaller via uv (onedir for fast startup)
echo [2/4] Building executable...
uv run pyinstaller --onedir --name api-tree --clean --noconfirm --icon=icon.ico src/api_tree/main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    del src\api_tree\_version.py >nul 2>nul
    exit /b 1
)

REM Cleanup build-time version file
del src\api_tree\_version.py >nul 2>nul

REM Show executable result
echo [3/4] Executable build complete.
echo.
echo ---------------------------------------
if exist dist\api-tree\api-tree.exe (
    echo   Output : dist\api-tree\api-tree.exe
) else (
    echo [WARNING] Output file not found.
)

REM Copy install/uninstall scripts to dist for zip distribution
copy src\api_tree\installer\Windows\install.bat dist\api-tree\ >nul
copy src\api_tree\installer\Windows\uninstall.bat dist\api-tree\ >nul

REM Create zip archive of dist\api-tree
set "ZIP_NAME=api-tree-%VERSION%-win64.zip"
if exist "dist\!ZIP_NAME!" del "dist\!ZIP_NAME!"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\api-tree\*' -DestinationPath 'dist\!ZIP_NAME!' -Force"
if !errorlevel! equ 0 (
    echo   Zip    : dist\!ZIP_NAME!
) else (
    echo [WARNING] Zip creation failed.
)

REM Remove install scripts before Inno Setup (not needed in installer)
del dist\api-tree\install.bat >nul 2>nul
del dist\api-tree\uninstall.bat >nul 2>nul

REM ── Generate installer with Inno Setup ──────────────
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
echo   Start  : %START_TIME%
echo   End    : %TIME%
echo ---------------------------------------
echo.
echo ========================================
echo   Build Successful!
echo ========================================

endlocal
