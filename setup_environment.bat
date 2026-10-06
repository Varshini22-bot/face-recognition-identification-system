@echo off
title Face Recognition System Setup
echo ========================================================
echo  Face Recognition Identification System - One-Click Setup
echo ========================================================
echo.

echo [1/4] Creating Python virtual environment (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment. Ensure Python 3.10+ is installed.
    pause
    exit /b 1
)

echo [2/4] Activating venv and upgrading pip...
call .\venv\Scripts\activate
python -m pip install --upgrade pip

echo [3/4] Installing Backend & GUI dependencies...
pip install -r backend\requirements.txt
pip install -r gui\requirements.txt

echo [4/4] Installing Web Dashboard dependencies...
cd dashboard
call npm install
cd ..

echo.
echo ========================================================
echo  Setup Completed Successfully!
echo  To run:
echo    1. run_backend.bat
echo    2. run_gui.bat (Desktop app) OR run_dashboard.bat (Web app)
echo ========================================================
pause
