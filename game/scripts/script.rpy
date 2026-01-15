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
default current_day = 1
default current_month = 1  # 1-based (Frostveil = 1)
default current_year = 1

# Initialize persistent calendar variables if they don't exist
init python:
    if not hasattr(persistent, "current_day") or persistent.current_day is None:
        persistent.current_day = 1
    if not hasattr(persistent, "current_month") or persistent.current_month is None:
        persistent.current_month = 1
    if not hasattr(persistent, "current_year") or persistent.current_year is None:
        persistent.current_year = 1

    def initialize_calendar(force_reset=False):
        """Initialize or sync calendar variables."""
        # Reset explicitly only when requested
        if force_reset:
            store.current_day = 1
            store.current_month = 1
            store.current_year = 1
            persistent.current_day = 1
            persistent.current_month = 1
            persistent.current_year = 1
            renpy.save_persistent()
            renpy.log("Calendar reset for new game (forced)")
            return

        # If the game already has a valid calendar in store, keep it and just sync persistent
        if (hasattr(store, 'current_day') and hasattr(store, 'current_month') and hasattr(store, 'current_year')
            and isinstance(store.current_day, int) and isinstance(store.current_month, int) and isinstance(store.current_year, int)
            and store.current_day > 0 and store.current_month > 0 and store.current_year > 0):
            persistent.current_day = store.current_day
            persistent.current_month = store.current_month
            persistent.current_year = store.current_year
            renpy.save_persistent()
            renpy.log(f"Calendar init (kept store): Day {store.current_day}, {month_names[store.current_month - 1]} {store.current_year}")
            return

        # Otherwise, ensure persistent exists and seed store from it (without resetting existing values)
        if not hasattr(persistent, "current_day") or persistent.current_day is None or persistent.current_day <= 0:
            persistent.current_day = 1
        if not hasattr(persistent, "current_month") or persistent.current_month is None or persistent.current_month <= 0:
            persistent.current_month = 1
        if not hasattr(persistent, "current_year") or persistent.current_year is None or persistent.current_year <= 0:
            persistent.current_year = 1

        store.current_day = persistent.current_day
        store.current_month = persistent.current_month
        store.current_year = persistent.current_year
        renpy.log(f"Calendar initialized: Day {store.current_day}, {month_names[store.current_month - 1]} {store.current_year}")

    # Initialize event tracking dictionaries
    if not hasattr(store, "event_flags"):
        store.event_flags = {}
    if not hasattr(store, "event_occurrences"):
        store.event_occurrences = {}
    if not hasattr(store, "event_last_occurred"):
        store.event_last_occurred = {}
    
    def reset_calendar_to_start():
        """Reset calendar to the very beginning (Day 1, Month 1, Year 1)"""
        persistent.current_day = 1
        persistent.current_month = 1  # 1-based (Frostveil = 1)
        persistent.current_year = 1
        store.current_day = 1
        store.current_month = 1
        store.current_year = 1
        renpy.save_persistent()  # Force save persistent data
        renpy.log("Calendar manually reset to Day 1, Frostveil Year 1")

    def sync_calendar():
        """Synchronize calendar between store and persistent variables"""
        # Always use store as the source of truth and sync to persistent
        persistent.current_day = store.current_day
        persistent.current_month = store.current_month
        persistent.current_year = store.current_year
        renpy.save_persistent()  # Force save persistent data
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



   

    
    
 
    



    def get_worker_folder(worker):
        """Resolve the worker's folder based on their data."""
        if isinstance(worker, dict):
            folder_name = worker.get("folder", "aspen")  # Fallback to aspen instead of default
            renpy.log(f"Worker name: {worker.get('name', 'Unknown')}, folder resolved: {folder_name}")
        else:
            folder_name = "aspen"  # Fallback to aspen instead of default
            renpy.log(f"Worker is not a dictionary, using aspen folder as fallback")
        
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
            "striptease": ["strip", "striptease"]  # Striptease busca "strip" o "striptease"
        }
        
        if skill_name in special_patterns:
            return special_patterns[skill_name]
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
        if hasattr(worker, 'get'):
            worker_folder = worker.get("folder", "aspen")  # Fallback to aspen instead of default
            worker_name = worker.get("name", "Unknown")
        else:
            worker_folder = "aspen"  # Fallback to aspen instead of default
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
        if hasattr(worker, 'get'):
            worker_folder = worker.get("folder", "aspen")  # Fallback to aspen instead of default
            worker_name = worker.get("name", "Unknown")
        else:
            worker_folder = "aspen"  # Fallback to aspen instead of default
            worker_name = "Unknown"
        
        base_folder = f"images/workers/{worker_folder}/"
        default_folder = "images/workers/default/"
        
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

        item_type = item_data.get("type", "unknown")
        if item_type in ["currency", "consumable"]:
            for i, entry in enumerate(inventory):
                if entry[0] == item_id:
                    new_quantity = entry[1] + quantity
                    inventory[i] = (entry[0], new_quantity, entry[2])
                    renpy.log(f"Added {quantity} of {item_id} to existing stack (new quantity: {new_quantity}).")
                    return
            inventory.append((item_id, quantity, False))
            renpy.log(f"Added new stack of {item_id} (quantity: {quantity}).")
        else:
            for _ in range(quantity):
                inventory.append((item_id, 1, False))
            renpy.log(f"Added equipment item {item_id} {quantity} time(s).")

    def toggle_equip_item(inventory, item_id, worker=None):
        """
        Toggle the equipped state of an item in the given inventory.
        For equipment items (like "weapon" or "armor"), only one item of that type may be equipped.
        Exception: "clothing" and "armor" are separate slots and can be equipped simultaneously.
        If a worker is provided, apply (or remove) the item's effects accordingly.
        Assumes inventory items are tuples: (item_id, quantity, equipped).
        """
        # Look up the item data for the given item_id.
        item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if not item_data:
            renpy.log("toggle_equip_item: Item data not found for " + item_id)
            return
        item_type = item_data.get("type", "")

        # Ensure all inventory entries are tuples.
        for i, entry in enumerate(inventory):
            if not isinstance(entry, tuple):
                converted = (entry.get("item_id"), entry.get("quantity"), entry.get("equipped", False))
                inventory[i] = converted

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
                
    def apply_item_effects(worker, item_id):
        """Apply the effects of an equipped item to a worker."""
        item = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if item and "effect" in item:
            for effect_type, effect_value in item["effect"].items():
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
                    if isinstance(effect_value, dict):
                        add_trait_with_duration(worker, effect_value.get("name", ""), effect_value.get("duration", 0))
                    else:
                        add_trait_with_duration(worker, effect_value, 0)

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
                    remove_trait(worker, effect_value)

    def remove_item_from_inventory(inventory, item_id, quantity=1):
        # First, ensure every entry in the inventory is a tuple
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
        
        # Now remove the item
        for i, entry in enumerate(inventory):
            if isinstance(entry, tuple) and entry[0] == item_id:
                new_quantity = entry[1] - quantity
                if new_quantity <= 0:
                    inventory.pop(i)
                else:
                    inventory[i] = (entry[0], new_quantity, entry[2])
                return

    def use_item(item_id, worker=None):
        """
        Uses a consumable item.
        Looks up the item in items_json; if its type is 'consumable', it applies any effect
        to the provided worker (if not None) and then removes one unit from the inventory.
        """
        # Look up the item in our loaded items_json.
        item = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if not item:
            renpy.log(f"ERROR: Item {item_id} not found in items_json")
            return
        
        if item.get("type") == "consumable":
            renpy.notify("Used " + item.get("name", "Unknown"))
        
        # Handle custom effects (like shop unlocks) - these don't require a worker
        if "effect" in item and "custom" in item["effect"]:
            custom_action = item["effect"]["custom"]
            # Create a temporary effect dict for apply_effects
            effect_dict = {"custom": custom_action}
            apply_effects(effect_dict, worker=worker)
            # Remove from manager inventory if it's a manager item
            remove_item_from_inventory(manager_inventory, item_id)
            return
        
        if worker:
            # Track tutorial objective 5 - potion usage
            if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item.get("name", "").lower().find("energy") != -1:
                store.potion_used_on_worker = True
                renpy.log("DEBUG: Tutorial - Energy potion used on worker")
                check_objective_completion()
            # Apply effects
            if "effect" in item:
                for effect_type, effect_value in item["effect"].items():
                    if effect_type == "money":
                        # Money effects go to the manager when used by a worker
                        money_change = effect_value
                        store.money += money_change
                        renpy.notify(f"Money changed by ${money_change}")
                        renpy.log(f"use_item: Applied money effect: ${money_change} (used by {worker.get('name', 'worker')})")
                        # Check objective completion after money change (for Objective 4: 5000 coins)
                        if hasattr(store, 'tutorial_active') and store.tutorial_active:
                            try:
                                check_objective_completion()
                            except Exception as e:
                                renpy.log(f"Error checking objective completion after item money effect: {e}")
                    elif effect_type == "health":
                        worker["health"] = min(calculate_max_health(worker), worker["health"] + effect_value)
                    elif effect_type == "energy":
                        worker["energy"] = min(calculate_max_energy(worker), worker["energy"] + effect_value)
                    elif effect_type == "skill_modifiers":
                        # Equipment bonuses are handled in calculate_skill_with_traits()
                        # No need to modify base skills here
                        pass
                    elif effect_type == "add_trait":
                        if isinstance(effect_value, dict):
                            add_trait_with_duration(worker, effect_value.get("name", ""), effect_value.get("duration", 0))
                        else:
                            add_trait_with_duration(worker, effect_value, 0)
                    elif effect_type == "remove_trait":
                        remove_trait(worker, effect_value)
            remove_item_from_inventory(worker.get("inventory", []), item_id)
        else:
            # If no worker and item is consumable, remove from manager inventory
            if item.get("type") == "consumable":
                remove_item_from_inventory(manager_inventory, item_id)


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

    

    

        # Filter traits that are not marked as only_assigned and are not NSFW (if applicable)
        possible_traits = [
            t for t in traits_list
            if not t.get("only_assigned", False) and (persistent.nsfw_enabled or not t.get("nsfw", False))
        ]
        random.shuffle(possible_traits)  # Shuffle to ensure randomness

        selected_traits = []
        attempts = 0
        max_attempts = 100  # Prevent infinite loops

        # Ensure at least 3 traits are assigned
        while len(selected_traits) < 3 and attempts < max_attempts and possible_traits:
            trait = possible_traits.pop()
            trait_name = trait["name"]

            # Check if the trait conflicts with any already selected traits
            if not any(conflict in selected_traits for conflict in trait.get("conflicts", [])):
                add_trait_with_duration(worker, trait_name, 0)
                selected_traits.append(trait_name)
                renpy.log(f"Assigned trait '{trait_name}' to {worker.get('name', 'Unknown')}")

            attempts += 1

        # If we couldn't assign 3 traits due to conflicts, log a warning
        if len(selected_traits) < 3:
            renpy.log(f"Warning: Only {len(selected_traits)} traits assigned to {worker.get('name', 'Unknown')} due to conflicts or lack of available traits.")

        # Try to add more traits up to 5, if possible
        while len(selected_traits) < 5 and possible_traits:
            trait = possible_traits.pop()
            trait_name = trait["name"]

            # Check if the trait conflicts with any already selected traits
            if not any(conflict in selected_traits for conflict in trait.get("conflicts", [])):
                add_trait_with_duration(worker, trait_name, 0)
                selected_traits.append(trait_name)
                renpy.log(f"Assigned additional trait '{trait_name}' to {worker.get('name', 'Unknown')}")

        return worker

   

    
    

    

    

    #################################
    # WORKER DEFAULTS & SPAWN LOGIC
    #################################

  
    

    def load_buy_workers():
        """
        Load workers available for purchase, prioritizing workers defined in JSON files.
        Generates procedural workers when needed, respecting the daily spawn limit.
        Refills once per day.
        """
        global daily_spawns, available_workers
        
        # Check if we need to refill (is it a new day?)
        current_date = (store.current_day, store.current_month, store.current_year)
        last_refill = (store.last_worker_refill_day, store.last_worker_refill_month, store.last_worker_refill_year)
        
        is_new_day = (last_refill[0] is None or current_date != last_refill)
        
        renpy.log(f"WORKER REFILL CHECK - Current: {current_date}, Last: {last_refill}, New day: {is_new_day}")
        
        if not is_new_day:
            # Same day - return existing workers, filter out hired ones
            hired_names = {w["name"] for w in workers}
            available_workers = [w for w in store.available_workers if w.get("name") not in hired_names]
            renpy.log(f"Same day - using existing workers: {[w.get('name') for w in available_workers]}")
            return available_workers
        
        # NEW DAY - Refill workers
        renpy.log(f"NEW DAY - Refilling workers")
        
        # Load all workers from JSON
        all_workers = load_workers(include_unique=True, include_encounter_only=False)
        hired_names = {w["name"] for w in workers}
        
        # Get available JSON workers (not hired, not dead, not recruit_only, not unique, not monsters)
        # Unique workers should only appear in special recruitment events, not in the normal buy menu
        # Monsters should ONLY appear in monster capture events, never in buy menu or recruitment events
        json_workers = [
            w for w in all_workers
            if not w.get("procedural", False)
            and not w.get("recruit_only", False)  # Exclude recruit_only workers
            and not w.get("unique", False)  # Exclude unique workers (they appear in recruitment events only)
            and not w.get("monster", False)  # Exclude monsters (they only appear in capture events)
            and w["name"] not in hired_names  # Exclude ALL hired workers
            and not is_worker_dead(w["name"])
        ]
        
        renpy.log(f"Available JSON workers: {len(json_workers)}")
        
        # Start fresh
        available_workers = []
        
        if len(json_workers) > 0:
            # Use random JSON workers (up to 5) - shuffle for variety each day
            random.shuffle(json_workers)
            available_workers = json_workers[:5]
            renpy.log(f"Using {len(available_workers)} JSON workers: {[w['name'] for w in available_workers]}")
        else:
            # JSON exhausted - generate procedural workers
            renpy.log("JSON workers exhausted - generating procedural workers")
            while len(available_workers) < 5 and daily_spawns < 5:
                new_worker = spawn_new_worker()
                if new_worker:
                    new_worker["market_worker"] = True
                    new_worker["procedural"] = True
                    available_workers.append(new_worker)
                    daily_spawns += 1
                    renpy.log(f"Generated procedural worker: {new_worker['name']}")
        
        # Apply defaults
        for worker in available_workers:
            ensure_worker_defaults(worker)
            worker["market_worker"] = True
        
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
        renpy.log(f"NSFW mode enabled: {persistent.nsfw_enabled}")
        renpy.log(f"Total workers before NSFW filter: {len(recruit_pool)}")
        renpy.log(f"Available workers for recruitment: {[w['name'] for w in available_recruit]}")
        renpy.log(f"NSFW status of available workers: {[(w['name'], w.get('nsfw', False)) for w in available_recruit]}")
        
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
            
            # Get the base skills (use original_skills if available, otherwise skills)
            # Always read from the actual dict, not a reference, to ensure we get current values
            if "original_skills" in worker and worker["original_skills"]:
                base_skills = worker["original_skills"]
            else:
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
                # Skills at 0 need 1 use to reach level 1, then uses_needed = current_level
                uses_needed = 1 if current_skill_level == 0 else current_skill_level
                
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
                    
                    # Re-read base_skills after modification to ensure we have the latest value
                    if "original_skills" in worker and worker["original_skills"]:
                        base_skills = worker["original_skills"]
                    else:
                        base_skills = worker.get("skills", {})
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
        all_workers = load_workers(include_unique=True, include_encounter_only=True)
        template_workers = [
            w for w in all_workers
            if not w.get("unique", False) 
            and not w.get("monster", False)
            and w.get("nsfw", False) == persistent.nsfw_enabled  # Match NSFW setting
        ]
        
        if not template_workers:
            # Fallback to default creation if no templates available
            return spawn_new_worker_default(filters)
        
        # Choose a random template
        template = random.choice(template_workers)
        
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
        new_worker.update({
            "name": final_name,
            "procedural": True,
            "unique": False,
            "encounter_only": False,
            # Randomize stats with high potential:
            # 50% chance: decent (12-28)
            # 30% chance: great (25-40)
            # 20% chance: exceptional (35-50)
            "skills": {
                skill_name: (
                    random.randint(12, 28) if (roll := random.random()) < 0.5
                    else random.randint(25, 40) if roll < 0.8
                    else random.randint(35, 50)
                )
                for skill_name in template["skills"].keys()
            },
            "cost": random.randint(500, 1500),
            "rebelliousness": random.randint(20, 80),
            "joy": random.randint(20, 80),
            "comfort_desired": random.randint(1, 5),
            "description": f"A skilled worker from the {template.get('folder', 'unknown')} region."
        })
        
        # Assign random traits
        new_worker["traits"] = assign_random_traits(new_worker)
        
        # Ensure all defaults are properly set
        ensure_worker_defaults(new_worker)
        
        return new_worker

    def spawn_new_worker_default(filters=None):
        """Fallback: Generate a basic procedural worker when no templates available."""
        filters = filters or {}
        # Choose a random gender
        gender = random.choice(["male", "female"])
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
        
        # Create the new worker with named skills only
        # 50% chance: decent (12-28)
        # 30% chance: great (25-40)
        # 20% chance: exceptional (35-50)
        new_worker = {
            "name": final_name,
            "folder": assigned_folder,
            "gender": gender,
            "names_list": f"{name_category}_{gender}",
            "skills": {
                skill_name: (
                    random.randint(12, 28) if (roll := random.random()) < 0.5
                    else random.randint(25, 40) if roll < 0.8
                    else random.randint(35, 50)
                )
                for skill_name in skill_names.keys()
            },
            "traits": [],  # Will be filled by assign_random_traits
            "description": f"A {final_name} from the {name_category} region.",
            "cost": random.randint(500, 1500),
            "level": 1,
            "energy": 50,
            "health": 100,
            "rebelliousness": random.randint(20, 80),
            "joy": random.randint(20, 80),
            "romance": 0,
            "relationship": 10,
            "comfort_level": 1,
            "comfort_desired": 1,
            "skill_uses": {skill_name: 0 for skill_name in skill_names.keys()},
            "success_count": 0,
            "procedural": True,
            "unique": False,
            "encounter_only": False,
            "monster": False,
            "nsfw": persistent.nsfw_enabled  # Set NSFW based on game mode
        }
        
        # Assign random traits
        new_worker["traits"] = assign_random_traits(new_worker)
        
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

    def unassign_worker(worker):
        """Fully remove worker from their building assignment."""
        remove_worker_from_building(worker)
        building_name = worker.get("assigned_building")
        if building_name and building_name in available_buildings:
            building = available_buildings[building_name]
            if worker in building["assigned_servants"]:
                building["assigned_servants"].remove(worker)
            if worker["name"] in building["servant_jobs"]:
                del building["servant_jobs"][worker["name"]]
        worker["assigned_building"] = "Unassigned"

    def remove_worker_from_building(worker):
        if worker.get("assigned_building", "Unassigned") != "Unassigned" and worker["assigned_building"] in available_buildings:
            building = available_buildings[worker["assigned_building"]]
            if worker in building["assigned_servants"]:
                building["assigned_servants"].remove(worker)

    def check_worker_health():
        global workers
        to_remove = []
        for worker in workers:
            if worker["health"] <= 0:
                unassign_worker(worker)
                to_remove.append(worker)
                # Add the worker to the dead workers list
                add_to_dead_workers(worker["name"])
        for worker in to_remove:
            workers.remove(worker)
        return len(to_remove)

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
            "skill_bonus": 0  # Initialize bonus to 0
        }
        calculate_reputation(name)  # Set initial value

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

    def split_text_for_dialogue(text, max_chars=200):
        """
        Divide un texto largo en múltiples mensajes que quepan en el cuadro de diálogo.
        Intenta dividir por frases completas primero, luego por palabras.
        max_chars: caracteres máximos por mensaje (aproximadamente 3-4 líneas)
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
        renpy.notify(f"Upgraded {custom_names[building_name]} to level {building['base_level']}!")

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
                
                total_skill = selected_building["skill"] + selected_building["skill_bonus"]

                roll = random.randint(1, 100)
                
                # --- DEBUG LOGGING ---
                renpy.log(f"--- Building Skill Check ---")
                renpy.log(f"Building: {selected_building_name}")
                renpy.log(f"Base Skill: {selected_building['skill']}")
                renpy.log(f"Skill Bonus: {selected_building['skill_bonus']}")
                renpy.log(f"Total Skill: {total_skill}")
                renpy.log(f"Roll (1-100): {roll}")
                renpy.log(f"Result: {'Success' if roll <= total_skill else 'Failure'}")
                renpy.log(f"--------------------------")
                # --- END DEBUG LOGGING ---

                acting_worker_name = "Building Team"
                event_worker_name = "Unknown"  # Default if no worker is involved

                # Check for assigned servants, limit to this specific building only
                assigned_servants = selected_building.get("assigned_servants", [])
                if not assigned_servants:
                    # Fallback: Find workers assigned to this specific building from store.workers
                    for worker in store.workers:
                        if worker.get("assigned_building") == selected_building_name:
                            assigned_servants.append(worker)

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
                    if len(outcome_message) > 260:
                        import re
                        sentences = re.split(r'(?<=[\.!?])\s+', outcome_message)
                        chunks = []
                        current = ""
                        for s in sentences:
                            if len(current) + len(s) + 1 <= 260:
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
                            min_success_chance = 90
                            effective_success_chance = max(skill_level, min_success_chance)
                            renpy.log(f"Worker {selected_worker['name']} skill {skill_level} meets threshold {threshold} - using {effective_success_chance}% success chance")
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
                        roll = random.randint(1, 100)
                        if roll <= skill_level:
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
                roll = random.random()
                if roll <= success_chance:
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
            new_trait = trait_data["name"]
            duration = trait_data.get("duration", 0)
            
            # Only add if not already present and meets conditions
            if new_trait not in worker.get("traits", []):
                add_trait_with_duration(worker, new_trait, duration)
                renpy.notify(f"{worker['name']} gained {new_trait} from expired trait")

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
                trait_name = trait_data.get("name")
                duration = trait_data.get("duration", 0)  # Default to 0 if duration is not specified
                target = trait_data.get("target", None)
                
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
                # Ensure persistent.unlocked_shops exists before accessing it
                if not hasattr(persistent, 'unlocked_shops') or persistent.unlocked_shops is None:
                    persistent.unlocked_shops = {"shop1": True, "shop2": False, "shop3": False}
                persistent.unlocked_shops["shop2"] = True
                store.unlocked_shops["shop2"] = True  # Sync to store variable
                renpy.log(f"Unlocked shop2 - persistent: {persistent.unlocked_shops}, store: {store.unlocked_shops}")
                renpy.notify("The Adventurer's Market is now available!")
            elif custom_action == "unlock_shop3":
                # Ensure persistent.unlocked_shops exists before accessing it
                if not hasattr(persistent, 'unlocked_shops') or persistent.unlocked_shops is None:
                    persistent.unlocked_shops = {"shop1": True, "shop2": False, "shop3": False}
                persistent.unlocked_shops["shop3"] = True
                store.unlocked_shops["shop3"] = True  # Sync to store variable
                renpy.log(f"Unlocked shop3 - persistent: {persistent.unlocked_shops}, store: {store.unlocked_shops}")
                renpy.notify("The Elite Emporium is now available!")
            elif custom_action == "give_item":
                # Add a specific item to the manager inventory
                item_id = effect_dict.get("item_id")
                try:
                    if item_id:
                        add_item_to_inventory(manager_inventory, item_id)
                        renpy.notify(f"Received {item_id.replace('_',' ').title()}!")
                        renpy.log(f"Custom give_item: added {item_id} to inventory")
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

        # Handle trait addition with duration
        if "add_trait" in effect_dict:
            trait_data = effect_dict["add_trait"]
            trait_name = trait_data["name"]
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            
            if trait_def and worker is not None:  # Check if worker is not None before adding trait
                duration = trait_data.get("duration", trait_def.get("duration", 0))
                add_trait_with_duration(worker, trait_name, duration)
            elif worker is None:
                renpy.log(f"Cannot add trait '{trait_name}' - worker is None")
        
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
        
        # Build a list of weights from the items.
        weights = []
        for item in items_list:
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
        chosen_items = random.choices(items_list, weights=weights, k=num_rolls)
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
        # Sync worker folders from JSON first (fixes Selene and any other mismatched folders)
        sync_worker_folders_from_json()
        # Then ensure defaults
        for worker in store.workers:
            ensure_worker_defaults(worker)
        for worker in store.available_workers:
            ensure_worker_defaults(worker)
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
        Returns a list of (skill_name, level) tuples.
        """
        base_skills = worker.get("original_skills", worker.get("skills", {}))
        return [(sid, lvl) for sid, lvl in base_skills.items() if is_skill_visible(sid)]

