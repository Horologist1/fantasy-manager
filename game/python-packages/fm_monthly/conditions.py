"""No Ren'Py dependencies. State is serialized JSON, replaced atomically for rollback.

Saved cards retain validated effects until the next calendar month, independently
of catalog edits. Never eval authored data. All selectors are exact, conjunctive.
"""
import copy
import json
import math
from functools import lru_cache

NEUTRAL = {"id": "quiet_month", "name": "Quiet month", "description":
           "No special conditions this month.", "weight": 1, "effects": [], "image": ""}


def number(value, lo, hi):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and lo <= value <= hi)


def validate_card(row, known=None):
    if not hasattr(row, "get"):
        raise ValueError("Card must be an object")
    result = {}
    for key in ("id", "name", "description"):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > (500 if key == "description" else 80):
            raise ValueError("Invalid card " + key)
        result[key] = value
    weight = row.get("weight", 1)
    if not number(weight, 0, 10000):
        raise ValueError("Invalid weight")
    result["weight"] = weight
    image = row.get("image", "")
    if not isinstance(image, str) or (image and (not image.startswith("images/")
            or ".." in image or "\\" in image or ":" in image
            or not image.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))):
        raise ValueError("Invalid optional image path")
    result["image"] = image
    if not isinstance(row.get("nsfw", False), bool):
        raise ValueError("Invalid content rating")
    result["nsfw"] = row.get("nsfw", False)
    effects = row.get("effects", [])
    if not isinstance(effects, (list, tuple)) or len(effects) > 3:
        raise ValueError("Expected at most three effects")
    result["effects"] = []
    for effect in effects:
        if not hasattr(effect, "get") or effect.get("type") not in ("skill", "earnings"):
            raise ValueError("Unknown effect type")
        kind = effect["type"]
        value = effect.get("value")
        if not number(value, -10 if kind == "skill" else .9, 10 if kind == "skill" else 1.15):
            raise ValueError("Effect outside supported balance limits")
        out = {"type": kind, "value": value}
        for selector in ("buildings", "professions", "skills"):
            values = effect.get(selector, [])
            if not isinstance(values, (list, tuple)) or any(not isinstance(v, str) or not v for v in values):
                raise ValueError("Invalid selector " + selector)
            if known is not None and any(v not in known[selector] for v in values):
                raise ValueError("Unknown " + selector + " identifier")
            out[selector] = list(dict.fromkeys(values))
        if kind == "skill" and not out["skills"]:
            raise ValueError("Skill effects need explicit skills")
        if kind == "earnings" and out["skills"]:
            raise ValueError("Earnings effects use building/profession selectors")
        if not out["buildings"] and not out["professions"]:
            raise ValueError("Effects need an explicit activity scope")
        result["effects"].append(out)
    if result["id"] == "quiet_month" and result["effects"]:
        raise ValueError("Quiet month cannot have effects")
    return result


def validate_catalog(data, known=None):
    errors, cards, seen = [], [], set()
    if not isinstance(data, list):
        return [copy.deepcopy(NEUTRAL)], ["Catalog must be an array"]
    for row in data:
        try:
            card = validate_card(row, known)
            if card["id"] in seen:
                raise ValueError("Duplicate card id: " + card["id"])
            seen.add(card["id"])
            cards.append(card)
        except (ValueError, TypeError) as exc:
            errors.append(str(exc))
    if "quiet_month" not in seen:
        cards.insert(0, copy.deepcopy(NEUTRAL))
    return cards, errors


def encode(state):
    return json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@lru_cache(maxsize=64)
def decode(raw):
    """Internal read-only view; callers copy before edits."""
    if not isinstance(raw, str) or len(raw) > 20000:
        raise ValueError("Invalid monthly state")
    state = json.loads(raw)
    if not isinstance(state, dict) or state.get("version") != 1:
        raise ValueError("Unknown monthly state version")
    for key in ("enabled", "requested", "experienced"):
        if not isinstance(state.get(key), bool):
            raise ValueError("Invalid monthly toggle")
    if not isinstance(state.get("month"), int) or isinstance(state["month"], bool) or state["month"] < 0:
        raise ValueError("Invalid monthly period")
    if not isinstance(state.get("previous"), str):
        raise ValueError("Invalid monthly history")
    state["card"] = validate_card(state.get("card"))
    return state


def valid_state(raw):
    if raw == "":
        return True
    try:
        decode(raw)
        return True
    except (ValueError, TypeError, KeyError):
        return False


def initial(month):
    return encode(dict(version=1, month=month, enabled=True, requested=True,
                       experienced=False, previous="", card=copy.deepcopy(NEUTRAL)))


def sync(raw, month, catalog, random_value):
    if not raw or not valid_state(raw):
        return initial(month)  # Legacy saves stay neutral for their current month.
    state = decode(raw)
    if month <= state["month"]:
        return raw
    state = copy.deepcopy(state)
    state["enabled"] = state["requested"]
    choices = [c for c in catalog if c["weight"] > 0]
    if not state["experienced"]:
        choices = [c for c in choices if c["effects"]]
    different = [c for c in choices if c["id"] != state["card"]["id"]]
    if different:
        choices = different
    card = copy.deepcopy(NEUTRAL)
    if month >= 3 and state["enabled"] and choices:
        ticket = random_value() * sum(c["weight"] for c in choices)
        card = choices[-1]
        for candidate in choices:
            ticket -= candidate["weight"]
            if ticket < 0:
                card = candidate
                break
    state.update(month=month, previous=state["card"]["id"], card=copy.deepcopy(card))
    state["experienced"] = state["experienced"] or bool(card["effects"])
    return encode(state)


def toggle(raw):
    state = copy.deepcopy(decode(raw))
    state["requested"] = not state["requested"]
    return encode(state)


def modifiers(raw, building, profession, skill=None):
    if not raw:
        return 0, 1.0
    delta, multiplier = 0, 1.0
    state = decode(raw)
    if not state["enabled"]:
        return delta, multiplier
    for effect in state["card"]["effects"]:
        if effect["buildings"] and building not in effect["buildings"]:
            continue
        if effect["professions"] and profession not in effect["professions"]:
            continue
        if effect["type"] == "skill" and skill in effect["skills"]:
            delta += effect["value"]
        elif effect["type"] == "earnings":
            multiplier *= effect["value"]
    return max(-10, min(10, delta)), max(.9, min(1.15, multiplier))


def skill_value(raw, building, profession, skill, value):
    delta, _ = modifiers(raw, building, profession, skill)
    return max(0, value + delta)


def payout(raw, building, profession, value):
    if value <= 0:
        return value
    _, multiplier = modifiers(raw, building, profession)
    return max(1, int(round(value * multiplier)))
