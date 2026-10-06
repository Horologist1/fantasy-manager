"""Android import lifecycle, with JNI outside the save store and real pack validation."""
import json
import base64
from pathlib import Path
import sys
from types import SimpleNamespace
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_mods import runtime, packs


@pytest.fixture
def phone(tmp_path, monkeypatch):
    state = {"status": "picking"}
    calls = []
    native = SimpleNamespace(start=lambda: calls.append("start"), poll=lambda: state,
                             discard=lambda: calls.append("discard"))
    engine = SimpleNamespace(invoke_in_thread=lambda job, *args: job(*args),
                             invoke_in_main_thread=lambda job: job(), restart_interaction=lambda: None)
    monkeypatch.setitem(sys.modules, "renpy", engine)
    monkeypatch.setattr(runtime, "android_picker", native)
    for key, value in {
        "_root": str(tmp_path / "installed"), "_reserved_names": [],
        "_known_files": {"data/items/example.json"}, "_mounted_ids": set(), "_startup_ids": set(),
        "_plan": None, "_android_pending": False, "_android_source": False,
        "_state": {"busy": False, "message": "", "preview": None, "installed": [], "override_mode": False},
    }.items():
        monkeypatch.setattr(runtime, key, value)
    return engine, state, calls, tmp_path


def pick(phone, content):
    engine, state, calls, folder = phone
    source = folder / "selected.zip"
    with zipfile.ZipFile(source, "w") as archive:
        for name, data in content.items():
            archive.writestr(name, data if isinstance(data, bytes) else json.dumps(data))
    runtime.start_android_picker(engine)
    state.update(status="ready", path=str(source))
    runtime.poll_android_picker(engine)
    return source


def test_cancel_does_not_install_or_enable_override_and_allows_retry(phone):
    engine, state, calls, _ = phone
    runtime.start_android_picker(engine)
    runtime.start_android_picker(engine)  # Rapid double tap must open one picker.
    assert calls == ["start"]
    state.update(status="cancelled")
    runtime.poll_android_picker(engine)
    assert not runtime.state()["busy"] and not runtime.state()["override_mode"]
    assert not packs.installed_packs(runtime._root)
    runtime.start_android_picker(engine)
    assert calls.count("start") == 2


def test_copied_override_uses_existing_validation_install_and_restart_mount(phone):
    engine, state, calls, folder = phone
    runtime.set_override_mode(True)
    pick(phone, {"data/items/example.json": {"items": [{"id": "herb", "price": 42}]}})
    assert runtime.state()["preview"]["mode"] == "override"
    assert not runtime.state()["busy"] and "discard" not in calls
    runtime.start_install(engine)
    assert calls[-1] == "discard"
    assert runtime._plan is None and not runtime.state()["override_mode"]
    mounted = packs.mount_paths(runtime._root)
    assert json.loads((Path(mounted[0]) / "data/items/example.json").read_text())["items"][0]["price"] == 42
    pack_id = packs.installed_packs(runtime._root)[0]["id"]
    runtime.start_uninstall(engine, pack_id)
    assert Path(mounted[0]).exists()  # Files remain for the active session.
    assert packs.finish_uninstalls(runtime._root) == []
    assert packs.mount_paths(runtime._root) == []


def test_regular_character_zip_does_not_need_override(phone):
    engine, _, calls, _ = phone
    pick(phone, {"workers.json": [{"name": "Android Test", "folder": "android_test", "gender": "female", "skills": {"Craft": 30}, "traits": ["Human"], "cost": 1}],
                 "images/workers/android_test/profile.png": base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")})
    assert runtime.state()["preview"]["workers"] == 1
    runtime.start_install(engine)
    assert packs.installed_packs(runtime._root)[0]["workers"] == 1
    assert calls[-1] == "discard"


def test_invalid_selection_releases_staging_and_can_select_again(phone):
    engine, _, calls, _ = phone
    pick(phone, {"data/items/example.json": {"items": [{"id": "herb"}]}})
    assert runtime.state()["preview"] is None and not runtime.state()["busy"]
    assert calls[-1] == "discard"
    runtime.start_android_picker(engine)
    assert calls[-1] == "start"


def test_preview_retains_copy_until_deselection(phone):
    runtime.set_override_mode(True)
    pick(phone, {"data/items/example.json": {"items": [{"id": "herb"}]}})
    assert runtime._android_source
    runtime.set_override_mode(False)
    assert phone[2][-1] == "discard"
    assert runtime._plan is None and not runtime._android_source


@pytest.mark.parametrize("status", ["error", "idle"])
def test_copy_failure_or_cancelled_copy_clears_busy(phone, status):
    engine, state, calls, _ = phone
    runtime.start_android_picker(engine)
    state.update(status=status, message="Storage unavailable")
    runtime.poll_android_picker(engine)
    assert not runtime.state()["busy"]
    assert runtime.state()["message"] == "Storage unavailable"
    assert calls[-1] == "discard"


def test_jni_failure_is_recoverable(phone, monkeypatch):
    def broken():
        raise RuntimeError("Missing bridge")
    monkeypatch.setattr(runtime.android_picker, "start", broken)
    runtime.start_android_picker(phone[0])
    assert not runtime.state()["busy"]
    assert "Missing bridge" in runtime.state()["message"]
    assert runtime._plan is None


def test_apk_without_bridge_explains_the_packaging_fault(phone, monkeypatch):
    def missing():
        raise RuntimeError("Class not found b'org/fantasymanager/mods/ModImportActivity'")
    monkeypatch.setattr(runtime.android_picker, "start", missing)
    runtime.start_android_picker(phone[0])
    assert not runtime.state()["busy"]
    assert "packaged without the mod importer" in runtime.state()["message"]
    assert "b'org/" not in runtime.state()["message"]
