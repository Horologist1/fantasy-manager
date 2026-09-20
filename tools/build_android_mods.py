"""Build the current game with the SAF bridge, entirely inside a disposable directory.

The default APK has a separate package and a debug signing key. It cannot replace
the user's existing Fantasy Manager app. Original SDK/game/signing keys are untouched.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def patch_bridge(rapt):
    java = rapt / "prototype/renpyandroid/src/main/java/org/fantasymanager/mods/ModImportActivity.java"
    java.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "tools/android/ModImportActivity.java", java)
    manifest = rapt / "templates/app-AndroidManifest.xml"
    text = manifest.read_text(encoding="utf-8")
    assert text.count("  </application>") == 1
    manifest.write_text(text.replace("  </application>", '''    <activity android:name="org.fantasymanager.mods.ModImportActivity"
        android:exported="false"
        android:theme="@android:style/Theme.Translucent.NoTitleBar"
        android:configChanges="orientation|screenSize|keyboardHidden" />
  </application>'''), encoding="utf-8")


def prepare(sdk, android_sdk, gradle_cache, jdk, release=False):
    run = ROOT / "backups" / ("android-build-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    run.mkdir(parents=True)
    print("Build directory: " + str(run), flush=True)
    isolated = run / "sdk"
    project = run / "game-project"
    isolated.mkdir()
    # The SDK's standard library is distributed as .pyc files; preserve it.
    ignore = shutil.ignore_patterns("__pycache__", "saves", "cache", "log.txt", "traceback.txt")
    for name in ("renpy.exe", "renpy.py", "LICENSE.txt"):
        shutil.copy2(sdk / name, isolated / name)
    for name in ("renpy", "lib", "launcher", "sdk-fonts"):
        shutil.copytree(sdk / name, isolated / name, ignore=ignore)
    rapt = isolated / "rapt"
    rapt.mkdir()
    for name in ("prototype", "templates", "buildlib"):
        shutil.copytree(sdk / "rapt" / name, rapt / name, ignore=ignore)
    for name in ("hash.txt", "blocklist.txt", "keeplist.txt", "bundletool.jar"):
        if (sdk / "rapt" / name).is_file():
            shutil.copy2(sdk / "rapt" / name, rapt / name)
    (rapt / "sdk.txt").write_text(str(android_sdk), encoding="utf-8")
    (rapt / "bin").mkdir()
    patch_bridge(rapt)
    # QA signing belongs solely to this disposable project; no release key is read.
    template = rapt / "templates/app-build.gradle"
    if not release:
        text = template.read_text(encoding="utf-8")
        first = text.index("    signingConfigs {")
        last = text.index("    buildTypes {", first)
        text = text[:first] + text[last:]
        text = text.replace("signingConfig signingConfigs.release", "signingConfig signingConfigs.debug\n            debuggable true")
        template.write_text(text, encoding="utf-8")
    else:
        key = ROOT / "android.keystore"
        if not key.is_file():
            raise RuntimeError("Release builds require the existing android.keystore. No replacement key will be generated.")
        # Ren'Py's standard signing configuration; read the original key in place.
        (rapt / "prototype/local.properties").write_text(
            "key.store=" + key.as_posix() + "\nkey.alias=android\nkey.store.password=android\nkey.alias.password=android\n", encoding="utf-8")
    # Use cached build dependencies; do not auto-download or update an installed SDK.
    build = rapt / "buildlib/rapt/build.py"
    text = build.read_text(encoding="utf-8")
    needle = '[ plat.gradlew, "-p", plat.path("project"), command ]'
    assert text.count(needle) == 1
    text = text.replace(needle, '[ plat.gradlew, "--offline", "--no-daemon", "--max-workers=2", "-p", plat.path("project"), command ]')
    build.write_text(text, encoding="utf-8")
    shutil.copytree(ROOT / "game", project / "game", ignore=shutil.ignore_patterns(
        "saves", "cache", "__pycache__", "*.pyc", "*.rpyc", "*.rpyb", "*.rpymc", "qa_*.rpy"))
    public = json.loads((ROOT / "android.json").read_text(encoding="utf-8-sig"))
    config = {k: public[k] for k in ("version", "orientation", "permissions", "source", "store", "heap_size") if k in public}
    config.update(package="fantasy.manager.modqa", name="Fantasy Manager Mod QA", icon_name="FM Mod QA",
                  numeric_version=1, update_always=True, update_keystores=False)
    if release:
        config.update({k: public[k] for k in ("package", "name", "icon_name")})
    (project / "android.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    for icon in ROOT.glob("android-icon*.png"):
        shutil.copy2(icon, project / icon.name)
    env = os.environ.copy()
    for key, folder in (("APPDATA", run / "profile/appdata"), ("LOCALAPPDATA", run / "profile/localappdata"),
                        ("ANDROID_USER_HOME", run / "profile/android"), ("GRADLE_USER_HOME", run / "gradle"),
                        ("TEMP", run / "temp"), ("TMP", run / "temp")):
        folder.mkdir(parents=True, exist_ok=True)
        env[key] = str(folder)
    env.update(JAVA_HOME=str(jdk), ANDROID_HOME=str(android_sdk), ANDROID_SDK_ROOT=str(android_sdk), RENPY_SIMPLE_EXCEPTIONS="1")
    for name in ("caches", "wrapper"):
        shutil.copytree(gradle_cache / name, run / "gradle" / name,
                        ignore=shutil.ignore_patterns("*.lock", "*.lck", "*.part"))
    # Gradle's debug key also stays within this build, regardless of host user profile.
    env["JAVA_TOOL_OPTIONS"] = "-Duser.home=" + str(run / "profile")
    hashes = {p.relative_to(ROOT / "game").as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT / "game").rglob("*") if p.is_file() and p.suffix in (".rpy", ".py", ".json")
              and not any(x in p.parts for x in ("saves", "cache", "__pycache__"))}
    (run / "source-manifest.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    (run / "build-info.json").write_text(json.dumps({"package": config["package"], "release": release}, indent=2), encoding="utf-8")
    (run / "build-env.json").write_text(json.dumps({k: env[k] for k in (
        "APPDATA", "LOCALAPPDATA", "ANDROID_USER_HOME", "GRADLE_USER_HOME", "TEMP", "TMP",
        "JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT", "RENPY_SIMPLE_EXCEPTIONS", "JAVA_TOOL_OPTIONS")}, indent=2), encoding="utf-8")
    return run, env


def verify_and_copy(run, env):
    expected = json.loads((run / "build-info.json").read_text())["package"]
    apk = run / "sdk/rapt/project/app/build/outputs/apk/release/app-release.apk"
    aapt = sorted((Path(env["ANDROID_HOME"]) / "build-tools").glob("*/aapt.exe"))[-1]
    badging = subprocess.check_output([str(aapt), "dump", "badging", str(apk)], text=True, encoding="utf-8")
    actual = re.search(r"^package: name='([^']+)'", badging)
    if not actual or actual.group(1) != expected:
        raise RuntimeError("APK applicationId did not match the requested package. Do not install it.")
    out = run / "apk"
    out.mkdir(exist_ok=True)
    target = out / ("FantasyManager-current-" + ("ModQA" if expected.endswith(".modqa") else "Android") + ".apk")
    shutil.copy2(apk, target)
    (out / "verification.json").write_text(json.dumps({"applicationId": expected,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size}, indent=2), encoding="utf-8")
    print("Verified APK: " + str(target), flush=True)


def build(run, env, gradle_only=False):
    sdk = run / "sdk"
    command = [str(sdk / "renpy.exe"), str(sdk / "launcher"), "android_build", str(run / "game-project"),
               "--destination", str(run / "apk")]
    if gradle_only:
        command = [str(sdk / "rapt/project/gradlew.bat"), "--offline", "--no-daemon", "--max-workers=2",
                   "-p", str(sdk / "rapt/project"), "assembleRelease"]
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
    print("Compiling current game and Android bridge...", flush=True)
    with (run / ("gradle-output.txt" if gradle_only else "build-output.txt")).open("wb") as output:
        result = subprocess.run(command, env=env, stdout=output, stderr=subprocess.STDOUT,
                                startupinfo=startup, timeout=1800)
    print("Build exit: " + str(result.returncode), flush=True)
    if result.returncode == 0:
        verify_and_copy(run, env)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=Path("D:/renpy-8.3.4-sdk"))
    parser.add_argument("--android-sdk", type=Path, default=Path("C:/Android"))
    parser.add_argument("--gradle-cache", type=Path, default=Path.home() / ".gradle")
    parser.add_argument("--jdk", type=Path, default=Path("C:/Program Files/Eclipse Adoptium/jdk-21.0.11.10-hotspot"))
    parser.add_argument("--resume", type=Path, help="Retry only a previously prepared disposable build")
    parser.add_argument("--gradle-only", action="store_true", help="With --resume, retry compilation after assets have been prepared")
    parser.add_argument("--release", action="store_true", help="Build the normal package with the existing signing key; never installs it")
    args = parser.parse_args()
    if args.gradle_only and not args.resume:
        parser.error("--gradle-only requires --resume")
    if args.resume:
        run = args.resume.resolve()
        if not run.is_relative_to((ROOT / "backups").resolve()) or not (run / "source-manifest.json").is_file():
            parser.error("Resume must name an existing build under this project's backups directory.")
        env = dict(os.environ, **json.loads((run / "build-env.json").read_text(encoding="utf-8")))
    else:
        run, env = prepare(args.sdk, args.android_sdk, args.gradle_cache, args.jdk, args.release)
    return build(run, env, args.gradle_only)


if __name__ == "__main__":
    raise SystemExit(main())
