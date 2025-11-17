# Recruitment Event Flow - Using proper Ren'Py dialogue and choice system

label start_recruitment_system:
    # Load events and workers using Python
    python:
        try:
            recruitment_events = load_events_from_folder("data/events", subfolder="recruit")
            recruit_candidates = load_recruit_workers()
            
            if not recruitment_events or not recruit_candidates:
                renpy.show_screen("error_popup", message="No recruitment data found")
                renpy.return_statement()
            
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
                renpy.show_screen("error_popup", message="No recruitment events available")
                renpy.return_statement()
            
            # Select random event based on weight from available events
            total_weight = sum(event.get("weight", 1) for event in available_events)
            r = random.random() * total_weight
            current_weight = 0
            selected_event = available_events[0]  # fallback
            
            for event in available_events:
                current_weight += event.get("weight", 1)
                if r <= current_weight:
                    selected_event = event
                    break
            
            # Select worker based on event requirements
            if selected_event.get("random_worker", True):
                # Random worker - filter by gender requirement if specified
                worker_gender_requirement = selected_event.get("worker_gender_requirement", None)
                if worker_gender_requirement:
                    recruit_candidates = [w for w in recruit_candidates if w.get("gender", "") == worker_gender_requirement]
                    if not recruit_candidates:
                        renpy.log(f"No workers available matching gender requirement: {worker_gender_requirement}")
                        renpy.show_screen("error_popup", message="No suitable workers available for this event")
                        renpy.return_statement()
                selected_worker = random.choice(recruit_candidates)
            else:
                # Specific worker name - find the worker (we already verified it exists in the filter step)
                worker_name = selected_event.get("worker_name")
                selected_worker = next((w for w in recruit_candidates if w.get("name") == worker_name), None)
                
                if not selected_worker:
                    # This shouldn't happen if filtering worked correctly, but handle it anyway
                    renpy.log(f"Worker {worker_name} not found in recruit candidates (this should not happen)")
                    renpy.show_screen("error_popup", message=f"Worker {worker_name} is not available for recruitment")
                    renpy.return_statement()
            
            # Store globally
            store.current_recruitment_event = selected_event
            store.current_recruitment_worker = selected_worker
            
        except Exception as e:
            renpy.log(f"Error in start_recruitment_system: {e}")
            renpy.show_screen("error_popup", message="Recruitment system error")
            renpy.return_statement()
    
    # Mark recruitment context active
    $ store.in_recruitment = True

    # Check if it's advanced or simple event
    if "choices" in selected_event and selected_event.get("choices"):
        call recruitment_event_flow(selected_event, selected_worker) from _call_recruitment_event_flow
    else:
        call recruitment_event_simple(selected_event, selected_worker) from _call_recruitment_event_simple
    # Clear recruitment context and return to tavern
    $ store.in_recruitment = False
    jump tavern_screen

label recruitment_event_flow(event, worker):
    # Set up the scene with background
    python:
        bg_image = event.get("background_image", "images/event_bg.png")
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
    scene expression current_bg with dissolve
    show expression Solid("#00000080")  # Semi-transparent black overlay
    
    # Calculate cost
    python:
        daily_cost = worker.get("comfort_desired", 50)
        worker["daily_cost"] = daily_cost
        
        # Replace placeholders in description and dialogue
        worker_name = worker.get("name", "Unknown")
        description = event["description"].replace("[event_worker]", worker_name)
        dialogue_text = event.get("dialogue", "").replace("[event_worker]", worker_name)
        description = description.replace("[COST]", str(daily_cost))
        dialogue_text = dialogue_text.replace("[COST]", str(daily_cost))
        
        # Prepare choices with cost replacement
        choices = event.get("choices", [])
        processed_choices = []
        for choice in choices:
            choice_text = choice.get("option", "Choice")
            choice_text = choice_text.replace("[COST]", str(daily_cost))
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
    python:
        bg_image = event.get("background_image", "images/event_bg.png")
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
    scene expression current_bg with dissolve
    show expression Solid("#00000080")  # Semi-transparent black overlay
    
    python:
        daily_cost = worker.get("comfort_desired", 50)
        worker["daily_cost"] = daily_cost
        worker["comfort_level"] = worker.get("comfort_desired", 1)
        worker_name = worker.get("name", "Unknown")
        description = event["description"].replace("[event_worker]", worker_name)
        description = description.replace("[COST]", str(daily_cost))
    
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
