"""Nivel B del plan de playtest: matriz de save/load en el motor real.

Corre sobre una COPIA DESECHABLE del proyecto, no sobre el repo. `--savedir` no
aisla por si solo: game/saves sigue siendo una segunda ubicacion de guardado y
persistent se mezcla campo a campo (newest-wins), asi que un flip de flag de QA
se filtra a la partida real. Patron tomado de tests/test_general_save_runtime.py.

Dos invocaciones del motor comparten un mismo savedir:
  fase 1 -> siembra, guarda, deforma snapshots y carga in-process
  fase 2 -> proceso NUEVO que carga lo que dejo la fase 1 (el ciclo del jugador
            que cierra el juego y vuelve mas tarde)

Uso:  python tools/qa_playtest_save.py
"""
from datetime import datetime
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get("FM_RENPY_SDK", os.environ.get("RENPY_EXE", "D:/renpy-8.3.4-sdk/renpy.exe")))
PROBE = ROOT / "tools/qa_playtest_save.rpy"
ANCHOR = "    # FM-SAVE-ANCHOR: after-load-end\n    jump tavern_screen\n"
REDIRECT = "    # FM-SAVE-ANCHOR: after-load-end\n    jump qa_save_loaded\n"

# Caso 9: un override de mod con RAIZ DICT en vez de lista.
DICT_ROOT_WORKER = {
    "name": "QA DictRoot", "folder": "holly", "gender": "female", "cost": 500,
    "skills": {"Service": 30, "Combat": 10, "Craft": 10}, "traits": ["Human"],
    "unique": False, "nsfw": False, "description": "Mod con raiz dict (caso 9).",
}


def make_project(destination):
    """Copia desechable: media por hardlink, sin saves/cache/rpyc ni sondas qa_."""
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

    snapshot = destination / "game/scripts/save_snapshot.rpy"
    source = snapshot.read_text(encoding="utf-8")
    if source.count(ANCHOR) != 1:
        sys.exit("FM-SAVE-ANCHOR no encontrado (o duplicado) en save_snapshot.rpy")
    snapshot.write_text(source.replace(ANCHOR, REDIRECT), encoding="utf-8")

    shutil.copy2(PROBE, destination / "game/qa_playtest_save.rpy")
    (destination / "game/data/workers/workers_qa_dictroot.json").write_text(
        json.dumps(DICT_ROOT_WORKER, indent=2), encoding="utf-8")


def run_phase(project, savedir, appdata, phase, timeout=300):
    env = os.environ.copy()
    env.update(APPDATA=str(appdata), LOCALAPPDATA=str(appdata.parent / "localappdata"),
               RENPY_SIMPLE_EXCEPTIONS="1", FM_QA_PHASE=str(phase))
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        env["RENPY_RENDERER"] = "gl2"
    print("--- fase %s ---" % phase, flush=True)
    try:
        result = subprocess.run([str(SDK), str(project), "run", "--savedir", str(savedir)],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                startupinfo=startup, timeout=timeout)
    except subprocess.TimeoutExpired as expired:
        output = (expired.stdout or b"").decode("utf-8", "replace")
        print("TIMEOUT tras %ss (no es un FAIL por si mismo: mira el log)" % timeout, flush=True)
        return None, output
    return result.returncode, result.stdout.decode("utf-8", "replace")


def main():
    if not SDK.is_file():
        sys.exit("SDK de Ren'Py no encontrado en " + str(SDK))

    base = Path(tempfile.gettempdir()) / ("fm-save-qa-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    project, savedir, appdata = base / "project", base / "saves", base / "env/appdata"
    savedir.mkdir(parents=True)
    appdata.mkdir(parents=True)
    print("QA aislada:", base, flush=True)
    make_project(project)

    log = savedir / "save-qa.txt"
    failed = False
    for phase in (1, 2):
        code, output = run_phase(project, savedir, appdata, phase)
        (base / ("engine-output-%s.txt" % phase)).write_text(output, encoding="utf-8")
        print("salida del motor:", code, flush=True)
        if code != 0:
            failed = True
            tail = output.strip().splitlines()[-40:]
            print("\n".join(tail), flush=True)
            break

    if log.exists():
        text = log.read_text(encoding="utf-8")
        print("\n" + text, flush=True)
        fails = [line for line in text.splitlines() if line.startswith("FAIL")]
        passes = [line for line in text.splitlines() if line.startswith("PASS")]
        print("resumen: %d PASS, %d FAIL" % (len(passes), len(fails)), flush=True)
        if fails:
            failed = True
    else:
        print("no se escribio log de checks", flush=True)
        failed = True

    print("artefactos en:", base, flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
