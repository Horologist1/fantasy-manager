#!/usr/bin/env python3
"""
Image Harmonizer for Fantasy Manager
=====================================
Converts PNG/WebP images to JPG with:
- Resolution: 1920x1080 (or smaller, maintaining aspect ratio)
- Quality: 70%
- Skips existing JPGs (already optimized)

Usage:
    python image_harmonizer.py [folder_path]
    
If no folder is specified, processes game/images/workers/
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)

# Configuration
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
QUALITY = 70
SKIP_EXTENSIONS = {'.jpg', '.jpeg'}  # Don't convert these
CONVERT_EXTENSIONS = {'.png', '.webp', '.bmp', '.tiff'}
BACKUP_FOLDER = "_originals_backup"
DRY_RUN = False  # Set to True to preview without making changes

def get_target_size(original_width, original_height):
    """Calculate target size maintaining aspect ratio, max 1920x1080"""
    # If already smaller than target, keep original size
    if original_width <= TARGET_WIDTH and original_height <= TARGET_HEIGHT:
        return original_width, original_height
    
    # Calculate scaling factor
    width_ratio = TARGET_WIDTH / original_width
    height_ratio = TARGET_HEIGHT / original_height
    ratio = min(width_ratio, height_ratio)
    
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    
    return new_width, new_height

def should_convert(filepath):
    """Check if file should be converted"""
    ext = filepath.suffix.lower()
    
    # Skip JPGs
    if ext in SKIP_EXTENSIONS:
        return False, "Already JPG"
    
    # Convert these formats
    if ext in CONVERT_EXTENSIONS:
        return True, f"Will convert {ext} to JPG"
    
    return False, f"Unknown format {ext}"

def convert_image(input_path, output_path, backup_path=None):
    """Convert image to JPG with target resolution and quality"""
    try:
        with Image.open(input_path) as img:
            # Convert to RGB (required for JPG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate target size
            original_size = img.size
            target_size = get_target_size(img.width, img.height)
            
            # Resize if needed
            if target_size != original_size:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save as JPG
            img.save(output_path, 'JPEG', quality=QUALITY, optimize=True)
            
            return True, original_size, target_size
    except Exception as e:
        return False, None, str(e)

def process_folder(folder_path, create_backup=True):
    """Process all images in folder and subfolders"""
    folder = Path(folder_path)
    if not folder.exists():
        print(f"ERROR: Folder not found: {folder}")
        return
    
    print(f"\n{'='*60}")
    print(f"Image Harmonizer - Fantasy Manager")
    print(f"{'='*60}")
    print(f"Folder: {folder}")
    print(f"Target: {TARGET_WIDTH}x{TARGET_HEIGHT} @ {QUALITY}% quality")
    print(f"Mode: {'DRY RUN (no changes)' if DRY_RUN else 'LIVE'}")
    print(f"{'='*60}\n")
    
    # Collect files
    all_files = list(folder.rglob('*'))
    image_files = [f for f in all_files if f.is_file() and f.suffix.lower() in (SKIP_EXTENSIONS | CONVERT_EXTENSIONS)]
    
    # Statistics
    skipped_jpg = 0
    converted = 0
    errors = 0
    saved_bytes = 0
    
    # Process each file
    for filepath in image_files:
        should, reason = should_convert(filepath)
        
        if not should:
            if filepath.suffix.lower() in SKIP_EXTENSIONS:
                skipped_jpg += 1
            continue
        
        # Prepare paths
        output_path = filepath.with_suffix('.jpg')
        backup_path = filepath.parent / BACKUP_FOLDER / filepath.name if create_backup else None
        
        original_size_bytes = filepath.stat().st_size
        
        if DRY_RUN:
            print(f"[DRY RUN] Would convert: {filepath.name}")
            converted += 1
            continue
        
        # Create backup folder if needed
        if backup_path:
            backup_path.parent.mkdir(exist_ok=True)
        
        # Convert
        success, orig_dims, target_dims = convert_image(filepath, output_path, backup_path)
        
        if success:
            new_size_bytes = output_path.stat().st_size
            savings = original_size_bytes - new_size_bytes
            saved_bytes += savings
            
            # Move original to backup (if different file) or delete
            if filepath != output_path:
                if backup_path:
                    filepath.rename(backup_path)
                else:
                    filepath.unlink()
            
            print(f"✓ {filepath.name} -> {output_path.name}")
            print(f"  {orig_dims[0]}x{orig_dims[1]} -> {target_dims[0]}x{target_dims[1]}")
            print(f"  {original_size_bytes//1024}KB -> {new_size_bytes//1024}KB (saved {savings//1024}KB)")
            converted += 1
        else:
            print(f"✗ ERROR: {filepath.name} - {target_dims}")
            errors += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"JPGs skipped (already optimized): {skipped_jpg}")
    print(f"Images converted: {converted}")
    print(f"Errors: {errors}")
    print(f"Total space saved: {saved_bytes/1024/1024:.1f} MB")
    if create_backup and not DRY_RUN:
        print(f"\nOriginals backed up to: {BACKUP_FOLDER}/ subfolders")
    print(f"{'='*60}\n")

def main():
    # Default folder
    script_dir = Path(__file__).parent.parent
    default_folder = script_dir / "game" / "images" / "workers"
    
    # Get folder from args or use default
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = default_folder
    
    # Confirm before running
    print(f"\nThis will convert PNG/WebP images in:")
    print(f"  {folder}")
    print(f"\nExisting JPGs will NOT be modified.")
    print(f"Original files will be backed up to '{BACKUP_FOLDER}' subfolders.")
    
    response = input("\nContinue? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    process_folder(folder)

if __name__ == "__main__":
    main()
