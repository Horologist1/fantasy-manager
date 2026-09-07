"""Pure roster sort-mode logic.

`default` is handled by the screen's own (building, job, -skill, name) tuple and
is deliberately rejected here. The attribute modes are pure: they read one
worker attribute (missing -> 0) with a case-insensitive name tiebreaker. All
"problem first" modes sort ascending except rebelliousness, where high is the
problem, so it is negated.
"""

SORT_MODES = ["default", "favorites", "energy", "health", "joy", "rebelliousness"]

# Modes where a higher raw value should sort first (negate the metric).
_DESCENDING = {"rebelliousness"}

# Human-readable labels for the cycling UI button.
SORT_LABELS = {
    "default": "Building",
    "favorites": "Favorites",
    "energy": "Energy",
    "health": "Health",
    "joy": "Joy",
    "rebelliousness": "Rebellious",
}


def next_sort_mode(current):
    """Return the next mode in the cycle; unknown input restarts at the first."""
    try:
        idx = SORT_MODES.index(current)
    except ValueError:
        return SORT_MODES[0]
    return SORT_MODES[(idx + 1) % len(SORT_MODES)]


def toggle_favorite(worker):
    """Toggle and return favorite state, including for legacy worker dicts."""
    current = bool(worker.get("favorite", False))
    worker["favorite"] = not current
    return worker["favorite"]


def worker_sort_key(worker, mode):
    """Sort key (metric, name) for an attribute mode.

    Raises ValueError for 'default' (screen owns it) or any unknown mode, so a
    miswired call fails loudly instead of sorting silently wrong.
    """
    if mode == "default" or mode not in SORT_MODES:
        raise ValueError("worker_sort_key does not handle mode %r" % (mode,))
    if mode == "favorites":
        try:
            fav = bool(worker.get("favorite"))
        except AttributeError:
            fav = False
        name = str(worker.get("name", "") if hasattr(worker, "get") else "").strip().lower()
        return (0 if fav else 1, name)
    try:
        value = worker.get(mode, 0) or 0
    except AttributeError:
        value = 0
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    if mode in _DESCENDING:
        value = -value
    name = str(worker.get("name", "") if hasattr(worker, "get") else "").strip().lower()
    return (value, name)
