# worker_stats.rpy - Extended version with secondary attributes support
init python:
    DEBUG_WORKER_STATS = False

    def calculate_skill_with_traits(worker, skill_name):
        """Return effective skill level (base + trait bonus + equipment bonus + libido bonus). Base skills are capped at 100, but total can exceed 100 with bonuses."""
        # Ensure we're using the real worker from store.workers to get current equipment state
        if hasattr(store, 'workers') and worker:
            worker_name = worker.get("name")
            if worker_name:
                real_worker = next((w for w in store.workers if w.get("name") == worker_name), None)
                if real_worker:
                    worker = real_worker
        
        # Use skills directly as the source of truth (original_skills is deprecated)
        base_skills = worker.get("skills", {})
        
        # Only use skill names, no numeric ID compatibility
        base = int(base_skills.get(skill_name, 0))
        bonus = 0

        # Add trait bonuses - read from traits.json definitions
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t.get("name") == trait_name), None)
            if trait_def and "modifiers" in trait_def:
                if "skill_modifiers" in trait_def["modifiers"]:
                    trait_bonus = trait_def["modifiers"]["skill_modifiers"].get(skill_name, 0)
                    if trait_bonus != 0 and DEBUG_WORKER_STATS:
                        renpy.log(f"calculate_skill_with_traits: Adding {trait_bonus} bonus from trait '{trait_name}' to {skill_name} for {worker.get('name', 'Unknown')}")
                    bonus += trait_bonus

        # Add equipment bonuses
        for item in worker.get("inventory", []):
            # Handle both lists (from JSON) and tuples (from Python)
            is_equipped = False
            item_id = None
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                item_id = item[0]
                equipped_flag = item[2]
                # Convert to boolean if needed
                if isinstance(equipped_flag, bool):
                    is_equipped = equipped_flag
                elif isinstance(equipped_flag, str):
                    is_equipped = equipped_flag.lower() in ("true", "1", "yes")
                elif isinstance(equipped_flag, (int, float)):
                    is_equipped = bool(equipped_flag) and equipped_flag != 0
            
            if is_equipped and item_id:
                item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
                if item_data and "effect" in item_data:
                    if "skill_modifiers" in item_data["effect"]:
                        equip_bonus = item_data["effect"]["skill_modifiers"].get(skill_name, 0)
                        if equip_bonus != 0 and DEBUG_WORKER_STATS:
                            renpy.log(f"calculate_skill_with_traits: Adding {equip_bonus} bonus from equipped item '{item_id}' to {skill_name} for {worker.get('name', 'Unknown')}")
                        bonus += equip_bonus

        # Add libido bonus to sexual skills (only in NSFW mode)
        if persistent.nsfw_enabled and skill_name in get_sexual_skill_names():
            libido_bonus = worker.get("libido", 0)
            libido_bonus = int(libido_bonus / 2)
            bonus += libido_bonus

        # Management skill bonuses (manager character sheet)
        mgmt = getattr(store, "management_skills", None) or {}
        if skill_name in get_sexual_skill_names():
            bonus += 5 * mgmt.get("whore_mastery", 0)
        if skill_name == "Combat":
            bonus += 5 * mgmt.get("combat_instruction", 0)
        if skill_name == "Service":
            bonus += 5 * mgmt.get("servant_training", 0)
        if skill_name == "Agility":
            bonus += 5 * mgmt.get("gang_leader", 0)

        # Only clamp base skill to 100, but allow bonuses to exceed the cap
        base = min(100, base)  # Ensure base skill doesn't exceed 100
        return base + bonus  # Total can exceed 100 with bonuses

    def calculate_max_health(worker):
        """Return effective maximum health (base from level plus trait bonus plus item bonuses).
        Always recalculates from scratch to avoid duplicate bonuses when items are re-applied."""
        base_health = 10 + (worker.get("level", 1) * 5)
        bonus = 0
        health_cap = None
        
        # Add trait bonuses
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    modifiers = trait.get("modifiers", {})
                    bonus += modifiers.get("health", 0)
                    bonus += modifiers.get("health_max", 0)
                    if "health_max_cap" in modifiers:
                        cap_val = modifiers.get("health_max_cap")
                        if isinstance(cap_val, (int, float)):
                            health_cap = cap_val if health_cap is None else min(health_cap, cap_val)
        
        # Add item bonuses from equipped items
        inventory = worker.get("inventory", [])
        for item in inventory:
            # Handle both lists (from JSON) and tuples (from Python)
            is_equipped = False
            item_id = None
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                item_id = item[0]
                equipped_flag = item[2]
                # Convert to boolean if needed
                if isinstance(equipped_flag, bool):
                    is_equipped = equipped_flag
                elif isinstance(equipped_flag, str):
                    is_equipped = equipped_flag.lower() in ("true", "1", "yes")
                elif isinstance(equipped_flag, (int, float)):
                    is_equipped = bool(equipped_flag) and equipped_flag != 0
            
            if is_equipped and item_id:
                item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
                if item_data and "effect" in item_data:
                    health_bonus = item_data["effect"].get("health", 0)
                    if health_bonus > 0:  # Only positive bonuses (max_health increases)
                        bonus += health_bonus
        
        # Management skill: Combat Instruction (+10 max HP per point)
        mgmt = getattr(store, "management_skills", None) or {}
        bonus += 10 * mgmt.get("combat_instruction", 0)
        
        max_health = base_health + bonus
        if health_cap is not None:
            max_health = min(max_health, health_cap)
        return max(1, int(max_health))

    def calculate_max_energy(worker):
        """Calculate maximum energy based on level, traits, and item bonuses.
        Always recalculates from scratch to avoid duplicate bonuses when items are re-applied."""
        base_energy = worker.get("level", 1) * 5
        bonus_energy = 0
        energy_cap = None
        
        # Add trait bonuses
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "modifiers" in trait_def:
                modifiers = trait_def["modifiers"]
                bonus_energy += modifiers.get("energy", 0)
                bonus_energy += modifiers.get("energy_max", 0)
                if "energy_max_cap" in modifiers:
                    cap_val = modifiers.get("energy_max_cap")
                    if isinstance(cap_val, (int, float)):
                        energy_cap = cap_val if energy_cap is None else min(energy_cap, cap_val)
        
        # Add item bonuses from equipped items
        inventory = worker.get("inventory", [])
        for item in inventory:
            # Handle both lists (from JSON) and tuples (from Python)
            is_equipped = False
            item_id = None
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                item_id = item[0]
                equipped_flag = item[2]
                # Convert to boolean if needed
                if isinstance(equipped_flag, bool):
                    is_equipped = equipped_flag
                elif isinstance(equipped_flag, str):
                    is_equipped = equipped_flag.lower() in ("true", "1", "yes")
                elif isinstance(equipped_flag, (int, float)):
                    is_equipped = bool(equipped_flag) and equipped_flag != 0
            
            if is_equipped and item_id:
                item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
                if item_data and "effect" in item_data:
                    energy_bonus = item_data["effect"].get("energy", 0)
                    if energy_bonus > 0:  # Only positive bonuses (max_energy increases)
                        bonus_energy += energy_bonus
        
        # Management skill: Gang Leader (+10 max Energy per point)
        mgmt = getattr(store, "management_skills", None) or {}
        bonus_energy += 10 * mgmt.get("gang_leader", 0)
        
        max_energy = base_energy + bonus_energy
        if energy_cap is not None:
            max_energy = min(max_energy, energy_cap)
        return max(0, int(max_energy))

    def calculate_health_regeneration(worker):
        """Return effective health regeneration (base 1 plus trait bonus)."""
        base_regen = 1
        bonus = 0
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    bonus += trait.get("modifiers", {}).get("health_regeneration", 0)
        return base_regen + bonus

    def calculate_energy_regeneration(worker):
        """Return additional daily energy regeneration from traits (added on top of level-based regen)."""
        bonus = 0
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t.get("name") == trait_name), None)
            if trait_def and "modifiers" in trait_def:
                bonus += trait_def["modifiers"].get("energy_regeneration", 0)
        return bonus

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
                    per_trait = min(per_trait, 1.5)  # cap per-trait impact
                    multiplier *= per_trait
                    if trait_name in client_seeked_traits:
                        multiplier *= 1.2
        multiplier = min(multiplier, 2.0)
        # Management skill: Business Acumen (+0.1 money multiplier per point)
        mgmt = getattr(store, "management_skills", None) or {}
        money_mult = 1.0 + 0.1 * mgmt.get("business_acumen", 0)
        return base_earnings * multiplier * money_mult

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
        """Handle libido overflow to rebelliousness when libido goes BELOW 0 (negative).
        NOTE: This is NOT 'excess over max' (e.g. 35/20). Only negative libido adds to rebelliousness."""
        if negative_libido < 0:
            overflow_amount = abs(negative_libido)
            # Add overflow to rebelliousness
            current_rebelliousness = worker.get("rebelliousness", 50)
            new_rebelliousness = current_rebelliousness + overflow_amount
            set_attribute_with_caps(worker, "rebelliousness", new_rebelliousness)
            # Reset libido to 0
            worker["libido"] = 0
            renpy.log(f"Libido overflow for {worker.get('name', 'Unknown')}: +{overflow_amount} rebelliousness")

    def get_sexual_skill_names():
        """Return list of sexual skill names that receive Libido bonus and count for libido drain."""
        return ["Sex", "Anal", "BDSM", "Hand", "Oral", "Homo", "Special", "Group", "Extreme", "Striptease"]

    def count_sexual_work_today(worker):
        """Count how many times this worker used sexual skills today.
        
        Uses daily_sexual_work counter which is separate from skill_uses.
        This allows skill_uses to accumulate for level ups while
        daily_sexual_work tracks only today's work for libido calculation.
        """
        return worker.get("daily_sexual_work", 0)

    def calculate_libido_regeneration(worker):
        """
        Return effective libido regeneration considering work intensity.
        
        Base regeneration: 1 + level + trait + item bonuses
        Penalty for sexual work: -1 per sexual skill use (minimum result: -2)
        
        This means:
        - No sexual work: full regeneration
        - Light work (1-2 uses): slight penalty
        - Heavy work (3+ uses): may not regenerate or even decrease
        """
        base_regen = 1 + worker.get("level", 1)
        bonus = 0
        
        # Trait bonuses
        for trait_name in worker.get("traits", []):
            for trait in traits_list:
                if trait["name"] == trait_name:
                    bonus += trait.get("modifiers", {}).get("libido_regeneration", 0)
        
        # Item bonuses
        for item in worker.get("inventory", []):
            # Handle both lists (from JSON) and tuples (from Python)
            is_equipped = False
            item_id = None
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                item_id = item[0]
                equipped_flag = item[2]
                # Convert to boolean if needed
                if isinstance(equipped_flag, bool):
                    is_equipped = equipped_flag
                elif isinstance(equipped_flag, str):
                    is_equipped = equipped_flag.lower() in ("true", "1", "yes")
                elif isinstance(equipped_flag, (int, float)):
                    is_equipped = bool(equipped_flag) and equipped_flag != 0
            
            if is_equipped and item_id:
                item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
                if item_data and "effect" in item_data and isinstance(item_data["effect"], dict):
                    bonus += item_data["effect"].get("libido_regeneration", 0)
        
        # Calculate work penalty
        sexual_work_count = count_sexual_work_today(worker)
        work_penalty = sexual_work_count  # -1 per sexual skill use
        
        # Total regeneration (can be negative, minimum -2)
        total_regen = base_regen + bonus - work_penalty
        
        # Allow slight decrease if overworked, but cap at -2 to prevent rapid drain
        return max(-2, total_regen)

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
            # Handle both lists (from JSON) and tuples (from Python)
            is_equipped = False
            item_id = None
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                item_id = item[0]
                equipped_flag = item[2]
                # Convert to boolean if needed
                if isinstance(equipped_flag, bool):
                    is_equipped = equipped_flag
                elif isinstance(equipped_flag, str):
                    is_equipped = equipped_flag.lower() in ("true", "1", "yes")
                elif isinstance(equipped_flag, (int, float)):
                    is_equipped = bool(equipped_flag) and equipped_flag != 0
            
            if is_equipped and item_id:
                item_data = next((i for i in items_json["items"] if i["id"] == item_id), None)
                if item_data and "effect" in item_data and isinstance(item_data["effect"], dict):
                    extra += item_data["effect"].get("libido_max", 0)
        max_libido = base_max + extra
        # Respect trait-enforced caps if present
        cap = get_attribute_cap(worker, "libido")
        if cap is not None:
            max_libido = min(max_libido, cap)
        return max_libido

    def regenerate_libido(worker):
        """
        Regenerate libido at end of day, considering sexual work done.
        
        - Regeneration can be negative if worker did lots of sexual work
        - If libido goes below 0, overflow converts to rebelliousness
        - Clears skill_uses counter after processing
        - Current libido is clamped to max before calculation so over-cap (e.g. 35/20)
          does not create unfair overflow when regen goes negative.
        """
        raw_libido = worker.get("libido", 10)
        max_lib = get_max_libido(worker)
        # Clamp current to max so we never use "over cap" in the formula (fixes 35/20 scenarios)
        current_libido = min(raw_libido, max_lib)
        if raw_libido > max_lib:
            worker["libido"] = current_libido
            renpy.log(f"Libido clamped from {raw_libido} to max {max_lib} for {worker.get('name', 'Unknown')} before regen")
        
        regen_amount = calculate_libido_regeneration(worker)
        
        # Count work for logging
        sexual_work = count_sexual_work_today(worker)
        
        # Calculate new libido (using clamped current)
        new_libido = current_libido + regen_amount
        
        # Handle overflow to rebelliousness if libido goes negative
        if new_libido < 0:
            overflow = abs(new_libido)
            apply_libido_overflow(worker, -overflow)  # This sets libido to 0
            renpy.log(f"Libido DRAIN for {worker.get('name', 'Unknown')}: {current_libido} -> 0 (overflow {overflow} to rebelliousness), sexual work: {sexual_work}")
        else:
            # Cap at max libido
            new_libido = min(max_lib, new_libido)
            worker["libido"] = new_libido
            
            if regen_amount >= 0:
                renpy.log(f"Libido regen for {worker.get('name', 'Unknown')}: {current_libido} -> {new_libido} (+{regen_amount}), sexual work: {sexual_work}")
            else:
                renpy.log(f"Libido drain for {worker.get('name', 'Unknown')}: {current_libido} -> {new_libido} ({regen_amount}), sexual work: {sexual_work}")
        
        # Reset daily_sexual_work counter after libido calculation
        # skill_uses is NOT reset here - it accumulates for skill level ups
        worker["daily_sexual_work"] = 0

    def modify_base_skill(worker, skill_name, change):
        """Modify a base skill while ensuring it doesn't exceed SKILL_MAX (100)."""
        current = worker["skills"].get(skill_name, 0)
        new_value = max(0, min(SKILL_MAX, current + change))  # Cap between 0 and 100
        worker["skills"][skill_name] = new_value
        renpy.log(f"Modified {skill_name} for {worker.get('name', 'Unknown')}: {current} -> {new_value} (change: {change})")
        return new_value

    def set_base_skill(worker, skill_name, value):
        """Set a base skill while ensuring it doesn't exceed SKILL_MAX (100)."""
        capped_value = max(0, min(SKILL_MAX, value))  # Cap between 0 and 100
        worker["skills"][skill_name] = capped_value
        renpy.log(f"Set {skill_name} for {worker.get('name', 'Unknown')} to {capped_value} (requested: {value})")
        return capped_value

