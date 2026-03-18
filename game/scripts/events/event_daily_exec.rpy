# event_daily_exec.rpy

    # ==============================
    # NEW: Updated process_daily_events() function
    # ==============================

init python:

    # Configurable skill penalty for high libido on non-sexual jobs.
    # Rule:
    # - At libido 20 -> -5 effective skill
    # - Above 20 -> -5 plus overflow above 20
    NON_SEXUAL_LIBIDO_BASELINE = 20
    NON_SEXUAL_LIBIDO_BASE_SKILL_PENALTY = 5

    def get_difficulty_comfort_mult():
        """Return the comfort cost multiplier for the current difficulty (used in process_next_day and UI)."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "story":
            return 5
        if diff == "nightmare":
            return 40
        if diff == "hard":
            return 30
        # easy and normal: same cost per design
        return 20

    def get_difficulty_building_skill_mult():
        """Return skill-bonus cost multiplier for building upkeep based on difficulty."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 2.0
        if diff == "hard":
            return 1.5
        return 1.0

    def _story_stats_match_worker(story, worker):
        """
        Validate optional story stat requirements.
        Supports:
        - {"joy": 40} -> min 40
        - {"joy": {"min": 30, "max": 80}}
        - {"joy": {"eq": 50}}
        """
        requirements = story.get("stat_requirements", {}) or {}
        if not requirements:
            return True

        for stat_name, requirement in requirements.items():
            worker_value = worker.get(stat_name, 0)
            try:
                worker_value = int(worker_value)
            except Exception:
                worker_value = 0

            if isinstance(requirement, dict):
                min_val = requirement.get("min")
                max_val = requirement.get("max")
                eq_val = requirement.get("eq")

                if eq_val is not None:
                    try:
                        if worker_value != int(eq_val):
                            return False
                    except Exception:
                        return False

                if min_val is not None:
                    try:
                        if worker_value < int(min_val):
                            return False
                    except Exception:
                        return False

                if max_val is not None:
                    try:
                        if worker_value > int(max_val):
                            return False
                    except Exception:
                        return False
            else:
                # Simple form -> minimum required value
                try:
                    if worker_value < int(requirement):
                        return False
                except Exception:
                    return False

        return True

    def is_story_eligible_for_worker(story, worker):
        """Trait/stat based story pre-filter. All keys are optional."""
        worker_traits = set(worker.get("traits", []) or [])

        if story.get("nsfw_only", False) and not getattr(persistent, "nsfw_enabled", False):
            return False

        required_traits = story.get("required_traits", []) or []
        for trait_name in required_traits:
            if trait_name not in worker_traits:
                return False

        excluded_traits = story.get("excluded_traits", []) or []
        for trait_name in excluded_traits:
            if trait_name in worker_traits:
                return False

        if not _story_stats_match_worker(story, worker):
            return False

        return True

    def _parse_trait_weights(data, default_weight=3):
        """
        Parse positive_traits or negative_traits. Returns list of (trait_name, weight).
        - List: ["A", "B"] -> [("A", 3), ("B", 3)]
        - Dict: {"A": 5, "B": 3} -> [("A", 5), ("B", 3)]
        Uses hasattr/get for dict-like (RevertableDict) per LA_BIBLIA - isinstance(dict) fails.
        """
        if not data:
            return []
        def _to_weight(w):
            try:
                return int(float(w)) if w is not None else default_weight
            except (TypeError, ValueError):
                return default_weight
        if hasattr(data, "items"):
            return [(str(t), _to_weight(w)) for t, w in data.items()]
        if hasattr(data, "__iter__") and not hasattr(data, "items"):
            return [(str(t), default_weight) for t in data]
        return []

    def _pick_weighted_trait(matching_traits_weights):
        """Pick one trait by weight. matching_traits_weights = [(trait, weight), ...]. Returns trait or None."""
        if not matching_traits_weights:
            return None
        if len(matching_traits_weights) == 1:
            return matching_traits_weights[0][0]
        traits = [t for t, _ in matching_traits_weights]
        weights = [max(1, w) for _, w in matching_traits_weights]
        return random.choices(traits, weights=weights, k=1)[0]

    def apply_nonsexual_libido_skill_penalty(worker, profession, effective_skill):
        """
        Apply effective skill penalty to non-NSFW professions when libido is high/max.
        Returns tuple: (adjusted_effective_skill, note_or_none).
        """
        # In SFW mode libido is fully disabled as a gameplay factor.
        if not getattr(persistent, "nsfw_enabled", False):
            return effective_skill, None

        if effective_skill <= 0:
            return effective_skill, None

        if profession.get("nsfw", False):
            return effective_skill, None

        try:
            max_libido = int(get_max_libido(worker))
        except Exception:
            max_libido = 100
        if max_libido <= 0:
            return effective_skill, None

        current_libido = worker.get("libido", 0)
        try:
            current_libido = int(current_libido)
        except Exception:
            current_libido = 0

        if current_libido < NON_SEXUAL_LIBIDO_BASELINE:
            return effective_skill, None

        overflow = max(0, current_libido - NON_SEXUAL_LIBIDO_BASELINE)
        penalty = NON_SEXUAL_LIBIDO_BASE_SKILL_PENALTY + overflow
        adjusted = max(0, effective_skill - penalty)

        if penalty <= 0:
            return effective_skill, None

        note = (
            f"High libido reduced non-sexual job focus "
            f"(-{penalty} effective skill, libido {current_libido}/{max_libido})."
        )
        return adjusted, note

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

        # 1. Agrupar trabajadores REALES (de store.workers) por su edificio asignado
        workers_by_building = {}
        for w in store.workers:
            b_name = w.get("assigned_building", "Unassigned")
            if b_name != "Unassigned":
                if b_name not in workers_by_building:
                    workers_by_building[b_name] = []
                workers_by_building[b_name].append(w)

        for building_name in store.owned_buildings:
            building = available_buildings.get(building_name)
            workers_here = workers_by_building.get(building_name, [])
            if not building:
                renpy.log(f"DAILY: Skipping {building_name} - not found in available_buildings")
                continue

            # Sincronizamos la lista visual por si acaso, pero no dependemos de ella
            building["assigned_servants"] = workers_here
            
            if not workers_here:
                renpy.log(f"DAILY: {building_name} has no workers assigned in store.workers -> skipping")
                continue

            btype_id = building.get("type")
            if not btype_id:
                continue

            btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), None)
            if not btype:
                continue

            # Update building costs to include skill bonus
            _skill_mult = get_difficulty_building_skill_mult()
            bonus_cost = int(((building["skill_bonus"] // 10) * 100) * _skill_mult)
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
                # Get all workers in rest for this building from the robust workers_here list
                workers_in_rest = []
                for w in workers_here:
                    worker_name = w.get("name", "")
                    job_raw = building.get("servant_jobs", {}).get(worker_name, "")
                    job_norm = str(job_raw).lower()
                    if "rest" in job_norm:
                        workers_in_rest.append(w)
                        renpy.log(f"DAILY: Found worker in rest: {worker_name} in {building_name}")
                
                # Process each worker in rest exactly once
                for worker in workers_in_rest:
                    stories = rest_profession.get("daily_stories", [])
                    if not stories:
                        renpy.log(f"DAILY: No daily_stories for rest profession, skipping")
                        continue
                    compatible_rest_stories = [s for s in stories if is_story_eligible_for_worker(s, worker)]
                    if not compatible_rest_stories:
                        compatible_rest_stories = stories
                    chosen_story = random.choice(compatible_rest_stories)
                    full_description = chosen_story.get("description", "")
                    full_description = full_description.replace("{worker_name}", worker.get("name", "Unknown"))
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
                            if "libido" in cons and getattr(persistent, "nsfw_enabled", False):
                                old_libido = worker.get("libido", 0)
                                apply_attribute_change(worker, "libido", cons["libido"])
                                renpy.log(f"Event: {worker['name']} libido {old_libido} -> {worker.get('libido', 0)} (change: {cons['libido']}), Worker ID: {id(worker)}")
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
                # Check if building has event_limit set (0 = unlimited, 1 = limit to 1, 2 = limit to 2, 3 = limit to 3)
                event_limit = building.get("event_limit", 0)
                if event_limit > 0:
                    events_per_worker = event_limit
                elif hasattr(daily_story_count, "get"):
                    base_events = int(daily_story_count.get("base", 0))
                    bonus_formula = daily_story_count.get("bonus_formula", "0")
                    try:
                        effective_rep = get_effective_reputation_for_events(building)
                        bonus = int(eval(bonus_formula, {"__builtins__": None}, {"reputation": effective_rep}))
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
                            if (story_gender_req is None or story_gender_req == worker_gender) and is_story_eligible_for_worker(story, worker):
                                compatible_stories.append(story)

                        # Safety fallback to preserve legacy behavior if custom filters remove all stories.
                        if not compatible_stories:
                            compatible_stories = []
                            for story in stories:
                                story_gender_req = story.get("worker_gender_requirement", None)
                                if story_gender_req is None or story_gender_req == worker_gender:
                                    compatible_stories.append(story)
                            if compatible_stories:
                                renpy.log(f"Story filter fallback used for {worker.get('name', 'Unknown')} in profession {profession.get('id', 'unknown')}")
                        
                        if not compatible_stories:
                            renpy.log(f"No compatible stories found for {worker['name']} (gender: {worker_gender})")
                            continue
                        
                        chosen_story = select_weighted_event(compatible_stories)
                        if not chosen_story:
                            continue

                        skill_options = chosen_story.get("skill_options", [])
                        diff = getattr(persistent, "difficulty", "normal")
                        if diff == "nightmare":
                            difficulty_skill_penalty = 10
                        elif diff == "hard":
                            difficulty_skill_penalty = 0
                        else:
                            difficulty_skill_penalty = 0
                        if skill_options:
                            selected_skill = random.choice(skill_options)
                            total_skill = sum(calculate_skill_with_traits(worker, s) for s in skill_options)  # Use skill names directly
                            count_skill = len(skill_options)
                            effective_skill = total_skill // count_skill if count_skill > 0 else 0
                        else:
                            selected_skill = None
                            effective_skill = 0
                        effective_skill = max(0, effective_skill - difficulty_skill_penalty)

                        # Apply libido-based skill penalty on non-sexual jobs.
                        effective_skill, libido_penalty_note = apply_nonsexual_libido_skill_penalty(worker, profession, effective_skill)

                        # Apply difficulty modifier from story
                        difficulty_modifier = chosen_story.get("difficulty_modifier", 0)
                        adjusted_skill = max(0, effective_skill + difficulty_modifier)

                        # Trait specialization: positive_traits and negative_traits (list or dict with weights).
                        # List -> weight 3 each. Dict -> trait name -> weight (roll bonus and message selection).
                        # Backwards compat: relevant_traits treated as positive_traits list.
                        pos_data = chosen_story.get("positive_traits") or chosen_story.get("relevant_traits") or []
                        neg_data = chosen_story.get("negative_traits") or []
                        pos_trait_weights = _parse_trait_weights(pos_data)
                        neg_trait_weights = _parse_trait_weights(neg_data)
                        worker_traits_raw = worker.get("traits", []) or []
                        worker_traits = set(str(t).strip() for t in (worker_traits_raw if hasattr(worker_traits_raw, "__iter__") else []) if t)
                        matching_pos = [(t, w) for t, w in pos_trait_weights if t in worker_traits]
                        matching_neg = [(t, w) for t, w in neg_trait_weights if t in worker_traits]
                        trait_modifier = sum(w for _, w in matching_pos) - sum(w for _, w in matching_neg)
                        if trait_modifier != 0:
                            adjusted_skill = max(0, adjusted_skill + trait_modifier)

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
                        env = {"skill": effective_skill, "level": worker.get("level", 1), "roll": roll}
                        try:
                            earnings = eval(earnings_formula, {"__builtins__": None}, env)
                        except Exception:
                            earnings = 0

                        # Earnings from JSON are used as-is (formulas already encode tier scaling)
                        earnings = int(earnings)
                        if outcome == "Failure" and earnings == 0:
                            earnings = -10

                        # Trait messages: pick ONE weighted-random trait. Success/critical -> positive; Failure/mediocre -> negative.
                        trait_success_messages = []
                        trait_roll = {"total": trait_modifier} if trait_modifier != 0 else None
                        if outcome in ["Success", "Critical Success"]:
                            worker["success_count"] = worker.get("success_count", 0) + 1

                        if trait_modifier != 0:
                            picked_trait = None
                            tpl = None
                            if outcome in ["Success", "Critical Success"] and matching_pos:
                                picked_trait = _pick_weighted_trait(matching_pos)
                                tpl = chosen_story.get("trait_msg_success") or chosen_story.get("trait_success")
                            elif outcome in ["Failure", "Mediocre"] and matching_neg:
                                picked_trait = _pick_weighted_trait(matching_neg)
                                tpl = chosen_story.get("trait_msg_failure") or chosen_story.get("trait_success")
                            if tpl and picked_trait:
                                try:
                                    txt = tpl.format(worker_name=worker.get("name", "Unknown"), trait=picked_trait)
                                    trait_success_messages.append(f"{txt} ({trait_modifier:+d} to roll)")
                                except Exception:
                                    trait_success_messages.append(f"Trait specialization: {trait_modifier:+d} to roll")
                        
                        # Apply trait earnings multipliers
                        earnings = calculate_earnings(worker, earnings)
                        
                        # Easy difficulty: cap how much workers can lose on failure (normal -20, vip -30, premium -40)
                        if outcome == "Failure" and earnings < 0 and getattr(persistent, "difficulty", "normal") == "easy":
                            failure_formula = chosen_story.get("earnings", {}).get("failure", "")
                            if "200" in failure_formula:
                                earnings = max(earnings, -40)
                            elif "150" in failure_formula:
                                earnings = max(earnings, -30)
                            else:
                                earnings = max(earnings, -20)
                        
                        # Log individual earnings for debugging
                        renpy.log(f"EARNINGS DEBUG: {worker['name']} earned ${earnings} (outcome: {outcome}, skill: {effective_skill}, roll: {roll}, difficulty_penalty: -{difficulty_skill_penalty})")

                        # Apply consequences
                        if "consequences" in chosen_story:
                            cons = chosen_story["consequences"].get(outcome_key, {})
                            if cons:
                                # Hard/Nightmare: failures are harsher.
                                diff = getattr(persistent, "difficulty", "normal")
                                consequence_mult = 3 if diff == "nightmare" else (2 if diff == "hard" else 1)
                                if outcome == "Failure" and consequence_mult > 1:
                                    cons = {
                                        k: (v * consequence_mult if isinstance(v, (int, float)) else v)
                                        for k, v in cons.items()
                                    }
                                    renpy.log(f"{diff.upper()} difficulty: x{consequence_mult} failure consequences for {worker.get('name', 'Unknown')}")
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
                                if "libido" in cons and getattr(persistent, "nsfw_enabled", False):
                                    old_libido = worker.get("libido", 0)
                                    apply_attribute_change(worker, "libido", cons["libido"])
                                    renpy.log(f"Event: {worker['name']} libido {old_libido} -> {worker.get('libido', 0)} (change: {cons['libido']}), Worker ID: {id(worker)}")

                                # Apply add_trait from daily story consequences
                                if "add_trait" in cons:
                                    trait_data = cons["add_trait"]
                                    if isinstance(trait_data, dict):
                                        trait_name = trait_data.get("name")
                                        duration = trait_data.get("duration", 0)
                                    elif isinstance(trait_data, str):
                                        trait_name = trait_data
                                        duration = 0
                                    else:
                                        trait_name = None
                                        duration = 0
                                    if trait_name and worker:
                                        add_trait_with_duration(worker, trait_name, duration)
                                        renpy.log(f"Daily story: Added trait '{trait_name}' to {worker.get('name', 'Unknown')}")

                                # Apply give_item from daily story consequences (to manager inventory)
                                if "give_item" in cons:
                                    item_data = cons["give_item"]
                                    if isinstance(item_data, str) and item_data:
                                        add_item_to_inventory(manager_inventory, item_data)
                                        renpy.log(f"Daily story: Gave item '{item_data}' to manager")
                                    elif isinstance(item_data, dict):
                                        item_id = item_data.get("item_id") or item_data.get("id")
                                        qty = int(item_data.get("quantity", 1))
                                        if item_id:
                                            for _ in range(max(1, qty)):
                                                add_item_to_inventory(manager_inventory, item_id)
                                            renpy.log(f"Daily story: Gave {qty}x '{item_id}' to manager")

                    # Build description
                        if selected_skill:
                            # Use skill name directly
                            skill_for_desc = selected_skill
                            # Calculate the actual skill value for display
                            skill_value = max(0, calculate_skill_with_traits(worker, selected_skill) - difficulty_skill_penalty)
                        else:
                            skill_for_desc = "No Skill"
                            skill_value = 0
                        base_description = chosen_story.get("descriptions", {}).get(outcome_key, "No description available").format(worker_name=worker["name"], skill=skill_for_desc)
                        full_description = base_description
                        if trait_success_messages:
                            full_description += "\n\n{color=#aaddaa}" + "\n".join(trait_success_messages) + "{/color}"
                        if libido_penalty_note:
                            full_description += "\n\n{color=#aa4444}" + libido_penalty_note + "{/color}"
                        # Determine color based on outcome (matching daily report colors)
                        if outcome in ["Critical Success", "Success", "Rest"]:
                            outcome_color = "#006600"  # Verde
                        elif outcome == "Mediocre":
                            outcome_color = "#666600"  # Amarillo
                        elif outcome == "Failure":
                            outcome_color = "#660000"  # Rojo
                        elif outcome == "Refused":
                            outcome_color = "#663333"  # Rojo claro
                        else:
                            outcome_color = "#ffffff"  # Blanco por defecto
                        # Show skill name and value before skill roll
                        if selected_skill and skill_value > 0:
                            full_description += "\n\n{{color={}}}{{size=18}}({}: {} - Skill roll: {} - {}){{/size}}{{/color}}".format(outcome_color, selected_skill, skill_value, roll, outcome)
                        else:
                            full_description += "\n\n{{color={}}}{{size=18}}(Skill roll: {} - {}){{/size}}{{/color}}".format(outcome_color, roll, outcome)

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
                            
                            # Track daily sexual work separately for libido calculation
                            # This allows skill_uses to accumulate for level ups
                            sexual_skills = get_sexual_skill_names()
                            if selected_skill in sexual_skills:
                                worker["daily_sexual_work"] = worker.get("daily_sexual_work", 0) + 1
                            
                            # Get current base skill level for debugging
                            current_level = worker.get("skills", {}).get(selected_skill, 0)
                            uses_needed = max(1, current_level // 15 + 1) if current_level <= 75 else 6 + int((current_level - 75) ** 1.8 / 5)
                            renpy.log(f"SKILL USE: {worker.get('name', 'Unknown')} used {selected_skill} - uses: {old_uses} -> {worker['skill_uses'][selected_skill]}, level: {current_level}, needs: {uses_needed}")

                        # Update building reputation, capped by building/manager level
                        cap = get_building_reputation_cap(building)
                        new_reputation = building["reputation"] + reputation_change
                        building["reputation"] = max(0, min(new_reputation, cap))
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
                                
                                # Bonus items handling - specific items with chance
                                bonus_items = loot_data.get("bonus_items", [])
                                loot_mult = get_difficulty_loot_multiplier()
                                for bonus in bonus_items:
                                    item_id = bonus.get("item_id")
                                    chance = min(1.0, max(0.0, bonus.get("chance", 1.0) * loot_mult))
                                    # Skip NSFW items if NSFW is disabled
                                    if bonus.get("nsfw", False) and not persistent.nsfw_enabled:
                                        continue
                                    # Only on critical success if specified
                                    if bonus.get("critical_only", False) and outcome != "Critical Success":
                                        continue
                                    if item_id and random.random() <= chance:
                                        add_item_to_inventory(manager_inventory, item_id)
                                        if item_id not in report_entry["loot"]:
                                            report_entry["loot"].append(item_id)
                                        renpy.log(f"Bonus loot: {item_id} (chance: {chance})")
                                
                                # Monster worker loot handling
                                if "monster_worker" in loot_data:
                                    chance = min(1.0, max(0.0, loot_data["monster_worker"].get("chance", 1.0) * loot_mult))
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

        # Academy: process workers assigned to Academy (building not in owned_buildings)
        ACADEMY_DAILY_COST_PER_WORKER = 300
        if getattr(store, "academy_enrolled", False) and "Academy" in available_buildings:
            academy_building = available_buildings["Academy"]
            academy_workers = workers_by_building.get("Academy", [])
            btype_academy = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == "academy"), None)
            if btype_academy and academy_workers:
                academy_building["assigned_servants"] = academy_workers
                for worker in academy_workers:
                    job_id = (academy_building.get("servant_jobs") or {}).get(worker.get("name"), "")
                    if not job_id:
                        continue
                    profession = next((p for p in btype_academy.get("professions", []) if p.get("id") == job_id), None)
                    if profession and profession.get("training_skills_distribution"):
                        daily_stories = profession.get("daily_stories") or []
                        compatible_stories = []
                        for story in daily_stories:
                            story_gender_req = story.get("worker_gender_requirement", None)
                            if (story_gender_req is None or story_gender_req == worker.get("gender", "")) and is_story_eligible_for_worker(story, worker):
                                compatible_stories.append(story)
                        if not compatible_stories:
                            for story in daily_stories:
                                story_gender_req = story.get("worker_gender_requirement", None)
                                if story_gender_req is None or story_gender_req == worker.get("gender", ""):
                                    compatible_stories.append(story)
                            if compatible_stories:
                                renpy.log(f"Academy story filter fallback used for {worker.get('name', 'Unknown')}")
                        chosen_story = select_weighted_event(compatible_stories) if compatible_stories else None
                        primary_skill = chosen_story.get("used_skill") if chosen_story else None
                        applied_uses = {}
                        if hasattr(store, "add_academy_training_skill_uses"):
                            applied_uses = store.add_academy_training_skill_uses(worker, profession, primary_skill=primary_skill) or {}
                        story_name = f"Academy: {profession.get('name', 'Training')}"
                        desc_base = f"{worker.get('name', 'Unknown')} attended {profession.get('name', 'Training')} at the Academy."
                        if chosen_story:
                            story_name = chosen_story.get("report") or story_name
                            desc_tpl = chosen_story.get("description") or desc_base
                            desc_base = desc_tpl.replace("{worker_name}", worker.get("name", "Unknown"))
                        if applied_uses:
                            parts = [f"{sk}: +{amt} experience" for sk, amt in sorted(applied_uses.items())]
                            desc_base += " Gained: " + ", ".join(parts) + "."
                        else:
                            desc_base += " Gained experience in relevant skills."
                        if not primary_skill and profession.get("skills"):
                            primary_skill = profession["skills"][0]
                        if not primary_skill:
                            primary_skill = "Clever"
                        report_entry = {
                            "building": "Academy",
                            "profession": profession.get("name", "Training"),
                            "worker_name": worker.get("name", "Unknown"),
                            "worker": worker,
                            "event_data": chosen_story if chosen_story else {"report": story_name},
                            "report": story_name,
                            "description": desc_base,
                            "result": "Success",
                            "earnings": -ACADEMY_DAILY_COST_PER_WORKER,
                            "used_skill": primary_skill,
                            "roll": "N/A",
                            "trait_roll": None,
                            "trait_success_messages": [],
                            "group_event": False,
                            "loot": [],
                            "story_image": get_event_image(worker, chosen_story or {}, outcome="success", skill_name=primary_skill)
                        }
                        daily_report.append(report_entry)
                        processed_events += 1

        renpy.log(f"process_daily_events() finished. Report entries: {len(daily_report)}")
        return None # Function finished successfully

# ==============================
    # process_next_day() function
    # ==============================
    def _relink_assigned_servants_to_store_workers():
        """Ensure buildings' assigned_servants reference the exact dict objects in store.workers.
        CRITICAL: Only use store.workers refs - never keep stale copies (which would lose inventory)."""
        try:
            name_to_worker = {w.get("name"): w for w in store.workers}
            for bname in store.owned_buildings:
                b = available_buildings.get(bname)
                if not isinstance(b, dict):
                    continue
                assigned = b.get("assigned_servants", []) or []
                jobs = b.get("servant_jobs", {}) or {}
                relinked = []
                seen_names = set()
                for sw in assigned:
                    wname = sw.get("name") if isinstance(sw, dict) else None
                    if not wname or wname in seen_names:
                        if wname and wname in seen_names:
                            renpy.log(f"RELINK: duplicate assigned_servant '{wname}' in {bname}, skipping")
                        continue
                    store_ref = name_to_worker.get(wname)
                    if store_ref:
                        relinked.append(store_ref)
                        seen_names.add(wname)
                    else:
                        renpy.log(f"RELINK: worker '{wname}' in {bname} not in store.workers, skipping (avoids stale ref)")
                for wname in jobs.keys():
                    if not wname or wname in seen_names:
                        continue
                    store_ref = name_to_worker.get(wname)
                    if store_ref:
                        relinked.append(store_ref)
                        seen_names.add(wname)
                b["assigned_servants"] = relinked
        except Exception as e:
            renpy.log("RELINK: error while relinking assigned_servants: " + str(e))

    _DAILY_EFFECT_STATS = ("joy", "rebelliousness", "romance", "relationship")

    def _coerce_int_or_none(value):
        try:
            return int(value)
        except Exception:
            return None

    def _daily_effect_delta(delta):
        """Resolve daily effect value: int -> use as-is; dict {min,max} or [a,b] -> random in range."""
        if delta is None:
            return None
        if isinstance(delta, int):
            return delta
        if isinstance(delta, dict):
            lo = delta.get("min")
            hi = delta.get("max")
            if lo is not None and hi is not None:
                try:
                    return random.randint(int(lo), int(hi))
                except Exception:
                    return None
        if isinstance(delta, (list, tuple)) and len(delta) >= 2:
            try:
                return random.randint(int(delta[0]), int(delta[1]))
            except Exception:
                return None
        d = _coerce_int_or_none(delta)
        return d

    def get_worker_daily_effects(worker):
        """
        Returns summed daily effects from:
        - Traits: trait_def["daily_effects"] (supports int or {min,max}/[a,b] for random range)
        - Equipped items: item["effect"]["daily_effects"]
        """
        totals = {s: 0 for s in _DAILY_EFFECT_STATS}
        if not isinstance(worker, dict):
            return totals

        # Traits
        for trait_name in worker.get("traits", []) or []:
            trait_def = next((t for t in traits_list if t.get("name") == trait_name), None)
            if not trait_def:
                continue
            daily_effects = trait_def.get("daily_effects") or {}
            if not isinstance(daily_effects, dict):
                continue
            for stat, delta in daily_effects.items():
                if stat not in totals:
                    continue
                d = _daily_effect_delta(delta)
                if d is None:
                    continue
                totals[stat] += d

        # Equipped items (inventory entries are typically (item_id, qty, equipped))
        for inv_entry in worker.get("inventory", []) or []:
            item_id = None
            equipped = False
            if isinstance(inv_entry, (list, tuple)) and len(inv_entry) >= 3:
                item_id = inv_entry[0]
                equipped = bool(inv_entry[2])
            elif isinstance(inv_entry, dict):
                item_id = inv_entry.get("id") or inv_entry.get("item_id")
                equipped = bool(inv_entry.get("equipped", False))

            if not equipped or not item_id:
                continue

            item_data = next((i for i in items_json.get("items", []) if i.get("id") == item_id), None)
            if not item_data:
                continue

            effect = item_data.get("effect") or {}
            daily_effects = effect.get("daily_effects") or {}
            if not isinstance(daily_effects, dict):
                continue

            for stat, delta in daily_effects.items():
                if stat not in totals:
                    continue
                d = _daily_effect_delta(delta) if stat == "rebelliousness" else _coerce_int_or_none(delta)
                if d is None:
                    continue
                totals[stat] += d

        return totals

    def apply_worker_daily_effects(worker):
        totals = get_worker_daily_effects(worker)
        for stat, delta in totals.items():
            if not delta:
                continue
            old = worker.get(stat, 0)
            apply_attribute_change(worker, stat, delta)
            renpy.log(f"DAILY_EFFECTS: {worker.get('name', 'Unknown')} {stat} {old} -> {worker.get(stat)} ({delta:+d})")

    AUTO_CONSUME_THRESHOLD = 0.30
    AUTO_CONSUME_REST_GUARD_THRESHOLD = 0.35

    def _inventory_quantity(inv, item_id):
        try:
            for e in inv or []:
                # Common format: [item_id, qty, equipped?] or (item_id, qty, equipped?)
                if isinstance(e, (list, tuple)) and len(e) >= 2:
                    if str(e[0]) == str(item_id):
                        return int(e[1])
                    continue
                # Alternate format: {"id": "...", "qty": 3, ...} (or Ren'Py RevertableDict)
                if hasattr(e, "get"):
                    eid = e.get("id") or e.get("item_id")
                    if str(eid) != str(item_id):
                        continue
                    qty = (
                        e.get("qty")
                        if e.get("qty") is not None
                        else e.get("quantity")
                        if e.get("quantity") is not None
                        else e.get("count")
                        if e.get("count") is not None
                        else e.get("amount")
                    )
                    if qty is None:
                        qty = 1
                    return int(qty)
            return 0
        except Exception:
            return 0

    def auto_consume_start_of_day(worker, threshold=AUTO_CONSUME_THRESHOLD):
        """
        Start-of-day auto-consume (runs when the player closes the daily report).
        - Only when worker's health or energy ratio is BELOW threshold (e.g. 0.30 = 30%).
        - Consumes potions ONLY from the worker's own inventory (never from manager_inventory).
        - Tops up until cap or potions run out; avoids wasting a potion when deficit < potion amount (unless stat < 5).
        """
        # Accept dict-like objects (Ren'Py often uses RevertableDict)
        if not hasattr(worker, "get"):
            return

        try:
            max_h = calculate_max_health(worker)
            max_e = calculate_max_energy(worker)
        except Exception as e:
            try:
                renpy.log(f"AUTO_CONSUME_DAYSTART_ERROR: cannot compute caps for {worker.get('name','Unknown')}: {e}")
            except Exception:
                pass
            return

        # Health: only auto-consume when health ratio is below threshold, and only from worker inventory
        try:
            if max_h > 0:
                def _get_health_potion_amount():
                    try:
                        potion = next((i for i in items_json.get("items", []) if i.get("id") == "health_potion"), None)
                        eff = potion.get("effect", {}) if potion else {}
                        amt = eff.get("health", 20)
                        return max(1, int(amt))
                    except Exception:
                        return 20

                potion_amt = _get_health_potion_amount()
                cur = int(worker.get("health", 0) or 0)
                cap = int(max_h)
                deficit = cap - cur
                inv_q = _inventory_quantity(worker.get("inventory", []), "health_potion")
                # Only run when health is below threshold and worker has potions in their own inventory
                health_ratio = cur / cap if cap > 0 else 1.0
                if cap > 0 and deficit > 0 and health_ratio < threshold and inv_q > 0:
                    must_use = cur < 5
                    should_use = must_use or (deficit >= potion_amt)
                    would_waste = (not must_use) and (deficit < potion_amt)
                    renpy.log(
                        f"AUTO_HEALTH_DAYSTART_CHECK: {worker.get('name','Unknown')} "
                        f"health={cur}/{cap} ratio={health_ratio:.2f}<{threshold} inv={inv_q} "
                        f"must_use={must_use} would_waste={would_waste}"
                    )
                    if should_use and not would_waste:
                        used = 0
                        while int(worker.get("health", 0) or 0) < cap:
                            cur_now = int(worker.get("health", 0) or 0)
                            deficit_now = cap - cur_now
                            if cur_now >= 5 and deficit_now < potion_amt:
                                break
                            inv_q_now = _inventory_quantity(worker.get("inventory", []), "health_potion")
                            if inv_q_now <= 0:
                                break
                            before = cur_now
                            store.use_item("health_potion", worker)
                            after = int(worker.get("health", 0) or 0)
                            used += 1
                            if after <= before:
                                break
                        if used:
                            renpy.log(
                                f"AUTO_HEALTH_DAYSTART: {worker.get('name','Unknown')} used health_potion x{used} "
                                f"-> {int(worker.get('health', 0) or 0)}/{cap}"
                            )
        except Exception as e:
            renpy.log(f"AUTO_CONSUME health error for {worker.get('name','Unknown')}: {e}")

        # Energy: only auto-consume when energy ratio is below threshold, and only from worker inventory
        try:
            if max_e > 0:
                def _get_energy_potion_amount():
                    try:
                        potion = next((i for i in items_json.get("items", []) if i.get("id") == "energy_potion"), None)
                        eff = potion.get("effect", {}) if potion else {}
                        amt = eff.get("energy", 5)
                        return max(1, int(amt))
                    except Exception:
                        return 5

                potion_amt = _get_energy_potion_amount()
                cur = int(worker.get("energy", 0) or 0)
                cap = int(max_e)
                deficit = cap - cur
                inv_q = _inventory_quantity(worker.get("inventory", []), "energy_potion")
                # Only run when energy is below threshold and worker has potions in their own inventory
                energy_ratio = cur / cap if cap > 0 else 1.0
                if cap > 0 and deficit > 0 and energy_ratio < threshold and inv_q > 0:
                    must_use = cur < 5
                    should_use = must_use or (deficit >= potion_amt)
                    would_waste = (not must_use) and (deficit < potion_amt)
                    renpy.log(
                        f"AUTO_ENERGY_DAYSTART_CHECK: {worker.get('name','Unknown')} "
                        f"energy={cur}/{cap} ratio={energy_ratio:.2f}<{threshold} inv={inv_q} "
                        f"must_use={must_use} would_waste={would_waste}"
                    )
                    if should_use and not would_waste:
                        used = 0
                        while int(worker.get("energy", 0) or 0) < cap:
                            cur_now = int(worker.get("energy", 0) or 0)
                            deficit_now = cap - cur_now
                            if cur_now >= 5 and deficit_now < potion_amt:
                                break
                            inv_q_now = _inventory_quantity(worker.get("inventory", []), "energy_potion")
                            if inv_q_now <= 0:
                                break
                            before = cur_now
                            store.use_item("energy_potion", worker)
                            after = int(worker.get("energy", 0) or 0)
                            used += 1
                            if after <= before:
                                break
                        if used:
                            renpy.log(
                                f"AUTO_ENERGY_DAYSTART: {worker.get('name','Unknown')} used energy_potion x{used} "
                                f"-> {int(worker.get('energy', 0) or 0)}/{cap}"
                            )
        except Exception as e:
            renpy.log(f"AUTO_CONSUME energy error for {worker.get('name','Unknown')}: {e}")

    def process_next_day():
        # Ensure necessary variables are global (removed filtered_building)
        global daily_report, displayed_workers, money, can_recruit_today, available_workers, daily_spawns

        # Hard reset of pending random-event context at day start.
        # Prevents stale events from previous flows from appearing together
        # with governor events on the same day.
        store.current_event = None
        store.current_worker = None

        # Check and update trait durations
        check_trait_durations()
        # One-time migration: rebelliousness no longer uses modifiers; prime _last_applied to avoid delta spike
        if not getattr(persistent, "_rebelliousness_v2_migrated", False):
            for w in getattr(store, "workers", []) or []:
                if isinstance(w, dict):
                    la = w.get("_last_applied_trait_modifiers") or {}
                    la["rebelliousness"] = 0
                    w["_last_applied_trait_modifiers"] = la
            persistent._rebelliousness_v2_migrated = True
            renpy.log("REBELLIOUSNESS_V2: Migration applied (primed _last_applied for all workers)")
        # Advance the date first
        advance_date()
        
        # Check if it's Monday and start BGM if needed
        check_and_start_monday_bgm()

        displayed_workers = []  # Clear displayed_workers at the start
        can_recruit_today = True  # Reset recruitment flag each day
        daily_spawns = 0  # Reset daily spawns counter
        if hasattr(store, "academy_haggle_available"):
            store.academy_haggle_available = True  # Reset Academy haggle option each day

        # --- ENSURE REPORT LIST IS CLEARED HERE ---
        daily_report = []
        renpy.log("Cleared daily_report for the new day.")
        # --- END CLEAR ---

        total_income = 0 # Initialize income for the day
        total_building_costs = 0  # Track total building costs

        # Ensure building assigned_servants reference live worker objects before daily processing.
        _relink_assigned_servants_to_store_workers()

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

                # Difficulty: Story (comfort x5, base 100), Easy/Normal (x20, base 100),
                # Hard (x30, base 200), Nightmare (x40, base 300)
                comfort_mult = get_difficulty_comfort_mult()
                diff = getattr(persistent, "difficulty", "normal")
                if diff == "nightmare":
                    base_per_level = 300
                elif diff == "hard":
                    base_per_level = 200
                else:
                    base_per_level = 100

                # Add base maintenance cost (per building level; Hard doubles it)
                base_cost = base_per_level * building["base_level"]
                building["costs"] += base_cost

                # Add worker costs based on comfort level and upkeep per worker (differs by source)
                if "assigned_servants" in building:
                    comfort_costs = sum(worker.get("comfort_level", 1) * comfort_mult for worker in building["assigned_servants"])
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

        # Poner a descansar / restaurar trabajo ANTES de regenerar: si se regenera primero, los de 0 energía ya no cumplen energy < rest_threshold
        try:
            process_manager_auto_rest()
            renpy.log("Manager auto-rest processing completed (before regen)")
        except Exception as e:
            renpy.log(f"Error in manager auto-rest: {e}")

        # Re-run auto-equip at day start so newly obtained gear (including accessories)
        # is considered without requiring manual toggle/profession changes.
        for worker in store.workers:
            if worker.get("auto_equip", False):
                try:
                    run_worker_auto_equip(worker)
                except Exception as e:
                    renpy.log(f"AUTO_EQUIP_DAYSTART error for {worker.get('name', 'Unknown')}: {e}")

        # Regenerate energy/health and update stats BEFORE events
        for worker in store.workers:
            old_health = worker["health"]
            base_regen = worker.get("level", 1)
            trait_regen = calculate_health_regeneration(worker)
            health_regen = base_regen + trait_regen
            max_health = calculate_max_health(worker)
            worker["max_health"] = max_health
            new_health = min(worker["health"] + health_regen, max_health)
            worker["health"] = new_health
            # Always log health regeneration to verify it's working
            if old_health != new_health:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} -> {new_health} (regen: +{health_regen} = level {base_regen} + trait {trait_regen}, max: {max_health})")
            else:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} (already at max {max_health}, regen would be +{health_regen} = level {base_regen} + trait {trait_regen})")

            old_energy = worker["energy"]
            base_energy_regen = worker.get("level", 1)
            trait_energy_regen = 0
            try:
                trait_energy_regen = calculate_energy_regeneration(worker)
            except Exception:
                trait_energy_regen = 0
            energy_regen = base_energy_regen + trait_energy_regen
            max_energy = calculate_max_energy(worker)
            worker["max_energy"] = max_energy
            new_energy = min(worker["energy"] + energy_regen, max_energy)
            worker["energy"] = new_energy
            if old_energy != new_energy:
                renpy.log(f"ENERGY REGEN: {worker.get('name', 'Unknown')} energy {old_energy} -> {new_energy} (regen: +{energy_regen} = level {base_energy_regen} + trait {trait_energy_regen}, max: {max_energy})")

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

            # Apply daily effects from traits + equipped items (then re-enforce minimum relationship)
            apply_worker_daily_effects(worker)
            if worker.get("relationship", 0) < minimum_relationship:
                set_attribute_with_caps(worker, "relationship", minimum_relationship)

            comfort_desired = get_effective_comfort_desired(worker)
            comfort_bonus = max(0, comfort - comfort_desired)
            if comfort_bonus > 0:
                old_joy = worker["joy"]
                apply_attribute_change(worker, "joy", comfort_bonus)
                renpy.log(f"Comfort bonus: {worker['name']} joy {old_joy} -> {worker['joy']} (bonus: {comfort_bonus}, comfort: {comfort}, desired: {comfort_desired})")

        # Ensure assigned_servants reference live worker objects before processing events
        _relink_assigned_servants_to_store_workers()

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
        if dead_workers:
            if len(dead_workers) == 1:
                renpy.say(None, f"{dead_workers[0]} has died and had to be let go.")
            else:
                names_text = ", ".join(dead_workers[:-1]) + f" and {dead_workers[-1]}"
                renpy.say(None, f"{names_text} have died and had to be let go.")

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

        # ===== GOVERNOR'S TENSION SYSTEM =====
        # Update tension level based on current objective
        try:
            update_governor_attention()
            
            # Check for governor's retaliation event (one-time)
            if check_governor_retaliation():
                renpy.log("TENSION: Governor retaliation triggered!")
                store.current_event = None
                store.current_worker = None
                return "governor_retaliation"
            
            # Check for random tension events (from objective 10 onwards)
            tension_event = process_governor_tension_event()
            if tension_event:
                renpy.log(f"TENSION: Triggering tension event: {tension_event}")
                store._pending_tension_event = tension_event
                store.current_event = None
                store.current_worker = None
                return "governor_tension_event"
        except Exception as e:
            renpy.log(f"TENSION ERROR: {e}")
        # ===================================

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
        
        # Check for priority events (NOT affected by managers):
        # - Events with explicit custom probability (event_probability defined)
        # - Events explicitly marked as priority (priority: true)
        # - Story/quest events explicitly tagged via event_type
        # NOTE: We no longer infer priority from limited == false.
        def _is_priority_event(e):
            event_type = str(e.get("event_type", "")).lower()
            return (
                e.get("event_probability") is not None
                or bool(e.get("priority", False))
                or event_type in ("story", "quest")
            )

        priority_events = [
            e for e in possible_events
            if _is_priority_event(e)
            and not e.get("guaranteed", False)
            and e.get("event_probability", 30) < 100
        ]
        
        # Normal events are affected by managers.
        normal_events = [
            e for e in possible_events
            if not _is_priority_event(e) and not e.get("guaranteed", False)
        ]
        
        if guaranteed_events:
            renpy.log(f"Found {len(guaranteed_events)} guaranteed events, skipping probability check")
            should_trigger_event = True
            possible_events = guaranteed_events  # Only consider guaranteed events
        elif priority_events or (normal_events and has_active_professions):
            # Two separate checks:
            # 1. Priority events (custom probability OR explicit priority/story tags) - NOT affected by managers
            # 2. Normal events - affected by managers
            
            should_trigger_event = False
            events_to_consider = []
            # Priority events with explicit custom probability are already gated once
            # by the priority roll. Avoid rolling their probability a second time.
            prepassed_priority_event_ids = set()
            
            # Check priority events (NOT affected by managers)
            # Priority events include: custom probability OR explicit priority/story tags
            if priority_events:
                # Use event_probability if defined, otherwise use 50% for limited events
                max_priority_prob = max([e.get("event_probability", 50) for e in priority_events])
                priority_roll = renpy.random.randint(1, 100)
                renpy.log(f"DEBUG: Priority events roll: {priority_roll}/100 (max prob: {max_priority_prob}%, NOT affected by managers, {len(priority_events)} events)")
                if priority_roll <= max_priority_prob:
                    should_trigger_event = True
                    events_to_consider.extend(priority_events)
                    for e in priority_events:
                        event_id = e.get("id")
                        if event_id and e.get("event_probability") is not None and e.get("event_probability", 0) < 100:
                            prepassed_priority_event_ids.add(event_id)
            
            # Check normal events (affected by managers)
            if normal_events and has_active_professions:
                base_probability = 30
                manager_count = count_active_managers()
                manager_reduction = manager_count * 10
                effective_probability = max(1, base_probability - manager_reduction)  # Minimum 1%
                
                normal_roll = renpy.random.randint(1, 100)
                renpy.log(f"DEBUG: Normal events roll: {normal_roll}/100 (base: {base_probability}%, managers: {manager_count} (-{manager_reduction}%), effective: {effective_probability}%)")
                if normal_roll <= effective_probability:
                    should_trigger_event = True
                    events_to_consider.extend(normal_events)
            
            # If any check passed, consider those events
            if events_to_consider:
                possible_events = events_to_consider
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
                        event_id = event.get("id")
                        # If event has custom probability (fixed chance), use it as-is (NOT affected by managers)
                        # If not, use the effective base probability (reduced by managers)
                        event_probability = event.get("event_probability")
                        prepassed_priority = event_id in prepassed_priority_event_ids
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
                        elif prepassed_priority:
                            probability_filtered_events.append((event, worker))
                            renpy.log(
                                f"Event {event.get('id')} already passed priority probability gate; "
                                f"skipping duplicate individual probability roll."
                            )
                        else:
                            # Roll for individual event probability
                            individual_roll = renpy.random.randint(1, 100)
                            if individual_roll <= event_probability:
                                probability_filtered_events.append((event, worker))
                                renpy.log(
                                    f"Event {event.get('id')} passed individual probability check ({individual_roll} <= {event_probability}%)"
                                )
                            else:
                                renpy.log(
                                    f"Event {event.get('id')} failed individual probability check ({individual_roll} > {event_probability}%)"
                                )

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
        
        # Daily report will be shown in next_day label after this returns
        return "tavern"
