"""El avance de varios dias dibuja progreso, y la pausa que lo hace DEBE expirar.

`auto_advance_days` hace `hide screen tavern`, asi que mientras se simulan los
dias no se dibujaba nada: medido con el perfilador de fotogramas de Ren'Py,
process_next_day() cuesta ~300 ms y el bucle encadenaba dos dias por fotograma,
o sea tirones de 630-736 ms con la pantalla muerta. Ahora se dibuja una tarjeta
de progreso entre dia y dia (verificado: 32 fotogramas con exactamente 1 dia cada
uno, de 387-436 ms).

La trampa, que me comi entera al escribirlo: `renpy.pause(delay)` con el `modal`
por defecto (True) **no expira nunca mientras haya una pantalla modal mostrada**,
y la tarjeta de progreso es modal. El juego se quedaba colgado para siempre en el
avance de varios dias. Lo cazo el autojugador como atasco O2 en esa misma linea.
Estos contratos impiden que vuelva.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "game/scripts/core/gameplay_improvements_ui.rpy"


def _fuente():
    return UI.read_text(encoding="utf-8", errors="replace")


def _cuerpo_del_tick():
    fuente = _fuente()
    assert "def smart_advance_tick(" in fuente, (
        "desaparecio smart_advance_tick: el avance de varios dias vuelve a "
        "simular sin dibujar nada")
    return fuente.split("def smart_advance_tick(")[1].split("\n    def ")[0]


def test_la_pausa_puede_expirar_con_la_tarjeta_modal():
    cuerpo = _cuerpo_del_tick()
    pausa = re.search(r"renpy\.pause\(([^)]*)\)", cuerpo)
    assert pausa, "smart_advance_tick ya no pausa: sin pausa no se dibuja nada"
    args = pausa.group(1)
    assert "modal=False" in args, (
        "la pausa del avance necesita modal=False. Con el valor por defecto NO "
        "expira mientras la tarjeta modal este en pantalla, y el juego se queda "
        "colgado para siempre a mitad del avance de varios dias")


def test_la_pausa_no_se_salta_con_un_clic_ni_toca_el_rollback():
    args = re.search(r"renpy\.pause\(([^)]*)\)", _cuerpo_del_tick()).group(1)
    assert "hard=True" in args, (
        "sin hard=True un clic salta la pausa y se cuela en mitad de la "
        "simulacion del dia")
    assert "checkpoint=False" in args, (
        "sin checkpoint=False la pausa escribe en el log de rollback una vez por "
        "dia simulado; este proyecto corre con rollback desactivado y los saves "
        "viajan en el snapshot")


def test_la_tarjeta_se_muestra_y_se_oculta_en_la_misma_llamada():
    # El bucle del avance tiene varias salidas (resumen, bancarrota, tres tipos
    # de evento, fin de mes). Si la tarjeta se mostrara fuera de aqui, alguna de
    # ellas la dejaria pegada encima del juego.
    cuerpo = _cuerpo_del_tick()
    assert "renpy.show_screen(\"smart_advance_progress\"" in cuerpo
    assert "renpy.hide_screen(\"smart_advance_progress\")" in cuerpo
    assert "finally:" in cuerpo, (
        "el hide debe estar en un finally: si la pausa revienta, la tarjeta se "
        "quedaria en pantalla")
    fuente = _fuente()
    assert fuente.count("renpy.show_screen(\"smart_advance_progress\"") == 1, (
        "la tarjeta se muestra desde mas de un sitio: vuelve a poder quedarse "
        "pegada por alguna salida del bucle")


def test_los_saltos_del_motor_se_dejan_pasar():
    cuerpo = _cuerpo_del_tick()
    assert "CONTROL_EXCEPTIONS" in cuerpo, (
        "smart_advance_tick debe re-lanzar las excepciones de control: tragarse "
        "un salto o un fin de interaccion rompe el flujo del juego")


def test_el_tick_corre_una_vez_por_dia_y_antes_de_simularlo():
    fuente = _fuente()
    assert fuente.count("smart_advance_tick(") == 2, (
        "smart_advance_tick deberia definirse una vez y llamarse una vez")
    pos_tick = fuente.index("$ smart_advance_tick(")
    pos_dia = fuente.index("$ auto_advance_pending_result = process_next_day()")
    assert pos_tick < pos_dia, (
        "el dibujo debe ir ANTES de simular el dia, o el jugador ve el progreso "
        "cuando ya ha pasado la espera")
