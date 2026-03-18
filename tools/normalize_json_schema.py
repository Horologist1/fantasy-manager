import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "game" / "data"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def infer_default_from_value(value: Any) -> Any:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return 0
    if isinstance(value, str):
        return None
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def collect_union_keys(items: list[dict]) -> dict[str, Any]:
    union: dict[str, Any] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        for k, v in item.items():
            if k not in union:
                union[k] = infer_default_from_value(v)
    return union


def ensure_keys(d: dict, defaults: dict[str, Any]) -> None:
    for key, default in defaults.items():
        if key not in d:
            d[key] = copy.deepcopy(default)


def _is_default_like(value: Any) -> bool:
    if value is None:
        return True
    if value is False:
        return True
    if value == 0:
        return True
    if value == "":
        return True
    if value == []:
        return True
    if value == {}:
        return True
    return False


def _drop_empty_keys(d: dict, keys: list[str]) -> None:
    for key in keys:
        if key in d and _is_default_like(d[key]):
            del d[key]


def normalize_events() -> None:
    events_dir = DATA / "events"
    event_files = [
        ("events_common.json", "list"),
        ("events_building.json", "list"),
        ("events_seasonal.json", "dict"),
        ("events_shops.json", "list"),
        ("events_special.json", "list"),
    ]
    recruit_dir = events_dir / "recruit"
    recruit_files = list(recruit_dir.glob("*.json")) if recruit_dir.exists() else []

    all_events: list[dict] = []
    file_data: list[tuple[Path, Any, str]] = []

    for fname, fmt in event_files:
        path = events_dir / fname
        if not path.exists():
            continue
        try:
            data = read_json(path)
        except Exception:
            continue
        if fmt == "list" and isinstance(data, list):
            events = [e for e in data if isinstance(e, dict)]
            all_events.extend(events)
            file_data.append((path, data, "list"))
        elif fmt == "dict" and isinstance(data, dict):
            events = [v for v in data.values() if isinstance(v, dict)]
            all_events.extend(events)
            file_data.append((path, data, "dict"))

    for path in recruit_files:
        try:
            data = read_json(path)
        except Exception:
            continue
        if isinstance(data, list):
            events = [e for e in data if isinstance(e, dict)]
            all_events.extend(events)
            file_data.append((path, data, "list"))
        elif isinstance(data, dict):
            events = [v for v in data.values() if isinstance(v, dict)]
            all_events.extend(events)
            file_data.append((path, data, "dict"))

    event_defaults = collect_union_keys(all_events)
    event_defaults.update(
        {
            "id": None,
            "description": None,
            "weight": 0,
            "limited": False,
            "max_occurrences": 0,
            "cooldown_days": 0,
            "event_probability": 0,
            "guaranteed": False,
            "worker_selection": None,
            "worker_gender_requirement": None,
            "player_gender_requirement": None,
            "requires_assigned_worker": False,
            "required_building_worker_traits": [],
            "required_building_traits": [],
            "building_type": [],
            "background_image": None,
            "success_image": None,
            "failure_image": None,
            "nsfw": False,
            "required_flags": {},
            "excluded_flags": {},
            "conditions": {},
            "start_when": None,
            "stop_when": None,
            "choices": [],
        }
    )
    condition_defaults = {"start_when": None, "stop_when": None}

    all_choices: list[dict] = []
    for e in all_events:
        for c in e.get("choices", []) or []:
            if isinstance(c, dict):
                all_choices.append(c)

    choice_defaults = collect_union_keys(all_choices)
    choice_defaults.update(
        {
            "option": None,
            "condition": None,
            "threshold": 0,
            "required_trait": None,
            "required_traits": [],
            "excluded_traits": [],
            "trait_visibility": "hide",
            "blocked_message": None,
            "message": None,
            "message_success": None,
            "message_failure": None,
            "conditions": {},
            "required_flags": {},
            "excluded_flags": {},
            "effect": {},
        }
    )

    all_effects = [c.get("effect", {}) for c in all_choices if isinstance(c.get("effect", {}), dict)]
    effect_defaults = collect_union_keys(all_effects)
    effect_defaults.update(
        {
            "money": 0,
            "reputation": 0,
            "custom": None,
            "event_flags": {},
            "item_id": None,
            "loot_rolls": 0,
            "worker_name": None,
            "random_worker": False,
            "skill_modifiers": {},
            "add_trait": {},
            "success": {},
            "failure": {},
        }
    )

    add_trait_defaults = {"name": None, "duration": 0, "target": None}
    branch_defaults = {
        "money": 0,
        "reputation": 0,
        "custom": None,
        "event_flags": {},
        "skill_modifiers": {},
        "add_trait": {},
    }

    def normalize_event_list(event_list: list[dict]) -> list[dict]:
        for event in event_list:
            if not isinstance(event, dict):
                continue
            ensure_keys(event, event_defaults)
            if not isinstance(event.get("conditions"), dict):
                event["conditions"] = {}
            ensure_keys(event["conditions"], condition_defaults)
            if not isinstance(event.get("required_flags"), dict):
                event["required_flags"] = {}
            if not isinstance(event.get("excluded_flags"), dict):
                event["excluded_flags"] = {}
            if not isinstance(event.get("required_building_worker_traits"), list):
                event["required_building_worker_traits"] = []
            if not isinstance(event.get("required_building_traits"), list):
                event["required_building_traits"] = []
            if not isinstance(event.get("building_type"), list):
                event["building_type"] = []
            if not isinstance(event.get("choices"), list):
                event["choices"] = []

            for choice in event["choices"]:
                if not isinstance(choice, dict):
                    continue
                ensure_keys(choice, choice_defaults)
                if not isinstance(choice.get("conditions"), dict):
                    choice["conditions"] = {}
                ensure_keys(choice["conditions"], condition_defaults)
                if not isinstance(choice.get("required_flags"), dict):
                    choice["required_flags"] = {}
                if not isinstance(choice.get("excluded_flags"), dict):
                    choice["excluded_flags"] = {}
                if not isinstance(choice.get("effect"), dict):
                    choice["effect"] = {}
                ensure_keys(choice["effect"], effect_defaults)
                if not isinstance(choice.get("required_traits"), list):
                    choice["required_traits"] = []
                if not isinstance(choice.get("excluded_traits"), list):
                    choice["excluded_traits"] = []

                if not isinstance(choice["effect"].get("event_flags"), dict):
                    choice["effect"]["event_flags"] = {}
                if not isinstance(choice["effect"].get("add_trait"), dict):
                    choice["effect"]["add_trait"] = {}
                ensure_keys(choice["effect"]["add_trait"], add_trait_defaults)

                for branch in ("success", "failure"):
                    if not isinstance(choice["effect"].get(branch), dict):
                        choice["effect"][branch] = {}
                    ensure_keys(choice["effect"][branch], branch_defaults)
                    if not isinstance(choice["effect"][branch].get("event_flags"), dict):
                        choice["effect"][branch]["event_flags"] = {}
                    if not isinstance(choice["effect"][branch].get("add_trait"), dict):
                        choice["effect"][branch]["add_trait"] = {}
                    ensure_keys(choice["effect"][branch]["add_trait"], add_trait_defaults)

                # Lightweight cleanup for choices/effects.
                if isinstance(choice.get("conditions"), dict):
                    _drop_empty_keys(choice["conditions"], ["start_when", "stop_when"])
                    if not choice["conditions"]:
                        del choice["conditions"]
                _drop_empty_keys(
                    choice,
                    [
                        "condition",
                        "threshold",
                        "required_trait",
                        "required_traits",
                        "excluded_traits",
                        "trait_visibility",
                        "blocked_message",
                        "message",
                        "message_success",
                        "message_failure",
                        "required_flags",
                        "excluded_flags",
                    ],
                )
                if choice.get("trait_visibility") == "hide":
                    del choice["trait_visibility"]

                effect = choice.get("effect", {})
                if isinstance(effect, dict):
                    # Remove default-like add_trait
                    if isinstance(effect.get("add_trait"), dict):
                        _drop_empty_keys(effect["add_trait"], ["name", "duration", "target"])
                        if not effect["add_trait"]:
                            del effect["add_trait"]

                    for branch in ("success", "failure"):
                        branch_data = effect.get(branch)
                        if isinstance(branch_data, dict):
                            if isinstance(branch_data.get("add_trait"), dict):
                                _drop_empty_keys(branch_data["add_trait"], ["name", "duration", "target"])
                                if not branch_data["add_trait"]:
                                    del branch_data["add_trait"]
                            if isinstance(branch_data.get("skill_modifiers"), dict) and not branch_data["skill_modifiers"]:
                                del branch_data["skill_modifiers"]
                            _drop_empty_keys(branch_data, ["money", "reputation", "custom", "event_flags", "add_trait"])
                            if not branch_data:
                                del effect[branch]

                    if isinstance(effect.get("skill_modifiers"), dict) and not effect["skill_modifiers"]:
                        del effect["skill_modifiers"]
                    _drop_empty_keys(
                        effect,
                        [
                            "money",
                            "reputation",
                            "custom",
                            "event_flags",
                            "item_id",
                            "loot_rolls",
                            "worker_name",
                            "random_worker",
                            "add_trait",
                            "success",
                            "failure",
                        ],
                    )

            # Lightweight cleanup for events.
            if isinstance(event.get("conditions"), dict):
                _drop_empty_keys(event["conditions"], ["start_when", "stop_when"])
                if not event["conditions"]:
                    del event["conditions"]
            _drop_empty_keys(
                event,
                [
                    "weight",
                    "limited",
                    "max_occurrences",
                    "cooldown_days",
                    "event_probability",
                    "guaranteed",
                    "worker_selection",
                    "worker_gender_requirement",
                    "requires_assigned_worker",
                    "required_building_worker_traits",
                    "required_building_traits",
                    "building_type",
                    "background_image",
                    "success_image",
                    "failure_image",
                    "nsfw",
                    "required_flags",
                    "excluded_flags",
                    "conditions",
                    "start_when",
                    "stop_when",
                ],
            )
        return event_list

    for path, data, fmt in file_data:
        if fmt == "list":
            normalize_event_list(data)
        elif fmt == "dict":
            normalize_event_list(list(data.values()))
        write_json(path, data)


