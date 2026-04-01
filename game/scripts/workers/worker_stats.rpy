init python:
    DEBUG_WORKER_STATS = False
    _trait_defs_cache_key = None
    _trait_defs_cache = {}
    _item_defs_cache_key = None
    _item_defs_cache = {}

    def _coerce_equipped_flag(equipped_flag):
        """Match inventory UI / snapshot semantics for the third slot of (id, qty, equipped)."""
        if isinstance(equipped_flag, bool):
            return equipped_flag
        if isinstance(equipped_flag, str):
            return equipped_flag.lower() in ("true", "1", "yes")
        if isinstance(equipped_flag, (int, float)):
            return bool(equipped_flag) and equipped_flag != 0
        return bool(equipped_flag)

    def _inventory_row_like(raw):
        """True if raw supports indexed access like a save-game inventory row (RevertableList-safe; see LA_BIBLIA §1)."""
        return raw is not None and hasattr(raw, "__len__") and hasattr(raw, "__getitem__")

    def _iter_normalized_inventory_rows(worker):
        """Yield (item_id, quantity, is_equipped) per inventory slot.

        Uses store._normalize_inventory_entry when available so dict-shaped rows and
        Ren'Py RevertableList rows (not always isinstance(..., list)) still count toward
        equipped item effects. Without this, after_load can cap health/energy to the
        unequipped max because calculate_max_* never sees gear bonuses.
        """
        if not worker or not hasattr(worker, "get"):
            return
        inv = worker.get("inventory")
        if not inv:
            return
        try:
            seq = list(inv)
        except Exception:
            return
        norm_fn = getattr(store, "_normalize_inventory_entry", None)
        for raw in seq:
            item_id = None
            qty = 1
            is_equipped = False
            if callable(norm_fn):
                ent = norm_fn(raw)
                if ent is None:
                    continue
                item_id, qty, is_equipped = ent[0], ent[1], ent[2]
                # _normalize_inventory_entry uses bool(slot3) for list rows; fix string "true"/"false" (§1: row may be RevertableList, not list).
                try:
                    if _inventory_row_like(raw) and len(raw) >= 3 and isinstance(raw[2], str):
                        is_equipped = _coerce_equipped_flag(raw[2])
                except Exception:
                    pass
            elif _inventory_row_like(raw):
                try:
                    ln = len(raw)
                except Exception:
                    ln = 0
                if ln < 1:
                    continue
                item_id = raw[0]
                if not item_id:
                    continue
                if ln >= 2:
                    try:
                        qty = int(raw[1]) if raw[1] is not None else 1
                    except Exception:
                        qty = 1
                is_equipped = _coerce_equipped_flag(raw[2]) if ln >= 3 else False
            else:
                continue
            if item_id:
                yield (item_id, max(0, int(qty) if qty is not None else 1), bool(is_equipped))

    def _get_trait_defs_by_name():
        """
        Fast name->trait map for the current traits_list snapshot.
        """
        global _trait_defs_cache_key, _trait_defs_cache
        key = (id(traits_list), len(traits_list))
        if _trait_defs_cache_key != key:
            mapped = {}
            for trait in (traits_list or []):
                if hasattr(trait, "get"):
                    name = trait.get("name")
                    if name:
                        mapped[name] = trait
            _trait_defs_cache = mapped
            _trait_defs_cache_key = key
        return _trait_defs_cache

    def _get_item_defs_by_id():
        """
        Fast id->item map for the current items_json snapshot.
        """
        global _item_defs_cache_key, _item_defs_cache
        items_seq = (items_json or {}).get("items", []) if hasattr(items_json, "get") else []
        key = (id(items_seq), len(items_seq))
        if _item_defs_cache_key != key:
            mapped = {}
            for item in (items_seq or []):
                if hasattr(item, "get"):
                    item_id = item.get("id")
                    if item_id:
                        mapped[item_id] = item
            _item_defs_cache = mapped
            _item_defs_cache_key = key
        return _item_defs_cache

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

        trait_defs = _get_trait_defs_by_name()
        item_defs = _get_item_defs_by_id()

        # Add trait bonuses - read from traits.json definitions
        for trait_name in worker.get("traits", []):
            trait_def = trait_defs.get(trait_name)
            if trait_def and "modifiers" in trait_def:
                if "skill_modifiers" in trait_def["modifiers"]:
                    trait_bonus = trait_def["modifiers"]["skill_modifiers"].get(skill_name, 0)
                    if trait_bonus != 0 and DEBUG_WORKER_STATS:
                        renpy.log(f"calculate_skill_with_traits: Adding {trait_bonus} bonus from trait '{trait_name}' to {skill_name} for {worker.get('name', 'Unknown')}")
                    bonus += trait_bonus

        # Add equipment bonuses
        for item_id, _qty, is_equipped in _iter_normalized_inventory_rows(worker):
            if not is_equipped:
                continue
            item_data = item_defs.get(item_id)
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
        
        trait_defs = _get_trait_defs_by_name()
        item_defs = _get_item_defs_by_id()

        # Add trait bonuses
        for trait_name in worker.get("traits", []):
            trait = trait_defs.get(trait_name)
            if trait:
                modifiers = trait.get("modifiers", {})
                bonus += modifiers.get("health", 0)
                bonus += modifiers.get("health_max", 0)
                if "health_max_cap" in modifiers:
                    cap_val = modifiers.get("health_max_cap")
                    # Ignore neutral/invalid caps (0 or negative) introduced by schema defaults.
                    if isinstance(cap_val, (int, float)) and cap_val > 0:
                        health_cap = cap_val if health_cap is None else min(health_cap, cap_val)
        
        # Add item bonuses from equipped items
        for item_id, _qty, is_equipped in _iter_normalized_inventory_rows(worker):
            if not is_equipped:
                continue
            item_data = item_defs.get(item_id)
            if item_data and "effect" in item_data:
                effect = item_data["effect"]
                try:
                    health_bonus = int(effect.get("health") or 0) + int(effect.get("health_max") or 0)
                except (TypeError, ValueError):
                    health_bonus = 0
                if health_bonus > 0:
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
        
        trait_defs = _get_trait_defs_by_name()
        item_defs = _get_item_defs_by_id()

        # Add trait bonuses
        for trait_name in worker.get("traits", []):
            trait_def = trait_defs.get(trait_name)
            if trait_def and "modifiers" in trait_def:
                modifiers = trait_def["modifiers"]
                bonus_energy += modifiers.get("energy", 0)
                bonus_energy += modifiers.get("energy_max", 0)
                if "energy_max_cap" in modifiers:
                    cap_val = modifiers.get("energy_max_cap")
                    # Ignore neutral/invalid caps (0 or negative) introduced by schema defaults.
                    if isinstance(cap_val, (int, float)) and cap_val > 0:
                        energy_cap = cap_val if energy_cap is None else min(energy_cap, cap_val)
        
        # Add item bonuses from equipped items
        for item_id, _qty, is_equipped in _iter_normalized_inventory_rows(worker):
            if not is_equipped:
                continue
            item_data = item_defs.get(item_id)
            if item_data and "effect" in item_data:
                effect = item_data["effect"]
                try:
                    energy_bonus = int(effect.get("energy") or 0) + int(effect.get("energy_max") or 0)
                except (TypeError, ValueError):
                    energy_bonus = 0
                if energy_bonus > 0:
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
        trait_defs = _get_trait_defs_by_name()
        for trait_name in worker.get("traits", []):
            trait = trait_defs.get(trait_name)
            if trait:
                bonus += trait.get("modifiers", {}).get("health_regeneration", 0)
        return base_regen + bonus

    def calculate_energy_regeneration(worker):
        """Return additional daily energy regeneration from traits (added on top of level-based regen)."""
        bonus = 0
        trait_defs = _get_trait_defs_by_name()
        for trait_name in worker.get("traits", []):
            trait_def = trait_defs.get(trait_name)
            if trait_def and "modifiers" in trait_def:
                bonus += trait_def["modifiers"].get("energy_regeneration", 0)
        return bonus

    def get_effective_comfort_desired(worker):
        """
        Return desired comfort after applying active trait caps/minimums.
        Uses stored comfort_desired as base so existing save values remain valid.
        """
        base_value = int(worker.get("comfort_desired", 1))
        cap = None
        minimum = None

        trait_defs = _get_trait_defs_by_name()
        for trait_name in worker.get("traits", []):
            trait_def = trait_defs.get(trait_name)
            if not trait_def:
                continue

            attr_caps = trait_def.get("attribute_caps", {})
            if "comfort_desired" in attr_caps:
                trait_cap = int(attr_caps.get("comfort_desired", 1))
                cap = trait_cap if cap is None else min(cap, trait_cap)

            attr_mins = trait_def.get("attribute_minimums", {})
            if "comfort_desired" in attr_mins:
                trait_min = int(attr_mins.get("comfort_desired", 1))
                minimum = trait_min if minimum is None else max(minimum, trait_min)

        effective = base_value
        if cap is not None:
            effective = min(effective, cap)
        if minimum is not None:
            effective = max(effective, minimum)
        return max(1, int(effective))

    def calculate_earnings(worker, base_earnings, client_seeked_traits=[]):
        """
        Return earnings after applying trait multipliers and Business Acumen.
        Losses (negative base_earnings) are returned unchanged so traits like "Beautiful"
        do not deepen failure payouts; building staffing money_mult still applies in the caller.
        """
        try:
            if float(base_earnings) < 0:
                return base_earnings
        except (TypeError, ValueError):
            pass
        multiplier = 1.0
        trait_defs = _get_trait_defs_by_name()
        for trait_name in worker.get("traits", []):
            trait = trait_defs.get(trait_name)
            if trait:
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
            "comfort_desired": get_effective_comfort_desired(worker),
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
        trait_defs = _get_trait_defs_by_name()
        item_defs = _get_item_defs_by_id()
        
        # Trait bonuses
        for trait_name in worker.get("traits", []):
            trait = trait_defs.get(trait_name)
            if trait:
                bonus += trait.get("modifiers", {}).get("libido_regeneration", 0)
        
        # Item bonuses
        for item_id, _qty, is_equipped in _iter_normalized_inventory_rows(worker):
            if not is_equipped:
                continue
            item_data = item_defs.get(item_id)
            if item_data and "effect" in item_data and hasattr(item_data["effect"], "get"):
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
        trait_defs = _get_trait_defs_by_name()
        item_defs = _get_item_defs_by_id()
        # Trait-based max bonuses
        for trait_name in worker.get("traits", []):
            trait = trait_defs.get(trait_name)
            if trait:
                extra += trait.get("modifiers", {}).get("libido_max", 0)
        # Item-based max bonuses
        for item_id, _qty, is_equipped in _iter_normalized_inventory_rows(worker):
            if not is_equipped:
                continue
            item_data = item_defs.get(item_id)
            if item_data and "effect" in item_data and hasattr(item_data["effect"], "get"):
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

