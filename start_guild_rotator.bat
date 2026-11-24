@echo off
chcp 65001 >nul
title Discord Server Badge Rotator
cd /d "%~dp0"

echo ====================================================
echo Starting Discord Server Badge Rotator...
echo ====================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python and check 'Add Python to PATH'.
    pause
    exit /b
)

echo Checking dependencies...
python -m pip install -q -r requirements.txt

python guild_badge_rotator.py

if %errorlevel% neq 0 (
    echo.
    echo Script stopped.
    pause
)
