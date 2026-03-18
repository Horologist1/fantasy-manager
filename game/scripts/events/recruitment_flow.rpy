# Recruitment Event Flow - Using proper Ren'Py dialogue and choice system

label start_recruitment_system:
    # Load events and workers using Python
    # IMPORTANT: This label is entered via Jump from UI (not call_in_new_context).
    # So we must NOT use renpy.return_statement() for early exits (it can break flow).
    $ store._recruitment_abort = False
    $ store._recruitment_abort_message = ""
    python:
        try:
            recruitment_events = load_events_from_folder("data/events", subfolder="recruit")
            renpy.log(f"RECRUITMENT: Loaded {len(recruitment_events)} recruitment events")
            if not recruitment_events:
                renpy.log(f"RECRUITMENT DEBUG: 0 events - check if data/events/recruit/*.json exist and paths (Windows uses backslash)")
            
            recruit_candidates = load_recruit_workers()
            renpy.log(f"RECRUITMENT: Loaded {len(recruit_candidates)} recruit candidates: {[w.get('name', 'Unknown') for w in recruit_candidates]}")
            
            if not recruitment_events:
                store._recruitment_abort = True
                store._recruitment_abort_message = "No recruitment events found"
            elif not recruit_candidates:
                store._recruitment_abort = True
                store._recruitment_abort_message = "No workers available for recruitment"
            
            # Filter events: only include events where the specific worker is available (if event requires specific worker)
            available_events = []
            for event in recruitment_events:
                if event.get("random_worker", True):
                    # Random worker events are always available
                    available_events.append(event)
                else:
                    # Specific worker event - check if that worker is available
                    worker_name = event.get("worker_name")
                    if worker_name:
                        worker_available = any(w.get("name") == worker_name for w in recruit_candidates)
                        if worker_available:
                            available_events.append(event)
                            renpy.log(f"Event {event.get('id')} is available - worker {worker_name} found")
                        else:
                            renpy.log(f"Event {event.get('id')} filtered out - worker {worker_name} not available")
                    else:
                        # Event has random_worker=false but no worker_name - include it anyway
                        available_events.append(event)
            
            if not available_events:
                renpy.log("No recruitment events available (all specific workers unavailable)")
                store._recruitment_abort = True
                store._recruitment_abort_message = "No recruitment events available"
            
            # IMPORTANT: Prioritize in this order:
            # 1. Workers with specific events (highest priority)
            # 2. JSON-defined workers (unique/encounter_only) without specific events
            # 3. Procedural workers (lowest priority)
            workers_with_events = []
            json_defined_workers = []
            procedural_workers = []
            
            for worker in recruit_candidates:
                worker_name = worker.get("name", "")
                is_procedural = worker.get("procedural", False)
                has_specific_event = any(
                    not event.get("random_worker", True) 
                    and event.get("worker_name") == worker_name
                    for event in available_events
                )
                
                if has_specific_event:
                    workers_with_events.append(worker)
                elif is_procedural:
                    procedural_workers.append(worker)
                else:
                    # JSON-defined worker (unique or encounter_only) without specific event
                    json_defined_workers.append(worker)
            
            # Prioritize in order: specific events > JSON-defined > procedural
            if workers_with_events:
                selected_worker = random.choice(workers_with_events)
                renpy.log(f"Selected worker with specific event: {selected_worker.get('name')}")
            elif json_defined_workers:
                selected_worker = random.choice(json_defined_workers)
                renpy.log(f"Selected JSON-defined worker (no specific event): {selected_worker.get('name')}")
            else:
                selected_worker = random.choice(recruit_candidates)
                renpy.log(f"Selected procedural worker: {selected_worker.get('name')}")
            
            worker_name = selected_worker.get("name", "")
            
            # Check if there's a specific event for this worker
            specific_event = None
            for event in available_events:
                if not event.get("random_worker", True):
                    event_worker_name = event.get("worker_name")
                    if event_worker_name and event_worker_name == worker_name:
                        specific_event = event
                        renpy.log(f"Found specific event {event.get('id')} for worker {worker_name}")
                        break
            
            if specific_event:
                # Use the specific event for this worker
                selected_event = specific_event
            else:
                # No specific event - use a generic random worker event
                generic_events = [e for e in available_events if e.get("random_worker", True)]
                if not generic_events:
                    renpy.log("No generic recruitment events available")
                    store._recruitment_abort = True
                    store._recruitment_abort_message = "No recruitment events available"
                else:
                    # Select random generic event based on weight
                    total_weight = sum(event.get("weight", 1) for event in generic_events)
                    r = random.random() * total_weight
                    current_weight = 0
                    selected_event = generic_events[0]  # fallback
                    
                    for event in generic_events:
                        current_weight += event.get("weight", 1)
                        if r <= current_weight:
                            selected_event = event
                            break
                    
                    # Filter worker by gender requirement if specified
                    worker_gender_requirement = selected_event.get("worker_gender_requirement", None)
                    if worker_gender_requirement:
                        filtered_candidates = [w for w in recruit_candidates if w.get("gender", "") == worker_gender_requirement]
                        if filtered_candidates:
                            selected_worker = random.choice(filtered_candidates)
                        else:
                            renpy.log(f"No workers available matching gender requirement: {worker_gender_requirement}")
                            store._recruitment_abort = True
                            store._recruitment_abort_message = "No suitable workers available for this event"
            
            # Store globally (only when recruitment succeeded)
            if not store._recruitment_abort:
                store.current_recruitment_event = selected_event
                store.current_recruitment_worker = selected_worker
            
        except Exception as e:
            renpy.log(f"Error in start_recruitment_system: {e}")
            if not store._recruitment_abort:
                store._recruitment_abort = True
                store._recruitment_abort_message = "Recruitment system error"
    
    # If recruitment setup failed, notify and return safely to tavern.
    if getattr(store, "_recruitment_abort", False):
        $ renpy.log(f"RECRUITMENT: aborting start_recruitment_system: {getattr(store, '_recruitment_abort_message', '')}")
        $ renpy.notify(getattr(store, "_recruitment_abort_message", "Recruitment error"))
        $ store.in_recruitment = False
        jump tavern_screen
    
    # Mark recruitment context active
    $ store.in_recruitment = True

    # Check if it's advanced or simple event
    if "choices" in selected_event and selected_event.get("choices"):
        call recruitment_event_flow(selected_event, selected_worker) from _call_recruitment_event_flow
    else:
        call recruitment_event_simple(selected_event, selected_worker) from _call_recruitment_event_simple
    # Clear recruitment context, consume the day's attempt, and return to tavern
    $ store.can_recruit_today = False
    $ store.in_recruitment = False
    jump tavern_screen

