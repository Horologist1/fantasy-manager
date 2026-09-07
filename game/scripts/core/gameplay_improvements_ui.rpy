# gameplay_improvements_ui.rpy
# Isolated modal UI so existing dense screens only gain compact entry buttons.

default auto_advance_requested_days = 1
default auto_advance_pending_result = None

# Shared visual language for roster-management modal actions.
style fm_panel_button is button:
    background "#5a3a1a"
    hover_background "#6b4a2a"
    insensitive_background "#8d7a66"
    padding (14, 8)

style fm_panel_button_text is button_text:
    color "#ffffff"
    hover_color "#ffffff"
    insensitive_color "#d2c2ae"
    xalign 0.5
    yalign 0.5
    text_align 0.5

style fm_danger_button is fm_panel_button:
    background "#7b342f"
    hover_background "#98443d"

style fm_danger_button_text is fm_panel_button_text:
    color "#ffffff"
    hover_color "#ffffff"

screen building_skill_policy(building_name):
    modal True
    zorder 120
    on "show" action SetVariable("_last_tooltip_screen", "building_skill_policy")
    on "hide" action Hide("tooltip")
    add Solid("#00000055")
    python:
        _policy_building, _policy_key = _resolve_building_by_name(building_name)
        _policy_building = _policy_building or {}
        _policy_btype_id = _policy_building.get("type")
        _policy_btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == _policy_btype_id), None)
        _policy_type_visible = building_type_is_visible(_policy_btype)
        _policy_skills = get_building_policy_skills(_policy_building, _policy_btype) if _policy_type_visible else []
        _policy_allowed_male, _policy_total_male = get_building_policy_story_counts(_policy_building, _policy_btype, "male")
        _policy_allowed_female, _policy_total_female = get_building_policy_story_counts(_policy_building, _policy_btype, "female")
        _policy_tradeoff = get_building_policy_tradeoff(_policy_building, _policy_btype)
        _policy_screen_name = "building_skill_policy"
        _policy_tooltips_enabled = get_tooltips_state_for_screen(_policy_screen_name)
        _policy_mouse_x, _policy_mouse_y = renpy.get_mouse_pos()
        _policy_tooltip_x = min(_policy_mouse_x + 20, config.screen_width - 340)
        _policy_tooltip_y = max(20, min(_policy_mouse_y - 20, config.screen_height - 220))
        _policy_help_text = (
            "Click to cycle this skill: Allowed -> Male banned -> Female banned -> Both banned. "
            "Each restricted skill grants +2 Focus to workers of the matching gender (max +10). "
            "Restricted services can cause a missed request: one daily story for $0; reputation is unaffected. "
            "Risk increases by 5% per restricted skill and caps at 25%."
        )

    frame:
        xalign 0.5
        yalign 0.5
        # Match worker_history_popup's top edge and close-button screen margin.
        yoffset -42
        xsize 820
        ysize 780
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (66, 62, 66, 40)

        vbox:
            spacing 10
            xsize 620
            xalign 0.5
            yalign 0.0

            # SKILL_POLICY_HEADER_CONTRACT: balanced actions keep the title truly centered.
            fixed:
                xfill True
                ysize 58
                label "SKILL POLICY" xalign 0.5 yalign 0.5 style "header_style"
                imagebutton:
                    idle Transform("gui/button/return_idle.png", zoom=(0.60 if renpy.variant("touch") else 0.46))
                    hover Transform("gui/button/return_hover.png", zoom=(0.60 if renpy.variant("touch") else 0.46))
                    action Hide("building_skill_policy")
                    xalign 1.0
                    yalign 0.5

            # SKILL_POLICY_SUMMARY_CONTRACT: one centered block directly under the title.
            vbox:
                spacing 4
                xalign 0.5
                text "Male stories: [_policy_allowed_male]/[_policy_total_male]    Focus: +[_policy_tradeoff['male_focus_bonus']]" size font_size(21) color gui.journal_hover_color xalign 0.5 text_align 0.5
                text "Female stories: [_policy_allowed_female]/[_policy_total_female]    Focus: +[_policy_tradeoff['female_focus_bonus']]" size font_size(21) color gui.journal_hover_color xalign 0.5 text_align 0.5
                text "Missed-request risk: [int(_policy_tradeoff['incident_chance'] * 100)]% per building/day" size font_size(21) color gui.journal_hover_color xalign 0.5 text_align 0.5

            # SKILL_POLICY_TABLE_CONTRACT: stable columns, row-sized targets, and hover help.
            fixed:
                xsize 560
                xalign 0.5
                ysize 24
                imagebutton:
                    idle Transform("gui/info_idle.png", zoom=0.315)
                    hover Transform("gui/info_hover.png", zoom=0.315)
                    selected_idle Transform("gui/info_active.png", zoom=0.315)
                    selected_hover Transform("gui/info_active.png", zoom=0.315)
                    selected _policy_tooltips_enabled
                    action Function(toggle_tooltips_for_screen, _policy_screen_name)
                    hovered Show("tooltip", message="Skill Policy help: {color=#ffffff}On{/color}/Off", xpos=_policy_tooltip_x, ypos=_policy_tooltip_y, screen_name=_policy_screen_name)
                    unhovered Hide("tooltip")
                    xalign 0.0
                    xoffset 18
                    yalign 0.5
            # Wheel/drag-scrollable, clipped to the parchment (no shaded box, no scrollbar widget)
            viewport:
                scrollbars None
                mousewheel True
                draggable True
                xsize 560
                xalign 0.5
                ysize 440
                vbox:
                    spacing 2
                    xfill True
                    if _policy_skills:
                        for _policy_index, skill_name in enumerate(_policy_skills):
                            python:
                                _skill_banned_genders = get_building_banned_skill_genders(_policy_building, skill_name)
                                if _skill_banned_genders == ["male"]:
                                    _skill_policy_label = "Male banned"
                                elif _skill_banned_genders == ["female"]:
                                    _skill_policy_label = "Female banned"
                                elif _skill_banned_genders:
                                    _skill_policy_label = "Both banned"
                                else:
                                    _skill_policy_label = "Allowed"
                            button:
                                xfill True
                                ysize 46
                                background (gui.row_alt_color if _policy_index % 2 else None)
                                hover_background "#4a2a1a18"
                                padding (8, 4)
                                action Function(cycle_building_banned_skill_mode, _policy_building, skill_name)
                                hovered If(get_tooltips_state_for_screen(_policy_screen_name), Show("tooltip", message=_policy_help_text, xpos=_policy_tooltip_x, ypos=_policy_tooltip_y, screen_name=_policy_screen_name), NullAction())
                                unhovered Hide("tooltip")
                                hbox:
                                    spacing 0
                                    yalign 0.5
                                    fixed:
                                        xsize 312
                                        ysize 38
                                        text "[skill_name!q]" size font_size(25) color gui.journal_text_color hover_color gui.journal_hover_color yalign 0.5
                                    fixed:
                                        xsize 220
                                        ysize 38
                                        text "[_skill_policy_label]" size font_size(23) color (_skill_banned_genders and gui.danger_color or gui.journal_text_color) hover_color gui.journal_hover_color yalign 0.5
                    else:
                        text "This building type has no visible selectable story skills." size font_size(24) color gui.parchment_muted_color xalign 0.5
    key "K_BACKSPACE" action Hide("building_skill_policy")

