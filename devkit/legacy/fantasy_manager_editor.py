#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fantasy Manager Editor v3.0
Editor completo para eventos, interacciones, items, workers y más
"""

import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import copy

class FantasyManagerEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Fantasy Manager Editor v3.0")
        self.root.geometry("1400x900")
        
        # Ruta base del juego
        self.game_path = None
        self.data_path = None
        
        # Datos cargados
        self.current_data = None
        self.current_file_type = None
        self.current_file_path = None
        
        # Crear interfaz
        self.create_ui()
        
        # Intentar detectar ruta del juego automáticamente
        self.auto_detect_game_path()
    
    def auto_detect_game_path(self):
        """Intenta detectar automáticamente la ruta del juego"""
        current_dir = Path(__file__).parent.parent
        if (current_dir / "game" / "data").exists():
            self.set_game_path(str(current_dir))
    
    def set_game_path(self, path):
        """Establece la ruta del juego"""
        self.game_path = path
        self.data_path = Path(path) / "game" / "data"
        self.update_file_tree()
    
    def create_ui(self):
        """Crea la interfaz de usuario"""
        # Panel principal
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel izquierdo: Navegación de archivos
        left_panel = ttk.Frame(main_panel)
        main_panel.add(left_panel, weight=1)
        
        # Botón para seleccionar ruta del juego
        path_frame = ttk.Frame(left_panel)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(path_frame, text="Seleccionar Carpeta del Juego", 
                  command=self.select_game_path).pack(side=tk.LEFT, padx=5)
        self.path_label = ttk.Label(path_frame, text="Ruta no seleccionada", 
                                   foreground="gray")
        self.path_label.pack(side=tk.LEFT, padx=5)
        
        # Treeview para archivos
        tree_frame = ttk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(tree_frame, text="Archivos de Datos:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.file_tree = ttk.Treeview(tree_frame)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_tree = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.configure(yscrollcommand=scrollbar_tree.set)
        
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)
        
        # Panel derecho: Editor
        right_panel = ttk.Frame(main_panel)
        main_panel.add(right_panel, weight=3)
        
        # Barra de herramientas
        toolbar = ttk.Frame(right_panel)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="💾 Guardar", command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Recargar", command=self.reload_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="➕ Nuevo Item", command=self.new_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✓ Validar JSON", command=self.validate_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 Buscar", command=self.search_text).pack(side=tk.LEFT, padx=2)
        
        # Editor de texto JSON
        editor_frame = ttk.Frame(right_panel)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(editor_frame, text="Editor JSON:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.NONE, 
                                                font=("Consolas", 10))
        self.editor.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def select_game_path(self):
        """Selecciona la carpeta del juego"""
        path = filedialog.askdirectory(title="Seleccionar carpeta del juego (fantasy-manager)")
        if path:
            if not (Path(path) / "game" / "data").exists():
                messagebox.showerror("Error", 
                    "La carpeta seleccionada no contiene 'game/data'.\n"
                    "Por favor selecciona la carpeta raíz del proyecto (fantasy-manager).")
                return
            self.set_game_path(path)
            self.path_label.config(text=path, foreground="black")
    
    def update_file_tree(self):
        """Actualiza el árbol de archivos"""
        self.file_tree.delete(*self.file_tree.get_children())
        
        if not self.data_path or not self.data_path.exists():
            return
        
        # Estructura de archivos a mostrar
        file_structure = {
            "Buildings": ["buildings/building_types.json"],
            "Events": [
                "events/events_building.json",
                "events/events_common.json",
                "events/events_seasonal.json",
                "events/events_shops.json",
                "events/recruit/events_recruit.json",
            ],
            "Interactions": [
                "interactions/interactions_main.json",
                "interactions/interactions_special.json",
                "interactions/interactions_structured.json",
            ],
            "Items": ["items/items.json"],
            "Workers": [
                "workers/workers_sfw_unique.json",
                "workers/workers_sfw_other.json",
                "workers/workers_nsfw_unique.json",
                "workers/workers_nsfw_other.json",
            ],
            "Traits": ["traits.json"],
        }
        
        for category, files in file_structure.items():
            category_node = self.file_tree.insert("", tk.END, text=category, 
                                                  values=("category",))
            for file_path in files:
                full_path = self.data_path / file_path
                if full_path.exists():
                    self.file_tree.insert(category_node, tk.END, 
                                        text=Path(file_path).name,
                                        values=("file", str(full_path)))
    
    def on_file_select(self, event):
        """Maneja la selección de un archivo"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item = self.file_tree.item(selection[0])
        values = item.get("values", [])
        
        if len(values) > 1 and values[0] == "file":
            file_path = values[1]
            self.load_file(file_path)
    
    def load_file(self, file_path):
        """Carga un archivo JSON"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.current_data = json.load(f)
            
            self.current_file_path = file_path
            self.current_file_type = Path(file_path).name
            
            # Mostrar JSON formateado
            json_str = json.dumps(self.current_data, indent=2, ensure_ascii=False)
            self.editor.delete(1.0, tk.END)
            self.editor.insert(1.0, json_str)
            
            self.status_bar.config(text=f"Cargado: {self.current_file_type}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar archivo:\n{str(e)}")
            self.status_bar.config(text=f"Error: {str(e)}")
    
    def save_file(self):
        """Guarda el archivo JSON actual"""
        if not self.current_file_path:
            messagebox.showwarning("Advertencia", "No hay archivo cargado")
            return
        
        try:
            # Parsear JSON del editor
            json_str = self.editor.get(1.0, tk.END)
            data = json.loads(json_str)
            
            # Guardar archivo
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.current_data = data
            self.status_bar.config(text=f"Guardado: {self.current_file_type}")
            messagebox.showinfo("Éxito", "Archivo guardado correctamente")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Error de JSON", 
                f"El JSON tiene errores de sintaxis:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar:\n{str(e)}")
    
    def reload_file(self):
        """Recarga el archivo actual"""
        if self.current_file_path:
            self.load_file(self.current_file_path)
    
    def new_item(self):
        """Crea un nuevo item según el tipo de archivo"""
        if not self.current_file_path:
            messagebox.showwarning("Advertencia", "No hay archivo cargado")
            return
        
        file_name = Path(self.current_file_path).name
        
        # Determinar tipo de template según el archivo
        if "items.json" in file_name:
            template = self.get_item_template()
        elif "events" in file_name:
            template = self.get_event_template()
        elif "interactions" in file_name:
            template = self.get_interaction_template()
        elif "workers" in file_name:
            template = self.get_worker_template()
        elif "traits.json" in file_name:
            template = self.get_trait_template()
        elif "building_types.json" in file_name:
            messagebox.showinfo("Info", "Para agregar edificios, edita el JSON manualmente")
            return
        else:
            messagebox.showwarning("Advertencia", "Tipo de archivo no reconocido")
            return
        
        # Agregar template al JSON
        try:
            json_str = self.editor.get(1.0, tk.END)
            data = json.loads(json_str)
            
            if isinstance(data, list):
                data.append(template)
            elif isinstance(data, dict):
                if "items" in data:
                    data["items"].append(template)
                elif "building_types" in data:
                    messagebox.showinfo("Info", "Para agregar edificios, edita el JSON manualmente")
                    return
                else:
                    # Es un diccionario de eventos (events_seasonal.json)
                    template_id = template.get("id", "new_item")
                    data[template_id] = template
            
            # Actualizar editor
            new_json_str = json.dumps(data, indent=2, ensure_ascii=False)
            self.editor.delete(1.0, tk.END)
            self.editor.insert(1.0, new_json_str)
            
            self.status_bar.config(text="Nuevo item agregado - Recuerda guardar")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar item:\n{str(e)}")
    
    def delete_item(self):
        """Elimina el item seleccionado (requiere selección manual en el JSON)"""
        messagebox.showinfo("Info", 
            "Para eliminar un item:\n"
            "1. Selecciona el objeto en el editor JSON\n"
            "2. Elimínalo manualmente\n"
            "3. Guarda el archivo")
    
    def validate_json(self):
        """Valida el JSON actual"""
        try:
            json_str = self.editor.get(1.0, tk.END)
            json.loads(json_str)
            messagebox.showinfo("Validación", "✓ JSON válido")
            self.status_bar.config(text="JSON válido")
        except json.JSONDecodeError as e:
            messagebox.showerror("Error de JSON", 
                f"El JSON tiene errores:\n\nLínea {e.lineno}, Columna {e.colno}:\n{str(e)}")
            # Intentar resaltar el error
            try:
                line_num = e.lineno
                self.editor.mark_set(tk.INSERT, f"{line_num}.0")
                self.editor.see(tk.INSERT)
            except:
                pass
    
    def search_text(self):
        """Abre diálogo de búsqueda"""
        search_window = tk.Toplevel(self.root)
        search_window.title("Buscar")
        search_window.geometry("400x100")
        
        ttk.Label(search_window, text="Buscar:").pack(pady=5)
        search_entry = ttk.Entry(search_window, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def do_search():
            query = search_entry.get()
            if query:
                content = self.editor.get(1.0, tk.END)
                if query in content:
                    # Encontrar primera ocurrencia
                    start = content.find(query)
                    line = content[:start].count('\n') + 1
                    col = start - content.rfind('\n', 0, start) - 1
                    self.editor.mark_set(tk.INSERT, f"{line}.{col}")
                    self.editor.see(tk.INSERT)
                    self.editor.tag_add(tk.SEL, f"{line}.{col}", f"{line}.{col + len(query)}")
                    search_window.destroy()
                else:
                    messagebox.showinfo("Búsqueda", "Texto no encontrado")
        
        ttk.Button(search_window, text="Buscar", command=do_search).pack(pady=5)
        search_entry.bind("<Return>", lambda e: do_search())
    
    def get_item_template(self):
        """Retorna un template para un nuevo item"""
        return {
            "id": "new_item",
            "name": "New Item",
            "display_name": "New Item",
            "type": "consumable",
            "effect": {
                "health": 10
            },
            "description": "A new item that restores health. (+10 Health)",
            "price": 100,
            "weight": 1
        }
    
    def get_event_template(self):
        """Retorna un template para un nuevo evento"""
        return {
            "id": "new_event",
            "description": "A new event description. The weight of decision hangs heavy in the air, and you sense that the choices made here will echo through the days to come",
            "weight": 3,
            "limited": False,
            "cooldown_days": 7,
            "worker_selection": "none",
            "building_type": [],
            "background_image": "event_bg",
            "success_image": "generic_success",
            "failure_image": "generic_failure",
            "choices": [
                {
                    "option": "Choice 1 (Risk/Potential)",
                    "condition": "building_skill",
                    "message_success": "Success message ({actual_money}, {actual_reputation} reputation).",
                    "message_failure": "Failure message ({actual_money}, {actual_reputation} reputation).",
                    "effect": {
                        "success": {
                            "money": 100,
                            "reputation": 5
                        },
                        "failure": {
                            "money": -50,
                            "reputation": -5
                        }
                    }
                },
                {
                    "option": "Choice 2 (Simple)",
                    "message": "Result message ({actual_money}, {actual_reputation} reputation).",
                    "effect": {
                        "money": 0,
                        "reputation": 0
                    }
                }
            ],
            "nsfw": False
        }
    
    def get_interaction_template(self):
        """Retorna un template para una nueva interacción"""
        return {
            "id": "new_interaction",
            "name": "New Interaction",
            "description": "A new interaction",
            "cost_energy": 1,
            "effect": {
                "relationship": 5
            },
            "gender_filter": None,
            "worker_gender": "female",
            "categories": ["Friendship"],
            "image": "interaction_image",
            "nsfw": False,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {}
        }
    
    def get_worker_template(self):
        """Retorna un template para un nuevo worker"""
        return {
            "name": "NewWorker",
            "folder": "default",
            "cost": 1000,
            "nsfw": False,
            "unique": False,
            "encounter_only": False,
            "monster": False,
            "procedural": False,
            "skills": {
                "Sex": 5, "Anal": 5, "BDSM": 5, "Hand": 5, "Oral": 5,
                "Homo": 5, "Special": 5, "Group": 5, "Extreme": 5,
                "Striptease": 5, "Combat": 5, "Clever": 5, "Charm": 5,
                "Service": 5, "Agility": 5, "Craft": 5
            },
            "names_list": "western_female",
            "traits": ["Human"],
            "description": "A new worker",
            "gender": "female",
            "comfort_desired": 5
        }
    
    def get_trait_template(self):
        """Retorna un template para un nuevo trait"""
        return {
            "name": "New Trait",
            "conflicts": [],
            "removes_traits": [],
            "modifiers": {},
            "description": "A new trait",
            "nsfw": False
        }


def main():
    root = tk.Tk()
    app = FantasyManagerEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()

