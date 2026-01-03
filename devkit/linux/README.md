# Fantasy Manager Editor - Versión Linux

Esta carpeta contiene todos los archivos necesarios para ejecutar y compilar el editor en Linux.

## 📁 Archivos

- `fantasy_manager_editor_v4_linux.py` - Editor compatible con Linux
- `ejecutar_editor.sh` - Script para ejecutar el editor
- `build_editor_linux.sh` - Script para crear el ejecutable (Linux)
- `compilar_ejecutable.ps1` - Script para compilar desde Windows (usa WSL)
- `COMPILAR_EJECUTABLE.md` - Instrucciones detalladas de compilación
- `README.md` - Este archivo

## 🚀 Uso Rápido

### Ejecutar el Editor

```bash
# Dar permisos de ejecución (solo la primera vez)
chmod +x ejecutar_editor.sh

# Ejecutar el editor
./ejecutar_editor.sh
```

O directamente con Python:
```bash
python3 fantasy_manager_editor_v4_linux.py
```

### Crear Ejecutable

**Desde Linux:**
```bash
# Dar permisos de ejecución (solo la primera vez)
chmod +x build_editor_linux.sh

# Crear el ejecutable
./build_editor_linux.sh

# El ejecutable estará en:
#   dist/FantasyManager_Editor_v4_Linux
#   FantasyManager_Editor_v4_Linux (copia en esta carpeta)
```

**Desde Windows (con WSL):**
```powershell
# Ejecutar el script de PowerShell
.\compilar_ejecutable.ps1
```

**Nota:** El ejecutable debe compilarse en un sistema Linux. Si no tienes acceso a Linux, puedes:
- Instalar WSL (Windows Subsystem for Linux)
- Usar una máquina virtual Linux
- O ejecutar el script Python directamente sin compilar

Para más detalles, consulta `COMPILAR_EJECUTABLE.md`.

## 📋 Requisitos

### Python
- Python 3.6 o superior
- Verificar: `python3 --version`

### tkinter (requerido)
```bash
# Ubuntu/Debian:
sudo apt install python3-tk

# Fedora:
sudo dnf install python3-tkinter

# Arch Linux:
sudo pacman -S tk
```

### Dependencias Python (opcionales pero recomendadas)
```bash
# Para previsualización de imágenes
pip3 install Pillow
```

### PyInstaller (solo para crear ejecutable)
Se instala automáticamente al ejecutar `build_editor_linux.sh`, o manualmente:
```bash
pip3 install pyinstaller
```

### FFmpeg (opcional, para conversión de GIFs)
```bash
# Ubuntu/Debian:
sudo apt install ffmpeg

# Fedora:
sudo dnf install ffmpeg

# Arch Linux:
sudo pacman -S ffmpeg
```

## 🔧 Características Especiales para Linux

Esta versión del editor incluye mejoras específicas para Linux:

- ✅ **Diálogo de selección de carpetas optimizado para Linux**: Usa directamente un diálogo de texto robusto con navegación de carpetas (no depende de diálogos nativos que pueden fallar)
- ✅ **Navegación de carpetas integrada**: Botón "Browse" para explorar subdirectorios sin salir del diálogo
- ✅ **Validación en tiempo real**: Muestra si la ruta es válida mientras escribes
- ✅ **Manejo robusto de errores**: Mejor manejo de errores relacionados con el sistema de ventanas
- ✅ **Funciona sin display server**: Puede funcionar incluso si X11/Wayland no está configurado correctamente
- ✅ **Soporte para rutas con ~**: Expande automáticamente `~` a tu directorio home

## ⚠️ Notas Importantes

1. **Ejecutables específicos de distribución**: El ejecutable creado con `build_editor_linux.sh` es específico para la distribución y arquitectura donde se compila. Si necesitas ejecutarlo en otra máquina Linux, compílalo en esa máquina o usa una distribución compatible.

2. **Rutas relativas**: Los scripts asumen que se ejecutan desde esta carpeta (`devkit/linux/`). Si ejecutas desde otra ubicación, asegúrate de ajustar las rutas.

3. **Permisos**: Recuerda dar permisos de ejecución a los scripts `.sh`:
   ```bash
   chmod +x ejecutar_editor.sh
   chmod +x build_editor_linux.sh
   ```

## 🐛 Solución de Problemas

### Los diálogos de selección de carpetas no funcionan
- **Solución mejorada**: Esta versión usa directamente un diálogo de texto robusto en Linux
- Si el diálogo no aparece, verifica que tkinter esté instalado correctamente
- Usa el botón "Browse" para navegar por subdirectorios
- Puedes usar Tab para autocompletar rutas en la terminal antes de copiarlas

### Probar el diálogo
```bash
# Ejecutar script de prueba
python3 test_dialog.py
```

Esto abrirá un diálogo de prueba para verificar que todo funciona correctamente.

### Error: "No module named 'tkinter'"
- Instala tkinter según tu distribución (ver Requisitos arriba)

### Error: "No display server"
- Si estás usando SSH, intenta con X11 forwarding: `ssh -X user@host`
- O usa el fallback de texto que se activa automáticamente

### El ejecutable no funciona en otra máquina Linux
- Los ejecutables de Linux son específicos de la distribución
- Compila el ejecutable en la máquina donde lo vas a usar
- O usa el script Python directamente en lugar del ejecutable

## 📖 Más Información

Para más información sobre el editor, consulta el README principal en `devkit/README.md`.

