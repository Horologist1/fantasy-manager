"""Multi-story day counter in the Daily Report (2026-09-07).

A worker can perform several daily-report stories on one day (reputation
bonus, per-building limit).  Rows now show "Name 2/3" next to the worker and
the details panel adds "Name: story 2 of 3 today"; single-story workers keep
their plain row.  The "N workers active" band segment counted report entries,
not people, and was removed.
"""

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"
GAMEPLAY = ROOT / "game" / "scripts" / "core" / "gameplay_improvements.rpy"
sys.path.insert(0, str(ROOT / "game" / "python-packages"))

from fm_performance.reporting import daily_report_story_positions  # noqa: E402


def entry(worker, building="Tavern", day=None, **extra):
    report = {"worker_name": worker, "building": building, "result": "Success"}
    if day is not None:
        report["_advance_day_index"] = day
    report.update(extra)
    return report


class StoryPositionsBehaviour(unittest.TestCase):
    def test_multi_story_workers_are_numbered_in_report_order(self):
        sage_1, sage_2, sage_3 = entry("Sage"), entry("Sage"), entry("Sage")
        reports = [sage_1, entry("Oak"), sage_2, sage_3]
        positions = daily_report_story_positions(reports)
        self.assertEqual(positions[id(sage_1)], (1, 3))
        self.assertEqual(positions[id(sage_2)], (2, 3))
        self.assertEqual(positions[id(sage_3)], (3, 3))

    def test_any_total_works_including_more_than_three(self):
        # Reputation bonus + no per-building limit can exceed 3; an energy cut can leave 2.
        five = [entry("Rose") for _ in range(5)]
        two = [entry("Lily") for _ in range(2)]
        positions = daily_report_story_positions(five + two)
        self.assertEqual([positions[id(r)] for r in five], [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)])
        self.assertEqual([positions[id(r)] for r in two], [(1, 2), (2, 2)])

    def test_single_story_workers_get_no_counter(self):
        oak = entry("Oak")
        positions = daily_report_story_positions([entry("Sage"), oak, entry("Sage")])
        self.assertNotIn(id(oak), positions)

    def test_refusals_and_policy_incidents_count_as_the_days_stories(self):
        refused = entry("Iris", result="Refused")
        story = entry("Iris")
        positions = daily_report_story_positions([refused, story])
        self.assertEqual(positions[id(refused)], (1, 2))
        self.assertEqual(positions[id(story)], (2, 2))

    def test_archived_multi_day_reports_do_not_merge_days(self):
        day1 = [entry("Sage", day=1), entry("Sage", day=1)]
        day2 = [entry("Sage", day=2)]
        positions = daily_report_story_positions(day1 + day2)
        self.assertEqual(positions[id(day1[0])], (1, 2))
        self.assertEqual(positions[id(day1[1])], (2, 2))
        self.assertNotIn(id(day2[0]), positions)

    def test_same_name_in_different_buildings_is_kept_apart(self):
        tavern = entry("Sage", building="Tavern")
        brothel = entry("Sage", building="Brothel")
        self.assertEqual(daily_report_story_positions([tavern, brothel]), {})

    def test_tolerates_empty_and_malformed_input(self):
        self.assertEqual(daily_report_story_positions(None), {})
        self.assertEqual(daily_report_story_positions([]), {})
        self.assertEqual(daily_report_story_positions(["junk", None, entry("Sage")]), {})


class ScreenContracts(unittest.TestCase):
    def setUp(self):
        self.screens = SCREENS.read_text(encoding="utf-8")
        self.report_block = re.search(r"(?ms)^screen daily_report\(.*?(?=^screen )", self.screens).group(0)
        self.details_block = re.search(r"(?ms)^screen report_details\(.*?(?=^screen |\Z)", self.screens).group(0)

    def test_helper_is_imported_with_the_other_reporting_helpers(self):
        self.assertIn(
            "from fm_performance.reporting import daily_report_story_positions, format_skill_level_badges, report_page_window",
            GAMEPLAY.read_text(encoding="utf-8"),
        )

    def test_daily_report_caches_positions_with_the_filtered_rows(self):
        self.assertIn("default _dr_story_positions = {}", self.report_block)
        self.assertIn("_dr_story_positions = daily_report_story_positions(filtered_reports)", self.report_block)
        # Counter rides in the badge string right after the worker name, before +Lv / skill / HP.
        row = re.search(
            r"_dr_story_pos = _dr_story_positions\.get\(id\(report\)\)\s*\n\s*if _dr_story_pos:\s*\n\s*_dr_badges \+= .*%d/%d.*\n\s*if _report_content_visible and _dr_delta:",
            self.report_block,
        )
        self.assertIsNotNone(row, "counter must be appended to _dr_badges before the delta badges")

    def test_details_panel_shows_the_days_position_under_the_nav_counter(self):
        self.assertIn("_rd_story_pos = daily_report_story_positions(_nav_reports).get(id(report))", self.details_block)
        self.assertRegex(
            self.details_block,
            r'text "Story \[story_number\] of \[total_stories\]".*\n\s*if _rd_story_pos:\s*\n\s*text "\[_rd_worker_display!q\]: story \[_rd_story_pos\[0\]\] of \[_rd_story_pos\[1\]\] today"',
        )

    def test_workers_active_segment_is_gone(self):
        for token in ("_dr_active_n", "_dr_count_label", "workers active", "report entries"):
            self.assertNotIn(token, self.screens, token)
        band = re.search(r'text "\[profit_display\]" size font_size\(24\) color profit_color\n(\s*)(\S+)', self.report_block)
        self.assertIsNotNone(band)
        self.assertEqual(band.group(2), "hbox:", "net profit must be the last item of the summary band")


if __name__ == "__main__":
    unittest.main()
