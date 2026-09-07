"""UI polish contracts (2026-09-06, after the user's in-game smoke).

1. Help book columns: left column 10 px further right, right column 20 px
   further left than the first positioned layout, then 60 px more (xpos 90 / 770).
2. Generic tooltip text is readable (size 24) and its wrap width and the
   mouse-avoidance width stay in step.
3. The "Skipping" indicator only appears while dialogue is on screen: holding
   Ctrl for Ctrl+Arrow navigation in management screens must not show it.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"


def screen_block(source: str, name: str) -> str:
    match = re.search(rf"(?m)^screen {re.escape(name)}\b[^\n]*:\n", source)
    if match is None:
        raise AssertionError(f"screen {name} not found")
    following = re.search(r"(?m)^(screen|transform|style|init|label|define|default) ", source[match.end():])
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


class HelpColumnsContracts(unittest.TestCase):
    def setUp(self):
        self.source = SCREENS.read_text(encoding="utf-8")

    def test_both_help_pages_use_the_adjusted_column_positions(self):
        for name in ("keyboard_help", "mouse_help"):
            block = screen_block(self.source, name)
            with self.subTest(screen=name):
                xpos = re.findall(r"(?m)^\s+xpos (\d+)\s*$", block)
                self.assertEqual(xpos, ["90", "770"], f"{name}: expected left xpos 90 and right xpos 770, found {xpos}")


class TooltipContracts(unittest.TestCase):
    def setUp(self):
        self.block = screen_block(SCREENS.read_text(encoding="utf-8"), "tooltip")

    def test_tooltip_text_size_is_readable(self):
        sizes = re.findall(r"(?m)^\s+size (\d+)\s*$", self.block)
        self.assertEqual(sizes, ["24"], f"tooltip text size must be 24, found {sizes}")

    def test_tooltip_wrap_width_matches_positioning_width(self):
        wrap = re.findall(r"xmaximum (\d+)", self.block)
        avoid = re.findall(r"tooltip_max_width = (\d+)", self.block)
        self.assertEqual(wrap, ["380"], wrap)
        self.assertEqual(avoid, ["380"], avoid)


class SkipIndicatorContracts(unittest.TestCase):
    def test_skip_indicator_only_renders_during_dialogue(self):
        block = screen_block(SCREENS.read_text(encoding="utf-8"), "skip_indicator")
        gate = re.search(r'(?m)^\s+if config\.skipping and \(renpy\.get_screen\("say"\) or renpy\.get_screen\("nvl"\)\):', block)
        self.assertIsNotNone(
            gate,
            "skip_indicator must be gated on dialogue being on screen: holding Ctrl for "
            "Ctrl+Arrow navigation sets config.skipping even in management screens.",
        )
        self.assertLess(gate.start(), block.index("frame:"), "the gate must wrap the frame")


if __name__ == "__main__":
    unittest.main()
