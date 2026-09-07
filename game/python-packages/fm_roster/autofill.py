"""Pure auto-fill planner.

Given a building's professions (in fill order, each with its free-slot count and
skill list) and a pool of candidate workers, decide who fills what. Scoring is
delegated to `skill_fn(worker, skill_name)` so the caller injects the real
`calculate_skill_with_traits` while tests inject a simple stub.

Greedy by design: professions are filled in the given order; each slot takes the
highest-scoring remaining candidate (ties broken by case-insensitive name). A
candidate is consumed once and never assigned twice. The caller is responsible
for excluding Manager/Rest/locked professions and for building the candidate
pool before calling.
"""


def capped_free_slots(capacity_free, holders, quota):
    """Clamp a profession's fillable slot count by an optional target headcount.

    `quota` is the desired TOTAL headcount for the job (None or invalid = no
    plan, fill to capacity). Returns how many workers auto-fill may still add:
    min(capacity_free, quota - holders), never negative.
    """
    try:
        target = int(quota)
    except (TypeError, ValueError):
        return capacity_free
    if target < 0:
        target = 0
    return max(0, min(capacity_free, target - holders))


def _score(worker, skills, skill_fn):
    total = 0.0
    for skill_name in skills or []:
        try:
            total += float(skill_fn(worker, skill_name) or 0)
        except (TypeError, ValueError):
            pass
    return total


def _name_key(worker):
    return str(worker.get("name", "")).strip().lower()


def reoptimization_candidates(workers, target_building, servant_jobs, resolve_building):
    """Return workers Auto-fill may optimize for one building.

    Includes globally unassigned workers plus everyone already assigned to the
    target building, regardless of whether they currently have a normal job.
    Manager/Rest reservations are protected, and workers in other buildings are
    never moved.
    """
    jobs = servant_jobs if hasattr(servant_jobs, "get") else {}
    candidates = []
    for worker in workers or []:
        if not hasattr(worker, "get"):
            continue
        assigned = resolve_building(worker.get("assigned_building"))
        if assigned is None:
            candidates.append(worker)
            continue
        if assigned != target_building:
            continue
        job_id = str(jobs.get(worker.get("name"), "") or "").strip().lower()
        if job_id in ("manager", "rest"):
            continue
        candidates.append(worker)
    return candidates


def plan_trim(candidates, skills, excess, skill_fn):
    """Pick which workers to unassign when a job exceeds its plan target.

    Ranks by the job's relevant skills (same scoring as the fill) and returns
    the names of the `excess` LOWEST-scoring workers (ties broken by name), so
    trimming always keeps the best staff in place.
    """
    try:
        excess = int(excess)
    except (TypeError, ValueError):
        return []
    if excess <= 0:
        return []
    ranked = sorted(
        [w for w in (candidates or []) if hasattr(w, "get")],
        key=lambda w: (_score(w, skills, skill_fn), _name_key(w)),
    )
    return [w.get("name") for w in ranked[:excess]]


def plan_autofill(professions, candidates, skill_fn):
    """Return {"assignments": [{"worker", "job_id"}...], "empty_slots": {job_id: n}}.

    `professions`: iterable of dicts with keys job_id, skills, free_slots.
    `candidates`: iterable of worker dicts eligible for assignment/reassignment.
    `skill_fn`: callable(worker, skill_name) -> number.
    """
    remaining = list(candidates)
    assignments = []
    empty_slots = {}

    for prof in professions:
        job_id = prof.get("job_id")
        skills = prof.get("skills", []) or []
        free = int(prof.get("free_slots", 0) or 0)
        filled = 0
        while filled < free and remaining:
            # Highest score first; ties -> alphabetically-first name. Sorting a
            # fresh scored list each slot keeps the choice stable as the pool
            # shrinks.
            best = min(
                remaining,
                key=lambda w: (-_score(w, skills, skill_fn), _name_key(w)),
            )
            remaining.remove(best)
            assignments.append({"worker": best.get("name"), "job_id": job_id})
            filled += 1
        empty_slots[job_id] = free - filled

    return {"assignments": assignments, "empty_slots": empty_slots}
