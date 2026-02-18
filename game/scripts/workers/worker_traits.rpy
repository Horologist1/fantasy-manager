init python:
    import random
    import renpy.store as store
    import json

    def load_traits():
        """Load traits from the traits.json file."""
        try:
            with renpy.file("data/traits.json") as f:
                traits = json.load(f)
            # Filter traits based on NSFW setting
            filtered_traits = [trait for trait in traits if persistent.nsfw_enabled or not trait.get("nsfw", False)]
            return filtered_traits
        except Exception as e:
            renpy.log("Error loading traits.json: " + str(e))
            return []

    traits_list = load_traits()

    def get_trait_desc(trait_name):
        """Get the description of a trait by name."""
        for t in traits_list:
            if t["name"] == trait_name:
                return t.get("description", "No description available")
        return "No description available"

    def can_assign_trait_to_worker(trait, worker):
        """Check if a trait can be assigned to a worker based on gender restrictions."""
        gender_restriction = trait.get("gender_restriction", None)
        if gender_restriction:
            worker_gender = worker.get("gender", "")
            if worker_gender != gender_restriction:
                return False
        return True

    def add_trait_with_duration(worker, trait_name, duration, is_variant=False):
        """
        Add a trait to the worker with an optional duration.
        If the trait has conflicts, remove conflicting traits.
        """
        # Return early if worker is None to prevent NoneType errors
        if worker is None:
            renpy.log(f"Cannot add trait '{trait_name}' - worker parameter is None")
            return
            
        # Find the trait definition
        trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
        if not trait_def:
            renpy.log(f"Cannot add trait '{trait_name}' - trait not found in traits_list")
            return

        # Check gender restrictions
        if not can_assign_trait_to_worker(trait_def, worker):
            renpy.log(f"Cannot add trait '{trait_name}' to {worker.get('name', 'Unknown')} - gender restriction not met")
            return
            
        if "traits" not in worker:
            worker["traits"] = []

        # Remove conflicting traits
        for trait in traits_list:
            if trait["name"] == trait_name:
                for conflict in trait.get("conflicts", []):
                    if conflict in worker["traits"]:
                        remove_trait_safe(worker, conflict)

        if trait_name not in worker["traits"]:
            worker["traits"].append(trait_name)

        if duration > 0:
            if "trait_durations" not in worker:
                worker["trait_durations"] = {}
            worker["trait_durations"][trait_name] = duration

        # Recalculate trait modifiers
        recalculate_trait_modifiers(worker)

    def remove_trait(worker, trait_name):
        """Remove a trait from the worker."""
        if not worker:
            renpy.log(f"remove_trait: Worker is None, cannot remove trait '{trait_name}'")
            return
        if not trait_name:
            renpy.log(f"remove_trait: Trait name is empty, cannot remove from worker '{worker.get('name', 'Unknown')}'")
            return
        
        worker_traits = worker.get("traits", [])
        if trait_name in worker_traits:
            worker["traits"].remove(trait_name)
            renpy.log(f"Removed trait '{trait_name}' from worker '{worker.get('name', 'Unknown')}'. Remaining traits: {len(worker['traits'])}")
            
            # Remove duration if it exists
            if "trait_durations" in worker and trait_name in worker["trait_durations"]:
                del worker["trait_durations"][trait_name]
            
            # Recalculate trait modifiers
            recalculate_trait_modifiers(worker)
        else:
            renpy.log(f"Trait '{trait_name}' not found in worker '{worker.get('name', 'Unknown')}' traits: {worker_traits}")

    def remove_trait_safe(worker, trait_name):
        """Remove a trait with case-insensitive cleanup of durations."""
        if not worker or not trait_name:
            return
        remove_trait(worker, trait_name)
        removed_any = False
        worker_traits = worker.get("traits", [])
        for existing in list(worker_traits):
            if isinstance(existing, str) and existing.lower() == str(trait_name).lower():
                worker_traits.remove(existing)
                removed_any = True
        if "trait_durations" in worker:
            for key in list(worker["trait_durations"].keys()):
                if isinstance(key, str) and key.lower() == str(trait_name).lower():
                    del worker["trait_durations"][key]
                    removed_any = True
        if removed_any:
            recalculate_trait_modifiers(worker)

    def apply_trait_secondary_modifiers_once(worker):
        """
        Apply trait modifiers to secondary attributes ONLY ONCE when traits are first assigned.
        This function should only be called when traits are added/removed, not on every access.
        """
        # ✅ CRÍTICO: Solo aplicar si no se han aplicado antes
        if worker.get("_secondary_attributes_initialized", False):
            renpy.log(f"Secondary attributes already initialized for {worker.get('name', 'Unknown')}, skipping recalculation")
            return
        
        # Calculate base values only if attributes don't exist yet
        if "joy" not in worker:
            worker["joy"] = random.randint(20, 80)
        if "rebelliousness" not in worker:
            worker["rebelliousness"] = 50
        if "romance" not in worker:
            worker["romance"] = 0
        if "comfort_level" not in worker:
            worker["comfort_level"] = 1
        if "comfort_desired" not in worker:
            worker["comfort_desired"] = worker.get("comfort_desired", 1)  # Initialize from JSON or default to 1
        if "relationship" not in worker:
            worker["relationship"] = 10 + worker.get("comfort_level", 1)
        if "libido" not in worker:
            worker["libido"] = 10
        
        # Calculate total modifiers from all traits
        total_modifiers = {
            "joy": 0,
            "rebelliousness": 0,
            "romance": 0,
            "comfort_level": 0,
            "comfort_desired": 0,
            "relationship": 0,
            "libido": 0
        }
        
        # Apply trait modifiers
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "modifiers" in trait_def:
                modifiers = trait_def["modifiers"]
                for attr in total_modifiers:
                    if attr in modifiers:
                        total_modifiers[attr] += modifiers[attr]
        
        # Apply modifiers to current values (not base values)
        for attr, modifier in total_modifiers.items():
            if modifier != 0:
                current_value = worker.get(attr, 0)
                new_value = current_value + modifier
                set_attribute_with_caps(worker, attr, new_value)
        
        # Mark as initialized to prevent future recalculations
        worker["_secondary_attributes_initialized"] = True
        renpy.log(f"Secondary attributes initialized for {worker.get('name', 'Unknown')}")

    def apply_trait_secondary_modifiers(worker):
        """Apply secondary attribute modifiers from traits (joy, rebelliousness, etc.)."""
        # This is just an alias for the _once version for compatibility
        apply_trait_secondary_modifiers_once(worker)

    def recalculate_trait_modifiers(worker):
        """
        Recalculate trait modifiers when traits are added or removed.
        This resets the initialization flag and recalculates from current values.
        """
        # Reset initialization flag to allow recalculation
        if "_secondary_attributes_initialized" in worker:
            del worker["_secondary_attributes_initialized"]
        
        # Reapply modifiers
        apply_trait_secondary_modifiers_once(worker)

    def get_attribute_cap(worker, attribute):
        """Get the cap for an attribute based on worker's traits and management skills."""
        cap = None
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "attribute_caps" in trait_def and attribute in trait_def["attribute_caps"]:
                trait_cap = trait_def["attribute_caps"][attribute]
                if cap is None or trait_cap < cap:  # Use the most restrictive cap
                    cap = trait_cap
        # Default cap for rebelliousness if no trait defines it
        if attribute == "rebelliousness" and cap is None:
            cap = 100
        # Management skill: Servant Training reduces max Rebelliousness by 10 per point
        if attribute == "rebelliousness":
            mgmt = getattr(store, "management_skills", None) or {}
            cap = max(0, (cap or 100) - 10 * mgmt.get("servant_training", 0))
        return cap

    def get_attribute_minimum(worker, attribute):
        """Get the minimum for an attribute based on worker's traits."""
        minimum = None
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "attribute_minimums" in trait_def and attribute in trait_def["attribute_minimums"]:
                trait_min = trait_def["attribute_minimums"][attribute]
                if minimum is None or trait_min > minimum:  # Use the highest minimum
                    minimum = trait_min
        return minimum

    def set_attribute_with_caps(worker, attribute, value):
        """Set an attribute value while respecting caps and minimums from traits."""
        # Apply trait-based caps
        cap = get_attribute_cap(worker, attribute)
        
        # Apply default caps if no trait cap is defined
        if cap is None:
            if attribute == "joy":
                cap = 100
            elif attribute == "rebelliousness":
                cap = 100
            elif attribute == "romance":
                cap = 100
            elif attribute == "relationship":
                cap = 100
        
        if cap is not None and value > cap:
            value = cap
            if get_attribute_cap(worker, attribute) is not None:
                renpy.log(f"Capped {attribute} at {cap} for {worker.get('name', 'Unknown')} due to trait restrictions")
            else:
                renpy.log(f"Capped {attribute} at {cap} for {worker.get('name', 'Unknown')} (default maximum)")
        
        # Apply trait-based minimums
        minimum = get_attribute_minimum(worker, attribute)
        
        # Handle special case for libido overflow before applying minimums
        # NOTE: "Overflow" here means libido going BELOW 0 (negative), not excess over max (e.g. 35/20).
        if attribute == "libido" and value < 0:
            if persistent.nsfw_enabled:
                # Handle overflow: add abs(negative value) to rebelliousness and reset libido to minimum or 0
                overflow_amount = abs(value)
                current_rebelliousness = worker.get("rebelliousness", 50)
                new_rebelliousness = current_rebelliousness + overflow_amount
                worker["rebelliousness"] = min(100, new_rebelliousness)  # Cap at 100
                worker["libido"] = minimum if minimum is not None else 0
                renpy.log(f"Libido overflow for {worker.get('name', 'Unknown')}: +{overflow_amount} rebelliousness, libido set to {worker['libido']}")
                return  # Don't continue with normal processing
            else:
                value = 0
        
        # Apply general minimum values (including trait minimums)
        if attribute == "joy" and value < 0:
            value = 0
        elif attribute == "rebelliousness" and value < 0:
            value = 0
        elif attribute == "relationship" and value < 0:
            value = 0
        elif attribute == "romance" and value < 0:
            value = 0
        elif attribute == "libido" and value < 0:
            value = 0
        
        # Apply trait minimums (overrides general minimums)
        if minimum is not None and value < minimum:
            value = minimum
            renpy.log(f"Applied minimum {attribute} of {minimum} for {worker.get('name', 'Unknown')} due to trait restrictions")

        # Dynamic maximum for libido based on traits/items
        if attribute == "libido":
            try:
                max_lib = get_max_libido(worker)
                if value > max_lib:
                    value = max_lib
                    renpy.log(f"Clamped libido to dynamic max {max_lib} for {worker.get('name', 'Unknown')}")
            except Exception:
                pass
            
        worker[attribute] = value

    def apply_attribute_change(worker, attribute, change):
        """Apply a change to an attribute while respecting caps."""
        current_value = worker.get(attribute, 0)
        new_value = current_value + change
        set_attribute_with_caps(worker, attribute, new_value)

    def deduplicate_traits(worker):
        """
        Remove duplicate traits from a worker's traits list.
        Preserves the order of first occurrence.
        """
        if "traits" not in worker or not worker["traits"]:
            return
        
        seen = set()
        deduplicated = []
        for trait_name in worker["traits"]:
            if trait_name not in seen:
                seen.add(trait_name)
                deduplicated.append(trait_name)
        
        if len(deduplicated) != len(worker["traits"]):
            removed_count = len(worker["traits"]) - len(deduplicated)
            renpy.log(f"Removed {removed_count} duplicate trait(s) from {worker.get('name', 'Unknown')}")
            worker["traits"] = deduplicated
            # Recalculate modifiers after deduplication
            recalculate_trait_modifiers(worker)

    def ensure_minimum_traits(worker, min_traits=3, max_traits=5):
        """Ensure worker has minimum number of traits, adding random ones if needed."""
        if not worker.get("traits"):
            worker["traits"] = []
        
        current_count = len(worker["traits"])
        if current_count >= min_traits:
            return  # Already has enough traits
        
        target_count = random.randint(min_traits, max_traits)
        traits_to_add = target_count - current_count
        
        renpy.log(f"Adding {traits_to_add} traits to {worker.get('name', 'Unknown')} (current: {current_count}, target: {target_count})")
        
        # Get possible traits (excluding only_assigned and respecting NSFW settings)
        possible_traits = [
            t for t in traits_list
            if not t.get("only_assigned", False) 
            and (persistent.nsfw_enabled or not t.get("nsfw", False))
            and t["name"] not in worker["traits"]  # Don't add traits they already have
        ]
        
        random.shuffle(possible_traits)
        
        added_count = 0
        attempts = 0
        max_attempts = 100
        
        while added_count < traits_to_add and attempts < max_attempts:
            attempts += 1
            trait = random.choice(possible_traits)
            trait_name = trait["name"]
            
            # Check gender restriction
            if not can_assign_trait_to_worker(trait, worker):
                continue
            
            # Check conflicts with existing traits
            conflicts = False
            for existing_trait_name in worker["traits"]:
                existing_trait = next((t for t in traits_list if t["name"] == existing_trait_name), None)
                if existing_trait:
                    if trait_name in existing_trait.get("conflicts", []):
                        conflicts = True
                        break
                    if existing_trait_name in trait.get("conflicts", []):
                        conflicts = True
                        break
            
            if not conflicts and trait_name not in worker["traits"]:
                worker["traits"].append(trait_name)
                added_count += 1
                renpy.log(f"Added trait '{trait_name}' to {worker.get('name', 'Unknown')}")
                
                # Remove from possible traits to avoid duplicates
                possible_traits = [t for t in possible_traits if t["name"] != trait_name]
        
        if added_count > 0:
            renpy.log(f"Successfully added {added_count} traits to {worker.get('name', 'Unknown')}")
            # Recalculate modifiers after adding traits
            recalculate_trait_modifiers(worker)
        else:
            renpy.log(f"Could not add any traits to {worker.get('name', 'Unknown')} - no suitable traits available")

