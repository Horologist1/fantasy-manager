"""Pure assignment-preset logic: normalize a captured layout and plan its reapply.

`normalize_preset` filters a raw capture down to real job assignments (drops
unassigned/rest/empty and de-dupes by worker). `plan_apply` decides, entry by
entry, what to assign vs skip, reporting a reason for each skip. All game access
(name presence, building-key resolution, capacity, current placement) is injected
so the planner stays pure and exhaustively testable.

Skip reasons: 'missing_worker', 'unknown_building', 'unknown_job', 'overflow'.
`capacity_of(building, job)` returns an int (free slots) for a valid slot, or
None when the job is not a valid profession slot in that building.

Known v1 limitation: capacity is read from the current static state, so a preset
that both frees and refills the same full slot may over-report overflow. It never
over-assigns (safe by construction).
"""

_NON_JOBS = {"", "unassigned", "rest"}


def normalize_preset(raw_entries):
    """Clean a raw [{worker, building, job}] capture into storable preset entries."""
    out = []
    seen = set()
    for entry in raw_entries or []:
        if not hasattr(entry, "get"):
            continue
        worker = str(entry.get("worker", "") or "").strip()
        building = str(entry.get("building", "") or "").strip()
        job = str(entry.get("job", "") or "").strip().lower()
        if not worker or not building or job in _NON_JOBS:
            continue
        if worker in seen:
            continue
        seen.add(worker)
        out.append({"worker": worker, "building": building, "job": job})
    return out


def plan_apply(entries, present_workers, resolve_building, capacity_of, current_of):
    """Plan a preset reapply.

    Returns {"assignments": [{worker, building, job}...],
             "unchanged": [worker...],
             "skipped": [{worker, reason, [building], [job]}...]}
    with assignments in entry order. `building` in assignments is the RESOLVED key.
    """
    present = set(present_workers or [])
    assignments = []
    unchanged = []
    skipped = []
    free_cache = {}

    for entry in entries or []:
        worker = entry.get("worker")
        raw_building = entry.get("building")
        job = entry.get("job")

        if worker not in present:
            skipped.append({"worker": worker, "reason": "missing_worker"})
            continue

        resolved = resolve_building(raw_building)
        if not resolved:
            skipped.append(
                {"worker": worker, "reason": "unknown_building", "building": raw_building}
            )
            continue

        target = (resolved, job)

        if current_of(worker) == target:
            unchanged.append(worker)
            continue

        if target not in free_cache:
            free_cache[target] = capacity_of(resolved, job)
        cap = free_cache[target]
        if cap is None:
            # The job is not a valid slot in this building (renamed/removed
            # profession) — distinct from a real slot that is merely full.
            skipped.append(
                {"worker": worker, "reason": "unknown_job", "building": resolved, "job": job}
            )
            continue
        if cap <= 0:
            skipped.append(
                {"worker": worker, "reason": "overflow", "building": resolved, "job": job}
            )
            continue

        free_cache[target] = cap - 1
        assignments.append({"worker": worker, "building": resolved, "job": job})

    return {"assignments": assignments, "unchanged": unchanged, "skipped": skipped}
