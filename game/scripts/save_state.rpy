init -1 python:
    import copy as _copy

    def _collect_game_state() -> dict:
        """Return a plain-JSON snapshot of the current game state.
        Keep to basic types (dict, list, str, int, float, bool, None).
        """
        state = {}
        try:
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

            # Calendar (redundant with persistent, but include for completeness)
            state["current_day"] = getattr(store, "current_day", 1)
            state["current_month"] = getattr(store, "current_month", 1)
            state["current_year"] = getattr(store, "current_year", 1)

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
                try:
                    name_to_worker = {w.get("name"): w for w in store.workers}
                    for bname, building in store.available_buildings.items():
                        if not isinstance(building, dict):
                            continue
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
            if "unlocked_shops" in state:
                store.unlocked_shops = _copy.deepcopy(state["unlocked_shops"]) or {}
                # Sync persistent.unlocked_shops with restored store.unlocked_shops
                if store.unlocked_shops:
                    persistent.unlocked_shops = _copy.deepcopy(store.unlocked_shops)
                    renpy.log(f"SAVE_STATE: Synced persistent.unlocked_shops from JSON: {persistent.unlocked_shops}")

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

            # Calendar - sync both store and persistent
            if "current_day" in state:
                store.current_day = state["current_day"]
                persistent.current_day = state["current_day"]
            if "current_month" in state:
                store.current_month = state["current_month"]
                persistent.current_month = state["current_month"]
            if "current_year" in state:
                store.current_year = state["current_year"]
                persistent.current_year = state["current_year"]

            # Optional: flags if present (future-proof)
            if "event_flags" in state:
                store.event_flags = _copy.deepcopy(state["event_flags"]) or store.event_flags

            # Final normalization pass to ensure no duplicates
            try:
                normalize_building_assignments()
                renpy.log("SAVE_STATE: normalize_building_assignments completed")
            except Exception as e:
                renpy.log("SAVE_STATE: normalize error: " + str(e))

            # Guard
            store.game_initialized = True
            persistent.loaded_via_save = True
            renpy.log("SAVE_STATE: state applied during load")
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


