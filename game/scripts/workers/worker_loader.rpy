# worker_loader.rpy - Improved version that loads from multiple locations
init python:
    def _ensure_worker_min_traits(worker):
        """Add random traits until worker has 3-5 total. Respects gender_restriction, requires_traits, conflicts, only_assigned, nsfw.
        Applies to ALL workers including unique - recruitment unique workers should also have 3-5 traits like Buy servants."""
        traits = worker.get("traits", [])
        worker["traits"] = [t for t in (traits if isinstance(traits, list) else []) if isinstance(t, str) and t]
        target = random.randint(3, 5)
        if len(worker["traits"]) >= target:
            return
        cache = getattr(store, "_trait_def_cache", None)
        if not isinstance(cache, dict) or not cache:
            return
        nsfw_ok = getattr(persistent, "nsfw_enabled", False)
        can_assign = getattr(store, "can_assign_trait_to_worker", lambda t, w: True)
        conflicts_check = getattr(store, "trait_conflicts_with_worker", lambda t, w, c=None: False)
        meets_reqs = getattr(store, "worker_meets_trait_requirements", lambda t, w: True)
        # Option: only_traits_without_requirements = True → only traits with no gender_restriction
        only_no_reqs = getattr(persistent, "only_traits_without_requirements", False)
        possible = [
            t for t in cache.values()
            if t.get("name") and t["name"] not in worker["traits"]
            and not t.get("only_assigned", False)
            and (nsfw_ok or not t.get("nsfw", False))
            and (not only_no_reqs or not t.get("gender_restriction"))
            and can_assign(t, worker)
            and meets_reqs(t, worker["traits"])
            and not conflicts_check(t, worker["traits"], cache)
        ]
        if not possible:
            return
        random.shuffle(possible)
        needed = max(0, target - len(worker["traits"]))
        for t in possible:
            if needed <= 0:
                break
            name = t.get("name")
            if name and meets_reqs(t, worker["traits"]) and not conflicts_check(t, worker["traits"], cache):
                worker["traits"].append(name)
                needed -= 1
        if hasattr(store, "recalculate_trait_modifiers"):
            store.recalculate_trait_modifiers(worker)

    store._ensure_worker_min_traits = _ensure_worker_min_traits

    def load_workers(include_unique=False, include_encounter_only=False, for_events=False):
        """
        Load all workers from multiple locations with optional filters.
        Loads from:
        1. data/workers.json (legacy location, if exists)
        2. data/workers/*.json (all JSON files in workers folder)
           - workers_sfw_unique.json: SFW unique workers (flower-themed names)
           - workers_sfw_other.json: SFW non-unique workers (non-flower names)
           - workers_nsfw_unique.json: NSFW unique workers (flower-themed names)
           - workers_nsfw_other.json: NSFW non-unique workers (non-flower names)
           Legacy files (workers_sfw.json, workers_nsfw.json) are also supported
        
        Ensures defaults are applied to every worker and avoids duplicates.
        """
        # Preload trait cache so ensure_worker_defaults and _ensure_worker_min_traits
        # have the catalog available (avoids "Trait catalog unavailable" during load)
        if hasattr(store, "refresh_traits_cache"):
            try:
                store.refresh_traits_cache(force=True)
            except Exception:
                pass

        all_workers = []
        loaded_names = set()  # Track loaded worker names to avoid duplicates
        base_skills = {
            "Sex": 5, "Anal": 5, "BDSM": 5, "Hand": 5, "Oral": 5, "Homo": 5,
            "Special": 5, "Group": 5, "Extreme": 5, "Striptease": 5, "Combat": 5, "Clever": 5,
            "Charm": 5, "Service": 5, "Agility": 5, "Craft": 5, "Specialty 4": 5, "Specialty 5": 5,
            "Specialty 6": 5, "Specialty 7": 5, "Specialty 8": 5, "Specialty 9": 5, "Specialty 10": 5,
            "Specialty 11": 5, "Specialty 12": 5
        }
        
        # 1. Try to load from data/workers.json (legacy location)
        try:
            if renpy.loadable("data/workers.json"):
                with renpy.file("data/workers.json") as f:
                    workers_data = json.loads(f.read().decode("utf-8"))
                    for worker in workers_data:
                        worker_name = worker.get("name", "Unknown")
                        
                        # Skip if already loaded (avoid duplicates)
                        if worker_name in loaded_names:
                            continue
                        
                        # Apply NSFW/SFW mode filter
                        if not persistent.nsfw_enabled and worker.get("nsfw", False):
                            continue
                        
                        # Apply worker gender filter (Both / Only Male / Only Female)
                        if getattr(persistent, "worker_gender_filter", "both") != "both":
                            wgender = (worker.get("gender") or "").strip().lower()
                            if persistent.worker_gender_filter == "male" and wgender == "female":
                                continue
                            if persistent.worker_gender_filter == "female" and wgender == "male":
                                continue
                        
                        # Apply existing filters
                        if worker.get("unique", False) and not include_unique:
                            continue
                        if worker.get("encounter_only", False) and not include_encounter_only and not for_events:
                            continue
                        
                        # Ensure defaults are applied
                        ensure_worker_defaults(worker)
                        _ensure_worker_min_traits(worker)
                        all_workers.append(worker)
                        loaded_names.add(worker_name)
                        
                    renpy.log(f"Loaded {len([w for w in workers_data if w.get('name') in loaded_names])} workers from data/workers.json")
                
        except Exception as e:
            # File doesn't exist or error reading - this is normal
            error_msg = str(e)
            if "Refusing to open" in error_msg and "while predicting" in error_msg:
                # Silently skip during prediction phase
                pass
            else:
                renpy.log(f"data/workers.json not found or error reading: {error_msg}")
        
        # 2. Load from data/workers/*.json (current standard location)
        workers_folder_path = "data/workers"
        try:
            worker_files = [
                f for f in renpy.list_files()
                if f.startswith(workers_folder_path) and f.endswith(".json")
            ]
            
            for worker_file in worker_files:
                try:
                    if not renpy.loadable(worker_file):
                        continue
                    with renpy.file(worker_file) as f:
                        workers_data = json.loads(f.read().decode("utf-8"))
                        file_workers_loaded = 0
                        for worker in workers_data:
                            worker_name = worker.get("name", "Unknown")
                            
                            # Skip if already loaded (avoid duplicates)
                            if worker_name in loaded_names:
                                continue
                            
                            # Apply NSFW/SFW mode filter
                            if not persistent.nsfw_enabled and worker.get("nsfw", False):
                                continue
                            
                            # Apply worker gender filter (Both / Only Male / Only Female)
                            if getattr(persistent, "worker_gender_filter", "both") != "both":
                                wgender = (worker.get("gender") or "").strip().lower()
                                if persistent.worker_gender_filter == "male" and wgender == "female":
                                    continue
                                if persistent.worker_gender_filter == "female" and wgender == "male":
                                    continue
                            
                            # Apply existing filters
                            if worker.get("unique", False) and not include_unique:
                                continue
                            if worker.get("encounter_only", False) and not include_encounter_only and not for_events:
                                continue
                            
                            # Ensure defaults are applied
                            ensure_worker_defaults(worker)
                            _ensure_worker_min_traits(worker)
                            all_workers.append(worker)
                            loaded_names.add(worker_name)
                            file_workers_loaded += 1
                            
                        if file_workers_loaded > 0:
                            renpy.log(f"Loaded {file_workers_loaded} workers from {worker_file}")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "Refusing to open" in error_msg and "while predicting" in error_msg:
                        # During prediction phase, we can't load files - log and continue
                        renpy.log(f"Cannot load {worker_file} during prediction phase - will retry later")
                        pass
                    else:
                        renpy.log(f"Error loading {worker_file}: {error_msg}")
                        import traceback
                        renpy.log(f"Traceback: {traceback.format_exc()}")
                    
        except Exception as e:
            error_msg = str(e)
            if "Refusing to open" in error_msg and "while predicting" in error_msg:
                # During prediction phase, we can't load files
                renpy.log("Cannot load worker files during prediction phase - will retry when needed")
                pass
            else:
                renpy.log(f"Error accessing workers folder: {error_msg}")
                import traceback
                renpy.log(f"Traceback: {traceback.format_exc()}")
        
        if not all_workers:
            renpy.log(f"LOAD WORKERS: No workers loaded (include_unique={include_unique}, include_encounter_only={include_encounter_only})")
        return all_workers

    def get_worker_files_info():
        """
        Debug function to show what worker files are available and their status.
        """
        info = {
            "legacy_file": None,
            "folder_files": [],
            "total_workers": 0
        }
        
        # Check legacy location
        try:
            if renpy.loadable("data/workers.json"):
                with renpy.file("data/workers.json") as f:
                    workers_data = json.loads(f.read().decode("utf-8"))
                    info["legacy_file"] = {
                        "path": "data/workers.json",
                        "workers_count": len(workers_data),
                        "worker_names": [w.get("name", "Unknown") for w in workers_data]
                    }
            else:
                info["legacy_file"] = {"status": "not_found"}
        except:
            info["legacy_file"] = {"status": "not_found"}
        
        # Check folder files
        workers_folder_path = "data/workers"
        try:
            worker_files = [f for f in renpy.list_files() 
                           if f.startswith(workers_folder_path) 
                           and f.endswith(".json")]
            
            for worker_file in worker_files:
                try:
                    if renpy.loadable(worker_file):
                        with renpy.file(worker_file) as f:
                            workers_data = json.loads(f.read().decode("utf-8"))
                            info["folder_files"].append({
                                "path": worker_file,
                                "workers_count": len(workers_data),
                                "worker_names": [w.get("name", "Unknown") for w in workers_data]
                            })
                            info["total_workers"] += len(workers_data)
                    else:
                        info["folder_files"].append({
                            "path": worker_file,
                            "error": "File not loadable"
                        })
                except Exception as e:
                    error_msg = str(e)
                    if "Refusing to open" in error_msg and "while predicting" in error_msg:
                        info["folder_files"].append({
                            "path": worker_file,
                            "error": "Skipped during prediction phase"
                        })
                    else:
                        info["folder_files"].append({
                            "path": worker_file,
                            "error": error_msg
                        })
        except:
            pass
        
        return info

    def debug_worker_loading():
        """
        Debug function to print detailed information about worker loading.
        Call this from console to troubleshoot worker loading issues.
        """
        info = get_worker_files_info()
        
        print("=== WORKER FILES DEBUG INFO ===")
        
        if info["legacy_file"] and "workers_count" in info["legacy_file"]:
            print(f"Legacy file (data/workers.json): {info['legacy_file']['workers_count']} workers")
            print(f"  Workers: {', '.join(info['legacy_file']['worker_names'])}")
        else:
            print("Legacy file (data/workers.json): NOT FOUND")
        
        print(f"\nFolder files (data/workers/*.json): {len(info['folder_files'])} files")
        for file_info in info["folder_files"]:
            if "workers_count" in file_info:
                print(f"  {file_info['path']}: {file_info['workers_count']} workers")
                print(f"    Workers: {', '.join(file_info['worker_names'])}")
            else:
                print(f"  {file_info['path']}: ERROR - {file_info.get('error', 'Unknown')}")
        
        print(f"\nTotal workers available: {info['total_workers']}")
        
        # Test actual loading
        try:
            loaded_workers = load_workers(include_unique=True, include_encounter_only=True, for_events=True)
            print(f"Successfully loaded: {len(loaded_workers)} workers")
            print(f"Loaded names: {', '.join([w['name'] for w in loaded_workers])}")
        except Exception as e:
            print(f"Error during loading: {str(e)}")
        
        print("=== END DEBUG INFO ===")
        
        return info

    def workers_filtered_by_gender(workers_list):
        """
        Return a list of workers that match the persistent worker_gender_filter.
        Use this when displaying the roster so that Only Male / Only Female behaves
        as if the other gender doesn't exist.
        """
        if not workers_list:
            return workers_list
        mode = getattr(persistent, "worker_gender_filter", "both")
        if mode == "both":
            return list(workers_list)
        result = []
        for w in workers_list:
            if not hasattr(w, "get"):
                result.append(w)
                continue
            wgender = (w.get("gender") or "").strip().lower()
            if mode == "male" and wgender == "female":
                continue
            if mode == "female" and wgender == "male":
                continue
            result.append(w)
        return result

