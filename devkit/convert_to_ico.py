#!/usr/bin/env python3
"""
Script para convertir una imagen PNG a formato ICO para usar como icono del ejecutable
"""

import sys
from pathlib import Path
from PIL import Image

def convert_png_to_ico(png_path, ico_path=None, sizes=None):
    """
    Convierte un PNG a ICO con múltiples tamaños
    
    Args:
        png_path: Ruta al archivo PNG
        ico_path: Ruta de salida para el ICO (opcional)
        sizes: Lista de tamaños para el ICO (por defecto: [16, 32, 48, 64, 128, 256])
    """
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    png_file = Path(png_path)
    if not png_file.exists():
        print(f"Error: El archivo {png_path} no existe")
        return False
    
    if ico_path is None:
        ico_path = png_file.with_suffix('.ico')
    else:
        ico_path = Path(ico_path)
    
    try:
        # Abrir imagen original
        img = Image.open(png_file)
        
        # Convertir a RGB si tiene transparencia (ICO no soporta RGBA directamente)
        if img.mode == 'RGBA':
            # Crear fondo blanco para transparencia
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Usar canal alpha como máscara
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Crear lista de imágenes en diferentes tamaños
        ico_images = []
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            ico_images.append(resized)
        
        # Guardar como ICO
        ico_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(ico_path), format='ICO', sizes=[(s, s) for s in sizes])
        
        print(f"[OK] Convertido: {png_file.name} -> {ico_path.name}")
        print(f"  Tamanos incluidos: {', '.join(map(str, sizes))}px")
        print(f"  Ubicacion: {ico_path}")
        return True
        
    except Exception as e:
        print(f"Error al convertir: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python convert_to_ico.py <archivo.png> [archivo.ico]")
        print()
        print("Ejemplos:")
        print("  python convert_to_ico.py game/gui/window_icon.png")
        print("  python convert_to_ico.py game/gui/window_icon.png icon.ico")
        return
    
    png_path = sys.argv[1]
    ico_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = convert_png_to_ico(png_path, ico_path)
    
    if success:
        print()
        print("=" * 60)
        print("IMPORTANTE: Para usar este icono en Ren'Py:")
        print("=" * 60)
        print("1. Coloca el archivo .ico en la raíz del proyecto o en game/")
        print("2. Edita game/scripts/core/options.rpy")
        print("3. Descomenta y configura: define build.icon = 'icon.ico'")
        print("=" * 60)

if __name__ == '__main__':
    main()

