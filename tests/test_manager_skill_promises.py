"""Cada habilidad de manager tiene que entregar EXACTAMENTE lo que su ficha promete.

La ficha del manager (screens.rpy) describe al jugador un numero concreto por
punto gastado, y el punto es irreversible. Si el texto promete +5 y el codigo
aplica +3, o si una habilidad no la consume nadie, el jugador paga un punto por
nada y no hay forma de que se entere: es la misma clase de fallo que el Elixir of
Passion (LA BIBLIA 21), que prometia +10 Libido y no aplicaba ninguna.

Comprobado el 2026-10-01: las cinco habilidades se consumen y los cinco
coeficientes coinciden con su texto. Este contrato lo mantiene asi.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SCREENS = ROOT / "game/scripts/core/screens.rpy"
STATS = ROOT / "game/scripts/workers/worker_stats.rpy"
TRAITS = ROOT / "game/scripts/workers/worker_traits.rpy"
FRANCHISE = ROOT / "game/scripts/franchise/franchise_holdings.rpy"

# Lo que la ficha promete, y donde tiene que estar aplicado. Cada entrada es
# (habilidad, [(fichero, patron_del_coeficiente, que_promete)]).
PROMESAS = {
    "business_acumen": [
        (STATS, r"money_mult\s*=\s*1\.0\s*\+\s*0\.1\s*\*\s*mgmt\.get\(\s*[\"']business_acumen[\"']",
         "+0.1 al multiplicador de dinero"),
        (FRANCHISE, r"income_multiplier\s*=\s*1\.0\s*\+\s*0\.1\s*\*\s*int\(management\.get\(\s*[\"']business_acumen[\"']",
         "+0.1 tambien en los ingresos de franquicia"),
    ],
    "whore_mastery": [
        (STATS, r"bonus\s*\+=\s*5\s*\*\s*mgmt\.get\(\s*[\"']whore_mastery[\"']",
         "+5 a las skills sexuales"),
    ],
    "combat_instruction": [
        (STATS, r"bonus\s*\+=\s*5\s*\*\s*mgmt\.get\(\s*[\"']combat_instruction[\"']",
         "+5 a Combat"),
        (STATS, r"bonus\s*\+=\s*10\s*\*\s*mgmt\.get\(\s*[\"']combat_instruction[\"']",
         "+10 a la vida maxima"),
    ],
    "servant_training": [
        (STATS, r"bonus\s*\+=\s*5\s*\*\s*mgmt\.get\(\s*[\"']servant_training[\"']",
         "+5 a Service"),
        (TRAITS, r"cap\s*=\s*max\(\s*0\s*,\s*\(cap or 100\)\s*-\s*10\s*\*\s*mgmt\.get\(\s*[\"']servant_training[\"']",
         "-10 al tope de rebeldia"),
    ],
    "gang_leader": [
        (STATS, r"bonus\s*\+=\s*5\s*\*\s*mgmt\.get\(\s*[\"']gang_leader[\"']",
         "+5 a Agility"),
        (STATS, r"bonus_energy\s*\+=\s*10\s*\*\s*mgmt\.get\(\s*[\"']gang_leader[\"']",
         "+10 a la energia maxima"),
    ],
}

# Numeros que la ficha ensena al jugador, tal y como los escribe screens.rpy.
TEXTO_PROMETIDO = {
    "business_acumen": "+0.1 to the money multiplier",
    "whore_mastery": "+5 to all sexual skills",
    "combat_instruction": "+5 to Combat and +10 to max HP",
    "servant_training": "+5 to Service and reduces max Rebelliousness by 10",
    "gang_leader": "+5 to Agility and +10 to max Energy",
}


def _fuente(ruta):
    return ruta.read_text(encoding="utf-8", errors="replace")


@pytest.mark.parametrize("habilidad", sorted(PROMESAS))
def test_la_habilidad_aplica_lo_que_promete(habilidad, subtests):
    for ruta, patron, promete in PROMESAS[habilidad]:
        with subtests.test(habilidad=habilidad, efecto=promete):
            assert re.search(patron, _fuente(ruta)), (
                "%s promete %r en la ficha del manager y %s ya no lo aplica con "
                "ese coeficiente: el jugador gasta un punto irreversible por nada"
                % (habilidad, promete, ruta.relative_to(ROOT)))


def test_la_ficha_sigue_describiendo_los_mismos_numeros(subtests):
    # Si alguien cambia el texto, tiene que cambiar tambien el coeficiente (y
    # este test). Lo que no vale es que el texto y el codigo se separen en silencio.
    fuente = _fuente(SCREENS)
    for habilidad, texto in sorted(TEXTO_PROMETIDO.items()):
        with subtests.test(habilidad=habilidad):
            assert texto in fuente, (
                "la ficha del manager ya no promete %r para %s; si el efecto "
                "cambio, hay que actualizar PROMESAS en este test"
                % (texto, habilidad))


def test_ninguna_habilidad_de_manager_se_queda_sin_consumidor(subtests):
    # El fallo que esto caza: una habilidad que solo existe en los defaults, en
    # el snapshot y en la UI, y que nadie lee para nada.
    declaradas = re.search(
        r"default management_skills = \{(.*?)\}", _fuente(ROOT / "game/scripts/script.rpy"),
        re.DOTALL)
    assert declaradas, "ya no existe el default de management_skills"
    claves = re.findall(r"[\"'](\w+)[\"']\s*:", declaradas.group(1))
    assert claves, "no se pudieron leer las habilidades declaradas"
    for clave in claves:
        with subtests.test(habilidad=clave):
            assert clave in PROMESAS, (
                "la habilidad de manager %r no esta en PROMESAS: o nadie la "
                "consume, o se anadio sin declarar aqui que efecto entrega" % clave)
