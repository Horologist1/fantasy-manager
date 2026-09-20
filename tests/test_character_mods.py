"""Real pack parsing and additive/atomic filesystem installation contracts."""
import base64
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_mods.packs import (PackError, inspect_pack, install_pack, installed_packs,
                          mount_paths, schedule_uninstall, finish_uninstalls,
                          REMOVE_MARKER, REMOVE_PREFIX)

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")


def worker(name="Pack Worker", folder="pack_worker"):
    return {"name": name, "folder": folder, "gender": "female", "skills": {"Craft": 40}, "traits": ["Human"], "nsfw": False, "cost": 400}


def pack(tmp_path, rows=None, extra=None, prefix="wrapper/version/game/"):
    path = tmp_path / "pack.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(prefix + "data/workers/characters.json", json.dumps(rows or [worker()]))
        z.writestr(prefix + "images/workers/pack_worker/profile (1).png", PNG)
        for name, value in (extra or {}).items():
            z.writestr(name, value)
    return path


def test_nested_pack_is_additive_idempotent_and_preserves_shared_folders(tmp_path):
    path = pack(tmp_path, [worker(), worker("Second Worker")], {"wrapper/version/game/data/events/recruit/extra.json": "[]", "wrapper/version/game/scripts/evil.rpy": "init python:\n    raise Exception('never run')"})
    before = path.read_bytes()
    plan = inspect_pack(path)
    root = tmp_path / "installed"
    assert len(plan["workers"]) == 2 and len(plan["images"]) == 1
    assert plan["warnings"]
    assert install_pack(plan, root) == "installed"
    assert install_pack(plan, root) == "already_installed"
    assert path.read_bytes() == before
    assert len(installed_packs(root)) == len(mount_paths(root)) == 1
    content = Path(mount_paths(root)[0])
    rows = json.loads(next((content / "data/workers").glob("*.json")).read_text())
    assert rows[0]["folder"] == rows[1]["folder"]
    assert rows[0]["folder"].startswith(plan["id"])
    assert not list(content.rglob("*.rpy"))
    assert not (content / "data/events").exists()
    assert not list(root.glob(".install-*"))


def test_plain_workers_json_and_folder_have_same_identity_as_zip(tmp_path):
    folder = tmp_path / "folder"
    (folder / "images/workers/pack_worker").mkdir(parents=True)
    (folder / "workers.json").write_text(json.dumps({"workers": [worker()]}))
    (folder / "images/workers/pack_worker/profile (1).png").write_bytes(PNG)
    assert inspect_pack(folder)["id"] == inspect_pack(pack(tmp_path))["id"]


@pytest.mark.parametrize("bad_path", ["../outside.txt", "/absolute.txt", "C:/outside.txt", "a/../../outside.txt", "a\\..\\outside.txt", "a/file.png:evil", "a/CON.png", "a/file. "])
def test_rejects_unsafe_archive_paths_before_writing(tmp_path, bad_path):
    path = pack(tmp_path, extra={bad_path: "unsafe"})
    with pytest.raises(PackError):
        inspect_pack(path)
    assert not (tmp_path / "outside.txt").exists()


def test_conflicts_fail_without_partial_install(tmp_path):
    plan = inspect_pack(pack(tmp_path))
    root = tmp_path / "installed"
    with pytest.raises(PackError, match="already in the game"):
        install_pack(plan, root, ["PACK WORKER"])
    assert list(root.iterdir()) == []


def test_source_changed_after_preview_is_rejected(tmp_path):
    path = pack(tmp_path)
    plan = inspect_pack(path)
    pack(tmp_path, [worker("Different Worker")])
    with pytest.raises(PackError, match="changed after preview"):
        install_pack(plan, tmp_path / "installed")


def test_explicit_keep_both_renames_only_the_imported_conflict(tmp_path):
    plan = inspect_pack(pack(tmp_path, [worker(), worker("Second Worker")]))
    root = tmp_path / "installed"
    install_pack(plan, root, ["Pack Worker"], rename_conflicts=True)
    manifest = installed_packs(root)[0]
    assert manifest["worker_names"][0].startswith("Pack Worker (Mod ")
    assert manifest["worker_names"][1] == "Second Worker"
    assert manifest["renamed"][0]["original"] == "Pack Worker"


@pytest.mark.parametrize("change", [{"cost": -1}, {"skills": {"Craft": "100"}}, {"gender": 3}, {"nsfw": "false"}, {"folder": "../oops"}, {"name": "[money]"}, {"procedural": True}, {"traits": "Human"}])
def test_invalid_workers_are_rejected(tmp_path, change):
    row = worker()
    row.update(change)
    with pytest.raises(PackError):
        inspect_pack(pack(tmp_path, [row]))


