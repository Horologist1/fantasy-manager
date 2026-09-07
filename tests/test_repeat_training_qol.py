"""Contracts for session-only Repeat Training QoL (Tasks 1–3)."""

import re
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / "game" / "scripts" / "workers" / "worker_training.rpy"
INTERACTIONS = ROOT / "game" / "scripts" / "workers" / "worker_interactions.rpy"
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"
PRIMITIVES = (type(None), str, int, float, bool)


def init_python_function(source: str, name: str) -> str:
    match = re.search(rf"(?ms)^    def {re.escape(name)}\(.*?(?=^    def |^\S)", source)
    if match is None:
        raise AssertionError(f"init python helper {name} not found")
    return textwrap.dedent(match.group(0))


def screen_block(source: str, name: str) -> str:
    match = re.search(rf"(?m)^screen {re.escape(name)}\b[^\n]*:\n", source)
    if match is None:
        raise AssertionError(f"screen {name} not found")
    following = re.search(r"(?m)^screen [A-Za-z0-9_]+", source[match.end():])
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


class RepeatTrainingBehaviour(unittest.TestCase):
    def test_training_is_remembered_only_after_completed_runner(self):
        namespace = {"renpy": SimpleNamespace(session={})}
        interaction_source = INTERACTIONS.read_text(encoding="utf-8")
        training_source = TRAINING.read_text(encoding="utf-8")
        exec(init_python_function(interaction_source, "_repeat_interaction_worker_key"), namespace)
        exec(init_python_function(interaction_source, "remember_last_interaction_for_worker"), namespace)
        for helper in (
            "begin_training_repeat_candidate",
            "mark_training_outcome_complete",
            "consume_completed_training_repeat",
        ):
            exec(init_python_function(training_source, helper), namespace)

        worker = {"name": "Aster"}
        interaction = {"id": "training_charm", "name": "Charm Drills", "categories": ["Training"]}
        session = namespace["renpy"].session

        namespace["begin_training_repeat_candidate"](interaction["id"])
        self.assertFalse(namespace["consume_completed_training_repeat"](worker, interaction))
        self.assertNotIn("last_interaction_info_by_worker", session)

        namespace["mark_training_outcome_complete"](interaction["id"])
        self.assertTrue(namespace["consume_completed_training_repeat"](worker, interaction))
        record = session["last_interaction_info_by_worker"]["Aster"]
        self.assertEqual(record, {
            "worker_name": "Aster",
            "category": "Training",
            "interaction_id": "training_charm",
            "interaction_name": "Charm Drills",
        })
        self.assertTrue(all(isinstance(value, PRIMITIVES) for value in record.values()))

        interaction["name"] = "Changed after completion"
        self.assertFalse(namespace["consume_completed_training_repeat"](worker, interaction))
        self.assertEqual(session["last_interaction_info_by_worker"]["Aster"], record)


class RepeatTrainingScreenContracts(unittest.TestCase):
    def setUp(self):
        self.block = screen_block(SCREENS.read_text(encoding="utf-8"), "worker_details")

    def test_repeat_button_routes_training_and_non_training_in_separate_branches(self):
        match = re.search(
            r"(?s)action If\(\s*is_training_interaction\(_rep_interaction\),\s*\[(.*?)\],\s*\[(.*?)\],\s*\)\s*hovered ShowTransient",
            self.block,
        )
        self.assertIsNotNone(match, "Repeat action must branch on is_training_interaction(_rep_interaction)")
        training_branch, normal_branch = match.groups()
        self.assertIn('renpy.call_in_new_context, "training_interaction_menu_runner", worker, _rep_interaction', training_branch)
        self.assertIn("training_resume_worker_details_after_context, worker", training_branch)
        self.assertNotIn("apply_interaction_effects", training_branch)
        self.assertIn('id "repeat_interaction_button"', self.block)
        self.assertIn("apply_interaction_effects", normal_branch)
        self.assertIn('Show("interaction_result", worker=worker, interaction=_rep_interaction)', normal_branch)
        self.assertNotIn("training_interaction_menu_runner", normal_branch)

    def test_repeat_candidate_is_revalidated_from_current_available_interactions(self):
        resolver = re.search(
            r"_rep_interaction\s*=\s*next\(\s*\(i for i in get_available_interactions_for_worker\(worker\).*?\),\s*None,\s*\)",
            self.block,
            re.S,
        )
        self.assertIsNotNone(resolver, "Repeat must resolve its remembered id through current availability")
        candidate_block = self.block[resolver.start():self.block.index("if _rep_interaction is not None:", resolver.end())]
        self.assertNotIn("json", candidate_block.lower())
        self.assertNotIn("_rep_info.get(\"interaction\")", candidate_block)


if __name__ == "__main__":
    unittest.main()