screen batch_worker_manager(worker_pool=None):
    modal True
    zorder 120
    on "show" action Function(batch_prepare_selection, list(worker_pool if worker_pool is not None else workers_filtered_by_gender(store.workers)))
    add Solid("#00000055")
    python:
        _batch_pool = list(worker_pool if worker_pool is not None else workers_filtered_by_gender(store.workers))
        _batch_valid_names = {worker.get("name") for worker in _batch_pool if hasattr(worker, "get")}
        _batch_selected = {name for name in (store.batch_selected_worker_names or []) if name in _batch_valid_names}
        _batch_selected_workers = [worker for worker in _batch_pool if worker.get("name") in _batch_selected]
        _batch_buildings = [_resolve_building_key(worker.get("assigned_building")) for worker in _batch_selected_workers]
        _batch_common_building = _batch_buildings[0] if _batch_buildings and all(value == _batch_buildings[0] for value in _batch_buildings) else None

    # Daily Report's native panoramic parchment; never stretch the square journal crop.
    add Transform("gui/gallery.png", align=(0.5, 0.5))

    # PARCHMENT_SAFE_AREA_CONTRACT: content stays inside the woven inner frame.
    frame:
        xalign 0.5
        yalign 0.5
        xsize 1700
        ysize 900
        background None
        padding (225, 60, 225, 70)
        # BIBLIA §12: close in the top-right CORNER, above the title (direct frame
        # child). The +205 xoffset cancels most of the 225 right-padding so it
        # lands near the woven border like daily_report, not deep in the content.
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("batch_worker_manager")
            xalign 1.0
            yalign 0.0
            xoffset 190
            yoffset -5
        vbox:
            spacing 16
            xfill True

            label "BATCH MANAGEMENT" xalign 0.5 style "header_style"

            # Selection toolbar
            hbox:
                spacing 8
                xalign 0.5
                textbutton "Select All":
                    style "fm_panel_button"
                    xsize 132
                    ysize 42
                    text_size font_size(21)
                    action Function(batch_select_workers, _batch_pool, "all")
                textbutton "Tired":
                    style "fm_panel_button"
                    xsize 106
                    ysize 42
                    text_size font_size(21)
                    action Function(batch_select_workers, _batch_pool, "tired")
                textbutton "Unassigned":
                    style "fm_panel_button"
                    xsize 142
                    ysize 42
                    text_size font_size(21)
                    action Function(batch_select_workers, _batch_pool, "unassigned")
                textbutton "Clear":
                    style "fm_panel_button"
                    xsize 100
                    ysize 42
                    text_size font_size(21)
                    action Function(batch_select_workers, _batch_pool, "clear")
                null width 12
                frame:
                    background "#4a2a1a18"
                    padding (14, 7)
                    ysize 42
                    text "Selected: [len(_batch_selected)] / [len(_batch_pool)]" size font_size(21) color gui.journal_text_color yalign 0.5

            hbox:
                spacing 30
                xsize 1250
                xalign 0.5

                # Worker selection panel.
                frame:
                    xsize 800
                    ysize 600
                    background "#4a2a1a12"
                    padding (20, 16)
                    vbox:
                        spacing 6
                        xsize 760
                        hbox:
                            spacing 0
                            xsize 740
                            xalign 0.5
                            null width 40
                            fixed:
                                xsize 220
                                ysize 28
                                text "WORKERS" size font_size(25) color gui.journal_text_color xalign 0.0 yalign 0.5
                            null width 8
                            fixed:
                                xsize 472
                                ysize 28
                                text "CURRENT ASSIGNMENT" size font_size(20) color gui.journal_text_color xalign 0.5 yalign 0.5
                        hbox:
                            spacing 0
                            xsize 740
                            xalign 0.5
                            null width 268
                            fixed:
                                xsize 160
                                ysize 22
                                text "BUILDING" size font_size(20) color gui.journal_text_color xalign 0.5 yalign 0.5
                            null width 8
                            fixed:
                                xsize 304
                                ysize 22
                                text "JOB" size font_size(20) color gui.journal_text_color xalign 0.5 yalign 0.5
                        viewport:
                            scrollbars None
                            mousewheel True
                            draggable True
                            xsize 760
                            ysize 506
                            vbox:
                                spacing 4
                                xfill True
                                for _batch_idx, worker in enumerate(_batch_pool):
                                    $ _batch_checked = worker.get("name") in _batch_selected
                                    $ _batch_building_cell, _batch_job_cell = get_batch_assignment_cells(worker)
                                    $ _batch_name_cell = compact_table_text(str(worker.get('name', 'Unknown')), 18)
                                    $ _batch_building_cell = compact_table_text(str(_batch_building_cell), 16)
                                    $ _batch_job_cell = compact_table_text(str(_batch_job_cell), 24)
                                    $ _batch_checkbox_asset = "gui/icons/batch_checkbox_on.png" if _batch_checked else "gui/icons/batch_checkbox_off.png"
                                    button:
                                        xfill True
                                        ysize 42
                                        padding (10, 5)
                                        background ("#6b652838" if _batch_checked else (gui.row_alt_color if _batch_idx % 2 else "#00000000"))
                                        hover_background "#6b4a2a24"
                                        action Function(batch_toggle_worker, worker.get("name"))
                                        hbox:
                                            xfill True
                                            spacing 8
                                            fixed:
                                                xsize 32
                                                ysize 32
                                                add Transform(_batch_checkbox_asset, xysize=(26, 26)) xalign 0.5 yalign 0.5
                                            fixed:
                                                xsize 220
                                                ysize 32
                                                text "[_batch_name_cell!q]" size font_size(22) color gui.journal_text_color xalign 0.0 yalign 0.5
                                            fixed:
                                                xsize 160
                                                ysize 32
                                                text "[_batch_building_cell!q]" size font_size(19) color gui.journal_text_color xalign 0.5 yalign 0.5
                                            fixed:
                                                xsize 304
                                                ysize 32
                                                text "[_batch_job_cell!q]" size font_size(20) color gui.journal_text_color xalign 0.5 yalign 0.5

                # Action panel with clear functional groups.
                frame:
                    xsize 420
                    ysize 600
                    background "#4a2a1a12"
                    padding (20, 16)
                    vbox:
                        spacing 10
                        xfill True
                        text "ACTIONS" size font_size(25) color gui.journal_text_color xalign 0.5
                        textbutton "Assign Building":
                            style "fm_panel_button"
                            xfill True
                            ysize 44
                            text_size font_size(23)
                            sensitive bool(_batch_selected)
                            action Show("batch_building_picker", worker_pool=_batch_pool)
                        textbutton "Assign Job":
                            style "fm_panel_button"
                            xfill True
                            ysize 44
                            text_size font_size(23)
                            sensitive bool(_batch_selected) and bool(_batch_common_building)
                            action Show("batch_job_picker", building_name=_batch_common_building, worker_pool=_batch_pool)
                            hovered ShowTransient("tooltip", message="Job assignment requires every selected worker to be in the same building.", screen_name="batch_worker_manager")
                            unhovered Hide("tooltip")
                        textbutton "Set to Rest":
                            style "fm_panel_button"
                            xfill True
                            ysize 44
                            text_size font_size(23)
                            sensitive bool(_batch_selected)
                            action [Function(batch_rest_workers), Function(renpy.notify, "Batch rest applied")]
                        textbutton "Unassign":
                            style "fm_panel_button"
                            xfill True
                            ysize 44
                            text_size font_size(23)
                            sensitive bool(_batch_selected)
                            action Confirm("Unassign all selected workers from their buildings?", Function(batch_unassign_workers), NullAction())
                        null height 4
                        text "AUTOMATION" size font_size(22) color gui.journal_text_color xalign 0.5
                        textbutton "Auto-fill Building":
                            style "fm_panel_button"
                            xfill True
                            ysize 42
                            text_size font_size(22)
                            action Show("autofill_building_picker")
                        textbutton "Save Current Layout":
                            style "fm_panel_button"
                            xfill True
                            ysize 42
                            text_size font_size(22)
                            action Function(renpy.invoke_in_new_context, prompt_and_save_preset)
                        textbutton "Manage Presets":
                            style "fm_panel_button"
                            xfill True
                            ysize 42
                            text_size font_size(22)
                            sensitive bool(getattr(store, "assignment_presets", {}))
                            action Show("preset_picker")
                        frame:
                            xfill True
                            background "#4a2a1a18"
                            padding (12, 7)
                            text "Building changes clear jobs. Full jobs safely skip overflow workers." size font_size(19) color gui.journal_text_color text_align 0.5 xalign 0.5
    key "K_BACKSPACE" action Hide("batch_worker_manager")

