@echo off
title GoFile Fast Link Transfer
cd /d "%~dp0"
echo ===================================================
echo     GoFile Fast Link Transfer - Single Job
echo ===================================================
echo.
python main.py %*
pause
