@echo off
chcp 65001 >nul
echo ========================================
echo Image Optimizer
echo (Normalizes resolutions and converts PNG to JPG)
echo ========================================
echo.
echo This script:
echo   - Normalizes all images to 1920x1080
echo   - Converts PNG without transparency to JPG
echo   - Maintains aspect ratio
echo   - Significantly reduces game size
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

REM Check if Pillow is installed
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Pillow is not installed. Installing...
    python -m pip install Pillow
    if errorlevel 1 (
        echo ERROR: Could not install Pillow
        echo Please install it manually with: pip install Pillow
        pause
        exit /b 1
    )
    echo Pillow installed successfully.
    echo.
)

REM Run the optimization script
cd /d "%~dp0"
echo Running optimization...
echo.
python normalize_resolutions.py

echo.
echo ========================================
echo Optimization completed
echo ========================================
echo.
echo Press any key to exit...
pause >nul