screen autofill_building_picker():
    modal True
    zorder 121
    add Solid("#00000055")
    # BIBLIA §12: close in the top-right CORNER (direct frame child, above the
    # title); 720-wide family so the centered title clears the corner button.
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 620
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (50, 50, 50, 38)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("autofill_building_picker")
            xalign 1.0
            yalign 0.0
            xoffset -5
            yoffset -55
        vbox:
            spacing 10
            xfill True
            null height 15
            label "AUTO-FILL BUILDING" xalign 0.5 style "header_style"
            text "Reoptimizes normal roles using workers already in the building plus globally unassigned workers. Existing professions do not lock workers in place; Manager, Rest, and other buildings are preserved. The three-dot button edits the final role plan." size font_size(20) color gui.journal_text_color xalign 0.5 text_align 0.5
            viewport:
                scrollbars None
                mousewheel True
                draggable True
                xsize 440
                # 290 keeps the whole vbox (title + 3-line subtitle + rows) inside
                # the 452px content area; 320 overflowed the parchment by ~23px.
                ysize 290
                xalign 0.5
                vbox:
                    spacing 7
                    xfill True
                    for _af_bkey in store.owned_buildings:
                        $ _af_b = available_buildings.get(_af_bkey, {})
                        if hasattr(_af_b, "get") and is_standard_managed_building(_af_bkey, _af_b):
                            # Building names are user-renamable -> !q (BIBLIA §9)
                            $ _af_disp = getattr(store, "custom_names", {}).get(_af_bkey, _af_b.get("display_name", _af_bkey))
                            $ _af_custom = building_has_autofill_quotas(_af_bkey)
                            hbox:
                                spacing 6
                                xfill True
                                textbutton "[_af_disp!q]":
                                    xsize 380
                                    ysize 46
                                    text_size font_size(25)
                                    text_color gui.journal_text_color
                                    text_hover_color gui.journal_hover_color
                                    action [Function(autofill_building, _af_bkey), Hide("autofill_building_picker")]
                                textbutton "...":
                                    xsize 46
                                    ysize 46
                                    yalign 0.5
                                    background "#5a3a1a"
                                    hover_background "#6b4a2a"
                                    text_size font_size(24)
                                    text_color ("#f5d76e" if _af_custom else "#ffffff")
                                    text_hover_color "#f5e6d3"
                                    text_xalign 0.5
                                    text_yalign 0.5
                                    left_padding 0
                                    right_padding 0
                                    top_padding 0
                                    bottom_padding 8
                                    action Show("autofill_settings", building_name=_af_bkey)
    key "K_BACKSPACE" action Hide("autofill_building_picker")

