# recruitment_functions.rpy
# Python functions for the recruitment system

init python:
    def sanitize_text(text):
        """Normalize curly quotes and dashes to ASCII to avoid font fallback boxes."""
        if not text:
            return text
        replacements = {
            "—": "-", "–": "-", "‑": "-", "−": "-",
            "“": '"', "”": '"', "’": "'", "‚": ",", "…": "..."
        }
        sanitized = text
        for bad, good in replacements.items():
            sanitized = sanitized.replace(bad, good)
        return sanitized
    def format_recruitment_message(message_text, applied_values):
        """Replace placeholders like [actual_comfort] with applied values in recruitment messages."""
        try:
            if not message_text:
                return ""
            if not applied_values:
                return message_text
            formatted = message_text
            for key, value in applied_values.items():
                placeholder = f"[{key}]"
                formatted = formatted.replace(placeholder, str(value))
            return formatted
        except Exception as e:
            renpy.log(f"format_dynamic_message error: {e}")
            return message_text

    def launch_recruitment_via_label():
        """
        Deprecated: Recruitment is now launched via Ren'Py `Jump("start_recruitment_system")`
        directly from UI actions to avoid stacking contexts (call_in_new_context), which was
        a major source of post-load frozen/black screens after recruitment.
        Kept for compatibility if any old screen still calls it.
        """
        try:
            renpy.jump("start_recruitment_system")
        except Exception as e:
            renpy.log(f"launch_recruitment_via_label error: {e}")
    def get_filtered_recruit_workers(event):
        """
        Get recruitment workers filtered by event requirements.
        """
        available_workers = load_recruit_workers()
        worker_filter = event.get("worker_filter", {})
        
        if not worker_filter:
            return available_workers
        
        filtered_workers = []
        for worker in available_workers:
            # Check minimum skill requirements
            if "min_combat" in worker_filter:
                if worker.get("skills", {}).get("Combat", 0) < worker_filter["min_combat"]:
                    continue
            if "min_charm" in worker_filter:
                if worker.get("skills", {}).get("Charm", 0) < worker_filter["min_charm"]:
                    continue
            if "min_clever" in worker_filter:
                if worker.get("skills", {}).get("Clever", 0) < worker_filter["min_clever"]:
                    continue
            if "min_craft" in worker_filter:
                if worker.get("skills", {}).get("Craft", 0) < worker_filter["min_craft"]:
                    continue
            
            # Check required traits
            if "traits_required" in worker_filter:
                worker_traits = set(worker.get("traits", []))
                required_traits = set(worker_filter["traits_required"])
                if not required_traits.issubset(worker_traits):
                    continue
            
            # Check excluded traits
            if "traits_excluded" in worker_filter:
                worker_traits = set(worker.get("traits", []))
                excluded_traits = set(worker_filter["traits_excluded"])
                if worker_traits.intersection(excluded_traits):
                    continue
            
            filtered_workers.append(worker)
        
        return filtered_workers

    def prepare_recruitment_worker(event, worker):
        """
        Prepare a worker for recruitment, calculating costs based on their desired_comfort.
        """
        if worker is None:
            # Generate a new worker if needed
            if event.get("random_worker", False):
                worker = spawn_new_worker()
                worker["is_servant"] = False
                worker["encounter_only"] = True
                worker["monster"] = False
                worker["unique"] = False
                ensure_worker_defaults(worker)
            else:
                return None
        
        # Make a copy to avoid modifying the original
        prepared_worker = worker.copy()
        
        # Use the worker's desired_comfort or fall back to comfort_range
        comfort_desired = get_effective_comfort_desired(prepared_worker)
        comfort_range = event.get("comfort_range", {"min": comfort_desired, "max": comfort_desired})
        
        # Set comfort level based on desired comfort or range
        if "comfort_range" in event:
            comfort_min = comfort_range.get("min", comfort_desired)
            comfort_max = comfort_range.get("max", comfort_desired)
            comfort_level = random.randint(comfort_min, comfort_max)
        else:
            comfort_level = comfort_desired
        
        prepared_worker["comfort_level"] = comfort_level
        
        # Calculate daily cost based on comfort level and current difficulty
        base_cost = comfort_level * get_difficulty_comfort_mult()
        prepared_worker["daily_cost"] = base_cost
        
        return prepared_worker

    def start_recruitment_event_legacy(event, worker):
        """
        Start a legacy format recruitment event using proper Ren'Py flow.
        """
        # Store event and worker data globally for the event system
        store.current_recruitment_event = event
        store.current_recruitment_worker = worker
        
        # Use the simple recruitment label for legacy events
        renpy.call("recruitment_event_simple", event, worker)

    def start_recruitment_event_advanced(event, worker):
        """
        Start an advanced format recruitment event using proper Ren'Py flow.
        """
        # Store event and worker data globally for the event system
        store.current_recruitment_event = event
        store.current_recruitment_worker = worker
        
        # Use the new Ren'Py label for proper dialogue and choice handling
        renpy.call("recruitment_event_flow", event, worker)

    def process_recruitment_choice(choice_data, event, worker):
        """
        Process a recruitment event choice and return the outcome.
        """
        effect = choice_data.get("effect", {})
        condition = choice_data.get("condition")
        
        # Determine if this is a skill check or guaranteed outcome
        if condition and condition != "building_skill":
            # This is a skill check - we need a worker from our roster to perform it
            eligible_workers = []
            for roster_worker in store.workers:
                if roster_worker.get("skills", {}).get(condition, 0) > 0:
                    eligible_workers.append(roster_worker)
            
            if not eligible_workers:
                # No eligible workers - automatic failure
                outcome_status = "failure"
                base_message = choice_data.get("message_failure", "No suitable worker available.")
                applied_values = apply_recruitment_effects(effect.get("failure", {}), worker)
            else:
                # Select the best worker for this skill
                selected_worker = max(eligible_workers, key=lambda w: w.get("skills", {}).get(condition, 0))
                skill_level = calculate_skill_with_traits(selected_worker, condition)
                roll = random.randint(1, 100)
                
                if roll <= skill_level:
                    outcome_status = "success"
                    base_message = choice_data.get("message_success", "The arrangement succeeds; terms are met and the day moves forward.")
                    applied_values = apply_recruitment_effects(effect.get("success", {}), worker)
                else:
                    outcome_status = "failure"
                    base_message = choice_data.get("message_failure", "The opportunity slips away; nothing more comes of it.")
                    applied_values = apply_recruitment_effects(effect.get("failure", {}), worker)
        else:
            # No skill check - check for success_chance probability
            success_chance = effect.get("success_chance")
            # If success_chance present AND effect has success/failure branches → probability-based
            # If success_chance is 0 or effect has no success/failure → guaranteed (apply main effect)
            if success_chance is not None and ("success" in effect or "failure" in effect):
                # Probability-based outcome
                roll = random.random()
                if roll <= success_chance:
                    outcome_status = "success"
                    base_message = choice_data.get("message_success", "The arrangement succeeds; terms are met and the day moves forward.")
                    applied_values = apply_recruitment_effects(effect.get("success", {}), worker)
                else:
                    outcome_status = "failure"
                    base_message = choice_data.get("message_failure", "The opportunity slips away; nothing more comes of it.")
                    applied_values = apply_recruitment_effects(effect.get("failure", {}), worker)
            else:
                # Guaranteed outcome (no success/failure branches, or success_chance omitted)
                outcome_status = "success"
                base_message = choice_data.get("message", "Done.")
                applied_values = apply_recruitment_effects(effect, worker)
        
        # Replace placeholders in the message
        worker_name = worker.get("name", "Unknown") if worker else "Unknown"
        outcome_message = base_message.replace("[event_worker]", worker_name)
        outcome_message = outcome_message.replace("[acting_worker]", selected_worker.get("name", "Manager") if 'selected_worker' in locals() else "Manager")

        # Apply dynamic message formatting for any remaining placeholders
        # Use the main format_dynamic_message from script.rpy for {actual_money} processing
        outcome_message = format_dynamic_message(outcome_message, applied_values)
        
        # Debug log to track message processing
        renpy.log(f"RECRUITMENT MESSAGE DEBUG: After format_dynamic_message: {outcome_message}")

        # First, resolve explicit [COST] if present so currency injection can see the number
        final_cost = 0
        try:
            final_cost = int(applied_values.get("actual_cost", worker.get("daily_cost", 0) if worker else 0))
        except Exception:
            final_cost = worker.get("daily_cost", 0) if worker else 0
        if "[COST]" in outcome_message:
            outcome_message = outcome_message.replace("[COST]", f"${final_cost}")

        # Fallback replacements to cover any missed placeholders
        final_comfort = applied_values.get("actual_comfort", worker.get("comfort_level", 1) if worker else 1)
        
        fallback_map = {
            "[actual_cost]": f"${final_cost}/day",
            "[actual_comfort]": f"{final_comfort}",
            # Removed [actual_money] fallback since no messages use it and it might cause conflicts
            "[actual_reputation]": str(applied_values.get("actual_reputation", "0")),
        }
        for ph, val in fallback_map.items():
            outcome_message = outcome_message.replace(ph, val)
        
        # Handle attribute placeholders (e.g., [attr_rebelliousness])
        for key, value in applied_values.items():
            if key.startswith("attr_"):
                attr_name = key.replace("attr_", "")
                # Capitalize first letter for display
                attr_display = attr_name.capitalize()
                outcome_message = outcome_message.replace(f"[attr_{attr_name}]", f"{attr_display} +{value}")

        # Reduce redundancy and ensure currency formatting inside the message
        try:
            import re
            # Only inject currency if there's no $ symbol already in the message
            if "per day" in outcome_message.lower() and "$" not in outcome_message:
                def _inject_cost(m):
                    return f"{m.group(1)} ${final_cost} {m.group(2)}"
                outcome_message = re.sub(r"(at|for)\s*[-+]?\d+\s*(per day)", _inject_cost, outcome_message, flags=re.I)
                outcome_message = re.sub(r"\b\d+\s*per day", f"${final_cost} per day", outcome_message, flags=re.I)
            # Collapse '(X comfort)' -> '(X)'
            outcome_message = re.sub(r"\((\s*\d+)\s*comfort\)", r"(\1)", outcome_message, flags=re.I)
        except Exception:
            pass

        # Final sanitization for any typographic characters that the font can't render
        outcome_message = sanitize_text(outcome_message)
        
        # Debug log to track final message
        renpy.log(f"RECRUITMENT MESSAGE DEBUG: Final message: {outcome_message}")

        # No generic summary: event texts should remain thematic and handle any confirmation inline.

        # Mark event as completed if it's limited
        if not event.get("unlimited", True):
            event_id = event.get("id")
            if event_id:
                store.event_occurrences[event_id] = store.event_occurrences.get(event_id, 0) + 1
                store.event_last_occurred[event_id] = calculate_total_days()

        return {"message": outcome_message, "outcome": outcome_status}

    def apply_recruitment_effects(effect_dict, worker):
        """
        Apply recruitment event effects and return applied values for message formatting.
        """
        applied_values = {}
        
        if not effect_dict:
            return applied_values
        
        # Handle money effects
        if "money" in effect_dict:
            money_change = int(effect_dict["money"])
            store.money += money_change
            applied_values["actual_money"] = money_change
        
        # Handle reputation effects (apply to Building 1 as default for recruitment events)
        # Note: Reputation changes from recruitment are minimal since reputation should come from worker performance
        if "reputation" in effect_dict:
            rep_change = int(effect_dict["reputation"])
            # For recruitment events, apply to Building 1 (main building) as default
            target_building_name = "Building 1"
            target_building = available_buildings.get(target_building_name)
            
            if target_building is not None:
                new_rep = target_building.get("reputation", 0) + rep_change
                # Cap reputation between 0 and 1000
                target_building["reputation"] = max(0, min(new_rep, 1000))
                applied_values["actual_reputation"] = rep_change
                applied_values["reputation_building"] = store.custom_names.get(target_building_name, target_building_name)
            else:
                renpy.log("Recruitment: Building 1 not found; skipping reputation effect.")
        
        # Handle health effects (prefer applying to the worker)
        if "health" in effect_dict:
            health_change = int(effect_dict["health"])
            if worker is not None:
                worker["health"] = max(0, worker.get("health", 100) + health_change)
            elif hasattr(store, "health"):
                store.health += health_change
            else:
                renpy.log("Recruitment: No health target available; skipping health effect.")
            applied_values["actual_health"] = abs(health_change)
        
        # Handle worker recruitment
        if effect_dict.get("recruit_worker", False) and worker:
            # Apply cost modifier if present
            cost_modifier = effect_dict.get("cost_modifier", 1.0)

            desired_comfort = get_effective_comfort_desired(worker)
            # If price was negotiated down, comfort should be exactly one point below desired (min 1)
            if cost_modifier < 1.0:
                negotiated_comfort = max(1, int(desired_comfort) - 1)
            else:
                negotiated_comfort = int(desired_comfort)
            worker["comfort_level"] = negotiated_comfort

            # Compute cost with a safety floor tied to comfort (use game economy: difficulty mult x comfort)
            _cm = get_difficulty_comfort_mult()
            original_daily_cost = worker.get("daily_cost", negotiated_comfort * _cm)
            final_cost_raw = int(original_daily_cost * cost_modifier)
            min_cost = max(_cm, negotiated_comfort * _cm)
            final_cost = max(min_cost, final_cost_raw)
            worker["daily_cost"] = final_cost
            
            # Apply relationship bonus if present (relative to comfort)
            if "relationship_bonus" in effect_dict:
                worker["relationship"] = max(10, 10 + worker.get("comfort_level", negotiated_comfort) + effect_dict["relationship_bonus"])
            
            # Add the worker to the roster using recruit_worker for proper tutorial tracking
            ensure_worker_defaults(worker)
            worker["is_servant"] = False
            store.recruit_worker(worker)
            
            # Apply attribute changes after recruitment (so they affect the recruited worker)
            if "add_attribute" in effect_dict:
                attr_info = effect_dict["add_attribute"]
                target = attr_info.get("target", "recruited_worker")
                
                if target == "recruited_worker" and worker:
                    for attr_name, attr_value in attr_info.items():
                        if attr_name != "target" and isinstance(attr_value, (int, float)):
                            current_value = worker.get(attr_name, 0)
                            worker[attr_name] = max(0, min(100, current_value + int(attr_value)))
                            # Store attribute changes for message formatting
                            applied_values[f"attr_{attr_name}"] = int(attr_value)
                            renpy.log(f"Applied {attr_name} change: {int(attr_value)} to {worker.get('name', 'Unknown')}")
            
            applied_values["actual_cost"] = f"{final_cost}"
            applied_values["actual_comfort"] = negotiated_comfort
            applied_values["comfort_desired"] = int(desired_comfort)
            applied_values["was_discount"] = cost_modifier < 1.0
            renpy.notify(f"{worker['name']} has been recruited!")
            renpy.log(f"Worker recruited: {worker['name']} at ${final_cost}/day")
        
        # Handle trait additions
        if "add_trait" in effect_dict:
            trait_info = effect_dict["add_trait"]
            target = trait_info.get("target", "recruited_worker")
            
            if target == "recruited_worker" and worker:
                trait_name = trait_info.get("name")
                duration = trait_info.get("duration", -1)  # -1 for permanent
                
                if trait_name:
                    # Use add_trait_with_duration to ensure no duplicates and proper conflict handling
                    # Convert -1 (permanent) to 0 (no duration) for the function
                    trait_duration = 0 if duration == -1 else duration
                    add_trait_with_duration(worker, trait_name, trait_duration)
                    
                    # Handle temporary traits with duration (for tracking purposes)
                    if duration > 0:
                        if "temporary_traits" not in worker:
                            worker["temporary_traits"] = {}
                        worker["temporary_traits"][trait_name] = duration
        
        # Handle custom effects
        if "custom" in effect_dict:
            custom_effect = effect_dict["custom"]
            if custom_effect == "give_item":
                # Add a specific item to the manager inventory
                item_id = effect_dict.get("item_id")
                if item_id:
                    add_item_to_inventory(manager_inventory, item_id)
                    # Get item name for notification
                    try:
                        item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
                        item_name = item_data.get("display_name", item_id.replace("_", " ").title()) if item_data else item_id.replace("_", " ").title()
                    except:
                        item_name = item_id.replace("_", " ").title()
                    renpy.notify(f"Received {item_name}!")
                    renpy.log(f"Recruitment custom give_item: added {item_id} to inventory")
                else:
                    renpy.log("Recruitment custom give_item: missing item_id")
        
        return applied_values

    def process_advanced_recruitment_choice(choice_data, event, worker):
        """
        Process an advanced recruitment choice and show the result using standard dialogue box.
        """
        try:
            # Process the choice
            outcome_details = process_recruitment_choice(choice_data, event, worker)
            outcome_message = outcome_details.get("message", "Something happened.")
            outcome_status = outcome_details.get("outcome", "success")
            
            # Hide the current screen
            renpy.hide_screen("advanced_recruitment_event_screen")
            
            # Show result using unified screen (like interactions)
            renpy.call_screen("recruitment_outcome", message=outcome_message, event=event, outcome=outcome_status)
            
        except Exception as e:
            renpy.log(f"Error processing advanced recruitment choice: {e}")
            renpy.hide_screen("advanced_recruitment_event_screen")
            renpy.show_screen("error_popup", message="Choice processing error")