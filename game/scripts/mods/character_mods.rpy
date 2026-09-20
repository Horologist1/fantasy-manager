# Installation is device-local. It must never be rolled back with a save.
init -50 python hide:
    import fm_mods.runtime
    fm_mods.runtime.bootstrap(renpy)

init python:
    import fm_mods.runtime as _fm_mods_runtime

    def fm_mod_browse(path=None):
        if not getattr(store, "main_menu", False) or _fm_mods_runtime.state()["busy"] or renpy.ios or renpy.emscripten:
            return
        if renpy.android:
            _fm_mods_runtime.start_android_picker(renpy)
            return
        renpy.show_screen("character_mod_browser", listing=_fm_mods_runtime.browse(path or _fm_mods_runtime.default_folder()))

    def fm_mod_preview(path):
        if not getattr(store, "main_menu", False) or renpy.android or renpy.ios or renpy.emscripten:
            return
        renpy.hide_screen("character_mod_browser")
        _fm_mods_runtime.start_preview(renpy, path)

    def fm_mod_install(rename_conflicts=False):
        if not getattr(store, "main_menu", False) or renpy.ios or renpy.emscripten:
            return
        _fm_mods_runtime.start_install(renpy, rename_conflicts)

    def fm_mod_override_request():
        if not getattr(store, "main_menu", False) or _fm_mods_runtime.state()["busy"] or renpy.ios or renpy.emscripten:
            return
        if _fm_mods_runtime.state()["override_mode"]:
            _fm_mods_runtime.set_override_mode(False)
        else:
            renpy.show_screen("character_mod_override_warning")

    def fm_mod_override_accept():
        if not getattr(store, "main_menu", False) or _fm_mods_runtime.state()["busy"] or renpy.ios or renpy.emscripten:
            return
        _fm_mods_runtime.set_override_mode(True)
        renpy.hide_screen("character_mod_override_warning")

    def fm_mod_request_uninstall(pack_id):
        if not getattr(store, "main_menu", False) or _fm_mods_runtime.state()["busy"]:
            return
        _fm_mods_runtime.refresh()
        pack = next((p for p in _fm_mods_runtime.state()["installed"] if p["id"] == pack_id), None)
        if pack and not pack["pending_uninstall"]:
            renpy.show_screen("character_mod_uninstall_confirm", pack=pack)

    def fm_mod_uninstall(pack_id, cancel=False):
        if not getattr(store, "main_menu", False) or _fm_mods_runtime.state()["busy"]:
            return
        renpy.hide_screen("character_mod_uninstall_confirm")
        _fm_mods_runtime.start_uninstall(renpy, pack_id, cancel=cancel)

screen mods_menu():
    tag menu
    add "gui/main_menu.png"
    add Solid("#24170d66")
    frame:
        align (0.5, 0.5)
        xsize 980
        padding (44, 36)
        background Solid("#eee2cb")
        vbox:
            spacing 22
            text _("Mods") size font_size(40) color gui.journal_dark_color
            textbutton _("Create Mods"):
                id "mods_create"
                xfill True
                yminimum 64
                padding (18, 10)
                background Solid("#e1cba9")
                hover_background Solid("#d7bd93")
                text_size font_size(30)
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                action OpenURL("https://horologist1.github.io/fantasy-manager/devkit/")
            textbutton _("Install mods"):
                id "mods_install"
                xfill True
                yminimum 64
                padding (18, 10)
                background Solid("#e1cba9")
                hover_background Solid("#d7bd93")
                text_size font_size(30)
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                action ShowMenu("character_mods")
            text _("Tip: You can download mods from our Discord or in F95, links are in itch.io"):
                size font_size(22)
                color "#79634f"
                xmaximum 892
            textbutton _("Back"):
                id "mods_back"
                yminimum 60
                text_size font_size(26)
                text_color gui.journal_dark_color
                text_hover_color gui.journal_hover_color
                action Return()
    key "game_menu" action Return()