# Per-building Auto-fill plan: target headcount per profession. Max (default)
# keeps the legacy fill-to-capacity behavior; a number caps how many workers
# auto-fill may staff into that job. Shared by every auto-fill entry point.
screen autofill_settings(building_name):
    modal True
    zorder 122
    add Solid("#00000055")
    python:
        _afs_resolved, _afs_building, _afs_btype = _fm_building_and_btype(building_name)
        _afs_profs = []
        if _afs_resolved and hasattr(_afs_btype, "get"):
            for _afs_p in _afs_btype.get("professions", []) or []:
                if not hasattr(_afs_p, "get"):
                    continue
                _afs_pid = str(_afs_p.get("id", "")).strip().lower()
                _afs_pname = str(_afs_p.get("name", _afs_pid) or _afs_pid)
                if _afs_pid in ("manager", "rest") or _afs_pname.strip().lower() in ("manager", "rest"):
                    continue
                if not profession_is_unlocked(_afs_p) or not profession_is_visible(_afs_p, _afs_btype):
                    continue
                _afs_cap = get_max_daily_workers(_afs_building, _afs_p)
                _afs_holders = _fm_job_holder_count(_afs_resolved, _afs_building, _afs_pid)
                _afs_profs.append((_afs_pid, _afs_pname, _afs_cap, _afs_holders))
        # Drop targets of professions that no longer exist (idempotent).
        prune_autofill_quotas(building_name, [t[0] for t in _afs_profs])
        _afs_trim = bool(_afs_building.get("autofill_allow_unassign", False)) if hasattr(_afs_building, "get") else False
    # BIBLIA §12: close in the top-right CORNER (direct frame child, above the
    # title); 720-wide family so the centered title clears the corner button.
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 620
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (50, 50, 50, 38)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("autofill_settings")
            xalign 1.0
            yalign 0.0
            xoffset -5
            yoffset -55
        vbox:
            spacing 10
            xfill True
            null height 15
            label "AUTO-FILL PLAN" xalign 0.5 style "header_style"
            text "Target workers per profession. Max fills every slot (default); a number stops Auto-fill at that headcount." size font_size(20) color gui.journal_text_color xalign 0.5 text_align 0.5
            $ _afs_checkbox_asset = "gui/icons/batch_checkbox_on.png" if _afs_trim else "gui/icons/batch_checkbox_off.png"
            button:
                xalign 0.0
                action SetDict(_afs_building, "autofill_allow_unassign", not _afs_trim)
                hbox:
                    spacing 8
                    fixed:
                        xsize 32
                        ysize 32
                        add Transform(_afs_checkbox_asset, xysize=(26, 26)) xalign 0.5 yalign 0.5
                    text "Allow unassign lower skill workers" size font_size(22) color gui.journal_text_color yalign 0.5
            null height 6
            viewport:
                scrollbars None
                mousewheel True
                draggable True
                xsize 520
                ysize 260
                xalign 0.5
                vbox:
                    spacing 8
                    xfill True
                    for _afs_pid, _afs_pname, _afs_cap, _afs_holders in _afs_profs:
                        $ _afs_q = get_autofill_quota(building_name, _afs_pid)
                        $ _afs_val = "Max" if _afs_q is None else str(_afs_q)
                        # Fixed-width column cells so rows never drift with long names.
                        hbox:
                            spacing 0
                            fixed:
                                xsize 250
                                ysize 40
                                text "[_afs_pname!q]" size font_size(23) color gui.journal_text_color yalign 0.5
                            fixed:
                                xsize 64
                                ysize 40
                                text "[_afs_holders]/[_afs_cap]" size font_size(22) color gui.journal_text_color xalign 1.0 yalign 0.5
                            null width 18
                            textbutton "-":
                                xsize 44
                                ysize 40
                                yalign 0.5
                                text_size font_size(26)
                                text_xalign 0.5
                                text_color gui.journal_text_color
                                text_hover_color gui.journal_hover_color
                                action Function(adjust_autofill_quota, building_name, _afs_pid, -1, _afs_cap)
                            fixed:
                                xsize 70
                                ysize 40
                                text "[_afs_val]" size font_size(24) color (gui.journal_hover_color if _afs_q is not None else gui.journal_text_color) xalign 0.5 yalign 0.5
                            textbutton "+":
                                xsize 44
                                ysize 40
                                yalign 0.5
                                text_size font_size(26)
                                text_xalign 0.5
                                text_color gui.journal_text_color
                                text_hover_color gui.journal_hover_color
                                action Function(adjust_autofill_quota, building_name, _afs_pid, 1, _afs_cap)
                    if not _afs_profs:
                        text "This building has no configurable professions." size font_size(22) color gui.journal_text_color xalign 0.5
            null height 4
            textbutton "Reset all to Max":
                xalign 0.5
                text_size font_size(24)
                text_color gui.journal_text_color
                text_hover_color gui.journal_hover_color
                sensitive building_has_autofill_quotas(building_name)
                action Function(clear_autofill_quotas, building_name)
    key "K_BACKSPACE" action Hide("autofill_settings")

