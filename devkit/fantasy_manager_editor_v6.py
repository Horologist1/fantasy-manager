#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fantasy Manager Editor v6.0
================================================================================
Based on v5.3, enhanced with:
- Event Probability field (1-100%) - absolute probability, not affected by managers
- Updated Limited field logic (limited: false = NOT affected by managers)
- COMPLETE Daily Stories Editor with:
  * Basic fields (ID, Report, Weight, Difficulty, Images)
  * Traits section (relevant_traits, trait_bonus, trait_success)
  * Earnings formulas
  * Descriptions for all outcomes (failure, mediocre, success, critical_success)
  * Consequences per outcome (energy, health, joy, rebelliousness, etc.)
  * Loot system (rolls + bonus_items with chance, NSFW, critical_only flags)
- COMPLETE Event Choice Editor with:
  * Skill check condition
  * Threshold (minimum skill level requirement)
  * Required trait (worker must have this trait)
  * Add trait on success effect
  * servant_health, servant_energy, servant_joy, rebelliousness effects
- All previous v5.1 features
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import random
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any

try:
    from validate_event_mechanics import validate_events_list as _validate_events_list
except ImportError:
    _validate_events_list = None

VERSION = "6.0"

# Templates embebidos (no dependen de archivos externos)
EMBEDDED_EVENT_TEMPLATE = {
    "id": None, "description": None, "weight": 0, "limited": False, "max_occurrences": 0,
    "cooldown_days": 0, "event_probability": 0, "guaranteed": False, "worker_selection": None,
    "worker_gender_requirement": None, "player_gender_requirement": None, "requires_assigned_worker": False,
    "required_building_worker_traits": [], "required_active_professions": [], "forbidden_active_professions": [],
    "required_building_worker_min_skill": None, "required_building_worker_skill": None, "building_type": [],
    "background_image": None, "success_image": None, "failure_image": None, "nsfw": False,
    "required_flags": {}, "excluded_flags": {},
    "conditions": {"start_when": None, "stop_when": None},
    "start_when": None, "stop_when": None,
    "choices": [{
        "option": None, "condition": None, "threshold": 0, "required_trait": None,
        "required_traits": [], "excluded_traits": [], "trait_visibility": "hide", "blocked_message": None,
        "restrict_worker_effects_to_filter": False,
        "effect_worker_filter": {
            "required_active_professions": [], "forbidden_active_professions": [],
            "required_traits": [], "excluded_traits": [],
            "min_skill": None, "required_building_worker_min_skill": None,
            "skill_name": None, "required_building_worker_skill": None, "required_trait": None,
        },
        "message_failure_worker_effect_skipped": None,
        "message": None, "message_success": None, "message_failure": None,
        "conditions": {"start_when": None, "stop_when": None},
        "required_flags": {}, "excluded_flags": {},
        "effect": {
            "money": 0, "reputation": 0, "custom": None, "event_flags": {}, "item_id": None,
            "loot_rolls": 0, "worker_name": None, "random_worker": False, "skill_modifiers": {},
            "add_trait": {"name": None, "duration": 0, "target": None},
            "success": {"money": 0, "reputation": 0, "custom": None, "event_flags": {}, "skill_modifiers": {}, "add_trait": {"name": None, "duration": 0, "target": None}},
            "failure": {"money": 0, "reputation": 0, "custom": None, "event_flags": {}, "skill_modifiers": {}, "add_trait": {"name": None, "duration": 0, "target": None}}
        }
    }]
}

EMBEDDED_DAILY_STORY_TEMPLATE = {
    "id": None, "weight": 0, "report": None, "description": None, "difficulty_modifier": 0,
    "worker_gender_requirement": None, "nsfw_only": False, "skill_options": [], "trait_roll_modifiers": {},
    "trait_msg_success_both": None, "trait_msg_success_pos": None, "trait_msg_success_neg": None,
    "trait_msg_failure_both": None, "trait_msg_failure_neg": None, "trait_msg_failure_pos": None,
    "required_traits": [], "excluded_traits": [], "stat_requirements": {},
    "descriptions": {"failure": None, "mediocre": None, "success": None, "critical_success": None},
    "earnings": {"failure": "0", "mediocre": "0", "success": "0", "critical_success": "0"},
    "consequences": {
        "failure": {"energy": 0, "health": 0, "joy": 0, "rebelliousness": 0, "romance": 0, "relationship": 0, "reputation": 0, "libido": 0, "obedience": 0, "add_trait": None, "give_item": None},
        "mediocre": {"energy": 0, "health": 0, "joy": 0, "rebelliousness": 0, "romance": 0, "relationship": 0, "reputation": 0, "libido": 0, "obedience": 0, "add_trait": None, "give_item": None},
        "success": {"energy": 0, "health": 0, "joy": 0, "rebelliousness": 0, "romance": 0, "relationship": 0, "reputation": 0, "libido": 0, "obedience": 0, "add_trait": None, "give_item": None},
        "critical_success": {"energy": 0, "health": 0, "joy": 0, "rebelliousness": 0, "romance": 0, "relationship": 0, "reputation": 0, "libido": 0, "obedience": 0, "add_trait": None, "give_item": None}
    },
    "story_image": None, "failure_image": None,
    "loot": {"rolls": 0, "bonus_items": [], "monster_worker": {"chance": 0, "filters": {}}, "captured_worker": {"chance": 0, "filters": {}}}
}

EMBEDDED_WORKER_TEMPLATE = {
    "name": None, "folder": None, "cost": 0, "nsfw": False, "unique": False, "encounter_only": False,
    "monster": False, "procedural": False,
    "skills": {"Sex": 25, "Anal": 25, "BDSM": 25, "Hand": 25, "Oral": 25, "Homo": 25, "Special": 25,
               "Group": 25, "Extreme": 25, "Striptease": 25, "Combat": 25, "Clever": 25, "Charm": 25,
               "Service": 25, "Agility": 25, "Craft": 25,
               "Specialty 4": 25, "Specialty 5": 25, "Specialty 6": 25, "Specialty 7": 25,
               "Specialty 8": 25, "Specialty 9": 25, "Specialty 10": 25, "Specialty 11": 25, "Specialty 12": 25},
    "names_list": None, "traits": [], "description": None, "gender": None, "comfort_desired": 1
}

EMBEDDED_ITEM_TEMPLATE = {
    "id": None, "name": None, "display_name": None, "type": None,
    "effect": {"custom": None, "skill_modifiers": {}, "attribute_modifiers": {}, "daily_effects": {}},
    "description": None, "durability": 0, "price": 0, "weight": 0, "nsfw": False
}

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Image preview disabled. Install with: pip install Pillow")

# =============================================================================
# WHOREMASTER MAPPINGS
# =============================================================================

# Skill value conversion: Whoremaster scale → Fantasy Manager (0-100)
# WM packs use 0-100 for skills; if your pack uses 0-70, set WM_SKILL_SCALE_MAX = 70
WM_SKILL_SCALE_MAX = 100
FM_SKILL_MAX = 100

def convert_wm_skill_value_to_fm(wm_raw: int, wm_scale_max: int = None) -> int:
    """Convert a Whoremaster skill value to Fantasy Manager scale (0-100)."""
    if wm_scale_max is None:
        wm_scale_max = WM_SKILL_SCALE_MAX
    if wm_scale_max <= 0:
        return min(FM_SKILL_MAX, max(0, int(wm_raw)))
    fm_val = int(round(wm_raw * FM_SKILL_MAX / wm_scale_max))
    return min(FM_SKILL_MAX, max(0, fm_val))

# Map Whoremaster skill names to Fantasy Manager canonical skill names (game expects capitalized)
WM_SKILL_MAPPING = {
    "NormalSex": "Sex", "OralSex": "Oral", "Lesbian": "Homo", "Handjob": "Hand",
    "TittySex": "Special", "Footjob": "Special", "Beastiality": "Extreme",
    "Strip": "Striptease", "Magic": "Craft", "Medicine": "Clever",
    "Performance": "Charm", "Crafting": "Craft", "Farming": "Service",
    "Cooking": "Service", "Herbalism": "Craft", "Brewing": "Clever", "AnimalHandling": "Craft",
    "Card": "Clever", "Sport": "Agility",
    "Anal": "Anal", "BDSM": "BDSM", "Group": "Group", "Service": "Service", "Combat": "Combat",
}

WM_TRAIT_MAPPING = {
    "Nymphomaniac": "Nymph-Touched", "Chaste": "Frigid Soul", "Frigid": "Frigid Soul",
    "High Sex Drive": "Burning Desire", "Slut": "Insatiable", "Big Boobs": "Large Breasts",
    "Busty Boobs": "Large Breasts", "Small Boobs": "Small Breasts", "Flat Chest": "Flat Chest",
    "Great Arse": "Firm Ass", "Plump Tush": "Soft Ass", "Not Human": "Transformed",
    "Cat Girl": "Transformed", "Cow Girl": "Transformed", "Iron Will": "Rebellious",
    "Broken Will": "Obedient", "Fearless": "Confident", "Deep Throat": "Pierced",
    "Fast Orgasms": "Sensitive", "Slow Orgasms": "Numb", "Cute": "Cute", "Beautiful": "Beautiful",
    "Charming": "Charming", "Charismatic": "Charismatic", "Elegant": "Elegant", "Agile": "Agile",
    "Strong": "Strong", "Tough": "Tough", "Clumsy": "Clumsy", "Adventurer": "Adventurer",
    "Maid": "Maid", "Singer": "Singer", "Teacher": "Teacher", "Waitress": "Waitress",
    "Elf": "Elf", "Dwarf": "Dwarf", "Demon": "Demon", "Angel": "Angel",
    "Vampire": "Vampire", "Orc": "Orc", "Goblin": "Goblin",
    "Quick Learner": "Quick Learner", "Dependant": "Dependant", "Optimist": "Optimist",
    "Open Minded": "Open Minded", "Cool Scars": "Cool Scars", "Nervous": "Nervous",
    "Sadistic": "Sadistic", "Exotic": "Exotic", "Flexible": "Flexible", "Brawler": "Brawler",
    "Tomboy": "Tomboy", "Tattooed": "Tattooed", "Pessimist": "Pessimist",
    "Cool Person": "Charming",
    "Small Scars": "Cool Scars",
    "Heavily Tattooed": "Tattooed",
    "Horrific Scars": "Scarred",
    "Retarded": "Dumb",
    "Mind Fucked": "Crazy",
}

# Female names pool for procedural workers (.rgirlsx)
FEMALE_NAMES = [
    "Elizabeth", "Victoria", "Charlotte", "Emma", "Isabella",
    "Sophia", "Amelia", "Margaret", "Catherine", "Eleanor",
    "Beatrice", "Clara", "Florence", "Grace", "Helena",
    "Alice", "Mary", "Anne", "Jane", "Caroline",
    "Lucy", "Sarah", "Rebecca", "Julia", "Laura",
    "Diana", "Rose", "Lily", "Agnes", "Martha",
    "Edith", "Frances", "Louise", "Marie", "Ethel",
    "Ada", "Mabel", "Pearl", "Ruby", "Violet",
    "Elsie", "Maud", "Gertrude", "Bertha", "Jessie",
    "Harriet", "Constance", "Evelyn", "Dorothy", "Gladys",
    "Irene", "Stella", "Blanche", "Olive", "Mildred",
    "Hazel", "Edna", "Lillian", "Ruth", "Helen",
    "Esther", "Anna", "Eva", "Nora", "Ida",
    "Cora", "Nell", "Dora", "May", "Minnie",
    "Flora", "Daisy", "Hilda", "Vera", "Bessie",
    "Aaliyah", "Abbey", "Abigail", "Adeline", "Adriana",
    "Agatha", "Aileen", "Aimee", "Alexandra", "Alexis",
    "Amanda", "Amber", "Amy", "Andrea", "Angela",
    "Anita", "Annabelle", "Ariana", "Ashley", "Audrey",
    "Barbara", "Belinda", "Beth", "Betty", "Beverly",
    "Bianca", "Bonnie", "Brenda", "Brittany", "Brooke",
    "Camilla", "Candace", "Carmen", "Carol", "Cassandra",
    "Cecilia", "Cheryl", "Christina", "Christine", "Claire",
    "Claudia", "Colleen", "Cynthia", "Danielle", "Dawn",
    "Deborah", "Denise", "Diane", "Donna", "Doris",
    "Elena", "Eliza", "Ellen", "Emily", "Erica",
    "Erin", "Estelle", "Faith", "Felicia", "Fiona",
    "Francine", "Gabrielle", "Gail", "Gemma", "Georgia",
    "Gina", "Gloria", "Haley", "Hannah", "Heather",
    "Heidi", "Holly", "Hope", "Ingrid", "Isabel",
    "Ivy", "Jacqueline", "Jamie", "Janet", "Jasmine",
    "Jean", "Jennifer", "Jessica", "Jill", "Joan",
    "Joanna", "Joyce", "Judith", "Julie", "Karen",
    "Katherine", "Kathleen", "Kelly", "Kimberly", "Kristen",
    "Lauren", "Leah", "Leslie", "Linda", "Lisa",
    "Lois", "Lorraine", "Lynn", "Madison", "Maria",
    "Marilyn", "Marina", "Maureen", "Megan", "Melanie",
    "Melissa", "Michelle", "Monica", "Nancy", "Natalie",
    "Nicole", "Norma", "Olivia", "Pamela", "Patricia",
    "Paula", "Penelope", "Rachel", "Rita", "Roberta",
    "Rosa", "Samantha", "Sandra", "Sara", "Shannon",
    "Sharon", "Sheila", "Shirley", "Stephanie", "Susan",
    "Sylvia", "Tamara", "Teresa", "Theresa", "Tiffany",
    "Tracy", "Valerie", "Vanessa", "Veronica", "Virginia",
    "Vivian", "Wendy"
]

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def check_ffmpeg() -> bool:
    """Check if ffmpeg is available in PATH."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5,
                              creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def install_ffmpeg_auto() -> Tuple[bool, str]:
    """Try to install FFmpeg automatically using available package managers."""
    if sys.platform != 'win32':
        return False, "Auto-install only available on Windows"
    
    # Try winget (Windows 10/11)
    try:
        result = subprocess.run(['winget', '--version'], 
                              capture_output=True, text=True, timeout=5,
                              creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        if result.returncode == 0:
            # Try to install with winget (without silent to see progress)
            try:
                install_result = subprocess.run(
                    ['winget', 'install', '--id', 'Gyan.FFmpeg', '--accept-package-agreements', '--accept-source-agreements'],
                    capture_output=True, text=True, timeout=300,  # 5 minutes timeout
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                if install_result.returncode == 0:
                    # Wait a moment for PATH to update
                    import time
                    time.sleep(2)
                    # Check if it's now available
                    if check_ffmpeg():
                        return True, "FFmpeg installed successfully via winget!"
                    else:
                        return False, "FFmpeg installed but not in PATH. Please restart the editor or add FFmpeg to PATH manually."
                else:
                    error_msg = install_result.stderr[:300] if install_result.stderr else install_result.stdout[:300]
                    # Check for VPN/network errors
                    if 'vpn' in error_msg.lower() or 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                        return False, "Network connection error. Please check your internet connection or try manual installation from https://www.gyan.dev/ffmpeg/builds/"
                    return False, f"winget install failed. Error: {error_msg}"
            except subprocess.TimeoutExpired:
                return False, "Installation timed out. This might be a network issue. Please try manual installation from https://www.gyan.dev/ffmpeg/builds/"
            except Exception as e:
                error_str = str(e).lower()
                if 'vpn' in error_str or 'network' in error_str or 'connection' in error_str:
                    return False, "Network connection error. Please check your internet connection or try manual installation from https://www.gyan.dev/ffmpeg/builds/"
                return False, f"Installation error: {str(e)}. Please try manual installation."
    except subprocess.TimeoutExpired:
        return False, "Connection timed out. Please try manual installation from https://www.gyan.dev/ffmpeg/builds/"
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        pass
    
    # Try chocolatey
    try:
        result = subprocess.run(['choco', '--version'], 
                              capture_output=True, text=True, timeout=5,
                              creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        if result.returncode == 0:
            try:
                install_result = subprocess.run(
                    ['choco', 'install', 'ffmpeg', '-y'],
                    capture_output=True, text=True, timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                if install_result.returncode == 0:
                    import time
                    time.sleep(2)
                    if check_ffmpeg():
                        return True, "FFmpeg installed successfully via Chocolatey!"
                    else:
                        return False, "FFmpeg installed but not in PATH. Please restart the editor."
                else:
                    error_msg = install_result.stderr[:300] if install_result.stderr else install_result.stdout[:300]
                    if 'vpn' in error_msg.lower() or 'network' in error_msg.lower() or 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                        return False, "Network connection error. Please check your internet connection or try manual installation from https://www.gyan.dev/ffmpeg/builds/"
                    return False, f"Chocolatey install failed. Error: {error_msg}"
            except subprocess.TimeoutExpired:
                return False, "Installation timed out. This might be a network issue. Please try manual installation from https://www.gyan.dev/ffmpeg/builds/"
            except Exception as e:
                error_str = str(e).lower()
                if 'vpn' in error_str or 'network' in error_str or 'connection' in error_str:
                    return False, "Network connection error. Please check your internet connection or try manual installation from https://www.gyan.dev/ffmpeg/builds/"
                return False, f"Installation error: {str(e)}. Please try manual installation."
            else:
                error_msg = install_result.stderr[:300] if install_result.stderr else install_result.stdout[:300]
                return False, f"choco install failed. Error: {error_msg}"
    except subprocess.TimeoutExpired:
        return False, "Installation timed out. Please try manual installation."
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    return False, "No package manager found (winget/choco). Please install manually."

def get_ffmpeg_install_instructions() -> str:
    """Get user-friendly FFmpeg installation instructions."""
    if sys.platform == 'win32':
        return """FFMPEG INSTALLATION - Windows

Option 1: Automatic installation (recommended)
1. Open PowerShell as Administrator
2. Run: winget install --id Gyan.FFmpeg
3. Restart this editor

Option 2: Manual installation
1. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/
2. Download "ffmpeg-release-essentials.zip"
3. Extract the ZIP (e.g., to C:\\ffmpeg)
4. Add C:\\ffmpeg\\bin to your system PATH:
   - Control Panel → System → Advanced system settings
   - Environment Variables → Path → Edit → New
   - Add: C:\\ffmpeg\\bin
5. Restart this editor

Option 3: Chocolatey (if you have it)
   choco install ffmpeg -y

After installing, restart the editor for FFmpeg to be detected."""
    else:
        return """FFMPEG INSTALLATION

Linux: sudo apt install ffmpeg  (or equivalent for your distro)
macOS: brew install ffmpeg  (requires Homebrew)

Restart the editor after installing."""

def convert_gif_to_webm(gif_path: Path, output_path: Path = None) -> Tuple[bool, str]:
    """Convert a GIF to WebM format."""
    if output_path is None:
        output_path = gif_path.with_suffix('.webm')
    
    try:
        cmd = ['ffmpeg', '-y', '-i', str(gif_path), '-c:v', 'libvpx-vp9',
               '-pix_fmt', 'yuva420p', '-auto-alt-ref', '0', '-crf', '30',
               '-b:v', '0', '-an', str(output_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                               creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        
        if result.returncode == 0 and output_path.exists():
            return True, f"Converted: {gif_path.name} → {output_path.name}"
        else:
            return False, f"FFmpeg error: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout converting {gif_path.name}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def sanitize_folder_name(name: str) -> str:
    """Convert a name to a valid folder name."""
    sanitized = re.sub(r'[^\w\s-]', '', name.lower())
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized

# =============================================================================
# IMAGE RENAMING - Whoremaster to Fantasy Manager compatibility
# =============================================================================

# Patterns for renaming images (regex pattern, replacement)
WM_IMAGE_RENAME_PATTERNS = [
    # Portrait -> profile
    (r'^Portrait', 'profile'),
    
    # PREGNANT IMAGES - WM uses "Preg", FM uses "pregnant_"
    # PregSex -> pregnant_sex (with skill combined - case insensitive)
    (r'^Preg(Sex|Anal|Oral|Group|BDSM|Hand|Strip|Special|Extreme|Combat|Service|Charm|Craft|Striptease|Homo)', r'pregnant_\1'),
    (r'^Preg(Les|Gay)', r'pregnant_\1'),
    # PregNude -> pregnant_strip (nude = strip in FM)
    (r'^PregNude', 'pregnant_strip'),
    # PregBeast -> pregnant_extreme
    (r'^PregBeast', 'pregnant_extreme'),
    # PregProfile -> pregnant_profile
    (r'^PregProfile', 'pregnant_profile'),
    # Preg alone (profile/generic) -> pregnant_profile
    (r'^Preg\b', 'pregnant_profile'),
    # Preggo variants
    (r'^Preggo(Sex|Anal|Oral|Group|BDSM|Hand|Strip|Special|Extreme|Combat|Service|Charm|Craft|Striptease|Homo)', r'pregnant_\1'),
    (r'^Preggo(Les|Gay)', r'pregnant_\1'),
    (r'^PreggoProfile', 'pregnant_profile'),
    (r'^Preggo\b', 'pregnant_profile'),
    
    # Foot -> hand (FM doesn't search for "foot")
    (r'^Foot\b', 'hand'),
    (r'^Footjob\b', 'hand'),
    
    # Dildo/Mast -> special
    (r'^Dildo\b', 'special'),
    (r'^Mast\b', 'special'),
    
    # Escort/Formal -> charm
    (r'^Escort\b', 'charm'),
    (r'^Formal\b', 'charm'),
    
    # Swim/Bath -> rest
    (r'^Swim\b', 'rest'),
    (r'^Bath\b', 'rest'),
    
    # Nurse -> service
    (r'^Nurse\b', 'service'),
    
    # Ecchi/Presented/Nude -> strip
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
    
    # Death -> combat_failure
    (r'^Death\b', 'combat_failure'),
    
    # Cook -> service
    (r'^Cook\b', 'service'),
    
    (r'^Blacksmith\b', 'craft'),
    (r'^Card\b', 'charm'),
    (r'^Dance\b', 'charm'),
    (r'^Doctor\b', 'service'),
    (r'^Farm\b', 'service'),
    (r'^Eatout\b', 'oral'),
    (r'^Deepthroat\b', 'oral'),
    (r'^Futa\b', 'futa_sex'),
    (r'^Sub\b', 'bdsm'),
    (r'^Study\b', 'clever'),
    (r'^Work1\b', 'service'),
    (r'^Maid3\b', 'service'),
    (r'^Matron3\b', 'service'),
]

def rename_wm_images_in_folder(folder: Path) -> int:
    """
    Rename images in a folder from WM naming to FM naming conventions.
    Returns the number of files renamed.
    """
    renamed_count = 0
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.webm', '.mp4'}
    
    for file in folder.iterdir():
        if not file.is_file():
            continue
        if file.suffix.lower() not in valid_extensions:
            continue
            
        original_name = file.stem
        new_name = original_name
        
        # Apply renaming patterns
        for pattern, replacement in WM_IMAGE_RENAME_PATTERNS:
            new_name = re.sub(pattern, replacement, new_name, flags=re.IGNORECASE)
        
        # Lowercase the result for consistency
        new_name_lower = new_name.lower()
        
        # Clean up problematic number patterns:
        # Remove numbers in parentheses: "bdsm (2)" -> "bdsm"
        new_name_lower = re.sub(r'\s*\(\d+\)\s*', '', new_name_lower)
        # Remove trailing underscores with numbers: "bdsm_2" -> "bdsm"
        new_name_lower = re.sub(r'_+\d+$', '', new_name_lower)
        # Remove multiple consecutive underscores or spaces
        new_name_lower = re.sub(r'[_\s]+', '_', new_name_lower)
        # Remove leading/trailing underscores
        new_name_lower = new_name_lower.strip('_')
        
        if new_name_lower != original_name.lower() or file.suffix != file.suffix.lower():
            new_filename = new_name_lower + file.suffix.lower()
            new_path = file.parent / new_filename
            
            # Avoid overwriting existing files
            if new_path.exists() and new_path != file:
                # Add counter to avoid collision using (1), (2), etc.
                counter = 1
                while new_path.exists():
                    new_filename = f"{new_name_lower} ({counter}){file.suffix.lower()}"
                    new_path = file.parent / new_filename
                    counter += 1
            
            try:
                file.rename(new_path)
                renamed_count += 1
                print(f"Renamed: {file.name} -> {new_path.name}")
            except Exception as e:
                print(f"Error renaming {file.name}: {e}")
    
    return renamed_count

def parse_wm_girl_xml(xml_path: Path) -> Optional[Dict]:
    """Parse a Whoremaster .girlsx or .rgirlsx file."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        girl = root.find('Girl')
        if girl is None:
            return None
        
        is_random = xml_path.suffix.lower() == '.rgirlsx'
        # Get name from XML (prefer FirstName, then Name)
        xml_firstname = girl.get('FirstName', '')
        xml_name = girl.get('Name', 'Unknown')
        
        # Use FirstName if available, otherwise full Name
        base_name = xml_firstname if xml_firstname else xml_name
        
        # If name is too long (more than 15 chars), use only first name (before first space)
        MAX_NAME_LENGTH = 15
        if len(base_name) > MAX_NAME_LENGTH:
            # Split by space and take first part
            first_space_idx = base_name.find(' ')
            if first_space_idx > 0:
                preferred_name = base_name[:first_space_idx]
            else:
                preferred_name = base_name  # No space found, use as is
        else:
            preferred_name = base_name
        
        data = {
            'name': preferred_name,
            'xml_name': xml_name,  # Keep XML name for reference (for image folder lookup)
            'description': girl.get('Desc', ''),
            'is_random': is_random,
            'stats': {}, 'skills': {}, 'traits': []
        }
        
        if is_random:
            for stat in girl.findall('Stat'):
                name = stat.get('Name')
                data['stats'][name] = {'min': int(stat.get('Min', 0)), 'max': int(stat.get('Max', 100))}
            for skill in girl.findall('Skill'):
                name = skill.get('Name')
                data['skills'][name] = {'min': int(skill.get('Min', 0)), 'max': int(skill.get('Max', 100))}
            for trait in girl.findall('Trait'):
                data['traits'].append({'name': trait.get('Name'), 'percent': int(trait.get('Percent', 100))})
        else:
            for attr in ['Charisma', 'Intelligence', 'Agility', 'Strength', 'Constitution', 
                        'Beauty', 'Confidence', 'Obedience', 'Spirit', 'Libido', 'Mana']:
                val = girl.get(attr)
                if val: data['stats'][attr] = int(val)
            ask_price = girl.get('AskPrice')
            if ask_price:
                try:
                    data['ask_price'] = int(ask_price)
                except (ValueError, TypeError):
                    pass
            # All WM skill attributes we can map to FM (canonical names handled in convert_wm_to_fm_worker)
            wm_skill_attrs = [
                'NormalSex', 'Anal', 'BDSM', 'OralSex', 'Group', 'Lesbian',
                'Combat', 'Magic', 'Service', 'Strip', 'Handjob', 'TittySex',
                'Footjob', 'Beastiality', 'Medicine', 'Performance', 'Crafting',
                'Farming', 'Cooking', 'Herbalism', 'Brewing', 'AnimalHandling', 'Card', 'Sport'
            ]
            for attr in wm_skill_attrs:
                val = girl.get(attr)
                if val:
                    try:
                        data['skills'][attr] = int(val)
                    except (ValueError, TypeError):
                        pass
            for trait in girl.findall('Trait'):
                data['traits'].append(trait.get('Name'))
        return data
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None

def convert_wm_to_fm_worker(wm_data: Dict, folder_name: str, all_skills: List[str]) -> Dict:
    """Convert Whoremaster character data to Fantasy Manager format.
    
    File type rules:
    - .girlsx = unique workers → unique: true, encounter_only: true, procedural: false
    - .rgirlsx = random templates → unique: false, encounter_only: false, procedural: true
    """
    is_random = wm_data.get('is_random', False)
    
    # Mapear AskPrice a comfort_desired
    # Normalizar AskPrice (0-1000+) a comfort_desired (1-5)
    ask_price = wm_data.get('ask_price', 0)
    if ask_price > 0:
        # Convertir AskPrice a comfort_desired (escala 1-5)
        if ask_price <= 200:
            comfort_desired = 1
        elif ask_price <= 400:
            comfort_desired = 2
        elif ask_price <= 600:
            comfort_desired = 3
        elif ask_price <= 800:
            comfort_desired = 4
        else:
            comfort_desired = 5
    else:
        comfort_desired = 3  # Default
    
    # For .rgirlsx (procedural templates), assign random name from female names pool
    if is_random:
        worker_name = random.choice(FEMALE_NAMES)
        names_list = "western_female"  # Set names_list so procedural workers use this pool
    else:
        # For .girlsx (unique workers), use the processed name from XML
        worker_name = wm_data.get('name', 'Unknown')
        names_list = None  # Unique workers don't need names_list
    
    # Cost in same range as game unique/encounter workers (1200-1500)
    base_cost = 1300 if not is_random else random.randint(1200, 1400)
    fm_worker = {
        "name": worker_name, "folder": folder_name, "cost": base_cost,
        "nsfw": True, 
        "unique": not is_random,           # .girlsx = unique, .rgirlsx = not unique
        "encounter_only": not is_random,   # .girlsx = encounter_only, .rgirlsx = can be bought
        "monster": False,
        "procedural": is_random,           # .rgirlsx = procedural generation
        "skills": {}, "traits": ["Human"],
        "description": wm_data.get('description', ''), "gender": "female", 
        "comfort_desired": comfort_desired
    }
    
    # Add names_list for procedural workers so generated workers use the same name pool
    if names_list:
        fm_worker["names_list"] = names_list
    
    # Baseline similar to game unique workers: main skills 20-30, Specialty 4-12 varied 18-32
    specialty_skills = [s for s in all_skills if s.startswith("Specialty ")]
    main_skills = [s for s in all_skills if s not in specialty_skills]
    for skill_name in main_skills:
        fm_worker["skills"][skill_name] = random.randint(20, 30)
    for skill_name in specialty_skills:
        fm_worker["skills"][skill_name] = random.randint(18, 32)
    
    # Overwrite only skills that ARE specified in Whoremaster, using conversion WM scale → FM 0-100
    for wm_skill, value in wm_data.get('skills', {}).items():
        fm_skill_canonical = WM_SKILL_MAPPING.get(wm_skill)
        if fm_skill_canonical is None:
            fm_skill_canonical = wm_skill if wm_skill in all_skills else (wm_skill[:1].upper() + wm_skill[1:] if wm_skill else None)
        if fm_skill_canonical and fm_skill_canonical in all_skills:
            if isinstance(value, dict):
                # .rgirlsx: use midpoint of Min/Max, then convert to FM scale
                wm_mid = (value.get('min', 0) + value.get('max', 100)) // 2
                fm_worker["skills"][fm_skill_canonical] = convert_wm_skill_value_to_fm(wm_mid)
            else:
                # .girlsx: raw value, convert WM scale → FM 0-100
                fm_worker["skills"][fm_skill_canonical] = convert_wm_skill_value_to_fm(int(value))
    
    TRAIT_REQUIREMENTS = {
        "Strong Magic": "Magical",
        "Powerful Magic": "Magical",
        "Psychic": "Magical",
    }
    
    fm_traits = ["Human"]
    for trait in wm_data.get('traits', []):
        trait_name = trait.get('name', '') if isinstance(trait, dict) else trait
        fm_trait = WM_TRAIT_MAPPING.get(trait_name)
        if fm_trait and fm_trait not in fm_traits:
            if fm_trait in TRAIT_REQUIREMENTS:
                required_trait = TRAIT_REQUIREMENTS[fm_trait]
                if required_trait not in fm_traits:
                    fm_traits.append(required_trait)
            
            if fm_trait in ["Elf", "Dwarf", "Demon", "Angel", "Vampire", "Orc", "Goblin", "Transformed"]:
                fm_traits = [t for t in fm_traits if t != "Human"]
            fm_traits.append(fm_trait)
    fm_worker["traits"] = fm_traits
    return fm_worker

