"""Native assignment selectors: empty states, legacy aliases and 800 workers."""
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

from test_general_save_runtime import make_project, SDK

ROOT = Path(__file__).resolve().parents[1]
HARNESS = '''
init python:
    def qa_assign_setup():
        qa_intro_setup()
        persistent.intro_popups_enabled = False
        template = copy.deepcopy(store.workers[0])
        store.workers = []
        for index in range(800):
            worker = copy.deepcopy(template)
            worker["name"] = "Worker %d" % index
            store.workers.append(worker)
        store.available_buildings = {"Building 1": {"type": "restaurant", "owned": True,
            "display_name": "Business [literal] {literal}", "base_level": 1, "reputation": 0,
            "assigned_servants": [], "servant_jobs": {}}}
        store.owned_buildings = ["Building_1"]
        store.building_types_json = copy.deepcopy(store.building_types_json)
        btype = next(b for b in store.building_types_json["building_types"] if b["id"] == "restaurant")
        prof = next(p for p in btype["professions"] if p["id"] == "service")
        prof.update(name="Server [literal] {literal}", description="Serve [literal] {literal} meals.",
                    original_max_daily_workers=1, max_daily_workers=1)
        btype["professions"] = [prof]

    def qa_assign_text():
        texts = []
        for node in qa_intro_walk(renpy.get_screen("job_selection").child):
            if isinstance(node, renpy.text.text.Text):
                texts.extend(str(part) for part in node.text if isinstance(part, str))
        return "\\n".join(texts)

    def qa_assign_check_text(expected, absent=None):
        text = qa_assign_text()
        qa_intro_check(expected in text, "Assignment message: " + expected)
        if absent:
            qa_intro_check(absent not in text, "No contradictory message: " + absent)

    def qa_assign_prof():
        return next(b for b in store.building_types_json["building_types"] if b["id"] == "restaurant")["professions"][0]

label splashscreen:
    $ qa_assign_setup()
    show screen job_selection(workers[-1])
    call screen qa_intro_gate
    $ qa_assign_check_text("Select a building first", "No building assigned or building type not set")
    $ qa_intro_check(renpy.get_widget("job_selection", "job_building_Building 1") is not None, "Owned legacy alias resolves to clickable building")
    $ qa_intro_capture("assign_unassigned")
    $ qa_intro_widget("job_selection", "job_building_Building 1")
    call screen qa_intro_gate
    $ qa_intro_check(workers[-1]["assigned_building"] == "Building 1", "Building click changes canonical worker in roster of 800")
    $ qa_intro_check("{{color=" not in renpy.get_screen("job_selection").scope["_prof_blurb"], "Built-in mechanics keep their formatted color tags")
    $ qa_intro_check("[[literal]" not in renpy.get_screen("job_selection").scope["_prof_blurb"], "Description brackets are not double-escaped")
    $ qa_intro_capture("assign_roles")
    $ qa_intro_widget("job_selection", "job_role_service")
    call screen qa_intro_gate
    $ qa_intro_check(available_buildings["Building 1"]["servant_jobs"].get(workers[-1]["name"]) == "service", "Actual role click sets service job")
    $ workers[-1]["assigned_building"] = "Building_1"
    show screen job_selection(workers[-1])
    call screen qa_intro_gate
    $ qa_intro_check(renpy.get_widget("job_selection", "job_role_service") is not None, "Legacy assigned alias still exposes current role")
    hide screen job_selection
    $ workers[0]["assigned_building"] = "Building 1"
    show screen job_selection(workers[0])
    call screen qa_intro_gate
    $ qa_assign_check_text("Role Full")
    $ qa_intro_check(not renpy.get_screen("job_selection").scope["_can_assign_profession"], "Legacy alias occupant is counted toward role capacity")
    hide screen job_selection
    $ available_buildings["Building 1"]["type"] = None
    show screen job_selection(workers[-1])
    call screen qa_intro_gate
    $ qa_assign_check_text("has no business type yet", "Select a building first")
    $ qa_intro_capture("assign_no_type")
    hide screen job_selection
    $ available_buildings["Building 1"]["type"] = "missing_mod_type"
    show screen job_selection(workers[-1])
    call screen qa_intro_gate
    $ qa_assign_check_text("type is unavailable")
    hide screen job_selection
    $ available_buildings["Building 1"]["type"] = "restaurant"
    $ qa_assign_prof()["required_flag"] = "qa_locked_role"
    show screen job_selection(workers[-1])
    call screen qa_intro_gate
    $ qa_assign_check_text("No roles are available")
    hide screen job_selection
    $ qa_assign_prof().pop("required_flag")
    $ workers[-1]["assigned_building"] = "Missing Building"
    show screen job_selection(workers[-1])
    call screen qa_intro_gate
    $ qa_assign_check_text("Select a building first", "No building assigned or building type not set")
    $ qa_intro_check(workers[-1]["assigned_building"] == "Missing Building", "Rendering a stale assignment never rewrites it")
    hide screen job_selection
    $ owned_buildings = []
    show screen job_selection(workers[-1])
    call screen qa_intro_gate
    $ qa_assign_check_text("No owned business is available")
    hide screen job_selection
    $ owned_buildings = ["Building 1"]
    $ workers[-1]["assigned_building"] = "Building 1"
    $ workers[0]["assigned_building"] = "Unassigned"
    show screen building_selection(workers[-1], return_to_workers=False)
    call screen qa_intro_gate
    $ qa_intro_capture("building_selector_literal_name")
    hide screen building_selection
    show screen Manager("Building 1")
    call screen qa_intro_gate
    $ qa_intro_capture("manager_literal_names")
    hide screen Manager
    python:
        persistent.default_auto_supply_potions = False
        persistent.default_auto_rest = False
        persistent.default_auto_equip = True
        for _qa_w in workers:
            _qa_w["auto_supply_potions"] = True
            _qa_w["auto_supply_potion_count"] = 5
            _qa_w["auto_rest"] = True
            _qa_w["auto_rest_entry_pct"] = 45
        toggle_persistent_default_auto_equip()
    $ qa_intro_check(all(w["auto_rest"] and w["auto_supply_potions"] and not w["auto_equip"] for w in workers), "Global equip toggle preserves independent rest and supply for 800 workers")
    python:
        # Auto-rest rules: a worker rested from Unassigned never gets a job
        # invented for them, a manual Rest (auto_rest off) also waits for
        # health, and a recovered worker waits while the reserved job is full.
        _qa_rested = workers[5]
        _qa_rested["assigned_building"] = "Building 1"
        _qa_rested["auto_rest"] = False
        _qa_rested["energy"] = calculate_max_energy(_qa_rested)
        _qa_rested["health"] = calculate_max_health(_qa_rested)
        _qa_rested.pop("previous_profession", None)
        _qa_rested.pop("previous_job", None)
        available_buildings["Building 1"]["servant_jobs"][_qa_rested["name"]] = "rest"
        process_manager_auto_rest(restore_only=True)
        qa_intro_check(available_buildings["Building 1"]["servant_jobs"].get(_qa_rested["name"]) == "unassigned", "Rest without a reserved job returns to Unassigned, never to an invented job")
        _qa_hurt = workers[6]
        _qa_hurt["assigned_building"] = "Building 1"
        _qa_hurt["auto_rest"] = False
        _qa_hurt["energy"] = calculate_max_energy(_qa_hurt)
        _qa_hurt["health"] = 1
        _qa_hurt["previous_profession"] = "service"
        available_buildings["Building 1"]["servant_jobs"][_qa_hurt["name"]] = "rest"
        process_manager_auto_rest(restore_only=True)
        qa_intro_check(available_buildings["Building 1"]["servant_jobs"].get(_qa_hurt["name"]) == "rest", "Manual Rest keeps healing while health is low")
        _qa_hurt["health"] = calculate_max_health(_qa_hurt)
        process_manager_auto_rest(restore_only=True)
        qa_intro_check(available_buildings["Building 1"]["servant_jobs"].get(_qa_hurt["name"]) == "rest", "Recovered worker keeps waiting while the reserved job is full")
        available_buildings["Building 1"]["servant_jobs"].pop(_qa_rested["name"], None)
        available_buildings["Building 1"]["servant_jobs"].pop(_qa_hurt["name"], None)
        _qa_rested["assigned_building"] = "Unassigned"
        _qa_hurt["assigned_building"] = "Unassigned"
        _qa_hurt.pop("previous_profession", None)
        _qa_rested["auto_rest"] = True
        _qa_hurt["auto_rest"] = True
    $ qa_intro_save(94)
    $ qa_intro_save(94)
    $ CanonicalSnapshotFileLoad(FileLoad(94, confirm=False), 94, confirm=False)()
    return

label qa_general_loaded:
    $ qa_intro_check(len(workers) == 800, "All 800 workers survive canonical load")
    $ qa_intro_check(all(w["auto_rest"] and w["auto_supply_potions"] and not w["auto_equip"] and w["auto_rest_entry_pct"] == 45 and w["auto_supply_potion_count"] == 5 for w in workers), "Independent automation policies survive canonical load")
    $ qa_intro_check(available_buildings["Building 1"]["servant_jobs"].get(workers[-1]["name"]) == "service", "Assigned role survives canonical load")
    $ qa_intro_save(95)
    $ renpy.quit(status=0)
'''


