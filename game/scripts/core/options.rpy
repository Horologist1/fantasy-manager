## This file contains options that can be changed to customize your game.
##
## Lines beginning with two '#' marks are comments, and you shouldn't uncomment
## them. Lines beginning with a single '#' mark are commented-out code, and you
## may want to uncomment them when appropriate.


## Basics ######################################################################

define config.rollback_enabled = False

## A human-readable name of the game. This is used to set the default window
## title, and shows up in the interface and error reports.
##
## The _() surrounding the string marks it as eligible for translation.

define config.name = _("Fantasy Manager")


## Determines if the title given above is shown on the main menu screen. Set
## this to False to hide the title.

define gui.show_name = True



define config.version = "0.9.6.1"
define build.version = "0.9.6.1"


## Text that is placed on the game's about screen. Place the text between the
## triple-quotes, and leave a blank line between paragraphs.

define gui.about = _p("""
""")


## A short name for the game used for executables and directories in the built
## distribution. This must be ASCII-only, and must not contain spaces, colons,
## or semicolons.

define build.name = "Fantasy_Manager"


## Sounds and music ############################################################

## These three variables control, among other things, which mixers are shown
## to the player by default. Setting one of these to False will hide the
## appropriate mixer.

define config.has_sound = True
define config.has_music = True
define config.has_voice = True


## To allow the user to play a test sound on the sound or voice channel,
## uncomment a line below and use it to set a sample sound to play.

# define config.sample_sound = "sample-sound.ogg"
# define config.sample_voice = "sample-voice.ogg"


## Uncomment the following line to set an audio file that will be played while
## the player is at the main menu. This file will continue playing into the
## game, until it is stopped or another file is played.

# define config.main_menu_music = "main-menu-theme.ogg"


## Transitions #################################################################
##
## These variables set transitions that are used when certain events occur.
## Each variable should be set to a transition, or None to indicate that no
## transition should be used.

## Entering or exiting the game menu.

define config.enter_transition = dissolve
define config.exit_transition = dissolve


## Between screens of the game menu.

define config.intra_transition = dissolve


## A transition that is used after a game has been loaded.

define config.after_load_transition = None


## Used when entering the main menu after the game has ended.

define config.end_game_transition = None


## A variable to set the transition used when the game starts does not exist.
## Instead, use a with statement after showing the initial scene.


## Window management ###########################################################
##
## This controls when the dialogue window is displayed. If "show", it is always
## displayed. If "hide", it is only displayed when dialogue is present. If
## "auto", the window is hidden before scene statements and shown again once
## dialogue is displayed.
##
## After the game has started, this can be changed with the "window show",
## "window hide", and "window auto" statements.

define config.window = "auto"


## Transitions used to show and hide the dialogue window

define config.window_show_transition = Dissolve(.2)
define config.window_hide_transition = Dissolve(.2)

## Preference defaults #########################################################

## Controls the default text speed. The default, 0, is infinite, while any other
## number is the number of characters per second to type out.

default preferences.text_cps = 0

## Default save/load page starts at 1
init -1 python:
    if getattr(persistent, '_file_page_reset_v2', None) is None:
        persistent._file_page = 1
        persistent._file_page_reset_v2 = True
    if getattr(persistent, 'difficulty', None) is None:
        persistent.difficulty = 'normal'


## The default auto-forward delay. Larger numbers lead to longer waits, with 0
## to 30 being the valid range.

default preferences.afm_time = 15


## Save directory ##############################################################
##
## Controls the platform-specific place Ren'Py will place the save files for
## this game. The save files will be placed in:
##
## Windows: %APPDATA\RenPy\<config.save_directory>
##
## Macintosh: $HOME/Library/RenPy/<config.save_directory>
##
## Linux: $HOME/.renpy/<config.save_directory>
##
## This generally should not be changed, and if it is, should always be a
## literal string, not an expression.

define config.save_directory = "FantasyManager"


## Icon ########################################################################
##
## The icon displayed on the taskbar or dock.

