################################################################################
### IMPROVED BGM SYSTEM WITH EVENT MUSIC
################################################################################

init python:
    import copy as _copy
    if not hasattr(store, 'bgm_volume'):
        store.bgm_volume = 0.6  # Volumen normal de BGM (60%)
    if not hasattr(store, 'event_volume'):
        store.event_volume = 0.4  # Volumen de eventos (40%)

    # Breathing room between BGM repeats. The game deliberately avoids
    # wall-to-wall music; before the loop existed, BGM played ONCE per session
    # and then went silent forever (and the old fallback pointed at a file
    # that doesn't exist).
    BGM_LOOP_GAP_SECONDS = 90.0

    def start_bgm_simple(filename="audio/BGM.ogg"):
        """
        Inicia la música de fondo principal en el canal 'music':
        pista + pausa de respiración, en bucle.
        """
        try:
            renpy.file(filename)
        except Exception:
            renpy.log(f"BGM DEBUG: {filename} not loadable; staying silent")
            return
        try:
            playlist = [filename, "<silence %.1f>" % BGM_LOOP_GAP_SECONDS]
            renpy.music.play(playlist, loop=True, if_changed=True, fadein=3.0, channel="music")
            renpy.music.set_volume(store.bgm_volume, delay=1.0, channel="music")
            renpy.log(f"BGM DEBUG: Started looping BGM ({filename} + {BGM_LOOP_GAP_SECONDS:.0f}s gap)")
        except Exception as e:
            renpy.log(f"BGM DEBUG: could not start BGM: {e}")

    def ensure_bgm_playing():
        """
        Reanuda el bucle ambiental si el canal de música quedó parado
        (p. ej. tras cargar una partida o un stop de emergencia).
        """
        try:
            if not renpy.music.is_playing(channel="music"):
                start_bgm_simple("audio/BGM.ogg")
        except Exception as e:
            renpy.log(f"BGM DEBUG: ensure_bgm_playing failed: {e}")

    def check_and_start_monday_bgm():
        """
        Hook diario (nombre conservado por compatibilidad con event_daily_exec):
        con el bucle ambiental ya no hay lógica de lunes, solo mantenerlo vivo.
        """
        ensure_bgm_playing()

    def play_event_music(event_data=None):
        """
        Reproduce música específica para eventos en el canal 'sound'.
        Reduce el volumen de la BGM principal mientras suena el evento.
        """
        try:
            event_music = None
            
            if event_data and hasattr(event_data, "get"):
                event_music = event_data.get('event_music')
                renpy.log(f"EVENT MUSIC: Found event_music field: {event_music}")
            
            if not event_music:
                event_music = "audio/event.ogg"
                renpy.log("EVENT MUSIC: Using fallback event.ogg")
            
            # Reducir volumen de BGM principal
            renpy.music.set_volume(0.05, delay=1.0, channel="music")
            renpy.log("EVENT MUSIC: BGM volume reduced to 0.05 (5%)")
            
            try:
                renpy.file(event_music)
                renpy.music.play(event_music, loop=False, if_changed=True, fadein=1.5, channel="sound")
                renpy.music.set_volume(0.4, delay=1.0, channel="sound")
                store.event_volume = 0.4
                renpy.log(f"EVENT MUSIC: Successfully playing {event_music} on sound channel at 40% volume")
            except:
                try:
                    renpy.file("audio/event.ogg")
                    renpy.music.play("audio/event.ogg", loop=False, if_changed=True, fadein=1.5, channel="sound")
                    renpy.music.set_volume(0.4, delay=1.0, channel="sound")
                    store.event_volume = 0.4
                    renpy.log("EVENT MUSIC: Fallback to event.ogg successful on sound channel at 40% volume")
                except:
                    renpy.log("EVENT MUSIC: No event music files found, continuing with current BGM")
                        
        except Exception as e:
            renpy.log(f"EVENT MUSIC ERROR: {e}")

    def start_event_with_music(event_data):
        """
        Inicia un evento con la música apropiada basándose en los datos del evento.
        """
        play_event_music(event_data)
        event_id = event_data.get('id', 'unknown') if event_data else 'unknown'
        renpy.log(f"EVENT START: {event_id} with music from JSON data")

    def end_event_with_quick_fadeout():
        """
        Termina un evento con fade-out rápido de la música del evento.
        Restaura el volumen de la BGM principal.
        """
        try:
            renpy.music.set_volume(0.0, delay=1.5, channel="sound")
            
            # Restaurar volumen de BGM principal
            renpy.music.set_volume(store.bgm_volume, delay=1.5, channel="music")
            renpy.log(f"BGM DEBUG: BGM volume restored to {store.bgm_volume} after quick fadeout")
                
        except Exception as e:
            renpy.log(f"BGM QUICK FADEOUT ERROR: {e}")
    
    def immediate_event_fadeout():
        """
        Fade-out inmediato para cuando se cierra la pantalla de evento manualmente.
        Restaura el volumen de la BGM principal.
        """
        try:
            renpy.music.set_volume(0.0, delay=1.0, channel="sound")
            
            # Restaurar volumen de BGM principal
            renpy.music.set_volume(store.bgm_volume, delay=1.0, channel="music")
            renpy.log(f"BGM DEBUG: BGM volume restored to {store.bgm_volume} after immediate fadeout")
                
        except Exception as e:
            renpy.log(f"BGM IMMEDIATE FADEOUT ERROR: {e}")
    
    def emergency_stop_all_music():
        """
        Para toda la música inmediatamente - función de emergencia.
        """
        try:
            renpy.music.stop(channel="music")
            renpy.music.stop(channel="sound")
            # Restaurar volumen normal
            store.bgm_volume = 0.6
            store.event_volume = 0.4
            renpy.log("BGM DEBUG: EMERGENCY STOP - All music stopped")
        except Exception as e:
            renpy.log(f"EMERGENCY STOP ERROR: {e}")

    def run_start_of_day_automation(context=""):
        """
        Start-of-new-day automation, run right after the player closes the
        daily report: relink building->worker refs, auto-supply potions,
        auto-equip, auto-consume, and let the manager restore rested workers.
        (Previously copy-pasted at 5 call sites with drifting feature sets.)
        """
        try:
            renpy.log(f"START_OF_DAY_AUTOMATION: running ({context})")
            # Keep building->worker references consistent (prevents UI seeing stale worker dicts)
            relink = getattr(store, "_relink_assigned_servants_to_store_workers", None)
            if callable(relink):
                relink()
            for w in getattr(store, "workers", []) or []:
                try:
                    store.run_worker_auto_supply_potions(w)
                except Exception as e1:
                    renpy.log(f"run_worker_auto_supply_potions error ({context}): {e1}")
                try:
                    store.run_worker_auto_equip(w)
                except Exception as e2:
                    renpy.log(f"run_worker_auto_equip error ({context}): {e2}")
            thr = getattr(store, "AUTO_CONSUME_THRESHOLD", 0.30)
            ac = getattr(store, "auto_consume_start_of_day", None)
            if callable(ac):
                for w in getattr(store, "workers", []) or []:
                    ac(w, threshold=thr)
            # If anyone was put into rest, let the manager restore their job now
            # that energy/HP may be refilled.
            pm = getattr(store, "process_manager_auto_rest", None)
            if callable(pm):
                pm(restore_only=True)
            # Force UI refresh so screens don't show stale worker dicts/values.
            renpy.restart_interaction()
        except Exception as e:
            try:
                renpy.log(f"START_OF_DAY_AUTOMATION error ({context}): {e}")
            except Exception:
                pass

    def unlock_governor_castle(log_tag=""):
        """
        Create/repair the Governor's Castle entry (idempotent). Used by both
        endings and the tavern-screen consistency check — previously three
        divergent copy-pastes (the repair copy silently upgraded base_level to
        5). Canonical initial base_level is 3; existing upgrades are preserved
        via setdefault so a repair never downgrades or resets progress.
        """
        castle_name = "Governor's Castle"
        renpy.log(f"DEBUG: ===== UNLOCKING GOVERNOR'S CASTLE {log_tag} =====")
        if castle_name not in available_buildings:
            available_buildings[castle_name] = {}
            renpy.log(f"DEBUG: Created new entry for {castle_name} in available_buildings")
        castle = available_buildings[castle_name]
        castle["price"] = 0
        castle.setdefault("reputation", 0)
        castle.setdefault("base_level", 3)
        castle["type"] = "governor_castle"
        castle["assigned_servants"] = castle.get("assigned_servants", [])
        castle["servant_jobs"] = castle.get("servant_jobs", {})
        castle["max_workers"] = 10
        castle["costs"] = 0
        castle["owned"] = True
        castle.setdefault("skill", 50)
        castle.setdefault("skill_bonus", 0)
        if castle_name not in owned_buildings:
            owned_buildings.append(castle_name)
        store.buildings_owned = len(owned_buildings)
        map_button_buildings["Castle"] = castle_name
        custom_names.setdefault(castle_name, castle_name)
        renpy.log(
            f"DEBUG: Castle unlock OK {log_tag} - available: {castle_name in available_buildings}, "
            f"owned: {castle_name in owned_buildings}, map: {'Castle' in map_button_buildings}"
        )

