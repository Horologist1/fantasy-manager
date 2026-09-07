"""Per-building manager gating for normal random events.

Rule: a manager calms their own building, not the world. A normal event's
probability is BASE minus REDUCTION per manager in the event's building
context, floored at MIN (quiet but never dead). No context -> plain BASE.

Context resolution: the paired worker's building count wins when known; for
worker-less events tied to building types, the minimum count among candidate
buildings applies (the event happens where nobody is watching); no building
context at all -> None.
"""

BASE_EVENT_PROBABILITY = 30
REDUCTION_PER_MANAGER = 10
MIN_EVENT_PROBABILITY = 5


def _as_count(value):
    """Coerce a manager count to a non-negative int; garbage -> None."""
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def event_probability(managers_in_context):
    """Daily probability (int %) for a normal event given its context count.

    None (no building context) -> BASE. Garbage/negative counts are treated as
    zero managers rather than crashing the daily loop.
    """
    count = _as_count(managers_in_context)
    if count is None:
        return BASE_EVENT_PROBABILITY
    return max(MIN_EVENT_PROBABILITY, BASE_EVENT_PROBABILITY - REDUCTION_PER_MANAGER * count)


def resolve_context_count(worker_building_count, candidate_counts):
    """Pick the manager count that governs an event's probability.

    worker_building_count: count for the paired worker's building (None if the
    event has no worker yet). candidate_counts: counts for owned buildings
    matching the event's building_type. Returns int count or None (no context).
    """
    worker_count = _as_count(worker_building_count)
    if worker_count is not None:
        return worker_count
    cleaned = [c for c in (_as_count(v) for v in (candidate_counts or [])) if c is not None]
    if cleaned:
        return min(cleaned)
    return None
