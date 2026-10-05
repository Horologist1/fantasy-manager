"""Campana de autojuego: muchas sesiones, resultado agregado.

Una sesion suelta pasa las pruebas pero toca poco: medido, 3 profesiones de 35 y
5 eventos de 275 en 330 s. La lista de pruebas pide volumen (35 profesiones, 50
eventos, 60 dias), y eso solo se consigue acumulando sesiones con semillas
distintas. Esto las lanza y suma lo ejercitado.

Uso:
    python tools/autoplay_campaign.py --sessions 10 --seconds 300
    python tools/autoplay_campaign.py --sessions 6 --from-save <dir> --mix
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
AUTOPLAY = ROOT / "tools/autoplay.py"
FIXTURE = ROOT / "tools/make_fixture_save.py"

# Las profesiones van por TIPO DE EDIFICIO: una partida por tipo las cubre
# todas. Repartir la plantilla entre seis edificios a la vez deja casi todos
# vacios, porque el auto-relleno solo usa el pool sin asignar.
EDIFICIOS = ("tavern", "brothel", "casino", "castle", "guild", "restaurant")


def generar_fixture(tipo, workers=40):
    """Crea una partida avanzada que posee SOLO ese tipo de edificio."""
    entorno = dict(os.environ, FM_FIXTURE_BUILDING=tipo, FM_FIXTURE_WORKERS=str(workers))
    # Reclutar y colocar 200 workers no cabe en los 120 s que bastan para 40:
    # con el tiempo corto el fixture sale a medias y la sesion mide otra cosa.
    segundos = 120 if workers <= 60 else 420
    proc = subprocess.run([sys.executable, str(FIXTURE), "--seconds", str(segundos)],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          env=entorno, timeout=segundos + 240)
    for linea in proc.stdout.decode("utf-8", "replace").splitlines():
        if linea.startswith("fixture listo en:"):
            return linea.split(":", 1)[1].strip()
    return None


def run_session(seconds, seed, mode, title, from_save, variant, fast_days=False):
    # --keep es imprescindible: sin el, la sesion borra su carpeta al terminar
    # y la campana se queda sin informe que leer. La campana la borra despues,
    # salvo que haya hallazgos que mirar.
    cmd = [sys.executable, str(AUTOPLAY), "--seconds", str(seconds), "--seed", str(seed),
           "--mode", mode, "--title", title, "--keep"]
    if from_save:
        cmd += ["--from-save", from_save]
    if variant:
        cmd += ["--variant", variant]
    if fast_days:
        cmd += ["--fast-days"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=seconds + 240)
    salida = proc.stdout.decode("utf-8", "replace")
    carpeta = None
    for linea in salida.splitlines():
        if linea.startswith("artefactos:"):
            carpeta = linea.split(":", 1)[1].strip()
    informe = None
    if carpeta:
        ruta = Path(carpeta) / "saves" / "autoplay-report.json"
        if ruta.exists():
            try:
                informe = json.loads(ruta.read_text(encoding="utf-8"))
            except ValueError:
                informe = None
    return informe, salida, carpeta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=int, default=6)
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--from-save", default="")
    parser.add_argument("--variant", default="")
    parser.add_argument("--rotate-buildings", action="store_true",
                        help="una partida por tipo de edificio (cubre sus profesiones)")
    parser.add_argument("--mix", action="store_true",
                        help="alterna SFW/NSFW y Lord/Lady entre sesiones")
    args = parser.parse_args()

    pantallas, profesiones, eventos = set(), set(), set()
    pruebas_ok, pruebas_ko = {}, {}
    hallazgos, dias = [], 0
    vacias = []
    objetivos = None

    inicio = datetime.now()
    for indice in range(1, args.sessions + 1):
        modo = ("sfw" if indice % 2 == 0 else "nsfw") if args.mix else "nsfw"
        titulo = ("Lord" if indice % 3 == 0 else "Lady") if args.mix else "Lady"
        print("--- sesion %d/%d (semilla %d, %s, %s%s) ---"
              % (indice, args.sessions, indice, modo, titulo,
                 ", dias rapidos" if (args.mix and indice % 2 == 0) else ""), flush=True)
        # Alternar los dos modos: el normal asigna y cubre profesiones, el
        # rapido acumula dias y eventos. Juntos cubren mas que cualquiera solo.
        partida = args.from_save
        if args.rotate_buildings:
            tipo = EDIFICIOS[(indice - 1) % len(EDIFICIOS)]
            # El techo de diseno son 200 workers, no 40: alternar los dos tamanos
            # para que lo que solo se rompe con la plantilla grande salga en la
            # campana y no haya que acordarse de medirlo a mano (BIBLIA 22).
            plantilla = 200 if indice % 2 == 1 else 40
            print("  preparando partida con solo: %s (%d workers)"
                  % (tipo, plantilla), flush=True)
            partida = generar_fixture(tipo, workers=plantilla)
            if not partida:
                print("  no se pudo generar el fixture; se salta", flush=True)
                continue
        rapido = args.mix and indice % 2 == 0
        informe, salida, carpeta = run_session(args.seconds, indice, modo, titulo,
                                               partida, args.variant, rapido)
        # La campana borra el fixture que ella creo, en cuanto termina de usarlo.
        # Asi no depende de una poda por antiguedad que puede llevarse por delante
        # el fixture de otra corrida que este en marcha.
        if args.rotate_buildings and partida:
            try:
                shutil.rmtree(Path(partida).parent, ignore_errors=True)
            except Exception:
                pass
        if informe is None:
            print("  sin informe; ultimas lineas:", flush=True)
            print("  " + "\n  ".join(salida.strip().splitlines()[-5:]), flush=True)
            continue
        cobertura = informe.get("coverage") or {}
        # Una sesion con 0 pantallas escribio informe pero no jugo: el bucle de
        # ticks nunca corrio. Sin la cola de su salida es imposible saber por que,
        # y la campana la estaba tirando a la basura.
        if not (cobertura.get("reached") or 0):
            print("  SESION VACIA (status=%r, ticks=%r, acciones=%r); ultimas lineas:"
                  % (informe.get("status"), informe.get("ticks"), informe.get("actions")),
                  flush=True)
            for _linea in salida.strip().splitlines()[-12:]:
                print("  " + _linea, flush=True)
            print("  artefactos conservados en: %s" % (carpeta,), flush=True)
            vacias.append((indice, carpeta))
        objetivos = cobertura.get("targets") or objetivos
        pantallas |= set(informe.get("screens_seen") or [])
        ejercitado = informe.get("ejercitado") or {}
        profesiones |= set(ejercitado.get("profesiones") or [])
        eventos |= set(ejercitado.get("eventos") or [])
        dias += int(ejercitado.get("dias_jugados") or 0)
        for nombre, fila in (informe.get("tests") or {}).items():
            if fila.get("ok") is True:
                pruebas_ok[nombre] = fila.get("detail", "")
            elif fila.get("ok") is False:
                pruebas_ko[nombre] = fila.get("detail", "")
        for fila in (informe.get("findings") or []):
            hallazgos.append(fila.get("message", ""))
        limpia = not (informe.get("findings") or [])
        if limpia and carpeta:
            shutil.rmtree(carpeta, ignore_errors=True)
        print("  cobertura %s/%s, %d pruebas, %d hallazgos"
              % (cobertura.get("reached"), cobertura.get("targets"),
                 len(informe.get("tests") or {}), len(informe.get("findings") or [])), flush=True)

    minutos = (datetime.now() - inicio).total_seconds() / 60.0
    print("")
    print("=========== CAMPANA (%d sesiones, %.0f min) ===========" % (args.sessions, minutos))
    objetivos = objetivos or 120
    utiles = len([p for p in pantallas if not str(p).startswith("_")])
    print("pantallas distintas vistas : %d (objetivo %d)" % (utiles, objetivos))
    print("profesiones ejercitadas    : %d de 35" % len(profesiones))
    print("eventos distintos vistos   : %d de 275" % len(eventos))
    print("dias jugados (suma)        : %d" % dias)
    print("pruebas distintas PASA     : %d" % len(pruebas_ok))
    if pruebas_ko:
        print("pruebas FALLA              : %d" % len(pruebas_ko))
        for nombre in sorted(pruebas_ko):
            print("   %-7s %s" % (nombre, pruebas_ko[nombre]))
    else:
        print("pruebas FALLA              : 0")
    if hallazgos:
        print("hallazgos de invariante    : %d" % len(hallazgos))
        for mensaje in hallazgos[:10]:
            print("   " + str(mensaje)[:150])
    else:
        print("hallazgos de invariante    : 0")
    if profesiones:
        print("profesiones: " + ", ".join(sorted(profesiones)))
    sys.exit(1 if (pruebas_ko or hallazgos) else 0)


if __name__ == "__main__":
    main()