screen character_mods():
    tag menu
    predict False
    on "show" action Function(_fm_mods_runtime.refresh)
    on "hide" action Function(_fm_mods_runtime.discard_preview)
    $ _mod_state = _fm_mods_runtime.state()
    add Solid("#242720")
    frame:
        align (0.5, 0.5)
        xsize 1400
        ysize 930
        padding (48, 36)
        background Solid("#eee2cb")
        vbox:
            spacing 20
            text _("Install mods") size font_size(36) color gui.journal_dark_color
            viewport:
                id "mod_content_viewport"
                ysize 680
                mousewheel True
                draggable True
                scrollbars "vertical"
                vbox:
                    spacing 20
                    if renpy.android:
                        text "Choose a mod ZIP from Downloads or another document provider. The game copies it to its own storage. Normal imports add characters and images; restart to activate installed packs." size font_size(24) color gui.journal_text_color xmaximum 1240
                    else:
                        text "Import a ZIP or an unpacked folder. Normal imports add characters and images. Packs are kept separately from the game and become available after restarting." size font_size(24) color gui.journal_text_color xmaximum 1240
                    if renpy.ios or renpy.emscripten:
                        text "File import is currently available on desktop." size font_size(24) color gui.journal_text_color
                    elif main_menu:
                        button:
                            id "mod_override_toggle"
                            background None
                            sensitive not _mod_state["busy"]
                            action Function(fm_mod_override_request)
                            hbox:
                                spacing 12
                                add Transform("gui/icons/batch_checkbox_on.png" if _mod_state["override_mode"] else "gui/icons/batch_checkbox_off.png", xysize=(26, 26)) yalign 0.5
                                text "Import as JSON override (experimental)" size font_size(26) color gui.journal_text_color
                        if _mod_state["override_mode"]:
                            text "For this import: replace whole existing JSON files by their exact data/... path. Installed overrides stay active until uninstalled. Start a new game after restarting." size font_size(22) color gui.journal_text_color xmaximum 1240
                        textbutton ("Choose ZIP" if renpy.android else "Choose ZIP or folder"):
                            id "mod_choose_source"
                            text_size font_size(28)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            sensitive not _mod_state["busy"]
                            action Function(fm_mod_browse)
                    if not main_menu:
                        text "Save your game and return to the main menu to install or uninstall packs." size font_size(24) color gui.journal_text_color
                    $ _mod_message = _mod_state["message"]
                    text "[_mod_message!q]" size font_size(24) color gui.journal_text_color
                    if _mod_state["preview"]:
                        $ preview = _mod_state["preview"]
                        text "[preview['title']!q]" size font_size(28) color gui.journal_dark_color
                        if preview.get("mode") == "override":
                            text "JSON override / [preview['mb']] MB" size font_size(24) color gui.journal_text_color
                            for path in preview["files"]:
                                text "[path!q]" size font_size(22) color gui.journal_text_color xmaximum 1240
                        else:
                            text "[preview['workers']] characters / [preview['images']] images / [preview['mb']] MB" size font_size(24) color gui.journal_text_color
                            text "[preview['names']!q]" size font_size(22) color gui.journal_text_color xmaximum 1240
                            text "Characters use the normal market/recruitment rules and your content filters. Custom recruitment scenes are excluded." size font_size(22) color gui.journal_text_color xmaximum 1240
                        for warning in preview["warnings"]:
                            text "[warning!q]" size font_size(22) color gui.journal_text_color xmaximum 1240
                        textbutton ("Install JSON override" if preview.get("mode") == "override" else "Install and keep both versions of overlapping names" if preview["conflicts"] else "Install this pack"):
                            id "mod_install_pack"
                            text_size font_size(28)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            sensitive main_menu and not _mod_state["busy"]
                            action Function(fm_mod_install, bool(preview["conflicts"]))
                    text "Installed packs" size font_size(28) color gui.journal_dark_color
                    if not _mod_state["installed"]:
                        text "No packs installed." size font_size(24) color gui.journal_text_color
                    for pack in _mod_state["installed"]:
                        if pack.get("mode") == "override":
                            text "[pack['title']!q] - JSON override (priority [pack['load_order']])" size font_size(24) color gui.journal_text_color xmaximum 1240
                        else:
                            text "[pack['title']!q] - [pack['workers']] characters" size font_size(24) color gui.journal_text_color xmaximum 1240
                        text ("Uninstall scheduled: restart required" if pack["pending_uninstall"] else "Active" if pack["active"] else "Restart required" if pack["restart_required"] else "Unavailable: installation is incomplete or invalid") size font_size(22) color gui.journal_text_color
                        textbutton ("Cancel uninstall" if pack["pending_uninstall"] else "Uninstall"):
                            id ("mod_uninstall_" + pack["id"])
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            sensitive main_menu and not _mod_state["busy"]
                            action (Function(fm_mod_uninstall, pack["id"], True) if pack["pending_uninstall"] else Function(fm_mod_request_uninstall, pack["id"]))
            textbutton "Back":
                id "mod_install_back"
                text_size font_size(28)
                text_color gui.journal_text_color
                text_hover_color gui.journal_hover_color
                sensitive not _mod_state["busy"]
                action ShowMenu("mods_menu")
    if _mod_state["busy"]:
        timer 0.4 repeat True action [Function(_fm_mods_runtime.poll_android_picker, renpy), Function(renpy.restart_interaction)]
        key "game_menu" action NullAction()
    else:
        key "game_menu" action ShowMenu("mods_menu")

