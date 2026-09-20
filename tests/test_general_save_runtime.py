"""Real Ren'Py save/load/restart gate; all writes stay in a disposable project."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get("RENPY_EXE", "D:/renpy-8.3.4-sdk/renpy.exe"))

HARNESS = r'''
init python:
    import json as _qa_general_json
    import os as _qa_general_os
    import shutil as _qa_general_shutil

    def qa_general_expected():
        return {"academy_lib_stage": 2, "academy_lib_last_visit_total_days": 1,
                "academy_lib_seal_attempts_today": 2, "character_event_last_day": 1,
                "academy_director_intro_done": True, "vengeance_path_chosen": True,
                "vengeance_path": "Shadow", "monster_instance_counter": 73,
                "tutorial_skipped": True}

    def qa_general_check(name, ok, actual=None):
        results = renpy.session.setdefault("qa_general_results", [])
        results.append({"check": name, "passed": bool(ok), "actual": actual})
        with open(_qa_general_os.path.join(config.savedir, "report.json"), "w", encoding="utf-8") as handle:
            _qa_general_json.dump(results, handle, indent=2)
        if not ok:
            raise AssertionError("QA: %s: %r" % (name, actual))

    def qa_general_write(path, snap):
        with open(path, "w", encoding="utf-8") as handle:
            _qa_general_json.dump(snap, handle)

    def qa_general_save(slot):
        name = _get_current_slot_name(slot)
        before = _native_save_commit_marker(name)
        SnapshotFileSave(slot)()
        after = _native_save_commit_marker(name)
        qa_general_check("native save committed: " + str(slot), _native_save_marker_advanced(before, after))
        return name

    def qa_general_setup():
        store.main_menu = False
        store.at_main_menu = False
        store.tutorial_active = False
        store.game_initialized = True
        store.workers = []
        store.available_workers = []
        store.manager_inventory = []
        store.current_day = store.current_month = store.current_year = 1
        persistent.nsfw_enabled = False
        store.event_flags = {"academy_lib_migrated_v2": True, "academy_lib_ready_decrypt": True,
                             "academy_lib_started": True, "academy_lib_hint_a": True,
                             "academy_lib_hint_b": True, "academy_lib_hint_c": True}
        for field, value in qa_general_expected().items():
            setattr(store, field, value)
        set_save_blocked_context(None)

        # Exercise real overwrite, legacy-v3 missing fields, and an interrupted
        # write where only the durable recovery file matches the native save.
        store.money = 10000
        qa_general_save(91)
        for slot in (91, 92, 93):
            store.money = 50000 + slot
            name = qa_general_save(slot)
            snap = _read_snapshot_file(_get_snapshot_file_path(name))
            for field, value in qa_general_expected().items():
                qa_general_check("capture %s: %s" % (slot, field), snap.get(field) == value)
            if slot == 92:
                for field in qa_general_expected():
                    snap.pop(field, None)
                qa_general_check("legacy v3 accepted", _snapshot_is_complete_for_canonical_load(snap))
                qa_general_write(_get_snapshot_file_path(name), snap)
                qa_general_write(_get_backup_file_path(name), snap)
            elif slot == 93:
                _qa_general_shutil.copy2(_get_snapshot_file_path(name), _previous_snapshot_backup_temp_path(name))
                snap["snapshot_transaction_id"] = "uncommitted-write"
                snap["money"] = 999999
                qa_general_write(_get_snapshot_file_path(name), snap)
                qa_general_write(_get_backup_file_path(name), snap)

        # Declined trust must not deserialize any native payload.
        original_check = renpy.savetoken.check_load
        original_loads = renpy.loadsave.loads
        calls = []
        def decline(data, signatures):
            calls.append("check")
            return False
        def read(data):
            calls.append("unpickle")
            return original_loads(data)
        try:
            renpy.savetoken.check_load = decline
            renpy.loadsave.loads = read
            qa_general_check("declined trust blocks load", not _prepare_canonical_snapshot_load(91))
            qa_general_check("declined trust precedes unpickle", calls == ["check"], calls)
        finally:
            renpy.savetoken.check_load = original_check
            renpy.loadsave.loads = original_loads

        renpy.session["qa_general_slot"] = 91
        CanonicalSnapshotFileLoad(FileLoad(91, confirm=False), 91, confirm=False)()
        raise AssertionError("canonical load did not restart")

    def qa_general_loaded():
        slot = renpy.session["qa_general_slot"]
        qa_general_check("load money " + str(slot), store.money == 50000 + slot, store.money)
        for field, value in qa_general_expected().items():
            actual = getattr(store, field, None)
            qa_general_check("load %s: %s" % (slot, field), actual == value, actual)
        qa_general_check("cooldown survives " + str(slot), not character_event_cooldown_ready(2))
        qa_general_check("seal available " + str(slot), academy_lib_can_attempt_seal())
        if slot < 93:
            renpy.session["qa_general_slot"] = slot + 1
            CanonicalSnapshotFileLoad(FileLoad(slot + 1, confirm=False), slot + 1, confirm=False)()
            raise AssertionError("canonical load did not restart")
        name = qa_general_save(93)
        qa_general_check("recovered slot can be overwritten", not _qa_general_os.path.exists(_previous_snapshot_backup_temp_path(name)))
        qa_general_check("recovered slot has a valid new pair", _prepare_canonical_snapshot_load(93))
        persistent._canonical_snapshot_load_pending = None

        before = _build_snapshot()
        damaged = _cp.deepcopy(before)
        damaged["money"] = 1
        damaged["academy_lib_stage"] = -1
        qa_general_check("invalid progression refuses apply", not _apply_snapshot(damaged))
        after = _build_snapshot()
        for field in ("money", "event_flags", "workers", "manager_inventory") + tuple(qa_general_expected()):
            qa_general_check("failed apply rolls back " + field, after[field] == before[field])

        store.academy_lib_stage = -1
        marker = _native_save_commit_marker(name)
        SnapshotFileSave(93)()
        qa_general_check("unloadable state cannot overwrite native save", _native_save_commit_marker(name) == marker)
        qa_general_check("previous valid slot remains loadable", _prepare_canonical_snapshot_load(93))
        persistent._canonical_snapshot_load_pending = None
        store.academy_lib_stage = before["academy_lib_stage"]

        # If both old sources omitted a value, retain only progress supported
        # by the existing flags, and reset absent cooldowns instead of leaking
        # the previously loaded slot's values.
        old = _cp.deepcopy(before)
        for field in qa_general_expected():
            old.pop(field, None)
        qa_general_check("legacy flags-only apply succeeds", _apply_snapshot(old))
        qa_general_check("legacy academy progress inferred", store.academy_lib_stage == 2)
        qa_general_check("absent cooldown does not leak", store.character_event_last_day is None)

        # 0.9.6/0.9.6.1 never captured academy_lib_stage, so every load reset
        # it to 0 while event_flags kept "manual found"; saves made afterwards
        # persisted that 0. Loading either shape must restore the finished
        # quest and unlock the Master's Elixir.
        finished_flags = dict(before["event_flags"], academy_lib_decrypt_done=True, academy_lib_manual_found=True)
        damaged_0961 = _cp.deepcopy(before)
        damaged_0961["event_flags"] = _cp.deepcopy(finished_flags)
        damaged_0961["academy_lib_stage"] = 0
        damaged_0961["alchemy_unlocked"] = True
        damaged_0961["elixir_award_granted"] = False
        qa_general_check("0.9.6.1-shaped apply succeeds", _apply_snapshot(damaged_0961))
        qa_general_check("0.9.6.1 stage reconciled", store.academy_lib_stage == 3, store.academy_lib_stage)
        qa_general_check("0.9.6.1 elixir available", masters_elixir_is_available())
        legacy_finished = _cp.deepcopy(damaged_0961)
        for field in qa_general_expected():
            legacy_finished.pop(field, None)
        qa_general_check("legacy finished apply succeeds", _apply_snapshot(legacy_finished))
        qa_general_check("legacy finished stage inferred", store.academy_lib_stage == 3, store.academy_lib_stage)
        qa_general_check("legacy finished elixir available", masters_elixir_is_available())
        store.academy_lib_stage = 0
        store.event_flags = _cp.deepcopy(finished_flags)
        qa_general_check("elixir gate trusts flags", masters_elixir_is_available())
        store.event_flags = _cp.deepcopy(before["event_flags"])
        qa_general_check("elixir gate still closed mid-quest", not masters_elixir_is_available())

        # Saves that unlocked Bikini Bouts through the old card ladder, or that
        # still have fighters on the job, must show the job to new fighters.
        legacy_arena = _cp.deepcopy(before)
        legacy_arena["lanista_card_tier"] = 2
        legacy_arena["lanista_pinup_unlocked"] = False
        legacy_arena["lanista_arena_program_tier"] = 0
        qa_general_check("legacy arena apply succeeds", _apply_snapshot(legacy_arena))
        qa_general_check("legacy card tier unlocks Bikini Bouts", store.lanista_pinup_unlocked)
        qa_general_check("legacy card tier sets program tier", store.lanista_arena_program_tier >= 1)

        # An owned Academy with the enrolment flag lost, an owned Arena with the
        # permit flag lost, and a journal ahead of its objective flags all heal.
        legacy_gates = _cp.deepcopy(before)
        legacy_gates["available_buildings"] = dict(_cp.deepcopy(before["available_buildings"]))
        legacy_gates["available_buildings"]["Academy"] = {"price": 0, "base_level": 1, "assigned_servants": [], "servant_jobs": {}, "type": "academy", "reputation": 0, "max_workers": {}, "costs": 0, "owned": True, "skill": 10, "skill_bonus": 0, "event_limit": 0, "training_focus": {}}
        legacy_gates["available_buildings"]["Arena"] = {"price": 0, "base_level": 1, "assigned_servants": [], "servant_jobs": {}, "type": "arena", "reputation": 0, "max_workers": {}, "costs": 0, "owned": True, "skill": 10, "skill_bonus": 0, "event_limit": 0, "training_focus": {}}
        legacy_gates["academy_enrolled"] = False
        legacy_gates["arena_lanista_paid"] = False
        legacy_gates["current_objective"] = 9
        for _n in range(1, 9):
            legacy_gates["objective_%d_complete" % _n] = False
        qa_general_check("legacy gates apply succeeds", _apply_snapshot(legacy_gates))
        qa_general_check("owned Academy heals enrolment", store.academy_enrolled)
        qa_general_check("owned Arena heals permit", store.arena_lanista_paid and store.arena_unlocked)
        qa_general_check("objective flags heal from current objective", all(getattr(store, "objective_%d_complete" % _n) for _n in range(1, 9)))
        # dead workers recorded only in the legacy list survive a load
        legacy_dead = _cp.deepcopy(before)
        legacy_dead["dead_worker_names"] = ["Old Ghost"]
        qa_general_check("legacy dead list apply succeeds", _apply_snapshot(legacy_dead))
        qa_general_check("legacy dead worker stays dead", church_worker_is_dead("Old Ghost"))
        renpy.quit(status=0)

label splashscreen:
    $ qa_general_setup()
    return

label qa_general_loaded:
    $ qa_general_loaded()
    return
'''


def make_project(destination):
    def ignore(directory, names):
        return [name for name in names if name in {"saves", "cache", "__pycache__"}
                or Path(name).suffix in {".rpyc", ".rpyb", ".pyc"}
                or name.startswith("qa_")]

    def copy_file(source, target):
        # Media is never modified. All code/data, caches, saves and preferences
        # belong to the disposable copy, including Ren'Py's second save location.
        if Path(source).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".ogg", ".mp3"}:
            try:
                os.link(source, target)
                return target
            except OSError:
                pass
        return shutil.copy2(source, target)

    shutil.copytree(ROOT / "game", destination / "game", ignore=ignore, copy_function=copy_file)
    snapshot = destination / "game/scripts/save_snapshot.rpy"
    source = snapshot.read_text(encoding="utf-8")
    anchor = '    # FM-SAVE-ANCHOR: after-load-end\n    jump tavern_screen\n'
    assert source.count(anchor) == 1
    snapshot.write_text(source.replace(anchor, '    # FM-SAVE-ANCHOR: after-load-end\n    jump qa_general_loaded\n'), encoding="utf-8")
    (destination / "game/qa_general_audit.rpy").write_text(HARNESS, encoding="utf-8")


def test_real_canonical_load_preserves_progress_and_recovers_interrupted_save(tmp_path):
    if not SDK.is_file():
        if os.environ.get("RENPY_RUNTIME_REQUIRED") == "1":
            pytest.fail("RENPY_RUNTIME_REQUIRED=1 but the Ren'Py SDK is unavailable")
        pytest.skip("requires the Ren'Py SDK (set RENPY_EXE)")
    project = tmp_path / "project"
    make_project(project)
    env = os.environ.copy()
    env.update(APPDATA=str(tmp_path / "env/appdata"), LOCALAPPDATA=str(tmp_path / "env/localappdata"),
               RENPY_SIMPLE_EXCEPTIONS="1")
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        env["RENPY_RENDERER"] = "gl2"
    result = subprocess.run([str(SDK), str(project), "run", "--savedir", str(tmp_path / "saves")],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            startupinfo=startup, timeout=60)
    output = result.stdout.decode("utf-8", "replace")
    (tmp_path / "engine-output.txt").write_text(output, encoding="utf-8")
    assert result.returncode == 0, output[-6000:]
    rows = json.loads((tmp_path / "saves/report.json").read_text(encoding="utf-8"))
    assert len(rows) >= 70
    assert all(row["passed"] for row in rows), rows