def test_executable_added_to_installed_content_is_not_mounted(tmp_path):
    plan = inspect_pack(pack(tmp_path))
    root = tmp_path / "installed"
    install_pack(plan, root)
    path = Path(mount_paths(root)[0])
    (path / "injected.py").write_text("raise Exception('never run')")
    assert mount_paths(root) == []


@pytest.mark.parametrize("manifest", [[], {}, {"id": "wrong"}, {"format": 1, "worker_names": [None]}])
def test_corrupt_manifest_does_not_break_discovery(tmp_path, manifest):
    plan = inspect_pack(pack(tmp_path))
    root = tmp_path / "installed"
    install_pack(plan, root)
    (root / plan["id"] / "manifest.json").write_text(json.dumps(manifest))
    assert installed_packs(root) == []
    assert mount_paths(root) == []


@pytest.mark.parametrize("change", [{"skills": {"Craft": "invalid"}}, {"folder": "base_game_folder"}, {"name": "Changed name"}])
def test_damaged_installed_workers_are_not_mounted(tmp_path, change):
    plan = inspect_pack(pack(tmp_path))
    root = tmp_path / "installed"
    install_pack(plan, root)
    data = root / plan["id"] / "content/data/workers" / (plan["id"] + ".json")
    rows = json.loads(data.read_text())
    rows[0].update(change)
    data.write_text(json.dumps(rows))
    assert mount_paths(root) == []


def test_mod_loader_preserves_existing_callbacks(tmp_path, monkeypatch):
    from fm_mods import runtime
    imported = tmp_path / "profile.png"
    imported.write_bytes(PNG)
    monkeypatch.setattr(runtime, "_files", {"images/workers/mod_test/profile.png": str(imported)})
    monkeypatch.setattr(runtime, "_previous_open", lambda name: "previous:" + name)
    monkeypatch.setattr(runtime, "_previous_loadable", lambda name: name == "old-callback-file")
    with runtime._open_file("images/workers/mod_test/profile.png") as handle:
        assert handle.read() == PNG
    assert runtime._loadable("images/workers/mod_test/profile.png")
    assert runtime._open_file("unrelated.json") == "previous:unrelated.json"
    assert runtime._loadable("old-callback-file")
    assert not runtime._loadable("missing")


def test_unreadable_mod_directory_does_not_break_discovery(tmp_path, monkeypatch):
    def denied(path):
        raise PermissionError("simulated inaccessible mods directory")
    monkeypatch.setattr(Path, "is_dir", denied)
    assert installed_packs(tmp_path) == []


def test_failed_copy_rolls_back_only_its_own_staging_directory(tmp_path, monkeypatch):
    from fm_mods import packs
    plan = inspect_pack(pack(tmp_path))
    root = tmp_path / "installed"
    root.mkdir()
    sentinel = root / "keep.txt"
    sentinel.write_text("preserve")
    original = Path.write_bytes
    def fail_image(path, data):
        if path.suffix == ".png":
            raise OSError("simulated full disk")
        return original(path, data)
    monkeypatch.setattr(Path, "write_bytes", fail_image)
    with pytest.raises(OSError):
        packs.install_pack(plan, root)
    assert list(root.iterdir()) == [sentinel]
    assert sentinel.read_text() == "preserve"


def test_uninstall_can_be_cancelled_and_keeps_open_session_files(tmp_path):
    plan = inspect_pack(pack(tmp_path))
    root = tmp_path / "installed"
    install_pack(plan, root)
    content = Path(mount_paths(root)[0])
    image = next(content.rglob("*.png"))
    before = image.read_bytes()
    schedule_uninstall(root, plan["id"])
    schedule_uninstall(root, plan["id"])  # Repeated clicks are idempotent.
    assert installed_packs(root)[0]["pending_uninstall"]
    assert image.read_bytes() == before
    assert mount_paths(root) == []  # A new process must not mount it.
    with pytest.raises(PackError, match="Cancel its uninstall"):
        install_pack(plan, root)
    schedule_uninstall(root, plan["id"], cancel=True)
    schedule_uninstall(root, plan["id"], cancel=True)
    assert not installed_packs(root)[0]["pending_uninstall"]
    assert mount_paths(root) == [str(content)]
    assert finish_uninstalls(root) == []
    assert image.read_bytes() == before


def test_startup_removes_only_selected_pack_and_can_reinstall(tmp_path):
    root = tmp_path / "installed"
    first = inspect_pack(pack(tmp_path))
    install_pack(first, root)
    second = inspect_pack(pack(tmp_path, [worker("Other Worker")]))
    install_pack(second, root)
    original = Path(second["source"]).read_bytes()
    save = tmp_path / "slot.save"
    save.write_bytes(b"player progress")
    sentinel = root / "unrelated.txt"
    sentinel.write_bytes(b"keep")
    schedule_uninstall(root, first["id"])
    assert finish_uninstalls(root) == []
    assert not (root / first["id"]).exists()
    assert [p["id"] for p in installed_packs(root)] == [second["id"]]
    assert len(mount_paths(root)) == 1
    assert save.read_bytes() == b"player progress"
    assert sentinel.read_bytes() == b"keep"
    assert Path(second["source"]).read_bytes() == original
    assert finish_uninstalls(root) == []
    first = inspect_pack(pack(tmp_path))
    assert install_pack(first, root) == "installed"
    assert len(mount_paths(root)) == 2


