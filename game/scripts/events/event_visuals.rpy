init python:
    import os
    
    # Cache global para imágenes seleccionadas
    image_selection_cache = {}
    # También ponerlo en store para acceso desde otros módulos
    store.image_selection_cache = image_selection_cache
    # Contador de instancias: cada daily story obtiene un índice distinto para variar imágenes
    _image_selection_instance = 0

    def clear_image_cache():
        """
        Limpia el caché de imágenes seleccionadas.
        Se llama cuando se genera un nuevo Daily Report.
        Resetea también el contador de instancias.
        """
        global image_selection_cache, _image_selection_instance
        image_selection_cache.clear()
        _image_selection_instance = 0
        renpy.log("Image selection cache cleared for new Daily Report")

    def get_cached_choice(choices, cache_key):
        """
        Selecciona un elemento de la lista usando caché.
        La primera vez selecciona aleatoriamente, luego usa el caché.
        Incluye día e índice de instancia en la clave para que:
        - Distintos días muestren imágenes distintas.
        - Cada daily story dentro del mismo día use una imagen distinta.
        - La misma instancia siempre use la misma imagen (al reabrir ventana).
        """
        global _image_selection_instance
        if not choices:
            return None
        try:
            day_suffix = getattr(store, "current_day", 1)
            year = getattr(store, "current_year", 1)
            month = getattr(store, "current_month", 1)
            total_days = (year - 1) * 12 * 28 + (month - 1) * 28 + day_suffix
        except Exception:
            total_days = 1
        _image_selection_instance += 1
        cache_key = f"{cache_key}_d{total_days}_n{_image_selection_instance}"

        # Si ya está en caché, devolver el resultado guardado
        if cache_key in image_selection_cache:
            cached_result = image_selection_cache[cache_key]
            # Verificar que el resultado cached aún esté en las opciones disponibles
            if cached_result in choices:
                return cached_result
            else:
                # Si el archivo cached ya no existe, limpiar caché y seleccionar nuevo
                del image_selection_cache[cache_key]
        
        # Primera vez o caché inválido - seleccionar aleatoriamente y guardar
        selected = renpy.random.choice(choices)
        image_selection_cache[cache_key] = selected
        return selected

    def get_random_choice(choices):
        """
        Selecciona un elemento aleatorio de la lista SIN usar caché.
        Para uso en el menú de habilidades donde queremos explorar contenido.
        """
        if not choices:
            return None
        return renpy.random.choice(choices)



    def should_exclude_trait_file(filepath, trait_prefixes, current_skill_patterns):
        """
        Determina si un archivo debe ser excluido por tener un prefijo de trait.
        
        Args:
            filepath: Ruta completa del archivo
            trait_prefixes: Tupla de prefijos de traits a verificar
            current_skill_patterns: Lista de patrones de skill que estamos buscando actualmente (no usado actualmente, pero mantenido para futuras extensiones)
        
        Returns:
            True si el archivo debe ser excluido, False si no
        """
        basename = os.path.basename(filepath).lower()
        
        # Excluir archivos que empiezan con cualquier prefijo de trait
        for prefix in trait_prefixes:
            if basename.startswith(prefix):
                return True
        
        return False

    # Prefijos de imágenes reservadas para interacciones (worker interactions, Take a Walk, etc.)
    # No deben usarse en eventos diarios aunque coincidan con el patrón de skill (ej. discipline_bdsm_lady para BDSM)
    INTERACTION_IMAGE_PREFIXES = ("discipline_", "romance_", "friendship_", "obedience")

    def should_exclude_interaction_file(filepath):
        """
        Excluye imágenes reservadas para el menú de interacciones del trabajador.
        Ej.: discipline_bdsm_lady es para 'BDSM Conditioning', no para eventos diarios de BDSM.
        """
        basename = os.path.basename(filepath).lower()
        for prefix in INTERACTION_IMAGE_PREFIXES:
            if basename.startswith(prefix):
                return True
        return False

    def get_trait_prefixes(worker):
        """
        Get trait prefixes in priority order: Transformed > Magical > Futa > Pregnant
        Returns a list of prefix combinations to try.
        
        Images should use "pregnant_" prefix (WM images are renamed during import).
        """
        if not worker or "traits" not in worker:
            return []
        
        worker_traits = worker["traits"]
        relevant_traits = []
        
        # Check for relevant traits in priority order
        if "Transformed" in worker_traits:
            relevant_traits.append("transformed")
        if "Magical" in worker_traits:
            relevant_traits.append("magical")
        if "Futa" in worker_traits:
            relevant_traits.append("futa")
        if "Pregnant" in worker_traits:
            relevant_traits.append("pregnant")
        
        if not relevant_traits:
            return []
        
        # Generate combinations in priority order
        prefixes = []
        
        # If we have multiple traits, try combinations first
        if len(relevant_traits) >= 2:
            # Try all combinations starting with highest priority
            # Transformed combinations
            if "transformed" in relevant_traits and "magical" in relevant_traits:
                prefixes.append("transformed_magical")
            if "transformed" in relevant_traits and "futa" in relevant_traits:
                prefixes.append("transformed_futa")
            if "transformed" in relevant_traits and "pregnant" in relevant_traits:
                prefixes.append("transformed_pregnant")
            # Magical combinations
            if "magical" in relevant_traits and "futa" in relevant_traits:
                prefixes.append("magical_futa")
            if "magical" in relevant_traits and "pregnant" in relevant_traits:
                prefixes.append("magical_pregnant")
            # Futa combinations
            if "futa" in relevant_traits and "pregnant" in relevant_traits:
                prefixes.append("futa_pregnant")
            
            # Try three-way combinations if present
            if "transformed" in relevant_traits and "magical" in relevant_traits and "futa" in relevant_traits:
                prefixes.insert(0, "transformed_magical_futa")  # Highest priority
            if "transformed" in relevant_traits and "magical" in relevant_traits and "pregnant" in relevant_traits:
                prefixes.insert(0, "transformed_magical_pregnant")
            if "transformed" in relevant_traits and "futa" in relevant_traits and "pregnant" in relevant_traits:
                prefixes.insert(0, "transformed_futa_pregnant")
            if "magical" in relevant_traits and "futa" in relevant_traits and "pregnant" in relevant_traits:
                prefixes.insert(0, "magical_futa_pregnant")
            
            # Try four-way combination if all are present
            if len(relevant_traits) == 4:
                prefixes.insert(0, "transformed_magical_futa_pregnant")  # Absolute highest priority
        
        # Then try individual traits in priority order
        prefixes.extend(relevant_traits)
        
        return prefixes

    def _worker_allows_profile_variant(worker, filepath):
        """
        Return True if a profile-variant file is valid for this worker's traits.
        Examples:
        - profile.png -> always valid
        - pregnant_profile.png -> requires Pregnant
        - transformed_magical_profile.png -> requires Transformed + Magical
        """
        if not filepath:
            return False

        basename = os.path.basename(filepath).lower()
        if "profile" not in basename:
            return True

        # Prefix section before "profile" (e.g. "pregnant_", "transformed_magical_")
        prefix_part = basename.split("profile", 1)[0].rstrip("_")
        if not prefix_part:
            return True

        token_to_trait = {
            "pregnant": "Pregnant",
            "futa": "Futa",
            "transformed": "Transformed",
            "magical": "Magical",
        }

        required_traits = []
        for token in prefix_part.split("_"):
            if token in token_to_trait:
                required_traits.append(token_to_trait[token])

        if not required_traits:
            return True

        worker_traits = set((worker or {}).get("traits", []) or [])
        return set(required_traits).issubset(worker_traits)

    def get_skill_name_for_images(skill_name):
        """
        Convert skill_name (number or name) to the appropriate name for image searching.
        Handles special cases like Homosexual -> les/gay and Service -> service/maid
        """
        # Use the global skill mapping system
        skill_name_str = str(skill_name)
        
        # Use skill name directly - no conversion needed
        skill_name = skill_name_str
        
        # Convert skill name to lowercase for image searching
        skill_name_mapping = {
            "Sex": "sex", "Anal": "anal", "BDSM": "bdsm",
            "Hand": "hand", "Oral": "oral", "Homo": "homo",
            "Special": "special", "Group": "group", "Extreme": "extreme",
            "Striptease": "striptease", "Combat": "combat", "Clever": "clever",
            "Charm": "charm", "Service": "service", "Agility": "agility",
            "Craft": "craft"
        }
        
        if skill_name in skill_name_mapping:
            return skill_name_mapping[skill_name]
        
        # Para skills que no están mapeadas, devolver como está
        return skill_name.lower()

    def get_skill_search_patterns(skill_name):
        """
        Get search patterns for a skill name. Some skills search for multiple patterns.
        """
        special_patterns = {
            "homo": ["les", "gay"],           # Homosexual busca "les" o "gay"
            "service": ["wait", "service", "maid"],      # Service busca "wait", "service" o "maid"
            "special": ["special", "titty"],  # Special busca "special" o "titty"
            "striptease": ["strip", "striptease"],  # Striptease busca "strip" o "striptease"
            "extreme": ["extreme", "beast"]  # Extreme busca "extreme" o "beast"
        }
        
        skill_lower = skill_name.lower() if skill_name else skill_name
        if skill_lower in special_patterns:
            return special_patterns[skill_lower]
        else:
            return [skill_name]

    def try_trait_image_search_worker_only(worker, base_folder, story_image, skill_name, outcome, trait_prefixes):
        """
        Try to find images with trait prefixes in worker's folder only
        """
        if not trait_prefixes:
            return None
            
        is_success = outcome == "success" or outcome == "critical_success"
        is_failure = outcome == "failure" or outcome == "mediocre"
        
        for prefix in trait_prefixes:
            renpy.log(f"Trying trait prefix in worker folder: {prefix}")
            
            # 1. Event-specific with trait prefix and outcome
            if story_image:
                # Try failure version first if it's a failure
                if is_failure:
                    failure_pattern = f"{prefix}_{story_image}_failure"
                    failure_matches = [f for f in renpy.list_files() if f.startswith(base_folder) and failure_pattern in os.path.basename(f)]
                    if failure_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{skill_name}_{outcome}_skill_failure"
                        selected = get_cached_choice(failure_matches, cache_key)
                        renpy.log(f"Found trait-specific event failure image: {selected}")
                        return selected
                
                # Try success version (or general version for success)
                if is_success:
                    success_pattern = f"{prefix}_{story_image}"
                    success_matches = [f for f in renpy.list_files() if f.startswith(base_folder) and success_pattern in os.path.basename(f) and "failure" not in os.path.basename(f)]
                    if success_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{skill_name}_{outcome}_skill_success"
                        selected = get_cached_choice(success_matches, cache_key)
                        renpy.log(f"Found trait-specific event success image: {selected}")
                        return selected
                
                # Try general event image with trait prefix
                general_pattern = f"{prefix}_{story_image}"
                general_matches = [f for f in renpy.list_files() if f.startswith(base_folder) and general_pattern in os.path.basename(f)]
                if general_matches:
                    # Filter based on outcome
                    filtered_matches = []
                    for f in general_matches:
                        basename = os.path.basename(f).lower()
                        if is_failure and "failure" not in basename:
                            continue
                        if is_success and "failure" in basename:
                            continue
                        filtered_matches.append(f)
                    
                    if filtered_matches:
                        selected = renpy.random.choice(filtered_matches)
                        renpy.log(f"Found trait-specific event image: {selected}")
                        return selected
            
            # 2. Skill-specific with trait prefix and outcome
            if skill_name is not None:
                # Convert skill_name to skill name for image searching
                skill_name_for_search = get_skill_name_for_images(skill_name)
                skill_patterns = get_skill_search_patterns(skill_name_for_search)
                
                for skill_pattern_name in skill_patterns:
                    # Try failure version first if it's a failure
                    if is_failure:
                        skill_failure_pattern = f"{prefix}_{skill_pattern_name}_failure"
                        skill_failure_matches = [f for f in renpy.list_files() if f.startswith(base_folder) and skill_failure_pattern in os.path.basename(f)]
                        if skill_failure_matches:
                            selected = renpy.random.choice(skill_failure_matches)
                            renpy.log(f"Found trait-specific skill failure image: {selected}")
                            return selected
                    
                    # Try success version (or general version for success)
                    if is_success:
                        skill_success_pattern = f"{prefix}_{skill_pattern_name}"
                        skill_success_matches = [f for f in renpy.list_files() if f.startswith(base_folder) and skill_success_pattern in os.path.basename(f) and "failure" not in os.path.basename(f)]
                        if skill_success_matches:
                            selected = renpy.random.choice(skill_success_matches)
                            renpy.log(f"Found trait-specific skill success image: {selected}")
                            return selected
                    
                    # Try general skill image with trait prefix
                    skill_pattern = f"{prefix}_{skill_pattern_name}"
                    skill_matches = [f for f in renpy.list_files() if f.startswith(base_folder) and skill_pattern in os.path.basename(f)]
                    if skill_matches:
                        # First try to find outcome-specific images
                        outcome_specific_matches = []
                        general_matches = []
                        
                        for f in skill_matches:
                            basename = os.path.basename(f).lower()
                            if is_failure and "failure" in basename:
                                outcome_specific_matches.append(f)
                            elif is_success and "failure" not in basename:
                                outcome_specific_matches.append(f)

                            elif "failure" not in basename:  # General images (no failure in name)
                                general_matches.append(f)
                        
                        # Prefer outcome-specific, fallback to general
                        if outcome_specific_matches:
                            cache_key = f"{worker.get('name', 'unknown')}_{skill_name}_{outcome}_trait_specific"
                            selected = get_cached_choice(outcome_specific_matches, cache_key)
                            renpy.log(f"Found trait-specific outcome-specific skill image: {selected}")
                            return selected
                        elif general_matches:
                            cache_key = f"{worker.get('name', 'unknown')}_{skill_name}_{outcome}_trait_general"
                            selected = get_cached_choice(general_matches, cache_key)
                            renpy.log(f"Found trait-specific general skill image (fallback): {selected}")
                            return selected
        
        return None

    def try_trait_image_search(worker, base_folder, default_folder, story_image, skill_name, outcome, trait_prefixes):
        """
        Try to find images with trait prefixes in default folder (for fallback)
        """
        if not trait_prefixes:
            return None
            
        is_success = outcome == "success" or outcome == "critical_success"
        is_failure = outcome == "failure" or outcome == "mediocre"
        
        for prefix in trait_prefixes:
            renpy.log(f"Trying trait prefix in default folder: {prefix}")
            
            # 1. Event-specific with trait prefix and outcome
            if story_image:
                # Try failure version first if it's a failure
                if is_failure:
                    failure_pattern = f"{prefix}_{story_image}_failure"
                    failure_matches = get_pattern_matches_flexible(default_folder, failure_pattern)
                    if failure_matches:
                        selected = renpy.random.choice(failure_matches)
                        renpy.log(f"Found default trait-specific event failure image: {selected}")
                        return selected
                
                # Try success version (or general version for success)
                if is_success:
                    success_pattern = f"{prefix}_{story_image}"
                    success_matches = get_pattern_matches_flexible(default_folder, success_pattern, exclude_failure=True)
                    if success_matches:
                        selected = renpy.random.choice(success_matches)
                        renpy.log(f"Found default trait-specific event success image: {selected}")
                        return selected
            
            # 2. Skill-specific with trait prefix and outcome
            if skill_name is not None:
                # Convert skill_name to skill name for image searching
                skill_name_for_search = get_skill_name_for_images(skill_name)
                skill_patterns = get_skill_search_patterns(skill_name_for_search)
                
                for skill_pattern_name in skill_patterns:
                    # Try failure version first if it's a failure
                    if is_failure:
                        skill_failure_pattern = f"{prefix}_{skill_pattern_name}_failure"
                        skill_failure_matches = get_pattern_matches_flexible(default_folder, skill_failure_pattern)
                        if skill_failure_matches:
                            selected = renpy.random.choice(skill_failure_matches)
                            renpy.log(f"Found default trait-specific skill failure image: {selected}")
                            return selected
                    
                    # Try success version (or general version for success)
                    if is_success:
                        skill_success_pattern = f"{prefix}_{skill_pattern_name}"
                        skill_success_matches = get_pattern_matches_flexible(default_folder, skill_success_pattern, exclude_failure=True)
                        if skill_success_matches:
                            selected = renpy.random.choice(skill_success_matches)
                            renpy.log(f"Found default trait-specific skill success image: {selected}")
                            return selected
        
        return None

    def get_event_image(worker, event, outcome=None, skill_name=None):
        """
        Get the appropriate image for an event, with proper priority order.
        Priority: Worker folder with traits > Worker folder without traits > Default folder with traits > Default folder without traits > Profile image
        """
        if not worker or not event:
            return None
        
        # Get worker folder
        fallback = get_fallback_folder(worker)
        if hasattr(worker, 'get'):
            worker_folder = worker.get("folder", fallback)
            renpy.log(f"Worker folder: {worker_folder}")
        else:
            worker_folder = fallback
            renpy.log(f"Worker has no get method, using {fallback} folder as fallback")
        
        base_folder = f"images/workers/{worker_folder}/"
        default_folder = f"images/workers/{fallback}/"  # Use gender-appropriate fallback
        
        renpy.log(f"Worker: {worker['name']}, Outcome: {outcome}, Skill: {skill_name}, Folder: {base_folder}")
        
        # Get story image name from event
        story_image = event.get("story_image")
        success_image = event.get("success_image")
        failure_image = event.get("failure_image")
        renpy.log(f"Story image: {story_image}, Success image: {success_image}, Failure image: {failure_image}")
        
        # Debug the actual outcome value - matching outcome_key format from event_daily_exec.rpy
        is_success = outcome in ["success", "critical_success"]
        is_failure = outcome in ["failure", "mediocre"]  # Both "failure" and "mediocre" should look for failure images
        is_mediocre = outcome == "mediocre"
        renpy.log(f"Outcome analysis - Raw: '{outcome}', Is success: {is_success}, Is failure: {is_failure}")
        
        # Get trait prefixes for the worker
        trait_prefixes = get_trait_prefixes(worker)
        
        # PRIORITY 1: Worker folder with traits (for event-specific images)
        if trait_prefixes and story_image:
            renpy.log(f"Worker has relevant traits, trying event-specific images with traits: {trait_prefixes}")
            for prefix in trait_prefixes:
                # Try failure version first if it's a failure
                if is_failure:
                    # Try explicit failure image with trait
                    if failure_image:
                        failure_pattern = f"{prefix}_{failure_image}"
                        failure_matches = get_pattern_matches_flexible(base_folder, failure_pattern)
                        if failure_matches:
                            cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{failure_image}_{outcome}_event_failure"
                            selected = get_cached_choice(failure_matches, cache_key)
                            renpy.log(f"Found trait-specific event failure image: {selected}")
                            return selected
                    
                    # Try story_image with _failure suffix and trait
                    failure_pattern = f"{prefix}_{story_image}_failure"
                    failure_matches = get_pattern_matches_flexible(base_folder, failure_pattern)
                    if failure_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{story_image}_{outcome}_event_story_failure"
                        selected = get_cached_choice(failure_matches, cache_key)
                        renpy.log(f"Found trait-specific story failure image: {selected}")
                        return selected
                
                # Try success version with trait
                elif is_success:
                    # Try explicit success image with trait
                    if success_image:
                        success_pattern = f"{prefix}_{success_image}"
                        success_matches = get_pattern_matches_flexible(base_folder, success_pattern)
                        if success_matches:
                            cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{success_image}_{outcome}_event_success"
                            selected = get_cached_choice(success_matches, cache_key)
                            renpy.log(f"Found trait-specific event success image: {selected}")
                            return selected
                    
                    # Try story_image without _failure suffix and trait
                    success_pattern = f"{prefix}_{story_image}"
                    success_matches = get_pattern_matches_flexible(base_folder, success_pattern, exclude_failure=True)
                    if success_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{story_image}_{outcome}_event_story_success"
                        selected = get_cached_choice(success_matches, cache_key)
                        renpy.log(f"Found trait-specific story success image: {selected}")
                        return selected
                
                # Try general story image with trait (flexible extension matching)
                general_pattern = f"{prefix}_{story_image}"
                general_matches = get_pattern_matches_flexible(base_folder, general_pattern)
                if general_matches:
                    # Filter based on outcome if possible
                    filtered_matches = []
                    for f in general_matches:
                        basename = os.path.basename(f).lower()
                        if is_failure and "failure" not in basename:
                            continue
                        if is_success and "failure" in basename:
                            continue
                        filtered_matches.append(f)
                    
                    if filtered_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{story_image}_{outcome}_event_general_filtered"
                        selected = get_cached_choice(filtered_matches, cache_key)
                        renpy.log(f"Found trait-specific story image (filtered): {selected}")
                        return selected
                    else:
                        # If no filtered matches, use any match as fallback
                        cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{story_image}_{outcome}_event_general_fallback"
                        selected = get_cached_choice(general_matches, cache_key)
                        renpy.log(f"Found trait-specific story image (fallback): {selected}")
                        return selected
        
        # PRIORITY 2: Worker folder without traits (for event-specific images)
        if story_image:
            renpy.log(f"Processing story image in worker folder: {story_image}")
            
            # For failure outcomes
            if is_failure:
                # Try explicit failure image first (flexible extension matching)
                if failure_image:
                    failure_matches = get_image_matches_flexible(base_folder, failure_image)
                    if failure_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{failure_image}_{outcome}_event_failure"
                        selected = get_cached_choice(failure_matches, cache_key)
                        renpy.log(f"Found worker folder event failure image: {selected}")
                        return selected
                
                # Try story_image with _failure suffix (flexible extension matching)
                failure_pattern = f"{story_image}_failure"
                failure_matches = get_pattern_matches_flexible(base_folder, failure_pattern)
                if failure_matches:
                    cache_key = f"{worker.get('name', 'unknown')}_{story_image}_{outcome}_event_story_failure"
                    selected = get_cached_choice(failure_matches, cache_key)
                    renpy.log(f"Found worker folder story failure image: {selected}")
                    return selected
            
            # For success outcomes
            elif is_success:
                # Try explicit success image first (flexible extension matching)
                if success_image:
                    success_matches = get_image_matches_flexible(base_folder, success_image)
                    if success_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{success_image}_{outcome}_event_success"
                        selected = get_cached_choice(success_matches, cache_key)
                        renpy.log(f"Found worker folder event success image: {selected}")
                        return selected
                
                # Try story_image without _failure suffix (flexible extension matching)
                # For rest images, use pattern matching
                if story_image and story_image.startswith("rest_"):
                    success_matches = get_pattern_matches_flexible(base_folder, story_image)
                    # Filter out failure images manually
                    success_matches = [f for f in success_matches if "failure" not in os.path.basename(f).lower()]
                else:
                    success_matches = get_image_matches_flexible(base_folder, story_image, exclude_failure=True)
                if success_matches:
                    cache_key = f"{worker.get('name', 'unknown')}_{story_image}_{outcome}_event_story_success"
                    selected = get_cached_choice(success_matches, cache_key)
                    renpy.log(f"Found worker folder story success image: {selected}")
                    return selected
            
            # Try general story image (flexible extension matching)
            # For rest images, first try the specific name, then fallback to generic "rest"
            if story_image and story_image.startswith("rest_"):
                # First try the specific rest image name (e.g., "rest_brothel")
                general_matches = get_pattern_matches_flexible(base_folder, story_image)
                if not general_matches:
                    # If not found, try generic "rest" pattern
                    renpy.log(f"Specific rest image '{story_image}' not found, trying generic 'rest' pattern")
                    general_matches = get_pattern_matches_flexible(base_folder, "rest")
            else:
                general_matches = get_image_matches_flexible(base_folder, story_image)
            if general_matches:
                # Filter based on outcome if possible
                filtered_matches = []
                for f in general_matches:
                    basename = os.path.basename(f).lower()
                    if is_failure and "failure" not in basename:
                        continue
                    if is_success and "failure" in basename:
                        continue
                    filtered_matches.append(f)
                
                if filtered_matches:
                    cache_key = f"{worker.get('name', 'unknown')}_{story_image}_{outcome}_event_general_filtered"
                    selected = get_cached_choice(filtered_matches, cache_key)
                    renpy.log(f"Found worker folder story image (filtered): {selected}")
                    return selected
                else:
                    # If no filtered matches, use any match as fallback
                    cache_key = f"{worker.get('name', 'unknown')}_{story_image}_{outcome}_event_general_fallback"
                    selected = get_cached_choice(general_matches, cache_key)
                    renpy.log(f"Found worker folder story image (fallback): {selected}")
                    return selected
        
        # PRIORITY 3: Worker folder with traits (for skill-based images)
        if trait_prefixes and skill_name is not None:
            renpy.log(f"Worker has relevant traits, trying skill-based images with traits: {trait_prefixes}")
            skill_name_for_search = get_skill_name_for_images(skill_name)
            skill_patterns = get_skill_search_patterns(skill_name_for_search)
            
            for skill_pattern_name in skill_patterns:
                for prefix in trait_prefixes:
                    # Try failure version first if it's a failure
                    if is_failure:
                        skill_failure_pattern = f"{prefix}_{skill_pattern_name}_failure"
                        skill_failure_matches = get_pattern_matches_flexible(base_folder, skill_failure_pattern)
                        skill_failure_matches = [f for f in skill_failure_matches if not should_exclude_interaction_file(f)]
                        if skill_failure_matches:
                            cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{skill_pattern_name}_{outcome}_skill_failure"
                            selected = get_cached_choice(skill_failure_matches, cache_key)
                            renpy.log(f"Found trait-specific skill failure image: {selected}")
                            return selected
                    
                    # Try success version
                    elif is_success:
                        skill_success_pattern = f"{prefix}_{skill_pattern_name}"
                        skill_success_matches = get_pattern_matches_flexible(base_folder, skill_success_pattern, exclude_failure=True)
                        skill_success_matches = [f for f in skill_success_matches if not should_exclude_interaction_file(f)]
                        if skill_success_matches:
                            cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{skill_pattern_name}_{outcome}_skill_success"
                            selected = get_cached_choice(skill_success_matches, cache_key)
                            renpy.log(f"Found trait-specific skill success image: {selected}")
                            return selected
                    
                    # Try general skill image with trait (flexible extension matching)
                    skill_pattern = f"{prefix}_{skill_pattern_name}"
                    skill_matches = get_pattern_matches_flexible(base_folder, skill_pattern)
                    skill_matches = [f for f in skill_matches if not should_exclude_interaction_file(f)]
                    if skill_matches:
                        # Filter based on outcome
                        filtered_matches = []
                        for f in skill_matches:
                            basename = os.path.basename(f).lower()
                            if is_failure and "failure" not in basename:
                                continue
                            if is_success and "failure" in basename:
                                continue
                            filtered_matches.append(f)
                        
                        if filtered_matches:
                            cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{skill_pattern_name}_{outcome}_skill_general_filtered"
                            selected = get_cached_choice(filtered_matches, cache_key)
                            renpy.log(f"Found trait-specific skill image (filtered): {selected}")
                            return selected
                        else:
                            # If no filtered matches, use any match as fallback
                            cache_key = f"{worker.get('name', 'unknown')}_{prefix}_{skill_pattern_name}_{outcome}_skill_general_fallback"
                            selected = get_cached_choice(skill_matches, cache_key)
                            renpy.log(f"Found trait-specific skill image (fallback): {selected}")
                            return selected
        
        # PRIORITY 4: Worker folder without traits (for skill-based images)
        if skill_name is not None:
            renpy.log(f"No trait-specific images found, trying worker folder without traits for skill: {skill_name}")
            skill_name_for_search = get_skill_name_for_images(skill_name)
            skill_patterns = get_skill_search_patterns(skill_name_for_search)
            trait_file_prefixes = ("pregnant_", "futa_", "transformed_", "magical_")
            
            for skill_pattern_name in skill_patterns:
                # Try failure version first if it's a failure
                if is_failure:
                    skill_failure_pattern = f"{skill_pattern_name}_failure"
                    skill_failure_matches = get_pattern_matches_flexible(base_folder, skill_failure_pattern)
                    # Exclude trait-prefixed files if worker has no matching trait; exclude interaction images
                    skill_failure_matches = [f for f in skill_failure_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns) and not should_exclude_interaction_file(f)]
                    if skill_failure_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{skill_pattern_name}_{outcome}_skill_failure"
                        selected = get_cached_choice(skill_failure_matches, cache_key)
                        renpy.log(f"Found worker folder skill failure image: {selected}")
                        return selected
                
                # Try success version
                elif is_success:
                    skill_success_matches = get_pattern_matches_flexible(base_folder, skill_pattern_name, exclude_failure=True)
                    # Exclude trait-prefixed files; exclude interaction images (e.g. discipline_bdsm_lady)
                    skill_success_matches = [f for f in skill_success_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns) and not should_exclude_interaction_file(f)]
                    if skill_success_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{skill_pattern_name}_{outcome}_skill_success"
                        selected = get_cached_choice(skill_success_matches, cache_key)
                        renpy.log(f"Found worker folder skill success image: {selected}")
                        return selected
                
                # Try general skill image (flexible extension matching)
                skill_matches = get_pattern_matches_flexible(base_folder, skill_pattern_name)
                # Exclude trait-prefixed files; exclude interaction images (e.g. discipline_bdsm_lady)
                skill_matches = [f for f in skill_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns) and not should_exclude_interaction_file(f)]
                if skill_matches:
                    # Filter based on outcome
                    filtered_matches = []
                    for f in skill_matches:
                        basename = os.path.basename(f).lower()
                        if is_failure and "failure" not in basename:
                            continue
                        if is_success and "failure" in basename:
                            continue
                        filtered_matches.append(f)
                    
                    if filtered_matches:
                        cache_key = f"{worker.get('name', 'unknown')}_{skill_pattern_name}_{outcome}_skill_general_filtered"
                        selected = get_cached_choice(filtered_matches, cache_key)
                        renpy.log(f"Found worker folder skill image (filtered): {selected}")
                        return selected
                    else:
                        # If no filtered matches, use any match as fallback
                        cache_key = f"{worker.get('name', 'unknown')}_{skill_pattern_name}_{outcome}_skill_general_fallback"
                        selected = get_cached_choice(skill_matches, cache_key)
                        renpy.log(f"Found worker folder skill image (fallback): {selected}")
                        return selected
        
        # PRIORITY 5: Default folder with traits (for event-specific images)
        if trait_prefixes and story_image:
            renpy.log(f"No worker folder images found, trying default folder with traits for event: {story_image}")
            for prefix in trait_prefixes:
                # Try failure version first if it's a failure
                if is_failure:
                    # Try explicit failure image with trait
                    if failure_image:
                        failure_pattern = f"{prefix}_{failure_image}"
                        failure_matches = get_pattern_matches_flexible(default_folder, failure_pattern)
                        if failure_matches:
                            selected = renpy.random.choice(failure_matches)
                            renpy.log(f"Found default trait-specific event failure image: {selected}")
                            return selected
                    
                    # Try story_image with _failure suffix and trait
                    failure_pattern = f"{prefix}_{story_image}_failure"
                    failure_matches = get_pattern_matches_flexible(default_folder, failure_pattern)
                    if failure_matches:
                        selected = renpy.random.choice(failure_matches)
                        renpy.log(f"Found default trait-specific story failure image: {selected}")
                        return selected
                
                # Try success version with trait
                elif is_success:
                    # Try explicit success image with trait
                    if success_image:
                        success_pattern = f"{prefix}_{success_image}"
                        success_matches = get_pattern_matches_flexible(default_folder, success_pattern)
                        if success_matches:
                            selected = renpy.random.choice(success_matches)
                            renpy.log(f"Found default trait-specific event success image: {selected}")
                            return selected
                    
                    # Try story_image without _failure suffix and trait
                    success_pattern = f"{prefix}_{story_image}"
                    success_matches = get_pattern_matches_flexible(default_folder, success_pattern, exclude_failure=True)
                    if success_matches:
                        selected = renpy.random.choice(success_matches)
                        renpy.log(f"Found default trait-specific story success image: {selected}")
                        return selected
                
                # Try general story image with trait (flexible extension matching)
                general_pattern = f"{prefix}_{story_image}"
                general_matches = get_pattern_matches_flexible(default_folder, general_pattern)
                if general_matches:
                    # Filter based on outcome if possible
                    filtered_matches = []
                    for f in general_matches:
                        basename = os.path.basename(f).lower()
                        if is_failure and "failure" not in basename:
                            continue
                        if is_success and "failure" in basename:
                            continue
                        if is_mediocre and "failure" in basename:
                            continue  # Mediocre should not use failure images
                        filtered_matches.append(f)
                    
                    if filtered_matches:
                        selected = renpy.random.choice(filtered_matches)
                        renpy.log(f"Found default trait-specific story image (filtered): {selected}")
                        return selected
                    else:
                        # If no filtered matches, use any match as fallback
                        selected = renpy.random.choice(general_matches)
                        renpy.log(f"Found default trait-specific story image (fallback): {selected}")
                        return selected
        
        # PRIORITY 6: Default folder without traits (for event-specific images)
        if story_image:
            renpy.log(f"No worker folder images found, trying default folder without traits for event: {story_image}")
            
            # For failure outcomes
            if is_failure:
                # Try explicit failure image first
                if failure_image:
                    failure_matches = get_image_matches_flexible(default_folder, failure_image)
                    if failure_matches:
                        selected = renpy.random.choice(failure_matches)
                        renpy.log(f"Found default event failure image: {selected}")
                        return selected
                
                # Try story_image with _failure suffix (flexible extension matching)
                failure_pattern = f"{story_image}_failure"
                failure_matches = get_pattern_matches_flexible(default_folder, failure_pattern)
                if failure_matches:
                    selected = renpy.random.choice(failure_matches)
                    renpy.log(f"Found default story failure image: {selected}")
                    return selected
            
            # For success outcomes
            elif is_success:
                # Try explicit success image first
                if success_image:
                    success_matches = get_image_matches_flexible(default_folder, success_image)
                    if success_matches:
                        selected = renpy.random.choice(success_matches)
                        renpy.log(f"Found default event success image: {selected}")
                        return selected
                
                # Try story_image without _failure suffix
                # For rest images, use pattern matching
                if story_image and story_image.startswith("rest_"):
                    success_matches = get_pattern_matches_flexible(default_folder, story_image)
                    # Filter out failure images manually
                    success_matches = [f for f in success_matches if "failure" not in os.path.basename(f).lower()]
                else:
                    success_matches = get_image_matches_flexible(default_folder, story_image, exclude_failure=True)
                if success_matches:
                    selected = renpy.random.choice(success_matches)
                    renpy.log(f"Found default story success image: {selected}")
                    return selected
            
            # Try general story image (flexible extension matching)
            # For rest images, first try the specific name, then fallback to generic "rest"
            if story_image and story_image.startswith("rest_"):
                # First try the specific rest image name (e.g., "rest_brothel")
                general_matches = get_pattern_matches_flexible(default_folder, story_image)
                if not general_matches:
                    # If not found, try generic "rest" pattern
                    renpy.log(f"Specific rest image '{story_image}' not found in default folder, trying generic 'rest' pattern")
                    general_matches = get_pattern_matches_flexible(default_folder, "rest")
            else:
                general_matches = get_image_matches_flexible(default_folder, story_image)
            if general_matches:
                # Filter based on outcome if possible
                filtered_matches = []
                for f in general_matches:
                    basename = os.path.basename(f).lower()
                    if is_failure and "failure" not in basename:
                        continue
                    if is_success and "failure" in basename:
                        continue
                    filtered_matches.append(f)
                
                if filtered_matches:
                    selected = renpy.random.choice(filtered_matches)
                    renpy.log(f"Found default story image (filtered): {selected}")
                    return selected
                else:
                    # If no filtered matches, use any match as fallback
                    selected = renpy.random.choice(general_matches)
                    renpy.log(f"Found default story image (fallback): {selected}")
                    return selected
        
        # PRIORITY 7: Default folder with traits (for skill-based images)
        if trait_prefixes and skill_name is not None:
            renpy.log(f"No worker folder images found, trying default folder with traits for skill: {skill_name}")
            skill_name_for_search = get_skill_name_for_images(skill_name)
            skill_patterns = get_skill_search_patterns(skill_name_for_search)
            
            for skill_pattern_name in skill_patterns:
                for prefix in trait_prefixes:
                    # Try failure version first if it's a failure
                    if is_failure:
                        skill_failure_pattern = f"{prefix}_{skill_pattern_name}_failure"
                        skill_failure_matches = get_pattern_matches_flexible(default_folder, skill_failure_pattern)
                        skill_failure_matches = [f for f in skill_failure_matches if not should_exclude_interaction_file(f)]
                        if skill_failure_matches:
                            selected = renpy.random.choice(skill_failure_matches)
                            renpy.log(f"Found default trait-specific skill failure image: {selected}")
                            return selected
                    
                    # Try success version
                    elif is_success:
                        skill_success_pattern = f"{prefix}_{skill_pattern_name}"
                        skill_success_matches = get_pattern_matches_flexible(default_folder, skill_success_pattern, exclude_failure=True)
                        skill_success_matches = [f for f in skill_success_matches if not should_exclude_interaction_file(f)]
                        if skill_success_matches:
                            selected = renpy.random.choice(skill_success_matches)
                            renpy.log(f"Found default trait-specific skill success image: {selected}")
                            return selected
                    
                    # Try general skill image with trait (flexible extension matching)
                    skill_pattern = f"{prefix}_{skill_pattern_name}"
                    skill_matches = get_pattern_matches_flexible(default_folder, skill_pattern)
                    skill_matches = [f for f in skill_matches if not should_exclude_interaction_file(f)]
                    if skill_matches:
                        # Filter based on outcome
                        filtered_matches = []
                        for f in skill_matches:
                            basename = os.path.basename(f).lower()
                            if is_failure and "failure" not in basename:
                                continue
                            if is_success and "failure" in basename:
                                continue
                            filtered_matches.append(f)
                        
                        if filtered_matches:
                            selected = renpy.random.choice(filtered_matches)
                            renpy.log(f"Found default trait-specific skill image (filtered): {selected}")
                            return selected
                        else:
                            # If no filtered matches, use any match as fallback
                            selected = renpy.random.choice(skill_matches)
                            renpy.log(f"Found default trait-specific skill image (fallback): {selected}")
                            return selected
        
        # PRIORITY 8: Default folder without traits (for skill-based images)
        if skill_name is not None:
            renpy.log(f"No worker folder images found, trying default folder without traits for skill: {skill_name}")
            skill_name_for_search = get_skill_name_for_images(skill_name)
            skill_patterns = get_skill_search_patterns(skill_name_for_search)
            trait_file_prefixes = ("pregnant_", "futa_", "transformed_", "magical_")
            
            for skill_pattern_name in skill_patterns:
                # Try failure version first if it's a failure
                if is_failure:
                    skill_failure_pattern = f"{skill_pattern_name}_failure"
                    skill_failure_matches = get_pattern_matches_flexible(default_folder, skill_failure_pattern)
                    skill_failure_matches = [f for f in skill_failure_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns) and not should_exclude_interaction_file(f)]
                    if skill_failure_matches:
                        selected = renpy.random.choice(skill_failure_matches)
                        renpy.log(f"Found default skill failure image: {selected}")
                        return selected
                
                # Try success version
                elif is_success:
                    skill_success_matches = get_pattern_matches_flexible(default_folder, skill_pattern_name, exclude_failure=True)
                    skill_success_matches = [f for f in skill_success_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns) and not should_exclude_interaction_file(f)]
                    if skill_success_matches:
                        selected = renpy.random.choice(skill_success_matches)
                        renpy.log(f"Found default skill success image: {selected}")
                        return selected
                
                # Try general skill image (flexible extension matching)
                skill_matches = get_pattern_matches_flexible(default_folder, skill_pattern_name)
                skill_matches = [f for f in skill_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns) and not should_exclude_interaction_file(f)]
                if skill_matches:
                    # Filter based on outcome
                    filtered_matches = []
                    for f in skill_matches:
                        basename = os.path.basename(f).lower()
                        if is_failure and "failure" not in basename:
                            continue
                        if is_success and "failure" in basename:
                            continue
                        filtered_matches.append(f)
                    
                    if filtered_matches:
                        selected = renpy.random.choice(filtered_matches)
                        renpy.log(f"Found default skill image (filtered): {selected}")
                        return selected
                    else:
                        # If no filtered matches, use any match as fallback
                        selected = renpy.random.choice(skill_matches)
                        renpy.log(f"Found default skill image (fallback): {selected}")
                        return selected
        
        # FALLBACK FOR REST IMAGES: Try "rest" pattern before profile
        if story_image and story_image.startswith("rest_"):
            renpy.log("No specific rest images found, trying generic 'rest' pattern")
            
            # Try worker's rest images (flexible extension matching)
            rest_matches = get_pattern_matches_flexible(base_folder, "rest")
            if rest_matches:
                selected = renpy.random.choice(rest_matches)
                renpy.log(f"Found worker rest image: {selected}")
                return selected
            
            # Try default rest images (flexible extension matching)
            default_rest_matches = get_pattern_matches_flexible(default_folder, "rest")
            if default_rest_matches:
                selected = renpy.random.choice(default_rest_matches)
                renpy.log(f"Found default rest image: {selected}")
                return selected
        
        # FALLBACK TO PROFILE IMAGE
        renpy.log("No specific images found, falling back to profile image")
        
        # Try worker's profile image (flexible extension matching)
        profile_matches = get_pattern_matches_flexible(base_folder, "profile")
        profile_matches = [f for f in profile_matches if _worker_allows_profile_variant(worker, f)]
        if profile_matches:
            selected = renpy.random.choice(profile_matches)
            renpy.log(f"Found worker profile image: {selected}")
            return selected
        
        # Try default profile image (flexible extension matching)
        default_profile_matches = get_pattern_matches_flexible(default_folder, "profile")
        default_profile_matches = [f for f in default_profile_matches if _worker_allows_profile_variant(worker, f)]
        if default_profile_matches:
            selected = renpy.random.choice(default_profile_matches)
            renpy.log(f"Found default profile image: {selected}")
            return selected
        
        # If no profile image exists, return None
        renpy.log("No profile images found for worker")
        return None


    def _resolve_event_media_name(media_name):
        """Resolve event media from short name or explicit path."""
        if not media_name:
            return None

        valid_exts = (".png", ".jpg", ".jpeg", ".webp", ".webm", ".mp4")

        # Explicit file path.
        if isinstance(media_name, str) and media_name.startswith("images/"):
            return media_name if renpy.loadable(media_name) else None

        # Some data may already contain a loadable relative path.
        if renpy.loadable(media_name):
            return media_name

        lower_name = str(media_name).lower()
        target_base = str(media_name)
        has_known_ext = False
        for ext in valid_exts:
            if lower_name.endswith(ext):
                has_known_ext = True
                target_base = str(media_name)[: -len(ext)]
                break

        if has_known_ext:
            event_candidate = f"images/events/{media_name}"
            if renpy.loadable(event_candidate):
                return event_candidate
            root_candidate = f"images/{media_name}"
            if renpy.loadable(root_candidate):
                return root_candidate

        for media_ext in valid_exts:
            event_candidate = f"images/events/{target_base}{media_ext}"
            if renpy.loadable(event_candidate):
                return event_candidate
            root_candidate = f"images/{target_base}{media_ext}"
            if renpy.loadable(root_candidate):
                return root_candidate

        return None

    def _resolve_worker_media_name(worker, media_name):
        """
        Resolve a media name inside the selected worker folder only.
        Returns None if no worker-specific media exists.
        """
        if not worker or not media_name:
            return None

        fallback = get_fallback_folder(worker)
        worker_folder = worker.get("folder", fallback) if hasattr(worker, "get") else fallback
        base_folder = f"images/workers/{worker_folder}/"

        # Exact base-name matches first.
        matches = get_image_matches_flexible(base_folder, media_name)
        if matches:
            selected = renpy.random.choice(matches)
            renpy.log(f"Using worker-specific media (exact): {selected}")
            return selected

        # Then allow pattern matches (numbered variants, etc.).
        pattern_matches = get_pattern_matches_flexible(base_folder, media_name)
        if pattern_matches:
            selected = renpy.random.choice(pattern_matches)
            renpy.log(f"Using worker-specific media (pattern): {selected}")
            return selected

        return None

    def _resolve_worker_skill_media_name(worker, skill_name, outcome):
        """
        Resolve worker-folder media by skill name with trait-aware priority.
        This is used for event success/failure fallback when explicit success/failure
        media is missing in the worker folder.
        """
        if not worker or not skill_name:
            return None

        # "building_skill" is not a worker personal skill image lookup.
        if str(skill_name).strip().lower() == "building_skill":
            return None

        fallback = get_fallback_folder(worker)
        worker_folder = worker.get("folder", fallback) if hasattr(worker, "get") else fallback
        base_folder = f"images/workers/{worker_folder}/"

        is_success = outcome in ("success", "critical_success")
        is_failure = outcome in ("failure", "mediocre")

        skill_name_for_search = get_skill_name_for_images(skill_name)
        skill_patterns = get_skill_search_patterns(skill_name_for_search)
        trait_prefixes = get_trait_prefixes(worker)
        trait_file_prefixes = ("pregnant_", "futa_", "transformed_", "magical_")

        # 1) Trait-specific skill images.
        for skill_pattern_name in skill_patterns:
            for prefix in trait_prefixes:
                if is_failure:
                    failure_pattern = f"{prefix}_{skill_pattern_name}_failure"
                    failure_matches = get_pattern_matches_flexible(base_folder, failure_pattern)
                    if failure_matches:
                        selected = renpy.random.choice(failure_matches)
                        renpy.log(f"Using worker trait-skill failure media: {selected}")
                        return selected
                elif is_success:
                    success_pattern = f"{prefix}_{skill_pattern_name}"
                    success_matches = get_pattern_matches_flexible(base_folder, success_pattern, exclude_failure=True)
                    if success_matches:
                        selected = renpy.random.choice(success_matches)
                        renpy.log(f"Using worker trait-skill success media: {selected}")
                        return selected

                general_pattern = f"{prefix}_{skill_pattern_name}"
                general_matches = get_pattern_matches_flexible(base_folder, general_pattern)
                if general_matches:
                    filtered_matches = []
                    for f in general_matches:
                        basename = os.path.basename(f).lower()
                        if is_failure and "failure" not in basename:
                            continue
                        if is_success and "failure" in basename:
                            continue
                        filtered_matches.append(f)
                    if filtered_matches:
                        selected = renpy.random.choice(filtered_matches)
                        renpy.log(f"Using worker trait-skill filtered media: {selected}")
                        return selected

        # 2) Non-trait skill images (explicitly excluding trait-prefixed files).
        for skill_pattern_name in skill_patterns:
            if is_failure:
                failure_pattern = f"{skill_pattern_name}_failure"
                failure_matches = get_pattern_matches_flexible(base_folder, failure_pattern)
                failure_matches = [f for f in failure_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns)]
                if failure_matches:
                    selected = renpy.random.choice(failure_matches)
                    renpy.log(f"Using worker skill failure media: {selected}")
                    return selected
            elif is_success:
                success_matches = get_pattern_matches_flexible(base_folder, skill_pattern_name, exclude_failure=True)
                success_matches = [f for f in success_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns)]
                if success_matches:
                    selected = renpy.random.choice(success_matches)
                    renpy.log(f"Using worker skill success media: {selected}")
                    return selected

            general_matches = get_pattern_matches_flexible(base_folder, skill_pattern_name)
            general_matches = [f for f in general_matches if not should_exclude_trait_file(f, trait_file_prefixes, skill_patterns)]
            if general_matches:
                filtered_matches = []
                for f in general_matches:
                    basename = os.path.basename(f).lower()
                    if is_failure and "failure" not in basename:
                        continue
                    if is_success and "failure" in basename:
                        continue
                    filtered_matches.append(f)
                if filtered_matches:
                    selected = renpy.random.choice(filtered_matches)
                    renpy.log(f"Using worker skill filtered media: {selected}")
                    return selected

        return None

    def get_event_background(event, outcome=None, worker=None, skill_name=None):
        """
        Get event scene media with this priority:
        1) Initial event display: background_image from events folder.
        2) Resolved success/failure with selected worker: worker-folder success/failure image.
        3) Fallback to events folder success/failure.
        4) Fallback to generic event_bg.
        """
        outcome = outcome.lower() if outcome else ""

        # Outcome-specific image keys from event JSON.
        if outcome in ("success", "critical_success"):
            media_name = event.get("success_image") or event.get("success_background")
        elif "failure" in outcome or outcome == "mediocre":
            media_name = event.get("failure_image") or event.get("failure_background")
        else:
            media_name = event.get("background_image")

        # For resolved outcomes with a selected worker, prefer worker-folder media first.
        if worker and hasattr(worker, "get") and outcome in ("success", "critical_success", "failure", "mediocre"):
            worker_media = _resolve_worker_media_name(worker, media_name)
            if worker_media:
                return worker_media

            # If explicit success/failure media is missing in worker folder, try skill media.
            if skill_name:
                worker_skill_media = _resolve_worker_skill_media_name(worker, skill_name, outcome)
                if worker_skill_media:
                    return worker_skill_media

        # Fallback to global event media (images/events, then images root).
        resolved = _resolve_event_media_name(media_name)
        if resolved:
            renpy.log(f"Using resolved event media: {resolved}")
            return resolved

        # Generic fallback chain.
        generic_name = "generic_success" if outcome in ("success", "critical_success") else ("generic_failure" if ("failure" in outcome or outcome == "mediocre") else "event_bg")
        resolved_generic = _resolve_event_media_name(generic_name)
        if resolved_generic:
            renpy.log(f"Using generic event media fallback: {resolved_generic}")
            return resolved_generic

        renpy.log(f"Using default event background: {event_bg}")
        return event_bg

    def get_image_matches_flexible(base_folder, image_name, exclude_failure=False):
        """
        Get image/video matches for a given media name, allowing different extensions.
        For example, searching for "Profile.jpg" will match "Profile.png", "Profile.webm", "Profile (2).png", etc.
        
        Supports all Ren'Py media formats: 
        - Images: .png, .jpg, .jpeg, .webp
        - Videos: .webm, .mp4
        """
        # Remove extension if present to get base name
        image_base = os.path.splitext(image_name)[0]
        
        matches = []
        all_files = renpy.list_files()
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.webm', '.mp4')
        
        for f in all_files:
            if f.startswith(base_folder):
                filename = os.path.basename(f)
                file_base = os.path.splitext(filename)[0]
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Only consider files with valid media extensions
                if file_ext not in valid_extensions:
                    continue
                
                # Check if the base names match (case insensitive)
                if file_base.lower() == image_base.lower():
                    if exclude_failure and "failure" in filename.lower():
                        continue
                    matches.append(f)
                # Also check for numbered variations like "Profile (2)"
                elif file_base.lower().startswith(image_base.lower() + " ("):
                    if exclude_failure and "failure" in filename.lower():
                        continue
                    matches.append(f)
        
        return matches

    def get_pattern_matches_flexible(base_folder, pattern, exclude_failure=False):
        """
        Get image/video matches for a pattern within filename, allowing different extensions.
        For example, searching for "human_Profile" will match any file containing that pattern.
        
        This is for trait-prefixed searches and skill searches.
        """
        matches = []
        all_files = renpy.list_files()
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.webm', '.mp4')
        
        # Debug logging for troubleshooting
        if "Android" in base_folder or pattern == "profile":
            files_in_folder = [f for f in all_files if f.startswith(base_folder)]
            renpy.log(f"DEBUG get_pattern_matches_flexible:")
            renpy.log(f"  Base folder: {base_folder}")
            renpy.log(f"  Pattern: {pattern}")
            renpy.log(f"  Files in folder: {len(files_in_folder)}")
            if len(files_in_folder) > 0 and len(files_in_folder) < 10:
                renpy.log(f"  First few files: {files_in_folder[:5]}")
        
        for f in all_files:
            if f.startswith(base_folder):
                filename = os.path.basename(f)
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Only consider files with valid media extensions
                if file_ext not in valid_extensions:
                    continue
                
                # Check if pattern is in filename (case insensitive)
                if pattern.lower() in filename.lower():
                    if exclude_failure and "failure" in filename.lower():
                        continue
                    # When searching for generic "rest", exclude rest_* subtypes (rest_libido, rest_brothel, etc.)
                    if pattern.lower() == "rest" and filename.lower().startswith("rest_"):
                        continue
                    matches.append(f)
        
        return matches

    def show_event_flags():
        """Display a notification with current event flags and occurrences for debugging purposes"""
        flag_strings = []

        # Add safety checks: ensure the dictionaries exist before iterating
        if not hasattr(store, "event_flags"):
            store.event_flags = {}
        if not hasattr(store, "event_occurrences"):
            store.event_occurrences = {}
        if not hasattr(store, "event_last_occurred"):
            store.event_last_occurred = {}

        # Add regular event flags
        for flag, value in store.event_flags.items():
            flag_strings.append(f"{flag}: {value}")

        # Add event occurrences
        for event_id, count in store.event_occurrences.items():
            flag_strings.append(f"occurrence: {event_id}: {count}")
            
        # Add event last occurrence times
        current_total_days = calculate_total_days()
        for event_id, last_day in store.event_last_occurred.items():
            days_since = current_total_days - last_day
            flag_strings.append(f"last_occurred: {event_id}: {days_since} days ago")

        if not flag_strings:
            renpy.notify("No event flags or occurrences are set")
            # Explicitly return None (or just use 'return')
            return None

        flags_str = "\n".join(flag_strings)
        renpy.notify(f"Current event flags and occurrences:\n{flags_str}")
        # Explicitly return None (or just use 'return')
        return None

