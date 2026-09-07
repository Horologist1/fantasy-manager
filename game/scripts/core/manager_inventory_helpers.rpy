# Init-safe callable helpers for manager_inventory.
# Screen-local defs can enter Ren'Py rollback/save state; these module functions cannot.
init python:
    config.keymap.setdefault("fm_storage_prev", ["ctrl_K_LEFT"])
    config.keymap.setdefault("fm_storage_next", ["ctrl_K_RIGHT"])

    def manager_inventory_use_item(item_id, worker):
        return use_item(item_id, worker)

    def manager_inventory_toggle_equip_item(worker, item_id, item_index=None):
        return toggle_equip_item(worker.get("inventory", []), item_id, worker=worker, item_index=item_index)

    def close_manager_inventory(return_to_worker=None, return_to_in_roster=True,
                                return_to_from_buy_workers=False,
                                return_to_from_recruitment=False,
                                return_to_tavern=None):
        """Close inventory to its caller, including when invoked globally by ESC."""
        if return_to_tavern is None:
            # The global ESC overlay has no direct access to screen parameters.
            # Read the live screen scope; get_screen_variable only supports
            # screen-local defaults, not screen parameters.
            inventory_screen = renpy.get_screen("manager_inventory")
            screen_scope = getattr(inventory_screen, "scope", None)
            if not hasattr(screen_scope, "get"):
                return False
            return_to_worker = screen_scope.get("return_to_worker")
            return_to_in_roster = screen_scope.get("return_to_in_roster", True)
            return_to_from_buy_workers = screen_scope.get("return_to_from_buy_workers", False)
            return_to_from_recruitment = screen_scope.get("return_to_from_recruitment", False)
            return_to_tavern = screen_scope.get("return_to_tavern", False)

        renpy.hide_screen("manager_inventory")
        if return_to_worker is not None:
            renpy.show_screen(
                "worker_details",
                worker=return_to_worker,
                in_roster=return_to_in_roster,
                from_buy_workers=return_to_from_buy_workers,
                from_recruitment=return_to_from_recruitment,
            )
        elif return_to_tavern:
            renpy.show_screen("tavern")
        else:
            renpy.show_screen("map_screen")

    def cycle_manager_inventory_right_worker(direction):
        inventory_screen = renpy.get_screen("manager_inventory")
        screen_scope = getattr(inventory_screen, "scope", None)
        if not hasattr(screen_scope, "get"):
            return False
        if screen_scope.get("shop_mode") is not None:
            return False
        if screen_scope.get("is_transferring"):
            return False
        if any(renpy.get_screen(name) for name in ("worker_selection_popup", "inventory_filter_popup", "screen_intro_popup", "confirm", "error_popup")):
            return False

        workers = workers_filtered_by_gender(store.workers)
        left_worker = store.left_worker
        left_name = left_worker.get("name") if hasattr(left_worker, "get") else None
        workers = [worker for worker in workers if hasattr(worker, "get") and worker.get("name") != left_name]
        right_worker = store.right_worker
        right_name = right_worker.get("name") if hasattr(right_worker, "get") else None
        current_index = next((index for index, worker in enumerate(workers) if hasattr(worker, "get") and worker.get("name") == right_name), None)
        if not workers:
            if right_worker is False:
                return False
            next_worker = False
        else:
            step = -1 if direction < 0 else 1
            if current_index is None:
                next_worker = workers[-1] if step < 0 else workers[0]
            else:
                next_worker = workers[(current_index + step) % len(workers)]

            if right_name == next_worker.get("name"):
                return False

        _clear_row_selection("manager_inventory")
        renpy.set_screen_variable("last_row_click_key", None, "manager_inventory")
        renpy.set_screen_variable("last_row_click_ts", 0.0, "manager_inventory")
        store.right_worker = next_worker
        renpy.restart_interaction()
        return True

    def cycle_trade_multiplier():
        """Cycle through x1 -> x10 -> x100 -> x1"""
        current = renpy.get_screen_variable("trade_multiplier")
        if current == 1:
            renpy.set_screen_variable("trade_multiplier", 10)
        elif current == 10:
            renpy.set_screen_variable("trade_multiplier", 100)
        else:
            renpy.set_screen_variable("trade_multiplier", 1)
        renpy.restart_interaction()

    # _is_equipped is now defined at module level (init python) to avoid pickling issues

    def _set_left_row_selection(item, idx, item_info):
        renpy.set_screen_variable("selected_manager_item", item)
        renpy.set_screen_variable("selected_manager_index", idx)
        renpy.set_screen_variable("selected_worker_item", None)
        renpy.set_screen_variable("selected_worker_index", None)
        renpy.set_screen_variable("selected_description", item_info.get("description", ""))

    def _clear_row_selection(screen_name=None):
        renpy.set_screen_variable("selected_manager_item", None, screen_name)
        renpy.set_screen_variable("selected_manager_index", None, screen_name)
        renpy.set_screen_variable("selected_worker_item", None, screen_name)
        renpy.set_screen_variable("selected_worker_index", None, screen_name)
        renpy.set_screen_variable("selected_description", "", screen_name)

    def _set_right_worker_row_selection(item, idx, item_info):
        renpy.set_screen_variable("selected_worker_item", item)
        renpy.set_screen_variable("selected_worker_index", idx)
        renpy.set_screen_variable("selected_manager_item", None)
        renpy.set_screen_variable("selected_manager_index", None)
        renpy.set_screen_variable("selected_description", item_info.get("description", ""))

    def _set_right_shop_row_selection(item, item_info):
        renpy.set_screen_variable("selected_worker_item", item)
        renpy.set_screen_variable("selected_worker_index", None)
        renpy.set_screen_variable("selected_manager_item", None)
        renpy.set_screen_variable("selected_manager_index", None)
        renpy.set_screen_variable("selected_description", item_info.get("description", ""))

    # These helpers deliberately live at init/module scope. Do not move them back
    # into screen python blocks; repeated renders can retain runtime callables in
    # rollback and poison later saves (BIBLIA §8).

    def _get_item_info_by_id(item_id):
        item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
        return item_info if item_content_is_visible(item_info) else None

    def _get_canonical_worker_ref(worker):
        if not worker or worker is False:
            return None
        worker_name = worker.get("name", None) if hasattr(worker, "get") else None
        if worker_name:
            for w in store.workers:
                if hasattr(w, "get") and w.get("name", None) == worker_name:
                    return w
        return worker

    def _get_equipped_item_id_for_types(inventory, slot_types):
        for slot_type in slot_types:
            for item in inventory:
                if not item or len(item) < 2 or not store._is_equipped(item):
                    continue
                item_info = _get_item_info_by_id(item[0])
                if item_info and item_info.get("type") == slot_type:
                    return item[0]
        return None

    def _get_slot_candidate_item_ids(inventory, slot_types):
        candidate_ids = []
        for item in inventory:
            if not item or len(item) < 2:
                continue
            item_id = item[0]
            if item_id in candidate_ids:
                continue
            item_info = _get_item_info_by_id(item_id)
            if item_info and item_info.get("type") in slot_types:
                candidate_ids.append(item_id)
        return candidate_ids

    def cycle_summary_equipment_slot(worker, slot_key, direction=1):
        def get_item_info_by_id(item_id):
            item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
            return item_info if item_content_is_visible(item_info) else None

        def get_canonical_worker_ref(raw_worker):
            if not raw_worker or raw_worker is False:
                return None
            worker_name = raw_worker.get("name", None) if hasattr(raw_worker, "get") else None
            if worker_name:
                for w in store.workers:
                    if hasattr(w, "get") and w.get("name", None) == worker_name:
                        return w
            return raw_worker

        def get_equipped_item_id_for_types(inventory, slot_types):
            for slot_type in slot_types:
                for item in inventory:
                    if not item or len(item) < 2 or not store._is_equipped(item):
                        continue
                    item_info = get_item_info_by_id(item[0])
                    if item_info and item_info.get("type") == slot_type:
                        return item[0]
            return None

        def get_slot_candidate_item_ids(inventory, slot_types):
            candidate_ids = []
            for item in inventory:
                if not item or len(item) < 2:
                    continue
                item_id = item[0]
                if item_id in candidate_ids:
                    continue
                item_info = get_item_info_by_id(item_id)
                if item_info and item_info.get("type") in slot_types:
                    candidate_ids.append(item_id)
            return candidate_ids

        worker_ref = get_canonical_worker_ref(worker)
        if not worker_ref:
            return

        slot_types_map = {
            "weapon": ["weapon"],
            "body": ["armor", "clothing"],
            "accessory": ["accessory"],
        }
        slot_label_map = {
            "weapon": "Weapon",
            "body": "Clothing/Armor",
            "accessory": "Accessory",
        }
        slot_types = slot_types_map.get(slot_key, None)
        if not slot_types:
            return

        inventory = worker_ref.get("inventory", []) if hasattr(worker_ref, "get") else []
        options = [None] + get_slot_candidate_item_ids(inventory, slot_types)
        if len(options) <= 1:
            renpy.notify("{}: no available items".format(slot_label_map.get(slot_key, "Slot")))
            return

        current_item_id = get_equipped_item_id_for_types(inventory, slot_types)
        current_idx = options.index(current_item_id) if current_item_id in options else 0
        step = -1 if direction < 0 else 1
        next_idx = (current_idx + step) % len(options)
        next_item_id = options[next_idx]

        # Clear currently equipped entries in this slot family first.
        for idx, inv_item in enumerate(inventory):
            if not inv_item or len(inv_item) < 3 or not store._is_equipped(inv_item):
                continue
            equipped_info = get_item_info_by_id(inv_item[0])
            if equipped_info and equipped_info.get("type") in slot_types:
                inventory[idx] = (inv_item[0], inv_item[1], False)
                remove_item_effects(worker_ref, inv_item[0])

        if next_item_id:
            equip_index = None
            for idx, inv_item in enumerate(inventory):
                if not inv_item or len(inv_item) < 2:
                    continue
                if str(inv_item[0]) == str(next_item_id):
                    equip_index = idx
                    break
            toggle_equip_item(inventory, next_item_id, worker=worker_ref, item_index=equip_index)
            next_info = get_item_info_by_id(next_item_id) or {}
            renpy.notify("{}: {}".format(slot_label_map.get(slot_key, "Slot"), next_info.get("name", "Equipped")))
        else:
            renpy.notify("{}: Empty".format(slot_label_map.get(slot_key, "Slot")))

        renpy.restart_interaction()
    
    def get_item_action_elements(item, item_info, worker, item_index=None):
        item_type = item_info.get("type", "unknown")
        is_equipped = item[2]
        label = "No Action"
        action = NullAction()
        sensitive = False
        bg = None

        if item_type == "consumable" and worker is not None and worker is not False:
            label = "Use"
            action = Function(manager_inventory_use_item, item[0], worker)
            sensitive = True
        elif item_type not in ["consumable", "currency", "misc"] and worker is not None and worker is not False:
            sensitive = True
            if is_equipped:
                label = "Unequip"
            else:
                label = "Equip"
            action = Function(manager_inventory_toggle_equip_item, worker, item[0], item_index)
        # "currency" and "misc" fall through to "No Action" by default

        return (label, action, sensitive, bg)

    def transfer_to_right(left_worker, right_worker):
        smi = renpy.get_screen_variable("selected_manager_item")
        smi_index = renpy.get_screen_variable("selected_manager_index")
        multiplier = renpy.get_screen_variable("trade_multiplier")
        if smi is not None and (right_worker is not False) and not renpy.get_screen_variable("is_transferring"):
            renpy.set_screen_variable("is_transferring", True)
            renpy.set_screen_variable("selected_manager_item", None)
            renpy.set_screen_variable("selected_manager_index", None)
            
            # CRITICAL: Create a fresh copy of smi to break any reference sharing
            # This ensures we're working with the actual item data, not a shared reference
            if _is_inv_entry(smi) and len(smi) >= 2:
                smi = (str(smi[0]), int(smi[1]), bool(smi[2] if len(smi) > 2 else False))
                renpy.log(f"transfer_to_right: Normalized smi to {smi}")
            
            # Ensure locals exist even when transferring to/from storage
            source_worker = None
            target_worker = None

            # Get references to the actual store inventories (not local copies)
            if left_worker is None:
                source_inventory = store.manager_inventory
            else:
                # Find the worker in store.workers and use their inventory
                for w in store.workers:
                    if w.get("name") == left_worker.get("name"):
                        source_worker = w
                        break
                if source_worker:
                    if "inventory" not in source_worker:
                        source_worker["inventory"] = []
                    source_inventory = source_worker["inventory"]
                else:
                    source_inventory = left_worker.get("inventory", [])
            
            if right_worker is None:
                target_inventory = store.manager_inventory
            else:
                # Find the worker in store.workers and use their inventory
                for w in store.workers:
                    if w.get("name") == right_worker.get("name"):
                        target_worker = w
                        break
                if target_worker:
                    if "inventory" not in target_worker:
                        target_worker["inventory"] = []
                    target_inventory = target_worker["inventory"]
                else:
                    target_inventory = right_worker.get("inventory", [])
            
            # Ensure smi reflects the exact selected index (avoid equality collisions)
            if smi_index is not None and smi_index < len(source_inventory):
                try:
                    smi = source_inventory[smi_index]
                except Exception:
                    pass

            renpy.log(f"Transfer to right: Left={left_worker['name'] if left_worker else 'Storage'}, Right={right_worker['name'] if right_worker else 'Storage'}, Source={source_inventory}, Target={target_inventory}, Item={smi}")
            if store._is_equipped(smi) and left_worker and left_worker is not False:
                renpy.log(f"Unequipping selected copy of {smi[0]} from left worker")
                # Prefer exact index match to avoid desequipping a different copy
                did_unequip = False
                if smi_index is not None and smi_index < len(source_inventory):
                    try:
                        inv_item = source_inventory[smi_index]
                        if _is_inv_entry(inv_item) and len(inv_item) >= 3 and str(inv_item[0]) == str(smi[0]):
                            source_inventory[smi_index] = (inv_item[0], inv_item[1], False)
                            if source_worker or left_worker:
                                remove_item_effects(source_worker if source_worker else left_worker, inv_item[0])
                            did_unequip = True
                    except Exception:
                        pass
                if not did_unequip:
                    unequip_item_by_match(
                        source_inventory,
                        smi[0],
                        quantity=smi[1],
                        worker=source_worker if source_worker else left_worker
                    )
                # Keep smi consistent after unequip
                smi = (str(smi[0]), int(smi[1]), False)
            # Calculate actual transfer quantity (limited by available)
            available_qty = smi[1]
            transfer_qty = min(multiplier, available_qty)
            item_info = next((i for i in items_json["items"] if i["id"] == smi[0]), None)
            is_gift_to_worker = bool(
                item_info
                and item_info.get("type") == "gift"
                and left_worker is None
                and target_worker
            )
            # Gifts are delivered one by one to workers.
            if is_gift_to_worker and transfer_qty > 1:
                transfer_qty = 1
            renpy.log(f"transfer_to_right: Removing {smi[0]} (quantity: {transfer_qty}) from source")
            
            # Remove the exact selected entry when possible
            removed_exact = False
            if smi_index is not None:
                removed_exact = remove_item_from_inventory_by_index(source_inventory, smi_index, quantity=transfer_qty)
            if not removed_exact:
                # Fallback to id-based removal
                remove_item_from_inventory(source_inventory, smi[0], quantity=transfer_qty)

            # If source is manager_inventory and we removed by index, refresh store list
            if left_worker is None and removed_exact:
                store.manager_inventory = list(store.manager_inventory)
                renpy.store.manager_inventory = store.manager_inventory
            
            # Verify the removal worked
            if left_worker is None:
                # Double-check that the item was actually removed
                remaining_count = sum(item[1] for item in store.manager_inventory if _is_inv_entry(item) and len(item) >= 2 and item[0] == smi[0])
                renpy.log(f"transfer_to_right: After removal, {smi[0]} remaining in manager_inventory: {remaining_count}")
            renpy.log(f"Source after removal: {source_inventory}")
            renpy.log(f"Adding {smi[0]} (quantity: {transfer_qty}) to target: {target_inventory}")
            add_item_to_inventory(target_inventory, smi[0], quantity=transfer_qty)
            
            # Auto-consume on receive when item has auto_consume_on_receive and target is a worker
            try:
                if target_worker and item_info and (item_info.get("auto_consume_on_receive", False) or is_gift_to_worker):
                    for _ in range(int(transfer_qty)):
                        store.use_item(smi[0], target_worker)
            except Exception as e:
                renpy.log(f"auto_consume_on_receive error (to right): {e}")

            # CRITICAL: Force Ren'Py to recognize changes if target is manager_inventory
            if right_worker is None:
                # Also recreate target inventory to break references
                new_inv = []
                for item in store.manager_inventory:
                    if _is_inv_entry(item) and len(item) >= 2:
                        new_inv.append((str(item[0]), int(item[1]), bool(item[2] if len(item) > 2 else False)))
                    else:
                        new_inv.append(item)
                store.manager_inventory = new_inv
                renpy.store.manager_inventory = store.manager_inventory
            renpy.log(f"Target after addition: {target_inventory}")
            store.selected_description = ""
            if is_gift_to_worker and target_worker:
                renpy.notify(f"Gift delivered to {target_worker.get('name', 'worker')}")
            else:
                renpy.notify(f"Transferred {transfer_qty}x item to right")
            # Track tutorial objective 5 - potion transfer
            if item_info and hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item_info.get("name", "").lower().find("energy") != -1:
                store.potion_transferred = True
                renpy.log("DEBUG: Tutorial - Energy potion transferred to worker")
                renpy.log(f"DEBUG: Tutorial - Item name: {item_info.get('name', 'Unknown')}")
                renpy.log(f"DEBUG: Tutorial - tutorial_active: {store.tutorial_active}, current_objective: {store.current_objective}")
                try:
                    check_objective_completion()
                    renpy.log("DEBUG: Tutorial - check_objective_completion() called successfully")
                except Exception as e:
                    renpy.log(f"DEBUG: Tutorial - Error calling check_objective_completion(): {e}")
            else:
                renpy.log(f"DEBUG: Tutorial - Transfer conditions not met: tutorial_active={hasattr(store, 'tutorial_active')}, current_objective={store.current_objective if hasattr(store, 'current_objective') else 'NOT_SET'}, item_name={item_info.get('name', 'Unknown') if item_info else 'NO_ITEM_INFO'}")
            renpy.restart_interaction()
            renpy.set_screen_variable("is_transferring", False)

    def transfer_to_left(left_worker, right_worker):
        swi = renpy.get_screen_variable("selected_worker_item")
        swi_index = renpy.get_screen_variable("selected_worker_index")
        multiplier = renpy.get_screen_variable("trade_multiplier")
        if swi is not None and (left_worker is not False) and not renpy.get_screen_variable("is_transferring"):
            renpy.set_screen_variable("is_transferring", True)
            renpy.set_screen_variable("selected_worker_item", None)
            renpy.set_screen_variable("selected_worker_index", None)

            # Ensure locals exist even when transferring to/from storage
            source_worker = None
            target_worker = None
            
            # Get references to the actual store inventories (not local copies)
            if right_worker is None:
                source_inventory = store.manager_inventory
            else:
                # Find the worker in store.workers and use their inventory
                for w in store.workers:
                    if w.get("name") == right_worker.get("name"):
                        source_worker = w
                        break
                if source_worker:
                    if "inventory" not in source_worker:
                        source_worker["inventory"] = []
                    source_inventory = source_worker["inventory"]
                else:
                    source_inventory = right_worker.get("inventory", [])
            
            if left_worker is None:
                target_inventory = store.manager_inventory
            else:
                # Find the worker in store.workers and use their inventory
                for w in store.workers:
                    if w.get("name") == left_worker.get("name"):
                        target_worker = w
                        break
                if target_worker:
                    if "inventory" not in target_worker:
                        target_worker["inventory"] = []
                    target_inventory = target_worker["inventory"]
                else:
                    target_inventory = left_worker.get("inventory", [])
            
            # Ensure swi reflects the exact selected index (avoid equality collisions)
            if swi_index is not None and swi_index < len(source_inventory):
                try:
                    swi = source_inventory[swi_index]
                except Exception:
                    pass

            renpy.log(f"Transfer to left: Left={left_worker['name'] if left_worker else 'Storage'}, Right={right_worker['name'] if right_worker else 'Storage'}, Source={source_inventory}, Target={target_inventory}, Item={swi}")
            if store._is_equipped(swi) and right_worker and right_worker is not False:
                renpy.log(f"Unequipping selected copy of {swi[0]} from right worker")
                # Prefer exact index match to avoid desequipping a different copy
                did_unequip = False
                if swi_index is not None and swi_index < len(source_inventory):
                    try:
                        inv_item = source_inventory[swi_index]
                        if _is_inv_entry(inv_item) and len(inv_item) >= 3 and str(inv_item[0]) == str(swi[0]):
                            source_inventory[swi_index] = (inv_item[0], inv_item[1], False)
                            if source_worker or right_worker:
                                remove_item_effects(source_worker if source_worker else right_worker, inv_item[0])
                            did_unequip = True
                    except Exception:
                        pass
                if not did_unequip:
                    unequip_item_by_match(
                        source_inventory,
                        swi[0],
                        quantity=swi[1],
                        worker=source_worker if source_worker else right_worker
                    )
                # Keep swi consistent after unequip
                swi = (str(swi[0]), int(swi[1]), False)
            # Calculate actual transfer quantity (limited by available)
            available_qty = swi[1]
            transfer_qty = min(multiplier, available_qty)
            item_info = next((i for i in items_json["items"] if i["id"] == swi[0]), None)
            is_gift_to_worker = bool(
                item_info
                and item_info.get("type") == "gift"
                and right_worker is None
                and target_worker
            )
            # Gifts are delivered one by one to workers.
            if is_gift_to_worker and transfer_qty > 1:
                transfer_qty = 1
            renpy.log(f"transfer_to_left: Removing {swi[0]} (quantity: {transfer_qty}) from source")
            
            # Remove the exact selected entry when possible
            removed_exact = False
            if swi_index is not None:
                removed_exact = remove_item_from_inventory_by_index(source_inventory, swi_index, quantity=transfer_qty)
            if not removed_exact:
                # Fallback to id-based removal
                remove_item_from_inventory(source_inventory, swi[0], quantity=transfer_qty)

            # If source is manager_inventory and we removed by index, refresh store list
            if right_worker is None and removed_exact:
                store.manager_inventory = list(store.manager_inventory)
                renpy.store.manager_inventory = store.manager_inventory
            
            # Verify the removal worked
            if right_worker is None:
                # Double-check that the item was actually removed
                remaining_count = sum(item[1] for item in store.manager_inventory if _is_inv_entry(item) and len(item) >= 2 and item[0] == swi[0])
                renpy.log(f"transfer_to_left: After removal, {swi[0]} remaining in manager_inventory: {remaining_count}")
            renpy.log(f"Source after removal: {source_inventory}")
            renpy.log(f"Adding {swi[0]} (quantity: {transfer_qty}) to target: {target_inventory}")
            add_item_to_inventory(target_inventory, swi[0], quantity=transfer_qty)
            
            # Auto-consume on receive when item has auto_consume_on_receive and target is a worker
            try:
                if target_worker and item_info and (item_info.get("auto_consume_on_receive", False) or is_gift_to_worker):
                    for _ in range(int(transfer_qty)):
                        store.use_item(swi[0], target_worker)
            except Exception as e:
                renpy.log(f"auto_consume_on_receive error (to left): {e}")

            # CRITICAL: Force Ren'Py to recognize changes if target is manager_inventory
            if left_worker is None:
                # Also recreate target inventory to break references
                new_inv = []
                for item in store.manager_inventory:
                    if _is_inv_entry(item) and len(item) >= 2:
                        new_inv.append((str(item[0]), int(item[1]), bool(item[2] if len(item) > 2 else False)))
                    else:
                        new_inv.append(item)
                store.manager_inventory = new_inv
                renpy.store.manager_inventory = store.manager_inventory
            renpy.log(f"Target after addition: {target_inventory}")
            store.selected_description = ""
            if is_gift_to_worker and target_worker:
                renpy.notify(f"Gift delivered to {target_worker.get('name', 'worker')}")
            else:
                renpy.notify(f"Transferred {transfer_qty}x item to left")
            # Track tutorial objective 5 - potion transfer
            if item_info and hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item_info.get("name", "").lower().find("energy") != -1:
                store.potion_transferred = True
                renpy.log("DEBUG: Tutorial - Energy potion transferred to worker")
                check_objective_completion()
            renpy.restart_interaction()
            renpy.set_screen_variable("is_transferring", False)

    def get_item_sell_price(item_info):
        """Single source for shop sell pricing: 50% of buy price (shared by
        sell_item and the mass-sell plan builders below)."""
        return int((item_info or {}).get("price", 0) * 0.5)

    def sell_item(item_id, left_worker, quantity=None):
        # _price captured via default arg: screen-local defs can't see sibling
        # screen locals at call time (BIBLIA §10 / note above handle_inventory_row_click).
        multiplier = renpy.get_screen_variable("trade_multiplier")
        item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if item_info:
            sell_price = get_item_sell_price(item_info)  # 50% of buy price
            source_inventory = manager_inventory if left_worker is None else left_worker.get("inventory", [])
            # Find item in inventory to check available quantity
            item_entry = next((item for item in source_inventory if item[0] == item_id), None)
            available_qty = item_entry[1] if item_entry else 0
            # Calculate actual sell quantity (limited by available)
            actual_qty = min(multiplier if quantity is None else quantity, available_qty)
            if actual_qty > 0:
                store.money += sell_price * actual_qty
                remove_item_from_inventory(source_inventory, item_id, actual_qty)
                renpy.notify(f"Sold {actual_qty}x {item_info.get('name', 'Unknown')} for ${sell_price * actual_qty}")
            renpy.restart_interaction()

    def buy_item_from_shop(item_id):
        multiplier = renpy.get_screen_variable("trade_multiplier")
        item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
        if item_info:
            price = item_info.get("price", 0)
            consume_on_purchase = item_info.get("consume_on_purchase", False)
            purchase_effect = item_info.get("purchase_effect", "")
            # Consume-on-purchase: only buy 1 at a time and apply effect instead of adding to inventory
            if consume_on_purchase:
                actual_qty = min(1, store.money // price if price > 0 else 1)
            else:
                max_affordable = store.money // price if price > 0 else multiplier
                actual_qty = min(multiplier, max_affordable)
            if actual_qty > 0 and store.money >= price * actual_qty:
                store.money -= price * actual_qty
                if consume_on_purchase:
                    if purchase_effect == "manager_level_up":
                        for _ in range(actual_qty):
                            store.manager_level = getattr(store, "manager_level", 1) + 1
                        renpy.notify(f"Manager Level up! (consumed {actual_qty}x {item_info.get('name', 'Unknown')})")
                    elif purchase_effect == "add_money":
                        money_per_item = int(item_info.get("effect", {}).get("money", 0))
                        total_added = money_per_item * actual_qty
                        store.money += total_added
                        renpy.notify(f"+${total_added} (consumed {actual_qty}x {item_info.get('name', 'Unknown')})")
                    elif purchase_effect == "custom":
                        custom_effect = item_info.get("effect", {})
                        for _ in range(actual_qty):
                            apply_effects({"custom": custom_effect.get("custom")}, worker=None)
                        renpy.notify(f"Applied effect (consumed {actual_qty}x {item_info.get('name', 'Unknown')})")
                    else:
                        renpy.notify(f"Consumed {actual_qty}x {item_info.get('name', 'Unknown')}")
                else:
                    for _ in range(actual_qty):
                        add_item_to_inventory(manager_inventory, item_id)
                    renpy.notify(f"Bought {actual_qty}x {item_info.get('name', 'Unknown')} for ${price * actual_qty}")
                # Track tutorial objective 5 - potion purchase
                if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item_info.get("name", "").lower().find("energy") != -1:
                    store.potion_purchased = True
                    renpy.log("DEBUG: Tutorial - Energy potion purchased")
                    renpy.log(f"DEBUG: Tutorial - Item name: {item_info.get('name', 'Unknown')}")
                    renpy.log(f"DEBUG: Tutorial - tutorial_active: {store.tutorial_active}, current_objective: {store.current_objective}")
                    renpy.log(f"DEBUG: Tutorial - potion_purchased set to: {store.potion_purchased}")
                    check_objective_completion()
                else:
                    renpy.log(f"DEBUG: Tutorial - Purchase conditions not met: tutorial_active={hasattr(store, 'tutorial_active')}, current_objective={store.current_objective if hasattr(store, 'current_objective') else 'NOT_SET'}, item_name={item_info.get('name', 'Unknown')}")
            renpy.restart_interaction()

    def handle_inventory_row_click(row_scope, row_idx, item, item_info, is_shop_mode=False, can_transfer_right=True, can_transfer_left=True,
                                   left_worker=None, right_worker=None):
        def set_left_row_selection():
            renpy.set_screen_variable("selected_manager_item", item)
            renpy.set_screen_variable("selected_manager_index", row_idx)
            renpy.set_screen_variable("selected_worker_item", None)
            renpy.set_screen_variable("selected_worker_index", None)
            renpy.set_screen_variable("selected_description", item_info.get("description", ""))

        def clear_row_selection():
            renpy.set_screen_variable("selected_manager_item", None)
            renpy.set_screen_variable("selected_manager_index", None)
            renpy.set_screen_variable("selected_worker_item", None)
            renpy.set_screen_variable("selected_worker_index", None)
            renpy.set_screen_variable("selected_description", "")

        def set_right_worker_row_selection():
            renpy.set_screen_variable("selected_worker_item", item)
            renpy.set_screen_variable("selected_worker_index", row_idx)
            renpy.set_screen_variable("selected_manager_item", None)
            renpy.set_screen_variable("selected_manager_index", None)
            renpy.set_screen_variable("selected_description", item_info.get("description", ""))

        def set_right_shop_row_selection():
            renpy.set_screen_variable("selected_worker_item", item)
            renpy.set_screen_variable("selected_worker_index", None)
            renpy.set_screen_variable("selected_manager_item", None)
            renpy.set_screen_variable("selected_manager_index", None)
            renpy.set_screen_variable("selected_description", item_info.get("description", ""))

        now = __import__("time").time()
        item_id = item[0] if _is_inv_entry(item) and len(item) >= 1 else str(item)
        row_key = "{}:{}:{}".format(row_scope, row_idx, item_id)
        last_key = renpy.get_screen_variable("last_row_click_key")
        last_ts = renpy.get_screen_variable("last_row_click_ts")
        is_double = (last_key == row_key) and ((now - float(last_ts or 0.0)) <= 0.32)

        if row_scope == "left":
            current_idx = renpy.get_screen_variable("selected_manager_index")
            if is_double:
                set_left_row_selection()
                if not renpy.get_screen_variable("is_transferring"):
                    if is_shop_mode:
                        sell_item(item_id, left_worker)
                    elif can_transfer_right:
                        transfer_to_right(left_worker, right_worker)
                renpy.set_screen_variable("last_row_click_key", None)
                renpy.set_screen_variable("last_row_click_ts", 0.0)
                return
            if current_idx != row_idx:
                set_left_row_selection()

        elif row_scope == "right_worker":
            current_idx = renpy.get_screen_variable("selected_worker_index")
            if is_double:
                set_right_worker_row_selection()
                if can_transfer_left and (not renpy.get_screen_variable("is_transferring")):
                    transfer_to_left(left_worker, right_worker)
                renpy.set_screen_variable("last_row_click_key", None)
                renpy.set_screen_variable("last_row_click_ts", 0.0)
                return
            if current_idx != row_idx:
                set_right_worker_row_selection()

        elif row_scope == "right_shop":
            current_item = renpy.get_screen_variable("selected_worker_item")
            if is_double:
                set_right_shop_row_selection()
                if (not renpy.get_screen_variable("is_transferring")) and store.money >= item_info.get("price", 0):
                    buy_item_from_shop(item_id)
                renpy.set_screen_variable("last_row_click_key", None)
                renpy.set_screen_variable("last_row_click_ts", 0.0)
                return
            if current_item != item:
                set_right_shop_row_selection()

        renpy.set_screen_variable("last_row_click_key", row_key)
        renpy.set_screen_variable("last_row_click_ts", now)

    # All functions referenced by screen actions below are module-level and
    # pickle-resolvable. Keep the screen itself free of runtime defs/classes.


    def get_item_name_for_sort(idx_item):
        item = idx_item[1]
        item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
        return item_info.get("name", "ZZZ").lower()

    def get_item_price_for_sort(idx_item):
        item = idx_item[1]
        item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
        return int(item_info.get("price", 0))

    def item_matches_search(idx_item, search_text, category_filter=None):
        item = idx_item[1]
        item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
        if not item_content_is_visible(item_info): return False
        if category_filter is not None:
            if category_filter == "gifts":
                if item_info.get("type") != "gift": return False
            elif item_info.get("type") != category_filter and category_filter not in (item_info.get("extra_filter_categories") or []): return False
        return not search_text or search_text.lower() in item_info.get("name", "").lower()

    def _bulk_sellable(_item_id, _info):
        if (_info or {}).get("type") == "quest_item": return False
        _idl = str(_item_id).lower()
        return "test" not in _idl and "debug" not in _idl

    def _bulk_totals(_plan):
        return (sum(_p[1] for _p in _plan), sum(_p[1] * _p[2] for _p in _plan))

    def get_item_name_for_sort_right(idx_item):
        return get_item_name_for_sort(idx_item)

    def item_matches_search_right(idx_item, search_text, category_filter=None):
        return item_matches_search(idx_item, search_text, category_filter)
