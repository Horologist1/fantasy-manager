"""Failure injection against production save actions, using disposable files."""
import copy
import json
import os
import shutil
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "game/scripts/save_snapshot.rpy").read_text(encoding="utf-8")


def definition(name, source=SOURCE, kind="def"):
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(f"    {kind} {name}("))
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= 4:
            break
        end += 1
    return textwrap.dedent("\n".join(lines[start:end]))


def environment(tmp_path, mode="fail"):
    state = SimpleNamespace(snapshot_transaction_id="old", money=100)
    persistent = SimpleNamespace(_slot_guids={"1-1": "guid"})
    native = {"transaction": "old", "marker": (1, 1)}
    notices = []
    renpy = SimpleNamespace(session={}, log=notices.append, notify=notices.append)
    renpy.store = SimpleNamespace(Action=object)
    renpy.python = SimpleNamespace(store_dicts={"store": SimpleNamespace(get_changes=lambda *args: None)})
    renpy.can_load = lambda slot: native["marker"][0] is not None
    renpy.loadsave = SimpleNamespace(
        location=SimpleNamespace(load=lambda slot: (b"native", b"signature")),
        loads=lambda data: ({"store.snapshot_transaction_id": native["transaction"]}, None),
    )
    renpy.savetoken = SimpleNamespace(check_load=lambda *args: True)
    env = dict(store=state, persistent=persistent, renpy=renpy, os=SimpleNamespace(**vars(os)),
               shutil=shutil, json=json, _cp=copy, _=lambda value: value,
               config=SimpleNamespace(savedir=str(tmp_path), basedir=str(tmp_path)),
               save_is_allowed=lambda: True, _get_current_slot_name=lambda slot: "1-1",
               _native_save_commit_marker=lambda slot: native["marker"],
               _get_slot_guid=lambda slot: "guid", _acquire_snapshot_slot_lock=lambda slot: "lock",
               _release_snapshot_slot_lock=lambda token: None,
               _snapshot_is_complete_for_canonical_load=lambda snap: bool(snap and snap.get("money") is not None),
               _SNAPSHOT_PROGRESS_DEFAULTS={}, DEBUG_SNAPSHOT=False)
    names = ["_get_snapshot_file_path", "_get_backup_file_path", "_get_snapshot_file_path_for_reading",
             "_get_backup_file_path_for_reading", "_read_snapshot_file", "_create_backup",
             "_previous_snapshot_backup_temp_path", "_preserve_previous_snapshot_backup",
             "_cleanup_previous_snapshot_backup", "_restore_snapshot_after_failed_native_save",
             "_cleanup_stale_snapshot_temps", "_read_native_snapshot_transaction_id",
             "_canonical_snapshot_matches_identity", "_prepare_canonical_snapshot_load"]
    for optional in ("_snapshot_load_candidates", "_native_save_marker_advanced", "_snapshot_progress_value_valid"):
        if f"    def {optional}(" in SOURCE:
            names.append(optional)
    for name in names:
        exec(definition(name), env)
    exec(definition("SnapshotFileSave", kind="class"), env)

    def snap(transaction, money):
        return {"snapshot_slot": "1-1", "snapshot_guid": "guid", "snapshot_transaction_id": transaction,
                "snapshot_version": 3, "money": money}

    def write(path, data):
        Path(path).write_text(json.dumps(data), encoding="utf-8")

    main = Path(env["_get_snapshot_file_path"]("1-1"))
    backup = Path(env["_get_backup_file_path"]("1-1"))
    recovery = Path(env["_previous_snapshot_backup_temp_path"]("1-1"))
    write(main, snap("old", 100))
    write(backup, snap("old", 100))

    def stage(slot):
        env["_create_backup"](str(main), "1-1")
        write(main, snap("new", 200))
        renpy.session["_fm_snapshot_pre_save_may_have_touched_main"] = True
        state.snapshot_transaction_id = "new"
        return True

    def native_save():
        if mode == "fail":
            raise OSError("injected native write failure")
        if mode == "cancel":
            return
        native.update(transaction="new", marker=(2, 2))
        if mode == "post_commit_fail":
            raise OSError("injected failure after native commit")

    env["snapshot_pre_save_slot"] = stage
    renpy.store.FileSave = lambda *args, **kwargs: native_save
    return SimpleNamespace(env=env, state=state, native=native, main=main, backup=backup, recovery=recovery,
                           persistent=persistent, write=write, snap=snap, notices=notices)


@pytest.mark.parametrize("mode", ["fail", "cancel"])
def test_failed_native_save_restores_previous_pair(tmp_path, mode):
    qa = environment(tmp_path, mode)
    qa.env["SnapshotFileSave"](1)()
    assert qa.native["transaction"] == qa.state.snapshot_transaction_id == "old"
    assert json.loads(qa.main.read_text())["money"] == 100
    assert qa.main.read_bytes() == qa.backup.read_bytes()
    assert not qa.recovery.exists()


def test_failed_restore_keeps_last_recoverable_generation(tmp_path):
    qa = environment(tmp_path)
    real_replace = os.replace

    def fail_restore(source, destination):
        if str(source).endswith(".restore.tmp"):
            raise OSError("injected restore failure")
        real_replace(source, destination)

    qa.env["os"].replace = fail_restore
    qa.env["SnapshotFileSave"](1)()
    assert qa.recovery.exists(), "the last matching sidecar must survive a failed restore"
    assert json.loads(qa.recovery.read_text())["money"] == 100
    assert qa.env["_prepare_canonical_snapshot_load"](1)
    assert qa.persistent._canonical_snapshot_load_pending["source_name"] == "RECOVERY"


