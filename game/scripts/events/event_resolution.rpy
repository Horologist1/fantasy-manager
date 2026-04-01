# event_resolution.rpy
# NOTE: apply_interaction_effects is defined in worker_interactions.rpy (full implementation
# with level scaling / flags). Do not redefine it here or the interaction level unlock system breaks.

init python:

    def render_event_text(event, result="success", extra_replacements=None):
        # Determine worker_name from the event; assume individual event.
        if hasattr(event.get("worker"), "get"):
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
        if hasattr(descriptions, "get"):
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
        """Adjust building reputation based on event outcome. Capped by building/manager level."""
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
        cap = get_building_reputation_cap(building)
        # Update and clamp to level cap (no growth above cap until level up)
        building["reputation"] = max(0, min(building["reputation"] + reputation_change, cap))
        renpy.log(f"Updated {building_name} reputation to {building['reputation']} after {event_result}")
