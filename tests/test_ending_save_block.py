"""Un guardado a mitad del final no puede costar el Governor's Castle.

El jugador con objetivo (2026-10-03, partida Burdel NSFW) guardo y cargo en
mitad de show_ending_assassination: la carga volvio al hub con el objetivo 16
completo, pero sin la subida de nivel del manager ni el Governor's Castle, que
se conceden al FINAL de la escena. La reparacion de tavern_screen solo actuaba
si el castillo ya estaba en owned_buildings, asi que no se recuperaba nunca.

Dos capas: los finales bloquean el guardado hasta conceder las recompensas
(tavern_screen lo libera al llegar) y tavern_screen concede el castillo a las
partidas que ya quedaron asi.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_FLOW = ROOT / "game/scripts/main_flow.rpy"


def _label(source, name):
    head = "label %s" % name
    assert head in source, "desaparecio %s" % head
    body = source.split(head, 1)[1]
    end = body.find("\nlabel ")
    return body if end < 0 else body[:end]


def test_both_endings_block_saves_before_granting_rewards():
    source = MAIN_FLOW.read_text(encoding="utf-8")
    for name in ("show_ending_assassination:", "show_ending_blackmail:"):
        body = _label(source, name)
        block = 'set_save_blocked_context("ending")'
        assert block in body, "%s ya no bloquea el guardado" % name
        assert body.index(block) < body.index("unlock_governor_castle("), (
            "%s: el bloqueo debe ir ANTES de conceder el castillo" % name)
        assert body.index(block) < body.index("manager_levelup_benefit"), (
            "%s: el bloqueo debe ir ANTES de la subida de nivel" % name)


def test_tavern_screen_releases_the_block_and_repairs_missing_castle():
    body = _label(MAIN_FLOW.read_text(encoding="utf-8"), "tavern_screen")
    assert "set_save_blocked_context(None)" in body, (
        "tavern_screen ya no libera el bloqueo de guardado: tras el final no "
        "se podria guardar nunca mas")
    assert "objective_16_complete" in body and "Governor's Castle\" not in owned_buildings" in body, (
        "tavern_screen ya no repara las partidas con el objetivo 16 completo "
        "y sin castillo")