label day_transition:
    # Show black IMMEDIATELY (no transition yet) to cover daily_report
    scene expression Solid('#000000')
    # NOW hide daily_report (it's covered by black, so no transparency)
    $ renpy.hide_screen("daily_report")

    # Start-of-new-day automation hook (player closes the daily report).
    # This is intentionally NOT "during work": it happens right after the report, before returning control.
    $ run_start_of_day_automation("day_transition")
    # Show date text with fade in
    $ day_name = day_names[(store.current_day - 1) % 7]
    $ month_name = month_names[store.current_month - 1]
    $ date_text = f"{day_name}, {store.current_day} {month_name} {store.current_year}"
    show expression Text(date_text, size=42, color="#ffffff") as daytext at truecenter with dissolve
    # Auto-advance after a short time, but still skippable by click
    pause 1.0
    hide daytext with dissolve
    # Fade to tavern
    jump tavern_screen

################################################################################
### MAIN GAME FLOW
################################################################################

label start:
    $ renpy.log("Game started at label start")

    # CRITICAL: Preload trait catalog so workers get 3-5 traits when first loaded.
    # After "Making clean stores", store._trait_def_cache is empty; load it before any worker logic.
    python:
        try:
            if hasattr(store, "refresh_traits_cache"):
                store.refresh_traits_cache(force=True)
                renpy.log("START: Preloaded trait catalog")
        except Exception as e:
            renpy.log(f"START: refresh_traits_cache error: {e}")

    # CRITICAL: Check if this is a load operation before doing ANYTHING else
    python:
        # Check multiple indicators that this might be a load
        is_load_operation = False
        
        # Method 1: Check if _just_loaded was set by after_load
        if getattr(store, "_just_loaded", False):
            is_load_operation = True
            renpy.log("START: _just_loaded=True detected")
        
        # Method 2: Check if Ren'Py's loadname is set
        try:
            if getattr(renpy.loadsave, "loadname", None):
                is_load_operation = True
                renpy.log("START: Ren'Py loadname detected")
        except:
            pass
        
        # Method 3: Check if game_initialized without explicit new game flag
        if not getattr(store, "_force_new_game_reset", False) and getattr(store, "game_initialized", False):
            is_load_operation = True
            renpy.log("START: game_initialized=True without new_game flag")
        
        # Method 4: Check if we have save data (money != default, or workers exist)
        # IMPORTANT: explicit New Game must override stale in-memory state.
        if not getattr(store, "_force_new_game_reset", False):
            if getattr(store, "money", 6000) != 6000 or len(getattr(store, "workers", [])) > 0:
                is_load_operation = True
                renpy.log(f"START: Non-default state detected (money={getattr(store, 'money', 6000)}, workers={len(getattr(store, 'workers', []))})")
        
        # If this is a load, skip ALL reset logic and go straight to tavern
        if is_load_operation:
            store._just_loaded = False
            store.is_new_game = False
            store.game_initialized = True
            store._force_new_game_reset = False
            renpy.log("START: Load operation detected, skipping all reset logic and jumping to tavern_screen")
            renpy.jump("tavern_screen")
    
    # CRITICAL: Clear player_name and player_title FIRST, before anything else
    # This prevents Ren'Py from restoring old values from persistent/defaults
    # We'll set them properly later if this is actually a load, or leave them empty for new game
    python:
        if getattr(store, "_force_new_game_reset", False):
            # This is an explicit new game start; clear player data immediately
            store.player_name = ""
            store.player_title = ""
            renpy.log("START: Cleared player_name and player_title for new game")
    
    # Start BGM at game start (only plays once, no loops)
    $ start_bgm_simple("audio/BGM.ogg")
    
    # Age verification check - MUST be first, before any other conditions
    $ age_verified_status = getattr(persistent, 'age_verified', False)
    $ renpy.log(f"Age verification status: {age_verified_status}")
    if not age_verified_status:
        $ renpy.log("Showing age verification screen")
        call age_verification from _call_age_verification
    else:
        $ renpy.log("Age verification already completed, skipping")
    
    # IMPORTANT: Do not use is_new_game to decide skipping the intro here.
    # Use store._just_loaded instead (set during actual load). This prevents "New Game"
    # from accidentally inheriting state and skipping the intro.

    # CRITICAL: Ensure this is a new game by explicitly setting flags
    # This prevents contamination from previous loads
    python:
        # Only reset data when this is truly a new game (explicit flag).
        if getattr(store, "_force_new_game_reset", False):
            # Clear ALL persistent flags related to loading to prevent cross-contamination
            persistent._slot_to_apply = None
            persistent.loaded_via_save = False
            persistent._context_restored = False
            # Reset which intro popups were shown (so they appear again in new game if enabled).
            # Do NOT reset intro_popups_enabled – user preference persists across new games.
            persistent.intro_popups_seen = {}
            store._intro_popup_current = None
            # Note: We don't clear _slot_snapshots or _last_snapshot as they're needed for saves
            # But we ensure load flags are cleared
            
            # CRITICAL: Clear store data from previous games to prevent contamination
            # This ensures a truly fresh start
            store.workers = []
            store.available_workers = []
            store.owned_buildings = ["Building 1"]
            store.custom_names = {"Building 1": "Building 1"}
            store.map_button_buildings = {}
            store.player_name = ""
            store.player_title = ""
            store.money = 6000
            store.current_day = 1
            store.current_month = 1
            store.current_year = 1
            # Clear calendar restore flags to avoid cross-save confusion
            store._calendar_restored_from_json = False
            store._calendar_restored_values = None
            store.event_flags = {}
            store.event_occurrences = {}
            store.event_last_occurred = {}
            store.manager_interactions_today = 0
            store.last_take_a_walk_day = None
            store.last_save_slot = None
            
            # Set new game flags explicitly
            store.is_new_game = True
            store.game_initialized = False
            
            renpy.save_persistent()
            renpy.log("NEW GAME: Cleared all load-related persistent flags, reset store data, and set is_new_game=True")
            store._force_new_game_reset = False
        else:
            renpy.log("START: game_initialized=True, skipping new game reset")

    scene expression workers_bg
    show expression Solid("#00000080")  # Semi-transparent black overlay
    
    # Initialize tutorial variables
    $ tutorial_active = True
    $ current_objective = 1
    $ tutorial_skipped = False
    $ objective_1_complete = False
    $ objective_2_complete = False
    $ objective_3_complete = False
    $ objective_4_complete = False
    $ objective_5_complete = False
    $ workers_hired = 0
    $ building_1_type_set = False
    $ workers_assigned = False
    $ help_screen_active = True  # Tooltips enabled by default
    $ buildings_owned = 1
    $ total_workers = 0
    $ objective_dialogue_triggered = False
    
    # Start with the inheritance scene
    call tutorial_start from _call_tutorial_start
    
    # CRITICAL: Ensure player_name and player_title are empty before asking for input
    # This prevents old values from appearing in the input field
    python:
        store.player_name = ""
        store.player_title = ""
        renpy.log("NEW GAME: Cleared player_name and player_title before input")
    
    menu:
        "Choose your title"
        "Lord":
            $ player_title = "Lord"
        "Lady":
            $ player_title = "Lady"

    python:
        # Ensure we're using a fresh input, not a restored value
        store.player_name = ""
        player_name = renpy.input("Enter your name:", length=32, default="")
        player_name = player_name.strip()
        if not player_name:
            player_name = "Manager"
        store.player_name = player_name
        renpy.log(f"NEW GAME: Player set name to '{player_name}' with title '{player_title}'")

    "Very well, [player_title] [player_name]. Let's take back our emporium."

    # Transition to black and show initial date (like day_transition)
    scene expression Solid('#000000') with dissolve
    $ day_name = day_names[(store.current_day - 1) % 7]
    $ month_name = month_names[store.current_month - 1]
    $ date_text = f"{day_name}, {store.current_day} {month_name} {store.current_year}"
    show expression Text(date_text, size=42, color="#ffffff") as daytext at truecenter
    # Auto-advance after a short time, but still skippable by click
    pause 1.0
    hide daytext
    scene expression Solid('#000000') with dissolve

    # Initialize the calendar with forced reset ONLY for new game
    # When loading, the calendar should already be restored by _apply_game_state
    # Only call initialize_calendar if it's a new game, otherwise trust the loaded date
    if getattr(store, 'is_new_game', True):
        $ initialize_calendar(force_reset=True)
    else:
        # For loaded games, only initialize if calendar is truly missing/invalid
        # This prevents overwriting a date that was just restored from save
        $ initialize_calendar(force_reset=False)

    # Initialize unlocked_shops ONLY in store (per-save, NOT in persistent to avoid cross-save bleed)
    if getattr(store, 'is_new_game', True):
        # New game: initialize default shops
        $ store.unlocked_shops = {"shop1": True, "shop2": False, "shop3": False}
        $ renpy.log("Initialized unlocked_shops for NEW GAME: " + str(store.unlocked_shops))
    else:
        # Loaded game: ensure unlocked_shops exists (should be restored from JSON save)
        if not hasattr(store, 'unlocked_shops') or not store.unlocked_shops:
            $ store.unlocked_shops = {"shop1": True, "shop2": False, "shop3": False}
            $ renpy.log("Initialized unlocked_shops as fallback for loaded game: " + str(store.unlocked_shops))
        else:
            $ renpy.log("unlocked_shops restored from save: " + str(store.unlocked_shops))

    # FIXED: Do NOT reinitialize workers - they're already defined with 'default workers = []'
    # The line below was causing workers to reset on load:
    # $ store.workers = [] if not hasattr(store, "workers") else store.workers
    $ renpy.log("Initial store.workers: " + str([w.get("name", "Unknown") for w in store.workers]))

    # Load available workers for the market
    $ available_workers = load_buy_workers()
    $ renpy.log("Loaded available_workers: " + str([w["name"] for w in available_workers]))

    # Load interactions
    $ interactions = load_interactions()
    $ renpy.log("Loaded interactions: " + str([inter["name"] for inter in interactions]))

    
    python:
        for worker in store.workers:
            ensure_worker_defaults(worker)
        for worker in store.available_workers:
            ensure_worker_defaults(worker)
        renpy.log("After defaults - store.workers: " + str([w["name"] for w in store.workers]))
        renpy.log("After defaults - available_workers: " + str([w["name"] for w in available_workers]))

    python:
        reset_limited_events()

    python:
        for worker in store.workers:
            if "skill_uses" not in worker:
                worker["skill_uses"] = {skill_name: 0 for skill_name in worker["skills"]}
            if "level" not in worker:
                worker["level"] = 1
            if "success_count" not in worker:
                worker["success_count"] = 0

    python:
        for worker in store.workers:
            if "energy" not in worker:
                worker["energy"] = calculate_max_energy(worker)
            if "comfort_level" not in worker:
                worker["comfort_level"] = worker.get("comfort_desired", 1)
 
    python:
        update_displayed_workers()
        renpy.log("After update_displayed_workers - displayed_workers: " + str([w["name"] for w in displayed_workers]))

    # Music already started in main menu via start_bgm_simple.
    # Do not touch the BGM here to avoid cuts.
    
    # Mark new game flags so subsequent loads that reach start don't re-init
    $ game_initialized = True
    $ is_new_game = False

    # Show the ESC key handler screen
    show screen esc_key_handler

    jump tavern_screen

