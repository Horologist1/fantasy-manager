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
            if "available_buildings" in state:
                store.available_buildings = _copy.deepcopy(state["available_buildings"]) or {}
            if "manager_inventory" in state:
                store.manager_inventory = _copy.deepcopy(state["manager_inventory"]) or []
            if "owned_buildings" in state:
                store.owned_buildings = _copy.deepcopy(state["owned_buildings"]) or []
            if "custom_names" in state:
                store.custom_names = _copy.deepcopy(state["custom_names"]) or {}
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

    # Register save callback exactly once. Not all Ren'Py versions expose
    # load_json_callbacks, so we apply on after_load instead.
    if not hasattr(store, "_save_state_callbacks_registered"):
        try:
            config.save_json_callbacks.append(_save_json_cb)
        except Exception as e:
            renpy.log("SAVE_STATE: could not register save callback: " + str(e))
        store._save_state_callbacks_registered = True
        renpy.log("SAVE_STATE: save callback registered")


