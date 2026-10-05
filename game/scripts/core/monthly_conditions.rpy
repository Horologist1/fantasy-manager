# Atomic JSON string keeps snapshot compatibility and Ren'Py rollback simple.
default monthly_condition_state = ""

init python:
    import fm_monthly.conditions as _fm_monthly
    import json as _monthly_json

    def monthly_period():
        return (max(1, int(store.current_year)) - 1) * 12 + max(1, int(store.current_month)) - 1

    def monthly_catalog():
        # Catalog is runtime data, never copied into a save except the active card.
        known = {"buildings": set(), "professions": set(), "skills": set()}
        for bt in getattr(store, "building_types_json", {}).get("building_types", []):
            known["buildings"].add(bt.get("id"))
            for job in bt.get("professions", []):
                known["professions"].add(job.get("id"))
                known["skills"].update(job.get("skills", []) or [])
                for story in job.get("daily_stories", []):
                    known["skills"].update(story.get("skill_options", []) or [])
        try:
            with renpy.file("data/monthly_conditions/cards.json") as handle:
                data = _monthly_json.loads(handle.read().decode("utf-8-sig"))
            cards, errors = _fm_monthly.validate_catalog(data, known)
            for error in errors:
                renpy.log("MONTHLY: " + error)
            return [card for card in cards if not card.get("nsfw") or getattr(persistent, "nsfw_enabled", False)]
        except (ValueError, OSError, TypeError) as exc:
            renpy.log("MONTHLY: catalog unavailable: " + str(exc))
            return [_fm_monthly.NEUTRAL]

    def monthly_sync():
        raw = getattr(store, "monthly_condition_state", "")
        # Do not re-read catalogs during UI rendering or for each worker.
        if raw and _fm_monthly.valid_state(raw) and _fm_monthly.decode(raw)["month"] == monthly_period():
            return
        store.monthly_condition_state = _fm_monthly.sync(raw, monthly_period(), monthly_catalog(), renpy.random.random)

    def monthly_state():
        raw = getattr(store, "monthly_condition_state", "")
        return _fm_monthly.decode(raw if raw and _fm_monthly.valid_state(raw) else _fm_monthly.initial(monthly_period()))

    def monthly_toggle():
        monthly_sync()
        store.monthly_condition_state = _fm_monthly.toggle(store.monthly_condition_state)
        renpy.restart_interaction()

    def monthly_skill(worker, skill, building_type, profession):
        value = calculate_skill_with_traits(worker, skill)
        return _fm_monthly.skill_value(store.monthly_condition_state, building_type, profession, skill, value)

    def monthly_earnings(value, building_type, profession):
        return _fm_monthly.payout(store.monthly_condition_state, building_type, profession, value)

    def monthly_effect_lines(card=None):
        card = card if card is not None else monthly_state()["card"]
        result = []
        buildings = getattr(store, "building_types_json", {}).get("building_types", [])
        for effect in card["effects"]:
            scope = []
            for building_id in effect.get("buildings", []):
                scope.append(next((bt.get("name", building_id) for bt in buildings if bt.get("id") == building_id), building_id))
            for job_id in effect.get("professions", []):
                scope.append(next((job.get("name", job_id) for bt in buildings
                    if not effect.get("buildings") or bt.get("id") in effect["buildings"]
                    for job in bt.get("professions", []) if job.get("id") == job_id), job_id))
            if effect["type"] == "skill":
                label = "%+g %s" % (effect["value"], ", ".join(effect["skills"]))
            else:
                label = "%+g%% positive activity earnings" % round((effect["value"] - 1) * 100, 2)
            result.append(label + " — " + " / ".join(scope))
        return result

    def monthly_presentation():
        state = monthly_state()
        card = state["card"]
        hidden = card.get("nsfw", False) and not getattr(persistent, "nsfw_enabled", False)
        return {
            "name": "Monthly condition" if hidden else card["name"],
            "description": "Temporary activity modifiers." if hidden else card["description"],
            "image": "" if hidden or not card.get("image") or not renpy.loadable(card["image"]) else card["image"],
            "effects": monthly_effect_lines(card),
            "enabled": state["enabled"], "requested": state["requested"],
            "pending": ("Will activate next month." if state["requested"] else "Will deactivate next month.") if state["requested"] != state["enabled"] else "",
            "duration": "Through day 28 of %s, year %s" % (month_names[store.current_month - 1], store.current_year),
        }

    def monthly_report_note(building_type, profession, skills, positive):
        bits = []
        for skill in skills:
            delta, _ = _fm_monthly.modifiers(store.monthly_condition_state, building_type, profession, skill)
            if delta:
                bits.append("%s %+g" % (skill, delta))
        _, mult = _fm_monthly.modifiers(store.monthly_condition_state, building_type, profession)
        if positive and mult != 1:
            bits.append("positive earnings x%g" % mult)
        if not bits:
            return ""
        return "Monthly: " + monthly_presentation()["name"] + " — " + "; ".join(bits)

    def monthly_intro_entry():
        # Existing popup supports authored formatting, so quote catalog text here.
        card = monthly_presentation()
        safe = lambda text: str(text).replace("{", "{{").replace("[", "[[")
        return {"title": "Monthly conditions", "body": [
            "This condition lasts through the end of the current month. Its effects change activity performance, not learned skills.",
            safe(card["name"] + ": " + "; ".join(card["effects"])),
            "Select the underlined calendar date in the Tavern to review the card. You may adapt your staff or keep your current organization; no workers are reassigned automatically.",
            "The checkbox changes whether conditions are enabled starting NEXT month. You can cancel a pending change before then."]}

    def monthly_maybe_intro():
        if monthly_state()["enabled"] and monthly_state()["card"]["effects"]:
            maybe_show_intro_popup("monthly_conditions")

    def monthly_open():
        monthly_sync()
        renpy.show_screen("monthly_card")
        monthly_maybe_intro()

