import json
from collections import Counter
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_alchemy.recipes import potion_pool, recipe_rows


def result_function(nsfw=False):
    source = (ROOT / "game/scripts/script.rpy").read_text(encoding="utf-8")
    start = source.index("    def apply_alchemy_result(")
    end = source.index("\n    def ", start + 1)
    def add(inv, item, quantity=1):
        inv[item] = inv.get(item, 0) + quantity
    ns = {"store": SimpleNamespace(persistent=SimpleNamespace(nsfw_enabled=nsfw)), "add_item_to_inventory": add}
    exec(textwrap.dedent(source[start:end]), ns)
    return ns["apply_alchemy_result"]


def test_every_recipe_item_exists_and_sfw_never_includes_desire():
    catalog = json.loads((ROOT / "game/data/items/items.json").read_text(encoding="utf-8"))["items"]
    ids = {i["id"] for i in catalog}
    for row in recipe_rows(True):
        assert set(potion_pool(row[0], True)) <= ids
    assert "desire" not in [r[0] for r in recipe_rows(False)]
    assert potion_pool("desire", False) == potion_pool("surprise", False)
    assert potion_pool("missing", False) == potion_pool("surprise", False)
    assert not set(potion_pool("desire", True)) & set(potion_pool("surprise", False))


def test_targeted_actual_rewards_stay_in_category_and_inventory_matches():
    apply = result_function(True)
    for recipe in recipe_rows(True):
        for tier in ("quality", "premium"):
            inventory = {}
            for _ in range(50):
                given = apply(tier, "success", inventory, recipe[0])
                assert len(given) == (2 if tier == "premium" else 1) and set(given) <= set(potion_pool(recipe[0], True))
            assert sum(inventory.values()) == (100 if tier == "premium" else 50)


def test_legacy_rewards_and_failure_remain_unchanged():
    apply = result_function()
    for outcome, count in (("critical_success", 30), ("success", 15), ("mediocre", 2)):
        inv = {}
        assert len(apply("basic", outcome, inv)) == count * 2
        assert inv == {"health_potion": count, "energy_potion": count}
    for tier in ("basic", "quality", "premium"):
        inv = {"existing": 4}
        assert apply(tier, "failure", inv, "arcana") == []
        assert inv == {"existing": 4}
    for tier in ("quality", "premium"):
        assert apply(tier, "mediocre", {}, "arcana")[0] in {"health_potion", "energy_potion", "stamina_elixir"}


@pytest.mark.parametrize("nsfw", [False, True])
@pytest.mark.parametrize("tier,quantity", [("quality", 1), ("premium", 2)])
@pytest.mark.parametrize("recipe", ["surprise", "vigor", "arcana", "grace", "desire", "missing"])
def test_critical_keeps_the_selected_family_and_adds_one_troll_blood(nsfw, tier, quantity, recipe, monkeypatch):
    # Exercise both ends of the actual allowed pool, including legacy/hidden
    # recipe fallbacks. The critical must never replace the purchased family.
    pool = potion_pool(recipe, nsfw)
    apply = result_function(nsfw)
    for selected in (pool[0], pool[-1]):
        def choose(options):
            assert options == pool
            return selected
        monkeypatch.setattr("random.choice", choose)
        before = {"health_potion": 9, "potion_troll_blood": 3, selected: 7}
        inventory = dict(before)
        given = apply(tier, "critical_success", inventory, recipe)
        assert Counter(given) == Counter({selected: quantity, "potion_troll_blood": 1})
        assert Counter(inventory) == Counter(before) + Counter(given)
        ordinary = apply(tier, "success", {}, recipe)
        assert Counter(given) - Counter(ordinary) == Counter({"potion_troll_blood": 1})


def test_discounted_cancel_refunds_once_and_clears_context():
    source = (ROOT / "game/scripts/academy/alchemy_recipes.rpy").read_text(encoding="utf-8")
    start = source.index("    def alchemy_refund_session(")
    end = source.index("\nscreen ", start)
    state = SimpleNamespace(money=100, _alchemy_paid_cost=400, _alchemy_recipe_id="arcana", _alchemy_chosen_worker={"name": "Test"})
    contexts = []
    ns = {"store": state, "set_save_blocked_context": contexts.append}
    exec(textwrap.dedent(source[start:end]), ns)
    ns["alchemy_refund_session"]()
    ns["alchemy_refund_session"]()
    assert state.money == 500 and state._alchemy_paid_cost == 0
    assert state._alchemy_chosen_worker is None and state._alchemy_recipe_id == "surprise"
    assert contexts == [None, None]
