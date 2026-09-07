"""Pure Academy curriculum rules shared by runtime glue and tests."""

_SKILL_ORDER = (
    "Sex", "Anal", "BDSM", "Hand", "Oral", "Homo", "Special", "Group",
    "Extreme", "Striptease", "Combat", "Clever", "Charm", "Service",
    "Agility", "Craft",
)


def _names(values):
    return {str(value).strip() for value in (values or []) if str(value).strip()}


def _ordered(values):
    names = _names(values)
    known = [name for name in _SKILL_ORDER if name in names]
    known.extend(sorted(names.difference(known), key=str.lower))
    return known


def _canonical(value, allowed):
    wanted = str(value or "").strip().lower()
    return next((name for name in allowed if name.lower() == wanted), None)


def allowed_focus_skills(profession, worker_skills=None, visible_skills=None):
    """Return valid curriculum choices in stable display order."""
    profession = profession or {}
    curriculum = profession.get("training_curriculum") or {}
    if not curriculum:
        return []

    pool_mode = str(curriculum.get("focus_pool", "profession")).strip().lower()
    if pool_mode == "visible":
        pool = _ordered(visible_skills)
    else:
        permitted = _names(profession.get("skills") or [])
        pool = [name for name in _SKILL_ORDER if name in permitted]
        pool.extend(sorted(permitted.difference(pool), key=str.lower))

    if visible_skills is not None:
        visible = _names(visible_skills)
        pool = [name for name in pool if name in visible]
    if worker_skills is not None:
        present = _names(worker_skills)
        pool = [name for name in pool if name in present]

    fixed = str(curriculum.get("fixed_primary") or "").strip()
    if fixed and fixed not in pool:
        fixed_visible = visible_skills is None or fixed in _names(visible_skills)
        fixed_present = worker_skills is None or fixed in _names(worker_skills)
        if fixed_visible and fixed_present:
            pool.insert(0, fixed)
    return pool


def normalize_focus(profession, focus, allowed_skills):
    """Validate a saved selection and return canonical primary/secondary names."""
    if not hasattr(focus, "get"):
        return None
    profession = profession or {}
    curriculum = profession.get("training_curriculum") or {}
    allowed = list(allowed_skills or [])
    if str(curriculum.get("focus_pool", "profession")).strip().lower() == "profession":
        profession_skills = _names(profession.get("skills") or [])
        allowed = [name for name in allowed if name in profession_skills]
    if not curriculum or len(allowed) < 2:
        return None

    fixed = str(curriculum.get("fixed_primary") or "").strip()
    primary = _canonical(fixed, allowed) if fixed else _canonical(focus.get("primary"), allowed)
    secondary = _canonical(focus.get("secondary"), allowed)
    if not primary or not secondary or primary == secondary:
        return None
    return {"primary": primary, "secondary": secondary}


def build_directed_plan(profession, focus, worker_skills=None, visible_skills=None):
    """Return {skill: uses} for a valid focus, or None for the legacy path."""
    if not focus:
        return None
    curriculum = (profession or {}).get("training_curriculum") or {}
    allowed = allowed_focus_skills(profession, worker_skills, visible_skills)
    normalized = normalize_focus(profession, focus, allowed)
    if not normalized:
        return None

    try:
        primary_uses = int(curriculum.get("primary_uses", 0) or 0)
        secondary_uses = int(curriculum.get("secondary_uses", 0) or 0)
    except (TypeError, ValueError):
        return None
    if primary_uses <= 0 or secondary_uses <= 0:
        return None
    return {
        normalized["primary"]: primary_uses,
        normalized["secondary"]: secondary_uses,
    }


def focus_story_pool(stories, primary_skill):
    """Prefer stories matching the curriculum; preserve the original fallback."""
    original = list(stories or [])
    wanted = str(primary_skill or "").strip().lower()
    if not wanted:
        return original
    matches = [
        story for story in original
        if str((story or {}).get("used_skill") or "").strip().lower() == wanted
    ]
    return matches or original
