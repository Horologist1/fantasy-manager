# Tutorial Quest System - Main File
# This file contains the complete tutorial system for the game

# ===== VARIABLES SETUP =====
default tutorial_active = True
default current_objective = 1
default tutorial_skipped = False

# Initialize objective_just_completed in init block to survive Next Day
init python:
    if not hasattr(store, 'objective_just_completed'):
        store.objective_just_completed = 0
    if not hasattr(store, 'pending_objective_4_dialogue'):
        store.pending_objective_4_dialogue = False
    if not hasattr(store, 'objective_4_dialogue_shown'):
        store.objective_4_dialogue_shown = False
    if not hasattr(store, 'potion_purchased'):
        store.potion_purchased = False
    if not hasattr(store, 'potion_transferred'):
        store.potion_transferred = False
    if not hasattr(store, 'potion_used_on_worker'):
        store.potion_used_on_worker = False

# Add default declarations for tutorial variables to ensure global access
default potion_purchased = False
default potion_transferred = False
default potion_used_on_worker = False

# Objective completion tracking
default objective_1_complete = False
default objective_2_complete = False
default objective_3_complete = False
default objective_4_complete = False
default objective_5_complete = False
default objective_6_complete = False
default objective_7_complete = False
default objective_8_complete = False
default objective_9_complete = False
default objective_10_complete = False
default objective_11_complete = False
default objective_12_complete = False
default objective_13_complete = False
default objective_14_complete = False
default objective_15_complete = False
default objective_16_complete = False

# New tutorial flags for building progression
default building_upgraded_tutorial = False
default building_skill_bonus_increased_tutorial = False
default tutorial_friendly_chat_done = False

# Progress tracking
default workers_hired = 0
default building_1_type_set = False
default workers_assigned = False
default workers_assigned_count = 0
default buildings_owned = 1
default total_workers = 0
default objective_dialogue_triggered = False
default show_objective_dialogue = False

# New flags for extended objectives
default vengeance_path_chosen = False
default vengeance_path = ""  # "Blade" or "Shadow"

# Governor's Tension System
default governor_attention = 0  # 0-100, increases as player progresses
default governor_retaliation_done = False  # Has the retaliation event occurred?
default governor_tension_active = False  # Is the tension system active?
default days_since_last_tension_event = 0  # Track days without tension events (guarantee after 10)

# Objective content
default objective_titles = {
    1: "The First Gathering - Assembling Loyal Souls",
    2: "The Path Chosen - Establishing Thy Domain", 
    3: "The Deployment - Assigning Daily Duties",
    4: "The Foundation - Amassing Fortune's Favor",
    5: "The Mastery - Learning the Arts of Provision",
    6: "The Stronghold - Fortifying Thy Realm",
    7: "The Understanding - Knowing Thy Faithful",
    8: "The Grand Design - Expanding Thy Empire",
    9: "The Final Gambit - The Governor's Reckoning",
    10: "The Shadow's Wealth - Amassing the War Chest",
    11: "The Informant Network - Eyes in the Darkness",
    12: "The Arsenal of Vengeance - Gathering the Tools of War",
    13: "The Empire of Shadows - Expanding the Domain",
    14: "The Elite Guard - Forging the Inner Circle",
    15: "The Final Preparation - The Eve of Reckoning",
    16: "The Reckoning Begins - The Final Strike"
}

default objective_descriptions = {
    1: "If ever I am to raise the dynasty's empire from the ashes of ruination, then verily, I shall require the hands and hearts of loyal workers. Three workers should suffice to begin this grand endeavor - some may be bought with coin from the market square's bustling commerce, whilst others might be recruited through providence's chance encounters that may span several days, yet oft prove more skilled in their craft.",
    
    2: "The hour of decision draws nigh, wherein I must decree what manner of building type this hallowed place shall become. Perchance a brothel, where secrets flow as freely as wine and influence is currency? Mayhap a restaurant, where respectable coin may be earned through honest trade? Or shall it be an adventurer's guild, where muscle and steel forge connections of power? Each path doth offer different opportunities... and different means by which to gather the strength needed for what is to come.",
    
    3: "Each worker in my service doth possess their own gifts and talents, bestowed by fate and honed through experience. A wise lord doth employ his workers according to their greatest strengths, for 'tis through such wisdom that empires are built. I must assign three workers to their destined professions - for efficiency shall be the cornerstone upon which wealth is swiftly accumulated.",
    
    4: "Gold is the lifeblood of power, and power is the weapon I must wield. Five thousand coins should suffice to begin contemplating the expansion of my domain. Every transaction, every service rendered, every bargain struck brings me ever closer to the resources I shall require for the reckoning that approaches.",
    
    5: "The time has come to master the arts of item management and the care of those who serve. I must procure an energy potion from the merchant's stall, transfer it to one of my workers, and witness its effects. Through such endeavors shall I learn to tend to my workers' needs and employ items with wisdom and effectiveness. Yet I must remember: no remedy is truly necessary, for all workers regain their strength with each passing day and shall perform their duties. But with this energetic elixir, a worker may accomplish far more than a single task, turning the tide of fortune in my favor.",
    
    6: "The foundation of any lasting empire lies in its infrastructure and preparedness. I must enhance a building's level and its Building skill for the trials ahead. To elevate a building's level shall cost one thousand coins of the realm. Then, I must increase the building's Building skill bonus by ten measures, be they equipment, ingredients, or Hag Potions - whatever the establishment requires to weather the storms of fortune.",
    
    7: "The time has arrived to know the hearts and minds of those workers who have sworn themselves to my cause. A cordial discourse shall reveal their true nature, their motivations, and the depths of their loyalty. I should speak with any of my workers - beginning with gentle conversation to understand the souls who would follow me into darkness.",
    
    8: "Behold, the grand design reveals itself at last! Two buildings under my dominion, ten loyal workers in my service, and ten thousand coins to fuel my ambitions. With such resources at my command, I may at last move against the governor who destroyed all that was dear to me.",
    
    9: "Two paths diverge before me in this wood of vengeance: I may orchestrate the governor's final breath through shadow and steel, or I may corner the wretch with cunning theft and the chains of blackmail. Each road leads to justice, yet by different means shall it be achieved.",
    
    10: "To wage war against the shadow that haunts this city, I shall require resources beyond mere governance. Fifty thousand coins - a sum vast enough to fund an army, bribe informants, and purchase the tools of vengeance. Every coin earned brings me closer to the reckoning.",
    
    11: "Knowledge is power, and I must know mine enemy's every move. I require a network of informants - twenty loyal workers who can gather intelligence, spread rumors, and move unseen through the city's underbelly. Each soul I recruit strengthens my web of eyes and ears.",
    
    12: "Mere gold and information will not suffice - I must arm myself for the battles ahead. I seek three artifacts of power: a Binding Gem to break dark pacts, an Obsidian Blade to pierce enchanted armor, and an Enchanted Ring to grant my agents supernatural charm. These treasures shall be my weapons.",
    
    13: "To challenge the powers that rule from darkness, I must command an empire of mine own. Five buildings under my dominion, each a fortress of influence and a wellspring of resources. Through these strongholds, I shall project power across the city and fund the final campaign.",
    
    14: "For the trials ahead, I require not merely workers, but champions. I must cultivate an elite guard: three warriors of supreme combat prowess (Combat 80+), and two masters of cunning and charm (Clever or Charm 80+). These paragons shall be my sword and shield in the battles to come.",
    
    15: "All the pieces are in place, yet one final test remains. I must prove my empire's strength by achieving a single day's revenue of ten thousand coins - a demonstration that my operations run with ruthless efficiency. Only then shall I be ready to strike.",
    
    16: "The hour of vengeance is at hand. All preparations are complete - my wealth is vast, my network extensive, my arsenal deadly, my empire formidable, and my champions unmatched. Now I must choose the path of reckoning: shall I strike with overwhelming force, or with cunning subterfuge? The choice is mine, and the fate of my enemy hangs in the balance."
}

