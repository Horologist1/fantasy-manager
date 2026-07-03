# Define helper functions in store namespace to avoid pickling errors
init python:
    def _worker_meets_trait_requirements(worker_obj, required_traits_list, excluded_traits_list):
        """Check if worker has all required traits and none of the excluded traits. Must be in store for pickling."""
        if not worker_obj:
            return False
        worker_traits = set(worker_obj.get("traits", []) or [])
        if required_traits_list and not set(required_traits_list).issubset(worker_traits):
            return False
        if excluded_traits_list and any(t in worker_traits for t in excluded_traits_list):
            return False
        return True

    def _any_eligible_worker_meets_traits(required_traits_list, excluded_traits_list, event=None):
        """Check if any eligible worker satisfies trait requirements. Must be in store for pickling."""
        event = event or getattr(store, "current_event", None)
        if not event:
            return False
        event_building_types = event.get("building_type", [])
        available_buildings = getattr(store, "available_buildings", {})
        workers = getattr(store, "workers", []) or []
        if hasattr(store, "current_affected_building") and store.current_affected_building:
            affected_building = store.current_affected_building
            candidates = [w for w in workers if w.get("assigned_building") == affected_building]
        elif event_building_types:
            candidates = []
            for w in workers:
                assigned_bldg = w.get("assigned_building", "Unassigned")
                if assigned_bldg != "Unassigned" and assigned_bldg in available_buildings:
                    if available_buildings[assigned_bldg].get("type") in event_building_types:
                        candidates.append(w)
        else:
            candidates = list(workers)

        for candidate in candidates:
            if _worker_meets_trait_requirements(candidate, required_traits_list, excluded_traits_list):
                return True
        return False

    def _parse_event_worker_name_list(event):
        """Parse event['worker_name'] into a flat list of name strings.

        Handles all formats found in JSON: a single string, a list of strings,
        or a nested list (e.g. [["Aspen", "Violet"]]).  Uses duck-typing per
        LA_BIBLIA (no isinstance checks on Ren'Py runtime data).
        """
        raw = event.get("worker_name") if event else None
        if not raw:
            return []
        names = []
        if hasattr(raw, "strip"):
            _name = str(raw).strip()
            if _name:
                names.append(_name)
        elif hasattr(raw, "__iter__"):
            for entry in list(raw):
                if not entry:
                    continue
                if hasattr(entry, "strip"):
                    _name = str(entry).strip()
                    if _name:
                        names.append(_name)
                elif hasattr(entry, "__iter__"):
                    for nested in list(entry):
                        if not nested:
                            continue
                        _name = str(nested).strip()
                        if _name:
                            names.append(_name)
                else:
                    _name = str(entry).strip()
                    if _name:
                        names.append(_name)
        else:
            _name = str(raw).strip()
            if _name:
                names.append(_name)
        return names

    def _parse_identity_string_list(raw):
        """Parse a string / list / nested-list field into a flat list of trimmed strings.

        Duck-typed per LA_BIBLIA. Used for worker_name and specific_worker_images
        on events, and specific_workers / specific_worker_images on interactions.
        """
        if not raw:
            return []
        names = []
        if hasattr(raw, "strip"):
            _name = str(raw).strip()
            if _name:
                names.append(_name)
        elif hasattr(raw, "__iter__"):
            for entry in list(raw):
                if not entry:
                    continue
                if hasattr(entry, "strip"):
                    _name = str(entry).strip()
                    if _name:
                        names.append(_name)
                elif hasattr(entry, "__iter__"):
                    for nested in list(entry):
                        if not nested:
                            continue
                        _name = str(nested).strip()
                        if _name:
                            names.append(_name)
                else:
                    _name = str(entry).strip()
                    if _name:
                        names.append(_name)
        else:
            _name = str(raw).strip()
            if _name:
                names.append(_name)
        return names

    def _parse_event_worker_images_list(event):
        """Parse event['specific_worker_images'] into a flat list of folder strings."""
        raw = event.get("specific_worker_images") if event else None
        return _parse_identity_string_list(raw)

    def _worker_matches_identity_filters(worker, name_list, folder_list):
        """Return True if worker passes identity filters.

        Semantics (retro-compatible):
          - Both filters empty -> True (no restriction).
          - Only names -> worker.name must be in names.
          - Only folders -> worker.folder must be in folders.
          - Both -> OR (name match OR folder match).
        Name matching is case-insensitive to match existing interaction behavior
        (see filter_interactions_by_worker_name); folder matching is exact since
        folder strings are canonical identifiers written by pack authors.
        """
        if not name_list and not folder_list:
            return True
        if not worker:
            return False
        if name_list:
            w_name = worker.get("name", "") if hasattr(worker, "get") else ""
            if w_name and w_name.lower() in [str(n).lower() for n in name_list]:
                return True
        if folder_list:
            w_folder = worker.get("folder", "") if hasattr(worker, "get") else ""
            if w_folder and w_folder in folder_list:
                return True
        return False

    def _worker_matches_event_identity(worker, event):
        """Convenience: OR filter for events using worker_name + specific_worker_images."""
        name_list = _parse_event_worker_name_list(event)
        folder_list = _parse_event_worker_images_list(event)
        return _worker_matches_identity_filters(worker, name_list, folder_list)

    def _event_has_identity_filters(event):
        """True if the event restricts by worker_name or specific_worker_images."""
        return bool(_parse_event_worker_name_list(event)) or bool(_parse_event_worker_images_list(event))

    store._worker_meets_trait_requirements = _worker_meets_trait_requirements
    store._any_eligible_worker_meets_traits = _any_eligible_worker_meets_traits
    store._parse_event_worker_name_list = _parse_event_worker_name_list
    store._parse_event_worker_images_list = _parse_event_worker_images_list
    store._parse_identity_string_list = _parse_identity_string_list
    store._worker_matches_identity_filters = _worker_matches_identity_filters
    store._worker_matches_event_identity = _worker_matches_event_identity
    store._event_has_identity_filters = _event_has_identity_filters

    def clear_random_event_context(reason=""):
        """Reset per-event transient state to prevent stale UI/event filters."""
        try:
            store.current_affected_building = None
        except Exception:
            pass
        try:
            store.current_worker = None
        except Exception:
            pass
        try:
            store.temp_eligible_workers_for_event = []
        except Exception:
            pass
        try:
            store.building_notification = None
        except Exception:
            pass
        try:
            store.chosen_choice_data = None
        except Exception:
            pass
        if reason:
            renpy.log(f"EVENT_CONTEXT: cleared ({reason})")

    store.clear_random_event_context = clear_random_event_context

    def _split_for_narrator(msg: str, limit: int = 180):
        """
        Split a message into chunks for narrator display, respecting sentence boundaries.
        Falls back to splitting by natural pauses (commas/semicolons/colons), then by words.
        """
        try:
            import re

            msg = str(msg or "")
            if not msg or len(msg) <= limit:
                return [msg]

            chunks = []
            current = ""

            # 1) Sentence split first
            sentences = re.split(r'(?<=[\.!?])\s+', msg)

            def flush(buf):
                if buf:
                    chunks.append(buf.strip())

            def split_by_words(text):
                words = text.split()
                buf = ""
                for w in words:
                    if buf and (len(buf) + len(w) + 1) > limit:
                        flush(buf)
                        buf = w
                    else:
                        buf = (buf + " " + w).strip()
                flush(buf)

            for s in sentences:
                s = s.strip()
                if not s:
                    continue

                # If sentence fits in current chunk, add it
                if current and (len(current) + len(s) + 1) <= limit:
                    current = (current + " " + s).strip()
                    continue

                # Otherwise, flush current and handle s
                flush(current)
                current = ""

                if len(s) <= limit:
                    current = s
                    continue

                # 2) Split long sentence by natural pauses
                parts = re.split(r'(?<=[,;:])\s+', s)
                part_buf = ""
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue

                    if part_buf and (len(part_buf) + len(p) + 1) <= limit:
                        part_buf = (part_buf + " " + p).strip()
                        continue

                    flush(part_buf)
                    part_buf = ""

                    if len(p) <= limit:
                        part_buf = p
                    else:
                        # 3) Split too-long part by words
                        split_by_words(p)

                flush(part_buf)

            flush(current)

            if not chunks:
                return [msg]
            return chunks
        except Exception:
            return [str(msg or "")]

