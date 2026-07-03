init -2 python:
    DEBUG_SNAPSHOT = False

    def _snap_log(message):
        if DEBUG_SNAPSHOT:
            renpy.log(message)

    def _snap_err(message):
        renpy.log(message)
    import copy as _cp
    import json
    import os
    import tempfile
    import shutil
    import uuid

    def _ensure_slot_guid(slot_name):
        """Ensure a stable GUID exists for a slot."""
        if not hasattr(persistent, "_slot_guids") or persistent._slot_guids is None:
            persistent._slot_guids = {}
        if slot_name not in persistent._slot_guids:
            persistent._slot_guids[slot_name] = str(uuid.uuid4())
        return persistent._slot_guids[slot_name]

    def _get_slot_guid(slot_name):
        """Get GUID for a slot if it exists."""
        if not hasattr(persistent, "_slot_guids") or persistent._slot_guids is None:
            return None
        return persistent._slot_guids.get(slot_name)
    
    def _get_current_slot_name(slot_num):
        """Compute the current Ren'Py slot name for a slot number."""
        try:
            page = getattr(persistent, "_file_page", "1")
            folder = getattr(persistent, "_file_folder", 0)
            pages_per_folder = getattr(config, "file_pages_per_folder", 100)
            
            # Try to expand numeric pages with folder offset (matches Ren'Py __slotname)
            try:
                page_int = int(page)
                page_int = page_int + int(folder) * int(pages_per_folder)
                page = str(page_int)
            except Exception:
                page = str(page)
            
            # Handle linear saves mode if configured
            if getattr(config, "linear_saves_page_size", None) is not None:
                try:
                    page_int = int(page)
                    name_int = int(slot_num)
                    return str((page_int - 1) * config.linear_saves_page_size + name_int)
                except Exception:
                    pass
            
            name = str(slot_num)
            if getattr(config, "file_slotname_callback", None) is not None:
                return config.file_slotname_callback(page, name)
            return page + "-" + name
        except Exception as e:
            renpy.log(f"SNAPSHOT: ERROR - could not compute slot name: {e}")
            return None

    def snapshot_pre_delete_slot(slot_num):
        """Delete snapshot files for a given slot number."""
        try:
            slot_name = _get_current_slot_name(slot_num)
            if not slot_name:
                return
            filepath = _get_snapshot_file_path(slot_name)
            backup_path = _get_backup_file_path(slot_name)
            tmp_path = filepath + ".tmp"
            
            for path in (filepath, backup_path, tmp_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        renpy.log(f"SNAPSHOT: WARNING - Could not delete {path}: {e}")
        except Exception as e:
            renpy.log(f"SNAPSHOT: ERROR - snapshot_pre_delete_slot failed: {e}")

    def _snapshot_matches_slot(snap, slot_name):
        """Validate that a snapshot belongs to the expected slot."""
        try:
            if not hasattr(snap, "get"):
                return False
            snap_slot = snap.get("snapshot_slot")
            snap_guid = snap.get("snapshot_guid")
            legacy_snapshot = False

            if snap_slot and snap_slot != slot_name:
                store._snapshot_validation_error = f"Slot mismatch (expected {slot_name}, got {snap_slot}). Do not save in this slot; load another and save to a new one."
                _snap_err(f"SNAPSHOT: ERROR - Slot mismatch. Expected {slot_name}, got {snap_slot}.")
                return False

            expected_guid = _get_slot_guid(slot_name)
            if expected_guid and snap_guid and snap_guid != expected_guid:
                store._snapshot_validation_error = f"GUID mismatch for slot {slot_name}. Do not save in this slot; load another and save to a new one."
                _snap_err(f"SNAPSHOT: ERROR - GUID mismatch for {slot_name}.")
                return False

            if not snap_slot or not snap_guid:
                legacy_snapshot = True
                snap["snapshot_slot"] = slot_name
                if expected_guid:
                    snap["snapshot_guid"] = expected_guid
                else:
                    snap["snapshot_guid"] = _ensure_slot_guid(slot_name)

            if not expected_guid and snap_guid:
                _ensure_slot_guid(slot_name)
                persistent._slot_guids[slot_name] = snap_guid

            if legacy_snapshot:
                snap["_legacy_snapshot"] = True
            return True
        except Exception as e:
            store._snapshot_validation_error = f"Snapshot validation failed: {e}. Do not save in this slot; load another and save to a new one."
            _snap_err(f"SNAPSHOT: ERROR - snapshot slot validation failed: {e}")
            return False

    def _upgrade_legacy_snapshot_file(filepath, snap, slot_name):
        """Persist legacy snapshot with slot/guid to prevent cross-slot corruption."""
        try:
            if not hasattr(snap, "get"):
                return
            if not snap.get("_legacy_snapshot"):
                return
            snap.pop("_legacy_snapshot", None)
            snap["snapshot_slot"] = slot_name
            snap["snapshot_guid"] = _ensure_slot_guid(slot_name)
            _write_snapshot_file(filepath, snap, slot_name)
            _snap_log(f"SNAPSHOT: Upgraded legacy snapshot for {slot_name}")
        except Exception as e:
            _snap_err(f"SNAPSHOT: ERROR - Failed to upgrade legacy snapshot for {slot_name}: {e}")

    def _sync_building_assignments_from_workers():
        """Rebuild building assigned_servants from workers' assigned_building (single source of truth).
        Deduplicates by name. Cleans orphaned servant_jobs entries."""
        try:
            ab_dict = getattr(store, "available_buildings", {}) or {}

            # Step 1: Clear all assigned_servants
            for bname, bdata in ab_dict.items():
                if hasattr(bdata, "get"):
                    bdata["assigned_servants"] = []

            # Step 2: Rebuild from workers
            seen_per_building = {}
            for w in store.workers:
                if not hasattr(w, "get"):
                    continue
                wname = w.get("name")
                if not wname:
                    continue
                assigned = w.get("assigned_building", "Unassigned")
                if assigned == "Unassigned" or assigned not in ab_dict:
                    continue
                if assigned not in seen_per_building:
                    seen_per_building[assigned] = set()
                if wname in seen_per_building[assigned]:
                    continue
                seen_per_building[assigned].add(wname)
                ab_dict[assigned]["assigned_servants"].append(w)

            # Step 3: Clean orphaned servant_jobs
            for bname, bdata in ab_dict.items():
                if not hasattr(bdata, "get"):
                    continue
                sj = bdata.get("servant_jobs")
                if not sj or not hasattr(sj, "keys"):
                    continue
                assigned_here = seen_per_building.get(bname, set())
                for k in [k for k in sj if k not in assigned_here]:
                    del sj[k]
        except Exception as e:
            _snap_err(f"SNAPSHOT: ERROR - sync building assignments failed: {e}")
    
    def _safe_getattr(store_obj, attr_name, default_value):
        """Safely get attribute from store, returning default if it doesn't exist or causes error."""
        try:
            if hasattr(store_obj, attr_name):
                return getattr(store_obj, attr_name, default_value)
            return default_value
        except Exception:
            return default_value
    
    def _to_list(value):
        """Convert value to a native Python list, handling RevertableList and other list-like objects."""
        if value is None:
            return None
        if hasattr(value, '__iter__') and hasattr(value, '__len__') and not isinstance(value, str):
            try:
                return list(value)
            except Exception:
                pass
        return None
    
    def _to_dict(value):
        """Convert value to a native Python dict, handling RevertableDict and other dict-like objects."""
        if value is None:
            return None
        if hasattr(value, "get"):
            return value
        if hasattr(value, '__getitem__') and hasattr(value, 'keys') and hasattr(value, '__len__'):
            try:
                return dict(value)
            except Exception:
                pass
        return None
    
    def _is_list_like(value):
        """Check if value is list-like (list, RevertableList, or other iterable with length)."""
        if value is None:
            return False
        if hasattr(value, '__iter__') and hasattr(value, '__len__') and not isinstance(value, str):
            return True
        return False
    
    def _is_dict_like(value):
        """Check if value is dict-like (dict, RevertableDict, or other mapping)."""
        if value is None:
            return False
        if hasattr(value, "get"):
            return True
        if hasattr(value, '__getitem__') and hasattr(value, 'keys') and hasattr(value, '__len__'):
            return True
        return False
    
    def _sanitize_data_before_save():
        """Clean and validate data before saving to prevent corruption."""
        sanitized_count = 0

        # Sanitize manager_inventory - ONLY convert RevertableList to normal list, don't validate/reject items
        manager_inv = getattr(store, "manager_inventory", [])
        manager_inv_list = _to_list(manager_inv)
        
        # CRITICAL: Only convert to normal list if needed, but DON'T validate or reject items
        # The items exist in the game, so they are valid by definition
        if manager_inv_list is not None:
            # Only update if it's not already a normal list (to prevent RevertableList issues)
            if not (hasattr(store.manager_inventory, "__iter__") and not isinstance(store.manager_inventory, str)):
                store.manager_inventory = manager_inv_list
                renpy.store.manager_inventory = store.manager_inventory
                _snap_log(f"SNAPSHOT: SANITIZE - Converted manager_inventory from {type(manager_inv)} to list ({len(manager_inv_list)} items)")
        else:
            # If conversion failed, initialize empty list
            if not hasattr(store, 'manager_inventory') or store.manager_inventory is None:
                store.manager_inventory = []
                renpy.store.manager_inventory = store.manager_inventory
        
        # Sanitize workers
        workers = getattr(store, "workers", [])
        for worker in workers:
            # Ensure worker has required fields
            if not hasattr(worker, "get"):
                continue

            # Ensure name exists and is valid
            if not worker.get("name") or not isinstance(worker.get("name"), str):
                worker["name"] = f"Worker_{sanitized_count}"
                sanitized_count += 1
                _snap_log(f"SNAPSHOT: SANITIZE - Worker missing name, assigned '{worker['name']}'")
            
            # Sanitize inventory - ONLY convert RevertableList to normal list, don't validate/reject items
            if "inventory" in worker:
                inv = _to_list(worker["inventory"])
                if inv is None:
                    worker["inventory"] = []
                else:
                    # Only convert to normal list if needed, but DON'T validate or reject items
                    # The items exist in the game, so they are valid by definition
                    if not (hasattr(worker["inventory"], "__iter__") and not isinstance(worker["inventory"], str)):
                        worker["inventory"] = inv
                        _snap_log(f"SNAPSHOT: SANITIZE - Converted {worker.get('name')}'s inventory from {type(worker.get('inventory'))} to list ({len(inv)} items)")
        
        # Sanitize available_buildings references
        buildings = getattr(store, "available_buildings", {})
        worker_names = {w.get("name") for w in workers if w.get("name")}
        
        for bname, building in buildings.items():
            building_dict = _to_dict(building)
            if not building_dict:
                continue
            
            # Clean servant_jobs
            servant_jobs = _to_dict(building_dict.get("servant_jobs", {}))
            if servant_jobs and worker_names:
                valid_jobs = {name: job for name, job in servant_jobs.items() if name in worker_names}
                if len(valid_jobs) != len(servant_jobs):
                    building_dict["servant_jobs"] = valid_jobs
                    sanitized_count += 1
                    _snap_log(f"SNAPSHOT: SANITIZE - Cleaned invalid worker references from {bname}.servant_jobs")
        
        if sanitized_count > 0:
            _snap_log(f"SNAPSHOT: SANITIZE - Cleaned {sanitized_count} data issues before saving")
        
        return sanitized_count
    
    def _build_snapshot():
        """Build a complete snapshot of current game state."""
        try:
            # Log manager_inventory BEFORE sanitization
            manager_inv_before = getattr(store, "manager_inventory", [])
            manager_inv_before_list = _to_list(manager_inv_before)
            _snap_log(f"SNAPSHOT: _build_snapshot - manager_inventory BEFORE sanitization: type={type(manager_inv_before)}, len={len(manager_inv_before_list) if manager_inv_before_list else 0}, items={manager_inv_before_list[:3] if manager_inv_before_list and len(manager_inv_before_list) > 0 else 'empty'}")
            
            # Sanitize data before building snapshot
            _snap_log("SNAPSHOT: Starting _build_snapshot, calling _sanitize_data_before_save()")
            _sanitize_data_before_save()
            _snap_log("SNAPSHOT: _sanitize_data_before_save() completed")
            
            # Log manager_inventory AFTER sanitization
            manager_inv_after = getattr(store, "manager_inventory", [])
            manager_inv_after_list = _to_list(manager_inv_after)
            _snap_log(f"SNAPSHOT: _build_snapshot - manager_inventory AFTER sanitization: type={type(manager_inv_after)}, len={len(manager_inv_after_list) if manager_inv_after_list else 0}, items={manager_inv_after_list[:3] if manager_inv_after_list and len(manager_inv_after_list) > 0 else 'empty'}")
            
            # Direct deepcopy of workers - this should preserve inventory if it exists
            workers_copy = _cp.deepcopy(getattr(store, "workers", []))
            total_inventory_items = 0
            
            # Ensure all workers have inventory field (even if empty) and log what we're saving
            for worker in workers_copy:
                worker_name = worker.get("name", "Unknown")
                worker_energy = worker.get("energy", "N/A")
                worker_health = worker.get("health", "N/A")
                
                # Ensure inventory exists as a list
                if "inventory" not in worker:
                    worker["inventory"] = []
                else:
                    # Convert to list if it's not already (handles RevertableList, etc.)
                    converted_inv = _to_list(worker["inventory"])
                    worker["inventory"] = converted_inv if converted_inv is not None else []
                
                inv_count = len(worker["inventory"])
                if inv_count > 0:
                    total_inventory_items += inv_count
                    # Log first few items to verify they're being captured
                    items_preview = []
                    for item in worker["inventory"][:3]:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            items_preview.append(f"{item[0]}(qty:{item[1]},eq:{item[2] if len(item) > 2 else False})")
                        else:
                            items_preview.append(str(item))
            
            # manager_interactions_today saved above
            
            # Build snapshot dict
            # CRITICAL: Get manager_inventory - preserve it as-is but ensure it's a list
            # Don't normalize here - just ensure it's serializable
            manager_inv_final = _to_list(getattr(store, "manager_inventory", [])) or []
            _snap_log(f"SNAPSHOT: _build_snapshot - manager_inventory has {len(manager_inv_final)} items before deepcopy")
            if len(manager_inv_final) > 0:
                _snap_log(f"SNAPSHOT: _build_snapshot - First few items: {manager_inv_final[:3]}")
            
            snapshot_result = {
                "snapshot_version": 2,
                "money": int(store.money) if hasattr(store, "money") else 6000,
                "current_day": getattr(store, "current_day", 1),
                "current_month": getattr(store, "current_month", 1),
                "current_year": getattr(store, "current_year", 1),
                "workers": workers_copy,
                "available_workers": _cp.deepcopy(_to_list(getattr(store, "available_workers", [])) or []),
                "available_buildings": _cp.deepcopy(getattr(store, "available_buildings", {})),
                "owned_buildings": _cp.deepcopy(getattr(store, "owned_buildings", [])),
                "map_button_buildings": _cp.deepcopy(getattr(store, "map_button_buildings", {})),
                "custom_names": dict(getattr(store, "custom_names", {})),
                "player_name": getattr(store, "player_name", ""),
                "player_title": getattr(store, "player_title", ""),
                "tutorial_active": getattr(store, "tutorial_active", True),
                "current_objective": getattr(store, "current_objective", 1),
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
                "governor_attention": _safe_getattr(store, "governor_attention", 0),
                "governor_tension_active": _safe_getattr(store, "governor_tension_active", False),
                "governor_retaliation_done": _safe_getattr(store, "governor_retaliation_done", False),
                "days_since_last_tension_event": _safe_getattr(store, "days_since_last_tension_event", 0),
                "workers_hired": getattr(store, "workers_hired", 0),
                "building_1_type_set": getattr(store, "building_1_type_set", False),
                "workers_assigned_count": getattr(store, "workers_assigned_count", 0),
                "potion_purchased": _safe_getattr(store, "potion_purchased", False),
                "potion_transferred": _safe_getattr(store, "potion_transferred", False),
                "potion_used_on_worker": _safe_getattr(store, "potion_used_on_worker", False),
                "building_upgraded_tutorial": _safe_getattr(store, "building_upgraded_tutorial", False),
                "building_skill_bonus_increased_tutorial": _safe_getattr(store, "building_skill_bonus_increased_tutorial", False),
                "tutorial_friendly_chat_done": _safe_getattr(store, "tutorial_friendly_chat_done", False),
                "event_flags": _cp.deepcopy(getattr(store, "event_flags", {})),
                "event_occurrences": _cp.deepcopy(getattr(store, "event_occurrences", {})),
                "event_last_occurred": _cp.deepcopy(getattr(store, "event_last_occurred", {})),
                "daily_spawns": _safe_getattr(store, "daily_spawns", 0),
                "can_recruit_today": _safe_getattr(store, "can_recruit_today", True),
                "last_worker_refill_day": _safe_getattr(store, "last_worker_refill_day", None),
                "last_worker_refill_month": _safe_getattr(store, "last_worker_refill_month", None),
                "last_worker_refill_year": _safe_getattr(store, "last_worker_refill_year", None),
                "map_worker_refill_count": _safe_getattr(store, "map_worker_refill_count", 0),
                "last_map_refill_day": _safe_getattr(store, "last_map_refill_day", None),
                "last_take_a_walk_day": _safe_getattr(store, "last_take_a_walk_day", None),
                "take_a_walk_in_progress": _safe_getattr(store, "take_a_walk_in_progress", False),
                "manager_inventory": _cp.deepcopy(manager_inv_final),
                "unlocked_shops": _cp.deepcopy(getattr(store, "unlocked_shops", {})),
                "manager_interactions_today": _safe_getattr(store, "manager_interactions_today", 0),
                "game_initialized": True,
                "is_new_game": False,
                "academy_enrolled": _safe_getattr(store, "academy_enrolled", False),
                "academy_haggle_available": _safe_getattr(store, "academy_haggle_available", True),
                # Yvara route progression (Stage 1+)
                "yvara_known_name": _safe_getattr(store, "yvara_known_name", False),
                "yvara_devotion": _safe_getattr(store, "yvara_devotion", 0),
                "yvara_dominion": _safe_getattr(store, "yvara_dominion", 0),
                "yvara_affection": _safe_getattr(store, "yvara_affection", 0),
                "yvara_stage": _safe_getattr(store, "yvara_stage", 1),
                "yvara_visit_count": _safe_getattr(store, "yvara_visit_count", 0),
                "yvara_last_question_total_days": _safe_getattr(store, "yvara_last_question_total_days", None),
                "yvara_last_gift_total_days": _safe_getattr(store, "yvara_last_gift_total_days", None),
                "yvara_last_talk_total_days": _safe_getattr(store, "yvara_last_talk_total_days", None),
                "yvara_s3_gate_ready": _safe_getattr(store, "yvara_s3_gate_ready", False),
                "yvara_s3_gate_ready_total_days": _safe_getattr(store, "yvara_s3_gate_ready_total_days", None),
                "yvara_s4_finance_unlocked": _safe_getattr(store, "yvara_s4_finance_unlocked", False),
                "yvara_s4_finance_last_day": _safe_getattr(store, "yvara_s4_finance_last_day", None),
                "yvara_s4_donation_total": _safe_getattr(store, "yvara_s4_donation_total", 0),
                "yvara_s4_donation_highest_tier": _safe_getattr(store, "yvara_s4_donation_highest_tier", 0),
                "yvara_s4_favors_total": _safe_getattr(store, "yvara_s4_favors_total", 0),
                "yvara_s4_favor_highest_tier": _safe_getattr(store, "yvara_s4_favor_highest_tier", 0),
                "yvara_s1_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s1_talks_done", [])) or []),
                "yvara_s1_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s1_remarks_done", [])) or []),
                "yvara_gifts_given": _safe_getattr(store, "yvara_gifts_given", 0),
                "yvara_s2_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s2_talks_done", [])) or []),
                "yvara_s2_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s2_remarks_done", [])) or []),
                "yvara_s2_gifts_given": _safe_getattr(store, "yvara_s2_gifts_given", 0),
                "yvara_s3_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s3_talks_done", [])) or []),
                "yvara_s3_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s3_remarks_done", [])) or []),
                "yvara_observed_sessions": _safe_getattr(store, "yvara_observed_sessions", 0),
                "yvara_observed_last_day": _safe_getattr(store, "yvara_observed_last_day", None),
                "yvara_lesson_absorbed": _safe_getattr(store, "yvara_lesson_absorbed", False),
                "yvara_leverage_financial": _safe_getattr(store, "yvara_leverage_financial", False),
                "yvara_s3_gate_fired": _safe_getattr(store, "yvara_s3_gate_fired", False),
                "yvara_s4_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s4_talks_done", [])) or []),
                "yvara_s4_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s4_remarks_done", [])) or []),
                "yvara_s4_gate_fired": _safe_getattr(store, "yvara_s4_gate_fired", False),
                "yvara_morning_after_done": _safe_getattr(store, "yvara_morning_after_done", False),
                "yvara_evening_academy_last_day": _safe_getattr(store, "yvara_evening_academy_last_day", None),
                "yvara_evening_tier": _safe_getattr(store, "yvara_evening_tier", 1),
                "yvara_evening_variant_index": _safe_getattr(store, "yvara_evening_variant_index", 0),
                "yvara_academy_investment_tier": _safe_getattr(store, "yvara_academy_investment_tier", 0),
                "yvara_academy_investment_total": _safe_getattr(store, "yvara_academy_investment_total", 0),
                "yvara_academy_investments_count": _safe_getattr(store, "yvara_academy_investments_count", 0),
                "yvara_s5_gate_fired": _safe_getattr(store, "yvara_s5_gate_fired", False),
                "yvara_s6_gate_fired": _safe_getattr(store, "yvara_s6_gate_fired", False),
                "yvara_ending_route": _safe_getattr(store, "yvara_ending_route", ""),
                "yvara_is_worker": _safe_getattr(store, "yvara_is_worker", False),
                "yvara_ending_done": _safe_getattr(store, "yvara_ending_done", False),
                "yvara_academy_discount_active": _safe_getattr(store, "yvara_academy_discount_active", False),
                "yvara_lab_access": _safe_getattr(store, "yvara_lab_access", False),
                "yvara_lab_gift_last_day": _safe_getattr(store, "yvara_lab_gift_last_day", None),
                "yvara_post_arc_talk_index": _safe_getattr(store, "yvara_post_arc_talk_index", 0),
                "yvara_arrangement_change_count": _safe_getattr(store, "yvara_arrangement_change_count", 0),
                "yvara_good_word_count": _safe_getattr(store, "yvara_good_word_count", 0),
                "yvara_good_word_last_day": _safe_getattr(store, "yvara_good_word_last_day", None),
                "yvara_good_word_peak": _safe_getattr(store, "yvara_good_word_peak", False),
                "yvara_s5_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s5_talks_done", [])) or []),
                "yvara_s5_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s5_remarks_done", [])) or []),
                "yvara_s6_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_s6_talks_done", [])) or []),
                # Lanista arc progression
                "lanista_gender": _safe_getattr(store, "lanista_gender", ""),
                "lanista_known_name": _safe_getattr(store, "lanista_known_name", False),
                "lanista_devotion": _safe_getattr(store, "lanista_devotion", 0),
                "lanista_dominion": _safe_getattr(store, "lanista_dominion", 0),
                "lanista_affection": _safe_getattr(store, "lanista_affection", 0),
                "lanista_corruption": _safe_getattr(store, "lanista_corruption", 0),
                "lanista_stage": _safe_getattr(store, "lanista_stage", 1),
                "lanista_visit_count": _safe_getattr(store, "lanista_visit_count", 0),
                "lanista_last_talk_total_days": _safe_getattr(store, "lanista_last_talk_total_days", None),
                "lanista_last_question_total_days": _safe_getattr(store, "lanista_last_question_total_days", None),
                "lanista_last_gift_total_days": _safe_getattr(store, "lanista_last_gift_total_days", None),
                "lanista_gifts_given": _safe_getattr(store, "lanista_gifts_given", 0),
                "lanista_debt_finance_unlocked": _safe_getattr(store, "lanista_debt_finance_unlocked", False),
                "lanista_debt_finance_last_day": _safe_getattr(store, "lanista_debt_finance_last_day", None),
                "lanista_donation_total": _safe_getattr(store, "lanista_donation_total", 0),
                "lanista_donation_highest_tier": _safe_getattr(store, "lanista_donation_highest_tier", 0),
                "lanista_favors_total": _safe_getattr(store, "lanista_favors_total", 0),
                "lanista_favor_highest_tier": _safe_getattr(store, "lanista_favor_highest_tier", 0),
                "lanista_card_tier": _safe_getattr(store, "lanista_card_tier", 0),
                "lanista_card_last_day": _safe_getattr(store, "lanista_card_last_day", None),
                "lanista_pinup_unlocked": _safe_getattr(store, "lanista_pinup_unlocked", False),
                "lanista_oilchains_unlocked": _safe_getattr(store, "lanista_oilchains_unlocked", False),
                "lanista_spectacle_unlocked": _safe_getattr(store, "lanista_spectacle_unlocked", False),
                "lanista_wager_last_day": _safe_getattr(store, "lanista_wager_last_day", None),
                "lanista_s3_gate_fired": _safe_getattr(store, "lanista_s3_gate_fired", False),
                "lanista_s4_gate_fired": _safe_getattr(store, "lanista_s4_gate_fired", False),
                "lanista_morning_after_done": _safe_getattr(store, "lanista_morning_after_done", False),
                "lanista_s5_gate_fired": _safe_getattr(store, "lanista_s5_gate_fired", False),
                "lanista_s6_gate_fired": _safe_getattr(store, "lanista_s6_gate_fired", False),
                "lanista_aftercrowd_last_day": _safe_getattr(store, "lanista_aftercrowd_last_day", None),
                "lanista_aftercrowd_tier": _safe_getattr(store, "lanista_aftercrowd_tier", 1),
                "lanista_aftercrowd_variant_index": _safe_getattr(store, "lanista_aftercrowd_variant_index", 0),
                "lanista_ending_route": _safe_getattr(store, "lanista_ending_route", ""),
                "lanista_ending_done": _safe_getattr(store, "lanista_ending_done", False),
                "lanista_is_worker": _safe_getattr(store, "lanista_is_worker", False),
                "lanista_ending_devotion": _safe_getattr(store, "lanista_ending_devotion", False),
                "lanista_ending_dominion": _safe_getattr(store, "lanista_ending_dominion", False),
                "lanista_ending_mixed": _safe_getattr(store, "lanista_ending_mixed", False),
                "lanista_post_arc_talk_index": _safe_getattr(store, "lanista_post_arc_talk_index", 0),
                "lanista_arrangement_change_count": _safe_getattr(store, "lanista_arrangement_change_count", 0),
                "lanista_s1_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s1_talks_done", [])) or []),
                "lanista_s1_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s1_remarks_done", [])) or []),
                "lanista_s2_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s2_talks_done", [])) or []),
                "lanista_s2_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s2_remarks_done", [])) or []),
                "lanista_s3_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s3_talks_done", [])) or []),
                "lanista_s3_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s3_remarks_done", [])) or []),
                "lanista_s4_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s4_talks_done", [])) or []),
                "lanista_s4_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s4_remarks_done", [])) or []),
                "lanista_s5_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s5_talks_done", [])) or []),
                "lanista_s5_remarks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s5_remarks_done", [])) or []),
                "lanista_s6_talks_done": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_s6_talks_done", [])) or []),
                "management_skills": _cp.deepcopy(getattr(store, "management_skills", {"business_acumen": 0, "whore_mastery": 0, "combat_instruction": 0, "servant_training": 0, "gang_leader": 0})),
                "manager_portrait": getattr(store, "manager_portrait", ""),
                "manager_start_skill_chosen": _safe_getattr(store, "manager_start_skill_chosen", False),
                "manager_level": _safe_getattr(store, "manager_level", 1),
                # Arena / Laboratory progression and cooldowns
                "arena_unlocked": _safe_getattr(store, "arena_unlocked", False),
                "arena_lanista_paid": _safe_getattr(store, "arena_lanista_paid", False),
                "arena_special_match_intro_done": _safe_getattr(store, "arena_special_match_intro_done", False),
                "last_special_match_total_days": _safe_getattr(store, "last_special_match_total_days", None),
                "last_special_match_worker_name": _safe_getattr(store, "last_special_match_worker_name", None),
                "alchemy_unlocked": _safe_getattr(store, "alchemy_unlocked", False),
                "last_laboratory_use_total_days": _safe_getattr(store, "last_laboratory_use_total_days", None)
            }
            if DEBUG_SNAPSHOT:
                renpy.log(f"SNAPSHOT: DEBUG - _build_snapshot returning type: {type(snapshot_result)}, is dict: {hasattr(snapshot_result, 'get')}, keys: {len(snapshot_result.keys()) if hasattr(snapshot_result, 'get') else 'N/A'}")
            return snapshot_result
        except Exception as e:
            renpy.log(f"SNAPSHOT: CRITICAL ERROR - build error: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: CRITICAL ERROR - traceback: {traceback.format_exc()}")
            # Return empty dict but log critical error - caller should check for empty
            return {}
    
    def _normalize_trait_set(raw):
        out = set()
        if raw is None:
            return out
        if isinstance(raw, str):
            if raw:
                out.add(raw.strip().lower())
            return out
        if hasattr(raw, "__iter__"):
            try:
                for t in raw:
                    if t is None:
                        continue
                    out.add(str(t).strip().lower())
            except Exception:
                pass
        return out

    def _build_json_template_index():
        # Returns (by_name, by_folder). Each row is the JSON template dict.
        # Returns (None, None) if templates can't be loaded — caller must abort migration.
        by_name = {}
        by_folder = {}
        try:
            _loader = getattr(store, "load_workers", None)
            if not callable(_loader):
                return None, None
            templates = _loader(include_unique=True, include_encounter_only=True, for_events=True) or []
            if not templates:
                return None, None
            for tpl in templates:
                if not hasattr(tpl, "get"):
                    continue
                if tpl.get("procedural", False) or tpl.get("monster", False):
                    continue
                name = tpl.get("name")
                folder = tpl.get("folder")
                if not name or not folder:
                    continue
                by_name.setdefault(name, []).append(tpl)
                by_folder.setdefault(folder, tpl)
            return by_name, by_folder
        except Exception as e:
            renpy.log(f"MIGRATION v2: failed to build JSON template index: {e}")
            return None, None

    def _migrate_worker_folders_inplace(workers_list, by_name, by_folder, label=""):
        # Conservative, idempotent. Returns (stamped, fixed_folder, skipped_ambiguous).
        # Never overwrites a valid template_id. Never touches procedural/monster.
        # When ambiguous, leaves the worker alone rather than guessing.
        stamped = 0
        fixed_folder = 0
        skipped_ambiguous = 0
        if not workers_list:
            return stamped, fixed_folder, skipped_ambiguous

        for worker in workers_list:
            if not hasattr(worker, "get"):
                continue
            if worker.get("procedural", False) or worker.get("monster", False):
                continue

            name = worker.get("name")
            if not name:
                continue

            existing_tid = worker.get("template_id") or ""
            current_folder = worker.get("folder", "") or ""

            resolved_tid = None

            # Preference 1: existing template_id still valid in current JSON.
            if existing_tid and existing_tid in by_folder:
                mapped = by_folder.get(existing_tid)
                if mapped and mapped.get("name") == name:
                    resolved_tid = existing_tid

            # Preference 2: current folder maps to a known template with matching name.
            if not resolved_tid and current_folder and current_folder in by_folder:
                mapped = by_folder.get(current_folder)
                if mapped and mapped.get("name") == name:
                    resolved_tid = current_folder

            # Preference 3: unique name match across JSON.
            if not resolved_tid:
                candidates = by_name.get(name, [])
                if len(candidates) == 1:
                    resolved_tid = candidates[0].get("folder")
                elif len(candidates) > 1:
                    # Disambiguate by trait intersection, race as a strong secondary signal.
                    worker_traits = _normalize_trait_set(worker.get("traits"))
                    worker_race = (worker.get("race") or "").strip().lower()

                    best_tid = None
                    best_score = -1
                    tied = False
                    for cand in candidates:
                        cand_traits = _normalize_trait_set(cand.get("traits"))
                        cand_race = (cand.get("race") or "").strip().lower()
                        score = len(worker_traits & cand_traits)
                        if worker_race and cand_race and worker_race == cand_race:
                            score += 10
                        if score > best_score:
                            best_score = score
                            best_tid = cand.get("folder")
                            tied = False
                        elif score == best_score:
                            tied = True

                    if best_tid and best_score > 0 and not tied:
                        resolved_tid = best_tid

            if not resolved_tid:
                if by_name.get(name):
                    renpy.log(f"MIGRATION v2{label}: ambiguous template for '{name}' (folder='{current_folder}') — leaving unchanged")
                    skipped_ambiguous += 1
                continue

            if existing_tid != resolved_tid:
                worker["template_id"] = resolved_tid
                stamped += 1

            if current_folder != resolved_tid:
                renpy.log(f"MIGRATION v2{label}: '{name}' folder '{current_folder}' -> '{resolved_tid}'")
                worker["folder"] = resolved_tid
                fixed_folder += 1

        return stamped, fixed_folder, skipped_ambiguous

    # Expose to store so other modules (script.rpy fallback, debug helper) can reuse.
    store._build_json_template_index = _build_json_template_index
    store._migrate_worker_folders_inplace = _migrate_worker_folders_inplace

    def _migrate_snapshot(snap):
        """Migrate snapshot to current version format if needed."""
        if not hasattr(snap, "get"):
            return snap

        version = snap.get("snapshot_version", 0)
        current_version = 2

        if version == current_version:
            return snap  # No migration needed

        renpy.log(f"SNAPSHOT: MIGRATION - Migrating snapshot from version {version} to {current_version}")

        if version == 0:
            snap["snapshot_version"] = 1
            version = 1

        if version == 1:
            # v1 -> v2: stamp template_id, correct legacy folder corruption from name-based sync.
            by_name, by_folder = _build_json_template_index()
            if by_name is None:
                renpy.log("MIGRATION v2: JSON templates unavailable — aborting migration, will retry on next load")
                # Do NOT bump version; snap stays at 1 so next load retries.
                return snap

            s1, f1, sk1 = _migrate_worker_folders_inplace(snap.get("workers") or [], by_name, by_folder, label=" [workers]")
            s2, f2, sk2 = _migrate_worker_folders_inplace(snap.get("available_workers") or [], by_name, by_folder, label=" [available]")
            renpy.log(
                f"MIGRATION v2: stamped template_id on {s1 + s2} workers, fixed folder on {f1 + f2}, "
                f"skipped {sk1 + sk2} ambiguous"
            )
            snap["snapshot_version"] = 2
            version = 2

        renpy.log(f"SNAPSHOT: MIGRATION - Migration complete, snapshot now at version {snap.get('snapshot_version', current_version)}")
        return snap
    
    def _apply_snapshot(snap):
        """Apply a snapshot to restore game state. Applies all valid fields individually.
        Returns True if at least one critical field was applied, False if completely unusable."""
        applied_any = False
        applied_critical = False
        applied_fields = []
        missing_fields = []
        failed_fields = []
        
        try:
            if not snap:
                renpy.log("SNAPSHOT: WARNING - Empty snapshot provided to _apply_snapshot")
                return False
            
            # Pre-validation: ensure snapshot is a dict
            if not hasattr(snap, "get"):
                renpy.log(f"SNAPSHOT: ERROR - Snapshot is not a dict (type: {type(snap)})")
                return False
            
            snap = _migrate_snapshot(snap)
            
            # Track expected fields
            expected_fields = [
                "money", "current_day", "current_month", "current_year", "workers",
                "available_buildings", "owned_buildings", "map_button_buildings",
                "custom_names", "player_name", "player_title", "tutorial_active",
                "current_objective", "manager_inventory", "unlocked_shops",
                "manager_interactions_today", "event_flags", "event_occurrences",
                "event_last_occurred"
            ]
            
            # Try to apply each field individually, preserving what we can
            # Money (critical)
            try:
                money_val = snap.get("money")
                if money_val is not None:
                    current_money = getattr(store, 'money', 6000)
                    store.money = int(money_val)
                    applied_any = True
                    applied_critical = True
                    applied_fields.append("money")
                else:
                    missing_fields.append("money")
                    renpy.log("SNAPSHOT: WARNING - money is None, keeping current value")
            except Exception as e:
                failed_fields.append("money")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply money: {e}, keeping current value")
            
            # Date fields (critical: day, important: month/year)
            try:
                day_val = snap.get("current_day")
                if day_val is not None:
                    store.current_day = int(day_val)
                    applied_any = True
                    applied_critical = True
                    applied_fields.append("current_day")
                else:
                    missing_fields.append("current_day")
                    renpy.log("SNAPSHOT: WARNING - current_day is None, keeping current value")
            except Exception as e:
                failed_fields.append("current_day")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply current_day: {e}")
            
            try:
                month_val = snap.get("current_month")
                if month_val is not None:
                    store.current_month = int(month_val)
                    applied_any = True
                    applied_fields.append("current_month")
                else:
                    missing_fields.append("current_month")
                    # Use current value or default
                    if not hasattr(store, 'current_month'):
                        store.current_month = 1
            except Exception as e:
                failed_fields.append("current_month")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply current_month: {e}")
            
            try:
                year_val = snap.get("current_year")
                if year_val is not None:
                    store.current_year = int(year_val)
                    applied_any = True
                    applied_fields.append("current_year")
                else:
                    missing_fields.append("current_year")
                    # Use current value or default
                    if not hasattr(store, 'current_year'):
                        store.current_year = 1
            except Exception as e:
                failed_fields.append("current_year")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply current_year: {e}")
            
            # Workers (critical)
            try:
                workers_val = snap.get("workers")
                converted_workers = _to_list(workers_val)
                
                if converted_workers is not None:
                    store.workers = _cp.deepcopy(converted_workers)
                    # CRITICAL: Force Ren'Py to recognize the new workers immediately
                    renpy.store.workers = store.workers
                    applied_any = True
                    applied_critical = True
                    applied_fields.append("workers")
                    renpy.log(f"SNAPSHOT: Applied {len(store.workers)} workers successfully")
                    # Log flags for debugging
                    for worker in store.workers[:3]:
                        worker_flags = worker.get("flags", {})
                        if worker_flags:
                            renpy.log(f"SNAPSHOT: Worker {worker.get('name', 'Unknown')} has flags: {list(worker_flags.keys())}")
                else:
                    missing_fields.append("workers")
                    renpy.log(f"SNAPSHOT: WARNING - workers is invalid (type: {type(workers_val)}, is None: {workers_val is None}), keeping current workers")
            except Exception as e:
                failed_fields.append("workers")
                renpy.log(f"SNAPSHOT: ERROR - Exception applying workers: {e}, keeping current workers")
                import traceback
                renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")

            # Apply available_workers (non-critical, but needed for buy servants list)
            try:
                available_workers_val = snap.get("available_workers")
                converted_available_workers = _to_list(available_workers_val)
                if converted_available_workers is not None:
                    store.available_workers = _cp.deepcopy(converted_available_workers)
                    # Keep Ren'Py store in sync
                    renpy.store.available_workers = store.available_workers
                    applied_any = True
                    applied_fields.append("available_workers")
                    renpy.log(f"SNAPSHOT: Applied {len(store.available_workers)} available_workers")
                else:
                    missing_fields.append("available_workers")
                    if not hasattr(store, "available_workers"):
                        store.available_workers = []
            except Exception as e:
                failed_fields.append("available_workers")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply available_workers: {e}")

            # CRITICAL: Apply management_skills BEFORE ensure_worker_defaults.
            # ensure_worker_defaults calls calculate_max_energy/calculate_max_health which read
            # management_skills for Gang Leader (+10 max Energy), Combat Instruction (+10 max HP),
            # and get_attribute_cap for Servant Training (reduces max Rebelliousness).
            for field_name, default_val in [
                ("management_skills", {"business_acumen": 0, "whore_mastery": 0, "combat_instruction": 0, "servant_training": 0, "gang_leader": 0}),
                ("manager_portrait", ""),
                ("manager_start_skill_chosen", False),
                ("manager_level", 1)
            ]:
                try:
                    if field_name in snap:
                        val = snap.get(field_name)
                        if field_name == "management_skills":
                            converted = _to_dict(val)
                            if converted is not None:
                                setattr(store, field_name, _cp.deepcopy(converted))
                                applied_any = True
                                applied_fields.append(field_name)
                        elif val is not None or default_val is None:
                            setattr(store, field_name, val if val is not None else default_val)
                            applied_any = True
                            applied_fields.append(field_name)
                        elif not hasattr(store, field_name):
                            setattr(store, field_name, default_val)
                    elif not hasattr(store, field_name):
                        setattr(store, field_name, default_val)
                except Exception as e:
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name} (pre-worker-defaults): {e}")

            # CRITICAL: Ensure worker defaults (including min 3-5 traits) after snapshot restore.
            # Restored workers never pass through ensure_worker_defaults otherwise.
            try:
                if hasattr(store, 'ensure_worker_defaults'):
                    for worker in getattr(store, 'workers', []):
                        store.ensure_worker_defaults(worker)
                    for worker in getattr(store, 'available_workers', []):
                        store.ensure_worker_defaults(worker)
                    renpy.log("SNAPSHOT: Applied ensure_worker_defaults to all workers after restore")
                else:
                    renpy.log("SNAPSHOT: WARNING - ensure_worker_defaults not found")
            except Exception as e:
                renpy.log(f"SNAPSHOT: ensure_worker_defaults error: {e}")

            # Only continue if we applied at least one critical field
            if not applied_critical:
                renpy.log("SNAPSHOT: ERROR - No critical fields (money, day, or workers) could be applied")
                return False
            
            # Apply buildings (important but not critical - try each individually)
            try:
                buildings_val = snap.get("available_buildings")
                converted_buildings = _to_dict(buildings_val)
                
                if converted_buildings is not None:
                    restored_buildings = _cp.deepcopy(converted_buildings)
                    store.available_buildings = restored_buildings
                    applied_any = True
                    applied_fields.append("available_buildings")
                    # Log servant_jobs info
                    total_servant_jobs = 0
                    for bname, building in restored_buildings.items():
                        building_dict = _to_dict(building)
                        if building_dict:
                            servant_jobs = building_dict.get("servant_jobs", {})
                            jobs_dict = _to_dict(servant_jobs)
                            if jobs_dict:
                                total_servant_jobs += len(jobs_dict)
                    renpy.log(f"SNAPSHOT: Applied available_buildings with {len(restored_buildings)} buildings, {total_servant_jobs} total servant_jobs")
                else:
                    missing_fields.append("available_buildings")
                    renpy.log(f"SNAPSHOT: WARNING - available_buildings is invalid (type: {type(buildings_val)}, is None: {buildings_val is None})")
                    # Keep current value or initialize empty
                    if not hasattr(store, 'available_buildings'):
                        store.available_buildings = {}
            except Exception as e:
                failed_fields.append("available_buildings")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply available_buildings: {e}")
                import traceback
                renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            
            try:
                owned_val = snap.get("owned_buildings")
                converted_owned = _to_list(owned_val)
                
                if converted_owned is not None:
                    store.owned_buildings = _cp.deepcopy(converted_owned)
                    applied_any = True
                    applied_fields.append("owned_buildings")
                else:
                    missing_fields.append("owned_buildings")
                    # Keep current value or initialize empty
                    if not hasattr(store, 'owned_buildings'):
                        store.owned_buildings = []
            except Exception as e:
                failed_fields.append("owned_buildings")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply owned_buildings: {e}")
            
            try:
                map_btn_val = snap.get("map_button_buildings")
                converted_map_btn = _to_dict(map_btn_val)
                
                if converted_map_btn is not None:
                    store.map_button_buildings = _cp.deepcopy(converted_map_btn)
                    applied_any = True
                    applied_fields.append("map_button_buildings")
                else:
                    missing_fields.append("map_button_buildings")
                    # Keep current value or initialize empty
                    if not hasattr(store, 'map_button_buildings'):
                        store.map_button_buildings = {}
            except Exception as e:
                failed_fields.append("map_button_buildings")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply map_button_buildings: {e}")
            
            # CRITICAL: After restoring workers and buildings, relink assigned_servants to point to the NEW worker objects
            # This ensures that assigned_servants references the correct worker objects with the correct energy values
            try:
                # The function should be available in store after event_daily_exec.rpy is loaded
                # Try multiple ways to access it
                relink_func = None
                if hasattr(store, '_relink_assigned_servants_to_store_workers'):
                    relink_func = store._relink_assigned_servants_to_store_workers
                elif hasattr(renpy.store, '_relink_assigned_servants_to_store_workers'):
                    relink_func = renpy.store._relink_assigned_servants_to_store_workers
                
                if relink_func:
                    relink_func()
                else:
                    # Function not found - log warning but continue (non-critical)
                    renpy.log("SNAPSHOT: WARNING - _relink_assigned_servants_to_store_workers not found, skipping relink (non-critical)")
                
                # CRITICAL: Force Ren'Py to recognize the new worker objects by explicitly updating the store
                # This prevents Ren'Py from restoring old values from its native save system
                renpy.store.workers = store.workers
                _sync_building_assignments_from_workers()
            except Exception as e:
                renpy.log(f"SNAPSHOT: Error relinking assigned_servants: {e}")
                import traceback
                renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                # Don't fail the entire load if relinking fails - it's not critical
            # Apply remaining fields individually (non-critical, but try to restore as many as possible)
            for field_name, default_val, field_type in [
                ("custom_names", {}, dict),
                ("player_name", "", str),
                ("player_title", "", str),
                ("tutorial_active", True, bool),
                ("current_objective", 1, int)
            ]:
                try:
                    field_val = snap.get(field_name)
                    if field_val is not None:
                        if field_type == dict:
                            converted = _to_dict(field_val)
                            if converted is not None:
                                setattr(store, field_name, converted)
                                applied_any = True
                                applied_fields.append(field_name)
                            else:
                                missing_fields.append(field_name)
                        elif field_type == str:
                            setattr(store, field_name, str(field_val))
                            applied_any = True
                            applied_fields.append(field_name)
                        elif field_type == bool:
                            setattr(store, field_name, bool(field_val))
                            applied_any = True
                            applied_fields.append(field_name)
                        elif field_type == int:
                            setattr(store, field_name, int(field_val))
                            applied_any = True
                            applied_fields.append(field_name)
                    else:
                        missing_fields.append(field_name)
                        if not hasattr(store, field_name):
                            setattr(store, field_name, default_val)
                except Exception as e:
                    failed_fields.append(field_name)
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name}: {e}")
            store.objective_1_complete = snap.get("objective_1_complete", False)
            store.objective_2_complete = snap.get("objective_2_complete", False)
            store.objective_3_complete = snap.get("objective_3_complete", False)
            store.objective_4_complete = snap.get("objective_4_complete", False)
            store.objective_5_complete = snap.get("objective_5_complete", False)
            store.objective_6_complete = snap.get("objective_6_complete", False)
            store.objective_7_complete = snap.get("objective_7_complete", False)
            store.objective_8_complete = snap.get("objective_8_complete", False)
            store.objective_9_complete = snap.get("objective_9_complete", False)
            store.objective_10_complete = snap.get("objective_10_complete", False)
            store.objective_11_complete = snap.get("objective_11_complete", False)
            store.objective_12_complete = snap.get("objective_12_complete", False)
            store.objective_13_complete = snap.get("objective_13_complete", False)
            store.objective_14_complete = snap.get("objective_14_complete", False)
            store.objective_15_complete = snap.get("objective_15_complete", False)
            store.objective_16_complete = snap.get("objective_16_complete", False)
            store.workers_hired = snap.get("workers_hired", 0)
            store.building_1_type_set = snap.get("building_1_type_set", False)
            store.workers_assigned_count = snap.get("workers_assigned_count", 0)
            # Academy (special building, not in owned_buildings)
            store.academy_enrolled = snap.get("academy_enrolled", False)
            store.academy_haggle_available = snap.get("academy_haggle_available", True)
            if store.academy_enrolled and "Academy" not in getattr(store, "available_buildings", {}):
                if hasattr(store, "add_academy_building"):
                    store.add_academy_building()
                    renpy.log("SNAPSHOT: Restored Academy (academy_enrolled=True, Academy was missing from available_buildings)")
            # Tutorial progress variables - safe restoration
            if "potion_purchased" in snap:
                store.potion_purchased = snap.get("potion_purchased", False)
            if "potion_transferred" in snap:
                store.potion_transferred = snap.get("potion_transferred", False)
            if "potion_used_on_worker" in snap:
                store.potion_used_on_worker = snap.get("potion_used_on_worker", False)
            if "building_upgraded_tutorial" in snap:
                store.building_upgraded_tutorial = snap.get("building_upgraded_tutorial", False)
            if "building_skill_bonus_increased_tutorial" in snap:
                store.building_skill_bonus_increased_tutorial = snap.get("building_skill_bonus_increased_tutorial", False)
            if "tutorial_friendly_chat_done" in snap:
                store.tutorial_friendly_chat_done = snap.get("tutorial_friendly_chat_done", False)
            # Event and daily tracking (apply individually)
            for field_name in ["event_flags", "event_occurrences", "event_last_occurred"]:
                try:
                    field_val = snap.get(field_name)
                    converted = _to_dict(field_val)
                    if converted is not None:
                        setattr(store, field_name, _cp.deepcopy(converted))
                        applied_any = True
                        applied_fields.append(field_name)
                    else:
                        missing_fields.append(field_name)
                        if not hasattr(store, field_name):
                            setattr(store, field_name, {})
                except Exception as e:
                    failed_fields.append(field_name)
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name}: {e}")
            
            # Manager character sheet
            for field_name, default_val in [
                ("management_skills", {"business_acumen": 0, "whore_mastery": 0, "combat_instruction": 0, "servant_training": 0, "gang_leader": 0}),
                ("manager_portrait", ""),
                ("manager_start_skill_chosen", False),
                ("manager_level", 1)
            ]:
                try:
                    if field_name in snap:
                        val = snap.get(field_name)
                        if field_name == "management_skills":
                            converted = _to_dict(val)
                            if converted is not None:
                                setattr(store, field_name, _cp.deepcopy(converted))
                                applied_any = True
                                applied_fields.append(field_name)
                        elif val is not None or default_val is None:
                            setattr(store, field_name, val if val is not None else default_val)
                            applied_any = True
                            applied_fields.append(field_name)
                        elif not hasattr(store, field_name):
                            setattr(store, field_name, default_val)
                    else:
                        missing_fields.append(field_name)
                except Exception as e:
                    failed_fields.append(field_name)
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name}: {e}")

            # Apply optional fields if present
            for field_name, default_val in [
                ("daily_spawns", 0),
                ("can_recruit_today", True),
                ("last_worker_refill_day", None),
                ("last_worker_refill_month", None),
                ("last_worker_refill_year", None),
                ("map_worker_refill_count", 0),
                ("last_map_refill_day", None),
                ("governor_attention", 0),
                ("governor_tension_active", False),
                ("governor_retaliation_done", False),
                ("days_since_last_tension_event", 0),
                ("last_take_a_walk_day", None),
                ("take_a_walk_in_progress", False),
                # Yvara route progression
                ("yvara_known_name", False),
                ("yvara_devotion", 0),
                ("yvara_dominion", 0),
                ("yvara_affection", 0),
                ("yvara_stage", 1),
                ("yvara_visit_count", 0),
                ("yvara_last_question_total_days", None),
                ("yvara_last_gift_total_days", None),
                ("yvara_last_talk_total_days", None),
                ("yvara_s3_gate_ready", False),
                ("yvara_s3_gate_ready_total_days", None),
                ("yvara_s4_finance_unlocked", False),
                ("yvara_s4_finance_last_day", None),
                ("yvara_s4_donation_total", 0),
                ("yvara_s4_donation_highest_tier", 0),
                ("yvara_s4_favors_total", 0),
                ("yvara_s4_favor_highest_tier", 0),
                ("yvara_gifts_given", 0),
                ("yvara_s2_gifts_given", 0),
                ("yvara_observed_sessions", 0),
                ("yvara_observed_last_day", None),
                ("yvara_lesson_absorbed", False),
                ("yvara_leverage_financial", False),
                ("yvara_s3_gate_fired", False),
                ("yvara_s4_gate_fired", False),
                ("yvara_morning_after_done", False),
                ("yvara_evening_academy_last_day", None),
                ("yvara_evening_tier", 1),
                ("yvara_evening_variant_index", 0),
                ("yvara_academy_investment_tier", 0),
                ("yvara_academy_investment_total", 0),
                ("yvara_academy_investments_count", 0),
                ("yvara_s5_gate_fired", False),
                ("yvara_s6_gate_fired", False),
                ("yvara_ending_route", ""),
                ("yvara_is_worker", False),
                ("yvara_ending_done", False),
                ("yvara_academy_discount_active", False),
                ("yvara_lab_access", False),
                ("yvara_lab_gift_last_day", None),
                ("yvara_post_arc_talk_index", 0),
                ("yvara_arrangement_change_count", 0),
                ("yvara_good_word_count", 0),
                ("yvara_good_word_last_day", None),
                ("yvara_good_word_peak", False),
                # Lanista arc progression
                ("lanista_gender", ""),
                ("lanista_known_name", False),
                ("lanista_devotion", 0),
                ("lanista_dominion", 0),
                ("lanista_affection", 0),
                ("lanista_corruption", 0),
                ("lanista_stage", 1),
                ("lanista_visit_count", 0),
                ("lanista_last_talk_total_days", None),
                ("lanista_last_question_total_days", None),
                ("lanista_last_gift_total_days", None),
                ("lanista_gifts_given", 0),
                ("lanista_debt_finance_unlocked", False),
                ("lanista_debt_finance_last_day", None),
                ("lanista_donation_total", 0),
                ("lanista_donation_highest_tier", 0),
                ("lanista_favors_total", 0),
                ("lanista_favor_highest_tier", 0),
                ("lanista_card_tier", 0),
                ("lanista_card_last_day", None),
                ("lanista_pinup_unlocked", False),
                ("lanista_oilchains_unlocked", False),
                ("lanista_spectacle_unlocked", False),
                ("lanista_wager_last_day", None),
                ("lanista_s3_gate_fired", False),
                ("lanista_s4_gate_fired", False),
                ("lanista_morning_after_done", False),
                ("lanista_s5_gate_fired", False),
                ("lanista_s6_gate_fired", False),
                ("lanista_aftercrowd_last_day", None),
                ("lanista_aftercrowd_tier", 1),
                ("lanista_aftercrowd_variant_index", 0),
                ("lanista_ending_route", ""),
                ("lanista_ending_done", False),
                ("lanista_is_worker", False),
                ("lanista_ending_devotion", False),
                ("lanista_ending_dominion", False),
                ("lanista_ending_mixed", False),
                ("lanista_post_arc_talk_index", 0),
                ("lanista_arrangement_change_count", 0),
                # Arena / Laboratory progression and cooldowns
                ("arena_unlocked", False),
                ("arena_lanista_paid", False),
                ("arena_special_match_intro_done", False),
                ("last_special_match_total_days", None),
                ("last_special_match_worker_name", None),
                ("alchemy_unlocked", False),
                ("last_laboratory_use_total_days", None)
            ]:
                try:
                    if field_name in snap:
                        val = snap.get(field_name)
                        if val is not None or default_val is None:
                            setattr(store, field_name, val if val is not None else default_val)
                            applied_any = True
                            applied_fields.append(field_name)
                        elif not hasattr(store, field_name):
                            setattr(store, field_name, default_val)
                    else:
                        missing_fields.append(field_name)
                except Exception as e:
                    failed_fields.append(field_name)
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name}: {e}")

            # Apply arc list fields separately (must stay lists; deepcopy so the
            # store never aliases the transient snapshot dict)
            for field_name, default_val in [
                ("yvara_s1_talks_done", []),
                ("yvara_s1_remarks_done", []),
                ("yvara_s2_talks_done", []),
                ("yvara_s2_remarks_done", []),
                ("yvara_s3_talks_done", []),
                ("yvara_s3_remarks_done", []),
                ("yvara_s4_talks_done", []),
                ("yvara_s4_remarks_done", []),
                ("yvara_s5_talks_done", []),
                ("yvara_s5_remarks_done", []),
                ("yvara_s6_talks_done", []),
                ("lanista_s1_talks_done", []),
                ("lanista_s1_remarks_done", []),
                ("lanista_s2_talks_done", []),
                ("lanista_s2_remarks_done", []),
                ("lanista_s3_talks_done", []),
                ("lanista_s3_remarks_done", []),
                ("lanista_s4_talks_done", []),
                ("lanista_s4_remarks_done", []),
                ("lanista_s5_talks_done", []),
                ("lanista_s5_remarks_done", []),
                ("lanista_s6_talks_done", [])
            ]:
                try:
                    if field_name in snap:
                        val = _to_list(snap.get(field_name))
                        setattr(store, field_name, _cp.deepcopy(val) if val is not None else list(default_val))
                        applied_any = True
                        applied_fields.append(field_name)
                    elif not hasattr(store, field_name):
                        setattr(store, field_name, list(default_val))
                except Exception as e:
                    failed_fields.append(field_name)
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name}: {e}")
            
            # Inventory and shops
            for field_name, default_val, field_type in [
                ("manager_inventory", [], list),
                ("unlocked_shops", {}, dict),
                ("manager_interactions_today", 0, int)
            ]:
                try:
                    field_val = snap.get(field_name)
                    converted_val = None
                    
                    if field_type == list:
                        converted_val = _to_list(field_val)
                    elif field_type == dict:
                        converted_val = _to_dict(field_val)
                    elif field_type == int:
                        try:
                            converted_val = int(field_val) if field_val is not None else default_val
                        except (TypeError, ValueError):
                            converted_val = default_val
                    
                    if converted_val is not None:
                        restored_val = converted_val if field_type == int else _cp.deepcopy(converted_val)
                        
                        # CRITICAL: For manager_inventory, create new tuples to break reference sharing
                        # But preserve ALL items - don't skip anything
                        if field_name == "manager_inventory":
                            # Convert to list if needed
                            if not (hasattr(restored_val, "__iter__") and not isinstance(restored_val, str)):
                                restored_val = list(restored_val) if restored_val else []
                            
                            # Create new tuples to break references, but preserve everything
                            original_count = len(restored_val)
                            new_items = []
                            
                            for item in restored_val:
                                try:
                                    if (isinstance(item, tuple) or (hasattr(item, "__getitem__") and not isinstance(item, str) and not hasattr(item, "get"))) and len(item) >= 1:
                                        # Create new tuple from values
                                        item_id = item[0] if len(item) > 0 else ""
                                        quantity = item[1] if len(item) > 1 else 1
                                        equipped = item[2] if len(item) > 2 else False
                                        # Convert to primitives and create NEW tuple
                                        new_items.append((str(item_id) if item_id is not None else "", 
                                                         int(quantity) if quantity is not None else 1, 
                                                         bool(equipped) if equipped is not None else False))
                                    elif hasattr(item, "get"):
                                        # Convert dict to tuple
                                        item_id = item.get("item_id", "")
                                        quantity = item.get("quantity", 1)
                                        equipped = item.get("equipped", False)
                                        new_items.append((str(item_id) if item_id is not None else "", 
                                                         int(quantity) if quantity is not None else 1, 
                                                         bool(equipped) if equipped is not None else False))
                                    else:
                                        # Preserve as-is if it's not a recognized format
                                        new_items.append(item)
                                except (ValueError, TypeError, AttributeError) as e:
                                    # Preserve item even if conversion fails
                                    renpy.log(f"SNAPSHOT: WARNING - Could not normalize item {item}, preserving as-is (error: {e})")
                                    new_items.append(item)
                            
                            restored_val = new_items
                            renpy.log(f"SNAPSHOT: Applied manager_inventory: {len(restored_val)} items (from {original_count} in snapshot)")
                            if len(restored_val) > 0:
                                renpy.log(f"SNAPSHOT: First few items: {restored_val[:3]}")
                            else:
                                renpy.log(f"SNAPSHOT: WARNING - manager_inventory is EMPTY after restoration!")
                        
                        setattr(store, field_name, restored_val)
                        # CRITICAL: Force Ren'Py to recognize changes for manager_inventory
                        if field_name == "manager_inventory":
                            # Ensure it's a list (already normalized above, but double-check)
                            if not (hasattr(store.manager_inventory, "__iter__") and not isinstance(store.manager_inventory, str)):
                                store.manager_inventory = list(store.manager_inventory) if store.manager_inventory else []
                            renpy.store.manager_inventory = store.manager_inventory
                            _snap_log(f"SNAPSHOT: Final manager_inventory set with {len(store.manager_inventory)} items")
                        applied_any = True
                        applied_fields.append(field_name)
                    else:
                        missing_fields.append(field_name)
                        if field_name == "manager_inventory":
                            _snap_log(f"SNAPSHOT: WARNING - {field_name} is invalid (type: {type(field_val)}, is None: {field_val is None})")
                        if not hasattr(store, field_name):
                            setattr(store, field_name, default_val)
                except Exception as e:
                    failed_fields.append(field_name)
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name}: {e}")
                    import traceback
                    renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            store.game_initialized = True
            store.is_new_game = False
            
            # Verify what was actually restored and apply equipped item effects
            total_restored_items = 0
            total_equipped_items = 0
            for worker in store.workers:
                worker_name = worker.get("name", "Unknown")
                
                # Ensure inventory exists and convert lists to tuples for consistency
                if "inventory" not in worker:
                    worker["inventory"] = []
                else:
                    # Convert to list if it's not already (handles RevertableList, etc.)
                    converted_inv = _to_list(worker["inventory"])
                    worker["inventory"] = converted_inv if converted_inv is not None else []
                
                # Convert all inventory items from lists (JSON) to tuples (Python standard)
                converted_items = []
                for idx, item in enumerate(worker["inventory"]):
                    
                    # Try multiple ways to detect and convert the item
                    item_id = None
                    quantity = 1
                    equipped = False
                    converted = False
                    
                    # Method 1: Direct list/tuple check
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        item_id = item[0]
                        quantity = item[1] if len(item) > 1 else 1
                        equipped = item[2] if len(item) > 2 else False
                        converted = True
                    # Method 2: Check if it has sequence methods
                    elif hasattr(item, '__getitem__') and hasattr(item, '__len__'):
                        try:
                            if len(item) >= 2:
                                item_id = item[0]
                                quantity = item[1] if len(item) > 1 else 1
                                equipped = item[2] if len(item) > 2 else False
                                converted = True
                        except Exception as e:
                            pass
                    # Method 3: Try to convert to list first
                    else:
                        try:
                            item_list = list(item) if item else []
                            if len(item_list) >= 2:
                                item_id = item_list[0]
                                quantity = item_list[1] if len(item_list) > 1 else 1
                                equipped = item_list[2] if len(item_list) > 2 else False
                                converted = True
                        except Exception as e:
                            pass
                    
                    if converted and item_id is not None:
                        # Ensure equipped is boolean
                        if isinstance(equipped, bool):
                            is_equipped = equipped
                        elif isinstance(equipped, str):
                            is_equipped = equipped.lower() in ("true", "1", "yes")
                        elif isinstance(equipped, (int, float)):
                            is_equipped = bool(equipped) and equipped != 0
                        else:
                            is_equipped = False
                        
                        converted_tuple = (item_id, quantity, is_equipped)
                        converted_items.append(converted_tuple)
                    elif isinstance(item, tuple):
                        # Already a tuple, keep it
                        converted_items.append(item)
                    else:
                        # Failed to convert
                        _snap_log(f"SNAPSHOT: ERROR - Could not convert item {idx}: {item} (type: {type(item)})")
                        converted_items.append(item)  # Keep original as fallback
                
                worker["inventory"] = converted_items
                inv_count = len(worker["inventory"])
                if inv_count > 0:
                    total_restored_items += inv_count
                    # Log first few items to verify
                    items_preview = []
                    for item in worker["inventory"][:3]:
                        if isinstance(item, (list, tuple)) and len(item) > 0:
                            items_preview.append(f"{item[0]}(eq:{item[2] if len(item) > 2 else False})")
                        else:
                            items_preview.append(str(item))
                
                # Apply effects for all equipped items (now in tuple format)
                for idx, item in enumerate(worker["inventory"]):
                    try:
                        # Items should now be tuples: (item_id, quantity, equipped)
                        if isinstance(item, tuple) and len(item) >= 3:
                            item_id = item[0]
                            quantity = item[1]
                            equipped = item[2]
                            
                            
                            # Convert equipped to boolean if needed
                            if isinstance(equipped, bool):
                                is_equipped = equipped
                            elif isinstance(equipped, str):
                                is_equipped = equipped.lower() in ("true", "1", "yes")
                            elif isinstance(equipped, (int, float)):
                                is_equipped = bool(equipped) and equipped != 0
                            else:
                                is_equipped = False
                            
                            
                            if is_equipped:
                                try:
                                    if hasattr(store, 'apply_item_effects'):
                                        store.apply_item_effects(worker, item_id)
                                        total_equipped_items += 1
                                    else:
                                        _snap_err("SNAPSHOT: ERROR - apply_item_effects not found in store!")
                                except Exception as e:
                                    _snap_err(f"SNAPSHOT: Error applying effects for item '{item_id}': {e}")
                                    import traceback
                                    renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                        elif hasattr(item, "__getitem__") and not isinstance(item, (tuple, str)) and not hasattr(item, "get") and len(item) >= 3:
                            # Still a list, try to convert and apply
                            item_id = item[0]
                            quantity = item[1]
                            equipped = item[2]
                            if isinstance(equipped, bool):
                                is_equipped = equipped
                            elif isinstance(equipped, str):
                                is_equipped = equipped.lower() in ("true", "1", "yes")
                            elif isinstance(equipped, (int, float)):
                                is_equipped = bool(equipped) and equipped != 0
                            else:
                                is_equipped = False
                            
                            if is_equipped:
                                try:
                                    if hasattr(store, 'apply_item_effects'):
                                        store.apply_item_effects(worker, item_id)
                                        total_equipped_items += 1
                                    else:
                                        _snap_err("SNAPSHOT: ERROR - apply_item_effects not found in store!")
                                except Exception as e:
                                    _snap_err(f"SNAPSHOT: Error applying effects for item '{item_id}': {e}")
                                    import traceback
                                    renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                        else:
                            _snap_log(f"SNAPSHOT: Item {idx} invalid format: {item} (type: {type(item)}, len: {len(item) if hasattr(item, '__len__') else 'N/A'})")
                    except Exception as e:
                        _snap_err(f"SNAPSHOT: Error processing item {idx}: {e}, item={item}")
                        import traceback
                        renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            
            if total_restored_items > 0:
                pass
            
            # Ensure custom_names for all owned buildings
            for bname in store.owned_buildings:
                if bname not in store.custom_names:
                    store.custom_names[bname] = bname
            
            # VALIDATION: Skip validation - let rebuild handle everything
            # The rebuild section below will properly reconstruct assigned_servants from workers' assigned_building
            renpy.log("SNAPSHOT: Skipping validation, rebuild will handle it")
            
            # Restore worker jobs from autorest if they have recovered energy
            # This ensures workers who were put to rest by manager auto-rest get their jobs back
            # if they have sufficient energy after loading
            try:
                # Try multiple ways to access the function
                process_func = None
                if hasattr(store, 'process_manager_auto_rest'):
                    process_func = store.process_manager_auto_rest
                elif 'process_manager_auto_rest' in globals():
                    process_func = globals()['process_manager_auto_rest']
                else:
                    # Try to import from building_logic
                    try:
                        import sys
                        if 'building_logic' in sys.modules:
                            process_func = sys.modules['building_logic'].process_manager_auto_rest
                    except:
                        pass
                
                if process_func:
                    process_func(restore_only=True)
                else:
                    _snap_log("SNAPSHOT: WARNING - process_manager_auto_rest not found")
            except Exception as e:
                renpy.log(f"SNAPSHOT: Error running process_manager_auto_rest: {e}")
                import traceback
                renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            
            # Check tutorial objectives after restoring all state
            # This ensures objectives are properly detected if conditions are met
            # Wrapped in try-except to prevent breaking the load process
            try:
                if getattr(store, 'tutorial_active', False):
                    try:
                        import tutorial_system
                        if hasattr(tutorial_system, 'check_objective_completion'):
                            tutorial_system.check_objective_completion()
                    except Exception as e:
                        # Silently fail - don't break loading if objective check fails
                        pass
            except Exception:
                # Silently fail - don't break loading
                pass
            
            # CRITICAL: Rebuild assigned_servants from workers' assigned_building
            renpy.log("SNAPSHOT: === REBUILD SECTION REACHED ===")
            # This fixes the bug where buildings lose track of their workers after load
            # Done inline to avoid import/timing issues
            try:
                renpy.log("SNAPSHOT: Starting assigned_servants rebuild...")
                if hasattr(store, 'workers') and hasattr(store, 'available_buildings'):
                    # Step 1: Clear all assigned_servants
                    for bname, bdata in store.available_buildings.items():
                        if hasattr(bdata, "get"):
                            bdata["assigned_servants"] = []

                    # Step 2: Rebuild from workers' assigned_building
                    seen_per_building = {}
                    for worker in store.workers:
                        if not hasattr(worker, "get"):
                            continue
                        wname = worker.get("name")
                        if not wname:
                            continue
                        assigned = worker.get("assigned_building", "Unassigned")
                        if assigned == "Unassigned" or assigned not in store.available_buildings:
                            continue
                        # Dedupe by name
                        if assigned not in seen_per_building:
                            seen_per_building[assigned] = set()
                        if wname in seen_per_building[assigned]:
                            continue
                        seen_per_building[assigned].add(wname)
                        store.available_buildings[assigned]["assigned_servants"].append(worker)
                    
                    # Log results
                    total = sum(len(b.get("assigned_servants", [])) for b in store.available_buildings.values() if hasattr(b, "get"))
                    renpy.log(f"SNAPSHOT: Rebuilt assigned_servants - {total} workers across {len(seen_per_building)} buildings")
                else:
                    renpy.log("SNAPSHOT: WARNING - workers or available_buildings not found")
            except Exception as e:
                renpy.log(f"SNAPSHOT: WARNING - assigned_servants rebuild error: {e}")
            
            # Post-validation: verify at least one critical field was applied
            try:
                has_money = hasattr(store, 'money') and store.money is not None
                has_day = hasattr(store, 'current_day') and store.current_day is not None
                has_workers = hasattr(store, 'workers') and hasattr(store.workers, "__iter__") and not isinstance(store.workers, str)
                
                if not (has_money or has_day or has_workers):
                    renpy.log("SNAPSHOT: ERROR - Post-validation failed: no critical fields were applied")
                    return False
                
                # Log summary of applied/missing/failed fields (ALWAYS log, not just when there are issues)
                if missing_fields or failed_fields:
                    _snap_log(f"SNAPSHOT: Missing fields from save: {', '.join(missing_fields) if missing_fields else 'none'}")
                    if failed_fields:
                        _snap_err(f"SNAPSHOT: Failed to apply fields: {', '.join(failed_fields)}")
                    if applied_fields:
                        _snap_log(f"SNAPSHOT: Successfully applied fields: {', '.join(applied_fields[:10])}{'...' if len(applied_fields) > 10 else ''}")
                else:
                    _snap_log(f"SNAPSHOT: All fields applied successfully - {len(applied_fields)} fields: {', '.join(applied_fields[:15])}{'...' if len(applied_fields) > 15 else ''}")
            except Exception as validation_error:
                renpy.log(f"SNAPSHOT: ERROR - Post-validation exception: {validation_error}")
                # Still return True if we applied something
                return applied_any
            
            return True  # Success - at least some data was applied
        except Exception as e:
            renpy.log(f"SNAPSHOT: CRITICAL ERROR - apply_snapshot failed: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            # Return False to indicate failure - caller can try backup
            return False
    
    def _get_snapshot_file_path(slot_name):
        """Get the file path for a snapshot JSON file. Uses config.savedir so saves work on all platforms (e.g. macOS .app bundle where basedir may be read-only)."""
        saves_dir = getattr(config, "savedir", None) or os.path.join(config.basedir, "game", "saves")
        return os.path.join(saves_dir, f"snapshot_{slot_name}.json")
    
    def _get_backup_file_path(slot_name):
        """Get the file path for a backup snapshot JSON file."""
        saves_dir = getattr(config, "savedir", None) or os.path.join(config.basedir, "game", "saves")
        return os.path.join(saves_dir, f"snapshot_{slot_name}.json.bak")
    
    def _get_snapshot_file_path_for_reading(slot_name):
        """Path to use when loading: prefers config.savedir, falls back to legacy game/saves if file exists there (backwards compatibility)."""
        current_path = _get_snapshot_file_path(slot_name)
        if os.path.exists(current_path):
            return current_path
        legacy_path = os.path.join(config.basedir, "game", "saves", f"snapshot_{slot_name}.json")
        if os.path.exists(legacy_path):
            return legacy_path
        return current_path
    
    def _get_backup_file_path_for_reading(slot_name):
        """Path to use when loading backup: prefers config.savedir, falls back to legacy game/saves if file exists there."""
        current_path = _get_backup_file_path(slot_name)
        if os.path.exists(current_path):
            return current_path
        legacy_path = os.path.join(config.basedir, "game", "saves", f"snapshot_{slot_name}.json.bak")
        if os.path.exists(legacy_path):
            return legacy_path
        return current_path
    
    def _create_backup(filepath, slot_name):
        """Create a backup of the existing snapshot file before overwriting."""
        try:
            if os.path.exists(filepath):
                backup_path = _get_backup_file_path(slot_name)
                # Remove old backup if it exists
                if os.path.exists(backup_path):
                    try:
                        os.remove(backup_path)
                    except Exception as e:
                        renpy.log(f"SNAPSHOT: WARNING - Could not remove old backup: {e}")
                
                # Create new backup
                try:
                    shutil.copy2(filepath, backup_path)
                    if DEBUG_SNAPSHOT:
                        renpy.log(f"SNAPSHOT: Created backup for {slot_name}")
                except Exception as e:
                    renpy.log(f"SNAPSHOT: WARNING - Could not create backup for {slot_name}: {e}")
                    # Don't fail the save if backup fails - it's just a safety measure
        except Exception as e:
            renpy.log(f"SNAPSHOT: WARNING - Backup creation error (non-fatal): {e}")
            # Don't raise - backup is optional, save should continue
    
    def _write_snapshot_file(filepath, snap, slot_name=None):
        """Write snapshot to file atomically (using temp file then rename to prevent corruption)."""
        temp_filepath = None
        file_obj = None
        try:
            # Create temporary file in the same directory as the target file
            # This ensures atomic rename works (same filesystem)
            saves_dir = os.path.dirname(filepath)
            try:
                os.makedirs(saves_dir, exist_ok=True)
            except Exception as e:
                renpy.log(f"SNAPSHOT: WARNING - Could not ensure saves dir {saves_dir}: {e}")
            temp_fd, temp_filepath = tempfile.mkstemp(
                suffix='.json.tmp',
                dir=saves_dir,
                text=True
            )
            
            # Write to temporary file
            file_obj = os.fdopen(temp_fd, 'w', encoding='utf-8')
            try:
                try:
                    json.dump(snap, file_obj, indent=2, ensure_ascii=False)
                except (TypeError, ValueError) as json_err:
                    # Identify which top-level key(s) caused the failure so the next
                    # offender is easy to find without touching the happy path.
                    bad_keys = []
                    if isinstance(snap, dict):
                        for _k, _v in snap.items():
                            try:
                                json.dumps({_k: _v}, ensure_ascii=False)
                            except Exception as _probe_err:
                                bad_keys.append((_k, type(_v).__name__, str(_probe_err)[:120]))
                    renpy.log(f"SNAPSHOT: ERROR - json.dump failed: {json_err}")
                    if bad_keys:
                        renpy.log(f"SNAPSHOT: ERROR - non-serializable snapshot keys: {bad_keys}")
                    raise
                file_obj.flush()  # Ensure all data is written to buffer
                os.fsync(file_obj.fileno())  # Force write to disk
            finally:
                file_obj.close()
                file_obj = None
            
            # Small delay to ensure file system has written (Windows sometimes needs this)
            import time
            time.sleep(0.01)  # 10ms delay
            
            # Verify the temp file was written correctly by reading it back
            try:
                # Check file size first - if it's 0, something went wrong
                file_size = os.path.getsize(temp_filepath)
                if file_size == 0:
                    raise ValueError(f"Verification failed: temp file is empty (size: {file_size})")
                
                with open(temp_filepath, 'r', encoding='utf-8') as verify_file:
                    verify_data = json.load(verify_file)
                    # CRITICAL: Convert RevertableDict to dict if needed
                    verify_data = _to_dict(verify_data) if verify_data is not None else None
                    if verify_data is None or not hasattr(verify_data, "get"):
                        raise ValueError(f"Verification failed: temp file is not a dict (type: {type(verify_data)})")
                    if len(verify_data) == 0:
                        raise ValueError("Verification failed: temp file dict is empty")
                    # Check for critical fields
                    if "money" not in verify_data or "workers" not in verify_data:
                        raise ValueError(f"Verification failed: temp file missing critical fields. Keys: {list(verify_data.keys())[:10]}")
            except json.JSONDecodeError as json_error:
                renpy.log(f"SNAPSHOT: ERROR - Verification failed: JSON decode error: {json_error}")
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                raise ValueError(f"Verification failed: JSON decode error - {json_error}")
            except Exception as verify_error:
                renpy.log(f"SNAPSHOT: ERROR - Verification of temp file failed: {verify_error}")
                if os.path.exists(temp_filepath):
                    # Log file contents for debugging
                    try:
                        with open(temp_filepath, 'r', encoding='utf-8') as debug_file:
                            content = debug_file.read(500)  # First 500 chars
                            renpy.log(f"SNAPSHOT: DEBUG - Temp file content (first 500 chars): {content}")
                    except:
                        pass
                    os.remove(temp_filepath)
                raise
            
            # Create backup of existing file before overwriting (if it exists)
            if slot_name:
                _create_backup(filepath, slot_name)
            else:
                # Fallback: extract slot_name from filepath if not provided
                filename = os.path.basename(filepath)
                if filename.startswith("snapshot_") and filename.endswith(".json"):
                    slot_name = filename[9:-5]  # Remove "snapshot_" prefix and ".json" suffix
                    _create_backup(filepath, slot_name)
            
            # Atomic rename: replace destination file only if temp file is valid
            # On Windows, we need to remove destination first if it exists
            if os.path.exists(filepath):
                os.remove(filepath)
            os.rename(temp_filepath, filepath)
            temp_filepath = None  # Mark as successfully moved
            if DEBUG_SNAPSHOT:
                renpy.log(f"SNAPSHOT: Atomic save successful - {os.path.basename(filepath)}")
            
        except Exception as e:
            renpy.log(f"SNAPSHOT: ERROR - Failed to write snapshot atomically: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            # Clean up temp file if it still exists
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass
            raise  # Re-raise to let caller know save failed
        finally:
            # Ensure file is closed
            if file_obj and not file_obj.closed:
                try:
                    file_obj.close()
                except:
                    pass
            file_obj = None
            # Clean up temp file if rename failed
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass
    
    def snapshot_pre_save_slot(slot_num):
        """Save snapshot before saving to a specific slot."""
        try:
            success = True
            # Build slot name using the same logic as Ren'Py
            slot_name = _get_current_slot_name(slot_num)
            if not slot_name:
                # Fallback to previous logic if something went wrong
                page = getattr(persistent, "_file_page", 1)
                if page in ["auto", "quick"]:
                    slot_name = f"{page}-{slot_num}"
                else:
                    slot_name = f"{int(page)}-{slot_num}"

            # Warn if an existing snapshot file looks like a different slot/guid
            existing_path = _get_snapshot_file_path(slot_name)
            if os.path.exists(existing_path):
                existing_snap = _read_snapshot_file(existing_path)
                if existing_snap is None:
                    renpy.notify(f"Snapshot WARNING: existing file for {slot_name} is unreadable; overwriting.")
                elif hasattr(existing_snap, "get"):
                    existing_slot = existing_snap.get("snapshot_slot")
                    existing_guid = existing_snap.get("snapshot_guid")
                    expected_guid = _get_slot_guid(slot_name)
                    if existing_slot and existing_slot != slot_name:
                        renpy.notify(f"Snapshot WARNING: file for {slot_name} contains slot {existing_slot}; overwriting.")
                    if expected_guid and existing_guid and existing_guid != expected_guid:
                        renpy.notify(f"Snapshot WARNING: GUID mismatch for {slot_name}; overwriting.")
            
            # Update save_name so file slots show in-game date + money. FileSaveName(slot)
            # reads whatever was assigned to store.save_name at the moment of saving.
            try:
                _day = int(getattr(store, "current_day", 1) or 1)
                _month_idx = int(getattr(store, "current_month", 1) or 1) - 1
                _year = int(getattr(store, "current_year", 1) or 1)
                _money = int(getattr(store, "money", 0) or 0)
                _months = getattr(store, "month_names", []) or []
                _month_label = _months[_month_idx] if 0 <= _month_idx < len(_months) else f"M{_month_idx+1}"
                store.save_name = "Day {} — {} Y{}\n\n${:,}".format(_day, _month_label, _year, _money)
            except Exception as _sn_e:
                renpy.log(f"SNAPSHOT: save_name update failed (non-fatal): {_sn_e}")

            # Ensure assignments are consistent before snapshot
            _sync_building_assignments_from_workers()
            # Build and save snapshot BEFORE Ren'Py saves (captures current state in memory)
            snap = _build_snapshot()
            # Stamp slot identity to prevent cross-slot corruption
            slot_guid = _ensure_slot_guid(slot_name)
            snap["snapshot_slot"] = slot_name
            snap["snapshot_guid"] = slot_guid
            
            # Protection: Don't save empty snapshots (would cause game reset on load)
            if not snap or len(snap) == 0:
                renpy.log(f"SNAPSHOT: CRITICAL ERROR - Empty snapshot generated for slot {slot_name}! Aborting save to prevent game reset.")
                import traceback
                renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                return False  # Don't save empty snapshot
            
            # Additional validation: ensure critical fields exist
            if "money" not in snap or "workers" not in snap:
                renpy.log(f"SNAPSHOT: CRITICAL ERROR - Snapshot missing critical fields for slot {slot_name}! Keys: {list(snap.keys())[:10]}")
                return False  # Don't save invalid snapshot
            
            filepath = _get_snapshot_file_path(slot_name)
            
            # Try atomic save first, fallback to simple save if it fails
            try:
                _write_snapshot_file(filepath, snap, slot_name)
            except Exception as atomic_error:
                renpy.log(f"SNAPSHOT: WARNING - Atomic save failed, attempting fallback save: {atomic_error}")
                # Create backup before fallback save too
                _create_backup(filepath, slot_name)
                # Fallback: simple direct write (less safe but better than losing the save)
                try:
                    with open(filepath, 'w', encoding='utf-8') as fallback_file:
                        json.dump(snap, fallback_file, indent=2, ensure_ascii=False)
                    renpy.log(f"SNAPSHOT: Fallback save successful for {slot_name}")
                except Exception as fallback_error:
                    renpy.log(f"SNAPSHOT: CRITICAL ERROR - Both atomic and fallback save failed for {slot_name}: {fallback_error}")
                    import traceback
                    renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                    # Don't raise - let Ren'Py's native save system handle it
                    success = False
            
            # Log what was saved (only log if there's an issue, to avoid spam)
            # This helps debug if something goes wrong
            if DEBUG_SNAPSHOT:
                workers_with_items = sum(1 for w in snap.get("workers", []) if w.get("inventory") and len(w.get("inventory", [])) > 0)
                renpy.log(f"SNAPSHOT: Saved slot {slot_name} - money={snap.get('money')}, day={snap.get('current_day')}, workers={len(snap.get('workers', []))}, workers_with_items={workers_with_items}")
            return success
        except Exception as e:
            renpy.log(f"SNAPSHOT: pre_save_slot error: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            return False
    
    # Mark which slot is being loaded (called before FileAction)
    def snapshot_mark_load_slot(slot_num):
        """Mark which slot is being loaded so we can load the correct snapshot."""
        try:
            slot_name = _get_current_slot_name(slot_num)
            if not slot_name:
                page = getattr(persistent, "_file_page", 1)
                if page in ["auto", "quick"]:
                    slot_name = f"{page}-{slot_num}"
                else:
                    slot_name = f"{int(page)}-{slot_num}"
            # Store in persistent so it survives the load.
            # Keep both fields aligned to avoid first-load misses on some platforms.
            persistent._loading_slot = slot_name
            persistent._last_loaded_snapshot_slot = slot_name
        except Exception as e:
            renpy.log(f"SNAPSHOT: Error marking load slot: {e}")
    
    def snapshot_mark_load(slot_number):
        snapshot_mark_load_slot(slot_number)

    def snapshot_mark_load_name(slot_name):
        try:
            if slot_name:
                persistent._loading_slot = slot_name
                persistent._last_loaded_snapshot_slot = slot_name
        except Exception as e:
            renpy.log(f"SNAPSHOT: Error marking load slot by name: {e}")
    
    class SnapshotFileSave(renpy.store.Action):
        """Save snapshot first; only save if snapshot succeeds."""
        def __init__(self, slot_num, confirm=False):
            self.slot_num = slot_num
            self.confirm = confirm

        def __call__(self):
            try:
                if snapshot_pre_save_slot(self.slot_num):
                    return renpy.store.FileSave(self.slot_num, confirm=self.confirm)()
                renpy.notify(_("Save cancelled: snapshot stage failed (see log.txt)."))
            except Exception as e:
                import traceback
                renpy.log(f"SNAPSHOT: ERROR - SnapshotFileSave failed: {e}")
                renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                renpy.notify(_("Save cancelled: {} (see log.txt).").format(type(e).__name__))
        
        def get_sensitive(self):
            return renpy.store.FileSave(self.slot_num, confirm=self.confirm).get_sensitive()
        
        def get_selected(self):
            return renpy.store.FileSave(self.slot_num, confirm=self.confirm).get_selected()

    def _read_snapshot_file(filepath):
        """Read snapshot from file and ensure it's closed. Returns None only if file is completely unreadable."""
        file_obj = None
        try:
            if not os.path.exists(filepath):
                # File doesn't exist - this is normal for new saves, don't log as error
                return None
            
            file_obj = open(filepath, 'r', encoding='utf-8')
            data = json.load(file_obj)
            file_obj.close()
            file_obj = None
            
            # Debug: Log what we got (only if DEBUG_SNAPSHOT is enabled)
            if DEBUG_SNAPSHOT:
                renpy.log(f"SNAPSHOT: DEBUG - Loaded data type: {type(data)}, is dict: {hasattr(data, 'get')}")
                if hasattr(data, "get"):
                    renpy.log(f"SNAPSHOT: DEBUG - Dict has {len(data)} keys, first few: {list(data.keys())[:5]}")
            
            # Basic validation - must be a dict
            # Check if it's actually a dict (handle Ren'Py RevertableDict or other dict-like objects)
            if not hasattr(data, "get"):
                # Check if it's dict-like (has keys, get, etc.)
                if hasattr(data, 'keys') and hasattr(data, 'get') and hasattr(data, '__len__'):
                    # It's dict-like, convert to regular dict for safety
                    try:
                        data = dict(data)
                        if DEBUG_SNAPSHOT:
                            renpy.log(f"SNAPSHOT: DEBUG - Converted dict-like object to dict")
                    except Exception as conv_error:
                        renpy.log(f"SNAPSHOT: WARNING - Snapshot data is not a dict in {filepath}, type is {type(data)}, and conversion failed: {conv_error}")
                        if data is None or (hasattr(data, '__len__') and len(data) == 0):
                            return None
                        return data if data else None
                else:
                    renpy.log(f"SNAPSHOT: WARNING - Snapshot data is not a dict in {filepath}, type is {type(data)}, value repr: {repr(data)[:200]}")
                    # If it's None or empty, return None. Otherwise try to use it.
                    if data is None or (hasattr(data, '__len__') and len(data) == 0):
                        return None
                    # Try to return it anyway - _apply_snapshot will handle it with .get() defaults
                    return data if data else None
            
            return data
        except json.JSONDecodeError as e:
            # JSON is completely corrupt - this is a real error
            renpy.log(f"SNAPSHOT: JSON decode error in {filepath}: {e}")
            return None
        except Exception as e:
            # Other errors - log but try to be lenient
            renpy.log(f"SNAPSHOT: Error reading snapshot from {filepath}: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            return None
        finally:
            if file_obj and not file_obj.closed:
                file_obj.close()
            file_obj = None
    
    def _after_load_snapshot_callback():
        """Called by Ren'Py after loading. Apply snapshot to restore full game state.
        Strategy: Try complete load -> backup complete -> partial load -> backup partial -> defaults"""
        try:
            # Init-python globals get pickled into saves, so caches that listed
            # files at save time override the freshly-init'd None and hide any
            # mod files (workers/events/items/images) added after that save.
            # Reset before _apply_snapshot so migration and ensure_worker_defaults
            # see current files.
            try:
                store._renpy_file_list_cache = None
                store._worker_json_files_cache = None
                if hasattr(store, "invalidate_interactions_cache"):
                    store.invalidate_interactions_cache()
                else:
                    store._interactions_cache = None
                    store._interactions_cache_nsfw = None
                if hasattr(store, "_reset_media_file_caches"):
                    store._reset_media_file_caches()
                if hasattr(store, "image_selection_cache") and hasattr(store.image_selection_cache, "clear"):
                    store.image_selection_cache.clear()
                if hasattr(store, "_trait_def_cache") and hasattr(store._trait_def_cache, "clear"):
                    store._trait_def_cache.clear()
                if hasattr(store, "_trait_defs_cache") and hasattr(store._trait_defs_cache, "clear"):
                    store._trait_defs_cache.clear()
                if hasattr(store, "_item_defs_cache") and hasattr(store._item_defs_cache, "clear"):
                    store._item_defs_cache.clear()
                if hasattr(store, "refresh_traits_cache"):
                    try:
                        store.refresh_traits_cache(force=True)
                    except Exception:
                        pass
                _snap_log("SNAPSHOT: Invalidated data-listing caches (mod-aware load)")
            except Exception as _cache_e:
                renpy.log(f"SNAPSHOT: cache invalidation error (non-fatal): {_cache_e}")

            # Get the slot that was marked for loading
            slot_name = getattr(persistent, "_loading_slot", None)
            if not slot_name:
                slot_name = getattr(persistent, "_last_loaded_snapshot_slot", None)
            if not slot_name:
                # Fallback: use Ren'Py's loadname when slot wasn't marked (first-save edge case)
                try:
                    slot_name = getattr(renpy.loadsave, "loadname", None)
                    if slot_name:
                        persistent._loading_slot = slot_name
                        _snap_log(f"SNAPSHOT: Fallback to renpy.loadsave.loadname = {slot_name}")
                except Exception:
                    pass
            store._snapshot_load_alert = None
            store._snapshot_validation_error = None
            
            if slot_name:
                # Use "for_reading" so we find snapshots in legacy game/saves (backwards compatibility)
                filepath = _get_snapshot_file_path_for_reading(slot_name)
                backup_path = _get_backup_file_path_for_reading(slot_name)
                store._snapshot_load_alert = None
                
                # Strategy: Try multiple recovery methods in order
                main_snap = None
                backup_snap = None
                
                # Step 1: Read main save file
                if os.path.exists(filepath):
                    main_snap = _read_snapshot_file(filepath)
                    if main_snap is not None and not _snapshot_matches_slot(main_snap, slot_name):
                        main_snap = None
                        if store._snapshot_validation_error:
                            store._snapshot_load_alert = f"Snapshot MAIN invalid for {slot_name}: {store._snapshot_validation_error}"
                else:
                    store._snapshot_load_alert = f"Snapshot MAIN missing for {slot_name}. Load another slot and save to a new one."
                
                # Step 2: Read backup file (if main failed or for later use)
                if os.path.exists(backup_path):
                    backup_snap = _read_snapshot_file(backup_path)
                    if backup_snap is not None and not _snapshot_matches_slot(backup_snap, slot_name):
                        backup_snap = None
                        if store._snapshot_validation_error and not store._snapshot_load_alert:
                            store._snapshot_load_alert = f"Snapshot BACKUP invalid for {slot_name}: {store._snapshot_validation_error}"
                else:
                    if not store._snapshot_load_alert or "missing" not in store._snapshot_load_alert.lower():
                        store._snapshot_load_alert = f"Snapshot BACKUP missing for {slot_name}. If MAIN fails, do not save in this slot."
                
                # Step 3: Try complete load of main save
                if main_snap is not None:
                    success = _apply_snapshot(main_snap)
                    if success:
                        store._snapshot_load_alert = None
                        # Check if it was a complete load (no missing/failed fields)
                        # This is already logged by _apply_snapshot
                        if DEBUG_SNAPSHOT:
                            renpy.log(f"SNAPSHOT: Complete load successful from {slot_name}")
                        _upgrade_legacy_snapshot_file(filepath, main_snap, slot_name)
                        persistent._last_loaded_snapshot_slot = slot_name
                        persistent._loading_slot = None
                        return  # Success!
                    else:
                        renpy.log(f"SNAPSHOT: WARNING - Complete load of main save failed for {slot_name}, trying backup complete load...")
                        store._snapshot_load_alert = f"Snapshot MAIN failed for {slot_name}; trying BACKUP. Do not save in this slot if it fails."
                
                # Step 4: Try complete load of backup
                if backup_snap is not None:
                    success = _apply_snapshot(backup_snap)
                    if success:
                        renpy.log(f"SNAPSHOT: SUCCESS - Complete load from backup for {slot_name}")
                        store._snapshot_load_alert = f"Snapshot BACKUP loaded for {slot_name}. Save to a new slot."
                        _upgrade_legacy_snapshot_file(filepath, backup_snap, slot_name)
                        persistent._last_loaded_snapshot_slot = slot_name
                        persistent._loading_slot = None
                        return  # Success!
                    else:
                        renpy.log(f"SNAPSHOT: WARNING - Complete load of backup failed for {slot_name}, trying partial load of main save...")
                        store._snapshot_load_alert = f"Snapshot BACKUP failed for {slot_name}; trying partial recovery. Do not save in this slot."
                
                # Step 5: Try partial load of main save (apply what we can)
                if main_snap is not None:
                    renpy.log(f"SNAPSHOT: Attempting partial load of main save for {slot_name} (applying valid fields only)...")
                    success = _apply_snapshot(main_snap)  # _apply_snapshot already does partial application
                    if success:
                        renpy.log(f"SNAPSHOT: SUCCESS - Partial load from main save for {slot_name} (some fields may be missing)")
                        store._snapshot_load_alert = f"Snapshot MAIN partially loaded for {slot_name}. Save to a new slot."
                        _upgrade_legacy_snapshot_file(filepath, main_snap, slot_name)
                        persistent._last_loaded_snapshot_slot = slot_name
                        persistent._loading_slot = None
                        return  # Partial success!
                    else:
                        renpy.log(f"SNAPSHOT: WARNING - Partial load of main save also failed for {slot_name}, trying partial load of backup...")
                        store._snapshot_load_alert = f"Snapshot MAIN partial failed for {slot_name}; trying BACKUP. Do not save in this slot."
                
                # Step 6: Try partial load of backup (last resort)
                if backup_snap is not None:
                    renpy.log(f"SNAPSHOT: Attempting partial load of backup for {slot_name} (applying valid fields only)...")
                    success = _apply_snapshot(backup_snap)
                    if success:
                        renpy.log(f"SNAPSHOT: SUCCESS - Partial load from backup for {slot_name} (some fields may be missing)")
                        store._snapshot_load_alert = f"Snapshot BACKUP partially loaded for {slot_name}. Save to a new slot."
                        _upgrade_legacy_snapshot_file(filepath, backup_snap, slot_name)
                        persistent._last_loaded_snapshot_slot = slot_name
                        persistent._loading_slot = None
                        return  # Partial success!
                
                # Step 7: All attempts failed
                if main_snap is None and backup_snap is None:
                    renpy.log(f"SNAPSHOT: CRITICAL ERROR - No readable save files found for {slot_name} (main and backup both missing/unreadable). Game will use Ren'Py's default values.")
                    if not store._snapshot_load_alert:
                        store._snapshot_load_alert = f"Snapshot MAIN+BACKUP missing/unreadable for {slot_name}. Using defaults. Do not save in this slot."
                else:
                    renpy.log(f"SNAPSHOT: CRITICAL ERROR - All load attempts failed for {slot_name} (complete and partial for both main and backup). Game will use Ren'Py's default values.")
                    if not store._snapshot_load_alert:
                        store._snapshot_load_alert = f"Snapshot recovery failed for {slot_name}. Using defaults. Do not save in this slot."
                persistent._loading_slot = None
            else:
                renpy.log(f"SNAPSHOT: WARNING - No slot marked for loading. Game will use Ren'Py's default values.")
                store._snapshot_load_alert = "Snapshot load aborted: no slot marked. Return to menu and load another save."
        except Exception as e:
            renpy.log(f"SNAPSHOT: after_load callback error: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            persistent._loading_slot = None
    
    # Register after_load callback - use init -2 to run after other callbacks
    try:
        config.after_load_callbacks.append(_after_load_snapshot_callback)
    except Exception as e:
        renpy.log(f"SNAPSHOT: could not register after_load callback: {e}")

label after_load:
    $ _snap_log("AFTER_LOAD: label entered (snapshot should already be applied via callback)")
    python:
        if hasattr(store, "_snapshot_load_alert") and store._snapshot_load_alert:
            renpy.notify(store._snapshot_load_alert)
            store._snapshot_load_alert = None
    # Snapshot is applied via config.after_load_callbacks
    $ store.game_initialized = True
    $ store._just_loaded = True
    $ store.is_new_game = False
    
    # CRITICAL: Re-apply snapshot values that might have been overwritten by Ren'Py's native save system
    # This happens because Ren'Py restores 'default' variables AFTER our callbacks run
    python:
        try:
            # Get the slot that was loaded
            slot_name = getattr(persistent, "_loading_slot", None)
            if not slot_name:
                slot_name = getattr(persistent, "_last_loaded_snapshot_slot", None)
            if slot_name:
                # Use the _for_reading variant so saves still living in the
                # legacy location get the re-apply pass too.
                filepath = _get_snapshot_file_path_for_reading(slot_name)
                if os.path.exists(filepath):
                    snap = _read_snapshot_file(filepath)
                    if snap is not None and _snapshot_matches_slot(snap, slot_name):
                        # Re-apply critical fields that Ren'Py might have overwritten
                        # Manager inventory
                        manager_inv_val = snap.get("manager_inventory")
                        if manager_inv_val is not None:
                            # Convert to list if needed
                            if not (hasattr(manager_inv_val, "__iter__") and not isinstance(manager_inv_val, str)):
                                manager_inv_val = list(manager_inv_val) if manager_inv_val else []
                            
                            current_inv = getattr(store, 'manager_inventory', [])
                            # Always restore if snapshot has items OR if current is empty but snapshot has data
                            if len(manager_inv_val) > 0 or (len(current_inv) == 0 and manager_inv_val is not None):
                                if len(current_inv) != len(manager_inv_val):
                                    _snap_log(f"AFTER_LOAD: manager_inventory mismatch - current: {len(current_inv)}, snapshot: {len(manager_inv_val)}. Restoring from snapshot.")
                                else:
                                    _snap_log(f"AFTER_LOAD: manager_inventory lengths match ({len(manager_inv_val)}), but restoring anyway to ensure correct format.")
                                # CRITICAL: Create new tuples to break reference sharing
                                # But preserve ALL items - don't skip anything
                                original_count = len(manager_inv_val)
                                new_items = []
                                
                                for item in manager_inv_val:
                                    try:
                                        if (isinstance(item, tuple) or (hasattr(item, "__getitem__") and not isinstance(item, str) and not hasattr(item, "get"))) and len(item) >= 1:
                                            # Create new tuple from values
                                            item_id = item[0] if len(item) > 0 else ""
                                            quantity = item[1] if len(item) > 1 else 1
                                            equipped = item[2] if len(item) > 2 else False
                                            # Convert to primitives and create NEW tuple - preserve even if item_id is empty
                                            new_items.append((str(item_id) if item_id is not None else "", 
                                                             int(quantity) if quantity is not None else 1, 
                                                             bool(equipped) if equipped is not None else False))
                                        elif hasattr(item, "get"):
                                            # Convert dict to tuple
                                            item_id = item.get("item_id", "")
                                            quantity = item.get("quantity", 1)
                                            equipped = item.get("equipped", False)
                                            new_items.append((str(item_id) if item_id is not None else "", 
                                                             int(quantity) if quantity is not None else 1, 
                                                             bool(equipped) if equipped is not None else False))
                                        else:
                                            # Preserve as-is if it's not a recognized format
                                            new_items.append(item)
                                    except (ValueError, TypeError, AttributeError) as e:
                                        # Preserve item even if conversion fails
                                        _snap_log(f"AFTER_LOAD: WARNING - Could not normalize item {item}, preserving as-is (error: {e})")
                                        new_items.append(item)
                                
                                store.manager_inventory = new_items
                                renpy.store.manager_inventory = store.manager_inventory
                                _snap_log(f"AFTER_LOAD: Restored manager_inventory with {len(new_items)} items (from {original_count} in snapshot)")
                                if len(new_items) > 0:
                                    _snap_log(f"AFTER_LOAD: First few restored items: {new_items[:3]}")
                                else:
                                    _snap_log("AFTER_LOAD: WARNING - manager_inventory is EMPTY after restoration!")
                        
                        # Available buildings (contains servant_jobs)
                        buildings_val = snap.get("available_buildings")
                        if buildings_val is not None and hasattr(buildings_val, "get"):
                            current_buildings = getattr(store, 'available_buildings', {})
                            # Check if servant_jobs are missing
                            needs_restore = False
                            for bname, building in buildings_val.items():
                                if hasattr(building, "get"):
                                    saved_jobs = building.get("servant_jobs", {})
                                    current_building = current_buildings.get(bname)
                                    if hasattr(current_building, "get"):
                                        current_jobs = current_building.get("servant_jobs", {})
                                        if len(saved_jobs) != len(current_jobs):
                                            needs_restore = True
                                            break
                            
                            if needs_restore:
                                _snap_log("AFTER_LOAD: WARNING - available_buildings/servant_jobs were overwritten! Restoring from snapshot")
                                store.available_buildings = _cp.deepcopy(buildings_val)
                                renpy.store.available_buildings = store.available_buildings
                                # Re-relink assigned_servants after restoring buildings
                                relink_func = None
                                if hasattr(store, '_relink_assigned_servants_to_store_workers'):
                                    relink_func = store._relink_assigned_servants_to_store_workers
                                elif hasattr(renpy.store, '_relink_assigned_servants_to_store_workers'):
                                    relink_func = renpy.store._relink_assigned_servants_to_store_workers
                                if relink_func:
                                    relink_func()

                        # Re-apply Arena/Laboratory cooldown/progression flags in case
                        # Ren'Py default restoration overwrote them after callback order.
                        for _field_name in [
                            "arena_unlocked",
                            "arena_lanista_paid",
                            "arena_special_match_intro_done",
                            "last_special_match_total_days",
                            "last_special_match_worker_name",
                            "alchemy_unlocked",
                            "last_laboratory_use_total_days",
                        ]:
                            if _field_name in snap:
                                _val = snap.get(_field_name)
                                setattr(store, _field_name, _val)
                                setattr(renpy.store, _field_name, _val)

                        # Re-apply Yvara progression/state from snapshot to avoid
                        # losing VN progression when Ren'Py default restoration
                        # runs after callback order in some loads.
                        _yvara_scalar_fields = [
                            "yvara_known_name",
                            "yvara_devotion",
                            "yvara_dominion",
                            "yvara_affection",
                            "yvara_stage",
                            "yvara_visit_count",
                            "yvara_last_question_total_days",
                            "yvara_last_gift_total_days",
                            "yvara_last_talk_total_days",
                            "yvara_s3_gate_ready",
                            "yvara_s3_gate_ready_total_days",
                            "yvara_s4_finance_unlocked",
                            "yvara_s4_finance_last_day",
                            "yvara_s4_donation_total",
                            "yvara_s4_donation_highest_tier",
                            "yvara_s4_favors_total",
                            "yvara_s4_favor_highest_tier",
                            "yvara_gifts_given",
                            "yvara_s2_gifts_given",
                            "yvara_observed_sessions",
                            "yvara_observed_last_day",
                            "yvara_lesson_absorbed",
                            "yvara_leverage_financial",
                            "yvara_s3_gate_fired",
                            "yvara_s4_gate_fired",
                            "yvara_morning_after_done",
                            "yvara_evening_academy_last_day",
                            "yvara_evening_tier",
                            "yvara_evening_variant_index",
                            "yvara_academy_investment_tier",
                            "yvara_academy_investment_total",
                            "yvara_academy_investments_count",
                            "yvara_s5_gate_fired",
                            "yvara_s6_gate_fired",
                            "yvara_ending_route",
                            "yvara_is_worker",
                            "yvara_ending_done",
                            "yvara_academy_discount_active",
                            "yvara_lab_access",
                            "yvara_lab_gift_last_day",
                            "yvara_post_arc_talk_index",
                            "yvara_arrangement_change_count",
                            "yvara_good_word_count",
                            "yvara_good_word_last_day",
                            "yvara_good_word_peak",
                        ]
                        _lanista_scalar_fields = [
                            "lanista_gender",
                            "lanista_known_name",
                            "lanista_devotion",
                            "lanista_dominion",
                            "lanista_affection",
                            "lanista_corruption",
                            "lanista_stage",
                            "lanista_visit_count",
                            "lanista_last_talk_total_days",
                            "lanista_last_question_total_days",
                            "lanista_last_gift_total_days",
                            "lanista_gifts_given",
                            "lanista_debt_finance_unlocked",
                            "lanista_debt_finance_last_day",
                            "lanista_donation_total",
                            "lanista_donation_highest_tier",
                            "lanista_favors_total",
                            "lanista_favor_highest_tier",
                            "lanista_card_tier",
                            "lanista_card_last_day",
                            "lanista_pinup_unlocked",
                            "lanista_oilchains_unlocked",
                            "lanista_spectacle_unlocked",
                            "lanista_wager_last_day",
                            "lanista_s3_gate_fired",
                            "lanista_s4_gate_fired",
                            "lanista_morning_after_done",
                            "lanista_s5_gate_fired",
                            "lanista_s6_gate_fired",
                            "lanista_aftercrowd_last_day",
                            "lanista_aftercrowd_tier",
                            "lanista_aftercrowd_variant_index",
                            "lanista_ending_route",
                            "lanista_ending_done",
                            "lanista_is_worker",
                            "lanista_ending_devotion",
                            "lanista_ending_dominion",
                            "lanista_ending_mixed",
                            "lanista_post_arc_talk_index",
                            "lanista_arrangement_change_count",
                        ]
                        _yvara_list_fields = [
                            "yvara_s1_talks_done",
                            "yvara_s1_remarks_done",
                            "yvara_s2_talks_done",
                            "yvara_s2_remarks_done",
                            "yvara_s3_talks_done",
                            "yvara_s3_remarks_done",
                            "yvara_s4_talks_done",
                            "yvara_s4_remarks_done",
                            "yvara_s5_talks_done",
                            "yvara_s5_remarks_done",
                            "yvara_s6_talks_done",
                        ]
                        _lanista_list_fields = [
                            "lanista_s1_talks_done",
                            "lanista_s1_remarks_done",
                            "lanista_s2_talks_done",
                            "lanista_s2_remarks_done",
                            "lanista_s3_talks_done",
                            "lanista_s3_remarks_done",
                            "lanista_s4_talks_done",
                            "lanista_s4_remarks_done",
                            "lanista_s5_talks_done",
                            "lanista_s5_remarks_done",
                            "lanista_s6_talks_done",
                        ]

                        for _field_name in _yvara_scalar_fields:
                            if _field_name in snap:
                                _val = snap.get(_field_name)
                                setattr(store, _field_name, _val)
                                setattr(renpy.store, _field_name, _val)

                        for _field_name in _yvara_list_fields:
                            if _field_name in snap:
                                _src = snap.get(_field_name)
                                _val = _cp.deepcopy(_to_list(_src) or [])
                                setattr(store, _field_name, _val)
                                setattr(renpy.store, _field_name, _cp.deepcopy(_val))

                        for _field_name in _lanista_scalar_fields:
                            if _field_name in snap:
                                _val = snap.get(_field_name)
                                setattr(store, _field_name, _val)
                                setattr(renpy.store, _field_name, _val)

                        for _field_name in _lanista_list_fields:
                            if _field_name in snap:
                                _src = snap.get(_field_name)
                                _val = _cp.deepcopy(_to_list(_src) or [])
                                setattr(store, _field_name, _val)
                                setattr(renpy.store, _field_name, _cp.deepcopy(_val))

            # Log current state
            _snap_log(f"AFTER_LOAD: store.workers has {len(store.workers)} workers, renpy.store.workers has {len(renpy.store.workers)} workers")
            
            # CRITICAL: Ensure renpy.store.workers matches store.workers
            # This prevents Ren'Py from overwriting our restored workers
            if len(store.workers) != len(renpy.store.workers):
                _snap_log(f"AFTER_LOAD: WARNING - Worker count mismatch! store.workers={len(store.workers)}, renpy.store.workers={len(renpy.store.workers)}")
                _snap_log("AFTER_LOAD: Forcing renpy.store.workers to match store.workers")
                renpy.store.workers = store.workers
            
            # Try to access the function from store
            relink_func = None
            if hasattr(store, '_relink_assigned_servants_to_store_workers'):
                relink_func = store._relink_assigned_servants_to_store_workers
            elif hasattr(renpy.store, '_relink_assigned_servants_to_store_workers'):
                relink_func = renpy.store._relink_assigned_servants_to_store_workers
            
            if relink_func:
                relink_func()
                _snap_log("AFTER_LOAD: Re-relinked assigned_servants to ensure correct worker references")
            else:
                _snap_log("AFTER_LOAD: WARNING - _relink_assigned_servants_to_store_workers not found (non-critical)")
            
            _sync_building_assignments_from_workers()
            
            # Drop servant_jobs that are invalid for the building type (stale id after moves / data changes).
            try:
                san = getattr(store, "sanitize_invalid_servant_job", None)
                if callable(san):
                    for w in list(getattr(store, "workers", []) or []):
                        if not hasattr(w, "get"):
                            continue
                        bname = w.get("assigned_building", "Unassigned")
                        if bname == "Unassigned":
                            continue
                        b = (getattr(store, "available_buildings", {}) or {}).get(bname)
                        if hasattr(b, "get"):
                            san(b, w.get("name"), w)
            except Exception as e:
                renpy.log(f"AFTER_LOAD: sanitize_invalid_servant_job sweep error: {e}")
            
            # Log worker names to verify they're correct
            worker_names = [w.get("name", "Unknown") for w in store.workers]
            _snap_log(f"AFTER_LOAD: Final check - {len(store.workers)} workers: {', '.join(worker_names[:10])}{'...' if len(worker_names) > 10 else ''}")
        except Exception as e:
            renpy.log(f"AFTER_LOAD: Error in final worker verification: {e}")
            import traceback
            renpy.log(f"AFTER_LOAD: traceback: {traceback.format_exc()}")
        
        # Validate objective 12 items if player is on that objective
        try:
            current_obj = getattr(store, 'current_objective', 0)
            if current_obj == 12:
                renpy.log("AFTER_LOAD: Player is on objective 12, validating items...")
                if hasattr(store, 'validate_objective_12_items'):
                    store.validate_objective_12_items()
                else:
                    renpy.log("AFTER_LOAD: WARNING - validate_objective_12_items function not found")
        except Exception as e:
            renpy.log(f"AFTER_LOAD: Error validating objective 12 items: {e}")
    
    # Clean up load state
    python:
        persistent._last_loaded_snapshot_slot = None

    # Resume the ambient BGM on load explicitly, so it does not depend on the
    # tavern_screen routing below (belt-and-suspenders per audit note #1).
    python:
        try:
            _ebp = getattr(store, "ensure_bgm_playing", None)
            if callable(_ebp):
                _ebp()
        except Exception as e:
            renpy.log(f"AFTER_LOAD: ensure_bgm_playing error: {e}")

    show screen esc_key_handler
    jump tavern_screen
