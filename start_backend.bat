@echo off
setlocal enabledelayedexpansion
set "DIR=%~dp0"

:: ============================================
::  YOLO11 摔倒检测 — 后端启动脚本
:: ============================================

:: 1. 查找可用的 Python 解释器
set "PYTHON="
set "PIP="

:: 1a. 项目 venv
if exist "%DIR%venv\Scripts\python.exe" (
    set "PYTHON=%DIR%venv\Scripts\python.exe"
    set "PIP=%DIR%venv\Scripts\pip.exe"
    echo [INFO] 使用 venv Python
    goto :check_deps
)

:: 1b. CRAC 虚拟环境
if exist "%DIR%CRAC\Scripts\python.exe" (
    set "PYTHON=%DIR%CRAC\Scripts\python.exe"
    set "PIP=%DIR%CRAC\Scripts\pip.exe"
    echo [INFO] 使用 CRAC Python
    goto :check_deps
)

:: 1c. 系统 Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where python') do set "PYTHON=%%i"
    for /f "delims=" %%i in ('where pip') do set "PIP=%%i"
    echo [INFO] 使用系统 Python: !PYTHON!
    goto :check_deps
)

:: 未找到 Python
echo [ERROR] 未找到 Python，请安装 Python 或创建虚拟环境。
echo          conda create -n yolo python=3.8 -y ^&^& conda activate yolo
pause
exit /b 1


:: ============================================
::  检查 & 安装依赖
:: ============================================
:check_deps
echo [INFO] 检查后端依赖...

"%PYTHON%" -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] fastapi 未安装，正在自动安装依赖...
    "%PIP%" install fastapi uvicorn python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo [ERROR] 依赖安装失败，请手动执行:
        echo          "%PIP%" install fastapi uvicorn python-multipart
        pause
        exit /b 1
    )
    echo [ OK ] 依赖安装完成
) else (
    echo [ OK ] 依赖已就绪
)


:: ============================================
::  启动后端服务
:: ============================================
echo.
echo ============================================
echo   YOLO11 摔倒检测系统 API 启动中...
echo   访问地址: http://localhost:8000
echo   API 文档:  http://localhost:8000/docs
echo ============================================
echo.

cd /d "%DIR%"
"%PYTHON%" "%DIR%backend\main.py"

pause
endlocal