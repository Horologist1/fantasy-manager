# legacy_progress.rpy — heal progression gates that older versions recorded
# differently. Saves travel across many builds and a load applies the JSON
# snapshot onto a clean store, so any gate whose "proof" lives in another
# field must be re-derived here. Rules only turn things ON: loading never
# takes progress away. Called from _apply_snapshot after buildings, workers
# and flags are in place.

init python:
    def reconcile_legacy_progress_on_load():
        """Return the list of fields healed (empty when nothing changed)."""
        healed = []
        buildings = getattr(store, "available_buildings", None)
        if not hasattr(buildings, "get"):
            buildings = {}
        owned = getattr(store, "owned_buildings", None) or []

        # Academy: owning the building IS enrolment. With the flag lost, the
        # map shows "enroll to unlock", the tuition menu takes the money and
        # add_academy_building() returns early, so paying buys nothing.
        if "Academy" in buildings and not getattr(store, "academy_enrolled", False):
            store.academy_enrolled = True
            healed.append("academy_enrolled")

        # Arena: an owned Arena proves the permit was paid. Otherwise the
        # Lanista sells the permit again and paying it re-locks Arena
        # operations behind a fresh opening trial.
        arena = buildings.get("Arena")
        arena_owned = "Arena" in owned or (hasattr(arena, "get") and bool(arena.get("owned", False)))
        if arena_owned:
            if not getattr(store, "arena_unlocked", False):
                store.arena_unlocked = True
                healed.append("arena_unlocked")
            if not getattr(store, "arena_lanista_paid", False):
                store.arena_lanista_paid = True
                healed.append("arena_lanista_paid")

        # Yvara S4: the ledger talk (s4_t1) is what unlocks the finance track.
        # A save that played the talk without the flag can never finish S4.
        talks = getattr(store, "yvara_s4_talks_done", None) or ()
        if "s4_t1" in talks and not getattr(store, "yvara_s4_finance_unlocked", False):
            store.yvara_s4_finance_unlocked = True
            healed.append("yvara_s4_finance_unlocked")

        # Lanista identity for saves that predate the choice: same rule as
        # lanista_visit, applied on load so the unique Arena recruit (gated
        # on lanista_gender) can appear before the next visit.
        legacy_progress = getattr(store, "lanista_has_legacy_progress", None)
        if not getattr(store, "lanista_gender", "") and callable(legacy_progress):
            try:
                if legacy_progress():
                    store.lanista_gender = "male"
                    store.lanista_name = "Varro"
                    store.lanista_known_name = True
                    healed.append("lanista_gender")
            except Exception as e:
                renpy.log("LEGACY PROGRESS: lanista identity inference failed: %s" % e)

        # Tutorial objectives: being on objective N proves 1..N-1 were done.
        # A sidecar written before a later objective flag existed strands the
        # journal (is_previous_objective_complete) once the False is re-saved.
        try:
            current = int(getattr(store, "current_objective", 0) or 0)
        except (TypeError, ValueError):
            current = 0
        for number in range(1, min(current, 17)):
            flag = "objective_%d_complete" % number
            if not getattr(store, flag, False):
                setattr(store, flag, True)
                healed.append(flag)

        if healed:
            renpy.log("LEGACY PROGRESS: healed on load: %s" % ", ".join(healed))
        return healed
