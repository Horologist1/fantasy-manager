"""Run the production event UI in a disposable Ren'Py project.

    python tools/qa_choice_layout.py [--mode all|layout|clicks] [--limit 3]
    python tools/qa_choice_layout.py --variant "small touch"

No script is injected into the live game. Saves, persistent, compiled scripts and
negative controls live under the printed run directory. Art is hard-linked read
only (copied on filesystems without hard links); source and JSON are copied.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", default=os.environ.get("RENPY_SDK_EXE", "D:/renpy-8.3.4-sdk/renpy.exe"))
    parser.add_argument("--mode", choices=("all", "layout", "clicks"), default="all")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--variant", default=os.environ.get("RENPY_VARIANT", ""))
    parser.add_argument("--fault", choices=("locked-style", "wrong-return", "no-scroll"))
    args = parser.parse_args()
    renpy = Path(args.sdk)
    if not renpy.is_file():
        parser.error("Ren'Py executable not found: " + str(renpy))
    run = ROOT / "backups" / ("choice-qa-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    project = run / "project"
    (run / "saves").mkdir(parents=True)
    print("run dir: " + str(run), flush=True)

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
    shutil.copy2(ROOT / "tools" / "qa_choice_layout.rpy", project / "game" / "qa_choice_layout.rpy")
    if args.fault:
        screen = project / "game/scripts/core/screens.rpy"
        source = screen.read_text(encoding="utf-8")
        if args.fault == "locked-style":
            source = source.replace('style "event_choice_locked_vbox"', 'style "choice_vbox"')
        elif args.fault == "wrong-return":
            source = source.replace('action Return(choice)', 'action Return({"qa_wrong_choice": True})')
        else:
            source = source.replace('ymaximum (config.screen_height - 80)', 'ymaximum 10000')
        screen.write_text(source, encoding="utf-8")
    env = os.environ.copy()
    for key, path in (("APPDATA", run / "env/appdata"), ("LOCALAPPDATA", run / "env/localappdata")):
        path.mkdir(parents=True)
        env[key] = str(path)
    env.update(RENPY_SIMPLE_EXCEPTIONS="1", FM_QA_CHOICE_LAYOUT="1", FM_QA_CHOICE_MODE=args.mode,
               FM_QA_CHOICE_LIMIT=str(args.limit), FM_QA_CHOICE_FAULT=args.fault or "")
    if args.variant:
        env["RENPY_VARIANT"] = args.variant
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run([str(renpy), str(project), "run", "--savedir", str(run / "saves")],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            startupinfo=startup, timeout=1800)
    output = result.stdout.decode("utf-8", "replace")
    (run / "engine-output.txt").write_text(output, encoding="utf-8")
    report_path = run / "saves/report.json"
    if not report_path.exists():
        print(output[-4000:])
        raise SystemExit("No complete report produced (exit %d); inspect the isolated project traceback." % result.returncode)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    print("cases: %d  failures: %d  engine exit: %d" % (report["cases"], report["failures"], result.returncode))
    for row in report["results"]:
        if row["problems"]:
            print("FAIL %s %s: %s" % (row["event"], row["variant"], row["problems"]))
    if args.fault:
        print("Negative control: failures are expected; a green run invalidates the gate.")
    return 1 if report["failures"] or result.returncode else 0


if __name__ == "__main__":
    sys.exit(main())
