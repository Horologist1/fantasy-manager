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
    9: "The Final Gambit - The Governor's Reckoning"
}

default objective_descriptions = {
    1: "If ever I am to raise the dynasty's empire from the ashes of ruination, then verily, I shall require the hands and hearts of loyal workers. Three workers should suffice to begin this grand endeavor - some may be bought with coin from the market square's bustling commerce, whilst others might be recruited through providence's chance encounters that may span several days, yet oft prove more skilled in their craft.",
    
    2: "The hour of decision draws nigh, wherein I must decree what manner of building type this hallowed place shall become. Perchance a brothel, where secrets flow as freely as wine and influence is currency? Mayhap a restaurant, where respectable coin may be earned through honest trade? Or shall it be an adventurer's guild, where muscle and steel forge connections of power? Each path doth offer different opportunities... and different means by which to gather the strength needed for what is to come.",
    
    3: "Each worker in my service doth possess their own gifts and talents, bestowed by fate and honed through experience. A wise lord doth employ his workers according to their greatest strengths, for 'tis through such wisdom that empires are built. I must assign three workers to their destined professions - for efficiency shall be the cornerstone upon which wealth is swiftly accumulated.",
    
    4: "Gold is the lifeblood of power, and power is the weapon I must wield. Five thousand coins should suffice to begin contemplating the expansion of my domain. Every transaction, every service rendered, every bargain struck brings me ever closer to the resources I shall require for the reckoning that approaches.",
    
    5: "The time has come to master the arts of item management and the care of those who serve. I must procure an energy potion from the merchant's stall, transfer it to one of my workers, and witness its effects. Through such endeavors shall I learn to tend to my workers' needs and employ items with wisdom and effectiveness.",
    6: "The foundation of any lasting empire lies in its infrastructure and preparedness. I must enhance a building's level and its supplies for the trials ahead. To elevate a building's level shall cost five thousand coins of the realm. Then, I must increase the building's supplies bonus by ten measures, be they equipment, ingredients, or mystical potions - whatever the establishment requires to weather the storms of fortune.",
    7: "The time has arrived to know the hearts and minds of those workers who have sworn themselves to my cause. A cordial discourse shall reveal their true nature, their motivations, and the depths of their loyalty. I should speak with any of my workers - beginning with gentle conversation to understand the souls who would follow me into darkness.",
    8: "Behold, the grand design reveals itself at last! Three buildings under my dominion, fifteen loyal workers in my service, and twenty thousand coins to fuel my ambitions. With such resources at my command, I may at last move against the governor who destroyed all that was dear to me.",
    9: "Two paths diverge before me in this wood of vengeance: I may orchestrate the governor's final breath through shadow and steel, or I may corner the wretch with cunning theft and the chains of blackmail. Each road leads to justice, yet by different means shall it be achieved."
}

