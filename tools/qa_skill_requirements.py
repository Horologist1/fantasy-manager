"""Play events with skill_requirements in a disposable Ren'Py project.

    python tools/qa_skill_requirements.py [--fault]

Real handle_random_event flow, real screens, SDK test-mouse clicks. Saves,
persistent and screenshots go under the printed run directory.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = os.environ.get("RENPY_SDK_EXE", "D:/renpy-8.3.4-sdk/renpy.exe")


def copy_asset(source, target):
    if Path(source).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".ttf", ".ogg", ".mp3", ".wav", ".mp4", ".webm"}:
        try:
            os.link(source, target)
            return target
        except OSError:
            pass
    return shutil.copy2(source, target)


def main():
    run = ROOT / "backups" / ("skillreq-qa-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    project = run / "project"
    (run / "saves").mkdir(parents=True)
    print("run dir: " + str(run), flush=True)
    shutil.copytree(ROOT / "game", project / "game", copy_function=copy_asset,
                    ignore=shutil.ignore_patterns("saves", "cache", "__pycache__", "*.rpyc", "*.rpyb", "*.rpymc", "*.pyc", "qa_*.rpy"))
    shutil.copy2(ROOT / "tools" / "qa_skill_requirements.rpy", project / "game" / "qa_skill_requirements.rpy")
    if "--fault" in sys.argv:
        # Negative control: drop the requirement filter from the worker pickers.
        events = project / "game/scripts/events/events.rpy"
        source = events.read_text(encoding="utf-8")
        line = "temp_eligible = [w for w in temp_eligible if worker_meets_choice_skill_requirements(w, chosen_choice_data)]"
        assert source.count(line) == 2
        events.write_text(source.replace(line, "pass"), encoding="utf-8")
        print("NEGATIVE CONTROL: failures are expected", flush=True)
    env = os.environ.copy()
    for key, path in (("APPDATA", run / "env/appdata"), ("LOCALAPPDATA", run / "env/localappdata")):
        path.mkdir(parents=True)
        env[key] = str(path)
    env.update(RENPY_SIMPLE_EXCEPTIONS="1", FM_QA_SKILL_REQ="1")
    if os.environ.get("RENPY_VARIANT"):
        env["RENPY_VARIANT"] = os.environ["RENPY_VARIANT"]
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run([SDK, str(project), "run", "--savedir", str(run / "saves")], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startup, timeout=900)
    output = result.stdout.decode("utf-8", "replace")
    (run / "engine-output.txt").write_text(output, encoding="utf-8")
    report_path = run / "saves/report.json"
    if not report_path.exists():
        print(output[-4000:])
        raise SystemExit("No report (exit %d); see %s" % (result.returncode, run))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for row in report["results"]:
        print(("FAIL " if row["problems"] else "ok   ") + row["case"], json.dumps({k: row[k] for k in ("options", "eligible", "money_delta", "problems")}, ensure_ascii=False))
    print("cases: %d  failures: %d  engine exit: %d" % (report["cases"], report["failures"], result.returncode))
    return 1 if report["failures"] or result.returncode else 0


if __name__ == "__main__":
    sys.exit(main())