# Ensure store has current_event so handle_random_event never raises AttributeError
default current_event = None

label _random_event_show_bg(media):
    # Same idea as interaction image layers in screens.rpy (fit "contain" + 1920×1080 stage):
    # avoids cropping/"zoom" when art is not exactly the game's aspect ratio.
    scene black
    if media and isinstance(media, str) and media.lower().endswith((".webm", ".mp4")):
        show expression Movie(play=media, size=(1920, 1080), loop=True) zorder 0 as random_event_bg:
            xalign 0.5
            yalign 0.5
    elif media:
        show expression Image(media) zorder 0 as random_event_bg:
            xalign 0.5
            yalign 0.5
            fit "contain"
            xysize (1920, 1080)
    else:
        show expression Solid("#000000") zorder 0 as random_event_bg
    with dissolve
    return

label handle_random_event:
    # Mark start of new conversation for history navigation
    $ start_new_conversation()
    
    # Initial checks and setup (Ren'Py)
    if store.current_event is None:
        $ renpy.log("No current_event in handle_random_event; returning to caller without re-running next_day.")
        $ store.clear_random_event_context("no_current_event")
        return

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
            if eligible_buildings and store.event_uses_building_availability_gates(event):
                filtered = [
                    (b_name, b) for b_name, b in eligible_buildings
                    if store.building_matches_random_event_availability(b, event)
                ]
                if filtered:
                    eligible_buildings = filtered
                else:
                    renpy.log("handle_random_event: no building passed availability gates for event %r; clearing affected building." % event.get("id"))
                    eligible_buildings = []
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
    # Initial event scene may use worker-specific media when a worker is already preselected.
    $ current_bg = get_event_background(event, worker=final_worker)
    call _random_event_show_bg(current_bg) from _call__random_event_show_bg
    
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
                for _chunk in _split_for_narrator(store.temp_narrator_text, limit=180):
                    renpy.say(narrator, _chunk)

    # Prepare choices (Python) - use store functions to avoid pickle errors
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

            # Trait gating at choice level.
            required_traits = list(choice_option.get("required_traits", []) or [])
            rt_one = choice_option.get("required_trait")
            if rt_one:
                required_traits.append(rt_one)
            excluded_traits = choice_option.get("excluded_traits", []) or []
            trait_visibility = choice_option.get("trait_visibility", "hide") or "hide"  # hide|blocked
            blocked_reason = choice_option.get("blocked_message") or "Locked: trait requirement not met."

            trait_requirements_met = True
            if required_traits or excluded_traits:
                if final_worker is not None:
                    trait_requirements_met = store._worker_meets_trait_requirements(final_worker, required_traits, excluded_traits)
                elif worker_selection_mode in ("choose", "random"):
                    # If no selected worker yet, check if at least one eligible worker can satisfy.
                    trait_requirements_met = store._any_eligible_worker_meets_traits(required_traits, excluded_traits, event)
                else:
                    # Non-worker choice cannot satisfy worker trait requirements.
                    trait_requirements_met = False

            if not trait_requirements_met and trait_visibility == "hide":
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
            condition_for_preview = choice_option.get("condition", None)
            check_preview = ""
            if condition_for_preview == "building_skill" and hasattr(store, "current_affected_building") and store.current_affected_building:
                preview_building = available_buildings.get(store.current_affected_building)
                preview_info = get_event_building_skill_check_info(preview_building)
                check_preview = preview_info.get("label", "") if preview_info.get("valid") else ""
            elif final_worker is not None and condition_for_preview and condition_for_preview != "building_skill":
                preview_info = get_event_worker_skill_check_info(final_worker, choice_option)
                check_preview = preview_info.get("label", "") if preview_info.get("valid") else ""
            if check_preview and check_preview not in option_text:
                # Parentheses (not brackets) so Ren'Py never tries to interpolate
                # the preview text — keeps modded events safe from accidental
                # SyntaxErrors regardless of what the label contains.
                option_text = option_text + " (" + check_preview + ")"
            new_choice["option"] = option_text
            # Prepare success/failure messages with placeholders resolved; avoid empty messages
            # When final_worker is None (e.g. worker_selection "choose" before pick), keep
            # [acting_worker]/[event_worker] as-is so process_choice can replace them after
            # the player selects a worker. Otherwise we'd show "a worker" instead of the name.
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
                    # else: leave [acting_worker]/[event_worker] for process_choice to fill
                new_choice[key] = txt
            new_choice["effect"] = choice_option.get("effect", {})
            new_choice["condition"] = choice_option.get("condition", None)
            new_choice["_blocked"] = (not trait_requirements_met and trait_visibility == "blocked")
            new_choice["_blocked_reason"] = blocked_reason
            # Skip choices with empty or whitespace-only option to avoid blank slots in the UI
            if not (option_text and str(option_text).strip()):
                continue
            prepared_choices.append(new_choice)
        store.temp_prepared_choices = prepared_choices

    # Hide window before showing choices
    window hide
    
    # Show choices screen (Ren'Py) - ONLY shows the choices now
    call screen random_event_choice(event_choices=store.temp_prepared_choices)
    $ chosen_choice_data = _return
    $ store.chosen_choice_data = chosen_choice_data

    if chosen_choice_data is None:
        $ outcome_message = "No valid option selected."
        narrator "[outcome_message]"
        window hide
        # Declined events reappear after a cooldown: select_possible_events reads
        # {id}_passed / {id}_pass_timestamp (that logic was dead until now because
        # nothing ever set the flags).
        python:
            _declined_id = event.get("id") if event and hasattr(event, "get") else None
            if _declined_id:
                store.event_flags[f"{_declined_id}_passed"] = True
                store.event_flags[f"{_declined_id}_pass_timestamp"] = calculate_total_days()
                renpy.log(f"Event {_declined_id} declined; will reappear after its pass cooldown.")
        $ store.clear_random_event_context("no_choice_selected")
        return

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
                                worker_skill = get_event_worker_skill_check_info(w, chosen_choice_data).get("roll_skill", 0)
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
                                    worker_skill = get_event_worker_skill_check_info(w, chosen_choice_data).get("roll_skill", 0)
                                    if worker_skill >= threshold:
                                        temp_eligible.append(w)
                                else:
                                    temp_eligible.append(w)
                else:
                    for w in store.workers:
                        # Check threshold if specified
                        if threshold > 0 and condition_skill:
                            worker_skill = get_event_worker_skill_check_info(w, chosen_choice_data).get("roll_skill", 0)
                            if worker_skill >= threshold:
                                temp_eligible.append(w)
                        else:
                            temp_eligible.append(w)
                
                req_tr = list(chosen_choice_data.get("required_traits", []) or [])
                if chosen_choice_data.get("required_trait"):
                    req_tr.append(chosen_choice_data.get("required_trait"))
                ex_tr = chosen_choice_data.get("excluded_traits", []) or []
                if req_tr or ex_tr:
                    temp_eligible = [
                        w for w in temp_eligible
                        if store._worker_meets_trait_requirements(w, req_tr, ex_tr)
                    ]

                # Filter by event worker_name and/or specific_worker_images (OR semantics)
                if store._event_has_identity_filters(event):
                    temp_eligible = [w for w in temp_eligible if store._worker_matches_event_identity(w, event)]

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
                                    worker_skill = get_event_worker_skill_check_info(w, chosen_choice_data).get("roll_skill", 0)
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
                                        worker_skill = get_event_worker_skill_check_info(w, chosen_choice_data).get("roll_skill", 0)
                                        if worker_skill >= threshold:
                                            temp_eligible.append(w)
                                    else:
                                        temp_eligible.append(w)
                    else:
                        for w in store.workers:
                            # Check threshold if specified
                            if threshold > 0 and condition_skill:
                                worker_skill = get_event_worker_skill_check_info(w, chosen_choice_data).get("roll_skill", 0)
                                if worker_skill >= threshold:
                                    temp_eligible.append(w)
                            else:
                                temp_eligible.append(w)
                    
                    req_tr = list(chosen_choice_data.get("required_traits", []) or [])
                    if chosen_choice_data.get("required_trait"):
                        req_tr.append(chosen_choice_data.get("required_trait"))
                    ex_tr = chosen_choice_data.get("excluded_traits", []) or []
                    if req_tr or ex_tr:
                        temp_eligible = [
                            w for w in temp_eligible
                            if store._worker_meets_trait_requirements(w, req_tr, ex_tr)
                        ]

                    # Filter by event worker_name and/or specific_worker_images (OR semantics)
                    if store._event_has_identity_filters(event):
                        temp_eligible = [w for w in temp_eligible if store._worker_matches_event_identity(w, event)]

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
                # Screen returns worker ref from store.workers; use it directly so trait/stat changes persist
                $ final_worker = chosen_worker
                $ store.current_worker = final_worker
                $ renpy.log(f"Set final_worker: {final_worker.get('name')} (in store.workers: {final_worker in store.workers})")
                $ event_status = "proceed_with_action"
                
                # Re-process the outcome message with the chosen worker's name
                python:
                    if final_worker:
                        import re as _re
                        acting_worker_name = final_worker.get("name", "the worker")
                        # Update the outcome message for when it's displayed later.
                        # Word-boundary replace: a blanket .replace() also mangled
                        # "the workers" into e.g. "Aeliss".
                        store.temp_narrator_text = _re.sub(r"\bthe worker\b", acting_worker_name, store.temp_narrator_text)
                        store.temp_narrator_text = store.temp_narrator_text.replace("[event_worker]", acting_worker_name)
                        store.temp_narrator_text = store.temp_narrator_text.replace("[acting_worker]", acting_worker_name)
                        
            else:
                $ renpy.log(f"ERROR: chosen_worker from screen was not dict-like: {chosen_worker}, Type: {type(chosen_worker)}")
                $ final_worker = None
                $ store.current_worker = None
                $ event_status = "cancelled"

    if worker_needed and final_worker is None and event_status not in ("cancelled", "no_worker_available", "no_suitable_worker"):
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
        $ outcome_message = "You look around, but none of your people have the skills this situation demands. The moment passes without resolution—an opportunity lost to a gap in your roster."
        $ event_outcome_for_bg = "failure"
    elif event_status == "cancelled":
        $ outcome_message = "You weigh the options and decide not to commit anyone. The situation resolves itself—for better or worse—without your intervention."
        # Cancelling worker selection counts as declining: schedule the reappear cooldown.
        python:
            _declined_id = event.get("id") if event and hasattr(event, "get") else None
            if _declined_id:
                store.event_flags[f"{_declined_id}_passed"] = True
                store.event_flags[f"{_declined_id}_pass_timestamp"] = calculate_total_days()
                renpy.log(f"Event {_declined_id} cancelled at worker selection; will reappear after its pass cooldown.")
    elif event_status == "no_suitable_worker":
        $ outcome_message = "You run through your roster in your head, but no one fits the bill. Without the right person for the job, all you can do is watch the opportunity slip by."
        $ event_outcome_for_bg = "failure"
    elif event_status == "error_no_worker":
        $ outcome_message = "The day's been long, and your people are stretched thin. There's no one left to send—you'll have to wait for tomorrow."
        $ event_outcome_for_bg = "failure"

    # --- Update background based on outcome ---
    # Pass choice condition as skill hint so worker-folder skill media can be used
    # when success/failure-specific event media is not present.
    $ skill_for_event_media = chosen_choice_data.get("condition") if chosen_choice_data else None
    # Quiet audio stinger for the resolved outcome
    python:
        if event_outcome_for_bg == "success":
            play_ui_sound("success")
        elif event_outcome_for_bg == "failure":
            play_ui_sound("failure")
    $ new_bg = get_event_background(event, event_outcome_for_bg, final_worker, skill_name=skill_for_event_media, choice=chosen_choice_data)
    if new_bg != current_bg:
        call _random_event_show_bg(new_bg) from _call__random_event_show_bg_1
        $ current_bg = new_bg # Update the current background variable

    # --- Show the final outcome message (split into chunks if long) ---
    python:
        _chunks = _split_for_narrator(outcome_message, limit=130)
    python:
        for _chunk in _chunks:
            renpy.say(narrator, _chunk)
    # --- Final image-only click (no message) ---
    window hide
    pause
    
    # Restore main BGM after event with quick fade-out for daily report transition
    $ end_event_with_quick_fadeout()
    
    # NOTE: Daily report will be shown by process_next_day() after this returns
    # Removed duplicate call screen daily_report to prevent double display
    $ store.clear_random_event_context("event_completed")
    return # Exit the label cleanly

label tavern:
    jump tavern_screen

label tavern_after_event:
    # Ensure workers are updated and jump to tavern
    $ update_displayed_workers()
    $ renpy.log("Jumped to tavern_after_event, updated workers, now showing tavern")
    jump tavern_screen