label show_objective_1_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_1_dialogue - STARTING DIALOGUE")
    
    "My eyes survey the three workers who have sworn themselves to my cause. A modest beginning, yet from such humble seeds mighty empires grow."
    "These loyal souls are the first foundation of what I shall rebuild—and one day, the path to the reckoning."
    "Now I must put them to their destined labors. Let me consult my journal to discern the way ahead."
    $ renpy.log("DEBUG: show_objective_1_dialogue - FINISHED DIALOGUE")
    # Invoked via call/call_in_new_context: must return (a jump here leaked the frame).
    return

label show_objective_2_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_2_dialogue - STARTING DIALOGUE")
    "This is the business I shall focus upon, for now."
    "The governor began with naught but ambition burning in his breast—I walk the same treacherous path he once trod. But the end will be different."
    "My journal has been inscribed with the next duty."
    $ renpy.log("DEBUG: show_objective_2_dialogue - FINISHED DIALOGUE")
    return

label show_objective_3_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_3_dialogue - STARTING DIALOGUE")
    "Each worker brings their own gifts and talents to this enterprise."
    "Choose the right soul for the right profession—these are the foundations of the power I need. We shall be well upon our way to prosperity."
    "Should I require more detail on how they have performed, I may open the Daily Report and examine the results."
    "My journal has been inscribed with the next duty."
    $ renpy.log("DEBUG: show_objective_3_dialogue - FINISHED DIALOGUE")
    return

