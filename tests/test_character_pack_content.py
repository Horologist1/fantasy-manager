"""Character packs carrying events, traits, recruitment scenes and daily stories."""
import base64
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_mods.packs import (PackError, inspect_pack, install_pack, installed_packs, mount_paths,
                          game_catalog, check_pack_content)

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")
CATALOG = {"traits": {"Human", "Elf"}, "events": {"shipped_event"}, "stories": {"adventurer_story1"},
           "professions": {"adventurers_guild": {"adventurer", "boss_hunting"}}}


def worker(name="Suzuka", folder="Suzuka"):
    return {"name": name, "folder": folder, "gender": "female", "skills": {"Agility": 55},
            "traits": ["Velox"], "nsfw": False, "cost": 400}


def event(event_id="unique_suzuka_ascent", **extra):
    row = {"id": event_id, "worker_name": "Suzuka", "conditions": {"start_when": "has_worker:Suzuka"},
           "choices": [{"option": "Go", "effect": {"success": {"event_flags": {"suzuka_done": True}}}}]}
    row.update(extra)
    return row


def stories(merge_mode="append", story_id="windchaser_ridge"):
    return {"daily_story_extensions": [{"building_id": "adventurers_guild", "profession_id": "adventurer",
                                         "merge_mode": merge_mode, "daily_stories": [{"id": story_id, "weight": 1}]}]}


def pack(tmp_path, files=None, workers=True, name="velox.zip"):
    path = tmp_path / name
    defaults = {
        "game/data/traits/velox.json": [{"name": "Velox"}],
        "game/data/events/suzuka.json": [event()],
        "game/data/events/recruit/suzuka.json": [{"id": "event_recruit_suzuka", "worker_name": "Suzuka"}],
        "game/data/buildings/daily_story_extensions/velox.json": stories(),
    }
    defaults.update(files or {})
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("README.txt", "Install instructions")
        if workers:
            z.writestr("game/data/workers/suzuka.json", json.dumps([worker()]))
            z.writestr("game/images/workers/Suzuka/profile (1).png", PNG)
        for filename, value in defaults.items():
            if value is not None:
                z.writestr(filename, value if isinstance(value, str) else json.dumps(value))
    return path


def test_content_is_previewed_installed_and_mounted_as_namespaced_files(tmp_path):
    plan = inspect_pack(pack(tmp_path), CATALOG)
    assert {kind: len(rows) for kind, rows in plan["content"].items()} == {"traits": 1, "events": 1, "recruit": 1, "stories": 1}
    assert plan["warnings"] == []  # README is documentation, not an excluded file.
    root = tmp_path / "installed"
    assert install_pack(plan, root, catalog=CATALOG) == "installed"
    content = Path(mount_paths(root)[0])
    pid = plan["id"]
    assert json.loads((content / "data/traits" / (pid + ".json")).read_text())[0]["name"] == "Velox"
    assert json.loads((content / "data/events" / (pid + ".json")).read_text())[0]["id"] == "unique_suzuka_ascent"
    assert (content / "data/events/recruit" / (pid + ".json")).is_file()
    ext = json.loads((content / "data/buildings/daily_story_extensions" / (pid + ".json")).read_text())
    assert ext["daily_story_extensions"][0]["merge_mode"] == "append"
    manifest = installed_packs(root)[0]
    assert set(manifest["content_ids"]["events"]) == {"unique_suzuka_ascent", "event_recruit_suzuka"}


def test_worker_only_packs_keep_their_previous_identity(tmp_path):
    empty = {key: None for key in ("game/data/traits/velox.json", "game/data/events/suzuka.json",
                                   "game/data/events/recruit/suzuka.json", "game/data/buildings/daily_story_extensions/velox.json")}
    plan = inspect_pack(pack(tmp_path, empty))
    assert plan["content"] == {}
    import hashlib
    canonical = json.dumps({"workers": plan["workers"], "images": [(i["relative"], i["sha256"]) for i in plan["images"]]},
                           sort_keys=True, ensure_ascii=False).encode("utf-8")
    assert plan["id"] == "mod_" + hashlib.sha256(canonical).hexdigest()[:20]


