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
if exist src\_version.py (
    del src\_version.py
    echo   Removed src\_version.py
)

echo Done.
