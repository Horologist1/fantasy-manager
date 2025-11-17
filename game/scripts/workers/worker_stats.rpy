# worker_stats.rpy - Extended version with secondary attributes support
init python:

    def calculate_skill_with_traits(worker, skill_name):
        """Return effective skill level (base + trait bonus + equipment bonus + libido bonus). Base skills are capped at 100, but total can exceed 100 with bonuses."""
        base_skills = worker.get("original_skills", worker["skills"])
        
        # Only use skill names, no numeric ID compatibility
        base = int(base_skills.get(skill_name, 0))
        bonus = 0

        # Add trait bonuses
        for trait_name in worker.get("traits", []):
            if trait_name in worker.get("trait_modifiers", {}):
                trait_bonus = worker["trait_modifiers"][trait_name].get(skill_name, 0)
                bonus += trait_bonus

        # Add equipment bonuses
        for item in worker.get("inventory", []):
            if isinstance(item, tuple) and len(item) >= 3 and item[2]:  # Check if item is equipped
                item_data = next((i for i in items_json["items"] if i["id"] == item[0]), None)
                if item_data and "effect" in item_data:
                    if "skill_modifiers" in item_data["effect"]:
                        equip_bonus = item_data["effect"]["skill_modifiers"].get(skill_name, 0)
                        bonus += equip_bonus

        # Add libido bonus to sexual skills (only in NSFW mode)
        if persistent.nsfw_enabled and skill_name in get_sexual_skill_names():
            libido_bonus = worker.get("libido", 0)
            libido_bonus = int(libido_bonus / 2)
            bonus += libido_bonus

        # Only clamp base skill to 100, but allow bonuses to exceed the cap
        base = min(100, base)  # Ensure base skill doesn't exceed 100
        return base + bonus  # Total can exceed 100 with bonuses

    def calculate_max_health(worker):
        """Return effective maximum health (base from level plus trait bonus)."""
        if "max_health" in worker:
            return worker["max_health"]
        base_health = worker.get("level", 1) * 5
        bonus = 0
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    bonus += trait.get("modifiers", {}).get("health", 0)
        return base_health + bonus

    def calculate_max_energy(worker):
        """Calculate maximum energy based on level and traits."""
        if "max_energy" in worker:
            return worker["max_energy"]
        base_energy = worker.get("level", 1) * 5
        bonus_energy = 0
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "modifiers" in trait_def and "energy" in trait_def["modifiers"]:
                bonus_energy += trait_def["modifiers"]["energy"]
        return base_energy + bonus_energy

    def calculate_health_regeneration(worker):
        """Return effective health regeneration (base 1 plus trait bonus)."""
        base_regen = 1
        bonus = 0
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    bonus += trait.get("modifiers", {}).get("health_regeneration", 0)
        return base_regen + bonus

    def calculate_earnings(worker, base_earnings, client_seeked_traits=[]):
        """
        Return earnings after applying trait multipliers.
        Each trait's earnings_multiplier is multiplied in; if the client seeks a trait that the worker has,
        an extra multiplier is applied.
        """
        multiplier = 1.0
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    per_trait = trait.get("modifiers", {}).get("earnings_multiplier", 1.0)
                    per_trait = min(per_trait, 1.15)  # cap per-trait impact
                    multiplier *= per_trait
                    if trait_name in client_seeked_traits:
                        multiplier *= 1.2
        multiplier = min(multiplier, 1.6)
        return base_earnings * multiplier

    # Extended functions for secondary attributes
    def get_secondary_attribute(worker, attribute):
        """Get a secondary attribute value (joy, rebelliousness, etc.)."""
        return worker.get(attribute, 0)

    def set_secondary_attribute(worker, attribute, value):
        """Set a secondary attribute value while respecting caps."""
        set_attribute_with_caps(worker, attribute, value)

    def modify_secondary_attribute(worker, attribute, change):
        """Modify a secondary attribute by a certain amount while respecting caps."""
        apply_attribute_change(worker, attribute, change)

    def get_all_secondary_attributes(worker):
        """Get all secondary attributes as a dictionary."""
        return {
            "joy": worker.get("joy", 50),
            "rebelliousness": worker.get("rebelliousness", 50),
            "romance": worker.get("romance", 0),
            "relationship": worker.get("relationship", 10),
            "comfort_level": worker.get("comfort_level", 1),
            "comfort_desired": worker.get("comfort_desired", 1),
            "libido": worker.get("libido", 10)
        }

    def debug_worker_attributes(worker):
        """Debug function to print all worker attributes."""
        renpy.log(f"Worker {worker.get('name', 'Unknown')} attributes:")
        for attr, value in get_all_secondary_attributes(worker).items():
            cap = get_attribute_cap(worker, attr)
            cap_text = f" (cap: {cap})" if cap is not None else ""
            renpy.log(f"  {attr}: {value}{cap_text}")

    def apply_libido_overflow(worker, negative_libido):
        """Handle libido overflow to rebelliousness when libido goes below 0."""
        if negative_libido < 0:
            overflow_amount = abs(negative_libido)
            # Add overflow to rebelliousness
            current_rebelliousness = worker.get("rebelliousness", 50)
            new_rebelliousness = current_rebelliousness + overflow_amount
            set_attribute_with_caps(worker, "rebelliousness", new_rebelliousness)
            # Reset libido to 0
            worker["libido"] = 0
            renpy.log(f"Libido overflow for {worker.get('name', 'Unknown')}: +{overflow_amount} rebelliousness")

    def calculate_libido_regeneration(worker):
        """Return effective libido regeneration (base 1 + level + trait + item bonuses)."""
        base_regen = 1 + worker.get("level", 1)
        bonus = 0
        # Trait bonuses
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    bonus += trait.get("modifiers", {}).get("libido_regeneration", 0)
        # Item bonuses
        for item in worker.get("inventory", []):
            if isinstance(item, tuple) and len(item) >= 3 and item[2]:
                item_data = next((i for i in items_json["items"] if i["id"] == item[0]), None)
                if item_data and "effect" in item_data and isinstance(item_data["effect"], dict):
                    bonus += item_data["effect"].get("libido_regeneration", 0)
        return base_regen + bonus

    def get_max_libido(worker):
        """Return the maximum libido considering base, traits, items, and trait caps."""
        base_max = 20
        extra = 0
        # Trait-based max bonuses
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    extra += trait.get("modifiers", {}).get("libido_max", 0)
        # Item-based max bonuses
        for item in worker.get("inventory", []):
            if isinstance(item, tuple) and len(item) >= 3 and item[2]:
                item_data = next((i for i in items_json["items"] if i["id"] == item[0]), None)
                if item_data and "effect" in item_data and isinstance(item_data["effect"], dict):
                    extra += item_data["effect"].get("libido_max", 0)
        max_libido = base_max + extra
        # Respect trait-enforced caps if present
        cap = get_attribute_cap(worker, "libido")
        if cap is not None:
            max_libido = min(max_libido, cap)
        return max_libido

    def regenerate_libido(worker):
        """Regenerate libido based on worker level + trait + item bonuses with dynamic max."""
        current_libido = worker.get("libido", 10)
        regen_amount = calculate_libido_regeneration(worker)
        max_lib = get_max_libido(worker)
        new_libido = min(max_lib, current_libido + regen_amount)
        worker["libido"] = new_libido
        renpy.log(f"Libido regeneration for {worker.get('name', 'Unknown')}: +{regen_amount} (now {new_libido}/{max_lib})")

    def get_sexual_skill_names():
        """Return list of sexual skill names that receive Libido bonus."""
        return ["Sex", "Anal", "BDSM", "Hand", "Oral", "Homo", "Special", "Group", "Extreme", "Striptease"]

    def modify_base_skill(worker, skill_name, change):
        """Modify a base skill while ensuring it doesn't exceed SKILL_MAX (100)."""
        current = worker["skills"].get(skill_name, 0)
        new_value = max(0, min(SKILL_MAX, current + change))  # Cap between 0 and 100
        worker["skills"][skill_name] = new_value
        
        # Also update original_skills to maintain consistency
        if "original_skills" in worker:
            worker["original_skills"][skill_name] = new_value
            
        renpy.log(f"Modified {skill_name} for {worker.get('name', 'Unknown')}: {current} -> {new_value} (change: {change})")
        return new_value

    def set_base_skill(worker, skill_name, value):
        """Set a base skill while ensuring it doesn't exceed SKILL_MAX (100)."""
        capped_value = max(0, min(SKILL_MAX, value))  # Cap between 0 and 100
        worker["skills"][skill_name] = capped_value
        
        # Also update original_skills to maintain consistency
        if "original_skills" in worker:
            worker["original_skills"][skill_name] = capped_value
            
        renpy.log(f"Set {skill_name} for {worker.get('name', 'Unknown')} to {capped_value} (requested: {value})")
        return capped_value

