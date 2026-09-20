"""Invariants of the building slot lifecycle: buy, retype, sell.

Audit 2026-09-20. The purchase path is covered by test_building_purchase_slots;
this file pins what the other two ends of the lifecycle must leave behind. A
slot lives in five places at once (available_buildings, owned_buildings,
custom_names, map_button_buildings and every worker's assigned_building), and a
step that forgets one of them is what produces "two locations, one building".
"""

import re
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "game" / "scripts" / "script.rpy"
BUILDING_LOGIC = ROOT / "game" / "scripts" / "buildings" / "building_logic.rpy"
MAIN_FLOW = ROOT / "game" / "scripts" / "main_flow.rpy"

# Fields the daily loop and the UI read off a building, some with bracket access
# (script.rpy: building["base_level"], building["servant_jobs"], ...). Every
# creator must provide them or day-end raises on that building.
CORE_FIELDS = {
    "price", "base_level", "type", "assigned_servants", "servant_jobs",
    "reputation", "costs", "owned", "skill", "skill_bonus",
}


def extract(path, names):
    source = path.read_text(encoding="utf-8")
    blocks = []
    for name in names:
        match = re.search(r"(?ms)^    def " + re.escape(name) + r"\(.*?\n(?=    \S)", source)
        if match is None:
            raise AssertionError(name + " not found in " + path.name)
        blocks.append("\n".join(line[4:] if line.startswith("    ") else line
                                for line in match.group(0).splitlines()))
    return "\n".join(blocks)


def build_namespace(buildings, store, extra=None):
    unassigned = []

    class _Renpy(object):
        def log(self, *args):
            pass

        def notify(self, *args, **kwargs):
            pass

    def _unassign(worker):
        worker["assigned_building"] = "Unassigned"
        unassigned.append(worker.get("name"))

    namespace = {
        "re": re,
        "store": store,
        "available_buildings": buildings,
        "renpy": _Renpy(),
        "_": lambda text: text,
        "unassign_worker": _unassign,
        "sync_building_assignments_from_workers": lambda: None,
        "calculate_reputation": lambda name: None,
    }
    namespace.update(extra or {})
    namespace["unassigned"] = unassigned
    return namespace


def a_building(btype="brothel", **extra):
    data = {
        "price": 30000, "base_level": 3, "type": btype, "owned": True,
        "reputation": 400, "servant_jobs": {"Lyra": "prostitute"},
        "assigned_servants": [], "max_workers": {}, "costs": 0,
        "skill": 30, "skill_bonus": 10, "event_limit": 0,
    }
    data.update(extra)
    return data


class SellLeavesNoDanglingReference(unittest.TestCase):
    def setUp(self):
        self.buildings = {"Building 1": a_building("tavern"), "Building 2": a_building("brothel")}
        self.worker = {"name": "Lyra", "assigned_building": "Building 2"}
        self.store = types.SimpleNamespace(
            money=1000, max_building=50, workers=[self.worker],
            owned_buildings=["Building 1", "Building 2"],
            custom_names={"Building 1": "The Tavern", "Building 2": "Brothel A"},
            map_button_buildings={"S2Tavern": "Building 1", "S4Redhouse": "Building 2"},
            buildings_owned=2, current_affected_building="Building 2",
        )
        self.ns = build_namespace(self.buildings, self.store)
        exec(compile(extract(SCRIPT, (
            "_generic_building_slot_index", "_normalize_building_key_for_match",
            "_alternate_building_key", "_resolve_building_key", "sell_building",
            "sellable_generic_building_names",
        )), "sell", "exec"), self.ns)

    def test_sale_clears_every_structure_that_names_the_slot(self):
        self.assertTrue(self.ns["sell_building"]("Building 2"))
        self.assertNotIn("Building 2", self.buildings)
        self.assertNotIn("Building 2", self.store.owned_buildings)
        self.assertNotIn("Building 2", self.store.custom_names)
        # the freed location must stop pointing at the sold slot, or the next
        # purchase that reuses the number shows up in two places at once
        self.assertNotIn("Building 2", self.store.map_button_buildings.values())
        self.assertEqual(self.worker["assigned_building"], "Unassigned")
        self.assertIsNone(self.store.current_affected_building)
        self.assertEqual(self.store.money, 1000 + 25000)

    def test_sale_accepts_the_underscore_spelling_of_the_same_slot(self):
        self.buildings["Building_2"] = self.buildings.pop("Building 2")
        self.store.owned_buildings = ["Building 1", "Building_2"]
        self.assertTrue(self.ns["sell_building"]("Building 2"))
        self.assertNotIn("Building_2", self.buildings)
        self.assertNotIn("Building_2", self.store.owned_buildings)

    def test_first_building_and_unknown_slots_are_refused(self):
        self.assertFalse(self.ns["sell_building"]("Building 1"))
        self.assertFalse(self.ns["sell_building"]("Castle"))
        self.assertIn("Building 1", self.buildings)
        self.assertEqual(self.store.money, 1000)


