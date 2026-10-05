"""Un `modifiers` que nadie lee es un rasgo que miente al jugador.

Los rasgos prometen su efecto en la propia descripcion, que es lo que el jugador
lee en la ficha del worker. Si una clave de `modifiers` no la consume ningun
codigo, el rasgo se queda en decoracion y el jugador cuenta con un efecto que no
existe. Es la misma clase de fallo que el Elixir of Passion (LA BIBLIA 21).

Cazado asi el 2026-10-01: el rasgo "Construct" declaraba `health_multiplier: 3.0`
y prometia "[3x Health, -10 Libido]". La clave no aparecia en NINGUN sitio del
codigo, asi que el -10 de libido se aplicaba y el triple de vida no: una
desventaja pura vendida como intercambio. Y era alcanzable, porque "Crown of the
Machine" (3650 de oro) concede el rasgo y repite la promesa.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TRAITS_DIR = ROOT / "game/data/traits"
CODE_DIRS = (ROOT / "game/scripts", ROOT / "game/python-packages")

# Claves que el codigo lee por un bucle genérico sobre los atributos secundarios
# (worker_traits.rpy, recalculate/apply_trait_secondary_modifiers_once) y por eso
# no aparecen como literal junto a `modifiers`.
CONSUMIDAS_POR_BUCLE_GENERICO = frozenset((
    "joy", "romance", "relationship", "libido", "comfort_desired",
    "comfort_level", "rebelliousness",
))


def _claves_de_modifiers():
    """Toda clave de `modifiers` declarada en el catalogo, con quien la declara."""
    encontradas = {}
    for ruta in sorted(TRAITS_DIR.glob("*.json")):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        if isinstance(datos, dict):
            datos = datos.get("traits") or []
        iterable = datos.values() if hasattr(datos, "values") else datos
        for rasgo in iterable:
            if not isinstance(rasgo, dict):
                continue
            for clave in (rasgo.get("modifiers") or {}):
                encontradas.setdefault(clave, []).append(
                    "%s/%s" % (ruta.name, rasgo.get("name", "?")))
    return encontradas


def _codigo():
    partes = []
    for carpeta in CODE_DIRS:
        if not carpeta.exists():
            continue
        for patron in ("*.rpy", "*.py"):
            for ruta in carpeta.rglob(patron):
                partes.append(ruta.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(partes)


CLAVES = _claves_de_modifiers()
CODIGO = _codigo()


def test_el_catalogo_de_rasgos_se_pudo_leer():
    assert CLAVES, "no se leyo ninguna clave de modifiers: ¿cambio el formato?"
    assert CODIGO, "no se leyo codigo con el que comparar"


@pytest.mark.parametrize("clave", sorted(CLAVES))
def test_cada_modificador_de_rasgo_lo_consume_alguien(clave):
    if clave in CONSUMIDAS_POR_BUCLE_GENERICO:
        pytest.skip("la aplica el bucle generico de atributos secundarios")
    # Basta con que el nombre aparezca como literal en el codigo: lo que este
    # test caza es la clave que no aparece en NINGUN sitio.
    assert re.search(r"[\"']%s[\"']" % re.escape(clave), CODIGO), (
        "ningun codigo lee el modificador de rasgo %r, declarado por %s: el "
        "rasgo promete un efecto en su descripcion y no lo entrega"
        % (clave, ", ".join(CLAVES[clave][:3])))
