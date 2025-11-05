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


################################################################################
## Styles
################################################################################

style default:
    properties gui.text_properties()
    language gui.language

# Estilos requeridos (agregar en tu archivo de estilos)
style table_button_text:
    color "#ffffff"
    hover_color "#ffd700"  # Dorado para hover
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

# Custom styles for comfort adjustment and other UI elements
style header_style:
    color "#ffddaa"
    size 28
    xalign 0.5
    bold True

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


## Make the namebox available for styling through the Character object.
init python:
    config.character_id_prefixes.append('namebox')

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

screen quick_menu:
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

style quick_button_text:
    properties gui.text_properties("quick_button")


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

            textbutton _("Start") action Start()

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
            textbutton _("Quit") action Quit(confirm=not main_menu)


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
    imagebutton auto "gui/main_menu/buttons/start_%s.png" xpos 761 ypos 345 focus_mask True action Start()
    imagebutton auto "gui/main_menu/buttons/load_%s.png" xalign 0.5 ypos 456 focus_mask True action ShowMenu("load")
    imagebutton auto "gui/main_menu/buttons/options_%s.png" xalign 0.5 ypos 516 focus_mask True action ShowMenu("preferences")
    imagebutton auto "gui/main_menu/buttons/gallery_%s.png" xalign 0.5 ypos 569 focus_mask True action ShowMenu("gallery")
    imagebutton auto "gui/main_menu/buttons/about_%s.png" xalign 0.5 ypos 622 focus_mask True action ShowMenu("about")
    imagebutton auto "gui/main_menu/buttons/help_%s.png" xalign 0.5 ypos 675 focus_mask True action ShowMenu("help")
    imagebutton auto "gui/main_menu/buttons/quit_%s.png" xalign 0.5 ypos 728 focus_mask True action Quit(confirm=False)

    if gui.show_name:

        vbox:
            style "main_menu_vbox"

            text "[config.name!t]":
                style "main_menu_title"

            text "0.62":
                style "main_menu_version"


style main_menu_frame is empty
style main_menu_vbox is vbox
style main_menu_text is gui_text
style main_menu_title is main_menu_text
style main_menu_version is main_menu_text

style main_menu_frame:
    xsize 420
    yfill True

    background "gui/overlay/main_menu.png"

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

    ## Fondo con gallery.png
    add "gui/gallery.png"

    ## Botón de return (ajustado 115px abajo y 140px a la izquierda)
    imagebutton:
        idle "gui/button/return_idle.png"
        hover "gui/button/return_hover.png"
        action Return()
        xalign 1.0
        yalign 0.0
        xoffset -135
        yoffset 140

    ## Contenido alineado arriba a la izquierda
    vbox:
        xpos 160
        ypos 210
        spacing 20

        ## Título del juego
        text "Fantasy Manager":
            style "about_title"
            xalign 0.0

        ## Versión
        text "Version 0.62":
            style "about_version"
            xalign 0.0

        ## Información del juego
        text "A fantasy management game where you build your empire. NSFW content is optional and can be enabled or disabled from this menu.":
            style "about_description"
            xalign 0.0

        ## NSFW toggle before Credits
        textbutton ("NSFW: Enabled" if persistent.nsfw_enabled else "NSFW: Disabled"):
            text_color "#3c1f14"
            text_hover_color "#6b6528"
            background None
            hover_background None
            action ToggleField(persistent, "nsfw_enabled")

        ## Espacio antes de Credits
        null height 20

        ## Créditos
        text "Credits:":
            style "about_section_header"
            xalign 0.0
        text "Game development, AI + Digital illustration - Horologist":
            style "about_section_text"
            xalign 0.0
        text "AI + Digital illustration - Annekka":
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

        ## Créditos con versión de Ren'Py
        text "Made with Ren'Py [renpy.version_only]":
            style "about_credits"
            xalign 0.0




## Estilos personalizados para la pantalla About
style about_title:
    size 48
    color "#3c1f14"
    xalign 0.5

style about_version:
    size 32
    color "#6b6528"
    xalign 0.5

style about_description:
    size 24
    color "#3c1f14"
    xalign 0.5

style about_credits:
    size 20
    color "#6b6528"
    xalign 0.5

style about_section_header:
    size 22
    color "#3c1f14"
    xalign 0.5
    underline True

style about_section_text:
    size 20
    color "#3c1f14"
    xalign 0.5

style about_instruction:
    size 28
    color "#314311"
    xalign 0.5


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

        ## Save slots
        # File save slot (replaces slot 1)
        hotspot (468, 312, 393, 207) action Show("file_save_dialog"):
            frame:
                background "#d4a574"  # Color del frame de save al hacer hover
                hover_background "#d4a574"
                xsize 393
                ysize 207
                vbox:
                    spacing 10
                    xalign 0.5
                    yalign 0.5
                    textbutton "Save to File":
                        text_size 26
                        text_color "#5d4037"
                        text_hover_color "#314311"
                        background None
                        hover_background None
                        xalign 0.5
                        action Show("file_save_dialog")
                    textbutton "Export game to external file":
                        text_size 18
                        text_color "#5d4037"
                        text_hover_color "#314311"
                        background None
                        hover_background None
                        xalign 0.5
                        action Show("file_save_dialog")
        hotspot (468, 620, 393, 207) action [Function(snapshot_pre_save, 2), FileAction(2)]:
            use load_save_slot(number=2)
        hotspot (1055, 312, 393, 207) action [Function(snapshot_pre_save, 3), FileAction(3)]:
            use load_save_slot(number=3)
        hotspot (1055, 620, 393, 207) action [Function(snapshot_pre_save, 4), FileAction(4)]:
            use load_save_slot(number=4)

        ## Navigation buttons
        hotspot (85, 263, 233, 90) action ShowMenu('history')
        hotspot (1584, 245, 239, 91) action ShowMenu('about')
        hotspot (1584, 411, 242, 98) action ShowMenu('help')

        hotspot (75, 613, 246, 88) action ShowMenu('preferences')
        hotspot (75, 483, 257, 91) action ShowMenu('load')
        hotspot (82, 366, 265, 90) action ShowMenu('save')
        hotspot (1584, 537, 254, 91) action MainMenu()
        hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

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

        ## Load slots
        # File load slot (replaces slot 1)
        hotspot (468, 312, 393, 207) action Show("file_load_dialog"):
            frame:
                background "#d4a574"  # Color del frame de save al hacer hover
                hover_background "#d4a574"
                xsize 393
                ysize 207
                vbox:
                    spacing 10
                    xalign 0.5
                    yalign 0.5
                    textbutton "Load from File":
                        text_size 26
                        text_color "#5d4037"
                        text_hover_color "#314311"
                        background None
                        hover_background None
                        xalign 0.5
                        action Show("file_load_dialog")
                    textbutton "Import game from external file":
                        text_size 18
                        text_color "#5d4037"
                        text_hover_color "#314311"
                        background None
                        hover_background None
                        xalign 0.5
                        action Show("file_load_dialog")
        hotspot (468, 620, 393, 207) action [Function(snapshot_mark_load, 2), FileAction(2)]:
            use load_save_slot(number=2)
        hotspot (1055, 312, 393, 207) action [Function(snapshot_mark_load, 3), FileAction(3)]:
            use load_save_slot(number=3)
        hotspot (1055, 620, 393, 207) action [Function(snapshot_mark_load, 4), FileAction(4)]:
            use load_save_slot(number=4)

        ## Navigation buttons
        hotspot (85, 263, 233, 90) action ShowMenu('history')
        hotspot (1584, 245, 239, 91) action ShowMenu('about')
        hotspot (1584, 411, 242, 98) action ShowMenu('help')

        hotspot (75, 613, 246, 88) action ShowMenu('preferences')
        hotspot (75, 483, 257, 91) action ShowMenu('load')
        hotspot (82, 366, 265, 90) action ShowMenu('save')
        hotspot (1584, 537, 254, 91) action MainMenu()
        hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

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
                        action FileAction(slot)

                        has vbox

                        add FileScreenshot(slot) xalign 0.5

                        text FileTime(slot, format=_("{#file_time}%A, %B %d %Y, %H:%M"), empty=_("empty slot")):
                            style "slot_time_text"

                        text FileSaveName(slot):
                            style "slot_name_text"

                        key "save_delete" action FileDelete(slot)

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
        hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

        hotspot (1448, 183, 64, 65) action Return()

        hotbar (1053, 291, 372, 37) value Preference('text speed')
        hotbar (1053, 466, 372, 37) value Preference('music volume')
        hotbar (1053, 640, 372, 37) value Preference('sound volume')
        hotbar (1053, 728, 372, 37) value Preference('voice volume')
        hotbar (1053, 816, 372, 37) value Preference('auto-forward time')

    ## NSFW toggle removed from Preferences (moved to About screen)


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
    color "#3c1f14"

style pref_vbox:
    xsize 338

style radio_vbox:
    spacing gui.pref_button_spacing

style radio_button:
    properties gui.button_properties("radio_button")
    foreground "gui/button/radio_[prefix_]foreground.png"

style radio_button_text:
    properties gui.text_properties("radio_button")
    color "#3c1f14"

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
        hotspot (1601, 698, 229, 96) action [SetVariable("pending_exit", True), Quit()]

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
                text_size 26
                text_color "#7a4b2a"
                text_hover_color "#6b6528"
                background None
                hover_background None
            textbutton _("Mouse") action SetScreenVariable("device", "mouse"):
                text_size 26
                text_color "#7a4b2a"
                text_hover_color "#6b6528"
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
                        size 19
        vbox:
            spacing 8
            xoffset -110
            for k, d in entries[mid:]:
                hbox:
                    spacing 24
                    label k
                    text d:
                        size 19


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
                        size 19
        vbox:
            spacing 8
            xoffset -110
            for k, d in entries[mid:]:
                hbox:
                    spacing 24
                    label k
                    text d:
                        size 19


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
    size 42  # Aumentado 50% desde 28
    color "#3c1f14"  # Marrón oscuro como los menús laterales
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
    color "#ffffff"  # Texto blanco para mejor legibilidad


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
## Mobile Variants
################################################################################

style pref_vbox:
    variant "medium"
    xsize 675

## Since a mouse may not be present, we replace the quick menu with a version
## that uses fewer and bigger buttons that are easier to touch.
screen quick_menu():
    variant "touch"

    zorder 100

    if quick_menu:

        hbox:
            style_prefix "quick"

            xalign 0.5
            yalign 1.0

            textbutton _("Back") action Rollback()
            textbutton _("Skip") action Skip() alternate Skip(fast=True, confirm=True)
            textbutton _("Auto") action Preference("auto-forward", "toggle")
            textbutton _("Menu") action ShowMenu()


style window:
    variant "small"
    background "gui/phone/textbox.png"

style radio_button:
    variant "small"
    foreground "gui/phone/button/radio_[prefix_]foreground.png"

style check_button:
    variant "small"
    foreground "gui/phone/button/check_[prefix_]foreground.png"

style nvl_window:
    variant "small"
    background "gui/phone/nvl.png"

style main_menu_frame:
    variant "small"
    background "gui/phone/overlay/main_menu.png"

style game_menu_outer_frame:
    variant "small"
    background "gui/phone/overlay/game_menu.png"

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
    left_bar Frame("gui/phone/bar/left.png", gui.bar_borders, tile=gui.bar_tile)
    right_bar Frame("gui/phone/bar/right.png", gui.bar_borders, tile=gui.bar_tile)

style vbar:
    variant "small"
    xsize gui.bar_size
    top_bar Frame("gui/phone/bar/top.png", gui.vbar_borders, tile=gui.bar_tile)
    bottom_bar Frame("gui/phone/bar/bottom.png", gui.vbar_borders, tile=gui.bar_tile)

style scrollbar:
    variant "small"
    ysize gui.scrollbar_size
    base_bar Frame("gui/phone/scrollbar/horizontal_[prefix_]bar.png", gui.scrollbar_borders, tile=gui.scrollbar_tile)
    thumb Frame("gui/phone/scrollbar/horizontal_[prefix_]thumb.png", gui.scrollbar_borders, tile=gui.scrollbar_tile)

style vscrollbar:
    variant "small"
    xsize gui.scrollbar_size
    base_bar Frame("gui/phone/scrollbar/vertical_[prefix_]bar.png", gui.vscrollbar_borders, tile=gui.scrollbar_tile)
    thumb Frame("gui/phone/scrollbar/vertical_[prefix_]thumb.png", gui.vscrollbar_borders, tile=gui.scrollbar_tile)

style slider:
    variant "small"
    ysize gui.slider_size
    base_bar Frame("gui/phone/slider/horizontal_[prefix_]bar.png", gui.slider_borders, tile=gui.slider_tile)
    thumb "gui/phone/slider/horizontal_[prefix_]thumb.png"

style vslider:
    variant "small"
    xsize gui.slider_size
    base_bar Frame("gui/phone/slider/vertical_[prefix_]bar.png", gui.vslider_borders, tile=gui.slider_tile)
    thumb "gui/phone/slider/vertical_[prefix_]thumb.png"

style slider_vbox:
    variant "small"
    xsize None

style slider_slider:
    variant "small"
    xsize 900

################################################################################
### SCREEN DEFINITIONS
################################################################################

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

screen random_event_choice(event_choices):
    modal True
    zorder 99
    
    default affected_building_info = ""
    
    on "show" action Function(get_affected_building_info)
    
    # Use the same style as standard Ren'Py choices (Lord/Lady format)
    style_prefix "choice"
    
    vbox:
        for choice in event_choices:
            textbutton choice["option"] action Return(choice)

