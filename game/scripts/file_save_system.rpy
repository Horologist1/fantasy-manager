################################################################################
### FILE SAVE/LOAD SYSTEM
### Sistema especial para guardar/cargar desde archivos externos
################################################################################

# Custom style for file save/load buttons
style file_button is button:
    background "images/tablebutton.png"
    hover_background "#d4a574"  # Color del frame de save al hacer hover
    selected_background "images/tablebutton.png"
    insensitive_background "images/tablebutton.png"
    xalign 0.5
    yalign 0.5

style file_button_text is button_text:
    xalign 0.5
    yalign 0.5
    text_align 0.5
    color "#5d4037"      # Marrón oscuro para el texto normal
    hover_color "#314311"  # Verde oscuro usado en el juego
    selected_color "#5d4037"
    insensitive_color "#888888"

# Custom style for file dialog frames
style file_dialog_frame is frame:
    background "#d4a574"  # Color del frame de save al hacer hover
    padding (20, 15)

style file_dialog_text is text:
    color "#5d4037"      # Marrón oscuro
    hover_color "#314311"  # Verde oscuro

# Custom styles for interaction screens
style interaction_frame is frame:
    background "#d4a574"  # Color beige
    padding (20, 20)

style interaction_text is text:
    color "#5d4037"      # Marrón oscuro
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
    color "#5d4037"      # Marrón oscuro
    hover_color "#314311"  # Verde oscuro

