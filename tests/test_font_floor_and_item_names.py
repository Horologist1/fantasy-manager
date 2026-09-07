"""Font-size floor and item-name abbreviation contracts (2026-09-07).

Study result: every hardcoded 16/17 px text in the management UI could go to
18-20 without wrapping, except the Storage compact panel (stats/slot labels at
18 already fill their 116-124 px cells). Equipped item names in that panel
overflowed 136 px even at 18, and Storage rows truncated names by a blind
character count. Both now use a width-aware abbreviation that measures text
with the game font (CaslonAntique) and shortens tier prefixes first.
"""

import json
import re
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"
GAMEPLAY = ROOT / "game" / "scripts" / "core" / "gameplay_improvements.rpy"
GAMEPLAY_UI = ROOT / "game" / "scripts" / "core" / "gameplay_improvements_ui.rpy"
SCRIPT = ROOT / "game" / "scripts" / "script.rpy"
TUTORIAL = ROOT / "game" / "scripts" / "tutorial_system.rpy"
DAILY_EXEC = ROOT / "game" / "scripts" / "events" / "event_daily_exec.rpy"
ITEMS = ROOT / "game" / "data" / "items" / "items.json"
FONT = ROOT / "game" / "gui" / "font" / "CaslonAntique.ttf"


def init_python_function(source: str, name: str) -> str:
    match = re.search(rf"(?ms)^    def {re.escape(name)}\(.*?(?=^    def |^    [A-Z_]+ = |^\S)", source)
    if match is None:
        raise AssertionError(f"{name} not found")
    return textwrap.dedent(match.group(0))


def load_helpers():
    source = GAMEPLAY.read_text(encoding="utf-8")
    table = re.search(r"(?m)^    _CASLON_GLYPH_WIDTHS = \{.*\}\s*$", source)
    if table is None:
        raise AssertionError("_CASLON_GLYPH_WIDTHS table missing")
    namespace = {}
    exec(textwrap.dedent(table.group(0)), namespace)
    tiers = re.search(r"(?m)^    _ITEM_TIER_ABBREVIATIONS = \(.*\)\s*$", source)
    if tiers is None:
        raise AssertionError("_ITEM_TIER_ABBREVIATIONS missing")
    exec(textwrap.dedent(tiers.group(0)), namespace)
    for name in ("compact_table_text", "text_px_width", "abbreviate_item_name"):
        exec(init_python_function(source, name), namespace)
    return namespace


def real_width(text: str, size: int) -> float:
    from PIL import ImageFont
    return ImageFont.truetype(str(FONT), size).getlength(text)


class ItemNameAbbreviationBehaviour(unittest.TestCase):
    def setUp(self):
        ns = load_helpers()
        self.abbr = ns["abbreviate_item_name"]
        self.width = ns["text_px_width"]

    def test_tier_prefix_is_shortened_before_truncating(self):
        self.assertEqual(self.abbr("Elite Diamond Earrings", 136, 18), "E. Diamond Earrings")
        self.assertEqual(self.abbr("Advanced Bartender Apron", 136, 18), "A. Bartender Apron")

    def test_short_names_are_untouched(self):
        self.assertEqual(self.abbr("Basic Heels", 136, 18), "Basic Heels")
        self.assertEqual(self.abbr("", 136, 18), "")
        self.assertEqual(self.abbr(None, 136, 18), "")

    def test_long_names_get_an_ellipsis_not_a_wrap(self):
        out = self.abbr("The Grandmaster's Apron of Culinary Perfection", 136, 18)
        self.assertTrue(out.endswith("…"), out)
        self.assertLessEqual(real_width(out, 18), 136, out)

    def test_every_catalogue_name_fits_both_cells_with_the_real_font(self):
        payload = json.loads(ITEMS.read_text(encoding="utf-8-sig"))
        items = payload if isinstance(payload, list) else payload.get("items", [])
        for item in items:
            name = item.get("name", "")
            for max_px, size in ((136, 18), (184, 24)):
                with self.subTest(name=name, cell=(max_px, size)):
                    out = self.abbr(name, max_px, size)
                    self.assertLessEqual(real_width(out, size), max_px, f"{name!r} -> {out!r}")

    def test_width_model_tracks_the_real_font(self):
        for text in ("Elite Diamond Earrings", "Champion's Hand Wraps", "E 100/100"):
            model, real = self.width(text, 18), real_width(text, 18)
            self.assertLess(abs(model - real) / real, 0.08, (text, model, real))


class FontFloorContracts(unittest.TestCase):
    def test_no_16_or_17_px_text_remains_in_management_screens(self):
        for path in (SCREENS, GAMEPLAY_UI, TUTORIAL):
            source = path.read_text(encoding="utf-8")
            hits = re.findall(r"font_size\((1[0-7])\)|(?<![A-Za-z_])size (1[0-7])\b|\{size=(1[0-7])\}", source)
            self.assertEqual(hits, [], f"{path.name}: sub-18 px text left: {hits}")

    def test_report_footnotes_are_20px(self):
        source = DAILY_EXEC.read_text(encoding="utf-8")
        self.assertNotIn("{{size=18}}", source)
        self.assertGreaterEqual(source.count("{{size=20}}"), 5)

    def test_dead_16px_styles_are_gone(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for style in ("nav_button_text", "roster_button_text", "roster_stats", "roster_button"):
            self.assertNotRegex(source, rf"(?m)^style {style}:", f"dead style {style} still defined")

    def test_storage_uses_width_aware_item_names(self):
        block = re.search(r"(?ms)^screen manager_inventory\(.*?(?=^screen )", SCREENS.read_text(encoding="utf-8")).group(0)
        self.assertNotRegex(block, r'_item_name\[:1\d\] \+ "\.\.\."', "blind character truncation still used for item rows")
        self.assertGreaterEqual(block.count("abbreviate_item_name(_item_name, 184, font_size(24))"), 5)
        self.assertGreaterEqual(block.count("abbreviate_item_name(_slot_value, 136, font_size(18))"), 1)


if __name__ == "__main__":
    unittest.main()
