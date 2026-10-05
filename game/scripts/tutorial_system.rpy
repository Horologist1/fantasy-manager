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

# Tutorial milestone images (place files in game/images/tutorial/; fallback used if missing)
# 1) governor_note_on_door.png - note on door (shows in Governor Retaliation event, the day after you choose path at Obj 9)
# 2) tutorial_consolidation.png - three magical artifacts / breaking the djinn's binding (show_objective_12_dialogue)
# 3) ending_blade_throne.png - throne room (show_ending_assassination)
# 4) ending_blackmail_study.png - study (show_ending_blackmail). If file is .png.png, rename to .png or we try both.
default tutorial_milestone_note_door = "images/tutorial/governor_note_on_door.png"
default tutorial_milestone_consolidation = "images/tutorial/tutorial_consolidation.png"
default tutorial_milestone_ending_blade = "images/tutorial/ending_blade_throne.png"
default tutorial_milestone_ending_blackmail = "images/tutorial/ending_blackmail_study.png"

init python:
    def get_tutorial_milestone_image(primary_path, fallback_paths=None):
        """Return primary_path if loadable, else first loadable from fallback_paths, else None. Use for scene expression with a fallback bg."""
        try:
            if renpy.loadable(primary_path):
                return primary_path
            if fallback_paths:
                for p in fallback_paths:
                    if renpy.loadable(p):
                        return p
        except Exception:
            pass
        return None

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
    1: "First Hires - Three Workers and a Focus",
    2: "Choosing the Business - What This Place Becomes",
    3: "Putting People to Work - Assign Three Workers",
    4: "Building Capital - Five Thousand Coins",
    5: "Supplies and Upkeep - Potions and Energy",
    6: "Upgrading - Building Level and Building Skill",
    7: "Getting to Know Them - A Friendly Lunch",
    8: "Expansion - Two Buildings, Ten Workers",
    9: "Choosing the Method - How the Governor Falls",
    10: "The War Chest - Thirty Thousand Coins",
    11: "The Network - Fifteen Workers",
    12: "The Arsenal - Three Artifacts",
    13: "Holding the City - Three Buildings",
    14: "The Inner Circle - Five Specialists",
    15: "Proving the Machine - Three Thousand in a Day",
    16: "The Reckoning - The Final Strike",
}

