# Define helper function in store namespace to avoid pickling errors
init python:
    def _split_for_narrator(msg: str, limit: int = 220):
        """
        Split a message into chunks for narrator display, respecting sentence boundaries.
        Falls back to word splitting if sentences are too long.
        """
        try:
            import re
            # First attempt: split by sentence boundaries
            sentences = re.split(r'(?<=[\.!?])\s+', msg)
            chunks, current = [], ""
            for s in sentences:
                if len(current) + len(s) + 1 <= limit:
                    current = (current + " " + s).strip()
                else:
                    if current:
                        chunks.append(current)
                    # If a single sentence is too long, fall back to word split
                    if len(s) > limit:
                        words = s.split()
                        buf = ""
                        for w in words:
                            if len(buf) + len(w) + 1 <= limit:
                                buf = (buf + " " + w).strip()
                            else:
                                if buf:
                                    chunks.append(buf)
                                buf = w
                        if buf:
                            chunks.append(buf)
                        current = ""
                    else:
                        current = s
            if current:
                chunks.append(current)
            if not chunks:
                chunks = [msg]
            return chunks
        except Exception:
            return [msg]

label handle_random_event:
    # Mark start of new conversation for history navigation
    $ start_new_conversation()
    
    # Initial checks and setup (Ren'Py)
    if store.current_event is None:
        $ renpy.log("No event to handle, skipping to next_day")
        jump next_day

    # Get event data (Ren'Py $)
    $ event = store.current_event
    $ worker_selection_mode = event.get("worker_selection", "none")
    $ final_worker = store.current_worker # Initial worker (may be None)
    $ event_status = "start" # Control flag for logic flow
    $ worker_needed = False # Flag if the chosen action requires a worker
    $ outcome_message = ""
    $ eligible_workers = []
    $ store.event_worker_name = "" # Reset the event worker name for new events

    # Start event music based on event data
    $ start_event_with_music(event)

    # Prepare initial description (Python)
    python:
        initial_desc = event["description"]
        initial_desc = initial_desc.replace("[player_title]", str(player_title))
        initial_desc = initial_desc.replace("[player_name]", str(player_name))
        
        # First, select a specific building if needed for this event
        building_notification = None
        if "building_type" in event and event.get("building_type"):
            event_building_types = event.get("building_type", [])
            eligible_buildings = [
                (b_name, b) for b_name, b in available_buildings.items()
                if b.get("type") in event_building_types and b.get("owned", False)
            ]
            if eligible_buildings:
                # Select a specific building and store its name
                affected_building_name, affected_building = random.choice(eligible_buildings)
                store.current_affected_building = affected_building_name
                
                # Format building info for display
                btype_id = affected_building.get("type")
                if btype_id:
                    building_type = next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "")
                    display_name = store.custom_names.get(affected_building_name, affected_building_name)
                    affected_building_info = f"{building_type}: {display_name}"
                    
                    # Create separate building notification
                    building_notification = f"Something happened in {affected_building_info}"
            else:
                store.current_affected_building = None
        else:
            store.current_affected_building = None
            
        # Replace worker placeholders
        if final_worker is not None:
            acting_worker_name = final_worker.get("name", "the worker")
            initial_desc = initial_desc.replace("[event_worker]", acting_worker_name)
            initial_desc = initial_desc.replace("[acting_worker]", acting_worker_name)
        else:
            initial_desc = initial_desc.replace("[event_worker]", "the worker")
            initial_desc = initial_desc.replace("[acting_worker]", "the worker")
        store.temp_narrator_text = initial_desc
        store.current_event_description = initial_desc # Keep for potential use in worker choice screens
        store.building_notification = building_notification

    # --- Start Event Scene ---
    $ current_bg = get_event_background(event) # Get initial background
    scene expression current_bg with dissolve
    
    # Check if event has no_dialogue flag or if there's actual dialogue content
    $ no_dialogue_flag = event.get("no_dialogue", False)
    $ has_dialogue = not no_dialogue_flag and bool(store.building_notification or (store.temp_narrator_text and store.temp_narrator_text.strip()))
    
    if has_dialogue:
        window show # Show the narrator window only if there's dialogue
        
        # Display building notification first if available
        if store.building_notification:
            narrator "[store.building_notification]"
        
        # Then display the event description (split into chunks to avoid overflow)
        if store.temp_narrator_text:
            python:
                for _chunk in _split_for_narrator(store.temp_narrator_text, limit=220):
                    renpy.say(narrator, _chunk)

    # Prepare choices (Python)
    python:
        prepared_choices = []
        for choice_option in event.get("choices", []):
            # Check for required flags at the choice level
            required_flags = choice_option.get("required_flags", {})
            if required_flags:
                all_flags_met = True
                for flag, value in required_flags.items():
                    if store.event_flags.get(flag) != value:
                        all_flags_met = False
                        break
                if not all_flags_met:
                    continue  # Skip this choice

            # Check for excluded flags at the choice level
            excluded_flags = choice_option.get("excluded_flags", {})
            if excluded_flags:
                excluded = False
                for flag, excl_value in excluded_flags.items():
                    if store.event_flags.get(flag) == excl_value:
                        excluded = True
                        break
                if excluded:
                    continue  # Skip this choice

            # Optional conditional start/stop at the choice level
            choice_conditions = choice_option.get("conditions", {})
            if choice_conditions:
                start_when = choice_conditions.get("start_when", "True")
                stop_when = choice_conditions.get("stop_when", "False")
                try:
                    if not evaluate_condition(start_when):
                        continue  # Not available yet
                    if evaluate_condition(stop_when):
                        continue  # Explicitly stopped
                except Exception as e:
                    renpy.log(f"Choice conditions evaluation error: {e}")
                    # Be safe: hide the option if evaluation failed
                    continue

            new_choice = choice_option.copy()
            # Preserve threshold if it exists
            if "threshold" in choice_option:
                new_choice["threshold"] = choice_option["threshold"]
            option_text = new_choice.get("option", "")
            option_text = option_text.replace("[player_title]", str(player_title))
            option_text = option_text.replace("[player_name]", str(player_name))
            
            # Replace worker placeholders with proper name if available, otherwise use generic terms
            if final_worker is not None:
                acting_worker_name = final_worker.get("name", "the worker")
                option_text = option_text.replace("[event_worker]", acting_worker_name)
                option_text = option_text.replace("[acting_worker]", acting_worker_name)
            else:
                option_text = option_text.replace("[event_worker]", "a worker")
                option_text = option_text.replace("[acting_worker]", "a worker")
            new_choice["option"] = option_text
            # Prepare success/failure messages with placeholders resolved; avoid empty messages
            ms = choice_option.get("message_success")
            mf = choice_option.get("message_failure")
            for key in ("message_success", "message_failure"):
                val = choice_option.get(key, None)
                if isinstance(val, str):
                    txt = val
                else:
                    txt = None
                if txt:
                    txt = txt.replace("[player_title]", str(player_title))
                    txt = txt.replace("[player_name]", str(player_name))
                    if final_worker is not None:
                        acting_worker_name = final_worker.get("name", "the worker")
                        txt = txt.replace("[event_worker]", acting_worker_name)
                        txt = txt.replace("[acting_worker]", acting_worker_name)
                    else:
                        txt = txt.replace("[event_worker]", "a worker")
                        txt = txt.replace("[acting_worker]", "a worker")
                new_choice[key] = txt
            new_choice["effect"] = choice_option.get("effect", {})
            new_choice["condition"] = choice_option.get("condition", None)
            prepared_choices.append(new_choice)
        store.temp_prepared_choices = prepared_choices

    # Hide window before showing choices
    window hide
    
    # Show choices screen (Ren'Py) - ONLY shows the choices now
    call screen random_event_choice(event_choices=store.temp_prepared_choices)
    $ chosen_choice_data = _return

    # --- Python block to evaluate the choice and determine next steps ---
    python:
        event_status = "evaluate_choice" 
        if "condition" in chosen_choice_data:
            condition = chosen_choice_data.get("condition")
            if condition != "building_skill" and condition is not None:
                worker_needed = True
                renpy.log(f"Worker needed for choice with condition: {condition}")

        if worker_needed:
            renpy.log(f"Choice requires a worker. Mode: {worker_selection_mode}, Initial worker: {final_worker}")
            if worker_selection_mode == "choose":
                event_building_types = event.get("building_type", [])
                temp_eligible = []
                
                # Get threshold from choice if specified, default to 0 (no threshold)
                threshold = int(chosen_choice_data.get("threshold", 0))
                condition_skill = chosen_choice_data.get("condition")
                
                # If we have a specific affected building, limit to workers from that building
                if hasattr(store, "current_affected_building") and store.current_affected_building:
                    affected_building = store.current_affected_building
                    for w in store.workers:
                        if w.get("assigned_building") == affected_building:
                            # Check threshold if specified
                            if threshold > 0 and condition_skill:
                                worker_skill = calculate_skill_with_traits(w, condition_skill)
                                if worker_skill >= threshold:
                                    temp_eligible.append(w)
                            else:
                                temp_eligible.append(w)
                    renpy.log(f"Limiting eligible workers to those in affected building: {affected_building}")
                # Otherwise, use the original building type filtering
                elif event_building_types:
                    for w in store.workers:
                        assigned_bldg = w.get("assigned_building", "Unassigned")
                        if assigned_bldg != "Unassigned" and assigned_bldg in available_buildings:
                            if available_buildings[assigned_bldg].get("type") in event_building_types:
                                # Check threshold if specified
                                if threshold > 0 and condition_skill:
                                    worker_skill = calculate_skill_with_traits(w, condition_skill)
                                    if worker_skill >= threshold:
                                        temp_eligible.append(w)
                                else:
                                    temp_eligible.append(w)
                else:
                    for w in store.workers:
                        # Check threshold if specified
                        if threshold > 0 and condition_skill:
                            worker_skill = calculate_skill_with_traits(w, condition_skill)
                            if worker_skill >= threshold:
                                temp_eligible.append(w)
                        else:
                            temp_eligible.append(w)
                
                if not temp_eligible:
                    renpy.log("No eligible workers for choice, cannot proceed.")
                    final_worker = None
                    store.current_worker = None
                    event_status = "no_worker_available"
                else:
                    renpy.log("Mode is 'choose' and eligible workers found. Proceeding to worker selection screen.")
                    event_status = "needs_worker_choice"
                    store.temp_eligible_workers_for_event = temp_eligible
            elif worker_selection_mode == "random":
                if final_worker is None:
                    event_building_types = event.get("building_type", [])
                    temp_eligible = []
                    
                    # Get threshold from choice if specified, default to 0 (no threshold)
                    threshold = int(chosen_choice_data.get("threshold", 0))
                    condition_skill = chosen_choice_data.get("condition")
                    
                    # If we have a specific affected building, limit to workers from that building
                    if hasattr(store, "current_affected_building") and store.current_affected_building:
                        affected_building = store.current_affected_building
                        for w in store.workers:
                            if w.get("assigned_building") == affected_building:
                                # Check threshold if specified
                                if threshold > 0 and condition_skill:
                                    worker_skill = calculate_skill_with_traits(w, condition_skill)
                                    if worker_skill >= threshold:
                                        temp_eligible.append(w)
                                else:
                                    temp_eligible.append(w)
                        renpy.log(f"Limiting eligible workers to those in affected building: {affected_building}")
                    # Otherwise, use the original building type filtering
                    elif event_building_types:
                        for w in store.workers:
                            assigned_bldg = w.get("assigned_building", "Unassigned")
                            if assigned_bldg != "Unassigned" and assigned_bldg in available_buildings:
                                if available_buildings[assigned_bldg].get("type") in event_building_types:
                                    # Check threshold if specified
                                    if threshold > 0 and condition_skill:
                                        worker_skill = calculate_skill_with_traits(w, condition_skill)
                                        if worker_skill >= threshold:
                                            temp_eligible.append(w)
                                    else:
                                        temp_eligible.append(w)
                    else:
                        for w in store.workers:
                            # Check threshold if specified
                            if threshold > 0 and condition_skill:
                                worker_skill = calculate_skill_with_traits(w, condition_skill)
                                if worker_skill >= threshold:
                                    temp_eligible.append(w)
                            else:
                                temp_eligible.append(w)
                    
                    if temp_eligible:
                        final_worker = random.choice(temp_eligible)
                        store.current_worker = final_worker
                        renpy.log(f"Random worker selected: {final_worker['name']}")
                        event_status = "proceed_with_action"
                    else:
                        renpy.log("Random worker selection mode, but no eligible workers found.")
                        store.current_worker = None
                        event_status = "no_suitable_worker"
                else:
                    renpy.log(f"Random worker selection mode using pre-selected worker: {final_worker['name']}")
                    event_status = "proceed_with_action"
            elif final_worker is None:
                renpy.log("Worker needed but none available/selected initially.")
                store.current_worker = None
                event_status = "no_suitable_worker"
            else:
                renpy.log(f"Worker needed, mode is {worker_selection_mode}, using pre-selected worker: {final_worker['name']}")
                event_status = "proceed_with_action"
        else:
            renpy.log("Worker not needed for this choice.")
            final_worker = None
            store.current_worker = None
            event_status = "proceed_with_action"

    # --- Ren'Py block to handle screen calls and process based on status ---
    if event_status == "needs_worker_choice":
        # Still show narrator window during worker choice
        call screen choose_event_worker_screen(eligible_workers=store.temp_eligible_workers_for_event)
        $ chosen_worker = _return
        if chosen_worker is None:
            $ renpy.log("Player cancelled worker selection.")
            $ final_worker = None
            $ event_status = "cancelled"
        else:
            $ renpy.log(f"Worker chosen from screen: {chosen_worker}, Type: {type(chosen_worker)}")
            if chosen_worker is not None and hasattr(chosen_worker, 'items'):
                $ final_worker = dict(chosen_worker.items())
                $ store.current_worker = final_worker
                $ renpy.log(f"Set final_worker from chosen_worker copy: {final_worker.get('name')}")
                $ event_status = "proceed_with_action"
                
                # Re-process the outcome message with the chosen worker's name
                python:
                    if final_worker:
                        acting_worker_name = final_worker.get("name", "the worker")
                        # Update the outcome message for when it's displayed later
                        store.temp_narrator_text = store.temp_narrator_text.replace("the worker", acting_worker_name)
                        store.temp_narrator_text = store.temp_narrator_text.replace("[event_worker]", acting_worker_name)
                        store.temp_narrator_text = store.temp_narrator_text.replace("[acting_worker]", acting_worker_name)
                        
            else:
                $ renpy.log(f"ERROR: chosen_worker from screen was not dict-like: {chosen_worker}, Type: {type(chosen_worker)}")
                $ final_worker = None
                $ store.current_worker = None
                $ event_status = "cancelled"

    if worker_needed and final_worker is None and event_status != "cancelled" and event_status != "no_worker_available":
        $ renpy.log(f"Worker required, but none selected/available after checks. Status: {event_status}")
        $ event_status = "error_no_worker"

    # --- Determine outcome and update background ---
    $ outcome_message = ""
    $ event_outcome_for_bg = "default" # Default outcome for background check
    if event_status == "proceed_with_action":
        $ outcome_details = process_choice(chosen_choice_data, event, final_worker) # Assume process_choice returns dict now
        $ outcome_message = outcome_details.get("message", "An unknown outcome occurred.")
        $ event_outcome_for_bg = outcome_details.get("outcome", "default") # Get success/failure status
        $ renpy.log(f"Event outcome for background: {event_outcome_for_bg}")
    elif event_status == "no_worker_available":
        $ outcome_message = "No eligible workers were found for this task."
        $ event_outcome_for_bg = "failure"
    elif event_status == "cancelled":
        $ outcome_message = "You decided not to choose a worker. The event is cancelled."
    elif event_status == "no_suitable_worker":
        $ outcome_message = "No suitable worker was available for this task."
        $ event_outcome_for_bg = "failure"
    elif event_status == "error_no_worker":
        $ outcome_message = "You can't find any other workers to recruit today."
        $ event_outcome_for_bg = "failure"

    # --- Update background based on outcome ---
    $ new_bg = get_event_background(event, event_outcome_for_bg)
    if new_bg != current_bg:
        scene expression new_bg with dissolve
        $ current_bg = new_bg # Update the current background variable

    # --- Show the final outcome message (split into chunks if long) ---
    python:
        _chunks = _split_for_narrator(outcome_message, limit=260)
    python:
        for _chunk in _chunks:
            renpy.say(narrator, _chunk)
    # Final transition note so the user knows there's one more continue
    narrator "On to other matters."

    # --- Clean up and finish ---
    window hide # Hide the narrator window
    
    # Restore main BGM after event with quick fade-out for daily report transition
    $ end_event_with_quick_fadeout()
    
    # NOTE: Daily report will be shown by process_next_day() after this returns
    # Removed duplicate call screen daily_report to prevent double display
    return # Exit the label cleanly

label tavern:
    jump tavern_screen

label tavern_after_event:
    # Ensure workers are updated and jump to tavern
    $ update_displayed_workers()
    $ renpy.log("Jumped to tavern_after_event, updated workers, now showing tavern")
    jump tavern_screen