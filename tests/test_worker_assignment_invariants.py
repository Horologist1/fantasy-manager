"""Assignment invariants: the target building key is always resolved.

Audit 2026-09-20, block 3 (workers). Saves carry both "Building 2" and
"Building_2" (LA BIBLIA 3). `unassign_worker` and `sell_building` resolved the
key; `add_worker_to_building` and `set_worker_job` only resolved the *old*
building, so the alternate spelling made an assignment vanish without a notice.
"""

import re
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "game" / "scripts" / "script.rpy"

RESOLVING_FUNCTIONS = ("add_worker_to_building", "set_worker_job")


def function_source(path, name):
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


class KeyResolutionIsPartOfTheContract(unittest.TestCase):
    def test_both_assignment_entry_points_resolve_the_target(self):
        for name in RESOLVING_FUNCTIONS:
            body = function_source(SCRIPT, name)
            resolve = body.find("building_name = _resolve_building_key(building_name)")
            check = body.find("building_name not in available_buildings")
            self.assertGreaterEqual(resolve, 0, name + " does not resolve the target key")
            self.assertLess(resolve, check, name + " checks membership before resolving")


class SetWorkerJobBehaviour(unittest.TestCase):
    def setUp(self):
        self.worker = {"name": "QA Lyra", "assigned_building": "Building_2"}
        self.building = {"type": "casino", "servant_jobs": {}, "assigned_servants": []}
        self.buildings = {"Building_2": self.building}
        self.store = types.SimpleNamespace(workers=[self.worker])

        class _Renpy(object):
            def log(self, *args):
                pass

            def notify(self, *args, **kwargs):
                pass

        self.ns = {
            "re": re,
            "store": self.store,
            "available_buildings": self.buildings,
            "renpy": _Renpy(),
            "building_accepts_worker_assignment": lambda name: True,
            "canonicalize_servant_job_id": lambda building, job: str(job).strip().lower(),
            "verify_assignment_integrity": lambda tag: None,
        }
        source = "\n".join(
            "\n".join(line[4:] if line.startswith("    ") else line
                      for line in function_source(SCRIPT, name).splitlines())
            for name in ("_alternate_building_key", "_resolve_building_key", "set_worker_job")
        )
        exec(compile(source, "assignment", "exec"), self.ns)

    def test_the_alternate_spelling_still_sets_the_job(self):
        self.assertTrue(self.ns["set_worker_job"](self.worker, "Building 2", "dealer"))
        self.assertEqual(self.building["servant_jobs"], {"QA Lyra": "dealer"})

    def test_an_unknown_building_reports_failure(self):
        self.assertFalse(self.ns["set_worker_job"](self.worker, "Building 9", "dealer"))
        self.assertEqual(self.building["servant_jobs"], {})

    def test_rest_remembers_the_previous_profession(self):
        self.ns["set_worker_job"](self.worker, "Building 2", "dealer")
        self.ns["set_worker_job"](self.worker, "Building 2", "rest")
        self.assertEqual(self.worker["previous_profession"], "dealer")


if __name__ == "__main__":
    unittest.main()