default objective_descriptions = {
    1: "Hire three workers to start with.\n\nI can buy them outright at the market, or wait for someone to turn up looking for work. Recruits take a few days to appear, but they usually come better skilled than anything on sale.\n\nI should also decide what I am good at. My own best skills shape what this place can do, so I need to pick a focus before I start telling other people what to do.",
    2: "Decide what this building becomes.\n\nA brothel trades on discretion and appetite, and the coin comes fast. A restaurant is slower and respectable. An adventurers' guild deals in muscle and salvage, and the people it attracts are useful in other ways.\n\nEach one earns differently and draws a different crowd. Whichever I choose has to fund what comes after, because the governor will not be brought down on goodwill.",
    3: "Assign three workers to a profession.\n\nEveryone is better at some things than others, and the day's takings depend on putting people where their best skills actually apply. Put a strong earner in the wrong job and they still bring something in - just a fraction of what they would make where their skills fit.\n\nThis is also how I find out who I can rely on. When it is time to move against the governor, I will need people already standing in the right places.",
    4: "Reach five thousand coins.\n\nThat is enough to start thinking about a second building. Every service sold and every deal struck adds to it, and none of what I am planning happens without money first.\n\nThe governor sits in his fortress and does not think about me at all. Every coin changes that.",
    5: "Buy an energy potion at the market, give it to one of my workers, and use it.\n\nWork costs energy. A worker who runs out leaves the rest of the day's tasks undone, and they only recover overnight. A potion puts them back on their feet in the middle of a busy day.\n\nIt is worth knowing how a day fills up, too. Every worker does at least one task a day, and those are the tasks listed in the daily report. As this place gets busier and word spreads, one worker can be pulled into several tasks in a single day. If that starts costing me more in exhaustion than it earns, I can cap the tasks per worker in each building's management screen.",
    6: "Raise a building's level, and raise its Building skill by ten.\n\nA level costs one thousand coins. The Building skill goes up through equipment, ingredients or Hag Potions, depending on what that particular business runs on.\n\nBoth make every worker inside more effective. I would rather be over-prepared when the governor finally looks in my direction.",
    7: "Invite one of my workers to a Friendly Lunch. It costs one hundred and fifty coins.\n\nSitting down with someone tells me more than a week of watching them work: what they want, what they are afraid of, whether they would stay if this got difficult.\n\nThe governor keeps people in line with fear and money. I would rather have a handful who chose to be here.",
    8: "Two buildings, ten workers, ten thousand coins.\n\nWith that much behind me I can stop reacting and start planning. This is the point where the operation becomes something the governor has to take seriously.",
    9: "Choose how this ends.\n\nI can have the governor killed. Quiet, final, and it makes an enemy of everyone still loyal to him.\n\nOr I can ruin him: take back what he stole, put the proof somewhere he cannot reach, and own him for as long as he lives.\n\nBoth work. They cost different things.",
    10: "Reach thirty thousand coins.\n\nEnough to pay fighters, buy informants, and cover whatever this turns out to actually cost. Vengeance runs on the same accounts as everything else.",
    11: "Recruit fifteen workers.\n\nNot for the work. For the reach. Fifteen people spread across the city hear things: which guards take money, who visits the governor's house after dark, which of his allies is already looking for a way out.\n\nA network like that is worth more than any single weapon.",
    12: "Collect three artifacts: a Binding Gem, an Obsidian Blade, and an Enchanted Ring.\n\nThe gem breaks dark pacts, and the governor has at least one. The blade goes through enchanted armour. The ring makes whoever wears it very hard to refuse.\n\nThese are the tools the last night will need.",
    13: "Own three buildings.\n\nThree businesses in three districts means income that does not stop if one of them is shut down, and eyes in parts of the city the governor still thinks are his. It also means funding the end of this without borrowing from anyone.",
    14: "Train five specialists: three workers at Combat 80 or higher, and two at Clever or Charm 80 or higher.\n\nThe fighters are the obvious part. The other two matter more. Most of what happens that night will be talking, and lying, and getting through doors that are supposed to be locked.",
    15: "Take three thousand coins in a single day.\n\nNot for the money. It proves the operation runs without me standing over it, which is exactly what needs to be true on the night I am somewhere else.",
    16: "Everything is ready: the money, the network, the weapons, the buildings, the people.\n\nNow I choose how to do it. Overwhelming force, or something quieter. Either way, the governor's last ordinary day is already behind him.",
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
            elif hasattr(entry, "__getitem__") and not isinstance(entry, (tuple, str)) and not hasattr(entry, "get"):
                # Handle list format: [item_id] or [item_id, quantity] or [item_id, quantity, equipped]
                if len(entry) > 0 and entry[0] == item_id:
                    found = True
            elif hasattr(entry, "get"):
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
                elif hasattr(entry, "__getitem__") and not isinstance(entry, (tuple, str)) and not hasattr(entry, "get"):
                    # Handle list format
                    if len(entry) > 0 and entry[0] == item_id:
                        found = True
                elif hasattr(entry, "get"):
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

    # Safety valve: if the player is stuck on objective 12 (which needs the Binding Gem)
    # for this many days, the Journal offers a manual button to obtain the gem. This guards
    # against the (rare) case where the binding_gem_lead_2 event never resolves into a gem.
    OBJECTIVE_12_FALLBACK_DAYS = 14

    def record_objective_12_entry():
        """Stamp the day the player entered objective 12 (used by the stuck-player safety valve)."""
        if not hasattr(store, "event_flags") or store.event_flags is None:
            store.event_flags = {}
        if "objective_12_entered_day" not in store.event_flags:
            store.event_flags["objective_12_entered_day"] = calculate_total_days()

    def days_stuck_on_objective_12():
        """Days since entering objective 12 (0 if not tracked or not currently on objective 12)."""
        if getattr(store, "current_objective", 0) != 12:
            return 0
        ef = getattr(store, "event_flags", {}) or {}
        entered = ef.get("objective_12_entered_day") if hasattr(ef, "get") else None
        if not isinstance(entered, (int, float)):
            return 0
        return max(0, calculate_total_days() - entered)

    def journal_show_binding_gem_fallback():
        """True when the Journal should offer the manual Binding Gem fallback button."""
        if getattr(store, "current_objective", 0) != 12:
            return False
        if getattr(store, "objective_12_complete", False):
            return False
        if has_objective_12_item_flag("binding_gem") or has_item_anywhere("binding_gem"):
            return False
        return days_stuck_on_objective_12() >= OBJECTIVE_12_FALLBACK_DAYS

    def journal_grant_binding_gem_fallback():
        """Hand the player the Binding Gem when they have been stuck on objective 12 too long."""
        if not journal_show_binding_gem_fallback():
            return
        if not hasattr(store, "manager_inventory") or store.manager_inventory is None:
            store.manager_inventory = []
        add_item_to_inventory(store.manager_inventory, "binding_gem")
        mark_objective_12_item_collected("binding_gem")
        renpy.log("FALLBACK: Granted binding_gem via Journal 14-day safety valve")
        renpy.notify("A weary merchant finally tracks you down — the Binding Gem is yours.")

    store.record_objective_12_entry = record_objective_12_entry
    store.days_stuck_on_objective_12 = days_stuck_on_objective_12
    store.journal_show_binding_gem_fallback = journal_show_binding_gem_fallback
    store.journal_grant_binding_gem_fallback = journal_grant_binding_gem_fallback

    def validate_objective_12_items():
        """
        Validate and fix items for objective 12 (binding gem quest).
        This function checks if the required items exist and logs detailed information.
        It's called when the player is on objective 12 to ensure items are properly tracked.
        """
        # Stamp objective-12 entry day (covers legacy saves that predate this tracking).
        if getattr(store, "current_objective", 0) == 12:
            record_objective_12_entry()

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
            char_sheet_done = getattr(store, "manager_start_skill_chosen", False)
            if workers_hired >= 3 and char_sheet_done:
                return "Progress: Workers 3/3\nManager Assign Skill point 1/1 {image=journal_check_on}"
            return f"Progress: Workers {workers_hired}/3\nManager Assign Skill point {1 if char_sheet_done else 0}/1"
        elif current_objective == 2:
            if building_1_type_set:
                return "Progress: Building type chosen {image=journal_check_on}"
            else:
                return "Progress: Building type remains unselected"
        elif current_objective == 3:
            if workers_assigned_count >= 3:
                return "Progress: 3 workers assigned to their duties {image=journal_check_on}"
            else:
                return f"Progress: {workers_assigned_count}/3 workers assigned to professions"
        elif current_objective == 4:
            return f"Progress: {money}/5000 Coins"
        elif current_objective == 5:
            if store.potion_purchased and store.potion_transferred and store.potion_used_on_worker:
                return "Progress: Energy potion used {image=journal_check_on}"
            elif store.potion_purchased and store.potion_transferred:
                return "Progress: 2/3 - Energy potion purchased {image=journal_check_on}, Transferred to worker {image=journal_check_on}, Use potion on worker"
            elif store.potion_purchased:
                return "Progress: 1/3 - Energy potion purchased {image=journal_check_on}, Transfer to worker, Use on worker"
            else:
                return "Progress: 0/3 - Buy energy potion from shop, Transfer to worker, Use on worker"
        elif current_objective == 6:
            if store.building_upgraded_tutorial and store.building_skill_bonus_increased_tutorial:
                return "Progress: Building level enhanced {image=journal_check_on}, Building skill bonus increased {image=journal_check_on}"
            elif store.building_upgraded_tutorial:
                return "Progress: 1/2 - Building level enhanced {image=journal_check_on}, Increase Building skill bonus"
            elif store.building_skill_bonus_increased_tutorial:
                return "Progress: 1/2 - Building skill bonus increased {image=journal_check_on}, Enhance building level"
            else:
                return "Progress: 0/2 - Upgrade building level, Increase Building skill bonus"
        elif current_objective == 7:
            return "Progress: Invite a worker to Friendly Lunch ($150)\nGuidance: Workers -> Details -> Interactions -> Friendship -> Friendly Lunch"
        elif current_objective == 8:
            actual_buildings = journal_owned_building_count()
            actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
            return f"Progress:\n- Buildings: {actual_buildings}/2\n- Workers: {actual_workers}/10\n- Coins: {money}/10000"
        elif current_objective == 9:
            if store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False):
                branch = "Assassination" if store.event_flags.get("branch_assassination", False) else "Blackmail"
                return f"Progress: Path chosen -> {branch}\nMark 'Complete' to advance"
            else:
                return "Progress: Choose your path in the Journal"
        elif current_objective == 10:
            return f"Progress: {money}/30000 Coins"
        elif current_objective == 11:
            actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
            return f"Progress: {actual_workers}/15 Workers"
        elif current_objective == 12:
            # Validate and fix items when checking objective 12 progress
            validate_objective_12_items()
            
            sync_objective_12_flags_from_inventory()
            has_binding_gem = has_objective_12_item_flag("binding_gem")
            has_obsidian_blade = has_objective_12_item_flag("obsidian_blade")
            has_enchanted_ring = has_objective_12_item_flag("enchanted_ring")
            items_collected = sum([has_binding_gem, has_obsidian_blade, has_enchanted_ring])
            check_gem = "{image=journal_check_on}" if has_binding_gem else "{image=journal_check_off}"
            check_blade = "{image=journal_check_on}" if has_obsidian_blade else "{image=journal_check_off}"
            check_ring = "{image=journal_check_on}" if has_enchanted_ring else "{image=journal_check_off}"
            # Debug logging
            renpy.log(f"DEBUG Objective 12: binding_gem={has_binding_gem}, obsidian_blade={has_obsidian_blade}, enchanted_ring={has_enchanted_ring}")
            renpy.log(f"DEBUG Objective 12: manager_inventory sample={str(store.manager_inventory[:3]) if len(store.manager_inventory) > 0 else 'EMPTY'}")
            return f"Progress: {items_collected}/3 Artifacts\n- Binding Gem: {check_gem} (follow the rumors)\n- Obsidian Blade: {check_blade} (Elite Emporium)\n- Enchanted Ring: {check_ring} (Adventurer's Market)"
        elif current_objective == 13:
            actual_buildings = journal_owned_building_count()
            return f"Progress: {actual_buildings}/3 Buildings"
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
            warriors_ready = "{image=journal_check_on}" if warriors >= 3 else "{image=journal_check_off}"
            agents_ready = "{image=journal_check_on}" if unique_agents >= 2 else "{image=journal_check_off}"
            return f"Progress (Requires BOTH):\n- Elite Warriors (Combat 80+): {warriors}/3 {warriors_ready}\n- Elite Agents (Clever/Charm 80+): {unique_agents}/2 {agents_ready}"
        elif current_objective == 15:
            if store.event_flags.get("daily_revenue_10k_achieved", False):
                return "Progress: Daily revenue goal achieved (3,000 coins) {image=journal_check_on}"
            else:
                return "Progress: Achieve 3,000 coins revenue in a single day\nTip: Upgrade buildings, assign skilled workers, increase Building skill"
        elif current_objective == 16:
            if store.vengeance_path_chosen:
                return f"Progress: Path chosen -> {store.vengeance_path}\nMark 'Complete' to begin the final strike"
            else:
                combat_count = count_workers_with_skill("Combat", 70)
                clever_count = count_workers_with_skill("Clever", 70)
                blade_ready = "{image=journal_check_on}" if combat_count >= 5 else "{image=journal_check_off}"
                shadow_ready = "{image=journal_check_on}" if clever_count >= 5 else "{image=journal_check_off}"
                return f"Progress: Choose your path of vengeance\n- Path of the Blade (Combat 70+): {combat_count}/5 {blade_ready}\n- Path of the Shadow (Clever 70+): {clever_count}/5 {shadow_ready}\nTip: Check out shops for items to boost skills!"
        else:
            return "Progress: I have not chosen how this ends yet"

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
    
    # Arena and Academy are unlocked venues, not player-built holdings; the
    # Journal's building objectives (8 and 13) must not count them.
    _journal_excluded_buildings = frozenset(("Arena", "Academy"))

    def journal_owned_building_count():
        _owned = getattr(store, "owned_buildings", None) or []
        return len([b for b in _owned if b not in _journal_excluded_buildings])

    def can_complete_objective_8():
        """Check if objective 8 conditions are met"""
        # Check prerequisite: objective 7 must be complete
        if not getattr(store, 'objective_7_complete', False):
            return False
        actual_buildings = journal_owned_building_count()
        actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
        return actual_buildings >= 2 and actual_workers >= 10 and money >= 10000
    
    def can_complete_objective_10():
        """Check if objective 10 conditions are met"""
        # Check prerequisite: objective 9 must be complete
        if not getattr(store, 'objective_9_complete', False):
            return False
        return money >= 30000
    
    def can_complete_objective_11():
        """Check if objective 11 conditions are met"""
        # Check prerequisite: objective 10 must be complete
        if not getattr(store, 'objective_10_complete', False):
            return False
        actual_workers = len(store.workers) if hasattr(store, 'workers') else total_workers
        return actual_workers >= 15
    
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
        actual_buildings = journal_owned_building_count()
        return actual_buildings >= 3
    
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
    GOV_TENSION_EVENT_COOLDOWN_DAYS = 4
    GOV_EVENT_GLOBAL_COOLDOWN_DAYS = 4

    def _governor_abs_day_index():
        """Stable absolute day index used by governor event cooldowns."""
        try:
            return int(calculate_total_days())
        except Exception:
            day = int(getattr(store, "current_day", 1))
            month = int(getattr(store, "current_month", 1))
            year = int(getattr(store, "current_year", 1))
            return ((year - 1) * 12 * 28) + ((month - 1) * 28) + day
    
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

        # Global cooldown for any governor event.
        # Prevents back-to-back governor events regardless of type.
        last_any_day = store.event_flags.get("governor_event_last_day", None)
        global_cooldown = int(getattr(store, "GOV_EVENT_GLOBAL_COOLDOWN_DAYS", GOV_EVENT_GLOBAL_COOLDOWN_DAYS))
        global_cooldown = max(0, global_cooldown)
        if last_any_day is not None:
            now = _governor_abs_day_index()
            try:
                days_since_any = now - int(last_any_day)
            except Exception:
                days_since_any = global_cooldown
            if days_since_any < global_cooldown:
                renpy.log(
                    f"TENSION: Retaliation blocked by global governor cooldown "
                    f"({days_since_any}/{global_cooldown} days)."
                )
                return False
        
        # Only trigger when player has chosen a path (assassination or blackmail)
        # Also check if objective 9 is complete (player may have completed it before this system was added)
        has_path = store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False)
        obj_9_complete = getattr(store, 'objective_9_complete', False)
        
        # Trigger if path is chosen OR if objective 9 is complete (for players who completed it before)
        if has_path or (obj_9_complete and store.current_objective >= 9):
            store.governor_retaliation_done = True
            store.governor_tension_active = True
            store.event_flags["governor_event_last_day"] = _governor_abs_day_index()
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
        
        # Global cooldown for any governor event.
        # Ensures no two governor events happen too close together.
        last_any_day = store.event_flags.get("governor_event_last_day", None)
        global_cooldown = int(getattr(store, "GOV_EVENT_GLOBAL_COOLDOWN_DAYS", GOV_EVENT_GLOBAL_COOLDOWN_DAYS))
        global_cooldown = max(0, global_cooldown)
        if last_any_day is not None:
            now = _governor_abs_day_index()
            try:
                days_since_any = now - int(last_any_day)
            except Exception:
                days_since_any = global_cooldown
            if days_since_any < global_cooldown:
                renpy.log(
                    f"TENSION: Governor event blocked by global cooldown "
                    f"({days_since_any}/{global_cooldown} days)."
                )
                return None

        def _eligible_tension_types():
            """Return event types that are not on cooldown; avoid immediate repeat when possible."""
            all_types = ["poison", "sabotage", "spy"]
            now = _governor_abs_day_index()
            cooldown = int(getattr(store, "GOV_TENSION_EVENT_COOLDOWN_DAYS", GOV_TENSION_EVENT_COOLDOWN_DAYS))
            cooldown = max(0, cooldown)

            eligible = []
            for ev_type in all_types:
                last_key = f"governor_tension_last_day_{ev_type}"
                last_day = store.event_flags.get(last_key, None)
                if last_day is None:
                    eligible.append(ev_type)
                    continue
                try:
                    delta = now - int(last_day)
                except Exception:
                    delta = cooldown
                if delta >= cooldown:
                    eligible.append(ev_type)

            # Avoid immediate repetition if there is at least one alternative.
            last_type = store.event_flags.get("governor_tension_last_type")
            if last_type in eligible and len(eligible) > 1:
                eligible = [t for t in eligible if t != last_type]

            # If all are blocked by cooldown, fall back to full pool (still avoiding immediate repeat when possible).
            if not eligible:
                eligible = list(all_types)
                if last_type in eligible and len(eligible) > 1:
                    eligible = [t for t in eligible if t != last_type]
                renpy.log("TENSION: All tension types on cooldown; using fallback pool.")

            return eligible

        def _choose_tension_type():
            """Weighted pick among eligible tension types."""
            eligible = _eligible_tension_types()
            if not eligible:
                return None
            weights_map = {
                "poison": 1.15,
                "sabotage": 1.0,
                "spy": 1.0,
            }
            weights = [weights_map.get(t, 1.0) for t in eligible]
            try:
                return random.choices(eligible, weights=weights, k=1)[0]
            except Exception:
                return random.choice(eligible)

        def _record_tension_type(ev_type):
            """Persist last-trigger metadata for cooldown/anti-repeat behavior."""
            if not ev_type:
                return
            now = _governor_abs_day_index()
            store.event_flags["governor_tension_last_type"] = ev_type
            store.event_flags[f"governor_tension_last_day_{ev_type}"] = now
            store.event_flags["governor_event_last_day"] = now

        # Guarantee an event after 10 days without one
        if store.days_since_last_tension_event >= 10:
            renpy.log(f"TENSION: Guaranteed event after {store.days_since_last_tension_event} days without one")
            store.days_since_last_tension_event = 0
            event_type = _choose_tension_type()
            _record_tension_type(event_type)
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
        
        event_type = _choose_tension_type()
        _record_tension_type(event_type)
        
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
        
        # Arena and Academy are never sabotaged by governor tension events.
        _gov_sabotage_excluded_names = frozenset(("Arena", "Academy"))
        _gov_sabotage_excluded_types = frozenset(("arena", "academy"))
        candidates = []
        for bname in list(store.owned_buildings):
            if bname in _gov_sabotage_excluded_names:
                continue
            bld = store.available_buildings.get(bname)
            if not bld:
                continue
            btype = str(bld.get("type", "") or "").lower()
            if btype in _gov_sabotage_excluded_types:
                continue
            candidates.append(bname)
        if not candidates:
            renpy.log("TENSION: Sabotage skipped — no eligible buildings (Arena/Academy excluded).")
            return None
        
        building_name = random.choice(candidates)
        building = store.available_buildings.get(building_name)
        
        if not building:
            return None
        
        # Reduce skill bonus; the daily loop restores it 3 days later via the
        # sabotage_restore_/sabotage_amount_ flags (see event_daily_exec). Record
        # the ACTUAL reduction: blindly restoring +10 would inflate low bonuses.
        old_bonus = building.get("skill_bonus", 0)
        reduction = min(10, max(0, old_bonus))
        building["skill_bonus"] = old_bonus - reduction

        store.event_flags[f"sabotage_{building_name}"] = store.current_day
        store.event_flags[f"sabotage_restore_{building_name}"] = calculate_total_days() + 3
        store.event_flags[f"sabotage_amount_{building_name}"] = reduction

        renpy.log(f"TENSION: {building_name} has been sabotaged! Skill bonus reduced by {reduction} for 3 days.")
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
    store.apply_governor_poison_event = apply_governor_poison_event
    store.apply_governor_sabotage_event = apply_governor_sabotage_event
    store.apply_governor_spy_event = apply_governor_spy_event

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
        # Objective 1: 3 workers + character sheet (assign first management skill)
        manager_skill_done = getattr(store, "manager_start_skill_chosen", False)
        if current_objective == 1 and is_previous_objective_complete(1) and workers_hired >= 3 and manager_skill_done and not objective_1_complete:
            renpy.log("DEBUG: Objective 1 completed!")
            objective_1_complete = True
            current_objective = 2
            renpy.call_in_new_context("show_objective_1_dialogue")
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


