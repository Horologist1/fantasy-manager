# worker_loader.rpy - Improved version that loads from multiple locations
init python:
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
        all_workers = []
        loaded_names = set()  # Track loaded worker names to avoid duplicates
        base_skills = {
            "Sex": 5, "Anal": 5, "BDSM": 5, "Hand": 5, "Oral": 5, "Homo": 5,
            "Special": 5, "Group": 5, "Extreme": 5, "Striptease": 5, "Combat": 5, "Clever": 5,
            "Charm": 5, "Wait": 5, "Agility": 5, "Craft": 5, "Specialty 4": 5, "Specialty 5": 5,
            "Specialty 6": 5, "Specialty 7": 5, "Specialty 8": 5, "Specialty 9": 5, "Specialty 10": 5,
            "Specialty 11": 5, "Specialty 12": 5
        }
        
        # 1. Try to load from data/workers.json (legacy location)
        try:
            with renpy.file("data/workers.json") as f:
                workers_data = json.loads(f.read().decode("utf-8"))
                
                for worker in workers_data:
                    worker_name = worker.get("name", "Unknown")
                    
                    # Skip if already loaded (avoid duplicates)
                    if worker_name in loaded_names:
                        renpy.log(f"Skipping duplicate worker: {worker_name} from data/workers.json")
                        continue
                    
                    # Apply NSFW/SFW mode filter
                    if not persistent.nsfw_enabled and worker.get("nsfw", False):
                        continue
                    
                    # Apply existing filters
                    if worker.get("unique", False) and not include_unique:
                        continue
                    if worker.get("encounter_only", False) and not include_encounter_only and not for_events:
                        continue
                    
                    # Ensure defaults are applied
                    ensure_worker_defaults(worker)
                    all_workers.append(worker)
                    loaded_names.add(worker_name)
                    
                renpy.log(f"Loaded {len([w for w in workers_data if w.get('name') in loaded_names])} workers from data/workers.json")
                
        except Exception as e:
            # File doesn't exist or error reading - this is normal
            renpy.log(f"data/workers.json not found or error reading: {str(e)}")
        
        # 2. Load from data/workers/*.json (current standard location)
        workers_folder_path = "data/workers"
        try:
            worker_files = [f for f in renpy.list_files() 
                           if f.startswith(workers_folder_path) 
                           and f.endswith(".json")]
            
            for worker_file in worker_files:
                try:
                    with renpy.file(worker_file) as f:
                        workers_data = json.loads(f.read().decode("utf-8"))
                        
                        file_workers_loaded = 0
                        for worker in workers_data:
                            worker_name = worker.get("name", "Unknown")
                            
                            # Skip if already loaded (avoid duplicates)
                            if worker_name in loaded_names:
                                renpy.log(f"Skipping duplicate worker: {worker_name} from {worker_file}")
                                continue
                            
                            # Apply NSFW/SFW mode filter
                            if not persistent.nsfw_enabled and worker.get("nsfw", False):
                                continue
                            
                            # Apply existing filters
                            if worker.get("unique", False) and not include_unique:
                                continue
                            if worker.get("encounter_only", False) and not include_encounter_only and not for_events:
                                continue
                            
                            # Ensure defaults are applied
                            ensure_worker_defaults(worker)
                            all_workers.append(worker)
                            loaded_names.add(worker_name)
                            file_workers_loaded += 1
                            
                        renpy.log(f"Loaded {file_workers_loaded} workers from {worker_file}")
                        
                except Exception as e:
                    renpy.log(f"Error loading {worker_file}: {str(e)}")
                    
        except Exception as e:
            renpy.log(f"Error accessing workers folder: {str(e)}")
        
        # Log summary
        renpy.log(f"Total workers loaded: {len(all_workers)}")
        renpy.log(f"Worker names: {[w['name'] for w in all_workers]}")
        
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
            with renpy.file("data/workers.json") as f:
                workers_data = json.loads(f.read().decode("utf-8"))
                info["legacy_file"] = {
                    "path": "data/workers.json",
                    "workers_count": len(workers_data),
                    "worker_names": [w.get("name", "Unknown") for w in workers_data]
                }
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
                    with renpy.file(worker_file) as f:
                        workers_data = json.loads(f.read().decode("utf-8"))
                        info["folder_files"].append({
                            "path": worker_file,
                            "workers_count": len(workers_data),
                            "worker_names": [w.get("name", "Unknown") for w in workers_data]
                        })
                        info["total_workers"] += len(workers_data)
                except Exception as e:
                    info["folder_files"].append({
                        "path": worker_file,
                        "error": str(e)
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

