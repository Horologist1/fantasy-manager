"""Gates recorded differently by older versions must be re-derived on load."""
from pathlib import Path
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def load():
    source = (ROOT / "game/scripts/core/legacy_progress.rpy").read_text(encoding="utf-8")
    start = source.index("    def reconcile_legacy_progress_on_load(")
    ns = {"renpy": SimpleNamespace(log=lambda message: None)}
    exec(textwrap.dedent(source[start:]), ns)
    return ns["reconcile_legacy_progress_on_load"]


def make_store(**overrides):
    store = SimpleNamespace(
        available_buildings={}, owned_buildings=[],
        academy_enrolled=False, arena_unlocked=False, arena_lanista_paid=False,
        yvara_s4_talks_done=[], yvara_s4_finance_unlocked=False,
        lanista_gender="", lanista_name="", lanista_known_name=False,
        lanista_has_legacy_progress=lambda: False,
        current_objective=1,
    )
    for number in range(1, 17):
        setattr(store, "objective_%d_complete" % number, False)
    for key, value in overrides.items():
        setattr(store, key, value)
    return store


def run(**overrides):
    fn = load()
    store = make_store(**overrides)
    fn.__globals__["store"] = store
    return store, fn()


def test_fresh_game_heals_nothing():
    store, healed = run()
    assert healed == []


def test_owned_academy_means_enrolled():
    store, healed = run(available_buildings={"Academy": {"type": "academy", "owned": True}})
    assert healed == ["academy_enrolled"] and store.academy_enrolled


def test_owned_arena_means_permit_paid_and_unlocked():
    store, healed = run(available_buildings={"Arena": {"type": "arena", "owned": True}})
    assert healed == ["arena_unlocked", "arena_lanista_paid"]
    store, healed = run(owned_buildings=["Arena"], arena_unlocked=True)
    assert healed == ["arena_lanista_paid"]


def test_ledger_talk_unlocks_yvara_finance():
    store, healed = run(yvara_s4_talks_done=["s4_t1"])
    assert healed == ["yvara_s4_finance_unlocked"] and store.yvara_s4_finance_unlocked
    store, healed = run(yvara_s4_talks_done=["s4_t2"])
    assert healed == []


def test_legacy_lanista_arc_gets_the_original_identity():
    store, healed = run(lanista_has_legacy_progress=lambda: True)
    assert healed == ["lanista_gender"]
    assert (store.lanista_gender, store.lanista_name, store.lanista_known_name) == ("male", "Varro", True)
    store, healed = run(lanista_gender="female", lanista_has_legacy_progress=lambda: True)
    assert healed == [] and store.lanista_gender == "female"


def test_current_objective_proves_earlier_ones():
    store, healed = run(current_objective=12, objective_3_complete=True)
    assert healed == ["objective_%d_complete" % n for n in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11)]
    assert not store.objective_12_complete and not store.objective_16_complete
    store, healed = run(current_objective="oops")
    assert healed == []


# --- Orden de aplicación en la carga -----------------------------------------
# El helper de arriba se prueba con las listas ya pobladas, lo que demuestra que la
# REGLA funciona pero no que _apply_snapshot la invoque cuando sus datos ya existen.
# En 0.9.6.2 la llamada iba 14 líneas ANTES de restaurar yvara_s4_talks_done, así que
# la cura de Yvara S4 nunca podía dispararse en una carga real.

SNAPSHOT_SRC = (ROOT / "game/scripts/save_snapshot.rpy").read_text(encoding="utf-8")


def _line_of(needle, source=None, start=0):
    src = source if source is not None else SNAPSHOT_SRC
    return src.count("\n", 0, src.index(needle, start)) + 1


def test_reconciliation_runs_after_the_lists_it_reads():
    """La reconciliación debe ir después de restaurar las listas de arco que lee."""
    lista = _line_of('("yvara_s4_talks_done", [])')
    reconciliacion = _line_of("store.reconcile_legacy_progress_on_load()")
    assert lista < reconciliacion, (
        "reconcile_legacy_progress_on_load() se ejecuta antes de restaurar "
        "yvara_s4_talks_done: leeria el default del store limpio y no curaria nada"
    )


def test_late_repair_pass_reconciles_again():
    """La pasada tardía reescribe campos curados desde el snapshot; hay que recurar."""
    primera = SNAPSHOT_SRC.index("store.reconcile_legacy_progress_on_load()")
    segunda = SNAPSHOT_SRC.find("store.reconcile_legacy_progress_on_load()", primera + 1)
    assert segunda != -1, (
        "falta la segunda reconciliacion: la pasada tardia de after_load reescribe "
        "yvara_s4_finance_unlocked y arena_unlocked desde el snapshot y desharia la cura"
    )
    sobrescritura = _line_of('"yvara_s4_finance_unlocked",')
    assert sobrescritura < _line_of("store.reconcile_legacy_progress_on_load()", start=primera + 1)