define config.window_icon = "gui/window_icon.png"

## Build icon - used for the executable file icon in distributions
## IMPORTANT: For Windows, you need a .ico file (not .png)
## The icon file should be in the project root directory (not in game/)

define build.windows_icon = "icon.ico"
define build.icon = "icon.ico"


## Build configuration #########################################################
##
## This section controls how Ren'Py turns your project into distribution files.

init python:

    ## The following functions take file patterns. File patterns are case-
    ## insensitive, and matched against the path relative to the base directory,
    ## with and without a leading /. If multiple patterns match, the first is
    ## used.
    ##
    ## In a pattern:
    ##
    ## / is the directory separator.
    ##
    ## * matches all characters, except the directory separator.
    ##
    ## ** matches all characters, including the directory separator.
    ##
    ## For example, "*.txt" matches txt files in the base directory, "game/
    ## **.ogg" matches ogg files in the game directory or any of its
    ## subdirectories, and "**.psd" matches psd files anywhere in the project.

    ## Classify files as None to exclude them from the built distributions.

    build.classify('**~', None)
    build.classify('**.bak', None)
    build.classify('**/.**', None)
    build.classify('**/#**', None)
    build.classify('**/thumbs.db', None)

    ## Internal development/release documents are not player-facing content.
    build.classify('AUDIT_SUMMARY.md', None)
    build.classify('RELEASE_NOTES.md', None)

    ## Never distribute Python bytecode. Installed copies compile from the
    ## matching .py source, avoiding stale cache/source pairs after updates.
    build.classify('**/__pycache__/', None)
    build.classify('**/__pycache__/**', None)
    build.classify('**.pyc', None)
    
    ## Exclude the docs folder completely
    build.classify('docs/**', None)
    
    ## Exclude ALL devkit files and folders completely (including all .exe files and the folder itself)
    ## This ensures the entire devkit folder is excluded from builds
    build.classify('devkit/**', None)
    build.classify('devkit/', None)
    ## Exclude the browser devkit (devkit_web), including node_modules and the built bundle.
    build.classify('devkit_web/**', None)
    build.classify('devkit_web/', None)
    ## Exclude developer maintenance scripts + their compiled bytecode (offline JSON tooling,
    ## never used at runtime; .py patchers + .pyc blobs can trip download-scanner heuristics).
    build.classify('tools/**', None)
    build.classify('tools/', None)

    ## Test sources are development-only and must not enter release packages.
    build.classify('tests/**', None)
    build.classify('tests/', None)

    ## Exclude local AI/tooling metadata and debug artifacts from releases.
    build.classify('AGENTS.md', None)
    build.classify('**/AGENTS.md', None)
    build.classify('.claude/**', None)
    build.classify('.cursor/**', None)
    build.classify('claude-*.log', None)
    build.classify('cursor-*.log', None)
    build.classify('*-debug.log', None)
    build.classify('*_debug.log', None)

    ## Exclude local runtime/cache artifacts from releases.
    build.classify('game/saves/**', None)
    build.classify('game/cache/**', None)
    build.classify('errors.txt', None)
    build.classify('log.txt', None)
    build.classify('traceback.txt', None)
    build.classify('**.tab', None)
    build.classify('_fix.py', None)
    build.classify('temp_original.rpy', None)

    ## Exclude art working files (Krita/Photoshop/etc.). These are editing
    ## sources for the exported PNG/JPG assets and must never ship - a single
    ## .kra can dwarf the flattened image it produces.
    build.classify('**.kra', None)
    build.classify('**.psd', None)
    build.classify('**.xcf', None)
    build.classify('**.clip', None)
    build.classify('**.ora', None)

    ## Exclude the devkit JSON-schema reference (modding documentation; the
    ## devkit itself is already excluded above, so its companion doc follows).
    build.classify('game/data/json_schema_standard.md', None)

    ## Exclude Android signing/config files from PC distributions.
    build.classify('android.json', None)
    build.classify('**.keystore', None)
    build.classify('**.jks', None)
    build.classify('**/keystore.properties', None)
    build.classify('**/local.properties', None)

    ## To archive files, classify them as 'archive'.

    # build.classify('game/**.png', 'archive')
    # build.classify('game/**.jpg', 'archive')

    ## Files matching documentation patterns are duplicated in a mac app build,
    ## so they appear in both the app and the zip file.

    build.documentation('*.html')
    build.documentation('*.txt')
    build.documentation('user_docs/**.md')
    build.documentation('user_docs/**.txt')
    build.documentation('user_docs/**.json')


