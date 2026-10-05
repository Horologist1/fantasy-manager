"""El roster tiene que aguantar 200 workers: nada cuadratico por fila.

Medido jugando con un save de 200 workers el 2026-10-01: abrir las pantallas de
plantilla costaba 1,56-1,73 s por culpa de dos patrones repetidos POR FILA, que
a 200 filas son decenas de miles de operaciones en cada repintado:

  1. buscar la posicion de un worker con next((idx for idx, n in enumerate(...)))
     dentro del propio bucle sobre la plantilla -> O(n^2);
  2. barrer building_types_json entero para resolver el tipo de edificio de cada
     worker, y re-emparejar los nombres de fichero de su carpeta de imagenes.

Tras indexar los tres (mapa nombre->posicion, building_type_def y memoizar
get_pattern_matches_flexible) las interacciones lentas pasaron de 5 a 0 y el
coste en frio de los retratos de 0,345 s a 0,030 s.

Estos contratos impiden que el patron vuelva a colarse.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Un bucle sobre la plantilla...
BUCLE_PLANTILLA = re.compile(
    r"for\s+\w+\s+in\s+.*(workers|roster|plantilla)", re.IGNORECASE)
# ...que dentro hace un barrido lineal de algo que se puede indexar.
BARRIDO_LINEAL = re.compile(
    r"next\s*\(\(|\bfor\s+\w+\s+in\s+(items_json|building_types_json|traits_json)\b")


def _ficheros_rpy():
    return sorted((ROOT / "game" / "scripts").rglob("*.rpy"))


def _bucles_con_barrido(ruta):
    """Devuelve (linea_bucle, linea_barrido, texto) por cada caso encontrado.

    Recorre el cuerpo del bucle por sangria, que es como Ren'Py delimita tanto
    los bloques de screen language como los de python.
    """
    lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    casos = []
    for i, linea in enumerate(lineas):
        if not BUCLE_PLANTILLA.search(linea):
            continue
        sangria = len(linea) - len(linea.lstrip())
        for j in range(i + 1, min(i + 60, len(lineas))):
            hijo = lineas[j]
            if not hijo.strip():
                continue
            if len(hijo) - len(hijo.lstrip()) <= sangria:
                break
            if BARRIDO_LINEAL.search(hijo):
                casos.append((i + 1, j + 1, hijo.strip()))
                break
    return casos


def test_ningun_bucle_sobre_la_plantilla_barre_linealmente(subtests):
    # A 200 workers cada barrido dentro del bucle se paga 200 veces por
    # fotograma. Lo que hay que hacer es construir el indice ANTES del bucle.
    for ruta in _ficheros_rpy():
        casos = _bucles_con_barrido(ruta)
        with subtests.test(fichero=ruta.name):
            assert not casos, (
                "%s tiene un barrido lineal dentro de un bucle sobre la "
                "plantilla (O(n^2) a 200 workers): %r"
                % (ruta.relative_to(ROOT), casos))


def test_existe_el_indice_de_tipos_de_edificio():
    fuente = (ROOT / "game/scripts/buildings/building_logic.rpy").read_text(encoding="utf-8")
    assert "def building_type_def(" in fuente, (
        "building_type_def desaparecio: sin el, cada fila de plantilla vuelve a "
        "barrer building_types_json entero")
    assert "renpy.session" in fuente.split("def building_type_index(")[1][:800], (
        "el indice de tipos de edificio debe vivir en renpy.session: un global de "
        "init python se serializa dentro del save y se queda rancio cuando un mod "
        "anade tipos")


def test_el_emparejado_de_imagenes_esta_memoizado_fuera_del_save():
    fuente = (ROOT / "game/scripts/events/event_visuals.rpy").read_text(encoding="utf-8")
    assert "def _pattern_matches_store(" in fuente, (
        "se perdio el cache de get_pattern_matches_flexible: volvera a tokenizar "
        "los nombres de fichero una vez por worker")
    almacen = fuente.split("def _pattern_matches_store(")[1][:400]
    assert "renpy.session" in almacen, (
        "el cache de emparejados debe vivir en renpy.session: pickleado en un save "
        "devolveria rutas de arte que ya no esta en disco")
    # Y tiene que vaciarse con los listados de los que deriva.
    reset = fuente.split("def _reset_media_file_caches(")[1][:600]
    assert "_pattern_matches_store().clear()" in reset, (
        "_reset_media_file_caches debe vaciar tambien el cache de emparejados")


def test_el_emparejado_devuelve_copias():
    # Varios llamantes filtran o mutan la lista devuelta; servir la lista del
    # cache tal cual la corromperia para todos los siguientes.
    fuente = (ROOT / "game/scripts/events/event_visuals.rpy").read_text(encoding="utf-8")
    cuerpo = fuente.split("def get_pattern_matches_flexible(")[1].split("\n    def ")[0]
    assert "return list(en_cache)" in cuerpo, "el acierto de cache debe devolver una copia"
    assert "return list(matches)" in cuerpo, "el fallo de cache debe devolver una copia"