# ===== JOURNAL "MORE BELOW" ARROW =====
init python:
    def fm_journal_adjustment():
        """The journal viewport's Adjustment, kept in renpy.session.

        session on purpose (same as fm_roster_adjustment): an Adjustment kept
        in a screen scope or the store enters the rollback log and can poison
        saves (LA BIBLIA 8). session is never serialized.
        """
        adj = renpy.session.get("fm_journal_adj")
        if adj is None:
            adj = renpy.display.behavior.Adjustment()
            renpy.session["fm_journal_adj"] = adj
        return adj

    def fm_journal_reset_scroll():
        """Open at the top, like before the shared Adjustment existed."""
        adj = renpy.session.get("fm_journal_adj")
        if adj is not None:
            try:
                adj.value = 0
            except Exception:
                pass

    def fm_journal_more_arrow(st, at):
        """Down arrow while content remains below the fold.

        Polled at render time (0.1 s): the viewport only learns its `range`
        when it renders, after the screen is evaluated, so a plain `if` in the
        screen would lag one interaction behind. DejaVuSans because neither
        journal font has a down-arrow glyph.
        """
        adj = renpy.session.get("fm_journal_adj")
        more = False
        if adj is not None:
            try:
                more = (float(adj.range) - float(adj.value)) > 4
            except Exception:
                more = False
        box = 32  # width of the close button above (return_idle.png 64 px x 0.5)
        if more:
            arrow = Text(u"▼", font="DejaVuSans.ttf", size=font_size(28), color="#7a4b2a", xalign=0.5)
            return Fixed(arrow, xsize=box, ysize=font_size(28) + 6), 0.1
        return Null(box, 1), 0.1


