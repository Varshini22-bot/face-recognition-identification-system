@echo off
title Face Recognition Backend API
echo ========================================================
echo  Face Recognition Identification System - Backend API
echo ========================================================
echo  FastAPI Docs: http://127.0.0.1:8000/docs
echo  Health Check: http://127.0.0.1:8000/health
echo ========================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please create the virtual environment first:
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

call .\venv\Scripts\activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
