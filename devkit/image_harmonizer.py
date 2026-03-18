#!/usr/bin/env python3
"""
Image Harmonizer for Fantasy Manager
=====================================
Converts images to JPG with:
- Resolution: normalized to 1920x1080 (scales up smaller, scales down larger; maintains aspect ratio)
- Quality: 70%
- By default skips existing JPGs (use --include-jpg to recompress heavy ones)

Usage:
    python image_harmonizer.py [folder_path] [--include-jpg] [--jpg-max-kb=NNN]

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
SKIP_EXTENSIONS = {'.jpg', '.jpeg'}  # Skipped unless --include-jpg is used
CONVERT_EXTENSIONS = {'.png', '.webp', '.bmp', '.tiff'}
BACKUP_FOLDER = "_originals_backup"
DRY_RUN = False  # Set to True to preview without making changes
DEFAULT_JPG_MAX_KB = 350  # Recompress JPG only if larger than this

def get_target_size(original_width, original_height):
    """Calculate target size maintaining aspect ratio, normalizing to 1920x1080.
    Scales down images larger than target; scales up images smaller than target."""
    # Calculate scaling factor (works for both scale-up and scale-down)
    width_ratio = TARGET_WIDTH / original_width
    height_ratio = TARGET_HEIGHT / original_height
    ratio = min(width_ratio, height_ratio)  # Ensures result fits within 1920x1080
    
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    
    return new_width, new_height

def should_convert(filepath, include_jpg=False, jpg_max_kb=DEFAULT_JPG_MAX_KB):
    """Check if file should be converted"""
    ext = filepath.suffix.lower()

    # Skip JPGs unless explicitly requested
    if ext in SKIP_EXTENSIONS:
        if include_jpg:
            try:
                size_kb = filepath.stat().st_size / 1024.0
            except Exception:
                size_kb = 0
            if size_kb > float(jpg_max_kb):
                return True, f"Will recompress JPG ({size_kb:.0f}KB > {jpg_max_kb}KB)"
            return False, f"JPG under threshold ({size_kb:.0f}KB <= {jpg_max_kb}KB)"
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

def process_folder(folder_path, create_backup=True, include_jpg=False, jpg_max_kb=DEFAULT_JPG_MAX_KB):
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
        should, reason = should_convert(filepath, include_jpg=include_jpg, jpg_max_kb=jpg_max_kb)
        
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
    if include_jpg:
        print("JPGs skipped: 0 (include-jpg enabled)")
    else:
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
    
    include_jpg = "--include-jpg" in sys.argv
    jpg_max_kb = DEFAULT_JPG_MAX_KB
    args = []
    for a in sys.argv[1:]:
        if a == "--include-jpg":
            continue
        if a.startswith("--jpg-max-kb="):
            try:
                jpg_max_kb = int(a.split("=", 1)[1])
            except Exception:
                print(f"WARNING: Invalid --jpg-max-kb value '{a}', using default {DEFAULT_JPG_MAX_KB}")
                jpg_max_kb = DEFAULT_JPG_MAX_KB
            continue
        args.append(a)

    # Get folder from args or use default
    if args:
        folder = Path(args[0])
    else:
        folder = default_folder

    # Confirm before running
    print(f"\nThis will harmonize images in:")
    print(f"  {folder}")
    if include_jpg:
        print(f"\nJPG files larger than {jpg_max_kb}KB WILL be recompressed/normalized.")
    else:
        print("\nExisting JPGs will NOT be modified.")
    print(f"Original files will be backed up to '{BACKUP_FOLDER}' subfolders.")
    
    response = input("\nContinue? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    process_folder(folder, include_jpg=include_jpg, jpg_max_kb=jpg_max_kb)

if __name__ == "__main__":
    main()