# --- NEW SCREEN START ---
screen choose_event_worker_screen(eligible_workers):
    modal True
    zorder 100
    
    python:
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
    
    # Main frame in the middle for worker selection
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#1a1a1acc")
        padding (20, 20)
        maximum (800, 490)  # Reduced height by another 10% from 540 to 490
        vbox:
            spacing 15
            label (f"Choose a worker from {building_name}" if building_name else "Choose a worker for the event") xalign 0.5 style "header_style"
            null height 10
            if not eligible_workers:
                text "No eligible workers found for this event." color "#ff0000" xalign 0.5 text_align 0.5
                null height 20
                textbutton "Continue":
                    xalign 0.5
                    action Return(None)
            else:
                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    vbox:
                        spacing 10
                        for worker in eligible_workers:
                            hbox:
                                spacing 10
                                xfill True
                                
                                # Only display skill value if we found a condition skill
                                if condition_skill:
                                    $ skill_value = calculate_skill_with_traits(worker, condition_skill)
                                    $ skill_name = skill_names.get(condition_skill, "Skill")
                                    textbutton "[worker['name']] - [skill_name]: [skill_value]":
                                        xalign 0.0
                                        action Return(worker)
                                else:
                                    # Fallback if no condition skill found
                                    textbutton "[worker['name']]":
                                        xalign 0.0
                                        action Return(worker)

screen choose_worker_for_event(skill_name, threshold):
    python:
        # All Python logic in a single block to avoid linter errors
        skill_name = str(skill_name)  # Ensure skill_name is a string
        threshold = int(threshold)  # Ensure threshold is an integer
        eligible_workers = []
        
        # Find workers with the required skill level
        for worker in store.workers:
            # Check if worker has an assigned job and is available
            if worker.get("assigned_job") is not None:
                # If we have a specific affected building, only include workers from that building
                if hasattr(store, "current_affected_building") and store.current_affected_building:
                    if worker.get("assigned_building") != store.current_affected_building:
                        continue
                        
                worker_skill = calculate_skill_with_traits(worker, skill_name)
                
                # Log for debugging
                renpy.log(f"Worker: {worker['name']}, Skill: {skill_name}, Value: {worker_skill}, Threshold: {threshold}")
                
                # Only include workers whose skill meets or exceeds the threshold
                if worker_skill >= threshold:
                    eligible_workers.append(worker)
                    renpy.log(f"Added eligible worker: {worker['name']} with skill {worker_skill}")
        
        # Get building info for title
        building_name = ""
        if hasattr(store, "current_affected_building") and store.current_affected_building:
            bld_name = store.current_affected_building
            bld = available_buildings.get(bld_name, {})
            btype_id = bld.get("type")
            if btype_id:
                building_type = next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "")
                display_name = store.custom_names.get(bld_name, bld_name)
                building_name = f"{building_type}: {display_name}"
    
    modal True
    zorder 99
    # Removing the darkening background effect
    # add Solid("#000000dd")
    
    # Main selection frame in the middle
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#1a1a1acc")
        padding (20, 20)
        vbox:
            spacing 15
            label (f"Choose a Worker from {building_name}" if building_name else "Choose a Worker") xalign 0.5 style "header_style"
            
            # Display message if no workers are eligible
            if not eligible_workers:
                text "No eligible workers found. Make sure you have workers with [skill_name] assigned to the right building type." color "#ff0000" xalign 0.5 text_align 0.5
            else:
                # List all eligible workers
                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    ysize 400
                    xsize 500
                    vbox:
                        spacing 10
                        for worker in eligible_workers:
                            $ worker_skill = calculate_skill_with_traits(worker, skill_name)
                            textbutton "[worker['name']] ([skill_name]: [worker_skill])":
                                xalign 0.5
                                xsize 400
                                action Return(worker)
            
            # Close button
            textbutton "Close":
                xalign 0.5
                xsize 200
                action Return(None)

screen recruitment_event_screen(event, worker):
    modal True
    zorder 98
    

    
    add event_bg
    add Solid("#000000dd")
    
    $ comfort_level = worker.get("comfort_level", worker.get("comfort_desired", 1))
    $ daily_cost = worker.get("daily_cost", comfort_level * 10)
    
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
            text description size 24 xalign 0.5 color "#ffffff"
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
            textbutton choice["option"] action Return(choice)
        
        # Separator
        null height 20
        
        # Additional recruitment actions with normal choice style
        textbutton "*Examine Worker*" action [SetVariable("in_recruit_examine", True), Show("worker_details", worker=store.current_recruitment_worker, in_roster=False, from_recruitment=True)]

screen advanced_recruitment_event_screen(event, worker, description, dialogue, choices):
    modal True
    zorder 99
    

    
    # Background
    $ background_image = event.get("background_image", "event_bg")
    add background_image
    add Solid("#000000dd")
    
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#1a1a1acc")
        padding (30, 30)
        xsize 800
        
        vbox:
            xfill True
            spacing 20
            
            # Description
            text description size 24 xalign 0.5 color "#ffffff" text_align 0.5
            
            null height 10
            
            # Dialogue
            if dialogue:
                text dialogue size 22 xalign 0.5 color "#ffdd88" text_align 0.5 italic True
            
            null height 20
            
            # Choices
            vbox:
                spacing 15
                for choice in choices:
                    textbutton choice.get("option", "Choice"):
                        xsize 700
                        text_size 20
                        action Function(process_advanced_recruitment_choice, choice, event, worker)
            
            null height 20
            
            # Examine worker option
            hbox:
                spacing 20
                xalign 0.5
                textbutton "Examine Worker":
                    xsize 200
                    text_size 18
                    action Show("worker_details", worker=worker, in_roster=False, from_recruitment=True)
                textbutton "Cancel":
                    xsize 200
                    text_size 18
                    action Hide("advanced_recruitment_event_screen")

screen recruitment_result_screen(message, outcome, event):
    modal True
    zorder 100
    

    
    # Background based on outcome
    if outcome == "success":
        $ bg_image = event.get("success_image", "generic_success")
    else:
        $ bg_image = event.get("failure_image", "generic_failure")
    
    add bg_image
    add Solid("#000000dd")
    
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#1a1a1acc")
        padding (30, 30)
        xsize 700
        
        vbox:
            spacing 20
            
            # No title - just show what happened
            
            null height 10
            
            text message size 24 xalign 0.5 color "#ffffff" text_align 0.5 substitute False
            
            null height 30
            
            hbox:
                xfill True
                textbutton "Continue":
                    xalign 0.5
                    text_xalign 0.5
                    text_size 22
                    action Return(True)

screen Building_select_global():
    zorder 3
    modal True
    add Solid("#000000dd")
    
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
                        # List all owned buildings
                        for building in owned_buildings:
                            $ building_data = available_buildings[building]
                            $ btype_id = building_data.get("type")
                            $ type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                            $ parts = building.split('_')
                            $ default_name = f"Building {parts[1]}" if len(parts) > 1 else building
                            $ display_name = store.custom_names.get(building, default_name)
                            textbutton "[type_name]: [display_name]":
                                xsize 580  # Keep button width same
                                text_size 26  # Larger font like journal
                                text_color "#7a4b2a"  # Brown text like journal
                                text_hover_color "#6b6528"  # Unified dark green hover
                                action [Hide("tavern"), Hide("Building_select_global"), Show("Manager", building_name=building)]
        
        # Close button positioned like journal (outside vbox)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action [Hide("Building_select_global"), Show("tavern")]
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5
         
screen Building_select(worker):
    modal True
    zorder 99
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#000000ee")
        padding (20, 20)
        vbox:
            spacing 10
            label "Select Building" style "header_style" xalign 0.5
            $ bnames = sorted(available_buildings.keys())
            for building_name in bnames:
                if available_buildings[building_name]["owned"]:
                    textbutton "[custom_names[building_name]]":
                        action [
                            # Remove the worker from any current building.
                            Function(remove_worker_from_building, worker),
                            # Add the worker to this building's assigned workers list.
                            Function(available_buildings[building_name]["assigned_servants"].append, worker),
                            # Set the worker's assigned_building field.
                            SetDict(worker, "assigned_building", building_name),
                            Hide("Building_select"),
                            Show("workers")
                        ]
                else:
                    textbutton "[custom_names[building_name]] (Not Available)":
                        style "nav_button_text"
                        text_size 24
                        xalign 0.0
                        sensitive False
            textbutton "Close":
                style "nav_button_text"
                xalign 0.5
                action [Hide("Building_select"), Show("workers")]

screen job_selection(worker):
    zorder 99
    modal True
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
                    
                    # Universal Unassign option (available for all buildings)
                    if building is not None:
                        vbox:
                            spacing 2
                            textbutton "Unassign (No Role)":
                                xsize 500
                                text_size 28
                                text_color "#7a4b2a"
                                text_hover_color "#6b6528"
                                sensitive True
                                action [
                                    SetDict(building["servant_jobs"], worker["name"], "unassigned"),
                                    Hide("job_selection")
                                ]
                            text "{color=#000000}{size=18}No specific role assigned{/size}{/color}\n{size=16}{color=#7a4b2a}Worker will not participate in daily activities{/color}{/size}":
                                xsize 500
                                xalign 0.0
                                xoffset 5
                    
                    if building is not None and building.get("type") is not None:
                        $ btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == building["type"]), None)
                        if btype is not None:
                            # Filter professions based on NSFW toggle
                            for profession in [p for p in btype.get("professions", []) if persistent.nsfw_enabled or not p.get("nsfw", False)]:
                                $ prof_name = profession.get("name", "Unnamed Profession")
                                $ prof_description = profession.get("description", "No description available.")
                                $ skills_used = profession.get("skills", [])
                                $ required_skills = ", ".join([skill_names.get(str(s), str(s)) for s in skills_used]) if skills_used else "None"  # Check for empty skills
                                $ total = 0
                                $ count = 0
                                for s in skills_used:
                                    $ total += calculate_skill_with_traits(worker, str(s))
                                    $ count += 1
                                if count > 0:
                                    $ avg_skill = total // count
                                else:
                                    $ avg_skill = 0
                                $ current_count = len([w for w in building["assigned_servants"] if building["servant_jobs"].get(w["name"], "") == profession["id"]])
                                $ max_limit = profession.get("max_daily_workers", 99)
                                vbox:  # Wrap each profession entry in a vbox
                                    spacing 2  # Tight spacing between lines
                                    if current_count < max_limit:
                                        textbutton "[prof_name]":
                                            xsize 500  # Match shop_selection button width
                                            text_size 28
                                            text_color "#7a4b2a"
                                            text_hover_color "#6b6528"
                                            sensitive True
                                            action [
                                                Function(lambda w, b: b["assigned_servants"].append(w) if w not in b["assigned_servants"] else None, worker, building),
                                                SetDict(building["servant_jobs"], worker["name"], profession["id"]),
                                                Function(lambda: setattr(store, 'workers_assigned_count', store.workers_assigned_count + 1) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 3 else None),
                                                Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 3 else None),
                                                Hide("job_selection")
                                            ]
                                        text "{color=#5a3a1a}{size=18}Skills Used: [required_skills]{/size}{/color}\n{size=16}{color=#6b6528}Average Skill: [avg_skill]/100{/color}{/size}\n{size=16}{color=#7a4b2a}[prof_description]{/color}{/size}":
                                            xsize 500  # Match the textbutton width for alignment
                                            xalign 0.0  # Align left to match textbutton
                                            xoffset 5
                                    else:
                                        textbutton "[prof_name]":
                                            xsize 500  # Match shop_selection button width
                                            text_size 28
                                            text_color "#7a4b2a"
                                            text_hover_color "#6b6528"
                                            sensitive False
                                        text "{color=#5a3a1a}{size=18}Skills Used: [required_skills]{/size}{/color}\n{size=16}{color=#6b6528}Average Skill: [avg_skill]/100{/color}{/size}\n{size=16}{color=#ff0000}Role Full{/color}{/size}":
                                            xsize 500  # Match the textbutton width for alignment
                                            xalign 0.0  # Align left to match textbutton
                        else:
                            text "No building type data found" size 28 xalign 0.5
                    else:
                        text "No building assigned or building type not set" size 28 xalign 0.5
        
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action [Hide("job_selection"), Show("workers")]
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5


