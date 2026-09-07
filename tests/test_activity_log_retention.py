"""Worker activity_log retention (2026-09-06).

100 days of per-worker history was ~97 % of every worker's saved state
(~150 KB per worker) and made the save snapshot 24 MB with 50 workers. The
retention is now 10 days; the writer slice, the History grouping slice and the
popup caption must keep saying the same number.
"""

import re
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
GAMEPLAY = ROOT / "game" / "scripts" / "core" / "gameplay_improvements.rpy"
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"

EXPECTED_DAYS = 10


def init_python_function(source: str, name: str) -> str:
    """Return the dedented source of a 4-space-indented def inside an init python block."""
    match = re.search(rf"(?ms)^    def {name}\(.*?(?=^    def |^\S)", source)
    if match is None:
        raise AssertionError(f"{name} not found")
    return textwrap.dedent(match.group(0))


def trailing_slice(body: str) -> int:
    matches = re.findall(r"\[-(\d+):\]", body)
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one [-N:] retention slice, found {matches}")
    return int(matches[0])


class ActivityLogRetentionContracts(unittest.TestCase):
    def setUp(self):
        self.gameplay = GAMEPLAY.read_text(encoding="utf-8")
        self.screens = SCREENS.read_text(encoding="utf-8")

    def test_writer_keeps_ten_days(self):
        body = init_python_function(self.gameplay, "add_worker_activity_items")
        self.assertEqual(trailing_slice(body), EXPECTED_DAYS)

    def test_history_grouping_keeps_the_same_number_of_days(self):
        body = init_python_function(self.gameplay, "get_worker_activity_entries")
        self.assertEqual(trailing_slice(body), EXPECTED_DAYS)

    def test_history_popup_caption_matches(self):
        captions = re.findall(r"Worker Activity Log - Last (\d+) days", self.screens)
        self.assertEqual(captions, [str(EXPECTED_DAYS)])


class ActivityLogWriterBehaviour(unittest.TestCase):
    """Run the real add_worker_activity_items with a stub store and clock."""

    def setUp(self):
        source = GAMEPLAY.read_text(encoding="utf-8")
        body = init_python_function(source, "add_worker_activity_items")
        self.days = trailing_slice(body)
        self.clock = {"day": 1}
        namespace = {
            "store": SimpleNamespace(current_day=1, current_month=1, current_year=1),
            "calculate_total_days": lambda: self.clock["day"],
        }
        exec(body, namespace)
        self.add_items = namespace["add_worker_activity_items"]

    def test_only_the_newest_days_are_kept(self):
        worker = {"name": "Probe"}
        for day in range(1, 31):
            self.clock["day"] = day
            self.assertTrue(self.add_items(worker, "stats", [f"Energy: {day}"]))
        log = worker["activity_log"]
        self.assertEqual(len(log), EXPECTED_DAYS)
        self.assertEqual([entry["day"] for entry in log], list(range(31 - EXPECTED_DAYS, 31)))

    def test_same_day_items_merge_into_one_entry(self):
        worker = {"name": "Probe"}
        self.clock["day"] = 5
        self.add_items(worker, "stats", ["Energy: 5"])
        self.add_items(worker, "progress", ["Charm skill: 1 -> 2."])
        self.assertEqual(len(worker["activity_log"]), 1)
        self.assertEqual(len(worker["activity_log"][0]["items"]), 2)

    def test_legacy_hundred_day_log_is_trimmed_on_next_write(self):
        worker = {"name": "Legacy", "activity_log": [
            {"day": day, "date": f"{day}/1/1", "items": [{"category": "stats", "text": "x"}]}
            for day in range(1, 101)
        ]}
        self.clock["day"] = 101
        self.add_items(worker, "stats", ["Energy: 101"])
        self.assertEqual(len(worker["activity_log"]), EXPECTED_DAYS)
        self.assertEqual(worker["activity_log"][-1]["day"], 101)


if __name__ == "__main__":
    unittest.main()
