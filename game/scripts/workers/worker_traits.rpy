init python:
    import random
    import renpy.store as store
    import json
    import os

    def _extract_traits_from_data(traits_data, source_name):
        """Normalize a JSON payload into a list of trait dicts."""
        traits_get = getattr(traits_data, "get", None)
        if callable(traits_get):
            extracted = traits_get("traits", [])
            return list(extracted) if extracted else []
        if isinstance(traits_data, (list, tuple)):
            return list(traits_data)
        if hasattr(traits_data, "__iter__") and not isinstance(traits_data, (str, bytes)):
            try:
                return list(traits_data)
            except Exception:
                pass
        renpy.log(f"TRAITS: {source_name} has unexpected type: {type(traits_data)}")
        return []

    def _load_traits_from_file(file_path):
        """Load traits from a single JSON file. Tries renpy.file() first (as worker_loader), then disk fallback."""
        renpy_err = None
        try:
            with renpy.file(file_path) as f:
                traits_data = json.loads(f.read().decode("utf-8"))
            return _extract_traits_from_data(traits_data, file_path)
        except Exception as e:
            renpy_err = e
        try:
            disk_path = os.path.join(renpy.config.gamedir, file_path.replace("/", os.sep))
            with open(disk_path, "r", encoding="utf-8") as f:
                traits_data = json.load(f)
            return _extract_traits_from_data(traits_data, file_path)
        except Exception as e:
            renpy.log(f"TRAITS: Failed to load {file_path}: renpy.file={renpy_err!r}, disk={e!r}")
            return []

    def _discover_trait_files():
        """Discover trait files using Ren'Py's file API (same approach as worker_loader).
        Uses renpy.list_files() so traits are found regardless of project layout or gamedir."""
        traits_prefix = "data/traits/"
        _gcfl = getattr(store, "get_cached_file_list", None)
        all_files = _gcfl() if callable(_gcfl) else (renpy.list_files() if hasattr(renpy, 'list_files') else [])
        discovered = sorted([
            f for f in all_files
            if f.startswith(traits_prefix) and f.endswith(".json")
        ])
        if not discovered:
            disk_dir = os.path.join(renpy.config.gamedir, "data", "traits")
            if os.path.isdir(disk_dir):
                for filename in sorted(os.listdir(disk_dir)):
                    if filename.endswith(".json"):
                        discovered.append(f"data/traits/{filename}")
                renpy.log(f"TRAITS: Fallback disk discovery found {len(discovered)} files in {disk_dir}")
        if discovered:
            renpy.log(f"TRAITS: Discovered {len(discovered)} trait files: {discovered}")
        return discovered

    def _is_valid_trait_definition(trait, source_name):
        """Validate minimum runtime shape for trait definitions."""
        trait_get = getattr(trait, "get", None)
        if not callable(trait_get):
            renpy.log(f"TRAITS: Ignoring non-dict trait in {source_name}: {type(trait)}")
            return False
        trait_name = trait_get("name")
        if not isinstance(trait_name, str) or not trait_name.strip():
            renpy.log(f"TRAITS: Ignoring trait without valid 'name' in {source_name}")
            return False
        return True

    def _build_trait_caches():
        """Build filtered and raw trait caches from disk-backed JSON files."""
        nsfw_enabled = getattr(persistent, "nsfw_enabled", False)
        raw_traits = []
        filtered_traits = []
        raw_cache = {}
        filtered_cache = {}
        seen_names = set()

        for trait_file in _discover_trait_files():
            for trait in _load_traits_from_file(trait_file):
                if not _is_valid_trait_definition(trait, trait_file):
                    continue
                trait_name = trait.get("name")
                if trait_name in seen_names:
                    renpy.log(f"TRAITS: Duplicate trait name '{trait_name}' in {trait_file}; keeping first definition")
                    continue
                seen_names.add(trait_name)
                raw_traits.append(trait)
                raw_cache[trait_name] = trait
                if nsfw_enabled or not trait.get("nsfw", False):
                    filtered_traits.append(trait)
                    filtered_cache[trait_name] = trait

        if not raw_traits:
            legacy_file = "data/traits.json"
            for trait in _load_traits_from_file(legacy_file):
                if not _is_valid_trait_definition(trait, legacy_file):
                    continue
                trait_name = trait.get("name")
                if trait_name in seen_names:
                    renpy.log(f"TRAITS: Duplicate trait name '{trait_name}' in legacy file; keeping first definition")
                    continue
                seen_names.add(trait_name)
                raw_traits.append(trait)
                raw_cache[trait_name] = trait
                if nsfw_enabled or not trait.get("nsfw", False):
                    filtered_traits.append(trait)
                    filtered_cache[trait_name] = trait

        return raw_traits, filtered_traits, raw_cache, filtered_cache

    def load_traits():
        """Load traits from data/traits/*.json with legacy fallback."""
        _, filtered_traits, _, _ = _build_trait_caches()
        return filtered_traits

    def refresh_traits_cache(force=False):
        """Reload and cache traits list + lookup map."""
        global traits_list
        raw_traits, filtered_traits, raw_cache, filtered_cache = _build_trait_caches()
        traits_list = filtered_traits
        store._trait_name_set = set(filtered_cache.keys())
        store._trait_def_cache = filtered_cache
        store._trait_def_raw_cache = raw_cache
        store._trait_list_raw = raw_traits
        if traits_list:
            renpy.log(f"TRAITS: Cache loaded with {len(traits_list)} traits (filtered), {len(raw_traits)} raw")
        return traits_list

    def get_all_traits():
        """Return trait definitions from cache. Use store (not globals) so ensure_worker_defaults sees it."""
        cached = getattr(store, "_trait_def_cache", None)
        if hasattr(cached, "get") and cached:
            return list(cached.values())
        return refresh_traits_cache(force=True) or []

    def get_trait_definition(trait_name):
        """Return trait definition by name."""
        if not trait_name:
            return None
        cache = getattr(store, "_trait_def_cache", {})
        raw_cache = getattr(store, "_trait_def_raw_cache", {})
        if not cache and not raw_cache:
            refresh_traits_cache(force=True)
            cache = getattr(store, "_trait_def_cache", {})
            raw_cache = getattr(store, "_trait_def_raw_cache", {})

        return cache.get(trait_name) or raw_cache.get(trait_name)

    # Lazy load: don't load at init (renpy.file/open can fail during init phase).
    # First get_all_traits/refresh call will load - happens when load_workers runs (runtime).
    traits_list = []
    store.load_traits = load_traits
    store.refresh_traits_cache = refresh_traits_cache
    store.get_all_traits = get_all_traits
    store.get_trait_definition = get_trait_definition

    def get_trait_desc(trait_name):
        """Get the description of a trait by name."""
        trait_def = get_trait_definition(trait_name)
        if trait_def:
            return trait_def.get("description", "No description available")
        return "No description available"

    def can_assign_trait_to_worker(trait, worker):
        """Check if a trait can be assigned to a worker based on gender restrictions."""
        gender_restriction = trait.get("gender_restriction", None)
        if gender_restriction:
            worker_gender = (worker.get("gender") or "").strip().lower()
            if worker_gender != str(gender_restriction).strip().lower():
                return False
        return True

    def trait_conflicts_with_worker(trait, worker_traits, cache=None):
        """Return True if trait conflicts with any of worker's existing traits."""
        cache = cache or getattr(store, "_trait_def_cache", {})
        for existing_name in (worker_traits or []):
            existing_def = cache.get(existing_name) if hasattr(cache, "get") else None
            if existing_def and trait.get("name") in existing_def.get("conflicts", []):
                return True
            if trait.get("name") and existing_name in trait.get("conflicts", []):
                return True
        return False

    def worker_meets_trait_requirements(trait, worker_traits):
        """Return True if worker has all traits required by this trait (requires_traits)."""
        required = trait.get("requires_traits")
        if not required:
            return True
        if isinstance(required, str):
            required = [required]
        elif not isinstance(required, (list, tuple)):
            return True
        worker_set = set(worker_traits or [])
        return all(r in worker_set for r in required if isinstance(r, str))

    def sanitize_worker_trait_state(worker, trait_catalog=None):
        """
        Normalize and validate a worker trait list in-place.
        - Removes duplicates
        - Removes known traits that fail gender restrictions
        - Removes known traits whose requires_traits are missing
        - Resolves conflicts by preserving earlier traits and dropping later ones
        Unknown traits are preserved.
        """
        if not hasattr(worker, "get"):
            return []

        raw_traits = worker.get("traits") or []
        if isinstance(raw_traits, str):
            normalized = [raw_traits] if raw_traits else []
        elif hasattr(raw_traits, "__iter__"):
            try:
                normalized = [t for t in list(raw_traits) if isinstance(t, str) and t]
            except Exception:
                normalized = []
        else:
            normalized = []

        trait_map = {}
        if trait_catalog:
            for trait_def in trait_catalog:
                if hasattr(trait_def, "get"):
                    trait_name = trait_def.get("name")
                    if isinstance(trait_name, str) and trait_name and trait_name not in trait_map:
                        trait_map[trait_name] = trait_def
        if not trait_map:
            raw_cache = getattr(store, "_trait_def_raw_cache", None)
            if hasattr(raw_cache, "get") and raw_cache:
                trait_map.update(raw_cache)
            filtered_cache = getattr(store, "_trait_def_cache", None)
            if hasattr(filtered_cache, "get") and filtered_cache:
                for trait_name, trait_def in filtered_cache.items():
                    if trait_name not in trait_map:
                        trait_map[trait_name] = trait_def

        # De-duplicate while preserving order.
        deduped = []
        seen = set()
        for trait_name in normalized:
            if trait_name in seen:
                continue
            seen.add(trait_name)
            deduped.append(trait_name)

        cleaned = list(deduped)
        changed = True
        while changed:
            changed = False
            worker_trait_set = set(cleaned)
            next_traits = []
            for trait_name in cleaned:
                trait_def = trait_map.get(trait_name) if hasattr(trait_map, "get") else None
                if not (hasattr(trait_def, "get") and callable(getattr(trait_def, "get", None))):
                    next_traits.append(trait_name)
                    continue

                if not can_assign_trait_to_worker(trait_def, worker):
                    renpy.log(f"TRAITS: Removing '{trait_name}' from {worker.get('name', 'Unknown')} - gender restriction mismatch")
                    changed = True
                    continue

                if not worker_meets_trait_requirements(trait_def, worker_trait_set):
                    renpy.log(f"TRAITS: Removing '{trait_name}' from {worker.get('name', 'Unknown')} - missing required trait(s)")
                    changed = True
                    continue

                conflicts = trait_def.get("conflicts", [])
                if isinstance(conflicts, str):
                    conflicts = [conflicts]
                elif not hasattr(conflicts, "__iter__"):
                    conflicts = []

                has_conflict = False
                for existing in next_traits:
                    if existing in conflicts:
                        has_conflict = True
                        break
                    existing_def = trait_map.get(existing) if hasattr(trait_map, "get") else None
                    if hasattr(existing_def, "get") and trait_name in (existing_def.get("conflicts", []) or []):
                        has_conflict = True
                        break
                if has_conflict:
                    renpy.log(f"TRAITS: Removing '{trait_name}' from {worker.get('name', 'Unknown')} - conflicts with existing trait")
                    changed = True
                    continue

                next_traits.append(trait_name)

            cleaned = next_traits

        worker["traits"] = cleaned
        return cleaned

    store.can_assign_trait_to_worker = can_assign_trait_to_worker
    store.trait_conflicts_with_worker = trait_conflicts_with_worker
    store.worker_meets_trait_requirements = worker_meets_trait_requirements
    store.sanitize_worker_trait_state = sanitize_worker_trait_state

    def add_trait_with_duration(worker, trait_name, duration, is_variant=False):
        """
        Add a trait to the worker with an optional duration.
        If the trait has conflicts, remove conflicting traits.
        """
        # Return early if worker is None to prevent NoneType errors
        if worker is None:
            renpy.log(f"Cannot add trait '{trait_name}' - worker parameter is None")
            return
            
        # Find the trait definition (traits_list first, then raw cache for event-assigned/NSFW traits)
        trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
        if not trait_def:
            trait_def = get_trait_definition(trait_name)
        if not trait_def:
            renpy.log(f"Cannot add trait '{trait_name}' - trait not found in traits_list or trait cache")
            return

        # Check gender restrictions
        if not can_assign_trait_to_worker(trait_def, worker):
            renpy.log(f"Cannot add trait '{trait_name}' to {worker.get('name', 'Unknown')} - gender restriction not met")
            return

        # Check prerequisite traits (requires_traits)
        if not worker_meets_trait_requirements(trait_def, worker.get("traits") or []):
            missing = [r for r in (trait_def.get("requires_traits") or []) if r not in (worker.get("traits") or [])]
            renpy.log(f"Cannot add trait '{trait_name}' to {worker.get('name', 'Unknown')} - missing required traits: {missing}")
            return

        if "traits" not in worker:
            worker["traits"] = []

        # Remove conflicting traits (use trait_def we already have)
        for conflict in trait_def.get("conflicts", []):
            if conflict in worker["traits"]:
                remove_trait_safe(worker, conflict)

        if trait_name not in worker["traits"]:
            worker["traits"].append(trait_name)

        if duration > 0:
            if "trait_durations" not in worker:
                worker["trait_durations"] = {}
            worker["trait_durations"][trait_name] = duration

        # Keep dependency graph valid (e.g. remove traits that now fail requirements).
        _sanitize = getattr(store, "sanitize_worker_trait_state", None)
        if callable(_sanitize):
            _sanitize(worker)

        # Recalculate trait modifiers
        recalculate_trait_modifiers(worker)

    def remove_trait(worker, trait_name):
        """Remove a trait from the worker."""
        if not worker:
            renpy.log(f"remove_trait: Worker is None, cannot remove trait '{trait_name}'")
            return
        if not trait_name:
            renpy.log(f"remove_trait: Trait name is empty, cannot remove from worker '{worker.get('name', 'Unknown')}'")
            return
        
        worker_traits = worker.get("traits", [])
        if trait_name in worker_traits:
            worker["traits"].remove(trait_name)
            renpy.log(f"Removed trait '{trait_name}' from worker '{worker.get('name', 'Unknown')}'. Remaining traits: {len(worker['traits'])}")
            
            # Remove duration if it exists
            if "trait_durations" in worker and trait_name in worker["trait_durations"]:
                del worker["trait_durations"][trait_name]

            # Removing a prerequisite trait may invalidate dependent traits.
            _sanitize = getattr(store, "sanitize_worker_trait_state", None)
            if callable(_sanitize):
                _sanitize(worker)
            
            # Recalculate trait modifiers
            recalculate_trait_modifiers(worker)
        else:
            renpy.log(f"Trait '{trait_name}' not found in worker '{worker.get('name', 'Unknown')}' traits: {worker_traits}")

    def remove_trait_safe(worker, trait_name):
        """Remove a trait with case-insensitive cleanup of durations."""
        if not worker or not trait_name:
            return
        remove_trait(worker, trait_name)
        removed_any = False
        worker_traits = worker.get("traits", [])
        for existing in list(worker_traits):
            if isinstance(existing, str) and existing.lower() == str(trait_name).lower():
                worker_traits.remove(existing)
                removed_any = True
        if "trait_durations" in worker:
            for key in list(worker["trait_durations"].keys()):
                if isinstance(key, str) and key.lower() == str(trait_name).lower():
                    del worker["trait_durations"][key]
                    removed_any = True
        if removed_any:
            _sanitize = getattr(store, "sanitize_worker_trait_state", None)
            if callable(_sanitize):
                _sanitize(worker)
            recalculate_trait_modifiers(worker)

    def check_trait_durations():
        """
        Called at day transition. Decrements trait_durations for all workers.
        When duration reaches 0, removes the trait and runs on_expire (e.g. add_trait for Badly Burnt -> Scarred).
        """
        workers = getattr(store, "workers", []) or []
        for worker in workers:
            durations = worker.get("trait_durations") or {}
            if not durations:
                continue
            expired = []
            for trait_name, days_left in list(durations.items()):
                new_days = days_left - 1
                if new_days <= 0:
                    expired.append(trait_name)
                else:
                    durations[trait_name] = new_days
            for trait_name in expired:
                trait_def = get_trait_definition(trait_name)
                remove_trait(worker, trait_name)
                if trait_def:
                    on_expire = trait_def.get("on_expire") or {}
                    add_trait_data = on_expire.get("add_trait")
                    if add_trait_data:
                        if hasattr(add_trait_data, "get") and callable(getattr(add_trait_data, "get", None)):
                            entries = [add_trait_data]
                        elif isinstance(add_trait_data, (str, bytes)):
                            entries = [add_trait_data]
                        elif hasattr(add_trait_data, "__iter__"):
                            entries = list(add_trait_data)
                        else:
                            entries = []
                        for entry in entries:
                            if hasattr(entry, "get") and callable(getattr(entry, "get", None)):
                                new_name = entry.get("name") or entry.get("trait")
                                try:
                                    new_duration = int(entry.get("duration", 0) or 0)
                                except Exception:
                                    new_duration = 0
                            elif isinstance(entry, (str, bytes)):
                                new_name = str(entry)
                                new_duration = 0
                            else:
                                new_name = None
                                new_duration = 0
                            if new_name:
                                add_trait_with_duration(worker, new_name, new_duration)
                                renpy.log(f"Trait '{trait_name}' expired for {worker.get('name', 'Unknown')}, applied on_expire: {new_name}")

    store.check_trait_durations = check_trait_durations

    def apply_trait_secondary_modifiers_once(worker):
        """
        Apply trait modifiers to secondary attributes. Uses delta on recalculate to avoid
        double-application when traits are added/removed during play.
        """
        is_recalculating = worker.pop("_recalculating_traits", False)
        if worker.get("_secondary_attributes_initialized", False) and not is_recalculating:
            renpy.log(f"Secondary attributes already initialized for {worker.get('name', 'Unknown')}, skipping")
            return

        # Initialize base values only if attributes don't exist yet
        if "joy" not in worker:
            worker["joy"] = random.randint(20, 80)
        if "rebelliousness" not in worker:
            worker["rebelliousness"] = 50
        if "romance" not in worker:
            worker["romance"] = 0
        if "comfort_level" not in worker:
            worker["comfort_level"] = 1
        if "comfort_desired" not in worker:
            worker["comfort_desired"] = worker.get("comfort_desired", 1)
        if "relationship" not in worker:
            worker["relationship"] = 10 + worker.get("comfort_level", 1)
        if "libido" not in worker:
            worker["libido"] = 10

        # Calculate new total modifiers from current traits
        # rebelliousness: no longer from modifiers (uses daily_effects/daily_effects_random instead)
        new_total = {
            "joy": 0, "rebelliousness": 0, "romance": 0, "comfort_level": 0,
            "comfort_desired": 0, "relationship": 0, "libido": 0
        }
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "modifiers" in trait_def:
                for attr in new_total:
                    if attr == "rebelliousness":
                        continue  # rebelliousness uses daily_effects, not modifiers
                    if attr in trait_def["modifiers"]:
                        new_total[attr] += trait_def["modifiers"][attr]

        last_applied = worker.get("_last_applied_trait_modifiers", {})

        # Old save: has values but no _last - do not modify, only prime _last for future recalculates
        if is_recalculating and not last_applied:
            worker["_last_applied_trait_modifiers"] = dict(new_total)
            worker["_secondary_attributes_initialized"] = True
            renpy.log(f"Secondary attributes: primed _last for {worker.get('name', 'Unknown')} (old save, no changes)")
            return

        for attr in new_total:
            old_val = last_applied.get(attr, 0)
            new_val = new_total[attr]
            delta = new_val - old_val
            if delta == 0:
                continue
            current_value = worker.get(attr, 0)
            set_attribute_with_caps(worker, attr, current_value + delta)

        worker["_last_applied_trait_modifiers"] = dict(new_total)
        worker["_secondary_attributes_initialized"] = True
        renpy.log(f"Secondary attributes initialized for {worker.get('name', 'Unknown')}")

    def recalculate_trait_modifiers(worker):
        """
        Recalculate trait modifiers when traits are added or removed.
        Uses delta (new_total - last_applied) to avoid double-application.
        """
        if "_secondary_attributes_initialized" in worker:
            del worker["_secondary_attributes_initialized"]
        worker["_recalculating_traits"] = True
        try:
            apply_trait_secondary_modifiers_once(worker)
        finally:
            worker.pop("_recalculating_traits", None)

    def get_attribute_cap(worker, attribute):
        """Get the cap for an attribute based on worker's traits and management skills."""
        cap = None
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "attribute_caps" in trait_def and attribute in trait_def["attribute_caps"]:
                trait_cap = trait_def["attribute_caps"][attribute]
                if cap is None or trait_cap < cap:  # Use the most restrictive cap
                    cap = trait_cap
        # Default cap for rebelliousness if no trait defines it
        if attribute == "rebelliousness" and cap is None:
            cap = 100
        # Management skill: Servant Training reduces max Rebelliousness by 10 per point
        if attribute == "rebelliousness":
            mgmt = getattr(store, "management_skills", None) or {}
            cap = max(0, (cap or 100) - 10 * mgmt.get("servant_training", 0))
        return cap

    def get_skill_cap(worker, skill_name):
        """Return the max for a base skill given the worker's traits. Defaults to SKILL_MAX.
        A trait may declare {"skill_caps": {"Clever": 50}}. Most restrictive cap wins."""
        cap = None
        for trait_name in (worker.get("traits") or []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if not trait_def:
                trait_def = get_trait_definition(trait_name)  # NSFW/event-assigned traits live in the raw cache
            if not trait_def:
                continue
            caps = trait_def.get("skill_caps", {})
            if hasattr(caps, "get") and skill_name in caps:
                trait_cap = caps[skill_name]
                if cap is None or trait_cap < cap:
                    cap = trait_cap
        return SKILL_MAX if cap is None else min(SKILL_MAX, cap)

    def get_attribute_minimum(worker, attribute):
        """Get the minimum for an attribute based on worker's traits."""
        minimum = None
        for trait_name in worker.get("traits", []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if trait_def and "attribute_minimums" in trait_def and attribute in trait_def["attribute_minimums"]:
                trait_min = trait_def["attribute_minimums"][attribute]
                if minimum is None or trait_min > minimum:  # Use the highest minimum
                    minimum = trait_min
        return minimum

    def set_attribute_with_caps(worker, attribute, value):
        """Set an attribute value while respecting caps and minimums from traits."""
        # Apply trait-based caps
        cap = get_attribute_cap(worker, attribute)
        
        # Apply default caps if no trait cap is defined
        if cap is None:
            if attribute == "joy":
                cap = 100
            elif attribute == "rebelliousness":
                cap = 100
            elif attribute == "romance":
                cap = 100
            elif attribute == "relationship":
                cap = 100
        
        if cap is not None and value > cap:
            value = cap
            if get_attribute_cap(worker, attribute) is not None:
                renpy.log(f"Capped {attribute} at {cap} for {worker.get('name', 'Unknown')} due to trait restrictions")
            else:
                renpy.log(f"Capped {attribute} at {cap} for {worker.get('name', 'Unknown')} (default maximum)")
        
        # Apply trait-based minimums
        minimum = get_attribute_minimum(worker, attribute)
        
        # Handle special case for libido overflow before applying minimums
        # NOTE: "Overflow" here means libido going BELOW 0 (negative), not excess over max (e.g. 35/20).
        if attribute == "libido" and value < 0:
            if persistent.nsfw_enabled:
                # Handle overflow: add abs(negative value) to rebelliousness and reset libido to minimum or 0
                overflow_amount = abs(value)
                current_rebelliousness = worker.get("rebelliousness", 50)
                new_rebelliousness = current_rebelliousness + overflow_amount
                worker["rebelliousness"] = min(100, new_rebelliousness)  # Cap at 100
                worker["libido"] = minimum if minimum is not None else 0
                renpy.log(f"Libido overflow for {worker.get('name', 'Unknown')}: +{overflow_amount} rebelliousness, libido set to {worker['libido']}")
                return  # Don't continue with normal processing
            else:
                value = 0
        
        # Apply general minimum values (including trait minimums)
        if attribute == "joy" and value < 0:
            value = 0
        elif attribute == "rebelliousness" and value < 0:
            value = 0
        elif attribute == "relationship" and value < 0:
            value = 0
        elif attribute == "romance" and value < 0:
            value = 0
        elif attribute == "libido" and value < 0:
            value = 0
        
        # Apply trait minimums (overrides general minimums)
        if minimum is not None and value < minimum:
            value = minimum
            renpy.log(f"Applied minimum {attribute} of {minimum} for {worker.get('name', 'Unknown')} due to trait restrictions")

        # Dynamic maximum for libido based on traits/items
        if attribute == "libido":
            try:
                max_lib = get_max_libido(worker)
                if value > max_lib:
                    value = max_lib
                    renpy.log(f"Clamped libido to dynamic max {max_lib} for {worker.get('name', 'Unknown')}")
            except Exception:
                pass
            
        worker[attribute] = value

    def apply_attribute_change(worker, attribute, change):
        """Apply a change to an attribute while respecting caps."""
        current_value = worker.get(attribute, 0)
        new_value = current_value + change
        set_attribute_with_caps(worker, attribute, new_value)

    def deduplicate_traits(worker):
        """
        Remove duplicate traits from a worker's traits list.
        Preserves the order of first occurrence.
        """
        if "traits" not in worker or not worker["traits"]:
            return
        
        seen = set()
        deduplicated = []
        for trait_name in worker["traits"]:
            if trait_name not in seen:
                seen.add(trait_name)
                deduplicated.append(trait_name)
        
        if len(deduplicated) != len(worker["traits"]):
            removed_count = len(worker["traits"]) - len(deduplicated)
            renpy.log(f"Removed {removed_count} duplicate trait(s) from {worker.get('name', 'Unknown')}")
            worker["traits"] = deduplicated
            # Recalculate modifiers after deduplication
            recalculate_trait_modifiers(worker)

    def ensure_minimum_traits(worker, min_traits=3, max_traits=5):
        """Ensure worker has minimum number of traits, adding random ones if needed."""
        # Unique story workers (Yvara, the Lanista, Aelis...) must keep exactly their
        # authored traits: random backfill contradicted the design (the Lanista ships
        # with a single trait on purpose).
        if worker.get("unique", False):
            return
        if not worker.get("traits"):
            worker["traits"] = []
        
        current_count = len(worker["traits"])
        if current_count >= min_traits:
            return  # Already has enough traits
        
        # Use traits_list; fallback to store._trait_def_cache if traits_list is empty
        trait_source = traits_list if traits_list else []
        if not trait_source:
            cache = getattr(store, "_trait_def_cache", None)
            if hasattr(cache, "get") and cache:
                trait_source = list(cache.values())
        if not trait_source:
            renpy.log(f"TRAITS: No trait source available for {worker.get('name', 'Unknown')}; skipping backfill")
            return

        target_count = random.randint(min_traits, max_traits)
        traits_to_add = target_count - current_count
        
        renpy.log(f"Adding {traits_to_add} traits to {worker.get('name', 'Unknown')} (current: {current_count}, target: {target_count})")
        
        # Get possible traits (excluding only_assigned and respecting NSFW settings)
        # Option: only_traits_without_requirements → only traits with no gender_restriction
        only_no_reqs = getattr(persistent, "only_traits_without_requirements", False)
        possible_traits = [
            t for t in trait_source
            if not t.get("only_assigned", False)
            and (persistent.nsfw_enabled or not t.get("nsfw", False))
            and t["name"] not in worker["traits"]
            and (not only_no_reqs or not t.get("gender_restriction"))
            and worker_meets_trait_requirements(t, worker["traits"])
        ]
        random.shuffle(possible_traits)
        
        added_count = 0
        attempts = 0
        max_attempts = 100
        
        while added_count < traits_to_add and attempts < max_attempts:
            attempts += 1
            if not possible_traits:
                break  # Pool exhausted (all added/filtered out) - avoid random.choice IndexError
            trait = random.choice(possible_traits)
            trait_name = trait["name"]
            
            # Check gender restriction
            if not can_assign_trait_to_worker(trait, worker):
                continue
            # Check requires_traits (e.g. Psychic requires Magical)
            if not worker_meets_trait_requirements(trait, worker["traits"]):
                continue

            # Check conflicts with existing traits
            conflicts = False
            for existing_trait_name in worker["traits"]:
                existing_trait = next((t for t in trait_source if t["name"] == existing_trait_name), None)
                if existing_trait:
                    if trait_name in existing_trait.get("conflicts", []):
                        conflicts = True
                        break
                    if existing_trait_name in trait.get("conflicts", []):
                        conflicts = True
                        break
            
            if not conflicts and trait_name not in worker["traits"]:
                worker["traits"].append(trait_name)
                added_count += 1
                renpy.log(f"Added trait '{trait_name}' to {worker.get('name', 'Unknown')}")
                
                # Remove from possible traits to avoid duplicates
                possible_traits = [t for t in possible_traits if t["name"] != trait_name]
        
        if added_count > 0:
            renpy.log(f"Successfully added {added_count} traits to {worker.get('name', 'Unknown')}")
            # Recalculate modifiers after adding traits
            recalculate_trait_modifiers(worker)
        else:
            renpy.log(f"Could not add any traits to {worker.get('name', 'Unknown')} - no suitable traits available")

    store.ensure_minimum_traits = ensure_minimum_traits