screen character_mod_override_warning():
    modal True
    predict False
    zorder 220
    add Solid("#0009")
    frame:
        align (0.5, 0.5)
        xsize 1100
        padding (40, 32)
        background Solid("#eee2cb")
        vbox:
            spacing 22
            text "Import a JSON override?" size font_size(32) color gui.journal_dark_color
            text "For this import, replace complete JSON files, including every entry inside them. Individual fields are not merged. Images and scripts are excluded." size font_size(24) color gui.journal_text_color xmaximum 1020
            text "Experimental: install your packs, restart, then begin a new game. Changing or removing packs during a playthrough may cause errors. Older saves are not adapted." size font_size(24) color gui.journal_text_color xmaximum 1020
            text "Only use packs you trust. JSON structure is checked, but valid JSON can still contain incompatible gameplay changes. Later installed overrides take priority for the same file." size font_size(24) color gui.journal_text_color xmaximum 1020
            hbox:
                spacing 48
                textbutton "Enable override":
                    id "mod_override_accept"
                    action Function(fm_mod_override_accept)
                    text_size font_size(26)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                textbutton "Cancel":
                    id "mod_override_cancel"
                    action Hide("character_mod_override_warning")
                    text_size font_size(26)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
    key "game_menu" action Hide("character_mod_override_warning")

screen character_mod_uninstall_confirm(pack):
    modal True
    predict False
    zorder 220
    add Solid("#0009")
    frame:
        align (0.5, 0.5)
        xsize 1100
        padding (40, 32)
        background Solid("#eee2cb")
        vbox:
            spacing 22
            text "Uninstall pack?" size font_size(32) color gui.journal_dark_color
            text "[pack['title']!q]" size font_size(26) color gui.journal_dark_color xmaximum 1020
            text "The pack will be removed when you close and reopen the game. You can cancel before restarting." size font_size(24) color gui.journal_text_color xmaximum 1020
            if pack.get("mode") == "override":
                text "The original files or earlier overrides will be used again. Start a new game afterwards: existing saves are not adapted. Your original ZIP or folder is kept." size font_size(24) color gui.journal_text_color xmaximum 1020
            else:
                text "Saved characters and progress are kept, but this pack's images will no longer be available. Your original ZIP or folder is kept." size font_size(24) color gui.journal_text_color xmaximum 1020
            hbox:
                spacing 48
                textbutton "Uninstall":
                    id "mod_uninstall_confirm"
                    action Function(fm_mod_uninstall, pack["id"])
                    text_size font_size(26)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
                textbutton "Cancel":
                    id "mod_uninstall_cancel"
                    action Hide("character_mod_uninstall_confirm")
                    text_size font_size(26)
                    text_color gui.journal_text_color
                    text_hover_color gui.journal_hover_color
    key "game_menu" action Hide("character_mod_uninstall_confirm")

screen character_mod_browser(listing):
    modal True
    predict False
    zorder 210
    default typed_path = ""
    add Solid("#0009")
    frame:
        align (0.5, 0.5)
        xsize 1280
        ysize 950
        padding (40, 30)
        background Solid("#eee2cb")
        vbox:
            spacing 16
            text "Choose a mod pack" size font_size(32) color gui.journal_dark_color
            viewport:
                ysize 76
                mousewheel True
                draggable True
                text "[listing['path']!q]" size font_size(22) color gui.journal_text_color xmaximum 1180
            hbox:
                spacing 24
                textbutton "Parent folder" action Function(fm_mod_browse, listing["parent"]) text_size font_size(24) text_color gui.journal_text_color text_hover_color gui.journal_hover_color
                textbutton "Downloads" action Function(fm_mod_browse) text_size font_size(24) text_color gui.journal_text_color text_hover_color gui.journal_hover_color
                textbutton "Use this folder" action Function(fm_mod_preview, listing["path"]) text_size font_size(24) text_color gui.journal_text_color text_hover_color gui.journal_hover_color
            viewport:
                ysize (350 if persistent.large_font_mode else 440)
                mousewheel True
                draggable True
                scrollbars "vertical"
                vbox:
                    spacing 5
                    if listing["error"]:
                        text "[listing['error']!q]" size font_size(22) color gui.journal_text_color
                    for row in listing["rows"]:
                        $ _mod_filename = ("Folder: " if row["directory"] else "ZIP: ") + row["name"]
                        textbutton "[_mod_filename!q]":
                            xfill True
                            text_size font_size(24)
                            text_color gui.journal_text_color
                            text_hover_color gui.journal_hover_color
                            action (Function(fm_mod_browse, row["path"]) if row["directory"] else Function(fm_mod_preview, row["path"]))
            text "Or paste a ZIP/folder path:" size font_size(22) color gui.journal_text_color
            viewport:
                xsize 1180
                ysize 48
                xinitial 1.0
                input value ScreenVariableInputValue("typed_path") length 1024 color gui.journal_dark_color size font_size(24)
            hbox:
                spacing 40
                textbutton "Inspect path" action Function(fm_mod_preview, typed_path.strip().strip('"')) sensitive bool(typed_path.strip()) text_size font_size(24) text_color gui.journal_text_color text_hover_color gui.journal_hover_color
                textbutton "Cancel" action Hide("character_mod_browser") text_size font_size(24) text_color gui.journal_text_color text_hover_color gui.journal_hover_color
    key "game_menu" action Hide("character_mod_browser")