screen manager_inventory(shop_mode=None):
    default selected_manager_item = None
    default selected_worker_item = None
    default selected_description = ""
    default is_transferring = False  # Debounce flag

    python:
        def get_item_action_elements(item, item_info, worker):
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
                action = Function(lambda: toggle_equip_item(worker.get("inventory", []), item[0], worker=worker))
            # "currency" and "misc" fall through to "No Action" by default

            return (label, action, sensitive, bg)

        def transfer_to_right():
            smi = renpy.get_screen_variable("selected_manager_item")
            if smi is not None and (right_worker is not False) and not renpy.get_screen_variable("is_transferring"):
                renpy.set_screen_variable("is_transferring", True)
                renpy.set_screen_variable("selected_manager_item", None)
                source_inventory = manager_inventory if left_worker is None else left_worker.get("inventory", [])
                target_inventory = manager_inventory if right_worker is None else right_worker.get("inventory", [])
                renpy.log(f"Transfer to right: Left={left_worker['name'] if left_worker else 'Storage'}, Right={right_worker['name'] if right_worker else 'Storage'}, Source={source_inventory}, Target={target_inventory}, Item={smi}")
                if smi[2] and left_worker and left_worker is not False:
                    renpy.log(f"Unequipping {smi[0]} from left worker")
                    toggle_equip_item(source_inventory, smi[0], worker=left_worker)
                    for i, item in enumerate(source_inventory):
                        if item[0] == smi[0]:
                            smi = source_inventory[i]
                            renpy.log(f"Refreshed smi after unequip: {smi}")
                            break
                renpy.log(f"Removing {smi[0]} from source: {source_inventory}")
                remove_item_from_inventory(source_inventory, smi[0])
                renpy.log(f"Source after removal: {source_inventory}")
                renpy.log(f"Adding {smi[0]} to target: {target_inventory}")
                add_item_to_inventory(target_inventory, smi[0])
                renpy.log(f"Target after addition: {target_inventory}")
                store.selected_description = ""
                renpy.notify("Item transferred to right")
                # Track tutorial objective 5 - potion transfer
                item_info = next((i for i in items_json["items"] if i["id"] == smi[0]), None)
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
            if swi is not None and (left_worker is not False) and not renpy.get_screen_variable("is_transferring"):
                renpy.set_screen_variable("is_transferring", True)
                renpy.set_screen_variable("selected_worker_item", None)
                source_inventory = manager_inventory if right_worker is None else right_worker.get("inventory", [])
                target_inventory = manager_inventory if left_worker is None else left_worker.get("inventory", [])
                renpy.log(f"Transfer to left: Left={left_worker['name'] if left_worker else 'Storage'}, Right={right_worker['name'] if right_worker else 'Storage'}, Source={source_inventory}, Target={target_inventory}, Item={swi}")
                if swi[2] and right_worker and right_worker is not False:
                    renpy.log(f"Unequipping {swi[0]} from right worker")
                    toggle_equip_item(source_inventory, swi[0], worker=right_worker)
                    for i, item in enumerate(source_inventory):
                        if item[0] == swi[0]:
                            swi = source_inventory[i]
                            renpy.log(f"Refreshed swi after unequip: {swi}")
                            break
                renpy.log(f"Removing {swi[0]} from source: {source_inventory}")
                remove_item_from_inventory(source_inventory, swi[0])
                renpy.log(f"Source after removal: {source_inventory}")
                renpy.log(f"Adding {swi[0]} to target: {target_inventory}")
                add_item_to_inventory(target_inventory, swi[0])
                renpy.log(f"Target after addition: {target_inventory}")
                store.selected_description = ""
                renpy.notify("Item transferred to left")
                # Track tutorial objective 5 - potion transfer
                item_info = next((i for i in items_json["items"] if i["id"] == swi[0]), None)
                if item_info and hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 5 and item_info.get("name", "").lower().find("energy") != -1:
                    store.potion_transferred = True
                    renpy.log("DEBUG: Tutorial - Energy potion transferred to worker")
                    check_objective_completion()
                renpy.restart_interaction()
                renpy.set_screen_variable("is_transferring", False)

        def sell_item(item_id, quantity=1):
            item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
            if item_info:
                sell_price = int(item_info.get("price", 0) * 0.5)  # 50% of buy price
                source_inventory = manager_inventory if left_worker is None else left_worker.get("inventory", [])
                store.money += sell_price * quantity
                remove_item_from_inventory(source_inventory, item_id, quantity)
                renpy.notify(f"Sold {item_info.get('name', 'Unknown')} for ${sell_price * quantity}")
                renpy.restart_interaction()

        def buy_item_from_shop(item_id):
            item_info = next((i for i in items_json["items"] if i["id"] == item_id), None)
            if item_info and store.money >= item_info.get("price", 0):
                store.money -= item_info.get("price", 0)
                add_item_to_inventory(manager_inventory, item_id)
                renpy.notify(f"Bought {item_info.get('name', 'Unknown')} for ${item_info.get('price', 0)}")
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

    modal True
    zorder 99
    tag manager_inventory

    # Dynamic background based on shop_mode
    add get_inventory_bg(shop_mode)
    # Decorative context background strip (same asset used in Tavern/Map)
    add context_menu_bg xalign 0.5 yalign 0.5

    # Money and Date positioned over context menu area (top-right)
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        ysize 80
        # Money display with icon-style $ symbol
        hbox:
            spacing 5
            text "$" color "#3c1f14" size 22 bold True yalign 0.5
            text "[int(money)]" color "#3c1f14" size 28 yalign 0.5
        # Calendar display with icon
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]
            $ month_name = month_names[store.current_month]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color "#3c1f14" size 21 yalign 0.5

    # Left dim panel matching Manage Building width (stops at right strip)
    frame:
        xalign 0.0
        yalign 1.0
        xsize 1511
        ysize 600
        background Solid("#1a1a1acc")
        padding (20, 20)

    # (Context menu moved to bottom of screen so it renders on top of other panels)

    frame:
        xalign 0.0
        yalign 0.9
        yoffset 75
        xsize 1511
        ysize 600
        background None

        hbox:
            spacing 20
            xalign 0.5
            yalign 0.0

            frame:
                xsize 500
                ysize 500
                background Solid("#1a1a1acc")
                padding (10, 10)
                vbox:
                    spacing 10
                    button:
                        background "tablebutton.png"
                        xsize 500
                        ysize 50
                        text "{size=32}{b}[left_worker['name'] if left_worker and left_worker is not False else ('Storage' if left_worker is None else 'None')]{/b}{/size}" xalign 0.5 yalign 0.5 color "#ffffff"
                        action If(not shop_mode, 
                            Show("worker_selection_popup", panel="left", current_left=left_worker, current_right=right_worker, shop_mode=shop_mode),
                            None
                        )
                        sensitive (not shop_mode)
                    hbox:
                        spacing 0
                        button:
                            background "tablebutton.png"
                            xsize 180
                            ysize 40
                            text "Name" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                            action None
                        button:
                            background "tablebutton.png"
                            xsize 90
                            ysize 40
                            text "Price" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                            action None
                        button:
                            background "tablebutton.png"
                            xsize 90
                            ysize 40
                            text "Qty" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                            action None
                        button:
                            background None
                            padding (0, 0, 0, 0)
                            xsize 140
                            ysize 40
                            $ header_action = "Sell" if shop_mode else "Trade"
                            text "[header_action]" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                            action None
                    viewport:
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        ysize 370
                        vbox:
                            spacing 5
                            xoffset 5 # shift entire table (headers + rows) 5px to the right
                            $ left_inventory = [] if left_worker is False else (manager_inventory if left_worker is None else left_worker.get("inventory", []))
                            $ equipped_items = [item for item in left_inventory if item[2]]
                            $ unequipped_items = [item for item in left_inventory if not item[2]]

                            for item in equipped_items:
                                $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                $ bg_button = Solid("#ff69b4")
                                button:
                                    background bg_button
                                    xsize 500
                                    ysize 40
                                    padding (0, 0, 0, 0)
                                    hover_background Solid("#c0c0c0cc")
                                    action If(selected_manager_item != item,
                                            [SetScreenVariable("selected_manager_item", item),
                                            SetScreenVariable("selected_description", item_info.get("description", ""))],
                                            [SetScreenVariable("selected_manager_item", None),
                                            SetScreenVariable("selected_description", "")])
                                    hbox:
                                        spacing 0
                                        frame:
                                            xsize 180
                                            background None
                                            text ("{b}" + item_info.get("name", "Unknown") + "{/b}" if selected_manager_item == item else item_info.get("name", "Unknown")) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text "${}".format(item_info.get("price", 0)) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text str(item[1]) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                        button:
                                            xsize 140
                                            background None
                                            text ("{u}{b}Sell{/b}{/u}" if shop_mode and selected_manager_item == item else "{u}{b}Right{/b}{/u}" if selected_manager_item == item else "Sell" if shop_mode else "Right") size 20 xalign 0.0 yalign 0.5 yoffset 3
                                            action If(selected_manager_item == item and not is_transferring,
                                                        Function(sell_item, item[0]) if shop_mode else Function(transfer_to_right)
                                                    )
                                            sensitive (selected_manager_item == item and (right_worker is not False or shop_mode) and not is_transferring)

                            for i, item in enumerate(unequipped_items):
                                $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                $ bg_button = Solid("#777777") if i % 2 == 0 else Solid("#555555")
                                button:
                                    background bg_button
                                    xsize 500
                                    ysize 40
                                    padding (0, 0, 0, 0)
                                    hover_background Solid("#c0c0c0cc")
                                    action If(selected_manager_item != item,
                                                [
                                                    SetScreenVariable("selected_manager_item", item),
                                                    SetScreenVariable("selected_description",
                                                    item_info.get("description", ""))
                                                ],
                                                [
                                                    SetScreenVariable("selected_manager_item", None),
                                                    SetScreenVariable("selected_description", "")
                                                ]
                                            )
                                    hbox:
                                        spacing 0
                                        frame:
                                            xsize 180
                                            background None
                                            text ("{b}" + item_info.get("name", "Unknown") + "{/b}" if selected_manager_item == item else item_info.get("name", "Unknown")) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text "${}".format(item_info.get("price", 0)) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                        frame:
                                            xsize 90
                                            background None
                                            text str(item[1]) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                        button:
                                            xsize 140
                                            background None
                                            text ("{u}{b}Sell{/b}{/u}" if shop_mode and selected_manager_item == item else "{u}{b}Right{/b}{/u}" if selected_manager_item == item else "Sell" if shop_mode else "Right") size 20 xalign 0.0 yalign 0.5 yoffset 3
                                            action If(selected_manager_item == item and not is_transferring,
                                                        Function(sell_item, item[0]) if shop_mode else Function(transfer_to_right)
                                                    )
                                            sensitive (selected_manager_item == item and (right_worker is not False or shop_mode) and not is_transferring)

            frame:
                xsize 380
                ysize 500
                background Solid("#444444cc")
                padding (10, 10)
                vbox:
                    spacing 10
                    frame:
                        background Solid("#1a1a1a")
                        xsize 360
                        ysize 235
                        padding (10, 10)
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            ysize 215
                            text "{size=22}[selected_description]{/size}" color "#ffffff"
                    # Item image box (50% of the right panel)
                    frame:
                        background Solid("#1a1a1a")
                        xsize 360
                        ysize 235
                        padding (10, 10)
                        $ current_item = selected_worker_item if selected_worker_item is not None else selected_manager_item
                        $ current_item_id = current_item[0] if current_item else None
                        $ img_path_png = f"images/items/{current_item_id}.png" if current_item_id is not None else None
                        $ img_path_jpg = f"images/items/{current_item_id}.jpg" if current_item_id is not None else None
                        $ img_path_jpeg = f"images/items/{current_item_id}.jpeg" if current_item_id is not None else None
                        $ displayable = img_path_png if (current_item_id is not None and renpy.loadable(img_path_png)) else (img_path_jpg if (current_item_id is not None and renpy.loadable(img_path_jpg)) else (img_path_jpeg if (current_item_id is not None and renpy.loadable(img_path_jpeg)) else None))
                        if displayable:
                            add Transform(displayable, xysize=(340, 215)) xalign 0.5 yalign 0.5
                        else:
                            text "No Image found" size 22 color "#ffffff" xalign 0.5 yalign 0.5

            frame:
                xsize 500
                ysize 500
                background Solid("#1a1a1acc")
                padding (10, 10)
                vbox:
                    spacing 10
                    $ shop_name = "Basic Shop" if shop_mode == "shop1" else "Adventurer's Market" if shop_mode == "shop2" else "Elite Emporium" if shop_mode == "shop3" else (right_worker['name'] if right_worker and right_worker is not False else ('Storage' if right_worker is None else 'No Worker Selected'))
                    button:
                        background "tablebutton.png"
                        xsize 500
                        ysize 50
                        text "{size=32}{b}[shop_name]{/b}{/size}" xalign 0.5 yalign 0.5 color "#ffffff"
                        action If(not shop_mode, 
                            Show("worker_selection_popup", panel="right", current_left=left_worker, current_right=right_worker, shop_mode=shop_mode),
                            None
                        )
                        sensitive (not shop_mode)
                    if right_worker is False and shop_mode is None:
                        text "No worker selected." size 26 xalign 0.5 yalign 0.5
                    else:
                        hbox:
                            spacing 0
                            button:
                                background "tablebutton.png"
                                xsize 180
                                ysize 40
                                text "Name" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                                action None
                            button:
                                background "tablebutton.png"
                                xsize 90
                                ysize 40
                                $ qty_or_price = "Price" if shop_mode else "Qty"
                                text "[qty_or_price]" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                                action None
                            if shop_mode is None:
                                button:
                                    background "tablebutton.png"
                                    xsize 90
                                    ysize 40
                                    text "Action" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                                    action None
                            else:
                                # Spacer to alinear con la columna "Buy" cuando hay tienda
                                null width 90 height 40
                            button:
                                background None
                                padding (0, 0, 0, 0)
                                xsize 140
                                ysize 40
                                $ header_action = "Buy" if shop_mode else "Trade"
                                text "[header_action]" size 22 xalign 0.0 yalign 0.5 yoffset 3 color "#ffffff"
                                action None
                        viewport:
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            ysize 370
                            vbox:
                                spacing 5
                                if shop_mode:
                                    $ price_limit = 200 if shop_mode == "shop1" else 500 if shop_mode == "shop2" else 1000
                                    $ shop_items = [(item["id"], 1, False) for item in items_json["items"] if item.get("price", 0) <= price_limit and is_item_available_in_shop(item, shop_mode)]
                                    for item in shop_items:
                                        $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                        $ bg_button = Solid("#777777") if shop_items.index(item) % 2 == 0 else Solid("#555555")
                                        button:
                                            background bg_button
                                            xsize 500
                                            ysize 40
                                            padding (0, 0, 0, 0)
                                            hover_background Solid("#c0c0c0cc")
                                            action If(
                                                        selected_worker_item != item,
                                                        [
                                                            SetScreenVariable("selected_worker_item", item),
                                                            SetScreenVariable("selected_description", item_info.get("description", ""))
                                                        ],
                                                        [
                                                            SetScreenVariable("selected_worker_item", None),
                                                            SetScreenVariable("selected_description", "")
                                                        ]
                                                    )
                                            hbox:
                                                spacing 0
                                                frame:
                                                    xsize 180
                                                    background None
                                                    text ("{b}" + item_info.get("name", "Unknown") + "{/b}" if selected_worker_item == item else item_info.get("name", "Unknown")) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 90
                                                    background None
                                                    text "${}".format(item_info.get("price", 0)) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 90
                                                    background None
                                                button:
                                                    xsize 140
                                                    background None
                                                    text ("{u}{b}Buy{/b}{/u}" if selected_worker_item == item else "Buy") size 20 xalign 0.0 yalign 0.5 yoffset 3
                                                    action If(
                                                                selected_worker_item == item and not is_transferring,
                                                                Function(buy_item_from_shop, item[0])
                                                            )
                                                    sensitive (selected_worker_item == item and not is_transferring and store.money >= item_info.get("price", 0))
                                else:
                                    $ right_inventory = [] if right_worker is False else (manager_inventory if right_worker is None else right_worker.get("inventory", []))
                                    $ equipped_items = [item for item in right_inventory if item[2]]
                                    $ unequipped_items = [item for item in right_inventory if not item[2]]

                                    for item in equipped_items:
                                        $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                        $ label, the_action, is_sens, btn_bg = get_item_action_elements(item, item_info, right_worker)
                                        $ bg_button = Solid("#ff69b4")
                                        button:
                                            background bg_button
                                            xsize 500
                                            ysize 40
                                            padding (0, 0, 0, 0)
                                            hover_background Solid("#c0c0c0cc")
                                            action If(
                                                        selected_worker_item != item,
                                                        [
                                                            SetScreenVariable("selected_worker_item", item),
                                                            SetScreenVariable("selected_description", item_info.get("description", ""))
                                                        ],
                                                        [
                                                            SetScreenVariable("selected_worker_item", None),
                                                            SetScreenVariable("selected_description", "")
                                                        ]
                                                    )
                                            hbox:
                                                spacing 0
                                                frame:
                                                    xsize 180
                                                    background None
                                                    text ("{b}" + item_info.get("name", "Unknown") + "{/b}" if selected_worker_item == item else item_info.get("name", "Unknown")) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 90
                                                    background None
                                                    text str(item[1]) size 20 xalign 0.0 yalign 0.5 yoffset 3
                                                button:
                                                    xsize 90
                                                    background None
                                                    text "[label]" size 20 xalign 0.0 yalign 0.5 yoffset 3
                                                    action the_action
                                                    sensitive is_sens
                                                button:
                                                    xsize 140
                                                    background None
                                                    text ("{u}{b}Left{/b}{/u}" if selected_worker_item == item else "Left") size 20 xalign 0.0 yalign 0.5 yoffset 3
                                                    action If(selected_worker_item == item and (left_worker is not False) and not is_transferring, Function(transfer_to_left))
                                                    sensitive (selected_worker_item == item and (left_worker is not False) and not is_transferring)

                                    for i, item in enumerate(unequipped_items):
                                        $ item_info = next((i for i in items_json["items"] if i["id"] == item[0]), {})
                                        $ label, the_action, is_sens, btn_bg = get_item_action_elements(item, item_info, right_worker)
                                        $ bg_button = Solid("#777777") if i % 2 == 0 else Solid("#555555")
                                        button:
                                            background bg_button
                                            xsize 550
                                            ysize 40
                                            padding (0, 0, 0, 0)
                                            hover_background Solid("#c0c0c0cc")
                                            action If(
                                                        selected_worker_item != item,
                                                        [
                                                            SetScreenVariable("selected_worker_item", item),
                                                            SetScreenVariable("selected_description", item_info.get("description", ""))
                                                        ],
                                                        [
                                                            SetScreenVariable("selected_worker_item", None),
                                                            SetScreenVariable("selected_description", "")
                                                        ]
                                                    )
                                            hbox:
                                                spacing 0
                                                frame:
                                                    xsize 200
                                                    background None
                                                    text ("{b}" + item_info.get("name", "Unknown") + "{/b}" if selected_worker_item == item else item_info.get("name", "Unknown")) size 18 xalign 0.0 yalign 0.5 yoffset 3
                                                frame:
                                                    xsize 100
                                                    background None
                                                    text str(item[1]) size 18 xalign 0.0 yalign 0.5 yoffset 3
                                                button:
                                                    xsize 100
                                                    background None
                                                    text "[label]" size 18 xalign 0.0 yalign 0.5 yoffset 3
                                                    action the_action
                                                    sensitive is_sens
                                                button:
                                                    xsize 150
                                                    background None
                                                    text ("{u}{b}Left{/b}{/u}" if selected_worker_item == item else "Left") size 18 xalign 0.0 yalign 0.5 yoffset 3
                                                    action If(selected_worker_item == item and (left_worker is not False) and not is_transferring, Function(transfer_to_left))
                                                    sensitive (selected_worker_item == item and (left_worker is not False) and not is_transferring)

    # Context menu drawn last so it appears on top
    fixed:
        xalign 1.0
        yalign 0.5
        xsize 320
        yfill True
        xoffset -5
        add context_menu_bg
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 10
            if shop_mode is None:
                if left_worker is not None and left_worker is not False:
                    textbutton "View [left_worker['name']]":
                        action Show("worker_details", worker=left_worker, in_roster=True)
                        xsize 300
                        ysize 50
                        text_size 42
                        text_color "#3c1f14"
                        text_hover_color "#6b6528"
                        align (0.5, 0.5)
                if right_worker is not None and right_worker is not False:
                    textbutton "View [right_worker['name']]":
                        action Show("worker_details", worker=right_worker, in_roster=True)
                        xsize 300
                        ysize 50
                        text_size 42
                        text_color "#3c1f14"
                        text_hover_color "#6b6528"
                        align (0.5, 0.5)
            textbutton "Close":
                action Hide("manager_inventory")
                xsize 300
                ysize 50
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
                align (0.5, 0.5)

    # Money and Date positioned over context menu area (top-right)
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        ysize 80
        hbox:
            spacing 5
            text "$" color "#3c1f14" size 22 bold True yalign 0.5
            text "[int(money)]" color "#3c1f14" size 28 yalign 0.5
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]
            $ month_name = month_names[store.current_month]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color "#3c1f14" size 21 yalign 0.5

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
                        text_size 28
                        text_color "#7a4b2a"
                        text_hover_color "#6b6528"
                    
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
                            for worker in store.workers:
                                textbutton "[worker['name']]":
                                    action [
                                        SetVariable("left_worker" if panel == "left" else "right_worker", worker),
                                        Hide("worker_selection_popup"),
                                        Function(renpy.restart_interaction)
                                    ]
                                    xsize 580
                                    text_size 28
                                    text_color "#7a4b2a"
                                    text_hover_color "#6b6528"
                                    sensitive (panel == "left" and worker != current_right) or (panel == "right" and worker != current_left)
                else:
                    # Display message in shop mode
                    text "Worker selection is disabled in shop mode." size 24 xalign 0.5 color "#7a4b2a"
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action Hide("worker_selection_popup")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

