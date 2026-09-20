# Loaded only in the disposable copy created by qa_json_overrides.py.
init python:
    import os as _qa_mod_os
    import json as _qa_mod_json

    def qa_mod_check(value, message):
        if not value:
            qa_mod_report(message)
            raise AssertionError(message)
        renpy.session.setdefault("qa_mod_checks", []).append(message)
        qa_mod_report()

    def qa_mod_phase():
        return _qa_mod_os.environ["FM_QA_OVERRIDE_PHASE"]

    def qa_mod_watchdog():
        ticks = renpy.session.get("qa_mod_ticks", 0) + 1
        renpy.session["qa_mod_ticks"] = ticks
        if ticks in (100, 400):
            renpy.screenshot(_qa_mod_os.path.join(config.savedir, qa_mod_phase() + "-watchdog.png"))
        if ticks > 800:
            qa_mod_report("Native interaction timed out; inspect watchdog screenshot")
            renpy.quit(status=1)

    config.periodic_callbacks.append(qa_mod_watchdog)

    def qa_mod_report(error=None):
        with open(_qa_mod_os.path.join(config.savedir, qa_mod_phase() + "-report.json"), "w", encoding="utf-8") as handle:
            _qa_mod_json.dump({"engine": renpy.version_string, "checks": renpy.session.get("qa_mod_checks", []), "error": error}, handle, indent=2)

    def qa_mod_catalogs():
        with open(_qa_mod_os.path.join(config.basedir, "qa_mod_expected.json"), encoding="utf-8") as handle:
            expected = _qa_mod_json.load(handle)[_qa_mod_os.environ["FM_QA_OVERRIDE_EXPECTED"]]
        catalog = load_workers(include_unique=True, include_encounter_only=True, for_events=True)
        worker = next(w for w in catalog if w.get("folder") == expected["worker_folder"])
        qa_mod_check(worker["cost"] == expected["worker_cost"], "Worker template replacement")
        item = next(i for i in items_json["items"] if i["id"] == expected["item_id"])
        qa_mod_check(item["price"] == expected["item_price"], "Item replacement and installation priority")
        qa_mod_check(get_trait_definition("Beautiful")["description"] == expected["trait_description"], "Trait replacement")
        building = next(b for b in building_types_json["building_types"] if b["id"] == "brothel")
        qa_mod_check(building["name"] == expected["building_name"], "Building replacement")
        profession = next(p for p in building["professions"] if p["id"] == "service")
        story = next(s for s in profession["daily_stories"] if s["id"] == expected["story_id"])
        qa_mod_check(story["report"] == expected["story_report"], "Daily story extension uses replacement")
        event = next(e for e in load_events_from_folder() if e["id"] == expected["event_id"])
        qa_mod_check(event["description"] == expected["event_description"], "Event replacement")
        if _qa_mod_os.environ.get("FM_QA_OVERRIDE_ADDITIVE"):
            qa_mod_check(any(w["name"] == "QA Additive Worker" for w in catalog), "Additive character pack remains available")
        qa_mod_check(bool(available_workers), "New-game market contains workers")

    def qa_mod_save():
        set_save_blocked_context(None)
        store.tutorial_active = False
        store.event_flags["qa_override_saved"] = True
        before = _native_save_commit_marker(_get_current_slot_name(98))
        SnapshotFileSave(98)()
        after = _native_save_commit_marker(_get_current_slot_name(98))
        qa_mod_check(bool(after[0] and after[1]) and after != before, "Fresh native snapshot save committed")

    def qa_mod_button_rect(screen, widget):
        target = renpy.get_widget(screen, widget)
        if target is None:
            return None
        Button = renpy.display.behavior.Button
        Render = renpy.display.render.Render
        def contains(node):
            return node is target or any(contains(child) for child in node.visit())
        def walk(render, ox, oy):
            for entry in render.children:
                child, x, y = entry[:3]
                if not isinstance(child, Render):
                    continue
                if any(isinstance(d, Button) and contains(d) for d in (child.render_of or [])):
                    return ox + x, oy + y, child.width, child.height
                found = walk(child, ox + x, oy + y)
                if found:
                    return found
            return None
        return walk(renpy.display.render.render(renpy.get_screen(screen), config.screen_width, config.screen_height, 0, 0), 0, 0)

    def qa_mod_click(screen, widget):
        renpy.test.testmouse.reset()
        for attempt in range(24):
            rect = qa_mod_button_rect(screen, widget)
            if rect:
                x, y, width, height = rect
                if width > 0 and height > 0 and 0 <= y < config.screen_height - height:
                    renpy.test.testmouse.move_mouse(int(x + width / 2), int(y + height / 2))
                    renpy.pause(0.05, hard=True, modal=False)
                    renpy.test.testmouse.press_mouse(1)
                    renpy.pause(0.07, hard=True, modal=False)
                    renpy.test.testmouse.release_mouse(1)
                    renpy.pause(0.15, hard=True, modal=False)
                    return
            renpy.test.testmouse.move_mouse(1300, 600)
            renpy.test.testmouse.press_mouse(5)
            renpy.test.testmouse.release_mouse(5)
            renpy.pause(0.1, hard=True, modal=False)
        qa_mod_check(False, "Could not click " + widget)

    def qa_mod_ui():
        store.main_menu = True
        renpy.show_screen("character_mods")
        renpy.pause(0.25, hard=True, modal=False)
        qa_mod_check(not _fm_mods_runtime.state()["override_mode"], "Override checkbox defaults off")
        qa_mod_click("character_mods", "mod_override_toggle")
        qa_mod_check(bool(renpy.get_screen("character_mod_override_warning")), "Click opens warning before enabling")
        qa_mod_check(not _fm_mods_runtime.state()["override_mode"], "Warning alone does not enable overrides")
        renpy.screenshot(_qa_mod_os.path.join(config.savedir, "override-warning.png"))
        qa_mod_click("character_mod_override_warning", "mod_override_cancel")
        qa_mod_check(not _fm_mods_runtime.state()["override_mode"], "Cancel keeps override off")
        qa_mod_click("character_mods", "mod_override_toggle")
        qa_mod_click("character_mod_override_warning", "mod_override_accept")
        qa_mod_check(_fm_mods_runtime.state()["override_mode"], "Confirmation enables checkbox")
        qa_mod_click("character_mods", "mod_override_toggle")
        qa_mod_check(not _fm_mods_runtime.state()["override_mode"], "Checkbox can be disabled")
        qa_mod_click("character_mods", "mod_override_toggle")
        qa_mod_click("character_mod_override_warning", "mod_override_accept")
        fm_mod_preview(_qa_mod_os.environ["FM_QA_OVERRIDE_SOURCE"])
        for attempt in range(100):
            renpy.pause(0.05, hard=True, modal=False)
            if not _fm_mods_runtime.state()["busy"]:
                break
        qa_mod_check(bool(_fm_mods_runtime.state()["preview"]), "Native preview lists exact JSON replacements")
        renpy.screenshot(_qa_mod_os.path.join(config.savedir, "override-preview.png"))
        qa_mod_click("character_mods", "mod_install_pack")
        for attempt in range(100):
            renpy.pause(0.05, hard=True, modal=False)
            if not _fm_mods_runtime.state()["busy"]:
                break
        qa_mod_check(len(_fm_mods_runtime.state()["installed"]) == 1, "Install button installs one override pack")
        qa_mod_check(not _fm_mods_runtime.state()["override_mode"], "Install returns checkbox to off")
        pack = _fm_mods_runtime.state()["installed"][0]
        qa_mod_check(pack["restart_required"] and not pack["active"], "Installation waits for next process")
        # The install collapsed the preview. Return to the top before locating
        # uninstall; native wheel input above covers reaching the install action.
        viewport = renpy.get_widget("character_mods", "mod_content_viewport")
        viewport.yadjustment.change(0)
        renpy.restart_interaction()
        renpy.pause(0.15, hard=True, modal=False)
        qa_mod_click("character_mods", "mod_uninstall_" + pack["id"])
        qa_mod_click("character_mod_uninstall_confirm", "mod_uninstall_cancel")
        qa_mod_check(not _fm_mods_runtime.state()["installed"][0]["pending_uninstall"], "Uninstall cancellation keeps pack")
        qa_mod_click("character_mods", "mod_uninstall_" + pack["id"])
        qa_mod_click("character_mod_uninstall_confirm", "mod_uninstall_confirm")
        for attempt in range(100):
            renpy.pause(0.05, hard=True, modal=False)
            if not _fm_mods_runtime.state()["busy"]:
                break
        qa_mod_check(_fm_mods_runtime.state()["installed"][0]["pending_uninstall"], "Uninstall button schedules safe removal")
        renpy.hide_screen("character_mods")
        store.main_menu = False

label splashscreen:
    $ persistent.age_verified = True
    $ persistent.nsfw_enabled = False
    $ persistent.large_font_mode = False
    $ renpy.session["qa_mod_checks"] = []
    if qa_mod_phase() == "load":
        $ snapshot_mark_load_slot(98)
        $ renpy.load(_get_current_slot_name(98))
    if qa_mod_phase() == "ui":
        $ qa_mod_ui()
    $ main_menu = False
    $ mark_new_game_start()
    jump start

label qa_mod_started:
    $ qa_mod_check(game_initialized and current_day == 1 and money == 6000 and not workers, "Actual start label completed a fresh game")
    $ qa_mod_catalogs()
    $ qa_mod_save()
    $ qa_mod_report()
    $ renpy.quit(status=0)

label qa_mod_loaded:
    $ qa_mod_check(event_flags.get("qa_override_saved"), "Native save reload with unchanged packs")
    $ qa_mod_catalogs()
    $ qa_mod_save()
    $ qa_mod_report()
    $ renpy.quit(status=0)
