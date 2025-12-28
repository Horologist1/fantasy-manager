#!/usr/bin/env python3
"""
Whoremaster Media Converter for Fantasy Manager
================================================
Converts GIF files to WebM videos for Ren'Py compatibility and optionally
renames files that need adjustment.

Fantasy Manager already understands most Whoremaster image names:
- "les", "gay" -> homo skill
- "beast" -> extreme skill  
- "strip" -> striptease skill
- "wait", "maid" -> service skill
- "titty" -> special skill

So this script focuses on:
1. Converting GIF animations to WebM videos (Ren'Py can't play GIFs)
2. Optional cleanup of edge cases

Usage:
    python rename_wm_images.py <source_folder> [--convert-gifs] [--dry-run]

Example:
    python rename_wm_images.py "../game/images/workers/aeris_gainsborough" --convert-gifs
    python rename_wm_images.py "../game/images/workers" --all --convert-gifs
"""

import os
import re
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# MINIMAL IMAGE MAPPINGS - Only truly necessary renames
# ============================================================================
# Fantasy Manager already handles most WM names case-insensitively:
# - "les", "gay" -> homo
# - "beast" -> extreme
# - "strip" -> striptease
# - "titty" -> special
# - "wait", "maid" -> service
#
# Only map things FM genuinely doesn't understand:

IMAGE_MAPPINGS = [
    # Portrait -> Profile (FM looks for "profile", not "portrait")
    (r'^Portrait', 'profile'),
    
    # =========================================================================
    # PREGNANT IMAGES - WM uses "Preg", FM uses "pregnant_"
    # =========================================================================
    # WM: PregSex.jpg, PregGroup.jpeg, Preg (2).jpg, PregNude.jpeg
    # FM: pregnant_sex.jpg, pregnant_group.jpg, pregnant (2).jpg, pregnant_strip.jpg
    
    # PregSex -> pregnant_sex (with skill combined)
    (r'^Preg(Sex|Anal|Oral|Group|BDSM|Hand|Strip|Special|Extreme|Combat|Service|Charm|Craft|Striptease|Homo|Les|Gay)\b', r'pregnant_\1'),
    # PregNude -> pregnant_strip (nude = strip in FM)
    (r'^PregNude\b', 'pregnant_strip'),
    # PregBeast -> pregnant_extreme
    (r'^PregBeast\b', 'pregnant_extreme'),
    # PregProfile -> pregnant_profile (explicit)
    (r'^PregProfile\b', 'pregnant_profile'),
    # Preg alone (profile/generic) -> pregnant_profile
    (r'^Preg\b', 'pregnant_profile'),
    # Preggo variants
    (r'^Preggo(Sex|Anal|Oral|Group|BDSM|Hand|Strip|Special|Extreme|Combat|Service|Charm|Craft|Striptease|Homo|Les|Gay)\b', r'pregnant_\1'),
    (r'^PreggoProfile\b', 'pregnant_profile'),
    (r'^Preggo\b', 'pregnant_profile'),
    
    # Foot -> hand (FM doesn't search for "foot", but "hand" works)
    (r'^Foot\b', 'hand'),
    (r'^Footjob\b', 'hand'),
    
    # Dildo/Mast -> special (these aren't in FM's patterns)
    (r'^Dildo\b', 'special'),
    (r'^Mast\b', 'special'),
    
    # Escort/Formal -> charm (FM doesn't search for these)
    (r'^Escort\b', 'charm'),
    (r'^Formal\b', 'charm'),
    
    # Swim/Bath -> rest
    (r'^Swim\b', 'rest'),
    (r'^Bath\b', 'rest'),
    
    # Nurse -> service
    (r'^Nurse\b', 'service'),
    
    # Ecchi/Presented/Nude -> strip (FM understands "strip")
    (r'^Ecchi\b', 'strip'),
    (r'^Presented\b', 'strip'),
    (r'^Nude\b', 'strip'),
    
    # Bunny/Dancer/Sing -> charm
    (r'^Bunny\b', 'charm'),
    (r'^Dancer\b', 'charm'),
    (r'^Sing\b', 'charm'),
    
    # Dom/Torture -> bdsm
    (r'^Dom\b', 'bdsm'),
    (r'^Torture\b', 'bdsm'),
    
    # Lick -> oral
    (r'^Lick\b', 'oral'),
    
    # Jail -> combat_failure
    (r'^Jail\b', 'combat_failure'),
    
    # Refuse -> charm_failure
    (r'^Refuse\b', 'charm_failure'),
    
    # Bed -> rest
    (r'^Bed\b', 'rest'),
    
    # Magic -> craft
    (r'^Magic\b', 'craft'),
    
    # Fight -> combat
    (r'^Fight\b', 'combat'),
    
    # Shop -> service
    (r'^Shop\b', 'service'),
    
    # Herd -> extreme (beast is already understood, but herd isn't)
    (r'^Herd\b', 'extreme'),
    
    # Creampie -> sex
    (r'^[Cc]reampie\b', 'sex'),
    
    # Milk -> service
    (r'^Milk\b', 'service'),
]

