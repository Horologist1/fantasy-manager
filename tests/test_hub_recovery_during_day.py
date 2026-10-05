"""La red de seguridad del hub no puede volver a mostrar la taberna A MITAD del dia.

`fm_recover_hub_if_bare` (main_flow.rpy) re-muestra la taberna cuando el juego
espera en main_flow.rpy con la escena vacia. Se inhibe con
`renpy.session["fm_en_paso_de_dia"]`, pero esa marca solo se encendia en
`day_transition`, al FINAL del dia. El jugador con objetivo lo cazo (2026-10-03):
al cumplirse el objetivo 4 durante "Next Day", el log dice "HUB RECOVERY: bare
scene while waiting at the hub" justo antes del evento aleatorio del dia; la
taberna quedaba pulsable antes del evento y del informe diario (el jugador fue a
la tienda y uso una pocion), y luego la tarjeta "Quiet month / Review monthly
conditions" flotaba sobre la taberna, que es el sintoma que habia reportado un
jugador.

La marca se enciende ahora al EMPEZAR a procesar el dia (next_day y el avance de
varios dias) y la limpia tavern_screen al llegar. Estos contratos lo fijan.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_FLOW = ROOT / "game/scripts/main_flow.rpy"
UI = ROOT / "game/scripts/core/gameplay_improvements_ui.rpy"
FLAG = 'renpy.session["fm_en_paso_de_dia"] = True'


def _label_body(source, label):
    head = "label %s" % label
    assert head in source, "desaparecio %s" % head
    body = source.split(head, 1)[1]
    # Hasta el siguiente label de nivel superior.
    end = body.find("\nlabel ")
    return body if end < 0 else body[:end]


def test_next_day_marks_the_day_before_processing_it():
    body = _label_body(MAIN_FLOW.read_text(encoding="utf-8"), "next_day:")
    assert FLAG in body, (
        "next_day ya no enciende fm_en_paso_de_dia: la recuperacion del hub "
        "vuelve a mostrar la taberna a mitad del dia")
    assert body.index(FLAG) < body.index("process_next_day()"), (
        "la marca debe encenderse ANTES de process_next_day(): ahi dentro se "
        "lanzan los dialogos de objetivo y se elige el evento del dia")


def test_multi_day_advance_marks_the_day_too():
    source = UI.read_text(encoding="utf-8")
    body = _label_body(source, "auto_advance_days:")
    assert FLAG in body, (
        "el avance de varios dias no enciende fm_en_paso_de_dia")


def test_tavern_screen_still_clears_the_mark():
    body = _label_body(MAIN_FLOW.read_text(encoding="utf-8"), "tavern_screen")
    assert 'renpy.session["fm_en_paso_de_dia"] = False' in body, (
        "tavern_screen ya no limpia la marca: la red de seguridad del hub "
        "quedaria apagada para siempre tras el primer dia")


def test_recovery_still_honours_the_mark():
    source = MAIN_FLOW.read_text(encoding="utf-8")
    body = source.split("def fm_recover_hub_if_bare():", 1)[1].split("\nscreen ", 1)[0]
    assert 'renpy.session.get("fm_en_paso_de_dia")' in body, (
        "fm_recover_hub_if_bare ya no consulta la marca del paso de dia")
