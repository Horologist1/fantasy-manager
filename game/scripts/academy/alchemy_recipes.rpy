default _alchemy_recipe_id = "surprise"
default _alchemy_paid_cost = 0
default _alchemy_session_fee = None
default _alchemy_material_quote = None

init python:
    import fm_alchemy.recipes as _alchemy_rules

    def alchemy_start_material_session(tier):
        """Reserve a quoted fee, without taking money or materials yet."""
        store._alchemy_investment_tier = tier
        base = ALCHEMY_COST_QUALITY if tier == "quality" else ALCHEMY_COST_PREMIUM
        store._alchemy_session_fee = base // 2 if getattr(store, "yvara_academy_discount_active", False) else base
        store._alchemy_paid_cost = 0
        store._alchemy_material_quote = None
        store._alchemy_recipe_id = "surprise"
        set_save_blocked_context("alchemy_craft")

    def alchemy_current_quote(recipe_id):
        fee = getattr(store, "_alchemy_session_fee", None)
        if fee is None:
            return None
        return _alchemy_rules.brew_quote(recipe_id, store.manager_inventory, items_json.get("items", []), fee,
                                          bool(getattr(persistent, "nsfw_enabled", False)))

    def alchemy_recipe_rows():
        nsfw = bool(getattr(persistent, "nsfw_enabled", False))
        names = {item.get("id"): item.get("name", item.get("id")) for item in items_json.get("items", [])}
        result = []
        for row in _alchemy_rules.recipe_rows(nsfw):
            quote = alchemy_current_quote(row[0])
            if quote is None:
                continue
            result.append({"id": row[0], "name": row[1], "ingredients": row[2],
                           "stock": "  |  ".join(material["name"] + ": " + str(material["owned"]) + " owned / 1 needed" for material in quote["materials"]),
                           "cost": "Lab fee: " + str(quote["fee"]) + "  +  Missing ingredients: " + str(quote["missing_cost"]) + "  =  " + str(quote["total"]) + " coins",
                           "action": "Buy missing & use mixture" if quote["missing_cost"] else "Use stored ingredients",
                           "affordable": store.money >= quote["total"],
                           "potions": ", ".join(names.get(p, p) for p in _alchemy_rules.potion_pool(row[0], nsfw))})
        return result

    def alchemy_select_material_recipe(recipe_id):
        quote = alchemy_current_quote(recipe_id)
        if quote is None or store.money < quote["total"]:
            renpy.notify("You cannot afford this mixture or it is no longer available.")
            return False
        quote["tier"] = store._alchemy_investment_tier
        store._alchemy_material_quote = quote
        store._alchemy_recipe_id = recipe_id
        return True

    def alchemy_commit_materials(worker):
        if store._alchemy_investment_tier not in ("quality", "premium"):
            return True
        quote = getattr(store, "_alchemy_material_quote", None)
        if not quote or quote.get("tier") != store._alchemy_investment_tier or quote.get("recipe_id") != store._alchemy_recipe_id:
            renpy.notify("Please choose a mixture before brewing.")
            return False
        if not any(current is worker for current in store.workers):
            renpy.notify("Choose a worker from your current roster before brewing.")
            return False
        inventory, cost, result = _alchemy_rules.prepare_brew(
            quote["recipe_id"], store.manager_inventory, items_json.get("items", []), quote["fee"],
            store.money, quote["total"], bool(getattr(persistent, "nsfw_enabled", False)))
        if result != "ok":
            renpy.notify("Your funds or ingredients changed. Please review the mixture again.")
            return False
        # All checks precede this non-interacting transaction. Consume the quote
        # too: repeated callbacks cannot spend resources or start a free batch.
        store.manager_inventory[:] = inventory
        store.money -= cost
        store._alchemy_material_quote = None
        store._alchemy_session_fee = None
        store._alchemy_paid_cost = 0
        return True

    def alchemy_grant_guild_ingredients(worker, building_type, profession, outcome, awarded_names):
        name = worker.get("name")
        if name in awarded_names or building_type != "adventurers_guild" or profession not in _alchemy_rules.GUILD_JOBS or outcome not in ("Success", "Critical Success"):
            return []
        nsfw = bool(getattr(persistent, "nsfw_enabled", False))
        drops = _alchemy_rules.guild_material_drop(building_type, profession, outcome, nsfw,
                    renpy.random.random(), renpy.random.randrange(6 if nsfw else 5), get_difficulty_loot_multiplier())
        if drops:
            add_item_to_inventory(store.manager_inventory, drops[0], quantity=len(drops))
            awarded_names.add(name)
        return drops

    def alchemy_refund_session():
        """Cancel once, refunding the exact discounted price that was paid."""
        paid = max(0, int(getattr(store, "_alchemy_paid_cost", 0) or 0))
        store.money += paid
        store._alchemy_paid_cost = 0
        store._alchemy_chosen_worker = None
        store._alchemy_recipe_id = "surprise"
        store._alchemy_session_fee = None
        store._alchemy_material_quote = None
        set_save_blocked_context(None)

