"""Choice-level skill_requirements: several minimums, optional guaranteed outcome."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_events import skill_requirements as req

SKILLS = {"Combat": 80, "Agility": 60, "Clever": 20}
skill_of = SKILLS.get


def test_parse_keeps_valid_minimums_only():
    raw = {"Combat": 70, "Agility": 55.9, "": 10, "Oral": "high", "Clever": True, "Charm": -5}
    assert req.parse(raw) == {"Combat": 70, "Agility": 55, "Charm": 0}
    assert req.parse(None) == {} and req.parse(["Combat"]) == {}


def test_every_minimum_must_be_met():
    assert req.meets({"Combat": 70, "Agility": 55}, skill_of)
    assert req.unmet({"Combat": 70, "Agility": 65}, skill_of) == [("Agility", 60, 65)]
    assert not req.meets({"Combat": 70, "Clever": 30}, skill_of)


def test_unknown_or_broken_skill_counts_as_zero():
    def broken(skill):
        raise KeyError(skill)
    assert req.unmet({"Combat": 1}, broken) == [("Combat", 0, 1)]


@pytest.mark.parametrize("choice, guaranteed", [
    ({"skill_requirements": {"Combat": 70}}, True),
    ({"skill_requirements": {"Combat": 70}, "condition": None}, True),
    ({"skill_requirements": {"Combat": 70}, "condition": "Agility"}, False),
    ({"skill_requirements": {}}, False),
    ({"condition": "Agility"}, False),
    ({}, False),
])
def test_guaranteed_only_without_a_roll_condition(choice, guaranteed):
    assert req.is_guaranteed(choice) is guaranteed


def test_label_uses_display_names():
    names = {"Hand": "Handjob"}
    assert req.label({"Combat": 70, "Hand": 40}, lambda s: names.get(s, s)) == "requires Combat 70, Handjob 40"


def test_guaranteed_effect_never_returns_the_wrapper():
    nested = {"success": {"money": 100}, "failure": {"joy": -5}, "success_chance": 0.5}
    assert req.guaranteed_effect(nested) == {"money": 100}
    assert req.guaranteed_effect({"failure": {"joy": -5}}) == {}
    assert req.guaranteed_effect({"money": 50, "success_chance": 0}) == {"money": 50}
    assert req.guaranteed_effect(None) == {}


def test_engine_wires_requirements_into_every_worker_filter():
    """The three candidate filters must agree, or a choice looks open and then
    burns the event on 'no eligible workers'."""
    events = (ROOT / "game/scripts/events/events.rpy").read_text(encoding="utf-8")
    logic = (ROOT / "game/scripts/events/events_logic.rpy").read_text(encoding="utf-8")
    script = (ROOT / "game/scripts/script.rpy").read_text(encoding="utf-8")
    assert events.count("worker_meets_choice_skill_requirements(w, chosen_choice_data)") == 2  # choose + random
    assert "worker_meets_choice_skill_requirements(w, choice)" in logic  # pre-check that disables the option
    assert "worker_meets_choice_skill_requirements(final_worker, choice_option)" in events  # pre-selected worker
    assert "event_choice_is_guaranteed(choice)" in script and "_resolve_guaranteed_event_choice" in script


def test_shipped_events_do_not_use_the_field_yet():
    """Additive feature: no shipped event changes behaviour."""
    import json
    for path in (ROOT / "game/data/events").rglob("*.json"):
        assert "skill_requirements" not in path.read_text(encoding="utf-8"), path.name


# --- importer validation -------------------------------------------------

from fm_mods.packs import PackError, _check_skill_requirements


def event(choice, **extra):
    row = {"id": "e1", "worker_selection": "random", "choices": [choice]}
    row.update(extra)
    return row


def test_importer_accepts_valid_requirements():
    _check_skill_requirements(event({"skill_requirements": {"Combat": 70, "Agility": 55}}), "events")
    _check_skill_requirements(event({"skill_requirements": {"Oral": 40}, "condition": "Charm"}, nsfw=True), "events")


@pytest.mark.parametrize("row, kind, message", [
    (event({"skill_requirements": {"Combat": 70}}), "recruit", "recruitment"),
    (event({"skill_requirements": {"Combat": 70}}, worker_selection="none"), "events", "needs a worker"),
    (event({"skill_requirements": {"Combat": 70}, "condition": "building_skill"}), "events", "needs a worker"),
    (event({"skill_requirements": {"Cooking": 70}}), "events", "unknown skill"),
    (event({"skill_requirements": {"Combat": "70"}}), "events", "numbers"),
    (event({"skill_requirements": {}}), "events", "1 to 6"),
    (event({"skill_requirements": {"Sex": 40}}), "events", "NSFW"),
    (event({"skill_requirements": {"Combat": 40}, "condition": "none"}), "events", "not a skill"),
])
def test_importer_rejects_bad_requirements(row, kind, message):
    with pytest.raises(PackError, match=message):
        _check_skill_requirements(row, kind)