class RetypeIsSafeOnEverySlotShape(unittest.TestCase):
    def setUp(self):
        self.buildings = {"Building_2": a_building("brothel")}
        self.store = types.SimpleNamespace(workers=[], owned_buildings=["Building_2"])
        self.ns = build_namespace(self.buildings, self.store)
        exec(compile(extract(SCRIPT, (
            "_alternate_building_key", "_resolve_building_key",
        )), "keys", "exec"), self.ns)
        exec(compile(extract(BUILDING_LOGIC, ("change_building_type",)), "retype", "exec"), self.ns)

    def test_retype_resolves_the_alternate_key_instead_of_doing_nothing(self):
        # the caller charges $1000 before this runs, so a silent miss is a theft
        self.assertTrue(self.ns["change_building_type"]("Building 2"))
        self.assertIsNone(self.buildings["Building_2"]["type"])
        self.assertEqual(self.buildings["Building_2"]["base_level"], 1)
        self.assertEqual(self.buildings["Building_2"]["servant_jobs"], {})

    def test_retype_survives_a_building_without_staff_keys(self):
        self.buildings["Building_2"] = {"type": "brothel", "base_level": 2}
        self.assertTrue(self.ns["change_building_type"]("Building 2"))
        self.assertEqual(self.buildings["Building_2"]["servant_jobs"], {})

    def test_retype_reports_a_missing_building(self):
        self.assertFalse(self.ns["change_building_type"]("Building 9"))


class EveryCreatorProducesAWholeBuilding(unittest.TestCase):
    """A slot that reaches owned_buildings without these fields breaks day-end."""

    def literal_fields(self, source, anchor):
        """Field names of the dict literal that starts at `anchor` (brace-matched)."""
        start = source.index(anchor)
        opening = source.index("{", start)
        depth = 0
        for index in range(opening, len(source)):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    return set(re.findall(r'"(\w+)":', source[opening:index]))
        raise AssertionError("unbalanced literal after " + anchor)

    def test_all_creators_agree_on_the_core_fields(self):
        script = SCRIPT.read_text(encoding="utf-8")
        main_flow = MAIN_FLOW.read_text(encoding="utf-8")

        creators = {
            "add_new_building": self.literal_fields(script, "available_buildings[name] = {"),
            "default Building 1": self.literal_fields(script, "default available_buildings = {"),
            "Arena": self.literal_fields(script, 'available_buildings["Arena"] = {'),
        }
        for label, fields in creators.items():
            missing = sorted(CORE_FIELDS - fields)
            self.assertFalse(missing, label + " is missing " + str(missing))

        # the castle is assembled field by field rather than as a literal
        castle = set(re.findall(r'castle(?:\.setdefault\(|\[)"(\w+)"', main_flow))
        missing = sorted(CORE_FIELDS - castle)
        self.assertFalse(missing, "castle unlock is missing " + str(missing))