## A Google Play license key is required to perform in-app purchases. It can be
## found in the Google Play developer console, under "Monetize" > "Monetization
## Setup" > "Licensing".

# define build.google_play_key = "..."


## The username and project name associated with an itch.io project, separated
## by a slash.

# define build.itch_project = "renpytom/test-project"

    # Define a persistent variable to store the NSFW preference
    if persistent.nsfw_enabled is None:
        persistent.nsfw_enabled = True  # Default to True (NSFW content shown)

    # Worker gender filter: "both", "male", "female". Existing hidden workers remain employed.
    if not hasattr(persistent, "worker_gender_filter") or persistent.worker_gender_filter not in ("both", "male", "female"):
        persistent.worker_gender_filter = "both"
    if not hasattr(persistent, "worker_gender_filter_warning_ack"):
        persistent.worker_gender_filter_warning_ack = None

    def set_worker_gender_filter(mode, acknowledge=False):
        """Set the filter and whether its hidden-worker warning is acknowledged."""
        if mode not in ("both", "male", "female"):
            mode = "both"
        persistent.worker_gender_filter = mode
        persistent.worker_gender_filter_warning_ack = mode if acknowledge else None

    # Worker orientation traits (NSFW), one cycle per trait:
    # "off" = only_assigned behavior (designed/modded workers only),
    # "enable" = joins the random trait pool for generated workers,
    # "force" = every worker of the matching gender gets it, unique story workers included.
    if not hasattr(persistent, "orientation_gay_mode") or persistent.orientation_gay_mode not in ("off", "enable", "force"):
        persistent.orientation_gay_mode = "off"
    if not hasattr(persistent, "orientation_lesbian_mode") or persistent.orientation_lesbian_mode not in ("off", "enable", "force"):
        persistent.orientation_lesbian_mode = "off"
    # One-time image warning when first switching an orientation trait to Force
    if not hasattr(persistent, "orientation_force_warning_seen"):
        persistent.orientation_force_warning_seen = False

    # Global defaults for worker automation (used by More Options > Defaults).
    if not hasattr(persistent, "default_auto_supply_potions"):
        persistent.default_auto_supply_potions = False
    else:
        persistent.default_auto_supply_potions = bool(persistent.default_auto_supply_potions)

    if not hasattr(persistent, "default_auto_supply_potion_count"):
        persistent.default_auto_supply_potion_count = 3
    else:
        try:
            _auto_supply_count = int(persistent.default_auto_supply_potion_count)
        except Exception:
            _auto_supply_count = 3
        persistent.default_auto_supply_potion_count = max(1, min(5, _auto_supply_count))

    if not hasattr(persistent, "default_auto_equip"):
        persistent.default_auto_equip = False
    else:
        persistent.default_auto_equip = bool(persistent.default_auto_equip)

    if not hasattr(persistent, "default_auto_rest"):
        persistent.default_auto_rest = False
    else:
        persistent.default_auto_rest = bool(persistent.default_auto_rest)

    if not hasattr(persistent, "default_auto_rest_entry_pct"):
        persistent.default_auto_rest_entry_pct = 35
    else:
        try:
            _auto_rest_pct = int(persistent.default_auto_rest_entry_pct)
        except Exception:
            _auto_rest_pct = 35
        _allowed_rest_pcts = (15, 25, 35, 45)
        if _auto_rest_pct not in _allowed_rest_pcts:
            _auto_rest_pct = min(_allowed_rest_pcts, key=lambda x: abs(x - _auto_rest_pct))
        persistent.default_auto_rest_entry_pct = _auto_rest_pct

    # Optionally, customize the preferences screen to include this option
    def set_nsfw_content_enabled(enabled):
        """Apply the runtime content policy without rewriting canonical game state."""
        enabled = bool(enabled)
        persistent.nsfw_enabled = enabled
        # Recorded into the save file so loading can restore the mode later.
        store.save_nsfw_mode = enabled

        # These are derived catalogs/caches only. Workers, reports, inventories,
        # events and assignments are deliberately left untouched.
        trait_refresh = globals().get("refresh_traits_cache")
        if callable(trait_refresh):
            trait_refresh(force=True)
        interaction_refresh = globals().get("invalidate_interactions_cache")
        if callable(interaction_refresh):
            interaction_refresh()
        if hasattr(store, "_worker_portrait_cache"):
            store._worker_portrait_cache = {}

        # Close overlays whose screen-local variables may retain already-resolved
        # text or media from the previous policy. Their backing data is preserved.
        for screen_name in (
            "manager_inventory", "worker_details", "report_details",
            "worker_history_popup", "interaction_dialogue",
        ):
            try:
                renpy.hide_screen(screen_name)
            except Exception:
                pass

        # Restore a previously suspended transient only when its active slot is free.
        # The dictionaries contain data only, so they remain save/rollback safe.
        if enabled:
            suspended_event = getattr(store, "_content_filter_suspended_event_context", None)
            if suspended_event and not getattr(store, "current_event", None):
                store.current_event = suspended_event.get("event")
                store.current_worker = suspended_event.get("worker")
                store.current_affected_building = suspended_event.get("affected_building")
                store.temp_eligible_workers_for_event = list(suspended_event.get("eligible_workers") or [])
                store.building_notification = suspended_event.get("building_notification")
                store.chosen_choice_data = suspended_event.get("chosen_choice_data")
                store._content_filter_suspended_event_context = None
                renpy.log("CONTENT_FILTER: restored suspended random event")
                renpy.jump("handle_random_event")
                return

            suspended_recruitment = getattr(store, "_content_filter_suspended_recruitment_context", None)
            if suspended_recruitment and not getattr(store, "current_recruitment_event", None):
                store.current_recruitment_event = suspended_recruitment.get("event")
                store.current_recruitment_worker = suspended_recruitment.get("worker")
                store.in_recruitment = True
                store._content_filter_suspended_recruitment_context = None
                renpy.log("CONTENT_FILTER: restored suspended recruitment")
                renpy.jump("resume_content_filtered_recruitment")
                return

        abort_transient = False
        if not enabled:
            event_visible = globals().get("event_is_visible_for_content_filter")
            content_restricted = globals().get("content_object_is_restricted")
            current_event = getattr(store, "current_event", None)
            if current_event and hasattr(current_event, "get"):
                abort_transient = bool(callable(event_visible) and not event_visible(current_event))
                current_worker = getattr(store, "current_worker", None)
                if not abort_transient and current_worker and callable(content_restricted):
                    abort_transient = bool(content_restricted(current_worker))
                if abort_transient:
                    store._content_filter_suspended_event_context = {
                        "event": current_event,
                        "worker": current_worker,
                        "affected_building": getattr(store, "current_affected_building", None),
                        "eligible_workers": list(getattr(store, "temp_eligible_workers_for_event", []) or []),
                        "building_notification": getattr(store, "building_notification", None),
                        "chosen_choice_data": getattr(store, "chosen_choice_data", None),
                    }
                    store.current_event = None

            recruitment_event = getattr(store, "current_recruitment_event", None)
            if recruitment_event and hasattr(recruitment_event, "get"):
                recruitment_blocked = bool(callable(event_visible) and not event_visible(recruitment_event))
                recruitment_worker = getattr(store, "current_recruitment_worker", None)
                if not recruitment_blocked and recruitment_worker and callable(content_restricted):
                    recruitment_blocked = bool(content_restricted(recruitment_worker))
                if recruitment_blocked:
                    store._content_filter_suspended_recruitment_context = {
                        "event": recruitment_event,
                        "worker": recruitment_worker,
                    }
                    store.current_recruitment_event = None
                    if hasattr(store, "current_recruitment_worker"):
                        store.current_recruitment_worker = None
                    if hasattr(store, "in_recruitment"):
                        store.in_recruitment = False
                    abort_transient = True

        if abort_transient:
            clear_context = getattr(store, "clear_random_event_context", None)
            if callable(clear_context):
                clear_context("content_filter_toggled")
            renpy.log("CONTENT_FILTER: aborted restricted transient context after disabling NSFW")
            renpy.jump("tavern_screen")

        renpy.restart_interaction()

    def add_nsfw_preference():
        return [
            ("Show NSFW Content", "nsfw_enabled", True, False, "Toggle NSFW content visibility.")
        ]

    def _save_has_restricted_building(buildings, building_types):
        for building in (buildings or {}).values():
            if not hasattr(building, "get"):
                continue
            btype_id = building.get("type")
            if not btype_id:
                continue
            btype = next((entry for entry in (building_types or []) if hasattr(entry, "get") and entry.get("id") == btype_id), None)
            if btype and content_object_is_restricted(btype):
                return True
        return False

    def _save_expects_nsfw(recorded_mode, buildings, building_types):
        # Saves made before save_nsfw_mode existed load it as None; for those we
        # fall back to inspecting the buildings the player actually owns.
        if recorded_mode is not None:
            return bool(recorded_mode)
        return _save_has_restricted_building(buildings, building_types)

    # persistent.nsfw_enabled is global, so a session that flipped it to SFW
    # would mask every NSFW save as "Restricted Business". Restore is upward-only:
    # loading never disables a mode the player enabled by hand.
    def _after_load_restore_nsfw_mode():
        recorded = getattr(store, "save_nsfw_mode", None)
        building_types = building_types_json.get("building_types", [])
        if _save_expects_nsfw(recorded, getattr(store, "available_buildings", {}), building_types) and not getattr(persistent, "nsfw_enabled", False):
            set_nsfw_content_enabled(True)
            renpy.notify("NSFW mode restored to match this save")
        if recorded is None:
            store.save_nsfw_mode = bool(getattr(persistent, "nsfw_enabled", False))

    # Warn once per filter mode when a loaded save contains workers hidden by that filter.
    def _after_load_check_gender_filter():
        # Must never raise: Ren'Py runs after_load callbacks in a plain loop,
        # so an exception here would skip every callback registered later.
        try:
            if getattr(persistent, "worker_gender_filter", "both") == "both":
                return
            mode = persistent.worker_gender_filter
            workers = getattr(store, "workers", [])
            if not workers:
                return
            other_gender = "female" if mode == "male" else "male"
            has_other = any((w.get("gender") or "").strip().lower() == other_gender for w in workers if hasattr(w, "get"))
            warning_ack = getattr(persistent, "worker_gender_filter_warning_ack", None)
            if has_other and warning_ack != mode:
                store._pending_gender_filter_load_warning = True
                renpy.show_screen("gender_filter_after_load_warning")
        except Exception as e:
            import traceback
            renpy.log("GENDER_FILTER: ERROR - after_load check failed: %s" % e)
            renpy.log("GENDER_FILTER: traceback: %s" % traceback.format_exc())

    if not hasattr(config, "after_load_callbacks"):
        config.after_load_callbacks = []
    config.after_load_callbacks.append(_after_load_check_gender_filter)
    # _after_load_restore_nsfw_mode is invoked from label after_load
    # (save_snapshot.rpy) instead of config.after_load_callbacks: the label runs
    # after every callback AND after the label's second snapshot pass, so
    # save_nsfw_mode / available_buildings already hold their final restored
    # values when the heuristic reads them.
