"""Nivel A del plan de playtest: contenido nuevo jugado en el motor real.

Mismo aislamiento que el nivel B: copia desechable del proyecto (game/saves es
una segunda ubicacion de guardado y persistent se mezcla newest-wins, asi que
correr sobre el repo filtraria flags de QA a la partida real).

Uso:  python tools/qa_playtest_content.py
"""
from datetime import datetime
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get("FM_RENPY_SDK", os.environ.get("RENPY_EXE", "D:/renpy-8.3.4-sdk/renpy.exe")))
PROBE = ROOT / "tools/qa_playtest_content.rpy"


def make_project(destination):
    def ignore(directory, names):
        return [name for name in names if name in {"saves", "cache", "__pycache__"}
                or Path(name).suffix in {".rpyc", ".rpyb", ".pyc"}
                or name.startswith("qa_")]

    def copy_file(source, target):
        if Path(source).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".ogg", ".mp3"}:
            try:
                os.link(source, target)
                return target
            except OSError:
                pass
        return shutil.copy2(source, target)

    shutil.copytree(ROOT / "game", destination / "game", ignore=ignore, copy_function=copy_file)
    shutil.copy2(PROBE, destination / "game/qa_playtest_content.rpy")


def main():
    if not SDK.is_file():
        sys.exit("SDK de Ren'Py no encontrado en " + str(SDK))

    base = Path(tempfile.gettempdir()) / ("fm-content-qa-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    project, savedir, appdata = base / "project", base / "saves", base / "env/appdata"
    savedir.mkdir(parents=True)
    appdata.mkdir(parents=True)
    print("QA aislada:", base, flush=True)
    make_project(project)

    env = os.environ.copy()
    env.update(APPDATA=str(appdata), LOCALAPPDATA=str(base / "env/localappdata"),
               RENPY_SIMPLE_EXCEPTIONS="1")
    variant = os.environ.get("FM_QA_VARIANT", "").strip()
    if variant:
        # Caso 26: la UI tactil no renderiza en escritorio, asi que la unica
        # prueba real es correr con la variante puesta y mirar las capturas.
        env["RENPY_VARIANT"] = variant
        print("variante de pantalla:", variant, flush=True)
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        env["RENPY_RENDERER"] = "gl2"

    failed = False
    try:
        result = subprocess.run([str(SDK), str(project), "run", "--savedir", str(savedir)],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                startupinfo=startup, timeout=900)
        output = result.stdout.decode("utf-8", "replace")
        code = result.returncode
    except subprocess.TimeoutExpired as expired:
        output = (expired.stdout or b"").decode("utf-8", "replace")
        code = None
        print("TIMEOUT tras 900s (no es un FAIL por si mismo: mira el log)", flush=True)

    (base / "engine-output.txt").write_text(output, encoding="utf-8")
    print("salida del motor:", code, flush=True)
    if code != 0:
        failed = True

    log = savedir / "content-qa.txt"
    if log.exists():
        text = log.read_text(encoding="utf-8")
        print("\n" + text, flush=True)
        fails = [l for l in text.splitlines() if l.startswith("FAIL")]
        passes = [l for l in text.splitlines() if l.startswith("PASS")]
        print("resumen: %d PASS, %d FAIL" % (len(passes), len(fails)), flush=True)
        if fails:
            failed = True
    else:
        print("no se escribio log de checks", flush=True)
        print("\n".join(output.strip().splitlines()[-40:]), flush=True)
        failed = True

    shots = sorted(savedir.glob("shot-*.png"))
    if shots:
        print("capturas:", [s.name for s in shots], flush=True)
    print("artefactos en:", base, flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
