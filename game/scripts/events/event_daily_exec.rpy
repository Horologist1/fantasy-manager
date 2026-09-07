# event_daily_exec.rpy

    # ==============================
    # NEW: Updated process_daily_events() function
    # ==============================

init python:

    from fm_events.earnings import protect_positive_payout, resolve_story_earnings
    from fm_performance.reporting import collect_net_hp_losses, snapshot_worker_health

    # Configurable skill penalty for high libido on non-sexual jobs.
    # Rule:
    # - At libido 20 -> -5 effective skill
    # - Above 20 -> -5 plus overflow above 20
    NON_SEXUAL_LIBIDO_BASELINE = 20
    NON_SEXUAL_LIBIDO_BASE_SKILL_PENALTY = 5
    DAILY_SIM_DEBUG = False
    # Game over when player money is at or below this (after daily ledger or at day start).
    BANKRUPTCY_MONEY_THRESHOLD = -5000
    store.BANKRUPTCY_MONEY_THRESHOLD = BANKRUPTCY_MONEY_THRESHOLD

    def _daily_debug_log(message):
        if DAILY_SIM_DEBUG:
            renpy.log(message)

    def choose_guaranteed_event_tuple(valid_events, current_day, current_month):
        """Prefer expiring exact-date events, then deterministic recovery events."""
        if not valid_events:
            return None

        exact_today = []
        for event_tuple in valid_events:
            event = event_tuple[0]
            start_when = str((event.get("conditions", {}) or {}).get("start_when", ""))
            if not start_when.startswith("exact_date:"):
                continue
            try:
                raw_day, raw_month = start_when.split(":", 1)[1].split(",", 1)
                if int(raw_day.strip()) == int(current_day) and int(raw_month.strip()) == int(current_month):
                    exact_today.append(event_tuple)
            except (TypeError, ValueError):
                continue
        if exact_today:
            return sorted(exact_today, key=lambda item: str(item[0].get("id", "")))[0]

        recovery_events = [
            event_tuple for event_tuple in valid_events
            if event_tuple[0].get("recovery_priority", False)
        ]
        if recovery_events:
            return sorted(recovery_events, key=lambda item: str(item[0].get("id", "")))[0]

        total_weight = sum(event.get("weight", 1) for event, _worker in valid_events)
        pick = renpy.random.uniform(0, total_weight)
        cumulative_weight = 0
        for event_tuple in valid_events:
            cumulative_weight += event_tuple[0].get("weight", 1)
            if pick <= cumulative_weight:
                return event_tuple
        return valid_events[0]

    def get_difficulty_comfort_mult():
        """Comfort unit cost scaled by difficulty."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 30
        if diff == "hard":
            return 25
        if diff == "normal":
            return 20
        if diff == "easy":
            return 18
        # story
        return 15

    def get_difficulty_building_skill_mult():
        """Return skill-bonus cost multiplier for building upkeep based on difficulty."""
        diff = getattr(persistent, "difficulty", "normal")
        if diff == "nightmare":
            return 2.0
        if diff == "hard":
            return 1.5
        return 1.0

    def _is_first_building_slot(building_name):
        """True for Building 1 aliases ('Building 1' / 'Building_1')."""
        s = str(building_name or "").strip().replace("_", " ")
        s = " ".join(s.split()).lower()
        return s == "building 1"

    def _fixed_maintenance_ladder_cost(base_level):
        """
        Fixed building upkeep by level (normal difficulty): 100, 300, 500, 700, 900 for levels 1-5;
        continues +200 per level beyond 5 if uncapped.
        """
        try:
            lv = int(base_level)
        except Exception:
            lv = 1
        lv = max(1, lv)
        return 100 + (lv - 1) * 200

    def get_building_base_maintenance_cost(building_name, building):
        """
        Base daily maintenance before worker comfort charges and skill-bonus upkeep.
        """
        if building is None or not hasattr(building, "get"):
            return 0

        diff = getattr(persistent, "difficulty", "normal")
        try:
            base_level = int(building.get("base_level", 1))
        except Exception:
            base_level = 1
        base_level = max(1, base_level)

        raw = _fixed_maintenance_ladder_cost(base_level)
        if diff == "nightmare":
            base_cost = int(raw * 3)
        elif diff == "hard":
            base_cost = int(raw * 2)
        else:
            base_cost = int(raw)

        return base_cost

    def get_building_daily_cost_scaling_tooltip():
        """Tooltip copy for UI: how building level affects fixed upkeep."""
        _cm = get_difficulty_comfort_mult()
        return (
            "Fixed daily upkeep by building level (Normal): $100, $300, $500, $700, $900 for levels 1-5.\n"
            "Hard doubles that ladder; Nightmare triples it (same relative tiers as before).\n"
            "Assigned workers: comfort x " + str(_cm) + " each, with no extra multiplier from building level."
        )

    def get_building_level_short_tooltip():
        _cm = get_difficulty_comfort_mult()
        return (
            "Higher building levels raise fixed daily upkeep (see Costs tooltip) and reputation cap. "
            "Worker charges are comfort x " + str(_cm) + " only."
        )

    def get_building_comfort_line_tooltip():
        """Worker UI: base comfort line and building-level context."""
        _cm = get_difficulty_comfort_mult()
        return (
            "Base worker comfort cost is comfort x " + str(_cm) + ". "
            "Building totals sum that for assigned workers; level does not multiply worker comfort. "
            "Hover Costs on Manager for the full breakdown. "
            "Comfort level 1 is baseline (no extra regen). Each comfort level above 1 adds +1 daily energy regeneration at day start (before work). "
            "Comfort above desired adds daily Joy (which reduces Rebelliousness above 80)."
        )

    def compute_worker_portion_daily_costs(workers, base_level):
        """
        Returns (total, comfort_part, upkeep_part) for assigned servants.
        upkeep_part is kept for backward compatibility and is always 0.
        workers: iterable of worker dicts.
        base_level is ignored; kept for call-site compatibility.
        """
        comfort_mult = get_difficulty_comfort_mult()
        seq = workers if workers is not None else []
        comfort_costs = 0
        for w in seq:
            if not hasattr(w, "get"):
                continue
            try:
                cl = int(w.get("comfort_level", 1))
            except Exception:
                cl = 1
            comfort_costs += cl * comfort_mult
        comfort_costs = int(comfort_costs)
        upkeep_costs = 0
        return comfort_costs + upkeep_costs, comfort_costs, upkeep_costs

    def compute_single_worker_daily_charge(worker):
        """
        Base worker daily comfort charge shown in worker details (comfort x rate, scaled by difficulty).
        Same per-worker rate is summed for building totals; building level does not multiply it.
        """
        if not worker or not hasattr(worker, "get"):
            return 0
        try:
            cl = int(worker.get("comfort_level", 1))
        except Exception:
            cl = 1
        return int(max(1, cl) * get_difficulty_comfort_mult())

    def daily_story_apply_trait_chance_from_cons(worker, cons):
        """
        Apply consequences.trait_chance (same schema as training: list of { trait|name, chance_percent|percent, optional duration }).
        Returns list of trait names actually granted for UI/report.
        """
        if not cons or not hasattr(cons, "get"):
            return []
        tc = cons.get("trait_chance")
        if tc is None:
            return []
        if hasattr(tc, "get") and callable(getattr(tc, "get", None)):
            entries = [tc]
        elif hasattr(tc, "__iter__") and not isinstance(tc, (str, bytes)):
            entries = list(tc)
        else:
            return []
        if not entries:
            return []
        fn = getattr(store, "apply_trait_chance_entries", None)
        if not callable(fn):
            return []
        stat_changes = {}
        fn(worker, entries, stat_changes, granted_list_key="traits_from_daily_story", log_prefix="Daily story")
        return list(stat_changes.get("traits_from_daily_story") or [])

    def daily_story_apply_trait_remove_chance_from_cons(worker, cons):
        """
        Apply consequences.trait_remove_chance (same entry shape as trait_chance, without duration).
        Returns list of trait names actually removed for UI/report.
        """
        if not cons or not hasattr(cons, "get"):
            return []
        tc = cons.get("trait_remove_chance")
        if tc is None:
            return []
        if hasattr(tc, "get") and callable(getattr(tc, "get", None)):
            entries = [tc]
        elif hasattr(tc, "__iter__") and not isinstance(tc, (str, bytes)):
            entries = list(tc)
        else:
            return []
        if not entries:
            return []
        fn = getattr(store, "apply_trait_remove_chance_entries", None)
        if not callable(fn):
            return []
        stat_changes = {}
        fn(worker, entries, stat_changes, removed_list_key="traits_removed_from_daily_story", log_prefix="Daily story")
        return list(stat_changes.get("traits_removed_from_daily_story") or [])

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
            # Prefer nested worker skills while preserving legacy top-level stat checks.
            worker_stats = worker.get("skills", {}) if hasattr(worker, "get") else {}
            if hasattr(worker_stats, "get"):
                legacy_value = worker.get(stat_name, 0) if hasattr(worker, "get") else 0
                worker_value = worker_stats.get(stat_name, legacy_value)
            else:
                worker_value = worker.get(stat_name, 0) if hasattr(worker, "get") else 0
            try:
                worker_value = int(worker_value)
            except Exception:
                worker_value = 0

            if hasattr(requirement, "get"):
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

    def is_story_eligible_for_worker(story, worker, ignore_nsfw_filter=False):
        """Trait/stat based story pre-filter. All keys are optional."""
        worker_traits = get_worker_trait_match_names(worker)

        story_restricted = content_object_is_restricted(story)
        if story_restricted and not ignore_nsfw_filter and not getattr(persistent, "nsfw_enabled", False):
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

    def _fm_normal_event_probability(event, worker):
        """Per-building manager gating for a normal event (spec 2026-08-13).

        Context: paired worker's building wins; else min manager count among
        content-visible buildings matching the event's building_type; else no
        context -> flat base. Fallback on import failure: flat base 30 (never
        resurrects the old global reduction, never crashes the daily loop).
        """
        try:
            from fm_events.manager_gating import event_probability, resolve_context_count
        except Exception as e:
            renpy.log("manager gating import failed: %r" % (e,))
            return 30
        worker_count = None
        if worker is not None and hasattr(worker, "get"):
            ab = worker.get("assigned_building")
            resolved = _resolve_building_key(ab) if ab and ab != "Unassigned" else None
            if resolved:
                worker_count = count_managers_in_building(resolved)
        candidate_counts = []
        if worker_count is None and event.get("building_type"):
            try:
                for _cand_name, _cand_b in get_content_visible_event_buildings(event, available_buildings):
                    candidate_counts.append(count_managers_in_building(_cand_name))
            except Exception:
                candidate_counts = []
        return event_probability(resolve_context_count(worker_count, candidate_counts))

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

        if content_object_is_restricted(profession):
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

    def _story_requires_high_libido(story):
        """True when the story is gated on a minimum libido (a libido-vent story).
        Supports both {"libido": 20} and {"libido": {"min": 20}} requirement forms."""
        if not story or not hasattr(story, "get"):
            return False
        req = (story.get("stat_requirements") or {}).get("libido")
        if hasattr(req, "get"):
            req = req.get("min")
        try:
            return int(req) > 0
        except (TypeError, ValueError):
            return False

    # Staffing: per-profession penalty (0 workers) / bonus (>=1) on building earnings; clamp product.
    STAFFING_MONEY_MULT_MIN = 1.0 / 3.0
    STAFFING_MONEY_MULT_MAX = 3.0
    PRESENCE_ROLL_BONUS_TOTAL_CAP = 40

    def compute_building_staffing_modifiers(btype, building, workers_here):
        """
        Returns (building_money_mult, building_roll_bonus).
        - Money: product of staffing_penalty if job count==0 else staffing_bonus per profession (skip rest); clamp [1/3, 3].
        - Synergy: sum of presence_roll_bonus * n_workers (added to skill threshold for d100 checks); cap total magnitude.
        """
        sj = building.get("servant_jobs") or {}
        job_counts = {}
        for w in workers_here:
            if not hasattr(w, "get"):
                continue
            wn = w.get("name")
            if not wn:
                continue
            jid = sj.get(wn, "")
            job_counts[jid] = job_counts.get(jid, 0) + 1

        raw_money = 1.0
        roll_bonus_raw = 0
        for prof in btype.get("professions", []):
            pid = prof.get("id")
            if pid == "rest":
                continue
            n = job_counts.get(pid, 0)
            try:
                if n == 0:
                    m = float(prof.get("staffing_penalty", 1.0))
                else:
                    m = float(prof.get("staffing_bonus", 1.0))
                raw_money *= m
            except (TypeError, ValueError):
                pass
            prb = prof.get("presence_roll_bonus")
            if prb is not None:
                try:
                    roll_bonus_raw += int(float(prb)) * n
                except (TypeError, ValueError):
                    pass
        money_mult = max(STAFFING_MONEY_MULT_MIN, min(STAFFING_MONEY_MULT_MAX, raw_money))
        roll_bonus = max(-PRESENCE_ROLL_BONUS_TOTAL_CAP, min(PRESENCE_ROLL_BONUS_TOTAL_CAP, roll_bonus_raw))
        return money_mult, roll_bonus

    def get_projected_job_roll_bonus(worker, profession, building, btype):
        """Return the staffing roll bonus after hypothetically assigning worker to profession."""
        if not building or not btype or not worker or not profession:
            return 0

        projected_building = dict(building)
        projected_jobs = dict(building.get("servant_jobs") or {})
        worker_name = worker.get("name")
        if worker_name:
            projected_jobs[worker_name] = profession.get("id", "")
        projected_building["servant_jobs"] = projected_jobs

        workers_here = list(building.get("assigned_servants") or [])
        if worker_name and not any(w.get("name") == worker_name for w in workers_here if hasattr(w, "get")):
            workers_here.append(worker)

        _money_mult, roll_bonus = compute_building_staffing_modifiers(btype, projected_building, workers_here)
        return roll_bonus

    def estimate_daily_job_success(worker, profession, building_roll_bonus=0, building=None, building_type=None):
        """Estimate the weighted success threshold using the same rules as the daily job roll."""
        if not worker or not profession or is_unrefuseable_profession(profession):
            return None

        stories = profession.get("daily_stories", []) or []
        worker_gender = worker.get("gender", "")

        def _compatible(include_player_filter):
            result = []
            for story in stories:
                if building is not None and not story_allowed_by_building_policy(building, story, worker_gender):
                    continue
                gender_requirement = story.get("worker_gender_requirement")
                if gender_requirement is not None and gender_requirement != worker_gender:
                    continue
                if not is_story_eligible_for_worker(story, worker):
                    continue
                if include_player_filter and not store.event_passes_player_gender_requirement(story):
                    continue
                result.append(story)
            return result

        compatible_stories = _compatible(True)
        if not compatible_stories:
            compatible_stories = _compatible(False)
        if not compatible_stories:
            return None

        diff = getattr(persistent, "difficulty", "normal")
        difficulty_skill_penalty = 10 if diff == "nightmare" else 0
        worker_traits = get_worker_trait_match_names(worker)
        weighted_threshold = 0.0
        total_weight = 0.0

        for story in compatible_stories:
            skill_options = story.get("skill_options", []) or []
            if skill_options:
                effective_skill = sum(calculate_skill_with_traits(worker, skill) for skill in skill_options) // len(skill_options)
            else:
                effective_skill = 0
            effective_skill = max(0, effective_skill - difficulty_skill_penalty)
            effective_skill, _libido_note = apply_nonsexual_libido_skill_penalty(worker, profession, effective_skill)

            adjusted_skill = max(0, effective_skill + int(story.get("difficulty_modifier", 0) or 0))
            positive = _parse_trait_weights(story.get("positive_traits") or story.get("relevant_traits") or [])
            negative = _parse_trait_weights(story.get("negative_traits") or [])
            trait_modifier = sum(weight for trait, weight in positive if trait in worker_traits)
            trait_modifier -= sum(weight for trait, weight in negative if trait in worker_traits)
            policy_focus_bonus = get_building_policy_focus_bonus(building, building_type, worker.get("gender")) if building is not None else 0
            threshold = min(100, max(0, adjusted_skill + trait_modifier + int(building_roll_bonus or 0) + policy_focus_bonus))

            try:
                weight = max(0.0, float(story.get("weight", 1) or 0))
            except (TypeError, ValueError):
                weight = 1.0
            weighted_threshold += threshold * weight
            total_weight += weight

        if total_weight <= 0:
            return None
        return int(round(weighted_threshold / total_weight))

    def sanitize_daily_report_entry_for_filter(report_entry, btype, profession, story=None):
        """Attach immutable content provenance; presentation performs all masking."""
        story = story or {}
        worker = report_entry.get("worker", {}) or {}
        is_nsfw_content = bool(
            content_object_is_restricted(btype)
            or content_object_is_restricted(profession)
            or content_object_is_restricted(story)
        )
        report_entry["building_type_id"] = (btype or {}).get("id")
        # Archive the raw canonical label. SFW masking belongs exclusively to
        # get_report_building_display(), so changing the toggle stays reversible.
        report_entry.setdefault("building_type_name", (btype or {}).get("name", (btype or {}).get("id", "Building")))
        if not report_entry.get("building_display_name"):
            building_name = report_entry.get("building", "Unknown Building")
            parts = str(building_name).split("_")
            default_name = "Building %s" % parts[1] if len(parts) > 1 else str(building_name).replace("_", " ")
            custom_name = (getattr(store, "custom_names", {}) or {}).get(building_name, default_name)
            report_entry["building_display_name"] = "%s: %s" % (report_entry["building_type_name"], custom_name)
        report_entry["profession_id"] = (profession or {}).get("id")
        report_entry["nsfw_content"] = is_nsfw_content
        report_entry["worker_nsfw"] = bool(content_object_is_restricted(worker))
        return report_entry

    def build_no_permitted_stories_report_entry(worker, building_name, btype, profession):
        # Neutral ledger row for a worker whose every story was vetoed by the
        # Skill Policy / eligibility filters; without it the worker silently
        # vanished from the daily report with $0 and no explanation.
        report_entry = {
            "worker_name": worker.get("name", "Unknown"),
            "worker": worker,
            "building": building_name,
            "event_data": {"story_image": "Refuse"},
            "report": f"{worker.get('name', 'Unknown')} had no permitted tasks",
            "description": f"{worker.get('name', 'Unknown')} spent the day idle: the building's Skill Policy does not permit any of this job's tasks for them. Review the policy or reassign the worker.",
            "result": "Unhandled",
            "earnings": 0,
            "used_skill": "N/A",
            "roll": "N/A",
            "trait_roll": None,
            "trait_success_messages": [],
            "group_event": False,
            "loot": [],
            "story_image": get_event_image(worker, {"story_image": "Refuse"}, outcome="refused"),
        }
        return sanitize_daily_report_entry_for_filter(report_entry, btype, profession)

    def is_unrefuseable_profession(profession):
        prof_id = str((profession or {}).get("id", "")).strip().lower()
        if prof_id == "rest":
            return True
        if prof_id.startswith("academy_"):
            return True
        return False

    def apply_simple_daily_story_consequences(worker, cons, manager_inv):
        granted = []
        removed = []
        if not cons:
            return granted, removed
        if "energy" in cons:
            old_energy = worker["energy"]
            worker["energy"] = min(calculate_max_energy(worker), max(0, worker["energy"] + cons["energy"]))
            renpy.log(f"Academy: {worker['name']} energy {old_energy} -> {worker['energy']} (change: {cons['energy']})")
        if "health" in cons:
            old_health = worker["health"]
            worker["health"] = min(calculate_max_health(worker), max(0, worker["health"] + cons["health"]))
            renpy.log(f"Academy: {worker['name']} health {old_health} -> {worker['health']} (change: {cons['health']})")
        if "joy" in cons:
            old_joy = worker["joy"]
            apply_attribute_change(worker, "joy", cons["joy"])
            renpy.log(f"Academy: {worker['name']} joy {old_joy} -> {worker['joy']} (change: {cons['joy']})")
        if "rebelliousness" in cons:
            old_rebelliousness = worker["rebelliousness"]
            apply_attribute_change(worker, "rebelliousness", cons["rebelliousness"])
            renpy.log(f"Academy: {worker['name']} rebelliousness {old_rebelliousness} -> {worker['rebelliousness']} (change: {cons['rebelliousness']})")
        if "romance" in cons:
            old_romance = worker["romance"]
            apply_attribute_change(worker, "romance", cons["romance"])
            renpy.log(f"Academy: {worker['name']} romance {old_romance} -> {worker['romance']} (change: {cons['romance']})")
        if "relationship" in cons:
            old_relationship = worker["relationship"]
            apply_attribute_change(worker, "relationship", cons["relationship"])
            renpy.log(f"Academy: {worker['name']} relationship {old_relationship} -> {worker['relationship']} (change: {cons['relationship']})")
        if "reputation" in cons:
            rep_delta = cons["reputation"]
            if rep_delta:
                try:
                    rep_delta = int(rep_delta)
                except Exception:
                    rep_delta = 0
                if rep_delta and "Academy" in available_buildings:
                    ab = available_buildings["Academy"]
                    cap = get_building_reputation_cap(ab)
                    new_rep = ab.get("reputation", 0) + rep_delta
                    ab["reputation"] = max(0, min(new_rep, cap))
                    renpy.log(f"Academy reputation {rep_delta} -> {ab['reputation']} (cap {cap})")
        if "libido" in cons and getattr(persistent, "nsfw_enabled", False):
            old_libido = worker.get("libido", 0)
            apply_attribute_change(worker, "libido", cons["libido"])
            renpy.log(f"Academy: {worker['name']} libido {old_libido} -> {worker.get('libido', 0)} (change: {cons['libido']})")
        granted.extend(daily_story_apply_trait_chance_from_cons(worker, cons))
        removed.extend(daily_story_apply_trait_remove_chance_from_cons(worker, cons))
        if "give_item" in cons and manager_inv is not None:
            item_data = cons["give_item"]
            if isinstance(item_data, str) and item_data:
                add_item_to_inventory(manager_inv, item_data)
                renpy.log(f"Academy daily: gave item '{item_data}' to manager")
            elif hasattr(item_data, "get"):
                item_id = item_data.get("item_id") or item_data.get("id")
                qty = int(item_data.get("quantity", 1))
                if item_id:
                    for _ in range(max(1, qty)):
                        add_item_to_inventory(manager_inv, item_id)
                    renpy.log(f"Academy daily: gave {qty}x '{item_id}' to manager")
        return granted, removed

    def process_daily_events():
        global daily_report, manager_inventory
        renpy.log("process_daily_events() starting...")

        # Daily badge tracker (level/skill ups, HP loss) shown in the report.
        # SESSION-ONLY, and reset here at the single once-per-day entry point:
        # process_daily_events runs exactly once per day (from `label next_day`).
        # If it were ever chained twice within one day, only the last pass's
        # deltas would show in the report. Not saved (display-only). (Audit note #6.)
        store.daily_worker_deltas = {}
        # process_daily_events can cross Ren'Py interactions; session state
        # survives those boundaries without leaking into saves or rollback.
        renpy.session["_fm_daily_hp_at_start"] = snapshot_worker_health(store.workers)

        # Clear image cache for new Daily Report
        clear_image_cache()

        # Defensive: ensure assigned_servants are linked to live worker objects
        try:
            _relink_assigned_servants_to_store_workers()
        except Exception as e:
            renpy.log("RELINK in process_daily_events error: " + str(e))

        # Precompute name -> store worker map for identity enforcement
        name_to_store = {w.get("name"): w for w in store.workers}

        try:
            _daily_debug_log("ENERGY SNAPSHOT: begin daily events")
            for bname in store.owned_buildings:
                b = available_buildings.get(bname)
                if not hasattr(b, "get"):
                    continue
                for aw in b.get("assigned_servants", []) or []:
                    n = aw.get("name")
                    sw = name_to_store.get(n)
                    if sw is not None and aw is not sw:
                        aw["energy"] = sw.get("energy", aw.get("energy", 0))
                        aw["health"] = sw.get("health", aw.get("health", 0))
                    _daily_debug_log(f"  {bname}: {n} assigned energy={aw.get('energy')} id={id(aw)} | store energy={sw.get('energy') if sw else 'N/A'} id={id(sw) if sw else 'N/A'} job={b.get('servant_jobs', {}).get(n)}")
        except Exception as e:
            renpy.log("ENERGY SNAPSHOT error: " + str(e))

        workers_by_building = {}
        for w in store.workers:
            b_name = w.get("assigned_building", "Unassigned")
            if b_name != "Unassigned":
                if b_name not in workers_by_building:
                    workers_by_building[b_name] = []
                workers_by_building[b_name].append(w)

        all_owned_buildings = list(store.owned_buildings or [])
        if getattr(store, "academy_enrolled", False) and "Academy" in available_buildings and "Academy" not in all_owned_buildings:
            all_owned_buildings.append("Academy")

        for building_name in all_owned_buildings:
            building = available_buildings.get(building_name)
            workers_here = workers_by_building.get(building_name, [])
            if not building:
                renpy.log(f"DAILY: Skipping {building_name} - not found in available_buildings")
                continue

            building["assigned_servants"] = workers_here
            
            if not workers_here:
                renpy.log(f"DAILY: {building_name} has no workers assigned in store.workers -> skipping")
                continue

            btype_id = building.get("type")
            if not btype_id and str(building_name) == "Academy":
                btype_id = "academy"
            if not btype_id:
                continue

            if btype_id == "arena" and not arena_operations_are_unlocked():
                renpy.log("DAILY: Arena opening trial incomplete -> skipping operations")
                continue

            btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), None)
            if not btype:
                continue

            building_money_mult, building_roll_bonus = compute_building_staffing_modifiers(btype, building, workers_here)
            renpy.log(
                f"DAILY {building_name}: staffing_money_mult={building_money_mult:.4f} "
                f"presence_roll_bonus={building_roll_bonus}"
            )

            # Update building costs to include skill bonus
            _skill_mult = get_difficulty_building_skill_mult()
            bonus_cost = int(((building["skill_bonus"] // 10) * 100) * _skill_mult)
            renpy.log(f"Building {building_name} previous costs: {building.get('costs', 0)}, adding skill bonus: {bonus_cost}")
            building["costs"] = building.get("costs", 0) + bonus_cost
            renpy.log(f"Building {building_name} new costs after skill bonus: {building['costs']}")

            policy_incident = apply_building_policy_incident(building, btype, building_name)
            policy_incident_worker_name = None
            policy_incident_profession_id = None
            if policy_incident:
                policy_incident_worker_name = policy_incident.get("worker_name")
                policy_incident_profession_id = str(policy_incident.get("profession_id", "")).strip().lower()
                policy_profession = next(
                    (entry for entry in (btype.get("professions", []) or []) if str(entry.get("id", "")).strip().lower() == policy_incident_profession_id),
                    {"id": "service_policy", "name": "Service Policy", "nsfw_content": bool(content_object_is_restricted(btype))},
                )
                sanitize_daily_report_entry_for_filter(policy_incident, btype, policy_profession, policy_incident.get("event_data", {}))
                daily_report.append(policy_incident)

            for profession in btype.get("professions", []):
                _pid = str(profession.get("id", "")).strip().lower()
                if not profession_is_visible(profession, btype):
                    renpy.log(f"DAILY: Profession {_pid} hidden by content filter -> skipping")
                    continue
                assigned_workers = [
                    name_to_store.get(w.get("name"), w)
                    for w in building["assigned_servants"]
                    if str((building.get("servant_jobs") or {}).get(w.get("name"), "")).strip().lower() == _pid
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
                        effective_rep = get_effective_reputation_for_events(building)
                        bonus = int(eval(bonus_formula, {"__builtins__": None}, {"reputation": effective_rep}))
                    except Exception:
                        bonus = 0
                    events_per_worker = max(1, base_events + bonus)
                else:
                    events_per_worker = int(daily_story_count)

                # Building event_limit caps stories per worker (0 = unlimited; 1–3 = max per worker per day).
                event_limit = building.get("event_limit", 0)
                try:
                    event_limit = int(event_limit)
                except Exception:
                    event_limit = 0
                if event_limit > 0:
                    events_per_worker = min(events_per_worker, event_limit)

                for worker in eligible_workers:
                    renpy.log(f"Processing worker: {worker['name']}, ID: {id(worker)}")
                    worker_events_remaining = events_per_worker
                    if (
                        policy_incident
                        and worker.get("name") == policy_incident_worker_name
                        and str(profession.get("id", "")).strip().lower() == policy_incident_profession_id
                        and worker_events_remaining > 0
                    ):
                        worker_events_remaining -= 1
                        renpy.log("POLICY: consumed one daily story for %s after a missed service request" % worker.get("name", "Unknown"))
                    if worker_events_remaining <= 0:
                        continue
                    # Check for rebelliousness
                    if not is_unrefuseable_profession(profession):
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
                            sanitize_daily_report_entry_for_filter(report_entry, btype, profession, {"story_image": "Refuse"})
                            daily_report.append(report_entry)
                            continue  # Skip further processing for this worker

                    # Track the number of events processed
                    processed_events = 0
                    for _ in range(worker_events_remaining):
                        daily_story_traits_granted = []
                        daily_story_traits_removed = []
                        # Check if worker has enough energy to perform another event
                        if worker["energy"] <= 0 and str(profession.get("id", "")).strip().lower() != "rest":
                            renpy.log(f"{worker['name']} has no energy left. Skipping further events.")
                            break

                        stories = profession.get("daily_stories", [])
                        if not stories:
                            continue
                        hidden_content_job = bool(content_object_is_restricted(btype) or content_object_is_restricted(profession))
                        
                        # Filter stories by worker gender, manager (Lord/Lady) gender, and eligibility
                        worker_gender = worker.get("gender", "")
                        building_policy_focus_bonus = get_building_policy_focus_bonus(building, btype, worker.get("gender"))

                        def _collect_daily_stories_compatible(include_player_filter, include_eligible):
                            out = []
                            for story in stories:
                                if not story_allowed_by_building_policy(building, story, worker_gender):
                                    continue
                                story_gender_req = story.get("worker_gender_requirement", None)
                                if story_gender_req is not None and story_gender_req != worker_gender:
                                    continue
                                if include_player_filter and not store.event_passes_player_gender_requirement(story):
                                    continue
                                if include_eligible and not is_story_eligible_for_worker(story, worker, ignore_nsfw_filter=hidden_content_job):
                                    continue
                                out.append(story)
                            return out

                        compatible_stories = _collect_daily_stories_compatible(True, True)
                        # Relax manager gender if nothing matches (same idea as legacy worker/eligible fallback)
                        if not compatible_stories:
                            compatible_stories = _collect_daily_stories_compatible(False, True)
                        
                        if not compatible_stories:
                            renpy.log(f"No compatible stories found for {worker['name']} (gender: {worker_gender})")
                            daily_report.append(build_no_permitted_stories_report_entry(worker, building_name, btype, profession))
                            break

                        # A focused Academy course uses the matching lesson variant.
                        # If data is incomplete, focus_story_pool preserves the full legacy pool.
                        _academy_profession_id = str(profession.get("id", "")).strip().lower()
                        if _academy_profession_id.startswith("academy_"):
                            try:
                                from fm_academy.curriculum import focus_story_pool
                                _academy_focus = get_academy_training_focus(_academy_profession_id)
                                compatible_stories = focus_story_pool(
                                    compatible_stories,
                                    (_academy_focus or {}).get("primary"),
                                )
                            except Exception as e:
                                renpy.log("Academy story focus fallback for %s: %r" % (_academy_profession_id, e))
                        
                        chosen_story = select_weighted_event(compatible_stories)
                        if not chosen_story:
                            continue

                        profession_id = str(profession.get("id", "")).strip().lower()
                        if is_unrefuseable_profession(profession):
                            daily_story_traits_granted = []
                            daily_story_traits_removed = []
                            academy_primary_skill = None
                            academy_applied_uses = {}

                            if profession_id.startswith("academy_"):
                                academy_primary_skill = chosen_story.get("used_skill")
                                if not academy_primary_skill and profession.get("skills"):
                                    academy_primary_skill = profession.get("skills")[0]
                                if not academy_primary_skill:
                                    academy_primary_skill = "Clever"
                                if profession.get("training_skills_distribution") and hasattr(store, "add_academy_training_skill_uses"):
                                    academy_applied_uses = store.add_academy_training_skill_uses(worker, profession, primary_skill=academy_primary_skill) or {}

                            no_roll_cons = {}
                            if hasattr(chosen_story.get("consequences"), "get"):
                                no_roll_cons = chosen_story.get("consequences", {}).get("success", {}) or {}
                            if no_roll_cons:
                                daily_story_traits_granted, daily_story_traits_removed = apply_simple_daily_story_consequences(worker, no_roll_cons, manager_inventory)

                            if profession_id.startswith("academy_"):
                                try:
                                    _acad_lv = max(1, int(worker.get("level", 1)))
                                except Exception:
                                    _acad_lv = 1
                                earnings = -int(round(300 * (1.0 + 0.06 * float(_acad_lv - 1))))
                                outcome = "Success"
                                used_skill = academy_primary_skill or "N/A"
                            else:
                                earnings = 0
                                outcome = "Rest"
                                used_skill = "N/A"
                                # Rest comfort bonus: comfort-1 extra energy recovery
                                try:
                                    _rc = int(worker.get("comfort_level", 1))
                                except Exception:
                                    _rc = 1
                                _rest_comfort_bonus = max(0, _rc - 1)
                                if _rest_comfort_bonus > 0:
                                    _max_e = calculate_max_energy(worker)
                                    worker["energy"] = min(_max_e, worker["energy"] + _rest_comfort_bonus)

                            _raw_desc = chosen_story.get("description", "")
                            if not _raw_desc:
                                _raw_desc = chosen_story.get("descriptions", {}).get("success", "No description available")
                            full_description = _raw_desc.format(worker_name=worker.get("name", "Unknown"), skill=used_skill)

                            if academy_applied_uses:
                                parts = [f"{sk}: +{amt} experience" for sk, amt in sorted(academy_applied_uses.items())]
                                full_description += " Gained: " + ", ".join(parts) + "."

                            if daily_story_traits_granted:
                                full_description += (
                                    "\n\n{color=#88cc88}Trait(s) gained: "
                                    + ", ".join(str(t) for t in daily_story_traits_granted)
                                    + "{/color}"
                                )
                            if daily_story_traits_removed:
                                full_description += (
                                    "\n\n{color=#cc8888}Trait(s) removed: "
                                    + ", ".join(str(t) for t in daily_story_traits_removed)
                                    + "{/color}"
                                )

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
                                "roll": "N/A",
                                "trait_roll": None,
                                "trait_success_messages": [],
                                "group_event": False,
                                "loot": [],
                                "story_image": get_event_image(worker, chosen_story, outcome="success", skill_name=used_skill)
                            }
                            sanitize_daily_report_entry_for_filter(report_entry, btype, profession, chosen_story)
                            daily_report.append(report_entry)
                            processed_events += 1
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
                        # Libido-vent stories ARE the outlet for that tension (and carry their own
                        # difficulty_modifier); a red penalty note on the day the valve fires
                        # reads as a problem, so only show it on non-vent days.
                        if libido_penalty_note and _story_requires_high_libido(chosen_story):
                            libido_penalty_note = None

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
                        worker_traits = get_worker_trait_match_names(worker)
                        matching_pos = [(t, w) for t, w in pos_trait_weights if t in worker_traits]
                        matching_neg = [(t, w) for t, w in neg_trait_weights if t in worker_traits]
                        trait_modifier = sum(w for _, w in matching_pos) - sum(w for _, w in matching_neg)
                        if trait_modifier != 0:
                            adjusted_skill = max(0, adjusted_skill + trait_modifier)

                        # Roll outcome: success if d100 <= skill threshold. Synergy bonus raises the threshold (not the die).
                        roll = random.randint(1, 100)
                        try:
                            synergy_skill_bonus = int(building_roll_bonus) + int(building_policy_focus_bonus)
                        except (TypeError, ValueError):
                            synergy_skill_bonus = 0
                        skill_threshold = min(100, max(0, adjusted_skill + synergy_skill_bonus))

                        # Critical success: 10% of effective threshold, max 25%
                        crit_pct = min(25, max(1, int(round(0.10 * skill_threshold))))
                        
                        if roll <= crit_pct:
                            outcome = "Critical Success"
                            reputation_change = 10
                        elif roll <= skill_threshold:
                            # Success: roll <= threshold (core mechanic)
                            outcome = "Success"
                            reputation_change = 5
                        elif roll <= skill_threshold + 10:
                            # Mediocre: just above threshold (threshold+1 to threshold+10)
                            outcome = "Mediocre"
                            reputation_change = 0
                        else:
                            # Failure: everything above threshold+10
                            outcome = "Failure"
                            reputation_change = -5
                        # no_fail stories (relationship-arc rewards) never fail: keep the
                        # crit chance but remap Mediocre/Failure -> Success so they read as
                        # a guaranteed reward.
                        if chosen_story.get("no_fail") and outcome in ("Mediocre", "Failure"):
                            outcome = "Success"
                            reputation_change = 5
                        outcome_key = outcome.lower().replace(" ", "_")

                        base_earnings, earnings_error = resolve_story_earnings(
                            chosen_story,
                            outcome_key,
                            skill=skill_threshold,
                            level=worker.get("level", 1),
                            roll=roll,
                        )
                        if earnings_error:
                            renpy.log("EARNINGS FORMULA ERROR: " + earnings_error)
                        earnings = base_earnings

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
                                    # trait_modifier is net from ALL matching pos/neg traits; picked_trait is narrative only.
                                    # Always label the number so it is never read as only this trait weight.
                                    trait_success_messages.append(
                                        f"{txt} ({trait_modifier:+d} total from traits)"
                                    )
                                except Exception:
                                    trait_success_messages.append(f"Trait specialization: {trait_modifier:+d}")
                        
                        # Trait + Business Acumen money mult (calculate_earnings skips negatives; staffing mult always applies)
                        earnings = calculate_earnings(worker, earnings)
                        earnings = int(round(earnings * building_money_mult))

                        # Difficulty earnings scaling (applies to positive earnings only)
                        if earnings > 0:
                            earnings = int(round(earnings * get_difficulty_earnings_mult()))

                        # A valid positive formula must never become "No payout" because
                        # a downstream trait, management or staffing multiplier is broken.
                        earnings, payout_repaired = protect_positive_payout(
                            outcome_key,
                            base_earnings=base_earnings,
                            final_earnings=earnings,
                        )
                        if payout_repaired:
                            renpy.log(
                                "EARNINGS PAYOUT REPAIRED: story=%s outcome=%s base=%s"
                                % (chosen_story.get("id", "<unknown>"), outcome_key, base_earnings)
                            )

                        # Story/Easy: floor on failure losses (daily stories use failure: "-roll" after rebalance)
                        if outcome == "Failure" and earnings < 0:
                            diff_fail = getattr(persistent, "difficulty", "normal")
                            if diff_fail == "story":
                                earnings = 0
                            elif diff_fail == "easy":
                                earnings = max(earnings, -25)
                        
                        # Log individual earnings for debugging
                        renpy.log(
                            f"EARNINGS DEBUG: {worker['name']} earned ${earnings} (outcome: {outcome}, skill: {effective_skill}, "
                            f"die: {roll}, threshold: {skill_threshold} (adj {adjusted_skill} + synergy {synergy_skill_bonus}), "
                            f"money_mult: {building_money_mult:.4f}, difficulty_penalty: -{difficulty_skill_penalty})"
                        )

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

                                daily_story_traits_granted.extend(daily_story_apply_trait_chance_from_cons(worker, cons))
                                daily_story_traits_removed.extend(daily_story_apply_trait_remove_chance_from_cons(worker, cons))

                                # Apply give_item from daily story consequences (to manager inventory)
                                if "give_item" in cons:
                                    item_data = cons["give_item"]
                                    if isinstance(item_data, str) and item_data:
                                        add_item_to_inventory(manager_inventory, item_data)
                                        renpy.log(f"Daily story: Gave item '{item_data}' to manager")
                                    elif hasattr(item_data, "get"):
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
                        if daily_story_traits_granted:
                            full_description += (
                                "\n\n{color=#88cc88}Trait(s) gained: "
                                + ", ".join(str(t) for t in daily_story_traits_granted)
                                + "{/color}"
                            )
                        if daily_story_traits_removed:
                            full_description += (
                                "\n\n{color=#cc8888}Trait(s) removed: "
                                + ", ".join(str(t) for t in daily_story_traits_removed)
                                + "{/color}"
                            )
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
                        # Check line: multi-skill stories list all skills before ":", then value + " avg"; single skill omits avg.
                        if synergy_skill_bonus > 0:
                            syn_seg = " + {} syn".format(synergy_skill_bonus)
                        elif synergy_skill_bonus < 0:
                            syn_seg = " − {} syn".format(abs(synergy_skill_bonus))
                        else:
                            syn_seg = ""
                        if len(skill_options) > 1:
                            check_skill_label = " ".join(str(s) for s in skill_options)
                            avg_seg = " avg"
                        else:
                            check_skill_label = selected_skill
                            avg_seg = ""
                        if selected_skill:
                            full_description += "\n\n{{color={}}}{{size=20}}({}: {}{}{} — Skill roll {} — {}){{/size}}{{/color}}".format(
                                outcome_color,
                                check_skill_label,
                                adjusted_skill,
                                avg_seg,
                                syn_seg,
                                roll,
                                outcome,
                            )
                        else:
                            full_description += "\n\n{{color={}}}{{size=20}}(Skill roll {} — {}){{/size}}{{/color}}".format(
                                outcome_color, roll, outcome
                            )

                        # Gated stories say WHY they fired: stat gates (romance /
                        # friendship / rebelliousness / libido) show the worker's
                        # current value; trait gates (Loves you, Harem Member...)
                        # show the trait name. Same lookup order as the gate check
                        # (nested skills first, legacy top-level fallback).
                        _gate_reqs = chosen_story.get("stat_requirements", {}) or {}
                        _gate_bits = []
                        if hasattr(_gate_reqs, "items"):
                            for _gate_stat in _gate_reqs:
                                _gate_ws = worker.get("skills", {}) if hasattr(worker, "get") else {}
                                if hasattr(_gate_ws, "get"):
                                    _gate_val = _gate_ws.get(_gate_stat, worker.get(_gate_stat, 0))
                                else:
                                    _gate_val = worker.get(_gate_stat, 0) if hasattr(worker, "get") else 0
                                try:
                                    _gate_bits.append("{} {}".format(str(_gate_stat).capitalize(), int(_gate_val)))
                                except Exception:
                                    _gate_bits.append(str(_gate_stat).capitalize())
                        for _gate_trait in (chosen_story.get("required_traits") or []):
                            _gate_bits.append(str(_gate_trait))
                        if _gate_bits:
                            full_description += "\n{{color=#557799}}{{size=20}}(Unlocked by {}){{/size}}{{/color}}".format(", ".join(_gate_bits))

                        _earn_col = "#228822" if earnings > 0 else ("#aa2222" if earnings < 0 else "#666666")
                        if earnings > 0:
                            full_description += "\n{{color={0}}}{{size=20}}Earned +${1}{{/size}}{{/color}}".format(_earn_col, earnings)
                        elif earnings < 0:
                            full_description += "\n{{color={0}}}{{size=20}}Lost ${1}{{/size}}{{/color}}".format(_earn_col, -earnings)
                        else:
                            full_description += "\n{{color={0}}}{{size=20}}No payout{{/size}}{{/color}}".format(_earn_col)

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
                            "building_type_id": btype.get("id"),
                            "building_type_name": building_type_display_name(btype, btype.get("id", "Building")),
                            "building_display_name": "%s: %s" % (
                                building_type_display_name(btype, btype.get("id", "Building")),
                                (getattr(store, "custom_names", {}) or {}).get(
                                    building_name,
                                    "Building %s" % str(building_name).split("_")[1] if len(str(building_name).split("_")) > 1 else str(building_name).replace("_", " "),
                                ),
                            ),
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
                                
                                # Bonus items: JSON chance only (no difficulty loot multiplier; same idea as monster_worker).
                                bonus_items = loot_data.get("bonus_items", [])
                                for bonus in bonus_items:
                                    item_id = bonus.get("item_id")
                                    chance = min(1.0, max(0.0, bonus.get("chance", 1.0)))
                                    # Keep restricted definitions/inventory intact, but do not
                                    # acquire them through a hidden runtime route.
                                    if not item_content_is_visible(item_id) or (content_object_is_restricted(bonus) and not persistent.nsfw_enabled):
                                        continue
                                    # Only on critical success if specified
                                    if bonus.get("critical_only", False) and outcome != "Critical Success":
                                        continue
                                    if item_id and random.random() <= chance:
                                        add_item_to_inventory(manager_inventory, item_id)
                                        if item_id not in report_entry["loot"]:
                                            report_entry["loot"].append(item_id)
                                        renpy.log(f"Bonus loot: {item_id} (chance: {chance})")
                                
                                # Monster worker loot handling (JSON chance only; no difficulty loot multiplier).
                                if "monster_worker" in loot_data:
                                    chance = min(1.0, max(0.0, loot_data["monster_worker"].get("chance", 1.0)))
                                    filters = loot_data["monster_worker"].get("filters", {"monster": True})
                                    if random.random() <= chance:
                                        looted_worker = loot_monster_worker(filters)
                                        if looted_worker:
                                            # Add the worker to the roster immediately
                                            ensure_worker_defaults(looted_worker)
                                            store.workers.append(looted_worker)
                                            
                                            # Update the report
                                            report_entry["description"] += f"\n\n{{color=#00ff00}}Captured {looted_worker['name']}!{{/color}}"
                                            report_entry["loot"].append(f"Monster Worker: {looted_worker['name']}")
                                            if not hidden_content_job or getattr(persistent, "nsfw_enabled", False):
                                                renpy.notify(f"Captured {looted_worker['name']}!")
                        sanitize_daily_report_entry_for_filter(report_entry, btype, profession, chosen_story)
                        daily_report.append(report_entry)
                        processed_events += 1

        for report_entry in daily_report:
            record_daily_report_moment(report_entry)
        try:
            from fm_lanista.arena_feedback import summarize_daily_arena_feedback
            _arena_feedback = summarize_daily_arena_feedback(daily_report, calculate_total_days())
            if _arena_feedback:
                store.arena_lanista_feedback_pending = _arena_feedback
        except Exception as e:
            renpy.log("Arena Lanista feedback summary failed: %s" % str(e))
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
                if not hasattr(b, "get"):
                    continue
                assigned = b.get("assigned_servants", []) or []
                jobs = b.get("servant_jobs", {}) or {}
                relinked = []
                seen_names = set()
                for sw in assigned:
                    wname = sw.get("name") if hasattr(sw, "get") else None
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
        if hasattr(delta, "get"):
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
        if not hasattr(worker, "get"):
            return totals

        # Traits
        for trait_name in worker.get("traits", []) or []:
            trait_def = next((t for t in traits_list if t.get("name") == trait_name), None)
            if not trait_def:
                continue
            daily_effects = trait_def.get("daily_effects") or {}
            if not hasattr(daily_effects, "get"):
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
            elif hasattr(inv_entry, "get"):
                item_id = inv_entry.get("id") or inv_entry.get("item_id")
                equipped = bool(inv_entry.get("equipped", False))

            if not equipped or not item_id:
                continue

            item_data = next((i for i in items_json.get("items", []) if i.get("id") == item_id), None)
            if not item_data:
                continue

            effect = item_data.get("effect") or {}
            daily_effects = effect.get("daily_effects") or {}
            if not hasattr(daily_effects, "get"):
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
        global daily_report, displayed_workers, can_recruit_today, available_workers, daily_spawns

        # Hard reset of pending random-event context at day start.
        # Prevents stale events from previous flows from appearing together
        # with governor events on the same day.
        store.current_event = None
        store.current_worker = None

        # Close the previous day's history before advancing the calendar. This
        # captures training, interactions and manual changes made in the tavern.
        capture_all_worker_activity_changes()

        # Bankruptcy at day start: catches spending after last daily report (UI uses store.money).
        _thr = getattr(store, "BANKRUPTCY_MONEY_THRESHOLD", BANKRUPTCY_MONEY_THRESHOLD)
        _cur = int(getattr(store, "money", 0) or 0)
        if _cur <= _thr:
            renpy.log(f"BANKRUPTCY: money ${_cur} at start of day (threshold <= {_thr}), game over.")
            return "game_over"

        # Check and update trait durations
        check_trait_durations()
        # One-time migration: rebelliousness no longer uses modifiers; prime _last_applied to avoid delta spike
        if not getattr(persistent, "_rebelliousness_v2_migrated", False):
            for w in getattr(store, "workers", []) or []:
                if hasattr(w, "get"):
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

                # Add base maintenance cost (difficulty + base level)
                base_cost = get_building_base_maintenance_cost(building_name, building)
                building["costs"] += base_cost

                # Add worker comfort costs (comfort x rate each; no building-level multiplier).
                if "assigned_servants" in building:
                    worker_costs, comfort_costs, _upkeep_costs = compute_worker_portion_daily_costs(
                        building.get("assigned_servants") or [],
                        building.get("base_level", 1),
                    )
                    building["costs"] += worker_costs
                    renpy.log(
                        f"Added base cost {base_cost} + worker comfort {comfort_costs} "
                        f"to {building_name}, total: {building['costs']}"
                    )

        try:
            process_manager_auto_rest()
            renpy.log("Manager auto-rest processing completed (before regen)")
        except Exception as e:
            renpy.log(f"Error in manager auto-rest: {e}")

        # Re-run auto-equip at day start so newly obtained gear (including accessories)
        # is considered without requiring manual toggle/profession changes.
        for worker in store.workers:
            if worker_is_in_franchise(worker):
                continue
            if worker.get("auto_equip", False):
                try:
                    run_worker_auto_equip(worker)
                except Exception as e:
                    renpy.log(f"AUTO_EQUIP_DAYSTART error for {worker.get('name', 'Unknown')}: {e}")

        # Recalculate max health/energy and reset daily counters (regen moved to after events and dead check)
        for worker in store.workers:
            if worker_is_in_franchise(worker):
                continue
            worker["max_health"] = calculate_max_health(worker)
            worker["max_energy"] = calculate_max_energy(worker)

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

            # Joy affects rebelliousness: high joy calms, low joy agitates
            if joy > 80:
                old_rebel = worker.get("rebelliousness", 50)
                apply_attribute_change(worker, "rebelliousness", -3)
                renpy.log(f"Joy calming: {worker['name']} rebelliousness {old_rebel} -> {worker['rebelliousness']} (joy {joy} > 80, -3)")
            elif joy < 20:
                old_rebel = worker.get("rebelliousness", 50)
                apply_attribute_change(worker, "rebelliousness", 2)
                renpy.log(f"Joy agitation: {worker['name']} rebelliousness {old_rebel} -> {worker['rebelliousness']} (joy {joy} < 20, +2)")

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

        # Remote franchises use one aggregate calculation and one report row.
        # They deliberately stay outside process_daily_events and its story/media paths.
        process_franchise_holdings_day()

        # Process daily events (THIS POPULATES THE GLOBAL daily_report)
        process_daily_events_result = process_daily_events()
        # Preserve work damage, spent energy, libido and learning before nightly recovery.
        capture_all_worker_activity_changes()
        # Check if process_daily_events triggered an early game over (e.g., if it were to return "game_over")
        if process_daily_events_result == "game_over":
            return "game_over" # Propagate game over if needed

        # --- CALCULATE TOTAL INCOME AND COSTS *AFTER* ALL EVENTS ---
        total_income = sum(report.get("earnings", 0) for report in daily_report)
        renpy.log(f"Calculated total income from daily_report: {total_income}")
        
        # Log detailed breakdown of all earnings
        _daily_debug_log("EARNINGS BREAKDOWN:")
        for i, report in enumerate(daily_report):
            earnings = report.get("earnings", 0)
            worker_name = report.get("worker_name", "Unknown")
            outcome = report.get("result", "Unknown")
            _daily_debug_log(f"  Entry {i+1}: {worker_name} - ${earnings} ({outcome})")

        for building_name in store.owned_buildings:
            building = available_buildings.get(building_name)
            if building:
                # Skill bonus cost is added during process_daily_events, sum final costs here
                renpy.log(f"Final costs for {building_name} after process_daily_events: {building.get('costs', 0)}")
                total_building_costs += building.get('costs', 0)
        # --- END INCOME/COST CALCULATION ---

        # Zero health is reversible: withdraw the worker from duty, never delete the roster entry.
        incapacitated_workers = check_worker_health()
        if incapacitated_workers:
            if len(incapacitated_workers) == 1:
                renpy.say(None, f"{incapacitated_workers[0]} collapsed and was withdrawn from duty to recover.")
            else:
                names_text = ", ".join(incapacitated_workers[:-1]) + f" and {incapacitated_workers[-1]}"
                renpy.say(None, f"{names_text} collapsed and were withdrawn from duty to recover.")

        # --- NIGHTLY REST: Regenerate health/energy/libido AFTER events and incapacitation check ---
        for worker in store.workers:
            if worker_is_in_franchise(worker):
                continue
            old_health = worker["health"]
            base_regen = worker.get("level", 1)
            trait_regen = calculate_health_regeneration(worker)
            health_regen = base_regen + trait_regen
            max_health = calculate_max_health(worker)
            worker["max_health"] = max_health
            new_health = min(worker["health"] + health_regen, max_health)
            worker["health"] = new_health
            if old_health != new_health:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} -> {new_health} (regen: +{health_regen} = level {base_regen} + trait {trait_regen}, max: {max_health})")
            else:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} (already at max {max_health}, regen would be +{health_regen} = level {base_regen} + trait {trait_regen})")

            old_energy = worker["energy"]
            base_energy_regen = worker.get("level", 1)
            try:
                _comfort_lv = int(worker.get("comfort_level", 1))
            except Exception:
                _comfort_lv = 1
            comfort_energy_regen = max(0, _comfort_lv - 1)
            trait_energy_regen = 0
            try:
                trait_energy_regen = calculate_energy_regeneration(worker)
            except Exception:
                trait_energy_regen = 0
            energy_regen = base_energy_regen + comfort_energy_regen + trait_energy_regen
            max_energy = calculate_max_energy(worker)
            worker["max_energy"] = max_energy
            new_energy = min(worker["energy"] + energy_regen, max_energy)
            worker["energy"] = new_energy
            if old_energy != new_energy:
                renpy.log(f"ENERGY REGEN: {worker.get('name', 'Unknown')} energy {old_energy} -> {new_energy} (regen: +{energy_regen} = level {base_energy_regen} + comfort {comfort_energy_regen} + trait {trait_energy_regen}, max: {max_energy})")

            if persistent.nsfw_enabled:
                regenerate_libido(worker)
        # --- END NIGHTLY REST ---

        # Update skill levels and worker levels
        update_skill_levels()
        update_worker_levels()
        # Record recovery and any worker/skill level-ups as separate changes.
        capture_all_worker_activity_changes()

        # Record each surviving worker's net HP loss for the report badges.
        # Pop guarantees a later day cannot consume a stale baseline.
        for _wn, _hp_delta in collect_net_hp_losses(
            store.workers,
            renpy.session.pop("_fm_daily_hp_at_start", {}),
        ).items():
            _record_daily_worker_delta(_wn, "hp", _hp_delta)

        # Reload available workers unconditionally
        available_workers = load_buy_workers()
        renpy.log(f"Reloaded available_workers: {[w['name'] for w in available_workers]}")

        # Update displayed_workers using the proper function that handles JSON exhaustion
        update_displayed_workers()
        renpy.log(f"Updated displayed_workers: {[w['name'] for w in displayed_workers]}")

        # Apply daily ledger to store.money (same variable as UI/screens; avoid bare `money` in init python).
        old_money = int(getattr(store, "money", 0) or 0)
        store.money = old_money + total_income - total_building_costs
        store.money = int(store.money)
        
        # Log money changes for debugging
        renpy.log(f"MONEY CHANGE: ${old_money} + ${total_income} - ${total_building_costs} = ${store.money}")

        # Bankruptcy (game over): must run here, before governor/random-event early returns.
        # Those paths used to skip the check at the end of this function entirely.
        _thr = getattr(store, "BANKRUPTCY_MONEY_THRESHOLD", BANKRUPTCY_MONEY_THRESHOLD)
        if store.money <= _thr:
            renpy.log(f"BANKRUPTCY: final money ${store.money} (threshold <= {_thr}), game over.")
            return "game_over"
        
        # Check objective completion after money change (for Objective 4: 5000 coins)
        if hasattr(store, 'tutorial_active') and store.tutorial_active:
            try:
                check_objective_completion()
            except Exception as e:
                renpy.log(f"Error checking objective completion after daily money update: {e}")
        
        # Check for daily revenue achievement (Objective 15; flag key is legacy "10k")
        if total_income >= 3000 and not store.event_flags.get("daily_revenue_10k_achieved", False):
            store.event_flags["daily_revenue_10k_achieved"] = True
            renpy.log("ACHIEVEMENT: Daily revenue objective (3,000 in one day) achieved!")

        # Expire timed worker flags (interaction flags with duration > 0, e.g. the
        # 4/5-day flags from interactions_special.json). See expire_worker_flags
        # in worker_interactions.rpy for the duration semantics.
        try:
            expire_worker_flags()
        except Exception as e:
            renpy.log(f"FLAGS ERROR expiring worker flags: {e}")

        # Restore sabotaged building skill bonuses once their timer expires.
        # Counterpart of the governor-tension sabotage effect, which promised a
        # 3-day recovery but never restored anything. Flags written at sabotage
        # time: sabotage_restore_<building> = expiry day, sabotage_amount_<building>.
        try:
            _today_total = calculate_total_days()
            for _flag in [k for k in list(store.event_flags.keys()) if k.startswith("sabotage_restore_")]:
                if _today_total >= store.event_flags.get(_flag, 0):
                    _bname = _flag[len("sabotage_restore_"):]
                    _amount = store.event_flags.pop("sabotage_amount_" + _bname, 10)
                    _b = available_buildings.get(_bname)
                    if _b is not None:
                        _b["skill_bonus"] = _b.get("skill_bonus", 0) + _amount
                        renpy.notify(f"{custom_names.get(_bname, _bname)} has recovered from the sabotage.")
                        renpy.log(f"TENSION: Restored sabotaged skill_bonus (+{_amount}) on {_bname}")
                    store.event_flags.pop("sabotage_" + _bname, None)
                    del store.event_flags[_flag]
        except Exception as e:
            renpy.log(f"TENSION ERROR restoring sabotage: {e}")

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

        # Fallback: surface events with exact_date matching today in case the
        # guaranteed/probability classification missed them. Scan the FILTERED
        # list: scanning all_events bypassed occurrence caps and flags, so
        # consumed one-shots re-fired every anniversary.
        try:
            today_day = store.current_day
            today_month = store.current_month
            for e in possible_events:
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

        # Immediate path: if there are guaranteed/date-specific events, trigger one directly.
        # IMPORTANT: apply worker availability/name filters here too, otherwise this path can
        # bypass worker_name / specific_worker_images constraints for 100% events.
        if guaranteed_pool:
            guaranteed_valid_events = []
            for event in guaranteed_pool:
                has_identity_filter = store._event_has_identity_filters(event)

                random_worker_flag = event.get("random_worker", False)
                worker_selection = event.get("worker_selection", "none")
                event_building_types = event.get("building_type", [])

                eligible_workers = []
                if event_building_types:
                    visible_building_names = {name for name, _building in get_content_visible_event_buildings(event, available_buildings)}
                    eligible_workers = [
                        w for w in store.workers
                        if w.get("assigned_building", "Unassigned") != "Unassigned"
                        and w.get("assigned_building") in visible_building_names
                    ]
                else:
                    eligible_workers = store.workers

                # Gender gate lives in filter_workers_for_event_progress (normalized:
                # "any"/null = no gate); a raw equality filter here broke on "any".
                eligible_workers = filter_workers_for_event_progress(eligible_workers, event)
                eligible_workers = filter_workers_for_event_building_policy(eligible_workers, event)

                worker = None
                is_available = False

                if has_identity_filter and not random_worker_flag:
                    target_worker = next((w for w in eligible_workers if store._worker_matches_event_identity(w, event)), None)
                    if target_worker:
                        worker, is_available = target_worker, True
                elif random_worker_flag:
                    if worker_selection == "none" or worker_selection == "random":
                        candidate_workers = eligible_workers
                        if has_identity_filter:
                            candidate_workers = [w for w in eligible_workers if store._worker_matches_event_identity(w, event)]
                        if candidate_workers:
                            worker, is_available = random.choice(candidate_workers), True
                    elif worker_selection == "choose":
                        if has_identity_filter:
                            is_available = any(store._worker_matches_event_identity(w, event) for w in eligible_workers)
                        else:
                            is_available = bool(eligible_workers)
                elif worker_selection == "random":
                    if eligible_workers:
                        worker, is_available = random.choice(eligible_workers), True
                elif worker_selection == "choose":
                    is_available = bool(eligible_workers)
                elif worker_selection == "none":
                    is_available = True

                if is_available:
                    guaranteed_valid_events.append((event, worker))

            if guaranteed_valid_events:
                chosen_tuple = choose_guaranteed_event_tuple(
                    guaranteed_valid_events,
                    store.current_day,
                    store.current_month,
                )
                chosen_event, chosen_worker = chosen_tuple
                renpy.log(f"Triggering guaranteed event immediately: {chosen_event.get('id')}")
                store.current_event = chosen_event
                store.current_worker = chosen_worker
                return "handle_random_event"
            else:
                renpy.log("Guaranteed/date-specific pool had no valid events after worker availability checks.")

        # NOTE: the guaranteed pool was fully handled by the immediate path above.
        # Reaching this point means it was empty or had no eligible worker today,
        # so re-locking onto it here would only starve the other pools (it used
        # to: one unsatisfiable guaranteed event blocked every other event).
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
                or event_is_character_arc(e)
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
        
        should_trigger_event = False
        events_to_consider = []

        # Priority events (custom probability OR explicit priority/story tags) are
        # NOT affected by managers. Each is gated exactly once, per-event, in the
        # individual probability phase below. (They used to be double-gated: one
        # shared roll against the pool's MAX probability here, then a second,
        # manager-reduced roll below for events without an explicit probability —
        # contradicting the "not affected by managers" design.)
        if priority_events:
            should_trigger_event = True
            events_to_consider.extend(priority_events)
            renpy.log(f"DEBUG: {len(priority_events)} priority event(s) advance to the individual probability phase (NOT affected by managers)")

        # Normal events: one pool-level roll at the flat base. Manager gating is
        # now PER-BUILDING and applied in the individual-probability phase below
        # (spec 2026-08-13: a manager calms their own building, not the world).
        if normal_events and has_active_professions:
            base_probability = 30
            normal_roll = renpy.random.randint(1, 100)
            renpy.log(f"DEBUG: Normal events roll: {normal_roll}/100 (base: {base_probability}%; manager gating is per-building in the individual phase)")
            if normal_roll <= base_probability:
                should_trigger_event = True
                events_to_consider.extend(normal_events)

        # If any check passed, consider those events
        if events_to_consider:
            possible_events = events_to_consider
        
        if should_trigger_event:
            renpy.log("Triggering event check...")

            if possible_events:
                # Further filter based on worker availability for the event
                valid_events = []
                for event in possible_events:
                    event_id = event.get("id", "unknown")
                    renpy.log(f"Checking worker availability for event {event_id}...")

                    has_identity_filter = store._event_has_identity_filters(event)
                    random_worker_flag = event.get("random_worker", False) # Renamed to avoid conflict
                    worker_selection = event.get("worker_selection", "none")
                    event_building_types = event.get("building_type", [])

                    # Determine eligible workers
                    eligible_workers = []
                    if event_building_types:
                        visible_building_names = {name for name, _building in get_content_visible_event_buildings(event, available_buildings)}
                        eligible_workers = [
                            w for w in store.workers
                            if w.get("assigned_building", "Unassigned") != "Unassigned"
                            and w.get("assigned_building") in visible_building_names
                        ]
                    else:
                        eligible_workers = store.workers

                    # Gender gate lives in filter_workers_for_event_progress (normalized:
                    # "any"/null = no gate); a raw equality filter here broke on "any".
                    eligible_workers = filter_workers_for_event_progress(eligible_workers, event)
                    eligible_workers = filter_workers_for_event_building_policy(eligible_workers, event)

                    worker = None
                    is_available = False

                    if has_identity_filter and not random_worker_flag:
                        target_worker = next((w for w in eligible_workers if store._worker_matches_event_identity(w, event)), None)
                        if target_worker:
                            worker, is_available = target_worker, True
                    elif random_worker_flag:
                        if worker_selection == "none" or worker_selection == "random":
                            candidate_workers = eligible_workers
                            if has_identity_filter:
                                candidate_workers = [w for w in eligible_workers if store._worker_matches_event_identity(w, event)]
                            if candidate_workers:
                                worker, is_available = random.choice(candidate_workers), True
                        elif worker_selection == "choose":
                            if has_identity_filter:
                                is_available = any(store._worker_matches_event_identity(w, event) for w in eligible_workers)
                            else:
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

                    for event, worker in valid_events:
                        event_id = event.get("id")
                        # Priority events roll their OWN probability (default 50%),
                        # never manager-reduced. Normal events without a custom
                        # probability use the PER-BUILDING manager-gated base
                        # (worker's building, else min across matching buildings).
                        event_probability = event.get("event_probability")
                        if _is_priority_event(event):
                            event_probability = max(1, event_probability if event_probability is not None else 50)
                        elif event_probability is None:
                            event_probability = _fm_normal_event_probability(event, worker)
                            renpy.log(f"DEBUG: {event_id} per-building gated probability: {event_probability}%")
                        else:
                            # Custom probability on a normal event - use it exactly as
                            # defined, NOT affected by managers; keep a 1% floor.
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
                                renpy.log(
                                    f"Event {event.get('id')} passed individual probability check ({individual_roll} <= {event_probability}%)"
                                )
                            else:
                                renpy.log(
                                    f"Event {event.get('id')} failed individual probability check ({individual_roll} > {event_probability}%)"
                                )

                    if probability_filtered_events:
                        # Use weight-based selection among events that passed probability check
                        chosen_event_tuple = None
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
        renpy.log(
            f"End of Day: Income=${total_income}, Costs=${total_building_costs}, "
            f"Final Money=${getattr(store, 'money', 0)}"
        )
        
        # Daily report will be shown in next_day label after this returns
        return "tavern"
