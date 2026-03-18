@echo off
cd /d "%~dp0"
echo Fantasy Manager Editor v6.0
echo.
echo Features:
echo  - Workers, Traits, Events, Items, Buildings editors
echo  - Trait selectors for items (dropdown menus)
echo  - Daily Stories editor with loot and consequences
echo  - Event editor with cooldowns, occurrences, probabilities
echo  - Whoremaster Import
echo  - GIF to WebM conversion
echo.
python fantasy_manager_editor_v6.py
if errorlevel 1 (
    echo.
    echo Error: Could not run Python
    echo Make sure Python 3.6+ is installed
    echo.
    echo Optional: pip install Pillow (for image preview)
    pause
)
