# A small story location, independent of the business/assignment systems.
# Progress lives in event_flags, already covered by every snapshot restore pass.
define church_caretaker = Character("Priestess")
# One active background. Keep scene identifiers used by the narrative; the
# other supplied backgrounds are stored with the building art for later use.
image church_interior = Transform("images/buildings/church.png", xysize=(1920, 1080))
image church_night = Transform("images/buildings/church.png", xysize=(1920, 1080))
image church_priestess_room = Transform("images/buildings/church.png", xysize=(1920, 1080))
image church_cemetery = Transform("images/buildings/church.png", xysize=(1920, 1080))
define church_map_position = (452, 178)

init python:
    def church_map_art(selected=False):
        """Grow behind the same wall; the hidden facade never catches clicks."""
        size = 260 if selected else 240
        offset = (280 - size) // 2
        sprite = Transform("gui/map/church.png", xysize=(size, size))
        layers = []
        if selected:
            silhouette = AlphaMask(Solid("#ffffff", xysize=(size, size)), sprite)
            for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (-3, 3), (3, -3), (3, 3)):
                layers.extend(((offset + dx, offset + dy), silhouette))
        # Match the map's black ink, with the white hover halo outside it.
        ink = AlphaMask(Solid("#11110e", xysize=(size, size)), sprite)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            layers.extend(((offset + dx, offset + dy), ink))
        layers.extend(((offset, offset), sprite))
        # This mask follows the existing map's crenellations at
        # church_map_position. Apply it AFTER enlargement and outline, so
        # neither the building nor its hover border can cover the masonry.
        return AlphaMask(Composite((280, 280), *layers), "gui/map/church_wall_mask.svg")

    def church_story_status():
        flags = getattr(store, "event_flags", None) or {}
        stage = max(0, min(3, int(flags.get("church_intro_stage", 0) or 0)))
        ready = stage < 3 and flags.get("church_last_visit_day") != calculate_total_days()
        return stage, ready

    def church_complete_visit(stage):
        current, ready = church_story_status()
        if not ready or current != stage:
            return False
        if not hasattr(getattr(store, "event_flags", None), "get"):
            store.event_flags = {}
        store.event_flags["church_intro_stage"] = stage + 1
        store.event_flags["church_last_visit_day"] = calculate_total_days()
        if stage == 2:
            store.event_flags["church_circle_welcomed"] = True
        return True

    # Immutable displayables constructed once, never in prediction or a label.
    church_map_idle = church_map_art(False)
    church_map_hover = church_map_art(True)
    # Reuse the map's dirt-road texture in the gap below the steps. This
    # scenery stays fixed during hover; the wall and church cover its edges.
    church_map_path = AlphaMask(
        Composite((280, 280), (56, 232), Crop((344, 928, 30, 30), "images/map.png")),
        "gui/map/church_wall_mask.svg")

# Compatibility name for saves made with the first church screen. New visits
# use the same narrator/Character/menu presentation as the Academy and Arena.
screen church_menu():
    predict False
    timer 0.01 action Return("leave")

label church_visit:
    hide screen tooltip
    hide screen map_screen
    hide screen church_menu
    scene expression ("church_night" if church_is_night() else "church_interior")
    $ maybe_show_intro_popup("church_visit")
    if not church_life_state()["unlocked"] and church_exploration()["stage"] == 0:
        jump church_discovery_arrival
    church_caretaker "The Circle remembers those who do not return from their work. Their resting places are here, beyond the wall."
    jump church_dialogue_menu

