@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo    FANTASY MANAGER EDITOR v5.1 - BUILD EXE
echo ============================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller is not installed. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo [ERROR] Could not install PyInstaller
        echo Try manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo Building Fantasy Manager Editor v5.1...
echo This may take a few minutes...
echo.

REM Build with PyInstaller
pyinstaller --onefile --windowed --name "FantasyManager_Editor_v5" --icon=..\icon.ico fantasy_manager_editor_v4.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    BUILD COMPLETED
echo ============================================================
echo.
echo The executable is located at:
echo   dist\FantasyManager_Editor_v5.exe
echo.
echo You can move the .exe to any folder you prefer.
echo.

REM Copy to current directory
if exist "dist\FantasyManager_Editor_v5.exe" (
    copy "dist\FantasyManager_Editor_v5.exe" "FantasyManager_Editor_v5.exe" >nul
    echo Also copied to: devkit\FantasyManager_Editor_v5.exe
)

echo.
pause
