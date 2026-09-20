"""A new public Ren'Py default must be saved or explicitly classified as transient.

This gate caught the missing quest fields; it is intentionally independent of
the required v3 key set, which must stay compatible with historical saves.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "game/scripts/save_snapshot.rpy").read_text(encoding="utf-8")

PROGRESS_DEFAULTS = ast.literal_eval(re.search(
    r"(?ms)^    _SNAPSHOT_PROGRESS_DEFAULTS = (\{.*?^    \})", SOURCE
).group(1))

# Values reconstructed from authoritative saved records, or temporary UI state.
CLASSIFIED = {
    "derived": {
        "dead_worker_names", "workers_assigned", "buildings_owned", "total_workers",
        "daily_report", "franchise_last_summary", "arena_lanista_speaker_name",
    },
    "presentation": {
        "manager_pending_skill_id", "current_bg", "displayed_workers", "roster_current_page",
        "current_report_index", "left_worker", "right_worker", "building_filter",
        "worker_building_filter", "worker_job_filter", "daily_report_job_filter",
        "current_worker_index", "current_worker", "buy_servants_filter_gender", "acting_worker",
        "plaza_servants_text_hover", "shops_text_hover", "recruit_workers_text_hover",
        "take_a_walk_text_hover", "buy_buildings_text_hover", "tooltips_enabled_by_screen",
        "event_worker_name", "current_affected_building", "affected_building_info",
        "building_notification", "objective_dialogue_triggered", "show_objective_dialogue",
        "auto_advance_requested_days", "auto_advance_pending_result", "quick_menu", "tavern_click_guard",
        "worker_details_panel_view", "current_event",
    },
    "constants": {
        "max_building", "objective_titles", "objective_descriptions",
        "tutorial_milestone_note_door", "tutorial_milestone_consolidation",
        "tutorial_milestone_ending_blade", "tutorial_milestone_ending_blackmail",
    },
    "custom_serializer": {"snapshot_transaction_id"},
}


def uncovered_defaults(source):
    build = SOURCE[SOURCE.index("    def _build_snapshot():"):SOURCE.index("    def _normalize_trait_set(")]
    saved = set(re.findall(r'"(\w+)"\s*:', build)) | set(PROGRESS_DEFAULTS)
    classified = set().union(*CLASSIFIED.values())
    declared = set(re.findall(r"(?m)^default\s+([\w.]+)\s*=", source))
    return {name for name in declared if not name.startswith(("_", "persistent.", "preferences."))
            and name not in saved | classified}


def test_all_public_defaults_have_a_save_or_transient_policy():
    unclassified = {}
    for path in sorted((ROOT / "game/scripts").rglob("*.rpy")):
        names = uncovered_defaults(path.read_text(encoding="utf-8"))
        if names:
            unclassified[str(path.relative_to(ROOT))] = sorted(names)
    assert unclassified == {}, "Review save/load coverage instead of silently resetting new progress"


def test_coverage_gate_detects_a_new_unsaved_quest():
    assert uncovered_defaults("default new_quest_stage = 0") == {"new_quest_stage"}


def test_new_progression_fields_do_not_make_historical_v3_incomplete():
    required = re.search(r"(?ms)^    _CANONICAL_SNAPSHOT_REQUIRED_KEYS = (.*?)(?=^    def )", SOURCE).group(1)
    for field in PROGRESS_DEFAULTS:
        assert f'"{field}"' not in required
