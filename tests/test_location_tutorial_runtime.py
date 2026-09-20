"""First-visit UI, real brewing labels, and native saves in an isolated game."""
import os
from pathlib import Path
import subprocess

import pytest

from test_general_save_runtime import make_project, SDK

ROOT = Path(__file__).resolve().parents[1]


def test_location_tutorials_brewing_and_save_load(tmp_path, literal_mod_names=False):
    if not SDK.is_file():
        if os.environ.get("RENPY_RUNTIME_REQUIRED") == "1":
            pytest.fail("Ren'Py SDK required but unavailable")
        pytest.skip("requires Ren'Py SDK")
    project = tmp_path / "project"
    make_project(project)
    harness = (ROOT / "tools/qa_location_tutorials.rpy").read_text(encoding="utf-8")
    if literal_mod_names:
        harness = harness.replace("QA Brewer", "QA [not_a_variable] {not_a_tag}")
        anchor = '        store.manager_inventory = [["health_potion", 7, False]]\n'
        assert harness.count(anchor) == 1
        harness = harness.replace(anchor, anchor + '''        store.items_json = copy.deepcopy(store.items_json)
        for item in store.items_json["items"]:
            if item.get("id", "").startswith(("alchemy_", "potion_")):
                item["name"] += " [not_a_variable] {not_a_tag}"
''')
    (project / "game/qa_general_audit.rpy").write_text(harness, encoding="utf-8")
    flow = project / "game/scripts/main_flow.rpy"
    source = flow.read_text(encoding="utf-8")
    anchor = "label tavern_screen():\n"
    assert source.count(anchor) == 1
    flow.write_text(source.replace(anchor, anchor + '    if renpy.session.get("qa_intro_return"):\n        jump expression renpy.session["qa_intro_return"]\n', 1), encoding="utf-8")
    env = os.environ.copy()
    env.update(APPDATA=str(tmp_path / "env/appdata"), LOCALAPPDATA=str(tmp_path / "env/localappdata"),
               RENPY_SIMPLE_EXCEPTIONS="1", RENPY_RENDERER="gl2")
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run([str(SDK), str(project), "run", "--savedir", str(tmp_path / "saves")],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            startupinfo=startup, timeout=90)
    output = result.stdout.decode("utf-8", "replace")
    (tmp_path / "engine-output.txt").write_text(output, encoding="utf-8")
    assert result.returncode == 0, output[-6000:]
    report = (tmp_path / "saves/location-qa.txt").read_text(encoding="utf-8")
    assert "FAIL:" not in report
    assert "Native save committed: 95" in report
    for key in ("academy_menu", "arena_menu", "alchemy_laboratory", "church_visit"):
        assert report.count("Production first-visit popup: " + key) == 1
        assert (tmp_path / "saves" / (key + ".png")).is_file()


def test_modded_alchemy_names_are_literal_and_saves_still_work(tmp_path):
    test_location_tutorials_brewing_and_save_load(tmp_path, literal_mod_names=True)
