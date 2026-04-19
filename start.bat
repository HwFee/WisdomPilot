@echo off
chcp 65001 >nul
title AIcodiingTeach 启动

echo.
echo ==================================================
echo  AIcodiingTeach 启动中...
echo ==================================================
echo.

cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [1/4] 启动后端服务...
cd backend
if not exist ".venv" (
    echo [提示] 未找到虚拟环境，使用系统 Python
)
start "AIcodiingTeach - Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
cd ..

:: Wait for backend to start
timeout /t 3 /nobreak >nul

echo [2/4] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo [提示] 安装前端依赖...
    call pnpm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
)

echo [3/4] 启动前端服务...
start "AIcodiingTeach - Frontend" cmd /k "pnpm dev"
cd ..

echo [4/4] 服务启动完成！
echo.
echo ==================================================
echo  后端服务: http://localhost:8000
echo  前端服务: http://localhost:3000
echo  API 文档: http://localhost:8000/docs
echo ==================================================
echo.
echo 按任意键关闭此窗口（服务将继续运行）
pause >nul
