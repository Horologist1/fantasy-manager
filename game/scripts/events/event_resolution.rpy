# event_resolution.rpy

init python:

    def apply_interaction_effects(worker, interaction):
        """Apply the effects of an interaction to a worker."""
        if "effect" in interaction:
            for stat, value in interaction["effect"].items():
                if stat in worker:
                    worker[stat] += value
                    worker[stat] = max(0, min(100, worker[stat]))  # Ensure stats stay within bounds

        if "cost_energy" in interaction:
            worker["energy"] = max(0, worker["energy"] - interaction["cost_energy"])

        if "cost_health" in interaction:
            worker["health"] = max(0, worker["health"] - interaction["cost_health"])

        if "cost_money" in interaction:
            store.money = max(0, store.money - interaction["cost_money"])


    def render_event_text(event, result="success", extra_replacements=None):
        # Determine worker_name from the event; assume individual event.
        if isinstance(event.get("worker"), dict):
            worker_name = event["worker"].get("name", "Unknown")
        else:
            worker_name = event.get("worker_name", "Unknown")
        
        replacements = {
            "worker_name": str(worker_name),
            "skill": event.get("skill", "N/A"),
            "individual_earnings": event.get("individual_earnings", "N/A"),
            "X": event.get("daily_cost", "N/A"),
        }
        if extra_replacements:
            replacements.update(extra_replacements)
        
        descriptions = event.get("descriptions")
        if isinstance(descriptions, dict):
            template = descriptions.get(result, event.get("description", "No description available."))
        else:
            template = descriptions or event.get("description", "No description available.")
        
        try:
            text = template.format(**replacements)
        except KeyError as e:
            missing = e.args[0]
            replacements[missing] = ""
            text = template.format(**replacements)
        return text


    def update_reputation_from_events(building_name, event_result):
        """Adjust building reputation based on event outcome."""
        building = available_buildings[building_name]
        # Get base reputation
        calculate_reputation(building_name)  # Updates building["reputation"]
        # Apply event-based adjustment
        reputation_change = {
            "critical success": 10,
            "success": 5,
            "mediocre": 0,
            "failure": -5
        }.get(event_result.lower(), 0)
        # Update stored reputation
        building["reputation"] = max(0, building["reputation"] + reputation_change)
        renpy.log(f"Updated {building_name} reputation to {building['reputation']} after {event_result}")
