"""Guard: every top-level `default` is either captured by the save snapshot or
declared transient here. Loading applies the JSON snapshot onto a CLEAN store,
so an uncaptured progression variable silently resets on every load (this is
how the Master's Elixir, dead workers and Bikini Bouts broke in 0.9.6).

If this test fails after you add a `default`, decide:
  * progression/economy/state the player must keep -> capture it in
    game/scripts/save_snapshot.rpy (add it to _SNAPSHOT_PROGRESS_DEFAULTS or to
    _build_snapshot + the apply lists), and add a load-time heal if an older
    save can prove the same thing through other state;
  * transient UI/session state -> add it to TRANSIENT_DEFAULTS below with a
    reason, and make sure nothing reads it across a load.
See docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md, section 18.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "game/scripts/save_snapshot.rpy"

# name -> why losing it on load is harmless
TRANSIENT_DEFAULTS = {
    # alchemy session (saving is blocked while it runs)
    "_alchemy_investment_tier": "session, save blocked",
    "_alchemy_material_quote": "session, save blocked",
    "_alchemy_paid_cost": "session, save blocked",
    "_alchemy_recipe_id": "session, save blocked",
    "_alchemy_session_fee": "session, save blocked",
    # engine / bootstrap
    "_force_new_game_reset": "bootstrap flag",
    "_last_tooltip_screen": "tooltip context",
    "_training_interaction_result_active": "modal flag",
    "quick_menu": "Ren'Py quick menu toggle",
    "current_bg": "current background",
    "max_building": "constant",
    # event presentation (event choice screen is rebuilt from event data)
    "acting_worker": "current event actor",
    "affected_building_info": "current event text",
    "building_notification": "current event text",
    "current_affected_building": "current event",
    "current_event": "current event",
    "event_worker_name": "current event",
    # roster / report / storage UI state
    "building_filter": "UI filter",
    "buy_servants_filter_gender": "UI filter",
    "current_report_index": "UI index",
    "current_worker": "UI selection",
    "current_worker_index": "UI index",
    "daily_report": "rebuilt every day",
    "daily_report_job_filter": "UI filter",
    "displayed_workers": "UI cache",
    "left_worker": "storage panel selection",
    "right_worker": "storage panel selection",
    "roster_current_page": "UI page",
    "worker_building_filter": "UI filter",
    "worker_job_filter": "UI filter",
    "worker_details_panel_view": "UI tab",
    "manager_pending_skill_id": "unconfirmed UI pick",
    "auto_advance_pending_result": "popup result",
    "auto_advance_requested_days": "popup input",
    "tavern_click_guard": "click debounce",
    "tooltips_enabled_by_screen": "tooltip toggles",
    "franchise_last_summary": "write-only summary",
    "arena_lanista_speaker_name": "recomputed per use",
    # map hover flags
    "buy_buildings_text_hover": "hover",
    "plaza_servants_text_hover": "hover",
    "recruit_workers_text_hover": "hover",
    "shops_text_hover": "hover",
    "take_a_walk_text_hover": "hover",
    # tutorial constants / derived counters (objectives read live state)
    "buildings_owned": "derived, never read across a load",
    "total_workers": "derived, never read across a load",
    "workers_assigned": "derived, never read across a load",
    "objective_dialogue_triggered": "set and cleared synchronously",
    "show_objective_dialogue": "set and cleared synchronously",
    "objective_descriptions": "constant table",
    "objective_titles": "constant table",
    "tutorial_milestone_consolidation": "image path constant",
    "tutorial_milestone_ending_blackmail": "image path constant",
    "tutorial_milestone_ending_blade": "image path constant",
    "tutorial_milestone_note_door": "image path constant",
}


def top_level_defaults():
    """Top-level `default name = ...` declarations (screen-local defaults excluded)."""
    found = {}
    for path in sorted((ROOT / "game/scripts").rglob("*.rpy")):
        in_screen = False
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            if re.match(r"^(screen|label|init|define|default|transform|image|style|python)\b", line):
                in_screen = line.startswith("screen")
            match = re.match(r"^default\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if match and not in_screen:
                found.setdefault(match.group(1), "%s:%d" % (path.relative_to(ROOT).as_posix(), number))
    return found


def snapshot_mentions(name, source):
    return re.search(r'["\']' + re.escape(name) + r'["\']', source) is not None \
        or re.search(r"\bstore\." + re.escape(name) + r"\b", source) is not None


def test_every_default_is_captured_or_declared_transient():
    source = SNAPSHOT.read_text(encoding="utf-8")
    undecided = {name: where for name, where in top_level_defaults().items()
                 if not snapshot_mentions(name, source) and name not in TRANSIENT_DEFAULTS}
    assert not undecided, (
        "Uncaptured `default` variables (they reset on EVERY load). Capture them in "
        "save_snapshot.rpy or declare them transient in TRANSIENT_DEFAULTS:\n  "
        + "\n  ".join("%s  (%s)" % (name, where) for name, where in sorted(undecided.items()))
    )


def test_transient_list_has_no_stale_entries():
    source = SNAPSHOT.read_text(encoding="utf-8")
    declared = top_level_defaults()
    stale = [name for name in TRANSIENT_DEFAULTS if name not in declared or snapshot_mentions(name, source)]
    assert not stale, "Remove from TRANSIENT_DEFAULTS (no longer a default, or now captured): %s" % stale


def test_every_required_flag_is_captured():
    """A profession gate that is not saved would silently relock on load."""
    source = SNAPSHOT.read_text(encoding="utf-8")
    missing = []
    for path in (ROOT / "game/data/buildings").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for btype in data.get("building_types", []):
            for profession in btype.get("professions", []) or []:
                flag = profession.get("required_flag")
                if flag and not snapshot_mentions(flag, source):
                    missing.append("%s.%s -> %s" % (btype.get("id"), profession.get("id"), flag))
    assert not missing, "required_flag not captured by the snapshot: %s" % missing
