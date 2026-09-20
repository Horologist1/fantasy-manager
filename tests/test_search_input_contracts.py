"""Search fields must never trap a player behind the on-screen keyboard.

Player report (Android, 2026-09): opening a menu with a search bar raised the
keyboard by itself and there was no way to put it away, while the panel's close
button sits bottom-right, under the keyboard. Every search field is now
tap-to-focus, tap-again-to-dismiss, with a full-screen layer behind the panel
that releases it.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"


class EverySearchFieldIsTapToFocus(unittest.TestCase):
    def setUp(self):
        self.source = SCREENS.read_text(encoding="utf-8")

    def test_no_input_grabs_focus_on_its_own(self):
        raw = re.findall(r'value ScreenVariableInputValue\("(\w+)"\)', self.source)
        self.assertFalse(raw, "these inputs still auto-focus: " + str(raw))

    def test_every_input_value_is_declared_without_default_focus(self):
        declared = re.findall(r'default _fm_search_input = ScreenVariableInputValue\("(\w+)", default=False\)',
                              self.source)
        used = re.findall(r"value _fm_search_input", self.source)
        self.assertEqual(len(declared), len(used),
                         "each screen with a search field declares exactly one value")
        self.assertGreaterEqual(len(declared), 6, declared)

    def test_each_field_sits_in_a_toggle_button(self):
        self.assertEqual(self.source.count("action _fm_search_input.Toggle()"),
                         self.source.count("value _fm_search_input"))

    def test_each_screen_has_a_dismiss_layer(self):
        self.assertEqual(self.source.count("action _fm_search_input.Disable()"),
                         self.source.count("action _fm_search_input.Toggle()"))


if __name__ == "__main__":
    unittest.main()
