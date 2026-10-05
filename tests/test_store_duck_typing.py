"""Los guardas de secuencia del store deben ser duck-typed, no isinstance.

En codigo del store, renpy/minstore.py:37-47 religa `list`, `dict` y `set` a los
tipos de renpy.revertable y renpy/python.py:246-252 copia ese namespace en cada
store. Por eso isinstance(valor_nativo, list) es False, y los valores nativos
entran por json.loads (data, sidecars de save, mods, DevKit) y por el motor.
Medido en ejecucion el 2026-09-28: list.__module__ == "renpy.revertable".
Ver LA BIBLIA §1.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _block(path, anchor, lines_after):
    source = (ROOT / path).read_text(encoding="utf-8")
    assert anchor in source, "%s ya no contiene %r" % (path, anchor)
    start = source.index(anchor)
    return "\n".join(source[start:].split("\n")[:lines_after])


def test_is_equipped_does_not_use_isinstance_against_list():
    # Una entrada de inventario recien parseada de JSON es una lista NATIVA:
    # con isinstance salia "no equipada".
    block = _block("game/scripts/core/screens.rpy", "def _is_equipped(item):", 14)
    assert "isinstance(item, (list, tuple))" not in block
    assert 'hasattr(item, "__getitem__")' in block
    assert 'not hasattr(item, "get")' in block


def test_captured_monster_deep_copy_does_not_use_isinstance_against_list():
    # `selected` sale de load_workers -> json.loads, asi que sus listas son
    # nativas: con isinstance la copia no se hacia y el worker compartia
    # traits/inventory con la plantilla del catalogo.
    block = _block("game/scripts/script.rpy", "            worker = dict(selected)", 12)
    assert "isinstance(value, list)" not in block
    assert 'hasattr(value, "__iter__")' in block


def test_inventory_entry_helper_stays_duck_typed():
    block = _block("game/scripts/core/screens.rpy", "def _is_inv_entry(x):", 12)
    assert 'hasattr(x, "__getitem__")' in block
    assert 'not hasattr(x, "get")' in block