# ===== WRAPPER FUNCTION FOR GLOBAL ACCESS =====
init python:
    def check_tutorial_objective():
        """Wrapper function to call check_objective_completion from anywhere"""
        check_objective_completion()



# ===== JOURNAL SCREEN =====
# Inline checkboxes for progress text; the game font lacks ✓/✗ glyphs (rendered as tofu)
image journal_check_on = Transform("gui/icons/batch_checkbox_on.png", xysize=(24, 24))
image journal_check_off = Transform("gui/icons/batch_checkbox_off.png", xysize=(24, 24))

screen journal_panel():
    modal True
    zorder 200
    on "show" action [Function(fm_journal_reset_scroll), Function(check_existing_building_upgrades), Function(check_objective_completion)]
    # Universal close/back hotkey (mirrors config.rpy's esc routing for this screen)
    key "K_BACKSPACE" action Hide("journal_panel")
    
    # Background overlay matching building selection
    add Solid("#000000dd")
    
    # Main content frame sized similarly to Building_select_global / building_selection
    frame:
        xalign 0.35  # Left of center for visible left margin
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (40, 40)  # Slightly reduced vertical padding
        xsize 780  # Increased width
        ysize 740  # Increased height for more verticality
        
        vbox:
            spacing 15  # Match shop_selection spacing
            null height 15  # Push JOURNAL title down a bit
            label "JOURNAL" xalign 0.5 style "header_style"
            null height 10  # Less space after JOURNAL title
            viewport:
                scrollbars None
                mousewheel True
                draggable True
                yadjustment fm_journal_adjustment()
                ysize 500
                xsize 650
                xoffset 60
                yoffset 25
                has vbox
                spacing 10

                if tutorial_active:
                    if current_objective < 9:
                        text "The governor destroyed everything I loved. Every step I take—every coin, every ally, every stronghold—brings me closer to the day I can make him pay.":
                            xsize 580
                            size font_size(22)
                            color "#6b6528"
                            text_align 0.0
                            italic True
                        null height 12

                    text "[get_current_objective_title()]":
                        xsize 580
                        size font_size(34)
                        color "#7a4b2a"

                    text "[get_current_objective_description()]":
                        xsize 580
                        size font_size(26)
                        color "#7a4b2a"
                        text_align 0.0

                    null height 15

                    text "[get_current_objective_progress()]":
                        xsize 580
                        size font_size(24)
                        color "#6b6528"

                    null height 20

                    # Tutorial quick access links for objectives 1-7
                    if current_objective == 1:
                        text "Tutorial:":
                            size font_size(26)
                            color "#7a4b2a"
                        textbutton "Explore > Recruit workers or Buy Servants":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("map_screen")]
                        textbutton "Context menu (right) > [player_title] [player_name] (Character sheet) > Assign first management skill":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("map_screen")]
                    
                    elif current_objective == 2:
                        text "Tutorial:":
                            size font_size(26)
                            color "#7a4b2a"
                        textbutton "Manage Buildings > Select building > Building Type":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Hide("tavern"), Show("Building_select_global")]
                    
                    elif current_objective == 3:
                        text "Tutorial:":
                            size font_size(26)
                            color "#7a4b2a"
                        textbutton "Workers > Worker Name > Assign Building > Select Job":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]
                    
                    elif current_objective == 4:
                        text "Tutorial:":
                            size font_size(26)
                            color "#7a4b2a"
                        textbutton "Tavern > Next Day":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("tavern")]
                        text "Tip: Lower worker comfort when needed to save daily costs and build gold faster." size font_size(20) color "#7a4b2a" italic True
                    
                    elif current_objective == 5:
                        text "Tutorial:":
                            size font_size(26)
                            color "#7a4b2a"
                        textbutton "Map > Shop":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("map_screen")]
                        textbutton "Workers > Worker Name > Details > Inventory":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]
                        text "Tip: For this tutorial, purchase the potion from the shop and transfer it manually. In the future, you can use potions directly from Manage Workers or Manage Buildings." size font_size(22) color "#7a4b2a"
                        textbutton "Manage Buildings > Select building > Daily Stories Limit":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Hide("tavern"), Show("Building_select_global")]
                        text "Tip: Extra daily stories come from the building's Reputation (capped by its level) and stop once a worker runs out of energy. Cap them per worker with Daily Stories Limit." size font_size(22) color "#7a4b2a"
                    
                    elif current_objective == 6:
                        text "Tutorial:":
                            size font_size(26)
                            color "#7a4b2a"
                        textbutton "Manage Buildings > Select building > Upgrade Building":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Hide("tavern"), Show("Building_select_global")]
                        textbutton "Manage Buildings > Select building > Skill Bonus":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Hide("tavern"), Show("Building_select_global")]
                        text "Tip: Each +10 Building skill bonus costs $100/day." size font_size(22) color "#7a4b2a"
                    
                    elif current_objective == 7:
                        text "Tutorial:":
                            size font_size(26)
                            color "#7a4b2a"
                        textbutton "Workers > Worker Name > Details > Interactions > Friendship > Friendly Lunch":
                            xsize 580
                            text_size font_size(24)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]
                        text "Tip: Friendly Lunch costs $150. Choose a worker, open Interactions, then Friendship, and select Friendly Lunch." size font_size(22) color "#7a4b2a"

                    # MARK AS COMPLETE buttons for objectives 8+
                    if current_objective == 8:
                        null height 10
                        text "Tip: Lower worker comfort when needed to save daily costs and grow your treasury faster." size font_size(20) color "#7a4b2a" italic True
                        $ can_complete_8 = can_complete_objective_8()
                        if can_complete_8:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 580
                                text_size font_size(26)
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
                                xsize 580
                                size font_size(22)
                                color "#7a4b2a"
                    
                    elif current_objective == 10:
                        $ can_complete_10 = can_complete_objective_10()
                        if can_complete_10:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 580
                                text_size font_size(26)
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
                                xsize 580
                                size font_size(22)
                                color "#7a4b2a"
                    
                    elif current_objective == 11:
                        $ can_complete_11 = can_complete_objective_11()
                        if can_complete_11:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 580
                                text_size font_size(26)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_11_complete", True),
                                    SetVariable("current_objective", 12),
                                    Function(record_objective_12_entry),
                                    Hide("journal_panel"),
                                    Jump("show_objective_11_dialogue")
                                ]
                        else:
                            null height 10
                            text "Complete the requirements above to mark this objective as complete.":
                                xsize 580
                                size font_size(22)
                                color "#7a4b2a"
                    
                    elif current_objective == 12:
                        $ can_complete_12 = can_complete_objective_12()
                        if can_complete_12:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 580
                                text_size font_size(26)
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
                                xsize 580
                                size font_size(22)
                                color "#7a4b2a"
                            if journal_show_binding_gem_fallback():
                                null height 18
                                textbutton "Send word through your contacts (secure the Binding Gem)":
                                    xsize 580
                                    text_size font_size(22)
                                    text_color "#2a5a7a"
                                    text_hover_color "#1a3a5a"
                                    action [
                                        Function(journal_grant_binding_gem_fallback),
                                        Hide("journal_panel")
                                    ]
                                text "Your hunt for the Binding Gem has dragged on. Call in a favor to secure it.":
                                    xsize 580
                                    size font_size(20)
                                    color "#5a6a7a"

                    elif current_objective == 13:
                        $ can_complete_13 = can_complete_objective_13()
                        if can_complete_13:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 580
                                text_size font_size(26)
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
                                xsize 580
                                size font_size(22)
                                color "#7a4b2a"
                    
                    elif current_objective == 14:
                        $ can_complete_14 = can_complete_objective_14()
                        if can_complete_14:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 580
                                text_size font_size(26)
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
                                xsize 580
                                size font_size(22)
                                color "#7a4b2a"
                    
                    elif current_objective == 15:
                        $ can_complete_15 = can_complete_objective_15()
                        if can_complete_15:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 580
                                text_size font_size(26)
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
                                xsize 580
                                size font_size(22)
                                color "#7a4b2a"
                    
                    elif current_objective == 9:
                        null height 10
                        text "Choose Your Gambit:" size font_size(26) color "#7a4b2a" xalign 0.5
                        null height 15
                        
                        # Calculate requirements dynamically. One gambit only: once a
                        # branch is chosen the other button goes inactive, so both flags
                        # can never be set at once.
                        $ _branch_chosen = bool(store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False))
                        $ can_assassinate = has_team_assassination() and not _branch_chosen
                        $ can_blackmail = has_team_blackmail() and not _branch_chosen
                        
                        # Assassination path button (same style as objective 16)
                        textbutton "Plan the Governor's Death\n(requires 3 with 70+ Combat or Craft)":
                            xsize 580
                            text_size font_size(26)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                Function(lambda: setattr(store, 'event_flags', getattr(store, 'event_flags', {}))),
                                If(can_assassinate,
                                    [Function(lambda: store.event_flags.update({'branch_assassination': True})),
                                     Function(check_objective_completion)],
                                    None)
                            ]
                            sensitive can_assassinate

                        # Blackmail path button (same style as objective 16)
                        textbutton "Heist and Blackmail\n(requires 1 with 70+ Clever/Charm and 2 with 70+ Charm)":
                            xsize 580
                            text_size font_size(26)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                Function(lambda: setattr(store, 'event_flags', getattr(store, 'event_flags', {}))),
                                If(can_blackmail,
                                    [Function(lambda: store.event_flags.update({'branch_blackmail': True})),
                                     Function(check_objective_completion)],
                                    None)
                            ]
                            sensitive can_blackmail
                        
                        null height 10
                        text "Tip: Check out shops for items to boost skills!" size font_size(20) color "#7a4b2a" italic True
                        
                        if store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False):
                            null height 15
                            textbutton "MARK COMPLETE":
                                xsize 580
                                text_size font_size(26)
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_9_complete", True),
                                    SetVariable("current_objective", 10),
                                    Hide("journal_panel"),
                                    Jump("show_objective_9_dialogue")
                                ]
                    
                    elif current_objective == 16:
                        text "Choose Your Path of Vengeance:" size font_size(26) color "#7a4b2a"
                        
                        $ combat_count = count_workers_with_skill("Combat", 70)
                        $ clever_count = count_workers_with_skill("Clever", 70)
                        
                        textbutton "Path of the Blade - Strike with overwhelming force (requires 5 with Combat 70+)":
                            xsize 580
                            text_size font_size(26)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                If(combat_count >= 5,
                                    [SetVariable("vengeance_path_chosen", True),
                                     SetVariable("vengeance_path", "Blade")],
                                    None)
                            ]
                            sensitive combat_count >= 5
                        
                        textbutton "Path of the Shadow - Strike with cunning subterfuge (requires 5 with Clever 70+)":
                            xsize 580
                            text_size font_size(26)
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                If(clever_count >= 5,
                                    [SetVariable("vengeance_path_chosen", True),
                                     SetVariable("vengeance_path", "Shadow")],
                                    None)
                            ]
                            sensitive clever_count >= 5
                        
                        if store.vengeance_path_chosen:
                            null height 15
                            # Use vengeance_path from objective 16 choice (Blade vs Shadow), not objective 9
                            if getattr(store, "vengeance_path", None) == "Blade":
                                textbutton "MARK COMPLETE - BEGIN THE FINAL STRIKE":
                                    xsize 580
                                    text_size font_size(26)
                                    text_color "#2a7a4b"
                                    text_hover_color "#1a5a3b"
                                    action [
                                        SetVariable("objective_16_complete", True),
                                        SetVariable("tutorial_active", False),
                                        Hide("journal_panel"),
                                        Jump("show_ending_assassination")
                                    ]
                            elif getattr(store, "vengeance_path", None) == "Shadow":
                                textbutton "MARK COMPLETE - BEGIN THE FINAL STRIKE":
                                    xsize 580
                                    text_size font_size(26)
                                    text_color "#2a7a4b"
                                    text_hover_color "#1a5a3b"
                                    action [
                                        SetVariable("objective_16_complete", True),
                                        SetVariable("tutorial_active", False),
                                        Hide("journal_panel"),
                                        Jump("show_ending_blackmail")
                                    ]
                            else:
                                # Fallback for old saves without vengeance_path: use objective 9 branch
                                if store.event_flags.get("branch_blackmail", False):
                                    textbutton "MARK COMPLETE - BEGIN THE FINAL STRIKE":
                                        xsize 580
                                        text_size font_size(26)
                                        text_color "#2a7a4b"
                                        text_hover_color "#1a5a3b"
                                        action [
                                            SetVariable("objective_16_complete", True),
                                            SetVariable("tutorial_active", False),
                                            Hide("journal_panel"),
                                            Jump("show_ending_blackmail")
                                        ]
                                else:
                                    textbutton "MARK COMPLETE - BEGIN THE FINAL STRIKE":
                                        xsize 580
                                        text_size font_size(26)
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
                            text_size font_size(24)
                            text_color "#444444"
                            text_hover_color "#777777"
                            action Show("skip_tutorial_confirm")
                else:
                    text "It is done. The empire stands, and the people who took everything from me do not.":
                        xsize 580
                        xalign 0.0
                        size font_size(30)
                        color "#7a4b2a"
                        text_align 0.0
        
        # Close button positioned at top-right at JOURNAL title height (outside vbox)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action Hide("journal_panel")
            xalign 1.0
            yalign 0.0
            xoffset -45
            yoffset 15

        # "There is more below" hint. The journal has no scrollbar on purpose,
        # but the completion buttons (MARK AS COMPLETE, the objective 9 gambit,
        # the final strike) often sit below the fold. Same column as the close
        # button: a box as wide as it (64 px image at zoom 0.5 = 32), aligned
        # exactly like it, with the arrow centred inside.
        add DynamicDisplayable(fm_journal_more_arrow):
            xalign 1.0
            xoffset -45
            yalign 1.0
            yoffset 17


