@echo off
REM ILLUM AI STUDIO — Windows Desktop Launcher
setlocal

echo ========================================================
echo    ILLUM AI STUDIO — Local Desktop Launch
echo ========================================================

REM Check Python installation
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in system PATH.
    echo Please install Python 3.12 (64-bit) from https://www.python.org/
    pause
    exit /b 1
)

REM Check or create virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment in .\venv...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created.
    call venv\Scripts\activate.bat
    echo [INFO] Installing pinned dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    call venv\Scripts\activate.bat
)

REM Verify .env exists
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating local .env from .env.example...
        copy .env.example .env >nul
        echo [NOTE] Local .env created. Open in Notepad to enter your API keys.
    )
)

echo [INFO] Starting ILLUM AI STUDIO backend on http://127.0.0.1:8000 ...
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
