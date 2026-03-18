init -1 python:
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