label recruitment_event_flow(event, worker):
    # Mark start of new conversation for history navigation
    $ start_new_conversation()
    
    # Set up the scene with background
    python:
        bg_image = event.get("background_image", "event_bg")
        # Ensure we have a valid background - default to event_bg if missing or invalid
        if not bg_image:
            bg_image = "event_bg"
        
        # Check if it's a Ren'Py defined variable (like tavern_bg) or a file path
        if bg_image and not bg_image.startswith("images/"):
            # Try to get the variable from store first (for defined backgrounds like tavern_bg)
            if hasattr(store, bg_image):
                current_bg = getattr(store, bg_image)
            else:
                # If not a variable, treat as filename and convert to full path
                current_bg = f"images/{bg_image}.png"
        else:
            current_bg = bg_image
        
        # Fallback to event_bg if the image doesn't exist
        if not renpy.loadable(current_bg):
            renpy.log(f"Background image {current_bg} not found, using event_bg")
            current_bg = store.event_bg if hasattr(store, "event_bg") else "images/event_bg.png"
    scene expression current_bg with dissolve
    show expression Solid("#00000080")  # Semi-transparent black overlay
    
    # Calculate cost (uses current difficulty multiplier)
    python:
        comfort_level = get_effective_comfort_desired(worker)
        daily_cost = comfort_level * get_difficulty_comfort_mult()
        worker["daily_cost"] = daily_cost
        
        # Replace placeholders in description and dialogue
        worker_name = worker.get("name", "Unknown")
        description = event["description"].replace("[event_worker]", worker_name)
        dialogue_text = event.get("dialogue", "").replace("[event_worker]", worker_name)
        description = description.replace("[COST]", f"${daily_cost}")
        dialogue_text = dialogue_text.replace("[COST]", f"${daily_cost}")
        
        # Prepare choices with cost replacement
        choices = event.get("choices", [])
        processed_choices = []
        for choice in choices:
            choice_text = choice.get("option", "Choice")
            choice_text = choice_text.replace("[COST]", f"${daily_cost}")
            choice_copy = choice.copy()
            choice_copy["option"] = choice_text
            processed_choices.append(choice_copy)
        
        # Split description into sentences/phrases
        import re
        description_sentences = []
        if description:
            # Split by sentence endings (periods, exclamation marks, question marks)
            # Keep the punctuation with the sentence
            sentences = re.split(r'(?<=[.!?])\s+', description)
            for sentence in sentences:
                sentence = sentence.strip()
                # Also split by double newlines if they exist
                if '\n\n' in sentence:
                    parts = sentence.split('\n\n')
                    for part in parts:
                        part = part.strip()
                        if part:
                            description_sentences.append(part)
                elif sentence:
                    description_sentences.append(sentence)
        
        # Split dialogue into sentences/phrases
        dialogue_sentences = []
        if dialogue_text:
            # First split by double newlines (paragraph breaks)
            paragraphs = dialogue_text.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Remove quotes if they wrap the entire paragraph
                    if para.startswith('"') and para.endswith('"'):
                        para = para[1:-1]
                    # Split by sentence endings (keep punctuation)
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if sentence:
                            dialogue_sentences.append(sentence)
    
    # Show the description sentences one by one
    window show
    if description_sentences:
        python:
            for sentence in description_sentences:
                renpy.say(None, sentence)
    
    # Show the worker dialogue sentences one by one with speaker name
    if dialogue_sentences:
        python:
            # Create a temporary character for the worker
            worker_char = renpy.character.Character(worker_name, color="#ffdd88", what_italic=True)
            for sentence in dialogue_sentences:
                renpy.say(worker_char, sentence)
    
    # Hide window before showing choices
    window hide
    
    # Loop to handle returning from worker details
    label recruitment_choice_loop:
        # Show choices using the same system as regular events (like random_event_choice)
        call screen recruitment_choice_screen(event_choices=processed_choices)
        $ chosen_choice_data = _return
        
        # Check if no choice was made (from examining worker details)
        if chosen_choice_data is None:
            # User returned from worker details - go back to choices
            jump recruitment_choice_loop
    
    # Process the choice
    python:
        outcome_details = process_recruitment_choice(chosen_choice_data, event, worker)
        outcome_message = outcome_details.get("message", "Something happened.")
        outcome_type = outcome_details.get("outcome", "default")
    
    # Show the outcome using unified screen (like interactions)
    call screen recruitment_outcome(message=outcome_message, event=event, outcome=outcome_type)
    
    return

