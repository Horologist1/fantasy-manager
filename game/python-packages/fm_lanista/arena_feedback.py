"""Deterministic summaries for ordinary Arena combat reports."""

COMBAT_PROFESSION_IDS = frozenset(
    {
        "arena_exhibition",
        "arena_proving",
        "arena_championship",
    }
)

_RESULT_KEYS = {
    "critical success": "critical_successes",
    "success": "successes",
    "mediocre": "mediocres",
    "failure": "failures",
}


def _normalized(value):
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def summarize_daily_arena_feedback(report_entries, day):
    """Return one primitive-only summary for the day's ordinary Arena bouts."""
    summary = {
        "day": int(day),
        "total": 0,
        "critical_successes": 0,
        "successes": 0,
        "mediocres": 0,
        "failures": 0,
        "standout_worker": "",
        "concern_worker": "",
    }
    standout_rank = 0
    concern_rank = 0

    for entry in report_entries or ():
        if not hasattr(entry, "get"):
            continue
        if _normalized(entry.get("building_type_id")) != "arena":
            continue
        profession_id = str(entry.get("profession_id") or "").strip().lower()
        if profession_id not in COMBAT_PROFESSION_IDS:
            continue
        result = _normalized(entry.get("result"))
        counter = _RESULT_KEYS.get(result)
        if counter is None:
            continue

        summary["total"] += 1
        summary[counter] += 1
        worker_name = str(entry.get("worker_name") or "").strip()

        positive_rank = 2 if result == "critical success" else (1 if result == "success" else 0)
        if positive_rank > standout_rank and worker_name:
            standout_rank = positive_rank
            summary["standout_worker"] = worker_name

        negative_rank = 2 if result == "failure" else (1 if result == "mediocre" else 0)
        if negative_rank > concern_rank and worker_name:
            concern_rank = negative_rank
            summary["concern_worker"] = worker_name

    return summary if summary["total"] else None