class FantasyManagerEditorV6:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Fantasy Manager Editor v{VERSION} - Complete Edition with Event Probability")
        self.root.geometry("1600x1000")
        
        # Variables de datos
        self.workers_data = []
        self.traits_data = []
        self.buildings_data = {}
        self.events_data = {}
        self.interactions_data = []
        self.items_data = {}
        
        # Variables de estado
        self.current_worker = None
        self.current_trait = None
        self.current_building = None
        self.current_profession = None
        self.current_profession_index = None
        self.current_event = None
        self.current_interaction = None
        self.current_item = None
        
        self.game_directory = None
        self.image_configs = {}
        self.current_workers_file = None
        
        # FFmpeg availability
        self.has_ffmpeg = check_ffmpeg()
        
        # Image cache for preview
        self.image_cache = {}
        
        # Lista de habilidades
        self.all_skills = [
            "Sex", "Anal", "BDSM", "Hand", "Oral", "Homo", "Special", "Group",
            "Extreme", "Striptease", "Combat", "Clever", "Charm", "Service",
            "Agility", "Craft", "Specialty 4", "Specialty 5", "Specialty 6",
            "Specialty 7", "Specialty 8", "Specialty 9", "Specialty 10",
            "Specialty 11", "Specialty 12"
        ]
        
        self.has_unsaved_changes = False
        
        self.setup_ui()
        self.bind_mouse_wheel()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-detect game path (based on script location)
        self.auto_detect_game_path()
        
        # Show FFmpeg status
        if self.has_ffmpeg:
            self.update_status("Ready - FFmpeg available for GIF conversion")
        else:
            self.update_status("Ready - FFmpeg not found (GIF to WebM conversion disabled)")
    
    def auto_detect_game_path(self):
        """Try to auto-detect game directory based on script location."""
        current_dir = Path(__file__).parent.parent
        if (current_dir / "game" / "data").exists():
            self.set_game_directory(str(current_dir))
            self.update_status(f"Auto-detected game directory: {current_dir}")
    
    def get_initial_dir(self, subpath=""):
        """Get initial directory for file dialogs, or None if not set."""
        if self.game_directory:
            path = Path(self.game_directory) / "game" / subpath if subpath else Path(self.game_directory)
            if path.exists():
                return str(path)
        return None
    
    def set_game_directory(self, path):
        """Establece el directorio del juego"""
        self.game_directory = path
        self.load_all_data()
    
    def bind_mouse_wheel(self):
        """Habilitar scroll del ratón"""
        def _on_mousewheel(event):
            try:
                widget = event.widget
                if hasattr(widget, 'winfo_class'):
                    if widget.winfo_class() in ['Listbox', 'Text', 'Canvas']:
                        if hasattr(widget, 'yview_scroll'):
                            delta = getattr(event, 'delta', 0)
                            if delta != 0:
                                widget.yview_scroll(int(-1*(delta/120)), "units")
            except:
                pass
        self.root.bind_all("<MouseWheel>", _on_mousewheel)
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Game Directory", command=self.select_game_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Save All", command=self.save_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Convert GIFs to WebM...", command=self.convert_gifs_dialog)
        tools_menu.add_command(label="Batch Rename Images...", command=self.batch_rename_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="Create Worker from Image Folder...", command=self.create_worker_from_folder)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.setup_wm_import_tab()
        self.setup_workers_tab()
        self.setup_traits_tab()
        self.setup_buildings_tab()
        self.setup_events_tab()
        self.setup_interactions_tab()
        self.setup_items_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message):
        """Actualizar barra de estado"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    # ==================== WM IMPORT TAB ====================
    
    def setup_wm_import_tab(self):
        """Setup the Whoremaster Import tab."""
        import_frame = ttk.Frame(self.notebook)
        self.notebook.add(import_frame, text="🔄 WM Import")
        
        # Header
        header = ttk.Label(import_frame, text="Whoremaster Character & Item Importer", 
                          font=("Arial", 14, "bold"))
        header.pack(pady=10)
        
        desc = ttk.Label(import_frame, text=
            "Import characters and items from Whoremaster.\n"
            "Converts XML files (.girlsx, .rgirlsx, .itemsx) to Fantasy Manager JSON format.",
            justify=tk.CENTER)
        desc.pack(pady=5)
        
        # Main content frame
        content = ttk.Frame(import_frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left: Source selection
        left_frame = ttk.LabelFrame(content, text="Source (Whoremaster)")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(left_frame, text="WM Characters Folder:").pack(anchor="w", padx=5, pady=5)
        
        wm_path_frame = ttk.Frame(left_frame)
        wm_path_frame.pack(fill=tk.X, padx=5)
        
        self.wm_characters_path = tk.StringVar()
        ttk.Entry(wm_path_frame, textvariable=self.wm_characters_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(wm_path_frame, text="Browse...", command=self.browse_wm_characters).pack(side=tk.RIGHT, padx=5)
        
        # Character list
        ttk.Label(left_frame, text="Available Characters:").pack(anchor="w", padx=5, pady=(10, 5))
        
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.wm_characters_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=15)
        self.wm_characters_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.wm_characters_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.wm_characters_listbox.config(yscrollcommand=scrollbar.set)
        
        ttk.Button(left_frame, text="Scan for Characters", command=self.scan_wm_characters).pack(pady=10)
        
        # Right: Options and actions
        right_frame = ttk.LabelFrame(content, text="Import Options")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Options
        self.import_copy_images = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Copy image folders", variable=self.import_copy_images).pack(anchor="w", padx=10, pady=5)
        
        self.import_convert_gifs = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(right_frame, text="Convert GIFs to WebM", variable=self.import_convert_gifs)
        cb.pack(anchor="w", padx=10, pady=5)
        
        ffmpeg_frame = ttk.Frame(right_frame)
        ffmpeg_frame.pack(anchor="w", padx=30, pady=2)
        
        if not self.has_ffmpeg:
            cb.config(state="disabled")
            ttk.Label(ffmpeg_frame, text="(FFmpeg not found)", foreground="red").pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(ffmpeg_frame, text="Install FFmpeg", command=self.install_ffmpeg_dialog).pack(side=tk.LEFT)
        
        self.import_rename_images = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Rename images for FM compatibility", variable=self.import_rename_images).pack(anchor="w", padx=10, pady=5)
        
        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, padx=10, pady=10)
        
        # Output
        ttk.Label(right_frame, text="Output File:").pack(anchor="w", padx=10, pady=5)
        self.import_output_file = tk.StringVar(value="workers_wm_imported.json")
        ttk.Entry(right_frame, textvariable=self.import_output_file, width=40).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Separator(right_frame, orient="horizontal").pack(fill=tk.X, padx=10, pady=10)
        
        # Action buttons
        ttk.Button(right_frame, text="Import Selected Characters", command=self.import_selected_characters).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(right_frame, text="Import All Characters", command=self.import_all_characters).pack(fill=tk.X, padx=10, pady=5)
        
        # Progress
        self.import_progress = ttk.Progressbar(right_frame, mode='determinate')
        self.import_progress.pack(fill=tk.X, padx=10, pady=10)
        
        self.import_status = ttk.Label(right_frame, text="Ready to import")
        self.import_status.pack(anchor="w", padx=10, pady=5)
    
    def browse_wm_characters(self):
        """Browse for WM Characters folder."""
        path = filedialog.askdirectory(title="Select Whoremaster Characters Folder")
        if path:
            self.wm_characters_path.set(path)
            self.scan_wm_characters()
    
    def scan_wm_characters(self):
        """Scan for .girlsx and .rgirlsx files."""
        path = self.wm_characters_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Please select a valid folder")
            return
        
        self.wm_characters_listbox.delete(0, tk.END)
        
        for file in Path(path).iterdir():
            if file.suffix.lower() in ['.girlsx', '.rgirlsx']:
                self.wm_characters_listbox.insert(tk.END, file.name)
        
        count = self.wm_characters_listbox.size()
        self.import_status.config(text=f"Found {count} character files")
    
    def import_selected_characters(self):
        """Import selected characters."""
        selection = self.wm_characters_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No characters selected")
            return
        files = [self.wm_characters_listbox.get(i) for i in selection]
        self._do_wm_import(files)
    
    def import_all_characters(self):
        """Import all characters."""
        files = [self.wm_characters_listbox.get(i) for i in range(self.wm_characters_listbox.size())]
        if not files:
            messagebox.showwarning("Warning", "No characters found")
            return
        self._do_wm_import(files)
    
    def _do_wm_import(self, files):
        """Perform the actual import."""
        if not self.game_directory:
            messagebox.showerror("Error", "Please select a game directory first")
            return
        
        wm_path = Path(self.wm_characters_path.get())
        output_file = Path(self.game_directory) / "game" / "data" / "workers" / self.import_output_file.get()
        images_dest = Path(self.game_directory) / "game" / "images" / "workers"
        
        imported_workers = []
        total = len(files)
        gifs_to_convert = []  # Collect GIFs to convert after copying
        
        self.import_progress['maximum'] = total
        self.import_progress['value'] = 0
        
        # Step 1: Import characters and copy images
        for i, filename in enumerate(files):
            self.import_status.config(text=f"Importing {filename}... ({i+1}/{total})")
            self.root.update_idletasks()
            
            xml_path = wm_path / filename
            wm_data = parse_wm_girl_xml(xml_path)
            
            if wm_data:
                folder_name = sanitize_folder_name(wm_data['name'])
                fm_worker = convert_wm_to_fm_worker(wm_data, folder_name, self.all_skills)
                imported_workers.append(fm_worker)
                
                # Copy images if enabled
                if self.import_copy_images.get():
                    # Use XML name for image folder (WM folders use full XML name)
                    if 'xml_name' in wm_data:
                        img_folder = wm_path / wm_data['xml_name']
                    if img_folder.exists():
                        dest_folder = images_dest / folder_name
                        if not dest_folder.exists():
                            try:
                                shutil.copytree(img_folder, dest_folder)
                            except Exception as e:
                                print(f"Error copying images: {e}")
                        
                        # Rename images for FM compatibility
                        if self.import_rename_images.get():
                            rename_wm_images_in_folder(dest_folder)
                        
                        # Collect GIFs for batch conversion
                        if self.import_convert_gifs.get() and self.has_ffmpeg:
                            for gif in dest_folder.glob("*.gif"):
                                gifs_to_convert.append(gif)
            
            self.import_progress['value'] = i + 1
            self.root.update_idletasks()
        
        # Step 2: Convert GIFs in batch with progress
        converted = 0
        failed = 0
        if gifs_to_convert and self.import_convert_gifs.get() and self.has_ffmpeg:
            total_gifs = len(gifs_to_convert)
            self.import_progress['maximum'] = total + total_gifs
            self.import_status.config(text=f"Converting {total_gifs} GIFs to WebM...")
            self.root.update()
            
            for i, gif in enumerate(gifs_to_convert):
                self.import_status.config(text=f"Converting {gif.name}... ({i+1}/{total_gifs})")
                self.root.update_idletasks()
                self.root.update()  # Force update
                
                try:
                    success, msg = convert_gif_to_webm(gif)
                    if success:
                        converted += 1
                    else:
                        failed += 1
                        print(f"Failed to convert {gif.name}: {msg}")
                except Exception as e:
                    failed += 1
                    print(f"Error converting {gif.name}: {e}")
                
                self.import_progress['value'] = total + i + 1
                self.root.update_idletasks()
                self.root.update()  # Force update every iteration
            
            if failed > 0:
                self.import_status.config(text=f"Converted {converted}/{total_gifs} GIFs ({failed} failed)")
            else:
                self.import_status.config(text=f"Converted {converted} GIFs to WebM")
            self.root.update()
        
        # Step 3: Save to JSON
        self.import_status.config(text="Saving JSON file...")
        self.root.update()
        self.root.update_idletasks()
        
        saved_successfully = False
        error_message = None
        
        try:
            print(f"[DEBUG] Preparing to save to: {output_file}")
            print(f"[DEBUG] Output directory: {output_file.parent}")
            print(f"[DEBUG] Workers to save: {len(imported_workers)}")
            
            # Ensure directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            print(f"[DEBUG] Directory created/verified: {output_file.parent.exists()}")
            
            # Save JSON file
            print(f"[DEBUG] Opening file for writing...")
            with open(output_file, 'w', encoding='utf-8') as f:
                print(f"[DEBUG] Writing JSON data...")
                json.dump(imported_workers, f, indent=2, ensure_ascii=False)
                f.flush()  # Force write to disk
                os.fsync(f.fileno())  # Ensure data is written
            
            print(f"[DEBUG] File written, verifying...")
            
            # Verify file was created
            if output_file.exists():
                file_size = output_file.stat().st_size
                print(f"[DEBUG] File exists! Size: {file_size} bytes")
                saved_successfully = True
            else:
                error_message = "File was not created"
                print(f"[ERROR] File does not exist after write!")
            
        except PermissionError as e:
            error_message = f"Permission denied: {e}\n\nMake sure the file is not open in another program."
            print(f"[ERROR] Permission error: {e}")
        except OSError as e:
            error_message = f"File system error: {e}"
            print(f"[ERROR] OS error: {e}")
        except Exception as e:
            error_message = f"Failed to save: {e}"
            print(f"[ERROR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        # Update UI
        self.import_progress['value'] = self.import_progress['maximum']
        self.root.update()
        self.root.update_idletasks()
        
        # Show result message
        if saved_successfully:
            self.import_status.config(text=f"Imported {len(imported_workers)} characters to {output_file.name}")
            result_msg = f"Imported {len(imported_workers)} characters!\nSaved to: {output_file.name}"
            if gifs_to_convert:
                result_msg += f"\n\nConverted {converted} GIFs to WebM"
                if failed > 0:
                    result_msg += f" ({failed} failed)"
            
            # Show success message immediately (don't use after for critical messages)
            messagebox.showinfo("Success", result_msg)
            
            # self.root.after(100, lambda: self._reload_workers_background())
        else:
            self.import_status.config(text=f"Error: {error_message or 'Unknown error'}")
            messagebox.showerror("Error", error_message or "Failed to save JSON file")
    
    def _reload_workers_background(self):
        """Reload workers data in background without blocking."""
        try:
            self.load_workers_files(Path(self.game_directory) / "game" / "data")
            self.refresh_workers_list()
        except Exception as e:
            print(f"Warning: Could not reload workers: {e}")
    
    # ==================== MENU FUNCTIONS ====================
    
    def save_all_data(self):
        """Save all modified data files."""
        saved = []
        if self.workers_data and self.current_workers_file:
            self.save_workers()
            saved.append("Workers")
        if self.traits_data:
            self.save_traits()
            saved.append("Traits")
        if saved:
            messagebox.showinfo("Saved", f"Saved: {', '.join(saved)}")
        else:
            messagebox.showinfo("Info", "Nothing to save")
    
    def install_ffmpeg_dialog(self):
        """Show dialog to install FFmpeg."""
        instructions = get_ffmpeg_install_instructions()
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Install FFmpeg")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        ttk.Label(dialog, text="FFmpeg Installation", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Instructions text
        text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, height=15, width=70)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, instructions)
        text_widget.config(state=tk.DISABLED)
        
        # Buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        # Try auto-install button
        def try_auto_install():
            self.update_status("Attempting to install FFmpeg...")
            success, msg = install_ffmpeg_auto()
            if success:
                messagebox.showinfo("Success", msg + "\n\nPlease restart the editor for changes to take effect.")
                dialog.destroy()
            else:
                messagebox.showwarning("Auto-install Failed", 
                    f"{msg}\n\nPlease use manual installation (see instructions above).")
        
        ttk.Button(btn_frame, text="Try Auto-Install (Windows)", command=try_auto_install).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Open Download Page", 
                  command=lambda: subprocess.run(['start', 'https://www.gyan.dev/ffmpeg/builds/'], shell=True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def convert_gifs_dialog(self):
        """Show dialog to convert GIFs."""
        if not self.has_ffmpeg:
            response = messagebox.askyesno("FFmpeg Not Found", 
                "FFmpeg is required to convert GIFs to WebM.\n\n"
                "Would you like to see installation instructions?")
            if response:
                self.install_ffmpeg_dialog()
            return
        
        folder = filedialog.askdirectory(title="Select folder with GIFs to convert")
        if folder:
            converted = 0
            errors = 0
            for gif in Path(folder).rglob("*.gif"):
                success, msg = convert_gif_to_webm(gif)
                if success:
                    converted += 1
                else:
                    errors += 1
                    print(msg)
            messagebox.showinfo("Done", f"Converted {converted} GIF files to WebM\nErrors: {errors}")
    
    def batch_rename_dialog(self):
        """Show dialog for batch rename."""
        folder = filedialog.askdirectory(title="Select folder with images to rename")
        if not folder:
            return
        
        # Simple renaming patterns for WM compatibility
        rename_map = {
            "Les ": "gay ", "Les.": "gay.", "Les(": "gay(",
            "Beast ": "extreme ", "Beast.": "extreme.", "Beast(": "extreme(",
            "Preggo ": "pregnant ", "Preggo.": "pregnant.", "Preggo(": "pregnant(",
        }
        
        renamed = 0
        for file in Path(folder).iterdir():
            if file.is_file():
                new_name = file.name
                for old, new in rename_map.items():
                    if old in new_name:
                        new_name = new_name.replace(old, new)
                
                # Also lowercase the extension
                if file.suffix.upper() != file.suffix:
                    new_name = file.stem + file.suffix.lower()
                
                if new_name != file.name:
                    try:
                        file.rename(file.parent / new_name)
                        renamed += 1
                    except Exception as e:
                        print(f"Error renaming {file.name}: {e}")
        
        messagebox.showinfo("Done", f"Renamed {renamed} files")
    
    def create_worker_from_folder(self):
        """Create a new worker from an image folder."""
        initial = self.get_initial_dir("images/workers")
        folder = filedialog.askdirectory(
            title="Select Image Folder for New Worker",
            initialdir=initial
        )
        
        if not folder:
            return
        
        folder_path = Path(folder)
        folder_name = folder_path.name
        
        # Detect skills from image names
        detected_skills = set()
        media_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.webm', '.mp4'}
        
        for img in folder_path.iterdir():
            if img.suffix.lower() in media_extensions:
                name = img.stem.lower()
                for skill in self.all_skills:
                    if skill.lower() in name:
                        detected_skills.add(skill)
        
        # Create basic worker
        new_worker = {
            "name": folder_name.replace("_", " ").title(),
            "folder": folder_name,
            "cost": 1000,
            "nsfw": True,
            "unique": False,
            "encounter_only": False,
            "monster": False,
            "procedural": False,
            "skills": {skill: 30 for skill in self.all_skills},
            "traits": ["Human"],
            "description": f"A worker with images in {folder_name}",
            "gender": "female",
            "comfort_desired": 3
        }
        
        # Boost detected skills
        for skill in detected_skills:
            new_worker["skills"][skill] = 50
        
        # Add to current workers data
        self.workers_data.append(new_worker)
        self.refresh_workers_list()
        
        messagebox.showinfo("Worker Created", 
            f"Created worker: {new_worker['name']}\n"
            f"Folder: {folder_name}\n"
            f"Detected skills: {', '.join(detected_skills) or 'None'}\n\n"
            "Worker added to current list. Remember to save!")
        
        self.has_unsaved_changes = True
        self.update_title()
    
    def show_about(self):
        """Show about dialog."""
        about_text = f"""Fantasy Manager Editor v{VERSION}

A complete editor for Fantasy Manager game data.

Features:
• Whoremaster import
• Image conversion (GIF→WebM)
• Workers, Traits, Events, Items editors
• Image preview and management

FFmpeg: {'Available ✓' if self.has_ffmpeg else 'Not found ✗'}
PIL: {'Available ✓' if PIL_AVAILABLE else 'Not found ✗'}