label show_objective_4_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_4_dialogue - STARTING DIALOGUE")
    $ store.objective_4_dialogue_shown = True
    "Five thousand coins in my coffers. Not a fortune, but enough to start thinking about expansion."
    "Every coin is another step toward the resources the day of reckoning will demand. I need infrastructure—improving the building to hold more workers, or the gear to be better prepared. Perhaps a bit of both."
    "Journal has been updated with the next objective."
    $ renpy.log("DEBUG: show_objective_4_dialogue - FINISHED DIALOGUE")
    return

label show_objective_5_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_5_dialogue - STARTING DIALOGUE")
    "Good. Now I understand how to manage my workers' needs and use items effectively."
    "This knowledge will be vital when my operation grows—and when the governor takes notice of what I am building."
    "Journal has been updated with the next objective."
    $ store.current_objective = 6
    call show_objective_6_intro from _call_show_objective_6_intro
    $ renpy.log("DEBUG: show_objective_5_dialogue - FINISHED DIALOGUE")
    return

label show_objective_6_intro:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_6_intro - STARTING DIALOGUE")
    "Time to strengthen my foundation."
    "I will upgrade a building's level and raise its Building skill bonus—preparation for what comes when I dare to act. The upgrade costs 1,000 coins."
    $ renpy.log("DEBUG: show_objective_6_intro - FINISHED DIALOGUE")
    return

label show_objective_6_outro:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_6_outro - STARTING DIALOGUE")
    "Excellent. The building can accommodate more souls now."
    "The foundation is stronger. Time to expand the scale of this entire operation."
    $ renpy.log("DEBUG: show_objective_6_outro - FINISHED DIALOGUE")
    call show_objective_7_intro from _call_show_objective_7_intro
    return

