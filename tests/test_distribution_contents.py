"""What a player build may and may not contain.

Audit 2026-09-20: the 0.9.6.2 packages shipped editorial_delivery/ — internal
audit reports, external review notes and patches — because the build's exclude
list predated that folder. Developer fixtures (test_items.json) had the same
shape of problem in the item catalog.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPTIONS = ROOT / "game" / "scripts" / "core" / "options.rpy"

# Directories that exist in the repo and must never reach a player.
INTERNAL_DIRS = ("docs", "tests", "tools", "devkit", "devkit_web", "editorial_delivery", "backups")


class BuildExcludesInternalMaterial(unittest.TestCase):
    def setUp(self):
        self.source = OPTIONS.read_text(encoding="utf-8")
        self.excluded = set(re.findall(r"build\.classify\('([^']+)',\s*None\)", self.source))

    def test_every_internal_directory_is_excluded(self):
        for name in INTERNAL_DIRS:
            self.assertIn(name + "/**", self.excluded, name + " would ship to players")

    def test_developer_item_fixtures_are_excluded(self):
        self.assertIn("game/data/items/test_items.json", self.excluded)

    def test_the_guarded_directories_still_exist(self):
        present = [name for name in INTERNAL_DIRS if (ROOT / name).is_dir()]
        self.assertTrue(present, "update INTERNAL_DIRS if the repo layout changed")


if __name__ == "__main__":
    unittest.main()
