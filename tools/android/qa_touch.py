"""Small adb toolbox for driving the QA build on a real phone.

Used to verify touch-only behaviour that a desktop run cannot show — the
Android IME in particular. Every command prints a single line of state so the
result can be read without looking at the device.

    python tools/android/qa_touch.py devices
    python tools/android/qa_touch.py install [apk]
    python tools/android/qa_touch.py launch
    python tools/android/qa_touch.py shot [name]
    python tools/android/qa_touch.py tap X Y
    python tools/android/qa_touch.py swipe X1 Y1 X2 Y2
    python tools/android/qa_touch.py ime          # is the keyboard up?
    python tools/android/qa_touch.py back
    python tools/android/qa_touch.py logcat [lines]
    python tools/android/qa_touch.py stop
"""
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ADB = "C:/Android/platform-tools/adb.exe"
PACKAGE = "fantasy.manager.modqa"
ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "backups" / "android-qa-shots"


def adb(*args, binary=False, check=True):
    result = subprocess.run([ADB, *args], capture_output=True, check=False)
    if check and result.returncode:
        raise SystemExit("adb " + " ".join(args) + " failed: "
                         + result.stderr.decode("utf-8", "replace").strip())
    return result.stdout if binary else result.stdout.decode("utf-8", "replace")


def devices():
    lines = [line for line in adb("devices").splitlines()[1:] if line.strip()]
    print("devices: " + (", ".join(lines) if lines else "none"))
    return lines


def newest_apk():
    candidates = sorted((ROOT / "backups").glob("**/apk/*ModQA*.apk"),
                        key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit("No ModQA apk found under backups/**/apk/")
    return candidates[0]


def install(apk=None):
    path = Path(apk) if apk else newest_apk()
    print("installing " + str(path) + " (" + str(round(path.stat().st_size / 1e6, 1)) + " MB)")
    print(adb("install", "-r", str(path)).strip())


def launch():
    adb("shell", "monkey", "-p", PACKAGE, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(6)
    print("focus: " + focus())


def focus():
    window = adb("shell", "dumpsys", "window")
    for line in window.splitlines():
        if "mCurrentFocus=" in line:
            return line.strip()
    return "unknown"


def shot(name=None):
    SHOTS.mkdir(parents=True, exist_ok=True)
    stamp = name or datetime.now().strftime("%H%M%S")
    target = SHOTS / (stamp + ".png")
    target.write_bytes(adb("exec-out", "screencap", "-p", binary=True))
    print("shot: " + str(target))
    return target


def tap(x, y):
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(1.2)
    print("tapped %s,%s | ime_up=%s" % (x, y, ime(quiet=True)))


def swipe(x1, y1, x2, y2):
    adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), "300")
    time.sleep(1.0)
    print("swiped")


def ime(quiet=False):
    dump = adb("shell", "dumpsys", "input_method")
    shown = re.search(r"mInputShown=(\w+)", dump)
    active = re.search(r"mServedView=([^\s]+)", dump)
    value = shown.group(1) if shown else "unknown"
    if not quiet:
        print("keyboard up: %s (%s)" % (value, active.group(1) if active else "no served view"))
    return value


def logcat(lines="120"):
    print(adb("logcat", "-d", "-t", str(lines), "-s", "python:*", "renpy:*", "AndroidRuntime:*"))


def stop():
    adb("shell", "am", "force-stop", PACKAGE)
    print("stopped " + PACKAGE)


COMMANDS = {
    "devices": devices, "install": install, "launch": launch, "focus": lambda: print(focus()),
    "shot": shot, "tap": tap, "swipe": swipe, "ime": ime, "back": lambda: adb("shell", "input", "keyevent", "4"),
    "logcat": logcat, "stop": stop,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit(__doc__)
    COMMANDS[sys.argv[1]](*sys.argv[2:])
