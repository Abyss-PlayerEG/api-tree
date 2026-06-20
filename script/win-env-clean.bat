@echo off
cd /d "%~dp0\.."

if exist .venv (
    echo Removing .venv...
    rmdir /s /q .venv
    echo Done.
) else (
    echo .venv not found.
)
