"""Pure building skill-policy decisions for random events.

The Ren'Py layer supplies already-eligible workers/buildings. This module only
answers whether the event's depicted worker skills are permitted by that
building's saved policy.
"""


def _normalized_skill(value):
    return str(value or "").strip().lower()


def _as_values(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    try:
        return list(raw)
    except TypeError:
        return [raw]


def _dedupe_skills(values):
    result = []
    seen = set()
    for value in values:
        clean = str(value or "").strip()
        key = _normalized_skill(clean)
        if clean and key and key not in seen:
            result.append(clean)
            seen.add(key)
    return tuple(result)


def event_choice_policy_skills(choice):
    """Return the worker skills whose depicted content this choice exposes.

    ``policy_skills`` is an explicit author override. Otherwise the rolled
    condition is the depicted skill. ``image_skill`` already means that the
    outcome depicts a different category, so it replaces the mechanical check.
    Same-sex media (gay/les) is additive: the underlying act still occurs and
    the Homo policy must also be respected. Explicit null suppresses skill media
    and therefore marks the choice as policy-neutral.
    """
    if not choice or not hasattr(choice, "get"):
        return ()

    if "policy_skills" in choice:
        return _dedupe_skills(_as_values(choice.get("policy_skills")))

    condition = str(choice.get("condition") or "").strip()
    if condition.lower() == "building_skill":
        condition = ""

    if "image_skill" not in choice:
        return _dedupe_skills([condition])

    image_skill = choice.get("image_skill")
    if image_skill is None:
        return ()

    image_clean = str(image_skill or "").strip()
    image_key = _normalized_skill(image_clean)
    if image_key in ("gay", "les", "homo"):
        return _dedupe_skills([condition, "Homo"])
    return _dedupe_skills([image_clean])


def banned_skills_for_gender(building, worker_gender):
    """Read both legacy global bans and additive gender-targeted save data."""
    if not building or not hasattr(building, "get"):
        return frozenset()

    result = {
        _normalized_skill(value)
        for value in (building.get("banned_skills", []) or [])
        if _normalized_skill(value)
    }
    gender = str(worker_gender or "").strip().lower()
    rules = building.get("banned_skills_by_gender", {}) or {}
    if not hasattr(rules, "items"):
        return frozenset(result)

    for skill_name, raw_genders in rules.items():
        if hasattr(raw_genders, "get"):
            raw_genders = raw_genders.get("genders", [])
        genders = {
            str(value or "").strip().lower()
            for value in _as_values(raw_genders)
        }
        if "both" in genders or "all" in genders:
            genders.update(("male", "female"))
        if gender in genders:
            key = _normalized_skill(skill_name)
            if key:
                result.add(key)
    return frozenset(result)


def choice_allowed_by_building_policy(building, choice, worker_gender):
    """True when none of a choice's depicted skills is banned for the worker."""
    policy_skills = {
        _normalized_skill(value)
        for value in event_choice_policy_skills(choice)
        if _normalized_skill(value)
    }
    if not policy_skills:
        return True
    return not bool(policy_skills.intersection(banned_skills_for_gender(building, worker_gender)))


def event_has_policy_relevant_choices(event):
    """Whether an event depicts at least one worker skill governed by policy."""
    if not event or not hasattr(event, "get"):
        return False
    return any(event_choice_policy_skills(choice) for choice in (event.get("choices", []) or []))


def event_worker_allowed_by_building_policy(building, event, worker):
    """True if this worker can perform at least one policy-relevant event choice.

    Neutral decline/pass choices deliberately do not keep a blocked event alive.
    Events without any depicted worker skill remain unaffected.
    """
    choices = [
        choice for choice in ((event or {}).get("choices", []) or [])
        if event_choice_policy_skills(choice)
    ]
    if not choices:
        return True
    gender = worker.get("gender") if hasattr(worker, "get") else None
    return any(
        choice_allowed_by_building_policy(building, choice, gender)
        for choice in choices
    )
