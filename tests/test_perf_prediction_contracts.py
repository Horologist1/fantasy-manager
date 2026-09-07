"""Source contracts for the roster-size performance fix (2026-09-06).

Ren'Py predicts every Show(...) action of every visible button at the start of
each interaction, running the target screen's whole body. With one
`Show("worker_details", ...)` per roster row that cost 2.2 s per click at 50
workers. These contracts pin the three pieces of the fix so a later edit cannot
silently reintroduce it.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"

HUD_BLINK_SCREENS = ("tavern", "map_screen", "Manager", "manager_inventory")


def screen_block(source: str, name: str) -> str:
    match = re.search(rf"(?m)^screen {re.escape(name)}\b[^\n]*:\n", source)
    if match is None:
        raise AssertionError(f"screen {name} not found")
    following = re.search(r"(?m)^screen [A-Za-z0-9_]+", source[match.end():])
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


def top_level_block_before(source: str, index: int) -> str:
    """Return the header line of the innermost top-level block that contains index."""
    headers = list(re.finditer(r"(?m)^(init(?: -?\d+)? python|screen|label|transform|style|define|default)\b[^\n]*", source[:index]))
    return headers[-1].group(0) if headers else ""


class WorkerDetailsPredictionContracts(unittest.TestCase):
    def setUp(self):
        self.source = SCREENS.read_text(encoding="utf-8")
        self.block = screen_block(self.source, "worker_details")

    def test_worker_details_is_excluded_from_prediction(self):
        header_end = self.block.index("\n") + 1
        leading = [
            line.strip() for line in self.block[header_end:].splitlines()
            if line.strip() and not line.strip().startswith("#")
        ][:3]
        self.assertIn(
            "predict False",
            leading,
            "screen worker_details must declare `predict False` up front: every roster "
            "and Manager row shows it via Show(...), so the engine otherwise evaluates "
            "the whole screen once per row on every interaction.",
        )

    def test_worker_details_image_lookups_run_on_click_not_on_build(self):
        eager = re.findall(r'SetScreenVariable\(\s*"current_image"\s*,\s*get_worker_image', self.block)
        self.assertEqual(
            eager,
            [],
            "worker_details evaluates get_worker_image_safe(...) as an action argument, "
            "i.e. once per skill button on every screen build; route it through "
            "Function(set_worker_details_image, ...) so it only runs when clicked.",
        )
        self.assertTrue(
            "Function(set_worker_details_image" in self.block,
            "worker_details must resolve click images through set_worker_details_image",
        )

    def test_lazy_image_helper_is_an_init_python_module_function(self):
        match = re.search(r"(?m)^    def set_worker_details_image\(", self.source)
        self.assertIsNotNone(match, "set_worker_details_image must be defined at init python level")
        header = top_level_block_before(self.source, match.start())
        self.assertTrue(
            header.startswith("init"),
            f"set_worker_details_image must live in an init python block (BIBLIA §8), found under: {header!r}",
        )


class HudNameBlinkContracts(unittest.TestCase):
    def setUp(self):
        self.source = SCREENS.read_text(encoding="utf-8")

    def test_blink_no_longer_restarts_the_interaction(self):
        self.assertFalse(
            'ToggleVariable("manager_name_blink_highlight")' in self.source,
            "the 0.7s repeat timer + ToggleVariable restarts the interaction (and the "
            "prediction pass of every visible screen) every 0.7s while skill points are unspent.",
        )
        self.assertFalse("manager_name_blink_highlight" in self.source, "dead blink variable still referenced")

    def test_blink_is_an_atl_transform(self):
        match = re.search(r"(?ms)^transform manager_name_blink:\n(.*?)(?=^\S)", self.source)
        self.assertIsNotNone(match, "transform manager_name_blink must exist")
        body = match.group(1)
        self.assertIn("matrixcolor", body)
        self.assertIn("pause 0.7", body)
        self.assertIn("repeat", body)

    def test_every_hud_screen_uses_the_transform_behind_the_same_gate(self):
        for name in HUD_BLINK_SCREENS:
            block = screen_block(self.source, name)
            with self.subTest(screen=name):
                self.assertTrue("manager_name_blink" in block, f"{name}: HUD name must use manager_name_blink")
                self.assertTrue("manager_has_unspent_skill_points()" in block, f"{name}: blink must stay gated on unspent points")
                self.assertFalse("timer 0.7 repeat True" in block, f"{name}: the interaction-restarting timer is back")


if __name__ == "__main__":
    unittest.main()
