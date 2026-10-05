"""Genera una partida avanzada como fixture para el autojugador.

Aislamiento (revisado el 2026-09-28 antes de tocar nada):
  - La copia desechable NUNCA incluye `game/saves`: ahi viven las partidas reales
    del usuario y estan en .gitignore, asi que no se recuperan. El filtro de
    copytree las excluye; no hay ningun borrado en este script.
  - El proyecto desechable vive en el directorio temporal, NUNCA en `backups/`:
    persistirlo ahi es lo que dejo 5 arneses del repo apuntando a rutas muertas.
  - Un savedir por copia de proyecto. Cambiar de savedir a mitad de corrida hace
    que el save nativo de `game/saves` no case con su sidecar (es lo que rompio
    la fase `ui` de qa_json_overrides).

Uso:
    python tools/autoplay.py [--seconds 120] [--seed 1] [--variant "touch small mobile android"]
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get("FM_RENPY_SDK", os.environ.get("RENPY_EXE", "D:/renpy-8.3.4-sdk/renpy.exe")))
PROBE = ROOT / "tools/make_fixture_save.rpy"

MEDIA = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".ogg", ".mp3"}


def limpiar_antiguas(prefijo, conservar=2):
    """Borra corridas viejas. Cada sesion copia el proyecto entero (~95 MB): sin
    esto, 44 sesiones dejaron 4,1 GB tirados en %TEMP%."""
    raiz = Path(tempfile.gettempdir())
    try:
        carpetas = sorted((p for p in raiz.glob(prefijo + "-*") if p.is_dir()),
                          key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return 0
    borradas = 0
    for vieja in carpetas[conservar:]:
        try:
            shutil.rmtree(vieja, ignore_errors=True)
            borradas += 1
        except OSError:
            pass
    return borradas


def make_project(destination):
    def ignore(directory, names):
        # "saves" excluido a proposito: ver cabecera.
        return [name for name in names if name in {"saves", "cache", "__pycache__"}
                or Path(name).suffix in {".rpyc", ".rpyb", ".pyc"}
                or name.startswith("qa_") or name in ("autoplay.rpy", "make_fixture_save.rpy")]

    def copy_file(source, target):
        if Path(source).suffix.lower() in MEDIA:
            try:
                os.link(source, target)
                return target
            except OSError:
                pass
        return shutil.copy2(source, target)

    shutil.copytree(ROOT / "game", destination / "game", ignore=ignore, copy_function=copy_file)
    assert not (destination / "game/saves").exists(), "la copia no debe traer saves"
    shutil.copy2(PROBE, destination / "game/make_fixture_save.rpy")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=120, help="presupuesto de la sesion")
    parser.add_argument("--seed", default="1")
    parser.add_argument("--variant", default="")
    parser.add_argument("--from-save", default="", help="carpeta con una partida preparada")
    args = parser.parse_args()

    if not SDK.is_file():
        sys.exit("SDK de Ren'Py no encontrado en " + str(SDK))

    # conservar=1 borraba el fixture que otra corrida estaba USANDO en ese
    # momento: la sesion se quedaba sin partida, salia por sys.exit y dejaba una
    # carpeta vacia sin informe. Un fixture pesa ~5 MB, no 950, asi que guardar
    # unos cuantos no cuesta disco; quien crea uno para una campana lo borra el.
    viejas = limpiar_antiguas("fm-fixture", conservar=6)
    if viejas:
        print("limpieza: %d fixtures antiguos borrados" % viejas, flush=True)
    base = Path(tempfile.gettempdir()) / ("fm-fixture-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    project, savedir, appdata = base / "project", base / "saves", base / "env/appdata"
    savedir.mkdir(parents=True)
    appdata.mkdir(parents=True)
    print("sesion aislada:", base, flush=True)
    make_project(project)
    if args.from_save:
        source = Path(args.from_save)
        if not source.is_dir():
            sys.exit("no existe la carpeta de partida: " + str(source))
        for item in source.iterdir():
            if item.is_file():
                shutil.copy2(item, savedir / item.name)
        print("partida preparada copiada desde:", source, flush=True)

    env = os.environ.copy()
    env.update(APPDATA=str(appdata), LOCALAPPDATA=str(base / "env/localappdata"),
               RENPY_SIMPLE_EXCEPTIONS="1", FM_AUTOPLAY_SEED=str(args.seed))
    if args.from_save:
        env["FM_AUTOPLAY_LOAD"] = "1"
    if args.variant:
        env["RENPY_VARIANT"] = args.variant
        print("variante:", args.variant, flush=True)
    startup = None
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        env["RENPY_RENDERER"] = "gl2"

    timed_out = False
    try:
        result = subprocess.run([str(SDK), str(project), "run", "--savedir", str(savedir)],
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                startupinfo=startup, timeout=args.seconds)
        code, output = result.returncode, result.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as expired:
        # Lo normal: la sesion se corta por presupuesto, no por fallo.
        timed_out = True
        code, output = None, (expired.stdout or b"").decode("utf-8", "replace")

    (base / "engine-output.txt").write_text(output, encoding="utf-8")
    print("fin de sesion (%s)" % ("presupuesto agotado" if timed_out else "exit %s" % code), flush=True)

    journal = savedir / "autoplay-journal.jsonl"
    rows = []
    if journal.exists():
        for line in journal.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass

    clicks = [r for r in rows if r.get("kind") in ("CLICK", "DISMISS")]
    goals = [r for r in rows if r.get("kind") == "GOAL"]
    findings = [r for r in rows if r.get("kind") in ("BUG", "ERROR")]
    screens = sorted({r.get("screen") for r in clicks if r.get("screen")})

    print("\nacciones: %d   objetivos del guion cumplidos: %d" % (len(clicks), len(goals)), flush=True)
    print("screens alcanzadas (%d): %s" % (len(screens), ", ".join(screens)), flush=True)
    if goals:
        print("guion: " + " -> ".join(g.get("message", "") for g in goals), flush=True)
    print("\nprimeras 25 acciones:", flush=True)
    for row in clicks[:25]:
        print("  %-10s %-24s %s" % (row.get("kind"), row.get("screen") or "-", row.get("message")), flush=True)

    if findings:
        print("\nHALLAZGOS (%d):" % len(findings), flush=True)
        for row in findings:
            print("  [%s] %s" % (row.get("kind"), row.get("message")), flush=True)
    else:
        print("\nsin hallazgos de oraculo", flush=True)

    report_path = savedir / "autoplay-report.json"
    if report_path.exists():
        try:
            coverage = json.loads(report_path.read_text(encoding="utf-8")).get("coverage") or {}
        except ValueError:
            coverage = {}
        if coverage:
            print("")
            print("cobertura: %s/%s screens objetivo (%s%%)" % (
                coverage.get("reached"), coverage.get("targets"), coverage.get("percent")), flush=True)
            missing = coverage.get("unreached") or []
            print("sin alcanzar (%d): %s" % (len(missing), ", ".join(missing[:40])), flush=True)

    shots = sorted(savedir.glob("shot-*.png"))
    print("capturas: %d" % len(shots), flush=True)
    # El proyecto copiado ya no hace falta: solo interesa la partida guardada.
    proyecto = base / "project"
    if proyecto.exists():
        shutil.rmtree(proyecto, ignore_errors=True)
    print("fixture listo en:", savedir, flush=True)
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
