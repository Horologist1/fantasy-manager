# worker_interactions.rpy

init python:

    def load_interactions():
        """
        Load interactions from all JSON files in the interactions folder.
        No longer treats interactions_default.json as special - loads all files equally.
        """
        interactions = []
        loaded_files = False
        
        # Log all available files
        all_files = renpy.list_files()
        interaction_files = [f for f in all_files if f.startswith("data/interactions/") and f.endswith(".json")]
        renpy.log(f"Found interaction files: {interaction_files}")
        
        # Load all interaction files from the interactions folder
        for file in interaction_files:
            try:
                renpy.log(f"Attempting to load file: {file}")
                with renpy.file(file) as f:
                    file_content = f.read()
                    renpy.log(f"File content: {file_content[:200]}...")  # Log first 200 chars
                    file_interactions = json.load(renpy.file(file))
                    # Don't filter NSFW interactions - let player choose when NSFW is enabled
                    # When NSFW is disabled, only show SFW interactions
                    if persistent.nsfw_enabled:
                        # NSFW enabled: show all interactions (both NSFW and SFW)
                        filtered_interactions = file_interactions
                        interactions.extend(file_interactions)
                    else:
                        # NSFW disabled: only show SFW interactions
                        filtered_interactions = [inter for inter in file_interactions 
                                               if not inter.get("nsfw", False)]
                        interactions.extend(filtered_interactions)
                    loaded_files = True
                    renpy.log(f"Successfully loaded {len(filtered_interactions)} interactions from {file}")
                    # Log the names of loaded interactions
                    for inter in filtered_interactions:
                        renpy.log(f"Loaded interaction: {inter.get('name', 'Unknown')} for {inter.get('specific_workers', [])}")
            except Exception as e:
                renpy.log(f"Error loading interactions from {file}: {str(e)}")
        
        # If no files were successfully loaded, log an error
        if not loaded_files:
            renpy.log("Warning: No interaction files were successfully loaded!")
        else:
            renpy.log(f"Total interactions loaded: {len(interactions)}")
            
        # Always return whatever interactions were loaded, even if empty
        return interactions

    def filter_interactions_by_gender(interactions, gender):
        """Filter interactions by player gender."""
        return [interaction for interaction in interactions if interaction.get("gender_filter") is None or interaction["gender_filter"] == gender]

    def filter_interactions_by_worker_gender(interactions, worker):
        """Filter interactions by worker gender."""
        worker_gender = worker.get("gender", None)
        return [interaction for interaction in interactions if interaction.get("worker_gender") is None or interaction["worker_gender"] == worker_gender]

    def filter_interactions_by_stats(interactions, worker):
        """Filter interactions based on worker's stats."""
        filtered = []
        for interaction in interactions:
            # Check stat requirements
            stat_requirements = interaction.get("stat_requirements", {})
            meets_requirements = True
            
            for stat, required_value in stat_requirements.items():
                if worker.get(stat, 0) < required_value:
                    meets_requirements = False
                    break
            
            if meets_requirements:
                filtered.append(interaction)
        
        return filtered

    def filter_interactions_by_flags(interactions, worker):
        """Filter interactions based on required and excluded flags."""
        filtered = []
        for interaction in interactions:
            # Check required flags
            required_flags = interaction.get("required_flags", {})
            meets_requirements = True
            
            for flag_name, required_value in required_flags.items():
                current_value = worker.get("flags", {}).get(flag_name)
                if current_value != required_value:
                    meets_requirements = False
                    break
            
            # Check excluded flags
            excluded_flags = interaction.get("excluded_flags", {})
            excluded = False
            
            for flag_name, excluded_value in excluded_flags.items():
                current_value = worker.get("flags", {}).get(flag_name)
                if current_value == excluded_value:
                    excluded = True
                    break
            
            if meets_requirements and not excluded:
                filtered.append(interaction)
        
        return filtered

    def filter_interactions_by_items(interactions, worker):
        """Filter interactions based on required items in manager inventory."""
        filtered = []
        for interaction in interactions:
            # Check required items
            required_items = interaction.get("required_items", [])
            
            # If no items are required, include the interaction
            if not required_items:
                filtered.append(interaction)
                continue
            
            # Check if manager has all required items
            has_required_items = True
            for item_id in required_items:
                item_found = False
                for inventory_item in manager_inventory:
                    if inventory_item[0] == item_id and inventory_item[1] > 0:
                        item_found = True
                        break
                if not item_found:
                    has_required_items = False
                    break
            
            if has_required_items:
                filtered.append(interaction)
        
        return filtered

    def filter_interactions_by_usage_limits(interactions, worker):
        """Filter interactions based on usage limits."""
        filtered = []
        for interaction in interactions:
            # Check usage limits
            usage_limit = interaction.get("usage_limit")
            
            # If no usage limit is set, include the interaction
            if not usage_limit:
                filtered.append(interaction)
                continue
            
            # Get limit parameters
            flag_name = usage_limit.get("flag")
            max_uses = usage_limit.get("max_uses", 1)
            
            if not flag_name:
                # If no flag specified, include the interaction
                filtered.append(interaction)
                continue
            
            # Check current usage count
            current_uses = 0
            flag_value = worker.get("flags", {}).get(flag_name)
            
            if flag_value is not None:
                if isinstance(flag_value, dict) and "value" in flag_value:
                    current_uses = flag_value.get("value", 0)
                elif isinstance(flag_value, (int, float)):
                    current_uses = flag_value
            
            # Include interaction if under the limit
            if current_uses < max_uses:
                filtered.append(interaction)
        
        return filtered

    def filter_interactions_by_unlock_level(interactions, worker):
        """
        Filter interactions based on unlock level system.
        Each category has 4 levels:
        - Level 1: Always available
        - Level 2: Unlocked after 5 uses of level 1
        - Level 3: Unlocked after 5 uses of level 2
        - Level 4: Unlocked after 5 uses of level 3 (farmeable, optimal cost/benefit)
        """
        filtered = []
        if not worker.get("flags"):
            worker["flags"] = {}
        
        for interaction in interactions:
            interaction_level = interaction.get("interaction_level", 1)
            category = interaction.get("categories", [])
            
            # If no category or level specified, include it (for backwards compatibility)
            if not category or interaction_level is None:
                filtered.append(interaction)
                continue
            
            # Get the main category (first one)
            main_category = category[0] if category else "Other"
            
            # Build flag name for tracking uses in this category
            category_flag_base = f"{main_category.lower()}_uses"
            
            # Level 1 is always available
            if interaction_level == 1:
                filtered.append(interaction)
                continue
            
            # For levels 2, 3, and 4, check if previous level has been used enough
            required_uses = 5
            previous_level = interaction_level - 1
            
            # Check uses of previous level
            previous_level_flag = f"{category_flag_base}_level_{previous_level}"
            previous_uses = 0
            flag_value = worker.get("flags", {}).get(previous_level_flag)
            
            if flag_value is not None:
                if isinstance(flag_value, dict) and "value" in flag_value:
                    previous_uses = flag_value.get("value", 0)
                elif isinstance(flag_value, (int, float)):
                    previous_uses = flag_value
            
            # Unlock if previous level has been used enough times
            if previous_uses >= required_uses:
                filtered.append(interaction)
        
        return filtered
        
    def filter_interactions_by_traits(interactions, worker):
        """Filter interactions based on worker traits."""
        filtered = []
        for interaction in interactions:
            # Check required traits
            required_traits = interaction.get("required_traits", [])
            worker_traits = worker.get("traits", [])
            
            # If no traits are required, include the interaction
            if not required_traits:
                filtered.append(interaction)
                continue
                
            # Check if worker has all required traits
            has_required_traits = all(trait in worker_traits for trait in required_traits)
            
            if has_required_traits:
                filtered.append(interaction)
        
        return filtered
        
    def filter_interactions_by_worker_name(interactions, worker):
        """Filter interactions based on worker name."""
        filtered = []
        worker_name = worker.get("name", "Unknown")
        renpy.log(f"Filtering interactions for worker: {worker_name}")
        
        for interaction in interactions:
            # Check if interaction is restricted to specific workers
            specific_workers = interaction.get("specific_workers", [])
            
            # Debug log for interactions with specific workers
            if specific_workers:
                renpy.log(f"Found interaction '{interaction.get('name')}' for specific workers: {specific_workers}")
                
            # If not restricted to specific workers, include it
            if not specific_workers:
                filtered.append(interaction)
                continue
            
            # Case-insensitive name matching
            worker_name_lower = worker_name.lower() if worker_name else ""
            specific_workers_lower = [name.lower() for name in specific_workers]
                
            # Check if this worker is in the list of specific workers (case-insensitive)
            if worker_name_lower in specific_workers_lower:
                renpy.log(f"✓ Added specific interaction for {worker_name}: {interaction.get('name')}")
                filtered.append(interaction)
            else:
                renpy.log(f"✗ Skipped specific interaction, not for {worker_name}: {interaction.get('name')} (looking for {specific_workers})")
        
        return filtered
        
    def categorize_interactions(interactions):
        """
        Categorize interactions into predefined and custom categories.
        Returns a dictionary with category names as keys and lists of interactions as values.
        """
        categories = {
            "Discipline": [],
            "Romance": [],
            "Friendship": [],
            "Joy": [],
            "Other": []
        }
        
        for interaction in interactions:
            # First check for explicit categories
            explicit_categories = interaction.get("categories", [])
            if explicit_categories:
                # Add interaction to each of its explicit categories
                for category in explicit_categories:
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(interaction)
                continue
            
            # If no explicit categories, categorize based on effects
            effects = interaction.get("effect", {})
            categorized = False
            
            if "rebelliousness" in effects and effects["rebelliousness"] < 0:
                categories["Discipline"].append(interaction)
                categorized = True
            if "relationship" in effects and effects["relationship"] > 0:
                categories["Friendship"].append(interaction)
                categorized = True
            if "romance" in effects and effects["romance"] > 0:
                categories["Romance"].append(interaction)
                categorized = True
            if "joy" in effects and effects["joy"] > 0:
                categories["Joy"].append(interaction)
                categorized = True
            
            # If not categorized by effects, put in Other
            if not categorized:
                categories["Other"].append(interaction)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def apply_interaction_effects(worker, interaction, apply_costs=True):
        """Apply the effects of an interaction to a worker.
        
        Args:
            worker: The worker to apply effects to
            interaction: The interaction data
            apply_costs: If True, apply energy/health/money costs. If False, skip costs.
        """
        # Apply stat changes
        effects = interaction.get("effect", {})
        for stat, change in effects.items():
            if stat != "flags":  # Handle flags separately
                current_value = worker.get(stat, 0)
                worker[stat] = max(0, min(100, current_value + change))
        
        # Apply flag changes
        flag_effects = effects.get("flags", {})
        if not worker.get("flags"):
            worker["flags"] = {}
        
        for flag_name, flag_value in flag_effects.items():
            if flag_value is None:
                # Remove flag if value is None
                if flag_name in worker["flags"]:
                    del worker["flags"][flag_name]
            else:
                # Handle incremental flags (for usage counting)
                if isinstance(flag_value, dict) and flag_value.get("increment"):
                    current_flag = worker["flags"].get(flag_name)
                    if current_flag is not None:
                        if isinstance(current_flag, dict) and "value" in current_flag:
                            # Increment existing dict flag
                            new_value = current_flag["value"] + flag_value["value"]
                            worker["flags"][flag_name] = {
                                "value": new_value,
                                "duration": flag_value.get("duration", current_flag.get("duration", -1))
                            }
                        elif isinstance(current_flag, (int, float)):
                            # Convert simple number to dict and increment
                            worker["flags"][flag_name] = {
                                "value": current_flag + flag_value["value"],
                                "duration": flag_value.get("duration", -1)
                            }
                        else:
                            # Set new incremental flag
                            worker["flags"][flag_name] = flag_value
                    else:
                        # Set new incremental flag
                        worker["flags"][flag_name] = flag_value
                else:
                    # Add or update flag normally
                    worker["flags"][flag_name] = flag_value
        
        # Track interaction usage for unlock system
        interaction_level = interaction.get("interaction_level", 1)
        category = interaction.get("categories", [])
        
        if category and interaction_level:
            main_category = category[0] if category else "Other"
            category_flag_base = f"{main_category.lower()}_uses"
            level_flag = f"{category_flag_base}_level_{interaction_level}"
            
            # Increment usage count for this level
            current_uses = 0
            flag_value = worker["flags"].get(level_flag)
            
            if flag_value is not None:
                if isinstance(flag_value, dict) and "value" in flag_value:
                    current_uses = flag_value.get("value", 0)
                elif isinstance(flag_value, (int, float)):
                    current_uses = flag_value
            
            # Increment and store
            worker["flags"][level_flag] = {
                "value": current_uses + 1,
                "duration": -1  # Permanent
            }
        
        # Apply costs only if apply_costs is True
        if apply_costs:
            worker["energy"] = max(0, worker["energy"] - interaction.get("cost_energy", 0))
            worker["health"] = max(0, worker["health"] - interaction.get("cost_health", 0))
            store.money = max(0, store.money - interaction.get("cost_money", 0))

        # Tutorial: friendly chat completion is now handled when closing the interaction_result screen

    def get_interaction_image(worker, interaction):
        """
        Returns an image for the given interaction, prioritizing the worker's folder over the default folder.
        Uses robust flexible matching for better compatibility with different file formats and naming.
        Uses cache to maintain the same image throughout the entire interaction.
        
        Args:
            worker: Objeto trabajador (diccionario)
            interaction: Interacción actual (diccionario)
            
        Returns:
            Ruta a la imagen de la interacción
        """
        # Crear clave de caché única basada solo en worker e interaction
        worker_name = worker.get("name", "unknown") if hasattr(worker, "get") else "unknown"
        interaction_id = interaction.get("id", "unknown") if hasattr(interaction, "get") else "unknown"
        cache_key = f"{worker_name}_{interaction_id}_interaction_image"
        
        # PRIMERO: Verificar si ya tenemos una imagen en caché para esta interacción
        # Usar get_cached_choice con una lista temporal para verificar el caché
        # Si existe en caché, devolverlo directamente sin verificar opciones
        try:
            # Intentar obtener del caché directamente
            # image_selection_cache está definido en event_visuals.rpy en init python
            # En Ren'Py, está disponible en el store global
            if hasattr(store, 'image_selection_cache') and cache_key in store.image_selection_cache:
                cached_image = store.image_selection_cache[cache_key]
                # Verificar que la imagen cached aún existe
                if renpy.loadable(cached_image):
                    renpy.log(f"Usando imagen en caché para interacción: {cached_image}")
                    return cached_image
                else:
                    # Si el archivo cached ya no existe, limpiar caché
                    del store.image_selection_cache[cache_key]
        except (AttributeError, KeyError, NameError):
            # Si el caché no está disponible, continuar con búsqueda normal
            pass
        
        # Extraer el folder del worker exactamente como lo hace get_worker_image
        if hasattr(worker, "get") and callable(worker.get):
                worker_folder = worker.get("folder", "aspen")  # Fallback to aspen instead of default
        else:
            worker_folder = "aspen"  # Fallback to aspen instead of default
        
        # Definir base folder del trabajador
        base_folder = f"images/workers/{worker_folder}/"
        
        # Determinar el nombre base de la imagen
        image_base = interaction.get("image")
        categories = interaction.get("categories", []) or []
        worker_gender = (worker.get("gender", "").lower() if hasattr(worker, "get") else "").lower()
        is_player_male = store.player_title.lower() == "lord"
        player_gendered_suffix = "_male" if is_player_male else "_female"

        # Preparar candidatos por prioridad
        candidate_bases = []
        if image_base:
            # 1) Imagen específica del interaction (con y sin sufijo de género del jugador)
            candidate_bases.append(f"{image_base}{player_gendered_suffix}")
            candidate_bases.append(image_base)

        # 2) Fallback por categoría (basado en género del trabajador cuando aplica)
        if "Romance" in categories:
            if worker_gender == "female":
                candidate_bases.append("romance_female")
            elif worker_gender == "male":
                candidate_bases.append("romance_male")
            else:
                # Si no se conoce el género, probar ambas
                candidate_bases.extend(["romance_female", "romance_male"])
        elif "Friendship" in categories:
            candidate_bases.append("friendship")
        elif "Joy" in categories:
            if worker_gender == "female":
                candidate_bases.append("joy_female")
            elif worker_gender == "male":
                candidate_bases.append("joy_male")
            else:
                candidate_bases.extend(["joy_female", "joy_male"])
        elif "Discipline" in categories:
            candidate_bases.append("obedience")
        
        # Recopilar TODAS las posibles imágenes de todas las bases candidatas
        all_possible_matches = []
        for base in candidate_bases:
            if not base:
                continue
            matches = get_pattern_matches_flexible(base_folder, base)
            if matches:
                all_possible_matches.extend(matches)
        
        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_matches = []
        for match in all_possible_matches:
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)
        all_possible_matches = unique_matches
        
        # Si encontramos imágenes, usar get_cached_choice con TODAS las opciones
        # Esto asegura que siempre use la misma imagen, incluso si diferentes bases tienen matches
        if all_possible_matches:
            renpy.log(f"DEBUG: Cache key: {cache_key}, Total matches: {len(all_possible_matches)}")
            selected_media = get_cached_choice(all_possible_matches, cache_key)
            renpy.log(f"¡ENCONTRADO! Usando archivo en carpeta del trabajador: {selected_media}")
            return selected_media
        
        # FALLBACK: Usar imagen de perfil del trabajador
        renpy.log("No se encontró ninguna imagen específica, usando imagen de perfil del trabajador")
        profile_image = get_worker_image(worker)
        # Cachear la imagen de perfil también
        get_cached_choice([profile_image], cache_key)
        return profile_image

