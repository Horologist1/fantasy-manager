"""Equipped units are never sold or consumed while an unequipped one is available."""
from pathlib import Path
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "game/scripts/script.rpy").read_text(encoding="utf-8")
HELPERS = (ROOT / "game/scripts/core/manager_inventory_helpers.rpy").read_text(encoding="utf-8")


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


def is_equipped(entry):
    return bool(entry[2]) if len(entry) > 2 else False


def make_env(worker_inventory, multiplier=1):
    store = SimpleNamespace(money=0, manager_inventory=[], _is_equipped=is_equipped)
    notices = []
    env = {
        "store": store,
        "renpy": SimpleNamespace(log=lambda m: None, notify=notices.append, restart_interaction=lambda: None,
                                 get_screen_variable=lambda name: multiplier, store=store),
        "items_json": {"items": [{"id": "sword", "name": "Sword", "price": 100}]},
        "manager_inventory": store.manager_inventory,
    }
    exec(function(SCRIPT, "remove_item_from_inventory"), env)
    exec(function(HELPERS, "get_item_sell_price"), env)
    exec(function(HELPERS, "sell_item"), env)
    env["notices"] = notices
    return env


def test_generic_removal_takes_unequipped_units_first():
    env = make_env([])
    inventory = [("sword", 1, True), ("sword", 2, False)]
    env["remove_item_from_inventory"](inventory, "sword", 1)
    assert inventory == [("sword", 1, True), ("sword", 1, False)]
    env["remove_item_from_inventory"](inventory, "sword", 1)
    assert inventory == [("sword", 1, True)]


def test_selling_never_touches_the_equipped_unit():
    env = make_env([], multiplier=10)
    worker = {"name": "Brax", "inventory": [("sword", 1, True), ("sword", 2, False)]}
    env["sell_item"]("sword", worker)
    assert worker["inventory"] == [("sword", 1, True)]
    assert env["store"].money == 100
    env["sell_item"]("sword", worker)
    assert worker["inventory"] == [("sword", 1, True)]
    assert env["store"].money == 100
    assert env["notices"][-1] == "Nothing to sell: unequip it first."