# ===== HELPER FUNCTIONS =====
init python:
    def get_current_objective_title():
        title = objective_titles.get(current_objective, "Unknown Objective")
        return f"Objective {current_objective}: {title}"
    
    def get_current_objective_description():
        return objective_descriptions.get(current_objective, "No description available.")
    
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
            return f"Progress:\n- Buildings: {buildings_owned}/3\n- Workers: {total_workers}/15\n- Coins: {money}/20000"
        else:
            return "Progress: The path remains shrouded in mystery"

    def _get_worker_skill_value(worker, skill_name):
        try:
            return int(worker.get("skills", {}).get(skill_name, 0))
        except Exception:
            return 0

    def has_team_assassination():
        # Needs 3 workers with >=65 in Combat or Magic
        qualifying = 0
        for w in store.workers:
            if _get_worker_skill_value(w, "Combat") >= 65 or _get_worker_skill_value(w, "Magic") >= 65:
                qualifying += 1
        return qualifying >= 3

    def has_team_blackmail():
        # Needs 2 workers with >=65 Charm, and 1 worker with >=65 Clever OR Charm
        charm_workers = [w for w in store.workers if _get_worker_skill_value(w, "Charm") >= 65]
        clever_workers = [w for w in store.workers if _get_worker_skill_value(w, "Clever") >= 65]
        
        # Need at least 2 charm workers
        if len(charm_workers) < 2:
            return False
        
        # Check if we have a clever worker OR a third charm worker
        if len(charm_workers) >= 3:
            return True
        if len(clever_workers) >= 1:
            return True
        
        return False
    
    def check_objective_completion():
        global current_objective, tutorial_active, objective_1_complete, objective_2_complete, objective_3_complete, objective_4_complete, objective_5_complete, objective_6_complete, objective_7_complete, objective_8_complete
        global workers_hired, building_1_type_set, workers_assigned, money, buildings_owned, total_workers
        global objective_just_completed
        
        renpy.log(f"DEBUG: check_objective_completion called - tutorial_active: {tutorial_active}, current_objective: {current_objective}, workers_hired: {workers_hired}, objective_1_complete: {objective_1_complete}")
        
        if not tutorial_active:
            renpy.log("DEBUG: Tutorial not active, returning")
            return
            
        if current_objective == 1 and workers_hired >= 3 and not objective_1_complete:
            renpy.log("DEBUG: Objective 1 completed! Showing dialogue immediately")
            objective_1_complete = True
            current_objective = 2
            
            # Show dialogue immediately with proper context
            renpy.call_in_new_context("show_objective_1_dialogue")
            
        elif current_objective == 2 and building_1_type_set and not objective_2_complete:
            renpy.log("DEBUG: Objective 2 completed! Showing dialogue immediately")
            objective_2_complete = True
            current_objective = 3
            
            # Show dialogue immediately with proper context
            renpy.call_in_new_context("show_objective_2_dialogue")
            
        elif current_objective == 3 and workers_assigned_count >= 3 and not objective_3_complete:
            renpy.log("DEBUG: Objective 3 completed! Showing dialogue immediately")
            objective_3_complete = True
            current_objective = 4
            
            # Show dialogue immediately with proper context
            renpy.call_in_new_context("show_objective_3_dialogue")
            
        elif current_objective == 4 and money >= 5000 and not objective_4_complete:
            renpy.log("DEBUG: Objective 4 completed! Setting flag for delayed dialogue")
            objective_4_complete = True
            current_objective = 5
            
            # Set flag for delayed dialogue (after daily processing)
            store.pending_objective_4_dialogue = True
            
        elif current_objective == 5 and store.potion_purchased and store.potion_transferred and store.potion_used_on_worker and not objective_5_complete:
            renpy.log("DEBUG: Objective 5 completed! Showing dialogue immediately")
            objective_5_complete = True
            current_objective = 6
            
            # Show dialogue immediately with proper context
            renpy.call_in_new_context("show_objective_5_dialogue")
            
        elif current_objective == 6 and store.building_upgraded_tutorial and store.building_skill_bonus_increased_tutorial and not store.objective_6_complete:
            renpy.log("DEBUG: Objective 6 completed! Showing outro immediately")
            store.objective_6_complete = True
            current_objective = 7
            
            # Show concise outro
            renpy.call_in_new_context("show_objective_6_outro")
            
        elif current_objective == 7 and store.tutorial_friendly_chat_done and not store.objective_7_complete:
            renpy.log("DEBUG: Objective 7 completed! Showing dialogue immediately")
            store.objective_7_complete = True
            current_objective = 8
            
            # Show dialogue immediately with proper context
            renpy.call_in_new_context("show_objective_7_dialogue")

        elif current_objective == 8 and buildings_owned >= 3 and total_workers >= 15 and money >= 20000 and not store.objective_8_complete:
            renpy.log("DEBUG: Objective 8 completed! Advancing to branching objective 9")
            store.objective_8_complete = True
            store.current_objective = 9
            
            # Show dialogue immediately with proper context
            renpy.call_in_new_context("show_objective_8_dialogue")
        
        # Objective 9 is manually completed via button - no auto-detection
        # The ending is triggered directly from the "Mark Complete" button action


# ===== WRAPPER FUNCTION FOR GLOBAL ACCESS =====
init python:
    def check_tutorial_objective():
        """Wrapper function to call check_objective_completion from anywhere"""
        check_objective_completion()



# ===== JOURNAL SCREEN =====
screen journal_panel():
    modal True
    zorder 200
    
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
                    elif current_objective == 9:
                        text "Choose Your Gambit:" size 22 color "#7a4b2a"
                        textbutton "Plan the Governor's Death (requires 3 with 65+ Combat or Magic)":
                            xsize 520
                            text_size 22
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                Function(lambda: setattr(store, 'event_flags', getattr(store, 'event_flags', {}))),
                                Function(lambda: store.event_flags.update({'branch_assassination': True}) if has_team_assassination() else None)
                            ]
                        textbutton "Heist and Blackmail (requires 2 with 65+ Charm and 1 with 65+ Clever or Charm)":
                            xsize 520
                            text_size 22
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action [
                                Function(lambda: setattr(store, 'event_flags', getattr(store, 'event_flags', {}))),
                                Function(lambda: store.event_flags.update({'branch_blackmail': True}) if has_team_blackmail() else None)
                            ]
                        
                        if store.event_flags.get("branch_assassination", False) or store.event_flags.get("branch_blackmail", False):
                            null height 15
                            textbutton "Mark Complete - Begin the Final Strike":
                                xsize 520
                                text_size 22
                                text_color "#2a7a4b"
                                text_hover_color "#1a5a3b"
                                action [
                                    SetVariable("objective_9_complete", True),
                                    If(store.event_flags.get("branch_assassination", False),
                                        [SetVariable("tutorial_active", False), Jump("show_ending_assassination")],
                                        [SetVariable("tutorial_active", False), Jump("show_ending_blackmail")]
                                    ),
                                    Hide("journal_panel")
                                ]

                    if current_objective <= 7:
                        null height 15
                        textbutton "Skip Tutorial":
                            xalign 0.0
                            xsize 200
                            text_size 20
                            text_color "#444444"
                            text_hover_color "#777777"
                            action Show("skip_tutorial_confirm")
                else:
                    text "The teachings have been mastered! Thou art now free to forge thy empire as thou seest fit.":
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

