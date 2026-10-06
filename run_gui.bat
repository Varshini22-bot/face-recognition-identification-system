@echo off
title Face Recognition Desktop GUI
echo ========================================================
echo  Face Recognition Desktop Application (PyQt6)
echo ========================================================
echo  NOTE: Ensure run_backend.bat is running first!
echo ========================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please create the virtual environment first:
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -r gui\requirements.txt
    pause
    exit /b 1
)

call .\venv\Scripts\activate
python gui\main.py
pause