Requirements:
• pip install Pillow (for image preview)
• FFmpeg in PATH (for GIF conversion)
"""
        messagebox.showinfo("About", about_text)
    
    def select_game_directory(self):
        """Seleccionar directorio del juego"""
        path = filedialog.askdirectory(title="Select Game Directory (fantasy-manager folder)")
        if path:
            if not (Path(path) / "game" / "data").exists():
                messagebox.showerror("Error", 
                    "Selected folder doesn't contain 'game/data'.\n"
                    "Please select the root project folder (fantasy-manager).")
                return
            self.set_game_directory(path)
            messagebox.showinfo("Success", f"Game directory set: {path}")
    
    def load_all_data(self):
        """Cargar todos los archivos de datos"""
        if not self.game_directory:
            return
        
        data_path = Path(self.game_directory) / "game" / "data"
        
        # self.load_workers_files(data_path)
        
        # Cargar traits
        self.load_traits_file(data_path)
        
        # Cargar buildings
        self.load_buildings_file(data_path)
        
        # Cargar events
        self.load_events_files(data_path)
        
        # Cargar interactions
        self.load_interactions_files(data_path)
        
        # Cargar items
        self.load_items_file(data_path)
        
        if hasattr(self, 'traits_listbox'):
            self.refresh_traits_list()
        if hasattr(self, 'buildings_listbox'):
            self.refresh_buildings_list()
        if hasattr(self, 'events_listbox'):
            self.refresh_events_list()
        if hasattr(self, 'interactions_listbox'):
            self.refresh_interactions_list()
        if hasattr(self, 'items_listbox'):
            self.refresh_items_list()
        self.status_bar.config(text="Data loaded (workers not loaded - use 'Load Workers File' to load manually)")
    
    def load_workers_files(self, data_path):
        """Cargar archivos de workers"""
        self.workers_data = []
        worker_files = [
            "workers/workers_sfw_unique.json",
            "workers/workers_sfw_other.json",
            "workers/workers_nsfw_unique.json",
            "workers/workers_nsfw_other.json"
        ]
        
        seen_names = set()
        
        for file_path in worker_files:
            full_path = data_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for worker in data:
                                if worker.get('images_folder') == '' or worker.get('images_folder') is None:
                                    worker.pop('images_folder', None)
                                if worker.get('image_folder') == '' or worker.get('image_folder') is None:
                                    worker.pop('image_folder', None)
                                
                                worker_name = worker.get('name', '')
                                if worker_name and worker_name not in seen_names:
                                    self.workers_data.append(worker)
                                    seen_names.add(worker_name)
                                elif worker_name:
                                    print(f"Warning: Duplicate worker '{worker_name}' skipped from {file_path}")
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
    
    def load_traits_file(self, data_path):
        """Cargar archivo de traits"""
        traits_path = data_path / "traits.json"
        if traits_path.exists():
            try:
                with open(traits_path, 'r', encoding='utf-8') as f:
                    self.traits_data = json.load(f)
                # Update item trait combos if they exist
                self.update_item_trait_combos()
            except Exception as e:
                print(f"Error loading traits: {e}")
                self.traits_data = []
    
    def load_buildings_file(self, data_path):
        """Cargar archivo de buildings"""
        buildings_path = data_path / "buildings" / "building_types.json"
        if buildings_path.exists():
            try:
                with open(buildings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.buildings_data = data.get("building_types", [])
            except Exception as e:
                print(f"Error loading buildings: {e}")
                self.buildings_data = []
    
    def load_events_files(self, data_path):
        """Cargar archivos de events"""
        self.events_data = {}
        event_files = [
            "events/events_building.json",
            "events/events_common.json",
            "events/events_seasonal.json",
            "events/events_shops.json"
        ]
        
        for file_path in event_files:
            full_path = data_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for event in data:
                                if "id" in event:
                                    self.events_data[event["id"]] = event
                        elif isinstance(data, dict):
                            self.events_data.update(data)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
    
    def load_interactions_files(self, data_path):
        """Cargar archivos de interactions"""
        self.interactions_data = []
        interaction_files = [
            "interactions/interactions_main.json",
            "interactions/interactions_special.json",
            "interactions/interactions_structured.json"
        ]
        
        for file_path in interaction_files:
            full_path = data_path / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.interactions_data.extend(data)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
    
    def load_items_file(self, data_path):
        """Cargar archivo de items"""
        items_path = data_path / "items" / "items.json"
        if items_path.exists():
            try:
                with open(items_path, 'r', encoding='utf-8') as f:
                    self.items_data = json.load(f)
            except Exception as e:
                print(f"Error loading items: {e}")
                self.items_data = {"items": [], "excluded_from_shops": []}
    
    def refresh_all_lists(self):
        """Actualizar todas las listas"""
        if hasattr(self, 'workers_listbox'):
            self.refresh_workers_list()
        if hasattr(self, 'traits_listbox'):
            self.refresh_traits_list()
        if hasattr(self, 'buildings_listbox'):
            self.refresh_buildings_list()
        if hasattr(self, 'events_listbox'):
            self.refresh_events_list()
        if hasattr(self, 'interactions_listbox'):
            self.refresh_interactions_list()
        if hasattr(self, 'items_listbox'):
            self.refresh_items_list()
    
    def on_closing(self):
        """Manejar cierre de ventana"""
        if self.has_unsaved_changes:
            if messagebox.askyesno("Unsaved Changes", 
                "You have unsaved changes. Do you want to exit anyway?"):
                self.root.destroy()
        else:
            self.root.destroy()
    
    def update_title(self):
        """Actualizar título de ventana"""
        title = f"Fantasy Manager Editor v{VERSION}"
        if self.has_unsaved_changes:
            title += " *"
        self.root.title(title)
    
    # ==================== WORKERS TAB ====================
    
    def setup_workers_tab(self):
        """Configurar pestaña de Workers"""
        workers_frame = ttk.Frame(self.notebook)
        self.notebook.add(workers_frame, text="Workers")
        
        main_frame = ttk.Frame(workers_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Columna izquierda - Lista de workers
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="Workers List", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Lista de workers
        self.workers_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.workers_listbox.pack(fill=tk.BOTH, expand=True)
        self.workers_listbox.bind('<<ListboxSelect>>', self.on_worker_select)
        
        # Botones de workers
        workers_buttons_frame = ttk.Frame(left_frame)
        workers_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(workers_buttons_frame, text="New Worker", command=self.new_worker).pack(fill=tk.X, pady=2)
        ttk.Button(workers_buttons_frame, text="New from Template", command=self.new_worker_from_template).pack(fill=tk.X, pady=2)
        ttk.Button(workers_buttons_frame, text="Duplicate Worker", command=self.duplicate_worker).pack(fill=tk.X, pady=2)
        ttk.Button(workers_buttons_frame, text="Delete Worker", command=self.delete_worker).pack(fill=tk.X, pady=2)
        ttk.Separator(workers_buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(workers_buttons_frame, text="Load Workers File", command=self.load_workers_file_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(workers_buttons_frame, text="Save Workers As...", command=self.save_workers_as).pack(fill=tk.X, pady=2)
        ttk.Button(workers_buttons_frame, text="Save Workers", command=self.save_workers).pack(fill=tk.X, pady=2)
        
        # Columna derecha - Editor de worker
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        worker_header_frame = ttk.Frame(right_frame)
        worker_header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(worker_header_frame, text="Worker Editor", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(worker_header_frame, text="? Help", command=self.show_worker_help).pack(side=tk.RIGHT)
        
        self.worker_notebook = ttk.Notebook(right_frame)
        self.worker_notebook.pack(fill=tk.BOTH, expand=True)
        
        basic_frame = ttk.Frame(self.worker_notebook)
        self.worker_notebook.add(basic_frame, text="Basic Information")
        
        basic_canvas = tk.Canvas(basic_frame)
        basic_scrollbar = ttk.Scrollbar(basic_frame, orient="vertical", command=basic_canvas.yview)
        basic_scrollable_frame = ttk.Frame(basic_canvas)
        
        basic_scrollable_frame.bind(
            "<Configure>",
            lambda e: basic_canvas.configure(scrollregion=basic_canvas.bbox("all"))
        )
        
        basic_canvas.create_window((0, 0), window=basic_scrollable_frame, anchor="nw")
        basic_canvas.configure(yscrollcommand=basic_scrollbar.set)
        
        basic_canvas.pack(side="left", fill="both", expand=True)
        basic_scrollbar.pack(side="right", fill="y")
        
        self.setup_worker_basic_fields(basic_scrollable_frame)
        
        images_frame = ttk.Frame(self.worker_notebook)
        self.worker_notebook.add(images_frame, text="Images")
        self.setup_worker_images_tab(images_frame)
    
    def setup_worker_basic_fields(self, parent):
        """Configurar campos básicos del worker"""
        row = 0
        
        # Name
        ttk.Label(parent, text="Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.worker_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.worker_name_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Description
        ttk.Label(parent, text="Description:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        self.worker_description_text = scrolledtext.ScrolledText(parent, width=50, height=4)
        self.worker_description_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Folder (images):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        folder_frame = ttk.Frame(parent)
        folder_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.worker_folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.worker_folder_var, width=30).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(folder_frame, text="Browse", command=self.browse_worker_folder).pack(side=tk.LEFT)
        row += 1
        
        # Cost
        ttk.Label(parent, text="Cost:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.worker_cost_var = tk.IntVar(value=1000)
        ttk.Spinbox(parent, from_=0, to=999999, textvariable=self.worker_cost_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Gender
        ttk.Label(parent, text="Gender:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.worker_gender_var = tk.StringVar(value="female")
        ttk.Combobox(parent, textvariable=self.worker_gender_var, values=["female", "male"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Checkboxes
        self.worker_nsfw_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="NSFW", variable=self.worker_nsfw_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        self.worker_unique_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Unique", variable=self.worker_unique_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        self.worker_encounter_only_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Encounter Only", variable=self.worker_encounter_only_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        self.worker_monster_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Monster", variable=self.worker_monster_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        self.worker_procedural_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Procedural", variable=self.worker_procedural_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Comfort Desired
        ttk.Label(parent, text="Comfort Desired:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.worker_comfort_desired_var = tk.IntVar(value=5)
        ttk.Spinbox(parent, from_=0, to=20, textvariable=self.worker_comfort_desired_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Names List
        ttk.Label(parent, text="Names List:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.worker_names_list_var = tk.StringVar(value="western_female")
        names_list_values = ["western_female", "western_male", "eastern_female", "eastern_male", "fantasy_female", "fantasy_male"]
        ttk.Combobox(parent, textvariable=self.worker_names_list_var, values=names_list_values, width=20).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Skills
        ttk.Label(parent, text="Skills", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        skills_frame = ttk.Frame(parent)
        skills_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.worker_skills_vars = {}
        skills_per_row = 4
        for idx, skill in enumerate(self.all_skills):
            skill_frame = ttk.Frame(skills_frame)
            skill_frame.grid(row=idx // skills_per_row, column=idx % skills_per_row, padx=5, pady=2, sticky="w")
            
            ttk.Label(skill_frame, text=f"{skill}:").pack(side=tk.LEFT)
            var = tk.IntVar(value=5)
            self.worker_skills_vars[skill] = var
            ttk.Spinbox(skill_frame, from_=0, to=100, textvariable=var, width=8).pack(side=tk.LEFT, padx=2)
        
        row += 1
        
        # Traits
        ttk.Label(parent, text="Traits", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        traits_frame = ttk.Frame(parent)
        traits_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.worker_traits_listbox = tk.Listbox(traits_frame, height=6)
        self.worker_traits_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        traits_buttons_frame = ttk.Frame(traits_frame)
        traits_buttons_frame.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(traits_buttons_frame, text="Add Trait", command=self.add_trait_to_worker).pack(pady=2)
        ttk.Button(traits_buttons_frame, text="Remove Trait", command=self.remove_trait_from_worker).pack(pady=2)
        
        parent.columnconfigure(1, weight=1)
    
    def setup_worker_images_tab(self, parent):
        """Configurar pestaña de imágenes del worker"""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(main_frame, text="Image Management", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Botones de control
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(buttons_frame, text="Select Images Folder", command=self.select_images_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Auto-detect Configuration", command=self.auto_detect_image_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Select All", command=self.select_all_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Deselect All", command=self.deselect_all_images).pack(side=tk.LEFT, padx=5)
        
        images_canvas = tk.Canvas(main_frame)
        images_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=images_canvas.yview)
        self.images_scrollable_frame = ttk.Frame(images_canvas)
        
        self.images_scrollable_frame.bind(
            "<Configure>",
            lambda e: images_canvas.configure(scrollregion=images_canvas.bbox("all"))
        )
        
        images_canvas.create_window((0, 0), window=self.images_scrollable_frame, anchor="nw")
        images_canvas.configure(yscrollcommand=images_scrollbar.set)
        
        images_canvas.pack(side="left", fill="both", expand=True)
        images_scrollbar.pack(side="right", fill="y")
        
        rename_frame = ttk.Frame(main_frame)
        rename_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(rename_frame, text="Rename Selected Files", command=self.rename_selected_images).pack()
        
        self.worker_images_folder_var = tk.StringVar()
    
    def browse_worker_folder(self):
        """Navegar por carpeta de imágenes del worker"""
        initial = self.get_initial_dir("images/workers")
        folder = filedialog.askdirectory(initialdir=initial, title="Select Worker Images Folder")
        if folder:
            folder_name = Path(folder).name
            self.worker_folder_var.set(folder_name)
            self.worker_images_folder_var.set(folder)
            self.load_images_from_folder_path(folder)
            if self.current_worker:
                self.current_worker['folder'] = folder_name
    
    def select_images_folder(self):
        """Seleccionar carpeta de imágenes"""
        initial = self.get_initial_dir("images/workers") or self.get_initial_dir("images") or self.get_initial_dir("")
        folder = filedialog.askdirectory(initialdir=initial, title="Select Images Folder")
        if folder:
            self.worker_images_folder_var.set(folder)
            self.load_images_from_folder_path(folder)
            if self.current_worker:
                folder_name = Path(folder).name
                if 'workers' in str(folder):
                    self.current_worker['folder'] = folder_name
                    self.worker_folder_var.set(folder_name)
    
    def load_images_from_folder_path(self, folder_path):
        """Cargar imágenes desde ruta específica"""
        if not os.path.exists(folder_path):
            return
        
        self.image_configs.clear()
        
        # Buscar archivos de imagen y video
        media_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.avi', '.mov', '.webm')
        media_files = []
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(media_extensions):
                media_files.append(file)
        
        # Eliminar duplicados y ordenar
        media_files = sorted(list(set(media_files)))
        
        for filename in media_files:
            self.image_configs[filename] = {
                'category': 'Skills',
                'trait': 'No trait',
                'specific': '',
                'failure': False,
                'selected': False
            }
        
        self.auto_detect_all_images_config()
        
        # Actualizar interfaz
        self.update_images_interface()
    
    def auto_detect_all_images_config(self):
        """Auto-detectar configuración de todas las imágenes"""
        for filename in self.image_configs.keys():
            self.auto_detect_single_image_config(filename)
    
    def auto_detect_single_image_config(self, filename):
        """Auto-detectar configuración de una imagen específica"""
        if filename not in self.image_configs:
            return
        
        name_lower = filename.lower()
        name_parts = name_lower.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').replace('.mp4', '').replace('.gif', '').replace('.webp', '').replace('.avi', '').replace('.mov', '').replace('.webm', '')
        
        # Detectar failure
        if 'failure' in name_parts or '_fail' in name_parts:
            self.image_configs[filename]['failure'] = True
            name_parts = name_parts.replace('_failure', '').replace('_fail', '')
        
        # Detectar trait
        trait_detected = 'No trait'
        if isinstance(self.traits_data, list):
            for trait in self.traits_data:
                trait_name = trait.get('name', '').lower()
                if trait_name and trait_name in name_parts:
                    trait_detected = trait.get('name', '')
                    name_parts = name_parts.replace(trait_name, '')
                    break
        
        self.image_configs[filename]['trait'] = trait_detected
        
        specific_detected = ''
        for skill in self.all_skills:
            if skill.lower() in name_parts:
                specific_detected = skill
                self.image_configs[filename]['category'] = 'Skills'
                break
        
        if not specific_detected:
            for event_id in self.events_data.keys():
                if event_id.lower() in name_parts:
                    specific_detected = event_id
                    self.image_configs[filename]['category'] = 'Events'
                    break
        
        if not specific_detected:
            for interaction in self.interactions_data:
                interaction_id = interaction.get('id', '').lower()
                if interaction_id and interaction_id in name_parts:
                    specific_detected = interaction.get('id', '')
                    self.image_configs[filename]['category'] = 'Interactions'
                    break
        
        self.image_configs[filename]['specific'] = specific_detected
    
    def auto_detect_image_config(self):
        """Auto-detectar configuración de imágenes (botón)"""
        self.auto_detect_all_images_config()
        self.update_images_interface()
    
    def update_images_interface(self):
        """Actualizar interfaz de imágenes"""
        # Limpiar frame
        for widget in self.images_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Crear encabezados
        headers = ["Sel", "File", "View", "Category", "Trait", "Specific", "Failure"]
        for col, header in enumerate(headers):
            ttk.Label(self.images_scrollable_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=2, pady=2, sticky="w")
        
        row = 1
        for filename, config in self.image_configs.items():
            self.create_image_config_row(row, filename, config)
            row += 1
    
    def create_image_config_row(self, row, filename, config):
        """Crear fila de configuración para una imagen"""
        selected_var = tk.BooleanVar(value=config['selected'])
        selected_var.trace('w', lambda *args, f=filename, v=selected_var: self.update_image_selection(f, v.get()))
        ttk.Checkbutton(self.images_scrollable_frame, variable=selected_var).grid(row=row, column=0, padx=2, pady=1)
        
        display_name = filename[:25] + "..." if len(filename) > 25 else filename
        ttk.Label(self.images_scrollable_frame, text=display_name).grid(row=row, column=1, padx=2, pady=1, sticky="w")
        
        ttk.Button(self.images_scrollable_frame, text="View", command=lambda f=filename: self.preview_image(f)).grid(row=row, column=2, padx=2, pady=1)
        
        category_var = tk.StringVar(value=config['category'])
        category_combo = ttk.Combobox(self.images_scrollable_frame, textvariable=category_var, 
                                     values=["Events", "Interactions", "Skills"], state="readonly", width=12)
        category_combo.grid(row=row, column=3, padx=2, pady=1)
        category_combo.bind('<<ComboboxSelected>>', lambda e, f=filename, v=category_var: self.update_image_category(f, v.get()))
        
        # Trait
        trait_values = ["No trait"]
        if isinstance(self.traits_data, list):
            trait_values.extend([t.get('name', '') for t in self.traits_data if t.get('name')])
        
        trait_var = tk.StringVar(value=config['trait'])
        trait_combo = ttk.Combobox(self.images_scrollable_frame, textvariable=trait_var, 
                                   values=trait_values, state="readonly", width=20)
        trait_combo.grid(row=row, column=4, padx=2, pady=1)
        trait_combo.bind('<<ComboboxSelected>>', lambda e, f=filename, v=trait_var: self.update_image_trait(f, v.get()))
        
        specific_values = self.get_specific_values_for_category(config['category'])
        specific_var = tk.StringVar(value=config['specific'])
        specific_combo = ttk.Combobox(self.images_scrollable_frame, textvariable=specific_var, 
                                     values=specific_values, state="readonly", width=15)
        specific_combo.grid(row=row, column=5, padx=2, pady=1)
        specific_combo.bind('<<ComboboxSelected>>', lambda e, f=filename, v=specific_var: self.update_image_specific(f, v.get()))
        
        # Failure
        failure_var = tk.BooleanVar(value=config['failure'])
        failure_var.trace('w', lambda *args, f=filename, v=failure_var: self.update_image_failure(f, v.get()))
        ttk.Checkbutton(self.images_scrollable_frame, variable=failure_var).grid(row=row, column=6, padx=2, pady=1)
    
    def get_specific_values_for_category(self, category):
        """Obtener valores específicos según la categoría"""
        if category == "Skills":
            return self.all_skills
        elif category == "Events":
            return list(self.events_data.keys())
        elif category == "Interactions":
            return [inter.get('id', '') for inter in self.interactions_data if inter.get('id')]
        else:
            return []
    
    def update_image_selection(self, filename, selected):
        """Actualizar selección de imagen"""
        if filename in self.image_configs:
            self.image_configs[filename]['selected'] = selected
    
    def update_image_category(self, filename, category):
        """Actualizar categoría de imagen"""
        if filename in self.image_configs:
            self.image_configs[filename]['category'] = category
            self.image_configs[filename]['specific'] = ''
            self.update_images_interface()
    
    def update_image_trait(self, filename, trait):
        """Actualizar trait de imagen"""
        if filename in self.image_configs:
            self.image_configs[filename]['trait'] = trait
    
    def update_image_specific(self, filename, specific):
        """Actualizar específico de imagen"""
        if filename in self.image_configs:
            self.image_configs[filename]['specific'] = specific
    
    def update_image_failure(self, filename, failure):
        """Actualizar failure de imagen"""
        if filename in self.image_configs:
            self.image_configs[filename]['failure'] = failure
    
    def preview_image(self, filename):
        """Previsualizar imagen"""
        if not self.worker_images_folder_var.get():
            messagebox.showwarning("Warning", "No images folder selected")
            return
        
        image_path = os.path.join(self.worker_images_folder_var.get(), filename)
        if not os.path.exists(image_path):
            messagebox.showerror("Error", f"Image not found: {image_path}")
            return
        
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"Preview: {filename}")
        preview_window.geometry("800x600")
        
        if not PIL_AVAILABLE:
            info_text = f"Image Preview\n\nFile: {filename}\nPath: {image_path}\n\n"
            info_text += "PIL/Pillow is not installed.\n"
            info_text += "To enable image preview, install Pillow:\n"
            info_text += "pip install Pillow"
            ttk.Label(preview_window, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)
            return
        
        try:
            # Intentar cargar imagen
            img = Image.open(image_path)
            img.thumbnail((750, 550), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(preview_window, image=photo)
            label.image = photo  # Mantener referencia
            label.pack(padx=10, pady=10)
            
            ttk.Label(preview_window, text=filename).pack(pady=5)
        except Exception as e:
            ttk.Label(preview_window, text=f"Error loading image: {str(e)}").pack(padx=10, pady=10)
    
    def select_all_images(self):
        """Seleccionar todas las imágenes"""
        for filename in self.image_configs:
            self.image_configs[filename]['selected'] = True
        self.update_images_interface()
    
    def deselect_all_images(self):
        """Deseleccionar todas las imágenes"""
        for filename in self.image_configs:
            self.image_configs[filename]['selected'] = False
        self.update_images_interface()
    
    def rename_selected_images(self):
        """Renombrar archivos seleccionados"""
        if not self.worker_images_folder_var.get():
            messagebox.showwarning("Warning", "No images folder selected")
            return
        
        selected_files = [filename for filename, config in self.image_configs.items() if config['selected']]
        
        if not selected_files:
            messagebox.showwarning("Warning", "No files selected")
            return
        
        if not messagebox.askyesno("Confirm", f"Rename {len(selected_files)} selected files?"):
            return
        
        renamed_count = 0
        errors = []
        
        for filename in selected_files:
            config = self.image_configs[filename]
            new_name = self.generate_new_filename(filename, config)
            
            if new_name and new_name != filename:
                old_path = os.path.join(self.worker_images_folder_var.get(), filename)
                new_path = os.path.join(self.worker_images_folder_var.get(), new_name)
                
                counter = 1
                base_new_path = new_path
                while os.path.exists(new_path):
                    name_parts = base_new_path.rsplit('.', 1)
                    if len(name_parts) == 2:
                        new_path = f"{name_parts[0]} ({counter}).{name_parts[1]}"
                    else:
                        new_path = f"{base_new_path} ({counter})"
                    counter += 1
                
                try:
                    if os.path.exists(old_path):
                        shutil.move(old_path, new_path)
                        renamed_count += 1
                except Exception as e:
                    errors.append(f"Error renaming {filename}: {str(e)}")
        
        # Mostrar resultados
        if renamed_count > 0:
            messagebox.showinfo("Success", f"Renamed {renamed_count} files")
            self.load_images_from_folder_path(self.worker_images_folder_var.get())
        
        if errors:
            error_text = "\n".join(errors[:10])
            if len(errors) > 10:
                error_text += f"\n... and {len(errors) - 10} more errors"
            messagebox.showerror("Errors during renaming", error_text)
    
    def generate_new_filename(self, original_filename, config):
        """Generar nuevo nombre de archivo basado en configuración"""
        extension = os.path.splitext(original_filename)[1]
        parts = []
        
        if config['trait'] != 'No trait':
            parts.append(config['trait'].lower().replace(' ', '_'))
        
        if config['specific']:
            parts.append(config['specific'].lower().replace(' ', '_'))
        
        if config['failure']:
            parts.append('failure')
        
        if not parts:
            return None
        
        new_name = '_'.join(parts) + extension
        new_name = ''.join(c for c in new_name if c.isalnum() or c in '._-')
        
        return new_name
    
    def refresh_workers_list(self):
        """Actualizar lista de workers"""
        if hasattr(self, 'workers_listbox'):
            self.workers_listbox.delete(0, tk.END)
            for worker in self.workers_data:
                name = worker.get('name', 'Unknown')
                self.workers_listbox.insert(tk.END, name)
    
    def on_worker_select(self, event):
        """Manejar selección de worker"""
        selection = self.workers_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_worker = self.workers_data[index]
            self.load_worker_data()
    
    def load_worker_data(self):
        """Cargar datos del worker seleccionado"""
        if not self.current_worker:
            return
        
        self.worker_name_var.set(self.current_worker.get('name', ''))
        self.worker_description_text.delete(1.0, tk.END)
        self.worker_description_text.insert(1.0, self.current_worker.get('description', ''))
        self.worker_folder_var.set(self.current_worker.get('folder', ''))
        self.worker_cost_var.set(self.current_worker.get('cost', 1000))
        self.worker_gender_var.set(self.current_worker.get('gender', 'female'))
        self.worker_nsfw_var.set(self.current_worker.get('nsfw', False))
        self.worker_unique_var.set(self.current_worker.get('unique', False))
        self.worker_encounter_only_var.set(self.current_worker.get('encounter_only', False))
        self.worker_monster_var.set(self.current_worker.get('monster', False))
        self.worker_procedural_var.set(self.current_worker.get('procedural', False))
        self.worker_comfort_desired_var.set(self.current_worker.get('comfort_desired', 5))
        self.worker_names_list_var.set(self.current_worker.get('names_list', 'western_female'))
        
        # Cargar skills
        skills = self.current_worker.get('skills', {})
        for skill_name, var in self.worker_skills_vars.items():
            var.set(skills.get(skill_name, 5))
        
        # Cargar traits
        self.worker_traits_listbox.delete(0, tk.END)
        traits = self.current_worker.get('traits', [])
        for trait in traits:
            self.worker_traits_listbox.insert(tk.END, trait)
        
        # Prioridad: images_folder > image_folder > folder
        images_folder = (self.current_worker.get('images_folder') or 
                        self.current_worker.get('image_folder') or 
                        self.current_worker.get('folder'))
        
        if images_folder and images_folder.strip() and self.game_directory:
            images_path = Path(self.game_directory) / "game" / "images" / "workers" / images_folder.strip()
            
            if images_path.exists():
                self.worker_images_folder_var.set(str(images_path))
                self.load_images_from_folder_path(str(images_path))
            else:
                self.worker_images_folder_var.set(str(images_path))
        else:
            self.worker_images_folder_var.set('')
    
    def save_current_worker_data(self):
        """Guardar datos del worker actual"""
        if not self.current_worker:
            return
        
        self.current_worker['name'] = self.worker_name_var.get()
        self.current_worker['description'] = self.worker_description_text.get(1.0, tk.END).strip()
        self.current_worker['folder'] = self.worker_folder_var.get()
        self.current_worker['cost'] = self.worker_cost_var.get()
        self.current_worker['gender'] = self.worker_gender_var.get()
        self.current_worker['nsfw'] = self.worker_nsfw_var.get()
        self.current_worker['unique'] = self.worker_unique_var.get()
        self.current_worker['encounter_only'] = self.worker_encounter_only_var.get()
        self.current_worker['monster'] = self.worker_monster_var.get()
        self.current_worker['procedural'] = self.worker_procedural_var.get()
        self.current_worker['comfort_desired'] = self.worker_comfort_desired_var.get()
        self.current_worker['names_list'] = self.worker_names_list_var.get()
        
        # Actualizar skills
        skills = {}
        for skill_name, var in self.worker_skills_vars.items():
            skills[skill_name] = var.get()
        self.current_worker['skills'] = skills
        
        # Actualizar traits
        traits = []
        for i in range(self.worker_traits_listbox.size()):
            traits.append(self.worker_traits_listbox.get(i))
        self.current_worker['traits'] = traits
        
        images_folder_path = self.worker_images_folder_var.get()
        if images_folder_path and images_folder_path.strip():
            folder_name = Path(images_folder_path).name
            if folder_name and folder_name.strip():
                self.current_worker['folder'] = folder_name
        self.current_worker.pop('images_folder', None)
        self.current_worker.pop('image_folder', None)
        
        self.refresh_workers_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def new_worker(self):
        """Crear nuevo worker"""
        new_worker = {
            'name': 'NewWorker',
            'folder': 'default',
            'cost': 1000,
            'nsfw': False,
            'unique': False,
            'encounter_only': False,
            'monster': False,
            'procedural': False,
            'skills': {skill: 5 for skill in self.all_skills},
            'names_list': 'western_female',
            'traits': ['Human'],
            'description': 'A new worker',
            'gender': 'female',
            'comfort_desired': 5
        }
        
        self.workers_data.append(new_worker)
        self.current_worker = new_worker
        self.refresh_workers_list()
        self.load_worker_data()
        self.has_unsaved_changes = True
        self.update_title()
    
    def new_worker_from_template(self):
        """Crear nuevo worker desde template embebido"""
        import copy
        new_worker = copy.deepcopy(EMBEDDED_WORKER_TEMPLATE)
        new_worker['name'] = 'NewWorker'
        new_worker['description'] = 'A new worker'
        new_worker['folder'] = 'default'
        new_worker['cost'] = 1000
        new_worker['gender'] = 'female'
        new_worker['traits'] = ['Human']
        new_worker['comfort_desired'] = 5
        new_worker['names_list'] = 'western_female'
        self.workers_data.append(new_worker)
        self.current_worker = new_worker
        self.refresh_workers_list()
        self.load_worker_data()
        self.has_unsaved_changes = True
        self.update_title()
        messagebox.showinfo("Success", "New worker created from template.")
    
    def duplicate_worker(self):
        """Duplicar worker actual"""
        if not self.current_worker:
            messagebox.showwarning("Warning", "No worker selected")
            return
        
        import copy
        new_worker = copy.deepcopy(self.current_worker)
        new_worker['name'] = new_worker['name'] + '_copy'
        self.workers_data.append(new_worker)
        self.refresh_workers_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def delete_worker(self):
        """Eliminar worker"""
        if not self.current_worker:
            messagebox.showwarning("Warning", "No worker selected")
            return
        
        if messagebox.askyesno("Confirm", f"Delete worker '{self.current_worker.get('name', 'Unknown')}'?"):
            if self.current_worker in self.workers_data:
                self.workers_data.remove(self.current_worker)
            self.current_worker = None
            self.refresh_workers_list()
            self.clear_worker_form()
            self.has_unsaved_changes = True
            self.update_title()
    
    def clear_worker_form(self):
        """Limpiar formulario de worker"""
        self.worker_name_var.set('')
        self.worker_description_text.delete(1.0, tk.END)
        self.worker_folder_var.set('')
        self.worker_cost_var.set(1000)
        self.worker_gender_var.set('female')
        self.worker_nsfw_var.set(False)
        self.worker_unique_var.set(False)
        self.worker_encounter_only_var.set(False)
        self.worker_monster_var.set(False)
        self.worker_procedural_var.set(False)
        self.worker_comfort_desired_var.set(5)
        self.worker_names_list_var.set('western_female')
        
        for var in self.worker_skills_vars.values():
            var.set(5)
        
        self.worker_traits_listbox.delete(0, tk.END)
    
    def add_trait_to_worker(self):
        """Agregar trait al worker"""
        if not self.traits_data:
            messagebox.showwarning("Warning", "No traits loaded")
            return
        
        trait_window = tk.Toplevel(self.root)
        trait_window.title("Select Trait")
        trait_window.geometry("400x300")
        
        ttk.Label(trait_window, text="Select a trait:").pack(pady=10)
        
        trait_listbox = tk.Listbox(trait_window)
        trait_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        trait_names = []
        if isinstance(self.traits_data, list):
            for trait in self.traits_data:
                name = trait.get('name', '')
                if name:
                    trait_names.append(name)
                    trait_listbox.insert(tk.END, name)
        
        def add_selected_trait():
            selection = trait_listbox.curselection()
            if selection:
                trait_name = trait_listbox.get(selection[0])
                self.worker_traits_listbox.insert(tk.END, trait_name)
                trait_window.destroy()
        
        ttk.Button(trait_window, text="Add", command=add_selected_trait).pack(pady=10)
        ttk.Button(trait_window, text="Cancel", command=trait_window.destroy).pack()
    
    def remove_trait_from_worker(self):
        """Quitar trait del worker"""
        selection = self.worker_traits_listbox.curselection()
        if selection:
            self.worker_traits_listbox.delete(selection[0])
    
    def load_workers_file_dialog(self):
        """Cargar archivo de workers desde diálogo"""
        initial = self.get_initial_dir("data/workers")
        
        file_path = filedialog.askopenfilename(
            title="Load Workers File",
            initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    cleaned_data = []
                    for worker in data:
                        cleaned_worker = worker.copy()
                        if cleaned_worker.get('images_folder') == '' or cleaned_worker.get('images_folder') is None:
                            cleaned_worker.pop('images_folder', None)
                        if cleaned_worker.get('image_folder') == '' or cleaned_worker.get('image_folder') is None:
                            cleaned_worker.pop('image_folder', None)
                        cleaned_data.append(cleaned_worker)
                    
                    self.workers_data = cleaned_data
                    self.current_workers_file = file_path
                    self.refresh_workers_list()
                    messagebox.showinfo("Success", f"Loaded {len(data)} workers from {Path(file_path).name}")
                else:
                    messagebox.showerror("Error", "Invalid file format. Expected a JSON array.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")
    
    def save_workers_as(self):
        """Guardar workers en archivo específico"""
        if not self.workers_data:
            messagebox.showwarning("Warning", "No workers to save")
            return
        
        # Guardar datos actuales
        if self.current_worker:
            self.save_current_worker_data()
        
        initial = self.get_initial_dir("data/workers")
        
        file_path = filedialog.asksaveasfilename(
            title="Save Workers As...",
            initialdir=initial,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if os.path.exists(file_path):
                if not messagebox.askyesno("Confirm Overwrite", 
                    f"File {Path(file_path).name} already exists.\n\nOverwrite it?"):
                    return
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.workers_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Saved {len(self.workers_data)} workers to {Path(file_path).name}")
                self.has_unsaved_changes = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def save_workers(self):
        """Guardar solo el worker actual en el archivo correcto"""
        if not self.game_directory:
            messagebox.showwarning("Warning", "Please select game directory first")
            return
        
        if not self.current_worker:
            messagebox.showwarning("Warning", "No worker selected to save")
            return
        
        self.save_current_worker_data()
        
        # Determinar el archivo de destino
        target_file = None
        
        if self.current_workers_file and Path(self.current_workers_file).exists():
            target_file = Path(self.current_workers_file)
        else:
            data_path = Path(self.game_directory) / "game" / "data" / "workers"
            is_nsfw = self.current_worker.get('nsfw', False)
            is_unique = self.current_worker.get('unique', False)
            
            if is_nsfw and is_unique:
                target_file = data_path / "workers_nsfw_unique.json"
            elif is_nsfw:
                target_file = data_path / "workers_nsfw_other.json"
            elif is_unique:
                target_file = data_path / "workers_sfw_unique.json"
            else:
                target_file = data_path / "workers_sfw_other.json"
        
        # Confirmar guardado
        response = messagebox.askyesno(
            "Save Worker",
            f"This will save the current worker '{self.current_worker.get('name', 'Unknown')}' to:\n\n"
            f"{target_file.name}\n\n"
            f"If the file exists, the worker will be updated or added.\n\n"
            f"Continue?"
        )
        
        if not response:
            return
        
        existing_workers = []
        if target_file.exists():
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_workers = existing_data
            except Exception as e:
                messagebox.showerror("Error", f"Error reading existing file:\n{str(e)}")
                return
        
        worker_name = self.current_worker.get('name', '')
        worker_updated = False
        for i, worker in enumerate(existing_workers):
            if worker.get('name') == worker_name:
                # Actualizar el worker existente
                existing_workers[i] = self.current_worker.copy()
                worker_updated = True
                break
        
        if not worker_updated:
            existing_workers.append(self.current_worker.copy())
        
        cleaned_workers = []
        for worker in existing_workers:
            cleaned_worker = worker.copy()
            if cleaned_worker.get('images_folder') == '' or cleaned_worker.get('images_folder') is None:
                cleaned_worker.pop('images_folder', None)
            if cleaned_worker.get('image_folder') == '' or cleaned_worker.get('image_folder') is None:
                cleaned_worker.pop('image_folder', None)
            cleaned_workers.append(cleaned_worker)
        
        # Guardar el archivo
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_workers, f, indent=2, ensure_ascii=False)
            
            action = "updated" if worker_updated else "added"
            messagebox.showinfo("Success", 
                f"Worker '{worker_name}' {action} in {target_file.name}\n\n"
                f"Total workers in file: {len(cleaned_workers)}")
            
            if not self.current_workers_file:
                self.current_workers_file = str(target_file)
            
            self.has_unsaved_changes = False
            self.update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def show_worker_help(self):
        """Mostrar ayuda para workers"""
        help_text = """
WORKER EDITOR HELP

Basic Information:
- Name: Worker's name
- Description: Worker description
- Folder: Image folder name (for images/workers/)
- Cost: Recruitment cost
- Gender: female or male
- NSFW: Mark if worker is NSFW content
- Unique: Mark if worker is unique (flower name)
- Encounter Only: Only available through encounters
- Monster: Mark if worker is a monster
- Procedural: Mark if worker is procedurally generated
- Comfort Desired: Desired comfort level (0-20)
- Names List: Name list to use for procedural generation

Skills:
- Set skill values from 0 to 100
- All skills are listed with spinboxes

Traits:
- Click "Add Trait" to add traits
- Select trait and click "Remove Trait" to remove

