@echo off
setlocal enabledelayedexpansion

title Video Subtitle Generator - Starting...

echo.
echo.
echo ************************************************************************
echo.
echo    V  I  D  E  O       S  U  B  T  I  T  L  E       G  E  N  E  R  A  T  O  R
echo.
echo               Professional AI Subtitle Tool
echo.
echo ************************************************************************
echo.

rem Check Python installation
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected
echo.

rem Check virtual environment
echo [2/4] Checking environment...
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo [INFO] No virtual environment found, using system Python
)
echo.

rem Check required packages
echo [3/4] Checking dependencies...
python -c "import customtkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing GUI dependencies...
    pip install customtkinter Pillow
)
python -c "import faster_whisper" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required packages...
    pip install -e .[gui]
)
echo [OK] All dependencies checked
echo.

rem Launch application
echo [4/4] Launching Video Subtitle Generator...
echo ************************************************************************
echo.

start "Video Subtitle Generator" /B python -m video_subtitle.gui

rem Wait a moment to check if GUI started successfully
timeout /t 2 /nobreak >nul

echo.
echo [OK] GUI launched successfully!
echo [INFO] The application window should have opened.
echo.
echo ************************************************************************
echo Quick Start Guide:
echo   1. Click "Add Files" to add video files
echo   2. Configure parameters (model, language, output dir)
echo   3. Click "Start Processing" to generate subtitles
echo   4. Find subtitle files in the output directory
echo ************************************************************************
echo.
echo Application is running. You can close this window.
echo.

exit /b 0