screen preset_picker():
    modal True
    zorder 121
    add Solid("#00000055")
    python:
        _pp_presets = getattr(store, "assignment_presets", {}) or {}
        _pp_names = sorted(_pp_presets.keys()) if hasattr(_pp_presets, "keys") else []
    # PARCHMENT_SAFE_AREA_CONTRACT: match Batch's inset content zone.
    frame:
        xalign 0.5
        yalign 0.5
        xsize 1040
        ysize 720
        background Transform(Crop((542, 107, 842, 857), "gui/Journalback.png"), xysize=(1040, 720), align=(0.5, 0.5))
        padding (140, 85, 140, 70)
        vbox:
            spacing 14
            xfill True

            # PRESET_TABLE_LAYOUT_CONTRACT: matching title/close header.
            fixed:
                xfill True
                ysize 58
                label "ASSIGNMENT PRESETS" xalign 0.5 yalign 0.5 style "header_style"
                imagebutton:
                    idle Transform("gui/button/return_idle.png", zoom=(0.60 if renpy.variant("touch") else 0.46))
                    hover Transform("gui/button/return_hover.png", zoom=(0.60 if renpy.variant("touch") else 0.46))
                    action Hide("preset_picker")
                    xalign 1.0
                    yalign 0.5

            frame:
                xfill True
                background "#4a2a1a12"
                padding (20, 14)
                text "Apply keeps current assignments. Replace clears them first. Missing workers, buildings, and full jobs are safely skipped." size font_size(22) color gui.journal_text_color xalign 0.5 text_align 0.5

            viewport:
                scrollbars None
                mousewheel True
                draggable True
                xsize 760
                ysize 350
                xalign 0.5
                vbox:
                    spacing 8
                    xfill True
                    if _pp_names:
                        for _pp_idx, _pp_name in enumerate(_pp_names):
                            python:
                                _pp_count = len(_pp_presets.get(_pp_name, []) or [])
                                _pp_count_label = "{} worker{}".format(_pp_count, "" if _pp_count == 1 else "s")
                                # Pre-escape for Confirm() messages (re-interpolated); !q handles the row label.
                                _pp_name_safe = str(_pp_name).replace("[", "[[").replace("{", "{{")
                            frame:
                                xfill True
                                ysize 56
                                background (gui.row_alt_color if _pp_idx % 2 else "#4a2a1a0d")
                                padding (8, 6)
                                hbox:
                                    spacing 10
                                    xalign 0.5
                                    fixed:
                                        xsize 260
                                        ysize 42
                                        text "[_pp_name!q]" size font_size(22) color gui.journal_text_color xalign 0.0 yalign 0.5
                                    text "[_pp_count_label]" size font_size(20) color gui.journal_text_color xsize 100 text_align 0.5 yalign 0.5
                                    textbutton "Apply":
                                        style "fm_panel_button"
                                        xsize 110
                                        ysize 42
                                        text_size font_size(20)
                                        action [Function(apply_assignment_preset, _pp_name, False), Hide("preset_picker")]
                                    textbutton "Replace":
                                        style "fm_panel_button"
                                        xsize 120
                                        ysize 42
                                        text_size font_size(20)
                                        action Confirm("Unassign everyone, then apply '" + _pp_name_safe + "'?", [Function(apply_assignment_preset, _pp_name, True), Hide("preset_picker")], NullAction())
                                    textbutton "Delete":
                                        style "fm_danger_button"
                                        xsize 110
                                        ysize 42
                                        text_size font_size(20)
                                        action Confirm("Delete preset '" + _pp_name_safe + "'?", Function(delete_assignment_preset, _pp_name), NullAction())
                    else:
                        vbox:
                            xsize 760
                            ysize 250
                            xalign 0.5
                            yalign 0.5
                            spacing 10
                            text "No presets saved yet." size font_size(26) color gui.journal_text_color xalign 0.5
                            text "Save a layout from Batch Management to reuse it here." size font_size(20) color gui.parchment_muted_color xalign 0.5 text_align 0.5
    key "K_BACKSPACE" action Hide("preset_picker")

