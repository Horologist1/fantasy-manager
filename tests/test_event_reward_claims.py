"""Un texto de opcion no puede prometer una recompensa que el efecto no da.

El caso concreto que motivo esto: 18 opciones anunciaban un "% de descuento"
cuando el motor solo sabe bajar el comfort en 1 via cost_modifier. Verificado
jugando el 2026-09-28 (nivel A del playtest): hoy no queda ninguno.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# "a 20% cut below their preferred rate" slipped past the first version of this
# pattern (it only knew "discount"/"off").
DISCOUNT = re.compile(r"(\d+\s*%|percent)\s*(discount|off|cut|less|reduction|below)|discount of\s*\d+", re.I)

TEXT_FIELDS = ("option", "message_success", "message_failure", "message")


def _choices():
    for path in sorted((ROOT / "game/data/events").rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        events = data.get("events", data) if isinstance(data, dict) else data
        if isinstance(events, dict):
            events = [events]
        for event in events:
            if not isinstance(event, dict):
                continue
            for choice in event.get("choices") or []:
                if isinstance(choice, dict):
                    yield path.name, event.get("id"), choice


def test_no_choice_promises_a_percentage_discount():
    offenders = []
    for filename, event_id, choice in _choices():
        blob = " ".join(str(choice.get(field) or "") for field in TEXT_FIELDS)
        if DISCOUNT.search(blob):
            offenders.append("%s:%s -> %r" % (filename, event_id, DISCOUNT.search(blob).group(0)))
    assert not offenders, (
        "El motor no aplica descuentos porcentuales (cost_modifier solo baja el comfort "
        "en 1). Estas opciones lo prometen:\n  " + "\n  ".join(offenders))


def test_paying_above_the_asking_price_costs_one_comfort_level_more():
    """The only cost_modifier > 1 in the data ("Offer above their asking price")
    must really cost more: one comfort level above the worker's demand, the
    mirror of the one-level discount."""
    source = (ROOT / "game/scripts/events/recruitment_functions.rpy").read_text(encoding="utf-8")
    assert "elif cost_modifier > 1.0:" in source
    assert "negotiated_comfort = min(20, int(desired_comfort) + 1)" in source


def test_better_terms_options_really_cost_more():
    """Design rule (2026-10-05): offering a recruit better or more generous terms
    is a real choice. It pays one comfort level above their demand
    (cost_modifier > 1) in exchange for the extra reputation and relationship.
    Before, it cost the asking price, so it was always the best option."""
    pattern = re.compile(r"^Offer (better|refined) terms|above their asking price", re.I)
    free = []
    for filename, event_id, choice in _choices():
        effect = choice.get("effect") or {}
        if pattern.search(str(choice.get("option") or "")) and effect.get("recruit_worker"):
            if not float(effect.get("cost_modifier") or 0) > 1:
                free.append("%s:%s" % (filename, event_id))
    assert not free, "These 'better terms' options cost nothing extra:\n  " + "\n  ".join(free)
