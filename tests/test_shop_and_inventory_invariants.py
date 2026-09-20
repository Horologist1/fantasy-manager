"""Shop and inventory invariants.

Audit 2026-09-20, block 2 (inventory and items). The catalog ships developer
fixtures (test_money_50k, test_manager_level, test_unlock_shop2/3, the trait
rings) priced at $1. roll_loot has always filtered them; the shop only hid them
behind a "Toggle test items" button that every player could see and click.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "game" / "scripts" / "script.rpy"
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"
HELPERS = ROOT / "game" / "scripts" / "core" / "manager_inventory_helpers.rpy"
OPTIONS = ROOT / "game" / "scripts" / "core" / "options.rpy"
ITEM_DIR = ROOT / "game" / "data" / "items"

SHOP_MODES = ("shop1", "shop2", "shop3")


def function_source(path, name):
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((index for index, line in enumerate(lines)
                  if line.startswith("    def " + name + "(")), None)
    if start is None:
        raise AssertionError(name + " not found in " + path.name)
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.strip() and not line.startswith("     ") and line.startswith("    "):
            end = index
            break
    return "\n".join(lines[start:end])


def load_catalog():
    items, excluded = [], []
    for path in sorted(ITEM_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            items.extend(data.get("items", []))
            excluded.extend(data.get("excluded_from_shops", []))
    return items, excluded


def load_shop_rules(dev_enabled):
    """Exec the shipped shop-availability rules against a stub store."""
    source = "\n".join(
        "\n".join(line[4:] if line.startswith("    ") else line
                  for line in function_source(SCRIPT, name).splitlines())
        for name in ("_is_dev_only_item", "item_fits_shop_price_band", "is_item_available_in_shop")
    )

    class _Store(object):
        current_day = 3

    namespace = {
        "os": __import__("os"),
        "hashlib": __import__("hashlib"),
        "random": __import__("random"),
        "store": _Store(),
        "persistent": type("P", (), {"fm_dev_items": dev_enabled})(),
        "config": type("C", (), {"developer": True})(),
        "item_content_is_visible": lambda item: True,
        "dev_items_enabled": lambda: dev_enabled,
    }
    exec(compile(source, "shop_rules", "exec"), namespace)
    return namespace


class DeveloperItemsNeverReachAPlayer(unittest.TestCase):
    def setUp(self):
        self.items, self.excluded = load_catalog()
        self.dev_items = [item for item in self.items
                          if "test" in item["id"].lower() or "debug" in item["id"].lower()]

    def test_the_catalog_still_ships_the_fixtures_this_guards(self):
        self.assertTrue(self.dev_items, "no dev fixtures found; update this test if they were removed")

    def test_no_shop_lists_them_by_default(self):
        rules = load_shop_rules(dev_enabled=False)
        for item in self.dev_items:
            for mode in SHOP_MODES:
                self.assertFalse(rules["is_item_available_in_shop"](item, mode),
                                 item["id"] + " is on sale in " + mode)

    def test_a_developer_can_still_get_them(self):
        rules = load_shop_rules(dev_enabled=True)
        listed = [item["id"] for item in self.dev_items
                  if any(rules["is_item_available_in_shop"](item, mode) for mode in SHOP_MODES)]
        self.assertTrue(listed, "developer machines must keep the fixtures usable")

    def test_ordinary_items_are_unaffected(self):
        rules = load_shop_rules(dev_enabled=False)
        normal = [item for item in self.items
                  if item not in self.dev_items and item["id"] not in self.excluded
                  and int(item.get("price", 0) or 0) > 0]
        listed = [item["id"] for item in normal
                  if any(rules["is_item_available_in_shop"](item, mode) for mode in SHOP_MODES)]
        self.assertGreater(len(listed), 50, "the filter must not empty the shops")

    def test_the_toggle_button_is_developer_only(self):
        screens = SCREENS.read_text(encoding="utf-8")
        self.assertIn("if shop_mode and store.dev_items_enabled():", screens)

    def test_loot_keeps_its_own_filter(self):
        body = function_source(SCRIPT, "roll_loot")
        self.assertIn('"test" in item_id or "debug" in item_id', body)

    def test_the_dev_item_file_is_out_of_distributions(self):
        options = OPTIONS.read_text(encoding="utf-8")
        self.assertIn("build.classify('game/data/items/test_items.json', None)", options)


class SellingCannotPayForEquippedUnits(unittest.TestCase):
    def test_availability_skips_equipped_stacks(self):
        helpers = HELPERS.read_text(encoding="utf-8")
        sell = helpers[helpers.index("def sell_item("):]
        sell = sell[:sell.index("\n    def ", 10)]
        self.assertIn("store._is_equipped(item)", sell)
        paid = sell.index("store.money += sell_price * actual_qty")
        guard = sell.index("if actual_qty > 0:")
        self.assertLess(guard, paid, "the payout must sit inside the availability guard")

    def test_transfer_unequips_before_moving(self):
        helpers = HELPERS.read_text(encoding="utf-8")
        transfer = helpers[helpers.index("def transfer_to_right"):]
        transfer = transfer[:transfer.index("\n    def ", 10)]
        unequip = transfer.index("remove_item_effects")
        add = transfer.index("add_item_to_inventory(target_inventory")
        self.assertLess(unequip, add, "effects must come off before the item leaves the worker")


class RemovalPrefersUnequippedStacks(unittest.TestCase):
    def test_ordering_is_explicit(self):
        body = function_source(SCRIPT, "remove_item_from_inventory")
        self.assertIn("ordered_indices", body)
        self.assertIn("not _entry_equipped", body)


if __name__ == "__main__":
    unittest.main()
