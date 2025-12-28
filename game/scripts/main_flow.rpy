################################################################################
### IMPROVED BGM SYSTEM WITH EVENT MUSIC
################################################################################

init python:
    # Inicializar variables del sistema de música por capas
    if not hasattr(store, 'bgm_volume'):
        store.bgm_volume = 0.6  # Volumen normal de BGM (60%)
    if not hasattr(store, 'event_volume'):
        store.event_volume = 0.4  # Volumen de eventos (40%)
    if not hasattr(store, 'bgm_last_played_week'):
        store.bgm_last_played_week = -1
    if not hasattr(store, 'bgm_silence_start_time'):
        store.bgm_silence_start_time = 0.0
    if not hasattr(store, 'bgm_silence_duration'):
        store.bgm_silence_duration = 60.0  # 1 minuto de silencio

    def start_bgm_simple(filename="audio/BGM.ogg"):
        """
        Inicia la música de fondo principal en el canal 'music'.
        Se reproduce una sola vez, sin loop.
        """
        try:
            renpy.file(filename)
            renpy.music.play(filename, loop=False, if_changed=True, fadein=3.0, channel="music")
            renpy.music.set_volume(0.6, delay=1.0, channel="music")
            store.bgm_volume = 0.6
            renpy.log(f"BGM DEBUG: Started BGM single play at 60% volume - {filename}")
        except Exception:
            # Fallback to legacy theme
            renpy.music.play("audio/main_theme.ogg", loop=False, if_changed=True, fadein=3.0, channel="music")
            renpy.music.set_volume(0.6, delay=1.0, channel="music")
            store.bgm_volume = 0.6
            renpy.log("BGM DEBUG: Fallback to main_theme.ogg (single play at 60% volume)")

    def check_and_start_monday_bgm():
        """
        Verifica si es lunes (día 1 de la semana) y si es el primer o último lunes del mes.
        Si es lunes y cumple la condición, inicia la BGM.
        """
        try:
            # Calcular si es lunes (día 1 de la semana)
            is_monday = (store.current_day % 7 == 1) or (store.current_day == 1)
            
            if not is_monday:
                renpy.log(f"BGM DEBUG: Not Monday - Day {store.current_day}")
                return
            
            # Calcular qué lunes del mes es (1-4)
            week_of_month = ((store.current_day - 1) // 7) + 1
            
            # Verificar si ya se reprodujo este mes
            month_key = f"bgm_played_month_{store.current_year}_{store.current_month}"
            bgm_played_this_month = getattr(store, month_key, False)
            
            # Solo reproducir en el primer lunes (semana 1) o último lunes del mes
            is_first_monday = (week_of_month == 1)
            is_last_monday = (week_of_month >= 4)  # Última semana del mes
            
            if (is_first_monday or is_last_monday) and not bgm_played_this_month:
                start_bgm_simple("audio/BGM.ogg")
                setattr(store, month_key, True)
                renpy.log(f"BGM DEBUG: BGM started - First/Last Monday of month, Week {week_of_month}")
            else:
                renpy.log(f"BGM DEBUG: Not first/last Monday or already played this month - Day {store.current_day}, Week {week_of_month}, Played: {bgm_played_this_month}")
                
        except Exception as e:
            renpy.log(f"BGM MONDAY CHECK ERROR: {e}")

    def start_bgm_with_pauses(filename="audio/BGM.ogg", silence_seconds=120.0):
        """
        DEPRECATED: Usar start_bgm_simple() o check_and_start_monday_bgm() en su lugar.
        """
        start_bgm_simple(filename)

    def play_event_music(event_data=None):
        """
        Reproduce música específica para eventos en el canal 'sound'.
        Reduce el volumen de la BGM principal mientras suena el evento.
        """
        try:
            event_music = None
            
            # Si se proporcionan datos del evento, buscar el campo event_music
            if event_data and isinstance(event_data, dict):
                event_music = event_data.get('event_music')
                renpy.log(f"EVENT MUSIC: Found event_music field: {event_music}")
            
            # Si no hay música específica, usar fallback
            if not event_music:
                event_music = "audio/event.ogg"
                renpy.log("EVENT MUSIC: Using fallback event.ogg")
            
            # Reducir volumen de BGM principal
            renpy.music.set_volume(0.05, delay=1.0, channel="music")
            renpy.log("EVENT MUSIC: BGM volume reduced to 0.05 (5%)")
            
            # Intentar reproducir la música del evento en canal separado
            try:
                renpy.file(event_music)
                renpy.music.play(event_music, loop=False, if_changed=True, fadein=1.5, channel="sound")
                renpy.music.set_volume(0.4, delay=1.0, channel="sound")
                store.event_volume = 0.4
                renpy.log(f"EVENT MUSIC: Successfully playing {event_music} on sound channel at 40% volume")
            except:
                # Si falla, usar event.ogg como fallback final
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

    def end_event_music():
        """
        Termina la música del evento y restaura el volumen de la BGM principal.
        """
        try:
            # Fade-out de la música del evento en canal sound
            renpy.music.set_volume(0.0, delay=3.0, channel="sound")
            
            # Restaurar volumen de BGM principal
            renpy.music.set_volume(store.bgm_volume, delay=3.0, channel="music")
            renpy.log(f"EVENT MUSIC: BGM volume restored to {store.bgm_volume}")
                
        except Exception as e:
            renpy.log(f"EVENT MUSIC END ERROR: {e}")

    def get_remaining_bgm_silence_seconds(desired=60.0):
        """
        Devuelve el silencio restante hasta reanudar la BGM sin reiniciar el temporizador
        si otro evento ocurre dentro de la misma ventana de silencio.
        """
        try:
            import time
            now = time.time()
            resume_at = float(getattr(store, 'bgm_resume_at_epoch', 0.0) or 0.0)
            if resume_at > now:
                remaining = max(0.0, resume_at - now)
            else:
                remaining = float(desired)
            # No extender si ya hay un temporizador activo; conservar la misma fecha objetivo.
            if resume_at <= now:
                store.bgm_resume_at_epoch = now + remaining
            return remaining
        except Exception as e:
            renpy.log(f"BGM SILENCE CALC ERROR: {e}")
            return float(desired)

    def start_bgm_with_initial_silence(filename="audio/BGM.ogg", initial_silence=30.0, loop_silence=30.0):
        """
        Inicia la BGM empezando con un bloque de silencio inicial y luego lazo con pausas.
        """
        try:
            renpy.file(filename)
            renpy.music.play(f"<silence {initial_silence}>", loop=False, channel="music")
            renpy.music.queue(filename, loop=False, fadein=3.0, channel="music")
            renpy.music.queue(f"<silence {loop_silence}>", channel="music")
            renpy.music.queue(filename, loop=True, fadein=3.0, channel="music")
        except Exception:
            renpy.music.play("audio/main_theme.ogg", loop=True, if_changed=True, fadein=3.0, channel="music")
        renpy.music.set_volume(0.6, delay=1.0, channel="music")
        renpy.log(f"BGM DEBUG: BGM with initial silence {initial_silence}s and loop silence {loop_silence}s")

    def _resume_bgm_after_fade(remaining_silence=60.0, loop_silence=60.0, filename="audio/BGM.ogg"):
        """
        Helper ejecutado tras el fade-out para arrancar la BGM con silencio inicial
        sin cortar el desvanecimiento.
        """
        try:
            start_bgm_with_initial_silence(filename, initial_silence=remaining_silence, loop_silence=loop_silence)
        except Exception as e:
            renpy.log(f"BGM RESUME ERROR: {e}")

    def restore_main_bgm_with_fadeout():
        """
        Restaura la música de fondo principal después de un evento con fade-out de 10 segundos.
        """
        try:
            # Hacer fade-out de la música actual durante 10 segundos
            renpy.music.set_volume(0.0, delay=10.0, channel="music")
            
            # Después del fade-out, restaurar la BGM principal
            renpy.music.queue("<silence 10.0>")  # Esperar 10 segundos para el fade-out
            renpy.music.queue("audio/BGM.ogg", loop=False, fadein=2.0)
            renpy.music.queue("<silence 120.0>")  # 2 minutes of silence
            renpy.music.queue("audio/BGM.ogg", loop=True, fadein=3.0)  # Loop with fade-in
            
            # Restaurar volumen gradualmente
            renpy.music.set_volume(0.6, delay=12.0, channel="music")
            
            renpy.log("BGM DEBUG: Started fade-out and BGM restoration sequence")
        except Exception as e:
            renpy.log(f"BGM RESTORE ERROR: {e}")

    def restore_main_bgm():
        """
        Versión rápida sin fade-out para compatibilidad
        """
        restore_main_bgm_with_fadeout()

    def start_event_with_music(event_data):
        """
        Inicia un evento con la música apropiada basándose en los datos del evento.
        """
        play_event_music(event_data)
        event_id = event_data.get('id', 'unknown') if event_data else 'unknown'
        renpy.log(f"EVENT START: {event_id} with music from JSON data")

    def end_event_with_music():
        """
        Termina un evento y hace fade-out de la música del evento.
        La música principal no se reanuda automáticamente.
        """
        end_event_music()
        renpy.log("EVENT END: Event music faded out")
    
    def end_event_with_quick_fadeout():
        """
        Termina un evento con fade-out rápido de la música del evento.
        Restaura el volumen de la BGM principal.
        """
        try:
            # Fade-out rápido de la música del evento en canal sound
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
            # Fade-out inmediato de la música del evento en canal sound
            renpy.music.set_volume(0.0, delay=1.0, channel="sound")
            
            # Restaurar volumen de BGM principal
            renpy.music.set_volume(store.bgm_volume, delay=1.0, channel="music")
            renpy.log(f"BGM DEBUG: BGM volume restored to {store.bgm_volume} after immediate fadeout")
                
        except Exception as e:
            renpy.log(f"BGM IMMEDIATE FADEOUT ERROR: {e}")
    
    def stop_event_music_now():
        """
        Para la música de evento inmediatamente sin fade-out.
        Restaura el volumen de la BGM principal.
        """
        try:
            renpy.music.stop(channel="sound")
            
            # Restaurar volumen de BGM principal
            renpy.music.set_volume(store.bgm_volume, channel="music")
            renpy.log(f"BGM DEBUG: BGM volume restored to {store.bgm_volume} after immediate stop")
                
        except Exception as e:
            renpy.log(f"BGM STOP ERROR: {e}")
    
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

    def show_day_transition():
        # Black screen with date, then back to tavern
        try:
            # Capture current date strings
            day_names_local = renpy.store.day_names
            month_names_local = renpy.store.month_names
            day_name = day_names_local[(renpy.store.current_day - 1) % 7]
            month_name = month_names_local[renpy.store.current_month]
            date_text = f"{day_name}, {renpy.store.current_day} {month_name} {renpy.store.current_year}"

            # Fade to black
            renpy.scene()
            renpy.with_statement(Fade(0.75, 0.0, 0.75))

            # Show black screen and centered date text
            renpy.scene()
            renpy.show("expression Solid('#000000FF')")
            renpy.show("expression Text(date_text, size=42, color='#ffffff')", at_list=[Position(xalign=0.5, yalign=0.5)])
            renpy.pause(2.0)

            # Fade out text and return to tavern
            renpy.scene()
            renpy.with_statement(Fade(0.75, 0.0, 0.75))
            renpy.call_in_new_context("_return_to_tavern")
        except Exception as e:
            renpy.log("DAY TRANSITION ERROR: " + str(e))

label _return_to_tavern:
    $ renpy.hide_screen("daily_report")
    jump tavern_screen

label day_transition:
    scene black with Fade(0.25, 0.0, 0.25)
    $ day_name = day_names[(store.current_day - 1) % 7]
    $ month_name = month_names[store.current_month]
    $ date_text = f"{day_name}, {store.current_day} {month_name} {store.current_year}"
    show expression Text(date_text, size=42, color="#ffffff") as daytext at truecenter
    # Auto-advance after a short time, but still skippable by click
    pause 1.0
    hide daytext
    scene black with Fade(0.25, 0.0, 0.25)
    jump tavern_screen

################################################################################
### MAIN GAME FLOW
################################################################################

label start:
    $ renpy.log("Game started at label start")
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
    
    # Fallback: if we reached start due to a load, apply snapshot and jump to tavern
    if getattr(persistent, 'loaded_via_save', False):
        $ renpy.log("Start reached during load - applying snapshot fallback INLINE and jumping to tavern")
        python:
            try:
                slot = getattr(persistent, "_slot_to_apply", None)
                snap = None
                d = getattr(persistent, "_slot_snapshots", {}) or {}
                if slot is not None:
                    if slot in d:
                        snap = d.get(slot)
                    elif isinstance(slot, int) and str(slot) in d:
                        snap = d.get(str(slot))
                    elif isinstance(slot, str) and slot.isdigit() and int(slot) in d:
                        snap = d.get(int(slot))
                if snap is None:
                    snap = getattr(persistent, "_last_snapshot", None)
                if snap:
                    _apply_snapshot(snap)
                    renpy.log("START SNAPSHOT: applied inline")
                else:
                    renpy.log("START SNAPSHOT: no snapshot found inline")
                store.is_new_game = False
                # Flags will be cleared in tavern screen
            except Exception as e:
                renpy.log("START SNAPSHOT FALLBACK error: " + str(e))
        # Show the ESC key handler screen for loaded snapshots too
        show screen esc_key_handler
        jump tavern_screen
    # If the engine jumped to start during a load, avoid re-initializing
    if not is_new_game:
        $ renpy.log("Start reached during load - skipping initialization and going to tavern_screen")
        # Show the ESC key handler screen for loaded games too
        show screen esc_key_handler
        jump tavern_screen

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
    
    menu:
        "Choose your title"
        "Lord":
            $ player_title = "Lord"
        "Lady":
            $ player_title = "Lady"

    python:
        player_name = renpy.input("Enter your name:", length=32)
        player_name = player_name.strip()
        if not player_name:
            player_name = "Manager"

    "Very well, [player_title] [player_name]. Let's take back our emporium."

    # Transition to black and show initial date (like day_transition)
    scene black with Fade(0.25, 0.0, 0.25)
    $ day_name = day_names[(store.current_day - 1) % 7]
    $ month_name = month_names[store.current_month]
    $ date_text = f"{day_name}, {store.current_day} {month_name} {store.current_year}"
    show expression Text(date_text, size=42, color="#ffffff") as daytext at truecenter
    # Auto-advance after a short time, but still skippable by click
    pause 1.0
    hide daytext
    scene black with Fade(0.25, 0.0, 0.25)

    # Initialize the calendar with forced reset for new game
    $ initialize_calendar(force_reset=True) if getattr(store, 'is_new_game', True) else initialize_calendar(False)

    # Reset persistent.unlocked_shops for a new game and link to store
    $ persistent.unlocked_shops = {"shop1": True, "shop2": False, "shop3": False}
    $ store.unlocked_shops = persistent.unlocked_shops
    $ renpy.log("Initialized persistent.unlocked_shops: " + str(persistent.unlocked_shops))
    $ renpy.log("Linked store.unlocked_shops: " + str(store.unlocked_shops))

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

    # Music already started in main menu via start_bgm_with_pauses.
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
    
    "Mine eyes survey the three workers who have sworn themselves to my cause. 'Tis but a modest beginning, yet from such humble seeds do mighty empires grow."
    "Verily, now must I put these loyal souls to their destined labors. Let me consult my journal to discern the path ahead."
    $ renpy.log("DEBUG: show_objective_1_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_2_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_2_dialogue - STARTING DIALOGUE")
    "'Tis the business I shall focus upon, for the present hour..."
    "The governor began with naught but ambition burning in his breast - I walk the same treacherous path he once trod."
    "My journal hath been inscribed with the next duty."
    $ renpy.log("DEBUG: show_objective_2_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_3_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_3_dialogue - STARTING DIALOGUE")
    "Each worker doth bring their own gifts and talents to this enterprise."
    "Choose the right soul for the right profession, and we shall be well upon our way to prosperity."
    "Should I require more detail on how they have performed, I may open the Daily Report and examine the results."
    "My journal hath been inscribed with the next duty."
    $ renpy.log("DEBUG: show_objective_3_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_4_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_4_dialogue - STARTING DIALOGUE")
    $ store.objective_4_dialogue_shown = True
    "Five thousand coins in my coffers. Not a fortune, but enough to start thinking about expansion."
    $ renpy.log("DEBUG: show_objective_4_dialogue - First line shown")
    "I need to start thinking about infrastructure, improving the building to hold more workers, or the gear to be better prepared. Maybe a bit of both?"
    $ renpy.log("DEBUG: show_objective_4_dialogue - Second line shown")
    "Journal has been updated with the next objective."
    $ renpy.log("DEBUG: show_objective_4_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_5_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_5_dialogue - STARTING DIALOGUE")
    "Good! Now I understand how to manage my workers' needs and use items effectively."
    "This knowledge will be crucial as my operation grows and I need to keep my workers happy and productive."
    "Journal has been updated with the next objective."
    $ store.current_objective = 6
    call show_objective_6_intro from _call_show_objective_6_intro
    $ renpy.log("DEBUG: show_objective_5_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_6_intro:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_6_intro - STARTING DIALOGUE")
    "Time to strengthen my foundation."
    "I'll upgrade a building level and raise its supplies bonus. The upgrade costs 1,000 coins."
    $ renpy.log("DEBUG: show_objective_6_intro - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_6_outro:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_6_outro - STARTING DIALOGUE")
    "Excellent. The building can accommodate more souls now."
    "'Tis time to expand the scale of this entire operation."
    $ renpy.log("DEBUG: show_objective_6_outro - FINISHED DIALOGUE")
    call show_objective_7_intro from _call_show_objective_7_intro
    jump tavern_screen

label show_objective_7_intro:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_7_intro - STARTING DIALOGUE")
    "Time to meet the people who make this place run."
    "I'll have a Friendly Chat with one of my workers to get a feel for their mood and motivations."
    "Journal has been updated with the next objective."
    $ renpy.log("DEBUG: show_objective_7_intro - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_7_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_7_dialogue - STARTING DIALOGUE")
    "Excellent. Taking the time to commune with my workers doth yield its rewards."
    "Now, 'tis time to establish the emporium — expand to multiple buildings and swell our coffers with gold."
    $ renpy.log("DEBUG: show_objective_7_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

label show_objective_8_dialogue:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_objective_8_dialogue - STARTING DIALOGUE")
    "I possess what I require for now, yet this is merely the dawn of my ascension. I must expand my operations, recruit more workers, erect more buildings."
    "Two buildings, ten workers, and ten thousand coins. That is the threshold where the city begins to take notice of my growing power."
    "My journal hath been inscribed with the next duty. From this moment forth, mark 'Complete' within it to advance."
    $ renpy.log("DEBUG: show_objective_8_dialogue - FINISHED DIALOGUE")
    jump tavern_screen

# ===== EPIC ENDINGS =====
label show_ending_assassination:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_ending_assassination - STARTING EPIC ENDING")
    
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
    
    "We move like shadows through the night, my team of warriors and mages executing the plan with lethal precision. The governor's guards fall silently, their throats cut or their minds shattered by arcane forces before they can raise the alarm."
    
    "The governor himself sits in his study, surrounded by the spoils of his tyranny - paintings seized from my family's estate, ledgers filled with debts called in under false pretenses, trophies from the lives he destroyed."
    
    "He looks up as we enter, his face a mask of surprise that quickly turns to terror. 'You... you cannot be here. The guards...'"
    
    "'The guards are dead,' I reply, my voice cold as the grave. 'And so shall you be, before this night ends.'"
    
    "My team moves with practiced efficiency. [team_names[0] if len(team_names) > 0 else 'The warrior']'s blade finds its mark even as [team_names[1] if len(team_names) > 1 else 'the mage']'s spells bind the governor in chains of pure force. [team_names[2] if len(team_names) > 2 else 'The assassin'] delivers the final blow - quick, clean, merciless."
    
    "The governor's body slumps to the floor, his blood mingling with the wine from the shattered goblet he had been holding. Justice, at long last, served not by the law he corrupted, but by the steel and sorcery of those he wronged."
    
    "As dawn breaks over the city, word spreads like wildfire. The governor is dead. The balance of power hath shifted irrevocably."
    
    "My empire stands unchallenged now. The [building_count] buildings that bear my banner, the [worker_count] souls who serve my will, the vast fortune I have amassed - all of it secured through this single act of vengeance."
    
    "The city's elite scramble to curry favor with the new power in their midst. They come bearing gifts, seeking alliances, offering tribute. I accept their offerings, but I do not forget."
    
    "I do not forget how they stood by while my family was destroyed. I do not forget how they profited from our ruin. But for now, I am content."
    
    "The governor's head adorns a spike above my main establishment. A warning to all who would cross me. A declaration that the old order is dead, and a new empire hath risen in its place."
    
    "My revenge is complete. But my ambition? That is only beginning."
    
    "The sun rises on a new day, and I am its master."
    
    $ renpy.log("DEBUG: show_ending_assassination - EPIC ENDING COMPLETE")
    $ tutorial_active = False
    return

label show_ending_blackmail:
    scene expression workers_bg
    $ renpy.log("DEBUG: show_ending_blackmail - STARTING EPIC ENDING")
    
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
    
    "Three of my most cunning souls stand ready: [team_names[0] if len(team_names) > 0 else 'a master of charm'], [team_names[1] if len(team_names) > 1 else 'a skilled seducer'], and [team_names[2] if len(team_names) > 2 else 'a clever strategist']. Their weapons are not swords or spells, but secrets and seduction."
    
    "From the [building_count] strongholds I have built, from the [worker_count] souls who have sworn fealty to my cause, from the [money] coins that have filled my coffers - all of it hath led to this single, decisive moment."
    
    "The governor's mansion looms before us, but we do not come to kill. We come to steal what he values most: his secrets, his reputation, his power."
    
    "Under cover of darkness, my team executes a plan of exquisite complexity. [team_names[0] if len(team_names) > 0 else 'The charmer'] gains entry to the governor's private study, seducing a guard with honeyed words and false promises. [team_names[1] if len(team_names) > 1 else 'The seducer'] distracts the governor himself in his chambers, while [team_names[2] if len(team_names) > 2 else 'the clever one'] cracks the safe containing documents of incalculable value."
    
    "Ledgers detailing embezzlement. Letters proving bribery of city officials. Contracts showing illegal dealings with criminal syndicates. Evidence that would destroy the governor's reputation and send him to the gallows."
    
    "We emerge from the mansion like shadows, carrying with us the governor's entire empire of lies, written in his own hand and sealed with his own seal."
    
    "The next morning, I send a messenger to the governor's mansion. The message is simple: 'I have in my possession documents that would see you hanged. Your choice is simple - surrender your holdings to me, publicly declare me your successor, and leave this city forever. Or face the consequences.'"
    
    "The governor's response comes that evening. He is a broken man, his power stripped away not by force of arms, but by the weight of his own sins brought to light."
    
    "He signs the documents transferring his properties to my name. He makes the public declaration, his voice trembling with fear and shame. And then he flees, a shadow of the tyrant he once was."
    
    "As the sun sets on his departure, word spreads throughout the city. The governor hath been brought low. The balance of power hath shifted irrevocably."
    
    "My empire stands unchallenged now. The [building_count] buildings that bear my banner, the [worker_count] souls who serve my will, the vast fortune I have amassed - all of it secured through cunning and blackmail, the tools of a true master of the shadows."
    
    "The city's elite scramble to curry favor with the new power in their midst. They come bearing gifts, seeking alliances, offering tribute. I accept their offerings, but I do not forget."
    
    "I do not forget how they stood by while my family was destroyed. I do not forget how they profited from our ruin. But for now, I am content."
    
    "The governor's portrait hangs in my main establishment, but with a black ribbon across it. A warning to all who would cross me. A declaration that the old order is dead, and a new empire hath risen in its place."
    
    "My revenge is complete. But my ambition? That is only beginning."
    
    "The sun rises on a new day, and I am its master."
    
    $ renpy.log("DEBUG: show_ending_blackmail - EPIC ENDING COMPLETE")
    $ tutorial_active = False
    return

label tavern_screen():
    $ renpy.log("DEBUG: tavern_screen label - STARTING")
    
    $ current_obj = getattr(store, 'current_objective', None)
    $ tutorial_act = getattr(store, 'tutorial_active', False)
    $ obj4_shown = getattr(store, 'objective_4_dialogue_shown', False)
    $ renpy.log(f"DEBUG: tavern_screen - current_objective={current_obj}, tutorial_active={tutorial_act}, money=${money}, obj4_dialogue_shown={obj4_shown}")
    # Removed pending_exit auto-quit; rely on standard confirmation and quit flow
    
    # Call the tavern screen
    call screen tavern
    return

label next_day:
    $ renpy.log("DEBUG: next_day label - STARTING")
    python:
        renpy.log("DEBUG: next_day - about to call process_next_day")
        result = process_next_day()
        renpy.log(f"DEBUG: next_day - process_next_day returned: {result}")
        if result == "game_over":
            renpy.log("DEBUG: next_day - jumping to game_over")
            renpy.jump("game_over")
        elif result == "handle_random_event":
            renpy.log("DEBUG: next_day - event detected, handling event first then continuing with daily report")
            renpy.jump("handle_event_then_daily_report")
        else:
            # Check tutorial progress before returning to tavern
            renpy.log("DEBUG: next_day - jumping to tavern_screen")
            renpy.jump("tavern_screen")  # Default to tavern for any other return value

label handle_event_then_daily_report:
    $ renpy.log("DEBUG: handle_event_then_daily_report - STARTING")
    
    # Process the event with full visual presentation (exactly as before)
    call handle_random_event from _call_handle_random_event
    
    # After event is complete, continue with the rest of the day (daily report)
    python:
        renpy.log("DEBUG: Event completed, now continuing with daily report")
        # Continue processing the day from where it was interrupted
        # Show daily report
        renpy.call_screen("daily_report")
    
    # After daily report, go to tavern
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