@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo    FANTASY MANAGER EDITOR v4.0 - BUILD EXE
echo ============================================================
echo.

REM Verificar si PyInstaller está instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller no está instalado. Instalando...
    pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudo instalar PyInstaller
        echo Intenta manualmente: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo Compilando Fantasy Manager Editor v4.0...
echo Esto puede tardar unos minutos...
echo.

REM Compilar con PyInstaller
pyinstaller --onefile --windowed --name "FantasyManager_Editor_v4" --icon=NUL fantasy_manager_editor_v4.py

if errorlevel 1 (
    echo.
    echo [ERROR] La compilación falló
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    COMPILACIÓN COMPLETADA
echo ============================================================
echo.
echo El ejecutable se encuentra en:
echo   dist\FantasyManager_Editor_v4.exe
echo.
echo Puedes mover el .exe a la carpeta que prefieras.
echo.

REM Mover a la carpeta actual
if exist "dist\FantasyManager_Editor_v4.exe" (
    copy "dist\FantasyManager_Editor_v4.exe" "FantasyManager_Editor_v4.exe" >nul
    echo También se ha copiado a: devkit\FantasyManager_Editor_v4.exe
)

echo.
pause

