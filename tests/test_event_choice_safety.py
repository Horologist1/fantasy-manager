"""Behavioural regressions for rejected recruitment transactions."""
import copy
import re
import textwrap
from pathlib import Path
from types import SimpleNamespace
import pytest

SOURCE = (Path(__file__).resolve().parents[1] / "game/scripts/events/recruitment_functions.rpy").read_text(encoding="utf-8")


def function(name):
    lines = SOURCE.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("    def " + name + "("))
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= 4:
            break
        end += 1
    return textwrap.dedent("\n".join(lines[start:end]))


def environment(worker, duplicate=False, dead=False):
    state = SimpleNamespace(workers=[worker] if duplicate else [], money=100,
                            event_occurrences={"offer": 2}, event_last_occurred={"offer": 10})
    env = {"store": state, "is_worker_dead": lambda w: dead,
           "renpy": SimpleNamespace(log=lambda message: None),
           "player_name": "Manager", "player_title": "Lady",
           "format_dynamic_message": lambda message, values: message}
    exec(function("apply_recruitment_effects"), env)
    exec(function("process_recruitment_choice"), env)
    return state, env


@pytest.mark.parametrize("reason", ["duplicate", "dead", "monster", "missing"])
def test_invalid_hire_has_no_money_attributes_reputation_or_roster_effects(reason):
    worker = {"name": "Guest", "health": 40, "joy": 20, "traits": [], "monster": reason == "monster"}
    if reason == "missing":
        worker = None
    state, env = environment(worker, duplicate=reason == "duplicate", dead=reason == "dead")
    before = copy.deepcopy((vars(state), worker))
    result = env["apply_recruitment_effects"]({"recruit_worker": True, "money": 50,
        "reputation": 5, "health": -10, "joy": 8, "add_trait": {"name": "Trial Worker"}}, worker)
    assert result["recruitment_blocked"]
    assert (vars(state), worker) == before


def test_stale_hire_does_not_claim_success_or_consume_another_occurrence():
    worker = {"name": "Already Hired", "daily_cost": 100, "comfort_level": 2}
    state, env = environment(worker, duplicate=True)
    result = env["process_recruitment_choice"](
        {"option": "Hire", "message": "[event_worker] has joined!", "effect": {"recruit_worker": True, "money": 50}},
        {"id": "offer", "unlimited": False}, worker)
    assert result["outcome"] == "failure"
    assert "No changes were made" in result["message"]
    assert state.money == 100 and state.workers == [worker]
    assert state.event_occurrences == {"offer": 2} and state.event_last_occurred == {"offer": 10}
