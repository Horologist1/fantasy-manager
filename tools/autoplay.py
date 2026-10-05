"""Autojugador: lanza el juego y lo JUEGA con input real, desde el menu principal.

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
PROBE = ROOT / "tools/autoplay.rpy"

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
    ahora = datetime.now().timestamp()
    for vieja in carpetas[conservar:]:
        # Nunca una sesion VIVA: con partidas en paralelo, la tercera mas
        # reciente puede seguir jugando (casi se borra un end game en curso).
        diario = vieja / "saves" / "autoplay-journal.jsonl"
        try:
            if diario.exists() and ahora - diario.stat().st_mtime < 20 * 60:
                continue
            # Recien creada (aun sin diario): otra corrida lanzada a la vez.
            if ahora - vieja.stat().st_mtime < 20 * 60:
                continue
        except OSError:
            continue
        try:
            shutil.rmtree(vieja, ignore_errors=True)
            borradas += 1
        except OSError:
            pass
    return borradas


def make_project(destination, goal=False):
    def ignore(directory, names):
        # "saves" excluido a proposito: ver cabecera.
        return [name for name in names if name in {"saves", "cache", "__pycache__"}
                or Path(name).suffix in {".rpyc", ".rpyb", ".pyc"}
                or name.startswith("qa_") or name.startswith("autoplay")]

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
    shutil.copy2(PROBE, destination / "game/autoplay.rpy")
    if goal:
        # El jugador con objetivo va SIN la bateria de pruebas: las pruebas
        # toman el control a mitad de tarea y le desvian de lo que persigue.
        shutil.copy2(ROOT / "tools/autoplay_goal.rpy", destination / "game/autoplay_goal.rpy")
        return
    tests = ROOT / "tools/autoplay_tests.rpy"
    if tests.is_file():
        shutil.copy2(tests, destination / "game/autoplay_tests.rpy")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=120, help="presupuesto de la sesion")
    parser.add_argument("--seed", default="1")
    parser.add_argument("--variant", default="")
    parser.add_argument("--from-save", default="", help="carpeta con una partida preparada")
    parser.add_argument("--mode", default="nsfw", choices=("sfw", "nsfw"))
    parser.add_argument("--fast-days", action="store_true",
                        help="prioriza pasar dias para acumular volumen jugado")
    parser.add_argument("--keep", action="store_true",
                        help="conserva la carpeta de la sesion aunque no haya hallazgos")
    parser.add_argument("--bad-mod", action="store_true",
                        help="deja un JSON de mod malformado para comprobar que no rompe el catalogo")
    parser.add_argument("--title", default="Lady", choices=("Lady", "Lord"))
    parser.add_argument("--i7-every", type=int, default=0,
                        help="guardar+cargar cada N acciones (por defecto 250)")
    parser.add_argument("--goal", action="store_true",
                        help="jugador con objetivo: intenta pasarse los objetivos del Journal")
    parser.add_argument("--goal-target", type=int, default=9,
                        help="objetivo que da el tramo por superado (9 = completar 1-8)")
    parser.add_argument("--endgame-days", type=int, default=0,
                        help="tras ganar, seguir N dias invirtiendo y midiendo (end game)")
    parser.add_argument("--goal-building", default="Tavern",
                        help="tipo del primer edificio para el jugador con objetivo")
    args = parser.parse_args()

    if not SDK.is_file():
        sys.exit("SDK de Ren'Py no encontrado en " + str(SDK))

    viejas = limpiar_antiguas("fm-autoplay", conservar=2)
    if viejas:
        print("limpieza: %d sesiones antiguas borradas" % viejas, flush=True)
    # Sufijo del pid: dos corridas lanzadas en el mismo segundo compartian carpeta.
    base = Path(tempfile.gettempdir()) / ("fm-autoplay-" + datetime.now().strftime("%Y%m%d-%H%M%S")
                                          + "-%d" % os.getpid())
    project, savedir, appdata = base / "project", base / "saves", base / "env/appdata"
    savedir.mkdir(parents=True)
    appdata.mkdir(parents=True)
    print("sesion aislada:", base, flush=True)
    make_project(project, goal=args.goal)
    if args.bad_mod:
        # T14.5: un override roto no puede llevarse por delante el catalogo.
        destino = project / "game/data/workers/workers_qa_roto.json"
        roto = {
            "workers": [
                {"name": 12345, "folder": None, "skills": "no-soy-un-dict",
                 "traits": {"mal": True}, "cost": "gratis"},
                "cadena suelta", None,
            ]
        }
        destino.write_text(json.dumps(roto), encoding="utf-8")
        print("mod malformado colocado en la copia desechable", flush=True)

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
               RENPY_SIMPLE_EXCEPTIONS="1", FM_AUTOPLAY_SEED=str(args.seed),
               FM_AUTOPLAY_MODE=args.mode, FM_AUTOPLAY_TITLE=args.title)
    if args.bad_mod:
        env["FM_AUTOPLAY_BADMOD"] = "1"
    if args.fast_days:
        env["FM_AUTOPLAY_FASTDAYS"] = "1"
    if args.i7_every:
        env["FM_AP_I7_EVERY"] = str(args.i7_every)
    if args.goal:
        env["FM_AUTOPLAY_GOAL"] = "1"
        env["FM_GOAL_TARGET"] = str(args.goal_target)
        env["FM_GOAL_BUILDING"] = args.goal_building
        if args.endgame_days:
            env["FM_GOAL_ENDGAME"] = "1"
            env["FM_GOAL_ENDGAME_DAYS"] = str(args.endgame_days)
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

    if report_path.exists():
        try:
            tests = json.loads(report_path.read_text(encoding="utf-8")).get("tests") or {}
        except ValueError:
            tests = {}
        if tests:
            ok = [k for k, v in tests.items() if v.get("ok") is True]
            ko = [k for k, v in tests.items() if v.get("ok") is False]
            nc = [k for k, v in tests.items() if v.get("ok") is None]
            print("")
            print("pruebas: %d PASA, %d FALLA%s" % (
                len(ok), len(ko), (", %d no concluyentes" % len(nc)) if nc else ""), flush=True)
            for name in sorted(tests):
                row = tests[name]
                print("  %-6s %-15s %s" % (name, row.get("estado", "?"),
                                           row.get("detail", "")), flush=True)

    if report_path.exists():
        try:
            ejercitado = json.loads(report_path.read_text(encoding="utf-8")).get("ejercitado") or {}
        except ValueError:
            ejercitado = {}
        if ejercitado:
            print("")
            print("volumen jugado: %d profesiones, %d eventos distintos, %d dias" % (
                len(ejercitado.get("profesiones") or []),
                len(ejercitado.get("eventos") or []),
                ejercitado.get("dias_jugados") or 0), flush=True)
            ocupadas = ejercitado.get("profesiones_ocupadas") or []
            if ocupadas:
                print("  ocupadas (con alguien asignado): %d -> %s" % (
                    len(ocupadas), ", ".join(ocupadas[:14])), flush=True)
            if ejercitado.get("profesiones"):
                print("  profesiones: " + ", ".join(ejercitado["profesiones"][:20]), flush=True)
            costes = ejercitado.get("coste_next_day") or []
            if costes:
                ordenados = sorted(costes)
                print("  avance de dia: %d medidos, mediana %.2f s, peor %.2f s" % (
                    len(costes), ordenados[len(ordenados) // 2], ordenados[-1]), flush=True)
            # Picos del avance de dia con la memoria del sistema en ese instante:
            # un pico con la RAM al limite apunta al PC; con RAM holgada, al juego.
            ctx = ejercitado.get("next_day_ctx") or []
            picos = [c for c in ctx if (c.get("s") or 0) > 1.0]
            if ctx:
                libres = [c.get("ram_libre_mb") for c in ctx if c.get("ram_libre_mb") is not None]
                print("  memoria en los avances: RAM libre min %s MB / max %s MB; juego hasta %s MB" % (
                    min(libres) if libres else "?", max(libres) if libres else "?",
                    max([c.get("juego_mb") or 0 for c in ctx])), flush=True)
            for c in picos:
                print("  PICO next day %.2f s el dia %s (%s workers, evento %s, RAM libre %s MB, %s%% usada, juego %s MB)" % (
                    c["s"], c.get("dia"), c.get("workers"), c.get("evento"),
                    c.get("ram_libre_mb"), c.get("ram_carga_pct"), c.get("juego_mb")), flush=True)
            comprobadas = ejercitado.get("compras_verificadas") or 0
            rechazadas = ejercitado.get("compras_rechazadas") or 0
            if comprobadas or rechazadas:
                print("  compras comprobadas (T12.3): %d cobradas, %d rechazadas por falta de oro"
                      % (comprobadas, rechazadas), flush=True)
            censo = ejercitado.get("scroll_censo") or {}
            if censo:
                print("  listas largas vigiladas (T15.4): %s" % (
                    ", ".join("%s=%d" % (k, v) for k, v in sorted(censo.items()))), flush=True)

    goal_path = savedir / "autoplay-goal.json"
    if goal_path.exists():
        try:
            goal = json.loads(goal_path.read_text(encoding="utf-8"))
        except ValueError:
            goal = {}
        if goal:
            print("")
            print("JUGADOR CON OBJETIVO: %s -- objetivo %s de %s, %s dias, $%s, %s workers, edificios %s" % (
                goal.get("status"), goal.get("objective"), goal.get("target"),
                goal.get("days_played"), goal.get("money"), goal.get("workers"),
                goal.get("buildings")), flush=True)
            previo = None
            for paso in goal.get("timeline") or []:
                dias = "" if previo is None else "  (+%d dias, +%d acciones)" % (
                    paso["day"] - previo["day"], paso["actions"] - previo["actions"])
                print("  objetivo %-2s desde el dia %-3s $%-7s %2s workers%s" % (
                    paso["objective"], paso["day"], paso["money"], paso["workers"], dias), flush=True)
                previo = paso
            for e in goal.get("experiments") or []:
                print("  experimento %-28s dia %-4s coste %-7s neto/dia %s -> %s (delta %s, se paga en %s dias)" % (
                    e.get("name"), e.get("day"), e.get("cost"), e.get("net_before"),
                    e.get("net_after"), e.get("delta"), e.get("payback_days")), flush=True)
            for tarea, dias in (goal.get("task_fail_days") or {}).items():
                print("  tarea atascada: %s (%d dias)" % (tarea, len(dias)), flush=True)

    shots = sorted(savedir.glob("shot-*.png"))
    print("capturas: %d" % len(shots), flush=True)
    # Una sesion tambien se conserva si alguna prueba fallo: ahi esta la
    # evidencia (capturas shot-fail-*) que hace falta para triarla.
    pruebas_fallidas = False
    if report_path.exists():
        try:
            _t = json.loads(report_path.read_text(encoding="utf-8")).get("tests") or {}
            pruebas_fallidas = any(v.get("ok") is False for v in _t.values())
        except ValueError:
            pass
    hubo_fallos = bool(findings) or pruebas_fallidas
    if hubo_fallos or args.keep:
        print("artefactos:", base, flush=True)
    else:
        # Sesion limpia: no hay nada que mirar y ocupa ~95 MB. Se borra.
        shutil.rmtree(base, ignore_errors=True)
        print("sesion limpia: carpeta borrada (usa --keep para conservarla)", flush=True)
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
