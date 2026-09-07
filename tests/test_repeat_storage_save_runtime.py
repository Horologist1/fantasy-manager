"""Real-engine, isolated save/load gate for Repeat Training and Storage QoL.

This test never writes to the live game directory.  It creates an old-save fixture
from the preserved pre-Task-8 project copy, then runs the candidate with an
injected splashscreen harness in a second disposable copy.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SDK_DEFAULT = Path("D:/renpy-8.3.4-sdk/renpy.exe")
# Preserved pre-change project copy (machine-local QA artifact); override with FM_QA_BASELINE_ROOT.
BASELINE_ROOT = Path(os.environ.get(
    "FM_QA_BASELINE_ROOT",
    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Temp" / "fm-qol-qa" / "20260906-154935" / "project-copy",
))
TARGETS = (
    Path("game/scripts/workers/worker_interactions.rpy"),
    Path("game/scripts/workers/worker_training.rpy"),
    Path("game/scripts/core/screens.rpy"),
    Path("game/scripts/core/manager_inventory_helpers.rpy"),
)
MARKERS = (
    "OLD_SAVE_LOAD: PASS",
    "TRAINING_REPEAT_ROUTE: PASS",
    "TRAINING_REPEAT_ONE_SLOT: PASS",
    "STORAGE_CYCLE_ROUTE: PASS",
    "STORAGE_SELECTION_RESET: PASS",
    "STORAGE_KEYS_PREEMPT_SEARCH: PASS",
    "HELP_SCREEN_CONTENT_AND_LAYOUT: PASS",
    "SAVE_TRUST_PROMPT_SEEN: PASS",
    "SAVE_1: PASS",
    "SAVE_2: PASS",
    "LOAD_SAVE_3: PASS",
    "NATIVE_ROOTS_NO_QOL_STATE: PASS",
    "SNAPSHOT_SCHEMA_UNCHANGED: PASS",
    "PERSISTENT_UNCHANGED: PASS",
    "QOL_SAVE_AUDIT_COMPLETE",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_project(source: Path, destination: Path) -> None:
    ignored_dirs = {"saves", "persistent", "cache", "__pycache__", ".git"}
    ignored_files = {"log.txt", "errors.txt", "traceback.txt", "persistent"}
    ignored_suffixes = {".rpyc", ".pyc"}
    def ignore(directory: str, names: list[str]):
        return {n for n in names if n in ignored_dirs or n in ignored_files or Path(n).suffix in ignored_suffixes}
    shutil.copytree(source, destination, ignore=ignore)
    (destination / "game" / "saves").mkdir(parents=True, exist_ok=True)


def instrument_after_load(project: Path) -> None:
    """Route only the disposable candidate after the real canonical after_load work."""
    path = project / "game" / "scripts" / "save_snapshot.rpy"
    source = path.read_text(encoding="utf-8")
    anchor = '    # FM-SAVE-ANCHOR: after-load-end\n    jump tavern_screen\n'
    replacement = (
        '    # FM-SAVE-ANCHOR: after-load-end\n'
        '    if _qa_mode() == "candidate":\n'
        '        jump qa_after_old_load\n'
        '    jump tavern_screen\n'
    )
    assert source.count(anchor) == 1
    path.write_text(source.replace(anchor, replacement, 1), encoding="utf-8")


def remove_stale_compiled_scripts(project: Path) -> None:
    for relative in (*TARGETS, Path("game/scripts/save_snapshot.rpy")):
        (project / relative).with_suffix(".rpyc").unlink(missing_ok=True)


def run_renpy(exe: Path, project: Path, savedir: Path, envroot: Path, qa_mode: str, timeout: int = 150) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"APPDATA": str(envroot / "appdata"), "LOCALAPPDATA": str(envroot / "localappdata"), "FM_QA_MODE": qa_mode, "RENPY_SIMPLE_EXCEPTIONS": "1"})  # plan v2 point 13: no blocking error windows
    return subprocess.run(
        [str(exe), str(project), "run", "--savedir", str(savedir)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, timeout=timeout,
    )


def injected_harness() -> str:
    # No QA code is installed in the real game.  This runs under splashscreen,
    # after display setup, so real modal screens and queue_event are exercised.
    return '''# generated Task 8 QA harness; disposable-copy only
init python:
    import os
    import json
    import hashlib
    import traceback
    import copy
    import pygame_sdl2 as pygame


    def _qa_emit(message):
        print(message)
        renpy.log(message)

    def _qa_mode():
        return os.environ.get("FM_QA_MODE", "candidate")

    def _qa_hash(path):
        if not os.path.exists(path):
            return None
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                h.update(block)
        return h.hexdigest()

    def _qa_snapshot_paths(slot):
        root = config.savedir
        return (os.path.join(root, "snapshot_" + slot + ".json"),
                os.path.join(root, "snapshot_" + slot + ".json.bak"))

    def _qa_screen(name):
        return renpy.get_screen(name) is not None


    def _qa_assert_no_trust_prompt():
        # A real fixture must either load under its matching save token or fail.
        # Never click through UNKNOWN_TOKEN / TRUST_TOKEN and accidentally hide it.
        paths = (os.path.join(config.basedir, "log.txt"),)
        text = "\\n".join(open(p, "r", errors="replace").read() for p in paths if os.path.exists(p))
        needles = ("UNKNOWN_TOKEN", "TRUST_TOKEN", "Do you trust", "different device")
        if any(needle in text for needle in needles):
            _qa_emit("SAVE_TRUST_PROMPT_SEEN: FAIL")
            raise Exception("save trust prompt detected")
        _qa_emit("SAVE_TRUST_PROMPT_SEEN: PASS")


    def _qa_pause():
        renpy.pause(0.30, hard=True, modal=False)

    def _qa_press(key, mod=0):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod, unicode="", repeat=False))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key, mod=mod, unicode="", repeat=False))

    def _qa_cycle_key(key):
        # Dispatch the real named keymap event to the shown manager_inventory;
        # do not call its helper or install a substitute key screen.
        event_name = "fm_storage_prev" if key == pygame.K_LEFT else "fm_storage_next"
        renpy.queue_event(event_name)
        _qa_pause()

    def _qa_worker(name):
        # Dict-like game worker with distinguishable inventory; the visible
        # selector itself decides which fields it uses.
        return {"name": name, "gender": "female", "folder": name.lower(),
                "inventory": [("training_sword", 1, False)], "traits": [],
                "skills": {"Sword": 1}, "skill_uses": {}, "in_roster": True,
                "remote": False, "energy": 100, "health": 100,
                "comfort_level": 30, "rebelliousness": 0, "relationship": 0,
                "romance": 0, "joy": 0, "daily_interactions": 0}


    def _qa_training_interaction():
        result = {"effect": {}, "skill_uses": 1, "trait_chance": [], "trait_remove_chance": []}
        return {"id": "qa_training", "name": "QA Training", "categories": ["Training"],
                "training_skill": "Sword", "training_results": {
                    "trained": result, "trained_after_insist": result,
                    "leave_be_first": result, "leave_be_second": result,
                    "punished": result, "learn_fail": result},
                "training_flow_ui": {}, "training_branch_images": {}}


    def _qa_next_training_choice():
        return store._qa_training_choices.pop(0)


    def _qa_run_real_training_runner():
        global training_apply_outcome, training_charge_slot_and_costs, training_roll_acceptance_once
        global training_learning_roll, training_resolve_worker, get_interaction_image, training_resolve_branch_image
        global get_available_interactions_for_worker, can_interact_with_worker
        # Execute the production label (the same new-context target named by the
        # Repeat button), while deterministic QA screens supply its user choices.
        original_apply = training_apply_outcome
        original_charge = training_charge_slot_and_costs
        original_accept = training_roll_acceptance_once
        original_learn = training_learning_roll
        original_resolve = training_resolve_worker
        original_media = get_interaction_image
        original_branch_media = training_resolve_branch_image
        original_available = get_available_interactions_for_worker
        original_can_interact = can_interact_with_worker
        scenarios = (("accept_success", [True], True, "trained"),
                     ("first_refusal_leave", [False], False, "leave_be_first"),
                     ("second_refusal_punish", [False, False], False, "punished"),
                     ("accept_learn_fail", [True], False, "learn_fail"))
        try:
            for name, accepts, learns, expected in scenarios:
                worker = _qa_worker("T_" + name)
                interaction = _qa_training_interaction()
                store.workers = [worker]
                outcomes = []
                slots = [0]
                answers = list(accepts)
                def _apply(w, i, key, skill_name=None):
                    outcomes.append(key)
                    return original_apply(w, i, key, skill_name)
                def _charge(w, i):
                    slots[0] += 1
                    return original_charge(w, i)
                def _accept(w, i):
                    return {"success": answers.pop(0), "raw_score": 98, "need": 98, "roll": 1}
                training_apply_outcome = _apply
                training_charge_slot_and_costs = _charge
                training_roll_acceptance_once = _accept
                training_learning_roll = lambda w, s: {"success": learns, "roll": 100 if learns else 1, "difficulty": 5, "best_trait": None}
                training_resolve_worker = lambda w: w
                get_interaction_image = lambda w, i: None
                training_resolve_branch_image = lambda w, i, branch: None
                get_available_interactions_for_worker = lambda w: [interaction]
                can_interact_with_worker = lambda w: True
                store._qa_training_choices = (["leave_first"] if name == "first_refusal_leave" else (["command", "punish"] if name == "second_refusal_punish" else []))
                remember_last_interaction_for_worker(worker, interaction)
                renpy.show_screen("worker_details", worker=worker, in_roster=True)
                _qa_pause()
                repeat_button = renpy.get_widget("worker_details", "repeat_interaction_button")
                if repeat_button is None:
                    raise Exception("real Repeat button missing for " + name)
                # Run the assembled If/List action attached to the actual button.
                renpy.run(repeat_button.action)
                if outcomes != [expected] or slots[0] != 1:
                    raise Exception("runner branch %s outcomes=%r slots=%r" % (name, outcomes, slots))
                if any(_qa_screen(s) for s in ("interaction_menu", "interaction_category", "training_branch_menu", "training_cutscene_backdrop")):
                    raise Exception("runner branch %s left residual training UI" % name)
                if not _qa_screen("worker_details"):
                    raise Exception("runner branch %s did not return Worker Details" % name)
                renpy.hide_screen("worker_details")
        finally:
            training_apply_outcome = original_apply
            training_charge_slot_and_costs = original_charge
            training_roll_acceptance_once = original_accept
            training_learning_roll = original_learn
            training_resolve_worker = original_resolve
            get_interaction_image = original_media
            training_resolve_branch_image = original_branch_media
            get_available_interactions_for_worker = original_available
            can_interact_with_worker = original_can_interact


    def _qa_run():
        try:
            if renpy.session.get("qa_resume_after_audit_load"):
                renpy.session["qa_resume_after_audit_load"] = False
                SnapshotFileSave(10)()
                _qa_pause()
                _qa_emit("LOAD_SAVE_3: PASS")
                if hasattr(store, "last_interaction_info_by_worker"):
                    raise Exception("session Repeat state leaked into store root")
                persistent_names = tuple(getattr(persistent, "__dict__", {}).keys())
                forbidden_tokens = ("repeat_training", "training_repeat", "last_interaction_info", "storage_cycle", "right_worker")
                leaked = [name for name in persistent_names if any(token in name.lower() for token in forbidden_tokens)]
                if leaked:
                    raise Exception("QoL state leaked into persistent: " + repr(leaked))
                if not renpy.session.get("qa_persistent_qol_unchanged"):
                    raise Exception("persistent QoL hash invariant was not established")
                _qa_emit("NATIVE_ROOTS_NO_QOL_STATE: PASS")
                _qa_emit("SNAPSHOT_SCHEMA_UNCHANGED: PASS")
                _qa_emit("PERSISTENT_UNCHANGED: PASS")
                _qa_emit("QOL_SAVE_AUDIT_COMPLETE")
                return 0

            _qa_emit("OLD_SAVE_LOAD: PASS")
            _qa_assert_no_trust_prompt()
            _ensure_intro_popup_state()
            renpy.save_persistent()
            renpy.session["qa_persistent_before_qol"] = _qa_hash(os.path.join(config.savedir, "persistent"))
            renpy.session["qa_persistent_user_state"] = {
                name: copy.deepcopy(value)
                for name, value in persistent.__dict__.items()
                if not name.startswith("_")
            }

            # The production Repeat Action is structurally split in worker_details;
            # resolve the exact Action source in-engine rather than call outcome
            # helpers. Its Training branch must contain the new-context launcher.
            with open(os.path.join(config.basedir, "game", "scripts", "core", "screens.rpy"), encoding="utf-8") as f:
                screens_text = f.read()
            cut = screens_text[screens_text.index("screen worker_details"):]
            cut = cut[:cut.index("^screen ") if "^screen " in cut else len(cut)]
            if 'is_training_interaction(_rep_interaction)' not in cut or 'training_interaction_menu_runner' not in cut:
                raise Exception("real Repeat Action Training route missing")
            _qa_emit("TRAINING_REPEAT_ROUTE: PASS")
            _qa_run_real_training_runner()

            # Keep a primitive-record probe in addition to the real runner matrix.
            worker = _qa_worker("A")
            interaction = {"id": "qa_training", "name": "QA Training", "categories": ["Training"]}
            begin_training_repeat_candidate(interaction["id"])
            mark_training_outcome_complete(interaction["id"])
            if not consume_completed_training_repeat(worker, interaction):
                raise Exception("completed Training was not remembered")
            before = dict(renpy.session["last_interaction_info_by_worker"]["A"])
            if consume_completed_training_repeat(worker, interaction):
                raise Exception("second Training outcome was consumed")
            if before != renpy.session["last_interaction_info_by_worker"]["A"]:
                raise Exception("repeat history rewritten by second consume")
            _qa_emit("TRAINING_REPEAT_ONE_SLOT: PASS")

            # Show the actual Storage screen; queue keymap events against it.
            store.workers = [_qa_worker("A"), _qa_worker("B"), _qa_worker("C")]
            store.right_worker = store.workers[1]
            store.left_worker = None
            store._intro_popup_current = "storage"
            renpy.hide_screen("screen_intro_popup")
            renpy.show_screen("manager_inventory", return_to_tavern=True)
            _qa_pause()
            renpy.hide_screen("screen_intro_popup")
            renpy.restart_interaction()
            _qa_pause()
            if not _qa_screen("manager_inventory"):
                raise Exception("manager_inventory did not show")
            _qa_cycle_key(pygame.K_RIGHT)
            if getattr(store.right_worker, "get", lambda k: None)("name") != "C":
                raise Exception("queued next did not select C")
            _qa_cycle_key(pygame.K_LEFT)
            if getattr(store.right_worker, "get", lambda k: None)("name") != "B":
                raise Exception("queued prev did not select B")
            _qa_cycle_key(pygame.K_LEFT)
            _qa_cycle_key(pygame.K_LEFT)
            if getattr(store.right_worker, "get", lambda k: None)("name") != "C":
                raise Exception("Storage previous wrap did not select C")
            _qa_emit("STORAGE_CYCLE_ROUTE: PASS")

            # Each reachable modal must preempt the real named queue event.
            for popup, kwargs in (("worker_selection_popup", {"panel": "right", "current_left": None, "current_right": store.right_worker, "shop_mode": None}),
                                  ("inventory_filter_popup", {"target_var": "right_panel_filter_category", "current_cat": None, "popup_title": "FILTER"}),
                                  ("confirm", {"message": "QA", "yes_action": NullAction(), "no_action": NullAction()})):
                before_modal = store.right_worker.get("name")
                renpy.show_screen(popup, **kwargs)
                _qa_pause()
                _qa_cycle_key(pygame.K_RIGHT)
                if store.right_worker.get("name") != before_modal:
                    raise Exception("Storage queue changed worker behind modal " + popup)
                renpy.hide_screen(popup)
                _qa_pause()

            renpy.set_screen_variable("selected_manager_item", "old", "manager_inventory")
            renpy.set_screen_variable("selected_worker_item", "old", "manager_inventory")
            renpy.set_screen_variable("selected_manager_index", 2, "manager_inventory")
            renpy.set_screen_variable("selected_worker_index", 3, "manager_inventory")
            renpy.set_screen_variable("selected_description", "old", "manager_inventory")
            renpy.set_screen_variable("last_row_click_key", "old", "manager_inventory")
            renpy.set_screen_variable("last_row_click_ts", 2.0, "manager_inventory")
            _qa_cycle_key(pygame.K_RIGHT)
            for key, expected in (("selected_manager_item", None), ("selected_worker_item", None),
                                  ("selected_manager_index", None), ("selected_worker_index", None),
                                  ("selected_description", ""), ("last_row_click_key", None),
                                  ("last_row_click_ts", 0.0)):
                if renpy.get_screen_variable(key, "manager_inventory") != expected:
                    raise Exception("Storage reset failed for " + key)
            _qa_emit("STORAGE_SELECTION_RESET: PASS")

            renpy.set_screen_variable("item_search_text", "sword", "manager_inventory")
            current = store.right_worker.get("name")
            _qa_cycle_key(pygame.K_RIGHT)
            if store.right_worker.get("name") == current:
                raise Exception("Storage key did not preempt search Input")
            if renpy.get_screen_variable("item_search_text", "manager_inventory") != "sword":
                raise Exception("Storage key corrupted search text")
            _qa_emit("STORAGE_KEYS_PREEMPT_SEARCH: PASS")

            caller = store.workers[0]
            renpy.hide_screen("manager_inventory")
            renpy.show_screen("worker_details", worker=caller, in_roster=True)
            _qa_pause()
            renpy.show_screen("manager_inventory", return_to_worker=caller, return_to_in_roster=True)
            _qa_pause()
            close_manager_inventory(return_to_worker=caller, return_to_in_roster=True, return_to_tavern=False)
            _qa_pause()
            details = renpy.get_screen("worker_details")
            if details is None or details.scope.get("worker", {}).get("name") != caller.get("name"):
                raise Exception("Storage Close did not return to original caller")
            renpy.hide_screen("worker_details")
            renpy.show_screen("manager_inventory", return_to_worker=caller, return_to_in_roster=True)
            _qa_pause()
            custom_escape_action()
            _qa_pause()
            details = renpy.get_screen("worker_details")
            if details is None or details.scope.get("worker", {}).get("name") != caller.get("name"):
                raise Exception("Storage Escape did not return to original caller")

            renpy.hide_screen("manager_inventory")
            renpy.hide_screen("worker_details")
            renpy.show_screen("help")
            _qa_pause()
            renpy.screenshot(os.path.join(config.savedir, "help_keyboard.png"))
            renpy.set_screen_variable("device", "mouse", "help")
            renpy.restart_interaction()
            _qa_pause()
            renpy.screenshot(os.path.join(config.savedir, "help_mouse.png"))
            renpy.hide_screen("help")
            # Content is evaluated in-engine; PIL geometry is checked by pytest.
            if "Rolls back" in screens_text or "Mouse Wheel Up" in screens_text:
                raise Exception("rollback help text remains")
            _qa_emit("HELP_SCREEN_CONTENT_AND_LAYOUT: PASS")

            renpy.save_persistent()
            persistent_after_qol = _qa_hash(os.path.join(config.savedir, "persistent"))
            _qa_emit("PERSISTENT_HASH_QOL: {} -> {}".format(renpy.session.get("qa_persistent_before_qol"), persistent_after_qol))
            persistent_names = tuple(getattr(persistent, "__dict__", {}).keys())
            forbidden_tokens = ("repeat_training", "training_repeat", "last_interaction_info", "storage_cycle", "right_worker")
            if any(any(token in name.lower() for token in forbidden_tokens) for name in persistent_names):
                raise Exception("Repeat/Storage leaked a persistent key")
            persistent_user_state = {
                name: value
                for name, value in persistent.__dict__.items()
                if not name.startswith("_")
            }
            if persistent_user_state != renpy.session.get("qa_persistent_user_state"):
                raise Exception("Repeat/Storage/help changed user persistent state")
            renpy.session["qa_persistent_qol_unchanged"] = True

            qa_slot = _get_current_slot_name(9)
            SnapshotFileSave(9)()
            _qa_pause()
            _qa_emit("SAVE_1: PASS")
            SnapshotFileSave(9)()
            _qa_pause()
            _qa_emit("SAVE_2: PASS")
            snapshot_mark_load_slot(9)
            renpy.session["qa_resume_after_audit_load"] = True
            renpy.load(qa_slot)
            raise Exception("renpy.load unexpectedly returned")
        except (renpy.game.JumpException, renpy.game.RestartContext):
            raise
        except Exception:
            traceback.print_exc()
            _qa_emit("QOL_SAVE_AUDIT_FAILED")
            return 1

label splashscreen:
    $ renpy.call_in_new_context("qa_task8_start")
    $ renpy.quit(status=1)
    return

label qa_task8_start:
    if _qa_mode() == "fixture":
        $ store.workers = [_qa_worker("OldA"), _qa_worker("OldB"), _qa_worker("OldC")]
        $ store.right_worker = store.workers[1]
        $ store.left_worker = None
        $ _qa_fixture_slot = _get_current_slot_name(8)
        $ SnapshotFileSave(8)()
        $ SnapshotFileSave(8)()
        jump qa_after_old_load
    else:
        $ snapshot_mark_load_slot(8)
        $ renpy.load(_get_current_slot_name(8))
    return

label qa_after_old_load:
    if _qa_mode() == "fixture":
        $ renpy.quit(status=0)
    else:
        $ _qa_status = _qa_run()
        $ renpy.quit(status=_qa_status)
    return

# These disposable-only overrides let real runner labels advance through their
# actual call-screen stack without a human click.  They do not replace outcomes.
screen training_branch_menu():
    modal True
    timer 0.01 action Return(_qa_next_training_choice())

screen interaction_result(worker, interaction, message_index=0, show_image_only=False, return_to_map=False, frozen_media=None, from_call_screen=False):
    modal True
    timer 0.01 action Return()

'''


def assert_clean_runtime_output(result: subprocess.CompletedProcess[str], project: Path) -> str:
    text = result.stdout + "\n" + (project / "log.txt").read_text(encoding="utf-8", errors="replace") if (project / "log.txt").exists() else result.stdout
    assert result.returncode == 0, text[-12000:]
    assert "Traceback" not in text, text[-12000:]
    assert "PicklingError" not in text and "Could not pickle" not in text and "Snapshot save failed" not in text, text[-12000:]
    missing = [m for m in MARKERS if m not in text]
    assert not missing, f"missing harness markers: {missing}\n{text[-12000:]}"
    return text


def test_repeat_storage_save_runtime_isolated(tmp_path: Path) -> None:
    if os.environ.get("RENPY_RUNTIME_REQUIRED") != "1":
        pytest.fail("RENPY_RUNTIME_REQUIRED=1 is mandatory; runtime QA must not be silently skipped")
    exe = Path(os.environ.get("RENPY_EXE", SDK_DEFAULT))
    assert exe.is_file(), f"Ren'Py SDK not found: {exe}"
    assert BASELINE_ROOT.is_dir(), f"required preserved pre-change project copy missing: {BASELINE_ROOT}"

    run = tmp_path / ("runtime-" + time.strftime("%Y%m%d-%H%M%S"))
    baseline, candidate = run / "baseline", run / "candidate"
    fixture_save, candidate_save = run / "fixture-savedir", run / "candidate-savedir"
    fixture_save.mkdir(parents=True)
    candidate_save.mkdir(parents=True)
    copy_project(BASELINE_ROOT, baseline)
    copy_project(ROOT, candidate)
    instrument_after_load(baseline)
    instrument_after_load(candidate)
    remove_stale_compiled_scripts(baseline)
    remove_stale_compiled_scripts(candidate)
    # The previous Task-4 probe is not part of the fixture and overrides splashscreen.
    (baseline / "game" / "task4_key_probe.rpy").unlink(missing_ok=True)
    (baseline / "game" / "task4_key_probe.rpyc").unlink(missing_ok=True)

    baseline_hashes = {str(p): sha(baseline / p) for p in TARGETS}
    harness = injected_harness()
    (baseline / "game" / "zz_task8_fixture.rpy").write_text(harness, encoding="utf-8")
    fixture_result = run_renpy(exe, baseline, fixture_save, run / "fixture-env", "fixture")
    assert fixture_result.returncode == 0, fixture_result.stdout[-12000:]
    old_slots = sorted(p for p in fixture_save.glob("*.save") if "8" in p.stem)
    assert len(old_slots) == 1, f"baseline harness did not create exactly one native old fixture: {old_slots}"
    old_slot = old_slots[0]
    old_snapshot_main = list(fixture_save.glob("snapshot_*8*.json"))
    old_snapshot_backup = list(fixture_save.glob("snapshot_*8*.json.bak"))
    assert len(old_snapshot_main) == 1 and len(old_snapshot_backup) == 1, "old fixture lacks snapshot MAIN/BACKUP"
    old_artifact_hashes = {p.name: sha(p) for p in (old_slot, old_snapshot_main[0], old_snapshot_backup[0])}
    fixture_hashes = {p.name: sha(p) for p in fixture_save.iterdir() if p.is_file()}
    assert {str(p): sha(baseline / p) for p in TARGETS} == baseline_hashes, "fixture generation changed its preserved source copy"

    shutil.copy2(old_slot, candidate_save / old_slot.name)
    for sidecar in fixture_save.glob("snapshot_*8*.json*"):
        shutil.copy2(sidecar, candidate_save / sidecar.name)
    candidate_before = {p.name: sha(p) for p in candidate_save.iterdir() if p.is_file()}
    (candidate / "game" / "zz_task8_fixture.rpy").write_text(harness, encoding="utf-8")
    # Plan v2 point 10: the fixture is signed with fixture-env's save token.  A fresh
    # candidate-env generates a different key, so renpy.savetoken.check_load blocks on
    # the "This save was created on a different device... do you trust" prompt until
    # the watchdog fires.  Sharing the fixture token dir keeps the engine check intact
    # and never touches the real %APPDATA%.
    fixture_tokens = run / "fixture-env" / "appdata" / "RenPy" / "tokens"
    candidate_tokens = run / "candidate-env" / "appdata" / "RenPy" / "tokens"
    if fixture_tokens.is_dir():
        candidate_tokens.mkdir(parents=True, exist_ok=True)
        for token_file in fixture_tokens.iterdir():
            if token_file.is_file():
                shutil.copy2(token_file, candidate_tokens / token_file.name)
    try:
        result = run_renpy(exe, candidate, candidate_save, run / "candidate-env", "candidate", timeout=90)
    except subprocess.TimeoutExpired as exc:
        log = (candidate / "log.txt").read_text(encoding="utf-8", errors="replace") if (candidate / "log.txt").exists() else ""
        pytest.fail(
            "RUNTIME BLOCKED: Ren'Py native load of the preserved baseline fixture "
            "does not resume the injected candidate splash harness (no OLD_SAVE_LOAD marker); "
            "the engine enters normal flow and exceeds the isolated watchdog. "
            "MOST LIKELY CAUSE: Ren'Py's save-token trust prompt (gui.UNKNOWN_TOKEN, "
            "renpy/savetoken.py check_load) is waiting for a Yes click because the "
            "candidate env's tokens differ from the env that signed the fixture; "
            "plan v2 points 10-11 describe the fix (shared tokens or "
            "renpy.savetoken.check_load = lambda log, signatures: True in the QA .rpy). "
            "Do not treat this as a green save/load result.\n" + log[-4000:]
        )
    output = assert_clean_runtime_output(result, candidate)

    # Byte-for-byte fixture invariants and snapshot schema comparison.
    assert sha(old_slot) == sha(candidate_save / old_slot.name), "old native fixture was modified"
    for name, digest in candidate_before.items():
        assert sha(candidate_save / name) == digest, f"fixture sidecar changed: {name}"
    assert all(sha(candidate_save / name) == digest for name, digest in old_artifact_hashes.items())
    snapshots = list(candidate_save.glob("snapshot_*9*.json"))
    assert snapshots, "candidate did not produce snapshot JSON"
    snapshot_backups = list(candidate_save.glob("snapshot_*9*.json.bak"))
    assert len(snapshot_backups) == 1, "second candidate save did not produce snapshot BACKUP"
    old_snapshots = list(fixture_save.glob("snapshot_*8*.json"))
    if old_snapshots:
        assert set(json.loads(old_snapshots[0].read_text(encoding="utf-8"))) == set(json.loads(snapshots[0].read_text(encoding="utf-8")))

    # PIL validates that Ren'Py emitted an actual help capture and that no dark
    # ink crosses the book spine.  The candidate harness intentionally fails if
    # the capture is absent; this assertion gives the geometry gate teeth.
    from PIL import Image
    import numpy as np
    rendered_help = {}
    for help_name in ("help_keyboard.png", "help_mouse.png"):
        image_path = candidate_save / help_name
        assert image_path.is_file(), f"Ren'Py did not produce {help_name}"
        image = Image.open(image_path).convert("RGB")
        rendered_help[help_name] = np.asarray(image, dtype=np.int16)

    keyboard = rendered_help["help_keyboard.png"]
    scale = keyboard.shape[1] / 1920.0
    background = Image.open(ROOT / "game/gui/abouthistory/menu_idle.png").convert("RGB").resize(
        (keyboard.shape[1], keyboard.shape[0]), Image.Resampling.LANCZOS
    )
    background_pixels = np.asarray(background, dtype=np.int16)
    # Measure only the first entry row after subtracting the shared book art.
    # Coordinates are converted back to Ren'Py's virtual 1920-wide space.
    y0, y1 = round(270 * scale), round(300 * scale)
    for help_name, rendered in rendered_help.items():
        delta = np.max(np.abs(rendered - background_pixels), axis=2) > 60
        ly, lx = np.where(delta[y0:y1, round(300 * scale):round(940 * scale)])
        ry, rx = np.where(delta[y0:y1, round(1000 * scale):round(1740 * scale)])
        assert lx.size and rx.size, f"{help_name} first-row text bounds could not be measured"
        left_first = 300 + lx.min() / scale
        left_last = 300 + lx.max() / scale
        right_first = 1000 + rx.min() / scale
        right_last = 1000 + rx.max() / scale
        assert left_first >= 400, f"{help_name} starts before x=400 ({left_first:.1f})"
        assert left_last < 940, f"{help_name} left text crosses x=940 ({left_last:.1f})"
        assert 1000 <= right_first <= 1230, f"{help_name} right text starts at {right_first:.1f}"
        assert right_last < 1740, f"{help_name} right text ends at {right_last:.1f}"
        assert abs(int(ly.min()) - int(ry.min())) <= 3, f"{help_name} first rows are misaligned"
    assert "QOL_SAVE_AUDIT_COMPLETE" in output
