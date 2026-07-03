# worker_defaults.rpy

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

        if "inventory" not in worker:
            worker["inventory"] = []
        elif worker["inventory"] is None:
            worker["inventory"] = []
        elif not (hasattr(worker["inventory"], "__iter__") and not isinstance(worker["inventory"], str)):
            try:
                worker["inventory"] = list(worker["inventory"]) if worker["inventory"] else []
            except Exception:
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
        
        # Fixed health initialization
        # If a worker template ships with base health but traits increase max HP,
        # promote to full HP to avoid "injured by default" in recruitment lists.
        max_health = calculate_max_health(worker)
        base_health = 10 + (worker.get("level", 1) * 5)
        if "health" not in worker:
            worker["health"] = max_health
        else:
            try:
                worker["health"] = int(worker.get("health", 0))
            except Exception:
                worker["health"] = 0
            # Heal template workers that still have legacy/base health after max increased by traits/items.
            if worker["health"] == base_health and max_health > base_health:
                worker["health"] = max_health
            # Only cap health to maximum otherwise
            if worker["health"] > max_health:
                worker["health"] = max_health
            # Make sure health doesn't go below 0
            elif worker["health"] < 0:
                worker["health"] = 0

        # Fixed energy initialization
        # Same compatibility rule as health for "tired by default" templates.
        max_energy = calculate_max_energy(worker)
        base_energy = worker.get("level", 1) * 5
        if "energy" not in worker:
            worker["energy"] = max_energy
        else:
            try:
                worker["energy"] = int(worker.get("energy", 0))
            except Exception:
                worker["energy"] = 0
            # Recover template workers with old/base energy when traits/items raise max.
            if worker["energy"] == base_energy and max_energy > base_energy:
                worker["energy"] = max_energy
            # Only cap energy to maximum otherwise
            if worker["energy"] > max_energy:
                worker["energy"] = max_energy
            # Make sure energy doesn't go below 0
            elif worker["energy"] < 0:
                worker["energy"] = 0

        worker.setdefault("success_count", 0)
        worker.setdefault("special_match_victories", 0)

        trait_catalog = []
        if hasattr(store, "get_all_traits"):
            trait_catalog = list(store.get_all_traits() or [])
        if not trait_catalog and hasattr(store, "refresh_traits_cache"):
            trait_catalog = list(store.refresh_traits_cache(force=True) or [])

        known_trait_names = set(t.get("name") for t in trait_catalog if hasattr(t, "get") and t.get("name"))
        has_trait_catalog = len(known_trait_names) > 0

        raw_traits = worker.get("traits", [])
        if isinstance(raw_traits, str):
            normalized_traits = [raw_traits] if raw_traits else []
        elif isinstance(raw_traits, (list, tuple)) or hasattr(raw_traits, "__iter__"):
            try:
                normalized_traits = [t for t in list(raw_traits) if isinstance(t, str) and t]
            except Exception:
                normalized_traits = []
        else:
            normalized_traits = []
        worker["traits"] = normalized_traits

        # Enforce trait validity on existing worker data (requirements/conflicts/gender restrictions).
        _sanitize_traits = getattr(store, "sanitize_worker_trait_state", None)
        if callable(_sanitize_traits):
            _sanitize_traits(worker, trait_catalog=trait_catalog)

        # Arena Champion must come from 5 special match victories, never from random generation.
        # Keep backward compatibility by cleaning legacy invalid states on load.
        if "Arena Champion" in (worker.get("traits") or []):
            try:
                _arena_wins = int(worker.get("special_match_victories", 0) or 0)
            except Exception:
                _arena_wins = 0
            if _arena_wins < 5:
                worker["traits"] = [t for t in (worker.get("traits") or []) if t != "Arena Champion"]
                _dur = worker.get("trait_durations")
                if hasattr(_dur, "pop"):
                    _dur.pop("Arena Champion", None)
                renpy.log(
                    f"TRAITS: Removed invalid 'Arena Champion' from {worker.get('name', 'Unknown')} "
                    f"(special_match_victories={_arena_wins})"
                )

        if has_trait_catalog:
            missing_definitions = [t for t in worker["traits"] if t not in known_trait_names]
            if missing_definitions:
                renpy.log(
                    f"TRAITS: Preserving {len(missing_definitions)} unknown trait(s) for "
                    f"{worker.get('name', 'Unknown')}: {missing_definitions}"
                )
        else:
            # During renpy.predicting(), file I/O is restricted so cache can't load - skip log spam
            if not renpy.predicting():
                renpy.log(
                    f"TRAITS: Trait catalog unavailable while loading {worker.get('name', 'Unknown')}; "
                    "preserving traits and skipping random backfill"
                )

        # Unique workers should not get random traits - they should only have traits
        # defined in JSON. That skip lives in ensure_minimum_traits (worker_traits.rpy);
        # here every worker just gets an empty traits list as a default.
        if "traits" not in worker:
            worker["traits"] = []

        # Preserve existing comfort_level if it exists, otherwise set to comfort_desired or default to 1
        if "comfort_level" not in worker:
            worker["comfort_level"] = worker.get("comfort_desired", 1)
        try:
            _comfort_cost_lv = int(worker.get("comfort_level", 1))
        except Exception:
            _comfort_cost_lv = 1
        # Canon rule: worker daily cost is comfort x difficulty rate.
        worker["daily_cost"] = int(max(1, _comfort_cost_lv) * get_difficulty_comfort_mult())
        worker.setdefault("comfort_desired", 1)  # Initialize from JSON or default to 1
        worker.setdefault("rebelliousness", 50)
        worker.setdefault("joy", random.randint(20, 80))
        worker.setdefault("romance", 0)
        worker.setdefault("relationship", 10 + worker.get("comfort_level", 1))
        worker.setdefault("libido", 10)  # New Libido stat, max 20

        # Automation defaults for new workers come from persistent global Defaults.
        _def_supply_on = bool(getattr(persistent, "default_auto_supply_potions", False))
        try:
            _def_supply_count = int(getattr(persistent, "default_auto_supply_potion_count", 3))
        except Exception:
            _def_supply_count = 3
        _def_supply_count = max(1, min(5, _def_supply_count))
        _def_auto_equip = bool(getattr(persistent, "default_auto_equip", False))
        _def_auto_rest = bool(getattr(persistent, "default_auto_rest", False))
        try:
            _def_rest_pct = int(getattr(persistent, "default_auto_rest_entry_pct", 35))
        except Exception:
            _def_rest_pct = 35
        _allowed_rest_pcts = (15, 25, 35, 45)
        if _def_rest_pct not in _allowed_rest_pcts:
            _def_rest_pct = min(_allowed_rest_pcts, key=lambda x: abs(x - _def_rest_pct))

        worker.setdefault("auto_supply_potions", _def_supply_on)
        worker.setdefault("auto_supply_potion_count", _def_supply_count)
        worker.setdefault("auto_equip", _def_auto_equip)
        worker.setdefault("auto_rest", _def_auto_rest)
        worker.setdefault("auto_rest_entry_pct", _def_rest_pct)
        _narp = getattr(store, "normalize_auto_rest_entry_pct_for_worker", None)
        if callable(_narp):
            worker["auto_rest_entry_pct"] = _narp(worker)

        if "trait_modifiers" not in worker:
            worker["trait_modifiers"] = {}

        # Apply trait secondary modifiers only once when worker is first created/loaded
        # This ensures traits affect secondary attributes but don't recalculate on every access
        apply_trait_secondary_modifiers_once(worker)

        # No migration needed for new game - system uses only skill names

        # Ensure minimum traits only when trait catalog is available.
        if has_trait_catalog:
            ensure_minimum_traits(worker)
        
        # Deduplicate traits to prevent duplicates
        deduplicate_traits(worker)

        return worker



