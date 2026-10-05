"""Multi-skill requirements on event choices.

A choice may carry "skill_requirements": {"Combat": 70, "Agility": 55}. Every
listed minimum must be met for a worker to take the choice. With a "condition"
the usual roll still decides the outcome; without one the choice succeeds
without a roll (a guaranteed outcome for whoever qualifies).

Plain data in, decisions out: skill levels arrive through a callable so the
.rpy layer keeps owning the trait/equipment maths.
"""

MAX_REQUIREMENTS = 6


def parse(raw):
    """{skill: minimum} with integer minimums; malformed entries are dropped."""
    if not hasattr(raw, "items"):
        return {}
    result = {}
    for skill, minimum in list(raw.items())[:MAX_REQUIREMENTS]:
        if not isinstance(skill, str) or not skill.strip():
            continue
        if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
            continue
        result[skill.strip()] = max(0, int(minimum))
    return result


def unmet(requirements, skill_of):
    """[(skill, has, needs)] for every minimum the worker misses."""
    missing = []
    for skill, minimum in requirements.items():
        try:
            level = int(skill_of(skill))
        except Exception:
            level = 0
        if level < minimum:
            missing.append((skill, level, minimum))
    return missing


def meets(requirements, skill_of):
    return not unmet(requirements, skill_of)


def is_guaranteed(choice):
    """No roll: requirements present and no skill condition to roll against."""
    if not hasattr(choice, "get"):
        return False
    return bool(parse(choice.get("skill_requirements"))) and not choice.get("condition")


def label(requirements, display_name=None):
    """'requires Combat 70, Agility 55' for option texts and lock reasons."""
    name = display_name or (lambda skill: skill)
    return "requires " + ", ".join("%s %d" % (name(skill), minimum) for skill, minimum in requirements.items())


def guaranteed_effect(effect):
    """The block a guaranteed choice applies: its success block when the author
    wrote success/failure, otherwise the flat effect. Never the wrapper dict,
    whose nested blocks apply_effects() would silently drop."""
    if not hasattr(effect, "get"):
        return {}
    if "success" in effect or "failure" in effect:
        success = effect.get("success")
        return success if hasattr(success, "get") else {}
    return {key: value for key, value in effect.items() if key != "success_chance"}
