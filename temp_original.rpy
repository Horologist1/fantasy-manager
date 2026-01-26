# building_logic.rpy
# Cargar tipos de edificios y l├│gica asociada

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

    def calculate_reputation(building_name):
        building = available_buildings[building_name]
        # Use stored reputation if present, otherwise calculate base
        total_reputation = building.get("reputation", building["base_level"] * 10)
        for worker in building["assigned_servants"]:
            total_reputation -= 5
            highest_skill = max(int(skill) for skill in worker["skills"].values())
            total_reputation += highest_skill // 10
        # Store and clamp result
        building["reputation"] = max(0, min(total_reputation, 1000))
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
        # Update stored reputation
        building["reputation"] = max(0, building["reputation"] + reputation_change)
        renpy.log(f"Updated {building_name} reputation to {building['reputation']} after {event_result}")

    def process_manager_auto_rest():
        """
        Automatic rest management when a Manager is assigned to a building.
        
        If a building has a worker with profession 'manager', the manager will:
        - Automatically assign workers with energy < 2 to 'rest'
        - Save their previous profession for restoration
        - Restore workers to their previous profession when energy recovers
        """
        for building_name in store.owned_buildings:
            building = available_buildings.get(building_name)
            if not building or not building.get("assigned_servants"):
                continue
            
            servant_jobs = building.get("servant_jobs", {})
            
            # Check if there's a manager in this building
            has_manager = False
            for worker in building["assigned_servants"]:
                worker_name = worker.get("name")
                if servant_jobs.get(worker_name, "") == "manager":
                    has_manager = True
                    renpy.log(f"Manager detected in {building_name}: {worker_name}")
                    break
            
            if not has_manager:
                continue
            
            # Manager found - process all other workers in the building
            for worker in building["assigned_servants"]:
                worker_name = worker.get("name")
                current_job = servant_jobs.get(worker_name, "")
                
                # Skip the manager themselves
                if current_job == "manager":
                    continue
                
                worker_energy = worker.get("energy", 0)
                max_energy = calculate_max_energy(worker)
                
                # Calculate percentage-based thresholds that scale with level
                rest_threshold = max_energy * 0.35  # Put to rest when below 35% energy
                restore_threshold = max_energy * 0.95  # Restore to work when at 95% energy (almost full recovery)
                
                # Initialize previous_profession field if it doesn't exist
                if "previous_profession" not in worker:
                    worker["previous_profession"] = None
                
                # Case 1: Worker has low energy and is not resting - put them to rest
                if worker_energy < rest_threshold and current_job not in ["rest", "unassigned"]:
                    # Save current profession
                    worker["previous_profession"] = current_job
                    # Change to rest
                    servant_jobs[worker_name] = "rest"
                    renpy.log(f"Manager auto-rest: {worker_name} moved to rest (energy: {worker_energy}/{max_energy} < {rest_threshold:.1f}, saved profession: {current_job})")
                
                # Case 2: Worker is resting (managed by manager) and has recovered - restore profession
                elif current_job == "rest" and worker["previous_profession"] is not None:
                    # Check if worker has recovered (energy at reasonable level)
                    if worker_energy >= restore_threshold:
                        # Restore previous profession
                        restored_profession = worker["previous_profession"]
                        servant_jobs[worker_name] = restored_profession
                        worker["previous_profession"] = None
                        renpy.log(f"Manager auto-restore: {worker_name} returned to {restored_profession} (energy: {worker_energy}/{max_energy} >= {restore_threshold:.1f})")
