#!/usr/bin/env python3
"""
Script de compresión agresiva para reducir peso a la mitad
Mantiene resolución 1920x1080 pero comprime más agresivamente
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image

# Resolución objetivo
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

# Configuración de compresión agresiva
PNG_COMPRESS_LEVEL = 9  # Máxima compresión PNG
PNG_OPTIMIZE = True
JPG_QUALITY = 75  # Calidad más baja pero aún buena
CONVERT_PNG_TO_JPG = True  # Convierte PNG sin transparencia a JPG

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


def compress_png_aggressive(image_path, output_path=None):
    """
    Comprime PNG agresivamente
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, porcentaje_reducción)
    """
    if output_path is None:
        output_path = image_path
    
    original_size = get_file_size_mb(image_path)
    
    try:
        img = Image.open(image_path)
        
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


def compress_jpg_aggressive(image_path, output_path=None, quality=75):
    """
    Comprime JPG agresivamente
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
        
        return original_size, new_size, reduction
        
    except Exception as e:
        print(f"Error comprimiendo {image_path}: {e}")
        return original_size, original_size, 0


def convert_png_to_jpg_aggressive(image_path, quality=75):
    """
    Convierte PNG sin transparencia a JPG (más compresión)
    Retorna: (tamaño_original_mb, tamaño_nuevo_mb, porcentaje_reducción, convertido)
    """
    original_size = get_file_size_mb(image_path)
    
    try:
        img = Image.open(image_path)
        
        # Solo convertir si no tiene transparencia
        if has_transparency(img):
            return original_size, original_size, 0, False
        
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
            return original_size, jpg_size, reduction, True
        else:
            # Si el JPG es más grande, mantener el PNG
            os.remove(jpg_path)
            return original_size, original_size, 0, False
        
    except Exception as e:
        print(f"Error convirtiendo {image_path}: {e}")
        return original_size, original_size, 0, False


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
        description='Compresión agresiva para reducir peso a la mitad (mantiene 1920x1080)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Este script comprime agresivamente todas las imágenes:
  - Mantiene resolución 1920x1080
  - PNG: Máxima compresión (nivel 9)
  - JPG: Calidad 75 (más compresión)
  - Convierte PNG sin transparencia a JPG (más compresión)

Objetivo: Reducir peso total a la mitad

Ejemplos:
  python compress_aggressive.py                    # Comprime todas las imágenes
  python compress_aggressive.py --dry-run            # Solo muestra estadísticas
  python compress_aggressive.py --quality 70         # Calidad JPG 70 (más agresivo)
  python compress_aggressive.py --no-convert        # No convierte PNG a JPG
        """
    )
    parser.add_argument('--quality', type=int, default=JPG_QUALITY,
                        help=f'Calidad JPG (default: {JPG_QUALITY}, más bajo = más compresión)')
    parser.add_argument('--no-convert', action='store_true',
                        help='No convierte PNG sin transparencia a JPG')
    parser.add_argument('--dry-run', action='store_true',
                        help='Solo muestra estadísticas sin comprimir archivos')
    
    args = parser.parse_args()
    
    # Obtener directorio base
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    print("=" * 60)
    print("Compresor Agresivo - Reducir Peso a la Mitad")
    print("=" * 60)
    print(f"\nConfiguración:")
    print(f"  - Resolución: {TARGET_WIDTH}x{TARGET_HEIGHT} (mantiene)")
    print(f"  - Compresión PNG: Nivel {PNG_COMPRESS_LEVEL}/9 (máxima)")
    print(f"  - Calidad JPG: {args.quality} (agresiva)")
    print(f"  - Convertir PNG→JPG: {'No' if args.no_convert else 'Sí (sin transparencia)'}")
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
    converted = 0
    errors = 0
    
    # Procesar cada imagen
    for i, img_path in enumerate(images, 1):
        rel_path = img_path.relative_to(base_dir)
        print(f"[{i}/{len(images)}] Procesando: {rel_path}")
        
        ext = img_path.suffix.lower()
        original_size = get_file_size_mb(img_path)
        total_original += original_size
        
        if args.dry_run:
            # Estimación conservadora
            if ext == '.png' and not args.no_convert:
                # Puede convertirse a JPG
                estimated_reduction = 50  # 50% si se convierte
            else:
                estimated_reduction = 30  # 30% si solo comprime
            
            estimated_new = original_size * (1 - estimated_reduction / 100)
            total_new += estimated_new
            processed += 1
            print(f"  [DRY RUN] {original_size:.2f} MB -> ~{estimated_new:.2f} MB (~{estimated_reduction:.1f}% estimado)")
        else:
            if ext == '.png':
                # Intentar convertir a JPG si no tiene transparencia y está permitido
                if not args.no_convert:
                    orig, new, reduction, was_converted = convert_png_to_jpg_aggressive(
                        img_path,
                        quality=args.quality
                    )
                    if was_converted:
                        converted += 1
                        print(f"  🔄 PNG→JPG: {orig:.2f} MB -> {new:.2f} MB ({reduction:.1f}% reducción)")
                        total_new += new
                        processed += 1
                        continue
                
                # Si no se convirtió, comprimir PNG
                orig, new, reduction = compress_png_aggressive(img_path)
                
            elif ext in ('.jpg', '.jpeg'):
                orig, new, reduction = compress_jpg_aggressive(img_path, quality=args.quality)
            else:
                print(f"  ⚠ Formato no soportado: {ext}")
                errors += 1
                continue
            
            total_new += new
            processed += 1
            
            if reduction > 0:
                print(f"  ✓ {orig:.2f} MB -> {new:.2f} MB ({reduction:.1f}% reducción)")
            elif reduction < 0:
                print(f"  ⚠ {orig:.2f} MB -> {new:.2f} MB (aumentó {abs(reduction):.1f}%)")
            else:
                print(f"  → {orig:.2f} MB (sin cambios)")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
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
        target_reduction = 50  # Objetivo: 50%
        
        print(f"Espacio ahorrado: {space_saved:.2f} MB ({space_saved/1024:.2f} GB)")
        print(f"Reducción total: {total_reduction:.1f}%")
        
        if total_reduction >= target_reduction:
            print(f"✅ Objetivo alcanzado: {total_reduction:.1f}% >= {target_reduction}%")
        else:
            print(f"⚠ Objetivo no alcanzado: {total_reduction:.1f}% < {target_reduction}%")
            print(f"   Considera usar --quality 70 o --quality 65 para más compresión")
    
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











