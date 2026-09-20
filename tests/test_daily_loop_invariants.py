"""Invariants of the day loop: one charge, one date advance, one report.

Audit 2026-09-20, block 1 (economy and day). The day is the place where a
"second traversal of the same truth" costs the player money, and where an early
return can skip a step the rest of the game assumes happened.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAILY = ROOT / "game" / "scripts" / "events" / "event_daily_exec.rpy"
MAIN_FLOW = ROOT / "game" / "scripts" / "main_flow.rpy"
BUILDING_TYPES = ROOT / "game" / "data" / "buildings" / "building_types.json"

DAY_PATHS = (
    "next_day/no_event",
    "handle_event_then_daily_report",
    "governor_retaliation flow",
    "governor_tension flow",
)


def function_source(path, name):
    """Body of one `    def name(...)` inside an init python block, to EOF if last."""
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


class TheDayChargesTheLedgerOnce(unittest.TestCase):
    def setUp(self):
        self.body = function_source(DAILY, "process_next_day")

    def test_the_charge_comes_from_the_ledger(self):
        self.assertIn("daily_ledger_cost_map()", self.body)

    def test_no_second_traversal_of_building_costs(self):
        # the old loop summed available_buildings again, so the report and the
        # charge could disagree
        self.assertNotIn("total_building_costs += building.get('costs', 0)", self.body)

    def test_money_is_applied_as_a_delta_read_at_the_moment_of_the_charge(self):
        capture = self.body.index('old_money = int(getattr(store, "money", 0) or 0)')
        apply = self.body.index("store.money = old_money + total_income - total_building_costs")
        between = self.body[capture:apply]
        self.assertEqual(between.count("\n"), 1, "money must be read immediately before it is written")


class TheDateAdvancesExactlyOnce(unittest.TestCase):
    def test_advance_date_has_a_single_call_site(self):
        whole = DAILY.read_text(encoding="utf-8")
        self.assertEqual(whole.count("advance_date()"), 1)

    def test_no_early_return_can_skip_the_advance(self):
        body = function_source(DAILY, "process_next_day")
        advance = body.index("advance_date()")
        early = body[:advance]
        returns = [line.strip() for line in early.splitlines() if line.strip().startswith("return ")]
        # the only return allowed before the date moves is the bankruptcy game over
        self.assertTrue(all("game_over" in line for line in returns), returns)


class EveryDayEndRunsTheStartOfDayAutomation(unittest.TestCase):
    def test_all_four_day_endings_call_it(self):
        flow = MAIN_FLOW.read_text(encoding="utf-8")
        for context in DAY_PATHS:
            self.assertIn('run_start_of_day_automation("' + context + '")', flow)


class TheReportIsRebuiltEachDay(unittest.TestCase):
    def test_the_reset_is_declared_global(self):
        # `daily_report = []` inside a function without `global` would silently
        # create a local and leave yesterday's entries (and income) in place
        body = function_source(DAILY, "process_next_day")
        self.assertIn("daily_report = []", body)
        self.assertRegex(body, r"global [^\n]*\bdaily_report\b")

    def test_the_writer_declares_it_too(self):
        body = function_source(DAILY, "process_daily_events")
        self.assertRegex(body, r"global [^\n]*\bdaily_report\b")


class AuthoredStoryCountsCannotBreakTheDay(unittest.TestCase):
    def test_every_profession_declares_a_usable_daily_story_count(self):
        data = json.loads(BUILDING_TYPES.read_text(encoding="utf-8"))
        for building in data.get("building_types", []):
            for profession in building.get("professions", []):
                value = profession.get("daily_story_count", 0)
                label = str(building.get("id")) + "/" + str(profession.get("id"))
                if isinstance(value, dict):
                    self.assertIsInstance(value.get("base", 0), int, label + " base")
                    self.assertIsInstance(value.get("bonus_formula", "0"), str, label + " bonus_formula")
                else:
                    self.assertIsInstance(value, int, label + " daily_story_count")

    def test_the_engine_tolerates_a_bad_value_anyway(self):
        body = function_source(DAILY, "process_daily_events")
        chunk = body[body.index("events_per_worker = int(daily_story_count)") - 400:]
        self.assertIn("except (TypeError, ValueError)", chunk)


if __name__ == "__main__":
    unittest.main()
