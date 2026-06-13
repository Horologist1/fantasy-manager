@echo off
cd /d "%~dp0"
echo ============================================================
echo  DEPRECATED - this editor is no longer maintained.
echo.
echo  Use the new web devkit instead:
echo    https://horologist1.github.io/fantasy-manager/devkit/
echo  or double-click:
echo    devkit_web\dist\FantasyManagerDevkit.html
echo.
echo  The web devkit covers every content type, has no .exe
echo  (no antivirus false positives), and saves straight into
echo  your game folder. This old editor is kept only as a
echo  temporary fallback and may be removed in a future release.
echo ============================================================
echo.
echo Press any key to launch the old editor anyway,
echo or close this window to switch to the web devkit.
pause >nul
echo.
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
