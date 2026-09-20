"""Daily exploration, legacy puzzle access, and save-safe collection rules."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_lifecycle.rules import (new_state, read_state, pilgrimage_state, can_explore,
    discover_seal, place_seal, remember_death, prepare_resurrection, SEALS, STATE_KEY)


def json_loaded(state):
    return read_state(json.loads(json.dumps({STATE_KEY: state})))


def test_four_chapters_require_four_separate_days_and_survive_each_save():
    state = new_state()
    for stage, day in enumerate((27, 28, 29, 337)):
        before = deepcopy(state)
        assert can_explore(state, day)
        updated, result = discover_seal(state, stage, day)
        assert result == "found" and state == before
        state = json_loaded(updated)
        assert pilgrimage_state(state)["stage"] == stage + 1
        assert not can_explore(state, day)
        assert state["seals"] == [] and not state["unlocked"]
        assert pilgrimage_state(state)["last_day"] == day
    assert not can_explore(state, 999)
    for seal in SEALS:
        state, result = place_seal(state, seal)
    assert result == "unlocked"


@pytest.mark.parametrize("stage", range(4))
def test_missing_seals_block_direct_puzzle_calls_without_changing_attempts(stage):
    state = new_state()
    for index in range(stage):
        state, result = discover_seal(state, index, 10 + index)
    before = deepcopy(state)
    assert place_seal(state, "Stone") == (state, "missing_seals")
    assert state == before and state["attempts"] == 0


def test_stale_repeated_and_backward_day_actions_never_grant_another_seal():
    state, result = discover_seal(new_state(), 0, 28)
    before = deepcopy(state)
    assert discover_seal(state, 0, 29) == (state, "stale")
    assert discover_seal(state, 2, 29) == (state, "stale")
    for day in (27, 28):
        assert discover_seal(state, 1, day) == (state, "wait")
    assert state == before
    assert discover_seal(state, 1, 29)[1] == "found"


def test_prayer_records_only_its_local_evening_and_does_not_rewrite_other_progress():
    state = new_state()
    state["unrelated_extra"] = {"keep": [7]}
    for stage in range(4):
        state, result = discover_seal(state, stage, stage + 1)
        assert pilgrimage_state(state)["night_day"] == (None if stage < 2 else 3)
    assert state["unrelated_extra"] == {"keep": [7]}


@pytest.mark.parametrize("seals,attempts,unlocked", [
    (["Stone"], 0, False), (["Stone", "Water"], 0, False),
    ([], 2, False), ([], 1, True),
])
def test_older_partial_failed_or_unlocked_puzzles_keep_access(seals, attempts, unlocked):
    state = new_state()
    del state["pilgrimage"]
    state.update(seals=seals, attempts=attempts, unlocked=unlocked)
    before = deepcopy(state)
    loaded = json_loaded(state)
    assert pilgrimage_state(loaded)["stage"] == 4
    assert not can_explore(loaded, 20)
    assert discover_seal(loaded, 0, 20) == (loaded, "complete")
    assert loaded == before and "pilgrimage" not in loaded
    if unlocked:
        assert place_seal(loaded, "Stone") == (loaded, "unlocked")
    else:
        remaining = [seal for seal in SEALS if seal not in seals]
        for seal in remaining:
            loaded, result = place_seal(loaded, seal)
        assert result == "unlocked" and loaded["attempts"] == attempts + 1


def test_older_unstarted_puzzle_begins_search_without_mutating_the_save():
    state = new_state()
    del state["pilgrimage"]
    flags = {STATE_KEY: state, "church_intro_stage": 3, "other_quest": 12}
    before = deepcopy(flags)
    loaded = read_state(flags)
    assert pilgrimage_state(loaded)["stage"] == 0 and can_explore(loaded, 3)
    assert flags == before


def test_exploration_never_changes_burials_or_the_rite_price_and_cannot_repeat():
    person = {"name": "Mod Character", "level": 4, "inventory": [["health_potion", 3, False]],
              "custom_data": {"memories": ["keep"]}}
    state, grave, result = remember_death(new_state(), person, 1, "Work")
    remembered = deepcopy(state["graves"])
    for stage in range(4):
        state, result = discover_seal(state, stage, stage + 2)
    assert state["graves"] == remembered
    assert prepare_resurrection(state, grave["id"], [], 8000)[3] == "locked"
    for seal in SEALS:
        state, result = place_seal(state, seal)
    before = deepcopy(state)
    assert discover_seal(state, 0, 100) == (state, "complete")
    assert state == before
    updated, worker, cost, result = prepare_resurrection(state, grave["id"], [], 8000)
    assert result == "ok" and cost == 8000
    assert worker["inventory"] == person["inventory"] and worker["custom_data"] == person["custom_data"]
    assert updated["graves"] == []