# ===== SKIP TUTORIAL CONFIRMATION =====
screen skip_tutorial_confirm():
    modal True
    zorder 250
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 320
        background "#1a1a1a"

        vbox:
            spacing 30
            xalign 0.5
            yalign 0.5

            text "Skip Tutorial?":
                size 30
                color "#7a4b2a"
                xalign 0.5

            text "Are you sure you want to skip the tutorial?\nYou'll jump to the final tutorial objective.":
                size 20
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



# ===== NEW OBJECTIVE DIALOGUES =====
# Note: show_objective_7_dialogue is defined in main_flow.rpy

label show_objective_10_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_10_dialogue - STARTING DIALOGUE")
    "Thirty thousand coins. I count the sum twice — not from doubt, but for the pleasure of it."
    "This is no mere wealth. It is the war chest of my vengeance, gathered coin by patient coin."
    "The governor has his armies and his influence. I have patience, and now the gold to make patience dangerous."
    "With such resources I can buy loyalty, purchase silence, and open doors that steel alone could never breach."
    "Whether through blade or whisper, the reckoning draws nearer with every ledger I close."
    "The final pieces of my plan are falling into place."
    "The next objective is in my Journal."
    $ renpy.log("DEBUG: show_objective_10_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_11_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_11_dialogue - STARTING DIALOGUE")
    "Fifteen people on my books, and not one of them only carries plates."
    "They watch, they listen, and they tell me. That is not a workforce, it is a net across the city."
    "Fighters, talkers, people who know which doors are unlocked. Every one of them picked this over something safer."
    "The governor holds his people with fear and wages. Mine stay because they want to, which costs less and holds better."
    "Very little happens here now that I do not hear about before the night is out. His weak points are written down."
    "The net is finished. Now he walks into it."
    "The next objective is in my Journal."
    $ renpy.log("DEBUG: show_objective_11_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_12_dialogue:
    # Milestone image: three relics (Binding Gem, Obsidian Blade, Enchanted Ring), enchantment, breaking the djinn's protection (tutorial_consolidation.png)
    $ _consolidation_bg = get_tutorial_milestone_image(tutorial_milestone_consolidation, ["images/tutorial/tutorial_consolidation.png.png"]) or workers_bg
    scene expression _consolidation_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_12_dialogue - STARTING DIALOGUE")
    "The artifacts are mine. Three of them, and each one solves a problem money could not."
    "The Binding Gem breaks the djinn's protection. That is the thing that has kept him alive this long."
    "The Obsidian Blade goes through whatever a bodyguard or a ward puts in front of it."
    "The Enchanted Ring makes people agree with me who have no reason to."
    "None of them is an ornament. Each was bought for one specific moment on one specific night."
    "That is the last of what I needed. What is left is timing."
    "The next objective is in my Journal."
    $ renpy.log("DEBUG: show_objective_12_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_13_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_13_dialogue - STARTING DIALOGUE")
    "Three buildings under my name, and from them I run the streets the governor only taxes."
    "A room where information moves faster than the drink. A hall where fighters train. A house where people say things they would not say sober."
    "Every one of them is a staging post, and everyone working inside is doing two jobs, whether they know it or not."
    "The governor sits in his castle and calls that power. I hold the markets, the gossip and the debts, which is what the city actually runs on."
    "When the night comes, all of it launches from these three doors."
    "Everything is where it needs to be."
    "The next objective is in my Journal."
    $ renpy.log("DEBUG: show_objective_13_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_14_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_14_dialogue - STARTING DIALOGUE")
    "My best people are picked and standing by, and there is nobody in this city I would rather have."
    "Some of them are for open trouble. The others do quieter work and are better at it than anyone I have met."
    "Between them they can handle it whichever way it goes, blades or paperwork."
    "The governor's guards turn up for wages. Mine chose this, and they will still be standing there at the end of it."
    "He does not have long. This is where it starts."
    "The next objective is in my Journal."
    $ renpy.log("DEBUG: show_objective_14_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_15_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_15_dialogue - STARTING DIALOGUE")
    "Three thousand coins in a single day, and I did not have to stand over any of it."
    "That is what the training and the buildings and the patient years actually bought: a business that runs without me watching it."
    "The governor inherited his money. I built mine out of one deed and a grudge, and mine is still growing."
    "Money like this pays for work that would ruin a smaller operation, and buys the help that loyalty on its own will not."
    "The machine works. All it needs now is somewhere to point it."
    "The next objective is in my Journal."
    $ renpy.log("DEBUG: show_objective_15_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_tutorial_completion_message:
    scene expression event_bg
    show expression Solid("#00000080")
    
    # Unlock the Governor's Castle (backup in case we got here without going
    # through endings). One implementation only: this block used to repeat the
    # helper inline and drifted from it (level 5 here vs 3 there, and it reset
    # reputation and skill_bonus instead of preserving them).
    python:
        unlock_governor_castle("tutorial completion")
    
    "It is done."
    "The governor's rule is over, ended by my hand, with steel or with secrets as I chose."
    "The city answers to somebody who started with nothing and took it one building at a time."
    "The Governor's Castle is mine. Not a symbol of anything: a property, with staff, an income, and better locks than anywhere else I own."
    "Servants, courtesans, guards, chamberlains. The best of them, and all of them working for me now."
    "It is the best-earning thing I have, and it is the last address he ever gave an order from. Both of those matter."
    "The old order is finished. What stands in its place is mine."
    "With the quest complete, new options open up. You can now buy buildings in other cities through the 'Buy Buildings Abroad' option on the map."
    "The castle stays the centre of it, though. Everything else is expansion."
    jump tavern_screen
