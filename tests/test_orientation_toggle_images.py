"""Worker Orientation toggle: image remap + trait reconciliation rules.

Spec: docs/superpowers/specs/2026-08-24-orientation-forced-images-design.md
Pure-logic tests for fm_orientation.rules; source-contract tests are added
to this same file in Task 6.
"""

from fm_orientation.rules import (
    REMAP_SKILLS,
    MARKER_FORCE,
    MARKER_ROLLED,
    remap_image_skill,
    toggle_action,
)


# --- remap_image_skill -------------------------------------------------------

NON_REMAP_SKILLS = [
    "striptease", "combat", "clever", "charm", "service", "agility", "craft",
    "wait", "maid", "rest",
]


def test_remap_set_is_exactly_the_agreed_skills():
    # User decision 2026-08-24: all sexual skills except Striptease.
    assert REMAP_SKILLS == frozenset(
        {"sex", "anal", "bdsm", "hand", "oral", "special", "group", "extreme"}
    )


def test_unmarked_worker_is_identity_for_every_skill():
    for skill in sorted(REMAP_SKILLS) + NON_REMAP_SKILLS + ["homo", "gay", "les"]:
        assert remap_image_skill(skill, "male", None) == skill
        assert remap_image_skill(skill, "female", None) == skill


def test_marked_male_sexual_skills_remap_to_gay():
    for marker in (MARKER_FORCE, MARKER_ROLLED):
        for skill in sorted(REMAP_SKILLS):
            assert remap_image_skill(skill, "male", marker) == "gay"


def test_marked_female_sexual_skills_remap_to_les():
    for marker in (MARKER_FORCE, MARKER_ROLLED):
        for skill in sorted(REMAP_SKILLS):
            assert remap_image_skill(skill, "female", marker) == "les"


def test_marked_homo_skill_shows_hetero_art_via_sex():
    # Hetero-client story on a marked worker -> the folder's real hetero art.
    assert remap_image_skill("homo", "male", MARKER_FORCE) == "sex"
    assert remap_image_skill("homo", "female", MARKER_ROLLED) == "sex"


def test_marked_non_sexual_skills_are_identity():
    # User requirement (2026-08-24): striptease, combat and the rest work unmodified.
    for skill in NON_REMAP_SKILLS:
        assert remap_image_skill(skill, "male", MARKER_FORCE) == skill
        assert remap_image_skill(skill, "female", MARKER_FORCE) == skill


def test_explicit_gay_les_image_skills_pass_through():
    # Per-choice image_skill "gay"/"les" is already correct art - identity.
    assert remap_image_skill("gay", "male", MARKER_FORCE) == "gay"
    assert remap_image_skill("les", "female", MARKER_FORCE) == "les"


def test_none_and_empty_skill_are_identity():
    assert remap_image_skill(None, "male", MARKER_FORCE) is None
    assert remap_image_skill("", "female", MARKER_FORCE) == ""


# --- toggle_action -----------------------------------------------------------

def test_force_mode_adds_when_trait_absent():
    assert toggle_action("force", False, None) == "add"


def test_force_mode_leaves_authored_trait_alone():
    # Worker already has the trait (authored) -> no add, no marker.
    assert toggle_action("force", True, None) is None


def test_force_marker_removed_when_mode_drops_to_off():
    assert toggle_action("off", True, MARKER_FORCE) == "remove"


def test_force_marker_removed_when_mode_drops_to_enable():
    assert toggle_action("enable", True, MARKER_FORCE) == "remove"


def test_force_marker_kept_while_mode_is_force():
    assert toggle_action("force", True, MARKER_FORCE) is None


def test_rolled_marker_is_permanent():
    # User decision: only Force reverts; "On"-rolled traits are generation outcomes.
    for mode in ("off", "enable", "force"):
        assert toggle_action(mode, True, MARKER_ROLLED) is None


def test_authored_workers_never_touched_below_force():
    for mode in ("off", "enable"):
        assert toggle_action(mode, True, None) is None
        assert toggle_action(mode, False, None) is None


def test_stale_force_marker_without_trait_is_cleaned():
    # Trait manually removed (devkit) but marker left behind -> still "remove"
    # so the applier clears the stale marker.
    assert toggle_action("off", False, MARKER_FORCE) == "remove"


# --- source contracts (wiring, mirrors test_event_ux_quality.py style) -------

import os
import re

GAME = os.path.join(os.path.dirname(__file__), "..", "game")


def _read_script(*parts):
    with open(os.path.join(GAME, *parts), encoding="utf-8-sig") as f:
        return f.read()


def test_les_image_pattern_matches_les_and_homo_only():
    visuals = _read_script("scripts", "events", "event_visuals.rpy")
    m = re.search(r'"les":\s*\[([^\]]*)\]', visuals)
    assert m, "les image alias missing from get_skill_search_patterns"
    patterns = [p.strip().strip('"') for p in m.group(1).split(",")]
    assert "les" in patterns and "homo" in patterns
    assert "hetero" not in patterns and "gay" not in patterns and "sex" not in patterns


def test_orientation_remap_wired_into_all_four_resolvers():
    visuals = _read_script("scripts", "events", "event_visuals.rpy")
    script = _read_script("scripts", "script.rpy")
    # event_visuals: definition + get_event_image + _resolve_worker_skill_media_name.
    assert visuals.count("_orientation_image_skill(") >= 3
    # script.rpy: get_worker_image (simulated story_image) + get_worker_image_random.
    assert script.count("_orientation_image_skill(") >= 2


def test_default_folder_stages_guarded_for_locked_lookups():
    visuals = _read_script("scripts", "events", "event_visuals.rpy")
    script = _read_script("scripts", "script.rpy")
    assert visuals.count("not _orientation_locked") >= 4  # P5-P8 in get_event_image
    assert script.count("not _orientation_locked") >= 2   # P3-P4 in get_worker_image_random


def test_lock_engages_only_for_same_sex_remaps():
    # Review decision 2026-08-24: homo->"sex" must NOT skip default-folder art.
    visuals = _read_script("scripts", "events", "event_visuals.rpy")
    script = _read_script("scripts", "script.rpy")
    assert visuals.count('_orientation_locked = _osk_remapped in ("gay", "les")') == 1
    assert script.count('_orientation_locked = _osk_remapped in ("gay", "les")') == 1


def test_toggle_buttons_run_the_reconcile_sweep():
    screens = _read_script("scripts", "core", "screens.rpy")
    assert screens.count("Function(reconcile_orientation_toggle)") >= 4  # 2 per button (Confirm + direct)
    traits = _read_script("scripts", "workers", "worker_traits.rpy")
    assert "store.reconcile_orientation_toggle = reconcile_orientation_toggle" in traits


def test_rolled_marker_set_only_behind_only_assigned_bypass():
    traits = _read_script("scripts", "workers", "worker_traits.rpy")
    idx = traits.find('worker["orientation_forced"] = "rolled"')
    assert idx != -1, "rolled marker assignment missing from worker_traits.rpy"
    # The assignment must sit inside the guard that checks the only_assigned bypass
    # (_gay_random/_les_random): all three tokens within the preceding ~500 chars.
    window = traits[max(0, idx - 500):idx]
    assert "only_assigned" in window
    assert "_gay_random" in window and "_les_random" in window
