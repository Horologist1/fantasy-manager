# (Removed unused closing overlay after switching to confirm+direct actions)
################################################################################
## Initialization
################################################################################

init offset = -1

init python:
    from calendar import Calendar
    from renpy import store

    class Player:
        def __init__(self):
            self.title = "Tavern Owner"  # Default title
            self.name = "Player"  # Default name
            self.money = 1000  # Starting money
            self.workers = []  # List of workers
            self.buildings = []  # List of buildings

    store.player = Player()
    
    def _is_equipped(item):
        """Check if an item is equipped. Must be defined at module level for pickling."""
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            return False
        eq = item[2]
        if isinstance(eq, bool):
            return eq
        if isinstance(eq, str):
            return eq.lower() in ("true", "1", "yes")
        if isinstance(eq, (int, float)):
            return bool(eq) and eq != 0
        return False
    
    store._is_equipped = _is_equipped

    def _is_inv_entry(x):
        """Duck-typed sequence check for inventory entries (tuples/lists).

        Inside screen/label python, `list` is RevertableList, so
        isinstance(x, (list, tuple)) silently fails for PLAIN lists coming from
        fresh json.loads. This accepts tuple/list/RevertableList and rejects
        str and dict-likes.
        """
        return hasattr(x, "__getitem__") and not isinstance(x, str) and not hasattr(x, "get")

    def get_worker_portrait_cached(worker):
        """
        Small portrait path for roster-row thumbnails, cached per worker.
        get_worker_image() scans the worker's image folder, which is far too
        costly to run per row per render. Only static image formats qualify
        (a webm/mp4 profile would be wasteful at 48px); None means "no art"
        and callers should show a placeholder.
        """
        if not worker or not hasattr(worker, "get"):
            return None
        key = (str(worker.get("name", "")), str(worker.get("folder", "")))
        cache = getattr(store, "_worker_portrait_cache", None)
        if cache is None:
            cache = {}
            store._worker_portrait_cache = cache
        if key not in cache:
            path = None
            try:
                cand = get_worker_image(worker)
                if (cand and isinstance(cand, str)
                        and cand.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
                        and renpy.loadable(cand)):
                    path = cand
            except Exception:
                path = None
            cache[key] = path
        return cache[key]

    def _building_select_global_sync():
        """Sync buildings once when Building_select_global is shown (moved out of the render path)."""
        if renpy.predicting():
            return
        try:
            validate_and_sync_buildings(include_worker_refs=False)
        except Exception as e:
            renpy.log(f"Building_select_global: validate_and_sync_buildings error: {str(e)}")

    def _map_screen_autorefill():
        """Auto-refill map worker offers once when map_screen is shown (moved out of the render path).

        Auto-refill does NOT count as a manual refresh - it's just initial population.
        """
        if renpy.predicting():
            return
        # Check if it's a new day - reset counter if so
        if store.last_map_refill_day != store.current_day:
            store.map_worker_refill_count = 0
            store.last_map_refill_day = store.current_day
        # Only auto-refill if available_workers is empty
        if not getattr(store, "available_workers", None):
            load_buy_workers()
            update_displayed_workers()

    def rebuild_assigned_servants():
        """Rebuild assigned_servants from current runtime state (no snapshot restore in UI flow)."""
        canonical_fn = getattr(store, "_canonical_rebuild_assigned_servants", None)
        if callable(canonical_fn):
            canonical_fn()
            return
        try:
            if not hasattr(store, 'workers') or not hasattr(store, 'available_buildings'):
                return
            
            # Rebuild assigned_servants from workers' assigned_building.
            # Use normalized key matching so "Building 1" and "Building_1" both work.
            _norm = getattr(store, '_norm_building_key', lambda k: (str(k).strip() if k else ""))
            workers_by_building = {}
            for w in store.workers:
                if hasattr(w, 'get'):
                    ab = w.get("assigned_building", "Unassigned")
                    if ab == "Unassigned" or not ab:
                        continue
                    ab_norm = _norm(ab)
                    matched_bname = None
                    for bname in store.available_buildings:
                        if _norm(bname) == ab_norm:
                            matched_bname = bname
                            break
                    if matched_bname:
                        if matched_bname not in workers_by_building:
                            workers_by_building[matched_bname] = []
                        workers_by_building[matched_bname].append(w)
            
            for bname, bdata in store.available_buildings.items():
                if hasattr(bdata, '__setitem__'):
                    bdata["assigned_servants"] = workers_by_building.get(bname, [])
        except Exception as e:
            renpy.log("rebuild_assigned_servants error: " + str(e))

    store.rebuild_assigned_servants = rebuild_assigned_servants

    def calculate_specialty_buyer_sale_price(worker):
        """
        Sale price formula:
        (original_cost + sum(skills)) * level * 3
        """
        try:
            base_cost = int(worker.get("cost", 0) or 0)
        except Exception:
            base_cost = 0

        skills_sum = 0
        try:
            skills = worker.get("skills", {}) or {}
            if hasattr(skills, "items"):
                for _, v in skills.items():
                    try:
                        skills_sum += int(v)
                    except Exception:
                        continue
        except Exception:
            skills_sum = 0

        try:
            lvl = int(worker.get("level", 1) or 1)
        except Exception:
            lvl = 1

        try:
            return int((base_cost + skills_sum) * lvl * 3)
        except Exception:
            return 0

    store.calculate_specialty_buyer_sale_price = calculate_specialty_buyer_sale_price

    def sell_worker_to_specialty_buyer(worker):
        """Apply sale payout and remove worker from roster. Returns sale price (int)."""
        price = calculate_specialty_buyer_sale_price(worker)
        try:
            store.money = int(getattr(store, "money", 0) or 0) + int(price or 0)
        except Exception:
            pass

        try:
            wname = worker.get("name")
            if wname and hasattr(store, "workers") and store.workers is not None:
                # Mutate in-place to preserve Ren'Py reactivity (RevertableList)
                store.workers[:] = [w for w in store.workers if (hasattr(w, "get") and w.get("name") != wname)]
        except Exception as e:
            renpy.log("sell_worker_to_specialty_buyer error: " + str(e))

        try:
            if hasattr(store, "rebuild_assigned_servants"):
                store.rebuild_assigned_servants()
        except Exception:
            pass

        return price

    store.sell_worker_to_specialty_buyer = sell_worker_to_specialty_buyer

    INTRO_POPUP_COMMON_TIP = (
        "at the top-right to enable or review tooltips."
    )

    INTRO_POPUP_TEXTS = {
        "tavern": {
            "title": "Welcome to the Tavern",
            "body": [
                "This is your command hub between day cycles. Most strategic decisions start here before pressing next day.",
                "",
                "{u}Journal{/u}: track objectives, tutorial progress, and quest gates that unlock systems such as new shops or progression routes.",
                "{u}Explore{/u}: open the city map to recruit workers, buy servants, visit shops, unlock academy and arena, and trigger city-side actions.",
                "{u}Buildings{/u}: assign staff, configure jobs, run upgrades, and tune each building skill bonus for output versus upkeep.",
                "{u}Workers{/u}: control roster actions (fire/sell, reassignment, rest), monitor readiness, and open each worker's detailed management panel.",
                "{u}Storage{/u}: move equipment and consumables between manager stock and workers before work starts.",
                "{u}Next day{/u}: advances time and then opens the daily report with incomes, costs, and outcomes; click result entries (success, failure, mediocre) to view related scene images.",
            ],
        },
        "map_screen": {
            "title": "Welcome to the City Map",
            "body": [
                "This screen handles expansion, recruiting, shopping, and city progression outside the tavern menu.",
                "",
                "{u}Recruit workers{/u}: available once per day. this runs recruitment events where unique or encounter candidates can join if you succeed.",
                "{u}Buy servants{/u}: direct market purchase with upfront gold cost. Bought workers usually start at desired comfort 1, while recruited workers usually start around 4 (or 3 after successful wage negotiation).",
                "{u}Servant refresh{/u}: buy servants has one free refresh and one paid refresh per day, then no more rerolls until tomorrow.",
                "{u}Buy buildings{/u}: expands your economy with new properties and more assignment capacity.",
                "{u}Visit shops{/u}: each shop has different inventory/value tiers, and higher tiers unlock later through progression.",
                "{u}Take a walk{/u}: limited to once per day and can trigger city outcomes without direct gold cost.",
                "{u}Academy{/u} and {u}Arena{/u}: both require entry investment, then open long-term training and combat progression loops.",
            ],
        },
        "manager_buildings": {
            "title": "Welcome to Manage Buildings",
            "body": [
                "This is where each property is configured for production, costs, and role efficiency.",
                "",
                "{u}Upgrade building{/u}: raises building level using a level-based cost curve and improves your performance ceiling.",
                "{u}Building skill{/u}: appears right under upgrade. the label changes by building type, and the bonus has its own daily upkeep.",
                "{u}Assignment quality{/u}: assign workers to jobs that match their strengths to improve daily results.",
                "{u}Economy control{/u}: stronger skill bonuses increase output but also increase daily expenses, so tune for sustainable net profit.",
                "{u}Management loop{/u}: use this screen with daily report to identify weak buildings and adjust assignments or costs quickly.",
            ],
        },
        "workers": {
            "title": "Welcome to Manage Workers",
            "body": [
                "This roster is your staffing control center for assignments, quick actions, and operational readiness.",
                "",
                "{u}Building and job filters{/u}: isolate teams by property and role to fix mismatches fast.",
                "{u}Rows and statuses{/u}: each line shows assignment, energy and health state, and action availability.",
                "{u}Sell or fire{/u}: servants are sold, non-servants are fired. this affects roster size and economy planning differently.",
                "{u}Reassign or rest{/u}: move workers between buildings/jobs or set rest when they need recovery.",
                "{u}Quick recovery{/u}: if energy or health is low, row actions can use or buy potions directly.",
                "{u}Worker details{/u}: open full control for comfort, automation, equipment, interactions, and long-term growth.",
            ],
        },
        "worker_details": {
            "title": "Worker Details Explained",
            "body": [
                "This panel gives full control over one worker's assignment, stats, comfort, automation, and progression.",
                "",
                "{u}Assignment summary{/u}: shows current building and job, so you can confirm role placement before day resolution.",
                "{u}Comfort and salary{/u}: comfort level directly drives daily cost; level 1 is baseline, and each level above 1 adds +1 daily energy regeneration at day start. Comfort targets also affect relationship stability.",
                "{u}Auto equip{/u}: when enabled, equips stronger role-appropriate gear from manager inventory after assignment changes.",
                "{u}Auto supply potions{/u}: pulls a configured number of potions from manager stock each day if available.",
                "{u}Bars and growth{/u}: health, energy, and other bars combine base values with traits, gear effects, and progression bonuses.",
                "{u}Interact{/u}: interactions have daily limits and category-based unlock progression, so use them consistently for long-term development.",
            ],
        },
        "storage": {
            "title": "Welcome to Storage",
            "body": [
                "Use this screen to transfer, equip, and organize items between manager inventory and workers.",
                "",
                "{u}Left and right panels{/u}: left is source, right is destination. use right/left transfer buttons to move in that direction.",
                "{u}Worker headers{/u}: click the worker name to swap panel ownership without leaving this screen.",
                "{u}Worker mini panel{/u}: the right-side summary shows the selected worker's quick stats or skills while you trade.",
                "{u}Rotate panel{/u}: use the switch button to flip between stats view and skills view instantly.",
                "{u}Quantity{/u}: cycle x1, x10, x100 for precise moves or bulk transfers.",
                "{u}Equipment rules{/u}: workers equip one item per slot/type; moving equipped items auto-unequips when required.",
                "{u}Item actions{/u}: consumables can be used directly, and gear can be equipped or unequipped from here.",
            ],
        },
        "shop_inventory": {
            "title": "Welcome to Shop Trading",
            "body": [
                "This is the active trading view used when entering a shop from the city map.",
                "",
                "{u}Shop tiers{/u}: different markets expose different price ranges, and higher-tier shops unlock later.",
                "{u}Buy flow{/u}: select an item on the shop side, then click the underlined {u}Buy{/u} button in that row to purchase it into manager inventory.",
                "{u}Buy button behavior{/u}: if quantity is above x1, one click buys in bulk up to your affordable limit.",
                "{u}Quantity{/u}: x1, x10, x100 controls bulk buying and selling speed.",
                "{u}Affordability check{/u}: bulk buy is capped automatically by your current gold and item price.",
                "{u}Sell value{/u}: selling back to shop uses a reduced return, so prioritize purchases with clear roster impact.",
            ],
        },
        "daily_report": {
            "title": "Daily Report Overview",
            "body": [
                "After next day, this screen explains what happened financially and operationally across your business.",
                "",
                "{u}Totals{/u}: compare earnings, costs, and net result to understand whether the day was profitable.",
                "{u}Cost composition{/u}: daily costs include building fixed cost, worker comfort-based pay, and building skill upkeep.",
                "{u}Building filter{/u}: isolate one property to evaluate its contribution and detect weak performers.",
                "{u}Job filter{/u}: narrow by profession to see which roles are creating profit or losses.",
                "{u}Result colors{/u}: outcome color coding helps you spot failures, mediocre runs, and strong performances quickly.",
                "{u}Decision loop{/u}: use this report to decide tomorrow's assignment, comfort, and investment changes.",
            ],
        },
        "yvara_visit": {
            "title": "Yvara Romance Quest",
            "body": [
                "This is a visual novel style romance route. Progress comes from repeated visits, conversations, remarks, and gifts over multiple days.",
                "",
                "{u}Devotion{/u}: romantic progress (warmth, trust, emotional intimacy). Higher devotion pushes scenes and tone toward romance.",
                "{u}Dominion{/u}: domination progress (control, leverage, submission dynamics). Higher dominion pushes scenes toward manager-led power dynamics.",
                "{u}Affection{/u}: overall closeness and route momentum. This is the main stage gate, regardless of whether romance or domination leads.",
                "{u}Progress system{/u}: talking with her advances the route. Remarks and gifts accelerate progression.",
                "{u}Pacing{/u}: talk, remark, and gift actions are day-gated, so progress is spread across multiple days.",
                "{u}Quick read{/u}: use {u}Take her measure{/u} during visits to see current totals and route direction in-character.",
            ],
        },
    }

    def _ensure_intro_popup_state():
        if not hasattr(persistent, "intro_popups_enabled"):
            persistent.intro_popups_enabled = True
        if not hasattr(persistent, "intro_popups_seen") or persistent.intro_popups_seen is None:
            persistent.intro_popups_seen = {}
        if not hasattr(store, "_intro_popup_current"):
            store._intro_popup_current = None

    def get_intro_popup_entry(screen_id):
        return INTRO_POPUP_TEXTS.get(screen_id)

    def maybe_show_intro_popup(screen_id):
        _ensure_intro_popup_state()
        if not persistent.intro_popups_enabled:
            return
        if persistent.intro_popups_seen.get(screen_id, False):
            return
        if store._intro_popup_current == screen_id:
            return
        if renpy.get_screen("screen_intro_popup") is not None:
            return
        if get_intro_popup_entry(screen_id) is None:
            return
        store._intro_popup_current = screen_id
        renpy.show_screen("screen_intro_popup", screen_id=screen_id)

    def mark_intro_popup_seen(screen_id):
        _ensure_intro_popup_state()
        seen = dict(persistent.intro_popups_seen)
        seen[screen_id] = True
        persistent.intro_popups_seen = seen
        if store._intro_popup_current == screen_id:
            store._intro_popup_current = None
        renpy.save_persistent()

    def close_intro_popup(screen_id):
        mark_intro_popup_seen(screen_id)
        renpy.hide_screen("screen_intro_popup")

    def disable_intro_popups(screen_id=None):
        _ensure_intro_popup_state()
        persistent.intro_popups_enabled = False
        if screen_id:
            seen = dict(persistent.intro_popups_seen)
            seen[screen_id] = True
            persistent.intro_popups_seen = seen
        store._intro_popup_current = None
        renpy.hide_screen("screen_intro_popup")
        renpy.save_persistent()

    store.INTRO_POPUP_COMMON_TIP = INTRO_POPUP_COMMON_TIP
    store.get_intro_popup_entry = get_intro_popup_entry
    store.maybe_show_intro_popup = maybe_show_intro_popup
    store.close_intro_popup = close_intro_popup
    store.disable_intro_popups = disable_intro_popups

################################################################################
## Styles
################################################################################

style default:
    properties gui.text_properties()
    language gui.language

# Estilos requeridos (agregar en tu archivo de estilos)
style table_button_text:
    color "#ffffff"
    hover_color "#ffd700"
    size 20
    xalign 0.5
    yalign 0.5
    outlines [(1, "#000000", 0, 0)]

style table_text:
    color "#ffffff"
    size 20
    xalign 0.5
    yalign 0.5
    bold False

# Buy/Sell/Left/Right action buttons in inventory/shop: underlined, no bold, green hover
style inv_trade_action_button:
    background None
    hover_background None
style inv_trade_action_button_text:
    color "#ffffff"
    hover_color gui.journal_hover_color
    bold False
    size 24

# Custom styles for comfort adjustment and other UI elements
style header_style:
    color "#ffddaa"
    size 28
    xalign 0.5
    bold True

# Interaction screen styles (moved here from the deleted file_save_system.rpy;
# used by the interaction_menu / interaction category screens below)
style interaction_frame is frame:
    background "#d4a574"  # Color beige
    padding (20, 20)

style interaction_text is text:
    color "#5d4037"
    hover_color "#314311"  # Verde oscuro

style interaction_button is button:
    background "images/tablebutton.png"
    hover_background "#d4a574"
    xalign 0.5
    yalign 0.5

style interaction_button_text is button_text:
    xalign 0.5
    yalign 0.5
    text_align 0.5
    color "#5d4037"
    hover_color "#314311"  # Verde oscuro

style confirm_button:
    background "#1a1a1acc"
    hover_background "#3a3a3acc"
    xsize 150
    ysize 50
    
style confirm_button_text:
    color "#ffffff"
    hover_color "#ff69b4"
    size 24
    xalign 0.5
    yalign 0.5

style cancel_button:
    background "#1a1a1acc"
    hover_background "#3a3a3acc"
    xsize 150
    ysize 50

style cancel_button_text:
    color "#ffffff"
    hover_color "#ff69b4"
    size 24
    xalign 0.5
    yalign 0.5

style input:
    properties gui.text_properties("input", accent=True)
    adjust_spacing False

style hyperlink_text:
    properties gui.text_properties("hyperlink", accent=True)
    hover_underline True

style gui_text:
    properties gui.text_properties("interface")


style button:
    properties gui.button_properties("button")

style button_text is gui_text:
    properties gui.text_properties("button")
    yalign 0.5


style label_text is gui_text:
    properties gui.text_properties("label", accent=True)

style prompt_text is gui_text:
    properties gui.text_properties("prompt")


style bar:
    ysize gui.bar_size
    left_bar Frame("gui/slider/horizontal_idle_bar.png", gui.bar_borders, tile=gui.bar_tile)
    right_bar Frame("gui/slider/horizontal_hover_bar.png", gui.bar_borders, tile=gui.bar_tile)

style vbar:
    xsize gui.bar_size
    top_bar Frame("gui/bar/top.png", gui.vbar_borders, tile=gui.bar_tile)
    bottom_bar Frame("gui/bar/bottom.png", gui.vbar_borders, tile=gui.bar_tile)

style scrollbar:
    ysize gui.scrollbar_size
    base_bar Frame("gui/scrollbar/horizontal_[prefix_]bar.png", gui.scrollbar_borders, tile=gui.scrollbar_tile)
    thumb Frame("gui/scrollbar/horizontal_[prefix_]thumb.png", gui.scrollbar_borders, tile=gui.scrollbar_tile)

style vscrollbar:
    xsize gui.scrollbar_size
    base_bar Frame("gui/scrollbar/vertical_[prefix_]bar.png", gui.vscrollbar_borders, tile=gui.scrollbar_tile)
    thumb Frame("gui/scrollbar/vertical_[prefix_]thumb.png", gui.vscrollbar_borders, tile=gui.scrollbar_tile)

style slider:
    ysize gui.slider_size
    base_bar Frame("gui/slider/horizontal_[prefix_]bar.png", gui.slider_borders, tile=gui.slider_tile)
    thumb "gui/slider/horizontal_[prefix_]thumb.png"

style vslider:
    xsize gui.slider_size
    base_bar Frame("gui/slider/vertical_[prefix_]bar.png", gui.vslider_borders, tile=gui.slider_tile)
    thumb "gui/slider/vertical_[prefix_]thumb.png"


style frame:
    padding gui.frame_borders.padding
    background Frame("gui/frame.png", gui.frame_borders, tile=gui.frame_tile)


################################################################################
## In-game screens
################################################################################


## Say screen ##################################################################
##
## The say screen is used to display dialogue to the player. It takes two
## parameters, who and what, which are the name of the speaking character and
## the text to be displayed, respectively. (The who parameter can be None if no
## name is given.)
##
## This screen must create a text displayable with id "what", as Ren'Py uses
## this to manage text display. It can also create displayables with id "who"
## and id "window" to apply style properties.
##
## https://www.renpy.org/doc/html/screen_special.html#say

screen say(who, what):
    style_prefix "say"

    window:
        id "window"

        if who is not None:

            window:
                id "namebox"
                style "namebox"
                text who id "who"

        text what id "what"


    ## If there's a side image, display it above the text. Do not display on the
    ## phone variant - there's no room.
    if not renpy.variant("small"):
        add SideImage() xalign 0.0 yalign 1.0
    
    ## Overlay for historical message when navigating back
    if dialogue_history_offset > 0:
        $ clamp_history_offset()
        $ history_entry = get_history_message(dialogue_history_offset)
        if history_entry:
            # Full overlay that covers the dialogue box
            window:
                id "history_overlay"
                style_prefix "say"
                xalign 0.5
                yalign gui.textbox_yalign
                xfill True
                ysize gui.textbox_height
                background Image("gui/textbox.png", xalign=0.5, yalign=1.0)
                
                # Historical character name
                if history_entry.who:
                    window:
                        style "namebox"
                        text history_entry.who
                
                # Historical dialogue text
                $ history_what = renpy.filter_text_tags(history_entry.what, allow=gui.history_allow_tags)
                text history_what:
                    style "say_dialogue"
            
    ## History navigation buttons - navigate through previous messages without undoing actions
    use dialogue_history_nav

## Optional message window for scripted show/hide calls.
screen message_window():
    window:
        id "window"
        style "say_window"


## Make the namebox available for styling through the Character object.
init python:
    config.character_id_prefixes.append('namebox')

## Dialogue History Navigation Screen ###########################################
##
## This screen provides navigation buttons to view previous dialogue messages
## without undoing any game actions. It's a read-only navigation system.
##
init python:
    # Variable to track history navigation offset (0 = current message, 1 = previous, etc.)
    dialogue_history_offset = 0
    
    def get_history_message(offset):
        """Get a message from history at the given offset (0 = current, 1 = previous, etc.)."""
        if not _history_list:
            return None
        
        history_size = len(_history_list)
        
        # Clamp offset to valid range
        safe_offset = max(0, min(offset, history_size - 1))
        
        # Calculate the actual index in _history_list
        # _history_list is ordered newest first: [newest, ..., oldest]
        # So index = size - 1 - offset
        history_index = history_size - 1 - safe_offset
        
        if history_index < 0 or history_index >= history_size:
            return None
        
        try:
            return _history_list[history_index]
        except (IndexError, TypeError):
            return None
    
    def can_go_back_in_history():
        """Check if we can go back further in history."""
        if not _history_list or len(_history_list) <= 1:
            return False
        
        # Simple check: can go back if offset is less than history size - 1
        # This allows navigating through recent messages
        history_size = len(_history_list)
        max_offset = history_size - 1
        
        return dialogue_history_offset < max_offset
    
    def can_go_forward_in_history():
        """Check if we can go forward (toward current message)."""
        return dialogue_history_offset > 0
    
    def mark_dialogue_start():
        """Mark the current position as the start of a new conversation."""
        store.dialogue_history_start_index = len(_history_list)
        store.dialogue_history_offset = 0
        renpy.log(f"Dialogue start index set to {store.dialogue_history_start_index}")
    
    def clamp_history_offset():
        """Clamp history offset to valid range. Called after ANY modification."""
        if not _history_list:
            store.dialogue_history_offset = 0
            return
        
        history_size = len(_history_list)
        max_offset = max(0, history_size - 1)
        store.dialogue_history_offset = max(0, min(store.dialogue_history_offset, max_offset))
    
    def safe_increment_history_offset():
        """Safely increment history offset with bounds checking."""
        if can_go_back_in_history():
            store.dialogue_history_offset += 1
            clamp_history_offset()
    
    def safe_decrement_history_offset():
        """Safely decrement history offset with bounds checking."""
        if store.dialogue_history_offset > 0:
            store.dialogue_history_offset -= 1
            clamp_history_offset()

screen dialogue_history_nav():
    ## Only show if we're viewing dialogue and there's history
    if len(_history_list) > 0:
        # Ensure offset is always valid when drawing buttons
        $ clamp_history_offset()
        $ can_go_back = can_go_back_in_history()
        $ can_go_forward = can_go_forward_in_history()
        
        # Previous message button - moved 345px from left, 140px up from bottom
        imagebutton:
            xpos 345
            yalign 0.95
            yoffset -140
            idle "gui/arrowpreviousidle.png"
            hover "gui/arrowprevioushover.png"
            action If(can_go_back, Function(safe_increment_history_offset), NullAction())
            tooltip "Previous message (←)"
            at transform:
                zoom 0.0625
        
        # Next message button - right side, same height as previous, 345px from right edge
        imagebutton:
            xalign 1.0
            xoffset -345
            yalign 0.95
            yoffset -140
            idle "gui/arrownextidle.png"
            hover "gui/arrownexthover.png"
            action If(can_go_forward, Function(safe_decrement_history_offset), NullAction())
            tooltip "Next message (→)"
            at transform:
                zoom 0.0625
        
        # Small indicator below Previous button
        if dialogue_history_offset > 0:
            text "[dialogue_history_offset]":
                xpos 350
                yalign 0.95
                yoffset -120
                size 16
                color "#D2691E"
                xanchor 0.5

style window is default
style say_label is default
style say_dialogue is default
style say_thought is say_dialogue

style namebox is default
style namebox_label is say_label


style window:
    xalign 0.5
    xfill True
    yalign gui.textbox_yalign
    ysize gui.textbox_height

    background Image("gui/textbox.png", xalign=0.5, yalign=1.0)

style namebox:
    xpos gui.name_xpos
    xanchor gui.name_xalign
    xsize gui.namebox_width
    ypos gui.name_ypos
    ysize gui.namebox_height

    background Frame("gui/namebox.png", gui.namebox_borders, tile=gui.namebox_tile, xalign=gui.name_xalign)
    padding gui.namebox_borders.padding

style say_label:
    properties gui.text_properties("name", accent=True)
    xalign gui.name_xalign
    yalign 0.5

style say_dialogue:
    properties gui.text_properties("dialogue")

    xpos gui.dialogue_xpos
    xsize gui.dialogue_width
    ypos gui.dialogue_ypos

    adjust_spacing False

## Input screen ################################################################
##
## This screen is used to display renpy.input. The prompt parameter is used to
## pass a text prompt in.
##
## This screen must create an input displayable with id "input" to accept the
## various input parameters.
##
## https://www.renpy.org/doc/html/screen_special.html#input

screen input(prompt):
    style_prefix "input"

    window:

        vbox:
            xanchor gui.dialogue_text_xalign
            xpos gui.dialogue_xpos
            xsize gui.dialogue_width
            ypos gui.dialogue_ypos

            text prompt style "input_prompt"
            input id "input"

style input_prompt is default

style input_prompt:
    xalign gui.dialogue_text_xalign
    properties gui.text_properties("input_prompt")

style input:
    xalign gui.dialogue_text_xalign
    xmaximum gui.dialogue_width


## Choice screen ###############################################################
##
## This screen is used to display the in-game choices presented by the menu
## statement. The one parameter, items, is a list of objects, each with caption
## and action fields.
##
## https://www.renpy.org/doc/html/screen_special.html#choice

screen choice(items):
    style_prefix "choice"

    vbox:
        for i in items:
            textbutton i.caption action i.action


style choice_vbox is vbox
style choice_button is button
style choice_button_text is button_text

style choice_vbox:
    xalign 0.5
    ypos 405
    yanchor 0.5

    spacing gui.choice_spacing

style choice_button is default:
    properties gui.button_properties("choice_button")

style choice_button_text is default:
    properties gui.text_properties("choice_button")


## Quick Menu screen ###########################################################
##
## The quick menu is displayed in-game to provide easy access to the out-of-game
## menus.

screen quick_menu():
    pass

## This code ensures that the quick_menu screen is displayed in-game, whenever
## the player has not explicitly hidden the interface.
init python:
    config.overlay_screens.append("quick_menu")

default quick_menu = True

style quick_button is default
style quick_button_text is button_text

style quick_button:
    properties gui.button_properties("quick_button")
    variant "touch"
    xminimum 240
    yminimum 92
    xpadding 18
    ypadding 12
    background Frame("gui/button/quick_[prefix_]_background.png", gui.quick_button_borders, tile=gui.button_tile)

style quick_button_text:
    properties gui.text_properties("quick_button")
    variant "touch"
    xalign 0.5
    yalign 0.5


################################################################################
## Main and Game Menu Screens
################################################################################

## Navigation screen ###########################################################
##
## This screen is included in the main and game menus, and provides navigation
## to other menus, and to start the game.

screen navigation():

    vbox:
        style_prefix "navigation"

        xpos gui.navigation_xpos
        yalign 0.5

        spacing gui.navigation_spacing

        if main_menu:

            textbutton _("Start") action [Function(mark_new_game_start), Start()]

        else:

            textbutton _("History") action ShowMenu("history")

            textbutton _("Save") action ShowMenu("save")

        textbutton _("Load") action ShowMenu("load")

        textbutton _("Preferences") action ShowMenu("preferences")

        if _in_replay:

            textbutton _("End Replay") action EndReplay(confirm=True)

        elif not main_menu:

            textbutton _("Main Menu") action MainMenu()

        textbutton _("About") action ShowMenu("about")

        if renpy.variant("pc") or (renpy.variant("web") and not renpy.variant("mobile")):

            ## Help isn't necessary or relevant to mobile devices.
            textbutton _("Help") action ShowMenu("help")

        if renpy.variant("pc"):

            ## The quit button is banned on iOS and unnecessary on Android and
            ## Web.
            ## DISABLED: Quit button causes issues, use Main Menu or window close instead
            # textbutton _("Quit") action Quit(confirm=not main_menu)
            pass


style navigation_button is gui_button
style navigation_button_text is gui_button_text

style navigation_button:
    size_group "navigation"
    properties gui.button_properties("navigation_button")

style navigation_button_text:
    properties gui.text_properties("navigation_button")


## Main Menu screen ############################################################
##
## Used to display the main menu when Ren'Py starts.
##
## https://www.renpy.org/doc/html/screen_special.html#main-menu

screen main_menu():

    ## This ensures that any other menu screen is replaced.
    tag menu

    add "gui/main_menu.png"
    on "show" action [SetVariable("at_main_menu", True), Function(start_bgm_simple, "audio/BGM.ogg")]
    on "hide" action SetVariable("at_main_menu", False)

    ## Use imagebuttons with centered positions
    imagebutton auto "gui/main_menu/buttons/start_%s.png" xpos 761 ypos 345 focus_mask True action [Function(mark_new_game_start), Start()]
    imagebutton auto "gui/main_menu/buttons/load_%s.png" xalign 0.5 ypos 456 focus_mask True action ShowMenu("load")
    imagebutton auto "gui/main_menu/buttons/options_%s.png" xalign 0.5 ypos 516 focus_mask True action ShowMenu("preferences")
    # Gallery button removed while the gallery screen is a "Coming Soon" stub (screen kept below for later)
    imagebutton auto "gui/main_menu/buttons/about_%s.png" xalign 0.5 ypos 622 focus_mask True action ShowMenu("about")
    imagebutton auto "gui/main_menu/buttons/help_%s.png" xalign 0.5 ypos 675 focus_mask True action ShowMenu("help")
    imagebutton auto "gui/main_menu/buttons/quit_%s.png" xalign 0.5 ypos 728 focus_mask True action Quit(confirm=True)

    if gui.show_name:

        vbox:
            style "main_menu_vbox"

            text "Version [config.version]":
                style "main_menu_version"


style main_menu_frame is empty
style main_menu_vbox is vbox
style main_menu_text is gui_text
style main_menu_title is main_menu_text
style main_menu_version is main_menu_text

style main_menu_frame:
    xsize 420
    yfill True
    # (background "gui/overlay/main_menu.png" removed: asset does not exist)

style main_menu_vbox:
    xalign 1.0
    xoffset -150
    xmaximum 1200
    yalign 1.0
    yoffset -130

style main_menu_text:
    properties gui.text_properties("main_menu", accent=True)

style main_menu_title:
    properties gui.text_properties("title")
    size gui.title_text_size - 4

style main_menu_version:
    properties gui.text_properties("version")


## Game Menu screen ############################################################
##
## This lays out the basic common structure of a game menu screen. It's called
## with the screen title, and displays the background, title, and navigation.
##
## The scroll parameter can be None, or one of "viewport" or "vpgrid".
## This screen is intended to be used with one or more children, which are
## transcluded (placed) inside it.

screen game_menu(title, scroll=None, yinitial=0.0, spacing=0):

    style_prefix "game_menu"

    if main_menu:
        add gui.main_menu_background
    else:
        add gui.game_menu_background

    frame:
        style "game_menu_outer_frame"

        hbox:

            ## Reserve space for the navigation section.
            frame:
                style "game_menu_navigation_frame"

            frame:
                style "game_menu_content_frame"

                if scroll == "viewport":

                    viewport:
                        yinitial yinitial
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        pagekeys True

                        side_yfill True

                        vbox:
                            spacing spacing

                            transclude

                elif scroll == "vpgrid":

                    vpgrid:
                        cols 1
                        yinitial yinitial

                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        pagekeys True

                        side_yfill True

                        spacing spacing

                        transclude

                else:

                    transclude

    use navigation

    textbutton _("Return"):
        style "return_button"

        action Return()

    label title

    if main_menu:
        key "game_menu" action ShowMenu("main_menu")


style game_menu_outer_frame is empty
style game_menu_navigation_frame is empty
style game_menu_content_frame is empty
style game_menu_viewport is gui_viewport
style game_menu_side is gui_side
style game_menu_scrollbar is gui_vscrollbar

style game_menu_label is gui_label
style game_menu_label_text is gui_label_text

style return_button is navigation_button
style return_button_text is navigation_button_text

style game_menu_outer_frame:
    bottom_padding 45
    top_padding 180

    background "gui/overlay/game_menu.png"

style game_menu_navigation_frame:
    xsize 420
    yfill True

style game_menu_content_frame:
    left_margin 60
    right_margin 30
    top_margin 15

style game_menu_viewport:
    xsize 1380

style game_menu_vscrollbar:
    unscrollable gui.unscrollable

style game_menu_side:
    spacing 15

style game_menu_label:
    xpos 75
    ysize 180

style game_menu_label_text:
    size gui.title_text_size
    color gui.accent_color
    yalign 0.5

style return_button:
    xpos gui.navigation_xpos
    yalign 1.0
    yoffset -45


## About screen ################################################################
##
## This screen gives credit and copyright information about the game and Ren'Py.
##
## There's nothing special about this screen, and hence it also serves as an
## example of how to make a custom screen.

screen about():

    tag menu

    add "gui/gallery.png"

    imagebutton:
        idle "gui/button/return_idle.png"
        hover "gui/button/return_hover.png"
        action Return()
        xalign 1.0
        yalign 0.0
        xoffset -135
        yoffset 140

    fixed:
        xpos 200
        ypos 240
        xmaximum config.screen_width - 360
        ymaximum 660
        viewport:
            scrollbars "vertical"
            mousewheel True
            draggable True
            vbox:
                spacing 20

                text "Fantasy Manager":
                    style "about_title"
                    xalign 0.0

                text "Version [config.version]":
                    style "about_version"
                    xalign 0.0

                text "A fantasy management game where you build your empire. NSFW content is optional and can be enabled or disabled from Options → More Options.":
                    style "about_description"
                    xalign 0.0

                ## Espacio antes de Credits
                null height 20

                text "Credits:":
                    style "about_section_header"
                    xalign 0.0
                text "Game development, AI + Digital illustration - Horologist":
                    style "about_section_text"
                    xalign 0.0
                text "AI + Digital illustration - Annekka":
                    style "about_section_text"
                    xalign 0.0
                text "Guest Workers Design - Lupse":
                    style "about_section_text"
                    xalign 0.0
                text "Code Review - Bohnd":
                    style "about_section_text"
                    xalign 0.0
                text "UI Assets - Skolaztika":
                    style "about_section_text"
                    xalign 0.0

                ## Licencia
                text "License:":
                    style "about_section_header"
                    xalign 0.0
                text "This game is licensed under CC BY-NC-SA 4.0, you can find information online, and in the game folder.":
                    style "about_section_text"
                    xalign 0.0

                ## Espacio antes de Ren'Py
                null height 60

                text "Made with Ren'Py [renpy.version_only]":
                    style "about_credits"
                    xalign 0.0




style about_title:
    size 48
    color gui.journal_dark_color
    xalign 0.5

style about_version:
    size 32
    color gui.journal_hover_color
    xalign 0.5

style about_description:
    size 24
    color gui.journal_dark_color
    xalign 0.5

style about_credits:
    size 20
    color gui.journal_hover_color
    xalign 0.5

style about_section_header:
    size 22
    color gui.journal_dark_color
    xalign 0.5
    underline True

style about_section_text:
    size 20
    color gui.journal_dark_color
    xalign 0.5

style about_instruction:
    size 28
    color "#314311"
    xalign 0.5


## Worker Gender: warning after loading a save that has both genders ###########
screen gender_filter_after_load_warning():
    modal True
    zorder 200
    $ _filter_label = "Only Male" if persistent.worker_gender_filter == "male" else "Only Female"
    add Solid(gui.surface_dark)
    frame:
        xalign 0.5
        yalign 0.5
        xsize 700
        padding (30, 30)
        background Solid("#2a2a1acc")
        vbox:
            spacing 20
            label "Worker Gender filter" xalign 0.5 style "header_style"
            text "This save has workers of both genders, but your filter is set to '[_filter_label]'. If you continue, workers of the other gender will be unassigned and sold or fired (you keep refunds for servants). For the best experience, start a new game.":
                size 22
                color "#e8e8e8"
                text_align 0.5
                xalign 0.5
            null height 10
            hbox:
                xalign 0.5
                spacing 30
                textbutton "Go to Main Menu":
                    action [SetVariable("_pending_gender_filter_load_warning", False), Hide("gender_filter_after_load_warning"), MainMenu()]
                    text_size 24
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                textbutton "Continue playing":
                    action [
                        Function(remove_workers_of_other_gender_for_filter),
                        SetVariable("_pending_gender_filter_load_warning", False),
                        Hide("gender_filter_after_load_warning")
                    ]
                    text_size 24
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color


## Load and Save screens #######################################################
##
## These screens are responsible for letting the player save the game and load
## it again. Since they share nearly everything in common, both are implemented
## in terms of a third screen, file_slots.
##
## https://www.renpy.org/doc/html/screen_special.html#save https://
## www.renpy.org/doc/html/screen_special.html#load

screen save():

    tag menu

    imagemap:
        ground 'gui/SaveLoad/saveload_ground.png'
        idle 'gui/SaveLoad/saveload_idle.png'
        hover 'gui/SaveLoad/saveload_hover.png'
        selected_idle 'gui/SaveLoad/saveload_selected.png'
        selected_hover 'gui/SaveLoad/saveload_hover.png'
        cache False

        hotspot (458, 204, 47, 48) action FilePage(1)
        hotspot (531, 204, 48, 48) action FilePage(2)
        hotspot (606, 204, 45, 48) action FilePage(3)
        hotspot (679, 204, 47, 48) action FilePage(4)
        hotspot (753, 204, 47, 48) action FilePage(5)
        hotspot (827, 204, 47, 48) action FilePage(6)
        
        # Page navigation buttons
        textbutton _("<"):
            xpos 410
            ypos 204
            xsize 32
            ysize 48
            text_size 32
            text_color "#5d4037"
            text_hover_color "#314311"
            background None
            hover_background None
            action FilePagePrevious()
        textbutton _(">"):
            xpos 880
            ypos 204
            xsize 32
            ysize 48
            text_size 32
            text_color "#5d4037"
            text_hover_color "#314311"
            background None
            hover_background None
            action FilePageNext()
        
        # Show page number when beyond page 6
        if persistent._file_page not in ["auto", "quick", 1, 2, 3, 4, 5, 6, "1", "2", "3", "4", "5", "6"]:
            frame:
                xpos 915
                ypos 204
                xsize 48
                ysize 48
                background "#5d4037"
                text "[persistent._file_page]":
                    xalign 0.5
                    yalign 0.5
                    size 22
                    color "#f0e6c8"

        ## Save slots
        $ slot1_has_save = FileTime(1, empty=None) is not None
        $ slot2_has_save = FileTime(2, empty=None) is not None
        $ slot3_has_save = FileTime(3, empty=None) is not None
        $ slot4_has_save = FileTime(4, empty=None) is not None
        hotspot (468, 312, 393, 207) action If(
            slot1_has_save,
            Confirm(_("Overwrite this save?"), SnapshotFileSave(1, confirm=False), None),
            SnapshotFileSave(1, confirm=False)
        ):
            use load_save_slot(number=1)
        hotspot (468, 620, 393, 207) action If(
            slot2_has_save,
            Confirm(_("Overwrite this save?"), SnapshotFileSave(2, confirm=False), None),
            SnapshotFileSave(2, confirm=False)
        ):
            use load_save_slot(number=2)
        hotspot (1055, 312, 393, 207) action If(
            slot3_has_save,
            Confirm(_("Overwrite this save?"), SnapshotFileSave(3, confirm=False), None),
            SnapshotFileSave(3, confirm=False)
        ):
            use load_save_slot(number=3)
        hotspot (1055, 620, 393, 207) action If(
            slot4_has_save,
            Confirm(_("Overwrite this save?"), SnapshotFileSave(4, confirm=False), None),
            SnapshotFileSave(4, confirm=False)
        ):
            use load_save_slot(number=4)

        ## Navigation buttons
        hotspot (85, 263, 233, 90) action ShowMenu('history')
        hotspot (1584, 245, 239, 91) action ShowMenu('about')
        hotspot (1584, 411, 242, 98) action ShowMenu('help')

        hotspot (75, 613, 246, 88) action ShowMenu('preferences')
        hotspot (75, 483, 257, 91) action ShowMenu('load')
        hotspot (82, 366, 265, 90) action ShowMenu('save')
        hotspot (1584, 537, 254, 91) action MainMenu()
        # Quit button disabled - close window instead
        # hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

        hotspot (1448, 183, 64, 65) action Return()


screen load():

    tag menu

    imagemap:
        ground 'gui/SaveLoad/saveload_ground.png'
        idle 'gui/SaveLoad/saveload_idle.png'
        hover 'gui/SaveLoad/saveload_hover.png'
        selected_idle 'gui/SaveLoad/saveload_selected.png'
        selected_hover 'gui/SaveLoad/saveload_hover.png'
        cache False

        hotspot (458, 204, 47, 48) action FilePage(1)
        hotspot (531, 204, 48, 48) action FilePage(2)
        hotspot (606, 204, 45, 48) action FilePage(3)
        hotspot (679, 204, 47, 48) action FilePage(4)
        hotspot (753, 204, 47, 48) action FilePage(5)
        hotspot (827, 204, 47, 48) action FilePage(6)
        
        # Page navigation buttons
        textbutton _("<"):
            xpos 410
            ypos 204
            xsize 32
            ysize 48
            text_size 32
            text_color "#5d4037"
            text_hover_color "#314311"
            background None
            hover_background None
            action FilePagePrevious()
        textbutton _(">"):
            xpos 880
            ypos 204
            xsize 32
            ysize 48
            text_size 32
            text_color "#5d4037"
            text_hover_color "#314311"
            background None
            hover_background None
            action FilePageNext()
        
        # Show page number when beyond page 6
        if persistent._file_page not in ["auto", "quick", 1, 2, 3, 4, 5, 6, "1", "2", "3", "4", "5", "6"]:
            frame:
                xpos 915
                ypos 204
                xsize 48
                ysize 48
                background "#5d4037"
                text "[persistent._file_page]":
                    xalign 0.5
                    yalign 0.5
                    size 22
                    color "#f0e6c8"

        ## Load slots
        hotspot (468, 312, 393, 207) action [Function(snapshot_mark_load_slot, 1), FileAction(1)]:
            use load_save_slot(number=1)
        hotspot (468, 620, 393, 207) action [Function(snapshot_mark_load_slot, 2), FileAction(2)]:
            use load_save_slot(number=2)
        hotspot (1055, 312, 393, 207) action [Function(snapshot_mark_load_slot, 3), FileAction(3)]:
            use load_save_slot(number=3)
        hotspot (1055, 620, 393, 207) action [Function(snapshot_mark_load_slot, 4), FileAction(4)]:
            use load_save_slot(number=4)

        ## Navigation buttons
        hotspot (85, 263, 233, 90) action ShowMenu('history')
        hotspot (1584, 245, 239, 91) action ShowMenu('about')
        hotspot (1584, 411, 242, 98) action ShowMenu('help')

        hotspot (75, 613, 246, 88) action ShowMenu('preferences')
        hotspot (75, 483, 257, 91) action ShowMenu('load')
        hotspot (82, 366, 265, 90) action ShowMenu('save')
        hotspot (1584, 537, 254, 91) action MainMenu()
        # Quit button disabled - close window instead
        # hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

        hotspot (1448, 183, 64, 65) action Return()


screen file_slots(title):

    default page_name_value = FilePageNameInputValue(pattern=_("Page {}"), auto=_("Automatic saves"), quick=_("Quick saves"))

    use game_menu(title):

        fixed:

            ## This ensures the input will get the enter event before any of the
            ## buttons do.
            order_reverse True

            ## The page name, which can be edited by clicking on a button.
            button:
                style "page_label"

                key_events True
                xalign 0.5
                action page_name_value.Toggle()

                input:
                    style "page_label_text"
                    value page_name_value

            ## The grid of file slots.
            grid gui.file_slot_cols gui.file_slot_rows:
                style_prefix "slot"

                xalign 0.5
                yalign 0.5

                spacing gui.slot_spacing

                for i in range(gui.file_slot_cols * gui.file_slot_rows):

                    $ slot = i + 1

                    button:
                        action [Function(snapshot_mark_load_slot, slot), FileAction(slot)]

                        # Thumbnail fills the slot; date + save_name overlay at the bottom on a dark band.
                        fixed:
                            xsize gui.slot_button_width - 30
                            ysize gui.slot_button_height - 30

                            add Solid("#1a1a1a")
                            add FileScreenshot(slot) xalign 0.5 yalign 0.0

                            frame:
                                xalign 0.5
                                yalign 1.0
                                xfill True
                                background Solid("#000000c0")
                                padding (8, 6)

                                vbox:
                                    xfill True
                                    spacing 2

                                    text FileTime(slot, format=_("{#file_time}%a %b %d %Y, %H:%M"), empty=_("empty slot")):
                                        size 22
                                        color "#ffffff"
                                        xalign 0.5

                                    text FileSaveName(slot):
                                        size 24
                                        color "#ffe680"
                                        xalign 0.5

                        key "save_delete" action [Function(snapshot_pre_delete_slot, slot), FileDelete(slot)]

            ## Buttons to access other pages.
            vbox:
                style_prefix "page"

                xalign 0.5
                yalign 1.0

                hbox:
                    xalign 0.5

                    spacing gui.page_spacing

                    textbutton _("<") action FilePagePrevious()

                    if config.has_autosave:
                        textbutton _("{#auto_page}A") action FilePage("auto")

                    if config.has_quicksave:
                        textbutton _("{#quick_page}Q") action FilePage("quick")

                    ## range(1, 10) gives the numbers from 1 to 9.
                    for page in range(1, 10):
                        textbutton "[page]" action FilePage(page)

                    textbutton _(">") action FilePageNext()

                if config.has_sync:
                    if CurrentScreenName() == "save":
                        textbutton _("Upload Sync"):
                            action UploadSync()
                            xalign 0.5
                    else:
                        textbutton _("Download Sync"):
                            action DownloadSync()
                            xalign 0.5


style page_label is gui_label
style page_label_text is gui_label_text
style page_button is gui_button
style page_button_text is gui_button_text

style slot_button is gui_button
style slot_button_text is gui_button_text
style slot_time_text is slot_button_text
style slot_name_text is slot_button_text

style page_label:
    xpadding 75
    ypadding 5

style page_label_text:
    textalign 0.5
    layout "subtitle"
    hover_color gui.hover_color

style page_button:
    properties gui.button_properties("page_button")

style page_button_text:
    properties gui.text_properties("page_button")

style slot_button:
    properties gui.button_properties("slot_button")

style slot_button_text:
    properties gui.text_properties("slot_button")


## Preferences screen ##########################################################
##
## The preferences screen allows the player to configure the game to better suit
## themselves.
##
## https://www.renpy.org/doc/html/screen_special.html#preferences

screen preferences():

    tag menu

    imagemap:
        ground 'gui/Config/config_ground.png'
        idle 'gui/Config/config_idle.png'
        hover 'gui/Config/config_hover.png'
        selected_idle 'gui/Config/config_sidle.png'
        selected_hover 'gui/Config/config_shover.png'
        cache False

        ## DISPLAY
        hotspot (547, 275, 201, 59) action Preference('display', 'fullscreen')
        hotspot (547, 347, 201, 53) action Preference('display', 'window')

        ## SKIP
        hotspot (547, 504, 126, 54) action Preference('skip', 'seen')
        hotspot (547, 574, 101, 54) action Preference('skip', 'all')

        ## AFTER CHOICES
        hotspot (547, 718, 266, 59) action Preference('after choices', 'skip')
        hotspot (547, 794, 129, 55) action Preference('after choices', 'stop')

        ## NAVIGATION
        hotspot (85, 263, 233, 90) action ShowMenu('history')
        hotspot (1584, 245, 239, 91) action ShowMenu('about')
        hotspot (1584, 411, 242, 98) action ShowMenu('help')

        hotspot (75, 613, 246, 88) action ShowMenu('preferences')
        hotspot (75, 483, 257, 91) action ShowMenu('load')
        hotspot (82, 366, 265, 90) action ShowMenu('save')
        hotspot (1584, 537, 254, 91) action MainMenu()
        # Quit button disabled - close window instead
        # hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

        hotspot (1448, 183, 64, 65) action Return()

        hotbar (1053, 291, 372, 37) value Preference('text speed')
        hotbar (1053, 466, 372, 37) value Preference('music volume')
        hotbar (1053, 640, 372, 37) value Preference('sound volume')
        hotbar (1053, 728, 372, 37) value Preference('voice volume')
        hotbar (1053, 816, 372, 37) value Preference('auto-forward time')

    ## More Options button (bottom right) – opens second options page
    textbutton _("More Options"):
        xalign 1.0
        yalign 1.0
        xoffset -410
        yoffset -150
        text_size 28
        text_color gui.journal_dark_color
        text_hover_color gui.journal_hover_color
        action ShowMenu("more_options")
    ## NSFW toggle removed from Preferences (moved to About screen)


## More Options screen (second options page) #####################################
##
## Shown when the player clicks "More Options" on the Preferences screen.
## Uses the image in gui/Config (e.g. config_page2.png). Back returns to Preferences.

screen more_options():

    tag menu

    add "gui/Config/config_page2.png"

    ## Options tab: full-screen image with transparent background, "Options" tab in correct position
    add "gui/Config/options_hover.png"

    ## Close button (top-right): same as preferences – idle/hover from config images, not color overlay
    imagebutton:
        idle Transform("gui/Config/config_idle.png", crop=(1448, 183, 64, 65))
        hover Transform("gui/Config/config_hover.png", crop=(1448, 183, 64, 65))
        xpos 1448
        ypos 183
        action Return()

    ## Options content: NSFW, Gender, Difficulty (left), Tutorials (right)
    fixed:
        xmaximum 1400
        vbox:
            xpos 475
            ypos 275
            spacing 14
            hbox:
                spacing 20
                $ _nsfw_on = persistent.nsfw_enabled
                $ _c_en = gui.journal_hover_color if _nsfw_on else gui.journal_dark_color
                $ _c_off = gui.journal_hover_color if not _nsfw_on else gui.journal_dark_color
                textbutton "Enabled":
                    text_color _c_en
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    # Refresh trait/interaction caches so the toggle applies without a restart
                    action [SetField(persistent, "nsfw_enabled", True), Function(refresh_traits_cache, force=True), Function(invalidate_interactions_cache)]
                textbutton "Disabled":
                    text_color _c_off
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action [SetField(persistent, "nsfw_enabled", False), Function(refresh_traits_cache, force=True), Function(invalidate_interactions_cache)]

        ## Worker Gender: Both / Only Female / Only Male
        vbox:
            xpos 475
            ypos 505
            spacing 14
            hbox:
                spacing 18
                $ _wg = persistent.worker_gender_filter
                $ _cb = gui.journal_hover_color if _wg == "both" else gui.journal_dark_color
                $ _cf = gui.journal_hover_color if _wg == "female" else gui.journal_dark_color
                $ _cm = gui.journal_hover_color if _wg == "male" else gui.journal_dark_color
                textbutton "Both":
                    text_color _cb
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "worker_gender_filter", "both")
                textbutton "Only Female":
                    text_color _cf
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action If(main_menu,
                        SetField(persistent, "worker_gender_filter", "female"),
                        Confirm(_("For the best experience with 'Only Female', start a new game. Workers of the other gender in your current save will remain (costs, assignments) but won't appear in lists. Go to Main Menu to start a new game?"),
                            [SetField(persistent, "worker_gender_filter", "female"), MainMenu()],
                            SetField(persistent, "worker_gender_filter", "female")))
                textbutton "Only Male":
                    text_color _cm
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action If(main_menu,
                        SetField(persistent, "worker_gender_filter", "male"),
                        Confirm(_("For the best experience with 'Only Male', start a new game. Workers of the other gender in your current save will remain (costs, assignments) but won't appear in lists. Go to Main Menu to start a new game?"),
                            [SetField(persistent, "worker_gender_filter", "male"), MainMenu()],
                            SetField(persistent, "worker_gender_filter", "male")))

        ## Difficulty: Story / Easy / Normal / Hard / Nightmare
        vbox:
            xpos 475
            ypos 720
            spacing 14
            $ _diff = getattr(persistent, "difficulty", "normal")
            $ _hovered = getattr(store, "_about_hovered_difficulty", None)
            $ _display_diff = _hovered if _hovered else _diff
            $ _cs = gui.journal_hover_color if _diff == "story" else gui.journal_dark_color
            $ _ce = gui.journal_hover_color if _diff == "easy" else gui.journal_dark_color
            $ _cn = gui.journal_hover_color if _diff == "normal" else gui.journal_dark_color
            $ _ch = gui.journal_hover_color if _diff == "hard" else gui.journal_dark_color
            $ _cnm = gui.journal_hover_color if _diff == "nightmare" else gui.journal_dark_color
            $ _diff_descriptions = {
                "story": "Relaxed. +30 worker bonus, 75% min success, no money loss on failure, earnings x1.3, comfort $15/pt, normal maintenance.",
                "easy": "Forgiving. +20 worker bonus, 60% min success, failure losses capped at -$25, earnings x1.15, comfort $18/pt, normal maintenance.",
                "normal": "Standard. +10 worker bonus, 55% min success, no failure cap, earnings x1.0, comfort $20/pt, normal maintenance.",
                "hard": "Tough. No worker bonus, 45% min success, no failure cap, earnings x0.85, x2 consequences, comfort $25/pt, x2 maintenance, x1.5 skill upkeep, reduced loot.",
                "nightmare": "Brutal. No worker bonus, 35% min success, -10 skill penalty, earnings x0.7, x3 consequences, comfort $30/pt, x3 maintenance, x2 skill upkeep, heavily reduced loot."
            }
            hbox:
                spacing 6
                textbutton "Story":
                    text_size font_size(28)
                    text_color _cs
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "difficulty", "story")
                    hovered SetVariable("_about_hovered_difficulty", "story")
                    unhovered SetVariable("_about_hovered_difficulty", None)
                textbutton "Easy":
                    text_size font_size(28)
                    text_color _ce
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "difficulty", "easy")
                    hovered SetVariable("_about_hovered_difficulty", "easy")
                    unhovered SetVariable("_about_hovered_difficulty", None)
                textbutton "Normal":
                    text_size font_size(28)
                    text_color _cn
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "difficulty", "normal")
                    hovered SetVariable("_about_hovered_difficulty", "normal")
                    unhovered SetVariable("_about_hovered_difficulty", None)
                textbutton "Hard":
                    text_size font_size(28)
                    text_color _ch
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "difficulty", "hard")
                    hovered SetVariable("_about_hovered_difficulty", "hard")
                    unhovered SetVariable("_about_hovered_difficulty", None)
                textbutton "Nightmare":
                    text_size font_size(28)
                    text_color _cnm
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "difficulty", "nightmare")
                    hovered SetVariable("_about_hovered_difficulty", "nightmare")
                    unhovered SetVariable("_about_hovered_difficulty", None)
            text _diff_descriptions.get(_display_diff, _diff_descriptions["normal"]):
                size 20
                color "#5D2E1A"
                xalign 0.0
                xmaximum 400
                text_align 0.0

        ## Tutorials: Enabled / Disabled / Reset (right page, same format as NSFW)
        vbox:
            xpos 1085
            ypos 275
            spacing 14
            $ _te = getattr(persistent, "intro_popups_enabled", True)
            $ _tc = gui.journal_hover_color if _te else gui.journal_dark_color
            $ _td = gui.journal_hover_color if not _te else gui.journal_dark_color
            hbox:
                spacing 20
                textbutton "Enabled":
                    text_color _tc
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "intro_popups_enabled", True)
                textbutton "Disabled":
                    text_color _td
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action SetField(persistent, "intro_popups_enabled", False)
                textbutton "Reset":
                    text_color gui.journal_hover_color
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action [
                        SetField(persistent, "intro_popups_enabled", True),
                        SetField(persistent, "intro_popups_seen", {}),
                        SetVariable("_intro_popup_current", None)
                    ]

        ## Worker automation defaults (right page, under Defaults)
        vbox:
            xpos 1085
            ypos 505
            spacing 14
            vbox:
                spacing 8
                textbutton "Stock Potions: [default_auto_supply_compact_label()]":
                    text_color gui.journal_dark_color
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action Function(cycle_persistent_default_auto_supply_compact)
                textbutton "Auto-rest: [default_auto_rest_compact_label()]":
                    text_color gui.journal_dark_color
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action Function(cycle_persistent_default_auto_rest_compact)
                textbutton "Auto Equip: [getattr(persistent, 'default_auto_equip', False) and 'On' or 'Off']":
                    text_color gui.journal_dark_color
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action Function(toggle_persistent_default_auto_equip)
                # Note: label reads "confirm: On" when the dialog IS shown
                # (i.e. skip_potion_buy_confirm is False).
                textbutton "Potion buy confirm: [not getattr(persistent, 'skip_potion_buy_confirm', False) and 'On' or 'Off']":
                    text_color gui.journal_dark_color
                    text_hover_color gui.journal_hover_color
                    background None
                    hover_background None
                    action ToggleField(persistent, "skip_potion_buy_confirm")
            text "Applies to all current workers. Auto-stock/Auto-equip try to apply immediately; Auto-rest is evaluated during the daily cycle (Next Day).":
                size 20
                color "#5D2E1A"
                xalign 0.0
                xmaximum 430
                text_align 0.0

    textbutton _("Back"):
        xalign 1.0
        yalign 1.0
        xoffset -410
        yoffset -150
        text_size 28
        text_color gui.journal_dark_color
        text_hover_color gui.journal_hover_color
        action ShowMenu("preferences")


style pref_label is gui_label
style pref_label_text is gui_label_text
style pref_vbox is vbox

style radio_label is pref_label
style radio_label_text is pref_label_text
style radio_button is gui_button
style radio_button_text is gui_button_text
style radio_vbox is pref_vbox

style check_label is pref_label
style check_label_text is pref_label_text
style check_button is gui_button
style check_button_text is gui_button_text
style check_vbox is pref_vbox

style slider_label is pref_label
style slider_label_text is pref_label_text
style slider_slider is gui_slider
style slider_button is gui_button
style slider_button_text is gui_button_text
style slider_pref_vbox is pref_vbox

style mute_all_button is check_button
style mute_all_button_text is check_button_text

style pref_label:
    top_margin gui.pref_spacing
    bottom_margin 3

style pref_label_text:
    yalign 1.0
    color gui.journal_dark_color

style pref_vbox:
    xsize 338

style radio_vbox:
    spacing gui.pref_button_spacing

style radio_button:
    properties gui.button_properties("radio_button")
    foreground "gui/button/radio_[prefix_]foreground.png"

style radio_button_text:
    properties gui.text_properties("radio_button")
    color gui.journal_dark_color

style check_vbox:
    spacing gui.pref_button_spacing

style check_button:
    properties gui.button_properties("check_button")
    foreground "gui/button/check_[prefix_]foreground.png"

style check_button_text:
    properties gui.text_properties("check_button")

style slider_slider:
    xsize 525

style slider_button:
    properties gui.button_properties("slider_button")
    yalign 0.5
    left_margin 15

style slider_button_text:
    properties gui.text_properties("slider_button")

style slider_vbox:
    xsize 675


## History screen ##############################################################
##
## This is a screen that displays the dialogue history to the player. While
## there isn't anything special about this screen, it does have to access the
## dialogue history stored in _history_list.
##
## https://www.renpy.org/doc/html/history.html

screen history():

    tag menu

    ## Avoid predicting this screen, as it can be very large.
    predict False
    style_prefix "history"
    
    imagemap:
        ground 'gui/abouthistory/menu_idle.png'
        idle 'gui/abouthistory/menu_idle.png'
        hover 'gui/abouthistory/menu_hover.png'
        selected_idle 'gui/abouthistory/menu_hover.png'
        selected_hover 'gui/abouthistory/menu_hover.png'
        cache False

        hotspot (85, 263, 233, 90) action ShowMenu('history')
        hotspot (1584, 245, 239, 91) action ShowMenu('about')
        hotspot (1584, 411, 242, 98) action ShowMenu('help')

        hotspot (75, 613, 246, 88) action ShowMenu('preferences')
        hotspot (75, 483, 257, 91) action ShowMenu('load')
        hotspot (82, 366, 265, 90) action ShowMenu('save')
        hotspot (1584, 537, 254, 91) action MainMenu()
        # Quit button disabled - close window instead
        # hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

        hotspot (1448, 183, 64, 65) action Return()
        
    # Two-panel layout for history
    hbox:
        xalign 0.5
        ypos 250
        spacing 20
        
        # Left page
        frame:
            xsize 580
            ysize 600
            background None
            viewport id "vpgrid_left":
                yinitial 1.0
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 580
                xsize 560
                
                vbox:
                    spacing 0
                    
                    for h in _history_list[::2]:  # Even indices (0, 2, 4...)
                        window:
                            has fixed:
                                yfit True
                                
                            if h.who:
                                text h.who:
                                    size 26
                                    color "#5D2E1A"
                                    bold True
                                    xpos 20
                                    ypos 5
                                    substitute False
                                    
                            $ what = renpy.filter_text_tags(h.what, allow=gui.history_allow_tags)
                            text what:
                                size 24
                                color "#8B4513"
                                xpos 20
                                ypos 25
                                xsize 520
                                substitute False
        
        # Right page  
        frame:
            xsize 580
            ysize 600
            background None
            viewport id "vpgrid_right":
                yinitial 1.0
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 580
                xsize 560
                
                vbox:
                    spacing 0
                    
                    for h in _history_list[1::2]:  # Odd indices (1, 3, 5...)
                        window:
                            has fixed:
                                yfit True
                                
                            if h.who:
                                text h.who:
                                    size 26
                                    color "#5D2E1A"
                                    bold True
                                    xpos 20
                                    ypos 5
                                    substitute False
                                    
                            $ what = renpy.filter_text_tags(h.what, allow=gui.history_allow_tags)
                            text what:
                                size 24
                                color "#8B4513"
                                xpos 20
                                ypos 25
                                xsize 520
                                substitute False
    
    # Empty message if no history
    if not _history_list:
        label _("The dialogue history is empty."):
            xalign 0.5
            ypos 400


## This determines what tags are allowed to be displayed on the history screen.

define gui.history_allow_tags = { "alt", "noalt", "rt", "rb", "art" }


style history_window is empty

style history_name is gui_label
style history_name_text is gui_label_text
style history_text is gui_text

style history_label is gui_label
style history_label_text is gui_label_text

style history_window:
    xfill True
    ysize gui.history_height

style history_name:
    xpos gui.history_name_xpos
    xanchor gui.history_name_xalign
    ypos gui.history_name_ypos
    xsize gui.history_name_width

style history_name_text:
    min_width gui.history_name_width
    textalign gui.history_name_xalign
    color "#ffffff"

style history_text:
    xpos gui.history_text_xpos
    ypos gui.history_text_ypos
    xanchor gui.history_text_xalign
    xsize gui.history_text_width
    min_width gui.history_text_width
    textalign gui.history_text_xalign
    layout ("subtitle" if gui.history_text_xalign else "tex")
    color "#ffffff"

style history_label:
    xfill True

style history_label_text:
    xalign 0.5
    color "#ffffff"


## Help screen #################################################################
##
## A screen that gives information about key and mouse bindings. It uses other
## screens (keyboard_help, mouse_help, and gamepad_help) to display the actual
## help.

screen help():

    tag menu

    default device = "keyboard"

    ## Background imagemap matching About/History pages
    imagemap:
        ground 'gui/abouthistory/menu_idle.png'
        idle 'gui/abouthistory/menu_idle.png'
        hover 'gui/abouthistory/menu_hover.png'
        selected_idle 'gui/abouthistory/menu_hover.png'
        selected_hover 'gui/abouthistory/menu_hover.png'
        cache False

        ## Navigation tabs on the sides
        hotspot (85, 263, 233, 90) action ShowMenu('history')
        hotspot (1584, 245, 239, 91) action ShowMenu('about')
        hotspot (1584, 411, 242, 98) action ShowMenu('help')

        ## Return button (top-right X)
        hotspot (1448, 183, 64, 65) action Return()

    style_prefix "help"

    ## Page content area
    vbox:
        xpos 160
        ypos 210
        spacing 20

        ## Device selector (styled like other menus)
        hbox:
            spacing 30
            xoffset 220
            textbutton _("Keyboard") action SetScreenVariable("device", "keyboard"):
                text_size font_size(26)
                text_color gui.journal_text_color
                text_hover_color gui.journal_hover_color
                background None
                hover_background None
            textbutton _("Mouse") action SetScreenVariable("device", "mouse"):
                text_size font_size(26)
                text_color gui.journal_text_color
                text_hover_color gui.journal_hover_color
                background None
                hover_background None

        if device == "keyboard":
            use keyboard_help
        elif device == "mouse":
            use mouse_help


screen keyboard_help():

    $ entries = [
        (_("Enter"), _("Advances dialogue and activates the interface.")),
        (_("Space"), _("Advances dialogue without selecting choices.")),
        (_("Arrow Keys"), _("Navigate the interface.")),
        (_("Escape"), _("Accesses the game menu.")),
        (_("BackSpace"), _("Closes most game screens (Close, Back, and Return buttons).")),
        (_("Ctrl+Left Arrow"), _("Triggers the Previous button where available.")),
        (_("Ctrl+Right Arrow"), _("Triggers the Next button where available.")),
        (_("Ctrl"), _("Skips dialogue while held down.")),
        (_("Tab"), _("Toggles dialogue skipping.")),
        (_("Page Up"), _("Rolls back to earlier dialogue.")),
        (_("Page Down"), _("Rolls forward to later dialogue.")),
        ("H", _("Hides the user interface.")),
        ("S", _("Takes a screenshot.")),
        ("V", _("Toggles assistive {a=https://www.renpy.org/l/voicing}self-voicing{/a}.")),
        ("Shift+A", _("Opens the accessibility menu.")),
    ]
    $ mid = (len(entries) + 1) // 2

    hbox:
        xalign 0.5
        spacing 60
        vbox:
            spacing 8
            xoffset 0
            for k, d in entries[:mid]:
                hbox:
                    spacing 24
                    label k
                    text d:
                        size 20
        vbox:
            spacing 8
            xoffset -110
            for k, d in entries[mid:]:
                hbox:
                    spacing 24
                    label k
                    text d:
                        size 20


screen mouse_help():

    $ entries = [
        (_("Left Click"), _("Advances dialogue and activates the interface.")),
        (_("Middle Click"), _("Hides the user interface.")),
        (_("Right Click"), _("Accesses the game menu.")),
        (_("Mouse Wheel Up"), _("Rolls back to earlier dialogue.")),
        (_("Mouse Wheel Down"), _("Rolls forward to later dialogue.")),
    ]
    $ mid = (len(entries) + 1) // 2

    hbox:
        xalign 0.5
        spacing 60
        vbox:
            spacing 8
            xoffset 0
            for k, d in entries[:mid]:
                hbox:
                    spacing 24
                    label k
                    text d:
                        size 20
        vbox:
            spacing 8
            xoffset -110
            for k, d in entries[mid:]:
                hbox:
                    spacing 24
                    label k
                    text d:
                        size 20


## gamepad_help removed intentionally


style help_button is gui_button
style help_button_text is gui_button_text
style help_label is gui_label
style help_label_text is gui_label_text
style help_text is gui_text

style help_button:
    properties gui.button_properties("help_button")
    xmargin 12

style help_button_text:
    properties gui.text_properties("help_button")

style help_label:
    xsize 375
    right_padding 30

style help_label_text:
    size 22
    xalign 1.0
    textalign 1.0



################################################################################
## Additional screens
################################################################################


## Confirm screen ##############################################################
##
## The confirm screen is called when Ren'Py wants to ask the player a yes or no
## question.
##
## https://www.renpy.org/doc/html/screen_special.html#confirm

screen confirm(message, yes_action, no_action):

    ## Ensure other screens do not get input while this screen is displayed.
    modal True

    zorder 200

    style_prefix "confirm"

    add "gui/overlay/confirm.png"

    on "show" action Function(set_quit_action_disabled)
    on "hide" action Function(set_quit_action_smart)

    frame:

        vbox:
                xalign .5
                yalign .5
                spacing 45

                label _(message):
                    style "confirm_prompt"
                    xalign 0.5

                hbox:
                    xalign 0.5
                    spacing 50
                    textbutton _("Yes") action [yes_action, Function(set_quit_action_smart)]
                    textbutton _("No") action [no_action, Function(set_quit_action_smart)]

    ## Right-click and escape answer "no".
    key "game_menu" action no_action
    key "K_BACKSPACE" action no_action


style confirm_frame is gui_frame
style confirm_prompt is gui_prompt
style confirm_prompt_text is gui_prompt_text
style confirm_button is gui_medium_button
style confirm_button_text is gui_medium_button_text

style confirm_frame:
    background Frame("gui/frame.png", gui.confirm_frame_borders, tile=gui.frame_tile)
    padding gui.confirm_frame_borders.padding
    xalign .5
    yalign .5

style confirm_prompt_text:
    textalign 0.5
    layout "subtitle"
    size 42  # Aumentado 50% desde 28

style confirm_button:
    properties gui.button_properties("confirm_button")

style confirm_button_text:
    properties gui.text_properties("confirm_button")
    size 38
    color gui.journal_dark_color
    hover_color "#ffffff"  # Blanco en hover


## Skip indicator screen #######################################################
##
## The skip_indicator screen is displayed to indicate that skipping is in
## progress.
##
## https://www.renpy.org/doc/html/screen_special.html#skip-indicator

screen skip_indicator():

    zorder 100
    style_prefix "skip"

    frame:

        hbox:
            spacing 9

            text _("Skipping")

            text "▸" at delayed_blink(0.0, 1.0) style "skip_triangle"
            text "▸" at delayed_blink(0.2, 1.0) style "skip_triangle"
            text "▸" at delayed_blink(0.4, 1.0) style "skip_triangle"


## This transform is used to blink the arrows one after another.
transform delayed_blink(delay, cycle):
    alpha .5

    pause delay

    block:
        linear .2 alpha 1.0
        pause .2
        linear .2 alpha 0.5
        pause (cycle - .4)
        repeat

# Blink transform for PlazaServants button when textbutton is hovered
transform blink_transform:
    block:
        alpha 1.0
        pause 0.8
        alpha 0.0
        pause 0.8
        repeat


style skip_frame is empty
style skip_text is gui_text
style skip_triangle is skip_text

style skip_frame:
    ypos gui.skip_ypos
    background Frame("gui/skip.png", gui.skip_frame_borders, tile=gui.frame_tile)
    padding gui.skip_frame_borders.padding

style skip_text:
    size gui.notify_text_size

style skip_triangle:
    ## We have to use a font that has the BLACK RIGHT-POINTING SMALL TRIANGLE
    ## glyph in it.
    font "DejaVuSans.ttf"


## Notify screen ###############################################################
##
## The notify screen is used to show the player a message. (For example, when
## the game is quicksaved or a screenshot has been taken.)
##
## https://www.renpy.org/doc/html/screen_special.html#notify-screen

screen notify(message):

    zorder 100
    style_prefix "notify"

    frame at notify_appear:
        text "[message!tq]"

    timer 3.25 action Hide('notify')


transform notify_appear:
    on show:
        alpha 0
        linear .25 alpha 1.0
    on hide:
        linear .5 alpha 0.0


style notify_frame is empty
style notify_text is gui_text

style notify_frame:
    ypos gui.notify_ypos

    background Frame("gui/notify.png", gui.notify_frame_borders, tile=gui.frame_tile)
    padding gui.notify_frame_borders.padding

style notify_text:
    properties gui.text_properties("notify")
    color "#ffffff"


## NVL screen ##################################################################
##
## This screen is used for NVL-mode dialogue and menus.
##
## https://www.renpy.org/doc/html/screen_special.html#nvl


screen nvl(dialogue, items=None):

    window:
        style "nvl_window"

        has vbox:
            spacing gui.nvl_spacing

        ## Displays dialogue in either a vpgrid or the vbox.
        if gui.nvl_height:

            vpgrid:
                cols 1
                yinitial 1.0

                use nvl_dialogue(dialogue)

        else:

            use nvl_dialogue(dialogue)

        ## Displays the menu, if given. The menu may be displayed incorrectly if
        ## config.narrator_menu is set to True.
        for i in items:

            textbutton i.caption:
                action i.action
                style "nvl_button"

    add SideImage() xalign 0.0 yalign 1.0


screen nvl_dialogue(dialogue):

    for d in dialogue:

        window:
            id d.window_id

            fixed:
                yfit gui.nvl_height is None

                if d.who is not None:

                    text d.who:
                        id d.who_id

                text d.what:
                    id d.what_id


## This controls the maximum number of NVL-mode entries that can be displayed at
## once.
define config.nvl_list_length = gui.nvl_list_length

style nvl_window is default
style nvl_entry is default

style nvl_label is say_label
style nvl_dialogue is say_dialogue

style nvl_button is button
style nvl_button_text is button_text

style nvl_window:
    xfill True
    yfill True

    background "gui/nvl.png"
    padding gui.nvl_borders.padding

style nvl_entry:
    xfill True
    ysize gui.nvl_height

style nvl_label:
    xpos gui.nvl_name_xpos
    xanchor gui.nvl_name_xalign
    ypos gui.nvl_name_ypos
    yanchor 0.0
    xsize gui.nvl_name_width
    min_width gui.nvl_name_width
    textalign gui.nvl_name_xalign

style nvl_dialogue:
    xpos gui.nvl_text_xpos
    xanchor gui.nvl_text_xalign
    ypos gui.nvl_text_ypos
    xsize gui.nvl_text_width
    min_width gui.nvl_text_width
    textalign gui.nvl_text_xalign
    layout ("subtitle" if gui.nvl_text_xalign else "tex")

style nvl_thought:
    xpos gui.nvl_thought_xpos
    xanchor gui.nvl_thought_xalign
    ypos gui.nvl_thought_ypos
    xsize gui.nvl_thought_width
    min_width gui.nvl_thought_width
    textalign gui.nvl_thought_xalign
    layout ("subtitle" if gui.nvl_text_xalign else "tex")

style nvl_button:
    properties gui.button_properties("nvl_button")
    xpos gui.nvl_button_xpos
    xanchor gui.nvl_button_xalign

style nvl_button_text:
    properties gui.text_properties("nvl_button")


## Bubble screen ###############################################################
##
## The bubble screen is used to display dialogue to the player when using speech
## bubbles. The bubble screen takes the same parameters as the say screen, must
## create a displayable with the id of "what", and can create displayables with
## the "namebox", "who", and "window" ids.
##
## https://www.renpy.org/doc/html/bubble.html#bubble-screen

screen bubble(who, what):
    style_prefix "bubble"

    window:
        id "window"

        if who is not None:

            window:
                id "namebox"
                style "bubble_namebox"

                text who:
                    id "who"

        text what:
            id "what"

style bubble_window is empty
style bubble_namebox is empty
style bubble_who is default
style bubble_what is default

style bubble_window:
    xpadding 30
    top_padding 5
    bottom_padding 5

style bubble_namebox:
    xalign 0.5

style bubble_who:
    xalign 0.5
    textalign 0.5
    color "#000"

style bubble_what:
    align (0.5, 0.5)
    text_align 0.5
    layout "subtitle"
    color "#000"

define bubble.frame = Frame("gui/bubble.png", 55, 55, 55, 95)
define bubble.thoughtframe = Frame("gui/thoughtbubble.png", 55, 55, 55, 55)

define bubble.properties = {
    "bottom_left" : {
        "window_background" : Transform(bubble.frame, xzoom=1, yzoom=1),
        "window_bottom_padding" : 27,
    },

    "bottom_right" : {
        "window_background" : Transform(bubble.frame, xzoom=-1, yzoom=1),
        "window_bottom_padding" : 27,
    },

    "top_left" : {
        "window_background" : Transform(bubble.frame, xzoom=1, yzoom=-1),
        "window_top_padding" : 27,
    },

    "top_right" : {
        "window_background" : Transform(bubble.frame, xzoom=-1, yzoom=-1),
        "window_top_padding" : 27,
    },

    "thought" : {
        "window_background" : bubble.thoughtframe,
    }
}

define bubble.expand_area = {
    "bottom_left" : (0, 0, 0, 22),
    "bottom_right" : (0, 0, 0, 22),
    "top_left" : (0, 22, 0, 0),
    "top_right" : (0, 22, 0, 0),
    "thought" : (0, 0, 0, 0),
}



################################################################################
## Tooltip System
################################################################################

screen tooltip(message, xpos=None, ypos=None, screen_name=None):
    # Generic tooltip screen that displays a message.
    # Can be positioned with xpos/ypos, or defaults to mouse position.
    # Only shows if tooltips are enabled for the current screen
    zorder 500
    modal False
    
    python:
        # Determine current screen name if not provided
        if screen_name is None:
            # Check screens in priority order using renpy.get_screen()
            # renpy.get_screen() returns the screen object if shown, None otherwise
            if renpy.get_screen("map_screen"):
                detected_screen = "map_screen"
            elif renpy.get_screen("Manager"):
                detected_screen = "Manager"
            elif renpy.get_screen("tavern"):
                detected_screen = "tavern"
            elif renpy.get_screen("manager_inventory"):
                detected_screen = "manager_inventory"
            elif renpy.get_screen("report_details"):
                detected_screen = "report_details"
            elif renpy.get_screen("adjust_comfort"):
                detected_screen = "adjust_comfort"
            elif renpy.get_screen("adjust_skill_bonus"):
                detected_screen = "adjust_skill_bonus"
            elif renpy.get_screen("worker_details"):
                detected_screen = "WorkerDetails"
            else:
                # Fallback to default
                detected_screen = "default"
            screen_name = detected_screen
        else:
            detected_screen = screen_name
        
        # Guard: Hide tooltip if screen context changed (prevents tooltips from persisting across screens)
        if not hasattr(store, '_last_tooltip_screen'):
            store._last_tooltip_screen = detected_screen
        elif store._last_tooltip_screen != detected_screen:
            # Screen changed, hide tooltip
            renpy.hide_screen("tooltip")
            store._last_tooltip_screen = detected_screen
            tooltips_enabled = False
        else:
            store._last_tooltip_screen = detected_screen
            # Check if tooltips are enabled for this screen (defaults to True if not set)
            tooltips_enabled = get_tooltips_state_for_screen(screen_name)
    
    # Only show tooltip content if tooltips are enabled for this screen
    if tooltips_enabled:
        python:
            # Use provided position or default to mouse position
            if xpos is None:
                mouse_x, mouse_y = renpy.get_mouse_pos()
                # Tooltip max width is 250px, so we need to ensure it doesn't overflow
                screen_width = config.screen_width
                tooltip_max_width = 320
                # Position tooltip to the LEFT of mouse cursor to avoid blocking clicks
                # Only position to the right if we're near the left edge of screen
                if mouse_x < tooltip_max_width + 40:  # Near left edge, show on right
                    xpos = mouse_x + 20
                else:
                    # Show on left side of mouse
                    xpos = mouse_x - (tooltip_max_width + 20)
            if ypos is None:
                mouse_x, mouse_y = renpy.get_mouse_pos()
                ypos = mouse_y - 60  # Offset above mouse (adjusted for better visibility)
        
        # Outer frame with beige background and dark border
        frame:
            xpos xpos
            ypos ypos
            xpadding 0
            ypadding 0
            background Solid(gui.journal_dark_color)  # Dark brown border
            xsize None
            ysize None
            
            # Inner frame with beige background
            frame:
                xsize None
                ysize None
                xmargin 2
                ymargin 2
                background Solid("#d4a574")  # Beige background
                xpadding 6
                ypadding 4
                
                # Set maximum width for tooltip to allow text wrapping
                text message:
                    size 20
                    color gui.journal_dark_color
                    text_align 0.0
                    xalign 0.0
                    yalign 0.0
                    xmaximum 320  # Wider wrap for economy / multi-line help tooltips

################################################################################
## Mobile Variants
################################################################################

style pref_vbox:
    variant "medium"
    xsize 675

## that uses fewer and bigger buttons that are easier to touch.
screen quick_menu():
    variant "touch"

    zorder 100

    if quick_menu:

        hbox:
            style_prefix "quick"

            xalign 0.5
            yalign 1.0
            yoffset -8
            spacing 10

            # (Back/Rollback button removed: rollback is disabled game-wide in options.rpy)
            textbutton _("Skip") action Skip() alternate Skip(fast=True, confirm=True)
            textbutton _("Auto") action Preference("auto-forward", "toggle")
            textbutton _("Menu") action ShowMenu()


style window:
    variant "small"
    background Image("gui/textbox.png", xalign=0.5, yalign=1.0)

style choice_button:
    variant "small"
    background Frame("gui/button/choice_[prefix_]_background.png", gui.choice_button_borders, tile=gui.choice_button_tile)

style radio_button:
    variant "small"
    foreground "gui/button/radio_[prefix_]foreground.png"

style check_button:
    variant "small"
    foreground "gui/button/check_[prefix_]foreground.png"

style nvl_window:
    variant "small"
    background "gui/nvl.png"

style game_menu_outer_frame:
    variant "small"
    background "gui/overlay/game_menu.png"

style game_menu_navigation_frame:
    variant "small"
    xsize 510

style game_menu_content_frame:
    variant "small"
    top_margin 0

style pref_vbox:
    variant "small"
    xsize 600

style bar:
    variant "small"
    ysize gui.bar_size
    left_bar Frame("gui/bar/left.png", gui.bar_borders, tile=gui.bar_tile)
    right_bar Frame("gui/bar/right.png", gui.bar_borders, tile=gui.bar_tile)

style vbar:
    variant "small"
    xsize gui.bar_size
    top_bar Frame("gui/bar/top.png", gui.vbar_borders, tile=gui.bar_tile)
    bottom_bar Frame("gui/bar/bottom.png", gui.vbar_borders, tile=gui.bar_tile)

style scrollbar:
    variant "small"
    ysize gui.scrollbar_size
    base_bar Frame("gui/scrollbar/horizontal_[prefix_]bar.png", gui.scrollbar_borders, tile=gui.scrollbar_tile)
    thumb Frame("gui/scrollbar/horizontal_[prefix_]thumb.png", gui.scrollbar_borders, tile=gui.scrollbar_tile)

style vscrollbar:
    variant "small"
    xsize gui.scrollbar_size
    base_bar Frame("gui/scrollbar/vertical_[prefix_]bar.png", gui.vscrollbar_borders, tile=gui.scrollbar_tile)
    thumb Frame("gui/scrollbar/vertical_[prefix_]thumb.png", gui.vscrollbar_borders, tile=gui.scrollbar_tile)

style slider:
    variant "small"
    ysize gui.slider_size
    base_bar Frame("gui/slider/horizontal_[prefix_]bar.png", gui.slider_borders, tile=gui.slider_tile)
    thumb "gui/slider/horizontal_[prefix_]thumb.png"

style vslider:
    variant "small"
    xsize gui.slider_size
    base_bar Frame("gui/slider/vertical_[prefix_]bar.png", gui.vslider_borders, tile=gui.slider_tile)
    thumb "gui/slider/vertical_[prefix_]thumb.png"

style slider_vbox:
    variant "small"
    xsize None

style slider_slider:
    variant "small"
    xsize 900

################################################################################
### SCREEN DEFINITIONS
################################################################################
# Blink highlight for context-menu manager name when there are pending skill points
default manager_name_blink_highlight = False

screen error_popup(message):
    modal True
    zorder 200
    style_prefix "confirm"
    
    add "gui/overlay/confirm.png"
    
    frame:
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45
            
            text message:
                style "confirm_prompt"
                xalign 0.5
            
            hbox:
                xalign 0.5
                
                textbutton _("Ok") action Hide("error_popup")

    key "K_BACKSPACE" action Hide("error_popup")

screen screen_intro_popup(screen_id):
    modal True
    zorder 190
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))

    $ intro_entry = get_intro_popup_entry(screen_id)
    $ intro_title = intro_entry["title"] if intro_entry else "Screen Help"
    $ intro_body = intro_entry["body"] if intro_entry else ["No help text available for this screen."]

    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)

        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Function(close_intro_popup, screen_id)
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

        vbox:
            spacing 15
            xfill True
            null height 15
            label "[intro_title]" xalign 0.5 style "header_style"
            null height 6

            viewport:
                xsize 615
                ysize 410
                xalign 0.5
                mousewheel True
                draggable True
                scrollbars "vertical"

                vbox:
                    xsize 595
                    spacing 10
                    hbox:
                        spacing 4
                        xalign 0.5
                        text "Tip: Use the" size font_size(17) color "#5a3a1a" yalign 0.5 text_align 0.0
                        fixed:
                            xsize 20
                            ysize 20
                            yalign 0.5
                            add Transform("gui/info_idle.png", zoom=0.24) align (0.5, 0.5)
                        text "[INTRO_POPUP_COMMON_TIP]" size font_size(17) color "#5a3a1a" yalign 0.5 text_align 0.0
                    null height 8
                    for paragraph in intro_body:
                        text "[paragraph]" size font_size(22) color gui.journal_text_color text_align 0.0 xfill True justify True
            null height 4

            textbutton "Stop showing these messages":
                xalign 1.0
                xoffset -25
                yoffset 10
                text_size font_size(20)
                text_color gui.journal_hover_color
                text_hover_color "#ffffff"
                action Confirm(
                    _("Stop showing tutorial messages from now on? (You can turn them back on in options; more options)"),
                    Function(disable_intro_popups, screen_id),
                    NullAction()
                )

    key "game_menu" action Function(close_intro_popup, screen_id)
    key "K_BACKSPACE" action Function(close_intro_popup, screen_id)

screen random_event_choice(event_choices):
    modal True
    zorder 99
    
    default affected_building_info = ""
    
    on "show" action Function(get_affected_building_info)
    
    # Use the same style as standard Ren'Py choices (Lord/Lady format)
    style_prefix "choice"
    
    python:
        # Filter out choices with empty option to avoid blank slots in the UI
        display_choices = [c for c in event_choices if c.get("option") and str(c.get("option", "")).strip()]
    
    vbox:
        for choice in display_choices:
            if choice.get("_blocked", False):
                $ reason = choice.get("_blocked_reason", "Locked") or ""
                vbox:
                    spacing 2
                    textbutton "[choice['option']!q] (Locked)":
                        action NullAction()
                        sensitive False
                    if reason.strip():
                        text "[reason!q]" size font_size(20) color "#cc8888"
            else:
                textbutton "[choice['option']!q]" action Return(choice)

# --- NEW SCREEN START ---
screen choose_event_worker_screen(eligible_workers):
    modal True
    zorder 100
    
    python:
        # Apply Worker Gender filter so only matching workers are shown (no caller can forget)
        eligible_workers = workers_filtered_by_gender(eligible_workers)
        
        # Get the building name for the title
        building_type = ""
        building_name = ""
        specific_building = ""
        
        # If we have a specific affected building, use that
        if hasattr(store, "current_affected_building") and store.current_affected_building:
            specific_building = store.current_affected_building
            
            # Filter eligible workers to only those in the affected building
            eligible_workers = [w for w in eligible_workers if w.get("assigned_building") == specific_building]
            
            # Get the building info for display
            bld = available_buildings.get(specific_building, {})
            btype_id = bld.get("type")
            if btype_id:
                building_type = next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "")
                display_name = store.custom_names.get(specific_building, specific_building)
                building_name = f"{building_type}: {display_name}"
        # If no specific building, use first worker's building (original behavior)
        elif eligible_workers and len(eligible_workers) > 0:
            first_worker = eligible_workers[0]
            bld_name = first_worker.get("assigned_building", "Unassigned")
            if bld_name != "Unassigned" and bld_name in available_buildings:
                building = available_buildings[bld_name]
                btype_id = building.get("type")
                if btype_id:
                    building_type = next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "")
                    display_name = store.custom_names.get(bld_name, bld_name)
                    building_name = f"{building_type}: {display_name}"
        
        # Get the exact skill from the event condition
        condition_skill = None
        # Try to find the currently selected choice - in case this screen is called after a choice
        if hasattr(store, "chosen_choice_data") and store.chosen_choice_data:
            if "condition" in store.chosen_choice_data and store.chosen_choice_data["condition"] not in ["building_skill", None]:
                condition_skill = str(store.chosen_choice_data["condition"])
        
        # If we didn't find a skill in the chosen choice, check all choices in the event
        if not condition_skill and hasattr(store, "current_event") and store.current_event and "choices" in store.current_event:
            for choice in store.current_event["choices"]:
                if "condition" in choice and choice["condition"] not in ["building_skill", None]:
                    condition_skill = str(choice["condition"])
                    break
    
    # Background overlay
    add Solid(gui.surface_dark)
    
    # Main frame in the middle for worker selection
    frame:
        xalign 0.5  # Centered for wider panel
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))  # Journal background
        padding (40, 40)
        xsize 800  # Wider than journal to accommodate longer text
        ysize 720
        
        vbox:
            spacing 15
            null height 15  # Push title down like journal
            label (f"Choose a worker from {building_name}" if building_name else "Choose a worker for the event") xalign 0.5 style "header_style"
            null height 10  # Less space after title like journal
            
            vbox:
                xsize 720  # Wider content area
                spacing 10
                xoffset 50  # Moved 10px to the right
                yoffset 25
                
                if not eligible_workers:
                    text "No eligible workers found for this event." color "#ff0000" xalign 0.5 text_align 0.5 size 20
                    null height 20
                    textbutton "Continue":
                        xalign 0.5
                        xsize 200
                        text_size font_size(20)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                        action Return(None)
                else:
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        ysize 480  # Adjusted for journal layout
                        xsize 650  # Reduced to move scrollbar left
                        vbox:
                            spacing 10
                            for worker in eligible_workers:
                                # Only display skill value if we found a condition skill
                                if condition_skill:
                                    $ check_info = get_event_worker_skill_check_info(worker, store.chosen_choice_data)
                                    $ skill_label = check_info.get("label") or (str(skill_names.get(condition_skill, condition_skill)) + ": " + str(check_info.get("roll_skill", 0)))
                                    textbutton "[worker['name']!q] - [skill_label!q]":
                                        xsize 640  # Wider buttons for longer text
                                        text_size font_size(25)  # Increased by 5 points
                                        text_color gui.journal_text_color
                                        text_hover_color gui.journal_hover_color
                                        action Return(worker)
                                else:
                                    # Fallback if no condition skill found
                                    textbutton "[worker['name']!q]":
                                        xsize 640  # Wider buttons for longer text
                                        text_size font_size(25)  # Increased by 5 points
                                        text_color gui.journal_text_color
                                        text_hover_color gui.journal_hover_color
                                        action Return(worker)
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Return(None)
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    key "K_BACKSPACE" action Return(None)

screen recruitment_event_screen(event, worker):
    modal True
    zorder 98
    python:
        bg_name = event.get("background_image", "event_bg")
        if bg_name and not bg_name.startswith("images/"):
            if hasattr(store, bg_name):
                recruitment_bg = getattr(store, bg_name)
            else:
                recruitment_bg = f"images/{bg_name}.png"
        else:
            recruitment_bg = bg_name
        if not renpy.loadable(recruitment_bg):
            recruitment_bg = getattr(store, "event_bg", "images/event_bg.png")
        if not renpy.loadable(recruitment_bg):
            recruitment_bg = "images/event_bg.png"
    add recruitment_bg
    add Solid("#000000dd")
    
    $ comfort_level = worker.get("comfort_level", get_effective_comfort_desired(worker))
    $ daily_cost = int(comfort_level * get_difficulty_comfort_mult())
    
    $ description = event["description"].replace("[event_worker]", worker.get("name", "Unknown"))
    $ description = description.replace("[X]", "$" + str(daily_cost) + " (Comfort: " + str(comfort_level) + ")")
    $ description = description.replace("[acting_worker]", "Manager")

    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#1a1a1acc")
        padding (20, 20)
        vbox:
            spacing 15
            # !q so stray [..]/{..} in JSON event text can't crash interpolation (BIBLIA §9)
            text "[description!q]" size font_size(24) xalign 0.5 color "#ffffff"
            null height 20
            hbox:
                spacing 40
                xalign 0.5
                textbutton "Examine them":
                    action Return("examine")
                textbutton "Recruit them":
                    action Return("recruit")
                textbutton "Refuse them":
                    action Return("refuse")

screen recruitment_choice_screen(event_choices):
    modal True
    zorder 99
    

    
    # Use the same style as standard Ren'Py choices (same as regular events)
    style_prefix "choice"
    
    vbox:
        spacing 12
        
        # Main event choices with normal Ren'Py style
        for choice in event_choices:
            textbutton "[choice['option']!q]" action Return(choice)
        
        # Separator
        null height 20
        
        # Additional recruitment actions with normal choice style
        textbutton "*Examine Worker*" action [SetVariable("in_recruit_examine", True), Show("worker_details", worker=store.current_recruitment_worker, in_roster=False, from_recruitment=True)] sensitive (store.current_recruitment_worker is not None)

screen Building_select_global():
    zorder 3
    modal True
    add Solid(gui.surface_dark)

    # Ensure buildings are synced when opening this screen (once per show, not per render)
    on "show" action Function(_building_select_global_sync)

    frame:
        xalign 0.35  # Match journal positioning
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))  # Journal background
        padding (40, 40)
        xsize 720  # Match journal frame size
        ysize 720
        
        vbox:
            spacing 15
            null height 15  # Push title down like journal
            label "Manage Buildings" xalign 0.5 style "header_style"
            null height 10  # Less space after title like journal
            vbox:
                xsize 640  # Match journal content width
                spacing 10
                xoffset 30  # Match journal content offset
                yoffset 25
                
                viewport:
                    scrollbars "vertical"  # Keep scrollbar as requested
                    mousewheel True
                    draggable True
                    ysize 480  # Adjusted for journal layout
                    xsize 600   # Back to 600px
                    vbox:
                        spacing 10
                        # List all owned buildings (only those that exist in available_buildings)
                        for building in owned_buildings:
                            if building in available_buildings:
                                $ building_data = available_buildings[building]
                                $ btype_id = building_data.get("type")
                                $ type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                                $ parts = building.split('_')
                                $ default_name = f"Building {parts[1]}" if len(parts) > 1 else building
                                $ display_name = store.custom_names.get(building, default_name)
                                textbutton "[type_name]: [display_name]":
                                    xsize 580  # Keep button width same
                                    text_size font_size(26)  # Larger font like journal
                                    text_color gui.journal_text_color  # Brown text like journal
                                    text_hover_color gui.journal_hover_color  # Unified dark green hover
                                    action [Hide("tavern"), Hide("Building_select_global"), Show("Manager", building_name=building)]
        
        # Close button positioned like journal (outside vbox)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action [Hide("Building_select_global"), Show("tavern")]
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    key "K_BACKSPACE" action [Hide("Building_select_global"), Show("tavern")]

screen job_selection(worker):
    zorder 99
    modal True
    # Hover preview target (skills / bonus / estimated success of the hovered profession)
    default _job_tt_text = ""
    frame:
        xalign 0.5
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (40, 40)
        xsize 720
        ysize 720
        vbox:
            spacing 15
            null height 15
            label "ASSIGN ROLE" xalign 0.5 style "header_style"
            null height 10
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 480
                xsize 625
                xoffset -5
                yoffset -20
                vbox:
                    spacing 10
                    xsize 580
                    yoffset 25
                    $ building_name = worker.get("assigned_building", "Unassigned")
                    if building_name != "Unassigned":
                        $ building = available_buildings.get(building_name, {})
                    else:
                        $ building = None
                    
                    # If worker has no building assigned, show building selection first
                    if building is None:
                        text "{color=#7a4b2a}{size=20}Select a building first:{/size}{/color}":
                            xsize 500
                            xalign 0.0
                        null height 10
                        for b_name in store.owned_buildings:
                            $ b = available_buildings.get(b_name, {})
                            if b:
                                # !q: building display names are user-renamable (BIBLIA §9)
                                $ b_disp = b.get('display_name', b_name)
                                textbutton "[b_disp!q]":
                                    xsize 500
                                    text_size font_size(28)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    sensitive True
                                    action [
                                        Function(add_worker_to_building, worker, b_name),
                                        Hide("job_selection"),
                                        Show("job_selection", worker=worker)
                                    ]
                        null height 20
                        text "{color=#5a3a1a}{size=16}After selecting a building, you can assign a job.{/size}{/color}":
                            xsize 500
                            xalign 0.0
                    
                    # Universal Unassign option (available for all buildings)
                    if building is not None:
                        vbox:
                            spacing 2
                            textbutton "Unassign (No Role)":
                                xsize 500
                                text_size font_size(28)
                                text_color gui.journal_text_color
                                text_hover_color gui.journal_hover_color
                                sensitive True
                                action [
                                    # CRITICAL: Use function to set job, ensuring we modify the real dict
                                    Function(set_worker_job, worker, building_name, "unassigned"),
                                    # Clear autorest state when manually unassigning
                                    Function(clear_worker_autorest_state, worker),
                                    Hide("job_selection")
                                ]
                            text "{color=#000000}{size=18}No specific role assigned{/size}{/color}\n{size=16}{color=#7a4b2a}Worker will not participate in daily activities{/color}{/size}":
                                xsize 500
                                xalign 0.0
                                xoffset 5
                    
                    if building is not None and building.get("type") is not None:
                        $ btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == building["type"]), None)
                        if btype is not None:
                            # Filter professions based on NSFW toggle and required_flag gating
                            # (a profession with no required_flag is always shown — safe for all buildings)
                            for profession in [p for p in btype.get("professions", []) if (persistent.nsfw_enabled or not p.get("nsfw", False)) and profession_is_unlocked(p)]:
                                $ prof_name = profession.get("name", "Unnamed Profession")
                                $ prof_description = profession.get("description", "No description available.")
                                $ skills_used = profession.get("skills", [])
                                $ required_skills = ", ".join([skill_names.get(str(s), str(s)) for s in skills_used]) if skills_used else "None"  # Check for empty skills
                                python:
                                    total = 0
                                    count = 0
                                    _tt_skill_lines = []
                                    for s in skills_used:
                                        _sk_key = str(s)
                                        _sk_val = calculate_skill_with_traits(worker, _sk_key, include_libido=False)
                                        total += _sk_val
                                        count += 1
                                        # Skill display names are JSON-derived: escape text-tag/interp chars (BIBLIA §9)
                                        _sk_disp = str(skill_names.get(_sk_key, _sk_key)).replace("[", "[[").replace("{", "{{")
                                        _tt_skill_lines.append("{}: {}".format(_sk_disp, _sk_val))
                                    avg_skill = (total // count) if count > 0 else 0
                                    _is_rest_prof = str(profession.get("id", "")).strip().lower() == "rest"
                                    # Hover tooltip: per-skill values + building bonus + estimated daily success.
                                    # Mirrors the daily roll (event_daily_exec: d100 <= adjusted skill + building bonus),
                                    # labelled as an estimate (traits/story modifiers/synergy vary per day).
                                    _prof_success_tt = None
                                    if not _is_rest_prof:
                                        _b_skill_bonus = int(building.get("skill_bonus", 0) or 0) if building else 0
                                        _est_success = max(5, min(100, avg_skill + _b_skill_bonus))
                                        # Compact labels: rendered in the narrow fixed panel at top-right
                                        _tt_parts = list(_tt_skill_lines)
                                        if _b_skill_bonus:
                                            _tt_parts.append("Bonus: +{}".format(_b_skill_bonus))
                                        _tt_parts.append("Success: ~{}%".format(_est_success))
                                        _prof_success_tt = "\n".join(_tt_parts)
                                # For rest job, show "-" instead of skill value
                                $ avg_skill_display = "-" if _is_rest_prof else f"{avg_skill}/100"
                                # Count workers with this specific job - use servant_jobs as source of truth
                                # Only count if the worker actually exists and is assigned to this building
                                python:
                                    _current_count = 0
                                    _servant_jobs = building.get("servant_jobs", {})
                                    _prof_id_lc = str(profession.get("id", "")).strip().lower()
                                    for _wname, _job in _servant_jobs.items():
                                        if str(_job).strip().lower() == _prof_id_lc:
                                            # Verify worker exists and is assigned to this building
                                            _worker_exists = any(w.get("name") == _wname and w.get("assigned_building") == building_name for w in store.workers)
                                            if _worker_exists:
                                                _current_count += 1
                                    current_count = _current_count
                                $ max_limit = get_max_daily_workers(building, profession)
                                $ _mech_h = profession_mechanics_summary(profession)
                                $ _prof_blurb = prof_description + (("\n\n" + _mech_h) if _mech_h else "")
                                vbox:  # Wrap each profession entry in a vbox
                                    spacing 2  # Tight spacing between lines
                                    if current_count < max_limit:
                                        textbutton "[prof_name]":
                                            xsize 500  # Match shop_selection button width
                                            text_size font_size(28)
                                            text_color gui.journal_text_color
                                            text_hover_color gui.journal_hover_color
                                            sensitive True
                                            hovered SetScreenVariable("_job_tt_text", _prof_success_tt or "")
                                            unhovered SetScreenVariable("_job_tt_text", "")
                                            action [
                                                # Add worker to building with dedup protection
                                                Function(add_worker_to_building, worker, building_name),
                                                # CRITICAL: Use function to set job, ensuring we modify the real dict
                                                Function(set_worker_job, worker, building_name, profession["id"]),
                                                # Clear autorest state when manually changing profession
                                                Function(clear_worker_autorest_state, worker),
                                                # Auto-equip best items for new profession if worker has auto_equip on
                                                Function(run_worker_auto_equip, worker),
                                                # Always recalculate and check objectives when assigning workers during tutorial
                                                Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active else None),
                                                Hide("job_selection")
                                            ]
                                        vbox:
                                            spacing 16
                                            xsize 500
                                            xalign 0.0
                                            xoffset 5
                                            text "{size=20}{color=#7a4b2a}[_prof_blurb]{/color}{/size}":
                                                xsize 500
                                                xalign 0.0
                                            text "{color=#5a3a1a}{size=20}Skills Used: [required_skills]{/size}{/color}\n{size=17}{color=#6b6528}Average Skill: [avg_skill_display]{/color}{/size}":
                                                xsize 500
                                                xalign 0.0
                                    else:
                                        textbutton "[prof_name]":
                                            xsize 500  # Match shop_selection button width
                                            text_size font_size(28)
                                            text_color gui.journal_text_color
                                            text_hover_color gui.journal_hover_color
                                            sensitive False
                                        vbox:
                                            spacing 8
                                            xsize 500
                                            xalign 0.0
                                            xoffset 5
                                            text "{size=20}{color=#7a4b2a}[_prof_blurb]{/color}{/size}":
                                                xsize 500
                                                xalign 0.0
                                            text "{color=#5a3a1a}{size=20}Skills Used: [required_skills]{/size}{/color}\n{size=17}{color=#6b6528}Average Skill: [avg_skill_display]{/color}{/size}\n{size=17}{color=#ff0000}Role Full{/color}{/size}":
                                                xsize 500
                                                xalign 0.0
                        else:
                            text "No building type data found" size font_size(28) xalign 0.5
                    else:
                        text "No building assigned or building type not set" size font_size(28) xalign 0.5
        
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            # Close this modal and return to whatever screen opened it
            # (Manager, workers, etc.) instead of always jumping to workers.
            action Hide("job_selection")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    # Hover panel: profession preview (skills, bonus, estimated success).
    # X is fixed (left of the scrollbar, user-placed); Y follows the mouse,
    # clamped so the panel stays inside the journal frame. Styling mirrors the
    # generic tooltip screen exactly: dark 2px border, beige fill, size-20 text.
    if _job_tt_text:
        python:
            _job_tt_y = renpy.get_mouse_pos()[1]
            _job_tt_y = max(300, min(860, _job_tt_y))
        frame:
            xanchor 1.0
            yanchor 0.5
            xpos 1245
            ypos _job_tt_y
            xpadding 0
            ypadding 0
            background Solid(gui.journal_dark_color)  # Dark brown border
            frame:
                xmargin 2
                ymargin 2
                background Solid("#d4a574")  # Beige background (tooltip standard)
                xpadding 6
                ypadding 4
                text _job_tt_text:
                    size 20
                    color gui.journal_dark_color
                    text_align 0.0
                    xmaximum 185

    key "K_BACKSPACE" action Hide("job_selection")


screen manager_inventory(shop_mode=None, return_to_worker=None, return_to_in_roster=True, return_to_from_buy_workers=False, return_to_from_recruitment=False, return_to_tavern=False):
    if shop_mode is None:
        on "show" action Function(maybe_show_intro_popup, "storage")
    else:
        on "show" action Function(maybe_show_intro_popup, "shop_inventory")

    default selected_manager_item = None
    default selected_worker_item = None
    default selected_description = ""
    default selected_manager_index = None
    default selected_worker_index = None
    default is_transferring = False  # Debounce flag
    default left_panel_filter_category = None  # Independent filter for left panel
    default right_panel_filter_category = None  # Independent filter for right panel
    default show_test_items = False  # Toggle to show/hide test items
    default trade_multiplier = 1  # x1, x10, x100 for buy/sell/transfer
    default item_search_text = ""  # Search filter for items by name
    default left_sort_by_name = False  # False = arrival order, True = alphabetical
    default left_sort_by_price = False  # Left panel: price descending toggle
    default right_sort_by_name = False  # False = arrival order, True = alphabetical
    default right_shop_sort_by_price = False  # Right panel in shop: price descending toggle
    default quick_panel_mode = "stats"  # Compact worker panel: "stats" or "skills"
    default last_row_click_key = None
    default last_row_click_ts = 0.0

    python:
        def cycle_trade_multiplier():
            """Cycle through x1 -> x10 -> x100 -> x1"""
            current = renpy.get_screen_variable("trade_multiplier")
            if current == 1:
                renpy.set_screen_variable("trade_multiplier", 10)
            elif current == 10:
                renpy.set_screen_variable("trade_multiplier", 100)
            else:
                renpy.set_screen_variable("trade_multiplier", 1)
            renpy.restart_interaction()

        # _is_equipped is now defined at module level (init python) to avoid pickling issues

        def _set_left_row_selection(item, idx, item_info):
            renpy.set_screen_variable("selected_manager_item", item)
            renpy.set_screen_variable("selected_manager_index", idx)
            renpy.set_screen_variable("selected_worker_item", None)
            renpy.set_screen_variable("selected_worker_index", None)
            renpy.set_screen_variable("selected_description", item_info.get("description", ""))

        def _clear_row_selection():
            renpy.set_screen_variable("selected_manager_item", None)
            renpy.set_screen_variable("selected_manager_index", None)
            renpy.set_screen_variable("selected_worker_item", None)
            renpy.set_screen_variable("selected_worker_index", None)
            renpy.set_screen_variable("selected_description", "")

        def _set_right_worker_row_selection(item, idx, item_info):
            renpy.set_screen_variable("selected_worker_item", item)
            renpy.set_screen_variable("selected_worker_index", idx)
            renpy.set_screen_variable("selected_manager_item", None)
            renpy.set_screen_variable("selected_manager_index", None)
            renpy.set_screen_variable("selected_description", item_info.get("description", ""))

        def _set_right_shop_row_selection(item, item_info):
            renpy.set_screen_variable("selected_worker_item", item)
            renpy.set_screen_variable("selected_worker_index", None)
            renpy.set_screen_variable("selected_manager_item", None)
            renpy.set_screen_variable("selected_manager_index", None)
            renpy.set_screen_variable("selected_description", item_info.get("description", ""))

        # handle_inventory_row_click is defined AFTER sell_item / buy_item_from_shop /
        # transfer_to_left / transfer_to_right so it can capture them via default
        # arguments. Late-binding does NOT work here: defs inside a screen python:
        # block get __globals__ = renpy.store, NOT the screen-local scope, so sibling
        # names aren't visible at call time. Default args evaluate at def time and
        # bake in the references. See BIBLIA §8 for why we must not bridge via store.X.

        def _get_item_info_by_id(item_id):
            return next((i for i in items_json["items"] if i["id"] == item_id), None)

        def _get_canonical_worker_ref(worker):
            if not worker or worker is False:
                return None
            worker_name = worker.get("name", None) if hasattr(worker, "get") else None
            if worker_name:
                for w in store.workers:
                    if hasattr(w, "get") and w.get("name", None) == worker_name:
                        return w
            return worker

        def _get_equipped_item_id_for_types(inventory, slot_types):
            for slot_type in slot_types:
                for item in inventory:
                    if not item or len(item) < 2 or not store._is_equipped(item):
                        continue
                    item_info = _get_item_info_by_id(item[0])
                    if item_info and item_info.get("type") == slot_type:
                        return item[0]
            return None

        def _get_slot_candidate_item_ids(inventory, slot_types):
            candidate_ids = []
            for item in inventory:
                if not item or len(item) < 2:
                    continue
                item_id = item[0]
                if item_id in candidate_ids:
                    continue
                item_info = _get_item_info_by_id(item_id)
                if item_info and item_info.get("type") in slot_types:
                    candidate_ids.append(item_id)
            return candidate_ids

        def cycle_summary_equipment_slot(worker, slot_key, direction=1):
            def get_item_info_by_id(item_id):
                return next((i for i in items_json["items"] if i["id"] == item_id), None)

            def get_canonical_worker_ref(raw_worker):
                if not raw_worker or raw_worker is False:
                    return None
                worker_name = raw_worker.get("name", None) if hasattr(raw_worker, "get") else None
                if worker_name:
                    for w in store.workers:
                        if hasattr(w, "get") and w.get("name", None) == worker_name:
                            return w
                return raw_worker

            def get_equipped_item_id_for_types(inventory, slot_types):
                for slot_type in slot_types:
                    for item in inventory:
                        if not item or len(item) < 2 or not store._is_equipped(item):
                            continue
                        item_info = get_item_info_by_id(item[0])
                        if item_info and item_info.get("type") == slot_type:
                            return item[0]
                return None

            def get_slot_candidate_item_ids(inventory, slot_types):
                candidate_ids = []
                for item in inventory:
                    if not item or len(item) < 2:
                        continue
                    item_id = item[0]
                    if item_id in candidate_ids:
                        continue
                    item_info = get_item_info_by_id(item_id)
                    if item_info and item_info.get("type") in slot_types:
                        candidate_ids.append(item_id)
                return candidate_ids

            worker_ref = get_canonical_worker_ref(worker)
            if not worker_ref:
                return

            slot_types_map = {
                "weapon": ["weapon"],
                "body": ["armor", "clothing"],
                "accessory": ["accessory"],
            }
            slot_label_map = {
                "weapon": "Weapon",
                "body": "Clothing/Armor",
                "accessory": "Accessory",
            }
            slot_types = slot_types_map.get(slot_key, None)
            if not slot_types:
                return

            inventory = worker_ref.get("inventory", []) if hasattr(worker_ref, "get") else []
            options = [None] + get_slot_candidate_item_ids(inventory, slot_types)
            if len(options) <= 1:
                renpy.notify("{}: no available items".format(slot_label_map.get(slot_key, "Slot")))
                return

            current_item_id = get_equipped_item_id_for_types(inventory, slot_types)
            current_idx = options.index(current_item_id) if current_item_id in options else 0
            step = -1 if direction < 0 else 1
            next_idx = (current_idx + step) % len(options)
            next_item_id = options[next_idx]

            # Clear currently equipped entries in this slot family first.
            for idx, inv_item in enumerate(inventory):
                if not inv_item or len(inv_item) < 3 or not store._is_equipped(inv_item):
                    continue
                equipped_info = get_item_info_by_id(inv_item[0])
                if equipped_info and equipped_info.get("type") in slot_types:
                    inventory[idx] = (inv_item[0], inv_item[1], False)
                    remove_item_effects(worker_ref, inv_item[0])

            if next_item_id:
                equip_index = None
                for idx, inv_item in enumerate(inventory):
                    if not inv_item or len(inv_item) < 2:
                        continue
                    if str(inv_item[0]) == str(next_item_id):
                        equip_index = idx
                        break
                toggle_equip_item(inventory, next_item_id, worker=worker_ref, item_index=equip_index)
                next_info = get_item_info_by_id(next_item_id) or {}
                renpy.notify("{}: {}".format(slot_label_map.get(slot_key, "Slot"), next_info.get("name", "Equipped")))
            else:
                renpy.notify("{}: Empty".format(slot_label_map.get(slot_key, "Slot")))

            renpy.restart_interaction()
        
        def get_item_action_elements(item, item_info, worker, item_index=None):
            item_type = item_info.get("type", "unknown")
            is_equipped = item[2]
            label = "No Action"
            action = NullAction()
            sensitive = False
            bg = None

            if item_type == "consumable" and worker is not None and worker is not False:
                label = "Use"
                action = Function(lambda: use_item(item[0], worker))
                sensitive = True
            elif item_type not in ["consumable", "currency", "misc"] and worker is not None and worker is not False:
                sensitive = True
                if is_equipped:
                    label = "Unequip"
                else:
                    label = "Equip"
                action = Function(lambda: toggle_equip_item(worker.get("inventory", []), item[0], worker=worker, item_index=item_index))
            # "currency" and "misc" fall through to "No Action" by default

            return (label, action, sensitive, bg)

        def transfer_to_right():
            smi = renpy.get_screen_variable("selected_manager_item")
            smi_index = renpy.get_screen_variable("selected_manager_index")
            multiplier = renpy.get_screen_variable("trade_multiplier")
            if smi is not None and (right_worker is not False) and not renpy.get_screen_variable("is_transferring"):
                renpy.set_screen_variable("is_transferring", True)
                renpy.set_screen_variable("selected_manager_item", None)
                renpy.set_screen_variable("selected_manager_index", None)
                
                # CRITICAL: Create a fresh copy of smi to break any reference sharing
                # This ensures we're working with the actual item data, not a shared reference
                if _is_inv_entry(smi) and len(smi) >= 2:
                    smi = (str(smi[0]), int(smi[1]), bool(smi[2] if len(smi) > 2 else False))
                    renpy.log(f"transfer_to_right: Normalized smi to {smi}")
                
                # Ensure locals exist even when transferring to/from storage
                source_worker = None
                target_worker = None

                # Get references to the actual store inventories (not local copies)
                if left_worker is None:
                    source_inventory = store.manager_inventory
                else:
                    # Find the worker in store.workers and use their inventory
                    for w in store.workers:
                        if w.get("name") == left_worker.get("name"):
                            source_worker = w
                            break
                    if source_worker:
                        if "inventory" not in source_worker:
                            source_worker["inventory"] = []
                        source_inventory = source_worker["inventory"]
                    else:
                        source_inventory = left_worker.get("inventory", [])
                
                if right_worker is None:
                    target_inventory = store.manager_inventory
                else:
                    # Find the worker in store.workers and use their inventory
                    for w in store.workers:
                        if w.get("name") == right_worker.get("name"):
                            target_worker = w
                            break
                    if target_worker:
                        if "inventory" not in target_worker:
                            target_worker["inventory"] = []
                        target_inventory = target_worker["inventory"]
                    else:
                        target_inventory = right_worker.get("inventory", [])
                
                # Ensure smi reflects the exact selected index (avoid equality collisions)
                if smi_index is not None and smi_index < len(source_inventory):
                    try:
                        smi = source_inventory[smi_index]
                    except Exception:
                        pass

                renpy.log(f"Transfer to right: Left={left_worker['name'] if left_worker else 'Storage'}, Right={right_worker['name'] if right_worker else 'Storage'}, Source={source_inventory}, Target={target_inventory}, Item={smi}")
                if store._is_equipped(smi) and left_worker and left_worker is not False:
                    renpy.log(f"Unequipping selected copy of {smi[0]} from left worker")
                    # Prefer exact index match to avoid desequipping a different copy
                    did_unequip = False
                    if smi_index is not None and smi_index < len(source_inventory):
                        try:
                            inv_item = source_inventory[smi_index]
                            if _is_inv_entry(inv_item) and len(inv_item) >= 3 and str(inv_item[0]) == str(smi[0]):
                                source_inventory[smi_index] = (inv_item[0], inv_item[1], False)
                                if source_worker or left_worker:
                                    remove_item_effects(source_worker if source_worker else left_worker, inv_item[0])
                                did_unequip = True
                        except Exception:
                            pass
                    if not did_unequip:
                        unequip_item_by_match(
                            source_inventory,
                            smi[0],
                            quantity=smi[1],
                            worker=source_worker if source_worker else left_worker
                        )
                    # Keep smi consistent after unequip
                    smi = (str(smi[0]), int(smi[1]), False)
                # Calculate actual transfer quantity (limited by available)
                available_qty = smi[1]
                transfer_qty = min(multiplier, available_qty)
                item_info = next((i for i in items_json["items"] if i["id"] == smi[0]), None)
                is_gift_to_worker = bool(
                    item_info
                    and item_info.get("type") == "gift"
                    and left_worker is None
                    and target_worker
                )
                # Gifts are delivered one by one to workers.
                if is_gift_to_worker and transfer_qty > 1:
                    transfer_qty = 1
                renpy.log(f"transfer_to_right: Removing {smi[0]} (quantity: {transfer_qty}) from source")
                
                # Remove the exact selected entry when possible
                removed_exact = False
                if smi_index is not None:
                    removed_exact = remove_item_from_inventory_by_index(source_inventory, smi_index, quantity=transfer_qty)
                if not removed_exact:
                    # Fallback to id-based removal
                    remove_item_from_inventory(source_inventory, smi[0], quantity=transfer_qty)

                # If source is manager_inventory and we removed by index, refresh store list
                if left_worker is None and removed_exact:
                    store.manager_inventory = list(store.manager_inventory)
                    renpy.store.manager_inventory = store.manager_inventory
                
                # Verify the removal worked
                if left_worker is None:
                    # Double-check that the item was actually removed
                    remaining_count = sum(item[1] for item in store.manager_inventory if _is_inv_entry(item) and len(item) >= 2 and item[0] == smi[0])
                    renpy.log(f"transfer_to_right: After removal, {smi[0]} remaining in manager_inventory: {remaining_count}")
                renpy.log(f"Source after removal: {source_inventory}")
                renpy.log(f"Adding {smi[0]} (quantity: {transfer_qty}) to target: {target_inventory}")
                add_item_to_inventory(target_inventory, smi[0], quantity=transfer_qty)
                
                # Auto-consume on receive when item has auto_consume_on_receive and target is a worker
                try:
                    if target_worker and item_info and (item_info.get("auto_consume_on_receive", False) or is_gift_to_worker):
                        for _ in range(int(transfer_qty)):
                            store.use_item(smi[0], target_worker)
                except Exception as e:
                    renpy.log(f"auto_consume_on_receive error (to right): {e}")

                # CRITICAL: Force Ren'Py to recognize changes if target is manager_inventory
                if right_worker is None:
                    # Also recreate target inventory to break references
                    new_inv = []
                    for item in store.manager_inventory:
                        if _is_inv_entry(item) and len(item) >= 2:
                            new_inv.append((str(item[0]), int(item[1]), bool(item[2] if len(item) > 2 else False)))
                        else:
                            new_inv.append(item)
                    store.manager_inventory = new_inv
                    renpy.store.manager_inventory = store.manager_inventory
                renpy.log(f"Target after addition: {target_inventory}")
                store.selected_description = ""
                if is_gift_to_worker and target_worker:
                    renpy.notify(f"Gift delivered to {target_worker.get('name', 'worker')}")
                else:
                    renpy.notify(f"Transferred {transfer_qty}x item to right")
                # Track tutorial objective 5 - potion transfer
                if item_info and hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item_info.get("name", "").lower().find("energy") != -1:
                    store.potion_transferred = True
                    renpy.log("DEBUG: Tutorial - Energy potion transferred to worker")
                    renpy.log(f"DEBUG: Tutorial - Item name: {item_info.get('name', 'Unknown')}")
                    renpy.log(f"DEBUG: Tutorial - tutorial_active: {store.tutorial_active}, current_objective: {store.current_objective}")
                    try:
                        check_objective_completion()
                        renpy.log("DEBUG: Tutorial - check_objective_completion() called successfully")
                    except Exception as e:
                        renpy.log(f"DEBUG: Tutorial - Error calling check_objective_completion(): {e}")
                else:
                    renpy.log(f"DEBUG: Tutorial - Transfer conditions not met: tutorial_active={hasattr(store, 'tutorial_active')}, current_objective={store.current_objective if hasattr(store, 'current_objective') else 'NOT_SET'}, item_name={item_info.get('name', 'Unknown') if item_info else 'NO_ITEM_INFO'}")
                renpy.restart_interaction()
                renpy.set_screen_variable("is_transferring", False)

        def transfer_to_left():
            swi = renpy.get_screen_variable("selected_worker_item")
            swi_index = renpy.get_screen_variable("selected_worker_index")
            multiplier = renpy.get_screen_variable("trade_multiplier")
            if swi is not None and (left_worker is not False) and not renpy.get_screen_variable("is_transferring"):
                renpy.set_screen_variable("is_transferring", True)
                renpy.set_screen_variable("selected_worker_item", None)
                renpy.set_screen_variable("selected_worker_index", None)

                # Ensure locals exist even when transferring to/from storage
                source_worker = None
                target_worker = None
                
                # Get references to the actual store inventories (not local copies)
                if right_worker is None:
                    source_inventory = store.manager_inventory
                else:
                    # Find the worker in store.workers and use their inventory
                    for w in store.workers:
                        if w.get("name") == right_worker.get("name"):
                            source_worker = w
                            break
                    if source_worker:
                        if "inventory" not in source_worker:
                            source_worker["inventory"] = []
                        source_inventory = source_worker["inventory"]
                    else:
                        source_inventory = right_worker.get("inventory", [])
                
                if left_worker is None:
                    target_inventory = store.manager_inventory
                else:
                    # Find the worker in store.workers and use their inventory
                    for w in store.workers:
                        if w.get("name") == left_worker.get("name"):
                            target_worker = w
                            break
                    if target_worker:
                        if "inventory" not in target_worker:
                            target_worker["inventory"] = []
                        target_inventory = target_worker["inventory"]
                    else:
                        target_inventory = left_worker.get("inventory", [])
                
                # Ensure swi reflects the exact selected index (avoid equality collisions)
                if swi_index is not None and swi_index < len(source_inventory):
                    try:
                        swi = source_inventory[swi_index]
                    except Exception:
                        pass

                renpy.log(f"Transfer to left: Left={left_worker['name'] if left_worker else 'Storage'}, Right={right_worker['name'] if right_worker else 'Storage'}, Source={source_inventory}, Target={target_inventory}, Item={swi}")
                if store._is_equipped(swi) and right_worker and right_worker is not False:
                    renpy.log(f"Unequipping selected copy of {swi[0]} from right worker")
                    # Prefer exact index match to avoid desequipping a different copy
                    did_unequip = False
                    if swi_index is not None and swi_index < len(source_inventory):
                        try:
                            inv_item = source_inventory[swi_index]
                            if _is_inv_entry(inv_item) and len(inv_item) >= 3 and str(inv_item[0]) == str(swi[0]):
                                source_inventory[swi_index] = (inv_item[0], inv_item[1], False)
                                if source_worker or right_worker:
                                    remove_item_effects(source_worker if source_worker else right_worker, inv_item[0])
                                did_unequip = True
                        except Exception:
                            pass
                    if not did_unequip:
                        unequip_item_by_match(
                            source_inventory,
                            swi[0],
                            quantity=swi[1],
                            worker=source_worker if source_worker else right_worker
                        )
                    # Keep swi consistent after unequip
                    swi = (str(swi[0]), int(swi[1]), False)
                # Calculate actual transfer quantity (limited by available)
                available_qty = swi[1]
                transfer_qty = min(multiplier, available_qty)
                item_info = next((i for i in items_json["items"] if i["id"] == swi[0]), None)
                is_gift_to_worker = bool(
                    item_info
                    and item_info.get("type") == "gift"
                    and right_worker is None
                    and target_worker
                )
                # Gifts are delivered one by one to workers.
                if is_gift_to_worker and transfer_qty > 1:
                    transfer_qty = 1
                renpy.log(f"transfer_to_left: Removing {swi[0]} (quantity: {transfer_qty}) from source")
                
                # Remove the exact selected entry when possible
                removed_exact = False
                if swi_index is not None:
                    removed_exact = remove_item_from_inventory_by_index(source_inventory, swi_index, quantity=transfer_qty)
                if not removed_exact:
                    # Fallback to id-based removal
                    remove_item_from_inventory(source_inventory, swi[0], quantity=transfer_qty)

                # If source is manager_inventory and we removed by index, refresh store list
                if right_worker is None and removed_exact:
                    store.manager_inventory = list(store.manager_inventory)
                    renpy.store.manager_inventory = store.manager_inventory
                
                # Verify the removal worked
                if right_worker is None:
                    # Double-check that the item was actually removed
                    remaining_count = sum(item[1] for item in store.manager_inventory if _is_inv_entry(item) and len(item) >= 2 and item[0] == swi[0])
                    renpy.log(f"transfer_to_left: After removal, {swi[0]} remaining in manager_inventory: {remaining_count}")
                renpy.log(f"Source after removal: {source_inventory}")
                renpy.log(f"Adding {swi[0]} (quantity: {transfer_qty}) to target: {target_inventory}")
                add_item_to_inventory(target_inventory, swi[0], quantity=transfer_qty)
                
                # Auto-consume on receive when item has auto_consume_on_receive and target is a worker
                try:
                    if target_worker and item_info and (item_info.get("auto_consume_on_receive", False) or is_gift_to_worker):
                        for _ in range(int(transfer_qty)):
                            store.use_item(swi[0], target_worker)
                except Exception as e:
                    renpy.log(f"auto_consume_on_receive error (to left): {e}")

                # CRITICAL: Force Ren'Py to recognize changes if target is manager_inventory
                if left_worker is None:
                    # Also recreate target inventory to break references
                    new_inv = []
                    for item in store.manager_inventory:
                        if _is_inv_entry(item) and len(item) >= 2:
                            new_inv.append((str(item[0]), int(item[1]), bool(item[2] if len(item) > 2 else False)))
                        else:
                            new_inv.append(item)
                    store.manager_inventory = new_inv
                    renpy.store.manager_inventory = store.manager_inventory
                renpy.log(f"Target after addition: {target_inventory}")
                store.selected_description = ""
                if is_gift_to_worker and target_worker:
                    renpy.notify(f"Gift delivered to {target_worker.get('name', 'worker')}")
                else:
                    renpy.notify(f"Transferred {transfer_qty}x item to left")
                # Track tutorial objective 5 - potion transfer
                if item_info and hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item_info.get("name", "").lower().find("energy") != -1:
                    store.potion_transferred = True
                    renpy.log("DEBUG: Tutorial - Energy potion transferred to worker")
                    check_objective_completion()
                renpy.restart_interaction()
                renpy.set_screen_variable("is_transferring", False)

        def get_item_sell_price(item_info):
            """Single source for shop sell pricing: 50% of buy price (shared by
            sell_item and the mass-sell plan builders below)."""
            return int((item_info or {}).get("price", 0) * 0.5)

        def sell_item(item_id, quantity=None, _price=get_item_sell_price):
            # _price captured via default arg: screen-local defs can't see sibling
            # screen locals at call time (BIBLIA §10 / note above handle_inventory_row_click).
            multiplier = renpy.get_screen_variable("trade_multiplier")
            item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
            if item_info:
                sell_price = _price(item_info)  # 50% of buy price
                source_inventory = manager_inventory if left_worker is None else left_worker.get("inventory", [])
                # Find item in inventory to check available quantity
                item_entry = next((item for item in source_inventory if item[0] == item_id), None)
                available_qty = item_entry[1] if item_entry else 0
                # Calculate actual sell quantity (limited by available)
                actual_qty = min(multiplier if quantity is None else quantity, available_qty)
                if actual_qty > 0:
                    store.money += sell_price * actual_qty
                    remove_item_from_inventory(source_inventory, item_id, actual_qty)
                    renpy.notify(f"Sold {actual_qty}x {item_info.get('name', 'Unknown')} for ${sell_price * actual_qty}")
                renpy.restart_interaction()

        def buy_item_from_shop(item_id):
            multiplier = renpy.get_screen_variable("trade_multiplier")
            item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
            if item_info:
                price = item_info.get("price", 0)
                consume_on_purchase = item_info.get("consume_on_purchase", False)
                purchase_effect = item_info.get("purchase_effect", "")
                # Consume-on-purchase: only buy 1 at a time and apply effect instead of adding to inventory
                if consume_on_purchase:
                    actual_qty = min(1, store.money // price if price > 0 else 1)
                else:
                    max_affordable = store.money // price if price > 0 else multiplier
                    actual_qty = min(multiplier, max_affordable)
                if actual_qty > 0 and store.money >= price * actual_qty:
                    store.money -= price * actual_qty
                    if consume_on_purchase:
                        if purchase_effect == "manager_level_up":
                            for _ in range(actual_qty):
                                store.manager_level = getattr(store, "manager_level", 1) + 1
                            renpy.notify(f"Manager Level up! (consumed {actual_qty}x {item_info.get('name', 'Unknown')})")
                        elif purchase_effect == "add_money":
                            money_per_item = int(item_info.get("effect", {}).get("money", 0))
                            total_added = money_per_item * actual_qty
                            store.money += total_added
                            renpy.notify(f"+${total_added} (consumed {actual_qty}x {item_info.get('name', 'Unknown')})")
                        elif purchase_effect == "custom":
                            custom_effect = item_info.get("effect", {})
                            for _ in range(actual_qty):
                                apply_effects({"custom": custom_effect.get("custom")}, worker=None)
                            renpy.notify(f"Applied effect (consumed {actual_qty}x {item_info.get('name', 'Unknown')})")
                        else:
                            renpy.notify(f"Consumed {actual_qty}x {item_info.get('name', 'Unknown')}")
                    else:
                        for _ in range(actual_qty):
                            add_item_to_inventory(manager_inventory, item_id)
                        renpy.notify(f"Bought {actual_qty}x {item_info.get('name', 'Unknown')} for ${price * actual_qty}")
                    # Track tutorial objective 5 - potion purchase
                    if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item_info.get("name", "").lower().find("energy") != -1:
                        store.potion_purchased = True
                        renpy.log("DEBUG: Tutorial - Energy potion purchased")
                        renpy.log(f"DEBUG: Tutorial - Item name: {item_info.get('name', 'Unknown')}")
                        renpy.log(f"DEBUG: Tutorial - tutorial_active: {store.tutorial_active}, current_objective: {store.current_objective}")
                        renpy.log(f"DEBUG: Tutorial - potion_purchased set to: {store.potion_purchased}")
                        check_objective_completion()
                    else:
                        renpy.log(f"DEBUG: Tutorial - Purchase conditions not met: tutorial_active={hasattr(store, 'tutorial_active')}, current_objective={store.current_objective if hasattr(store, 'current_objective') else 'NOT_SET'}, item_name={item_info.get('name', 'Unknown')}")
                renpy.restart_interaction()

        def handle_inventory_row_click(row_scope, row_idx, item, item_info, is_shop_mode=False, can_transfer_right=True, can_transfer_left=True,
                                       _sell=sell_item, _buy=buy_item_from_shop, _to_right=transfer_to_right, _to_left=transfer_to_left):
            # Helpers (_sell/_buy/_to_right/_to_left) are captured via default args
            # so they're bound at def time. See note above this def for why.
            def set_left_row_selection():
                renpy.set_screen_variable("selected_manager_item", item)
                renpy.set_screen_variable("selected_manager_index", row_idx)
                renpy.set_screen_variable("selected_worker_item", None)
                renpy.set_screen_variable("selected_worker_index", None)
                renpy.set_screen_variable("selected_description", item_info.get("description", ""))

            def clear_row_selection():
                renpy.set_screen_variable("selected_manager_item", None)
                renpy.set_screen_variable("selected_manager_index", None)
                renpy.set_screen_variable("selected_worker_item", None)
                renpy.set_screen_variable("selected_worker_index", None)
                renpy.set_screen_variable("selected_description", "")

            def set_right_worker_row_selection():
                renpy.set_screen_variable("selected_worker_item", item)
                renpy.set_screen_variable("selected_worker_index", row_idx)
                renpy.set_screen_variable("selected_manager_item", None)
                renpy.set_screen_variable("selected_manager_index", None)
                renpy.set_screen_variable("selected_description", item_info.get("description", ""))

            def set_right_shop_row_selection():
                renpy.set_screen_variable("selected_worker_item", item)
                renpy.set_screen_variable("selected_worker_index", None)
                renpy.set_screen_variable("selected_manager_item", None)
                renpy.set_screen_variable("selected_manager_index", None)
                renpy.set_screen_variable("selected_description", item_info.get("description", ""))

            now = __import__("time").time()
            item_id = item[0] if _is_inv_entry(item) and len(item) >= 1 else str(item)
            row_key = "{}:{}:{}".format(row_scope, row_idx, item_id)
            last_key = renpy.get_screen_variable("last_row_click_key")
            last_ts = renpy.get_screen_variable("last_row_click_ts")
            is_double = (last_key == row_key) and ((now - float(last_ts or 0.0)) <= 0.32)

            if row_scope == "left":
                current_idx = renpy.get_screen_variable("selected_manager_index")
                if is_double:
                    set_left_row_selection()
                    if not renpy.get_screen_variable("is_transferring"):
                        if is_shop_mode:
                            _sell(item_id)
                        elif can_transfer_right:
                            _to_right()
                    renpy.set_screen_variable("last_row_click_key", None)
                    renpy.set_screen_variable("last_row_click_ts", 0.0)
                    return
                if current_idx != row_idx:
                    set_left_row_selection()

            elif row_scope == "right_worker":
                current_idx = renpy.get_screen_variable("selected_worker_index")
                if is_double:
                    set_right_worker_row_selection()
                    if can_transfer_left and (not renpy.get_screen_variable("is_transferring")):
                        _to_left()
                    renpy.set_screen_variable("last_row_click_key", None)
                    renpy.set_screen_variable("last_row_click_ts", 0.0)
                    return
                if current_idx != row_idx:
                    set_right_worker_row_selection()

            elif row_scope == "right_shop":
                current_item = renpy.get_screen_variable("selected_worker_item")
                if is_double:
                    set_right_shop_row_selection()
                    if (not renpy.get_screen_variable("is_transferring")) and store.money >= item_info.get("price", 0):
                        _buy(item_id)
                    renpy.set_screen_variable("last_row_click_key", None)
                    renpy.set_screen_variable("last_row_click_ts", 0.0)
                    return
                if current_item != item:
                    set_right_shop_row_selection()

            renpy.set_screen_variable("last_row_click_key", row_key)
            renpy.set_screen_variable("last_row_click_ts", now)

        # NOTE: do NOT add `store.foo = local_fn` lines here.
        # That assignment poisons Ren'Py's rollback log permanently
        # (the delta captures the local function, and pickle of the rollback
        # log fails on save). See docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md §8.
        # Function(local_fn, ...) in screen Actions IS safe because the
        # displayable tree is rebuilt on load, not pickled with rollback.

    modal True
    zorder 99
    tag manager_inventory

    # Dynamic background based on shop_mode (adjusted to 1515px width to account for side panel)
    add get_inventory_bg(shop_mode):
        xsize 1515
        ysize 1080
        xalign 0.0
        yalign 0.0
    # Decorative context background strip (same asset used in Tavern/Map)
    add context_menu_bg xalign 0.5 yalign 0.5

    # Money and Date positioned over context menu area (top-right)
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        # Money display with icon-style $ symbol
        hbox:
            spacing 5
            text "$" color gui.journal_dark_color size 24 bold True yalign 0.5
            text "[format(int(money), ',')]" color gui.journal_dark_color size 28 yalign 0.5
        # Calendar display with icon
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]
            $ month_name = month_names[store.current_month - 1]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color gui.journal_dark_color size 26 yalign 0.5
        # Compact status strip: roster size and owned holdings (read-only)
        python:
            _tv_worker_count = len(store.workers)
            _tv_building_count = len(getattr(store, "owned_buildings", []) or [])
        text "Workers: [_tv_worker_count]      Buildings: [_tv_building_count]" color gui.journal_dark_color size 20
        # Player title and name (click to open character sheet) — blink when pending skill points
        if manager_has_unspent_skill_points():
            timer 0.7 repeat True action ToggleVariable("manager_name_blink_highlight")
        python:
            _manager_name_color = gui.journal_hover_color if (getattr(store, 'manager_name_blink_highlight', False) and manager_has_unspent_skill_points()) else gui.journal_dark_color
        textbutton "[player_title] [player_name]":
            action Show("manager_character_sheet")
            text_color _manager_name_color
            text_hover_color gui.journal_hover_color
            text_size 26
            text_italic True
            background None
            hover_background None

    # Toggle button for test items (discrete, bottom-right)
    if shop_mode:
        button:
            xpos 1615
            ypos 260
            xsize 140
            ysize 30
            background Solid("#3c1f14cc")
            hover_background Solid("#3c1f14ee")
            text "Toggle test items" size font_size(16) color "#ffffff" hover_color "#ffffff" xalign 0.5 yalign 0.5
            action ToggleScreenVariable("show_test_items")
            tooltip "Toggle test items visibility"

    # Left dim panel matching Manage Building width (stops at right strip)
    frame:
        xalign 0.0
        yalign 1.0
        xsize 1511
        ysize 560
        background Solid("#1a1a1acc")
        padding (20, 20)

    # (Context menu moved to bottom of screen so it renders on top of other panels)

    frame:
        xalign 0.0
        yalign 0.9
        yoffset 105
        xsize 1511
        ysize 600
        background None

        hbox:
            spacing 20
            xalign 0.5
            yalign 0.0

            frame:
                xsize 540
                xoffset 10
                ysize 540
                background Solid("#1a1a1acc")
                padding (10, 10)
                vbox:
                    spacing 5
                    button:
                        background "images/tablebutton.png"
                        xsize 500
                        ysize 50
                        hbox:
                            xalign 0.5
                            yalign 0.5
                            spacing 10
                            text "{size=32}[left_worker['name'] if left_worker and left_worker is not False else ('Storage' if left_worker is None else 'None')]{/size}" color "#ffffff" yalign 0.5
                            if not shop_mode:
                                text "{size=18}(click to change){/size}" color "#ffffff" yalign 0.5
                        action If(not shop_mode, 
                            Show("worker_selection_popup", panel="left", current_left=left_worker, current_right=right_worker, shop_mode=shop_mode),
                            None
                        )
                        sensitive (not shop_mode)
                        hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Left panel source. Click to select which worker or storage is on the left side.", screen_name="manager_inventory"), NullAction())
                        unhovered Hide("tooltip")
                    python:
                        _cat_names = {
                            "weapon": "Weapons",
                            "armor": "Armor",
                            "clothing": "Clothing",
                            "accessory": "Accessories",
                            "consumable": "Consumables",
                            "gifts": "Gifts",
                            "currency": "Currency",
                            "quest_item": "Quest Items",
                            "misc": "Misc"
                        }
                        _left_cat_label = "All Items" if left_panel_filter_category is None else _cat_names.get(left_panel_filter_category, str(left_panel_filter_category).replace("_", " ").title())
                    textbutton "Filter: [_left_cat_label]":
                        action Show("inventory_filter_popup", target_var="left_panel_filter_category", current_cat=left_panel_filter_category, popup_title="FILTER LEFT PANEL")
                        xsize 500
                        ysize 40
                        text_size 30
                        text_color "#d8bf9a"
                        text_hover_color "#ffffff"
                        background "images/tablebutton.png"
                    hbox:
                        spacing 0
                        button:
                            background "images/tablebutton.png"
                            xsize 200
                            ysize 40
                            action If(
                                left_sort_by_name,
                                [SetScreenVariable("left_sort_by_name", False)],
                                [SetScreenVariable("left_sort_by_name", True), SetScreenVariable("left_sort_by_price", False)]
                            )
                            hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Sort left panel by name. Toggle between alphabetical and arrival order.", screen_name="manager_inventory"), NullAction())
                            unhovered Hide("tooltip")
                            hbox:
                                spacing 3
                                yalign 0.5
                                text "Name" size font_size(22) yalign 0.5 yoffset 3 color "#ffffff" hover_color gui.journal_hover_color
                                if left_sort_by_name:
                                    add "gui/arrowdown.png" zoom 0.1 yalign 0.5
                        button:
                            background "images/tablebutton.png"
                            xsize 90
                            ysize 40
                            action If(
                                left_sort_by_price,
                                [SetScreenVariable("left_sort_by_price", False)],
                                [SetScreenVariable("left_sort_by_price", True), SetScreenVariable("left_sort_by_name", False)]
                            )
                            hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Sort left panel by price. Toggle price ranking on or off.", screen_name="manager_inventory"), NullAction())
                            unhovered Hide("tooltip")
                            hbox:
                                spacing 3
                                yalign 0.5
                                text "Price" size font_size(22) xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff" hover_color gui.journal_hover_color
                                if left_sort_by_price:
                                    add "gui/arrowdown.png" zoom 0.1 yalign 0.5
                        button:
                            background "images/tablebutton.png"
                            xsize 90
                            ysize 40
                            text "Qty" size font_size(22) xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                            action None
                        button:
                            background None
                            padding (0, 0, 0, 0)
                            xsize 140
                            ysize 40
                            $ header_action = "Sell" if shop_mode else "Trade"
                            text "[header_action]" size font_size(22) xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                            action None
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        xsize 500
                        ysize 395
                        vbox:
                            spacing 5
                            xoffset 5
                            $ left_inventory = [] if left_worker is False else (manager_inventory if left_worker is None else left_worker.get("inventory", []))
                            # Sort and filter items - alphabetically or by arrival order based on toggle
                            python:
                                def get_item_name_for_sort(idx_item):
                                    item = idx_item[1]
                                    item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                    return item_info.get("name", "ZZZ").lower()
                                
                                def get_item_price_for_sort(idx_item):
                                    item = idx_item[1]
                                    item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                    return int(item_info.get("price", 0))
                                
                                def item_matches_search(idx_item, search_text, category_filter=None):
                                    item = idx_item[1]
                                    item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                    if category_filter is not None:
                                        if category_filter == "gifts":
                                            _gift_ids = set(getattr(store, "YVARA_GIFTS", {}).keys())
                                            _gift_ids -= {"diamond", "ruby", "emerald", "sapphire"}
                                            if item[0] not in _gift_ids:
                                                return False
                                        elif item_info.get("type") != category_filter:
                                            return False
                                    if not search_text:
                                        return True
                                    item_name = item_info.get("name", "").lower()
                                    return search_text.lower() in item_name
                                
                                search_text = item_search_text if item_search_text else ""
                                category_filter = left_panel_filter_category
                                # Filter items first
                                equipped_list = [(idx, item) for idx, item in enumerate(left_inventory) if store._is_equipped(item) and item_matches_search((idx, item), search_text, category_filter)]
                                unequipped_list = [(idx, item) for idx, item in enumerate(left_inventory) if not store._is_equipped(item) and item_matches_search((idx, item), search_text, category_filter)]
                                # Sort by selected mode, or keep arrival order
                                if left_sort_by_price:
                                    equipped_items = sorted(
                                        equipped_list,
                                        key=lambda x: (
                                            -int(next((i for i in items_json["items"] if i["id"] == x[1][0]), {}).get("price", 0)),
                                            next((i for i in items_json["items"] if i["id"] == x[1][0]), {}).get("name", "ZZZ").lower(),
                                        ),
                                    )
                                    unequipped_items = sorted(
                                        unequipped_list,
                                        key=lambda x: (
                                            -int(next((i for i in items_json["items"] if i["id"] == x[1][0]), {}).get("price", 0)),
                                            next((i for i in items_json["items"] if i["id"] == x[1][0]), {}).get("name", "ZZZ").lower(),
                                        ),
                                    )
                                elif left_sort_by_name:
                                    equipped_items = sorted(equipped_list, key=get_item_name_for_sort)
                                    unequipped_items = sorted(unequipped_list, key=get_item_name_for_sort)
                                else:
                                    equipped_items = equipped_list  # Keep original order (arrival)
                                    unequipped_items = unequipped_list

                            for idx, item in equipped_items:
                                $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                $ _item_name = item_info.get("name", "Unknown")
                                $ _item_name_display = _item_name[:15] + "..." if len(_item_name) > 17 else _item_name
                                $ bg_button = Solid("#d4a574")
                                button:
                                    background bg_button
                                    xsize 520
                                    ysize 40
                                    padding (0, 0, 0, 0)
                                    hover_background Solid("#c0c0c0cc")
                                    action Function(handle_inventory_row_click, "left", idx, item, item_info, bool(shop_mode), (right_worker is not False), False)
                                    hbox:
                                        spacing 0
                                        frame:
                                            xsize 200
                                            background None
                                            text ("{b}" + _item_name_display + "{/b}" if selected_manager_index == idx else _item_name_display) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text "${}".format(item_info.get("price", 0)) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text str(item[1]) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                        button:
                                            style "inv_trade_action_button"
                                            xsize 140
                                            background None
                                            text ("{u}Sell{/u}" if shop_mode else "{u}Right{/u}") size font_size(24) hover_color gui.journal_hover_color xalign 0.0 yalign 0.5 yoffset 3
                                            action [SetScreenVariable("selected_manager_item", item), SetScreenVariable("selected_manager_index", idx), SetScreenVariable("selected_worker_item", None), SetScreenVariable("selected_worker_index", None), SetScreenVariable("selected_description", item_info.get("description", "")), Function(sell_item, item[0]) if shop_mode else Function(transfer_to_right)]
                                            sensitive ((right_worker is not False or shop_mode) and not is_transferring)
                                            hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message=("Sell selected item to shop. Double-click row for quick sell." if shop_mode else "Move selected item to the right panel target. Double-click row for quick transfer."), screen_name="manager_inventory"), NullAction())
                                            unhovered Hide("tooltip")

                            for i, idx_item in enumerate(unequipped_items):
                                $ idx, item = idx_item
                                $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                $ _item_name = item_info.get("name", "Unknown")
                                $ _item_name_display = _item_name[:15] + "..." if len(_item_name) > 17 else _item_name
                                $ bg_button = Solid("#777777") if i % 2 == 0 else Solid("#555555")
                                button:
                                    background bg_button
                                    xsize 520
                                    ysize 40
                                    padding (0, 0, 0, 0)
                                    hover_background Solid("#c0c0c0cc")
                                    action Function(handle_inventory_row_click, "left", idx, item, item_info, bool(shop_mode), (right_worker is not False), False)
                                    hbox:
                                        spacing 0
                                        frame:
                                            xsize 200
                                            background None
                                            text ("{b}" + _item_name_display + "{/b}" if selected_manager_index == idx else _item_name_display) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text "${}".format(item_info.get("price", 0)) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text str(item[1]) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                        button:
                                            style "inv_trade_action_button"
                                            xsize 140
                                            background None
                                            text ("{u}Sell{/u}" if shop_mode else "{u}Right{/u}") size font_size(24) hover_color gui.journal_hover_color xalign 0.0 yalign 0.5 yoffset 3
                                            action [SetScreenVariable("selected_manager_item", item), SetScreenVariable("selected_manager_index", idx), SetScreenVariable("selected_worker_item", None), SetScreenVariable("selected_worker_index", None), SetScreenVariable("selected_description", item_info.get("description", "")), Function(sell_item, item[0]) if shop_mode else Function(transfer_to_right)]
                                            sensitive ((right_worker is not False or shop_mode) and not is_transferring)
                                            hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message=("Sell selected item to shop. Double-click row for quick sell." if shop_mode else "Move selected item to the right panel target. Double-click row for quick transfer."), screen_name="manager_inventory"), NullAction())
                                            unhovered Hide("tooltip")

            frame:
                xsize 380
                ysize 540
                yoffset 0
                background Solid("#444444cc")
                padding (10, 5, 10, 10)
                vbox:
                    yoffset 0
                    spacing 0
                    null height 5
                    # Search field (moved from context menu to central column)
                    hbox:
                        xalign 0.5
                        xsize 360
                        spacing 0
                        button:
                            xsize 86
                            ysize 30
                            background Solid("#c7aa7f")
                            hover_background Solid("#c7aa7f")
                            padding (8, 4)
                            action NullAction()
                            hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Search items by name across visible panel lists.", screen_name="manager_inventory"), NullAction())
                            unhovered Hide("tooltip")
                            text "Search" color gui.journal_dark_color size font_size(20) xalign 0.0 yalign 0.5
                        frame:
                            xsize 274
                            ysize 30
                            background Solid("#d8bf9a")
                            padding (8, 4)
                            input:
                                value ScreenVariableInputValue("item_search_text")
                                pixel_width 254
                                size font_size(20)
                                color gui.journal_dark_color
                                allow "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -'"
                    null height 5
                    # Multiplier button (x1 / x10 / x100)
                    button:
                        background Solid(gui.journal_dark_color)
                        hover_background Solid("#5a3a2a")
                        xsize 360
                        ysize 40
                        yoffset 0
                        action Function(cycle_trade_multiplier)
                        hbox:
                            xalign 0.5
                            yalign 0.5
                            spacing 10
                            text "Quantity:" size font_size(22) color "#ffffff" yalign 0.5
                            text "x[trade_multiplier]" size font_size(24) color "#ffffff" yalign 0.5
                            text "(click to cycle)" size font_size(20) color "#aaaaaa" yalign 0.5
                    if shop_mode:
                        # Mass-sell tools (Sell stack / Sell shown / Sell duplicates).
                        # GEOMETRY: middle panel is 380x540, padding (10,5,10,10) -> 525px of
                        # content. Base layout used exactly 525 (5+30+5+40+5+200+5+235), so this
                        # 35px row (null 5 + hbox 30) is paid for by shrinking the description
                        # frame 200->165 (viewport 180->145) in shop mode only.
                        #
                        # Plans are computed at render time from the same filtered lists the left
                        # panel just rendered (equipped entries never enter unequipped_list); any
                        # inventory change restarts the interaction, so plans match the screen.
                        python:
                            _bulk_items_by_id = {it.get("id"): it for it in items_json.get("items", [])}

                            def _bulk_sellable(_item_id, _info):
                                if (_info or {}).get("type") == "quest_item":
                                    return False
                                _idl = str(_item_id).lower()
                                if "test" in _idl or "debug" in _idl:
                                    return False
                                return True

                            _bulk_worker_name = left_worker.get("name") if (left_worker and left_worker is not False) else None

                            # Sell stack: every unequipped copy of the selected item (whole inventory).
                            _stack_plan = []
                            _stk_name_esc = "item"
                            if selected_manager_item is not None:
                                _stk_id = str(selected_manager_item[0])
                                _stk_info = _bulk_items_by_id.get(selected_manager_item[0], {})
                                if _bulk_sellable(_stk_id, _stk_info):
                                    _stk_qty = 0
                                    for _bit in left_inventory:
                                        if _is_inv_entry(_bit) and len(_bit) >= 2 and str(_bit[0]) == _stk_id and not store._is_equipped(_bit):
                                            _stk_qty += int(_bit[1] or 0)
                                    if _stk_qty > 0:
                                        _stack_plan = [(_stk_id, _stk_qty, get_item_sell_price(_stk_info))]
                                # Item names are JSON-derived: escape text-tag/interp chars (BIBLIA §9)
                                _stk_name_esc = str(_stk_info.get("name", "item")).replace("[", "[[").replace("{", "{{")

                            # Sell shown: everything passing the active filter+search (unequipped only).
                            _shown_qty_by_id = {}
                            for _sidx, _sitem in unequipped_list:
                                if not (_is_inv_entry(_sitem) and len(_sitem) >= 2):
                                    continue
                                _sid = str(_sitem[0])
                                if not _bulk_sellable(_sid, _bulk_items_by_id.get(_sitem[0], {})):
                                    continue
                                _shown_qty_by_id[_sid] = _shown_qty_by_id.get(_sid, 0) + int(_sitem[1] or 0)
                            _shown_plan = [(_sid, _q, get_item_sell_price(_bulk_items_by_id.get(_sid, {}))) for _sid, _q in _shown_qty_by_id.items() if _q > 0]

                            # Sell duplicates: keep 1 copy of each distinct shown item, sell the rest.
                            _dupes_plan = [(_sid, _q - 1, get_item_sell_price(_bulk_items_by_id.get(_sid, {}))) for _sid, _q in _shown_qty_by_id.items() if _q > 1]

                            def _bulk_totals(_plan):
                                return (sum(_p[1] for _p in _plan), sum(_p[1] * _p[2] for _p in _plan))

                            _stack_n, _stack_gold = _bulk_totals(_stack_plan)
                            _shown_n, _shown_gold = _bulk_totals(_shown_plan)
                            _dupes_n, _dupes_gold = _bulk_totals(_dupes_plan)
                        null height 5
                        hbox:
                            xsize 360
                            spacing 6
                            button:
                                xsize 116
                                ysize 30
                                background Solid(gui.journal_dark_color)
                                hover_background Solid("#5a3a2a")
                                sensitive (bool(_stack_plan) and not is_transferring)
                                action Confirm("Sell all {}x {} for ${}?".format(_stack_n, _stk_name_esc, _stack_gold), Function(mass_sell_inventory_items, _stack_plan, _bulk_worker_name), NullAction())
                                hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Sell every unequipped copy of the selected item (quest and test items are never sold).", screen_name="manager_inventory"), NullAction())
                                unhovered Hide("tooltip")
                                text "Sell stack" size font_size(18) color ("#ffffff" if _stack_plan else "#aaaaaa") xalign 0.5 yalign 0.5
                            button:
                                xsize 116
                                ysize 30
                                background Solid(gui.journal_dark_color)
                                hover_background Solid("#5a3a2a")
                                sensitive (bool(_shown_plan) and not is_transferring)
                                action Confirm("Sell all {} shown items ({} kinds) for ${}?".format(_shown_n, len(_shown_plan), _shown_gold), Function(mass_sell_inventory_items, _shown_plan, _bulk_worker_name), NullAction())
                                hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Sell every item currently passing the filter and search (equipped, quest and test items are never sold).", screen_name="manager_inventory"), NullAction())
                                unhovered Hide("tooltip")
                                text "Sell shown" size font_size(18) color ("#ffffff" if _shown_plan else "#aaaaaa") xalign 0.5 yalign 0.5
                            button:
                                xsize 116
                                ysize 30
                                background Solid(gui.journal_dark_color)
                                hover_background Solid("#5a3a2a")
                                sensitive (bool(_dupes_plan) and not is_transferring)
                                action Confirm("Keep 1 of each shown item and sell {} duplicates for ${}?".format(_dupes_n, _dupes_gold), Function(mass_sell_inventory_items, _dupes_plan, _bulk_worker_name), NullAction())
                                hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="For each distinct shown item keep one copy and sell the rest (equipped, quest and test items are never sold).", screen_name="manager_inventory"), NullAction())
                                unhovered Hide("tooltip")
                                text "Sell dupes" size font_size(18) color ("#ffffff" if _dupes_plan else "#aaaaaa") xalign 0.5 yalign 0.5
                    null height 5
                    frame:
                        background Solid("#1a1a1a")
                        xsize 360
                        ysize (165 if shop_mode else 200)
                        padding (10, 10)
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            ysize (145 if shop_mode else 180)
                            # Get selected item name for header
                            python:
                                _sel_item = selected_worker_item if selected_worker_item is not None else selected_manager_item
                                _sel_item_name = ""
                                _sel_item_category = ""
                                _category_labels = {
                                    "weapon": "Weapon",
                                    "armor": "Armor",
                                    "clothing": "Clothing",
                                    "accessory": "Accessory",
                                    "consumable": "Consumable",
                                    "gift": "Gift",
                                    "currency": "Currency",
                                    "quest_item": "Quest Item",
                                    "misc": "Misc",
                                }
                                if _sel_item:
                                    _sel_item_info = next((i for i in items_json["items"] if i["id"] == _sel_item[0]), {})
                                    _sel_item_name = _sel_item_info.get("name", "")
                                    _sel_item_category = _category_labels.get(_sel_item_info.get("type", "misc"), str(_sel_item_info.get("type", "misc")).replace("_", " ").title())
                            if _sel_item_name:
                                vbox:
                                    spacing 5
                                    text "{color=#d4a574}[_sel_item_name]{/color}  {color=#d8bf9a}Category: [_sel_item_category]{/color}" size font_size(24) xalign 0.0 yalign 0.5 xmaximum 340
                                    text "[selected_description]" size font_size(24) color "#ffffff"
                            else:
                                text "[selected_description]" size font_size(26) color "#ffffff"
                    null height 5
                    # Item image box (50% of the right panel)
                    frame:
                        background Solid("#1a1a1a")
                        xsize 360
                        ysize 235
                        padding (10, 10)
                        $ current_item = selected_worker_item if selected_worker_item is not None else selected_manager_item
                        $ current_item_id = current_item[0] if current_item else None
                        $ _item_def = next((i for i in items_json.get("items", []) if i.get("id") == current_item_id), None) if current_item_id else None
                        $ _img_basename = _item_def.get("image", current_item_id) if _item_def and _item_def.get("image") else current_item_id
                        $ img_path_png = f"images/items/{_img_basename}.png" if _img_basename is not None else None
                        $ img_path_jpg = f"images/items/{_img_basename}.jpg" if _img_basename is not None else None
                        $ img_path_jpeg = f"images/items/{_img_basename}.jpeg" if _img_basename is not None else None
                        $ displayable = img_path_png if (_img_basename is not None and renpy.loadable(img_path_png)) else (img_path_jpg if (_img_basename is not None and renpy.loadable(img_path_jpg)) else (img_path_jpeg if (_img_basename is not None and renpy.loadable(img_path_jpeg)) else None))
                        if displayable:
                            add Transform(displayable, xysize=(340, 205)) xalign 0.5 yalign 0.0
                        else:
                            text "No Image found" size font_size(22) color "#ffffff" xalign 0.5 yalign 0.5

            frame:
                xsize 540
                xoffset -10
                ysize 540
                background Solid("#1a1a1acc")
                padding (10, 10)
                vbox:
                    spacing 5
                    $ shop_name = "Basic Shop" if shop_mode == "shop1" else "Adventurer's Market" if shop_mode == "shop2" else "Elite Emporium" if shop_mode == "shop3" else (right_worker['name'] if right_worker and right_worker is not False else ('Storage' if right_worker is None else 'No Worker Selected'))
                    button:
                        background "images/tablebutton.png"
                        xsize 500
                        ysize 50
                        hbox:
                            xalign 0.5
                            yalign 0.5
                            spacing 10
                            text "{size=32}[shop_name]{/size}" color "#ffffff" yalign 0.5
                            if not shop_mode:
                                text "{size=18}(click to change){/size}" color "#ffffff" yalign 0.5
                        action If(not shop_mode, 
                            Show("worker_selection_popup", panel="right", current_left=left_worker, current_right=right_worker, shop_mode=shop_mode),
                            None
                        )
                        sensitive (not shop_mode)
                        hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Right panel destination. Click to select which worker or storage is on the right side.", screen_name="manager_inventory"), NullAction())
                        unhovered Hide("tooltip")
                    python:
                        _cat_names = {
                            "weapon": "Weapons",
                            "armor": "Armor",
                            "clothing": "Clothing",
                            "accessory": "Accessories",
                            "consumable": "Consumables",
                            "gifts": "Gifts",
                            "currency": "Currency",
                            "quest_item": "Quest Items",
                            "misc": "Misc"
                        }
                        _right_cat_label = "All Items" if right_panel_filter_category is None else _cat_names.get(right_panel_filter_category, str(right_panel_filter_category).replace("_", " ").title())
                    textbutton "Filter: [_right_cat_label]":
                        action Show("inventory_filter_popup", target_var="right_panel_filter_category", current_cat=right_panel_filter_category, popup_title="FILTER RIGHT PANEL")
                        xsize 500
                        ysize 40
                        text_size 30
                        text_color "#d8bf9a"
                        text_hover_color "#ffffff"
                        background "images/tablebutton.png"
                    if right_worker is False and shop_mode is None:
                        text "No worker selected." size font_size(26) xalign 0.5 yalign 0.5
                    else:
                        # Calculate right panel sort settings
                        $ right_show_arrow = shop_mode or right_sort_by_name
                        $ right_name_action = None if shop_mode else ToggleScreenVariable("right_sort_by_name")
                        hbox:
                            spacing 0
                            button:
                                background "images/tablebutton.png"
                                xsize 200
                                ysize 40
                                action right_name_action
                                hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message=("Shop list sorted by name." if shop_mode else "Sort right panel by name. Toggle alphabetical and arrival order."), screen_name="manager_inventory"), NullAction())
                                unhovered Hide("tooltip")
                                hbox:
                                    spacing 3
                                    yalign 0.5
                                    text "Name" size font_size(22) yalign 0.5 yoffset 3 color "#ffffff" hover_color ("#ffffff" if shop_mode else gui.journal_hover_color)
                                    if right_show_arrow:
                                        add "gui/arrowdown.png" zoom 0.1 yalign 0.5
                            if shop_mode:
                                button:
                                    background "images/tablebutton.png"
                                    xsize 90
                                    ysize 40
                                    action ToggleScreenVariable("right_shop_sort_by_price")
                                    hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Sort shop list by price ranking. Toggle price and name order.", screen_name="manager_inventory"), NullAction())
                                    unhovered Hide("tooltip")
                                    hbox:
                                        spacing 3
                                        yalign 0.5
                                        text "Price" size font_size(22) xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff" hover_color gui.journal_hover_color
                                        if right_shop_sort_by_price:
                                            add "gui/arrowdown.png" zoom 0.1 yalign 0.5
                            else:
                                button:
                                    background "images/tablebutton.png"
                                    xsize 90
                                    ysize 40
                                    text "Qty" size font_size(22) xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                                    action None
                            if shop_mode is None:
                                button:
                                    background "images/tablebutton.png"
                                    xsize 90
                                    ysize 40
                                    text "Action" size font_size(22) xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                                    action None
                            else:
                                null width 90 height 40
                            button:
                                background None
                                padding (0, 0, 0, 0)
                                xsize 140
                                ysize 40
                                $ header_action = "Buy" if shop_mode else "Trade"
                                text "[header_action]" size font_size(22) xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                                action None
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            xsize 500
                            ysize 395
                            vbox:
                                spacing 5
                                if shop_mode:
                                    # shop1: Basic (<=200), shop2: Adventurer's (<=500), shop3: Elite (no limit)
                                    $ price_limit = 200 if shop_mode == "shop1" else 500 if shop_mode == "shop2" else 999999
                                    # Get excluded items list from items_json (empty list if not present)
                                    $ excluded_items = items_json.get("excluded_from_shops", [])
                                    # Filter items by category if one is selected
                                    $ filtered_items = items_json["items"]
                                    if right_panel_filter_category:
                                        if right_panel_filter_category == "gifts":
                                            $ _gift_ids_shop = set(getattr(store, "YVARA_GIFTS", {}).keys())
                                            $ _gift_ids_shop -= {"diamond", "ruby", "emerald", "sapphire"}
                                            $ filtered_items = [item for item in filtered_items if item.get("id") in _gift_ids_shop]
                                        else:
                                            $ filtered_items = [item for item in filtered_items if item.get("type") == right_panel_filter_category]
                                    # Exclude items from excluded_from_shops list
                                    $ filtered_items = [item for item in filtered_items if item.get("id") not in excluded_items]
                                    # Filter out test items if show_test_items is False
                                    if not show_test_items:
                                        $ filtered_items = [item for item in filtered_items if "test" not in item.get("id", "").lower() and "debug" not in item.get("id", "").lower()]
                                    # Apply search filter if search text is provided
                                    if item_search_text:
                                        $ filtered_items = [item for item in filtered_items if item_search_text.lower() in item.get("name", "").lower()]
                                    # Sort by selected mode
                                    if right_shop_sort_by_price:
                                        $ filtered_items = sorted(filtered_items, key=lambda x: (-int(x.get("price", 0)), x.get("name", "ZZZ").lower()))
                                    else:
                                        $ filtered_items = sorted(filtered_items, key=lambda x: x.get("name", "ZZZ").lower())
                                    $ shop_items = [(item["id"], 1, False) for item in filtered_items if item.get("price", 0) <= price_limit and is_item_available_in_shop(item, shop_mode)]
                                    $ _items_by_id = {it.get("id"): it for it in items_json.get("items", [])}
                                    for item_idx, item in enumerate(shop_items):
                                        $ item_info = _items_by_id.get(item[0], {})
                                        $ _item_name = item_info.get("name", "Unknown")
                                        $ _item_name_display = _item_name[:15] + "..." if len(_item_name) > 17 else _item_name
                                        $ bg_button = Solid("#777777") if item_idx % 2 == 0 else Solid("#555555")
                                        button:
                                            background bg_button
                                            xsize 520
                                            ysize 40
                                            padding (0, 0, 0, 0)
                                            hover_background Solid("#c0c0c0cc")
                                            action Function(handle_inventory_row_click, "right_shop", item_idx, item, item_info, True, False, False)
                                            hbox:
                                                spacing 0
                                                frame:
                                                    xsize 200
                                                    background None
                                                    text ("{b}" + _item_name_display + "{/b}" if selected_worker_item == item else _item_name_display) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 90
                                                    background None
                                                    text "${}".format(item_info.get("price", 0)) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 90
                                                    background None
                                                button:
                                                    style "inv_trade_action_button"
                                                    xsize 140
                                                    background None
                                                    text "{u}Buy{/u}" size font_size(24) hover_color gui.journal_hover_color xalign 0.0 yalign 0.5 yoffset 3
                                                    action [SetScreenVariable("selected_worker_item", item), SetScreenVariable("selected_worker_index", None), SetScreenVariable("selected_manager_item", None), SetScreenVariable("selected_manager_index", None), SetScreenVariable("selected_description", item_info.get("description", "")), Function(buy_item_from_shop, item[0])]
                                                    sensitive (not is_transferring and store.money >= item_info.get("price", 0))
                                                    hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Buy selected item. Double-click row for quick buy.", screen_name="manager_inventory"), NullAction())
                                                    unhovered Hide("tooltip")
                                else:
                                    $ right_inventory = [] if right_worker is False else (manager_inventory if right_worker is None else right_worker.get("inventory", []))
                                    # Sort and filter items - alphabetically or by arrival order based on toggle
                                    python:
                                        def get_item_name_for_sort_right(idx_item):
                                            item = idx_item[1]
                                            item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                            return item_info.get("name", "ZZZ").lower()
                                        
                                        def item_matches_search_right(idx_item, search_text, category_filter=None):
                                            item = idx_item[1]
                                            item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                            if category_filter is not None:
                                                if category_filter == "gifts":
                                                    _gift_ids = set(getattr(store, "YVARA_GIFTS", {}).keys())
                                                    _gift_ids -= {"diamond", "ruby", "emerald", "sapphire"}
                                                    if item[0] not in _gift_ids:
                                                        return False
                                                elif item_info.get("type") != category_filter:
                                                    return False
                                            if not search_text:
                                                return True
                                            item_name = item_info.get("name", "").lower()
                                            return search_text.lower() in item_name
                                        
                                        search_text_r = item_search_text if item_search_text else ""
                                        category_filter_r = right_panel_filter_category
                                        # Filter items first
                                        equipped_list_r = [(idx, item) for idx, item in enumerate(right_inventory) if store._is_equipped(item) and item_matches_search_right((idx, item), search_text_r, category_filter_r)]
                                        unequipped_list_r = [(idx, item) for idx, item in enumerate(right_inventory) if not store._is_equipped(item) and item_matches_search_right((idx, item), search_text_r, category_filter_r)]
                                        # Sort by name only if toggle is on, otherwise keep arrival order (by index)
                                        if right_sort_by_name:
                                            equipped_items = sorted(equipped_list_r, key=get_item_name_for_sort_right)
                                            unequipped_items = sorted(unequipped_list_r, key=get_item_name_for_sort_right)
                                        else:
                                            equipped_items = equipped_list_r  # Keep original order (arrival)
                                            unequipped_items = unequipped_list_r

                                    for idx, item in equipped_items:
                                        $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                        $ _item_name = item_info.get("name", "Unknown")
                                        $ _item_name_display = _item_name[:15] + "..." if len(_item_name) > 17 else _item_name
                                        $ label, the_action, is_sens, btn_bg = get_item_action_elements(item, item_info, right_worker, idx)
                                        $ bg_button = Solid("#d4a574")
                                        button:
                                            background bg_button
                                            xsize 520
                                            ysize 40
                                            padding (0, 0, 0, 0)
                                            hover_background Solid("#c0c0c0cc")
                                            action Function(handle_inventory_row_click, "right_worker", idx, item, item_info, False, False, (left_worker is not False))
                                            hbox:
                                                spacing 0
                                                frame:
                                                    xsize 200
                                                    background None
                                                    text ("{b}" + _item_name_display + "{/b}" if selected_worker_index == idx else _item_name_display) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 90
                                                    background None
                                                    text str(item[1]) size font_size(24) xalign 0.0 yalign 0.5 yoffset 3
                                                button:
                                                    xsize 90
                                                    background None
                                                    text "[label]" size font_size(20) xalign 0.0 yalign 0.5 yoffset 3
                                                    action the_action
                                                    sensitive is_sens
                                                button:
                                                    style "inv_trade_action_button"
                                                    xsize 140
                                                    background None
                                                    text "{u}Left{/u}" size font_size(24) hover_color gui.journal_hover_color xalign 0.0 yalign 0.5 yoffset 3
                                                    action [SetScreenVariable("selected_worker_item", item), SetScreenVariable("selected_worker_index", idx), SetScreenVariable("selected_manager_item", None), SetScreenVariable("selected_manager_index", None), SetScreenVariable("selected_description", item_info.get("description", "")), Function(transfer_to_left)]
                                                    sensitive ((left_worker is not False) and not is_transferring)
                                                    hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Move selected item to the left panel target. Double-click row for quick transfer.", screen_name="manager_inventory"), NullAction())
                                                    unhovered Hide("tooltip")

                                    for i, idx_item in enumerate(unequipped_items):
                                        $ idx, item = idx_item
                                        $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                        $ _item_name = item_info.get("name", "Unknown")
                                        $ _item_name_display = _item_name[:17] + "..." if len(_item_name) > 19 else _item_name
                                        $ label, the_action, is_sens, btn_bg = get_item_action_elements(item, item_info, right_worker, idx)
                                        $ bg_button = Solid("#777777") if i % 2 == 0 else Solid("#555555")
                                        button:
                                            background bg_button
                                            xsize 550
                                            ysize 40
                                            padding (0, 0, 0, 0)
                                            hover_background Solid("#c0c0c0cc")
                                            action Function(handle_inventory_row_click, "right_worker", idx, item, item_info, False, False, (left_worker is not False))
                                            hbox:
                                                spacing 0
                                                frame:
                                                    xsize 200
                                                    background None
                                                    text ("{b}" + _item_name_display + "{/b}" if selected_worker_index == idx else _item_name_display) size font_size(22) xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 100
                                                    background None
                                                    text str(item[1]) size font_size(22) xalign 0.0 yalign 0.5 yoffset 3
                                                button:
                                                    xsize 100
                                                    background None
                                                    text "[label]" size font_size(20) xalign 0.0 yalign 0.5 yoffset 3
                                                    action the_action
                                                    sensitive is_sens
                                                button:
                                                    style "inv_trade_action_button"
                                                    xsize 150
                                                    background None
                                                    text "{u}Left{/u}" size font_size(22) hover_color gui.journal_hover_color xalign 0.0 yalign 0.5 yoffset 3
                                                    action [SetScreenVariable("selected_worker_item", item), SetScreenVariable("selected_worker_index", idx), SetScreenVariable("selected_manager_item", None), SetScreenVariable("selected_manager_index", None), SetScreenVariable("selected_description", item_info.get("description", "")), Function(transfer_to_left)]
                                                    sensitive ((left_worker is not False) and not is_transferring)
                                                    hovered If(get_tooltips_state_for_screen("manager_inventory"), ShowTransient("tooltip", message="Move selected item to the left panel target. Double-click row for quick transfer.", screen_name="manager_inventory"), NullAction())
                                                    unhovered Hide("tooltip")

    # Context menu drawn last so it appears on top
    fixed:
        xalign 1.0
        yalign 0.5
        xsize 320
        yfill True
        xoffset -5
        add context_menu_bg
        
        # Help/Information button - positioned in top-right corner of context menu (green panel)
        python:
            screen_name = "manager_inventory"
            tooltips_enabled = get_tooltips_state_for_screen(screen_name)
        
        imagebutton:
            idle Transform("gui/info_idle.png", zoom=0.315)
            hover Transform("gui/info_hover.png", zoom=0.315)
            selected_idle Transform("gui/info_active.png", zoom=0.315)
            selected_hover Transform("gui/info_active.png", zoom=0.315)
            selected tooltips_enabled
            action Function(toggle_tooltips_for_screen, screen_name)
            hovered ShowTransient("tooltip", message="Tooltips: {color=#ffffff}On{/color}/Off", screen_name=screen_name)
            unhovered Hide("tooltip")
            xalign 1.0
            xoffset -60
            yalign 0.0
            yoffset 55
        
        vbox:
            xalign 0.5
            yalign 0.5
            xoffset -17
            yoffset (20 if shop_mode is None else 20)
            spacing 10
            if shop_mode is None:
                # Compact worker summary panel (for quick stats/skills while trading)
                $ summary_worker = right_worker if (right_worker is not None and right_worker is not False) else (left_worker if (left_worker is not None and left_worker is not False) else None)
                if summary_worker is not None:
                    frame:
                        background "#00000033"
                        xsize 300
                        ysize 390
                        padding (10, 14)
                        vbox:
                            spacing 6
                            xsize 280
                            hbox:
                                spacing 6
                                xalign 0.0
                                textbutton "[summary_worker['name']]":
                                    action Show("worker_details", worker=summary_worker, in_roster=True)
                                    text_size font_size(28)
                                    text_color gui.journal_dark_color
                                    text_hover_color gui.journal_hover_color
                                    background None
                                    yalign 0.5
                                    hovered If(get_tooltips_state_for_screen(screen_name), ShowTransient("tooltip", message="Open this worker's full details screen.", screen_name=screen_name), NullAction())
                                    unhovered Hide("tooltip")
                                text "(click for details)" size font_size(20) color gui.journal_dark_color yalign 0.5
                            null height 0
                            # Energy / Health mini bars
                            # E/H color coherence: same rule as the workers roster
                            # (numbers turn gui.danger_color below 30% of the calculated max).
                            python:
                                _sum_max_e = calculate_max_energy(summary_worker)
                                _sum_max_h = calculate_max_health(summary_worker)
                                _sum_cur_e = int(summary_worker.get("energy", 0) or 0)
                                _sum_cur_h = int(summary_worker.get("health", 0) or 0)
                                _sum_e_col = gui.danger_color if (_sum_max_e and _sum_cur_e < 0.3 * _sum_max_e) else "#ffffff"
                                _sum_h_col = gui.danger_color if (_sum_max_h and _sum_cur_h < 0.3 * _sum_max_h) else "#ffffff"
                            hbox:
                                spacing 4
                                xalign 0.5
                                xoffset -2
                                button:
                                    background None
                                    xsize 136
                                    ysize 32
                                    padding (0, 0)
                                    action NullAction()
                                    hovered If(get_tooltips_state_for_screen(screen_name), ShowTransient("tooltip", message="Energy bar: current and maximum energy for this worker.", screen_name=screen_name), NullAction())
                                    unhovered Hide("tooltip")
                                    fixed:
                                        xsize 136
                                        ysize 24
                                        bar:
                                            value summary_worker.get("energy", 0)
                                            range calculate_max_energy(summary_worker)
                                            xsize 136
                                            ysize 24
                                            left_bar gui.energy_bar_color
                                            right_bar "#444444"
                                        text "E [_sum_cur_e]/[_sum_max_e]" size font_size(18) color _sum_e_col xalign 0.5 yalign 0.5
                                button:
                                    background None
                                    xsize 136
                                    ysize 32
                                    padding (0, 0)
                                    action NullAction()
                                    hovered If(get_tooltips_state_for_screen(screen_name), ShowTransient("tooltip", message="Health bar: current and maximum health for this worker.", screen_name=screen_name), NullAction())
                                    unhovered Hide("tooltip")
                                    fixed:
                                        xsize 136
                                        ysize 24
                                        bar:
                                            value summary_worker.get("health", 0)
                                            range calculate_max_health(summary_worker)
                                            xsize 136
                                            ysize 24
                                            left_bar gui.health_bar_color
                                            right_bar "#444444"
                                        text "H [_sum_cur_h]/[_sum_max_h]" size font_size(18) color _sum_h_col xalign 0.5 yalign 0.5

                            textbutton "Switch to [quick_panel_mode == 'skills' and 'Stats' or 'Skills']":
                                text_size font_size(20)
                                text_color "#ffffff"
                                text_hover_color gui.journal_hover_color
                                background None
                                xalign 0.0
                                action SetScreenVariable("quick_panel_mode", quick_panel_mode == "skills" and "stats" or "skills")
                                hovered If(get_tooltips_state_for_screen(screen_name), ShowTransient("tooltip", message="Rotate quick panel view between stats and skills.", screen_name=screen_name), NullAction())
                                unhovered Hide("tooltip")

                            if quick_panel_mode == "stats":
                                vbox:
                                    spacing 6
                                    $ _summary_reb_cap = get_attribute_cap(summary_worker, "rebelliousness")
                                    $ _summary_reb_cap_display = int(_summary_reb_cap if _summary_reb_cap is not None else 100)
                                    $ _summary_lib_cap_display = int(get_max_libido(summary_worker))
                                    $ _summary_stats = [
                                        ("Rebelliousness", summary_worker.get("rebelliousness", 0), _summary_reb_cap_display),
                                        ("Joy", summary_worker.get("joy", 0), 100),
                                        ("Romance", summary_worker.get("romance", 0), 100),
                                        ("Relationship", summary_worker.get("relationship", 0), 100),
                                    ]
                                    if persistent.nsfw_enabled:
                                        $ _summary_stats.insert(3, ("Libido", summary_worker.get("libido", 0), _summary_lib_cap_display))
                                    $ _summary_stats_left = _summary_stats[::2]
                                    $ _summary_stats_right = _summary_stats[1::2]
                                    hbox:
                                        spacing 4
                                        xalign 0.5
                                        vbox:
                                            spacing 6
                                            xsize 136
                                            for stat_name, stat_value, stat_max in _summary_stats_left:
                                                button:
                                                    background "#00000044"
                                                    xsize 136
                                                    ysize 32
                                                    padding (4, 4)
                                                    action NullAction()
                                                    fixed:
                                                        xsize 128
                                                        ysize 24
                                                        bar:
                                                            value stat_value
                                                            range max(1, stat_max)
                                                            xsize 128
                                                            ysize 24
                                                            left_bar gui.journal_hover_color
                                                            right_bar "#444444"
                                                        text "[stat_name]: [stat_value]" size font_size(18) color "#ffffff" xalign 0.5 yalign 0.5 xmaximum 124
                                        vbox:
                                            spacing 6
                                            xsize 136
                                            for stat_name, stat_value, stat_max in _summary_stats_right:
                                                button:
                                                    background "#00000044"
                                                    xsize 136
                                                    ysize 32
                                                    padding (4, 4)
                                                    action NullAction()
                                                    fixed:
                                                        xsize 128
                                                        ysize 24
                                                        bar:
                                                            value stat_value
                                                            range max(1, stat_max)
                                                            xsize 128
                                                            ysize 24
                                                            left_bar gui.journal_hover_color
                                                            right_bar "#444444"
                                                        text "[stat_name]: [stat_value]" size font_size(18) color "#ffffff" xalign 0.5 yalign 0.5 xmaximum 124
                                    null height 6
                                    # Profession and building (dynamic)
                                    textbutton "[get_worker_profession_and_building_display(summary_worker)]":
                                        action NullAction()
                                        background None
                                        text_size font_size(21)
                                        text_color "#3d2914"
                                        text_hover_color "#3d2914"
                                        xalign 0.0
                                        hovered If(get_tooltips_state_for_screen(screen_name), ShowTransient("tooltip", message="Current assignment: building and job for this worker.", screen_name=screen_name), NullAction())
                                        unhovered Hide("tooltip")
                            else:
                                vbox:
                                    xsize 280
                                    ysize 238
                                    xoffset 3
                                    yoffset 0
                                    vbox:
                                        spacing 2
                                        $ _summary_skills = list(get_visible_skills(summary_worker))
                                        $ _summary_skills_half = (len(_summary_skills) + 1) // 2
                                        $ _summary_skills_left = _summary_skills[:_summary_skills_half]
                                        $ _summary_skills_right = _summary_skills[_summary_skills_half:]
                                        $ _skills_row_count = max(len(_summary_skills_left), len(_summary_skills_right))
                                        for _row_idx in range(_skills_row_count):
                                            $ _left_skill = _summary_skills_left[_row_idx] if _row_idx < len(_summary_skills_left) else None
                                            $ _right_skill = _summary_skills_right[_row_idx] if _row_idx < len(_summary_skills_right) else None
                                            $ _left_value = calculate_skill_with_traits(summary_worker, _left_skill[0], include_libido=False) if _left_skill else None
                                            $ _right_value = calculate_skill_with_traits(summary_worker, _right_skill[0], include_libido=False) if _right_skill else None
                                            $ _row_bg = "#0000002a" if _row_idx % 2 == 0 else "#00000044"
                                            hbox:
                                                spacing 0
                                                xsize 276
                                                ysize 26
                                                xalign 0.5
                                                frame:
                                                    background _row_bg
                                                    xsize 136
                                                    ysize 26
                                                    padding (0, 0)
                                                    hbox:
                                                        spacing 0
                                                        xsize 136
                                                        ysize 26
                                                        fixed:
                                                            xsize 92
                                                            ysize 26
                                                            if _left_skill:
                                                                text " [_left_skill[0]]:" size font_size(20) color gui.journal_dark_color yalign 0.5 xmaximum 90
                                                        fixed:
                                                            xsize 44
                                                            ysize 26
                                                            if _left_value is not None:
                                                                text "[_left_value]" size font_size(20) color gui.journal_dark_color yalign 0.5 xalign 1.0 text_align 1.0 xmaximum 39 xoffset -4
                                                null width 4
                                                frame:
                                                    background _row_bg
                                                    xsize 136
                                                    ysize 26
                                                    padding (0, 0)
                                                    hbox:
                                                        spacing 0
                                                        xsize 136
                                                        ysize 26
                                                        fixed:
                                                            xsize 92
                                                            ysize 26
                                                            if _right_skill:
                                                                text " [_right_skill[0]]:" size font_size(20) color gui.journal_dark_color yalign 0.5 xmaximum 90
                                                        fixed:
                                                            xsize 44
                                                            ysize 26
                                                            if _right_value is not None:
                                                                text "[_right_value]" size font_size(20) color gui.journal_dark_color yalign 0.5 xalign 1.0 text_align 1.0 xmaximum 39 xoffset -4
                                        null height 28
                            null height 0
                    frame:
                        background "#00000033"
                        xsize 300
                        ysize 180
                        padding (10, 12)
                        vbox:
                            spacing 6
                            xsize 280
                            text "Equipment" size font_size(24) color gui.journal_dark_color xalign 0.0
                            null height 2
                            $ _eq_pairs = [(i, next((x for x in items_json["items"] if x["id"] == i[0]), None)) for i in summary_worker.get("inventory", []) if store._is_equipped(i)]
                            $ _eq_weapon_name = next((info.get("name", "?") for _, info in _eq_pairs if info and info.get("type") == "weapon"), "Empty")
                            $ _eq_armor_name = next((info.get("name", "?") for _, info in _eq_pairs if info and info.get("type") == "armor"), None)
                            $ _eq_clothing_name = next((info.get("name", "?") for _, info in _eq_pairs if info and info.get("type") == "clothing"), None)
                            $ _eq_body_name = _eq_armor_name or _eq_clothing_name or "Empty"
                            $ _eq_accessory_name = next((info.get("name", "?") for _, info in _eq_pairs if info and info.get("type") == "accessory"), "Empty")
                            for _slot_key, _slot_label, _slot_value in [("weapon", "Weapon", _eq_weapon_name), ("body", "Clothing/Armor", _eq_body_name), ("accessory", "Accessory", _eq_accessory_name)]:
                                button:
                                    background "#00000044"
                                    xsize 272
                                    ysize 32
                                    padding (6, 4)
                                    action Function(cycle_summary_equipment_slot, summary_worker, _slot_key, 1)
                                    hovered If(get_tooltips_state_for_screen(screen_name), ShowTransient("tooltip", message="Click to cycle this slot. Includes Empty.", screen_name=screen_name), NullAction())
                                    unhovered Hide("tooltip")
                                    hbox:
                                        spacing 0
                                        xsize 260
                                        ysize 24
                                        fixed:
                                            xsize 120
                                            ysize 24
                                            text "[_slot_label]:" size font_size(18) color "#ffffff" yalign 0.5 xalign 0.0 xmaximum 116
                                        fixed:
                                            xsize 140
                                            ysize 24
                                            text "[_slot_value]" size font_size(18) color "#ffffff" yalign 0.5 xalign 0.0 xmaximum 136

        textbutton "Close":
            action If(
                return_to_worker is not None,
                [
                    Hide("manager_inventory"),
                    Show(
                        "worker_details",
                        worker=return_to_worker,
                        in_roster=return_to_in_roster,
                        from_buy_workers=return_to_from_buy_workers,
                        from_recruitment=return_to_from_recruitment
                    )
                ],
                If(
                    return_to_tavern,
                    [Hide("manager_inventory"), Show("tavern")],
                    [Hide("manager_inventory"), Show("map_screen")]
                )
            )
            xsize 300
            ysize 50
            text_size 42
            text_color gui.journal_dark_color
            text_hover_color gui.journal_hover_color
            xalign 0.5
            yalign 1.0
            yoffset -30

screen worker_selection_popup(panel, current_left, current_right, shop_mode=None):
    modal True
    zorder 100
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 720
        background None
        padding (40, 40)
        
        vbox:
            spacing 15
            null height 15
            label "SELECT FOR [panel.upper()] PANEL" xalign 0.5 style "header_style"
            null height 10
            vbox:
                xsize 640
                spacing 10
                xoffset 30
                yoffset 25
                
                if not shop_mode:  # Only show worker selection options if not in shop mode
                    # Storage option
                    textbutton "Storage":
                        action [
                            SetVariable("left_worker" if panel == "left" else "right_worker", None),
                            Hide("worker_selection_popup"),
                            Function(renpy.restart_interaction)
                        ]
                        xsize 580
                        text_size font_size(28)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                    
                    null height 8
                    
                    # Worker selection
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        ysize 400
                        xsize 625
                        xoffset -25
                        yoffset -20
                        
                        vbox:
                            spacing 10
                            for worker in workers_filtered_by_gender(store.workers):
                                textbutton "[worker['name']]":
                                    action [
                                        SetVariable("left_worker" if panel == "left" else "right_worker", worker),
                                        Hide("worker_selection_popup"),
                                        Function(renpy.restart_interaction)
                                    ]
                                    xsize 580
                                    text_size font_size(28)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    sensitive (panel == "left" and worker != current_right) or (panel == "right" and worker != current_left)
                else:
                    # Display message in shop mode
                    text "Worker selection is disabled in shop mode." size font_size(24) xalign 0.5 color gui.journal_text_color
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("worker_selection_popup")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    key "K_BACKSPACE" action Hide("worker_selection_popup")

screen inventory_filter_popup(target_var="left_panel_filter_category", current_cat=None, popup_title="FILTER ITEMS"):
    modal True
    zorder 110
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 720
        background None
        padding (40, 40)

        # Close button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("inventory_filter_popup")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
        
        vbox:
            spacing 15
            null height 15
            label "[popup_title]" xalign 0.5 style "header_style"
            null height 10
            
            python:
                if current_cat is None:
                    current_cat = renpy.get_screen_variable(target_var, "manager_inventory")
                category_names = {
                    None: "All Items",
                    "weapon": "Weapons",
                    "armor": "Armor",
                    "clothing": "Clothing",
                    "accessory": "Accessories",
                    "consumable": "Consumables",
                    "gifts": "Gifts",
                    "currency": "Currency",
                    "quest_item": "Quest Items",
                    "misc": "Misc"
                }
                option_ids = [None, "weapon", "armor", "clothing", "accessory", "consumable", "gifts", "currency", "quest_item", "misc"]
            
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 480
                xsize 625
                xoffset -5
                yoffset -20
                
                vbox:
                    spacing 10
                    for cid in option_ids:
                        $ lbl = category_names.get(cid, str(cid).replace("_", " ").title())
                        button:
                            xsize 580
                            ysize 44
                            background None
                            hover_background None
                            action [
                                Function(lambda _cid=cid, _target_var=target_var: renpy.set_screen_variable(_target_var, _cid, "manager_inventory")),
                                Hide("inventory_filter_popup"),
                                Function(renpy.restart_interaction)
                            ]
                            hbox:
                                spacing 0
                                null width 20
                                text "[lbl]" size font_size(28) color (gui.journal_hover_color if cid == current_cat else gui.journal_text_color) hover_color gui.journal_hover_color

    key "K_BACKSPACE" action Hide("inventory_filter_popup")

screen confirm_upgrade(building_name):
    modal True
    zorder 200
    style_prefix "confirm"
    add "gui/overlay/confirm.png"

    python:
        building = available_buildings[building_name]
        current_level = building["base_level"]
        upgrade_cost = current_level ** 2 * 1000  # Match the calculation in upgrade_building function

    frame:
        style "confirm_frame"
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45

            label "Spend $[upgrade_cost] to increase 1 level?":
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 150

                textbutton "Yes" action If(money >= upgrade_cost,
                    [Function(upgrade_building, building_name), Function(lambda: setattr(store, 'building_upgraded_tutorial', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 6 else None), Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 6 else None), Hide("confirm_upgrade")],
                    Show("error_popup", message="You do not have enough money to upgrade.")
                )
                textbutton "No" action Hide("confirm_upgrade")

    key "game_menu" action Hide("confirm_upgrade")
    key "K_BACKSPACE" action Hide("confirm_upgrade")

screen building_type_selection(building_name):
    zorder 101
    modal True
    tag building_type
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 720
        background None
        padding (40, 40)
        
        vbox:
            spacing 15
            null height 15
            label "SELECT BUILDING TYPE" xalign 0.5 style "header_style"
            null height 10
            vbox:
                xsize 640
                spacing 10
                xoffset 30
                yoffset 25
                
                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    draggable True
                    ysize 480
                    xsize 625
                    xoffset -25
                    yoffset -20
                    
                    vbox:
                        spacing 10
                        for btype in building_types_json.get("building_types", []):
                            # Castle only via ending; Academy and Arena are map-only, not assignable to generic buildings
                            if btype.get("id") not in ("governor_castle", "academy", "arena"):
                                textbutton "[btype['name']]":
                                    xsize 580
                                    text_size font_size(28)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action [
                                        SetDict(available_buildings[building_name], "type", btype["id"]),
                                        Function(lambda: setattr(store, 'building_1_type_set', True) if hasattr(store, 'tutorial_active') and store.tutorial_active else None),
                                        Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active else None),
                                        Hide("building_type_selection")
                                    ]
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("building_type_selection")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    key "K_BACKSPACE" action Hide("building_type_selection")

screen confirm_change_type(building_name):
    modal True
    zorder 200
    style_prefix "confirm"
    add "gui/overlay/confirm.png"

    frame:
        style "confirm_frame"
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45

            label "Changing type will reset building to level 1 and cost $1000. Continue?":
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 150

                textbutton "Yes" action If(money >= 1000,
                    [SetVariable("money", money - 1000), Function(change_building_type, building_name), Hide("confirm_change_type")],
                    Show("error_popup", message="Insufficient funds!")
                )
                textbutton "No" action Hide("confirm_change_type")

    key "game_menu" action Hide("confirm_change_type")
    key "K_BACKSPACE" action Hide("confirm_change_type")

screen confirm_buy_potion(worker, potion_id):
    modal True
    zorder 200
    style_prefix "confirm"
    add "gui/overlay/confirm.png"

    python:
        potion_item = next((i for i in items_json["items"] if i["id"] == potion_id), None)
        if potion_item:
            potion_name = potion_item.get("name", "Potion")
            potion_price = potion_item.get("price", 0)
        else:
            potion_name = "Potion"
            potion_price = 0

    frame:
        style "confirm_frame"
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45

            text "You have no [potion_name]s, do you want to buy one for $[potion_price]? {size=34}(You have $[money]){/size}":
                style "confirm_prompt"
                xalign 0.5
                yalign 0.5
                size 38
                color gui.journal_dark_color
                text_align 0.5
                xsize 600

            # QoL: skip this dialog next time (Yes-path runs directly).
            # Can be re-enabled in Options > More Options ("Potion buy confirm").
            textbutton "Don't ask again: [getattr(persistent, 'skip_potion_buy_confirm', False) and 'On' or 'Off']":
                xalign 0.5
                text_size font_size(22)
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                background None
                hover_background None
                action ToggleField(persistent, "skip_potion_buy_confirm")

            hbox:
                xalign 0.5
                spacing 150

                textbutton "Yes" action If(money >= potion_price,
                    [
                        Function(lambda p=potion_price: setattr(store, 'money', store.money - p)),
                        Function(lambda pid=potion_id: add_item_to_inventory(manager_inventory, pid, 1)),
                        Function(lambda w=worker, pid=potion_id: use_potion_from_inventory(w, pid)),
                        Hide("confirm_buy_potion")
                    ],
                    [
                        Hide("confirm_buy_potion"),
                        Show("error_popup", message="You do not have enough money to buy this potion.")
                    ]
                )
                textbutton "No" action Hide("confirm_buy_potion")

    key "game_menu" action Hide("confirm_buy_potion")
    key "K_BACKSPACE" action Hide("confirm_buy_potion")

screen confirm_buy_worker(worker, return_screen=None):
    modal True
    zorder 200
    style_prefix "confirm"
    add "gui/overlay/confirm.png"

    frame:
        style "confirm_frame"
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45

            label "Buy [worker['name']] for $[worker['cost']]?":
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 150

                textbutton "Yes" action If(money >= worker["cost"],
                    [Function(buy_worker, worker), Hide("confirm_buy_worker")],
                    Show("error_popup", message="You do not have enough money to buy this worker.")
                )
                textbutton "No" action If(return_screen,
                    [Hide("confirm_buy_worker"), Show(return_screen, worker=worker)],
                    Hide("confirm_buy_worker")
                )

    key "K_BACKSPACE" action If(return_screen,
        [Hide("confirm_buy_worker"), Show(return_screen, worker=worker)],
        Hide("confirm_buy_worker")
    )

screen confirm_refresh_workers():
    modal True
    zorder 200
    style_prefix "confirm"
    add "gui/overlay/confirm.png"

    frame:
        style "confirm_frame"
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45

            label "Refresh the worker list for $2500?":
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 150

                textbutton "Yes" action If(hasattr(store, 'money') and store.money >= 2500,
                    [Function(store.refresh_buy_workers), Hide("confirm_refresh_workers"), Function(renpy.restart_interaction)],
                    Show("error_popup", message="You do not have enough money to refresh the worker list.")
                )
                textbutton "No" action Hide("confirm_refresh_workers")

    key "game_menu" action Hide("confirm_refresh_workers")
    key "K_BACKSPACE" action Hide("confirm_refresh_workers")

screen confirm_sell_worker(worker, return_screen=None):
    modal True
    zorder 200
    style_prefix "confirm"
    add "gui/overlay/confirm.png"

    python:
        sell_text = get_sell_text(worker)
        # Base worker daily comfort charge.
        daily_cost = compute_single_worker_daily_charge(worker)
        if daily_cost == 0:
            comfort_level = worker.get("comfort_level", 1)
            daily_cost = int(comfort_level * get_difficulty_comfort_mult())
        
        if worker.get("is_servant", False):
            refund = worker.get("level", 1) * 500
            message = f"Sell {worker['name']} for ${refund}?\nYou will save ${daily_cost} per day."
        else:
            message = f"Fire {worker['name']}?\nYou will save ${daily_cost} per day.\nThis action cannot be undone."

    frame:
        style "confirm_frame"
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45

            label message:
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 150

                textbutton "Yes" action If(return_screen == "worker_details",
                    [Function(sell_worker, worker), Hide("confirm_sell_worker"), Hide("worker_details")],
                    [Function(sell_worker, worker), Hide("confirm_sell_worker")]
                )
                textbutton "No" action If(return_screen,
                    [Hide("confirm_sell_worker"), Show(return_screen, worker=worker)],
                    Hide("confirm_sell_worker")
                )

    key "game_menu" action If(return_screen,
        [Hide("confirm_sell_worker"), Show(return_screen, worker=worker)],
        Hide("confirm_sell_worker")
    )
    key "K_BACKSPACE" action If(return_screen,
        [Hide("confirm_sell_worker"), Show(return_screen, worker=worker)],
        Hide("confirm_sell_worker")
    )

screen adjust_skill_bonus(building_name):
    modal True
    zorder 100
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 720
        background None
        padding (40, 40)
        
        $ building = available_buildings[building_name]
        $ btype_id = building.get("type")
        $ skill_name = "Skill" if btype_id is None else next((bt["skill_name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "Skill")
        $ skill_description = "No description available" if btype_id is None else next((bt.get("skill_description", "No description available") for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "No description available")
        
        vbox:
            spacing 15
            null height 15
            label "[skill_name] Bonus" xalign 0.5 style "header_style"
            null height 10
            vbox:
                xsize 580
                spacing 10
                xoffset 30
                yoffset 25
                
                # Skill description
                text "[skill_description]" size font_size(24) color gui.journal_text_color text_align 0.0 xalign 0.0
                
                null height 20
                
                # Calculator section
                vbox:
                    spacing 10
                $ total_skill = building["skill"] + building["skill_bonus"]
                $ fixed_cost = get_building_base_maintenance_cost(building_name, building)
                $ worker_costs = compute_worker_portion_daily_costs(building.get("assigned_servants") or [], building.get("base_level", 1))[0]
                $ _skill_mult = get_difficulty_building_skill_mult()
                $ current_bonus_cost = int(((building["skill_bonus"] // 10) * 100) * _skill_mult)
                $ current_total_cost = fixed_cost + worker_costs + current_bonus_cost
                $ new_bonus_cost = int((((building["skill_bonus"] + 10) // 10) * 100) * _skill_mult) if building["skill_bonus"] < 50 else current_bonus_cost
                $ new_total_cost = fixed_cost + worker_costs + new_bonus_cost
                
                # Base and bonus display with buttons
                hbox:
                    xalign 0.0
                    spacing 10
                    text "Base: [building['skill']], Bonus: [building['skill_bonus']]" size font_size(24) color gui.journal_text_color
                    hbox:
                        spacing 0
                        textbutton "+" style "game_menu_button":
                            action [SetDict(available_buildings[building_name], "skill_bonus", min(50, building["skill_bonus"] + 10)), Function(lambda: setattr(store, 'building_skill_bonus_increased_tutorial', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 6 else None), Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective in [6] else None)]
                            xsize 25
                            text_size font_size(28)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            text_bold True
                            text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                            sensitive building["skill_bonus"] < 50
                        textbutton "-" style "game_menu_button":
                            action SetDict(available_buildings[building_name], "skill_bonus", max(0, building["skill_bonus"] - 10))
                            xsize 25
                            text_size font_size(28)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            text_bold True
                            text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                            sensitive building["skill_bonus"] > 0
                
                if building["skill_bonus"] < 50:
                    $ _adj_sk_bonus_tt = "Total/day preview = Fixed + Workers + Skill Bonus.\n\nFixed: $" + str(fixed_cost) + "\nWorkers: $" + str(worker_costs) + " (sum of comfort x " + str(get_difficulty_comfort_mult()) + "; building level does not multiply this)\nSkill Bonus upkeep (current): $" + str(current_bonus_cost) + "\nSkill Bonus upkeep (next): $" + str(new_bonus_cost)
                    button:
                        background None
                        padding (0, 0)
                        xalign 0.0
                        action NullAction()
                        hovered If(get_tooltips_state_for_screen("adjust_skill_bonus"), ShowTransient("tooltip", message=_adj_sk_bonus_tt, screen_name="adjust_skill_bonus"), NullAction())
                        unhovered Hide("tooltip")
                        text "Next Total/day: $[new_total_cost] {size=20}(Fixed: $[fixed_cost], Workers: $[worker_costs], Skill Bonus: $[new_bonus_cost]){/size}" size font_size(24) color "#444444"
                else:
                    text "Max [skill_name] Bonus Reached" size font_size(24) color "#1b5e20" xalign 0.0
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("adjust_skill_bonus")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    key "K_BACKSPACE" action Hide("adjust_skill_bonus")

screen Manager(building_name):
    on "show" action [Function(sync_assigned_servants_for_building, building_name), Function(maybe_show_intro_popup, "manager_buildings")]
    zorder 5
    python:
        _bn = str(building_name or "").strip()
        _norm_fn = getattr(store, "_norm_building_key", lambda k: str(k or "").strip())
        _tgt = _norm_fn(_bn)
        _roster = store.workers or []
        manager_servants = [w for w in _roster if hasattr(w, "get") and w.get("name") and _norm_fn(w.get("assigned_building", "")) == _tgt and w.get("assigned_building") not in (None, "", "Unassigned")]
        # Keep a stable visual order across repeated re-renders/open-close cycles.
        manager_servants = sorted(
            manager_servants,
            key=lambda ww: (
                str(ww.get("name", "")).strip().lower(),
                int(ww.get("level", 1) or 1),
            ),
        )
        _displayed_servants = manager_servants
        _resolved_data = store._resolve_building_by_name(_bn)[0] if hasattr(store, "_resolve_building_by_name") else None
        _resolved_data = _resolved_data or store.available_buildings.get(_bn) or {}

    # Building background adjusted to 1515px width to account for side panel
    # Exception: default.png shows at full size (1920x1080)
    $ bg_image = get_building_bg(building_name)
    $ is_default = bg_image == "images/buildings/default.png"
    if is_default:
        add bg_image
    else:
        add bg_image:
            xsize 1515
            ysize 1080
            xalign 0.0
            yalign 0.0
    # Decorative context panel background centered like tavern/map
    add context_menu_bg xalign 0.5 yalign 0.5
    
    # Money and Date positioned over context menu area (top-right)
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        hbox:
            spacing 5
            text "$" color gui.journal_dark_color size 24 bold True yalign 0.5
            text "[format(int(money), ',')]" color gui.journal_dark_color size 28 yalign 0.5
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]
            $ month_name = month_names[store.current_month - 1]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color gui.journal_dark_color size 26 yalign 0.5
        # Compact status strip: roster size and owned holdings (read-only)
        python:
            _tv_worker_count = len(store.workers)
            _tv_building_count = len(getattr(store, "owned_buildings", []) or [])
        text "Workers: [_tv_worker_count]      Buildings: [_tv_building_count]" color gui.journal_dark_color size 20
        # Player title and name (click to open character sheet) — blink when pending skill points
        if manager_has_unspent_skill_points():
            timer 0.7 repeat True action ToggleVariable("manager_name_blink_highlight")
        python:
            _manager_name_color = gui.journal_hover_color if (getattr(store, 'manager_name_blink_highlight', False) and manager_has_unspent_skill_points()) else gui.journal_dark_color
        textbutton "[player_title] [player_name]":
            action Show("manager_character_sheet")
            text_color _manager_name_color
            text_hover_color gui.journal_hover_color
            text_size 26
            text_italic True
            background None
            hover_background None

    # Left panel: place behind the right context menu; reduced width and full height
    frame:
        xalign 0.0
        yalign 0.5
        xsize 1511
        ysize 1.0
        background Solid("#000000cc")
        padding (40, 40)
        vbox:
            spacing 5
            xfill True
            vbox:
                spacing 5
                $ building = _resolved_data if (_resolved_data and hasattr(_resolved_data, 'get')) else {}
                $ _building_jobs_use = dict(building.get("servant_jobs") or {}) if building else {}
                $ btype_id = building.get("type")
                $ type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                $ skill_name = "Skill" if btype_id is None else next((bt["skill_name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "Skill")
                $ parts = building_name.split('_')
                $ default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                $ display_name = store.custom_names.get(building_name, default_name)
                $ total_skill = building.get("skill", 10) + building.get("skill_bonus", 0)
                $ rep_cap = get_building_reputation_cap(building) if building else 200
                $ capped_reputation = min(building.get("reputation", 0), rep_cap)
                $ rep_tier = get_reputation_tier(capped_reputation)
                $ rep_is_capped = (capped_reputation >= rep_cap and rep_cap > 0)
                $ _erep_for_stories = get_effective_reputation_for_events(building) if building else 0
                # Typical extra stories from reputation (default formula reputation/400; shown once at building header).
                $ typical_bonus_stories = get_reputation_bonus_stories(_erep_for_stories, "reputation / 400")
                hbox:
                    spacing 10
                    text "[type_name]: [display_name]" size font_size(42) xalign 0.0 color gui.journal_text_color
                $ fixed_cost = get_building_base_maintenance_cost(building_name, building)
                $ worker_costs = compute_worker_portion_daily_costs(manager_servants, building.get("base_level", 1))[0]
                $ bonus_cost = int(((building.get("skill_bonus", 0) // 10) * 100) * get_difficulty_building_skill_mult())
                $ total_costs = fixed_cost + worker_costs + bonus_cost
                $ _mgr_cost_tt = "How daily costs are calculated:\n\nTotal/day = Fixed + Workers + Skill Bonus\nFixed: $" + str(fixed_cost) + " (scales with building level; Normal: $100, $300, $500, $700, $900 for levels 1-5)\nWorkers: $" + str(worker_costs) + " (sum of comfort x " + str(get_difficulty_comfort_mult()) + "; not multiplied by level)\nSkill Bonus upkeep: $" + str(bonus_cost) + "\n\nWorker Details shows per-worker comfort cost only."
                textbutton "Costs/day: $[total_costs] {size=22}(Fixed: $[fixed_cost], Workers: $[worker_costs], Skill Bonus: $[bonus_cost]){/size}":
                    xalign 0.0
                    yalign 0.5
                    action NullAction()
                    text_size font_size(26)
                    text_color "#ffffff"
                    text_hover_color "#f5e6d3"
                    background None
                    padding (0, 0)
                    hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message=_mgr_cost_tt, screen_name="Manager"), NullAction())
                    unhovered Hide("tooltip")
                button:
                    xalign 0.0
                    background None
                    padding (0, 0)
                    action NullAction()
                    hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message=get_building_level_short_tooltip(), screen_name="Manager"), NullAction())
                    unhovered Hide("tooltip")
                    text "Level: [building.get('base_level', 1)]" size font_size(26) color "#ffffff"
                text "Reputation: [capped_reputation][rep_is_capped and ' (capped by building level)' or ''] - {b}[rep_tier]{/b}" size font_size(26) color "#ffffff" xalign 0.0
                $ event_limit = building.get("event_limit", 0)
                if typical_bonus_stories > 0:
                    if event_limit == 0:
                        text "  → +[typical_bonus_stories] stories per profession per day" size font_size(24) color "#d4a574" xalign 0.0
                    elif event_limit == 1:
                        text "  → +[typical_bonus_stories] stories per profession per day (limited to 1)" size font_size(24) color "#d4a574" xalign 0.0
                    elif event_limit == 2:
                        text "  → +[typical_bonus_stories] stories per profession per day (limited to 2)" size font_size(24) color "#d4a574" xalign 0.0
                    elif event_limit == 3:
                        text "  → +[typical_bonus_stories] stories per profession per day (limited to 3)" size font_size(24) color "#d4a574" xalign 0.0
                elif event_limit > 0:
                    text "  → Limited to [event_limit] event[event_limit != 1 and 's' or ''] per worker per day" size font_size(24) color "#d4a574" xalign 0.0
                text "[skill_name]: [total_skill] {size=22}(Base: [building.get('skill', 10)], Bonus: [building.get('skill_bonus', 0)]){/size=}" size font_size(26) color "#ffffff" xalign 0.0
                hbox:
                    spacing 10
                    text "Daily Stories Limit:" size font_size(26) color "#ffffff" yalign 0.5
                    $ event_limit = building.get("event_limit", 0)
                    $ limit_texts = ["Unlimited (with reputation bonus)", "Limited to 1 per worker", "Limited to 2 per worker", "Limited to 3 per worker"]
                    $ current_text = limit_texts[event_limit] if event_limit < len(limit_texts) else limit_texts[0]
                    textbutton "[current_text]":
                        text_size font_size(26)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                        action SetDict(building, "event_limit", (event_limit + 1) % 4)
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 700
                xsize 1440
                vbox:
                    spacing 5
                    xfill True
                    $ building_type_id = building.get("type")
                    if building_type_id is not None:
                        $ building_type_entry = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == building_type_id), None)
                        if building_type_entry is not None:
                            for profession in building_type_entry.get("professions", []):
                                $ current_count = len([s for s in _displayed_servants if _building_jobs_use.get(s["name"], "") == profession["id"]])
                                $ max_limit = get_max_daily_workers(building, profession)
                                text "[profession['name']] ([current_count]/[max_limit])" size font_size(26) xalign 0.0 color gui.journal_text_color
                                $ _prof_mech = profession_mechanics_summary(profession)
                                if _prof_mech:
                                    text "[_prof_mech]" size font_size(26) xalign 0.0 color "#9a8a6a"
                                frame:
                                    background Solid("#1a1a1a99")
                                    padding (10, 10)
                                    xfill True
                                    viewport:
                                        scrollbars None
                                        mousewheel True
                                        draggable True
                                        ysize 300
                                        xfill True
                                        vbox:
                                            spacing 5
                                            hbox:
                                                spacing 5
                                                xsize 1440
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Name (Level)" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Average / Best skill" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Energy - Health" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Actions" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                            python:
                                                _workers_in_prof = [
                                                    w for w in _displayed_servants
                                                    if _building_jobs_use.get(w["name"], "") == profession["id"]
                                                ]
                                                _skills_for_prof = profession.get("skills", []) or []
                                                def _prof_sort_key(_w, _skills=_skills_for_prof):
                                                    if _skills:
                                                        _vals = [calculate_skill_with_traits(_w, str(_s), include_libido=False) for _s in _skills]
                                                        _avg = int(sum(_vals) // len(_vals)) if _vals else 0
                                                        _best = int(max(_vals)) if _vals else 0
                                                    else:
                                                        _avg = 0
                                                        _best = 0
                                                    _name = str(_w.get("name", "")).strip().lower()
                                                    # Higher avg/best skill first, stable tie-break by name.
                                                    return (-_avg, -_best, _name)
                                                _workers_in_prof = sorted(_workers_in_prof, key=_prof_sort_key)
                                            for worker in _workers_in_prof:
                                                $ worker_level = worker.get('level', 1)
                                                # E/H color coherence: danger color below 30% of max (roster rule).
                                                $ _mgr_max_e = calculate_max_energy(worker)
                                                $ _mgr_max_h = calculate_max_health(worker)
                                                $ _mgr_e_col = gui.danger_color if (_mgr_max_e and int(worker.get("energy", 0) or 0) < 0.3 * _mgr_max_e) else "#ffffff"
                                                $ _mgr_h_col = gui.danger_color if (_mgr_max_h and int(worker.get("health", 0) or 0) < 0.3 * _mgr_max_h) else "#ffffff"
                                                hbox:
                                                    spacing 5
                                                    xsize 1440
                                                    textbutton "[worker['name']] ([worker_level])":
                                                        xsize 275
                                                        text_size font_size(24)
                                                        text_color "#ffffff"
                                                        text_hover_color gui.journal_hover_color
                                                        action Show("worker_details", worker=worker, in_roster=True)
                                                    $ avg_skill = 0
                                                    $ best_skill_name = "N/A"
                                                    $ best_skill_value = 0
                                                    $ skills_used_worker = profession.get("skills", [])
                                                    $ total_worker = 0
                                                    $ count_worker = 0
                                                    $ best_skill_id = None
                                                    for s in skills_used_worker:
                                                        $ skill_value = calculate_skill_with_traits(worker, str(s), include_libido=False)
                                                        $ total_worker += skill_value
                                                        $ count_worker += 1
                                                        if skill_value > best_skill_value:
                                                            $ best_skill_value = skill_value
                                                            $ best_skill_id = str(s)
                                                    if count_worker > 0:
                                                        $ avg_skill = total_worker // count_worker
                                                    if best_skill_id is not None:
                                                        $ best_skill_name = skill_names.get(best_skill_id, best_skill_id)
                                                    $ skill_text = f"{avg_skill} / {best_skill_name}: {best_skill_value}" if avg_skill > 0 and best_skill_id is not None else "N/A"
                                                    textbutton "[skill_text]":
                                                        xsize 275
                                                        text_size font_size(24)
                                                        text_color "#ffffff"
                                                        text_hover_color gui.journal_hover_color
                                                    hbox:
                                                        spacing 2
                                                        xsize 275
                                                        textbutton "E: [worker['energy']]/[_mgr_max_e]":
                                                            xsize 136
                                                            text_size font_size(24)
                                                            text_color _mgr_e_col
                                                            text_hover_color "#2c4aa6"
                                                            action use_or_buy_potion_action(worker, "energy_potion")
                                                            sensitive worker["energy"] < _mgr_max_e
                                                        textbutton "H: [worker['health']]/[_mgr_max_h]":
                                                            xsize 137
                                                            text_size font_size(24)
                                                            text_color _mgr_h_col
                                                            text_hover_color "#a63c3c"
                                                            action use_or_buy_potion_action(worker, "health_potion")
                                                            sensitive worker["health"] < _mgr_max_h
                                                    textbutton "Change / View skills":
                                                        xsize 275
                                                        text_size font_size(24)
                                                        text_color "#ffffff"
                                                        text_hover_color gui.journal_hover_color
                                                        action Show("job_selection", worker=worker)
                            # Unassigned: workers in building but with no profession or "unassigned"
                            $ _unassigned = [w for w in _displayed_servants if str(_building_jobs_use.get(w["name"], "unassigned") or "").strip().lower() in ("", "unassigned")]
                            $ _unassigned = sorted(_unassigned, key=lambda _w: str(_w.get("name", "")).strip().lower())
                            if _unassigned:
                                text "Unassigned ([len(_unassigned)])" size font_size(26) xalign 0.0 color gui.journal_text_color
                                frame:
                                    background Solid("#1a1a1a99")
                                    padding (10, 10)
                                    xfill True
                                    viewport:
                                        scrollbars None
                                        mousewheel True
                                        draggable True
                                        ysize 300
                                        xfill True
                                        vbox:
                                            spacing 5
                                            hbox:
                                                spacing 5
                                                xsize 1440
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Name (Level)" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Assign a role to participate" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Energy - Health" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                                button:
                                                    background "images/tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Actions" size font_size(26) color gui.journal_text_color
                                                    sensitive False
                                            for worker in _unassigned:
                                                $ worker_level = worker.get('level', 1)
                                                # E/H color coherence: danger color below 30% of max (roster rule).
                                                $ _mgr_max_e = calculate_max_energy(worker)
                                                $ _mgr_max_h = calculate_max_health(worker)
                                                $ _mgr_e_col = gui.danger_color if (_mgr_max_e and int(worker.get("energy", 0) or 0) < 0.3 * _mgr_max_e) else "#ffffff"
                                                $ _mgr_h_col = gui.danger_color if (_mgr_max_h and int(worker.get("health", 0) or 0) < 0.3 * _mgr_max_h) else "#ffffff"
                                                hbox:
                                                    spacing 5
                                                    xsize 1440
                                                    textbutton "[worker['name']] ([worker_level])":
                                                        xsize 275
                                                        text_size font_size(24)
                                                        text_color "#ffffff"
                                                        text_hover_color gui.journal_hover_color
                                                        action Show("worker_details", worker=worker, in_roster=True)
                                                    textbutton "—":
                                                        xsize 275
                                                        text_size font_size(24)
                                                        text_color "#888888"
                                                        sensitive False
                                                    hbox:
                                                        spacing 2
                                                        xsize 275
                                                        textbutton "E: [worker['energy']]/[_mgr_max_e]":
                                                            xsize 136
                                                            text_size font_size(24)
                                                            text_color _mgr_e_col
                                                            text_hover_color "#2c4aa6"
                                                            action use_or_buy_potion_action(worker, "energy_potion")
                                                            sensitive worker["energy"] < _mgr_max_e
                                                        textbutton "H: [worker['health']]/[_mgr_max_h]":
                                                            xsize 137
                                                            text_size font_size(24)
                                                            text_color _mgr_h_col
                                                            text_hover_color "#a63c3c"
                                                            action use_or_buy_potion_action(worker, "health_potion")
                                                            sensitive worker["health"] < _mgr_max_h
                                                    textbutton "Assign role":
                                                        xsize 275
                                                        text_size font_size(24)
                                                        text_color "#ffffff"
                                                        text_hover_color gui.journal_hover_color
                                                        action Show("job_selection", worker=worker)
    
    # Right panel: building management buttons and global context menu
    frame:
        xalign 1.0
        yalign 0.5
        xsize 320
        ysize 1.0
        background None
        
        # Help/Information button - positioned in top-right corner of context menu (green panel)
        python:
            screen_name = "Manager"
            tooltips_enabled = get_tooltips_state_for_screen(screen_name)
        
        imagebutton:
            idle Transform("gui/info_idle.png", zoom=0.315)
            hover Transform("gui/info_hover.png", zoom=0.315)
            selected_idle Transform("gui/info_active.png", zoom=0.315)
            selected_hover Transform("gui/info_active.png", zoom=0.315)
            selected tooltips_enabled
            action Function(toggle_tooltips_for_screen, screen_name)
            hovered ShowTransient("tooltip", message="Tooltips: {color=#ffffff}On{/color}/Off", screen_name=screen_name)
            unhovered Hide("tooltip")
            xalign 1.0
            xoffset -60
            yalign 0.0
            yoffset 55
        
        frame:
            xalign 1.0
            yalign 0.5
            xsize 320
            ysize 1.0
            background context_menu_bg
            vbox:
                xalign 0.5
                yalign 0.5
                spacing 10
                textbutton "Rename Building":
                    action [Function(ensure_custom_name_for_building, building_name), Show("rename_building", building_name=building_name)]
                    xsize 300
                    text_size 42
                    text_color gui.journal_dark_color
                    text_hover_color gui.journal_hover_color
                    ysize 50
                    align (0.5, 0.5)
                    hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message="Change the display name of this building", screen_name="Manager"), NullAction())
                    unhovered Hide("tooltip")
                
                # Only show upgrade buttons if building has a type (building from left panel)
                if building.get("type") is not None:
                    python:
                        current_level = building["base_level"]
                        max_level = 5
                        is_max_level = current_level >= max_level
                        upgrade_cost = current_level ** 2 * 1000
                        if is_max_level:
                            upgrade_tooltip = "This building is already at maximum level (5)."
                        else:
                            upgrade_tooltip = f"Increase building level by 1. Cost: ${upgrade_cost}. Higher levels increase max workers per profession and improve reputation."
                    if is_max_level:
                        textbutton "Max Level":
                            xsize 300
                            text_size 42
                            text_color "#888888"
                            ysize 50
                            align (0.5, 0.5)
                            sensitive False
                            hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message=upgrade_tooltip, screen_name="Manager"), NullAction())
                            unhovered Hide("tooltip")
                    else:
                        textbutton "Upgrade Building":
                            action Show("confirm_upgrade", building_name=building_name)
                            xsize 300
                            text_size 42
                            text_color gui.journal_dark_color
                            text_hover_color gui.journal_hover_color
                            ysize 50
                            align (0.5, 0.5)
                            hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message=upgrade_tooltip, screen_name="Manager"), NullAction())
                            unhovered Hide("tooltip")
                    python:
                        skill_name = next((bt.get('skill_name', 'Skill') for bt in building_types_json.get('building_types', []) if bt.get('id') == building.get('type')), 'Skill')
                        skill_description = next((bt.get('skill_description', 'No description available') for bt in building_types_json.get('building_types', []) if bt.get('id') == building.get('type')), 'No description available')
                        skill_tooltip = "This is the building's skill. " + skill_description
                    textbutton "[skill_name]":
                        action Show("adjust_skill_bonus", building_name=building_name)
                        xsize 300
                        text_size 42
                        text_color gui.journal_dark_color
                        text_hover_color gui.journal_hover_color
                        ysize 50
                        align (0.5, 0.5)
                        hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message=skill_tooltip, screen_name="Manager"), NullAction())
                        unhovered Hide("tooltip")
                
                # Building type/change type button
                if building.get("type") is None:
                    textbutton "Building Type":
                        action Show("building_type_selection", building_name=building_name)
                        xsize 300
                        text_size 42
                        text_color gui.journal_dark_color
                        text_hover_color gui.journal_hover_color
                        ysize 50
                        align (0.5, 0.5)
                        hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message="Select a business type for this building. Each type has unique professions and skills.", screen_name="Manager"), NullAction())
                        unhovered Hide("tooltip")
                else:
                    textbutton "Change Type":
                        action Show("confirm_change_type", building_name=building_name)
                        xsize 300
                        text_size 42
                        text_color gui.journal_dark_color
                        text_hover_color gui.journal_hover_color
                        ysize 50
                        align (0.5, 0.5)
                        hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message="Change the business type of this building. Warning: This will reset the building to level 1 and unassign all workers.", screen_name="Manager"), NullAction())
                        unhovered Hide("tooltip")

                $ _mgr_can_sell = store.manager_building_is_sellable(building_name) if callable(getattr(store, "manager_building_is_sellable", None)) else False
                if _mgr_can_sell:
                    $ _mgr_sale, _mgr_paid = store.building_sale_preview(building_name) if callable(getattr(store, "building_sale_preview", None)) else (0, 0)
                    $ _mgr_sell_confirm = "Sell %s for $%s? All workers in this building will be unassigned." % (display_name, _mgr_sale)
                    textbutton "Sell Building":
                        action Confirm(
                            _mgr_sell_confirm,
                            Function(store.manager_sell_current_building_then_exit, building_name),
                            NullAction()
                        )
                        xsize 300
                        text_size 42
                        text_color gui.journal_dark_color
                        text_hover_color gui.journal_hover_color
                        ysize 50
                        align (0.5, 0.5)
                        hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message="Sell this numbered slot (Building 2+). You receive purchase price minus $5,000; workers are unassigned.", screen_name="Manager"), NullAction())
                        unhovered Hide("tooltip")

                textbutton "Back":
                    action [SetVariable("current_bg", tavern_bg), Hide("Manager"), Show("tavern")]
                    xsize 300
                    text_size 42
                    text_color gui.journal_hover_color
                    text_hover_color "#ffffff"
                    ysize 50
                    align (0.5, 0.5)
                    hovered If(get_tooltips_state_for_screen("Manager"), ShowTransient("tooltip", message="Return to the tavern", screen_name="Manager"), NullAction())
                    unhovered Hide("tooltip")

            # (Context-only building options retained; tavern global options removed)

    # (Removed duplicate foreground left panel)

    key "K_BACKSPACE" action [SetVariable("current_bg", tavern_bg), Hide("Manager"), Show("tavern")]

screen building_selection(worker, return_to_workers=True):
    modal True
    zorder 99
    add Solid(gui.surface_dark)
    frame:
        xalign 0.5
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (40, 40)
        xsize 720
        ysize 720
        vbox:
            spacing 15
            null height 15
            label "SELECT BUILDING" xalign 0.5 style "header_style"
            null height 10
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 480
                xsize 625
                xoffset -5
                yoffset -20
                vbox:
                    spacing 10
                    xsize 580
                    yoffset 25
                    textbutton "Unassigned: No Building":
                        xsize 500
                        text_size font_size(28)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                        action [
                            Function(unassign_worker, worker),
                            Hide("building_selection"),
                            If(return_to_workers, Show("workers"), NullAction())
                        ]
                    $ bnames = sorted(available_buildings.keys())
                    for building_name in bnames:
                        # Fallback: If "owned" key is missing, assume the building is owned
                        $ is_owned = available_buildings[building_name].get("owned", True)
                        $ building = available_buildings[building_name]
                        $ btype_id = building.get("type")
                        $ type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                        $ parts = building_name.split('_')
                        $ default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                        $ display_name = store.custom_names.get(building_name, default_name)
                        if is_owned:
                            textbutton "[type_name]: [display_name]":
                                xsize 500
                                text_size font_size(28)
                                text_color gui.journal_text_color
                                text_hover_color gui.journal_hover_color
                                action [
                                    Function(remove_worker_from_building, worker),
                                    # Add worker to building with dedup protection
                                    Function(add_worker_to_building, worker, building_name),
                                    Hide("building_selection"),
                                    If(return_to_workers, Show("workers"), NullAction())
                                ]
                                sensitive True  # Always sensitive if owned
                        else:
                            textbutton "[type_name]: [display_name] (Not Available)":
                                xsize 500
                                text_size font_size(28)
                                text_color gui.journal_text_color
                                text_hover_color gui.journal_hover_color
                                sensitive False
        
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action [Hide("building_selection"), If(return_to_workers, Show("workers"), NullAction())]
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    key "K_BACKSPACE" action [Hide("building_selection"), If(return_to_workers, Show("workers"), NullAction())]

screen rename_building(building_name):
    modal True
    zorder 99
    default new_name = custom_names.get(building_name, building_name)
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        
        # Close button positioned like journal (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("rename_building")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
        
        vbox:
            spacing 15
            null height 15  # Push title down like journal
            label "Rename [custom_names.get(building_name, building_name)]" xalign 0.5 style "header_style"
            null height 10  # Less space after title like journal
            
            vbox:
                xsize 640  # Match journal content width
                spacing 15
                xoffset 30  # Match journal content offset
                yoffset 25
                
                # Input field
                text "New Name:" size font_size(34) color gui.journal_text_color xalign 0.0
                null height 10
                input:
                    id "new_name"
                    value ScreenVariableInputValue("new_name")
                    length 20
                    # Keep interpolation-sensitive characters out of custom names (BIBLIA §9)
                    exclude "{}[]"
                    color gui.journal_text_color
                null height 60
                
                # Confirm button centered
                textbutton "Confirm":
                    xalign 0.5
                    xsize 200
                    text_size font_size(34)
                    yoffset 10
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                    action If(
                        new_name.strip() != "",
                        [
                            Function(store.custom_names.update, {building_name: new_name}),
                            Hide("rename_building"),
                            Show("Manager", building_name=building_name)
                        ],
                        Show("error_popup", message="Name cannot be empty")
                    )

screen manager_character_sheet():
    modal True
    zorder 99
    default show_manager_benefits = False
    $ _mgmt_keys_full = ["business_acumen", "whore_mastery", "combat_instruction", "servant_training", "gang_leader"]
    $ _mgmt_keys = [k for k in _mgmt_keys_full if k != "whore_mastery" or getattr(persistent, "nsfw_enabled", False)]
    $ _spent = sum(management_skills.get(k, 0) for k in _mgmt_keys)
    $ _pending_d = getattr(store, "manager_pending_skills", None)
    $ store.manager_pending_skills = _pending_d if hasattr(_pending_d, "get") else {}
    $ _total_pending = sum(store.manager_pending_skills.get(k, 0) for k in _mgmt_keys)
    $ _manager_remaining = manager_level - _spent - _total_pending
    $ _skills_data_raw = [
        ("business_acumen", "Business Acumen", "A keen eye for ledgers and opportunity. You turn every coin and every handshake into advantage.", "Each point adds +0.1 to the money multiplier in any context."),
        ("whore_mastery", "Whore Mastery", "You know how to draw out the best in those who serve in the arts of pleasure. Your guidance sharpens their talents.", "Each point adds +5 to all sexual skills of all your workers."),
        ("combat_instruction", "Combat Instruction", "You drill your people in the arts of war. Blades, fists, and readiness become second nature under your command.", "Each point adds +5 to Combat and +10 to max HP for all workers."),
        ("servant_training", "Servant Training", "You instill discipline, grace, and devotion. Your household runs with quiet efficiency and loyalty.", "Each point adds +5 to Service and reduces max Rebelliousness by 10."),
        ("gang_leader", "Gang Leader", "You run a tight crew. Your people move faster, last longer, and follow your lead without question.", "Each point adds +5 to Agility and +10 to max Energy for all workers."),
    ]
    $ _skills_data = [s for s in _skills_data_raw if s[0] != "whore_mastery" or getattr(persistent, "nsfw_enabled", False)]
    add Solid(gui.surface_dark)
    fixed:
        xfill True
        yfill True
        frame:
            xalign 0.5
            yalign 0.5
            xsize 1.0
            ysize 1.0
            background Transform("gui/gallery.png", xysize=(1920, 1080))
            padding (20, 20)
            imagebutton:
                idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                action If(_total_pending > 0, Confirm("Your changes have not been saved. Do you want to continue?", [SetVariable("manager_pending_skills", {}), Hide("manager_character_sheet")], NullAction()), Hide("manager_character_sheet"))
                xalign 1.0
                yalign 0.0
                xoffset -125
                yoffset 125
            hbox:
                spacing 40
                xfill True
                yfill True
                xoffset 150
                yoffset 150
                # Left: portrait, then name, then level and explanation (fixed width so Benefits panel doesn't push)
                vbox:
                    spacing 8
                    xalign 0.0
                    yalign 0.0
                    xmaximum 260
                    frame:
                        background Solid("#1a1a1acc")
                        xsize 260
                        ysize 260
                        padding (2, 2)
                        xalign 0.0
                        yalign 0.0
                        if get_manager_portrait():
                            add get_manager_portrait():
                                xsize 256
                                ysize 256
                                fit "contain"
                                xalign 0.5
                                yalign 0.5
                        else:
                            vbox:
                                xalign 0.5
                                yalign 0.5
                                spacing 4
                                xmaximum 240
                                text "No portrait" size font_size(20) color "#ffffff" bold True xalign 0.5
                    text "Character portrait (256×256). Place lord.png or lady.png in game/images/manager_portraits/ for a custom look." size font_size(16) color "#ffffff" xalign 0.5 text_align 0.5
                    label "[player_title] [player_name]" xalign 0.0 style "header_style" text_size font_size(38)
                    hbox:
                        spacing 12
                        xalign 0.0
                        text "Level [manager_level]" size font_size(26) color gui.journal_hover_color bold True yalign 0.5
                        textbutton "Benefits":
                            text_size font_size(20)
                            text_color "#5a4a2a"
                            text_hover_color gui.journal_hover_color
                            action ToggleScreenVariable("show_manager_benefits")
                            yalign 0.5
                            background None
                            hover_background None
                            padding (8, 4)
                    if show_manager_benefits:
                        frame:
                            background Solid("#00000033")
                            padding (16, 14)
                            xsize 256
                            xalign 0.0
                            vbox:
                                spacing 8
                                xmaximum 224
                                $ _manager_rep_cap = min(1000, manager_level * 200)
                                text "Your building's reputation can go to [_manager_rep_cap] without upgrading the building's level." size font_size(18) color "#5a4a2a" xalign 0.0
                                $ _benefit_lines = []
                                $ _v = management_skills.get("business_acumen", 0)
                                if _v > 0:
                                    $ _benefit_lines.append("+%.1f to money multiplier in any context." % (_v * 0.1))
                                if getattr(persistent, "nsfw_enabled", False):
                                    $ _v = management_skills.get("whore_mastery", 0)
                                    if _v > 0:
                                        $ _benefit_lines.append("+%d to all sexual skills of all workers." % (_v * 5))
                                $ _v = management_skills.get("combat_instruction", 0)
                                if _v > 0:
                                    $ _benefit_lines.append("+%d Combat, +%d max HP for all workers." % (_v * 5, _v * 10))
                                $ _v = management_skills.get("servant_training", 0)
                                if _v > 0:
                                    $ _benefit_lines.append("+%d Service, -%d max Rebelliousness for all workers." % (_v * 5, _v * 10))
                                $ _v = management_skills.get("gang_leader", 0)
                                if _v > 0:
                                    $ _benefit_lines.append("+%d Agility, +%d max Energy for all workers." % (_v * 5, _v * 10))
                                if _benefit_lines:
                                    text "\n".join(_benefit_lines) size font_size(18) color "#5a4a2a" xalign 0.0
                # Right: skills only
                vbox:
                    spacing 20
                    xfill True
                    yalign 0.0
                    hbox:
                        spacing 12
                        text "Management Skills" size font_size(30) color gui.journal_text_color bold True xalign 0.0
                        if manager_level - _spent > 0:
                            text "(Please assign remaining skill points: [manager_level - _spent][_total_pending > 0 and ' (' + str(_total_pending) + ' pending)' or ''])" size font_size(24) color gui.journal_hover_color italic True yalign 0.5
                    null height 6
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        ysize 640
                        xsize 1280
                        vbox:
                            spacing 22
                            for skill_id, skill_name, flavor, mechanics in _skills_data:
                                $ val = management_skills.get(skill_id, 0)
                                $ preview = store.manager_pending_skills.get(skill_id, 0)
                                $ show_val = val + preview
                                frame:
                                    background Solid("#00000033")
                                    padding (16, 14)
                                    xsize 1280
                                    hbox:
                                        spacing 16
                                        vbox:
                                            spacing 6
                                            xmaximum 1150
                                            xfill True
                                            hbox:
                                                spacing 8
                                                text "[skill_name]" size font_size(26) color gui.journal_text_color
                                                text " [show_val]" size font_size(26) color gui.journal_hover_color
                                            text "[flavor]" size font_size(22) color "#5a4a2a" xalign 0.0 italic True
                                            text "[mechanics]" size font_size(20) color "#4a3a1a" xalign 0.0
                                        if _manager_remaining > 0:
                                            textbutton "+":
                                                text_size font_size(64)
                                                text_color "#3c2a1a"
                                                text_hover_color gui.journal_hover_color
                                                text_selected_color gui.journal_hover_color
                                                action Function(add_pending_management_skill, skill_id)
                                                xalign 1.0
                                                yalign 0.5
                                                background None
                                                hover_background None
                                                selected_background None
                                                selected (store.manager_pending_skills.get(skill_id, 0) > 0)
                                                padding (16, 12)
                                                xsize 72
                                                ysize 72
            if _total_pending > 0:
                textbutton "Confirm":
                    text_size font_size(28)
                    text_color "#3c2a1a"
                    text_hover_color gui.journal_hover_color
                    action Function(confirm_all_management_skill_points)
                    xalign 1.0
                    yalign 1.0
                    xoffset -180
                    yoffset -115
                    background None
                    hover_background None
                    padding (8, 4)

    key "K_BACKSPACE" action If(_total_pending > 0, Confirm("Your changes have not been saved. Do you want to continue?", [SetVariable("manager_pending_skills", {}), Hide("manager_character_sheet")], NullAction()), Hide("manager_character_sheet"))

screen manager_levelup_benefit():
    modal True
    zorder 200
    add Solid("#00000099")
    frame:
        xalign 0.5
        yalign 0.5
        background Frame("gui/frame.png", 20, 20)
        xpadding 40
        ypadding 30
        xminimum 400
        yminimum 180
        vbox:
            spacing 20
            label "Manager Level Up" xalign 0.5 style "header_style"
            text "You have 1 additional skill point to assign." size font_size(22) xalign 0.5 color gui.journal_text_color text_align 0.5
            textbutton "Continue":
                xalign 0.5
                text_size font_size(24)
                text_color gui.journal_text_color
                text_hover_color gui.journal_hover_color
                action Return()

    key "K_BACKSPACE" action Return()

screen buy_buildings():
    modal True
    zorder 99
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        # Close button in the top-right inside the panel
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action Hide("buy_buildings")

        vbox:
            spacing 15
            null height 15
            label "Available Buildings" xalign 0.5 style "header_style"
            null height 10
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 480
                xsize 605
                xoffset 25
                yoffset -20
                vbox:
                    spacing 10
                    xsize 580
                    yoffset 25
                    text "Purchase" xalign 0.0 size font_size(26) color "#5a3a1a"
                    $ _slot = store.next_generic_building_slot() if callable(getattr(store, "next_generic_building_slot", None)) else None
                    if _slot:
                        $ building_name, price = _slot
                        textbutton "[building_name] - $[price]":
                            xsize 500
                            text_size font_size(28)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action If(money >= price,
                                [
                                    Function(add_new_building, building_name, price),
                                    SetVariable("money", money - price),
                                    Function(register_new_building, building_name),
                                    Function(store.rebuild_assigned_servants),
                                    SetVariable("buildings_owned", len(store.owned_buildings)),
                                    Hide("buy_buildings"),
                                ])
                            sensitive (money >= price)
                    else:
                        text "No more building slots available to purchase." size font_size(24) xalign 0.0 color gui.journal_text_color

                    null height 18
                    text "Sell (Building 2+)" xalign 0.0 size font_size(26) color "#5a3a1a"
                    text "You receive purchase price minus $5,000. Workers are unassigned." size font_size(20) xalign 0.0 color "#6a5a4a"
                    $ _sellable = store.sellable_generic_building_names() if callable(getattr(store, "sellable_generic_building_names", None)) else []
                    if not _sellable:
                        text "No extra buildings to sell." size font_size(24) xalign 0.0 color gui.journal_text_color
                    for bn in _sellable:
                        $ sale, paid = store.building_sale_preview(bn)
                        $ disp = store.custom_names.get(bn, bn)
                        $ _sell_confirm = "Sell %s for $%s? All workers in this building will be unassigned." % (disp, sale)
                        textbutton "Sell [disp] — receive $[sale] (paid $[paid])":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action Confirm(
                                _sell_confirm,
                                Function(store.sell_building, bn),
                                NullAction()
                            )

    key "K_BACKSPACE" action Hide("buy_buildings")

screen in_development():
    modal True
    zorder 100
    add Solid("#00000099")
    frame:
        xalign 0.5
        yalign 0.5
        background Frame("gui/frame.png", 20, 20)
        xpadding 40
        ypadding 30
        xminimum 400
        yminimum 180
        vbox:
            spacing 20
            label "In development" xalign 0.5 style "header_style"
            text "This location is not available yet. Come back in a future update!" size font_size(22) xalign 0.5 color gui.journal_text_color text_align 0.5
            textbutton "Close":
                xalign 0.5
                text_size font_size(24)
                text_color gui.journal_text_color
                text_hover_color gui.journal_hover_color
                action Hide("in_development")

    key "K_BACKSPACE" action Hide("in_development")

# Yvara (Academy director): reserved screen kept for potential future dialogue overlays.
default academy_director_intro_done = False

screen academy_first_dialogue():
    ## Reserved for future "Visit director" dialogue. Tuition uses Ren'Py say + menu in academy_tuition_dialogue.
    modal True
    zorder 101
    # Full-screen background (same as recruitment events)
    $ academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else ("images/events/academy_director.png" if renpy.loadable("images/events/academy_director.png") else getattr(store, "event_bg", "images/event_bg.png"))
    add academy_bg
    add Solid("#000000dd")
    imagebutton:
        idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        xalign 1.0
        yalign 0.0
        xoffset -15
        yoffset 5
        action [SetVariable("academy_director_intro_done", False), Hide("academy_first_dialogue"), Show("map_screen")]
    # One box: speaker, text, and choices (like recruitment)
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#1a1a1acc")
        padding (30, 30)
        xsize 800
        vbox:
            xfill True
            spacing 20
            text "Yvara" size font_size(24) color "#c9a227" bold True xalign 0.0
            null height 5
            text "Welcome, traveller. I am Yvara. Our institution offers structured courses in Academics, Amatory Arts, Hospitality, and Artisan Studies. Your workers may attend and gain experience under our teachers." size font_size(20) color "#e8e8e8" xalign 0.0 text_align 0.0
            text "\"To enroll your establishment and gain access to our curriculum, the tuition is fifteen thousand coins. Pay once, and you may assign workers to our courses from the Manage Workers screen or from here.\"" size font_size(20) color "#c4b896" xalign 0.0 text_align 0.0 italic True
            null height 15
            text "What will you do?" size font_size(22) color "#ffdd88" xalign 0.0 italic True
            null height 10
            vbox:
                spacing 12
                textbutton "Pay the tuition ($15,000)":
                    xsize 700
                    text_size font_size(20)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                    action If(store.money >= 15000,
                        [Function(store.add_academy_building), SetVariable("money", store.money - 15000), SetVariable("academy_director_intro_done", False), Hide("academy_first_dialogue"), Show("academy_menu")],
                        Show("error_popup", message="You need $15,000 to pay the tuition.")
                    )
                    sensitive (store.money >= 15000)
                if store.academy_haggle_available:
                    textbutton "Try to haggle (50% chance; if it fails, locked until tomorrow)":
                        xsize 700
                        text_size font_size(20)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                        action If(store.money >= 7500,
                            [Function(academy_try_haggle_and_continue)],
                            Show("error_popup", message="You need at least $7,500 to try haggling.")
                        )
                        sensitive (store.money >= 7500)
                textbutton "Leave":
                    xsize 700
                    text_size font_size(20)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                    action [SetVariable("academy_director_intro_done", False), Hide("academy_first_dialogue"), Show("map_screen")]

    key "K_BACKSPACE" action [SetVariable("academy_director_intro_done", False), Hide("academy_first_dialogue"), Show("map_screen")]

screen yvara_gift_picker():
    ## Gift picker for Yvara: journal-style, lists giftable items in manager_inventory.
    modal True
    zorder 120
    $ _gift_items = yvara_get_giftable_items()
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action Return(("close", None))
        vbox:
            spacing 20
            null height 15
            label "Bring a Gift" xalign 0.5 style "header_style"
            hbox:
                spacing 0
                null width 28
                vbox:
                    spacing 14
                    text "Choose something from your pack." size font_size(22) color gui.journal_text_color text_align 0.0 xmaximum 520
                    null height 6
                    if _gift_items:
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            xsize 560
                            ysize 420
                            vbox:
                                spacing 10
                                for _gid, _gname, _gqty in _gift_items:
                                    textbutton "[_gname] (x[_gqty])":
                                        xsize 520
                                        text_size font_size(24)
                                        text_color gui.journal_text_color
                                        text_hover_color gui.journal_hover_color
                                        action Return(("gift", _gid))
                    else:
                        text "You carry nothing she would value right now." size font_size(21) color gui.journal_text_color xalign 0.0 text_align 0.0 italic True

    key "K_BACKSPACE" action Return(("close", None))

screen academy_menu():
    ## Academy main menu (after enrolled): Send workers / Visit director / Attend class.
    modal True
    zorder 101
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action [Hide("academy_menu"), Show("map_screen")]
        vbox:
            spacing 20
            null height 15
            label "Academy" xalign 0.5 style "header_style"
            hbox:
                spacing 0
                null width 28
                vbox:
                    spacing 20
                    text "Scholars and tutors await within—whether you wish to assign workers to a course, speak with the director, or lose yourself in the library." size font_size(22) xalign 0.0 color gui.journal_text_color text_align 0.0 xmaximum 520
                    null height 15
                    vbox:
                        spacing 12
                        textbutton "Train workers":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("academy_menu"), Show("academy_training_menu")]
                        if getattr(store, "academy_enrolled", False):
                            textbutton "Rent the Laboratory":
                                xsize 500
                                text_size font_size(24)
                                text_color gui.journal_text_color
                                text_hover_color gui.journal_hover_color
                                action [Hide("academy_menu"), Hide("map_screen"), Jump("academy_laboratory_dialogue")]
                        if getattr(store, "yvara_ending_route", "") != "dominion":
                            if getattr(store, "yvara_ending_route", "") == "mixed" and (calculate_total_days() % 2 == 1):
                                textbutton "Visit director":
                                    xsize 500
                                    text_size font_size(24)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action Function(renpy.notify, "Yvara is working in one of your buildings today, not at the Academy.")
                            else:
                                textbutton "Visit director":
                                    xsize 500
                                    text_size font_size(24)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action [Hide("academy_menu"), Hide("map_screen"), Jump("yvara_visit")]
                        textbutton "Visit the library":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("academy_menu"), Hide("map_screen"), Jump("academy_library_quest")]

    key "K_BACKSPACE" action [Hide("academy_menu"), Show("map_screen")]

screen academy_training_menu():
    ## Choose course: Academics / Amatory Arts / Hospitality Arts / Artisan Studies. Options also in Manage Workers.
    modal True
    zorder 102
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action [Hide("academy_training_menu"), Hide("academy_menu"), Show("map_screen")]
        vbox:
            spacing 16
            vbox:
                xoffset 15
                spacing 16
                null height 10
                label "Train workers" xalign 0.5 style "header_style"
                text "Choose a course. You will be taken to Manage Workers to assign workers to the Academy and select their course. These options will also be available from Manage Workers—assign a worker to the Academy there and choose their course." size font_size(23) xalign 0.5 color "#6a5a3a" text_align 0.5 xmaximum 580
                null height 8
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 440
                xsize 635
                hbox:
                    spacing 0
                    null width 28
                    vbox:
                        spacing 14
                        xsize 535
                        textbutton "Academics":
                            xsize 515
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("academy_training_menu"), Hide("academy_menu"), Hide("map_screen"), Show("workers"), Function(renpy.notify, "Assign workers to Academy and choose Academics as their lesson in Manage Workers.")]
                        text "Scholars and tutors here focus on wit and logic. Each day, the curriculum emphasises Clever and one other discipline chosen at random—so the mind stays sharp and versatile." size font_size(20) xalign 0.0 color "#5a4a2a" xoffset 0 text_align 0.0
                        null height 4
                        textbutton "Amatory Arts":
                            xsize 515
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("academy_training_menu"), Hide("academy_menu"), Hide("map_screen"), Show("workers"), Function(renpy.notify, "Assign workers to Academy and choose Amatory Arts as their lesson in Manage Workers.")]
                        text "The arts of intimacy are taught in discrete modules. Each lesson centres on one discipline—from core intimacy to dance and seduction—and touches one other at the tutors' choice, so progress stays focused but varied." size font_size(20) xalign 0.0 color "#5a4a2a" xoffset 0 text_align 0.0
                        null height 4
                        textbutton "Hospitality Arts":
                            xsize 515
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("academy_training_menu"), Hide("academy_menu"), Hide("map_screen"), Show("workers"), Function(renpy.notify, "Assign workers to Academy and choose Hospitality Arts as their lesson in Manage Workers.")]
                        text "Students learn to put guests at ease and tend to their needs. Training is split between Charm—presence and words—and Service—attentiveness and care—so they become reliable in both manner and deed." size font_size(20) xalign 0.0 color "#5a4a2a" xoffset 0 text_align 0.0
                        null height 4
                        textbutton "Artisan Studies":
                            xsize 515
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("academy_training_menu"), Hide("academy_menu"), Hide("map_screen"), Show("workers"), Function(renpy.notify, "Assign workers to Academy and choose Artisan Studies as their lesson in Manage Workers.")]
                        text "Workshops in the Academy's craft wing teach hands-on practice—measuring, mixing, and shaping under an artisan's eye. Each lesson centres on Craft and touches one other discipline at random, to keep hands and head working together." size font_size(20) xalign 0.0 color "#5a4a2a" xoffset 0 text_align 0.0

    key "K_BACKSPACE" action [Hide("academy_training_menu"), Hide("academy_menu"), Show("map_screen")]

# Arena: choose a worker for the trial by combat (any worker, show Combat skill).
screen choose_worker_for_arena_trial():
    modal True
    zorder 100
    python:
        eligible_workers = workers_filtered_by_gender(list(store.workers))
    add Solid(gui.surface_dark)
    frame:
        xalign 0.5
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (40, 40)
        xsize 800
        ysize 720
        vbox:
            spacing 15
            null height 15
            label "Choose a combatant for the arena trial" xalign 0.5 style "header_style"
            text "The trial may be to the death. Choose a worker to send into the sands." size font_size(20) color gui.journal_text_color xalign 0.5 text_align 0.5 xmaximum 700
            null height 10
            if not eligible_workers:
                text "You have no workers to send." color "#a63c3c" xalign 0.5 text_align 0.5 size 20
                textbutton "Back":
                    xalign 0.5
                    xsize 200
                    text_size font_size(20)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                    action [SetVariable("_arena_chosen_worker", None), Return(False)]
            else:
                vbox:
                    xoffset 50
                    spacing 10
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        ysize 480
                        xsize 630
                        vbox:
                            spacing 10
                            for worker in eligible_workers:
                                $ worker_combat = calculate_skill_with_traits(worker, "Combat")
                                textbutton "[worker['name']] (Combat: [worker_combat])":
                                    xsize 620
                                    text_size font_size(25)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action [Hide("choose_worker_for_arena_trial"), Function(renpy.call_in_new_context, "arena_run_trial_and_result", worker["name"])]
        # Close button: top-right inside the frame (drawn on top)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action [SetVariable("_arena_chosen_worker", None), Return(False)]
            xalign 1.0
            yalign 0.0
            xoffset -45
            yoffset 5

    key "K_BACKSPACE" action [SetVariable("_arena_chosen_worker", None), Return(False)]

# Arena: choose a worker for the special match (5000 entry, 2 rounds + combat roll).
screen choose_worker_for_arena_special_match():
    modal True
    zorder 100
    python:
        eligible_workers = workers_filtered_by_gender(list(store.workers))
    add Solid(gui.surface_dark)
    frame:
        xalign 0.5
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (40, 40)
        xsize 800
        ysize 720
        vbox:
            spacing 15
            null height 15
            label "Choose a fighter for the special match" xalign 0.5 style "header_style" xoffset 5
            text "Entry paid. Choose who enters the sands. Two rounds of choices, then skill decides. Defeat may mean death—or mercy and scars." size font_size(20) color gui.journal_text_color xalign 0.5 text_align 0.5 xmaximum 480 xoffset 5
            null height 10
            if not eligible_workers:
                text "You have no workers to send." color "#a63c3c" xalign 0.5 text_align 0.5 size 20
                textbutton "Back":
                    xalign 0.5
                    xsize 200
                    text_size font_size(20)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                    action [SetVariable("_arena_special_chosen_worker", None), Return()]
            else:
                vbox:
                    xoffset 50
                    spacing 10
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        ysize 380
                        xsize 630
                        vbox:
                            xoffset 5
                            spacing 10
                            for worker in eligible_workers:
                                $ worker_combat = calculate_skill_with_traits(worker, "Combat")
                                $ is_champion = "Arena Champion" in worker.get("traits", [])
                                $ btn_text = worker["name"] + " (Combat: " + str(worker_combat) + ")" + (" — Champion of the sands" if is_champion else "")
                                textbutton "[btn_text]":
                                    xsize 620
                                    text_size font_size(25)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action [Hide("choose_worker_for_arena_special_match"), SetVariable("_arena_special_chosen_worker", worker), Function(renpy.call_in_new_context, "arena_special_match_run", worker["name"])]
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action [SetVariable("_arena_special_chosen_worker", None), Return()]
            xalign 1.0
            yalign 0.0
            xoffset -45
            yoffset 5

    key "K_BACKSPACE" action [SetVariable("_arena_special_chosen_worker", None), Return()]

screen choose_worker_for_alchemy_craft():
    modal True
    zorder 100
    python:
        eligible_workers = workers_filtered_by_gender(list(store.workers))
    add Solid(gui.surface_dark)
    frame:
        xalign 0.5
        yalign 0.5
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (40, 40)
        xsize 800
        ysize 720
        vbox:
            spacing 15
            null height 15
            label "Choose a worker for the craft" xalign 0.5 style "header_style" xoffset 5
            text "Investment paid. Choose who directs the brew. Two rounds of choices, then Craft decides the outcome." size font_size(20) color gui.journal_text_color xalign 0.5 text_align 0.5 xmaximum 480 xoffset 5
            null height 10
            if not eligible_workers:
                text "You have no workers to send." color "#a63c3c" xalign 0.5 text_align 0.5 size 20
                textbutton "Back":
                    xalign 0.5
                    xsize 200
                    text_size font_size(20)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                    action [SetVariable("_alchemy_chosen_worker", None), Return()]
            else:
                vbox:
                    xoffset 50
                    spacing 10
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        ysize 380
                        xsize 630
                        vbox:
                            xoffset 5
                            spacing 10
                            for worker in eligible_workers:
                                $ worker_craft = calculate_skill_with_traits(worker, "Craft")
                                $ btn_text = worker["name"] + " (Craft: " + str(worker_craft) + ")"
                                textbutton "[btn_text]":
                                    xsize 620
                                    text_size font_size(25)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action [SetVariable("_alchemy_chosen_worker", worker), Hide("choose_worker_for_alchemy_craft"), Function(renpy.call_in_new_context, "academy_alchemy_craft_run")]
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action [SetVariable("_alchemy_chosen_worker", None), Return()]
            xalign 1.0
            yalign 0.0
            xoffset -45
            yoffset 5

    key "K_BACKSPACE" action [SetVariable("_alchemy_chosen_worker", None), Return()]

screen arena_menu():
    modal True
    zorder 101
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action [Hide("arena_menu"), Show("map_screen")]
        vbox:
            spacing 20
            null height 15
            label "Arena" xalign 0.5 style "header_style"
            hbox:
                spacing 0
                null width 28
                vbox:
                    spacing 20
                    text "Combat and spectacle await. Send gladiators to fight in exhibitions, proving bouts, or championship matches—or put on a Pin up Barbarians show." size font_size(22) xalign 0.0 color gui.journal_text_color text_align 0.0 xmaximum 520
                    null height 15
                    vbox:
                        spacing 12
                        textbutton "Send gladiators to fight":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("arena_menu"), Show("arena_training_menu")]
                        textbutton "Buy special match ([SPECIAL_MATCH_COST] coins)":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("arena_menu"), Hide("map_screen"), Jump("arena_special_match_dialogue")]
                        textbutton "Visit promoter":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("arena_menu"), Show("in_development")]
                        textbutton "Watch the fights":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("arena_menu"), Show("in_development")]
                        textbutton "Visit the Lanista":
                            xsize 500
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("arena_menu"), Hide("map_screen"), Jump("lanista_visit")]

    key "K_BACKSPACE" action [Hide("arena_menu"), Show("map_screen")]

screen arena_training_menu():
    modal True
    zorder 102
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action [Hide("arena_training_menu"), Hide("arena_menu"), Show("map_screen")]
        vbox:
            spacing 16
            vbox:
                xoffset 15
                spacing 16
                null height 10
                label "Send gladiators to fight" xalign 0.5 style "header_style"
                text "Assign workers to the Arena, then choose their role in Manage Workers: Exhibition fighter, Proving fighter, Championship fighter, or Pin up Barbarians. You can also assign workers to the Arena directly from Manage Workers—assign a worker to the Arena and choose their role there." size font_size(23) xalign 0.5 color "#6a5a3a" text_align 0.5 xmaximum 580
                null height 8
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 440
                xsize 635
                hbox:
                    spacing 0
                    null width 28
                    vbox:
                        spacing 14
                        xsize 535
                        textbutton "Assign workers to Arena":
                            xsize 515
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action [Hide("arena_training_menu"), Hide("arena_menu"), Hide("map_screen"), Show("workers"), Function(renpy.notify, "Assign workers to the Arena, then choose their role (Exhibition, Proving, Championship, or Pin up) in Manage Workers.")]

    key "K_BACKSPACE" action [Hide("arena_training_menu"), Hide("arena_menu"), Show("map_screen")]

screen buy_map_building(map_button_id):
    modal True
    zorder 100
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        # Close button in the top-right inside the panel
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action Hide("buy_map_building")
        
        vbox:
            spacing 15
            null height 15
            label "Purchase Building" xalign 0.5 style "header_style"
            text "Would you like to purchase this building? You could convert it into one of the following businesses:" size font_size(24) xalign 0.5 color gui.journal_text_color text_align 0.5
            null height 10
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 480
                xsize 605
                xoffset 25
                yoffset -20
                vbox:
                    spacing 10
                    xsize 580
                    yoffset 25
                    python:
                        available_businesses = get_available_businesses_for_map_button(map_button_id)
                        num = len(owned_buildings)
                        if "Tavern" in map_button_id:
                            price = 15000
                        elif "Bluehouse" in map_button_id:
                            price = 20000
                        elif "Redhouse" in map_button_id:
                            price = 25000
                        elif "Greenhouse" in map_button_id:
                            price = 30000
                        else:
                            price = 20000
                        building_name = f"Building {str(num + 1)}"
                    
                    if num < max_building:
                        if len(available_businesses) > 0:
                            for btype in available_businesses:
                                textbutton "[btype['name']] - $[price]":
                                    xsize 500
                                    text_size font_size(28)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action If(money >= price,
                                        [
                                            Function(add_new_building, building_name, price),
                                            SetVariable("money", money - price),
                                            Function(lambda bn=building_name, bt=btype["id"]: available_buildings[bn].update({"type": bt}) if bn in available_buildings else None),
                                            Function(register_new_building, building_name),
                                            Function(store.map_button_buildings.__setitem__, map_button_id, building_name),
                                            SetVariable("buildings_owned", len(store.owned_buildings)),
                                            Hide("buy_map_building"),
                                            Hide("map_screen"),
                                            Function(renpy.notify, f"Purchased {building_name} as {btype['name']}!"),
                                            Show("Manager", building_name=building_name)
                                        ],
                                        Show("error_popup", message=f"Not enough money. Cost: ${price}")
                                    )
                                    sensitive (money >= price)
                        else:
                            text "No businesses available for this location." size font_size(28) xalign 0.5 color gui.journal_text_color
                    else:
                        text "No more buildings available to purchase." size font_size(28) xalign 0.5 color gui.journal_text_color

    key "K_BACKSPACE" action Hide("buy_map_building")

screen buy_servants_table():
    zorder 90
    modal True
    
    on "show" action Function(_ensure_buy_workers_loaded)
    default _buy_servants_initialized = False
    if not _buy_servants_initialized:
        $ _buy_servants_initialized = True
        $ _ensure_buy_workers_loaded()
    
    add Solid("#00000099")
    frame:
        xalign 0.5
        yalign 0.5
        xsize 1344
        ysize 768
        background Transform("gui/gallery.png", xysize=(1344, 768))
        padding (20, 20)
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("buy_servants_table")
            xalign 1.0
            yalign 0.0
            xoffset -85
            yoffset 85
            
        vbox:
            xalign 0.5
            spacing 15
            null height 80
            fixed:
                xsize 870
                ysize 50
                label "Buy Servants" xalign 0.5 yalign 0.5 style "header_style"
                # Refresh button (right side)
                python:
                    # Check if it's a new day - reset counter if so
                    if store.last_map_refill_day != store.current_day:
                        store.map_worker_refill_count = 0
                        store.last_map_refill_day = store.current_day
                    
                    # Use store variable to ensure consistency
                    refresh_count = store.map_worker_refill_count
                    can_refresh = refresh_count < 2
                    has_money = hasattr(store, 'money') and store.money >= 2500
                    
                    # Calculate button text based on refresh count
                    if refresh_count == 0:
                        refresh_text = "Refresh (Free)"
                    elif refresh_count == 1:
                        refresh_text = "Refresh ($2500)"
                    else:
                        refresh_text = "Refresh (Limit reached)"
                    
                    # Can only refresh if under limit AND (free OR has money for paid)
                    can_refresh = can_refresh and (refresh_count == 0 or (refresh_count == 1 and has_money))
                
                # Dynamic button text and action based on refresh count
                textbutton "[refresh_text]":
                    xalign 1.0
                    yalign 0.5
                    style "game_menu_button"
                    text_size font_size(24)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                    action If(
                        store.map_worker_refill_count == 0,
                        Function(store.refresh_buy_workers),
                        If(
                            store.map_worker_refill_count == 1,
                            Show("confirm_refresh_workers"),
                            NullAction()
                        )
                    )
                    sensitive can_refresh
            null height 10
            
            # Gender filter only when global Worker Gender is "Both"; hidden for "Only Male" / "Only Female"
            if getattr(persistent, "worker_gender_filter", "both") == "both":
                python:
                    _gf = getattr(store, "buy_servants_filter_gender", None)
                    _color_all = gui.journal_hover_color if _gf is None else gui.journal_text_color
                    _color_male = gui.journal_hover_color if _gf == "male" else gui.journal_text_color
                    _color_female = gui.journal_hover_color if _gf == "female" else gui.journal_text_color
                hbox:
                    xalign 0.5
                    spacing 15
                    text "Filter: " size font_size(24) color gui.journal_text_color yalign 0.5
                    textbutton "All":
                        style "game_menu_button"
                        text_size font_size(24)
                        text_color _color_all
                        text_hover_color gui.journal_hover_color
                        action [SetVariable("buy_servants_filter_gender", None), Function(renpy.restart_interaction)]
                    textbutton "Male":
                        style "game_menu_button"
                        text_size font_size(24)
                        text_color _color_male
                        text_hover_color gui.journal_hover_color
                        action [SetVariable("buy_servants_filter_gender", "male"), Function(renpy.restart_interaction)]
                    textbutton "Female":
                        style "game_menu_button"
                        text_size font_size(24)
                        text_color _color_female
                        text_hover_color gui.journal_hover_color
                        action [SetVariable("buy_servants_filter_gender", "female"), Function(renpy.restart_interaction)]
                null height 5
            
            # Header: plain labels over ONE hairline (the unified table-header
            # system shared with the workers roster and the daily report).
            # GEOMETRY: row content is 52 (framed portrait) + 4x200 (columns) + 4x30 (gaps) = 972.
            # Container budget: frame 1344 - padding 2x20 - parchment art border ~2x25 = ~1254,
            # so the extra 82px fits without shrinking any text column.
            vbox:
                spacing 6
                xalign 0.5
                hbox:
                    spacing 30
                    xsize 972
                    yalign 0.5
                    # Spacer over the portrait column so headers stay aligned with rows
                    # (same null-width technique as the workers roster header).
                    null width 52
                    button:
                        background None
                        xsize 200
                        ysize 30
                        text "Name" size 28 color gui.journal_text_color text_align 0.0
                        sensitive False
                    button:
                        background None
                        xsize 200
                        ysize 30
                        text "Price" size 28 color gui.journal_text_color text_align 0.0
                        sensitive False
                    button:
                        background None
                        xsize 200
                        ysize 30
                        text "Trait" size 28 color gui.journal_text_color text_align 0.0
                        sensitive False
                    button:
                        background None
                        xsize 200
                        ysize 30
                        text "Actions" size 28 color gui.journal_text_color text_align 0.0
                        sensitive False
                use table_rule(972, rule_xalign=0.5)
                
            
            # Main content area: when global Worker Gender is Only Male/Female, list is already filtered; else use local filter
            python:
                _global_gender = getattr(persistent, "worker_gender_filter", "both")
                if _global_gender != "both":
                    filtered_displayed_workers = list(displayed_workers)
                else:
                    _gender_filter = getattr(store, "buy_servants_filter_gender", None)
                    filtered_displayed_workers = [w for w in displayed_workers if (_gender_filter is None or w.get("gender") == _gender_filter)]
            if not filtered_displayed_workers and displayed_workers:
                text "No workers match the selected filter." size font_size(22) color gui.journal_text_color xalign 0.5
            else:
                vbox:
                    xalign 0.5
                    spacing 12
                    for worker in filtered_displayed_workers:
                        $ _buy_nav_names = [w.get("name") for w in filtered_displayed_workers if hasattr(w, "get") and w.get("name")]
                        $ _buy_nav_index = next((idx for idx, n in enumerate(_buy_nav_names) if n == worker.get("name")), 0)
                        $ _row_portrait = get_worker_portrait_cached(worker)
                        $ _row_initial = (str(worker.get("name", "")).strip() or "?")[:1]
                        hbox:
                            xalign 0.5
                            spacing 30
                            xoffset 0
                            xsize 972
                            yalign 0.5
                            # Framed portrait miniature (cached lookup; letter placeholder without art)
                            use worker_portrait_thumb(_row_portrait, _row_initial)
                            button:
                                background "images/tablebutton1b.png"
                                xsize 200
                                ysize 50
                                text "[worker['name']] [('(M)' if worker.get('gender', '') == 'male' else '(F)' if worker.get('gender', '') == 'female' else '(?)')]" size 26 color gui.journal_text_color hover_color gui.journal_hover_color text_align 0.0
                                action Show("worker_details", worker=worker, in_roster=False, from_buy_workers=True, nav_worker_names=_buy_nav_names, nav_worker_index=_buy_nav_index, nav_worker_pool=filtered_displayed_workers)
                            button:
                                background "images/tablebutton1b.png"
                                xsize 200
                                ysize 50
                                text "$[worker['cost']]" size 26 color gui.journal_text_color text_align 0.0
                            button:
                                background "images/tablebutton1b.png"
                                xsize 200
                                ysize 50
                                $ trait_text = ", ".join(worker.get("traits", [])[:2]) if worker.get("traits") else "No Traits"
                                text "[trait_text]" size 20 color gui.journal_text_color text_align 0.0
                            button:
                                background "images/tablebutton1b.png"
                                xsize 200
                                ysize 50
                                text "Buy" size 26 color gui.journal_text_color hover_color gui.journal_hover_color text_align 0.0
                                action Show("confirm_buy_worker", worker=worker)
                                sensitive (money >= worker["cost"])

    key "K_BACKSPACE" action Hide("buy_servants_table")


screen shop_selection():
    modal True
    zorder 100
    
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        # Close button in the top-right inside the panel
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
            action Hide("shop_selection")

        vbox:
            spacing 15
            null height 15
            label "Select a Shop" xalign 0.5 style "header_style"
            null height 10
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 480
                xsize 605
                xoffset 25
                yoffset -20
                vbox:
                    spacing 10
                    xsize 580
                    yoffset 25
                    $ shop1_name = "Basic Shop" if unlocked_shops.get("shop1", False) else "Basic Shop (Closed)"
                    textbutton "[shop1_name]":
                        action [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop1"), Hide("shop_selection")]
                        xsize 500
                        text_size font_size(28)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                        sensitive "shop1" in unlocked_shops and unlocked_shops["shop1"]
                    $ shop2_name = "Adventurer's Market" if unlocked_shops.get("shop2", False) else "Adventurer's Market (Closed)"
                    textbutton "[shop2_name]":
                        action [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop2"), Hide("shop_selection")]
                        xsize 500
                        text_size font_size(28)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                        sensitive "shop2" in unlocked_shops and unlocked_shops["shop2"]
                    $ shop3_name = "Elite Emporium (Closed)" if not unlocked_shops.get("shop3", False) else "Elite Emporium"
                    textbutton "[shop3_name]":
                        action [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop3"), Hide("shop_selection")]
                        xsize 500
                        text_size font_size(28)
                        text_color gui.journal_text_color
                        text_hover_color gui.journal_hover_color
                        sensitive "shop3" in unlocked_shops and unlocked_shops["shop3"]

    key "K_BACKSPACE" action Hide("shop_selection")

screen more_details_screen(worker):
    modal True
    zorder 99
    add Solid(gui.surface_dark)
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    frame:
        xalign 0.5
        yalign 0.5
        background None
        xsize 720
        ysize 720
        padding (40, 40)
        
        # Close button positioned like journal (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("more_details_screen")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
        
        vbox:
            spacing 15
            null height 15  # Push title down like journal
            label "More Details" xalign 0.5 style "header_style"
            null height 10  # Less space after title like journal
            
            vbox:
                xsize 640  # Match journal content width
                spacing 15
                xoffset 30  # Match journal content offset
                yoffset 25
                
                text "Description:" size font_size(20) color gui.journal_text_color xalign 0.0
                text "[worker.get('description', 'No description available')]" size font_size(20) color gui.journal_text_color xalign 0.0 text_align 0.0

                null height 10

                text "Folder: [worker.get('folder', 'default')]" size font_size(20) color gui.journal_text_color xalign 0.0
                
                null height 10
                
                if worker.get('procedural', False):
                    text "Type: Procedural Worker" size font_size(20) color gui.journal_text_color xalign 0.0
                else:
                    text "Type: Predefined Character" size font_size(20) color gui.journal_text_color xalign 0.0

    key "K_BACKSPACE" action Hide("more_details_screen")

init python:
    def _apply_discipline_final_and_close(worker, trait_name, close_actions):
        """Apply discipline finale choice (Harem Member or House Servant) and close the interaction."""
        worker.setdefault("flags", {})
        worker["flags"]["discipline_final_done"] = {"value": True, "duration": -1}
        store.add_trait_with_duration(worker, trait_name, 0)
        store.set_attribute_with_caps(worker, "rebelliousness", worker.get("rebelliousness", 0))
        renpy.notify("Trait gained: " + trait_name)
        for a in close_actions:
            renpy.run(a)

screen interaction_result(worker, interaction, message_index=0, show_image_only=False, return_to_map=False, frozen_media=None, from_call_screen=False):
    modal True
    zorder 120
    # Advance with screen variables — do NOT Show() this screen again on each click (that was causing flicker).
    default ir_idx = 0
    default ir_img_only = False
    # Resolve background media once per screen show so clicks through dialogue do not re-roll random art.
    default ir_resolved_media = frozen_media if frozen_media is not None else get_interaction_image(worker, interaction)
    on "show" action [
        SetScreenVariable("ir_idx", message_index),
        SetScreenVariable("ir_img_only", show_image_only),
    ]
    python:
        # Training uses `call screen`: must end with Return() so execution continues after `call screen` and
        # training_restore_ui_after_result runs. Hide() alone leaves the call pending — only the black backdrop remains.
        # Detect training by store flag (set before each call) OR interaction data — avoids wrong branch if flag hiccups.
        # Never run friendship tutorial lambdas + check_objective_completion here: call_in_new_context can break this stack.
        # Close with Return(0), not bare Return(): Ren'Py's Return(None) treats None specially and can ShowMenu(main_menu).
        _ir_training_flow = bool(getattr(store, "_training_interaction_result_active", False)) or is_training_interaction(interaction)
        _ir_desc = interaction.get("description") or "No description available."
        if is_training_interaction(interaction):
            _ir_res = training_resolved_training_description(worker, interaction)
            if _ir_res:
                _ir_desc = _ir_res
        # Pre-escape stray [..]/{..} from JSON text BEFORE the legit {color=} stat tag is
        # appended below, so display_message can't hit interpolation twice (BIBLIA §9).
        _ir_desc = str(_ir_desc).replace("{", "{{").replace("[", "[[")
        interaction_messages = split_text_for_dialogue(_ir_desc)
        total_messages = len(interaction_messages)
        is_last_message = (total_messages > 0 and ir_idx >= total_messages - 1)
        
        # Special-case: Romance finale (Confess Feelings) -> show a choice at the end
        interaction_id = interaction.get("id", "") or ""
        is_romance_confess = "_confess" in interaction_id and interaction_id.startswith("romance_level5_")
        is_friendship_final = interaction_id == "friendship_level5"
        is_discipline_final_harem = interaction_id == "discipline_level5_finale_harem_member"
        is_discipline_final_servant = interaction_id == "discipline_level5_finale_house_servant"
        is_discipline_final = is_discipline_final_harem or is_discipline_final_servant
        is_discipline_sell = interaction_id == "discipline_level5_sell_specialty_buyer"

        sale_price = None
        if is_discipline_sell:
            try:
                sale_price = store.calculate_specialty_buyer_sale_price(worker)
            except Exception:
                sale_price = 0
        
        # Get stat changes for display
        stat_changes = getattr(store, '_last_interaction_changes', {})
        stat_display_names = {
            "relationship": "Relation",
            "obedience": "Obedience",
            "joy": "Joy",
            "romance": "Romance",
            "libido": "Libido",
            "rebelliousness": "Rebelliousness",
            "energy": "Energy",
            "health": "Health",
            "money": "Money",
        }
        # Build stat change text
        stat_change_text = ""
        if stat_changes:
            change_parts = []
            for stat, change in stat_changes.items():
                if stat in ("traits_from_training", "traits_removed_by_chance"):
                    continue
                sstat = str(stat)
                if sstat.startswith("skill_uses_"):
                    try:
                        su = int(change or 0)
                    except (TypeError, ValueError):
                        su = 0
                    if su != 0:
                        sk_label = sstat[len("skill_uses_") :]
                        change_parts.append("+%d %s training" % (su, sk_label))
                    continue
                if hasattr(change, "get") or (hasattr(change, "__iter__") and not isinstance(change, str)):
                    continue
                try:
                    chv = int(change)
                except (TypeError, ValueError):
                    continue
                if stat in stat_display_names and chv != 0:
                    sign = "+" if chv > 0 else ""
                    change_parts.append(f"{sign}{chv} {stat_display_names[stat]}")
            if change_parts:
                stat_change_text = " | ".join(change_parts)
            _tg = stat_changes.get("traits_from_training") if stat_changes else None
            if _tg:
                _suffix = " | ".join("+%s trait" % str(tn) for tn in _tg)
                stat_change_text = (stat_change_text + " | " + _suffix) if stat_change_text else _suffix
            _trm = stat_changes.get("traits_removed_by_chance") if stat_changes else None
            if _trm:
                _suffix_rm = " | ".join("-%s trait" % str(tn) for tn in _trm)
                stat_change_text = (stat_change_text + " | " + _suffix_rm) if stat_change_text else _suffix_rm
        
        if ir_img_only:
            show_dialogue = False
            if return_to_map:
                close_action = [
                    Hide("interaction_result"),
                    Hide("interaction_menu"),
                    Show("map_screen"),
                    Function(lambda: setattr(store, '_last_interaction_changes', {}))
                ]
            else:
                if _ir_training_flow:
                    close_action = [
                        Function(lambda: setattr(store, '_last_interaction_changes', {})),
                        Return(0),
                    ]
                elif from_call_screen:
                    close_action = [
                        Function(lambda: setattr(store, '_last_interaction_changes', {})),
                        Function(lambda i=interaction: setattr(store, 'tutorial_friendly_chat_done', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None),
                        Function(lambda i=interaction: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None),
                        Return(),
                    ]
                else:
                    close_action = [
                        Hide("interaction_result"),
                        Hide("interaction_menu"),
                        Show("worker_details", worker=worker, in_roster=True),
                        Function(lambda: setattr(store, '_last_interaction_changes', {})),
                        Function(lambda i=interaction: setattr(store, 'tutorial_friendly_chat_done', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None),
                        Function(lambda i=interaction: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None)
                    ]
            sale_close_action = [
                Hide("interaction_result"),
                Hide("interaction_menu"),
                Hide("worker_details"),
                Show("tavern"),
                Function(lambda: setattr(store, "_last_interaction_changes", {}))
            ]
        else:
            show_dialogue = True
            display_message = interaction_messages[ir_idx] if ir_idx < total_messages else (interaction_messages[-1] if interaction_messages else "No description available.")
            if is_last_message and stat_change_text:
                display_message = display_message + " {color=#2a7a4b}(" + stat_change_text + "){/color}"
            if total_messages == 0:
                click_action = SetScreenVariable("ir_img_only", True)
            elif ir_idx < total_messages - 1:
                click_action = SetScreenVariable("ir_idx", ir_idx + 1)
            else:
                click_action = SetScreenVariable("ir_img_only", True)

        # Shared close action: used by BOTH the top-right Return button and the
        # K_BACKSPACE key at the bottom of this screen, so the two can never drift.
        _ir_close_action = If(
            is_romance_confess or is_friendship_final or is_discipline_final or is_discipline_sell,
            NullAction(),
            If(
                return_to_map,
                If(
                    _ir_training_flow,
                    [
                        Function(lambda: setattr(store, '_last_interaction_changes', {})),
                        Return(0),
                    ],
                    If(
                        from_call_screen,
                        [
                            Function(lambda: setattr(store, '_last_interaction_changes', {})),
                            Return(),
                        ],
                        [
                            Hide("interaction_result"),
                            Hide("interaction_menu"),
                            Show("map_screen"),
                            Function(lambda: setattr(store, '_last_interaction_changes', {}))
                        ],
                    ),
                ),
                If(
                    _ir_training_flow,
                    [
                        Function(lambda: setattr(store, '_last_interaction_changes', {})),
                        Return(0),
                    ],
                    If(
                        from_call_screen,
                        [
                            Function(lambda: setattr(store, '_last_interaction_changes', {})),
                            Function(lambda i=interaction: setattr(store, 'tutorial_friendly_chat_done', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None),
                            Function(lambda i=interaction: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None),
                            Return(),
                        ],
                        [
                            Hide("interaction_result"),
                            Hide("interaction_menu"),
                            Show("worker_details", worker=worker, in_roster=True),
                            Function(lambda: setattr(store, '_last_interaction_changes', {})),
                            Function(lambda i=interaction: setattr(store, 'tutorial_friendly_chat_done', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None),
                            Function(lambda i=interaction: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('name', '').strip() in ("Friendly Chat", "Friendly Lunch") or i.get('id') in ("friendship_chat_female", "friendship_chat_male", "friendship_level1", "friendship_level1_lord_female", "friendship_level1_lord_male_platonic", "friendship_level1_lady_female_platonic", "friendship_level1_lady_male")) else None)
                        ],
                    ),
                )
            )
        )

    $ _ir_sw, _ir_sh = config.screen_width, config.screen_height
    $ media_file = ir_resolved_media
    fixed:
        xfill True
        yfill True
        add Solid("#000000"):
            xsize _ir_sw
            ysize _ir_sh
        if media_file and isinstance(media_file, str) and media_file.lower().endswith(('.webm', '.mp4')):
            add Movie(
                play=media_file,
                size=(1920, 1080),
                loop=True
            )
        elif media_file:
            add media_file:
                xalign 0.5
                yalign 0.5
                fit "contain"
                xysize (1920, 1080)

    # Full-viewport click layer (same fixed tree as CG so no uncovered strips)
    if show_dialogue:
        fixed:
            xfill True
            yfill True
            button:
                xfill True
                yfill True
                background None
                action click_action
                
                # Dialogue box at the bottom (non-interactive, just display)
                window:
                    id "window"
                    style "say_window"
                    xalign 0.5
                    xfill True
                    yalign gui.textbox_yalign
                    ysize gui.textbox_height
                    
                    text display_message:
                        id "what"
                        xpos gui.dialogue_xpos
                        xsize gui.dialogue_width
                        yalign 0.5
    else:
        # Image-only mode:
        # - Normally: whole screen is clickable to close.
        # - Finale/confirm overlays: keep the image on-screen and show a choice instead.
        fixed:
            xfill True
            yfill True
            if is_romance_confess or is_friendship_final or is_discipline_final or is_discipline_sell:
                button:
                    xfill True
                    yfill True
                    background None
                    action NullAction()
            else:
                button:
                    xfill True
                    yfill True
                    background None
                    action close_action
    
    # Romance finale choice overlay (same style as event/recruitment choices)
    if ir_img_only and is_romance_confess:
        vbox:
            style_prefix "choice"
            xalign 0.5
            yalign 0.85
            spacing gui.choice_spacing
            textbutton "Make it official: gain trait (Earnings x1.15, Libido cap 5, Rebelliousness cap 20).":
                action ([
                    Function(lambda w=worker: w.setdefault("flags", {}).update({"romance_confess_done": {"value": True, "duration": -1}})),
                    Function(add_trait_with_duration, worker, "Loves you", 0),
                    Function(lambda w=worker: set_attribute_with_caps(w, "libido", w.get("libido", 0))),
                    Function(lambda w=worker: set_attribute_with_caps(w, "rebelliousness", w.get("rebelliousness", 0))),
                    Function(lambda: renpy.notify("Trait gained: Loves you")),
                ] + close_action)
            textbutton "Keep it private: set Rebelliousness to 0 and gain +40 Joy.":
                action ([
                    Function(lambda w=worker: w.setdefault("flags", {}).update({"romance_confess_done": {"value": True, "duration": -1}})),
                    Function(lambda w=worker: set_attribute_with_caps(w, "rebelliousness", 0)),
                    Function(lambda w=worker: apply_attribute_change(w, "joy", 40)),
                    Function(lambda: renpy.notify("You keep it private. (+40 Joy, Rebelliousness set to 0)")),
                ] + close_action)

    # Friendship finale choice overlay (same style as event/recruitment choices)
    if ir_img_only and is_friendship_final:
        vbox:
            style_prefix "choice"
            xalign 0.5
            yalign 0.85
            spacing gui.choice_spacing
            textbutton "Make it permanent: gain trait (Daily +1 Joy; +2 Energy/day, +5 Max Energy).":
                action ([
                    Function(lambda w=worker: w.setdefault("flags", {}).update({"friendship_final_done": {"value": True, "duration": -1}})),
                    Function(add_trait_with_duration, worker, "Best Friends", 0),
                    Function(lambda: renpy.notify("Trait gained: Best Friends")),
                ] + close_action)
            textbutton "Keep it simple.":
                action close_action

    if ir_img_only and is_discipline_final:
        vbox:
            style_prefix "choice"
            xalign 0.5
            yalign 0.85
            spacing gui.choice_spacing
            if is_discipline_final_harem:
                textbutton "Assign their place: Harem Member.":
                    action Confirm(
                        "Assign this worker as Harem Member?",
                        Function(_apply_discipline_final_and_close, worker, "Harem Member", close_action)
                    )
            else:
                textbutton "Assign their place: House Servant.":
                    action Confirm(
                        "Assign this worker as House Servant?",
                        Function(_apply_discipline_final_and_close, worker, "House Servant", close_action)
                    )
            textbutton "Cancel.":
                action close_action

    # Discipline sale confirmation overlay (same style as event/recruitment choices). Only Confirm Sale or Cancel.
    if ir_img_only and is_discipline_sell:
        vbox:
            style_prefix "choice"
            xalign 0.5
            yalign 0.85
            spacing gui.choice_spacing
            textbutton "Confirm Sale. (Sale price: [sale_price])":
                action Confirm(
                    "Sell this worker to a specialty buyer?",
                    [
                        Function(lambda w=worker: setattr(store, "_last_sale_price", store.sell_worker_to_specialty_buyer(w))),
                        Function(lambda: renpy.notify("Sold to a specialty buyer for " + str(getattr(store, "_last_sale_price", 0)))),
                    ] + sale_close_action
                )
            textbutton "Cancel.":
                action close_action
    
    # Return button (top-right corner) - always available, on top of everything.
    # Action is the shared _ir_close_action computed in the python block above.
    imagebutton:
        idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        action _ir_close_action
        xalign 1.0
        yalign 0.0
        xoffset -15
        yoffset 5

    key "K_BACKSPACE" action _ir_close_action

screen take_a_walk_result(stage=0):
    # Screen to handle Take a Walk feature without nested call screen.
    # Stage 0: Show intro text 1
    # Stage 1: Show intro text 2
    # Stage 2: Show intro text 3
    # Stage 3+: Show interaction result with message navigation
    modal True
    zorder 99
    
    python:
        worker = store.walk_worker
        interaction = store.walk_interaction
        
        if stage == 0:
            # Stage 0: First intro text
            show_dialogue = True
            display_message = store.walk_intro_text_1
            next_action = Return("next")
            bg_image = None
        elif stage == 1:
            # Stage 1: Second intro text
            show_dialogue = True
            display_message = store.walk_intro_text_2
            next_action = Return("next")
            bg_image = None
        elif stage == 2:
            # Stage 2: Third intro text
            show_dialogue = True
            display_message = store.walk_intro_text_3
            next_action = Return("next")
            bg_image = None
        else:
            # Stage 3+: Show interaction result messages (one resolved image for the whole walk; set in start_take_a_walk).
            _walk_bg = getattr(store, "walk_interaction_media", None)
            if _walk_bg is None and worker and interaction:
                _walk_bg = get_interaction_image(worker, interaction)
                store.walk_interaction_media = _walk_bg
            interaction_messages = split_text_for_dialogue(interaction.get('description', 'No description available.'))
            message_index = stage - 3
            total_messages = len(interaction_messages)
            
            if message_index >= total_messages:
                # All messages shown, display image only
                show_dialogue = False
                display_message = ""
                next_action = Return("done")
                bg_image = _walk_bg
            else:
                # Show current message
                show_dialogue = True
                display_message = interaction_messages[message_index]
                next_action = Return("next")
                bg_image = _walk_bg

        # Escape stray [..]/{..} from JSON/worker-name text (per-render local; BIBLIA §9)
        if display_message:
            display_message = str(display_message).replace("{", "{{").replace("[", "[[")

    # Background
    if stage < 3:
        # Black background for intro text
        add Solid("#000000")
    else:
        # Dark overlay for interaction
        add Solid("#000000dd")
        
        # Show interaction image/video
        if bg_image and bg_image.lower().endswith(('.webm', '.mp4')):
            add Movie(
                play=bg_image,
                size=(1920, 1080),
                loop=True
            )
        elif bg_image:
            add bg_image:
                xalign 0.5
                yalign 0.5
                fit "contain"
                xysize (1920, 1080)
    
    # Make the whole screen clickable to advance
    if show_dialogue:
        button:
            xfill True
            yfill True
            background None
            action next_action
            
            # Dialogue box at the bottom
            window:
                id "window"
                style "say_window"
                xalign 0.5
                xfill True
                yalign gui.textbox_yalign
                ysize gui.textbox_height
                
                text display_message:
                    id "what"
                    style "say_dialogue"
                    xpos gui.dialogue_xpos
                    xsize gui.dialogue_width
                    ypos gui.dialogue_ypos
    else:
        # Image-only mode: click to close
        button:
            xfill True
            yfill True
            background None
            action next_action
    
    # Return button (top-right corner) - always available
    imagebutton:
        idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        action Return("done")
        xalign 1.0
        yalign 0.0
        xoffset -15
        yoffset 5

    key "K_BACKSPACE" action Return("done")

# Screens shown with call screen / renpy.call_screen: do not Hide(this_screen) before Return —
# that drops the call context and Return() can send the player to the main menu.
screen recruitment_outcome(message, event, outcome, message_index=0, show_image_only=False, frozen_bg=None):
    modal True
    zorder 99
    python:
        # Escape stray [..]/{..} from JSON text on a display copy only — the raw `message`
        # is re-passed through Show() on each click, so escaping it in place would stack (BIBLIA §9).
        outcome_messages = split_text_for_dialogue(str(message).replace("{", "{{").replace("[", "[["))
        current_message_index = message_index
        total_messages = len(outcome_messages)
        if show_image_only:
            show_dialogue = False
            close_action = [Return(True)]
        else:
            show_dialogue = True
            display_message = outcome_messages[current_message_index] if current_message_index < total_messages else outcome_messages[-1] if outcome_messages else "No message available."
            is_last_message = current_message_index >= total_messages - 1
            if is_last_message:
                click_action = Show(
                    "recruitment_outcome",
                    message=message,
                    event=event,
                    outcome=outcome,
                    message_index=current_message_index,
                    show_image_only=True,
                    frozen_bg=frozen_bg
                )
            else:
                click_action = Show(
                    "recruitment_outcome",
                    message=message,
                    event=event,
                    outcome=outcome,
                    message_index=current_message_index + 1,
                    show_image_only=False,
                    frozen_bg=frozen_bg
                )
    
    add Solid("#000000dd")

    # Get background image based on outcome with proper fallback chain
    python:
        # Keep one stable image through all clicks in this outcome sequence.
        bg_image = frozen_bg

        if not bg_image:
            candidate_worker = getattr(store, "current_recruitment_worker", None)
            if not (candidate_worker and hasattr(candidate_worker, "get")):
                candidate_worker = getattr(store, "current_worker", None)

            # Skill-check recruitments use the rich trait-aware lookup; everything else
            # delegates to get_recruitment_image (worker-folder convention + heuristics).
            if event.get("condition") and candidate_worker and hasattr(candidate_worker, "get"):
                outcome_key = "success" if outcome == "success" else ("failure" if outcome == "failure" else "default")
                try:
                    bg_image = get_event_image(candidate_worker, event, outcome=outcome_key, skill_name=event.get("condition"))
                except Exception as e:
                    renpy.log(f"recruitment_outcome get_event_image failed: {e}")

            if not bg_image or not renpy.loadable(bg_image):
                try:
                    bg_image = get_recruitment_image(candidate_worker, outcome, event)
                except Exception as e:
                    renpy.log(f"recruitment_outcome get_recruitment_image failed: {e}")
                    bg_image = "images/event_bg.png"
    python:
        # Keep image stable across click-driven re-renders of this same outcome sequence.
        if show_dialogue:
            if current_message_index >= total_messages - 1:
                click_action = Show(
                    "recruitment_outcome",
                    message=message,
                    event=event,
                    outcome=outcome,
                    message_index=current_message_index,
                    show_image_only=True,
                    frozen_bg=bg_image
                )
            else:
                click_action = Show(
                    "recruitment_outcome",
                    message=message,
                    event=event,
                    outcome=outcome,
                    message_index=current_message_index + 1,
                    show_image_only=False,
                    frozen_bg=bg_image
                )
    
    # Show the background image (full screen)
    add bg_image:
        xalign 0.5
        yalign 0.5
        fit "contain"
        xysize (1920, 1080)
    
    # Make the whole screen clickeable to advance dialogue (but dialogue box renders on top)
    if show_dialogue:
        button:
            xfill True
            yfill True
            background None
            action click_action
            
            # Dialogue box at the bottom (non-interactive, just display)
            window:
                id "window"
                style "say_window"
                xalign 0.5
                xfill True
                yalign gui.textbox_yalign
                ysize gui.textbox_height
                
                text display_message:
                    id "what"
                    style "say_dialogue"
                    xpos gui.dialogue_xpos
                    xsize gui.dialogue_width
                    ypos gui.dialogue_ypos
    else:
        # Image-only mode: make the whole screen clickeable to close
        button:
            xfill True
            yfill True
            background None
            action close_action
    
    # Return button (top-right corner) - always available, on top of everything
    imagebutton:
        idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
        action Return(True)
        xalign 1.0
        yalign 0.0
        xoffset -15
        yoffset 5

    key "K_BACKSPACE" action Return(True)

screen adjust_comfort(worker):
    modal True
    zorder 100
    add Transform("gui/Journalback.png", align=(0.5, 0.5))
    
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 720
        background None
        padding (40, 40)
        
        $ current_comfort = worker["comfort_level"]
        $ current_comfort_desired = get_effective_comfort_desired(worker)
        python:
            _cmu = get_difficulty_comfort_mult()
            current_daily_cost = int(round(current_comfort * _cmu))
            next_daily_cost = int(round((current_comfort + 1) * _cmu)) if current_comfort < 20 else current_daily_cost
            prev_daily_cost = int(round(max(1, current_comfort - 1) * _cmu)) if current_comfort > 1 else current_daily_cost
        $ current_relationship = worker.get("relationship", 10 + current_comfort)
        
        viewport:
            xsize 640
            ysize 640
            xalign 0.5
            yoffset 0
            scrollbars None
            mousewheel True
            draggable True

            vbox:
                spacing 15
                null height 15
                label "Worker Comfort" xalign 0.5 style "header_style"
                vbox:
                    xsize 580
                    spacing 10
                    xoffset 30
                    # Tightened vertical rhythm so the Adjust Comfort row fits inside
                    # the 640px viewport without scrolling (user request).

                    # Comfort description
                    text "Comfort determines the quality of life and accommodations provided to your worker. Higher comfort levels improve worker satisfaction and relationship. Comfort level 1 is the minimum; each level above 1 adds +1 to daily energy regeneration at day start, but increases daily maintenance costs. Desired Comfort is the worker's personal baseline set by recruitment/template data and can be affected by traits. Changing worker JSON affects new recruits, not already-hired workers in your current save." size font_size(24) color gui.journal_text_color text_align 0.0 xalign 0.0

                    null height 8

                    # Current status section
                    vbox:
                        spacing 8
                        
                        text "Current Status:" size font_size(26) color gui.journal_text_color bold True
                        text "• Comfort Level: [current_comfort]" size font_size(24) color gui.journal_text_color
                        text "• Desired Comfort: [current_comfort_desired]" size font_size(24) color gui.journal_text_color
                        button:
                            background None
                            padding (0, 0)
                            xalign 0.0
                            action NullAction()
                            hovered If(get_tooltips_state_for_screen("adjust_comfort"), ShowTransient("tooltip", message=get_building_comfort_line_tooltip(), screen_name="adjust_comfort"), NullAction())
                            unhovered Hide("tooltip")
                            text "• Daily Cost: $[current_daily_cost]" size font_size(24) color gui.journal_text_color
                        text "• Relationship: [current_relationship]" size font_size(24) color gui.journal_text_color

                        null height 10

                        # Comfort adjustment with buttons
                        hbox:
                            xalign 0.0
                            spacing 10
                            text "Adjust Comfort:" size font_size(24) color gui.journal_text_color
                            hbox:
                                spacing 0
                                textbutton "+" style "game_menu_button":
                                    action [
                                        Function(lambda w=worker, c=current_comfort: adjust_comfort_and_recalculate_relationship(w, c + 1))
                                    ]
                                    xsize 25
                                    text_size font_size(28)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    text_bold True
                                    text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                                    sensitive current_comfort < 20
                                textbutton "-" style "game_menu_button":
                                    action [
                                        Function(lambda w=worker, c=current_comfort: adjust_comfort_and_recalculate_relationship(w, max(1, c - 1)))
                                    ]
                                    xsize 25
                                    text_size font_size(28)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    text_bold True
                                    text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                                    sensitive current_comfort > 1
                            if current_comfort < 20:
                                button:
                                    background None
                                    padding (8, 0)
                                    xalign 0.0
                                    action NullAction()
                                    hovered If(get_tooltips_state_for_screen("adjust_comfort"), ShowTransient("tooltip", message=get_building_comfort_line_tooltip(), screen_name="adjust_comfort"), NullAction())
                                    unhovered Hide("tooltip")
                                    text "Next Level Cost: $[next_daily_cost]/day" size font_size(24) color "#444444"
                            else:
                                text "Maximum Comfort Reached" size font_size(24) color "#1b5e20" xalign 0.0


        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("adjust_comfort")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

    key "K_BACKSPACE" action Hide("adjust_comfort")

screen interaction_menu(worker):
    modal True
    zorder 99
    $ _imenu_sw, _imenu_sh = config.screen_width, config.screen_height
    add Solid("#000000"):
        xsize _imenu_sw
        ysize _imenu_sh
    frame:
        style "interaction_frame"
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 15
            label "Interact with [worker['name']]" xalign 0.5 style "header_style"
            $ filtered_interactions = get_available_interactions_for_worker(worker)
            
            if not filtered_interactions:
                text "No interactions available for this worker." style "interaction_text" xalign 0.5
            else:
                $ categorized_interactions = categorize_interactions(filtered_interactions)
                
                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    draggable True
                    ysize 500
                    xsize 600
                    vbox:
                        spacing 10
                        # Display category buttons
                        for category_name, interactions_list in categorized_interactions.items():
                            textbutton "[category_name]":
                                style "interaction_button"
                                text_style "interaction_button_text"
                                action Show("interaction_category", worker=worker, category_name=category_name, 
                                          interactions_list=interactions_list)
                                xalign 0.0
                                text_xalign 0.0
            textbutton "Close":
                style "interaction_button"
                text_style "interaction_button_text"
                xalign 0.5
                action Hide("interaction_menu")

    key "K_BACKSPACE" action Hide("interaction_menu")

# New screen to display interactions in a specific category
screen interaction_category(worker, category_name, interactions_list):
    modal True
    zorder 100
    $ _icat_sw, _icat_sh = config.screen_width, config.screen_height
    add Solid("#000000"):
        xsize _icat_sw
        ysize _icat_sh
    frame:
        style "interaction_frame"
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 10
            label "[category_name] for [worker['name']]" xalign 0.0 style "header_style"
            $ progression_subtitle = get_category_progress_subtitle(worker, category_name)
            if progression_subtitle:
                text "[progression_subtitle]" style "interaction_text" size font_size(22) color "#5a4a2a" xalign 0.0
            
            # Show daily interaction limit info (manager pool: 2 + Manager Level)
            $ interaction_count = get_worker_interaction_count(worker)
            $ _max_interactions = get_max_daily_interactions()
            $ remaining_interactions = _max_interactions - interaction_count
            if remaining_interactions <= 0:
                text "Manager interaction limit reached ([interaction_count]/[_max_interactions]). Interactions disabled until next day." style "interaction_text" size font_size(24) color "#a63c3c" xalign 0.0
            else:
                text "Manager interactions remaining today: [remaining_interactions]/[_max_interactions]" style "interaction_text" size font_size(24) color gui.journal_text_color xalign 0.0
            
            null height 5  # Small spacing between message and interactions list
            
            # Normal category display
            viewport:
                    scrollbars "vertical"
                    mousewheel True
                    draggable True
                    ysize 500
                    xsize 600
                    vbox:
                        spacing 10
                        # Calculate interaction count once for all interactions (manager pool)
                        $ interaction_count = get_worker_interaction_count(worker)
                        $ can_interact = can_interact_with_worker(worker)
                        $ remaining_interactions = get_max_daily_interactions() - interaction_count
                        for interaction in interactions_list:
                            vbox:
                                spacing 5
                                vbox:
                                    spacing 2
                                    textbutton "[interaction['name']]":
                                        style "interaction_button"
                                        text_style "interaction_button_text"
                                        action If(
                                            is_training_interaction(interaction),
                                            [
                                                Hide("interaction_category"),
                                                Hide("interaction_menu"),
                                                # Do not use Call() here: renpy.call from a live screen stacks badly with
                                                # nested call screen (interaction_result) and can dump to the main menu.
                                                # Same pattern as arena trial / alchemy: fresh context.
                                                Function(renpy.call_in_new_context, "training_interaction_menu_runner", worker, interaction),
                                                # Subcontext teardown drops screens shown inside it; parent still had menus.
                                                Function(training_resume_worker_details_after_context, worker),
                                            ],
                                            [
                                                Function(lambda w=worker, i=interaction: setattr(store, '_last_interaction_changes', apply_interaction_effects(w, i))),
                                                Show("interaction_result", worker=worker, interaction=interaction),
                                                Hide("interaction_category"),
                                            ],
                                        )
                                        sensitive (can_interact
                                                    and worker["energy"] >= interaction.get("cost_energy", 0)
                                                    and 
                                                    worker["health"] >= interaction.get("cost_health", 0) 
                                                    and
                                                    (interaction.get("cost_money", 0) <= 0 or store.money >= interaction.get("cost_money", 0))
                                                )
                                        xalign 0.0
                                        text_xalign 0.0

                                    if is_training_interaction(interaction):
                                        if training_primary_art_missing(worker, interaction):
                                            text "Image not found, fallback will be used" style "interaction_text" size font_size(20) color "#5a3a1a" xalign 0.0 xoffset 18 yoffset -10

                                if is_training_interaction(interaction) and training_primary_art_missing(worker, interaction):
                                    null height 14

                                # Show costs and effects below each interaction
                                vbox:
                                    spacing 3
                                    xalign 0.0
                                    $ _is_training_row = is_training_interaction(interaction)
                                    # Costs (training: no upfront energy/health/money; costs come from outcome only)
                                    if not _is_training_row:
                                        hbox:
                                            spacing 10
                                            xalign 0.0
                                            if interaction.get("cost_energy", 0) > 0:
                                                text "Energy: [interaction.get('cost_energy', 0)]" style "interaction_text" size font_size(20) color "#2c4aa6"
                                            if interaction.get("cost_health", 0) > 0:
                                                text "Health: [interaction.get('cost_health', 0)]" style "interaction_text" size font_size(20) color "#a63c3c"
                                            if interaction.get("cost_money", 0) > 0:
                                                text "Money: $[interaction.get('cost_money', 0)]" style "interaction_text" size font_size(20) color "#2a6b2a"
                                    # Effects (stats gained)
                                    $ effects = interaction.get("effect", {})
                                    hbox:
                                        spacing 10
                                        xalign 0.0
                                        # Fixed order + stable colors per stat (except Rebelliousness sign color)
                                        $ rom_val = effects.get("romance", 0)
                                        if rom_val != 0:
                                            $ rom_text = f"Romance: {rom_val:+d}"
                                            text "[rom_text]" style "interaction_text" size font_size(20) color "#c2185b"

                                        $ rel_val = effects.get("relationship", 0)
                                        if rel_val != 0:
                                            $ rel_text = f"Relationship: {rel_val:+d}"
                                            text "[rel_text]" style "interaction_text" size font_size(20) color "#1976d2"

                                        $ reb_val = effects.get("rebelliousness", 0)
                                        if reb_val != 0:
                                            $ reb_color = "#d32f2f" if reb_val < 0 else "#388e3c"
                                            $ reb_text = f"Rebelliousness: {reb_val:+d}"
                                            text "[reb_text]" style "interaction_text" size font_size(20) color reb_color

                                        # Joy last (secondary stat) + brown color for readability
                                        $ joy_val = effects.get("joy", 0)
                                        if joy_val != 0:
                                            $ joy_text = f"Joy: {joy_val:+d}"
                                            text "[joy_text]" style "interaction_text" size font_size(20) color gui.journal_text_color
                
            hbox:
                spacing 20
                xalign 0.5
                textbutton "Back":
                    style "interaction_button"
                    text_style "interaction_button_text"
                    action Hide("interaction_category")
                textbutton "Close":
                    style "interaction_button"
                    text_style "interaction_button_text"
                    action [Hide("interaction_category"), Hide("interaction_menu")]

    # Backspace mirrors the "Back" button (one level up), not the full "Close".
    key "K_BACKSPACE" action Hide("interaction_category")

# Persist worker details panel tab (main vs traits) when switching workers
default worker_details_panel_view = "main"

screen worker_details(worker, in_roster=False, from_buy_workers=False, from_recruitment=False, nav_worker_names=None, nav_worker_index=None, nav_worker_pool=None):
    on "show" action Function(maybe_show_intro_popup, "worker_details")
    # Guard: worker must not be None (use safe default to avoid crash)
    $ worker = worker if (worker and hasattr(worker, "get")) else {"name": "Unknown", "comfort_level": 1, "daily_cost": 0}
    # Ensure worker is updated with latest data from store.workers
    $ worker = next((w for w in store.workers if w["name"] == worker["name"]), worker)
    $ worker = ensure_worker_defaults(worker)
    $ sell_text = get_sell_text(worker)
    $ comfort_level = worker.get("comfort_level", 1)
    $ daily_cost = compute_single_worker_daily_charge(worker)
    default current_image = get_worker_image(worker)
    default details_view = worker_details_panel_view

    zorder 99
    modal True
    add Solid(gui.surface_dark)

    fixed:
        xfill True
        yfill True

        frame:
            xalign 0.5
            yalign 0.5
            xsize 1.0
            ysize 1.0
            background Transform("gui/gallery.png", xysize=(1920, 1080))
            padding (20, 20)

            # Return button (top-right inside the frame)
            imagebutton:
                idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                xalign 1.0
                yalign 0.0
                xoffset -125
                yoffset 125
                if from_recruitment:
                    # Store the worker and return to recruitment
                    action [SetVariable("temp_recruitment_worker", worker), SetVariable("in_recruit_examine", False), Hide("worker_details"), Function(return_to_recruitment)]
                else:
                    action Hide("worker_details")

            hbox:
                spacing 10
                xfill True
                yfill True

                # Left Column: Header + Bars above the image, then the image lowered 100px
                vbox:
                    xsize 1024
                    ysize 768
                    yalign 0.5
                    yoffset -65

                    # Image container (moved up since worker info is now on the right)
                    fixed:
                        xsize 970
                        ysize 710
                        xoffset 132
                        yoffset 69

                        if current_image:
                            add current_image:
                                xalign 0.5
                                yalign 0.5
                                yoffset 0
                                fit "contain"
                        else:
                            text "No Image Available" color "#ffffff" xalign 0.5 yalign 0.5

                    # Navigation Buttons (below image)
                    if in_roster or from_buy_workers:
                        # Prefer explicit navigation context from caller.
                        $ _fallback_roster = workers_filtered_by_gender(store.workers)
                        $ _fallback_names = [w.get("name") for w in _fallback_roster if hasattr(w, "get") and w.get("name")]
                        $ _context_pool = [w for w in (nav_worker_pool or []) if hasattr(w, "get")]
                        $ _context_names = [n for n in (nav_worker_names or []) if n]
                        if not _context_names:
                            $ _context_names = [w.get("name") for w in _context_pool if w.get("name")]
                        $ _nav_names = _context_names if _context_names else (_fallback_names if in_roster else [])
                        $ _current_name = worker.get("name")
                        $ _roster_idx = nav_worker_index if (nav_worker_index is not None and 0 <= nav_worker_index < len(_nav_names) and _nav_names[nav_worker_index] == _current_name) else next((i for i, n in enumerate(_nav_names) if n == _current_name), 0)
                        $ _prev_name = _nav_names[(_roster_idx - 1) % len(_nav_names)] if _nav_names else None
                        $ _next_name = _nav_names[(_roster_idx + 1) % len(_nav_names)] if _nav_names else None
                        $ _prev_worker = (next((w for w in store.workers if w.get("name") == _prev_name), None) if _prev_name else None) or (next((w for w in _context_pool if w.get("name") == _prev_name), worker) if _prev_name else worker)
                        $ _next_worker = (next((w for w in store.workers if w.get("name") == _next_name), None) if _next_name else None) or (next((w for w in _context_pool if w.get("name") == _next_name), worker) if _next_name else worker)
                        $ _prev_store_idx = next((i for i, w in enumerate(store.workers) if w.get("name") == _prev_name), 0) if _prev_name else 0
                        $ _next_store_idx = next((i for i, w in enumerate(store.workers) if w.get("name") == _next_name), 0) if _next_name else 0
                        hbox:
                            xalign 0.5
                            xoffset 90
                            yoffset 95
                            spacing 40
                            textbutton "Previous":
                                background None
                                text_size font_size(37)
                                text_color "#2a150d"
                                text_hover_color gui.journal_hover_color
                                action If(len(_nav_names) > 0, [
                                    SetVariable("current_worker_index", _prev_store_idx),
                                    SetScreenVariable("current_image", get_worker_image(_prev_worker)),
                                    Show("worker_details", worker=_prev_worker, in_roster=in_roster, from_buy_workers=from_buy_workers, from_recruitment=from_recruitment, nav_worker_names=_nav_names, nav_worker_index=(_roster_idx - 1) % len(_nav_names), nav_worker_pool=_context_pool)
                                ])
                                hovered ShowTransient("tooltip", message="Navigate to previous worker in this list.", screen_name="WorkerDetails")
                                unhovered Hide("tooltip")
                            textbutton "Next":
                                background None
                                text_size font_size(37)
                                text_color "#2a150d"
                                text_hover_color gui.journal_hover_color
                                action If(len(_nav_names) > 0, [
                                    SetVariable("current_worker_index", _next_store_idx),
                                    SetScreenVariable("current_image", get_worker_image(_next_worker)),
                                    Show("worker_details", worker=_next_worker, in_roster=in_roster, from_buy_workers=from_buy_workers, from_recruitment=from_recruitment, nav_worker_names=_nav_names, nav_worker_index=(_roster_idx + 1) % len(_nav_names), nav_worker_pool=_context_pool)
                                ])
                                hovered ShowTransient("tooltip", message="Navigate to next worker in this list.", screen_name="WorkerDetails")
                                unhovered Hide("tooltip")

                # Right Column: Panels (skills/stats) and actions
                vbox:
                    xsize 610
                    spacing 5
                    xoffset -20
                    yoffset 119
                    # (Name/level/bars moved to the left column)

                    # Worker Info (moved from left column) - ABOVE Switch to Stats
                    vbox:
                        xsize 540
                        spacing 5
                        yoffset 0
                        # Name + Level/XP/Comfort on a single row
                        hbox:
                            spacing 6
                            yalign 0.5
                            textbutton "[worker['name']]":
                                background None
                                text_size font_size(34)
                                text_color gui.journal_text_color
                                text_hover_color gui.journal_hover_color
                                action SetScreenVariable("current_image", get_pattern_matches_flexible(worker.get('folder', ''), "Profile", ["png", "jpg", "jpeg", "webp", "webm", "mp4"]) or get_worker_image(worker))
                                hovered ShowTransient("tooltip", message="Click to view worker's profile image.", screen_name="WorkerDetails")
                                unhovered Hide("tooltip")
                            button:
                                background None
                                yalign 0.5
                                yoffset 2
                                xoffset 5
                                action NullAction()
                                hovered ShowTransient("tooltip", message="Worker's current level. Higher levels unlock more interactions and improve performance.", screen_name="WorkerDetails")
                                unhovered Hide("tooltip")
                                text "Level: [worker.get('level', 1)]" size font_size(22) color "#ffffff" yalign 0.5
                            button:
                                background None
                                yalign 0.5
                                yoffset 2
                                xoffset 5
                                action NullAction()
                                hovered ShowTransient("tooltip", message="Experience points. Workers gain XP from successful daily activities. Reach the target to level up.", screen_name="WorkerDetails")
                                unhovered Hide("tooltip")
                                text "XP: [worker.get('success_count', 0)]/[20 * worker.get('level', 1)]" size font_size(22) color "#ffffff" yalign 0.5
                            if in_roster:
                                hbox:
                                    spacing 5
                                    yalign 0.5
                                    yoffset 2
                                    xoffset 5
                                    textbutton "Comfort: [comfort_level] - $[daily_cost]":
                                        background None
                                        text_size font_size(22)
                                        text_color gui.journal_text_color
                                        text_hover_color gui.journal_hover_color
                                        action Show("adjust_comfort", worker=worker)
                                        hovered ShowTransient("tooltip", message="Adjust worker comfort level. Daily worker cost is comfort x " + str(get_difficulty_comfort_mult()) + ". Building-level comfort scaling is applied in building totals (hover Costs on Manager for formulas).", screen_name="WorkerDetails")
                                        unhovered Hide("tooltip")
                                    python:
                                        screen_name = "WorkerDetails"
                                        tooltips_enabled = get_tooltips_state_for_screen(screen_name)
                                    imagebutton:
                                        idle Transform("gui/info_idle.png", zoom=0.4)
                                        hover Transform("gui/info_hover.png", zoom=0.4)
                                        selected_idle Transform("gui/info_active.png", zoom=0.4)
                                        selected_hover Transform("gui/info_active.png", zoom=0.4)
                                        selected tooltips_enabled
                                        yalign 0.5
                                        action Function(toggle_tooltips_for_screen, screen_name)
                                        hovered ShowTransient("tooltip", message="Tooltips: {color=#ffffff}On{/color}/Off", screen_name=screen_name)
                                        unhovered Hide("tooltip")
                        # Health and Energy Bars
                        # E/H color coherence: same rule as the workers roster (numbers turn
                        # gui.danger_color below 30% of calculated max). Full-size bars already
                        # exist here, so no extra 64x7 bars are added.
                        python:
                            _wd_max_e = calculate_max_energy(worker)
                            _wd_max_h = calculate_max_health(worker)
                            _wd_e_col = gui.danger_color if (_wd_max_e and int(worker.get("energy", 0) or 0) < 0.3 * _wd_max_e) else "#ffffff"
                            _wd_h_col = gui.danger_color if (_wd_max_h and int(worker.get("health", 0) or 0) < 0.3 * _wd_max_h) else "#ffffff"
                        hbox:
                            spacing 5
                            button:
                                background "#00000044"
                                xsize 200
                                ysize 40
                                padding (1, 0)
                                hovered ShowTransient("tooltip", message="Energy is consumed by daily activities. Daily energy regeneration formula: +Level + comfort bonus + trait bonus (level part = +1 per level, e.g. Lv1 +1, Lv5 +5). Use energy potions to restore more.", screen_name="WorkerDetails")
                                unhovered Hide("tooltip")
                                action NullAction()
                                fixed:
                                    xsize 192
                                    ysize 32
                                    xalign 0.5
                                    yalign 0.5
                                    bar:
                                        value worker["energy"]
                                        range calculate_max_energy(worker)
                                        xsize 192
                                        ysize 32
                                        left_bar gui.energy_bar_color  # token: same amber as the roster bars
                                        right_bar "#444444"
                                    text "Energy [worker['energy']]/[_wd_max_e]" size font_size(22) color _wd_e_col xalign 0.5 yalign 0.5
                            button:
                                background "#00000044"
                                xsize 200
                                ysize 40
                                padding (1, 0)
                                hovered ShowTransient("tooltip", message="Health decreases from dangerous activities or failures. Low health reduces performance. Maximum health and regeneration increase with level. Use health potions to restore.", screen_name="WorkerDetails")
                                unhovered Hide("tooltip")
                                action NullAction()
                                fixed:
                                    xsize 192
                                    ysize 32
                                    xalign 0.5
                                    yalign 0.5
                                    bar:
                                        value worker["health"]
                                        range calculate_max_health(worker)
                                        xsize 192
                                        ysize 32
                                        left_bar gui.health_bar_color  # token: same red as the roster bars
                                        right_bar "#444444"
                                    text "Health [worker['health']]/[_wd_max_h]" size font_size(22) color _wd_h_col xalign 0.5 yalign 0.5
                
                    # Auto-supply / Auto-equip
                    hbox:
                        spacing 8
                        yalign 0.0
                        textbutton "[details_view == 'main' and 'Switch to Traits' or 'Switch to Stats']":
                            text_size font_size(22)
                            yoffset -2
                            text_hover_color gui.journal_hover_color
                            action [
                                SetVariable("worker_details_panel_view", details_view == "main" and "traits" or "main"),
                                SetScreenVariable("details_view", details_view == "main" and "traits" or "main")
                            ]
                            hovered ShowTransient("tooltip", message="Flip panel between stats+skills and traits-only view.", screen_name="WorkerDetails")
                            unhovered Hide("tooltip")
                        textbutton "Stock Potions: [worker_auto_supply_compact_label(worker)]":
                            text_size font_size(22)
                            text_color "#3c2a1a"
                            text_hover_color gui.journal_hover_color
                            action Function(cycle_worker_auto_supply_compact, worker)
                            hovered ShowTransient("tooltip", message="Click to cycle: Off, then x3/x4/x5/x1/x2. When not Off, each day take that many health and energy potions from manager stock (up to limit per type).", screen_name="WorkerDetails")
                            unhovered Hide("tooltip")
                        textbutton "Auto-rest: [worker_auto_rest_compact_label(worker)]":
                            text_size font_size(22)
                            text_color "#3c2a1a"
                            text_hover_color gui.journal_hover_color
                            action Function(cycle_worker_auto_rest_compact, worker)
                            hovered ShowTransient("tooltip", message="Click to cycle: Off, 15%, 25%, 35%, 45%. When not Off, manager assigns Rest if energy OR health is below that % of max; return at 95% energy and health. When Off, leaving Rest only needs 95% energy.", screen_name="WorkerDetails")
                            unhovered Hide("tooltip")
                        textbutton "Auto Equip: [worker.get('auto_equip', False) and 'On' or 'Off']":
                            text_size font_size(22)
                            text_color "#3c2a1a"
                            text_hover_color gui.journal_hover_color
                            action Function(toggle_worker_auto_equip, worker)
                            hovered ShowTransient("tooltip", message="Equip best items for this worker's profession from manager inventory. Updates when job changes. Rest does not unequip.", screen_name="WorkerDetails")
                            unhovered Hide("tooltip")

                    # Flippable details panel
                    if details_view == "main":
                        frame:
                            background "#00000044"
                            xsize 600
                            ysize 585
                            padding (12, 10)
                            vbox:
                                spacing 8
                                $ _assigned_building = worker.get("assigned_building", "Unassigned")
                                $ _details_job_label = "Unassigned"
                                $ _details_building_label = "Unassigned: No Building"
                                if _assigned_building != "Unassigned" and _assigned_building in available_buildings:
                                    $ _details_building_data = available_buildings.get(_assigned_building, {})
                                    $ _details_btype_id = _details_building_data.get("type")
                                    $ _details_btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == _details_btype_id), None)
                                    $ _details_type_name = "Unassigned" if _details_btype_id is None else (_details_btype.get("name", _details_btype_id) if _details_btype else _details_btype_id)
                                    $ _details_parts = _assigned_building.split("_")
                                    $ _details_default_name = "Building " + _details_parts[1] if len(_details_parts) > 1 else _assigned_building
                                    $ _details_display_name = store.custom_names.get(_assigned_building, _details_default_name)
                                    $ _details_building_label = f"{_details_type_name}: {_details_display_name}"
                                    $ _details_job_id = (_details_building_data.get("servant_jobs") or {}).get(worker.get("name", ""), "Unassigned")
                                    $ _details_rpj = getattr(store, "resolve_profession_for_job", None)
                                    $ _details_job_label = (_details_rpj(_details_btype, _details_job_id)[0] if callable(_details_rpj) else str(_details_job_id))
                                hbox:
                                    spacing 4
                                    xalign 0.0
                                    text "Assignment:" size font_size(24) color "#3d2914" yalign 0.5
                                    textbutton "{u}[_details_job_label]{/u}":
                                        background None
                                        text_size font_size(24)
                                        text_color "#3d2914"
                                        text_hover_color gui.journal_hover_color
                                        action Show("job_selection", worker=worker)
                                        hovered ShowTransient("tooltip", message="Change this worker's role (profession), including Unassigned/Rest, using the same rules as Manage Workers.", screen_name="WorkerDetails")
                                        unhovered Hide("tooltip")
                                    text " - " size font_size(24) color "#3d2914" yalign 0.5
                                    textbutton "{u}[_details_building_label]{/u}":
                                        background None
                                        text_size font_size(24)
                                        text_color "#3d2914"
                                        text_hover_color gui.journal_hover_color
                                        action Show("building_selection", worker=worker, return_to_workers=False)
                                        hovered ShowTransient("tooltip", message="Move this worker to another building or set No Building, with the same synchronization as Manage Workers.", screen_name="WorkerDetails")
                                        unhovered Hide("tooltip")
                                $ _details_reb_cap = get_attribute_cap(worker, "rebelliousness")
                                $ _details_reb_cap_display = int(_details_reb_cap if _details_reb_cap is not None else 100)
                                $ _details_reb_bar_range = max(1, _details_reb_cap_display)
                                $ _details_lib_cap_display = int(get_max_libido(worker))
                                $ _details_lib_bar_range = max(1, _details_lib_cap_display)
                                python:
                                    _stats_items = [
                                        ("Rebelliousness", worker.get("rebelliousness", 0), _details_reb_cap_display, _details_reb_bar_range, "Rebelliousness increases from poor treatment or failures. Above 80, workers may refuse to work. Low joy (below 20) adds +2 daily; high joy (above 80) reduces it by 3."),
                                        ("Joy", worker.get("joy", 0), 100, 100, "Joy increases from comfort above desired and positive interactions. Above 80, reduces Rebelliousness by 3/day. Below 20, adds +2 Rebelliousness/day."),
                                        ("Romance", worker.get("romance", 0), 100, 100, "Romance builds through intimate interactions. High romance improves relationship and unlocks special interactions."),
                                        ("Relationship", worker.get("relationship", 0), 100, 100, "Relationship reflects the bond between you and this worker. Higher relationship improves loyalty and unlocks special interactions."),
                                    ]
                                    if persistent.nsfw_enabled:
                                        _stats_items.insert(3, ("Libido", worker.get("libido", 0), _details_lib_cap_display, _details_lib_bar_range, "Libido affects intimate interactions. High libido improves performance in NSFW activities."))
                                    _stats_left = _stats_items[::2]
                                    _stats_right = _stats_items[1::2]
                                hbox:
                                    spacing 10
                                    xalign 0.5
                                    vbox:
                                        spacing 8
                                        xsize 280
                                        for stat_name, stat_value, stat_max_display, stat_bar_range, stat_tooltip in _stats_left:
                                            button:
                                                background "#00000044"
                                                xsize 275
                                                ysize 38
                                                padding (1, 0)
                                                action NullAction()
                                                hovered ShowTransient("tooltip", message=stat_tooltip, screen_name="WorkerDetails")
                                                unhovered Hide("tooltip")
                                                fixed:
                                                    xsize 267
                                                    ysize 30
                                                    xalign 0.5
                                                    yalign 0.5
                                                    bar:
                                                        value stat_value
                                                        range stat_bar_range
                                                        xsize 267
                                                        ysize 30
                                                        left_bar gui.journal_hover_color
                                                        right_bar "#444444"
                                                    text "[stat_name]: [stat_value]/[stat_max_display]" size font_size(22) color "#ffffff" xalign 0.5 yalign 0.5
                                    vbox:
                                        spacing 8
                                        xsize 280
                                        for stat_name, stat_value, stat_max_display, stat_bar_range, stat_tooltip in _stats_right:
                                            button:
                                                background "#00000044"
                                                xsize 275
                                                ysize 38
                                                padding (1, 0)
                                                action NullAction()
                                                hovered ShowTransient("tooltip", message=stat_tooltip, screen_name="WorkerDetails")
                                                unhovered Hide("tooltip")
                                                fixed:
                                                    xsize 267
                                                    ysize 30
                                                    xalign 0.5
                                                    yalign 0.5
                                                    bar:
                                                        value stat_value
                                                        range stat_bar_range
                                                        xsize 267
                                                        ysize 30
                                                        left_bar gui.journal_hover_color
                                                        right_bar "#444444"
                                                    text "[stat_name]: [stat_value]/[stat_max_display]" size font_size(22) color "#ffffff" xalign 0.5 yalign 0.5

                                python:
                                    _skills = list(get_visible_skills(worker))
                                    _half = (len(_skills) + 1) // 2
                                    _skills_left = _skills[:_half]
                                    _skills_right = _skills[_half:]
                                text "Skills" size font_size(24) color "#2f1f13"
                                viewport:
                                    scrollbars None
                                    mousewheel True
                                    draggable True
                                    yfill True
                                    hbox:
                                        spacing 10
                                        xalign 0.5
                                        vbox:
                                            spacing 5
                                            xsize 280
                                            for skill_name, level in _skills_left:
                                                $ total_skill = calculate_skill_with_traits(worker, skill_name, include_libido=False)
                                                $ skill_uses = worker["skill_uses"].get(skill_name, 0)
                                                $ uses_needed = level
                                                $ skill_progress = skill_uses / float(uses_needed) if uses_needed > 0 else 0.0
                                                button:
                                                    background "#00000044"
                                                    xsize 275
                                                    ysize 36
                                                    padding (1, 0)
                                                    action SetScreenVariable("current_image", get_worker_image_random(worker, skill_name) or get_worker_image(worker))
                                                    hovered ShowTransient("tooltip", message="Click to view worker performing this skill. Progress bar shows current uses and uses required for next level.", screen_name="WorkerDetails")
                                                    unhovered Hide("tooltip")
                                                    fixed:
                                                        xsize 267
                                                        ysize 28
                                                        xalign 0.5
                                                        yalign 0.5
                                                        bar:
                                                            value skill_progress
                                                            range 1.0
                                                            xsize 267
                                                            ysize 28
                                                            left_bar "#7a7a7a"
                                                            right_bar "#444444"
                                                        text "[skill_name]: [total_skill]/100" size font_size(22) color "#ffffff" xalign 0.5 yalign 0.5 xmaximum 258
                                        vbox:
                                            spacing 5
                                            xsize 280
                                            for skill_name, level in _skills_right:
                                                $ total_skill = calculate_skill_with_traits(worker, skill_name, include_libido=False)
                                                $ skill_uses = worker["skill_uses"].get(skill_name, 0)
                                                $ uses_needed = level
                                                $ skill_progress = skill_uses / float(uses_needed) if uses_needed > 0 else 0.0
                                                button:
                                                    background "#00000044"
                                                    xsize 275
                                                    ysize 36
                                                    padding (1, 0)
                                                    action SetScreenVariable("current_image", get_worker_image_random(worker, skill_name) or get_worker_image(worker))
                                                    hovered ShowTransient("tooltip", message="Click to view worker performing this skill. Progress bar shows current uses and uses required for next level.", screen_name="WorkerDetails")
                                                    unhovered Hide("tooltip")
                                                    fixed:
                                                        xsize 267
                                                        ysize 28
                                                        xalign 0.5
                                                        yalign 0.5
                                                        bar:
                                                            value skill_progress
                                                            range 1.0
                                                            xsize 267
                                                            ysize 28
                                                            left_bar "#7a7a7a"
                                                            right_bar "#444444"
                                                        text "[skill_name]: [total_skill]/100" size font_size(22) color "#ffffff" xalign 0.5 yalign 0.5 xmaximum 258
                    else:
                        frame:
                            background "#00000044"
                            xsize 600
                            ysize 585
                            padding (12, 10)
                            vbox:
                                spacing 8
                                python:
                                    _filtered_traits = [t for t in worker.get("traits", []) if persistent.nsfw_enabled or any(t == tr["name"] and not tr.get("nsfw", False) for tr in traits_list)]
                                hbox:
                                    spacing 10
                                    xoffset 6
                                    fixed:
                                        xsize 150
                                        ysize 32
                                        text "Trait" size font_size(23) text_align 0.0 xalign 0.0 yalign 0.0 color gui.journal_dark_color
                                    fixed:
                                        xsize 320
                                        ysize 32
                                        text "Description" size font_size(23) text_align 0.0 xalign 0.0 xoffset 32 yalign 0.0 color gui.journal_dark_color
                                if _filtered_traits:
                                    viewport:
                                        scrollbars "vertical"
                                        mousewheel True
                                        draggable True
                                        xfill True
                                        ysize 485
                                        vbox:
                                            spacing 8
                                            for trait_idx, trait in enumerate(_filtered_traits):
                                                $ desc = get_trait_desc(trait)
                                                $ row_bg = "#00000033" if trait_idx % 2 == 0 else "images/tablebutton.png"
                                                frame:
                                                    background row_bg
                                                    xfill True
                                                    yminimum 40
                                                    padding (6, 6)
                                                    hbox:
                                                        spacing 10
                                                        xfill True
                                                        fixed:
                                                            xsize 150
                                                            yfit True
                                                            text "[trait]" size font_size(22) text_align 0.0 xalign 0.0 yalign 0.0 xsize 150 color gui.journal_dark_color
                                                        fixed:
                                                            xsize 320
                                                            yfit True
                                                            text "[desc]" size font_size(22) text_align 0.0 xalign 0.0 xsize 320 color gui.journal_dark_color
                                else:
                                    text "No traits" size font_size(22) color gui.journal_dark_color xalign 0.0 yalign 0.5

                    # Action Buttons Section
                    vbox:
                        spacing 3
                        xalign 0.5
                        yoffset -5
                        if in_roster:
                            hbox:
                                spacing 1
                                button:
                                    background "images/tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "Description" size font_size(23) xalign 0.5 hover_color gui.journal_hover_color
                                    action Show("more_details_screen", worker=worker)
                                button:
                                    background "images/tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "Inventory" size font_size(23) xalign 0.5 hover_color gui.journal_hover_color
                                    action [
                                        SetVariable("left_worker", None),
                                        SetVariable("right_worker", worker),
                                        Show(
                                            "manager_inventory",
                                            return_to_worker=worker,
                                            return_to_in_roster=in_roster,
                                            return_to_from_buy_workers=from_buy_workers,
                                            return_to_from_recruitment=from_recruitment
                                        ),
                                        Hide("worker_details")
                                    ]
                                    hovered ShowTransient("tooltip", message="Manage worker's inventory. Transfer items, equip gear, or use consumables to improve worker performance.", screen_name="WorkerDetails")
                                    unhovered Hide("tooltip")
                
                    # More Details and Sell Buttons (separate vbox for positioning)
                    vbox:
                        spacing 1
                        xalign 0.5
                        yoffset -20
                        if in_roster:
                            # QoL: repeat the last interaction launched this session, on THE
                            # CURRENTLY VIEWED worker. Only shown when that interaction id is
                            # currently available for this worker (same filter chain as the
                            # interaction menu) and re-launched through the exact same action
                            # path as the menu button, so all gating still applies.
                            python:
                                _rep_info = getattr(renpy, "session", {}).get("last_interaction_info")
                                _rep_interaction = None
                                _rep_can = False
                                _rep_tt = ""
                                if _rep_info and _rep_info.get("interaction_id"):
                                    _rep_interaction = next(
                                        (i for i in get_available_interactions_for_worker(worker)
                                         if hasattr(i, "get") and i.get("id") == _rep_info.get("interaction_id")),
                                        None,
                                    )
                                    # Training launches are not recorded (they run a cancelable
                                    # sub-flow in a fresh context); guard anyway.
                                    if _rep_interaction is not None and is_training_interaction(_rep_interaction):
                                        _rep_interaction = None
                                if _rep_interaction is not None:
                                    _rep_name = str(_rep_interaction.get("name", "interaction"))
                                    _rep_tt = ("Repeat '" + _rep_name.replace("[", "[[").replace("{", "{{")
                                               + "' - same costs, daily limit and requirements as the Interact menu.")
                                    # Same sensitivity rules as the interaction_category button.
                                    _rep_can = (can_interact_with_worker(worker)
                                                and worker["energy"] >= _rep_interaction.get("cost_energy", 0)
                                                and worker["health"] >= _rep_interaction.get("cost_health", 0)
                                                and (_rep_interaction.get("cost_money", 0) <= 0 or store.money >= _rep_interaction.get("cost_money", 0)))
                            # Full-width "Repeat: <name>" row BETWEEN the two button rows:
                            # says which interaction it repeats, keeps the 2x2 grid columns
                            # aligned (250/250), and stays away from the frame's bottom edge.
                            if _rep_interaction is not None:
                                button:
                                    background "images/tablebutton.png"
                                    xsize 501
                                    ysize 40
                                    sensitive _rep_can
                                    text "Repeat: [_rep_name!q]" size font_size(20) xalign 0.5 hover_color gui.journal_hover_color
                                    # Exact same launch path as the interaction_category button
                                    # (non-training branch); no Hide needed since no menu is open.
                                    action [
                                        Function(lambda w=worker, i=_rep_interaction: setattr(store, '_last_interaction_changes', apply_interaction_effects(w, i))),
                                        Show("interaction_result", worker=worker, interaction=_rep_interaction),
                                    ]
                                    hovered ShowTransient("tooltip", message=_rep_tt, screen_name="WorkerDetails")
                                    unhovered Hide("tooltip")
                            hbox:
                                spacing 1
                                button:
                                    background "images/tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "Interact" size font_size(23) xalign 0.5 hover_color gui.journal_hover_color
                                    action Show("interaction_menu", worker=worker)
                                    hovered ShowTransient("tooltip", message="Interact with this worker. Choose from available interactions based on worker stats, traits, and relationship level.", screen_name="WorkerDetails")
                                    unhovered Hide("tooltip")
                                button:
                                    background "images/tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "[sell_text]" size font_size(23) xalign 0.5 hover_color gui.journal_hover_color
                                    action Show("confirm_sell_worker", worker=worker, return_screen="worker_details")
                                    hovered ShowTransient("tooltip", message="Sell this worker. You'll receive money based on their level and skills, but lose them permanently.", screen_name="WorkerDetails")
                                    unhovered Hide("tooltip")
                        else:
                            hbox:
                                spacing 1
                                yoffset 15
                                button:
                                    background "images/tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "Description" size font_size(23) xalign 0.5 hover_color gui.journal_hover_color
                                    action Show("more_details_screen", worker=worker)
                                    hovered ShowTransient("tooltip", message="View detailed information about this worker, including full stats, history, and background.", screen_name="WorkerDetails")
                                    unhovered Hide("tooltip")
                                if from_buy_workers:
                                    button:
                                        background "images/tablebutton.png"
                                        xsize 250
                                        ysize 50
                                        text "Buy ($[worker['cost']])" size font_size(23) xalign 0.5
                                        action Show("confirm_buy_worker", worker=worker, return_screen="worker_details")

    # Keyboard QoL: Backspace mirrors the top-right Return button exactly.
    if from_recruitment:
        key "K_BACKSPACE" action [SetVariable("temp_recruitment_worker", worker), SetVariable("in_recruit_examine", False), Hide("worker_details"), Function(return_to_recruitment)]
    else:
        key "K_BACKSPACE" action Hide("worker_details")

    # Ctrl+Left/Right mirror the Previous/Next buttons (same guards; the _nav_*
    # variables are computed in the navigation block above, which runs under
    # this same in_roster/from_buy_workers condition earlier in the screen).
    if in_roster or from_buy_workers:
        key "ctrl_K_LEFT" action If(len(_nav_names) > 0, [
            SetVariable("current_worker_index", _prev_store_idx),
            SetScreenVariable("current_image", get_worker_image(_prev_worker)),
            Show("worker_details", worker=_prev_worker, in_roster=in_roster, from_buy_workers=from_buy_workers, from_recruitment=from_recruitment, nav_worker_names=_nav_names, nav_worker_index=(_roster_idx - 1) % len(_nav_names), nav_worker_pool=_context_pool)
        ])
        key "ctrl_K_RIGHT" action If(len(_nav_names) > 0, [
            SetVariable("current_worker_index", _next_store_idx),
            SetScreenVariable("current_image", get_worker_image(_next_worker)),
            Show("worker_details", worker=_next_worker, in_roster=in_roster, from_buy_workers=from_buy_workers, from_recruitment=from_recruitment, nav_worker_names=_nav_names, nav_worker_index=(_roster_idx + 1) % len(_nav_names), nav_worker_pool=_context_pool)
        ])


# Phase-proof table header rule shared by roster/report headers. A hard 2-3px
# Solid rasterizes as 1px on one screen and 2-3px on another after window
# downscaling (subpixel phase lottery - measured on captures). Soft 1px
# shoulders around the 2px core make bilinear filtering read the same visual
# weight at any phase.
screen table_rule(rule_width, rule_xalign=0.0, rule_xoffset=0):
    vbox:
        spacing 0
        xalign rule_xalign
        xoffset rule_xoffset
        add Solid("#8f7a5640") xsize rule_width ysize 1
        add Solid(gui.divider_color) xsize rule_width ysize 2
        add Solid("#8f7a5640") xsize rule_width ysize 1

# 52x52 framed portrait miniature shared by roster/buy-servants rows.
# The viewport is what CROPS: Transform with fit="cover" scales to cover the
# box but does NOT clip, so wide art would otherwise spill into the next
# column. xinitial/yinitial bias the crop toward the upper-center (faces).
screen worker_portrait_thumb(portrait_path, initial):
    frame:
        xsize 52
        ysize 52
        yalign 0.5
        padding (2, 2)
        background Solid(gui.journal_dark_color)
        viewport:
            xsize 48
            ysize 48
            xinitial 0.5
            yinitial 0.25
            if portrait_path:
                add Transform(portrait_path, xysize=(48, 48), fit="cover")
            else:
                frame:
                    xsize 48
                    ysize 48
                    padding (0, 0)
                    background Solid("#00000022")
                    text "[initial!q]" size 26 color gui.parchment_muted_color xalign 0.5 yalign 0.5

screen workers():
    zorder 10
    modal True
    # NOTE: no renpy.restart_interaction here. on-show actions already run
    # before the first paint; the extra restart re-created the list viewport's
    # scroll adjustment mid-reflow and the roster opened scrolled ~1.5 rows
    # down (first row half-hidden under the header). Verified by screenshot.
    on "show" action [Function(process_manager_auto_rest), Function(ensure_manager_inventory_synced_for_potions), Function(maybe_show_intro_popup, "workers")]
    add workers_bg
    add Solid("#00000099")
    
    # Roster list filtered by Worker Gender preference (Both / Only Male / Only Female)
    $ _displayed_roster = workers_filtered_by_gender(store.workers)
    
    frame:
        xalign 0.5  # Center the frame horizontally
        yalign 0.5  # Center the frame vertically
        xsize 1536
        ysize 864
        background Transform("gui/gallery.png", xysize=(1536, 864))
        padding (20, 20)
        
        # Overlay close button (X) anchored to top-right inside the panel
        fixed:
            xfill True
            yfill True
            imagebutton:
                idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
                # Context-aware close: if Workers was opened over Manager, return there;
                # otherwise, go back to tavern as usual.
                action If(
                    renpy.get_screen("Manager"),
                    Hide("workers"),
                    [Hide("workers"), Show("tavern")]
                )
                align (0.985, 0.10)
                xoffset -80
                yoffset 22
        vbox:
            xalign 0.5  # Center the vbox contents horizontally
            spacing 15
            null height 80  # Push content further down into the lighter beige area
            label "Manage Workers" xalign 0.5 style "header_style"
            # (was null 5: removed to lift the list 5px off the bottom border art
            # without shortening the 420px viewport - user request)
            
            hbox:
                spacing 20
                xalign 0.5
                yoffset -10
                
                hbox:
                    spacing 10
                    text "Filter by Building:" size font_size(20) color gui.journal_text_color yalign 0.5
                    
                    python:
                        # Ensure worker_building_filter is set to default if not defined
                        if not hasattr(store, 'worker_building_filter') or store.worker_building_filter is None:
                            store.worker_building_filter = "All Workers"
                        unique_buildings = ["All Workers"]
                        for worker in _displayed_roster:
                            building_name = worker.get('assigned_building', 'Unassigned')
                            building = available_buildings.get(building_name, {})
                            btype_id = building.get("type")
                            type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                            parts = building_name.split('_')
                            default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                            building_display_name = store.custom_names.get(building_name, default_name)
                            full_display_name = f"{type_name}: {building_display_name}"
                            
                            if full_display_name not in unique_buildings:
                                unique_buildings.append(full_display_name)
                    
                    frame:
                        background "#4a2a1acc"
                        padding (10, 5)
                        
                        button:
                            xsize 300
                            ysize 40
                            background "#5a3a1a"
                            hover_background "#6b4a2a"
                            
                            text "[worker_building_filter]" size font_size(20) color "#ffffff" xalign 0.5 yalign 0.5
                            
                            action Show("worker_building_filter_menu", buildings=unique_buildings)
                
                hbox:
                    spacing 10
                    text "Filter by Job:" size font_size(20) color gui.journal_text_color yalign 0.5
                    
                    python:
                        # Ensure worker_job_filter is set to default if not defined
                        if not hasattr(store, 'worker_job_filter') or store.worker_job_filter is None:
                            store.worker_job_filter = "All Jobs"
                        unique_jobs = ["All Jobs"]
                        
                        selected_building_internal = None
                        if worker_building_filter != "All Workers":
                            for bname, bdata in available_buildings.items():
                                btype_id = bdata.get("type")
                                type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                                parts = bname.split('_')
                                default_name = f"Building {parts[1]}" if len(parts) > 1 else bname
                                building_display_name = store.custom_names.get(bname, default_name)
                                full_display_name = f"{type_name}: {building_display_name}"
                                if full_display_name == worker_building_filter:
                                    selected_building_internal = bname
                                    break
                        
                        for worker in _displayed_roster:
                            building_name = worker.get('assigned_building', 'Unassigned')
                            
                            if selected_building_internal is not None:
                                if building_name != selected_building_internal:
                                    continue
                            
                            if building_name != "Unassigned" and building_name in available_buildings:
                                job_id = available_buildings[building_name]["servant_jobs"].get(worker["name"], "Unassigned")
                                btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == available_buildings[building_name]["type"]), None)
                                # Match filter logic below: "Unassigned" job slot is not the same as unassigned building.
                                jid_low = str(job_id).strip().lower() if job_id is not None else "unassigned"
                                if jid_low != "unassigned" and btype is not None:
                                    _rpj = getattr(store, "resolve_profession_for_job", None)
                                    if callable(_rpj):
                                        job_name, _pj_unused = _rpj(btype, job_id)
                                    else:
                                        job_name = next((p["name"] for p in btype.get("professions", []) if str(p.get("id", "")).strip().lower() == str(job_id).strip().lower()), job_id)
                                    if job_name not in unique_jobs:
                                        unique_jobs.append(job_name)
                                else:
                                    if "Unassigned" not in unique_jobs:
                                        unique_jobs.append("Unassigned")
                            else:
                                if "Unassigned" not in unique_jobs:
                                    unique_jobs.append("Unassigned")
                        
                        if worker_job_filter not in unique_jobs:
                            store.worker_job_filter = "All Jobs"
                    
                    frame:
                        background "#4a2a1acc"
                        padding (10, 5)
                        
                        button:
                            xsize 300
                            ysize 40
                            background "#5a3a1a"
                            hover_background "#6b4a2a"
                            
                            text "[worker_job_filter]" size font_size(20) color "#ffffff" xalign 0.5 yalign 0.5
                            
                            action Show("worker_job_filter_menu", jobs=unique_jobs)
            
            null height 0
            
            # Header: plain labels over ONE full-width hairline (daily-report
            # style). The old per-column underline art (tablebutton4) plus a
            # separate divider read as two redundant line systems.
            # NOTE: no yoffset here or on the viewport below — negative draw
            # offsets made the drawn position diverge from the layout position,
            # which is how every height budget on this screen went wrong.
            # WIDTH: box = actual content (52 portrait + 5x180 columns + 5x14
            # gaps = 1022) so xalign 0.5 truly centers it; the old 1200 box
            # left-aligned its content and the whole table sat left of center.
            vbox:
                spacing 6
                xalign 0.5
                hbox:
                    xalign 0.5
                    spacing 14  # Much tighter gaps between columns
                    xsize 1022
                    yalign 0.5
                    # Spacer over the portrait column so headers stay aligned with rows
                    null width 52
                    button:
                        background None
                        xsize 180
                        ysize 30
                        text "Name (Level)" size font_size(22) color gui.journal_text_color
                        sensitive False
                    button:
                        background None
                        xsize 180
                        ysize 30
                        text "Building" size font_size(22) color gui.journal_text_color
                        sensitive False
                    button:
                        background None
                        xsize 180
                        ysize 30
                        text "Job (Skill)" size font_size(22) color gui.journal_text_color
                        sensitive False
                    button:
                        background None
                        xsize 180
                        ysize 30
                        text "Energy - Health" size font_size(22) color gui.journal_text_color
                        sensitive False
                    button:
                        background None
                        xsize 180
                        ysize 30
                        text "Type / Action" size font_size(22) color gui.journal_text_color
                        sensitive False
                # The single separator: also keeps partially-scrolled rows from
                # kissing the header labels.
                use table_rule(1022, rule_xalign=0.5)

            # Main content area (viewport)
            viewport:
                xalign 0.5  # Center the viewport horizontally
                scrollbars "vertical"
                mousewheel True
                draggable True
                # Height budget (verified against real screenshots): frame top 108
                # + padding 20 + null 80 + title ~45 + null 5 + filters 50 + header 50
                # + 6 vbox gaps of 15 = viewport starts ~433 (1080-space). The
                # gallery.png art's inner bottom edge sits ~900; 430 still let the
                # scrollbar graze the crosshatch border lines, so 420 it is.
                ysize 420
                # 1267: near the full panel width so the scrollbar sits at the right
                # edge UNDER the close X (conventional), not floating mid-panel. Rows
                # are centered inside this viewport (below), which is centered in the
                # frame -> rows land on the header's axis while the bar stays at the
                # edge. Width tuned by measurement so the bar's center sits under the
                # X's center (content center unchanged - both edges come in equally).
                xsize 1283
                vbox:
                    # Explicit width = viewport width: without it the vbox collapsed
                    # to content width and landed LEFT-anchored (screenshot-verified),
                    # so the rows' xalign 0.5 had nothing to center against.
                    xsize 1283
                    spacing 10
                    
                    # Aplicar filtros (building y job)
                    python:
                        # Ensure filters are set to default if not defined
                        if not hasattr(store, 'worker_building_filter') or store.worker_building_filter is None:
                            store.worker_building_filter = "All Workers"
                        if not hasattr(store, 'worker_job_filter') or store.worker_job_filter is None:
                            store.worker_job_filter = "All Jobs"
                        
                        filtered_workers = []
                        for worker in _displayed_roster:
                            building_match = True
                            if worker_building_filter != "All Workers":
                                building_name = worker.get('assigned_building', 'Unassigned')
                                building = available_buildings.get(building_name, {})
                                btype_id = building.get("type")
                                type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                                parts = building_name.split('_')
                                default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                                building_display_name = store.custom_names.get(building_name, default_name)
                                full_display_name = f"{type_name}: {building_display_name}"
                                
                                if full_display_name != worker_building_filter:
                                    building_match = False
                            
                            # Filtro por trabajo
                            job_match = True
                            if worker_job_filter != "All Jobs":
                                building_name = worker.get('assigned_building', 'Unassigned')
                                if building_name != "Unassigned" and building_name in available_buildings:
                                    job_id = available_buildings[building_name]["servant_jobs"].get(worker["name"], "Unassigned")
                                    btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == available_buildings[building_name]["type"]), None)
                                    if job_id.lower() != "unassigned" and btype is not None:
                                        _rpj = getattr(store, "resolve_profession_for_job", None)
                                        if callable(_rpj):
                                            job_name, _pj_unused = _rpj(btype, job_id)
                                        else:
                                            job_name = next((p["name"] for p in btype.get("professions", []) if str(p.get("id", "")).strip().lower() == str(job_id).strip().lower()), job_id)
                                        if job_name != worker_job_filter:
                                            job_match = False
                                    else:
                                        if worker_job_filter != "Unassigned":
                                            job_match = False
                                else:
                                    if worker_job_filter != "Unassigned":
                                        job_match = False
                            
                            if building_match and job_match:
                                filtered_workers.append(worker)
                        
                        # Rest job always goes last within each building
                        _norm_building_key = getattr(store, "_norm_building_key", lambda k: str(k or "").strip())

                        # Per-worker profession skill totals, computed ONCE per render.
                        # (Previously calculate_skill_with_traits ran per skill per worker in
                        # BOTH the sort key and the row display.)
                        _ws_skill_cache = {}
                        for _w in filtered_workers:
                            _entry = {"sum": 0, "avg": 0}
                            _b_name = _w.get('assigned_building', 'Unassigned')
                            if _b_name != "Unassigned" and _b_name in available_buildings:
                                _b_data = available_buildings[_b_name]
                                _j_id = _b_data.get("servant_jobs", {}).get(_w["name"], "Unassigned")
                                _j_id_lc = str(_j_id).strip().lower()
                                _b_type_def = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == _b_data.get("type")), None)
                                if _j_id_lc != "unassigned" and _b_type_def:
                                    _rpjc = getattr(store, "resolve_profession_for_job", None)
                                    _jd = _rpjc(_b_type_def, _j_id)[1] if callable(_rpjc) else None
                                    if not _jd:
                                        _jd = next((p for p in _b_type_def.get("professions", []) if str(p.get("id", "")).strip().lower() == _j_id_lc), None)
                                    if _jd and hasattr(_jd, "get"):
                                        _sks = [str(_sk) for _sk in (_jd.get("skills", []) or [])]
                                        _tot = 0
                                        for _sk in _sks:
                                            _tot += calculate_skill_with_traits(_w, _sk, include_libido=False)
                                        _entry["sum"] = int(_tot)
                                        _entry["avg"] = (_tot // len(_sks)) if _sks else 0
                            _ws_skill_cache[str(_w.get("name", ""))] = _entry

                        # NOTE: defs inside a screen `python:` block do NOT see the
                        # screen's locals at call time (the block runs exec-style, so
                        # the function's globals are the store). Screen-local values
                        # must be bound as default arguments at def time.
                        def get_worker_sort_key(w, _ws_skill_cache=_ws_skill_cache):
                            b_name = w.get('assigned_building', 'Unassigned')
                            skill_metric = 0
                            if b_name != "Unassigned" and b_name in available_buildings:
                                b_data = available_buildings[b_name]
                                b_type_id = b_data.get("type")
                                j_id = b_data.get("servant_jobs", {}).get(w["name"], "Unassigned")
                                b_type_def = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == b_type_id), None)
                                j_id_lc = str(j_id).strip().lower()
                                if j_id_lc != "unassigned" and b_type_def:
                                    _rpj2 = getattr(store, "resolve_profession_for_job", None)
                                    if callable(_rpj2):
                                        j_name = _rpj2(b_type_def, j_id)[0]
                                    else:
                                        j_def = next((p for p in b_type_def.get("professions", []) if str(p.get("id", "")).strip().lower() == j_id_lc), None)
                                        j_name = j_def.get("name", "ZZZ") if j_def else ("Rest" if j_id_lc == "rest" else "ZZZ")
                                    # Preserve skill-priority ordering inside each role (cached totals).
                                    skill_metric = _ws_skill_cache.get(str(w.get("name", "")), {}).get("sum", 0)
                                    j_sort_name = "zzz_rest" if j_name.lower() == "rest" else j_name.lower()
                                else:
                                    j_sort_name = "zzz"
                            else:
                                j_sort_name = "zzz"
                            # Stable tie-breakers avoid jitter while keeping skill priority.
                            b_sort = _norm_building_key(b_name)
                            w_name = str(w.get("name", "")).strip().lower()
                            return (b_sort, j_sort_name, -skill_metric, w_name)

                        filtered_workers = sorted(filtered_workers, key=get_worker_sort_key)

                        # Loop-invariant nav list (was rebuilt inside the per-worker row loop)
                        _workers_nav_names = [w.get("name") for w in filtered_workers if hasattr(w, "get") and w.get("name")]

                    for worker in filtered_workers:
                        $ _workers_nav_index = next((idx for idx, n in enumerate(_workers_nav_names) if n == worker.get("name")), 0)
                        $ worker_level = worker.get('level', 1)
                        $ _row_portrait = get_worker_portrait_cached(worker)
                        $ _row_initial = (str(worker.get("name", "")).strip() or "?")[:1]
                        frame:
                            xalign 0.5  # Center each worker row horizontally
                            # The vertical scrollbar shifts the viewport half a bar left
                            # of the frame's axis; nudge rows back so they share the
                            # header's (frame-centered) axis.
                            xoffset (gui.scrollbar_size // 2)
                            padding (0, 2)
                            # Zebra striping so long rosters stay scannable
                            background (Solid(gui.row_alt_color) if _workers_nav_index % 2 else None)
                            # WIDTH: content-sized (see header note) so the zebra band
                            # ends at the last column instead of trailing empty space.
                            hbox:
                                spacing 14
                                xsize 1022
                                yalign 0.5
                                # Framed portrait miniature (cached lookup; letter placeholder without art)
                                use worker_portrait_thumb(_row_portrait, _row_initial)
                                button:
                                    background "images/tablebutton1b.png"
                                    xsize 180
                                    ysize 50
                                    text "[worker['name']!q] ([worker_level])" size font_size(22) color gui.journal_text_color hover_color gui.journal_hover_color
                                    action Show("worker_details", worker=worker, in_roster=True, nav_worker_names=_workers_nav_names, nav_worker_index=_workers_nav_index)
                                $ assigned_building = worker.get("assigned_building", "Unassigned")
                                $ building_display_name = custom_names.get(assigned_building, assigned_building)
                                button:
                                    background "images/tablebutton1b.png"
                                    xsize 180
                                    ysize 50
                                    text "[building_display_name!q]" size font_size(22) color gui.journal_text_color hover_color gui.journal_hover_color
                                    action Show("building_selection", worker=worker)
                                if worker.get("assigned_building", "Unassigned") != "Unassigned":
                                    $ building_name = worker["assigned_building"]
                                    if building_name in available_buildings:
                                        $ job_id = available_buildings[building_name]["servant_jobs"].get(worker["name"], "Unassigned")
                                        $ btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == available_buildings[building_name]["type"]), None)
                                    else:
                                        $ job_id = "Unassigned"
                                        $ btype = None
                                    $ _rpj3 = getattr(store, "resolve_profession_for_job", None)
                                    $ job_name = "Unassigned" if job_id.lower() == "unassigned" else ((_rpj3(btype, job_id)[0] if callable(_rpj3) and btype else next((p["name"] for p in btype.get("professions", []) if str(p.get("id", "")).strip().lower() == str(job_id).strip().lower()), job_id)) if btype else job_id)
                                    $ avg_skill = 0
                                    if job_id.lower() != "unassigned" and btype is not None:
                                        # Cached per render in _ws_skill_cache (computed above, before the loop)
                                        $ avg_skill = _ws_skill_cache.get(str(worker.get("name", "")), {}).get("avg", 0)
                                    # For rest job, don't show skill value
                                    $ job_name_with_skill = job_name if avg_skill == 0 or job_id.lower() == "unassigned" or job_id.lower() == "rest" else f"{job_name} ({avg_skill})"
                                    button:
                                        background "images/tablebutton1b.png"
                                        xsize 180
                                        ysize 50
                                        text "[job_name_with_skill!q]" size font_size(22) color gui.journal_text_color hover_color gui.journal_hover_color
                                        action Show("job_selection", worker=worker)
                                else:
                                    button:
                                        background "images/tablebutton1b.png"
                                        xsize 180
                                        ysize 50
                                        text "Unassigned" size font_size(22) color gui.journal_text_color hover_color gui.journal_hover_color
                                        action Show("job_selection", worker=worker)
                                # Energy - Health column: numbers + thin stat bars.
                                # Buttons keep their use/buy-potion actions and sensitivity.
                                $ _max_e = calculate_max_energy(worker)
                                $ _max_h = calculate_max_health(worker)
                                $ _cur_e = int(worker.get('energy', 0) or 0)
                                $ _cur_h = int(worker.get('health', 0) or 0)
                                $ _e_frac = min(1.0, (_cur_e / float(_max_e)) if _max_e else 0.0)
                                $ _h_frac = min(1.0, (_cur_h / float(_max_h)) if _max_h else 0.0)
                                $ _e_col = gui.danger_color if _e_frac < 0.3 else gui.journal_text_color
                                $ _h_col = gui.danger_color if _h_frac < 0.3 else gui.journal_text_color
                                hbox:
                                    spacing 2
                                    xsize 180
                                    ysize 50
                                    button:
                                        background "images/tablebutton1b.png"
                                        hover_foreground Solid("#6b652820")
                                        xsize 89
                                        ysize 50
                                        action use_or_buy_potion_action(worker, "energy_potion")
                                        sensitive _cur_e < _max_e
                                        vbox:
                                            xalign 0.5
                                            yalign 0.5
                                            spacing 4
                                            text "E [_cur_e]/[_max_e]" size font_size(18) color _e_col xalign 0.5
                                            fixed:
                                                xsize 64
                                                ysize 7
                                                xalign 0.5
                                                add Solid(gui.bar_track_color, xysize=(64, 7))
                                                add Solid(gui.energy_bar_color, xysize=(max(2, int(64 * _e_frac)), 7))
                                    button:
                                        background "images/tablebutton1b.png"
                                        hover_foreground Solid("#6b652820")
                                        xsize 89
                                        ysize 50
                                        action use_or_buy_potion_action(worker, "health_potion")
                                        sensitive _cur_h < _max_h
                                        vbox:
                                            xalign 0.5
                                            yalign 0.5
                                            spacing 4
                                            text "H [_cur_h]/[_max_h]" size font_size(18) color _h_col xalign 0.5
                                            fixed:
                                                xsize 64
                                                ysize 7
                                                xalign 0.5
                                                add Solid(gui.bar_track_color, xysize=(64, 7))
                                                add Solid(gui.health_bar_color, xysize=(max(2, int(64 * _h_frac)), 7))
                                # Type / Action column (fused)
                                frame:
                                    background "images/tablebutton1b.png"
                                    xsize 180
                                    ysize 50
                                    padding (0, 0)
                                    $ worker_type = 'Servant' if worker.get('is_servant', False) else 'Worker'
                                    $ action_text = get_sell_text(worker)
                                    hbox:
                                        xalign 0.0
                                        yalign 0.5
                                        spacing 0
                                        text "[worker_type] / " size font_size(22) color gui.journal_text_color yalign 0.5
                                        textbutton "[action_text]":
                                            text_size font_size(22)
                                            text_color gui.journal_text_color
                                            text_hover_color gui.journal_hover_color
                                            action Show("confirm_sell_worker", worker=worker)
                                            yalign 0.5

            # (Removed duplicate close button)

    key "K_BACKSPACE" action If(
        renpy.get_screen("Manager"),
        Hide("workers"),
        [Hide("workers"), Show("tavern")]
    )

screen map_screen():
    # Ensure workers are loaded when map opens (once per show, not per render;
    # auto-refill doesn't count as a manual refresh)
    on "show" action [Function(maybe_show_intro_popup, "map_screen"), Function(_map_screen_autorefill)]
    zorder 2
    modal True
    add map_bg

    # Map building buttons with focus_mask
    # Images are full map size with transparent areas, so they auto-position correctly
    # Order matters: later buttons render on top (higher z-order)
    
    # Plaza buildings
    # Plaza Shop - before Plaza Tavern so Plaza Tavern renders on top
    imagebutton:
        idle If(shops_text_hover,
            At("gui/map/PlazaShopb.png", blink_transform),
            "gui/map/PlazaShopa.png")
        hover "gui/map/PlazaShopb.png"
        focus_mask True
        action [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop1")]
        hovered [ShowTransient("tooltip", message="[get_shop_tooltip_text('shop1')]"), SetVariable("shops_text_hover", False)]
        unhovered [Hide("tooltip"), SetVariable("shops_text_hover", False)]
    
    # Blinking animation for PlazaServants when textbutton is hovered
    imagebutton:
        idle If(plaza_servants_text_hover, 
            At("gui/map/PlazaServantsb.png", blink_transform),
            get_map_button_idle_image("PlazaServants"))
        hover "gui/map/PlazaServantsb.png"
        focus_mask True
        action Show("buy_servants_table")
        hovered [ShowTransient("tooltip", message="Buy Servants"), SetVariable("plaza_servants_text_hover", False)]
        unhovered [Hide("tooltip"), SetVariable("plaza_servants_text_hover", False)]
    
    # Plaza Fountain - Take a Walk
    imagebutton:
        idle If(take_a_walk_text_hover,
            At("gui/map/PlazaFountainb.png", blink_transform),
            "gui/map/PlazaFountaina.png")
        hover "gui/map/PlazaFountainb.png"
        focus_mask True
        action If(
            last_take_a_walk_day == current_day or take_a_walk_in_progress,
            Show("error_popup", message="You've already taken a walk today. Come back tomorrow."),
            Function(renpy.call_in_new_context, "take_a_walk")
        )
        hovered ShowTransient("tooltip", message="Take a walk")
        unhovered Hide("tooltip")
    
    # S1 (South 1) buildings - Elite Emporium (shop3)
    imagebutton:
        idle If(shops_text_hover,
            At("gui/map/S1Shop1b.png", blink_transform),
            get_map_button_idle_image("S1Shop1"))
        hover "gui/map/S1Shop1b.png"
        focus_mask True
        action If(
            unlocked_shops.get("shop3", False),
            [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop3")],
            Show("error_popup", message="This shop will open when the owner is found and an investment has been made (an event will appear as you advance with the journal objectives).")
        )
        hovered [ShowTransient("tooltip", message="[get_shop_tooltip_text('shop3')]"), SetVariable("shops_text_hover", False)]
        unhovered [Hide("tooltip"), SetVariable("shops_text_hover", False)]
    
    # Adventurer's Market (shop2)
    imagebutton:
        idle If(shops_text_hover,
            At("gui/map/S1Shop2b.png", blink_transform),
            get_map_button_idle_image("S1Shop2"))
        hover "gui/map/S1Shop2b.png"
        focus_mask True
        action If(
            unlocked_shops.get("shop2", False),
            [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop2")],
            Show("error_popup", message="This shop will open when the owner is found (an event will appear as you advance with the journal objectives).")
        )
        hovered [ShowTransient("tooltip", message="[get_shop_tooltip_text('shop2')]"), SetVariable("shops_text_hover", False)]
        unhovered [Hide("tooltip"), SetVariable("shops_text_hover", False)]
    
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("S1Greenhouse") is None,
            At("gui/map/S1Greenhouseb.png", blink_transform),
            get_map_button_idle_image("S1Greenhouse"))
        hover "gui/map/S1Greenhouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("S1Greenhouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("S1Greenhouse"))],
            Show("buy_map_building", map_button_id="S1Greenhouse")
        )
        hovered If(
            get_map_building_name_safe("S1Greenhouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('S1Greenhouse')]")
        )
        unhovered Hide("tooltip")
    
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("S1Redhouse") is None,
            At("gui/map/S1Redhouseb.png", blink_transform),
            get_map_button_idle_image("S1Redhouse"))
        hover "gui/map/S1Redhouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("S1Redhouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("S1Redhouse"))],
            Show("buy_map_building", map_button_id="S1Redhouse")
        )
        hovered If(
            get_map_building_name_safe("S1Redhouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('S1Redhouse')]")
        )
        unhovered Hide("tooltip")
    
    # S3 (South 3) buildings - before S2 so S2 renders on top
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("S3Bluehouse") is None,
            At("gui/map/S3Bluehouseb.png", blink_transform),
            get_map_button_idle_image("S3Bluehouse"))
        hover "gui/map/S3Bluehouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("S3Bluehouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("S3Bluehouse"))],
            Show("buy_map_building", map_button_id="S3Bluehouse")
        )
        hovered If(
            get_map_building_name_safe("S3Bluehouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('S3Bluehouse')]")
        )
        unhovered Hide("tooltip")
    
    # S2 (South 2) buildings - after S3 so it renders on top
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("S2Tavern") is None,
            At("gui/map/S2Tavernb.png", blink_transform),
            get_map_button_idle_image("S2Tavern"))
        hover "gui/map/S2Tavernb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("S2Tavern") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("S2Tavern"))],
            Show("buy_map_building", map_button_id="S2Tavern")
        )
        hovered If(
            get_map_building_name_safe("S2Tavern") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('S2Tavern')]")
        )
        unhovered Hide("tooltip")
    
    # S4 (South 4) buildings
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("S4Redhouse") is None,
            At("gui/map/S4Redhouseb.png", blink_transform),
            get_map_button_idle_image("S4Redhouse"))
        hover "gui/map/S4Redhouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("S4Redhouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("S4Redhouse"))],
            Show("buy_map_building", map_button_id="S4Redhouse")
        )
        hovered If(
            get_map_building_name_safe("S4Redhouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('S4Redhouse')]")
        )
        unhovered Hide("tooltip")
    
    imagebutton:
        idle Transform(get_map_button_idle_image("S4Shop"), matrixcolor=SaturationMatrix(0.35))
        hover get_map_button_idle_image("S4Shop")
        focus_mask True
        action NullAction()  # No buildings available for this location
        sensitive False  # Desactivar interactividad
    
    # N1 (North 1) buildings
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("N1Bluehouse") is None,
            At("gui/map/N1Bluehouseb.png", blink_transform),
            get_map_button_idle_image("N1Bluehouse"))
        hover "gui/map/N1Bluehouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("N1Bluehouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("N1Bluehouse"))],
            Show("buy_map_building", map_button_id="N1Bluehouse")
        )
        hovered If(
            get_map_building_name_safe("N1Bluehouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('N1Bluehouse')]")
        )
        unhovered Hide("tooltip")
    
    # N2 (North 2) buildings
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("N2Greenhouse") is None,
            At("gui/map/N2Greenhouseb.png", blink_transform),
            get_map_button_idle_image("N2Greenhouse"))
        hover "gui/map/N2Greenhouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("N2Greenhouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("N2Greenhouse"))],
            Show("buy_map_building", map_button_id="N2Greenhouse")
        )
        hovered If(
            get_map_building_name_safe("N2Greenhouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('N2Greenhouse')]")
        )
        unhovered Hide("tooltip")
    
    # N4 (North 4) buildings - before N3 so N3 renders on top
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("N4Redhouse") is None,
            At("gui/map/N4Redhouseb.png", blink_transform),
            get_map_button_idle_image("N4Redhouse"))
        hover "gui/map/N4Redhouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("N4Redhouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("N4Redhouse"))],
            Show("buy_map_building", map_button_id="N4Redhouse")
        )
        hovered If(
            get_map_building_name_safe("N4Redhouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('N4Redhouse')]")
        )
        unhovered Hide("tooltip")
    
    # N3 (North 3) buildings - after N4 so it renders on top
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("N3Bluehouse") is None,
            At("gui/map/N3Bluehouseb.png", blink_transform),
            get_map_button_idle_image("N3Bluehouse"))
        hover "gui/map/N3Bluehouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("N3Bluehouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("N3Bluehouse"))],
            Show("buy_map_building", map_button_id="N3Bluehouse")
        )
        hovered If(
            get_map_building_name_safe("N3Bluehouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('N3Bluehouse')]")
        )
        unhovered Hide("tooltip")
    
    # N5 (North 5) buildings
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("N5Greenhouse") is None,
            At("gui/map/N5Greenhouseb.png", blink_transform),
            get_map_button_idle_image("N5Greenhouse"))
        hover "gui/map/N5Greenhouseb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("N5Greenhouse") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("N5Greenhouse"))],
            Show("buy_map_building", map_button_id="N5Greenhouse")
        )
        hovered If(
            get_map_building_name_safe("N5Greenhouse") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('N5Greenhouse')]")
        )
        unhovered Hide("tooltip")
    
    imagebutton:
        idle Transform(get_map_button_idle_image("N5Shop"), matrixcolor=SaturationMatrix(0.35))
        hover get_map_button_idle_image("N5Shop")
        focus_mask True
        action NullAction()  # No buildings available for this location
        sensitive False  # Desactivar interactividad
    
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("N5Tavern") is None,
            At("gui/map/N5Tavernb.png", blink_transform),
            get_map_button_idle_image("N5Tavern"))
        hover "gui/map/N5Tavernb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("N5Tavern") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("N5Tavern"))],
            Show("buy_map_building", map_button_id="N5Tavern")
        )
        hovered If(
            get_map_building_name_safe("N5Tavern") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('N5Tavern')]")
        )
        unhovered Hide("tooltip")
    
    # N6 Murderhouse - "In development" (NewMap: N6murderhousea.png, N6murderhouseb.png hover)
    imagebutton:
        idle Transform("gui/map/N6murderhousea.png", matrixcolor=SaturationMatrix(0.35))
        hover "gui/map/N6murderhouseb.png"
        focus_mask True
        action Show("in_development")
        hovered ShowTransient("tooltip", message="In development")
        unhovered Hide("tooltip")
    
    # N5 Academy - on first unlock call Yvara prologue (tuition dialogue); when enrolled, show academy menu.
    imagebutton:
        idle If(store.academy_enrolled, "gui/map/N5academya.png", Transform("gui/map/N5academya.png", matrixcolor=SaturationMatrix(0.35)))
        hover "gui/map/N5academyb.png"
        focus_mask True
        action If(store.academy_enrolled, Show("academy_menu"), [Hide("map_screen"), Jump("yvara_prologue")])
        hovered ShowTransient("tooltip", message="Academy" if store.academy_enrolled else "Academy (enroll to unlock)")
        unhovered Hide("tooltip")
    
    # Arena - first visit: dialogue; after unlock: arena menu (like Academy).
    imagebutton:
        idle If(store.arena_unlocked, "gui/map/arenaa.png", Transform("gui/map/arenaa.png", matrixcolor=SaturationMatrix(0.35)))
        hover "gui/map/arenab.png"
        focus_mask True
        action If(store.arena_unlocked, Show("arena_menu"), [Hide("map_screen"), Jump("arena_first_dialogue")])
        hovered ShowTransient("tooltip", message="Arena" if store.arena_unlocked else "Arena (enter to unlock)")
        unhovered Hide("tooltip")
    
    # Castle - renders on top of N5 Tavern
    imagebutton:
        idle "gui/map/Castlea.png"
        hover "gui/map/Castleb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("Castle") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("Castle"))],
            NullAction()  # Castle not unlocked yet
        )
        sensitive get_map_building_name_safe("Castle") is not None
        hovered If(
            get_map_building_name_safe("Castle") is not None,
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('Castle')]"),
            NullAction()
        )
        unhovered Hide("tooltip")
    
    # S4 Tavern - after Castle so it renders on top
    imagebutton:
        idle If(buy_buildings_text_hover and get_map_building_name_safe("S4Tavern") is None,
            At("gui/map/S4Tavernb.png", blink_transform),
            get_map_button_idle_image("S4Tavern"))
        hover "gui/map/S4Tavernb.png"
        focus_mask True
        action If(
            get_map_building_name_safe("S4Tavern") is not None,
            [Hide("map_screen"), Show("Manager", building_name=get_map_building_name_safe("S4Tavern"))],
            Show("buy_map_building", map_button_id="S4Tavern")
        )
        hovered If(
            get_map_building_name_safe("S4Tavern") is None,
            ShowTransient("tooltip", message="Click to buy this property"),
            ShowTransient("tooltip", message="Go to [get_map_building_display_name('S4Tavern')]")
        )
        unhovered Hide("tooltip")
    
    # Plaza Tavern - after S4 Tavern so it renders on top of everything (Plaza Shop, N4 Red house, etc.)
    imagebutton:
        idle "gui/map/PlazaTaverna.png"
        hover "gui/map/PlazaTavernb.png"
        focus_mask True
        action [Hide("map_screen"), Show("tavern")]
        hovered ShowTransient("tooltip", message="Go to [get_building_1_display_name()]")
        unhovered Hide("tooltip")
    
    # Context menu background - placed after all map buttons so it renders on top
    add context_menu_bg xalign 0.5 yalign 0.5
    
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        # Money display with icon-style $ symbol
        hbox:
            spacing 5
            text "$" color gui.journal_dark_color size 22 bold True yalign 0.5
            text "[format(int(money), ',')]" color gui.journal_dark_color size 28 yalign 0.5
        # Calendar display with icon
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]  # Map day 1-28 to 7-day week
            $ month_name = month_names[store.current_month - 1]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color gui.journal_dark_color size 25 yalign 0.5
        # Compact status strip: roster size and owned holdings (read-only)
        python:
            _tv_worker_count = len(store.workers)
            _tv_building_count = len(getattr(store, "owned_buildings", []) or [])
        text "Workers: [_tv_worker_count]      Buildings: [_tv_building_count]" color gui.journal_dark_color size 20
        # Player title and name (click to open character sheet) — blink when pending skill points
        if manager_has_unspent_skill_points():
            timer 0.7 repeat True action ToggleVariable("manager_name_blink_highlight")
        python:
            _manager_name_color = gui.journal_hover_color if (getattr(store, 'manager_name_blink_highlight', False) and manager_has_unspent_skill_points()) else gui.journal_dark_color
        textbutton "[player_title] [player_name]":
            action Show("manager_character_sheet")
            text_color _manager_name_color
            text_hover_color gui.journal_hover_color
            text_size 24
            text_italic True
            background None
            hover_background None
    
    # Context menu - placed at the end to render on top of all map buttons
    frame:
        xalign 1.0
        yalign 0.5
        xsize 320
        ysize 1.0
        background None
        
        # Help/Information button - positioned in top-right corner of context menu (green panel)
        python:
            screen_name = "map_screen"
            tooltips_enabled = get_tooltips_state_for_screen(screen_name)
        
        imagebutton:
            idle Transform("gui/info_idle.png", zoom=0.315)  # 10% smaller than 0.35
            hover Transform("gui/info_hover.png", zoom=0.315)
            selected_idle Transform("gui/info_active.png", zoom=0.315)
            selected_hover Transform("gui/info_active.png", zoom=0.315)
            selected tooltips_enabled
            action Function(toggle_tooltips_for_screen, screen_name)
            hovered ShowTransient("tooltip", message="Tooltips: {color=#ffffff}On{/color}/Off", screen_name=screen_name)
            unhovered Hide("tooltip")
            xalign 1.0
            xoffset -55  # More to the left
            yalign 0.0
            yoffset 55  # More down
        
        vbox:
            xalign 1.0
            yalign 0.5
            xoffset -5
            spacing 10
            textbutton "Buy Buildings":
                action Show("error_popup", message="Select a building on the map to view purchase options.")
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered SetVariable("buy_buildings_text_hover", True)
                unhovered SetVariable("buy_buildings_text_hover", False)
            textbutton "Buy Servants":
                action Show("buy_servants_table")
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered SetVariable("plaza_servants_text_hover", True)
                unhovered SetVariable("plaza_servants_text_hover", False)
            textbutton "Recruit Workers":
                action If(can_recruit_today,
                    [Hide("map_screen"), Jump("start_recruitment_system")],
                    Show("error_popup", message="You can only recruit once per day"))
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
            textbutton "Take a Walk":
                action If(
                    last_take_a_walk_day == current_day or take_a_walk_in_progress,
                    Show("error_popup", message="You've already taken a walk today. Come back tomorrow."),
                    Function(renpy.call_in_new_context, "take_a_walk")
                )
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered SetVariable("take_a_walk_text_hover", True)
                unhovered SetVariable("take_a_walk_text_hover", False)
            if not tutorial_active:
                textbutton "Buy Buildings Abroad":
                    action Show("buy_buildings")
                    xsize 300
                    text_size 42
                    text_color gui.journal_dark_color
                    text_hover_color gui.journal_hover_color
            textbutton "Visit Shops":
                action Show("shop_selection")
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered SetVariable("shops_text_hover", True)
                unhovered SetVariable("shops_text_hover", False)
            textbutton "Back":
                action [Hide("map_screen"), Show("tavern")]
                xsize 300
                text_size 42
                text_color gui.journal_hover_color
                text_hover_color "#ffffff"

    key "K_BACKSPACE" action [Hide("map_screen"), Show("tavern")]

# --- screen daily_report() ---

screen daily_report():
    on "show" action Function(maybe_show_intro_popup, "daily_report")
    tag menu
    modal True
    zorder 50

    # Filter/cost computations are cached per (day, filters) key and only
    # recomputed when the key changes (they used to run on every render).
    default _dr_key = None
    default _dr_totals = (0, 0, 0)
    default _dr_filtered_reports = []
    default _dr_unique_buildings = ["All Buildings"]
    default _dr_unique_jobs = ["All Jobs"]
    
    add Transform("gui/gallery.png", align=(0.5, 0.5))
    
    frame:
        background None
        xalign 0.3
        yalign 0.5
        xoffset 35
        yoffset 40
        xsize 1700
        ysize 900
        
        # Return button positioned at top-right (outside vbox)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Jump("day_transition")
            xalign 1.0
            yalign 0.0
            xoffset -15  # Slight adjustment from edge
            yoffset 5    # Higher up
        
        vbox:
            spacing 0
            xfill True
            yfill True
            
            # Updated title with date
            $ day_name = day_names[(store.current_day - 1) % 7]
            $ month_name = month_names[store.current_month - 1]
            
            # Calculate totals + filter option lists + filtered rows, all keyed by
            # (day, filters). Recomputed only when the key changes.
            python:
                # Ensure filters are set
                if not hasattr(store, 'building_filter') or store.building_filter is None:
                    store.building_filter = "All Buildings"
                if not hasattr(store, 'daily_report_job_filter') or store.daily_report_job_filter is None:
                    store.daily_report_job_filter = "All Jobs"

                def _dr_building_display(building_name):
                    building = available_buildings.get(building_name, {})
                    btype_id = building.get("type")
                    type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                    parts = building_name.split('_')
                    default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                    return f"{type_name}: {store.custom_names.get(building_name, default_name)}"

                _dr_now_key = (store.current_day, store.building_filter, store.daily_report_job_filter, len(daily_report) if daily_report else 0)
                if _dr_key != _dr_now_key:
                    daily_total_earnings = 0
                    daily_total_costs = 0
                    daily_net_profit = 0
                    filtered_reports = []
                    unique_buildings = ["All Buildings"]
                    unique_jobs = ["All Jobs"]

                    if daily_report:
                        # Building filter options (from all reports)
                        for report in daily_report:
                            full_display_name = _dr_building_display(report.get('building', 'Unknown Building'))
                            if full_display_name not in unique_buildings:
                                unique_buildings.append(full_display_name)

                        # Job filter options (restricted to the selected building)
                        for report in daily_report:
                            if building_filter != "All Buildings" and _dr_building_display(report.get('building', 'Unknown Building')) != building_filter:
                                continue
                            job_name = report.get('profession', 'N/A')
                            if job_name and job_name != 'N/A' and job_name not in unique_jobs:
                                unique_jobs.append(job_name)
                        if store.daily_report_job_filter not in unique_jobs:
                            store.daily_report_job_filter = "All Jobs"

                        # Filter reports (building + job)
                        for report in daily_report:
                            if building_filter != "All Buildings" and _dr_building_display(report.get('building', 'Unknown Building')) != building_filter:
                                continue
                            if store.daily_report_job_filter != "All Jobs" and report.get('profession', 'N/A') != store.daily_report_job_filter:
                                continue
                            filtered_reports.append(report)

                        # Calculate earnings from filtered reports
                        daily_total_earnings = sum(int(report.get("earnings", 0)) for report in filtered_reports)

                        # Calculate costs for filtered buildings
                        for building_name, building in available_buildings.items():
                            if not building.get("owned", False):
                                continue
                            if building_filter != "All Buildings" and _dr_building_display(building_name) != building_filter:
                                continue
                            fixed_cost = get_building_base_maintenance_cost(building_name, building)
                            worker_costs = compute_worker_portion_daily_costs(building.get("assigned_servants") or [], building.get("base_level", 1))[0]
                            bonus_cost = int(((building.get("skill_bonus", 0) // 10) * 100) * get_difficulty_building_skill_mult())
                            daily_total_costs += fixed_cost + worker_costs + bonus_cost

                        daily_net_profit = daily_total_earnings - daily_total_costs

                    _dr_totals = (daily_total_earnings, daily_total_costs, daily_net_profit)
                    _dr_filtered_reports = filtered_reports
                    _dr_unique_buildings = unique_buildings
                    _dr_unique_jobs = unique_jobs
                    # Key uses the possibly-reset job filter so the cache settles immediately
                    _dr_key = (store.current_day, store.building_filter, store.daily_report_job_filter, len(daily_report) if daily_report else 0)

                daily_total_earnings, daily_total_costs, daily_net_profit = _dr_totals
                filtered_reports = _dr_filtered_reports
                unique_buildings = _dr_unique_buildings
                unique_jobs = _dr_unique_jobs
            
            # Title - centered (net total lives in the summary band below)
            $ profit_color = gui.success_color if daily_net_profit >= 0 else gui.danger_color
            $ profit_sign = "+" if daily_net_profit >= 0 else ""
            label "Daily Report: [day_name], [store.current_day] [month_name] [store.current_year]" xalign 0.5 style "header_style" text_size font_size(30)
            
            
            if not daily_report:
                text "No significant events occurred today." size font_size(24) xalign 0.5 color "#ffffff"
            else:
                # Summary band: income / costs / net / active entries (cached totals only)
                $ _dr_active_n = len(filtered_reports)
                hbox:
                    spacing 10
                    xalign 0.5
                    yoffset -30
                    text "Income" size font_size(22) color gui.journal_text_color
                    text "$[daily_total_earnings]" size font_size(22) color gui.success_color
                    text "|" size font_size(22) color gui.parchment_muted_color
                    text "Costs" size font_size(22) color gui.journal_text_color
                    text "$[daily_total_costs]" size font_size(22) color gui.danger_color
                    text "|" size font_size(22) color gui.parchment_muted_color
                    text "Net" size font_size(22) color gui.journal_text_color
                    text "[profit_sign]$[daily_net_profit]" size font_size(22) color profit_color
                    text "|" size font_size(22) color gui.parchment_muted_color
                    text "[_dr_active_n] workers active" size font_size(22) color gui.parchment_muted_color
                hbox:
                    spacing 20
                    xalign 0.5
                    yoffset -35  # Filters nudged up 5px (user request)

                    hbox:
                        spacing 10
                        text "Filter by Building:" size font_size(20) color gui.journal_text_color yalign 0.5

                        # unique_buildings computed in the cached python block above
                        frame:
                            background "#4a2a1acc"
                            padding (10, 5)
                            
                            button:
                                xsize 300
                                ysize 40
                                background "#5a3a1a"
                                hover_background "#6b4a2a"
                                hover_foreground Solid("#6b652820")
                                
                                text "[building_filter]" size font_size(20) color "#ffffff" xalign 0.5 yalign 0.5
                                
                                action Show("building_filter_menu", buildings=unique_buildings)
                    
                    hbox:
                        spacing 10
                        text "Filter by Job:" size font_size(20) color gui.journal_text_color yalign 0.5

                        # unique_jobs computed in the cached python block above
                        frame:
                            background "#4a2a1acc"
                            padding (10, 5)
                            
                            button:
                                xsize 300
                                ysize 40
                                background "#5a3a1a"
                                hover_background "#6b4a2a"
                                hover_foreground Solid("#6b652820")
                                
                                text "[daily_report_job_filter]" size font_size(20) color "#ffffff" xalign 0.5 yalign 0.5
                                
                                action Show("daily_report_job_filter_menu", jobs=unique_jobs)

                # filtered_reports computed in the cached python block above
                if not filtered_reports:
                    text "No events found for the selected building." size font_size(20) xalign 0.5 color "#ffffff"
                else:
                    vbox:
                        spacing 1
                        xoffset 5 # shift entire table (headers + rows) 5px to the right
                        yoffset -60  # Lowered table 30px from filter
                        # Breathing room between the filter row and the column headers
                        # (10: +5px more air before headers, user request)
                        null height 10
                        # Header row (fixed, outside viewport): plain labels over ONE
                        # hairline — EXACTLY the workers-roster structure: header hbox
                        # and rule share one sub-vbox (same origin) and one declared
                        # width equal to the real cell sum, so the rule hugs the
                        # columns instead of floating past them.
                        # Cell sum: 80+10+280+25+280+25+280+25+280+25+360 = 1670.
                        vbox:
                            spacing 6
                            hbox:
                                spacing 0 # Remove default spacing, use manual spacing
                                xsize 1670
                                yalign 0.5
                                button:
                                    background None
                                    xsize 80 # Number column
                                    ysize 30
                                    # Slight right shift for header '#'
                                    text "#" size font_size(22) xalign 0.5 xoffset 12 yalign 0.5
                                null width 10 # Reduced spacing after # column
                                button:
                                    background None
                                    xsize 280 # Restored larger width
                                    ysize 30
                                    text "Building" size font_size(22)
                                null width 25 # Standard spacing after Building (+5)
                                button:
                                    background None
                                    xsize 280 # Restored larger width
                                    ysize 30
                                    text "Job (Skill)" size font_size(22)
                                null width 25 # Standard spacing after Profession (+5)
                                button:
                                    background None
                                    xsize 280 # Restored larger width
                                    ysize 30
                                    text "Worker" size font_size(22)
                                null width 25 # Standard spacing after Worker (+5)
                                button:
                                    background None
                                    xsize 280 # Restored larger width
                                    ysize 30
                                    text "Story" size font_size(22)
                                null width 25 # Standard spacing after Story (+5)
                                button:
                                    background None
                                    xsize 360 # Narrower result column to keep content inside viewport
                                    ysize 30
                                    text "Result (Click for Details)" size font_size(22)
                            # Span [x0+40, x0+1580]: 40px left inset so the rule does
                            # not crash into the panel margin (the # cell starts at
                            # x0 but its glyph sits ~45px in); right end dies ~65px
                            # past the Result label, matching the workers rule. The
                            # group dividers below share this EXACT span (their
                            # container, the row viewport, is offset +10, hence 30).
                            use table_rule(1540, rule_xoffset=40)
                        null height 4

                        # Data rows viewport (only data scrolls, headers stay fixed)
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            ysize 620 # Increased height for more table space
                            xsize 1655 # Match header width
                            xalign 0.0
                            xoffset 10 # Slight offset for alignment
                            vbox:
                                spacing 1
                                # Data rows (Iterate over filtered_reports)
                                # Group rows by building display name (presentation only;
                                # uses the cached filtered_reports and _dr_building_display)
                                python:
                                    _dr_grouped_map = {}
                                    for _dr_rep in filtered_reports:
                                        _dr_grouped_map.setdefault(_dr_building_display(_dr_rep.get('building', 'Unknown Building')), []).append(_dr_rep)
                                    _dr_groups = list(_dr_grouped_map.items())
                                    _dr_nav_reports = []
                                    for _dr_gname, _dr_greps in _dr_groups:
                                        _dr_nav_reports.extend(_dr_greps)
                                    _dr_row_no = 0
                                for _dr_group_name, _dr_group_reports in _dr_groups:
                                    if _dr_group_name != _dr_groups[0][0]:
                                        null height 5
                                        # Same tone and the EXACT same span as the header
                                        # rule (this viewport is offset +10 vs the header's
                                        # container, hence 30 = 40 - 10); thinner weight is
                                        # the only difference, keeping the hierarchy.
                                        add Solid(gui.divider_color) xsize 1540 ysize 2 xoffset 30
                                        null height 5
                                    # Muted building header row before each group. A section
                                    # label: sits a little LEFT of the Building column (a
                                    # hanging indent), well clear of the left margin.
                                    text "[_dr_group_name!q]" size font_size(22) color gui.parchment_muted_color xoffset 60
                                    for report in _dr_group_reports:
                                        $ _dr_row_no += 1
                                        $ i = _dr_row_no
                                        # --- Pre-calculate values needed for the row ---
                                        python:
                                            # Find worker and determine action for worker button
                                            found_worker = find_worker_by_name(report.get('worker_name', 'Unknown'))
                                            if found_worker:
                                                worker_button_action = Show("worker_details", worker=found_worker, in_roster=True)
                                            else:
                                                worker_button_action = NullAction() # Worker not found, button does nothing

                                            # Get building display info
                                            building_name_raw = report.get('building', 'Unknown Building')
                                            building = available_buildings.get(building_name_raw, {})
                                            btype_id = building.get("type")
                                            type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                                            parts = building_name_raw.split('_')
                                            default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name_raw
                                            building_display_name = store.custom_names.get(building_name_raw, default_name)

                                            # Get result text and color
                                            result_text = report.get("result", "N/A")
                                            earnings_text = "$" + str(int(report.get("earnings", 0)))
                                            _dr_earn_val = int(report.get("earnings", 0))
                                            if _dr_earn_val > 0:
                                                _dr_earn_color = gui.success_color
                                            elif _dr_earn_val < 0:
                                                _dr_earn_color = gui.danger_color
                                            else:
                                                _dr_earn_color = gui.parchment_muted_color
                                            if result_text == "Unhandled":
                                                color_code = "#808080"
                                            elif result_text in ["Critical Success", "Success", "Rest"]:
                                                color_code = "#006600"
                                            elif result_text == "Mediocre":
                                                color_code = "#666600"
                                            elif result_text == "Failure":
                                                color_code = "#660000"
                                            elif result_text == "Refused":
                                                color_code = "#663333"
                                            else:
                                                color_code = "#ffffff"

                                            # Small badges next to the worker name: worker level up,
                                            # skill level ups, net HP lost today (see daily_worker_deltas)
                                            _dr_delta = getattr(store, "daily_worker_deltas", {}).get(str(report.get('worker_name', '')), {})
                                            _dr_badges = ""
                                            if _dr_delta:
                                                if _dr_delta.get("level"):
                                                    _dr_badges += " {color=" + gui.gold_color + "}+Lv{/color}"
                                                _dr_sk_n = len(_dr_delta.get("skills", []) or [])
                                                if _dr_sk_n:
                                                    _dr_badges += " {color=" + gui.success_color + "}+" + str(_dr_sk_n) + " skill" + ("s" if _dr_sk_n > 1 else "") + "{/color}"
                                                _dr_hp_loss = _dr_delta.get("hp")
                                                if _dr_hp_loss:
                                                    _dr_badges += " {color=" + gui.danger_color + "}" + str(_dr_hp_loss) + " HP{/color}"
                                        # --- End Pre-calculation ---

                                        hbox:
                                            spacing 0 # Remove default spacing, use manual spacing
                                            xsize 1650 # Match header width to avoid overlap
                                            yalign 0.5
                                            # Number column
                                            button:
                                                background "images/tablebutton.png"
                                                xsize 80 # Number column
                                                ysize 46
                                                # Keep numbers centered horizontally; remove extra xoffset so only header moves
                                                text "[i]" size font_size(21) xalign 0.5 yalign 0.5 yoffset -8
                                            null width 10 # Reduced spacing after # column
                                            # Building column (type: name)
                                            button:
                                                background "images/tablebutton.png"
                                                xsize 280 # Restored larger width
                                                ysize 46
                                                text "[type_name]: [building_display_name]" size font_size(21) # Use pre-calculated display name
                                            null width 25 # Standard spacing after Building (+5)
                                            # Profession column (Job with Skill)
                                            python:
                                                profession_name = report.get('profession', 'N/A')
                                                used_skill = report.get('used_skill', None)
                                                worker_for_skill = report.get('worker', None)
                                                if used_skill and used_skill != "N/A" and worker_for_skill:
                                                    skill_value = calculate_skill_with_traits(worker_for_skill, used_skill, include_libido=False)
                                                    profession_display = f"{profession_name} ({skill_value})"
                                                else:
                                                    profession_display = profession_name
                                            button:
                                                background "images/tablebutton.png"
                                                xsize 280 # Restored larger width
                                                ysize 46
                                                text "[profession_display]" size font_size(21)
                                            null width 25 # Standard spacing after Profession (+5)
                                            # Worker column (name + daily delta badges)
                                            button:
                                                background "images/tablebutton.png"
                                                xsize 280 # Restored larger width
                                                ysize 46
                                                text "[report.get('worker_name', 'Unknown')]{size=17}[_dr_badges]{/size}" size font_size(21) hover_color gui.journal_hover_color
                                                action worker_button_action # Use the pre-calculated action
                                            null width 25 # Standard spacing after Worker (+5)
                                            # Story Name column
                                            button:
                                                background "images/tablebutton.png"
                                                xsize 280 # Restored larger width
                                                ysize 46
                                                text "[report.get('event_data', {}).get('report', 'N/A')]" size font_size(21)
                                            null width 25 # Standard spacing after Story (+5)
                                            # Combined Result & Earnings column (clickable)
                                            button:
                                                background "images/tablebutton.png"
                                                xsize 360
                                                ysize 46
                                                action Show("report_details", report=report, nav_reports=_dr_nav_reports, nav_index=i - 1)
                                                text "{color=[color_code]}[result_text]{/color} {color=[_dr_earn_color]}([earnings_text]){/color}" size font_size(21)

    key "K_BACKSPACE" action Jump("day_transition")


screen building_filter_menu(buildings):
    modal True
    zorder 100
    
    button:
        xfill True
        yfill True
        background None
        action Hide("building_filter_menu")
    
    frame:
        xalign 0.5
        yalign 0.3
        background "#4a2a1acc"
        padding (10, 10)
        
        vbox:
            spacing 5
            
            text "Select Building:" size font_size(20) color "#ffffff" xalign 0.5
            
            null height 10
            
            for building in buildings:
                textbutton "[building]":
                    xsize 300
                    ysize 30
                    background (gui.journal_hover_color if building == getattr(store, "building_filter", None) else "#5a3a1a")
                    hover_background "#6b4a2a"
                    hover_foreground Solid("#6b652820")
                    text_size font_size(16)
                    text_color "#ffffff"
                    text_hover_color gui.journal_hover_color
                    action [
                        SetVariable("building_filter", building),
                        SetVariable("daily_report_job_filter", "All Jobs"),  # Reset job filter when building changes
                        Hide("building_filter_menu")
                    ]
            
            null height 10
            
            textbutton "Cancel":
                xsize 300
                ysize 30
                background "#5a3a1a"
                hover_background "#6b4a2a"
                hover_foreground Solid("#6b652820")
                text_size font_size(16)
                text_color "#ffffff"
                text_hover_color gui.journal_hover_color
                action Hide("building_filter_menu")

    key "K_BACKSPACE" action Hide("building_filter_menu")

screen daily_report_job_filter_menu(jobs):
    modal True
    zorder 100
    
    button:
        xfill True
        yfill True
        background None
        action Hide("daily_report_job_filter_menu")
    
    frame:
        xalign 0.5
        yalign 0.3
        background "#4a2a1acc"
        padding (10, 10)
        
        vbox:
            spacing 5
            
            text "Select Job:" size font_size(20) color "#ffffff" xalign 0.5
            
            null height 10
            
            for job in jobs:
                textbutton "[job]":
                    xsize 300
                    ysize 30
                    background (gui.journal_hover_color if job == getattr(store, "daily_report_job_filter", None) else "#5a3a1a")
                    hover_background "#6b4a2a"
                    hover_foreground Solid("#6b652820")
                    text_size font_size(16)
                    text_color "#ffffff"
                    text_hover_color gui.journal_hover_color
                    action [
                        SetVariable("daily_report_job_filter", job),
                        Hide("daily_report_job_filter_menu")
                    ]
            
            null height 10
            
            textbutton "Cancel":
                xsize 300
                ysize 30
                background "#5a3a1a"
                hover_background "#6b4a2a"
                hover_foreground Solid("#6b652820")
                text_size font_size(16)
                text_color "#ffffff"
                text_hover_color gui.journal_hover_color
                action Hide("daily_report_job_filter_menu")

    key "K_BACKSPACE" action Hide("daily_report_job_filter_menu")

screen report_details(report, nav_reports=None, nav_index=None):
    zorder 100
    modal True
    add Solid("#000000")
    
    python:
        _candidate_reports = [r for r in (nav_reports or []) if hasattr(r, "get")]
        _nav_reports = _candidate_reports if _candidate_reports else [r for r in daily_report if hasattr(r, "get")]
        if not _nav_reports:
            _nav_reports = [report] if hasattr(report, "get") else [{"description": "No description available."}]

        # Resolve the current report inside the active navigation sequence.
        if nav_index is not None and 0 <= nav_index < len(_nav_reports) and _nav_reports[nav_index] == report:
            current_report_index = nav_index
        else:
            current_report_index = next((i for i, r in enumerate(_nav_reports) if r == report), 0)

        report = _nav_reports[current_report_index]
        worker = report.get("worker", {})
        event = report.get("event_data", {})
        outcome = report.get("result", "").lower().replace(" ", "_")
        skill_name = report.get("used_skill", None)
        selected_media = report.get("story_image")
        if not selected_media:
            selected_media = get_event_image(worker, event, outcome, skill_name)
        event_description = report.get("description", "No description available.") if hasattr(report, "get") else "No description available."
        loot_items = (report.get("loot", []) or []) if hasattr(report, "get") else []

        can_go_previous = current_report_index > 0
        can_go_next = current_report_index < len(_nav_reports) - 1
        story_number = current_report_index + 1
        total_stories = len(_nav_reports)
    
    hbox:
        spacing 0
        xfill True
        yfill True
        
        fixed:
            xsize 1600
            ysize 1080
            yalign 0.5
            add Solid("#000000dd"):
                xsize 1600
                ysize 1080
                align (0.5, 0.5)
            if selected_media and selected_media.lower().endswith(('.webm', '.mp4')):
                add Movie(
                    play=selected_media,
                    size=(1600, 900),
                    loop=True
                )
            elif selected_media:
                add selected_media:
                    fit "contain"
                    xysize (1600, 900)
                    align (0.5, 0.5)
            else:
                # Fallback when no image is found
                text "No image available":
                    align (0.5, 0.5)
                    size 24

        frame:
            xsize 320
            yfill True
            background context_menu_bg
            vbox:
                spacing 20
                xalign 0.5
                yalign 0.5
                xfill True
                
                # Story number and navigation info
                text "Story [story_number] of [total_stories]" size font_size(26) color "#ffffff" xalign 0.5 bold True
                
                frame:
                    background Solid("#1a1a1acc")
                    xsize 300
                    ysize 600
                    padding (10, 10)
                    xalign 0.5
                    viewport:
                        scrollbars None
                        mousewheel True
                        draggable True
                        vbox:
                            text "[event_description]" size font_size(24) color "#ffffff" xalign 0.0 text_align 0.0 substitute True
                            if loot_items:
                                text ""  # Blank line for spacing
                                text "Loot Obtained:" size font_size(24) color "#006600" bold True
                                for item in loot_items:
                                    # If 'item' is a string (the id), look it up in items_json
                                    if isinstance(item, str):
                                        $ item_data = next((i for i in items_json["items"] if i["id"] == item), {"display_name": item})
                                    else:
                                        $ item_data = item  # Assume it's already a dictionary
                                    $ display_name = item_data.get("display_name", item_data.get("id", "Unknown Item"))
                                    text "{color=#aaaaaa}[display_name]{/color}" size 22
                # Previous button (disabled if on first story)
                if can_go_previous:
                    button:
                        xalign 0.0
                        xsize 290
                        ysize 50
                        background None
                        text "Previous" color "#ffffff" hover_color gui.journal_hover_color xalign 0.0
                        action [
                            SetVariable("current_report_index", current_report_index - 1),
                            Show("report_details", report=_nav_reports[current_report_index - 1], nav_reports=_nav_reports, nav_index=current_report_index - 1)
                        ]
                else:
                    button:
                        xalign 0.0
                        xsize 290
                        ysize 50
                        background None
                        text "Previous" color "#666666" xalign 0.0
                        action NullAction()
                
                # Next button (disabled if on last story)
                if can_go_next:
                    button:
                        xalign 0.0
                        xsize 290
                        ysize 50
                        background None
                        text "Next" color "#ffffff" hover_color gui.journal_hover_color xalign 0.0
                        action [
                            SetVariable("current_report_index", current_report_index + 1),
                            Show("report_details", report=_nav_reports[current_report_index + 1], nav_reports=_nav_reports, nav_index=current_report_index + 1)
                        ]
                else:
                    button:
                        xalign 0.0
                        xsize 290
                        ysize 50
                        background None
                        text "Next" color "#666666" xalign 0.0
                        action NullAction()
                
                textbutton "Close":
                    xalign 0.0
                    text_color "#ffffff"
                    action Hide("report_details")

    key "K_BACKSPACE" action Hide("report_details")
    # Ctrl+Left/Right mirror the Previous/Next buttons (only bound when the
    # corresponding button is active, same conditions as above).
    if can_go_previous:
        key "ctrl_K_LEFT" action [
            SetVariable("current_report_index", current_report_index - 1),
            Show("report_details", report=_nav_reports[current_report_index - 1], nav_reports=_nav_reports, nav_index=current_report_index - 1)
        ]
    if can_go_next:
        key "ctrl_K_RIGHT" action [
            SetVariable("current_report_index", current_report_index + 1),
            Show("report_details", report=_nav_reports[current_report_index + 1], nav_reports=_nav_reports, nav_index=current_report_index + 1)
        ]

screen tavern():
    on "show" action Function(maybe_show_intro_popup, "tavern")
    # Persistent flags are now cleared at the start of _apply_pending_snapshot_and_show_tavern
    # Just ensure _context_restored is cleared if it was set
    if getattr(persistent, "_context_restored", False):
        $ persistent._context_restored = False
        $ renpy.save_persistent()
    zorder 1
    # Tavern background adjusted to 1515px width to account for side panel
    add tavern_bg:
        xsize 1515
        ysize 1080
        xalign 0.0
        yalign 0.0
    # Draw decorative PNG centered behind the menu so it doesn't get clipped
    add context_menu_bg xalign 0.5 yalign 0.5
    frame:
        xalign 1.0
        yalign 0.5
        xsize 320
        ysize 1.0
        background None
        
        # Help/Information button - positioned in top-right corner of context menu (green panel)
        python:
            screen_name = "tavern"
            tooltips_enabled = get_tooltips_state_for_screen(screen_name)
        
        imagebutton:
            idle Transform("gui/info_idle.png", zoom=0.315)
            hover Transform("gui/info_hover.png", zoom=0.315)
            selected_idle Transform("gui/info_active.png", zoom=0.315)
            selected_hover Transform("gui/info_active.png", zoom=0.315)
            selected tooltips_enabled
            action [Function(lambda: toggle_tooltips_for_screen("tavern"))]
            hovered ShowTransient("tooltip", message="Tooltips: {color=#ffffff}On{/color}/Off", screen_name=screen_name)
            unhovered Hide("tooltip")
            xalign 1.0
            xoffset -60
            yalign 0.0
            yoffset 55
        
        vbox:
            xalign 1.0
            yalign 0.5
            xoffset -5
            spacing 10
            textbutton "Journal":
                action Show("journal_panel")
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered ShowTransient("tooltip", message="View your quest objectives and track your progress", screen_name="tavern")
                unhovered Hide("tooltip")
            textbutton "Explore":
                action [
                    Function(renpy.log, "Explore button clicked"),
                    Hide("tavern"),
                    Show("map_screen")
                ]
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered ShowTransient("tooltip", message="Explore the city map and visit different locations", screen_name="tavern")
                unhovered Hide("tooltip")
            textbutton "Buildings":
                action [
                    Function(renpy.log, "Manage Buildings button clicked"),
                    Function(rebuild_assigned_servants),
                    Show("Building_select_global")
                ]
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered ShowTransient("tooltip", message="Manage your buildings, upgrade them, and adjust settings", screen_name="tavern")
                unhovered Hide("tooltip")
            textbutton "Workers":
                action [
                    Function(renpy.log, "Workers button clicked"),
                    Hide("tavern"),
                    Show("workers")
                ]
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered ShowTransient("tooltip", message="View and manage your workers roster", screen_name="tavern")
                unhovered Hide("tooltip")
            $ _storage_roster = workers_filtered_by_gender(store.workers)
            textbutton "Storage":
                action [
                    SetVariable("left_worker", None),
                    SetVariable("right_worker", (_storage_roster[0] if _storage_roster else False)),
                    Show("manager_inventory", return_to_tavern=True),
                    Hide("tavern")
                ]
                xsize 300
                text_size 42
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                hovered ShowTransient("tooltip", message="Open storage to manage items and equipment.", screen_name="tavern")
                unhovered Hide("tooltip")
            textbutton "Next Day":
                action [
                    Function(renpy.log, "Next Day button clicked"),
                    Hide("tavern"),
                    Jump("next_day")
                ]
                xsize 300
                text_size 42
                text_color gui.journal_hover_color
                text_hover_color "#ffffff"
                hovered ShowTransient("tooltip", message="Advance to the next day and process daily events", screen_name="tavern")
                unhovered Hide("tooltip")


    # Money and Date positioned over context menu area
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        # Money display with icon-style $ symbol
        hbox:
            spacing 5
            text "$" color gui.journal_dark_color size 22 bold True yalign 0.5
            text "[format(int(money), ',')]" color gui.journal_dark_color size 28 yalign 0.5
        # Calendar display with icon
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]  # Map day 1-28 to 7-day week
            $ month_name = month_names[store.current_month - 1]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color gui.journal_dark_color size 25 yalign 0.5
        # Compact status strip: roster size and owned holdings (read-only)
        python:
            _tv_worker_count = len(store.workers)
            _tv_building_count = len(getattr(store, "owned_buildings", []) or [])
        text "Workers: [_tv_worker_count]      Buildings: [_tv_building_count]" color gui.journal_dark_color size 20
        # Player title and name (click to open character sheet) — blink when pending skill points
        if manager_has_unspent_skill_points():
            timer 0.7 repeat True action ToggleVariable("manager_name_blink_highlight")
        python:
            _manager_name_color = gui.journal_hover_color if (getattr(store, 'manager_name_blink_highlight', False) and manager_has_unspent_skill_points()) else gui.journal_dark_color
        textbutton "[player_title] [player_name]":
            action Show("manager_character_sheet")
            text_color _manager_name_color
            text_hover_color gui.journal_hover_color
            text_size 24
            text_italic True
            background None
            hover_background None

style tavern_frame:
    background "#00000080"  # Semi-transparent black
    padding (20, 20)

style tavern_title:
    color "#ffffff"
    size 24
    bold True
    xalign 0.0

style tavern_text:
    color "#ffffff"
    size 20

style tavern_button:
    background "#00000080"
    hover_background "#000000c0"
    padding (10, 5)
    xsize 160

screen tutorial_dialogue_trigger():
    if hasattr(store, 'objective_just_completed') and store.objective_just_completed > 0:
        $ current_objective = store.objective_just_completed
        $ label_name = "show_objective_%d_dialogue" % current_objective
        $ renpy.log(f"DEBUG: tutorial_dialogue_trigger - objective_just_completed: {current_objective}, returning to script")
        timer 0.1 action [
            SetVariable("objective_just_completed", 0),
            Return("objective_" + str(current_objective))
        ]
## Load/Save slot screen ######################################################

screen load_save_slot(number):
    $ file_text = "% s\n%s" % (FileTime(number, empty="Empty Slot"), FileSaveName(number))
    add FileScreenshot(number) xpos -1 ypos 0
    frame:
        xpos -1
        ypos 0
        xsize config.thumbnail_width
        ysize config.thumbnail_height
        background Solid("#00000099")
        text file_text:
            xalign 0.5
            yalign 0.5
            size font_size(24)
            color "#ffffff"

## Configure thumbnail size for save slots
init python:
    config.thumbnail_width = 393
    config.thumbnail_height = 207

## Gallery screen ##############################################################

screen gallery():

    tag menu
    
    add "gui/gallery.png"
    
    ## Simple placeholder content
    vbox:
        xalign 0.5
        yalign 0.5
        spacing 50
        
        text "Gallery" size font_size(60) color gui.journal_dark_color xalign 0.5
        text "Coming Soon..." size font_size(40) color "#887441" xalign 0.5
        
        textbutton "Return" action Return() xalign 0.5 text_size font_size(30)

    key "K_BACKSPACE" action Return()

screen worker_building_filter_menu(buildings):
    modal True
    zorder 100
    
    button:
        xfill True
        yfill True
        background None
        action Hide("worker_building_filter_menu")
    
    frame:
        xalign 0.5
        yalign 0.3
        background "#4a2a1acc"
        padding (10, 10)
        
        vbox:
            spacing 5
            
            text "Select Building:" size font_size(20) color "#ffffff" xalign 0.5
            
            null height 10
            
            for building in buildings:
                textbutton "[building]":
                    xsize 300
                    ysize 30
                    background (gui.journal_hover_color if building == getattr(store, "worker_building_filter", None) else "#5a3a1a")
                    hover_background "#6b4a2a"
                    hover_foreground Solid("#6b652820")
                    text_size font_size(16)
                    text_color "#ffffff"
                    text_hover_color gui.journal_hover_color
                    action [
                        SetVariable("worker_building_filter", building),
                        SetVariable("worker_job_filter", "All Jobs"),  # Reset job filter when building changes
                        Hide("worker_building_filter_menu")
                    ]
            
            null height 10
            
            textbutton "Cancel":
                xsize 300
                ysize 30
                background "#5a3a1a"
                hover_background "#6b4a2a"
                hover_foreground Solid("#6b652820")
                text_size font_size(16)
                text_color "#ffffff"
                text_hover_color gui.journal_hover_color
                action Hide("worker_building_filter_menu")

    key "K_BACKSPACE" action Hide("worker_building_filter_menu")

screen worker_job_filter_menu(jobs):
    modal True
    zorder 100
    
    button:
        xfill True
        yfill True
        background None
        action Hide("worker_job_filter_menu")
    
    frame:
        xalign 0.5
        yalign 0.3
        background "#4a2a1acc"
        padding (10, 10)
        
        vbox:
            spacing 5
            
            text "Select Job:" size font_size(20) color "#ffffff" xalign 0.5
            
            null height 10
            
            for job in jobs:
                textbutton "[job]":
                    xsize 300
                    ysize 30
                    background (gui.journal_hover_color if job == getattr(store, "worker_job_filter", None) else "#5a3a1a")
                    hover_background "#6b4a2a"
                    hover_foreground Solid("#6b652820")
                    text_size font_size(16)
                    text_color "#ffffff"
                    text_hover_color gui.journal_hover_color
                    action [
                        SetVariable("worker_job_filter", job),
                        Hide("worker_job_filter_menu")
                    ]
            
            null height 10
            
            textbutton "Cancel":
                xsize 300
                ysize 30
                background "#5a3a1a"
                hover_background "#6b4a2a"
                hover_foreground Solid("#6b652820")
                text_size font_size(16)
                text_color "#ffffff"
                text_hover_color gui.journal_hover_color
                action Hide("worker_job_filter_menu")

    key "K_BACKSPACE" action Hide("worker_job_filter_menu")
