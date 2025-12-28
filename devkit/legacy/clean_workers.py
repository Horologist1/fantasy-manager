#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para limpiar campos vacíos de images_folder/image_folder en archivos de workers"""

import json
from pathlib import Path

def clean_workers_file(file_path):
    """Limpiar campos vacíos de un archivo de workers"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"Skipping {file_path.name}: not a list")
            return False
        
        cleaned = False
        for worker in data:
            # Eliminar images_folder/image_folder si están vacíos
            if 'images_folder' in worker and (worker['images_folder'] == '' or worker['images_folder'] is None):
                del worker['images_folder']
                cleaned = True
            if 'image_folder' in worker and (worker['image_folder'] == '' or worker['image_folder'] is None):
                del worker['image_folder']
                cleaned = True
        
        if cleaned:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Cleaned {file_path.name}")
            return True
        else:
            print(f"No changes needed in {file_path.name}")
            return False
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return False

if __name__ == "__main__":
    # Buscar archivos de workers
    workers_dir = Path("game/data/workers")
    
    if not workers_dir.exists():
        print(f"Directory {workers_dir} not found")
        exit(1)
    
    worker_files = [
        workers_dir / "workers_sfw_unique.json",
        workers_dir / "workers_sfw_other.json",
        workers_dir / "workers_nsfw_unique.json",
        workers_dir / "workers_nsfw_other.json"
    ]
    
    cleaned_count = 0
    for file_path in worker_files:
        if file_path.exists():
            if clean_workers_file(file_path):
                cleaned_count += 1
    
    print(f"\nCleaned {cleaned_count} file(s)")


