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
    # Event Success Configuration
    #############################
    # Base success bonus added to all skill-based event checks
    # This increases the baseline success chance for all events
    EVENT_SUCCESS_BASE_BONUS_WORKER = 30  # Percentage points added to worker skill level for success checks
    EVENT_SUCCESS_BASE_BONUS_BUILDING = 50  # Percentage points added to building skill for success checks
    EVENT_SUCCESS_MIN_CHANCE = 0.6  # Minimum success chance (60%) for events with defined success_chance

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
        Returns 'aspen' for males, 'blossom' for females/unknown."""
        if worker and isinstance(worker, dict):
            gender = worker.get("gender", "").lower()
            if gender == "male":
                return "aspen"
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
        
        # Try worker's profile image using robust flexible matching
        profile_matches = get_pattern_matches_flexible(base_folder, "profile")
        renpy.log(f"Profile matches found: {len(profile_matches) if profile_matches else 0}")
        if profile_matches:
            renpy.log(f"Profile matches: {profile_matches}")
            selected = renpy.random.choice(profile_matches)
            renpy.log(f"Selected profile image: {selected}")
            return selected
        
        # Try any image in worker folder as fallback (excluding failure images)
        all_worker_images = get_pattern_matches_flexible(base_folder, "", exclude_failure=True)
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
                        
                        if not should_exclude:
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
                        
                        if not should_exclude:
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
        
        if item_type in ["currency", "consumable"]:
            for i, entry in enumerate(inventory):
                if entry[0] == item_id:
                    # CRITICAL: Validate existing quantity before adding
                    existing_qty = entry[1]
                    try:
                        existing_qty = int(existing_qty)
                        if existing_qty < 0:
                            existing_qty = 0  # Fix negative quantities
                            renpy.log(f"WARNING: Fixed negative quantity for {item_id}, resetting to 0")
                        if existing_qty > 999999:
                            existing_qty = 999999  # Cap excessive quantities
                            renpy.log(f"WARNING: Capped excessive quantity for {item_id} to 999999")
                    except (ValueError, TypeError):
                        existing_qty = 0
                        renpy.log(f"WARNING: Invalid quantity for {item_id}, resetting to 0")
                    
                    new_quantity = existing_qty + quantity
                    # Cap at reasonable maximum
                    if new_quantity > 999999:
                        new_quantity = 999999
                        renpy.log(f"WARNING: Capped total quantity for {item_id} to 999999")
                    
                    # CRITICAL: Create a NEW tuple to break any reference sharing
                    inventory[i] = (entry[0], new_quantity, entry[2])
                    renpy.log(f"Added {quantity} of {item_id} to existing stack (new quantity: {new_quantity}).")
                    # CRITICAL: Force Ren'Py to recognize changes if this is manager_inventory
                    if is_manager_inventory:
                        # Also ensure the entire list is a new list to break references
                        store.manager_inventory = list(store.manager_inventory)
                        renpy.store.manager_inventory = store.manager_inventory
                    _mark_objective_12_item_if_needed(item_id)
                    return
            inventory.append((item_id, quantity, False))
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
        """Cache traits.json lookups for item effects."""
        if not hasattr(store, "_trait_def_cache") or not store._trait_def_cache:
            try:
                traits_json_path = os.path.join(renpy.config.gamedir, "data", "traits.json")
                with open(traits_json_path, "r", encoding="utf-8") as f:
                    traits_data = json.load(f)
                traits_get = getattr(traits_data, "get", None)
                if callable(traits_get):
                    trait_list = traits_get("traits", [])
                elif isinstance(traits_data, (list, tuple)):
                    trait_list = list(traits_data)
                else:
                    renpy.log(f"TRAITS: traits.json unexpected type: {type(traits_data)}")
                    trait_list = []
                store._trait_def_cache = {t.get("name"): t for t in trait_list if t.get("name")}
            except Exception as e:
                renpy.log(f"TRAITS: Failed to load traits.json for item effects: {e}")
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
                    # Calculate the current health percentage
                    current_health_percentage = worker["health"] / calculate_max_health(worker)
                    # Update the maximum health
                    worker["max_health"] = calculate_max_health(worker) + effect_value
                    # Adjust current health proportionally
                    worker["health"] = int(worker["max_health"] * current_health_percentage)
                elif effect_type == "energy":
                    # Calculate the current energy percentage
                    current_energy_percentage = worker["energy"] / calculate_max_energy(worker)
                    # Update the maximum energy
                    worker["max_energy"] = calculate_max_energy(worker) + effect_value
                    # Adjust current energy proportionally
                    worker["energy"] = int(worker["max_energy"] * current_energy_percentage)
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
                    # Calculate the current health percentage
                    current_health_percentage = worker["health"] / calculate_max_health(worker)
                    # Revert the maximum health
                    worker["max_health"] = calculate_max_health(worker) - effect_value
                    # Adjust current health proportionally
                    worker["health"] = int(worker["max_health"] * current_health_percentage)
                elif effect_type == "energy":
                    # Calculate the current energy percentage
                    current_energy_percentage = worker["energy"] / calculate_max_energy(worker)
                    # Revert the maximum energy
                    worker["max_energy"] = calculate_max_energy(worker) - effect_value
                    # Adjust current energy proportionally
                    worker["energy"] = int(worker["max_energy"] * current_energy_percentage)
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

        # Only consumables are usable
        if item.get("type") != "consumable":
            return

        renpy.notify("Used " + item.get("name", "Unknown"))

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
    
    def assign_random_traits_with_limits(worker, target_min=3, target_max=5):
        """
        Assign random traits to a worker, excluding only_assigned traits.
        If worker already has traits, adds additional ones to reach target_min-target_max total.
        
        Args:
            worker: Worker dictionary
            target_min: Minimum total traits (default 3)
            target_max: Maximum total traits (default 5)
        """
        # Load traits from JSON
        traits_json_path = os.path.join(renpy.config.gamedir, "data", "traits.json")
        if not os.path.exists(traits_json_path):
            renpy.log(f"Traits JSON not found at {traits_json_path}")
            return worker
        
        with open(traits_json_path, 'r', encoding='utf-8') as f:
            traits_data = json.load(f)

        traits_get = getattr(traits_data, "get", None)
        if callable(traits_get):
            traits_list = traits_get("traits", [])
        elif isinstance(traits_data, (list, tuple)):
            traits_list = list(traits_data)
        else:
            renpy.log(f"Traits JSON unexpected type: {type(traits_data)}")
            traits_list = []
        
        # Get existing traits (to avoid duplicates and check conflicts)
        existing_traits = worker.get("traits", [])
        if not isinstance(existing_traits, list):
            existing_traits = []
        
        # Filter traits that are not marked as only_assigned, are not NSFW (if applicable), and not already present
        possible_traits = [
            t for t in traits_list
            if not t.get("only_assigned", False) 
            and (persistent.nsfw_enabled or not t.get("nsfw", False))
            and t["name"] not in existing_traits
        ]
        random.shuffle(possible_traits)  # Shuffle to ensure randomness

        selected_traits = list(existing_traits)  # Start with existing traits
        attempts = 0
        max_attempts = 200  # Prevent infinite loops

        # Calculate how many more traits we need
        traits_needed = max(0, target_min - len(existing_traits))
        
        # Ensure at least target_min traits total (existing + new)
        while len(selected_traits) < target_min and attempts < max_attempts and possible_traits:
            trait = possible_traits.pop()
            trait_name = trait["name"]

            # Check if the trait conflicts with any already selected traits
            conflicts = False
            for existing_trait_name in selected_traits:
                existing_trait = next((t for t in traits_list if t["name"] == existing_trait_name), None)
                if existing_trait and trait_name in existing_trait.get("conflicts", []):
                    conflicts = True
                    break
                if trait_name in trait.get("conflicts", []):
                    conflicts = True
                    break
            
            if not conflicts:
                add_trait_with_duration(worker, trait_name, 0)
                selected_traits.append(trait_name)
                renpy.log(f"Assigned trait '{trait_name}' to {worker.get('name', 'Unknown')} (total: {len(selected_traits)})")

            attempts += 1

        # If we couldn't assign enough traits due to conflicts, log a warning
        if len(selected_traits) < target_min:
            renpy.log(f"Warning: Only {len(selected_traits)} traits assigned to {worker.get('name', 'Unknown')} (target: {target_min}) due to conflicts or lack of available traits.")

        # Try to add more traits up to target_max, if possible
        while len(selected_traits) < target_max and possible_traits:
            trait = possible_traits.pop()
            trait_name = trait["name"]

            # Check if the trait conflicts with any already selected traits
            conflicts = False
            for existing_trait_name in selected_traits:
                existing_trait = next((t for t in traits_list if t["name"] == existing_trait_name), None)
                if existing_trait and trait_name in existing_trait.get("conflicts", []):
                    conflicts = True
                    break
                if trait_name in trait.get("conflicts", []):
                    conflicts = True
                    break

            if not conflicts:
                add_trait_with_duration(worker, trait_name, 0)
                selected_traits.append(trait_name)
                renpy.log(f"Assigned additional trait '{trait_name}' to {worker.get('name', 'Unknown')} (total: {len(selected_traits)})")

        return worker

    # Expose the extended trait assignment helper to avoid name collisions
    store.assign_random_traits_with_limits = assign_random_traits_with_limits

   

    
    

    

    

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
        
        # Apply defaults
        for worker in available_workers:
            ensure_worker_defaults(worker)
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
        
        # Randomly select gender
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
            "traits": list(base_traits)  # Keep template traits (e.g., race) for image consistency
        })
        
        # Assign additional random traits if needed (to reach 3 total max)
        store.assign_random_traits_with_limits(new_worker, target_min=3, target_max=3)
        
        # Ensure all defaults are properly set
        ensure_worker_defaults(new_worker)
        
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
            "nsfw": persistent.nsfw_enabled  # Set NSFW based on game mode
        }
        
        # Assign additional random traits if needed (to reach 3 total max)
        store.assign_random_traits_with_limits(new_worker, target_min=3, target_max=3)
        
        # Ensure all defaults are properly set
        ensure_worker_defaults(new_worker)
        
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
            workers.append(worker)
            available_buildings["Building 1"]["servant_jobs"][worker["name"]] = "Unassigned"
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

    def sync_assigned_servants_for_building(building_name):
        """Rebuild assigned_servants for a single building from servant_jobs and store.workers."""
        try:
            if not building_name or building_name not in available_buildings:
                return
            building = available_buildings.get(building_name)
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
                    if worker_obj.get("assigned_building", "Unassigned") != building_name:
                        worker_obj["assigned_building"] = building_name
            
            # Source 2: Workers with assigned_building matching this building
            for worker in store.workers:
                if not isinstance(worker, dict):
                    continue
                wname = worker.get("name")
                if not wname or wname in seen:
                    continue
                if worker.get("assigned_building") == building_name:
                    rebuilt.append(worker)
                    seen.add(wname)
                    # Ensure they have an entry in servant_jobs
                    if "servant_jobs" not in building:
                        building["servant_jobs"] = {}
                    if wname not in building["servant_jobs"]:
                        building["servant_jobs"][wname] = "unassigned"
            
            building["assigned_servants"] = rebuilt
        except Exception as e:
            renpy.log("sync_assigned_servants_for_building error: " + str(e))

    def get_building_servants(building_name):
        """Return a deduped list of canonical workers for a building.
        Uses both servant_jobs AND worker assigned_building as sources for robustness.
        This ensures workers show even if servant_jobs is incomplete (e.g., old saves)."""
        try:
            if not building_name or building_name not in available_buildings:
                return []
            building = available_buildings.get(building_name, {})
            if not isinstance(building, dict):
                return []
            name_to_worker = {w.get("name"): w for w in store.workers if isinstance(w, dict) and w.get("name")}
            servants = []
            seen = set()
            
            # Source 1: servant_jobs dictionary (primary source)
            jobs = building.get("servant_jobs", {}) or {}
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
            
            # Source 2: workers with assigned_building matching this building (fallback)
            # This ensures workers show even if servant_jobs is incomplete
            for worker in store.workers:
                if not isinstance(worker, dict):
                    continue
                wname = worker.get("name")
                if not wname or wname in seen:
                    continue
                if worker.get("assigned_building") == building_name:
                    servants.append(worker)
                    seen.add(wname)
                    # Also ensure they have an entry in servant_jobs for consistency
                    if wname not in jobs:
                        building.setdefault("servant_jobs", {})[wname] = "unassigned"
            
            return servants
        except Exception as e:
            renpy.log("get_building_servants error: " + str(e))
            return []

    def validate_and_sync_buildings(include_worker_refs=True):
        """Ensure all buildings in owned_buildings exist in available_buildings.
        Also checks workers for building references and creates missing buildings.
        This fixes corrupted saves where buildings are missing from available_buildings."""
        import re
        try:
            renpy.log("validate_and_sync_buildings: STARTING")
            
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
            
            # 3. Create missing buildings
            created_count = 0
            for building_name in buildings_to_check:
                if building_name not in available_buildings:
                    renpy.log(f"validate_and_sync_buildings: WARNING - {building_name} referenced but not in available_buildings, recreating...")
                    # Recreate the building with default values
                    # Try to determine if it's a special building (like Castle) or a regular building
                    if "Castle" in building_name or building_name.startswith("Governor"):
                        # Special building (Castle)
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
                        # Regular building - use default values
                        # Try to extract building number to estimate price
                        match = re.search(r'Building (\d+)', building_name)
                        if match:
                            building_num = int(match.group(1))
                            # Default price increases with building number
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
                    
                    # Ensure custom_names entry exists
                    if not hasattr(store, 'custom_names'):
                        store.custom_names = {}
                    if building_name not in store.custom_names:
                        store.custom_names[building_name] = building_name
                    
                    # If building is referenced by workers but not in owned_buildings, add it
                    if hasattr(store, 'owned_buildings'):
                        if building_name not in store.owned_buildings:
                            store.owned_buildings.append(building_name)
                            renpy.log(f"validate_and_sync_buildings: Added {building_name} to owned_buildings")
                        else:
                            renpy.log(f"validate_and_sync_buildings: {building_name} already in owned_buildings")
                    else:
                        store.owned_buildings = [building_name]
                        renpy.log(f"validate_and_sync_buildings: Created owned_buildings list with {building_name}")
                    
                    renpy.log(f"validate_and_sync_buildings: Recreated {building_name} in available_buildings")
                    created_count += 1
                else:
                    renpy.log(f"validate_and_sync_buildings: {building_name} already exists in available_buildings")
            
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
                if assigned_building not in available_buildings:
                    worker["assigned_building"] = "Unassigned"
                    continue
                # Deduplicate by name per building
                if assigned_building not in seen_per_building:
                    seen_per_building[assigned_building] = set()
                if wname in seen_per_building[assigned_building]:
                    continue  # Skip duplicate
                seen_per_building[assigned_building].add(wname)
                building = available_buildings[assigned_building]
                if isinstance(building, dict):
                    building["assigned_servants"].append(worker)
            
            renpy.log("sync_building_assignments_from_workers: done")
        except Exception as e:
            renpy.log(f"sync_building_assignments_from_workers error: {e}")
    
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
                total_skill = min(100, base_total_skill + EVENT_SUCCESS_BASE_BONUS_BUILDING)

                roll = random.randint(1, 100)
                
                # --- DEBUG LOGGING ---
                renpy.log(f"--- Building Skill Check ---")
                renpy.log(f"Building: {selected_building_name}")
                renpy.log(f"Base Skill: {selected_building['skill']}")
                renpy.log(f"Skill Bonus: {selected_building['skill_bonus']}")
                renpy.log(f"Base Total Skill: {base_total_skill}")
                renpy.log(f"With +{EVENT_SUCCESS_BASE_BONUS_BUILDING}% bonus: {total_skill}")
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
                    # Success case: building skill event, no worker involved
                    applied_values = apply_effects(effect.get("success", {}), worker=None, building=selected_building)
                    # For building skill events, use fixed placeholders
                    event_worker_name = "Unknown"
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
                    applied_values = apply_effects(effect)
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
                        applied_values = apply_effects(effect)
                        # Get the message and apply replacements
                        message = choice.get("message", "The event concludes.")
                        message = message.replace("[player_title]", str(player_title)).replace("[player_name]", str(player_name))
                        # Apply dynamic message formatting
                        message = format_dynamic_message(message, applied_values)
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

                # Check required_trait if specified
                required_trait = choice.get("required_trait")
                if required_trait and selected_worker:
                    worker_traits = selected_worker.get("traits", [])
                    if required_trait not in worker_traits:
                        renpy.log(f"Worker {selected_worker['name']} missing required trait '{required_trait}'")
                        return {"message": f"This task requires someone with the '{required_trait}' trait. {selected_worker['name']} does not have this trait.", "outcome": "failure"}

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
                            skill_with_bonus = min(100, skill_level + EVENT_SUCCESS_BASE_BONUS_WORKER)
                            effective_success_chance = max(skill_with_bonus, min_success_chance)
                            renpy.log(f"Worker {selected_worker['name']} skill {skill_level} (with +{EVENT_SUCCESS_BASE_BONUS_WORKER} bonus = {skill_with_bonus}) meets threshold {threshold} - using {effective_success_chance}% success chance")
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
                        effective_skill = min(100, skill_level + EVENT_SUCCESS_BASE_BONUS_WORKER)
                        roll = random.randint(1, 100)
                        renpy.log(f"Worker {selected_worker['name']} skill {skill_level} (with +{EVENT_SUCCESS_BASE_BONUS_WORKER}% bonus = {effective_skill}) - roll {roll} vs {effective_skill}%")
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
                effective_success_chance = max(EVENT_SUCCESS_MIN_CHANCE, success_chance)
                roll = random.random()
                if roll <= effective_success_chance:
                    outcome_status = "success"
                    message = choice.get("message_success", "Fortune smiles upon you.")
                    applied_values = apply_effects(effect.get("success", {}))
                else:
                    outcome_status = "failure"
                    message = choice.get("message_failure", "Fortune turns her back.")
                    applied_values = apply_effects(effect.get("failure", {}))
                
                # Replace worker name if present
                if acting_worker and hasattr(acting_worker, 'get'):
                    worker_name = acting_worker.get("name", "Unknown")
                    message = message.replace("[acting_worker]", worker_name)
                
                if effective_success_chance > success_chance:
                    renpy.log(f"Success chance event: roll {roll:.2f} vs {success_chance} (boosted to minimum {EVENT_SUCCESS_MIN_CHANCE*100}% = {effective_success_chance:.2f}) = {outcome_status}")
                else:
                    renpy.log(f"Success chance event: roll {roll:.2f} vs {success_chance} = {outcome_status}")
            else:
                # Simple choice without probability
                applied_values = apply_effects(effect)
                message = choice.get("message", "The event concludes.")
                outcome_status = "success"
            
            message = message.replace("[player_title]", str(player_title)).replace("[player_name]", str(player_name))
            
            # Apply dynamic message formatting
            message = format_dynamic_message(message, applied_values)
            
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
                                worker["traits"].remove(trait_name)
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
                worker["traits"].remove(trait_name)
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
                # Your existing worker addition logic
                ensure_worker_defaults(target_worker)
                store.workers.append(target_worker.copy())
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
                worker["energy"] = max(0, worker["energy"] + effect_dict["servant_energy"])
                # Only show notification if energy actually changed
                if effect_dict["servant_energy"] != 0:
                    renpy.notify(f"{worker['name']}'s energy changed by {effect_dict['servant_energy']}")

            # Adjust health
            if "servant_health" in effect_dict:
                worker["health"] = max(0, worker["health"] + effect_dict["servant_health"])
                # Only show notification if health actually changed
                if effect_dict["servant_health"] != 0:
                    renpy.notify(f"{worker['name']}'s health changed by {effect_dict['servant_health']}")

            # Add traits with duration
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

                    # Handle different target types
                    target_worker = worker

                    if target == "random_worker":
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
                        add_trait_with_duration(target_worker, trait_name, duration)
                    elif trait_name:
                        renpy.log(f"Could not add trait '{trait_name}' - no suitable worker found")
                    else:
                        renpy.log("Error: 'add_trait' effect is missing 'name' key.")

                # Robust type checking for Ren'Py JSON-loaded data
                is_list = isinstance(trait_data, list) or (hasattr(trait_data, '__iter__') and not isinstance(trait_data, str) and not isinstance(trait_data, dict))
                is_dict = isinstance(trait_data, dict) or (hasattr(trait_data, 'get') and callable(getattr(trait_data, 'get', None)) and not isinstance(trait_data, str))
                is_string = isinstance(trait_data, str) and not is_dict
                
                try:
                    if is_list:
                        for trait_entry in trait_data:
                            apply_trait_entry(trait_entry)
                    elif is_dict or is_string:
                        apply_trait_entry(trait_data)
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
                        target_worker["is_servant"] = False
                        store.workers.append(target_worker)
                        renpy.notify(f"{target_worker['name']} has joined you!")
                        store.event_worker_name = target_worker["name"]
                    else:
                        new_worker = spawn_new_worker()
                        ensure_worker_defaults(new_worker)
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
                """Helper function to apply a single trait entry."""
                # Robust type checking for Ren'Py JSON-loaded data
                # Check if it's a dict-like object (has 'get' method)
                is_dict = isinstance(trait_entry, dict) or (hasattr(trait_entry, 'get') and callable(getattr(trait_entry, 'get', None)))
                # Check if it's a string (but not a dict that happens to have get)
                is_string = isinstance(trait_entry, str) and not is_dict
                
                if is_dict:
                    try:
                        trait_name = trait_entry.get("name") if hasattr(trait_entry, 'get') else None
                        duration = trait_entry.get("duration", 0) if hasattr(trait_entry, 'get') else 0
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
                
                if trait_name and target_worker:
                    trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
                    if trait_def:
                        if duration == 0:
                            duration = trait_def.get("duration", 0)
                        add_trait_with_duration(target_worker, trait_name, duration)
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
        
        Available placeholders:
        {actual_money} - Money amount after multipliers (e.g., "+750" or "-200")
        {base_money} - Original money amount before multipliers
        {actual_reputation} - Reputation change after multipliers
        {base_reputation} - Original reputation change before multipliers
        {money_multiplier} - Building multiplier for money (e.g., "1.5")
        {reputation_multiplier} - Building multiplier for reputation
        """
        # Always process placeholders, even if applied_values is empty
        # This prevents Ren'Py from treating them as unknown text tags
            
        # Format money with + or - sign
        if "actual_money" in applied_values:
            money = applied_values["actual_money"]
            if money > 0:
                message = message.replace("{actual_money}", f"+${money}")
            elif money < 0:
                message = message.replace("{actual_money}", f"-${abs(money)}")
            else:
                message = message.replace("{actual_money}", "$0")
        else:
            # Replace with placeholder text if no money effect was applied
            message = message.replace("{actual_money}", "$0")
                
        if "base_money" in applied_values:
            base_money = applied_values["base_money"]
            if base_money > 0:
                message = message.replace("{base_money}", f"+${base_money}")
            elif base_money < 0:
                message = message.replace("{base_money}", f"-${abs(base_money)}")
            else:
                message = message.replace("{base_money}", "$0")
        else:
            # Replace with placeholder text if no base money info available
            message = message.replace("{base_money}", "$0")
        
        # Format reputation with + or - sign
        if "actual_reputation" in applied_values:
            rep = applied_values["actual_reputation"]
            if rep > 0:
                message = message.replace("{actual_reputation}", f"+{rep}")
            elif rep < 0:
                message = message.replace("{actual_reputation}", f"{rep}")
            else:
                message = message.replace("{actual_reputation}", "0")
        else:
            # Replace with placeholder text if no reputation effect was applied
            message = message.replace("{actual_reputation}", "0")
                
        if "base_reputation" in applied_values:
            base_rep = applied_values["base_reputation"]
            if base_rep > 0:
                message = message.replace("{base_reputation}", f"+{base_rep}")
            elif base_rep < 0:
                message = message.replace("{base_reputation}", f"{base_rep}")
            else:
                message = message.replace("{base_reputation}", "0")
        else:
            # Replace with placeholder text if no base reputation info available
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
        
        # Use random.choices to select items based on their weights.
        chosen_items = random.choices(filtered_items, weights=weights, k=num_rolls)
        loot_ids = [item["id"] for item in chosen_items]
        
        renpy.log(f"roll_loot: Loot rolled using random.choices: {loot_ids} (weights: {weights})")
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

init python:
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
    return