@pytest.mark.parametrize("pack_id", ["../outside", "..", "", "C:/outside", "mod_" + "a" * 20 + "/../outside", None])
def test_uninstall_rejects_paths_and_invalid_ids(tmp_path, pack_id):
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(PackError, match="identifier"):
        schedule_uninstall(tmp_path, pack_id)
    assert list(outside.iterdir()) == []


def test_failed_removal_never_mounts_partial_pack_and_retries(tmp_path, monkeypatch):
    from fm_mods import packs
    root = tmp_path / "installed"
    plan = inspect_pack(pack(tmp_path))
    install_pack(plan, root)
    schedule_uninstall(root, plan["id"])
    original = packs.shutil.rmtree
    def fail_after_one_file(path):
        (path / "manifest.json").unlink()
        raise PermissionError("simulated locked image")
    monkeypatch.setattr(packs.shutil, "rmtree", fail_after_one_file)
    assert "locked image" in finish_uninstalls(root)[0]
    assert installed_packs(root) == mount_paths(root) == []
    retired = root / (REMOVE_PREFIX + plan["id"])
    assert retired.is_dir()
    monkeypatch.setattr(packs.shutil, "rmtree", original)
    assert finish_uninstalls(root) == []
    assert not retired.exists()


def test_failed_retirement_preserves_pack_and_pending_status(tmp_path, monkeypatch):
    root = tmp_path / "installed"
    plan = inspect_pack(pack(tmp_path))
    install_pack(plan, root)
    schedule_uninstall(root, plan["id"])
    def denied(*args):
        raise PermissionError("simulated folder lock")
    monkeypatch.setattr(Path, "rename", denied)
    assert "folder lock" in finish_uninstalls(root)[0]
    assert installed_packs(root)[0]["pending_uninstall"]
    assert mount_paths(root) == []
    assert (root / plan["id"] / "manifest.json").exists()


@pytest.mark.parametrize("location", ["root", "pack", "image", "marker"])
def test_uninstall_rejects_links_before_deleting_anything(tmp_path, monkeypatch, location):
    from fm_mods import packs
    root = tmp_path / "installed"
    plan = inspect_pack(pack(tmp_path))
    install_pack(plan, root)
    schedule_uninstall(root, plan["id"])
    target = root / plan["id"]
    image = next(target.rglob("*.png"))
    linked = {"root": root, "pack": target, "image": image, "marker": target / REMOVE_MARKER}[location]
    original = packs._is_link
    monkeypatch.setattr(packs, "_is_link", lambda path: path.name == linked.name or original(path))
    assert finish_uninstalls(root)
    assert image.read_bytes() == PNG
    assert target.exists()


def test_uninstall_jobs_refresh_ui_and_leave_mounted_callbacks_intact(tmp_path, monkeypatch):
    from fm_mods import runtime
    from types import SimpleNamespace
    plan = inspect_pack(pack(tmp_path))
    root = tmp_path / "installed"
    install_pack(plan, root)
    image = next((root / plan["id"]).rglob("*.png"))
    fake = SimpleNamespace(invoke_in_thread=lambda fn, *args: fn(*args),
                           invoke_in_main_thread=lambda fn: fn(), restart_interaction=lambda: None)
    monkeypatch.setitem(sys.modules, "renpy", fake)
    monkeypatch.setattr(runtime, "_root", str(root))
    monkeypatch.setattr(runtime, "_mounted_ids", {plan["id"]})
    monkeypatch.setattr(runtime, "_startup_ids", {plan["id"]})
    monkeypatch.setattr(runtime, "_state", {"busy": False, "message": "", "preview": None, "installed": []})
    monkeypatch.setattr(runtime, "_files", {"profile.png": str(image)})
    runtime.start_uninstall(fake, plan["id"])
    assert not runtime.state()["busy"]
    assert runtime.state()["installed"][0]["pending_uninstall"]
    assert runtime.state()["installed"][0]["active"]
    with runtime._open_file("profile.png") as handle:
        assert handle.read() == PNG
    runtime.start_uninstall(fake, plan["id"], cancel=True)
    assert not runtime.state()["installed"][0]["pending_uninstall"]
    runtime.start_uninstall(fake, "../bad")
    assert not runtime.state()["busy"]
    assert "Could not update" in runtime.state()["message"]
    runtime.state()["busy"] = True
    runtime.start_uninstall(fake, plan["id"])
    assert not (root / plan["id"] / REMOVE_MARKER).exists()
