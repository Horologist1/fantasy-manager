"""Pure auto-fill planner.

Given a building's professions (in fill order, each with its free-slot count and
skill list) and a pool of candidate workers, decide who fills what. Scoring is
delegated to `skill_fn(worker, skill_name)` so the caller injects the real
`calculate_skill_with_traits` while tests inject a simple stub.

The original priority order determines how many slots each profession receives.
Within those quotas, compare the original greedy allocation with a scarcity-first
allocation, then improve the team by bounded exchanges. This is a heuristic, not
a guarantee of the global optimum. A candidate is never assigned twice. The caller is responsible
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
    workers = list(candidates)
    roles = list(professions)
    # Cache effective skill averages: a three-skill role must not count triple
    # when comparing its contribution with a one-skill role.
    scores = [[_score(w, p.get("skills", []), lambda worker, skill: max(0, skill_fn(worker, skill) + p.get("skill_adjustments", {}).get(skill, 0))) /
               max(1, len(p.get("skills", []) or []))
               if int(p.get("free_slots", 0) or 0) > 0 else 0.0
               for p in roles] + [0.0] for w in workers]
    bench = len(roles)
    ranked = [sorted(range(len(workers)),
                     key=lambda i: (-scores[i][r], _name_key(workers[i])))
              for r in range(len(roles))]
    original = [bench] * len(workers)
    counts, empty = [], {}
    for r, p in enumerate(roles):
        free = max(0, int(p.get("free_slots", 0) or 0))
        chosen = [i for i in ranked[r] if original[i] == bench][:free]
        for i in chosen:
            original[i] = r
        counts.append(len(chosen))
        empty[p.get("job_id")] = free - len(chosen)

    def value(allocation):
        return sum(scores[i][r] for i, r in enumerate(allocation))

    # Fill the role with the largest loss if its best remaining candidate is
    # used elsewhere. Keep original headcounts, including when understaffed.
    scarce = [bench] * len(workers)
    left = list(counts)
    cursors = [0] * len(roles)
    while any(left):
        options = []
        for r, count in enumerate(left):
            if not count:
                continue
            ranking = ranked[r]
            cursor = cursors[r]
            while scarce[ranking[cursor]] != bench:
                cursor += 1
            cursors[r] = cursor
            best = ranking[cursor]
            runner = cursor + 1
            while runner < len(ranking) and scarce[ranking[runner]] != bench:
                runner += 1
            fallback = scores[ranking[runner]][r] if runner < len(ranking) else 0.0
            options.append((scores[best][r] - fallback, -r, best))
        _gap, negative_role, worker = max(options)
        role = -negative_role
        scarce[worker] = role
        left[role] -= 1
    allocation = scarce if value(scarce) > value(original) else original

    # Only accept strict improvements. Four sweeps bound the work for large
    # rosters; equal-score assignments remain stable. Bench swaps are allowed.
    if sum(n > 0 for n in counts) > 1:
        for _ in range(4):
            changed = False
            for i in range(len(workers)):
                a = allocation[i]
                best_gain, partner = 1e-9, None
                for j in range(i + 1, len(workers)):
                    b = allocation[j]
                    if a == b:
                        continue
                    gain = scores[i][b] + scores[j][a] - scores[i][a] - scores[j][b]
                    if gain > best_gain:
                        best_gain, partner = gain, j
                if partner is not None:
                    allocation[i], allocation[partner] = allocation[partner], a
                    changed = True
            if not changed:
                break

    assignments = []
    for r, p in enumerate(roles):
        assignments.extend({"worker": workers[i].get("name"), "job_id": p.get("job_id")}
                           for i in ranked[r] if allocation[i] == r)
    return {"assignments": assignments, "empty_slots": empty}