# File extensions to process
VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
VALID_VIDEO_EXTENSIONS = {'.webm', '.mp4', '.ogv'}
GIF_EXTENSION = '.gif'


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def convert_gif_to_webm(gif_path: Path, output_path: Path = None, 
                        dry_run: bool = False) -> Tuple[bool, str]:
    """
    Convert a GIF file to WebM video format.
    Returns (success, message).
    
    Uses ffmpeg with settings optimized for Ren'Py:
    - VP9 codec for good compression
    - Preserves transparency if present
    - Loops properly
    """
    if output_path is None:
        output_path = gif_path.with_suffix('.webm')
    
    if dry_run:
        return True, f"Would convert: {gif_path.name} -> {output_path.name}"
    
    try:
        # FFmpeg command for GIF to WebM with transparency support
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-i', str(gif_path),
            '-c:v', 'libvpx-vp9',  # VP9 codec
            '-pix_fmt', 'yuva420p',  # Support transparency
            '-auto-alt-ref', '0',  # Required for transparency
            '-crf', '30',  # Quality (lower = better, 30 is good balance)
            '-b:v', '0',  # Use CRF mode
            '-an',  # No audio
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and output_path.exists():
            # Optionally remove original GIF
            # gif_path.unlink()  # Uncomment to delete original
            return True, f"Converted: {gif_path.name} -> {output_path.name}"
        else:
            return False, f"FFmpeg error for {gif_path.name}: {result.stderr[:200]}"
    
    except subprocess.TimeoutExpired:
        return False, f"Timeout converting {gif_path.name}"
    except Exception as e:
        return False, f"Error converting {gif_path.name}: {str(e)}"


def get_new_filename(old_name: str) -> Tuple[str, bool]:
    """
    Get the new filename based on mappings.
    Returns (new_name, was_changed).
    
    Note: Fantasy Manager is case-insensitive and already understands
    most WM image names, so we only rename things FM doesn't recognize.
    """
    # Get base name and extension
    if '.' in old_name:
        name_without_ext, ext = old_name.rsplit('.', 1)
        ext = '.' + ext
    else:
        name_without_ext = old_name
        ext = ''
    
    # Try each mapping
    for pattern, replacement in IMAGE_MAPPINGS:
        if re.match(pattern, name_without_ext, re.IGNORECASE):
            # Apply replacement to the name part only
            new_name_part = re.sub(pattern, replacement, name_without_ext, 
                                   count=1, flags=re.IGNORECASE)
            new_name = new_name_part + ext
            return new_name, True
    
    # No mapping needed - FM already understands this name
    return old_name, False


