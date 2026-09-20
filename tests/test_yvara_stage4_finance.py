"""Yvara Stage 4 finance: tiers never regress and a completed track stays complete."""
from pathlib import Path
import re
import textwrap
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parents[1] / "game/scripts/yvara/yvara_complete.rpy").read_text(encoding="utf-8")


def function(name):
    lines = SOURCE.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("    def " + name + "("))
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= 4:
            break
        end += 1
    return textwrap.dedent("\n".join(lines[start:end]))


def complete(**state):
    store = SimpleNamespace(yvara_devotion=0, yvara_dominion=0, yvara_s4_favors_total=0, yvara_s4_donation_total=0,
                            yvara_observed_sessions=0, yvara_good_word_count=0,
                            yvara_s4_favor_highest_tier=0, yvara_s4_donation_highest_tier=0)
    for key, value in state.items():
        setattr(store, key, value)
    env = {"store": store}
    exec(function("yvara_is_dominion_route"), env)
    exec(function("yvara_s4_finance_track_complete"), env)
    return env["yvara_s4_finance_track_complete"]()


def test_every_tier_assignment_is_monotonic():
    assignments = re.findall(r"\$ (yvara_s4_(?:favor|donation)_highest_tier) = (.+)", SOURCE)
    assert len(assignments) == 8
    for name, value in assignments:
        assert value.startswith("max(%s, " % name), (name, value)


def test_completed_track_counts_whichever_way_the_lean_points():
    assert complete(yvara_s4_favor_highest_tier=4, yvara_devotion=30, yvara_dominion=5)
    assert complete(yvara_s4_donation_highest_tier=4, yvara_devotion=5, yvara_dominion=30)


def test_split_or_partial_progress_is_not_complete():
    assert not complete(yvara_s4_favor_highest_tier=3, yvara_s4_donation_highest_tier=3)
    assert not complete()
