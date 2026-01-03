# Cómo Compilar el Ejecutable de Linux

El ejecutable de Linux **debe compilarse en un sistema Linux** (no se puede compilar desde Windows).

## Opciones para Compilar

### Opción 1: En una Máquina Linux

1. **Copia la carpeta `devkit/linux/` a tu máquina Linux**

2. **Abre una terminal en la carpeta `linux/`**

3. **Ejecuta el script de compilación:**
   ```bash
   chmod +x build_editor_linux.sh
   ./build_editor_linux.sh
   ```

4. **El ejecutable estará en:**
   - `dist/FantasyManager_Editor_v4_Linux`
   - `FantasyManager_Editor_v4_Linux` (copia en la carpeta actual)

### Opción 2: Usando WSL (Windows Subsystem for Linux)

Si tienes WSL instalado en Windows:

1. **Instala WSL si no lo tienes:**
   ```powershell
   wsl --install
   ```

2. **Abre WSL y navega a la carpeta:**
   ```bash
   cd /mnt/c/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager/devkit/linux
   ```

3. **Ejecuta el script:**
   ```bash
   chmod +x build_editor_linux.sh
   ./build_editor_linux.sh
   ```

### Opción 3: Usando una Máquina Virtual Linux

1. Instala una distribución Linux en una VM (Ubuntu, Fedora, etc.)
2. Comparte la carpeta del proyecto con la VM
3. Sigue los pasos de la Opción 1

## Requisitos Previos

Antes de compilar, asegúrate de tener instalado:

```bash
# Python 3.6+
python3 --version

# tkinter
# Ubuntu/Debian:
sudo apt install python3-tk

# PyInstaller (se instala automáticamente, o manualmente):
pip3 install pyinstaller
```

## Nota Importante

⚠️ **El ejecutable compilado será específico para la distribución y arquitectura donde se compile.**

- Si compilas en Ubuntu 22.04 x64, funcionará en otras máquinas con Ubuntu 22.04 x64
- Si necesitas ejecutarlo en otra distribución, compílalo en esa distribución
- O usa el script Python directamente: `python3 fantasy_manager_editor_v4_linux.py`

## Verificación

Después de compilar, verifica que el ejecutable funciona:

```bash
./FantasyManager_Editor_v4_Linux
```

Si hay errores, ejecuta con salida de consola para ver los mensajes de error.



