# Isolated QA sweep: draws EVERY authored option list through the real
# random_event_choice / recruitment_choice_screen and checks geometry, coordinate
# input, real event/recruitment processing, and native saves. Installed only in the
# disposable copy by tools/qa_choice_layout.py.
init python:
    import os as _qa_os
    import json as _qa_json

    def qa_choice_out(name):
        return _qa_os.path.join(config.savedir, name)

    def qa_choice_note(message):
        with open(qa_choice_out("progress.txt"), "a", encoding="utf-8") as handle:
            handle.write(str(message) + "\n")
            handle.flush()

    def qa_choice_prepared(event, variant):
        """The fields random_event_choice actually reads off a prepared choice."""
        rows = []
        for index, choice in enumerate(event.get("choices") or []):
            option = str(choice.get("option") or "").strip()
            if not option:
                continue
            condition = choice.get("condition")
            lockable = bool(
                (condition and condition != "building_skill")
                or choice.get("required_traits") or choice.get("required_trait")
            )
            if variant in ("none", "preview"):
                blocked = False
            elif variant in ("all", "preview_locked"):
                blocked = lockable
            else:
                blocked = lockable and (index % 2 == 0)
            if variant.startswith("preview") and condition and condition != "building_skill":
                # events.rpy appends the live check preview when a worker is already
                # picked ("Charm 62 (+5 event) vs 70 -> 41%"); worst case here.
                threshold = choice.get("threshold")
                option += (" (%s 100 (+25 event) vs %s -> Guaranteed)" % (condition, threshold)
                           if threshold else " (%s 100 (+25 event) -> Guaranteed)" % condition)
            row = dict(choice)
            row.update({
                "_qa_choice_id": "%s:%s" % (event.get("id"), index),
                "option": option,
                "condition": condition,
                "_blocked": blocked,
                "_blocked_reason": choice.get("blocked_message") or (
                    "No assigned worker can attempt this check." if condition
                    else "Locked: trait requirement not met."
                ),
            })
            rows.append(row)
        return rows

    def qa_choice_rects(screen_name):
        """Every button's absolute rectangle, from the render tree the engine
        just blitted. Focus rectangles are NOT enough: an insensitive (locked)
        button registers no focus area, and the locked rows are exactly the ones
        that used to be displaced on top of the others."""
        displayable = renpy.get_screen(screen_name)
        if displayable is None:
            return []
        Button = renpy.display.behavior.Button
        Render = renpy.display.render.Render
        root = renpy.display.render.render(
            displayable, config.screen_width, config.screen_height, 0, 0)
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
                    # subsurface removes off-screen buttons. Measure the engine's
                    # uncropped child at the viewport's actual render origin.
                    surface = renpy.display.render.render(vp.child, vp.child_width or vp.width, vp.child_height or vp.height, 0, 0)
                    walk(surface, x - int(vp.xadjustment.value), y - int(vp.yadjustment.value))
                    continue
                if any(isinstance(d, Button) for d in (child.render_of or [])):
                    rows.append((int(x), int(y), int(child.width), int(child.height)))
                    continue  # a button's own children are its label, not options
                walk(child, x, y)

        walk(root, 0, 0)
        # Traversal order is blit order is authored order: do NOT sort, or the
        # "options came out in the wrong order" check silently passes.
        return rows

    def qa_choice_problems(rects, expected):
        """rects are in AUTHORED order; a correct list runs strictly downwards."""
        problems = []
        if len(rects) != expected:
            problems.append("expected %d options drawn, engine drew %d" % (expected, len(rects)))
        for index in range(1, len(rects)):
            if rects[index][1] <= rects[index - 1][1]:
                problems.append("option %d (y=%d) is not below option %d (y=%d): authored order broken"
                                % (index + 1, rects[index][1], index, rects[index - 1][1]))
        ordered = sorted(range(len(rects)), key=lambda i: rects[i][1])
        for first, second in zip(ordered, ordered[1:]):
            ax, ay, aw, ah = rects[first]
            bx, by, bw, bh = rects[second]
            if by < ay + ah and bx < ax + aw and ax < bx + bw:
                problems.append("option %d (y=%d..%d) overlaps option %d (y=%d..%d)"
                                % (first + 1, ay, ay + ah, second + 1, by, by + bh))
        for index, (x, y, w, h) in enumerate(rects):
            if x < 0 or y < 0 or x + w > config.screen_width or y + h > config.screen_height:
                problems.append("option %d is off screen: (%d, %d, %d, %d)" % (index + 1, x, y, w, h))
        return problems

    def qa_choice_sweep():
        persistent.nsfw_enabled = True
        store.at_main_menu = False
        store.tutorial_active = False
        catalogue = [e for e in load_events_from_folder("data/events") if e.get("choices")]
        limit = int(_qa_os.environ.get("FM_QA_CHOICE_LIMIT", "0") or 0)
        if limit:
            # A short run is only meaningful on events that CAN lock an option:
            # the locked rows are the ones the layout defect displaced.
            catalogue = [e for e in catalogue
                         if any(r["_blocked"] for r in qa_choice_prepared(e, "all"))][:limit]
        qa_choice_note("catalogue: %d events with choices" % len(catalogue))
        results = []
        failures = 0

        mode = _qa_os.environ.get("FM_QA_CHOICE_MODE", "all")
        layout_catalogue = catalogue if mode != "clicks" else []
        for event in layout_catalogue:
            for variant in ("none", "all", "alternate", "preview", "preview_locked"):
                rows = qa_choice_prepared(event, variant)
                if not rows:
                    continue
                renpy.show_screen("random_event_choice", event_choices=rows)
                renpy.pause(0.05, hard=True, modal=False)
                rects = qa_choice_rects("random_event_choice")
                everything_locked = all(r["_blocked"] for r in rows)
                problems = qa_choice_problems(rects, len(rows) + (1 if everything_locked else 0))
                if problems:
                    failures += 1
                    renpy.screenshot(qa_choice_out("fail_%s_%s.png" % (event["id"], variant)))
                    qa_choice_note("FAIL %s/%s %r" % (event["id"], variant, problems))
                elif event["id"] == "rescue_shop_owner_debt" and variant == "preview_locked":
                    renpy.screenshot(qa_choice_out("sample_rescue.png"))
                elif not results:
                    renpy.screenshot(qa_choice_out("sample_first_case.png"))
                renpy.hide_screen("random_event_choice")
                results.append({
                    "screen": "random_event_choice", "event": event["id"], "variant": variant,
                    "options": len(rows), "locked": len([r for r in rows if r["_blocked"]]),
                    "rects": rects, "problems": problems,
                })
                if len(results) % 100 == 0:
                    qa_choice_note("%d cases done, %d failures" % (len(results), failures))

        store.current_recruitment_event = {}
        store.current_recruitment_worker = None
        for event in layout_catalogue:
            rows = qa_choice_prepared(event, "none")
            if not rows:
                continue
            renpy.show_screen("recruitment_choice_screen", event_choices=rows)
            renpy.pause(0.05, hard=True, modal=False)
            rects = qa_choice_rects("recruitment_choice_screen")
            problems = qa_choice_problems(rects, len(rows) + 1)  # + "*Examine Worker*"
            if problems:
                failures += 1
                renpy.screenshot(qa_choice_out("fail_recruit_%s.png" % event["id"]))
                qa_choice_note("FAIL recruit %s %r" % (event["id"], problems))
            renpy.hide_screen("recruitment_choice_screen")
            results.append({
                "screen": "recruitment_choice_screen", "event": event["id"], "variant": "none",
                "options": len(rows), "locked": 0, "rects": rects, "problems": problems,
            })

        if mode != "layout":
            results.extend(qa_choice_click_sweep(catalogue))
        if mode != "layout" and not _qa_os.environ.get("FM_QA_CHOICE_FAULT"):
            results.extend(qa_choice_save_cases())
        failures = sum(bool(row["problems"]) for row in results)
        qa_choice_note("DONE %d cases, %d failures" % (len(results), failures))
        with open(qa_choice_out("report.json"), "w", encoding="utf-8") as handle:
            _qa_json.dump({"engine": renpy.version(), "variants": config.variants, "choice_width": gui.choice_button_width, "cases": len(results), "failures": failures, "results": results}, handle, indent=1)


    def qa_choice_post_mouse(x, y, phase, held=False):
        # The SDK's test mouse feeds real SDL events and keeps the virtual pointer
        # coherent on timer/redraw events during a grab, without moving the user's
        # OS pointer. Plain posted events alone snap a drag back to the OS pointer.
        mouse = renpy.test.testmouse
        mouse.move_mouse(int(x), int(y))
        if phase == 1:
            mouse.press_mouse(1)
        elif phase == 2:
            mouse.release_mouse(1)

    def qa_choice_click_tick():
        plan = renpy.session.get("qa_choice_plan")
        if not plan:
            return
        if plan.get("flow"):
            active = "choose_event_worker_screen" if renpy.get_screen("choose_event_worker_screen") else "random_event_choice"
            if not renpy.get_screen(active):
                renpy.queue_event("dismiss")
                return
            if active != plan["screen"]:
                plan["screen"] = active
                plan["phase"] = 0
                plan["targets"] = [len(qa_choice_rects(active)) - 1]
                plan["worker_cancelled"] = True
        screen_name = plan["screen"]
        if plan.get("examined") and not renpy.get_screen("worker_details") and not plan.get("back"):
            plan["back"] = True
            plan["targets"] = [0]
            plan["phase"] = 0
        if plan.get("examine") and renpy.get_screen("worker_details"):
            plan["examined"] = True
            rects = qa_choice_rects("worker_details")
            # worker_details declares its return imagebutton before all other buttons.
            target = 0
        else:
            rects = qa_choice_rects(screen_name)
            target = plan["targets"][0] if plan["targets"] else None
        if target is None or target >= len(rects):
            return
        x, y, w, h = rects[target]
        if plan.get("settle", 0):
            plan["settle"] -= 1
            return
        if plan.get("scroll") and (plan.get("drag_phase") is not None or not (40 <= y and y + h <= config.screen_height - 40)):
            if renpy.variant("touch"):
                moves = ((0, 860), (1, 860), (0, 700), (0, 520), (0, 350), (2, 350))
                phase_index = plan.get("drag_phase") or 0
                drag_action, drag_y = moves[phase_index]
                if _qa_os.environ.get("FM_QA_CHOICE_DEBUG_DRAG"):
                    vp = renpy.get_displayable(screen_name, "event_choices_viewport")
                    qa_choice_note("DRAG %s value=%s range=%s drag=%s draggable=%s grab=%s" % (phase_index, vp.yadjustment.value, vp.yadjustment.range, vp.drag_position, vp.draggable, type(renpy.display.focus.get_grab()).__name__))
                qa_choice_post_mouse(config.screen_width // 2, drag_y, drag_action, held=phase_index > 1)
                plan["drag_phase"] = phase_index + 1 if phase_index + 1 < len(moves) else None
                if plan["drag_phase"] is None:
                    plan["settle"] = 12
                plan["scrolled"] = True
                return
            # Dispatch wheel input at the actual viewport, through the same
            # virtual-pointer path as clicks and touch drags.
            renpy.test.testmouse.move_mouse(config.screen_width // 2, config.screen_height // 2)
            button = 5 if y + h > config.screen_height - 40 else 4
            renpy.test.testmouse.press_mouse(button)
            renpy.test.testmouse.release_mouse(button)
            plan["scrolled"] = True
            return
        phase = plan["phase"]
        if phase < 3:
            qa_choice_post_mouse(x + w // 2, y + h // 2, phase)
        else:
            # Reaching another interaction after a blocked click proves it did
            # not execute Return. Then choose the specified live row/escape.
            if plan.get("examine") and plan.get("examined"):
                pass
            elif len(plan["targets"]) > 1:
                plan["blocked_held"] = True
                plan["targets"].pop(0)
            else:
                return
        plan["phase"] = (phase + 1) % 4

    def qa_choice_click_case(screen_name, rows, target, blocked=None, scroll=False, examine=False):
        qa_choice_note("CLICK %s target=%s blocked=%s scroll=%s examine=%s" % (screen_name, target, blocked, scroll, examine))
        plan = {"screen": screen_name, "targets": ([blocked] if blocked is not None else []) + [target],
                "phase": 0, "scroll": scroll, "examine": examine}
        renpy.session["qa_choice_plan"] = plan
        renpy.show_screen("qa_choice_driver")
        try:
            if screen_name == "choose_event_worker_screen":
                result = renpy.call_screen(screen_name, eligible_workers=rows)
            else:
                result = renpy.call_screen(screen_name, event_choices=rows)
        finally:
            renpy.hide_screen("qa_choice_driver")
            renpy.hide_screen("worker_details")
            renpy.session.pop("qa_choice_plan", None)
            renpy.test.testmouse.reset()
        expected = rows[target] if target < len(rows) else False
        if screen_name == "recruitment_choice_screen" and not rows and not examine:
            expected = {"_dismiss_recruitment": True}
        problems = []
        if examine:
            if not plan.get("examined") or not plan.get("back") or result != rows[0]:
                problems.append("Examine/back failed: %r / %r" % (plan, result))
        elif result != expected:
            problems.append("coordinate click returned %r; expected %r" % (result, expected))
        if blocked is not None and not plan.get("blocked_held"):
            problems.append("blocked option accepted a click")
        if scroll and not plan.get("scrolled"):
            problems.append("oversized list was not reached by scrolling")
        qa_choice_note("RESULT %r" % problems)
        return problems

    def qa_choice_click_sweep(catalogue):
        results = []
        for event in catalogue:
            gates = qa_choice_prepared(event, "all")
            if not any(row["_blocked"] for row in gates):
                continue
            # Both parities: every authored row is actually selected when live,
            # and every gate is clicked when locked (including odd-only gates).
            for parity in (0, 1):
                rows = qa_choice_prepared(event, "none")
                for i, row in enumerate(rows):
                    row["_blocked"] = gates[i]["_blocked"] and i % 2 == parity
                locked = [i for i, row in enumerate(rows) if row["_blocked"]]
                live = [i for i, row in enumerate(rows) if not row["_blocked"]] or [len(rows)]
                for index in live:
                    problems = qa_choice_click_case("random_event_choice", rows, index)
                    results.append({"screen": "random_event_choice", "event": event["id"], "variant": "click-%s-%s" % (parity, index), "problems": problems})
                for index in locked:
                    problems = qa_choice_click_case("random_event_choice", rows, live[0], blocked=index)
                    results.append({"screen": "random_event_choice", "event": event["id"], "variant": "locked-click-%s-%s" % (parity, index), "problems": problems})
        for name, rows, target, scroll in (
            ("empty", [], 0, False),
            ("all-locked", [{"option": "Locked", "_blocked": True, "_blocked_reason": "Requires a worker."}], 1, False),
            ("literal-tags", [{"option": "Literal [unknown_variable] {broken tag}", "_qa_choice_id": "literal"}], 0, False),
            ("long-locked-list", [{"option": "Locked option %d" % i, "_blocked": True, "_blocked_reason": "A detailed explanation of the missing requirement. " * 10} for i in range(8)], 8, True),
            ("long-list", [{"option": "Option %d: %s" % (i, "An additional detail in a long event choice. " * 4), "_qa_choice_id": i} for i in range(16)], 15, True),
        ):
            problems = qa_choice_click_case("random_event_choice", rows, target, scroll=scroll)
            results.append({"screen": "random_event_choice", "event": name, "variant": "edge-click", "problems": problems})
        store.current_recruitment_event = {"id": "qa_recruitment", "choices": [{"option": "Hire"}]}
        store.current_recruitment_worker = None
        problems = qa_choice_click_case("recruitment_choice_screen", [], 0)
        results.append({"screen": "recruitment_choice_screen", "event": "empty-recruitment", "variant": "edge-click", "problems": problems})
        worker = {"name": "QA Visitor", "gender": "female", "level": 1, "skills": {"Charm": 60}, "traits": [], "comfort_desired": 2}
        ensure_worker_defaults(worker)
        store.current_recruitment_worker = prepare_recruitment_worker({"random_worker": False}, worker)
        rows = [{"option": "Hire QA Visitor", "effect": {"recruit_worker": True}}, {"option": "Decline", "effect": {}}]
        for target in range(len(rows)):
            problems = qa_choice_click_case("recruitment_choice_screen", rows, target)
            results.append({"screen": "recruitment_choice_screen", "event": "real-worker", "variant": "click-%s" % target, "problems": problems})
        problems = qa_choice_click_case("recruitment_choice_screen", rows, len(rows), examine=True)
        results.append({"screen": "recruitment_choice_screen", "event": "real-worker", "variant": "examine-back", "problems": problems})
        for workers, target in (([], 0), ([], 1), ([store.current_recruitment_worker], 1)):
            problems = qa_choice_click_case("choose_event_worker_screen", workers, target)
            results.append({"screen": "choose_event_worker_screen", "event": "worker-cancel", "variant": "empty-%s-target-%s" % (not workers, target), "problems": problems})
        if _qa_os.environ.get("FM_QA_CHOICE_FAULT"):
            return results
        results.extend(qa_choice_flow_cases())
        results.extend(qa_recruitment_resolution_cases())
        return results

    def qa_choice_flow_cases():
        results = []
        for name, option, mode, worker, target in (
            ("locked", {"option": "Requires an absent trait", "required_trait": "QA Missing Trait", "trait_visibility": "blocked", "effect": {"money": 700}}, "none", None, 1),
            ("empty", {"option": "", "effect": {"money": 700}}, "none", None, 0),
            ("resolved", {"option": "Accept the offer.", "effect": {"money": 17}, "message": "Offer accepted."}, "none", None, 0),
            ("decline-authored", {"option": "Decline the offer.", "effect": {}, "message": "You decline."}, "none", None, 0),
        ):
            event_id = "qa_flow_" + name
            event = {"id": event_id, "description": "A visitor brings an offer.", "arc_id": "qa_flow", "arc_stage": 1,
                     "completion_timestamp_flag": event_id + "_done", "worker_selection": mode, "no_dialogue": True,
                     "choices": [option], "background_image": "event_bg"}
            store.current_event = event
            store.current_worker = worker
            store.event_flags.pop(event_id + "_done", None)
            before_money = store.money
            day = calculate_total_days()
            plan = {"screen": "random_event_choice", "targets": [target], "phase": 0, "flow": True}
            renpy.session["qa_choice_plan"] = plan
            qa_choice_note("FLOW " + name)
            renpy.call_in_new_context("qa_choice_flow_entry")
            renpy.session.pop("qa_choice_plan", None)
            problems = []
            cancelled = name in ("locked", "empty")
            if cancelled:
                if event_id + "_done" in store.event_flags or not store.event_flags.get(event_id + "_passed"):
                    problems.append("cancelled event stamped completion or lost pass cooldown")
                if store.money != before_money:
                    problems.append("cancelled event applied money effects")
            else:
                if store.event_flags.get(event_id + "_done") != day:
                    problems.append("resolved event did not stamp completion")
                expected = before_money + (17 if name == "resolved" else 0)
                if store.money != expected:
                    problems.append("resolved event applied the wrong money delta")
            if store.current_worker is not None or store.chosen_choice_data is not None:
                problems.append("event leaked selected worker/choice context")
            results.append({"screen": "handle_random_event", "event": event_id, "variant": "production-flow", "problems": problems})
        return results

    def qa_recruitment_resolution_cases():
        import copy
        results = []
        store.in_recruitment = True
        store.tutorial_active = False
        catalogue = [e for e in load_events_from_folder("data/events/recruit") if e.get("choices")]
        for event in catalogue:
            for index, choice in enumerate(event["choices"]):
                for roll in ("low", "high"):
                    original = {"name": "QA Recruit %s %s" % (event["id"], index), "gender": "female", "level": 1,
                                "skills": {"Charm": 60}, "traits": [], "comfort_desired": 3, "nsfw": False}
                    ensure_worker_defaults(original)
                    worker = prepare_recruitment_worker(event, original)
                    template_before = copy.deepcopy(original)
                    store.workers = []
                    store.available_workers = []
                    before = store.money
                    old_random = random.random
                    try:
                        random.random = qa_roll_low if roll == "low" else qa_roll_high
                        result = process_recruitment_choice(copy.deepcopy(choice), event, worker)
                    finally:
                        random.random = old_random
                    effect = choice.get("effect", {})
                    if "success_chance" in effect and ("success" in effect or "failure" in effect):
                        effect = effect.get("success" if roll == "low" else "failure", {})
                    should_hire = bool(effect.get("recruit_worker"))
                    problems = []
                    if len(store.workers) != int(should_hire):
                        problems.append("wrong roster result")
                    if store.money != before + int(effect.get("money", 0)):
                        problems.append("wrong recruitment money delta")
                    if should_hire:
                        if worker["daily_cost"] != worker["comfort_level"] * get_difficulty_comfort_mult():
                            problems.append("daily cost differs from comfort times difficulty")
                        if worker["assigned_building"] != "Unassigned":
                            problems.append("recruit was unexpectedly assigned")
                    if original != template_before:
                        problems.append("recruitment mutated its original worker template")
                    if not result.get("message") or "[COST]" in result["message"] or "[event_worker]" in result["message"]:
                        problems.append("unresolved recruitment message")
                    results.append({"screen": "process_recruitment_choice", "event": event["id"], "variant": "%s-%s" % (index, roll), "problems": problems})
        # A stale hire callback must not award reputation/money a second time.
        worker = store.workers[0] if store.workers else {"name": "QA Already Hired", "traits": [], "skills": {}}
        store.workers = [worker]
        before_money = store.money
        building, _key = _resolve_building_by_name("Building 1")
        before_rep = building.get("reputation", 0) if building else None
        result = apply_recruitment_effects({"recruit_worker": True, "money": 50, "reputation": 5}, worker)
        problems = []
        if store.money != before_money or (building and building.get("reputation", 0) != before_rep) or len(store.workers) != 1:
            problems.append("duplicate hire applied effects before rejecting the worker")
        results.append({"screen": "apply_recruitment_effects", "event": "duplicate-hire", "variant": "stale-callback", "problems": problems})
        store.in_recruitment = False
        return results

    def qa_choice_save_cases():
        results = []
        set_save_blocked_context(None)
        for slot in (96, 97):
            before = _native_save_commit_marker(_get_current_slot_name(slot))
            SnapshotFileSave(slot)()
            after = _native_save_commit_marker(_get_current_slot_name(slot))
            problems = []
            if not after[0] or not after[1] or after == before or after[1] == before[1]:
                problems.append("native save did not commit fresh bytes after event/recruitment UI")
            results.append({"screen": "SnapshotFileSave", "event": "after-event-%s" % slot, "variant": "native-save", "problems": problems})
        problems = []
        poison = open(qa_choice_out("progress.txt"), "rb")
        poison.close()
        store.qa_choice_poison = poison
        try:
            renpy.python.store_dicts["store"].get_changes(True, None)
            if renpy.game.log.get_roots().get("store.qa_choice_poison") is not poison:
                problems.append("negative control never entered native save roots")
            rejected = False
            try:
                renpy.save("qa-event-negative-control")
            except Exception as exc:
                rejected = "BufferedReader" in str(exc) or "pickle" in str(exc).lower()
            if not rejected:
                problems.append("real native serializer accepted a file handle")
        finally:
            store.qa_choice_poison = None
        results.append({"screen": "renpy.save", "event": "file-handle-control", "variant": "native-save-negative", "problems": problems})
        return results

    def qa_roll_low():
        return 0.0

    def qa_roll_high():
        return 0.999999

label qa_choice_flow_entry:
    show screen qa_choice_driver
    call handle_random_event
    hide screen qa_choice_driver
    return

screen qa_choice_driver():
    zorder 1000
    timer 0.04 repeat True action Function(qa_choice_click_tick, _update_screens=False)
    timer 25.0 action Return("QA_TIMEOUT")


label splashscreen:
    if not _qa_os.environ.get("FM_QA_CHOICE_LAYOUT"):
        return
    $ store.main_menu = False
    $ qa_choice_sweep()
    $ renpy.quit(status=0)
