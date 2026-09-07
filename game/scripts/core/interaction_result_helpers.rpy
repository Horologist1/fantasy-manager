init python:
    def _interaction_result_clear_changes():
        store._last_interaction_changes = {}

    def _interaction_result_is_friendly_tutorial_step(interaction):
        if not (
            getattr(store, "tutorial_active", False)
            and getattr(store, "current_objective", None) == 7
            and hasattr(interaction, "get")
        ):
            return False
        return (
            interaction.get("name", "").strip() in ("Friendly Chat", "Friendly Lunch")
            or interaction.get("id") in (
                "friendship_chat_female",
                "friendship_chat_male",
                "friendship_level1",
                "friendship_level1_lord_female",
                "friendship_level1_lord_male_platonic",
                "friendship_level1_lady_female_platonic",
                "friendship_level1_lady_male",
            )
        )

    def _interaction_result_mark_friendly_tutorial(interaction):
        if _interaction_result_is_friendly_tutorial_step(interaction):
            store.tutorial_friendly_chat_done = True

    def _interaction_result_check_friendly_tutorial(interaction):
        if _interaction_result_is_friendly_tutorial_step(interaction):
            check_objective_completion()

    def _interaction_result_mark_worker_flag(worker, flag_name):
        worker.setdefault("flags", {})[flag_name] = {"value": True, "duration": -1}

    def _interaction_result_refresh_capped_attribute(worker, attribute_name):
        set_attribute_with_caps(worker, attribute_name, worker.get(attribute_name, 0))

    def _interaction_result_set_capped_attribute(worker, attribute_name, value):
        set_attribute_with_caps(worker, attribute_name, value)

    def _interaction_result_apply_attribute_change(worker, attribute_name, amount):
        apply_attribute_change(worker, attribute_name, amount)

    def _interaction_result_notify(message):
        renpy.notify(message)

    def _interaction_result_sell_worker(worker):
        store._last_sale_price = store.sell_worker_to_specialty_buyer(worker)

    def _interaction_result_notify_sale():
        renpy.notify("Sold to a specialty buyer for " + str(getattr(store, "_last_sale_price", 0)))
