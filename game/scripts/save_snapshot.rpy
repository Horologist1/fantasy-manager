init python:
    import copy as _cp
    import hashlib
    import json

    SNAPSHOT_VERSION = 2

    def _compute_snapshot_hash(snap: dict) -> str:
        """Compute a stable hash for snapshot integrity checks."""
        try:
            # Exclude hash field itself
            snap_copy = _cp.deepcopy(snap)
            if "_snapshot_hash" in snap_copy:
                del snap_copy["_snapshot_hash"]
            payload = json.dumps(snap_copy, sort_keys=True, separators=(",", ":"))
            return hashlib.sha256(payload.encode("utf-8")).hexdigest()
        except Exception as e:
            renpy.log(f"SNAPSHOT: hash computation failed: {e}")
            return ""

    # Ensure snapshot store is a dict (older persistents may hold None or other)
    if not isinstance(getattr(persistent, "_slot_snapshots", None), dict):
        persistent._slot_snapshots = {}

    def _build_snapshot() -> dict:
        # Detect current screen context
        current_screen_context = "tavern"  # default
        try:
            # Keep building data consistent before snapshotting
            validate_and_sync_buildings()
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
        
        # Add timestamp for validation
        import time
        snapshot_timestamp = time.time()
        
        return {
            "_snapshot_version": SNAPSHOT_VERSION,
            # Timestamp for validation (prevents loading old snapshots)
            "_snapshot_timestamp": snapshot_timestamp,
            "_snapshot_day": getattr(store, "current_day", 1),
            "_snapshot_month": getattr(store, "current_month", 1),
            "_snapshot_year": getattr(store, "current_year", 1),
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
            "_worker_original_skills": _cp.deepcopy({w.get("name"): w.get("original_skills", w.get("skills", {}).copy()) for w in getattr(store, "workers", [])}),
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
                    "energy": w.get("energy", 0),
                    # NOTE: max_health and max_energy are NOT saved - they are recalculated
                    # from equipped items to avoid duplicate bonuses when items are re-applied
                    "daily_cost": w.get("daily_cost", w.get("comfort_level", 1) * 20),
                    "flags": _cp.deepcopy(w.get("flags", {})),
                    "assigned_building": w.get("assigned_building", "Unassigned"),
                    "assigned_job": w.get("assigned_job", None)
                }
                for w in getattr(store, "workers", [])
            }),
            # Building-specific inventories or state if present
            "_building_inventories": _cp.deepcopy({bname: b.get("inventory", []) for bname, b in getattr(store, "available_buildings", {}).items()}),
            "_building_skill_bonus": _cp.deepcopy({bname: b.get("skill_bonus", 0) for bname, b in getattr(store, "available_buildings", {}).items()}),
            "_building_base_levels": _cp.deepcopy({bname: b.get("base_level", 1) for bname, b in getattr(store, "available_buildings", {}).items()}),
            "_building_reputation": _cp.deepcopy({bname: b.get("reputation", 0) for bname, b in getattr(store, "available_buildings", {}).items()}),
            "_building_skill": _cp.deepcopy({bname: b.get("skill", 10) for bname, b in getattr(store, "available_buildings", {}).items()}),
            "_building_event_limit": _cp.deepcopy({bname: b.get("event_limit", 0) for bname, b in getattr(store, "available_buildings", {}).items()}),
            # Event/journal flags and progress
            "_event_flags": _cp.deepcopy(getattr(store, "event_flags", {})),
            "_event_occurrences": _cp.deepcopy(getattr(store, "event_occurrences", {})),
            "_event_last_occurred": _cp.deepcopy(getattr(store, "event_last_occurred", {})),
            # Daily interaction tracking
            "_worker_interactions_today": _cp.deepcopy(getattr(store, "worker_interactions_today", {})),
            "_last_take_a_walk_day": getattr(store, "last_take_a_walk_day", None),
            "_journal_state": {
                "tutorial_active": getattr(store, "tutorial_active", False),
                "current_objective": getattr(store, "current_objective", 0),
                "objective_1_complete": getattr(store, "objective_1_complete", False),
                "objective_2_complete": getattr(store, "objective_2_complete", False),
                "objective_3_complete": getattr(store, "objective_3_complete", False),
                "objective_4_complete": getattr(store, "objective_4_complete", False),
                "objective_5_complete": getattr(store, "objective_5_complete", False),
                "objective_6_complete": getattr(store, "objective_6_complete", False),
                "objective_7_complete": getattr(store, "objective_7_complete", False),
                "objective_8_complete": getattr(store, "objective_8_complete", False),
                "objective_9_complete": getattr(store, "objective_9_complete", False),
                "objective_10_complete": getattr(store, "objective_10_complete", False),
                "objective_11_complete": getattr(store, "objective_11_complete", False),
                "objective_12_complete": getattr(store, "objective_12_complete", False),
                "objective_13_complete": getattr(store, "objective_13_complete", False),
                "objective_14_complete": getattr(store, "objective_14_complete", False),
                "objective_15_complete": getattr(store, "objective_15_complete", False),
                "objective_16_complete": getattr(store, "objective_16_complete", False),
                "objective_4_dialogue_shown": getattr(store, "objective_4_dialogue_shown", False)
            },
        }

    def _apply_snapshot(s: dict) -> None:
        if not s:
            return
        store.money = int(s.get("money", 5000))
        # Restore workers first
        store.workers = _cp.deepcopy(s.get("workers", []))
        # Deduplicate workers by name to avoid save-induced duplicates
        try:
            seen_names = set()
            deduped_workers = []
            for w in store.workers:
                wname = w.get("name")
                if wname in seen_names:
                    renpy.log(f"SNAPSHOT: duplicate worker '{wname}' in workers list, skipping")
                    continue
                deduped_workers.append(w)
                if wname:
                    seen_names.add(wname)
            store.workers = deduped_workers
        except Exception as e:
            renpy.log("SNAPSHOT: error deduping workers list: " + str(e))
        # Restore buildings next
        store.available_buildings = _cp.deepcopy(s.get("available_buildings", {}))
        store.manager_inventory = _cp.deepcopy(s.get("manager_inventory", []))
        store.owned_buildings = _cp.deepcopy(s.get("owned_buildings", []))
        store.custom_names = _cp.deepcopy(s.get("custom_names", {}))
        store.unlocked_shops = _cp.deepcopy(s.get("unlocked_shops", {}))
        
        # IMPORTANTE: Validar y sincronizar edificios ANTES de procesar asignaciones
        # Esto asegura que todos los edificios referenciados por workers existan
        try:
            validate_and_sync_buildings()
            renpy.log("SNAPSHOT: validate_and_sync_buildings completed (early)")
        except Exception as e:
            renpy.log("SNAPSHOT: validate_and_sync_buildings error (early): " + str(e))
        store.player_name = s.get("player_name", "")
        store.player_title = s.get("player_title", "")
        
        # IMPORTANT: JSON (save_state.rpy) always restores the calendar if it exists in the save file
        # The snapshot should ONLY restore the calendar if JSON didn't restore it
        # Check if calendar was already restored (JSON would have set it)
        current_day_exists = hasattr(store, "current_day") and store.current_day is not None
        current_month_exists = hasattr(store, "current_month") and store.current_month is not None
        current_year_exists = hasattr(store, "current_year") and store.current_year is not None
        
        # Only restore calendar from snapshot if it wasn't already restored from JSON
        # This prevents snapshot from overwriting the correct date from JSON
        if not (current_day_exists and current_month_exists and current_year_exists):
            store.current_day = s.get("current_day", 1)
            store.current_month = s.get("current_month", 1)
            store.current_year = s.get("current_year", 1)
            renpy.log(f"SNAPSHOT: Restored calendar from snapshot (JSON didn't restore it): {store.current_day}/{store.current_month}/{store.current_year}")
        else:
            # Calendar was already restored from JSON, keep it (don't overwrite with potentially older snapshot)
            renpy.log(f"SNAPSHOT: Keeping calendar from JSON (not overwriting): {store.current_day}/{store.current_month}/{store.current_year}")
        
        # Do not sync calendar to persistent to avoid cross-save bleed

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
            original_skills_map = s.get("_worker_original_skills", {}) or {}
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
            for wname, orig_sk in original_skills_map.items():
                if wname in name_to_worker and isinstance(orig_sk, dict):
                    name_to_worker[wname]["original_skills"] = orig_sk
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
                seen_names = set()
                for sw in assigned:
                    wname = sw.get("name") if isinstance(sw, dict) else None
                    if wname in seen_names:
                        renpy.log(f"SNAPSHOT: duplicate assigned_servant '{wname}' in {bname}, skipping")
                        continue
                    relinked.append(name_to_worker.get(wname, sw))
                    if wname:
                        seen_names.add(wname)
                b["assigned_servants"] = relinked
                # Ensure servant_jobs exists
                if "servant_jobs" not in b or not isinstance(b["servant_jobs"], dict):
                    b["servant_jobs"] = {}
                # Restore building-level state if present
                try:
                    inv_map = s.get("_building_inventories", {}) or {}
                    bonus_map = s.get("_building_skill_bonus", {}) or {}
                    base_map = s.get("_building_base_levels", {}) or {}
                    rep_map = s.get("_building_reputation", {}) or {}
                    skill_map = s.get("_building_skill", {}) or {}
                    event_limit_map = s.get("_building_event_limit", {}) or {}
                    
                    if bname in inv_map:
                        b["inventory"] = inv_map[bname]
                    if bname in bonus_map:
                        b["skill_bonus"] = bonus_map[bname]
                    if bname in base_map:
                        b["base_level"] = base_map[bname]
                    if bname in rep_map:
                        b["reputation"] = rep_map[bname]
                    if bname in skill_map:
                        b["skill"] = skill_map[bname]
                    if bname in event_limit_map:
                        b["event_limit"] = event_limit_map[bname]
                    # Note: max_workers is calculated dynamically via get_max_daily_workers() based on base_level
                    # Note: costs is reset to 0 and recalculated daily in event_daily_exec.rpy
                    
                    # Ensure base_level exists and is valid (persist building levels)
                    if "base_level" not in b or not isinstance(b.get("base_level"), int) or b["base_level"] < 1:
                        b["base_level"] = b.get("base_level", 1)
                        renpy.log(f"SNAPSHOT: initialized/restored base_level for {bname} to {b['base_level']}")
                except Exception as e:
                    renpy.log("SNAPSHOT: building restore error: " + str(e))
        except Exception as e:
            renpy.log("SNAPSHOT: relink error: " + str(e))
        
        # Note: No need to recalculate max_daily_workers here anymore
        # The get_max_daily_workers() function calculates it dynamically based on base_level

        # Restore event/journal state
        try:
            # Only restore if JSON didn't already restore them (JSON takes priority)
            # JSON is the primary save source and executes before snapshot
            if not hasattr(store, "event_flags") or not store.event_flags:
                store.event_flags = _cp.deepcopy(s.get("_event_flags", {})) or {}
            else:
                # Merge flags from snapshot if JSON didn't have them
                snap_flags = s.get("_event_flags", {}) or {}
                for flag_name, flag_value in snap_flags.items():
                    if flag_name not in store.event_flags:
                        store.event_flags[flag_name] = flag_value
            
            if not hasattr(store, "event_occurrences") or not store.event_occurrences:
                store.event_occurrences = s.get("_event_occurrences", {}) or {}
            else:
                # Merge occurrences from snapshot if JSON didn't have them (prefer higher values)
                snap_occurrences = s.get("_event_occurrences", {}) or {}
                for event_id, snap_count in snap_occurrences.items():
                    current_count = store.event_occurrences.get(event_id, 0)
                    # Use the higher count (more recent data)
                    store.event_occurrences[event_id] = max(current_count, snap_count)
            
            if not hasattr(store, "event_last_occurred") or not store.event_last_occurred:
                store.event_last_occurred = s.get("_event_last_occurred", {}) or {}
            else:
                # Merge last_occurred from snapshot if JSON didn't have them (prefer more recent dates)
                snap_last_occurred = s.get("_event_last_occurred", {}) or {}
                for event_id, snap_date in snap_last_occurred.items():
                    current_date = store.event_last_occurred.get(event_id, 0)
                    # Use the more recent date (higher value = more recent)
                    store.event_last_occurred[event_id] = max(current_date, snap_date)
            # Daily interaction tracking
            if "_worker_interactions_today" in s:
                store.worker_interactions_today = _cp.deepcopy(s.get("_worker_interactions_today", {})) or {}
            if "_last_take_a_walk_day" in s:
                store.last_take_a_walk_day = s.get("_last_take_a_walk_day", None)
            j = s.get("_journal_state", {}) or {}
            for key, val in j.items():
                setattr(store, key, val)
        except Exception as e:
            renpy.log("SNAPSHOT: journal/flags restore error: " + str(e))

        # Validate and sync buildings BEFORE normalization
        # This ensures all buildings referenced by workers or owned_buildings exist
        try:
            validate_and_sync_buildings()
            renpy.log("SNAPSHOT: validate_and_sync_buildings completed")
        except Exception as e:
            renpy.log("SNAPSHOT: validate_and_sync_buildings error: " + str(e))

        # Final normalization pass to ensure no duplicates
        try:
            normalize_building_assignments()
            renpy.log("SNAPSHOT: normalize_building_assignments completed")
        except Exception as e:
            renpy.log("SNAPSHOT: normalize error: " + str(e))

    def snapshot_pre_save(slot_number: int):
        try:
            # Build snapshot safely without generators and with only JSON-serializable structures
            if not isinstance(getattr(persistent, "_slot_snapshots", None), dict):
                persistent._slot_snapshots = {}
            store.last_save_slot = str(int(slot_number))
            snap = _build_snapshot()
            snap["_snapshot_slot"] = str(int(slot_number))
            snap["_snapshot_hash"] = _compute_snapshot_hash(snap)
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
            store.last_save_slot = str(slot_name)
            snap = _build_snapshot()
            snap["_snapshot_slot"] = str(slot_name)
            snap["_snapshot_hash"] = _compute_snapshot_hash(snap)
            snap_day = snap.get("_snapshot_day", 0)
            snap_month = snap.get("_snapshot_month", 0)
            snap_year = snap.get("_snapshot_year", 0)
            persistent._slot_snapshots[str(slot_name)] = snap
            persistent._last_snapshot = snap
            renpy.log(f"SNAPSHOT: saved for slot '{slot_name}' with date {snap_day}/{snap_month}/{snap_year} (timestamp: {snap.get('_snapshot_timestamp', 'N/A')})")
            renpy.save_persistent()
        except Exception as e:
            renpy.log("SNAPSHOT: error pre_save_name: " + str(e))
            import traceback
            renpy.log("SNAPSHOT: traceback: " + traceback.format_exc())

    def snapshot_mark_load_name(slot_name: str):
        try:
            persistent._slot_to_apply = str(slot_name)
            persistent.loaded_via_save = True
            renpy.log(f"SNAPSHOT: marked slot '{slot_name}' for apply after load")
            renpy.save_persistent()
        except Exception as e:
            renpy.log("SNAPSHOT: error mark_load_name: " + str(e))

    # Helper functions that capture current page at click time
    def snapshot_pre_save_slot(slot_num):
        """Save snapshot with page-aware slot name, evaluated at click time."""
        page = getattr(persistent, "_file_page", 1)
        # Handle special page values
        if page in ["auto", "quick"]:
            slot_name = f"{page}-{slot_num}"
        else:
            try:
                page = int(page)
            except (ValueError, TypeError):
                page = 1
            slot_name = f"{page}-{slot_num}"
        current_day = getattr(store, "current_day", 0)
        current_month = getattr(store, "current_month", 0)
        current_year = getattr(store, "current_year", 0)
        renpy.log(f"SNAPSHOT: pre_save_slot called with slot_num={slot_num}, page={page}, slot_name='{slot_name}', game_date={current_day}/{current_month}/{current_year}")
        snapshot_pre_save_name(slot_name)

    def snapshot_mark_load_slot(slot_num):
        """Mark load with page-aware slot name, evaluated at click time."""
        page = getattr(persistent, "_file_page", 1)
        # Handle special page values
        if page in ["auto", "quick"]:
            slot_name = f"{page}-{slot_num}"
        else:
            try:
                page = int(page)
            except (ValueError, TypeError):
                page = 1
            slot_name = f"{page}-{slot_num}"
        renpy.log(f"SNAPSHOT: mark_load_slot called with slot_num={slot_num}, page={page}, slot_name='{slot_name}'")
        snapshot_mark_load_name(slot_name)

    # Custom action class for page-aware FileAction
    class PageAwareFileAction(renpy.store.Action):
        """Action that handles both save and load with page-aware snapshots."""
        def __init__(self, slot_num):
            self.slot_num = slot_num
        
        def __call__(self):
            """
            IMPORTANT:
            - When user is in the Save screen, clicking a slot must create a snapshot for THAT save.
            - When user is in the Load screen, clicking a slot must ONLY mark load.
            
            The old logic tried to infer "save vs load" from whether the slot had data, which is wrong:
            in Save mode, occupied slots still mean "save overwrite", and in Load mode we must never
            write a pre-save snapshot (it can overwrite the slot snapshot with current session state).
            """
            try:
                in_save = bool(renpy.get_screen("save"))
                in_load = bool(renpy.get_screen("load"))

                if in_save:
                    renpy.log(f"SNAPSHOT: PageAwareFileAction slot {self.slot_num} in SAVE screen -> pre_save snapshot")
                    snapshot_pre_save_slot(self.slot_num)
                elif in_load:
                    renpy.log(f"SNAPSHOT: PageAwareFileAction slot {self.slot_num} in LOAD screen -> mark_load snapshot")
                    snapshot_mark_load_slot(self.slot_num)
                else:
                    # Fallback: default to pre_save (safer than marking load)
                    renpy.log(f"SNAPSHOT: PageAwareFileAction slot {self.slot_num} unknown context -> default pre_save")
                    snapshot_pre_save_slot(self.slot_num)
            except Exception as e:
                renpy.log(f"SNAPSHOT: PageAwareFileAction error: {str(e)} (defaulting to pre_save)")
                try:
                    snapshot_pre_save_slot(self.slot_num)
                except Exception as e2:
                    renpy.log(f"SNAPSHOT: PageAwareFileAction fallback pre_save error: {str(e2)}")
            
            # Execute the native FileAction (Ren'Py decides save vs load based on current menu).
            return renpy.store.FileAction(self.slot_num)()
        
        def get_sensitive(self):
            return renpy.store.FileAction(self.slot_num).get_sensitive()

    def _apply_pending_snapshot_and_show_tavern():
        try:
            slot = getattr(persistent, "_slot_to_apply", None)
            renpy.log(f"SNAPSHOT: _apply_pending start, slot={slot}, keys={list((getattr(persistent, '_slot_snapshots', {}) or {}).keys())}")
            
            # CRITICAL: Only proceed if this is actually a load operation
            # If slot is None and loaded_via_save is False, this shouldn't be executing
            if slot is None and not getattr(persistent, "loaded_via_save", False):
                renpy.log("SNAPSHOT: WARNING - _apply_pending called but no load detected! This might be a new game. Skipping.")
                return
            
            # CRITICAL: Reset ALL state variables at the start of each load to prevent cross-save contamination
            # This ensures clean state even when loading multiple times without closing the game
            try:
                # Clear persistent flags IMMEDIATELY (but save slot first for validation)
                saved_slot = slot  # Save for later use
                persistent._slot_to_apply = None
                persistent.loaded_via_save = False
                persistent._context_restored = False
                renpy.save_persistent()
                
                # Do NOT reset store flags here.
                # At this point, Ren'Py + JSON callbacks may have already restored state.
                # Resetting store.game_initialized would make us treat a valid load as "empty"
                # and incorrectly apply an older snapshot on top.
                renpy.log("SNAPSHOT: Cleared persistent load flags at start of load (store flags preserved)")
            except Exception as e_clear:
                renpy.log(f"SNAPSHOT: error resetting state flags: {str(e_clear)}")
            
            # Use saved_slot instead of slot (which is now None)
            slot = saved_slot
            
            snap = None
            d = getattr(persistent, "_slot_snapshots", {}) or {}
            
            # Only look for snapshot with exact slot key - don't fallback to _last_snapshot
            # Ren'Py already restored the variables, only apply snapshot if we find exact match
            if slot is not None:
                key_try = slot
                if key_try in d:
                    snap = d.get(key_try)
                    renpy.log(f"SNAPSHOT: found exact match for slot '{key_try}'")
                elif isinstance(slot, int) and str(slot) in d:
                    snap = d.get(str(slot))
                    renpy.log(f"SNAPSHOT: found match for slot '{slot}' as string")
                elif isinstance(slot, str) and slot.isdigit() and int(slot) in d:
                    snap = d.get(int(slot))
                    renpy.log(f"SNAPSHOT: found match for slot '{slot}' as int")
                else:
                    renpy.log(f"SNAPSHOT: no snapshot found for slot '{slot}', Ren'Py data preserved")
            
            # Validate snapshot version/slot/hash if present
            if snap is not None:
                snap_version = snap.get("_snapshot_version", None)
                expected_slot = str(slot) if slot is not None else None
                snap_slot = snap.get("_snapshot_slot", None)
                if snap_version != SNAPSHOT_VERSION:
                    renpy.log(f"SNAPSHOT: version mismatch (snap={snap_version}, expected={SNAPSHOT_VERSION}) - skipping apply")
                    snap = None
                elif expected_slot is not None and snap_slot is not None and str(snap_slot) != str(expected_slot):
                    renpy.log(f"SNAPSHOT: slot mismatch (snap={snap_slot}, expected={expected_slot}) - skipping apply")
                    snap = None
                else:
                    expected_hash = _compute_snapshot_hash(snap)
                    snap_hash = snap.get("_snapshot_hash", "")
                    if expected_hash and snap_hash and expected_hash != snap_hash:
                        renpy.log("SNAPSHOT: hash mismatch - skipping apply to prevent corrupted data")
                        snap = None
            
            # Check if Ren'Py/save_state already restored valid data.
            #
            # IMPORTANT:
            # Using "len(workers) > 0" as a proxy is WRONG (early-game saves can legitimately have 0 workers),
            # and it causes us to treat valid loads as "empty" and apply an older snapshot on top.
            #
            # The JSON load path sets store.game_initialized = True when it successfully applies state.
            has_valid_data = bool(getattr(store, "game_initialized", False))
            current_workers = getattr(store, "workers", None)
            renpy.log(f"SNAPSHOT: has_valid_data={has_valid_data} (game_initialized={getattr(store,'game_initialized',None)}), workers_len={len(current_workers) if isinstance(current_workers, list) else 'N/A'}")
            
            # Validate snapshot age if it exists
            snapshot_is_older = False
            if snap is not None and has_valid_data:
                # Compare snapshot date with current game date
                snap_day = snap.get("_snapshot_day", 0)
                snap_month = snap.get("_snapshot_month", 0)
                snap_year = snap.get("_snapshot_year", 0)
                current_day = getattr(store, "current_day", 0)
                current_month = getattr(store, "current_month", 0)
                current_year = getattr(store, "current_year", 0)
                
                # Calculate days difference (simple approximation: year*365 + month*30 + day)
                snap_days = snap_year * 365 + snap_month * 30 + snap_day
                current_days = current_year * 365 + current_month * 30 + current_day
                
                if snap_days < current_days - 1:  # Allow 1 day difference for safety
                    snapshot_is_older = True
                    renpy.log(f"SNAPSHOT: WARNING - Snapshot is older than current game state! Snapshot: Day {snap_day}/{snap_month}/{snap_year}, Current: Day {current_day}/{current_month}/{current_year}. NOT applying snapshot to prevent data loss.")
            
            if has_valid_data:
                if snapshot_is_older:
                    renpy.log(f"SNAPSHOT: Ren'Py restored {len(current_workers)} workers with newer data than snapshot. Keeping Ren'Py data, ignoring old snapshot.")
                else:
                    renpy.log(f"SNAPSHOT: Ren'Py already restored {len(current_workers)} workers, skipping snapshot apply")
                    # IMPORTANT: Even if Ren'Py restored data, we need to validate and sync buildings
                    # because the save file might be corrupted (missing buildings in available_buildings)
                    try:
                        validate_and_sync_buildings()
                        renpy.log("SNAPSHOT: validate_and_sync_buildings completed after Ren'Py restore")
                    except Exception as e:
                        renpy.log(f"SNAPSHOT: validate_and_sync_buildings error after Ren'Py restore: {str(e)}")
                    # Merge custom building names from snapshot if Ren'Py did not restore them
                    try:
                        snap_custom = (snap or {}).get("custom_names", {}) or {}
                        if snap_custom:
                            if not hasattr(store, "custom_names") or store.custom_names is None:
                                store.custom_names = {}
                            if not store.custom_names:
                                store.custom_names = _cp.deepcopy(snap_custom)
                                renpy.log("SNAPSHOT: restored custom_names from snapshot (store was empty)")
                            else:
                                for key, val in snap_custom.items():
                                    # If store has default name but snapshot has a custom name, prefer snapshot
                                    if key not in store.custom_names:
                                        store.custom_names[key] = val
                                    elif store.custom_names.get(key) == key and val != key:
                                        store.custom_names[key] = val
                                renpy.log("SNAPSHOT: merged custom_names from snapshot")
                    except Exception as e:
                        renpy.log(f"SNAPSHOT: custom_names merge error: {str(e)}")
            elif snap is not None:
                # Apply snapshot if Ren'Py didn't restore data
                snap_player = snap.get("player_name", "")
                current_player = getattr(store, "player_name", "")
                if snap_player == current_player or not current_player:
                    try:
                        _apply_snapshot(snap)
                        renpy.log("SNAPSHOT: applied as fallback (Ren'Py data was empty)")
                    except Exception as e_apply:
                        renpy.log("SNAPSHOT: error during _apply_snapshot: " + str(e_apply))
                else:
                    renpy.log(f"SNAPSHOT: player mismatch (snap='{snap_player}', store='{current_player}'), skipping apply")
            else:
                renpy.log("SNAPSHOT: no snapshot available and Ren'Py data empty - this may indicate a problem")
            
            # NOTE: Objective sync for old saves is now handled generically in save_state.rpy
            # (syncs ALL previous objectives based on current_objective)
            
            # Mark that this is a loaded game (not a new game)
            # This was already set at the start, but ensure it's correct
            store.is_new_game = False
            # game_initialized will be set by save_state.rpy after successful load
            
            # Restore the correct screen based on saved context.
            # IMPORTANT: Do NOT try to manage screens/scenes from here.
            # If something goes wrong during screen restoration, Ren'Py can end up on a black screen.
            # Instead, always jump into the normal game flow label, which will show the proper screen.
            screen_context = "tavern"  # default fallback
            if snap and "screen_context" in snap:
                screen_context = snap["screen_context"]
            
            # Store desired context for later (optional) use by tavern_screen.
            store._post_load_screen_context = screen_context
            renpy.log(f"SNAPSHOT: post-load context='{screen_context}'. Will jump to tavern_screen from label after_load for safe UI restoration.")

            # Mark context restored so tavern() doesn't try to do old flag logic.
            try:
                persistent._context_restored = True
                renpy.save_persistent()
            except Exception as e_ctx:
                renpy.log("SNAPSHOT: could not set _context_restored: " + str(e_ctx))

            # IMPORTANT: Do not renpy.jump() from inside this python function.
            # We'll jump using Ren'Py script flow in label after_load to avoid control-flow exceptions being swallowed.
            return
        except Exception as e:
            # IMPORTANT: Don't swallow Ren'Py control-flow exceptions (jump/return), or you'll get a black/frozen screen.
            if e.__class__.__name__ in ("JumpException", "ReturnException", "EndInteraction", "RestartInteraction"):
                raise
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
    
    # NOTE: fix_objective_11_* functions removed - objective sync is now handled
    # generically in save_state.rpy for ALL objectives based on current_objective

label after_load:
    $ renpy.log("AFTER_LOAD: entered")
    python:
        # Apply snapshot merge only if our load-marker is present (page-aware slot load).
        # But ALWAYS jump to tavern_screen after any load to avoid resuming old call stacks
        # (which can result in black/frozen screens).
        slot_to_apply = getattr(persistent, "_slot_to_apply", None)
        loaded_via_save = getattr(persistent, "loaded_via_save", False)
        if slot_to_apply is not None or loaded_via_save:
            renpy.log(f"AFTER_LOAD: Load marker present (slot={slot_to_apply}, loaded_via_save={loaded_via_save}), running snapshot merge")
        try:
            _apply_pending_snapshot_and_show_tavern()
        except Exception as e:
                renpy.log("AFTER_LOAD snapshot merge error: " + str(e))
        else:
            renpy.log("AFTER_LOAD: No snapshot load marker present; skipping snapshot merge")
    
    # Show the ESC key handler screen after loading
    show screen esc_key_handler

    # ALWAYS restore via normal label flow to avoid frozen/black screens.
    jump tavern_screen

# Screen removed - no longer needed since we apply directly in after_load


