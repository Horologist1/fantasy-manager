"""The worker catalog must never hand a nameless row to a name-based filter.

Audit 2026-09-20. 0.9.6.1 moved the monster archetypes into
workers_monster_templates.json as recipes with no "name" (they are named at
capture time). load_workers kept returning them, and five call sites filter the
catalog with worker["name"] — e.g. the `recruit_worker` custom action used by
event_recruit_unique_generic_1/2/3 — so an NSFW game raised KeyError: 'name'
on those recruits. Templates are now withheld unless a caller asks for them.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "game" / "scripts" / "workers" / "worker_loader.rpy"
SCRIPT = ROOT / "game" / "scripts" / "script.rpy"
WORKER_DIR = ROOT / "game" / "data" / "workers"

# The only two callers that know how to turn a recipe into a worker.
TEMPLATE_CONSUMERS = ("loot_monster_worker", "spawn_new_monster_worker")


def function_source(path, name):
    source = path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^    def " + re.escape(name) + r"\(.*?\n(?=    \S)", source)
    if match is None:
        raise AssertionError(name + " not found in " + path.name)
    return match.group(0)


class ShippedCatalogRows(unittest.TestCase):
    def test_only_procedural_templates_may_omit_a_name(self):
        for path in sorted(WORKER_DIR.rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            entries = data if isinstance(data, list) else data.get("workers", [])
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                name = str(entry.get("name") or "").strip()
                if not name:
                    self.assertTrue(
                        entry.get("procedural_template", False),
                        path.name + ": a non-template row has no name: " + json.dumps(entry)[:120],
                    )

    def test_a_template_row_still_carries_what_the_spawner_needs(self):
        templates = json.loads((WORKER_DIR / "workers_monster_templates.json").read_text(encoding="utf-8"))
        entries = templates if isinstance(templates, list) else templates.get("workers", [])
        self.assertTrue(entries)
        for entry in entries:
            for field in ("template_id", "monster_archetype", "names_list", "gender", "folder"):
                self.assertIn(field, entry, entry.get("template_id", "?") + " lacks " + field)


class LoaderWithholdsTemplates(unittest.TestCase):
    def setUp(self):
        self.loader = LOADER.read_text(encoding="utf-8")

    def test_templates_are_opt_in_at_the_signature(self):
        self.assertIn("include_procedural_templates=False", self.loader)

    def test_both_load_branches_skip_templates_unless_asked(self):
        skips = re.findall(r"if not include_procedural_templates:\s*\n\s*continue", self.loader)
        self.assertEqual(len(skips), 2, "legacy and per-file load branches must both skip")


class OnlyTheCaptureePathAsksForTemplates(unittest.TestCase):
    def setUp(self):
        self.script = SCRIPT.read_text(encoding="utf-8")

    def test_every_opt_in_belongs_to_a_template_consumer(self):
        for match in re.finditer(r"include_procedural_templates=True", self.script):
            preceding = self.script[:match.start()]
            owner = re.findall(r"(?m)^    def (\w+)\(", preceding)
            self.assertIn(owner[-1], TEMPLATE_CONSUMERS,
                          owner[-1] + " asks for nameless template rows")

    def test_template_consumers_never_index_a_row_by_name(self):
        for name in TEMPLATE_CONSUMERS:
            body = function_source(SCRIPT, name)
            self.assertNotIn('["name"]', body, name + " indexes a catalog row by name")

    def test_name_filtering_call_sites_take_the_plain_catalog(self):
        # These read worker["name"] straight off the catalog; a nameless row
        # would raise before any other condition is evaluated.
        for name in ("loot_normal_worker", "load_recruit_workers"):
            body = function_source(SCRIPT, name)
            self.assertIn("load_workers(", body)
            self.assertNotIn("include_procedural_templates", body)


if __name__ == "__main__":
    unittest.main()
