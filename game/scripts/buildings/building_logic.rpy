# building_logic.rpy
# Cargar tipos de edificios y lógica asociada

# Load building types from JSON (main file + special_buildings: academy, arena, etc.).
# Always load from disk so we never use a truncated/corrupt building_types_json from a save.
init 100 python:
    import json
    try:
        with renpy.file("data/buildings/building_types.json") as f:
            store.building_types_json = json.load(f)
        with renpy.file("data/buildings/special_buildings.json") as f:
            special_data = json.load(f)
        special_list = special_data.get("building_types", [])
        if special_list:
            existing_ids = {bt.get("id") for bt in store.building_types_json.get("building_types", [])}
            for bt in special_list:
                if bt.get("id") not in existing_ids:
                    store.building_types_json.setdefault("building_types", []).append(bt)
                    existing_ids.add(bt.get("id"))
    except Exception as e:
        renpy.log("building_logic: Failed to load/merge building types (building_types + special_buildings): " + str(e))

init python:

    def get_building(worker):
        """Returns the building object for a worker, or None if unassigned."""
        building_name = worker.get("assigned_building", "Unassigned")
        if building_name != "Unassigned":
            return available_buildings.get(building_name, None)
        return None

    def change_building_type(building_name):
        building = available_buildings.get(building_name)
        if building:
            # Full reset to base state
            building.update({
                "base_level": 1,
                "skill": 10,  # base_level * 10
                "skill_bonus": 0,
                "reputation": 0,
                "type": None,
                "max_workers": {},
                "costs": 0
            })
            
            # Unassign all workers
            for worker in list(building["assigned_servants"]):
                unassign_worker(worker)
            
            # Clear all servant jobs
            building["servant_jobs"].clear()

    def get_building_reputation_cap(building):
        """Cap is the higher of: building level * 200, or manager level * 200 (same formula, max 1000 each)."""
        if not building:
            return 200
        building_level = building.get("base_level", 1)
        building_cap = min(1000, building_level * 200)
        # Manager(s) in this building: worker level same formula
        jobs = building.get("servant_jobs", {})
        manager_level = 0
        for w in building.get("assigned_servants", []):
            job = str(jobs.get(w.get("name", ""), "")).lower()
            if "manager" in job:
                manager_level = max(manager_level, w.get("level", 1))
        manager_cap = min(1000, manager_level * 200) if manager_level else 0
        return max(building_cap, manager_cap)

    def calculate_reputation(building_name):
        building = available_buildings[building_name]
        cap = get_building_reputation_cap(building)
        # Use stored reputation if present, otherwise calculate base
        total_reputation = building.get("reputation", building["base_level"] * 10)
        for worker in building["assigned_servants"]:
            total_reputation -= 5
            highest_skill = max(int(skill) for skill in worker["skills"].values())
            total_reputation += highest_skill // 10
        # Store and clamp to level-based cap (no growth above cap until level up)
        building["reputation"] = max(0, min(total_reputation, cap))
        return building["reputation"]

    def get_reputation_tier(reputation):
        """Returns the reputation tier name (matches dist build)."""
        rep = int(reputation)
        if rep < 50:
            return "Unknown"
        elif rep < 100:
            return "New"
        elif rep < 200:
            return "Recognized"
        elif rep < 300:
            return "Respected"
        elif rep < 400:
            return "Well-Known"
        elif rep < 500:
            return "Popular"
        elif rep < 600:
            return "Famous"
        elif rep < 700:
            return "Highly Regarded"
        elif rep < 800:
            return "Prestigious"
        elif rep < 900:
            return "Elite"
        else:
            return "Master"

    def get_reputation_bonus_stories(reputation, bonus_formula):
        """Calculate bonus stories per profession per day based on reputation and formula, with 50% reduction."""
        if not bonus_formula or bonus_formula == "0":
            return 0
        try:
            bonus = int(eval(bonus_formula, {"__builtins__": None}, {"reputation": int(reputation)}))
            bonus = int(bonus * 0.5)  # Apply same 50% reduction as events
            return bonus
        except Exception:
            return 0

    def update_reputation_from_events(building_name, event_result):
        """Adjust building reputation based on event outcome."""
        building = available_buildings[building_name]
        # Get base reputation
        calculate_reputation(building_name)  # Updates building["reputation"]
        # Apply event-based adjustment
        reputation_change = {
            "critical success": 10,
            "success": 5,
            "mediocre": 0,
            "failure": -5
        }.get(event_result.lower(), 0)
        cap = get_building_reputation_cap(building)
        # Update and clamp to level cap (no growth above cap until level up)
        building["reputation"] = max(0, min(building["reputation"] + reputation_change, cap))

    def process_manager_auto_rest(restore_only=False):
        """Sistema robusto: Usa store.workers como única fuente de verdad."""
        # 1. Agrupar trabajadores por edificio usando store.workers
        workers_by_building = {}
        for w in store.workers:
            b_name = w.get("assigned_building", "Unassigned")
            if b_name != "Unassigned":
                if b_name not in workers_by_building:
                    workers_by_building[b_name] = []
                workers_by_building[b_name].append(w)

        for b_name in store.owned_buildings:
            building = available_buildings.get(b_name)
            workers_here = workers_by_building.get(b_name, [])
            if not building or not workers_here:
                continue
            
            if "servant_jobs" not in building:
                building["servant_jobs"] = {}
            jobs = building["servant_jobs"]
            
            # 2. ¿Hay un manager trabajando aquí? (activo o en rest)
            has_manager = False
            for w in workers_here:
                job_id = str(jobs.get(w["name"], "")).lower()
                previous_prof = str(w.get("previous_profession", "")).lower()
                # Detecta "manager" o "manager (39)" en el job actual
                # o en el trabajo previo cuando está en "rest"
                if "manager" in job_id or "manager" in previous_prof:
                    has_manager = True
                    break
            
            if not has_manager:
                continue

            # 3. El manager procesa a todos los trabajadores de este edificio
            for w in workers_here:
                name = w["name"]
                current_job_raw = jobs.get(name, "")
                current_job_norm = str(current_job_raw).lower()
                
                # No procesar si no tiene trabajo asignado
                if not current_job_raw or current_job_norm == "unassigned":
                    continue

                energy = w.get("energy", 0)
                max_e = calculate_max_energy(w)
                
                # Umbrales
                rest_threshold = max_e * 0.35
                restore_threshold = max_e * 0.95
                
                # Caso A: Poner a descansar (solo si no es restore_only)
                if not restore_only and energy < rest_threshold and "rest" not in current_job_norm:
                    w["previous_profession"] = current_job_raw
                    jobs[name] = "rest"
                    renpy.log(f"AUTOREST: {name} puesto a descansar (Energía {energy}/{max_e})")
                
                # Caso B: Restaurar trabajo
                elif "rest" in current_job_norm and w.get("previous_profession"):
                    if energy >= restore_threshold:
                        jobs[name] = w["previous_profession"]
                        w["previous_profession"] = None
                        renpy.log(f"AUTOREST: {name} vuelve a {jobs[name]} (Energía {energy}/{max_e})")

    def clear_worker_autorest_state(worker):
        if worker:
            worker["previous_profession"] = None

    def set_worker_job(worker, building_name, job_id):
        if not building_name or building_name not in available_buildings:
            return
        
        # Check if worker has dict-like interface (works for dict, RevertableDict, etc.)
        # Use hasattr instead of isinstance to handle Ren'Py's RevertableDict
        if not hasattr(worker, 'get'):
            return
        
        worker_name = worker.get("name")
        if not worker_name:
            return
        
        # CRITICAL: Ensure worker_name is always a string (hashable)
        if not isinstance(worker_name, str):
            worker_name = str(worker_name)
        
        building = available_buildings[building_name]
        if "servant_jobs" not in building:
            building["servant_jobs"] = {}
        
        building["servant_jobs"][worker_name] = job_id
        renpy.restart_interaction()
