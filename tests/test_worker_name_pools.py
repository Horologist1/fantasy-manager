"""Procedural naming must never mint a worker literally called "Unknown".

A template can carry `names_list: null` (the web devkit and the WM converter
both emit it) or a key this build's names.json does not define. `dict.get`
only substitutes its default for a MISSING key, so those templates fell
through to the literal ["Unknown"] pool and put "Unknown" (then "Unknown 1",
...) on the player's roster. These tests pin the resolver and the shipped data.
"""

import json
import random
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "game" / "scripts" / "script.rpy"
NAMES = ROOT / "game" / "data" / "names.json"
WORKER_DIR = ROOT / "game" / "data" / "workers"


def load_resolver():
    """Exec the shipped resolve_name_pool with the real name pools behind it."""
    source = SCRIPT.read_text(encoding="utf-8")
    match = re.search(r"(?m)^    def resolve_name_pool\(.*?\n(?=    def )", source, re.S)
    if match is None:
        raise AssertionError("resolve_name_pool not found in script.rpy")
    body = "\n".join(line[4:] if line.startswith("    ") else line
                     for line in match.group(0).splitlines())

    class _Renpy(object):
        def log(self, *args, **kwargs):
            pass

    namespace = {
        "name_lists": json.loads(NAMES.read_text(encoding="utf-8")),
        "renpy": _Renpy(),
        "random": random,
    }
    exec(compile(body, "resolve_name_pool", "exec"), namespace)
    return namespace["resolve_name_pool"], namespace["name_lists"]


class ResolveNamePool(unittest.TestCase):
    def setUp(self):
        self.resolve, self.pools = load_resolver()

    def assert_usable(self, pool):
        self.assertTrue(pool, "name pool must not be empty")
        self.assertNotIn("Unknown", pool)
        for name in pool:
            self.assertNotIn("unknown", str(name).lower())

    def test_null_names_list_never_yields_unknown(self):
        # devkit/WM converter emit names_list: null for hand-named characters.
        self.assert_usable(self.resolve(None, "female"))

    def test_blank_and_typo_keys_fall_back(self):
        for value in ("", "   ", "wetsern_female", "custom_pool"):
            self.assert_usable(self.resolve(value, "female"))

    def test_fallback_follows_requested_gender(self):
        self.assertEqual(self.resolve(None, "male"), self.pools["western_male"])
        self.assertEqual(self.resolve(None, "female"), self.pools["western_female"])

    def test_known_key_wins(self):
        self.assertEqual(self.resolve("goblin_female", "female"), self.pools["goblin_female"])


class NamingSourceContracts(unittest.TestCase):
    def test_no_placeholder_pool_left_in_spawn_paths(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('["Unknown"]', source)

    def test_spawn_paths_use_the_resolver(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(source.count("name_pool = resolve_name_pool("), 2)


class ShippedWorkerData(unittest.TestCase):
    def test_declared_names_lists_exist(self):
        resolve, pools = load_resolver()
        for path in sorted(WORKER_DIR.rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data if isinstance(data, list) else data.get("workers", [])
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                declared = entry.get("names_list")
                if not declared:
                    continue
                self.assertIn(
                    declared, pools,
                    f"{path.name}: {entry.get('name')} declares unknown names_list '{declared}'",
                )

    def test_every_spawn_template_resolves_to_a_real_pool(self):
        resolve, pools = load_resolver()
        for path in sorted(WORKER_DIR.rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data if isinstance(data, list) else data.get("workers", [])
            for entry in entries:
                if not isinstance(entry, dict) or entry.get("unique") or entry.get("monster"):
                    continue
                pool = resolve(entry.get("names_list"), entry.get("gender"))
                self.assertTrue(pool)
                self.assertNotIn("Unknown", pool)


if __name__ == "__main__":
    unittest.main()