################################################################################
### GLOBAL VARIABLES
################################################################################
default player_title = ""
default player_name = ""
default money = 5000
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
default available_workers = []
default displayed_workers = []
default roster_current_page = 0
default current_report_index = 0
default left_worker = None  # Storage by default
default right_worker = None  # Will be set in init python
default daily_report = []
default building_filter = "All Buildings"
default worker_building_filter = "All Workers"
define roster_page_size = 50
default current_worker_index = 0
default current_worker = None  # Updated after workers are loaded
default daily_spawns = 0
define MAX_DAILY_SPAWNS = 5
default last_worker_refill_day = None
default last_worker_refill_month = None
default last_worker_refill_year = None
default take_a_walk_in_progress = False
default last_take_a_walk_day = None
default worker_interactions_today = {}  # Track daily interactions per worker: {worker_name: {day: count}}
default MAX_DAILY_INTERACTIONS = 2  # Maximum interactions per worker per day
default custom_names = {
    "Building 1": "Building 1"
}
default acting_worker = ""  # Default value for acting_worker
default event_flags = {}  # Storage for event flags/tokens that are used for event chains and conditions
default plaza_servants_text_hover = False  # Controls hover state of PlazaServants imagebutton when textbutton is hovered
default shops_text_hover = False  # Controls hover state of shop imagebuttons when "Visit Shops" textbutton is hovered
default recruit_workers_text_hover = False  # Controls hover state of PlazaFountain imagebutton when "Recruit Workers" textbutton is hovered
default take_a_walk_text_hover = False  # Controls hover state of PlazaFountain imagebutton when "Take a Walk" textbutton is hovered
default buy_buildings_text_hover = False  # Controls hover state of buyable buildings when "Buy Buildings" textbutton is hovered
default tooltips_enabled_by_screen = {}  # Dictionary to store tooltip state per screen (defaults to True if not set)

init python:
    def toggle_tooltips_for_screen(screen_name):
        """Toggle tooltips for a specific screen. Does not return anything."""
        # Default state: False for "tavern" and "Manager", True for all others
        default_state = False if screen_name in ["tavern", "Manager"] else True
        current_state = tooltips_enabled_by_screen.get(screen_name, default_state)
        tooltips_enabled_by_screen[screen_name] = not current_state
        # Don't return anything - Ren'Py actions should not return values
    
    def get_tooltips_state_for_screen(screen_name):
        """Get tooltips state for a specific screen. Returns True if enabled (default)."""
        # Default state: False for "tavern" and "Manager", True for all others
        default_state = False if screen_name in ["tavern", "Manager"] else True
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
            call screen market
        "Return to Tavern":
            jump tavern_screen
    
    return
    return