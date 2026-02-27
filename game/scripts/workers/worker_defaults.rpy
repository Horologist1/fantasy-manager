# worker_defaults.rpy
# funciones que definen y mantienen la estructura básica de los trabajadores

init python:

    def ensure_worker_defaults(worker):
        """
        Ensure all required worker attributes are initialized with default values,
        with special handling for monster workers.
        """
        base_skills = {
            "Sex": 5, "Anal": 5, "BDSM": 5, "Hand": 5, "Oral": 5, "Homo": 5,
            "Special": 5, "Group": 5, "Extreme": 5, "Striptease": 5, "Combat": 5, "Clever": 5,
            "Charm": 5, "Service": 5, "Agility": 5, "Craft": 5, "Specialty 4": 5, "Specialty 5": 5,
            "Specialty 6": 5, "Specialty 7": 5, "Specialty 8": 5, "Specialty 9": 5, "Specialty 10": 5,
            "Specialty 11": 5, "Specialty 12": 5
        }
        # Map lowercase/alternate keys from imports (e.g. Whoremaster) to canonical skill names
        _skill_name_aliases = {
            "sex": "Sex", "anal": "Anal", "bdsm": "BDSM", "hand": "Hand", "oral": "Oral",
            "homo": "Homo", "special": "Special", "group": "Group", "extreme": "Extreme",
            "striptease": "Striptease", "combat": "Combat", "clever": "Clever", "charm": "Charm",
            "service": "Service", "agility": "Agility", "craft": "Craft"
        }

        # Ensure skills exist and are valid - only use canonical skill names
        if "skills" not in worker:
            worker["skills"] = base_skills.copy()
        else:
            # Normalize: merge lowercase/alias keys into canonical names (e.g. "sex" -> "Sex"), take max value
            raw = worker["skills"]
            normalized = {}
            for k, v in raw.items():
                try:
                    val = max(0, min(100, int(v)))
                except (TypeError, ValueError):
                    val = 5
                canonical = _skill_name_aliases.get(k, k) if k not in base_skills else k
                if canonical in base_skills:
                    normalized[canonical] = max(normalized.get(canonical, 0), val)
            worker["skills"] = normalized
            for skill_name in base_skills:
                worker["skills"].setdefault(skill_name, 5)

        # NOTE: original_skills has been removed - skills is now the single source of truth
        # Item and trait bonuses are calculated dynamically in calculate_skill_with_traits()
        # Clean up original_skills from old saves to keep data clean
        if "original_skills" in worker:
            del worker["original_skills"]

        # Monster-specific defaults
        if worker.get("monster", False):
            worker.setdefault("folder", "monsters")
            worker.setdefault("nsfw", True)
            worker.setdefault("encounter_only", True)
            worker.setdefault("unique", False)
            worker.setdefault("description", f"A {worker['name'].lower()} captured from the wild.")

        # Initialize skill_uses with skill names only
        # IMPORTANT: Preserve existing skill_uses values - don't reset progress when changing professions
        if "skill_uses" not in worker:
            worker["skill_uses"] = {skill_name: 0 for skill_name in base_skills.keys()}
        else:
            # Preserve ALL existing skill_uses values, only initialize missing ones
            # This ensures progress is not lost when changing professions
            for skill_name in base_skills.keys():
                if skill_name not in worker["skill_uses"]:
                    worker["skill_uses"][skill_name] = 0
                else:
                    # Ensure it's an integer
                    worker["skill_uses"][skill_name] = int(worker["skill_uses"][skill_name])
            # Don't remove skills that aren't in base_skills - preserve all progress

        worker["level"] = max(1, int(worker.get("level", 1)))
        
        # Initialize daily_sexual_work if not present (for libido calculation)
        # This is separate from skill_uses which accumulates for level ups
        if "daily_sexual_work" not in worker:
            worker["daily_sexual_work"] = 0

        if "inventory" not in worker or not isinstance(worker["inventory"], list):
            worker["inventory"] = []
        else:
            worker["inventory"] = list(worker["inventory"])

        # Remove max_health/max_energy if they exist to force recalculation from items
        # This prevents duplicate bonuses when items are re-applied after loading
        if "max_health" in worker:
            del worker["max_health"]
        if "max_energy" in worker:
            del worker["max_energy"]
        
        # Cap secondary attributes to their maximum values (100 by default, or trait-defined)
        # This fixes any existing saves where attributes exceeded their limits
        # Note: set_attribute_with_caps is defined in worker_traits.rpy and available globally
        for attr in ["joy", "rebelliousness", "romance", "relationship"]:
            if attr in worker:
                current_value = worker[attr]
                set_attribute_with_caps(worker, attr, current_value)
                if worker[attr] != current_value:
                    renpy.log(f"Fixed {attr} for {worker.get('name', 'Unknown')}: {current_value} -> {worker[attr]} (capped)")
        
        # Cap libido to max (fixes saves where libido was over cap, e.g. 35/20 after losing item/trait)
        if "libido" in worker:
            try:
                max_lib = get_max_libido(worker)
                if worker["libido"] > max_lib:
                    old_lib = worker["libido"]
                    worker["libido"] = max_lib
                    renpy.log(f"Fixed libido for {worker.get('name', 'Unknown')}: {old_lib} -> {max_lib} (capped to max)")
            except Exception:
                pass
        
        # Fixed health initialization - only set to max if doesn't exist
        max_health = calculate_max_health(worker)
        if "health" not in worker:
            worker["health"] = max_health
        else:
            # Only cap health to maximum, don't set to maximum
            if worker["health"] > max_health:
                worker["health"] = max_health
            # Make sure health doesn't go below 0
            elif worker["health"] < 0:
                worker["health"] = 0

        # Fixed energy initialization - only set to max if doesn't exist
        max_energy = calculate_max_energy(worker)
        if "energy" not in worker:
            worker["energy"] = max_energy
        else:
            # Only cap energy to maximum, don't set to maximum
            if worker["energy"] > max_energy:
                worker["energy"] = max_energy
            # Make sure energy doesn't go below 0
            elif worker["energy"] < 0:
                worker["energy"] = 0

        worker.setdefault("success_count", 0)
        worker.setdefault("special_match_victories", 0)

        # Unique workers should not get random traits - they should only have traits defined in JSON
        if worker.get("unique", False):
            # For unique workers, only validate existing traits, don't assign random ones
            if "traits" in worker and worker["traits"]:
                valid_traits = [trait for trait in worker["traits"] if trait in [t["name"] for t in traits_list]]
                worker["traits"] = valid_traits
            # If no traits defined, keep empty list (don't assign random)
            elif "traits" not in worker:
                worker["traits"] = []
        else:
            # Non-unique workers: validate existing traits first
            if "traits" in worker and worker["traits"]:
                valid_traits = [trait for trait in worker["traits"] if trait in [t["name"] for t in traits_list]]
                worker["traits"] = valid_traits
            else:
                worker["traits"] = []
            
            # Ensure non-unique workers have at least 3 traits
            # If they have fewer than 3, add random traits to reach 3-4 total
            current_trait_count = len(worker.get("traits", []))
            if current_trait_count < 3:
                # Assign random traits to fill up to 3-4 total (preserving existing traits)
                store.assign_random_traits_with_limits(worker, target_min=3, target_max=4)
                # After assignment, log final count
                final_count = len(worker.get("traits", []))
                renpy.log(f"TRAITS: Worker {worker.get('name', 'Unknown')} - Started with {current_trait_count}, now has {final_count} traits")

        # Preserve existing comfort_level if it exists, otherwise set to comfort_desired or default to 1
        if "comfort_level" not in worker:
            worker["comfort_level"] = worker.get("comfort_desired", 1)
        worker.setdefault("comfort_desired", 1)  # Initialize from JSON or default to 1
        worker.setdefault("rebelliousness", 50)
        worker.setdefault("joy", random.randint(20, 80))
        worker.setdefault("romance", 0)
        worker.setdefault("relationship", 10 + worker.get("comfort_level", 1))
        worker.setdefault("libido", 10)  # New Libido stat, max 20

        # Auto-supply potions and auto-equip (worker details toggles)
        worker.setdefault("auto_supply_potions", False)
        worker.setdefault("auto_supply_potion_count", 3)
        worker.setdefault("auto_equip", False)

        if "trait_modifiers" not in worker:
            worker["trait_modifiers"] = {}

        # Apply trait secondary modifiers only once when worker is first created/loaded
        # This ensures traits affect secondary attributes but don't recalculate on every access
        apply_trait_secondary_modifiers_once(worker)

        # No migration needed for new game - system uses only skill names

        # Ensure minimum traits for workers that might have too few
        ensure_minimum_traits(worker)
        
        # Deduplicate traits to prevent duplicates
        deduplicate_traits(worker)

        return worker



