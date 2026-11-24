@echo off
chcp 65001 >nul
title Install 24/7 Permanent Background Bot
cd /d "%~dp0"
python setup_startup.py
pause