def test_content_only_pack_installs_without_workers(tmp_path):
    plan = inspect_pack(pack(tmp_path, workers=False), CATALOG)
    assert plan["workers"] == []
    root = tmp_path / "installed"
    install_pack(plan, root, catalog=CATALOG)
    assert installed_packs(root)[0]["workers"] == 0
    content = Path(mount_paths(root)[0])
    assert not (content / "data/workers").exists()


@pytest.mark.parametrize("files, message", [
    ({"game/data/traits/velox.json": [{"name": "Elf"}]}, "already exists"),
    ({"game/data/events/suzuka.json": [event("shipped_event")]}, "already exists"),
    ({"game/data/events/suzuka.json": [event("event_recruit_x")]}, "data/events/recruit"),
    ({"game/data/buildings/daily_story_extensions/velox.json": stories("replace_all")}, "append"),
    ({"game/data/buildings/daily_story_extensions/velox.json": stories("upsert")}, "append"),
    ({"game/data/buildings/daily_story_extensions/velox.json": stories(story_id="adventurer_story1")}, "already exists"),
    ({"game/data/buildings/daily_story_extensions/velox.json": {"daily_story_extensions": [
        {"building_id": "castle", "profession_id": "king", "daily_stories": [{"id": "x"}]}]}}, "unknown profession"),
    ({"game/data/events/suzuka.json": [event(), event()]}, "Duplicate|written twice|duplicate"),
    ({"game/data/events/suzuka.json": '[{"id": "a", "threshold": 1, "threshold": 2}]'}, "written twice"),
])
def test_content_collisions_and_unsafe_merges_are_rejected(tmp_path, files, message):
    with pytest.raises(PackError, match=message):
        inspect_pack(pack(tmp_path, files), CATALOG)


@pytest.mark.parametrize("condition", [
    "store.renpy.exit.get(1) or True",
    "money.__class__ == 1",
    "has_flag:a AND store.x.get('y') == 1",
    "len(store.workers) > 1",
])
def test_conditions_the_game_would_eval_are_rejected(tmp_path, condition):
    files = {"game/data/events/suzuka.json": [event(conditions={"start_when": condition})]}
    with pytest.raises(PackError, match="unsupported condition"):
        inspect_pack(pack(tmp_path, files), CATALOG)


@pytest.mark.parametrize("condition", [
    "has_worker:Suzuka", "has_flag:a AND after_days:10", "store.current_objective >= 7",
    "store.lanista_gender == 'male'", "money >= 5000 OR has_flag:rich", "True",
])
def test_data_only_conditions_are_accepted(tmp_path, condition):
    files = {"game/data/events/suzuka.json": [event(conditions={"start_when": condition})]}
    inspect_pack(pack(tmp_path, files), CATALOG)


def test_evaluated_event_flag_values_are_rejected_anywhere(tmp_path):
    bad = event()
    bad["choices"][0]["effect"]["failure"] = {"event_flags": {"x": "[__import__('os').getcwd()]"}}
    with pytest.raises(PackError, match="code"):
        inspect_pack(pack(tmp_path, {"game/data/events/suzuka.json": [bad]}), CATALOG)


def test_renamed_worker_keeps_its_events_and_folder_references(tmp_path):
    special = event(specific_worker_images=["Suzuka"], conditions={"start_when": "has_worker:Suzuka AND has_folder_worker:Suzuka"})
    plan = inspect_pack(pack(tmp_path, {"game/data/events/suzuka.json": [special]}), CATALOG)
    root = tmp_path / "installed"
    install_pack(plan, root, ["Suzuka"], rename_conflicts=True, catalog=CATALOG)
    content = Path(mount_paths(root)[0])
    row = json.loads((content / "data/events" / (plan["id"] + ".json")).read_text())[0]
    new_name = installed_packs(root)[0]["worker_names"][0]
    assert new_name.startswith("Suzuka (Mod ")
    assert row["worker_name"] == new_name
    assert row["specific_worker_images"] == [plan["id"] + "__Suzuka"]
    assert row["conditions"]["start_when"] == "has_worker:" + new_name + " AND has_folder_worker:" + plan["id"] + "__Suzuka"


