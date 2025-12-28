# Fantasy Manager DevKit

Herramientas de desarrollo para Fantasy Manager.

## 📁 Estructura

```
devkit/
├── fantasy_manager_editor_v4.py  # Editor principal (nuevo)
├── fantasy_manager_editor_v3.py  # Editor anterior (funcional completo)
├── wm_to_fm_converter.py         # Conversor XML→JSON para Whoremaster
├── rename_wm_images.py           # Renombrador de imágenes + GIF→WebM
├── convert_wm_characters.bat     # Script batch para conversión
├── ejecutar_editor.bat           # Lanzador del editor
├── README.md                     # Este archivo
└── legacy/                       # Archivos antiguos/obsoletos
    ├── fantasy_manager_editor.py
    ├── FantasyManager_Editor_v2.exe
    └── clean_workers.py
```

## 🚀 Uso Rápido

### Ejecutar Editor v4 (Nuevo)
```bash
python fantasy_manager_editor_v4.py
```

### Ejecutar Editor v3 (Completo)
```bash
python fantasy_manager_editor_v3.py
```

O usa `ejecutar_editor.bat`

## 🔧 Herramientas

### 1. Editor Principal (`fantasy_manager_editor_v4.py`)

Editor visual completo con:
- ✅ Importador de Whoremaster integrado
- ✅ Conversión GIF→WebM
- ✅ Editor de Workers, Traits, Events, Items
- ✅ Previsualización de imágenes (requiere Pillow)

**Requisitos:**
```bash
pip install Pillow  # Para previsualización de imágenes
```

**FFmpeg** (opcional, para conversión de GIFs):
- Descargar de https://ffmpeg.org/
- Añadir al PATH del sistema

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
