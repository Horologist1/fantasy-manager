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

    def _resolve_building_by_name(building_name):
        """Find building in available_buildings by exact key or normalized match. Returns (building, actual_key) or (None, None)."""
        ab = getattr(store, "available_buildings", {})
        target_norm = _norm_building_key(building_name) if building_name else ""
        if not target_norm:
            return (None, None)
        # Try exact key first
        b = ab.get(building_name)
        if b and hasattr(b, "get"):
            return (b, building_name)
        # Search by normalized name (handles Building 1/2/3 vs Building_1/2/3, any format)
        for key, data in ab.items():
            if data and hasattr(data, "get") and _norm_building_key(key) == target_norm:
                return (data, key)
        return (None, None)

    store._resolve_building_by_name = _resolve_building_by_name

    def get_building_servants(building_name):
        """
        Returns workers assigned to a building. Uses servant_jobs + workers (assigned_building).
        Resolves building by normalized key so Building 1/2/3/N work regardless of key format.
        """
        try:
            building, _ = _resolve_building_by_name(building_name)
            if not building:
                return []
            _rw = lambda w: hasattr(w, "get") and w.get("name")
            name_to_worker = {w.get("name"): w for w in getattr(store, "workers", []) if _rw(w)}
            jobs = building.get("servant_jobs") or {}
            jobs = dict(jobs) if hasattr(jobs, "keys") else {}
            result = []
            seen = set()
            target_norm = _norm_building_key(building_name) if building_name else ""
            # 1) From servant_jobs
            for wname in list(jobs.keys()):
                if not wname or wname in seen:
                    continue
                w = name_to_worker.get(wname)
                if w:
                    result.append(w)
                    seen.add(wname)
            # 2) From workers' assigned_building (match by normalized key)
            for w in getattr(store, "workers", []):
                if not _rw(w):
                    continue
                wname = w.get("name")
                if not wname or wname in seen:
                    continue
                ab_val = w.get("assigned_building")
                if not ab_val:
                    continue
                if ab_val == building_name or (target_norm and _norm_building_key(ab_val) == target_norm):
                    result.append(w)
                    seen.add(wname)
            # 3) Fallback: assigned_servants
            for sw in (building.get("assigned_servants") or []):
                if not (hasattr(sw, "get") and sw.get("name")):
                    continue
                wname = sw.get("name")
                if wname and wname not in seen:
                    w = name_to_worker.get(wname)
                    if w:
                        result.append(w)
                        seen.add(wname)
            return result
        except Exception as e:
            renpy.log(f"get_building_servants error: {e}")
            return []

    store.get_building_servants = get_building_servants

    def _norm_building_key(key):
        """Normalize for matching: Building 1 <-> Building_1."""
        if not key:
            return ""
        s = str(key).strip()
        if "_" in s:
            parts = s.split("_")
            if len(parts) >= 2 and parts[0].lower() == "building":
                return "Building " + parts[1]
        return s

    store._norm_building_key = _norm_building_key

    def sync_assigned_servants_for_building(building_name):
        """
        Syncs building's assigned_servants from servant_jobs and workers.
        Uses _resolve_building_by_name so Building 1/2/3 vs Building_1/2/3 always match.
        """
        try:
            building, actual_key = _resolve_building_by_name(building_name)
            if not building or not hasattr(building, "get"):
                return
            owned = getattr(store, "owned_buildings", []) or []
            _norm = _norm_building_key(building_name)
            if not any(_norm_building_key(b) == _norm for b in owned):
                return
            _rw = lambda w: hasattr(w, "get") and w.get("name")
            name_to_worker = {w.get("name"): w for w in getattr(store, "workers", []) if _rw(w)}
            rebuilt = []
            seen = set()
            for wname in list((building.get("servant_jobs") or {}).keys()):
                if not wname or wname in seen:
                    continue
                w = name_to_worker.get(wname)
                if w:
                    rebuilt.append(w)
                    seen.add(wname)
                    if w.get("assigned_building", "Unassigned") != actual_key:
                        w["assigned_building"] = actual_key
            for w in getattr(store, "workers", []):
                if not _rw(w):
                    continue
                wname = w.get("name")
                if not wname or wname in seen:
                    continue
                ab_val = w.get("assigned_building")
                if ab_val == actual_key or (_norm and _norm_building_key(ab_val) == _norm):
                    rebuilt.append(w)
                    seen.add(wname)
                    if ab_val != actual_key:
                        w["assigned_building"] = actual_key
                    if wname not in (building.get("servant_jobs") or {}):
                        building.setdefault("servant_jobs", {})[wname] = "unassigned"
            building["assigned_servants"] = rebuilt
        except Exception as e:
            renpy.log(f"sync_assigned_servants_for_building error: {e}")

    def validate_and_sync_buildings(include_worker_refs=True):
        """Validates buildings and syncs assigned_servants. Never overwrites worker data."""
        try:
            for bname in getattr(store, "owned_buildings", []):
                sync_assigned_servants_for_building(bname)
        except Exception as e:
            renpy.log(f"validate_and_sync_buildings error: {e}")

    def sync_building_assignments_from_workers():
        """Syncs all buildings' assigned_servants from store.workers. Never overwrites worker data."""
        try:
            validate_and_sync_buildings()
        except Exception as e:
            renpy.log(f"sync_building_assignments_from_workers error: {e}")

    def get_worker_profession_and_building_display(worker):
        """Returns a string like 'Prostitute - Brothel: Building 1' or 'Unassigned'."""
        if not worker or not hasattr(worker, 'get'):
            return "Unassigned"
        building_name = worker.get("assigned_building", "Unassigned")
        if not building_name or building_name == "Unassigned":
            return "Unassigned"
        building = available_buildings.get(building_name)
        if not building:
            return "Unassigned"
        btype_id = building.get("type")
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        if not btype:
            parts = building_name.split('_')
            default_name = "Building " + parts[1] if len(parts) > 1 else building_name
            custom_names = getattr(store, 'custom_names', {}) or {}
            display_name = custom_names.get(building_name, default_name)
            return display_name
        parts = building_name.split('_')
        default_name = "Building " + parts[1] if len(parts) > 1 else building_name
        custom_names = getattr(store, 'custom_names', {}) or {}
        display_name = custom_names.get(building_name, default_name)
        type_name = btype.get("name", btype_id)
        building_display = type_name + ": " + display_name
        jobs = building.get("servant_jobs", {})
        job_id = jobs.get(worker.get("name", ""), "")
        if not job_id:
            return building_display
        job_lower = str(job_id).lower()
        if "rest" in job_lower:
            prof_display = "Rest"
        else:
            prof = next((p for p in btype.get("professions", []) if p.get("id") == job_id), None)
            prof_display = prof.get("name", job_id) if prof else job_id
        return prof_display + " - " + building_display

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
        """Cap = building level * 200 + manager level * 200 (additive, each max 1000).
        Need level 2 + 400 rep to reach building ceiling; manager adds on top."""
        if not building:
            return 200
        building_level = building.get("base_level", 1)
        building_cap = min(1000, building_level * 200)
        jobs = building.get("servant_jobs", {})
        manager_level = 0
        for w in building.get("assigned_servants", []):
            job = str(jobs.get(w.get("name", ""), "")).lower()
            if "manager" in job:
                manager_level = max(manager_level, w.get("level", 1))
        manager_cap = min(1000, manager_level * 200) if manager_level else 0
        return building_cap + manager_cap

    def get_effective_reputation_for_events(building):
        """Effective reputation for bonus events: min(rep, level*200) + manager level*200.
        Requires BOTH building level AND reputation; manager adds on top.
        E.g. level 2 + 400 rep = 400 from building; manager level 2 adds 400 more."""
        if not building:
            return 0
        building_level = building.get("base_level", 1)
        reputation = building.get("reputation", 0)
        building_contribution = min(reputation, min(1000, building_level * 200))
        jobs = building.get("servant_jobs", {})
        manager_level = 0
        for w in building.get("assigned_servants", []):
            job = str(jobs.get(w.get("name", ""), "")).lower()
            if "manager" in job:
                manager_level = max(manager_level, w.get("level", 1))
        manager_contribution = min(1000, manager_level * 200) if manager_level else 0
        return building_contribution + manager_contribution

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

    def _get_first_profession_id_for_building(building):
        """Primera profesión del edificio que no sea Rest (para fallback en partidas antiguas sin previous_profession)."""
        if not building:
            return None
        btype_id = building.get("type")
        if not btype_id:
            return None
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        if not btype:
            return None
        for prof in btype.get("professions", []):
            pid = prof.get("id", "")
            if pid and "rest" not in str(pid).lower():
                return pid
        return None

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
            
            # 2. Procesar todos los edificios: poner a descansar a los de poca energía y restaurar a los que ya descansaron.
            # (Antes se exigía un manager en el edificio; se quitó para que siempre se pongan a descansar / vuelvan al trabajo.)

            # 3. Procesar a todos los trabajadores de este edificio
            for w in workers_here:
                name = w.get("name")
                if not name:
                    continue
                current_job_raw = jobs.get(name, "")
                current_job_norm = str(current_job_raw).lower()
                
                # No procesar si no tiene trabajo asignado
                if not current_job_raw or current_job_norm == "unassigned":
                    continue

                # Forzar numérico: partidas antiguas o saves pueden tener energy como string y romper la comparación
                try:
                    energy = int(float(w.get("energy", 0) or 0))
                except (TypeError, ValueError):
                    energy = 0
                try:
                    max_e = int(calculate_max_energy(w))
                except (TypeError, ValueError):
                    continue
                if max_e <= 0:
                    continue

                # Umbrales
                rest_threshold = max_e * 0.35
                restore_threshold = max_e * 0.95
                
                # Caso A: Poner a descansar (solo si no es restore_only)
                if not restore_only and energy < rest_threshold and "rest" not in current_job_norm:
                    w["previous_profession"] = current_job_raw
                    jobs[name] = "rest"
                    renpy.log(f"AUTOREST: {name} puesto a descansar (Energía {energy}/{max_e})")
                
                # Caso B: Restaurar trabajo (con fallback para partidas antiguas sin previous_profession)
                elif "rest" in current_job_norm and energy >= restore_threshold:
                    prev = w.get("previous_profession")
                    if prev:
                        jobs[name] = prev
                        w["previous_profession"] = None
                        renpy.log(f"AUTOREST: {name} vuelve a {jobs[name]} (Energía {energy}/{max_e})")
                    else:
                        # Partida antigua o worker puesto a Rest sin guardar previous_profession: usar primera profesión del edificio
                        first_prof = _get_first_profession_id_for_building(building)
                        if first_prof:
                            jobs[name] = first_prof
                            renpy.log(f"AUTOREST: {name} sin previous_profession -> restaurado a {first_prof} (Energía {energy}/{max_e})")

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
        
        job_id_norm = str(job_id).lower() if job_id else ""
        is_rest = "rest" in job_id_norm
        current_job = building["servant_jobs"].get(worker_name, "")
        current_norm = str(current_job).lower() if current_job else ""
        
        # When player assigns Rest: save current job so process_manager_auto_rest(restore_only=True) can restore it later
        if is_rest and current_job and "rest" not in current_norm:
            worker["previous_profession"] = current_job
        # When player assigns a non-Rest job: clear auto-rest state so we don't override their choice
        if not is_rest:
            clear_worker_autorest_state(worker)
        
        building["servant_jobs"][worker_name] = job_id
        renpy.restart_interaction()
