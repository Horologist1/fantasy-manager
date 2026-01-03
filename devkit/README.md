# Fantasy Manager DevKit

Herramientas de desarrollo para Fantasy Manager.

## 📁 Estructura

```
devkit/
├── fantasy_manager_editor_v4.py       # Editor principal (Windows/estándar)
├── fantasy_manager_editor_v3.py       # Editor anterior (funcional completo)
├── wm_to_fm_converter.py              # Conversor XML→JSON para Whoremaster
├── rename_wm_images.py                # Renombrador de imágenes + GIF→WebM
├── convert_wm_characters.bat          # Script batch para conversión
├── ejecutar_editor.bat                # Lanzador del editor (Windows)
├── build_editor_exe.bat               # Script para crear ejecutable (Windows)
├── FantasyManager_Editor_v4.exe       # Ejecutable Windows (pre-compilado)
├── README.md                          # Este archivo
├── linux/                             # Archivos para Linux
│   ├── fantasy_manager_editor_v4_linux.py  # Editor compatible con Linux
│   ├── ejecutar_editor.sh             # Lanzador del editor (Linux)
│   ├── build_editor_linux.sh          # Script para crear ejecutable (Linux)
│   └── README.md                      # Documentación específica de Linux
└── legacy/                            # Archivos antiguos/obsoletos
    ├── fantasy_manager_editor.py
    ├── FantasyManager_Editor_v2.exe
    └── clean_workers.py
```

## 🚀 Uso Rápido

### Windows
```bash
# Ejecutar con el script batch
ejecutar_editor.bat

# O directamente con Python
python fantasy_manager_editor_v4.py
```

### Linux
```bash
# Ir a la carpeta Linux
cd linux

# Dar permisos de ejecución (solo la primera vez)
chmod +x ejecutar_editor.sh

# Ejecutar el editor
./ejecutar_editor.sh

# O directamente con Python
python3 fantasy_manager_editor_v4_linux.py
```

**Nota para Linux:** 
- Todos los archivos de Linux están en la carpeta `devkit/linux/`
- La versión `fantasy_manager_editor_v4_linux.py` está especialmente optimizada para Linux
- Si los diálogos de selección de carpetas no funcionan, usará automáticamente un diálogo de entrada de texto como alternativa
- Consulta `linux/README.md` para más información específica de Linux

### Ejecutar Editor v3 (Completo)
```bash
python fantasy_manager_editor_v3.py
# o python3 en Linux
```

## 🔧 Herramientas

### 1. Editor Principal

#### Versión Estándar (`fantasy_manager_editor_v4.py`)
Editor visual completo con:
- ✅ Importador de Whoremaster integrado
- ✅ Conversión GIF→WebM
- ✅ Editor de Workers, Traits, Events, Items
- ✅ Previsualización de imágenes (requiere Pillow)

**Recomendado para:** Windows y Linux con entorno gráfico configurado correctamente

#### Versión Linux (`linux/fantasy_manager_editor_v4_linux.py`)
Mismas funcionalidades que la versión estándar, más:
- ✅ Selección de carpetas compatible con Linux (fallback automático)
- ✅ Funciona incluso sin X11/Wayland configurado correctamente
- ✅ Diálogos de texto como alternativa cuando los diálogos nativos fallan

**Recomendado para:** Linux, especialmente si tienes problemas con los diálogos de selección de carpetas

**Ubicación:** Todos los archivos de Linux están en `devkit/linux/`. Consulta `linux/README.md` para más detalles.

**Requisitos:**
```bash
pip install Pillow  # Para previsualización de imágenes
```

**Requisitos específicos de Linux:**
```bash
# Instalar tkinter (requerido para la interfaz gráfica)
# Ubuntu/Debian:
sudo apt install python3-tk

# Fedora:
sudo dnf install python3-tkinter

# Arch Linux:
sudo pacman -S tk
```

**FFmpeg** (opcional, para conversión de GIFs):
- **Windows:** Descargar de https://ffmpeg.org/ y añadir al PATH
- **Linux:** `sudo apt install ffmpeg` (Ubuntu/Debian) o equivalente para tu distribución

## 🔨 Construir Ejecutables

### Windows
```bash
# Ejecutar el script de build
build_editor_exe.bat

# El ejecutable se creará en:
#   dist/FantasyManager_Editor_v4.exe
# También se copiará a: devkit/FantasyManager_Editor_v4.exe
```

**Requisitos:**
- Python 3.6+
- PyInstaller (se instala automáticamente si no está presente)
- `pip install pyinstaller` (si falla la instalación automática)

### Linux
```bash
# Ir a la carpeta Linux
cd linux

# Dar permisos de ejecución (solo la primera vez)
chmod +x build_editor_linux.sh

# Ejecutar el script de build
./build_editor_linux.sh

# El ejecutable se creará en:
#   linux/dist/FantasyManager_Editor_v4_Linux
# También se copiará a: linux/FantasyManager_Editor_v4_Linux
```

**Requisitos:**
- Python 3.6+
- PyInstaller (se instala automáticamente si no está presente)
- `pip3 install pyinstaller` (si falla la instalación automática)
- tkinter (para la interfaz gráfica)

**Nota:** El ejecutable de Linux es específico para la distribución y arquitectura donde se compila. Si necesitas ejecutarlo en otra máquina Linux, puede que necesites compilarlo en esa máquina o usar una distribución compatible.

### 2. Conversor Whoremaster (`wm_to_fm_converter.py`)

Convierte personajes e items de Whoremaster a formato Fantasy Manager.

```bash
# Convertir personajes
python wm_to_fm_converter.py \
    --characters "C:/path/to/WM/Resources/Characters" \
    --output "../game/data/workers/workers_wm.json" \
    --copy-images \
    --image-dest "../game/images/workers"

# Convertir items
python wm_to_fm_converter.py \
    --items "C:/path/to/WM/Resources/Items" \
    --output "../game/data/items/items_wm.json"
```

### 3. Renombrador de Imágenes (`rename_wm_images.py`)

Renombra imágenes de Whoremaster y convierte GIFs a WebM.

```bash
# Ver qué haría (dry run)
python rename_wm_images.py "../game/images/workers/personaje" --dry-run

# Renombrar + convertir GIFs
python rename_wm_images.py "../game/images/workers/personaje" --convert-gifs

# Procesar todas las carpetas
python rename_wm_images.py "../game/images/workers" --all --convert-gifs
```

## 📋 Flujo de Trabajo Típico

### Importar Personajes de Whoremaster

1. **Usar el Editor v4:**
   - Abrir `fantasy_manager_editor_v4.py`
   - Ir a pestaña "WM Import"
   - Seleccionar carpeta de Characters de WM
   - Configurar opciones
   - Click "Import"

2. **O usar scripts directamente:**
   ```bash
   # Paso 1: Convertir XML a JSON
   python wm_to_fm_converter.py --characters "path/to/WM/Characters" --output "workers_wm.json" --copy-images --image-dest "../game/images/workers"
   
   # Paso 2: Procesar imágenes
   python rename_wm_images.py "../game/images/workers" --all --convert-gifs
   ```

## 📝 Notas

- El editor v3 tiene la implementación completa de todos los tabs
- El editor v4 está en desarrollo activo con nuevas funcionalidades
- Siempre haz backup antes de editar archivos del juego
- Los archivos JSON usan encoding UTF-8

## 🔗 Documentación Relacionada

Ver carpeta `docs/` en la raíz del proyecto:
- `docs/guides/` - Guías de mecánicas y sistemas
- `docs/references/` - Referencias de imágenes y listas
- `docs/prompts/` - Prompts para generación de contenido
