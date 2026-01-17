@echo off
REM MetaKGP Bot - Quick Start Script for Windows

echo.
echo ============================================================
echo   MetaKGP RAG Bot - Frontend Integration
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [✓] Python is installed
echo.

REM Check if requirements are installed
echo [*] Checking dependencies...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo [!] Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [✓] Dependencies installed
) else (
    echo [✓] Dependencies are installed
)

echo.
echo [✓] All checks passed!
echo.
echo ============================================================
echo   Starting MetaKGP Bot Server...
echo ============================================================
echo.
echo Frontend: http://127.0.0.1:5000
echo API Docs: http://127.0.0.1:5000/api
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the Flask app
python app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Flask app failed to start
    echo Check the error messages above
    pause
)
