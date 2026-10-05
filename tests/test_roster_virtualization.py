"""La lista de plantilla construye solo las filas visibles: no romper las piezas.

Una fila del roster declara 31 displayables. Con 200 workers eso eran 6.200
construidos en CADA actualizacion de pantalla: 96 ms de media y 195 ms en el peor
caso, medido con renpy.profile_screen. Construyendo solo la ventana visible baja a
11,8 ms (8x). Es lo que hace una hoja de calculo: nunca dibuja las 200 filas.

La tecnica se apoya en cuatro piezas, y si falta cualquiera de ellas el resultado
no es "mas lento", es una lista rota: huecos al desplazar, o un ultimo worker
inalcanzable. Estos contratos las fijan. El comportamiento en ejecucion lo
comprueban ademas las pruebas jugadas T15.10, T15.11 y T15.12.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game/scripts/core/screens.rpy"


def _fuente():
    return SCREENS.read_text(encoding="utf-8", errors="replace")


def test_el_viewport_usa_el_adjustment_propio():
    # Sin el Adjustment propio nadie avisa de que el jugador ha desplazado, y la
    # ventana de filas construidas se queda congelada: huecos en blanco al bajar.
    fuente = _fuente()
    assert "yadjustment fm_roster_adjustment()" in fuente, (
        "el viewport del roster ya no usa fm_roster_adjustment(): al desplazar no "
        "se reevalua la pantalla y la lista se vera con huecos")


def test_el_callback_de_scroll_reevalua_la_pantalla():
    fuente = _fuente()
    cuerpo = fuente.split("def fm_roster_scrolled(")[1].split("\n    def ")[0]
    assert "restart_interaction" in cuerpo, (
        "fm_roster_scrolled debe reevaluar la pantalla: Adjustment.change solo "
        "redibuja, y redibujar no vuelve a construir las filas")
    assert "predicting" in cuerpo, (
        "hay que salir si Ren'Py esta prediciendo, o se reinicia una interaccion "
        "que no existe")


def test_la_fila_tiene_alto_explicito():
    # El hueco de las filas no construidas se calcula con esta constante. Si la
    # fila pasa a medir otra cosa sin actualizarla, el scroll se descuadra.
    fuente = _fuente()
    assert "ysize FM_ROSTER_ALTO_FILA" in fuente, (
        "la fila del roster perdio su alto explicito: la virtualizacion calcula "
        "los huecos con FM_ROSTER_ALTO_FILA y dejaria de cuadrar")


def test_existen_los_dos_huecos():
    fuente = _fuente()
    assert "if _fm_desde > 0:" in fuente and "null height fm_relleno_de_roster(_fm_desde)" in fuente, (
        "falta el hueco de arriba: la lista saltaria al principio al desplazar")
    assert "if _fm_hasta < _fm_total_filas:" in fuente, (
        "falta el hueco de abajo: el recorrido de la barra se acortaria y el "
        "ultimo worker quedaria inalcanzable")


def test_la_ventana_se_calcula_despues_de_ordenar_y_de_la_navegacion():
    # Es la propiedad de seguridad central: ordenar, contar, navegar y las
    # acciones por lotes tienen que ver la plantilla COMPLETA. La ventana solo
    # recorta lo que se construye.
    fuente = _fuente()
    pos_orden = fuente.index("filtered_workers = sort_worker_roster_entries(")
    pos_nav = fuente.index("_workers_nav_pos = {}")
    pos_ventana = fuente.index("_fm_desde, _fm_hasta = fm_ventana_de_roster(")
    assert pos_orden < pos_ventana, "la ventana se calcula antes de ordenar"
    assert pos_nav < pos_ventana, (
        "la ventana se calcula antes del indice de navegacion: el teclado "
        "indexaria sobre la ventana y no sobre la lista entera")
    # Y el bucle de filas es el UNICO que ve la ventana.
    assert "for worker in filtered_workers[_fm_desde:_fm_hasta]:" in fuente
    assert fuente.count("filtered_workers[_fm_desde:_fm_hasta]") == 1, (
        "la ventana se esta usando en mas sitios que el bucle de filas")


def test_hay_interruptor_de_emergencia():
    fuente = _fuente()
    assert re.search(r"FM_ROSTER_VIRTUAL\s*=\s*True", fuente), (
        "desaparecio el interruptor FM_ROSTER_VIRTUAL, que permite volver al "
        "comportamiento anterior sin tocar la pantalla")
    cuerpo = fuente.split("def fm_ventana_de_roster(")[1].split("\n    def ")[0]
    assert "if not FM_ROSTER_VIRTUAL" in cuerpo, (
        "fm_ventana_de_roster ya no respeta el interruptor")


def test_la_red_de_seguridad_sigue_puesta():
    fuente = _fuente()
    cuerpo = fuente.split("def fm_ventana_de_roster(")[1].split("\n    def ")[0]
    assert "fm_roster_paso_valido" in cuerpo, (
        "fm_ventana_de_roster ya no comprueba que la maquetacion cuadre: un "
        "cambio de alto de fila pasaria a descuadrar el scroll en silencio en "
        "vez de volver a construir la lista entera")


def test_el_adjustment_no_se_guarda_en_el_save():
    # Un Adjustment con callback metido en el store o en el scope de una screen
    # entra en el log de rollback y puede dejar los saves rotos (LA BIBLIA 8).
    fuente = _fuente()
    cuerpo = fuente.split("def fm_roster_adjustment(")[1].split("\n    def ")[0]
    assert "renpy.session" in cuerpo, (
        "el Adjustment del roster debe vivir en renpy.session, que no se "
        "serializa, y no en el store ni en el scope de la pantalla")