label show_objective_7_intro:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_7_intro - STARTING DIALOGUE")
    "Time to meet the people who make this place run."
    "I shall invite one of my workers to a Friendly Lunch—breaking bread together—to learn their hearts and motivations."
    "Journal has been updated with the next objective."
    $ renpy.log("DEBUG: show_objective_7_intro - FINISHED DIALOGUE")
    return

label show_objective_7_dialogue:
    scene expression workers_bg
    show expression Solid("#00000080")
    $ renpy.log("DEBUG: show_objective_7_dialogue - STARTING DIALOGUE")
    "We have broken bread together. Over food and drink, they spoke of their hopes, their past, and what binds them to this house."
    "To share a meal is to offer trust—and to receive it in return. I have seen the face behind the servant, the person beneath the duty."
    "Such understanding is the foundation upon which loyalty is built. Those who eat at my table are no longer merely workers; they are souls I know, and who know me in turn."
    "The governor rules through fear and gold. Loyalty is a weapon he does not have. I shall build something different: a circle of those who have chosen to stand with me."
    "My journal has been inscribed with the next duty. The path to the grand design lies ahead."
    $ renpy.log("DEBUG: show_objective_7_dialogue - FINISHED DIALOGUE")
    return

label show_objective_8_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_8_dialogue - STARTING DIALOGUE")
    "I possess what I require for now, yet this is merely the dawn of my ascension."
    "Two buildings now stand under my banner, their foundations as solid as my resolve."
    "Ten souls serve my cause, each one chosen for their loyalty and skill."
    "Ten thousand coins fill my coffers, a fortune that whispers of greater things to come."
    "This is the threshold where whispers become rumors, where shadows take notice, where the city's power brokers begin to mark my name in their ledgers."
    "The governor may still believe himself secure in his fortress, but I have built something he cannot ignore: an empire of shadows that grows stronger with each passing day."
    "My network spreads through the city like roots through stone, finding purchase in places he never thought to guard."
    "My workers are not mere servants—they are my eyes, my ears, my hands reaching into every corner of this accursed city."
    "From this moment forth, the true game begins."
    "Every choice I make, every resource I gather, every alliance I forge brings me closer to the moment when I shall stand before the governor and claim what is rightfully mine."
    "My journal hath been inscribed with the next duty. The path ahead is clear, and I shall walk it without hesitation."
    $ renpy.log("DEBUG: show_objective_8_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_9_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_9_dialogue - STARTING DIALOGUE")
    if store.event_flags.get("branch_assassination", False):
        "The die is cast. I have chosen the path of the blade—a swift, decisive end to the governor's reign."
        "In the quiet hours before dawn, when even the guards grow complacent, my most skilled warriors shall strike."
        "They are not mere killers—they are instruments of justice, honed to perfection, each one a master of their craft."
        "The governor believes himself protected by walls and guards, by wealth and influence."
        "But steel cares not for such things. When the moment comes, when his guard is down and the shadows offer their protection, my blade shall find its mark."
        "This path requires strength, but it is clean. One strike, and the tyrant falls."
        "The city shall wake to find their oppressor dead, and they shall know that those who cross me do not live to regret it."
        "There is a certain poetry to it—the man who thought himself untouchable, brought low by the very shadows he sought to control."
        "His blood shall water the ground, and from that soil, a new order shall rise."
        "My journal hath been inscribed with the next duty. I must gather the resources needed to see this plan through to its bloody conclusion."
        "Gold, weapons, and the unwavering loyalty of those who shall strike the fatal blow."
    elif store.event_flags.get("branch_blackmail", False):
        "The die is cast. I have chosen the path of shadows—a subtle game of secrets and leverage that shall bring the governor to his knees."
        "My cleverest agents shall infiltrate his sanctum, moving like ghosts through corridors he believes secure."
        "They shall uncover the dark truths he hides from the world—the bribes, the betrayals, the skeletons locked away in forgotten chambers."
        "With those secrets in hand, he shall dance to my tune."
        "Every word he speaks, every decision he makes, shall be guided by the knowledge that I hold the keys to his destruction."
        "This path requires cunning, but it is elegant. No blood need be spilled, yet the governor's power shall crumble all the same."
        "He shall watch helplessly as his influence wanes, as his allies turn away, as his carefully constructed empire of lies collapses around him."
        "There is a certain satisfaction in watching a tyrant brought low not by force, but by his own secrets."
        "He shall learn that the most dangerous weapon is not a blade, but knowledge—and I am its master."
        "My journal hath been inscribed with the next duty. I must gather the resources needed to see this plan through to its inevitable conclusion."
        "Agents, information, and the patience to let the trap close slowly around my prey."
    else:
        "A choice has been made, though the path forward remains shrouded in uncertainty."
        "My journal hath been inscribed with the next duty."
    $ renpy.log("DEBUG: show_objective_9_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

# ===== EPIC ENDINGS =====
label show_ending_assassination:
    # Optional milestone image: throne room (ending_blade_throne.png)
    $ _ending_bg = get_tutorial_milestone_image(tutorial_milestone_ending_blade) or event_bg
    scene expression _ending_bg
    $ renpy.log("DEBUG: show_ending_assassination - STARTING EPIC ENDING")
    
    # Resolve governor tension - remove fear traits from workers
    $ healed_workers = resolve_governor_tension()
    
    python:
        # Get the workers who participated in the assassination
        assassination_team = [w for w in store.workers if (w.get("skills", {}).get("Combat", 0) >= 65 or w.get("skills", {}).get("Craft", 0) >= 65)]
        team_names = [w.get("name", "Unknown") for w in assassination_team[:3]]
        building_count = len(store.owned_buildings) if hasattr(store, 'owned_buildings') else buildings_owned
        worker_count = len(store.workers) if hasattr(store, 'workers') else total_workers
    
    "The hour of reckoning hath arrived. The moon hangs low in the midnight sky, casting long shadows across the cobblestone streets of the governor's district."
    
    "Three of my most trusted souls stand ready at my side: [team_names[0] if len(team_names) > 0 else 'a loyal warrior'], [team_names[1] if len(team_names) > 1 else 'a skilled mage'], and [team_names[2] if len(team_names) > 2 else 'a deadly assassin']. Their eyes burn with the same fire that consumed my family's legacy."
    
    "From the [building_count] strongholds I have built, from the [worker_count] souls who have sworn fealty to my cause, from the [money] coins that have filled my coffers - all of it hath led to this single, decisive moment."
    
    "The governor's mansion looms before us, a monument to corruption and greed. But tonight, it shall become a tomb."
    
    "We move like shadows through the night, my team of warriors and mages executing the plan with lethal precision."
    
    "The governor's guards fall silently, their throats cut or their minds shattered by arcane forces before they can raise the alarm."
    
    "The governor himself sits in his study, surrounded by the spoils of his tyranny - paintings seized from my family's estate, ledgers filled with debts called in under false pretenses."
    
    "Trophies from the lives he destroyed line the walls, each one a testament to his corruption."
    
    "He looks up as we enter, his face a mask of surprise that quickly turns to terror. 'You... you cannot be here. The guards...'"
    
    "'The guards are dead,' I reply, my voice cold as the grave. 'And so shall you be, before this night ends.'"
    
    "My team moves with practiced efficiency. [team_names[0] if len(team_names) > 0 else 'The warrior']'s blade finds its mark even as [team_names[1] if len(team_names) > 1 else 'the mage']'s spells bind the governor in chains of pure force."
    
    "[team_names[2] if len(team_names) > 2 else 'The assassin'] delivers the final blow - quick, clean, merciless."
    
    "The governor's body slumps to the floor, his blood mingling with the wine from the shattered goblet he had been holding."
    
    "Justice, at long last, served not by the law he corrupted, but by the steel and sorcery of those he wronged."
    
    "As dawn breaks over the city, word spreads like wildfire. The governor is dead. The balance of power hath shifted irrevocably."
    
    "My empire stands unchallenged now. The [building_count] buildings that bear my banner, the [worker_count] souls who serve my will, the vast fortune I have amassed."
    
    "All of it secured through this single act of vengeance."
    
    "The city's elite scramble to curry favor with the new power in their midst. They come bearing gifts, seeking alliances, offering tribute."
    
    "I accept their offerings, but I do not forget."
    
    "I do not forget how they stood by while my family was destroyed. I do not forget how they profited from our ruin. But for now, I am content."
    
    "The governor's head adorns a spike above my main establishment. A warning to all who would cross me. A declaration that the old order is dead, and a new empire hath risen in its place."
    
    "My revenge is complete. But my ambition? That is only beginning."
    
    "The sun rises on a new day, and I am its master."
    $ renpy.log("DEBUG: show_ending_assassination - EPIC ENDING COMPLETE")
    $ tutorial_active = False
    
    # Manager level up (increment, so other sources can have raised level already)
    $ store.manager_level = getattr(store, 'manager_level', 1) + 1
    call screen manager_levelup_benefit
    
    # Unlock the Governor's Castle
    $ unlock_governor_castle("(ASSASSINATION)")

    "The Governor's Castle is now yours. You can access it from the map."

    jump tavern_screen

label show_ending_blackmail:
    # Optional milestone image: study (ending_blackmail_study.png; also tries .png.png if file was misnamed)
    $ _ending_bg = get_tutorial_milestone_image(tutorial_milestone_ending_blackmail, ["images/tutorial/ending_blackmail_study.png.png"]) or event_bg
    scene expression _ending_bg
    $ renpy.log("DEBUG: show_ending_blackmail - STARTING EPIC ENDING")
    
    # Resolve governor tension - remove fear traits from workers
    $ healed_workers = resolve_governor_tension()
    
    python:
        # Get the workers who participated in the blackmail
        blackmail_team = []
        charm_workers = [w for w in store.workers if w.get("skills", {}).get("Charm", 0) >= 65]
        clever_workers = [w for w in store.workers if w.get("skills", {}).get("Clever", 0) >= 65]
        if len(charm_workers) >= 2:
            blackmail_team = charm_workers[:2]
            if clever_workers:
                blackmail_team.append(clever_workers[0])
            elif len(charm_workers) >= 3:
                blackmail_team.append(charm_workers[2])
        team_names = [w.get("name", "Unknown") for w in blackmail_team[:3]]
        building_count = len(store.owned_buildings) if hasattr(store, 'owned_buildings') else buildings_owned
        worker_count = len(store.workers) if hasattr(store, 'workers') else total_workers
    
    "The hour of reckoning hath arrived, but not through the path of the blade. The governor's downfall shall come not from steel, but from the chains of his own corruption."
    
    "Three of my most cunning souls stand ready: [team_names[0] if len(team_names) > 0 else 'a master of charm'], [team_names[1] if len(team_names) > 1 else 'a skilled seducer'], and [team_names[2] if len(team_names) > 2 else 'a clever strategist']."
    
    "Their weapons are not swords or spells, but secrets and seduction."
    
    "From the [building_count] strongholds I have built, from the [worker_count] souls who have sworn fealty to my cause, from the [money] coins that have filled my coffers."
    
    "All of it hath led to this single, decisive moment."
    
    "The governor's mansion looms before us, but we do not come to kill. We come to steal what he values most: his secrets, his reputation, his power."
    
    "Under cover of darkness, my team executes a plan of exquisite complexity."
    
    "[team_names[0] if len(team_names) > 0 else 'The charmer'] gains entry to the governor's private study, seducing a guard with honeyed words and false promises."
    
    "[team_names[1] if len(team_names) > 1 else 'The seducer'] distracts the governor himself in his chambers, while [team_names[2] if len(team_names) > 2 else 'the clever one'] cracks the safe containing documents of incalculable value."
    
    "Ledgers detailing embezzlement. Letters proving bribery of city officials. Contracts showing illegal dealings with criminal syndicates."
    
    "Evidence that would destroy the governor's reputation and send him to the gallows."
    
    "We emerge from the mansion like shadows, carrying with us the governor's entire empire of lies, written in his own hand and sealed with his own seal."
    
    "The next morning, I send a messenger to the governor's mansion."
    
    "The message is simple:"
    "'I have in my possession documents that would see you hanged."
    "Your choice is simple - surrender your holdings to me, publicly declare me your successor, and leave this city forever."
    "Or face the consequences.'"
    
    "The governor's response comes that evening. He is a broken man, his power stripped away not by force of arms, but by the weight of his own sins brought to light."
    
    "He signs the documents transferring his properties to my name. He makes the public declaration, his voice trembling with fear and shame."
    
    "And then he flees, a shadow of the tyrant he once was."
    
    "As the sun sets on his departure, word spreads throughout the city. The governor hath been brought low. The balance of power hath shifted irrevocably."
    
    "My empire stands unchallenged now. The [building_count] buildings that bear my banner, the [worker_count] souls who serve my will, the vast fortune I have amassed."
    
    "All of it secured through cunning and blackmail, the tools of a true master of the shadows."
    
    "The city's elite scramble to curry favor with the new power in their midst. They come bearing gifts, seeking alliances, offering tribute."
    
    "I accept their offerings, but I do not forget."
    
    "I do not forget how they stood by while my family was destroyed. I do not forget how they profited from our ruin. But for now, I am content."
    
    "The governor's portrait hangs in my main establishment, but with a black ribbon across it. A warning to all who would cross me. A declaration that the old order is dead, and a new empire hath risen in its place."
    
    "My revenge is complete. But my ambition? That is only beginning."
    
    "The sun rises on a new day, and I am its master."
    $ renpy.log("DEBUG: show_ending_blackmail - EPIC ENDING COMPLETE")
    $ tutorial_active = False
    
    # Manager level up (increment, so other sources can have raised level already)
    $ store.manager_level = getattr(store, 'manager_level', 1) + 1
    call screen manager_levelup_benefit
    
    # Unlock the Governor's Castle
    $ unlock_governor_castle("(BLACKMAIL)")

    "The Governor's Castle is now yours. You can access it from the map."

    jump tavern_screen

label tavern_screen():
    $ renpy.log("DEBUG: tavern_screen label - STARTING")

    # Call-stack hygiene: nothing legitimately returns past the hub (no `call
    # tavern_screen` exists anywhere). Any frames still on the return stack here
    # are leaks from flows that were call-ed but exited via jump; historically
    # they accumulated forever, got pickled into saves, and made stray `return`
    # statements teleport the player. Clear them.
    python:
        try:
            _stale_frames = renpy.get_return_stack()
            if _stale_frames:
                renpy.log(f"DEBUG: tavern_screen clearing {len(_stale_frames)} stale call frame(s).")
                renpy.set_return_stack([])
        except Exception as _e:
            renpy.log(f"WARNING: tavern_screen could not clear return stack: {_e}")

    # Keep the ambient BGM loop alive (idempotent; covers loads and stops).
    $ ensure_bgm_playing()


    $ current_obj = getattr(store, 'current_objective', None)
    $ tutorial_act = getattr(store, 'tutorial_active', False)
    $ obj4_shown = getattr(store, 'objective_4_dialogue_shown', False)
    $ renpy.log(f"DEBUG: tavern_screen - current_objective={current_obj}, tutorial_active={tutorial_act}, money=${money}, obj4_dialogue_shown={obj4_shown}")
    
    # Verify castle is properly set up if tutorial is complete
    python:
        if not tutorial_act:
            castle_name = "Governor's Castle"
            # If castle should exist but isn't properly set up, repair it
            if castle_name in owned_buildings and (
                castle_name not in available_buildings
                or "Castle" not in map_button_buildings
                or castle_name not in custom_names
            ):
                renpy.log(f"WARNING: {castle_name} owned but inconsistent, repairing...")
                unlock_governor_castle("(TAVERN REPAIR)")
    
    # Check if objective 4 dialogue is pending
    if getattr(store, 'pending_objective_4_dialogue', False) and not obj4_shown:
        $ store.pending_objective_4_dialogue = False
        $ renpy.log("DEBUG: Showing pending objective 4 dialogue from tavern_screen")
        call show_objective_4_dialogue from _call_show_objective_4_dialogue
    
    # Removed pending_exit auto-quit; rely on standard confirmation and quit flow
    
    # Call the tavern screen
    call screen tavern
    # Safety net: if a menu/options return closed tavern flow and no
    # hub screen is active, recover to tavern instead of leaving a bare scene.
    python:
        _hub_screens = (
            "tavern",
            "map_screen",
            "workers",
            "manager_inventory",
            "Building_select_global",
            "academy_menu",
            "arena_menu",
            "shop_selection",
        )
        _any_hub_visible = any(renpy.get_screen(_s) for _s in _hub_screens)
    if not _any_hub_visible:
        $ renpy.log("DEBUG: tavern_screen safety net triggered (no hub screen visible), recovering tavern UI.")
        show screen tavern
        pause 0.01
        jump tavern_screen
    # Never `return` past the hub: there is no caller, so a bare return used to
    # pop a stale leaked frame (teleporting the player) or end the game once the
    # stack is clean. Loop back into the hub instead.
    jump tavern_screen

label next_day:
    $ renpy.log("DEBUG: next_day label - STARTING")
    # Soft chime marking the day transition
    $ play_ui_sound("day_chime")
    # Reset walk flag for new day
    $ take_a_walk_in_progress = False
    # Reset manager's daily interaction count
    $ manager_interactions_today = 0
    python:
        renpy.log("DEBUG: next_day - about to call process_next_day")
        result = process_next_day()
        renpy.log(f"DEBUG: next_day - process_next_day returned: {result}")
        if result == "game_over":
            renpy.log("DEBUG: next_day - jumping to game_over")
            renpy.jump("game_over")
        elif result == "governor_retaliation":
            renpy.log("DEBUG: next_day - governor retaliation event detected, jumping to governor_retaliation")
            # Run governor events in script context to keep normal click-per-line dialogue pacing.
            renpy.jump("handle_governor_retaliation_then_daily_report")
        elif result == "governor_tension_event":
            renpy.log("DEBUG: next_day - governor tension event detected, jumping to governor_tension_event")
            # Run governor events in script context to keep normal click-per-line dialogue pacing.
            renpy.jump("handle_governor_tension_then_daily_report")
        elif result == "handle_random_event":
            renpy.log("DEBUG: next_day - event detected, handling event first then continuing with daily report")
            renpy.jump("handle_event_then_daily_report")
        else:
            # No event, show daily report then go to tavern
            renpy.log("DEBUG: next_day - no event, showing daily report then going to tavern_screen")
            renpy.call_screen("daily_report")
            # "Start of day" as player experiences it: right after closing daily report.
            run_start_of_day_automation("next_day/no_event")
            renpy.jump("tavern_screen")

label handle_event_then_daily_report:
    $ renpy.log("DEBUG: handle_event_then_daily_report - STARTING")
    
    # Show black overlay first to prevent transparency during transition
    scene expression Solid('#000000')
    
    # Process the event with full visual presentation (exactly as before)
    call handle_random_event from _call_handle_random_event

    python:
        _bthr = getattr(store, "BANKRUPTCY_MONEY_THRESHOLD", -5000)
        if store.money <= _bthr:
            renpy.log(f"BANKRUPTCY after random event: money ${store.money} (threshold <= {_bthr}), game over.")
            renpy.jump("game_over")
    
    # After event is complete, continue with the rest of the day (daily report)
    python:
        renpy.log("DEBUG: Event completed, now continuing with daily report")
        # Continue processing the day from where it was interrupted
        # Show daily report
        renpy.call_screen("daily_report")
        # "Start of day" as player experiences it: right after closing daily report.
        run_start_of_day_automation("handle_event_then_daily_report")
    
    # After daily report, go to tavern
    jump tavern_screen

label handle_governor_retaliation_then_daily_report:
    $ renpy.log("DEBUG: handle_governor_retaliation_then_daily_report - STARTING")
    call governor_retaliation from _call_governor_retaliation_from_next_day
    python:
        _bthr = getattr(store, "BANKRUPTCY_MONEY_THRESHOLD", -5000)
        if store.money <= _bthr:
            renpy.log(f"BANKRUPTCY after governor retaliation flow: money ${store.money} (threshold <= {_bthr}), game over.")
            renpy.jump("game_over")
        renpy.call_screen("daily_report")
        run_start_of_day_automation("governor_retaliation flow")
    jump tavern_screen

label handle_governor_tension_then_daily_report:
    $ renpy.log("DEBUG: handle_governor_tension_then_daily_report - STARTING")
    call governor_tension_event from _call_governor_tension_from_next_day
    python:
        _bthr = getattr(store, "BANKRUPTCY_MONEY_THRESHOLD", -5000)
        if store.money <= _bthr:
            renpy.log(f"BANKRUPTCY after governor tension event: money ${store.money} (threshold <= {_bthr}), game over.")
            renpy.jump("game_over")
        renpy.call_screen("daily_report")
        run_start_of_day_automation("governor_tension flow")
    jump tavern_screen

################################################################################
### AGE VERIFICATION
################################################################################

label age_verification:
    $ renpy.log("Age verification screen started")
    scene black
    with fade
    
    centered "{size=+10}{color=#ffffff}ADULT CONTENT WARNING{/color}{/size}"
    
    centered "{color=#ffffff}This game contains adult content including sexual themes and mature situations.{/color}"
    
    centered "{color=#ffffff}All characters in this game are adults and are fictional.{/color}"
    
    centered "{color=#ffffff}By continuing, you confirm that you are 18 years of age or older and consent to viewing such content.{/color}"
    
    menu:
        "Are you 18 years of age or older?"
        
        "Yes, I am 18 or older":
            $ persistent.age_verified = True
            $ renpy.log("Age verification confirmed - setting persistent.age_verified = True")
            
            # Ask for NSFW preference immediately after age confirmation
            centered "{color=#ffffff}Before we begin: NSFW content (nudity/sexual themes) is optional.{/color}"
            menu:
                "Do you want to enable NSFW content and art? (You can change this later in Options > About)"
                "Enable NSFW content":
                    $ persistent.nsfw_enabled = True
                    $ renpy.log("NSFW preference chosen at age gate: True")
                "Disable NSFW content":
                    $ persistent.nsfw_enabled = False
                    $ renpy.log("NSFW preference chosen at age gate: False")
            centered "{color=#ffffff}Preference saved. You can change this later in Options > About.{/color}"
            with fade
            return
            
        "No, I am under 18":
            $ renpy.log("Age verification denied - exiting game")
            centered "{color=#ffffff}This game is not suitable for minors. Please exit the game.{/color}"
            $ renpy.quit()
    
    return

################################################################################
### TAKE A WALK SYSTEM
################################################################################

label take_a_walk:
    # Handle Take a Walk feature without nested contexts
    hide screen map_screen
    
    # Call the function to set up the walk
    $ success = start_take_a_walk()
    
    # If not successful, show message (if any) and return to map
    if not success:
        if getattr(store, "take_a_walk_fail_message", None):
            centered "[store.take_a_walk_fail_message]"
            $ store.take_a_walk_fail_message = None
        show screen map_screen
        return
    
    # Loop through stages until done
    $ current_stage = 0
    $ walk_continue = True
    
    while walk_continue:
        # Show the current stage and wait for user response
        call screen take_a_walk_result(stage=current_stage)
        
        # Check the result
        if _return == "next":
            # User clicked to continue, advance to next stage
            $ current_stage += 1
        else:
            # User clicked to finish or pressed return button
            $ walk_continue = False
    
    $ store.walk_interaction_media = None
    # Return to map after walk is complete
    show screen map_screen
    return
