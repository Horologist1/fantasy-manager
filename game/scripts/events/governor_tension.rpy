# governor_tension.rpy
# Governor's Tension System - Events and narrative

init python:
    # Variable to store pending tension event type
    store._pending_tension_event = None

# ==========================================
# GOVERNOR'S RETALIATION - One-time event
# Triggered when player chooses assassination/blackmail path
# ==========================================

label governor_retaliation:
    $ start_new_conversation()
    
    scene black
    with fade
    
    centered "{color=#8b0000}A shadow falls upon your establishment...{/color}"
    
    pause 1.0
    
    "As you prepare for the next phase of your plan, a hooded messenger arrives at your door."
    
    "His face is pale, his hands trembling."
    
    show screen message_window
    
    "Messenger" "M-my lord... there's been an incident. The Governor... he knows."
    
    "You" "Knows what, exactly?"
    
    "Messenger" "Your workers... some of them fell ill this morning. Violently ill."
    
    "A cold chill runs down your spine."
    
    "Messenger" "The apothecary says it's poison. Slow-acting. The Governor's favorite method for sending... messages."
    
    hide screen message_window
    
    # Apply poison to 1-2 random workers
    python:
        import random
        
        # Determine number of victims (1-2)
        num_victims = min(len(store.workers), random.choice([1, 2]))
        
        # Get workers who aren't already poisoned
        available_workers = [w for w in store.workers if "Poisoned" not in w.get("traits", [])]
        
        # Choose victims
        victims = []
        if available_workers:
            victims = random.sample(available_workers, min(num_victims, len(available_workers)))
        
        # Apply poison and "Shaken by the Governor" traits
        victim_names = []
        for victim in victims:
            add_trait_with_duration(victim, "Poisoned", 7)
            add_trait_with_duration(victim, "Shaken by the Governor", 0)  # Permanent until quest ends
            victim["health"] = max(1, victim["health"] - 15)
            victim_names.append(victim["name"])
        
        store._retaliation_victims = victim_names
    
    if store._retaliation_victims:
        if len(store._retaliation_victims) == 1:
            $ victim_name = store._retaliation_victims[0]
            "When you rush to check on your workers, you find [victim_name] writhing in agony."
            
            "[victim_name]" "M-master... the water... it tasted strange..."
            
            "The poison courses through their veins. They'll survive, but recovery will be slow."
        else:
            $ victims_str = " and ".join(store._retaliation_victims)
            "When you rush to check on your workers, you find [victims_str] both collapsed on the floor."
            
            "Their bodies convulse with the effects of the poison. They'll survive, but barely."
        
        pause 0.5
    
    scene black
    with fade
    
    centered "{color=#8b0000}A message has been delivered.{/color}"
    
    pause 0.8
    
    "A note is found pinned to your door, sealed with the Governor's crest."
    
    "The message is simple:"
    
    centered "{i}\"I know what you're planning. Consider this your first and only warning.\n\nEvery move you make, I will counter. Every ally you gather, I will turn.\n\nYou may run this little establishment, but I run this city.\n\n- G.\"{/i}"
    
    pause 1.0
    
    "You crumple the note in your fist."
    
    "You" "So be it. If the Governor wants a war, he shall have one."
    
    "You" "But I will be the one left standing."
    
    pause 0.5
    
    centered "{color=#f4c594}The Governor is now aware of your plans.\nRandom incidents may occur as you progress.\nStay vigilant.{/color}"
    
    pause 1.5
    
    # Clean up
    $ store._retaliation_victims = None
    
    # Return to tavern
    jump tavern


# ==========================================
# GOVERNOR'S TENSION EVENTS - Random events
# Triggered periodically from objective 10 onwards
# ==========================================

label governor_tension_event:
    $ start_new_conversation()
    
    # Get the pending event type
    $ tension_type = store._pending_tension_event
    $ store._pending_tension_event = None
    
    if tension_type == "poison":
        jump governor_poison_event
    elif tension_type == "sabotage":
        jump governor_sabotage_event
    elif tension_type == "spy":
        jump governor_spy_event
    else:
        # Fallback - shouldn't happen
        jump tavern


label governor_poison_event:
    scene black
    with fade
    
    "A worker stumbles into your office, their face pale and covered in sweat."
    
    python:
        victim_name = apply_governor_poison_event()
        store._tension_victim = victim_name
    
    if store._tension_victim:
        $ vname = store._tension_victim
        
        "[vname]" "M-master... I don't feel well..."
        
        "[vname] collapses onto a chair, clutching their stomach."
        
        "You" "What happened? What did you eat?"
        
        "[vname]" "Just... the usual breakfast... but... the water had a strange taste..."
        
        "You recognize the symptoms. The Governor's agents have struck again."
        
        "{color=#8b0000}[vname] has been poisoned!{/color}"
        "{color=#888888}They will suffer health and energy penalties until the poison wears off.{/color}"
    else:
        "But when you check on them, they seem fine. Perhaps it was just fatigue."
        "You remain vigilant. The Governor's shadow looms over everything."
    
    $ store._tension_victim = None
    
    pause 1.0
    
    jump tavern


label governor_sabotage_event:
    scene black
    with fade
    
    "You hear a commotion from one of your buildings..."
    
    python:
        building_name = apply_governor_sabotage_event()
        store._tension_building = building_name
    
    if store._tension_building:
        $ bname = store._tension_building
        
        "When you arrive at [bname], you find the place in disarray."
        
        "Equipment has been tampered with. Supplies have been spoiled."
        
        "A guard approaches you, looking ashamed."
        
        "Guard" "My lord, a stranger was seen leaving the premises last night."
        
        "Guard" "By the time we noticed the damage, they were long gone."
        
        "You" "The Governor's agents. They grow bolder."
        
        "{color=#8b0000}[bname] has been sabotaged!{/color}"
        "{color=#888888}The building's effectiveness has been temporarily reduced.{/color}"
    else:
        "But when you investigate, everything seems in order."
        "Perhaps it was just a false alarm. Still, you remain on guard."
    
    $ store._tension_building = None
    
    pause 1.0
    
    jump tavern


label governor_spy_event:
    scene black
    with fade
    
    "Something feels wrong when you count the day's earnings..."
    
    python:
        stolen = apply_governor_spy_event()
        store._tension_stolen = stolen
    
    if store._tension_stolen and store._tension_stolen > 0:
        $ amount = store._tension_stolen
        
        "The numbers don't add up. Someone has been skimming from your coffers."
        
        "Upon investigation, you find that a \"new hire\" in your accounting staff..."
        
        "...vanished sometime during the night, along with a significant sum."
        
        "You" "A spy. The Governor placed a spy among my people."
        
        "{color=#8b0000}${amount} has been stolen by the Governor's spy!{/color}"
        "{color=#888888}Be careful - the Governor has eyes everywhere.{/color}"
    else:
        "After careful counting, everything seems to be in order."
        "But you can't shake the feeling of being watched."
    
    $ store._tension_stolen = None
    
    pause 1.0
    
    jump tavern
