#!/usr/bin/env python3
"""
Script to normalize image resolutions to 1920x1080
- Resizes images larger than 1920x1080
- Resizes images smaller than 1920x1080
- Maintains aspect ratio
- Converts PNG without transparency to JPG (optional)
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageOps

# Target resolution
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT  # 16:9 = 1.777...

# PNG->JPG conversion settings
JPG_QUALITY = 85  # JPG quality
CONVERT_PNG_TO_JPG = True  # Converts PNG without transparency to JPG

# Folders to process
IMAGE_FOLDERS = [
    'game/images/workers'
]

# Image extensions to process
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}

# Files/folders to exclude
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.bak',
    '~',
    '.kra'  # Krita files
]


def get_file_size_mb(filepath):
    """Gets the size of a file in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)


def should_exclude(filepath):
    """Checks if a file should be excluded"""
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath_str:
            return True
    return False


def has_transparency(img):
    """Checks if an image has transparency"""
    if img.mode in ('RGBA', 'LA'):
        return True
    if img.mode == 'P':
        return 'transparency' in img.info
    return False


def resize_with_aspect_ratio(img, target_width, target_height, method='fit'):
    """
    Resizes an image maintaining aspect ratio
    
    Args:
        img: PIL Image
        target_width: Target width
        target_height: Target height
        method: 'fit' (fits inside), 'fill' (fills with padding), 'crop' (crops)
    
    Returns:
        Resized image
    """
    original_width, original_height = img.size
    original_ratio = original_width / original_height
    target_ratio = target_width / target_height
    
    if method == 'fit':
        # Fit image inside target area maintaining proportion
        if original_ratio > target_ratio:
            # Wider image - adjust by width
            new_width = target_width
            new_height = int(target_width / original_ratio)
        else:
            # Taller image - adjust by height
            new_height = target_height
            new_width = int(target_height * original_ratio)
        
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create image of target size with transparent or black background
        if img.mode == 'RGBA':
            # Maintain transparency
            result = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
            # Center the image
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            result.paste(resized, (x_offset, y_offset), resized if img.mode == 'RGBA' else None)
        else:
            # Black background for images without transparency
            result = Image.new('RGB', (target_width, target_height), (0, 0, 0))
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            result.paste(resized, (x_offset, y_offset))
        
        return result
    
    elif method == 'fill':
        # Fill with padding maintaining proportion
        return ImageOps.pad(img, (target_width, target_height), Image.Resampling.LANCZOS, color='black')
    
    elif method == 'crop':
        # Crop to fill exactly the area
        return ImageOps.fit(img, (target_width, target_height), Image.Resampling.LANCZOS)
    
    else:
        # Default, just resize by stretching (not recommended)
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)


