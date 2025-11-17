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
            "Charm": 5, "Wait": 5, "Agility": 5, "Craft": 5, "Specialty 4": 5, "Specialty 5": 5,
            "Specialty 6": 5, "Specialty 7": 5, "Specialty 8": 5, "Specialty 9": 5, "Specialty 10": 5,
            "Specialty 11": 5, "Specialty 12": 5
        }

        # Ensure skills exist and are valid - only use skill names
        if "skills" not in worker:
            worker["skills"] = base_skills.copy()
        else:
            # Only keep valid skill names and cap them at SKILL_MAX (100)
            worker["skills"] = {k: max(0, min(100, int(v))) for k, v in worker["skills"].items() if k in base_skills}
            for skill_name in base_skills:
                worker["skills"].setdefault(skill_name, 5)

        # Store original skills before any modifications
        if "original_skills" not in worker:
            worker["original_skills"] = worker["skills"].copy()

        # Monster-specific defaults
        if worker.get("monster", False):
            worker.setdefault("folder", "monsters")
            worker.setdefault("nsfw", True)
            worker.setdefault("encounter_only", True)
            worker.setdefault("unique", False)
            worker.setdefault("description", f"A {worker['name'].lower()} captured from the wild.")

        # Initialize skill_uses with skill names only
        if "skill_uses" not in worker:
            worker["skill_uses"] = {skill_name: 0 for skill_name in base_skills.keys()}
        else:
            # Only keep valid skill names in skill_uses
            new_skill_uses = {}
            for skill_name in base_skills.keys():
                new_skill_uses[skill_name] = int(worker["skill_uses"].get(skill_name, 0))
            worker["skill_uses"] = new_skill_uses

        worker["level"] = max(1, int(worker.get("level", 1)))

        if "inventory" not in worker or not isinstance(worker["inventory"], list):
            worker["inventory"] = []
        else:
            worker["inventory"] = list(worker["inventory"])

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
            # Non-unique workers can get random traits if they don't have any
            if "traits" not in worker or not worker["traits"]:
                assign_random_traits(worker)
            else:
                valid_traits = [trait for trait in worker["traits"] if trait in [t["name"] for t in traits_list]]
                worker["traits"] = valid_traits

        # Preserve existing comfort_level if it exists, otherwise set to comfort_desired or default to 1
        if "comfort_level" not in worker:
            worker["comfort_level"] = worker.get("comfort_desired", 1)
        worker.setdefault("comfort_desired", 1)  # Initialize from JSON or default to 1
        worker.setdefault("rebelliousness", 50)
        worker.setdefault("joy", random.randint(20, 80))
        worker.setdefault("romance", 0)
        worker.setdefault("relationship", 10 + worker.get("comfort_level", 1))
        worker.setdefault("libido", 10)  # New Libido stat, max 20

        if "trait_modifiers" not in worker:
            worker["trait_modifiers"] = {}

        # Apply trait secondary modifiers only once when worker is first created/loaded
        # This ensures traits affect secondary attributes but don't recalculate on every access
        apply_trait_secondary_modifiers_once(worker)

        # No migration needed for new game - system uses only skill names

        # Ensure minimum traits for workers that might have too few
        ensure_minimum_traits(worker)

        return worker



