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
