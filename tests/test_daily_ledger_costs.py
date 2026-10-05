"""Report and summary cost totals must equal what the daily ledger charges."""
from pathlib import Path
import textwrap
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parents[1] / "game/scripts/events/event_daily_exec.rpy").read_text(encoding="utf-8")


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


def load(owned_buildings, available_buildings):
    env = {"store": SimpleNamespace(owned_buildings=owned_buildings), "available_buildings": available_buildings}
    exec(function("daily_ledger_building_names"), env)
    exec(function("daily_ledger_cost_map"), env)
    return env


BUILDINGS = {
    "Building 1": {"owned": True, "costs": 450, "type": "tavern"},
    "Building 2": {"owned": True, "costs": 300, "type": "brothel"},
    "Arena": {"owned": True, "costs": 100, "type": "arena"},
    "Academy": {"owned": True, "costs": 999, "type": "academy"},
}


def test_only_owned_buildings_list_is_charged():
    env = load(["Building 1", "Building 2", "Arena"], BUILDINGS)
    assert env["daily_ledger_building_names"]() == ["Building 1", "Building 2", "Arena"]
    assert env["daily_ledger_cost_map"]() == {"Building 1": 450, "Building 2": 300, "Arena": 100}


def test_academy_owned_flag_alone_is_not_a_charge():
    env = load(["Building 1"], BUILDINGS)
    assert "Academy" not in env["daily_ledger_cost_map"]()
    assert sum(env["daily_ledger_cost_map"]().values()) == 450


def test_missing_duplicate_and_bad_entries_are_tolerated():
    buildings = dict(BUILDINGS, Broken={"owned": True, "costs": "n/a"})
    env = load(["Building 1", "Building 1", "Ghost", "Broken", None], buildings)
    assert env["daily_ledger_building_names"]() == ["Building 1", "Broken"]
    assert env["daily_ledger_cost_map"]() == {"Building 1": 450, "Broken": 0}
    env = load(None, buildings)
    assert env["daily_ledger_cost_map"]() == {}


def _maintenance(building, difficulty="normal"):
    env = {"persistent": SimpleNamespace(difficulty=difficulty)}
    exec(function("_fixed_maintenance_ladder_cost"), env)
    exec(function("get_building_base_maintenance_cost"), env)
    return env["get_building_base_maintenance_cost"]("x", building)


def test_governor_castle_level_is_a_gift_not_an_upkeep_bill():
    """The end-game reward arrives at level 5; it pays level-1 upkeep (it cost
    900/day and ran at a loss even when fully staffed)."""
    assert _maintenance({"type": "governor_castle", "base_level": 5}) == 100
    assert _maintenance({"type": "governor_castle", "base_level": 5}, "hard") == 200
    # Every other building keeps the level ladder.
    assert _maintenance({"type": "tavern", "base_level": 5}) == 900


def _maintenance_named(name, building, difficulty="normal"):
    env = {"persistent": SimpleNamespace(difficulty=difficulty)}
    exec(function("_fixed_maintenance_ladder_cost"), env)
    exec(function("get_building_base_maintenance_cost"), env)
    return env["get_building_base_maintenance_cost"](name, building)


def test_first_building_has_no_fixed_upkeep_at_any_level():
    """Balance 2026-10-05: the start was the hardest stretch players reported.
    The player's own premises pay no fixed upkeep (comfort is still charged)."""
    for level in (1, 3, 5):
        assert _maintenance_named("Building 1", {"type": "tavern", "base_level": level}) == 0
        assert _maintenance_named("Building_1", {"type": "brothel", "base_level": level}, "hard") == 0
    assert _maintenance_named("Building 2", {"type": "tavern", "base_level": 1}) == 100


def test_failed_stories_lose_half_and_before_the_easy_floor():
    body = SOURCE.split('earnings = monthly_earnings(earnings, btype.get("id"), profession.get("id"))', 1)[1]
    half = 'earnings = -((abs(earnings) + 1) // 2)'
    assert half in body, "failed daily stories no longer lose half of the formula's loss"
    assert body.index(half) < body.index("earnings = max(earnings, -25)"), (
        "halve the loss BEFORE the Easy -25 floor, or Easy players lose the benefit")