label church_dialogue_menu:
    scene expression ("church_night" if church_is_night() else "church_interior")
    $ _church_stage = church_exploration()["stage"]
    menu:
        church_caretaker "What brings you to the Circle?"
        "Ask about death and the cemetery.":
            church_caretaker "When a worker dies, we keep their remains in one of ten resting places. Their name, their possessions, and the life they lived stay with them."
            church_caretaker "If all ten places are occupied, we cannot preserve another soul for the rite. Raise someone or release a resting place before you need it."
            church_caretaker "The dead cannot be hired again. Those whose remains we keep may return through the Circle."
            jump church_dialogue_menu
        "Examine the empty Circle." if not church_life_state()["unlocked"] and not church_ritual_ready():
            narrator "Four hollows surround a shallow notch in the ring. The seals you have found rest beside it."
            church_caretaker "The Circle needs all four seals. Follow the marks on the ones you have found; they will lead you to the others."
            jump church_dialogue_menu
        "Stay for evening prayer." if not church_life_state()["unlocked"] and _church_stage == 2:
            jump church_discovery_prayer
        "Visit the priestess's room." if not church_life_state()["unlocked"] and _church_stage == 3:
            jump church_discovery_room
        "Review the discovered seals and clues." if _church_stage > 0:
            call church_read_clues
            jump church_dialogue_menu
        "Study the Circle ritual." if not church_life_state()["unlocked"] and church_ritual_ready():
            jump church_ritual
        "Resurrect a worker." if church_life_state()["unlocked"]:
            jump church_cemetery
        "Visit the cemetery.":
            jump church_cemetery
        "Leave.":
            jump church_leave

label church_exploration_wait:
    church_caretaker "The seal you found today is still settling. Its mark will answer another only after dawn. Come back tomorrow, and we can continue."
    church_caretaker "You may still read your discoveries or visit the graves. The resting places remain in our care."
    jump church_dialogue_menu

label church_discovery_arrival:
    if church_life_state()["unlocked"] or church_exploration()["stage"] != 0:
        jump church_dialogue_menu
    if not church_can_explore():
        jump church_exploration_wait
    narrator "As you cross the threshold, a loose stone turns beneath your boot. In its hollow lies a small seal, carved with a mountain."
    church_caretaker "You found Stone. We thought the old Circle had fallen silent. Turn it over; the makers always left a path to the next keeper."
    $ _church_discovery_result = church_discover_seal(0)
    if _church_discovery_result != "found":
        jump church_dialogue_menu
    narrator "On the back, beneath a worn notch, you read: {i}Stone takes the first place. Seek Water where the names of the departed are kept.{/i}"
    church_caretaker "The cemetery, beyond the side door. But let this seal rest by the ring tonight. Each one must settle from dusk until dawn before the next can answer."
    church_caretaker "Return tomorrow and search among the memorial stones. The dead in our care can be visited at any time."
    $ renpy.notify("Stone seal found. Its inscription has been recorded.")
    jump church_dialogue_menu

label church_discovery_cemetery:
    if church_life_state()["unlocked"] or church_exploration()["stage"] != 1:
        jump church_cemetery
    if not church_can_explore():
        jump church_exploration_wait
    scene church_cemetery
    narrator "Following the mark on Stone, you walk between the cypresses. A shallow circle on an old memorial has caught the morning rain."
    narrator "As you brush away the wet leaves, a blue-grey seal slips free. A wave is carved on its face."
    $ _church_discovery_result = church_discover_seal(1)
    if _church_discovery_result != "found":
        jump church_cemetery
    narrator "Water bears a second inscription: {i}Water passes before Wind. Seek the breath that carries the names at the evening prayer.{/i}"
    church_caretaker "We speak the names here so they are not lost. At evening prayer, we carry them back inside. Listen to the old response when you return tomorrow."
    $ renpy.notify("Water seal found. The evening prayer may reveal Wind.")
    jump church_cemetery

label church_discovery_prayer:
    if church_life_state()["unlocked"] or church_exploration()["stage"] != 2:
        jump church_dialogue_menu
    if not church_can_explore():
        jump church_exploration_wait
    church_caretaker "Stay, then. Listen to the response between the names. That is the oldest part of the prayer."
    narrator "You take a place by the aisle. The light drains from the windows, and the priestess lights the last candles."
    scene church_night with Dissolve(0.8)
    narrator "The names of the departed pass from voice to voice. A breath stirs the candle beside an open book."
    church_caretaker "{i}Water passes before Wind. After Wind comes Flame, with no silence between them. Let no name fall into the silence.{/i}"
    narrator "Beneath the book, a small hollow holds a seal cut with three flowing lines. When the prayer ends, you lift Wind from its resting place."
    $ _church_discovery_result = church_discover_seal(2)
    if _church_discovery_result != "found":
        jump church_dialogue_menu
    church_caretaker "Flame must follow Wind immediately. Keep those words with the inscriptions. I have the last seal in my room, with the old records."
    church_caretaker "It will answer when Wind has rested. Come tomorrow; I will show you why the Circle was left unfinished."
    $ renpy.notify("Wind seal found. The words of the prayer have been recorded.")
    jump church_dialogue_menu

