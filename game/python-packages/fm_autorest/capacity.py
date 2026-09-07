"""Save-safe job-capacity decisions shared by runtime and tests."""


def _job_id(value):
    return str(value or "").strip().lower()


def reserved_job_id(worker, current_job):
    """Return the capacity slot occupied by a worker's current state."""
    current = _job_id(current_job)
    if current != "rest":
        return current
    if not hasattr(worker, "get"):
        return current
    previous = worker.get("previous_profession") or worker.get("previous_job")
    return _job_id(previous) or current


def count_job_slots(servant_jobs, workers, job_id, include_reservations=True):
    """Count active workers and, optionally, Rest reservations for one job."""
    target = _job_id(job_id)
    if not target or target in ("rest", "unassigned"):
        return 0
    if not hasattr(servant_jobs, "items"):
        return 0

    workers_by_name = {
        worker.get("name"): worker
        for worker in (workers or [])
        if hasattr(worker, "get") and worker.get("name")
    }
    count = 0
    for worker_name, current_job in servant_jobs.items():
        worker = workers_by_name.get(worker_name)
        if worker is None:
            continue
        occupied_job = _job_id(current_job)
        if include_reservations:
            occupied_job = reserved_job_id(worker, occupied_job)
        if occupied_job == target:
            count += 1
    return count


def claim_job_slot(
    worker,
    current_job,
    target_job,
    occupied_count,
    active_count,
    capacity,
):
    """Plan one direct assignment without activating an overbooked reservation."""
    try:
        occupied = int(occupied_count)
        active = int(active_count)
        limit = int(capacity)
    except (TypeError, ValueError):
        return False, occupied_count, active_count

    current = _job_id(current_job)
    target = _job_id(target_job)
    if not target or target in ("rest", "unassigned") or limit <= 0:
        return False, occupied, active
    if current == target:
        return True, occupied, active
    if current == "rest" and reserved_job_id(worker, current) == target:
        if active >= limit:
            return False, occupied, active
        return True, occupied, active + 1
    if occupied >= limit:
        return False, occupied, active
    return True, occupied + 1, active + 1


def can_restore_reserved_job(servant_jobs, workers, job_id, capacity):
    """A rested worker returns only while the active job remains below capacity."""
    try:
        limit = int(capacity)
    except (TypeError, ValueError):
        return False
    if limit <= 0:
        return False
    active = count_job_slots(
        servant_jobs,
        workers,
        job_id,
        include_reservations=False,
    )
    return active < limit