screen batch_building_picker(worker_pool=None):
    modal True
    zorder 130
    add Solid("#00000055")
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 720
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (55, 45)
        vbox:
            spacing 12
            xfill True
            label "ASSIGN BUILDING" xalign 0.5 style "header_style"
            viewport:
                scrollbars None
                mousewheel True
                draggable True
                ysize 520
                vbox:
                    spacing 8
                    xfill True
                    for building_name in sorted(getattr(store, "owned_buildings", []) or []):
                        $ _batch_bdata = available_buildings.get(building_name, {})
                        $ _batch_bt = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == _batch_bdata.get("type")), None)
                        if _batch_bdata and is_standard_managed_building(building_name, _batch_bdata) and building_type_is_visible(_batch_bt):
                            $ _batch_label = building_type_display_name(_batch_bt, building_name) + ": " + store.custom_names.get(building_name, building_name.replace("_", " "))
                            textbutton "[_batch_label]":
                                xfill True
                                text_size font_size(25)
                                action [Function(batch_apply_building, building_name), Hide("batch_building_picker"), Show("batch_worker_manager", worker_pool=worker_pool)]

        # Return button inset onto the parchment, top-right (same as worker_history_popup)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("batch_building_picker")
            xalign 1.0
            yalign 0.0
            xoffset -48
            yoffset 50
    key "K_BACKSPACE" action Hide("batch_building_picker")