def test_two_packs_cannot_claim_the_same_event_id(tmp_path):
    root = tmp_path / "installed"
    first = inspect_pack(pack(tmp_path), CATALOG)
    install_pack(first, root, catalog=CATALOG)
    other = {"game/data/traits/velox.json": [{"name": "Velox Two"}]}
    second = inspect_pack(pack(tmp_path, other, workers=False, name="other.zip"), CATALOG)
    with pytest.raises(PackError, match="Another installed pack"):
        check_pack_content(second, root)
    with pytest.raises(PackError, match="already exists"):
        install_pack(second, root, catalog=CATALOG)
    assert len(installed_packs(root)) == 1
    check_pack_content(first, root)  # Re-previewing an installed pack is not a clash.


def test_tampered_installed_content_is_not_mounted(tmp_path):
    plan = inspect_pack(pack(tmp_path), CATALOG)
    root = tmp_path / "installed"
    install_pack(plan, root, catalog=CATALOG)
    target = root / plan["id"] / "content/data/events" / (plan["id"] + ".json")
    target.write_text(json.dumps([event(conditions={"start_when": "len(x) > 1"})]))
    assert mount_paths(root) == []


def test_unlisted_json_in_installed_pack_is_not_mounted(tmp_path):
    plan = inspect_pack(pack(tmp_path), CATALOG)
    root = tmp_path / "installed"
    install_pack(plan, root, catalog=CATALOG)
    extra = root / plan["id"] / "content/data/events/injected.json"
    extra.write_text("[]")
    assert mount_paths(root) == []


def test_game_catalog_reads_shipped_identifiers():
    game = ROOT / "game"
    files = [p.relative_to(game).as_posix() for p in (game / "data").rglob("*.json")]
    catalog = game_catalog(files, lambda name: (game / name).read_bytes())
    assert "Elf" in catalog["traits"]
    assert "boss_hunting" in catalog["professions"]["adventurers_guild"]
    assert "boss_hunting_story1" in catalog["stories"]
    assert "event_recruit_aelis" in catalog["events"] or any(e.startswith("event_recruit_") for e in catalog["events"])


def test_published_template_pack_passes_the_real_importer(tmp_path):
    game = ROOT / "game"
    files = [p.relative_to(game).as_posix() for p in (game / "data").rglob("*.json")]
    catalog = game_catalog(files, lambda name: (game / name).read_bytes())
    plan = inspect_pack(ROOT / "user_docs/templates/character_pack", catalog)
    assert plan["warnings"] == []
    assert {kind: len(rows) for kind, rows in plan["content"].items()} == {"traits": 2, "events": 1, "recruit": 1, "stories": 1}
    assert [w["name"] for w in plan["workers"]] == ["Mira"]
    install_pack(plan, tmp_path / "installed", catalog=catalog)
    assert len(mount_paths(tmp_path / "installed")) == 1


def test_day_stamp_flag_for_delayed_chains_is_allowed(tmp_path):
    row = event()
    row["choices"][0]["effect"]["success"]["event_flags"]["suzuka_day"] = "[calculate_total_days()]"
    follow = event("suzuka_follow_up", conditions={"start_when": "after_days_from_flag:suzuka_day,7"})
    inspect_pack(pack(tmp_path, {"game/data/events/suzuka.json": [row, follow]}), CATALOG)


def test_null_conditions_written_by_the_devkit_are_accepted(tmp_path):
    files = {"game/data/events/suzuka.json": [event(conditions={"start_when": None, "stop_when": None})]}
    inspect_pack(pack(tmp_path, files), CATALOG)
