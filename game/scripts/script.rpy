# script.rpy
# Fantasy Management Simulator - Full Version with Video Support


init python:
    if not hasattr(store, 'pending_exit'):
        store.pending_exit = False
    # Remove aggressive context popper to avoid UI glitches on quit

    def _set_pending_exit_if_quitting(message):
        try:
            if isinstance(message, str) and message.lower().find("quit") != -1:
                store.pending_exit = True
        except Exception:
            store.pending_exit = True

    def _quit_now():
        try:
            from renpy import exports as rpy
            rpy.quit()
        except Exception:
            pass
    
    config.log = "log.txt"  # Force log file
    config.developer = True  # restore original dev setting
    
    import random
    import hashlib
    import re
    import os
    import json

    #############################
    # Constants
    #############################
    SKILL_MAX = 100  # Cap for base worker skills (used by modify_base_skill, use_item, etc.)

    #############################
    # Event Success Configuration
    #############################
    # Base success bonus added to all skill-based event checks
    # This increases the baseline success chance for all events
    EVENT_SUCCESS_BASE_BONUS_WORKER = 30  # Easy baseline (+30)
    EVENT_SUCCESS_BASE_BONUS_BUILDING = 50  # Easy baseline (+50)
    EVENT_SUCCESS_MIN_CHANCE = 0.6  # Easy baseline minimum success chance (60%)

    def get_event_success_bonus_worker():
        """Difficulty-scaled worker baseline bonus for event checks."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 5
        if diff == "hard":
            return 15
        if diff == "normal":
            return 22
        # Keep easy/story unchanged as requested.
        return EVENT_SUCCESS_BASE_BONUS_WORKER

    def get_event_success_bonus_building():
        """Difficulty-scaled building baseline bonus for event checks."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 20
        if diff == "hard":
            return 30
        if diff == "normal":
            return 40
        # Keep easy/story unchanged as requested.
        return EVENT_SUCCESS_BASE_BONUS_BUILDING

    def get_event_success_min_chance():
        """Difficulty-scaled minimum success chance for probability-based events."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 0.35
        if diff == "hard":
            return 0.45
        if diff == "normal":
            return 0.55
        # Keep easy/story unchanged as requested.
        return EVENT_SUCCESS_MIN_CHANCE

    def get_difficulty_loot_multiplier():
        """Difficulty-scaled loot chance multiplier."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 0.50
        if diff == "hard":
            return 0.75
        return 1.00

    #############################
    # Helper Functions & Loading
    #############################

    def get_building_multipliers(building):
        """
        Calculate multipliers based on building level.
        
        *** ONLY APPLIES TO RANDOM EVENTS, NOT DAILY WORKER EARNINGS ***
        
        Building Level Bonuses for Random Events:
        - Level 1: No bonus (1.0x)
        - Level 2: Money +50%, Reputation +30% (1.5x money, 1.3x reputation)
        - Level 3: Money +100%, Reputation +60% (2.0x money, 1.6x reputation)
        - Level 4: Money +150%, Reputation +90% (2.5x money, 1.9x reputation)
        - Level 5: Money +200%, Reputation +120% (3.0x money, 2.2x reputation)
        
        Used by: apply_effects() function for random events only
        """
        building_level = building.get("base_level", 1) if building else 1
        if building_level <= 1:
            return {"money": 1.0, "reputation": 1.0}
        
        money_multiplier = 1.0 + (building_level - 1) * 0.5  # 50% bonus per level above 1
        money_multiplier = min(money_multiplier, 1.5)  # clamp to 1.5x max
        reputation_multiplier = 1.0 + (building_level - 1) * 0.3  # 30% bonus per level above 1
        
        return {
            "money": money_multiplier,
            "reputation": reputation_multiplier,
            "level": building_level
        }


    # Fantasy day and month names
    day_names = ["Monareth", "Tuelivane", "Wetheris", "Thurramor", "Freylorn", "Starrith", "Sundusk" ]
    month_names = ["Frostveil", "Glimmerthaw", "Eldergreen", "Blossomire", "Solstara", "Mistralune", "Harvestide", "Duskmoor", "Shadowfen", "Crystalfell", "Emberwane", "Nightspire"]

# Default calendar variables - these will persist between saves
# CRITICAL: These MUST be default (not define) so Ren'Py saves them per-save.
# DO NOT reset these except in a true new game.
default current_day = 1
default current_month = 1  # 1-based (Frostveil = 1)
default current_year = 1

init python:
    def initialize_calendar(force_reset=False):
        """Initialize calendar variables without cross-save persistent bleed."""
        # Reset explicitly only when requested
        if force_reset:
            store.current_day = 1
            store.current_month = 1
            store.current_year = 1
            renpy.log("Calendar reset for new game (forced)")
            return

        # If the game already has a valid calendar in store, keep it
        # Check for valid values (must be > 0, not None, and integers)
        has_valid_day = hasattr(store, 'current_day') and store.current_day is not None and isinstance(store.current_day, int) and store.current_day > 0
        has_valid_month = hasattr(store, 'current_month') and store.current_month is not None and isinstance(store.current_month, int) and store.current_month > 0
        has_valid_year = hasattr(store, 'current_year') and store.current_year is not None and isinstance(store.current_year, int) and store.current_year > 0
        
        if has_valid_day and has_valid_month and has_valid_year:
            renpy.log(f"Calendar init (kept store): Day {store.current_day}, {month_names[store.current_month - 1]} {store.current_year}")
            return

        # Only set defaults if calendar is truly uninitialized (0, None, or missing)
        # This prevents overwriting a date that was just restored from save
        if not has_valid_day:
            store.current_day = 1
        if not has_valid_month:
            store.current_month = 1
        if not has_valid_year:
            store.current_year = 1
        renpy.log(f"Calendar initialized/updated: Day {store.current_day}, {month_names[store.current_month - 1]} {store.current_year}")

    # Initialize event tracking dictionaries
    if not hasattr(store, "event_flags"):
        store.event_flags = {}
    if not hasattr(store, "event_occurrences"):
        store.event_occurrences = {}
    if not hasattr(store, "event_last_occurred"):
        store.event_last_occurred = {}
    
    def reset_calendar_to_start():
        """Reset calendar to the very beginning (Day 1, Month 1, Year 1)"""
        store.current_day = 1
        store.current_month = 1
        store.current_year = 1
        renpy.log("Calendar manually reset to Day 1, Frostveil Year 1")

    def sync_calendar():
        """Synchronize calendar (store is the single source of truth)."""
        renpy.log(f"Calendar synced: Day {store.current_day}, {month_names[store.current_month - 1]} {store.current_year}")

    def calculate_total_days():
        """Calculate total days since game start (day 1, month 1, year 1)"""
        return (store.current_year - 1) * 12 * 28 + (store.current_month - 1) * 28 + store.current_day

    def advance_date():
        """Advance the date by one day, updating month and year if needed."""
        store.current_day += 1
        if store.current_day > 28:  # Roll over to next month
            store.current_day = 1
            store.current_month += 1
            if store.current_month > 12:  # Roll over to next year (1-12, so >12)
                store.current_month = 1
                store.current_year += 1
        # Sync persistent data
        sync_calendar()
        renpy.log(f"Date advanced to: {day_names[(store.current_day - 1) % 7]}, {store.current_day} {month_names[store.current_month - 1]} {store.current_year}")

    building_types_json = {}
    for file in renpy.list_files():
        if file.startswith("data/buildings/") and file.endswith(".json"):
            try:
                with renpy.file(file) as f:
                    data = json.load(f)
                if not persistent.nsfw_enabled:
                    data["building_types"] = [bt for bt in data["building_types"] if not bt.get("nsfw", False)]
                for bt in data["building_types"]:
                    for profession in bt.get("professions", []):
                        profession["original_max_daily_workers"] = profession.get("max_daily_workers", 1)
                building_types_json.update(data)
            except Exception as e:
                renpy.log("Error loading " + file + ": " + str(e))

    # Initialize items_json with an empty list
    items_json = {"items": [], "excluded_from_shops": []}

    # Iterate over files in the "data/items/" folder
    for file in renpy.list_files():
        if file.startswith("data/items/") and file.endswith(".json"):
            try:
                with renpy.file(file) as f:
                    data = json.load(f)
                if "items" in data:
                    # Filter items based on NSFW setting
                    filtered_items = [item for item in data["items"] if persistent.nsfw_enabled or not item.get("nsfw", False)]
                    items_json["items"].extend(filtered_items)
                    renpy.log(f"Loaded {len(filtered_items)} items from {file}")
                else:
                    renpy.log(f"File {file} does not contain an 'items' key.")
                
                # Merge excluded_from_shops from all JSON files (allows multiple files to contribute to exclusions)
                if "excluded_from_shops" in data:
                    # Combine with existing exclusions, avoiding duplicates
                    existing_excluded = set(items_json.get("excluded_from_shops", []))
                    new_excluded = set(data["excluded_from_shops"])
                    items_json["excluded_from_shops"] = list(existing_excluded.union(new_excluded))
                    renpy.log(f"Loaded {len(data['excluded_from_shops'])} excluded items from {file}")
            except Exception as e:
                renpy.log(f"Error loading {file}: {e}")

    # Debug: log all loaded item IDs.
    renpy.log("Items available for loot: " + str([item["id"] for item in items_json.get("items", [])]))
    renpy.log("Items excluded from shops: " + str(items_json.get("excluded_from_shops", [])))
   

    
    
 
    



    def font_size(base_size):
        """
        Calculate font size based on user preference.
        Large mode adds 40% increase for better readability.
        Excludes the workers and buy_servants_table screens from font size increase.
        """
        if persistent.large_font_mode:
            # Check if we're in excluded screens and exclude them from font increase
            workers_screen = renpy.get_screen("workers")
            buy_servants_screen = renpy.get_screen("buy_servants_table")
            if workers_screen is None and buy_servants_screen is None:
                return int(base_size * 1.4)
        return base_size

    def col_size(base_size):
        """
        Calculate column width based on user preference.
        Large mode increases column width by 25% to accommodate larger text.
        """
        if persistent.large_font_mode:
            return int(base_size * 1.25)
        return base_size

    def get_fallback_folder(worker=None):
        """Get the appropriate fallback folder based on worker gender.
        Returns 'guy' for males, 'blossom' for females/unknown."""
        if worker and isinstance(worker, dict):
            gender = worker.get("gender", "").lower()
            if gender == "male":
                return "guy"
        return "blossom"  # Default for females or unknown
    
    def get_worker_folder(worker):
        """Resolve the worker's folder based on their data."""
        fallback = get_fallback_folder(worker)
        if isinstance(worker, dict):
            folder_name = worker.get("folder", fallback)
            renpy.log(f"Worker name: {worker.get('name', 'Unknown')}, folder resolved: {folder_name}")
        else:
            folder_name = fallback
            renpy.log(f"Worker is not a dictionary, using {fallback} folder as fallback")
        
        full_folder = f"images/workers/{folder_name}/"
        renpy.log(f"Resolved worker folder: {full_folder}")
        return full_folder

    # Function removed - using the one in event_visuals.rpy instead

    def get_skill_search_patterns(skill_name):
        """
        Get search patterns for a skill name. Some skills search for multiple patterns.
        """
        special_patterns = {
            "homo": ["les", "gay"],           # Homosexual busca "les" o "gay"
            "service": ["wait", "service", "maid"],      # Service busca "wait", "service" o "maid"
            "special": ["special", "titty"],  # Special busca "special" o "titty"
            "striptease": ["strip", "striptease"],  # Striptease busca "strip" o "striptease"
            "extreme": ["extreme", "beast"]   # Extreme busca "extreme" o "beast"
        }
        
        skill_lower = skill_name.lower() if skill_name else skill_name
        if skill_lower in special_patterns:
            return special_patterns[skill_lower]
        else:
            return [skill_name]

    def get_worker_image(worker, skill_name=None, outcome=None):
        """
        Returns an image for the given worker.
        - If skill_name is provided, uses the complex event image logic.
        - If skill_name is None, performs a robust search for a profile image.
        """
        # If a skill is specified, delegate to the powerful get_event_image function
        if skill_name is not None:
            simulated_event = {"story_image": skill_name}
            return get_event_image(worker, simulated_event, outcome=outcome, skill_name=skill_name)
        
        # Profile image logic when no skill is specified
        if not worker:
            return None
            
        # Get worker folder
        fallback = get_fallback_folder(worker)
        if hasattr(worker, 'get'):
            worker_folder = worker.get("folder", fallback)
            worker_name = worker.get("name", "Unknown")
        else:
            worker_folder = fallback
            worker_name = "Unknown"
        
        base_folder = f"images/workers/{worker_folder}/"
        
        renpy.log(f"=== get_worker_image DEBUG ===")
        renpy.log(f"Worker: {worker_name}, Folder: {worker_folder}")
        renpy.log(f"Looking in: {base_folder}")
        
        # Debug: list all files Ren'Py sees in this folder
        all_files = renpy.list_files()
        files_in_folder = [f for f in all_files if f.startswith(base_folder)]
        renpy.log(f"Files Ren'Py sees in {base_folder}: {len(files_in_folder)}")
        if len(files_in_folder) == 0:
            renpy.log(f"WARNING: Ren'Py sees NO files in {base_folder}!")
            # Check if folder exists with different case
            folder_name_lower = worker_folder.lower()
            similar_folders = [f for f in all_files if folder_name_lower in f.lower()]
            renpy.log(f"Similar paths with '{folder_name_lower}': {similar_folders[:5] if similar_folders else 'NONE'}")
        
        def _worker_allows_profile_variant(local_worker, filepath):
            basename = os.path.basename(filepath).lower()
            if "profile" not in basename:
                return True
            prefix_part = basename.split("profile", 1)[0].rstrip("_")
            if not prefix_part:
                return True
            token_to_trait = {
                "pregnant": "Pregnant",
                "futa": "Futa",
                "transformed": "Transformed",
                "magical": "Magical",
            }
            required = []
            for token in prefix_part.split("_"):
                if token in token_to_trait:
                    required.append(token_to_trait[token])
            if not required:
                return True
            traits = set((local_worker or {}).get("traits", []) or [])
            return set(required).issubset(traits)

        trait_file_prefixes = ("pregnant_", "futa_", "transformed_", "magical_")

        # Try worker's profile image using robust flexible matching
        profile_matches = get_pattern_matches_flexible(base_folder, "profile")
        profile_matches = [f for f in profile_matches if _worker_allows_profile_variant(worker, f)]
        renpy.log(f"Profile matches found: {len(profile_matches) if profile_matches else 0}")
        if profile_matches:
            renpy.log(f"Profile matches: {profile_matches}")
            selected = renpy.random.choice(profile_matches)
            renpy.log(f"Selected profile image: {selected}")
            return selected
        
        # Try any image in worker folder as fallback (excluding failure images)
        all_worker_images = get_pattern_matches_flexible(base_folder, "", exclude_failure=True)
        all_worker_images = [f for f in all_worker_images if not should_exclude_trait_file(f, trait_file_prefixes, [])]
        if all_worker_images:
            selected = renpy.random.choice(all_worker_images)
            renpy.log(f"Found fallback worker image: {selected}")
            return selected
        
        # If no images exist, return None
        renpy.log(f"No images found for worker in folder: {worker_folder}")
        return None

    def _safe_relink_worker_folder(worker_name):
        """Safe wrapper to relink folder by worker name and update screen image"""
        try:
            # Find worker in store.workers first
            worker = next((w for w in store.workers if w.get("name") == worker_name), None)
            if not worker:
                renpy.notify(f"Worker {worker_name} not found")
                return False
            
            # Relink the folder - this updates the worker's folder in store.workers
            new_image = relink_worker_folder_from_json(worker)
            
            if new_image:
                # Update the current_image screen variable if we're in worker_details screen
                if renpy.get_screen("worker_details"):
                    try:
                        renpy.set_screen_variable("current_image", new_image)
                        renpy.restart_interaction()
                        renpy.log(f"Updated current_image screen variable to: {new_image}")
                    except Exception as e:
                        renpy.log(f"Error updating screen variable: {e}")
                        # Fallback: try to refresh by getting the image again
                        updated_worker = next((w for w in store.workers if w.get("name") == worker_name), None)
                        if updated_worker:
                            fallback_image = get_worker_image(updated_worker)
                            if fallback_image:
                                renpy.set_screen_variable("current_image", fallback_image)
                                renpy.restart_interaction()
                renpy.notify(f"Folder relinked! New image loaded.")
                return True
            else:
                renpy.notify(f"Folder relinked but no image found. Check folder name in JSON.")
                return False
                    
        except Exception as e:
            import traceback
            renpy.log(f"Error in _safe_relink_worker_folder: {e}")
            renpy.log(traceback.format_exc())
            renpy.notify(f"Error: {str(e)}")
            return False
    
    def relink_worker_folder_from_json(worker):
        """
        Relink worker's folder field from JSON data.
        Safe function that only updates the folder field, preserving all game state.
        Updates both the worker object passed and the worker in store.workers.
        Returns the new image path or None.
        """
        if not worker or not worker.get("name"):
            renpy.notify("Invalid worker")
            return None
        
        worker_name = worker.get("name")
        try:
            # Load workers from JSON to find this one
            all_json_workers = load_workers(include_unique=True, include_encounter_only=True, for_events=True)
            json_worker = next((w for w in all_json_workers if w.get("name") == worker_name), None)
            
            if json_worker and json_worker.get("folder"):
                old_folder = worker.get("folder", "missing")
                new_folder = json_worker["folder"]
                
                # Update the worker object passed
                worker["folder"] = new_folder
                
                # Also update in store.workers if it exists there
                store_worker = next((w for w in store.workers if w.get("name") == worker_name), None)
                if store_worker:
                    store_worker["folder"] = new_folder
                    renpy.log(f"Updated folder in store.workers for {worker_name}")
                
                renpy.log(f"Relinked folder for {worker_name}: '{old_folder}' -> '{new_folder}'")
                renpy.notify(f"Relinked folder for {worker_name}: {new_folder}")
                
                # Return new image
                return get_worker_image(worker)
            else:
                renpy.notify(f"No folder found in JSON for {worker_name}")
                return None
        except Exception as e:
            import traceback
            renpy.log(f"Error relinking folder for {worker_name}: {e}")
            renpy.log(traceback.format_exc())
            renpy.notify(f"Error relinking folder: {str(e)}")
            return None

    def get_worker_image_random(worker, skill_name=None):
        """
        Returns a RANDOM image for the given worker and skill.
        Uses robust flexible matching for better compatibility with different file formats and naming.
        Used specifically for skills menu exploration.
        """
        if not worker or skill_name is None:
            return get_worker_image(worker)  # Fallback to regular function
        
        # Get worker folder using the same logic as get_event_image
        fallback = get_fallback_folder(worker)
        if hasattr(worker, 'get'):
            worker_folder = worker.get("folder", fallback)
            worker_name = worker.get("name", "Unknown")
        else:
            worker_folder = fallback
            worker_name = "Unknown"
        
        base_folder = f"images/workers/{worker_folder}/"
        default_folder = f"images/workers/{fallback}/"
        
        renpy.log(f"get_worker_image_random: Worker {worker_name}, Skill {skill_name}, Folder {base_folder}")
        
        # Get trait prefixes for the worker
        trait_prefixes = get_trait_prefixes(worker)
        
        # Convert skill_name for image searching
        skill_name_for_search = get_skill_name_for_images(skill_name)
        skill_patterns = get_skill_search_patterns(skill_name_for_search)
        
        renpy.log(f"Searching for skill patterns: {skill_patterns}")
        
        # PRIORITY 1: Worker folder with traits (for skill-based images)
        if trait_prefixes and skill_name is not None:
            for skill_pattern_name in skill_patterns:
                for prefix in trait_prefixes:
                    # Try general skill image with trait using robust matching
                    skill_pattern = f"{prefix}_{skill_pattern_name}"
                    skill_matches = get_pattern_matches_flexible(base_folder, skill_pattern, exclude_failure=True)
                    if skill_matches:
                        skill_matches = [f for f in skill_matches if not should_exclude_interaction_file(f)]
                    if skill_matches:
                        # Use random selection WITHOUT cache
                        selected = get_random_choice(skill_matches)
                        if selected:
                            renpy.log(f"Found skill image with trait: {selected}")
                            return selected
        
        # PRIORITY 2: Worker folder without traits (for skill-based images)
        if skill_name is not None:
            for skill_pattern_name in skill_patterns:
                # Try general skill image using robust matching
                skill_matches = get_pattern_matches_flexible(base_folder, skill_pattern_name, exclude_failure=True)
                # Exclude trait-prefixed files if worker doesn't have those traits
                if skill_matches:
                    worker_traits = worker.get("traits", [])
                    trait_file_prefixes = ("pregnant_", "futa_", "transformed_", "magical_")
                    trait_names = ("pregnant", "futa", "transformed", "magical")
                    filtered_matches = []
                    for f in skill_matches:
                        basename = os.path.basename(f).lower()
                        should_exclude = False
                        
                        # Check for single trait prefix
                        for i, prefix in enumerate(trait_file_prefixes):
                            if basename.startswith(prefix):
                                trait_name = trait_names[i].capitalize()
                                if trait_name not in worker_traits:
                                    should_exclude = True
                                break
                        
                        # Check for trait combinations (e.g., "transformed_pregnant_")
                        if not should_exclude:
                            for trait1 in trait_names:
                                for trait2 in trait_names:
                                    if trait1 != trait2:
                                        combo_prefix = f"{trait1}_{trait2}_"
                                        if basename.startswith(combo_prefix):
                                            trait1_name = trait1.capitalize()
                                            trait2_name = trait2.capitalize()
                                            if trait1_name not in worker_traits or trait2_name not in worker_traits:
                                                should_exclude = True
                                                break
                                if should_exclude:
                                    break
                        
                        if not should_exclude and not should_exclude_interaction_file(f):
                            filtered_matches.append(f)
                    
                    if filtered_matches:
                        # Use random selection WITHOUT cache
                        selected = get_random_choice(filtered_matches)
                        if selected:
                            renpy.log(f"Found skill image: {selected}")
                            return selected
        
        # PRIORITY 3: Default folder with traits (for skill-based images)
        if trait_prefixes and skill_name is not None:
            for skill_pattern_name in skill_patterns:
                for prefix in trait_prefixes:
                    # Try general skill image with trait in default folder using robust matching
                    skill_pattern = f"{prefix}_{skill_pattern_name}"
                    skill_matches = get_pattern_matches_flexible(default_folder, skill_pattern, exclude_failure=True)
                    if skill_matches:
                        skill_matches = [f for f in skill_matches if not should_exclude_interaction_file(f)]
                    if skill_matches:
                        # Use random selection WITHOUT cache
                        selected = get_random_choice(skill_matches)
                        if selected:
                            renpy.log(f"Found default skill image with trait: {selected}")
                            return selected
        
        # PRIORITY 4: Default folder without traits (for skill-based images)
        if skill_name is not None:
            for skill_pattern_name in skill_patterns:
                # Try general skill image in default folder using robust matching
                skill_matches = get_pattern_matches_flexible(default_folder, skill_pattern_name, exclude_failure=True)
                # Exclude trait-prefixed files if worker doesn't have those traits
                if skill_matches:
                    worker_traits = worker.get("traits", [])
                    trait_file_prefixes = ("pregnant_", "futa_", "transformed_", "magical_")
                    trait_names = ("pregnant", "futa", "transformed", "magical")
                    filtered_matches = []
                    for f in skill_matches:
                        basename = os.path.basename(f).lower()
                        should_exclude = False
                        
                        # Check for single trait prefix
                        for i, prefix in enumerate(trait_file_prefixes):
                            if basename.startswith(prefix):
                                trait_name = trait_names[i].capitalize()
                                if trait_name not in worker_traits:
                                    should_exclude = True
                                break
                        
                        # Check for trait combinations (e.g., "transformed_pregnant_")
                        if not should_exclude:
                            for trait1 in trait_names:
                                for trait2 in trait_names:
                                    if trait1 != trait2:
                                        combo_prefix = f"{trait1}_{trait2}_"
                                        if basename.startswith(combo_prefix):
                                            trait1_name = trait1.capitalize()
                                            trait2_name = trait2.capitalize()
                                            if trait1_name not in worker_traits or trait2_name not in worker_traits:
                                                should_exclude = True
                                                break
                                if should_exclude:
                                    break
                        
                        if not should_exclude and not should_exclude_interaction_file(f):
                            filtered_matches.append(f)
                    
                    if filtered_matches:
                        # Use random selection WITHOUT cache
                        selected = get_random_choice(filtered_matches)
                        if selected:
                            renpy.log(f"Found default skill image: {selected}")
                            return selected
        
        # Fallback to regular worker image
        renpy.log(f"No skill images found for {skill_name}, falling back to profile")
        return get_worker_image(worker)

    
    def load_names_from_json():
        """Load name pools from names.json file."""
        try:
            with renpy.file("data/names.json") as f:
                return json.load(f)
        except Exception as e:
            renpy.log(f"Error loading names.json: {str(e)}")
            # Fallback to basic name pools if file can't be loaded
            return {
                "western_male": ["James", "William", "Alexander"],
                "western_female": ["Elizabeth", "Victoria", "Charlotte"],
                "fantasy_male": ["Thalorin", "Eldred", "Kaelith"],
                "fantasy_female": ["Aelindra", "Celestia", "Luna"],
                "eastern_male": ["Hiroshi", "Kenji", "Takeshi"],
                "eastern_female": ["Sakura", "Yuki", "Mei"]
            }

    # Load name lists at init time
    name_lists = load_names_from_json()

    # Initialize a global variable to hold the panel mode.
    if not hasattr(store, "current_panel_mode"):
        store.current_panel_mode = "skills"

    def set_global_panel_mode(newmode):
        store.current_panel_mode = newmode

    # Helper: Look up a trait's description from your traits JSON (be sure traits_list exists).
    

    

    def add_item_to_inventory(inventory, item_id, quantity=1):
        # First, ensure every entry in the inventory is a tuple.
        for i, entry in enumerate(inventory):
            if not isinstance(entry, tuple):
                if isinstance(entry, dict):
                    # Handle dict format: {"item_id": ..., "quantity": ..., "equipped": ...}
                    converted = (entry.get("item_id"), entry.get("quantity", 1), entry.get("equipped", False))
                    inventory[i] = converted
                elif isinstance(entry, list):
                    # Handle list format: [item_id] or [item_id, quantity] or [item_id, quantity, equipped]
                    if len(entry) == 1:
                        converted = (entry[0], 1, False)
                    elif len(entry) == 2:
                        converted = (entry[0], entry[1], False)
                    elif len(entry) >= 3:
                        converted = (entry[0], entry[1], entry[2])
                    else:
                        continue  # Skip empty lists
                    inventory[i] = converted
                elif isinstance(entry, str):
                    # Handle old string format: just the item_id
                    inventory[i] = (entry, 1, False)

        item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if not item_data:
            renpy.log("add_item_to_inventory: Item not found: " + item_id)
            return
        
        def _mark_objective_12_item_if_needed(mark_item_id):
            if mark_item_id in ("binding_gem", "obsidian_blade", "enchanted_ring"):
                if not hasattr(store, "event_flags") or store.event_flags is None:
                    store.event_flags = {}
                flag_name = f"objective12_{mark_item_id}_collected"
                if not store.event_flags.get(flag_name, False):
                    store.event_flags[flag_name] = True
                    renpy.log(f"Objective 12: Marked {mark_item_id} as collected.")

        item_type = item_data.get("type", "unknown")
        is_manager_inventory = (hasattr(store, 'manager_inventory') and 
                               (inventory is store.manager_inventory or 
                                id(inventory) == id(getattr(store, 'manager_inventory', None))))
        
        if item_type in ["currency", "consumable", "gift"]:
            # Consolidate duplicate stacks first so stackables (e.g. gifts) stay on one line.
            match_indices = [idx for idx, e in enumerate(inventory) if isinstance(e, tuple) and len(e) >= 2 and e[0] == item_id]
            if match_indices:
                primary_idx = match_indices[0]
                total_existing = 0
                primary_equipped = bool(inventory[primary_idx][2]) if len(inventory[primary_idx]) >= 3 else False
                for idx in reversed(match_indices):
                    entry = inventory[idx]
                    qty_val = entry[1]
                    try:
                        qty_val = int(qty_val)
                    except (ValueError, TypeError):
                        qty_val = 0
                    if qty_val < 0:
                        qty_val = 0
                    if qty_val > 999999:
                        qty_val = 999999
                    total_existing += qty_val
                    if idx != primary_idx:
                        del inventory[idx]
                new_quantity = min(999999, total_existing + quantity)
                inventory[primary_idx] = (item_id, new_quantity, primary_equipped)
                renpy.log(f"Added {quantity} of {item_id} to existing stack (new quantity: {new_quantity}).")
            else:
                inventory.append((item_id, max(1, quantity), False))
                renpy.log(f"Added new stack of {item_id} (quantity: {quantity}).")
            # CRITICAL: Force Ren'Py to recognize changes if this is manager_inventory
            if is_manager_inventory:
                # Also ensure the entire list is a new list to break references
                store.manager_inventory = list(store.manager_inventory)
                renpy.store.manager_inventory = store.manager_inventory
            _mark_objective_12_item_if_needed(item_id)
        else:
            for _ in range(quantity):
                inventory.append((item_id, 1, False))
            renpy.log(f"Added equipment item {item_id} {quantity} time(s).")
            _mark_objective_12_item_if_needed(item_id)

    def toggle_equip_item(inventory, item_id, worker=None):
        """
        Toggle the equipped state of an item in the given inventory.
        For equipment items (like "weapon" or "armor"), only one item of that type may be equipped.
        Exception: "clothing" and "armor" are separate slots and can be equipped simultaneously.
        If a worker is provided, apply (or remove) the item's effects accordingly.
        Assumes inventory items are tuples: (item_id, quantity, equipped).
        """
        # CRITICAL: Ensure we're working with the actual worker in store.workers, not a copy
        if worker is not None and hasattr(store, 'workers'):
            worker_name = worker.get("name")
            if worker_name:
                real_worker = next((w for w in store.workers if w.get("name") == worker_name), None)
                if real_worker:
                    worker = real_worker
                    inventory = worker.get("inventory", [])
                    renpy.log(f"toggle_equip_item: Using real worker from store.workers: {worker_name}")
        
        # Look up the item data for the given item_id.
        item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if not item_data:
            renpy.log("toggle_equip_item: Item data not found for " + item_id)
            return
        item_type = item_data.get("type", "")

        # Ensure all inventory entries are tuples.
        # After JSON restore, entries are lists: [item_id, quantity, equipped]
        # They may also be dicts: {"item_id": ..., "quantity": ..., "equipped": ...}
        for i, entry in enumerate(inventory):
            if not isinstance(entry, tuple):
                if isinstance(entry, list) and len(entry) >= 2:
                    # Convert list to tuple: [item_id, quantity, equipped] -> (item_id, quantity, equipped)
                    equipped = entry[2] if len(entry) >= 3 else False
                    converted = (entry[0], entry[1], equipped)
                    inventory[i] = converted
                elif isinstance(entry, dict):
                    # Convert dict to tuple
                    converted = (entry.get("item_id"), entry.get("quantity"), entry.get("equipped", False))
                    inventory[i] = converted
                else:
                    renpy.log(f"toggle_equip_item: Unknown entry type {type(entry)}: {entry}")
                    # Try to convert anyway if it has index access
                    try:
                        if len(entry) >= 2:
                            equipped = entry[2] if len(entry) >= 3 else False
                            converted = (entry[0], entry[1], equipped)
                            inventory[i] = converted
                    except:
                        renpy.log(f"toggle_equip_item: Could not convert entry: {entry}")

        # Find the target item index in the inventory.
        target_index = None
        for i, item in enumerate(inventory):
            if item[0] == item_id:
                target_index = i
                break
        if target_index is None:
            renpy.log("toggle_equip_item: Target item not found in inventory: " + item_id)
            return

        target_item = inventory[target_index]
        renpy.log(f"toggle_equip_item: Found item {target_item} for item_id {item_id}")

        # If the target item is not equipped, we want to equip it.
        if not target_item[2]:
            # Unequip any other equipped item of the same type.
            # Special case: "clothing" and "armor" are separate slots, so they don't conflict with each other.
            for j, other in enumerate(inventory):
                if j != target_index and other[2]:
                    other_data = next((i for i in items_json["items"] if i["id"] == other[0]), None)
                    if other_data:
                        other_type = other_data.get("type")
                        # Only unequip if it's the same type, EXCEPT if one is "clothing" and the other is "armor"
                        if other_type == item_type:
                            renpy.log(f"Unequipping other item at index {j}: {other}")
                            inventory[j] = (other[0], other[1], False)
                            remove_item_effects(worker, other[0])
            # Now equip the target item.
            inventory[target_index] = (target_item[0], target_item[1], True)
            if worker is not None:
                apply_item_effects(worker, target_item[0])
            renpy.log(f"Equipped item {target_item[0]}; new inventory entry: {inventory[target_index]}")
        else:
            # If the item is equipped, unequip it.
            inventory[target_index] = (target_item[0], target_item[1], False)
            if worker is not None:
                remove_item_effects(worker, target_item[0])
            renpy.log(f"Unequipped item {target_item[0]}; new inventory entry: {inventory[target_index]}")

        renpy.restart_interaction()

    def unequip_item_by_match(inventory, item_id, quantity=None, worker=None):
        """
        Unequip a specific equipped item by matching item_id and (optionally) quantity.
        Avoids unequipping another copy with the same item_id.
        """
        for i, item in enumerate(inventory):
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                if str(item[0]) == str(item_id) and bool(item[2]) is True:
                    if quantity is None or item[1] == quantity:
                        inventory[i] = (item[0], item[1], False)
                        if worker is not None:
                            remove_item_effects(worker, item[0])
                        renpy.log(f"unequip_item_by_match: Unequipped item at index {i}: {inventory[i]}")
                        renpy.restart_interaction()
                        return True
        renpy.log(f"unequip_item_by_match: No equipped match for item_id={item_id}, quantity={quantity}")
        return False

    def _get_trait_def_cache():
        """Cache trait lookups for item effects."""
        if not hasattr(store, "_trait_def_cache") or not store._trait_def_cache:
            try:
                if hasattr(store, "get_all_traits"):
                    trait_list = store.get_all_traits()
                else:
                    trait_list = []
                    renpy.log("TRAITS: get_all_traits() unavailable; trait cache left empty")
                store._trait_def_cache = {t.get("name"): t for t in trait_list if t.get("name")}
            except Exception as e:
                renpy.log(f"TRAITS: Failed to build trait cache for item effects: {e}")
                store._trait_def_cache = {}
        return store._trait_def_cache

    def _get_trait_conflicts(trait_name):
        trait_def = _get_trait_def_cache().get(trait_name, {})
        return trait_def.get("conflicts", []) if trait_def else []

    def _record_removed_conflicts(worker, item_id, trait_name):
        """Record conflicts removed by add_trait so they can be restored on unequip."""
        if not worker or not trait_name:
            return
        conflicts = _get_trait_conflicts(trait_name)
        if not conflicts:
            return
        current_traits = worker.get("traits", [])
        removed = [t for t in conflicts if t in current_traits]
        if removed:
            if "_removed_conflicts_by_item" not in worker:
                worker["_removed_conflicts_by_item"] = {}
            existing = worker["_removed_conflicts_by_item"].get(item_id, [])
            # Deduplicate while preserving order
            for t in removed:
                if t not in existing:
                    existing.append(t)
            worker["_removed_conflicts_by_item"][item_id] = existing
            renpy.log(f"TRAITS: Recorded conflicts removed by '{item_id}': {existing}")

    def _can_restore_trait(worker, trait_name):
        if not worker or not trait_name:
            return False
        conflicts = _get_trait_conflicts(trait_name)
        if not conflicts:
            return True
        current_traits = worker.get("traits", [])
        return not any(conflict in current_traits for conflict in conflicts)
                
    def apply_item_effects(worker, item_id):
        """Apply the effects of an equipped item to a worker."""
        item = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if not item:
            renpy.log(f"apply_item_effects: Item '{item_id}' not found in items_json")
            return
        if "effect" not in item:
            renpy.log(f"apply_item_effects: Item '{item_id}' has no 'effect' key")
            return
        renpy.log(f"apply_item_effects: Processing effects for '{item_id}': {list(item['effect'].keys())}")
        if item and "effect" in item:
            for effect_type, effect_value in item["effect"].items():
                renpy.log(f"apply_item_effects: Processing effect_type='{effect_type}'")
                if effect_type == "skill_modifiers":
                    # Equipment bonuses are handled in calculate_skill_with_traits()
                    # No need to modify base skills here
                    pass
                elif effect_type == "health":
                    # Max health is derived from equipped items/traits. When this function runs,
                    # inventory state may already be updated, so never add health bonus manually.
                    old_max_health = int(worker.get("max_health", calculate_max_health(worker)))
                    if old_max_health <= 0:
                        old_max_health = 1
                    current_health = int(worker.get("health", 0))
                    health_ratio = float(current_health) / float(old_max_health)
                    new_max_health = max(1, int(calculate_max_health(worker)))
                    worker["max_health"] = new_max_health
                    worker["health"] = max(0, min(new_max_health, int(round(new_max_health * health_ratio))))
                elif effect_type == "energy":
                    # Same rule as health: never add energy bonus manually here.
                    old_max_energy = int(worker.get("max_energy", calculate_max_energy(worker)))
                    current_energy = int(worker.get("energy", 0))
                    if old_max_energy > 0:
                        energy_ratio = float(current_energy) / float(old_max_energy)
                    else:
                        energy_ratio = 0.0
                    new_max_energy = max(0, int(calculate_max_energy(worker)))
                    worker["max_energy"] = new_max_energy
                    worker["energy"] = max(0, min(new_max_energy, int(round(new_max_energy * energy_ratio))))
                elif effect_type == "add_trait":
                    # Support array of traits, single trait string, or dict with name/duration
                    renpy.log(f"add_trait effect_value type: {type(effect_value)}, is list: {isinstance(effect_value, list)}, value: {str(effect_value)[:100]}")
                    # Use type check that works with Ren'Py's JSON loading
                    if type(effect_value).__name__ == 'list' or isinstance(effect_value, (list, tuple)):
                        # Array of trait names
                        renpy.log(f"Processing {len(effect_value)} traits from list")
                        for trait_name in effect_value:
                            if isinstance(trait_name, dict) or type(trait_name).__name__ == 'dict':
                                _record_removed_conflicts(worker, item_id, trait_name.get("name", ""))
                                add_trait_with_duration(worker, trait_name.get("name", ""), trait_name.get("duration", 0))
                            else:
                                renpy.log(f"Adding trait: {trait_name}")
                                _record_removed_conflicts(worker, item_id, trait_name)
                                add_trait_with_duration(worker, trait_name, 0)
                    elif isinstance(effect_value, dict) or type(effect_value).__name__ == 'dict':
                        _record_removed_conflicts(worker, item_id, effect_value.get("name", ""))
                        add_trait_with_duration(worker, effect_value.get("name", ""), effect_value.get("duration", 0))
                    else:
                        _record_removed_conflicts(worker, item_id, effect_value)
                        add_trait_with_duration(worker, effect_value, 0)
                elif effect_type == "remove_trait":
                    # Support array of traits or single trait string - removes traits when equipping
                    renpy.log(f"remove_trait effect_value type: {type(effect_value)}, is list: {isinstance(effect_value, list)}, value: {str(effect_value)[:100]}")
                    removed_traits = []
                    # Use type check that works with Ren'Py's JSON loading
                    if type(effect_value).__name__ == 'list' or isinstance(effect_value, (list, tuple)):
                        # Array of trait names
                        renpy.log(f"Processing {len(effect_value)} traits to remove from list")
                        for trait_name in effect_value:
                            if isinstance(trait_name, dict) or type(trait_name).__name__ == 'dict':
                                trait_name_to_remove = trait_name.get("name", "")
                            else:
                                trait_name_to_remove = trait_name
                            if trait_name_to_remove:
                                renpy.log(f"Removing trait: '{trait_name_to_remove}' from worker '{worker.get('name', 'Unknown')}'")
                                if trait_name_to_remove in worker.get("traits", []):
                                    removed_traits.append(trait_name_to_remove)
                                remove_trait_safe(worker, trait_name_to_remove)
                    elif isinstance(effect_value, dict) or type(effect_value).__name__ == 'dict':
                        trait_name_to_remove = effect_value.get("name", "")
                        if trait_name_to_remove:
                            renpy.log(f"Removing trait (dict): '{trait_name_to_remove}' from worker '{worker.get('name', 'Unknown')}'")
                            if trait_name_to_remove in worker.get("traits", []):
                                removed_traits.append(trait_name_to_remove)
                            remove_trait_safe(worker, trait_name_to_remove)
                    else:
                        if effect_value:
                            renpy.log(f"Removing trait (string): '{effect_value}' from worker '{worker.get('name', 'Unknown')}'")
                            if effect_value in worker.get("traits", []):
                                removed_traits.append(effect_value)
                            remove_trait_safe(worker, effect_value)
                    if removed_traits:
                        if "_removed_traits_by_item" not in worker:
                            worker["_removed_traits_by_item"] = {}
                        worker["_removed_traits_by_item"][item_id] = removed_traits
                        renpy.log(f"remove_trait: Recorded removed traits for '{item_id}': {removed_traits}")

    def remove_item_effects(worker, item_id):
        """Remove the effects of an unequipped item from a worker."""
        item = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if item and "effect" in item:
            for effect_type, effect_value in item["effect"].items():
                if effect_type == "skill_modifiers":
                    # Equipment bonuses are handled in calculate_skill_with_traits()
                    # No need to revert skills here
                    pass
                elif effect_type == "health":
                    # Max health is derived from equipped items/traits. When this function runs,
                    # inventory state may already be updated, so never subtract health bonus manually.
                    old_max_health = int(worker.get("max_health", calculate_max_health(worker)))
                    if old_max_health <= 0:
                        old_max_health = 1
                    current_health = int(worker.get("health", 0))
                    health_ratio = float(current_health) / float(old_max_health)
                    new_max_health = max(1, int(calculate_max_health(worker)))
                    worker["max_health"] = new_max_health
                    worker["health"] = max(0, min(new_max_health, int(round(new_max_health * health_ratio))))
                elif effect_type == "energy":
                    # Same rule as health: never subtract energy bonus manually here.
                    old_max_energy = int(worker.get("max_energy", calculate_max_energy(worker)))
                    current_energy = int(worker.get("energy", 0))
                    if old_max_energy > 0:
                        energy_ratio = float(current_energy) / float(old_max_energy)
                    else:
                        energy_ratio = 0.0
                    new_max_energy = max(0, int(calculate_max_energy(worker)))
                    worker["max_energy"] = new_max_energy
                    worker["energy"] = max(0, min(new_max_energy, int(round(new_max_energy * energy_ratio))))
                elif effect_type == "add_trait":
                    # When unequipping, remove the traits that were added when equipping
                    renpy.log(f"remove_item_effects: Removing traits added by item '{item_id}': {effect_value}")
                    if type(effect_value).__name__ == 'list' or isinstance(effect_value, (list, tuple)):
                        # Array of trait names
                        for trait_name in effect_value:
                            if isinstance(trait_name, dict) or type(trait_name).__name__ == 'dict':
                                trait_name_to_remove = trait_name.get("name", "")
                            else:
                                trait_name_to_remove = trait_name
                            if trait_name_to_remove:
                                renpy.log(f"remove_item_effects: Removing trait '{trait_name_to_remove}' from worker '{worker.get('name', 'Unknown')}'")
                                remove_trait_safe(worker, trait_name_to_remove)
                    elif isinstance(effect_value, dict) or type(effect_value).__name__ == 'dict':
                        trait_name_to_remove = effect_value.get("name", "")
                        if trait_name_to_remove:
                            renpy.log(f"remove_item_effects: Removing trait '{trait_name_to_remove}' from worker '{worker.get('name', 'Unknown')}'")
                            remove_trait_safe(worker, trait_name_to_remove)
                    else:
                        if effect_value:
                            renpy.log(f"remove_item_effects: Removing trait '{effect_value}' from worker '{worker.get('name', 'Unknown')}'")
                            remove_trait_safe(worker, effect_value)
                    # Restore conflicts that were removed by the added trait(s), if safe
                    removed_conflicts = None
                    if "_removed_conflicts_by_item" in worker:
                        removed_conflicts = worker["_removed_conflicts_by_item"].pop(item_id, None)
                        if not worker["_removed_conflicts_by_item"]:
                            del worker["_removed_conflicts_by_item"]
                    if removed_conflicts:
                        renpy.log(f"remove_item_effects: Restoring conflicts removed by '{item_id}': {removed_conflicts}")
                        for trait_name in removed_conflicts:
                            if trait_name and trait_name not in worker.get("traits", []):
                                if _can_restore_trait(worker, trait_name):
                                    add_trait_with_duration(worker, trait_name, 0)
                                else:
                                    renpy.log(f"remove_item_effects: Skipping restore of '{trait_name}' due to current conflicts")
                elif effect_type == "remove_trait":
                    # When unequipping, add back the traits that were removed when equipping
                    removed_by_item = None
                    if "_removed_traits_by_item" in worker:
                        removed_by_item = worker["_removed_traits_by_item"].pop(item_id, None)
                        if not worker["_removed_traits_by_item"]:
                            del worker["_removed_traits_by_item"]
                    if removed_by_item:
                        renpy.log(f"remove_item_effects: Re-adding recorded traits for '{item_id}': {removed_by_item}")
                        for trait_name in removed_by_item:
                            if trait_name:
                                add_trait_with_duration(worker, trait_name, 0)
                    else:
                        renpy.log(f"remove_item_effects: Re-adding traits removed by item '{item_id}': {effect_value}")
                        if type(effect_value).__name__ == 'list' or isinstance(effect_value, (list, tuple)):
                            for trait_name in effect_value:
                                if isinstance(trait_name, dict) or type(trait_name).__name__ == 'dict':
                                    trait_name_to_add = trait_name.get("name", "")
                                else:
                                    trait_name_to_add = trait_name
                                if trait_name_to_add:
                                    add_trait_with_duration(worker, trait_name_to_add, 0)
                        elif isinstance(effect_value, dict) or type(effect_value).__name__ == 'dict':
                            trait_name_to_add = effect_value.get("name", "")
                            if trait_name_to_add:
                                add_trait_with_duration(worker, trait_name_to_add, 0)
                        else:
                            if effect_value:
                                add_trait_with_duration(worker, effect_value, 0)

    def remove_item_from_inventory(inventory, item_id, quantity=1):
        # CRITICAL: Check if this is manager_inventory and ALWAYS work directly with store.manager_inventory
        is_manager_inventory = (hasattr(store, 'manager_inventory') and 
                               (inventory is store.manager_inventory or 
                                id(inventory) == id(getattr(store, 'manager_inventory', None))))
        
        # If this is manager_inventory, work DIRECTLY with store.manager_inventory
        if is_manager_inventory:
            # Convert to a normal list if needed
            try:
                if 'RevertableList' in str(type(store.manager_inventory)) or not isinstance(store.manager_inventory, list):
                    store.manager_inventory = list(store.manager_inventory)
                # Always work with store.manager_inventory directly
                inventory = store.manager_inventory
            except Exception:
                pass
        
        # First, ensure every entry in the inventory is a tuple and normalize quantities
        for i, entry in enumerate(inventory):
            if not isinstance(entry, tuple):
                if isinstance(entry, dict):
                    # Handle dict format: {"item_id": ..., "quantity": ..., "equipped": ...}
                    converted = (entry.get("item_id"), entry.get("quantity", 1), entry.get("equipped", False))
                    inventory[i] = converted
                elif isinstance(entry, list):
                    # Handle list format: [item_id] or [item_id, quantity] or [item_id, quantity, equipped]
                    if len(entry) == 1:
                        converted = (entry[0], 1, False)
                    elif len(entry) == 2:
                        converted = (entry[0], entry[1], False)
                    elif len(entry) >= 3:
                        converted = (entry[0], entry[1], entry[2])
                    else:
                        continue  # Skip empty lists
                    inventory[i] = converted
                elif isinstance(entry, str):
                    # Handle old string format: just the item_id
                    inventory[i] = (entry, 1, False)
                elif hasattr(entry, '__getitem__') and hasattr(entry, '__len__'):
                    # Handle list-like objects (e.g., RevertableList)
                    try:
                        entry_list = list(entry)
                        if len(entry_list) == 1:
                            converted = (entry_list[0], 1, False)
                        elif len(entry_list) == 2:
                            converted = (entry_list[0], entry_list[1], False)
                        elif len(entry_list) >= 3:
                            converted = (entry_list[0], entry_list[1], entry_list[2])
                        else:
                            continue
                        inventory[i] = converted
                    except Exception:
                        continue
            else:
                # Normalize tuple quantities to int to avoid comparison issues
                try:
                    entry_id = entry[0]
                    entry_qty = entry[1] if len(entry) > 1 else 1
                    entry_eq = entry[2] if len(entry) > 2 else False
                    entry_qty = int(entry_qty) if entry_qty is not None else 1
                    entry_eq = bool(entry_eq) if entry_eq is not None else False
                    inventory[i] = (entry_id, entry_qty, entry_eq)
                except Exception:
                    continue
        
        # Now remove the item
        # CRITICAL: Find ALL items with this item_id and remove quantity from them
        # This handles cases where there are multiple separate items with the same id
        remaining_to_remove = quantity
        items_to_remove = []
        
        # Work with a copy of indices to avoid modification during iteration
        for i in range(len(inventory)):
            entry = inventory[i]
            if isinstance(entry, tuple) and str(entry[0]) == str(item_id):
                if remaining_to_remove > 0:
                    try:
                        entry_quantity = int(entry[1]) if entry[1] is not None else 1
                    except Exception:
                        entry_quantity = 1
                    if entry_quantity <= remaining_to_remove:
                        # This item will be completely removed
                        items_to_remove.append(i)
                        remaining_to_remove -= entry_quantity
                    else:
                        # Reduce this item's quantity
                        new_quantity = entry_quantity - remaining_to_remove
                        # CRITICAL: Create a completely NEW tuple to break reference sharing
                        inventory[i] = (str(entry[0]), int(new_quantity), bool(entry[2] if len(entry) > 2 else False))
                        remaining_to_remove = 0
                        renpy.log(f"remove_item_from_inventory: Reduced {item_id} from {entry_quantity} to {new_quantity} at index {i}")
        
        # Remove items that were completely consumed (in reverse order to maintain indices)
        for i in reversed(items_to_remove):
            inventory.pop(i)
            renpy.log(f"remove_item_from_inventory: Removed {item_id} completely at index {i}")
        
        # CRITICAL: For manager_inventory, ALWAYS recreate the entire list to break ALL references
        # This ensures Ren'Py recognizes the changes
        if is_manager_inventory:
            # Create a completely new list with new tuples for each item
            new_inv = []
            for item in inventory:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    try:
                        item_id = str(item[0]) if item[0] is not None else ""
                        qty = int(item[1]) if item[1] is not None else 1
                        eq = bool(item[2]) if len(item) > 2 and item[2] is not None else False
                        new_inv.append((item_id, qty, eq))
                    except Exception:
                        new_inv.append(item)
                else:
                    new_inv.append(item)
            store.manager_inventory = new_inv
            renpy.store.manager_inventory = store.manager_inventory
            renpy.log(f"remove_item_from_inventory: Recreated manager_inventory with {len(new_inv)} items (removed {quantity} of {item_id})")
        
        return

    def remove_item_from_inventory_by_index(inventory, index, quantity=1):
        """
        Remove quantity from a specific inventory entry by index.
        Falls back safely if index is invalid.
        """
        if inventory is None:
            return False
        if index is None or index < 0 or index >= len(inventory):
            return False
        entry = inventory[index]
        if not isinstance(entry, tuple) or len(entry) < 2:
            return False
        try:
            entry_qty = int(entry[1]) if entry[1] is not None else 1
        except Exception:
            entry_qty = 1
        if entry_qty <= quantity:
            inventory.pop(index)
        else:
            inventory[index] = (entry[0], entry_qty - quantity, entry[2] if len(entry) > 2 else False)
        return True

    def use_potion_from_inventory(worker, potion_id):
        """
        Use a potion on a worker from manager_inventory.
        Assumes the potion exists in manager_inventory.
        
        Args:
            worker: Worker dict to use the potion on
            potion_id: Item ID of the potion ("energy_potion" or "health_potion")
        """
        potion_item = next((i for i in items_json["items"] if i["id"] == potion_id), None)
        if not potion_item:
            renpy.notify(f"Potion {potion_id} not found!")
            return
        
        # Apply effects
        renpy.notify("Used " + potion_item.get("name", "Unknown"))
        if "effect" in potion_item and worker:
            for effect_type, effect_value in potion_item["effect"].items():
                if effect_type == "health":
                    worker["health"] = min(calculate_max_health(worker), worker["health"] + effect_value)
                elif effect_type == "energy":
                    worker["energy"] = min(calculate_max_energy(worker), worker["energy"] + effect_value)
        
        # Remove from manager_inventory
        remove_item_from_inventory(manager_inventory, potion_id)
        
        # Track tutorial objective 5 - potion usage
        if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and potion_item.get("name", "").lower().find("energy") != -1:
            store.potion_used_on_worker = True
            renpy.log("DEBUG: Tutorial - Energy potion used on worker")
            check_objective_completion()

    def use_or_buy_potion_action(worker, potion_id):
        """
        Returns an action to use a potion (from manager inventory) or show buy confirmation.
        """
        potion_item = next((i for i in items_json["items"] if i["id"] == potion_id), None)
        if not potion_item:
            return Function(lambda: renpy.notify(f"Potion {potion_id} not found!"))
        canonical = next((w for w in store.workers if w.get("name") == worker.get("name")), worker)
        has_in_manager = False
        for item_entry in manager_inventory:
            if isinstance(item_entry, (list, tuple)) and len(item_entry) >= 2 and item_entry[0] == potion_id and item_entry[1] > 0:
                has_in_manager = True
                break
        if has_in_manager:
            return Function(use_potion_from_inventory, canonical, potion_id)
        return Show("confirm_buy_potion", worker=canonical, potion_id=potion_id)

    def use_item(item_id, worker=None):
        """
        Uses a consumable item.
        Applies consumable effects to a target worker when provided.
        Removes 1 unit from the inventory that actually contains the item.
        """
        def _inv_has(inv, _item_id):
            try:
                for e in inv or []:
                    if isinstance(e, (list, tuple)) and len(e) >= 1 and str(e[0]) == str(_item_id):
                        # If quantity present, ensure > 0
                        if len(e) >= 2:
                            try:
                                return int(e[1]) > 0
                            except Exception:
                                return True
                        return True
                return False
            except Exception:
                return False

        def _remove_one(_item_id):
            # Prefer removing from worker inventory if the item is there; otherwise from manager inventory.
            if worker and _inv_has(worker.get("inventory", []), _item_id):
                remove_item_from_inventory(worker.get("inventory", []), _item_id)
            else:
                remove_item_from_inventory(manager_inventory, _item_id)

        # Ensure we operate on the canonical worker object from store.workers
        if worker is not None and hasattr(store, "workers"):
            worker_name = worker.get("name") if isinstance(worker, dict) else None
            if worker_name:
                canonical_worker = next((w for w in store.workers if w.get("name") == worker_name), None)
                if canonical_worker is not None and canonical_worker is not worker:
                    worker = canonical_worker

        item = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if not item:
            renpy.log(f"ERROR: Item {item_id} not found in items_json")
            return

        # Consumables and gifts can be used (gifts are mainly for worker delivery flows).
        if item.get("type") not in ("consumable", "gift"):
            return

        item_name = item.get("name", "Unknown")
        if item.get("type") == "gift" and worker:
            renpy.notify(f"Gave {item_name} to {worker.get('name', 'worker')}")
        else:
            renpy.notify("Used " + item_name)

        # Ren'Py may load JSON dicts as revertable dict-like objects, so be robust here.
        effect_raw = item.get("effect", None)
        if effect_raw is None:
            effect = {}
        elif isinstance(effect_raw, dict) or type(effect_raw).__name__ == "dict":
            effect = effect_raw
        elif hasattr(effect_raw, "items") and callable(getattr(effect_raw, "items", None)):
            try:
                effect = dict(effect_raw)
            except Exception:
                effect = {}
        else:
            effect = {}

        # Custom effects: keep using the shared system (it knows about story flags, unlocks, etc.)
        if effect and "custom" in effect:
            apply_effects({"custom": effect.get("custom")}, worker=worker)
            _remove_one(item_id)
            return

        # If no worker target, fall back to shared system for money/other global effects.
        if not worker:
            if effect:
                apply_effects(effect, worker=None)
            _remove_one(item_id)
            return

        # Apply worker-directed effects directly (this is what Wakeful Powder needs).
        for effect_type, effect_value in (effect or {}).items():
            if effect_type == "health":
                try:
                    worker["health"] = min(calculate_max_health(worker), worker.get("health", 0) + int(effect_value))
                except Exception:
                    pass
            elif effect_type == "energy":
                try:
                    worker["energy"] = min(calculate_max_energy(worker), worker.get("energy", 0) + int(effect_value))
                except Exception:
                    pass
            elif effect_type == "skill_modifiers":
                # Consumables that declare skill_modifiers should increase base skills.
                # This allows repeated uses until reaching the normal base-skill cap.
                try:
                    if isinstance(effect_value, dict) or type(effect_value).__name__ == "dict":
                        for skill_name, delta in effect_value.items():
                            try:
                                modify_base_skill(worker, skill_name, int(delta))
                            except Exception:
                                current = int(worker.get("skills", {}).get(skill_name, 0))
                                worker.setdefault("skills", {})[skill_name] = max(0, min(SKILL_MAX, current + int(delta)))
                    else:
                        renpy.log(f"WARNING: use_item skill_modifiers for '{item_id}' is not a dict: {type(effect_value)}")
                except Exception:
                    try:
                        renpy.log(f"ERROR: use_item skill_modifiers failed for '{item_id}' on '{worker.get('name','?')}' value={effect_value}")
                    except Exception:
                        pass
            elif effect_type in ("joy", "rebelliousness", "romance", "relationship"):
                try:
                    apply_attribute_change(worker, effect_type, int(effect_value))
                except Exception:
                    pass
            elif effect_type == "add_trait":
                # Support list, dict, or string
                try:
                    if type(effect_value).__name__ == "list" or isinstance(effect_value, (list, tuple)):
                        for t in effect_value:
                            if isinstance(t, dict) or type(t).__name__ == "dict":
                                store.add_trait_with_duration(worker, t.get("name", ""), t.get("duration", 0))
                            else:
                                store.add_trait_with_duration(worker, t, 0)
                    elif isinstance(effect_value, dict) or type(effect_value).__name__ == "dict":
                        store.add_trait_with_duration(worker, effect_value.get("name", ""), effect_value.get("duration", 0))
                    else:
                        store.add_trait_with_duration(worker, effect_value, 0)
                except Exception:
                    try:
                        renpy.log(f"ERROR: use_item add_trait failed for '{item_id}' on '{worker.get('name','?')}' value={effect_value}")
                    except Exception:
                        pass
            elif effect_type == "remove_trait":
                try:
                    if type(effect_value).__name__ == "list" or isinstance(effect_value, (list, tuple)):
                        for t in effect_value:
                            if isinstance(t, dict) or type(t).__name__ == "dict":
                                store.remove_trait_safe(worker, t.get("name", ""))
                            else:
                                store.remove_trait_safe(worker, t)
                    elif isinstance(effect_value, dict) or type(effect_value).__name__ == "dict":
                        store.remove_trait_safe(worker, effect_value.get("name", ""))
                    else:
                        store.remove_trait_safe(worker, effect_value)
                except Exception:
                    try:
                        renpy.log(f"ERROR: use_item remove_trait failed for '{item_id}' on '{worker.get('name','?')}' value={effect_value}")
                    except Exception:
                        pass
            else:
                # Ignore non-consumable fields like "cap" or "skill_modifiers"
                pass

        _remove_one(item_id)

        # Tutorial objective 5: mark when energy potion is used from a worker's inventory
        if worker and hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5:
            item_name = item.get("name", "") or ""
            if item_name.lower().find("energy") != -1 or item_id == "energy_potion":
                store.potion_used_on_worker = True
                renpy.log("DEBUG: Tutorial - Energy potion used on worker (from worker inventory)")
                try:
                    check_objective_completion()
                except Exception as e:
                    renpy.log(f"DEBUG: Tutorial - check_objective_completion error: {e}")

    def auto_consume_start_of_day(worker, threshold=0.30):
        """
        At start of day, auto-consume health_potion and energy_potion from the worker's inventory
        when health or energy is below threshold (fraction of max). Uses only health_potion and energy_potion.
        Applies effect and removes item without notifying (to avoid spam).
        """
        if not worker or not hasattr(worker, "get"):
            return
        inv = worker.get("inventory") or []
        if not isinstance(inv, list):
            return
        max_health = calculate_max_health(worker)
        max_energy = calculate_max_energy(worker)
        health_thresh = max(0, threshold * max_health)
        energy_thresh = max(0, threshold * max_energy)
        while True:
            need_health = worker.get("health", 0) < health_thresh
            need_energy = worker.get("energy", 0) < energy_thresh
            if not need_health and not need_energy:
                break
            found = None
            for i, entry in enumerate(inv):
                if not isinstance(entry, (list, tuple)) or len(entry) < 1:
                    continue
                item_id = (entry[0] if isinstance(entry[0], str) else str(entry[0])).strip()
                if item_id not in ("health_potion", "energy_potion"):
                    continue
                qty = 1
                if len(entry) >= 2 and entry[1] is not None:
                    try:
                        qty = int(entry[1])
                    except Exception:
                        pass
                if qty <= 0:
                    continue
                if item_id == "health_potion" and need_health:
                    found = (i, item_id, "health")
                    break
                if item_id == "energy_potion" and need_energy:
                    found = (i, item_id, "energy")
                    break
            if found is None:
                break
            idx, item_id, eff_type = found
            item_data = next((it for it in items_json.get("items", []) if it.get("id") == item_id), None)
            if not item_data or item_data.get("type") != "consumable":
                break
            effect = item_data.get("effect") or {}
            if eff_type == "health" and "health" in effect:
                worker["health"] = min(max_health, worker.get("health", 0) + int(effect.get("health", 0)))
            if eff_type == "energy" and "energy" in effect:
                worker["energy"] = min(max_energy, worker.get("energy", 0) + int(effect.get("energy", 0)))
            remove_item_from_inventory(inv, item_id, 1)
            renpy.log(f"Auto-consume: {worker.get('name', '?')} used 1x {item_id} ({eff_type} below {threshold*100:.0f}%)")

    def _get_first_profession_id_for_building(building):
        """Return the first profession id for this building type (e.g. 'prostitute' for brothel), or None."""
        if not building:
            return None
        btype_id = building.get("type")
        if not btype_id:
            return None
        for bt in building_types_json.get("building_types", []):
            if bt.get("id") == btype_id:
                profs = bt.get("professions") or []
                if profs and len(profs) > 0:
                    return profs[0].get("id")
                return None
        return None

    # process_manager_auto_rest: definido en building_logic.rpy (poner a descansar + restaurar).
    # No duplicar aquí para no sobrescribir esa versión.

    def evaluate_condition(condition_str):
        """
        Evaluates a condition string dynamically based on current game state.
        Supports basic comparisons (==, !=, >, <, >=, <=) and references to game variables.
        Handles AND/OR logic, flags, dates, and days passed. - Explicit Loop Version

        Args:
            condition_str (str): A string like "money >= 1000", "after_date:1,1,1", "after_days:10 AND has_flag:quest_active"

        Returns:
            bool: True if the condition is met, False otherwise
        """
        if not condition_str or not isinstance(condition_str, str):
            renpy.log(f"evaluate_condition: No condition provided or invalid format ('{condition_str}'), defaulting to True")
            return True

        condition_str = condition_str.strip() # Remove leading/trailing whitespace

        # Ensure calendar is initialized
        initialize_calendar()
        current_game_day = store.current_day
        current_game_month = store.current_month # 1-based
        current_game_year = store.current_year

        renpy.log(f"evaluate_condition: Top level evaluating '{condition_str}' with date {current_game_day}/{current_game_month}/{current_game_year}")

        try:
            # --- Handle logical operators FIRST using explicit loops ---
            if " AND " in condition_str:
                parts = condition_str.split(" AND ")
                renpy.log(f"evaluate_condition: Evaluating AND parts: {parts}")
                final_result = True # Start assuming true for AND
                for part in parts:
                    part_strip = part.strip()
                    renpy.log(f"evaluate_condition:   Recursing for AND part: '{part_strip}'")
                    part_result = evaluate_condition(part_strip) # Recursive call
                    renpy.log(f"evaluate_condition:   Result for '{part_strip}': {part_result}")
                    if not part_result:
                        final_result = False
                        break # Short-circuit AND
                renpy.log(f"evaluate_condition: AND final result for '{condition_str}' is {final_result}")
                return final_result # Return result for AND

            if " OR " in condition_str:
                parts = condition_str.split(" OR ")
                renpy.log(f"evaluate_condition: Evaluating OR parts: {parts}")
                final_result = False # Start assuming false for OR
                for part in parts:
                    part_strip = part.strip()
                    renpy.log(f"evaluate_condition:   Recursing for OR part: '{part_strip}'")
                    part_result = evaluate_condition(part_strip) # Recursive call
                    renpy.log(f"evaluate_condition:   Result for '{part_strip}': {part_result}")
                    if part_result:
                        final_result = True
                        break # Short-circuit OR
                renpy.log(f"evaluate_condition: OR final result for '{condition_str}' is {final_result}")
                return final_result # Return result for OR

            # --- If not AND/OR, evaluate the single condition ---
            renpy.log(f"evaluate_condition: Evaluating single condition: '{condition_str}'")

            if condition_str == "True": return True
            if condition_str == "False": return False

            if condition_str.startswith("has_flag:"):
                flag_name = condition_str.split(":", 1)[1].strip()
                result = flag_name in store.event_flags
                renpy.log(f"evaluate_condition: has_flag:{flag_name}? {result} (Flags: {store.event_flags})")
                return result

            if condition_str.startswith("flag_value:"):
                parts = condition_str.split(":", 1)[1].strip().split("=", 1)
                if len(parts) != 2:
                    renpy.log(f"evaluate_condition: Invalid flag_value format (missing '='): {condition_str}")
                    return False
                flag_name, value_str = parts
                flag_name = flag_name.strip(); value_str = value_str.strip()
                # Convert value string to appropriate type
                if value_str.lower() == "true": required_value = True
                elif value_str.lower() == "false": required_value = False
                elif value_str.isdigit(): required_value = int(value_str)
                else:
                    try:
                        required_value = float(value_str)
                        if required_value.is_integer(): required_value = int(required_value)
                    except ValueError: required_value = value_str # String comparison

                current_value = store.event_flags.get(flag_name)
                result = current_value == required_value
                renpy.log(f"evaluate_condition: flag_value:{flag_name}={value_str}? Current is {current_value}. Result: {result}")
                return result

            if condition_str.startswith("after_days_from_flag:"):
                parts = condition_str.split(":", 1)[1].strip().split(",")
                if len(parts) != 2:
                    renpy.log(f"evaluate_condition: Invalid after_days_from_flag format: {condition_str}")
                    return False
                flag_name, days_str = parts
                flag_name = flag_name.strip()
                days_to_wait = int(days_str.strip())
                
                if flag_name not in store.event_flags:
                    renpy.log(f"evaluate_condition: after_days_from_flag failed because flag '{flag_name}' is not set.")
                    return False
                    
                flag_timestamp = store.event_flags.get(flag_name)
                if not isinstance(flag_timestamp, (int, float)):
                    renpy.log(f"evaluate_condition: after_days_from_flag failed because flag '{flag_name}' is not a valid number ({flag_timestamp}).")
                    return False
                
                current_total_days = calculate_total_days()
                days_since_flag_set = current_total_days - flag_timestamp
                
                result = days_since_flag_set >= days_to_wait
                renpy.log(f"evaluate_condition: after_days_from_flag:{flag_name},{days_to_wait}? Days since: {days_since_flag_set}. Result: {result}")
                return result

            if condition_str.startswith("exact_date:"):
                # Format: exact_date:day,month (month is 1-based in JSON, matches specific day/month regardless of year)
                date_parts = condition_str.split(":", 1)[1].strip().split(",")
                if len(date_parts) != 2:
                    renpy.log(f"evaluate_condition: Invalid exact_date format: {condition_str}")
                    return False
                try:
                    required_day = int(date_parts[0]); required_month_1based = int(date_parts[1])
                except ValueError:
                    renpy.log(f"evaluate_condition: Invalid number in exact_date: {condition_str}")
                    return False

                # Check if current date matches exactly (day and month, any year) - both are 1-based now
                result = (current_game_day == required_day and current_game_month == required_month_1based)
                renpy.log(f"evaluate_condition: exact_date:{required_day},{required_month_1based}? Current={current_game_day}/{current_game_month}/{current_game_year}. Result: {result}")
                return result

            # New: check roster for a specific worker
            if condition_str.startswith("has_worker:"):
                target = condition_str.split(":", 1)[1].strip()
                result = any(w.get("name") == target for w in store.workers)
                renpy.log(f"evaluate_condition: has_worker:{target}? Result: {result}")
                return result

            if condition_str.startswith("not_has_worker:"):
                target = condition_str.split(":", 1)[1].strip()
                result = not any(w.get("name") == target for w in store.workers)
                renpy.log(f"evaluate_condition: not_has_worker:{target}? Result: {result}")
                return result

            if condition_str.startswith("after_date:"):
                # Format: after_date:day,month,year (month is 1-based in JSON)
                date_parts = condition_str.split(":", 1)[1].strip().split(",")
                if len(date_parts) != 3:
                    renpy.log(f"evaluate_condition: Invalid after_date format: {condition_str}")
                    return False
                try:
                    required_day = int(date_parts[0]); required_month_1based = int(date_parts[1]); required_year = int(date_parts[2])
                except ValueError:
                    renpy.log(f"evaluate_condition: Invalid number in after_date: {condition_str}")
                    return False

                # Compare dates
                if current_game_year > required_year: result = True
                elif current_game_year == required_year:
                    if current_game_month > required_month_0based: result = True
                    elif current_game_month == required_month_0based: result = current_game_day >= required_day
                    else: result = False # Current month is earlier in the same year
                else: result = False # Current year is earlier
                renpy.log(f"evaluate_condition: after_date:{required_day},{required_month_1based},{required_year}? Current={current_game_day},{current_game_month+1},{current_game_year}. Result: {result}")
                return result

            if condition_str.startswith("before_days:"):
                # Format: before_days:number (before specific number of days passed)
                days_str = condition_str.split(":", 1)[1].strip()
                try: required_days_limit = int(days_str)
                except ValueError:
                    renpy.log(f"evaluate_condition: Invalid number in before_days: {condition_str}")
                    return False

                # Calculate total days from start (Year 1, Month 1, Day 1) to current date
                current_total_days = (current_game_year - 1) * 12 * 28 + (current_game_month - 1) * 28 + current_game_day
                start_total_days = 1 # Day 1 of Month 1 (1-based) of Year 1
                days_passed = current_total_days - start_total_days
                result = days_passed < required_days_limit
                renpy.log(f"evaluate_condition: before_days:{required_days_limit}? Days passed: {days_passed}. Result: {result}")
                return result

            if condition_str.startswith("after_days:"):
                # Format: after_days:number (days passed since day 1, year 1)
                days_str = condition_str.split(":", 1)[1].strip()
                try: required_days_passed = int(days_str)
                except ValueError:
                    renpy.log(f"evaluate_condition: Invalid number in after_days: {condition_str}")
                    return False

                # Calculate total days from start (Year 1, Month 1, Day 1) to current date
                current_total_days = (current_game_year - 1) * 12 * 28 + (current_game_month - 1) * 28 + current_game_day
                start_total_days = 1 # Day 1 of Month 1 (1-based) of Year 1
                days_passed = current_total_days - start_total_days
                result = days_passed >= required_days_passed
                renpy.log(f"evaluate_condition: after_days:{required_days_passed}? Days passed: {days_passed}. Result: {result}")
                return result

            # --- Fallback eval for simple comparisons (use cautiously) ---
            renpy.log(f"evaluate_condition: No specific prefix matched. Trying fallback eval for '{condition_str}'.")
            try:
                safe_globals = {"__builtins__": {}}
                safe_locals = { "money": store.money, "store": store, "persistent": persistent, "available_buildings": available_buildings }
                # Basic check to prevent executing arbitrary functions via eval
                # Allow specific safe patterns like .get() or simple comparisons
                unsafe_patterns = re.compile(r"[()\[\]{}]") # Disallow brackets/braces/parens generally
                allowed_patterns = re.compile(r"\.get\(") # Allow .get( specifically
                if unsafe_patterns.search(condition_str) and not allowed_patterns.search(condition_str):
                    raise ValueError("Potential unsafe eval attempt detected")

                result = eval(condition_str, safe_globals, safe_locals)
                renpy.log(f"evaluate_condition: Fallback eval result for '{condition_str}': {result}")
                return bool(result) # Ensure boolean return
            except Exception as eval_e:
                renpy.log(f"evaluate_condition: Fallback eval FAILED for '{condition_str}': {eval_e} - Likely invalid syntax for eval.")
                return False # Fallback eval failed

        except Exception as e:
            renpy.log(f"Error during condition evaluation '{condition_str}': {e}")
            # import traceback # Uncomment for full traceback in log if needed
            # renpy.log(traceback.format_exc())
            return False # Fail closed on any unexpected error

    #################################
    # TRAITS – LOADING AND MODIFIERS
    #################################

    

    def get_inherited_traits_from_json_workers():
        """
        Get up to 3 traits from a random JSON non-unique worker.
        This makes procedural workers inherit traits from JSON workers.
        If you add Elf, Dwarf, etc. to JSON workers, procedural workers will automatically use them.
        """
        try:
            # Load all non-unique workers from JSON
            all_workers = load_workers(include_unique=False, include_encounter_only=True)
            
            if not all_workers:
                renpy.log("PROCEDURAL: No JSON non-unique workers found, defaulting to Human")
                return ["Human"]
            
            # Get traits from a random JSON non-unique worker (up to 3)
            random_worker = random.choice(all_workers)
            traits = random_worker.get("traits", [])
            
            if traits and len(traits) > 0:
                # Take up to 3 traits
                inherited_traits = traits[:3]
                renpy.log(f"PROCEDURAL: Inherited {len(inherited_traits)} traits {inherited_traits} from JSON worker '{random_worker.get('name', 'Unknown')}'")
                return inherited_traits
            else:
                renpy.log("PROCEDURAL: Random JSON worker has no traits, defaulting to Human")
                return ["Human"]
        except Exception as e:
            renpy.log(f"PROCEDURAL: Error getting inherited traits from JSON workers: {e}, defaulting to Human")
            return ["Human"]
    
    

    
    

    

    

    #################################
    # WORKER DEFAULTS & SPAWN LOGIC
    #################################

  
    

    def load_buy_workers(force_refresh=False, exclude_names=None):
        """
        Load workers available for purchase, prioritizing workers defined in JSON files.
        Generates procedural workers when needed, respecting the daily spawn limit.
        Refills once per day.
        
        Args:
            force_refresh: If True, always generate new workers even if it's the same day
            exclude_names: Set of worker names to avoid when possible (used on refresh to guarantee new/different workers)
        """
        global daily_spawns, available_workers
        
        # Check if we need to refill (is it a new day?)
        current_date = (store.current_day, store.current_month, store.current_year)
        last_refill = (store.last_worker_refill_day, store.last_worker_refill_month, store.last_worker_refill_year)
        
        is_new_day = (last_refill[0] is None or current_date != last_refill)
        stored_workers = getattr(store, "available_workers", [])
        is_missing_pool = not stored_workers
        
        renpy.log(
            f"WORKER REFILL CHECK - Current: {current_date}, Last: {last_refill}, "
            f"New day: {is_new_day}, Missing pool: {is_missing_pool}, Force refresh: {force_refresh}"
        )
        
        if not is_new_day and not is_missing_pool and not force_refresh:
            # Same day - return existing workers, filter out hired ones
            hired_names = {w["name"] for w in workers}
            available_workers = [w for w in store.available_workers if w.get("name") not in hired_names]
            renpy.log(f"Same day - using existing workers: {[w.get('name') for w in available_workers]}")
            return available_workers
        
        # NEW DAY or FORCED REFRESH - Refill workers
        exclude_set = set(exclude_names) if exclude_names else set()
        gender_filter = getattr(store, "buy_servants_filter_gender", None)  # When set, only load/generate workers of this gender
        if force_refresh:
            renpy.log(f"FORCED REFRESH - Generating new workers (exclude {len(exclude_set)} previous, gender_filter={gender_filter})")
        else:
            renpy.log(f"NEW DAY - Refilling workers (gender_filter={gender_filter})")
        
        # Load all workers from JSON
        all_workers = load_workers(include_unique=True, include_encounter_only=False)
        hired_names = {w["name"] for w in workers}
        
        renpy.log(f"BUY WORKERS: Total workers loaded: {len(all_workers)}")
        renpy.log(f"BUY WORKERS: Hired workers: {len(hired_names)}")
        
        # Count JSON workers before filtering
        total_json_before_filter = [w for w in all_workers if not w.get("procedural", False)]
        renpy.log(f"BUY WORKERS: Total JSON workers (before filters): {len(total_json_before_filter)}")
        
        # Get available JSON workers (not hired, not dead, not recruit_only, not unique, not monsters)
        # Unique workers should only appear in special recruitment events, not in the normal buy menu
        # Monsters should ONLY appear in monster capture events, never in buy menu or recruitment events
        json_workers = []
        filtered_out = {
            "procedural": 0,
            "recruit_only": 0,
            "unique": 0,
            "monster": 0,
            "hired": 0,
            "dead": 0
        }
        
        for w in all_workers:
            if w.get("procedural", False):
                filtered_out["procedural"] += 1
                continue
            if w.get("recruit_only", False):
                filtered_out["recruit_only"] += 1
                continue
            if w.get("unique", False):
                filtered_out["unique"] += 1
                continue
            if w.get("monster", False):
                filtered_out["monster"] += 1
                continue
            if w["name"] in hired_names:
                filtered_out["hired"] += 1
                continue
            if is_worker_dead(w["name"]):
                filtered_out["dead"] += 1
                continue
            json_workers.append(w)
        
        renpy.log(f"BUY WORKERS: Filtered out - procedural: {filtered_out['procedural']}, recruit_only: {filtered_out['recruit_only']}, unique: {filtered_out['unique']}, monster: {filtered_out['monster']}, hired: {filtered_out['hired']}, dead: {filtered_out['dead']}")
        # Apply gender filter so refresh guarantees only workers of selected gender (when filter is set)
        if gender_filter:
            json_workers = [w for w in json_workers if w.get("gender") == gender_filter]
            renpy.log(f"BUY WORKERS: After gender filter '{gender_filter}': {len(json_workers)} JSON workers")
        renpy.log(f"BUY WORKERS: Available JSON workers: {len(json_workers)}")
        if len(json_workers) > 0:
            renpy.log(f"BUY WORKERS: JSON worker names: {[w['name'] for w in json_workers[:10]]}")  # Log first 10
        else:
            renpy.log("BUY WORKERS: WARNING - No JSON workers available! Check filters.")
            if filtered_out["hired"] > 0:
                renpy.log(f"BUY WORKERS: All {filtered_out['hired']} JSON workers are hired. Consider firing some to see them in the market.")
        
        # Start fresh
        available_workers = []
        
        # Mixed system: JSON workers have maximum priority
        # On refresh (exclude_set): prefer workers NOT in exclude_set so at least half / all change
        target_count = 5
        json_selected = []
        procedural_selected = []
        
        if len(json_workers) > 0:
            # On refresh, split into "new" (not in previous list) and "old" (in previous list)
            if exclude_set:
                json_new = [w for w in json_workers if w["name"] not in exclude_set]
                random.shuffle(json_new)
                # On refresh: only use workers NOT in the previous list; fill the rest with procedural (never reuse excluded)
                for w in json_new:
                    if len(available_workers) >= target_count:
                        break
                    json_selected.append(w)
                    available_workers.append(w)
                renpy.log(f"BUY WORKERS (refresh): {len(json_new)} new (excluded previous), rest will be procedural. Selected so far: {[w['name'] for w in json_selected]}")
            else:
                random.shuffle(json_workers)
                json_count_to_use = min(len(json_workers), target_count)
                for i in range(json_count_to_use):
                    if len(available_workers) >= target_count:
                        break
                    json_selected.append(json_workers[i])
                    available_workers.append(json_workers[i])
                renpy.log(f"JSON workers available: {len(json_workers)}, using {len(json_selected)}: {[w['name'] for w in json_selected]}")
        else:
            renpy.log("No JSON workers available (all hired, dead, or filtered out)")
        
        renpy.log(f"Selected {len(json_selected)} JSON workers: {[w['name'] for w in json_selected]}")
        
        # Fill remaining slots with procedural workers if needed
        remaining_slots = target_count - len(available_workers)
        if remaining_slots > 0:
            renpy.log(f"Filling {remaining_slots} remaining slots with procedural workers (daily_spawns: {daily_spawns})")
            attempts = 0
            max_attempts = 20  # Prevent infinite loop
            spawn_filters = {"gender": gender_filter} if gender_filter else {}
            while len(available_workers) < target_count and attempts < max_attempts:
                attempts += 1
                new_worker = spawn_new_worker(filters=spawn_filters)
                if new_worker:
                    new_worker["market_worker"] = True
                    new_worker["procedural"] = True
                    new_worker["comfort_desired"] = 1  # Buy servants workers always require comfort level 1
                    available_workers.append(new_worker)
                    procedural_selected.append(new_worker)
                    # Only increment daily_spawns if we haven't exceeded the daily limit
                    if daily_spawns < 5:
                        daily_spawns += 1
                    renpy.log(f"Generated procedural worker: {new_worker['name']} (daily_spawns: {daily_spawns}, attempt: {attempts})")
                else:
                    renpy.log(f"spawn_new_worker() returned None (attempt: {attempts})")
            if len(available_workers) < target_count:
                renpy.log(f"WARNING: Only generated {len(available_workers)} workers out of {target_count} requested (attempts: {attempts})")
        
        renpy.log(f"Final selection: {len(json_selected)} JSON + {len(procedural_selected)} procedural = {len(available_workers)} total")
        
        # Apply defaults and ensure min traits (worker_loader's inline logic, same context as file load)
        for worker in available_workers:
            ensure_worker_defaults(worker)
            if hasattr(store, "_ensure_worker_min_traits"):
                store._ensure_worker_min_traits(worker)
            worker["market_worker"] = True
            worker["comfort_desired"] = 1  # Buy servants workers always require comfort level 1
        
        # Update store
        store.available_workers = available_workers
        store.last_worker_refill_day = store.current_day
        store.last_worker_refill_month = store.current_month
        store.last_worker_refill_year = store.current_year
        
        renpy.log(f"Refilled workers: {[w['name'] for w in available_workers]}")
        return available_workers

    def _ensure_buy_workers_loaded():
        """Helper function to ensure workers are loaded when buy_servants_table screen is shown."""
        if renpy.predicting():
            return  # Skip during prediction - renpy.file() fails, would cache workers without traits
        try:
            load_buy_workers()
            update_displayed_workers()
        except Exception as e:
            renpy.log(f"Error in _ensure_buy_workers_loaded: {e}")
    
    def refresh_buy_workers():
        """Refresh the buy workers list: 1 free, 1 paid (2500$)."""
        global map_worker_refill_count, last_map_refill_day, available_workers
        
        renpy.log("BUY SERVANTS: refresh_buy_workers called")
        
        # Check if it's a new day - reset counter if so
        if store.last_map_refill_day != store.current_day:
            store.map_worker_refill_count = 0
            store.last_map_refill_day = store.current_day
            renpy.log(f"BUY SERVANTS: New day detected, reset counter")
        
        # Use store variable to ensure consistency
        current_count = store.map_worker_refill_count
        
        # Check if we can refresh (max 2 times per day: 1 free, 1 paid)
        if current_count >= 2:
            renpy.log("BUY SERVANTS: Refresh limit reached (2/2)")
            return
        
        # Check if this is the paid refresh (second one)
        is_paid_refresh = (current_count == 1)
        refresh_cost = 2500 if is_paid_refresh else 0
        
        # Check if player has enough money for paid refresh
        if is_paid_refresh:
            if not hasattr(store, 'money') or store.money < refresh_cost:
                renpy.log(f"BUY SERVANTS: Not enough money for paid refresh. Need {refresh_cost}, have {getattr(store, 'money', 0)}")
                return
        
        # Charge money for paid refresh
        if is_paid_refresh:
            store.money -= refresh_cost
            renpy.log(f"BUY SERVANTS: Charged {refresh_cost}$ for refresh. Remaining money: {store.money}")
        
        # Refresh workers - force new pool, excluding current ones so at least half / all change
        refresh_type = "paid" if is_paid_refresh else "free"
        exclude_names = {w["name"] for w in (getattr(store, "available_workers", []) or [])}
        renpy.log(f"BUY SERVANTS: Refreshing workers ({refresh_type}, count: {current_count + 1}/2), excluding: {exclude_names}")
        try:
            load_buy_workers(force_refresh=True, exclude_names=exclude_names)
            update_displayed_workers()
            # Update store variable directly
            store.map_worker_refill_count = current_count + 1
            # Also update global for compatibility
            map_worker_refill_count = store.map_worker_refill_count
            renpy.log(f"BUY SERVANTS: Workers refreshed. New count: {store.map_worker_refill_count}/2, available: {len(available_workers)}")
            # Force screen refresh to update button text and state
            renpy.restart_interaction()
        except Exception as e:
            renpy.log(f"BUY SERVANTS: Error refreshing workers: {e}")
            import traceback
            renpy.log(f"BUY SERVANTS: Traceback: {traceback.format_exc()}")
    
    # Make sure function is in store
    store.refresh_buy_workers = refresh_buy_workers

    def load_recruit_workers():
        """
        Build the Recruitment pool, prioritizing workers defined in JSON files.
        """
        # Load all workers, including unique and encounter-only ones
        all_workers = load_workers(include_unique=True, include_encounter_only=True)
        
        # Filter to include only unique or encounter-only workers, excluding monsters
        # Also filter by NSFW setting: 
        # - If NSFW enabled: only include NSFW workers
        # - If NSFW disabled: only include SFW workers
        recruit_pool = [
            w for w in all_workers
            if (w.get("unique", False) or w.get("encounter_only", False)) 
            and not w.get("monster", False)
            and (w.get("nsfw", False) == persistent.nsfw_enabled)
        ]
        
        # Remove workers that have already been recruited
        recruited_names = {w["name"] for w in store.workers}
        available_recruit = [
            w for w in recruit_pool
            if w["name"] not in recruited_names
        ]
        
        # Log available workers for debugging
        renpy.log(f"LOAD RECRUIT WORKERS: NSFW mode enabled: {persistent.nsfw_enabled}")
        renpy.log(f"LOAD RECRUIT WORKERS: Total workers loaded: {len(all_workers)}")
        renpy.log(f"LOAD RECRUIT WORKERS: Worker names loaded: {[w.get('name', 'Unknown') for w in all_workers[:20]]}")  # First 20
        renpy.log(f"LOAD RECRUIT WORKERS: Total workers before NSFW filter: {len(recruit_pool)}")
        renpy.log(f"LOAD RECRUIT WORKERS: Recruited workers: {[w['name'] for w in store.workers]}")
        renpy.log(f"LOAD RECRUIT WORKERS: Available workers for recruitment: {[w['name'] for w in available_recruit]}")
        renpy.log(f"LOAD RECRUIT WORKERS: NSFW status of available workers: {[(w['name'], w.get('nsfw', False)) for w in available_recruit]}")
        
        # Only generate procedural workers if no JSON-defined workers are available
        if not available_recruit:
            renpy.log("No JSON-defined workers available, generating procedural workers")
            available_recruit = [spawn_new_worker() for _ in range(6)]

        # Apply defaults and ensure min 3-5 traits (same as load_buy_workers)
        for worker in available_recruit:
            ensure_worker_defaults(worker)
            if hasattr(store, "_ensure_worker_min_traits"):
                store._ensure_worker_min_traits(worker)

        return available_recruit

    def is_worker_available(worker_name=None, random_worker=False, for_events=False):
        """
        Check if a specific worker or any worker is available for recruitment.
        
        Args:
            worker_name (str, optional): Name of the specific worker to check.
            random_worker (bool): If True, checks for any available worker instead.
            for_events (bool): If True, includes encounter-only workers for event-specific checks.
        
        Returns:
            tuple: (bool, dict or None) - (is_available, worker or None)
        """
        all_workers = load_workers(include_unique=True, include_encounter_only=True, for_events=for_events)
        recruited_names = {w["name"] for w in store.workers}
        
        if random_worker:
            # For random workers in events, we want to include encounter_only workers
            available_workers = [w for w in all_workers 
                                if w["name"] not in recruited_names 
                                and not is_worker_dead(w["name"])
                                and not w.get("monster", False)]  # Only filter out monsters
            if available_workers:
                return (True, random.choice(available_workers))
            return (False, None)
        elif worker_name:
            worker = next((w for w in all_workers if w["name"] == worker_name), None)
            # Monsters should only be available in capture events, not in normal recruitment
            if worker and worker["name"] not in recruited_names and not is_worker_dead(worker["name"]) and not worker.get("monster", False):
                return (True, worker)
            return (False, None)
        return (False, None)

    
    def loot_monster_worker(filters=None):
        """
        Loot a monster-worker and add it to the player's roster with a unique name.
        Returns the worker if successful, None if not.
        """
        if filters is None:
            filters = {"monster": True}  # Default to monster workers only
        
        # Load all workers, including unique and encounter-only ones
        all_workers = load_workers(include_unique=True, include_encounter_only=True)
        
        # Filter out already hired workers
        hired_worker_names = {w["name"] for w in store.workers}
        available_workers = [w for w in all_workers if w["name"] not in hired_worker_names]
        
        # Apply filters strictly
        filtered_workers = []
        for w in available_workers:
            match = True
            for key, value in filters.items():
                if w.get(key) != value:
                    match = False
                    break
            if match:
                filtered_workers.append(w)
        
        # If we found JSON-defined workers, pick one and clone it with a new name
        if filtered_workers:
            original_worker = random.choice(filtered_workers)
            worker = original_worker.copy()
            
            # Generate a new unique name if names_list is specified
            if "names_list" in worker:
                name_category, gender = worker["names_list"].split("_") if "_" in worker["names_list"] else (worker["names_list"], "female")
                name_pool = name_lists.get(f"{name_category}_{gender}", ["Unknown"])
                
                # Find all existing names (hired + available)
                existing_names = {w["name"] for w in store.workers + store.available_workers}
                
                # Use improved name generation
                worker["name"] = generate_unique_name(name_pool, existing_names)
        
        # If no JSON-defined workers found, generate a procedural one
        else:
            worker = spawn_new_monster_worker()
            if worker:
                # Apply filters to the new worker
                for key, value in filters.items():
                    worker[key] = value
        
        if not worker:
            renpy.notify("No monster workers available to capture.")
            return None
        
        # Ensure defaults are applied (including monster-specific ones)
        ensure_worker_defaults(worker)
        worker["assigned_building"] = "Unassigned"  # Captured workers are never pre-assigned

        # Return the worker without adding to roster here - let the caller handle it
        return worker

    def spawn_new_monster_worker():
        """
        Generate a new procedural monster worker with proper name generation.
        """
        # Define monster name pools with gender-specific options
        monster_names = {
            "male": ["Goblin", "Orc", "Troll", "Minotaur", "Ogre", "Gnoll", "Bugbear"],
            "female": ["Harpy", "Siren", "Banshee", "Succubus", "Dryad", "Lamia", "Hag"]
        }
        
        # Randomly select gender, respecting worker_gender_filter (Only Male / Only Female)
        filter_mode = getattr(persistent, "worker_gender_filter", "both")
        if filter_mode == "female":
            gender = "female"
        elif filter_mode == "male":
            gender = "male"
        else:
            gender = random.choice(["male", "female"])
        name_pool = monster_names[gender]
        
        # Get all existing names to ensure uniqueness
        existing_names = {w["name"] for w in store.workers + store.available_workers}
        
        # Generate unique name using improved algorithm
        final_name = generate_unique_name(name_pool, existing_names)
        
        # Create skills with emphasis on combat skills (Extreme and Combat)
        skills = {skill_name: random.randint(5, 15) for skill_name in skill_names.keys()}
        skills["Extreme"] = min(100, random.randint(15, 25))  # Extreme skill (capped at 100)
        skills["Combat"] = min(100, random.randint(15, 25))  # Combat skill (capped at 100)
        
        # Generate traits (2-3 random traits)
        possible_traits = ["Robust", "Fearless", "Mystical", "Charming", "Aggressive", "Wild"]
        num_traits = random.randint(2, 3)
        traits = random.sample(possible_traits, num_traits)
        
        new_worker = {
            "name": final_name,
            "folder": "monsters",
            "gender": gender,
            "cost": random.randint(500, 1500),
            "nsfw": True,  # Most monsters are NSFW by default
            "encounter_only": True,
            "monster": True,
            "unique": False,  # Procedural monsters aren't unique
            "skills": skills,
            "traits": traits,
            "description": f"A {final_name.lower()} captured from the wild, now serving in your establishment.",
            "level": 1,
            "energy": 50,
            "health": 100,
            "rebelliousness": random.randint(30, 70),
            "joy": random.randint(20, 60),
            "romance": 0,
            "relationship": 10,
            "comfort_level": 1,
            "skill_uses": {skill_name: 0 for skill_name in skill_names.keys()},
            "success_count": 0
        }
        
        return new_worker

    def loot_normal_worker(filters=None):
        """Spawn non-monster workers"""
        filters = filters or {}
        existing_names = {w["name"] for w in store.workers}
        
        # Try to find existing worker first
        all_workers = load_workers(include_unique=True, include_encounter_only=True)
        candidates = [
            w for w in all_workers
            if all(
                (isinstance(v, dict) and w.get(k, {}).items() >= v.items()) or 
                (w.get(k) == v)
                for k, v in filters.items()
            )
            and w["name"] not in existing_names
            and not w.get("monster", False)
        ]
        
        if candidates:
            return random.choice(candidates)
        
        # Fallback to procedural generation
        return spawn_new_worker(filters=filters)

    def update_skill_levels():
        """
        For each worker, check each skill's uses. If skill_uses >= current skill level,
        level up that skill by 1 and reset the skill_uses counter.
        """
        renpy.log("=== update_skill_levels() called ===")
        for worker in store.workers:
            worker_name = worker.get("name", "Unknown")
            # Ensure skill_uses exists
            if "skill_uses" not in worker:
                worker["skill_uses"] = {}
                renpy.log(f"Initialized skill_uses for {worker_name}")
            
            # Use worker["skills"] as the single source of truth for base skill levels
            # Trait and item bonuses are calculated dynamically in calculate_skill_with_traits()
            base_skills = worker.get("skills", {})
            
            if not base_skills:
                renpy.log(f"WARNING: {worker_name} has no skills!")
                continue
            
            # Ensure skill_uses is initialized for all skills
            if "skill_uses" not in worker:
                worker["skill_uses"] = {}
            
            # Check each skill for level ups
            for skill_name in list(base_skills.keys()):  # Use list() to avoid modification during iteration
                # Read current skill level directly from the dict
                current_skill_level = int(base_skills.get(skill_name, 0))
                skill_uses = int(worker["skill_uses"].get(skill_name, 0))
                
                # Determine uses needed for level up
                # Tiered system: fast early, slows down after 75, very hard after 85
                if current_skill_level <= 0:
                    uses_needed = 1  # Level 0 needs 1 use
                elif current_skill_level <= 75:
                    # Fast progression: 1-6 uses based on tier
                    uses_needed = max(1, current_skill_level // 15 + 1)
                else:
                    # Exponential slowdown after 75
                    excess = current_skill_level - 75
                    uses_needed = 6 + int(excess ** 1.8 / 5)
                
                # Log for debugging
                if skill_uses > 0:
                    renpy.log(f"{worker_name} - {skill_name}: level={current_skill_level}, uses={skill_uses}, needed={uses_needed}")
                
                # If uses meet or exceed threshold, level up the skill
                if skill_uses >= uses_needed and uses_needed > 0:
                    old_level = current_skill_level
                    renpy.log(f"LEVEL UP: {worker_name}'s {skill_name} from {old_level} to {old_level + 1} (uses: {skill_uses} >= needed: {uses_needed})")
                    # Use modify_base_skill to increment by 1 and ensure it stays within bounds
                    new_level = modify_base_skill(worker, skill_name, 1)
                    # Reset skill_uses counter
                    worker["skill_uses"][skill_name] = 0
                    renpy.notify(f"{worker_name}'s {skill_name} skill leveled up from {old_level} to {new_level}!")
                    
                    # Reduce rebelliousness when leveling up a skill (worker feels satisfied with progress)
                    comfort = worker.get("comfort_level", 1)
                    current_rebelliousness = worker.get("rebelliousness", 50)
                    new_rebelliousness = max(0, current_rebelliousness - comfort)
                    set_attribute_with_caps(worker, "rebelliousness", new_rebelliousness)
                    renpy.log(f"Skill level up reduces {worker_name}'s rebelliousness: {current_rebelliousness} -> {new_rebelliousness} (-{comfort} from comfort)")
        renpy.log("=== update_skill_levels() finished ===")

    def add_academy_training_skill_uses(worker, profession, primary_skill=None):
        """
        Add skill_uses to a worker based on Academy profession. Total experience per day ~10.
        - Academics: Clever + one random skill (from distribution).
        - Amatory: the daily story's skill (primary_skill) + one other random sex skill (5 each).
        - Hospitality: Charm + Service (from distribution).
        Returns a dict of {skill_name: uses_added} for use in daily report description.
        """
        import random
        applied = {}
        dist = profession.get("training_skills_distribution") or {}
        worker.setdefault("skill_uses", {})
        profession_id = profession.get("id", "")

        # Amatory: each daily story affects the chosen skill + one other random sex skill (5 each, total 10)
        if profession_id == "academy_amatory" and primary_skill:
            uses_per_skill = 5
            amatory_skills = [s for s in (profession.get("skills") or []) if s in worker.get("skills", {})]
            if primary_skill in worker.get("skills", {}):
                worker["skill_uses"][primary_skill] = worker["skill_uses"].get(primary_skill, 0) + uses_per_skill
                applied[primary_skill] = applied.get(primary_skill, 0) + uses_per_skill
                renpy.log(f"Academy training: {worker.get('name','Unknown')} +{uses_per_skill} uses to {primary_skill} (story focus)")
            other_candidates = [s for s in amatory_skills if s != primary_skill]
            if other_candidates:
                chosen = random.choice(other_candidates)
                worker["skill_uses"][chosen] = worker["skill_uses"].get(chosen, 0) + uses_per_skill
                applied[chosen] = applied.get(chosen, 0) + uses_per_skill
                renpy.log(f"Academy training: {worker.get('name','Unknown')} +{uses_per_skill} uses to {chosen} (random other)")
            return applied

        if not dist:
            return applied
        # Academics / Hospitality: use distribution (already scaled to 10 total in JSON)
        if "random_one" in dist:
            uses_random = int(dist.get("random_one", 0))
            skill_names_list = list(worker.get("skills", {}).keys())
            if skill_names_list:
                exclude = [s for s in dist.keys() if s != "random_one"]
                candidates = [s for s in skill_names_list if s not in exclude]
                if not candidates:
                    candidates = skill_names_list
                chosen = random.choice(candidates)
                worker["skill_uses"][chosen] = worker["skill_uses"].get(chosen, 0) + uses_random
                applied[chosen] = applied.get(chosen, 0) + uses_random
                renpy.log(f"Academy training: {worker.get('name','Unknown')} +{uses_random} uses to {chosen} (random_one)")
        for skill_name, uses in dist.items():
            if skill_name == "random_one":
                continue
            if skill_name not in worker.get("skills", {}):
                continue
            add_val = int(uses) if uses else 0
            if add_val <= 0:
                continue
            worker["skill_uses"][skill_name] = worker["skill_uses"].get(skill_name, 0) + add_val
            applied[skill_name] = applied.get(skill_name, 0) + add_val
            renpy.log(f"Academy training: {worker.get('name','Unknown')} +{add_val} uses to {skill_name}")
        return applied

    def update_worker_levels():
        """
        For each worker, if the overall success_count reaches or exceeds 20 * (current level),
        level up the worker (increase level by 1) and reset the success_count.
        """
        for worker in store.workers:
            threshold = 20 * worker.get("level", 1)
            if worker.get("success_count", 0) >= threshold:
                old_level = worker["level"]
                worker["level"] += 1
                worker["success_count"] = 0
                renpy.notify(f"{worker['name']} leveled up from {old_level} to {worker['level']}!")
                
                # Reduce rebelliousness when leveling up (worker feels satisfied with progress)
                comfort = worker.get("comfort_level", 1)
                current_rebelliousness = worker.get("rebelliousness", 50)
                new_rebelliousness = max(0, current_rebelliousness - comfort)
                set_attribute_with_caps(worker, "rebelliousness", new_rebelliousness)
                renpy.log(f"Level up reduces {worker['name']}'s rebelliousness: {current_rebelliousness} -> {new_rebelliousness} (-{comfort} from comfort)")


    def recruit_worker(worker):
        worker["is_servant"] = False
        worker["source"] = "recruited"
        worker["assigned_building"] = "Unassigned"  # New recruits are never pre-assigned
        # Defensive cleanup: if a stale servant_jobs entry exists for this name in any building
        # (e.g. from old saves / name collisions), remove it so the recruit stays unassigned.
        try:
            wname = worker.get("name")
            if wname:
                for _bname, _b in available_buildings.items():
                    if not isinstance(_b, dict):
                        continue
                    jobs = _b.get("servant_jobs")
                    if isinstance(jobs, dict) and wname in jobs:
                        del jobs[wname]
                    assigned = _b.get("assigned_servants")
                    if isinstance(assigned, list):
                        _b["assigned_servants"] = [
                            aw for aw in assigned
                            if not (isinstance(aw, dict) and aw.get("name") == wname)
                        ]
        except Exception as e:
            renpy.log(f"recruit_worker stale assignment cleanup error: {e}")
        workers.append(worker)
        if worker in available_workers:
            available_workers.remove(worker)
        store.can_recruit_today = False
        
        # Tutorial tracking
        if hasattr(store, 'tutorial_active') and store.tutorial_active:
            store.workers_hired += 1
            store.total_workers += 1
            renpy.log(f"DEBUG: Worker hired! workers_hired: {store.workers_hired}, current_objective: {store.current_objective}")
            # Only trigger when we reach exactly 3 workers for objective 1
            if store.current_objective == 1 and store.workers_hired == 3:
                renpy.log("DEBUG: Reached 3 workers! Calling check_tutorial_objective...")
                renpy.log(f"DEBUG: Before calling - tutorial_active: {store.tutorial_active}, current_objective: {store.current_objective}, workers_hired: {store.workers_hired}, objective_1_complete: {store.objective_1_complete}")
                check_tutorial_objective()
                renpy.log("DEBUG: After calling check_tutorial_objective")
        
        renpy.notify(f"{worker['name']} has joined your team!")
        renpy.hide_screen("recruitment_event_screen")
        update_displayed_workers()
        # Only jump to tavern screen if not inside recruitment flow
        if not getattr(store, 'in_recruitment', False):
            renpy.jump("tavern_screen")

    def generate_unique_name(name_pool, existing_names):
        """
        Generate a unique name from a pool, trying all unique names before adding numbers.
        """
        # Shuffle the name pool to randomize selection
        available_names = list(name_pool)
        random.shuffle(available_names)
        
        # Try to find a completely unique name first
        for name in available_names:
            if name not in existing_names:
                return name
        
        # If all names are taken, find the base name with the lowest suffix
        best_base = None
        lowest_suffix = float('inf')
        
        for base_name in available_names:
            # Count existing numbered versions of this base name
            current_suffix = 1
            while f"{base_name} {current_suffix}" in existing_names:
                current_suffix += 1
            
            # Use the base name with the lowest next available suffix
            if current_suffix < lowest_suffix:
                lowest_suffix = current_suffix
                best_base = base_name
        
        # Return the name with the lowest suffix
        if best_base:
            return f"{best_base} {lowest_suffix}"
        
        # Fallback (should never happen)
        return f"{random.choice(available_names)} {random.randint(1000, 9999)}"

    def spawn_new_worker(filters=None):
        """Generate a new procedural worker based on existing non-unique workers as templates."""
        filters = filters or {}
        
        # Get available non-unique workers as templates
        # IMPORTANT: Include ALL non-unique workers as templates, even if already recruited
        # This ensures variety in procedural worker generation
        # Load workers WITHOUT filtering by recruitment status - we want ALL templates
        all_workers = load_workers(include_unique=True, include_encounter_only=True)
        
        # Filter for non-unique, non-monster, non-procedural workers that match NSFW setting
        template_workers = [
            w for w in all_workers
            if not w.get("unique", False) 
            and not w.get("monster", False)
            and not w.get("procedural", False)  # Don't use procedural workers as templates
            and w.get("nsfw", False) == persistent.nsfw_enabled  # Match NSFW setting
        ]
        # When gender filter is set (e.g. from Buy Servants), only use templates of that gender so procedural worker matches
        if filters and filters.get("gender"):
            requested_gender = filters.get("gender")
            template_workers = [w for w in template_workers if w.get("gender") == requested_gender]
            if not template_workers:
                renpy.log(f"SPAWN NEW WORKER: No templates for gender '{requested_gender}', using default spawn")
                return spawn_new_worker_default(filters)
            renpy.log(f"SPAWN NEW WORKER: Filtered to {len(template_workers)} templates for gender '{requested_gender}'")
        
        renpy.log(f"SPAWN NEW WORKER: Total workers loaded: {len(all_workers)}")
        renpy.log(f"SPAWN NEW WORKER: Found {len(template_workers)} template workers")
        renpy.log(f"SPAWN NEW WORKER: Template names: {[w.get('name', 'Unknown') for w in template_workers]}")
        
        if not template_workers:
            renpy.log("SPAWN NEW WORKER: No templates available, using default")
            # Fallback to default creation if no templates available
            return spawn_new_worker_default(filters)
        
        # Choose a random template to ensure variety
        # Shuffle to avoid always picking the same template
        random.shuffle(template_workers)
        template = random.choice(template_workers)
        renpy.log(f"SPAWN NEW WORKER: Selected template: {template.get('name', 'Unknown')} from {len(template_workers)} options")
        
        # Generate unique name using improved algorithm
        existing_names = {w["name"] for w in store.workers}
        if hasattr(store, "available_workers"):
            existing_names.update({w["name"] for w in store.available_workers})
        
        # Use template's name list for appropriate names
        names_list = template.get("names_list", "western_female")
        name_pool = name_lists.get(names_list, ["Unknown"])
        
        final_name = generate_unique_name(name_pool, existing_names)
        
        # Create new worker based on template
        new_worker = template.copy()
        
        # Use template traits as the base so procedural workers match the template's race/theme
        base_traits = template.get("traits", [])
        if not isinstance(base_traits, list) or not base_traits:
            base_traits = ["Human"]
        
        # Generate skills with guarantee that at least 2 have minimum 35
        skills = {}
        skill_names_list = list(template["skills"].keys())
        random.shuffle(skill_names_list)  # Shuffle to randomize which skills get the guarantee
        
        # First, generate all skills normally
        for skill_name in skill_names_list:
            roll = random.random()
            skills[skill_name] = (
                random.randint(12, 28) if roll < 0.5
                else random.randint(25, 40) if roll < 0.8
                else random.randint(35, 50)
            )
        
        # Guarantee at least 2 skills have minimum 35
        skills_under_35 = [name for name, value in skills.items() if value < 35]
        if len(skills_under_35) >= 2:
            # Randomly select 2 skills to boost to at least 35
            skills_to_boost = random.sample(skills_under_35, 2)
            for skill_name in skills_to_boost:
                skills[skill_name] = random.randint(35, 50)  # Boost to 35-50
        elif len(skills_under_35) == 1:
            # Only 1 skill under 35, boost it and find another to boost
            skills[skills_under_35[0]] = random.randint(35, 50)
            # Find a skill that's already >= 35 but could be higher, or boost another
            other_skills = [name for name in skill_names_list if name not in skills_under_35]
            if other_skills:
                skills[random.choice(other_skills)] = random.randint(35, 50)
        
        new_worker.update({
            "name": final_name,
            "procedural": True,
            "unique": False,
            "encounter_only": False,
            "skills": skills,
            "cost": random.randint(1000, 1500),  # Minimum price increased to 1000
            "rebelliousness": random.randint(20, 80),
            "joy": random.randint(20, 80),
            "comfort_desired": 5,  # Procedural workers always require comfort level 5
            "description": f"A skilled worker from the {template.get('folder', 'unknown')} region.",
            "traits": list(base_traits),  # Keep template traits (e.g., race) for image consistency
            "assigned_building": "Unassigned"  # Never inherit template's building assignment
        })
        
        ensure_worker_defaults(new_worker)
        if hasattr(store, "_ensure_worker_min_traits"):
            store._ensure_worker_min_traits(new_worker)
        
        return new_worker

    def spawn_new_worker_default(filters=None):
        """Fallback: Generate a basic procedural worker when no templates available."""
        filters = filters or {}
        # Use requested gender from filter (e.g. Buy Servants) or random
        gender = (filters.get("gender") if filters else None) or random.choice(["male", "female"])
        name_category = random.choice(["western", "eastern", "fantasy"])
        
        # Get name from appropriate pool
        name_pool = name_lists.get(f"{name_category}_{gender}", ["Unknown"])
        
        # Generate unique name using improved algorithm
        existing_names = {w["name"] for w in store.workers}
        if hasattr(store, "available_workers"):
            existing_names.update({w["name"] for w in store.available_workers})
        
        final_name = generate_unique_name(name_pool, existing_names)
        
        # Assign a random folder from available worker folders (extract dynamically from loaded workers)
        all_workers = load_workers(include_unique=True, include_encounter_only=True)
        available_folders = list(set(w.get("folder", "aspen") for w in all_workers if w.get("folder")))
        if not available_folders:
            available_folders = ["aspen"]  # Fallback to default
        assigned_folder = random.choice(available_folders)
        
        # Try to align traits with a worker that uses the same folder
        folder_template = next((w for w in all_workers if w.get("folder") == assigned_folder and w.get("traits")), None)
        base_traits = folder_template.get("traits", []) if folder_template else []
        if not isinstance(base_traits, list) or not base_traits:
            base_traits = get_inherited_traits_from_json_workers()
        
        # Create the new worker with named skills only
        # Generate skills with guarantee that at least 2 have minimum 35
        skill_names_list = list(skill_names.keys())
        random.shuffle(skill_names_list)  # Shuffle to randomize which skills get the guarantee
        
        # First, generate all skills normally
        skills = {}
        for skill_name in skill_names_list:
            roll = random.random()
            skills[skill_name] = (
                random.randint(12, 28) if roll < 0.5
                else random.randint(25, 40) if roll < 0.8
                else random.randint(35, 50)
            )
        
        # Guarantee at least 2 skills have minimum 35
        skills_under_35 = [name for name, value in skills.items() if value < 35]
        if len(skills_under_35) >= 2:
            # Randomly select 2 skills to boost to at least 35
            skills_to_boost = random.sample(skills_under_35, 2)
            for skill_name in skills_to_boost:
                skills[skill_name] = random.randint(35, 50)  # Boost to 35-50
        elif len(skills_under_35) == 1:
            # Only 1 skill under 35, boost it and find another to boost
            skills[skills_under_35[0]] = random.randint(35, 50)
            # Find a skill that's already >= 35 but could be higher, or boost another
            other_skills = [name for name in skill_names_list if name not in skills_under_35]
            if other_skills:
                skills[random.choice(other_skills)] = random.randint(35, 50)
        
        new_worker = {
            "name": final_name,
            "folder": assigned_folder,
            "gender": gender,
            "names_list": f"{name_category}_{gender}",
            "skills": skills,
            "traits": list(base_traits),
            "description": f"A {final_name} from the {name_category} region.",
            "cost": random.randint(1000, 1500),  # Minimum price increased to 1000
            "level": 1,
            "energy": 50,
            "health": 100,
            "rebelliousness": random.randint(20, 80),
            "joy": random.randint(20, 80),
            "romance": 0,
            "relationship": 10,
            "comfort_level": 1,
            "comfort_desired": 5,  # Procedural workers always require comfort level 5
            "skill_uses": {skill_name: 0 for skill_name in skill_names.keys()},
            "success_count": 0,
            "procedural": True,
            "unique": False,
            "encounter_only": False,
            "monster": False,
            "nsfw": persistent.nsfw_enabled,  # Set NSFW based on game mode
            "assigned_building": "Unassigned"
        }
        
        ensure_worker_defaults(new_worker)
        if hasattr(store, "_ensure_worker_min_traits"):
            store._ensure_worker_min_traits(new_worker)
        
        return new_worker

    def return_to_recruitment():
        """
        Return to the appropriate recruitment screen after examining worker details.
        """
        # Check if we have stored recruitment data
        event = getattr(store, "current_recruitment_event", None)
        worker = getattr(store, "temp_recruitment_worker", None)
        
        if event and worker:
            # For advanced events with choices, we need to continue the label flow
            # The recruitment_choice_loop will handle displaying the screen again
            # Just return None to indicate the user cancelled/returned
            return None
        else:
            # Fallback - just close and go to tavern
            renpy.jump("tavern_screen")

    def buy_worker(worker):
        if store.money >= worker["cost"]:
            store.money -= worker["cost"]
            # Do not make a copy; use the original worker object.
            worker["energy"] = worker.get("level", 1) * 5
            worker["comfort_level"] = worker.get("comfort_level", 1)
            worker["source"] = "bought"
            worker["assigned_building"] = "Unassigned"  # Bought workers start unassigned (same as recruits)
            workers.append(worker)
            if worker in available_workers:
                available_workers.remove(worker)
            if worker in displayed_workers:
                displayed_workers.remove(worker)
            worker["is_servant"] = True
            
            # Tutorial tracking
            if hasattr(store, 'tutorial_active') and store.tutorial_active:
                store.workers_hired += 1
                store.total_workers += 1
                renpy.log(f"DEBUG: Worker bought! workers_hired: {store.workers_hired}, current_objective: {store.current_objective}")
                # Only trigger when we reach exactly 3 workers for objective 1
                if store.current_objective == 1 and store.workers_hired == 3:
                    renpy.log("DEBUG: Reached 3 workers! Calling check_tutorial_objective...")
                    renpy.log(f"DEBUG: Before calling - tutorial_active: {store.tutorial_active}, current_objective: {store.current_objective}, workers_hired: {store.workers_hired}, objective_1_complete: {store.objective_1_complete}")
                    check_tutorial_objective()
                    renpy.log("DEBUG: After calling check_tutorial_objective")
            
            # Update displayed workers to fill the empty slot
            update_displayed_workers()
            
            renpy.hide_screen("worker_details")

    def update_displayed_workers():
        displayed_workers.clear()
        renpy.log("Updating displayed_workers. Starting population...")
        hired_worker_names = {w["name"] for w in workers}
        renpy.log(f"Hired worker names: {hired_worker_names}")
        renpy.log(f"Available workers before filtering: {[w['name'] for w in available_workers]}")

        # Check if all JSON workers are exhausted
        # Load all JSON workers to check if any remain
        all_json_workers = load_workers(include_unique=True, include_encounter_only=False)
        json_worker_names = {w["name"] for w in all_json_workers if not w.get("procedural", False)}
        available_json_workers = json_worker_names - hired_worker_names
        all_json_exhausted = len(available_json_workers) == 0
        
        renpy.log(f"JSON workers available: {len(available_json_workers)}, All JSON exhausted: {all_json_exhausted}")

        # Add existing available workers (up to 5, respecting NSFW)
        for worker in available_workers:
            if (worker["name"] not in hired_worker_names and 
                (persistent.nsfw_enabled or not worker.get("nsfw", False))):
                if len(displayed_workers) < 5:
                    ensure_worker_defaults(worker)
                    displayed_workers.append(worker)
                    renpy.log(f"Added existing worker '{worker['name']}' to displayed_workers")

        # Ensure MAX_DAILY_SPAWNS is defined and allows spawning
        if not hasattr(store, "MAX_DAILY_SPAWNS"):
            store.MAX_DAILY_SPAWNS = 5  # Default value if not defined
        renpy.log(f"MAX_DAILY_SPAWNS: {store.MAX_DAILY_SPAWNS}")

        # Don't spawn new workers in update_displayed_workers - only display what's available
        # Worker refilling should only happen in load_buy_workers() once per day
        # This prevents instant refills when workers are bought
        renpy.log(f"update_displayed_workers: Not spawning new workers, only displaying available workers (available: {len(available_workers)}, displayed: {len(displayed_workers)})")

        renpy.log(f"Final displayed_workers: {[w['name'] for w in displayed_workers]}")
        renpy.log(f"Final available_workers after update: {[w['name'] for w in available_workers]}")
        renpy.log(f"Final daily_spawns: {daily_spawns}")

    def _remove_worker_from_building_by_name(building, worker_name):
        """Remove all instances of a worker by name from a building assignment list."""
        if not building or not worker_name:
            return
        assigned = building.get("assigned_servants", []) or []
        if not assigned:
            return
        filtered = []
        for w in assigned:
            if isinstance(w, dict):
                wname = w.get("name")
            else:
                wname = str(w) if w is not None else None
            if wname != worker_name:
                filtered.append(w)
        building["assigned_servants"] = filtered

    def add_worker_to_building(worker, building_name):
        """Assign worker to a building, ensuring no duplicates by name."""
        if not building_name or building_name not in available_buildings:
            return
        if not hasattr(worker, "get"):
            renpy.log("add_worker_to_building: invalid worker object, missing get()")
            return
        building = available_buildings[building_name]
        if "assigned_servants" not in building or not isinstance(building["assigned_servants"], list):
            building["assigned_servants"] = []
        worker_name = worker.get("name")
        if not worker_name:
            renpy.log("add_worker_to_building: worker name missing, skipping assignment")
            return
        # Always operate on the canonical worker object from store.workers if available.
        canonical_worker = None
        for w in store.workers:
            if isinstance(w, dict) and w.get("name") == worker_name:
                canonical_worker = w
                break
        if canonical_worker is None:
            canonical_worker = worker
        # Remove any stale duplicates by name before adding
        _remove_worker_from_building_by_name(building, worker_name)
        building["assigned_servants"].append(canonical_worker)
        # CRITICAL: Set the assigned_building on the worker
        canonical_worker["assigned_building"] = building_name
        # CRITICAL: Only initialize servant_jobs if it doesn't exist, don't replace it
        # This prevents clearing all jobs when adding a worker
        if "servant_jobs" not in building:
            building["servant_jobs"] = {}
        if "event_limit" not in building:
            building["event_limit"] = 0

        # Ensure the worker has a job entry (default unassigned).
        try:
            if worker_name not in building.get("servant_jobs", {}):
                building["servant_jobs"][worker_name] = "unassigned"
        except Exception as e:
            renpy.log("add_worker_to_building: ensure servant_jobs error: " + str(e))

    def set_worker_job(worker, building_name, job_id):
        """Set worker's job in the building. When setting to Rest, store current job as previous_job for auto-restore."""
        if not worker or not building_name or building_name not in available_buildings:
            return
        building = available_buildings[building_name]
        if "servant_jobs" not in building:
            building["servant_jobs"] = {}
        worker_name = worker.get("name") if hasattr(worker, "get") else None
        if not worker_name:
            return
        canonical = next((w for w in store.workers if isinstance(w, dict) and w.get("name") == worker_name), worker)
        current_job = (building.get("servant_jobs") or {}).get(worker_name)
        job_id_str = str(job_id).strip().lower() if job_id else ""
        if job_id_str == "rest" and current_job and str(current_job).strip().lower() not in ("rest", "", "unassigned"):
            canonical["previous_job"] = current_job
            renpy.log(f"set_worker_job: {worker_name} -> Rest (stored previous_job={current_job})")
        building["servant_jobs"][worker_name] = job_id if job_id is not None else "unassigned"

    def clear_worker_autorest_state(worker):
        """Clear previous_job when player manually changes job (so auto-restore doesn't override)."""
        if not worker or not hasattr(worker, "get"):
            return
        canonical = next((w for w in store.workers if isinstance(w, dict) and w.get("name") == worker.get("name")), worker)
        if "previous_job" in canonical:
            del canonical["previous_job"]

    def _normalize_building_key_for_match(key):
        """Normalize building key for matching (Building 1 <-> Building_1)."""
        if not key:
            return ""
        s = str(key).strip()
        if "_" in s:
            parts = s.split("_")
            if len(parts) >= 2 and parts[0].lower() == "building":
                return f"Building {parts[1]}"
        return s

    def _alternate_building_key(key):
        """Return the alternate format (Building 1 <-> Building_1) for lookup."""
        if not key:
            return None
        s = str(key).strip()
        if "_" in s:
            parts = s.split("_")
            if len(parts) >= 2 and parts[0].lower() == "building":
                return f"Building {parts[1]}"
        elif s.lower().startswith("building ") and " " in s:
            num = s.split(" ", 1)[1].strip()
            if num:
                return f"Building_{num}"
        return None

    def _resolve_building_key(building_name):
        """Return the key that exists in available_buildings (trying alternate if needed)."""
        if not building_name:
            return None
        if building_name in available_buildings:
            return building_name
        alt = _alternate_building_key(building_name)
        if alt and alt in available_buildings:
            return alt
        return None

    def sync_assigned_servants_for_building(building_name):
        """Rebuild assigned_servants for a single building from servant_jobs and store.workers.
        Resolves Building 1 / Building_1 and syncs the correct building."""
        try:
            resolved = _resolve_building_key(building_name)
            if not resolved:
                return
            building = available_buildings.get(resolved)
            if not isinstance(building, dict):
                return
            name_to_worker = {w.get("name"): w for w in store.workers if isinstance(w, dict) and w.get("name")}
            rebuilt = []
            seen = set()
            
            # Source 1: Workers in servant_jobs
            for wname in list(building.get("servant_jobs", {}) or {}):
                if not wname or wname in seen:
                    continue
                worker_obj = name_to_worker.get(wname)
                if worker_obj:
                    rebuilt.append(worker_obj)
                    seen.add(wname)
                    if worker_obj.get("assigned_building", "Unassigned") != resolved:
                        worker_obj["assigned_building"] = resolved
            
            # Source 2: Workers with assigned_building matching this building (with key normalization)
            _norm_bname = _normalize_building_key_for_match(resolved)
            for worker in store.workers:
                if not isinstance(worker, dict):
                    continue
                wname = worker.get("name")
                if not wname or wname in seen:
                    continue
                ab = worker.get("assigned_building")
                ab_match = (ab == resolved) or (_norm_bname and _normalize_building_key_for_match(ab) == _norm_bname)
                if ab_match:
                    rebuilt.append(worker)
                    seen.add(wname)
                    if ab != resolved:
                        worker["assigned_building"] = resolved  # Normalize to canonical key
                    # Ensure they have an entry in servant_jobs
                    if "servant_jobs" not in building:
                        building["servant_jobs"] = {}
                    if wname not in building["servant_jobs"]:
                        building["servant_jobs"][wname] = "unassigned"
            
            building["assigned_servants"] = rebuilt
        except Exception as e:
            renpy.log("sync_assigned_servants_for_building error: " + str(e))

    def get_manager_display_servants(building_name, building_data=None):
        """Return workers to display in Manager screen. Uses assigned_servants + resolve to store.workers, then get_building_servants as fallback. Resolves Building 1 / Building_1."""
        try:
            resolved = _resolve_building_key(building_name)
            bd = building_data if (building_data and isinstance(building_data, dict)) else (available_buildings.get(resolved or building_name, {}))
            name_to_w = {w.get("name"): w for w in (store.workers or []) if isinstance(w, dict) and w.get("name")}
            raw = bd.get("assigned_servants") or []
            result = []
            seen = set()
            for sw in raw:
                if not isinstance(sw, dict) or not sw.get("name"):
                    continue
                wname = sw.get("name")
                if wname in seen:
                    continue
                canon = name_to_w.get(wname, sw)
                result.append(canon)
                seen.add(wname)
            if result:
                return result
            return get_building_servants(building_name) or []
        except Exception as e:
            renpy.log("get_manager_display_servants error: " + str(e))
            return get_building_servants(building_name) or []

    def get_building_servants(building_name):
        """Return a deduped list of canonical workers for a building.
        Uses both servant_jobs AND worker assigned_building as sources for robustness.
        Resolves Building 1 <-> Building_1 and merges servant_jobs from alternate key."""
        try:
            resolved = _resolve_building_key(building_name)
            if not resolved:
                return []
            building = available_buildings.get(resolved, {})
            if not isinstance(building, dict):
                return []
            name_to_worker = {w.get("name"): w for w in store.workers if isinstance(w, dict) and w.get("name")}
            servants = []
            seen = set()
            # Merge servant_jobs from alternate key (Building 1 <-> Building_1) when both exist
            jobs = dict(building.get("servant_jobs", {}) or {})
            alt_key = _alternate_building_key(building_name) if building_name != resolved else _alternate_building_key(resolved)
            if alt_key and alt_key in available_buildings and alt_key != resolved:
                alt_b = available_buildings.get(alt_key, {})
                if isinstance(alt_b, dict):
                    for wname, jid in (alt_b.get("servant_jobs") or {}).items():
                        if wname and wname not in jobs and jid and (not isinstance(jid, str) or jid.strip()):
                            jobs[wname] = jid
                            building.setdefault("servant_jobs", {})[wname] = jid
            # Source 1: servant_jobs dictionary (primary source)
            for wname, job_id in jobs.items():
                if not wname or wname in seen:
                    continue
                # Only skip truly empty placeholders (None or empty string), NOT "unassigned"
                # Workers with job_id="unassigned" ARE assigned to the building, just without a role
                if job_id is None or (isinstance(job_id, str) and job_id.strip() == ""):
                    continue
                worker_obj = name_to_worker.get(wname)
                if worker_obj:
                    servants.append(worker_obj)
                    seen.add(wname)
            
            # Source 2: workers with assigned_building matching this building (fallback, with key normalization)
            _norm_bname = _normalize_building_key_for_match(building_name)
            for worker in store.workers:
                if not isinstance(worker, dict):
                    continue
                wname = worker.get("name")
                if not wname or wname in seen:
                    continue
                ab = worker.get("assigned_building")
                ab_match = (ab == building_name) or (_norm_bname and _normalize_building_key_for_match(ab) == _norm_bname)
                if ab_match:
                    servants.append(worker)
                    seen.add(wname)
                    if wname not in jobs:
                        building.setdefault("servant_jobs", {})[wname] = "unassigned"
            
            return servants
        except Exception as e:
            renpy.log("get_building_servants error: " + str(e))
            return []

    def _consolidate_duplicate_building_keys():
        """Merge Building 1 / Building_1 duplicates. Keep canonical key from owned_buildings, merge the other."""
        try:
            owned = getattr(store, "owned_buildings", []) or []
            to_merge = []
            for bname in list(available_buildings.keys()):
                alt = _alternate_building_key(bname)
                if not alt or alt == bname or alt not in available_buildings:
                    continue
                canonical = bname if bname in owned else (alt if alt in owned else bname)
                other = alt if canonical == bname else bname
                if canonical not in available_buildings or other not in available_buildings:
                    continue
                to_merge.append((canonical, other))
            for canonical, other in to_merge:
                cb, ob = available_buildings[canonical], available_buildings[other]
                if not isinstance(cb, dict) or not isinstance(ob, dict):
                    continue
                for wname, jid in (ob.get("servant_jobs") or {}).items():
                    if wname and (wname not in cb.get("servant_jobs", {})):
                        cb.setdefault("servant_jobs", {})[wname] = jid
                for w in ob.get("assigned_servants") or []:
                    if isinstance(w, dict) and w.get("name"):
                        cb_list = cb.get("assigned_servants") or []
                        if not any(x.get("name") == w.get("name") for x in cb_list if isinstance(x, dict)):
                            cb.setdefault("assigned_servants", []).append(w)
                for worker in store.workers:
                    if isinstance(worker, dict) and worker.get("assigned_building") == other:
                        worker["assigned_building"] = canonical
                if other in owned:
                    owned.remove(other)
                del available_buildings[other]
                renpy.log(f"_consolidate_duplicate_building_keys: merged {other} into {canonical}")
        except Exception as e:
            renpy.log(f"_consolidate_duplicate_building_keys error: {e}")

    def validate_and_sync_buildings(include_worker_refs=True):
        """Ensure all buildings in owned_buildings exist in available_buildings.
        Also checks workers for building references and creates missing buildings.
        Consolidates Building 1 / Building_1 duplicates into one canonical key."""
        import re
        try:
            renpy.log("validate_and_sync_buildings: STARTING")
            _consolidate_duplicate_building_keys()
            # Collect all building names that should exist
            buildings_to_check = set()
            
            # 1. Check owned_buildings
            if hasattr(store, 'owned_buildings') and store.owned_buildings:
                renpy.log(f"validate_and_sync_buildings: owned_buildings = {store.owned_buildings}")
                for building_name in store.owned_buildings:
                    buildings_to_check.add(building_name)
            else:
                renpy.log("validate_and_sync_buildings: owned_buildings is empty or doesn't exist")
            
            # 2. Optionally include worker assigned_building references
            if include_worker_refs:
                if hasattr(store, 'workers') and store.workers:
                    renpy.log(f"validate_and_sync_buildings: checking {len(store.workers)} workers")
                    for worker in store.workers:
                        if hasattr(worker, "get"):
                            assigned_building = worker.get("assigned_building", "Unassigned")
                            worker_name = worker.get("name", "Unknown")
                            renpy.log(f"validate_and_sync_buildings: worker {worker_name} has assigned_building = '{assigned_building}'")
                            if assigned_building != "Unassigned":
                                buildings_to_check.add(assigned_building)
                                renpy.log(f"validate_and_sync_buildings: worker {worker_name} assigned to {assigned_building} - added to check list")
                else:
                    renpy.log("validate_and_sync_buildings: workers is empty or doesn't exist")
            
            renpy.log(f"validate_and_sync_buildings: buildings_to_check = {buildings_to_check}")
            renpy.log(f"validate_and_sync_buildings: available_buildings keys = {list(available_buildings.keys())}")
            
            # 3. Create missing buildings (skip if alternate key exists - normalize workers instead)
            created_count = 0
            for building_name in list(buildings_to_check):
                if building_name in available_buildings:
                    continue
                alt = _alternate_building_key(building_name)
                if alt and alt in available_buildings:
                    for worker in store.workers:
                        if isinstance(worker, dict) and worker.get("assigned_building") == building_name:
                            worker["assigned_building"] = alt
                    renpy.log(f"validate_and_sync_buildings: Normalized {building_name} -> {alt} (alternate exists)")
                    continue
                renpy.log(f"validate_and_sync_buildings: WARNING - {building_name} referenced but not in available_buildings, recreating...")
                # Recreate the building with default values
                if "Castle" in building_name or building_name.startswith("Governor"):
                    available_buildings[building_name] = {
                        "price": 0,
                        "reputation": 0,
                        "base_level": 5,
                        "type": "governor_castle",
                        "assigned_servants": [],
                        "servant_jobs": {},
                        "max_workers": 10,
                        "costs": 0,
                        "owned": True,
                        "skill": 50,
                        "skill_bonus": 0
                    }
                else:
                    match = re.search(r'Building (\d+)', building_name)
                    if match:
                        building_num = int(match.group(1))
                        default_price = 10000 + (building_num - 1) * 5000
                    else:
                        default_price = 10000
                    available_buildings[building_name] = {
                        "price": default_price,
                        "reputation": 0,
                        "base_level": 1,
                        "assigned_servants": [],
                        "servant_jobs": {},
                        "type": None,
                        "max_workers": {},
                        "costs": 0,
                        "owned": True,
                        "skill": 10,
                        "skill_bonus": 0,
                        "event_limit": 0
                    }
                if not hasattr(store, 'custom_names'):
                    store.custom_names = {}
                if building_name not in store.custom_names:
                    store.custom_names[building_name] = building_name
                if hasattr(store, 'owned_buildings'):
                    if building_name not in store.owned_buildings:
                        store.owned_buildings.append(building_name)
                        renpy.log(f"validate_and_sync_buildings: Added {building_name} to owned_buildings")
                else:
                    store.owned_buildings = [building_name]
                    renpy.log(f"validate_and_sync_buildings: Created owned_buildings list with {building_name}")
                renpy.log(f"validate_and_sync_buildings: Recreated {building_name} in available_buildings")
                created_count += 1
            
            renpy.log(f"validate_and_sync_buildings: COMPLETED - created {created_count} buildings")
            renpy.log(f"validate_and_sync_buildings: Final owned_buildings = {store.owned_buildings if hasattr(store, 'owned_buildings') else 'N/A'}")
            renpy.log(f"validate_and_sync_buildings: Final available_buildings keys = {list(available_buildings.keys())}")
        except Exception as e:
            renpy.log(f"validate_and_sync_buildings error: {str(e)}")
            import traceback
            renpy.log(f"validate_and_sync_buildings traceback: {traceback.format_exc()}")

    def sync_building_assignments_from_workers():
        """Simple rebuild: clear assigned_servants and repopulate from workers' assigned_building.
        Deduplicates by worker name to prevent display issues."""
        try:
            if not hasattr(store, 'workers') or not store.workers:
                renpy.log("sync_building_assignments_from_workers: no workers")
                return

            # Step 1: Clear all assigned_servants
            for building_name, building in available_buildings.items():
                if isinstance(building, dict):
                    building["assigned_servants"] = []

            # Step 2: Add each worker to their building's assigned_servants (dedupe by name)
            seen_per_building = {}  # {building_name: set of worker names}
            for worker in store.workers:
                if not isinstance(worker, dict):
                    continue
                wname = worker.get("name")
                if not wname:
                    continue
                assigned_building = worker.get("assigned_building", "Unassigned")
                if assigned_building == "Unassigned":
                    continue
                resolved_ab = _resolve_building_key(assigned_building)
                if not resolved_ab:
                    worker["assigned_building"] = "Unassigned"
                    continue
                if assigned_building != resolved_ab:
                    worker["assigned_building"] = resolved_ab
                # Deduplicate by name per building
                if resolved_ab not in seen_per_building:
                    seen_per_building[resolved_ab] = set()
                if wname in seen_per_building[resolved_ab]:
                    continue  # Skip duplicate
                seen_per_building[resolved_ab].add(wname)
                building = available_buildings[resolved_ab]
                if isinstance(building, dict):
                    building["assigned_servants"].append(worker)
            
            renpy.log("sync_building_assignments_from_workers: done")
        except Exception as e:
            renpy.log(f"sync_building_assignments_from_workers error: {e}")

    def rebuild_assigned_servants():
        """Rebuild assigned_servants from workers. Alias for sync_building_assignments_from_workers."""
        sync_building_assignments_from_workers()
    
    def ensure_custom_name_for_building(building_name):
        """Ensure custom_names has a default entry for building_name."""
        try:
            if not hasattr(store, "custom_names") or store.custom_names is None:
                store.custom_names = {}
            if building_name not in store.custom_names:
                store.custom_names[building_name] = building_name
        except Exception as e:
            renpy.log(f"ensure_custom_name_for_building error: {str(e)}")

    def normalize_building_assignments():
        """Deduplicate assigned_servants per building by worker name.
        Also clean up workers with invalid building references.
        NOTE: This should be called AFTER validate_and_sync_buildings() to avoid
        incorrectly cleaning up references to buildings that can be recreated."""
        try:
            name_to_worker = {w.get("name"): w for w in store.workers}
            
            # IMPORTANT: First ensure all referenced buildings exist
            # This prevents us from incorrectly cleaning up valid references
            try:
                validate_and_sync_buildings()
            except Exception as e:
                renpy.log(f"normalize_building_assignments: validate_and_sync_buildings error: {str(e)}")
            
            # Now clean up workers with invalid building references
            # (should be none after validate_and_sync_buildings, but just in case)
            for worker in store.workers:
                assigned_building = worker.get("assigned_building", "Unassigned")
                if assigned_building != "Unassigned" and assigned_building not in available_buildings:
                    renpy.log(f"normalize_building_assignments: Worker {worker.get('name')} has invalid building reference '{assigned_building}', cleaning up")
                    worker["assigned_building"] = "Unassigned"
            
            # Deduplicate assigned_servants per building
            for bname in store.owned_buildings:
                building = available_buildings.get(bname)
                if not isinstance(building, dict):
                    continue
                assigned = building.get("assigned_servants", []) or []
                if not assigned:
                    continue
                deduped = []
                seen_names = set()
                for w in assigned:
                    wname = w.get("name")
                    if wname in seen_names:
                        continue
                    deduped.append(name_to_worker.get(wname, w))
                    if wname:
                        seen_names.add(wname)
                building["assigned_servants"] = deduped
        except Exception as e:
            renpy.log("normalize_building_assignments error: " + str(e))

    def unassign_worker(worker):
        """Fully remove worker from their building assignment."""
        remove_worker_from_building(worker)
        building_name = worker.get("assigned_building")
        if building_name and building_name in available_buildings:
            building = available_buildings[building_name]
            _remove_worker_from_building_by_name(building, worker.get("name"))
            if worker["name"] in building["servant_jobs"]:
                del building["servant_jobs"][worker["name"]]
        worker["assigned_building"] = "Unassigned"

    def remove_worker_from_building(worker):
        if worker.get("assigned_building", "Unassigned") != "Unassigned" and worker["assigned_building"] in available_buildings:
            building = available_buildings[worker["assigned_building"]]
            _remove_worker_from_building_by_name(building, worker.get("name"))

    def remove_workers_of_other_gender_for_filter():
        """
        When the player chooses 'Continue playing' after loading a save with both genders
        but filter is Only Male or Only Female: unassign and sell/fire all workers of the
        other gender so they no longer occupy space or cost money.
        """
        mode = getattr(persistent, "worker_gender_filter", "both")
        if mode == "both":
            return
        other_gender = "female" if mode == "male" else "male"
        workers_list = getattr(store, "workers", [])
        to_remove = [w for w in list(workers_list) if hasattr(w, "get") and (w.get("gender") or "").strip().lower() == other_gender]
        for w in to_remove:
            try:
                sell_worker(w)
            except Exception as e:
                renpy.log(f"remove_workers_of_other_gender_for_filter: error selling {w.get('name', '?')}: {e}")
        if to_remove and hasattr(store, "rebuild_assigned_servants") and callable(store.rebuild_assigned_servants):
            try:
                store.rebuild_assigned_servants()
            except Exception as e:
                renpy.log(f"remove_workers_of_other_gender_for_filter: rebuild_assigned_servants error: {e}")

    def adjust_comfort_and_recalculate_relationship(worker, new_comfort):
        """
        Adjust worker's comfort level and recalculate relationship maintaining the current difference.
        Relationship minimum is 10 + comfort, but if it was higher, we maintain that difference.
        Also updates daily_cost to reflect the new comfort level.
        """
        current_comfort = worker.get("comfort_level", 1)
        current_relationship = worker.get("relationship", 10 + current_comfort)
        
        # Calculate the minimum relationship for current comfort
        current_min_relationship = 10 + current_comfort
        
        # Calculate how much above minimum the relationship currently is
        relationship_bonus = max(0, current_relationship - current_min_relationship)
        
        # Set new comfort
        worker["comfort_level"] = new_comfort
        
        # Calculate new minimum relationship
        new_min_relationship = 10 + new_comfort
        
        # Recalculate relationship maintaining the bonus
        new_relationship = max(10, new_min_relationship + relationship_bonus)
        worker["relationship"] = new_relationship
        
        # Update daily_cost based on new comfort level (comfort * 20)
        worker["daily_cost"] = new_comfort * 20
        
        renpy.log(f"Comfort adjusted: {current_comfort} -> {new_comfort}, Relationship: {current_relationship} -> {new_relationship} (bonus: {relationship_bonus}), Daily Cost: ${worker['daily_cost']}")

    def check_worker_health():
        global workers
        to_remove = []
        dead_names = []
        for worker in workers:
            if worker["health"] <= 0:
                unassign_worker(worker)
                to_remove.append(worker)
                dead_names.append(worker["name"])
                # Add the worker to the dead workers list
                add_to_dead_workers(worker["name"])
        for worker in to_remove:
            workers.remove(worker)
        return dead_names  # Return list of names instead of count

    def add_new_building(name, price, reputation=0):
        available_buildings[name] = {
            "price": price,
            "base_level": 1,
            "assigned_servants": [],
            "servant_jobs": {},
            "type": None,
            "reputation": min(reputation, 1000),  # Cap reputation at 1000
            "max_workers": {},
            "costs": 0,
            "owned": True,
            "skill": 10,  # Initialize to base_level * 10
            "skill_bonus": 0,  # Initialize bonus to 0
            "event_limit": 0  # Event limit: 0 = unlimited (with reputation bonus), 1 = limit to 1, 2 = limit to 2
        }
        calculate_reputation(name)  # Set initial value

    def register_new_building(name):
        """Ensure new building is registered in owned_buildings and custom_names."""
        if not hasattr(store, "custom_names") or store.custom_names is None:
            store.custom_names = {}
        store.custom_names.setdefault(name, name)
        if not hasattr(store, "owned_buildings") or store.owned_buildings is None:
            store.owned_buildings = []
        if name not in store.owned_buildings:
            store.owned_buildings.append(name)
        if name in available_buildings and isinstance(available_buildings[name], dict):
            available_buildings[name].setdefault("owned", True)

    def add_academy_building():
        """Create the Academy in available_buildings (not in owned_buildings). Call when player pays tuition."""
        if "Academy" in available_buildings:
            return
        available_buildings["Academy"] = {
            "price": 0,
            "base_level": 1,
            "assigned_servants": [],
            "servant_jobs": {},
            "type": "academy",
            "reputation": 0,
            "max_workers": {},
            "costs": 0,
            "owned": True,
            "skill": 10,
            "skill_bonus": 0,
            "event_limit": 0
        }
        if not hasattr(store, "custom_names") or store.custom_names is None:
            store.custom_names = {}
        store.custom_names.setdefault("Academy", "Academy")
        store.academy_enrolled = True
        renpy.log("Academy added to available_buildings (not in owned_buildings)")

    def add_alchemy_pass():
        """Unlock the Academy laboratory. Call when player pays the alchemist pass."""
        store.alchemy_unlocked = True
        renpy.log("Alchemy pass purchased; laboratory unlocked.")

    def try_academy_haggle():
        """50% chance to succeed. On failure, haggle option is removed until next day. Returns (success, discounted_price)."""
        import random
        if random.random() < 0.5:
            return (True, 7500)  # Success: pay 7500
        store.academy_haggle_available = False
        return (False, 15000)  # Failure: still 15000, haggle locked until next day

    def add_arena_building():
        """Add the Arena to available_buildings when the player unlocks it (first visit)."""
        # Some save/data states already contain "Arena" in available_buildings.
        # In that case we must still mark it as unlocked/owned after winning the trial.
        if "Arena" not in available_buildings:
            available_buildings["Arena"] = {
                "price": 0,
                "base_level": 1,
                "assigned_servants": [],
                "servant_jobs": {},
                "type": "arena",
                "reputation": 0,
                "max_workers": {},
                "costs": 0,
                "owned": True,
                "skill": 10,
                "skill_bonus": 0,
                "event_limit": 0
            }
        else:
            available_buildings["Arena"]["owned"] = True
        if not hasattr(store, "custom_names") or store.custom_names is None:
            store.custom_names = {}
        store.custom_names.setdefault("Arena", "Arena")
        store.arena_unlocked = True
        if "Arena" not in store.owned_buildings:
            store.owned_buildings.append("Arena")
        renpy.log("Arena added to available_buildings and owned_buildings")

    def run_arena_trial(worker):
        """
        Run the arena trial combat roll. Uses worker's Combat skill.
        Returns one of: "critical_success", "success", "mediocre", "failure", "critical_failure".
        """
        import random
        skill_level = calculate_skill_with_traits(worker, "Combat")
        worker_bonus = get_event_success_bonus_worker()
        effective = min(100, skill_level + worker_bonus)
        roll = random.randint(1, 100)
        # Bands: critical_success <= 15% of effective, success <= effective, mediocre <= effective+25, else failure/crit_fail
        crit_threshold = max(1, int(effective * 0.15))
        if roll <= crit_threshold:
            return "critical_success"
        if roll <= effective:
            return "success"
        if roll <= effective + 25:
            return "mediocre"
        return "critical_failure" if roll > effective + 50 else "failure"

    # Special match: many opponent styles and beasts; 2 rounds (attack/defend/feint). Hints suggest what they're doing.
    # Beats: attack beats feint, defend beats attack, feint beats defend.
    SPECIAL_MATCH_STYLES = [
        # Murmillo variants
        {"id": "murmillo", "name": "Murmillo", "round1": "attack", "round2": "defend", "hint1": "They shift weight behind the great shield.", "hint2": "The shield drops a fraction; a strike is coming."},
        {"id": "murmillo2", "name": "Murmillo", "round1": "defend", "round2": "attack", "hint1": "Shield high, they close step by step.", "hint2": "The rim dips—they're about to strike."},
        {"id": "murmillo3", "name": "Murmillo", "round1": "defend", "round2": "feint", "hint1": "They plant behind the shield.", "hint2": "A false step, blade still hidden."},
        # Retiarius variants
        {"id": "retiarius", "name": "Retiarius", "round1": "feint", "round2": "attack", "hint1": "They circle, trident between you.", "hint2": "The net hand twitches; they mean to throw."},
        {"id": "retiarius2", "name": "Retiarius", "round1": "attack", "round2": "feint", "hint1": "The trident drives in low.", "hint2": "They skip back, net trailing—a feint."},
        {"id": "retiarius3", "name": "Retiarius", "round1": "feint", "round2": "defend", "hint1": "A flick of the net, no throw.", "hint2": "Trident raised, they hold the line."},
        # Secutor variants
        {"id": "secutor", "name": "Secutor", "round1": "attack", "round2": "attack", "hint1": "They close the gap with purpose.", "hint2": "Breath comes hard; they're committed to the rush."},
        {"id": "secutor2", "name": "Secutor", "round1": "attack", "round2": "defend", "hint1": "They come in fast.", "hint2": "Helm dips; they brace behind the blade."},
        {"id": "secutor3", "name": "Secutor", "round1": "defend", "round2": "attack", "hint1": "Short guard, waiting.", "hint2": "A sudden step—the rush is on."},
        # Thraex variants
        {"id": "thraex", "name": "Thraex", "round1": "feint", "round2": "feint", "hint1": "They feint with the curved blade.", "hint2": "They sidestep, blade held back."},
        {"id": "thraex2", "name": "Thraex", "round1": "feint", "round2": "attack", "hint1": "A flick of the sica, no commitment.", "hint2": "The hook comes round for real."},
        {"id": "thraex3", "name": "Thraex", "round1": "attack", "round2": "feint", "hint1": "They lunge with the sica.", "hint2": "Recovery step, then a fake cut."},
        # Hoplomachus variants
        {"id": "hoplomachus", "name": "Hoplomachus", "round1": "defend", "round2": "attack", "hint1": "Spear tip held toward you.", "hint2": "They shorten the grip—a thrust is coming."},
        {"id": "hoplomachus2", "name": "Hoplomachus", "round1": "attack", "round2": "defend", "hint1": "The spear drives in.", "hint2": "They pull back, point steady."},
        {"id": "hoplomachus3", "name": "Hoplomachus", "round1": "defend", "round2": "feint", "hint1": "Shield and spear, holding ground.", "hint2": "A short jab, then they circle."},
        # Provocator / other human styles
        {"id": "provocator", "name": "Provocator", "round1": "defend", "round2": "attack", "hint1": "Small shield up, watching.", "hint2": "They drop the shoulder and thrust."},
        {"id": "dimachaerus", "name": "Dimachaerus", "round1": "feint", "round2": "attack", "hint1": "Twin blades weave; one sweep is a feint.", "hint2": "Both blades commit to the cut."},
        {"id": "essedarius", "name": "Essedarius", "round1": "attack", "round2": "feint", "hint1": "They come in from the flank.", "hint2": "A pass-by, blade held—then nothing."},
        # Mythical beasts
        {"id": "crocotta", "name": "Crocotta", "round1": "feint", "round2": "attack", "hint1": "The hyena-beast feints with a snap.", "hint2": "It closes; the bite is real."},
        {"id": "crocotta2", "name": "Crocotta", "round1": "attack", "round2": "defend", "hint1": "It lunges for the leg.", "hint2": "It backs into a crouch."},
        {"id": "minotaur", "name": "Minotaur", "round1": "attack", "round2": "attack", "hint1": "The bull-man lowers his horns.", "hint2": "He charges again."},
        {"id": "minotaur2", "name": "Minotaur", "round1": "defend", "round2": "feint", "hint1": "He turns, flank guarded.", "hint2": "A feint with the axe."},
        {"id": "griffin", "name": "Griffin", "round1": "feint", "round2": "defend", "hint1": "Wings spread—a feint, no strike.", "hint2": "It folds back, talons ready."},
        {"id": "griffin2", "name": "Griffin", "round1": "attack", "round2": "feint", "hint1": "It stoops; the strike is true.", "hint2": "A second pass, but it pulls up."},
        {"id": "sphinx", "name": "Sphinx", "round1": "defend", "round2": "attack", "hint1": "It watches, coiled.", "hint2": "Claws extend in a rush."},
        {"id": "sphinx2", "name": "Sphinx", "round1": "feint", "round2": "feint", "hint1": "A paw raised, then lowered.", "hint2": "Again it feints, then waits."},
        {"id": "basilisk", "name": "Basilisk", "round1": "defend", "round2": "feint", "hint1": "It coils, head drawn back.", "hint2": "A strike that stops short."},
        {"id": "basilisk2", "name": "Basilisk", "round1": "attack", "round2": "defend", "hint1": "The strike comes from above.", "hint2": "It retreats into the coil."},
    ]
    def _special_match_action_beats(our_action, opponent_action):
        if our_action == "attack" and opponent_action == "feint": return True
        if our_action == "defend" and opponent_action == "attack": return True
        if our_action == "feint" and opponent_action == "defend": return True
        return False
    def _special_match_action_loses(our_action, opponent_action):
        if our_action == "attack" and opponent_action == "defend": return True
        if our_action == "defend" and opponent_action == "feint": return True
        if our_action == "feint" and opponent_action == "attack": return True
        return False
    # Option A: player shouts what the OPPONENT is doing; gladiator reacts with the counter.
    def _special_match_counter(opponent_action):
        """The action that beats opponent_action (what gladiator does when we call it right)."""
        if opponent_action == "attack": return "defend"
        if opponent_action == "defend": return "feint"
        if opponent_action == "feint": return "attack"
        return "defend"
    def _special_match_call_correct(call_action, actual_opponent_action):
        """True if we correctly called what the opponent is doing."""
        return call_action == actual_opponent_action
    def _special_match_call_neutral(call_action, actual_opponent_action):
        """True if our wrong call leads to a tie (gladiator's counter ties opponent)."""
        return _special_match_counter(call_action) == actual_opponent_action
    def run_arena_special_match_combat_roll(worker, total_difficulty_modifier):
        """Roll for special match outcome. Returns True if success, False if failure."""
        import random
        skill_level = calculate_skill_with_traits(worker, "Combat")
        worker_bonus = get_event_success_bonus_worker()
        effective = min(100, max(1, skill_level - total_difficulty_modifier + worker_bonus))
        roll = random.randint(1, 100)
        return roll <= effective

    # Alchemy laboratory: 2 rounds (heat_up / maintain / heat_down). Hints describe state only—no literal "raise/lower/steady" so options stay non-obvious.
    ALCHEMY_ROUND_STYLES = [
        {"id": "s1", "round1": "heat_up", "round2": "maintain", "hint1": "The distillate barely moves; the vapour is thin.", "hint2": "The mixture steadies. The drip is even."},
        {"id": "s2", "round1": "maintain", "round2": "heat_down", "hint1": "The brew holds at a gentle simmer.", "hint2": "The colour darkens. A note of scorch at the rim."},
        {"id": "s3", "round1": "heat_down", "round2": "heat_up", "hint1": "The alembic glows. Smoke curls at the neck.", "hint2": "The vapour has faded. The liquid sits still."},
        {"id": "s4", "round1": "heat_up", "round2": "heat_down", "hint1": "The vapour is wispy. The drip has slowed.", "hint2": "The essence has passed into the receiver."},
        {"id": "s5", "round1": "maintain", "round2": "maintain", "hint1": "The balance is delicate. The colour holds.", "hint2": "One more moment. The drip has not changed."},
        {"id": "s6", "round1": "heat_down", "round2": "maintain", "hint1": "The retort glows. The air above shimmers.", "hint2": "The drip from the condenser is steady."},
        {"id": "s7", "round1": "maintain", "round2": "heat_up", "hint1": "The blend is stable. The colour is true.", "hint2": "The vapour weakens. The spirit still sits in the herbs."},
        {"id": "s8", "round1": "heat_up", "round2": "heat_up", "hint1": "The mixture is lukewarm. The vapour barely rises.", "hint2": "Still faint. The condenser is almost dry."},
        {"id": "s9", "round1": "heat_down", "round2": "heat_down", "hint1": "A bitter note rises. The glass is too hot to touch.", "hint2": "The brew still fumes. The rim is dark."},
        {"id": "s10", "round1": "maintain", "round2": "heat_down", "hint1": "The colour is right. The simmer is even.", "hint2": "The last of the essence has left the still."},
        {"id": "s11", "round1": "heat_up", "round2": "maintain", "hint1": "The vapour barely rises. The fire is lazy.", "hint2": "The drip is even. Nothing has shifted."},
        {"id": "s12", "round1": "heat_down", "round2": "heat_up", "hint1": "Smoke curls at the neck. The air tastes sharp.", "hint2": "The mixture has cooled. The vapour is gone."},
        {"id": "s13", "round1": "maintain", "round2": "heat_up", "hint1": "The simmer is perfect. The colour holds.", "hint2": "The vapour thins. The drip has all but stopped."},
        {"id": "s14", "round1": "heat_up", "round2": "heat_down", "hint1": "The liquid barely moves. The condenser is cold.", "hint2": "The run is done. The receiver is full."},
        {"id": "s15", "round1": "heat_down", "round2": "maintain", "hint1": "The glass is scorching. The mixture threatens to boil over.", "hint2": "The temperature holds. The drip is steady."},
        {"id": "s16", "round1": "maintain", "round2": "maintain", "hint1": "The balance is good. The colour has not shifted.", "hint2": "A few heartbeats. The drip has not changed."},
        {"id": "s17", "round1": "heat_up", "round2": "heat_up", "hint1": "The essence still sits in the herbs. The vapour is thin.", "hint2": "The vapour is weak. The fire is too gentle."},
        {"id": "s18", "round1": "heat_down", "round2": "heat_down", "hint1": "The mixture froths at the rim. The air is acrid.", "hint2": "It still fumes. The colour has darkened."},
        {"id": "s19", "round1": "maintain", "round2": "heat_down", "hint1": "The brew behaves. The drip is regular.", "hint2": "The last drop has fallen. The receiver is full."},
        {"id": "s20", "round1": "heat_up", "round2": "maintain", "hint1": "The condenser is dry. The vapour has stalled.", "hint2": "The drip is steady. The colour holds."},
        {"id": "s21", "round1": "heat_down", "round2": "heat_up", "hint1": "A burnt smell. The rim is blackening.", "hint2": "Too cold. The vapour has gone. The liquid sits still."},
        {"id": "s22", "round1": "maintain", "round2": "heat_up", "hint1": "The blend holds. The simmer is even.", "hint2": "The vapour fades. The drip has slowed."},
        {"id": "s23", "round1": "heat_up", "round2": "heat_down", "hint1": "The vapour is thin and slow. The fire is low.", "hint2": "The run is complete. The receiver holds the essence."},
        {"id": "s24", "round1": "heat_down", "round2": "maintain", "hint1": "The liquid boils. The air above wavers.", "hint2": "The temperature holds. The drip is even."},
        {"id": "s25", "round1": "maintain", "round2": "heat_up", "hint1": "All is in order. The colour and drip are steady.", "hint2": "The spirit is not yet drawn. The vapour is faint."},
    ]
    def run_alchemy_craft_roll(worker, craft_modifier):
        """Roll for alchemy outcome. Uses Craft skill. Returns: critical_success, success, mediocre, failure."""
        import random
        skill_level = calculate_skill_with_traits(worker, "Craft")
        worker_bonus = get_event_success_bonus_worker()
        effective = min(100, max(1, skill_level - craft_modifier + worker_bonus))
        roll = random.randint(1, 100)
        crit_threshold = max(1, int(effective * 0.15))
        if roll <= crit_threshold:
            return "critical_success"
        if roll <= effective:
            return "success"
        if roll <= effective + 25:
            return "mediocre"
        return "failure"
    def apply_alchemy_result(tier, outcome, inventory):
        """Apply alchemy result: give potions to manager_inventory by tier and outcome. Modifies inventory in place.
        Quality/premium critical = Troll Blood (+1 Health, +1 Health Regen). Success = trait potions (SFW-only in SFW games)."""
        import random
        if outcome == "failure":
            return []
        given = []
        if tier == "basic":
            # Basic cost 350. Failure = lose all (no refund).
            if outcome == "critical_success":
                for _ in range(30):
                    add_item_to_inventory(inventory, "health_potion")
                    given.append("health_potion")
                for _ in range(30):
                    add_item_to_inventory(inventory, "energy_potion")
                    given.append("energy_potion")
            elif outcome == "success":
                for _ in range(15):
                    add_item_to_inventory(inventory, "health_potion")
                    given.append("health_potion")
                for _ in range(15):
                    add_item_to_inventory(inventory, "energy_potion")
                    given.append("energy_potion")
            else:  # mediocre
                for _ in range(2):
                    add_item_to_inventory(inventory, "health_potion")
                    given.append("health_potion")
                for _ in range(2):
                    add_item_to_inventory(inventory, "energy_potion")
                    given.append("energy_potion")
        elif tier in ("quality", "premium"):
            if outcome == "critical_success":
                add_item_to_inventory(inventory, "potion_troll_blood")
                given.append("potion_troll_blood")
            elif outcome == "success":
                success_potions = [
                    "potion_strong", "potion_tough", "potion_transformed", "potion_magical",
                    "potion_robust", "potion_energetic", "potion_agile",
                    "potion_great_figure", "potion_long_legs", "potion_exotic", "potion_beautiful"
                ]
                if getattr(store.persistent, "nsfw_enabled", False):
                    success_potions.extend([
                        "potion_large_breasts", "potion_small_breasts",
                        "potion_firm_ass", "potion_soft_ass", "potion_large_hips", "potion_deluxe_derriere",
                        "potion_large_penis", "potion_tight", "potion_sensitive",
                        "potion_high_libido", "potion_nympho", "potion_satyr", "potion_cum_addict"
                    ])
                choice = random.choice(success_potions)
                add_item_to_inventory(inventory, choice)
                given.append(choice)
            else:  # mediocre
                standard = ["health_potion", "energy_potion", "stamina_elixir"]
                choice = random.choice(standard)
                add_item_to_inventory(inventory, choice)
                given.append(choice)
        return given

    def academy_try_haggle_and_continue():
        """Try to haggle Academy tuition; on success pay 7500 and show academy menu, on failure notify and return to map."""
        success, price = try_academy_haggle()
        if hasattr(store, "academy_director_intro_done"):
            store.academy_director_intro_done = False
        if success:
            add_academy_building()
            store.money = int(store.money) - int(price)
            renpy.hide_screen("academy_first_dialogue")
            renpy.show_screen("academy_menu")
            renpy.notify("The director agreed! You paid $7,500 for tuition.")
        else:
            renpy.notify("The director refused. You cannot haggle again until tomorrow.")
            renpy.hide_screen("academy_first_dialogue")
            renpy.show_screen("map_screen")

    def get_available_businesses_for_map_button(button_id):
        """
        Determina qué negocios están disponibles para un botón específico del mapa.
        
        button_id puede ser el nombre del botón (ej: "S2Tavern", "PlazaTavern", etc.)
        La función detecta automáticamente el tipo basándose en el nombre:
        - Si contiene "Tavern" -> se trata como "tavern"
        - Si contiene "Redhouse" -> se trata como "redhouse"
        - Si contiene "Bluehouse" -> se trata como "bluehouse"
        - Si contiene "Greenhouse" -> se trata como "greenhouse" (comodín)
        - Si contiene "Shop" -> se trata como "shop" (puede tener todos los tipos, como greenhouse)
        """
        available = []
        
        # Determinar el tipo de botón basándose en el nombre
        button_type = None
        if "Greenhouse" in button_id:
            button_type = "greenhouse"
        elif "Redhouse" in button_id:
            button_type = "redhouse"
        elif "Bluehouse" in button_id:
            button_type = "bluehouse"
        elif "Tavern" in button_id:
            button_type = "tavern"
        elif "Shop" in button_id:
            button_type = "shop"
        
        # Greenhouse y Shop son comodines - pueden tener todos los tipos
        if button_type == "greenhouse" or button_type == "shop":
            for btype in building_types_json.get("building_types", []):
                if btype.get("id") != "governor_castle":  # Castle is only obtained through ending
                    available.append(btype)
            return available
        
        # Para otros botones, verificar allowed_map_locations
        # También verificar si el button_id específico está en la lista (para casos especiales)
        for btype in building_types_json.get("building_types", []):
            if btype.get("id") != "governor_castle":  # Castle is only obtained through ending
                allowed_locations = btype.get("allowed_map_locations", [])
                if button_type and button_type in allowed_locations:
                    available.append(btype)
                elif button_id in allowed_locations:
                    available.append(btype)
        
        return available

    def get_map_building_name_safe(button_id):
        """
        Devuelve el nombre del edificio asociado a un botón del mapa de forma segura.
        Retorna None si no existe.
        """
        if button_id in map_button_buildings:
            building_name = map_button_buildings[button_id]
            if building_name in owned_buildings:
                return building_name
        return None

    def get_map_button_idle_image(button_id):
        """
        Devuelve la ruta de la imagen idle correcta para un botón del mapa.
        Si el edificio está comprado, usa "c.png", si no, usa "a.png".
        """
        if get_map_building_name_safe(button_id) is not None:
            # Edificio comprado, usar imagen "c.png"
            return f"gui/map/{button_id}c.png"
        else:
            # Edificio no comprado, usar imagen "a.png"
            return f"gui/map/{button_id}a.png"

    def get_map_building_display_name(button_id):
        """
        Devuelve el nombre de visualización del edificio asociado a un botón del mapa.
        Retorna None si el edificio no está comprado.
        """
        building_name = get_map_building_name_safe(button_id)
        if building_name is None:
            return None
        
        # Obtener el nombre de visualización
        parts = building_name.split('_')
        default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
        display_name = store.custom_names.get(building_name, default_name)
        return display_name

    def get_building_1_display_name():
        """
        Devuelve el nombre de visualización de Building 1 (el edificio base).
        """
        building_name = "Building 1"
        parts = building_name.split('_')
        default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
        display_name = store.custom_names.get(building_name, default_name)
        return display_name

    def get_shop_tooltip_text(shop_id):
        """
        Devuelve el texto del tooltip para una tienda.
        shop_id puede ser "shop1", "shop2", o "shop3"
        """
        shop_names = {
            "shop1": "Basic Shop",
            "shop2": "Adventurer's Market",
            "shop3": "Elite Emporium"
        }
        
        shop_name = shop_names.get(shop_id, "Shop")
        is_unlocked = store.unlocked_shops.get(shop_id, False)
        
        if is_unlocked:
            return shop_name
        else:
            return f"{shop_name} (Closed)"

    def split_text_for_dialogue(text, max_chars=200, min_chunk_chars=60):
        """
        Divide un texto largo en múltiples mensajes que quepan en el cuadro de diálogo.
        Intenta dividir por frases completas primero, luego por palabras.
        max_chars: caracteres máximos por mensaje (conservador para evitar overflow en UI)
        min_chunk_chars: si el último trozo queda demasiado corto, se fusiona con el anterior
        """
        if not text:
            return [""]
        
        import re
        
        # Primero intentar dividir por frases (puntos, exclamaciones, interrogaciones)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        messages = []
        current_message = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Si la frase sola es muy larga, dividirla por palabras
            if len(sentence) > max_chars:
                words = sentence.split()
                current_sentence = ""
                
                for word in words:
                    if len(current_sentence) + len(word) + 1 > max_chars:
                        if current_sentence:
                            if len(current_message) + len(current_sentence) + 2 <= max_chars:
                                current_message = (current_message + " " + current_sentence).strip()
                            else:
                                if current_message:
                                    messages.append(current_message)
                                current_message = current_sentence
                        else:
                            # Palabra muy larga, añadirla sola
                            if current_message:
                                messages.append(current_message)
                            current_message = word
                        current_sentence = word
                    else:
                        if current_sentence:
                            current_sentence += " " + word
                        else:
                            current_sentence = word
                
                # Añadir la última parte de la frase
                if current_sentence:
                    if len(current_message) + len(current_sentence) + 2 <= max_chars:
                        current_message = (current_message + " " + current_sentence).strip()
                    else:
                        if current_message:
                            messages.append(current_message)
                        current_message = current_sentence
            else:
                # Si añadir esta frase excede el límite, guardar el mensaje actual y empezar uno nuevo
                if len(current_message) + len(sentence) + 2 > max_chars:
                    if current_message:
                        messages.append(current_message)
                    current_message = sentence
                else:
                    if current_message:
                        current_message += " " + sentence
                    else:
                        current_message = sentence
        
        # Añadir el último mensaje si existe
        if current_message:
            messages.append(current_message)

        # Evitar trozos finales ridículamente cortos (ej. "been.")
        # Importante: nunca eliminamos texto. Solo fusionamos si cabe; si no cabe, se deja como último mensaje.
        try:
            if (
                messages
                and len(messages) >= 2
                and isinstance(messages[-1], str)
                and len(messages[-1].strip()) > 0
                and len(messages[-1].strip()) < int(min_chunk_chars)
            ):
                merged = (messages[-2].rstrip() + " " + messages[-1].lstrip()).strip()
                # Solo fusionar si cabe en el límite (si no cabe, mantener el último trozo aunque sea corto)
                if len(merged) <= int(max_chars):
                    messages[-2] = merged
                    messages.pop()
        except Exception:
            pass

        return messages if messages else [text]

    def get_building_bg(building_name):
        """Returns background image path based on building type and level, dynamically reading from building_types_json."""
        building = available_buildings.get(building_name, {})
        btype_id = building.get("type")
        base_level = building.get("base_level", 1)
        
        # Default fallback if no type is assigned or type is invalid
        if not btype_id or btype_id not in [bt["id"] for bt in building_types_json.get("building_types", [])]:
            return "images/buildings/default.png"  # Fallback image
        
        # Use the building type ID directly as the prefix
        type_prefix = btype_id
        
        # Cap level at 3 (assuming 3 quality tiers)
        level = min(max(base_level, 1), 3)
        
        # Construct the image path using the type ID and level
        image_path = f"images/buildings/{type_prefix}_level{level}.png"
        
        # Log for debugging
        renpy.log(f"get_building_bg: Looking for image: {image_path}, building: {building_name}, type: {btype_id}, level: {level}")
        
        # Fallback to default if the specific image doesn't exist
        if not renpy.loadable(image_path):
            renpy.log(f"get_building_bg: Image not found: {image_path}, falling back to default.png")
            return "images/buildings/default.png"
        
        renpy.log(f"get_building_bg: Found image: {image_path}")
        return image_path

    def get_inventory_bg(shop_mode=None):
            """Returns background image path for manager_inventory screen."""
            if shop_mode == "shop1":
                return "images/shops/shop1.png"
            elif shop_mode == "shop2":
                return "images/shops/shop2.png"
            elif shop_mode == "shop3":
                return "images/shops/shop3.png"
            else:
                return "images/shops/storage.png"  # Default for non-shop mode (Storage)

    def get_max_daily_workers(building, profession):
        """
        Calculate max_daily_workers dynamically based on building level.
        This ensures the value is always correct regardless of save/load state.
        
        Args:
            building: Building dict with base_level
            profession: Profession dict from building_types_json
            
        Returns:
            int: Maximum daily workers for this profession at this building level
        """
        # Get the original base value (stored when building_types_json was first loaded)
        original_max = profession.get("original_max_daily_workers", profession.get("max_daily_workers", 1))
        # Calculate based on current building level
        base_level = building.get("base_level", 1)
        return original_max + (base_level - 1)

    def upgrade_building(building_name):
        building = available_buildings[building_name]
        upgrade_cost = building["base_level"] ** 2 * 1000
        
        if store.money < upgrade_cost:
            renpy.notify("Not enough money to upgrade!")
            return

        building["base_level"] += 1
        store.money -= upgrade_cost

        # No need to update max_daily_workers here - it's now calculated dynamically
        # The get_max_daily_workers() function will always return the correct value

        calculate_reputation(building_name)
        building_display_name = custom_names.get(building_name, building_name)
        renpy.notify(f"Upgraded {building_display_name} to level {building['base_level']}!")

    def process_choice(choice, event, acting_worker=None):
        renpy.log(f"process_choice received acting_worker: {acting_worker}, Type: {type(acting_worker)}")
        import random
        effect = choice.get("effect", {})
        selected_worker = None
        outcome_status = "default" # Default status
        # REMOVING THIS LINE: store.current_affected_building = None  # Reset the affected building for this event
        # This was incorrectly resetting the affected building that was set at the beginning of the event

        if "condition" in choice:
            if choice["condition"] == "building_skill":
                # Handle building skill-based events (worker_selection: "none")
                event_building_types = event.get("building_type", [])
                
                # First, check if we already have a selected building from earlier
                if hasattr(store, "current_affected_building") and store.current_affected_building:
                    building_name = store.current_affected_building
                    selected_building = available_buildings.get(building_name)
                    selected_building_name = building_name
                    
                    # Verify the building has the correct type
                    if selected_building and selected_building.get("type") in event_building_types:
                        renpy.log(f"Using previously selected building {selected_building_name}")
                    else:
                        # If the building isn't valid, clear it and select a new one
                        selected_building = None
                        selected_building_name = None
                else:
                    selected_building = None
                    selected_building_name = None
                
                # If we don't have a valid building yet, select one
                if not selected_building:
                    if not event_building_types:
                        # Return dictionary for error
                        return {"message": "No building type specified for this event.", "outcome": "failure"}

                    eligible_buildings = [
                        (b_name, b) for b_name, b in available_buildings.items()
                        if b.get("type") in event_building_types and b.get("owned", False)
                    ]
                    if not eligible_buildings:
                        # Return dictionary for error
                        return {"message": f"No buildings of type {event_building_types[0] if event_building_types else 'any'} available to handle the situation.", "outcome": "failure"}

                    # Select a specific building and store its name
                    selected_building_name, selected_building = random.choice(eligible_buildings)
                    store.current_affected_building = selected_building_name
                
                # Log which building we're using
                renpy.log(f"Event using building: {selected_building_name}")
                
                base_total_skill = selected_building["skill"] + selected_building["skill_bonus"]
                # Apply base success bonus to increase baseline success chance
                building_bonus = get_event_success_bonus_building()
                total_skill = min(100, base_total_skill + building_bonus)

                roll = random.randint(1, 100)
                
                # --- DEBUG LOGGING ---
                renpy.log(f"--- Building Skill Check ---")
                renpy.log(f"Building: {selected_building_name}")
                renpy.log(f"Base Skill: {selected_building['skill']}")
                renpy.log(f"Skill Bonus: {selected_building['skill_bonus']}")
                renpy.log(f"Base Total Skill: {base_total_skill}")
                renpy.log(f"With +{building_bonus}% bonus: {total_skill}")
                renpy.log(f"Roll (1-100): {roll}")
                renpy.log(f"Result: {'Success' if roll <= total_skill else 'Failure'}")
                renpy.log(f"--------------------------")
                # --- END DEBUG LOGGING ---

                acting_worker_name = "Building Team"
                event_worker_name = "Unknown"  # Default if no worker is involved

                # Check for assigned servants, limit to this specific building only
                assigned_servants = selected_building.get("assigned_servants", [])
                if not assigned_servants:
                    # Fallback: Rebuild assigned_servants from store.workers (dedupe by name)
                    for worker in store.workers:
                        if worker.get("assigned_building") == selected_building_name:
                            add_worker_to_building(worker, selected_building_name)
                    assigned_servants = selected_building.get("assigned_servants", [])

                # Get text first
                description = store.current_event_description
                option_text = choice["option"]
                message_success = choice["message_success"]
                message_failure = choice["message_failure"]

                # Check if message_failure has been pre-replaced and revert if necessary
                original_message_failure = "[event_worker] is badly burnt in the fight and will need time to recover. The guild's reputation takes a hit."
                if "Unknown" in message_failure and "[event_worker]" not in message_failure:
                    message_failure = original_message_failure

                # Determine outcome and worker
                if roll <= total_skill:
                    # Success case: building skill event
                    success_effects = effect.get("success", {})
                    success_worker = None
                    if "add_trait" in success_effects:
                        # Resolve worker for trait application (same logic as failure)
                        if assigned_servants:
                            success_worker = random.choice(assigned_servants)
                        else:
                            for w in store.workers:
                                if w.get("assigned_building") == selected_building_name:
                                    success_worker = w
                                    break
                            if success_worker is None and store.workers:
                                success_worker = random.choice(store.workers)
                    applied_values = apply_effects(success_effects, worker=success_worker, building=selected_building)
                    event_worker_name = success_worker["name"] if success_worker else "Unknown"
                    acting_worker_name = "Building Team"
                    outcome_status = "success"
                else:
                    # Failure case: check if we need a worker for trait effects
                    failure_effects = effect.get("failure", {})
                    needs_worker_for_effect = "add_trait" in failure_effects
                    
                    # If we need a worker for failure effects but none are assigned
                    if needs_worker_for_effect and not assigned_servants:
                        renpy.log("Failure effect needs a worker (for trait), but no workers are assigned to this building.")
                        random_worker = None
                        # Try to find any worker assigned to this specific building
                        for worker in store.workers:
                            if worker.get("assigned_building") == selected_building_name:
                                random_worker = worker
                                break
                                
                        # If still no worker found and we really need one, pick randomly from all workers
                        if random_worker is None and store.workers:
                            random_worker = random.choice(store.workers)
                            renpy.log(f"No worker in target building, selected random worker {random_worker['name']} for trait application")
                        
                        # Apply effects with the selected worker
                        applied_values = apply_effects(failure_effects, worker=random_worker, building=selected_building)
                        
                        # Use the worker's name in failure message if one was selected
                        if random_worker:
                            event_worker_name = random_worker["name"]
                            acting_worker_name = "Building Team"
                        else:
                            event_worker_name = "An adventurer"
                            acting_worker_name = "Building Team"
                    else:
                        # Either no worker needed for effects, or we have assigned servants
                        if needs_worker_for_effect and assigned_servants:
                            # Use one of the assigned servants for the trait effect
                            affected_worker = random.choice(assigned_servants)
                            event_worker_name = affected_worker["name"]
                            acting_worker_name = "Building Team"
                            applied_values = apply_effects(failure_effects, worker=affected_worker, building=selected_building)
                        else:
                            # No worker traits involved
                            applied_values = apply_effects(failure_effects, worker=None, building=selected_building)
                            event_worker_name = "An adventurer"
                            acting_worker_name = "Building Team"
                    outcome_status = "failure"

                # Apply replacements to new variables
                replaced_description = description.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                replaced_option_text = option_text.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                replaced_message_success = message_success.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                replaced_message_failure = message_failure.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)

                store.current_event_description = replaced_description

                # Record event occurrence regardless of limited status
                event_id = event.get("id")
                store.event_occurrences[event_id] = store.event_occurrences.get(event_id, 0) + 1
                store.event_last_occurred[event_id] = calculate_total_days() # <<<--- ADDED THIS LINE

                if roll <= total_skill:
                    outcome_message = replaced_message_success
                else:
                    outcome_message = replaced_message_failure
                
                # --->>> NEW: Apply dynamic formatting here <<<---
                outcome_message = format_dynamic_message(outcome_message, applied_values)
                outcome_message = outcome_message + build_changes_summary(applied_values)
                
                # Split long messages into multiple narrator bubbles to avoid overflow
                try:
                    if len(outcome_message) > 180:
                        import re
                        sentences = re.split(r'(?<=[\.!?])\s+', outcome_message)
                        chunks = []
                        current = ""
                        for s in sentences:
                            if len(current) + len(s) + 1 <= 180:
                                current = (current + " " + s).strip()
                            else:
                                if current:
                                    chunks.append(current)
                                current = s
                        if current:
                            chunks.append(current)
                        outcome_message = "\n\n".join(chunks)
                except Exception:
                    pass
                
                # Return dictionary
                return {"message": outcome_message, "outcome": outcome_status}
            else:
                # Worker-based skill check
                skill_name = choice["condition"]
                worker_selection_mode = event.get("worker_selection", "random")

                # --- Original worker selection/skill check logic continues below ---
                building_types = event.get("building_type", [])

                # For worker-based checks too, we should respect the current_affected_building
                if hasattr(store, "current_affected_building") and store.current_affected_building:
                    building_name = store.current_affected_building
                    eligible_workers = [w for w in store.workers if w.get("assigned_building") == building_name]
                    renpy.log(f"Filtering eligible workers to those in building: {building_name}")
                # Fall back to building type filtering if no specific building
                elif building_types:
                    eligible_workers = []
                    for worker in store.workers:
                        building_name = worker.get("assigned_building", "Unassigned")
                        if building_name != "Unassigned" and building_name in available_buildings:
                            building = available_buildings[building_name]
                            if building.get("type") in building_types:
                                eligible_workers.append(worker)
                else:
                    eligible_workers = store.workers

                # If no worker selection is intended for this event, skip skill check.
                if worker_selection_mode == "none":
                    # Apply base effects directly
                    applied_values = apply_effects(effect, worker=acting_worker)
                    # Use the primary message if available, otherwise a generic one
                    outcome_message = choice.get("message", choice.get("message_success", "The action is taken."))
                    # Replace worker placeholders (safe fallbacks for non-worker events)
                    event_worker_name = "your staff"
                    acting_worker_name = "your staff"
                    # Replace worker placeholders
                    outcome_message = outcome_message.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                    # Replace player placeholders
                    outcome_message = outcome_message.replace("[player_title]", str(player_title)).replace("[player_name]", str(player_name))
                    # Apply dynamic message formatting
                    outcome_message = format_dynamic_message(outcome_message, applied_values)
                    outcome_message = outcome_message + build_changes_summary(applied_values)
                    # Ensure description exists before replacement
                    if hasattr(store, 'current_event_description') and store.current_event_description:
                        store.current_event_description = store.current_event_description.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                    # Record event occurrence
                    event_id = event.get("id")
                    if event_id: # Check if event_id exists
                        store.event_occurrences[event_id] = store.event_occurrences.get(event_id, 0) + 1
                        # Record when this event last occurred (for cooldown tracking)
                        store.event_last_occurred[event_id] = calculate_total_days()
                    # Return dictionary (assume default success for 'none' mode with message)
                    return {"message": outcome_message, "outcome": "success" if choice.get("message") or choice.get("message_success") else "default"}

                # Handle random worker selection
                elif worker_selection_mode == "random":
                    # MODIFIED: For "random" mode, prioritize the pre-selected worker passed in as acting_worker
                    # If a valid worker was passed in, use it
                    if acting_worker is not None and hasattr(acting_worker, 'get') and acting_worker.get('name') is not None:
                        selected_worker = acting_worker
                        renpy.log(f"Using pre-selected worker in random mode: {selected_worker['name']}")
                    # Only fallback to random selection if no valid worker was passed
                    elif eligible_workers:
                        selected_worker = renpy.random.choice(eligible_workers)
                        renpy.log(f"No valid worker passed for random mode, selecting new random worker: {selected_worker['name']}")
                    else:
                        renpy.notify(f"No workers assigned to {building_types[0] if building_types else 'any building'} available!")
                        return {"message": f"No worker from {building_types[0] if building_types else 'your roster'} could handle the situation.", "outcome": "failure"}

                # Handle chosen worker (passed via acting_worker)
                elif worker_selection_mode == "choose":
                    # Check if this specific choice actually needs a worker
                    # If the choice doesn't have a condition, we don't need to validate the worker
                    if not choice.get("condition"):
                        # For choices without conditions in a "choose" worker event, skip worker validation
                        renpy.log(f"Worker selection mode is 'choose', but this specific choice has no condition, so no worker needed")
                        # Handle the choice without a worker
                        applied_values = apply_effects(effect, worker=acting_worker)
                        # Get the message and apply replacements
                        message = choice.get("message", "The event concludes.")
                        message = message.replace("[player_title]", str(player_title)).replace("[player_name]", str(player_name))
                        # Apply dynamic message formatting
                        message = format_dynamic_message(message, applied_values)
                        message = message + build_changes_summary(applied_values)
                        # Record event occurrence
                        event_id = event.get("id")
                        if event_id: # Check if event_id exists
                            store.event_occurrences[event_id] = store.event_occurrences.get(event_id, 0) + 1
                            # Record when this event last occurred (for cooldown tracking)
                            store.event_last_occurred[event_id] = calculate_total_days()
                        # Return dictionary (assume success for simple choices)
                        return {"message": message, "outcome": "success"}
                        
                    # Otherwise, for choices with conditions, validate the worker
                    if acting_worker is not None and hasattr(acting_worker, 'get') and acting_worker.get('name') is not None:
                        selected_worker = acting_worker
                    else:
                        # Log error and return a failure message if acting_worker is bad
                        renpy.log(f"ERROR: Invalid worker object passed to process_choice in 'choose' mode: {acting_worker}")
                        return {"message": "Error: Invalid worker selected for this action.", "outcome": "failure"}
                    # No need to update store.current_worker here yet
                
                # If after selection logic, we still don't have a worker (e.g. 'none' mode, or other issue)
                # This shouldn't happen for 'random' or 'choose' if eligible_workers exist
                if selected_worker is None and worker_selection_mode != "none":
                    renpy.log(f"ERROR: selected_worker is None unexpectedly for mode {worker_selection_mode}")
                    return "Error processing event: Could not determine worker."

                # --- CENTRALIZED GLOBAL UPDATE --- 
                # Update global state AFTER selection is confirmed
                if selected_worker:
                    store.current_worker = selected_worker 
                # ----------------------------------

                # Trait requirements at choice level.
                required_trait = choice.get("required_trait")
                required_traits = choice.get("required_traits", []) or []
                excluded_traits = choice.get("excluded_traits", []) or []
                if required_trait:
                    required_traits.append(required_trait)
                if selected_worker and (required_traits or excluded_traits):
                    worker_traits = set(selected_worker.get("traits", []) or [])
                    missing_required = [t for t in required_traits if t not in worker_traits]
                    has_excluded = [t for t in excluded_traits if t in worker_traits]
                    if missing_required:
                        missing_str = ", ".join(missing_required)
                        renpy.log(f"Worker {selected_worker['name']} missing required traits: {missing_str}")
                        return {
                            "message": f"This task requires trait(s): {missing_str}. {selected_worker['name']} does not meet the requirement.",
                            "outcome": "failure",
                        }
                    if has_excluded:
                        excluded_str = ", ".join(has_excluded)
                        renpy.log(f"Worker {selected_worker['name']} has excluded traits: {excluded_str}")
                        return {
                            "message": f"This task cannot be done by workers with trait(s): {excluded_str}.",
                            "outcome": "failure",
                        }

                # Use skill name directly - no conversion needed
                skill_name = choice["condition"]
                
                if selected_worker is None:
                    renpy.log("ERROR: Worker is None but trying to calculate skill. Using default skill level.")
                    outcome_message = "Without an assigned worker, the task could not be completed."
                    apply_effects(effect.get("failure", {}), worker=None)
                    outcome_status = "failure"
                    # Return dictionary for this error case
                    return {"message": outcome_message, "outcome": outcome_status}
                else:
                    skill_level = calculate_skill_with_traits(selected_worker, skill_name)
                    threshold = int(choice.get("threshold", 0))
                    
                    # If threshold is specified and worker meets/exceeds it, give better success chances
                    if threshold > 0 and skill_level >= threshold:
                        skill_above_threshold = skill_level - threshold
                        # If worker is 15+ points above threshold, guaranteed success
                        if skill_above_threshold >= 15:
                            renpy.log(f"Worker {selected_worker['name']} skill {skill_level} is {skill_above_threshold} points above threshold {threshold} - guaranteed success")
                            base_outcome_message = choice.get("message_success") or "The plan proceeds smoothly, yielding modest gains."
                            applied_values = apply_effects(effect.get("success", {}), worker=selected_worker)
                            outcome_status = "success"
                        else:
                            # If worker meets threshold, use a minimum success chance of 90%
                            # Also apply base success bonus
                            min_success_chance = 90
                            worker_bonus = get_event_success_bonus_worker()
                            skill_with_bonus = min(100, skill_level + worker_bonus)
                            effective_success_chance = max(skill_with_bonus, min_success_chance)
                            renpy.log(f"Worker {selected_worker['name']} skill {skill_level} (with +{worker_bonus} bonus = {skill_with_bonus}) meets threshold {threshold} - using {effective_success_chance}% success chance")
                            roll = random.randint(1, 100)
                            if roll <= effective_success_chance:
                                base_outcome_message = choice.get("message_success") or "The plan proceeds smoothly, yielding modest gains."
                                applied_values = apply_effects(effect.get("success", {}), worker=selected_worker)
                                outcome_status = "success"
                            else:
                                base_outcome_message = choice.get("message_failure") or "The attempt falters, and the moment slips away without reward."
                                applied_values = apply_effects(effect.get("failure", {}), worker=selected_worker)
                                outcome_status = "failure"
                    else:
                        # No threshold or doesn't meet it - use normal skill-based roll
                        # Apply base success bonus to increase baseline success chance
                        worker_bonus = get_event_success_bonus_worker()
                        effective_skill = min(100, skill_level + worker_bonus)
                        roll = random.randint(1, 100)
                        renpy.log(f"Worker {selected_worker['name']} skill {skill_level} (with +{worker_bonus}% bonus = {effective_skill}) - roll {roll} vs {effective_skill}%")
                        if roll <= effective_skill:
                            base_outcome_message = choice.get("message_success") or "The plan proceeds smoothly, yielding modest gains."
                            applied_values = apply_effects(effect.get("success", {}), worker=selected_worker)
                            outcome_status = "success"
                        else:
                            base_outcome_message = choice.get("message_failure") or "The attempt falters, and the moment slips away without reward."
                            applied_values = apply_effects(effect.get("failure", {}), worker=selected_worker)
                            outcome_status = "failure"
                    
                    worker_name_to_use = selected_worker["name"]
                    event_worker_name = store.event_worker_name if hasattr(store, "event_worker_name") and store.event_worker_name else worker_name_to_use
                    if not isinstance(base_outcome_message, str):
                        base_outcome_message = str(base_outcome_message or "")
                    outcome_message = base_outcome_message.replace("[event_worker]", event_worker_name).replace("[acting_worker]", worker_name_to_use)
                    outcome_message = outcome_message.replace("[player_title]", str(player_title)).replace("[player_name]", str(player_name))
                    
                    # Apply dynamic message formatting
                    outcome_message = format_dynamic_message(outcome_message, applied_values)
                    outcome_message = outcome_message + build_changes_summary(applied_values)

                event_id = event.get("id")
                if event_id:
                    store.event_occurrences[event_id] = store.event_occurrences.get(event_id, 0) + 1
                    # Record when this event last occurred (for cooldown tracking)
                    store.event_last_occurred[event_id] = calculate_total_days()

                # Return dictionary
                return {"message": outcome_message, "outcome": outcome_status}
        else:
            # Handle choices without conditions (no worker skill check)
            
            # Check if this choice uses success_chance for probability-based outcomes
            success_chance = effect.get("success_chance")
            if success_chance is not None:
                # Probability-based outcome (like fortune telling)
                # Ensure minimum success chance of 60%
                min_success_chance = get_event_success_min_chance()
                effective_success_chance = max(min_success_chance, success_chance)
                roll = random.random()
                if roll <= effective_success_chance:
                    outcome_status = "success"
                    message = choice.get("message_success", "Fortune smiles upon you.")
                    applied_values = apply_effects(effect.get("success", {}), worker=acting_worker)
                else:
                    outcome_status = "failure"
                    message = choice.get("message_failure", "Fortune turns her back.")
                    applied_values = apply_effects(effect.get("failure", {}), worker=acting_worker)
                
                # Replace worker name if present
                if acting_worker and hasattr(acting_worker, 'get'):
                    worker_name = acting_worker.get("name", "Unknown")
                    message = message.replace("[acting_worker]", worker_name)
                
                if effective_success_chance > success_chance:
                    renpy.log(f"Success chance event: roll {roll:.2f} vs {success_chance} (boosted to minimum {min_success_chance*100}% = {effective_success_chance:.2f}) = {outcome_status}")
                else:
                    renpy.log(f"Success chance event: roll {roll:.2f} vs {success_chance} = {outcome_status}")
            else:
                # Simple choice without probability
                applied_values = apply_effects(effect, worker=acting_worker)
                message = choice.get("message", "The event concludes.")
                outcome_status = "success"
            
            message = message.replace("[player_title]", str(player_title)).replace("[player_name]", str(player_name))
            
            # Apply dynamic message formatting
            message = format_dynamic_message(message, applied_values)
            message = message + build_changes_summary(applied_values)
            
            # Record event occurrence
            event_id = event.get("id")
            if event_id:
                store.event_occurrences[event_id] = store.event_occurrences.get(event_id, 0) + 1
                store.event_last_occurred[event_id] = calculate_total_days()
            
            # Return dictionary
            return {"message": message, "outcome": outcome_status}

    def select_weighted_event(events):
        """Select an event from the list based on their weights."""
        if not events:
            return None
        total_weight = sum(event.get("weight", 1) for event in events)
        r = random.random() * total_weight
        cumulative = 0
        for event in events:
            cumulative += event.get("weight", 1)
            if r < cumulative:
                return event
        return events[0]

    def reset_limited_events():
        """Resets occurrence counts for limited events, handling missing IDs."""
        # Load events once
        all_events = load_events_from_folder()
        renpy.log(f"Resetting limited events. Found {len(all_events)} total events.")

        # Ensure event_occurrences exists
        if not hasattr(store, "event_occurrences"):
            store.event_occurrences = {}

        for event in all_events:
            # Check if the event dictionary itself is valid (not None, is a dict)
            if not isinstance(event, dict):
                renpy.log(f"Warning: Encountered non-dictionary item in event list during reset: {event}")
                continue

            # Check if the event is marked as limited
            if event.get("limited", False):
                # Attempt to get the event ID - this is the preferred identifier
                event_id = event.get("id") # <<<--- LOOK HERE: No fallback to event["description"]

                # If ID is missing, log a warning and skip this event
                if event_id is None:
                    # Try to get description for logging purposes, but don't use it as ID
                    desc_for_log = event.get("description", "NO DESCRIPTION")
                    renpy.log(f"Warning: Skipping event in reset_limited_events because it's missing an 'id'. Description snippet: '{desc_for_log[:50]}...' Event data: {event}")
                    continue # Skip to the next event in the loop

                # If ID exists, reset its occurrence count in the store
                store.event_occurrences[event_id] = 0
                # Optional: Log which event was reset
                # renpy.log(f"Reset occurrence count for limited event: {event_id}")

    def check_trait_durations():
        """Handle trait expiration and effects"""
        for worker in store.workers:
            if "trait_durations" not in worker:
                continue
            traits_to_process = list(worker["trait_durations"].keys())
            for trait_name in traits_to_process:
                worker["trait_durations"][trait_name] -= 1
                if worker["trait_durations"][trait_name] <= 0:
                    trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
                    if trait_def and trait_def.get("duration", 0) > 0:
                        handle_trait_expiration(worker, trait_def)
                        if trait_def.get("duration", 0) > 0:
                            if trait_name in worker.get("traits", []):
                                # Use centralized removal to keep trait modifiers in sync
                                remove_trait(worker, trait_name)
                            if trait_name in worker.get("trait_durations", {}):
                                del worker["trait_durations"][trait_name]

    def handle_trait_expiration(worker, trait_def):
        """Handle expiration effects for a trait"""
        effects = trait_def.get("on_expire", {})
        
        # Add new traits
        if "add_trait" in effects:
            trait_data = effects["add_trait"]
            
            def process_trait_entry(trait_entry):
                """Process a single trait entry (string, dict, or list element)."""
                if isinstance(trait_entry, dict):
                    trait_name = trait_entry.get("name")
                    duration = trait_entry.get("duration", 0)
                else:
                    # trait_entry is a string (trait name)
                    trait_name = trait_entry
                    duration = 0
                
                if trait_name and trait_name not in worker.get("traits", []):
                    add_trait_with_duration(worker, trait_name, duration)
                    renpy.notify(f"{worker['name']} gained {trait_name} from expired trait")
            
            # Handle different formats: string, list, or dict
            if isinstance(trait_data, list):
                for trait_entry in trait_data:
                    process_trait_entry(trait_entry)
            elif isinstance(trait_data, dict):
                process_trait_entry(trait_data)
            else:
                # Single string (trait name)
                process_trait_entry(trait_data)

        # Add new workers with proper condition checking
        if "add_worker" in effects:
            worker_data = effects["add_worker"]
            if "worker_name" in worker_data:
                # Check if main worker meets conditions
                conditions = worker_data.get("conditions", {})
                meets_conditions = True
                
                # Skill check
                if "skills" in conditions:
                    for skill_id, min_value in conditions["skills"].items():
                        if calculate_skill_with_traits(worker, skill_name) < min_value:
                            meets_conditions = False
                
                # Trait check
                if "traits" in conditions:
                    for trait in conditions["traits"]:
                        if trait not in worker.get("traits", []):
                            meets_conditions = False
                
                if meets_conditions:
                    add_specific_worker(worker, worker_data)
                    
            elif "random" in worker_data:
                add_random_worker(worker, worker_data)

        # Remove expired trait only if it has duration > 0
        if trait_def.get("duration", 0) > 0:
            trait_name = trait_def["name"]
            if trait_name in worker.get("traits", []):
                # Use centralized removal to keep trait modifiers in sync
                remove_trait(worker, trait_name)
            if trait_name in worker.get("trait_durations", {}):
                del worker["trait_durations"][trait_name]

    def add_specific_worker(main_worker, config):
        """Add a specific worker by name with condition checking"""
        worker_name = config.get("worker_name")
        conditions = config.get("conditions", {})
        
        # Check if main worker meets conditions
        meets_conditions = True
        
        # Skill check
        if "skills" in conditions:
            for skill_id, min_value in conditions["skills"].items():
                if main_worker["skills"].get(str(skill_id), 0) < min_value:
                    meets_conditions = False
        
        # Trait check
        if "traits" in conditions:
            for trait in conditions["traits"]:
                if trait not in main_worker.get("traits", []):
                    meets_conditions = False
        
        if meets_conditions:
            # Existing code to add worker
            all_workers = load_workers(include_unique=True, include_encounter_only=True)
            target_worker = next((w for w in all_workers if w["name"] == worker_name), None)
            if target_worker and target_worker["name"] not in {w["name"] for w in store.workers}:
                to_append = target_worker.copy()
                ensure_worker_defaults(to_append)
                to_append["assigned_building"] = "Unassigned"  # Do not inherit template assignment
                store.workers.append(to_append)
                renpy.notify(f"{target_worker['name']} has joined you!")

    

    def apply_effects(effect_dict, worker=None, building=None):
        # Track actual values applied for dynamic message replacement
        applied_values = {}
        
        # Apply money changes with building level multiplier (FOR RANDOM EVENTS ONLY)
        if "money" in effect_dict:
            money_change = effect_dict["money"]
            
            # Calculate building level multiplier
            target_building = building
            if not target_building and hasattr(store, "current_affected_building") and store.current_affected_building:
                building_name = store.current_affected_building
                target_building = available_buildings.get(building_name)
            
            multipliers = get_building_multipliers(target_building)
            money_multiplier = multipliers["money"]
            
            if money_multiplier > 1.0:
                money_change = int(money_change * money_multiplier)
                building_level = target_building.get("base_level", 1) if target_building else 1
                renpy.log(f"Building level {building_level} money multiplier: {money_multiplier:.1f}x (${effect_dict['money']} -> ${money_change})")
            
            store.money += money_change
            applied_values["actual_money"] = money_change
            applied_values["base_money"] = effect_dict["money"]
            applied_values["money_multiplier"] = money_multiplier
            
            if money_multiplier > 1.0:
                renpy.notify(f"Money changed by ${money_change} (x{money_multiplier:.1f} building bonus)")
            else:
                renpy.notify(f"Money changed by ${money_change}")
            
            # Check objective completion after money change (for Objective 4: 5000 coins)
            if hasattr(store, 'tutorial_active') and store.tutorial_active:
                try:
                    check_objective_completion()
                except Exception as e:
                    renpy.log(f"Error checking objective completion after event money change: {e}")

        # Apply reputation changes with building level multiplier (FOR RANDOM EVENTS ONLY)
        if "reputation" in effect_dict:
            # Prioritize the building passed as parameter
            target_building = building
            
            # If no specific building was passed but we have an affected building, use that
            if not target_building and hasattr(store, "current_affected_building") and store.current_affected_building:
                building_name = store.current_affected_building
                target_building = available_buildings.get(building_name)
            
            if target_building:
                reputation_change = effect_dict["reputation"]
                
                # Calculate building level multiplier for reputation
                multipliers = get_building_multipliers(target_building)
                reputation_multiplier = multipliers["reputation"]
                
                if reputation_multiplier > 1.0:
                    reputation_change = int(reputation_change * reputation_multiplier)
                    building_level = target_building.get("base_level", 1)
                    renpy.log(f"Building level {building_level} reputation multiplier: {reputation_multiplier:.1f}x ({effect_dict['reputation']} -> {reputation_change})")
                
                target_building["reputation"] += reputation_change
                target_building["reputation"] = max(0, min(target_building["reputation"], 1000))  # Cap reputation
                
                applied_values["actual_reputation"] = reputation_change
                applied_values["base_reputation"] = effect_dict["reputation"]
                applied_values["reputation_multiplier"] = reputation_multiplier

                # Extract the building name for the notification
                building_name = next((k for k, v in available_buildings.items() if v == target_building), "Unknown Building")
                # Only show notification if reputation actually changed
                if reputation_change != 0:
                    if reputation_multiplier > 1.0:
                        renpy.notify(f"Reputation changed by {reputation_change} (x{reputation_multiplier:.1f} building bonus) for {building_name}")
                    else:
                        renpy.notify(f"Reputation changed by {reputation_change} for {building_name}")

        # Apply effects to a specific worker
        if worker:
            # Adjust energy
            if "servant_energy" in effect_dict:
                energy_change = effect_dict["servant_energy"]
                worker["energy"] = max(0, worker["energy"] + energy_change)
                applied_values["actual_energy"] = energy_change
                # Only show notification if energy actually changed
                if energy_change != 0:
                    renpy.notify(f"{worker['name']}'s energy changed by {energy_change}")

            # Adjust health (support both "health" and "servant_health" for consistency with recruitment/daily stories)
            health_change = effect_dict.get("servant_health") if "servant_health" in effect_dict else effect_dict.get("health")
            if health_change is not None:
                try:
                    health_change = int(health_change)
                    worker["health"] = max(0, worker["health"] + health_change)
                    applied_values["actual_health"] = health_change
                    # Only show notification if health actually changed
                    if health_change != 0:
                        renpy.notify(f"{worker['name']}'s health changed by {health_change}")
                except (TypeError, ValueError) as e:
                    renpy.log(f"apply_effects health error: {e}")

            # Apply skill modifiers (e.g. Charm +3 from event choice)
            if "skill_modifiers" in effect_dict:
                skill_data = effect_dict["skill_modifiers"]
                if isinstance(skill_data, dict) or (hasattr(skill_data, "items") and callable(getattr(skill_data, "items", None))):
                    for skill_name, delta in skill_data.items():
                        try:
                            delta_int = int(delta)
                            modify_base_skill(worker, skill_name, delta_int)
                            if delta_int != 0:
                                renpy.notify(f"{worker.get('name', 'Worker')}'s {skill_name} changed by {delta_int:+d}")
                        except Exception as e:
                            renpy.log(f"apply_effects skill_modifiers error for {skill_name}: {e}")

        # Add traits with duration (outside if worker: so traits with target random_worker* work when worker=None)
        if "add_trait" in effect_dict:
            trait_data = effect_dict["add_trait"]

            def apply_trait_entry(trait_entry):
                # Robust type checking for Ren'Py JSON-loaded data
                is_dict = isinstance(trait_entry, dict) or (hasattr(trait_entry, 'get') and callable(getattr(trait_entry, 'get', None)))
                is_string = isinstance(trait_entry, str) and not is_dict
                
                if is_dict:
                    try:
                        trait_name = trait_entry.get("name") if hasattr(trait_entry, 'get') else None
                        duration = trait_entry.get("duration", 0) if hasattr(trait_entry, 'get') else 0
                        target = trait_entry.get("target", None) if hasattr(trait_entry, 'get') else None
                        if not trait_name:
                            renpy.log(f"ERROR: add_trait dict missing 'name' key: {trait_entry}")
                            return
                    except (AttributeError, TypeError) as e:
                        renpy.log(f"ERROR: add_trait dict access failed: {e}, type: {type(trait_entry)}, value: {trait_entry}")
                        return
                elif is_string:
                    trait_name = trait_entry
                    duration = 0
                    target = None
                else:
                    renpy.log(f"ERROR: add_trait entry has invalid type: {type(trait_entry)}, value: {trait_entry}")
                    return

                # Handle different target types (worker param = event worker; target overrides)
                target_worker = worker

                if isinstance(target, str) and target not in ("acting_worker", "event_worker", "random_worker", "random_worker_female", "random_worker_male"):
                    # Target by worker name (e.g. "Aspen")
                    for w in store.workers:
                        if w.get("name") == target:
                            target_worker = w
                            renpy.log(f"Resolved trait target by name: {target}")
                            break
                elif target == "random_worker":
                    # Choose a random worker from all available
                    if store.workers:
                        target_worker = random.choice(store.workers)
                        renpy.log(f"Selected random worker {target_worker['name']} for trait application")

                elif target == "random_worker_female":
                    # Choose a random female worker
                    female_workers = [w for w in store.workers if w.get("gender", "") == "female"]
                    if female_workers:
                        target_worker = random.choice(female_workers)
                        renpy.log(f"Selected random female worker {target_worker['name']} for trait application")
                    else:
                        renpy.log("No female workers available for trait application - skipping")
                        target_worker = None

                elif target == "random_worker_male":
                    # Choose a random male worker
                    male_workers = [w for w in store.workers if w.get("gender", "") == "male"]
                    if male_workers:
                        target_worker = random.choice(male_workers)
                        renpy.log(f"Selected random male worker {target_worker['name']} for trait application")
                    else:
                        renpy.log("No male workers available for trait application - skipping")
                        target_worker = None

                if trait_name and target_worker:
                    target_worker = _resolve_worker_for_automation(target_worker)
                    if target_worker:
                        add_trait_with_duration(target_worker, trait_name, duration)
                        renpy.log(f"Applied trait '{trait_name}' to {target_worker.get('name', '?')}")
                elif trait_name:
                    renpy.log(f"Could not add trait '{trait_name}' - no suitable worker found")
                else:
                    renpy.log("Error: 'add_trait' effect is missing 'name' key.")

            # Robust type checking for Ren'Py JSON-loaded data.
            # Check dict-like/string FIRST: Ren'Py dict-like objects are iterable (keys), so they'd wrongly be treated as lists.
            has_get = hasattr(trait_data, 'get') and callable(getattr(trait_data, 'get', None))
            is_dict_like = isinstance(trait_data, dict) or (has_get and not isinstance(trait_data, str))
            is_string = isinstance(trait_data, str)
            is_list = isinstance(trait_data, list)
            
            try:
                if is_dict_like or is_string:
                    apply_trait_entry(trait_data)
                elif is_list:
                    for trait_entry in trait_data:
                        apply_trait_entry(trait_entry)
                else:
                    renpy.log(f"ERROR: add_trait has invalid type: {type(trait_data)}, value: {trait_data}")
            except Exception as e:
                renpy.log(f"ERROR processing add_trait: {e}, type: {type(trait_data)}, value: {trait_data}")
                import traceback
                renpy.log(traceback.format_exc())

        # Handle event flags - add, remove, or modify flags used for event chains and conditions
        if "event_flags" in effect_dict:
            flags_data = effect_dict["event_flags"]
            for flag_name, flag_value in flags_data.items():
                if flag_value is None:
                    # Remove the flag if set to None
                    if flag_name in store.event_flags:
                        del store.event_flags[flag_name]
                        renpy.log(f"Removed event flag: {flag_name}")
                else:
                    # Check if the value is a string that needs to be evaluated
                    if isinstance(flag_value, basestring) and flag_value.startswith("[") and flag_value.endswith("]"):
                        eval_str = flag_value[1:-1]
                        try:
                            evaluated_value = eval(eval_str)
                            store.event_flags[flag_name] = evaluated_value
                            renpy.log(f"Set event flag: {flag_name} = {evaluated_value} (from evaluated string: {eval_str})")
                        except Exception as e:
                            renpy.log(f"ERROR evaluating event flag string '{eval_str}': {e}")
                            store.event_flags[flag_name] = flag_value # Store as literal string on error
                    else:
                        # Add or update the flag with its literal value
                        store.event_flags[flag_name] = flag_value
                        renpy.log(f"Set event flag: {flag_name} = {flag_value}")

        # Handle custom effects
        if "custom" in effect_dict:
            custom_action = effect_dict["custom"]
            if custom_action == "unlock_shop2":
                store.unlocked_shops["shop2"] = True  # Sync to store variable
                renpy.log(f"Unlocked shop2 - store: {store.unlocked_shops}")
                renpy.notify("The Adventurer's Market is now available!")
            elif custom_action == "unlock_shop3":
                store.unlocked_shops["shop3"] = True  # Sync to store variable
                renpy.log(f"Unlocked shop3 - store: {store.unlocked_shops}")
                renpy.notify("The Elite Emporium is now available!")
            elif custom_action == "give_item":
                # Add a specific item to the manager inventory (with optional chance)
                item_id = effect_dict.get("item_id")
                chance = effect_dict.get("chance", 1.0)  # Default 100% if not specified
                try:
                    if item_id:
                        # Roll for chance if specified
                        if renpy.random.random() <= chance:
                            add_item_to_inventory(manager_inventory, item_id)
                            item_name = item_id.replace('_', ' ').title()
                            renpy.notify(f"Received {item_name}!")
                            renpy.log(f"Custom give_item: added {item_id} to inventory (chance: {chance*100}%)")
                        else:
                            renpy.log(f"Custom give_item: {item_id} roll failed (chance: {chance*100}%)")
                    else:
                        renpy.log("Custom give_item: missing item_id")
                except Exception as e:
                    renpy.log(f"ERROR in give_item: {e}")
            elif custom_action == "consume_item":
                # Remove a specific item from the manager inventory
                item_id = effect_dict.get("item_id")
                try:
                    if item_id:
                        # Find and remove the item
                        item_removed = False
                        for i, (inv_item_id, quantity) in enumerate(manager_inventory):
                            if inv_item_id == item_id and quantity > 0:
                                if quantity > 1:
                                    manager_inventory[i] = (inv_item_id, quantity - 1)
                                else:
                                    del manager_inventory[i]
                                item_removed = True
                                break
                        
                        if item_removed:
                            renpy.notify(f"Used {item_id.replace('_',' ').title()}")
                            renpy.log(f"Custom consume_item: removed {item_id} from inventory")
                        else:
                            renpy.log(f"Custom consume_item: {item_id} not found in inventory")
                    else:
                        renpy.log("Custom consume_item: missing item_id")
                except Exception as e:
                    renpy.log(f"ERROR in consume_item: {e}")
            elif custom_action == "grant_loot":
                # Roll random loot and add to inventory
                # First, consume item if specified
                consume_item_id = effect_dict.get("consume_item")
                if consume_item_id:
                    item_consumed = False
                    for i, (inv_item_id, quantity) in enumerate(manager_inventory):
                        if inv_item_id == consume_item_id and quantity > 0:
                            if quantity > 1:
                                manager_inventory[i] = (inv_item_id, quantity - 1)
                            else:
                                del manager_inventory[i]
                            item_consumed = True
                            break
                    if item_consumed:
                        renpy.log(f"Custom grant_loot: consumed {consume_item_id}")
                    else:
                        renpy.log(f"Custom grant_loot: failed to consume {consume_item_id}")
                
                rolls = int(effect_dict.get("loot_rolls", 1))
                try:
                    loot_ids = roll_loot(rolls) or []
                    for lid in loot_ids:
                        add_item_to_inventory(manager_inventory, lid)
                    if loot_ids:
                        renpy.notify(f"Received loot: {', '.join(loot_ids)}")
                    renpy.log(f"Custom grant_loot: rolled {loot_ids}")
                except Exception as e:
                    renpy.log(f"ERROR in grant_loot: {e}")
            elif custom_action == "complete_tutorial":
                # Complete the tutorial and show completion message
                store.objective_16_complete = True
                store.tutorial_active = False
                renpy.log("DEBUG: Tutorial completed via debug item")
                renpy.call_in_new_context("show_tutorial_completion_message")
            elif custom_action == "recruit_worker":
                # Prefer explicit overrides from effect_dict; fallback to current_event
                random_from_effect = bool(effect_dict.get("random_worker", False))
                random_from_event = bool(getattr(store, 'current_event', {}).get("random_worker", False)) if hasattr(store, 'current_event') else False
                use_random = random_from_effect or random_from_event

                if use_random:
                    # Generate or pick a random available worker not yet hired
                    all_workers = load_workers(include_unique=True, include_encounter_only=True)
                    hired_worker_names = {w["name"] for w in store.workers}
                    available_workers_list = [w for w in all_workers if w["name"] not in hired_worker_names]
                    if available_workers_list:
                        target_worker = random.choice(available_workers_list).copy()
                        ensure_worker_defaults(target_worker)
                        target_worker["assigned_building"] = "Unassigned"
                        target_worker["is_servant"] = False
                        store.workers.append(target_worker)
                        renpy.notify(f"{target_worker['name']} has joined you!")
                        store.event_worker_name = target_worker["name"]
                    else:
                        new_worker = spawn_new_worker()
                        ensure_worker_defaults(new_worker)
                        new_worker["assigned_building"] = "Unassigned"
                        new_worker["is_servant"] = False
                        store.workers.append(new_worker)
                        renpy.notify(f"{new_worker['name']} has joined you!")
                        store.event_worker_name = new_worker["name"]
                else:
                    # Fixed worker by name
                    worker_name = effect_dict.get("worker_name") or (getattr(store, 'current_event', {}).get("worker_name") if hasattr(store, 'current_event') else None)
                    if not worker_name:
                        renpy.notify("No worker specified for recruitment.")
                        renpy.log("Custom recruit_worker: missing worker_name and random_worker not set")
                        # Do not early-return None; continue gracefully
                    else:
                        all_workers = load_workers(include_unique=True, include_encounter_only=True)
                        target_worker = next((w for w in all_workers if w["name"] == worker_name), None)
                        if target_worker and target_worker["name"] not in {w["name"] for w in store.workers}:
                            target_worker = target_worker.copy()
                            ensure_worker_defaults(target_worker)
                            target_worker["assigned_building"] = "Unassigned"
                            target_worker["is_servant"] = False
                            store.workers.append(target_worker)
                            renpy.notify(f"{target_worker['name']} has joined you!")
                            store.event_worker_name = target_worker["name"]
                        elif target_worker:
                            renpy.notify(f"{target_worker['name']} is already part of your roster.")
                        else:
                            renpy.notify(f"Worker {worker_name} could not be found to recruit.")

        # Handle trait addition with duration (OUTSIDE worker block - for events without workers)
        if "add_trait" in effect_dict:
            trait_data = effect_dict["add_trait"]
            
            def apply_trait_entry(trait_entry, target_worker_override=None):
                """Helper function to apply a single trait entry. Resolves target when worker is None (e.g. building_skill events)."""
                # Robust type checking for Ren'Py JSON-loaded data
                # Check if it's a dict-like object (has 'get' method)
                is_dict = isinstance(trait_entry, dict) or (hasattr(trait_entry, 'get') and callable(getattr(trait_entry, 'get', None)))
                # Check if it's a string (but not a dict that happens to have get)
                is_string = isinstance(trait_entry, str) and not is_dict
                
                target = None
                if is_dict:
                    try:
                        trait_name = trait_entry.get("name") if hasattr(trait_entry, 'get') else None
                        duration = trait_entry.get("duration", 0) if hasattr(trait_entry, 'get') else 0
                        target = trait_entry.get("target", None) if hasattr(trait_entry, 'get') else None
                        if not trait_name:
                            renpy.log(f"ERROR: add_trait dict missing 'name' key: {trait_entry}")
                            return
                    except (AttributeError, TypeError) as e:
                        renpy.log(f"ERROR: add_trait dict access failed: {e}, type: {type(trait_entry)}, value: {trait_entry}")
                        return
                elif is_string:
                    # trait_entry is a string (trait name)
                    trait_name = trait_entry
                    duration = 0
                else:
                    renpy.log(f"ERROR: add_trait entry has invalid type: {type(trait_entry)}, value: {trait_entry}")
                    return
                
                target_worker = target_worker_override if target_worker_override is not None else worker
                # When worker is None (e.g. building_skill events), resolve target to select a worker
                if target_worker is None and target and store.workers:
                    if target == "random_worker":
                        target_worker = random.choice(store.workers)
                        renpy.log(f"Selected random worker {target_worker['name']} for trait application (no worker context)")
                    elif target == "random_worker_female":
                        female_workers = [w for w in store.workers if w.get("gender", "") == "female"]
                        if female_workers:
                            target_worker = random.choice(female_workers)
                            renpy.log(f"Selected random female worker {target_worker['name']} for trait application (no worker context)")
                        else:
                            renpy.log("No female workers available for trait application - skipping")
                    elif target == "random_worker_male":
                        male_workers = [w for w in store.workers if w.get("gender", "") == "male"]
                        if male_workers:
                            target_worker = random.choice(male_workers)
                            renpy.log(f"Selected random male worker {target_worker['name']} for trait application (no worker context)")
                        else:
                            renpy.log("No male workers available for trait application - skipping")
                    elif isinstance(target, str) and target not in ("acting_worker", "event_worker"):
                        # Target by worker name (e.g. "Aspen")
                        for w in store.workers:
                            if w.get("name") == target:
                                target_worker = w
                                renpy.log(f"Resolved trait target by name: {target}")
                                break
                
                if trait_name and target_worker:
                    # Resolve to canonical worker in store.workers so trait changes persist (fixes copy-from-screen)
                    target_worker = _resolve_worker_for_automation(target_worker)
                    if target_worker:
                        cache = getattr(store, "_trait_def_cache", {}) or {}
                        trait_def = cache.get(trait_name) if isinstance(cache, dict) else None
                        if not trait_def and hasattr(store, "get_trait_definition"):
                            trait_def = store.get_trait_definition(trait_name)
                        if trait_def:
                            if duration == 0:
                                duration = trait_def.get("duration", 0)
                            add_trait_with_duration(target_worker, trait_name, duration)
                            renpy.log(f"Applied trait '{trait_name}' to {target_worker.get('name', '?')}")
                        else:
                            renpy.log(f"Trait '{trait_name}' not found in traits_list")
                elif trait_name:
                    renpy.log(f"Cannot add trait '{trait_name}' - worker is None")
            
            # Robust type checking for Ren'Py JSON-loaded data
            # Check if it's a list (but not a string, which is also iterable)
            is_list = isinstance(trait_data, list) or (hasattr(trait_data, '__iter__') and not isinstance(trait_data, str) and not isinstance(trait_data, dict))
            # Check if it's a dict-like object
            is_dict = isinstance(trait_data, dict) or (hasattr(trait_data, 'get') and callable(getattr(trait_data, 'get', None)) and not isinstance(trait_data, str))
            # Check if it's a string (but not a dict that happens to have get)
            is_string = isinstance(trait_data, str) and not is_dict
            
            try:
                if is_list:
                    # Array of trait names or dicts
                    for trait_entry in trait_data:
                        apply_trait_entry(trait_entry)
                elif is_dict:
                    # Single dict with name/duration
                    apply_trait_entry(trait_data)
                elif is_string:
                    # Single string (trait name)
                    apply_trait_entry(trait_data)
                else:
                    renpy.log(f"ERROR: add_trait has invalid type: {type(trait_data)}, value: {trait_data}")
            except Exception as e:
                renpy.log(f"ERROR processing add_trait: {e}, type: {type(trait_data)}, value: {trait_data}")
                import traceback
                renpy.log(traceback.format_exc())
        
        # Return applied values for dynamic message replacement
        return applied_values

    def format_dynamic_message(message, applied_values):
        """
        Replace dynamic placeholders in event messages with actual values.
        Change values (money, reputation, health, energy) are NOT injected into the narrative
        since they appear in the "Changes" summary; their placeholders are removed instead.
        
        Available placeholders:
        {actual_money}, {actual_reputation}, {actual_health}, {actual_energy} - removed (shown in Changes)
        {base_money}, {base_reputation} - for internal use / special cases
        {money_multiplier}, {reputation_multiplier} - Building multiplier display
        """
        # Change placeholders: remove from narrative (they appear in Changes summary)
        import re
        for ph in ["{actual_money}", "{actual_reputation}", "{actual_health}", "{actual_energy}"]:
            message = message.replace(ph, "")
        # Clean up orphaned parentheses and commas left after removal
        message = re.sub(r"\s*\(\s*\)\s*", " ", message)
        message = re.sub(r"\s*\(\s*,\s*\)\s*", " ", message)
        message = re.sub(r"\s*\(\s*,\s*reputation\s*\)\s*", " ", message, flags=re.IGNORECASE)
        message = re.sub(r"\s*\(\s*reputation\s*\)\s*", " ", message, flags=re.IGNORECASE)
        message = re.sub(r",\s*,", ",", message)
        message = re.sub(r"\s*,\s*\.", ".", message)
        message = re.sub(r"\(\s*,", "(", message)
        message = re.sub(r",\s*\)", ")", message)
        message = re.sub(r"\(\s*\)", "", message)
        message = re.sub(r"\s+\.", ".", message)  # " ." -> "."
        message = re.sub(r"  +", " ", message).strip()

        # Format base_money, base_reputation (less common in narrative)
        if "base_money" in applied_values:
            base_money = applied_values["base_money"]
            if base_money > 0:
                message = message.replace("{base_money}", f"+${base_money}")
            elif base_money < 0:
                message = message.replace("{base_money}", f"-${abs(base_money)}")
            else:
                message = message.replace("{base_money}", "$0")
        else:
            message = message.replace("{base_money}", "$0")
                
        if "base_reputation" in applied_values:
            base_rep = applied_values["base_reputation"]
            if base_rep > 0:
                message = message.replace("{base_reputation}", f"+{base_rep}")
            elif base_rep < 0:
                message = message.replace("{base_reputation}", f"{base_rep}")
            else:
                message = message.replace("{base_reputation}", "0")
        else:
            message = message.replace("{base_reputation}", "0")
        
        # Format multipliers
        if "money_multiplier" in applied_values:
            multiplier = applied_values["money_multiplier"]
            message = message.replace("{money_multiplier}", f"{multiplier:.1f}x")
        else:
            # Replace with default multiplier if not available
            message = message.replace("{money_multiplier}", "1.0x")
            
        if "reputation_multiplier" in applied_values:
            multiplier = applied_values["reputation_multiplier"]
            message = message.replace("{reputation_multiplier}", f"{multiplier:.1f}x")
        else:
            # Replace with default multiplier if not available
            message = message.replace("{reputation_multiplier}", "1.0x")
        
        return message

    def build_changes_summary(applied_values):
        """
        Build a highlighted summary of changes from applied_values for event outcome display.
        Returns a string to append to the outcome message, or empty if nothing to show.
        """
        if not applied_values:
            return ""
        parts = []
        if "actual_money" in applied_values:
            m = applied_values["actual_money"]
            if m != 0:
                parts.append(f"+${m}" if m > 0 else f"-${abs(m)}")
        if "actual_reputation" in applied_values:
            r = applied_values["actual_reputation"]
            if r != 0:
                parts.append(f"+{r} Reputation" if r > 0 else f"{r} Reputation")
        if "actual_health" in applied_values:
            h = applied_values["actual_health"]
            if h != 0:
                parts.append(f"+{h} Health" if h > 0 else f"{h} Health")
        if "actual_energy" in applied_values:
            e = applied_values["actual_energy"]
            if e != 0:
                parts.append(f"+{e} Energy" if e > 0 else f"{e} Energy")
        if not parts:
            return ""
        return "\n\nChanges: " + ", ".join(parts)

    def combat_check():
        for worker in store.workers:
            if int(worker["skills"].get("9", 0)) >= 80:
                return True
        return False
        
    def roll_loot(num_rolls):
        # Get the list of items from our loaded items_json.
        items_list = items_json.get("items", [])
        if not items_list:
            renpy.log("roll_loot: No items found in items_json. Please check your items JSON file.")
            return []
        try:
            requested_rolls = max(0, int(num_rolls))
        except Exception:
            requested_rolls = 0
        if requested_rolls <= 0:
            return []
        
        # Filter out test items and debug items (items with "test" or "debug" in their id)
        filtered_items = []
        for item in items_list:
            item_id = item.get("id", "").lower()
            # Skip test items and debug items
            if "test" not in item_id and "debug" not in item_id:
                filtered_items.append(item)
        
        if not filtered_items:
            renpy.log("roll_loot: No valid items after filtering test items.")
            return []
        
        # Build a list of weights from the filtered items.
        weights = []
        for item in filtered_items:
            try:
                weight = float(item.get("weight", 1))
            except Exception:
                weight = 1
            weights.append(weight)
        
        total_weight = sum(weights)
        if total_weight <= 0:
            renpy.log("roll_loot: Total weight of items is non-positive. Check items JSON configuration.")
            return []
        
        # Difficulty can reduce the number of effective loot rolls.
        loot_mult = get_difficulty_loot_multiplier()
        effective_rolls = 0
        for _ in range(requested_rolls):
            if random.random() <= loot_mult:
                effective_rolls += 1
        if effective_rolls <= 0:
            renpy.log(f"roll_loot: No loot this time (requested_rolls={requested_rolls}, loot_mult={loot_mult}).")
            return []

        # Use random.choices to select items based on their weights.
        chosen_items = random.choices(filtered_items, weights=weights, k=effective_rolls)
        loot_ids = [item["id"] for item in chosen_items]
        
        renpy.log(f"roll_loot: Loot rolled using random.choices: {loot_ids} (requested_rolls={requested_rolls}, effective_rolls={effective_rolls}, loot_mult={loot_mult})")
        return loot_ids

    def is_item_available_in_shop(item, shop_mode):
        """Deterministic per-day availability check for shop listings."""
        if not item.get("shop_available", True):
            return False
        only = item.get("shop_only")
        if only and only != shop_mode:
            return False
        chance = float(item.get("shop_chance", 1.0))
        day = store.current_day if hasattr(store, 'current_day') else 0
        iid = item.get("id", "")
        seed_str = f"{day}:{iid}:{shop_mode}"
        seed_hash = hashlib.md5(seed_str.encode('utf-8')).hexdigest()
        seed_int = int(seed_hash[:8], 16)
        rnd = random.Random(seed_int)
        return rnd.random() <= chance

    def buy_item(item_id):
        global money
        # Look up the item in our loaded items_json.
        item = next((i for i in items_json.get("items", []) if i["id"] == item_id), None)
        if item:
            price = item.get("price", 0)
            if money >= price:
                money -= price
                add_item_to_inventory(manager_inventory, item_id)
                renpy.notify("Bought " + item.get("name", "Unknown") + " for $" + str(price))
                renpy.log("buy_item: Purchased " + item.get("name", "Unknown") + " for $" + str(price))
                # Track tutorial objective 5 - potion purchase
                if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item.get("name", "").lower().find("energy") != -1:
                    store.potion_purchased = True
                    renpy.log("DEBUG: Tutorial - Energy potion purchased")
                    renpy.log(f"DEBUG: Tutorial - Item name: {item.get('name', 'Unknown')}")
                    renpy.log(f"DEBUG: Tutorial - tutorial_active: {store.tutorial_active}, current_objective: {store.current_objective}")
                    renpy.log(f"DEBUG: Tutorial - potion_purchased set to: {store.potion_purchased}")
                    check_objective_completion()
                else:
                    renpy.log(f"DEBUG: Tutorial - Conditions not met: tutorial_active={hasattr(store, 'tutorial_active')}, current_objective={store.current_objective if hasattr(store, 'current_objective') else 'NOT_SET'}, item_name={item.get('name', 'Unknown')}")
            else:
                renpy.notify("Not enough money!")
                renpy.log("buy_item: Not enough money to purchase " + item.get("name", "Unknown"))
        else:
            renpy.log("buy_item: Item with id " + str(item_id) + " not found!")

    def get_best_worker_with_skill(skill_name):
        best_worker = None
        highest_skill = -1
        for worker in store.workers:
            skill_level = calculate_skill_with_traits(worker, skill_name)  # Use calculate_skill_with_traits
            if skill_level > highest_skill:
                best_worker = worker
                highest_skill = skill_level
        return best_worker

    def get_worker_profession(worker):
        """Return the profession dict (with id, skills) for the worker's current job, or None if unassigned or rest."""
        building_name = worker.get("assigned_building", "Unassigned")
        if building_name == "Unassigned":
            return None
        building = available_buildings.get(building_name, {})
        if not building:
            return None
        job_id = (building.get("servant_jobs") or {}).get(worker.get("name", ""), "")
        if not job_id or str(job_id).strip().lower() == "rest":
            return None
        for bt in building_types_json.get("building_types", []):
            for prof in bt.get("professions", []):
                if prof.get("id") == job_id:
                    return prof
        return None

    def get_item_profession_score(item_data, profession_skills):
        """Sum of skill_modifiers for the profession's skills. Higher = better for that profession."""
        if not item_data or not profession_skills:
            return 0
        mods = item_data.get("effect", {}).get("skill_modifiers", {})
        if not mods:
            return 0
        return sum(int(mods.get(s, 0)) for s in profession_skills)

    def _normalize_inventory_entry(entry):
        """Normalize an inventory entry to (item_id, qty, equipped) or return None."""
        if entry is None:
            return None
        # Already list/tuple-like entry.
        if isinstance(entry, (list, tuple)):
            if len(entry) < 1:
                return None
            item_id = entry[0]
            if not item_id:
                return None
            qty = 1
            if len(entry) >= 2:
                try:
                    qty = int(entry[1]) if entry[1] is not None else 1
                except Exception:
                    qty = 1
            equipped = bool(entry[2]) if len(entry) >= 3 else False
            return (item_id, max(0, qty), equipped)
        # Dict entry.
        if isinstance(entry, dict):
            item_id = entry.get("item_id") or entry.get("id")
            if not item_id:
                return None
            try:
                qty = int(entry.get("quantity", 1))
            except Exception:
                qty = 1
            equipped = bool(entry.get("equipped", False))
            return (item_id, max(0, qty), equipped)
        # String entry: support plain item_id and stringified list/tuple/dict.
        if isinstance(entry, str):
            s = entry.strip()
            if not s:
                return None
            if s[:1] in ("[", "(", "{"):
                try:
                    import ast
                    parsed = ast.literal_eval(s)
                    return _normalize_inventory_entry(parsed)
                except Exception:
                    return None
            return (s, 1, False)
        # Generic list-like entry (e.g. RevertableList row).
        if hasattr(entry, "__len__") and hasattr(entry, "__getitem__"):
            try:
                return _normalize_inventory_entry(list(entry))
            except Exception:
                return None
        return None

    def _normalize_inventory_container(inventory):
        """Normalize inventory in-place, returning a plain Python list of tuples."""
        try:
            source = list(inventory) if inventory is not None else []
        except Exception:
            source = []
        normalized = []
        for e in source:
            ne = _normalize_inventory_entry(e)
            if ne is not None:
                normalized.append(ne)
        return normalized

    def _get_normalized_manager_inventory():
        """Return normalized manager inventory and keep store.manager_inventory synchronized."""
        inv = getattr(store, "manager_inventory", None)
        norm = _normalize_inventory_container(inv)
        store.manager_inventory = norm
        return store.manager_inventory

    def _resolve_worker_for_automation(worker):
        """Resolve the canonical worker dict in store.workers, handling copied screen dicts."""
        if not worker:
            return worker
        # Fast path: exact same object is already in store.workers.
        for w in getattr(store, "workers", []) or []:
            if w is worker:
                return w
        name = worker.get("name")
        assigned_building = worker.get("assigned_building")
        # Prefer strict match by name + assigned_building to avoid same-name collisions.
        if name is not None:
            strict = [w for w in (getattr(store, "workers", []) or [])
                      if w.get("name") == name and w.get("assigned_building") == assigned_building]
            if strict:
                return strict[0]
            loose = [w for w in (getattr(store, "workers", []) or []) if w.get("name") == name]
            if loose:
                return loose[0]
        return worker

    def _count_worker_allowed_potions(worker_inv, allowed_ids):
        """Count how many health_potion + energy_potion (or other allowed ids) the worker has. Accepts id or item name."""
        total = 0
        for entry in (worker_inv or []):
            if not isinstance(entry, (list, tuple)) or len(entry) < 1:
                continue
            raw = entry[0] if isinstance(entry[0], str) else str(entry[0])
            raw = raw.strip() if raw else ""
            canonical = raw if raw in allowed_ids else None
            if canonical is None and raw:
                for it in items_json.get("items", []):
                    if it.get("id") in allowed_ids and (it.get("name") == raw or it.get("display_name") == raw):
                        canonical = it.get("id")
                        break
            if canonical is None:
                continue
            qty = 1
            if len(entry) >= 2 and entry[1] is not None:
                try:
                    qty = int(entry[1])
                except Exception:
                    pass
            total += max(0, qty)
        return total

    def run_worker_auto_supply_potions(worker):
        """Take up to auto_supply_potion_count consumables from manager_inventory and add to worker. Called at start of day."""
        if not worker or not worker.get("auto_supply_potions", False):
            return
        worker = _resolve_worker_for_automation(worker)
        if "inventory" not in worker or not isinstance(worker["inventory"], list):
            worker["inventory"] = []
        n = max(1, min(5, int(worker.get("auto_supply_potion_count", 3))))
        # Only Health Potion and Energy Potion (no other consumables).
        ALLOWED_AUTO_SUPPLY_IDS = ("health_potion", "energy_potion")

        def _resolve_potion_id(stored_key):
            """Resolve inventory key to canonical id (health_potion/energy_potion) or None. Handles id or display name."""
            if not stored_key:
                return None
            sk = (stored_key if isinstance(stored_key, str) else str(stored_key)).strip()
            if sk in ALLOWED_AUTO_SUPPLY_IDS:
                return sk
            for it in items_json.get("items", []):
                if it.get("id") in ALLOWED_AUTO_SUPPLY_IDS and (it.get("name") == sk or it.get("display_name") == sk):
                    return it.get("id")
            return None

        worker_inv = worker["inventory"]
        # Limit is per type: up to n health potions AND up to n energy potions (e.g. 3 of each).
        health_count = _count_worker_allowed_potions(worker_inv, ("health_potion",))
        energy_count = _count_worker_allowed_potions(worker_inv, ("energy_potion",))
        if health_count >= n and energy_count >= n:
            renpy.log(f"Auto-supply potions: {worker.get('name', '?')} already has {health_count} health, {energy_count} energy (limit {n} each), skip")
            return

        inv = _get_normalized_manager_inventory()
        if not inv:
            return

        while True:
            inv = _get_normalized_manager_inventory()
            if not inv:
                break
            health_count = _count_worker_allowed_potions(worker_inv, ("health_potion",))
            energy_count = _count_worker_allowed_potions(worker_inv, ("energy_potion",))
            need_health = health_count < n
            need_energy = energy_count < n
            if not need_health and not need_energy:
                break

            # Prefer the type they have fewer of when both need more; else take the one that's below limit.
            prefer_energy = (need_energy and (not need_health or energy_count < health_count))

            found_stored_id = None
            found_canonical_id = None
            allowed_in_manager = []
            for entry in inv:
                if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                    continue
                stored_key = entry[0]
                if isinstance(stored_key, str):
                    stored_key = stored_key.strip()
                qty = int(entry[1]) if entry[1] is not None else 0
                if qty <= 0:
                    continue
                canonical = _resolve_potion_id(stored_key)
                if canonical is None:
                    continue
                allowed_in_manager.append((stored_key, canonical, qty))

            if prefer_energy and need_energy:
                for stored_key, canonical, _ in allowed_in_manager:
                    if canonical == "energy_potion":
                        found_stored_id = stored_key
                        found_canonical_id = canonical
                        break
            if (found_stored_id is None) and need_health:
                for stored_key, canonical, _ in allowed_in_manager:
                    if canonical == "health_potion":
                        found_stored_id = stored_key
                        found_canonical_id = canonical
                        break
            if (found_stored_id is None) and need_energy:
                for stored_key, canonical, _ in allowed_in_manager:
                    if canonical == "energy_potion":
                        found_stored_id = stored_key
                        found_canonical_id = canonical
                        break

            if found_stored_id is None:
                renpy.log(f"Auto-supply potions: no Health/Energy potion in manager inventory for {worker.get('name', '?')}")
                break
            remove_item_from_inventory(inv, found_stored_id, 1)
            add_item_to_inventory(worker_inv, found_canonical_id, 1)
            renpy.log(f"Auto-supply potions: gave 1x {found_canonical_id} to {worker.get('name', '?')} (health {health_count + (1 if found_canonical_id == 'health_potion' else 0)}/{n}, energy {energy_count + (1 if found_canonical_id == 'energy_potion' else 0)}/{n})")

    def run_worker_auto_equip(worker):
        """Equip best items for worker's profession from manager_inventory. No-op if rest/unassigned (does not unequip)."""
        if not worker or not worker.get("auto_equip", False):
            return
        worker = _resolve_worker_for_automation(worker)
        profession = get_worker_profession(worker)
        if not profession:
            return
        skills = profession.get("skills", [])
        if not skills:
            return
        inv = _get_normalized_manager_inventory()
        if not inv:
            return
        if "inventory" not in worker or not isinstance(worker["inventory"], list):
            worker["inventory"] = []
        worker_inv = worker["inventory"]
        # Include accessory slot in auto-equip (previously omitted),
        # so amulets/rings/collars don't accumulate unused.
        equippable_types = ["weapon", "armor", "clothing", "accessory"]
        for item_type in equippable_types:
            inv = _get_normalized_manager_inventory()
            if not inv:
                break
            candidates = []
            for entry in inv:
                if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                    continue
                item_id = entry[0]
                qty = int(entry[1]) if entry[1] is not None else 0
                if qty <= 0:
                    continue
                item_data = next((it for it in items_json.get("items", []) if it.get("id") == item_id), None)
                if not item_data or item_data.get("type") != item_type:
                    continue
                score = get_item_profession_score(item_data, skills)
                if score > 0:
                    candidates.append((item_id, score, item_data))
            if not candidates:
                renpy.log(f"Auto-equip: no candidates for {worker.get('name', '?')} in slot {item_type}")
                continue
            candidates.sort(key=lambda x: -x[1])
            best_id, best_score, _ = candidates[0]
            current_equipped_id = None
            for e in worker_inv:
                if isinstance(e, (list, tuple)) and len(e) >= 3 and e[2]:
                    ed = next((it for it in items_json.get("items", []) if it.get("id") == e[0]), None)
                    if ed and ed.get("type") == item_type:
                        current_equipped_id = e[0]
                        break
            current_score = 0
            if current_equipped_id:
                current_data = next((it for it in items_json.get("items", []) if it.get("id") == current_equipped_id), None)
                current_score = get_item_profession_score(current_data, skills) if current_data else 0
            if best_score <= current_score:
                continue
            remove_item_from_inventory(inv, best_id, 1)
            add_item_to_inventory(worker_inv, best_id, 1)
            toggle_equip_item(worker_inv, best_id, worker)
            renpy.log(f"Auto-equip: {worker.get('name', '?')} equipped {best_id} for {item_type} (score {best_score})")

    def toggle_worker_auto_supply_potions(worker):
        """Toggle auto_supply_potions for the worker (used from Worker details screen)."""
        canonical = _resolve_worker_for_automation(worker)
        new_value = not canonical.get("auto_supply_potions", False)
        canonical["auto_supply_potions"] = new_value
        # Keep current screen dict in sync when UI is rendering a copy.
        try:
            worker["auto_supply_potions"] = new_value
        except Exception:
            pass
        renpy.log(f"AUTO_SUPPLY_TOGGLE: {canonical.get('name', '?')} -> {new_value}")
        # Optional immediate pass so player sees the effect right away.
        if new_value:
            try:
                run_worker_auto_supply_potions(canonical)
            except Exception as e:
                renpy.log("toggle_worker_auto_supply_potions immediate run error: " + str(e))
        renpy.restart_interaction()

    def cycle_worker_auto_supply_count(worker):
        """Cycle auto_supply_potion_count 1->2->3->4->5->1 (used from Worker details screen)."""
        canonical = _resolve_worker_for_automation(worker)
        c = canonical.get("auto_supply_potion_count", 3)
        new_count = (int(c) % 5) + 1
        canonical["auto_supply_potion_count"] = new_count
        try:
            worker["auto_supply_potion_count"] = new_count
        except Exception:
            pass
        renpy.log(f"AUTO_SUPPLY_COUNT: {canonical.get('name', '?')} -> {new_count}")
        renpy.restart_interaction()

    def toggle_worker_auto_equip(worker):
        """Toggle auto_equip for the worker (used from Worker details screen)."""
        canonical = _resolve_worker_for_automation(worker)
        new_value = not canonical.get("auto_equip", False)
        canonical["auto_equip"] = new_value
        try:
            worker["auto_equip"] = new_value
        except Exception:
            pass
        renpy.log(f"AUTO_EQUIP_TOGGLE: {canonical.get('name', '?')} -> {new_value}")
        # Optional immediate pass so player sees equipment update instantly.
        if new_value:
            try:
                run_worker_auto_equip(canonical)
            except Exception as e:
                renpy.log("toggle_worker_auto_equip immediate run error: " + str(e))
        renpy.restart_interaction()

    

    
    
    # Function to check if any worker has an active profession (not "unassigned" or "rest")
    def any_worker_has_active_profession():
        renpy.log(f"DEBUG: Checking active professions for {len(store.workers)} workers")
        for worker in store.workers:
            building_name = worker.get("assigned_building", "Unassigned")
            renpy.log(f"DEBUG: Worker {worker['name']} assigned to building: {building_name}")
            if building_name == "Unassigned":
                continue
            
            building = available_buildings.get(building_name, {})
            servant_job = building.get("servant_jobs", {}).get(worker["name"], "")
            renpy.log(f"DEBUG: Worker {worker['name']} job in {building_name}: '{servant_job}'")
            
            # If the worker has a job that's not "rest" and not empty (unassigned)
            if servant_job and servant_job.lower() != "rest":
                renpy.log(f"DEBUG: Found active profession: {worker['name']} is working as {servant_job}")
                return True
        
        # If we got here, no worker has an active profession
        renpy.log("DEBUG: No workers found with active professions")
        return False
    
    # Function to count active Manager professions that reduce event probability
    def count_active_managers():
        """Count how many workers are assigned as Manager, which reduces event probability"""
        manager_count = 0
        manager_names = []
        # Prefer servant_jobs maps to avoid relying on worker.assigned_building
        seen_names = set()
        for building in available_buildings.values():
            if not isinstance(building, dict):
                continue
            for worker_name, job_id in (building.get("servant_jobs") or {}).items():
                if job_id and job_id.lower() == "manager" and worker_name and worker_name not in seen_names:
                    manager_count += 1
                    manager_names.append(worker_name)
                    seen_names.add(worker_name)
        # Fallback: if no managers found via servant_jobs, use worker.assigned_building
        if manager_count == 0:
            for worker in store.workers:
                building_name = worker.get("assigned_building", "Unassigned")
                if building_name == "Unassigned":
                    continue
                
                building = available_buildings.get(building_name, {})
                servant_job = building.get("servant_jobs", {}).get(worker["name"], "")
                
                # Check if the job is "manager" (case-insensitive)
                if servant_job and servant_job.lower() == "manager":
                    manager_count += 1
                    manager_names.append(worker["name"])
        
        if manager_count > 0:
            renpy.log(f"DEBUG: Found {manager_count} active Manager(s): {', '.join(manager_names)}")
        
        return manager_count
    
    # Function to count Managers in a specific building
    def count_managers_in_building(building_name):
        """Count how many Managers are assigned to a specific building"""
        building = available_buildings.get(building_name, {})
        if not building:
            return 0
        
        manager_count = 0
        manager_names = []
        assigned_servants = building.get("assigned_servants", [])
        servant_jobs = building.get("servant_jobs", {})
        
        for worker in assigned_servants:
            # Extract worker name safely
            if isinstance(worker, dict):
                worker_name = worker.get("name", "")
            else:
                worker_name = str(worker) if worker else ""
            
            # Skip if we don't have a valid worker name
            if not worker_name or not isinstance(worker_name, str):
                continue
                
            job = servant_jobs.get(worker_name, "")
            if job and job.lower() == "manager":
                manager_count += 1
                manager_names.append(worker_name)
        
        if manager_count > 0:
            renpy.log(f"DEBUG: Found {manager_count} Manager(s) in {building_name}: {', '.join(manager_names)}")
        
        return manager_count
    
    # Function to check if a building has workers with active professions
    def building_has_active_professions(building_name):
        """Check if a specific building has workers with active professions"""
        building = available_buildings.get(building_name, {})
        if not building:
            return False
        
        assigned_servants = building.get("assigned_servants", [])
        servant_jobs = building.get("servant_jobs", {})
        
        # If no assigned servants, no active professions
        if not assigned_servants:
            return False
        
        # Check each worker
        for worker in assigned_servants:
            # Extract worker name safely
            if isinstance(worker, dict):
                worker_name = worker.get("name", "")
            else:
                worker_name = str(worker) if worker else ""
            
            # Skip if we don't have a valid worker name
            if not worker_name or not isinstance(worker_name, str):
                continue
                
            # Get job from servant_jobs dict
            job = servant_jobs.get(worker_name, "")
            
            # Check if job is active (not rest, unassigned, or empty)
            if job and isinstance(job, str) and job.lower() not in ["rest", "unassigned", ""]:
                renpy.log(f"DEBUG: building_has_active_professions found active job '{job}' for worker '{worker_name}' in building '{building_name}'")
                return True
        
        renpy.log(f"DEBUG: building_has_active_professions found no active professions in building '{building_name}' (servant_jobs: {servant_jobs})")
        return False

    # Reputation helpers for UI (aligned with dist/building_logic)
    def get_reputation_tier(reputation):
        """Returns the reputation tier name."""
        rep = int(reputation)
        if rep < 50:
            return "Unknown"
        elif rep < 100:
            return "New"
        elif rep < 200:
            return "Recognized"
        elif rep < 300:
            return "Respected"
        elif rep < 400:
            return "Well-Known"
        elif rep < 500:
            return "Popular"
        elif rep < 600:
            return "Famous"
        elif rep < 700:
            return "Highly Regarded"
        elif rep < 800:
            return "Prestigious"
        elif rep < 900:
            return "Elite"
        else:
            return "Master"

    def get_reputation_bonus_stories(reputation, bonus_formula):
        """Calculate bonus stories per profession per day based on reputation and formula, with 50% reduction."""
        if not bonus_formula or bonus_formula == "0":
            return 0
        try:
            bonus = int(eval(bonus_formula, {"__builtins__": None}, {"reputation": int(reputation)}))
            bonus = int(bonus * 0.5)  # Match event_daily_exec reduction
            return bonus
        except Exception:
            return 0

    def sync_worker_folders_from_json():
        """
        Sync all worker folders from JSON data.
        This fixes workers that have incorrect folder values saved in their game state.
        Called automatically on game load.
        """
        try:
            # Load all workers from JSON
            all_json_workers = load_workers(include_unique=True, include_encounter_only=True, for_events=True)
            
            # Create a lookup dict by name
            json_folders = {w.get("name"): w.get("folder") for w in all_json_workers if w.get("name") and w.get("folder")}
            
            updated_count = 0
            
            # Update folders in store.workers
            for worker in store.workers:
                worker_name = worker.get("name")
                if worker_name and worker_name in json_folders:
                    correct_folder = json_folders[worker_name]
                    current_folder = worker.get("folder", "")
                    if current_folder != correct_folder:
                        renpy.log(f"Syncing folder for {worker_name}: '{current_folder}' -> '{correct_folder}'")
                        worker["folder"] = correct_folder
                        updated_count += 1
            
            # Update folders in store.available_workers
            for worker in store.available_workers:
                worker_name = worker.get("name")
                if worker_name and worker_name in json_folders:
                    correct_folder = json_folders[worker_name]
                    current_folder = worker.get("folder", "")
                    if current_folder != correct_folder:
                        renpy.log(f"Syncing folder for available worker {worker_name}: '{current_folder}' -> '{correct_folder}'")
                        worker["folder"] = correct_folder
                        updated_count += 1
            
            if updated_count > 0:
                renpy.log(f"sync_worker_folders_from_json: Updated {updated_count} worker folders")
        except Exception as e:
            import traceback
            renpy.log(f"Error in sync_worker_folders_from_json: {e}")
            renpy.log(traceback.format_exc())

    def after_load_callback():
        import copy as _cp
        import os
        import json
        
        # Sync worker folders from JSON first (fixes Selene and any other mismatched folders)
        sync_worker_folders_from_json()
        # Then ensure defaults
        for worker in store.workers:
            ensure_worker_defaults(worker)
        for worker in store.available_workers:
            ensure_worker_defaults(worker)
        
        # CRITICAL: Restore worker flags from snapshot
        # This ensures interaction progress is preserved after loading
        try:
            renpy.log("AFTER_LOAD_CALLBACK: Starting flags restoration")
            
            # Get the slot that was loaded
            slot_name = getattr(persistent, "_loading_slot", None)
            if not slot_name:
                slot_name = getattr(persistent, "_last_loaded_snapshot_slot", None)
            
            renpy.log(f"AFTER_LOAD_CALLBACK: slot_name = {slot_name}")
            
            if slot_name:
                # Build snapshot path
                save_dir = os.path.join(renpy.config.gamedir, "saves")
                filepath = os.path.join(save_dir, f"snapshot_{slot_name}.json")
                renpy.log(f"AFTER_LOAD_CALLBACK: Looking for snapshot at {filepath}")
                
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            snap = json.load(f)
                        
                        if snap and "workers" in snap:
                            snapshot_workers = snap["workers"]
                            renpy.log(f"AFTER_LOAD_CALLBACK: Found {len(snapshot_workers)} workers in snapshot")
                            
                            # Create a mapping of snapshot workers by name for quick lookup
                            snapshot_by_name = {w.get("name"): w for w in snapshot_workers if w.get("name")}
                            
                            # Restore flags for each current worker
                            flags_restored = 0
                            for worker in store.workers:
                                worker_name = worker.get("name")
                                if worker_name and worker_name in snapshot_by_name:
                                    snapshot_worker = snapshot_by_name[worker_name]
                                    snapshot_flags = snapshot_worker.get("flags", {})
                                    if snapshot_flags:
                                        worker["flags"] = _cp.deepcopy(snapshot_flags)
                                        flags_restored += 1
                                        renpy.log(f"AFTER_LOAD_CALLBACK: Restored flags for {worker_name}: {list(snapshot_flags.keys())}")
                                    elif "flags" not in worker:
                                        worker["flags"] = {}
                                elif "flags" not in worker:
                                    worker["flags"] = {}
                            
                            renpy.log(f"AFTER_LOAD_CALLBACK: Restored flags for {flags_restored} workers")
                        else:
                            renpy.log("AFTER_LOAD_CALLBACK: No workers in snapshot")
                    except Exception as e:
                        renpy.log(f"AFTER_LOAD_CALLBACK: Error reading snapshot: {e}")
                else:
                    renpy.log(f"AFTER_LOAD_CALLBACK: Snapshot file not found: {filepath}")
            else:
                renpy.log("AFTER_LOAD_CALLBACK: No slot_name found")
        except Exception as e:
            renpy.log(f"AFTER_LOAD_CALLBACK: Error restoring flags: {e}")
            import traceback
            renpy.log(traceback.format_exc())
    
    config.after_load_callbacks.append(after_load_callback)

    def get_manager_portrait():
        """Return the manager portrait image path. Uses manager_portrait if set, else lord.png/lady.png from images/manager_portraits/."""
        custom = getattr(store, "manager_portrait", "") or ""
        if custom and renpy.loadable(custom):
            return custom
        title = (getattr(store, "player_title", "") or "").lower()
        if "lady" in title or title == "lady":
            path = "images/manager_portraits/lady.png"
        else:
            path = "images/manager_portraits/lord.png"
        if renpy.loadable(path):
            return path
        return None  # No portrait; screen will show placeholder

    def add_management_skill_point(skill_id):
        """Add +1 to a management skill. Called from confirm_all_management_skill_points or legacy single confirm."""
        skills = getattr(store, "management_skills", None)
        if not isinstance(skills, dict):
            store.management_skills = {"business_acumen": 0, "whore_mastery": 0, "combat_instruction": 0, "servant_training": 0, "gang_leader": 0}
            skills = store.management_skills
        current = skills.get(skill_id, 0)
        skills[skill_id] = current + 1
        store.manager_start_skill_chosen = True

    def add_pending_management_skill(skill_id):
        """Add one pending point to a skill (multiple + clicks accumulate). Only if remaining points allow."""
        keys = ["business_acumen", "whore_mastery", "combat_instruction", "servant_training", "gang_leader"]
        skills = getattr(store, "management_skills", None) or {}
        spent = sum(skills.get(k, 0) for k in keys)
        pending = getattr(store, "manager_pending_skills", None) or {}
        if not isinstance(pending, dict):
            store.manager_pending_skills = {}
            pending = store.manager_pending_skills
        total_pending = sum(pending.values())
        level = getattr(store, "manager_level", 1)
        remaining = level - spent - total_pending
        if remaining > 0:
            pending[skill_id] = pending.get(skill_id, 0) + 1
            store.manager_pending_skills = dict(pending)
        renpy.restart_interaction()

    def confirm_all_management_skill_points():
        """Apply all pending skill points (from multiple + clicks) and clear pending."""
        pending = getattr(store, "manager_pending_skills", None) or {}
        if not isinstance(pending, dict):
            store.manager_pending_skills = {}
            return
        for sid, count in list(pending.items()):
            for _ in range(count):
                add_management_skill_point(sid)
        store.manager_pending_skill_id = None
        store.manager_pending_skills = {}
        check_objective_completion()
        renpy.restart_interaction()

    def manager_has_unspent_skill_points():
        """True if manager has skill points to assign (manager_level minus spent points)."""
        skills = getattr(store, "management_skills", None) or {}
        if not isinstance(skills, dict):
            return False
        keys = ["business_acumen", "whore_mastery", "combat_instruction", "servant_training", "gang_leader"]
        spent = sum(skills.get(k, 0) for k in keys)
        level = getattr(store, "manager_level", 1)
        return level > spent

    

################################################################################
### GAME CONSTANTS
################################################################################

define skill_names = {
    "Sex": "Sex", "Anal": "Anal", "BDSM": "BDSM",
    "Hand": "Handjob", "Oral": "Oral", "Homo": "Homosexual",
    "Special": "Special", "Group": "Group", "Extreme": "Extreme",
    "Striptease": "Striptease", "Combat": "Combat", "Clever": "Clever",
    "Charm": "Charm", "Service": "Service", "Agility": "Agility",
    "Craft": "Craft", "Specialty 4": "Specialty 4", "Specialty 5": "Specialty 5",
    "Specialty 6": "Specialty 6", "Specialty 7": "Specialty 7", "Specialty 8": "Specialty 8",
    "Specialty 9": "Specialty 9", "Specialty 10": "Specialty 10", "Specialty 11": "Specialty 11",
    "Specialty 12": "Specialty 12"
}

# Canonical order of skills for display purposes
define skill_order = [
    "Sex", "Anal", "BDSM", "Hand", "Oral", "Homo",
    "Special", "Group", "Extreme", "Striptease",
    "Combat", "Clever", "Charm", "Service", "Agility", "Craft",
    "Specialty 4", "Specialty 5", "Specialty 6",
    "Specialty 7", "Specialty 8", "Specialty 9",
    "Specialty 10", "Specialty 11", "Specialty 12"
]

# Eliminado: Mapeo de IDs numéricos a nombres de skills - solo se usan nombres

# Define SFW skill IDs
define sfw_skills = [
    "Striptease", # Striptease (era Agility)
    "Combat",     # Combat
    "Clever",     # Clever
    "Charm",      # Charm
    "Service",    # Service
    "Agility",    # Agility (era Specialty 2)
    "Craft"       # Craft (era Specialty 3, antes Magic)
]

define SKILL_MAX = 100

init python:
    def is_skill_visible(skill_name):
        """
        Check if a skill should be visible in the UI.
        Hides skills that start with "Specialty" (for future extensibility).
        Also respects NSFW/SFW mode.
        """
        # Hide skills that start with "Specialty"
        if skill_name.startswith("Specialty"):
            return False
        
        # Respect NSFW/SFW mode
        if not persistent.nsfw_enabled:
            return skill_name in sfw_skills
        
        return True
    
    def get_visible_skills(worker):
        """
        Get a filtered list of visible skills for a worker.
        Returns a list of (skill_name, level) tuples in canonical order.
        """
        base_skills = worker.get("skills", {})
        # Return skills in canonical order defined by skill_order
        result = []
        for skill_name in skill_order:
            if skill_name in base_skills and is_skill_visible(skill_name):
                result.append((skill_name, base_skills[skill_name]))
        # Add any skills not in skill_order (shouldn't happen, but safe fallback)
        for skill_name, lvl in base_skills.items():
            if skill_name not in skill_order and is_skill_visible(skill_name):
                result.append((skill_name, lvl))
        return result

################################################################################
### GLOBAL VARIABLES
################################################################################
default player_title = ""
default player_name = ""
default money = 6000
# Manager character sheet: Management Skills (all start at 0; +1 to one at game start)
default management_skills = {
    "business_acumen": 0,
    "whore_mastery": 0,
    "combat_instruction": 0,
    "servant_training": 0,
    "gang_leader": 0
}
default manager_portrait = ""  # Custom path; empty = use lord.png/lady.png from images/manager_portraits/
default manager_start_skill_chosen = False  # True after player picks +1 management skill at game start
default manager_level = 1  # Manager level; level 1 gives 1 point to assign at game start
default manager_pending_skill_id = None  # Skill selected with + but not yet confirmed (for discard warning)
default current_bg = tavern_bg
default manager_inventory = []
default is_new_game = True
default game_initialized = False
default event_occurrences = {}  # Tracks event occurrences
default can_recruit_today = True
default owned_buildings = ["Building 1"]
default max_building = 50
default map_button_buildings = {}  # Maps map button IDs to building names
default available_buildings = {
    "Building 1": {
        "price": 10000,
        "reputation": 0,
        "base_level": 1,
        "type": None,
        "assigned_servants": [],
        "servant_jobs": {},
        "max_workers": 5,
        "costs": 0,
        "owned": True,
        "skill": 10,  # Initialize to base_level * 10
        "skill_bonus": 0  # Initialize bonus to 0
    }
}

default workers = []
default unlocked_shops = {"shop1": True, "shop2": False, "shop3": False}

# Font size preferences - persistent across sessions
default persistent.large_font_mode = False
default available_workers = []
default displayed_workers = []
default roster_current_page = 0
default current_report_index = 0
default left_worker = None  # Storage by default
default right_worker = None  # Will be set in init python
default daily_report = []
default building_filter = "All Buildings"
default worker_building_filter = "All Workers"
default worker_job_filter = "All Jobs"
default daily_report_job_filter = "All Jobs"
define roster_page_size = 50
default current_worker_index = 0
default current_worker = None  # Updated after workers are loaded
default daily_spawns = 0
define MAX_DAILY_SPAWNS = 5
default last_worker_refill_day = None
default last_worker_refill_month = None
default last_worker_refill_year = None
default map_worker_refill_count = 0  # Count how many times workers were refilled from map today
default last_map_refill_day = None  # Track which day the map refill count was reset
default buy_servants_filter_gender = None  # None = All, "male" = Male only, "female" = Female only (filter for Buy Servants list)
default take_a_walk_in_progress = False
default last_take_a_walk_day = None
default worker_interactions_today = {}  # Track daily interactions per worker: {worker_name: {day: count}}
default MAX_DAILY_INTERACTIONS = 2  # Maximum interactions per worker per day
default custom_names = {
    "Building 1": "Building 1"
}
default _force_new_game_reset = False
default acting_worker = ""  # Default value for acting_worker
default event_flags = {}  # Storage for event flags/tokens that are used for event chains and conditions
default plaza_servants_text_hover = False  # Controls hover state of PlazaServants imagebutton when textbutton is hovered
default shops_text_hover = False  # Controls hover state of shop imagebuttons when "Visit Shops" textbutton is hovered
default recruit_workers_text_hover = False  # Controls hover state of PlazaFountain imagebutton when "Recruit Workers" textbutton is hovered
default take_a_walk_text_hover = False  # Controls hover state of PlazaFountain imagebutton when "Take a Walk" textbutton is hovered
default buy_buildings_text_hover = False  # Controls hover state of buyable buildings when "Buy Buildings" textbutton is hovered
default tooltips_enabled_by_screen = {}  # Dictionary to store tooltip state per screen (defaults to True if not set)
default _last_tooltip_screen = None  # Track last screen for tooltip context guard
default academy_enrolled = False  # True after player pays Academy tuition (Academy appears in building_selection, not in Manage Buildings)
default academy_haggle_available = True  # Reset each day; False after a failed haggle until next day
default yvara_known_name = False
default yvara_devotion = 0   # Romantic route progress — warmth, trust, genuine feeling
default yvara_dominion = 0  # Domination route progress — leverage, submission, power over her
default yvara_affection = 0 # General closeness; gates stage transitions regardless of route
default yvara_stage = 1
default yvara_visit_count = 0
default yvara_last_question_total_days = None
default yvara_last_gift_total_days = None
default yvara_last_talk_total_days = None
default yvara_s1_talks_done = []        # IDs of completed Stage 1 conversations
default yvara_s1_remarks_done = []      # IDs of completed Stage 1 remarks
default yvara_gifts_given = 0           # Total gifts accepted by Yvara (non-negative reactions)
default yvara_s2_talks_done = []        # IDs of completed Stage 2 conversations
default yvara_s2_remarks_done = []      # IDs of completed Stage 2 remarks
default yvara_s2_gifts_given = 0        # Gifts given during Stage 2 specifically
default yvara_s3_talks_done = []        # IDs of completed Stage 3 conversations
default yvara_s3_remarks_done = []      # IDs of completed Stage 3 remarks
default yvara_observed_sessions = 0         # Number of Observed Lesson sessions completed
default yvara_observed_last_day = None      # Last day Observed Lesson was used
default yvara_lesson_absorbed = False       # Flag: 6th session absorbed flag
default yvara_leverage_financial = False    # Flag: player discovered/used Academy ledger leverage
default yvara_s3_gate_ready = False         # Flag: Stage 3 gate scene unlocked, waiting for after-hours visit
default yvara_s3_gate_ready_total_days = None  # Day the after-hours invitation was unlocked
default yvara_s3_gate_fired = False         # Flag: Stage 3 gate scene already triggered
default yvara_s4_talks_done = []            # IDs of completed Stage 4 conversations
default yvara_s4_remarks_done = []          # IDs of completed Stage 4 remarks
default yvara_s4_finance_unlocked = False   # Stage 4 favor/donation menu unlocked after the Academy pressure becomes visible
default yvara_s4_finance_last_day = None    # Last day a Stage 4 finance interaction was used
default yvara_s4_donation_total = 0         # Total number of Stage 4 donation interactions
default yvara_s4_donation_highest_tier = 0  # Highest donation tier reached in Stage 4
default yvara_s4_favors_total = 0           # Total number of Stage 4 paid favors
default yvara_s4_favor_highest_tier = 0     # Highest paid-favor tier reached in Stage 4
default yvara_s4_gate_fired = False         # Flag: Stage 4 gate scene (The Storm) already triggered
default yvara_morning_after_done = False    # Flag: Morning After scene already fired
default yvara_evening_academy_last_day = None  # Last day Evening at Academy was visited
default yvara_continuation_notice_shown = False  # One-time notice that more story content is planned
default arena_unlocked = False  # True after arena trial succeeds/mediocre/critical
default arena_lanista_paid = False  # True after player pays Lanista permit
define LANISTA_PERMIT_COST = 10000  # Cost to obtain Lanista permit for the coliseum
define SPECIAL_MATCH_COST = 5000  # Cost to enter a special match (2 rounds + combat roll)
default alchemy_unlocked = False  # True after player pays alchemist pass at Academy laboratory
define ALCHEMY_PASS_COST = 6000  # One-time cost to unlock the Academy laboratory
define ALCHEMY_COST_BASIC = 350  # Batch of basic potions (health/energy)
define ALCHEMY_COST_QUALITY = 800  # Quality tier: trait or greater potions
define ALCHEMY_COST_PREMIUM = 1400  # Premium tier: extraordinary potions on critical
default _alchemy_chosen_worker = None  # Worker chosen for alchemy craft (set by screen)
default _alchemy_investment_tier = None  # "basic", "quality", or "premium" (set before choose_worker)
default last_laboratory_use_total_days = None  # Total days when laboratory was last used; 3-day cooldown between sessions
define ALCHEMY_LABORATORY_COOLDOWN_DAYS = 3
default arena_special_match_intro_done = False  # True after first-time explanation of special matches
default last_special_match_total_days = None  # Total days when last special match was played; once per week (7 days). Saved.
default last_special_match_worker_name = None  # Name of gladiator who last fought (for cooldown message). Saved.
default _arena_chosen_worker = None  # Worker chosen in choose_worker_for_arena_trial (set by screen, read by arena_do_trial)
default _arena_special_chosen_worker = None  # Worker chosen for special match (set by screen)

init python:
    def yvara_recalculate_stage():
        """Update Yvara stage from affection thresholds.
        Stage 4 requires the S3 gate to have fired.
        Stage 5+ requires both S3 and S4 gates to have fired."""
        aff = int(getattr(store, "yvara_affection", 0) or 0)
        gate_s3 = bool(getattr(store, "yvara_s3_gate_fired", False))
        gate_s4 = bool(getattr(store, "yvara_s4_gate_fired", False))
        if gate_s3 and gate_s4 and aff >= 91:
            store.yvara_stage = 8
        elif gate_s3 and gate_s4 and aff >= 83:
            store.yvara_stage = 7
        elif gate_s3 and gate_s4 and aff >= 73:
            store.yvara_stage = 6
        elif gate_s3 and gate_s4 and aff >= 64:
            store.yvara_stage = 5
        elif gate_s3 and aff >= 51:
            store.yvara_stage = 4
        elif aff >= 31:
            store.yvara_stage = 3
        elif aff >= 16:
            store.yvara_stage = 2
        else:
            store.yvara_stage = 1

    def yvara_is_dominion_route():
        """Return True when Yvara's route should resolve to dominion.

        Neutral is intentionally removed: ties are broken by route-specific
        content where possible, and fall back to devotion otherwise.
        """
        devotion = int(getattr(store, "yvara_devotion", 0) or 0)
        dominion = int(getattr(store, "yvara_dominion", 0) or 0)
        if dominion != devotion:
            return dominion > devotion

        favors = int(getattr(store, "yvara_s4_favors_total", 0) or 0)
        donations = int(getattr(store, "yvara_s4_donation_total", 0) or 0)
        if favors != donations:
            return favors > donations

        observed = int(getattr(store, "yvara_observed_sessions", 0) or 0)
        good_word = int(getattr(store, "yvara_good_word_count", 0) or 0)
        if observed != good_word:
            return observed > good_word

        return False

    def yvara_is_devotion_route():
        return not yvara_is_dominion_route()

    # Gift table: item_id -> (devotion_gain, dominion_gain, affection_gain, reaction_label)
    YVARA_GIFTS = {
        # Shared gifts
        "rare_book":          (3, 0, 5, "yvara_gift_rare_book"),
        "fine_wine":          (2, 0, 3, "yvara_gift_fine_wine"),
        "herbal_tea":         (2, 0, 2, "yvara_gift_herbal_tea"),
        "flower_bouquet":     (3, 0, 4, "yvara_gift_flowers"),
        "chocolates":         (1, 0, 2, "yvara_gift_chocolates"),
        "bonbons_box":        (1, 0, 2, "yvara_gift_chocolates"),
        "elixir_passion":     (0, 2, -2, "yvara_gift_elixir"),
        # Devotion route — romantic, personal
        "handwritten_poem":   (4, 0, 4, "yvara_gift_poem"),
        "botanical_pressing": (3, 0, 3, "yvara_gift_botanical"),
        # Dominion route — control, compliance
        "spiked_tea":         (0, 3, 1, "yvara_gift_spiked_tea"),
        "silk_ribbon":        (0, 2, 2, "yvara_gift_silk_ribbon"),
    }

    def yvara_get_giftable_items():
        """Return list of (item_id, display_name, qty) from manager inventory that Yvara accepts."""
        inv_store = getattr(store, "manager_inventory", [])
        inv_global = manager_inventory if "manager_inventory" in globals() else []
        item_defs = items_json.get("items", []) if "items_json" in globals() and isinstance(items_json, dict) else []
        allowed = set(getattr(store, "YVARA_GIFTS", YVARA_GIFTS).keys())
        blocked_ids = {"diamond", "ruby", "emerald", "sapphire"}
        allowed -= blocked_ids

        result = []
        qty_by_id = {}
        seen = set()
        inv = list(inv_store or [])
        if inv_global is not inv_store:
            inv += list(inv_global or [])
        for entry in inv:
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            iid = str(entry[0])
            try:
                qty = int(entry[1])
            except Exception:
                qty = 1
            if iid in allowed and qty > 0:
                qty_by_id[iid] = qty_by_id.get(iid, 0) + qty
        for iid, qty in qty_by_id.items():
            if iid in seen:
                continue
            seen.add(iid)
            item_data = next((i for i in item_defs if i.get("id") == iid), None)
            name = item_data["display_name"] if item_data else iid
            result.append((iid, name, qty))
        return result

    def yvara_remove_gift_item(item_id, quantity=1):
        """Remove gift item from manager inventory (store/global safe)."""
        try:
            _qty = max(1, int(quantity))
        except Exception:
            _qty = 1
        def _count_item(inv, target_id):
            total = 0
            try:
                for entry in list(inv or []):
                    if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                        continue
                    if str(entry[0]) != str(target_id):
                        continue
                    try:
                        total += max(0, int(entry[1]))
                    except Exception:
                        total += 1
            except Exception:
                return 0
            return total

        _store_inv = getattr(store, "manager_inventory", None)
        _global_inv = manager_inventory if "manager_inventory" in globals() else None

        if _store_inv is not None:
            try:
                _before = _count_item(_store_inv, item_id)
                if _before > 0:
                    remove_item_from_inventory(_store_inv, item_id, min(_qty, _before))
                    _after = _count_item(getattr(store, "manager_inventory", _store_inv), item_id)
                    if _after < _before:
                        return True
            except Exception:
                pass

        if _global_inv is not None and _global_inv is not _store_inv:
            try:
                _before = _count_item(_global_inv, item_id)
                if _before > 0:
                    remove_item_from_inventory(_global_inv, item_id, min(_qty, _before))
                    _after = _count_item(_global_inv, item_id)
                    if _after < _before:
                        return True
            except Exception:
                pass

        return False

    class SafeNameDict(dict):
        """Legacy compatibility class (do not store in persistent)."""
        def __missing__(self, key):
            self[key] = key
            return key

    def _sanitize_persistent_obj(obj):
        """Convert SafeNameDict to plain dict inside persistent data."""
        try:
            if isinstance(obj, dict):
                if obj.__class__.__name__ == "SafeNameDict":
                    obj = dict(obj)
                return {k: _sanitize_persistent_obj(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize_persistent_obj(v) for v in obj]
            if isinstance(obj, tuple):
                return tuple(_sanitize_persistent_obj(v) for v in obj)
            if isinstance(obj, set):
                return set(_sanitize_persistent_obj(v) for v in obj)
        except Exception as e:
            renpy.log(f"_sanitize_persistent_obj error: {str(e)}")
        return obj

    # Clean any legacy SafeNameDict from persistent at init
    try:
        for k, v in list(getattr(persistent, "__dict__", {}).items()):
            setattr(persistent, k, _sanitize_persistent_obj(v))
        # Drop legacy snapshot fields from persistent (no longer used)
        if hasattr(persistent, "_slot_snapshots"):
            persistent._slot_snapshots = {}
        if hasattr(persistent, "_last_snapshot"):
            persistent._last_snapshot = None
        if hasattr(persistent, "_slot_to_apply"):
            persistent._slot_to_apply = None
        if hasattr(persistent, "loaded_via_save"):
            persistent.loaded_via_save = False
        if hasattr(persistent, "_context_restored"):
            persistent._context_restored = False
    except Exception as e:
        renpy.log(f"persistent sanitize error: {str(e)}")

    def mark_new_game_start():
        """Mark that the user explicitly started a new game."""
        try:
            store._force_new_game_reset = True
            store._just_loaded = False
        except Exception as e:
            renpy.log(f"mark_new_game_start error: {str(e)}")

    def _mark_loaded():
        """Ensure loaded saves don't trigger new-game reset."""
        try:
            store._just_loaded = True
            store.is_new_game = False
            store.game_initialized = True
            # Safety sync: if Arena is already owned in save data, keep it unlocked.
            arena_data = getattr(store, "available_buildings", {}).get("Arena", None)
            arena_in_owned = "Arena" in getattr(store, "owned_buildings", [])
            arena_owned_flag = isinstance(arena_data, dict) and bool(arena_data.get("owned", False))
            if arena_in_owned or arena_owned_flag:
                store.arena_unlocked = True
        except Exception as e:
            renpy.log(f"_mark_loaded error: {str(e)}")

    # Register after-load marker to prevent start reset after load.
    try:
        config.after_load_callbacks.append(_mark_loaded)
    except Exception as e:
        renpy.log(f"after_load callback register error: {str(e)}")
    def toggle_tooltips_for_screen(screen_name):
        """Toggle tooltips for a specific screen. Does not return anything."""
        # Default state: True only for map_screen, False for all others
        default_state = True if screen_name == "map_screen" else False
        current_state = tooltips_enabled_by_screen.get(screen_name, default_state)
        tooltips_enabled_by_screen[screen_name] = not current_state
        # Don't return anything - Ren'Py actions should not return values
    
    def get_tooltips_state_for_screen(screen_name):
        """Get tooltips state for a specific screen. Returns True if enabled (default)."""
        # Default state: True only for map_screen, False for all others
        default_state = True if screen_name == "map_screen" else False
        return tooltips_enabled_by_screen.get(screen_name, default_state)
default event_worker_name = ""  # Variable to store the name of the worker being discussed in an event
default current_affected_building = None  # Variable to store the currently affected building in an event
default affected_building_info = ""  # Holds formatted info about the affected building
default building_notification = None  # Holds the notification message about the affected building


# Ensure store.workers exists; do NOT auto-populate roster with all workers
# FIXED: Removed init python block that was reinitializing workers on load
# Workers are already defined with 'default workers = []' above
init python:
    # Only define acting_worker default if needed
    if not hasattr(store, "acting_worker"):
        store.acting_worker = "Manager"

# Set right_worker and current_worker to the first rostered worker, with higher priority
init 10 python:
    renpy.log("Setting right_worker and current_worker...")
    if hasattr(store, "workers") and store.workers:
        store.right_worker = store.workers[0]
        store.current_worker = store.workers[0]
        renpy.log(f"Set right_worker to {store.right_worker['name']} and current_worker to {store.current_worker['name']}")
    else:
        store.right_worker = None
        store.current_worker = None
        renpy.log("No workers loaded, setting right_worker and current_worker to None")

    # Apply defaults to workers if workers list exists
    if hasattr(store, "workers"):
        for worker in store.workers:
            ensure_worker_defaults(worker)

# Initialize inventories after all init phases
label after_init:
    python:
        # Ensure workers have unique inventories
        for worker in store.workers:
            if "inventory" not in worker or not isinstance(worker["inventory"], list):
                worker["inventory"] = []
            else:
                worker["inventory"] = list(worker["inventory"])  # Force a new copy
            renpy.log(f"Initialized {worker['name']} inventory: {worker['inventory']}, ID: {id(worker['inventory'])}")
        renpy.log(f"Manager inventory: {manager_inventory}, ID: {id(manager_inventory)}")
    return
    
################################################################################
### UI STYLE DEFINITIONS
################################################################################

style header_style:
    size 24
    color "#ffffff"
    bold True
    outlines [(2, "#000000", 0, 0)]
    xalign 0.5

style nav_button_text:
    color "#ffffff"
    hover_color "#ff69b4"
    size 14
    bold True
    outlines [(1, "#000000", 0, 0)]
    hover_outlines [(1, "#ff69b499", 0, 0)]
    xalign 0.5
    yalign 0.5
    xpadding 20
    ypadding 10
    text_align 0.5
    layout "nobreak"
    background None

style roster_button_text:
    color "#ffffff"
    hover_color "#ffffff"
    text_align 0.0
    size 14
    layout "subtitle"

style worker_details_header:
    size 24
    color "#ffffff"
    bold True
    xalign 0.0
    yalign 0.0

style roster_stats:
    size 14
    color "#aaaaaa"
    xalign 0.0
    text_align 0.0

style roster_button:
    xalign 0.0
    xpadding 0
    background None
    idle_background None
    hover_background "#333333"
    size 14
    text_align 0.0

################################################################################
### ALL SCREENS MOVED TO SCREENS.RPY
################################################################################






label game_over:
    scene black
    with fade
    "You have completely run out of money."
    "Game Over!"
    menu:
        "Quit the game":
            return
        "Restart game":
            jump start

init python:
    # Other existing init functions

    def get_affected_building_info():
        """
        Gets a formatted string with information about the affected building in an event.
        Sets the result in store.affected_building_info.
        """
        store.affected_building_info = ""
        if hasattr(store, "current_affected_building") and store.current_affected_building:
            building_name = store.current_affected_building
            building = available_buildings.get(building_name, {})
            btype_id = building.get("type")
            if btype_id:
                building_type = next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "")
                display_name = store.custom_names.get(building_name, building_name)
                store.affected_building_info = f"{building_type}: {display_name}"

    class Player:
        def __init__(self):
            self.title = "Tavern Owner"  # Default title
            self.name = "Player"  # Default name
            self.money = 1000  # Starting money
            self.workers = []  # List of workers
            self.buildings = []  # List of buildings

    # Create global player instance
    player = Player()

label explore:
    scene expression tavern_bg
    "You decide to explore the town..."
    
    menu:
        "Visit Shops":
            call screen shop_selection
        "Return to Tavern":
            jump tavern_screen
    
    return

# Soft focus to push scenery behind Yvara's bust.
transform yvara_bg_blur:
    blur 4.0

# Compatibility alias for academy entry flow.
label yvara_prologue:
    jump academy_tuition_dialogue

# Academy tuition: Ren'Py say (dialogue box + name) + menu (same style as recruitment). After pay → map + academy_menu overlay.
label academy_tuition_dialogue:
    $ _academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else "images/event_bg.png")
    $ _yvara_bust = "images/yvara/yvara_formal_neutral.png" if renpy.loadable("images/yvara/yvara_formal_neutral.png") else None
    scene expression _academy_bg at yvara_bg_blur
    # Stronger dimmer to push background behind Yvara's bust.
    show black as yvara_bg_dim:
        alpha 0.35
    if _yvara_bust:
        show expression _yvara_bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    academy_director "Welcome, traveller. I am Yvara. I direct this Academy. Our institution offers structured courses in Academics, Amatory Arts, and Hospitality. Your workers may attend and gain experience under our teachers."
    $ yvara_known_name = True
    yvara "To enrol your establishment and gain access to our curriculum, the tuition is fifteen thousand coins. Pay once, and your workers may study under our teachers whenever you send them."
    jump academy_tuition_menu

label academy_tuition_menu:
    menu:
        yvara "What will you do?"
        "Pay the tuition ($15,000).":
            if money >= 15000:
                $ add_academy_building()
                $ money -= 15000
                if _yvara_bust:
                    hide expression _yvara_bust
                hide yvara_bg_dim
                $ renpy.show_screen("map_screen")
                $ renpy.show_screen("academy_menu")
                jump tavern_screen
            else:
                yvara "You need $15,000 to pay the tuition."
                jump academy_tuition_menu
        "Try to haggle (50%% chance; if it fails, locked until tomorrow)." if academy_haggle_available:
            if money < 7500:
                yvara "You need at least $7,500 to try haggling."
                jump academy_tuition_menu
            $ _haggle_success, _haggle_price = try_academy_haggle()
            if _haggle_success:
                $ add_academy_building()
                $ money -= _haggle_price
                if _yvara_bust:
                    hide expression _yvara_bust
                hide yvara_bg_dim
                $ renpy.show_screen("map_screen")
                $ renpy.show_screen("academy_menu")
                $ renpy.notify("The director agreed! You paid $7,500 for tuition.")
                jump tavern_screen
            else:
                if _yvara_bust:
                    hide expression _yvara_bust
                hide yvara_bg_dim
                $ renpy.notify("The director refused. You cannot haggle again until tomorrow.")
                $ renpy.show_screen("map_screen")
                jump tavern_screen
        "Leave.":
            if _yvara_bust:
                hide expression _yvara_bust
            hide yvara_bg_dim
            $ renpy.show_screen("map_screen")
            jump tavern_screen

label yvara_visit:
    $ maybe_show_intro_popup("yvara_visit")
    $ _academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else "images/event_bg.png")
    $ _yvara_bust = "images/yvara/yvara_formal_neutral.png" if renpy.loadable("images/yvara/yvara_formal_neutral.png") else None
    $ yvara_visit_count += 1
    $ yvara_recalculate_stage()
    scene expression _academy_bg at yvara_bg_blur
    show black as yvara_bg_dim:
        alpha 0.35
    if _yvara_bust:
        show expression _yvara_bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40

    if not yvara_known_name:
        academy_director "The director glances up from her papers. Her expression is composed—measured."
        academy_director "I am Yvara. I run this institution."
        yvara "Tell me, how can I help you?"
        $ yvara_known_name = True
    elif yvara_visit_count <= 2:
        yvara "Back again. Is there something you needed, or are you here out of habit now?"
    elif yvara_stage >= 3 and yvara_is_devotion_route():
        yvara "Come in."
        narrator "She does not look up, but the word comes immediately — no pause, no question."
    elif yvara_stage >= 3:
        yvara "You are here."
        narrator "A statement, not a greeting. But her posture shifts fractionally when she says it."
    elif yvara_stage >= 2 and yvara_is_devotion_route():
        yvara "You are becoming a reliable fixture around here."
        narrator "She says it without complaint. That might be the point."
    elif yvara_stage >= 2:
        yvara "I was wondering when you would show up."
        narrator "She does not say it warmly. But she does not say it coldly either."
    elif yvara_is_devotion_route():
        yvara "Come in."
    else:
        yvara "You again. What can I do for you?"

    jump yvara_visit_menu

label yvara_visit_menu:
    $ _total_days = calculate_total_days()
    if not yvara_s4_gate_fired and len(yvara_s4_talks_done) >= 3 and yvara_affection >= 64:
        $ yvara_s4_gate_fired = True
        jump yvara_s4_gate_scene
    if yvara_s4_gate_fired and not yvara_morning_after_done:
        $ yvara_morning_after_done = True
        jump yvara_s4_morning_after
    $ _talk_free_today = yvara_last_talk_total_days != _total_days
    $ _s1_talk_pending = yvara_stage == 1 and len(yvara_s1_talks_done) < 3
    $ _s2_talk_pending = yvara_stage == 2 and len(yvara_s2_talks_done) < 3
    $ _s3_talk_pending = not yvara_s3_gate_fired and yvara_stage >= 3 and len(yvara_s3_talks_done) < 3
    $ _s4_talk_pending = not yvara_s4_gate_fired and yvara_stage >= 4 and len(yvara_s4_talks_done) < 3
    $ _remark_free_today = yvara_last_question_total_days != _total_days
    $ _s1_remark_pending = yvara_stage == 1 and len(yvara_s1_remarks_done) < 3
    $ _s2_remark_pending = yvara_stage == 2 and len(yvara_s2_remarks_done) < 2
    $ _s3_remark_pending = not yvara_s3_gate_fired and yvara_stage >= 3 and len(yvara_s3_remarks_done) < 2
    $ _s4_remark_pending = not yvara_s4_gate_fired and yvara_stage >= 4 and len(yvara_s4_remarks_done) < 2
    $ _visit_after_hours_available = yvara_s3_gate_ready and not yvara_s3_gate_fired and yvara_s3_gate_ready_total_days is not None and _total_days > yvara_s3_gate_ready_total_days
    $ _s4_finance_available = yvara_stage >= 4 and not yvara_s4_gate_fired and yvara_s4_finance_unlocked
    $ _s4_finance_free_today = yvara_s4_finance_last_day != _total_days
    $ _s4_finance_favor_route = yvara_is_dominion_route()
    $ _evening_available = yvara_s4_gate_fired and (_total_days - (yvara_evening_academy_last_day or 0)) >= 3
    menu:
        yvara "..."

        "Talk." if _talk_free_today and _s1_talk_pending:
            jump yvara_s1_talk_router
        "Talk." if _talk_free_today and _s2_talk_pending:
            jump yvara_s2_talk_router
        "Talk." if _talk_free_today and _s3_talk_pending:
            jump yvara_s3_talk_router
        "Talk." if _talk_free_today and _s4_talk_pending:
            jump yvara_s4_talk_router
        "Talk." if _talk_free_today and not _s1_talk_pending and not _s2_talk_pending and not _s3_talk_pending and not _s4_talk_pending:
            jump yvara_talk_generic
        "Talk." if not _talk_free_today:
            yvara "I need to get back to work. If you need anything else, I might find some time tomorrow."
            jump yvara_visit_menu

        "Make a remark." if _remark_free_today and _s1_remark_pending:
            jump yvara_s1_remark_router
        "Make a remark." if _remark_free_today and _s2_remark_pending:
            jump yvara_s2_remark_router
        "Make a remark." if _remark_free_today and _s3_remark_pending:
            jump yvara_s3_remark_router
        "Make a remark." if _remark_free_today and _s4_remark_pending:
            jump yvara_s4_remark_router
        "Make a remark." if _remark_free_today and not _s1_remark_pending and not _s2_remark_pending and not _s3_remark_pending and not _s4_remark_pending:
            if yvara_stage >= 5 and not yvara_continuation_notice_shown:
                $ yvara_continuation_notice_shown = True
                yvara "We have more to say to each other. When the time is right."
                narrator "(More on this story in future updates)"
            else:
                yvara "You have said everything worth saying for now."
            jump yvara_visit_menu
        "Make a remark." if not _remark_free_today:
            yvara "You have already made your point today."
            jump yvara_visit_menu

        "Buy favors." if _s4_finance_available and _s4_finance_free_today and _s4_finance_favor_route:
            jump yvara_s4_buy_favors
        "Buy favors." if _s4_finance_available and not _s4_finance_free_today and _s4_finance_favor_route:
            narrator "You have already tested that particular boundary today."
            jump yvara_visit_menu
        "Donate money." if _s4_finance_available and _s4_finance_free_today and not _s4_finance_favor_route:
            jump yvara_s4_donate_money
        "Donate money." if _s4_finance_available and not _s4_finance_free_today and not _s4_finance_favor_route:
            narrator "Another gesture today would feel too pointed. You leave it alone for now."
            jump yvara_visit_menu

        "Visit after hours." if _visit_after_hours_available:
            jump yvara_visit_after_hours

        "Evening at the Academy." if _evening_available:
            jump yvara_evening_academy
        "Evening at the Academy." if yvara_s4_gate_fired and not _evening_available:
            narrator "It has not been long enough since the last time. A few more days."
            jump yvara_visit_menu

        "Bring a gift." if yvara_last_gift_total_days != _total_days:
            jump yvara_gift
        "Bring a gift." if yvara_last_gift_total_days == _total_days:
            narrator "Bringing another gift the same day would be excessive. You think better of it."
            jump yvara_visit_menu

        "Take her measure.":
            jump yvara_assess_feelings

        "Leave.":
            if _yvara_bust:
                hide expression _yvara_bust
            hide yvara_bg_dim
            $ renpy.show_screen("map_screen")
            $ renpy.show_screen("academy_menu")
            jump tavern_screen

label yvara_assess_feelings:
    if yvara_is_devotion_route():
        narrator "You watch her while she works. The distance is still there, but there are moments where it softens before she catches herself."
        narrator "If this keeps going, the bond between you will likely grow through trust before anything else."
    else:
        narrator "She still meets you directly, but there is a subtle shift in how she responds when you press your point."
        narrator "The dynamic is becoming clearer: she resists, then yields in small ways she does not openly acknowledge."

    if yvara_stage == 1:
        $ _s1_talks = len(yvara_s1_talks_done)
        narrator "Assess: Devotion [yvara_devotion] | Dominion [yvara_dominion] | Affection [yvara_affection]/16 | Stage [yvara_stage] | Talks [_s1_talks]/3"
        if _s1_talks >= 3 and yvara_affection < 16:
            narrator "You have exhausted the available conversations for this stage. A thoughtful gift could help tip the balance."
    elif yvara_stage == 2:
        $ _s2_talks = len(yvara_s2_talks_done)
        narrator "Assess: Devotion [yvara_devotion] | Dominion [yvara_dominion] | Affection [yvara_affection]/31 | Stage [yvara_stage] | Talks [_s2_talks]/3"
        if _s2_talks >= 3 and yvara_affection < 31:
            narrator "No new core talks remain at this stage. If you need momentum, try a gift."
    elif yvara_stage == 3:
        $ _s3_talks = len(yvara_s3_talks_done)
        narrator "Assess: Devotion [yvara_devotion] | Dominion [yvara_dominion] | Affection [yvara_affection]/51 | Stage [yvara_stage] | Talks [_s3_talks]/3"
        if _s3_talks >= 3 and yvara_affection < 51:
            narrator "You are at a holding point. A gift could provide the final push."
    elif yvara_stage == 4:
        $ _s4_talks = len(yvara_s4_talks_done)
        narrator "Assess: Devotion [yvara_devotion] | Dominion [yvara_dominion] | Affection [yvara_affection]/64 | Stage [yvara_stage] | Talks [_s4_talks]/3"
        if yvara_s4_finance_unlocked and not yvara_s4_gate_fired:
            if yvara_is_dominion_route():
                narrator "The Academy's need has become a lever. She has yielded [yvara_s4_favors_total] time(s), and each concession leaves a little more of the dynamic exposed."
            else:
                narrator "She has accepted your help [yvara_s4_donation_total] time(s). Each gesture lands a little more personally than she intends."
        if _s4_talks >= 3 and yvara_affection < 64:
            narrator "The stage gate is close, but not there yet. Consider bringing a gift."
    else:
        narrator "Assess: Devotion [yvara_devotion] | Dominion [yvara_dominion] | Affection [yvara_affection] | Stage [yvara_stage]"
    jump yvara_visit_menu

# ── Stage 1 talk router ──────────────────────────────────────────────────────
label yvara_s1_talk_router:
    if "s1_t1" not in yvara_s1_talks_done:
        jump yvara_s1_talk_1
    elif "s1_t2" not in yvara_s1_talks_done:
        jump yvara_s1_talk_2
    elif "s1_t3" not in yvara_s1_talks_done:
        jump yvara_s1_talk_3
    else:
        jump yvara_talk_generic

# ── Stage 1 Talk 1: The Academy ──────────────────────────────────────────────
label yvara_s1_talk_1:
    $ _total_days = calculate_total_days()
    yvara "This institution has been standing for longer than most of the buildings on this street."
    yvara "You paid the tuition. That tells me something. What it tells me exactly, I have not decided yet."
    yvara "How long have you been running your establishment?"
    menu:
        "Long enough to know what I need from people.":
            $ yvara_dominion += 1
            yvara "Efficient. You see the people around you as means to an end."
            yvara "There is nothing wrong with that, provided the end is worth it."
        "We are still growing. I learn from the people I work with.":
            $ yvara_devotion += 2
            yvara "That is either wisdom or weakness. I have not decided which."
            narrator "But there is something in her expression that leans toward the former."
        "That is not your concern.":
            $ yvara_dominion += 1
            $ yvara_affection -= 1
            yvara "Fair enough."
            narrator "She returns to her papers without ceremony. Somehow it does not feel like a dismissal."
    yvara "I have seen people with coin and ambition walk through that door, overestimate those they employ, and disappear within a year."
    yvara "I hope you are not that kind."
    menu:
        "I am not.":
            $ yvara_affection += 2
            yvara "We will see."
        "What kind am I, then?":
            $ yvara_dominion += 1
            $ yvara_affection += 1
            yvara "Forthright. That is something."
            narrator "She does not smile, but she does not look away either."
        "What kind were the ones who failed?":
            $ yvara_devotion += 1
            $ yvara_affection += 2
            yvara "Impatient. Mistook speed for progress."
            yvara "A person who rushes past understanding is not learning—they are pretending."
    $ yvara_s1_talks_done = list(yvara_s1_talks_done) + ["s1_t1"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance
    jump yvara_visit_menu

# ── Stage 1 Talk 2: The Students ─────────────────────────────────────────────
label yvara_s1_talk_2:
    $ _total_days = calculate_total_days()
    yvara "A student asked me yesterday why we practice the same exercise every morning."
    yvara "I told her: because excellence is not an event. It is a habit."
    yvara "She did not seem satisfied with that answer."
    menu:
        "She will understand it when she needs it.":
            $ yvara_dominion += 1
            $ yvara_affection += 1
            yvara "That is what I thought."
            narrator "A pause. As if she is deciding whether to say the next part."
            yvara "You think in longer terms than most people I deal with."
        "What would have satisfied her?":
            $ yvara_devotion += 2
            yvara "A demonstration. Not an explanation."
            yvara "I adjusted the exercise the next day. She has not complained since."
            narrator "The way she says it is matter-of-fact, but there is satisfaction behind it."
        "Students should ask those questions.":
            $ yvara_devotion += 1
            $ yvara_affection += 2
            yvara "Yes. The ones who do not ask are the ones I worry about."
    yvara "What do you look for when you hire someone new?"
    menu:
        "Potential. Someone with something to prove.":
            $ yvara_devotion += 2
            $ yvara_affection += 1
            yvara "Interesting. Potential is unstable, but it burns clean when it catches."
            yvara "I do the same."
        "Obedience first. I can teach skill, not disposition.":
            $ yvara_dominion += 2
            $ yvara_affection += 1
            yvara "Pragmatic. I disagree—but only partly."
            yvara "Disposition shapes everything. You are not wrong to want it clear from the start."
        "Honesty. It is rarer than skill.":
            $ yvara_affection += 3
            yvara "..."
            yvara "Yes. It is."
            narrator "She says it quietly, and for a moment she seems somewhere else entirely."
    $ yvara_s1_talks_done = list(yvara_s1_talks_done) + ["s1_t2"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_1
    jump yvara_visit_menu

# ── Stage 1 Talk 3: The Methods ──────────────────────────────────────────────
label yvara_s1_talk_3:
    $ _total_days = calculate_total_days()
    yvara "I learned to teach from a woman I hated for six years."
    narrator "She says it without preamble, without looking up from the ledger she is annotating."
    yvara "She was exacting. Unforgiving of carelessness. She never praised anything until it was done."
    yvara "I left her school certain I would do things differently."
    menu:
        "And did you?":
            $ yvara_devotion += 1
            $ yvara_affection += 3
            yvara "Not as much as I intended."
            yvara "I understand now what she was doing. I did not then."
            narrator "There is no shame in it—just the flat fact of someone who has thought about it for years."
        "You became her.":
            $ yvara_dominion += 2
            $ yvara_affection += 2
            narrator "She looks up at that."
            yvara "Partly. I kept what worked."
            yvara "The part I discarded was the contempt. She never believed her students would actually make it."
            yvara "I believe mine will."
        "What did you do differently?":
            $ yvara_devotion += 2
            $ yvara_affection += 2
            yvara "I tell my students when they do well."
            yvara "It sounds small. It is not."
    yvara "Why are you still coming here, exactly?"
    menu:
        "To understand how things are progressing here.":
            $ yvara_affection += 1
            yvara "That is what you say."
            narrator "She leaves it there."
        "I find the conversation useful.":
            $ yvara_devotion += 1
            $ yvara_affection += 2
            yvara "I have been told I am difficult to talk to."
            yvara "Most people mean it as a complaint."
            narrator "You are not sure how she means it right now."
        "I have not decided yet.":
            $ yvara_dominion += 1
            $ yvara_affection += 2
            yvara "At least that is honest."
            narrator "For the first time, she almost looks amused."
    $ yvara_s1_talks_done = list(yvara_s1_talks_done) + ["s1_t3"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_2
    jump yvara_visit_menu

# ── Generic talk (after all S1 conversations done or S2+) ────────────────────
label yvara_talk_generic:
    $ _total_days = calculate_total_days()
    if yvara_stage == 1:
        # All three formal conversations done — now just companionable time
        narrator "You stay a while. She works. You talk about small things—a difficult student, the cost of ink, whether the autumn light comes through the east window at the right angle for reading."
        if yvara_is_dominion_route():
            narrator "She keeps her answers short, but she keeps answering. There is something in the way she watches you from the corner of her eye—measuring."
            yvara "You ask a lot of questions for someone who claims to just be passing through."
            narrator "She says it without real hostility. It is almost like a game she has started playing without admitting it."
        else:
            narrator "She answers more than she needs to. She does not seem to notice, or perhaps she does not mind."
            narrator "When you eventually stand to leave, there is a pause before she looks back down at her papers."
            yvara "Same time tomorrow, probably."
            narrator "It is not quite a question."
    elif yvara_stage == 2:
        if yvara_is_dominion_route():
            narrator "She pushes back on something you say—a small thing, a matter of opinion—and holds the position longer than the argument warrants."
            narrator "It is not hostility. It might be the opposite."
            yvara "You do not back down easily."
            narrator "There is a pause. She seems to decide something."
            yvara "Good."
        else:
            narrator "The conversation finds its own level without either of you steering it. She talks about a student who has been struggling, and you notice she is thinking out loud rather than reporting."
            narrator "At some point she refills her tea and offers you the second cup without comment. She does not usually do that."
            yvara "You are easier to talk to than most people who come through here."
            narrator "She says it like a fact she has only recently confirmed."
    elif yvara_stage == 4:
        if yvara_is_dominion_route():
            narrator "She is composed and exact and aware of you in the room the way someone is aware of a thing they are trying not to think about."
            narrator "The conversation stays on the surface. Both of you know that. Neither of you breaks through it."
            yvara "You are patient."
            narrator "A pause."
            yvara "I have not decided whether that is comfortable or not."
        else:
            narrator "You talk the way people do after something has changed but neither of them is ready to name it. She is careful with her words. You are, too."
            narrator "At some point the conversation does what conversations do when both people are paying close attention — it says something true without either of them quite deciding to."
            yvara "I am not sure what the protocol is for this."
            narrator "She says it plainly. Not asking for help with the protocol."
            yvara "I suspect there is not one."
    elif yvara_stage >= 3:
        if yvara_is_dominion_route():
            narrator "She is more precise than usual today—answers clipped, movements deliberate—and you realize she is very aware of where you are in the room."
            narrator "At some point she stops what she is doing to look at you directly."
            yvara "You have a particular quality of attention."
            narrator "A pause."
            yvara "I have not decided whether I find it inconvenient."
        else:
            narrator "You talk with an ease that neither of you remarks on—about the students, about the season, about nothing in particular. The Incident is between you somewhere, unspoken but present."
            narrator "At one point she glances up from the page she was not really reading."
            yvara "Someone spoke of you today. Quite fondly, as it happens."
            narrator "She does not say who."
            yvara "I find I am glad you were here that day."
            narrator "She does not say which day. She does not need to."
        if yvara_stage >= 5 and not yvara_continuation_notice_shown:
            $ yvara_continuation_notice_shown = True
            yvara "We have more to say to each other. When the time is right."
            narrator "(More on this story in future updates)"
    elif yvara_is_dominion_route():
        narrator "The conversation has an edge to it today. She disagrees with something you say—firmly, without apology—and for a moment you are not sure which direction this is going."
        narrator "Then she refills her tea and keeps talking."
        yvara "You are either very confident or very stubborn. I have not decided which."
        narrator "There is something in the way she watches you that suggests she finds both possibilities interesting."
    else:
        narrator "You talk for longer than you meant to. She mentions a book she has been re-reading—something she first encountered as a student—and you find yourself actually listening."
        narrator "By the time the conversation slows, the light in the room has shifted."
        yvara "This was... not unpleasant."
        narrator "She sounds faintly surprised at herself."
    $ yvara_last_talk_total_days = _total_days
    jump yvara_visit_menu

# ── Stage 2 talk router ───────────────────────────────────────────────────────
label yvara_s2_talk_router:
    if "s2_t1" not in yvara_s2_talks_done:
        jump yvara_s2_talk_1
    elif "s2_t2" not in yvara_s2_talks_done:
        jump yvara_s2_talk_2
    elif "s2_t3" not in yvara_s2_talks_done:
        jump yvara_s2_talk_3
    else:
        jump yvara_talk_generic

# ── Stage 2 Talk 1: The Question She Asks ────────────────────────────────────
label yvara_s2_talk_1:
    $ _total_days = calculate_total_days()
    narrator "She does not look up when you come in, which is normal. What is not normal is that she speaks first."
    yvara "I have been thinking."
    narrator "A pause. She sets her pen down—a thing she almost never does."
    yvara "What is it you actually want? Not from this institution. From all of it."
    narrator "The question sits in the room. She is watching you now."
    menu:
        "To build something that lasts.":
            $ yvara_devotion += 2
            $ yvara_affection += 2
            yvara "That is a longer ambition than most people in your position carry."
            narrator "She considers it for a moment, as though weighing it against something."
            yvara "Most people want what they can touch by the end of the season."
            menu:
                "I am patient.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 2
                    yvara "..."
                    yvara "Yes. I am beginning to believe that."
                    narrator "She picks up her pen again, but she does not immediately write anything."
                "The short view is for people who do not expect to be around long.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 1
                    yvara "Blunt."
                    yvara "But not wrong."
                    narrator "The corner of her mouth moves, barely."
        "Power. I would rather not pretend otherwise.":
            $ yvara_dominion += 2
            $ yvara_affection += 1
            narrator "She does not flinch. If anything, something in her posture settles."
            yvara "At least you say it plainly."
            yvara "Most people who want power spend a great deal of energy describing something else."
            menu:
                "Dishonesty is inefficient.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 2
                    yvara "Mm."
                    narrator "She seems to find that answer more interesting than she expected."
                    yvara "What do you do with it, when you have it?"
                    narrator "She does not wait for the answer. She returns to her work. But the question stays in the room."
                "I prefer to know what I am dealing with.":
                    $ yvara_affection += 2
                    yvara "Then we have something in common."
                    narrator "Brief. Final. Not unfriendly."
        "I am not entirely certain yet.":
            $ yvara_affection += 3
            narrator "She blinks. It is the closest thing to surprise you have seen from her."
            yvara "That is honest."
            yvara "Most people have an answer prepared. A real one and then the one they say."
            menu:
                "I find rehearsed answers suspicious.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 2
                    yvara "..."
                    narrator "She looks at you for a moment longer than necessary."
                    yvara "So do I."
                "I thought you might appreciate the unvarnished version.":
                    $ yvara_affection += 2
                    yvara "I do."
                    narrator "Simply said. She seems to mean it."
    $ yvara_s2_talks_done = list(yvara_s2_talks_done) + ["s2_t1"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_3
    jump yvara_visit_menu

# ── Stage 2 Talk 2: The Correction ───────────────────────────────────────────
label yvara_s2_talk_2:
    $ _total_days = calculate_total_days()
    narrator "She does not greet you. She waits until you have settled, and then she says:"
    yvara "You said something the last time you were here."
    narrator "She does not look up from the page she is annotating."
    yvara "About how you make decisions under pressure. You said you go quiet."
    narrator "A beat."
    yvara "You do not. I have watched you. You go very still, and then you act."
    narrator "She says it as a correction, the same way she would correct a student's misread passage. But she has been paying attention—closely—and there is no pretending otherwise."
    menu:
        "I did not think you were listening that carefully.":
            $ yvara_devotion += 1
            $ yvara_affection += 3
            yvara "I always listen carefully."
            narrator "A pause. Then, quieter:"
            yvara "With some people more than others."
            narrator "She does not explain which category you are in. She does not need to."
            menu:
                "I will have to be more precise, then.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 1
                    yvara "Please do. Vague people are tiresome."
                    narrator "But there is something in her tone that is not quite a reprimand."
                "Why the difference?":
                    $ yvara_affection += 2
                    narrator "She considers the question."
                    yvara "Some people are worth understanding."
                    narrator "She returns to her page. The sentence sits there, complete."
        "Was I wrong?":
            $ yvara_dominion += 1
            $ yvara_affection += 2
            yvara "Yes."
            yvara "Self-knowledge is harder than most people admit. You described what you feel, not what you do."
            menu:
                "And you can tell the difference.":
                    $ yvara_affection += 2
                    yvara "Usually."
                    narrator "She says it without vanity, as a plain fact."
                "That is a useful distinction.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 1
                    yvara "Most of the useful distinctions are."
                    narrator "Dry. But she offers it without impatience."
        "You are right.":
            $ yvara_devotion += 2
            $ yvara_affection += 2
            narrator "She stops annotating."
            yvara "You are not going to argue it."
            narrator "It is not quite a question."
            menu:
                "There is no argument. You observed correctly.":
                    $ yvara_affection += 2
                    yvara "..."
                    narrator "She looks at you for a moment with something that is not quite satisfaction—but is close to it."
                    yvara "You are easier to talk to when you are not performing."
                "I have no reason to.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 1
                    yvara "Good."
                    narrator "Short. Genuine."
    $ yvara_s2_talks_done = list(yvara_s2_talks_done) + ["s2_t2"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_4
    jump yvara_visit_menu

# ── Stage 2 Talk 3: The Evening ───────────────────────────────────────────────
label yvara_s2_talk_3:
    $ _total_days = calculate_total_days()
    narrator "The light through the east window has gone from gold to grey. You have been here longer than usual."
    narrator "She notices. She does not comment. She keeps working."
    narrator "Then she does."
    yvara "It is getting late."
    narrator "She says it without looking up. Not a suggestion. Not quite an observation."
    menu:
        "I suppose I should go.":
            $ yvara_devotion += 2
            $ yvara_affection += 3
            narrator "She does look up at that."
            yvara "You were not going to."
            narrator "She says it plainly, without accusation. It lands like a fact she finds curious."
            menu:
                "No. Not yet.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 2
                    narrator "She holds your gaze for a moment, then looks back at her papers."
                    yvara "Then stay."
                    narrator "She does not say it gently. But she does say it."
                "I lose track of time here.":
                    $ yvara_affection += 2
                    yvara "I know."
                    narrator "Said quietly. Almost to herself."
        "I enjoy watching you work.":
            $ yvara_dominion += 2
            $ yvara_affection += 2
            narrator "She goes still for a moment."
            yvara "Do you."
            narrator "Not a question. She is deciding something."
            menu:
                "You concentrate differently than most people.":
                    $ yvara_affection += 2
                    narrator "A pause."
                    yvara "No one has said that to me before."
                    narrator "She does not say whether she minds."
                "It tells me things.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 1
                    yvara "What kind of things."
                    narrator "Still not a question. But she is waiting for the answer."
                    narrator "You do not give it. The silence is more interesting."
        "I do not know why I am still here.":
            $ yvara_affection += 4
            narrator "She sets her pen down."
            narrator "The silence between you stretches—not uncomfortably. She is thinking."
            yvara "Neither do I."
            narrator "It is the most uncertain she has sounded. It does not seem to trouble her."
            menu:
                "Maybe that is enough of a reason.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 1
                    narrator "She considers that for a long moment."
                    yvara "Perhaps."
                    narrator "There is something in her expression that is very close to warmth."
                "Some things do not need explaining.":
                    $ yvara_affection += 1
                    yvara "..."
                    yvara "No. I suppose they do not."
                    narrator "She picks up her pen again. But she does not start writing."
    $ yvara_s2_talks_done = list(yvara_s2_talks_done) + ["s2_t3"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_5
    jump yvara_visit_menu

# ── Stage 2 remark router ─────────────────────────────────────────────────────
label yvara_s2_remark_router:
    $ _total_days = calculate_total_days()
    if "s2_r1" not in yvara_s2_remarks_done:
        jump yvara_s2_remark_1
    elif "s2_r2" not in yvara_s2_remarks_done:
        jump yvara_s2_remark_2
    else:
        yvara "You have said everything worth saying for now."
        jump yvara_visit_menu

# ── Stage 2 Remark 1: What No One Notices ────────────────────────────────────
label yvara_s2_remark_1:
    narrator "You have been watching her long enough to notice things. You say one of them."
    menu:
        "You mark your books in the margins, but only on the right-hand page.":
            narrator "She looks up from what she is doing."
            yvara "..."
            narrator "A pause that is a little longer than usual."
            yvara "I learned to read in a house with no natural light on the left side of the room. The habit stayed."
            narrator "She says it as though it is a minor fact. But no one has ever asked before."
            menu:
                "Habits like that tell you where a person came from.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 3
                    narrator "She is quiet for a moment."
                    yvara "Yes."
                    narrator "Just that. But she does not look away."
                "I find it difficult to read margins on the left anyway.":
                    $ yvara_affection += 2
                    $ yvara_devotion += 1
                    yvara "Most people do not notice it at all."
                    narrator "There is something in the way she says it that is almost wondering."
        "When you are thinking, you hold your pen without writing. You press the nib against your thumbnail.":
            narrator "She stops. Looks at her hand. The pen is exactly where you described."
            yvara "I was not aware I did that."
            narrator "She sets it down carefully."
            menu:
                "You do it when something is difficult.":
                    $ yvara_affection += 3
                    $ yvara_devotion += 1
                    yvara "And you noticed."
                    narrator "It is not an accusation. It is something closer to being seen, and not quite knowing what to do with it."
                "It happens whenever you are in the middle of a problem.":
                    $ yvara_affection += 2
                    $ yvara_dominion += 1
                    yvara "You have been paying very close attention."
                    narrator "She says it carefully—not threatened, not flattered. Working out what it means."
                    yvara "I am not sure how I feel about that."
                    narrator "She does not say she minds."
    $ yvara_s2_remarks_done = list(yvara_s2_remarks_done) + ["s2_r1"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_6
    jump yvara_visit_menu

# ── Stage 2 Remark 2: An Admission ───────────────────────────────────────────
label yvara_s2_remark_2:
    narrator "You say something you do not usually say."
    menu:
        "Tell her this is the part of the day you look forward to most.":
            narrator "She goes still."
            yvara "..."
            narrator "For a moment she seems to be deciding whether to deflect it."
            yvara "That is either very kind or very foolish."
            menu:
                "Does it matter which?":
                    $ yvara_devotion += 2
                    $ yvara_affection += 3
                    narrator "She considers that for a moment."
                    yvara "No."
                    narrator "Quiet. Genuine. The single syllable lands with more weight than a longer answer would have."
                "I have learned to prefer honest to sensible.":
                    $ yvara_affection += 3
                    yvara "Then we have something in common."
                    narrator "She says it so softly that for a moment you are not certain you heard it correctly."
        "Tell her you find it easier to think clearly here than anywhere else.":
            yvara "Here."
            narrator "She repeats the word as though she is placing it somewhere."
            yvara "Not the library? Not your own establishment?"
            menu:
                "Here specifically. I cannot explain it.":
                    $ yvara_affection += 3
                    $ yvara_devotion += 1
                    narrator "She is quiet for a long moment."
                    yvara "I will not ask you to."
                    narrator "And for once she does not press further. She lets it sit between you, gently."
                "Something about this room is clarifying.":
                    $ yvara_affection += 2
                    $ yvara_dominion += 1
                    yvara "The room has not changed."
                    narrator "She looks at you when she says it."
                    yvara "But perhaps something else has."
    $ yvara_s2_remarks_done = list(yvara_s2_remarks_done) + ["s2_r2"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_7
    jump yvara_visit_menu

# ── Stage 3 talk router ───────────────────────────────────────────────────────
label yvara_s3_talk_router:
    if "s3_t1" not in yvara_s3_talks_done:
        jump yvara_s3_talk_1
    elif "s3_t2" not in yvara_s3_talks_done:
        jump yvara_s3_talk_2
    elif "s3_t3" not in yvara_s3_talks_done:
        jump yvara_s3_talk_3
    else:
        jump yvara_talk_generic

# ── Stage 3 Talk 1: The Garden ───────────────────────────────────────────────
label yvara_s3_talk_1:
    $ _total_days = calculate_total_days()
    narrator "She is outside during a break, sitting on the low bench beside the east wall with a book open in her lap."
    narrator "She does not invite you to sit. She does not ask you to leave."
    narrator "After a moment she closes the book on her finger and looks at you."
    yvara "You have been building toward something. I have watched the way you move through this city."
    narrator "She says it plainly, as though she has been sitting with the observation for some time."
    yvara "What is it you actually want? Not from this place. From all of it."
    menu:
        "Build something worth keeping.":
            $ yvara_devotion += 3
            $ yvara_affection += 3
            narrator "She considers that."
            yvara "Most people in your position have not thought that far."
            narrator "A beat. She opens her book again, but does not read."
            yvara "I find that I hope you mean it."
            menu:
                "I do.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 2
                    narrator "She nods once. Not approval, exactly — something quieter than that."
                "Time will tell.":
                    $ yvara_affection += 1
                    yvara "Yes. It usually does."
                    narrator "She says it without irony."
        "I have not gotten that far.":
            $ yvara_devotion += 1
            $ yvara_affection += 2
            yvara "Honest, at least."
            narrator "She tilts her head slightly."
            yvara "Most people have a ready answer. I am never sure whether to trust those."
            menu:
                "Ready answers are usually rehearsed ones.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    yvara "Yes."
                    narrator "A longer pause. Something shifts in her expression — almost like recognition."
                    yvara "The Academy was built the same way. No plan for after. Just the conviction that it had to exist."
                "I will think of something.":
                    $ yvara_affection += 1
                    yvara "I expect you will."
                    narrator "Said simply. Not flattery."
        "Whatever serves my purpose.":
            $ yvara_dominion += 2
            $ yvara_affection += 2
            yvara "Yes."
            narrator "She looks at you steadily."
            yvara "I suppose that is the honest answer for most."
            narrator "A pause. Then, quietly:"
            yvara "The Academy was everything I had left. That is what I built it from."
            menu:
                "That makes it worth more than most things.":
                    $ yvara_affection += 2
                    narrator "She looks at you for a moment, and something in her posture shifts — not quite softening, but less guarded."
                    yvara "I think so too."
                "And now?":
                    $ yvara_dominion += 1
                    $ yvara_affection += 1
                    yvara "Now it stands on its own."
                    narrator "She says it like something she had to earn the right to believe."
    $ yvara_s3_talks_done = list(yvara_s3_talks_done) + ["s3_t1"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_8
    jump yvara_visit_menu

# ── Stage 3 Talk 2: The Favor ────────────────────────────────────────────────
label yvara_s3_talk_2:
    $ _total_days = calculate_total_days()
    narrator "She has left the ledger open on the side of the desk rather than putting it away before you arrived. The numbers are visible."
    narrator "They are not catastrophic. But they are uncomfortable. And she knows you have seen them."
    yvara "The Academy is in a period of... consolidation."
    narrator "She says it with the precise composure of someone who has decided not to be ashamed of something difficult."
    menu:
        "I can help with that. If you want.":
            $ yvara_devotion += 4
            $ yvara_affection += 3
            narrator "She goes still."
            narrator "It was not what she expected. She had prepared for something else — negotiation, perhaps, or the quiet implication of leverage."
            yvara "..."
            yvara "That is not a response I had anticipated."
            menu:
                "I know.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    narrator "She looks at you for a long moment. Then she closes the ledger."
                    yvara "Give me a few days to think about what that would look like."
                    narrator "She does not say thank you. But she does not need to."
                "The Academy matters. That is reason enough.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 2
                    yvara "You are not what I expected when you first came through that door."
                    narrator "She says it quietly, as though she is still working out whether that is a problem."
        "That is concerning. For my investment.":
            $ yvara_dominion += 3
            $ yvara_affection += 2
            $ yvara_leverage_financial = True
            narrator "She straightens. You have framed it correctly - not as a threat, exactly, but as an observation with weight behind it."
            yvara "Your investment is secure. The situation is temporary."
            yvara "But I understand your concern."
            menu:
                "Then let me look at the full picture.":
                    $ yvara_dominion += 2
                    $ yvara_affection += 1
                    narrator "A beat. She reaches across the desk and slides the ledger toward you."
                    yvara "This evening, then. After the last class."
                    narrator "The tour is professional. But it is private. And she offered it."
                "I am not here to pressure you.":
                    $ yvara_affection += 2
                    yvara "No. I did not think so."
                    narrator "She says it carefully. She is deciding something about you."
        "Show me everything.":
            $ yvara_dominion += 5
            $ yvara_affection += 2
            $ yvara_leverage_financial = True
            narrator "A pause. She holds your gaze."
            narrator "Then she stands, moves to the shelf behind her, and takes down a second ledger — one that was not visible from the doorway."
            yvara "This evening. After the last class closes."
            narrator "Her voice is level. She has made a calculation and executed it."
            yvara "You will want to see the full picture."
            menu:
                "I will be here.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 2
                    narrator "She nods once. Puts both ledgers on the desk."
                    yvara "Then we will discuss terms."
                "Terms are simple. I want to understand, not to take.":
                    $ yvara_affection += 3
                    narrator "She looks at you for a moment with something difficult to name."
                    yvara "...I will keep that in mind."
    $ yvara_s3_talks_done = list(yvara_s3_talks_done) + ["s3_t2"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_9
    jump yvara_visit_menu

# ── Stage 3 Talk 3: The Incident ─────────────────────────────────────────────
label yvara_s3_talk_3:
    $ _total_days = calculate_total_days()
    narrator "You are present when it happens — a student stumbles during a practical demonstration, catches a shelf edge badly, goes down hard."
    narrator "Two things happen simultaneously: Yvara moves from the far side of the room without breaking stride, and you move from the door."
    narrator "The student is on his feet within moments. Neither of you spoke more than was necessary. The room settles."
    narrator "After, when the students have filed out, she looks at you across the now-quiet room."
    yvara "You did not hesitate."
    menu:
        "Neither did you.":
            $ yvara_affection += 4
            narrator "A beat. She seems to find that answer both accurate and somehow disarming."
            yvara "No. I rarely do, in my own building."
            narrator "A pause."
            yvara "But you are not in your own building."
            menu:
                "I act the same in either case.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    narrator "She studies you for a moment."
                    yvara "I know."
                    narrator "She says it quietly, as though she has known it for longer than today."
                "Habit.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 2
                    yvara "Yes. I thought it might be."
                    narrator "She seems to respect the honesty more than a larger answer would have earned."
        "You would have handled it.":
            $ yvara_devotion += 2
            $ yvara_affection += 3
            yvara "Yes. But more slowly."
            narrator "She says it without false modesty — an assessment."
            yvara "It matters, sometimes, not to be the only person in the room who acts."
            menu:
                "I have been in enough rooms like this.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 1
                    yvara "I thought as much."
                    narrator "She tilts her head slightly, as though confirming something she had suspected."
                "Someone had to.":
                    $ yvara_affection += 2
                    yvara "..."
                    narrator "She looks at you for a moment longer than necessary."
                    yvara "Yes. Someone did."
        "I do not leave things unresolved.":
            $ yvara_dominion += 2
            $ yvara_affection += 3
            yvara "No. I have noticed that."
            narrator "She crosses the room, begins straightening the shelves the student disturbed. She does not look at you while she speaks."
            yvara "There are people who act because they cannot stop themselves, and people who act because they have decided to."
            yvara "You are the second kind."
            menu:
                "Is there a difference?":
                    $ yvara_devotion += 1
                    $ yvara_affection += 1
                    yvara "A great one."
                    narrator "She says it as though she has thought about this before."
                "Does it matter?":
                    $ yvara_dominion += 1
                    $ yvara_affection += 1
                    yvara "To the student? No."
                    narrator "She sets a book back in its place."
                    yvara "To me? Yes."
    $ yvara_s3_talks_done = list(yvara_s3_talks_done) + ["s3_t3"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_10
    jump yvara_visit_menu

# ── Stage 3 remark router ─────────────────────────────────────────────────────
label yvara_s3_remark_router:
    $ _total_days = calculate_total_days()
    if "s3_r1" not in yvara_s3_remarks_done:
        jump yvara_s3_remark_1
    elif "s3_r2" not in yvara_s3_remarks_done:
        jump yvara_s3_remark_2
    else:
        yvara "You have said everything worth saying for now."
        jump yvara_visit_menu

# ── Stage 3 Remark 1: Different ──────────────────────────────────────────────
label yvara_s3_remark_1:
    menu:
        "You seem less guarded than when I first came here.":
            narrator "She stops what she is doing."
            yvara "..."
            narrator "For a moment she seems to be preparing a denial. Then she doesn't."
            yvara "I suppose I am."
            menu:
                "It suits you.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 3
                    narrator "She looks at you for a moment with something she does not name."
                    yvara "That is either a compliment or an observation."
                    yvara "I find I do not particularly mind which."
                "What changed?":
                    $ yvara_affection += 3
                    narrator "A long pause."
                    yvara "The circumstances."
                    narrator "She says it without elaborating. But she holds your gaze a moment longer than she needs to."
        "You smile more than you used to.":
            yvara "I was not aware I did."
            narrator "A pause. She seems to take a brief internal inventory."
            yvara "...I suppose I do."
            menu:
                "It is not a complaint.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    narrator "She looks at you almost warily, then decides something."
                    yvara "No. I did not think it was."
                "What changed?":
                    $ yvara_affection += 3
                    $ yvara_devotion += 1
                    narrator "She considers the question with the same attention she gives difficult texts."
                    yvara "I am not entirely sure."
                    narrator "She says it like that is itself interesting to her."
    $ yvara_s3_remarks_done = list(yvara_s3_remarks_done) + ["s3_r1"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_11
    jump yvara_visit_menu

# ── Stage 3 Remark 2: How Long ───────────────────────────────────────────────
label yvara_s3_remark_2:
    narrator "She says it in the middle of something else entirely, without looking up."
    menu:
        "Remark that you hope she has let more people in since.":
            yvara "It has been... some time since I allowed anyone close enough to matter."
            narrator "A pause. She continues reading, or pretends to."
            menu:
                "That takes something to say.":
                    $ yvara_devotion += 3
                    $ yvara_affection += 3
                    narrator "She is quiet for a moment."
                    yvara "It takes less than I expected."
                    narrator "She does not look up. But something in the set of her shoulders is different."
                "I am glad you said it.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 3
                    narrator "She goes still."
                    yvara "..."
                    yvara "So am I."
                    narrator "Said very quietly. She moves on immediately. But she meant it."
        "Say nothing. Let it sit.":
            yvara "It has been... some time since I allowed anyone close enough to matter."
            narrator "The silence between you holds the sentence."
            narrator "She does not fill it. Neither do you. After a moment she turns a page — slowly, like someone who is not really reading."
            menu:
                "Meet her eyes when she finally looks up.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 3
                    narrator "She looks up eventually. When she does, whatever she was expecting to find in your expression, she seems to find something different."
                    yvara "You are unexpectedly patient."
                    narrator "It is not quite a compliment. It is not quite an observation. It is both."
                "Look away first.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 2
                    narrator "You look away. She notices."
                    yvara "..."
                    narrator "A moment later, she sets down her book entirely."
    $ yvara_s3_remarks_done = list(yvara_s3_remarks_done) + ["s3_r2"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_12
    jump yvara_visit_menu

# ── Stage 3 Gate Scene: After the Tour ───────────────────────────────────────
label yvara_s3_gate_scene:
    $ yvara_s3_gate_ready = False
    $ yvara_affection = max(yvara_affection, 51)
    $ yvara_recalculate_stage()
    $ _cg_before = "images/yvara/cg_after_tour_before.png" if renpy.loadable("images/yvara/cg_after_tour_before.png") else None
    if not _cg_before and renpy.loadable("images/yvara/library.png"):
        $ _cg_before = "images/yvara/library.png"
    $ _title = (getattr(store, "player_title", "") or "").strip().lower()
    $ _cg_hands = "images/yvara/cg_after_tour_hands_lady.png" if _title == "lady" else "images/yvara/cg_after_tour_hands_lord.png"
    if not renpy.loadable(_cg_hands):
        if _title == "lady" and renpy.loadable("images/yvara/handslady.png"):
            $ _cg_hands = "images/yvara/handslady.png"
        elif _title != "lady" and renpy.loadable("images/yvara/handslord.png"):
            $ _cg_hands = "images/yvara/handslord.png"
        else:
            $ _cg_hands = None
    $ _cg_after = "images/yvara/cg_after_tour_after.png" if renpy.loadable("images/yvara/cg_after_tour_after.png") else None
    if not _cg_after and renpy.loadable("images/yvara/cg_after_tour.png"):
        $ _cg_after = "images/yvara/cg_after_tour.png"
    if _cg_before:
        scene expression _cg_before
        window hide
        pause
        window show
    narrator "The visit begins on a pretext that neither of you bothers to make convincing."
    narrator "The building is empty. The last class ended an hour ago. She has left the lamp burning."
    if yvara_is_dominion_route():
        jump yvara_s3_gate_dominion
    else:
        jump yvara_s3_gate_devotion

label yvara_s3_gate_devotion:
    narrator "She is in the library — the back room, where the personal collection lives and no student ever goes."
    narrator "She is less armored than usual. Not because she is unguarded, but because she has stopped performing the guard."
    narrator "At some point the conversation runs out of neutral territory."
    narrator "The distance between you has closed — not suddenly, but incrementally, over the last half-hour — and neither of you has remarked on it."
    if _cg_hands:
        window hide
        scene expression _cg_hands
        pause
        window show
    narrator "For a moment, words seem less important than the space between your hands."
    yvara "I should..."
    narrator "She does not finish the sentence."
    narrator "Your hands are close. Not touching. The space between them has the particular quality of something about to change."
    if _cg_after:
        window hide
        scene expression _cg_after
        pause
        window show
    narrator "She does not move away."
    narrator "Neither do you."
    narrator "The moment stretches long enough that it becomes its own kind of answer."
    yvara "..."
    narrator "When you finally step apart, neither of you attempts to reduce the moment into language."
    narrator "When you finally leave, the walk back feels different. Something was crossed tonight that neither of you will name for a while."
    window hide
    pause
    window show
    jump yvara_s3_gate_end

label yvara_s3_gate_dominion:
    narrator "She shows you the records. She is precise, professional — but she is very aware of where you are in the room."
    narrator "At one point she reaches past you for a ledger on the shelf behind you. She does not step back afterward."
    if _cg_hands:
        window hide
        scene expression _cg_hands
        pause
        window show
    narrator "For a moment, words seem less important than the space between your hands."
    narrator "You reach out — deliberately, watching her — and adjust the clasp on her collar. It had come loose."
    narrator "She lets you."
    if _cg_after:
        window hide
        scene expression _cg_after
        pause
        window show
    yvara "You are testing something."
    narrator "She says it without stepping back. There is tension in her, but no retreat."
    menu:
        "I am.":
            $ yvara_dominion += 2
            $ yvara_affection += 1
            yvara "..."
            yvara "And if I asked you to stop?"
            menu:
                "Then I would stop.":
                    $ yvara_affection += 2
                    narrator "A long silence. She holds your gaze."
                    narrator "She measures the answer, then gives a near-imperceptible nod."
                    narrator "She does not ask you to stop."
                "You are not going to.":
                    $ yvara_dominion += 1
                    narrator "The silence that follows is the longest of the evening."
                    narrator "Her jaw sets for a moment, then eases."
                    narrator "She does not ask you to stop."
        "Only what you will allow.":
            $ yvara_devotion += 1
            $ yvara_affection += 2
            yvara "..."
            narrator "She seems to recalibrate something."
            yvara "That is a more careful answer than I expected."
            narrator "She does not move away."
    narrator "By the time the distance between you reasserts itself, it no longer feels like the same distance."
    narrator "When you leave, the dynamic is not softer — only clearer. Something has settled into place between you."
    window hide
    pause
    window show
    jump yvara_s3_gate_end

label yvara_s3_gate_end:
    $ _academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else "images/event_bg.png")
    $ _yvara_bust = "images/yvara/yvara_formal_neutral.png" if renpy.loadable("images/yvara/yvara_formal_neutral.png") else None
    scene expression _academy_bg at yvara_bg_blur
    show black as yvara_bg_dim:
        alpha 0.35
    if _yvara_bust:
        show expression _yvara_bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    jump yvara_visit_menu

label yvara_visit_after_hours:
    $ yvara_s3_gate_fired = True
    $ _academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else "images/event_bg.png")
    scene expression _academy_bg
    narrator "You return later than usual, when the halls have emptied and the day's noise has finally thinned into silence."
    narrator "Most of the Academy is dark. One room is not."
    narrator "She knew you would understand what after hours meant."
    jump yvara_s3_gate_scene

# ── Off-Camera Mechanic A: The Good Word ─────────────────────────────────────
label yvara_good_word:
    $ _total_days = calculate_total_days()
    narrator "You arrange for a worker to spend the day at the Academy — extra tutoring, on your recommendation."
    narrator "While there, they talk about what it is like to work for you. It is what workers do."
    narrator "Yvara, who has spent years hearing people complain about their employers, finds herself listening differently."
    $ yvara_good_word_count += 1
    $ yvara_good_word_last_day = _total_days
    $ yvara_devotion += 3
    $ yvara_affection += 1
    if yvara_good_word_count == 1:
        narrator "The next time you visit, she mentions it in passing."
        yvara "Your worker spoke of you. Favourably."
        narrator "She moves on immediately."
    elif yvara_good_word_count == 3:
        narrator "On your next visit, she is writing something when you arrive. She pauses."
        yvara "They all say the same things."
        narrator "A beat."
        yvara "I find that... notable."
    elif yvara_good_word_count >= 5 and not yvara_good_word_peak:
        $ yvara_good_word_peak = True
        $ yvara_devotion += 5
        narrator "One of your workers mentions, without being asked, that Yvara sought them out — asked questions about you."
        narrator "She did not tell you this. She may not intend to."
        narrator "But you know."
    else:
        narrator "She does not mention it at the next visit. But something is slightly different when she looks at you."
    jump yvara_visit_menu

# ── Off-Camera Mechanic B: The Observed Lesson ───────────────────────────────
label yvara_observed_lesson:
    $ _total_days = calculate_total_days()
    if money < 200:
        yvara "The consultation fee is two hundred coins. Come back when you can meet it."
        jump yvara_visit_menu
    $ money -= 200
    narrator "You have mentioned a worker who requires firmer handling. As an educator, you ask her to come and observe — purely as a professional consultation. She agrees."
    narrator "She arrives at your establishment at the arranged hour. She takes a seat at the back and opens her notebook."
    narrator "She watches what you do. She takes notes. She says nothing during the session."
    $ yvara_observed_sessions += 1
    $ yvara_observed_last_day = _total_days
    $ yvara_dominion += 4
    if yvara_observed_sessions == 1:
        narrator "Afterward, she sends written notes to the Academy. The language is clinical, precise."
        narrator "It is also, word for word, the language you used during the session."
    elif yvara_observed_sessions == 3:
        narrator "On your next visit to the Academy, she corrects a student in the corridor with the same phrasing you used."
        narrator "She stops herself mid-sentence. Says nothing."
    elif yvara_observed_sessions == 5:
        narrator "During a normal exchange at the Academy, she starts to say something — and stops."
        yvara "Yes, my—"
        narrator "She completes the sentence differently. Her expression closes immediately."
    elif yvara_observed_sessions >= 6 and not yvara_lesson_absorbed:
        $ yvara_lesson_absorbed = True
        $ yvara_dominion += 6
        yvara "I believe the consultations are no longer necessary."
        narrator "When you ask why:"
        yvara "I believe I have absorbed sufficient... methodology."
        narrator "The pause before the last word is long."
    jump yvara_visit_menu

# ── Stage 4 talk router ───────────────────────────────────────────────────────
label yvara_s4_talk_router:
    if "s4_t1" not in yvara_s4_talks_done:
        jump yvara_s4_talk_1
    elif "s4_t2" not in yvara_s4_talks_done:
        jump yvara_s4_talk_2
    elif "s4_t3" not in yvara_s4_talks_done:
        jump yvara_s4_talk_3
    else:
        jump yvara_talk_generic

# ── Stage 4 Talk 1: The Frame ────────────────────────────────────────────────
label yvara_s4_talk_1:
    $ _total_days = calculate_total_days()
    narrator "She is working when you arrive — or performing the act of working. The distinction has become readable."
    narrator "An open ledger sits at the corner of her desk, weighted down by two unpaid invoices."
    yvara "The Academy is proving more expensive to preserve than most people imagine."
    narrator "She sets down her pen before you have said anything."
    yvara "I have been thinking about how to classify what has been happening."
    narrator "She says it with the composure of someone who has been rehearsing the opening."
    yvara "It does not fit cleanly into any existing category."
    menu:
        "Does it need to?":
            $ yvara_devotion += 3
            $ yvara_affection += 6
            narrator "A pause. She seems to have prepared for several answers. This one was not among them."
            yvara "..."
            yvara "No. I suppose it does not."
            narrator "She picks up her pen again. Does not write anything."
            menu:
                "Then let it be what it is.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 4
                    narrator "She looks at you for a long moment. Something in her posture shifts — not a decision, but the beginning of one."
                    yvara "You make that sound straightforward."
                    yvara "You are aware that it is not."
                "I will wait until you find the right word.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 3
                    yvara "That could take some time."
                    narrator "She says it like a warning. But she does not look displeased."
        "I would be interested in what category you settled on.":
            $ yvara_dominion += 2
            $ yvara_affection += 5
            narrator "She looks at you steadily."
            yvara "I have not settled on one. That is rather the problem."
            menu:
                "The problem, or the answer?":
                    $ yvara_dominion += 2
                    $ yvara_affection += 4
                    narrator "A beat. She seems caught between amusement and something more cautious."
                    yvara "You are not helpful."
                    narrator "She says it without actual complaint."
                "What are the candidates?":
                    $ yvara_affection += 3
                    yvara "I have not made that list public."
                    narrator "She turns back to her papers. There is color at the edge of her composure that was not there before."
        "You do not have to classify it.":
            $ yvara_affection += 4
            narrator "She looks at you."
            yvara "I find that I need to understand things before I can proceed with them."
            yvara "It is a significant personal limitation."
            menu:
                "It is a significant personal strength.":
                    $ yvara_devotion += 3
                    $ yvara_affection += 4
                    narrator "Something in her expression does something it does not usually do."
                    yvara "..."
                    yvara "Thank you."
                    narrator "Brief. Direct. Genuine."
                "And yet here you are. Proceeding.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 3
                    yvara "..."
                    yvara "Yes. Apparently."
                    narrator "She does not sound displeased about it."
    if not yvara_s4_finance_unlocked:
        narrator "When you leave, the ledger is still open on the desk. For the first time, she has let you see the strain plainly."
        $ yvara_s4_finance_unlocked = True
    $ yvara_s4_talks_done = list(yvara_s4_talks_done) + ["s4_t1"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_13
    jump yvara_visit_menu

# ── Stage 4 Talk 2: The Limit ────────────────────────────────────────────────
label yvara_s4_talk_2:
    $ _total_days = calculate_total_days()
    narrator "She is standing at the window when you arrive — facing it, not looking out of it."
    narrator "The ledger from yesterday is closed now, but not put away. It rests on the sill beside her like an argument deferred."
    narrator "She turns when she hears you. Something is already decided in her expression."
    yvara "I have been considering how to manage this appropriately."
    narrator "A pause."
    yvara "I think it would be sensible to establish some clarity about what this is and is not."
    menu:
        "I am listening.":
            $ yvara_devotion += 2
            $ yvara_affection += 5
            narrator "She seems briefly wrong-footed by the absence of pushback."
            yvara "I am... not certain I have the full argument assembled yet."
            narrator "She says it with the precision of someone accustomed to knowing exactly what they think."
            yvara "This is unusual for me."
            menu:
                "Take your time.":
                    $ yvara_devotion += 3
                    $ yvara_affection += 5
                    narrator "A long pause. She looks at you with an expression she does not immediately put away."
                    yvara "You are consistently not what I expect."
                    yvara "I find that I am not sure what to do with that."
                "I think you have the argument. You are reconsidering whether to make it.":
                    $ yvara_dominion += 2
                    $ yvara_affection += 4
                    narrator "The pause is longer."
                    yvara "..."
                    yvara "That is accurate."
                    narrator "She turns back toward the window. Then does not."
        "What clarity were you looking for?":
            $ yvara_dominion += 2
            $ yvara_affection += 4
            yvara "I was going to say that this should remain..."
            narrator "She does not finish the sentence."
            yvara "It is a reasonable position."
            menu:
                "Tell me the position.":
                    $ yvara_dominion += 2
                    $ yvara_affection += 3
                    narrator "She meets your eyes."
                    yvara "I was going to say that it should remain uncomplicated."
                    yvara "I am no longer certain that is what I want."
                    narrator "She says it like a confession extracted against her better judgment."
                "Then say something unreasonable instead.":
                    $ yvara_affection += 5
                    $ yvara_devotion += 1
                    narrator "A beat. Then something close to a laugh — not quite, but in that direction."
                    yvara "You are very difficult."
                    narrator "She says it without the slightest indication she minds."
        "Then perhaps we should not manage it.":
            $ yvara_dominion += 3
            $ yvara_affection += 4
            narrator "She looks at you. The rehearsed opening she had prepared becomes visibly less available to her."
            yvara "That is a dangerous position."
            menu:
                "I know. I hold it anyway.":
                    $ yvara_dominion += 2
                    $ yvara_affection += 4
                    narrator "A long silence. She holds your gaze with the specific composure of someone not retreating."
                    yvara "..."
                    yvara "I see."
                    narrator "She turns back to her desk. Picks up a book. Sets it down again."
                "Then tell me the danger.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 3
                    yvara "I think you already know."
                    narrator "She says it quietly. She does not look away."
    $ yvara_s4_talks_done = list(yvara_s4_talks_done) + ["s4_t2"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_14
    jump yvara_visit_menu

# ── Stage 4 Talk 3: Before the Rain ─────────────────────────────────────────
label yvara_s4_talk_3:
    $ _total_days = calculate_total_days()
    narrator "The sky outside the office windows has the particular quality of a sky that has made up its mind."
    narrator "She is at her desk. The lamp is already lit, though it is not yet evening."
    narrator "You came without a particular reason. She does not ask for one."
    yvara "It is going to rain."
    narrator "It is an observation about the weather. It is also not."
    menu:
        "It has been building for a while.":
            $ yvara_devotion += 3
            $ yvara_affection += 6
            narrator "She looks up from her papers."
            yvara "Yes."
            narrator "A pause. The thunder is still distant."
            yvara "I have noticed."
            narrator "She says it like an admission she had not meant to make aloud."
            menu:
                "So have I.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 5
                    narrator "The silence that follows is not uncomfortable. It is the opposite."
                    narrator "Outside, the first rain comes."
                    yvara "..."
                    yvara "I suppose we will have to wait it out."
                    narrator "She says it without looking toward the door."
                "Some things are better once the storm breaks.":
                    $ yvara_affection += 4
                    narrator "She looks at you for a long moment."
                    yvara "That depends on what the storm was holding back."
                    narrator "The rain begins."
        "Better for it to break than to wait.":
            $ yvara_dominion += 3
            $ yvara_affection += 5
            narrator "She sets her pen down. Looks at you."
            yvara "You are speaking about the weather."
            menu:
                "Among other things.":
                    $ yvara_dominion += 2
                    $ yvara_affection += 4
                    narrator "A silence. The lamp flickers once."
                    yvara "..."
                    narrator "She does not contradict that."
                "Exclusively about the weather.":
                    $ yvara_affection += 2
                    narrator "She looks at you for a moment, and then a corner of her expression shifts."
                    yvara "Of course."
                    narrator "She does not believe you. She does not seem to mind."
        "Should I go? Before it starts.":
            $ yvara_affection += 3
            narrator "She glances at the window. Then at you."
            yvara "..."
            yvara "If you like."
            narrator "A pause."
            yvara "Though the roads will be difficult once it begins."
            menu:
                "Then I will stay until it passes.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 5
                    narrator "She nods. Returns to her work. But she does not say anything further about the roads."
                "It is not far.":
                    $ yvara_affection += 2
                    yvara "No."
                    narrator "She agrees too quickly. A small thing. She does not pursue it."
    narrator "The rain arrives in full."
    narrator "The roads outside close off, one by one, in the way roads do when the weather has its own opinion about where people should be."
    narrator "Neither of you mentions it."
    $ yvara_s4_talks_done = list(yvara_s4_talks_done) + ["s4_t3"]
    $ yvara_last_talk_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_15
    jump yvara_visit_menu

# ── Stage 4 remark router ─────────────────────────────────────────────────────
label yvara_s4_remark_router:
    $ _total_days = calculate_total_days()
    if "s4_r1" not in yvara_s4_remarks_done:
        jump yvara_s4_remark_1
    elif "s4_r2" not in yvara_s4_remarks_done:
        jump yvara_s4_remark_2
    else:
        yvara "You have already said everything worth saying for now."
        jump yvara_visit_menu

# ── Stage 4 Remark 1: The Tell ────────────────────────────────────────────────
label yvara_s4_remark_1:
    $ _total_days = calculate_total_days()
    narrator "You notice something she does — a small thing. The way she keeps her pen in her hand when she has stopped writing. The way her expression holds an extra half-second before it reassembles."
    menu:
        "You do that when you are thinking about something you do not want to say.":
            $ yvara_devotion += 3
            $ yvara_affection += 5
            narrator "She looks at you."
            yvara "..."
            yvara "I am aware that I do that."
            narrator "A pause."
            yvara "I was not aware that you had noticed."
            menu:
                "I pay attention.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 4
                    narrator "She looks at you for a long moment. Then she sets the pen down."
                    yvara "Yes. I can see that."
                    narrator "She says it quietly. As though it is something she is still deciding how to feel about."
                "Is it useful, knowing I have noticed?":
                    $ yvara_affection += 3
                    yvara "I am not sure yet."
                    narrator "She is not being evasive. She genuinely does not know."
        "You have been quiet since I arrived.":
            $ yvara_affection += 4
            narrator "She glances at you."
            yvara "I am often quiet."
            menu:
                "Not like this.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 4
                    narrator "A pause."
                    yvara "..."
                    yvara "No. Perhaps not like this."
                    narrator "She does not explain what the difference is. She does not have to."
                "It is a different kind of quiet.":
                    $ yvara_dominion += 1
                    $ yvara_affection += 3
                    yvara "You are very observant."
                    narrator "She says it without quite deciding how she feels about that."
    $ yvara_s4_remarks_done = list(yvara_s4_remarks_done) + ["s4_r1"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_16
    jump yvara_visit_menu

# ── Stage 4 Remark 2: The Implication ────────────────────────────────────────
label yvara_s4_remark_2:
    $ _total_days = calculate_total_days()
    narrator "The conversation has been ordinary. Then it isn't."
    menu:
        "The Academy will do well. Because you are here.":
            $ yvara_devotion += 3
            $ yvara_affection += 5
            narrator "She looks up."
            yvara "I... thank you."
            narrator "Brief. Then she glances away, and then back."
            yvara "That was not what I expected you to say."
            menu:
                "What were you expecting?":
                    $ yvara_devotion += 1
                    $ yvara_affection += 3
                    yvara "Something about the curriculum. Or the enrollment figures."
                    narrator "A pause."
                    yvara "Not that."
                    narrator "She says 'not that' the way someone says something that has not been said to them enough."
                "It is simply true.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 4
                    narrator "She holds your gaze."
                    yvara "..."
                    yvara "Yes. I suppose it is."
                    narrator "She says it like someone discovering they can accept something they could not, before."
        "There is something about this room when you are in it.":
            $ yvara_dominion += 1
            $ yvara_affection += 5
            narrator "She goes still."
            yvara "That is an unusual observation."
            menu:
                "An accurate one.":
                    $ yvara_dominion += 2
                    $ yvara_affection += 4
                    narrator "She holds your gaze with the specific steadiness of someone not backing down and not sure they want to."
                    yvara "You say things like that very calmly."
                    yvara "I find it difficult to respond to."
                "I have been trying to find the right words for a while.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 4
                    narrator "Something in her expression does something quiet."
                    yvara "..."
                    yvara "I am glad you found them."
                    narrator "She says it softly. It surprises her that she does."
    $ yvara_s4_remarks_done = list(yvara_s4_remarks_done) + ["s4_r2"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_17
    jump yvara_visit_menu

# ── Stage 4 Finance: Donate money ─────────────────────────────────────────────
label yvara_s4_donate_money:
    $ _tier_two_unlocked = yvara_s4_donation_highest_tier >= 1 or yvara_s4_donation_total >= 1
    $ _tier_three_unlocked = yvara_s4_donation_highest_tier >= 2 or yvara_s4_donation_total >= 2
    $ _tier_four_unlocked = yvara_s4_donation_highest_tier >= 3 or yvara_s4_donation_total >= 3
    menu:
        "Offer a modest donation (900 coins). She places her hand over your heart." if money >= 900:
            jump yvara_s4_donate_tier_1
        "Offer a modest donation (900 coins). She places her hand over your heart." if money < 900:
            narrator "You do not have enough coin for even a modest gesture."
            jump yvara_s4_donate_money
        "Offer meaningful support (2,100 coins). She kisses you." if _tier_two_unlocked and money >= 2100:
            jump yvara_s4_donate_tier_2
        "Offer meaningful support (2,100 coins). She kisses you." if _tier_two_unlocked and money < 2100:
            narrator "You cannot commit that much coin right now."
            jump yvara_s4_donate_money
        "Cover a serious expense (4,200 coins). She gives you a massage." if _tier_three_unlocked and money >= 4200:
            jump yvara_s4_donate_tier_3
        "Cover a serious expense (4,200 coins). She gives you a massage." if _tier_three_unlocked and money < 4200:
            narrator "That level of support is beyond what you can spare at the moment."
            jump yvara_s4_donate_money
        "Take the burden off her shoulders (5,400 coins). A massage with a happy ending." if _tier_four_unlocked and money >= 5400:
            jump yvara_s4_donate_tier_4
        "Take the burden off her shoulders (5,400 coins). A massage with a happy ending." if _tier_four_unlocked and money < 5400:
            narrator "You cannot spare enough coin to offer that kind of relief."
            jump yvara_s4_donate_money
        "Leave it be for now.":
            jump yvara_visit_menu

label yvara_s4_donate_tier_1:
    $ _total_days = calculate_total_days()
    $ money -= 900
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_donation_total += 1
    $ yvara_s4_donation_highest_tier = max(yvara_s4_donation_highest_tier, 1)
    $ yvara_devotion += 2
    $ yvara_affection += 2
    $ _emote = "images/yvara/yvara_formal_moved.png" if renpy.loadable("images/yvara/yvara_formal_moved.png") else "images/yvara/yvara_formal_neutral.png"
    if renpy.loadable(_emote):
        show expression _emote:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "You place a small purse beside the ledger and nudge it toward her."
    narrator "She looks at it, then at you."
    yvara "I did not ask you for this."
    narrator "You tell her it should cover the immediate nuisance: paper, lamp oil, one less compromise than she had planned to make this week."
    narrator "She says nothing. Then she steps closer, rests her hand on your chest — over your heart — and leaves it there a moment, as if feeling your pulse."
    yvara "Thank you."
    narrator "She says it quietly. When she withdraws her hand, the formal mask has slipped fractionally."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_18
    jump yvara_visit_menu

label yvara_s4_donate_tier_2:
    $ _total_days = calculate_total_days()
    $ money -= 2100
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_donation_total += 1
    $ yvara_s4_donation_highest_tier = max(yvara_s4_donation_highest_tier, 2)
    $ yvara_devotion += 3
    $ yvara_affection += 3
    $ _emote = "images/yvara/yvara_formal_flustered_light.png" if renpy.loadable("images/yvara/yvara_formal_flustered_light.png") else "images/yvara/yvara_formal_neutral.png"
    if renpy.loadable(_emote):
        show expression _emote:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "You set down enough coin to solve more than one immediate problem."
    narrator "She knows that at a glance. So do you."
    yvara "That is not a casual amount."
    narrator "You tell her the Academy matters, and that you would rather see the strain taken off her face than left there out of principle."
    yvara "You should not say things like that while handing me money."
    narrator "Her composure holds. Barely."
    narrator "When she reaches for the purse, her fingers brush yours and remain there for a second longer than either of you strictly needs. Then she steps in and kisses you."
    yvara "Thank you."
    narrator "This time she does not sound formal at all."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_19
    jump yvara_visit_menu

label yvara_s4_donate_tier_3:
    $ _total_days = calculate_total_days()
    $ money -= 4200
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_donation_total += 1
    $ yvara_s4_donation_highest_tier = 3
    $ yvara_devotion += 4
    $ yvara_affection += 4
    $ _emote = "images/yvara/yvara_formal_warm.png" if renpy.loadable("images/yvara/yvara_formal_warm.png") else "images/yvara/yvara_formal_neutral.png"
    if renpy.loadable(_emote):
        show expression _emote:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "You name the expense plainly and offer enough to erase it."
    narrator "For once she does not answer immediately."
    yvara "That is... not a donation. That is rescue."
    narrator "You tell her she can call it whatever lets her accept it."
    narrator "She looks at you for a long moment, caught between pride and relief."
    yvara "Sit down. I have spent years studying anatomy for the Amatory curriculum — pressure points, musculature. I am better at this than you might expect."
    narrator "She settles her hands on your shoulders and begins to work the tension out with the same precision she applies to everything else."
    yvara "You carry too much tension here."
    narrator "The contact is deliberate, close. When she finishes, her hands linger on your shoulders a moment before she withdraws."
    yvara "Thank you."
    narrator "This time she says it like a confession rather than etiquette."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_20
    jump yvara_visit_menu

label yvara_s4_donate_tier_4:
    $ _total_days = calculate_total_days()
    $ money -= 5400
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_donation_total += 1
    $ yvara_s4_donation_highest_tier = 4
    $ yvara_devotion += 5
    $ yvara_affection += 5
    $ _emote = "images/yvara/yvara_formal_yielding.png" if renpy.loadable("images/yvara/yvara_formal_yielding.png") else "images/yvara/yvara_formal_neutral.png"
    if renpy.loadable(_emote):
        show expression _emote:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "You place enough coin on the desk to remove the problem entirely, not just soften it."
    narrator "She does not touch it. She looks at you instead."
    yvara "Do you understand what you are doing?"
    narrator "You tell her that you do, and that you would rather see her breathe easier than watch her grind herself down out of principle."
    narrator "That lands harder than the money."
    narrator "She removes her glasses and sets them on the desk."
    yvara "Lie down."
    narrator "The massage begins at your shoulders and neck. It travels down your back. Her hands pause at the small of your back a moment before they continue."
    narrator "The rhythm changes. It is no longer only gratitude."
    narrator "When her hand finds what it is looking for, there is no question. Only a decision already made."
    narrator "Afterward, she washes her hands at the basin in the corner with the same composure she brings to her paperwork."
    yvara "That was not part of any arrangement."
    narrator "There is color in her cheeks and no real distance left in her eyes."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_21
    jump yvara_visit_menu

# ── Stage 4 Finance: Buy favors ───────────────────────────────────────────────
label yvara_s4_buy_favors:
    $ _tier_two_unlocked = yvara_s4_favor_highest_tier >= 1 or yvara_s4_favors_total >= 1
    $ _tier_three_unlocked = yvara_s4_favor_highest_tier >= 2 or yvara_s4_favors_total >= 2
    $ _tier_four_unlocked = yvara_s4_favor_highest_tier >= 3 or yvara_s4_favors_total >= 3
    menu:
        "Turn for me (900 coins). She stands and turns slowly for you." if money >= 900:
            jump yvara_s4_favor_turn
        "Turn for me (900 coins). She stands and turns slowly for you." if money < 900:
            narrator "You do not have enough coin to make even that bargain."
            jump yvara_s4_buy_favors
        "Strip down to lingerie (2,400 coins). She undresses until she is down to her underthings." if _tier_two_unlocked and money >= 2400:
            jump yvara_s4_favor_lingerie
        "Strip down to lingerie (2,400 coins). She undresses until she is down to her underthings." if _tier_two_unlocked and money < 2400:
            narrator "You cannot afford that particular indulgence right now."
            jump yvara_s4_buy_favors
        "Go topless for me (2,700 coins). She removes her top under your gaze." if _tier_three_unlocked and money >= 2700:
            jump yvara_s4_favor_topless
        "Go topless for me (2,700 coins). She removes her top under your gaze." if _tier_three_unlocked and money < 2700:
            narrator "You cannot afford to call in that kind of favor right now."
            jump yvara_s4_buy_favors
        "Striptease for me (4,500 coins). A dance with sexy moves, ending in full undress." if _tier_four_unlocked and money >= 4500:
            jump yvara_s4_favor_striptease
        "Striptease for me (4,500 coins). A dance with sexy moves, ending in full undress." if _tier_four_unlocked and money < 4500:
            narrator "You do not have enough coin to demand that much tonight."
            jump yvara_s4_buy_favors
        "Leave it there.":
            jump yvara_visit_menu

label yvara_s4_favor_turn:
    $ _total_days = calculate_total_days()
    $ money -= 900
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_favors_total += 1
    $ yvara_s4_favor_highest_tier = max(yvara_s4_favor_highest_tier, 1)
    $ yvara_dominion += 2
    $ yvara_affection += 1
    $ yvara_leverage_financial = True
    narrator "You slide the agreed coin across the desk and tell her to stand."
    narrator "She looks at the money, then at you."
    yvara "You are very calm when you say things like that."
    narrator "You tell her to turn for you."
    narrator "The silence stretches. Then she rises."
    $ _bust = "images/yvara/yvara_formal_back.png"
    if renpy.loadable(_bust):
        show expression _bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "She turns once, slowly, with the rigid grace of someone refusing to rush simply because you asked."
    yvara "There. Was that sufficient?"
    narrator "The question is dry. The heat beneath it is not."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_22
    jump yvara_visit_menu

label yvara_s4_favor_lingerie:
    $ _total_days = calculate_total_days()
    $ money -= 2400
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_favors_total += 1
    $ yvara_s4_favor_highest_tier = 2
    $ yvara_dominion += 3
    $ yvara_affection += 2
    $ yvara_leverage_financial = True
    narrator "You set down enough coin that refusing would require a kind of pride she is already tired of paying for."
    narrator "Then you tell her to strip down to her lingerie."
    yvara "That is... specific."
    narrator "You do not take the money back."
    narrator "After a silence long enough to matter, she steps away from the desk."
    narrator "She unfastens her formal layers with deliberate precision — the same care she applies to everything else."
    $ _bust = "images/yvara/yvara_formal_lingerie.png"
    if renpy.loadable(_bust):
        show expression _bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "When she is done, she stands before you in her underthings, neither rushing nor apologising."
    yvara "If you smirk, this ends."
    narrator "You do not. She notices."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_23
    jump yvara_visit_menu

label yvara_s4_favor_topless:
    $ _total_days = calculate_total_days()
    $ money -= 2700
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_favors_total += 1
    $ yvara_s4_favor_highest_tier = 3
    $ yvara_dominion += 4
    $ yvara_affection += 1
    $ yvara_leverage_financial = True
    narrator "You name the favor and let the amount speak for itself."
    yvara "My top."
    narrator "You hold her gaze."
    narrator "The pause that follows is sharp enough to cut on."
    narrator "Then, with the deliberate precision she applies to everything that matters, she removes it."
    $ _bust = "images/yvara/yvara_formal_topless.png"
    if renpy.loadable(_bust):
        show expression _bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "She stands before you, bare from the waist up, with the same controlled composure she brings to her desk."
    yvara "You should be very clear with yourself about what sort of person asks for this."
    narrator "She says it while remaining exactly where you told her to remain."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_24
    jump yvara_visit_menu

label yvara_s4_favor_striptease:
    $ _total_days = calculate_total_days()
    $ money -= 4500
    $ yvara_s4_finance_last_day = _total_days
    $ yvara_s4_favors_total += 1
    $ yvara_s4_favor_highest_tier = 4
    $ yvara_dominion += 5
    $ yvara_affection += 2
    $ yvara_leverage_financial = True
    narrator "You place enough coin on the desk that the air in the room changes before you even speak."
    narrator "Then you tell her to give you a striptease."
    yvara "You enjoy choosing the moment where a request becomes an insult."
    narrator "You do not deny it."
    narrator "She stands very still, furious for a second. Then she moves."
    narrator "It starts as a slow turn — a measured dance. Her hands trace the line of her collar, her waist. Each piece comes away with the same exacting care she brings to everything else."
    narrator "The moves are deliberate, almost austere. That only makes them harder to look away from."
    $ _bust = "images/yvara/yvara_formal_striptease.png"
    if renpy.loadable(_bust):
        show expression _bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    narrator "By the time the last layer is gone, the silence feels louder than any order you gave."
    yvara "Look quickly."
    narrator "She says it as if that could somehow restore the balance between you."
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_25
    jump yvara_visit_menu

# ── Stage 4 Gate Scene: The Storm ─────────────────────────────────────────────
label yvara_s4_gate_scene:
    $ yvara_affection = max(yvara_affection, 64)
    $ _title = (getattr(store, "player_title", "") or "").strip().lower()
    $ _cg_01 = "images/yvara/cg_storm_01_common.png" if renpy.loadable("images/yvara/cg_storm_01_common.png") else ("images/yvara/cg_storm.png" if renpy.loadable("images/yvara/cg_storm.png") else None)
    if _cg_01:
        scene expression _cg_01
        window hide
        pause
        window show
    narrator "The storm does not ask permission."
    narrator "One hour it was weather. The next it is something else — the kind that makes roads impassable and the distance between here and anywhere else academic."
    narrator "The Academy is empty. The last class ended before it started in earnest. The staff have gone."
    narrator "It is only the two of you and the sound of rain on the roof, which is a very particular kind of company."
    if yvara_is_dominion_route():
        jump yvara_s4_gate_dominion
    else:
        jump yvara_s4_gate_devotion

label yvara_s4_gate_devotion:
    $ _cg_02 = "images/yvara/cg_storm_02_lady.png" if _title == "lady" else "images/yvara/cg_storm_02_lord.png"
    $ _cg_02 = _cg_02 if renpy.loadable(_cg_02) else None
    $ _cg_02b = "images/yvara/cg_storm_02b_common.png" if renpy.loadable("images/yvara/cg_storm_02b_common.png") else None
    $ _cg_03 = "images/yvara/cg_storm_03_devotion_lady.png" if _title == "lady" else "images/yvara/cg_storm_03_devotion_lord.png"
    $ _cg_03 = _cg_03 if renpy.loadable(_cg_03) else None
    narrator "She has been reading — or pretending to. The book has not turned a page in twenty minutes."
    if yvara_s4_donation_total > 0:
        narrator "You have spent days making it easier for her to keep the Academy standing. She has spent those same days pretending that gratitude was the whole of what she felt."
    narrator "At some point the conversation runs out of neutral territory."
    narrator "Not dramatically. Not with any single thing that causes it. The careful distance has simply been there for a long time, and tonight, it runs out."
    yvara "I should not—"
    narrator "She does not finish the sentence."
    narrator "She does not move away."
    if _cg_02:
        window hide
        scene expression _cg_02
        pause
        window show
    narrator "When she kisses you it is not tentative. She has been thinking about it, clearly, and she has decided. The decision is in it."
    yvara "I should not have done that."
    menu:
        "You should do it again.":
            $ yvara_devotion += 3
            $ yvara_affection += 6
            narrator "She considers this. For a long moment."
            narrator "The lamp flickers. Outside, the rain is doing something serious."
            narrator "She does it again."
        "You should do whatever you want.":
            $ yvara_devotion += 2
            $ yvara_affection += 5
            narrator "Something in her expression changes — not surprise, but the resolution of a tension."
            yvara "..."
            yvara "That is the most dangerous thing anyone has said to me in some time."
            narrator "She does not back away."
    narrator "The storm grows louder. The Academy is closed around you. By the time either of you says anything coherent again, there is no practical sense in pretending you will spend the night apart."
    narrator "You end up in the same bed before the storm has spent half its force."
    if _cg_02b:
        window hide
        scene expression _cg_02b
        pause
        window show
    if _cg_03:
        window hide
        scene expression _cg_03
        pause
        window show
    narrator "Afterward, she is quiet in the specific way of someone who has done something they had thought about carefully and found it was exactly what they thought it would be."
    yvara "I am not sure what this is."
    narrator "She says it to the ceiling, or the rain, or some neutral middle distance."
    menu:
        "Neither am I.":
            $ yvara_affection += 3
            yvara "Good."
            narrator "She turns her head."
            yvara "I would distrust certainty at this stage."
        "It is what it is.":
            $ yvara_devotion += 1
            $ yvara_affection += 2
            yvara "..."
            yvara "Yes. I suppose it is."
            narrator "She says it like she is trying on something new."
    jump yvara_s4_gate_end

label yvara_s4_gate_dominion:
    $ _cg_02 = "images/yvara/cg_storm_02_lady.png" if _title == "lady" else "images/yvara/cg_storm_02_lord.png"
    $ _cg_02 = _cg_02 if renpy.loadable(_cg_02) else None
    $ _cg_02b = "images/yvara/cg_storm_02b_common.png" if renpy.loadable("images/yvara/cg_storm_02b_common.png") else None
    $ _cg_03 = "images/yvara/cg_storm_03_dominion_lady.png" if _title == "lady" else "images/yvara/cg_storm_03_dominion_lord.png"
    $ _cg_03 = _cg_03 if renpy.loadable(_cg_03) else None
    narrator "She has been professional all evening — which is to say that she has been performing the idea of professional, and the performance is visible to both of them."
    if yvara_s4_favors_total > 0:
        narrator "Small bargains have been accumulating between you for days. Each one left something unsettled in the room. Tonight there is nowhere for that unfinished tension to go except forward."
    narrator "At some point she stops."
    narrator "Not suddenly. Not with any announcement. She simply stops maintaining the distance, and what was behind it is the same thing that has been accumulating for weeks."
    narrator "You move. Not quickly. With the specific clarity of someone who has been patient long enough."
    yvara "This was not part of any arrangement."
    menu:
        "No. It is a new one.":
            $ yvara_dominion += 3
            $ yvara_affection += 5
            narrator "She holds your gaze."
            narrator "There is genuine resistance in her — not fear, not reluctance. Pride. The specific kind that knows what it is doing."
            narrator "And then, carefully, it yields."
            yvara "..."
            narrator "She does not ask you to stop. She does something more deliberate than that: she continues."
        "It is not an arrangement at all.":
            $ yvara_affection += 4
            $ yvara_dominion += 1
            narrator "A silence."
            yvara "Then what is it?"
            menu:
                "Something without a name yet.":
                    $ yvara_affection += 3
                    narrator "She considers this."
                    narrator "She decides she can work with that."
                "Ask me again when the storm has passed.":
                    $ yvara_dominion += 2
                    $ yvara_affection += 3
                    narrator "A beat."
                    yvara "..."
                    yvara "Yes. All right."
                    narrator "She says it like someone who has just decided to stop arguing about the map and simply walk."
    if _cg_02:
        window hide
        scene expression _cg_02
        pause
        window show
    narrator "The rain makes departure impossible and denial feel even more ridiculous than it already did."
    narrator "What begins standing and charged ends with the two of you in the same bed, the storm spending itself against the windows while she says nothing that sounds like regret."
    if _cg_02b:
        window hide
        scene expression _cg_02b
        pause
        window show
    if _cg_03:
        window hide
        scene expression _cg_03
        pause
        window show
    narrator "Afterward she is quieter than usual. Not broken — settled. The specific settledness of someone who has made a decision in full awareness of what it means."
    yvara "You will not make a point of this."
    narrator "It is not quite a question."
    menu:
        "No.":
            $ yvara_dominion += 1
            $ yvara_affection += 3
            yvara "Good."
            narrator "She says it simply. She is already herself again — just a different arrangement of it."
        "It does not need to be a point. It is simply true.":
            $ yvara_affection += 4
            narrator "She looks at you."
            yvara "..."
            yvara "Yes. I suppose it is."
    jump yvara_s4_gate_end

label yvara_s4_gate_end:
    $ yvara_recalculate_stage()
    $ _academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else "images/event_bg.png")
    $ _yvara_bust = "images/yvara/yvara_formal_neutral.png" if renpy.loadable("images/yvara/yvara_formal_neutral.png") else None
    scene expression _academy_bg at yvara_bg_blur
    show black as yvara_bg_dim:
        alpha 0.35
    if _yvara_bust:
        show expression _yvara_bust:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
    jump yvara_visit_menu

# ── Stage 4: The Morning After ────────────────────────────────────────────────
label yvara_s4_morning_after:
    narrator "She is already at her desk when you wake."
    narrator "Professional posture. Papers arranged. Tea made — there are two cups."
    narrator "She does not look up immediately. When she does, her expression is the composed one, fully assembled."
    yvara "I trust you slept adequately."
    narrator "A pause that lasts slightly too long to be nothing."
    menu:
        "I did.":
            $ yvara_affection += 3
            narrator "She hands you the second cup."
            narrator "Her fingers brush yours. Neither of you comments."
            yvara "Good."
            narrator "She returns to her papers. The distance between you is exactly the same as it has always been. It means something entirely different now."
        "Better than I expected.":
            $ yvara_devotion += 1
            $ yvara_affection += 3
            narrator "Something at the corner of her expression moves."
            yvara "The couch in the study is more comfortable than it appears."
            narrator "She hands you the tea. Her fingers brush yours. She does not comment on it."
        "You made tea.":
            $ yvara_affection += 4
            narrator "She looks at the cup she is holding out to you."
            yvara "I make tea every morning."
            narrator "A pause."
            yvara "There happened to be enough for two."
            narrator "She holds your gaze for one moment longer than necessary. Then returns to her work."
    $ yvara_affection += 0
    jump yvara_visit_menu

# ── Stage 4: Evening at the Academy (repeatable) ─────────────────────────────
label yvara_evening_academy:
    $ _total_days = calculate_total_days()
    $ yvara_evening_academy_last_day = _total_days
    if yvara_is_devotion_route():
        narrator "You come in the evening, when the last students have left and the building has the particular quiet of a place that has finished its work for the day."
        narrator "She is in the back — the library, or the study — and she hears you and does not call out to ask who it is."
        narrator "She already knows."
        yvara "You came."
        narrator "She says it as though she had been waiting without admitting she was waiting."
        menu:
            "I said I would.":
                $ yvara_devotion += 2
                $ yvara_affection += 3
                narrator "She nods once. Something settles in her expression."
                narrator "The evening passes the way evenings do now — talking, and then less talking, and then something that does not need words."
                yvara "You should not stay too late."
                narrator "She says it much later than she should have."
            "I could not stay away.":
                $ yvara_devotion += 1
                $ yvara_affection += 2
                narrator "A beat. She looks at you with an expression that has stopped trying to be neutral."
                yvara "..."
                yvara "No. I find I am not surprised by that."
                narrator "The evening is unhurried. That is the best thing about it."
    else:
        narrator "You come without announcement. You do not need to announce yourself anymore — that is something that has changed, quietly, without either of you marking it."
        narrator "She looks up when you come in and does not reach for her professional register."
        yvara "I was beginning to wonder."
        narrator "She says it without preamble."
        menu:
            "About what?":
                $ yvara_dominion += 1
                $ yvara_affection += 2
                yvara "Whether you would come this evening."
                narrator "She says it with the flat directness she uses when she has decided not to pretend about something."
                menu:
                    "Here I am.":
                        $ yvara_affection += 2
                        narrator "She looks at you."
                        yvara "Yes."
                        narrator "She says it like something she is glad about and is not quite ready to say she is glad about."
                    "And now that I have?":
                        $ yvara_dominion += 2
                        $ yvara_affection += 2
                        narrator "The corner of her expression shifts."
                        yvara "Now that you have."
                        narrator "She does not complete the sentence. She does not need to."
            "I was delayed.":
                $ yvara_affection += 2
                yvara "It does not matter."
                narrator "She says it quickly. Too quickly."
                yvara "You are here now."
                narrator "She turns back toward the back room. She does not ask if you are following. She knows you are."
    $ yvara_affection += 2
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_26
    jump yvara_visit_menu

# ── Stage 1 remark router ─────────────────────────────────────────────────────
label yvara_s1_remark_router:
    $ _total_days = calculate_total_days()
    if "s1_r1" not in yvara_s1_remarks_done:
        jump yvara_s1_remark_1
    elif "s1_r2" not in yvara_s1_remarks_done:
        jump yvara_s1_remark_2
    elif "s1_r3" not in yvara_s1_remarks_done:
        jump yvara_s1_remark_3
    else:
        yvara "You have made your point."
        jump yvara_visit_menu

# ── Stage 1 Remark 1 ──────────────────────────────────────────────────────────
label yvara_s1_remark_1:
    narrator "You look around the room before speaking."
    menu:
        "The library is better stocked than I expected for a place this size.":
            yvara "Most people do not notice the library at all."
            yvara "I spent six years building that collection. Every volume was chosen deliberately."
            menu:
                "It shows.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    yvara "Thank you."
                    narrator "Brief, direct. Genuine."
                "What is the rarest piece in there?":
                    $ yvara_devotion += 1
                    $ yvara_affection += 3
                    yvara "A commentary on the original Principles of Order, pre-reform edition."
                    yvara "It contradicts three things taught in every academic institution in this region."
                    yvara "I find that useful."
        "Your selection process seems unusually rigorous for a place this size.":
            yvara "Size has nothing to do with it."
            yvara "A small institution with high standards produces more than a large one without them."
            menu:
                "Agreed.":
                    $ yvara_devotion += 1
                    $ yvara_affection += 1
                    yvara "Good."
                "How many do you turn away?":
                    $ yvara_dominion += 1
                    $ yvara_affection += 2
                    yvara "Most of them."
                    narrator "She says it without satisfaction and without apology."
    $ yvara_s1_remarks_done = list(yvara_s1_remarks_done) + ["s1_r1"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_27
    jump yvara_visit_menu

# ── Stage 1 Remark 2 ──────────────────────────────────────────────────────────
label yvara_s1_remark_2:
    menu:
        "Your students seem to respect you. Not just obey you.":
            narrator "A short pause."
            yvara "There is a difference."
            menu:
                "Most people in authority do not know the difference.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    yvara "No. They do not."
                    narrator "Something shifts slightly in her posture. An acknowledgment."
                "Which matters more to you?":
                    $ yvara_affection += 3
                    yvara "Respect. Obedience without it is fragile."
                    yvara "It breaks the moment you look away."
                    narrator "She glances at you, then away."
        "You seem more at ease here than most people I have met in positions like this.":
            yvara "This place was built around what I believe. Most institutions are built around something else and then ask people to believe it."
            menu:
                "That is rare.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    yvara "It required a great deal of argument."
                    narrator "Almost dry. The closest thing to humor you have heard from her."
                "What did you have to sacrifice for it?":
                    $ yvara_affection += 3
                    $ yvara_devotion += 1
                    yvara "..."
                    yvara "Time. Certain kinds of ease. A few relationships."
                    yvara "I do not regret any of it."
    $ yvara_s1_remarks_done = list(yvara_s1_remarks_done) + ["s1_r2"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_28
    jump yvara_visit_menu

# ── Stage 1 Remark 3 ──────────────────────────────────────────────────────────
label yvara_s1_remark_3:
    menu:
        "Ask if she ever gets tired of it.":
            yvara "..."
            yvara "Some mornings. Then a student understands something for the first time and I forget I was tired."
            narrator "She says it flatly, but it lands like a confession."
            menu:
                "That is enough to keep going.":
                    $ yvara_devotion += 2
                    $ yvara_affection += 2
                    yvara "Yes. It is."
                "Do you ever wish it were enough?":
                    $ yvara_affection += 4
                    narrator "She looks at you for a moment longer than usual."
                    yvara "That is a strange question."
                    yvara "...Yes. Sometimes."
        "Tell her the Academy has changed since the first time you visited.":
            yvara "Has it, or have you?"
            menu:
                "Both, probably.":
                    $ yvara_affection += 3
                    $ yvara_devotion += 1
                    yvara "That is an honest answer."
                "I am not sure.":
                    $ yvara_affection += 2
                    $ yvara_dominion += 1
                    yvara "Neither am I."
                    narrator "It is the first thing she has said that sounds uncertain."
    $ yvara_s1_remarks_done = list(yvara_s1_remarks_done) + ["s1_r3"]
    $ yvara_last_question_total_days = _total_days
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_29
    jump yvara_visit_menu

# ── Stage gate check ──────────────────────────────────────────────────────────
label yvara_check_stage_advance:
    if yvara_stage == 1 and len(yvara_s1_talks_done) >= 3 and yvara_affection >= 16:
        $ yvara_recalculate_stage()
        narrator "Something has shifted between you. Small, barely visible—but real."
        yvara "You keep coming back."
        yvara "I am beginning to think that is intentional."
    elif yvara_stage == 2 and len(yvara_s2_talks_done) >= 3 and yvara_affection >= 31:
        $ yvara_recalculate_stage()
        narrator "She sets down her pen. Not because she has finished—she rarely finishes—but deliberately. She looks at you."
        yvara "Whatever this is."
        narrator "She does not complete the sentence. She does not seem to need to."
        yvara "I think we should keep doing it."
        narrator "It is not a question. It might be the most direct thing she has said to you."
    elif not yvara_s3_gate_fired and not yvara_s3_gate_ready and len(yvara_s3_talks_done) >= 3 and yvara_affection >= 51:
        $ yvara_s3_gate_ready = True
        $ yvara_s3_gate_ready_total_days = calculate_total_days()
        narrator "You start to leave. Before you reach the door, she speaks."
        yvara "If you come by tomorrow..."
        narrator "She stops, as though reconsidering the sentence while already inside it."
        yvara "Come after hours."
        narrator "It is not phrased like an invitation. It lands like one anyway."
    elif not yvara_s4_gate_fired and len(yvara_s4_talks_done) >= 3 and yvara_affection >= 64:
        $ yvara_s4_gate_fired = True
        jump yvara_s4_gate_scene
    return

label yvara_gift:
    $ _total_days = calculate_total_days()
    $ _gift_result = renpy.call_screen("yvara_gift_picker")
    $ _gift_action = _gift_result[0] if isinstance(_gift_result, (list, tuple)) and len(_gift_result) >= 1 else "close"
    $ _gid = _gift_result[1] if isinstance(_gift_result, (list, tuple)) and len(_gift_result) >= 2 else None
    if _gift_action != "gift":
        jump yvara_visit_menu
    $ _valid_gift_ids = [g[0] for g in yvara_get_giftable_items()]
    if _gid is None or _gid not in _valid_gift_ids:
        jump yvara_visit_menu
    $ _removed = yvara_remove_gift_item(_gid, 1)
    if not _removed:
        narrator "You cannot find that gift in your accessible storage right now."
        jump yvara_visit_menu
    $ store.manager_inventory = list(getattr(store, "manager_inventory", manager_inventory))
    $ _gdata = YVARA_GIFTS.get(_gid, (1, 0, 1, "yvara_gift_default"))
    $ yvara_devotion += _gdata[0]
    $ yvara_dominion += _gdata[1]
    $ yvara_affection += _gdata[2]
    $ yvara_last_gift_total_days = _total_days
    if _gdata[2] >= 0:
        $ yvara_gifts_given += 1
        if yvara_stage == 2:
            $ yvara_s2_gifts_given += 1
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_30
    jump expression _gdata[3]

label yvara_gift_rare_book:
    yvara "..."
    yvara "Where did you find this?"
    narrator "She takes it carefully, opens it to a middle page, and reads a sentence in silence."
    yvara "I searched for this text for two years. I thought the only copy was in the capital."
    yvara "How did you know I wanted it?"
    narrator "She seems genuinely moved."
    jump yvara_visit_menu

label yvara_gift_fine_wine:
    yvara "A decent vintage."
    narrator "She holds the bottle at eye level for a moment, reading the label."
    yvara "Southern hills. Good year."
    yvara "You have some taste. I had not expected that."
    narrator "She seems to like it, even if she keeps her tone controlled."
    jump yvara_visit_menu

label yvara_gift_herbal_tea:
    yvara "Tea."
    narrator "She is quiet for a moment."
    yvara "Mountain blend. I have not had this one in years."
    yvara "It is oddly... considerate."
    narrator "She sets it beside her papers without looking up again."
    narrator "The reaction is subtle, but warm."
    jump yvara_visit_menu

label yvara_gift_flowers:
    narrator "She takes the bouquet without speaking. Sets it on the desk."
    yvara "They suit the light in here, I suppose."
    narrator "She does not look at you, but the corner of her mouth moves."
    narrator "She seems pleased, though she does not quite admit it."
    jump yvara_visit_menu

label yvara_gift_chocolates:
    yvara "Sweets."
    yvara "You do not strike me as someone who gives sweets."
    yvara "...Thank you, all the same."
    narrator "A small but very real reaction."
    jump yvara_visit_menu

label yvara_gift_gem:
    yvara "This is worth real money."
    yvara "I do not collect stones, and I would not know what to do with it."
    yvara "I appreciate the gesture. The choice was... impersonal."
    narrator "She values the gesture, but it feels impersonal to her."
    jump yvara_visit_menu

label yvara_gift_elixir:
    yvara "..."
    narrator "She looks at the bottle. Looks at you. Sets it down slowly."
    yvara "Get out."
    yvara "Come back tomorrow and we will pretend this did not happen."
    narrator "That was far too soon."
    jump yvara_visit_menu

label yvara_gift_poem:
    narrator "She takes the paper. Reads it once. Reads it again."
    yvara "..."
    yvara "You wrote this."
    narrator "It is not a question. She folds it carefully and sets it between the pages of the book on her desk—not to put it aside, but to keep it."
    yvara "I will read it again later."
    narrator "She says it quietly, as though she is telling herself as much as you."
    jump yvara_visit_menu

label yvara_gift_botanical:
    narrator "She opens the pressing to a page at random and studies the specimen for a moment."
    yvara "Verath moss. Properly dried."
    narrator "She looks up."
    yvara "Who chose the specimens?"
    narrator "When you tell her, she looks back at the page."
    yvara "You have better taste than I gave you credit for."
    narrator "She sets it beside the lamp where the light will reach it."
    jump yvara_visit_menu

label yvara_gift_spiked_tea:
    narrator "She accepts the tin without comment. Prepares it in the usual way."
    narrator "A moment passes. She takes a sip."
    yvara "This blend is... different."
    narrator "She takes another."
    yvara "There is something in it I cannot place."
    narrator "She does not put it down."
    yvara "It is not unpleasant."
    narrator "She finishes the cup."
    jump yvara_visit_menu

label yvara_gift_silk_ribbon:
    narrator "She holds it for a moment without speaking, turning it slowly between her fingers."
    yvara "This is a fine quality."
    narrator "She sets it on the corner of her desk rather than to the side."
    yvara "I do not know what to do with it."
    narrator "She does not give it back."
    jump yvara_visit_menu

label yvara_gift_default:
    yvara "This is... something."
    yvara "Thank you."
    narrator "She accepts it politely."
    jump yvara_visit_menu

# Academy laboratory: alchemist pass (one-time), then craft sessions with investment tiers and 2 rounds of choices.
label academy_laboratory_dialogue:
    $ _lab_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else "images/event_bg.png")
    scene expression _lab_bg
    if not alchemy_unlocked:
        lab_director "The Academy's laboratory is open to those who pay the alchemist's pass. Here we work in batches—simple draughts in quantity—or risk coin and skill for rarer brews."
        lab_director "One payment of [ALCHEMY_PASS_COST] coins unlocks the laboratory for good. After that, you choose how much to invest each session. What will you do?"
        jump academy_laboratory_pass_menu
    $ _total = calculate_total_days()
    $ _last = last_laboratory_use_total_days
    if _last is not None and (_total - _last) < ALCHEMY_LABORATORY_COOLDOWN_DAYS:
        jump academy_laboratory_cooldown
    jump academy_laboratory_craft_menu

label academy_laboratory_pass_menu:
    menu:
        lab_director "What will you do?"
        "Pay the alchemist pass ([ALCHEMY_PASS_COST] coins)." if money >= ALCHEMY_PASS_COST:
            $ money -= ALCHEMY_PASS_COST
            $ add_alchemy_pass()
            lab_director "Done. The laboratory is yours to use. Invest coin at the start of each session; your worker's Craft and your choices in the rounds decide the outcome."
            $ renpy.show_screen("map_screen")
            $ renpy.show_screen("academy_menu")
            $ renpy.notify("Laboratory unlocked!")
            jump tavern_screen
        "Pay the alchemist pass ([ALCHEMY_PASS_COST] coins)." if money < ALCHEMY_PASS_COST:
            lab_director "Your purse is too light. The price is [ALCHEMY_PASS_COST] coins. Return when you can meet it."
            jump academy_laboratory_pass_menu
        "Leave.":
            $ renpy.show_screen("map_screen")
            jump tavern_screen

label academy_laboratory_craft_menu:
    lab_director "How much do you invest? Basic coin yields basic draughts in number. Deeper pockets open the way to quality—or something extraordinary."
    menu:
        lab_director "What will you do?"
        "Batch basic ([ALCHEMY_COST_BASIC] coins)." if money >= ALCHEMY_COST_BASIC:
            $ _alchemy_investment_tier = "basic"
            $ money -= ALCHEMY_COST_BASIC
            jump academy_alchemy_choose_worker
        "Batch basic ([ALCHEMY_COST_BASIC] coins)." if money < ALCHEMY_COST_BASIC:
            lab_director "You need at least [ALCHEMY_COST_BASIC] coins for a basic batch."
            jump academy_laboratory_craft_menu
        "Quality ([ALCHEMY_COST_QUALITY] coins)." if money >= ALCHEMY_COST_QUALITY:
            $ _alchemy_investment_tier = "quality"
            $ money -= ALCHEMY_COST_QUALITY
            jump academy_alchemy_choose_worker
        "Quality ([ALCHEMY_COST_QUALITY] coins)." if money < ALCHEMY_COST_QUALITY:
            lab_director "You need at least [ALCHEMY_COST_QUALITY] coins for a quality run."
            jump academy_laboratory_craft_menu
        "Premium ([ALCHEMY_COST_PREMIUM] coins)." if money >= ALCHEMY_COST_PREMIUM:
            $ _alchemy_investment_tier = "premium"
            $ money -= ALCHEMY_COST_PREMIUM
            jump academy_alchemy_choose_worker
        "Premium ([ALCHEMY_COST_PREMIUM] coins)." if money < ALCHEMY_COST_PREMIUM:
            lab_director "You need at least [ALCHEMY_COST_PREMIUM] coins for a premium run."
            jump academy_laboratory_craft_menu
        "Leave.":
            $ renpy.show_screen("map_screen")
            $ renpy.show_screen("academy_menu")
            jump tavern_screen

label academy_laboratory_cooldown:
    $ _total = calculate_total_days()
    $ _days_left = ALCHEMY_LABORATORY_COOLDOWN_DAYS - (_total - last_laboratory_use_total_days)
    lab_director "The laboratory has been in use recently. The alchemist needs a few days to restock and prepare the workspace. Return in [_days_left] day(s)."
    menu:
        "Leave.":
            $ renpy.show_screen("map_screen")
            $ renpy.show_screen("academy_menu")
            jump tavern_screen

label academy_alchemy_choose_worker:
    $ renpy.call_screen("choose_worker_for_alchemy_craft")
    $ _worker = _alchemy_chosen_worker
    $ _alchemy_chosen_worker = None
    if _worker is None or not isinstance(_worker, dict) or not _worker.get("name"):
        $ money += ALCHEMY_COST_BASIC if _alchemy_investment_tier == "basic" else (ALCHEMY_COST_QUALITY if _alchemy_investment_tier == "quality" else ALCHEMY_COST_PREMIUM)
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("academy_menu")
        jump tavern_screen
    jump academy_alchemy_craft_run

label academy_alchemy_craft_run:
    $ _worker = _alchemy_chosen_worker
    $ _tier = _alchemy_investment_tier
    $ _lab_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else "images/event_bg.png")
    scene expression _lab_bg
    if not getattr(persistent, "alchemy_craft_intro_done", False):
        $ persistent.alchemy_craft_intro_done = True
        lab_director "Your craftsperson will call out what they see—vapour, colour, the drip. Help them choose what to do with the fire."
        lab_director "Right choices sharpen the result; wrong ones can spoil the batch."
    $ _style = renpy.random.choice(ALCHEMY_ROUND_STYLES)
    $ craft_modifier = 0
    $ renpy.say(narrator, "Round one. " + _style["hint1"])
    menu:
        "Raise the heat.":
            $ _action = "heat_up"
        "Keep the temperature steady.":
            $ _action = "maintain"
        "Lower the heat.":
            $ _action = "heat_down"
    if _action == _style["round1"]:
        $ craft_modifier -= 15
        $ renpy.say(narrator, "Right call. The mixture stabilises.")
    else:
        $ craft_modifier += 15
        $ renpy.say(narrator, "Wrong call. The brew darkens; a note of burn.")
    $ renpy.say(narrator, "Round two. " + _style["hint2"])
    menu:
        "Raise the heat.":
            $ _action = "heat_up"
        "Keep the temperature steady.":
            $ _action = "maintain"
        "Lower the heat.":
            $ _action = "heat_down"
    if _action == _style["round2"]:
        $ craft_modifier -= 15
        $ renpy.say(narrator, "Right call. The mixture holds.")
    else:
        $ craft_modifier += 15
        $ renpy.say(narrator, "Wrong call. The vapour turns acrid.")
    $ _outcome = run_alchemy_craft_roll(_worker, craft_modifier)
    $ _given = apply_alchemy_result(_tier, _outcome, manager_inventory)
    $ last_laboratory_use_total_days = calculate_total_days()
    if _outcome == "failure":
        $ renpy.say(narrator, "The mixture turns. The batch is lost.")
        $ renpy.notify("The craft failed; the investment is lost.")
    else:
        python:
            _seen = {}
            for _id in _given:
                _seen[_id] = _seen.get(_id, 0) + 1
            _parts = []
            for _id, _count in _seen.items():
                _def = next((i for i in items_json.get("items", []) if i.get("id") == _id), None)
                _name = _def.get("name", _id) if _def else _id
                _parts.append((str(_count) + " " + _name) if _count > 1 else _name)
            _craft_result_text = _worker["name"] + "'s steady hand yields " + ", ".join(_parts) + "."
            _craft_notify_text = "Craft successful! Obtained: " + ", ".join(_parts)
        $ renpy.say(narrator, _craft_result_text)
        $ renpy.notify(_craft_notify_text)
    $ renpy.show_screen("map_screen")
    $ renpy.show_screen("academy_menu")
    jump tavern_screen

# Arena: Lanista permit then trial by combat. First dialogue asks for permit payment; then requests a combatant (potentially lethal).
label arena_first_dialogue:
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena_promoter.png" if renpy.loadable("images/events/arena_promoter.png") else "images/event_bg.png")
    scene expression _arena_bg
    if not arena_lanista_paid:
        arena_promoter "The coliseum welcomes you—but the sands do not. I am master here: the Lanista. These grounds have tasted blood and glory for generations, and they do not open to just anyone."
        arena_promoter "If you would train gladiators under my banner, you must first buy in. [LANISTA_PERMIT_COST] coins—one payment, no haggling. After that, we speak of worth. Proof is in the sand: a trial by combat. What say you?"
        jump arena_permit_menu
    # Already paid permit, need trial
    arena_promoter "The permit is yours. Paper and coin open the gate—but the crowd and the sands demand more. They demand proof."
    arena_promoter "Send me one of your own for a trial by combat before the masses. The bout may be to the death; the sands show no mercy."
    arena_promoter "If your fighter survives—or falls with honour, blade in hand—the Arena is yours to use. Do you accept?"
    jump arena_combatant_menu

label arena_permit_menu:
    menu:
        arena_promoter "What will you do?"
        "Pay the Lanista permit ([LANISTA_PERMIT_COST] coins)." if money >= LANISTA_PERMIT_COST:
            $ money -= LANISTA_PERMIT_COST
            $ arena_lanista_paid = True
            arena_promoter "Done. The coin is received; the ledger is satisfied. Now the sands ask for blood—or at least courage. Bring me a combatant worthy of the arena. The trial can be lethal. Choose with care."
            jump arena_combatant_menu
        "Pay the Lanista permit ([LANISTA_PERMIT_COST] coins)." if money < LANISTA_PERMIT_COST:
            arena_promoter "Your purse is too light. The price is fixed: [LANISTA_PERMIT_COST] coins. Return when you can meet it."
            jump arena_permit_menu
        "Leave.":
            $ renpy.show_screen("map_screen")
            jump tavern_screen

label arena_combatant_menu:
    menu:
        "Send a combatant to the trial.":
            jump arena_do_trial
        "Leave.":
            $ renpy.show_screen("map_screen")
            jump tavern_screen

label arena_do_trial:
    $ renpy.call_screen("choose_worker_for_arena_trial")
    $ _worker = _arena_chosen_worker
    $ _arena_chosen_worker = None
    if _worker is None or not isinstance(_worker, dict) or not _worker.get("name"):
        $ renpy.show_screen("map_screen")
        jump tavern_screen
    jump arena_run_trial_and_result

# Run from screen action when user picks a worker; worker_name is passed so the new context has it.
label arena_run_trial_and_result(worker_name=None):
    $ _worker = next((w for w in store.workers if w.get("name") == worker_name), None)
    if _worker is None or not _worker.get("name"):
        $ renpy.show_screen("map_screen")
        jump tavern_screen
    $ _outcome = run_arena_trial(_worker)
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena_promoter.png" if renpy.loadable("images/events/arena_promoter.png") else "images/event_bg.png")
    scene expression _arena_bg
    if _outcome == "critical_success":
        $ add_arena_building()
        $ add_item_to_inventory(manager_inventory, "arena_champion_blade")
        $ renpy.say(narrator, _worker["name"] + " stepped into the sands with cold focus. Blow after blow, they turned the trial into a masterclass, and the crowd roared with each parry and strike.")
        $ renpy.say(narrator, "When the dust settled, they stood unmarked, and even the arena promoter rose from his seat.")
        $ renpy.say(narrator, "The Arena is yours. As a token of the sands, he grants you a champion's blade from his own armoury.")
        $ renpy.notify("Arena unlocked! You received Arena Champion's Blade.")
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("arena_menu")
        jump tavern_screen
    elif _outcome == "success":
        $ add_arena_building()
        $ renpy.say(narrator, _worker["name"] + " took the sand and gave as good as they got. Bloodied but unbowed, they outlasted their opponent and raised their weapon to the crowd's approval.")
        $ renpy.say(narrator, "The trial is won. The Arena opens its gates to you—you may use it from the map from now on.")
        $ renpy.notify("Arena unlocked!")
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("arena_menu")
        jump tavern_screen
    elif _outcome == "mediocre":
        $ add_arena_building()
        $ add_trait_with_duration(_worker, "Scarred", 0)
        $ renpy.say(narrator, _worker["name"] + " was thrown to the sand more than once, but each time they staggered back to their feet. The fight was ugly, but they endured until the arena promoter called it.")
        $ renpy.say(narrator, "The sands have left their mark. They will carry the scars, but the Arena is yours. Honour was earned the hard way.")
        $ renpy.notify("Arena unlocked. " + _worker["name"] + " was injured and gained Scarred.")
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("arena_menu")
        jump tavern_screen
    else:
        $ _worker["health"] = 0
        $ renpy.say(narrator, _worker["name"] + " fought with everything they had, but the sands are unforgiving. When the dust settled, they did not rise again.")
        $ renpy.say(narrator, "The Arena remains closed. When you are ready, send another combatant—or pay the permit again and try once more.")
        $ renpy.show_screen("map_screen")
        jump tavern_screen

# -------- Special match: 5000 entry, first-time intro, choose worker, 2 rounds with hints, combat roll, outcomes --------
label arena_special_match_dialogue:
    $ renpy.hide_screen("arena_menu")
    $ renpy.hide_screen("map_screen")
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena_promoter.png" if renpy.loadable("images/events/arena_promoter.png") else "images/event_bg.png")
    scene expression _arena_bg
    if not arena_special_match_intro_done:
        arena_promoter "A special match is a staged duel. Your gladiator faces a style—Murmillo, Retiarius, Secutor, Thraex, Hoplomachus—or a beast of myth."
        arena_promoter "Watch the opponent and shout to your gladiator what they are doing: attacking, defending, or feinting. Get it right and they react; wrong and they pay for it."
        arena_promoter "Two rounds, then skill decides. Lose and they may die or be scarred. Win and the purse grows; five wins crown them Arena Champion."
        $ arena_special_match_intro_done = True
    $ _total_days = calculate_total_days()
    if last_special_match_total_days is not None and (_total_days - last_special_match_total_days) < 7:
        $ _days_left = 7 - (_total_days - last_special_match_total_days)
        $ _cooldown_who = "Your gladiator " + last_special_match_worker_name + " fought here recently." if last_special_match_worker_name else "You fought here recently."
        arena_promoter "One special match per week. [_cooldown_who] Return in [_days_left] days."
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("arena_menu")
        jump tavern_screen
    if money < SPECIAL_MATCH_COST:
        arena_promoter "Your purse is too light. [SPECIAL_MATCH_COST] coins to enter."
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("arena_menu")
        jump tavern_screen
    $ money -= SPECIAL_MATCH_COST
    $ renpy.call_screen("choose_worker_for_arena_special_match")
    $ renpy.show_screen("map_screen")
    $ renpy.show_screen("arena_menu")
    jump tavern_screen

label arena_special_match_run(worker_name):
    $ _worker = next((w for w in store.workers if w.get("name") == worker_name), None)
    if _worker is None or not _worker.get("name"):
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("arena_menu")
        jump tavern_screen
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena_promoter.png" if renpy.loadable("images/events/arena_promoter.png") else "images/event_bg.png")
    scene expression _arena_bg
    if "Arena Champion" in _worker.get("traits", []):
        arena_promoter "I know this one. A champion of the sands. Good."
    $ _style = renpy.random.choice(SPECIAL_MATCH_STYLES)
    $ special_match_diff = 0
    $ special_match_health_lost = 0
    $ renpy.say(narrator, "Your fighter faces a " + _style["name"] + ".")
    # Round 1: player shouts what the opponent is doing; good = correct call, neutral = tie, bad = wrong call
    $ renpy.say(narrator, "Round one. " + _style["hint1"])
    menu:
        "They're attacking!":
            $ _action = "attack"
        "They're defending!":
            $ _action = "defend"
        "They're feinting!":
            $ _action = "feint"
    $ _opp = _style["round1"]
    if _special_match_call_correct(_action, _opp):
        $ special_match_diff -= 20
        $ renpy.say(narrator, "Right call. Your gladiator gains the edge.")
    elif _special_match_call_neutral(_action, _opp):
        $ renpy.say(narrator, "Neutral. The exchange settles nothing.")
    else:
        $ special_match_diff += 20
        $ special_match_health_lost += 10
        $ renpy.say(narrator, "Wrong call. Your fighter takes a heavy blow.")
    # Round 2
    $ renpy.say(narrator, "Round two. " + _style["hint2"])
    menu:
        "They're attacking!":
            $ _action = "attack"
        "They're defending!":
            $ _action = "defend"
        "They're feinting!":
            $ _action = "feint"
    $ _opp = _style["round2"]
    if _special_match_call_correct(_action, _opp):
        $ special_match_diff -= 20
        $ renpy.say(narrator, "Right call. Your gladiator gains the edge.")
    elif _special_match_call_neutral(_action, _opp):
        $ renpy.say(narrator, "Neutral. The exchange settles nothing.")
    else:
        $ special_match_diff += 20
        $ special_match_health_lost += 10
        $ renpy.say(narrator, "Wrong call. Your fighter takes a heavy blow.")
    # Apply health loss
    $ _worker["health"] = max(0, _worker.get("health", 0) - special_match_health_lost)
    # Combat roll
    $ _won = run_arena_special_match_combat_roll(_worker, special_match_diff)
    if _won:
        $ victories = min(5, _worker.get("special_match_victories", 0) + 1)  # Cap at 5; same money bonus if they fight again with 5
        $ _worker["special_match_victories"] = victories
        $ _prize = 5000 + 5000 * victories
        $ money += _prize
        if special_match_diff >= 40:
            $ renpy.say(narrator, _worker["name"] + " had two wrong calls against them. By sheer skill they turned the tide.")
        elif special_match_diff <= -40:
            $ renpy.say(narrator, _worker["name"] + " read the sand twice. Cold execution. The " + _style["name"] + " falls.")
        else:
            $ renpy.say(narrator, _worker["name"] + " had one right call and one mistake. The " + _style["name"] + " yields.")
        $ renpy.say(narrator, "Victory. Purse: " + str(_prize) + " coins. Wins: " + str(victories) + "/5.")
        if victories >= 5:
            $ add_trait_with_duration(_worker, "Arena Champion", 0)
            $ renpy.say(narrator, "Five victories. The arena promoter crowns " + _worker["name"] + " Arena Champion.")
            $ renpy.notify("Arena Champion! " + _worker["name"] + " earned the Arena Champion trait.")
        else:
            $ renpy.notify("Special match won! +" + str(_prize) + " coins. Victories: " + str(victories) + "/5.")
    else:
        if "Arena Champion" in _worker.get("traits", []):
            $ remove_trait(_worker, "Arena Champion")
            $ renpy.say(narrator, _worker["name"] + " falls before the " + _style["name"] + ". The crown is lost; the sands spare their life.")
            $ renpy.notify("Arena Champion lost. " + _worker["name"] + " survived but lost the trait.")
        else:
            $ _death = renpy.random.random() < 0.5
            if _death:
                $ renpy.say(narrator, _worker["name"] + " fought hard but the " + _style["name"] + " was merciless. They did not rise again.")
                $ renpy.say(narrator, "The sands have claimed another.")
                $ store.workers[:] = [w for w in store.workers if w.get("name") != _worker["name"]]
                $ rebuild_assigned_servants()
                $ renpy.notify(_worker["name"] + " has died in the special match.")
            else:
                $ add_trait_with_duration(_worker, "Scarred", 0)
                $ _worker["health"] = 1
                $ renpy.say(narrator, _worker["name"] + " is beaten to the sand. The arena promoter raises his hand. Mercy.")
                $ renpy.say(narrator, "They are dragged out scarred, with a single point of life.")
                $ renpy.notify(_worker["name"] + " was spared with Scarred and 1 HP.")
    $ last_special_match_total_days = calculate_total_days()
    $ last_special_match_worker_name = _worker["name"]
    $ renpy.show_screen("map_screen")
    $ renpy.show_screen("arena_menu")
    jump tavern_screen

