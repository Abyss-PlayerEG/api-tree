@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "INSTALL_DIR=%LOCALAPPDATA%\api-tree"
set "SRC=%~dp0"

echo ============================================
echo  api-tree Installer
echo ============================================
echo.

if not exist "%SRC%api-tree.exe" (
    echo [ERROR] api-tree.exe not found
    echo Please run this script from the release directory.
    pause
    exit /b 1
)

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [1/3] Installing files...

if exist "%INSTALL_DIR%\_internal" rmdir /S /Q "%INSTALL_DIR%\_internal"
copy /Y "%SRC%api-tree.exe" "%INSTALL_DIR%\" >nul
if exist "%SRC%_internal\" (
    xcopy /E /Y /I /Q "%SRC%_internal" "%INSTALL_DIR%\_internal\" >nul
)

if /I not "%SRC%"=="%INSTALL_DIR%\" (
    copy /Y "%SRC%install.bat" "%INSTALL_DIR%\" >nul 2>nul
    copy /Y "%SRC%uninstall.bat" "%INSTALL_DIR%\" >nul 2>nul
)

echo    Done.

echo [2/3] Configuring PATH...

for /f "skip=2 tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "CUR_PATH=%%B"

echo !CUR_PATH! | findstr /I /C:"%INSTALL_DIR%" >nul
if errorlevel 1 (
    if defined CUR_PATH (
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "!CUR_PATH!;%INSTALL_DIR%" /f >nul
    ) else (
        reg add "HKCU\Environment" /v Path /t REG_EXPAND_SZ /d "%INSTALL_DIR%" /f >nul
    )
    echo    Added to user PATH
) else (
    echo    Already in PATH
)

echo [3/3] Creating config directory...

if not exist "%USERPROFILE%\.config\api-tree" (
    mkdir "%USERPROFILE%\.config\api-tree"
    echo    Created
) else (
    echo    Already exists
)

echo.
echo ============================================
echo  Installation complete.
echo  Restart your terminal and run:
echo    api-tree --init-config
echo ============================================

endlocal
