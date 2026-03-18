@echo off
echo ============================================================
echo   Image Harmonizer - Fantasy Manager
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Pillow is installed
python -c "from PIL import Image" >nul 2>&1
if errorlevel 1 (
    echo Installing Pillow...
    pip install Pillow
    echo.
)

REM Run the script
cd /d "%~dp0"
python image_harmonizer.py --include-jpg --jpg-max-kb=350

echo.
pause
