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
        # Sync persistent.unlocked_shops with restored store.unlocked_shops
        if store.unlocked_shops:
            persistent.unlocked_shops = _cp.deepcopy(store.unlocked_shops)
            renpy.log(f"SNAPSHOT: Synced persistent.unlocked_shops from snapshot: {persistent.unlocked_shops}")
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
        
        # Note: No need to recalculate max_daily_workers here anymore
        # The get_max_daily_workers() function calculates it dynamically based on base_level

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
        renpy.log(f"SNAPSHOT: pre_save_slot called with slot_num={slot_num}, page={page}, slot_name='{slot_name}'")
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
            try:
                # Check if slot has a save file by trying to get its time
                # FileTime returns "empty slot" if there's no save
                from renpy.store import FileTime
                slot_time = FileTime(self.slot_num, empty="empty slot")
                slot_has_data = (slot_time != "empty slot")
                
                if slot_has_data:
                    # Slot has data - this will likely LOAD (unless user overwrites)
                    # Mark for load - if user overwrites, the save will create new snapshot anyway
                    renpy.log(f"SNAPSHOT: PageAwareFileAction detected slot {self.slot_num} has data - preparing for LOAD")
                    snapshot_mark_load_slot(self.slot_num)
                    # Also prepare save snapshot in case user overwrites (confirms overwrite dialog)
                    snapshot_pre_save_slot(self.slot_num)
                else:
                    # Slot is empty - this will SAVE
                    renpy.log(f"SNAPSHOT: PageAwareFileAction detected slot {self.slot_num} is empty - preparing for SAVE")
                    snapshot_pre_save_slot(self.slot_num)
                
            except Exception as e:
                renpy.log(f"SNAPSHOT: PageAwareFileAction error: {str(e)}, defaulting to save")
                # On error, default to save (safer)
                snapshot_pre_save_slot(self.slot_num)
            
            # Then execute the native FileAction (which will save or load accordingly)
            return renpy.store.FileAction(self.slot_num)()
        
        def get_sensitive(self):
            return renpy.store.FileAction(self.slot_num).get_sensitive()

    def _apply_pending_snapshot_and_show_tavern():
        try:
            slot = getattr(persistent, "_slot_to_apply", None)
            renpy.log(f"SNAPSHOT: _apply_pending start, slot={slot}, keys={list((getattr(persistent, '_slot_snapshots', {}) or {}).keys())}")
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
            
            # Check if Ren'Py/save_state already restored valid data
            # If workers list is populated, data was already restored - don't overwrite
            current_workers = getattr(store, "workers", None)
            has_valid_data = current_workers and len(current_workers) > 0
            
            if has_valid_data:
                renpy.log(f"SNAPSHOT: Ren'Py already restored {len(current_workers)} workers, skipping snapshot apply")
            elif snap is not None:
                # Only apply snapshot if Ren'Py didn't restore data
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
            
            # Auto-fix objective 11 if player has 20+ workers but objective not marked
            try:
                workers_count = len(getattr(store, "workers", []))
                objective_11_complete = getattr(store, "objective_11_complete", False)
                if workers_count >= 20 and not objective_11_complete:
                    store.objective_11_complete = True
                    renpy.log(f"AUTO-FIX: Marked objective_11_complete=True (has {workers_count} workers)")
                    # Also update the snapshot for this slot if it exists
                    if slot is not None and snap is not None:
                        journal_state = snap.get("_journal_state", {})
                        if isinstance(journal_state, dict):
                            journal_state["objective_11_complete"] = True
                            snap["_journal_state"] = journal_state
                            # Update the snapshot in persistent
                            if slot in d:
                                persistent._slot_snapshots[slot] = snap
                                renpy.save_persistent()
                                renpy.log(f"AUTO-FIX: Updated snapshot '{slot}' with objective_11_complete=True")
            except Exception as e_fix:
                renpy.log(f"AUTO-FIX: Error auto-fixing objective 11: {str(e_fix)}")
            # Ensure we don't re-run init path in this session
            store.is_new_game = False
            # NOTE: Do NOT clear persistent flags here; clear them once screen is shown
            
            # Restore the correct screen based on saved context
            screen_context = "tavern"  # default fallback
            if snap and "screen_context" in snap:
                screen_context = snap["screen_context"]
            
            renpy.log(f"SNAPSHOT: restoring screen context = {screen_context}")

            # Clear existing UI/state before showing the restored screen to avoid stale overlays
            try:
                for _screen in [
                    "daily_report",
                    "workers",
                    "Building_select_global",
                    "map_screen",
                    "journal_panel",
                    "manager_inventory",
                    "tavern",
                    "Building_select",
                    "job_selection",
                    "building_selection",
                    "worker_details",
                    "more_details_screen",
                    "report_details",
                ]:
                    if renpy.get_screen(_screen):
                        renpy.hide_screen(_screen)
                renpy.scene()
            except Exception as e_reset:
                renpy.log("SNAPSHOT: UI reset error: " + str(e_reset))
            
            try:
                # Clear persistent flags before transferring control to a screen/label
                persistent._slot_to_apply = None
                persistent.loaded_via_save = False
                persistent._context_restored = True
                renpy.save_persistent()
                renpy.log("SNAPSHOT: persistent flags cleared before screen restoration")

                if screen_context == "daily_report":
                    renpy.call_screen("daily_report")
                    renpy.log("SNAPSHOT: daily_report screen called successfully")
                elif screen_context == "workers":
                    renpy.call_screen("workers")
                    renpy.log("SNAPSHOT: workers screen called successfully")
                elif screen_context == "buildings":
                    renpy.call_screen("Building_select_global")
                    renpy.log("SNAPSHOT: buildings screen called successfully")
                elif screen_context == "map":
                    renpy.call_screen("map_screen")
                    renpy.log("SNAPSHOT: map screen called successfully")
                elif screen_context == "journal":
                    renpy.call_screen("journal_panel")
                    renpy.log("SNAPSHOT: journal screen called successfully")
                elif screen_context == "inventory":
                    renpy.call_screen("manager_inventory")
                    renpy.log("SNAPSHOT: inventory screen called successfully")
                else:
                    # Default to tavern flow label (handles setup and calls screen)
                    renpy.jump("tavern_screen")
            except Exception as e_show:
                renpy.log(f"SNAPSHOT: show_screen error for {screen_context}: " + str(e_show))
                try:
                    # Fallback to tavern flow if specific screen fails
                    renpy.jump("tavern_screen")
                except Exception as e_fallback:
                    renpy.log("SNAPSHOT: fallback tavern error: " + str(e_fallback))
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
    
    def fix_objective_11_in_all_snapshots():
        """Fix objective_11_complete in all saved snapshots - call this once to update existing saves"""
        try:
            if not isinstance(getattr(persistent, "_slot_snapshots", None), dict):
                return
            
            updated_count = 0
            for slot_key, snap in persistent._slot_snapshots.items():
                if not isinstance(snap, dict):
                    continue
                journal_state = snap.get("_journal_state", {})
                if isinstance(journal_state, dict):
                    # Check if objective 11 can be completed (has 20 workers)
                    workers_count = len(getattr(store, "workers", []))
                    if workers_count >= 20 and not journal_state.get("objective_11_complete", False):
                        journal_state["objective_11_complete"] = True
                        snap["_journal_state"] = journal_state
                        updated_count += 1
                        renpy.log(f"FIXED: Marked objective_11_complete=True in snapshot '{slot_key}' (has {workers_count} workers)")
            
            if updated_count > 0:
                renpy.save_persistent()
                renpy.log(f"FIXED: Updated {updated_count} snapshot(s) with objective_11_complete=True")
            else:
                renpy.log("FIXED: No snapshots needed updating")
        except Exception as e:
            renpy.log(f"FIXED: Error fixing objective 11 in snapshots: {str(e)}")
    
    def fix_objective_11_current():
        """Fix objective_11_complete in current game state and update all snapshots"""
        try:
            # Check if objective 11 can be completed
            workers_count = len(getattr(store, "workers", []))
            if workers_count >= 20:
                store.objective_11_complete = True
                renpy.log(f"FIXED: Marked objective_11_complete=True in current game (has {workers_count} workers)")
                
                # Also update all snapshots
                fix_objective_11_in_all_snapshots()
                
                return True
            else:
                renpy.log(f"FIXED: Cannot mark objective 11 - only have {workers_count} workers (need 20)")
                return False
        except Exception as e:
            renpy.log(f"FIXED: Error fixing objective 11: {str(e)}")
            return False

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


