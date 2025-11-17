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
    
    5: "The time has come to master the arts of item management and the care of those who serve. I must procure an energy potion from the merchant's stall, transfer it to one of my workers, and witness its effects. Through such endeavors shall I learn to tend to my workers' needs and employ items with wisdom and effectiveness.",
    
    6: "The foundation of any lasting empire lies in its infrastructure and preparedness. I must enhance a building's level and its supplies for the trials ahead. To elevate a building's level shall cost five thousand coins of the realm. Then, I must increase the building's supplies bonus by ten measures, be they equipment, ingredients, or mystical potions - whatever the establishment requires to weather the storms of fortune.",
    
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
        
        for entry in store.manager_inventory:
            if isinstance(entry, tuple):
                if len(entry) > 0 and entry[0] == item_id:
                    return True
            elif isinstance(entry, list):
                # Handle list format: [item_id] or [item_id, quantity] or [item_id, quantity, equipped]
                if len(entry) > 0 and entry[0] == item_id:
                    return True
            elif isinstance(entry, dict):
                # Handle old dict format for backwards compatibility
                if entry.get("item_id") == item_id:
                    return True
            elif isinstance(entry, str):
                # Handle old string format for backwards compatibility
                if entry == item_id:
                    return True
        
        # Check worker inventories (also can be tuples, lists, dicts, or strings)
        for worker in store.workers:
            worker_inventory = worker.get("inventory", [])
            for entry in worker_inventory:
                if isinstance(entry, tuple):
                    if len(entry) > 0 and entry[0] == item_id:
                        return True
                elif isinstance(entry, list):
                    # Handle list format
                    if len(entry) > 0 and entry[0] == item_id:
                        return True
                elif isinstance(entry, dict):
                    # Handle old dict format
                    if entry.get("item_id") == item_id:
                        return True
                elif isinstance(entry, str):
                    # Handle old string format
                    if entry == item_id:
                        return True
        return False
    
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
                return "Progress: Building level enhanced ->, Supplies bonus increased ->"
            elif store.building_upgraded_tutorial:
                return "Progress: 1/2 - Building level enhanced ->, Increase supplies bonus"
            elif store.building_skill_bonus_increased_tutorial:
                return "Progress: 1/2 - Supplies bonus increased ->, Enhance building level"
            else:
                return "Progress: 0/2 - Upgrade building level, Increase supplies bonus"
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
            has_binding_gem = has_item_anywhere("binding_gem")
            has_obsidian_blade = has_item_anywhere("obsidian_blade")
            has_enchanted_ring = has_item_anywhere("enchanted_ring")
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
            return f"Progress:\n- Elite Warriors (Combat 80+): {warriors}/3\n- Elite Agents (Clever/Charm 80+): {unique_agents}/2"
        elif current_objective == 15:
            if store.event_flags.get("daily_revenue_10k_achieved", False):
                return "Progress: Daily revenue goal achieved ->"
            else:
                return "Progress: Achieve 10,000 coins revenue in a single day\nTip: Upgrade buildings, assign skilled workers, increase supplies"
        elif current_objective == 16:
            if store.vengeance_path_chosen:
                return f"Progress: Path chosen -> {store.vengeance_path}\nMark 'Complete' to begin the final strike"
            else:
                combat_count = count_workers_with_skill("Combat", 70)
                clever_count = count_workers_with_skill("Clever", 70)
                blade_ready = "[Ready]" if combat_count >= 5 else "[Not Ready]"
                shadow_ready = "[Ready]" if clever_count >= 5 else "[Not Ready]"
                return f"Progress: Choose your path of vengeance\n- Path of the Blade (Combat 70+): {combat_count}/5 {blade_ready}\n- Path of the Shadow (Clever 70+): {clever_count}/5 {shadow_ready}"
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
        if not getattr(store, 'objective_11_complete', False):
            return False
        return (has_item_anywhere("binding_gem") and 
                has_item_anywhere("obsidian_blade") and 
                has_item_anywhere("enchanted_ring"))
    
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
    
    def check_objective_completion():
        global current_objective, tutorial_active
        global objective_1_complete, objective_2_complete, objective_3_complete, objective_4_complete
        global objective_5_complete, objective_6_complete, objective_7_complete, objective_8_complete
        global objective_9_complete, objective_10_complete, objective_11_complete, objective_12_complete
        global objective_13_complete, objective_14_complete, objective_15_complete, objective_16_complete
        global workers_hired, building_1_type_set, workers_assigned, money, buildings_owned, total_workers
        global objective_just_completed
        
        renpy.log(f"DEBUG: check_objective_completion called - tutorial_active: {tutorial_active}, current_objective: {current_objective}")
        
        if not tutorial_active:
            renpy.log("DEBUG: Tutorial not active, returning")
            return
        
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
            
        elif current_objective == 3 and is_previous_objective_complete(3) and workers_assigned_count >= 3 and not objective_3_complete:
            renpy.log("DEBUG: Objective 3 completed!")
            objective_3_complete = True
            current_objective = 4
            renpy.call_in_new_context("show_objective_3_dialogue")
            
        elif current_objective == 4 and is_previous_objective_complete(4) and money >= 5000 and not objective_4_complete:
            # Double-check that objective 3 is actually complete
            if not objective_3_complete:
                renpy.log(f"DEBUG: Objective 4 check failed - objective 3 not complete! (objective_3_complete={objective_3_complete})")
                return
            # Additional safety check: verify we're actually on objective 4 and previous objectives are done
            if current_objective != 4:
                renpy.log(f"DEBUG: Objective 4 check failed - current_objective is {current_objective}, not 4!")
                return
            renpy.log(f"DEBUG: Objective 4 completed! (money={money}, objective_3_complete={objective_3_complete})")
            objective_4_complete = True
            current_objective = 5
            renpy.call_in_new_context("show_objective_4_dialogue")
            
        elif current_objective == 5 and is_previous_objective_complete(5) and store.potion_purchased and store.potion_transferred and store.potion_used_on_worker and not objective_5_complete:
            renpy.log("DEBUG: Objective 5 completed!")
            objective_5_complete = True
            current_objective = 6
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
    on "show" action Function(check_objective_completion)
    
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
                        size 30
                        color "#7a4b2a"

                    text "[get_current_objective_description()]":
                        xsize 520
                        size 22
                        color "#7a4b2a"
                        text_align 0.0

                    null height 15

                    text "[get_current_objective_progress()]":
                        xsize 520
                        size 20
                        color "#6b6528"

                    null height 20

                    # Tutorial quick access links for objectives 1-7
                    if current_objective == 1:
                        text "Tutorial:":
                            size 22
                            color "#7a4b2a"
                        textbutton "Map > Buy Servants":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("map_screen")]
                    
                    elif current_objective == 2:
                        text "Tutorial:":
                            size 22
                            color "#7a4b2a"
                        textbutton "Manage Buildings > Select building > Building Type":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("Building_select_global")]
                    
                    elif current_objective == 3:
                        text "Tutorial:":
                            size 22
                            color "#7a4b2a"
                        textbutton "Workers > Worker Name > Assign Building > Select Job":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]
                    
                    elif current_objective == 4:
                        text "Tutorial:":
                            size 22
                            color "#7a4b2a"
                        textbutton "Tavern > Next Day":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("tavern")]
                    
                    elif current_objective == 5:
                        text "Tutorial:":
                            size 22
                            color "#7a4b2a"
                        textbutton "Map > Shop":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("map_screen")]
                        textbutton "Workers > Worker Name > Details > Inventory":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("workers")]
                    
                    elif current_objective == 6:
                        text "Tutorial:":
                            size 22
                            color "#7a4b2a"
                        textbutton "Manage Buildings > Select building > Upgrade Building":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("Building_select_global")]
                        textbutton "Manage Buildings > Select building > Skill Bonus":
                            xsize 520
                            text_size 20
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [Hide("journal_panel"), Show("Building_select_global")]
                        text "Tip: Each +10 supplies bonus costs $100/day." size 18 color "#6b6528"
                    
                    elif current_objective == 7:
                        text "Tutorial:":
                            size 22
                            color "#7a4b2a"
                        textbutton "Workers > Worker Name > Details > Interactions > Friendly Chat":
                            xsize 520
                            text_size 20
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
                                text_size 22
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
                                size 18
                                color "#6b6528"
                    
                    elif current_objective == 10:
                        $ can_complete_10 = can_complete_objective_10()
                        if can_complete_10:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size 22
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
                                size 18
                                color "#6b6528"
                    
                    elif current_objective == 11:
                        $ can_complete_11 = can_complete_objective_11()
                        if can_complete_11:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size 22
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
                                size 18
                                color "#6b6528"
                    
                    elif current_objective == 12:
                        $ can_complete_12 = can_complete_objective_12()
                        if can_complete_12:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size 22
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
                                size 18
                                color "#6b6528"
                    
                    elif current_objective == 13:
                        $ can_complete_13 = can_complete_objective_13()
                        if can_complete_13:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size 22
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
                                size 18
                                color "#6b6528"
                    
                    elif current_objective == 14:
                        $ can_complete_14 = can_complete_objective_14()
                        if can_complete_14:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size 22
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
                                size 18
                                color "#6b6528"
                    
                    elif current_objective == 15:
                        $ can_complete_15 = can_complete_objective_15()
                        if can_complete_15:
                            null height 10
                            textbutton "MARK AS COMPLETE":
                                xsize 520
                                text_size 22
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
                                size 18
                                color "#6b6528"
                    
                    elif current_objective == 9:
                        null height 10
                        text "Choose Your Gambit:" size 24 color "#7a4b2a" xalign 0.5
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
                                text_size 24
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
                                text_size 24
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
                        
                        if store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False):
                            null height 15
                            textbutton "Mark Complete":
                                xsize 520
                                text_size 22
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_9_complete", True),
                                    SetVariable("current_objective", 10),
                                    Hide("journal_panel")
                                ]
                    
                    elif current_objective == 16:
                        text "Choose Your Path of Vengeance:" size 22 color "#7a4b2a"
                        
                        $ combat_count = count_workers_with_skill("Combat", 70)
                        $ clever_count = count_workers_with_skill("Clever", 70)
                        
                        textbutton "Path of the Blade - Strike with overwhelming force (requires 5 with Combat 70+)":
                            xsize 520
                            text_size 22
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
                            text_size 22
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
                            textbutton "Mark Complete - Begin the Final Strike":
                                xsize 520
                                text_size 22
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_16_complete", True),
                                    SetVariable("tutorial_active", False),
                                    Hide("journal_panel"),
                                    Function(lambda: renpy.call_in_new_context("show_tutorial_completion_message"))
                                ]

                    if current_objective < 8:
                        null height 15
                        textbutton "Skip Tutorial":
                            xalign 0.0
                            xsize 200
                            text_size 20
                            text_color "#444444"
                            text_hover_color "#777777"
                            action Show("skip_tutorial_confirm")
                else:
                    text "The vengeance is complete! Thy empire stands supreme, and thy enemies lie vanquished.":
                        xsize 580
                        size 28
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
            call objective_1_complete_dialogue from _call_objective_1_complete_dialogue
        elif objective_just_completed == 2:
            $ objective_just_completed = 0
            call objective_2_complete_dialogue from _call_objective_2_complete_dialogue
        elif objective_just_completed == 3:
            $ objective_just_completed = 0
            call objective_3_complete_dialogue from _call_objective_3_complete_dialogue
        elif objective_just_completed == 4:
            $ objective_just_completed = 0
            call objective_4_complete_dialogue from _call_objective_4_complete_dialogue
        elif objective_just_completed == 5:
            $ objective_just_completed = 0
            call objective_5_complete_dialogue from _call_objective_5_complete_dialogue
    return

