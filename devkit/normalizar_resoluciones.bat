@echo off
chcp 65001 >nul
echo ========================================
echo Normalizador de Resoluciones
echo (Ajusta todas a 1920x1080)
echo ========================================
echo.
echo Este script normaliza todas las imagenes
echo de workers a 1920x1080 manteniendo
echo la proporcion de aspecto.
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor, instala Python 3.7 o superior
    pause
    exit /b 1
)

REM Verificar si Pillow está instalado
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Pillow no esta instalado. Instalando...
    python -m pip install Pillow
    if errorlevel 1 (
        echo ERROR: No se pudo instalar Pillow
        echo Por favor, instalalo manualmente con: pip install Pillow
        pause
        exit /b 1
    )
    echo Pillow instalado correctamente.
    echo.
)

REM Ejecutar el script de normalización
cd /d "%~dp0"
python normalize_resolutions.py

echo.
echo Presiona cualquier tecla para salir...
pause >nul











