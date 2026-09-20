# No new snapshot keys: this entire record travels in the existing event_flags
# build/apply/after-load paths. No dead character is reconstructed from a template.
init python:
    import fm_lifecycle.rules as _life_rules

    def church_life_state():
        return _life_rules.read_state(getattr(store, "event_flags", {}), getattr(store, "dead_worker_names", []) or [])

    def church_life_commit(state):
        if not hasattr(getattr(store, "event_flags", None), "get"):
            store.event_flags = {}
        store.event_flags[_life_rules.STATE_KEY] = state
        # Compatibility alias for older scripts. The snapshot record above is
        # authoritative, so stale native roots cannot override a restored record.
        store.dead_worker_names = [row["name"] for row in state["dead"]]

    def church_dead_names():
        return [row["name"] for row in church_life_state()["dead"]]

    def church_worker_is_dead(worker):
        return _life_rules.is_dead(church_life_state(), worker)

    def church_record_legacy_death_name(name):
        if name and not church_worker_is_dead(name):
            state, grave, status = _life_rules.remember_death(church_life_state(), {"name": name}, calculate_total_days(), "Legacy death record", capacity=0)
            church_life_commit(state)

    def church_clear_worker_assignment(worker):
        name = worker.get("name")
        for building in (getattr(store, "available_buildings", {}) or {}).values():
            if not hasattr(building, "get"):
                continue
            _remove_worker_from_building_by_name(building, name)
            for field in ("servant_jobs", "training_focus"):
                values = building.get(field)
                if hasattr(values, "pop"):
                    values.pop(name, None)
        worker["assigned_building"] = "Unassigned"
        clear_worker_autorest_state(worker)
        for field in ("batch_selected_worker_names", "batch_allowed_worker_names"):
            values = getattr(store, field, None)
            if values is not None:
                setattr(store, field, [value for value in values if value != name])

    def record_worker_death(worker, cause="Daily work"):
        if not hasattr(worker, "get") or not worker.get("name"):
            return False
        # Only an owned, live instance can die. Repeated/stale event callbacks
        # must not duplicate a grave or erase a newly resurrected character.
        if not any(current is worker for current in (getattr(store, "workers", []) or [])):
            return False
        state, grave, status = _life_rules.remember_death(church_life_state(), worker, calculate_total_days(), cause)
        if status == "already_recorded":
            return False
        church_clear_worker_assignment(worker)
        store.workers[:] = [current for current in store.workers if current is not worker]
        for field in ("available_workers", "displayed_workers"):
            values = getattr(store, field, None)
            if values is not None:
                setattr(store, field, [current for current in values if not _life_rules.is_dead(state, current)])
        church_life_commit(state)
        if status == "full":
            renpy.notify(worker["name"] + " died. The cemetery is full; this death cannot be resurrected.")
        else:
            renpy.notify(worker["name"] + " died and was laid to rest at the church (" + str(len(state["graves"])) + "/10).")
        renpy.log("DEATH: " + worker["name"] + "; " + str(cause) + "; " + status)
        return True

    def church_exploration():
        return _life_rules.pilgrimage_state(church_life_state())

    def church_can_explore():
        return _life_rules.can_explore(church_life_state(), calculate_total_days())

    def church_discover_seal(stage):
        state, result = _life_rules.discover_seal(church_life_state(), stage, calculate_total_days())
        if result == "found":
            church_life_commit(state)
        return result

    def church_ritual_ready():
        return church_life_state()["unlocked"] or church_exploration()["stage"] >= 4

    def church_is_night():
        return church_exploration().get("night_day") == calculate_total_days()

    def church_place_seal(seal):
        state, result = _life_rules.place_seal(church_life_state(), seal)
        church_life_commit(state)
        return result

    def church_grave(grave_id):
        return _life_rules.grave_by_id(church_life_state(), grave_id)

    def church_resurrection_price(grave_id):
        grave = church_grave(grave_id)
        return _life_rules.resurrection_price(grave) if grave else 0

    def church_cemetery_choices(page=0):
        # Reuse the game's normal dialogue choice screen; three graves per
        # page leave room for navigation even with the large-font preference.
        graves = church_life_state()["graves"]
        start = max(0, int(page)) * 3
        choices = [(str(row["name"]).replace("[", "[[").replace("{", "{{") + " — " + str(row["cause"]).replace("[", "[[").replace("{", "{{"), ("grave", row["id"])) for row in graves[start:start + 3]]
        if start + 3 < len(graves):
            choices.append(("Next graves.", ("page", page + 1)))
        if start > 0:
            choices.append(("Previous graves.", ("page", page - 1)))
        choices.append(("Return to the priestess.", ("leave", 0)))
        return choices

    def church_resurrect(grave_id):
        state, worker, cost, result = _life_rules.prepare_resurrection(church_life_state(), grave_id, store.workers, store.money)
        if result != "ok":
            return result
        # Preserve inventory, progression and ownership. Only duty/recovery
        # state changes; never recruit from JSON or reroll a replacement.
        ensure_worker_defaults(worker)
        clear_worker_autorest_state(worker)
        worker["health"] = calculate_max_health(worker)
        worker["energy"] = 0
        church_clear_worker_assignment(worker)
        store.workers.append(worker)
        store.money -= cost
        church_life_commit(state)
        renpy.notify(worker["name"] + " has returned to your roster. -" + str(cost) + " coins.")
        return "ok"

    def church_release_grave(grave_id):
        state, released = _life_rules.release_grave(church_life_state(), grave_id)
        if released:
            church_life_commit(state)
        return released
