"""Send a scoped verification expression to an already-open Ren'Py QA console."""
import argparse
import base64
from pathlib import Path
import shlex
import subprocess

ADB = "C:/Android/platform-tools/adb.exe"
PACKAGE = "fantasy.manager.modqa"


def console(code):
    # Both quoting layers are explicit: Android's shell and the console's Python.
    encoded = base64.b64encode(code.encode()).decode()
    expression = "exec(__import__('base64').b64decode('" + encoded + "'))"
    subprocess.run([ADB, "shell", "input text " + shlex.quote(expression)], check=True)
    subprocess.run([ADB, "shell", "input", "keyevent", "66"], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expression_file", type=Path)
    args = parser.parse_args()
    focused = subprocess.check_output([ADB, "shell", "dumpsys", "window"], text=True, errors="replace")
    if not any(PACKAGE in line for line in focused.splitlines() if "mCurrentFocus=" in line):
        raise SystemExit("FM Mod QA must be the foreground app with its console open.")
    console(args.expression_file.read_text(encoding="utf-8"))
