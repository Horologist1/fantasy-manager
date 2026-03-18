# events_logic.rpy

init python:

    def _building_matches_event_worker_requirements(building, required_worker_traits=None, require_worker=False):
        """Check if a building satisfies worker-presence/worker-trait event requirements."""
        assigned = building.get("assigned_servants", []) or []
        if require_worker and not assigned:
            return False
        if not required_worker_traits:
            return True
        req = set(required_worker_traits)
        for worker in assigned:
            worker_traits = set((worker or {}).get("traits", []) or [])
            if req.issubset(worker_traits):
                return True
        return False

    def _building_matches_event_building_traits(building, required_building_traits=None):
        """Check if a building has all required building traits/tags."""
        if not required_building_traits:
            return True
        building_traits = set((building or {}).get("traits", []) or [])
        return set(required_building_traits).issubset(building_traits)

    def load_events_from_folder(folder_name="data/events", subfolder=None, exclude_prefix=None):
        all_events = []
        files = []

        # Determine the path we're looking for
        if subfolder:
            expected_path = folder_name + "/" + subfolder
            renpy.log(f"Looking for events in subfolder: {expected_path}")
        else:
            expected_path = folder_name
            renpy.log(f"Looking for events in main folder: {expected_path}")

        # Find all matching JSON files
        for file in renpy.list_files():
            if file.startswith(expected_path) and file.endswith(".json"):
                # If no subfolder, only include files directly in the folder, not in subfolders
                if not subfolder and "/" in file[len(expected_path)+1:]:
                    continue
                files.append(file)

        renpy.log(f"Found {len(files)} event files to load: {files}")

        # Load all files found
        for file in files:
            try:
                renpy.log(f"Loading events from file: {file}")
                with renpy.file(file) as f:
                    events_in_file = json.load(f)
                renpy.log(f"Loaded {len(events_in_file)} potential events from {file}")

                # Check each event before adding
                for index, event in enumerate(events_in_file):
                    # --->>> ADD LOGGING HERE <<<---
                    event_id_check = event.get("id", "MISSING_ID")
                    event_desc_check = event.get("description", "MISSING_DESCRIPTION")
                    renpy.log(f"  Checking event index {index} from {file}: id='{event_id_check}', desc_start='{str(event_desc_check)[:50]}...'")
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
                print("Error loading/processing event file", file, e) # Print to console too

        renpy.log(f"Loaded total of {len(all_events)} events from all files")
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
        renpy.log(f"select_possible_events starting with {len(all_events)} events and building types: {active_building_types}")

        # Handle case where there are no active building types
        if not active_building_types:
            renpy.log("WARNING: No active building types! This will filter out all events with building_type requirements.")

        possible_events = []
        
        for event in all_events:
            event_id = event.get("id")
            if not event_id:
                renpy.log(f"Skipping event with no ID: {event}")
                continue

            # Check if this event was passed and if it's time for it to reappear
            passed_flag = f"{event_id}_passed"
            pass_timestamp_flag = f"{event_id}_pass_timestamp"
            
            if passed_flag in store.event_flags and store.event_flags[passed_flag]:
                # Event was passed, check if enough time has passed for it to reappear
                if pass_timestamp_flag in store.event_flags:
                    pass_timestamp = store.event_flags[pass_timestamp_flag]
                    current_total_days = calculate_total_days()
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
                        renpy.log(f"Filtered out {event_id} because it was passed {days_since_passed} days ago, needs {cooldown_after_pass} days to reappear")
                        continue
                    else:
                        # Reset the passed flag so the event can appear again
                        renpy.log(f"Event {event_id} passed cooldown period after being passed ({days_since_passed} days), resetting passed flag")
                        store.event_flags[passed_flag] = False
                        if pass_timestamp_flag in store.event_flags:
                            del store.event_flags[pass_timestamp_flag]

            # Check occurrence limits
            max_occurrences = event.get("max_occurrences", float('inf'))  # Use float('inf') for no limit if missing
            current_occurrences = store.event_occurrences.get(event_id, 0)
            renpy.log(f"Checking {event_id}: limited={event.get('limited', False)}, occurrences={current_occurrences}, max={max_occurrences}")
            if event.get("limited", False) and current_occurrences >= max_occurrences:
                renpy.log(f"Filtered out {event_id} due to occurrence limit")
                continue

            # Check cooldown period (default 3 days)
            cooldown_days = event.get("cooldown_days", 3)  # Default 3-day cooldown for all events
            if hasattr(store, "event_last_occurred") and event_id in store.event_last_occurred:
                last_occurred_day = store.event_last_occurred[event_id]
                
                # Calculate total days from start (Year 1, Month 0, Day 1) to current date
                current_total_days = calculate_total_days()
                days_since_last = current_total_days - last_occurred_day
                
                if days_since_last < cooldown_days:
                    renpy.log(f"Filtered out {event_id} due to cooldown: last occurred {days_since_last} days ago, cooldown is {cooldown_days} days")
                    continue
                
                renpy.log(f"Event {event_id} cooldown passed: last occurred {days_since_last} days ago, cooldown is {cooldown_days} days")

            # Check building type requirements
            event_building_types = event.get("building_type", [])
            # If the event *has* building type requirements, at least one must match the active types
            if event_building_types and not any(bt in active_building_types for bt in event_building_types):
                renpy.log(f"Filtered out {event_id} due to building type mismatch. Event requires {event_building_types} but active buildings are {active_building_types}")
                continue

            # New worker/building-trait gates for event availability.
            require_worker = bool(event.get("requires_assigned_worker", False))
            required_worker_traits = event.get("required_building_worker_traits", []) or []
            required_building_traits = event.get("required_building_traits", []) or []

            if require_worker or required_worker_traits or required_building_traits:
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
                    if not _building_matches_event_building_traits(candidate, required_building_traits):
                        continue
                    if not _building_matches_event_worker_requirements(
                        candidate,
                        required_worker_traits=required_worker_traits,
                        require_worker=require_worker,
                    ):
                        continue
                    requirements_met = True
                    break

                if not requirements_met:
                    renpy.log(
                        f"Filtered out {event_id} by worker/building trait requirements "
                        f"(requires_assigned_worker={require_worker}, "
                        f"required_building_worker_traits={required_worker_traits}, "
                        f"required_building_traits={required_building_traits})"
                    )
                    continue

            # Player gender filter
            player_gender = "male" if (store.player_title and store.player_title.lower().strip() == "lord") else "female"
            player_req = event.get("player_gender_requirement", None)
            if player_req is not None and player_req != player_gender:
                renpy.log(f"Filtered out {event_id} due to player gender: requires {player_req}, player is {player_gender}")
                continue

            # Check for required flags - ALL must be met
            required_flags = event.get("required_flags", {})
            if required_flags:
                renpy.log(f"Event {event_id} has required flag requirements: {required_flags}")
                flag_conditions_met = True # Assume met initially
                for flag_name, required_value in required_flags.items():
                    current_value = store.event_flags.get(flag_name) # Use .get() for safety

                    # Check if flag exists AND matches required value
                    if flag_name not in store.event_flags:
                        # Flag doesn't exist
                        flag_conditions_met = False
                        renpy.log(f"Filtered out {event_id} because required flag '{flag_name}' is not set")
                        break # No need to check other required flags
                    elif required_value is not None and current_value != required_value:
                        # Flag exists but value doesn't match requirement (allow required_value==None to just check existence)
                        flag_conditions_met = False
                        renpy.log(f"Filtered out {event_id} because required flag '{flag_name}' has value {current_value}, but {required_value} is required")
                        break # No need to check other required flags

                # If any required flag condition was not met, skip this event
                if not flag_conditions_met:
                    continue

                renpy.log(f"Event {event_id} passed required flag check")
            else:
                renpy.log(f"Event {event_id} has no required flag requirements")


            # Check for excluded flags - if ANY exclusion condition is met, skip the event
            excluded_flags = event.get("excluded_flags", {})
            if excluded_flags:
                renpy.log(f"Event {event_id} has exclusion flag requirements: {excluded_flags}")
                exclusion_met = False # Assume exclusion is NOT met initially
                for flag_name, required_value_to_exclude in excluded_flags.items():
                    current_value = store.event_flags.get(flag_name) # Use .get() for safety

                    # Check if the flag exists AND its value matches the exclusion requirement
                    if flag_name in store.event_flags and current_value == required_value_to_exclude:
                        exclusion_met = True
                        renpy.log(f"Filtered out {event_id} because excluded flag '{flag_name}' is set to the required exclusion value '{required_value_to_exclude}' (current: {current_value})")
                        break # Found one exclusion match, no need to check others

                # If any exclusion condition was met, skip the event
                if exclusion_met:
                    continue

                renpy.log(f"Event {event_id} passed exclusion flag check")
            else:
                renpy.log(f"Event {event_id} has no exclusion flag requirements")


            # Evaluate custom conditions (start_when / stop_when)
            conditions = event.get("conditions", {})
            start_when = conditions.get("start_when", "True") # Default to True if not specified
            stop_when = conditions.get("stop_when", "False") # Default to False if not specified

            # Check if the event should start
            if not evaluate_condition(start_when):
                renpy.log(f"Filtered out {event_id} because start_when condition '{start_when}' is not met")
                continue

            # Check if the event should stop
            if evaluate_condition(stop_when):
                renpy.log(f"Filtered out {event_id} because stop_when condition '{stop_when}' is met")
                continue

            # If all checks passed, add the event to the list of possibilities
            possible_events.append(event)
            renpy.log(f"Event {event_id} passed all filters and is now a possible event")

        renpy.log(f"Selected {len(possible_events)} possible events: {[e['id'] for e in possible_events]}")

        # If no events passed the filter, log a warning
        if not possible_events:
            renpy.log("WARNING: No events passed the filtering process! Check building types, flags, and conditions.")

        return possible_events