init -1 python:
    import copy as _copy

    def _collect_game_state() -> dict:
        """Return a plain-JSON snapshot of the current game state.
        Keep to basic types (dict, list, str, int, float, bool, None).
        """
        state = {}
        try:
            # Ensure building data is consistent before snapshotting
            validate_and_sync_buildings()
            # Core economy and collections
            state["money"] = int(store.money) if hasattr(store, "money") else 5000
            state["workers"] = _copy.deepcopy(getattr(store, "workers", []))
            state["available_buildings"] = _copy.deepcopy(getattr(store, "available_buildings", {}))
            state["manager_inventory"] = _copy.deepcopy(getattr(store, "manager_inventory", []))
            state["owned_buildings"] = _copy.deepcopy(getattr(store, "owned_buildings", []))
            state["custom_names"] = _copy.deepcopy(getattr(store, "custom_names", {}))
            state["unlocked_shops"] = _copy.deepcopy(getattr(store, "unlocked_shops", {}))

            # Player meta
            state["player_name"] = getattr(store, "player_name", "")
            state["player_title"] = getattr(store, "player_title", "")
            state["tutorial_active"] = getattr(store, "tutorial_active", True)
            state["current_objective"] = getattr(store, "current_objective", 1)
            
            # Objective completion states
            state["objective_1_complete"] = getattr(store, "objective_1_complete", False)
            state["objective_2_complete"] = getattr(store, "objective_2_complete", False)
            state["objective_3_complete"] = getattr(store, "objective_3_complete", False)
            state["objective_4_complete"] = getattr(store, "objective_4_complete", False)
            state["objective_5_complete"] = getattr(store, "objective_5_complete", False)
            state["objective_6_complete"] = getattr(store, "objective_6_complete", False)
            state["objective_7_complete"] = getattr(store, "objective_7_complete", False)
            state["objective_8_complete"] = getattr(store, "objective_8_complete", False)
            state["objective_9_complete"] = getattr(store, "objective_9_complete", False)
            state["objective_10_complete"] = getattr(store, "objective_10_complete", False)
            state["objective_11_complete"] = getattr(store, "objective_11_complete", False)
            state["objective_12_complete"] = getattr(store, "objective_12_complete", False)
            state["objective_13_complete"] = getattr(store, "objective_13_complete", False)
            state["objective_14_complete"] = getattr(store, "objective_14_complete", False)
            state["objective_15_complete"] = getattr(store, "objective_15_complete", False)
            state["objective_16_complete"] = getattr(store, "objective_16_complete", False)

            # Governor's Tension System
            state["governor_attention"] = getattr(store, "governor_attention", 0)
            state["governor_retaliation_done"] = getattr(store, "governor_retaliation_done", False)
            state["governor_tension_active"] = getattr(store, "governor_tension_active", False)
            state["vengeance_path_chosen"] = getattr(store, "vengeance_path_chosen", False)
            state["vengeance_path"] = getattr(store, "vengeance_path", "")

            # Calendar (redundant with persistent, but include for completeness)
            state["current_day"] = getattr(store, "current_day", 1)
            state["current_month"] = getattr(store, "current_month", 1)
            state["current_year"] = getattr(store, "current_year", 1)
            state["last_save_slot"] = getattr(store, "last_save_slot", None)

            # Event tracking (critical for event system)
            state["event_flags"] = _copy.deepcopy(getattr(store, "event_flags", {}))
            state["event_occurrences"] = _copy.deepcopy(getattr(store, "event_occurrences", {}))
            state["event_last_occurred"] = _copy.deepcopy(getattr(store, "event_last_occurred", {}))

            # Daily interaction tracking
            state["worker_interactions_today"] = _copy.deepcopy(getattr(store, "worker_interactions_today", {}))
            state["last_take_a_walk_day"] = getattr(store, "last_take_a_walk_day", None)

            # Flags
            state["game_initialized"] = True
        except Exception as e:
            renpy.log("SAVE_STATE: error collecting state: " + str(e))
        return state

    def _apply_game_state(state: dict) -> None:
        """Apply a previously saved plain-JSON snapshot to store variables."""
        try:
            if not state:
                return
            # Core
            if "money" in state:
                store.money = int(state["money"])
            if "workers" in state:
                store.workers = _copy.deepcopy(state["workers"]) or []
                # Deduplicate workers by name to avoid save-induced duplicates
                try:
                    seen_names = set()
                    deduped_workers = []
                    for w in store.workers:
                        wname = w.get("name")
                        if wname in seen_names:
                            renpy.log(f"SAVE_STATE: duplicate worker '{wname}' in workers list, skipping")
                            continue
                        deduped_workers.append(w)
                        if wname:
                            seen_names.add(wname)
                    store.workers = deduped_workers
                except Exception as e:
                    renpy.log("SAVE_STATE: error deduping workers: " + str(e))
            if "available_buildings" in state:
                store.available_buildings = _copy.deepcopy(state["available_buildings"]) or {}
                # Deduplicate assigned_servants in each building and relink to store.workers
                # Also ensure base_level is present and valid
                try:
                    name_to_worker = {w.get("name"): w for w in store.workers}
                    for bname, building in store.available_buildings.items():
                        if not isinstance(building, dict):
                            continue
                        # Ensure base_level exists and is valid (persist building levels)
                        if "base_level" not in building or not isinstance(building.get("base_level"), int) or building["base_level"] < 1:
                            building["base_level"] = building.get("base_level", 1)
                            renpy.log(f"SAVE_STATE: initialized/restored base_level for {bname} to {building['base_level']}")
                        assigned = building.get("assigned_servants", []) or []
                        if not assigned:
                            continue
                        seen_names = set()
                        deduped = []
                        for sw in assigned:
                            wname = sw.get("name") if isinstance(sw, dict) else None
                            if wname in seen_names:
                                renpy.log(f"SAVE_STATE: duplicate assigned_servant '{wname}' in {bname}, skipping")
                                continue
                            # Relink to canonical store.workers object
                            deduped.append(name_to_worker.get(wname, sw))
                            if wname:
                                seen_names.add(wname)
                        building["assigned_servants"] = deduped
                        # Ensure servant_jobs exists
                        if "servant_jobs" not in building or not isinstance(building["servant_jobs"], dict):
                            building["servant_jobs"] = {}
                except Exception as e:
                    renpy.log("SAVE_STATE: error deduping building servants: " + str(e))
            if "manager_inventory" in state:
                store.manager_inventory = _copy.deepcopy(state["manager_inventory"]) or []
            if "owned_buildings" in state:
                store.owned_buildings = _copy.deepcopy(state["owned_buildings"]) or []
            if "custom_names" in state:
                store.custom_names = _copy.deepcopy(state["custom_names"]) or {}
            
            # IMPORTANTE: Validar y sincronizar edificios ANTES de normalizar asignaciones
            # Esto asegura que todos los edificios en owned_buildings existan en available_buildings
            # antes de que cualquier código intente acceder a ellos
            try:
                validate_and_sync_buildings()
                renpy.log("SAVE_STATE: validate_and_sync_buildings completed (early)")
            except Exception as e:
                renpy.log("SAVE_STATE: validate_and_sync_buildings error (early): " + str(e))
            if "unlocked_shops" in state:
                store.unlocked_shops = _copy.deepcopy(state["unlocked_shops"]) or {}

            # Meta
            if "player_name" in state:
                store.player_name = state["player_name"]
            if "player_title" in state:
                store.player_title = state["player_title"]
            if "tutorial_active" in state:
                store.tutorial_active = state["tutorial_active"]
            if "current_objective" in state:
                store.current_objective = state["current_objective"]
            
            # Restore objective completion states
            if "objective_1_complete" in state:
                store.objective_1_complete = state["objective_1_complete"]
            if "objective_2_complete" in state:
                store.objective_2_complete = state["objective_2_complete"]
            if "objective_3_complete" in state:
                store.objective_3_complete = state["objective_3_complete"]
            if "objective_4_complete" in state:
                store.objective_4_complete = state["objective_4_complete"]
            if "objective_5_complete" in state:
                store.objective_5_complete = state["objective_5_complete"]
            if "objective_6_complete" in state:
                store.objective_6_complete = state["objective_6_complete"]
            if "objective_7_complete" in state:
                store.objective_7_complete = state["objective_7_complete"]
            if "objective_8_complete" in state:
                store.objective_8_complete = state["objective_8_complete"]
            if "objective_9_complete" in state:
                store.objective_9_complete = state["objective_9_complete"]
            if "objective_10_complete" in state:
                store.objective_10_complete = state["objective_10_complete"]
            if "objective_11_complete" in state:
                store.objective_11_complete = state["objective_11_complete"]
            if "objective_12_complete" in state:
                store.objective_12_complete = state["objective_12_complete"]
            if "objective_13_complete" in state:
                store.objective_13_complete = state["objective_13_complete"]
            if "objective_14_complete" in state:
                store.objective_14_complete = state["objective_14_complete"]
            if "objective_15_complete" in state:
                store.objective_15_complete = state["objective_15_complete"]
            if "objective_16_complete" in state:
                store.objective_16_complete = state["objective_16_complete"]

            # Governor's Tension System
            if "governor_attention" in state:
                store.governor_attention = state["governor_attention"]
            if "governor_retaliation_done" in state:
                store.governor_retaliation_done = state["governor_retaliation_done"]
            if "governor_tension_active" in state:
                store.governor_tension_active = state["governor_tension_active"]
            if "vengeance_path_chosen" in state:
                store.vengeance_path_chosen = state["vengeance_path_chosen"]
            if "vengeance_path" in state:
                store.vengeance_path = state["vengeance_path"]

            # Calendar - keep per-save, do not sync to persistent (avoids cross-save bleed)
            if "current_day" in state:
                old_day = getattr(store, "current_day", None)
                store.current_day = int(state["current_day"])
                renpy.log(f"SAVE_STATE: Restored current_day from JSON: {old_day} -> {store.current_day}")
            if "current_month" in state:
                old_month = getattr(store, "current_month", None)
                store.current_month = int(state["current_month"])
                renpy.log(f"SAVE_STATE: Restored current_month from JSON: {old_month} -> {store.current_month}")
            if "current_year" in state:
                old_year = getattr(store, "current_year", None)
                store.current_year = int(state["current_year"])
                renpy.log(f"SAVE_STATE: Restored current_year from JSON: {old_year} -> {store.current_year}")
            if "current_day" in state or "current_month" in state or "current_year" in state:
                renpy.log(f"SAVE_STATE: Calendar fully restored from JSON: Day {store.current_day}/{store.current_month}/{store.current_year}")
            if "last_save_slot" in state:
                store.last_save_slot = state["last_save_slot"]

            # SYNC OBJECTIVES FOR OLD SAVES: If current_objective > N, all objectives 1 to N-1 must be complete
            # This fixes old saves where objective completion states weren't saved
            current_obj = getattr(store, "current_objective", 1)
            if current_obj > 1:
                for i in range(1, current_obj):
                    obj_var = f"objective_{i}_complete"
                    if not getattr(store, obj_var, False):
                        setattr(store, obj_var, True)
                        renpy.log(f"SAVE_STATE: Synced {obj_var} to True (current_objective={current_obj})")

            # Event tracking (critical for event system)
            if "event_flags" in state:
                store.event_flags = _copy.deepcopy(state["event_flags"]) or {}
            if "event_occurrences" in state:
                store.event_occurrences = _copy.deepcopy(state["event_occurrences"]) or {}
            if "event_last_occurred" in state:
                store.event_last_occurred = _copy.deepcopy(state["event_last_occurred"]) or {}

            # Daily interaction tracking
            if "worker_interactions_today" in state:
                store.worker_interactions_today = _copy.deepcopy(state["worker_interactions_today"]) or {}
            if "last_take_a_walk_day" in state:
                store.last_take_a_walk_day = state["last_take_a_walk_day"]

            # Validate and sync buildings before normalization
            try:
                validate_and_sync_buildings()
                renpy.log("SAVE_STATE: validate_and_sync_buildings completed")
            except Exception as e:
                renpy.log("SAVE_STATE: validate_and_sync_buildings error: " + str(e))

            # Final normalization pass to ensure no duplicates
            try:
                normalize_building_assignments()
                renpy.log("SAVE_STATE: normalize_building_assignments completed")
            except Exception as e:
                renpy.log("SAVE_STATE: normalize error: " + str(e))

            # Mark game as initialized AFTER successful load
            # Note: persistent.loaded_via_save is already cleared by snapshot system
            store.game_initialized = True
            # Mark that we just loaded (used to prevent "Start" from re-running the intro)
            store._just_loaded = True
            renpy.log("SAVE_STATE: state applied during load, game_initialized set to True")
        except Exception as e:
            renpy.log("SAVE_STATE: error applying state: " + str(e))

    def _save_json_cb(data: dict) -> dict:
        try:
            snapshot = _collect_game_state()
            data = dict(data or {})
            data["game_state"] = snapshot
            renpy.log("SAVE_STATE: snapshot stored in save JSON")
            return data
        except Exception as e:
            renpy.log("SAVE_STATE: save callback error: " + str(e))
            return data

    def _load_json_cb(data: dict) -> dict:
        try:
            state = (data or {}).get("game_state")
            if state:
                _apply_game_state(state)
            return data
        except Exception as e:
            renpy.log("SAVE_STATE: load callback error: " + str(e))
            return data

    # Register save AND load callbacks exactly once.
    if not hasattr(store, "_save_state_callbacks_registered"):
        try:
            config.save_json_callbacks.append(_save_json_cb)
            renpy.log("SAVE_STATE: save callback registered")
        except Exception as e:
            renpy.log("SAVE_STATE: could not register save callback: " + str(e))
        
        # Try to register load callback - this is the primary source of truth for loading
        try:
            if hasattr(config, "load_json_callbacks"):
                config.load_json_callbacks.append(_load_json_cb)
                renpy.log("SAVE_STATE: load callback registered (JSON-based restore)")
            else:
                renpy.log("SAVE_STATE: load_json_callbacks not available, will rely on after_load")
        except Exception as e:
            renpy.log("SAVE_STATE: could not register load callback: " + str(e))
        
        store._save_state_callbacks_registered = True


