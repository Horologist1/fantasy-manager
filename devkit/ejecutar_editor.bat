@echo off
cd /d "%~dp0"
echo Fantasy Manager Editor v4.0 - Complete Edition
echo.
echo Features:
echo  - Whoremaster Import
echo  - GIF to WebM conversion
echo  - Workers, Traits, Events, Items editors
echo.
python fantasy_manager_editor_v4.py
if errorlevel 1 (
    echo.
    echo Error: Could not run Python
    echo Make sure Python 3.6+ is installed
    echo.
    echo Optional: pip install Pillow (for image preview)
    pause
)