def normalize_image(image_path, output_path=None, method='fit', dry_run=False, convert_png_to_jpg=True):
    """
    Normalizes an image to 1920x1080 and optionally converts PNG without transparency to JPG
    Returns: (original_size_mb, new_size_mb, original_resolution, new_resolution, changed, converted)
    """
    if output_path is None:
        output_path = image_path
    
    original_size = get_file_size_mb(image_path)
    changed = False
    converted = False
    
    try:
        # Open image
        img = Image.open(image_path)
        original_resolution = img.size
        original_mode = img.mode
        original_ext = image_path.suffix.lower()
        
        width, height = original_resolution
        
        # Check if normalization is needed
        needs_resize = (width != TARGET_WIDTH or height != TARGET_HEIGHT)
        
        # Check if it's PNG without transparency and can be converted to JPG
        should_convert_to_jpg = (convert_png_to_jpg and 
                                 original_ext == '.png' and 
                                 not has_transparency(img))
        
        if not needs_resize and not should_convert_to_jpg:
            # Already at correct resolution and format
            return original_size, original_size, original_resolution, original_resolution, False, False
        
        if dry_run:
            # In dry-run mode, only estimate
            estimated_new_size = original_size
            if should_convert_to_jpg:
                # JPG is usually smaller
                estimated_new_size = original_size * 0.6
            return original_size, estimated_new_size, original_resolution, (TARGET_WIDTH, TARGET_HEIGHT), True, should_convert_to_jpg
        
        # Resize maintaining aspect ratio (if needed)
        if needs_resize:
            resized_img = resize_with_aspect_ratio(img, TARGET_WIDTH, TARGET_HEIGHT, method=method)
        else:
            resized_img = img
        
        # Decide output format
        if should_convert_to_jpg:
            # Convert PNG without transparency to JPG
            if resized_img.mode != 'RGB':
                resized_img = resized_img.convert('RGB')
            
            jpg_path = image_path.with_suffix('.jpg')
            resized_img.save(jpg_path, 'JPEG', quality=JPG_QUALITY, optimize=True)
            
            jpg_size = get_file_size_mb(jpg_path)
            
            # Only replace if JPG is smaller
            if jpg_size < original_size:
                os.remove(image_path)
                output_path = jpg_path
                new_size = jpg_size
                converted = True
            else:
                # If JPG is larger, keep PNG
                os.remove(jpg_path)
                # Save as normalized PNG
                if needs_resize:
                    if resized_img.mode == 'RGBA':
                        resized_img = resized_img.convert('RGBA')
                    resized_img.save(output_path, 'PNG', optimize=True, compress_level=9)
                new_size = original_size
        else:
            # Save in original format
            ext = image_path.suffix.lower()
            if ext == '.png':
                # Maintain transparency if it had it
                if resized_img.mode == 'RGBA':
                    resized_img = resized_img.convert('RGBA')
                resized_img.save(output_path, 'PNG', optimize=True, compress_level=9)
            elif ext in ('.jpg', '.jpeg'):
                # Convert to RGB if it has transparency
                if resized_img.mode == 'RGBA':
                    # Create white background for transparency
                    background = Image.new('RGB', resized_img.size, (255, 255, 255))
                    background.paste(resized_img, mask=resized_img.split()[3])
                    resized_img = background
                elif resized_img.mode != 'RGB':
                    resized_img = resized_img.convert('RGB')
                resized_img.save(output_path, 'JPEG', quality=JPG_QUALITY, optimize=True)
            
            new_size = get_file_size_mb(output_path)
        
        new_resolution = resized_img.size
        changed = True
        
        return original_size, new_size, original_resolution, new_resolution, True, converted
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return original_size, original_size, (0, 0), (0, 0), False, False


def find_images(base_dir):
    """Finds all images in the specified folders"""
    images = []
    base_path = Path(base_dir)
    
    for folder in IMAGE_FOLDERS:
        folder_path = base_path / folder
        if not folder_path.exists():
            print(f"Warning: Folder {folder_path} does not exist")
            continue
        
        for ext in IMAGE_EXTENSIONS:
            for img_path in folder_path.rglob(f'*{ext}'):
                if not should_exclude(img_path):
                    images.append(img_path)
    
    return images


