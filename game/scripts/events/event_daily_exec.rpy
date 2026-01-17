# event_daily_exec.rpy

    # ==============================
    # NEW: Updated process_daily_events() function
    # ==============================

init python:

    def process_daily_events():
        global daily_report, manager_inventory
        renpy.log("process_daily_events() starting...")
        
        # Clear image cache for new Daily Report
        clear_image_cache()

        # Defensive: ensure assigned_servants are linked to live worker objects
        try:
            _relink_assigned_servants_to_store_workers()
        except Exception as e:
            renpy.log("RELINK in process_daily_events error: " + str(e))

        # Precompute name -> store worker map for identity enforcement
        name_to_store = {w.get("name"): w for w in store.workers}

        # Debug snapshot of energies y sincronización con store.workers
        try:
            renpy.log("ENERGY SNAPSHOT: begin daily events")
            for bname in store.owned_buildings:
                b = available_buildings.get(bname)
                if not isinstance(b, dict):
                    continue
                for aw in b.get("assigned_servants", []) or []:
                    n = aw.get("name")
                    sw = name_to_store.get(n)
                    # Si el objeto asignado no es el mismo que el de store, sincroniza energía/salud
                    if sw is not None and aw is not sw:
                        aw["energy"] = sw.get("energy", aw.get("energy", 0))
                        aw["health"] = sw.get("health", aw.get("health", 0))
                    renpy.log(f"  {bname}: {n} assigned energy={aw.get('energy')} id={id(aw)} | store energy={sw.get('energy') if sw else 'N/A'} id={id(sw) if sw else 'N/A'} job={b.get('servant_jobs', {}).get(n)}")
        except Exception as e:
            renpy.log("ENERGY SNAPSHOT error: " + str(e))

        for building_name in store.owned_buildings:
            building = available_buildings.get(building_name)
            if not building:
                renpy.log(f"DAILY: Skipping {building_name} - not found in available_buildings")
                continue
            # Debug building assignment snapshot
            try:
                assigned_names = [w.get("name") for w in (building.get("assigned_servants") or [])]
                renpy.log(f"DAILY: Building {building_name} type={building.get('type')} assigned={assigned_names}")
                renpy.log(f"DAILY: servant_jobs={ {k:v for k,v in (building.get('servant_jobs') or {}).items()} }")
            except Exception as e:
                renpy.log("DAILY: assignment snapshot error: " + str(e))
            if not building.get("assigned_servants"):
                renpy.log(f"DAILY: {building_name} has no assigned_servants -> skipping")
                continue

            btype_id = building.get("type")
            if not btype_id:
                continue

            btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), None)
            if not btype:
                continue

            # Update building costs to include skill bonus
            bonus_cost = (building["skill_bonus"] // 10) * 100
            renpy.log(f"Building {building_name} previous costs: {building.get('costs', 0)}, adding skill bonus: {bonus_cost}")
            building["costs"] = building.get("costs", 0) + bonus_cost
            renpy.log(f"Building {building_name} new costs after skill bonus: {building['costs']}")

            # Process "rest" workers ONCE per building, before processing other professions
            # Find the rest profession definition (should only be one, but we'll take the first)
            rest_profession = None
            for prof in btype.get("professions", []):
                if prof.get("id") == "rest":
                    rest_profession = prof
                    break
            
            if rest_profession:
                # Get all workers in rest for this building, ensuring no duplicates
                workers_in_rest = []
                seen_worker_names = set()
                for w in building["assigned_servants"]:
                    worker_name = w.get("name", "")
                    job = building["servant_jobs"].get(worker_name, "").lower()
                    if job == "rest" and worker_name not in seen_worker_names:
                        workers_in_rest.append(w)
                        seen_worker_names.add(worker_name)
                        renpy.log(f"DAILY: Found worker in rest: {worker_name} in {building_name}")
                
                # Process each worker in rest exactly once
                for worker in workers_in_rest:
                    stories = rest_profession.get("daily_stories", [])
                    if not stories:
                        renpy.log(f"DAILY: No daily_stories for rest profession, skipping")
                        continue
                    chosen_story = random.choice(stories)
                    full_description = chosen_story.get("description", "")
                    outcome = "Rest"

                    if "consequences" in chosen_story:
                        cons = chosen_story["consequences"].get("success", {})
                        if cons:
                            # Apply energy and health changes
                            if "energy" in cons:
                                old_energy = worker["energy"]
                                worker["energy"] = min(calculate_max_energy(worker), max(0, worker["energy"] + cons["energy"]))
                                renpy.log(f"Event: {worker['name']} energy {old_energy} -> {worker['energy']} (change: {cons['energy']}), Worker ID: {id(worker)}")
                            if "health" in cons:
                                old_health = worker["health"]
                                worker["health"] = min(calculate_max_health(worker), max(0, worker["health"] + cons["health"]))
                                renpy.log(f"Event: {worker['name']} health {old_health} -> {worker['health']} (change: {cons['health']}), Worker ID: {id(worker)}")

                            # Apply joy changes
                            if "joy" in cons:
                                old_joy = worker["joy"]
                                apply_attribute_change(worker, "joy", cons["joy"])
                                renpy.log(f"Event: {worker['name']} joy {old_joy} -> {worker['joy']} (change: {cons['joy']}), Worker ID: {id(worker)}")

                            # Apply rebelliousness changes
                            if "rebelliousness" in cons:
                                old_rebelliousness = worker["rebelliousness"]
                                apply_attribute_change(worker, "rebelliousness", cons["rebelliousness"])
                                renpy.log(f"Event: {worker['name']} rebelliousness {old_rebelliousness} -> {worker['rebelliousness']} (change: {cons['rebelliousness']}), Worker ID: {id(worker)}")

                            # Apply romance changes
                            if "romance" in cons:
                                old_romance = worker["romance"]
                                apply_attribute_change(worker, "romance", cons["romance"])
                                renpy.log(f"Event: {worker['name']} romance {old_romance} -> {worker['romance']} (change: {cons['romance']}), Worker ID: {id(worker)}")

                            # Apply relationship changes
                            if "relationship" in cons:
                                old_relationship = worker["relationship"]
                                apply_attribute_change(worker, "relationship", cons["relationship"])
                                renpy.log(f"Event: {worker['name']} relationship {old_relationship} -> {worker['relationship']} (change: {cons['relationship']}), Worker ID: {id(worker)}")
                    report_entry = {
                        "building": building_name,
                        "profession": rest_profession.get("name", "Rest"),
                        "worker_name": worker.get("name", "Unknown"),
                        "worker": worker,
                        "event_data": chosen_story,
                        "report": chosen_story.get("report", "Resting"),
                        "description": full_description,
                        "result": outcome,
                        "earnings": 0,
                        "used_skill": "N/A",
                        "roll": "N/A",
                        "trait_roll": None,
                        "trait_success_messages": [],
                        "group_event": False,
                        "loot": [],
                        "story_image": get_event_image(worker, chosen_story, outcome="success")
                    }
                    daily_report.append(report_entry)

            for profession in btype.get("professions", []):
                # Skip rest profession as it's already processed above
                if profession["id"] == "rest":
                    continue

                assigned_workers = [
                    name_to_store.get(w.get("name"), w)
                    for w in building["assigned_servants"]
                    if (building.get("servant_jobs") or {}).get(w.get("name"), "") == profession["id"]
                ]
                # Keep building list referencing canonical store objects to avoid drift (dedupe by name)
                _deduped_assigned = []
                _seen_names = set()
                for _w in building.get("assigned_servants", []) or []:
                    _wname = _w.get("name")
                    if _wname in _seen_names:
                        continue
                    _deduped_assigned.append(name_to_store.get(_wname, _w))
                    if _wname:
                        _seen_names.add(_wname)
                building["assigned_servants"] = _deduped_assigned
                renpy.log(f"DAILY: Profession {profession['id']} -> assigned_workers={ [w.get('name') for w in assigned_workers] }")
                eligible_workers = [w for w in assigned_workers]  # No energy filter
                if not eligible_workers:
                    renpy.log(f"DAILY: Profession {profession['id']} has 0 eligible workers in {building_name}")
                    continue

                daily_story_count = profession.get("daily_story_count", 0)
                if hasattr(daily_story_count, "get"):
                    base_events = int(daily_story_count.get("base", 0))
                    bonus_formula = daily_story_count.get("bonus_formula", "0")
                    try:
                        bonus = int(eval(bonus_formula, {"__builtins__": None}, {"reputation": building.get("reputation", 0)}))
                    except Exception:
                        bonus = 0
                    # Balance tweaks: reduce base by 1 if >=2, and soften reputation bonus by 50%
                    if base_events >= 2:
                        base_events = max(1, base_events - 1)
                    bonus = int(bonus * 0.5)
                    events_per_worker = max(1, base_events + bonus)
                else:
                    events_per_worker = int(daily_story_count)

                for worker in eligible_workers:
                    renpy.log(f"Processing worker: {worker['name']}, ID: {id(worker)}")
                    # Check for rebelliousness
                    rebelliousness = worker.get("rebelliousness", 50)
                    if rebelliousness > 80 and random.random() < 0.2:  # 20% chance to refuse work
                        # Apply rebelliousness decay based on comfort level
                        comfort = worker.get("comfort_level", 1)
                        rebelliousness_reduction = comfort * 3
                        old_rebelliousness = worker["rebelliousness"]
                        apply_attribute_change(worker, "rebelliousness", -rebelliousness_reduction)
                        renpy.log(f"Rebelliousness decay: {worker['name']} refused work, rebelliousness {old_rebelliousness} -> {worker['rebelliousness']} (comfort {comfort} × 3 = -{rebelliousness_reduction})")
                        
                        report_entry = {
                            "building": building_name,
                            "profession": profession.get("name", "Unknown Profession"),
                            "worker_name": worker.get("name", "Unknown"),
                            "worker": worker,
                            "event_data": {"story_image": "Refuse"},
                            "report": f"Rebellious, {worker['name']} refused to work",
                            "description": f"Rebellious, {worker['name']} refused to work and spent the day doing other activities. However, the comfortable conditions helped calm their rebellious spirit. (-{rebelliousness_reduction} Rebelliousness from comfort)",
                            "result": "Refused",
                            "earnings": 0,
                            "used_skill": "N/A",
                            "roll": "N/A",
                            "trait_roll": None,
                            "trait_success_messages": [],
                            "group_event": False,
                            "loot": [],
                            "story_image": get_event_image(worker, {"story_image": "Refuse"}, outcome="refused")
                        }
                        daily_report.append(report_entry)
                        continue  # Skip further processing for this worker

                    # Initialize failed_rolls counter for joy adjustment
                    worker["failed_rolls"] = worker.get("failed_rolls", 0)

                    # Track the number of events processed
                    processed_events = 0
                    for _ in range(events_per_worker):
                        # Check if worker has enough energy to perform another event
                        if worker["energy"] <= 0:
                            renpy.log(f"{worker['name']} has no energy left. Skipping further events.")
                            break

                        stories = profession.get("daily_stories", [])
                        if not stories:
                            continue
                        
                        # Filter stories by worker gender requirement
                        worker_gender = worker.get("gender", "")
                        compatible_stories = []
                        for story in stories:
                            story_gender_req = story.get("worker_gender_requirement", None)
                            if story_gender_req is None or story_gender_req == worker_gender:
                                compatible_stories.append(story)
                        
                        if not compatible_stories:
                            renpy.log(f"No compatible stories found for {worker['name']} (gender: {worker_gender})")
                            continue
                        
                        chosen_story = select_weighted_event(compatible_stories)
                        if not chosen_story:
                            continue

                        skill_options = chosen_story.get("skill_options", [])
                        if skill_options:
                            selected_skill = random.choice(skill_options)
                            total_skill = sum(calculate_skill_with_traits(worker, s) for s in skill_options)  # Use skill names directly
                            count_skill = len(skill_options)
                            effective_skill = total_skill // count_skill if count_skill > 0 else 0
                        else:
                            selected_skill = None
                            effective_skill = 0

                        # Apply difficulty modifier from story
                        difficulty_modifier = chosen_story.get("difficulty_modifier", 0)
                        adjusted_skill = max(0, effective_skill + difficulty_modifier)

                        # Roll outcome with proper skill-based logic
                        roll = random.randint(1, 100)
                        if roll < 50:
                            worker["failed_rolls"] = worker.get("failed_rolls", 0) + 1

                        # Critical success: 10% of skill, max 25%
                        crit_pct = min(25, max(1, int(round(0.10 * adjusted_skill))))
                        
                        if roll <= crit_pct:
                            outcome = "Critical Success"
                            reputation_change = 10
                        elif roll <= adjusted_skill:
                            # Success: roll <= skill (the core mechanic)
                            outcome = "Success"
                            reputation_change = 5
                        elif roll <= adjusted_skill + 10:
                            # Mediocre: just above skill (skill+1 to skill+10)
                            outcome = "Mediocre"
                            reputation_change = 0
                        else:
                            # Failure: everything above skill+10
                            outcome = "Failure"
                            reputation_change = -5
                        outcome_key = outcome.lower().replace(" ", "_")

                        earnings_formula = chosen_story.get("earnings", {}).get(outcome_key, "0")
                        env = {"skill": effective_skill, "level": worker.get("level", 1)}
                        try:
                            earnings = eval(earnings_formula, {"__builtins__": None}, env)
                        except Exception:
                            earnings = 0

                        # Outcome-based earnings scaling and stronger penalties
                        if outcome == "Critical Success":
                            earnings = int(earnings * 0.65)
                        elif outcome == "Success":
                            earnings = int(earnings * 0.75)
                        elif outcome == "Mediocre":
                            earnings = int(earnings * 0.75)
                        else:  # Failure
                            if earnings < 0:
                                earnings = int(earnings * 2)  # increase penalty
                            elif earnings == 0:
                                earnings = -10

                        # Trait bonus
                        trait_bonus = 0
                        trait_success_messages = []
                        trait_roll = None
                        if outcome in ["Success", "Critical Success"]:
                            # Always count successes towards leveling
                            worker["success_count"] = worker.get("success_count", 0) + 1
                            trait_roll = random.random()
                            if trait_roll < 0.5:
                                for trait in worker.get("traits", []):
                                    if trait in chosen_story.get("relevant_traits", []):
                                        tb_formula = chosen_story.get("trait_bonus", "0")
                                        try:
                                            bonus_val = eval(tb_formula, {"__builtins__": None}, {"level": worker.get("level", 1)})
                                        except Exception:
                                            bonus_val = 0
                                        # Scale down trait bonuses to reduce snowball
                                        bonus_val = int(bonus_val * 0.3)
                                        trait_bonus += bonus_val
                                        trait_success_messages.append(
                                            chosen_story.get("trait_success", "").format(worker_name=worker["name"], trait=trait)
                                            + f" (+${bonus_val})"
                                        )
                                # Counted once above; do not double-increment
                        earnings += trait_bonus
                        
                        # Apply trait earnings multipliers
                        earnings = calculate_earnings(worker, earnings)
                        
                        # Log individual earnings for debugging
                        renpy.log(f"EARNINGS DEBUG: {worker['name']} earned ${earnings} (outcome: {outcome}, skill: {effective_skill}, roll: {roll})")

                        # Apply consequences
                        if "consequences" in chosen_story:
                            cons = chosen_story["consequences"].get(outcome_key, {})
                            if cons:
                                # Apply energy and health changes
                                if "energy" in cons:
                                    old_energy = worker["energy"]
                                    worker["energy"] = min(calculate_max_energy(worker), max(0, worker["energy"] + cons["energy"]))
                                    renpy.log(f"Event: {worker['name']} energy {old_energy} -> {worker['energy']} (change: {cons['energy']}), Worker ID: {id(worker)}")
                                if "health" in cons:
                                    old_health = worker["health"]
                                    worker["health"] = min(calculate_max_health(worker), max(0, worker["health"] + cons["health"]))
                                    renpy.log(f"Event: {worker['name']} health {old_health} -> {worker['health']} (change: {cons['health']}), Worker ID: {id(worker)}")

                                # Apply joy changes
                                if "joy" in cons:
                                    old_joy = worker["joy"]
                                    apply_attribute_change(worker, "joy", cons["joy"])
                                    renpy.log(f"Event: {worker['name']} joy {old_joy} -> {worker['joy']} (change: {cons['joy']}), Worker ID: {id(worker)}")

                                # Apply rebelliousness changes
                                if "rebelliousness" in cons:
                                    old_rebelliousness = worker["rebelliousness"]
                                    apply_attribute_change(worker, "rebelliousness", cons["rebelliousness"])
                                    renpy.log(f"Event: {worker['name']} rebelliousness {old_rebelliousness} -> {worker['rebelliousness']} (change: {cons['rebelliousness']}), Worker ID: {id(worker)}")

                                # Apply romance changes
                                if "romance" in cons:
                                    old_romance = worker["romance"]
                                    apply_attribute_change(worker, "romance", cons["romance"])
                                    renpy.log(f"Event: {worker['name']} romance {old_romance} -> {worker['romance']} (change: {cons['romance']}), Worker ID: {id(worker)}")

                                # Apply relationship changes
                                if "relationship" in cons:
                                    old_relationship = worker["relationship"]
                                    apply_attribute_change(worker, "relationship", cons["relationship"])
                                    renpy.log(f"Event: {worker['name']} relationship {old_relationship} -> {worker['relationship']} (change: {cons['relationship']}), Worker ID: {id(worker)}")

                    # Build description
                        if selected_skill:
                            # Use skill name directly
                            skill_for_desc = selected_skill
                        else:
                            skill_for_desc = "No Skill"
                        base_description = chosen_story.get("descriptions", {}).get(outcome_key, "No description available").format(worker_name=worker["name"], skill=skill_for_desc)
                        full_description = base_description
                        if trait_success_messages:
                            full_description += "\n" + "\n".join(trait_success_messages)
                        full_description += "\n\n{{color=#006600}}{{size=18}}(Skill roll: {} - {}){{/size}}{{/color}}".format(roll, outcome)

                        # Use skill name directly
                        if selected_skill is not None:
                            used_skill = selected_skill
                        else:
                            used_skill = "N/A"
                        if selected_skill:
                            # Use skill name directly
                            if "skill_uses" not in worker:
                                worker["skill_uses"] = {}
                            old_uses = worker["skill_uses"].get(selected_skill, 0)
                            worker["skill_uses"][selected_skill] = old_uses + 1
                            renpy.log(f"SKILL USE: {worker.get('name', 'Unknown')} used {selected_skill} (now {worker['skill_uses'][selected_skill]} uses)")

                        # Update building reputation, capped at 1000
                        new_reputation = building["reputation"] + reputation_change
                        building["reputation"] = max(0, min(new_reputation, 1000))
                        renpy.log(f"Updated {building_name} reputation to {building['reputation']} after {outcome}")

                        report_entry = {
                            "building": building_name,
                            "profession": profession.get("name", "Unknown Profession"),
                            "worker_name": worker.get("name", "Unknown"),
                            "worker": worker,
                            "event_data": chosen_story,
                            "report": chosen_story.get("report", ""),
                            "description": full_description,
                            "result": outcome,
                            "earnings": earnings,
                            "used_skill": used_skill,
                            "roll": roll,
                            "trait_roll": trait_roll,
                            "trait_success_messages": trait_success_messages,
                            "group_event": False,
                            "loot": [],
                            "story_image": get_event_image(worker, chosen_story, outcome=outcome_key, skill_name=used_skill)
                        }

                        if outcome in ["Success", "Critical Success"]:
                            if "loot" in chosen_story:
                                loot_data = chosen_story["loot"]
                                num_rolls = loot_data.get("rolls", 0)
                                if num_rolls > 0:
                                    loot = roll_loot(num_rolls)
                                    report_entry["loot"] = loot
                                    for item_id in loot:
                                        add_item_to_inventory(manager_inventory, item_id)
                                
                                # Monster worker loot handling
                                if "monster_worker" in loot_data:
                                    chance = loot_data["monster_worker"].get("chance", 1.0)
                                    filters = loot_data["monster_worker"].get("filters", {"monster": True})
                                    if random.random() <= chance:
                                        looted_worker = loot_monster_worker(filters)
                                        if looted_worker:
                                            # Add the worker to the roster immediately
                                            ensure_worker_defaults(looted_worker)
                                            looted_worker["source"] = "recruited"
                                            store.workers.append(looted_worker)
                                            
                                            # Update the report
                                            report_entry["description"] += f"\n\n{{color=#00ff00}}Captured {looted_worker['name']}!{{/color}}"
                                            report_entry["loot"].append(f"Monster Worker: {looted_worker['name']}")
                                            renpy.notify(f"Captured {looted_worker['name']}!")
                        daily_report.append(report_entry)
                        processed_events += 1

        renpy.log(f"process_daily_events() finished. Report entries: {len(daily_report)}")
        return None # Function finished successfully

# ==============================
    # process_next_day() function
    # ==============================
    def _relink_assigned_servants_to_store_workers():
        """Ensure buildings' assigned_servants reference the exact dict objects in store.workers"""
        try:
            name_to_worker = {w.get("name"): w for w in store.workers}
            for bname in store.owned_buildings:
                b = available_buildings.get(bname)
                if not isinstance(b, dict):
                    continue
                assigned = b.get("assigned_servants", []) or []
                relinked = []
                seen_names = set()
                for sw in assigned:
                    wname = sw.get("name") if isinstance(sw, dict) else None
                    if wname in seen_names:
                        renpy.log(f"RELINK: duplicate assigned_servant '{wname}' in {bname}, skipping")
                        continue
                    relinked.append(name_to_worker.get(wname, sw))
                    if wname:
                        seen_names.add(wname)
                b["assigned_servants"] = relinked
        except Exception as e:
            renpy.log("RELINK: error while relinking assigned_servants: " + str(e))

    def process_next_day():
        # Ensure necessary variables are global (removed filtered_building)
        global daily_report, displayed_workers, money, can_recruit_today, available_workers, daily_spawns

        # Check and update trait durations
        check_trait_durations()
        # Advance the date first
        advance_date()
        
        # Check if it's Monday and start BGM if needed
        check_and_start_monday_bgm()

        displayed_workers = []  # Clear displayed_workers at the start
        can_recruit_today = True  # Reset recruitment flag each day
        daily_spawns = 0  # Reset daily spawns counter

        # --- ENSURE REPORT LIST IS CLEARED HERE ---
        daily_report = []
        renpy.log("Cleared daily_report for the new day.")
        # --- END CLEAR ---

        total_income = 0 # Initialize income for the day
        total_building_costs = 0  # Track total building costs

        # Update building skills based on level, cap level at 5
        for building_name in store.owned_buildings:
            building = available_buildings.get(building_name)
            if building:
                # Cap base_level at 5
                building["base_level"] = min(building["base_level"], 5)
                building["skill"] = building["base_level"] * 10  # Update skill based on level
                # Cap reputation at 1000
                building["reputation"] = min(building["reputation"], 1000)
                # Reset building costs each day
                building["costs"] = 0
                renpy.log(f"Reset costs for {building_name} to 0")

                # Add base maintenance cost (100 per building level)
                base_cost = 100 * building["base_level"]
                building["costs"] += base_cost

                # Add worker costs based on comfort level (increased) and upkeep per worker (differs by source)
                if "assigned_servants" in building:
                    comfort_costs = sum(worker.get("comfort_level", 1) * 20 for worker in building["assigned_servants"])  # 20x comfort
                    upkeep_costs = 0
                    for w in building["assigned_servants"]:
                        source = w.get("source", "bought")
                        level = w.get("level", 1)
                        if source == "recruited":
                            upkeep_costs += (20 + 3 * level)
                        else:
                            upkeep_costs += (5 + 1 * level)
                    worker_costs = comfort_costs + upkeep_costs
                    building["costs"] += worker_costs
                    renpy.log(f"Added base cost {base_cost} + comfort {comfort_costs} + upkeep {upkeep_costs} to {building_name}, total: {building['costs']}")

        # Regenerate energy/health and update stats BEFORE events
        for worker in store.workers:
            old_health = worker["health"]
            health_regen = worker.get("level", 1) + calculate_health_regeneration(worker)
            worker["health"] = min(worker["health"] + health_regen, calculate_max_health(worker))

            old_energy = worker["energy"]
            energy_regen = worker.get("level", 1)
            worker["energy"] = min(worker["energy"] + energy_regen, calculate_max_energy(worker))

            if persistent.nsfw_enabled:
                regenerate_libido(worker)

            worker["failed_rolls"] = 0

            comfort = worker.get("comfort_level", 1)
            romance = worker.get("romance", 0)
            relationship = worker.get("relationship", 10 + comfort)
            rebelliousness = worker.get("rebelliousness", 50)
            joy = worker.get("joy", 50)

            if romance > 80 and rebelliousness > 80:
                set_attribute_with_caps(worker, "rebelliousness", 20)
            if romance > 80 and joy < 20:
                set_attribute_with_caps(worker, "joy", 50)
            if relationship > 80 and joy < 20:
                set_attribute_with_caps(worker, "joy", 80)

            minimum_relationship = 10 + comfort
            if relationship < minimum_relationship:
                set_attribute_with_caps(worker, "relationship", minimum_relationship)
            else:
                set_attribute_with_caps(worker, "relationship", relationship)

            comfort_desired = worker.get("comfort_desired", 1)
            comfort_bonus = max(0, comfort - comfort_desired)
            if comfort_bonus > 0:
                old_joy = worker["joy"]
                apply_attribute_change(worker, "joy", comfort_bonus)
                renpy.log(f"Comfort bonus: {worker['name']} joy {old_joy} -> {worker['joy']} (bonus: {comfort_bonus}, comfort: {comfort}, desired: {comfort_desired})")

        # Ensure assigned_servants reference live worker objects before processing events
        _relink_assigned_servants_to_store_workers()
        
        # Process manager auto-rest functionality
        try:
            process_manager_auto_rest()
            renpy.log("Manager auto-rest processing completed")
        except Exception as e:
            renpy.log(f"Error in manager auto-rest: {e}")
        # Process daily events (THIS POPULATES THE GLOBAL daily_report)
        process_daily_events_result = process_daily_events()
        # Check if process_daily_events triggered an early game over (e.g., if it were to return "game_over")
        if process_daily_events_result == "game_over":
            return "game_over" # Propagate game over if needed

        # --- CALCULATE TOTAL INCOME AND COSTS *AFTER* ALL EVENTS ---
        total_income = sum(report.get("earnings", 0) for report in daily_report)
        renpy.log(f"Calculated total income from daily_report: {total_income}")
        
        # Log detailed breakdown of all earnings
        renpy.log("EARNINGS BREAKDOWN:")
        for i, report in enumerate(daily_report):
            earnings = report.get("earnings", 0)
            worker_name = report.get("worker_name", "Unknown")
            outcome = report.get("result", "Unknown")
            renpy.log(f"  Entry {i+1}: {worker_name} - ${earnings} ({outcome})")

        for building_name in store.owned_buildings:
            building = available_buildings.get(building_name)
            if building:
                # Skill bonus cost is added during process_daily_events, sum final costs here
                renpy.log(f"Final costs for {building_name} after process_daily_events: {building.get('costs', 0)}")
                total_building_costs += building.get('costs', 0)
        # --- END INCOME/COST CALCULATION ---

        # Check for dead workers
        dead_workers = check_worker_health()
        if dead_workers > 0:
            renpy.say(None, f"{dead_workers} died and had to be let go.")

        # Update skill levels and worker levels
        update_skill_levels()
        update_worker_levels()

        # Reload available workers unconditionally
        available_workers = load_buy_workers()
        renpy.log(f"Reloaded available_workers: {[w['name'] for w in available_workers]}")

        # Update displayed_workers using the proper function that handles JSON exhaustion
        update_displayed_workers()
        renpy.log(f"Updated displayed_workers: {[w['name'] for w in displayed_workers]}")

        # Update money BEFORE events so events can modify the updated amount
        old_money = money
        money += total_income # Apply calculated income
        money -= total_building_costs  # Subtract calculated building costs
        money = int(money) # Ensure money is an integer
        
        # Log money changes for debugging
        renpy.log(f"MONEY CHANGE: ${old_money} + ${total_income} - ${total_building_costs} = ${money}")
        
        # Check objective completion after money change (for Objective 4: 5000 coins)
        if hasattr(store, 'tutorial_active') and store.tutorial_active:
            try:
                check_objective_completion()
            except Exception as e:
                renpy.log(f"Error checking objective completion after daily money update: {e}")
        
        # Check for daily revenue achievement (Objective 15)
        if total_income >= 10000 and not store.event_flags.get("daily_revenue_10k_achieved", False):
            store.event_flags["daily_revenue_10k_achieved"] = True
            renpy.log("ACHIEVEMENT: Daily revenue 10k achieved!")

        # Check for random events only if at least one worker has an active profession
        has_active_professions = any_worker_has_active_profession()
        
        # Load all events first to check for priority/guaranteed events
        all_events = load_events_from_folder("data/events", exclude_prefix="event_recruit_")
        renpy.log(f"Loaded {len(all_events)} potential non-recruit events.")

        # Get active building types
        active_building_types = [b["type"] for b in available_buildings.values() if b.get("type") is not None and b.get("owned", False)]
        renpy.log(f"Active building types for event filtering: {active_building_types}")

        # Filter events based on building types, flags, conditions, etc.
        possible_events = select_possible_events(all_events, active_building_types)
        renpy.log(f"After filtering, {len(possible_events)} possible random events remain.")

        # Build a pool of guaranteed/date-specific events from filtered list
        guaranteed_pool = [e for e in possible_events if e.get("guaranteed", False) or e.get("event_probability", 0) >= 100]

        # Fallback: also include events with exact_date matching today even if some filter excluded them unexpectedly
        try:
            today_day = store.current_day
            today_month = store.current_month
            for e in all_events:
                conds = e.get("conditions", {}) or {}
                start_when = conds.get("start_when", "")
                if isinstance(start_when, str) and start_when.startswith("exact_date:"):
                    _, val = start_when.split(":", 1)
                    parts = [p.strip() for p in val.split(",")]
                    if len(parts) == 2:
                        d, m = int(parts[0]), int(parts[1])
                        if d == today_day and m == today_month:
                            if e not in guaranteed_pool:
                                guaranteed_pool.append(e)
                                renpy.log(f"Added exact_date fallback event to pool: {e.get('id')}")
        except Exception as e:
            renpy.log(f"ERROR building exact_date fallback pool: {e}")

        # Immediate path: if there are guaranteed/date-specific events, trigger one directly
        if guaranteed_pool:
            # Weighted pick among guaranteed
            total_weight = sum(e.get("weight", 1) for e in guaranteed_pool)
            pick = renpy.random.uniform(0, total_weight)
            cum = 0
            chosen = None
            for e in guaranteed_pool:
                cum += e.get("weight", 1)
                if pick <= cum:
                    chosen = e
                    break
            if chosen is None:
                chosen = guaranteed_pool[0]
            renpy.log(f"Triggering guaranteed event immediately: {chosen.get('id')}")
            store.current_event = chosen
            store.current_worker = None
            return "handle_random_event"

        # Check for guaranteed events (100% probability or date-specific)
        guaranteed_events = [e for e in possible_events if e.get("guaranteed", False) or e.get("event_probability", 30) >= 100]
        
        if guaranteed_events:
            renpy.log(f"Found {len(guaranteed_events)} guaranteed events, skipping probability check")
            should_trigger_event = True
            possible_events = guaranteed_events  # Only consider guaranteed events
        elif has_active_professions:
            # Use default 30% chance (reduced from 50%)
            base_probability = 30
            
            # Each manager reduces event probability by 10%
            manager_count = count_active_managers()
            manager_reduction = manager_count * 10
            effective_probability = max(1, base_probability - manager_reduction)  # Minimum 1%
            
            max_event_probability = max([e.get("event_probability", effective_probability) for e in possible_events]) if possible_events else effective_probability
            
            random_roll = renpy.random.randint(1, 100)
            renpy.log(f"DEBUG: Event chance roll: {random_roll}/100 (base: {base_probability}%, managers: {manager_count} (-{manager_reduction}%), effective: {effective_probability}%, max event probability: {max_event_probability}%)")
            
            # Trigger if base chance succeeds OR if any event has higher probability that succeeds
            should_trigger_event = random_roll <= max(effective_probability, max_event_probability)
        else:
            should_trigger_event = False
        
        if should_trigger_event:
            renpy.log("Triggering event check...")

            if possible_events:
                # Further filter based on worker availability for the event
                valid_events = []
                for event in possible_events:
                    event_id = event.get("id", "unknown")
                    renpy.log(f"Checking worker availability for event {event_id}...")

                    worker_name = event.get("worker_name")
                    random_worker_flag = event.get("random_worker", False) # Renamed to avoid conflict
                    worker_selection = event.get("worker_selection", "none")
                    event_building_types = event.get("building_type", [])

                    # Determine eligible workers
                    eligible_workers = []
                    if event_building_types:
                        eligible_workers = [
                            w for w in store.workers
                            if w.get("assigned_building", "Unassigned") != "Unassigned"
                            and w["assigned_building"] in available_buildings
                            and available_buildings[w["assigned_building"]].get("type") in event_building_types
                        ]
                    else:
                        eligible_workers = store.workers
                    
                    # Gender requirement
                    worker_gender_requirement = event.get("worker_gender_requirement", None)
                    if worker_gender_requirement:
                        eligible_workers = [w for w in eligible_workers if w.get("gender", "") == worker_gender_requirement]

                    worker = None
                    is_available = False
                    
                    if worker_name and not random_worker_flag:
                        target_worker = next((w for w in eligible_workers if w["name"] == worker_name), None)
                        if target_worker:
                            worker, is_available = target_worker, True
                    elif random_worker_flag:
                        if worker_selection == "none" or worker_selection == "random":
                            if eligible_workers:
                                worker, is_available = random.choice(eligible_workers), True
                        elif worker_selection == "choose":
                            is_available = bool(eligible_workers)
                    elif worker_selection == "random":
                        if eligible_workers:
                            worker, is_available = random.choice(eligible_workers), True
                    elif worker_selection == "choose":
                        is_available = bool(eligible_workers)
                    elif worker_selection == "none":
                        is_available = True

                    if is_available:
                        valid_events.append((event, worker))
                        renpy.log(f"Added event {event_id} to valid random events pool.")
                    else:
                        renpy.log(f"Event {event_id} skipped due to worker availability/selection issues.")

                renpy.log(f"Found {len(valid_events)} valid random events with available workers/conditions met.")

                if valid_events:
                    # Filter events by their individual probability
                    probability_filtered_events = []
                    # Calculate effective base probability with manager reduction (already calculated above)
                    # Use the same effective_probability calculated earlier, or recalculate if needed
                    manager_count = count_active_managers()
                    manager_reduction = manager_count * 10
                    base_event_prob = max(1, 30 - manager_reduction)  # Minimum 1%
                    
                    for event, worker in valid_events:
                        # If event has custom probability (fixed chance), use it as-is (NOT affected by managers)
                        # If not, use the effective base probability (reduced by managers)
                        event_probability = event.get("event_probability")
                        if event_probability is None:
                            # No custom probability, use effective base (reduced by managers)
                            event_probability = base_event_prob
                        else:
                            # Has custom probability (fixed chance) - use it exactly as defined, NOT affected by managers
                            # Only ensure it's not below 1% for safety
                            event_probability = max(1, event_probability)
                        
                        if event.get("guaranteed", False) or event_probability >= 100:
                            # Guaranteed events always pass
                            probability_filtered_events.append((event, worker))
                            renpy.log(f"Event {event.get('id')} is guaranteed, adding to selection pool")
                        else:
                            # Roll for individual event probability
                            individual_roll = renpy.random.randint(1, 100)
                            if individual_roll <= event_probability:
                                probability_filtered_events.append((event, worker))
                                renpy.log(f"Event {event.get('id')} passed individual probability check ({individual_roll} <= {event_probability}%)")
                            else:
                                renpy.log(f"Event {event.get('id')} failed individual probability check ({individual_roll} > {event_probability}%)")
                    
                    if probability_filtered_events:
                        # Use weight-based selection among events that passed probability check
                        total_weight = sum(event.get("weight", 1) for event, _ in probability_filtered_events)
                        if total_weight > 0:
                            choice_val = renpy.random.uniform(0, total_weight)
                            cumulative_weight = 0
                            chosen_event_tuple = None
                            for event_tuple in probability_filtered_events:
                                cumulative_weight += event_tuple[0].get("weight", 1)
                                if choice_val <= cumulative_weight:
                                    chosen_event_tuple = event_tuple
                                    break
                        
                        if chosen_event_tuple:
                            event, worker = chosen_event_tuple
                            renpy.log(f"Selected random event: {event.get('id')}")
                            store.current_event = event
                            store.current_worker = worker
                            return "handle_random_event"
                        else:
                            renpy.log("Weighted selection failed to pick an event.")
                    else:
                        renpy.log("No events passed individual probability checks, skipping random event.")
                else:
                    renpy.log("No valid events found or total weight is zero, skipping random event.")
            else:
                renpy.log("No possible events after initial filtering.")
        else:
            if not has_active_professions:
                renpy.log("Skipping random event check: No workers have active professions.")
            else:
                renpy.log(f"Skipping random event check: Random chance failed.")

        # --- THIS CODE RUNS IF NO EVENT WAS RETURNED ---
        renpy.log(f"End of Day: Income=${total_income}, Costs=${total_building_costs}, Final Money=${money}")

        if money < -5000:
            return "game_over"

        renpy.call_screen("daily_report")
        
        return "tavern"
