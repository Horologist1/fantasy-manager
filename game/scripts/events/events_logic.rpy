# events_logic.rpy

init python:
    from fm_events.building_policy import (
        choice_allowed_by_building_policy,
        event_has_policy_relevant_choices,
        event_worker_allowed_by_building_policy,
    )

    EVENT_FILTER_DEBUG = False
    CHARACTER_EVENT_GLOBAL_COOLDOWN_DAYS = 5
    CHARACTER_EVENT_POOL_CAP = 1

    def _event_filter_log(message, force=False):
        if force or EVENT_FILTER_DEBUG or getattr(config, "developer", False):
            renpy.log(message)

    def _normalize_event_profession_id(pid):
        if pid is None:
            return ""
        return str(pid).strip().lower()

    def choice_is_visible_for_content_filter(choice):
        """Apply the content policy to one choice without mutating event data."""
        return bool(getattr(persistent, "nsfw_enabled", False) or not content_object_is_restricted(choice))

    def event_is_visible_for_content_filter(event, include_pending_building=True):
        """Reject serialized NSFW events before any text, choices, music, or media is shown."""
        if not event or not hasattr(event, "get") or getattr(persistent, "nsfw_enabled", False):
            return True
        if content_object_is_restricted(event):
            return False
        choices = event.get("choices", []) or []
        if choices and not any(choice_is_visible_for_content_filter(choice) for choice in choices):
            return False

        pending_building_name = getattr(store, "current_affected_building", None) if include_pending_building else None
        if pending_building_name:
            pending_building, _key = _resolve_building_by_name(pending_building_name)
            pending_type_id = pending_building.get("type") if pending_building else None
            pending_type = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == pending_type_id), None)
            if pending_type and not building_type_is_visible(pending_type):
                return False

        required_types = event.get("building_type", []) or []
        if isinstance(required_types, str):
            required_types = [required_types]
        matched_types = [bt for bt in building_types_json.get("building_types", []) if bt.get("id") in required_types]
        matched_ids = {bt.get("id") for bt in matched_types}
        if required_types and any(type_id not in matched_ids for type_id in required_types):
            return False
        if matched_types and not any(building_type_is_visible(bt) for bt in matched_types):
            return False
        return True

    def get_content_visible_event_buildings(event, buildings=None):
        """Return owned matching buildings without letting mixed events select hidden types in SFW mode."""
        buildings = buildings if buildings is not None else available_buildings
        required_types = (event or {}).get("building_type", []) or []
        if isinstance(required_types, str):
            required_types = [required_types]
        result = []
        for building_name, building in (buildings or {}).items():
            if not hasattr(building, "get") or not building.get("owned", False):
                continue
            btype_id = building.get("type")
            if required_types and btype_id not in required_types:
                continue
            btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == btype_id), None)
            if btype and not building_type_is_visible(btype):
                continue
            result.append((building_name, building))
        return result

    def event_has_restricted_content(event, choice=None):
        """Classify event provenance independently of the current NSFW toggle."""
        event = event or {}
        if content_object_is_restricted(event) or content_object_is_restricted(choice):
            return True
        affected_name = getattr(store, "current_affected_building", None)
        affected_building, _affected_key = _resolve_building_by_name(affected_name) if affected_name else (None, None)
        affected_type = affected_building.get("type") if affected_building else None
        required_types = event.get("building_type", []) or []
        if isinstance(required_types, str):
            required_types = [required_types]
        type_ids = [affected_type] if affected_type else list(required_types)
        for btype in building_types_json.get("building_types", []) or []:
            if btype.get("id") in type_ids and content_object_is_restricted(btype):
                return True
        return False

    store.choice_is_visible_for_content_filter = choice_is_visible_for_content_filter
    store.event_is_visible_for_content_filter = event_is_visible_for_content_filter
    store.get_content_visible_event_buildings = get_content_visible_event_buildings
    store.event_has_restricted_content = event_has_restricted_content

    def event_worker_is_visible_for_content_filter(worker):
        """Keep restricted workers out of event presentation without altering the roster."""
        if not worker or not hasattr(worker, "get"):
            return True
        return bool(
            getattr(persistent, "nsfw_enabled", False)
            or not content_object_is_restricted(worker)
        )

    def worker_matches_event_progress(worker, event):
        """Check save-safe event-level progression gates against permanent worker values."""
        progress = (event or {}).get("worker_progress") or {}
        if not progress:
            return True
        if not worker or not hasattr(worker, "get"):
            return False

        def _meets(actual, required):
            try:
                if isinstance(required, bool):
                    return False
                return float(actual) >= float(required)
            except (TypeError, ValueError):
                return False

        if "min_level" in progress and not _meets(worker.get("level", 0), progress.get("min_level")):
            return False

        min_stats = progress.get("min_stats") or {}
        if not hasattr(min_stats, "items"):
            return False
        for stat_name, required in min_stats.items():
            if not _meets(worker.get(stat_name, 0), required):
                return False

        min_skills = progress.get("min_skills") or {}
        if not hasattr(min_skills, "items"):
            return False
        base_skills = worker.get("skills") or {}
        if not hasattr(base_skills, "get"):
            base_skills = {}
        for skill_name, required in min_skills.items():
            if not _meets(base_skills.get(skill_name, 0), required):
                return False

        if "any_skills" in progress:
            any_skills = progress.get("any_skills")
            if not any_skills or not hasattr(any_skills, "items"):
                return False
            if not any(_meets(base_skills.get(skill_name, 0), required) for skill_name, required in any_skills.items()):
                return False

        required_traits = progress.get("required_traits") or []
        worker_traits = set(worker.get("traits") or [])
        if any(trait not in worker_traits for trait in required_traits):
            return False
        return True

    def _event_worker_gender_requirement(event):
        """Normalized worker_gender_requirement: "male"/"female", else None.
        "any", "", null and unknown values mean no gate — a truthy "any" must never
        reach an equality filter (it would exclude every worker)."""
        req = (event or {}).get("worker_gender_requirement") if hasattr(event, "get") else None
        req = str(req or "").strip().lower()
        return req if req in ("male", "female") else None

    def filter_workers_for_event_progress(worker_list, event):
        """Return content-visible workers that satisfy progression without mutating the roster.
        Honors worker_gender_requirement here (the shared chokepoint) so the
        resolution-time pickers in events.rpy can never leak the other gender."""
        gender_req = _event_worker_gender_requirement(event)
        return [
            worker for worker in (worker_list or [])
            if not worker_is_in_franchise(worker)
            and event_worker_is_visible_for_content_filter(worker)
            and worker_matches_event_progress(worker, event)
            and (gender_req is None
                 or str(worker.get("gender", "") if hasattr(worker, "get") else "").strip().lower() == gender_req)
        ]

    def worker_matches_event_choice_building_policy(worker, event, choice):
        """Apply the assigned building's skill policy to one event choice/worker pair."""
        if not worker or not hasattr(worker, "get"):
            return False
        building_name = worker.get("assigned_building")
        building, _key = _resolve_building_by_name(building_name) if building_name else (None, None)
        if not building:
            return not event_has_policy_relevant_choices(event)
        required_types = (event or {}).get("building_type", []) or []
        if isinstance(required_types, str):
            required_types = [required_types]
        if required_types and building.get("type") not in required_types:
            return False
        return choice_allowed_by_building_policy(
            building,
            choice,
            worker.get("gender"),
        )

    def filter_workers_for_event_choice_building_policy(worker_list, event, choice):
        """Keep only workers allowed to depict the selected choice in their building."""
        return [
            worker for worker in (worker_list or [])
            if worker_matches_event_choice_building_policy(worker, event, choice)
        ]

    def filter_workers_for_event_building_policy(worker_list, event):
        """Keep workers who can perform at least one policy-relevant event choice."""
        if not event_has_policy_relevant_choices(event):
            return list(worker_list or [])
        result = []
        for worker in (worker_list or []):
            if not worker or not hasattr(worker, "get"):
                continue
            building_name = worker.get("assigned_building")
            building, _key = _resolve_building_by_name(building_name) if building_name else (None, None)
            if building and event_worker_allowed_by_building_policy(building, event, worker):
                result.append(worker)
        return result

    def event_building_policy_has_eligible_worker(building, event):
        """True when this building can cast the event without violating its skill policy."""
        if not event_has_policy_relevant_choices(event):
            return True
        candidates = filter_workers_for_event_progress(
            (building or {}).get("assigned_servants", []) or [],
            event,
        )
        if store._event_has_identity_filters(event):
            candidates = [
                worker for worker in candidates
                if store._worker_matches_event_identity(worker, event)
            ]
        return any(
            event_worker_allowed_by_building_policy(building, event, worker)
            for worker in candidates
        )

    store.worker_matches_event_choice_building_policy = worker_matches_event_choice_building_policy
    store.filter_workers_for_event_choice_building_policy = filter_workers_for_event_choice_building_policy
    store.filter_workers_for_event_building_policy = filter_workers_for_event_building_policy
    store.event_building_policy_has_eligible_worker = event_building_policy_has_eligible_worker

    def event_choice_has_qualifying_worker(choice, event):
        """Mirror of the post-choice eligibility build in events.rpy (choose/random):
        True when at least one appropriately-assigned worker could take this
        choice's skill check. Lets the choice screen disable dead-end options
        BEFORE the player burns the event on "no eligible workers"."""
        if not choice or not hasattr(choice, "get"):
            return True
        condition_skill = choice.get("condition")
        if not condition_skill or condition_skill == "building_skill":
            return True
        try:
            threshold = int(choice.get("threshold", 0) or 0)
        except Exception:
            threshold = 0
        workers = getattr(store, "workers", []) or []
        buildings = getattr(store, "available_buildings", {}) or {}
        affected = getattr(store, "current_affected_building", None)
        event_building_types = (event or {}).get("building_type", []) if hasattr(event, "get") else []
        if affected:
            pool = [w for w in workers if w.get("assigned_building") == affected]
        elif event_building_types:
            pool = [
                w for w in workers
                if w.get("assigned_building", "Unassigned") != "Unassigned"
                and w.get("assigned_building") in buildings
                and buildings[w.get("assigned_building")].get("type") in event_building_types
            ]
        else:
            pool = list(workers)
        pool = filter_workers_for_event_progress(pool, event)
        req_tr = list(choice.get("required_traits", []) or [])
        if choice.get("required_trait"):
            req_tr.append(choice.get("required_trait"))
        ex_tr = choice.get("excluded_traits", []) or []
        if req_tr or ex_tr:
            pool = [w for w in pool if store._worker_meets_trait_requirements(w, req_tr, ex_tr)]
        if store._event_has_identity_filters(event):
            pool = [w for w in pool if store._worker_matches_event_identity(w, event)]
        pool = filter_workers_for_event_choice_building_policy(pool, event, choice)
        if threshold > 0:
            pool = [w for w in pool if get_event_worker_skill_check_info(w, choice).get("roll_skill", 0) >= threshold]
        return bool(pool)

    def event_progress_is_satisfied(event, worker_pool=None):
        """Resolve progression against the event's fixed identity before admitting it to the pool."""
        if not (event or {}).get("worker_progress"):
            return True
        candidates = list(worker_pool if worker_pool is not None else (getattr(store, "workers", []) or []))
        has_identity = getattr(store, "_event_has_identity_filters", None)
        matches_identity = getattr(store, "_worker_matches_event_identity", None)
        if callable(has_identity) and has_identity(event) and callable(matches_identity):
            candidates = [worker for worker in candidates if matches_identity(worker, event)]
        return bool(filter_workers_for_event_progress(candidates, event))

    def event_is_character_arc(event):
        """Authored character arcs are explicitly classified; never infer them from IDs."""
        return bool((event or {}).get("arc_id"))

    def character_event_cooldown_ready(current_day=None):
        """Global character-event cadence, independent of manager count."""
        current_day = calculate_total_days() if current_day is None else current_day
        last_day = getattr(store, "character_event_last_day", None)
        if last_day is None:
            return True
        try:
            return int(current_day) - int(last_day) >= CHARACTER_EVENT_GLOBAL_COOLDOWN_DAYS
        except (TypeError, ValueError):
            return True

    def limit_character_arc_candidates(events):
        """Keep ordinary events plus a bounded weighted sample of eligible character arcs."""
        ordinary = [event for event in (events or []) if not event_is_character_arc(event)]
        arcs = [event for event in (events or []) if event_is_character_arc(event)]
        if not arcs or not character_event_cooldown_ready():
            return ordinary

        remaining = list(arcs)
        selected = []
        cap = max(0, int(CHARACTER_EVENT_POOL_CAP))
        while remaining and len(selected) < cap:
            weights = []
            for event in remaining:
                try:
                    weights.append(max(0.0, float(event.get("weight", 1))))
                except (TypeError, ValueError):
                    weights.append(0.0)
            total = sum(weights)
            if total <= 0:
                break
            roll = renpy.random.uniform(0, total)
            cumulative = 0.0
            picked_index = len(remaining) - 1
            for index, weight in enumerate(weights):
                cumulative += weight
                if roll <= cumulative:
                    picked_index = index
                    break
            selected.append(remaining.pop(picked_index))
        return ordinary + selected

    def record_character_event_fired(event):
        """Start the global arc cooldown without marking the event completed."""
        if not event_is_character_arc(event):
            return False
        current_day = int(calculate_total_days())
        store.character_event_last_day = current_day
        return True

    def reconcile_cancelled_character_arc_timestamps(events):
        """Remove legacy completion stamps proven to come from cancelled arc events."""
        flags = getattr(store, "event_flags", None)
        occurrences = getattr(store, "event_occurrences", None)
        if not hasattr(flags, "get") or not hasattr(occurrences, "get"):
            return []

        removed = []
        for event in events or []:
            if not (event or {}).get("arc_id"):
                continue
            event_id = str(event.get("id", "")).strip()
            timestamp_flag = str(event.get("completion_timestamp_flag", "")).strip()
            if not event_id or not timestamp_flag or timestamp_flag not in flags:
                continue
            if not flags.get(f"{event_id}_passed", False):
                continue
            try:
                completed_count = int(occurrences.get(event_id, 0) or 0)
            except (TypeError, ValueError):
                completed_count = 0
            if completed_count <= 0:
                flags.pop(timestamp_flag, None)
                removed.append(timestamp_flag)
        return removed

    def reconcile_shop_unlock_state():
        """Heal legacy Shop 2 UI state into the event-gating namespace."""
        if not hasattr(store, "unlocked_shops") or store.unlocked_shops is None:
            store.unlocked_shops = {}
        if not hasattr(store, "event_flags") or store.event_flags is None:
            store.event_flags = {}

        changed = []
        shop2_open = bool(
            store.unlocked_shops.get("shop2", False)
            or store.event_flags.get("shop2_unlocked", False)
        )
        if shop2_open:
            if not store.unlocked_shops.get("shop2", False):
                store.unlocked_shops["shop2"] = True
                changed.append("unlocked_shops.shop2")
            if not store.event_flags.get("shop2_unlocked", False):
                store.event_flags["shop2_unlocked"] = True
                changed.append("shop2_unlocked")
            timestamp = store.event_flags.get("shop2_unlock_timestamp")
            if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
                store.event_flags["shop2_unlock_timestamp"] = int(calculate_total_days())
                changed.append("shop2_unlock_timestamp")

        shop3_open = bool(
            store.unlocked_shops.get("shop3", False)
            or store.event_flags.get("shop3_unlocked", False)
        )
        if shop3_open:
            if not store.unlocked_shops.get("shop3", False):
                store.unlocked_shops["shop3"] = True
                changed.append("unlocked_shops.shop3")
            if not store.event_flags.get("shop3_unlocked", False):
                store.event_flags["shop3_unlocked"] = True
                changed.append("shop3_unlocked")
        return changed

    def record_character_event_completed(event):
        """Stamp arc completion only after a player choice has resolved."""
        if not event_is_character_arc(event):
            return False
        timestamp_flag = str((event or {}).get("completion_timestamp_flag", "")).strip()
        if timestamp_flag:
            if not hasattr(store, "event_flags") or store.event_flags is None:
                store.event_flags = {}
            store.event_flags[timestamp_flag] = int(calculate_total_days())
        return True

    store.worker_matches_event_progress = worker_matches_event_progress
    store.filter_workers_for_event_progress = filter_workers_for_event_progress
    store.event_progress_is_satisfied = event_progress_is_satisfied
    store.event_is_character_arc = event_is_character_arc
    store.character_event_cooldown_ready = character_event_cooldown_ready
    store.limit_character_arc_candidates = limit_character_arc_candidates
    store.record_character_event_fired = record_character_event_fired
    store.reconcile_cancelled_character_arc_timestamps = reconcile_cancelled_character_arc_timestamps
    store.record_character_event_completed = record_character_event_completed

    def _job_is_active_profession(job_val):
        """True if servant_jobs value counts as a real profession (not empty/rest/unassigned)."""
        j = _normalize_event_profession_id(job_val)
        if not j:
            return False
        if j in ("rest", "unassigned"):
            return False
        return True

    def _skill_name_for_building_type(btype_id):
        if not btype_id:
            return None
        try:
            btlist = building_types_json.get("building_types", []) or []
        except Exception:
            btlist = []
        for bt in btlist:
            if bt.get("id") == btype_id:
                sn = bt.get("skill_name")
                return str(sn).strip() if sn else None
        return None

    def _building_has_any_active_profession_in(building, profession_ids):
        """At least one assigned servant has an active job id in profession_ids (case-insensitive)."""
        ids = {_normalize_event_profession_id(p) for p in (profession_ids or []) if _normalize_event_profession_id(p)}
        if not ids:
            return True
        jobs = building.get("servant_jobs") or {}
        if not hasattr(jobs, "get"):
            jobs = {}
        for worker in building.get("assigned_servants", []) or []:
            wn = (worker or {}).get("name")
            if not wn:
                continue
            job = jobs.get(wn)
            if not _job_is_active_profession(job):
                continue
            if _normalize_event_profession_id(job) in ids:
                return True
        return False

    def _building_respects_forbidden_professions(building, profession_ids):
        """No assigned servant has an active job id in profession_ids."""
        forbidden = {_normalize_event_profession_id(p) for p in (profession_ids or []) if _normalize_event_profession_id(p)}
        if not forbidden:
            return True
        jobs = building.get("servant_jobs") or {}
        if not hasattr(jobs, "get"):
            jobs = {}
        for worker in building.get("assigned_servants", []) or []:
            wn = (worker or {}).get("name")
            if not wn:
                continue
            job = jobs.get(wn)
            if not _job_is_active_profession(job):
                continue
            if _normalize_event_profession_id(job) in forbidden:
                return False
        return True

    def effect_worker_filter_has_constraints(filt):
        """True if choice-level effect_worker_filter should be enforced (non-empty constraints)."""
        if not filt or not hasattr(filt, "get"):
            return False
        if filt.get("required_active_professions"):
            return True
        if filt.get("forbidden_active_professions"):
            return True
        if filt.get("required_traits"):
            return True
        if filt.get("required_trait"):
            return True
        if filt.get("excluded_traits"):
            return True
        ms = filt.get("min_skill")
        if ms is None:
            ms = filt.get("required_building_worker_min_skill")
        try:
            if ms is not None and int(ms) >= 0:
                return True
        except Exception:
            pass
        return False

    def worker_matches_effect_worker_filter(worker, building, filt):
        """
        True if this worker passes choice-level effect_worker_filter (active job in building,
        traits, optional min skill). Used when applying event effects so manager-only staff
        do not receive prostitute-only outcomes, etc.
        """
        if not filt or not hasattr(filt, "get"):
            return True
        if not worker or not hasattr(worker, "get"):
            return False
        wname = worker.get("name")
        job = None
        if building and hasattr(building, "get") and wname:
            jobs = building.get("servant_jobs") or {}
            if hasattr(jobs, "get"):
                job = jobs.get(wname)
        jnorm = _normalize_event_profession_id(job)
        active = _job_is_active_profession(job)
        forb = filt.get("forbidden_active_professions") or []
        if forb:
            fset = {_normalize_event_profession_id(x) for x in forb if _normalize_event_profession_id(x)}
            if active and jnorm in fset:
                return False
        req = filt.get("required_active_professions") or []
        if req:
            rset = {_normalize_event_profession_id(x) for x in req if _normalize_event_profession_id(x)}
            if not active:
                return False
            if jnorm not in rset:
                return False
        worker_traits = set((worker.get("traits") or []) if hasattr(worker, "get") else [])
        rt = list(filt.get("required_traits") or [])
        if filt.get("required_trait"):
            rt.append(filt.get("required_trait"))
        for t in rt:
            if t and t not in worker_traits:
                return False
        for t in filt.get("excluded_traits") or []:
            if t and t in worker_traits:
                return False
        ms = filt.get("min_skill")
        if ms is None:
            ms = filt.get("required_building_worker_min_skill")
        try:
            min_i = int(ms) if ms is not None else None
        except Exception:
            min_i = None
        if min_i is not None:
            skill_nm = filt.get("skill_name") or filt.get("required_building_worker_skill")
            resolved = str(skill_nm).strip() if skill_nm else ""
            if not resolved and building and hasattr(building, "get"):
                resolved = _skill_name_for_building_type(building.get("type")) or ""
            if not resolved:
                return False
            try:
                if calculate_skill_with_traits(worker, resolved) < min_i:
                    return False
            except Exception:
                return False
        return True

    def filter_workers_for_effect_worker_filter(worker_list, filt, restrict, building):
        """Subset of worker_list that passes effect_worker_filter; unrestricted if not restrict or no constraints."""
        if not worker_list:
            return []
        if not restrict or not effect_worker_filter_has_constraints(filt):
            return list(worker_list)
        out = []
        for w in worker_list:
            if worker_matches_effect_worker_filter(w, building, filt):
                out.append(w)
        return out

    store.effect_worker_filter_has_constraints = effect_worker_filter_has_constraints
    store.worker_matches_effect_worker_filter = worker_matches_effect_worker_filter
    store.filter_workers_for_effect_worker_filter = filter_workers_for_effect_worker_filter

    def _coerce_event_min_skill(event):
        """Return int min skill or None if absent/invalid."""
        if "required_building_worker_min_skill" not in event:
            return None
        raw = event.get("required_building_worker_min_skill")
        if raw is None:
            return None
        try:
            return int(raw)
        except Exception:
            return None

    def event_uses_building_availability_gates(event):
        """True if select_possible_events must scan owned buildings for this event."""
        if bool(event.get("requires_assigned_worker", False)):
            return True
        if event.get("required_building_worker_traits", []):
            return True
        if event.get("required_active_professions", []):
            return True
        if event.get("forbidden_active_professions", []):
            return True
        if _coerce_event_min_skill(event) is not None:
            return True
        if event_has_policy_relevant_choices(event):
            return True
        return False

    def _building_matches_event_worker_requirements(
        building,
        required_worker_traits=None,
        require_worker=False,
        min_skill=None,
        skill_name=None,
    ):
        """Assigned workers: optional require_worker, trait subset on one worker, optional min skill (same worker)."""
        assigned = building.get("assigned_servants", []) or []
        if require_worker and not assigned:
            return False

        required_worker_traits = required_worker_traits or []
        req = set(required_worker_traits)
        need_traits = bool(req)
        need_skill = isinstance(min_skill, int)

        if not need_traits and not need_skill:
            return True

        resolved_skill = skill_name
        if need_skill:
            rs = str(resolved_skill).strip() if resolved_skill is not None else ""
            if not rs:
                resolved_skill = _skill_name_for_building_type(building.get("type"))
            else:
                resolved_skill = rs
        else:
            resolved_skill = None

        for worker in assigned:
            if need_traits:
                worker_traits = set((worker or {}).get("traits", []) or [])
                if not req.issubset(worker_traits):
                    continue
            if need_skill:
                if not resolved_skill:
                    continue
                try:
                    level = calculate_skill_with_traits(worker, resolved_skill)
                except Exception:
                    level = 0
                if level < min_skill:
                    continue
            return True
        return False

    def building_matches_random_event_availability(building, event):
        """
        True if this owned building passes all event gates that depend on assigned workers,
        servant_jobs professions, and optional min skill. Used by select_possible_events
        and handle_random_event when picking current_affected_building.
        """
        require_worker = bool(event.get("requires_assigned_worker", False))
        required_worker_traits = event.get("required_building_worker_traits", []) or []
        req_present = event.get("required_active_professions", []) or []
        req_forbid = event.get("forbidden_active_professions", []) or []
        min_skill = _coerce_event_min_skill(event)
        skill_nm = event.get("required_building_worker_skill")

        if not event_uses_building_availability_gates(event):
            return True

        if req_present and not _building_has_any_active_profession_in(building, req_present):
            return False
        if req_forbid and not _building_respects_forbidden_professions(building, req_forbid):
            return False

        if not _building_matches_event_worker_requirements(
            building,
            required_worker_traits=required_worker_traits,
            require_worker=require_worker,
            min_skill=min_skill,
            skill_name=skill_nm,
        ):
            return False
        if not event_building_policy_has_eligible_worker(building, event):
            return False
        return True

    store.building_matches_random_event_availability = building_matches_random_event_availability
    store.event_uses_building_availability_gates = event_uses_building_availability_gates

    def get_player_manager_gender():
        """Canonical manager gender for gating: Lord -> male, otherwise (e.g. Lady) -> female."""
        title = getattr(store, "player_title", None)
        if title and str(title).lower().strip() == "lord":
            return "male"
        return "female"

    def normalize_player_gender_requirement(req):
        """
        Map JSON player_gender_requirement to 'male' or 'female'.
        Accepts male/female/lord/lady (case-insensitive). Returns None if absent, blank, or invalid.
        """
        if req is None:
            return None
        s = str(req).strip().lower()
        if not s:
            return None
        if s in ("male", "lord"):
            return "male"
        if s in ("female", "lady"):
            return "female"
        return None

    def event_passes_player_gender_requirement(event_or_story):
        """True if object has no player_gender_requirement or it matches current manager gender."""
        raw = None
        if event_or_story is not None and hasattr(event_or_story, "get"):
            raw = event_or_story.get("player_gender_requirement", None)
        if raw is None:
            return True
        canon = normalize_player_gender_requirement(raw)
        if canon is None:
            renpy.log(f"Invalid player_gender_requirement: {raw!r} (use male, female, lord, or lady)")
            return False
        return canon == get_player_manager_gender()

    store.get_player_manager_gender = get_player_manager_gender
    store.normalize_player_gender_requirement = normalize_player_gender_requirement
    store.event_passes_player_gender_requirement = event_passes_player_gender_requirement

    def load_events_from_folder(folder_name="data/events", subfolder=None, exclude_prefix=None):
        all_events = []
        files = []

        # Determine the path we're looking for
        if subfolder:
            expected_path = folder_name + "/" + subfolder
            _event_filter_log(f"Looking for events in subfolder: {expected_path}")
        else:
            expected_path = folder_name
            _event_filter_log(f"Looking for events in main folder: {expected_path}")

        # Find all matching JSON files
        _gcfl = getattr(store, "get_cached_file_list", None)
        _all_files = _gcfl() if callable(_gcfl) else renpy.list_files()
        for file in _all_files:
            if file.startswith(expected_path) and file.endswith(".json"):
                # If no subfolder, only include files directly in the folder, not in subfolders
                if not subfolder and "/" in file[len(expected_path)+1:]:
                    continue
                files.append(file)

        _event_filter_log(f"Found {len(files)} event files to load: {files}")

        # Load all files found
        for file in files:
            try:
                _event_filter_log(f"Loading events from file: {file}")
                with renpy.file(file) as f:
                    events_in_file = json.load(f)
                _event_filter_log(f"Loaded {len(events_in_file)} potential events from {file}")

                # Check each event before adding
                for index, event in enumerate(events_in_file):
                    # --->>> ADD LOGGING HERE <<<---
                    event_id_check = event.get("id", "MISSING_ID")
                    event_desc_check = event.get("description", "MISSING_DESCRIPTION")
                    _event_filter_log(
                        f"  Checking event index {index} from {file}: id='{event_id_check}', desc_start='{str(event_desc_check)[:50]}...'"
                    )
                    # --->>> END LOGGING <<<---

                    # Original filtering logic
                    if not persistent.nsfw_enabled and content_object_is_restricted(event):
                        # renpy.log(f"Skipping NSFW event: {event.get('id')}") # Optional log
                        continue
                    if exclude_prefix and event.get("id", "").startswith(exclude_prefix):
                        # renpy.log(f"Skipping event with excluded prefix: {event.get('id')}") # Optional log
                        continue
                    # An authored max_occurrences implies a capped event. Authors kept
                    # shipping one-shots with "max_occurrences" but no "limited": true,
                    # which the occurrence-cap check requires — infer it. An explicit
                    # "limited": false still wins (e.g. binding_gem_lead_2).
                    if "max_occurrences" in event and "limited" not in event:
                        event["limited"] = True
                    event.setdefault("limited", False)
                    event.setdefault("max_occurrences", 1)
                    # Normalize unknown worker_selection values (e.g. "player" shipped in
                    # 10 building events): unknown modes broke choice resolution outright.
                    # "choose" preserves the evident intent (the player picks a worker).
                    _ws = event.get("worker_selection")
                    if _ws is not None and _ws not in ("none", "random", "choose"):
                        renpy.log(f"WARNING: event {event.get('id')} has unknown worker_selection '{_ws}'; treating as 'choose'.")
                        event["worker_selection"] = "choose"
                    event.setdefault("choices", [{"option": "Continue", "message": "Nothing significant happens."}])
                    all_events.append(event)
                    # renpy.log(f"Added event to pool: {event.get('id')} from {file}") # Optional log
            except Exception as e:
                renpy.log(f"Error loading or processing event file {file}: {str(e)}") # Log error during loading/processing
                print("Error loading or processing event file", file, e) # Print to console too

        _event_filter_log(f"Loaded total of {len(all_events)} events from all files")
        return all_events

    def select_possible_events(all_events, active_building_types=None):
        """
        Selects events that are possible based on building types, occurrence limits, required flags, excluded flags, and custom conditions.

        Args:
            all_events (list): List of event dictionaries from JSON.
            active_building_types (list, optional): List of active building type IDs.

        Returns:
            list: Filtered list of possible event dictionaries.
        """
        reconcile_shop_unlock_state()
        reconcile_cancelled_character_arc_timestamps(all_events)

        if active_building_types is None:
            active_building_types = [b["type"] for b in available_buildings.values() if b.get("type") is not None]

        # Log to ensure we have events to process
        _event_filter_log(f"select_possible_events starting with {len(all_events)} events and building types: {active_building_types}")

        # Handle case where there are no active building types
        if not active_building_types:
            renpy.log("WARNING: No active building types! This will filter out all events with building_type requirements.")

        possible_events = []
        current_total_days = calculate_total_days()
        
        for event in all_events:
            event_id = event.get("id")
            if not event_id:
                _event_filter_log(f"Skipping event with no ID: {event}")
                continue
            if not event_is_visible_for_content_filter(event, include_pending_building=False):
                _event_filter_log(f"Filtered out {event_id} by the active content filter")
                continue
            if not event_progress_is_satisfied(event, store.workers):
                _event_filter_log(f"Filtered out {event_id} because its subject has not met worker_progress")
                continue

            # Check if this event was passed and if it's time for it to reappear
            passed_flag = f"{event_id}_passed"
            pass_timestamp_flag = f"{event_id}_pass_timestamp"
            
            if passed_flag in store.event_flags and store.event_flags[passed_flag]:
                # Event was passed, check if enough time has passed for it to reappear
                if pass_timestamp_flag in store.event_flags:
                    pass_timestamp = store.event_flags[pass_timestamp_flag]
                    days_since_passed = current_total_days - pass_timestamp
                    
                    # Determine cooldown period based on event type
                    if "tier2_finale" in event_id or "tier3_finale" in event_id:
                        cooldown_after_pass = 15  # 15 days for final missions
                    elif "tier2_retry" in event_id:
                        cooldown_after_pass = 25  # 25 days for retry missions
                    elif "tier3_retry" in event_id:
                        cooldown_after_pass = 35  # 35 days for tier 3 retry
                    elif "tier3_start" in event_id:
                        cooldown_after_pass = 20  # 20 days for tier 3 start
                    else:
                        cooldown_after_pass = 10  # Default 10 days for other missions
                    
                    if days_since_passed < cooldown_after_pass:
                        _event_filter_log(f"Filtered out {event_id} because it was passed {days_since_passed} days ago, needs {cooldown_after_pass} days to reappear")
                        continue
                    else:
                        # Reset the passed flag so the event can appear again
                        _event_filter_log(f"Event {event_id} passed cooldown period after being passed ({days_since_passed} days), resetting passed flag")
                        store.event_flags[passed_flag] = False
                        if pass_timestamp_flag in store.event_flags:
                            del store.event_flags[pass_timestamp_flag]

            # Check occurrence limits
            max_occurrences = event.get("max_occurrences", float('inf'))  # Use float('inf') for no limit if missing
            current_occurrences = store.event_occurrences.get(event_id, 0)
            _event_filter_log(f"Checking {event_id}: limited={event.get('limited', False)}, occurrences={current_occurrences}, max={max_occurrences}")
            if event.get("limited", False) and current_occurrences >= max_occurrences:
                _event_filter_log(f"Filtered out {event_id} due to occurrence limit")
                continue

            # Check cooldown period (default 3 days)
            cooldown_days = event.get("cooldown_days", 3)  # Default 3-day cooldown for all events
            if hasattr(store, "event_last_occurred") and event_id in store.event_last_occurred:
                last_occurred_day = store.event_last_occurred[event_id]
                days_since_last = current_total_days - last_occurred_day
                
                if days_since_last < cooldown_days:
                    _event_filter_log(f"Filtered out {event_id} due to cooldown: last occurred {days_since_last} days ago, cooldown is {cooldown_days} days")
                    continue
                
                _event_filter_log(f"Event {event_id} cooldown passed: last occurred {days_since_last} days ago, cooldown is {cooldown_days} days")

            # Check building type requirements
            event_building_types = event.get("building_type", [])
            # If the event *has* building type requirements, at least one must match the active types
            if event_building_types and not any(bt in active_building_types for bt in event_building_types):
                _event_filter_log(f"Filtered out {event_id} due to building type mismatch. Event requires {event_building_types} but active buildings are {active_building_types}")
                continue

            # Worker / profession / skill gates for event availability (non-recruit pool).
            if event_uses_building_availability_gates(event):
                candidate_buildings = get_content_visible_event_buildings(event, available_buildings)

                requirements_met = False
                for _, candidate in candidate_buildings:
                    if building_matches_random_event_availability(candidate, event):
                        requirements_met = True
                        break

                if not requirements_met:
                    _event_filter_log(
                        f"Filtered out {event_id} by building availability gates "
                        f"(requires_assigned_worker={bool(event.get('requires_assigned_worker', False))}, "
                        f"required_building_worker_traits={event.get('required_building_worker_traits', []) or []}, "
                        f"required_active_professions={event.get('required_active_professions', []) or []}, "
                        f"forbidden_active_professions={event.get('forbidden_active_professions', []) or []}, "
                        f"required_building_worker_min_skill={_coerce_event_min_skill(event)})"
                    )
                    continue

            # Player / manager gender filter (Lord/Lady; JSON may use male/female or lord/lady)
            if not event_passes_player_gender_requirement(event):
                _event_filter_log(
                    f"Filtered out {event_id} due to player gender: requires {event.get('player_gender_requirement')!r}, "
                    f"player is {get_player_manager_gender()}"
                )
                continue

            # Check for required flags - ALL must be met
            required_flags = event.get("required_flags", {})
            if required_flags:
                _event_filter_log(f"Event {event_id} has required flag requirements: {required_flags}")
                flag_conditions_met = True # Assume met initially
                for flag_name, required_value in required_flags.items():
                    current_value = store.event_flags.get(flag_name) # Use .get() for safety

                    # Check if flag exists AND matches required value
                    if flag_name not in store.event_flags:
                        # Flag doesn't exist
                        flag_conditions_met = False
                        _event_filter_log(f"Filtered out {event_id} because required flag '{flag_name}' is not set")
                        break # No need to check other required flags
                    elif required_value is not None and current_value != required_value:
                        # Flag exists but value doesn't match requirement (allow required_value==None to just check existence)
                        flag_conditions_met = False
                        _event_filter_log(f"Filtered out {event_id} because required flag '{flag_name}' has value {current_value}, but {required_value} is required")
                        break # No need to check other required flags

                # If any required flag condition was not met, skip this event
                if not flag_conditions_met:
                    continue

                _event_filter_log(f"Event {event_id} passed required flag check")
            else:
                _event_filter_log(f"Event {event_id} has no required flag requirements")


            # Check for excluded flags - if ANY exclusion condition is met, skip the event
            excluded_flags = event.get("excluded_flags", {})
            if excluded_flags:
                _event_filter_log(f"Event {event_id} has exclusion flag requirements: {excluded_flags}")
                exclusion_met = False # Assume exclusion is NOT met initially
                for flag_name, required_value_to_exclude in excluded_flags.items():
                    current_value = store.event_flags.get(flag_name) # Use .get() for safety

                    # Check if the flag exists AND its value matches the exclusion requirement
                    if flag_name in store.event_flags and current_value == required_value_to_exclude:
                        exclusion_met = True
                        _event_filter_log(f"Filtered out {event_id} because excluded flag '{flag_name}' is set to the required exclusion value '{required_value_to_exclude}' (current: {current_value})")
                        break # Found one exclusion match, no need to check others

                # If any exclusion condition was met, skip the event
                if exclusion_met:
                    continue

                _event_filter_log(f"Event {event_id} passed exclusion flag check")
            else:
                _event_filter_log(f"Event {event_id} has no exclusion flag requirements")


            # Evaluate custom conditions (start_when / stop_when)
            conditions = event.get("conditions", {})
            start_when = conditions.get("start_when", "True") # Default to True if not specified
            stop_when = conditions.get("stop_when", "False") # Default to False if not specified

            # Check if the event should start
            if not evaluate_condition(start_when):
                _event_filter_log(f"Filtered out {event_id} because start_when condition '{start_when}' is not met")
                continue

            # Check if the event should stop
            if evaluate_condition(stop_when):
                _event_filter_log(f"Filtered out {event_id} because stop_when condition '{stop_when}' is met")
                continue

            # If all checks passed, add the event to the list of possibilities
            possible_events.append(event)
            _event_filter_log(f"Event {event_id} passed all filters and is now a possible event")

        possible_events = limit_character_arc_candidates(possible_events)
        _event_filter_log(f"Selected {len(possible_events)} possible events: {[e['id'] for e in possible_events]}")

        # If no events passed the filter, log a warning
        if not possible_events:
            renpy.log("WARNING: No events passed the filtering process! Check building types, flags, and conditions.")

        return possible_events
