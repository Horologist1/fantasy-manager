#!/usr/bin/env python3
"""
Script para comprimir imágenes que pesan más de 2 MB
Mantiene resolución 1920x1080 pero comprime más agresivamente
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image

# Umbral de tamaño (MB)
SIZE_THRESHOLD_MB = 2.0

# Resolución objetivo (mantener)
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

# Configuración de compresión agresiva para archivos grandes
PNG_COMPRESS_LEVEL = 9  # Máxima compresión PNG
PNG_OPTIMIZE = True
JPG_QUALITY = 70  # Calidad más baja para archivos grandes
CONVERT_PNG_TO_JPG = True  # Convierte PNG sin transparencia a JPG
FORCE_CONVERT_LARGE_PNG = True  # Por defecto, convierte PNG grandes a JPG incluso con transparencia

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
    '.kra'
]


def get_file_size_mb(filepath):
    """Obtiene el tamaño de un archivo en MB"""
    return os.path.getsize(filepath) / (1024 * 1024)


def has_transparency(img):
    """Verifica si una imagen tiene transparencia"""
    if img.mode in ('RGBA', 'LA'):
        return True
    if img.mode == 'P':
        return 'transparency' in img.info
    return False


def should_exclude(filepath):
    """Verifica si un archivo debe ser excluido"""
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath_str:
            return True
    return False


def compress_png_aggressive(image_path, output_path=None, force_convert_to_jpg=False, jpg_quality=70):
    """
    Comprime PNG agresivamente
    Si force_convert_to_jpg=True, convierte a JPG incluso si tiene transparencia (perdiendo transparencia)
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, porcentaje_reducción, resolución, convertido)
    """
    if output_path is None:
        output_path = image_path
    
    original_size = get_file_size_mb(image_path)
    
    try:
        img = Image.open(image_path)
        width, height = img.size
        original_mode = img.mode
        has_alpha = has_transparency(img)
        
        # Si se fuerza conversión a JPG, convertir siempre
        if force_convert_to_jpg:
            # Convertir a RGB (perdiendo transparencia si la tiene)
            if img.mode == 'RGBA':
                # Crear fondo blanco para transparencia
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Guardar como JPG
            jpg_path = output_path.with_suffix('.jpg')
            img.save(
                jpg_path,
                'JPEG',
                quality=jpg_quality,
                optimize=True,
                subsampling=-1
            )
            
            jpg_size = get_file_size_mb(jpg_path)
            if jpg_size < original_size:
                os.remove(image_path)
                reduction = ((original_size - jpg_size) / original_size * 100) if original_size > 0 else 0
                return original_size, jpg_size, reduction, (width, height), True
            else:
                os.remove(jpg_path)
        
        # Si no se convierte, comprimir PNG normal
        # Mantener modo original
        if img.mode == 'RGBA':
            img = img.convert('RGBA')
        elif img.mode not in ('RGB', 'RGBA', 'L', 'P'):
            img = img.convert('RGB')
        
        # Guardar con máxima compresión
        img.save(
            output_path,
            'PNG',
            optimize=PNG_OPTIMIZE,
            compress_level=PNG_COMPRESS_LEVEL
        )
        
        new_size = get_file_size_mb(output_path)
        reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
        
        return original_size, new_size, reduction, (width, height), False
        
    except Exception as e:
        print(f"Error comprimiendo {image_path}: {e}")
        return original_size, original_size, 0, (0, 0), False


def compress_jpg_aggressive(image_path, output_path=None, quality=70):
    """
    Comprime JPG agresivamente
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, porcentaje_reducción, resolución)
    """
    if output_path is None:
        output_path = image_path
    
    original_size = get_file_size_mb(image_path)
    
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Convertir a RGB si no lo está
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Guardar con compresión agresiva
        img.save(
            output_path,
            'JPEG',
            quality=quality,
            optimize=True,
            subsampling=-1  # Automático para mejor compresión
        )
        
        new_size = get_file_size_mb(output_path)
        reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
        
        return original_size, new_size, reduction, (width, height)
        
    except Exception as e:
        print(f"Error comprimiendo {image_path}: {e}")
        return original_size, original_size, 0, (0, 0)


def convert_png_to_jpg_aggressive(image_path, quality=70):
    """
    Convierte PNG sin transparencia a JPG (más compresión)
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, porcentaje_reducción, convertido, resolución)
    """
    original_size = get_file_size_mb(image_path)
    
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Solo convertir si no tiene transparencia
        if has_transparency(img):
            return original_size, original_size, 0, False, (width, height)
        
        # Convertir a RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Crear ruta JPG
        jpg_path = image_path.with_suffix('.jpg')
        
        # Guardar como JPG
        img.save(
            jpg_path,
            'JPEG',
            quality=quality,
            optimize=True,
            subsampling=-1
        )
        
        jpg_size = get_file_size_mb(jpg_path)
        
        # Solo reemplazar si el JPG es más pequeño
        if jpg_size < original_size:
            os.remove(image_path)
            reduction = ((original_size - jpg_size) / original_size * 100) if original_size > 0 else 0
            return original_size, jpg_size, reduction, True, (width, height)
        else:
            # Si el JPG es más grande, mantener el PNG
            os.remove(jpg_path)
            return original_size, original_size, 0, False, (width, height)
        
    except Exception as e:
        print(f"Error convirtiendo {image_path}: {e}")
        return original_size, original_size, 0, False, (0, 0)


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
        description='Comprime imágenes que pesan más de 2 MB (mantiene 1920x1080)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Este script solo comprime imágenes que pesan más de 2 MB:
  - Mantiene resolución 1920x1080
  - PNG: Máxima compresión (nivel 9)
  - JPG: Calidad 70 (agresiva)
  - Convierte PNG sin transparencia a JPG

Ejemplos:
  python compress_large_files.py                    # Umbral 2 MB por defecto
  python compress_large_files.py --threshold 3      # Umbral 3 MB
  python compress_large_files.py --quality 65        # Calidad 65 (más agresivo)
  python compress_large_files.py --dry-run            # Solo muestra estadísticas
        """
    )
    parser.add_argument('--threshold', type=float, default=SIZE_THRESHOLD_MB,
                        help=f'Umbral de tamaño en MB (default: {SIZE_THRESHOLD_MB} MB)')
    parser.add_argument('--quality', type=int, default=JPG_QUALITY,
                        help=f'Calidad JPG (default: {JPG_QUALITY}, más bajo = más compresión)')
    parser.add_argument('--no-convert', action='store_true',
                        help='No convierte PNG sin transparencia a JPG')
    parser.add_argument('--force-convert', action='store_true',
                        help='Fuerza conversión PNG→JPG incluso con transparencia (pierde transparencia)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo muestra estadísticas sin comprimir archivos')
    
    args = parser.parse_args()
    
    # Obtener directorio base
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    print("=" * 60)
    print("Compresor de Archivos Grandes (>2 MB)")
    print("=" * 60)
    print(f"\nConfiguración:")
    print(f"  - Umbral: {args.threshold} MB")
    print(f"  - Resolución: {TARGET_WIDTH}x{TARGET_HEIGHT} (mantiene)")
    print(f"  - Compresión PNG: Nivel {PNG_COMPRESS_LEVEL}/9 (máxima)")
    print(f"  - Calidad JPG: {args.quality} (agresiva)")
    print(f"  - Convertir PNG→JPG: {'No' if args.no_convert else ('Forzado (pierde transparencia)' if args.force_convert else 'Sí (sin transparencia)')}")
    if args.dry_run:
        print(f"  - Modo: DRY RUN (solo simulación)")
    print()
    
    # Encontrar todas las imágenes
    print("Buscando imágenes...")
    images = find_images(base_dir)
    
    if not images:
        print("No se encontraron imágenes para procesar.")
        return
    
    print(f"Se encontraron {len(images)} imágenes para analizar.\n")
    
    # Filtrar imágenes grandes
    large_images = []
    total_size_large = 0
    
    print("Analizando tamaños...")
    for img_path in images:
        size_mb = get_file_size_mb(img_path)
        if size_mb > args.threshold:
            large_images.append((img_path, size_mb))
            total_size_large += size_mb
    
    print(f"Imágenes mayores a {args.threshold} MB: {len(large_images)}")
    print(f"Tamaño total de imágenes grandes: {total_size_large:.2f} MB ({total_size_large/1024:.2f} GB)\n")
    
    if not large_images:
        print("No hay imágenes que superen el umbral. ¡Todo está optimizado!")
        return
    
    # Estadísticas
    total_original = 0
    total_new = 0
    processed = 0
    converted = 0
    errors = 0
    
    # Procesar cada imagen grande
    for i, (img_path, original_size) in enumerate(large_images, 1):
        rel_path = img_path.relative_to(base_dir)
        print(f"[{i}/{len(large_images)}] {rel_path}")
        print(f"  Tamaño: {original_size:.2f} MB")
        
        total_original += original_size
        ext = img_path.suffix.lower()
        
        if args.dry_run:
            # Estimación conservadora
            if ext == '.png' and not args.no_convert:
                estimated_reduction = 50  # 50% si se convierte
            else:
                estimated_reduction = 35  # 35% si solo comprime
            
            estimated_new = original_size * (1 - estimated_reduction / 100)
            total_new += estimated_new
            processed += 1
            print(f"  [DRY RUN] Estimado: {original_size:.2f} MB -> ~{estimated_new:.2f} MB (~{estimated_reduction:.1f}%)")
        else:
            if ext == '.png':
                # Para archivos grandes, intentar convertir a JPG primero (más compresión)
                should_force_convert = args.force_convert or (FORCE_CONVERT_LARGE_PNG and original_size > args.threshold)
                
                if should_force_convert and not args.no_convert:
                    # Forzar conversión a JPG (pierde transparencia pero reduce mucho)
                    orig, new, reduction, resolution, was_converted = compress_png_aggressive(
                        img_path,
                        force_convert_to_jpg=True,
                        jpg_quality=args.quality
                    )
                    if was_converted:
                        converted += 1
                        print(f"  🔄 PNG→JPG (forzado): {orig:.2f} MB -> {new:.2f} MB ({reduction:.1f}% reducción) | {resolution[0]}x{resolution[1]}")
                        total_new += new
                        processed += 1
                        continue
                
                # Intentar convertir a JPG si no tiene transparencia y está permitido
                if not args.no_convert:
                    orig, new, reduction, was_converted, resolution = convert_png_to_jpg_aggressive(
                        img_path,
                        quality=args.quality
                    )
                    if was_converted:
                        converted += 1
                        print(f"  🔄 PNG→JPG: {orig:.2f} MB -> {new:.2f} MB ({reduction:.1f}% reducción) | {resolution[0]}x{resolution[1]}")
                        total_new += new
                        processed += 1
                        continue
                
                # Si no se convirtió, comprimir PNG (último recurso)
                orig, new, reduction, resolution, _ = compress_png_aggressive(img_path)
                
            elif ext in ('.jpg', '.jpeg'):
                orig, new, reduction, resolution = compress_jpg_aggressive(img_path, quality=args.quality)
            else:
                print(f"  ⚠ Formato no soportado: {ext}")
                errors += 1
                continue
            
            total_new += new
            processed += 1
            
            if reduction > 0:
                print(f"  ✓ {orig:.2f} MB -> {new:.2f} MB ({reduction:.1f}% reducción) | {resolution[0]}x{resolution[1]}")
            elif reduction < 0:
                print(f"  ⚠ {orig:.2f} MB -> {new:.2f} MB (aumentó {abs(reduction):.1f}%) | {resolution[0]}x{resolution[1]}")
            else:
                print(f"  → {orig:.2f} MB (sin cambios) | {resolution[0]}x{resolution[1]}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Imágenes analizadas: {len(images)}")
    print(f"Imágenes > {args.threshold} MB: {len(large_images)}")
    print(f"Imágenes procesadas: {processed}")
    if converted > 0:
        print(f"Imágenes convertidas PNG→JPG: {converted}")
    if errors > 0:
        print(f"Errores: {errors}")
    print(f"Tamaño original total: {total_original:.2f} MB ({total_original/1024:.2f} GB)")
    print(f"Tamaño nuevo total: {total_new:.2f} MB ({total_new/1024:.2f} GB)")
    
    if total_original > 0:
        total_reduction = ((total_original - total_new) / total_original) * 100
        space_saved = total_original - total_new
        print(f"Espacio ahorrado: {space_saved:.2f} MB ({space_saved/1024:.2f} GB)")
        print(f"Reducción total: {total_reduction:.1f}%")
    
    if args.dry_run:
        print("\n⚠ Este fue un DRY RUN. No se modificaron archivos.")
        print("Ejecuta sin --dry-run para comprimir las imágenes.")
    
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

