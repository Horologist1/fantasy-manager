# events_logic.rpy

init python:
    EVENT_FILTER_DEBUG = False

    def _event_filter_log(message, force=False):
        if force or EVENT_FILTER_DEBUG or getattr(config, "developer", False):
            renpy.log(message)

    def _normalize_event_profession_id(pid):
        if pid is None:
            return ""
        return str(pid).strip().lower()

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
                    if not persistent.nsfw_enabled and event.get("nsfw", False):
                        # renpy.log(f"Skipping NSFW event: {event.get('id')}") # Optional log
                        continue
                    if exclude_prefix and event.get("id", "").startswith(exclude_prefix):
                        # renpy.log(f"Skipping event with excluded prefix: {event.get('id')}") # Optional log
                        continue
                    event.setdefault("limited", False)
                    event.setdefault("max_occurrences", 1)
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
                candidate_buildings = []
                for b_name, b in available_buildings.items():
                    if not b.get("owned", False):
                        continue
                    b_type = b.get("type")
                    if event_building_types and b_type not in event_building_types:
                        continue
                    candidate_buildings.append((b_name, b))

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

        _event_filter_log(f"Selected {len(possible_events)} possible events: {[e['id'] for e in possible_events]}")

        # If no events passed the filter, log a warning
        if not possible_events:
            renpy.log("WARNING: No events passed the filtering process! Check building types, flags, and conditions.")

        return possible_events
