"""Native fresh-game / UI / restart checks. Only a disposable copy is modified."""
import argparse
import base64
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_mods.packs import inspect_pack, install_pack, inspect_override_pack, install_override_pack, schedule_uninstall


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", default="D:/renpy-8.3.4-sdk/renpy.exe")
    parser.add_argument("--variant", default="")
    parser.add_argument("--fault", action="store_true", help="Negative control: disable routing in the disposable copy")
    args = parser.parse_args()
    run = ROOT / "backups" / ("override-qa-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    project = run / "project"
    run.mkdir(parents=True)
    print("QA directory: " + str(run), flush=True)
    def copy_asset(source, target):
        if Path(source).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".ttf", ".ogg", ".mp3", ".wav", ".mp4", ".webm"}:
            try:
                os.link(source, target)
                return target
            except OSError:
                pass
        return shutil.copy2(source, target)
    shutil.copytree(ROOT / "game", project / "game", copy_function=copy_asset,
                    ignore=shutil.ignore_patterns("saves", "cache", "__pycache__", "*.rpyc", "*.rpyb", "*.rpymc", "*.pyc", "qa_*.rpy"))
    shutil.copy2(ROOT / "tools/qa_json_overrides.rpy", project / "game/qa_json_overrides.rpy")
    # Skip only the introductory narration/title/name interaction. Run the
    # actual start label, reset, catalog loading, market and initialization.
    flow = project / "game/scripts/main_flow.rpy"
    text = flow.read_text(encoding="utf-8")
    first = text.index("    # Start with the inheritance scene\n")
    last = text.index("    # Initialize the calendar with forced reset ONLY", first)
    text = text[:first] + '    $ player_title = "Lord"\n    $ player_name = "Override QA"\n\n' + text[last:]
    anchor = "label tavern_screen():\n"
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + "    jump qa_mod_started\n", 1)
    flow.write_text(text, encoding="utf-8")
    snapshot = project / "game/scripts/save_snapshot.rpy"
    text = snapshot.read_text(encoding="utf-8")
    anchor = "    # FM-SAVE-ANCHOR: after-load-end\n    jump tavern_screen\n"
    assert text.count(anchor) == 1
    snapshot.write_text(text.replace(anchor, "    # FM-SAVE-ANCHOR: after-load-end\n    jump qa_mod_loaded\n", 1), encoding="utf-8")
    if args.fault:
        runtime = project / "game/python-packages/fm_mods/runtime.py"
        text = runtime.read_text(encoding="utf-8")
        assert "path = _files.get(name)" in text
        runtime.write_text(text.replace("path = _files.get(name)", "path = None  # deliberate negative control"), encoding="utf-8")
    paths = ["data/workers/workers_sfw_other.json", "data/items/alchemy_ingredients.json",
             "data/traits/traits_core.json", "data/buildings/building_types.json",
             "data/buildings/daily_story_extensions/relationship_brothel_service.json",
             "data/events/events_common.json"]
    before = {p: hashlib.sha256((ROOT / "game" / p).read_bytes()).hexdigest() for p in paths}
    data = {p: json.loads((ROOT / "game" / p).read_text(encoding="utf-8-sig")) for p in paths}
    worker = data[paths[0]][0]
    item = data[paths[1]]["items"][0]
    trait = next(t for t in data[paths[2]] if t["name"] == "Beautiful")
    building = next(b for b in data[paths[3]]["building_types"] if b["id"] == "brothel")
    story = data[paths[4]]["daily_stories"][0]
    event = data[paths[5]][0]
    baseline = {"worker_folder": worker["folder"], "worker_cost": worker["cost"], "item_id": item["id"], "item_price": item["price"],
                "trait_description": trait["description"], "building_name": building["name"], "story_id": story["id"],
                "story_report": story["report"], "event_id": event["id"], "event_description": event["description"]}
    worker["cost"] = 432
    item["price"] = 211
    trait["description"] = "QA replacement trait description."
    building["name"] = "QA replacement building"
    story["report"] = "QA replacement daily story"
    event["description"] = "QA replacement event description."
    override = dict(baseline, worker_cost=432, item_price=211, trait_description=trait["description"],
                    building_name=building["name"], story_report=story["report"], event_description=event["description"])
    def archive(name, entries):
        path = run / (name + ".zip")
        with zipfile.ZipFile(path, "w") as output:
            for relative, content in entries.items():
                output.writestr("game/" + relative, content if isinstance(content, bytes) else json.dumps(content))
        return path
    pack = archive("all-six-catalogs", data)
    item["price"] = 212
    latest = archive("latest-items", {paths[1]: data[paths[1]]})
    known = {p.relative_to(ROOT / "game").as_posix() for p in (ROOT / "game/data").rglob("*.json")}
    saves = run / "saves"
    saves.mkdir()
    mod_root = saves / "character_mods"
    first = inspect_override_pack(pack, known)
    second = inspect_override_pack(latest, known)
    (project / "qa_mod_expected.json").write_text(json.dumps({"base": baseline, "overrides": dict(override, item_price=212), "previous": override}), encoding="utf-8")
    env = os.environ.copy()
    for key, folder in (("APPDATA", run / "env/appdata"), ("LOCALAPPDATA", run / "env/localappdata")):
        folder.mkdir(parents=True)
        env[key] = str(folder)
    env.update(RENPY_SIMPLE_EXCEPTIONS="1", FM_QA_OVERRIDE_SOURCE=str(latest))
    if args.variant:
        env["RENPY_VARIANT"] = args.variant
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    results = []
    def execute(phase, expected, additive=False, destination=saves):
        env.update(FM_QA_OVERRIDE_PHASE=phase, FM_QA_OVERRIDE_EXPECTED=expected, FM_QA_OVERRIDE_ADDITIVE="1" if additive else "")
        destination.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run([args.sdk, str(project), "run", "--savedir", str(destination)], env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startup, timeout=150)
        (run / (phase + "-output.txt")).write_bytes(completed.stdout)
        report_path = destination / (phase + "-report.json")
        report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {"error": "No complete report"}
        results.append({"phase": phase, "exit": completed.returncode, "report": report})
        (run / "report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(phase + ": exit " + str(completed.returncode) + " / " + str(len(report.get("checks", []))) + " checks", flush=True)
        if completed.returncode or report.get("error"):
            raise RuntimeError("Native QA failed: " + phase + " - " + str(report))
    execute("base", "base")
    install_override_pack(first, mod_root, known)
    install_override_pack(second, mod_root, known)
    additive = archive("additive", {"data/workers/qa.json": [{"name": "QA Additive Worker", "folder": "qa_additive", "gender": "female", "skills": {"Craft": 30}, "traits": ["Human"], "cost": 1, "nsfw": False}],
                                    "images/workers/qa_additive/profile.png": base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")})
    install_pack(inspect_pack(additive), mod_root)
    execute("overrides", "overrides", True)
    execute("load", "overrides", True)
    schedule_uninstall(mod_root, second["id"])
    execute("remove-latest", "previous", True)
    schedule_uninstall(mod_root, first["id"])
    execute("remove-all", "base", True)
    execute("ui", "base", destination=run / "ui-saves")
    assert before == {p: hashlib.sha256((ROOT / "game" / p).read_bytes()).hexdigest() for p in paths}
    print("All native phases passed; original catalogs unchanged.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
