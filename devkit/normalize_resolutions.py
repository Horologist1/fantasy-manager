#!/usr/bin/env python3
"""
Script para normalizar resoluciones de imágenes a 1920x1080
- Redimensiona imágenes mayores a 1920x1080
- Redimensiona imágenes menores a 1920x1080
- Mantiene proporción de aspecto (aspect ratio)
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageOps

# Resolución objetivo
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT  # 16:9 = 1.777...

# Carpetas a procesar
IMAGE_FOLDERS = [
    'game/images/workers'
]

# Extensiones de imagen a procesar
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}

# Archivos/carpetas a excluir
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.bak',
    '~',
    '.kra'  # Archivos de Krita
]


def get_file_size_mb(filepath):
    """Obtiene el tamaño de un archivo en MB"""
    return os.path.getsize(filepath) / (1024 * 1024)


def should_exclude(filepath):
    """Verifica si un archivo debe ser excluido"""
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath_str:
            return True
    return False


def resize_with_aspect_ratio(img, target_width, target_height, method='fit'):
    """
    Redimensiona una imagen manteniendo el aspect ratio
    
    Args:
        img: Imagen PIL
        target_width: Ancho objetivo
        target_height: Alto objetivo
        method: 'fit' (ajusta dentro), 'fill' (rellena con padding), 'crop' (recorta)
    
    Returns:
        Imagen redimensionada
    """
    original_width, original_height = img.size
    original_ratio = original_width / original_height
    target_ratio = target_width / target_height
    
    if method == 'fit':
        # Ajusta la imagen dentro del área objetivo manteniendo proporción
        if original_ratio > target_ratio:
            # Imagen más ancha - ajustar por ancho
            new_width = target_width
            new_height = int(target_width / original_ratio)
        else:
            # Imagen más alta - ajustar por alto
            new_height = target_height
            new_width = int(target_height * original_ratio)
        
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crear imagen del tamaño objetivo con fondo transparente o negro
        if img.mode == 'RGBA':
            # Mantener transparencia
            result = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
            # Centrar la imagen
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            result.paste(resized, (x_offset, y_offset), resized if img.mode == 'RGBA' else None)
        else:
            # Fondo negro para imágenes sin transparencia
            result = Image.new('RGB', (target_width, target_height), (0, 0, 0))
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            result.paste(resized, (x_offset, y_offset))
        
        return result
    
    elif method == 'fill':
        # Rellena con padding manteniendo proporción
        return ImageOps.pad(img, (target_width, target_height), Image.Resampling.LANCZOS, color='black')
    
    elif method == 'crop':
        # Recorta para llenar exactamente el área
        return ImageOps.fit(img, (target_width, target_height), Image.Resampling.LANCZOS)
    
    else:
        # Por defecto, solo redimensionar estirando (no recomendado)
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def normalize_image(image_path, output_path=None, method='fit', dry_run=False):
    """
    Normaliza una imagen a 1920x1080
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, resolución_original, resolución_nueva, cambió)
    """
    if output_path is None:
        output_path = image_path
    
    original_size = get_file_size_mb(image_path)
    changed = False
    
    try:
        # Abrir imagen
        img = Image.open(image_path)
        original_resolution = img.size
        original_mode = img.mode
        
        width, height = original_resolution
        
        # Verificar si necesita normalización
        needs_resize = (width != TARGET_WIDTH or height != TARGET_HEIGHT)
        
        if not needs_resize:
            # Ya está en la resolución correcta
            return original_size, original_size, original_resolution, original_resolution, False
        
        if dry_run:
            # En modo dry-run, solo estimamos
            estimated_new_size = original_size  # Asumimos mismo tamaño
            return original_size, estimated_new_size, original_resolution, (TARGET_WIDTH, TARGET_HEIGHT), True
        
        # Redimensionar manteniendo aspect ratio
        resized_img = resize_with_aspect_ratio(img, TARGET_WIDTH, TARGET_HEIGHT, method=method)
        
        # Guardar
        ext = image_path.suffix.lower()
        if ext == '.png':
            # Mantener transparencia si la tenía
            if original_mode == 'RGBA':
                resized_img = resized_img.convert('RGBA')
            resized_img.save(output_path, 'PNG', optimize=True, compress_level=9)
        elif ext in ('.jpg', '.jpeg'):
            # Convertir a RGB si tiene transparencia
            if resized_img.mode == 'RGBA':
                # Crear fondo blanco para transparencia
                background = Image.new('RGB', resized_img.size, (255, 255, 255))
                background.paste(resized_img, mask=resized_img.split()[3])
                resized_img = background
            elif resized_img.mode != 'RGB':
                resized_img = resized_img.convert('RGB')
            resized_img.save(output_path, 'JPEG', quality=85, optimize=True)
        
        new_size = get_file_size_mb(output_path)
        new_resolution = resized_img.size
        changed = True
        
        return original_size, new_size, original_resolution, new_resolution, True
        
    except Exception as e:
        print(f"Error procesando {image_path}: {e}")
        return original_size, original_size, (0, 0), (0, 0), False


def find_images(base_dir):
    """Encuentra todas las imágenes en las carpetas especificadas"""
    images = []
    base_path = Path(base_dir)
    
    for folder in IMAGE_FOLDERS:
        folder_path = base_path / folder
        if not folder_path.exists():
            print(f"Advertencia: Carpeta {folder_path} no existe")
            continue
        
        for ext in IMAGE_EXTENSIONS:
            for img_path in folder_path.rglob(f'*{ext}'):
                if not should_exclude(img_path):
                    images.append(img_path)
    
    return images


def main():
    parser = argparse.ArgumentParser(
        description='Normaliza resoluciones de imágenes a 1920x1080',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Métodos de redimensionamiento:
  fit   - Ajusta dentro de 1920x1080 manteniendo proporción (con padding)
  fill  - Rellena con padding manteniendo proporción
  crop  - Recorta para llenar exactamente 1920x1080

Ejemplos:
  python normalize_resolutions.py                    # Usa método 'fit' por defecto
  python normalize_resolutions.py --method crop      # Usa método 'crop'
  python normalize_resolutions.py --dry-run          # Solo muestra estadísticas
        """
    )
    parser.add_argument('--method', choices=['fit', 'fill', 'crop'], default='fit',
                        help='Método de redimensionamiento (default: fit)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo muestra estadísticas sin modificar archivos')
    
    args = parser.parse_args()
    
    # Obtener directorio base
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    print("=" * 60)
    print("Normalizador de Resoluciones - Workers")
    print("=" * 60)
    print(f"\nConfiguración:")
    print(f"  - Resolución objetivo: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    print(f"  - Método: {args.method}")
    print(f"  - Carpetas: {', '.join(IMAGE_FOLDERS)}")
    if args.dry_run:
        print(f"  - Modo: DRY RUN (solo simulación)")
    print()
    
    # Encontrar todas las imágenes
    print("Buscando imágenes...")
    images = find_images(base_dir)
    
    if not images:
        print("No se encontraron imágenes para procesar.")
        return
    
    print(f"Se encontraron {len(images)} imágenes para procesar.\n")
    
    # Estadísticas
    total_original = 0
    total_new = 0
    processed = 0
    changed = 0
    errors = 0
    resolution_stats = {}
    needs_resize = []
    
    # Analizar primero (para estadísticas)
    print("Analizando resoluciones...")
    for img_path in images:
        try:
            img = Image.open(img_path)
            resolution = img.size
            resolution_key = f"{resolution[0]}x{resolution[1]}"
            resolution_stats[resolution_key] = resolution_stats.get(resolution_key, 0) + 1
            
            if resolution[0] != TARGET_WIDTH or resolution[1] != TARGET_HEIGHT:
                needs_resize.append((img_path, resolution))
        except Exception as e:
            errors += 1
    
    print(f"\nImágenes que necesitan redimensionamiento: {len(needs_resize)}")
    print(f"Imágenes ya en {TARGET_WIDTH}x{TARGET_HEIGHT}: {len(images) - len(needs_resize)}")
    print()
    
    # Procesar cada imagen
    for i, img_path in enumerate(images, 1):
        rel_path = img_path.relative_to(base_dir)
        print(f"[{i}/{len(images)}] Procesando: {rel_path}")
        
        original_size = get_file_size_mb(img_path)
        total_original += original_size
        
        orig, new, orig_res, new_res, changed_flag = normalize_image(
            img_path,
            method=args.method,
            dry_run=args.dry_run
        )
        
        total_new += new
        processed += 1
        
        if changed_flag:
            changed += 1
            if args.dry_run:
                print(f"  [DRY RUN] {orig_res[0]}x{orig_res[1]} -> {TARGET_WIDTH}x{TARGET_HEIGHT} | {orig:.2f} MB")
            else:
                print(f"  ✓ {orig_res[0]}x{orig_res[1]} -> {new_res[0]}x{new_res[1]} | {orig:.2f} MB -> {new:.2f} MB")
        else:
            print(f"  → {orig_res[0]}x{orig_res[1]} (ya normalizada) | {orig:.2f} MB")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Imágenes procesadas: {processed}")
    print(f"Imágenes modificadas: {changed}")
    print(f"Imágenes ya normalizadas: {processed - changed}")
    if errors > 0:
        print(f"Errores: {errors}")
    print(f"Tamaño original total: {total_original:.2f} MB ({total_original/1024:.2f} GB)")
    print(f"Tamaño nuevo total: {total_new:.2f} MB ({total_new/1024:.2f} GB)")
    
    # Mostrar estadísticas de resoluciones
    if resolution_stats:
        print("\nResoluciones encontradas:")
        print("-" * 60)
        for res, count in sorted(resolution_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            marker = " [OK]" if res == f"{TARGET_WIDTH}x{TARGET_HEIGHT}" else " [NEEDS RESIZE]"
            print(f"  {res}: {count} imágenes{marker}")
        if len(resolution_stats) > 10:
            print(f"  ... y {len(resolution_stats) - 10} resoluciones más")
    
    if args.dry_run:
        print("\n⚠ Este fue un DRY RUN. No se modificaron archivos.")
        print("Ejecuta sin --dry-run para normalizar las imágenes.")
    
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProceso cancelado por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)