def main():
    parser = argparse.ArgumentParser(
        description='Normalizes image resolutions to 1920x1080',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Resizing methods:
  fit   - Fits inside 1920x1080 maintaining proportion (with padding)
  fill  - Fills with padding maintaining proportion
  crop  - Crops to fill exactly 1920x1080

The script also converts PNG without transparency to JPG to reduce size.

Examples:
  python normalize_resolutions.py                    # Normalizes and converts PNG->JPG
  python normalize_resolutions.py --method crop      # Uses 'crop' method
  python normalize_resolutions.py --no-convert      # Does not convert PNG to JPG
  python normalize_resolutions.py --dry-run          # Only shows statistics
        """
    )
    parser.add_argument('--method', choices=['fit', 'fill', 'crop'], default='fit',
                        help='Resizing method (default: fit)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Only shows statistics without modifying files')
    parser.add_argument('--no-convert', action='store_true',
                        help='Does not convert PNG without transparency to JPG')
    
    args = parser.parse_args()
    
    # Get base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    print("=" * 60)
    print("Resolution Normalizer - Workers")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  - Target resolution: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    print(f"  - Method: {args.method}")
    print(f"  - Convert PNG->JPG: {'No' if args.no_convert else 'Yes (without transparency)'}")
    print(f"  - JPG quality: {JPG_QUALITY}")
    print(f"  - Folders: {', '.join(IMAGE_FOLDERS)}")
    if args.dry_run:
        print(f"  - Mode: DRY RUN (simulation only)")
    print()
    
    # Find all images
    print("Searching for images...")
    images = find_images(base_dir)
    
    if not images:
        print("No images found to process.")
        return
    
    print(f"Found {len(images)} images to process.\n")
    
    # Statistics
    total_original = 0
    total_new = 0
    processed = 0
    changed = 0
    converted = 0
    errors = 0
    resolution_stats = {}
    needs_resize = []
    
    # Analyze first (for statistics)
    print("Analyzing resolutions...")
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
    
    print(f"\nImages that need resizing: {len(needs_resize)}")
    print(f"Images already at {TARGET_WIDTH}x{TARGET_HEIGHT}: {len(images) - len(needs_resize)}")
    print()
    
    # Process each image
    for i, img_path in enumerate(images, 1):
        rel_path = img_path.relative_to(base_dir)
        print(f"[{i}/{len(images)}] Processing: {rel_path}")
        
        original_size = get_file_size_mb(img_path)
        total_original += original_size
        
        orig, new, orig_res, new_res, changed_flag, was_converted = normalize_image(
            img_path,
            method=args.method,
            dry_run=args.dry_run,
            convert_png_to_jpg=not args.no_convert
        )
        
        total_new += new
        processed += 1
        
        if was_converted:
            converted += 1
        
        if changed_flag:
            changed += 1
            if args.dry_run:
                convert_msg = " [PNG->JPG]" if was_converted else ""
                print(f"  [DRY RUN] {orig_res[0]}x{orig_res[1]} -> {TARGET_WIDTH}x{TARGET_HEIGHT}{convert_msg} | {orig:.2f} MB")
            else:
                convert_msg = " [PNG->JPG]" if was_converted else ""
                reduction = ((orig - new) / orig * 100) if orig > 0 else 0
                print(f"  [OK] {orig_res[0]}x{orig_res[1]} -> {new_res[0]}x{new_res[1]}{convert_msg} | {orig:.2f} MB -> {new:.2f} MB ({reduction:.1f}% reduction)")
        else:
            print(f"  [OK] {orig_res[0]}x{orig_res[1]} (already normalized) | {orig:.2f} MB")
    
    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Images processed: {processed}")
    print(f"Images modified: {changed}")
    print(f"Images already normalized: {processed - changed}")
    if converted > 0:
        print(f"Images converted PNG->JPG: {converted}")
    if errors > 0:
        print(f"Errors: {errors}")
    print(f"Total original size: {total_original:.2f} MB ({total_original/1024:.2f} GB)")
    print(f"Total new size: {total_new:.2f} MB ({total_new/1024:.2f} GB)")
    
    # Show resolution statistics
    if resolution_stats:
        print("\nResolutions found:")
        print("-" * 60)
        for res, count in sorted(resolution_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            marker = " [OK]" if res == f"{TARGET_WIDTH}x{TARGET_HEIGHT}" else " [NEEDS RESIZE]"
            print(f"  {res}: {count} images{marker}")
        if len(resolution_stats) > 10:
            print(f"  ... and {len(resolution_stats) - 10} more resolutions")
    
    if args.dry_run:
        print("\n⚠ This was a DRY RUN. No files were modified.")
        print("Run without --dry-run to normalize the images.")
    
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)











