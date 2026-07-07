@echo off
set "DIR=%~dp0"

:: 1. local venv
if exist "%DIR%venv\Scripts\python.exe" (
    echo [OK] venv Python
    "%DIR%venv\Scripts\python.exe" "%DIR%backend\main.py"
    pause
    exit /b
)

:: 2. CRAC venv
if exist "%DIR%CRAC\Scripts\python.exe" (
    echo [OK] CRAC Python
    "%DIR%CRAC\Scripts\python.exe" "%DIR%backend\main.py"
    pause
    exit /b
)

:: 3. fallback: system python
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] system Python
    cd /d "%DIR%backend"
    python main.py
    pause
    exit /b
)

:: 4. not found
echo [ERROR] Python not found. Please install Python or activate venv.
pause