label church_discovery_room:
    if church_life_state()["unlocked"] or church_exploration()["stage"] != 3:
        jump church_dialogue_menu
    if not church_can_explore():
        jump church_exploration_wait
    scene church_priestess_room with Dissolve(0.5)
    narrator "The priestess welcomes you into a quiet room behind the sanctuary. Beside the hearth, an old register lies open next to a small wooden chest."
    church_caretaker "The last keeper scattered the seals after a rite was attempted for someone whose remains had already been lost. The Circle needs a body to call a soul home."
    church_caretaker "That is why we preserve ten resting places. I kept Flame here, with the names. Your search has brought the other keepers back together."
    narrator "She opens the chest and places a warm, amber-coloured seal in your hand. Its flame is carved beside a tiny arrow pointing away from Wind."
    $ _church_discovery_result = church_discover_seal(3)
    if _church_discovery_result != "found":
        jump church_dialogue_menu
    church_caretaker "All four are here. Stone begins at the notch. The inscriptions and the prayer tell you how the others follow. You may arrange them now."
    church_caretaker "A mistaken arrangement harms no one. Read your discoveries again whenever you need them."
    $ renpy.notify("Flame seal found. The Circle ritual is ready to attempt.")
    jump church_dialogue_menu

label church_read_clues:
    $ _church_known_stage = church_exploration()["stage"]
    if church_life_state()["unlocked"]:
        $ _church_known_stage = 4
    if _church_known_stage >= 1:
        narrator "{b}Stone — the temple threshold.{/b} {i}Stone takes the first place. Seek Water where the names of the departed are kept.{/i}"
    if _church_known_stage >= 2:
        narrator "{b}Water — the cemetery memorial.{/b} {i}Water passes before Wind. Seek the breath that carries the names at the evening prayer.{/i}"
    if _church_known_stage >= 3:
        narrator "{b}Wind — the evening prayer.{/b} {i}After Wind comes Flame, with no silence between them.{/i} Flame must follow Wind immediately."
    if _church_known_stage >= 4:
        narrator "{b}Flame — the priestess's room.{/b} The last seal completes the set. Begin at the notch and use the inscriptions to place all four."
    return

label church_ritual:
    if not church_ritual_ready():
        church_caretaker "We still need the missing seals. Follow the discoveries you have recorded before trying the Circle."
        jump church_dialogue_menu
    narrator "Four seals lie beside an empty ring: stone, water, wind, and flame. The first place is marked by a shallow notch."
    call church_read_clues
    church_caretaker "Place the seals in order, beginning at the notch. The whole circle must agree. A mistake costs nothing; listen and try again."
    jump church_ritual_place

label church_ritual_place:
    if not church_ritual_ready():
        jump church_dialogue_menu
    if church_life_state()["unlocked"]:
        jump church_dialogue_menu
    $ _church_seals = church_life_state()["seals"]
    $ _church_sequence = ", ".join(_church_seals) if _church_seals else "None yet"
    $ _church_position = len(_church_seals) + 1
    menu:
        narrator "Seals placed: [_church_sequence]. Choose seal [_church_position] of four."
        "Stone." if "Stone" not in _church_seals:
            $ _church_ritual_result = church_place_seal("Stone")
        "Water." if "Water" not in _church_seals:
            $ _church_ritual_result = church_place_seal("Water")
        "Wind." if "Wind" not in _church_seals:
            $ _church_ritual_result = church_place_seal("Wind")
        "Flame." if "Flame" not in _church_seals:
            $ _church_ritual_result = church_place_seal("Flame")
        "Read the discovered clues again.":
            call church_read_clues
            jump church_ritual_place
        "Leave the remaining seals for later.":
            jump church_dialogue_menu
    if _church_ritual_result == "unlocked":
        narrator "The last seal settles. A pale thread of light joins the four marks and closes the circle."
        church_caretaker "You have found the order. Now we can guide a soul back to its body. The rite is open to your household."
        $ renpy.notify("Resurrection unlocked at the church.")
        jump church_dialogue_menu
    if _church_ritual_result == "retry":
        narrator "The ring stays dark. The priestess returns the seals to the table."
        church_caretaker "Stone must begin it. Water must precede wind, and flame must follow wind without a gap. Read the circle once more."
        jump church_dialogue_menu
    jump church_ritual_place

