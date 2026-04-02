@echo off
title Apex Arena - Backend Server
color 0A

echo.
echo  ============================================
echo    APEX ARENA - E-Sports Event Backend
echo    FastAPI + Supabase
echo  ============================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Install from https://python.org
    pause
    exit /b
)

echo.
echo [2/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install packages!
    pause
    exit /b
)

echo.
echo [3/3] Starting FastAPI server...
echo.
echo  Server running at: http://127.0.0.1:8000
echo  API Docs at:       http://127.0.0.1:8000/docs
echo.
echo  Press Ctrl+C to stop the server.
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

pause
