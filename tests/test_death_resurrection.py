"""Death and resurrection contracts across JSON saves and repeated actions."""
from copy import deepcopy
from itertools import permutations
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_lifecycle.rules import (new_state, read_state, remember_death, is_dead,
    prepare_resurrection, release_grave, place_seal, grave_by_id, resurrection_price,
    STATE_KEY, CEMETERY_CAPACITY, SEALS, discover_seal)


def worker(name="Remembered Worker", unique=False):
    return {"name": name, "folder": name.lower().replace(" ", "_"), "unique": unique,
            "level": 4, "health": 0, "energy": 0, "skills": {"Craft": 76},
            "relationship": 93, "romance": 48, "traits": ["Human", "Scarred"],
            "trait_durations": {"Scarred": 0}, "is_servant": True, "source": "bought",
            "assigned_building": "Building_1", "franchise_id": "inn",
            "inventory": [["health_potion", 3, False], ["arena_champion_blade", 1, True]],
            "custom_mod_data": {"memories": ["a", "b"]}}


def buried(state=None, person=None):
    return remember_death(state or new_state(), person or worker(), 12, "Daily work")


def ritual_ready():
    state = new_state()
    for stage in range(4):
        state, result = discover_seal(state, stage, stage + 1)
        assert result == "found"
    return state


def test_old_save_starts_empty_without_inventing_dead_workers_or_resetting_flags():
    flags = {"church_intro_stage": 3, "church_circle_welcomed": True, "other_quest": 12}
    before = deepcopy(flags)
    state = read_state(flags, ["Legacy Lost"])
    assert state["graves"] == [] and not state["unlocked"]
    assert is_dead(state, "Legacy Lost")
    assert flags == before and STATE_KEY not in flags


def test_grave_is_a_detached_copy_of_the_actual_character():
    person = worker(unique=True)
    before = deepcopy(person)
    original_state = new_state()
    state, grave, status = buried(original_state, person)
    assert status == "buried" and grave["worker"] == before
    assert original_state["graves"] == original_state["dead"] == []
    person["inventory"].clear()
    person["skills"]["Craft"] = 1
    assert grave["worker"] == before
    assert is_dead(state, before)
    assert is_dead(state, dict(before, name="A renamed unique worker"))
    assert not is_dead(state, worker("Someone Else", unique=True))


def test_repeated_death_never_duplicates_graves_or_ids():
    state, grave, unused = buried()
    again, record, status = buried(state)
    assert again == state and record is None and status == "already_recorded"
    assert len(again["graves"]) == 1 and again["next_id"] == 2


def test_ten_places_keep_existing_characters_and_record_overflow_death():
    state = new_state()
    for index in range(CEMETERY_CAPACITY + 1):
        state, grave, status = buried(state, worker("Worker " + str(index)))
    assert len(state["graves"]) == CEMETERY_CAPACITY == 10
    assert [row["name"] for row in state["graves"]] == ["Worker " + str(i) for i in range(10)]
    assert status == "full" and grave is None and is_dead(state, "Worker 10")
    state, released = release_grave(state, 1)
    assert released and is_dead(state, "Worker 0")
    state, grave, status = buried(state, worker("New Arrival"))
    assert status == "buried" and len(state["graves"]) == 10
    assert is_dead(state, "Worker 10")  # Freeing space does not invent lost remains.


@pytest.mark.parametrize("failure", ["locked", "money", "already_alive", "missing"])
def test_failed_rite_never_charges_or_alters_records(failure):
    state, grave, unused = buried()
    state["unlocked"] = failure != "locked"
    before = deepcopy(state)
    result = prepare_resurrection(state, 999 if failure == "missing" else grave["id"],
                                  [worker()] if failure == "already_alive" else [],
                                  0 if failure == "money" else 99999)
    assert result == (None, None, 0, failure)
    assert state == before


def test_resurrection_preserves_progress_gear_and_ownership_after_json_load():
    state, grave, unused = buried()
    state["unlocked"] = True
    saved_flags = json.loads(json.dumps({STATE_KEY: state, "other_quest": 17}))
    loaded = read_state(saved_flags, ["Stale Native Death"])
    assert not is_dead(loaded, "Stale Native Death")
    updated, restored, cost, status = prepare_resurrection(loaded, grave["id"], [], 10000)
    assert status == "ok" and cost == resurrection_price(grave) == 8000
    for field in ("name", "skills", "relationship", "romance", "inventory", "traits", "trait_durations", "is_servant", "source", "custom_mod_data"):
        assert restored[field] == grave["worker"][field]
    assert restored["assigned_building"] == "Unassigned" and "franchise_id" not in restored
    assert not is_dead(updated, restored) and updated["graves"] == []
    assert len(loaded["graves"]) == 1 and saved_flags["other_quest"] == 17
    assert prepare_resurrection(updated, grave["id"], [restored], 10000 - cost)[3] == "missing"
    again, new_grave, status = buried(updated, restored)
    assert status == "buried" and new_grave["id"] != grave["id"]
    assert len(again["graves"]) == 1


def test_release_is_permanent_and_cannot_be_used_to_recruit_a_unique_again():
    state, grave, unused = buried(person=worker(unique=True))
    updated, released = release_grave(state, grave["id"])
    assert released and grave_by_id(updated, grave["id"]) is None
    assert is_dead(updated, grave["worker"])
    assert release_grave(updated, grave["id"]) == (updated, False)
    assert len(state["graves"]) == 1


@pytest.mark.parametrize("level,budget,expected", [
    (1, 4999, "money"), (1, 5000, "ok"),
    (4, 7999, "money"), (4, 8000, "ok"),
    (10, 14000, "ok"), ("4", 8000, "ok"),
])
def test_current_price_applies_to_loaded_graves_without_changing_the_save(level, budget, expected):
    person = worker()
    person["level"] = level
    state, grave, unused = buried(person=person)
    state["unlocked"] = True
    loaded = read_state(json.loads(json.dumps({STATE_KEY: state})))
    before = deepcopy(loaded)
    updated, restored, cost, status = prepare_resurrection(loaded, grave["id"], [], budget)
    assert status == expected and loaded == before
    if expected == "ok":
        assert cost == budget and len(updated["graves"]) == 0
        assert restored["inventory"] == person["inventory"]
    else:
        assert updated is None and restored is None and cost == 0


@pytest.mark.parametrize("sequence", list(permutations(SEALS)))
def test_seal_puzzle_has_exactly_one_solution_and_survives_partial_saves(sequence):
    state = ritual_ready()
    for seal in sequence:
        state, result = place_seal(state, seal)
        state = read_state(json.loads(json.dumps({STATE_KEY: state})))
    assert state["unlocked"] == (sequence == SEALS)
    assert result == ("unlocked" if sequence == SEALS else "retry")
    assert state["attempts"] == 1 and state["seals"] == []


def test_duplicate_or_stale_seal_actions_do_not_advance_the_puzzle():
    state, unused = place_seal(ritual_ready(), "Stone")
    assert place_seal(state, "Stone") == (state, "invalid")
    assert place_seal(state, "Invalid") == (state, "invalid")
    for seal in SEALS[1:]:
        state, unused = place_seal(state, seal)
    assert place_seal(state, "Stone") == (state, "unlocked")


def test_unknown_future_state_is_not_silently_replaced():
    with pytest.raises(ValueError, match="not changed"):
        read_state({STATE_KEY: {"version": 99, "valuable": "future data"}})
