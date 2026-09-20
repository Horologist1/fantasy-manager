"""Arena erotic formats unlocked under older rules must stay assignable after loading."""
from pathlib import Path
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def reconcile():
    source = (ROOT / "game/scripts/lanista/lanista_complete.rpy").read_text(encoding="utf-8")
    start = source.index("    LANISTA_PROGRAM_UNLOCKS = (")
    end = source.index("\n    def ", source.index("    def lanista_reconcile_program_unlocks(") + 1)
    ns = {"renpy": SimpleNamespace(log=lambda message: None)}
    exec(textwrap.dedent(source[start:end]), ns)
    return ns


def make_store(**overrides):
    store = SimpleNamespace(
        lanista_arena_program_tier=0, lanista_card_tier=0,
        lanista_pinup_unlocked=False, lanista_oilchains_unlocked=False, lanista_spectacle_unlocked=False,
        available_buildings={}, workers=[],
    )
    for key, value in overrides.items():
        setattr(store, key, value)
    return store


def run(**overrides):
    ns = reconcile()
    store = make_store(**overrides)
    ns["store"] = store
    changed = ns["lanista_reconcile_program_unlocks"]()
    return store, changed


def test_fresh_save_stays_locked():
    store, changed = run()
    assert changed == []
    assert not store.lanista_pinup_unlocked


def test_legacy_card_tier_unlocks_bikini_bouts():
    store, changed = run(lanista_card_tier=2)
    assert changed == ["lanista_pinup_unlocked"]
    assert store.lanista_pinup_unlocked and not store.lanista_oilchains_unlocked
    assert store.lanista_arena_program_tier == 1


def test_legacy_card_tier_four_unlocks_every_format():
    store, changed = run(lanista_card_tier=4)
    assert changed == ["lanista_pinup_unlocked", "lanista_oilchains_unlocked", "lanista_spectacle_unlocked"]
    assert store.lanista_arena_program_tier == 3


def test_workers_already_on_the_job_prove_it_was_unlocked():
    """The reported bug: old fighters kept the job while new ones could not pick it."""
    store, changed = run(available_buildings={"Arena": {"type": "arena", "servant_jobs": {"Brax": "arena_pinup_barbarian"}}})
    assert changed == ["lanista_pinup_unlocked"]
    assert store.lanista_pinup_unlocked


def test_rest_reservation_on_the_job_also_counts():
    store, changed = run(workers=[{"name": "Brax", "previous_profession": "arena_oil_chains"}])
    assert changed == ["lanista_oilchains_unlocked"]


def test_program_tier_alone_is_enough():
    store, changed = run(lanista_arena_program_tier=2)
    assert changed == ["lanista_pinup_unlocked", "lanista_oilchains_unlocked"]
    assert not store.lanista_spectacle_unlocked


def test_already_unlocked_flags_are_untouched():
    store, changed = run(lanista_card_tier=2, lanista_pinup_unlocked=True)
    assert changed == []
    assert store.lanista_arena_program_tier == 0