screen monthly_card(transition=False):
    on "show" action Function(monthly_maybe_intro)
    modal True
    zorder 180
    $ card = monthly_presentation()
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 740
        padding (40, 36)
        background None
        fixed:
            imagebutton:
                id "monthly_close"
                idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                action (Return() if transition else Hide("monthly_card"))
                xalign 1.0
                ypos 0
            text "[card['name']!q]":
                font gui.text_font
                color gui.journal_dark_color
                bold False
                outlines []
                size font_size(42)
                xalign 0.5
                ypos 25
                xsize 540
                text_align 0.5
            text "[card['duration']!q]":
                size font_size(26)
                color gui.journal_text_color
                xalign 0.5
                ypos 130
            viewport:
                xpos 5
                ypos 180
                xsize 630
                ysize 330
                mousewheel True
                draggable True
                vbox:
                    spacing 18
                    xsize 620
                    if card["image"]:
                        add Transform(card["image"], xysize=(550, 220), fit="contain") xalign 0.5
                    text "[card['description']!q]" size font_size(32) color gui.journal_text_color
                    if not card["enabled"]:
                        text "Monthly conditions disabled." size font_size(32) color gui.journal_text_color
                    for effect in card["effects"]:
                        text "[effect!q]" size font_size(30) color gui.journal_text_color
            vbox:
                xpos 5
                ypos 545
                xsize 620
                spacing 10
                button:
                    id "monthly_toggle"
                    action Function(monthly_toggle)
                    background None
                    hover_background None
                    padding (0, 8)
                    yminimum 55
                    hbox:
                        spacing 12
                        add Transform("gui/icons/batch_checkbox_on.png" if card["requested"] else "gui/icons/batch_checkbox_off.png", xysize=(26, 26)) yalign 0.5
                        text "Enable monthly conditions" size font_size(32) color gui.journal_dark_color
                if card["pending"]:
                    text "[card['pending']!q]" size font_size(32) color gui.journal_text_color
    key "game_menu" action (Return() if transition else Hide("monthly_card"))

screen monthly_transition():
    zorder 50
    $ card = monthly_presentation()
    vbox:
        xalign 0.5
        # Sube un poco al crecer el texto, para que la lista de efectos no se
        # salga por abajo en un mes con varias condiciones.
        ypos 600
        xsize 1200
        spacing 14
        # Esto se lee a pantalla completa y durante un segundo: con 28/22 px
        # quedaba diminuto. El nombre del mes es el titular del momento.
        text "[card['name']!q]" size font_size(46) color "#ffffff" xalign 0.5 text_align 0.5
        if store.current_day == 1:
            text "[card['duration']!q]" size font_size(30) color "#ffffff" xalign 0.5 text_align 0.5
            for effect in card["effects"]:
                text "[effect!q]" size font_size(30) color "#ffffff" xalign 0.5 text_align 0.5
        if not card["enabled"]:
            text "Monthly conditions disabled." size font_size(30) color "#ffffff" xalign 0.5
        textbutton "Review monthly conditions":
            action Function(monthly_open)
            xalign 0.5
            text_size font_size(36)