screen batch_job_picker(building_name, worker_pool=None):
    modal True
    zorder 130
    add Solid("#00000055")
    python:
        _batch_job_building = available_buildings.get(building_name, {})
        _batch_job_btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == _batch_job_building.get("type")), None)
        _batch_jobs = [entry for entry in (_batch_job_btype.get("professions", []) if _batch_job_btype else []) if profession_is_visible(entry, _batch_job_btype) and profession_is_unlocked(entry)]
    frame:
        xalign 0.5
        yalign 0.5
        xsize 720
        ysize 720
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (55, 45)
        vbox:
            spacing 12
            xfill True
            label "ASSIGN JOB" xalign 0.5 style "header_style"
            viewport:
                scrollbars None
                mousewheel True
                draggable True
                ysize 520
                vbox:
                    spacing 8
                    xfill True
                    textbutton "Rest":
                        xfill True
                        text_size font_size(25)
                        action [Function(batch_apply_job, building_name, "rest"), Hide("batch_job_picker"), Show("batch_worker_manager", worker_pool=worker_pool)]
                    for profession in _batch_jobs:
                        textbutton "[profession.get('name', profession.get('id', 'Job'))]":
                            xfill True
                            text_size font_size(25)
                            action [Function(batch_apply_job, building_name, profession.get("id")), Hide("batch_job_picker"), Show("batch_worker_manager", worker_pool=worker_pool)]

        # Return button inset onto the parchment, top-right (same as worker_history_popup)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            hover Transform("gui/button/return_hover.png", zoom=(0.65 if renpy.variant("touch") else 0.5))
            action Hide("batch_job_picker")
            xalign 1.0
            yalign 0.0
            xoffset -48
            yoffset 50
    key "K_BACKSPACE" action Hide("batch_job_picker")

screen auto_advance_summary(summary):
    modal True
    zorder 140
    add Solid("#00000066")
    $ _advance_stop_reason = str(summary.get("stop_reason") or "Requested span completed")
    frame:
        xalign 0.5
        yalign 0.5
        xsize 760
        ysize 650
        background Transform("gui/Journalback.png", align=(0.5, 0.5))
        padding (65, 50)
        vbox:
            spacing 14
            xfill True
            label "ADVANCE SUMMARY" xalign 0.5 style "header_style"
            text "Days processed: [summary.get('days_processed', 0)] / [summary.get('requested_days', 0)]" size font_size(27) color gui.journal_text_color xalign 0.5
            text "Money: $[summary.get('start_money', 0)] to $[summary.get('end_money', 0)]" size font_size(25) color gui.journal_text_color xalign 0.5
            text "Gross earnings: $[summary.get('earnings', 0)]" size font_size(24) color gui.success_color xalign 0.5
            text "Operating costs: $[summary.get('costs', 0)]" size font_size(24) color gui.danger_color xalign 0.5
            text "Notable results: [summary.get('critical_events', 0)]" size font_size(24) color gui.journal_text_color xalign 0.5
            null height 6
            text "Stopped: [_advance_stop_reason]" size font_size(24) color gui.journal_hover_color xalign 0.5 text_align 0.5
            hbox:
                spacing 18
                xalign 0.5
                textbutton "View All Reports":
                    xsize 280
                    ysize 58
                    text_size font_size(26)
                    text_xalign 0.5
                    text_yalign 0.5
                    sensitive bool(getattr(store, "auto_advance_day_reports", None))
                    action [
                        Hide("auto_advance_summary"),
                        Show(
                            "daily_report",
                            report_data=get_auto_advance_reports(),
                            report_title=get_auto_advance_report_title(summary.get("days_processed", 0)),
                            return_action=[Hide("daily_report"), Show("auto_advance_summary", summary=summary)],
                            report_costs=get_auto_advance_report_costs(),
                        ),
                    ]
                textbutton "Continue":
                    xsize 280
                    ysize 58
                    text_size font_size(26)
                    text_xalign 0.5
                    text_yalign 0.5
                    action Return()
    key "K_BACKSPACE" action Return()

