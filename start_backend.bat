@echo off
chcp 65001 >nul
set "DIR=%~dp0"

:: ============================================
::  YOLO11 Fall Detection - Backend Launcher
:: ============================================

:: 1. Find Python
set "PYTHON="

if exist "%DIR%venv\Scripts\python.exe" (
    set "PYTHON=%DIR%venv\Scripts\python.exe"
    echo [INFO] Using venv Python
    goto :start
)

if exist "%DIR%CRAC\Scripts\python.exe" (
    set "PYTHON=%DIR%CRAC\Scripts\python.exe"
    echo [INFO] Using CRAC Python
    goto :start
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where python') do set "PYTHON=%%i"
    echo [INFO] Using system Python: %PYTHON%
    goto :start
)

echo [ERROR] Python not found
pause
exit /b 1


:: ============================================
::  Install & Start
:: ============================================
:start
echo [INFO] Ensuring dependencies...
"%PYTHON%" -m pip install fastapi uvicorn python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet 2>nul

echo.
echo ============================================
echo   YOLO11 Fall Detection API
echo   http://localhost:8001
echo   http://localhost:8001/docs
echo ============================================
echo.

cd /d "%DIR%"
"%PYTHON%" "%DIR%backend\main.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Backend exited with code %errorlevel%
    echo [INFO] If module not found, run manually:
    echo        python -m pip install fastapi uvicorn python-multipart ultralytics opencv-python
)
pause
