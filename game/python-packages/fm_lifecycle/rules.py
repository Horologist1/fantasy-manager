"""Pure, copy-on-write rules. All persisted values live inside event_flags."""
from copy import deepcopy

STATE_KEY = "church_life_cycle"
CEMETERY_CAPACITY = 10
SEALS = ("Stone", "Water", "Wind", "Flame")


def new_state(legacy_names=()):
    return {"version": 1, "next_id": 1, "graves": [],
            "dead": [{"name": name, "tokens": ["name:" + name.casefold()]}
                     for name in legacy_names if isinstance(name, str) and name],
            "unlocked": False, "seals": [], "attempts": 0,
            "pilgrimage": {"stage": 0, "last_day": None, "night_day": None}}


def read_state(flags, legacy_names=()):
    state = flags.get(STATE_KEY) if hasattr(flags, "get") else None
    if state is None:
        return new_state(legacy_names)
    if not hasattr(state, "get") or state.get("version") != 1:
        raise ValueError("Unsupported cemetery data; existing records were not changed.")
    return state


def identity_tokens(worker):
    if isinstance(worker, str):
        return {"name:" + worker.casefold()}
    if not hasattr(worker, "get"):
        return set()
    name = str(worker.get("worker_name") or worker.get("name") or "")
    tokens = {"name:" + name.casefold()} if name else set()
    if worker.get("unique"):
        identity = worker.get("template_id") or worker.get("source_template_id") or worker.get("folder")
        if identity:
            tokens.add("unique:" + str(identity).casefold())
    return tokens


def is_dead(state, worker):
    tokens = identity_tokens(worker)
    return any(tokens.intersection(row.get("tokens", [])) for row in state["dead"])


def remember_death(state, worker, day, cause, capacity=CEMETERY_CAPACITY):
    """Keep existing graves when full; never evict someone without a choice."""
    if is_dead(state, worker):
        return state, None, "already_recorded"
    updated = deepcopy(state)
    death_id = updated["next_id"]
    updated["next_id"] += 1
    memorial = {"id": death_id, "name": worker["name"],
                "tokens": sorted(identity_tokens(worker)), "day": int(day), "cause": str(cause)}
    updated["dead"].append(memorial)
    if len(updated["graves"]) >= capacity:
        return updated, None, "full"
    grave = dict(memorial, worker=deepcopy(worker))
    updated["graves"].append(grave)
    return updated, grave, "buried"


def grave_by_id(state, grave_id):
    return next((row for row in state["graves"] if row["id"] == grave_id), None)


def resurrection_price(grave):
    level = max(1, int(grave["worker"].get("level", 1) or 1))
    return 5000 + 1000 * (level - 1)


def prepare_resurrection(state, grave_id, roster, money):
    """Validate everything before returning a new state and the original worker."""
    if not state["unlocked"]:
        return None, None, 0, "locked"
    grave = grave_by_id(state, grave_id)
    if grave is None:
        return None, None, 0, "missing"
    tokens = set(grave["tokens"])
    if any(tokens.intersection(identity_tokens(worker)) for worker in roster):
        return None, None, 0, "already_alive"
    cost = resurrection_price(grave)
    if money < cost:
        return None, None, 0, "money"
    updated = deepcopy(state)
    updated["graves"] = [row for row in updated["graves"] if row["id"] != grave_id]
    updated["dead"] = [row for row in updated["dead"] if row.get("id") != grave_id]
    worker = deepcopy(grave["worker"])
    worker["assigned_building"] = "Unassigned"
    worker.pop("franchise_id", None)
    worker.pop("franchise_since_day", None)
    worker["energy"] = 0
    return updated, worker, cost, "ok"


def release_grave(state, grave_id):
    """Free one place while retaining the death/recruitment record."""
    if grave_by_id(state, grave_id) is None:
        return state, False
    updated = deepcopy(state)
    updated["graves"] = [row for row in updated["graves"] if row["id"] != grave_id]
    return updated, True


def pilgrimage_state(state):
    """Optional data inside the existing save record; never mutate on read.

    Earlier saves that reached the puzzle keep their seals and access. They
    already received every clue in the old dialogue, so need no new collection.
    """
    progress = state.get("pilgrimage")
    if progress is not None:
        return progress
    known = state.get("unlocked") or state.get("seals") or state.get("attempts", 0)
    return {"stage": len(SEALS) if known else 0, "last_day": None, "night_day": None}


def can_explore(state, day):
    progress = pilgrimage_state(state)
    return (not state["unlocked"] and progress["stage"] < len(SEALS)
            and (progress["last_day"] is None or int(day) > progress["last_day"]))


def discover_seal(state, expected_stage, day):
    """Award one chapter's seal, once, only after a later dawn than the last."""
    progress = pilgrimage_state(state)
    if state["unlocked"] or progress["stage"] >= len(SEALS):
        return state, "complete"
    if expected_stage != progress["stage"]:
        return state, "stale"
    if not can_explore(state, day):
        return state, "wait"
    updated = deepcopy(state)
    updated["pilgrimage"] = dict(progress, stage=expected_stage + 1, last_day=int(day))
    if expected_stage == 2:
        updated["pilgrimage"]["night_day"] = int(day)
    return updated, "found"


def place_seal(state, seal):
    if state["unlocked"]:
        return state, "unlocked"
    if pilgrimage_state(state)["stage"] < len(SEALS):
        return state, "missing_seals"
    if seal not in SEALS or seal in state["seals"]:
        return state, "invalid"
    updated = deepcopy(state)
    updated["pilgrimage"] = deepcopy(pilgrimage_state(state))
    updated["seals"].append(seal)
    if len(updated["seals"]) < len(SEALS):
        return updated, "continue"
    updated["attempts"] += 1
    correct = tuple(updated["seals"]) == SEALS
    updated["unlocked"] = correct
    updated["seals"] = []
    return updated, "unlocked" if correct else "retry"