label church_cemetery:
    scene church_cemetery
    if not church_life_state()["unlocked"] and church_exploration()["stage"] == 1:
        if church_can_explore():
            jump church_discovery_cemetery
        church_caretaker "Come back after dawn to search for Water. Stone needs to settle first. You can still visit the resting places today."
    $ _church_page = 0
    if not church_life_state()["graves"]:
        church_caretaker "No one from your household rests here."
        jump church_dialogue_menu
    jump church_cemetery_page

label church_cemetery_page:
    scene church_cemetery
    $ _church_count = len(church_life_state()["graves"])
    church_caretaker "[_church_count] of our ten resting places are occupied. Whose name shall we visit?"
    $ _church_pick = renpy.display_menu(church_cemetery_choices(_church_page))
    if _church_pick[0] == "leave":
        jump church_dialogue_menu
    if _church_pick[0] == "page":
        $ _church_page = _church_pick[1]
        jump church_cemetery_page
    $ _church_grave_id = _church_pick[1]
    jump church_grave_visit

label church_grave_visit:
    if church_grave(_church_grave_id) is None:
        jump church_cemetery
    $ _church_name = church_grave(_church_grave_id)["name"]
    $ _church_cause = church_grave(_church_grave_id)["cause"]
    $ _church_day = church_grave(_church_grave_id)["day"]
    $ _church_price = church_resurrection_price(_church_grave_id)
    narrator "[_church_name!q] rests beneath a simple stone. The register records the loss on day [_church_day], during [_church_cause!q]."
    menu:
        church_caretaker "Their resting place is in our keeping."
        "Perform the resurrection rite ([_church_price] coins)." if church_life_state()["unlocked"]:
            jump church_resurrection_confirm
        "Ask about the rite." if not church_life_state()["unlocked"]:
            church_caretaker "Find the four seals, then complete their circle inside the temple. Until then, we can keep the remains safe."
            jump church_grave_visit
        "Release this resting place permanently.":
            jump church_release_confirm
        "Return to the cemetery.":
            jump church_cemetery

label church_resurrection_confirm:
    menu:
        church_caretaker "For [_church_price] coins, [_church_name!q] will return with their possessions and memories. They will be unassigned and need rest before working."
        "Resurrect [_church_name!q].":
            $ _church_resurrection_result = church_resurrect(_church_grave_id)
        "Not now.":
            jump church_grave_visit
    if _church_resurrection_result == "ok":
        scene expression ("church_night" if church_is_night() else "church_interior")
        narrator "The circle brightens. A breath breaks the silence, and [_church_name!q] opens their eyes."
        church_caretaker "Take them home. Let them rest. Their place among your workers is theirs again."
    elif _church_resurrection_result == "money":
        church_caretaker "You do not have enough coins for the rite. Their resting place will remain safe."
    elif _church_resurrection_result == "already_alive":
        church_caretaker "Someone with this identity is already among your workers. We must leave this record untouched."
    else:
        church_caretaker "The rite cannot be performed from this record. Let us return to the register."
    jump church_cemetery

label church_release_confirm:
    menu:
        church_caretaker "Release [_church_name!q]'s remains? This frees one place, but they and their possessions will no longer be recoverable."
        "Release the remains permanently.":
            $ church_release_grave(_church_grave_id)
            narrator "The priestess closes the entry and makes room for another resting place."
            jump church_cemetery
        "Keep the resting place.":
            jump church_grave_visit

label church_leave:
    window hide
    $ _church_pick = None
    $ renpy.show_screen("map_screen")
    jump tavern_screen

# Retained so earlier saves can still resolve their script references.
label church_story:
    jump church_visit
