"""Reputation has one ceiling, get_building_reputation_cap, everywhere it is written."""
from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def function(text, name):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("    def " + name + "("))
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= 4:
            break
        end += 1
    return textwrap.dedent("\n".join(lines[start:end]))


def cap_fn():
    env = {}
    exec(function(source("game/scripts/buildings/building_logic.rpy"), "get_building_reputation_cap"), env)
    return env["get_building_reputation_cap"]


def test_cap_grows_with_building_and_manager_level():
    cap = cap_fn()
    assert cap(None) == 200
    assert cap({"base_level": 3, "assigned_servants": [], "servant_jobs": {}}) == 600
    manager = {"name": "Boss", "level": 3}
    assert cap({"base_level": 3, "assigned_servants": [manager], "servant_jobs": {"Boss": "manager"}}) == 1200
    assert cap({"base_level": 9, "assigned_servants": [manager], "servant_jobs": {"Boss": "manager"}}) == 1600


def test_no_writer_clamps_reputation_to_a_hard_thousand():
    """The event path clamped to 1000 while stories clamped to the level cap: '+5' showed as '-75'."""
    offenders = []
    for path in ("game/scripts/script.rpy", "game/scripts/events/event_daily_exec.rpy",
                 "game/scripts/events/recruitment_functions.rpy", "game/scripts/events/event_resolution.rpy",
                 "game/scripts/buildings/building_logic.rpy"):
        for number, line in enumerate(source(path).splitlines(), 1):
            if "reputation" not in line or "min(" not in line or "1000" not in line:
                continue
            if "min(1000, building_level" in line or "min(1000, manager" in line:
                continue  # the cap function's own components
            if "add_new_building" in line or "Cap reputation at 1000" in line and '"reputation": min(reputation, 1000)' in line:
                continue  # initial value of a brand-new building
            offenders.append("%s:%d: %s" % (path, number, line.strip()))
    assert offenders == [], offenders


def test_event_reputation_uses_the_shared_cap_and_never_deepens_a_loss():
    text = source("game/scripts/script.rpy")
    start = text.index("    def apply_effects(")
    end = text.find("\n    def ", start + 40)
    body = text[start:end]
    assert "get_building_reputation_cap(target_building)" in body
    assert "ceiling = reputation_cap if reputation_change > 0 else max(reputation_cap, old_reputation)" in body
