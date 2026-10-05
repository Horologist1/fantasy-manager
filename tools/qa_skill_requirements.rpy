# Isolated QA for choice-level skill_requirements. Plays real events through
# handle_random_event and clicks the production screens with the SDK test mouse.
# Installed only in the disposable copy by tools/qa_skill_requirements.py.
init python:
    import os as _qa_os
    import json as _qa_json

    def qa_sr_out(name):
        return _qa_os.path.join(config.savedir, name)

    def qa_sr_rects(screen_name):
        """Absolute button rectangles in blit (authored) order, insensitive ones included."""
        displayable = renpy.get_screen(screen_name)
        if displayable is None:
            return []
        Button = renpy.display.behavior.Button
        Render = renpy.display.render.Render
        root = renpy.display.render.render(displayable, config.screen_width, config.screen_height, 0, 0)
        rows = []
        def walk(render, ox, oy):
            for entry in render.children:
                child, xo, yo = entry[0], entry[1], entry[2]
                if not isinstance(child, Render):
                    continue
                x, y = ox + xo, oy + yo
                viewports = [d for d in (child.render_of or []) if isinstance(d, renpy.display.viewport.Viewport)]
                if viewports:
                    vp = viewports[0]
                    surface = renpy.display.render.render(vp.child, vp.child_width or vp.width, vp.child_height or vp.height, 0, 0)
                    walk(surface, x - int(vp.xadjustment.value), y - int(vp.yadjustment.value))
                    continue
                if any(isinstance(d, Button) for d in (child.render_of or [])):
                    rows.append((int(x), int(y), int(child.width), int(child.height)))
                    continue
                walk(child, x, y)
        walk(root, 0, 0)
        return rows

    def qa_sr_tick():
        plan = renpy.session.get("qa_sr_plan")
        if not plan:
            return
        active = next((s for s in ("random_event_choice", "choose_event_worker_screen") if renpy.get_screen(s)), None)
        if active is None:
            renpy.queue_event("dismiss")
            return
        if active != plan.get("active"):
            plan["active"] = active
            plan["phase"] = 0
            plan["settle"] = 10
            plan["queue"] = list(plan["clicks"].get(active, []))
            if active == "random_event_choice":
                plan["options"] = [[str(c.get("option")), bool(c.get("_blocked")), str(c.get("_blocked_reason") or "")]
                                   for c in (store.temp_prepared_choices or [])]
            else:
                plan["eligible"] = [w.get("name") for w in (store.temp_eligible_workers_for_event or [])]
            return
        if plan["settle"] > 0:
            plan["settle"] -= 1
            if plan["settle"] == 0:
                renpy.screenshot(qa_sr_out("%s_%s.png" % (plan["case"], active)))
            return
        if not plan["queue"]:
            return
        rects = qa_sr_rects(active)
        target = plan["queue"][0]
        if target >= len(rects):
            plan.setdefault("problems", []).append("click target %d missing on %s (%d buttons)" % (target, active, len(rects)))
            plan["queue"].pop(0)
            return
        x, y, w, h = rects[target]
        mouse = renpy.test.testmouse
        phase = plan["phase"]
        if phase == 0:
            mouse.move_mouse(x + w // 2, y + h // 2)
        elif phase == 1:
            mouse.press_mouse(1)
        elif phase == 2:
            mouse.release_mouse(1)
        else:
            plan["queue"].pop(0)  # still here: that row was locked; go on to the next target
        plan["phase"] = (phase + 1) % 4

    def qa_sr_worker(name, skills, building):
        worker = {"name": name, "folder": "blossom", "gender": "female", "level": 1, "traits": [],
                  "skills": dict(skills), "comfort_desired": 2, "nsfw": False}
        ensure_worker_defaults(worker)
        worker["skills"].update(skills)
        worker["traits"] = []
        worker["assigned_building"] = building
        return worker

    def qa_sr_setup():
        persistent.nsfw_enabled = False
        store.at_main_menu = False
        store.tutorial_active = False
        store.money = 10000
        store.available_buildings = {"QA Guild": {"type": "adventurers_guild", "name": "QA Guild", "reputation": 50,
                                                  "skill": 10, "skill_bonus": 0, "level": 1}}
        store.workers = [
            qa_sr_worker("Ready Rae", {"Combat": 80, "Agility": 60, "Charm": 30}, "QA Guild"),
            qa_sr_worker("Brawny Bo", {"Combat": 90, "Agility": 30, "Charm": 50}, "QA Guild"),
            qa_sr_worker("Novice Nia", {"Combat": 10, "Agility": 10, "Charm": 10}, "QA Guild"),
        ]
        store.current_affected_building = None

    def qa_sr_worker_named(name):
        return next(w for w in store.workers if w["name"] == name)

    def qa_sr_event(case, mode, choices, **extra):
        event = {"id": "qa_sr_" + case, "description": "A guild contract arrives.", "worker_selection": mode,
                 "building_type": ["adventurers_guild"], "no_dialogue": True, "background_image": "event_bg",
                 "choices": choices}
        event.update(extra)
        return event

    GUARANTEED = {"option": "Send someone who can fight AND move.", "skill_requirements": {"Combat": 70, "Agility": 55},
                  "message_success": "[acting_worker] clears the pass without a scratch.",
                  "effect": {"money": 500, "add_trait": "Wise", "event_flags": {"qa_sr_flag": True}}}
    DECLINE = {"option": "Turn the contract down.", "message": "You pass.", "effect": {}}

    def qa_sr_cases():
        nested = dict(GUARANTEED, effect={"success": {"money": 500, "add_trait": "Wise"}, "failure": {"money": -999}})
        rolled = {"option": "Charm the client into better terms.", "condition": "Charm", "threshold": 0,
                  "skill_requirements": {"Combat": 70},
                  "message_success": "Deal.", "message_failure": "No deal.",
                  "effect": {"success": {"money": 200}, "failure": {"money": -50}}}
        impossible = dict(GUARANTEED, skill_requirements={"Combat": 200})
        return [
            # case, event, preselected worker, clicks per screen, expectations
            ("choose_guaranteed", qa_sr_event("choose_guaranteed", "choose", [GUARANTEED, DECLINE]), None,
             {"random_event_choice": [0], "choose_event_worker_screen": [0]},
             {"eligible": ["Ready Rae"], "money": 500, "trait_on": "Ready Rae", "flag": True, "blocked": [False, False]}),
            ("random_guaranteed", qa_sr_event("random_guaranteed", "random", [GUARANTEED, DECLINE]), None,
             {"random_event_choice": [0]},
             {"money": 500, "trait_on": "Ready Rae", "flag": True}),
            ("choose_rolled", qa_sr_event("choose_rolled", "choose", [rolled, DECLINE]), None,
             {"random_event_choice": [0], "choose_event_worker_screen": [0]},
             {"eligible_set": ["Brawny Bo", "Ready Rae"], "money_in": [200, -50]}),
            ("nobody_qualifies", qa_sr_event("nobody_qualifies", "choose", [impossible, DECLINE]), None,
             {"random_event_choice": [0, 1]},
             {"money": 0, "blocked": [True, False]}),
            ("preselected_short", qa_sr_event("preselected_short", "random", [GUARANTEED, DECLINE]), "Novice Nia",
             {"random_event_choice": [0, 1]},
             {"money": 0, "blocked": [True, False], "reason_has": "Novice Nia does not meet"}),
            ("nested_effect", qa_sr_event("nested_effect", "choose", [nested, DECLINE]), None,
             {"random_event_choice": [0], "choose_event_worker_screen": [0]},
             {"money": 500, "trait_on": "Ready Rae"}),
        ]

    def qa_sr_run():
        results = []
        for case, event, preselected, clicks, expect in qa_sr_cases():
            qa_sr_setup()
            store.event_flags.pop("qa_sr_flag", None)
            store.current_event = event
            store.current_worker = qa_sr_worker_named(preselected) if preselected else None
            before = store.money
            plan = {"case": case, "clicks": clicks}
            renpy.session["qa_sr_plan"] = plan
            try:
                renpy.call_in_new_context("qa_sr_entry")
            except Exception as exc:
                plan.setdefault("problems", []).append("exception: %r" % exc)
            finally:
                renpy.session.pop("qa_sr_plan", None)
                renpy.test.testmouse.reset()
            problems = list(plan.get("problems", []))
            delta = store.money - before
            if "money" in expect and delta != expect["money"]:
                problems.append("money delta %d, expected %d" % (delta, expect["money"]))
            if "money_in" in expect and delta not in expect["money_in"]:
                problems.append("money delta %d not in %r" % (delta, expect["money_in"]))
            if "eligible" in expect and plan.get("eligible") != expect["eligible"]:
                problems.append("picker listed %r, expected %r" % (plan.get("eligible"), expect["eligible"]))
            if "eligible_set" in expect and sorted(plan.get("eligible") or []) != expect["eligible_set"]:
                problems.append("picker listed %r, expected %r" % (plan.get("eligible"), expect["eligible_set"]))
            if "blocked" in expect and [o[1] for o in plan.get("options", [])] != expect["blocked"]:
                problems.append("blocked flags %r, expected %r" % ([o[1] for o in plan.get("options", [])], expect["blocked"]))
            if "reason_has" in expect and not any(expect["reason_has"] in o[2] for o in plan.get("options", [])):
                problems.append("no lock reason mentions %r: %r" % (expect["reason_has"], plan.get("options")))
            if "trait_on" in expect:
                holders = [w["name"] for w in store.workers if "Wise" in (w.get("traits") or [])]
                if holders != [expect["trait_on"]]:
                    problems.append("Wise added to %r, expected [%r]" % (holders, expect["trait_on"]))
            if expect.get("flag") and not store.event_flags.get("qa_sr_flag"):
                problems.append("event flag not set")
            results.append({"case": case, "options": plan.get("options"), "eligible": plan.get("eligible"),
                            "money_delta": delta, "problems": problems})
        with open(qa_sr_out("report.json"), "w", encoding="utf-8") as handle:
            _qa_json.dump({"cases": len(results), "failures": sum(1 for r in results if r["problems"]), "results": results}, handle, indent=1)

label qa_sr_entry:
    show screen qa_sr_driver
    call handle_random_event
    hide screen qa_sr_driver
    return

screen qa_sr_driver():
    zorder 1000
    timer 0.04 repeat True action Function(qa_sr_tick, _update_screens=False)

label splashscreen:
    if not _qa_os.environ.get("FM_QA_SKILL_REQ"):
        return
    $ store.main_menu = False
    $ qa_sr_run()
    $ renpy.quit(status=0)
