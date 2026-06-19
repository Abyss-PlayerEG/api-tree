@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "INSTALL_DIR=%LOCALAPPDATA%\api-tree"

echo ============================================
echo  api-tree Uninstaller
echo ============================================
echo.

if not exist "%INSTALL_DIR%" (
    echo Nothing to uninstall.
    pause
    exit /b 0
)

echo [1/2] Removing files...

set "FOUND=0"

if exist "%INSTALL_DIR%\_internal" (
    rmdir /S /Q "%INSTALL_DIR%\_internal"
    set "FOUND=1"
)

if exist "%INSTALL_DIR%\api-tree.exe" (
    del /F /Q "%INSTALL_DIR%\api-tree.exe"
    set "FOUND=1"
)

for %%F in (install.bat uninstall.bat) do (
    if exist "%INSTALL_DIR%\%%F" (
        del /F /Q "%INSTALL_DIR%\%%F"
        set "FOUND=1"
    )
)

if "!FOUND!"=="0" (
    echo    No files found
) else (
    echo    Done
)

rd "%INSTALL_DIR%" 2>nul

echo [2/2] Removing from PATH...

for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CUR_PATH=%%B"

echo !CUR_PATH! | findstr /I /C:"%INSTALL_DIR%" >nul
if not errorlevel 1 (
    set "NEW_PATH="
    for %%P in ("!CUR_PATH:;=" "!") do (
        set "ENTRY=%%~P"
        if /I not "!ENTRY!"=="%INSTALL_DIR%" (
            if defined NEW_PATH (
                set "NEW_PATH=!NEW_PATH!;!ENTRY!"
            ) else (
                set "NEW_PATH=!ENTRY!"
            )
        )
    )
    if defined NEW_PATH (
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!NEW_PATH!" /f >nul
    ) else (
        reg delete "HKCU\Environment" /v Path /f >nul
    )
    echo    Removed from user PATH
) else (
    echo    Not found in PATH
)

echo.
echo ============================================
echo  Uninstallation complete.
echo  Restart your terminal for changes to apply.
echo ============================================

endlocal
