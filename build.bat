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

REM Run PyInstaller via uv (onedir for fast startup)
echo [2/4] Building executable...
uv run pyinstaller --onedir --name api-tree --clean --noconfirm --icon=icon.ico api-tree.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    exit /b 1
)

REM Show executable result
echo [3/4] Executable build complete.
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
"!ISCC!" setup.iss
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

pause
endlocal
