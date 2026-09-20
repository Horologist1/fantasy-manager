"""Pure alchemy rules; normal inventory entries, no Ren'Py objects or I/O."""
from copy import deepcopy

RECIPES = (
    ("surprise", "Alchemist's assortment", "Ironroot + Crystal dust", False,
     ("potion_strong", "potion_tough", "potion_transformed", "potion_magical",
      "potion_robust", "potion_energetic", "potion_agile", "potion_great_figure",
      "potion_long_legs", "potion_exotic", "potion_beautiful")),
    ("vigor", "Vigor", "Ironroot + Sunleaf", False,
     ("potion_strong", "potion_tough", "potion_robust", "potion_energetic", "potion_agile")),
    ("arcana", "Arcana", "Mooncap + Crystal dust", False,
     ("potion_transformed", "potion_magical")),
    ("grace", "Grace", "Rose petals + Mooncap", False,
     ("potion_great_figure", "potion_long_legs", "potion_exotic", "potion_beautiful")),
    ("desire", "Desire", "Rose petals + Velvet seed", True,
     ("potion_large_breasts", "potion_small_breasts", "potion_firm_ass", "potion_soft_ass",
      "potion_large_hips", "potion_deluxe_derriere", "potion_large_penis", "potion_tight",
      "potion_sensitive", "potion_high_libido", "potion_nympho", "potion_satyr", "potion_cum_addict")),
)


def recipe_rows(nsfw=False):
    return [row for row in RECIPES if nsfw or not row[3]]


def potion_pool(recipe_id="surprise", nsfw=False):
    """Unknown/now-hidden recipes fall back to the original permitted pool."""
    row = next((r for r in recipe_rows(nsfw) if r[0] == recipe_id), RECIPES[0])
    result = list(row[4])
    if row[0] == "surprise" and nsfw:
        result.extend(RECIPES[-1][4])
    return result


MATERIAL_IDS = (
    "alchemy_ironroot", "alchemy_sunleaf", "alchemy_mooncap",
    "alchemy_crystal_dust", "alchemy_rose_petals", "alchemy_velvet_seed",
)
REQUIREMENTS = {
    "surprise": ("alchemy_ironroot", "alchemy_crystal_dust"),
    "vigor": ("alchemy_ironroot", "alchemy_sunleaf"),
    "arcana": ("alchemy_mooncap", "alchemy_crystal_dust"),
    "grace": ("alchemy_rose_petals", "alchemy_mooncap"),
    "desire": ("alchemy_rose_petals", "alchemy_velvet_seed"),
}
GUILD_JOBS = ("adventurer", "treasure_hunter", "boss_hunting", "monster_taming")


def _entry_parts(entry):
    """Read old strings, mappings and sequence entries without rewriting them."""
    if isinstance(entry, str):
        return entry, 1, False
    if hasattr(entry, "get"):
        item_id, quantity, equipped = entry.get("item_id"), entry.get("quantity", 1), entry.get("equipped", False)
    elif hasattr(entry, "__len__") and hasattr(entry, "__getitem__") and len(entry):
        item_id = entry[0]
        quantity = entry[1] if len(entry) > 1 else 1
        equipped = entry[2] if len(entry) > 2 else False
    else:
        return None, 0, False
    try:
        quantity = max(0, int(quantity))
    except (TypeError, ValueError, OverflowError):
        quantity = 0
    if isinstance(equipped, str):
        equipped = equipped.strip().lower() in ("true", "1", "yes", "y", "on")
    return item_id, quantity, bool(equipped)


def material_count(inventory, item_id):
    return sum(quantity for key, quantity, equipped in map(_entry_parts, inventory or ())
               if key == item_id and not equipped)


def brew_quote(recipe_id, inventory, definitions, fee, nsfw=False):
    """Quote only visible, complete recipes. No fallback that changes ingredients."""
    if recipe_id not in {row[0] for row in recipe_rows(nsfw)}:
        return None
    try:
        fee = int(fee)
    except (TypeError, ValueError, OverflowError):
        return None
    if fee < 0:
        return None
    by_id = {row.get("id"): row for row in definitions if hasattr(row, "get")}
    materials = []
    for item_id in REQUIREMENTS[recipe_id]:
        item = by_id.get(item_id)
        if not item or item.get("type") != "ingredient":
            return None
        try:
            price = int(item["price"])
        except (KeyError, TypeError, ValueError, OverflowError):
            return None
        if price <= 0:
            return None
        owned = material_count(inventory, item_id)
        materials.append({"id": item_id, "name": item.get("name", item_id), "owned": owned,
                          "required": 1, "missing": max(0, 1 - owned), "price": price})
    missing_cost = sum(row["missing"] * row["price"] for row in materials)
    return {"recipe_id": recipe_id, "fee": fee, "materials": materials,
            "missing_cost": missing_cost, "total": fee + missing_cost}


def prepare_brew(recipe_id, inventory, definitions, fee, money, authorized_total, nsfw=False):
    """Return a detached inventory only after validating price and all materials.

    Missing units are purchased and immediately used in this same transaction.
    Unrelated entries (including their legacy shapes and equipment) stay intact.
    """
    quote = brew_quote(recipe_id, inventory, definitions, fee, nsfw)
    if quote is None:
        return None, 0, "recipe"
    if quote["total"] > authorized_total:
        return None, 0, "changed"
    if money < quote["total"]:
        return None, 0, "money"
    to_take = {row["id"]: min(row["owned"], row["required"]) for row in quote["materials"]}
    updated = []
    for entry in inventory:
        item_id, quantity, equipped = _entry_parts(entry)
        take = min(quantity, to_take.get(item_id, 0)) if not equipped else 0
        if not take:
            updated.append(deepcopy(entry))
            continue
        to_take[item_id] -= take
        if quantity > take:
            updated.append((item_id, quantity - take, False))
    return updated, quote["total"], "ok"


def guild_material_drop(building_type, profession, outcome, nsfw, chance_roll, choice_index, loot_multiplier=1.0):
    """One additional gathering roll, separate from the game's normal loot pool."""
    if building_type != "adventurers_guild" or profession not in GUILD_JOBS:
        return []
    if outcome not in ("Success", "Critical Success"):
        return []
    critical = outcome == "Critical Success"
    chance = min(1.0, (0.8 if critical else 0.4) * max(0.0, loot_multiplier))
    if chance_roll >= chance:
        return []
    pool = MATERIAL_IDS if nsfw else MATERIAL_IDS[:-1]
    item_id = pool[choice_index % len(pool)]
    return [item_id] * (2 if critical else 1)