init python:
    import json
    import os
    import datetime
    
    def export_save_to_file(filename=None):
        """Export current game state to an external JSON file"""
        try:
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fantasy_manager_save_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Build complete snapshot
            snapshot = _build_snapshot()
            
            # Add metadata
            export_data = {
                "metadata": {
                    "export_date": datetime.datetime.now().isoformat(),
                    "game_version": "Fantasy Manager v0.7",
                    "save_type": "external_file"
                },
                "game_state": snapshot
            }
            
            # Save to file in game/saves directory
            saves_dir = os.path.join(config.basedir, "game", "saves")
            filepath = os.path.join(saves_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            renpy.log(f"EXPORT: Game saved to {filepath}")
            renpy.notify(f"Game exported to: {filename}")
            return True, filepath
            
        except Exception as e:
            error_msg = f"Export error: {str(e)}"
            renpy.log(f"EXPORT ERROR: {error_msg}")
            renpy.notify(f"Export failed: {str(e)}")
            return False, error_msg
    
    def import_save_from_file(filename):
        """Import game state from an external JSON file"""
        try:
            renpy.log(f"IMPORT: Starting import of file: {filename}")
            # Construct full path
            saves_dir = os.path.join(config.basedir, "game", "saves")
            filepath = os.path.join(saves_dir, filename)
            renpy.log(f"IMPORT: Full path: {filepath}")
            
            if not os.path.exists(filepath):
                error_msg = f"File not found: {filename}"
                renpy.log(f"IMPORT ERROR: {error_msg}")
                renpy.notify(error_msg)
                return False, error_msg
            
            # Load and parse JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate structure
            if "game_state" not in import_data:
                error_msg = "Invalid save file format"
                renpy.log(f"IMPORT ERROR: {error_msg}")
                renpy.notify(error_msg)
                return False, error_msg
            
            # Extract game state
            snapshot = import_data["game_state"]
            
            # Apply the snapshot
            _apply_snapshot(snapshot)
            
            # Log metadata if available
            if "metadata" in import_data:
                metadata = import_data["metadata"]
                renpy.log(f"IMPORT: Loaded save from {metadata.get('export_date', 'unknown date')}")
            
            renpy.log(f"IMPORT: Game loaded from {filepath}")
            renpy.notify(f"Game imported from: {filename}")
            
            # Set flags to indicate successful import
            store.is_new_game = False
            
            return True, "Import successful"
            
        except Exception as e:
            error_msg = f"Import error: {str(e)}"
            renpy.log(f"IMPORT ERROR: {error_msg}")
            renpy.notify(f"Import failed: {str(e)}")
            return False, error_msg
    
    def list_save_files():
        """List all .json save files in the game directory"""
        try:
            save_files = []
            saves_dir = os.path.join(config.basedir, "game", "saves")
            
            for filename in os.listdir(saves_dir):
                # Only include JSON files that are game saves (exclude system files)
                if (filename.endswith('.json') and 
                    filename != 'navigation.json' and
                    not filename.startswith('.')):  # Exclude hidden files
                    filepath = os.path.join(saves_dir, filename)
                    # Get file modification time
                    mtime = os.path.getmtime(filepath)
                    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    save_files.append({
                        'filename': filename,
                        'modified': mtime_str,
                        'size': os.path.getsize(filepath)
                    })
            
            # Sort by modification time (newest first)
            save_files.sort(key=lambda x: x['modified'], reverse=True)
            return save_files
            
        except Exception as e:
            renpy.log(f"LIST FILES ERROR: {str(e)}")
            return []

# Simplified dialogs for Save/Load screen integration
screen file_save_dialog():
    tag menu
    modal True
    zorder 110
    
    add "#000000aa"
    
    frame:
        style "file_dialog_frame"
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 400
        
        vbox:
            spacing 20
            xalign 0.5
            yalign 0.5
            
            text "Export Game to File" style "file_dialog_text" size 32 xalign 0.5
            
            text "Choose export option:" style "file_dialog_text" size 22 xalign 0.5
            
            vbox:
                spacing 15
                xalign 0.5
                
                textbutton "Quick Export (Auto Name)":
                    style "file_button"
                    text_style "file_button_text"
                    xsize 400
                    text_size 22
                    action [
                        Function(export_save_to_file),
                        Hide("file_save_dialog")
                    ]
                
                textbutton "Export with Custom Name":
                    style "file_button"
                    text_style "file_button_text"
                    xsize 400
                    text_size 22
                    action [
                        Hide("file_save_dialog"),
                        Show("export_name_input")
                    ]
            
            textbutton "Cancel":
                style "file_button"
                text_style "file_button_text"
                xsize 200
                text_size 20
                action [
                    Hide("file_save_dialog"),
                    Return()
                ]

screen file_load_dialog():
    tag menu
    modal True
    zorder 110
    
    add "#000000aa"
    
    frame:
        style "file_dialog_frame"
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 400
        
        vbox:
            spacing 20
            xalign 0.5
            yalign 0.5
            
            text "Import Game from File" style "file_dialog_text" size 32 xalign 0.5
            
            text "Select a file to import:" style "file_dialog_text" size 22 xalign 0.5
            
            vbox:
                spacing 15
                xalign 0.5
                
                textbutton "Browse Available Files":
                    style "file_button"
                    text_style "file_button_text"
                    xsize 400
                    text_size 22
                    action [
                        Hide("file_load_dialog"),
                        Show("file_browser_simple")
                    ]
                
                text "Save files location: /game/saves/" style "file_dialog_text" size 18 xalign 0.5
            
            textbutton "Cancel":
                style "file_button"
                text_style "file_button_text"
                xsize 200
                text_size 20
                action [
                    Hide("file_load_dialog"),
                    Return()
                ]

# Screen for custom export filename input
screen export_name_input():
    tag menu
    modal True
    zorder 110
    
    add "#000000aa"
    
    frame:
        style "file_dialog_frame"
        xalign 0.5
        yalign 0.5
        xsize 600
        ysize 300
        
        vbox:
            spacing 20
            xalign 0.5
            yalign 0.5
            
            text "Export Filename" style "file_dialog_text" size 28 xalign 0.5
            
            text "Enter filename (without .json extension):" style "file_dialog_text" size 22 xalign 0.5
            
            python:
                if not hasattr(store, 'export_filename'):
                    store.export_filename = ""
            
            input:
                value VariableInputValue("export_filename")
                length 50
                xsize 500
            
            hbox:
                spacing 20
                xalign 0.5
                
                textbutton "Export":
                    style "file_button"
                    text_style "file_button_text"
                    xsize 150
                    text_size 20
                    action [
                        Function(export_save_to_file, export_filename),
                        Hide("export_name_input")
                    ]
                
                textbutton "Cancel":
                    style "file_button"
                    text_style "file_button_text"
                    xsize 150
                    text_size 20
                    action Hide("export_name_input")

# Simplified file browser for load screen
screen file_browser_simple():
    tag menu
    modal True
    zorder 110
    
    add "#000000aa"
    
    default selected_file = None
    
    frame:
        style "file_dialog_frame"
        xalign 0.5
        yalign 0.5
        xsize 700
        ysize 500
        
        vbox:
            spacing 15
            xfill True
            yfill True
            
            text "Select File to Import" style "file_dialog_text" size 28 xalign 0.5
            
            if selected_file:
                text "Selected: [selected_file]" style "file_dialog_text" size 20 color "#314311" xalign 0.5
            else:
                text "Click on a file to select it" style "file_dialog_text" size 20 xalign 0.5
            
            python:
                save_files = list_save_files()
            
            if not save_files:
                text "No save files found." style "file_dialog_text" size 22 xalign 0.5
            else:
                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    draggable True
                    ysize 300
                    xsize 650
                    vbox:
                        spacing 5
                        xfill True
                        
                        for save_file in save_files:
                            frame:
                                style "file_dialog_frame"
                                xfill True
                                ysize 60
                                padding (15, 10)
                                
                                button:
                                    xfill True
                                    yfill True
                                    background "#00000000"
                                    hover_background "#b8956a"  # Un tono más oscuro del dorado para hover
                                    action SetScreenVariable("selected_file", save_file['filename'])
                                    
                                    vbox:
                                        spacing 3
                                        xfill True
                                        yalign 0.5
                                        
                                        text save_file['filename'] style "file_dialog_text" size 20
                                        text "Modified: [save_file['modified']] - Size: [save_file['size']] bytes" style "file_dialog_text" size 16
            
            hbox:
                spacing 20
                xalign 0.5
                
                textbutton "Cancel":
                    style "file_button"
                    text_style "file_button_text"
                    xsize 150
                    text_size 20
                    action [
                        Hide("file_browser_simple"),
                        Show("file_load_dialog")
                    ]
                
                textbutton "Load File":
                    style "file_button"
                    text_style "file_button_text"
                    xsize 150
                    text_size 20
                    action [
                        Function(import_save_from_file, selected_file),
                        Hide("file_browser_simple"),
                        Hide("file_load_dialog"),
                        Show("tavern")
                    ]

