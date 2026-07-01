# script.rpy


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

    # Shared file list cache - renpy.list_files() is expensive; call once, reuse everywhere.
    _renpy_file_list_cache = None

    def get_cached_file_list():
        # Truthy check (not `is None`): an empty list pickled into an older save
        # would otherwise pass forever. renpy.list_files() returning empty is
        # never legitimate, so empty == stale → re-list from disk.
        global _renpy_file_list_cache
        if not _renpy_file_list_cache:
            _renpy_file_list_cache = renpy.list_files()
        return _renpy_file_list_cache

    store.get_cached_file_list = get_cached_file_list

    #############################
    # Constants
    #############################
    SKILL_MAX = 100  # Cap for base worker skills (used by modify_base_skill, use_item, etc.)

    #############################
    # Event Success Configuration
    #############################
    # Base success bonus added to all skill-based event checks
    # This increases the baseline success chance for all events
    EVENT_SUCCESS_BASE_BONUS_WORKER = 20  # Easy baseline (+20)
    EVENT_SUCCESS_BASE_BONUS_BUILDING = 25  # Easy baseline (+25, half of original 50)
    EVENT_SUCCESS_MIN_CHANCE = 0.6  # Easy baseline minimum success chance (60%)

    def get_event_success_bonus_worker():
        """Difficulty-scaled worker baseline bonus for event checks."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 0
        if diff == "hard":
            return 0
        if diff == "normal":
            return 10
        if diff == "easy":
            return EVENT_SUCCESS_BASE_BONUS_WORKER
        # story
        return 30

    def get_event_success_bonus_building():
        """Difficulty-scaled building baseline bonus for event checks (halved from original)."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 10
        if diff == "hard":
            return 15
        if diff == "normal":
            return 20
        if diff == "easy":
            return EVENT_SUCCESS_BASE_BONUS_BUILDING
        # story
        return 35

    def get_event_success_min_chance():
        """Difficulty-scaled minimum success chance for probability-based events."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 0.35
        if diff == "hard":
            return 0.45
        if diff == "normal":
            return 0.55
        if diff == "easy":
            return EVENT_SUCCESS_MIN_CHANCE
        # story
        return 0.75

    def _coerce_event_threshold(choice):
        """Return a safe integer threshold for event choices."""
        if not choice or not hasattr(choice, "get"):
            return 0
        try:
            raw = choice.get("threshold", 0)
            return int(raw or 0)
        except Exception:
            return 0

    def get_event_worker_skill_check_info(worker, choice):
        """
        Central source for worker event skill checks.

        The displayed skill and the resolver both use calculate_skill_with_traits()
        with its default bonuses, so event UI mirrors the actual roll basis.
        """
        info = {
            "valid": False,
            "skill_name": None,
            "display_skill": 0,
            "roll_skill": 0,
            "threshold": 0,
            "worker_bonus": 0,
            "target_chance": 0,
            "auto_success": False,
            "label": "",
        }
        if not worker or not hasattr(worker, "get") or not choice or not hasattr(choice, "get"):
            return info
        skill_name = choice.get("condition")
        if not skill_name or skill_name == "building_skill":
            return info

        threshold = _coerce_event_threshold(choice)
        try:
            roll_skill = int(calculate_skill_with_traits(worker, skill_name))
        except Exception:
            roll_skill = 0
        worker_bonus = get_event_success_bonus_worker()
        auto_success = False

        if threshold > 0 and roll_skill >= threshold:
            skill_above_threshold = roll_skill - threshold
            if skill_above_threshold >= 15:
                target_chance = 100
                auto_success = True
            else:
                skill_with_bonus = min(100, roll_skill + worker_bonus)
                target_chance = max(skill_with_bonus, 90)
        else:
            target_chance = min(100, roll_skill + worker_bonus)

        try:
            display_name = skill_names.get(skill_name, skill_name)
        except Exception:
            display_name = str(skill_name)

        bonus_text = ""
        if worker_bonus:
            bonus_text = " (+%d event)" % worker_bonus
        if auto_success:
            chance_text = "Guaranteed"
        else:
            chance_text = "%d%%" % int(target_chance)
        if threshold > 0:
            label = "%s %d%s vs %d -> %s" % (display_name, roll_skill, bonus_text, threshold, chance_text)
        else:
            label = "%s %d%s -> %s" % (display_name, roll_skill, bonus_text, chance_text)

        info.update({
            "valid": True,
            "skill_name": skill_name,
            "display_skill": roll_skill,
            "roll_skill": roll_skill,
            "threshold": threshold,
            "worker_bonus": worker_bonus,
            "target_chance": int(target_chance),
            "auto_success": auto_success,
            "label": label,
        })
        return info

    def get_event_building_skill_check_info(building):
        """Central source for building_skill event checks."""
        info = {
            "valid": False,
            "base_skill": 0,
            "skill_bonus": 0,
            "display_skill": 0,
            "building_bonus": 0,
            "target_chance": 0,
            "label": "",
        }
        if not building or not hasattr(building, "get"):
            return info
        try:
            base_skill = int(building.get("skill", 0) or 0)
        except Exception:
            base_skill = 0
        try:
            skill_bonus = int(building.get("skill_bonus", 0) or 0)
        except Exception:
            skill_bonus = 0
        display_skill = base_skill + skill_bonus
        building_bonus = get_event_success_bonus_building()
        target_chance = min(100, display_skill + building_bonus)
        bonus_text = ""
        if building_bonus:
            bonus_text = " (+%d event)" % building_bonus
        label = "Building Skill %d%s -> %d%%" % (display_skill, bonus_text, int(target_chance))
        info.update({
            "valid": True,
            "base_skill": base_skill,
            "skill_bonus": skill_bonus,
            "display_skill": display_skill,
            "building_bonus": building_bonus,
            "target_chance": int(target_chance),
            "label": label,
        })
        return info

    def get_difficulty_loot_multiplier():
        """
        Scales roll_loot effective rolls only. Daily-story bonus_items and monster_worker use raw JSON chances.
        """
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 0.15
        if diff == "hard":
            return 0.25
        if diff == "normal":
            return 0.35
        # story / easy / unknown
        return 0.35

    def get_difficulty_earnings_mult():
        """Multiplier applied to daily story positive earnings (not losses)."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 0.7
        if diff == "hard":
            return 0.85
        if diff == "normal":
            return 1.0
        if diff == "easy":
            return 1.15
        # story
        return 1.3

    #############################
    # Helper Functions & Loading
    #############################

    def get_building_multipliers(building):
        """
        Calculate multipliers based on building level.
        
        *** ONLY APPLIES TO RANDOM EVENTS, NOT DAILY WORKER EARNINGS ***
        
        Building Level Bonuses for Random Events:
        - Level 1: No bonus (1.0x)
        - Level 2: Money +10%, Reputation +30% (1.1x money, 1.3x reputation)
        - Level 3: Money +20%, Reputation +60% (1.2x money, 1.6x reputation)
        - Level 4: Money +30%, Reputation +90% (1.3x money, 1.9x reputation)
        - Level 5: Money +40%, Reputation +120% (1.4x money, 2.2x reputation)
        
        Used by: apply_effects() function for random events only
        """
        building_level = building.get("base_level", 1) if building else 1
        if building_level <= 1:
            return {"money": 1.0, "reputation": 1.0}
        
        money_multiplier = 1.0 + (building_level - 1) * 0.1  # +10% money per level above 1
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

    # Load buildings from all JSON files in data/buildings/ (merge by id; later files override earlier for same id).
    # Excludes data/buildings/daily_story_extensions/ which is used for story extensions only.
    def _find_building_type_entry(building_type_id):
        for bt in store.building_types_json.get("building_types", []):
            if bt.get("id") == building_type_id:
                return bt
        return None

    def _find_profession_entry(building_type_entry, profession_id):
        if not building_type_entry:
            return None
        for prof in building_type_entry.get("professions", []):
            if prof.get("id") == profession_id:
                return prof
        return None

    def _merge_daily_stories_into_profession(profession_entry, stories_to_merge, merge_mode):
        if not profession_entry:
            return 0
        incoming = list(stories_to_merge or [])
        if not incoming:
            return 0
        if merge_mode == "replace_all":
            profession_entry["daily_stories"] = incoming
            return len(incoming)
        daily_stories = profession_entry.get("daily_stories")
        is_list_like = (hasattr(daily_stories, "__iter__") and not hasattr(daily_stories, "get") and not isinstance(daily_stories, (str, bytes)))
        daily_stories = list(daily_stories) if is_list_like else []
        profession_entry["daily_stories"] = daily_stories
        existing_index_by_id = {}
        for idx, story in enumerate(daily_stories):
            sid = story.get("id") if hasattr(story, "get") else None
            if sid:
                existing_index_by_id[sid] = idx
        merged_count = 0
        for story in incoming:
            if not hasattr(story, "get"):
                continue
            story_id = story.get("id")
            if merge_mode == "append":
                if story_id and story_id in existing_index_by_id:
                    continue
                daily_stories.append(story)
                if story_id:
                    existing_index_by_id[story_id] = len(daily_stories) - 1
                merged_count += 1
            else:
                if story_id and story_id in existing_index_by_id:
                    daily_stories[existing_index_by_id[story_id]] = story
                else:
                    daily_stories.append(story)
                    if story_id:
                        existing_index_by_id[story_id] = len(daily_stories) - 1
                merged_count += 1
        return merged_count

    def _apply_daily_story_extensions():
        extension_files = sorted([
            f for f in get_cached_file_list()
            if f.startswith("data/buildings/daily_story_extensions/") and f.endswith(".json")
        ])
        if not extension_files:
            return 0
        total_merged = 0
        for file_path in extension_files:
            try:
                with renpy.file(file_path) as extension_file:
                    extension_data = json.load(extension_file)
            except Exception as e:
                renpy.log("Error loading daily story extension '" + file_path + "': " + str(e))
                continue
            extension_entries = []
            if hasattr(extension_data, "__iter__") and not hasattr(extension_data, "get") and not isinstance(extension_data, (str, bytes)):
                extension_entries = list(extension_data)
            elif hasattr(extension_data, "get"):
                raw_entries = extension_data.get("daily_story_extensions", None)
                if hasattr(raw_entries, "__iter__") and not hasattr(raw_entries, "get") and not isinstance(raw_entries, (str, bytes)):
                    extension_entries = list(raw_entries)
                elif hasattr(raw_entries, "get"):
                    extension_entries = [raw_entries]
                elif all(k in extension_data for k in ("building_id", "profession_id", "daily_stories")):
                    extension_entries = [extension_data]
                else:
                    continue
            else:
                continue
            for entry in extension_entries:
                if not hasattr(entry, "get"):
                    continue
                building_id = entry.get("building_id")
                profession_id = entry.get("profession_id")
                merge_mode = str(entry.get("merge_mode", "upsert")).lower().strip()
                if merge_mode not in ("upsert", "append", "replace_all"):
                    merge_mode = "upsert"
                stories = entry.get("daily_stories", [])
                if not building_id or not profession_id:
                    continue
                btype = _find_building_type_entry(building_id)
                if not btype:
                    renpy.log("Daily story extension: building not found '" + str(building_id) + "' in " + file_path)
                    continue
                profession = _find_profession_entry(btype, profession_id)
                if not profession:
                    renpy.log("Daily story extension: profession not found '" + str(building_id) + "/" + str(profession_id) + "' in " + file_path)
                    continue
                total_merged += _merge_daily_stories_into_profession(profession, stories, merge_mode)
        return total_merged

    buildings_by_id = {}
    for file in sorted(get_cached_file_list()):
        if not file.startswith("data/buildings/") or not file.endswith(".json"):
            continue
        if file.startswith("data/buildings/daily_story_extensions/"):
            continue
        try:
            with renpy.file(file) as f:
                data = json.load(f)
            for bt in data.get("building_types", []):
                if not persistent.nsfw_enabled and bt.get("nsfw", False):
                    continue
                for profession in bt.get("professions", []):
                    profession["original_max_daily_workers"] = profession.get("max_daily_workers", 1)
                buildings_by_id[bt.get("id")] = bt
        except Exception as e:
            renpy.log("Error loading " + file + ": " + str(e))

    building_types_json = {"building_types": list(buildings_by_id.values())}
    _ext_merged = _apply_daily_story_extensions()
    if _ext_merged:
        renpy.log("Daily story extensions applied. Stories merged: " + str(_ext_merged))

    # Initialize items_json with an empty list
    items_json = {"items": [], "excluded_from_shops": []}

    # Iterate over files in the "data/items/" folder
    for file in get_cached_file_list():
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
        if worker and hasattr(worker, "get"):
            gender = worker.get("gender", "").lower()
            if gender == "male":
                return "guy"
        return "blossom"  # Default for females or unknown
    
    def get_worker_folder(worker):
        """Resolve the worker's folder based on their data."""
        fallback = get_fallback_folder(worker)
        if hasattr(worker, "get"):
            folder_name = worker.get("folder", fallback)
            renpy.log(f"Worker name: {worker.get('name', 'Unknown')}, folder resolved: {folder_name}")
        else:
            folder_name = fallback
            renpy.log(f"Worker is not a dictionary, using {fallback} folder as fallback")
        
        full_folder = f"images/workers/{folder_name}/"
        renpy.log(f"Resolved worker folder: {full_folder}")
        return full_folder

    # get_skill_search_patterns lives in event_visuals.rpy.

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
        
        if getattr(config, "developer", False):
            renpy.log(f"=== get_worker_image DEBUG ===")
            renpy.log(f"Worker: {worker_name}, Folder: {worker_folder}")
            renpy.log(f"Looking in: {base_folder}")
        
        # _worker_allows_profile_variant lives in event_visuals.rpy.

        trait_file_prefixes = ("pregnant_", "futa_", "transformed_", "magical_")

        # Try worker's profile image using robust flexible matching
        profile_matches = get_pattern_matches_flexible(base_folder, "profile")
        profile_matches = [f for f in profile_matches if _worker_allows_profile_variant(worker, f)]
        if getattr(config, "developer", False):
            renpy.log(f"Profile matches found: {len(profile_matches) if profile_matches else 0}")

        # PRIORITY: When worker has Pregnant/Transformed/Magical/Futa, use ONLY trait-prefixed
        # profile images (e.g. pregnant_profile). Do not mix with plain profile.
        trait_prefixes = get_trait_prefixes(worker)
        if trait_prefixes and profile_matches:
            trait_profile_matches = [
                f for f in profile_matches
                if any(os.path.basename(f).lower().startswith(pp + "_") for pp in trait_prefixes)
            ]
            if trait_profile_matches:
                selected = renpy.random.choice(trait_profile_matches)
                if getattr(config, "developer", False):
                    renpy.log(f"Selected trait-priority profile image: {selected}")
                return selected

        if profile_matches:
            selected = renpy.random.choice(profile_matches)
            if getattr(config, "developer", False):
                renpy.log(f"Selected profile image: {selected}")
            return selected
        
        # Try any image in worker folder as fallback (excluding failure images)
        all_worker_images = get_pattern_matches_flexible(base_folder, "", exclude_failure=True)
        all_worker_images = [f for f in all_worker_images if not should_exclude_trait_file(f, trait_file_prefixes, [])]
        if all_worker_images:
            selected = renpy.random.choice(all_worker_images)
            if getattr(config, "developer", False):
                renpy.log(f"Found fallback worker image: {selected}")
            return selected
        
        # If no images exist, return None
        if getattr(config, "developer", False):
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
                if hasattr(entry, "get"):
                    # Handle dict format: {"item_id": ..., "quantity": ..., "equipped": ...}
                    converted = (entry.get("item_id"), entry.get("quantity", 1), entry.get("equipped", False))
                    inventory[i] = converted
                elif hasattr(entry, "__getitem__") and not isinstance(entry, str):
                    # Handle list/RevertableList format: [item_id] or [item_id, quantity] or [item_id, quantity, equipped]
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

        is_manager_inventory = (hasattr(store, 'manager_inventory') and 
                               (inventory is store.manager_inventory or 
                                id(inventory) == id(getattr(store, 'manager_inventory', None))))
        
        def _as_equipped_flag(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.strip().lower() in ("true", "1", "yes", "y", "on")
            if isinstance(v, (int, float)):
                return v != 0
            return bool(v)

        # Stack ALL item types in unequipped entries. Equipped copies remain split entries.
        match_indices = []
        for idx, e in enumerate(inventory):
            if not isinstance(e, tuple) or len(e) < 2:
                continue
            if e[0] != item_id:
                continue
            eq_flag = _as_equipped_flag(e[2]) if len(e) >= 3 else False
            if not eq_flag:
                match_indices.append(idx)
        if match_indices:
            primary_idx = match_indices[0]
            total_existing = 0
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
            inventory[primary_idx] = (item_id, new_quantity, False)
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

        if is_manager_inventory and item_id == "cipher_lattice":
            try:
                _lat_fn = getattr(store, "academy_lib_on_cipher_lattice_acquired", None)
                if callable(_lat_fn):
                    _lat_fn()
            except Exception as e:
                renpy.log("academy_lib_on_cipher_lattice_acquired: " + str(e))

    def toggle_equip_item(inventory, item_id, worker=None, item_index=None):
        def _as_equipped_flag(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.strip().lower() in ("true", "1", "yes", "y", "on")
            if isinstance(v, (int, float)):
                return v != 0
            return bool(v)

        def _merge_unequipped_stacks_for_item(inv, target_id):
            if inv is None:
                return
            primary_idx = None
            total_qty = 0
            remove_indices = []
            for k, ent in enumerate(inv):
                if not isinstance(ent, tuple) or len(ent) < 2:
                    continue
                if str(ent[0]) != str(target_id):
                    continue
                ent_eq = _as_equipped_flag(ent[2]) if len(ent) >= 3 else False
                if ent_eq:
                    continue
                try:
                    q = int(ent[1]) if ent[1] is not None else 0
                except Exception:
                    q = 0
                if q < 0:
                    q = 0
                total_qty += q
                if primary_idx is None:
                    primary_idx = k
                else:
                    remove_indices.append(k)
            if primary_idx is None:
                return
            if total_qty <= 0:
                total_qty = 1
            base_id = inv[primary_idx][0]
            inv[primary_idx] = (base_id, total_qty, False)
            for k in reversed(remove_indices):
                del inv[k]

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
                if hasattr(entry, "__getitem__") and not isinstance(entry, (tuple, str)) and not hasattr(entry, "get") and len(entry) >= 2:
                    # Convert list to tuple: [item_id, quantity, equipped] -> (item_id, quantity, equipped)
                    equipped = entry[2] if len(entry) >= 3 else False
                    converted = (entry[0], entry[1], equipped)
                    inventory[i] = converted
                elif hasattr(entry, "get"):
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
        if item_index is not None:
            try:
                _idx = int(item_index)
            except Exception:
                _idx = None
            if _idx is not None and 0 <= _idx < len(inventory):
                _it = inventory[_idx]
                if isinstance(_it, tuple) and len(_it) >= 1 and _it[0] == item_id:
                    target_index = _idx
        if target_index is None:
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
        if not _as_equipped_flag(target_item[2] if len(target_item) >= 3 else False):
            # Unequip any other equipped item of the same type.
            # Special case: "clothing" and "armor" are separate slots, so they don't conflict with each other.
            auto_unequipped_ids = []
            for j, other in enumerate(inventory):
                if j != target_index and _as_equipped_flag(other[2] if len(other) >= 3 else False):
                    other_data = next((i for i in items_json["items"] if i["id"] == other[0]), None)
                    if other_data:
                        other_type = other_data.get("type")
                        # Only unequip if it's the same type, EXCEPT if one is "clothing" and the other is "armor"
                        if other_type == item_type:
                            renpy.log(f"Unequipping other item at index {j}: {other}")
                            inventory[j] = (other[0], other[1], False)
                            remove_item_effects(worker, other[0])
                            auto_unequipped_ids.append(other[0])
            # Equip exactly one copy from stack; do not equip the whole stack.
            try:
                _target_qty = int(target_item[1]) if target_item[1] is not None else 1
            except Exception:
                _target_qty = 1
            if _target_qty > 1:
                inventory[target_index] = (target_item[0], _target_qty - 1, False)
                inventory.insert(target_index + 1, (target_item[0], 1, True))
            else:
                inventory[target_index] = (target_item[0], 1, True)
            if worker is not None:
                apply_item_effects(worker, target_item[0])
            for _old_item_id in auto_unequipped_ids:
                _merge_unequipped_stacks_for_item(inventory, _old_item_id)
            _merge_unequipped_stacks_for_item(inventory, target_item[0])
            renpy.log(f"Equipped one copy of {target_item[0]}; stack-aware equip applied.")
        else:
            # If the item is equipped, unequip it and merge into an unequipped stack when possible.
            try:
                _eq_qty = int(target_item[1]) if target_item[1] is not None else 1
            except Exception:
                _eq_qty = 1
            if _eq_qty < 1:
                _eq_qty = 1
            merge_idx = None
            for j, other in enumerate(inventory):
                if j == target_index:
                    continue
                if not isinstance(other, tuple) or len(other) < 2:
                    continue
                if other[0] != target_item[0]:
                    continue
                other_eq = _as_equipped_flag(other[2]) if len(other) >= 3 else False
                if not other_eq:
                    merge_idx = j
                    break
            if merge_idx is not None:
                try:
                    _merge_qty = int(inventory[merge_idx][1]) if inventory[merge_idx][1] is not None else 0
                except Exception:
                    _merge_qty = 0
                inventory[merge_idx] = (target_item[0], max(0, _merge_qty) + _eq_qty, False)
                del inventory[target_index]
            else:
                inventory[target_index] = (target_item[0], _eq_qty, False)
            if worker is not None:
                remove_item_effects(worker, target_item[0])
            _merge_unequipped_stacks_for_item(inventory, target_item[0])
            renpy.log(f"Unequipped one copy of {target_item[0]}; merged back into stack when available.")

        renpy.restart_interaction()

    def unequip_item_by_match(inventory, item_id, quantity=None, worker=None):
        """
        Unequip a specific equipped item by matching item_id and (optionally) quantity.
        Avoids unequipping another copy with the same item_id.
        """
        def _as_equipped_flag(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.strip().lower() in ("true", "1", "yes", "y", "on")
            if isinstance(v, (int, float)):
                return v != 0
            return bool(v)

        for i, item in enumerate(inventory):
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                if str(item[0]) == str(item_id) and _as_equipped_flag(item[2]):
                    if quantity is None or item[1] == quantity:
                        inventory[i] = (item[0], item[1], False)
                        if worker is not None:
                            remove_item_effects(worker, item[0])
                        # Keep worker inventories compact after forced unequip by match.
                        try:
                            _target_id = item[0]
                            _total = 0
                            _base_idx = None
                            _remove = []
                            for k, ent in enumerate(inventory):
                                if not isinstance(ent, tuple) or len(ent) < 2:
                                    continue
                                if str(ent[0]) != str(_target_id):
                                    continue
                                _raw_eq = ent[2] if len(ent) >= 3 else False
                                if isinstance(_raw_eq, bool):
                                    _is_eq = _raw_eq
                                elif isinstance(_raw_eq, str):
                                    _is_eq = _raw_eq.strip().lower() in ("true", "1", "yes", "y", "on")
                                elif isinstance(_raw_eq, (int, float)):
                                    _is_eq = _raw_eq != 0
                                else:
                                    _is_eq = bool(_raw_eq)
                                if _is_eq:
                                    continue
                                try:
                                    _q = int(ent[1]) if ent[1] is not None else 0
                                except Exception:
                                    _q = 0
                                if _q < 0:
                                    _q = 0
                                _total += _q
                                if _base_idx is None:
                                    _base_idx = k
                                else:
                                    _remove.append(k)
                            if _base_idx is not None:
                                if _total <= 0:
                                    _total = 1
                                inventory[_base_idx] = (_target_id, _total, False)
                                for k in reversed(_remove):
                                    del inventory[k]
                        except Exception:
                            pass
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

    def _get_item_granted_traits_map(worker, create=False):
        if not worker or not hasattr(worker, "get"):
            return {}
        key = "_item_granted_traits_by_item"
        granted_map = worker.get(key)
        if hasattr(granted_map, "get"):
            return granted_map
        if create:
            worker[key] = {}
            return worker[key]
        return {}

    def _record_item_granted_trait(worker, item_id, trait_name):
        """Track only traits that equipment actually added, so unequip can undo safely."""
        if not worker or not item_id or not trait_name:
            return
        granted_map = _get_item_granted_traits_map(worker, create=True)
        existing = granted_map.get(item_id, [])
        if not hasattr(existing, "__iter__") or isinstance(existing, str):
            existing = []
        else:
            existing = list(existing)
        if trait_name not in existing:
            existing.append(trait_name)
        granted_map[item_id] = existing
        renpy.log(f"TRAITS: Recorded item-granted trait for '{item_id}': {existing}")

    def _trait_has_item_source(worker, trait_name, exclude_item_id=None):
        if not worker or not trait_name:
            return False
        granted_map = _get_item_granted_traits_map(worker, create=False)
        if not hasattr(granted_map, "items"):
            return False
        for grant_item_id, granted_traits in granted_map.items():
            if exclude_item_id is not None and str(grant_item_id) == str(exclude_item_id):
                continue
            if not hasattr(granted_traits, "__iter__") or isinstance(granted_traits, str):
                continue
            if trait_name in granted_traits:
                return True
        return False

    def _pop_item_granted_traits(worker, item_id):
        if not worker or not item_id:
            return []
        key = "_item_granted_traits_by_item"
        granted_map = _get_item_granted_traits_map(worker, create=False)
        if not hasattr(granted_map, "pop"):
            return []
        granted_traits = granted_map.pop(item_id, []) or []
        if not granted_map and key in worker:
            del worker[key]
        if not hasattr(granted_traits, "__iter__") or isinstance(granted_traits, str):
            return []
        return list(granted_traits)

    def _promote_item_granted_trait(worker, trait_name):
        """A permanent inventory trait source overrides temporary equipment ownership."""
        if not worker or not trait_name:
            return
        key = "_item_granted_traits_by_item"
        granted_map = _get_item_granted_traits_map(worker, create=False)
        if not hasattr(granted_map, "items"):
            return
        changed = False
        for grant_item_id in list(granted_map.keys()):
            granted_traits = granted_map.get(grant_item_id, []) or []
            if not hasattr(granted_traits, "__iter__") or isinstance(granted_traits, str):
                continue
            new_traits = [t for t in list(granted_traits) if t != trait_name]
            if len(new_traits) != len(list(granted_traits)):
                changed = True
                if new_traits:
                    granted_map[grant_item_id] = new_traits
                else:
                    del granted_map[grant_item_id]
        if changed:
            if not granted_map and key in worker:
                del worker[key]
            renpy.log(f"TRAITS: Promoted '{trait_name}' from item-granted to permanent inventory trait")
                
    def _coerce_trait_effect_entries(raw):
        """Normalize trait effect payload (string/dict/list/Revertable*) into a list of entries."""
        if raw is None:
            return []
        if hasattr(raw, "get") and callable(getattr(raw, "get", None)):
            return [raw]
        if isinstance(raw, (str, bytes)):
            return [raw]
        if hasattr(raw, "__iter__"):
            return list(raw)
        return []

    def _trait_name_duration_from_entry(entry):
        """Return (trait_name, duration) from string or dict-like trait entry."""
        if entry is None:
            return None, 0
        if hasattr(entry, "get") and callable(getattr(entry, "get", None)):
            name = entry.get("name") or entry.get("trait")
            try:
                duration = int(entry.get("duration", 0) or 0)
            except Exception:
                duration = 0
            return name, duration
        if isinstance(entry, (str, bytes)):
            return str(entry), 0
        return None, 0

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
                    renpy.log(f"add_trait effect_value type: {type(effect_value)}, value: {str(effect_value)[:100]}")
                    entries = _coerce_trait_effect_entries(effect_value)
                    renpy.log(f"Processing {len(entries)} add_trait entries")
                    for trait_entry in entries:
                        trait_name, trait_duration = _trait_name_duration_from_entry(trait_entry)
                        if trait_name:
                            traits_before = worker.get("traits", []) or []
                            had_trait_before = trait_name in traits_before
                            was_item_granted = _trait_has_item_source(worker, trait_name)
                            _record_removed_conflicts(worker, item_id, trait_name)
                            add_trait_with_duration(worker, trait_name, trait_duration)
                            traits_after = worker.get("traits", []) or []
                            if trait_name in traits_after and (not had_trait_before or was_item_granted):
                                _record_item_granted_trait(worker, item_id, trait_name)
                elif effect_type == "remove_trait":
                    # Support array of traits or single trait string - removes traits when equipping
                    renpy.log(f"remove_trait effect_value type: {type(effect_value)}, value: {str(effect_value)[:100]}")
                    removed_traits = []
                    entries = _coerce_trait_effect_entries(effect_value)
                    renpy.log(f"Processing {len(entries)} remove_trait entries")
                    for trait_entry in entries:
                        trait_name_to_remove, _ = _trait_name_duration_from_entry(trait_entry)
                        if trait_name_to_remove:
                            renpy.log(f"Removing trait: '{trait_name_to_remove}' from worker '{worker.get('name', 'Unknown')}'")
                            if trait_name_to_remove in worker.get("traits", []):
                                removed_traits.append(trait_name_to_remove)
                            remove_trait_safe(worker, trait_name_to_remove)
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
                    # Only undo traits this equipment actually granted. Traits from workers,
                    # consumables, or old saves without provenance are preserved.
                    granted_by_item = _pop_item_granted_traits(worker, item_id)
                    renpy.log(f"remove_item_effects: Recorded traits granted by item '{item_id}': {granted_by_item}")
                    for trait_name_to_remove in granted_by_item:
                        if trait_name_to_remove and not _trait_has_item_source(worker, trait_name_to_remove):
                            renpy.log(f"remove_item_effects: Removing item-granted trait '{trait_name_to_remove}' from worker '{worker.get('name', 'Unknown')}'")
                            remove_trait_safe(worker, trait_name_to_remove)
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
                        renpy.log(f"remove_item_effects: No recorded traits to re-add for item '{item_id}'")

    def remove_item_from_inventory(inventory, item_id, quantity=1):
        # CRITICAL: Check if this is manager_inventory and ALWAYS work directly with store.manager_inventory
        is_manager_inventory = (hasattr(store, 'manager_inventory') and 
                               (inventory is store.manager_inventory or 
                                id(inventory) == id(getattr(store, 'manager_inventory', None))))
        
        # If this is manager_inventory, work DIRECTLY with store.manager_inventory
        if is_manager_inventory:
            # Convert to a normal list if needed
            try:
                store.manager_inventory = list(store.manager_inventory) if store.manager_inventory else []
                # Always work with store.manager_inventory directly
                inventory = store.manager_inventory
            except Exception:
                pass
        
        # First, ensure every entry in the inventory is a tuple and normalize quantities
        for i, entry in enumerate(inventory):
            if not isinstance(entry, tuple):
                if hasattr(entry, "get"):
                    # Handle dict format: {"item_id": ..., "quantity": ..., "equipped": ...}
                    converted = (entry.get("item_id"), entry.get("quantity", 1), entry.get("equipped", False))
                    inventory[i] = converted
                elif hasattr(entry, "__getitem__") and not isinstance(entry, str):
                    # Handle list/RevertableList format: [item_id] or [item_id, quantity] or [item_id, quantity, equipped]
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

    def ensure_manager_inventory_synced_for_potions():
        """Refresh manager_inventory when worker_details opens. Fixes bug where potions
        in storage are not detected at start of new day until user visits storage."""
        _get_normalized_manager_inventory()
        renpy.store.manager_inventory = store.manager_inventory

    def use_or_buy_potion_action(worker, potion_id):
        """
        Returns an action to use a potion (from manager inventory) or show buy confirmation.
        Always reads from store.manager_inventory at call time to avoid stale state after new day.
        """
        potion_item = next((i for i in items_json["items"] if i["id"] == potion_id), None)
        if not potion_item:
            return Function(lambda: renpy.notify(f"Potion {potion_id} not found!"))
        canonical = next((w for w in store.workers if w.get("name") == worker.get("name")), worker)
        # CRITICAL: Read from store.manager_inventory explicitly at call time.
        # After new day, cached references can be stale; Ren'Py may not have synced yet.
        inv = getattr(store, "manager_inventory", []) or []
        has_in_manager = False
        for item_entry in inv:
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
            worker_name = worker.get("name") if hasattr(worker, "get") else None
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
        elif hasattr(effect_raw, "get"):
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
                    if hasattr(effect_value, "get"):
                        for skill_name, delta in effect_value.items():
                            try:
                                modify_base_skill(worker, skill_name, int(delta))
                            except Exception:
                                current = int(worker.get("skills", {}).get(skill_name, 0))
                                worker.setdefault("skills", {})[skill_name] = max(0, min(get_skill_cap(worker, skill_name), current + int(delta)))
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
                    for t in _coerce_trait_effect_entries(effect_value):
                        t_name, t_duration = _trait_name_duration_from_entry(t)
                        if t_name:
                            store.add_trait_with_duration(worker, t_name, t_duration)
                            if t_duration <= 0 and t_name in (worker.get("traits", []) or []):
                                _promote_item_granted_trait(worker, t_name)
                except Exception:
                    try:
                        renpy.log(f"ERROR: use_item add_trait failed for '{item_id}' on '{worker.get('name','?')}' value={effect_value}")
                    except Exception:
                        pass
            elif effect_type == "remove_trait":
                try:
                    for t in _coerce_trait_effect_entries(effect_value):
                        t_name, _ = _trait_name_duration_from_entry(t)
                        if t_name:
                            store.remove_trait_safe(worker, t_name)
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
        if not hasattr(inv, "__iter__") or isinstance(inv, str):
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

            if condition_str.startswith("has_folder_worker:"):
                target_folder = condition_str.split(":", 1)[1].strip()
                result = any(w.get("folder") == target_folder for w in store.workers)
                renpy.log(f"evaluate_condition: has_folder_worker:{target_folder}? Result: {result}")
                return result

            if condition_str.startswith("not_has_folder_worker:"):
                target_folder = condition_str.split(":", 1)[1].strip()
                result = not any(w.get("folder") == target_folder for w in store.workers)
                renpy.log(f"evaluate_condition: not_has_folder_worker:{target_folder}? Result: {result}")
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
        gender_mode = getattr(persistent, "worker_gender_filter", "both")

        def _matches_gender_filter(worker_obj):
            if gender_mode == "both":
                return True
            wgender = (worker_obj.get("gender") or "").strip().lower()
            if gender_mode == "male":
                return wgender != "female"
            if gender_mode == "female":
                return wgender != "male"
            return True

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
            and not w.get("recruitment_locked", False)
            and (w.get("nsfw", False) == persistent.nsfw_enabled)
            and _matches_gender_filter(w)
        ]
        
        # Remove workers that have already been recruited
        recruited_names = {w["name"] for w in store.workers}
        available_recruit = [
            w for w in recruit_pool
            if w["name"] not in recruited_names
        ]

        # Safety gate: enforce current gender filter before selection.
        available_recruit = [w for w in available_recruit if _matches_gender_filter(w)]
        
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
            spawn_filters = {}
            if gender_mode in ("male", "female"):
                spawn_filters["gender"] = gender_mode
            available_recruit = [spawn_new_worker(filters=spawn_filters) for _ in range(6)]
            available_recruit = [w for w in available_recruit if w and _matches_gender_filter(w)]

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
                                and not w.get("monster", False)
                                and not w.get("recruitment_locked", False)]  # Filter out monsters and quest-locked recruits
            if available_workers:
                return (True, random.choice(available_workers))
            return (False, None)
        elif worker_name:
            worker = next((w for w in all_workers if w["name"] == worker_name), None)
            # Monsters should only be available in capture events, not in normal recruitment
            if worker and worker["name"] not in recruited_names and not is_worker_dead(worker["name"]) and not worker.get("monster", False) and not worker.get("recruitment_locked", False):
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
                (hasattr(v, "get") and w.get(k, {}).items() >= v.items()) or
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
                while True:
                    # Read current skill level and accumulated uses directly from the dict.
                    current_skill_level = int(base_skills.get(skill_name, 0))
                    skill_uses = int(worker["skill_uses"].get(skill_name, 0))

                    # Determine uses needed for level up.
                    # Tiered system: fast early, slows down after 75, very hard after 85.
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

                    # Not enough uses for next level (or invalid threshold): stop processing this skill.
                    if uses_needed <= 0 or skill_uses < uses_needed:
                        break

                    old_level = current_skill_level
                    renpy.log(f"LEVEL UP: {worker_name}'s {skill_name} from {old_level} to {old_level + 1} (uses: {skill_uses} >= needed: {uses_needed})")

                    # Use modify_base_skill to increment by 1 and ensure it stays within bounds.
                    new_level = modify_base_skill(worker, skill_name, 1)

                    # Safety: if skill is already capped and no level was gained, stop to avoid an infinite loop.
                    if new_level <= old_level:
                        break

                    # Consume only the uses needed for this level; keep leftover experience.
                    worker["skill_uses"][skill_name] = max(0, skill_uses - uses_needed)
                    remaining_uses = worker["skill_uses"][skill_name]
                    renpy.notify(f"{worker_name}'s {skill_name} skill leveled up from {old_level} to {new_level}!")
                    renpy.log(f"{worker_name} - {skill_name}: consumed {uses_needed} uses, remaining {remaining_uses}")

                    # Reduce rebelliousness when leveling up a skill (worker feels satisfied with progress).
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
                # random_one must never land on a placeholder/hidden skill (e.g. "Specialty N").
                # is_skill_visible filters those out and also keeps the pick inside the current
                # SFW/NSFW skill set. Fallback re-filters so placeholders can't sneak back in.
                candidates = [s for s in skill_names_list if s not in exclude and is_skill_visible(s)]
                if not candidates:
                    candidates = [s for s in skill_names_list if is_skill_visible(s)]
                if candidates:
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
                    if not hasattr(_b, "get"):
                        continue
                    jobs = _b.get("servant_jobs")
                    if hasattr(jobs, "get") and wname in jobs:
                        del jobs[wname]
                    assigned = _b.get("assigned_servants")
                    if hasattr(assigned, "__iter__") and not isinstance(assigned, str):
                        _b["assigned_servants"] = [
                            aw for aw in assigned
                            if not (hasattr(aw, "get") and aw.get("name") == wname)
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
        if not (hasattr(base_traits, "__iter__") and not isinstance(base_traits, str)) or not base_traits:
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
            "comfort_desired": 4,  # Procedural recruits default to comfort level 4
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
        if not (hasattr(base_traits, "__iter__") and not isinstance(base_traits, str)) or not base_traits:
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
            "comfort_desired": 4,  # Procedural recruits default to comfort level 4
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
            if hasattr(w, "get"):
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
        if "assigned_servants" not in building or not (hasattr(building.get("assigned_servants"), "__iter__") and not isinstance(building.get("assigned_servants"), str)):
            building["assigned_servants"] = []
        worker_name = worker.get("name")
        if not worker_name:
            renpy.log("add_worker_to_building: worker name missing, skipping assignment")
            return
        # Always operate on the canonical worker object from store.workers if available.
        canonical_worker = None
        for w in store.workers:
            if hasattr(w, "get") and w.get("name") == worker_name:
                canonical_worker = w
                break
        if canonical_worker is None:
            canonical_worker = worker
        # Remove worker from OLD building's assigned_servants before moving
        old_ab = canonical_worker.get("assigned_building")
        resolved_old = _resolve_building_key(old_ab) if old_ab else None
        if resolved_old and resolved_old != building_name and old_ab != "Unassigned":
            _remove_worker_from_building_by_name(available_buildings[resolved_old], worker_name)
        # Remove any stale duplicates by name in NEW building before adding
        _remove_worker_from_building_by_name(building, worker_name)
        building["assigned_servants"].append(canonical_worker)
        # CRITICAL: Set the assigned_building on the worker
        canonical_worker["assigned_building"] = building_name
        # Keep assignment unique across all buildings. If this worker had stale
        # servant_jobs entries elsewhere, Manager sync could pull them back.
        for other_name, other_building in available_buildings.items():
            if other_name == building_name or not hasattr(other_building, "get"):
                continue
            other_jobs = other_building.get("servant_jobs", {})
            if hasattr(other_jobs, "get") and worker_name in other_jobs:
                try:
                    del other_jobs[worker_name]
                except Exception:
                    pass
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

        try:
            sanitize_invalid_servant_job(building, worker_name, canonical_worker)
        except Exception as e:
            renpy.log("add_worker_to_building: sanitize_invalid_servant_job error: " + str(e))
        try:
            verify_assignment_integrity("add_worker_to_building")
        except Exception:
            pass

    def canonicalize_servant_job_id(building, job_id):
        """Return canonical profession id for servant_jobs: always lowercase 'rest', else JSON id spelling."""
        if job_id is None:
            return "unassigned"
        s = str(job_id).strip()
        if not s or s.lower() == "unassigned":
            return "unassigned"
        jlow = s.lower()
        if jlow == "rest":
            return "rest"
        btype_id = building.get("type") if building else None
        if not btype_id:
            return s
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        if not btype:
            return s
        for p in btype.get("professions", []) or []:
            pid = p.get("id")
            if pid is not None and str(pid).strip().lower() == jlow:
                return str(pid).strip()
        return s

    def sanitize_invalid_servant_job(building, worker_name, worker_obj=None):
        """If servant_jobs has a profession id not defined for this building type, reset to unassigned.
        Prevents stale jobs after moves (e.g. 'service' from another building). Rest is always allowed.
        Normalizes rest to lowercase 'rest' and profession ids to match JSON casing (fixes job filter duplicates)."""
        if not building or not worker_name:
            return
        jobs_map = building.get("servant_jobs") or {}
        jid = jobs_map.get(worker_name)
        if jid is None:
            return
        jlow = str(jid).strip().lower()
        if jlow in ("", "unassigned"):
            return
        if jlow == "rest":
            if str(jid).strip() != "rest":
                building["servant_jobs"][worker_name] = "rest"
                renpy.log("sanitize_invalid_servant_job: %s normalized rest job %r -> 'rest'" % (worker_name, jid))
            return
        btype_id = building.get("type")
        if not btype_id:
            return
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        if not btype:
            return
        canon = None
        for p in btype.get("professions", []) or []:
            pid = p.get("id")
            if pid is not None and str(pid).strip().lower() == jlow:
                canon = str(pid).strip()
                break
        if canon is not None:
            if str(jid).strip() != canon:
                building["servant_jobs"][worker_name] = canon
                renpy.log("sanitize_invalid_servant_job: %s normalized job %r -> %r" % (worker_name, jid, canon))
            return
        building["servant_jobs"][worker_name] = "unassigned"
        renpy.log("sanitize_invalid_servant_job: %s invalid job %r for building type %s -> unassigned" % (worker_name, jid, btype_id))
        try:
            cw = worker_obj
            if cw is None:
                cw = next((w for w in store.workers if hasattr(w, "get") and w.get("name") == worker_name), None)
            if cw:
                clear_worker_autorest_state(cw)
        except Exception:
            pass

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
        canonical = next((w for w in store.workers if hasattr(w, "get") and w.get("name") == worker_name), worker)
        current_job = (building.get("servant_jobs") or {}).get(worker_name)
        job_id_str = str(job_id).strip().lower() if job_id else ""
        if job_id_str == "rest" and current_job and str(current_job).strip().lower() not in ("rest", "", "unassigned"):
            # Unified key with auto-rest in process_manager_auto_rest, so manual Rest
            # also restores to the previous profession when energy/health recover.
            canonical["previous_profession"] = current_job
            renpy.log(f"set_worker_job: {worker_name} -> Rest (stored previous_profession={current_job})")
        canon_job = canonicalize_servant_job_id(building, job_id if job_id is not None else "unassigned")
        building["servant_jobs"][worker_name] = canon_job
        try:
            verify_assignment_integrity("set_worker_job")
        except Exception:
            pass

    def clear_worker_autorest_state(worker):
        """Clear previous_profession when player manually changes job (so auto-restore doesn't override).
        Also cleans the legacy previous_job key for any save that wrote it before keys were unified."""
        if not worker or not hasattr(worker, "get"):
            return
        canonical = next((w for w in store.workers if hasattr(w, "get") and w.get("name") == worker.get("name")), worker)
        if "previous_profession" in canonical:
            del canonical["previous_profession"]
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
        """Rebuild assigned_servants for a single building from store.workers.
        worker['assigned_building'] is the single source of truth for membership."""
        try:
            resolved = _resolve_building_key(building_name)
            if not resolved:
                return
            building = available_buildings.get(resolved)
            if not hasattr(building, "get"):
                return

            rebuilt = []
            seen = set()

            # Single source: workers whose assigned_building matches this building
            for worker in store.workers:
                if not hasattr(worker, "get"):
                    continue
                wname = worker.get("name")
                if not wname or wname in seen:
                    continue
                if worker.get("assigned_building") == resolved:
                    rebuilt.append(worker)
                    seen.add(wname)
                    # Ensure servant_jobs entry exists
                    if "servant_jobs" not in building:
                        building["servant_jobs"] = {}
                    if wname not in building["servant_jobs"]:
                        building["servant_jobs"][wname] = "unassigned"

            building["assigned_servants"] = rebuilt

            # Clean orphaned servant_jobs (workers no longer assigned here)
            sj = building.get("servant_jobs")
            if sj and hasattr(sj, "keys"):
                orphans = [k for k in sj if k not in seen]
                for k in orphans:
                    del sj[k]

            try:
                verify_assignment_integrity("sync_assigned_servants_for_building")
            except Exception:
                pass
        except Exception as e:
            renpy.log("sync_assigned_servants_for_building error: " + str(e))

    def get_manager_display_servants(building_name, building_data=None):
        """Return workers to display in Manager screen. Uses assigned_servants + resolve to store.workers, then get_building_servants as fallback. Resolves Building 1 / Building_1."""
        try:
            resolved = _resolve_building_key(building_name)
            bd = building_data if (building_data and hasattr(building_data, "get")) else (available_buildings.get(resolved or building_name, {}))
            name_to_w = {w.get("name"): w for w in (store.workers or []) if hasattr(w, "get") and w.get("name")}
            raw = bd.get("assigned_servants") or []
            result = []
            seen = set()
            for sw in raw:
                if not hasattr(sw, "get") or not sw.get("name"):
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
        worker['assigned_building'] is the single source of truth for membership."""
        try:
            resolved = _resolve_building_key(building_name)
            if not resolved:
                return []
            building = available_buildings.get(resolved, {})
            if not hasattr(building, "get"):
                return []

            servants = []
            seen = set()

            for worker in store.workers:
                if not hasattr(worker, "get"):
                    continue
                wname = worker.get("name")
                if not wname or wname in seen:
                    continue
                if worker.get("assigned_building") == resolved:
                    servants.append(worker)
                    seen.add(wname)
                    # Ensure servant_jobs entry exists
                    if wname not in (building.get("servant_jobs") or {}):
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
                if not hasattr(cb, "get") or not hasattr(ob, "get"):
                    continue
                for wname, jid in (ob.get("servant_jobs") or {}).items():
                    if wname and (wname not in cb.get("servant_jobs", {})):
                        cb.setdefault("servant_jobs", {})[wname] = jid
                for w in ob.get("assigned_servants") or []:
                    if hasattr(w, "get") and w.get("name"):
                        cb_list = cb.get("assigned_servants") or []
                        if not any(x.get("name") == w.get("name") for x in cb_list if hasattr(x, "get")):
                            cb.setdefault("assigned_servants", []).append(w)
                for worker in store.workers:
                    if hasattr(worker, "get") and worker.get("assigned_building") == other:
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
                        if hasattr(worker, "get") and worker.get("assigned_building") == building_name:
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
                if hasattr(building, "get"):
                    building["assigned_servants"] = []

            # Step 2: Add each worker to their building's assigned_servants (dedupe by name)
            seen_per_building = {}  # {building_name: set of worker names}
            for worker in store.workers:
                if not hasattr(worker, "get"):
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
                if hasattr(building, "get"):
                    building["assigned_servants"].append(worker)
            
            # Clean orphaned servant_jobs entries per building
            for bname, bdata in available_buildings.items():
                if not hasattr(bdata, "get"):
                    continue
                sj = bdata.get("servant_jobs")
                if not sj or not hasattr(sj, "keys"):
                    continue
                assigned_here = seen_per_building.get(bname, set())
                orphans = [k for k in sj if k not in assigned_here]
                for k in orphans:
                    del sj[k]

            renpy.log("sync_building_assignments_from_workers: done")
            try:
                verify_assignment_integrity("sync_building_assignments_from_workers")
            except Exception:
                pass
        except Exception as e:
            renpy.log(f"sync_building_assignments_from_workers error: {e}")

    def verify_assignment_integrity(reason=""):
        """
        Lightweight integrity checker for assignment state.
        Logs only when mismatches are found (or when verbose flag is enabled).
        """
        issues = []
        try:
            _norm = _normalize_building_key_for_match
            _rw = lambda w: hasattr(w, "get") and w.get("name")
            workers_seq = getattr(store, "workers", []) or []
            buildings_map = getattr(store, "available_buildings", {}) or {}
            name_to_worker = {w.get("name"): w for w in workers_seq if _rw(w)}
            worker_names = set(name_to_worker.keys())

            # Track where workers appear in building-side structures.
            seen_in_assigned = {}
            seen_in_jobs = {}

            for bname, bdata in buildings_map.items():
                if not hasattr(bdata, "get"):
                    continue

                # assigned_servants checks
                for sw in (bdata.get("assigned_servants") or []):
                    if not (hasattr(sw, "get") and sw.get("name")):
                        continue
                    wname = sw.get("name")
                    seen_in_assigned.setdefault(wname, []).append(bname)
                    worker_obj = name_to_worker.get(wname)
                    if worker_obj:
                        ab = worker_obj.get("assigned_building", "Unassigned")
                        if ab not in (None, "", "Unassigned") and _norm(ab) != _norm(bname):
                            issues.append("assigned_servants mismatch: worker=%s store=%s list=%s" % (wname, ab, bname))
                    else:
                        issues.append("assigned_servants unknown worker: worker=%s building=%s" % (wname, bname))

                # servant_jobs checks
                jobs = bdata.get("servant_jobs", {}) or {}
                if hasattr(jobs, "items"):
                    for wname, _jid in jobs.items():
                        if not wname:
                            continue
                        seen_in_jobs.setdefault(wname, []).append(bname)
                        if wname not in worker_names:
                            issues.append("servant_jobs unknown worker: worker=%s building=%s" % (wname, bname))
                            continue
                        worker_obj = name_to_worker.get(wname)
                        ab = worker_obj.get("assigned_building", "Unassigned") if worker_obj else "Unassigned"
                        if ab not in (None, "", "Unassigned") and _norm(ab) != _norm(bname):
                            issues.append("servant_jobs mismatch: worker=%s store=%s jobs=%s" % (wname, ab, bname))

            # Worker-side checks
            for wname, w in name_to_worker.items():
                ab = w.get("assigned_building", "Unassigned")
                if ab in (None, "", "Unassigned"):
                    if wname in seen_in_assigned:
                        issues.append("worker unassigned but in assigned_servants: worker=%s buildings=%s" % (wname, seen_in_assigned.get(wname)))
                    if wname in seen_in_jobs:
                        issues.append("worker unassigned but in servant_jobs: worker=%s buildings=%s" % (wname, seen_in_jobs.get(wname)))
                    continue
                if not _resolve_building_key(ab):
                    issues.append("worker points to missing building: worker=%s building=%s" % (wname, ab))

            # Duplicate appearances in building-side indices
            for wname, blist in seen_in_assigned.items():
                norm_set = set([_norm(x) for x in blist if x])
                if len(norm_set) > 1:
                    issues.append("worker appears in multiple assigned_servants: worker=%s buildings=%s" % (wname, blist))
            for wname, blist in seen_in_jobs.items():
                norm_set = set([_norm(x) for x in blist if x])
                if len(norm_set) > 1:
                    issues.append("worker appears in multiple servant_jobs: worker=%s buildings=%s" % (wname, blist))

        except Exception as e:
            renpy.log("ASSIGNMENT_INTEGRITY: checker error: %s" % e)
            return -1

        verbose = bool(getattr(store, "assignment_integrity_verbose", False))
        if issues or verbose:
            renpy.log("ASSIGNMENT_INTEGRITY: reason=%s issues=%d" % (reason or "unspecified", len(issues)))
            for msg in issues:
                renpy.log("ASSIGNMENT_INTEGRITY: " + msg)
        return len(issues)

    def rebuild_assigned_servants():
        """Rebuild assigned_servants from workers. Alias for sync_building_assignments_from_workers."""
        sync_building_assignments_from_workers()
    
    # Canonical assignment API used by other modules. Keep these bindings in one
    # place so duplicated helpers in legacy files can delegate consistently.
    store._canonical_set_worker_job = set_worker_job
    store._canonical_clear_worker_autorest_state = clear_worker_autorest_state
    store._canonical_sync_assigned_servants_for_building = sync_assigned_servants_for_building
    store._canonical_get_building_servants = get_building_servants
    store._canonical_validate_and_sync_buildings = validate_and_sync_buildings
    store._canonical_sync_building_assignments_from_workers = sync_building_assignments_from_workers
    store._canonical_rebuild_assigned_servants = rebuild_assigned_servants
    store.verify_assignment_integrity = verify_assignment_integrity

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
                if not hasattr(building, "get"):
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
        try:
            verify_assignment_integrity("unassign_worker")
        except Exception:
            pass

    def remove_worker_from_building(worker):
        if worker.get("assigned_building", "Unassigned") != "Unassigned" and worker["assigned_building"] in available_buildings:
            building = available_buildings[worker["assigned_building"]]
            _remove_worker_from_building_by_name(building, worker.get("name"))
            # Also clear job mapping from the old building.
            # Leaving this stale entry lets sync logic re-attach workers to the old building.
            try:
                jobs = building.get("servant_jobs", {})
                wname = worker.get("name")
                if hasattr(jobs, "get") and wname in jobs:
                    del jobs[wname]
            except Exception:
                pass
            try:
                verify_assignment_integrity("remove_worker_from_building")
            except Exception:
                pass

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
        
        # Base worker daily cost by design.
        worker["daily_cost"] = new_comfort * 20
        
        renpy.log(f"Comfort adjusted: {current_comfort} -> {new_comfort}, Relationship: {current_relationship} -> {new_relationship} (bonus: {relationship_bonus}), Daily Cost: ${worker['daily_cost']}")

    def check_worker_health():
        global workers
        to_remove = []
        dead_names = []
        for worker in workers:
            if worker["health"] <= 0:
                # Slimes reform from a puddle instead of dying - but only if not already mid-reform.
                already_reforming = "Reforming" in (worker.get("traits") or [])
                if worker_can_reform(worker) and not already_reforming:
                    worker["health"] = max(1, calculate_max_health(worker) // 4)
                    add_trait_with_duration(worker, "Reforming", 3)
                    renpy.notify(f"{worker['name']} reformed from a puddle!")
                    renpy.log(f"{worker['name']} reformed instead of dying (health -> {worker['health']})")
                    continue
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
        if name in available_buildings and hasattr(available_buildings[name], "get"):
            available_buildings[name].setdefault("owned", True)

    def _generic_building_slot_index(name):
        """Parse Building n or Building_n to slot index n, or None. (Space/underscore per save compatibility.)"""
        if name is None:
            return None
        s = str(name).strip()
        m = re.match(r"^Building\s+(\d+)$", s)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
        m2 = re.match(r"^Building_(\d+)$", s, re.IGNORECASE)
        if m2:
            try:
                return int(m2.group(1))
            except Exception:
                return None
        return None

    def _generic_slot_occupied(n):
        """True if either Building n or Building_n exists and is owned (dict-like, not isinstance dict)."""
        for k in ("Building %d" % n, "Building_%d" % n):
            b = available_buildings.get(k)
            if b is not None and hasattr(b, "get") and b.get("owned", True):
                return True
        return False

    def next_generic_building_slot():
        """
        Lowest n >= 1 where slot n has no owned Building n / Building_n. Price = n * 10000.
        Returns (name, price) or None if max_building slots are filled.
        """
        try:
            mb = int(getattr(store, "max_building", 50) or 50)
        except Exception:
            mb = 50
        for n in range(1, mb + 1):
            if not _generic_slot_occupied(n):
                return ("Building %d" % n, n * 10000)
        return None

    def sell_building(building_name):
        """
        Sell generic Building n (n > 1) for max(0, stored price - 5000).
        Unassigns all workers, removes the slot from available_buildings and owned_buildings.
        Building 1 cannot be sold. Accepts Building n or Building_n (LA BIBLIA §3).
        """
        idx = _generic_building_slot_index(building_name)
        if idx is None:
            renpy.notify(_("Only numbered building slots can be sold."))
            return False
        if idx <= 1:
            renpy.notify(_("You cannot sell your first building."))
            return False
        key_canon = "Building %d" % idx
        ob = getattr(store, "owned_buildings", None) or []
        aliases = [key_canon]
        alt = _alternate_building_key(key_canon)
        if alt:
            aliases.append(alt)
        if not any(a in ob for a in aliases if a):
            renpy.notify(_("That building is not in your portfolio."))
            return False

        resolved = _resolve_building_key(key_canon)
        if not resolved:
            resolved = _resolve_building_key(alt) if alt else None
        if not resolved:
            renpy.notify(_("Building data is missing."))
            return False
        b = available_buildings.get(resolved)
        if b is None or not hasattr(b, "get"):
            renpy.notify(_("Building data is missing."))
            return False

        try:
            paid = int(b.get("price", 0) or 0)
        except Exception:
            paid = 0
        sale = max(0, paid - 5000)

        norm_target = _normalize_building_key_for_match(key_canon)
        for w in list(getattr(store, "workers", []) or []):
            if not hasattr(w, "get"):
                continue
            ab = w.get("assigned_building")
            if not ab or ab == "Unassigned":
                continue
            if ab in aliases or (norm_target and _normalize_building_key_for_match(ab) == norm_target):
                try:
                    unassign_worker(w)
                except Exception as ex:
                    renpy.log("sell_building unassign error: %s" % ex)

        try:
            b["assigned_servants"] = []
            sj = b.get("servant_jobs")
            if sj is not None and hasattr(sj, "clear"):
                sj.clear()
            else:
                b["servant_jobs"] = {}
        except Exception:
            pass

        keys_to_drop = []
        for k in (resolved, _alternate_building_key(resolved), key_canon, alt):
            if k and k in available_buildings and k not in keys_to_drop:
                keys_to_drop.append(k)
        removed_any = False
        for k in keys_to_drop:
            try:
                del available_buildings[k]
                removed_any = True
            except Exception:
                pass
        if not removed_any:
            renpy.notify(_("Could not remove building from the map."))
            return False

        try:
            for a in aliases:
                if a in store.owned_buildings:
                    store.owned_buildings.remove(a)
        except Exception:
            pass

        try:
            cn = getattr(store, "custom_names", None)
            if cn is not None and hasattr(cn, "__contains__"):
                for k in keys_to_drop:
                    if k in cn:
                        del cn[k]
        except Exception:
            pass

        try:
            mbb = getattr(store, "map_button_buildings", None)
            if mbb is not None and hasattr(mbb, "items"):
                dead = [bk for bk, bv in mbb.items() if bv in keys_to_drop or bv in aliases]
                for bk in dead:
                    try:
                        del mbb[bk]
                    except Exception:
                        pass
        except Exception:
            pass

        cab = getattr(store, "current_affected_building", None)
        if cab and (cab in keys_to_drop or cab in aliases or (norm_target and _normalize_building_key_for_match(cab) == norm_target)):
            store.current_affected_building = None

        try:
            store.money = int(getattr(store, "money", 0) or 0) + int(sale)
        except Exception:
            pass

        if hasattr(store, "buildings_owned"):
            try:
                store.buildings_owned = len(store.owned_buildings)
            except Exception:
                pass

        try:
            if callable(getattr(store, "rebuild_assigned_servants", None)):
                store.rebuild_assigned_servants()
            else:
                sync_building_assignments_from_workers()
        except Exception as ex:
            renpy.log("sell_building sync error: %s" % ex)

        renpy.notify(_("Sold %(key)s for $%(sale)d (paid $%(paid)d).") % {"key": key_canon, "sale": sale, "paid": paid})
        renpy.log("sell_building: sold %s for %s (paid %s)" % (key_canon, sale, paid))
        return True

    def sellable_generic_building_names():
        """Owned Building n / Building_n slots with n > 1; returns canonical 'Building n' for UI."""
        out = []
        seen = set()
        for bn in getattr(store, "owned_buildings", []) or []:
            idx = _generic_building_slot_index(bn)
            if idx is None or idx <= 1:
                continue
            canon = "Building %d" % idx
            if canon not in seen:
                seen.add(canon)
                out.append(canon)
        return out

    def building_sale_preview(building_key):
        """Returns (sale_price, paid_price) for UI; sale = max(0, paid - 5000)."""
        idx = _generic_building_slot_index(building_key)
        if idx is None:
            return (0, 0)
        rk = _resolve_building_key("Building %d" % idx)
        if not rk:
            rk = _resolve_building_key("Building_%d" % idx)
        b = available_buildings.get(rk) if rk else None
        if b is None or not hasattr(b, "get"):
            return (0, 0)
        try:
            paid = int(b.get("price", 0) or 0)
        except Exception:
            paid = 0
        return (max(0, paid - 5000), paid)

    def manager_building_is_sellable(building_name):
        """True if Manage Buildings can offer Sell for this slot (generic Building n, n > 1, owned)."""
        idx = _generic_building_slot_index(building_name)
        if idx is None or idx <= 1:
            return False
        canon = "Building %d" % idx
        try:
            return canon in sellable_generic_building_names()
        except Exception:
            return False

    def manager_sell_current_building_then_exit(building_name):
        """Run sell_building; on success return to tavern (Manage screen would be stale)."""
        fn = getattr(store, "sell_building", None)
        if not callable(fn):
            return
        if not fn(building_name):
            return
        try:
            tbg = getattr(store, "tavern_bg", None)
            if tbg is not None:
                store.current_bg = tbg
        except Exception:
            pass
        try:
            renpy.hide_screen("Manager")
            renpy.show_screen("tavern")
        except Exception as ex:
            renpy.log("manager_sell_current_building_then_exit: %s" % ex)

    store.next_generic_building_slot = next_generic_building_slot
    store.sell_building = sell_building
    store.sellable_generic_building_names = sellable_generic_building_names
    store.building_sale_preview = building_sale_preview
    store.manager_building_is_sellable = manager_building_is_sellable
    store.manager_sell_current_building_then_exit = manager_sell_current_building_then_exit

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
        
        NON_PURCHASABLE = {"governor_castle", "arena", "academy"}
        
        # Greenhouse y Shop son comodines - pueden tener todos los tipos
        if button_type == "greenhouse" or button_type == "shop":
            for btype in building_types_json.get("building_types", []):
                if btype.get("id") not in NON_PURCHASABLE:
                    available.append(btype)
            return available
        
        for btype in building_types_json.get("building_types", []):
            if btype.get("id") not in NON_PURCHASABLE:
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
            return f"gui/map/{button_id}c.png"
        else:
            return f"gui/map/{button_id}a.png"

    def get_map_building_display_name(button_id):
        """
        Devuelve el nombre de visualización del edificio asociado a un botón del mapa.
        Retorna None si el edificio no está comprado.
        """
        building_name = get_map_building_name_safe(button_id)
        if building_name is None:
            return None
        
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
                            if current_message:
                                messages.append(current_message)
                            current_message = word
                        current_sentence = word
                    else:
                        if current_sentence:
                            current_sentence += " " + word
                        else:
                            current_sentence = word
                
                if current_sentence:
                    if len(current_message) + len(current_sentence) + 2 <= max_chars:
                        current_message = (current_message + " " + current_sentence).strip()
                    else:
                        if current_message:
                            messages.append(current_message)
                        current_message = current_sentence
            else:
                if len(current_message) + len(sentence) + 2 > max_chars:
                    if current_message:
                        messages.append(current_message)
                    current_message = sentence
                else:
                    if current_message:
                        current_message += " " + sentence
                    else:
                        current_message = sentence
        
        if current_message:
            messages.append(current_message)

        try:
            if (
                messages
                and len(messages) >= 2
                and isinstance(messages[-1], str)
                and len(messages[-1].strip()) > 0
                and len(messages[-1].strip()) < int(min_chunk_chars)
            ):
                merged = (messages[-2].rstrip() + " " + messages[-1].lstrip()).strip()
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
        _ef = choice.get("effect_worker_filter")
        _ef_dict = _ef if hasattr(_ef, "get") else {}
        _ef_restrict = bool(choice.get("restrict_worker_effects_to_filter", False))
        _ef_kw = {
            "effect_worker_filter": _ef_dict,
            "restrict_worker_effects_to_filter": _ef_restrict,
        }
        _fwf = getattr(store, "filter_workers_for_effect_worker_filter", None)
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
                        return {"message": "The situation unfolds, but without a clear point of contact among your properties, your hands are tied. It resolves on its own—messily.", "outcome": "failure"}

                    eligible_buildings = [
                        (b_name, b) for b_name, b in available_buildings.items()
                        if b.get("type") in event_building_types and b.get("owned", False)
                    ]
                    if not eligible_buildings:
                        # Return dictionary for error
                        return {"message": f"You don't have a {event_building_types[0] if event_building_types else 'suitable establishment'} equipped to deal with this. The problem sorts itself out, but not in your favor.", "outcome": "failure"}

                    # Select a specific building and store its name
                    selected_building_name, selected_building = random.choice(eligible_buildings)
                    store.current_affected_building = selected_building_name
                
                # Log which building we're using
                renpy.log(f"Event using building: {selected_building_name}")
                
                check_info = get_event_building_skill_check_info(selected_building)
                base_total_skill = check_info.get("display_skill", 0)
                building_bonus = check_info.get("building_bonus", 0)
                total_skill = check_info.get("target_chance", 0)

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
                    _needs_worker_success = (
                        ("add_trait" in success_effects)
                        or ("trait_chance" in success_effects)
                        or ("trait_remove_chance" in success_effects)
                    )
                    if _needs_worker_success:
                        pool = list(assigned_servants) if assigned_servants else []
                        if not pool:
                            for w in store.workers:
                                if w.get("assigned_building") == selected_building_name:
                                    pool.append(w)
                            if not pool and store.workers:
                                pool = list(store.workers)
                        if callable(_fwf) and pool:
                            pool = _fwf(pool, _ef_dict, _ef_restrict, selected_building)
                        if pool:
                            success_worker = random.choice(pool)
                    applied_values = apply_effects(success_effects, worker=success_worker, building=selected_building, **_ef_kw)
                    etn = (applied_values.get("event_trait_worker_name") or "").strip()
                    event_worker_name = etn or (success_worker["name"] if success_worker else "Unknown")
                    acting_worker_name = "Building Team"
                    outcome_status = "success"
                else:
                    # Failure case: check if we need a worker for trait effects
                    failure_effects = effect.get("failure", {})
                    needs_worker_for_effect = (
                        ("add_trait" in failure_effects)
                        or ("trait_chance" in failure_effects)
                        or ("trait_remove_chance" in failure_effects)
                    )
                    
                    # If we need a worker for failure effects but none are assigned
                    if needs_worker_for_effect and not assigned_servants:
                        renpy.log("Failure effect needs a worker (for trait), but no workers are assigned to this building.")
                        pool = [w for w in store.workers if w.get("assigned_building") == selected_building_name]
                        if not pool and store.workers:
                            pool = list(store.workers)
                        if callable(_fwf) and pool:
                            pool = _fwf(pool, _ef_dict, _ef_restrict, selected_building)
                        random_worker = random.choice(pool) if pool else None
                        if random_worker:
                            renpy.log(f"Selected worker {random_worker['name']} for failure trait application")
                        
                        applied_values = apply_effects(failure_effects, worker=random_worker, building=selected_building, **_ef_kw)
                        etn = (applied_values.get("event_trait_worker_name") or "").strip()
                        if etn:
                            event_worker_name = etn
                        elif applied_values.get("worker_effect_trait_skipped"):
                            event_worker_name = "your staff"
                        elif random_worker:
                            event_worker_name = random_worker["name"]
                        else:
                            event_worker_name = "An adventurer"
                        acting_worker_name = "Building Team"
                    else:
                        # Either no worker needed for effects, or we have assigned servants
                        if needs_worker_for_effect and assigned_servants:
                            pool = list(assigned_servants)
                            if callable(_fwf) and pool:
                                pool = _fwf(pool, _ef_dict, _ef_restrict, selected_building)
                            affected_worker = random.choice(pool) if pool else None
                            applied_values = apply_effects(failure_effects, worker=affected_worker, building=selected_building, **_ef_kw)
                            etn = (applied_values.get("event_trait_worker_name") or "").strip()
                            if etn:
                                event_worker_name = etn
                            elif applied_values.get("worker_effect_trait_skipped"):
                                event_worker_name = "your staff"
                            elif affected_worker:
                                event_worker_name = affected_worker["name"]
                            else:
                                event_worker_name = "An adventurer"
                            acting_worker_name = "Building Team"
                        else:
                            # No worker traits involved
                            applied_values = apply_effects(failure_effects, worker=None, building=selected_building, **_ef_kw)
                            event_worker_name = "An adventurer"
                            acting_worker_name = "Building Team"
                    outcome_status = "failure"

                msg_failure_use = message_failure
                if outcome_status == "failure" and applied_values.get("worker_effect_trait_skipped") and choice.get("message_failure_worker_effect_skipped"):
                    msg_failure_use = choice.get("message_failure_worker_effect_skipped") or message_failure

                # Apply replacements to new variables
                replaced_description = description.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                replaced_option_text = option_text.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                replaced_message_success = message_success.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)
                replaced_message_failure = msg_failure_use.replace("[event_worker]", event_worker_name).replace("[acting_worker]", acting_worker_name)

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
                        outcome_message = "\n".join(chunks)
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
                    applied_values = apply_effects(effect, worker=acting_worker, **_ef_kw)
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
                        return {"message": f"You scan your roster, but nobody assigned to {building_types[0] if building_types else 'the task'} has the right skills for this. The moment passes, and you make a mental note to fill the gap.", "outcome": "failure"}

                # Handle chosen worker (passed via acting_worker)
                elif worker_selection_mode == "choose":
                    # Check if this specific choice actually needs a worker
                    # If the choice doesn't have a condition, we don't need to validate the worker
                    if not choice.get("condition"):
                        # For choices without conditions in a "choose" worker event, skip worker validation
                        renpy.log(f"Worker selection mode is 'choose', but this specific choice has no condition, so no worker needed")
                        # Handle the choice without a worker
                        applied_values = apply_effects(effect, worker=acting_worker, **_ef_kw)
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
                    apply_effects(effect.get("failure", {}), worker=None, **_ef_kw)
                    outcome_status = "failure"
                    # Return dictionary for this error case
                    return {"message": outcome_message, "outcome": outcome_status}
                else:
                    check_info = get_event_worker_skill_check_info(selected_worker, choice)
                    skill_level = check_info.get("roll_skill", 0)
                    threshold = check_info.get("threshold", 0)
                    
                    # If threshold is specified and worker meets/exceeds it, give better success chances
                    if threshold > 0 and skill_level >= threshold:
                        skill_above_threshold = skill_level - threshold
                        # If worker is 15+ points above threshold, guaranteed success
                        if check_info.get("auto_success", False):
                            renpy.log(f"Worker {selected_worker['name']} skill {skill_level} is {skill_above_threshold} points above threshold {threshold} - guaranteed success")
                            base_outcome_message = choice.get("message_success") or "The plan proceeds smoothly, yielding modest gains."
                            applied_values = apply_effects(effect.get("success", {}), worker=selected_worker, **_ef_kw)
                            outcome_status = "success"
                        else:
                            # If worker meets threshold, use a minimum success chance of 90%
                            # Also apply base success bonus
                            worker_bonus = check_info.get("worker_bonus", 0)
                            effective_success_chance = check_info.get("target_chance", 0)
                            skill_with_bonus = min(100, skill_level + worker_bonus)
                            renpy.log(f"Worker {selected_worker['name']} skill {skill_level} (with +{worker_bonus} bonus = {skill_with_bonus}) meets threshold {threshold} - using {effective_success_chance}% success chance")
                            roll = random.randint(1, 100)
                            if roll <= effective_success_chance:
                                base_outcome_message = choice.get("message_success") or "The plan proceeds smoothly, yielding modest gains."
                                applied_values = apply_effects(effect.get("success", {}), worker=selected_worker, **_ef_kw)
                                outcome_status = "success"
                            else:
                                base_outcome_message = choice.get("message_failure") or "The attempt falters, and the moment slips away without reward."
                                applied_values = apply_effects(effect.get("failure", {}), worker=selected_worker, **_ef_kw)
                                outcome_status = "failure"
                    else:
                        # No threshold or doesn't meet it - use normal skill-based roll
                        # Apply base success bonus to increase baseline success chance
                        worker_bonus = check_info.get("worker_bonus", 0)
                        effective_skill = check_info.get("target_chance", 0)
                        roll = random.randint(1, 100)
                        renpy.log(f"Worker {selected_worker['name']} skill {skill_level} (with +{worker_bonus}% bonus = {effective_skill}) - roll {roll} vs {effective_skill}%")
                        if roll <= effective_skill:
                            base_outcome_message = choice.get("message_success") or "The plan proceeds smoothly, yielding modest gains."
                            applied_values = apply_effects(effect.get("success", {}), worker=selected_worker, **_ef_kw)
                            outcome_status = "success"
                        else:
                            base_outcome_message = choice.get("message_failure") or "The attempt falters, and the moment slips away without reward."
                            applied_values = apply_effects(effect.get("failure", {}), worker=selected_worker, **_ef_kw)
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
            
            # Only treat as probability-based when effect has explicit success/failure outcomes.
            # Many events use success_chance: 0 as metadata meaning "not random" - their money/reputation
            # are at top level and must be applied directly. If we treated success_chance=0 as
            # probability, we'd call apply_effects({}) and never apply the real effects.
            success_chance = effect.get("success_chance")
            has_success_outcome = "success" in effect
            has_failure_outcome = "failure" in effect
            is_probability_choice = (
                success_chance is not None
                and (has_success_outcome or has_failure_outcome)
            )
            if is_probability_choice:
                # Probability-based outcome (like fortune telling)
                # Ensure minimum success chance of 60%
                min_success_chance = get_event_success_min_chance()
                effective_success_chance = max(min_success_chance, success_chance)
                roll = random.random()
                if roll <= effective_success_chance:
                    outcome_status = "success"
                    message = choice.get("message_success", "Fortune smiles upon you.")
                    applied_values = apply_effects(effect.get("success", {}), worker=acting_worker, **_ef_kw)
                else:
                    outcome_status = "failure"
                    message = choice.get("message_failure", "Fortune turns her back.")
                    applied_values = apply_effects(effect.get("failure", {}), worker=acting_worker, **_ef_kw)
                
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
                applied_values = apply_effects(effect, worker=acting_worker, **_ef_kw)
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
            if not hasattr(event, "get"):
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
                trait_name, duration = _trait_name_duration_from_entry(trait_entry)
                
                if trait_name and trait_name not in worker.get("traits", []):
                    add_trait_with_duration(worker, trait_name, duration)
                    renpy.notify(f"{worker['name']} gained {trait_name} from expired trait")
            
            # Handle different formats: string, list, or dict
            for trait_entry in _coerce_trait_effect_entries(trait_data):
                process_trait_entry(trait_entry)

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

    

    def apply_effects(
        effect_dict,
        worker=None,
        building=None,
        effect_worker_filter=None,
        restrict_worker_effects_to_filter=False,
    ):
        # Track actual values applied for dynamic message replacement
        applied_values = {}
        filt = effect_worker_filter if hasattr(effect_worker_filter, "get") else {}
        _hascon = getattr(store, "effect_worker_filter_has_constraints", None)
        restrict = bool(restrict_worker_effects_to_filter) and callable(_hascon) and _hascon(filt)
        res_building = building
        if restrict and worker and (not hasattr(res_building, "get") or res_building is None):
            try:
                bn = worker.get("assigned_building") if hasattr(worker, "get") else None
                if bn and str(bn).strip() and str(bn) != "Unassigned":
                    res_building = available_buildings.get(bn)
            except Exception:
                pass
        eff_worker = worker
        if restrict and worker and filt:
            wm = getattr(store, "worker_matches_effect_worker_filter", None)
            if callable(wm):
                try:
                    if not wm(worker, res_building, filt):
                        eff_worker = None
                        renpy.log("apply_effects: worker failed effect_worker_filter; skipping worker-scoped effect keys")
                except Exception as e:
                    renpy.log("apply_effects: effect_worker_filter error: " + str(e))

        ewf_filt = filt
        ewf_restrict = restrict
        ewf_building = res_building

        def _ewf_filter_workers(wlist):
            fn = getattr(store, "filter_workers_for_effect_worker_filter", None)
            if not wlist:
                return []
            if not callable(fn):
                return list(wlist)
            try:
                return fn(wlist, ewf_filt, ewf_restrict, ewf_building)
            except Exception:
                return list(wlist)

        # Apply money changes
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

        # Apply effects to a specific worker (eff_worker may be cleared by effect_worker_filter)
        if eff_worker:
            # Adjust energy
            if "servant_energy" in effect_dict:
                energy_change = effect_dict["servant_energy"]
                eff_worker["energy"] = max(0, eff_worker["energy"] + energy_change)
                applied_values["actual_energy"] = energy_change
                # Only show notification if energy actually changed
                if energy_change != 0:
                    renpy.notify(f"{eff_worker['name']}'s energy changed by {energy_change}")

            # Adjust health (support both "health" and "servant_health" for consistency with recruitment/daily stories)
            health_change = effect_dict.get("servant_health") if "servant_health" in effect_dict else effect_dict.get("health")
            if health_change is not None:
                try:
                    health_change = int(health_change)
                    eff_worker["health"] = max(0, eff_worker["health"] + health_change)
                    applied_values["actual_health"] = health_change
                    # Only show notification if health actually changed
                    if health_change != 0:
                        renpy.notify(f"{eff_worker['name']}'s health changed by {health_change}")
                except (TypeError, ValueError) as e:
                    renpy.log(f"apply_effects health error: {e}")

            # Apply skill modifiers (e.g. Charm +3 from event choice)
            if "skill_modifiers" in effect_dict:
                skill_data = effect_dict["skill_modifiers"]
                if hasattr(skill_data, "get") or (hasattr(skill_data, "items") and callable(getattr(skill_data, "items", None))):
                    for skill_name, delta in skill_data.items():
                        try:
                            delta_int = int(delta)
                            modify_base_skill(eff_worker, skill_name, delta_int)
                            if delta_int != 0:
                                renpy.notify(f"{eff_worker.get('name', 'Worker')}'s {skill_name} changed by {delta_int:+d}")
                        except Exception as e:
                            renpy.log(f"apply_effects skill_modifiers error for {skill_name}: {e}")

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
                    # Fixed worker by name (supports string or list)
                    _raw_wn = effect_dict.get("worker_name") or (getattr(store, 'current_event', {}).get("worker_name") if hasattr(store, 'current_event') else None)
                    _wn_list = _raw_wn if (hasattr(_raw_wn, "__iter__") and not isinstance(_raw_wn, str)) else ([_raw_wn] if _raw_wn else [])
                    if not _wn_list:
                        renpy.notify("No worker specified for recruitment.")
                        renpy.log("Custom recruit_worker: missing worker_name and random_worker not set")
                        # Do not early-return None; continue gracefully
                        worker_name = None
                    else:
                        worker_name = _wn_list[0]  # Use first name for recruitment
                        all_workers = load_workers(include_unique=True, include_encounter_only=True)
                        target_worker = next((w for w in all_workers if w["name"] in _wn_list), None)
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
                is_dict = hasattr(trait_entry, "get") and callable(getattr(trait_entry, "get", None))
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
                
                target_worker = target_worker_override if target_worker_override is not None else eff_worker
                # Resolve acting/event worker placeholders
                if target_worker is None and isinstance(target, str) and target in ("acting_worker", "event_worker"):
                    target_worker = eff_worker
                    if target_worker is None and target == "event_worker":
                        ewn = getattr(store, "event_worker_name", None) or ""
                        if ewn:
                            for w in store.workers:
                                if w.get("name") == ewn:
                                    target_worker = w
                                    break
                # When eff_worker is None (e.g. building_skill events), resolve target to select a worker
                if target_worker is None and target and store.workers:
                    if target == "random_worker":
                        pool = _ewf_filter_workers(list(store.workers))
                        if pool:
                            target_worker = random.choice(pool)
                            renpy.log(f"Selected random worker {target_worker['name']} for trait application (no worker context)")
                        else:
                            renpy.log("No eligible workers for trait application (effect_worker_filter) - skipping")
                            applied_values["worker_effect_trait_skipped"] = True
                    elif target == "random_worker_female":
                        female_workers = [w for w in store.workers if w.get("gender", "") == "female"]
                        female_workers = _ewf_filter_workers(female_workers)
                        if female_workers:
                            target_worker = random.choice(female_workers)
                            renpy.log(f"Selected random female worker {target_worker['name']} for trait application (no worker context)")
                        else:
                            renpy.log("No eligible female workers for trait application - skipping")
                            applied_values["worker_effect_trait_skipped"] = True
                    elif target == "random_worker_male":
                        male_workers = [w for w in store.workers if w.get("gender", "") == "male"]
                        male_workers = _ewf_filter_workers(male_workers)
                        if male_workers:
                            target_worker = random.choice(male_workers)
                            renpy.log(f"Selected random male worker {target_worker['name']} for trait application (no worker context)")
                        else:
                            renpy.log("No eligible male workers for trait application - skipping")
                            applied_values["worker_effect_trait_skipped"] = True
                    elif isinstance(target, str) and target not in ("acting_worker", "event_worker"):
                        # Target by worker name (e.g. "Aspen")
                        for w in store.workers:
                            if w.get("name") == target:
                                target_worker = w
                                renpy.log(f"Resolved trait target by name: {target}")
                                break

                if trait_name and target_worker and ewf_restrict:
                    wm = getattr(store, "worker_matches_effect_worker_filter", None)
                    hc = getattr(store, "effect_worker_filter_has_constraints", None)
                    if callable(wm) and callable(hc) and hc(ewf_filt):
                        tb = ewf_building
                        if (not tb or not hasattr(tb, "get")) and hasattr(target_worker, "get"):
                            bn = target_worker.get("assigned_building")
                            if bn and str(bn).strip() and str(bn) != "Unassigned":
                                tb = available_buildings.get(bn)
                        try:
                            if not wm(target_worker, tb, ewf_filt):
                                renpy.log("apply_effects add_trait: target failed effect_worker_filter")
                                applied_values["worker_effect_trait_skipped"] = True
                                target_worker = None
                        except Exception as e:
                            renpy.log("apply_effects add_trait filter error: " + str(e))

                if trait_name and target_worker:
                    # Resolve to canonical worker in store.workers so trait changes persist (fixes copy-from-screen)
                    target_worker = _resolve_worker_for_automation(target_worker)
                    if target_worker:
                        cache = getattr(store, "_trait_def_cache", {}) or {}
                        trait_def = cache.get(trait_name) if hasattr(cache, "get") else None
                        if not trait_def and hasattr(store, "get_trait_definition"):
                            trait_def = store.get_trait_definition(trait_name)
                        if trait_def:
                            if duration == 0:
                                duration = trait_def.get("duration", 0)
                            add_trait_with_duration(target_worker, trait_name, duration)
                            renpy.log(f"Applied trait '{trait_name}' to {target_worker.get('name', '?')}")
                            try:
                                applied_values["event_trait_worker_name"] = target_worker.get("name", "")
                            except Exception:
                                pass
                        else:
                            renpy.log(f"Trait '{trait_name}' not found in traits_list")
                elif trait_name:
                    renpy.log(f"Cannot add trait '{trait_name}' - worker is None")
            
            # Ren'Py can supply RevertableDict/RevertableList. Prioritize dict-like via .get()
            # so add_trait objects {"name": "...", "duration": 0} are not mis-read as iterables.
            is_dict_like = hasattr(trait_data, "get") and callable(getattr(trait_data, "get", None))
            is_string = isinstance(trait_data, str)
            is_list_like = hasattr(trait_data, "__iter__") and not is_string and not is_dict_like
            
            try:
                if is_dict_like:
                    # Single dict-like entry with name/duration/target
                    apply_trait_entry(trait_data)
                elif is_list_like:
                    # Array of trait names or dicts
                    for trait_entry in trait_data:
                        apply_trait_entry(trait_entry)
                elif is_string:
                    # Single string (trait name)
                    apply_trait_entry(trait_data)
                else:
                    renpy.log(f"ERROR: add_trait has invalid type: {type(trait_data)}, value: {trait_data}")
            except Exception as e:
                renpy.log(f"ERROR processing add_trait: {e}, type: {type(trait_data)}, value: {trait_data}")
                import traceback
                renpy.log(traceback.format_exc())

        def _coerce_trait_roll_list(raw):
            if raw is None:
                return []
            if hasattr(raw, "get"):
                return [raw]
            if hasattr(raw, "__iter__") and not isinstance(raw, (str, bytes)):
                return list(raw)
            return []

        _tc_list = _coerce_trait_roll_list(effect_dict.get("trait_chance"))
        if _tc_list and eff_worker:
            _fn_tc = getattr(store, "apply_trait_chance_entries", None)
            if callable(_fn_tc):
                _fn_tc(eff_worker, _tc_list, applied_values, granted_list_key="traits_from_training", log_prefix="Event")

        _trc_list = _coerce_trait_roll_list(effect_dict.get("trait_remove_chance"))
        if _trc_list and eff_worker:
            _fn_trc = getattr(store, "apply_trait_remove_chance_entries", None)
            if callable(_fn_trc):
                _fn_trc(eff_worker, _trc_list, applied_values, removed_list_key="traits_removed_by_chance", log_prefix="Event")
        
        # Apply joy to worker when present (events use joy like interactions)
        if "joy" in effect_dict:
            joy_change = effect_dict["joy"]
            if joy_change != 0 and eff_worker and hasattr(store, "apply_attribute_change"):
                store.apply_attribute_change(eff_worker, "joy", joy_change)
                applied_values["actual_joy"] = joy_change
        
        # Return applied values for dynamic message replacement
        return applied_values

    def format_dynamic_message(message, applied_values):
        """
        Replace dynamic placeholders in event messages with actual values.
        Change values (money, reputation, health, energy, joy) are NOT duplicated in the narrative:
        money/reputation/health/energy placeholders are removed (shown in Changes); a trailing
        literal "(+N Joy)" is stripped when actual_joy is set so Joy appears only in Changes.
        
        Available placeholders:
        {actual_money}, {actual_reputation}, {actual_health}, {actual_energy} - removed (shown in Changes)
        {base_money}, {base_reputation} - for internal use / special cases
        {money_multiplier}, {reputation_multiplier} - Building multiplier display
        """
        # Change placeholders: remove from narrative (they appear in Changes summary).
        # Many messages end with a parenthetical like "({actual_money}, {actual_reputation} reputation, +5 Joy)."
        # We strip the entire trailing parenthetical when it contains change placeholders,
        # since build_changes_summary() already shows all of that info cleanly.
        import re
        _has_change_ph = any(ph in message for ph in ["{actual_money}", "{actual_reputation}", "{actual_health}", "{actual_energy}"])
        for ph in ["{actual_money}", "{actual_reputation}", "{actual_health}", "{actual_energy}"]:
            message = message.replace(ph, "")
        if _has_change_ph:
            # Remove trailing parenthetical that held the placeholders (may still contain literals like "+5 Joy", "reputation")
            message = re.sub(r"\s*\([^()]*\)\s*\.?\s*$", "", message)
        # Clean up any remaining orphaned patterns
        message = re.sub(r"\s*\(\s*\)", "", message)
        message = re.sub(r",\s*,", ",", message)
        message = re.sub(r"\s*,\s*\.", ".", message)
        message = re.sub(r"\s+\.", ".", message)
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

        # Standalone "(+N Joy)" at end of message (no other change placeholders were present): strip it too
        if applied_values and applied_values.get("actual_joy"):
            message = re.sub(r"\s*\(\s*[+-]?\d+\s*Joy\s*\)\s*\.?\s*$", "", message, flags=re.IGNORECASE)
        message = re.sub(r"[ \t]+\n", "\n", message)
        message = str(message).strip()

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
        if "actual_joy" in applied_values:
            j = applied_values["actual_joy"]
            if j != 0:
                parts.append(f"+{j} Joy" if j > 0 else f"{j} Joy")
        if not parts:
            return ""
        return "\nChanges: " + ", ".join(parts)

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
        jlow = str(job_id).strip().lower() if job_id is not None else ""
        if not jlow or jlow in ("rest", "unassigned"):
            return None
        btype_id = building.get("type")
        if not btype_id:
            return None
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        if not btype:
            return None
        for prof in btype.get("professions", []) or []:
            pid = prof.get("id")
            if pid is not None and str(pid).strip().lower() == jlow:
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
        if hasattr(entry, "get"):
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
        """Return normalized manager inventory and keep store.manager_inventory synchronized.
        Also syncs renpy.store so worker menu potion detection works after new day."""
        inv = getattr(store, "manager_inventory", None)
        norm = _normalize_inventory_container(inv)
        store.manager_inventory = norm
        renpy.store.manager_inventory = store.manager_inventory
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
        if "inventory" not in worker or not (hasattr(worker.get("inventory"), "__iter__") and not isinstance(worker.get("inventory"), str)):
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
        if "inventory" not in worker or not (hasattr(worker.get("inventory"), "__iter__") and not isinstance(worker.get("inventory"), str)):
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

    # Worker details: one control — Off, x3, x4, x5, x1, x2 (repeat)
    AUTO_SUPPLY_UI_CYCLE = (
        (False, 3),
        (True, 3),
        (True, 4),
        (True, 5),
        (True, 1),
        (True, 2),
    )

    def worker_auto_supply_compact_label(wref):
        """Short label for compact Stock Potions control."""
        w = _resolve_worker_for_automation(wref) if wref else None
        if not w:
            return "Off"
        if not w.get("auto_supply_potions", False):
            return "Off"
        try:
            c = int(w.get("auto_supply_potion_count", 3))
        except (TypeError, ValueError):
            c = 3
        c = max(1, min(5, c))
        return "x%d" % c

    def cycle_worker_auto_supply_compact(worker):
        """Cycle Stock Potions: Off -> x3 -> x4 -> x5 -> x1 -> x2 -> Off."""
        canonical = _resolve_worker_for_automation(worker)
        cycle = AUTO_SUPPLY_UI_CYCLE
        on = bool(canonical.get("auto_supply_potions", False))
        try:
            c = int(canonical.get("auto_supply_potion_count", 3))
        except (TypeError, ValueError):
            c = 3
        c = max(1, min(5, c))
        if not on:
            idx = 0
        else:
            idx = None
            for i, (oo, cc) in enumerate(cycle):
                if oo and cc == c:
                    idx = i
                    break
            if idx is None:
                idx = 1
        nxt = cycle[(idx + 1) % len(cycle)]
        new_on, new_count = nxt[0], nxt[1]
        canonical["auto_supply_potions"] = new_on
        canonical["auto_supply_potion_count"] = new_count
        try:
            worker["auto_supply_potions"] = new_on
            worker["auto_supply_potion_count"] = new_count
        except Exception:
            pass
        renpy.log(f"AUTO_SUPPLY_COMPACT: {canonical.get('name', '?')} -> on={new_on} count={new_count}")
        if new_on:
            try:
                run_worker_auto_supply_potions(canonical)
            except Exception as e:
                renpy.log("cycle_worker_auto_supply_compact immediate run error: " + str(e))
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

    AUTO_REST_ENTRY_PCTS = (15, 25, 35, 45)

    def normalize_auto_rest_entry_pct_for_worker(worker):
        """Clamp auto_rest_entry_pct to allowed presets (15, 25, 35, 45)."""
        allowed = AUTO_REST_ENTRY_PCTS
        if not worker:
            return 35
        raw = worker.get("auto_rest_entry_pct", 35)
        try:
            v = int(raw)
        except (TypeError, ValueError):
            v = 35
        if v in allowed:
            return v
        return min(allowed, key=lambda x: abs(x - v))

    store.normalize_auto_rest_entry_pct_for_worker = normalize_auto_rest_entry_pct_for_worker

    def toggle_worker_auto_rest(worker):
        """Toggle manager auto-rest for the worker (Worker details screen)."""
        canonical = _resolve_worker_for_automation(worker)
        new_value = not bool(canonical.get("auto_rest", False))
        canonical["auto_rest"] = new_value
        try:
            worker["auto_rest"] = new_value
        except Exception:
            pass
        renpy.log(f"AUTO_REST_TOGGLE: {canonical.get('name', '?')} -> {new_value}")
        renpy.restart_interaction()

    def cycle_worker_auto_rest_entry_pct(worker):
        """Cycle auto_rest_entry_pct: 15 -> 25 -> 35 -> 45 -> 15."""
        canonical = _resolve_worker_for_automation(worker)
        order = AUTO_REST_ENTRY_PCTS
        cur = normalize_auto_rest_entry_pct_for_worker(canonical)
        try:
            idx = order.index(cur)
        except ValueError:
            idx = 2
        new_pct = order[(idx + 1) % len(order)]
        canonical["auto_rest_entry_pct"] = new_pct
        try:
            worker["auto_rest_entry_pct"] = new_pct
        except Exception:
            pass
        renpy.log(f"AUTO_REST_ENTRY_PCT: {canonical.get('name', '?')} -> {new_pct}")
        renpy.restart_interaction()

    # Worker details: one control - Off, 15%, 25%, 35%, 45% (repeat)
    AUTO_REST_UI_CYCLE = (
        (False, None),
        (True, 15),
        (True, 25),
        (True, 35),
        (True, 45),
    )

    def worker_auto_rest_compact_label(wref):
        """Short label for compact Auto-rest control."""
        w = _resolve_worker_for_automation(wref) if wref else None
        if not w or not w.get("auto_rest", False):
            return "Off"
        return "%d%%" % normalize_auto_rest_entry_pct_for_worker(w)

    def cycle_worker_auto_rest_compact(worker):
        """Cycle Auto-rest: Off -> 15% -> 25% -> 35% -> 45% -> Off."""
        canonical = _resolve_worker_for_automation(worker)
        cycle = AUTO_REST_UI_CYCLE
        on = bool(canonical.get("auto_rest", False))
        pct = normalize_auto_rest_entry_pct_for_worker(canonical)
        if not on:
            idx = 0
        else:
            idx = None
            for i, (oo, pp) in enumerate(cycle):
                if oo and pp is not None and pp == pct:
                    idx = i
                    break
            if idx is None:
                idx = 1
        nxt_on, nxt_pct = cycle[(idx + 1) % len(cycle)]
        canonical["auto_rest"] = nxt_on
        if nxt_pct is not None:
            canonical["auto_rest_entry_pct"] = int(nxt_pct)
        try:
            worker["auto_rest"] = nxt_on
            if nxt_pct is not None:
                worker["auto_rest_entry_pct"] = int(nxt_pct)
        except Exception:
            pass
        renpy.log(f"AUTO_REST_COMPACT: {canonical.get('name', '?')} -> on={nxt_on} pct={nxt_pct}")
        renpy.restart_interaction()

    def _normalize_persistent_worker_automation_defaults():
        """Normalize persistent defaults used by global worker automation controls."""
        persistent.default_auto_supply_potions = bool(getattr(persistent, "default_auto_supply_potions", False))
        persistent.default_auto_equip = bool(getattr(persistent, "default_auto_equip", False))
        persistent.default_auto_rest = bool(getattr(persistent, "default_auto_rest", False))

        try:
            _count = int(getattr(persistent, "default_auto_supply_potion_count", 3))
        except Exception:
            _count = 3
        persistent.default_auto_supply_potion_count = max(1, min(5, _count))

        allowed = AUTO_REST_ENTRY_PCTS
        try:
            _pct = int(getattr(persistent, "default_auto_rest_entry_pct", 35))
        except Exception:
            _pct = 35
        if _pct not in allowed:
            _pct = min(allowed, key=lambda x: abs(x - _pct))
        persistent.default_auto_rest_entry_pct = int(_pct)

    def default_auto_supply_compact_label():
        _normalize_persistent_worker_automation_defaults()
        if not getattr(persistent, "default_auto_supply_potions", False):
            return "Off"
        return "x%d" % int(getattr(persistent, "default_auto_supply_potion_count", 3))

    def default_auto_rest_compact_label():
        _normalize_persistent_worker_automation_defaults()
        if not getattr(persistent, "default_auto_rest", False):
            return "Off"
        return "%d%%" % int(getattr(persistent, "default_auto_rest_entry_pct", 35))

    def apply_persistent_worker_automation_defaults_to_all_workers(restart_ui=True):
        """
        Apply persistent automation defaults to all current workers.
        This intentionally overrides per-worker automation settings.
        """
        _normalize_persistent_worker_automation_defaults()
        workers = list(getattr(store, "workers", []) or [])
        auto_supply_on = bool(getattr(persistent, "default_auto_supply_potions", False))
        auto_supply_count = int(getattr(persistent, "default_auto_supply_potion_count", 3))
        auto_equip_on = bool(getattr(persistent, "default_auto_equip", False))
        auto_rest_on = bool(getattr(persistent, "default_auto_rest", False))
        auto_rest_pct = int(getattr(persistent, "default_auto_rest_entry_pct", 35))

        for worker in workers:
            if not hasattr(worker, "get"):
                continue
            worker["auto_supply_potions"] = auto_supply_on
            worker["auto_supply_potion_count"] = auto_supply_count
            worker["auto_equip"] = auto_equip_on
            worker["auto_rest"] = auto_rest_on
            worker["auto_rest_entry_pct"] = auto_rest_pct

            if auto_supply_on:
                try:
                    run_worker_auto_supply_potions(worker)
                except Exception as e:
                    renpy.log("apply defaults auto-supply error: " + str(e))
            if auto_equip_on:
                try:
                    run_worker_auto_equip(worker)
                except Exception as e:
                    renpy.log("apply defaults auto-equip error: " + str(e))

        renpy.log(
            "AUTO_DEFAULTS_APPLY_ALL: workers=%d supply=%s x%d equip=%s rest=%s %d%%" % (
                len(workers),
                str(auto_supply_on),
                int(auto_supply_count),
                str(auto_equip_on),
                str(auto_rest_on),
                int(auto_rest_pct),
            )
        )
        if restart_ui:
            renpy.restart_interaction()

    def cycle_persistent_default_auto_supply_compact():
        """Cycle global Stock Potions default: Off -> x3 -> x4 -> x5 -> x1 -> x2 -> Off."""
        _normalize_persistent_worker_automation_defaults()
        cycle = AUTO_SUPPLY_UI_CYCLE
        on = bool(getattr(persistent, "default_auto_supply_potions", False))
        count = int(getattr(persistent, "default_auto_supply_potion_count", 3))
        count = max(1, min(5, count))
        if not on:
            idx = 0
        else:
            idx = None
            for i, (oo, cc) in enumerate(cycle):
                if oo and cc == count:
                    idx = i
                    break
            if idx is None:
                idx = 1
        nxt_on, nxt_count = cycle[(idx + 1) % len(cycle)]
        persistent.default_auto_supply_potions = bool(nxt_on)
        persistent.default_auto_supply_potion_count = int(nxt_count)
        apply_persistent_worker_automation_defaults_to_all_workers(restart_ui=True)

    def toggle_persistent_default_auto_equip():
        """Toggle global Auto Equip default and apply to all workers."""
        _normalize_persistent_worker_automation_defaults()
        persistent.default_auto_equip = not bool(getattr(persistent, "default_auto_equip", False))
        apply_persistent_worker_automation_defaults_to_all_workers(restart_ui=True)

    def cycle_persistent_default_auto_rest_compact():
        """Cycle global Auto-rest default: Off -> 15% -> 25% -> 35% -> 45% -> Off."""
        _normalize_persistent_worker_automation_defaults()
        cycle = AUTO_REST_UI_CYCLE
        on = bool(getattr(persistent, "default_auto_rest", False))
        pct = int(getattr(persistent, "default_auto_rest_entry_pct", 35))
        if pct not in AUTO_REST_ENTRY_PCTS:
            pct = 35
        if not on:
            idx = 0
        else:
            idx = None
            for i, (oo, pp) in enumerate(cycle):
                if oo and pp is not None and pp == pct:
                    idx = i
                    break
            if idx is None:
                idx = 1
        nxt_on, nxt_pct = cycle[(idx + 1) % len(cycle)]
        persistent.default_auto_rest = bool(nxt_on)
        if nxt_pct is not None:
            persistent.default_auto_rest_entry_pct = int(nxt_pct)
        apply_persistent_worker_automation_defaults_to_all_workers(restart_ui=True)

    
    
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
            if not hasattr(building, "get"):
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
            if hasattr(worker, "get"):
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
            if hasattr(worker, "get"):
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
        """Calculate bonus stories per profession per day based on reputation and formula."""
        if not bonus_formula or bonus_formula == "0":
            return 0
        try:
            bonus = int(eval(bonus_formula, {"__builtins__": None}, {"reputation": int(reputation)}))
            return bonus
        except Exception:
            return 0

    def _worker_folder_fallback_sync():
        # Fallback for saves that didn't go through the snapshot migration path
        # (snapshot corrupted, partial load, etc). Applies the same conservative
        # migration directly against store.workers / store.available_workers.
        # Idempotent: no-op when every non-procedural worker already has a
        # consistent template_id / folder pair.
        try:
            needs_check = False
            for _wlist in (getattr(store, "workers", None) or [], getattr(store, "available_workers", None) or []):
                for _w in _wlist:
                    if not hasattr(_w, "get"):
                        continue
                    if _w.get("procedural", False) or _w.get("monster", False):
                        continue
                    if not _w.get("template_id"):
                        needs_check = True
                        break
                if needs_check:
                    break
            if not needs_check:
                return

            build_idx = getattr(store, "_build_json_template_index", None)
            migrate = getattr(store, "_migrate_worker_folders_inplace", None)
            if not callable(build_idx) or not callable(migrate):
                return
            by_name, by_folder = build_idx()
            if by_name is None:
                renpy.log("MIGRATION v2 [fallback]: JSON templates unavailable — skipping")
                return
            s1, f1, sk1 = migrate(getattr(store, "workers", None) or [], by_name, by_folder, label=" [store.workers]")
            s2, f2, sk2 = migrate(getattr(store, "available_workers", None) or [], by_name, by_folder, label=" [store.available_workers]")
            if (s1 + s2 + f1 + f2) > 0 or (sk1 + sk2) > 0:
                renpy.log(
                    f"MIGRATION v2 [fallback]: stamped {s1 + s2}, fixed folder on {f1 + f2}, "
                    f"skipped {sk1 + sk2} ambiguous"
                )
        except Exception as e:
            import traceback
            renpy.log(f"MIGRATION v2 [fallback]: error: {e}")
            renpy.log(traceback.format_exc())

    def force_resync_worker_folder(name, folder=None):
        # Debug/recovery helper for ambiguous cases the auto-migration refused to
        # touch. Call from the Ren'Py console:
        #   force_resync_worker_folder("Amanita")             # auto-pick if unique
        #   force_resync_worker_folder("Amanita", "amanita")  # explicit folder
        # Refuses to write a folder that isn't a known JSON template.
        try:
            build_idx = getattr(store, "_build_json_template_index", None)
            if not callable(build_idx):
                renpy.log("force_resync_worker_folder: template index helper unavailable")
                return False
            by_name, by_folder = build_idx()
            if by_name is None:
                renpy.log("force_resync_worker_folder: JSON templates unavailable")
                return False

            target_folder = folder
            if target_folder is None:
                candidates = by_name.get(name, [])
                if len(candidates) == 1:
                    target_folder = candidates[0].get("folder")
                else:
                    options = [c.get("folder") for c in candidates]
                    renpy.log(f"force_resync_worker_folder: '{name}' has {len(candidates)} candidates: {options}. Pass folder=... explicitly.")
                    return False
            elif target_folder not in by_folder:
                renpy.log(f"force_resync_worker_folder: '{target_folder}' is not a known JSON template folder. Known folders: {sorted(list(by_folder.keys()))[:20]}...")
                return False

            updated = 0
            for wlist in (getattr(store, "workers", None) or [], getattr(store, "available_workers", None) or []):
                for w in wlist:
                    if not hasattr(w, "get"):
                        continue
                    if w.get("name") != name:
                        continue
                    if w.get("procedural", False) or w.get("monster", False):
                        renpy.log(f"force_resync_worker_folder: refusing to touch procedural/monster worker '{name}'")
                        continue
                    w["template_id"] = target_folder
                    w["folder"] = target_folder
                    updated += 1
                    renpy.log(f"force_resync_worker_folder: set '{name}' -> folder/template_id='{target_folder}'")
            return updated > 0
        except Exception as e:
            import traceback
            renpy.log(f"force_resync_worker_folder: error: {e}")
            renpy.log(traceback.format_exc())
            return False

    def after_load_callback():
        import copy as _cp
        import os
        import json

        # Versioned migration (v1 -> v2) runs inside _migrate_snapshot before
        # _apply_snapshot writes into the store. This is only a defensive
        # fallback for paths where snapshot migration didn't run or fully apply.
        _worker_folder_fallback_sync()
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
        if not hasattr(skills, "get"):
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
        if not hasattr(pending, "get"):
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
        if not hasattr(pending, "get"):
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
        if not hasattr(skills, "get"):
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
default manager_interactions_today = 0  # Manager's total interactions used today (shared pool; limit = 2 + Manager Level)
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
default arena_unlocked = False  # True after arena trial succeeds/mediocre/critical
default arena_lanista_paid = False  # True after player pays Lanista permit
define LANISTA_PERMIT_COST = 10000  # Cost to obtain Lanista permit for the coliseum
define SPECIAL_MATCH_COST = 5000  # Cost to enter a special match (2 rounds + combat roll)
define FIRST_BUILDING_BASE_DAILY_DISCOUNT = 0  # Daily base maintenance discount for Building 1 / Building_1 (disabled)
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
    class SafeNameDict(dict):
        """Legacy compatibility class (do not store in persistent)."""
        def __missing__(self, key):
            self[key] = key
            return key

    def _sanitize_persistent_obj(obj):
        """Convert SafeNameDict to plain dict inside persistent data."""
        try:
            if hasattr(obj, "get"):
                if obj.__class__.__name__ == "SafeNameDict":
                    obj = dict(obj)
                return {k: _sanitize_persistent_obj(v) for k, v in obj.items()}
            if isinstance(obj, tuple):
                return tuple(_sanitize_persistent_obj(v) for v in obj)
            if hasattr(obj, "add") and hasattr(obj, "discard"):
                # set-like (native set or RevertableSet) — must check before list-like
                return {_sanitize_persistent_obj(v) for v in obj}
            if hasattr(obj, "__iter__") and not isinstance(obj, str):
                # list-like (native list or RevertableList)
                return [_sanitize_persistent_obj(v) for v in obj]
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
            arena_owned_flag = hasattr(arena_data, "get") and bool(arena_data.get("owned", False))
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
            if "inventory" not in worker or not (hasattr(worker.get("inventory"), "__iter__") and not isinstance(worker.get("inventory"), str)):
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
    size 16
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
    size 16
    layout "subtitle"

style worker_details_header:
    size 24
    color "#ffffff"
    bold True
    xalign 0.0
    yalign 0.0

style roster_stats:
    size 16
    color "#aaaaaa"
    xalign 0.0
    text_align 0.0

style roster_button:
    xalign 0.0
    xpadding 0
    background None
    idle_background None
    hover_background "#333333"
    size 16
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

# Academy laboratory: alchemist pass (one-time), then craft sessions with investment tiers and 2 rounds of choices.
label academy_laboratory_dialogue:
    # Yvara devotion ending: weekly potion gift if a week has passed.
    if getattr(store, "yvara_lab_access", False) and getattr(store, "yvara_ending_route", "") == "devotion":
        $ _total = calculate_total_days()
        $ _last_gift = getattr(store, "yvara_lab_gift_last_day", None)
        if _last_gift is None or (_total - _last_gift) >= 7:
            jump yvara_lab_gift_scene

label academy_laboratory_dialogue_post_gift:
    # Defensive cleanup: any lingering Yvara bust/dim from a prior visit must not bleed into the lab director scene.
    hide yvara_bust
    hide yvara_bg_dim
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
    $ _lab_disc = getattr(store, "yvara_academy_discount_active", False)
    $ _cost_basic = ALCHEMY_COST_BASIC // 2 if _lab_disc else ALCHEMY_COST_BASIC
    $ _cost_quality = ALCHEMY_COST_QUALITY // 2 if _lab_disc else ALCHEMY_COST_QUALITY
    $ _cost_premium = ALCHEMY_COST_PREMIUM // 2 if _lab_disc else ALCHEMY_COST_PREMIUM
    if _lab_disc:
        lab_director "How much do you invest? Basic coin yields basic draughts in number. Deeper pockets open the way to quality—or something extraordinary. The director has standing instructions to honour your account at half rate."
    else:
        lab_director "How much do you invest? Basic coin yields basic draughts in number. Deeper pockets open the way to quality—or something extraordinary."
    menu:
        lab_director "What will you do?"
        "Batch basic ([_cost_basic] coins)." if money >= _cost_basic:
            $ _alchemy_investment_tier = "basic"
            $ money -= _cost_basic
            jump academy_alchemy_choose_worker
        "Batch basic ([_cost_basic] coins)." if money < _cost_basic:
            lab_director "You need at least [_cost_basic] coins for a basic batch."
            jump academy_laboratory_craft_menu
        "Quality ([_cost_quality] coins)." if money >= _cost_quality:
            $ _alchemy_investment_tier = "quality"
            $ money -= _cost_quality
            jump academy_alchemy_choose_worker
        "Quality ([_cost_quality] coins)." if money < _cost_quality:
            lab_director "You need at least [_cost_quality] coins for a quality run."
            jump academy_laboratory_craft_menu
        "Premium ([_cost_premium] coins)." if money >= _cost_premium:
            $ _alchemy_investment_tier = "premium"
            $ money -= _cost_premium
            jump academy_alchemy_choose_worker
        "Premium ([_cost_premium] coins)." if money < _cost_premium:
            lab_director "You need at least [_cost_premium] coins for a premium run."
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
    if _worker is None or not hasattr(_worker, "get") or not _worker.get("name"):
        python:
            _disc = getattr(store, "yvara_academy_discount_active", False)
            _refund_basic = ALCHEMY_COST_BASIC // 2 if _disc else ALCHEMY_COST_BASIC
            _refund_quality = ALCHEMY_COST_QUALITY // 2 if _disc else ALCHEMY_COST_QUALITY
            _refund_premium = ALCHEMY_COST_PREMIUM // 2 if _disc else ALCHEMY_COST_PREMIUM
            money += _refund_basic if _alchemy_investment_tier == "basic" else (_refund_quality if _alchemy_investment_tier == "quality" else _refund_premium)
        $ renpy.show_screen("map_screen")
        $ renpy.show_screen("academy_menu")
        jump tavern_screen
    jump academy_alchemy_craft_run

label academy_alchemy_craft_run:
    # Defensive cleanup: lab labels must not carry Yvara visuals.
    hide yvara_bust
    hide yvara_bg_dim
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
        arena_promoter "The coliseum welcomes you -- but the sands do not. I am master here: the Lanista. These grounds have tasted blood and glory for generations, and they do not open to just anyone."
        arena_promoter "If you would train gladiators under my banner, you must first buy in. [LANISTA_PERMIT_COST] coins -- one payment, no haggling. After that, we speak of worth. Proof is in the sand: a trial by combat. What say you?"
        jump arena_permit_menu
    # Already paid permit, need trial
    arena_promoter "The permit is yours. Paper and coin open the gate -- but the crowd and the sands demand more. They demand proof."
    arena_promoter "Send me one of your own for a trial by combat before the masses. The bout may be to the death; the sands show no mercy."
    arena_promoter "If your fighter survives -- or falls with honour, blade in hand -- the Arena is yours to use. Do you accept?"
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
    if _worker is None or not hasattr(_worker, "get") or not _worker.get("name"):
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
        $ renpy.say(narrator, "The trial is won. The Arena opens its gates to you -- you may use it from the map from now on.")
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

