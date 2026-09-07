# recruitment_functions.rpy
# Python functions for the recruitment system

init python:
    def select_weighted_specific_recruit(available_events, candidate_workers):
        """Select one eligible specific event by weight, then one matching worker."""
        identity_match = getattr(store, "_worker_matches_event_identity", None)
        has_identity_filter = getattr(store, "_event_has_identity_filters", None)
        if not callable(identity_match) or not callable(has_identity_filter):
            return (None, None)

        eligible = []
        for event in available_events or []:
            if event.get("random_worker", True) or not has_identity_filter(event):
                continue
            matching_workers = [
                worker
                for worker in (candidate_workers or [])
                if identity_match(worker, event)
            ]
            if not matching_workers:
                continue
            try:
                weight = max(0.0, float(event.get("weight", 1)))
            except (TypeError, ValueError):
                weight = 1.0
            eligible.append((event, matching_workers, weight))

        if not eligible:
            return (None, None)

        total_weight = sum(entry[2] for entry in eligible)
        if total_weight <= 0:
            selected_event, matching_workers, _weight = random.choice(eligible)
        else:
            roll = random.random() * total_weight
            selected_event, matching_workers, _weight = eligible[-1]
            current_weight = 0.0
            for event, workers, weight in eligible:
                current_weight += weight
                if roll < current_weight:
                    selected_event, matching_workers = event, workers
                    break

        return (random.choice(matching_workers), selected_event)

    def recruitment_context_is_visible(event, worker):
        """Revalidate serialized recruitment state against the current content policy."""
        if getattr(persistent, "nsfw_enabled", False):
            return True
        return bool(
            event_is_visible_for_content_filter(event)
            and event_worker_is_visible_for_content_filter(worker)
        )

    def clear_restricted_recruitment_context(reason="content_filter"):
        """Clear only transient recruitment state; roster/save entities remain untouched."""
        store.current_recruitment_event = None
        store.current_recruitment_worker = None
        store.in_recruitment = False
        renpy.log("RECRUITMENT: cleared transient context (%s)" % reason)

    def suspend_restricted_recruitment_context(event=None, worker=None, reason="content_filter"):
        """Preserve a blocked recruitment for reversible restoration when NSFW returns."""
        event = event or getattr(store, "current_recruitment_event", None)
        worker = worker or getattr(store, "current_recruitment_worker", None)
        if event:
            store._content_filter_suspended_recruitment_context = {
                "event": event,
                "worker": worker,
            }
        clear_restricted_recruitment_context(reason)

    def _recruitment_worker_already_hired(worker):
        """True when this recruitment context's worker is already on the roster."""
        name = worker.get("name") if hasattr(worker, "get") else None
        if not name:
            return False
        return any(
            hasattr(w, "get") and w.get("name") == name
            for w in (getattr(store, "workers", None) or [])
        )

    def purge_recruitment_transients(reason="stale_context"):
        """Unconditionally drop every serialized recruitment transient.

        Covers both the active slot (current_recruitment_event/worker,
        in_recruitment) and the label-scope leaks that python blocks in
        start_recruitment_system write into the store (selected_worker,
        specific_event), plus the content-filter suspension slot.
        """
        clear_restricted_recruitment_context(reason)
        for attr in (
            "selected_worker",
            "specific_event",
            "temp_recruitment_worker",
            "_content_filter_suspended_recruitment_context",
        ):
            if getattr(store, attr, None) is not None:
                setattr(store, attr, None)

    def clear_stale_recruitment_after_load(reason="after_load"):
        """Purge serialized recruitment context whose worker is already hired.

        Once a recruitment opens, the script stays parked on
        recruitment_choice_loop for the rest of the in-game day, so saves made
        later that day carry the finished recruitment in their roots forever.
        Loading such a save must not re-offer the hired worker, and the NSFW
        toggle must not be able to suspend-and-resurrect that context.
        Genuine mid-recruitment saves (worker not on the roster) are left
        untouched. Returns True when something stale was purged.
        """
        candidates = [
            getattr(store, "current_recruitment_worker", None),
            getattr(store, "selected_worker", None),
        ]
        suspended = getattr(store, "_content_filter_suspended_recruitment_context", None)
        if suspended and hasattr(suspended, "get"):
            candidates.append(suspended.get("worker"))
        if not any(
            candidate is not None and _recruitment_worker_already_hired(candidate)
            for candidate in candidates
        ):
            return False
        purge_recruitment_transients(reason)
        renpy.log("RECRUITMENT: purged stale post-load recruitment context (%s)" % reason)
        return True

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
    def get_recruitment_image(worker, outcome, event=None):
        """
        Resolve the best background / outcome image for a recruitment screen.

        Priority chain (mirrors get_event_image's trait-aware order):
          1. Event-level explicit override (full path, or shortname other than the
             generic placeholders "generic_success" / "generic_failure" / "event_bg").
          2a. Worker folder convention WITH trait prefix:
              <folder>/<trait>_recruit_success / _recruit_failure / _recruit.
          2b. Worker folder convention WITHOUT trait prefix.
          3a. Worker folder heuristic WITH trait prefix:
              <folder>/<trait>_charm / _charm_failure / _profile.
          3b. Worker folder heuristic WITHOUT trait prefix
              (excludes files that start with any trait prefix the worker doesn't have).
          4. The event's placeholder value, if it was a known default.
          5. Hardcoded generic placeholder for the outcome.
          6. event_bg as last resort.

        Trait prefixes are taken from get_trait_prefixes(worker) -- same priority
        order as daily events (Transformed > Magical > Futa > Pregnant, plus
        compound combinations).

        `outcome` should be "success", "failure", or anything else (background).
        Returns a renpy-loadable path (or "images/event_bg.png" if all fail).
        """
        event = event or {}
        if not recruitment_context_is_visible(event, worker):
            return "images/event_bg.png"
        DEFAULT_PLACEHOLDERS = {"generic_success", "generic_failure", "event_bg", None, ""}
        TRAIT_FILE_PREFIXES = ("pregnant_", "futa_", "transformed_", "magical_")

        if outcome == "success":
            event_key = event.get("success_image")
            convention_name = "recruit_success"
            heuristic_pattern = "charm"
            heuristic_failure_only = False
            generic_name = "generic_success"
        elif outcome == "failure":
            event_key = event.get("failure_image")
            convention_name = "recruit_failure"
            heuristic_pattern = "charm_failure"
            heuristic_failure_only = True
            generic_name = "generic_failure"
        else:
            event_key = event.get("background_image")
            convention_name = "recruit"
            heuristic_pattern = "profile"
            heuristic_failure_only = False
            generic_name = "event_bg"

        valid_exts = (".png", ".jpg", ".jpeg", ".webp", ".webm", ".mp4")

        def _resolve_shortname(name):
            if not name:
                return None
            if name.startswith("images/"):
                return name if renpy.loadable(name) else None
            lower = name.lower()
            has_ext = any(lower.endswith(e) for e in valid_exts)
            if has_ext:
                for prefix in ("images/events/", "images/"):
                    c = prefix + name
                    if renpy.loadable(c):
                        return c
                return None
            for ext in valid_exts:
                for prefix in ("images/events/", "images/"):
                    c = f"{prefix}{name}{ext}"
                    if renpy.loadable(c):
                        return c
            return None

        def _try_worker_basename(folder, basename):
            for ext in valid_exts:
                c = f"images/workers/{folder}/{basename}{ext}"
                if renpy.loadable(c):
                    return c
            return None

        def _pattern_match(base_folder, pattern):
            if heuristic_failure_only:
                return get_pattern_matches_flexible(base_folder, pattern)
            return get_pattern_matches_flexible(base_folder, pattern, exclude_failure=True)

        worker_folder = None
        if worker and hasattr(worker, "get"):
            worker_folder = worker.get("folder")

        worker_trait_prefixes = []
        if worker and hasattr(worker, "get"):
            try:
                worker_trait_prefixes = get_trait_prefixes(worker) or []
            except Exception as e:
                renpy.log(f"get_recruitment_image get_trait_prefixes failed: {e}")
                worker_trait_prefixes = []

        # 1. Explicit event override
        if event_key and event_key not in DEFAULT_PLACEHOLDERS:
            resolved = _resolve_shortname(event_key)
            if resolved:
                return resolved

        # 2a. Worker folder convention WITH trait prefix
        if worker_folder:
            for trait_prefix in worker_trait_prefixes:
                resolved = _try_worker_basename(worker_folder, f"{trait_prefix}_{convention_name}")
                if resolved:
                    return resolved

        # 2b. Worker folder convention WITHOUT trait prefix
        if worker_folder:
            resolved = _try_worker_basename(worker_folder, convention_name)
            if resolved:
                return resolved

        # 3a. Worker folder heuristic WITH trait prefix
        if worker_folder:
            base_folder = f"images/workers/{worker_folder}/"
            for trait_prefix in worker_trait_prefixes:
                try:
                    matches = _pattern_match(base_folder, f"{trait_prefix}_{heuristic_pattern}")
                    if matches:
                        return random.choice(matches)
                except Exception as e:
                    renpy.log(f"get_recruitment_image trait-prefixed heuristic failed: {e}")

        # 3b. Worker folder heuristic WITHOUT trait prefix (filter trait-prefixed files)
        if worker_folder:
            base_folder = f"images/workers/{worker_folder}/"
            try:
                matches = _pattern_match(base_folder, heuristic_pattern)
                if matches:
                    matches = [f for f in matches if not should_exclude_trait_file(f, TRAIT_FILE_PREFIXES, None)]
                if matches:
                    return random.choice(matches)
            except Exception as e:
                renpy.log(f"get_recruitment_image heuristic lookup failed: {e}")

        # 4. Event placeholder value (if it was a known default like generic_success)
        if event_key in DEFAULT_PLACEHOLDERS and event_key:
            resolved = _resolve_shortname(event_key)
            if resolved:
                return resolved

        # 5. Hardcoded generic placeholder for the outcome
        resolved = _resolve_shortname(generic_name)
        if resolved:
            return resolved

        # 6. event_bg fallback
        resolved = _resolve_shortname("event_bg")
        if resolved:
            return resolved

        return "images/event_bg.png"
    def get_filtered_recruit_workers(event, candidates=None):
        """
        Get recruitment workers filtered by event requirements (worker_filter).
        Pass `candidates` to filter an already-loaded pool instead of reloading.
        """
        available_workers = candidates if candidates is not None else load_recruit_workers()
        worker_filter = event.get("worker_filter", {}) or {}
        
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

    def process_recruitment_choice(choice_data, event, worker):
        """
        Process a recruitment event choice and return the outcome.
        """
        effect = choice_data.get("effect", {})
        condition = choice_data.get("condition")
        
        # Determine if this is a skill check or guaranteed outcome
        if condition and condition != "building_skill":
            # This is a skill check - we need a worker from our roster to perform it.
            # Eligibility uses the same trait-adjusted skill as the roll
            # (calculate_skill_with_traits), so workers whose skill comes only
            # from traits/equipment are not wrongly excluded.
            eligible_workers = []
            for roster_worker in store.workers:
                if worker_is_in_franchise(roster_worker):
                    continue
                try:
                    effective_skill = calculate_skill_with_traits(roster_worker, condition)
                except Exception:
                    effective_skill = roster_worker.get("skills", {}).get(condition, 0)
                if effective_skill > 0:
                    eligible_workers.append(roster_worker)

            if not eligible_workers:
                # No eligible workers - automatic failure
                try:
                    if condition not in skill_names:
                        renpy.log(f"WARNING: recruitment choice condition '{condition}' is not a known skill; no roster worker can pass it.")
                except Exception:
                    pass
                outcome_status = "failure"
                base_message = choice_data.get("message_failure", "No suitable worker available.")
                applied_values = apply_recruitment_effects(effect.get("failure", {}), worker)
            else:
                # Select the best worker for this skill (same trait-adjusted basis as the roll)
                selected_worker = max(eligible_workers, key=lambda w: calculate_skill_with_traits(w, condition))
                # Reuse the main engine's central skill-check info so recruitment
                # gets the same difficulty bonus and minimum-chance floor as daily
                # events (it also logs a WARNING for unknown skill conditions).
                check_info = get_event_worker_skill_check_info(selected_worker, choice_data)
                if check_info.get("valid"):
                    target_chance = check_info.get("target_chance", 0)
                    auto_success = check_info.get("auto_success", False)
                else:
                    target_chance = calculate_skill_with_traits(selected_worker, condition)
                    auto_success = False
                roll = random.randint(1, 100)

                if auto_success or roll <= target_chance:
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
                # Probability-based outcome: only the nested success/failure block
                # is applied (the wrapper's other keys are author-side defaults).
                # The difficulty floor (get_event_success_min_chance) is applied
                # for parity with the main engine's probability events
                # (see process_choice in script.rpy).
                effective_success_chance = max(get_event_success_min_chance(), success_chance)
                roll = random.random()
                if roll <= effective_success_chance:
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

        # Per-choice outcome override: lets decline/rejection choices display the
        # event's failure_image even though no skill check or probability ran.
        override = choice_data.get("outcome_override")
        if override in ("success", "failure"):
            outcome_status = override

        # Replace placeholders in the message
        worker_name = worker.get("name", "Unknown") if worker else "Unknown"
        outcome_message = base_message.replace("[event_worker]", worker_name)
        outcome_message = outcome_message.replace("[acting_worker]", selected_worker.get("name", "Manager") if 'selected_worker' in locals() else "Manager")
        # Replace player placeholders (parity with the main event engine)
        outcome_message = outcome_message.replace("[player_title]", str(player_title)).replace("[player_name]", str(player_name))

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
            target_building, resolved_building_name = _resolve_building_by_name(target_building_name)
            
            if target_building is not None:
                old_rep = int(target_building.get("reputation", 0) or 0)
                new_rep = old_rep + rep_change
                # Cap reputation between 0 and 1000
                target_building["reputation"] = max(0, min(new_rep, 1000))
                applied_values["actual_reputation"] = target_building["reputation"] - old_rep
                custom_names = getattr(store, "custom_names", {}) or {}
                applied_values["reputation_building"] = custom_names.get(
                    resolved_building_name,
                    resolved_building_name or target_building_name,
                )
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

        # Apply joy to the worker when present (recruit events use joy like
        # daily events; mirrors apply_effects in script.rpy)
        if "joy" in effect_dict:
            joy_change = effect_dict["joy"]
            if joy_change != 0 and worker and hasattr(store, "apply_attribute_change"):
                store.apply_attribute_change(worker, "joy", joy_change)
                applied_values["actual_joy"] = joy_change

        # Handle worker recruitment
        if effect_dict.get("recruit_worker", False) and worker:
            if worker.get("monster", False):
                renpy.log(f"Blocked recruitment-event path for monster worker: {worker.get('name', 'Unknown')}")
                applied_values["recruitment_blocked"] = True
                return applied_values
            # Duplicate guard: a stale serialized context (or any path that skips
            # the roster filter in load_recruit_workers) must never add a second
            # copy of an already-rostered worker. Mirrors the simple-flow check.
            _rec_name = worker.get("name", "")
            if _rec_name and any(
                hasattr(w, "get") and w.get("name") == _rec_name for w in (getattr(store, "workers", []) or [])
            ):
                renpy.log(f"Blocked duplicate recruitment of already-rostered worker: {_rec_name}")
                applied_values["recruitment_blocked"] = True
                applied_values["duplicate_worker"] = True
                return applied_values
            # Apply cost modifier if present.
            # Legacy event data often uses 0 as "no modifier", so normalize
            # non-positive values to 1.0 instead of treating them as discounts.
            _raw_cost_modifier = effect_dict.get("cost_modifier", 1.0)
            try:
                cost_modifier = float(_raw_cost_modifier)
            except (TypeError, ValueError):
                cost_modifier = 1.0
            if cost_modifier <= 0:
                cost_modifier = 1.0

            desired_comfort = get_effective_comfort_desired(worker)
            # If price was negotiated down, comfort should be exactly one point below desired (min 1)
            if cost_modifier < 1.0:
                negotiated_comfort = max(1, int(desired_comfort) - 1)
            else:
                negotiated_comfort = int(desired_comfort)
            worker["comfort_level"] = negotiated_comfort

            # Canon rule: worker daily cost is comfort x difficulty rate.
            _cm = get_difficulty_comfort_mult()
            final_cost = int(max(1, negotiated_comfort) * _cm)
            worker["daily_cost"] = final_cost
            
            # Apply relationship bonus if present (relative to comfort)
            if "relationship_bonus" in effect_dict:
                worker["relationship"] = max(10, 10 + worker.get("comfort_level", negotiated_comfort) + effect_dict["relationship_bonus"])
            
            # Add the worker to the roster using recruit_worker for proper tutorial tracking
            ensure_worker_defaults(worker)
            worker["is_servant"] = False
            if not store.recruit_worker(worker):
                renpy.log(f"Recruitment blocked for {worker.get('name', 'Unknown')}; skipping recruit effects")
                applied_values["recruitment_blocked"] = True
                return applied_values
            
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