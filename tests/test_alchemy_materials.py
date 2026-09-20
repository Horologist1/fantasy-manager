"""Real inventory shapes, atomic spending, content filtering and guild rewards."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_alchemy.recipes import (MATERIAL_IDS, REQUIREMENTS, recipe_rows, material_count,
                               brew_quote, prepare_brew, guild_material_drop)

DEFINITIONS = json.loads((ROOT / "game/data/items/alchemy_ingredients.json").read_text(encoding="utf-8"))["items"]
ROOT_ID, LEAF_ID = MATERIAL_IDS[:2]


def test_material_definitions_are_six_normal_items_and_every_recipe_uses_two():
    assert len(DEFINITIONS) == 6 and {row["id"] for row in DEFINITIONS} == set(MATERIAL_IDS)
    for row in DEFINITIONS:
        assert row["type"] == "ingredient" and row["price"] == 200
        assert row["guild_ingredient"] and row["weight"] == 0
        assert row["shop_only"] == "shop1" and row["shop_available"] and row["shop_chance"] == 1
    for row in recipe_rows(True):
        assert len(REQUIREMENTS[row[0]]) == len(set(REQUIREMENTS[row[0]])) == 2
        assert set(REQUIREMENTS[row[0]]) <= set(MATERIAL_IDS)


@pytest.mark.parametrize("entry,quantity", [
    (ROOT_ID, 1), ([ROOT_ID], 1), ([ROOT_ID, 3], 3), ((ROOT_ID, "4", False), 4),
    ({"item_id": ROOT_ID, "quantity": "2", "equipped": "false"}, 2),
    ([ROOT_ID, 3, True], 0), ([ROOT_ID, -5, False], 0), ([ROOT_ID, "bad", False], 0),
])
def test_legacy_inventory_shapes_are_counted_without_mutating(entry, quantity):
    inventory = [entry, ["health_potion", 6, False]]
    before = deepcopy(inventory)
    assert material_count(inventory, ROOT_ID) == quantity
    assert inventory == before


@pytest.mark.parametrize("inventory,cost", [
    ([], 800), ([(ROOT_ID, 3, False)], 600), ([(ROOT_ID, 1, False), (LEAF_ID, 2, False)], 400),
])
def test_buy_only_missing_and_consume_exactly_one_of_each(inventory, cost):
    inventory = deepcopy(inventory) + [["iron_sword", 1, True], {"item_id": "health_potion", "quantity": 13, "equipped": False}]
    before = deepcopy(inventory)
    quote = brew_quote("vigor", inventory, DEFINITIONS, 400)
    assert quote["total"] == cost
    updated, charged, status = prepare_brew("vigor", inventory, DEFINITIONS, 400, cost, cost)
    assert status == "ok" and charged == cost and inventory == before
    for key in (ROOT_ID, LEAF_ID):
        assert material_count(updated, key) == max(0, material_count(before, key) - 1)
    assert updated[-2:] == before[-2:]


def test_duplicate_material_stacks_and_equipped_entries_do_not_overconsume():
    inv = [(ROOT_ID, 0, False), [ROOT_ID, 1, False], [ROOT_ID, 4, False],
           (LEAF_ID, 1, True), {"item_id": LEAF_ID, "quantity": 2}]
    updated, cost, status = prepare_brew("vigor", inv, DEFINITIONS, 400, 400, 400)
    assert status == "ok" and cost == 400
    assert material_count(updated, ROOT_ID) == 4 and material_count(updated, LEAF_ID) == 1
    assert (LEAF_ID, 1, True) in updated


@pytest.mark.parametrize("reason", ["money", "changed", "recipe", "catalog"])
def test_rejected_brew_does_not_spend_or_mutate(reason):
    inv = [[ROOT_ID, 3, False], ["health_potion", 5, False]]
    before = deepcopy(inv)
    definitions = DEFINITIONS if reason != "catalog" else DEFINITIONS[:1]
    result = prepare_brew("desire" if reason == "recipe" else "vigor", inv, definitions, 400,
                          599 if reason == "money" else 9999, 400 if reason == "changed" else 800, False)
    assert result == (None, 0, "recipe" if reason == "catalog" else reason)
    assert inv == before


def test_quote_and_inventory_survive_json_without_new_save_fields():
    inv = [[ROOT_ID, 3, False], [LEAF_ID, 1, False]]
    snapshot = {"manager_inventory": inv, "event_flags": {"church_life_cycle": {"unlocked": True}}, "money": 700}
    loaded = json.loads(json.dumps(snapshot))
    quote = brew_quote("vigor", loaded["manager_inventory"], DEFINITIONS, 200)
    updated, cost, status = prepare_brew("vigor", loaded["manager_inventory"], DEFINITIONS, 200, loaded["money"], quote["total"])
    assert status == "ok" and cost == 200 and material_count(updated, ROOT_ID) == 2
    assert loaded == snapshot and set(loaded) == {"manager_inventory", "event_flags", "money"}


@pytest.mark.parametrize("building,job,outcome", [
    ("tavern", "adventurer", "Success"), ("adventurers_guild", "rest", "Critical Success"),
    ("adventurers_guild", "manager", "Success"), ("adventurers_guild", "adventurer", "Failure"),
])
def test_material_loot_only_rewards_successful_guild_expeditions(building, job, outcome):
    assert guild_material_drop(building, job, outcome, False, 0, 0) == []


def test_guild_drops_respect_probability_difficulty_and_content_filter():
    for idx in range(30):
        assert MATERIAL_IDS[-1] not in guild_material_drop("adventurers_guild", "adventurer", "Critical Success", False, 0, idx)
    assert guild_material_drop("adventurers_guild", "treasure_hunter", "Success", True, 0.39, 5) == [MATERIAL_IDS[-1]]
    assert guild_material_drop("adventurers_guild", "boss_hunting", "Success", True, 0.4, 0) == []
    assert guild_material_drop("adventurers_guild", "monster_taming", "Critical Success", True, 0.79, 0) == [ROOT_ID] * 2
    assert guild_material_drop("adventurers_guild", "adventurer", "Success", True, 0.25, 0, 0.5) == []
    assert guild_material_drop("adventurers_guild", "adventurer", "Success", True, 0, 0, 0) == []


def integration(discount=False):
    state = SimpleNamespace(money=2000, manager_inventory=[(ROOT_ID, 2, False)], workers=[{"name": "Brewer"}],
                            yvara_academy_discount_active=discount, _alchemy_paid_cost=0,
                            persistent=SimpleNamespace(nsfw_enabled=False))
    messages = []
    ns = {"store": state, "persistent": state.persistent, "items_json": {"items": DEFINITIONS},
          "ALCHEMY_COST_QUALITY": 400, "ALCHEMY_COST_PREMIUM": 1000,
          "set_save_blocked_context": lambda value: None,
          "renpy": SimpleNamespace(notify=messages.append)}
    source = (ROOT / "game/scripts/academy/alchemy_recipes.rpy").read_text(encoding="utf-8")
    exec(textwrap.dedent(source.split("init python:\n", 1)[1].split("\nscreen ", 1)[0]), ns)
    return state, ns


def test_cancelling_after_selecting_missing_materials_spends_nothing():
    state, ns = integration()
    before = deepcopy(state.manager_inventory)
    ns["alchemy_start_material_session"]("quality")
    assert ns["alchemy_select_material_recipe"]("vigor")
    ns["alchemy_refund_session"]()
    ns["alchemy_refund_session"]()
    assert state.money == 2000 and state.manager_inventory == before
    assert state._alchemy_material_quote is None and state._alchemy_session_fee is None


def test_real_commit_is_atomic_preserves_inventory_identity_and_cannot_repeat():
    state, ns = integration(True)
    inv = state.manager_inventory
    ns["alchemy_start_material_session"]("quality")
    assert ns["alchemy_select_material_recipe"]("vigor")
    assert state._alchemy_material_quote["total"] == 400  # Discounted 200 fee + one 200 ingredient.
    assert ns["alchemy_commit_materials"](state.workers[0])
    assert state.money == 1600 and material_count(state.manager_inventory, ROOT_ID) == 1
    assert state.manager_inventory is inv
    assert not ns["alchemy_commit_materials"](state.workers[0])
    assert state.money == 1600 and material_count(state.manager_inventory, ROOT_ID) == 1


def test_changed_inventory_and_detached_worker_cannot_spend_an_unapproved_amount():
    state, ns = integration()
    ns["alchemy_start_material_session"]("quality")
    assert ns["alchemy_select_material_recipe"]("vigor")
    assert not ns["alchemy_commit_materials"](dict(state.workers[0]))
    state.manager_inventory.clear()
    assert not ns["alchemy_commit_materials"](state.workers[0])
    assert state.money == 2000 and state.manager_inventory == []


def test_legacy_prepaid_cancel_still_refunds_once():
    state, ns = integration()
    state._alchemy_paid_cost = 800
    ns["alchemy_refund_session"]()
    ns["alchemy_refund_session"]()
    assert state.money == 2800