def process_folder(folder_path: str, dry_run: bool = False, 
                   convert_gifs: bool = False) -> Dict[str, int]:
    """
    Process all media files in a folder.
    - Renames files that FM doesn't understand
    - Optionally converts GIFs to WebM videos
    
    Returns statistics dictionary.
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Error: Folder not found: {folder}")
        return {"error": 1}
    
    stats = {
        "processed": 0,
        "renamed": 0,
        "gifs_converted": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    # Check ffmpeg availability for GIF conversion
    has_ffmpeg = check_ffmpeg() if convert_gifs else False
    if convert_gifs and not has_ffmpeg:
        print("  Warning: ffmpeg not found. GIF conversion disabled.")
        print("  Install ffmpeg and add to PATH to enable GIF->WebM conversion.")
    
    renames = []
    gif_conversions = []
    
    # First pass: collect all operations
    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue
        
        ext = file_path.suffix.lower()
        
        # Handle GIF files
        if ext == GIF_EXTENSION:
            stats["processed"] += 1
            if convert_gifs and has_ffmpeg:
                gif_conversions.append(file_path)
            continue
        
        # Handle image/video files
        if ext not in VALID_IMAGE_EXTENSIONS and ext not in VALID_VIDEO_EXTENSIONS:
            continue
        
        stats["processed"] += 1
        old_name = file_path.name
        new_name, changed = get_new_filename(old_name)
        
        if changed and new_name != old_name:
            new_path = folder / new_name
            renames.append((file_path, new_path, old_name, new_name))
    
    # Handle conflicts for renames
    final_renames = []
    used_names = set()
    
    for old_path, new_path, old_name, new_name in renames:
        counter = 1
        base_new_name = new_name
        while new_name.lower() in used_names or (folder / new_name).exists():
            if '.' in new_name:
                base, ext = new_name.rsplit('.', 1)
            else:
                base, ext = new_name, ''
            # Remove existing counter if present
            base = re.sub(r'\s*\(\d+\)$', '', base)
            new_name = f"{base} ({counter}).{ext}" if ext else f"{base} ({counter})"
            counter += 1
        
        used_names.add(new_name.lower())
        final_renames.append((old_path, folder / new_name, old_name, new_name))
    
    # Perform renames
    for old_path, new_path, old_name, new_name in final_renames:
        if dry_run:
            print(f"  [RENAME] {old_name} -> {new_name}")
        else:
            try:
                shutil.move(str(old_path), str(new_path))
                print(f"  Renamed: {old_name} -> {new_name}")
                stats["renamed"] += 1
            except Exception as e:
                print(f"  Error renaming {old_name}: {e}")
                stats["errors"] += 1
    
    # Perform GIF conversions
    for gif_path in gif_conversions:
        success, message = convert_gif_to_webm(gif_path, dry_run=dry_run)
        if dry_run:
            print(f"  [GIF->WEBM] {message}")
            stats["gifs_converted"] += 1
        elif success:
            print(f"  {message}")
            stats["gifs_converted"] += 1
        else:
            print(f"  Error: {message}")
            stats["errors"] += 1
    
    stats["skipped"] = stats["processed"] - stats["renamed"] - stats["gifs_converted"] - stats["errors"]
    
    return stats


def process_all_folders(base_path: str, dry_run: bool = False, 
                        convert_gifs: bool = False):
    """Process all subfolders in the workers directory."""
    base = Path(base_path)
    if not base.exists():
        print(f"Error: Base path not found: {base}")
        return
    
    total_stats = {
        "processed": 0,
        "renamed": 0,
        "gifs_converted": 0,
        "skipped": 0,
        "errors": 0,
        "folders": 0,
    }
    
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
        
        # Skip special folders
        if folder.name.startswith('.') or folder.name == 'default':
            continue
        
        print(f"\nProcessing: {folder.name}")
        stats = process_folder(str(folder), dry_run, convert_gifs)
        
        if "error" not in stats:
            total_stats["processed"] += stats["processed"]
            total_stats["renamed"] += stats["renamed"]
            total_stats["gifs_converted"] += stats.get("gifs_converted", 0)
            total_stats["skipped"] += stats["skipped"]
            total_stats["errors"] += stats["errors"]
            total_stats["folders"] += 1
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Folders processed: {total_stats['folders']}")
    print(f"Files processed: {total_stats['processed']}")
    print(f"Files renamed: {total_stats['renamed']}")
    print(f"GIFs converted to WebM: {total_stats['gifs_converted']}")
    print(f"Files skipped: {total_stats['skipped']}")
    print(f"Errors: {total_stats['errors']}")
    
    if dry_run:
        print("\n*** DRY RUN - No files were actually modified ***")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Whoremaster media for Fantasy Manager compatibility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Fantasy Manager already understands most WM image names:
  - "les", "gay" -> homo skill
  - "beast" -> extreme skill
  - "strip" -> striptease skill
  - "titty" -> special skill
  - "wait", "maid" -> service skill

This script only renames files FM doesn't recognize,
and optionally converts GIFs to WebM videos.

Examples:
  # Preview changes (dry run)
  python rename_wm_images.py "../game/images/workers/aeris_gainsborough" --dry-run
  
  # Process single folder with GIF conversion
  python rename_wm_images.py "../game/images/workers/aeris_gainsborough" --convert-gifs
  
  # Process all worker folders
  python rename_wm_images.py "../game/images/workers" --all --convert-gifs
  
  # Dry run on all folders
  python rename_wm_images.py "../game/images/workers" --all --dry-run
"""
    )
    
    parser.add_argument('path', help='Path to folder or base workers directory')
    parser.add_argument('--dry-run', '-n', action='store_true', 
                        help='Show what would be done without actually doing it')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Process all subfolders in the given path')
    parser.add_argument('--convert-gifs', '-g', action='store_true',
                        help='Convert GIF files to WebM videos (requires ffmpeg)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("Fantasy Manager Media Converter")
    print("="*60)
    
    if args.dry_run:
        print("*** DRY RUN MODE - No files will be modified ***\n")
    
    if args.convert_gifs:
        if check_ffmpeg():
            print("FFmpeg found - GIF conversion enabled\n")
        else:
            print("Warning: FFmpeg not found in PATH")
            print("GIF conversion disabled. Install ffmpeg to enable.\n")
    
    if args.all:
        process_all_folders(args.path, args.dry_run, args.convert_gifs)
    else:
        stats = process_folder(args.path, args.dry_run, args.convert_gifs)
        if "error" not in stats:
            print(f"\nProcessed: {stats['processed']}, Renamed: {stats['renamed']}, "
                  f"GIFs converted: {stats.get('gifs_converted', 0)}, "
                  f"Skipped: {stats['skipped']}, Errors: {stats['errors']}")


if __name__ == '__main__':
    main()

