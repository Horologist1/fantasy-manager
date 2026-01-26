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