screen alchemy_recipe_menu():
    modal True
    zorder 101
    add Solid(gui.surface_dark)
    frame:
        align (0.5, 0.5)
        xsize 1120
        ysize 970
        padding (44, 32)
        background Solid("#eee2cb")
        vbox:
            spacing 12
            text "Choose a potion mixture" size font_size(32) color gui.journal_dark_color
            text "Coins: [money] | Ingredients come from Storage." size font_size(23) color gui.journal_text_color
            viewport:
                ysize 735
                mousewheel True
                draggable True
                scrollbars "vertical"
                vbox:
                    spacing 18
                    text "Each mixture uses one of each ingredient. Buy missing units here at Basic Shop prices. Everything is charged and consumed only after you choose a worker and begin brewing." size font_size(22) color gui.journal_text_color
                    text "Find ingredients in the Basic Shop or as additional Adventurer's Guild loot. Materials carried by workers must be transferred to Storage first." size font_size(22) color gui.journal_text_color
                    text "Craft and the fire rounds decide the outcome. Success: Quality makes one potion from the chosen family; Premium makes two. Critical: the same family yield plus one bonus Troll Blood per batch. Imperfect: standard restorative. Failure: batch lost." size font_size(22) color gui.journal_text_color
                    for recipe in alchemy_recipe_rows():
                        button:
                            id ("alchemy_recipe_" + recipe["id"])
                            xfill True
                            padding (18, 14)
                            background Solid("#dccba9")
                            hover_background Solid("#cdb485")
                            action Return(recipe["id"])
                            sensitive recipe["affordable"]
                            vbox:
                                spacing 5
                                text recipe["name"] size font_size(26) color gui.journal_dark_color
                                text "[recipe['stock']!q]" size font_size(23) color gui.journal_text_color xmaximum 945
                                text "[recipe['potions']!q]" size font_size(22) color gui.journal_text_color xmaximum 945
                                text recipe["cost"] size font_size(23) color gui.journal_dark_color
                                text (recipe["action"] if recipe["affordable"] else "Not enough coins") size font_size(23) color gui.journal_dark_color
            textbutton "Cancel session":
                id "alchemy_recipe_cancel"
                text_size font_size(24)
                text_color gui.journal_text_color
                text_hover_color gui.journal_hover_color
                action Return("cancel")
    key "K_BACKSPACE" action Return("cancel")
    key "game_menu" action Return("cancel")

label academy_alchemy_choose_recipe:
    $ set_save_blocked_context("alchemy_craft")
    $ _alchemy_recipe_id = "surprise"
    if _alchemy_investment_tier in ("quality", "premium"):
        if _alchemy_session_fee is None:
            # An old native session can have prepaid its whole former price.
            # Refund that reservation before offering the current recipes.
            $ alchemy_refund_session()
            $ alchemy_start_material_session(_alchemy_investment_tier)
        call screen alchemy_recipe_menu
        if _return == "cancel":
            $ alchemy_refund_session()
            $ renpy.show_screen("map_screen")
            $ renpy.show_screen("academy_menu")
            jump tavern_screen
        if not alchemy_select_material_recipe(_return):
            jump academy_alchemy_choose_recipe
    jump academy_alchemy_choose_worker
