@echo off
chcp 65001 >nul
set "DIR=%~dp0"

:: ============================================
::  YOLO11 Fall Detection - Backend Launcher
:: ============================================

:: 1. venv
if exist "%DIR%venv\Scripts\python.exe" (
    echo [INFO] Using venv Python
    call :run "%DIR%venv\Scripts\python.exe"
    pause
    exit /b
)

:: 2. CRAC
if exist "%DIR%CRAC\Scripts\python.exe" (
    echo [INFO] Using CRAC Python
    call :run "%DIR%CRAC\Scripts\python.exe"
    pause
    exit /b
)

:: 3. system python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Using system Python
    call :run python
    pause
    exit /b
)

echo [ERROR] Python not found
pause
exit /b 1


:: ============================================
:run
set "PY=%1"
echo [INFO] Ensuring dependencies...
"%PY%" -m pip install fastapi uvicorn python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet 2>nul

echo.
echo ============================================
echo   YOLO11 Fall Detection API
echo   http://localhost:8001
echo   http://localhost:8001/docs
echo ============================================
echo.

cd /d "%DIR%"
"%PY%" "%DIR%backend\main.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Backend failed. Run manually:
    echo        python -m pip install fastapi uvicorn python-multipart ultralytics opencv-python
    echo        python backend\main.py
)
exit /b
