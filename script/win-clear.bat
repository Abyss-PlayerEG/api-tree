@echo off
cd /d "%~dp0\.."

echo Cleaning build artifacts...

if exist build (
    rmdir /s /q build
    echo   Removed build/
)
if exist dist (
    rmdir /s /q dist
    echo   Removed dist/
)
if exist src\api_tree\_version.py (
    del src\api_tree\_version.py
    echo   Removed src\api_tree\_version.py
)

echo Done.
