@echo off
chcp 65001 >nul
echo ========================================
echo Compresor Casi Lossless
echo (Solo imagenes que pesan demasiado)
echo ========================================
echo.
echo Este script comprime solo las imagenes
echo 1920x1080 que pesan demasiado para su
echo resolucion, usando calidad casi lossless.
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

REM Ejecutar el script de compresión
cd /d "%~dp0"
python compress_large_images.py

echo.
echo Presiona cualquier tecla para salir...
pause >nul











