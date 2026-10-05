"""Event presentation gates. Real layout/click checks: tools/qa_choice_layout.py.

English continuity requires editorial review, not shared-word matching. Every
transition has a review of all previous outcomes and both subsequent outcomes.
Fingerprints invalidate that review when any scene text or choice gate changes.
They do not claim to understand prose. See docs/AUDIT_event_verification_2026-09-09.md.
"""
import copy
import hashlib
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game/scripts/core/screens.rpy"
CHOICE_SCREENS = ("random_event_choice", "recruitment_choice_screen")
CONTAINERS = ("vbox", "hbox", "fixed", "frame", "viewport", "vpgrid", "side", "grid")
REVIEWS = ROOT / "tests/fixtures/event_arc_reviews.json"


def load_events():
    rows = []
    for path in sorted((ROOT / "game/data/events").rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        rows.extend(e for e in (data if isinstance(data, list) else [data]) if isinstance(e, dict) and "id" in e)
    return rows


def screen_block(source, name):
    match = re.search(rf"(?m)^screen {re.escape(name)}\b[^\n]*:\n", source)
    if match is None:
        raise AssertionError("screen not found: " + name)
    following = re.search(r"(?m)^(?:screen|transform|style|init|label|define|default) ", source[match.end():])
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


def direct_body(lines, index):
    indent = len(lines[index]) - len(lines[index].lstrip())
    body = []
    for line in lines[index + 1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        depth = len(line) - len(line.lstrip())
        if depth <= indent:
            break
        if depth == indent + 4:
            body.append(line.strip())
    return body


def review_fingerprint(event):
    # Includes *all* prose, including pages/results, plus the conditions that
    # determine which branches can be seen. Balance numbers alone need no re-review.
    keys = ("description", "description_pages", "dialogue", "option", "message", "message_pages",
            "message_success", "message_failure", "arc_id", "arc_stage", "conditions", "required_flags",
            "excluded_flags", "required_trait", "required_traits", "excluded_traits", "nsfw")
    payload = {key: event[key] for key in keys if key in event}
    if "choices" in event:
        payload["choices"] = [review_fingerprint(choice) for choice in event["choices"]]
    if "effect" in event:
        payload["effect_text"] = effect_text(event["effect"])
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def effect_text(value):
    if isinstance(value, dict):
        return {k: (v if k.startswith("message") else effect_text(v)) for k, v in value.items()
                if k.startswith("message") or isinstance(v, (dict, list))}
    if isinstance(value, list):
        return [effect_text(v) for v in value]
    return None


def arc_transitions(events):
    arcs = defaultdict(list)
    for event in events:
        if event.get("arc_id"):
            arcs[event["arc_id"]].append(event)
    return [(previous, current) for stages in arcs.values()
            for previous, current in zip(sorted(stages, key=lambda e: e["arc_stage"]), sorted(stages, key=lambda e: e["arc_stage"])[1:])]


class ChoiceListLayoutContracts(unittest.TestCase):
    def setUp(self):
        self.source = SCREENS.read_text(encoding="utf-8")

    def test_choice_containers_have_explicit_styles_in_their_own_body(self):
        for name in CHOICE_SCREENS:
            lines = screen_block(self.source, name).splitlines()
            for i, line in enumerate(lines):
                if re.match(r"^\s+(?:" + "|".join(CONTAINERS) + r")(?:\s+[^:]+)?:\s*$", line):
                    with self.subTest(screen=name, line=i):
                        self.assertTrue(any(re.match(r'^style "', child) for child in direct_body(lines, i)), line)

    def test_no_absolute_placement_leaks_into_event_choice_containers(self):
        for name in ("event_choice_vbox", "event_choice_locked_vbox", "event_choice_side", "event_choice_viewport"):
            for match in re.finditer(rf"(?m)^style {name}\b[^\n]*", self.source):
                lines = self.source[match.start():].splitlines()
                self.assertNotIn('is choice_', lines[0])
                for child in direct_body(lines, 0):
                    self.assertNotRegex(child, r"^(?:xpos|ypos|xoffset|yoffset|xanchor|yanchor)\b")

    def test_other_prefixed_screens_do_not_nest_absolute_container_styles(self):
        # Scan every script, not just the two choice screens. Root placement is
        # intentional (e.g. the standard choice menu); nested inheritance is not.
        sources = [p.read_text(encoding="utf-8-sig") for p in (ROOT / "game/scripts").rglob("*.rpy")]
        combined = "\n".join(sources)
        absolute = set()
        for m in re.finditer(r"(?m)^style (\w+)[^\n]*", combined):
            if any(re.match(r"^(?:ypos|yoffset|xpos|xoffset)\s+-?\d", child)
                   for child in direct_body(combined[m.start():].splitlines(), 0)):
                absolute.add(m.group(1))
        for source in sources:
            lines = source.splitlines()
            for i, line in enumerate(lines):
                prefix = re.match(r'^([ ]*)style_prefix "(\w+)"', line)
                if not prefix:
                    continue
                depth = len(prefix.group(1))
                for j in range(i + 1, len(lines)):
                    child = lines[j]
                    if not child.strip() or child.lstrip().startswith("#"):
                        continue
                    indent = len(child) - len(child.lstrip())
                    if indent < depth:
                        break
                    container = re.match(r"^\s*(" + "|".join(CONTAINERS) + r")(?:\s+[^:]+)?:\s*$", child)
                    if not container:
                        continue
                    resolved = prefix.group(2) + "_" + container.group(1)
                    explicit = any(re.match(r'^style "', prop) for prop in direct_body(lines, j))
                    # Equal-depth root siblings are deliberate screen placement.
                    if indent > depth and resolved in absolute:
                        self.assertTrue(explicit, "Implicit absolute style %s at %s" % (resolved, child.strip()))

    def test_overflow_has_bounded_scroll_and_readable_reasons(self):
        for name in CHOICE_SCREENS:
            block = screen_block(self.source, name)
            for contract in ('ymaximum (config.screen_height - 80)', 'yfill False', 'mousewheel True',
                             'draggable renpy.variant("touch")', 'pagekeys True', 'YScrollValue('):
                self.assertIn(contract, block)
        block = screen_block(self.source, "random_event_choice")
        self.assertIn('font_size(28)', block)
        self.assertIn('xmaximum (gui.choice_button_width - 40)', block)

    def test_cancellation_is_a_real_non_none_result_and_callers_accept_legacy_sentinels(self):
        for name in ("random_event_choice", "choose_event_worker_screen"):
            self.assertNotIn('Return(None)', screen_block(self.source, name))
            self.assertIn('Return(False)', screen_block(self.source, name))
        events = (ROOT / "game/scripts/events/events.rpy").read_text(encoding="utf-8")
        self.assertIn('if not hasattr(chosen_choice_data, "get"):', events)
        self.assertIn('if not hasattr(chosen_worker, "get"):', events)
        recruit = (ROOT / "game/scripts/events/recruitment_flow.rpy").read_text(encoding="utf-8")
        self.assertIn('if chosen_choice_data.get("_dismiss_recruitment", False):', recruit)


class ArcBackreferenceContracts(unittest.TestCase):
    def test_every_transition_has_a_current_full_branch_review(self):
        reviews = json.loads(REVIEWS.read_text(encoding="utf-8"))["transitions"]
        indexed = {(r["from"], r["to"]): r for r in reviews}
        transitions = arc_transitions(load_events())
        self.assertEqual(len(indexed), len(reviews), "Duplicate review")
        self.assertEqual(set(indexed), {(p["id"], c["id"]) for p, c in transitions}, "Missing or obsolete arc reviews")
        self.assertEqual(len(transitions), 48, "Catalogue changed: review all new/removed transitions")
        for previous, current in transitions:
            review = indexed[(previous["id"], current["id"])]
            with self.subTest(event=current["id"]):
                self.assertEqual(review["previous_sha256"], review_fingerprint(previous), "Previous premise/outcomes changed; re-read every branch")
                self.assertEqual(review["current_sha256"], review_fingerprint(current), "Continuation changed; editorial review required")
                self.assertTrue(review["premise"] and review["branches"], "Document why this works after failure/decline as well as success")

    def test_review_invalidates_for_later_sentences_results_and_gates(self):
        event = next(e for e in load_events() if e["id"] == "worker_lily_garden_boundaries")
        for mutate in (lambda e: e.update(description=e["description"] + " She remembers an unseen victory."),
                       lambda e: e["choices"][0].update(message_failure="A different outcome."),
                       lambda e: e["choices"][0].update(required_flags={"new_branch": True})):
            changed = copy.deepcopy(event)
            mutate(changed)
            self.assertNotEqual(review_fingerprint(event), review_fingerprint(changed))
        balance = copy.deepcopy(event)
        balance["choices"][0]["effect"]["success"]["money"] += 1
        self.assertEqual(review_fingerprint(event), review_fingerprint(balance))


if __name__ == "__main__":
    unittest.main()