def normalize_interactions() -> None:
    interactions_dir = DATA / "interactions"
    paths = [
        interactions_dir / "interactions_structured.json",
        interactions_dir / "interactions_special.json",
    ]
    arrays = [read_json(p) for p in paths]
    all_entries = [x for arr in arrays for x in arr if isinstance(x, dict)]

    interaction_defaults = collect_union_keys(all_entries)
    interaction_defaults.update(
        {
            "id": None,
            "name": None,
            "description": None,
            "interaction_level": None,
            "interaction_type": None,
            "cost_energy": 0,
            "cost_money": 0,
            "effect": {},
            "gender_filter": None,
            "worker_gender": None,
            "categories": [],
            "image": None,
            "nsfw": False,
            "stat_requirements": {},
            "specific_workers": [],
            "required_traits": [],
            "excluded_traits": [],
            "required_flags": {},
            "excluded_flags": {},
        }
    )

    effect_list = [x.get("effect", {}) for x in all_entries if isinstance(x.get("effect", {}), dict)]
    effect_defaults = collect_union_keys(effect_list)
    effect_defaults.update(
        {
            "romance": 0,
            "relationship": 0,
            "joy": 0,
            "rebelliousness": 0,
            "flags": {},
        }
    )

    def _is_default_flag_obj(value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        return bool(value.get("value", False)) is False and int(value.get("duration", 0) or 0) == 0

    def _is_falsey_flag_value(value: Any) -> bool:
        if isinstance(value, dict):
            return _is_default_flag_obj(value)
        return value in (False, None, 0, "")

    for path, arr in zip(paths, arrays):
        for entry in arr:
            if not isinstance(entry, dict):
                continue
            ensure_keys(entry, interaction_defaults)
            if not isinstance(entry.get("effect"), dict):
                entry["effect"] = {}
            ensure_keys(entry["effect"], effect_defaults)
            if not isinstance(entry["effect"].get("flags"), dict):
                entry["effect"]["flags"] = {}
            if not isinstance(entry.get("stat_requirements"), dict):
                entry["stat_requirements"] = {}
            if not isinstance(entry.get("required_flags"), dict):
                entry["required_flags"] = {}
            if not isinstance(entry.get("excluded_flags"), dict):
                entry["excluded_flags"] = {}
            if not isinstance(entry.get("specific_workers"), list):
                entry["specific_workers"] = []
            if not isinstance(entry.get("required_traits"), list):
                entry["required_traits"] = []
            if not isinstance(entry.get("excluded_traits"), list):
                entry["excluded_traits"] = []
            if not isinstance(entry.get("categories"), list):
                entry["categories"] = []

            # Lightweight runtime normalization:
            # keep only explicitly meaningful flags/requirements in data files.
            cleaned_required = {}
            for flag_name, flag_value in entry["required_flags"].items():
                if not _is_falsey_flag_value(flag_value):
                    cleaned_required[flag_name] = flag_value
            entry["required_flags"] = cleaned_required

            cleaned_excluded = {}
            for flag_name, flag_value in entry["excluded_flags"].items():
                if not _is_falsey_flag_value(flag_value):
                    cleaned_excluded[flag_name] = flag_value
            entry["excluded_flags"] = cleaned_excluded

            cleaned_effect_flags = {}
            for flag_name, flag_value in entry["effect"]["flags"].items():
                if isinstance(flag_value, dict):
                    normalized_flag = {
                        "value": bool(flag_value.get("value", False)),
                        "duration": int(flag_value.get("duration", 0) or 0),
                    }
                    if not _is_default_flag_obj(normalized_flag):
                        cleaned_effect_flags[flag_name] = normalized_flag
                elif not _is_falsey_flag_value(flag_value):
                    cleaned_effect_flags[flag_name] = {"value": bool(flag_value), "duration": 0}
            entry["effect"]["flags"] = cleaned_effect_flags

            # Keep stat requirements sparse: zeros are no-op thresholds and can alter
            # discipline semantics if injected globally.
            if isinstance(entry.get("stat_requirements"), dict):
                entry["stat_requirements"] = {
                    stat_name: stat_value
                    for stat_name, stat_value in entry["stat_requirements"].items()
                    if not _is_default_like(stat_value)
                }

            # Optional keys: omit when empty to reduce noise in runtime JSON.
            for optional_key in ("required_flags", "excluded_flags", "stat_requirements", "specific_workers", "required_traits", "excluded_traits"):
                if optional_key in entry and entry[optional_key] in ({}, []):
                    del entry[optional_key]
            if "interaction_type" in entry and entry["interaction_type"] is None:
                del entry["interaction_type"]
            if isinstance(entry.get("effect"), dict) and entry["effect"].get("flags") == {}:
                del entry["effect"]["flags"]
            _drop_empty_keys(entry, ["interaction_level", "cost_money"])

        write_json(path, arr)


def normalize_buildings() -> None:
    path = DATA / "buildings" / "building_types.json"
    data = read_json(path)
    btypes = data.get("building_types", [])
    if not isinstance(btypes, list):
        return

    bt_defaults = collect_union_keys([b for b in btypes if isinstance(b, dict)])
    bt_defaults.update(
        {
            "id": None,
            "name": None,
            "skill_name": None,
            "skill_description": None,
            "nsfw": False,
            "allowed_map_locations": [],
            "professions": [],
        }
    )

    professions = []
    for bt in btypes:
        if isinstance(bt, dict):
            professions.extend([p for p in bt.get("professions", []) if isinstance(p, dict)])
    prof_defaults = collect_union_keys(professions)
    prof_defaults.update(
        {
            "id": None,
            "name": None,
            "description": None,
            "nsfw": False,
            "difficulty": None,
            "skills": [],
            "max_daily_workers": 0,
            "daily_story_count": {"base": 0, "bonus_formula": "0"},
            "daily_stories": [],
        }
    )

    stories = []
    for p in professions:
        stories.extend([s for s in p.get("daily_stories", []) if isinstance(s, dict)])
    story_defaults = collect_union_keys(stories)
    story_defaults.update(
        {
            "id": None,
            "weight": 0,
            "report": None,
            "description": None,
            "difficulty_modifier": 0,
            "worker_gender_requirement": None,
            "nsfw_only": False,
            "skill_options": [],
            "trait_roll_modifiers": {},
            "trait_msg_success_both": None,
            "trait_msg_success_pos": None,
            "trait_msg_success_neg": None,
            "trait_msg_failure_both": None,
            "trait_msg_failure_neg": None,
            "trait_msg_failure_pos": None,
            "relevant_traits": [],
            "trait_success": None,
            "earnings": {},
            "descriptions": {},
            "consequences": {},
            "story_image": None,
            "failure_image": None,
            "loot": {},
            "required_traits": [],
            "excluded_traits": [],
            "stat_requirements": {},
        }
    )

    desc_defaults = {
        "failure": None,
        "mediocre": None,
        "success": None,
        "critical_success": None,
    }
    earning_defaults = {
        "failure": "0",
        "mediocre": "0",
        "success": "0",
        "critical_success": "0",
    }
    consequence_stats = {
        "energy": 0,
        "health": 0,
        "joy": 0,
        "rebelliousness": 0,
        "romance": 0,
        "relationship": 0,
        "reputation": 0,
        "libido": 0,
        "obedience": 0,
    }
    consequence_defaults = {
        "failure": copy.deepcopy(consequence_stats),
        "mediocre": copy.deepcopy(consequence_stats),
        "success": copy.deepcopy(consequence_stats),
        "critical_success": copy.deepcopy(consequence_stats),
    }
    loot_defaults = {
        "rolls": 0,
        "bonus_items": [],
        "monster_worker": {"chance": 0, "filters": {}},
        "captured_worker": {"chance": 0, "filters": {}},
    }
    bonus_item_defaults = {"item_id": None, "chance": 0, "nsfw": False}

    for bt in btypes:
        if not isinstance(bt, dict):
            continue
        ensure_keys(bt, bt_defaults)
        if not isinstance(bt.get("allowed_map_locations"), list):
            bt["allowed_map_locations"] = []
        if not isinstance(bt.get("professions"), list):
            bt["professions"] = []

        for prof in bt["professions"]:
            if not isinstance(prof, dict):
                continue
            ensure_keys(prof, prof_defaults)
            if isinstance(prof.get("daily_story_count"), int):
                prof["daily_story_count"] = {"base": prof["daily_story_count"], "bonus_formula": "0"}
            elif not isinstance(prof.get("daily_story_count"), dict):
                prof["daily_story_count"] = {"base": 0, "bonus_formula": "0"}
            ensure_keys(prof["daily_story_count"], {"base": 0, "bonus_formula": "0"})
            if not isinstance(prof.get("skills"), list):
                prof["skills"] = []
            if not isinstance(prof.get("daily_stories"), list):
                prof["daily_stories"] = []

            for story in prof["daily_stories"]:
                if not isinstance(story, dict):
                    continue
                ensure_keys(story, story_defaults)
                if not isinstance(story.get("required_traits"), list):
                    story["required_traits"] = []
                if not isinstance(story.get("excluded_traits"), list):
                    story["excluded_traits"] = []
                if not isinstance(story.get("stat_requirements"), dict):
                    story["stat_requirements"] = {}
                if not isinstance(story.get("skill_options"), list):
                    story["skill_options"] = []
                if not isinstance(story.get("relevant_traits"), list):
                    story["relevant_traits"] = []
                if not isinstance(story.get("descriptions"), dict):
                    story["descriptions"] = {}
                ensure_keys(story["descriptions"], desc_defaults)
                if not isinstance(story.get("earnings"), dict):
                    story["earnings"] = {}
                ensure_keys(story["earnings"], earning_defaults)
                if not isinstance(story.get("consequences"), dict):
                    story["consequences"] = {}
                ensure_keys(story["consequences"], consequence_defaults)
                for outcome in ("failure", "mediocre", "success", "critical_success"):
                    if not isinstance(story["consequences"].get(outcome), dict):
                        story["consequences"][outcome] = copy.deepcopy(consequence_stats)
                    ensure_keys(story["consequences"][outcome], consequence_stats)

                if not isinstance(story.get("loot"), dict):
                    story["loot"] = {}
                ensure_keys(story["loot"], loot_defaults)
                if not isinstance(story["loot"].get("bonus_items"), list):
                    story["loot"]["bonus_items"] = []
                for bonus_item in story["loot"]["bonus_items"]:
                    if isinstance(bonus_item, dict):
                        ensure_keys(bonus_item, bonus_item_defaults)
                for worker_key in ("monster_worker", "captured_worker"):
                    if not isinstance(story["loot"].get(worker_key), dict):
                        story["loot"][worker_key] = {"chance": 0, "filters": {}}
                    ensure_keys(story["loot"][worker_key], {"chance": 0, "filters": {}})
                    if not isinstance(story["loot"][worker_key].get("filters"), dict):
                        story["loot"][worker_key]["filters"] = {}

                # Lightweight story cleanup.
                _drop_empty_keys(
                    story,
                    [
                        "description",
                        "difficulty_modifier",
                        "worker_gender_requirement",
                        "skill_options",
                        "relevant_traits",
                        "trait_success",
                        "required_traits",
                        "excluded_traits",
                        "stat_requirements",
                        "failure_image",
                    ],
                )
                if isinstance(story.get("descriptions"), dict):
                    _drop_empty_keys(story["descriptions"], ["failure", "mediocre", "success", "critical_success"])
                    if not story["descriptions"]:
                        del story["descriptions"]
                if isinstance(story.get("earnings"), dict):
                    for k in list(story["earnings"].keys()):
                        if str(story["earnings"][k]).strip() in ("0", "0.0", ""):
                            del story["earnings"][k]
                    if not story["earnings"]:
                        del story["earnings"]
                if isinstance(story.get("consequences"), dict):
                    for outcome_key in list(story["consequences"].keys()):
                        outcome_data = story["consequences"].get(outcome_key, {})
                        if isinstance(outcome_data, dict):
                            for stat_key in list(outcome_data.keys()):
                                if _is_default_like(outcome_data[stat_key]):
                                    del outcome_data[stat_key]
                            if not outcome_data:
                                del story["consequences"][outcome_key]
                    if not story["consequences"]:
                        del story["consequences"]
                if isinstance(story.get("loot"), dict):
                    _drop_empty_keys(story["loot"], ["rolls", "bonus_items"])
                    for worker_key in ("monster_worker", "captured_worker"):
                        wdata = story["loot"].get(worker_key)
                        if isinstance(wdata, dict):
                            _drop_empty_keys(wdata, ["chance", "filters"])
                            if not wdata:
                                del story["loot"][worker_key]
                    if not story["loot"]:
                        del story["loot"]

            # Lightweight profession cleanup.
            _drop_empty_keys(prof, ["description", "nsfw", "difficulty", "max_daily_workers"])
            if isinstance(prof.get("daily_story_count"), dict):
                if int(prof["daily_story_count"].get("base", 0) or 0) == 0 and str(prof["daily_story_count"].get("bonus_formula", "0")).strip() in ("0", "0.0", ""):
                    del prof["daily_story_count"]
            if prof.get("skills") == []:
                del prof["skills"]

        # Lightweight building cleanup.
        _drop_empty_keys(bt, ["nsfw", "allowed_map_locations"])

    write_json(path, data)


def normalize_items() -> None:
    path = DATA / "items" / "items.json"
    data = read_json(path)
    items = data.get("items", [])
    if not isinstance(items, list):
        return
    item_defaults = collect_union_keys([i for i in items if isinstance(i, dict)])
    item_defaults.update(
        {
            "id": None,
            "name": None,
            "display_name": None,
            "type": None,
            "effect": {},
            "description": None,
            "durability": 0,
            "price": 0,
            "weight": 0,
            "nsfw": False,
        }
    )

    # Keep optional runtime-heavy keys sparse.
    for sparse_optional in ("shop_available", "auto_consume_on_receive", "obtain_hint"):
        if sparse_optional in item_defaults:
            del item_defaults[sparse_optional]

    # Avoid propagating scalar effect defaults across all items.
    effect_defaults = {"custom": None, "skill_modifiers": {}, "attribute_modifiers": {}, "daily_effects": {}}

    for item in items:
        if not isinstance(item, dict):
            continue
        ensure_keys(item, item_defaults)
        if not isinstance(item.get("effect"), dict):
            item["effect"] = {}
        ensure_keys(item["effect"], effect_defaults)
        for nested in ("skill_modifiers", "attribute_modifiers", "daily_effects"):
            if not isinstance(item["effect"].get(nested), dict):
                item["effect"][nested] = {}
        for nested in ("skill_modifiers", "attribute_modifiers", "daily_effects"):
            if item["effect"].get(nested) == {}:
                del item["effect"][nested]
        if item["effect"].get("custom") is None:
            del item["effect"]["custom"]
        if item["effect"] == {}:
            del item["effect"]

        _drop_empty_keys(item, ["display_name", "description", "durability", "weight", "nsfw", "auto_consume_on_receive", "obtain_hint"])

    if "excluded_from_shops" not in data or not isinstance(data.get("excluded_from_shops"), list):
        data["excluded_from_shops"] = []
    if data.get("excluded_from_shops") == []:
        del data["excluded_from_shops"]
    write_json(path, data)


def _extract_traits_list(data: Any) -> list[dict]:
    """Extract list of trait dicts from JSON (list or dict with 'traits' key)."""
    if isinstance(data, list):
        return [t for t in data if isinstance(t, dict)]
    if isinstance(data, dict) and "traits" in data:
        return [t for t in data.get("traits", []) if isinstance(t, dict)]
    return []


def normalize_traits() -> None:
    traits_dir = DATA / "traits"
    legacy_path = DATA / "traits.json"

    all_traits: list[dict] = []
    trait_files: list[tuple[Path, Any]] = []

    if legacy_path.exists():
        try:
            data = read_json(legacy_path)
            traits = _extract_traits_list(data)
            if traits:
                all_traits.extend(traits)
                trait_files.append((legacy_path, data))
        except Exception:
            pass

    if traits_dir.exists():
        for path in sorted(traits_dir.glob("*.json")):
            try:
                data = read_json(path)
                traits = _extract_traits_list(data)
                if traits:
                    all_traits.extend(traits)
                    trait_files.append((path, data))
            except Exception:
                continue

    if not all_traits:
        return

    trait_defaults = collect_union_keys(all_traits)
    trait_defaults.update(
        {
            "name": None,
            "conflicts": [],
            "removes_traits": [],
            "modifiers": {},
            "description": None,
            "nsfw": False,
        }
    )
    modifier_defaults = collect_union_keys(
        [t.get("modifiers", {}) for t in all_traits if isinstance(t.get("modifiers", {}), dict)]
    )
    for key in (
        "skill_modifiers",
        "attribute_caps",
        "attribute_minimums",
        "daily_effects",
        "earnings_multiplier",
        "libido_max",
        "libido_regeneration",
    ):
        if key not in modifier_defaults:
            modifier_defaults[key] = {} if key.endswith("modifiers") or key.endswith("caps") or key.endswith("minimums") or key.endswith("effects") else 0

    def normalize_trait_list(trait_list: list[dict]) -> None:
        for trait in trait_list:
            if not isinstance(trait, dict):
                continue
            ensure_keys(trait, trait_defaults)
            if not isinstance(trait.get("conflicts"), list):
                trait["conflicts"] = []
            if not isinstance(trait.get("removes_traits"), list):
                trait["removes_traits"] = []
            if not isinstance(trait.get("modifiers"), dict):
                trait["modifiers"] = {}
            ensure_keys(trait["modifiers"], modifier_defaults)
            for nested in ("skill_modifiers", "attribute_caps", "attribute_minimums", "daily_effects"):
                if not isinstance(trait["modifiers"].get(nested), dict):
                    trait["modifiers"][nested] = {}
            for nested in ("skill_modifiers", "attribute_caps", "attribute_minimums", "daily_effects"):
                if trait["modifiers"].get(nested) == {}:
                    del trait["modifiers"][nested]
            for mod_key in list(trait["modifiers"].keys()):
                if mod_key in ("skill_modifiers", "attribute_caps", "attribute_minimums", "daily_effects"):
                    continue
                if _is_default_like(trait["modifiers"].get(mod_key)):
                    del trait["modifiers"][mod_key]
            _drop_empty_keys(trait["modifiers"], ["earnings_multiplier", "libido_max", "libido_regeneration"])
            if trait["modifiers"] == {}:
                del trait["modifiers"]
            _drop_empty_keys(trait, ["conflicts", "removes_traits", "description", "nsfw"])

    for path, data in trait_files:
        traits = _extract_traits_list(data)
        if traits:
            normalize_trait_list(traits)
        write_json(path, data)


def main() -> None:
    normalize_events()
    normalize_interactions()
    normalize_buildings()
    normalize_items()
    normalize_traits()
    print("Normalization completed.")


if __name__ == "__main__":
    main()
