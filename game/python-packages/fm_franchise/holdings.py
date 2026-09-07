"""Pure Franchise Holdings rules shared by runtime and tests."""

ESTABLISH_COST = 10_000
MAX_LEVEL = 5

FRANCHISE_TYPES = {
    "hospitality": {
        "name": "Hospitality House",
        "description": "Guest houses, catering and discreet household services.",
        "skills": ("Charm", "Service"),
        "nsfw": False,
    },
    "workshop": {
        "name": "Artisan Workshop",
        "description": "Remote commissions, repairs and specialist craftwork.",
        "skills": ("Craft", "Clever"),
        "nsfw": False,
    },
    "arena_school": {
        "name": "Arena School",
        "description": "A provincial school for guards, fighters and performers.",
        "skills": ("Combat",),
        "nsfw": False,
    },
    "brothel": {
        "name": "Pleasure House",
        "description": "A remotely managed house using the enabled intimate arts.",
        "skills": ("Sex", "Anal", "BDSM", "Special", "Extreme", "Homo", "Striptease"),
        "nsfw": True,
    },
}


def _bounded_int(value, low, high):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


def normalize_holdings(raw):
    """Return save-safe established holdings only; legacy emptiness stays empty."""
    result = {}
    for type_id, value in ((raw or {}).items() if hasattr(raw, "items") else []):
        type_id = str(type_id or "").strip().lower()
        if type_id not in FRANCHISE_TYPES:
            continue
        if hasattr(value, "get"):
            level = value.get("level", 1)
        else:
            level = value
        normalized = {
            "type": type_id,
            "level": _bounded_int(level, 1, MAX_LEVEL),
        }
        if hasattr(value, "get") and value.get("enabled_skills") is not None:
            allowed = set(FRANCHISE_TYPES[type_id]["skills"])
            enabled = [str(skill) for skill in (value.get("enabled_skills") or []) if str(skill) in allowed]
            if enabled:
                normalized["enabled_skills"] = enabled
        result[type_id] = normalized
    return result


def franchise_upgrade_cost(current_level):
    """Use the game's normal building curve; None means already maxed."""
    level = _bounded_int(current_level, 1, MAX_LEVEL)
    if level >= MAX_LEVEL:
        return None
    return level * level * 1000


def visible_franchise_types(nsfw_enabled):
    return tuple(
        type_id for type_id, definition in FRANCHISE_TYPES.items()
        if nsfw_enabled or not definition.get("nsfw", False)
    )


def rotating_skill(type_id, total_day, enabled_skills=None):
    """Choose exactly one relevant skill deterministically for this day."""
    definition = FRANCHISE_TYPES.get(str(type_id or "").strip().lower())
    if not definition:
        return None
    allowed = tuple(definition["skills"])
    if enabled_skills is not None:
        enabled = {str(skill) for skill in enabled_skills}
        filtered = tuple(skill for skill in allowed if skill in enabled)
        if filtered:
            allowed = filtered
    if not allowed:
        return None
    day = _bounded_int(total_day, 0, 10**9)
    return allowed[day % len(allowed)]


def _worker_income_value(worker, relevant_skills):
    worker = worker or {}
    level = _bounded_int(worker.get("level", 1), 1, 100)
    skills = worker.get("skills", {}) or {}
    values = [_bounded_int(skills.get(skill, 0), 0, 100) for skill in relevant_skills]
    average_skill = sum(values) / float(len(values) or 1)
    return 10.0 + 1.5 * level + 0.75 * average_skill


def daily_franchise_result(type_id, level, workers, total_day, enabled_skills=None, income_multiplier=1.0):
    """Calculate one franchise in O(workers log workers), without mutating workers."""
    type_id = str(type_id or "").strip().lower()
    definition = FRANCHISE_TYPES.get(type_id)
    if not definition:
        return {
            "type": type_id,
            "income": 0,
            "worker_count": 0,
            "trained_skill": None,
            "training_uses": 0,
            "worker_training": {},
        }

    level = _bounded_int(level, 1, MAX_LEVEL)
    live_workers = [worker for worker in (workers or []) if hasattr(worker, "get") and worker.get("name")]
    relevant_skills = tuple(definition["skills"])
    if enabled_skills is not None:
        enabled = {str(skill) for skill in enabled_skills}
        filtered = tuple(skill for skill in relevant_skills if skill in enabled)
        if filtered:
            relevant_skills = filtered
    values = sorted(
        (_worker_income_value(worker, relevant_skills) for worker in live_workers),
        reverse=True,
    )
    # Every extra team member contributes, but progressively less. This keeps
    # hundreds of remote workers useful without turning the system exponential.
    diminished = sum(value / (1.0 + 0.12 * index) for index, value in enumerate(values))
    level_multiplier = 0.85 + 0.15 * level
    try:
        income_multiplier = max(0.0, float(income_multiplier))
    except (TypeError, ValueError):
        income_multiplier = 1.0
    income = max(0, int(round(diminished * level_multiplier * income_multiplier)))

    trained_skill = rotating_skill(type_id, total_day, enabled_skills=enabled_skills)
    worker_training = {}
    if trained_skill:
        worker_training = {
            str(worker["name"]): {trained_skill: level}
            for worker in live_workers
        }

    return {
        "type": type_id,
        "income": income,
        "worker_count": len(live_workers),
        "trained_skill": trained_skill,
        "training_uses": level if trained_skill else 0,
        "worker_training": worker_training,
    }
