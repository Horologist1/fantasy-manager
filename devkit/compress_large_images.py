#!/usr/bin/env python3
"""
Script de compresión casi lossless para imágenes 1920x1080
Solo comprime imágenes que pesan demasiado para su resolución
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image

# Resolución objetivo
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
TARGET_PIXELS = TARGET_WIDTH * TARGET_HEIGHT  # 2,073,600 píxeles

# Umbrales de tamaño (bytes por píxel)
# Si una imagen tiene más bytes/píxel que estos valores, se comprimirá
PNG_THRESHOLD_BPP = 2.0  # PNG: más de 2 bytes/píxel = demasiado pesado
JPG_THRESHOLD_BPP = 1.5  # JPG: más de 1.5 bytes/píxel = demasiado pesado

# Configuración de compresión casi lossless
PNG_COMPRESS_LEVEL = 9  # Máxima compresión PNG
PNG_OPTIMIZE = True
JPG_QUALITY = 92  # Calidad muy alta (casi lossless)

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


def get_bytes_per_pixel(filepath):
    """
    Calcula bytes por píxel de una imagen
    Retorna: (bytes_per_pixel, width, height, file_size_bytes)
    """
    try:
        img = Image.open(filepath)
        width, height = img.size
        pixels = width * height
        file_size = os.path.getsize(filepath)
        
        if pixels > 0:
            bpp = file_size / pixels
        else:
            bpp = 0
        
        return bpp, width, height, file_size
    except Exception as e:
        return 0, 0, 0, 0


def should_compress(image_path, ext):
    """
    Determina si una imagen debe comprimirse basándose en su tamaño
    Retorna: (debe_comprimir, razón, bytes_per_pixel)
    """
    bpp, width, height, file_size = get_bytes_per_pixel(image_path)
    
    # Solo procesar imágenes 1920x1080 (o muy cercanas)
    if width != TARGET_WIDTH or height != TARGET_HEIGHT:
        return False, f"Resolución {width}x{height} (no es {TARGET_WIDTH}x{TARGET_HEIGHT})", bpp
    
    # Verificar umbral según formato
    if ext == '.png':
        if bpp > PNG_THRESHOLD_BPP:
            return True, f"PNG con {bpp:.2f} bytes/píxel (umbral: {PNG_THRESHOLD_BPP})", bpp
        else:
            return False, f"PNG ya optimizado ({bpp:.2f} bytes/píxel)", bpp
    elif ext in ('.jpg', '.jpeg'):
        if bpp > JPG_THRESHOLD_BPP:
            return True, f"JPG con {bpp:.2f} bytes/píxel (umbral: {JPG_THRESHOLD_BPP})", bpp
        else:
            return False, f"JPG ya optimizado ({bpp:.2f} bytes/píxel)", bpp
    
    return False, "Formato no soportado", bpp


def compress_png_lossless(image_path, output_path=None):
    """
    Comprime PNG con máxima compresión (casi lossless)
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, porcentaje_reducción)
    """
    if output_path is None:
        output_path = image_path
    
    original_size = get_file_size_mb(image_path)
    
    try:
        img = Image.open(image_path)
        original_mode = img.mode
        
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
        
        return original_size, new_size, reduction
        
    except Exception as e:
        print(f"Error comprimiendo {image_path}: {e}")
        return original_size, original_size, 0


def compress_jpg_lossless(image_path, output_path=None):
    """
    Comprime JPG con calidad casi lossless
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, porcentaje_reducción)
    """
    if output_path is None:
        output_path = image_path
    
    original_size = get_file_size_mb(image_path)
    
    try:
        img = Image.open(image_path)
        
        # Convertir a RGB si no lo está
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Guardar con calidad casi lossless
        img.save(
            output_path,
            'JPEG',
            quality=JPG_QUALITY,
            optimize=True,
            subsampling=0  # Sin subsampling para mejor calidad
        )
        
        new_size = get_file_size_mb(output_path)
        reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
        
        return original_size, new_size, reduction
        
    except Exception as e:
        print(f"Error comprimiendo {image_path}: {e}")
        return original_size, original_size, 0


def should_exclude(filepath):
    """Verifica si un archivo debe ser excluido"""
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath_str:
            return True
    return False


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
        description='Compresión casi lossless para imágenes 1920x1080 que pesan demasiado',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Este script solo comprime imágenes que:
  - Tienen resolución 1920x1080
  - Pesan demasiado para su resolución (umbral configurable)

Calidad casi lossless:
  - PNG: Compresión nivel 9 (máxima)
  - JPG: Calidad 92 (muy alta)

Ejemplos:
  python compress_large_images.py                    # Comprime imágenes grandes
  python compress_large_images.py --dry-run            # Solo muestra estadísticas
  python compress_large_images.py --threshold-png 2.5  # Ajustar umbral PNG
        """
    )
    parser.add_argument('--threshold-png', type=float, default=PNG_THRESHOLD_BPP,
                        help=f'Umbral PNG en bytes/píxel (default: {PNG_THRESHOLD_BPP})')
    parser.add_argument('--threshold-jpg', type=float, default=JPG_THRESHOLD_BPP,
                        help=f'Umbral JPG en bytes/píxel (default: {JPG_THRESHOLD_BPP})')
    parser.add_argument('--quality', type=int, default=JPG_QUALITY,
                        help=f'Calidad JPG (default: {JPG_QUALITY}, casi lossless)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo muestra estadísticas sin comprimir archivos')
    
    args = parser.parse_args()
    
    # Obtener directorio base
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    print("=" * 60)
    print("Compresor Casi Lossless - Imágenes 1920x1080")
    print("=" * 60)
    print(f"\nConfiguración:")
    print(f"  - Resolución objetivo: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    print(f"  - Umbral PNG: {args.threshold_png} bytes/píxel")
    print(f"  - Umbral JPG: {args.threshold_jpg} bytes/píxel")
    print(f"  - Calidad JPG: {args.quality} (casi lossless)")
    print(f"  - Compresión PNG: Nivel {PNG_COMPRESS_LEVEL}/9")
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
    
    # Estadísticas
    total_original = 0
    total_new = 0
    processed = 0
    compressed = 0
    skipped = 0
    errors = 0
    size_stats = {
        'needs_compression': [],
        'already_optimized': [],
        'wrong_resolution': []
    }
    
    # Analizar y procesar cada imagen
    print("Analizando imágenes...")
    for i, img_path in enumerate(images, 1):
        rel_path = img_path.relative_to(base_dir)
        ext = img_path.suffix.lower()
        original_size = get_file_size_mb(img_path)
        total_original += original_size
        
        should_comp, reason, bpp = should_compress(img_path, ext)
        
        if not should_comp:
            # No necesita compresión
            skipped += 1
            if "no es" in reason:
                size_stats['wrong_resolution'].append((rel_path, reason, bpp))
            else:
                size_stats['already_optimized'].append((rel_path, reason, bpp))
            
            if i % 50 == 0 or i == len(images):
                print(f"[{i}/{len(images)}] Analizadas...", end='\r')
            continue
        
        # Necesita compresión
        size_stats['needs_compression'].append((rel_path, reason, bpp, original_size))
        
        print(f"[{i}/{len(images)}] {rel_path}")
        print(f"  {reason} | {original_size:.2f} MB")
        
        if args.dry_run:
            # Estimación conservadora
            estimated_reduction = 20  # 20% de reducción estimada
            estimated_new = original_size * (1 - estimated_reduction / 100)
            total_new += estimated_new
            processed += 1
            compressed += 1
            print(f"  [DRY RUN] Estimado: {original_size:.2f} MB -> ~{estimated_new:.2f} MB (~{estimated_reduction:.1f}%)")
        else:
            # Comprimir
            if ext == '.png':
                orig, new, reduction = compress_png_lossless(img_path)
            elif ext in ('.jpg', '.jpeg'):
                orig, new, reduction = compress_jpg_lossless(img_path)
            else:
                errors += 1
                continue
            
            total_new += new
            processed += 1
            compressed += 1
            
            if reduction > 0:
                print(f"  ✓ {orig:.2f} MB -> {new:.2f} MB ({reduction:.1f}% reducción)")
            else:
                print(f"  → {orig:.2f} MB (sin cambios)")
    
    print()  # Nueva línea después del progreso
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Imágenes analizadas: {len(images)}")
    print(f"Imágenes comprimidas: {compressed}")
    print(f"Imágenes ya optimizadas: {len(size_stats['already_optimized'])}")
    print(f"Imágenes con resolución incorrecta: {len(size_stats['wrong_resolution'])}")
    if errors > 0:
        print(f"Errores: {errors}")
    
    if compressed > 0:
        print(f"\nTamaño original (solo comprimidas): {sum(s[3] for s in size_stats['needs_compression']):.2f} MB")
        if not args.dry_run:
            print(f"Tamaño nuevo (solo comprimidas): {total_new - (total_original - sum(s[3] for s in size_stats['needs_compression'])):.2f} MB")
            space_saved = sum(s[3] for s in size_stats['needs_compression']) - (total_new - (total_original - sum(s[3] for s in size_stats['needs_compression'])))
            print(f"Espacio ahorrado: {space_saved:.2f} MB")
    
    # Mostrar ejemplos
    if size_stats['needs_compression']:
        print(f"\nEjemplos de imágenes que se comprimieron:")
        for path, reason, bpp, size in size_stats['needs_compression'][:5]:
            print(f"  - {path}: {reason} ({size:.2f} MB)")
    
    if size_stats['already_optimized']:
        print(f"\nEjemplos de imágenes ya optimizadas:")
        for path, reason, bpp in size_stats['already_optimized'][:5]:
            print(f"  - {path}: {reason}")
    
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