# ===== HELPER FUNCTIONS =====
init python:
    def get_current_objective_title():
        title = objective_titles.get(current_objective, "Unknown Objective")
        return f"Objective {current_objective}: {title}"
    
    def get_current_objective_description():
        return objective_descriptions.get(current_objective, "No description available.")
    
    def has_item_anywhere(item_id):
        """Check if item exists in manager or any worker inventory"""
        # Manager inventory can be tuples, lists, dicts, or strings
        if not hasattr(store, 'manager_inventory') or store.manager_inventory is None:
            store.manager_inventory = []
        
        # Check manager inventory
        for entry in store.manager_inventory:
            found = False
            if isinstance(entry, tuple):
                if len(entry) > 0 and entry[0] == item_id:
                    found = True
            elif isinstance(entry, list):
                # Handle list format: [item_id] or [item_id, quantity] or [item_id, quantity, equipped]
                if len(entry) > 0 and entry[0] == item_id:
                    found = True
            elif isinstance(entry, dict):
                # Handle old dict format for backwards compatibility
                if entry.get("item_id") == item_id:
                    found = True
            elif isinstance(entry, str):
                # Handle old string format for backwards compatibility
                if entry == item_id:
                    found = True
                # Handle string representation of list/tuple (e.g., "['obsidian_blade', 1, False]")
                elif entry.strip().startswith(('[', '(')) and item_id in entry:
                    # Try to safely parse the string representation
                    try:
                        # Use ast.literal_eval for safe evaluation
                        import ast
                        parsed = ast.literal_eval(entry)
                        if isinstance(parsed, (list, tuple)) and len(parsed) > 0 and parsed[0] == item_id:
                            found = True
                    except (ValueError, SyntaxError, ImportError):
                        # If parsing fails, check if item_id appears in the string with quotes
                        # This handles cases like "['obsidian_blade', 1, False]" or "('obsidian_blade', 1, False)"
                        if f"'{item_id}'" in entry or f'"{item_id}"' in entry:
                            found = True
            
            if found:
                renpy.log(f"DEBUG has_item_anywhere: Found {item_id} in manager_inventory as {type(entry).__name__}: {entry}")
                return True
        
        # Check worker inventories (also can be tuples, lists, dicts, or strings)
        for worker in store.workers:
            worker_inventory = worker.get("inventory", [])
            worker_name = worker.get("name", "Unknown")
            for entry in worker_inventory:
                found = False
                if isinstance(entry, tuple):
                    if len(entry) > 0 and entry[0] == item_id:
                        found = True
                elif isinstance(entry, list):
                    # Handle list format
                    if len(entry) > 0 and entry[0] == item_id:
                        found = True
                elif isinstance(entry, dict):
                    # Handle old dict format
                    if entry.get("item_id") == item_id:
                        found = True
                elif isinstance(entry, str):
                    # Handle old string format for backwards compatibility
                    if entry == item_id:
                        found = True
                    # Handle string representation of list/tuple (e.g., "['obsidian_blade', 1, False]")
                    elif entry.strip().startswith(('[', '(')) and item_id in entry:
                        # Try to safely parse the string representation
                        try:
                            # Use ast.literal_eval for safe evaluation
                            import ast
                            parsed = ast.literal_eval(entry)
                            if isinstance(parsed, (list, tuple)) and len(parsed) > 0 and parsed[0] == item_id:
                                found = True
                        except (ValueError, SyntaxError, ImportError):
                            # If parsing fails, check if item_id appears in the string with quotes
                            # This handles cases like "['obsidian_blade', 1, False]" or "('obsidian_blade', 1, False)"
                            if f"'{item_id}'" in entry or f'"{item_id}"' in entry:
                                found = True
                
                if found:
                    renpy.log(f"DEBUG has_item_anywhere: Found {item_id} in {worker_name}'s inventory as {type(entry).__name__}: {entry}")
                    return True
        
        renpy.log(f"DEBUG has_item_anywhere: {item_id} NOT FOUND in any inventory")
        return False
    
    def _objective_12_flag_name(item_id):
        return f"objective12_{item_id}_collected"
    
    def mark_objective_12_item_collected(item_id):
        if not hasattr(store, "event_flags") or store.event_flags is None:
            store.event_flags = {}
        store.event_flags[_objective_12_flag_name(item_id)] = True
    
    def has_objective_12_item_flag(item_id):
        return getattr(store, "event_flags", {}).get(_objective_12_flag_name(item_id), False)
    
    def sync_objective_12_flags_from_inventory():
        required_items = ["binding_gem", "obsidian_blade", "enchanted_ring"]
        for item_id in required_items:
            if has_item_anywhere(item_id):
                mark_objective_12_item_collected(item_id)
    
    def validate_objective_12_items():
        """
        Validate and fix items for objective 12 (binding gem quest).
        This function checks if the required items exist and logs detailed information.
        It's called when the player is on objective 12 to ensure items are properly tracked.
        """
        required_items = ["binding_gem", "obsidian_blade", "enchanted_ring"]
        
        renpy.log("=== OBJECTIVE 12 ITEM VALIDATION ===")
        
        # Ensure manager_inventory exists
        if not hasattr(store, 'manager_inventory') or store.manager_inventory is None:
            store.manager_inventory = []
            renpy.log("OBJECTIVE 12: manager_inventory was None, initialized to []")
        
        # Log current state
        renpy.log(f"OBJECTIVE 12: manager_inventory type: {type(store.manager_inventory)}, length: {len(store.manager_inventory)}")
        if len(store.manager_inventory) > 0:
            renpy.log(f"OBJECTIVE 12: manager_inventory items: {[str(item)[:50] for item in store.manager_inventory[:10]]}")
        
        # Check each required item
        for item_id in required_items:
            found = has_item_anywhere(item_id)
            renpy.log(f"OBJECTIVE 12: {item_id} - Found: {found}")
            
            if not found:
                # Item is missing - log detailed information
                renpy.log(f"OBJECTIVE 12: WARNING - {item_id} is MISSING!")
                
                # Check if it might be in manager_inventory but in wrong format
                found_in_manager = False
                for i, entry in enumerate(store.manager_inventory):
                    item_str = str(entry).lower()
                    if item_id.replace("_", " ") in item_str or item_id in item_str:
                        renpy.log(f"OBJECTIVE 12: Found potential match in manager_inventory at index {i}: {entry}")
                        found_in_manager = True
                        # Try to normalize string representations to actual lists
                        if isinstance(entry, str) and entry.strip().startswith(('[', '(')):
                            try:
                                import ast
                                parsed = ast.literal_eval(entry)
                                if isinstance(parsed, (list, tuple)) and len(parsed) > 0 and parsed[0] == item_id:
                                    # Convert to list format and replace in inventory
                                    store.manager_inventory[i] = list(parsed) if isinstance(parsed, tuple) else parsed
                                    renpy.log(f"OBJECTIVE 12: Normalized item at index {i} from string to list: {store.manager_inventory[i]}")
                            except (ValueError, SyntaxError, ImportError):
                                pass
                
                # Check worker inventories
                found_in_workers = False
                for worker in store.workers:
                    worker_name = worker.get("name", "Unknown")
                    worker_inventory = worker.get("inventory", [])
                    for entry in worker_inventory:
                        item_str = str(entry).lower()
                        if item_id.replace("_", " ") in item_str or item_id in item_str:
                            renpy.log(f"OBJECTIVE 12: Found potential match in {worker_name}'s inventory: {entry}")
                            found_in_workers = True
                
                if not found_in_manager and not found_in_workers:
                    renpy.log(f"OBJECTIVE 12: ERROR - {item_id} completely missing from all inventories!")
        
        # Sync persistent flags from inventory for older saves
        sync_objective_12_flags_from_inventory()

        renpy.log("=== END OBJECTIVE 12 VALIDATION ===")
    
    # Make function available in store
    store.validate_objective_12_items = validate_objective_12_items
    
    def count_workers_with_skill(skill_name, threshold):
        """Count workers with skill >= threshold (including bonuses and equipment)"""
        count = 0
        for w in store.workers:
            # Use calculate_skill_with_traits to include equipment bonuses and trait bonuses
            skill_value = _get_worker_skill_value(w, skill_name)
            if skill_value >= threshold:
                count += 1
        return count
    
    def get_current_objective_progress():
        if current_objective == 1:
            return f"Progress: {workers_hired}/3 Workers Hired"
        elif current_objective == 2:
            if building_1_type_set:
                return "Progress: Building type hath been chosen ->"
            else:
                return "Progress: Building type remains unselected"
        elif current_objective == 3:
            if workers_assigned_count >= 3:
                return "Progress: 3 workers assigned to their duties ->"
            else:
                return f"Progress: {workers_assigned_count}/3 workers assigned to professions"
        elif current_objective == 4:
            return f"Progress: {money}/5000 Coins"
        elif current_objective == 5:
            if store.potion_purchased and store.potion_transferred and store.potion_used_on_worker:
                return "Progress: Energy potion's power hath been witnessed ->"
            elif store.potion_purchased and store.potion_transferred:
                return "Progress: 2/3 - Transfer potion to worker ->, Use potion on worker"
            elif store.potion_purchased:
                return "Progress: 1/3 - Buy energy potion ->, Transfer to worker, Use on worker"
            else:
                return "Progress: 0/3 - Buy energy potion from shop, Transfer to worker, Use on worker"
        elif current_objective == 6:
            if store.building_upgraded_tutorial and store.building_skill_bonus_increased_tutorial:
                return "Progress: Building level enhanced ->, Building skill bonus increased ->"
            elif store.building_upgraded_tutorial:
                return "Progress: 1/2 - Building level enhanced ->, Increase Building skill bonus"
            elif store.building_skill_bonus_increased_tutorial:
                return "Progress: 1/2 - Building skill bonus increased ->, Enhance building level"
            else:
                return "Progress: 0/2 - Upgrade building level, Increase Building skill bonus"
        elif current_objective == 7:
            return "Progress: Have a Friendly Chat with any worker\nGuidance: Workers -> Details -> Interactions -> Friendly Chat"
        elif current_objective == 8:
            actual_buildings = len(store.owned_buildings) if hasattr(store, 'owned_buildings') else buildings_owned
            actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
            return f"Progress:\n- Buildings: {actual_buildings}/2\n- Workers: {actual_workers}/10\n- Coins: {money}/10000"
        elif current_objective == 9:
            if store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False):
                branch = "Assassination" if store.event_flags.get("branch_assassination", False) else "Blackmail"
                return f"Progress: Path chosen -> {branch}\nMark 'Complete' to advance"
            else:
                return "Progress: Choose your path in the Journal"
        elif current_objective == 10:
            return f"Progress: {money}/50000 Coins"
        elif current_objective == 11:
            actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
            return f"Progress: {actual_workers}/20 Workers"
        elif current_objective == 12:
            # Validate and fix items when checking objective 12 progress
            validate_objective_12_items()
            
            sync_objective_12_flags_from_inventory()
            has_binding_gem = has_objective_12_item_flag("binding_gem")
            has_obsidian_blade = has_objective_12_item_flag("obsidian_blade")
            has_enchanted_ring = has_objective_12_item_flag("enchanted_ring")
            items_collected = sum([has_binding_gem, has_obsidian_blade, has_enchanted_ring])
            check_gem = "✓" if has_binding_gem else "✗"
            check_blade = "✓" if has_obsidian_blade else "✗"
            check_ring = "✓" if has_enchanted_ring else "✗"
            # Debug logging
            renpy.log(f"DEBUG Objective 12: binding_gem={has_binding_gem}, obsidian_blade={has_obsidian_blade}, enchanted_ring={has_enchanted_ring}")
            renpy.log(f"DEBUG Objective 12: manager_inventory sample={str(store.manager_inventory[:3]) if len(store.manager_inventory) > 0 else 'EMPTY'}")
            return f"Progress: {items_collected}/3 Artifacts\n- Binding Gem: {check_gem}\n- Obsidian Blade: {check_blade}\n- Enchanted Ring: {check_ring}"
        elif current_objective == 13:
            actual_buildings = len(store.owned_buildings) if hasattr(store, 'owned_buildings') else buildings_owned
            return f"Progress: {actual_buildings}/5 Buildings"
        elif current_objective == 14:
            warriors = count_workers_with_skill("Combat", 80)
            # Count unique workers (a worker can't be counted twice)
            # Use calculate_skill_with_traits to include equipment bonuses
            unique_agents = 0
            for w in store.workers:
                clever = _get_worker_skill_value(w, "Clever")
                charm = _get_worker_skill_value(w, "Charm")
                if clever >= 80 or charm >= 80:
                    unique_agents += 1
            warriors_ready = "✓" if warriors >= 3 else "✗"
            agents_ready = "✓" if unique_agents >= 2 else "✗"
            return f"Progress (Requires BOTH):\n- Elite Warriors (Combat 80+): {warriors}/3 {warriors_ready}\n- Elite Agents (Clever/Charm 80+): {unique_agents}/2 {agents_ready}"
        elif current_objective == 15:
            if store.event_flags.get("daily_revenue_10k_achieved", False):
                return "Progress: Daily revenue goal achieved (10,000 coins) ->"
            else:
                return "Progress: Achieve 10,000 coins revenue in a single day\nTip: Upgrade buildings, assign skilled workers, increase Building skill"
        elif current_objective == 16:
            if store.vengeance_path_chosen:
                return f"Progress: Path chosen -> {store.vengeance_path}\nMark 'Complete' to begin the final strike"
            else:
                combat_count = count_workers_with_skill("Combat", 70)
                clever_count = count_workers_with_skill("Clever", 70)
                blade_ready = "[Ready]" if combat_count >= 5 else "[Not Ready]"
                shadow_ready = "[Ready]" if clever_count >= 5 else "[Not Ready]"
                return f"Progress: Choose your path of vengeance\n- Path of the Blade (Combat 70+): {combat_count}/5 {blade_ready}\n- Path of the Shadow (Clever 70+): {clever_count}/5 {shadow_ready}\nTip: Check out shops for items to boost skills!"
        else:
            return "Progress: The path remains shrouded in mystery"

    def _get_worker_skill_value(worker, skill_name):
        """Get worker skill value including equipment bonuses for tutorial checks."""
        try:
            # Use calculate_skill_with_traits to include equipment bonuses
            return calculate_skill_with_traits(worker, skill_name)
        except Exception:
            return 0

    def has_team_assassination():
        # Needs 3 workers with >=70 in Combat or Craft
        qualifying = 0
        for w in store.workers:
            if _get_worker_skill_value(w, "Combat") >= 70 or _get_worker_skill_value(w, "Craft") >= 70:
                qualifying += 1
        return qualifying >= 3

    def has_team_blackmail():
        # Needs 1 with >=70 Clever or >=70 Charm, and two OTHER workers with >=70 Charm
        charm_workers = [w for w in store.workers if _get_worker_skill_value(w, "Charm") >= 70]
        clever_workers = [w for w in store.workers if _get_worker_skill_value(w, "Clever") >= 70]
        if len(charm_workers) >= 3:
            # one can count as the single (Charm) and two others as the additional two
            return True
        if len(charm_workers) >= 2:
            # need a distinct worker with Clever >=70 not in the two charm picks
            charm_set = set(id(w) for w in charm_workers[:2])
            for w in clever_workers:
                if id(w) not in charm_set:
                    return True
        return False
    
    def can_complete_objective_8():
        """Check if objective 8 conditions are met"""
        # Check prerequisite: objective 7 must be complete
        if not getattr(store, 'objective_7_complete', False):
            return False
        actual_buildings = len(store.owned_buildings) if hasattr(store, 'owned_buildings') else buildings_owned
        actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
        return actual_buildings >= 2 and actual_workers >= 10 and money >= 10000
    
    def can_complete_objective_10():
        """Check if objective 10 conditions are met"""
        # Check prerequisite: objective 9 must be complete
        if not getattr(store, 'objective_9_complete', False):
            return False
        return money >= 50000
    
    def can_complete_objective_11():
        """Check if objective 11 conditions are met"""
        # Check prerequisite: objective 10 must be complete
        if not getattr(store, 'objective_10_complete', False):
            return False
        actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
        return actual_workers >= 20
    
    def can_complete_objective_12():
        """Check if objective 12 conditions are met"""
        # Check prerequisite: objective 11 must be complete
        objective_11_complete = getattr(store, 'objective_11_complete', False)
        if not objective_11_complete:
            renpy.log(f"DEBUG Objective 12: Objective 11 not complete (objective_11_complete={objective_11_complete})")
            return False
        
        # Validate items before checking
        validate_objective_12_items()
        sync_objective_12_flags_from_inventory()
        
        has_binding_gem = has_objective_12_item_flag("binding_gem")
        has_obsidian_blade = has_objective_12_item_flag("obsidian_blade")
        has_enchanted_ring = has_objective_12_item_flag("enchanted_ring")
        
        renpy.log(f"DEBUG Objective 12: binding_gem={has_binding_gem}, obsidian_blade={has_obsidian_blade}, enchanted_ring={has_enchanted_ring}")
        renpy.log(f"DEBUG Objective 12: manager_inventory length={len(getattr(store, 'manager_inventory', []))}")
        renpy.log(f"DEBUG Objective 12: manager_inventory sample={str(getattr(store, 'manager_inventory', [])[:5])}")
        
        result = (has_binding_gem and has_obsidian_blade and has_enchanted_ring)
        renpy.log(f"DEBUG Objective 12: can_complete={result}")
        return result
    
    def can_complete_objective_13():
        """Check if objective 13 conditions are met"""
        # Check prerequisite: objective 12 must be complete
        if not getattr(store, 'objective_12_complete', False):
            return False
        actual_buildings = len(store.owned_buildings) if hasattr(store, 'owned_buildings') else buildings_owned
        return actual_buildings >= 5
    
    def can_complete_objective_14():
        """Check if objective 14 conditions are met"""
        # Check prerequisite: objective 13 must be complete
        if not getattr(store, 'objective_13_complete', False):
            return False
        warriors = count_workers_with_skill("Combat", 80)
        unique_agents = 0
        for w in store.workers:
            clever = _get_worker_skill_value(w, "Clever")
            charm = _get_worker_skill_value(w, "Charm")
            if clever >= 80 or charm >= 80:
                unique_agents += 1
        return warriors >= 3 and unique_agents >= 2
    
    def can_complete_objective_15():
        """Check if objective 15 conditions are met"""
        # Check prerequisite: objective 14 must be complete
        if not getattr(store, 'objective_14_complete', False):
            return False
        return store.event_flags.get("daily_revenue_10k_achieved", False)
    
    def check_existing_building_upgrades():
        """Check if any buildings are already upgraded when reaching objective 6"""
        if not hasattr(store, 'tutorial_active') or not store.tutorial_active:
            return
        if not hasattr(store, 'current_objective') or store.current_objective != 6:
            return
        
        # Check if available_buildings exists
        if not hasattr(store, 'available_buildings'):
            renpy.log("DEBUG: check_existing_building_upgrades - available_buildings not found")
            return
        
        # Check all owned buildings for upgrades
        owned_buildings = getattr(store, 'owned_buildings', [])
        if not owned_buildings:
            renpy.log("DEBUG: check_existing_building_upgrades - no owned buildings")
            return
        
        for building_name in owned_buildings:
            if building_name not in store.available_buildings:
                continue
            
            building = store.available_buildings[building_name]
            
            # Check if building level is > 1 (upgraded)
            if building.get("base_level", 1) > 1:
                if not store.building_upgraded_tutorial:
                    renpy.log(f"DEBUG: Found already upgraded building: {building_name} (level {building.get('base_level', 1)})")
                    store.building_upgraded_tutorial = True
            
            # Check if building has skill bonus > 0
            if building.get("skill_bonus", 0) > 0:
                if not store.building_skill_bonus_increased_tutorial:
                    renpy.log(f"DEBUG: Found already upgraded building skill: {building_name} (bonus {building.get('skill_bonus', 0)})")
                    store.building_skill_bonus_increased_tutorial = True
    
    # ===== GOVERNOR'S TENSION SYSTEM =====
    
    def update_governor_attention():
        """Update governor's attention based on current objective progress"""
        current_obj = getattr(store, 'current_objective', 1)
        
        # Calculate attention based on objective
        if current_obj < 8:
            store.governor_attention = 0
            store.governor_tension_active = False
        elif current_obj == 8:
            store.governor_attention = 10
            store.governor_tension_active = False
        elif current_obj == 9:
            store.governor_attention = 30
            store.governor_tension_active = True
        elif current_obj == 10:
            store.governor_attention = 50
        elif current_obj == 11:
            store.governor_attention = 60
        elif current_obj == 12:
            store.governor_attention = 70
        elif current_obj == 13:
            store.governor_attention = 80
        elif current_obj == 14:
            store.governor_attention = 90
        elif current_obj == 15:
            store.governor_attention = 95
        elif current_obj >= 16:
            store.governor_attention = 100
        
        renpy.log(f"TENSION: Governor attention updated to {store.governor_attention} (objective {current_obj})")
    
    def check_governor_retaliation():
        """Check and trigger the governor's retaliation event when reaching objective 9"""
        if store.governor_retaliation_done:
            return False
        
        # Only trigger when player has chosen a path (assassination or blackmail)
        # Also check if objective 9 is complete (player may have completed it before this system was added)
        has_path = store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False)
        obj_9_complete = getattr(store, 'objective_9_complete', False)
        
        # Trigger if path is chosen OR if objective 9 is complete (for players who completed it before)
        if has_path or (obj_9_complete and store.current_objective >= 9):
            store.governor_retaliation_done = True
            store.governor_tension_active = True
            renpy.log(f"TENSION: Governor retaliation check - has_path={has_path}, obj_9_complete={obj_9_complete}, current_obj={store.current_objective}")
            return True
        return False
    
    def process_governor_tension_event():
        """Process a random tension event from the governor (called during daily events)"""
        import random
        
        # Only active from objective 10 onwards
        if not store.governor_tension_active or store.current_objective < 10:
            return None
        
        # Quest completed - no more tension events
        if store.current_objective > 16 or store.event_flags.get("quest_complete", False):
            store.governor_tension_active = False
            return None
        
        # Track days since last tension event (guarantee event after 10 days)
        if not hasattr(store, 'days_since_last_tension_event'):
            store.days_since_last_tension_event = 0
        
        store.days_since_last_tension_event += 1
        
        # Guarantee an event after 10 days without one
        if store.days_since_last_tension_event >= 10:
            renpy.log(f"TENSION: Guaranteed event after {store.days_since_last_tension_event} days without one")
            store.days_since_last_tension_event = 0
            # Choose event type
            event_types = ["poison", "sabotage", "spy"]
            event_type = random.choice(event_types)
            renpy.log(f"TENSION: Governor tension event triggered (guaranteed): {event_type}")
            return event_type
        
        # Calculate probability based on attention (max 25% chance at 100 attention, increased from 15%)
        probability = store.governor_attention / 100.0 * 0.25
        
        renpy.log(f"TENSION: Checking for event - attention: {store.governor_attention}, probability: {probability:.2%}, days since last: {store.days_since_last_tension_event}")
        
        roll = random.random()
        if roll > probability:
            renpy.log(f"TENSION: No event today (rolled {roll:.3f} > {probability:.3f})")
            return None  # No event today
        
        # Event triggered - reset counter
        store.days_since_last_tension_event = 0
        
        # Choose event type
        event_types = ["poison", "sabotage", "spy"]
        event_type = random.choice(event_types)
        
        renpy.log(f"TENSION: Governor tension event triggered: {event_type}")
        return event_type
    
    def resolve_governor_tension():
        """Called when the governor storyline ends - removes fear traits from workers"""
        store.governor_tension_active = False
        store.event_flags["quest_complete"] = True
        
        # Remove "Shaken by the Governor" from all workers (Poisoned expires naturally or via antidote)
        traits_to_remove = ["Shaken by the Governor"]
        workers_healed = []
        
        for worker in store.workers:
            worker_traits = worker.get("traits", [])
            for trait_name in traits_to_remove:
                if trait_name in worker_traits:
                    remove_trait_safe(worker, trait_name)
                    if worker["name"] not in workers_healed:
                        workers_healed.append(worker["name"])
        
        renpy.log(f"TENSION: Governor storyline resolved. Healed workers: {workers_healed}")
        return workers_healed
    
    def apply_governor_poison_event():
        """Apply poison effect to a random worker"""
        import random
        
        if not store.workers or len(store.workers) == 0:
            return None
        
        # Choose a random worker who isn't already poisoned
        available_workers = [w for w in store.workers if "Poisoned" not in w.get("traits", [])]
        if not available_workers:
            return None
        
        victim = random.choice(available_workers)
        
        # Apply Poisoned and Shaken traits
        add_trait_with_duration(victim, "Poisoned", 7)
        add_trait_with_duration(victim, "Shaken by the Governor", 0)  # Permanent until quest ends
        
        # Also deal some immediate health damage
        victim["health"] = max(1, victim["health"] - 10)
        
        renpy.log(f"TENSION: {victim['name']} has been poisoned!")
        return victim["name"]
    
    def apply_governor_sabotage_event():
        """Apply sabotage effect to a random building"""
        import random
        
        if not store.owned_buildings or len(store.owned_buildings) == 0:
            return None
        
        # Choose a random building
        building_name = random.choice(list(store.owned_buildings))
        building = store.available_buildings.get(building_name)
        
        if not building:
            return None
        
        # Reduce building skill bonus temporarily (stored in event_flags)
        sabotage_key = f"sabotage_{building_name}"
        store.event_flags[sabotage_key] = store.current_day
        
        # Reduce skill bonus (will be restored after 3 days)
        old_bonus = building.get("skill_bonus", 0)
        building["skill_bonus"] = max(0, old_bonus - 10)
        
        renpy.log(f"TENSION: {building_name} has been sabotaged! Skill bonus reduced.")
        return building_name
    
    def apply_governor_spy_event():
        """Apply spy effect - steal some money"""
        import random
        
        # Steal 5-15% of current money
        steal_percent = random.uniform(0.05, 0.15)
        stolen = int(store.money * steal_percent)
        stolen = min(stolen, 2000)  # Cap at 2000
        stolen = max(stolen, 100)   # Minimum 100 if player has money
        
        if store.money < stolen:
            stolen = store.money // 2
        
        if stolen <= 0:
            return None
        
        store.money -= stolen
        
        renpy.log(f"TENSION: Governor's spy stole ${stolen}!")
        return stolen
    
    # Make governor functions available in store (after all functions are defined)
    store.check_governor_retaliation = check_governor_retaliation
    store.update_governor_attention = update_governor_attention
    store.process_governor_tension_event = process_governor_tension_event
    
    def jump_to_ending():
        """Jump to the appropriate ending based on chosen path"""
        if store.event_flags.get("branch_assassination", False):
            renpy.log("DEBUG: Jumping to assassination ending")
            renpy.jump("show_ending_assassination")
        elif store.event_flags.get("branch_blackmail", False):
            renpy.log("DEBUG: Jumping to blackmail ending")
            renpy.jump("show_ending_blackmail")
        else:
            # Fallback: if no branch was chosen (shouldn't happen), default to assassination
            renpy.log("WARNING: No branch chosen, defaulting to assassination ending")
            renpy.jump("show_ending_assassination")
    
    def check_objective_completion():
        global current_objective, tutorial_active
        global objective_1_complete, objective_2_complete, objective_3_complete, objective_4_complete
        global objective_5_complete, objective_6_complete, objective_7_complete, objective_8_complete
        global objective_9_complete, objective_10_complete, objective_11_complete, objective_12_complete
        global objective_13_complete, objective_14_complete, objective_15_complete, objective_16_complete
        global workers_hired, building_1_type_set, workers_assigned, money, buildings_owned, total_workers
        global objective_just_completed, workers_assigned_count
        
        renpy.log(f"DEBUG: check_objective_completion called - tutorial_active: {tutorial_active}, current_objective: {current_objective}")
        
        if not tutorial_active:
            renpy.log("DEBUG: Tutorial not active, returning")
            return
        
        # Recalculate workers_assigned_count based on workers WITH PROFESSIONS assigned
        def recalculate_workers_assigned_count():
            count = 0
            for building_name, building_data in available_buildings.items():
                if building_data.get("owned", False):
                    servant_jobs = building_data.get("servant_jobs", {})
                    for worker_name, job_id in servant_jobs.items():
                        job_str = str(job_id).lower() if job_id else ""
                        if job_id and job_str != "unassigned" and job_str != "":
                            count += 1
            return count
        
        # Always update workers_assigned_count to reflect actual state when checking objectives
        # This ensures accuracy even if workers were assigned before reaching objective 3
        actual_count = recalculate_workers_assigned_count()
        if actual_count != workers_assigned_count:
            renpy.log(f"DEBUG: workers_assigned_count was {workers_assigned_count}, updating to {actual_count} based on actual assignments")
        workers_assigned_count = actual_count
        
        # Helper function to check if previous objective is complete
        def is_previous_objective_complete(obj_num):
            if obj_num == 1:
                return True  # First objective has no prerequisite
            prev_obj_complete = getattr(store, f'objective_{obj_num - 1}_complete', False)
            return prev_obj_complete
        
        # Objectives 1-7: Auto-complete with prerequisite checks
        if current_objective == 1 and is_previous_objective_complete(1) and workers_hired >= 3 and not objective_1_complete:
            renpy.log("DEBUG: Objective 1 completed!")
            objective_1_complete = True
            current_objective = 2
            renpy.call_in_new_context("show_objective_1_dialogue")
            # Si el tipo de edificio ya estaba establecido, completar el objetivo 2 inmediatamente
            if building_1_type_set and not objective_2_complete:
                renpy.log("DEBUG: Building type already set, completing objective 2 immediately")
                objective_2_complete = True
                current_objective = 3
                renpy.call_in_new_context("show_objective_2_dialogue")
            
        elif current_objective == 2 and is_previous_objective_complete(2) and building_1_type_set and not objective_2_complete:
            renpy.log("DEBUG: Objective 2 completed!")
            objective_2_complete = True
            current_objective = 3
            renpy.call_in_new_context("show_objective_2_dialogue")
            # Recalculate workers_assigned_count before checking objective 3
            actual_count = recalculate_workers_assigned_count()
            workers_assigned_count = actual_count
            renpy.log(f"DEBUG: After objective 2, recalculated workers_assigned_count: {workers_assigned_count}")
            # Check if objective 3 can be completed immediately after objective 2
            if workers_assigned_count >= 3 and not objective_3_complete:
                renpy.log(f"DEBUG: Objective 3 can be completed immediately after objective 2! (workers_assigned_count={workers_assigned_count})")
                objective_3_complete = True
                current_objective = 4
                renpy.call_in_new_context("show_objective_3_dialogue")
                # Check if objective 4 can be completed immediately after objective 3
                if money >= 5000 and not objective_4_complete:
                    renpy.log(f"DEBUG: Objective 4 can be completed immediately after objective 3! (money={money})")
                    objective_4_complete = True
                    current_objective = 5
                    renpy.log("DEBUG: About to show objective 4 dialogue (immediate after obj 3)")
                    # Set flag to show dialogue - will be checked in tavern_screen
                    store.pending_objective_4_dialogue = True
                    # Try to show immediately, but if we're in a context that doesn't allow it, 
                    # the flag will ensure it shows when returning to tavern_screen
                    renpy.call_in_new_context("show_objective_4_dialogue")
                    store.pending_objective_4_dialogue = False  # Clear flag if dialogue was shown
            
        elif current_objective == 3 and is_previous_objective_complete(3) and workers_assigned_count >= 3 and not objective_3_complete:
            renpy.log("DEBUG: Objective 3 completed!")
            objective_3_complete = True
            current_objective = 4
            renpy.call_in_new_context("show_objective_3_dialogue")
            # Check if objective 4 can be completed immediately after objective 3
            if money >= 5000 and not objective_4_complete:
                renpy.log(f"DEBUG: Objective 4 can be completed immediately after objective 3! (money={money})")
                objective_4_complete = True
                current_objective = 5
                renpy.log("DEBUG: About to show objective 4 dialogue (immediate after obj 3)")
                # Set flag to show dialogue - will be checked in tavern_screen
                store.pending_objective_4_dialogue = True
                # Try to show immediately, but if we're in a context that doesn't allow it, 
                # the flag will ensure it shows when returning to tavern_screen
                renpy.call_in_new_context("show_objective_4_dialogue")
                store.pending_objective_4_dialogue = False  # Clear flag if dialogue was shown
            
        # Objective 4: Can complete if objective 3 is done and money >= 5000
        # This check works even if current_objective has advanced past 4
        # Use store.money to ensure we get the correct value
        elif objective_3_complete and getattr(store, 'money', money) >= 5000 and not objective_4_complete:
            store_money = getattr(store, 'money', money)
            renpy.log(f"DEBUG: Objective 4 completed! (money={store_money}, objective_3_complete={objective_3_complete}, current_objective={current_objective})")
            objective_4_complete = True
            # Only advance current_objective if we're still on objective 4 or earlier
            if current_objective <= 4:
                current_objective = 5
            # Always show the dialogue when objective 4 is completed
            renpy.log("DEBUG: About to show objective 4 dialogue")
            # Set flag to show dialogue - will be checked in tavern_screen
            store.pending_objective_4_dialogue = True
            # Try to show immediately, but if we're in a context that doesn't allow it, 
            # the flag will ensure it shows when returning to tavern_screen
            renpy.call_in_new_context("show_objective_4_dialogue")
            store.pending_objective_4_dialogue = False  # Clear flag if dialogue was shown
            
        elif current_objective == 5 and is_previous_objective_complete(5) and store.potion_purchased and store.potion_transferred and store.potion_used_on_worker and not objective_5_complete:
            renpy.log("DEBUG: Objective 5 completed!")
            objective_5_complete = True
            current_objective = 6
            check_existing_building_upgrades()  # Check if buildings are already upgraded
            renpy.call_in_new_context("show_objective_5_dialogue")
            
        elif current_objective == 6 and is_previous_objective_complete(6) and store.building_upgraded_tutorial and store.building_skill_bonus_increased_tutorial and not store.objective_6_complete:
            renpy.log("DEBUG: Objective 6 completed!")
            store.objective_6_complete = True
            current_objective = 7
            renpy.call_in_new_context("show_objective_6_outro")
            
        elif current_objective == 7 and is_previous_objective_complete(7) and store.tutorial_friendly_chat_done and not objective_7_complete:
            renpy.log("DEBUG: Objective 7 completed!")
            objective_7_complete = True
            current_objective = 8
            renpy.call_in_new_context("show_objective_7_dialogue")

        # Objectives 8+: Manual completion only (no auto-completion)
        # These objectives will only be marked complete via "MARK AS COMPLETE" button in journal
        # We still check conditions here to enable the button, but don't auto-advance


