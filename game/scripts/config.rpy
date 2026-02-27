################################################################################
### INITIAL CONFIGURATION
################################################################################


define player = Character("Manager")
define academy_director = Character("Academy Director")
define yvara = Character("Yvara")
define arena_promoter = Character("Arena Promoter")
define lab_director = Character("Lab Director")
define narrator = Character(None)  # Narration / no speaker name (e.g. arena trial result)
# Benefit/stat gain messages (same green #006600 as interaction success in event_daily_exec)
define benefit_msg = Character(None, what_color="#006600", what_size=22)
# Backgrounds
define tavern_bg = "images/tavern.png"
define tutorial_dialogue_bg = "tavern.png"
define map_bg = "images/map.png"
define workers_bg = "images/workers_bg.png"  # Background for the worker screens
# Show the full PNG; positioning is handled per-screen
define context_menu_bg = "images/context_menu.png"
define event_bg = "images/event_bg.png"
# Governor tension events (sabotage, spy, poison) - castle/power theme
define governor_event_bg = "images/events/governor_event.png"

init python:
    # Global debug flags to control noisy logging
    # Set to True only when you want to troubleshoot; otherwise keep False
    if not hasattr(store, "debug_image_logging"):
        store.debug_image_logging = False
    if not hasattr(store, "debug_worker_loading_logging"):
        store.debug_worker_loading_logging = False
    if not hasattr(store, "debug_event_loading_logging"):
        store.debug_event_loading_logging = False

    # Keep a reference to the original logger
    if not hasattr(store, "_original_renpy_log"):
        store._original_renpy_log = renpy.log

    def image_debug(message):
        """Logs only when image debug is enabled."""
        if getattr(store, "debug_image_logging", False):
            store._original_renpy_log(message)

    def _should_suppress_log_message(message):
        text = str(message)
        # Always keep essential errors/warnings
        if "ERROR" in text or "WARNING" in text or "Traceback" in text or "Exception" in text:
            return False

        # Suppress generic UI/debug spam
        generic_terms = (
            "DEBUG:", "DEBUG ", "Tavern screen displayed", "Workers button clicked",
            "validate_and_sync_buildings:", "Secondary attributes", "Files Ren'Py sees",
            "Calendar synced:", "Date advanced to:", "BGM DEBUG:",
            "Added trait", "Successfully added", "Cleared daily_report",
            "Updated displayed_workers", "Reloaded available_workers"
        )
        if any(term in text for term in generic_terms):
            return True
        # Suppress image/folder search noise unless explicitly enabled
        if not getattr(store, "debug_image_logging", False):
            image_terms = (
                "get_worker_image", "get_worker_image_random", "get_event_image",
                "get_image_matches_flexible", "get_pattern_matches_flexible",
                "Worker folder", "Processing story image", "Story image:",
                "Outcome analysis -", "Found trait-specific", "Found worker folder",
                "Found default", "Found worker profile", "Found default profile",
                "No specific images found", "No skill images found", "Profile matches", "Selected profile image",
                "Searching for skill patterns", "Found skill image", "Using success background:",
                "Using failure background:", "Using generic event background:",
                "Using default event background:", "Image selection cache cleared",
                "Worker:", "Looking in:", "Base folder:", "Pattern:", "Files in folder:", "Folder: "
            )
            if "DEBUG get_pattern_matches_flexible:" in text:
                return True
            if any(term in text for term in image_terms):
                return True

        # Suppress worker loading noise unless explicitly enabled
        if not getattr(store, "debug_worker_loading_logging", False):
            worker_terms = (
                "Skipping duplicate worker:", "Loaded ", "workers from data/workers",
                "Error accessing workers folder:", "Total workers loaded:", "Worker names: ["
            )
            if any(term in text for term in worker_terms):
                return True

        # Suppress event loading/filtering noise unless explicitly enabled
        if not getattr(store, "debug_event_loading_logging", False):
            event_terms = (
                "Looking for events in subfolder:", "Looking for events in main folder:",
                "event files to load:", "Loading events from file:",
                "Loaded total of ", "select_possible_events starting with",
                "Selected ", "possible events", "WARNING: No events passed the filtering process"
            )
            if any(term in text for term in event_terms):
                return True

        # Suppress daily event execution noise (very verbose)
        # BUT keep profession/worker matching logs for debugging
        daily_terms = (
            "process_daily_events() starting",
            "ENERGY SNAPSHOT:",
            "Event: ", "EARNINGS DEBUG:", 
            "Rebelliousness decay:", "SKILL USE:", "Bonus loot:"
        )
        if any(term in text for term in daily_terms):
            # Allow profession matching and processing logs through
            if ("Checking profession" in text or "Worker " in text and "has job" in text or 
                "Matched!" in text or "Processing worker:" in text or "DAILY:" in text):
                return False
            return True

        # Suppress snapshot chatter (keep errors/warnings)
        # AUTOREST logs are NOT suppressed for debugging
        snapshot_terms = (
            "SNAPSHOT:", "AFTER_LOAD:", "SAVE_STATE:"
        )
        if any(term in text for term in snapshot_terms):
            # But allow AUTOREST through
            if "AUTOREST:" in text:
                return False
            return True

        return False

    def _filtered_renpy_log(message):
        # Drop message if it matches suppression criteria
        if _should_suppress_log_message(message):
            return
        store._original_renpy_log(message)

    # Install filtered logger
    renpy.log = _filtered_renpy_log


    # Disable Ren'Py autosaves (only manual slot saves are supported)
    config.has_autosave = False
    try:
        config.autosave_slots = 0
    except Exception:
        pass

    # Custom quit handler with confirmation that actually works
    def reliable_quit():
        # Force immediate quit - no confirmations, no redirects, just quit
        import sys
        try:
            renpy.quit()
        except:
            try:
                sys.exit()
            except:
                import os
                os._exit(0)
    
    def confirmed_quit():
        # Show confirmation then use reliable quit
        renpy.run(Confirm("Exit the game? Unsaved progress will be lost.", Function(reliable_quit), NullAction()))
    
    config.quit_action = Function(confirmed_quit)

    # Temporarily disable quit while a confirm dialog is on screen to avoid stacking
    def set_quit_action_disabled():
        config.quit_action = NullAction()

    def set_quit_action_smart():
        config.quit_action = Function(confirmed_quit)

    # Keep confirmed quit installed at all times
    config.quit_action = Function(confirmed_quit)
    
    # Custom ESC key handler for hierarchical screen closing
    def custom_escape_action():
        """
        Handle ESC key using the same close actions as the X/Close buttons on screens.
        This ensures consistent behavior and proper navigation flow.
        """
        # Map screens to their specific close actions (same as their close buttons)
        screen_close_actions = {
            # Main screens with back buttons
            "workers": [Hide("workers"), Show("tavern")],
            "map_screen": [Hide("map_screen"), Show("tavern")],
            "Building_select_global": [Hide("Building_select_global"), Show("tavern")],
            
            # Daily report with transition
            "daily_report": [Hide("daily_report"), Jump("day_transition")],
            
            # Shop and building screens
            "shop_selection": Hide("shop_selection"),
            "buy_buildings": Hide("buy_buildings"),
            "buy_servants_table": Hide("buy_servants_table"),
            
            # Worker details (conditional close based on context)
            "worker_details": Hide("worker_details"),
            
            # Sub-screens that return to workers
            "Building_select": [Hide("Building_select"), Show("workers")],
            "job_selection": [Hide("job_selection"), Show("workers")],
            "building_selection": [Hide("building_selection"), Show("workers")],
            
            # Simple hide actions for popups
            "journal_panel": Hide("journal_panel"),
            "worker_selection_popup": Return(),
            "building_type_selection": Return(),
            "adjust_skill_bonus": Return(),
            "adjust_comfort": Return(),
            "rename_building": Return(),
            "interaction_result": Return(),
            "interaction_menu": Return(),
            "interaction_category": Return(),
            "recruitment_outcome": Return(),
            "more_details_screen": Return(),
            "building_filter_menu": Return(),
            "worker_building_filter_menu": Return(),
            "report_details": Return(),
            "manager_inventory": Hide("manager_inventory"),
            
            # Event screens
            "random_event_choice": Return(),
            "choose_event_worker_screen": Return(None),
            "recruitment_choice_screen": Return(),
            "recruitment_result_screen": Return(),
            "recruitment_event_screen": Return(),
            "advanced_recruitment_event_screen": Return(),
            
            # Confirmation dialogs
            "skip_tutorial_confirm": Hide("skip_tutorial_confirm"),
            "error_popup": Return(),
            "confirm_upgrade": Return(),
            "confirm_change_type": Return(),
            "confirm_buy_worker": Return(),
            "confirm_sell_worker": Return(),
            "file_save_dialog": Hide("file_save_dialog"),
            "file_load_dialog": Hide("file_load_dialog"),
            "export_name_input": Hide("export_name_input"),
            "file_browser_simple": Hide("file_browser_simple")
        }
        
        # Check screens in priority order (confirmations first, then main screens)
        priority_order = [
            # High priority - confirmations and dialogs
            "skip_tutorial_confirm", "error_popup", "confirm_upgrade", "confirm_change_type", "confirm_buy_worker", "confirm_sell_worker",
            "file_save_dialog", "file_load_dialog", "export_name_input", "file_browser_simple",
            
            # Event screens (with immediate music fade-out)
            "random_event_choice", "choose_event_worker_screen", "recruitment_choice_screen",
            "recruitment_result_screen", "recruitment_event_screen", "advanced_recruitment_event_screen",
            
            # Configuration popups
            "journal_panel", "worker_selection_popup", "building_type_selection", "adjust_skill_bonus",
            "adjust_comfort", "rename_building", "interaction_result", "interaction_menu",
            "interaction_category", "more_details_screen", "building_filter_menu",
            "worker_building_filter_menu", "report_details", "manager_inventory", "worker_details",
            
            # Shop and building screens (HIGH PRIORITY - user wants these to close easily)
            "shop_selection", "buy_buildings", "buy_servants_table",
            
            # Sub-screens
            "Building_select", "job_selection", "building_selection",
            
            # Main screens and daily report (LOWER priority than shop screens)
            "daily_report", "Building_select_global", "workers"
            
            # Map screen moved to very low priority (user prefers shop closing over map->tavern)
            # "map_screen"  # Commented out - user prefers shop popups to close instead
        ]
        
        # Execute the close action for the first screen found
        for screen_name in priority_order:
            if renpy.get_screen(screen_name):
                # Check if it's an event screen and trigger immediate music fade-out
                event_screens = [
                    "random_event_choice", "choose_event_worker_screen", "recruitment_choice_screen",
                    "recruitment_result_screen", "recruitment_event_screen", "advanced_recruitment_event_screen"
                ]
                if screen_name in event_screens:
                    # Ren'Py .rpy files are not Python-importable modules; call through store.
                    if hasattr(store, "immediate_event_fadeout"):
                        store.immediate_event_fadeout()
                        renpy.log(f"ESC: Stopped event music and restored BGM with silence breaks for '{screen_name}'")
                    else:
                        renpy.log("ESC WARNING: immediate_event_fadeout not found in store")
                
                close_action = screen_close_actions.get(screen_name)
                if close_action:
                    renpy.log(f"ESC: Executing close action for '{screen_name}': {close_action}")
                    if isinstance(close_action, list):
                        # Multiple actions
                        for action in close_action:
                            if hasattr(action, '__call__'):
                                action()
                            else:
                                # It's a Ren'Py action, execute it
                                renpy.run(action)
                    else:
                        # Single action
                        if hasattr(close_action, '__call__'):
                            close_action()
                        else:
                            # It's a Ren'Py action, execute it
                            renpy.run(close_action)
                    return
                else:
                    # Fallback to simple hide if no specific action defined
                    renpy.hide_screen(screen_name)
                    renpy.log(f"ESC: Fallback hide for '{screen_name}'")
                    return
        
        # If no screens are open, show the game menu
        renpy.call_in_new_context("_game_menu")
    
    # We'll use a screen-based approach instead of modifying keymap directly
    
    # Money formatting utility to prevent double $ symbols
    def format_money(amount):
        """
        Format money amount ensuring only one $ symbol.
        Handles both numeric values and strings that might already contain $.
        """
        if isinstance(amount, str):
            # If it's already a string, check if it contains $
            if '$' in amount:
                return amount  # Already formatted
            else:
                try:
                    # Try to convert to number and format
                    num = float(amount)
                    return f"${num:g}"
                except:
                    return f"${amount}"
        else:
            # It's a number, format it
            return f"${amount:g}"

    # Function to mark start of new conversation (can be called from labels)
    def start_new_conversation():
        """Mark the current point as the start of a new conversation."""
        # Simply save the current history size - all messages from this point forward
        # will be part of this conversation
        if hasattr(store, "dialogue_history_start_index"):
            old_start = store.dialogue_history_start_index
        else:
            old_start = 0
            store.dialogue_history_start_index = 0
        
        # Get current history size
        try:
            current_history_size = len(_history_list)
        except:
            current_history_size = 0
        
        store.dialogue_history_start_index = current_history_size
        store.dialogue_history_offset = 0
        renpy.log(f"==========================================")
        renpy.log(f"NEW CONVERSATION STARTED")
        renpy.log(f"Start index: {old_start} -> {store.dialogue_history_start_index}")
        renpy.log(f"Current history size: {current_history_size}")
        renpy.log(f"==========================================")

# ESC key handler screen - this will be shown as an overlay
screen esc_key_handler():
    zorder 1000
    modal False
    key "game_menu" action Function(custom_escape_action)
    key "K_ESCAPE" action Function(custom_escape_action)
    # Emergency music stop with Ctrl+M
    key "K_m" action Function(emergency_stop_all_music)
