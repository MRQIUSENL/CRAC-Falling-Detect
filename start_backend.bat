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
    goto :check_deps
)

if exist "%DIR%CRAC\Scripts\python.exe" (
    set "PYTHON=%DIR%CRAC\Scripts\python.exe"
    echo [INFO] Using CRAC Python
    goto :check_deps
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where python') do set "PYTHON=%%i"
    echo [INFO] Using system Python
    goto :check_deps
)

echo [ERROR] Python not found
pause
exit /b 1


:: ============================================
::  Check & Install Dependencies
:: ============================================
:check_deps
echo [INFO] Checking dependencies...

"%PYTHON%" -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] fastapi not found, installing...
    "%PYTHON%" -m pip install fastapi uvicorn python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo [ERROR] Install failed. Run manually:
        echo         python -m pip install fastapi uvicorn python-multipart
        pause
        exit /b 1
    )
    echo [ OK ] Dependencies installed
) else (
    echo [ OK ] Dependencies ready
)


:: ============================================
::  Start Backend
:: ============================================
echo.
echo ============================================
echo   YOLO11 Fall Detection API
echo   http://localhost:8001
echo   http://localhost:8001/docs
echo ============================================
echo.

cd /d "%DIR%"
"%PYTHON%" "%DIR%backend\main.py"

pause
