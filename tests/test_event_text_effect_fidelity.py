"""Event message text must not announce stat changes the effect does not apply.

Regression gate for a defect class, not a single event. `knights_honor_duel` was
found announcing "-10 Health" while its failure effect declared `health: -5`; the
same mismatch was live in seven further events (arena_challenge_visitor,
bandit_shakedown, rooftop_chase_thief, collapsing_scaffold, escaped_beast_loose,
underground_fight_ring, guild_ancient_map_discovery).

The existing structural contracts cannot see this: the JSON is valid and every
field is recognised. Only comparing the prose against the declared effect catches
it, which is what this module does.

Editorial rule: the *text* is corrected to match the effect. A pass over the
writing never rebalances the game.
"""

import json
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS_DIR = os.path.join(REPO_ROOT, "game", "data", "events")

# Stats a message can plausibly announce and that events declare as effect keys.
STATS = (
    "health",
    "joy",
    "energy",
    "libido",
    "reputation",
    "romance",
    "relationship",
    "rebelliousness",
    "discipline",
    "obedience",
)

# Effect keys the engine reads under a different name than the prose uses.
# Recruitment applies "+N Relationship" through `relationship_bonus`
# (recruitment_functions.rpy:647), so the flat `relationship` key never appears.
STAT_EFFECT_ALIASES = {
    "relationship": ("relationship", "relationship_bonus"),
}

_STAT_ALT = "|".join(STATS)
# "-10 Health" / "+5 Joy"
_VALUE_FIRST = re.compile(r"([+-]?\d+)\s*(" + _STAT_ALT + r")\b", re.IGNORECASE)
# "Health -10"
_STAT_FIRST = re.compile(r"\b(" + _STAT_ALT + r")\s*([+-]\d+)", re.IGNORECASE)

# Branch-specific effect blocks a message maps onto.
_MESSAGE_BRANCH = {
    "message": None,
    "message_success": "success",
    "message_failure": "failure",
}


def _event_files():
    for name in sorted(os.listdir(EVENTS_DIR)):
        if name.endswith(".json"):
            yield os.path.join(EVENTS_DIR, name)
    recruit = os.path.join(EVENTS_DIR, "recruit")
    if os.path.isdir(recruit):
        for name in sorted(os.listdir(recruit)):
            if name.endswith(".json"):
                yield os.path.join(recruit, name)


def _claims(text):
    """Stat values the prose promises the player, as {stat: value}."""
    found = {}
    for match in _VALUE_FIRST.finditer(text):
        found[match.group(2).lower()] = int(match.group(1))
    for match in _STAT_FIRST.finditer(text):
        found[match.group(1).lower()] = int(match.group(2))
    return found


def _declared(effect, branch):
    """Effect block a message's claims must agree with.

    Branch blocks win over the flat effect; a branch event that omits a stat at
    branch level still falls back to the flat value the engine would apply.
    """
    if not isinstance(effect, dict):
        return {}
    resolved = dict(
        (key, value) for key, value in effect.items() if not isinstance(value, dict)
    )
    if branch and isinstance(effect.get(branch), dict):
        resolved.update(effect[branch])
    return resolved


class EventTextEffectFidelity(unittest.TestCase):
    def test_announced_stat_changes_match_declared_effects(self):
        mismatches = []
        for path in _event_files():
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, list):
                continue
            rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
            for event in data:
                if not isinstance(event, dict):
                    continue
                for index, choice in enumerate(event.get("choices") or []):
                    if not isinstance(choice, dict):
                        continue
                    effect = choice.get("effect") or {}
                    for field, branch in _MESSAGE_BRANCH.items():
                        text = choice.get(field)
                        if not isinstance(text, str):
                            continue
                        declared = _declared(effect, branch)
                        for stat, promised in _claims(text).items():
                            # {actual_x} placeholders are rendered from the real
                            # computed value, so the prose cannot lie about them.
                            if "{actual_%s}" % stat in text:
                                continue
                            keys = STAT_EFFECT_ALIASES.get(stat, (stat,))
                            stat_key = next(
                                (key for key in keys if key in declared), None
                            )
                            if stat_key is None:
                                mismatches.append(
                                    "%s :: %s :: choices[%d].%s announces "
                                    "%+d %s but the effect declares no %s"
                                    % (
                                        rel,
                                        event.get("id"),
                                        index,
                                        field,
                                        promised,
                                        stat,
                                        stat,
                                    )
                                )
                                continue
                            actual = declared[stat_key]
                            if not isinstance(actual, (int, float)):
                                continue
                            if int(actual) != promised:
                                mismatches.append(
                                    "%s :: %s :: choices[%d].%s announces "
                                    "%+d %s but the effect applies %+d"
                                    % (
                                        rel,
                                        event.get("id"),
                                        index,
                                        field,
                                        promised,
                                        stat,
                                        int(actual),
                                    )
                                )
        self.assertEqual(
            [],
            mismatches,
            "Event prose promises stat changes the engine does not apply. "
            "Correct the message, never the effect:\n  " + "\n  ".join(mismatches),
        )


if __name__ == "__main__":
    unittest.main()
