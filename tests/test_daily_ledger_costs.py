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
