"""Building level has one ceiling, MAX_BUILDING_LEVEL, and no upgrade can be sold past it."""
from pathlib import Path
import re
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "game/scripts/script.rpy").read_text(encoding="utf-8")


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


def upgrade(level, money):
    notices = []
    buildings = {"Building 1": {"base_level": level, "reputation": 0}}
    env = {"available_buildings": buildings, "store": SimpleNamespace(money=money), "custom_names": {},
           "renpy": SimpleNamespace(notify=notices.append, log=lambda m: None),
           "calculate_reputation": lambda name: None, "MAX_BUILDING_LEVEL": 5}
    exec(function(SCRIPT, "get_building_upgrade_cost"), env)
    exec(function(SCRIPT, "upgrade_building"), env)
    env["upgrade_building"]("Building 1")
    return buildings["Building 1"]["base_level"], env["store"].money, notices


def test_upgrade_below_the_ceiling_charges_and_raises_the_level():
    assert upgrade(4, 20000) == (5, 4000, ["Upgraded Building 1 to level 5!"])


def test_upgrade_at_the_ceiling_is_refused_and_charges_nothing():
    level, money, notices = upgrade(5, 100000)
    assert (level, money) == (5, 100000)
    assert notices == ["This building is already at its maximum level."]


def test_every_building_level_ceiling_uses_the_constant():
    sources = {path: (ROOT / path).read_text(encoding="utf-8") for path in
               ("game/scripts/core/screens.rpy", "game/scripts/events/event_daily_exec.rpy", "game/scripts/script.rpy")}
    assert "max_level = MAX_BUILDING_LEVEL" in sources["game/scripts/core/screens.rpy"]
    assert 'min(building["base_level"], MAX_BUILDING_LEVEL)' in sources["game/scripts/events/event_daily_exec.rpy"]
    assert re.search(r"define MAX_BUILDING_LEVEL = 5", sources["game/scripts/script.rpy"])
    for path, text in sources.items():
        for number, line in enumerate(text.splitlines(), 1):
            if "base_level" in line and re.search(r"(min\(|>=|<=|==)\s*5\b|\b5\)", line) and "MAX_BUILDING_LEVEL" not in line:
                if "castle" in line:
                    continue  # the Governor's Castle is created at max level on purpose
                raise AssertionError("literal level ceiling at %s:%d: %s" % (path, number, line.strip()))
