"""Opt-in whole-file overrides: parsing, ordering, isolation and recovery."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_mods import packs, runtime

CATALOGS = {
    "data/monthly_conditions/cards.json": [{"id": "quiet_month", "name": "Quiet month", "description": "No modifiers.", "effects": []}],
    "data/workers/people.json": [{"name": "Test", "folder": "existing"}],
    "data/items/items.json": {"items": [{"id": "apple", "cost": 5}]},
    "data/traits/traits_core.json": [{"name": "Beautiful", "description": "Changed"}],
    "data/buildings/building_types.json": {"building_types": [{"id": "brothel"}]},
    "data/buildings/daily_story_extensions/story.json": {"building_id": "brothel", "profession_id": "service", "daily_stories": []},
    "data/events/events_common.json": [{"id": "test", "description": "Changed"}],
    "data/events/recruit/event.json": [{"id": "recruit_test"}],
}


def source(tmp_path, entries=None, title="override", prefix="wrapper/game/"):
    path = tmp_path / (title + ".zip")
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in (entries or CATALOGS).items():
            archive.writestr(prefix + name, data if isinstance(data, bytes) else json.dumps(data))
    return path


def install(tmp_path, entries=None, title="override"):
    path = source(tmp_path, entries, title)
    plan = packs.inspect_override_pack(path, CATALOGS)
    assert packs.install_override_pack(plan, tmp_path / "installed", CATALOGS) == "installed"
    return plan


def test_every_supported_catalog_is_preserved_as_a_whole_file(tmp_path):
    plan = install(tmp_path)
    mounted = Path(packs.mount_paths(tmp_path / "installed")[0])
    assert len(plan["files"]) == len(CATALOGS)
    for name, data in CATALOGS.items():
        assert json.loads((mounted / name).read_text()) == data
    assert packs.installed_packs(tmp_path / "installed")[0]["mode"] == "override"
    assert packs.install_override_pack(plan, tmp_path / "installed", CATALOGS) == "already_installed"


def test_folder_and_wrapped_zip_have_same_identity(tmp_path):
    archive = source(tmp_path)
    folder = tmp_path / "folder"
    for name, value in CATALOGS.items():
        target = folder / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value))
    assert packs.inspect_override_pack(folder, CATALOGS)["id"] == packs.inspect_override_pack(archive, CATALOGS)["id"]


def test_shipped_worker_catalogs_with_templates_and_rating_variants_can_be_overridden(tmp_path):
    for filename in ("workers_monster_templates.json", "kar.json", "kara.json"):
        relative = "data/workers/" + filename
        data = (ROOT / "game" / relative).read_bytes()
        archive = source(tmp_path, {relative: data}, title=filename)
        plan = packs.inspect_override_pack(archive, [relative])
        assert plan["files"][0]["path"] == relative
        assert packs.install_override_pack(plan, tmp_path / (filename + "_installed"), [relative]) == "installed"
        mounted = packs.mount_paths(tmp_path / (filename + "_installed"))
        assert len(mounted) == 1
        assert (Path(mounted[0]) / relative).read_bytes() == data


@pytest.mark.parametrize("rows", [
    [{"procedural_template": True, "template_id": "goblin"}] * 2,
    [{"procedural_template": True}],
    [{"name": "Same", "nsfw": False}] * 2,
    [{"name": "Same", "nsfw": True}] * 2,
    [{"name": "Same"}, {"name": "Same", "nsfw": False}],
    [{"name": "Same", "nsfw": []}],
])
def test_worker_override_identity_fix_keeps_duplicate_and_malformed_checks(tmp_path, rows):
    relative = "data/workers/test.json"
    with pytest.raises(packs.PackError):
        packs.inspect_override_pack(source(tmp_path, {relative: rows}), [relative])


def test_ordinary_character_inspector_does_not_implicitly_enable_override(tmp_path):
    with pytest.raises(packs.PackError):
        packs.inspect_pack(source(tmp_path, {"data/items/items.json": CATALOGS["data/items/items.json"]}))


@pytest.mark.parametrize("path", ["data/items/unknown.json", "data/items/Items.json", "data/workers/new.json"])
def test_override_requires_exact_shipped_target(tmp_path, path):
    archive = source(tmp_path, {path: []})
    with pytest.raises(packs.PackError, match="does not exist"):
        packs.inspect_override_pack(archive, CATALOGS)


@pytest.mark.parametrize("bad", [b"{", b'[{"name":"x","name":"y"}]', b'[{"name":"x","value":NaN}]', b'[{"name":"x","value":1e999}]', b'[null]', b'[{}]', b'[{"name":"x"},{"name":"x"}]'])
def test_invalid_json_never_installs(tmp_path, bad):
    archive = source(tmp_path, {"data/traits/traits_core.json": bad})
    with pytest.raises(packs.PackError):
        packs.inspect_override_pack(archive, CATALOGS)
    assert not (tmp_path / "installed").exists()


def test_scripts_images_and_other_json_are_excluded(tmp_path):
    entries = dict(CATALOGS, **{"scripts/mod.rpy": b"never execute", "images/base.png": b"not imported", "data/settings.json": {}})
    plan = install(tmp_path, entries)
    assert "3 other file(s) excluded" in plan["warnings"][-1]
    mounted = Path(packs.mount_paths(tmp_path / "installed")[0])
    assert {p.relative_to(mounted).as_posix() for p in mounted.rglob("*") if p.is_file()} == set(CATALOGS)


def test_multiple_roots_rejected(tmp_path):
    path = source(tmp_path, {"a/data/items/items.json": CATALOGS["data/items/items.json"], "b/data/traits/traits_core.json": []}, prefix="")
    with pytest.raises(packs.PackError, match="Several game roots"):
        packs.inspect_override_pack(path, CATALOGS)


@pytest.mark.parametrize("bad_path", ["../data/items/items.json", "C:/data/items/items.json", "data/../items/items.json"])
def test_unsafe_source_paths_rejected(tmp_path, bad_path):
    with pytest.raises(packs.PackError, match="Unsafe path"):
        packs.inspect_override_pack(source(tmp_path, {bad_path: []}, prefix=""), CATALOGS)


def test_changed_source_is_rejected_before_writes(tmp_path):
    path = source(tmp_path)
    plan = packs.inspect_override_pack(path, CATALOGS)
    source(tmp_path, {"data/traits/traits_core.json": [{"name": "Changed"}]})
    with pytest.raises(packs.PackError, match="source changed"):
        packs.install_override_pack(plan, tmp_path / "installed", CATALOGS)
    assert not (tmp_path / "installed").exists()


@pytest.mark.parametrize("mutation", ["content", "script", "manifest_path", "manifest_order"])
def test_corrupt_installed_override_is_not_mounted(tmp_path, mutation):
    plan = install(tmp_path)
    directory = tmp_path / "installed" / plan["id"]
    if mutation == "content":
        (directory / "content/data/traits/traits_core.json").write_text("[]")
    elif mutation == "script":
        (directory / "content/injected.rpy").write_text("never execute")
    else:
        manifest = json.loads((directory / "manifest.json").read_text())
        if mutation == "manifest_path":
            manifest["files"][0]["path"] = "../outside.json"
        else:
            manifest["load_order"] = "bad"
        (directory / "manifest.json").write_text(json.dumps(manifest))
    assert packs.mount_paths(tmp_path / "installed") == []


def test_installation_order_wins_and_uninstall_exposes_previous_file(tmp_path, monkeypatch):
    first = install(tmp_path, title="first")
    second = install(tmp_path, {"data/items/items.json": {"items": [{"id": "apple", "cost": 29}]}}, "second")
    root = tmp_path / "installed"
    assert [p["load_order"] for p in packs.installed_packs(root)] == [1, 2]
    indexed = {}
    for directory in packs.mount_paths(root):
        with packs.Source(directory) as pack_source:
            indexed.update({name: str(path) for name, (path, _) in pack_source.entries.items()})
    monkeypatch.setattr(runtime, "_files", indexed)
    with runtime._open_file("data/items/items.json") as handle:
        assert json.load(handle)["items"][0]["cost"] == 29
    packs.schedule_uninstall(root, second["id"])
    with runtime._open_file("data/items/items.json") as handle:
        assert json.load(handle)["items"][0]["cost"] == 29  # current session stays intact
    assert len(packs.mount_paths(root)) == 1
    packs.schedule_uninstall(root, second["id"], cancel=True)
    assert len(packs.mount_paths(root)) == 2
    packs.schedule_uninstall(root, second["id"])
    original_source = Path(second["source"])
    original_hash = hashlib.sha256(original_source.read_bytes()).hexdigest()
    sentinel = root / "keep.save"
    sentinel.write_text("unrelated")
    assert packs.finish_uninstalls(root) == []
    assert sentinel.read_text() == "unrelated"
    assert hashlib.sha256(original_source.read_bytes()).hexdigest() == original_hash
    remaining = Path(packs.mount_paths(root)[0])
    assert json.loads((remaining / "data/items/items.json").read_text())["items"][0]["cost"] == 5
    assert packs.installed_packs(root)[0]["id"] == first["id"]


def test_failed_copy_leaves_existing_pack_and_save_intact(tmp_path, monkeypatch):
    first = install(tmp_path)
    plan = packs.inspect_override_pack(source(tmp_path, {"data/traits/traits_core.json": [{"name": "New"}]}, "second"), CATALOGS)
    original = Path.write_bytes
    def fail_json(path, data):
        if path.suffix == ".json":
            raise OSError("disk full")
        return original(path, data)
    monkeypatch.setattr(Path, "write_bytes", fail_json)
    with pytest.raises(OSError, match="disk full"):
        packs.install_override_pack(plan, tmp_path / "installed", CATALOGS)
    assert [p["id"] for p in packs.installed_packs(tmp_path / "installed")] == [first["id"]]
    assert not list((tmp_path / "installed").glob(".install-*"))


def test_mode_change_discards_stale_preview_and_is_ignored_while_busy(monkeypatch):
    state = {"busy": False, "override_mode": False, "preview": {"mode": "old"}, "message": "old"}
    monkeypatch.setattr(runtime, "_state", state)
    monkeypatch.setattr(runtime, "_plan", {"old": True})
    runtime.set_override_mode(True)
    assert state["override_mode"] and state["preview"] is None and runtime._plan is None
    state["busy"] = True
    runtime.set_override_mode(False)
    assert state["override_mode"]


def test_bootstrap_defaults_off_and_routes_overrides_before_normal_files(tmp_path, monkeypatch):
    install(tmp_path)
    savedir = tmp_path / "save-root"
    savedir.mkdir()
    (tmp_path / "installed").rename(savedir / "character_mods")
    fallback = lambda name: "original:" + name
    engine = SimpleNamespace(config=SimpleNamespace(savedir=str(savedir), file_open_callback=fallback, loadable_callback=None),
                             list_files=lambda: list(CATALOGS), file=lambda name: __import__("io").BytesIO(json.dumps(CATALOGS[name]).encode()),
                             loader=SimpleNamespace(scandirfiles_callbacks=[], cleardirfiles=lambda: None), log=lambda msg: None)
    for key in ("_root", "_state", "_plan", "_files", "_known_files", "_mounted_ids", "_startup_ids", "_reserved_names", "_previous_open", "_previous_loadable"):
        monkeypatch.setattr(runtime, key, getattr(runtime, key))
    runtime.bootstrap(engine)
    assert runtime.state()["override_mode"] is False
    assert runtime.state()["installed"][0]["active"]
    assert engine.config.file_open_callback("other.json") == "original:other.json"
    with engine.config.file_open_callback("data/items/items.json") as handle:
        assert json.load(handle) == CATALOGS["data/items/items.json"]