class PaidOperationsAreAtomic(unittest.TestCase):
    """Money moves with the operation or not at all (LA BIBLIA 19.3)."""

    def setUp(self):
        self.buildings = {"Building 2": a_building("brothel")}
        self.store = types.SimpleNamespace(money=20000, workers=[], owned_buildings=["Building 2"],
                                           custom_names={}, academy_enrolled=False)
        self.ns = build_namespace(self.buildings, self.store)
        exec(compile(extract(SCRIPT, (
            "_alternate_building_key", "_resolve_building_key",
            "add_academy_building", "pay_academy_tuition",
        )), "paid_script", "exec"), self.ns)
        exec(compile(extract(BUILDING_LOGIC, (
            "change_building_type", "change_building_type_paid",
        )), "paid_logic", "exec"), self.ns)

    def test_retype_charges_only_when_it_happens(self):
        self.assertTrue(self.ns["change_building_type_paid"]("Building 2", 1000))
        self.assertEqual(self.store.money, 19000)
        self.assertIsNone(self.buildings["Building 2"]["type"])

    def test_retype_of_a_missing_building_is_free(self):
        self.assertFalse(self.ns["change_building_type_paid"]("Building 7", 1000))
        self.assertEqual(self.store.money, 20000)

    def test_retype_without_funds_changes_nothing(self):
        self.store.money = 500
        self.assertFalse(self.ns["change_building_type_paid"]("Building 2", 1000))
        self.assertEqual(self.store.money, 500)
        self.assertEqual(self.buildings["Building 2"]["type"], "brothel")

    def test_tuition_creates_the_academy_once(self):
        self.assertTrue(self.ns["pay_academy_tuition"](15000))
        self.assertIn("Academy", self.buildings)
        self.assertEqual(self.store.money, 5000)
        self.assertTrue(self.store.academy_enrolled)

    def test_tuition_is_never_charged_twice(self):
        self.ns["pay_academy_tuition"](15000)
        self.store.money = 20000
        self.store.academy_enrolled = False  # the flag the guard is meant to repair
        self.assertFalse(self.ns["pay_academy_tuition"](15000))
        self.assertEqual(self.store.money, 20000)
        self.assertTrue(self.store.academy_enrolled)

    def test_tuition_without_funds_enrols_nobody(self):
        self.store.money = 1000
        self.assertFalse(self.ns["pay_academy_tuition"](15000))
        self.assertNotIn("Academy", self.buildings)
        self.assertEqual(self.store.money, 1000)


class TheCastleHasOneUnlockImplementation(unittest.TestCase):
    """Every path that grants the castle must produce the same building."""

    def test_no_inline_copy_of_the_unlock(self):
        for path in (ROOT / "game" / "scripts").rglob("*.rpy"):
            source = path.read_text(encoding="utf-8")
            if "unlock_governor_castle" in source and path.name != "main_flow.rpy":
                self.assertNotIn('available_buildings[castle_name]["type"] = "governor_castle"', source,
                                 path.name + " rebuilds the castle instead of calling the helper")

    def test_the_castle_is_granted_at_the_shared_ceiling(self):
        lines = MAIN_FLOW.read_text(encoding="utf-8").splitlines()
        start = next(index for index, line in enumerate(lines)
                     if line.startswith("    def unlock_governor_castle"))
        end = next((index for index in range(start + 1, len(lines))
                    if lines[index].strip()
                    and not lines[index].startswith("     ")
                    and (lines[index].startswith("    ") or not lines[index].startswith(" "))),
                   len(lines))
        helper = chr(10).join(lines[start:end])
        self.assertIn('castle["base_level"] = MAX_BUILDING_LEVEL', helper)
        self.assertNotIn('setdefault("base_level"', helper)

    def test_every_grant_goes_through_the_helper(self):
        calls = 0
        for path in (ROOT / "game" / "scripts").rglob("*.rpy"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if "unlock_governor_castle(" in line and "def " not in line:
                    calls += 1
        self.assertGreaterEqual(calls, 4, "the ending paths and the tutorial must all call it")


if __name__ == "__main__":
    unittest.main()