# ===== NEW OBJECTIVE DIALOGUES =====
label show_objective_10_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    "The coffers overflow with gold, enough to fund my campaign of vengeance. With such wealth, I can move mountains and topple tyrants."
    jump tavern_screen

label show_objective_11_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    "Twenty souls now serve my cause, a network of eyes and ears that spans the city. No secret shall escape my notice, no conspiracy remain hidden."
    jump tavern_screen

label show_objective_12_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    "The artifacts are mine! With these tools of power, I can face any foe, break any enchantment, and charm any ally. The arsenal of vengeance is complete."
    jump tavern_screen

label show_objective_13_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    "Five strongholds now fly my banner, an empire of shadows that rivals any power in this city. From these bastions, I shall launch my final assault."
    jump tavern_screen

label show_objective_14_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    "My elite guard is assembled - warriors who can fell any foe, and agents who can outwit any schemer. With such champions at my side, victory is assured."
    jump tavern_screen

label show_objective_15_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    "My empire generates wealth like a mighty river - ten thousand coins in a single day! This is the power I have built, the machine of prosperity that shall fuel my vengeance."
    jump tavern_screen

label show_tutorial_completion_message:
    scene expression tavern_bg
    show expression Solid("#00000080")
    "The vengeance is complete! Thy empire stands supreme, and thy enemies lie vanquished."
    "With your quest complete, new opportunities arise. You can now purchase buildings in other cities through the 'Buy Buildings Abroad' option on the map."
    jump tavern_screen
