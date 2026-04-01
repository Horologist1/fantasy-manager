# worker_interactions.rpy

init python:

    _interactions_cache = None
    _interactions_cache_nsfw = None

    def invalidate_interactions_cache():
        global _interactions_cache, _interactions_cache_nsfw
        _interactions_cache = None
        _interactions_cache_nsfw = None

    def load_interactions():
        """
        Load interactions from all JSON files in the interactions folder.
        No longer treats interactions_default.json as special - loads all files equally.
        Uses a module-level cache to avoid reloading from disk on every call.
        """
        global _interactions_cache, _interactions_cache_nsfw

        # Return cached result if available and NSFW mode hasn't changed
        current_nsfw = persistent.nsfw_enabled
        if _interactions_cache is not None and _interactions_cache_nsfw == current_nsfw:
            return list(_interactions_cache)

        interactions = []
        loaded_files = False

        # Log all available files
        _gcfl = getattr(store, "get_cached_file_list", None)
        all_files = _gcfl() if callable(_gcfl) else renpy.list_files()
        interaction_files = [f for f in all_files if f.startswith("data/interactions/") and f.endswith(".json")]
        renpy.log(f"Found interaction files: {interaction_files}")

        # Load all interaction files from the interactions folder
        for file in interaction_files:
            try:
                renpy.log(f"Attempting to load file: {file}")
                with renpy.file(file) as f:
                    file_content = f.read()
                    renpy.log(f"File content: {file_content[:200]}...")  # Log first 200 chars
                    if isinstance(file_content, bytes):
                        file_content = file_content.decode("utf-8")
                    file_interactions = json.loads(file_content)
                    # Don't filter NSFW interactions - let player choose when NSFW is enabled
                    # When NSFW is disabled, only show SFW interactions
                    if persistent.nsfw_enabled:
                        # NSFW enabled: show all interactions (both NSFW and SFW)
                        filtered_interactions = file_interactions
                        interactions.extend(file_interactions)
                    else:
                        # NSFW disabled: only show SFW interactions
                        filtered_interactions = [inter for inter in file_interactions
                                               if not inter.get("nsfw", False)]
                        interactions.extend(filtered_interactions)
                    loaded_files = True
                    renpy.log(f"Successfully loaded {len(filtered_interactions)} interactions from {file}")
                    # Log the names of loaded interactions
                    for inter in filtered_interactions:
                        renpy.log(f"Loaded interaction: {inter.get('name', 'Unknown')} for {inter.get('specific_workers', [])}")
            except Exception as e:
                renpy.log(f"Error loading interactions from {file}: {str(e)}")

        # If no files were successfully loaded, log an error
        if not loaded_files:
            renpy.log("Warning: No interaction files were successfully loaded!")
        else:
            renpy.log(f"Total interactions loaded: {len(interactions)}")

        # Store result in cache before returning
        _interactions_cache = list(interactions)
        _interactions_cache_nsfw = current_nsfw

        # Always return whatever interactions were loaded, even if empty
        return interactions

    def filter_interactions_by_gender(interactions, gender):
        """Filter by manager gender (male/female from Lord/Lady). gender_filter may use male/female/lord/lady."""
        result = []
        norm_fn = getattr(store, "normalize_player_gender_requirement", None)
        for interaction in interactions:
            gf = interaction.get("gender_filter")
            if gf is None:
                result.append(interaction)
                continue
            if callable(norm_fn):
                cf = norm_fn(gf)
                if cf is not None:
                    if cf == gender:
                        result.append(interaction)
                    continue
            if str(gf).strip().lower() == str(gender).strip().lower():
                result.append(interaction)
        return result

    def filter_interactions_by_worker_gender(interactions, worker):
        """Filter interactions by worker gender."""
        worker_gender = worker.get("gender", None)
        return [interaction for interaction in interactions if interaction.get("worker_gender") is None or interaction["worker_gender"] == worker_gender]

    def filter_interactions_by_stats(interactions, worker):
        """Filter interactions based on worker's stats.
        Most categories use 'stat >= threshold'. Discipline uses 'rebelliousness < threshold'
        (lower rebelliousness = more compliant = unlock next level; e.g. less than 80, less than 75).
        """
        filtered = []
        for interaction in interactions:
            stat_requirements = interaction.get("stat_requirements", {})
            meets_requirements = True
            categories = interaction.get("categories", [])
            is_discipline = "Discipline" in categories

            for stat, required_value in stat_requirements.items():
                worker_value = worker.get(stat, 0)
                # Discipline + rebelliousness: requirement is "less than" (worker must be below threshold)
                if is_discipline and stat == "rebelliousness":
                    # Zero/negative threshold is effectively "no threshold" for discipline,
                    # and should not block the whole branch.
                    if required_value is None or required_value <= 0:
                        continue
                    if worker_value >= required_value:
                        meets_requirements = False
                        break
                else:
                    # Normal: worker stat must be >= required value
                    if worker_value < required_value:
                        meets_requirements = False
                        break

            if meets_requirements:
                filtered.append(interaction)
        
        return filtered

    def filter_interactions_by_flags(interactions, worker):
        """Filter interactions based on required and excluded flags."""
        filtered = []
        for interaction in interactions:
            # Check required flags
            required_flags = interaction.get("required_flags", {})
            meets_requirements = True
            
            for flag_name, required_value in required_flags.items():
                current_value = worker.get("flags", {}).get(flag_name)
                if current_value != required_value:
                    meets_requirements = False
                    break
            
            # Check excluded flags
            excluded_flags = interaction.get("excluded_flags", {})
            excluded = False
            
            for flag_name, excluded_value in excluded_flags.items():
                current_value = worker.get("flags", {}).get(flag_name)
                if current_value == excluded_value:
                    excluded = True
                    break
            
            if meets_requirements and not excluded:
                filtered.append(interaction)
        
        return filtered

    def filter_interactions_by_items(interactions, worker):
        """Filter interactions based on required items in manager inventory."""
        filtered = []
        for interaction in interactions:
            # Check required items
            required_items = interaction.get("required_items", [])
            
            # If no items are required, include the interaction
            if not required_items:
                filtered.append(interaction)
                continue
            
            # Check if manager has all required items
            has_required_items = True
            for item_id in required_items:
                item_found = False
                for inventory_item in manager_inventory:
                    if inventory_item[0] == item_id and inventory_item[1] > 0:
                        item_found = True
                        break
                if not item_found:
                    has_required_items = False
                    break
            
            if has_required_items:
                filtered.append(interaction)
        
        return filtered

    def filter_interactions_by_usage_limits(interactions, worker):
        """Filter interactions based on usage limits."""
        filtered = []
        for interaction in interactions:
            # Check usage limits
            usage_limit = interaction.get("usage_limit")
            
            # If no usage limit is set, include the interaction
            if not usage_limit:
                filtered.append(interaction)
                continue
            
            # Get limit parameters
            flag_name = usage_limit.get("flag")
            max_uses = usage_limit.get("max_uses", 1)
            
            if not flag_name:
                # If no flag specified, include the interaction
                filtered.append(interaction)
                continue
            
            # Check current usage count
            current_uses = 0
            flag_value = worker.get("flags", {}).get(flag_name)
            
            if flag_value is not None:
                # Use hasattr instead of isinstance to handle RevertableDict
                if hasattr(flag_value, 'get') and "value" in flag_value:
                    current_uses = flag_value.get("value", 0)
                elif isinstance(flag_value, (int, float)):
                    current_uses = flag_value
            
            # Include interaction if under the limit
            if current_uses < max_uses:
                filtered.append(interaction)
        
        return filtered

    def get_unlock_required_uses():
        """How many uses are required to unlock the next interaction level."""
        return 1

    def _read_counter_flag(worker, flag_name):
        """Read numeric value from a worker counter flag."""
        value = 0
        flag_value = worker.get("flags", {}).get(flag_name)
        if flag_value is not None:
            if hasattr(flag_value, 'get') and "value" in flag_value:
                value = flag_value.get("value", 0)
            elif isinstance(flag_value, (int, float)):
                value = int(flag_value)
        return value

    def get_category_progress_subtitle(worker, category_name):
        """
        Build subtitle text for branch progression hints shown in category screens.
        """
        tracked_categories = {"Discipline", "Romance", "Friendship"}
        if category_name not in tracked_categories:
            return ""

        interactions = load_interactions()
        _pg = getattr(store, "get_player_manager_gender", None)
        player_gender = _pg() if callable(_pg) else (
            "male" if (store.player_title and store.player_title.lower().strip() == "lord") else "female"
        )
        filtered = filter_interactions_by_gender(interactions, player_gender)
        filtered = filter_interactions_by_worker_gender(filtered, worker)
        filtered = filter_interactions_by_worker_name(filtered, worker)

        category_interactions = [i for i in filtered if category_name in i.get("categories", [])]
        if not category_interactions:
            return ""

        required_uses = get_unlock_required_uses()
        levels = sorted({i.get("interaction_level", 1) for i in category_interactions if i.get("interaction_level", 1) is not None})
        levels = [lvl for lvl in levels if lvl >= 2]
        if not levels:
            return ""

        primary_stat_by_category = {
            "Discipline": "rebelliousness",
            "Romance": "romance",
            "Friendship": "relationship",
        }
        stat_name = primary_stat_by_category.get(category_name)
        stat_label = stat_name.capitalize() if stat_name else "Stat"

        for level in levels:
            prev_level = level - 1
            prev_flag = f"{category_name.lower()}_uses_level_{prev_level}"
            prev_uses = _read_counter_flag(worker, prev_flag)
            uses_ok = prev_uses >= required_uses

            level_interactions = [i for i in category_interactions if i.get("interaction_level", 1) == level]
            level_interactions.sort(key=lambda i: i.get("name", ""))
            target_interaction = level_interactions[0] if level_interactions else None

            threshold = 0
            current_value = worker.get(stat_name, 0) if stat_name else 0
            if target_interaction and stat_name:
                threshold = int(target_interaction.get("stat_requirements", {}).get(stat_name, 0) or 0)

            if stat_name == "rebelliousness":
                stat_ok = current_value < threshold if threshold > 0 else True
            else:
                stat_ok = current_value >= threshold

            if not (uses_ok and stat_ok):
                prev_level_interactions = [i for i in category_interactions if i.get("interaction_level", 1) == prev_level]
                prev_level_interactions.sort(key=lambda i: i.get("name", ""))
                previous_name = prev_level_interactions[0].get("name", f"Level {prev_level} interaction") if prev_level_interactions else f"Level {prev_level} interaction"

                if threshold > 0:
                    return f"Use {previous_name} once, achieve {current_value}/{threshold} {stat_label}."
                return f"Use {previous_name} once."

        return "All progression requirements completed for this branch."

    def filter_interactions_by_unlock_level(interactions, worker):
        """
        Filter interactions based on unlock level system.
        Each category has 4 levels:
        - Level 1: Always available
        - Level 2: Unlocked after 1 use of level 1
        - Level 3: Unlocked after 1 use of level 2
        - Level 4: Unlocked after 1 use of level 3
        """
        filtered = []
        if not worker.get("flags"):
            worker["flags"] = {}
        
        progression_categories = {"Discipline", "Romance", "Friendship"}
        for interaction in interactions:
            raw_level = interaction.get("interaction_level", 1)
            if raw_level is None:
                interaction_level = None
            else:
                try:
                    interaction_level = int(raw_level)
                except (TypeError, ValueError):
                    interaction_level = 1
            category = interaction.get("categories", [])
            
            # Backwards compatibility: include only when NOT a progression interaction with invalid level.
            # Progression interactions (Discipline, Romance, Friendship) with level 0 or None must never
            # bypass the unlock check - they would show tier 2+ content on day 1.
            if not category or interaction_level is None or interaction_level <= 0:
                main_cat = category[0] if category else None
                if main_cat in progression_categories and (interaction_level is None or interaction_level <= 0):
                    continue  # Skip malformed progression interaction (level 0 or null)
                filtered.append(interaction)
                continue
            
            # Get the main category (first one)
            main_category = category[0] if category else "Other"
            
            # Build flag name for tracking uses in this category
            category_flag_base = f"{main_category.lower()}_uses"

            # Branch finale exclusivity:
            # If the worker has completed a level 5 "finale" in one branch,
            # block level 5 interactions in the other branches. This makes
            # reaching level 5 a meaningful, mutually exclusive choice.
            if interaction_level >= 5:
                interaction_id = interaction.get("id", "") or ""

                # Exception: selling is not a "finale" and must remain available
                # even after choosing a Discipline L5 outcome.
                if interaction_id != "discipline_level5_sell_specialty_buyer":
                    def _flag_is_true(flag_name):
                        v = worker.get("flags", {}).get(flag_name)
                        if v is None:
                            return False
                        # Handle dict-style flags: {"value": X, "duration": Y}
                        if hasattr(v, 'get') and "value" in v:
                            return bool(v.get("value", False))
                        return bool(v)

                    # Currently implemented finales:
                    # - Romance: "Confess Feelings" sets romance_confess_done
                    # - Friendship: "Become Confidants" sets friendship_final_done
                    # - Discipline: choosing a path sets discipline_final_done
                    romance_final_done = _flag_is_true("romance_confess_done")
                    friendship_final_done = _flag_is_true("friendship_final_done")
                    discipline_final_done = _flag_is_true("discipline_final_done")

                    if romance_final_done or friendship_final_done or discipline_final_done:
                        # If any branch finale is done, prevent reaching level 5 in other branches.
                        # (The exception above keeps the Discipline sale action visible.)
                        continue
            
            # Level 1 is always available
            if interaction_level == 1:
                filtered.append(interaction)
                continue
            
            # For levels 2+, check if previous level has been used enough
            required_uses = get_unlock_required_uses()
            previous_level = interaction_level - 1
            
            # Check uses of previous level
            previous_level_flag = f"{category_flag_base}_level_{previous_level}"
            previous_uses = _read_counter_flag(worker, previous_level_flag)
            
            # Unlock if previous level has been used enough times
            if previous_uses >= required_uses:
                filtered.append(interaction)
        
        return filtered
        
    def filter_interactions_by_traits(interactions, worker):
        """Filter interactions based on worker traits."""
        filtered = []
        for interaction in interactions:
            # Check required traits
            required_traits = interaction.get("required_traits", [])
            excluded_traits = interaction.get("excluded_traits", [])
            worker_traits = worker.get("traits", [])
            
            has_required_traits = all(trait in worker_traits for trait in required_traits)
            has_excluded_traits = any(trait in worker_traits for trait in excluded_traits)

            if has_required_traits and not has_excluded_traits:
                filtered.append(interaction)
        
        return filtered
        
    def filter_interactions_by_worker_name(interactions, worker):
        """Filter interactions based on worker name."""
        filtered = []
        worker_name = worker.get("name", "Unknown")
        renpy.log(f"Filtering interactions for worker: {worker_name}")
        
        for interaction in interactions:
            # Check if interaction is restricted to specific workers
            specific_workers = interaction.get("specific_workers", [])
            
            # Debug log for interactions with specific workers
            if specific_workers:
                renpy.log(f"Found interaction '{interaction.get('name')}' for specific workers: {specific_workers}")
                
            # If not restricted to specific workers, include it
            if not specific_workers:
                filtered.append(interaction)
                continue
            
            # Case-insensitive name matching
            worker_name_lower = worker_name.lower() if worker_name else ""
            specific_workers_lower = [name.lower() for name in specific_workers]
                
            # Check if this worker is in the list of specific workers (case-insensitive)
            if worker_name_lower in specific_workers_lower:
                renpy.log(f"✓ Added specific interaction for {worker_name}: {interaction.get('name')}")
                filtered.append(interaction)
            else:
                renpy.log(f"✗ Skipped specific interaction, not for {worker_name}: {interaction.get('name')} (looking for {specific_workers})")
        
        return filtered

    def get_available_interactions_for_worker(worker):
        """
        Return the list of interactions available for this worker (same logic as the interaction menu).
        Use this for both the interaction menu and Take a walk so filtering stays in one place.
        """
        interactions = load_interactions()
        _pg = getattr(store, "get_player_manager_gender", None)
        player_gender = _pg() if callable(_pg) else (
            "male" if (store.player_title and store.player_title.lower().strip() == "lord") else "female"
        )
        filtered = filter_interactions_by_gender(interactions, player_gender)
        filtered = filter_interactions_by_worker_gender(filtered, worker)
        filtered = filter_interactions_by_stats(filtered, worker)
        filtered = filter_interactions_by_flags(filtered, worker)
        filtered = filter_interactions_by_traits(filtered, worker)
        filtered = filter_interactions_by_items(filtered, worker)
        filtered = filter_interactions_by_usage_limits(filtered, worker)
        filtered = filter_interactions_by_unlock_level(filtered, worker)
        filtered = filter_interactions_by_worker_name(filtered, worker)
        # Meta row: shared training UI/stat strings live in interactions_training.json only (not a real interaction).
        filtered = [i for i in filtered if hasattr(i, "get") and i.get("id") != "_training_flow_copy"]
        # Academy library quest: manager-led Training interactions stay locked until the sealed manual is recovered.
        if not store.event_flags.get("academy_lib_manual_found"):
            _fn_tr = getattr(store, "is_training_interaction", None)
            if callable(_fn_tr):
                filtered = [i for i in filtered if not _fn_tr(i)]
        return filtered
        
    def categorize_interactions(interactions):
        """
        Categorize interactions into predefined and custom categories.
        Returns a dictionary with category names as keys and lists of interactions as values.
        """
        categories = {
            "Discipline": [],
            "Romance": [],
            "Friendship": [],
            "Training": [],
            # "Joy": [],  # Commented out: Joy category removed - romance and relationship already influence joy
            "Other": []
        }
        
        for interaction in interactions:
            # First check for explicit categories
            explicit_categories = interaction.get("categories", [])
            if explicit_categories:
                # Add interaction to each of its explicit categories
                for category in explicit_categories:
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(interaction)
                continue
            
            # If no explicit categories, categorize based on effects
            effects = interaction.get("effect", {})
            categorized = False
            
            if "rebelliousness" in effects and effects["rebelliousness"] < 0:
                categories["Discipline"].append(interaction)
                categorized = True
            if "relationship" in effects and effects["relationship"] > 0:
                categories["Friendship"].append(interaction)
                categorized = True
            if "romance" in effects and effects["romance"] > 0:
                categories["Romance"].append(interaction)
                categorized = True
            # Joy category commented out - interactions with joy effects will go to Other or their explicit categories
            # if "joy" in effects and effects["joy"] > 0:
            #     categories["Joy"].append(interaction)
            #     categorized = True
            
            # If not categorized by effects, put in Other
            if not categorized:
                categories["Other"].append(interaction)
        
        # Remove empty categories (and commented out categories)
        return {k: v for k, v in categories.items() if v and k != "Joy"}

    def get_max_daily_interactions():
        """Maximum interactions the manager can use per day = 2 + Manager Level."""
        return 2 + getattr(store, "manager_level", 1)
    
    def get_worker_interaction_count(worker):
        """Get the manager's total interactions used today (shared pool, not per worker)."""
        return getattr(store, "manager_interactions_today", 0)
    
    def can_interact_with_worker(worker):
        """Check if the manager can perform more interactions today (limit not reached)."""
        current_count = get_worker_interaction_count(worker)
        max_interactions = get_max_daily_interactions()
        return current_count < max_interactions
    
    def increment_manager_interaction_count():
        """Increment the manager's interaction count for today."""
        store.manager_interactions_today = getattr(store, "manager_interactions_today", 0) + 1

    def get_interaction_uses_label(worker, interaction, required_uses=None):
        """
        Return a UI label fragment showing unlock-progress uses for an interaction.
        Example: " (Uses: 1/3)".

        Notes:
        - Uses existing per-category/per-level flags (e.g. romance_uses_level_2).
        - Intentionally hides the counter for Violet's special interaction.
        """
        if not worker or not interaction:
            return ""

        # Keep Violet's special visually outside the level progression UI.
        if interaction.get("id", "") == "violet_special":
            return ""

        categories = interaction.get("categories", [])
        interaction_level = interaction.get("interaction_level", 1)

        if required_uses is None:
            required_uses = get_unlock_required_uses()

        # Show progress only for the leveled progression (L1-L4).
        if not categories or interaction_level is None or interaction_level >= 5:
            return ""

        main_category = categories[0] if categories else "Other"
        level_flag = f"{main_category.lower()}_uses_level_{interaction_level}"

        current_uses = 0
        flag_value = worker.get("flags", {}).get(level_flag)
        if flag_value is not None:
            # Use hasattr instead of isinstance to handle RevertableDict.
            if hasattr(flag_value, 'get') and "value" in flag_value:
                current_uses = flag_value.get("value", 0)
            elif isinstance(flag_value, (int, float)):
                current_uses = int(flag_value)

        return f" (Uses: {current_uses}/{required_uses})"

    def apply_interaction_libido_effect(worker, effects, stat_changes):
        """Apply explicit libido delta from interaction JSON effect.libido."""
        if not hasattr(effects, "get"):
            return
        if "libido" not in effects:
            return

        try:
            libido_delta = int(effects.get("libido", 0))
        except Exception:
            return
        if libido_delta == 0:
            return

        old_libido = int(worker.get("libido", 0) or 0)
        try:
            max_libido = int(get_max_libido(worker))
        except Exception:
            max_libido = 20
        new_libido = max(0, min(max_libido, old_libido + libido_delta))
        if new_libido == old_libido:
            return

        worker["libido"] = new_libido
        stat_changes["libido"] = stat_changes.get("libido", 0) + (new_libido - old_libido)
        renpy.log(
            f"INTERACTION LIBIDO: {worker.get('name', 'Unknown')} "
            f"{old_libido} -> {new_libido} ({new_libido - old_libido:+d})"
        )

    def apply_interaction_effects(worker, interaction, apply_costs=True, skip_daily_limit=False):
        """Apply the effects of an interaction to a worker.
        
        Args:
            worker: The worker to apply effects to
            interaction: The interaction data
            apply_costs: If True, apply energy/health/money costs. If False, skip costs.
            skip_daily_limit: If True, don't count this interaction towards daily limit (e.g., for "take a walk").
        
        Returns:
            dict: Dictionary with stat changes (e.g., {"relationship": 5, "joy": 3})
        """
        # Ensure we update the canonical worker in store.workers so flags/levels persist
        if worker is not None and hasattr(store, "workers"):
            worker_name = worker.get("name") if hasattr(worker, "get") else None
            if worker_name:
                canonical = next((w for w in store.workers if w.get("name") == worker_name), None)
                if canonical is not None:
                    worker = canonical
        
        # Track stat changes for display
        stat_changes = {}
        
        # Increment manager's daily interaction count (unless skipping limit, e.g. Take a Walk)
        if not skip_daily_limit:
            increment_manager_interaction_count()
        # Apply stat changes
        effects = interaction.get("effect", {})
        for stat, change in effects.items():
            if stat not in ("flags", "libido", "add_trait", "remove_trait", "trait_chance", "trait_remove_chance"):  # Handle separately
                if change == 0:
                    continue
                if stat in ("rebelliousness", "joy", "romance", "relationship") and hasattr(store, "apply_attribute_change"):
                    store.apply_attribute_change(worker, stat, change)
                else:
                    current_value = worker.get(stat, 0)
                    new_value = max(0, min(100, current_value + change))
                    worker[stat] = new_value
                stat_changes[stat] = change

        def _coerce_trait_entries(raw):
            if raw is None:
                return []
            if hasattr(raw, "get") and callable(getattr(raw, "get", None)):
                return [raw]
            if isinstance(raw, (str, bytes)):
                return [raw]
            if hasattr(raw, "__iter__"):
                return list(raw)
            return []

        def _trait_name_duration(entry):
            if entry is None:
                return None, 0
            if hasattr(entry, "get") and callable(getattr(entry, "get", None)):
                name = entry.get("name") or entry.get("trait")
                try:
                    dur = int(entry.get("duration", 0) or 0)
                except Exception:
                    dur = 0
                return name, dur
            if isinstance(entry, (str, bytes)):
                return str(entry), 0
            return None, 0

        # Apply add_trait from interaction effect
        add_trait_data = effects.get("add_trait")
        if add_trait_data and worker and hasattr(store, "add_trait_with_duration"):
            for _entry in _coerce_trait_entries(add_trait_data):
                trait_name, duration = _trait_name_duration(_entry)
                if trait_name:
                    store.add_trait_with_duration(worker, trait_name, duration)
                    stat_changes["add_trait"] = trait_name
                    renpy.log(f"Interaction: Added trait '{trait_name}' to {worker.get('name', 'Unknown')}")

        # Apply remove_trait from interaction effect
        remove_trait_data = effects.get("remove_trait")
        if remove_trait_data and worker and hasattr(store, "remove_trait_safe"):
            for _entry in _coerce_trait_entries(remove_trait_data):
                trait_name, _ = _trait_name_duration(_entry)
                if trait_name:
                    store.remove_trait_safe(worker, trait_name)
                    stat_changes["remove_trait"] = trait_name
                    renpy.log(f"Interaction: Removed trait '{trait_name}' from {worker.get('name', 'Unknown')}")

        def _coerce_trait_roll_list(raw):
            if raw is None:
                return []
            # Ren'Py data may be RevertableDict/RevertableList: prioritize dict-like by .get()
            if hasattr(raw, "get") and callable(getattr(raw, "get", None)):
                return [raw]
            if hasattr(raw, "__iter__") and not isinstance(raw, (str, bytes)):
                return list(raw)
            return []

        _tc_list = _coerce_trait_roll_list(effects.get("trait_chance"))
        if _tc_list and worker:
            _fn_tc = getattr(store, "apply_trait_chance_entries", None)
            if callable(_fn_tc):
                _fn_tc(worker, _tc_list, stat_changes, granted_list_key="traits_from_training", log_prefix="Interaction")

        _trc_list = _coerce_trait_roll_list(effects.get("trait_remove_chance"))
        if _trc_list and worker:
            _fn_trc = getattr(store, "apply_trait_remove_chance_entries", None)
            if callable(_fn_trc):
                _fn_trc(worker, _trc_list, stat_changes, removed_list_key="traits_removed_by_chance", log_prefix="Interaction")

        # Apply flag changes
        flag_effects = effects.get("flags", {})
        if not worker.get("flags"):
            worker["flags"] = {}
        
        for flag_name, flag_value in flag_effects.items():
            if flag_value is None:
                # Remove flag if value is None
                if flag_name in worker["flags"]:
                    del worker["flags"][flag_name]
            else:
                # If a *_cooldown flag has duration 0, keep the system intact
                # but make it effectively non-blocking (do not set the flag).
                try:
                    if (
                        isinstance(flag_name, str)
                        and flag_name.endswith("_cooldown")
                        and hasattr(flag_value, 'get')
                        and int(flag_value.get("duration", -1)) == 0
                    ):
                        if flag_name in worker["flags"]:
                            del worker["flags"][flag_name]
                        continue
                except Exception:
                    pass

                # Handle incremental flags (for usage counting)
                # Use hasattr instead of isinstance to handle RevertableDict
                if hasattr(flag_value, 'get') and flag_value.get("increment"):
                    current_flag = worker["flags"].get(flag_name)
                    if current_flag is not None:
                        # Use hasattr instead of isinstance to handle RevertableDict
                        if hasattr(current_flag, 'get') and "value" in current_flag:
                            # Increment existing dict flag
                            new_value = current_flag["value"] + flag_value["value"]
                            worker["flags"][flag_name] = {
                                "value": new_value,
                                "duration": flag_value.get("duration", current_flag.get("duration", -1))
                            }
                        elif isinstance(current_flag, (int, float)):
                            # Convert simple number to dict and increment
                            worker["flags"][flag_name] = {
                                "value": current_flag + flag_value["value"],
                                "duration": flag_value.get("duration", -1)
                            }
                        else:
                            # Set new incremental flag
                            worker["flags"][flag_name] = flag_value
                    else:
                        # Set new incremental flag
                        worker["flags"][flag_name] = flag_value
                else:
                    # Add or update flag normally
                    worker["flags"][flag_name] = flag_value
        
        # Track interaction usage for unlock system
        interaction_level = interaction.get("interaction_level", 1)
        category = interaction.get("categories", [])
        
        if category and interaction_level:
            main_category = category[0] if category else "Other"
            category_flag_base = f"{main_category.lower()}_uses"
            level_flag = f"{category_flag_base}_level_{interaction_level}"
            
            # Increment usage count for this level
            current_uses = 0
            flag_value = worker["flags"].get(level_flag)
            
            if flag_value is not None:
                # Use hasattr instead of isinstance to handle RevertableDict
                if hasattr(flag_value, 'get') and "value" in flag_value:
                    current_uses = flag_value.get("value", 0)
                elif isinstance(flag_value, (int, float)):
                    current_uses = flag_value
            
            # Increment and store
            worker["flags"][level_flag] = {
                "value": current_uses + 1,
                "duration": -1  # Permanent
            }
        
        # Apply costs only if apply_costs is True
        if apply_costs:
            worker["energy"] = max(0, worker["energy"] - interaction.get("cost_energy", 0))
            worker["health"] = max(0, worker["health"] - interaction.get("cost_health", 0))
            # Only subtract cost; do not clamp money to 0 (player can be in debt from other mechanics)
            store.money -= interaction.get("cost_money", 0)

        # Explicit libido stat deltas are defined in interaction JSON (effect.libido).
        # In SFW mode we ignore libido changes entirely.
        if getattr(persistent, "nsfw_enabled", False):
            apply_interaction_libido_effect(worker, effects, stat_changes)

        # Tutorial: Friendly Lunch completion is now handled when closing the interaction_result screen
        
        return stat_changes

    def get_interaction_image(worker, interaction):
        """
        Returns an image for the given interaction, prioritizing the worker's folder over the default folder.
        Uses robust flexible matching for better compatibility with different file formats and naming.
        Uses cache to maintain the same image throughout the entire interaction.
        
        Args:
            worker: Objeto trabajador (diccionario)
            interaction: Interacción actual (diccionario)
            
        Returns:
            Ruta a la imagen de la interacción
        """
        worker_name = worker.get("name", "unknown") if hasattr(worker, "get") else "unknown"
        interaction_id = interaction.get("id", "unknown") if hasattr(interaction, "get") else "unknown"
        cache_key = f"{worker_name}_{interaction_id}_interaction_image"
        
        # NOTE: We intentionally do NOT early-return a cached image here.
        # We want to respect priority (interaction-specific > category fallback),
        # and only use the cache within the chosen priority tier.
        
        fallback = get_fallback_folder(worker)
        if hasattr(worker, "get") and callable(worker.get):
            worker_folder = worker.get("folder", fallback)
        else:
            worker_folder = fallback
        
        base_folder = f"images/workers/{worker_folder}/"
        
        image_base = interaction.get("image")
        categories = interaction.get("categories", []) or []
        is_player_male = store.player_title and store.player_title.lower().strip() == "lord"
        player_title_suffix = "_lord" if is_player_male else "_lady"
        legacy_player_gendered_suffix = "_male" if is_player_male else "_female"

        # Preparar candidatos por prioridad
        candidate_bases = []
        if "Training" in categories:
            candidate_bases.extend(training_interaction_primary_candidate_bases(worker, interaction))
        elif image_base:
            candidate_bases.append(f"{image_base}{player_title_suffix}")
            candidate_bases.append(f"{image_base}{legacy_player_gendered_suffix}")
            candidate_bases.append(image_base)

        if "Training" not in categories and "Romance" in categories:
            # Romance images should show the player, so use player gender
            if is_player_male:
                candidate_bases.append("romance_male")
            else:
                candidate_bases.append("romance_female")
        elif "Friendship" in categories:
            candidate_bases.append("friendship")
        elif "Discipline" in categories:
            candidate_bases.append("obedience")
        
        # Priority-based search:
        # pick the FIRST candidate base that has matches, and choose (cached) within that tier.
        is_training = "Training" in categories
        chosen_matches = []
        for base in candidate_bases:
            if not base:
                continue
            matches = (
                get_training_primary_image_matches(base_folder, base)
                if is_training
                else get_image_matches_flexible(base_folder, base)
            )
            if matches:
                chosen_matches = matches
                break

        if chosen_matches:
            return get_cached_choice(chosen_matches, cache_key)

        if is_training:
            _tsk = interaction.get("training_skill") if hasattr(interaction, "get") else None
            if _tsk:
                skill_media = get_worker_image(worker, _tsk, outcome="success")
                if skill_media:
                    get_cached_choice([skill_media], cache_key)
                    return skill_media
        
        profile_image = get_worker_image(worker)
        get_cached_choice([profile_image], cache_key)
        return profile_image
    
    def start_take_a_walk():
        """
        Function to handle Take a Walk feature without nested contexts.
        Returns True if walk was started, False if it couldn't be started.
        """
        # Prevent re-entry if already running
        if store.take_a_walk_in_progress:
            renpy.log("Take a walk already in progress, aborting")
            return False
        
        store.take_a_walk_in_progress = True
        store.take_a_walk_fail_message = None
        
        # Check if already used today
        if store.last_take_a_walk_day == store.current_day:
            store.take_a_walk_fail_message = "You've already taken a walk today. Come back tomorrow."
            store.take_a_walk_in_progress = False
            return False
        
        # Check if there are any workers available
        if not store.workers or len(store.workers) == 0:
            store.take_a_walk_fail_message = "You need workers to take a walk. Hire some first."
            store.take_a_walk_in_progress = False
            return False
        
        # Select a random worker - resolve canonical reference from store.workers
        import random
        selected_worker = random.choice(store.workers)
        worker_name = selected_worker.get("name", "Unknown")
        canonical_worker = next((w for w in store.workers if w.get("name") == worker_name), selected_worker)
        
        # Use the same list as the interaction menu: only interactions this worker has available.
        # All filters (stats, flags, traits, unlock level, etc.) must pass - never show tier 2+ on day 1.
        available_interactions = get_available_interactions_for_worker(canonical_worker)
        available_interactions = [i for i in available_interactions if not is_training_interaction(i)]
        # Take a walk is always a SFW pool (city stroll), even when persistent.nsfw_enabled is True.
        available_interactions = [i for i in available_interactions if not (hasattr(i, "get") and i.get("nsfw", False))]
        
        if not available_interactions:
            store.take_a_walk_fail_message = f"{worker_name} doesn't have any interactions available at the moment."
            store.take_a_walk_in_progress = False
            return False
        
        # Select a random interaction - must be one the worker could choose in the interaction menu
        chosen_interaction = random.choice(available_interactions)
        
        # Safety: ensure chosen interaction is still in the filtered list (defensive against edge cases)
        chosen_id = chosen_interaction.get("id", "")
        if not any(i.get("id") == chosen_id for i in available_interactions):
            renpy.log(f"Take a walk: chosen interaction {chosen_id} not in available list, aborting")
            store.take_a_walk_fail_message = f"Could not select a valid interaction for {worker_name}."
            store.take_a_walk_in_progress = False
            return False
        
        interaction_name = chosen_interaction.get("name", "interaction")
        interaction_name_lower = interaction_name.lower()
        
        # Apply interaction effects (without costs for "take a walk", and skip daily limit)
        apply_interaction_effects(canonical_worker, chosen_interaction, apply_costs=False, skip_daily_limit=True)
        
        # Mark as used today
        store.last_take_a_walk_day = store.current_day
        
        # Store the interaction data for the screen to display
        store.walk_worker = canonical_worker
        store.walk_interaction = chosen_interaction
        # One art pick for the whole walk (each stage is a fresh call screen; do not re-roll per click).
        store.walk_interaction_media = get_interaction_image(canonical_worker, chosen_interaction)
        store.walk_intro_text_1 = "I take a walk through the city..."
        store.walk_intro_text_2 = f"...and I encounter {worker_name}."
        store.walk_intro_text_3 = f"I decide it's time to have a {interaction_name_lower} with {worker_name}."
        
        # Reset the flag
        store.take_a_walk_in_progress = False
        
        renpy.log(f"Take a walk prepared with {worker_name} and {interaction_name}")
        return True

