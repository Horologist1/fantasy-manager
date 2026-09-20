"""Event bookkeeping invariants: counters, flags and caps.

Audit 2026-09-20, block 4 (events). The event layer already has contract tests
for shape and presentation; these cover the *state* it writes: occurrence
counters, timed flags and the building values an event effect can move.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "game" / "scripts"
SCRIPT = SCRIPTS / "script.rpy"
DAILY = SCRIPTS / "events" / "event_daily_exec.rpy"
MAIN_FLOW = SCRIPTS / "main_flow.rpy"
TUTORIAL = SCRIPTS / "tutorial_system.rpy"


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


def label_source(path, name):
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((index for index, line in enumerate(lines)
                  if line.startswith("label " + name + ":")), None)
    if start is None:
        raise AssertionError("label " + name + " not found in " + path.name)
    end = next((index for index in range(start + 1, len(lines))
                if lines[index].startswith("label ")), len(lines))
    return "\n".join(lines[start:end])


class LimitedEventsOnlyResetOnANewGame(unittest.TestCase):
    def test_single_call_site(self):
        calls = []
        for path in SCRIPTS.rglob("*.rpy"):
            for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "reset_limited_events()" in line and "def " not in line:
                    calls.append((path.name, index))
        self.assertEqual(len(calls), 1, calls)

    def test_it_lives_in_label_start(self):
        self.assertIn("reset_limited_events()", label_source(MAIN_FLOW, "start"))


class TimedFlagsAreDeletedSafely(unittest.TestCase):
    def test_every_del_on_event_flags_is_guarded_or_iterates_a_snapshot(self):
        pattern = re.compile(r"del store\.event_flags\[([^\]]+)\]")
        for path in SCRIPTS.rglob("*.rpy"):
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                match = pattern.search(line)
                if not match:
                    continue
                key = match.group(1)
                window = "\n".join(lines[max(0, index - 6):index])
                guarded = (key + " in store.event_flags") in window
                snapshot = "list(store.event_flags.keys())" in window
                self.assertTrue(guarded or snapshot,
                                path.name + ":" + str(index + 1) + " deletes " + key + " unguarded")


class SabotageCannotPushTheBonusPastItsCap(unittest.TestCase):
    def setUp(self):
        self.daily = function_source(DAILY, "process_next_day")

    def test_the_restore_clamps(self):
        restore = self.daily[self.daily.index("sabotage_restore_"):]
        restore = restore[:restore.index("except Exception")]
        self.assertIn("MAX_BUILDING_SKILL_BONUS", restore)

    def test_the_day_clamps_the_bonus_like_level_and_reputation(self):
        clamp = self.daily.index('building["skill_bonus"] = max(0, min(int(building.get("skill_bonus", 0) or 0), MAX_BUILDING_SKILL_BONUS))')
        reset = self.daily.index('building["costs"] = 0')
        self.assertLess(clamp, reset, "clamp before the day starts charging")

    def test_the_sabotage_records_the_real_reduction(self):
        body = TUTORIAL.read_text(encoding="utf-8")
        chunk = body[body.index("def apply_governor_sabotage_event") if "def apply_governor_sabotage_event" in body
                     else body.index("sabotage_restore_") - 800:]
        self.assertIn("reduction = min(10, max(0, old_bonus))", chunk)


class OccurrenceBookkeepingStaysInOnePlace(unittest.TestCase):
    def test_counter_and_timestamp_always_move_together(self):
        body = function_source(SCRIPT, "process_choice")
        counters = body.count("store.event_occurrences[event_id] = store.event_occurrences.get(event_id, 0) + 1")
        stamps = body.count("store.event_last_occurred[event_id] = calculate_total_days()")
        self.assertEqual(counters, stamps,
                         "every branch that counts an occurrence must also stamp the day")


class RecruitmentEffectsStayInsideTheirApplier(unittest.TestCase):
    """The recruitment flow has its own effect applier, narrower than apply_effects.

    A recruitment event that used event_flags, loot_rolls, consume_item,
    servant_energy/health, skill_modifiers or trait_chance would be accepted by
    the schema and then do nothing at all, silently.
    """

    APPLIER_KEYS = {
        "add_attribute", "add_trait", "cost_modifier", "custom", "health", "item_id",
        "joy", "money", "recruit_worker", "relationship_bonus", "reputation",
    }
    FLOW_KEYS = {"success_chance", "success", "failure"}

    def test_no_recruitment_effect_uses_an_ignored_key(self):
        import json

        allowed = self.APPLIER_KEYS | self.FLOW_KEYS
        offenders = []
        for path in sorted((ROOT / "game" / "data" / "events" / "recruit").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            events = data if isinstance(data, list) else data.get("events", [])
            for event in events:
                for choice in (event.get("choices") or []):
                    for field in ("effect", "success_effect", "failure_effect"):
                        effect = choice.get(field) or {}
                        if not isinstance(effect, dict):
                            continue
                        for key in effect:
                            if key not in allowed:
                                offenders.append((path.name, event.get("id"), field, key))
        self.assertFalse(offenders, "recruitment effects the applier ignores: " + str(offenders[:6]))

    def test_the_applier_still_handles_the_keys_this_test_assumes(self):
        body = function_source(ROOT / "game" / "scripts" / "events" / "recruitment_functions.rpy",
                               "apply_recruitment_effects")
        for key in sorted(self.APPLIER_KEYS):
            self.assertIn('"' + key + '"', body, "applier no longer handles " + key)


if __name__ == "__main__":
    unittest.main()