# Simple recruitment flow for legacy events
label recruitment_event_simple(event, worker):
    # Mark start of new conversation for history navigation
    $ start_new_conversation()
    
    python:
        bg_image = event.get("background_image", "event_bg")
        # Ensure we have a valid background - default to event_bg if missing or invalid
        if not bg_image:
            bg_image = "event_bg"
        
        # Check if it's a Ren'Py defined variable (like tavern_bg) or a file path
        if bg_image and not bg_image.startswith("images/"):
            # Try to get the variable from store first (for defined backgrounds like tavern_bg)
            if hasattr(store, bg_image):
                current_bg = getattr(store, bg_image)
            else:
                # If not a variable, treat as filename and convert to full path
                current_bg = f"images/{bg_image}.png"
        else:
            current_bg = bg_image
        
        # Fallback to event_bg if the image doesn't exist
        if not renpy.loadable(current_bg):
            renpy.log(f"Background image {current_bg} not found, using event_bg")
            current_bg = store.event_bg if hasattr(store, "event_bg") else "images/event_bg.png"
    scene expression current_bg with dissolve
    show expression Solid("#00000080")  # Semi-transparent black overlay
    
    python:
        comfort_level = get_effective_comfort_desired(worker)
        daily_cost = comfort_level * get_difficulty_comfort_mult()
        worker["daily_cost"] = daily_cost
        worker["comfort_level"] = comfort_level
        worker_name = worker.get("name", "Unknown")
        description = event["description"].replace("[event_worker]", worker_name)
        description = description.replace("[COST]", f"${daily_cost}")
    
    window show
    narrator "[description]"
    window hide
    
    call screen recruitment_event_screen(event=event, worker=worker)
    $ choice = _return
    
    if choice == "recruit":
        python:
            # Add worker to the game using recruit_worker for proper tutorial tracking
            if worker not in store.workers:
                recruit_worker(worker)
                outcome_msg = f"You successfully recruited {worker_name} for ${daily_cost} per day."
            else:
                outcome_msg = f"{worker_name} is already working for you."
    elif choice == "examine":
        $ outcome_msg = f"You examine {worker_name} carefully. They seem capable."
    else:
        $ outcome_msg = "You politely decline their offer."
    
    # Show outcome using unified screen (like interactions)
    # Use a dummy event structure for simple recruitment
    python:
        dummy_event = {
            "background_image": event.get("background_image", "event_bg"),
            "success_image": event.get("success_image", None),
            "failure_image": event.get("failure_image", None)
        }
        # Determine outcome type (default to success for simple recruitment)
        outcome_type = "success" if choice == "recruit" else "default"
    
    call screen recruitment_outcome(message=outcome_msg, event=dummy_event, outcome=outcome_type)
    
    return