label auto_advance_days:
    hide screen tavern
    $ take_a_walk_in_progress = False
    $ initialize_auto_advance_summary(auto_advance_requested_days)
    $ auto_advance_pending_result = None
    jump auto_advance_next_day

label auto_advance_next_day:
    $ _auto_requested = max(1, int(auto_advance_requested_days or 1))
    $ _auto_processed = int(store.auto_advance_summary.get("days_processed", 0) or 0)
    if _auto_processed >= _auto_requested:
        $ store.auto_advance_summary["stop_reason"] = "Requested span completed"
        jump auto_advance_show_summary

    $ store.manager_interactions_today = 0
    $ renpy.log("SMART_ADVANCE: processing day %s of %s" % (_auto_processed + 1, _auto_requested))
    $ _auto_start_total_days = calculate_total_days()
    $ auto_advance_pending_result = process_next_day()
    $ renpy.log("SMART_ADVANCE: day result=%s event=%s" % (auto_advance_pending_result, (store.current_event or {}).get("id", "none")))
    if auto_advance_day_was_processed(_auto_start_total_days, calculate_total_days()):
        $ update_auto_advance_summary()
        $ capture_auto_advance_day()

    if auto_advance_pending_result == "game_over":
        $ store.auto_advance_summary["stop_reason"] = "Bankruptcy threshold reached"
        jump auto_advance_show_summary
    elif auto_advance_pending_result == "handle_random_event":
        if store.current_event:
            jump auto_advance_handle_random_event
        $ renpy.log("SMART_ADVANCE: event result had no current_event; continuing completed span")
        $ auto_advance_pending_result = None
    elif auto_advance_pending_result == "governor_retaliation":
        jump auto_advance_handle_governor_retaliation
    elif auto_advance_pending_result == "governor_tension_event":
        jump auto_advance_handle_governor_tension
    elif not auto_advance_day_completed_without_event(auto_advance_pending_result):
        $ store.auto_advance_summary["stop_reason"] = "Simulation stopped"
        jump auto_advance_show_summary

    $ run_start_of_day_automation("smart_advance")
    jump auto_advance_next_day

label auto_advance_handle_random_event:
    $ renpy.log("SMART_ADVANCE: presenting random event %s" % ((store.current_event or {}).get("id", "unknown")))
    scene expression Solid('#000000')
    call handle_random_event from _call_auto_advance_handle_random_event
    $ renpy.log("SMART_ADVANCE: random event completed; resuming remaining days")
    jump auto_advance_after_event

label auto_advance_handle_governor_retaliation:
    call governor_retaliation from _call_auto_advance_governor_retaliation
    jump auto_advance_after_event

label auto_advance_handle_governor_tension:
    call governor_tension_event from _call_auto_advance_governor_tension
    jump auto_advance_after_event

label auto_advance_after_event:
    $ auto_advance_pending_result = None
    $ _auto_bankruptcy_threshold = getattr(store, "BANKRUPTCY_MONEY_THRESHOLD", -5000)
    if store.money <= _auto_bankruptcy_threshold:
        $ auto_advance_pending_result = "game_over"
        $ store.auto_advance_summary["stop_reason"] = "Bankruptcy threshold reached"
        jump auto_advance_show_summary
    $ run_start_of_day_automation("smart_advance/after_event")
    jump auto_advance_next_day

label auto_advance_show_summary:
    $ store.auto_advance_summary["end_money"] = int(getattr(store, "money", 0) or 0)
    show screen tavern
    call screen auto_advance_summary(summary=store.auto_advance_summary)
    hide screen tavern
    if auto_advance_pending_result == "game_over":
        jump game_over
    jump tavern_screen