Images Tab:
- Select images folder to manage worker images
- Auto-detect configuration from filenames
- Configure category, trait, specific, and failure
- Select images and rename them automatically
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Worker Editor Help")
        help_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
    
    # ==================== TRAITS TAB ====================
    
    def setup_traits_tab(self):
        """Configurar pestaña de Traits"""
        traits_frame = ttk.Frame(self.notebook)
        self.notebook.add(traits_frame, text="Traits")
        
        main_frame = ttk.Frame(traits_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Columna izquierda - Lista de traits
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="Traits List", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Lista de traits
        self.traits_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.traits_listbox.pack(fill=tk.BOTH, expand=True)
        self.traits_listbox.bind('<<ListboxSelect>>', self.on_trait_select)
        
        # Botones de traits
        traits_buttons_frame = ttk.Frame(left_frame)
        traits_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(traits_buttons_frame, text="New Trait", command=self.new_trait).pack(fill=tk.X, pady=2)
        ttk.Button(traits_buttons_frame, text="Duplicate Trait", command=self.duplicate_trait).pack(fill=tk.X, pady=2)
        ttk.Button(traits_buttons_frame, text="Delete Trait", command=self.delete_trait).pack(fill=tk.X, pady=2)
        ttk.Separator(traits_buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(traits_buttons_frame, text="Load Traits File", command=self.load_traits_file_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(traits_buttons_frame, text="Load All Traits from Game", command=self.load_all_traits_from_game).pack(fill=tk.X, pady=2)
        ttk.Button(traits_buttons_frame, text="Add Traits from File...", command=self.add_traits_from_file).pack(fill=tk.X, pady=2)
        ttk.Button(traits_buttons_frame, text="Save Traits As...", command=self.save_traits_as).pack(fill=tk.X, pady=2)
        ttk.Button(traits_buttons_frame, text="Save Traits", command=self.save_traits).pack(fill=tk.X, pady=2)
        
        # Columna derecha - Editor de trait
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        trait_header_frame = ttk.Frame(right_frame)
        trait_header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(trait_header_frame, text="Trait Editor", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(trait_header_frame, text="? Help", command=self.show_trait_help).pack(side=tk.RIGHT)
        
        trait_canvas = tk.Canvas(right_frame)
        trait_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=trait_canvas.yview)
        trait_scrollable_frame = ttk.Frame(trait_canvas)
        
        trait_scrollable_frame.bind(
            "<Configure>",
            lambda e: trait_canvas.configure(scrollregion=trait_canvas.bbox("all"))
        )
        
        trait_canvas.create_window((0, 0), window=trait_scrollable_frame, anchor="nw")
        trait_canvas.configure(yscrollcommand=trait_scrollbar.set)
        
        trait_canvas.pack(side="left", fill="both", expand=True)
        trait_scrollbar.pack(side="right", fill="y")
        
        self.setup_trait_fields(trait_scrollable_frame)
    
    def setup_trait_fields(self, parent):
        """Configurar campos del trait"""
        row = 0
        
        # Name
        ttk.Label(parent, text="Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.trait_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.trait_name_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Description
        ttk.Label(parent, text="Description:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        self.trait_description_text = scrolledtext.ScrolledText(parent, width=50, height=4)
        self.trait_description_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # NSFW
        self.trait_nsfw_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="NSFW", variable=self.trait_nsfw_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Only Assigned
        self.trait_only_assigned_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Only Assigned (not randomly assigned)", variable=self.trait_only_assigned_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Gender Restriction
        ttk.Label(parent, text="Gender Restriction:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.trait_gender_restriction_var = tk.StringVar(value='')
        ttk.Combobox(parent, textvariable=self.trait_gender_restriction_var, values=['', 'male', 'female'], width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Removes Traits
        ttk.Label(parent, text="Removes Traits:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        removes_frame = ttk.Frame(parent)
        removes_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.trait_removes_listbox = tk.Listbox(removes_frame, height=3)
        self.trait_removes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        removes_buttons = ttk.Frame(removes_frame)
        removes_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(removes_buttons, text="Add", command=self.add_trait_removes).pack(pady=2)
        ttk.Button(removes_buttons, text="Remove", command=self.remove_trait_removes).pack(pady=2)
        row += 1
        
        # Requires Traits
        ttk.Label(parent, text="Requires Traits:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        requires_frame = ttk.Frame(parent)
        requires_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.trait_requires_listbox = tk.Listbox(requires_frame, height=3)
        self.trait_requires_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        requires_buttons = ttk.Frame(requires_frame)
        requires_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(requires_buttons, text="Add", command=self.add_trait_requires).pack(pady=2)
        ttk.Button(requires_buttons, text="Remove", command=self.remove_trait_requires).pack(pady=2)
        row += 1
        
        # Conflicts
        ttk.Label(parent, text="Conflicts:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        conflicts_frame = ttk.Frame(parent)
        conflicts_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.trait_conflicts_listbox = tk.Listbox(conflicts_frame, height=4)
        self.trait_conflicts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        conflicts_buttons = ttk.Frame(conflicts_frame)
        conflicts_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(conflicts_buttons, text="Add", command=self.add_trait_conflict).pack(pady=2)
        ttk.Button(conflicts_buttons, text="Remove", command=self.remove_trait_conflict).pack(pady=2)
        row += 1
        
        # Modifiers
        ttk.Label(parent, text="Modifiers", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        # Earnings Multiplier
        ttk.Label(parent, text="Earnings Multiplier:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.trait_earnings_mult_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(parent, from_=0.1, to=5.0, increment=0.05, textvariable=self.trait_earnings_mult_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Skill Modifiers
        ttk.Label(parent, text="Skill Modifiers:", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5))
        row += 1
        
        skill_mods_frame = ttk.Frame(parent)
        skill_mods_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.trait_skill_mods_listbox = tk.Listbox(skill_mods_frame, height=4)
        self.trait_skill_mods_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        skill_mods_buttons = ttk.Frame(skill_mods_frame)
        skill_mods_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(skill_mods_buttons, text="Add", command=self.add_trait_skill_mod).pack(pady=2)
        ttk.Button(skill_mods_buttons, text="Remove", command=self.remove_trait_skill_mod).pack(pady=2)
        row += 1
        
        # Extended Modifiers (caps, regeneration, secondary attrs)
        ttk.Label(parent, text="Extended Modifiers:", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        row += 1
        
        ext_frame = ttk.Frame(parent)
        ext_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        # Row 1: Libido
        ttk.Label(ext_frame, text="libido_max:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        self.trait_mod_libido_max_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-20, to=50, textvariable=self.trait_mod_libido_max_var, width=8).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(ext_frame, text="libido_regeneration:").grid(row=0, column=2, sticky="w", padx=(20, 5), pady=2)
        self.trait_mod_libido_regen_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-5, to=10, textvariable=self.trait_mod_libido_regen_var, width=8).grid(row=0, column=3, padx=5, pady=2)
        # Row 2: Health
        ttk.Label(ext_frame, text="health:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        self.trait_mod_health_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-20, to=50, textvariable=self.trait_mod_health_var, width=8).grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(ext_frame, text="health_max:").grid(row=1, column=2, sticky="w", padx=(20, 5), pady=2)
        self.trait_mod_health_max_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-20, to=50, textvariable=self.trait_mod_health_max_var, width=8).grid(row=1, column=3, padx=5, pady=2)
        ttk.Label(ext_frame, text="health_max_cap:").grid(row=1, column=4, sticky="w", padx=(20, 5), pady=2)
        self.trait_mod_health_max_cap_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=0, to=200, textvariable=self.trait_mod_health_max_cap_var, width=8).grid(row=1, column=5, padx=5, pady=2)
        # Row 3: Energy
        ttk.Label(ext_frame, text="energy:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=2)
        self.trait_mod_energy_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-20, to=50, textvariable=self.trait_mod_energy_var, width=8).grid(row=2, column=1, padx=5, pady=2)
        ttk.Label(ext_frame, text="energy_max:").grid(row=2, column=2, sticky="w", padx=(20, 5), pady=2)
        self.trait_mod_energy_max_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-20, to=50, textvariable=self.trait_mod_energy_max_var, width=8).grid(row=2, column=3, padx=5, pady=2)
        ttk.Label(ext_frame, text="energy_max_cap:").grid(row=2, column=4, sticky="w", padx=(20, 5), pady=2)
        self.trait_mod_energy_max_cap_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=0, to=200, textvariable=self.trait_mod_energy_max_cap_var, width=8).grid(row=2, column=5, padx=5, pady=2)
        # Row 4: Regeneration
        ttk.Label(ext_frame, text="health_regeneration:").grid(row=3, column=0, sticky="w", padx=(0, 5), pady=2)
        self.trait_mod_health_regen_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-5, to=10, textvariable=self.trait_mod_health_regen_var, width=8).grid(row=3, column=1, padx=5, pady=2)
        ttk.Label(ext_frame, text="energy_regeneration:").grid(row=3, column=2, sticky="w", padx=(20, 5), pady=2)
        self.trait_mod_energy_regen_var = tk.IntVar(value=0)
        ttk.Spinbox(ext_frame, from_=-5, to=20, textvariable=self.trait_mod_energy_regen_var, width=8).grid(row=3, column=3, padx=5, pady=2)
        # Row 5-6: Secondary attrs (joy, romance, relationship, comfort_level, comfort_desired, libido)
        ttk.Label(ext_frame, text="Secondary attr deltas (joy, romance, relationship, etc.):").grid(row=4, column=0, columnspan=6, sticky="w", padx=(0, 5), pady=(10, 2))
        sec_attrs = [("joy", "trait_mod_joy"), ("romance", "trait_mod_romance"), ("relationship", "trait_mod_relationship"),
                     ("comfort_level", "trait_mod_comfort_level"), ("comfort_desired", "trait_mod_comfort_desired"), ("libido", "trait_mod_libido")]
        for i, (attr_name, var_attr) in enumerate(sec_attrs):
            ttk.Label(ext_frame, text=f"{attr_name}:").grid(row=5 + i // 3, column=(i % 3) * 2, sticky="w", padx=(0 if i % 3 == 0 else 15, 5), pady=2)
            v = tk.IntVar(value=0)
            setattr(self, var_attr + "_var", v)
            ttk.Spinbox(ext_frame, from_=-50, to=50, textvariable=v, width=6).grid(row=5 + i // 3, column=(i % 3) * 2 + 1, padx=5, pady=2)
        row += 1
        
        # Attribute Caps (top-level)
        ttk.Label(parent, text="Attribute Caps:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        ttk.Label(parent, text="(e.g. joy: 80, rebelliousness: 50)", font=("Arial", 8)).grid(row=row, column=0, columnspan=2, sticky="w", padx=15)
        row += 1
        caps_frame = ttk.Frame(parent)
        caps_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.trait_attr_caps_listbox = tk.Listbox(caps_frame, height=3)
        self.trait_attr_caps_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        caps_buttons = ttk.Frame(caps_frame)
        caps_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(caps_buttons, text="Add", command=self.add_trait_attr_cap).pack(pady=2)
        ttk.Button(caps_buttons, text="Remove", command=self.remove_trait_attr_cap).pack(pady=2)
        row += 1
        
        # Attribute Minimums (top-level)
        ttk.Label(parent, text="Attribute Minimums:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        mins_frame = ttk.Frame(parent)
        mins_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.trait_attr_mins_listbox = tk.Listbox(mins_frame, height=3)
        self.trait_attr_mins_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        mins_buttons = ttk.Frame(mins_frame)
        mins_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(mins_buttons, text="Add", command=self.add_trait_attr_min).pack(pady=2)
        ttk.Button(mins_buttons, text="Remove", command=self.remove_trait_attr_min).pack(pady=2)
        
        parent.columnconfigure(1, weight=1)
    
    def refresh_traits_list(self):
        """Actualizar lista de traits"""
        if hasattr(self, 'traits_listbox'):
            self.traits_listbox.delete(0, tk.END)
            if isinstance(self.traits_data, list):
                for trait in self.traits_data:
                    name = trait.get('name', 'Unknown')
                    self.traits_listbox.insert(tk.END, name)
        
        # Update item trait comboboxes with loaded traits
        self.update_item_trait_combos()
    
    def update_item_trait_combos(self):
        """Update trait comboboxes in Items editor with loaded traits"""
        trait_names = []
        if isinstance(self.traits_data, list):
            trait_names = sorted([trait.get('name', '') for trait in self.traits_data if trait.get('name', '')])
        
        # Update add trait combobox if it exists
        if hasattr(self, 'item_add_trait_combo'):
            self.item_add_trait_combo['values'] = trait_names
        
        # Update remove trait combobox if it exists
        if hasattr(self, 'item_remove_trait_combo'):
            self.item_remove_trait_combo['values'] = trait_names
    
    def on_trait_select(self, event):
        """Manejar selección de trait"""
        selection = self.traits_listbox.curselection()
        if selection and isinstance(self.traits_data, list):
            index = selection[0]
            self.current_trait = self.traits_data[index]
            self.load_trait_data()
    
    def load_trait_data(self):
        """Cargar datos del trait seleccionado"""
        if not self.current_trait:
            return
        
        self.trait_name_var.set(self.current_trait.get('name', ''))
        self.trait_description_text.delete(1.0, tk.END)
        self.trait_description_text.insert(1.0, self.current_trait.get('description', ''))
        self.trait_nsfw_var.set(self.current_trait.get('nsfw', False))
        self.trait_only_assigned_var.set(self.current_trait.get('only_assigned', False))
        self.trait_gender_restriction_var.set(self.current_trait.get('gender_restriction') or '')
        
        # Cargar removes_traits
        if hasattr(self, 'trait_removes_listbox'):
            self.trait_removes_listbox.delete(0, tk.END)
            for t in self.current_trait.get('removes_traits', []):
                self.trait_removes_listbox.insert(tk.END, t)
        
        # Cargar requires_traits
        if hasattr(self, 'trait_requires_listbox'):
            self.trait_requires_listbox.delete(0, tk.END)
            req = self.current_trait.get('requires_traits', [])
            if isinstance(req, str):
                req = [req] if req else []
            for t in req:
                self.trait_requires_listbox.insert(tk.END, t)
        
        # Cargar conflicts
        self.trait_conflicts_listbox.delete(0, tk.END)
        for conflict in self.current_trait.get('conflicts', []):
            self.trait_conflicts_listbox.insert(tk.END, conflict)
        
        # Cargar modifiers
        modifiers = self.current_trait.get('modifiers', {})
        self.trait_earnings_mult_var.set(modifiers.get('earnings_multiplier', 1.0))
        
        # Cargar skill modifiers
        self.trait_skill_mods_listbox.delete(0, tk.END)
        skill_mods = modifiers.get('skill_modifiers', {})
        for skill, value in skill_mods.items():
            self.trait_skill_mods_listbox.insert(tk.END, f"{skill}: {value}")
        
        # Cargar extended modifiers
        if hasattr(self, 'trait_mod_libido_max_var'):
            self.trait_mod_libido_max_var.set(modifiers.get('libido_max', 0))
            self.trait_mod_libido_regen_var.set(modifiers.get('libido_regeneration', 0))
            self.trait_mod_health_var.set(modifiers.get('health', 0))
            self.trait_mod_health_max_var.set(modifiers.get('health_max', 0))
            cap = modifiers.get('health_max_cap', 0)
            self.trait_mod_health_max_cap_var.set(cap if isinstance(cap, (int, float)) and cap > 0 else 0)
            self.trait_mod_energy_var.set(modifiers.get('energy', 0))
            self.trait_mod_energy_max_var.set(modifiers.get('energy_max', 0))
            ecap = modifiers.get('energy_max_cap', 0)
            self.trait_mod_energy_max_cap_var.set(ecap if isinstance(ecap, (int, float)) and ecap > 0 else 0)
            self.trait_mod_health_regen_var.set(modifiers.get('health_regeneration', 0))
            self.trait_mod_energy_regen_var.set(modifiers.get('energy_regeneration', 0))
            for attr_name, var_attr in [("joy", "trait_mod_joy"), ("romance", "trait_mod_romance"), ("relationship", "trait_mod_relationship"),
                                        ("comfort_level", "trait_mod_comfort_level"), ("comfort_desired", "trait_mod_comfort_desired"), ("libido", "trait_mod_libido")]:
                v = getattr(self, var_attr + "_var", None)
                if v is not None:
                    v.set(modifiers.get(attr_name, 0))
        
        # Cargar attribute_caps (top-level)
        if hasattr(self, 'trait_attr_caps_listbox'):
            self.trait_attr_caps_listbox.delete(0, tk.END)
            caps = self.current_trait.get('attribute_caps', {})
            for attr, val in caps.items():
                self.trait_attr_caps_listbox.insert(tk.END, f"{attr}: {val}")
        
        # Cargar attribute_minimums (top-level)
        if hasattr(self, 'trait_attr_mins_listbox'):
            self.trait_attr_mins_listbox.delete(0, tk.END)
            mins = self.current_trait.get('attribute_minimums', {})
            for attr, val in mins.items():
                self.trait_attr_mins_listbox.insert(tk.END, f"{attr}: {val}")
    
    def new_trait(self):
        """Crear nuevo trait"""
        new_trait = {
            'name': 'NewTrait',
            'description': 'A new trait',
            'nsfw': False,
            'only_assigned': False,
            'conflicts': [],
            'removes_traits': [],
            'modifiers': {}
        }
        
        if not isinstance(self.traits_data, list):
            self.traits_data = []
        
        self.traits_data.append(new_trait)
        self.current_trait = new_trait
        self.refresh_traits_list()
        self.load_trait_data()
        self.has_unsaved_changes = True
        self.update_title()
    
    def duplicate_trait(self):
        """Duplicar trait actual"""
        if not self.current_trait:
            messagebox.showwarning("Warning", "No trait selected")
            return
        
        import copy
        new_trait = copy.deepcopy(self.current_trait)
        new_trait['name'] = new_trait['name'] + '_copy'
        if isinstance(self.traits_data, list):
            self.traits_data.append(new_trait)
        self.refresh_traits_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def delete_trait(self):
        """Eliminar trait"""
        if not self.current_trait:
            messagebox.showwarning("Warning", "No trait selected")
            return
        
        if messagebox.askyesno("Confirm", f"Delete trait '{self.current_trait.get('name', 'Unknown')}'?"):
            if isinstance(self.traits_data, list) and self.current_trait in self.traits_data:
                self.traits_data.remove(self.current_trait)
            self.current_trait = None
            self.refresh_traits_list()
            self.has_unsaved_changes = True
            self.update_title()
    
    def add_trait_conflict(self):
        """Agregar conflicto al trait"""
        conflict = simpledialog.askstring("Add Conflict", "Enter trait name that conflicts:")
        if conflict:
            self.trait_conflicts_listbox.insert(tk.END, conflict)
    
    def remove_trait_conflict(self):
        """Quitar conflicto del trait"""
        selection = self.trait_conflicts_listbox.curselection()
        if selection:
            self.trait_conflicts_listbox.delete(selection[0])
    
    def add_trait_removes(self):
        trait = simpledialog.askstring("Add Removes Trait", "Enter trait name to remove when this is added:")
        if trait:
            self.trait_removes_listbox.insert(tk.END, trait)
    
    def remove_trait_removes(self):
        selection = self.trait_removes_listbox.curselection()
        if selection:
            self.trait_removes_listbox.delete(selection[0])
    
    def add_trait_requires(self):
        trait = simpledialog.askstring("Add Requires Trait", "Enter trait name worker must have:")
        if trait:
            self.trait_requires_listbox.insert(tk.END, trait)
    
    def remove_trait_requires(self):
        selection = self.trait_requires_listbox.curselection()
        if selection:
            self.trait_requires_listbox.delete(selection[0])
    
    def add_trait_attr_cap(self):
        cap_window = tk.Toplevel(self.root)
        cap_window.title("Add Attribute Cap")
        cap_window.geometry("300x120")
        attrs = ["joy", "rebelliousness", "romance", "relationship", "libido", "comfort_desired", "comfort_level"]
        ttk.Label(cap_window, text="Attribute:").grid(row=0, column=0, padx=5, pady=5)
        attr_var = tk.StringVar()
        ttk.Combobox(cap_window, textvariable=attr_var, values=attrs, width=20).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(cap_window, text="Cap value (0-100):").grid(row=1, column=0, padx=5, pady=5)
        val_var = tk.IntVar(value=100)
        ttk.Spinbox(cap_window, from_=0, to=100, textvariable=val_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        def do_add():
            a, v = attr_var.get().strip(), val_var.get()
            if a:
                self.trait_attr_caps_listbox.insert(tk.END, f"{a}: {v}")
            cap_window.destroy()
        ttk.Button(cap_window, text="Add", command=do_add).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(cap_window, text="Cancel", command=cap_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def remove_trait_attr_cap(self):
        selection = self.trait_attr_caps_listbox.curselection()
        if selection:
            self.trait_attr_caps_listbox.delete(selection[0])
    
    def add_trait_attr_min(self):
        min_window = tk.Toplevel(self.root)
        min_window.title("Add Attribute Minimum")
        min_window.geometry("300x120")
        attrs = ["joy", "rebelliousness", "romance", "relationship", "libido", "comfort_desired", "comfort_level"]
        ttk.Label(min_window, text="Attribute:").grid(row=0, column=0, padx=5, pady=5)
        attr_var = tk.StringVar()
        ttk.Combobox(min_window, textvariable=attr_var, values=attrs, width=20).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(min_window, text="Minimum value (0-100):").grid(row=1, column=0, padx=5, pady=5)
        val_var = tk.IntVar(value=0)
        ttk.Spinbox(min_window, from_=0, to=100, textvariable=val_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        def do_add():
            a, v = attr_var.get().strip(), val_var.get()
            if a:
                self.trait_attr_mins_listbox.insert(tk.END, f"{a}: {v}")
            min_window.destroy()
        ttk.Button(min_window, text="Add", command=do_add).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(min_window, text="Cancel", command=min_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def remove_trait_attr_min(self):
        selection = self.trait_attr_mins_listbox.curselection()
        if selection:
            self.trait_attr_mins_listbox.delete(selection[0])
    
    def add_trait_skill_mod(self):
        """Agregar modificador de skill al trait"""
        mod_window = tk.Toplevel(self.root)
        mod_window.title("Add Skill Modifier")
        mod_window.geometry("300x150")
        
        ttk.Label(mod_window, text="Skill:").grid(row=0, column=0, padx=5, pady=5)
        skill_var = tk.StringVar()
        ttk.Combobox(mod_window, textvariable=skill_var, values=self.all_skills, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(mod_window, text="Value:").grid(row=1, column=0, padx=5, pady=5)
        value_var = tk.IntVar(value=1)
        ttk.Spinbox(mod_window, from_=-10, to=10, textvariable=value_var).grid(row=1, column=1, padx=5, pady=5)
        
        def add_mod():
            skill = skill_var.get()
            value = value_var.get()
            if skill:
                self.trait_skill_mods_listbox.insert(tk.END, f"{skill}: {value}")
            mod_window.destroy()
        
        ttk.Button(mod_window, text="Add", command=add_mod).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(mod_window, text="Cancel", command=mod_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def remove_trait_skill_mod(self):
        """Quitar modificador de skill del trait"""
        selection = self.trait_skill_mods_listbox.curselection()
        if selection:
            self.trait_skill_mods_listbox.delete(selection[0])
    
    def save_current_trait_data(self):
        """Guardar datos del trait actual"""
        if not self.current_trait:
            return
        
        self.current_trait['name'] = self.trait_name_var.get()
        self.current_trait['description'] = self.trait_description_text.get(1.0, tk.END).strip()
        self.current_trait['nsfw'] = self.trait_nsfw_var.get()
        only_assigned = self.trait_only_assigned_var.get()
        if only_assigned:
            self.current_trait['only_assigned'] = True
        else:
            self.current_trait.pop('only_assigned', None)  # Remove if False
        
        gr = self.trait_gender_restriction_var.get().strip()
        if gr in ('male', 'female'):
            self.current_trait['gender_restriction'] = gr
        else:
            self.current_trait.pop('gender_restriction', None)
        
        # Guardar removes_traits
        if hasattr(self, 'trait_removes_listbox'):
            self.current_trait['removes_traits'] = [self.trait_removes_listbox.get(i) for i in range(self.trait_removes_listbox.size())]
        
        # Guardar requires_traits
        if hasattr(self, 'trait_requires_listbox'):
            self.current_trait['requires_traits'] = [self.trait_requires_listbox.get(i) for i in range(self.trait_requires_listbox.size())]
        
        # Guardar attribute_caps (top-level)
        if hasattr(self, 'trait_attr_caps_listbox'):
            caps = {}
            for i in range(self.trait_attr_caps_listbox.size()):
                text = self.trait_attr_caps_listbox.get(i)
                if ':' in text:
                    attr, val = text.split(':', 1)
                    caps[attr.strip()] = int(val.strip())
            if caps:
                self.current_trait['attribute_caps'] = caps
            else:
                self.current_trait.pop('attribute_caps', None)
        
        # Guardar attribute_minimums (top-level)
        if hasattr(self, 'trait_attr_mins_listbox'):
            mins = {}
            for i in range(self.trait_attr_mins_listbox.size()):
                text = self.trait_attr_mins_listbox.get(i)
                if ':' in text:
                    attr, val = text.split(':', 1)
                    mins[attr.strip()] = int(val.strip())
            if mins:
                self.current_trait['attribute_minimums'] = mins
            else:
                self.current_trait.pop('attribute_minimums', None)
        
        # Guardar conflicts
        conflicts = []
        for i in range(self.trait_conflicts_listbox.size()):
            conflicts.append(self.trait_conflicts_listbox.get(i))
        self.current_trait['conflicts'] = conflicts
        
        modifiers = dict(self.current_trait.get('modifiers', {}))
        modifiers['earnings_multiplier'] = self.trait_earnings_mult_var.get()
        
        # Guardar skill modifiers
        skill_mods = {}
        for i in range(self.trait_skill_mods_listbox.size()):
            text = self.trait_skill_mods_listbox.get(i)
            if ':' in text:
                skill, value = text.split(':', 1)
                skill_mods[skill.strip()] = int(value.strip())
        if skill_mods:
            modifiers['skill_modifiers'] = skill_mods
        
        if hasattr(self, 'trait_mod_libido_max_var'):
            ext_keys = [
                ('libido_max', self.trait_mod_libido_max_var),
                ('libido_regeneration', self.trait_mod_libido_regen_var),
                ('health', self.trait_mod_health_var),
                ('health_max', self.trait_mod_health_max_var),
                ('health_max_cap', self.trait_mod_health_max_cap_var),
                ('energy', self.trait_mod_energy_var),
                ('energy_max', self.trait_mod_energy_max_var),
                ('energy_max_cap', self.trait_mod_energy_max_cap_var),
                ('health_regeneration', self.trait_mod_health_regen_var),
                ('energy_regeneration', self.trait_mod_energy_regen_var),
                ('joy', self.trait_mod_joy_var),
                ('romance', self.trait_mod_romance_var),
                ('relationship', self.trait_mod_relationship_var),
                ('comfort_level', self.trait_mod_comfort_level_var),
                ('comfort_desired', self.trait_mod_comfort_desired_var),
                ('libido', self.trait_mod_libido_var),
            ]
            for key, var in ext_keys:
                val = var.get()
                if val != 0:
                    modifiers[key] = val
                else:
                    modifiers.pop(key, None)
        
        self.current_trait['modifiers'] = modifiers
        self.refresh_traits_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def _extract_traits_from_json(self, data):
        """Extract trait list from JSON (array or {'traits': [...]})."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'traits' in data:
            return data['traits'] if isinstance(data['traits'], list) else []
        return []
    
    def load_traits_file_dialog(self):
        """Cargar archivo de traits desde diálogo (reemplaza todos)"""
        initial = self.get_initial_dir("data")
        
        file_path = filedialog.askopenfilename(
            title="Load Traits File",
            initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                traits = self._extract_traits_from_json(data)
                if traits:
                    self.traits_data = traits
                    self.refresh_traits_list()
                    messagebox.showinfo("Success", f"Loaded {len(traits)} traits from {Path(file_path).name}")
                else:
                    messagebox.showerror("Error", "No traits found. Expected a JSON array or object with 'traits' key.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")
    
    def load_all_traits_from_game(self):
        """Cargar y fusionar todos los traits de data/traits/*.json y data/traits.json"""
        if not self.game_directory:
            messagebox.showwarning("Warning", "Select game directory first")
            return
        
        data_path = Path(self.game_directory) / "game" / "data"
        traits_dir = data_path / "traits"
        traits_json = data_path / "traits.json"
        
        files_to_load = []
        if traits_dir.exists():
            for f in sorted(traits_dir.glob("*.json")):
                files_to_load.append(f)
        if traits_json.exists():
            files_to_load.insert(0, traits_json)
        
        if not files_to_load:
            messagebox.showwarning("No files", "No trait files found in data/traits/ or data/traits.json")
            return
        
        seen_names = set()
        merged = list(self.traits_data) if isinstance(self.traits_data, list) else []
        for t in merged:
            n = t.get("name")
            if n:
                seen_names.add(n)
        
        total_added = 0
        for fp in files_to_load:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for t in self._extract_traits_from_json(data):
                    if isinstance(t, dict) and t.get("name"):
                        if t["name"] not in seen_names:
                            seen_names.add(t["name"])
                            merged.append(t)
                            total_added += 1
            except Exception as e:
                messagebox.showwarning("Load warning", f"Could not load {fp.name}: {e}")
        
        self.traits_data = merged
        self.refresh_traits_list()
        messagebox.showinfo("Success", f"Loaded all traits. Added {total_added} from {len(files_to_load)} file(s). Total: {len(merged)}")
    
    def add_traits_from_file(self):
        """Fusionar traits de un archivo con la lista actual (sin duplicados)"""
        initial = self.get_initial_dir("data")
        file_path = filedialog.askopenfilename(
            title="Add Traits from File",
            initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            new_traits = self._extract_traits_from_json(data)
            if not new_traits:
                messagebox.showwarning("No traits", "No traits found in file")
                return
            
            base = list(self.traits_data) if isinstance(self.traits_data, list) else []
            seen = {t.get("name") for t in base if t.get("name")}
            added = 0
            for t in new_traits:
                if isinstance(t, dict) and t.get("name") and t["name"] not in seen:
                    seen.add(t["name"])
                    base.append(t)
                    added += 1
            
            self.traits_data = base
            self.refresh_traits_list()
            messagebox.showinfo("Success", f"Added {added} traits from {Path(file_path).name}. Total: {len(base)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading file:\n{str(e)}")
    
    def save_traits_as(self):
        """Guardar traits en archivo específico"""
        if not isinstance(self.traits_data, list) or not self.traits_data:
            messagebox.showwarning("Warning", "No traits to save")
            return
        
        if self.current_trait:
            self.save_current_trait_data()
        
        initial = self.get_initial_dir("data")
        
        file_path = filedialog.asksaveasfilename(
            title="Save Traits As...",
            initialdir=initial,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if os.path.exists(file_path):
                if not messagebox.askyesno("Confirm Overwrite", f"File {Path(file_path).name} already exists.\n\nOverwrite it?"):
                    return
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.traits_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Saved {len(self.traits_data)} traits to {Path(file_path).name}")
                self.has_unsaved_changes = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def save_traits(self):
        """Guardar traits (con confirmación)"""
        if not isinstance(self.traits_data, list) or not self.traits_data:
            messagebox.showwarning("Warning", "No traits to save")
            return
        
        if self.current_trait:
            self.save_current_trait_data()
        
        if not self.game_directory:
            messagebox.showwarning("Warning", "Please select game directory first")
            return
        
        if not messagebox.askyesno("Confirm", f"Save {len(self.traits_data)} traits to traits.json?\n\nThis will overwrite the existing file."):
            return
        
        data_path = Path(self.game_directory) / "game" / "data" / "traits.json"
        
        try:
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(self.traits_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Saved {len(self.traits_data)} traits")
            self.has_unsaved_changes = False
            self.update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def show_trait_help(self):
        """Mostrar ayuda para traits"""
        help_text = """
TRAIT EDITOR HELP

Basic Information:
- Name: Trait name (must be unique)
- Description: Trait description
- NSFW: Mark if trait is NSFW content
- Only Assigned: Trait is not randomly assigned to workers
- Gender Restriction: Empty, male, or female (limits assignment)

Removes Traits:
- Traits that are removed when this trait is added to a worker

Requires Traits:
- Traits the worker must already have to receive this trait

Conflicts:
- Traits that conflict with this trait
- Workers cannot have conflicting traits at the same time

Attribute Caps (top-level):
- Caps on secondary attributes: joy, rebelliousness, romance, relationship,
  libido, comfort_desired, comfort_level (0-100)
- Example: joy: 80 limits joy to 80

Attribute Minimums (top-level):
- Minimum values for secondary attributes (0-100)

Modifiers:
- Earnings Multiplier: Multiplies worker earnings (1.0 = no change)
- Skill Modifiers: Adds/subtracts skill values
- Extended Modifiers:
  libido_max, libido_regeneration: Max libido bonus and daily regen
  health, health_max, health_max_cap: Health bonuses and cap
  energy, energy_max, energy_max_cap: Energy bonuses and cap
  health_regeneration, energy_regeneration: Daily regen bonuses
  Secondary attr deltas: joy, romance, relationship, comfort_level,
  comfort_desired, libido - flat deltas applied when trait is added

Note: Unknown modifier keys (e.g. daily_effects) are preserved when saving.
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Trait Editor Help")
        help_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
    
    # ==================== ITEMS TAB ====================
    
    def setup_items_tab(self):
        """Configurar pestaña de Items"""
        items_frame = ttk.Frame(self.notebook)
        self.notebook.add(items_frame, text="Items")
        
        main_frame = ttk.Frame(items_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="Items List", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        self.items_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.items_listbox.pack(fill=tk.BOTH, expand=True)
        self.items_listbox.bind('<<ListboxSelect>>', self.on_item_select)
        
        items_buttons_frame = ttk.Frame(left_frame)
        items_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(items_buttons_frame, text="Load Items File", command=self.load_items_file_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(items_buttons_frame, text="Save Items As...", command=self.save_items_as).pack(fill=tk.X, pady=2)
        ttk.Button(items_buttons_frame, text="Save Items", command=self.save_items).pack(fill=tk.X, pady=2)
        ttk.Separator(items_buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(items_buttons_frame, text="New Item", command=self.new_item).pack(fill=tk.X, pady=2)
        ttk.Button(items_buttons_frame, text="New from Template", command=self.new_item_from_template).pack(fill=tk.X, pady=2)
        ttk.Button(items_buttons_frame, text="Duplicate Item", command=self.duplicate_item).pack(fill=tk.X, pady=2)
        ttk.Button(items_buttons_frame, text="Delete Item", command=self.delete_item).pack(fill=tk.X, pady=2)
        ttk.Button(items_buttons_frame, text="Save Current Item", command=self.save_current_item_data).pack(fill=tk.X, pady=2)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        item_header_frame = ttk.Frame(right_frame)
        item_header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(item_header_frame, text="Item Editor", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(item_header_frame, text="? Help", command=self.show_item_help).pack(side=tk.RIGHT)
        
        item_canvas = tk.Canvas(right_frame)
        item_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=item_canvas.yview)
        item_scrollable_frame = ttk.Frame(item_canvas)
        
        item_scrollable_frame.bind("<Configure>", lambda e: item_canvas.configure(scrollregion=item_canvas.bbox("all")))
        item_canvas.create_window((0, 0), window=item_scrollable_frame, anchor="nw")
        item_canvas.configure(yscrollcommand=item_scrollbar.set)
        
        item_canvas.pack(side="left", fill="both", expand=True)
        item_scrollbar.pack(side="right", fill="y")
        
        self.setup_item_fields(item_scrollable_frame)
    
    def setup_item_fields(self, parent):
        """Configurar campos del item"""
        row = 0
        
        ttk.Label(parent, text="ID:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.item_id_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.item_id_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.item_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.item_name_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Display Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.item_display_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.item_display_name_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Type:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.item_type_var = tk.StringVar(value="consumable")
        ttk.Combobox(parent, textvariable=self.item_type_var, 
                    values=["weapon", "consumable", "armor", "accessory", "quest_item", "currency", "clothing"],
                    state="readonly", width=47).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Description:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        self.item_description_text = scrolledtext.ScrolledText(parent, width=50, height=4)
        self.item_description_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Price:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.item_price_var = tk.IntVar(value=0)
        ttk.Spinbox(parent, from_=0, to=999999, textvariable=self.item_price_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Weight:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.item_weight_var = tk.IntVar(value=0)
        ttk.Spinbox(parent, from_=0, to=999, textvariable=self.item_weight_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Durability:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.item_durability_var = tk.IntVar(value=0)
        ttk.Spinbox(parent, from_=0, to=999, textvariable=self.item_durability_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        self.item_shop_available_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Shop Available", variable=self.item_shop_available_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Effects Section
        ttk.Label(parent, text="Effects", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        # Stats (health, energy, libido)
        stats_frame = ttk.LabelFrame(parent, text="Stats")
        stats_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(stats_frame, text="Health:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.item_effect_health_var = tk.IntVar(value=0)
        ttk.Spinbox(stats_frame, from_=-100, to=100, textvariable=self.item_effect_health_var, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Energy:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.item_effect_energy_var = tk.IntVar(value=0)
        ttk.Spinbox(stats_frame, from_=-100, to=100, textvariable=self.item_effect_energy_var, width=10).grid(row=0, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(stats_frame, text="Libido:").grid(row=0, column=4, sticky="w", padx=5, pady=2)
        self.item_effect_libido_var = tk.IntVar(value=0)
        ttk.Spinbox(stats_frame, from_=-100, to=100, textvariable=self.item_effect_libido_var, width=10).grid(row=0, column=5, sticky="w", padx=5, pady=2)
        row += 1
        
        # Skill Modifiers
        skill_mods_frame = ttk.LabelFrame(parent, text="Skill Modifiers")
        skill_mods_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.item_skill_mods_listbox = tk.Listbox(skill_mods_frame, height=4)
        self.item_skill_mods_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        skill_mods_buttons = ttk.Frame(skill_mods_frame)
        skill_mods_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(skill_mods_buttons, text="Add", command=self.add_item_skill_mod).pack(pady=2)
        ttk.Button(skill_mods_buttons, text="Remove", command=self.remove_item_skill_mod).pack(pady=2)
        row += 1
        
        # Traits
        traits_frame = ttk.LabelFrame(parent, text="Traits")
        traits_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Add Traits
        ttk.Label(traits_frame, text="Add Traits (select from loaded traits):").pack(anchor="w", padx=5, pady=(5, 2))
        self.item_add_traits_listbox = tk.Listbox(traits_frame, height=3)
        self.item_add_traits_listbox.pack(fill=tk.X, padx=5, pady=2)
        add_trait_buttons = ttk.Frame(traits_frame)
        add_trait_buttons.pack(fill=tk.X, padx=5, pady=2)
        self.item_add_trait_var = tk.StringVar()
        self.item_add_trait_combo = ttk.Combobox(add_trait_buttons, textvariable=self.item_add_trait_var, width=25, state="readonly")
        self.item_add_trait_combo.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(add_trait_buttons, text="Add", command=self.add_item_trait).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(add_trait_buttons, text="Remove", command=self.remove_item_add_trait).pack(side=tk.LEFT)
        
        # Remove Traits
        ttk.Label(traits_frame, text="Remove Traits (select from loaded traits):").pack(anchor="w", padx=5, pady=(10, 2))
        self.item_remove_traits_listbox = tk.Listbox(traits_frame, height=3)
        self.item_remove_traits_listbox.pack(fill=tk.X, padx=5, pady=2)
        remove_trait_buttons = ttk.Frame(traits_frame)
        remove_trait_buttons.pack(fill=tk.X, padx=5, pady=2)
        self.item_remove_trait_var = tk.StringVar()
        self.item_remove_trait_combo = ttk.Combobox(remove_trait_buttons, textvariable=self.item_remove_trait_var, width=25, state="readonly")
        self.item_remove_trait_combo.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(remove_trait_buttons, text="Add", command=self.add_item_remove_trait).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(remove_trait_buttons, text="Remove", command=self.remove_item_remove_trait).pack(side=tk.LEFT)
        row += 1
        
        # Custom Action
        custom_frame = ttk.LabelFrame(parent, text="Custom Action")
        custom_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(custom_frame, text="Custom:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.item_effect_custom_var = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.item_effect_custom_var, width=40).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        custom_frame.columnconfigure(1, weight=1)
        
        parent.columnconfigure(1, weight=1)
    
    def refresh_items_list(self):
        """Actualizar lista de items"""
        if hasattr(self, 'items_listbox'):
            self.items_listbox.delete(0, tk.END)
            if isinstance(self.items_data, dict) and 'items' in self.items_data:
                for item in self.items_data['items']:
                    name = item.get('name', item.get('id', 'Unknown'))
                    self.items_listbox.insert(tk.END, name)
    
    def on_item_select(self, event):
        """Manejar selección de item"""
        selection = self.items_listbox.curselection()
        if selection and isinstance(self.items_data, dict) and 'items' in self.items_data:
            index = selection[0]
            self.current_item = self.items_data['items'][index]
            self.load_item_data()
    
    def load_item_data(self):
        """Cargar datos del item seleccionado"""
        if not self.current_item:
            return
        
        self.item_id_var.set(self.current_item.get('id', ''))
        self.item_name_var.set(self.current_item.get('name', ''))
        self.item_display_name_var.set(self.current_item.get('display_name', ''))
        self.item_type_var.set(self.current_item.get('type', 'consumable'))
        self.item_description_text.delete(1.0, tk.END)
        self.item_description_text.insert(1.0, self.current_item.get('description', ''))
        self.item_price_var.set(self.current_item.get('price', 0))
        self.item_weight_var.set(self.current_item.get('weight', 0))
        self.item_durability_var.set(self.current_item.get('durability', 0))
        self.item_shop_available_var.set(self.current_item.get('shop_available', True))
        
        # Cargar efectos
        effect = self.current_item.get('effect', {})
        self.item_effect_health_var.set(effect.get('health', 0))
        self.item_effect_energy_var.set(effect.get('energy', 0))
        self.item_effect_libido_var.set(effect.get('libido', 0))
        self.item_effect_custom_var.set(effect.get('custom', ''))
        
        # Cargar skill modifiers
        self.item_skill_mods_listbox.delete(0, tk.END)
        skill_mods = effect.get('skill_modifiers', {})
        for skill, value in skill_mods.items():
            self.item_skill_mods_listbox.insert(tk.END, f"{skill}: {value}")
        
        # Cargar traits
        self.item_add_traits_listbox.delete(0, tk.END)
        add_trait = effect.get('add_trait', '')
        if isinstance(add_trait, list):
            for trait in add_trait:
                trait_name = trait.get("name", "") if isinstance(trait, dict) else trait
                if trait_name:
                    self.item_add_traits_listbox.insert(tk.END, trait_name)
        elif isinstance(add_trait, dict):
            trait_name = add_trait.get("name", "")
            if trait_name:
                self.item_add_traits_listbox.insert(tk.END, trait_name)
        elif add_trait:
            self.item_add_traits_listbox.insert(tk.END, add_trait)
        
        self.item_remove_traits_listbox.delete(0, tk.END)
        remove_trait = effect.get('remove_trait', '')
        if isinstance(remove_trait, list):
            for trait in remove_trait:
                trait_name = trait.get("name", "") if isinstance(trait, dict) else trait
                if trait_name:
                    self.item_remove_traits_listbox.insert(tk.END, trait_name)
        elif isinstance(remove_trait, dict):
            trait_name = remove_trait.get("name", "")
            if trait_name:
                self.item_remove_traits_listbox.insert(tk.END, trait_name)
        elif remove_trait:
            self.item_remove_traits_listbox.insert(tk.END, remove_trait)
    
    def add_item_skill_mod(self):
        """Agregar modificador de skill al item"""
        mod_window = tk.Toplevel(self.root)
        mod_window.title("Add Skill Modifier")
        mod_window.geometry("300x150")
        
        ttk.Label(mod_window, text="Skill:").grid(row=0, column=0, padx=5, pady=5)
        skill_var = tk.StringVar()
        ttk.Combobox(mod_window, textvariable=skill_var, values=self.all_skills, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(mod_window, text="Value:").grid(row=1, column=0, padx=5, pady=5)
        value_var = tk.IntVar(value=1)
        ttk.Spinbox(mod_window, from_=-20, to=20, textvariable=value_var).grid(row=1, column=1, padx=5, pady=5)
        
        def add_mod():
            skill = skill_var.get()
            value = value_var.get()
            if skill:
                self.item_skill_mods_listbox.insert(tk.END, f"{skill}: {value}")
            mod_window.destroy()
        
        ttk.Button(mod_window, text="Add", command=add_mod).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(mod_window, text="Cancel", command=mod_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def remove_item_skill_mod(self):
        """Quitar modificador de skill del item"""
        selection = self.item_skill_mods_listbox.curselection()
        if selection:
            self.item_skill_mods_listbox.delete(selection[0])
    
    def add_item_trait(self):
        """Agregar trait al item"""
        trait = self.item_add_trait_var.get().strip()
        if trait:
            self.item_add_traits_listbox.insert(tk.END, trait)
            self.item_add_trait_var.set('')
    
    def remove_item_add_trait(self):
        """Quitar trait de add traits"""
        selection = self.item_add_traits_listbox.curselection()
        if selection:
            self.item_add_traits_listbox.delete(selection[0])
    
    def add_item_remove_trait(self):
        """Agregar trait a remover del item"""
        trait = self.item_remove_trait_var.get().strip()
        if trait:
            self.item_remove_traits_listbox.insert(tk.END, trait)
            self.item_remove_trait_var.set('')
    
    def remove_item_remove_trait(self):
        """Quitar trait de remove traits"""
        selection = self.item_remove_traits_listbox.curselection()
        if selection:
            self.item_remove_traits_listbox.delete(selection[0])
    
    def new_item(self):
        """Crear nuevo item"""
        new_item = {
            'id': 'new_item',
            'name': 'New Item',
            'display_name': 'New Item',
            'type': 'consumable',
            'description': 'A new item',
            'price': 0,
            'weight': 0,
            'shop_available': True
        }
        
        if not isinstance(self.items_data, dict):
            self.items_data = {'items': [], 'excluded_from_shops': []}
        if 'items' not in self.items_data:
            self.items_data['items'] = []
        
        self.items_data['items'].append(new_item)
        self.current_item = new_item
        self.refresh_items_list()
        self.load_item_data()
        self.has_unsaved_changes = True
        self.update_title()
    
    def new_item_from_template(self):
        """Crear nuevo item desde template embebido"""
        import copy
        new_item = copy.deepcopy(EMBEDDED_ITEM_TEMPLATE)
        new_item['id'] = 'new_item'
        new_item['name'] = 'New Item'
        new_item['display_name'] = 'New Item'
        new_item['type'] = 'consumable'
        new_item['description'] = 'A new item'
        if not isinstance(self.items_data, dict):
            self.items_data = {'items': [], 'excluded_from_shops': []}
        if 'items' not in self.items_data:
            self.items_data['items'] = []
        self.items_data['items'].append(new_item)
        self.current_item = new_item
        self.refresh_items_list()
        self.load_item_data()
        self.has_unsaved_changes = True
        self.update_title()
        messagebox.showinfo("Success", "New item created from template.")
    
    def duplicate_item(self):
        """Duplicar item actual"""
        if not self.current_item:
            messagebox.showwarning("Warning", "No item selected")
            return
        
        import copy
        new_item = copy.deepcopy(self.current_item)
        new_item['id'] = new_item.get('id', 'item') + '_copy'
        new_item['name'] = new_item.get('name', 'Item') + ' Copy'
        if isinstance(self.items_data, dict) and 'items' in self.items_data:
            self.items_data['items'].append(new_item)
        self.refresh_items_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def delete_item(self):
        """Eliminar item"""
        if not self.current_item:
            messagebox.showwarning("Warning", "No item selected")
            return
        
        if messagebox.askyesno("Confirm", f"Delete item '{self.current_item.get('name', 'Unknown')}'?"):
            if isinstance(self.items_data, dict) and 'items' in self.items_data:
                if self.current_item in self.items_data['items']:
                    self.items_data['items'].remove(self.current_item)
            self.current_item = None
            self.refresh_items_list()
            self.has_unsaved_changes = True
            self.update_title()
    
    def save_current_item_data(self):
        """Guardar datos del item actual"""
        if not self.current_item:
            return
        
        self.current_item['id'] = self.item_id_var.get()
        self.current_item['name'] = self.item_name_var.get()
        self.current_item['display_name'] = self.item_display_name_var.get()
        self.current_item['type'] = self.item_type_var.get()
        self.current_item['description'] = self.item_description_text.get(1.0, tk.END).strip()
        self.current_item['price'] = self.item_price_var.get()
        self.current_item['weight'] = self.item_weight_var.get()
        durability = self.item_durability_var.get()
        if durability > 0:
            self.current_item['durability'] = durability
        self.current_item['shop_available'] = self.item_shop_available_var.get()
        
        # Guardar efectos
        effect = {}
        
        # Stats
        health = self.item_effect_health_var.get()
        energy = self.item_effect_energy_var.get()
        libido = self.item_effect_libido_var.get()
        if health != 0:
            effect['health'] = health
        if energy != 0:
            effect['energy'] = energy
        if libido != 0:
            effect['libido'] = libido
        
        # Skill modifiers
        skill_mods = {}
        for i in range(self.item_skill_mods_listbox.size()):
            text = self.item_skill_mods_listbox.get(i)
            if ':' in text:
                skill, value = text.split(':', 1)
                skill_mods[skill.strip()] = int(value.strip())
        if skill_mods:
            effect['skill_modifiers'] = skill_mods
        
        # Traits
        add_traits = []
        for i in range(self.item_add_traits_listbox.size()):
            add_traits.append(self.item_add_traits_listbox.get(i))
        if add_traits:
            # Always save as array for consistency (game code now supports both)
            effect['add_trait'] = add_traits
        
        remove_traits = []
        for i in range(self.item_remove_traits_listbox.size()):
            remove_traits.append(self.item_remove_traits_listbox.get(i))
        if remove_traits:
            # Always save as array for consistency (game code now supports both)
            effect['remove_trait'] = remove_traits
        
        # Custom action
        custom = self.item_effect_custom_var.get().strip()
        if custom:
            effect['custom'] = custom
        
        if effect:
            self.current_item['effect'] = effect
        elif 'effect' in self.current_item:
            del self.current_item['effect']
        
        self.refresh_items_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def show_item_help(self):
        """Mostrar ayuda para items"""
        help_text = """
ITEM EDITOR HELP

Basic Information:
- ID: Unique item identifier
- Name: Internal item name
- Display Name: Name shown to players
- Type: Item type (weapon, consumable, accessory, quest_item, etc.)
- Description: Item description text
- Price: Item price in shops
- Weight: Item weight
- Durability: Item durability (for weapons/armor)
- Shop Available: Whether item appears in shops

Effects:
- Health/Energy/Libido: Direct stat modifications
- Skill Modifiers: Skill bonuses/penalties
- Add Traits: Select traits from loaded traits.json to add when item is equipped
  (use the dropdown selector to avoid typos, traits are saved as array)
- Remove Traits: Select traits to remove when item is equipped
  (useful for items that cure negative traits)
- Custom: Custom action identifier for special effects

Note: Make sure to load traits.json first (File > Load Traits) to populate
the trait selectors with available traits from your game data.
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Item Editor Help")
        help_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def load_items_file_dialog(self):
        """Cargar archivo de items desde diálogo"""
        initial = self.get_initial_dir("data/items")
        
        file_path = filedialog.askopenfilename(
            title="Load Items File",
            initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'items' in data:
                    self.items_data = data
                    self.refresh_items_list()
                    messagebox.showinfo("Success", f"Loaded {len(data['items'])} items from {Path(file_path).name}")
                elif isinstance(data, list):
                    self.items_data = {'items': data, 'excluded_from_shops': []}
                    self.refresh_items_list()
                    messagebox.showinfo("Success", f"Loaded {len(data)} items from {Path(file_path).name}")
                else:
                    messagebox.showerror("Error", "Invalid file format.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")
    
    def save_items_as(self):
        """Guardar items en archivo específico"""
        if not isinstance(self.items_data, dict) or 'items' not in self.items_data or not self.items_data['items']:
            messagebox.showwarning("Warning", "No items to save")
            return
        
        if self.current_item:
            self.save_current_item_data()
        
        initial = self.get_initial_dir("data/items")
        
        file_path = filedialog.asksaveasfilename(
            title="Save Items As...",
            initialdir=initial,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if os.path.exists(file_path):
                if not messagebox.askyesno("Confirm Overwrite", f"File {Path(file_path).name} already exists.\n\nOverwrite it?"):
                    return
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.items_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Saved {len(self.items_data['items'])} items to {Path(file_path).name}")
                self.has_unsaved_changes = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def save_items(self):
        """Guardar items (con confirmación)"""
        if not isinstance(self.items_data, dict) or 'items' not in self.items_data or not self.items_data['items']:
            messagebox.showwarning("Warning", "No items to save")
            return
        
        if self.current_item:
            self.save_current_item_data()
        
        if not self.game_directory:
            messagebox.showwarning("Warning", "Please select game directory first")
            return
        
        if not messagebox.askyesno("Confirm", f"Save {len(self.items_data['items'])} items to items.json?\n\nThis will overwrite the existing file."):
            return
        
        data_path = Path(self.game_directory) / "game" / "data" / "items" / "items.json"
        
        try:
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(self.items_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Saved {len(self.items_data['items'])} items")
            self.has_unsaved_changes = False
            self.update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    # ==================== BUILDINGS TAB ====================
    
    def setup_buildings_tab(self):
        """Configurar pestaña de Buildings"""
        buildings_frame = ttk.Frame(self.notebook)
        self.notebook.add(buildings_frame, text="Buildings")
        
        main_frame = ttk.Frame(buildings_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="Buildings List", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        self.buildings_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.buildings_listbox.pack(fill=tk.BOTH, expand=True)
        self.buildings_listbox.bind('<<ListboxSelect>>', self.on_building_select)
        
        buildings_buttons_frame = ttk.Frame(left_frame)
        buildings_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buildings_buttons_frame, text="Load Buildings File", command=self.load_buildings_file_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(buildings_buttons_frame, text="Save Buildings As...", command=self.save_buildings_as).pack(fill=tk.X, pady=2)
        ttk.Button(buildings_buttons_frame, text="Save Buildings", command=self.save_buildings).pack(fill=tk.X, pady=2)
        ttk.Separator(buildings_buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(buildings_buttons_frame, text="New Building", command=self.new_building).pack(fill=tk.X, pady=2)
        ttk.Button(buildings_buttons_frame, text="Save Current Building", command=self.save_current_building_data).pack(fill=tk.X, pady=2)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        building_header_frame = ttk.Frame(right_frame)
        building_header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(building_header_frame, text="Building Editor", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(building_header_frame, text="? Help", command=self.show_building_help).pack(side=tk.RIGHT)
        
        self.building_notebook = ttk.Notebook(right_frame)
        self.building_notebook.pack(fill=tk.BOTH, expand=True)
        
        basic_building_frame = ttk.Frame(self.building_notebook)
        self.building_notebook.add(basic_building_frame, text="Basic Information")
        
        building_canvas = tk.Canvas(basic_building_frame)
        building_scrollbar = ttk.Scrollbar(basic_building_frame, orient="vertical", command=building_canvas.yview)
        building_scrollable_frame = ttk.Frame(building_canvas)
        
        building_scrollable_frame.bind("<Configure>", lambda e: building_canvas.configure(scrollregion=building_canvas.bbox("all")))
        building_canvas.create_window((0, 0), window=building_scrollable_frame, anchor="nw")
        building_canvas.configure(yscrollcommand=building_scrollbar.set)
        
        building_canvas.pack(side="left", fill="both", expand=True)
        building_scrollbar.pack(side="right", fill="y")
        
        self.setup_building_basic_fields(building_scrollable_frame)
        
        professions_building_frame = ttk.Frame(self.building_notebook)
        self.building_notebook.add(professions_building_frame, text="Professions")
        self.setup_building_professions_tab(professions_building_frame)
    
    def refresh_buildings_list(self):
        """Actualizar lista de buildings"""
        if hasattr(self, 'buildings_listbox'):
            self.buildings_listbox.delete(0, tk.END)
            if isinstance(self.buildings_data, list):
                for building in self.buildings_data:
                    name = building.get('name', building.get('id', 'Unknown'))
                    self.buildings_listbox.insert(tk.END, name)
    
    def on_building_select(self, event):
        """Manejar selección de building"""
        selection = self.buildings_listbox.curselection()
        if selection and isinstance(self.buildings_data, list):
            index = selection[0]
            self.current_building = self.buildings_data[index]
            self.load_building_data()
    
    def setup_building_basic_fields(self, parent):
        """Configurar campos básicos del building"""
        row = 0
        
        # ID
        ttk.Label(parent, text="ID:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.building_id_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.building_id_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Name
        ttk.Label(parent, text="Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.building_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.building_name_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Skill Name
        ttk.Label(parent, text="Skill Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.building_skill_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.building_skill_name_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        ttk.Label(parent, text="Name of the skill workers train here (e.g. Hag Potions, Academy Training)", font=("Arial", 8)).grid(row=row, column=0, columnspan=2, sticky="w", padx=15)
        row += 1
        
        # Skill Description
        ttk.Label(parent, text="Skill Description:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        self.building_skill_description_text = scrolledtext.ScrolledText(parent, width=50, height=3)
        self.building_skill_description_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        ttk.Label(parent, text="Flavor text explaining what this skill does and how it's used in the game", font=("Arial", 8)).grid(row=row, column=0, columnspan=2, sticky="w", padx=15)
        row += 1
        
        # NSFW
        self.building_nsfw_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="NSFW", variable=self.building_nsfw_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Allowed Map Locations
        ttk.Label(parent, text="Allowed Map Locations:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        locations_frame = ttk.Frame(parent)
        locations_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.building_locations_listbox = tk.Listbox(locations_frame, height=4)
        self.building_locations_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        locations_buttons = ttk.Frame(locations_frame)
        locations_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(locations_buttons, text="Add", command=self.add_building_location).pack(pady=2)
        ttk.Button(locations_buttons, text="Add from list", command=self.add_building_location_from_list).pack(pady=2)
        ttk.Button(locations_buttons, text="Remove", command=self.remove_building_location).pack(pady=2)
        
        parent.columnconfigure(1, weight=1)
    
    def setup_building_professions_tab(self, parent):
        """Configurar pestaña de professions del building"""
        prof_notebook = ttk.Notebook(parent)
        prof_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        prof_list_frame = ttk.Frame(prof_notebook)
        prof_notebook.add(prof_list_frame, text="Professions List")
        
        ttk.Label(prof_list_frame, text="Available Professions:").pack(anchor="w", padx=5, pady=5)
        self.building_professions_listbox = tk.Listbox(prof_list_frame, height=15)
        self.building_professions_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.building_professions_listbox.bind('<<ListboxSelect>>', self.on_profession_select)
        
        prof_buttons_frame = ttk.Frame(prof_list_frame)
        prof_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(prof_buttons_frame, text="New Profession", command=self.add_profession).pack(side=tk.LEFT, padx=5)
        ttk.Button(prof_buttons_frame, text="Delete Profession", command=self.remove_profession).pack(side=tk.LEFT, padx=5)
        
        prof_edit_frame = ttk.Frame(prof_notebook)
        prof_notebook.add(prof_edit_frame, text="Profession Editor")
        
        prof_edit_canvas = tk.Canvas(prof_edit_frame)
        prof_edit_scrollbar = ttk.Scrollbar(prof_edit_frame, orient="vertical", command=prof_edit_canvas.yview)
        prof_edit_scrollable = ttk.Frame(prof_edit_canvas)
        
        prof_edit_scrollable.bind("<Configure>", lambda e: prof_edit_canvas.configure(scrollregion=prof_edit_canvas.bbox("all")))
        prof_edit_canvas.create_window((0, 0), window=prof_edit_scrollable, anchor="nw")
        prof_edit_canvas.configure(yscrollcommand=prof_edit_scrollbar.set)
        
        prof_edit_canvas.pack(side="left", fill="both", expand=True)
        prof_edit_scrollbar.pack(side="right", fill="y")
        
        self.setup_profession_editor(prof_edit_scrollable)
    
    def setup_profession_editor(self, parent):
        """Configurar editor de profession"""
        row = 0
        
        # Name
        ttk.Label(parent, text="Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.prof_name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prof_name_var, width=40).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # ID
        ttk.Label(parent, text="ID:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.prof_id_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.prof_id_var, width=40).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # NSFW
        self.prof_nsfw_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="NSFW", variable=self.prof_nsfw_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Difficulty
        ttk.Label(parent, text="Difficulty:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.prof_difficulty_var = tk.StringVar(value="medium")
        ttk.Combobox(parent, textvariable=self.prof_difficulty_var, values=["easy", "medium", "hard"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Max Daily Workers
        ttk.Label(parent, text="Max Daily Workers:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.prof_max_workers_var = tk.IntVar(value=3)
        ttk.Spinbox(parent, from_=1, to=20, textvariable=self.prof_max_workers_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Daily Story Count
        ttk.Label(parent, text="Daily Story Count", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        ttk.Label(parent, text="Base:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.prof_story_base_var = tk.IntVar(value=3)
        ttk.Spinbox(parent, from_=0, to=20, textvariable=self.prof_story_base_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        ttk.Label(parent, text="Bonus Formula:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.prof_story_bonus_var = tk.StringVar(value="reputation / 100")
        ttk.Entry(parent, textvariable=self.prof_story_bonus_var, width=40).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Skills
        ttk.Label(parent, text="Skills", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        skills_frame = ttk.Frame(parent)
        skills_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.prof_skills_listbox = tk.Listbox(skills_frame, height=6)
        self.prof_skills_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        skills_buttons = ttk.Frame(skills_frame)
        skills_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(skills_buttons, text="Add", command=self.add_profession_skill).pack(pady=2)
        ttk.Button(skills_buttons, text="Remove", command=self.remove_profession_skill).pack(pady=2)
        row += 1
        
        # Daily Stories
        ttk.Label(parent, text="Daily Stories", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        stories_frame = ttk.Frame(parent)
        stories_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.prof_stories_listbox = tk.Listbox(stories_frame, height=8)
        self.prof_stories_listbox.pack(fill=tk.X, pady=5)
        self.prof_stories_listbox.bind('<<ListboxSelect>>', self.on_daily_story_select)
        
        stories_buttons_frame = ttk.Frame(stories_frame)
        stories_buttons_frame.pack(fill=tk.X)
        ttk.Button(stories_buttons_frame, text="New Story", command=self.add_daily_story).pack(side=tk.LEFT, padx=5)
        ttk.Button(stories_buttons_frame, text="Edit Story", command=self.edit_daily_story).pack(side=tk.LEFT, padx=5)
        ttk.Button(stories_buttons_frame, text="Remove Story", command=self.remove_daily_story).pack(side=tk.LEFT, padx=5)
        
        parent.columnconfigure(1, weight=1)
    
    def load_building_data(self):
        """Cargar datos del building seleccionado"""
        if not self.current_building:
            return
        
        self.building_id_var.set(self.current_building.get('id', ''))
        self.building_name_var.set(self.current_building.get('name', ''))
        self.building_skill_name_var.set(self.current_building.get('skill_name', ''))
        self.building_skill_description_text.delete(1.0, tk.END)
        self.building_skill_description_text.insert(1.0, self.current_building.get('skill_description', ''))
        self.building_nsfw_var.set(self.current_building.get('nsfw', False))
        
        # Cargar locations
        self.building_locations_listbox.delete(0, tk.END)
        for location in self.current_building.get('allowed_map_locations', []):
            self.building_locations_listbox.insert(tk.END, location)
        
        # Limpiar profession actual al cambiar de building
        self.current_profession = None
        self.current_profession_index = None
        
        # Cargar professions y auto-seleccionar la primera
        self.refresh_professions_list()
        professions = self.current_building.get('professions', [])
        if professions and hasattr(self, 'building_professions_listbox'):
            self.building_professions_listbox.selection_clear(0, tk.END)
            self.building_professions_listbox.selection_set(0)
            self.current_profession = professions[0]
            self.current_profession_index = 0
            self.load_profession_data()
    
    def refresh_professions_list(self):
        """Actualizar lista de professions"""
        if hasattr(self, 'building_professions_listbox'):
            self.building_professions_listbox.delete(0, tk.END)
            if self.current_building:
                professions = self.current_building.get('professions', [])
                for prof in professions:
                    name = prof.get('name', prof.get('id', 'Unknown'))
                    self.building_professions_listbox.insert(tk.END, name)
    
    def on_profession_select(self, event):
        """Manejar selección de profession"""
        selection = self.building_professions_listbox.curselection()
        if selection and self.current_building:
            index = selection[0]
            professions = self.current_building.get('professions', [])
            if index < len(professions):
                self.current_profession = professions[index]
                self.current_profession_index = index
                self.load_profession_data()
    
    def load_profession_data(self):
        """Cargar datos de la profession seleccionada"""
        if not self.current_profession:
            return
        
        self.prof_name_var.set(self.current_profession.get('name', ''))
        self.prof_id_var.set(self.current_profession.get('id', ''))
        self.prof_nsfw_var.set(self.current_profession.get('nsfw', False))
        self.prof_difficulty_var.set(self.current_profession.get('difficulty', 'medium'))
        self.prof_max_workers_var.set(self.current_profession.get('max_daily_workers', 3))
        
        # Daily story count
        story_count = self.current_profession.get('daily_story_count', {})
        self.prof_story_base_var.set(story_count.get('base', 3))
        self.prof_story_bonus_var.set(story_count.get('bonus_formula', 'reputation / 100'))
        
        # Skills
        self.prof_skills_listbox.delete(0, tk.END)
        for skill in self.current_profession.get('skills', []):
            self.prof_skills_listbox.insert(tk.END, skill)
        
        # Daily stories
        self.refresh_daily_stories_list()
    
    def refresh_daily_stories_list(self):
        """Actualizar lista de daily stories"""
        if hasattr(self, 'prof_stories_listbox'):
            self.prof_stories_listbox.delete(0, tk.END)
            if self.current_profession:
                stories = self.current_profession.get('daily_stories', [])
                for story in stories:
                    story_id = story.get('id', 'Unknown')
                    self.prof_stories_listbox.insert(tk.END, story_id)
    
    def on_daily_story_select(self, event):
        """Manejar selección de daily story"""
        selection = self.prof_stories_listbox.curselection()
        if selection and self.current_profession:
            index = selection[0]
            stories = self.current_profession.get('daily_stories', [])
            if index < len(stories):
                self.open_daily_story_editor(stories[index], index)
    
    def _get_known_map_locations(self):
        """Extraer locations únicas de building_types.json y special_buildings.json."""
        locations = set()
        if not self.game_directory:
            return sorted(locations)
        data_path = Path(self.game_directory) / "game" / "data" / "buildings"
        for fname in ("building_types.json", "special_buildings.json"):
            p = data_path / fname
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for b in data.get("building_types", []):
                        for loc in b.get("allowed_map_locations", []):
                            if loc:
                                locations.add(loc)
                except Exception:
                    pass
        return sorted(locations)
    
    def add_building_location(self):
        """Agregar location al building (escribir manualmente)"""
        location = simpledialog.askstring("Add Location", "Enter map location:")
        if location and location.strip():
            self.building_locations_listbox.insert(tk.END, location.strip())
    
    def add_building_location_from_list(self):
        """Agregar location desde lista de locations conocidas del juego"""
        known = self._get_known_map_locations()
        loc_window = tk.Toplevel(self.root)
        loc_window.title("Add Map Location")
        loc_window.geometry("350x120")
        ttk.Label(loc_window, text="Select or type location:").pack(pady=5)
        loc_var = tk.StringVar()
        if known:
            combo = ttk.Combobox(loc_window, textvariable=loc_var, values=known, width=40)
            combo.pack(pady=5, padx=10, fill=tk.X)
            combo.current(0) if known else None
        else:
            ttk.Label(loc_window, text="(No game dir or no locations found. Use 'Add' to type manually.)").pack(pady=2)
            ttk.Entry(loc_window, textvariable=loc_var, width=40).pack(pady=5, padx=10, fill=tk.X)
        
        def do_add():
            loc = loc_var.get().strip()
            if loc:
                self.building_locations_listbox.insert(tk.END, loc)
            loc_window.destroy()
        
        ttk.Button(loc_window, text="Add", command=do_add).pack(pady=5)
        ttk.Button(loc_window, text="Cancel", command=loc_window.destroy).pack(pady=2)
    
    def remove_building_location(self):
        """Quitar location del building"""
        selection = self.building_locations_listbox.curselection()
        if selection:
            self.building_locations_listbox.delete(selection[0])
    
    def add_profession(self):
        """Agregar nueva profession"""
        if not self.current_building:
            messagebox.showwarning("Warning", "No building selected")
            return
        
        new_prof = {
            'id': 'new_profession',
            'name': 'New Profession',
            'nsfw': False,
            'difficulty': 'medium',
            'skills': [],
            'max_daily_workers': 3,
            'daily_story_count': {'base': 3, 'bonus_formula': 'reputation / 100'},
            'daily_stories': []
        }
        
        if 'professions' not in self.current_building:
            self.current_building['professions'] = []
        
        self.current_building['professions'].append(new_prof)
        self.refresh_professions_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def remove_profession(self):
        """Eliminar profession"""
        selection = self.building_professions_listbox.curselection()
        if selection and self.current_building:
            index = selection[0]
            professions = self.current_building.get('professions', [])
            if index < len(professions):
                if messagebox.askyesno("Confirm", f"Delete profession '{professions[index].get('name', 'Unknown')}'?"):
                    professions.pop(index)
                    self.refresh_professions_list()
                    self.current_profession = None
                    self.has_unsaved_changes = True
                    self.update_title()
    
    def save_current_profession(self):
        """Guardar profession actual"""
        if not self.current_profession:
            return
        
        self.current_profession['name'] = self.prof_name_var.get()
        self.current_profession['id'] = self.prof_id_var.get()
        self.current_profession['nsfw'] = self.prof_nsfw_var.get()
        self.current_profession['difficulty'] = self.prof_difficulty_var.get()
        self.current_profession['max_daily_workers'] = self.prof_max_workers_var.get()
        
        # Daily story count
        self.current_profession['daily_story_count'] = {
            'base': self.prof_story_base_var.get(),
            'bonus_formula': self.prof_story_bonus_var.get()
        }
        
        # Skills
        skills = []
        for i in range(self.prof_skills_listbox.size()):
            skills.append(self.prof_skills_listbox.get(i))
        self.current_profession['skills'] = skills
        
        self.refresh_professions_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def add_profession_skill(self):
        """Agregar skill a profession"""
        skill_window = tk.Toplevel(self.root)
        skill_window.title("Add Skill")
        skill_window.geometry("300x100")
        
        ttk.Label(skill_window, text="Skill:").grid(row=0, column=0, padx=5, pady=5)
        skill_var = tk.StringVar()
        ttk.Combobox(skill_window, textvariable=skill_var, values=self.all_skills, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        def add_skill():
            skill = skill_var.get()
            if skill:
                self.prof_skills_listbox.insert(tk.END, skill)
            skill_window.destroy()
        
        ttk.Button(skill_window, text="Add", command=add_skill).grid(row=1, column=0, padx=5, pady=10)
        ttk.Button(skill_window, text="Cancel", command=skill_window.destroy).grid(row=1, column=1, padx=5, pady=10)
    
    def remove_profession_skill(self):
        """Quitar skill de profession"""
        selection = self.prof_skills_listbox.curselection()
        if selection:
            self.prof_skills_listbox.delete(selection[0])
    
    def add_daily_story(self):
        """Agregar nueva daily story desde template embebido"""
        if not self.current_profession:
            messagebox.showwarning("Warning", "No profession selected")
            return
        
        import copy
        new_story = copy.deepcopy(EMBEDDED_DAILY_STORY_TEMPLATE)
        new_story['id'] = 'new_story'
        new_story['report'] = 'New story'
        new_story['weight'] = 1
        
        if 'daily_stories' not in self.current_profession:
            self.current_profession['daily_stories'] = []
        
        self.current_profession['daily_stories'].append(new_story)
        self.refresh_daily_stories_list()
        self.open_daily_story_editor(new_story, len(self.current_profession['daily_stories']) - 1)
        self.has_unsaved_changes = True
        self.update_title()
    
    def edit_daily_story(self):
        """Editar daily story seleccionada"""
        selection = self.prof_stories_listbox.curselection()
        if selection and self.current_profession:
            index = selection[0]
            stories = self.current_profession.get('daily_stories', [])
            if index < len(stories):
                self.open_daily_story_editor(stories[index], index)
    
    def remove_daily_story(self):
        """Eliminar daily story"""
        selection = self.prof_stories_listbox.curselection()
        if selection and self.current_profession:
            index = selection[0]
            stories = self.current_profession.get('daily_stories', [])
            if index < len(stories):
                if messagebox.askyesno("Confirm", f"Delete story '{stories[index].get('id', 'Unknown')}'?"):
                    stories.pop(index)
                    self.refresh_daily_stories_list()
                    self.has_unsaved_changes = True
                    self.update_title()
    
    def open_daily_story_editor(self, story, index):
        """Abrir editor de daily story - Version completa con todas las pestañas"""
        editor_window = tk.Toplevel(self.root)
        editor_window.title(f"Edit Daily Story: {story.get('id', 'Unknown')}")
        editor_window.geometry("1000x800")
        
        story_notebook = ttk.Notebook(editor_window)
        story_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        basic_story_frame = ttk.Frame(story_notebook)
        story_notebook.add(basic_story_frame, text="Basic")
        
        basic_canvas = tk.Canvas(basic_story_frame)
        basic_scrollbar = ttk.Scrollbar(basic_story_frame, orient="vertical", command=basic_canvas.yview)
        basic_scrollable = ttk.Frame(basic_canvas)
        basic_scrollable.bind("<Configure>", lambda e: basic_canvas.configure(scrollregion=basic_canvas.bbox("all")))
        basic_canvas.create_window((0, 0), window=basic_scrollable, anchor="nw")
        basic_canvas.configure(yscrollcommand=basic_scrollbar.set)
        basic_canvas.pack(side="left", fill="both", expand=True)
        basic_scrollbar.pack(side="right", fill="y")
        
        row = 0
        ttk.Label(basic_scrollable, text="ID:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_id_var = tk.StringVar(value=story.get('id', ''))
        ttk.Entry(basic_scrollable, textvariable=story_id_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Report:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_report_var = tk.StringVar(value=story.get('report', ''))
        ttk.Entry(basic_scrollable, textvariable=story_report_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Weight (frequency):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_weight_var = tk.DoubleVar(value=story.get('weight', 1))
        ttk.Spinbox(basic_scrollable, from_=0.1, to=10, increment=0.1, textvariable=story_weight_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Difficulty Modifier:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_diff_mod_var = tk.IntVar(value=story.get('difficulty_modifier', 0))
        ttk.Spinbox(basic_scrollable, from_=-20, to=20, textvariable=story_diff_mod_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Worker Gender Requirement:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_worker_gender_var = tk.StringVar(value=story.get('worker_gender_requirement') or '')
        ttk.Combobox(basic_scrollable, textvariable=story_worker_gender_var, values=['', 'male', 'female'], width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        story_nsfw_only_var = tk.BooleanVar(value=story.get('nsfw_only', False))
        ttk.Checkbutton(basic_scrollable, text="NSFW Only (show only when NSFW mode enabled)", variable=story_nsfw_only_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Images
        ttk.Label(basic_scrollable, text="Story Image:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_image_var = tk.StringVar(value=story.get('story_image', ''))
        ttk.Entry(basic_scrollable, textvariable=story_image_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Failure Image:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        failure_image_var = tk.StringVar(value=story.get('failure_image', ''))
        ttk.Entry(basic_scrollable, textvariable=failure_image_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Skill Options
        ttk.Label(basic_scrollable, text="Skill Options:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        skill_options_frame = ttk.Frame(basic_scrollable)
        skill_options_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        story_skill_options_listbox = tk.Listbox(skill_options_frame, height=4)
        story_skill_options_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        for skill in story.get('skill_options', []):
            story_skill_options_listbox.insert(tk.END, skill)
        
        skill_options_buttons = ttk.Frame(skill_options_frame)
        skill_options_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(skill_options_buttons, text="Add", command=lambda: self.add_story_skill_option(story_skill_options_listbox)).pack(pady=2)
        ttk.Button(skill_options_buttons, text="Remove", command=lambda: story_skill_options_listbox.delete(tk.ANCHOR)).pack(pady=2)
        row += 1
        
        basic_scrollable.columnconfigure(1, weight=1)
        
        traits_story_frame = ttk.Frame(story_notebook)
        story_notebook.add(traits_story_frame, text="Traits")
        
        traits_canvas = tk.Canvas(traits_story_frame)
        traits_scrollbar = ttk.Scrollbar(traits_story_frame, orient="vertical", command=traits_canvas.yview)
        traits_scrollable = ttk.Frame(traits_canvas)
        traits_scrollable.bind("<Configure>", lambda e: traits_canvas.configure(scrollregion=traits_canvas.bbox("all")))
        traits_canvas.create_window((0, 0), window=traits_scrollable, anchor="nw")
        traits_canvas.configure(yscrollcommand=traits_scrollbar.set)
        traits_canvas.pack(side="left", fill="both", expand=True)
        traits_scrollbar.pack(side="right", fill="y")
        
        row = 0
        ttk.Label(traits_scrollable, text="Trait Roll Modifiers (trait → +/- to d100 roll):", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        row += 1
        
        trait_roll_frame = ttk.Frame(traits_scrollable)
        trait_roll_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        story_trait_roll_listbox = tk.Listbox(trait_roll_frame, height=5)
        story_trait_roll_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        for tname, tval in story.get('trait_roll_modifiers', {}).items():
            story_trait_roll_listbox.insert(tk.END, f"{tname}: {tval:+d}")
        
        def add_trait_roll():
            wnd = tk.Toplevel(editor_window)
            wnd.title("Add Trait Roll Modifier")
            ttk.Label(wnd, text="Trait:").grid(row=0, column=0, padx=5, pady=5)
            tvar = tk.StringVar()
            ttk.Entry(wnd, textvariable=tvar, width=25).grid(row=0, column=1, padx=5, pady=5)
            ttk.Label(wnd, text="Modifier (+/-):").grid(row=1, column=0, padx=5, pady=5)
            vvar = tk.IntVar(value=0)
            ttk.Spinbox(wnd, from_=-20, to=20, textvariable=vvar, width=10).grid(row=1, column=1, padx=5, pady=5)
            def ok(): story_trait_roll_listbox.insert(tk.END, f"{tvar.get()}: {vvar.get():+d}"); wnd.destroy()
            ttk.Button(wnd, text="Add", command=ok).grid(row=2, column=0, columnspan=2, pady=10)
        
        def remove_trait_roll():
            s = story_trait_roll_listbox.curselection()
            if s: story_trait_roll_listbox.delete(s[0])
        
        tr_btns = ttk.Frame(trait_roll_frame)
        tr_btns.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(tr_btns, text="Add", command=add_trait_roll).pack(pady=2)
        ttk.Button(tr_btns, text="Remove", command=remove_trait_roll).pack(pady=2)
        row += 1
        
        story_trait_msg_vars = {}
        for lbl, key in [
            ("trait_msg_success_both", "trait_msg_success_both"),
            ("trait_msg_success_pos", "trait_msg_success_pos"),
            ("trait_msg_success_neg", "trait_msg_success_neg"),
            ("trait_msg_failure_both", "trait_msg_failure_both"),
            ("trait_msg_failure_neg", "trait_msg_failure_neg"),
            ("trait_msg_failure_pos", "trait_msg_failure_pos"),
        ]:
            ttk.Label(traits_scrollable, text=f"{lbl.replace('_', ' ').title()}:").grid(row=row, column=0, sticky="w", padx=5, pady=3)
            story_trait_msg_vars[key] = tk.StringVar(value=story.get(key) or '')
            ttk.Entry(traits_scrollable, textvariable=story_trait_msg_vars[key], width=55).grid(row=row, column=1, sticky="ew", padx=5, pady=3)
            row += 1
        
        ttk.Label(traits_scrollable, text="Required Traits (worker must have all):", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        row += 1
        req_traits_frame = ttk.Frame(traits_scrollable)
        req_traits_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        story_required_traits_listbox = tk.Listbox(req_traits_frame, height=3)
        story_required_traits_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        for t in story.get('required_traits', []):
            story_required_traits_listbox.insert(tk.END, t)
        req_btns = ttk.Frame(req_traits_frame)
        req_btns.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(req_btns, text="Add", command=lambda: self.add_trait_to_listbox(story_required_traits_listbox)).pack(pady=2)
        ttk.Button(req_btns, text="Remove", command=lambda: story_required_traits_listbox.delete(tk.ANCHOR)).pack(pady=2)
        row += 1
        
        ttk.Label(traits_scrollable, text="Excluded Traits (worker must have none):", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        row += 1
        exc_traits_frame = ttk.Frame(traits_scrollable)
        exc_traits_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        story_excluded_traits_listbox = tk.Listbox(exc_traits_frame, height=3)
        story_excluded_traits_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        for t in story.get('excluded_traits', []):
            story_excluded_traits_listbox.insert(tk.END, t)
        exc_btns = ttk.Frame(exc_traits_frame)
        exc_btns.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(exc_btns, text="Add", command=lambda: self.add_trait_to_listbox(story_excluded_traits_listbox)).pack(pady=2)
        ttk.Button(exc_btns, text="Remove", command=lambda: story_excluded_traits_listbox.delete(tk.ANCHOR)).pack(pady=2)
        row += 1
        
        ttk.Label(traits_scrollable, text="Stat Requirements (stat: min_value):", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        row += 1
        stat_req_frame = ttk.Frame(traits_scrollable)
        stat_req_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        story_stat_reqs_listbox = tk.Listbox(stat_req_frame, height=4)
        story_stat_reqs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        for k, v in story.get('stat_requirements', {}).items():
            story_stat_reqs_listbox.insert(tk.END, f"{k}: {v}")
        
        def add_stat_req():
            wnd = tk.Toplevel(editor_window)
            wnd.title("Add Stat Requirement")
            ttk.Label(wnd, text="Stat:").grid(row=0, column=0, padx=5, pady=5)
            svar = tk.StringVar()
            ttk.Combobox(wnd, textvariable=svar, values=["romance", "relationship", "rebelliousness", "joy"], width=20).grid(row=0, column=1, padx=5, pady=5)
            ttk.Label(wnd, text="Min Value:").grid(row=1, column=0, padx=5, pady=5)
            vvar = tk.IntVar(value=0)
            ttk.Spinbox(wnd, from_=0, to=100, textvariable=vvar, width=10).grid(row=1, column=1, padx=5, pady=5)
            def ok(): story_stat_reqs_listbox.insert(tk.END, f"{svar.get()}: {vvar.get()}"); wnd.destroy()
            ttk.Button(wnd, text="Add", command=ok).grid(row=2, column=0, columnspan=2, pady=10)
        
        def remove_stat_req():
            s = story_stat_reqs_listbox.curselection()
            if s: story_stat_reqs_listbox.delete(s[0])
        
        sr_btns = ttk.Frame(stat_req_frame)
        sr_btns.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(sr_btns, text="Add", command=add_stat_req).pack(pady=2)
        ttk.Button(sr_btns, text="Remove", command=remove_stat_req).pack(pady=2)
        row += 1
        
        ttk.Label(traits_scrollable, text="Legacy: Relevant Traits + Trait Success (optional):", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        row += 1
        traits_list_frame = ttk.Frame(traits_scrollable)
        traits_list_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        story_traits_listbox = tk.Listbox(traits_list_frame, height=4)
        story_traits_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        for trait in story.get('relevant_traits', []):
            story_traits_listbox.insert(tk.END, trait)
        traits_buttons = ttk.Frame(traits_list_frame)
        traits_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(traits_buttons, text="Add", command=lambda: self.add_trait_to_listbox(story_traits_listbox)).pack(pady=2)
        ttk.Button(traits_buttons, text="Remove", command=lambda: story_traits_listbox.delete(tk.ANCHOR)).pack(pady=2)
        row += 1
        
        ttk.Label(traits_scrollable, text="Trait Bonus Formula:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        trait_bonus_var = tk.StringVar(value=story.get('trait_bonus', 'level * 100'))
        ttk.Entry(traits_scrollable, textvariable=trait_bonus_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        ttk.Label(traits_scrollable, text="Trait Success Message:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        trait_success_var = tk.StringVar(value=story.get('trait_success', '{worker_name}\'s {trait} proves valuable.'))
        ttk.Entry(traits_scrollable, textvariable=trait_success_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        traits_scrollable.columnconfigure(1, weight=1)
        
        earnings_story_frame = ttk.Frame(story_notebook)
        story_notebook.add(earnings_story_frame, text="Earnings")
        
        earnings = story.get('earnings', {})
        row = 0
        
        ttk.Label(earnings_story_frame, text="Earnings Formulas", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Label(earnings_story_frame, text="Variables: skill, level").grid(row=row, column=3, sticky="w", padx=5)
        row += 1
        
        ttk.Label(earnings_story_frame, text="Success:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_earnings_success_var = tk.StringVar(value=earnings.get('success', '100 + skill * 5'))
        ttk.Entry(earnings_story_frame, textvariable=story_earnings_success_var, width=40).grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(earnings_story_frame, text="Failure:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_earnings_failure_var = tk.StringVar(value=earnings.get('failure', '-10'))
        ttk.Entry(earnings_story_frame, textvariable=story_earnings_failure_var, width=40).grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(earnings_story_frame, text="Critical Success:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_earnings_critical_var = tk.StringVar(value=earnings.get('critical_success', '150 + skill * 8'))
        ttk.Entry(earnings_story_frame, textvariable=story_earnings_critical_var, width=40).grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(earnings_story_frame, text="Mediocre:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        story_earnings_mediocre_var = tk.StringVar(value=earnings.get('mediocre', '50 + skill * 2'))
        ttk.Entry(earnings_story_frame, textvariable=story_earnings_mediocre_var, width=40).grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1
        
        earnings_story_frame.columnconfigure(1, weight=1)
        
        desc_story_frame = ttk.Frame(story_notebook)
        story_notebook.add(desc_story_frame, text="Descriptions")
        
        descriptions = story.get('descriptions', {})
        
        ttk.Label(desc_story_frame, text="Descriptions for each outcome", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=5)
        ttk.Label(desc_story_frame, text="Use: {worker_name}, {skill}").pack(anchor="w", padx=5)
        
        ttk.Label(desc_story_frame, text="Failure:").pack(anchor="w", padx=5, pady=(10, 2))
        desc_failure_text = scrolledtext.ScrolledText(desc_story_frame, width=80, height=4)
        desc_failure_text.pack(fill=tk.X, padx=5, pady=2)
        desc_failure_text.insert(tk.END, descriptions.get('failure', ''))
        
        ttk.Label(desc_story_frame, text="Mediocre:").pack(anchor="w", padx=5, pady=(10, 2))
        desc_mediocre_text = scrolledtext.ScrolledText(desc_story_frame, width=80, height=4)
        desc_mediocre_text.pack(fill=tk.X, padx=5, pady=2)
        desc_mediocre_text.insert(tk.END, descriptions.get('mediocre', ''))
        
        ttk.Label(desc_story_frame, text="Success:").pack(anchor="w", padx=5, pady=(10, 2))
        desc_success_text = scrolledtext.ScrolledText(desc_story_frame, width=80, height=4)
        desc_success_text.pack(fill=tk.X, padx=5, pady=2)
        desc_success_text.insert(tk.END, descriptions.get('success', ''))
        
        ttk.Label(desc_story_frame, text="Critical Success:").pack(anchor="w", padx=5, pady=(10, 2))
        desc_critical_text = scrolledtext.ScrolledText(desc_story_frame, width=80, height=4)
        desc_critical_text.pack(fill=tk.X, padx=5, pady=2)
        desc_critical_text.insert(tk.END, descriptions.get('critical_success', ''))
        
        conseq_story_frame = ttk.Frame(story_notebook)
        story_notebook.add(conseq_story_frame, text="Consequences")
        
        conseq_canvas = tk.Canvas(conseq_story_frame)
        conseq_scrollbar = ttk.Scrollbar(conseq_story_frame, orient="vertical", command=conseq_canvas.yview)
        conseq_scrollable = ttk.Frame(conseq_canvas)
        conseq_scrollable.bind("<Configure>", lambda e: conseq_canvas.configure(scrollregion=conseq_canvas.bbox("all")))
        conseq_canvas.create_window((0, 0), window=conseq_scrollable, anchor="nw")
        conseq_canvas.configure(yscrollcommand=conseq_scrollbar.set)
        conseq_canvas.pack(side="left", fill="both", expand=True)
        conseq_scrollbar.pack(side="right", fill="y")
        
        consequences = story.get('consequences', {})
        consequence_vars = {}
        
        outcomes = ['failure', 'mediocre', 'success', 'critical_success']
        attributes = ['energy', 'health', 'joy', 'rebelliousness', 'romance', 'relationship', 'reputation', 'libido', 'obedience']
        
        row = 0
        ttk.Label(conseq_scrollable, text="Consequences (attribute changes per outcome)", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=len(attributes)+1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Header
        ttk.Label(conseq_scrollable, text="Outcome").grid(row=row, column=0, padx=5, pady=2)
        for col, attr in enumerate(attributes):
            ttk.Label(conseq_scrollable, text=attr.capitalize()[:6]).grid(row=row, column=col+1, padx=2, pady=2)
        row += 1
        
        for outcome in outcomes:
            outcome_data = consequences.get(outcome, {})
            consequence_vars[outcome] = {}
            
            ttk.Label(conseq_scrollable, text=outcome.replace('_', ' ').title()).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            for col, attr in enumerate(attributes):
                var = tk.IntVar(value=outcome_data.get(attr, 0))
                consequence_vars[outcome][attr] = var
                ttk.Spinbox(conseq_scrollable, from_=-20, to=20, textvariable=var, width=5).grid(row=row, column=col+1, padx=2, pady=2)
            row += 1
        
        loot_story_frame = ttk.Frame(story_notebook)
        story_notebook.add(loot_story_frame, text="Loot")
        
        loot_data = story.get('loot', {})
        
        row = 0
        ttk.Label(loot_story_frame, text="Random Loot Rolls:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        loot_rolls_var = tk.IntVar(value=loot_data.get('rolls', 0))
        ttk.Spinbox(loot_story_frame, from_=0, to=10, textvariable=loot_rolls_var, width=10).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(loot_story_frame, text="(0 = no random loot)").grid(row=row, column=2, sticky="w", padx=5)
        row += 1
        
        ttk.Label(loot_story_frame, text="Bonus Items (specific items with chance):", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        bonus_items_frame = ttk.Frame(loot_story_frame)
        bonus_items_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        bonus_items_listbox = tk.Listbox(bonus_items_frame, height=8, width=60)
        bonus_items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Load existing bonus items
        bonus_items_data = loot_data.get('bonus_items', [])
        for item in bonus_items_data:
            item_str = f"{item.get('item_id', '?')} - {item.get('chance', 1.0)*100:.1f}%"
            if item.get('nsfw'):
                item_str += " [NSFW]"
            if item.get('critical_only'):
                item_str += " [Crit Only]"
            bonus_items_listbox.insert(tk.END, item_str)
        
        bonus_buttons = ttk.Frame(bonus_items_frame)
        bonus_buttons.pack(side=tk.LEFT, fill=tk.Y)
        
        def add_bonus_item():
            item_window = tk.Toplevel(editor_window)
            item_window.title("Add Bonus Item")
            item_window.geometry("400x200")
            
            ttk.Label(item_window, text="Item ID:").grid(row=0, column=0, padx=5, pady=5)
            item_id_var = tk.StringVar()
            ttk.Entry(item_window, textvariable=item_id_var, width=30).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(item_window, text="Chance (0.01 = 1%):").grid(row=1, column=0, padx=5, pady=5)
            chance_var = tk.DoubleVar(value=0.05)
            ttk.Entry(item_window, textvariable=chance_var, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)
            
            nsfw_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(item_window, text="NSFW Only", variable=nsfw_var).grid(row=2, column=1, sticky="w", padx=5, pady=5)
            
            crit_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(item_window, text="Critical Success Only", variable=crit_var).grid(row=3, column=1, sticky="w", padx=5, pady=5)
            
            def save_item():
                new_item = {
                    'item_id': item_id_var.get(),
                    'chance': chance_var.get()
                }
                if nsfw_var.get():
                    new_item['nsfw'] = True
                if crit_var.get():
                    new_item['critical_only'] = True
                bonus_items_data.append(new_item)
                
                item_str = f"{new_item['item_id']} - {new_item['chance']*100:.1f}%"
                if new_item.get('nsfw'):
                    item_str += " [NSFW]"
                if new_item.get('critical_only'):
                    item_str += " [Crit Only]"
                bonus_items_listbox.insert(tk.END, item_str)
                item_window.destroy()
            
            ttk.Button(item_window, text="Add", command=save_item).grid(row=4, column=0, columnspan=2, pady=10)
        
        def remove_bonus_item():
            sel = bonus_items_listbox.curselection()
            if sel:
                idx = sel[0]
                bonus_items_listbox.delete(idx)
                if idx < len(bonus_items_data):
                    bonus_items_data.pop(idx)
        
        ttk.Button(bonus_buttons, text="Add Item", command=add_bonus_item).pack(pady=2)
        ttk.Button(bonus_buttons, text="Remove", command=remove_bonus_item).pack(pady=2)
        
        loot_story_frame.columnconfigure(1, weight=1)
        
        # ========== BOTONES PRINCIPALES ==========
        buttons_frame = ttk.Frame(editor_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_story():
            # Basic
            story['id'] = story_id_var.get()
            story['report'] = story_report_var.get()
            story['weight'] = story_weight_var.get()
            story['difficulty_modifier'] = story_diff_mod_var.get()
            wg = story_worker_gender_var.get().strip()
            story['worker_gender_requirement'] = wg if wg in ('male', 'female') else None
            story['nsfw_only'] = story_nsfw_only_var.get()
            story['story_image'] = story_image_var.get()
            story['failure_image'] = failure_image_var.get()
            
            # Skill options
            skill_options = []
            for i in range(story_skill_options_listbox.size()):
                skill_options.append(story_skill_options_listbox.get(i))
            story['skill_options'] = skill_options
            
            # Trait roll modifiers
            trm = {}
            for i in range(story_trait_roll_listbox.size()):
                line = story_trait_roll_listbox.get(i)
                if ':' in line:
                    tname, rest = line.split(':', 1)
                    try:
                        trm[tname.strip()] = int(rest.strip().replace('+', ''))
                    except ValueError:
                        pass
            story['trait_roll_modifiers'] = trm
            
            # Trait message templates
            for key, var in story_trait_msg_vars.items():
                v = var.get().strip()
                story[key] = v if v else None
            
            # Required/excluded traits
            story['required_traits'] = [story_required_traits_listbox.get(i) for i in range(story_required_traits_listbox.size())]
            story['excluded_traits'] = [story_excluded_traits_listbox.get(i) for i in range(story_excluded_traits_listbox.size())]
            
            # Stat requirements
            sr = {}
            for i in range(story_stat_reqs_listbox.size()):
                line = story_stat_reqs_listbox.get(i)
                if ':' in line:
                    sname, sval = line.split(':', 1)
                    try:
                        sr[sname.strip()] = int(sval.strip())
                    except ValueError:
                        pass
            story['stat_requirements'] = sr
            
            # Legacy traits
            relevant_traits = []
            for i in range(story_traits_listbox.size()):
                relevant_traits.append(story_traits_listbox.get(i))
            story['relevant_traits'] = relevant_traits
            story['trait_bonus'] = trait_bonus_var.get()
            story['trait_success'] = trait_success_var.get()
            
            # Earnings
            story['earnings'] = {
                'success': story_earnings_success_var.get(),
                'failure': story_earnings_failure_var.get(),
                'critical_success': story_earnings_critical_var.get(),
                'mediocre': story_earnings_mediocre_var.get()
            }
            
            # Descriptions
            story['descriptions'] = {
                'failure': desc_failure_text.get("1.0", tk.END).strip(),
                'mediocre': desc_mediocre_text.get("1.0", tk.END).strip(),
                'success': desc_success_text.get("1.0", tk.END).strip(),
                'critical_success': desc_critical_text.get("1.0", tk.END).strip()
            }
            
            # Consequences
            story['consequences'] = {}
            for outcome in outcomes:
                story['consequences'][outcome] = {}
                for attr in attributes:
                    val = consequence_vars[outcome][attr].get()
                    if val != 0:  # Only save non-zero values
                        story['consequences'][outcome][attr] = val
            
            # Loot
            story['loot'] = {
                'rolls': loot_rolls_var.get(),
                'bonus_items': bonus_items_data
            }
            
            self.refresh_daily_stories_list()
            self.has_unsaved_changes = True
            self.update_title()
            editor_window.destroy()
        
        ttk.Button(buttons_frame, text="Save Story", command=save_story).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=editor_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_trait_to_listbox(self, listbox):
        """Agregar trait a una listbox"""
        trait = simpledialog.askstring("Add Trait", "Enter trait name:")
        if trait:
            listbox.insert(tk.END, trait)
    
    def add_story_skill_option(self, listbox):
        """Agregar skill option a story"""
        skill_window = tk.Toplevel(self.root)
        skill_window.title("Add Skill Option")
        skill_window.geometry("300x100")
        
        ttk.Label(skill_window, text="Skill:").grid(row=0, column=0, padx=5, pady=5)
        skill_var = tk.StringVar()
        ttk.Combobox(skill_window, textvariable=skill_var, values=self.all_skills, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        def add_skill():
            skill = skill_var.get()
            if skill:
                listbox.insert(tk.END, skill)
            skill_window.destroy()
        
        ttk.Button(skill_window, text="Add", command=add_skill).grid(row=1, column=0, padx=5, pady=10)
        ttk.Button(skill_window, text="Cancel", command=skill_window.destroy).grid(row=1, column=1, padx=5, pady=10)
    
    def save_current_building_data(self):
        """Guardar datos del building actual"""
        if not self.current_building:
            return
        
        self.current_building['id'] = self.building_id_var.get()
        self.current_building['name'] = self.building_name_var.get()
        self.current_building['skill_name'] = self.building_skill_name_var.get()
        self.current_building['skill_description'] = self.building_skill_description_text.get(1.0, tk.END).strip()
        self.current_building['nsfw'] = self.building_nsfw_var.get()
        
        # Locations
        locations = []
        for i in range(self.building_locations_listbox.size()):
            locations.append(self.building_locations_listbox.get(i))
        self.current_building['allowed_map_locations'] = locations
        
        if self.current_profession:
            self.save_current_profession()
        
        self.refresh_buildings_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def show_building_help(self):
        """Mostrar ayuda para buildings"""
        help_text = """
BUILDING EDITOR HELP

Basic Information:
- ID: Unique building identifier
- Name: Building display name
- Skill Name: Name of the skill that workers train in this building (e.g. "Hag Potions", "Academy Training"). Used in daily stories and events.
- Skill Description: Flavor text explaining what this skill does and how it's used in the game. Shown to players.
- NSFW: Mark if building is NSFW content
- Allowed Map Locations: Map locations where this building can be placed. Use "Add from list" to pick from known locations in the game.

Professions:
- Each building can have multiple professions
- Professions define what workers can do in the building
- Each profession has skills, daily stories, and earnings formulas

Daily Stories (v5.2 - Full Editor):
- Basic: ID, Report, Weight, Difficulty Modifier, Images
- Traits: Relevant traits, bonus formula, success message
- Earnings: Formulas for each outcome (use 'skill', 'level' variables)
- Descriptions: Text for failure, mediocre, success, critical_success
- Consequences: Attribute changes per outcome:
  * energy, health, joy, rebelliousness, romance, relationship, reputation, libido
- Loot: Random rolls + bonus_items with:
  * item_id: Item to potentially drop
  * chance: 0.01 = 1%, 0.05 = 5%, etc.
  * nsfw: Only drop if NSFW enabled
  * critical_only: Only drop on critical success

Variables in formulas: skill, level
Variables in messages: {worker_name}, {skill}, {trait}
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Building Editor Help")
        help_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def load_buildings_file_dialog(self):
        """Cargar archivo de buildings"""
        initial = self.get_initial_dir("data/buildings")
        
        file_path = filedialog.askopenfilename(
            title="Load Buildings File",
            initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and 'building_types' in data:
                    self.buildings_data = data['building_types']
                    self.refresh_buildings_list()
                    messagebox.showinfo("Success", f"Loaded {len(data['building_types'])} buildings")
                elif isinstance(data, list):
                    self.buildings_data = data
                    self.refresh_buildings_list()
                    messagebox.showinfo("Success", f"Loaded {len(data)} buildings")
                else:
                    messagebox.showerror("Error", "Invalid file format")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")
    
    def new_building(self):
        """Crear nuevo edificio vacío"""
        new_building = {
            'id': 'new_building',
            'name': 'New Building',
            'skill_name': 'Building Skill',
            'skill_description': 'Description of the skill workers train in this building.',
            'nsfw': False,
            'allowed_map_locations': [],
            'professions': []
        }
        if not isinstance(self.buildings_data, list):
            self.buildings_data = []
        self.buildings_data.append(new_building)
        self.current_building = new_building
        self.refresh_buildings_list()
        idx = len(self.buildings_data) - 1
        self.buildings_listbox.selection_clear(0, tk.END)
        self.buildings_listbox.selection_set(idx)
        self.buildings_listbox.see(idx)
        self.load_building_data()
        self.has_unsaved_changes = True
        self.update_title()
    
    def save_buildings_as(self):
        """Guardar buildings en archivo específico"""
        if not isinstance(self.buildings_data, list) or not self.buildings_data:
            messagebox.showwarning("Warning", "No buildings to save")
            return
        
        initial = self.get_initial_dir("data/buildings")
        
        file_path = filedialog.asksaveasfilename(
            title="Save Buildings As...",
            initialdir=initial,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if os.path.exists(file_path):
                if not messagebox.askyesno("Confirm Overwrite", f"File {Path(file_path).name} already exists.\n\nOverwrite it?"):
                    return
            
            try:
                data = {'building_types': self.buildings_data}
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Saved {len(self.buildings_data)} buildings")
                self.has_unsaved_changes = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def save_buildings(self):
        """Guardar buildings (con confirmación)"""
        if not isinstance(self.buildings_data, list) or not self.buildings_data:
            messagebox.showwarning("Warning", "No buildings to save")
            return
        
        if not self.game_directory:
            messagebox.showwarning("Warning", "Please select game directory first")
            return
        
        if not messagebox.askyesno("Confirm", f"Save {len(self.buildings_data)} buildings to building_types.json?\n\nThis will overwrite the existing file."):
            return
        
        data_path = Path(self.game_directory) / "game" / "data" / "buildings" / "building_types.json"
        
        try:
            data = {'building_types': self.buildings_data}
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Saved {len(self.buildings_data)} buildings")
            self.has_unsaved_changes = False
            self.update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    # ==================== EVENTS TAB ====================
    
    def setup_events_tab(self):
        """Configurar pestaña de Events"""
        events_frame = ttk.Frame(self.notebook)
        self.notebook.add(events_frame, text="Events")
        
        main_frame = ttk.Frame(events_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="Events List", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        self.events_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.events_listbox.pack(fill=tk.BOTH, expand=True)
        self.events_listbox.bind('<<ListboxSelect>>', self.on_event_select)
        
        events_buttons_frame = ttk.Frame(left_frame)
        events_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(events_buttons_frame, text="Load Events File", command=self.load_events_file_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(events_buttons_frame, text="Save Events As...", command=self.save_events_as).pack(fill=tk.X, pady=2)
        ttk.Button(events_buttons_frame, text="Save Events", command=self.save_events).pack(fill=tk.X, pady=2)
        ttk.Separator(events_buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(events_buttons_frame, text="New Event from Template", command=self.new_event_from_template).pack(fill=tk.X, pady=2)
        ttk.Button(events_buttons_frame, text="Validate Events", command=self.validate_events).pack(fill=tk.X, pady=2)
        ttk.Button(events_buttons_frame, text="Save Current Event", command=self.save_current_event_data).pack(fill=tk.X, pady=2)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        event_header_frame = ttk.Frame(right_frame)
        event_header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(event_header_frame, text="Event Editor", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(event_header_frame, text="? Help", command=self.show_event_help).pack(side=tk.RIGHT)
        
        self.event_notebook = ttk.Notebook(right_frame)
        self.event_notebook.pack(fill=tk.BOTH, expand=True)
        
        basic_event_frame = ttk.Frame(self.event_notebook)
        self.event_notebook.add(basic_event_frame, text="Basic Information")
        self.setup_event_basic_fields(basic_event_frame)
        
        config_event_frame = ttk.Frame(self.event_notebook)
        self.event_notebook.add(config_event_frame, text="Configuration")
        self.setup_event_config_fields(config_event_frame)
        
        choices_event_frame = ttk.Frame(self.event_notebook)
        self.event_notebook.add(choices_event_frame, text="Choices")
        self.setup_event_choices_tab(choices_event_frame)
    
    def refresh_events_list(self):
        """Actualizar lista de events"""
        if hasattr(self, 'events_listbox'):
            self.events_listbox.delete(0, tk.END)
            for event_id, event_data in self.events_data.items():
                name = event_data.get('id', event_id)
                self.events_listbox.insert(tk.END, name)
    
    def on_event_select(self, event):
        """Manejar selección de event"""
        selection = self.events_listbox.curselection()
        if selection:
            event_id = self.events_listbox.get(selection[0])
            self.current_event = self.events_data.get(event_id)
            if self.current_event:
                self.load_event_data()
    
    def setup_event_basic_fields(self, parent):
        """Configurar campos básicos del event"""
        event_canvas = tk.Canvas(parent)
        event_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=event_canvas.yview)
        event_scrollable = ttk.Frame(event_canvas)
        
        event_scrollable.bind("<Configure>", lambda e: event_canvas.configure(scrollregion=event_canvas.bbox("all")))
        event_canvas.create_window((0, 0), window=event_scrollable, anchor="nw")
        event_canvas.configure(yscrollcommand=event_scrollbar.set)
        
        event_canvas.pack(side="left", fill="both", expand=True)
        event_scrollbar.pack(side="right", fill="y")
        
        row = 0
        
        # ID
        ttk.Label(event_scrollable, text="ID:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_id_var = tk.StringVar()
        ttk.Entry(event_scrollable, textvariable=self.event_id_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Description
        ttk.Label(event_scrollable, text="Description:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        self.event_description_text = scrolledtext.ScrolledText(event_scrollable, width=50, height=6)
        self.event_description_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Weight
        ttk.Label(event_scrollable, text="Weight:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_weight_var = tk.IntVar(value=1)
        ttk.Spinbox(event_scrollable, from_=1, to=10, textvariable=self.event_weight_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Event Probability (percentage, 1-100) - Optional
        ttk.Label(event_scrollable, text="Event Probability (%):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        probability_frame = ttk.Frame(event_scrollable)
        probability_frame.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.event_probability_var = tk.IntVar(value=0)  # 0 means not set
        ttk.Spinbox(probability_frame, from_=0, to=100, textvariable=self.event_probability_var, width=15).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(probability_frame, text="(0 = default, 1-100 = NOT affected by managers)", font=("Arial", 8), foreground="gray").pack(side=tk.LEFT)
        row += 1
        
        # NSFW
        self.event_nsfw_var = tk.BooleanVar()
        ttk.Checkbutton(event_scrollable, text="NSFW", variable=self.event_nsfw_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Event Music
        ttk.Label(event_scrollable, text="Event Music:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_music_var = tk.StringVar()
        ttk.Entry(event_scrollable, textvariable=self.event_music_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Background Image
        ttk.Label(event_scrollable, text="Background Image:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_bg_image_var = tk.StringVar()
        ttk.Entry(event_scrollable, textvariable=self.event_bg_image_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Success Image
        ttk.Label(event_scrollable, text="Success Image:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_success_image_var = tk.StringVar()
        ttk.Entry(event_scrollable, textvariable=self.event_success_image_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Failure Image
        ttk.Label(event_scrollable, text="Failure Image:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_failure_image_var = tk.StringVar()
        ttk.Entry(event_scrollable, textvariable=self.event_failure_image_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        
        event_scrollable.columnconfigure(1, weight=1)
    
    def setup_event_config_fields(self, parent):
        """Configurar campos de configuración del event"""
        event_canvas = tk.Canvas(parent)
        event_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=event_canvas.yview)
        event_scrollable = ttk.Frame(event_canvas)
        
        event_scrollable.bind("<Configure>", lambda e: event_canvas.configure(scrollregion=event_canvas.bbox("all")))
        event_canvas.create_window((0, 0), window=event_scrollable, anchor="nw")
        event_canvas.configure(yscrollcommand=event_scrollbar.set)
        
        event_canvas.pack(side="left", fill="both", expand=True)
        event_scrollbar.pack(side="right", fill="y")
        
        row = 0
        
        # Limited (Note: limited: false = NOT affected by managers, limited: true = affected by managers)
        self.event_limited_var = tk.BooleanVar()
        limited_frame = ttk.Frame(event_scrollable)
        limited_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(limited_frame, text="Limited Event (affected by managers)", variable=self.event_limited_var).pack(side=tk.LEFT)
        ttk.Label(limited_frame, text="(Unchecked = NOT affected by managers)", font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        row += 1
        
        # Max Occurrences
        ttk.Label(event_scrollable, text="Max Occurrences:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_max_occurrences_var = tk.IntVar(value=1)
        ttk.Spinbox(event_scrollable, from_=1, to=100, textvariable=self.event_max_occurrences_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Cooldown Days
        ttk.Label(event_scrollable, text="Cooldown Days:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_cooldown_var = tk.IntVar(value=7)
        ttk.Spinbox(event_scrollable, from_=0, to=365, textvariable=self.event_cooldown_var, width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Worker Selection
        ttk.Label(event_scrollable, text="Worker Selection:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_worker_selection_var = tk.StringVar(value="choose")
        ttk.Combobox(event_scrollable, textvariable=self.event_worker_selection_var, values=["choose", "none", "random"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Worker Gender Requirement
        ttk.Label(event_scrollable, text="Worker Gender Requirement:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_worker_gender_var = tk.StringVar(value="any")
        ttk.Combobox(event_scrollable, textvariable=self.event_worker_gender_var, values=["any", "male", "female"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Player Gender Requirement (Lord/Lady)
        ttk.Label(event_scrollable, text="Player Gender Requirement:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_player_gender_var = tk.StringVar(value="")
        ttk.Combobox(event_scrollable, textvariable=self.event_player_gender_var, values=["", "male", "female"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(event_scrollable, text="(empty=both, male=Lord only, female=Lady only)", font=("Arial", 8), foreground="gray").grid(row=row, column=2, sticky="w", padx=5)
        row += 1
        
        self.event_requires_assigned_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(event_scrollable, text="Requires Assigned Worker (event only if worker in building)", variable=self.event_requires_assigned_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Required Building Worker Traits
        ttk.Label(event_scrollable, text="Required Building Worker Traits:", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5))
        row += 1
        req_bw_frame = ttk.Frame(event_scrollable)
        req_bw_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.event_req_building_worker_traits_listbox = tk.Listbox(req_bw_frame, height=3)
        self.event_req_building_worker_traits_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        req_bw_btns = ttk.Frame(req_bw_frame)
        req_bw_btns.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(req_bw_btns, text="Add", command=self.add_event_req_building_worker_trait).pack(pady=2)
        ttk.Button(req_bw_btns, text="Remove", command=lambda: self.event_req_building_worker_traits_listbox.delete(tk.ANCHOR)).pack(pady=2)
        row += 1
        
        # Required active professions (servant_jobs ids, e.g. guard)
        ttk.Label(event_scrollable, text="Required Active Professions (job ids):", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5))
        row += 1
        req_ap_frame = ttk.Frame(event_scrollable)
        req_ap_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.event_req_active_professions_listbox = tk.Listbox(req_ap_frame, height=3)
        self.event_req_active_professions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        req_ap_btns = ttk.Frame(req_ap_frame)
        req_ap_btns.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(req_ap_btns, text="Add", command=self.add_event_required_active_profession).pack(pady=2)
        ttk.Button(req_ap_btns, text="Remove", command=lambda: self.event_req_active_professions_listbox.delete(tk.ANCHOR)).pack(pady=2)
        row += 1

        # Forbidden active professions
        ttk.Label(event_scrollable, text="Forbidden Active Professions (job ids):", font=("Arial", 9, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5))
        row += 1
        forb_frame = ttk.Frame(event_scrollable)
        forb_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.event_forbidden_professions_listbox = tk.Listbox(forb_frame, height=3)
        self.event_forbidden_professions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        forb_btns = ttk.Frame(forb_frame)
        forb_btns.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(forb_btns, text="Add", command=self.add_event_forbidden_active_profession).pack(pady=2)
        ttk.Button(forb_btns, text="Remove", command=lambda: self.event_forbidden_professions_listbox.delete(tk.ANCHOR)).pack(pady=2)
        row += 1

        ttk.Label(event_scrollable, text="Min worker skill in building (optional):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_min_skill_var = tk.StringVar(value="")
        ttk.Entry(event_scrollable, textvariable=self.event_min_skill_var, width=12).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        ttk.Label(event_scrollable, text="Skill name (optional; blank = building type skill_name):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.event_worker_skill_name_var = tk.StringVar(value="")
        ttk.Entry(event_scrollable, textvariable=self.event_worker_skill_name_var, width=24).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Building Types
        ttk.Label(event_scrollable, text="Building Types:", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        building_types_frame = ttk.Frame(event_scrollable)
        building_types_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.event_building_types_listbox = tk.Listbox(building_types_frame, height=4)
        self.event_building_types_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        building_types_buttons = ttk.Frame(building_types_frame)
        building_types_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(building_types_buttons, text="Add", command=self.add_event_building_type).pack(pady=2)
        ttk.Button(building_types_buttons, text="Remove", command=self.remove_event_building_type).pack(pady=2)
        
        event_scrollable.columnconfigure(1, weight=1)
    
    def setup_event_choices_tab(self, parent):
        """Configurar pestaña de choices del event"""
        ttk.Label(parent, text="Event Choices", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        
        self.event_choices_listbox = tk.Listbox(parent, height=15)
        self.event_choices_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.event_choices_listbox.bind('<<ListboxSelect>>', self.on_event_choice_select)
        
        choices_buttons_frame = ttk.Frame(parent)
        choices_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(choices_buttons_frame, text="New Choice", command=self.add_event_choice).pack(side=tk.LEFT, padx=5)
        ttk.Button(choices_buttons_frame, text="Edit Choice", command=self.edit_event_choice).pack(side=tk.LEFT, padx=5)
        ttk.Button(choices_buttons_frame, text="Delete Choice", command=self.remove_event_choice).pack(side=tk.LEFT, padx=5)
    
    def load_event_data(self):
        """Cargar datos del event seleccionado"""
        if not self.current_event:
            return
        
        self.event_id_var.set(self.current_event.get('id', ''))
        self.event_description_text.delete(1.0, tk.END)
        self.event_description_text.insert(1.0, self.current_event.get('description', ''))
        self.event_weight_var.set(self.current_event.get('weight', 1))
        
        # Event Probability (optional, 1-100, 0 means not set)
        event_probability = self.current_event.get('event_probability')
        if event_probability is not None:
            self.event_probability_var.set(event_probability)
        else:
            self.event_probability_var.set(0)  # 0 = not set (default behavior)
        
        self.event_nsfw_var.set(self.current_event.get('nsfw', False))
        self.event_music_var.set(self.current_event.get('event_music', ''))
        self.event_bg_image_var.set(self.current_event.get('background_image', ''))
        self.event_success_image_var.set(self.current_event.get('success_image', ''))
        self.event_failure_image_var.set(self.current_event.get('failure_image', ''))
        
        # Config
        # Note: limited: false = NOT affected by managers, limited: true = affected by managers
        # Default to False (not affected by managers) if not set
        self.event_limited_var.set(self.current_event.get('limited', False))
        self.event_max_occurrences_var.set(self.current_event.get('max_occurrences', 1))
        self.event_cooldown_var.set(self.current_event.get('cooldown_days', 7))
        self.event_worker_selection_var.set(self.current_event.get('worker_selection', 'choose'))
        self.event_worker_gender_var.set(self.current_event.get('worker_gender_requirement', 'any'))
        
        # Player gender, requires assigned worker
        pg = self.current_event.get('player_gender_requirement') or ''
        self.event_player_gender_var.set('male' if pg == 'male' else 'female' if pg == 'female' else '')
        self.event_requires_assigned_var.set(self.current_event.get('requires_assigned_worker', False))
        
        # Required building worker traits
        if hasattr(self, 'event_req_building_worker_traits_listbox'):
            self.event_req_building_worker_traits_listbox.delete(0, tk.END)
            for t in self.current_event.get('required_building_worker_traits', []):
                self.event_req_building_worker_traits_listbox.insert(tk.END, t)
        
        if hasattr(self, 'event_req_active_professions_listbox'):
            self.event_req_active_professions_listbox.delete(0, tk.END)
            for t in self.current_event.get('required_active_professions', []) or []:
                self.event_req_active_professions_listbox.insert(tk.END, t)
        if hasattr(self, 'event_forbidden_professions_listbox'):
            self.event_forbidden_professions_listbox.delete(0, tk.END)
            for t in self.current_event.get('forbidden_active_professions', []) or []:
                self.event_forbidden_professions_listbox.insert(tk.END, t)
        if hasattr(self, 'event_min_skill_var'):
            ms = self.current_event.get('required_building_worker_min_skill', None)
            self.event_min_skill_var.set("" if ms is None else str(ms))
        if hasattr(self, 'event_worker_skill_name_var'):
            sn = self.current_event.get('required_building_worker_skill') or ""
            self.event_worker_skill_name_var.set(str(sn))
        
        # Building types
        self.event_building_types_listbox.delete(0, tk.END)
        building_types = self.current_event.get('building_type', [])
        if isinstance(building_types, str):
            building_types = [building_types]
        for bt in building_types:
            self.event_building_types_listbox.insert(tk.END, bt)
        
        # Choices
        self.refresh_event_choices_list()
    
    def refresh_event_choices_list(self):
        """Actualizar lista de choices"""
        if hasattr(self, 'event_choices_listbox'):
            self.event_choices_listbox.delete(0, tk.END)
            if self.current_event:
                choices = self.current_event.get('choices', [])
                for choice in choices:
                    option = choice.get('option', 'Unknown Choice')
                    self.event_choices_listbox.insert(tk.END, option)
    
    def on_event_choice_select(self, event):
        """Manejar selección de choice"""
        selection = self.event_choices_listbox.curselection()
        if selection and self.current_event:
            index = selection[0]
            choices = self.current_event.get('choices', [])
            if index < len(choices):
                self.open_choice_editor(choices[index], index)
    
    def add_event_building_type(self):
        """Agregar building type al event"""
        building_window = tk.Toplevel(self.root)
        building_window.title("Add Building Type")
        building_window.geometry("300x100")
        
        ttk.Label(building_window, text="Building Type:").grid(row=0, column=0, padx=5, pady=5)
        building_var = tk.StringVar()
        ttk.Combobox(building_window, textvariable=building_var, values=["tavern", "brothel", "restaurant", "casino", "adventurers_guild"], state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        def add_building():
            building = building_var.get()
            if building:
                self.event_building_types_listbox.insert(tk.END, building)
            building_window.destroy()
        
        ttk.Button(building_window, text="Add", command=add_building).grid(row=1, column=0, padx=5, pady=10)
        ttk.Button(building_window, text="Cancel", command=building_window.destroy).grid(row=1, column=1, padx=5, pady=10)
    
    def remove_event_building_type(self):
        """Quitar building type del event"""
        selection = self.event_building_types_listbox.curselection()
        if selection:
            self.event_building_types_listbox.delete(selection[0])
    
    def add_event_req_building_worker_trait(self):
        """Agregar required building worker trait"""
        trait = simpledialog.askstring("Add Trait", "Enter trait name (worker in building must have):")
        if trait:
            self.event_req_building_worker_traits_listbox.insert(tk.END, trait)
    
    def add_event_required_active_profession(self):
        pid = simpledialog.askstring("Profession id", "Enter profession id (must be active in building, e.g. guard):")
        if pid and str(pid).strip():
            self.event_req_active_professions_listbox.insert(tk.END, str(pid).strip())

    def add_event_forbidden_active_profession(self):
        pid = simpledialog.askstring("Profession id", "Enter profession id that must NOT be active (e.g. guard):")
        if pid and str(pid).strip():
            self.event_forbidden_professions_listbox.insert(tk.END, str(pid).strip())
    
    def _add_to_choice_listbox(self, listbox):
        """Add trait to choice listbox (required_traits or excluded_traits)"""
        trait = simpledialog.askstring("Add Trait", "Enter trait name:")
        if trait:
            listbox.insert(tk.END, trait)
    
    def validate_events(self):
        """Validar eventos cargados (mecánicas)"""
        if not _validate_events_list:
            messagebox.showwarning("Validate", "validate_event_mechanics not available.")
            return
        if not self.events_data:
            messagebox.showinfo("Validate", "No events loaded. Load an events file first.")
            return
        events_list = list(self.events_data.values())
        errors, warnings = _validate_events_list(events_list, "editor")
        msg_lines = [f"Errors: {len(errors)}", f"Warnings: {len(warnings)}"]
        if errors:
            msg_lines.append("")
            msg_lines.append("Errors:")
            for e in errors[:20]:
                msg_lines.append(f"  • {e}")
            if len(errors) > 20:
                msg_lines.append(f"  ... and {len(errors) - 20} more")
        if warnings:
            msg_lines.append("")
            msg_lines.append("Warnings:")
            for w in warnings[:10]:
                msg_lines.append(f"  • {w}")
            if len(warnings) > 10:
                msg_lines.append(f"  ... and {len(warnings) - 10} more")
        if not errors and not warnings:
            messagebox.showinfo("Validate", "All events passed validation.")
        else:
            messagebox.showinfo("Validation Result", "\n".join(msg_lines))
    
    def new_event_from_template(self):
        """Crear nuevo evento desde template embebido"""
        import copy
        new_event = copy.deepcopy(EMBEDDED_EVENT_TEMPLATE)
        new_event['id'] = 'new_event_from_template'
        new_event['description'] = 'New event description'
        if not isinstance(self.events_data, dict):
            self.events_data = {}
        self.events_data[new_event['id']] = new_event
        self.current_event = new_event
        self.refresh_events_list()
        self.load_event_data()
        self.has_unsaved_changes = True
        self.update_title()
        messagebox.showinfo("Success", "New event created from template. Edit ID and description, then save.")
    
    def add_event_choice(self):
        """Agregar nueva choice al event desde template embebido"""
        if not self.current_event:
            messagebox.showwarning("Warning", "No event selected")
            return
        
        import copy
        tmpl = EMBEDDED_EVENT_TEMPLATE
        choices = tmpl.get('choices', [])
        if choices and isinstance(choices[0], dict):
            new_choice = copy.deepcopy(choices[0])
            new_choice['option'] = 'New Choice'
            new_choice['message'] = 'Choice result message'
            new_choice['message_success'] = 'Success message'
            new_choice['message_failure'] = 'Failure message'
        else:
            new_choice = {
                'option': 'New Choice',
                'condition': '',
                'threshold': 0,
                'required_trait': '',
                'required_traits': [],
                'excluded_traits': [],
                'message': 'Choice result message (for simple choices)',
                'message_success': 'Success message (for skill checks)',
                'message_failure': 'Failure message (for skill checks)',
                'effect': {'success': {}, 'failure': {}, 'skill_modifiers': {}}
            }
        
        if 'choices' not in self.current_event:
            self.current_event['choices'] = []
        
        self.current_event['choices'].append(new_choice)
        self.refresh_event_choices_list()
        self.open_choice_editor(new_choice, len(self.current_event['choices']) - 1)
        self.has_unsaved_changes = True
        self.update_title()
    
    def edit_event_choice(self):
        """Editar choice seleccionada"""
        selection = self.event_choices_listbox.curselection()
        if selection and self.current_event:
            index = selection[0]
            choices = self.current_event.get('choices', [])
            if index < len(choices):
                self.open_choice_editor(choices[index], index)
    
    def remove_event_choice(self):
        """Eliminar choice"""
        selection = self.event_choices_listbox.curselection()
        if selection and self.current_event:
            index = selection[0]
            choices = self.current_event.get('choices', [])
            if index < len(choices):
                if messagebox.askyesno("Confirm", f"Delete choice '{choices[index].get('option', 'Unknown')}'?"):
                    choices.pop(index)
                    self.refresh_event_choices_list()
                    self.has_unsaved_changes = True
                    self.update_title()
    
    def open_choice_editor(self, choice, index):
        """Abrir editor de choice - Version completa con threshold y required_trait"""
        editor_window = tk.Toplevel(self.root)
        editor_window.title(f"Edit Choice: {choice.get('option', 'Unknown')}")
        editor_window.geometry("950x850")
        
        choice_notebook = ttk.Notebook(editor_window)
        choice_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        basic_choice_frame = ttk.Frame(choice_notebook)
        choice_notebook.add(basic_choice_frame, text="Basic")
        
        basic_canvas = tk.Canvas(basic_choice_frame)
        basic_scrollbar = ttk.Scrollbar(basic_choice_frame, orient="vertical", command=basic_canvas.yview)
        basic_scrollable = ttk.Frame(basic_canvas)
        basic_scrollable.bind("<Configure>", lambda e: basic_canvas.configure(scrollregion=basic_canvas.bbox("all")))
        basic_canvas.create_window((0, 0), window=basic_scrollable, anchor="nw")
        basic_canvas.configure(yscrollcommand=basic_scrollbar.set)
        basic_canvas.pack(side="left", fill="both", expand=True)
        basic_scrollbar.pack(side="right", fill="y")
        
        row = 0
        ttk.Label(basic_scrollable, text="Option Text:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        choice_option_var = tk.StringVar(value=choice.get('option', ''))
        ttk.Entry(basic_scrollable, textvariable=choice_option_var, width=60).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # ========== SKILL CHECK SECTION ==========
        ttk.Label(basic_scrollable, text="Skill Check (optional)", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        row += 1
        
        ttk.Label(basic_scrollable, text="Condition (skill name):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        choice_condition_var = tk.StringVar(value=choice.get('condition', ''))
        condition_combo = ttk.Combobox(basic_scrollable, textvariable=choice_condition_var, 
                                       values=['', 'building_skill', 'Combat', 'Charm', 'Clever', 'Agility', 'Service', 'Striptease', 
                                               'Sex', 'Oral', 'Anal', 'BDSM', 'Hand', 'Homo', 'Group', 
                                               'Extreme', 'Special', 'Craft'], width=30)
        condition_combo.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Threshold (min skill level):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        choice_threshold_var = tk.IntVar(value=choice.get('threshold', 0))
        ttk.Spinbox(basic_scrollable, from_=0, to=100, textvariable=choice_threshold_var, width=10).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(basic_scrollable, text="(0 = no minimum, worker just needs the condition skill)").grid(row=row, column=2, sticky="w", padx=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Required Trait:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        choice_required_trait_var = tk.StringVar(value=choice.get('required_trait', ''))
        ttk.Entry(basic_scrollable, textvariable=choice_required_trait_var, width=30).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(basic_scrollable, text="(legacy, worker MUST have)").grid(row=row, column=2, sticky="w", padx=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Required Traits (list):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        req_traits_frame = ttk.Frame(basic_scrollable)
        req_traits_frame.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        choice_req_traits_listbox = tk.Listbox(req_traits_frame, height=2, width=30)
        choice_req_traits_listbox.pack(side=tk.LEFT, padx=(0, 5))
        for t in choice.get('required_traits', []):
            choice_req_traits_listbox.insert(tk.END, t)
        ttk.Button(req_traits_frame, text="Add", command=lambda: self._add_to_choice_listbox(choice_req_traits_listbox)).pack(side=tk.LEFT, padx=2)
        ttk.Button(req_traits_frame, text="Remove", command=lambda: choice_req_traits_listbox.delete(tk.ANCHOR)).pack(side=tk.LEFT)
        row += 1
        
        ttk.Label(basic_scrollable, text="Excluded Traits (list):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        exc_traits_frame = ttk.Frame(basic_scrollable)
        exc_traits_frame.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        choice_exc_traits_listbox = tk.Listbox(exc_traits_frame, height=2, width=30)
        choice_exc_traits_listbox.pack(side=tk.LEFT, padx=(0, 5))
        for t in choice.get('excluded_traits', []):
            choice_exc_traits_listbox.insert(tk.END, t)
        ttk.Button(exc_traits_frame, text="Add", command=lambda: self._add_to_choice_listbox(choice_exc_traits_listbox)).pack(side=tk.LEFT, padx=2)
        ttk.Button(exc_traits_frame, text="Remove", command=lambda: choice_exc_traits_listbox.delete(tk.ANCHOR)).pack(side=tk.LEFT)
        row += 1
        
        ttk.Label(basic_scrollable, text="Trait Visibility:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        choice_trait_visibility_var = tk.StringVar(value=choice.get('trait_visibility', 'hide'))
        ttk.Combobox(basic_scrollable, textvariable=choice_trait_visibility_var, values=["hide", "blocked"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(basic_scrollable, text="(hide=not shown if req fail, blocked=shown locked)").grid(row=row, column=2, sticky="w", padx=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Blocked Message:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        choice_blocked_message_var = tk.StringVar(value=choice.get('blocked_message', ''))
        ttk.Entry(basic_scrollable, textvariable=choice_blocked_message_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # ========== MESSAGES SECTION ==========
        ttk.Label(basic_scrollable, text="Messages", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(15, 5))
        row += 1
        
        ttk.Label(basic_scrollable, text="Message (simple choices):").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        choice_message_text = scrolledtext.ScrolledText(basic_scrollable, width=60, height=3)
        choice_message_text.insert(1.0, choice.get('message', ''))
        choice_message_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Message Success:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        choice_message_success_text = scrolledtext.ScrolledText(basic_scrollable, width=60, height=4)
        choice_message_success_text.insert(1.0, choice.get('message_success', ''))
        choice_message_success_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Message Failure:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        choice_message_failure_text = scrolledtext.ScrolledText(basic_scrollable, width=60, height=4)
        choice_message_failure_text.insert(1.0, choice.get('message_failure', ''))
        choice_message_failure_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        ttk.Label(basic_scrollable, text="Use: [acting_worker] for worker name in messages").grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        basic_scrollable.columnconfigure(1, weight=1)
        
        effects_choice_frame = ttk.Frame(choice_notebook)
        choice_notebook.add(effects_choice_frame, text="Effects")
        
        effects_canvas = tk.Canvas(effects_choice_frame)
        effects_scrollbar = ttk.Scrollbar(effects_choice_frame, orient="vertical", command=effects_canvas.yview)
        effects_scrollable = ttk.Frame(effects_canvas)
        
        effects_scrollable.bind("<Configure>", lambda e: effects_canvas.configure(scrollregion=effects_canvas.bbox("all")))
        effects_canvas.create_window((0, 0), window=effects_scrollable, anchor="nw")
        effects_canvas.configure(yscrollcommand=effects_scrollbar.set)
        
        effects_canvas.pack(side="left", fill="both", expand=True)
        effects_scrollbar.pack(side="right", fill="y")
        
        # Effects directos
        ttk.Label(effects_scrollable, text="Direct Effects", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 5))
        
        effect_vars = {}
        effect_row = 1
        for effect_name in ['money', 'reputation', 'health', 'energy', 'joy']:
            ttk.Label(effects_scrollable, text=f"{effect_name.capitalize()}:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
            var = tk.StringVar(value=str(choice.get('effect', {}).get(effect_name, '')))
            ttk.Entry(effects_scrollable, textvariable=var, width=20).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
            effect_vars[effect_name] = var
            effect_row += 1

        # Helper to load trait fields
        def _parse_trait_fields(trait_value):
            name = ""
            duration = 0
            target = ""
            if isinstance(trait_value, dict):
                name = trait_value.get("name", "")
                duration = trait_value.get("duration", 0)
                target = trait_value.get("target", "")
            elif isinstance(trait_value, str):
                name = trait_value
            elif isinstance(trait_value, list) and trait_value:
                # Use first entry for display
                first = trait_value[0]
                if isinstance(first, dict):
                    name = first.get("name", "")
                    duration = first.get("duration", 0)
                    target = first.get("target", "")
                else:
                    name = first
            return name, duration, target

        # Trait list for dropdowns (optional)
        trait_names = []
        if isinstance(self.traits_data, list):
            trait_names = sorted([t.get("name", "") for t in self.traits_data if t.get("name")])

        # Direct add_trait
        direct_add_trait = choice.get('effect', {}).get('add_trait', '')
        direct_name, direct_duration, direct_target = _parse_trait_fields(direct_add_trait)
        ttk.Label(effects_scrollable, text="Add Trait (Direct):").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        direct_add_trait_var = tk.StringVar(value=direct_name)
        ttk.Combobox(effects_scrollable, textvariable=direct_add_trait_var, values=trait_names, width=25).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        ttk.Label(effects_scrollable, text="Duration (days):").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        direct_add_trait_duration_var = tk.IntVar(value=direct_duration)
        ttk.Spinbox(effects_scrollable, from_=0, to=9999, textvariable=direct_add_trait_duration_var, width=10).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        ttk.Label(effects_scrollable, text="Target:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        direct_add_trait_target_var = tk.StringVar(value=direct_target)
        ttk.Combobox(effects_scrollable, textvariable=direct_add_trait_target_var,
                     values=["", "random_worker", "random_worker_female", "random_worker_male", "selected_worker"], width=25).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        
        # Success effects
        ttk.Label(effects_scrollable, text="Success Effects", font=("Arial", 10, "bold")).grid(row=effect_row, column=0, columnspan=3, sticky="w", padx=5, pady=(20, 5))
        effect_row += 1
        
        success_effect = choice.get('effect', {}).get('success', {})
        success_vars = {}
        for effect_name in ['money', 'reputation', 'servant_health', 'servant_energy', 'servant_joy', 'rebelliousness']:
            display_name = effect_name.replace('servant_', '').capitalize()
            ttk.Label(effects_scrollable, text=f"{display_name}:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
            var = tk.StringVar(value=str(success_effect.get(effect_name, '')))
            ttk.Entry(effects_scrollable, textvariable=var, width=20).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
            success_vars[effect_name] = var
            effect_row += 1
        
        # Add trait on success
        success_add_trait = success_effect.get('add_trait', '')
        success_name, success_duration, success_target = _parse_trait_fields(success_add_trait)
        ttk.Label(effects_scrollable, text="Add Trait on Success:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        success_add_trait_var = tk.StringVar(value=success_name)
        ttk.Combobox(effects_scrollable, textvariable=success_add_trait_var, values=trait_names, width=25).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(effects_scrollable, text="(trait name)").grid(row=effect_row, column=2, sticky="w", padx=5)
        effect_row += 1
        ttk.Label(effects_scrollable, text="Duration (days):").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        success_add_trait_duration_var = tk.IntVar(value=success_duration)
        ttk.Spinbox(effects_scrollable, from_=0, to=9999, textvariable=success_add_trait_duration_var, width=10).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        ttk.Label(effects_scrollable, text="Target:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        success_add_trait_target_var = tk.StringVar(value=success_target)
        ttk.Combobox(effects_scrollable, textvariable=success_add_trait_target_var,
                     values=["", "random_worker", "random_worker_female", "random_worker_male", "selected_worker"], width=25).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        
        # Failure effects
        ttk.Label(effects_scrollable, text="Failure Effects", font=("Arial", 10, "bold")).grid(row=effect_row, column=0, columnspan=3, sticky="w", padx=5, pady=(20, 5))
        effect_row += 1
        
        failure_effect = choice.get('effect', {}).get('failure', {})
        failure_vars = {}
        for effect_name in ['money', 'reputation', 'servant_health', 'servant_energy', 'servant_joy', 'rebelliousness']:
            display_name = effect_name.replace('servant_', '').capitalize()
            ttk.Label(effects_scrollable, text=f"{display_name}:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
            var = tk.StringVar(value=str(failure_effect.get(effect_name, '')))
            ttk.Entry(effects_scrollable, textvariable=var, width=20).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
            failure_vars[effect_name] = var
            effect_row += 1

        # Add trait on failure
        failure_add_trait = failure_effect.get('add_trait', '')
        failure_name, failure_duration, failure_target = _parse_trait_fields(failure_add_trait)
        ttk.Label(effects_scrollable, text="Add Trait on Failure:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        failure_add_trait_var = tk.StringVar(value=failure_name)
        ttk.Combobox(effects_scrollable, textvariable=failure_add_trait_var, values=trait_names, width=25).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(effects_scrollable, text="(trait name)").grid(row=effect_row, column=2, sticky="w", padx=5)
        effect_row += 1
        ttk.Label(effects_scrollable, text="Duration (days):").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        failure_add_trait_duration_var = tk.IntVar(value=failure_duration)
        ttk.Spinbox(effects_scrollable, from_=0, to=9999, textvariable=failure_add_trait_duration_var, width=10).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        ttk.Label(effects_scrollable, text="Target:").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        failure_add_trait_target_var = tk.StringVar(value=failure_target)
        ttk.Combobox(effects_scrollable, textvariable=failure_add_trait_target_var,
                     values=["", "random_worker", "random_worker_female", "random_worker_male", "selected_worker"], width=25).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        
        # Success chance
        ttk.Label(effects_scrollable, text="Success Chance (0.0-1.0):").grid(row=effect_row, column=0, sticky="w", padx=5, pady=5)
        success_chance_var = tk.StringVar(value=str(choice.get('effect', {}).get('success_chance', '')))
        ttk.Entry(effects_scrollable, textvariable=success_chance_var, width=20).grid(row=effect_row, column=1, sticky="w", padx=5, pady=5)
        effect_row += 1
        
        # Skill Modifiers (direct)
        ttk.Label(effects_scrollable, text="Skill Modifiers (Skill: delta):", font=("Arial", 9, "bold")).grid(row=effect_row, column=0, columnspan=3, sticky="w", padx=5, pady=(15, 5))
        effect_row += 1
        choice_skill_mods_listbox = tk.Listbox(effects_scrollable, height=4, width=40)
        choice_skill_mods_listbox.grid(row=effect_row, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        for sk, val in choice.get('effect', {}).get('skill_modifiers', {}).items():
            choice_skill_mods_listbox.insert(tk.END, f"{sk}: {val:+d}")
        def add_skill_mod():
            w = tk.Toplevel(editor_window)
            w.title("Add Skill Modifier")
            ttk.Label(w, text="Skill:").grid(row=0, column=0, padx=5, pady=5)
            sv = tk.StringVar()
            ttk.Combobox(w, textvariable=sv, values=self.all_skills, width=20).grid(row=0, column=1, padx=5, pady=5)
            ttk.Label(w, text="Delta (+/-):").grid(row=1, column=0, padx=5, pady=5)
            vv = tk.IntVar(value=0)
            ttk.Spinbox(w, from_=-20, to=20, textvariable=vv, width=10).grid(row=1, column=1, padx=5, pady=5)
            def ok(): choice_skill_mods_listbox.insert(tk.END, f"{sv.get()}: {vv.get():+d}"); w.destroy()
            ttk.Button(w, text="Add", command=ok).grid(row=2, column=0, columnspan=2, pady=10)
        def remove_skill_mod():
            s = choice_skill_mods_listbox.curselection()
            if s: choice_skill_mods_listbox.delete(s[0])
        sk_btns = ttk.Frame(effects_scrollable)
        sk_btns.grid(row=effect_row, column=2, sticky="nw", padx=5)
        ttk.Button(sk_btns, text="Add", command=add_skill_mod).pack(pady=2)
        ttk.Button(sk_btns, text="Remove", command=remove_skill_mod).pack(pady=2)
        effect_row += 1
        
        # Botones
        buttons_frame = ttk.Frame(editor_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_choice():
            choice['option'] = choice_option_var.get()
            
            # Condition and skill check fields
            condition = choice_condition_var.get().strip()
            if condition:
                choice['condition'] = condition
            elif 'condition' in choice:
                del choice['condition']
            
            threshold = choice_threshold_var.get()
            if threshold > 0:
                choice['threshold'] = threshold
            elif 'threshold' in choice:
                del choice['threshold']
            
            required_trait = choice_required_trait_var.get().strip()
            if required_trait:
                choice['required_trait'] = required_trait
            elif 'required_trait' in choice:
                del choice['required_trait']
            
            choice['required_traits'] = [choice_req_traits_listbox.get(i) for i in range(choice_req_traits_listbox.size())]
            choice['excluded_traits'] = [choice_exc_traits_listbox.get(i) for i in range(choice_exc_traits_listbox.size())]
            tv = choice_trait_visibility_var.get()
            if tv and tv != 'hide':
                choice['trait_visibility'] = tv
            elif 'trait_visibility' in choice:
                del choice['trait_visibility']
            bm = choice_blocked_message_var.get().strip()
            if bm:
                choice['blocked_message'] = bm
            elif 'blocked_message' in choice:
                del choice['blocked_message']
            
            # Messages
            msg = choice_message_text.get(1.0, tk.END).strip()
            if msg:
                choice['message'] = msg
            elif 'message' in choice:
                del choice['message']
            
            msg_success = choice_message_success_text.get(1.0, tk.END).strip()
            if msg_success:
                choice['message_success'] = msg_success
            elif 'message_success' in choice:
                del choice['message_success']
            
            msg_failure = choice_message_failure_text.get(1.0, tk.END).strip()
            if msg_failure:
                choice['message_failure'] = msg_failure
            elif 'message_failure' in choice:
                del choice['message_failure']
            
            # Effects
            effect = {}

            def build_trait_payload(name_var, duration_var, target_var):
                name = name_var.get().strip()
                if not name:
                    return None
                duration = duration_var.get() if duration_var else 0
                target = target_var.get().strip() if target_var else ""
                if duration > 0 or target:
                    payload = {"name": name}
                    if duration > 0:
                        payload["duration"] = duration
                    if target:
                        payload["target"] = target
                    return payload
                return name
            
            # Direct effects
            for effect_name, var in effect_vars.items():
                value = var.get().strip()
                if value:
                    try:
                        effect[effect_name] = int(value) if '.' not in value else float(value)
                    except ValueError:
                        effect[effect_name] = value
            
            direct_trait_payload = build_trait_payload(
                direct_add_trait_var,
                direct_add_trait_duration_var,
                direct_add_trait_target_var
            )
            if direct_trait_payload is not None:
                effect["add_trait"] = direct_trait_payload
            
            skill_mods = {}
            for i in range(choice_skill_mods_listbox.size()):
                line = choice_skill_mods_listbox.get(i)
                if ':' in line:
                    sk, rest = line.split(':', 1)
                    try:
                        skill_mods[sk.strip()] = int(rest.strip().replace('+', ''))
                    except ValueError:
                        pass
            if skill_mods:
                effect["skill_modifiers"] = skill_mods
            
            # Success effects (including add_trait)
            success_trait_payload = build_trait_payload(
                success_add_trait_var,
                success_add_trait_duration_var,
                success_add_trait_target_var
            )
            if any(v.get().strip() for v in success_vars.values()) or success_trait_payload is not None:
                success_eff = {}
                for effect_name, var in success_vars.items():
                    value = var.get().strip()
                    if value:
                        try:
                            success_eff[effect_name] = int(value) if '.' not in value else float(value)
                        except ValueError:
                            success_eff[effect_name] = value
                if success_trait_payload is not None:
                    success_eff['add_trait'] = success_trait_payload
                if success_eff:
                    effect['success'] = success_eff
            
            # Failure effects
            failure_trait_payload = build_trait_payload(
                failure_add_trait_var,
                failure_add_trait_duration_var,
                failure_add_trait_target_var
            )
            if any(v.get().strip() for v in failure_vars.values()) or failure_trait_payload is not None:
                failure_eff = {}
                for effect_name, var in failure_vars.items():
                    value = var.get().strip()
                    if value:
                        try:
                            failure_eff[effect_name] = int(value) if '.' not in value else float(value)
                        except ValueError:
                            failure_eff[effect_name] = value
                if failure_trait_payload is not None:
                    failure_eff["add_trait"] = failure_trait_payload
                if failure_eff:
                    effect['failure'] = failure_eff
            
            # Success chance
            sc_value = success_chance_var.get().strip()
            if sc_value:
                try:
                    effect['success_chance'] = float(sc_value)
                except ValueError:
                    pass
            
            choice['effect'] = effect
            
            self.refresh_event_choices_list()
            self.has_unsaved_changes = True
            self.update_title()
            editor_window.destroy()
        
        ttk.Button(buttons_frame, text="Save", command=save_choice).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=editor_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_current_event_data(self):
        """Guardar datos del event actual"""
        if not self.current_event:
            return
        
        self.current_event['id'] = self.event_id_var.get()
        self.current_event['description'] = self.event_description_text.get(1.0, tk.END).strip()
        self.current_event['weight'] = self.event_weight_var.get()
        
        # Event Probability (optional, only save if > 0)
        event_probability = self.event_probability_var.get()
        if event_probability > 0:
            self.current_event['event_probability'] = event_probability
        elif 'event_probability' in self.current_event:
            # Remove if user set it to 0 (meaning "not set")
            del self.current_event['event_probability']
        
        self.current_event['nsfw'] = self.event_nsfw_var.get()
        self.current_event['event_music'] = self.event_music_var.get()
        self.current_event['background_image'] = self.event_bg_image_var.get()
        self.current_event['success_image'] = self.event_success_image_var.get()
        self.current_event['failure_image'] = self.event_failure_image_var.get()
        
        # Config
        # Note: limited: false = NOT affected by managers, limited: true = affected by managers
        self.current_event['limited'] = self.event_limited_var.get()
        if self.event_limited_var.get():
            self.current_event['max_occurrences'] = self.event_max_occurrences_var.get()
        self.current_event['cooldown_days'] = self.event_cooldown_var.get()
        self.current_event['worker_selection'] = self.event_worker_selection_var.get()
        worker_gender_req = self.event_worker_gender_var.get()
        if worker_gender_req and worker_gender_req != 'any':
            self.current_event['worker_gender_requirement'] = worker_gender_req
        else:
            self.current_event.pop('worker_gender_requirement', None)
        
        pg = self.event_player_gender_var.get().strip()
        if pg in ('male', 'female'):
            self.current_event['player_gender_requirement'] = pg
        else:
            self.current_event.pop('player_gender_requirement', None)
        
        self.current_event['requires_assigned_worker'] = self.event_requires_assigned_var.get()
        
        if hasattr(self, 'event_req_building_worker_traits_listbox'):
            self.current_event['required_building_worker_traits'] = [
                self.event_req_building_worker_traits_listbox.get(i) for i in range(self.event_req_building_worker_traits_listbox.size())
            ]
        if hasattr(self, 'event_req_active_professions_listbox'):
            self.current_event['required_active_professions'] = [
                self.event_req_active_professions_listbox.get(i).strip()
                for i in range(self.event_req_active_professions_listbox.size())
                if str(self.event_req_active_professions_listbox.get(i)).strip()
            ]
        if hasattr(self, 'event_forbidden_professions_listbox'):
            self.current_event['forbidden_active_professions'] = [
                self.event_forbidden_professions_listbox.get(i).strip()
                for i in range(self.event_forbidden_professions_listbox.size())
                if str(self.event_forbidden_professions_listbox.get(i)).strip()
            ]
        self.current_event.pop('required_building_traits', None)
        if hasattr(self, 'event_min_skill_var'):
            txt = (self.event_min_skill_var.get() or "").strip()
            if txt:
                try:
                    self.current_event['required_building_worker_min_skill'] = int(txt)
                except ValueError:
                    pass
            else:
                self.current_event.pop('required_building_worker_min_skill', None)
        if hasattr(self, 'event_worker_skill_name_var'):
            sn = (self.event_worker_skill_name_var.get() or "").strip()
            if sn:
                self.current_event['required_building_worker_skill'] = sn
            else:
                self.current_event.pop('required_building_worker_skill', None)
        
        # Building types
        building_types = []
        for i in range(self.event_building_types_listbox.size()):
            building_types.append(self.event_building_types_listbox.get(i))
        self.current_event['building_type'] = building_types
        
        self.refresh_events_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def show_event_help(self):
        """Mostrar ayuda para events"""
        help_text = """
EVENT EDITOR HELP (v5.3)

Basic Information:
- ID: Unique event identifier
- Description: Event description text (use [acting_worker] for worker name)
- Weight: Event probability weight (1-10) - relative probability among events
- Event Probability (%): Absolute probability (0-100). 
  * 0 = Not set (default behavior, affected by managers)
  * 1-100 = Set probability (event is NOT affected by managers, priority event)
- NSFW: Mark if event is NSFW content
- Event Music: Music file path
- Background/Success/Failure Images: Image file paths

Configuration:
- Limited Event: 
  * UNCHECKED (limited: false) = Event is NOT affected by managers (priority event)
  * CHECKED (limited: true) = Event IS affected by managers (normal event)
  Note: Events with event_probability set are ALWAYS priority (not affected by managers)
- Max Occurrences: Maximum times event can occur (if limited)
- Cooldown Days: Days before event can occur again
- Worker Selection: How worker is selected (choose/none/random)
- Worker Gender Requirement: Required worker gender (any/male/female)
- Building Types: Buildings where event can occur

Choices (v5.2 Enhanced):
- Option Text: Text shown to player
- Condition: Skill name for skill check (Combat, Charm, Clever, etc.) or "building_skill"
- Threshold: Minimum skill level (0 = no minimum, worker meets threshold = better chances)
- Required Trait: Worker MUST have this trait to select this choice
- Messages: message (simple), message_success, message_failure
- Effects (Direct/Success/Failure):
  * money, reputation: Manager resources
  * servant_health, servant_energy, servant_joy: Worker stats
  * rebelliousness: Worker rebelliousness change
  * add_trait: Trait to add (supports duration and target)

Example skill check choice:
- Condition: "Combat", Threshold: 60, Required Trait: ""
- Worker needs Combat skill, if Combat >= 60 they get better success chances
- Add "Blademaster" trait on success

Variables in messages: [acting_worker]
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Event Editor Help")
        help_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def load_events_file_dialog(self):
        """Cargar archivo de events"""
        initial = self.get_initial_dir("data/events")
        
        file_path = filedialog.askopenfilename(
            title="Load Events File",
            initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for event in data:
                        if 'id' in event:
                            self.events_data[event['id']] = event
                    self.refresh_events_list()
                    messagebox.showinfo("Success", f"Loaded {len(data)} events")
                elif isinstance(data, dict):
                    self.events_data.update(data)
                    self.refresh_events_list()
                    messagebox.showinfo("Success", f"Loaded {len(data)} events")
                else:
                    messagebox.showerror("Error", "Invalid file format")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")
    
    def save_events_as(self):
        """Guardar events en archivo específico"""
        if not self.events_data:
            messagebox.showwarning("Warning", "No events to save")
            return
        
        initial = self.get_initial_dir("data/events")
        
        file_path = filedialog.asksaveasfilename(
            title="Save Events As...",
            initialdir=initial,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if os.path.exists(file_path):
                if not messagebox.askyesno("Confirm Overwrite", f"File {Path(file_path).name} already exists.\n\nOverwrite it?"):
                    return
            
            try:
                events_list = list(self.events_data.values())
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(events_list, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Saved {len(events_list)} events")
                self.has_unsaved_changes = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def save_events(self):
        """Guardar events (con confirmación)"""
        if not self.events_data:
            messagebox.showwarning("Warning", "No events to save")
            return
        
        if not self.game_directory:
            messagebox.showwarning("Warning", "Please select game directory first")
            return
        
        messagebox.showwarning("Info", "Events are stored in multiple files.\nUse 'Save Events As...' to save to a specific file.")
    
    # ==================== INTERACTIONS TAB ====================
    
    def setup_interactions_tab(self):
        """Configurar pestaña de Interactions"""
        interactions_frame = ttk.Frame(self.notebook)
        self.notebook.add(interactions_frame, text="Interactions")
        
        main_frame = ttk.Frame(interactions_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="Interactions List", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        self.interactions_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.interactions_listbox.pack(fill=tk.BOTH, expand=True)
        self.interactions_listbox.bind('<<ListboxSelect>>', self.on_interaction_select)
        
        interactions_buttons_frame = ttk.Frame(left_frame)
        interactions_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(interactions_buttons_frame, text="Load Interactions File", command=self.load_interactions_file_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(interactions_buttons_frame, text="Save Interactions As...", command=self.save_interactions_as).pack(fill=tk.X, pady=2)
        ttk.Button(interactions_buttons_frame, text="Save Interactions", command=self.save_interactions).pack(fill=tk.X, pady=2)
        ttk.Separator(interactions_buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(interactions_buttons_frame, text="Save Current Interaction", command=self.save_current_interaction_data).pack(fill=tk.X, pady=2)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        interaction_header_frame = ttk.Frame(right_frame)
        interaction_header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(interaction_header_frame, text="Interaction Editor", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(interaction_header_frame, text="? Help", command=self.show_interaction_help).pack(side=tk.RIGHT)
        
        self.interaction_notebook = ttk.Notebook(right_frame)
        self.interaction_notebook.pack(fill=tk.BOTH, expand=True)
        
        basic_interaction_frame = ttk.Frame(self.interaction_notebook)
        self.interaction_notebook.add(basic_interaction_frame, text="Basic Information")
        self.setup_interaction_basic_fields(basic_interaction_frame)
        
        effects_interaction_frame = ttk.Frame(self.interaction_notebook)
        self.interaction_notebook.add(effects_interaction_frame, text="Effects & Requirements")
        self.setup_interaction_effects_fields(effects_interaction_frame)
    
    def refresh_interactions_list(self):
        """Actualizar lista de interactions"""
        if hasattr(self, 'interactions_listbox'):
            self.interactions_listbox.delete(0, tk.END)
            for interaction in self.interactions_data:
                name = interaction.get('name', interaction.get('id', 'Unknown'))
                self.interactions_listbox.insert(tk.END, name)
    
    def on_interaction_select(self, event):
        """Manejar selección de interaction"""
        selection = self.interactions_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_interaction = self.interactions_data[index]
            self.load_interaction_data()
    
    def setup_interaction_basic_fields(self, parent):
        """Configurar campos básicos del interaction"""
        interaction_canvas = tk.Canvas(parent)
        interaction_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=interaction_canvas.yview)
        interaction_scrollable = ttk.Frame(interaction_canvas)
        
        interaction_scrollable.bind("<Configure>", lambda e: interaction_canvas.configure(scrollregion=interaction_canvas.bbox("all")))
        interaction_canvas.create_window((0, 0), window=interaction_scrollable, anchor="nw")
        interaction_canvas.configure(yscrollcommand=interaction_scrollbar.set)
        
        interaction_canvas.pack(side="left", fill="both", expand=True)
        interaction_scrollbar.pack(side="right", fill="y")
        
        row = 0
        
        # ID
        ttk.Label(interaction_scrollable, text="ID:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.interaction_id_var = tk.StringVar()
        ttk.Entry(interaction_scrollable, textvariable=self.interaction_id_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Name
        ttk.Label(interaction_scrollable, text="Name:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.interaction_name_var = tk.StringVar()
        ttk.Entry(interaction_scrollable, textvariable=self.interaction_name_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Description
        ttk.Label(interaction_scrollable, text="Description:").grid(row=row, column=0, sticky="nw", padx=5, pady=5)
        self.interaction_description_text = scrolledtext.ScrolledText(interaction_scrollable, width=50, height=4)
        self.interaction_description_text.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # Image
        ttk.Label(interaction_scrollable, text="Image:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.interaction_image_var = tk.StringVar()
        ttk.Entry(interaction_scrollable, textvariable=self.interaction_image_var, width=50).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # NSFW
        self.interaction_nsfw_var = tk.BooleanVar()
        ttk.Checkbutton(interaction_scrollable, text="NSFW", variable=self.interaction_nsfw_var).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Gender Filter
        ttk.Label(interaction_scrollable, text="Gender Filter:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.interaction_gender_filter_var = tk.StringVar(value="any")
        ttk.Combobox(interaction_scrollable, textvariable=self.interaction_gender_filter_var, values=["any", "male", "female"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Worker Gender
        ttk.Label(interaction_scrollable, text="Worker Gender:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.interaction_worker_gender_var = tk.StringVar(value="any")
        ttk.Combobox(interaction_scrollable, textvariable=self.interaction_worker_gender_var, values=["any", "male", "female"], state="readonly", width=15).grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1
        
        # Costs
        ttk.Label(interaction_scrollable, text="Costs", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        costs_frame = ttk.Frame(interaction_scrollable)
        costs_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(costs_frame, text="Energy:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.interaction_cost_energy_var = tk.IntVar(value=0)
        ttk.Spinbox(costs_frame, from_=0, to=10, textvariable=self.interaction_cost_energy_var, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(costs_frame, text="Health:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.interaction_cost_health_var = tk.IntVar(value=0)
        ttk.Spinbox(costs_frame, from_=0, to=10, textvariable=self.interaction_cost_health_var, width=10).grid(row=0, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(costs_frame, text="Money:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.interaction_cost_money_var = tk.IntVar(value=0)
        ttk.Spinbox(costs_frame, from_=0, to=1000, textvariable=self.interaction_cost_money_var, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        row += 1
        
        # Categories
        ttk.Label(interaction_scrollable, text="Categories", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        categories_frame = ttk.Frame(interaction_scrollable)
        categories_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.interaction_categories_listbox = tk.Listbox(categories_frame, height=4)
        self.interaction_categories_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        categories_buttons = ttk.Frame(categories_frame)
        categories_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(categories_buttons, text="Add", command=self.add_interaction_category).pack(pady=2)
        ttk.Button(categories_buttons, text="Remove", command=self.remove_interaction_category).pack(pady=2)
        
        interaction_scrollable.columnconfigure(1, weight=1)
    
    def setup_interaction_effects_fields(self, parent):
        """Configurar campos de effects y requirements del interaction"""
        interaction_canvas = tk.Canvas(parent)
        interaction_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=interaction_canvas.yview)
        interaction_scrollable = ttk.Frame(interaction_canvas)
        
        interaction_scrollable.bind("<Configure>", lambda e: interaction_canvas.configure(scrollregion=interaction_canvas.bbox("all")))
        interaction_canvas.create_window((0, 0), window=interaction_scrollable, anchor="nw")
        interaction_canvas.configure(yscrollcommand=interaction_scrollbar.set)
        
        interaction_canvas.pack(side="left", fill="both", expand=True)
        interaction_scrollbar.pack(side="right", fill="y")
        
        row = 0
        
        # Stat Modifications (Effects)
        ttk.Label(interaction_scrollable, text="Stat Modifications (Effects)", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 5))
        row += 1
        
        stat_mods_frame = ttk.Frame(interaction_scrollable)
        stat_mods_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.interaction_stat_mods_listbox = tk.Listbox(stat_mods_frame, height=6)
        self.interaction_stat_mods_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        stat_mods_buttons = ttk.Frame(stat_mods_frame)
        stat_mods_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(stat_mods_buttons, text="Add", command=self.add_stat_modification).pack(pady=2)
        ttk.Button(stat_mods_buttons, text="Edit", command=self.edit_stat_modification).pack(pady=2)
        ttk.Button(stat_mods_buttons, text="Remove", command=self.remove_stat_modification).pack(pady=2)
        row += 1
        
        # Stat Requirements
        ttk.Label(interaction_scrollable, text="Stat Requirements", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        stat_reqs_frame = ttk.Frame(interaction_scrollable)
        stat_reqs_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.interaction_stat_reqs_listbox = tk.Listbox(stat_reqs_frame, height=4)
        self.interaction_stat_reqs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        stat_reqs_buttons = ttk.Frame(stat_reqs_frame)
        stat_reqs_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(stat_reqs_buttons, text="Add", command=self.add_stat_requirement).pack(pady=2)
        ttk.Button(stat_reqs_buttons, text="Edit", command=self.edit_stat_requirement).pack(pady=2)
        ttk.Button(stat_reqs_buttons, text="Remove", command=self.remove_stat_requirement).pack(pady=2)
        row += 1
        
        # Required Flags
        ttk.Label(interaction_scrollable, text="Required Flags", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        req_flags_frame = ttk.Frame(interaction_scrollable)
        req_flags_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.interaction_req_flags_listbox = tk.Listbox(req_flags_frame, height=3)
        self.interaction_req_flags_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        req_flags_buttons = ttk.Frame(req_flags_frame)
        req_flags_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(req_flags_buttons, text="Add", command=self.add_required_flag_interaction).pack(pady=2)
        ttk.Button(req_flags_buttons, text="Remove", command=self.remove_required_flag_interaction).pack(pady=2)
        row += 1
        
        # Excluded Flags
        ttk.Label(interaction_scrollable, text="Excluded Flags", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=5, pady=(20, 5))
        row += 1
        
        exc_flags_frame = ttk.Frame(interaction_scrollable)
        exc_flags_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.interaction_exc_flags_listbox = tk.Listbox(exc_flags_frame, height=3)
        self.interaction_exc_flags_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        exc_flags_buttons = ttk.Frame(exc_flags_frame)
        exc_flags_buttons.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Button(exc_flags_buttons, text="Add", command=self.add_excluded_flag_interaction).pack(pady=2)
        ttk.Button(exc_flags_buttons, text="Remove", command=self.remove_excluded_flag_interaction).pack(pady=2)
        
        interaction_scrollable.columnconfigure(1, weight=1)
    
    def load_interaction_data(self):
        """Cargar datos del interaction seleccionado"""
        if not self.current_interaction:
            return
        
        self.interaction_id_var.set(self.current_interaction.get('id', ''))
        self.interaction_name_var.set(self.current_interaction.get('name', ''))
        self.interaction_description_text.delete(1.0, tk.END)
        self.interaction_description_text.insert(1.0, self.current_interaction.get('description', ''))
        self.interaction_image_var.set(self.current_interaction.get('image', ''))
        self.interaction_nsfw_var.set(self.current_interaction.get('nsfw', False))
        self.interaction_gender_filter_var.set(self.current_interaction.get('gender_filter') or 'any')
        self.interaction_worker_gender_var.set(self.current_interaction.get('worker_gender', 'any'))
        
        # Costs
        self.interaction_cost_energy_var.set(self.current_interaction.get('cost_energy', 0))
        self.interaction_cost_health_var.set(self.current_interaction.get('cost_health', 0))
        self.interaction_cost_money_var.set(self.current_interaction.get('cost_money', 0))
        
        # Categories
        self.interaction_categories_listbox.delete(0, tk.END)
        for cat in self.current_interaction.get('categories', []):
            self.interaction_categories_listbox.insert(tk.END, cat)
        
        # Stat modifications
        self.refresh_stat_modifications_list()
        
        # Stat requirements
        self.refresh_stat_requirements_list()
        
        # Flags
        self.refresh_required_flags_list()
        self.refresh_excluded_flags_list()
    
    def refresh_stat_modifications_list(self):
        """Actualizar lista de stat modifications"""
        if hasattr(self, 'interaction_stat_mods_listbox'):
            self.interaction_stat_mods_listbox.delete(0, tk.END)
            if self.current_interaction:
                effect = self.current_interaction.get('effect', {})
                for stat, value in effect.items():
                    if stat != 'flags':
                        self.interaction_stat_mods_listbox.insert(tk.END, f"{stat}: {value}")
    
    def refresh_stat_requirements_list(self):
        """Actualizar lista de stat requirements"""
        if hasattr(self, 'interaction_stat_reqs_listbox'):
            self.interaction_stat_reqs_listbox.delete(0, tk.END)
            if self.current_interaction:
                stat_reqs = self.current_interaction.get('stat_requirements', {})
                for stat, value in stat_reqs.items():
                    self.interaction_stat_reqs_listbox.insert(tk.END, f"{stat}: {value}")
    
    def refresh_required_flags_list(self):
        """Actualizar lista de required flags"""
        if hasattr(self, 'interaction_req_flags_listbox'):
            self.interaction_req_flags_listbox.delete(0, tk.END)
            if self.current_interaction:
                req_flags = self.current_interaction.get('required_flags', {})
                for flag, value in req_flags.items():
                    if isinstance(value, dict):
                        self.interaction_req_flags_listbox.insert(tk.END, f"{flag}: {value.get('value')} (duration: {value.get('duration', -1)})")
                    else:
                        self.interaction_req_flags_listbox.insert(tk.END, f"{flag}: {value}")
    
    def refresh_excluded_flags_list(self):
        """Actualizar lista de excluded flags"""
        if hasattr(self, 'interaction_exc_flags_listbox'):
            self.interaction_exc_flags_listbox.delete(0, tk.END)
            if self.current_interaction:
                exc_flags = self.current_interaction.get('excluded_flags', {})
                for flag, value in exc_flags.items():
                    self.interaction_exc_flags_listbox.insert(tk.END, f"{flag}: {value}")
    
    def add_interaction_category(self):
        """Agregar category al interaction"""
        category = simpledialog.askstring("Add Category", "Enter category name:")
        if category:
            self.interaction_categories_listbox.insert(tk.END, category)
    
    def remove_interaction_category(self):
        """Quitar category del interaction"""
        selection = self.interaction_categories_listbox.curselection()
        if selection:
            self.interaction_categories_listbox.delete(selection[0])
    
    def add_stat_modification(self):
        """Agregar stat modification"""
        mod_window = tk.Toplevel(self.root)
        mod_window.title("Add Stat Modification")
        mod_window.geometry("300x150")
        
        ttk.Label(mod_window, text="Stat:").grid(row=0, column=0, padx=5, pady=5)
        stat_var = tk.StringVar()
        ttk.Entry(mod_window, textvariable=stat_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(mod_window, text="Value:").grid(row=1, column=0, padx=5, pady=5)
        value_var = tk.StringVar()
        ttk.Entry(mod_window, textvariable=value_var, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        def add_mod():
            stat = stat_var.get().strip()
            value = value_var.get().strip()
            if stat and value:
                try:
                    value_num = int(value) if '.' not in value else float(value)
                    self.interaction_stat_mods_listbox.insert(tk.END, f"{stat}: {value_num}")
                except ValueError:
                    self.interaction_stat_mods_listbox.insert(tk.END, f"{stat}: {value}")
            mod_window.destroy()
        
        ttk.Button(mod_window, text="Add", command=add_mod).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(mod_window, text="Cancel", command=mod_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def edit_stat_modification(self):
        """Editar stat modification seleccionada"""
        selection = self.interaction_stat_mods_listbox.curselection()
        if not selection:
            return
        
        current = self.interaction_stat_mods_listbox.get(selection[0])
        parts = current.split(': ', 1)
        if len(parts) != 2:
            return
        
        mod_window = tk.Toplevel(self.root)
        mod_window.title("Edit Stat Modification")
        mod_window.geometry("300x150")
        
        ttk.Label(mod_window, text="Stat:").grid(row=0, column=0, padx=5, pady=5)
        stat_var = tk.StringVar(value=parts[0])
        ttk.Entry(mod_window, textvariable=stat_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(mod_window, text="Value:").grid(row=1, column=0, padx=5, pady=5)
        value_var = tk.StringVar(value=parts[1])
        ttk.Entry(mod_window, textvariable=value_var, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        def save_mod():
            stat = stat_var.get().strip()
            value = value_var.get().strip()
            if stat and value:
                try:
                    value_num = int(value) if '.' not in value else float(value)
                    self.interaction_stat_mods_listbox.delete(selection[0])
                    self.interaction_stat_mods_listbox.insert(selection[0], f"{stat}: {value_num}")
                except ValueError:
                    self.interaction_stat_mods_listbox.delete(selection[0])
                    self.interaction_stat_mods_listbox.insert(selection[0], f"{stat}: {value}")
            mod_window.destroy()
        
        ttk.Button(mod_window, text="Save", command=save_mod).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(mod_window, text="Cancel", command=mod_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def remove_stat_modification(self):
        """Quitar stat modification"""
        selection = self.interaction_stat_mods_listbox.curselection()
        if selection:
            self.interaction_stat_mods_listbox.delete(selection[0])
    
    def add_stat_requirement(self):
        """Agregar stat requirement"""
        req_window = tk.Toplevel(self.root)
        req_window.title("Add Stat Requirement")
        req_window.geometry("300x150")
        
        ttk.Label(req_window, text="Stat:").grid(row=0, column=0, padx=5, pady=5)
        stat_var = tk.StringVar()
        ttk.Entry(req_window, textvariable=stat_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(req_window, text="Min Value:").grid(row=1, column=0, padx=5, pady=5)
        value_var = tk.StringVar()
        ttk.Entry(req_window, textvariable=value_var, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        def add_req():
            stat = stat_var.get().strip()
            value = value_var.get().strip()
            if stat and value:
                try:
                    value_num = int(value) if '.' not in value else float(value)
                    self.interaction_stat_reqs_listbox.insert(tk.END, f"{stat}: {value_num}")
                except ValueError:
                    self.interaction_stat_reqs_listbox.insert(tk.END, f"{stat}: {value}")
            req_window.destroy()
        
        ttk.Button(req_window, text="Add", command=add_req).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(req_window, text="Cancel", command=req_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def edit_stat_requirement(self):
        """Editar stat requirement seleccionada"""
        selection = self.interaction_stat_reqs_listbox.curselection()
        if not selection:
            return
        
        current = self.interaction_stat_reqs_listbox.get(selection[0])
        parts = current.split(': ', 1)
        if len(parts) != 2:
            return
        
        req_window = tk.Toplevel(self.root)
        req_window.title("Edit Stat Requirement")
        req_window.geometry("300x150")
        
        ttk.Label(req_window, text="Stat:").grid(row=0, column=0, padx=5, pady=5)
        stat_var = tk.StringVar(value=parts[0])
        ttk.Entry(req_window, textvariable=stat_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(req_window, text="Min Value:").grid(row=1, column=0, padx=5, pady=5)
        value_var = tk.StringVar(value=parts[1])
        ttk.Entry(req_window, textvariable=value_var, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        def save_req():
            stat = stat_var.get().strip()
            value = value_var.get().strip()
            if stat and value:
                try:
                    value_num = int(value) if '.' not in value else float(value)
                    self.interaction_stat_reqs_listbox.delete(selection[0])
                    self.interaction_stat_reqs_listbox.insert(selection[0], f"{stat}: {value_num}")
                except ValueError:
                    self.interaction_stat_reqs_listbox.delete(selection[0])
                    self.interaction_stat_reqs_listbox.insert(selection[0], f"{stat}: {value}")
            req_window.destroy()
        
        ttk.Button(req_window, text="Save", command=save_req).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(req_window, text="Cancel", command=req_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def remove_stat_requirement(self):
        """Quitar stat requirement"""
        selection = self.interaction_stat_reqs_listbox.curselection()
        if selection:
            self.interaction_stat_reqs_listbox.delete(selection[0])
    
    def add_required_flag_interaction(self):
        """Agregar required flag"""
        flag_window = tk.Toplevel(self.root)
        flag_window.title("Add Required Flag")
        flag_window.geometry("300x200")
        
        ttk.Label(flag_window, text="Flag Name:").grid(row=0, column=0, padx=5, pady=5)
        flag_name_var = tk.StringVar()
        ttk.Entry(flag_window, textvariable=flag_name_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(flag_window, text="Value:").grid(row=1, column=0, padx=5, pady=5)
        flag_value_var = tk.StringVar(value="true")
        ttk.Entry(flag_window, textvariable=flag_value_var, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(flag_window, text="Duration (-1 for permanent):").grid(row=2, column=0, padx=5, pady=5)
        flag_duration_var = tk.StringVar(value="-1")
        ttk.Entry(flag_window, textvariable=flag_duration_var, width=20).grid(row=2, column=1, padx=5, pady=5)
        
        def add_flag():
            name = flag_name_var.get().strip()
            value = flag_value_var.get().strip()
            duration = flag_duration_var.get().strip()
            if name:
                try:
                    duration_num = int(duration)
                    if duration_num != -1:
                        self.interaction_req_flags_listbox.insert(tk.END, f"{name}: {value} (duration: {duration_num})")
                    else:
                        self.interaction_req_flags_listbox.insert(tk.END, f"{name}: {value}")
                except ValueError:
                    self.interaction_req_flags_listbox.insert(tk.END, f"{name}: {value}")
            flag_window.destroy()
        
        ttk.Button(flag_window, text="Add", command=add_flag).grid(row=3, column=0, padx=5, pady=10)
        ttk.Button(flag_window, text="Cancel", command=flag_window.destroy).grid(row=3, column=1, padx=5, pady=10)
    
    def remove_required_flag_interaction(self):
        """Quitar required flag"""
        selection = self.interaction_req_flags_listbox.curselection()
        if selection:
            self.interaction_req_flags_listbox.delete(selection[0])
    
    def add_excluded_flag_interaction(self):
        """Agregar excluded flag"""
        flag_window = tk.Toplevel(self.root)
        flag_window.title("Add Excluded Flag")
        flag_window.geometry("300x150")
        
        ttk.Label(flag_window, text="Flag Name:").grid(row=0, column=0, padx=5, pady=5)
        flag_name_var = tk.StringVar()
        ttk.Entry(flag_window, textvariable=flag_name_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(flag_window, text="Value:").grid(row=1, column=0, padx=5, pady=5)
        flag_value_var = tk.StringVar(value="true")
        ttk.Entry(flag_window, textvariable=flag_value_var, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        def add_flag():
            name = flag_name_var.get().strip()
            value = flag_value_var.get().strip()
            if name:
                self.interaction_exc_flags_listbox.insert(tk.END, f"{name}: {value}")
            flag_window.destroy()
        
        ttk.Button(flag_window, text="Add", command=add_flag).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(flag_window, text="Cancel", command=flag_window.destroy).grid(row=2, column=1, padx=5, pady=10)
    
    def remove_excluded_flag_interaction(self):
        """Quitar excluded flag"""
        selection = self.interaction_exc_flags_listbox.curselection()
        if selection:
            self.interaction_exc_flags_listbox.delete(selection[0])
    
    def save_current_interaction_data(self):
        """Guardar datos del interaction actual"""
        if not self.current_interaction:
            return
        
        self.current_interaction['id'] = self.interaction_id_var.get()
        self.current_interaction['name'] = self.interaction_name_var.get()
        self.current_interaction['description'] = self.interaction_description_text.get(1.0, tk.END).strip()
        self.current_interaction['image'] = self.interaction_image_var.get()
        self.current_interaction['nsfw'] = self.interaction_nsfw_var.get()
        gender_filter = self.interaction_gender_filter_var.get()
        if gender_filter != 'any':
            self.current_interaction['gender_filter'] = gender_filter if gender_filter != 'any' else None
        self.current_interaction['worker_gender'] = self.interaction_worker_gender_var.get()
        
        # Costs
        if self.interaction_cost_energy_var.get() > 0:
            self.current_interaction['cost_energy'] = self.interaction_cost_energy_var.get()
        if self.interaction_cost_health_var.get() > 0:
            self.current_interaction['cost_health'] = self.interaction_cost_health_var.get()
        if self.interaction_cost_money_var.get() > 0:
            self.current_interaction['cost_money'] = self.interaction_cost_money_var.get()
        
        # Categories
        categories = []
        for i in range(self.interaction_categories_listbox.size()):
            categories.append(self.interaction_categories_listbox.get(i))
        self.current_interaction['categories'] = categories
        
        # Stat modifications
        effect = {}
        for i in range(self.interaction_stat_mods_listbox.size()):
            mod_str = self.interaction_stat_mods_listbox.get(i)
            parts = mod_str.split(': ', 1)
            if len(parts) == 2:
                stat = parts[0]
                try:
                    effect[stat] = int(parts[1]) if '.' not in parts[1] else float(parts[1])
                except ValueError:
                    effect[stat] = parts[1]
        self.current_interaction['effect'] = effect
        
        # Stat requirements
        stat_reqs = {}
        for i in range(self.interaction_stat_reqs_listbox.size()):
            req_str = self.interaction_stat_reqs_listbox.get(i)
            parts = req_str.split(': ', 1)
            if len(parts) == 2:
                stat = parts[0]
                try:
                    stat_reqs[stat] = int(parts[1]) if '.' not in parts[1] else float(parts[1])
                except ValueError:
                    stat_reqs[stat] = parts[1]
        self.current_interaction['stat_requirements'] = stat_reqs
        
        # Required flags
        req_flags = {}
        for i in range(self.interaction_req_flags_listbox.size()):
            flag_str = self.interaction_req_flags_listbox.get(i)
            if ': ' in flag_str:
                parts = flag_str.split(': ', 1)
                flag_name = parts[0]
                value_part = parts[1]
                if ' (duration: ' in value_part:
                    value_str, duration_str = value_part.split(' (duration: ', 1)
                    duration = int(duration_str.rstrip(')'))
                    req_flags[flag_name] = {'value': value_str, 'duration': duration}
                else:
                    req_flags[flag_name] = value_part
        self.current_interaction['required_flags'] = req_flags
        
        # Excluded flags
        exc_flags = {}
        for i in range(self.interaction_exc_flags_listbox.size()):
            flag_str = self.interaction_exc_flags_listbox.get(i)
            if ': ' in flag_str:
                parts = flag_str.split(': ', 1)
                exc_flags[parts[0]] = parts[1]
        self.current_interaction['excluded_flags'] = exc_flags
        
        self.refresh_interactions_list()
        self.has_unsaved_changes = True
        self.update_title()
    
    def show_interaction_help(self):
        """Mostrar ayuda para interactions"""
        help_text = """
INTERACTION EDITOR HELP

Basic Information:
- ID: Unique interaction identifier
- Name: Interaction display name
- Description: Interaction description text
- Image: Image file path
- NSFW: Mark if interaction is NSFW content
- Gender Filter: Player gender filter (any/male/female)
- Worker Gender: Required worker gender (any/male/female)
- Costs: Energy, Health, and Money costs
- Categories: Interaction categories

Effects & Requirements:
- Stat Modifications: Stats modified by this interaction
- Stat Requirements: Minimum stat values required
- Required Flags: Flags that must be present
- Excluded Flags: Flags that must NOT be present
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Interaction Editor Help")
        help_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def load_interactions_file_dialog(self):
        """Cargar archivo de interactions"""
        initial = self.get_initial_dir("data/interactions")
        
        file_path = filedialog.askopenfilename(
            title="Load Interactions File",
            initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    self.interactions_data = data
                    self.refresh_interactions_list()
                    messagebox.showinfo("Success", f"Loaded {len(data)} interactions")
                else:
                    messagebox.showerror("Error", "Invalid file format. Expected a JSON array.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file:\n{str(e)}")
    
    def save_interactions_as(self):
        """Guardar interactions en archivo específico"""
        if not self.interactions_data:
            messagebox.showwarning("Warning", "No interactions to save")
            return
        
        initial = self.get_initial_dir("data/interactions")
        
        file_path = filedialog.asksaveasfilename(
            title="Save Interactions As...",
            initialdir=initial,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if os.path.exists(file_path):
                if not messagebox.askyesno("Confirm Overwrite", f"File {Path(file_path).name} already exists.\n\nOverwrite it?"):
                    return
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.interactions_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Saved {len(self.interactions_data)} interactions")
                self.has_unsaved_changes = False
                self.update_title()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file:\n{str(e)}")
    
    def save_interactions(self):
        """Guardar interactions (con confirmación)"""
        if not self.interactions_data:
            messagebox.showwarning("Warning", "No interactions to save")
            return
        
        if not self.game_directory:
            messagebox.showwarning("Warning", "Please select game directory first")
            return
        
        messagebox.showwarning("Info", "Interactions are stored in multiple files.\nUse 'Save Interactions As...' to save to a specific file.")


def main():
    root = tk.Tk()
    app = FantasyManagerEditorV6(root)
    root.mainloop()


if __name__ == "__main__":
    main()

