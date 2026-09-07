"""Pure worker-choice ordering, searching, and pagination."""


def _normalized_name(worker):
    try:
        value = worker.get("name", "")
    except AttributeError:
        value = ""
    return str(value or "").strip().casefold()


def _numeric_score(worker, score_getter):
    try:
        value = score_getter(worker)
        return float(value or 0)
    except (AttributeError, TypeError, ValueError):
        return 0.0


def rank_worker_choices(workers, last_worker_name=None, query="", score_getter=None):
    """Filter by name and rank last-used, score descending, then name."""
    score_getter = score_getter or (lambda worker: 0)
    normalized_query = str(query or "").strip().casefold()
    normalized_last = str(last_worker_name or "").strip().casefold()
    ranked = []

    for index, worker in enumerate(workers or []):
        name = _normalized_name(worker)
        if normalized_query and normalized_query not in name:
            continue
        is_last = bool(normalized_last and name == normalized_last)
        ranked.append(
            (
                (0 if is_last else 1, -_numeric_score(worker, score_getter), name, index),
                worker,
            )
        )

    ranked.sort(key=lambda entry: entry[0])
    return [worker for _key, worker in ranked]


def page_worker_choices(workers, page, page_size):
    """Return one page plus a clamped zero-based page and page count."""
    try:
        size = max(1, int(page_size))
    except (TypeError, ValueError):
        size = 1
    items = list(workers or [])
    page_count = max(1, (len(items) + size - 1) // size)
    try:
        requested_page = int(page)
    except (TypeError, ValueError):
        requested_page = 0
    current_page = min(max(0, requested_page), page_count - 1)
    start = current_page * size
    return items[start:start + size], current_page, page_count