# ===== WRAPPER FUNCTION FOR GLOBAL ACCESS =====
init python:
    def check_tutorial_objective():
        """Wrapper function to call check_objective_completion from anywhere"""
        check_objective_completion()



# ===== JOURNAL SCREEN =====
screen journal_panel():
    modal True
    zorder 200
    on "show" action [Function(check_existing_building_upgrades), Function(check_objective_completion)]
    
    # Background overlay matching building selection
    add Solid("#000000dd")
    
    # Main content frame sized similarly to Building_select_global / building_selection
    frame:
        xalign 0.35  # Left of center for visible left margin
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (40, 40)  # Slightly reduced vertical padding
        xsize 720  # Increased width
        ysize 720  # Increased height for more verticality
        
        vbox:
            spacing 15  # Match shop_selection spacing
            null height 15  # Push JOURNAL title down a bit
            label "JOURNAL" xalign 0.5 style "header_style"
            null height 10  # Less space after JOURNAL title
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 480
                xsize 590
                xoffset 40
                yoffset 25
                has vbox
                spacing 10

                if tutorial_active:
                    text "[get_current_objective_title()]":
                        xsize 520
                        size font_size(32)
                        color "#7a4b2a"

                    text "[get_current_objective_description()]":
                        xsize 520
                        size font_size(24)
                        color "#7a4b2a"
                        text_align 0.0

                    null height 15

                    text "[get_current_objective_progress()]":
                        xsize 520
                        size font_size(22)
                        color "#6b6528"

                    null height 20

                    # Tutorial quick access links for objectives 1-7
                    if current_objective == 1:
                        text "Tutorial:":
                            size font_size(24)
                            color "#7a4b2a"
                        textbutton "Map > Buy Servants":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("map_screen")]
                    
                    elif current_objective == 2:
                        text "Tutorial:":
                            size font_size(24)
                            color "#7a4b2a"
                        textbutton "Manage Buildings > Select building > Building Type":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("Building_select_global")]
                    
                    elif current_objective == 3:
                        text "Tutorial:":
                            size font_size(24)
                            color "#7a4b2a"
                        textbutton "Workers > Worker Name > Assign Building > Select Job":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]
                    
                    elif current_objective == 4:
                        text "Tutorial:":
                            size font_size(24)
                            color "#7a4b2a"
                        textbutton "Tavern > Next Day":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("tavern")]
                    
                    elif current_objective == 5:
                        text "Tutorial:":
                            size font_size(24)
                            color "#7a4b2a"
                        textbutton "Map > Shop":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("map_screen")]
                        textbutton "Workers > Worker Name > Details > Inventory":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]
                        text "Tip: For this tutorial, purchase the potion from the shop and transfer it manually. In the future, you can use potions directly from Manage Workers or Manage Buildings." size font_size(20) color "#6b6528"
                    
                    elif current_objective == 6:
                        text "Tutorial:":
                            size font_size(24)
                            color "#7a4b2a"
                        textbutton "Manage Buildings > Select building > Upgrade Building":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("Building_select_global")]
                        textbutton "Manage Buildings > Select building > Skill Bonus":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("Building_select_global")]
                        text "Tip: Each +10 Building skill bonus costs $100/day." size font_size(20) color "#6b6528"
                    
                    elif current_objective == 7:
                        text "Tutorial:":
                            size font_size(24)
                            color "#7a4b2a"
                        textbutton "Workers > Worker Name > Details > Interactions > Friendly Chat":
                            xsize 520
                            text_size font_size(22)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]

                    # MARK AS COMPLETE buttons for objectives 8+
                    if current_objective == 8:
                        $ can_complete_8 = can_complete_objective_8()
                        if can_complete_8:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_8_complete", True),
                                    SetVariable("current_objective", 9),
                                    Function(lambda: setattr(store, 'event_flags', getattr(store, 'event_flags', {}))),
                                    Function(lambda: store.event_flags.update({'objective_8_complete': True})),
                                    Hide("journal_panel"),
                                    Jump("show_objective_8_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 520
                                size font_size(20)
                                color "#6b6528"
                    
                    elif current_objective == 10:
                        $ can_complete_10 = can_complete_objective_10()
                        if can_complete_10:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_10_complete", True),
                                    SetVariable("current_objective", 11),
                                    Hide("journal_panel"),
                                    Jump("show_objective_10_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 520
                                size font_size(20)
                                color "#6b6528"
                    
                    elif current_objective == 11:
                        $ can_complete_11 = can_complete_objective_11()
                        if can_complete_11:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_11_complete", True),
                                    SetVariable("current_objective", 12),
                                    Hide("journal_panel"),
                                    Jump("show_objective_11_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 520
                                size font_size(20)
                                color "#6b6528"
                    
                    elif current_objective == 12:
                        $ can_complete_12 = can_complete_objective_12()
                        if can_complete_12:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_12_complete", True),
                                    SetVariable("current_objective", 13),
                                    Hide("journal_panel"),
                                    Jump("show_objective_12_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 520
                                size font_size(20)
                                color "#6b6528"
                    
                    elif current_objective == 13:
                        $ can_complete_13 = can_complete_objective_13()
                        if can_complete_13:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_13_complete", True),
                                    SetVariable("current_objective", 14),
                                    Hide("journal_panel"),
                                    Jump("show_objective_13_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 520
                                size font_size(20)
                                color "#6b6528"
                    
                    elif current_objective == 14:
                        $ can_complete_14 = can_complete_objective_14()
                        if can_complete_14:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_14_complete", True),
                                    SetVariable("current_objective", 15),
                                    Hide("journal_panel"),
                                    Jump("show_objective_14_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 520
                                size font_size(20)
                                color "#6b6528"
                    
                    elif current_objective == 15:
                        $ can_complete_15 = can_complete_objective_15()
                        if can_complete_15:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_15_complete", True),
                                    SetVariable("current_objective", 16),
                                    Hide("journal_panel"),
                                    Jump("show_objective_15_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 520
                                size font_size(20)
                                color "#6b6528"
                    
                    elif current_objective == 9:
                        null height 10
                        text "Choose Your Gambit:" size font_size(24) color "#7a4b2a" xalign 0.5
                        null height 15
                        
                        # Calculate requirements dynamically
                        $ can_assassinate = has_team_assassination()
                        $ can_blackmail = has_team_blackmail()
                        
                        # Assassination path button
                        frame:
                            xsize 560
                            background Solid("#7a4b2a")
                            padding (15, 15)
                            margin (5, 5)
                            textbutton "Plan the Governor's Death\n(requires 3 with 70+ Combat or Magic)":
                                xsize 530
                                text_size font_size(24)
                                text_color "#ffffff"
                                text_hover_color "#f4c594"
                                action [
                                    Function(lambda: setattr(store, 'event_flags', getattr(store, 'event_flags', {}))),
                                    If(can_assassinate,
                                        [Function(lambda: store.event_flags.update({'branch_assassination': True})),
                                         Function(check_objective_completion)],
                                        None)
                                ]
                                sensitive can_assassinate
                        
                        null height 2
                        
                        # Blackmail path button
                        frame:
                            xsize 560
                            background Solid("#7a4b2a")
                            padding (15, 15)
                            margin (5, 5)
                            textbutton "Heist and Blackmail\n(requires 1 with 70+ Clever/Charm and 2 with 70+ Charm)":
                                xsize 530
                                text_size font_size(24)
                                text_color "#ffffff"
                                text_hover_color "#f4c594"
                                action [
                                    Function(lambda: setattr(store, 'event_flags', getattr(store, 'event_flags', {}))),
                                    If(can_blackmail,
                                        [Function(lambda: store.event_flags.update({'branch_blackmail': True})),
                                         Function(check_objective_completion)],
                                        None)
                                ]
                                sensitive can_blackmail
                        
                        null height 10
                        text "Tip: Check out shops for items to boost skills!" size font_size(18) color "#6b6528" italic True
                        
                        if store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False):
                            null height 15
                            textbutton "MARK COMPLETE":
                                xsize 520
                                text_size font_size(24)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_9_complete", True),
                                    SetVariable("current_objective", 10),
                                    Hide("journal_panel"),
                                    Jump("show_objective_9_dialogue")
                                ]
                    
                    elif current_objective == 16:
                        text "Choose Your Path of Vengeance:" size font_size(24) color "#7a4b2a"
                        
                        $ combat_count = count_workers_with_skill("Combat", 70)
                        $ clever_count = count_workers_with_skill("Clever", 70)
                        
                        textbutton "Path of the Blade - Strike with overwhelming force (requires 5 with Combat 70+)":
                            xsize 520
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                If(combat_count >= 5,
                                    [SetVariable("vengeance_path_chosen", True),
                                     SetVariable("vengeance_path", "Blade")],
                                    None)
                            ]
                        
                        textbutton "Path of the Shadow - Strike with cunning subterfuge (requires 5 with Clever 70+)":
                            xsize 520
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                If(clever_count >= 5,
                                    [SetVariable("vengeance_path_chosen", True),
                                     SetVariable("vengeance_path", "Shadow")],
                                    None)
                            ]
                        
                        if store.vengeance_path_chosen:
                            null height 15
                            # Determine which ending to show based on the branch chosen in objective 9
                            if store.event_flags.get("branch_assassination", False):
                                textbutton "MARK COMPLETE - BEGIN THE FINAL STRIKE":
                                    xsize 520
                                    text_size font_size(24)
                                    text_color "#2a7a4b"
                                    text_hover_color "#1a5a3b"
                                    action [
                                        SetVariable("objective_16_complete", True),
                                        SetVariable("tutorial_active", False),
                                        Hide("journal_panel"),
                                        Jump("show_ending_assassination")
                                    ]
                            elif store.event_flags.get("branch_blackmail", False):
                                textbutton "MARK COMPLETE - BEGIN THE FINAL STRIKE":
                                    xsize 520
                                    text_size font_size(24)
                                    text_color "#2a7a4b"
                                    text_hover_color "#1a5a3b"
                                    action [
                                        SetVariable("objective_16_complete", True),
                                        SetVariable("tutorial_active", False),
                                        Hide("journal_panel"),
                                        Jump("show_ending_blackmail")
                                    ]
                            else:
                                # Fallback if no branch was chosen (shouldn't happen)
                                textbutton "MARK COMPLETE - BEGIN THE FINAL STRIKE":
                                    xsize 520
                                    text_size font_size(24)
                                    text_color "#2a7a4b"
                                    text_hover_color "#1a5a3b"
                                    action [
                                        SetVariable("objective_16_complete", True),
                                        SetVariable("tutorial_active", False),
                                        Hide("journal_panel"),
                                        Jump("show_ending_assassination")
                                    ]

                    if current_objective < 8:
                        null height 15
                        textbutton "Skip Tutorial":
                            xalign 0.0
                            xsize 200
                            text_size font_size(22)
                            text_color "#444444"
                            text_hover_color "#777777"
                            action Show("skip_tutorial_confirm")
                else:
                    text "The vengeance is complete! Thy empire stands supreme, and thy enemies lie vanquished.":
                        xsize 580
                        size font_size(28)
                        color "#7a4b2a"
                        text_align 0.5
        
        # Close button positioned at top-right at JOURNAL title height (outside vbox)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action Hide("journal_panel")
            xalign 1.0
            yalign 0.0
            xoffset -15  # Slight adjustment from edge
            yoffset 5    # Higher up
        

# ===== SKIP TUTORIAL CONFIRMATION =====
screen skip_tutorial_confirm():
    modal True
    zorder 250
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 300
        background "#1a1a1a"
        
        vbox:
            spacing 30
            xalign 0.5
            yalign 0.5
            
            text "Skip Tutorial?":
                size 28
                color "#ffffff"
                xalign 0.5
            
            text "Are you sure you want to skip the tutorial?\nYou'll jump to the final tutorial objective.":
                size 16
                color "#cccccc"
                text_align 0.5
                xalign 0.5
            
            hbox:
                spacing 50
                xalign 0.5
                
                textbutton "Yes, Skip" action [
                    SetVariable("tutorial_skipped", True),
                    SetVariable("objective_1_complete", True),
                    SetVariable("objective_2_complete", True),
                    SetVariable("objective_3_complete", True),
                    SetVariable("objective_4_complete", True),
                    SetVariable("objective_5_complete", True),
                    SetVariable("objective_6_complete", True),
                    SetVariable("objective_7_complete", True),
                    SetVariable("objective_4_dialogue_shown", True),
                    SetVariable("workers_hired", 3),
                    SetVariable("building_1_type_set", True),
                    SetVariable("workers_assigned_count", 3),
                    SetVariable("potion_purchased", True), SetVariable("potion_transferred", True), SetVariable("potion_used_on_worker", True),
                    SetVariable("building_upgraded_tutorial", True), SetVariable("building_skill_bonus_increased_tutorial", True),
                    SetVariable("tutorial_friendly_chat_done", True),
                    SetVariable("current_objective", 8),
                    Hide("skip_tutorial_confirm"), Hide("journal_panel")
                ]
                
                textbutton "No, Continue" action Hide("skip_tutorial_confirm")



# ===== OBJECTIVE COMPLETION CHECKER =====
label check_tutorial_progress:
    if objective_just_completed > 0:
        if objective_just_completed == 1:
            $ objective_just_completed = 0
            call show_objective_1_dialogue from _call_show_objective_1_dialogue
        elif objective_just_completed == 2:
            $ objective_just_completed = 0
            call show_objective_2_dialogue from _call_show_objective_2_dialogue
        elif objective_just_completed == 3:
            $ objective_just_completed = 0
            call show_objective_3_dialogue from _call_show_objective_3_dialogue
        elif objective_just_completed == 4:
            $ objective_just_completed = 0
            call show_objective_4_dialogue from _call_show_objective_4_dialogue_1
        elif objective_just_completed == 5:
            $ objective_just_completed = 0
            call show_objective_5_dialogue from _call_show_objective_5_dialogue
    return

# ===== NEW OBJECTIVE DIALOGUES =====
label show_objective_10_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_10_dialogue - STARTING DIALOGUE")
    "Fifty thousand coins. The number echoes in my mind like a promise fulfilled."
    "My coffers overflow with gold, each coin a testament to the empire I have built from nothing."
    "This is not mere wealth—it is power made manifest, the fuel that shall drive my campaign of vengeance to its inevitable conclusion."
    "With such resources, I can move mountains and topple tyrants."
    "I can buy loyalty, silence enemies, and fund operations that would make lesser men tremble."
    "The governor may have his armies and his influence, but I have something he cannot match: the patience to build, and the gold to make it real."
    "Every coin I have earned represents a choice, a sacrifice, a moment when I chose power over comfort."
    "Now, that power is mine to wield, and I shall use it to reshape this city in my image."
    "The path ahead is clear. Whether through steel or secrets, the governor's reign ends here."
    "And when the dust settles, it shall be my banner that flies over the city, my law that governs, my will that shapes the future."
    "My journal hath been inscribed with the next duty. The final pieces of my plan are falling into place."
    $ renpy.log("DEBUG: show_objective_10_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_11_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_11_dialogue - STARTING DIALOGUE")
    "Twenty souls now serve my cause. Twenty pairs of eyes watching, twenty pairs of ears listening, twenty minds working toward a single purpose: my victory."
    "This is not merely a workforce—it is a network that spans the city like a web of shadows."
    "No secret shall escape my notice, no conspiracy remain hidden, no plot go undetected."
    "Each worker I have recruited brings their own skills, their own connections, their own value to my cause."
    "Warriors who can strike with deadly precision, spies who can slip through the tightest security, merchants who can move goods and information with equal ease."
    "The governor may have his guards and his informants, but I have something far more valuable: a network built on loyalty, not fear."
    "My workers serve me because they believe in my cause, because they have seen the future I offer, and because they know that when I triumph, they shall share in that victory."
    "With twenty souls at my command, I can monitor every corner of the city, gather intelligence on every target, and strike when and where I choose."
    "The governor's every move is known to me, his every weakness catalogued, his every ally marked."
    "My journal hath been inscribed with the next duty. The web is complete, and the spider waits."
    $ renpy.log("DEBUG: show_objective_11_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_12_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_12_dialogue - STARTING DIALOGUE")
    "The artifacts are mine! Three relics of power, each one a key to unlocking the governor's downfall."
    "The Binding Gem pulses with inner fire, its crystalline surface catching the light like captured starlight."
    "With this, I can break the djinn's protection, shattering the supernatural shield that has kept the governor safe from harm."
    "The Obsidian Blade rests in its sheath, its edge so sharp it seems to cut the very air."
    "Forged in darkness and quenched in shadow, this weapon can pierce any defense, magical or mundane."
    "The Enchanted Ring gleams on my finger, its power flowing through me like liquid silver."
    "With this, I can charm any ally, break any enchantment, and command respect from those who would otherwise stand against me."
    "These are not mere trinkets—they are tools of destiny, each one carefully chosen to serve a specific purpose in my grand design."
    "With these artifacts, I can face any foe, overcome any obstacle, and achieve what others would call impossible."
    "The governor may have his armies and his wealth, but I have something he cannot match: the power of legend itself, forged into instruments of vengeance."
    "The arsenal is complete, and the time for action draws near."
    "My journal hath been inscribed with the next duty. The final preparations begin."
    $ renpy.log("DEBUG: show_objective_12_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_13_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_13_dialogue - STARTING DIALOGUE")
    "Five strongholds now fly my banner. Five bastions of power, each one a declaration of my growing influence."
    "From these fortresses, I command the city."
    "Each building serves a purpose: taverns where information flows like wine, guilds where warriors train and plan, brothels where secrets are whispered in the dark, restaurants where deals are made over fine meals."
    "This is not merely an empire of shadows—it is a network of power that rivals any force in the city."
    "The governor may sit in his castle, but I control the streets, the markets, the places where real power is born."
    "From these bastions, I shall launch my final assault."
    "Each building is a staging ground, each worker a soldier in my army, each coin a weapon in my arsenal."
    "The governor's influence wanes with each passing day, while mine grows stronger."
    "He may have his title and his crown, but I have something far more valuable: the loyalty of those who control the city's true power—its people, its commerce, its secrets."
    "When the time comes, when I make my move, these five strongholds shall be the foundation upon which I build a new order."
    "The old ways shall fall, and from their ashes, my empire shall rise."
    "My journal hath been inscribed with the next duty. The stage is set, and the players take their positions."
    $ renpy.log("DEBUG: show_objective_13_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_14_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_14_dialogue - STARTING DIALOGUE")
    "My elite guard is assembled. Warriors who can fell any foe, agents who can outwit any schemer, champions who stand ready to serve my cause."
    "These are not mere workers—they are the finest the city has to offer, each one a master of their craft."
    "Warriors with combat skills that would make legends tremble, agents with cleverness and charm that can turn any situation to my advantage."
    "With such champions at my side, victory is not merely possible—it is assured."
    "The governor may have his guards, but I have something far more dangerous: individuals who have chosen to stand with me, who believe in my cause, and who will stop at nothing to see it through."
    "Each member of my elite guard brings their own unique talents to the table."
    "Some excel in open combat, ready to strike with overwhelming force. Others prefer the shadows, using cunning and charm to achieve their goals without bloodshed."
    "Together, they form a force that can adapt to any situation, overcome any obstacle, and achieve any objective."
    "Whether the path requires steel or subtlety, I have the right tool for the job."
    "The governor's days are numbered. With this elite guard at my command, there is nothing that can stand between me and my vengeance."
    "The final act begins."
    "My journal hath been inscribed with the next duty. The pieces are in place, and the endgame approaches."
    $ renpy.log("DEBUG: show_objective_14_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_15_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_15_dialogue - STARTING DIALOGUE")
    "Ten thousand coins in a single day. The number alone is staggering, but what it represents is far greater."
    "My empire generates wealth like a mighty river, flowing endlessly into my coffers."
    "This is not mere prosperity—it is the power I have built, the machine of commerce that shall fuel my vengeance and fund my rise to dominance."
    "Each coin earned is a testament to the network I have created, the workers I have trained, the buildings I have established."
    "This is the culmination of every choice, every sacrifice, every moment of planning that has brought me to this point."
    "With such wealth flowing through my hands, I can fund operations that would bankrupt lesser men."
    "I can buy loyalty, silence enemies, and create opportunities that others can only dream of."
    "The governor may have inherited his wealth, but I have built mine from nothing."
    "Every coin I earn is a victory, every transaction a step closer to my goal."
    "This is the power I have forged through patience and planning."
    "The machine of prosperity that I have built shall not only fund my vengeance, but ensure that when I take control, the city's economy flows through my hands."
    "My journal hath been inscribed with the next duty. The final preparations are complete, and the time for action has come."
    $ renpy.log("DEBUG: show_objective_15_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_tutorial_completion_message:
    scene expression event_bg
    show expression Solid("#00000080")
    
    # Unlock the Governor's Castle (backup in case we got here without going through endings)
    python:
        castle_name = "Governor's Castle"
        renpy.log("DEBUG: show_tutorial_completion_message - Ensuring castle is unlocked")
        
        # Ensure castle exists in available_buildings
        if castle_name not in available_buildings:
            available_buildings[castle_name] = {}
        
        # Set all castle properties
        available_buildings[castle_name]["price"] = 0
        available_buildings[castle_name]["reputation"] = 0
        available_buildings[castle_name]["base_level"] = 5
        available_buildings[castle_name]["type"] = "governor_castle"
        available_buildings[castle_name]["assigned_servants"] = available_buildings[castle_name].get("assigned_servants", [])
        available_buildings[castle_name]["servant_jobs"] = available_buildings[castle_name].get("servant_jobs", {})
        available_buildings[castle_name]["max_workers"] = 10
        available_buildings[castle_name]["costs"] = 0
        available_buildings[castle_name]["owned"] = True
        available_buildings[castle_name]["skill"] = 50
        available_buildings[castle_name]["skill_bonus"] = 0
        
        # Ensure it's in owned_buildings
        if castle_name not in owned_buildings:
            owned_buildings.append(castle_name)
        
        buildings_owned = len(owned_buildings)
        map_button_buildings["Castle"] = castle_name
        custom_names[castle_name] = castle_name
        
        renpy.log(f"DEBUG: Castle unlocked in completion message - in owned: {castle_name in owned_buildings}, map_button: {'Castle' in map_button_buildings}")
    
    "The vengeance is complete! Thy empire stands supreme, and thy enemies lie vanquished."
    "The governor's reign hath ended, brought low by my hand through steel or secrets, as I chose."
    "The city now answers to a new master—one who built their power from nothing, who forged an empire of shadows through cunning and determination."
    "The Governor's Castle is now mine, a symbol of my triumph and a testament to the empire I have built."
    "Within its walls, I command the finest servants, the most skilled courtesans, the deadliest guards, and the wisest chamberlains."
    "The castle serves as the crown jewel of my domain, a place where power flows like wine and where my will becomes law."
    "From this moment forth, the castle is mine to command as I see fit—its halls echo with my authority, its chambers filled with those who serve my cause."
    "With your quest complete, new opportunities arise. You can now purchase buildings in other cities through the 'Buy Buildings Abroad' option on the map."
    "But remember: the Governor's Castle remains the heart of your empire, a constant reminder of the vengeance you have achieved and the power you now wield."
    "The old order hath fallen. A new empire rises, and I am its master."
    jump tavern_screen
