default snapshot_transaction_id = None

init -2 python:
    DEBUG_SNAPSHOT = False
    # Single source of truth for the sidecar schema version this build writes.
    SNAPSHOT_CURRENT_VERSION = 3
    SNAPSHOT_KEEP_LIMIT_PER_VERSION = 5
    SNAPSHOT_LOCK_STALE_SECONDS = 600

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
    import hashlib
    import time
    import uuid
    import traceback

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

    def _snapshot_slot_lock_path(slot_name):
        return _get_snapshot_file_path(slot_name) + ".lock"

    def _acquire_snapshot_slot_lock(slot_name, stale_seconds=SNAPSHOT_LOCK_STALE_SECONDS):
        """Acquire an exclusive cross-process lock file for one save slot.

        Returns ``(path, token)`` on success, or ``None`` while another live
        writer owns the slot. Locks older than ``stale_seconds`` are reclaimed.
        """
        lock_path = _snapshot_slot_lock_path(slot_name)
        token = str(uuid.uuid4())
        payload = {"token": token, "pid": os.getpid(), "created": time.time()}
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)

        for _attempt in range(2):
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(lock_path) <= stale_seconds:
                        return None
                    os.remove(lock_path)
                    renpy.log(f"SNAPSHOT: WARNING - reclaimed stale slot lock for {slot_name}")
                    continue
                except FileNotFoundError:
                    continue
                except Exception as error:
                    renpy.log(f"SNAPSHOT: WARNING - could not inspect slot lock for {slot_name}: {error}")
                    return None
            except Exception as error:
                renpy.log(f"SNAPSHOT: ERROR - could not acquire slot lock for {slot_name}: {error}")
                return None

            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle)
                    handle.flush()
                    os.fsync(handle.fileno())
                return (lock_path, token)
            except Exception as error:
                try:
                    os.close(fd)
                except Exception:
                    pass
                try:
                    os.remove(lock_path)
                except Exception:
                    pass
                renpy.log(f"SNAPSHOT: ERROR - could not initialize slot lock for {slot_name}: {error}")
                return None
        return None

    def _release_snapshot_slot_lock(lock_token):
        """Release a lock only when its on-disk ownership token still matches."""
        if not lock_token or not isinstance(lock_token, (list, tuple)) or len(lock_token) != 2:
            return False
        lock_path, token = lock_token
        try:
            with open(lock_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not hasattr(payload, "get") or payload.get("token") != token:
                return False
            os.remove(lock_path)
            return True
        except FileNotFoundError:
            return True
        except Exception as error:
            renpy.log(f"SNAPSHOT: WARNING - could not release slot lock {lock_path}: {error}")
            return False

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

            _delete_future_snapshot_keeps(filepath)

            # Drop the slot GUID with the files: a residual GUID would block
            # adopting a save later copied into this slot from another device.
            try:
                guids = getattr(persistent, "_slot_guids", None)
                if guids and slot_name in guids:
                    del guids[slot_name]
            except Exception as e:
                renpy.log(f"SNAPSHOT: WARNING - Could not drop GUID for {slot_name}: {e}")
        except Exception as e:
            renpy.log(f"SNAPSHOT: ERROR - snapshot_pre_delete_slot failed: {e}")

    def snapshot_delete_sidecars(slot_num):
        """Return an Action that wipes MAIN/BACKUP/tmp sidecars for this slot.

        Used inside the confirmed delete action only, so a cancelled delete
        leaves native save + sidecars untouched.
        """
        return renpy.store.Function(snapshot_pre_delete_slot, slot_num)

    def snapshot_slot_has_any_data(slot_num):
        """True when a slot has native or recoverable sidecar data."""
        slot_name = _get_current_slot_name(slot_num)
        if not slot_name:
            return False
        try:
            if renpy.can_load(slot_name):
                return True
        except Exception:
            pass
        filepath = _get_snapshot_file_path(slot_name)
        if os.path.exists(filepath) or os.path.exists(_get_backup_file_path(slot_name)):
            return True
        return bool(_future_snapshot_keep_paths(filepath))

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

            native_transaction_id = getattr(store, "snapshot_transaction_id", None)
            snapshot_transaction_id = snap.get("snapshot_transaction_id")
            if (native_transaction_id or snapshot_transaction_id) and snapshot_transaction_id != native_transaction_id:
                store._snapshot_validation_error = f"Transaction mismatch for slot {slot_name}. Trying the paired backup."
                _snap_err(
                    f"SNAPSHOT: ERROR - Transaction mismatch for {slot_name} "
                    f"(native={native_transaction_id}, snapshot={snapshot_transaction_id})."
                )
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
                "snapshot_version": 3,
                "money": int(store.money) if hasattr(store, "money") else 6000,
                "current_day": getattr(store, "current_day", 1),
                "current_month": getattr(store, "current_month", 1),
                "current_year": getattr(store, "current_year", 1),
                "workers": workers_copy,
                "available_workers": _cp.deepcopy(_to_list(getattr(store, "available_workers", [])) or []),
                "available_buildings": _cp.deepcopy(getattr(store, "available_buildings", {})),
                "owned_buildings": _cp.deepcopy(getattr(store, "owned_buildings", [])),
                "map_button_buildings": _cp.deepcopy(getattr(store, "map_button_buildings", {})),
                "assignment_presets": _cp.deepcopy(getattr(store, "assignment_presets", {}) or {}),
                "franchise_holdings": _cp.deepcopy(getattr(store, "franchise_holdings", {}) or {}),
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
                # Mode active when the save was made; rollback_enabled=False means the
                # defaulted store var does not survive load, so it travels here.
                "save_nsfw_mode": bool(getattr(persistent, "nsfw_enabled", False)),
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
                "yvara_post_arc_talks_seen": _cp.deepcopy(_to_list(_safe_getattr(store, "yvara_post_arc_talks_seen", [])) or []),
                # Lanista arc progression
                "lanista_gender": _safe_getattr(store, "lanista_gender", ""),
                "lanista_name": _safe_getattr(store, "lanista_name", "The Lanista"),
                "lanista_known_name": _safe_getattr(store, "lanista_known_name", False),
                "lanista_devotion": _safe_getattr(store, "lanista_devotion", 0),
                "lanista_dominion": _safe_getattr(store, "lanista_dominion", 0),
                "lanista_affection": _safe_getattr(store, "lanista_affection", 0),
                "lanista_corruption": _safe_getattr(store, "lanista_corruption", 0),
                "lanista_stage": _safe_getattr(store, "lanista_stage", 1),
                "lanista_visit_count": _safe_getattr(store, "lanista_visit_count", 0),
                "lanista_night_visit_total_days": _safe_getattr(store, "lanista_night_visit_total_days", None),
                "lanista_gate_closed_total_days": _safe_getattr(store, "lanista_gate_closed_total_days", None),
                "lanista_last_talk_total_days": _safe_getattr(store, "lanista_last_talk_total_days", None),
                "lanista_filler_talk_index": _safe_getattr(store, "lanista_filler_talk_index", 0),
                "lanista_last_story_total_days": _safe_getattr(store, "lanista_last_story_total_days", None),
                "lanista_last_question_total_days": _safe_getattr(store, "lanista_last_question_total_days", None),
                "lanista_last_gift_total_days": _safe_getattr(store, "lanista_last_gift_total_days", None),
                "lanista_gifts_given": _safe_getattr(store, "lanista_gifts_given", 0),
                "lanista_wager_intro_done": _safe_getattr(store, "lanista_wager_intro_done", False),
                "lanista_debt_finance_unlocked": _safe_getattr(store, "lanista_debt_finance_unlocked", False),
                "lanista_debt_finance_last_day": _safe_getattr(store, "lanista_debt_finance_last_day", None),
                "lanista_donation_total": _safe_getattr(store, "lanista_donation_total", 0),
                "lanista_donation_highest_tier": _safe_getattr(store, "lanista_donation_highest_tier", 0),
                "lanista_favors_total": _safe_getattr(store, "lanista_favors_total", 0),
                "lanista_favor_highest_tier": _safe_getattr(store, "lanista_favor_highest_tier", 0),
                "lanista_favor_balance": _safe_getattr(store, "lanista_favor_balance", 0),
                "lanista_favors_collected": _safe_getattr(store, "lanista_favors_collected", 0),
                "lanista_collect_last_day": _safe_getattr(store, "lanista_collect_last_day", None),
                "lanista_monthly_purse_last_month": _safe_getattr(store, "lanista_monthly_purse_last_month", None),
                "lanista_spectacle_arc_step": _safe_getattr(store, "lanista_spectacle_arc_step", 0),
                "lanista_spectacle_arc_last_day": _safe_getattr(store, "lanista_spectacle_arc_last_day", None),
                "lanista_arena_program_tier": _safe_getattr(store, "lanista_arena_program_tier", 0),
                "lanista_arena_program_last_day": _safe_getattr(store, "lanista_arena_program_last_day", None),
                "lanista_card_tier": _safe_getattr(store, "lanista_card_tier", 0),
                "lanista_card_last_day": _safe_getattr(store, "lanista_card_last_day", None),
                "lanista_pinup_unlocked": _safe_getattr(store, "lanista_pinup_unlocked", False),
                "lanista_oilchains_unlocked": _safe_getattr(store, "lanista_oilchains_unlocked", False),
                "lanista_spectacle_unlocked": _safe_getattr(store, "lanista_spectacle_unlocked", False),
                "lanista_spectacle_pitch_done": _safe_getattr(store, "lanista_spectacle_pitch_done", False),
                "lanista_wager_last_day": _safe_getattr(store, "lanista_wager_last_day", None),
                "lanista_wager_loss_streak": _safe_getattr(store, "lanista_wager_loss_streak", 0),
                "lanista_s2_gate_fired": _safe_getattr(store, "lanista_s2_gate_fired", False),
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
                "lanista_weekly_cut_last_day": _safe_getattr(store, "lanista_weekly_cut_last_day", None),
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
                "lanista_fillers_seen": _cp.deepcopy(_to_list(_safe_getattr(store, "lanista_fillers_seen", [])) or []),
                "lanista_remark_choices": _cp.deepcopy(_to_dict(_safe_getattr(store, "lanista_remark_choices", {})) or {}),
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
                "last_arena_worker_name": _safe_getattr(store, "last_arena_worker_name", None),
                "arena_trial_completed": _safe_getattr(store, "arena_trial_completed", None),
                "arena_successor_met": _safe_getattr(store, "arena_successor_met", False),
                "arena_lanista_feedback_pending": _cp.deepcopy(_safe_getattr(store, "arena_lanista_feedback_pending", None)),
                "alchemy_unlocked": _safe_getattr(store, "alchemy_unlocked", False),
                "last_laboratory_use_total_days": _safe_getattr(store, "last_laboratory_use_total_days", None),
                "last_alchemy_worker_name": _safe_getattr(store, "last_alchemy_worker_name", None),
                # One-time manager level awards (Master's Elixir / first Arena crown)
                "elixir_award_granted": _safe_getattr(store, "elixir_award_granted", False),
                "elixir_intro_done": _safe_getattr(store, "elixir_intro_done", False),
                "arena_champion_award_granted": _safe_getattr(store, "arena_champion_award_granted", False)
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
        current_version = SNAPSHOT_CURRENT_VERSION

        # Future version: this binary cannot know the format. Warn honestly and
        # return the snapshot untouched - no migration, no version bump, no
        # fields added or removed.
        if version > current_version:
            renpy.log(
                f"SNAPSHOT: WARNING - Snapshot version {version} is newer than "
                f"the supported version {current_version}. Applying as-is without "
                f"migration; some newer fields may be ignored."
            )
            return snap


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

        if version == 2:
            # v2 -> v3: repair Lanista workers recruited after the v2 sweep.
            # The old endings overwrote the JSON folder before template_id was
            # stamped, so both fields can contain the same invalid legacy value.
            by_name, by_folder = _build_json_template_index()
            if by_name is None:
                renpy.log("MIGRATION v3: JSON templates unavailable — aborting migration, will retry on next load")
                return snap

            s1, f1, sk1 = _migrate_worker_folders_inplace(snap.get("workers") or [], by_name, by_folder, label=" [workers]")
            s2, f2, sk2 = _migrate_worker_folders_inplace(snap.get("available_workers") or [], by_name, by_folder, label=" [available]")
            renpy.log(
                f"MIGRATION v3: stamped template_id on {s1 + s2} workers, fixed folder on {f1 + f2}, "
                f"skipped {sk1 + sk2} ambiguous"
            )
            snap["snapshot_version"] = 3
            version = 3

        renpy.log(f"SNAPSHOT: MIGRATION - Migration complete, snapshot now at version {snap.get('snapshot_version', current_version)}")
        return snap
    
    def _apply_snapshot(snap):
        """Apply one snapshot and reject it if any tracked field fails."""
        applied_any = False
        applied_critical = False
        applied_fields = []
        missing_fields = []
        failed_fields = []
        snapshot_state = None
        snapshot_absent_fields = set()

        def _rollback_snapshot_state():
            if snapshot_state is None:
                return True
            rollback_errors = []
            for field_name, previous_value in snapshot_state.items():
                try:
                    setattr(store, field_name, _cp.deepcopy(previous_value))
                except Exception as rollback_error:
                    rollback_errors.append(f"{field_name}: {rollback_error}")
            for field_name in snapshot_absent_fields:
                try:
                    if hasattr(store, field_name):
                        delattr(store, field_name)
                except Exception as rollback_error:
                    rollback_errors.append(f"{field_name}: {rollback_error}")
            for alias_name in ("workers", "available_workers", "manager_inventory"):
                try:
                    if hasattr(store, alias_name):
                        setattr(renpy.store, alias_name, getattr(store, alias_name))
                except Exception as rollback_error:
                    rollback_errors.append(f"renpy.store.{alias_name}: {rollback_error}")
            if rollback_errors:
                renpy.log(
                    "SNAPSHOT: CRITICAL ERROR - rollback after failed apply was incomplete: "
                    + "; ".join(rollback_errors)
                )
                return False
            renpy.log("SNAPSHOT: Rolled back all snapshot fields after failed apply")
            return True
        
        try:
            if not snap:
                renpy.log("SNAPSHOT: WARNING - Empty snapshot provided to _apply_snapshot")
                return False
            
            # Pre-validation: ensure snapshot is a dict
            if not hasattr(snap, "get"):
                renpy.log(f"SNAPSHOT: ERROR - Snapshot is not a dict (type: {type(snap)})")
                return False
            
            snap = _migrate_snapshot(snap)

            # Applying the legacy field-by-field loader directly to the live
            # store is only safe if every touched field can be restored. Capture
            # the full current schema before the first mutation.
            try:
                transaction_fields = {
                    key for key in snap.keys()
                    if isinstance(key, str) and not key.startswith("_")
                }
                transaction_fields.update(_CANONICAL_SNAPSHOT_REQUIRED_KEYS)
                snapshot_state = {}
                for field_name in transaction_fields:
                    if hasattr(store, field_name):
                        snapshot_state[field_name] = _cp.deepcopy(
                            getattr(store, field_name)
                        )
                    else:
                        snapshot_absent_fields.add(field_name)
            except Exception as capture_error:
                renpy.log(
                    f"SNAPSHOT: ERROR - could not capture transactional apply state: {capture_error}"
                )
                return False
            
            # Track expected fields
            expected_fields = [
                "money", "current_day", "current_month", "current_year", "workers",
                "available_buildings", "owned_buildings", "map_button_buildings",
                "custom_names", "player_name", "player_title", "tutorial_active",
                "current_objective", "manager_inventory", "unlocked_shops",
                "manager_interactions_today", "event_flags", "event_occurrences",
                "event_last_occurred", "assignment_presets"
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

            # Assignment presets (QoL; optional). Missing on old saves -> {} (no crash).
            try:
                presets_val = snap.get("assignment_presets")
                store.assignment_presets = presets_val if presets_val is not None else {}
                if presets_val is not None:
                    applied_any = True
                    applied_fields.append("assignment_presets")
                else:
                    missing_fields.append("assignment_presets")
            except Exception as e:
                failed_fields.append("assignment_presets")
                store.assignment_presets = {}
                renpy.log(f"SNAPSHOT: WARNING - Could not apply assignment_presets: {e}")

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
                    failed_fields.append(field_name)
                    renpy.log(f"SNAPSHOT: WARNING - Could not apply {field_name} (pre-worker-defaults): {e}")

            # CRITICAL: Ensure worker defaults (including min 3-5 traits) after snapshot restore.
            # Restored workers never pass through ensure_worker_defaults otherwise.
            try:
                if hasattr(store, 'ensure_worker_defaults'):
                    for _roster_name, _roster in (
                        ("workers", getattr(store, 'workers', [])),
                        ("available_workers", getattr(store, 'available_workers', [])),
                    ):
                        for worker in _roster:
                            worker_before_defaults = _cp.deepcopy(worker)
                            try:
                                store.ensure_worker_defaults(worker)
                            except Exception as worker_error:
                                _name = worker.get("name", "?") if hasattr(worker, "get") else "?"
                                try:
                                    if hasattr(worker, "clear") and hasattr(worker, "update"):
                                        worker.clear()
                                        worker.update(worker_before_defaults)
                                    else:
                                        raise TypeError("worker is not restorable in place")
                                except Exception as worker_rollback_error:
                                    failed_fields.append(f"{_roster_name}.{_name}.defaults")
                                    renpy.log(
                                        f"SNAPSHOT: worker-default rollback failed for {_roster_name}/{_name}: {worker_rollback_error}"
                                    )
                                renpy.log(f"SNAPSHOT: ensure_worker_defaults failed for {_roster_name}/{_name}: {worker_error}")
                    renpy.log("SNAPSHOT: Applied ensure_worker_defaults to all workers after restore")
                else:
                    renpy.log("SNAPSHOT: WARNING - ensure_worker_defaults not found")
            except Exception as e:
                failed_fields.append("workers.defaults")
                renpy.log(f"SNAPSHOT: ensure_worker_defaults error: {e}")

            # Only continue if we applied at least one critical field
            if not applied_critical:
                renpy.log("SNAPSHOT: ERROR - No critical fields (money, day, or workers) could be applied")
                _rollback_snapshot_state()
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
                failed_fields.append("available_buildings.assigned_servants")
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
            # Franchise Holdings are absent from legacy snapshots by design.
            try:
                store.franchise_holdings = normalize_holdings(snap.get("franchise_holdings", {}))
                for _worker in getattr(store, "workers", []) or []:
                    if not hasattr(_worker, "get"):
                        continue
                    _fid = str(_worker.get("franchise_id", "") or "").strip().lower()
                    if _fid and _fid not in store.franchise_holdings:
                        _worker.pop("franchise_id", None)
                        _worker.pop("franchise_since_day", None)
            except Exception as e:
                failed_fields.append("franchise_holdings")
                store.franchise_holdings = {}
                renpy.log("SNAPSHOT: Franchise Holdings restore failed: %s" % e)
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
                ("lanista_name", "The Lanista"),
                ("lanista_known_name", False),
                ("lanista_devotion", 0),
                ("lanista_dominion", 0),
                ("lanista_affection", 0),
                ("lanista_corruption", 0),
                ("lanista_stage", 1),
                ("lanista_visit_count", 0),
                ("lanista_night_visit_total_days", None),
                ("lanista_gate_closed_total_days", None),
                ("lanista_last_talk_total_days", None),
                ("lanista_filler_talk_index", 0),
                ("lanista_last_story_total_days", None),
                ("lanista_last_question_total_days", None),
                ("lanista_last_gift_total_days", None),
                ("lanista_gifts_given", 0),
                ("lanista_wager_intro_done", False),
                ("lanista_debt_finance_unlocked", False),
                ("lanista_debt_finance_last_day", None),
                ("lanista_donation_total", 0),
                ("lanista_donation_highest_tier", 0),
                ("lanista_favors_total", 0),
                ("lanista_favor_highest_tier", 0),
                ("lanista_favor_balance", 0),
                ("lanista_favors_collected", 0),
                ("lanista_collect_last_day", None),
                ("lanista_monthly_purse_last_month", None),
                ("lanista_spectacle_arc_step", 0),
                ("lanista_spectacle_arc_last_day", None),
                ("lanista_arena_program_tier", 0),
                ("lanista_arena_program_last_day", None),
                ("lanista_card_tier", 0),
                ("lanista_card_last_day", None),
                ("lanista_pinup_unlocked", False),
                ("lanista_oilchains_unlocked", False),
                ("lanista_spectacle_unlocked", False),
                ("lanista_spectacle_pitch_done", False),
                ("lanista_wager_last_day", None),
                ("lanista_wager_loss_streak", 0),
                ("lanista_s2_gate_fired", False),
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
                ("lanista_weekly_cut_last_day", None),
                # Arena / Laboratory progression and cooldowns
                ("arena_unlocked", False),
                ("arena_lanista_paid", False),
                ("arena_special_match_intro_done", False),
                ("last_special_match_total_days", None),
                ("last_special_match_worker_name", None),
                ("last_arena_worker_name", None),
                ("arena_trial_completed", None),
                ("arena_successor_met", False),
                ("arena_lanista_feedback_pending", None),
                ("alchemy_unlocked", False),
                ("last_laboratory_use_total_days", None),
                ("last_alchemy_worker_name", None),
                # One-time manager level awards (Master's Elixir / first Arena crown)
                ("elixir_award_granted", False),
                ("elixir_intro_done", False),
                ("arena_champion_award_granted", False),
                # Missing key (legacy snapshot) leaves the store default None, which
                # sends _after_load_restore_nsfw_mode down the building heuristic.
                ("save_nsfw_mode", None),
            ]:
                try:
                    if field_name in snap:
                        val = snap.get(field_name)
                        if field_name == "arena_lanista_feedback_pending":
                            val = _cp.deepcopy(val)
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
                ("yvara_post_arc_talks_seen", []),
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
                ("lanista_s6_talks_done", []),
                ("lanista_fillers_seen", [])
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

            # Arc choice maps are dictionaries, not completion lists. Keep them
            # separate so malformed legacy values fall back safely.
            try:
                if "lanista_remark_choices" in snap:
                    val = _to_dict(snap.get("lanista_remark_choices"))
                    setattr(store, "lanista_remark_choices", _cp.deepcopy(val) if val is not None else {})
                    applied_any = True
                    applied_fields.append("lanista_remark_choices")
                elif not hasattr(store, "lanista_remark_choices"):
                    setattr(store, "lanista_remark_choices", {})
            except Exception as e:
                failed_fields.append("lanista_remark_choices")
                renpy.log(f"SNAPSHOT: WARNING - Could not apply lanista_remark_choices: {e}")
            
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
                                    failed_fields.append(f"workers.{worker_name}.item_effects.{item_id}")
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
                                    failed_fields.append(f"workers.{worker_name}.item_effects.{item_id}")
                                    _snap_err(f"SNAPSHOT: Error applying effects for item '{item_id}': {e}")
                                    import traceback
                                    renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                        else:
                            _snap_log(f"SNAPSHOT: Item {idx} invalid format: {item} (type: {type(item)}, len: {len(item) if hasattr(item, '__len__') else 'N/A'})")
                    except Exception as e:
                        failed_fields.append(f"workers.{worker_name}.inventory.{idx}")
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
                failed_fields.append("process_manager_auto_rest")
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
                failed_fields.append("available_buildings.assigned_servants.rebuild")
                renpy.log(f"SNAPSHOT: WARNING - assigned_servants rebuild error: {e}")
            
            # Post-validation: verify at least one critical field was applied
            try:
                has_money = hasattr(store, 'money') and store.money is not None
                has_day = hasattr(store, 'current_day') and store.current_day is not None
                has_workers = hasattr(store, 'workers') and hasattr(store.workers, "__iter__") and not isinstance(store.workers, str)
                
                if not (has_money or has_day or has_workers):
                    renpy.log("SNAPSHOT: ERROR - Post-validation failed: no critical fields were applied")
                    _rollback_snapshot_state()
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
                if failed_fields:
                    renpy.log("SNAPSHOT: ERROR - rejecting partially applied snapshot")
                    _rollback_snapshot_state()
                    return False
            except Exception as validation_error:
                renpy.log(f"SNAPSHOT: ERROR - Post-validation exception: {validation_error}")
                _rollback_snapshot_state()
                return False
            
            return True
        except Exception as e:
            renpy.log(f"SNAPSHOT: CRITICAL ERROR - apply_snapshot failed: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            _rollback_snapshot_state()
            # Return False after restoring the live store. The caller may report
            # the failure, but must not layer a second source over this attempt.
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
        """Atomically preserve the existing snapshot before overwriting it."""
        if not os.path.exists(filepath):
            return True
        backup_path = _get_backup_file_path(slot_name)
        backup_temp_path = backup_path + ".tmp"
        try:
            if os.path.exists(backup_temp_path):
                os.remove(backup_temp_path)
            shutil.copy2(filepath, backup_temp_path)
            os.replace(backup_temp_path, backup_path)
            if DEBUG_SNAPSHOT:
                renpy.log(f"SNAPSHOT: Created backup for {slot_name}")
            return True
        except Exception as e:
            if os.path.exists(backup_temp_path):
                try:
                    os.remove(backup_temp_path)
                except Exception:
                    pass
            renpy.log(f"SNAPSHOT: ERROR - Could not create required backup for {slot_name}: {e}")
            raise
    
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
            
            # Replace atomically in the same directory. os.replace supports an
            # existing destination on Windows without an unlink window.
            os.replace(temp_filepath, filepath)
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
    
    def _write_snapshot_fallback(filepath, snap):
        """Last-resort snapshot write when the atomic path failed.

        Still writes to its own temp file, re-reads it and verifies the
        critical fields before replacing MAIN, so MAIN is never truncated in
        place and a corrupt result raises instead of being reported as saved.
        """
        tmp_path = filepath + ".fallback.tmp"
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(snap, handle, indent=2, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            with open(tmp_path, "r", encoding="utf-8") as handle:
                verified = json.load(handle)
            expected = json.loads(json.dumps(snap, ensure_ascii=False))
            if verified != expected:
                raise ValueError("fallback verification failed: written snapshot differs from source")
            os.replace(tmp_path, filepath)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def _cleanup_stale_snapshot_temps(max_age_seconds=86400, max_deletions=25):
        """Remove leftover temp files from our own snapshot writes.

        Only matches the exact temp patterns this module creates, only files
        older than max_age_seconds (a fresh temp may belong to a live write in
        another instance), at most max_deletions per pass, and never raises.
        """
        import time
        deleted = 0
        try:
            saves_dir = getattr(config, "savedir", None) or os.path.join(config.basedir, "game", "saves")
            if not os.path.isdir(saves_dir):
                return 0
            now = time.time()
            for name in os.listdir(saves_dir):
                if deleted >= max_deletions:
                    break
                is_ours = (
                    (name.startswith("tmp") and name.endswith(".json.tmp"))
                    or (
                        name.startswith("snapshot_")
                        and name.endswith((".json.tmp", ".restore.tmp", ".fallback.tmp", ".bak.tmp", ".keep.tmp", ".previous.tmp"))
                    )
                )
                if not is_ours:
                    continue
                path = os.path.join(saves_dir, name)
                try:
                    if not os.path.isfile(path):
                        continue
                    if (now - os.path.getmtime(path)) < max_age_seconds:
                        continue
                    os.remove(path)
                    deleted += 1
                except Exception:
                    continue
            if deleted:
                renpy.log(f"SNAPSHOT: cleaned {deleted} stale temp file(s) from the saves dir")
        except Exception as e:
            renpy.log(f"SNAPSHOT: WARNING - stale temp cleanup aborted: {e}")
        return deleted

    def _future_snapshot_keep_paths(filepath, version=None):
        directory = os.path.dirname(filepath)
        basename = os.path.basename(filepath)
        prefix = basename + (f".v{int(version)}." if version is not None else ".v")
        try:
            return [
                os.path.join(directory, name)
                for name in os.listdir(directory)
                if name.startswith(prefix) and name.endswith(".keep")
            ]
        except Exception:
            return []

    def _prune_future_snapshot_keeps(filepath, version, protected_path=None):
        """Bound future-version copies while never deleting the current copy."""
        paths = _future_snapshot_keep_paths(filepath, version)
        if len(paths) <= SNAPSHOT_KEEP_LIMIT_PER_VERSION:
            return
        def _safe_mtime(path):
            try:
                return os.path.getmtime(path)
            except Exception:
                return 0
        paths.sort(key=_safe_mtime, reverse=True)
        retained = []
        if protected_path and protected_path in paths:
            retained.append(protected_path)
        for path in paths:
            if path not in retained and len(retained) < SNAPSHOT_KEEP_LIMIT_PER_VERSION:
                retained.append(path)
        for path in paths:
            if path in retained:
                continue
            try:
                os.remove(path)
                renpy.log(f"SNAPSHOT: pruned old future-version copy {os.path.basename(path)}")
            except Exception as error:
                renpy.log(f"SNAPSHOT: WARNING - could not prune future-version copy {path}: {error}")

    def _delete_future_snapshot_keeps(filepath):
        for path in _future_snapshot_keep_paths(filepath):
            try:
                os.remove(path)
            except Exception as error:
                renpy.log(f"SNAPSHOT: WARNING - could not delete future-version copy {path}: {error}")

    def _preserve_future_snapshot_if_needed(filepath, existing_snap, slot_name):
        """One-time preservation of a MAIN written by a NEWER game version.

        This build only writes SNAPSHOT_CURRENT_VERSION, so overwriting a
        future-version MAIN (plus the post-save backup refresh) would destroy
        the last copy holding its unknown fields. Keep it as
        snapshot_<slot>.json.v<N>.keep, outside the MAIN/BACKUP cycle. The
        .keep file itself is the guard: once a valid copy for that version
        exists it is never rewritten. Returns False only when the copy could
        not be secured - the caller must then abort the save (fail closed).
        """
        try:
            version = int(existing_snap.get("snapshot_version", 0) or 0)
        except Exception:
            return True  # unreadable version field: legacy data, not future
        if version <= SNAPSHOT_CURRENT_VERSION:
            return True
        keep_path = f"{filepath}.v{version}.keep"
        try:
            if os.path.exists(keep_path):
                kept = _read_snapshot_file(keep_path)
                if kept == existing_snap:
                    _prune_future_snapshot_keeps(filepath, version, keep_path)
                    return True  # already preserved; never overwrite it
                # Another future save of the same schema already owns the
                # stable path. Preserve this distinct MAIN under its content
                # digest rather than overwriting either copy.
                with open(filepath, "rb") as source:
                    digest = hashlib.sha256(source.read()).hexdigest()
                keep_path = f"{filepath}.v{version}.{digest}.keep"
                if os.path.exists(keep_path):
                    kept = _read_snapshot_file(keep_path)
                    if kept == existing_snap:
                        _prune_future_snapshot_keeps(filepath, version, keep_path)
                        return True
                    renpy.log(
                        f"SNAPSHOT: WARNING - replacing corrupt digest preservation for {slot_name}"
                    )
            keep_tmp = keep_path + ".tmp"
            if os.path.exists(keep_tmp):
                os.remove(keep_tmp)
            shutil.copy2(filepath, keep_tmp)
            with open(keep_tmp, "r+b") as durable_copy:
                durable_copy.flush()
                os.fsync(durable_copy.fileno())
            copied = _read_snapshot_file(keep_tmp)
            if copied != existing_snap:
                raise ValueError("preserved copy failed verification")
            os.replace(keep_tmp, keep_path)
            _prune_future_snapshot_keeps(filepath, version, keep_path)
            renpy.log(
                f"SNAPSHOT: WARNING - slot {slot_name} held a v{version} snapshot from a newer "
                f"game version; preserved it as {os.path.basename(keep_path)}"
            )
            renpy.notify(_("Newer-version save detected: a copy was preserved next to the save."))
            return True
        except Exception as e:
            try:
                keep_tmp = keep_path + ".tmp"
                if os.path.exists(keep_tmp):
                    os.remove(keep_tmp)
            except Exception:
                pass
            renpy.log(f"SNAPSHOT: ERROR - could not preserve future-version snapshot for {slot_name}: {e}")
            return False

    def snapshot_pre_save_slot(slot_num):
        """Save snapshot before saving to a specific slot."""
        try:
            # SnapshotFileSave uses this session-only flag to decide whether a
            # failed pre-save needs MAIN restored from BACKUP. Failures before
            # the write phase (notably future-version preservation) leave MAIN
            # untouched and must not replace it with a potentially stale backup.
            renpy.session["_fm_snapshot_pre_save_may_have_touched_main"] = False
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

            # One bounded sweep per session for our own leftover temp files.
            try:
                if not renpy.session.get("_fm_snapshot_temp_cleanup_done"):
                    renpy.session["_fm_snapshot_temp_cleanup_done"] = True
                    _cleanup_stale_snapshot_temps()
            except Exception as cleanup_error:
                renpy.log(f"SNAPSHOT: WARNING - stale temp cleanup skipped: {cleanup_error}")

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
                    if not _preserve_future_snapshot_if_needed(existing_path, existing_snap, slot_name):
                        renpy.log(f"SNAPSHOT: ERROR - aborting save for {slot_name}: future-version snapshot could not be preserved")
                        return False
            
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
            # Pair this JSON sidecar with the native Ren'Py save. The value is
            # part of native store roots and is also stamped into the JSON.
            transaction_id = str(uuid.uuid4())
            store.snapshot_transaction_id = transaction_id
            # Build and save snapshot BEFORE Ren'Py saves (captures current state in memory)
            snap = _build_snapshot()
            # Stamp slot identity to prevent cross-slot corruption
            slot_guid = _ensure_slot_guid(slot_name)
            snap["snapshot_slot"] = slot_name
            snap["snapshot_guid"] = slot_guid
            snap["snapshot_transaction_id"] = transaction_id
            
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
            renpy.session["_fm_snapshot_pre_save_may_have_touched_main"] = True
            try:
                _write_snapshot_file(filepath, snap, slot_name)
            except Exception as atomic_error:
                renpy.log(f"SNAPSHOT: WARNING - Atomic save failed, attempting fallback save: {atomic_error}")
                # Create backup before fallback save too
                _create_backup(filepath, slot_name)
                # Fallback: own temp + verify + replace, so MAIN is never
                # truncated in place and a corrupt write cannot pass as saved.
                try:
                    _write_snapshot_fallback(filepath, snap)
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

    class SnapshotFileLoad(renpy.store.Action):
        """Mark the slot immediately before the native load, and clear the
        marker again if the native load fails or returns without restarting
        the context (i.e. without actually loading).

        On success renpy.load() never returns (it raises through unfreeze),
        so the marker survives until _after_load_snapshot_callback clears it.
        """

        def __init__(self, load_action, slot_num, confirm=None, page=None):
            self.load_action = load_action
            self.slot_num = slot_num
            self.confirm = bool(getattr(load_action, "confirm", False)) if confirm is None else bool(confirm)
            self.page = page
            self.confirm_action = None

            if self.confirm:
                if isinstance(self.load_action, renpy.store.FileLoad):
                    native_action = renpy.store.FileLoad(
                        self.load_action.name,
                        confirm=False,
                        page=self.load_action.page,
                        newest=self.load_action.newest,
                        slot=self.load_action.slot,
                    )
                else:
                    native_action = self.load_action
                confirmed_action = SnapshotFileLoad(
                    native_action,
                    self.slot_num,
                    confirm=False,
                    page=self.page,
                )
                self.confirm_action = renpy.store.Confirm(
                    renpy.store.layout.LOADING,
                    confirmed_action,
                )

        def __call__(self):
            # Sensitivity is delegated to the wrapped action so empty slots,
            # replays and auto-page behave exactly like a plain FileAction.
            if not renpy.is_sensitive(self.load_action):
                return

            # FileLoad normally asks for confirmation while in-game. Defer both
            # marker assignment and the native load until the player confirms;
            # cancelling must leave persistent markers untouched.
            if self.confirm and not getattr(store, "main_menu", False):
                return renpy.run(self.confirm_action)

            previous_loading_slot = getattr(persistent, "_loading_slot", None)
            previous_last_slot = getattr(persistent, "_last_loaded_snapshot_slot", None)

            # Mark before anything else: this is the whole point of the wrapper.
            snapshot_mark_load_slot(self.slot_num)

            try:
                rv = renpy.run(self.load_action)
            except renpy.game.RestartTopContext:
                # Real load in progress: keep the marker for after_load.
                raise
            except Exception as load_error:
                # Load failed - don't leave an orphan marker pointing at a slot
                # the user never actually loaded. Re-raise so the error is seen.
                persistent._loading_slot = previous_loading_slot
                persistent._last_loaded_snapshot_slot = previous_last_slot
                renpy.log(f"SNAPSHOT: native load failed, cleared loading marker: {load_error}")
                raise

            # The native action ran but did NOT restart the context: nothing was
            # loaded (e.g. token check declined). Clear the marker.
            persistent._loading_slot = previous_loading_slot
            persistent._last_loaded_snapshot_slot = previous_last_slot
            return rv

        def get_sensitive(self):
            return renpy.is_sensitive(self.load_action)

        def get_selected(self):
            return renpy.is_selected(self.load_action)

        def get_tooltip(self):
            return renpy.display.behavior.get_tooltip(self.load_action)

    class CanonicalSnapshotFileLoad(renpy.store.Action):
        """Load a complete sidecar into a clean store, never a saved stack."""

        def __init__(self, load_action, slot_num, confirm=None, page=None):
            self.load_action = load_action
            self.slot_num = slot_num
            self.confirm = bool(getattr(load_action, "confirm", False)) if confirm is None else bool(confirm)
            self.page = page
            self.confirm_action = None

            if self.confirm:
                if isinstance(self.load_action, renpy.store.FileLoad):
                    native_action = renpy.store.FileLoad(
                        self.load_action.name,
                        confirm=False,
                        page=self.load_action.page,
                        newest=self.load_action.newest,
                        slot=self.load_action.slot,
                    )
                else:
                    native_action = self.load_action
                confirmed_action = CanonicalSnapshotFileLoad(
                    native_action,
                    self.slot_num,
                    confirm=False,
                    page=self.page,
                )
                self.confirm_action = renpy.store.Confirm(
                    renpy.store.layout.LOADING,
                    confirmed_action,
                )

        def __call__(self):
            if not renpy.is_sensitive(self.load_action):
                return

            if self.confirm and not getattr(store, "main_menu", False):
                return renpy.run(self.confirm_action)

            if not _prepare_canonical_snapshot_load(self.slot_num):
                renpy.notify(_("This save has no complete, verified snapshot and was not loaded."))
                return

            renpy.full_restart(
                transition=None,
                label="_canonical_snapshot_load",
                target="_canonical_snapshot_load",
                save=False,
            )

        def get_sensitive(self):
            return renpy.is_sensitive(self.load_action)

        def get_selected(self):
            return renpy.is_selected(self.load_action)

        def get_tooltip(self):
            return renpy.display.behavior.get_tooltip(self.load_action)

    class SnapshotDeletePair(renpy.store.Action):
        """Delete native and sidecar state while holding the slot lock."""

        def __init__(self, slot_num, page=None):
            self.slot_num = slot_num
            self.page = page
            self.native_action = renpy.store.FileDelete(
                slot_num, confirm=False, page=page
            )

        def __call__(self):
            if not snapshot_slot_has_any_data(self.slot_num):
                return
            slot_name = _get_current_slot_name(self.slot_num)
            if not slot_name:
                return
            lock_token = _acquire_snapshot_slot_lock(slot_name)
            if not lock_token:
                renpy.notify(_("This save slot is busy. Try again in a moment."))
                return
            try:
                result = None
                if renpy.is_sensitive(self.native_action):
                    result = renpy.run(self.native_action)
                snapshot_pre_delete_slot(self.slot_num)
                return result
            finally:
                _release_snapshot_slot_lock(lock_token)

        def get_sensitive(self):
            return snapshot_slot_has_any_data(self.slot_num)

        def get_selected(self):
            return False

    class SnapshotFileDelete(renpy.store.Action):
        """Delete snapshot sidecars only inside the confirmed delete.

        Cancelling leaves every file untouched. Accepting runs a single locked
        Action that removes sidecars, future keeps, GUID and native save.
        """

        def __init__(self, slot_num, page=None):
            self.slot_num = slot_num
            self.page = page
            self.yes_action = SnapshotDeletePair(slot_num, page=page)
            self.confirm_action = renpy.store.Confirm(
                renpy.store.layout.DELETE_SAVE,
                self.yes_action,
            )

        def __call__(self):
            return renpy.run(self.confirm_action)

        def get_sensitive(self):
            return self.confirm_action.get_sensitive()

        def get_selected(self):
            return False
    
    def _previous_snapshot_backup_temp_path(slot_name):
        return _get_backup_file_path(slot_name) + ".previous.tmp"

    def _preserve_previous_snapshot_backup(slot_name, had_snapshot):
        """Keep the previous sidecar pair until the native save commits."""
        previous_path = _previous_snapshot_backup_temp_path(slot_name)
        if os.path.exists(previous_path):
            os.remove(previous_path)
        if not had_snapshot:
            return None
        backup_path = _get_backup_file_path(slot_name)
        if not os.path.exists(backup_path):
            raise IOError(f"Previous snapshot backup is missing for {slot_name}")
        shutil.copy2(backup_path, previous_path)
        return previous_path

    def _cleanup_previous_snapshot_backup(previous_path):
        if previous_path and os.path.exists(previous_path):
            try:
                os.remove(previous_path)
            except Exception as cleanup_error:
                renpy.log(f"SNAPSHOT: WARNING - could not remove previous backup temp: {cleanup_error}")

    def _native_save_commit_marker(slot_name):
        """Return a marker that changes only when Ren'Py writes this slot."""
        try:
            location = renpy.loadsave.location
            metadata = location.json(slot_name) or {}
            created_at = metadata.get("_ctime") if hasattr(metadata, "get") else None
            return (location.mtime(slot_name), created_at)
        except Exception as marker_error:
            renpy.log(f"SNAPSHOT: WARNING - could not inspect native save marker for {slot_name}: {marker_error}")
            return (None, None)

    def _restore_snapshot_after_failed_native_save(slot_name, had_snapshot, previous_path=None):
        """Restore the previous sidecar pair when the native save does not commit."""
        filepath = _get_snapshot_file_path(slot_name)
        backup_path = _get_backup_file_path(slot_name)
        try:
            if had_snapshot:
                restore_source = previous_path if previous_path and os.path.exists(previous_path) else backup_path
                if not os.path.exists(restore_source):
                    renpy.log(f"SNAPSHOT: ERROR - Native save failed and no backup exists for {slot_name}")
                    return False
                restore_path = filepath + ".restore.tmp"
                shutil.copy2(restore_source, restore_path)
                os.replace(restore_path, filepath)
                if os.path.normcase(restore_source) != os.path.normcase(backup_path):
                    backup_restore_path = backup_path + ".restore.tmp"
                    shutil.copy2(restore_source, backup_restore_path)
                    os.replace(backup_restore_path, backup_path)
                renpy.log(f"SNAPSHOT: Restored previous snapshot after native save failure for {slot_name}")
            else:
                if os.path.exists(filepath):
                    os.remove(filepath)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                renpy.log(f"SNAPSHOT: Removed orphan snapshot after first native save failure for {slot_name}")
            return True
        except Exception as restore_error:
            renpy.log(f"SNAPSHOT: ERROR - Could not restore snapshot after native save failure for {slot_name}: {restore_error}")
            return False

    class SnapshotFileSave(renpy.store.Action):
        """Save snapshot first; only save if snapshot succeeds."""
        def __init__(self, slot_num, confirm=False):
            self.slot_num = slot_num
            self.confirm = confirm

        def __call__(self):
            if not save_is_allowed():
                renpy.notify(_("Saving is unavailable until the current sequence is complete."))
                return
            slot_name = _get_current_slot_name(self.slot_num)
            if not slot_name:
                page = getattr(persistent, "_file_page", 1)
                slot_name = f"{page}-{self.slot_num}"
            lock_token = _acquire_snapshot_slot_lock(slot_name)
            if not lock_token:
                renpy.log(f"SNAPSHOT: WARNING - save blocked because slot {slot_name} is busy")
                renpy.notify(_("This save slot is busy. Try again in a moment."))
                return
            try:
                return self._run_locked(slot_name)
            finally:
                _release_snapshot_slot_lock(lock_token)

        def _run_locked(self, slot_name):
            had_snapshot = os.path.exists(_get_snapshot_file_path(slot_name))
            previous_transaction_id = getattr(store, "snapshot_transaction_id", None)
            previous_backup_path = None
            native_marker_before = _native_save_commit_marker(slot_name)
            renpy.session["_fm_snapshot_pre_save_may_have_touched_main"] = False
            try:
                if snapshot_pre_save_slot(self.slot_num):
                    # Prepare the paired recovery sidecar before committing the
                    # native save. If this fails, the native slot is untouched.
                    previous_backup_path = _preserve_previous_snapshot_backup(
                        slot_name, had_snapshot
                    )
                    _create_backup(_get_snapshot_file_path(slot_name), slot_name)
                    # snapshot_pre_save_slot stamps snapshot_transaction_id during
                    # this Action call. Seal that mutation into Ren'Py roots before
                    # FileSave freezes them, otherwise the native save restores None.
                    # NOTE: cycling get_changes mid-interaction empties the pending
                    # delta of the current rollback record; that is only safe while
                    # config.rollback_enabled is False.
                    renpy.python.store_dicts["store"].get_changes(True, None)
                    result = renpy.store.FileSave(self.slot_num, confirm=self.confirm)()
                    native_marker_after = _native_save_commit_marker(slot_name)
                    # A real FileSave writes a fresh SaveRecord whose JSON carries
                    # a new _ctime (renpy/loadsave.py:451), so both components of
                    # the marker must advance. Requiring only "tuple changed"
                    # would accept an mtime-only touch (os.utime) as a commit.
                    if (
                        native_marker_after[0] is None
                        or native_marker_after[1] is None
                        or native_marker_after == native_marker_before
                        or native_marker_after[1] == native_marker_before[1]
                    ):
                        raise RuntimeError("Ren'Py native save returned without committing the slot")
                    renpy.session.pop("_fm_snapshot_pre_save_may_have_touched_main", None)
                    return result
                store.snapshot_transaction_id = previous_transaction_id
                may_have_touched_main = renpy.session.pop(
                    "_fm_snapshot_pre_save_may_have_touched_main", True
                )
                if may_have_touched_main:
                    _restore_snapshot_after_failed_native_save(
                        slot_name, had_snapshot, previous_backup_path
                    )
                renpy.notify(_("Save cancelled: snapshot stage failed (see log.txt)."))
            except Exception as e:
                store.snapshot_transaction_id = previous_transaction_id
                may_have_touched_main = renpy.session.pop(
                    "_fm_snapshot_pre_save_may_have_touched_main", True
                )
                if may_have_touched_main:
                    _restore_snapshot_after_failed_native_save(
                        slot_name, had_snapshot, previous_backup_path
                    )
                import traceback
                renpy.log(f"SNAPSHOT: ERROR - SnapshotFileSave failed: {e}")
                renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
                renpy.notify(_("Save cancelled: {} (see log.txt).").format(type(e).__name__))
            except BaseException:
                store.snapshot_transaction_id = previous_transaction_id
                may_have_touched_main = renpy.session.pop(
                    "_fm_snapshot_pre_save_may_have_touched_main", True
                )
                if may_have_touched_main:
                    _restore_snapshot_after_failed_native_save(
                        slot_name, had_snapshot, previous_backup_path
                    )
                raise
            finally:
                _cleanup_previous_snapshot_backup(previous_backup_path)
        
        def get_sensitive(self):
            return save_is_allowed() and renpy.store.FileSave(self.slot_num, confirm=self.confirm).get_sensitive()
        
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

    def _snapshot_has_complete_critical_state(snap):
        """Validate one snapshot source before it is allowed to touch the store."""
        if not snap or not hasattr(snap, "get"):
            return False
        try:
            candidate = _migrate_snapshot(_cp.deepcopy(snap))
            if candidate.get("money") is None or candidate.get("current_day") is None:
                return False
            int(candidate.get("money"))
            int(candidate.get("current_day"))
            if _to_list(candidate.get("workers")) is None:
                return False
            return True
        except Exception as validation_error:
            renpy.log(f"SNAPSHOT: critical pre-validation failed: {validation_error}")
            return False

    _LEGACY_CANONICAL_SNAPSHOT_REQUIRED_KEYS = (
        "snapshot_version",
        "snapshot_slot",
        "snapshot_guid",
        "money",
        "current_day",
        "current_month",
        "current_year",
        "workers",
        "available_workers",
        "available_buildings",
        "owned_buildings",
        "manager_inventory",
        "event_flags",
        "event_occurrences",
        "map_button_buildings",
        "unlocked_shops",
        "management_skills",
    )

    # Transaction-paired snapshots are produced by this build and must contain
    # the entire surface written by _build_snapshot. Unpaired legacy snapshots
    # retain the smaller compatibility contract above.
    _CANONICAL_SNAPSHOT_REQUIRED_KEYS = (
        "snapshot_slot",
        "snapshot_guid",
        "snapshot_transaction_id",
        "snapshot_version",
        "money",
        "current_day",
        "current_month",
        "current_year",
        "workers",
        "available_workers",
        "available_buildings",
        "owned_buildings",
        "map_button_buildings",
        "assignment_presets",
        "franchise_holdings",
        "custom_names",
        "player_name",
        "player_title",
        "tutorial_active",
        "current_objective",
        "objective_1_complete",
        "objective_2_complete",
        "objective_3_complete",
        "objective_4_complete",
        "objective_5_complete",
        "objective_6_complete",
        "objective_7_complete",
        "objective_8_complete",
        "objective_9_complete",
        "objective_10_complete",
        "objective_11_complete",
        "objective_12_complete",
        "objective_13_complete",
        "objective_14_complete",
        "objective_15_complete",
        "objective_16_complete",
        "governor_attention",
        "governor_tension_active",
        "governor_retaliation_done",
        "days_since_last_tension_event",
        "workers_hired",
        "building_1_type_set",
        "workers_assigned_count",
        "potion_purchased",
        "potion_transferred",
        "potion_used_on_worker",
        "building_upgraded_tutorial",
        "building_skill_bonus_increased_tutorial",
        "tutorial_friendly_chat_done",
        "event_flags",
        "event_occurrences",
        "event_last_occurred",
        "daily_spawns",
        "can_recruit_today",
        "save_nsfw_mode",
        "last_worker_refill_day",
        "last_worker_refill_month",
        "last_worker_refill_year",
        "map_worker_refill_count",
        "last_map_refill_day",
        "last_take_a_walk_day",
        "take_a_walk_in_progress",
        "manager_inventory",
        "unlocked_shops",
        "manager_interactions_today",
        "game_initialized",
        "is_new_game",
        "academy_enrolled",
        "academy_haggle_available",
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
        "yvara_s1_talks_done",
        "yvara_s1_remarks_done",
        "yvara_gifts_given",
        "yvara_s2_talks_done",
        "yvara_s2_remarks_done",
        "yvara_s2_gifts_given",
        "yvara_s3_talks_done",
        "yvara_s3_remarks_done",
        "yvara_observed_sessions",
        "yvara_observed_last_day",
        "yvara_lesson_absorbed",
        "yvara_leverage_financial",
        "yvara_s3_gate_fired",
        "yvara_s4_talks_done",
        "yvara_s4_remarks_done",
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
        "yvara_s5_talks_done",
        "yvara_s5_remarks_done",
        "yvara_s6_talks_done",
        "yvara_post_arc_talks_seen",
        "lanista_gender",
        "lanista_name",
        "lanista_known_name",
        "lanista_devotion",
        "lanista_dominion",
        "lanista_affection",
        "lanista_corruption",
        "lanista_stage",
        "lanista_visit_count",
        "lanista_night_visit_total_days",
        "lanista_gate_closed_total_days",
        "lanista_last_talk_total_days",
        "lanista_filler_talk_index",
        "lanista_last_story_total_days",
        "lanista_last_question_total_days",
        "lanista_last_gift_total_days",
        "lanista_gifts_given",
        "lanista_wager_intro_done",
        "lanista_debt_finance_unlocked",
        "lanista_debt_finance_last_day",
        "lanista_donation_total",
        "lanista_donation_highest_tier",
        "lanista_favors_total",
        "lanista_favor_highest_tier",
        "lanista_favor_balance",
        "lanista_favors_collected",
        "lanista_collect_last_day",
        "lanista_monthly_purse_last_month",
        "lanista_spectacle_arc_step",
        "lanista_spectacle_arc_last_day",
        "lanista_arena_program_tier",
        "lanista_arena_program_last_day",
        "lanista_card_tier",
        "lanista_card_last_day",
        "lanista_pinup_unlocked",
        "lanista_oilchains_unlocked",
        "lanista_spectacle_unlocked",
        "lanista_spectacle_pitch_done",
        "lanista_wager_last_day",
        "lanista_wager_loss_streak",
        "lanista_s2_gate_fired",
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
        "lanista_weekly_cut_last_day",
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
        "lanista_fillers_seen",
        "lanista_remark_choices",
        "management_skills",
        "manager_portrait",
        "manager_start_skill_chosen",
        "manager_level",
        "arena_unlocked",
        "arena_lanista_paid",
        "arena_special_match_intro_done",
        "last_special_match_total_days",
        "last_special_match_worker_name",
        "last_arena_worker_name",
        "arena_trial_completed",
        "arena_successor_met",
        "arena_lanista_feedback_pending",
        "alchemy_unlocked",
        "last_laboratory_use_total_days",
        "last_alchemy_worker_name",
        "elixir_award_granted",
        "elixir_intro_done",
        "arena_champion_award_granted",
    )

    def _snapshot_is_complete_for_canonical_load(snap):
        """Require a full save surface before bypassing native control flow."""
        if not _snapshot_has_complete_critical_state(snap):
            return False
        try:
            candidate = _migrate_snapshot(_cp.deepcopy(snap))
            if int(candidate.get("snapshot_version", 0)) > SNAPSHOT_CURRENT_VERSION:
                return False
            required_keys = (
                _CANONICAL_SNAPSHOT_REQUIRED_KEYS
                if candidate.get("snapshot_transaction_id")
                else _LEGACY_CANONICAL_SNAPSHOT_REQUIRED_KEYS
            )
            if any(key not in candidate for key in required_keys):
                return False
            for key in (
                "available_buildings",
                "event_flags",
                "event_occurrences",
                "map_button_buildings",
                "unlocked_shops",
                "management_skills",
            ):
                if not hasattr(candidate.get(key), "get"):
                    return False
            for key in ("assignment_presets", "franchise_holdings"):
                if key in candidate and not hasattr(candidate.get(key), "get"):
                    return False
            for key in (
                "workers",
                "available_workers",
                "owned_buildings",
                "manager_inventory",
            ):
                if _to_list(candidate.get(key)) is None:
                    return False
            return bool(
                candidate.get("snapshot_slot")
                and candidate.get("snapshot_guid")
            )
        except Exception as validation_error:
            renpy.log(f"SNAPSHOT: canonical completeness validation failed: {validation_error}")
            return False

    def _read_native_snapshot_transaction_id(slot_name):
        """Read only transaction identity; never unfreeze the saved context."""
        log_data = None
        roots = None
        rollback_log = None
        try:
            log_data, _signature = renpy.loadsave.location.load(slot_name)
            roots, rollback_log = renpy.loadsave.loads(log_data)
            return roots.get("store.snapshot_transaction_id")
        finally:
            log_data = None
            roots = None
            rollback_log = None

    def _canonical_snapshot_matches_identity(snap, slot_name, native_transaction_id, expected_guid=None):
        if not _snapshot_is_complete_for_canonical_load(snap):
            return False
        if snap.get("snapshot_slot") != slot_name:
            return False
        if snap.get("snapshot_transaction_id") != native_transaction_id:
            return False
        if expected_guid is not None and snap.get("snapshot_guid") != expected_guid:
            return False
        return True

    def _prepare_canonical_snapshot_load(slot_num):
        """Validate one sidecar and persist a restart handoff without applying it."""
        slot_name = _get_current_slot_name(slot_num)
        if not slot_name:
            return False
        try:
            native_transaction_id = _read_native_snapshot_transaction_id(slot_name)
        except Exception as native_error:
            renpy.log(f"SNAPSHOT: canonical native identity read failed for {slot_name}: {native_error}")
            return False

        expected_guid = _get_slot_guid(slot_name)
        candidates = (
            ("MAIN", _get_snapshot_file_path_for_reading(slot_name)),
            ("BACKUP", _get_backup_file_path_for_reading(slot_name)),
        )
        for source_name, source_path in candidates:
            if not os.path.exists(source_path):
                continue
            snap = _read_snapshot_file(source_path)
            if not _canonical_snapshot_matches_identity(
                snap,
                slot_name,
                native_transaction_id,
                expected_guid,
            ):
                continue
            if expected_guid is None:
                if not hasattr(persistent, "_slot_guids") or persistent._slot_guids is None:
                    persistent._slot_guids = {}
                persistent._slot_guids[slot_name] = snap.get("snapshot_guid")
            persistent._canonical_snapshot_load_pending = {
                "slot_name": slot_name,
                "source_name": source_name,
                "snapshot_guid": snap.get("snapshot_guid"),
                "snapshot_transaction_id": snap.get("snapshot_transaction_id"),
            }
            return True
        return False

    def _consume_canonical_snapshot_load():
        """Apply the selected source once, into the clean post-restart store."""
        pending = getattr(persistent, "_canonical_snapshot_load_pending", None)
        persistent._canonical_snapshot_load_pending = None
        if not pending or not hasattr(pending, "get"):
            return False

        slot_name = pending.get("slot_name")
        source_name = pending.get("source_name")
        if source_name == "MAIN":
            source_path = _get_snapshot_file_path_for_reading(slot_name)
        elif source_name == "BACKUP":
            source_path = _get_backup_file_path_for_reading(slot_name)
        else:
            return False

        snap = _read_snapshot_file(source_path)
        if not _canonical_snapshot_matches_identity(
            snap,
            slot_name,
            pending.get("snapshot_transaction_id"),
            pending.get("snapshot_guid"),
        ):
            return False

        store._snapshot_applied_slot_name = None
        store._snapshot_applied_source_path = None
        store._snapshot_load_alert = None
        if not _apply_snapshot(_cp.deepcopy(snap)):
            return False

        # No native rollback rewind follows this path, so normalization runs
        # once after the single snapshot application and cannot overwrite it.
        for callback in tuple(config.after_load_callbacks):
            if callback is _after_load_snapshot_callback:
                continue
            callback()

        persistent._last_loaded_snapshot_slot = slot_name
        persistent._loading_slot = None
        renpy.log(f"SNAPSHOT: canonical clean-store load applied {source_name} for {slot_name}")
        return True
    
    def _after_load_snapshot_callback():
        """Apply exactly one pre-validated MAIN or BACKUP snapshot after native load."""
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
                # clear_image_cache also resets _image_selection_instance, so
                # reopened day stories keep the same instance->image mapping.
                if hasattr(store, "clear_image_cache") and callable(store.clear_image_cache):
                    store.clear_image_cache()
                elif hasattr(store, "image_selection_cache") and hasattr(store.image_selection_cache, "clear"):
                    store.image_selection_cache.clear()
                if hasattr(store, "_trait_def_cache") and hasattr(store._trait_def_cache, "clear"):
                    store._trait_def_cache.clear()
                if hasattr(store, "_trait_defs_cache") and hasattr(store._trait_defs_cache, "clear"):
                    store._trait_defs_cache.clear()
                # Key must reset with the dict (parity with items below): a
                # stale key would serve the emptied dict as a valid catalog.
                store._trait_defs_cache_key = None
                if hasattr(store, "_item_defs_cache") and hasattr(store._item_defs_cache, "clear"):
                    store._item_defs_cache.clear()
                store._item_defs_cache_key = None
                # Portrait thumbnails are cached per (name, folder, nsfw) and
                # may point at art that changed on disk; reset like the rest.
                if hasattr(store, "_worker_portrait_cache"):
                    store._worker_portrait_cache = {}
                if hasattr(store, "refresh_traits_cache"):
                    try:
                        store.refresh_traits_cache(force=True)
                    except Exception:
                        pass
                _snap_log("SNAPSHOT: Invalidated data-listing caches (mod-aware load)")
            except Exception as _cache_e:
                renpy.log(f"SNAPSHOT: cache invalidation error (non-fatal): {_cache_e}")

            # CRITICAL (load hijack fix): suspended event/recruitment contexts are
            # TRANSIENT state from the session that saved. They are not part of
            # either the snapshot or the native save roots, so they survive in the
            # live store across a load. If NSFW restore then revives them via
            # renpy.jump("resume_content_filtered_recruitment"), loading slot B
            # would drop the player into slot A's recruitment offer - and, with
            # the old flow, re-recruit an already-rostered worker. Purge them on
            # EVERY load before any content-policy logic can see them.
            try:
                store._content_filter_suspended_event_context = None
                store._content_filter_suspended_recruitment_context = None
                if hasattr(store, "current_recruitment_event"):
                    store.current_recruitment_event = None
                if hasattr(store, "current_recruitment_worker"):
                    store.current_recruitment_worker = None
                store.in_recruitment = False
                _snap_log("SNAPSHOT: purged suspended event/recruitment transient context (load isolation)")
            except Exception as _purge_e:
                renpy.log(f"SNAPSHOT: transient context purge error (non-fatal): {_purge_e}")

            # Only use an authoritative load identity. Never guess from the last
            # manual slot: platform saves such as Android's _reload-1 do not have
            # a matching JSON sidecar and must keep their native Ren'Py state.
            slot_name = getattr(persistent, "_loading_slot", None)
            if not slot_name:
                # Some Ren'Py versions expose the actual native load name.
                # (renpy.loadsave.loadname does NOT exist in 8.3.4, so this is
                # a harmless no-op there; identity rests on _loading_slot.)
                try:
                    slot_name = getattr(renpy.loadsave, "loadname", None)
                    if slot_name:
                        _snap_log(f"SNAPSHOT: Fallback to renpy.loadsave.loadname = {slot_name}")
                except Exception:
                    pass
            store._snapshot_load_alert = None
            store._snapshot_validation_error = None
            store._snapshot_applied_slot_name = None
            store._snapshot_applied_source_path = None
            
            if slot_name:
                # Use "for_reading" so we find snapshots in legacy game/saves (backwards compatibility)
                filepath = _get_snapshot_file_path_for_reading(slot_name)
                backup_path = _get_backup_file_path_for_reading(slot_name)
                store._snapshot_load_alert = None
                
                # Read both candidates first. Exactly one complete source may be
                # applied; never layer MAIN, BACKUP or a second "partial" pass.
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
                
                selected_snap = None
                selected_path = None
                selected_label = None
                if _snapshot_is_complete_for_canonical_load(main_snap):
                    selected_snap = _cp.deepcopy(main_snap)
                    selected_path = filepath
                    selected_label = "MAIN"
                elif _snapshot_is_complete_for_canonical_load(backup_snap):
                    selected_snap = _cp.deepcopy(backup_snap)
                    selected_path = backup_path
                    selected_label = "BACKUP"

                if selected_snap is not None:
                    success = _apply_snapshot(selected_snap)
                    if success:
                        if selected_label == "MAIN":
                            store._snapshot_load_alert = None
                        else:
                            store._snapshot_load_alert = f"Snapshot BACKUP loaded for {slot_name}. Save to a new slot."
                        _upgrade_legacy_snapshot_file(filepath, selected_snap, slot_name)
                        store._snapshot_applied_slot_name = slot_name
                        store._snapshot_applied_source_path = selected_path
                        persistent._last_loaded_snapshot_slot = slot_name
                        _snap_log(f"SNAPSHOT: applied one validated source only ({selected_label}) for {slot_name}")
                    else:
                        # The selected source was pre-validated. An unexpected
                        # apply failure may already have touched the live store;
                        # fail closed instead of contaminating it with BACKUP.
                        store._snapshot_load_alert = f"Snapshot {selected_label} could not be applied for {slot_name}. Native state retained where possible; do not overwrite this slot."
                        renpy.log(f"SNAPSHOT: ERROR - validated {selected_label} apply failed for {slot_name}; refusing a second source")
                else:
                    store._snapshot_load_alert = f"No complete snapshot source for {slot_name}. Native save state retained; do not overwrite this slot."
                    renpy.log(f"SNAPSHOT: ERROR - MAIN and BACKUP lack complete state for {slot_name}; no sidecar applied")
                persistent._loading_slot = None
            else:
                _snap_log("SNAPSHOT: No marked manual slot; retaining native platform-save state.")
                store._snapshot_load_alert = None
        except Exception as e:
            renpy.log(f"SNAPSHOT: after_load callback error: {e}")
            import traceback
            renpy.log(f"SNAPSHOT: traceback: {traceback.format_exc()}")
            persistent._loading_slot = None
    
    # Register after_load callback. Registered at init -2, so it runs FIRST,
    # before save_state/options/script callbacks; anything they overwrite is
    # re-applied by the second pass in label after_load below.
    try:
        config.after_load_callbacks.append(_after_load_snapshot_callback)
    except Exception as e:
        renpy.log(f"SNAPSHOT: could not register after_load callback: {e}")

label _canonical_snapshot_load:
    $ _canonical_snapshot_loaded = _consume_canonical_snapshot_load()
    if not _canonical_snapshot_loaded:
        $ renpy.notify("The selected save could not be verified and was not loaded.")
        $ renpy.full_restart(transition=None, save=False)
    jump after_load

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
    
    # CRITICAL second pass: our snapshot callback runs FIRST in
    # config.after_load_callbacks (init -2), so the callbacks registered after
    # it (save_state sync/canonicalize, _mark_loaded, ...) and the on-load
    # rollback rewind can still overwrite restored values. Re-apply from the
    # exact snapshot source that won recovery. (The engine applies native
    # roots and `default`s BEFORE any callback runs - unfreeze in
    # renpy/rollback.py - so defaults are not the threat here.)
    python:
        try:
            # Re-apply from the exact source that the callback accepted. This is
            # critical when MAIN failed and BACKUP won recovery.
            slot_name = getattr(store, "_snapshot_applied_slot_name", None)
            filepath = getattr(store, "_snapshot_applied_source_path", None)
            if slot_name and filepath:
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
                        
                        # Available buildings (contains servant_jobs and Academy curriculum)
                        buildings_val = snap.get("available_buildings")
                        if buildings_val is not None and hasattr(buildings_val, "get"):
                            current_buildings = getattr(store, 'available_buildings', {})
                            # Check if assignments or the Academy curriculum were overwritten.
                            needs_restore = False
                            for bname, building in buildings_val.items():
                                if hasattr(building, "get"):
                                    saved_jobs = building.get("servant_jobs", {})
                                    saved_focus = building.get("training_focus", {})
                                    current_building = current_buildings.get(bname)
                                    if hasattr(current_building, "get"):
                                        current_jobs = current_building.get("servant_jobs", {})
                                        current_focus = current_building.get("training_focus", {})
                                        if len(saved_jobs) != len(current_jobs) or saved_focus != current_focus:
                                            needs_restore = True
                                            break
                                    elif saved_jobs or saved_focus:
                                        needs_restore = True
                                        break
                            
                            if needs_restore:
                                _snap_log("AFTER_LOAD: WARNING - building assignments/curriculum were overwritten! Restoring from snapshot")
                                store.available_buildings = _cp.deepcopy(buildings_val)
                                renpy.store.available_buildings = store.available_buildings
                                # The raw snapshot may carry legacy "Building_N"
                                # keys; _canonicalize_building_keys already ran in
                                # the save_state callback, so re-run it or this
                                # restore resurrects keys the workers no longer use.
                                _canon_fn = getattr(store, "_canonicalize_building_keys", None)
                                if callable(_canon_fn):
                                    _canon_fn()
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
                            "last_arena_worker_name",
                            "alchemy_unlocked",
                            "last_laboratory_use_total_days",
                            "last_alchemy_worker_name",
                            "elixir_award_granted",
                            "elixir_intro_done",
                            "arena_champion_award_granted",
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
                            "lanista_name",
                            "lanista_known_name",
                            "lanista_devotion",
                            "lanista_dominion",
                            "lanista_affection",
                            "lanista_corruption",
                            "lanista_stage",
                            "lanista_visit_count",
                            "lanista_night_visit_total_days",
                            "lanista_gate_closed_total_days",
                            "lanista_last_talk_total_days",
                            "lanista_filler_talk_index",
                            "lanista_last_story_total_days",
                            "lanista_last_question_total_days",
                            "lanista_last_gift_total_days",
                            "lanista_gifts_given",
                            "lanista_wager_intro_done",
                            "lanista_debt_finance_unlocked",
                            "lanista_debt_finance_last_day",
                            "lanista_donation_total",
                            "lanista_donation_highest_tier",
                            "lanista_favors_total",
                            "lanista_favor_highest_tier",
                            "lanista_favor_balance",
                            "lanista_favors_collected",
                            "lanista_collect_last_day",
                            "lanista_monthly_purse_last_month",
                            "lanista_spectacle_arc_step",
                            "lanista_spectacle_arc_last_day",
                            "lanista_arena_program_tier",
                            "lanista_arena_program_last_day",
                            "lanista_card_tier",
                            "lanista_card_last_day",
                            "lanista_pinup_unlocked",
                            "lanista_oilchains_unlocked",
                            "lanista_spectacle_unlocked",
                            "lanista_spectacle_pitch_done",
                            "lanista_wager_last_day",
                            "lanista_wager_loss_streak",
                            "lanista_s2_gate_fired",
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
                            "lanista_weekly_cut_last_day",
                            "arena_trial_completed",
                            "arena_successor_met",
                            "arena_lanista_feedback_pending",
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
                            "yvara_post_arc_talks_seen",
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
                            "lanista_fillers_seen",
                        ]
                        _lanista_dict_fields = [
                            "lanista_remark_choices",
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
                                if _field_name == "arena_lanista_feedback_pending":
                                    _val = _cp.deepcopy(_val)
                                setattr(store, _field_name, _val)
                                setattr(renpy.store, _field_name, _val)

                        for _field_name in _lanista_list_fields:
                            if _field_name in snap:
                                _src = snap.get(_field_name)
                                _val = _cp.deepcopy(_to_list(_src) or [])
                                setattr(store, _field_name, _val)
                                setattr(renpy.store, _field_name, _cp.deepcopy(_val))

                        for _field_name in _lanista_dict_fields:
                            if _field_name in snap:
                                _src = snap.get(_field_name)
                                _val = _cp.deepcopy(_to_dict(_src) or {})
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
        store._snapshot_applied_slot_name = None
        store._snapshot_applied_source_path = None

    # Resume the ambient BGM on load explicitly, so it does not depend on the
    # tavern_screen routing below (belt-and-suspenders per audit note #1).
    python:
        try:
            _ebp = getattr(store, "ensure_bgm_playing", None)
            if callable(_ebp):
                _ebp()
        except Exception as e:
            renpy.log(f"AFTER_LOAD: ensure_bgm_playing error: {e}")

    # Purge serialized recruitment transients whose worker is already hired
    # (old saves park on recruitment_choice_loop for the rest of the in-game
    # day, so their roots carry the finished recruitment forever). Must run
    # BEFORE the NSFW restore below so a mode flip cannot suspend-and-resurrect
    # the stale context.
    python:
        try:
            _csr = getattr(store, "clear_stale_recruitment_after_load", None)
            if callable(_csr):
                _csr("after_load")
        except Exception as e:
            renpy.log(f"AFTER_LOAD: stale recruitment cleanup error: {e}")

    # Runs here (not in after_load callbacks) so it sees the fully restored
    # save state, including defaulted vars like save_nsfw_mode.
    python:
        try:
            _after_load_restore_nsfw_mode()
        except renpy.game.JumpException:
            # set_nsfw_content_enabled may resume a suspended NSFW event via renpy.jump
            raise
        except Exception as e:
            renpy.log(f"AFTER_LOAD: NSFW mode restore error: {e}")

    # canonical load destination: Tavern. Native saves may contain a control
    # frame parked inside a selector while shared store data already contains
    # later results (secondary-context saves). Never resume that mixed stack.
    python:
        for _screen_name in (
            "choose_worker_for_arena_trial",
            "choose_worker_for_arena_special_match",
            "choose_worker_for_alchemy_craft",
            "arena_menu",
            "academy_menu",
            "map_screen",
        ):
            renpy.hide_screen(_screen_name)
        store._arena_chosen_worker = None
        store._arena_special_chosen_worker = None
        store._alchemy_chosen_worker = None
        set_save_blocked_context(None)
        renpy.log("AFTER_LOAD: discarded restored control stack; routing to canonical Tavern hub")
    # FM-SAVE-ANCHOR: after-load-end
    jump tavern_screen