def test_assignment_selectors_and_saves_with_800_workers(tmp_path):
    if not SDK.is_file():
        if os.environ.get("RENPY_RUNTIME_REQUIRED") == "1":
            pytest.fail("Ren'Py SDK required but unavailable")
        pytest.skip("requires Ren'Py SDK")
    project = tmp_path / "project"
    make_project(project)
    # Optional preserved source is only used to reproduce the bug in a copy.
    baseline = os.environ.get("FM_ASSIGNMENT_BASELINE_ZIP")
    if baseline:
        with zipfile.ZipFile(baseline) as archive:
            (project / "game/scripts/core/screens.rpy").write_bytes(archive.read("game/scripts/core/screens.rpy"))
    helpers = (ROOT / "tools/qa_location_tutorials.rpy").read_text(encoding="utf-8").split("\nlabel splashscreen:", 1)[0]
    (project / "game/qa_general_audit.rpy").write_text(helpers + HARNESS, encoding="utf-8")
    env = os.environ.copy()
    env.update(APPDATA=str(tmp_path / "env/appdata"), LOCALAPPDATA=str(tmp_path / "env/localappdata"),
               RENPY_SIMPLE_EXCEPTIONS="1", RENPY_RENDERER="gl2")
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run([str(SDK), str(project), "run", "--savedir", str(tmp_path / "saves")],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startup, timeout=90)
    output = result.stdout.decode("utf-8", "replace")
    (tmp_path / "engine-output.txt").write_text(output, encoding="utf-8")
    assert result.returncode == 0, output[-6000:]
    report = (tmp_path / "saves/location-qa.txt").read_text(encoding="utf-8")
    assert "FAIL:" not in report and "All 800 workers survive canonical load" in report
    assert "Native save committed: 95" in report
