init python:
    import copy as _cp

    # Ensure snapshot store is a dict (older persistents may hold None or other)
    if not isinstance(getattr(persistent, "_slot_snapshots", None), dict):
        persistent._slot_snapshots = {}

    def _build_snapshot() -> dict:
        # Detect current screen context
        current_screen_context = "tavern"  # default
        try:
            # Check which screens are currently shown using renpy.get_screen()
            # renpy.get_screen() returns the screen object if shown, None otherwise
            if renpy.get_screen("daily_report"):
                current_screen_context = "daily_report"
            elif renpy.get_screen("tavern"):
                current_screen_context = "tavern"
            elif renpy.get_screen("workers"):
                current_screen_context = "workers"
            elif renpy.get_screen("Building_select_global"):
                current_screen_context = "buildings"
            elif renpy.get_screen("map_screen"):
                current_screen_context = "map"
            elif renpy.get_screen("journal_panel"):
                current_screen_context = "journal"
            elif renpy.get_screen("manager_inventory"):
                current_screen_context = "inventory"
            # Add more contexts as needed
            
            renpy.log(f"SNAPSHOT: detected screen context = {current_screen_context}")
        except Exception as e:
            renpy.log(f"SNAPSHOT: error detecting screen context: {e}")
            current_screen_context = "tavern"  # fallback
        
        return {
            # Screen context - NEW!
            "screen_context": current_screen_context,
            "money": int(store.money) if hasattr(store, "money") else 5000,
            "workers": _cp.deepcopy(getattr(store, "workers", [])) or [],
            "available_buildings": _cp.deepcopy(getattr(store, "available_buildings", {})) or {},
            "manager_inventory": _cp.deepcopy(getattr(store, "manager_inventory", [])) or [],
            "owned_buildings": _cp.deepcopy(getattr(store, "owned_buildings", [])) or [],
            "custom_names": _cp.deepcopy(getattr(store, "custom_names", {})) or {},
            "unlocked_shops": _cp.deepcopy(getattr(store, "unlocked_shops", {})) or {},
            "player_name": getattr(store, "player_name", ""),
            "player_title": getattr(store, "player_title", ""),
            "current_day": getattr(store, "current_day", 1),
            "current_month": getattr(store, "current_month", 1),
            "current_year": getattr(store, "current_year", 1),
            # Derived tracking fields for XP/skills to ensure persistence
            "_skill_uses": _cp.deepcopy({w.get("name"): w.get("skill_uses", {}) for w in getattr(store, "workers", [])}),
            "_success_counts": _cp.deepcopy({w.get("name"): w.get("success_count", 0) for w in getattr(store, "workers", [])}),
            # Per-worker inventories, traits, secondary stats and base skills
            "_worker_inventories": _cp.deepcopy({w.get("name"): w.get("inventory", []) for w in getattr(store, "workers", [])}),
            "_worker_traits": _cp.deepcopy({w.get("name"): w.get("traits", []) for w in getattr(store, "workers", [])}),
            "_worker_trait_durations": _cp.deepcopy({w.get("name"): w.get("trait_durations", {}) for w in getattr(store, "workers", [])}),
            "_worker_temporary_traits": _cp.deepcopy({w.get("name"): w.get("temporary_traits", {}) for w in getattr(store, "workers", [])}),
            "_worker_skills": _cp.deepcopy({w.get("name"): w.get("skills", {}) for w in getattr(store, "workers", [])}),
            "_worker_secondary": _cp.deepcopy({
                w.get("name"): {
                    "joy": w.get("joy", 50),
                    "rebelliousness": w.get("rebelliousness", 50),
                    "romance": w.get("romance", 0),
                    "relationship": w.get("relationship", 10 + w.get("comfort_level", 1)),
                    "comfort_level": w.get("comfort_level", 1),
                    "comfort_desired": w.get("comfort_desired", 1),
                    "libido": w.get("libido", 10),
                    "level": w.get("level", 1),
                    "health": w.get("health", 0),
                    "energy": w.get("energy", 0)
                }
                for w in getattr(store, "workers", [])
            }),
            # Building-specific inventories or state if present
            "_building_inventories": _cp.deepcopy({bname: b.get("inventory", []) for bname, b in getattr(store, "available_buildings", {}).items()}),
            "_building_skill_bonus": _cp.deepcopy({bname: b.get("skill_bonus", 0) for bname, b in getattr(store, "available_buildings", {}).items()}),
            "_building_base_levels": _cp.deepcopy({bname: b.get("base_level", 1) for bname, b in getattr(store, "available_buildings", {}).items()}),
            # Event/journal flags and progress
            "_event_flags": _cp.deepcopy(getattr(store, "event_flags", {})),
            "_event_occurrences": _cp.deepcopy(getattr(store, "event_occurrences", {})),
            "_event_last_occurred": _cp.deepcopy(getattr(store, "event_last_occurred", {})),
            "_journal_state": {
                "tutorial_active": getattr(store, "tutorial_active", False),
                "current_objective": getattr(store, "current_objective", 0),
                "objective_1_complete": getattr(store, "objective_1_complete", False),
                "objective_2_complete": getattr(store, "objective_2_complete", False),
                "objective_3_complete": getattr(store, "objective_3_complete", False),
                "objective_4_complete": getattr(store, "objective_4_complete", False),
                "objective_5_complete": getattr(store, "objective_5_complete", False),
                "objective_6_complete": getattr(store, "objective_6_complete", False),
                "objective_4_dialogue_shown": getattr(store, "objective_4_dialogue_shown", False)
            },
        }

    def _apply_snapshot(s: dict) -> None:
        if not s:
            return
        store.money = int(s.get("money", 5000))
        # Restore workers first
        store.workers = _cp.deepcopy(s.get("workers", []))
        # Restore buildings next
        store.available_buildings = _cp.deepcopy(s.get("available_buildings", {}))
        store.manager_inventory = _cp.deepcopy(s.get("manager_inventory", []))
        store.owned_buildings = _cp.deepcopy(s.get("owned_buildings", []))
        store.custom_names = _cp.deepcopy(s.get("custom_names", {}))
        store.unlocked_shops = _cp.deepcopy(s.get("unlocked_shops", {}))
        store.player_name = s.get("player_name", "")
        store.player_title = s.get("player_title", "")
        store.current_day = s.get("current_day", 1)
        store.current_month = s.get("current_month", 1)
        store.current_year = s.get("current_year", 1)
        
        # Sync calendar with persistent variables
        persistent.current_day = store.current_day
        persistent.current_month = store.current_month
        persistent.current_year = store.current_year

        # Restore per-worker tracking structures and attributes
        try:
            name_to_worker = {w.get("name"): w for w in store.workers}
            skill_uses_map = s.get("_skill_uses", {}) or {}
            success_map = s.get("_success_counts", {}) or {}
            inventories_map = s.get("_worker_inventories", {}) or {}
            traits_map = s.get("_worker_traits", {}) or {}
            trait_durations_map = s.get("_worker_trait_durations", {}) or {}
            temporary_traits_map = s.get("_worker_temporary_traits", {}) or {}
            skills_map = s.get("_worker_skills", {}) or {}
            secondary_map = s.get("_worker_secondary", {}) or {}
            for wname, uses in skill_uses_map.items():
                if wname in name_to_worker and isinstance(uses, dict):
                    name_to_worker[wname]["skill_uses"] = uses
            for wname, sc in success_map.items():
                if wname in name_to_worker:
                    name_to_worker[wname]["success_count"] = sc
            for wname, inv in inventories_map.items():
                if wname in name_to_worker:
                    name_to_worker[wname]["inventory"] = inv
            for wname, tr in traits_map.items():
                if wname in name_to_worker:
                    name_to_worker[wname]["traits"] = tr
            for wname, td in trait_durations_map.items():
                if wname in name_to_worker and isinstance(td, dict):
                    name_to_worker[wname]["trait_durations"] = td
            for wname, tt in temporary_traits_map.items():
                if wname in name_to_worker and isinstance(tt, dict):
                    name_to_worker[wname]["temporary_traits"] = tt
            for wname, sk in skills_map.items():
                if wname in name_to_worker and isinstance(sk, dict):
                    name_to_worker[wname]["skills"] = sk
                    name_to_worker[wname].setdefault("original_skills", sk.copy())
            for wname, sec in secondary_map.items():
                if wname in name_to_worker and isinstance(sec, dict):
                    for k, v in sec.items():
                        name_to_worker[wname][k] = v
        except Exception as e:
            renpy.log("SNAPSHOT: restore tracking error: " + str(e))

        # Re-link assigned_servants in each building to the worker objects in store.workers
        try:
            name_to_worker = {w.get("name"): w for w in store.workers}
            for bname, b in store.available_buildings.items():
                if not isinstance(b, dict):
                    continue
                assigned = b.get("assigned_servants", []) or []
                relinked = []
                for sw in assigned:
                    wname = sw.get("name") if isinstance(sw, dict) else None
                    relinked.append(name_to_worker.get(wname, sw))
                b["assigned_servants"] = relinked
                # Ensure servant_jobs exists
                if "servant_jobs" not in b or not isinstance(b["servant_jobs"], dict):
                    b["servant_jobs"] = {}
                # Restore building-level state if present
                try:
                    inv_map = s.get("_building_inventories", {}) or {}
                    bonus_map = s.get("_building_skill_bonus", {}) or {}
                    if bname in inv_map:
                        b["inventory"] = inv_map[bname]
                    if bname in bonus_map:
                        b["skill_bonus"] = bonus_map[bname]
                    base_map = s.get("_building_base_levels", {}) or {}
                    if bname in base_map:
                        b["base_level"] = base_map[bname]
                except Exception as e:
                    renpy.log("SNAPSHOT: building restore error: " + str(e))
        except Exception as e:
            renpy.log("SNAPSHOT: relink error: " + str(e))

        # Restore event/journal state
        try:
            store.event_flags = _cp.deepcopy(s.get("_event_flags", {})) or {}
            store.event_occurrences = s.get("_event_occurrences", {}) or {}
            store.event_last_occurred = s.get("_event_last_occurred", {}) or {}
            j = s.get("_journal_state", {}) or {}
            for key, val in j.items():
                setattr(store, key, val)
        except Exception as e:
            renpy.log("SNAPSHOT: journal/flags restore error: " + str(e))

    def snapshot_pre_save(slot_number: int):
        try:
            # Build snapshot safely without generators and with only JSON-serializable structures
            if not isinstance(getattr(persistent, "_slot_snapshots", None), dict):
                persistent._slot_snapshots = {}
            snap = _build_snapshot()
            persistent._slot_snapshots[int(slot_number)] = snap
            persistent._last_snapshot = snap
            renpy.log(f"SNAPSHOT: saved for slot {slot_number}")
            renpy.save_persistent()
        except Exception as e:
            renpy.log("SNAPSHOT: error pre_save: " + str(e))

    def snapshot_mark_load(slot_number: int):
        try:
            persistent._slot_to_apply = int(slot_number)
            persistent.loaded_via_save = True
            renpy.log(f"SNAPSHOT: marked slot {slot_number} for apply after load")
            renpy.save_persistent()
        except Exception as e:
            renpy.log("SNAPSHOT: error mark_load: " + str(e))

    # New: snapshot keyed by slot name (page-aware)
    def snapshot_pre_save_name(slot_name: str):
        try:
            if not isinstance(getattr(persistent, "_slot_snapshots", None), dict):
                persistent._slot_snapshots = {}
            snap = _build_snapshot()
            persistent._slot_snapshots[str(slot_name)] = snap
            persistent._last_snapshot = snap
            renpy.log(f"SNAPSHOT: saved for slot '{slot_name}'")
            renpy.save_persistent()
        except Exception as e:
            renpy.log("SNAPSHOT: error pre_save_name: " + str(e))

    def snapshot_mark_load_name(slot_name: str):
        try:
            persistent._slot_to_apply = str(slot_name)
            persistent.loaded_via_save = True
            renpy.log(f"SNAPSHOT: marked slot '{slot_name}' for apply after load")
            renpy.save_persistent()
        except Exception as e:
            renpy.log("SNAPSHOT: error mark_load_name: " + str(e))

    def _apply_pending_snapshot_and_show_tavern():
        try:
            slot = getattr(persistent, "_slot_to_apply", None)
            renpy.log(f"SNAPSHOT: _apply_pending start, slot={slot}, keys={list((getattr(persistent, '_slot_snapshots', {}) or {}).keys())}")
            snap = None
            d = getattr(persistent, "_slot_snapshots", {}) or {}
            if slot is not None:
                key_try = slot
                if key_try in d:
                    snap = d.get(key_try)
                elif isinstance(slot, int) and str(slot) in d:
                    snap = d.get(str(slot))
                elif isinstance(slot, str) and slot.isdigit() and int(slot) in d:
                    snap = d.get(int(slot))
            if snap is None:
                snap = getattr(persistent, "_last_snapshot", None)
                if snap is None:
                    renpy.log("SNAPSHOT: no snapshot found; proceeding to tavern without apply")
            else:
                try:
                    _apply_snapshot(snap)
                    renpy.log("SNAPSHOT: applied via post-load timer")
                except Exception as e_apply:
                    renpy.log("SNAPSHOT: error during _apply_snapshot: " + str(e_apply))
            # Ensure we don't re-run init path in this session
            store.is_new_game = False
            # NOTE: Do NOT clear persistent flags here; clear them once screen is shown
            
            # Restore the correct screen based on saved context
            screen_context = "tavern"  # default fallback
            if snap and "screen_context" in snap:
                screen_context = snap["screen_context"]
            
            renpy.log(f"SNAPSHOT: restoring screen context = {screen_context}")
            
            try:
                if screen_context == "daily_report":
                    renpy.show_screen("daily_report")
                    renpy.log("SNAPSHOT: daily_report screen shown successfully")
                elif screen_context == "workers":
                    renpy.show_screen("workers")
                    renpy.log("SNAPSHOT: workers screen shown successfully")
                elif screen_context == "buildings":
                    renpy.show_screen("Building_select_global")
                    renpy.log("SNAPSHOT: buildings screen shown successfully")
                elif screen_context == "map":
                    renpy.show_screen("map_screen")
                    renpy.log("SNAPSHOT: map screen shown successfully")
                elif screen_context == "journal":
                    renpy.show_screen("journal_panel")
                    renpy.log("SNAPSHOT: journal screen shown successfully")
                elif screen_context == "inventory":
                    renpy.show_screen("manager_inventory")
                    renpy.log("SNAPSHOT: inventory screen shown successfully")
                else:
                    # Default to tavern
                    renpy.show_screen("tavern")
                    renpy.log("SNAPSHOT: tavern screen shown successfully (default)")
                
                # Clear persistent flags after successful screen restoration
                persistent._slot_to_apply = None
                persistent.loaded_via_save = False
                persistent._context_restored = True
                renpy.save_persistent()
                renpy.log("SNAPSHOT: persistent flags cleared after successful screen restore")
            except Exception as e_show:
                renpy.log(f"SNAPSHOT: show_screen error for {screen_context}: " + str(e_show))
                try:
                    # Fallback to tavern if specific screen fails
                    renpy.show_screen("tavern")
                    renpy.log("SNAPSHOT: fallback to tavern screen successful")
                except Exception as e_fallback:
                    renpy.log("SNAPSHOT: fallback tavern error: " + str(e_fallback))
                    try:
                        renpy.restart_interaction()
                    except Exception as e_restart:
                        renpy.log("SNAPSHOT: restart_interaction error: " + str(e_restart))
        except Exception as e:
            renpy.log("SNAPSHOT: post-load apply error: " + str(e))

    # Fallback: ensure application via after-load callback in case label after_load is bypassed
    def _after_load_callback():
        try:
            renpy.log("AFTER_LOAD_CB: fired - but skipping since after_load should handle it")
            # Skip callback execution since after_load should handle it directly
            # _apply_pending_snapshot_and_show_tavern()
        except Exception as e:
            renpy.log("AFTER_LOAD_CB error: " + str(e))

    # Register callback at low init priority
    try:
        config.after_load_callbacks.append(_after_load_callback)
    except Exception as e:
        renpy.log("Register after_load callback error: " + str(e))

label after_load:
    python:
        renpy.log("AFTER_LOAD: entered")
        try:
            _apply_pending_snapshot_and_show_tavern()
        except Exception as e:
            renpy.log("AFTER_LOAD direct apply error: " + str(e))
    
    # Show the ESC key handler screen after loading
    show screen esc_key_handler
    return

# Screen removed - no longer needed since we apply directly in after_load