def test_interrupted_save_loads_recovery_and_can_be_saved_again(tmp_path):
    qa = environment(tmp_path, "success")
    qa.write(qa.recovery, qa.snap("old", 100))
    qa.write(qa.main, qa.snap("interrupted", 200))
    qa.write(qa.backup, qa.snap("interrupted", 200))
    assert qa.env["_prepare_canonical_snapshot_load"](1)
    assert qa.persistent._canonical_snapshot_load_pending["source_name"] == "RECOVERY"
    qa.env["SnapshotFileSave"](1)()
    assert qa.native["transaction"] == "new"
    assert not qa.recovery.exists()
    assert qa.env["_prepare_canonical_snapshot_load"](1)


def test_recovery_file_is_not_stale_temporary_garbage(tmp_path):
    qa = environment(tmp_path)
    qa.write(qa.recovery, qa.snap("old", 100))
    os.utime(qa.recovery, (1, 1))
    garbage = tmp_path / "snapshot_1-1.json.restore.tmp"
    garbage.write_text("partial")
    os.utime(garbage, (1, 1))
    qa.env["_cleanup_stale_snapshot_temps"]()
    assert qa.recovery.exists()
    assert not garbage.exists()


def test_exception_after_native_commit_does_not_roll_back_sidecar(tmp_path):
    qa = environment(tmp_path, "post_commit_fail")
    qa.env["SnapshotFileSave"](1)()
    assert qa.native["transaction"] == qa.state.snapshot_transaction_id == "new"
    assert json.loads(qa.main.read_text())["snapshot_transaction_id"] == "new"
    assert qa.env["_prepare_canonical_snapshot_load"](1)


def test_declining_native_save_trust_never_unpickles(tmp_path):
    qa = environment(tmp_path)
    calls = []
    qa.env["renpy"].savetoken.check_load = lambda *args: calls.append("check") or False
    qa.env["renpy"].loadsave.loads = lambda data: calls.append("unpickle") or ({}, None)
    with pytest.raises(ValueError):
        qa.env["_read_native_snapshot_transaction_id"]("1-1")
    assert calls == ["check"]


def test_first_save_failure_leaves_no_orphan_sidecars(tmp_path):
    qa = environment(tmp_path)
    qa.main.unlink()
    qa.backup.unlink()
    qa.native.update(transaction=None, marker=(None, None))
    qa.state.snapshot_transaction_id = None
    qa.env["SnapshotFileSave"](1)()
    assert not qa.main.exists() and not qa.backup.exists() and not qa.recovery.exists()
    assert qa.state.snapshot_transaction_id is None


def test_corrupt_main_does_not_destroy_matching_backup_when_save_fails(tmp_path):
    qa = environment(tmp_path)
    qa.main.write_text("{broken")
    qa.env["SnapshotFileSave"](1)()
    assert json.loads(qa.main.read_text())["money"] == 100
    assert qa.main.read_bytes() == qa.backup.read_bytes()


def test_unmatched_orphan_is_not_deleted_by_a_failed_overwrite(tmp_path):
    qa = environment(tmp_path)
    qa.native.update(transaction=None, marker=(None, None))
    before = qa.main.read_bytes(), qa.backup.read_bytes()
    qa.env["SnapshotFileSave"](1)()
    assert (qa.main.read_bytes(), qa.backup.read_bytes()) == before


def test_mtime_touch_is_not_a_native_commit(tmp_path):
    qa = environment(tmp_path)
    qa.env["renpy"].store.FileSave = lambda *args, **kwargs: lambda: qa.native.update(marker=(2, 1))
    qa.env["SnapshotFileSave"](1)()
    assert json.loads(qa.main.read_text())["snapshot_transaction_id"] == "old"
    assert qa.state.snapshot_transaction_id == "old"


@pytest.mark.parametrize("field, value", [("snapshot_slot", "1-2"), ("snapshot_guid", "foreign"),
                                           ("snapshot_transaction_id", "another-write")])
def test_foreign_recovery_never_loads(tmp_path, field, value):
    qa = environment(tmp_path)
    snap = qa.snap("old", 100)
    snap[field] = value
    qa.write(qa.recovery, snap)
    qa.main.unlink()
    qa.backup.unlink()
    assert not qa.env["_prepare_canonical_snapshot_load"](1)


def test_overwrite_confirmation_defers_the_whole_transaction(tmp_path):
    qa = environment(tmp_path, "success")
    pending = []
    qa.env["renpy"].store.Confirm = lambda message, yes, no: lambda: pending.append(yes)
    before = qa.main.read_bytes(), qa.backup.read_bytes()
    qa.env["SnapshotFileSave"](1, confirm=True)()
    assert len(pending) == 1
    assert (qa.main.read_bytes(), qa.backup.read_bytes()) == before
    assert qa.native["transaction"] == "old"
    assert not qa.recovery.exists()
    pending[0]()
    assert qa.native["transaction"] == "new"
    assert qa.env["_prepare_canonical_snapshot_load"](1)


def test_busy_slot_does_not_mutate_any_save(tmp_path):
    qa = environment(tmp_path, "success")
    qa.env["_acquire_snapshot_slot_lock"] = lambda slot: None
    before = qa.main.read_bytes(), qa.backup.read_bytes()
    qa.env["SnapshotFileSave"](1)()
    assert (qa.main.read_bytes(), qa.backup.read_bytes()) == before
    assert qa.native["transaction"] == "old"
