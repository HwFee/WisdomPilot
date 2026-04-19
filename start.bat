@echo off
chcp 65001 >nul
title AIcodiingTeach 启动

echo.
echo ==================================================
echo  AIcodiingTeach 启动中...
echo ==================================================
echo.

cd /d "%~dp0"

python start_services.py

pause
