# Optimización de Peso del Juego - Fantasy Manager v9.1

## Análisis Actual

### Tamaño de Imágenes
- **Total**: ~835 MB
- **PNG**: 274 archivos = 648.25 MB (77.6% del total) ⚠️
- **JPG**: 623 archivos = 102.14 MB (12.2% del total)

### Problema Principal
Las imágenes PNG ocupan **6.3 veces más espacio** que las JPG, pero solo representan el 30% de los archivos.

## Recomendaciones de Optimización

### 1. ✅ CONVERTIR PNG A JPG (PRIORITARIO)
**Impacto**: Reducción de ~500-550 MB (60-65% del tamaño de imágenes)

**Acción**: Ejecutar el script de normalización que ya incluye conversión PNG→JPG:
```bash
cd devkit
python normalize_resolutions.py
```

**Beneficios**:
- Reduce tamaño de imágenes sin transparencia en ~70-80%
- Mantiene calidad visual aceptable (calidad 85)
- Ya está implementado en el script

### 2. ✅ NORMALIZAR RESOLUCIONES
**Impacto**: Optimización adicional y consistencia

**Acción**: El mismo script normaliza todas las imágenes a 1920x1080
- Elimina imágenes con resoluciones inconsistentes
- Reduce tamaño de imágenes muy grandes
- Mejora rendimiento del juego

### 3. 🔧 ARCHIVAR IMÁGENES EN EL BUILD
**Impacto**: Compresión adicional en la distribución final

**Acción**: Descomentar en `game/scripts/core/options.rpy`:
```python
build.classify('game/**.png', 'archive')
build.classify('game/**.jpg', 'archive')
```

**Beneficios**:
- Las imágenes se comprimen en archivos .rpa durante el build
- Reducción adicional del 10-20% en el tamaño final
- No afecta el desarrollo, solo la distribución

### 4. 🎵 OPTIMIZAR AUDIO
**Impacto**: Reducción de ~20-50 MB (dependiendo del tamaño actual)

**Recomendaciones**:
- Convertir MP3 a OGG Vorbis (mejor compresión)
- Reducir bitrate a 128 kbps para música de fondo
- Eliminar archivos de audio no utilizados

**Herramientas**:
- FFmpeg para conversión
- Audacity para edición

### 5. 🗑️ LIMPIAR ARCHIVOS INNECESARIOS
**Impacto**: Reducción variable

**Archivos a revisar**:
- `.bak` (backups) - ya excluidos del build
- `~` (archivos temporales) - ya excluidos
- `.kra` (archivos Krita) - ya excluidos
- Archivos duplicados
- Imágenes no utilizadas

### 6. 📦 COMPRIMIR TEXTURAS GUI
**Impacto**: Reducción de ~10-30 MB

**Acción**: Comprimir imágenes de la GUI (botones, frames, etc.)
- Usar compresión PNG nivel 9 (ya implementado)
- Considerar WebP para elementos GUI (si Ren'Py lo soporta)

### 7. 🔍 ANÁLISIS DE ARCHIVOS GRANDES
**Acción**: Identificar archivos individuales > 2 MB

Ejecutar:
```powershell
Get-ChildItem -Path "game" -Recurse -File | Where-Object {$_.Length -gt 2MB} | Sort-Object Length -Descending
```

Luego optimizar manualmente los archivos más grandes.

## Plan de Acción Recomendado

### Fase 1: Inmediata (Mayor Impacto)
1. ✅ Ejecutar `normalize_resolutions.py` para:
   - Normalizar resoluciones a 1920x1080
   - Convertir PNG sin transparencia a JPG
   - **Resultado esperado**: Reducción de ~500-550 MB

### Fase 2: Optimización de Build
2. Habilitar archivo de imágenes en `options.rpy`
3. **Resultado esperado**: Reducción adicional de ~50-100 MB en distribución

### Fase 3: Optimización Adicional
4. Optimizar audio
5. Limpiar archivos innecesarios
6. **Resultado esperado**: Reducción adicional de ~20-50 MB

## Estimación Final

**Tamaño actual**: ~835 MB (solo imágenes)
**Tamaño optimizado**: ~250-300 MB (solo imágenes)
**Reducción total**: ~65-70% del tamaño de imágenes

**Tamaño total del juego** (estimado):
- Actual: ~1-1.5 GB
- Optimizado: ~400-600 MB
- **Reducción**: ~60-70%

## Scripts Disponibles

1. **normalize_resolutions.py** - Normaliza resoluciones y convierte PNG→JPG
2. **compress_aggressive.py** - Compresión agresiva (mantiene 1920x1080)
3. **compress_large_files.py** - Comprime archivos > 2 MB

## Notas Importantes

⚠️ **Hacer backup antes de optimizar**: Los scripts modifican archivos permanentemente

⚠️ **PNG con transparencia**: No se convertirán a JPG automáticamente (se mantiene la transparencia)

✅ **Calidad**: La conversión PNG→JPG usa calidad 85, que mantiene buena calidad visual

✅ **Reversible**: Si necesitas revertir, tendrás que restaurar desde backup