screen confirm_upgrade(building_name):
    modal True
    zorder 200
    style_prefix "confirm"
    add "gui/overlay/confirm.png"

    python:
        building = available_buildings[building_name]
        current_level = building["base_level"]
        upgrade_cost = 5000 * current_level

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
                    [SetVariable("money", money - upgrade_cost), Function(upgrade_building, building_name), Function(lambda: setattr(store, 'building_upgraded_tutorial', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 6 else None), Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 6 else None), Hide("confirm_upgrade")],
                    Show("error_popup", message="You do not have enough money to upgrade.")
                )
                textbutton "No" action Hide("confirm_upgrade")

    key "game_menu" action Hide("confirm_upgrade")

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
                            textbutton "[btype['name']]":
                                xsize 580
                                text_size 28
                                text_color "#7a4b2a"
                                text_hover_color "#6b6528"
                                action [
                                    SetDict(available_buildings[building_name], "type", btype["id"]),
                                    Function(lambda: setattr(store, 'building_1_type_set', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 2 else None),
                                    Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 2 else None),
                                    Hide("building_type_selection")
                                ]
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action Hide("building_type_selection")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

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
                text "[skill_description]" size 24 color "#7a4b2a" text_align 0.0 xalign 0.0
                
                null height 20
                
                # Calculator section
                vbox:
                    spacing 10
                $ total_skill = building["skill"] + building["skill_bonus"]
                $ fixed_cost = int(building["price"] * 0.01)
                $ worker_costs = sum(worker["comfort_level"] * 10 for worker in building["assigned_servants"])
                $ current_bonus_cost = (building["skill_bonus"] // 10) * 100
                $ current_total_cost = fixed_cost + worker_costs + current_bonus_cost
                $ new_bonus_cost = ((building["skill_bonus"] + 10) // 10) * 100 if building["skill_bonus"] < 50 else current_bonus_cost
                $ new_total_cost = fixed_cost + worker_costs + new_bonus_cost
                
                # Base and bonus display with buttons
                hbox:
                    xalign 0.0
                    spacing 10
                    text "Base: [building['skill']], Bonus: [building['skill_bonus']]" size 24 color "#7a4b2a"
                    hbox:
                        spacing 0
                        textbutton "+" style "game_menu_button":
                            action [SetDict(available_buildings[building_name], "skill_bonus", min(50, building["skill_bonus"] + 10)), Function(lambda: setattr(store, 'building_skill_bonus_increased_tutorial', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 6 else None), Function(lambda: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective in [6] else None)]
                            xsize 25
                            text_size 28
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            text_bold True
                            text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                            sensitive building["skill_bonus"] < 50
                        textbutton "-" style "game_menu_button":
                            action SetDict(available_buildings[building_name], "skill_bonus", max(0, building["skill_bonus"] - 10))
                            xsize 25
                            text_size 28
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            text_bold True
                            text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                            sensitive building["skill_bonus"] > 0
                
                if building["skill_bonus"] < 50:
                    text "Next Increase Cost: $[new_total_cost]/day" size 24 color "#444444" xalign 0.0
                else:
                    text "Max [skill_name] Bonus Reached" size 24 color "#1b5e20" xalign 0.0
        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action Hide("adjust_skill_bonus")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

screen Manager(building_name):
    zorder 5
    add get_building_bg(building_name)
    # Decorative context panel background centered like tavern/map
    add context_menu_bg xalign 0.5 yalign 0.5
    
    # Money and Date positioned over context menu area (top-right)
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        ysize 80
        hbox:
            spacing 5
            text "$" color "#3c1f14" size 22 bold True yalign 0.5
            text "[int(money)]" color "#3c1f14" size 28 yalign 0.5
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]
            $ month_name = month_names[store.current_month]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color "#3c1f14" size 21 yalign 0.5

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
                $ building = available_buildings[building_name]
                $ btype_id = building.get("type")
                $ type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                $ skill_name = "Skill" if btype_id is None else next((bt["skill_name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), "Skill")
                $ parts = building_name.split('_')
                $ default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                $ display_name = store.custom_names.get(building_name, default_name)
                $ total_skill = building["skill"] + building["skill_bonus"]
                $ capped_reputation = min(building["reputation"], 1000)
                hbox:
                    spacing 10
                    text "[type_name]: [display_name]" size 42 xalign 0.0 color "#7a4b2a"
                $ fixed_cost = int(building["price"] * 0.01)
                $ worker_costs = sum(worker["comfort_level"] * 10 for worker in building["assigned_servants"])
                $ bonus_cost = (building["skill_bonus"] // 10) * 100
                $ total_costs = fixed_cost + worker_costs + bonus_cost
                text "Costs: $[total_costs] {size=18}(Workers: $[worker_costs], Skill Bonus: $[bonus_cost]){/size=}" size 24 color "#ffffff" xalign 0.0 yalign 0.5
                text "Level: [building['base_level']]" size 24 color "#ffffff" xalign 0.0
                text "Reputation: [capped_reputation]" size 24 color "#ffffff" xalign 0.0
                text "[skill_name]: [total_skill] {size=18}(Base: [building['skill']], Bonus: [building['skill_bonus']]){/size=}" size 24 color "#ffffff" xalign 0.0
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
                                $ current_count = len([s for s in building["assigned_servants"] if building["servant_jobs"].get(s["name"], "") == profession["id"]])
                                $ max_limit = profession.get("max_daily_workers", 99)
                                text "[profession['name']] ([current_count]/[max_limit])" size 26 xalign 0.0 color "#7a4b2a"
                                frame:
                                    background Solid("#1a1a1a99")
                                    padding (10, 10)
                                    xfill True
                                    viewport:
                                        scrollbars "vertical"
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
                                                    background "tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Name" size 24 color "#7a4b2a"
                                                    sensitive False
                                                button:
                                                    background "tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Status" size 24 color "#7a4b2a"
                                                    sensitive False
                                                button:
                                                    background "tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Energy - Health" size 24 color "#7a4b2a"
                                                    sensitive False
                                                button:
                                                    background "tablebutton2.png"
                                                    xsize 275
                                                    ysize 50
                                                    text "Actions" size 24 color "#7a4b2a"
                                                    sensitive False
                                            for worker in [w for w in building["assigned_servants"] if building["servant_jobs"].get(w["name"], "") == profession["id"]]:
                                                hbox:
                                                    spacing 5
                                                    xsize 1440
                                                    textbutton "[worker['name']]":
                                                        xsize 275
                                                        text_size 21
                                                        text_color "#ffffff"
                                                        text_hover_color "#6b6528"
                                                        action Show("worker_details", worker=worker, in_roster=True)
                                                    $ status = "Ok"
                                                    if int(worker.get("rebelliousness", 50)) > 80:
                                                        $ status = "Rebellious"
                                                    elif int(worker.get("rebelliousness", 50)) < 80 and int(worker.get("joy", 50)) < 20:
                                                        $ status = "Sad"
                                                    textbutton "[status]":
                                                        xsize 275
                                                        text_size 21
                                                        text_color "#ffffff"
                                                        text_hover_color "#6b6528"
                                                    textbutton "E: [worker['energy']]/[calculate_max_energy(worker)] - H: [worker['health']]/[calculate_max_health(worker)]":
                                                        xsize 275
                                                        text_size 21
                                                        text_color "#ffffff"
                                                        text_hover_color "#6b6528"
                                                    textbutton "Change / View skills":
                                                        xsize 275
                                                        text_size 21
                                                        text_color "#ffffff"
                                                        text_hover_color "#6b6528"
                                                        action Show("job_selection", worker=worker)
    
    # Right panel: building management buttons and global context menu
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
                action Show("rename_building", building_name=building_name)
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
                ysize 50
                align (0.5, 0.5)
            
            # Only show upgrade buttons if building has a type
            $ building = available_buildings[building_name]
            if building.get("type") is not None:
                textbutton "Upgrade Building":
                    action Show("confirm_upgrade", building_name=building_name)
                    xsize 300
                    text_size 42
                    text_color "#3c1f14"
                    text_hover_color "#6b6528"
                    ysize 50
                    align (0.5, 0.5)
                $ skill_name = next((bt.get('skill_name', 'Skill') for bt in building_types_json.get('building_types', []) if bt.get('id') == building.get('type')), 'Skill')
                textbutton "[skill_name]":
                    action Show("adjust_skill_bonus", building_name=building_name)
                    xsize 300
                    text_size 42
                    text_color "#3c1f14"
                    text_hover_color "#6b6528"
                    ysize 50
                    align (0.5, 0.5)
            
            # Building type/change type button
            if building.get("type") is None:
                textbutton "Building Type":
                    action Show("building_type_selection", building_name=building_name)
                    xsize 300
                    text_size 42
                    text_color "#3c1f14"
                    text_hover_color "#6b6528"
                    ysize 50
                    align (0.5, 0.5)
            else:
                textbutton "Change Type":
                    action Show("confirm_change_type", building_name=building_name)
                    xsize 300
                    text_size 42
                    text_color "#3c1f14"
                    text_hover_color "#6b6528"
                    ysize 50
                    align (0.5, 0.5)
            
            textbutton "Storage":
                action [
                    SetVariable("left_worker", None),
                    SetVariable("right_worker", store.workers[0] if store.workers else False),
                    Show("manager_inventory")
                ]
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
                ysize 50
                align (0.5, 0.5)
            textbutton "Back":
                action [SetVariable("current_bg", tavern_bg), Hide("Manager"), Show("tavern")]
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
                ysize 50
                align (0.5, 0.5)

            # (Context-only building options retained; tavern global options removed)

    # (Removed duplicate foreground left panel)

screen building_selection(worker):
    modal True
    zorder 99
    add Solid("#000000dd")
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
                                text_size 28
                                text_color "#7a4b2a"
                                text_hover_color "#6b6528"
                                action [
                                    Function(remove_worker_from_building, worker),
                                    Function(lambda w, b: available_buildings[b]["assigned_servants"].append(w) if w not in available_buildings[b]["assigned_servants"] else None, worker, building_name),
                                    SetDict(worker, "assigned_building", building_name),
                                    Hide("building_selection"),
                                    Show("workers")
                                ]
                                sensitive True  # Always sensitive if owned
                        else:
                            textbutton "[type_name]: [display_name] (Not Available)":
                                xsize 500
                                text_size 28
                                text_color "#7a4b2a"
                                text_hover_color "#6b6528"
                                sensitive False
        
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action [Hide("building_selection"), Show("workers")]
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

screen rename_building(building_name):
    modal True
    zorder 99
    default new_name = custom_names[building_name]
    add Solid("#000000dd")
    frame:
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 500
        background Solid("#1a1a1acc")
        padding (20, 20)
        # Title outside the vbox, centered
        frame:
            xalign 0.5
            yalign 0.0
            background None
            label "Rename [custom_names[building_name]]:" style "header_style"
        # Main content vbox
        vbox:
            xalign 0.1
            yalign 0.1  # Adjusted offset to give more space below the title
            spacing 25
            null height 40  # Match adjust_skill_bonus spacing
            vbox:
                spacing 10
                # Input field centered
                input:
                    id "new_name"
                    value ScreenVariableInputValue("new_name")
                    length 20
                    color "#ffffff"
                null height 15
        # Bottom action buttons: Confirm (left) and Close (right)
        textbutton "Confirm":
            xalign 0.0
            yalign 1.0
            xoffset 20
            text_size 24
            text_color "#ffffff"
            action If(
                new_name.strip() != "",
                [
                    Function(custom_names.update, {building_name: new_name}),
                    Hide("rename_building"),
                    Show("Manager", building_name=building_name)
                ],
                Show("error_popup", message="Name cannot be empty")
            )
        textbutton "Close":
            xalign 1.0
            yalign 1.0
            xoffset -20
            text_size 24
            text_color "#ffffff"
            action Hide("rename_building")

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
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
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
                    $ num = len(owned_buildings)
                    if num < max_building:
                        $ price = (num + 1) * 10000
                        $ building_name = f"Building {str(num + 1)}"
                        textbutton "[building_name] - $[price]":
                            xsize 500
                            text_size 28
                            text_color "#7a4b2a"
                            text_hover_color "#6b6528"
                            action If(money >= price,
                                [
                                    Function(add_new_building, building_name, price),
                                    SetVariable("money", money - price),
                                    Function(store.custom_names.__setitem__, building_name, building_name),
                                    Function(store.owned_buildings.append, building_name),
                                    SetVariable("buildings_owned", len(store.owned_buildings)),
                                    Hide("buy_buildings"),
                                ])
                            sensitive (money >= price)
                    else:
                        text "No more buildings available to purchase." size 28 xalign 0.5 color "#7a4b2a"
            

screen buy_servants_table():
    zorder 90
    modal True
    
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
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action Hide("buy_servants_table")
            xalign 1.0
            yalign 0.0
            xoffset -85
            yoffset 85
            
        vbox:
            xalign 0.5
            spacing 15
            null height 80
            label "Buy Servants" xalign 0.5 style "header_style"
            null height 10
            
            # Header row (outside the viewport)
            fixed:
                xalign 0.5
                xoffset -5  # shift headers 5px left
                ysize 50
                xsize 870
                hbox:
                    spacing 30
                    xsize 870
                    yalign 0.5
                    button:
                        background "tablebutton4.png"
                        xsize 200
                        ysize 50
                        text "Name" size 26 color "#7a4b2a" text_align 0.0
                        sensitive False
                    button:
                        background "tablebutton4.png"
                        xsize 200
                        ysize 50
                        text "Price" size 26 color "#7a4b2a" text_align 0.0
                        sensitive False
                    button:
                        background "tablebutton4.png"
                        xsize 200
                        ysize 50
                        text "Trait" size 26 color "#7a4b2a" text_align 0.0
                        sensitive False
                    button:
                        background "tablebutton4.png"
                        xsize 200
                        ysize 50
                        text "Actions" size 26 color "#7a4b2a" text_align 0.0
                        sensitive False
                
            
            # Main content area without scroll
            vbox:
                xalign 0.5
                spacing 8
                for worker in displayed_workers:
                    hbox:
                        xalign 0.5
                        spacing 30
                        xoffset 0
                        xsize 870
                        yalign 0.5
                        button:
                            background "tablebutton1b.png"
                            xsize 200
                            ysize 50
                            text "[worker['name']]" size 24 color "#7a4b2a" hover_color "#6b6528" text_align 0.0
                            action Show("worker_details", worker=worker, in_roster=False, from_buy_workers=True)
                        button:
                            background "tablebutton1b.png"
                            xsize 200
                            ysize 50
                            text "$[worker['cost']]" size 24 color "#7a4b2a" text_align 0.0
                        button:
                            background "tablebutton1b.png"
                            xsize 200
                            ysize 50
                            $ trait_text = ", ".join(worker.get("traits", [])[:2]) if worker.get("traits") else "No Traits"
                            text "[trait_text]" size 24 color "#7a4b2a" text_align 0.0
                        button:
                            background "tablebutton1b.png"
                            xsize 200
                            ysize 50
                            text "Buy" size 24 color "#7a4b2a" hover_color "#6b6528" text_align 0.0
                            action Function(buy_worker, worker)
                            sensitive (money >= worker["cost"])



screen shop_selection():
    modal True
    zorder 100
    python:
        # Sync store.unlocked_shops with persistent.unlocked_shops
        # This ensures shops unlocked by events are properly displayed
        # Initialize persistent.unlocked_shops if it doesn't exist
        if not hasattr(persistent, 'unlocked_shops') or persistent.unlocked_shops is None:
            persistent.unlocked_shops = {"shop1": True, "shop2": False, "shop3": False}
            renpy.log("Initialized persistent.unlocked_shops in shop_selection screen")
        
        # Sync from persistent to store
        if persistent.unlocked_shops:
            for shop_key in ["shop1", "shop2", "shop3"]:
                if shop_key in persistent.unlocked_shops and persistent.unlocked_shops[shop_key]:
                    store.unlocked_shops[shop_key] = True
                    renpy.log(f"Synced {shop_key} unlock from persistent to store: {store.unlocked_shops[shop_key]}")
        renpy.log(f"Final shop unlock state - persistent: {persistent.unlocked_shops}, store: {store.unlocked_shops}")
    
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
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
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
                        text_size 28
                        text_color "#7a4b2a"
                        text_hover_color "#6b6528"
                        sensitive "shop1" in unlocked_shops and unlocked_shops["shop1"]
                    $ shop2_name = "Adventurer's Market" if unlocked_shops.get("shop2", False) else "Adventurer's Market (Closed)"
                    textbutton "[shop2_name]":
                        action [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop2"), Hide("shop_selection")]
                        xsize 500
                        text_size 28
                        text_color "#7a4b2a"
                        text_hover_color "#6b6528"
                        sensitive "shop2" in unlocked_shops and unlocked_shops["shop2"]
                    $ shop3_name = "Elite Emporium (Closed)" if not unlocked_shops.get("shop3", False) else "Elite Emporium"
                    textbutton "[shop3_name]":
                        action [SetVariable("left_worker", None), SetVariable("right_worker", None), Show("manager_inventory", shop_mode="shop3"), Hide("shop_selection")]
                        xsize 500
                        text_size 28
                        text_color "#7a4b2a"
                        text_hover_color "#6b6528"
                        sensitive "shop3" in unlocked_shops and unlocked_shops["shop3"]
            

screen more_details_screen(worker):
    modal True
    zorder 99
    add Solid("#000000dd")
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#2d2d2dcc")
        padding (20, 20)
        vbox:
            spacing 15
            text "Description: [worker.get('description', 'No description available')]" size 18 color "#ffffff"
            text "Folder: [worker.get('folder', 'default')]" size 16 color "#cccccc"
            if worker.get('procedural', False):
                text "Type: Procedural Worker" size 16 color "#ffcc66"
            else:
                text "Type: Predefined Character" size 16 color "#66ccff"
            textbutton "Close":
                style "nav_button_text"
                action Hide("more_details_screen")

screen interaction_result(worker, interaction):
    modal True
    zorder 99
    add Solid("#000000dd")
    frame:
        xalign 0.5
        yalign 0.5
        background Solid("#1a1a1acc")
        padding (5, 5)
        vbox:
            spacing 15
            # Display the media file associated with the interaction
            $ media_file = get_interaction_image(worker, interaction)
            if media_file and media_file.lower().endswith(('.webm', '.mp4')):
                add Movie(
                    play=media_file,
                    size=(1600, 900),
                    loop=True
                )
            elif media_file:
                add media_file:
                    xalign 0.5
                    yalign 0.5
                    fit "contain"
                    xysize (1600, 900)
            else:
                text "No media available" color "#ffffff" xalign 0.5

            text "[interaction['description']]" size 24 color "#ffffff" xalign 0.5
            textbutton "Close":
                style "nav_button_text"
                xalign 0.5
                action [
                    Hide("interaction_result"),
                    Function(lambda i=interaction: setattr(store, 'tutorial_friendly_chat_done', True) if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('id') in ("friendship_chat_female", "friendship_chat_male")) else None),
                    Function(lambda i=interaction: check_objective_completion() if hasattr(store, 'tutorial_active') and store.tutorial_active and store.current_objective == 7 and (i.get('id') in ("friendship_chat_female", "friendship_chat_male")) else None)
                ]

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
        $ current_comfort_desired = worker.get("comfort_desired", 1)
        $ current_daily_cost = current_comfort * 10
        $ current_relationship = worker.get("relationship", 10 + current_comfort)
        
        vbox:
            spacing 15
            null height 15
            label "Worker Comfort" xalign 0.5 style "header_style"
            null height 10
            vbox:
                xsize 580
                spacing 10
                xoffset 30
                yoffset 25
                
                # Comfort description
                text "Comfort determines the quality of life and accommodations provided to your worker. Higher comfort levels improve worker satisfaction and relationship, but increase daily maintenance costs. Comfortable workers are more loyal and perform better over time." size 24 color "#7a4b2a" text_align 0.0 xalign 0.0
                
                null height 20
                
                # Current status section
                vbox:
                    spacing 10
                    
                    text "Current Status:" size 26 color "#7a4b2a" bold True
                    text "• Comfort Level: [current_comfort]" size 24 color "#7a4b2a"
                    text "• Desired Comfort: [current_comfort_desired]" size 24 color "#7a4b2a"
                    text "• Daily Cost: $[current_daily_cost]" size 24 color "#7a4b2a"
                    text "• Relationship: [current_relationship]" size 24 color "#7a4b2a"
                    
                    null height 20
                    
                    # Comfort adjustment with buttons
                    hbox:
                        xalign 0.0
                        spacing 10
                        text "Adjust Comfort:" size 24 color "#7a4b2a"
                        hbox:
                            spacing 0
                            textbutton "+" style "game_menu_button":
                                action [
                                    SetDict(worker, "comfort_level", current_comfort + 1),
                                    SetDict(worker, "relationship", max(10, 10 + current_comfort + 1))
                                ]
                                xsize 25
                                text_size 28
                                text_color "#7a4b2a"
                                text_hover_color "#6b6528"
                                text_bold True
                                text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                                sensitive current_comfort < 20
                            textbutton "-" style "game_menu_button":
                                action [
                                    SetDict(worker, "comfort_level", max(1, current_comfort - 1)),
                                    SetDict(worker, "relationship", max(10, 10 + max(1, current_comfort - 1)))
                                ]
                                xsize 25
                                text_size 28
                                text_color "#7a4b2a"
                                text_hover_color "#6b6528"
                                text_bold True
                                text_font "gui/font/MorrisRomanAlternate-Black.ttf"
                                sensitive current_comfort > 1
                    
                    $ next_daily_cost = (current_comfort + 1) * 10 if current_comfort < 20 else current_daily_cost
                    $ prev_daily_cost = max(1, current_comfort - 1) * 10 if current_comfort > 1 else current_daily_cost
                    
                    if current_comfort < 20:
                        text "Next Level Cost: $[next_daily_cost]/day" size 24 color "#444444" xalign 0.0
                    else:
                        text "Maximum Comfort Reached" size 24 color "#1b5e20" xalign 0.0
                    

        
        # Return button (top-right)
        imagebutton:
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action Hide("adjust_comfort")
            xalign 1.0
            yalign 0.0
            xoffset -15
            yoffset 5

screen interaction_menu(worker):
    modal True
    zorder 99
    add Solid("#000000dd")
    frame:
        style "interaction_frame"
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 15
            label "Interact with [worker['name']]" xalign 0.5 style "header_style"
            $ interactions = load_interactions()
            $ player_gender = "male" if player_title.lower() == "lord" else "female"
            $ filtered_interactions = filter_interactions_by_gender(interactions, player_gender)
            $ filtered_interactions = filter_interactions_by_worker_gender(filtered_interactions, worker)
            $ filtered_interactions = filter_interactions_by_stats(filtered_interactions, worker)
            $ filtered_interactions = filter_interactions_by_flags(filtered_interactions, worker)
            $ filtered_interactions = filter_interactions_by_traits(filtered_interactions, worker)
            $ filtered_interactions = filter_interactions_by_items(filtered_interactions, worker)
            $ filtered_interactions = filter_interactions_by_usage_limits(filtered_interactions, worker)
            $ filtered_interactions = filter_interactions_by_worker_name(filtered_interactions, worker)
            
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

# New screen to display interactions in a specific category
screen interaction_category(worker, category_name, interactions_list):
    modal True
    zorder 100
    add Solid("#000000dd")
    frame:
        style "interaction_frame"
        xalign 0.5
        yalign 0.5
        vbox:
            spacing 15
            label "[category_name] for [worker['name']]" xalign 0.0 style "header_style"
            
            viewport:
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 500
                xsize 600
                vbox:
                    spacing 10
                    for interaction in interactions_list:
                        vbox:
                            spacing 5
                            textbutton "[interaction['name']]":
                                style "interaction_button"
                                text_style "interaction_button_text"
                                action [
                                    Function(apply_interaction_effects, worker, interaction),
                                    Show("interaction_result", worker=worker, interaction=interaction),
                                    Hide("interaction_category")
                                ]
                                sensitive (worker["energy"] >= interaction.get("cost_energy", 0)
                                            and 
                                            worker["health"] >= interaction.get("cost_health", 0) 
                                            and
                                            store.money >= interaction.get("cost_money", 0)
                                        )
                                xalign 0.0
                                text_xalign 0.0
                            
                            # Show costs below each interaction
                            hbox:
                                spacing 10
                                xalign 0.0
                                if interaction.get("cost_energy", 0) > 0:
                                    text "Energy: [interaction.get('cost_energy', 0)]" style "interaction_text" size 14 color "#2c4aa6"
                                if interaction.get("cost_health", 0) > 0:
                                    text "Health: [interaction.get('cost_health', 0)]" style "interaction_text" size 14 color "#a63c3c"
                                if interaction.get("cost_money", 0) > 0:
                                    text "Money: $[interaction.get('cost_money', 0)]" style "interaction_text" size 14 color "#2a6b2a"
                
            hbox:
                spacing 20
                xalign 0.5
                textbutton "Back":
                    style "interaction_button"
                    text_style "interaction_button_text"
                    action Hide("interaction_category")
                textbutton "Close All":
                    style "interaction_button"
                    text_style "interaction_button_text"
                    action [Hide("interaction_category"), Hide("interaction_menu")]

screen worker_details(worker, in_roster=False, from_buy_workers=False, from_recruitment=False):
    # Ensure worker is updated with latest data from store.workers
    $ worker = next((w for w in store.workers if w["name"] == worker["name"]), worker)  # Sync with store.workers
    $ worker = ensure_worker_defaults(worker)
    $ sell_text = get_sell_text(worker)
    $ comfort_level = worker.get("comfort_level", 1)
    $ daily_cost = comfort_level * 10
    default current_image = get_worker_image(worker)
    default panel_mode = current_panel_mode

    zorder 99
    modal True
    add Solid("#000000dd")

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
                idle Transform("gui/button/return_idle.png", zoom=0.5)
                hover Transform("gui/button/return_hover.png", zoom=0.5)
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
                    if in_roster:
                        hbox:
                            xalign 0.5
                            xoffset 90
                            yoffset 95
                            spacing 40
                            textbutton "Previous":
                                background None
                                text_size 23
                                text_color "#3c1f14"
                                text_hover_color "#6b6528"
                                action If(len(workers) > 0, [
                                    SetVariable("current_worker_index", (current_worker_index - 1) % len(workers)),
                                    SetScreenVariable("current_image", get_worker_image(workers[(current_worker_index - 1) % len(workers)])),
                                    Show("worker_details", worker=workers[(current_worker_index - 1) % len(workers)], in_roster=True)
                                ])
                            textbutton "Next":
                                background None
                                text_size 23
                                text_color "#3c1f14"
                                text_hover_color "#6b6528"
                                action If(len(workers) > 0, [
                                    SetVariable("current_worker_index", (current_worker_index + 1) % len(workers)),
                                    SetScreenVariable("current_image", get_worker_image(workers[(current_worker_index + 1) % len(workers)])),
                                    Show("worker_details", worker=workers[(current_worker_index + 1) % len(workers)], in_roster=True)
                                ])

                # Right Column: Panels (skills/stats) and actions
                vbox:
                    xsize 560
                    spacing 5
                    xoffset -40
                    yoffset 124
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
                                text_size 32
                                text_color "#7a4b2a"
                                text_hover_color "#6b6528"
                                action SetScreenVariable("current_image", get_pattern_matches_flexible(worker.get('folder', ''), "Profile", ["png", "jpg", "jpeg", "webp", "webm", "mp4"]) or get_worker_image(worker))
                            text "Level: [worker.get('level', 1)]" size 18 color "#ffffff" yalign 0.5 yoffset 2 xoffset 5
                            text "XP: [worker.get('success_count', 0)]/[20 * worker.get('level', 1)]" size 18 color "#ffffff" yalign 0.5 yoffset 2 xoffset 5
                            if in_roster:
                                textbutton "Comfort: [comfort_level] - $[daily_cost]":
                                    background None
                                    yalign 0.5
                                    yoffset 2
                                    xoffset 5
                                    text_size 18
                                    text_color "#7a4b2a"
                                    text_hover_color "#6b6528"
                                    action Show("adjust_comfort", worker=worker)
                        # Health and Energy Bars
                        hbox:
                            spacing 5
                            frame:
                                background "#00000044"
                                xsize 200
                                ysize 40
                                padding (5, 5)
                                fixed:
                                    xsize 190
                                    ysize 30
                                    bar:
                                        value worker["energy"]
                                        range calculate_max_energy(worker)
                                        xsize 190
                                        ysize 30
                                        left_bar "#0000ff"
                                        right_bar "#444444"
                                    text "Energy [worker['energy']]/[calculate_max_energy(worker)]" size 18 color "#ffffff" xalign 0.5 yalign 0.5
                            frame:
                                background "#00000044"
                                xsize 200
                                ysize 40
                                padding (5, 5)
                                fixed:
                                    xsize 190
                                    ysize 30
                                    bar:
                                        value worker["health"]
                                        range calculate_max_health(worker)
                                        xsize 190
                                        ysize 30
                                        left_bar "#ff0000"
                                        right_bar "#444444"
                                    text "Health [worker['health']]/[calculate_max_health(worker)]" size 18 color "#ffffff" xalign 0.5 yalign 0.5
                    
                    # Toggle Panel Mode Button - BELOW Worker Info
                    textbutton "Switch to [panel_mode == 'skills' and 'Stats' or 'Skills']":
                        text_size 22
                        text_hover_color "#6b6528"
                        xalign 0.0
                        action [
                            SetScreenVariable("panel_mode", panel_mode == "skills" and "stats" or "skills"),
                            Function(set_global_panel_mode, panel_mode == "skills" and "stats" or "skills")
                        ]

                    # Skills Panel
                    if panel_mode == "skills":
                        frame:
                            background "#00000044"
                            xsize 540
                            ysize 580
                            padding (15, 10)
                            viewport:
                                scrollbars "vertical"
                                mousewheel True
                                draggable True
                                ysize 580
                                xfill True
                                vbox:
                                    spacing 5
                                    # Inside the worker_details screen
                                    for skill_name, level in [(sid, lvl) for sid, lvl in worker.get("original_skills", worker["skills"]).items() if persistent.nsfw_enabled or sid in sfw_skills]:
                                        $ total_skill = calculate_skill_with_traits(worker, skill_name)
                                        $ skill_uses = worker["skill_uses"].get(skill_name, 0)
                                        $ uses_needed = level
                                        $ progress = skill_uses / float(uses_needed) if uses_needed > 0 else 0.0
                                        vbox:
                                            spacing 5
                                            bar:
                                                value progress
                                                range 1.0
                                                xsize 475
                                                ysize 10
                                                left_bar "#6b6528"
                                                right_bar "#444444"
                                            button:
                                                action SetScreenVariable("current_image", get_worker_image_random(worker, skill_name) or get_worker_image(worker))
                                                hbox:
                                                    spacing 10
                                                    text "[skill_name]" size 20 xalign 0.0 yalign 0.5
                                                    text "[total_skill]/100" size 20 xalign 0.0 yalign 0.5  # Display total skill
                                    null height 50

                    # Stats Panel
                    elif panel_mode == "stats":
                        frame:
                            background "#00000044"
                            xsize 540
                            ysize 580
                            padding (15, 10)
                            vbox:
                                spacing 5
                                text "Rebelliousness: [worker['rebelliousness']]/100" size 24 color "#ffffff"
                                bar:
                                    value worker["rebelliousness"]
                                    range 100
                                    xsize 475
                                    ysize 15
                                    left_bar "#6b6528"
                                    right_bar "#444444"
                                text "Joy: [worker['joy']]/100" size 24 color "#ffffff"
                                bar:
                                    value worker["joy"]
                                    range 100
                                    xsize 475
                                    ysize 15
                                    left_bar "#6b6528"
                                    right_bar "#444444"
                                text "Romance: [worker['romance']]/100" size 24 color "#ffffff"
                                bar:
                                    value worker["romance"]
                                    range 100
                                    xsize 475
                                    ysize 15
                                    left_bar "#6b6528"
                                    right_bar "#444444"
                                # Show Libido only in NSFW mode
                                if persistent.nsfw_enabled:
                                    text "Libido: [worker['libido']]/20" size 24 color "#ffffff"
                                    bar:
                                        value worker["libido"]
                                        range 20
                                        xsize 475
                                        ysize 15
                                        left_bar "#6b6528"
                                        right_bar "#444444"
                                text "Relationship: [worker['relationship']]/100" size 24 color "#ffffff"
                                bar:
                                    value worker["relationship"]
                                    range 100
                                    xsize 475
                                    ysize 15
                                    left_bar "#6b6528"
                                    right_bar "#444444"
                                null height 0
                                hbox:
                                    spacing 10
                                    yoffset 6
                                    button:
                                        background "tablebutton.png"
                                        xsize 150
                                        ysize 44
                                        text "Trait" size 23
                                        sensitive False
                                    button:
                                        background "tablebutton.png"
                                        xsize 320
                                        ysize 44
                                        text "Description" size 23
                                        sensitive False
                                # Subtle translucent overlay behind traits list
                                frame:
                                    background "#00000022"
                                    padding (0, 4)
                                    xfill True
                                    yoffset 0
                                    viewport:
                                        scrollbars "vertical"
                                        mousewheel True
                                        draggable True
                                        ysize 435
                                        xfill True
                                        vbox:
                                            spacing 10
                                            # Filter traits: show all if NSFW enabled, otherwise only SFW traits
                                            for trait in [t for t in worker.get("traits", []) if persistent.nsfw_enabled or any(t == tr["name"] and not tr.get("nsfw", False) for tr in traits_list)]:
                                                $ desc = get_trait_desc(trait)
                                                hbox:
                                                    spacing 10
                                                    button:
                                                        background "tablebutton.png"
                                                        xsize 150
                                                        ysize 60
                                                        text "[trait]" size 22
                                                    button:
                                                        background "tablebutton.png"
                                                        xsize 320
                                                        ysize 60
                                                        text "[desc]" size 20

                    # Action Buttons Section
                    vbox:
                        spacing 3
                        xalign 0.5
                        yoffset -5
                        if in_roster:
                            hbox:
                                spacing 1
                                button:
                                    background "tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "Interact" size 23 xalign 0.5 hover_color "#6b6528"
                                    action Show("interaction_menu", worker=worker)
                                button:
                                    background "tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "Inventory" size 23 xalign 0.5 hover_color "#6b6528"
                                    action [SetVariable("left_worker", None), SetVariable("right_worker", worker), Show("manager_inventory"), Hide("worker_details")]
                    
                    # More Details and Sell Buttons (separate vbox for positioning)
                    vbox:
                        spacing 1
                        xalign 0.5
                        yoffset -20
                        if in_roster:
                            hbox:
                                spacing 1
                                button:
                                    background "tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "More Details" size 23 xalign 0.5 hover_color "#6b6528"
                                    action Show("more_details_screen", worker=worker)
                                button:
                                    background "tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "[sell_text]" size 23 xalign 0.5 hover_color "#6b6528"
                                    action [Function(sell_worker, worker), Hide("worker_details")]
                        else:
                            hbox:
                                spacing 1
                                yoffset 15
                                button:
                                    background "tablebutton.png"
                                    xsize 250
                                    ysize 50
                                    text "More Details" size 23 xalign 0.5 hover_color "#6b6528"
                                    action Show("more_details_screen", worker=worker)
                                if from_buy_workers:
                                    button:
                                        background "tablebutton.png"
                                        xsize 250
                                        ysize 50
                                        text "Buy ($[worker['cost']])" size 23 xalign 0.5
                                        action [Function(buy_worker, worker), Hide("worker_details")]





screen workers():
    zorder 10
    modal True
    add workers_bg
    add Solid("#00000099")
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
                idle Transform("gui/button/return_idle.png", zoom=0.5)
                hover Transform("gui/button/return_hover.png", zoom=0.5)
                action [Hide("workers"), Show("tavern")]
                align (0.985, 0.10)
                xoffset -80
                yoffset 22
        vbox:
            xalign 0.5  # Center the vbox contents horizontally
            spacing 15
            null height 80  # Push content further down into the lighter beige area
            label "Manage Workers" xalign 0.5 style "header_style"
            null height 5
            
            # Filtro por edificio
            hbox:
                spacing 20
                xalign 0.5
                yoffset -10
                
                text "Filter by Building:" size 20 color "#7a4b2a" yalign 0.5
                
                # Crear lista de edificios únicos
                python:
                    # Ensure worker_building_filter is set to default if not defined
                    if not hasattr(store, 'worker_building_filter') or store.worker_building_filter is None:
                        store.worker_building_filter = "All Workers"
                    unique_buildings = ["All Workers"]
                    for worker in workers:
                        building_name = worker.get('assigned_building', 'Unassigned')
                        # Obtener el nombre de display del edificio
                        building = available_buildings.get(building_name, {})
                        btype_id = building.get("type")
                        type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                        parts = building_name.split('_')
                        default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                        building_display_name = store.custom_names.get(building_name, default_name)
                        full_display_name = f"{type_name}: {building_display_name}"
                        
                        if full_display_name not in unique_buildings:
                            unique_buildings.append(full_display_name)
                
                # Menú desplegable para seleccionar edificio
                frame:
                    background "#1a1a1acc"
                    padding (10, 5)
                    
                    button:
                        xsize 300
                        ysize 40
                        background "#333333"
                        hover_background "#555555"
                        
                        text "[worker_building_filter]" size 18 color "#ffffff" xalign 0.5 yalign 0.5
                        
                        action Show("worker_building_filter_menu", buildings=unique_buildings)
            
            null height 0
            
            # Header row (outside the viewport so the scrollbar starts below it)
            hbox:
                xalign 0.5
                xoffset -45  # Shift headers 5px further left
                yoffset -15  # Move headers up closer to filter
                spacing 14  # Much tighter gaps between columns
                xsize 1200
                yalign 0.5
                button:
                    background "tablebutton4.png"
                    xsize 180
                    ysize 50
                    text "Name" size 26 color "#7a4b2a"
                    sensitive False
                button:
                    background "tablebutton4.png"
                    xsize 180
                    ysize 50
                    text "Building" size 26 color "#7a4b2a"
                    sensitive False
                button:
                    background "tablebutton4.png"
                    xsize 180
                    ysize 50
                    text "Job" size 26 color "#7a4b2a"
                    sensitive False
                button:
                    background "tablebutton4.png"
                    xsize 180
                    ysize 50
                    text "Type" size 26 color "#7a4b2a"
                    sensitive False
                button:
                    background "tablebutton4.png"
                    xsize 180
                    ysize 50
                    text "Actions" size 26 color "#7a4b2a"
                    sensitive False
            
            # Main content area (viewport)
            viewport:
                xalign 0.5  # Center the viewport horizontally
                yalign 0.5  # Center the viewport vertically (if needed, but vbox alignment handles this)
                yoffset -20  # Move viewport up closer to headers
                scrollbars "vertical"
                mousewheel True
                draggable True
                ysize 400  # Reduced viewport height to 400px
                xsize 1305  # Move scrollbar 5px further left
                vbox:
                    xalign 0.5  # Center the vbox inside the viewport horizontally
                    spacing 8
                    
                    # Aplicar filtro
                    python:
                        if worker_building_filter == "All Workers":
                            filtered_workers = workers
                        else:
                            filtered_workers = []
                            for worker in workers:
                                building_name = worker.get('assigned_building', 'Unassigned')
                                # Obtener el nombre de display del edificio
                                building = available_buildings.get(building_name, {})
                                btype_id = building.get("type")
                                type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                                parts = building_name.split('_')
                                default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                                building_display_name = store.custom_names.get(building_name, default_name)
                                full_display_name = f"{type_name}: {building_display_name}"
                                
                                if full_display_name == worker_building_filter:
                                    filtered_workers.append(worker)
                    
                    for worker in filtered_workers:
                        hbox:
                            xalign 0.5  # Center each worker row horizontally
                            spacing 14
                            xoffset 5  # Shift row contents slightly to the right
                            xsize 1200
                            yalign 0.5
                            button:
                                background "tablebutton1b.png"
                                xsize 180
                                ysize 50
                                text "[worker['name']]" size 24 color "#7a4b2a" hover_color "#6b6528"
                                action Show("worker_details", worker=worker, in_roster=True)
                            $ assigned_building = worker.get("assigned_building", "Unassigned")
                            $ building_display_name = custom_names.get(assigned_building, assigned_building)
                            button:
                                background "tablebutton1b.png"
                                xsize 180
                                ysize 50
                                text "[building_display_name]" size 24 color "#7a4b2a" hover_color "#6b6528"
                                action Show("building_selection", worker=worker)
                            if worker.get("assigned_building", "Unassigned") != "Unassigned":
                                $ building_name = worker["assigned_building"]
                                $ job_id = available_buildings[building_name]["servant_jobs"].get(worker["name"], "Unassigned")
                                $ btype = next((bt for bt in building_types_json.get("building_types", []) if bt["id"] == available_buildings[building_name]["type"]), None)
                                $ job_name = "Unassigned" if job_id.lower() == "unassigned" else (next((p["name"] for p in btype.get("professions", []) if p["id"] == job_id), job_id) if btype else job_id)
                                button:
                                    background "tablebutton1b.png"
                                    xsize 180
                                    ysize 50
                                    text "[job_name]" size 24 color "#7a4b2a" hover_color "#6b6528"
                                    action Show("job_selection", worker=worker)
                            else:
                                button:
                                    background "tablebutton1b.png"
                                    xsize 180
                                    ysize 50
                                    text "Unassigned" size 24 color "#7a4b2a" hover_color "#6b6528"
                                    action Show("job_selection", worker=worker)
                            button:
                                background "tablebutton1b.png"
                                xsize 180
                                ysize 50
                                text "[ 'Servant' if worker.get('is_servant', False) else 'Worker' ]" size 24 color "#7a4b2a"
                            button:
                                background "tablebutton1b.png"
                                xsize 180
                                ysize 50
                                text "[get_sell_text(worker)]" size 24 color "#7a4b2a" xalign 0.0 hover_color "#6b6528"  # Align text to the left
                                action Function(sell_worker, worker)

            # (Removed duplicate close button)

screen map_screen():
    zorder 2
    modal True
    add map_bg
    # Draw full-width decorative PNG centered behind the menu, without clipping
    add context_menu_bg xalign 0.5 yalign 0.5
    frame:
        xalign 1.0
        yalign 0.5
        xsize 320
        ysize 1.0
        background None
        vbox:
            xalign 1.0
            yalign 0.5
            xoffset -5
            spacing 10
            textbutton "Buy Servants":
                action Show("buy_servants_table")
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Recruit Workers":
                action If(can_recruit_today,
                    Function(launch_recruitment_via_label),
                    Show("error_popup", message="You can only recruit once per day"))
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Buy Buildings":
                action Show("buy_buildings")
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Visit Shops":
                action Show("shop_selection")
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Back":
                action [Hide("map_screen"), Show("tavern")]
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"

    # Money and Date positioned over context menu area
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        ysize 80
        # Money display with icon-style $ symbol
        hbox:
            spacing 5
            text "$" color "#3c1f14" size 22 bold True yalign 0.5
            text "[int(money)]" color "#3c1f14" size 28 yalign 0.5
        # Calendar display with icon
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]  # Map day 1-28 to 7-day week
            $ month_name = month_names[store.current_month]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color "#3c1f14" size 21 yalign 0.5

# --- screen daily_report() ---

label daily_report_screen:
    call screen daily_report
    return

screen daily_report():
    tag menu
    modal True
    zorder 50
    
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
            idle Transform("gui/button/return_idle.png", zoom=0.5)
            hover Transform("gui/button/return_hover.png", zoom=0.5)
            action [Hide("daily_report"), Jump("day_transition")]
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
            $ month_name = month_names[store.current_month]
            label "Daily Report: [day_name], [store.current_day] [month_name] {size=21}[store.current_year]{/size}" xalign 0.5 style "header_style" text_size 28
            if not daily_report:
                text "No significant events occurred today." size 24 xalign 0.5 color "#ffffff"
            else:
                # Filtro por edificio
                hbox:
                    spacing 20
                    xalign 0.5
                    yoffset -30  # Lowered filter 10px more
                    
                    text "Filter by Building:" size 20 color "#ffffff" yalign 0.5
                    
                    # Crear lista de edificios únicos
                    python:
                        unique_buildings = ["All Buildings"]
                        for report in daily_report:
                            building_name = report.get('building', 'Unknown Building')
                            # Obtener el nombre de display del edificio
                            building = available_buildings.get(building_name, {})
                            btype_id = building.get("type")
                            type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                            parts = building_name.split('_')
                            default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                            building_display_name = store.custom_names.get(building_name, default_name)
                            full_display_name = f"{type_name}: {building_display_name}"
                            
                            if full_display_name not in unique_buildings:
                                unique_buildings.append(full_display_name)
                    
                    # Menú desplegable para seleccionar edificio
                    frame:
                        background "#1a1a1acc"
                        padding (10, 5)
                        
                        button:
                            xsize 300
                            ysize 40
                            background "#333333"
                            hover_background "#555555"
                            
                            text "[building_filter]" size 18 color "#ffffff" xalign 0.5 yalign 0.5
                            
                            action Show("building_filter_menu", buildings=unique_buildings)

                # Aplicar filtro
                python:
                    if building_filter == "All Buildings":
                        filtered_reports = daily_report
                    else:
                        filtered_reports = []
                        for report in daily_report:
                            building_name = report.get('building', 'Unknown Building')
                            # Obtener el nombre de display del edificio
                            building = available_buildings.get(building_name, {})
                            btype_id = building.get("type")
                            type_name = "Unassigned" if btype_id is None else next((bt["name"] for bt in building_types_json.get("building_types", []) if bt["id"] == btype_id), btype_id)
                            parts = building_name.split('_')
                            default_name = f"Building {parts[1]}" if len(parts) > 1 else building_name
                            building_display_name = store.custom_names.get(building_name, default_name)
                            full_display_name = f"{type_name}: {building_display_name}"
                            
                            if full_display_name == building_filter:
                                filtered_reports.append(report)

                if not filtered_reports:
                    text "No events found for the selected building." size 20 xalign 0.5 color "#ffffff"
                else:
                    vbox:
                        spacing 1
                        xoffset 5 # shift entire table (headers + rows) 5px to the right
                        yoffset -60  # Lowered table 30px from filter
                        # Header row (fixed, outside viewport)
                        hbox:
                            spacing 0 # Remove default spacing, use manual spacing
                            xsize 1650 # Fit within viewport to avoid scrollbar overlap
                            yalign 0.5
                            button:
                                background "tablebutton.png"
                                xsize 80 # Number column
                                ysize 46
                                # Slight right shift for header '#'
                                text "#" size 18 xalign 0.5 xoffset 12 yalign 0.5 yoffset -8
                            null width 10 # Reduced spacing after # column
                            button:
                                background "tablebutton2.png"
                                xsize 280 # Restored larger width
                                ysize 46
                                text "Building" size 18
                            null width 25 # Standard spacing after Building (+5)
                            button:
                                background "tablebutton2.png"
                                xsize 280 # Restored larger width
                                ysize 46
                                text "Profession" size 18
                            null width 25 # Standard spacing after Profession (+5)
                            button:
                                background "tablebutton2.png"
                                xsize 280 # Restored larger width
                                ysize 46
                                text "Worker" size 18
                            null width 25 # Standard spacing after Worker (+5)
                            button:
                                background "tablebutton2.png"
                                xsize 280 # Restored larger width
                                ysize 46
                                text "Story" size 18
                            null width 25 # Standard spacing after Story (+5)
                            button:
                                background "tablebutton2.png"
                                xsize 360 # Narrower result column to keep content inside viewport
                                ysize 46
                                text "Result (Click for Details)" size 18

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
                                for i, report in enumerate(filtered_reports, 1):
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
                                        if result_text == "Unhandled":
                                            color_code = "#808080"
                                        elif result_text in ["Critical Success", "Success", "Rest"]:
                                            color_code = "#006600"  # Verde más oscuro y menos saturado
                                        elif result_text == "Mediocre":
                                            color_code = "#666600"  # Amarillo más oscuro y menos saturado
                                        elif result_text == "Failure":
                                            color_code = "#660000"  # Rojo más oscuro y menos saturado
                                        elif result_text == "Refused":
                                            color_code = "#663333"  # Rojo claro más oscuro y menos saturado
                                        else:
                                            color_code = "#ffffff"
                                    # --- End Pre-calculation ---

                                    hbox:
                                        spacing 0 # Remove default spacing, use manual spacing
                                        xsize 1650 # Match header width to avoid overlap
                                        yalign 0.5
                                        # Number column
                                        button:
                                            background "tablebutton.png"
                                            xsize 80 # Number column
                                            ysize 46
                                            # Keep numbers centered horizontally; remove extra xoffset so only header moves
                                            text "[i]" size 18 xalign 0.5 yalign 0.5 yoffset -8
                                        null width 10 # Reduced spacing after # column
                                        # Building column (type: name)
                                        button:
                                            background "tablebutton.png"
                                            xsize 280 # Restored larger width
                                            ysize 46
                                            text "[type_name]: [building_display_name]" size 18 # Use pre-calculated display name
                                        null width 25 # Standard spacing after Building (+5)
                                        # Profession column
                                        button:
                                            background "tablebutton.png"
                                            xsize 280 # Restored larger width
                                            ysize 46
                                            text "[report.get('profession', 'N/A')]" size 18
                                        null width 25 # Standard spacing after Profession (+5)
                                        # Worker column
                                        button:
                                            background "tablebutton.png"
                                            xsize 280 # Restored larger width
                                            ysize 46
                                            text "[report.get('worker_name', 'Unknown')]" size 18 hover_color "#6b6528"
                                            action worker_button_action # Use the pre-calculated action
                                        null width 25 # Standard spacing after Worker (+5)
                                        # Story Name column
                                        button:
                                            background "tablebutton.png"
                                            xsize 280 # Restored larger width
                                            ysize 46
                                            text "[report.get('event_data', {}).get('report', 'N/A')]" size 18
                                        null width 25 # Standard spacing after Story (+5)
                                        # Combined Result & Earnings column (clickable)
                                        button:
                                            background "tablebutton.png"
                                            xsize 360 # Narrower result column to keep content inside viewport
                                            ysize 46
                                            action Show("report_details", report=report)
                                            text "{color=[color_code]}[result_text] ([earnings_text]){/color}" size 18 # Use pre-calculated text/color


# Pantalla del menú desplegable para seleccionar edificio
screen building_filter_menu(buildings):
    modal True
    zorder 100
    
    # Cerrar el menú si se hace clic fuera de él
    button:
        xfill True
        yfill True
        background None
        action Hide("building_filter_menu")
    
    frame:
        xalign 0.5
        yalign 0.3
        background "#1a1a1acc"
        padding (10, 10)
        
        vbox:
            spacing 5
            
            text "Select Building:" size 20 color "#ffffff" xalign 0.5
            
            null height 10
            
            for building in buildings:
                textbutton "[building]":
                    xsize 300
                    ysize 30
                    background "#333333"
                    hover_background "#555555"
                    text_size 16
                    text_color "#ffffff"
                    text_hover_color "#6b6528"
                    action [
                        SetVariable("building_filter", building),
                        Hide("building_filter_menu")
                    ]
            
            null height 10
            
            textbutton "Cancel":
                xsize 300
                ysize 30
                background "#666666"
                hover_background "#888888"
                text_size 16
                text_color "#ffffff"
                text_hover_color "#6b6528"
                action Hide("building_filter_menu")

screen report_details(report):
    zorder 100
    modal True
    add Solid("#000000")
    
    python:
        worker = report.get("worker", {})
        event = report.get("event_data", {})
        outcome = report.get("result", "").lower().replace(" ", "_")
        skill_name = report.get("used_skill", None)
        selected_media = get_event_image(worker, event, outcome, skill_name)
        event_description = report.get("description", "No description available.")
        loot_items = report.get("loot", [])
        
        # Find current report index and calculate navigation
        current_report_index = 0
        for i, r in enumerate(daily_report):
            if r == report:
                current_report_index = i
                break
        
        can_go_previous = current_report_index > 0
        can_go_next = current_report_index < len(daily_report) - 1
        story_number = current_report_index + 1
        total_stories = len(daily_report)
    
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
                text "Story [story_number] of [total_stories]" size 20 color "#ffffff" xalign 0.5 bold True
                
                frame:
                    background Solid("#1a1a1acc")
                    xsize 300
                    ysize 600
                    padding (10, 10)
                    xalign 0.5
                    viewport:
                        vbox:
                            text "[event_description]" size 18 color "#ffffff" xalign 0.0 text_align 0.0 substitute True
                            if loot_items:
                                text ""  # Blank line for spacing
                                text "Loot Obtained:" size 18 color "#ff69b4" bold True
                                for item in loot_items:
                                    # If 'item' is a string (the id), look it up in items_json
                                    if isinstance(item, str):
                                        $ item_data = next((i for i in items_json["items"] if i["id"] == item), {"display_name": item})
                                    else:
                                        $ item_data = item  # Assume it's already a dictionary
                                    $ display_name = item_data.get("display_name", item_data.get("id", "Unknown Item"))
                                    text "{color=#aaaaaa}[display_name]{/color}" size 16
                # Previous button (disabled if on first story)
                if can_go_previous:
                    button:
                        xalign 0.0
                        xsize 290
                        ysize 50
                        background None
                        text "Previous" color "#ffffff" hover_color "#6b6528" xalign 0.0
                        action [
                            SetVariable("current_report_index", current_report_index - 1),
                            Show("report_details", report=daily_report[current_report_index - 1])
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
                        text "Next" color "#ffffff" hover_color "#6b6528" xalign 0.0
                        action [
                            SetVariable("current_report_index", current_report_index + 1),
                            Show("report_details", report=daily_report[current_report_index + 1])
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
                    action Hide("report_details")

screen tavern():
    $ renpy.log("Tavern screen displayed")
    # Only clear persistent flags if we're actually in tavern context
    # (not if we're being shown as fallback from another screen)
    if not getattr(persistent, "_context_restored", False):
        $ persistent._slot_to_apply = None
        $ persistent.loaded_via_save = False
        $ renpy.save_persistent()
    else:
        $ persistent._context_restored = False
        $ renpy.save_persistent()
    # Ensure calendar is initialized
    # $ initialize_calendar()
    
    # Auto-trigger objective 4 dialogue - SIMPLE VERSION
    $ tutorial_act = getattr(store, 'tutorial_active', False)
    $ obj4_shown = getattr(store, 'objective_4_dialogue_shown', False)
    $ renpy.log(f"DEBUG: tavern screen check - tutorial_active={tutorial_act}, money=${money}, obj4_shown={obj4_shown}")
    
    if tutorial_act and money >= 6000 and not obj4_shown:
        timer 0.1 action [
            SetVariable("objective_4_complete", True),
            SetVariable("current_objective", 5), 
            SetVariable("objective_4_dialogue_shown", True),
            Function(renpy.log, "DEBUG: Timer triggering objective 4 dialogue"),
            Hide("tavern"),
            Jump("show_objective_4_dialogue")
        ]
    
    zorder 1
    add tavern_bg
    # Draw decorative PNG centered behind the menu so it doesn't get clipped
    add context_menu_bg xalign 0.5 yalign 0.5
    frame:
        xalign 1.0
        yalign 0.5
        xsize 320
        ysize 1.0
        background None
        vbox:
            xalign 1.0
            yalign 0.5
            xoffset -5
            spacing 10
            textbutton "Journal":
                action Show("journal_panel")
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Explore":
                action [
                    Function(renpy.log, "Explore button clicked"),
                    Hide("tavern"),
                    Show("map_screen")
                ]
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Manage Buildings":
                action [
                    Function(renpy.log, "Manage Buildings button clicked"),
                    Show("Building_select_global")
                ]
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Workers":
                action [
                    Function(renpy.log, "Workers button clicked"),
                    Hide("tavern"),
                    Show("workers")
                ]
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"
            textbutton "Next Day":
                action [
                    Function(renpy.log, "Next Day button clicked"),
                    Hide("tavern"),
                    Jump("next_day")
                ]
                xsize 300
                text_size 42
                text_color "#3c1f14"
                text_hover_color "#6b6528"


    # Money and Date positioned over context menu area
    vbox:
        xpos 1615
        ypos 70
        spacing 8
        ysize 80
        # Money display with icon-style $ symbol
        hbox:
            spacing 5
            text "$" color "#3c1f14" size 22 bold True yalign 0.5
            text "[int(money)]" color "#3c1f14" size 28 yalign 0.5
        # Calendar display with icon
        hbox:
            spacing 5
            add "images/calendar.png" zoom 0.7 yalign 0.5
            $ day_name = day_names[(store.current_day - 1) % 7]  # Map day 1-28 to 7-day week
            $ month_name = month_names[store.current_month]
            text "[day_name], [store.current_day] [month_name] [store.current_year]" color "#3c1f14" size 21 yalign 0.5

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
    size 18

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
    $ file_text = "% s\n  %s" % (FileTime(number, empty="Empty Slot"), FileSaveName(number))
    add FileScreenshot(number) xpos -1 ypos 0
    text file_text xpos 11 ypos -20 size 15 color "#000000"

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
        
        text "Gallery" size 60 color "#3c1f14" xalign 0.5
        text "Coming Soon..." size 40 color "#887441" xalign 0.5
        
        textbutton "Return" action Return() xalign 0.5 text_size 30

# Pantalla del menú desplegable para seleccionar edificio en Manage Workers
screen worker_building_filter_menu(buildings):
    modal True
    zorder 100
    
    # Cerrar el menú si se hace clic fuera de él
    button:
        xfill True
        yfill True
        background None
        action Hide("worker_building_filter_menu")
    
    frame:
        xalign 0.5
        yalign 0.3
        background "#1a1a1acc"
        padding (10, 10)
        
        vbox:
            spacing 5
            
            text "Select Building:" size 20 color "#ffffff" xalign 0.5
            
            null height 10
            
            for building in buildings:
                textbutton "[building]":
                    xsize 300
                    ysize 30
                    background "#333333"
                    hover_background "#555555"
                    text_size 16
                    text_color "#ffffff"
                    text_hover_color "#6b6528"
                    action [
                        SetVariable("worker_building_filter", building),
                        Hide("worker_building_filter_menu")
                    ]
            
            null height 10
            
            textbutton "Cancel":
                xsize 300
                ysize 30
                background "#666666"
                hover_background "#888888"
                text_size 16
                text_color "#ffffff"
                text_hover_color "#6b6528"
                action Hide("worker_building_filter_menu")
