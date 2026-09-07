# governor_tension.rpy
# Governor's Tension System - Events and narrative
# Simplified: governor_event background + all text in the dialogue box below.

init python:
    store._pending_tension_event = None

    def say_governor_text(text, speaker=None, limit=170):
        """
        Show long governor-event lines in readable chunks (one click per chunk).
        """
        if not text:
            return
        cleaned = str(text).strip()
        if not cleaned:
            return
        chunks = []
        try:
            import re
            # First split by sentence boundaries, then merge up to limit.
            parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", cleaned) if p and p.strip()]
            current = ""
            for part in parts:
                if not current:
                    current = part
                    continue
                if len(current) + 1 + len(part) <= int(limit):
                    current += " " + part
                else:
                    chunks.append(current)
                    current = part
            if current:
                chunks.append(current)
        except Exception:
            chunks = []
        if not chunks:
            chunks = [cleaned]
        # renpy.say stays OUTSIDE the try: Ren'Py control flow (rollback,
        # interaction restarts) travels as exceptions, and swallowing one
        # here used to re-say the whole text in a single overflowing box.
        who = speaker if speaker is not None else narrator
        for chunk in chunks:
            renpy.say(who, chunk)

# ==========================================
# GOVERNOR'S RETALIATION - One-time event
# ==========================================

label governor_retaliation:
    $ start_new_conversation()
    $ _gov_bg = governor_event_bg if renpy.loadable(governor_event_bg) else event_bg
    scene expression _gov_bg
    with fade
    
    "A shadow falls upon your establishment."
    
    $ say_governor_text("As you prepare for the next phase of your plan, a hooded messenger arrives at your door. His face is pale, his hands trembling.")
    
    "Messenger" "M-my lord... there's been an incident. The Governor... he knows."
    
    $ say_governor_text("Your workers... some of them fell ill this morning. Violently ill. The apothecary says it's poison. Slow-acting. The Governor's favorite method for sending... messages.")
    
    # Apply poison to 1-2 random workers
    python:
        num_victims = min(len(store.workers), random.choice([1, 2]))
        available_workers = [w for w in store.workers if "Poisoned" not in w.get("traits", [])]
        victims = random.sample(available_workers, min(num_victims, len(available_workers))) if available_workers else []
        victim_names = []
        for victim in victims:
            add_trait_with_duration(victim, "Poisoned", 7)
            add_trait_with_duration(victim, "Shaken by the Governor", 0)
            victim["health"] = max(1, victim["health"] - 15)
            victim_names.append(victim["name"])
        store._retaliation_victims = victim_names
    
    if store._retaliation_victims:
        if len(store._retaliation_victims) == 1:
            $ victim_name = store._retaliation_victims[0]
            $ say_governor_text(f"When you rush to check on your workers, you find {victim_name} writhing in agony. The poison courses through their veins. They'll survive, but recovery will be slow.")
        else:
            $ victims_str = " and ".join(store._retaliation_victims)
            $ say_governor_text(f"When you rush to check on your workers, you find {victims_str} both collapsed on the floor. Their bodies convulse with the effects of the poison. They'll survive, but barely.")
    
    # Optional milestone image: note on door (governor_note_on_door.png)
    $ _note_bg = get_tutorial_milestone_image(tutorial_milestone_note_door) or _gov_bg
    scene expression _note_bg
    with fade
    $ say_governor_text("Back in your chambers, you find a blade embedded in the door. A folded note is skewered beneath it. The seal pressed into the wax is the Governor's crest. He did not bother to hide it.")
    
    "The note reads:"
    
    "\"You have been seen.\""
    
    "\"Consider this the last courtesy I shall extend.\""
    
    "\"Every step you take, I will answer. Every ally you gather, I will peel away.\""
    
    "\"This city is mine. Every soul within it — including yours — exists at my pleasure.\""
    
    "\"— G.\""
    
    $ say_governor_text("Your hands do not shake. That surprises you. He sent this to make you afraid. You hold the note to the candle flame and watch it curl to nothing. From this point forward, the Governor will act. Stay ready.")
    
    $ store._retaliation_victims = None
    window hide
    pause
    return


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
        return


label governor_poison_event:
    $ _gov_bg = governor_event_bg if renpy.loadable(governor_event_bg) else event_bg
    scene expression _gov_bg
    with fade
    
    "A worker stumbles into your office, their face pale and covered in sweat."
    
    python:
        victim_name = apply_governor_poison_event()
        store._tension_victim = victim_name
    
    if store._tension_victim:
        $ vname = store._tension_victim
        "[vname] collapses, clutching their stomach. The water had a strange taste. You recognize the symptoms - the Governor's agents have struck again."
        "[vname] has been poisoned and will suffer health and energy penalties until it wears off."
    else:
        "When you check on them, they seem fine. Perhaps it was just fatigue. You remain vigilant."
    
    $ store._tension_victim = None
    window hide
    pause
    return


label governor_sabotage_event:
    $ _gov_bg = governor_event_bg if renpy.loadable(governor_event_bg) else event_bg
    scene expression _gov_bg
    with fade
    
    python:
        building_name = apply_governor_sabotage_event()
        store._tension_building = building_name
    
    if store._tension_building:
        $ bname = store._tension_building
        "You hear a commotion. When you arrive at [bname], you find the place in disarray - equipment tampered with, supplies spoiled."
        "A guard reports a stranger seen leaving last night. It has the Governor's mark all over it."
        "[bname] has been sabotaged; its building skill bonus is temporarily reduced."
    else:
        "You hear a commotion from one of your buildings, but when you investigate, everything seems in order. You remain on guard."
    
    $ store._tension_building = None
    window hide
    pause
    return


label governor_spy_event:
    $ _gov_bg = governor_event_bg if renpy.loadable(governor_event_bg) else event_bg
    scene expression _gov_bg
    with fade
    
    python:
        stolen = apply_governor_spy_event()
        store._tension_stolen = stolen
    
    if store._tension_stolen and store._tension_stolen > 0:
        $ amount = store._tension_stolen
        "Something feels wrong when you count the day's earnings. The ledgers have been tampered with."
        "A trusted accountant - a \"new hire\" with access to your books - vanished during the night, along with [amount] coins."
        "The Governor had placed a spy in your counting-house. Be careful; he has eyes everywhere."
    else:
        "Something feels wrong when you count the earnings, but after careful counting everything is in order. You can't shake the feeling of being watched."
    
    $ store._tension_stolen = None
    window hide
    pause
    return
