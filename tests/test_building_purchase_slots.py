"""Buying a building must never land on a slot that is already occupied.

The map purchase named the new building "Building len(owned_buildings)+1".
That guess collides with a live building as soon as the numbering has a gap —
sell Building 2 and the next map purchase is named "Building 3", which
`add_new_building` then overwrote in place: the old building's type, level,
reputation and staff were replaced by the freshly bought one (player report:
"Brothel A becomes Tavern, both hovers blank, name shows as Tavern: Brothel A").
"""

import re
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "game" / "scripts" / "script.rpy"
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"

FUNCTIONS = (
    "_generic_building_slot_index",
    "_generic_slot_occupied",
    "next_generic_building_slot",
    "add_new_building",
    "register_new_building",
    "purchase_map_building",
)


def load_building_functions(buildings, store):
    """Exec the shipped slot/purchase helpers against a fake store."""
    source = SCRIPT.read_text(encoding="utf-8")
    blocks = []
    for name in FUNCTIONS:
        match = re.search(rf"(?ms)^    def {re.escape(name)}\(.*?\n(?=    \S)", source)
        if match is None:
            raise AssertionError(f"{name} not found in script.rpy")
        blocks.append("\n".join(line[4:] if line.startswith("    ") else line
                                for line in match.group(0).splitlines()))

    notices = []

    class _Renpy(object):
        def log(self, *args):
            notices.append(("log", args[0] if args else ""))

        def notify(self, message):
            notices.append(("notify", message))

        def show_screen(self, name, **kwargs):
            notices.append(("screen", name, kwargs))

    namespace = {
        "re": re,
        "store": store,
        "available_buildings": buildings,
        "renpy": _Renpy(),
        "calculate_reputation": lambda name: None,
        "building_types_json": {"building_types": [{"id": "tavern", "name": "Tavern"}]},
        "_": lambda text: text,
    }
    exec(compile("\n".join(blocks), "building_slots", "exec"), namespace)
    namespace["notices"] = notices
    return namespace


def a_building(btype, **extra):
    data = {
        "price": 10000, "base_level": 3, "type": btype, "owned": True,
        "reputation": 400, "servant_jobs": {"Lyra": "prostitute"},
        "assigned_servants": [], "max_workers": {}, "costs": 0,
        "skill": 30, "skill_bonus": 10, "event_limit": 0,
    }
    data.update(extra)
    return data


class SlotAllocation(unittest.TestCase):
    def setUp(self):
        self.buildings = {
            "Building 1": a_building("tavern"),
            "Building 2": a_building("brothel"),
            "Building 3": a_building("casino"),
        }
        self.store = types.SimpleNamespace(
            money=100000, max_building=50,
            owned_buildings=["Building 1", "Building 2", "Building 3"],
            custom_names={"Building 3": "Brothel A"},
            map_button_buildings={"S2Tavern": "Building 3"},
        )
        self.ns = load_building_functions(self.buildings, self.store)

    def sell_slot_two(self):
        del self.buildings["Building 2"]
        self.store.owned_buildings.remove("Building 2")

    def test_next_slot_fills_the_hole_left_by_a_sale(self):
        self.sell_slot_two()
        # len(owned_buildings) + 1 would have been "Building 3" — an occupied slot.
        self.assertEqual(self.ns["next_generic_building_slot"]()[0], "Building 2")

    def test_add_new_building_refuses_an_occupied_slot(self):
        before = dict(self.buildings["Building 3"])
        self.assertFalse(self.ns["add_new_building"]("Building 3", 15000))
        self.assertEqual(self.buildings["Building 3"], before)

    def test_add_new_building_still_creates_a_free_slot(self):
        self.assertTrue(self.ns["add_new_building"]("Building 4", 40000))
        self.assertEqual(self.buildings["Building 4"]["type"], None)
        self.assertEqual(self.buildings["Building 4"]["price"], 40000)

    def test_map_purchase_after_a_sale_leaves_the_other_building_alone(self):
        self.sell_slot_two()
        ok = self.ns["purchase_map_building"]("PlazaTavern", "tavern", 15000)
        self.assertTrue(ok)

        # the tavern took the free slot, not the live casino in slot 3
        self.assertEqual(self.buildings["Building 2"]["type"], "tavern")
        self.assertEqual(self.buildings["Building 3"]["type"], "casino")
        self.assertEqual(self.buildings["Building 3"]["servant_jobs"], {"Lyra": "prostitute"})
        # and each location keeps its own building
        self.assertEqual(self.store.map_button_buildings["PlazaTavern"], "Building 2")
        self.assertEqual(self.store.map_button_buildings["S2Tavern"], "Building 3")
        self.assertEqual(self.store.money, 85000)

    def test_map_purchase_is_refused_when_money_is_short(self):
        self.store.money = 100
        self.assertFalse(self.ns["purchase_map_building"]("PlazaTavern", "tavern", 15000))
        self.assertEqual(self.store.money, 100)
        self.assertNotIn("PlazaTavern", self.store.map_button_buildings)

    def test_map_purchase_is_refused_when_every_slot_is_taken(self):
        self.store.max_building = 3
        self.assertFalse(self.ns["purchase_map_building"]("PlazaTavern", "tavern", 15000))
        self.assertEqual(self.store.money, 100000)


class PurchaseSourceContracts(unittest.TestCase):
    def setUp(self):
        self.screens = SCREENS.read_text(encoding="utf-8")
        match = re.search(r"(?ms)^screen buy_map_building\(.*?\n(?=^screen )", self.screens)
        self.assertIsNotNone(match, "screen buy_map_building not found")
        self.block = match.group(0)
        # comments may still name the old formula; contracts check the code
        self.code = chr(10).join(line for line in self.block.splitlines()
                                 if not line.lstrip().startswith("#"))

    def test_map_screen_does_not_guess_the_slot_number(self):
        self.assertNotIn("len(owned_buildings)", self.code)
        self.assertNotIn("num + 1", self.code)

    def test_map_screen_buys_through_the_single_entry_point(self):
        self.assertIn("store.purchase_map_building", self.code)
        self.assertNotIn("Function(add_new_building", self.code)

    def test_add_new_building_keeps_its_overwrite_guard(self):
        source = SCRIPT.read_text(encoding="utf-8")
        match = re.search(r"(?ms)^    def add_new_building\(.*?\n(?=    \S)", source)
        self.assertIsNotNone(match)
        self.assertIn("refused to overwrite occupied slot", match.group(0))


if __name__ == "__main__":
    unittest.main()
