"""Trait modifiers record what they really changed, so add+remove never drifts a stat."""
from pathlib import Path
import random
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
TRAITS = (ROOT / "game/scripts/workers/worker_traits.rpy").read_text(encoding="utf-8")
STATS = (ROOT / "game/scripts/workers/worker_stats.rpy").read_text(encoding="utf-8")


def function(source, name):
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("    def " + name + "("))
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= 4:
            break
        end += 1
    return textwrap.dedent("\n".join(lines[start:end]))


def environment():
    env = {
        "random": random,
        "renpy": SimpleNamespace(log=lambda message: None),
        "store": SimpleNamespace(management_skills={}),
        "traits_list": [{"name": "Optimist", "modifiers": {"joy": 20}}, {"name": "Charmer", "modifiers": {"romance": 5}}],
    }
    for name in ("get_attribute_cap", "get_attribute_minimum", "set_attribute_with_caps",
                 "apply_trait_secondary_modifiers_once", "recalculate_trait_modifiers"):
        exec(function(TRAITS, name), env)
    return env


def worker(**values):
    base = {"name": "Test", "traits": [], "joy": 50, "rebelliousness": 50, "romance": 0, "comfort_level": 1,
            "comfort_desired": 1, "relationship": 11, "libido": 10}
    base.update(values)
    return base


def test_clamped_bonus_is_fully_reverted_on_removal():
    env = environment()
    w = worker(joy=90)
    env["apply_trait_secondary_modifiers_once"](w)
    w["traits"].append("Optimist")
    env["recalculate_trait_modifiers"](w)
    assert w["joy"] == 100
    assert w["_last_applied_trait_modifiers"]["joy"] == 10
    w["traits"].remove("Optimist")
    env["recalculate_trait_modifiers"](w)
    assert w["joy"] == 90


def test_unclamped_bonus_round_trips_exactly():
    env = environment()
    w = worker(joy=40)
    env["apply_trait_secondary_modifiers_once"](w)
    w["traits"].append("Optimist")
    env["recalculate_trait_modifiers"](w)
    assert w["joy"] == 60 and w["_last_applied_trait_modifiers"]["joy"] == 20
    w["joy"] = 30  # the day's events moved it
    w["traits"].remove("Optimist")
    env["recalculate_trait_modifiers"](w)
    assert w["joy"] == 10


def test_untouched_attributes_keep_their_recorded_value():
    env = environment()
    w = worker(joy=95, romance=0)
    w["traits"] = ["Optimist"]
    env["apply_trait_secondary_modifiers_once"](w)
    assert w["_last_applied_trait_modifiers"]["joy"] == 5
    w["traits"].append("Charmer")
    env["recalculate_trait_modifiers"](w)
    assert w["_last_applied_trait_modifiers"] == {"joy": 5, "rebelliousness": 0, "romance": 5, "comfort_level": 0,
                                                  "comfort_desired": 0, "relationship": 0, "libido": 0}


def test_max_energy_has_the_same_floor_as_max_health():
    assert "return max(1, int(max_energy))" in STATS
    assert "return max(1, int(max_health))" in STATS


def test_permanent_grant_clears_an_earlier_countdown():
    body = function(TRAITS, "add_trait_with_duration")
    assert "durations.pop(trait_name, None)" in body
