init -1 python:

    def _canonicalize_building_keys():
        """Normalize all 'Building_N' keys to 'Building N' (space format) across
        available_buildings, owned_buildings, custom_names, worker assignments,
        and map_button_buildings.  Called early in after_load before any sync.
        Idempotent: no-op if data is already canonical."""
        import re
        _US_PAT = re.compile(r'^Building_(\d+)$', re.IGNORECASE)

        def _canon(key):
            if not key or not isinstance(key, str):
                return None
            m = _US_PAT.match(key.strip())
            if m:
                return "Building %s" % m.group(1)
            return None

        migrated = []

        # 1. available_buildings dict keys
        ab = getattr(store, "available_buildings", None)
        if ab is not None and hasattr(ab, "keys"):
            for old_key in list(ab.keys()):
                new_key = _canon(old_key)
                if new_key is None or new_key == old_key:
                    continue
                if new_key in ab:
                    # Both exist: merge underscore into space format
                    old_b = ab[old_key]
                    new_b = ab[new_key]
                    if hasattr(old_b, "get") and hasattr(new_b, "get"):
                        for wname, jid in (old_b.get("servant_jobs") or {}).items():
                            if wname and wname not in (new_b.get("servant_jobs") or {}):
                                new_b.setdefault("servant_jobs", {})[wname] = jid
                        existing_names = {x.get("name") for x in (new_b.get("assigned_servants") or []) if hasattr(x, "get")}
                        for w in (old_b.get("assigned_servants") or []):
                            if hasattr(w, "get") and w.get("name") and w.get("name") not in existing_names:
                                new_b.setdefault("assigned_servants", []).append(w)
                                existing_names.add(w.get("name"))
                    del ab[old_key]
                    migrated.append("available_buildings: merged '%s' into '%s'" % (old_key, new_key))
                else:
                    # Only underscore exists: rename
                    ab[new_key] = ab.pop(old_key)
                    migrated.append("available_buildings: renamed '%s' -> '%s'" % (old_key, new_key))

        # 2. owned_buildings list entries
        ob = getattr(store, "owned_buildings", None)
        if ob is not None and hasattr(ob, "__iter__") and not isinstance(ob, str):
            for i in range(len(ob)):
                new_key = _canon(ob[i])
                if new_key is not None and new_key != ob[i]:
                    migrated.append("owned_buildings: '%s' -> '%s'" % (ob[i], new_key))
                    ob[i] = new_key
            # Deduplicate
            seen = set()
            deduped = []
            for entry in ob:
                if entry not in seen:
                    seen.add(entry)
                    deduped.append(entry)
            if len(deduped) != len(ob):
                migrated.append("owned_buildings: removed %d duplicate(s)" % (len(ob) - len(deduped)))
                ob[:] = deduped

        # 3. custom_names dict keys
        cn = getattr(store, "custom_names", None)
        if cn is not None and hasattr(cn, "keys"):
            for old_key in list(cn.keys()):
                new_key = _canon(old_key)
                if new_key is None or new_key == old_key:
                    continue
                if new_key not in cn:
                    cn[new_key] = cn[old_key]
                del cn[old_key]
                migrated.append("custom_names: '%s' -> '%s'" % (old_key, new_key))

        # 4. worker["assigned_building"]
        workers = getattr(store, "workers", None) or []
        for w in workers:
            if not hasattr(w, "get"):
                continue
            ab_val = w.get("assigned_building")
            new_key = _canon(ab_val)
            if new_key is not None and new_key != ab_val:
                migrated.append("worker '%s': assigned_building '%s' -> '%s'" % (w.get("name", "?"), ab_val, new_key))
                w["assigned_building"] = new_key

        # 5. map_button_buildings dict values
        mbb = getattr(store, "map_button_buildings", None)
        if mbb is not None and hasattr(mbb, "items"):
            for btn_id in list(mbb.keys()):
                val = mbb[btn_id]
                new_key = _canon(val)
                if new_key is not None and new_key != val:
                    migrated.append("map_button_buildings[%s]: '%s' -> '%s'" % (btn_id, val, new_key))
                    mbb[btn_id] = new_key

        # Log results
        if migrated:
            renpy.log("_canonicalize_building_keys: migrated %d item(s):" % len(migrated))
            for msg in migrated:
                renpy.log("  " + msg)
        else:
            renpy.log("_canonicalize_building_keys: all keys already canonical")

    def _after_load_callback():
        """Called by Ren'Py after loading. Mark that we loaded."""
        try:
            renpy.log("SAVE_STATE: after_load callback fired")
            renpy.log(f"SAVE_STATE: Ren'Py restored - money={getattr(store, 'money', 'N/A')}, day={getattr(store, 'current_day', 'N/A')}, workers={len(getattr(store, 'workers', []))}")
            
            # Ren'Py has ALREADY restored all default variables from the save.
            # Mark that this is a loaded game.
            store.game_initialized = True
            store._just_loaded = True
            store.is_new_game = False

            # Canonicalize building keys BEFORE any validation/sync
            try:
                _canonicalize_building_keys()
            except Exception as e:
                renpy.log("SAVE_STATE: _canonicalize_building_keys error: " + str(e))
                import traceback
                renpy.log("SAVE_STATE: traceback: " + traceback.format_exc())

            # Ensure custom_names has entries for all owned buildings
            try:
                if not hasattr(store, "custom_names") or store.custom_names is None:
                    store.custom_names = {}
                for bname in getattr(store, "owned_buildings", []):
                    if bname not in store.custom_names:
                        store.custom_names[bname] = bname
            except Exception as e:
                renpy.log(f"SAVE_STATE: custom_names error: {e}")
            
            # CRITICAL: Sync building assignments after load to fix bug where buildings lose track of workers
            try:
                if hasattr(store, 'validate_and_sync_buildings'):
                    store.validate_and_sync_buildings(include_worker_refs=False)
                    renpy.log("SAVE_STATE: Called validate_and_sync_buildings after load (no worker refs)")
                else:
                    renpy.log("SAVE_STATE: WARNING - validate_and_sync_buildings not found")
            except Exception as e:
                renpy.log(f"SAVE_STATE: validate_and_sync_buildings error: {e}")

            try:
                if hasattr(store, 'sync_building_assignments_from_workers'):
                    store.sync_building_assignments_from_workers()
                    renpy.log("SAVE_STATE: Called sync_building_assignments_from_workers after load")
                else:
                    renpy.log("SAVE_STATE: WARNING - sync_building_assignments_from_workers not found")
            except Exception as e:
                renpy.log(f"SAVE_STATE: sync_building_assignments_from_workers error: {e}")

            # CRITICAL: Preload trait catalog BEFORE ensure_worker_defaults.
            # After load, store is restored from save but _trait_def_cache is not saved - it's empty.
            try:
                if hasattr(store, "refresh_traits_cache"):
                    store.refresh_traits_cache(force=True)
                    renpy.log("SAVE_STATE: Preloaded trait catalog for worker defaults")
            except Exception as e:
                renpy.log(f"SAVE_STATE: refresh_traits_cache error: {e}")

            # CRITICAL: Ensure worker defaults (including min 3-5 traits) after load.
            # Loaded workers never pass through ensure_worker_defaults otherwise.
            try:
                if hasattr(store, 'ensure_worker_defaults'):
                    for worker in getattr(store, 'workers', []):
                        store.ensure_worker_defaults(worker)
                    for worker in getattr(store, 'available_workers', []):
                        store.ensure_worker_defaults(worker)
                    renpy.log("SAVE_STATE: Applied ensure_worker_defaults to all workers after load")
                else:
                    renpy.log("SAVE_STATE: WARNING - ensure_worker_defaults not found")
            except Exception as e:
                renpy.log(f"SAVE_STATE: ensure_worker_defaults error: {e}")

            try:
                if hasattr(store, "verify_assignment_integrity"):
                    issues = store.verify_assignment_integrity("after_load_callback")
                    renpy.log(f"SAVE_STATE: assignment integrity issues after load = {issues}")
            except Exception as e:
                renpy.log(f"SAVE_STATE: verify_assignment_integrity error: {e}")
            
            renpy.log("SAVE_STATE: Load complete")
                
        except Exception as e:
            renpy.log("SAVE_STATE: after_load callback error: " + str(e))
            import traceback
            renpy.log("SAVE_STATE: traceback: " + traceback.format_exc())

    # Register after_load callback
    try:
        config.after_load_callbacks.append(_after_load_callback)
        renpy.log("SAVE_STATE: after_load callback registered")
    except Exception as e:
        renpy.log("SAVE_STATE: could not register after_load callback: " + str(e))


