"""Pure helpers for Daily Report preparation and archiving."""

import copy


SKILL_BADGE_ABBREVIATIONS = {
    "Sex": "Sex",
    "Anal": "Anal",
    "BDSM": "BDSM",
    "Hand": "Hand",
    "Oral": "Oral",
    "Homo": "Homo",
    "Special": "Spc",
    "Group": "Grp",
    "Extreme": "Ext",
    "Striptease": "Strip",
    "Combat": "Cmb",
    "Clever": "Clv",
    "Charm": "Chm",
    "Service": "Srv",
    "Agility": "Agi",
    "Craft": "Crf",
}


def _escape_renpy_text(value):
    """Escape dynamic data before embedding it inside Ren'Py text markup."""
    return str(value).replace("[", "[[").replace("{", "{{")


def format_skill_level_badges(skill_deltas):
    """Format the day's skill gain as ONE inline badge (e.g. "+1 Agi").

    A story grants at most one skill level per worker per day, so this renders
    the first valid positive delta and ignores the rest by design — the badge
    must fit inline after the worker name on a single table row.
    """
    for entry in skill_deltas or []:
        if not isinstance(entry, (list, tuple)) or len(entry) < 3:
            continue
        skill_name = str(entry[0] or "").strip()
        if not skill_name:
            continue
        try:
            gained = int(entry[2]) - int(entry[1])
        except (TypeError, ValueError):
            continue
        if gained <= 0:
            continue
        return "+%s %s" % (
            gained,
            _escape_renpy_text(SKILL_BADGE_ABBREVIATIONS.get(skill_name, skill_name)),
        )
    return ""


def snapshot_worker_health(workers):
    """Capture a primitive name->health baseline before the daily event flow."""
    baseline = {}
    for worker in workers or []:
        if not hasattr(worker, "get"):
            continue
        name = str(worker.get("name", "")).strip()
        if not name:
            continue
        try:
            baseline[name] = int(worker.get("health", 0) or 0)
        except (TypeError, ValueError):
            continue
    return baseline


def collect_net_hp_losses(workers, baseline):
    """Return negative net HP deltas for workers present in the baseline."""
    source = baseline if hasattr(baseline, "get") else {}
    losses = {}
    for worker in workers or []:
        if not hasattr(worker, "get"):
            continue
        name = str(worker.get("name", "")).strip()
        if not name or name not in source:
            continue
        try:
            delta = int(worker.get("health", 0) or 0) - int(source.get(name, 0) or 0)
        except (TypeError, ValueError):
            continue
        if delta < 0:
            losses[name] = delta
    return losses


def copy_report_without_worker(report):
    """Deep-copy a report after excluding its live worker object graph."""
    if not hasattr(report, "items"):
        return {}

    projected = {key: value for key, value in report.items() if key != "worker"}
    try:
        return copy.deepcopy(projected)
    except Exception:
        archived = {}
        for key, value in projected.items():
            try:
                archived[copy.deepcopy(key)] = copy.deepcopy(value)
            except Exception:
                continue
        return archived


def report_page_window(reports, page, page_size=50):
    """Return one bounded report page plus its normalized index/count."""
    source = reports or []
    try:
        size = max(1, int(page_size))
    except (TypeError, ValueError):
        size = 50
    page_count = max(1, (len(source) + size - 1) // size)
    try:
        normalized_page = int(page)
    except (TypeError, ValueError):
        normalized_page = 0
    normalized_page = max(0, min(normalized_page, page_count - 1))
    start = normalized_page * size
    return list(source[start:start + size]), normalized_page, page_count


def daily_report_story_positions(reports):
    """Map id(report) -> (n, total) for workers with several report entries on
    one day, numbered in report order. Entries are grouped by archived day,
    building and worker, so a worker's 3 stories read 1/3, 2/3, 3/3 and a
    single-story worker gets no entry (no counter shown)."""
    groups = {}
    for report in reports or []:
        if not hasattr(report, "get"):
            continue
        key = (
            report.get("_advance_day_index"),
            str(report.get("building", "")),
            str(report.get("worker_name", "")),
        )
        groups.setdefault(key, []).append(report)
    positions = {}
    for entries in groups.values():
        total = len(entries)
        if total < 2:
            continue
        for number, report in enumerate(entries, 1):
            positions[id(report)] = (number, total)
    return positions
