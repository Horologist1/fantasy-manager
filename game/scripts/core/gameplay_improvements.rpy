# gameplay_improvements.rpy
# Pure/state helpers for automation, batch management, building policy,
# event-linked worker history. UI lives in gameplay_improvements_ui.rpy.

# Screen prediction imports are centralized in python_package_preload.rpy.

init python:
    from fm_performance.reporting import daily_report_story_positions, format_skill_level_badges, report_page_window
    from fm_roster.selection import page_worker_choices, rank_worker_choices

    if not hasattr(store, "batch_selected_worker_names"):
        store.batch_selected_worker_names = []
    if not hasattr(store, "batch_allowed_worker_names"):
        store.batch_allowed_worker_names = []
    if not hasattr(store, "auto_advance_summary"):
        store.auto_advance_summary = {}
    if not hasattr(store, "auto_advance_day_reports"):
        store.auto_advance_day_reports = []
    # Roster QoL. worker_roster_sort_mode is cosmetic (not snapshotted; resets on
    # load). assignment_presets MUST be persisted via _build/_apply_snapshot in
    # save_snapshot.rpy (rollback disabled -> defaults don't survive load).
    if not hasattr(store, "worker_roster_sort_mode"):
        store.worker_roster_sort_mode = "default"
    if not hasattr(store, "assignment_presets"):
        store.assignment_presets = {}

    def _normalized_skill_name(skill_name):
        return str(skill_name or "").strip().lower()

    def get_building_policy_skills(building, btype):
        """Return exact skill names that can block an unlocked daily story."""
        names = {}
        if not btype or not hasattr(btype, "get"):
            return []
        for profession in btype.get("professions", []) or []:
            if not profession_is_unlocked(profession) or not profession_is_visible(profession, btype):
                continue
            for story in profession.get("daily_stories", []) or []:
                if not getattr(persistent, "nsfw_enabled", False) and content_object_is_restricted(story):
                    continue
                for skill_name in story.get("skill_options", []) or []:
                    clean = str(skill_name or "").strip()
                    if clean:
                        names[_normalized_skill_name(clean)] = clean
        return sorted(names.values(), key=lambda value: value.lower())

    def get_building_banned_skill_genders(building, skill_name):
        """Return male/female targets; old banned_skills entries remain global."""
        if not building or not hasattr(building, "get"):
            return []
        key = _normalized_skill_name(skill_name)
        if not key:
            return []
        if any(_normalized_skill_name(value) == key for value in (building.get("banned_skills", []) or [])):
            return ["male", "female"]

        rules = building.get("banned_skills_by_gender", {}) or {}
        if not hasattr(rules, "items"):
            return []
        raw_genders = None
        for stored_skill, stored_genders in rules.items():
            if _normalized_skill_name(stored_skill) == key:
                raw_genders = stored_genders
                break
        if raw_genders is None:
            return []
        if hasattr(raw_genders, "get"):
            raw_genders = raw_genders.get("genders", [])
        if isinstance(raw_genders, str):
            raw_genders = [raw_genders]
        normalized = {str(value or "").strip().lower() for value in (raw_genders or [])}
        if "both" in normalized or "all" in normalized:
            normalized.update(("male", "female"))
        return [gender for gender in ("male", "female") if gender in normalized]

    def get_building_banned_skills(building, worker_gender=None):
        if not building or not hasattr(building, "get"):
            return []
        result = []
        seen = set()
        candidates = list(building.get("banned_skills", []) or [])
        rules = building.get("banned_skills_by_gender", {}) or {}
        if hasattr(rules, "keys"):
            candidates.extend(rules.keys())
        normalized_gender = str(worker_gender or "").strip().lower()
        for skill_name in candidates:
            clean = str(skill_name or "").strip()
            key = _normalized_skill_name(clean)
            if not clean or key in seen:
                continue
            genders = get_building_banned_skill_genders(building, clean)
            if normalized_gender in ("male", "female") and normalized_gender not in genders:
                continue
            if genders:
                result.append(clean)
                seen.add(key)
        return result

    def set_building_banned_skill_mode(building, skill_name, mode):
        """Set one skill to allowed/male/female/both using an additive save schema."""
        if not building or not hasattr(building, "get"):
            return "allowed"
        clean = str(skill_name or "").strip()
        key = _normalized_skill_name(clean)
        if not key:
            return "allowed"
        normalized_mode = str(mode or "allowed").strip().lower()
        genders = {
            "male": ["male"],
            "female": ["female"],
            "both": ["male", "female"],
        }.get(normalized_mode, [])

        building["banned_skills"] = [
            value for value in (building.get("banned_skills", []) or [])
            if _normalized_skill_name(value) != key
        ]
        rules = dict(building.get("banned_skills_by_gender", {}) or {})
        for stored_skill in list(rules.keys()):
            if _normalized_skill_name(stored_skill) == key:
                del rules[stored_skill]
        if genders:
            rules[clean] = list(genders)
        building["banned_skills_by_gender"] = rules
        return normalized_mode if genders else "allowed"

    def cycle_building_banned_skill_mode(building, skill_name):
        genders = get_building_banned_skill_genders(building, skill_name)
        if not genders:
            next_mode = "male"
        elif genders == ["male"]:
            next_mode = "female"
        elif genders == ["female"]:
            next_mode = "both"
        else:
            next_mode = "allowed"
        return set_building_banned_skill_mode(building, skill_name, next_mode)

    def toggle_building_banned_skill(building, skill_name):
        """Legacy two-state API: toggle a skill between allowed and banned for both genders."""
        current = get_building_banned_skill_genders(building, skill_name)
        mode = "allowed" if current == ["male", "female"] else "both"
        return set_building_banned_skill_mode(building, skill_name, mode) != "allowed"

    def story_allowed_by_building_policy(building, story, worker_gender=None):
        """Block a story when any listed skill is banned for the acting worker's gender."""
        banned = {_normalized_skill_name(value) for value in get_building_banned_skills(building, worker_gender)}
        if not banned or not story or not hasattr(story, "get"):
            return True
        story_skills = {_normalized_skill_name(value) for value in (story.get("skill_options", []) or [])}
        return not bool(banned.intersection(story_skills))

    def get_building_policy_focus_bonus(building, btype=None, worker_gender=None):
        """Return +2 per relevant ban for this worker gender, capped at +10."""
        banned = {_normalized_skill_name(value) for value in get_building_banned_skills(building, worker_gender)}
        if btype is not None:
            relevant = {_normalized_skill_name(value) for value in get_building_policy_skills(building, btype)}
            banned = banned.intersection(relevant)
        return min(10, len(banned) * 2)

    def get_building_policy_tradeoff(building, btype):
        blocked_services = []
        for skill_name in get_building_policy_skills(building, btype):
            genders = get_building_banned_skill_genders(building, skill_name)
            if genders:
                blocked_services.append({"skill": skill_name, "genders": list(genders)})
        count = len(blocked_services)
        return {
            "banned_count": count,
            "blocked_services": blocked_services,
            "focus_bonus": get_building_policy_focus_bonus(building, btype),
            "male_focus_bonus": get_building_policy_focus_bonus(building, btype, "male"),
            "female_focus_bonus": get_building_policy_focus_bonus(building, btype, "female"),
            "incident_chance": min(0.25, 0.05 * count),
            "money_loss": 0,
            "reputation_loss": 0,
        }

    def apply_building_policy_incident(building, btype, building_name):
        tradeoff = get_building_policy_tradeoff(building, btype)
        if tradeoff["banned_count"] <= 0:
            return None

        assigned_workers = [
            worker for worker in (building.get("assigned_servants", []) or [])
            if hasattr(worker, "get") and worker.get("name")
        ]
        assigned_jobs = building.get("servant_jobs", {}) or {}
        candidates = []
        for request in tradeoff["blocked_services"]:
            requested_skill_key = _normalized_skill_name(request["skill"])
            for profession in (btype or {}).get("professions", []) or []:
                if not profession_is_unlocked(profession) or not profession_is_visible(profession, btype):
                    continue
                profession_offers_skill = any(
                    requested_skill_key in {_normalized_skill_name(value) for value in (story.get("skill_options", []) or [])}
                    for story in (profession.get("daily_stories", []) or [])
                    if getattr(persistent, "nsfw_enabled", False) or not content_object_is_restricted(story)
                )
                if not profession_offers_skill:
                    continue
                profession_id = str(profession.get("id", "")).strip().lower()
                for worker in assigned_workers:
                    worker_name = worker.get("name")
                    worker_gender = str(worker.get("gender", "")).strip().lower()
                    worker_job = str(assigned_jobs.get(worker_name, "")).strip().lower()
                    if worker_job == profession_id and worker_gender in request["genders"]:
                        candidates.append({
                            "skill": request["skill"],
                            "gender": worker_gender,
                            "worker": worker,
                            "profession": profession,
                        })

        eligible_skill_count = len({_normalized_skill_name(candidate["skill"]) for candidate in candidates})
        incident_chance = min(0.25, 0.05 * eligible_skill_count)
        if not candidates or random.random() >= incident_chance:
            return None
        request = random.choice(candidates)
        requested_skill = request["skill"]
        requested_gender = request["gender"]
        reserved_worker = request["worker"]
        reserved_profession = request["profession"]
        description = (
            "A customer reserved %s and asked for %s, but this building's policy does not offer that service through a %s worker. "
            "No sale was made; the venue's specialist reputation was unaffected."
        ) % (reserved_worker.get("name"), requested_skill, requested_gender)
        story = {
            "id": "policy_unavailable_service",
            "report": "Missed Service Request",
            "description": description,
            "requested_skill": requested_skill,
            "requested_worker_gender": requested_gender,
            "reserved_worker_name": reserved_worker.get("name"),
            "reputation_change": 0,
            "nsfw_content": bool(content_object_is_restricted(btype or {})),
        }
        return {
            "building": building_name,
            "profession": reserved_profession.get("name", "Service Policy"),
            "profession_id": reserved_profession.get("id"),
            "worker_name": reserved_worker.get("name", "Unknown"),
            "worker": reserved_worker,
            "event_data": story,
            "report": story["report"],
            "description": story["description"],
            "result": "Missed Request",
            "earnings": 0,
            "reputation_change": 0,
            "used_skill": requested_skill,
            "roll": None,
            "trait_roll": None,
            "trait_success_messages": [],
            "group_event": False,
            "loot": [],
            "story_image": None,
        }

    def get_building_policy_story_counts(building, btype, worker_gender=None):
        total = 0
        allowed = 0
        if not btype or not hasattr(btype, "get"):
            return allowed, total
        for profession in btype.get("professions", []) or []:
            if not profession_is_unlocked(profession) or not profession_is_visible(profession, btype):
                continue
            for story in profession.get("daily_stories", []) or []:
                if not getattr(persistent, "nsfw_enabled", False) and content_object_is_restricted(story):
                    continue
                total += 1
                if story_allowed_by_building_policy(building, story, worker_gender):
                    allowed += 1
        return allowed, total

    def get_batch_visible_worker_pool(worker_pool, building_filter="All Workers", job_filter="All Jobs"):
        """Return the exact roster rows eligible for batch actions after active filters."""
        result = []
        for worker in (worker_pool or []):
            if not hasattr(worker, "get") or not worker.get("name"):
                continue
            building_name = worker.get("assigned_building", "Unassigned")
            building = available_buildings.get(building_name, {}) if building_name != "Unassigned" else {}
            btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == building.get("type")), None)

            if building_filter != "All Workers":
                type_name = building_type_display_name(btype, "Unassigned" if not building else building.get("type"))
                parts = str(building_name).split("_")
                default_name = "Building " + parts[1] if len(parts) > 1 else str(building_name)
                display_name = (getattr(store, "custom_names", {}) or {}).get(building_name, default_name)
                if "%s: %s" % (type_name, display_name) != building_filter:
                    continue

            if job_filter != "All Jobs":
                if not building:
                    job_name = "Unassigned"
                else:
                    job_id = (building.get("servant_jobs", {}) or {}).get(worker.get("name"), "Unassigned")
                    if str(job_id or "").strip().lower() == "unassigned":
                        job_name = "Unassigned"
                    else:
                        resolver = getattr(store, "resolve_profession_for_job", None)
                        if callable(resolver):
                            job_name = resolver(btype, job_id)[0]
                        else:
                            job_name = next((entry.get("name", job_id) for entry in (btype.get("professions", []) if btype else []) if str(entry.get("id", "")).strip().lower() == str(job_id).strip().lower()), job_id)
                if job_name != job_filter:
                    continue
            result.append(worker)
        return result

    def _batch_selected_workers():
        names = set(getattr(store, "batch_selected_worker_names", []) or [])
        if hasattr(store, "batch_allowed_worker_names"):
            names.intersection_update(set(getattr(store, "batch_allowed_worker_names", []) or []))
        return [worker for worker in (getattr(store, "workers", []) or []) if worker.get("name") in names]

    def compact_table_text(value, max_chars):
        """Return one-line table text with a stable ellipsis, preserving source data."""
        text = str(value or "")
        try:
            limit = max(1, int(max_chars))
        except (TypeError, ValueError):
            limit = 1
        if len(text) <= limit:
            return text
        if limit == 1:
            return "…"
        return text[:limit - 1].rstrip() + "…"

    # Advance widths of CaslonAntique.ttf (the interface font) per glyph at size 1,
    # measured with FreeType. Lets screens decide how much of a name fits a cell
    # without rendering; unknown glyphs fall back to an average width.
    _CASLON_GLYPH_WIDTHS = {' ': 0.325, '!': 0.215, '"': 0.335, '#': 0.515, '$': 0.465, '%': 0.575, '&': 0.57, "'": 0.17, '(': 0.29, ')': 0.295, '*': 0.37, '+': 0.46, ',': 0.195, '-': 0.2, '.': 0.2, '/': 0.43, '0': 0.46, '1': 0.275, '2': 0.42, '3': 0.435, '4': 0.42, '5': 0.42, '6': 0.47, '7': 0.395, '8': 0.46, '9': 0.46, ':': 0.2, ';': 0.195, '<': 0.5, '=': 0.46, '>': 0.5, '?': 0.365, '@': 0.695, 'A': 0.535, 'B': 0.52, 'C': 0.64, 'D': 0.63, 'E': 0.495, 'F': 0.465, 'G': 0.675, 'H': 0.715, 'I': 0.275, 'J': 0.285, 'K': 0.605, 'L': 0.45, 'M': 0.775, 'N': 0.67, 'O': 0.745, 'P': 0.5, 'Q': 0.745, 'R': 0.505, 'S': 0.52, 'T': 0.515, 'U': 0.7, 'V': 0.59, 'W': 0.82, 'X': 0.57, 'Y': 0.57, 'Z': 0.505, '[': 0.3, '\\': 0.425, ']': 0.295, '^': 0.5, '_': 0.5, '`': 0.5, 'a': 0.335, 'b': 0.425, 'c': 0.34, 'd': 0.41, 'e': 0.325, 'f': 0.23, 'g': 0.39, 'h': 0.41, 'i': 0.215, 'j': 0.225, 'k': 0.41, 'l': 0.21, 'm': 0.645, 'n': 0.4, 'o': 0.425, 'p': 0.405, 'q': 0.405, 'r': 0.265, 's': 0.305, 't': 0.245, 'u': 0.38, 'v': 0.33, 'w': 0.485, 'x': 0.34, 'y': 0.35, 'z': 0.32, '{': 0.295, '|': 0.5, '}': 0.3, '~': 0.665, '…': 0.6, '’': 0.195, '‘': 0.195, '×': 0.465, 'é': 0.325, 'ñ': 0.4, 'á': 0.335, 'í': 0.22, 'ó': 0.425, 'ú': 0.38}

    def text_px_width(text, size):
        """Approximate rendered width of `text` at font `size` (kerning ignored, +6% margin)."""
        total = 0.0
        for ch in str(text or ""):
            total += _CASLON_GLYPH_WIDTHS.get(ch, 0.55)
        return total * float(size) * 1.06

    _ITEM_TIER_ABBREVIATIONS = (("Elite ", "E. "), ("Advanced ", "A. "), ("Basic ", "B. "))

    def abbreviate_item_name(name, max_px, size):
        """Fit an item name into `max_px` at `size`: shorten the tier word first
        ("Elite Diamond Earrings" -> "E. Diamond Earrings"), then trim with an
        ellipsis only if it still does not fit. Never wraps."""
        text = str(name or "")
        if not text or text_px_width(text, size) <= max_px:
            return text
        for full, short in _ITEM_TIER_ABBREVIATIONS:
            if text.startswith(full):
                text = short + text[len(full):]
                break
        if text_px_width(text, size) <= max_px:
            return text
        for limit in range(len(text) - 1, 0, -1):
            candidate = compact_table_text(text, limit)
            if text_px_width(candidate, size) <= max_px:
                return candidate
        return "…"


    def resolve_depleted_worker_health(worker_pool):
        """Resolve zero health without permanent roster loss."""
        incapacitated_names = []
        for worker in list(worker_pool or []):
            if not hasattr(worker, "get") or int(worker.get("health", 0) or 0) > 0:
                continue
            already_reforming = "Reforming" in (worker.get("traits") or [])
            if worker_can_reform(worker) and not already_reforming:
                worker["health"] = max(1, calculate_max_health(worker) // 4)
                add_trait_with_duration(worker, "Reforming", 3)
                renpy.notify(f"{worker['name']} reformed from a puddle!")
                renpy.log(f"{worker['name']} reformed after reaching zero health (health -> {worker['health']})")
                continue
            unassign_worker(worker)
            worker["health"] = 1
            worker["energy"] = 0
            incapacitated_names.append(str(worker.get("name", "Unknown")))
            renpy.log(f"{worker.get('name', 'Unknown')} collapsed at zero health and was withdrawn from duty")
        return incapacitated_names

    def _coerce_stat_int(value, default=0):
        # Legacy saves can carry stats as strings ("18.5") or junk; int() alone raises.
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _batch_building_is_owned(building_name, building):
        if not building or not hasattr(building, "get"):
            return False
        if not is_standard_managed_building(building_name, building):
            return False
        if building.get("owned") is False:
            return False
        if building.get("owned") is True:
            return True
        normalized_name = str(building_name or "").replace("_", " ").strip().lower()
        return any(str(owned_name or "").replace("_", " ").strip().lower() == normalized_name for owned_name in (getattr(store, "owned_buildings", []) or []))

    def batch_toggle_worker(worker_name):
        if hasattr(store, "batch_allowed_worker_names") and worker_name not in (getattr(store, "batch_allowed_worker_names", []) or []):
            return False
        selected = list(getattr(store, "batch_selected_worker_names", []) or [])
        if worker_name in selected:
            selected.remove(worker_name)
        else:
            selected.append(worker_name)
        store.batch_selected_worker_names = selected
        return worker_name in selected

    def batch_prepare_selection(worker_pool):
        allowed = {worker.get("name") for worker in (worker_pool or []) if hasattr(worker, "get") and worker.get("name")}
        store.batch_allowed_worker_names = sorted(allowed)
        store.batch_selected_worker_names = [name for name in (getattr(store, "batch_selected_worker_names", []) or []) if name in allowed]
        # Used by an `on show` action: non-None would resolve the interaction.
        return None

    def get_batch_assignment_cells(worker):
        """Return the roster-consistent (building, job) labels for a batch row."""
        if not worker or not hasattr(worker, "get"):
            return ("Unassigned", "Unassigned")
        raw_building = worker.get("assigned_building", "Unassigned")
        resolved = _resolve_building_key(raw_building)
        building = available_buildings.get(resolved) if resolved else None
        if not resolved or not hasattr(building, "get"):
            return ("Unassigned", "Unassigned")

        custom_names = getattr(store, "custom_names", {}) or {}
        default_name = str(resolved).replace("_", " ")
        building_label = custom_names.get(resolved, custom_names.get(raw_building, default_name))

        btype_id = building.get("type")
        btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == btype_id), None)
        servant_jobs = building.get("servant_jobs", {}) or {}
        job_id = servant_jobs.get(worker.get("name", ""), "Unassigned") if hasattr(servant_jobs, "get") else "Unassigned"
        resolver = getattr(store, "resolve_profession_for_job", None)
        if callable(resolver):
            job_label = resolver(btype, job_id)[0]
        else:
            job_label = "Unassigned" if str(job_id or "").strip().lower() in ("", "unassigned") else str(job_id)
        return (str(building_label), str(job_label))

    def batch_select_workers(worker_pool, mode="all"):
        pool = [worker for worker in (worker_pool or []) if hasattr(worker, "get") and worker.get("name")]
        store.batch_allowed_worker_names = [worker["name"] for worker in pool]
        if mode == "clear":
            store.batch_selected_worker_names = []
        elif mode == "unassigned":
            store.batch_selected_worker_names = [worker["name"] for worker in pool if worker.get("assigned_building", "Unassigned") == "Unassigned"]
        elif mode == "tired":
            selected = []
            for worker in pool:
                max_energy = max(1, _coerce_stat_int(calculate_max_energy(worker), 1))
                max_health = max(1, _coerce_stat_int(calculate_max_health(worker), 1))
                if _coerce_stat_int(worker.get("energy")) * 100 <= max_energy * 35 or _coerce_stat_int(worker.get("health")) * 100 <= max_health * 35:
                    selected.append(worker["name"])
            store.batch_selected_worker_names = selected
        else:
            store.batch_selected_worker_names = [worker["name"] for worker in pool]
        return len(store.batch_selected_worker_names)

    def batch_apply_building(building_name):
        workers_to_move = _batch_selected_workers()
        resolved = _resolve_building_key(building_name)
        if not building_accepts_worker_assignment(resolved):
            return (0, len(workers_to_move))
        building = available_buildings.get(resolved) if resolved else None
        btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == (building or {}).get("type")), None)
        if not _batch_building_is_owned(resolved, building) or (btype and not building_type_is_visible(btype)):
            return (0, len(workers_to_move))
        applied = 0
        for worker in workers_to_move:
            add_worker_to_building(worker, resolved)
            set_worker_job(worker, resolved, "unassigned")
            clear_worker_autorest_state(worker)
            applied += 1
        return applied, len(workers_to_move) - applied

    def batch_apply_job(building_name, job_id):
        workers_to_assign = _batch_selected_workers()
        resolved = _resolve_building_key(building_name)
        if not resolved or not workers_to_assign:
            return (0, len(workers_to_assign))
        if not building_accepts_worker_assignment(resolved):
            return (0, len(workers_to_assign))
        building = available_buildings.get(resolved)
        if not _batch_building_is_owned(resolved, building):
            return (0, len(workers_to_assign))
        btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == building.get("type")), None)
        if btype and not building_type_is_visible(btype):
            return (0, len(workers_to_assign))
        profession = next((entry for entry in (btype.get("professions", []) if btype else []) if str(entry.get("id", "")).lower() == str(job_id or "").lower()), None)
        target_job = str(job_id or "").lower()
        if target_job != "rest" and (not profession or not profession_is_unlocked(profession) or not profession_is_visible(profession, btype)):
            return (0, len(workers_to_assign))

        selected_buildings = {_resolve_building_key(worker.get("assigned_building")) for worker in workers_to_assign}
        if selected_buildings != {resolved}:
            return (0, len(workers_to_assign))

        from fm_autorest.capacity import claim_job_slot, count_job_slots
        current_jobs = building.get("servant_jobs", {}) or {}
        workers_here = [
            worker for worker in (getattr(store, "workers", []) or [])
            if _resolve_building_key(worker.get("assigned_building")) == resolved
        ]
        limit = get_max_daily_workers(building, profession) if profession else 999
        occupied_count = count_job_slots(current_jobs, workers_here, target_job)
        active_count = count_job_slots(
            current_jobs,
            workers_here,
            target_job,
            include_reservations=False,
        )
        applied = 0
        skipped = 0
        for worker in workers_to_assign:
            if target_job != "rest":
                allowed, occupied_count, active_count = claim_job_slot(
                    worker,
                    current_jobs.get(worker.get("name")),
                    target_job,
                    occupied_count,
                    active_count,
                    limit,
                )
                if not allowed:
                    skipped += 1
                    continue
            set_worker_job(worker, resolved, job_id)
            clear_worker_autorest_state(worker)
            if target_job != "rest":
                if worker.get("auto_equip", False):
                    run_worker_auto_equip(worker)
            applied += 1
        return applied, skipped

    def batch_rest_workers():
        selected = _batch_selected_workers()
        applied = 0
        skipped = 0
        for worker in selected:
            building_name = _resolve_building_key(worker.get("assigned_building"))
            if not building_name:
                skipped += 1
                continue
            set_worker_job(worker, building_name, "rest")
            clear_worker_autorest_state(worker)
            applied += 1
        return applied, skipped

    def batch_unassign_workers():
        selected = _batch_selected_workers()
        for worker in selected:
            unassign_worker(worker)
            clear_worker_autorest_state(worker)
        return len(selected)

    # ---------------------------------------------------------------------------
    # Roster QoL executors (Ren'Py glue over the pure fm_roster.* planners).
    # Pure decision logic is unit-tested in tests/; these adapters gather state,
    # call the planner, and apply results via existing engine primitives. Modules
    # are imported locally so no module object is stored in the pickled store.
    # ---------------------------------------------------------------------------

    # These run on the always-rendered roster screen. A cosmetic sort helper must
    # NEVER crash the roster, so every fm_roster access degrades gracefully.
    def cycle_worker_sort_mode():
        try:
            from fm_roster.sorting import next_sort_mode
            store.worker_roster_sort_mode = next_sort_mode(
                getattr(store, "worker_roster_sort_mode", "default")
            )
        except Exception as e:
            renpy.log("cycle_worker_sort_mode failed, resetting to default: %r" % (e,))
            store.worker_roster_sort_mode = "default"

    def worker_sort_mode_label():
        try:
            from fm_roster.sorting import SORT_LABELS
            return SORT_LABELS.get(getattr(store, "worker_roster_sort_mode", "default"), "Building")
        except Exception as e:
            renpy.log("worker_sort_mode_label failed: %r" % (e,))
            return "Building"

    def toggle_worker_favorite(worker):
        """Favorite toggle that also supports workers from pre-feature saves."""
        try:
            from fm_roster.sorting import toggle_favorite
            toggle_favorite(worker)
            renpy.restart_interaction()
        except Exception as e:
            renpy.log("toggle_worker_favorite failed: %r" % (e,))

    def building_event_chance_label(building_name):
        """Manager-screen header line: this building's current random-event chance.
        Empty string on any failure so the screen simply omits the line."""
        try:
            from fm_events.manager_gating import event_probability
            resolved = _resolve_building_key(building_name)
            count = count_managers_in_building(resolved) if resolved else 0
            return "Random events here: %d%%/day" % event_probability(count)
        except Exception as e:
            renpy.log("building_event_chance_label failed: %r" % (e,))
            return ""

    def _fm_building_and_btype(building_key):
        """(resolved_key, building, btype) or (None, None, None)."""
        resolved = _resolve_building_key(building_key)
        if not resolved:
            return None, None, None
        building = available_buildings.get(resolved)
        if not hasattr(building, "get"):
            return None, None, None
        btype = next(
            (bt for bt in building_types_json.get("building_types", [])
             if hasattr(bt, "get") and bt.get("id") == building.get("type")),
            None,
        )
        return resolved, building, btype

    def _fm_job_holder_count(resolved_key, building, profession_id):
        """Active workers plus Rest reservations occupying (building, job).

        Must never raise: it runs from screen render paths (Manager, auto-fill
        plan popup), where an exception crash-loops the whole screen. A stale
        python-packages module in a long-running process (script reloads do NOT
        reimport python-packages) falls back to the inline count below.
        """
        pid = str(profession_id or "").strip().lower()
        servant_jobs = building.get("servant_jobs", {}) or {}
        workers_here = [
            worker for worker in store.workers
            if (hasattr(worker, "get")
                and _resolve_building_key(worker.get("assigned_building")) == resolved_key)
        ]
        try:
            from fm_autorest.capacity import count_job_slots
            return count_job_slots(servant_jobs, workers_here, pid)
        except Exception as e:
            renpy.log("_fm_job_holder_count: fm_autorest unavailable/stale (%r); inline fallback (restart the game to reload modules)" % (e,))
        # Inline mirror of fm_autorest.capacity.count_job_slots (canonical copy
        # lives there): active workers plus Rest reservations for this job.
        if not pid or pid in ("rest", "unassigned") or not hasattr(servant_jobs, "items"):
            return 0
        by_name = {w.get("name"): w for w in workers_here if hasattr(w, "get") and w.get("name")}
        count = 0
        for worker_name, current_job in servant_jobs.items():
            worker = by_name.get(worker_name)
            if worker is None:
                continue
            occupied = str(current_job or "").strip().lower()
            if occupied == "rest":
                occupied = str(worker.get("previous_profession") or worker.get("previous_job") or "").strip().lower() or "rest"
            if occupied == pid:
                count += 1
        return count

    def _autofill_quotas_for(building):
        """The building's per-profession auto-fill targets ({job_id: int}); {} = no plan."""
        quotas = building.get("autofill_quotas") if hasattr(building, "get") else None
        return quotas if hasattr(quotas, "get") else {}

    def building_has_autofill_quotas(building_key):
        resolved, building, btype = _fm_building_and_btype(building_key)
        return bool(resolved) and bool(_autofill_quotas_for(building))

    def get_autofill_quota(building_key, job_id):
        resolved, building, btype = _fm_building_and_btype(building_key)
        if not resolved:
            return None
        return _autofill_quotas_for(building).get(str(job_id).strip().lower())

    def adjust_autofill_quota(building_key, job_id, delta, slot_cap):
        """Step a profession's auto-fill target: Max(no key) <-> cap..0. '+' past cap returns to Max."""
        resolved, building, btype = _fm_building_and_btype(building_key)
        if not resolved:
            return
        pid = str(job_id).strip().lower()
        quotas = dict(_autofill_quotas_for(building))
        current = quotas.get(pid)
        cap = max(0, int(slot_cap or 0))
        if delta > 0:
            if current is None:
                return  # already Max
            if current + 1 > cap:
                quotas.pop(pid, None)  # past the cap -> back to Max
            else:
                quotas[pid] = current + 1
        else:
            if current is None:
                quotas[pid] = cap  # step down from Max
            elif current > 0:
                quotas[pid] = current - 1
            else:
                return
        building["autofill_quotas"] = quotas
        renpy.restart_interaction()

    def clear_autofill_quotas(building_key):
        resolved, building, btype = _fm_building_and_btype(building_key)
        if resolved and hasattr(building, "get"):
            building["autofill_quotas"] = {}
            renpy.restart_interaction()

    def prune_autofill_quotas(building_key, valid_job_ids):
        """Drop targets for professions that no longer exist (renamed/removed/hidden)."""
        resolved, building, btype = _fm_building_and_btype(building_key)
        if not resolved:
            return
        quotas = _autofill_quotas_for(building)
        valid = set(str(j).strip().lower() for j in (valid_job_ids or []))
        stale = [k for k in quotas.keys() if k not in valid]
        if stale:
            cleaned = dict(quotas)
            for k in stale:
                cleaned.pop(k, None)
            building["autofill_quotas"] = cleaned

    def autofill_building(building_key):
        """Optimize all normal roles in one building.

        Reconsiders workers already in this building (with or without a normal
        profession) and may draw from the globally unassigned pool. Manager and
        Rest reservations are preserved; workers assigned to another building
        are never moved. Optional quotas define final role headcounts.
        """
        try:
            from fm_roster.autofill import plan_autofill, capped_free_slots, reoptimization_candidates
        except Exception as e:
            renpy.log("autofill_building import failed: %r" % (e,))
            renpy.notify("Auto-fill unavailable")
            return None
        resolved, building, btype = _fm_building_and_btype(building_key)
        if not resolved or not hasattr(btype, "get") or not is_standard_managed_building(resolved, building):
            renpy.notify("Auto-fill: building unavailable")
            return None

        quotas = _autofill_quotas_for(building)
        allow_trim = bool(building.get("autofill_allow_unassign", False))
        servant_jobs = building.get("servant_jobs", {}) or {}
        if not hasattr(servant_jobs, "get"):
            servant_jobs = {}

        def _skill_fn(worker, skill_name):
            return calculate_skill_with_traits(worker, skill_name, include_libido=False)

        plan_reserved = 0
        profs = []
        for p in btype.get("professions", []) or []:
            if not hasattr(p, "get"):
                continue
            pid = str(p.get("id", "")).strip().lower()
            pname = str(p.get("name", pid) or pid)
            if pid in ("manager", "rest") or pname.strip().lower() in ("manager", "rest"):
                continue
            if not profession_is_unlocked(p) or not profession_is_visible(p, btype):
                continue
            capacity = max(0, get_max_daily_workers(building, p))
            quota = quotas.get(pid)
            free = capped_free_slots(capacity, 0, quota)
            plan_reserved += capacity - free
            if free <= 0:
                continue
            profs.append({
                "job_id": p.get("id"),
                "name": pname,
                "skills": list(p.get("skills", []) or []),
                "free_slots": free,
            })

        candidates = reoptimization_candidates(
            store.workers,
            resolved,
            servant_jobs,
            _resolve_building_key,
        )
        target_candidates = [
            candidate for candidate in candidates
            if _resolve_building_key(candidate.get("assigned_building")) == resolved
        ]
        plan = plan_autofill(profs, candidates, _skill_fn)
        selected_names = set(a.get("worker") for a in plan["assignments"])

        # Remove only normal role bindings before applying the optimized plan.
        # Workers stay inside the building unless the explicit trim option says
        # otherwise; Manager/Rest workers were excluded from candidates above.
        for _candidate in target_candidates:
            servant_jobs.pop(_candidate.get("name"), None)
            clear_worker_autorest_state(_candidate)
        building["servant_jobs"] = servant_jobs

        workers_by_name = {w.get("name"): w for w in store.workers if hasattr(w, "get")}
        assigned = 0
        for assignment in plan["assignments"]:
            worker = workers_by_name.get(assignment["worker"])
            if worker is None:
                continue
            if _resolve_building_key(worker.get("assigned_building")) != resolved:
                add_worker_to_building(worker, resolved)
            set_worker_job(worker, resolved, assignment["job_id"])
            clear_worker_autorest_state(worker)
            if worker.get("auto_equip", False):
                run_worker_auto_equip(worker)
            assigned += 1

        trimmed = []
        roleless = 0
        for _candidate in target_candidates:
            if _candidate.get("name") in selected_names:
                continue
            if allow_trim and _candidate.get("name") not in selected_names:
                unassign_worker(_candidate)
                trimmed.append(_candidate.get("name"))
            else:
                # Keep the worker in this building without a profession.
                _candidate["assigned_building"] = resolved
                roleless += 1

        empty = sum(int(v) for v in plan["empty_slots"].values())
        parts = ["%d roles optimized" % assigned]
        if roleless:
            parts.append("%d without role" % roleless)
        if trimmed:
            parts.append("%d unassigned by plan" % len(trimmed))
        if plan_reserved:
            parts.append("%d left by plan" % plan_reserved)
        parts.append("%d slots still empty" % empty)
        renpy.notify("Auto-fill: " + ", ".join(parts))
        return plan

    def build_current_assignment_preset():
        """Capture current worker->(building_key, job_id) assignments as preset entries."""
        try:
            from fm_roster.presets import normalize_preset
        except Exception as e:
            renpy.log("build_current_assignment_preset import failed: %r" % (e,))
            return []
        raw = []
        for w in store.workers:
            if not hasattr(w, "get"):
                continue
            ab = w.get("assigned_building")
            resolved = _resolve_building_key(ab) if ab else None
            if not resolved:
                continue
            building = available_buildings.get(resolved)
            if not hasattr(building, "get"):
                continue
            servant_jobs = building.get("servant_jobs", {}) or {}
            job = servant_jobs.get(w.get("name")) if hasattr(servant_jobs, "get") else None
            raw.append({"worker": w.get("name"), "building": resolved, "job": job})
        return normalize_preset(raw)

    def save_assignment_preset(name):
        name = str(name or "").strip()
        if not name:
            renpy.notify("Preset name required")
            return False
        presets = getattr(store, "assignment_presets", {}) or {}
        if not hasattr(presets, "get"):
            presets = {}
        if name not in presets and len(presets) >= 10:
            renpy.notify("Preset limit reached (max 10)")
            return False
        presets[name] = build_current_assignment_preset()
        store.assignment_presets = presets
        renpy.notify("Preset saved: %s (%d assignments)" % (name, len(presets[name])))
        return True

    def prompt_and_save_preset():
        """Prompt for a name in a fresh context (safe from a screen action) and save."""
        name = renpy.input("Name this assignment preset:", length=24)
        if name and name.strip():
            save_assignment_preset(name.strip())

    def delete_assignment_preset(name):
        presets = getattr(store, "assignment_presets", {}) or {}
        if hasattr(presets, "get") and name in presets:
            try:
                del presets[name]
            except Exception as e:
                renpy.log("delete_assignment_preset failed: %r" % (e,))
                renpy.notify("Could not delete preset")
                return
            store.assignment_presets = presets
            renpy.notify("Preset deleted: %s" % name)

    def apply_assignment_preset(name, unassign_first=False):
        """Reapply a saved preset. Skips missing workers, unknown buildings, and overflow."""
        try:
            from fm_roster.presets import plan_apply
        except Exception as e:
            renpy.log("apply_assignment_preset import failed: %r" % (e,))
            renpy.notify("Presets unavailable")
            return None
        presets = getattr(store, "assignment_presets", {}) or {}
        entries = presets.get(name) if hasattr(presets, "get") else None
        if not entries:
            renpy.notify("Preset not found or empty")
            return None
        if unassign_first:
            for w in list(store.workers):
                if hasattr(w, "get") and w.get("assigned_building") and w.get("assigned_building") != "Unassigned":
                    unassign_worker(w)
                    clear_worker_autorest_state(w)
        workers_by_name = {w.get("name"): w for w in store.workers if hasattr(w, "get")}
        present = set(workers_by_name.keys())

        def _resolve(raw):
            return _resolve_building_key(raw)

        def _current_of(worker_name):
            w = workers_by_name.get(worker_name)
            if w is None:
                return None
            ab = w.get("assigned_building")
            resolved = _resolve_building_key(ab) if ab else None
            if not resolved:
                return None
            building = available_buildings.get(resolved)
            if not hasattr(building, "get"):
                return None
            servant_jobs = building.get("servant_jobs", {}) or {}
            job = servant_jobs.get(worker_name) if hasattr(servant_jobs, "get") else None
            job = str(job or "").strip().lower()
            if job in ("", "unassigned", "rest"):
                return None
            return (resolved, job)

        def _capacity_of(resolved_building, job):
            # Returns free slots (int) for a valid job slot, or None when `job` is
            # not a real profession in this building (renamed/removed) so plan_apply
            # reports 'unknown_job' rather than a misleading 'overflow'.
            building = available_buildings.get(resolved_building)
            if not hasattr(building, "get"):
                return None
            btype = next(
                (bt for bt in building_types_json.get("building_types", [])
                 if hasattr(bt, "get") and bt.get("id") == building.get("type")),
                None,
            )
            if not hasattr(btype, "get"):
                return None
            prof = next(
                (p for p in btype.get("professions", [])
                 if hasattr(p, "get") and str(p.get("id", "")).strip().lower() == str(job).strip().lower()),
                None,
            )
            if not hasattr(prof, "get"):
                return None
            if not (profession_is_unlocked(prof) and profession_is_visible(prof, btype)):
                # Hidden/locked profession (building downgraded, NSFW off, etc.):
                # not a valid slot -> preset reports unknown_job, matching auto-fill
                # and batch_apply_job which also refuse locked/invisible professions.
                return None
            return max(0, get_max_daily_workers(building, prof) - _fm_job_holder_count(resolved_building, building, job))

        plan = plan_apply(entries, present, _resolve, _capacity_of, _current_of)
        for a in plan["assignments"]:
            w = workers_by_name.get(a["worker"])
            if w is None:
                continue
            add_worker_to_building(w, a["building"])
            set_worker_job(w, a["building"], a["job"])
            clear_worker_autorest_state(w)
            if w.get("auto_equip", False):
                run_worker_auto_equip(w)
        renpy.notify("Preset '%s': %d assigned, %d unchanged, %d skipped" % (
            name, len(plan["assignments"]), len(plan["unchanged"]), len(plan["skipped"])
        ))
        return plan

    def add_worker_activity_items(worker, category, items, metadata=None):
        """Append factual items to today's worker history and retain 10 days."""
        if worker is None or not hasattr(worker, "get"):
            return False
        clean_items = []
        for value in (items or []):
            text = str(value or "").strip()
            if text:
                clean_items.append(text)
        if not clean_items:
            return False

        day = int(calculate_total_days())
        date = "%s/%s/%s" % (
            int(getattr(store, "current_day", 1) or 1),
            int(getattr(store, "current_month", 1) or 1),
            int(getattr(store, "current_year", 1) or 1),
        )
        activity_log = list(worker.get("activity_log", []) or [])
        if activity_log and int(activity_log[-1].get("day", -1) or -1) == day:
            entry = activity_log[-1]
            entry["date"] = date
            entry["items"] = list(entry.get("items", []) or [])
        else:
            entry = {"day": day, "date": date, "items": []}
            activity_log.append(entry)

        added = False
        item_metadata = dict(metadata or {})
        for text in clean_items:
            item = {"category": str(category or "general"), "text": text}
            if item_metadata:
                item["metadata"] = dict(item_metadata)
            entry["items"].append(item)
            added = True
        worker["activity_log"] = activity_log[-10:]
        return added

    def build_worker_activity_snapshot(worker):
        """Return a save-safe snapshot of worker state used to build the history."""
        worker = worker or {}
        tracked_stats = (
            "health", "energy", "libido", "rebelliousness", "joy",
            "relationship", "romance", "discipline", "comfort_level",
            "level", "success_count",
        )
        stats = {}
        for key in tracked_stats:
            if key in worker:
                try:
                    stats[key] = int(worker.get(key, 0) or 0)
                except (TypeError, ValueError):
                    continue

        def _integer_map(value):
            result = {}
            for key, raw in ((value or {}).items() if hasattr(value, "items") else []):
                try:
                    result[str(key)] = int(raw or 0)
                except (TypeError, ValueError):
                    continue
            return result

        return {
            "stats": stats,
            "skills": _integer_map(worker.get("skills", {})),
            "skill_uses": _integer_map(worker.get("skill_uses", {})),
            "traits": [str(value) for value in (worker.get("traits", []) or []) if value],
            "assigned_building": str(worker.get("assigned_building", "Unassigned") or "Unassigned"),
        }

    def worker_activity_text_is_restricted(category, text):
        """Infer stable NSFW provenance for legacy and newly generated activity text."""
        category = str(category or "").strip().lower()
        text = str(text or "").strip()
        lowered = text.lower()
        if category == "stats" and lowered.startswith("libido:"):
            return True
        for skill_name in (get_sexual_skill_names() or []):
            prefix = str(skill_name or "").strip().lower()
            if lowered.startswith(prefix + " skill:") or lowered.startswith(prefix + " practice:"):
                return True
        for marker in ("gained trait: ", "lost trait: "):
            if lowered.startswith(marker):
                trait_name = text[len(marker):].strip().rstrip(".")
                raw_cache = getattr(store, "_trait_def_raw_cache", {}) or {}
                trait_def = raw_cache.get(trait_name) if hasattr(raw_cache, "get") else None
                # A removed/modded trait without provenance is ambiguous. In SFW
                # mode ambiguity fails closed; the persisted text stays untouched.
                return True if trait_def is None else bool(content_object_is_restricted(trait_def))
        return False

    def capture_worker_activity_changes(worker):
        """Compare a worker with their last snapshot and append readable changes."""
        if worker is None or not hasattr(worker, "get"):
            return False
        current = build_worker_activity_snapshot(worker)
        previous = worker.get("_activity_log_snapshot")
        worker["_activity_log_snapshot"] = current
        if not previous or not hasattr(previous, "get"):
            return False

        stat_labels = {
            "health": "Health", "energy": "Energy", "libido": "Libido",
            "rebelliousness": "Rebelliousness", "joy": "Joy",
            "relationship": "Relationship", "romance": "Romance",
            "discipline": "Discipline", "comfort_level": "Comfort",
        }
        stat_items = []
        old_stats = previous.get("stats", {}) or {}
        new_stats = current.get("stats", {}) or {}
        for key, label in stat_labels.items():
            if key not in old_stats or key not in new_stats or old_stats[key] == new_stats[key]:
                continue
            delta = new_stats[key] - old_stats[key]
            stat_items.append("%s: %s -> %s (%+d)." % (label, old_stats[key], new_stats[key], delta))

        progress_items = []
        old_level = old_stats.get("level")
        new_level = new_stats.get("level")
        if old_level is not None and new_level is not None and old_level != new_level:
            progress_items.append("Worker level: %s -> %s." % (old_level, new_level))
        elif new_stats.get("success_count", 0) > old_stats.get("success_count", 0):
            delta = new_stats["success_count"] - old_stats.get("success_count", 0)
            progress_items.append("Career progress: +%s successful %s." % (delta, "shift" if delta == 1 else "shifts"))

        old_skills = previous.get("skills", {}) or {}
        new_skills = current.get("skills", {}) or {}
        for skill_name in sorted(set(old_skills) | set(new_skills)):
            old_value = old_skills.get(skill_name, 0)
            new_value = new_skills.get(skill_name, 0)
            if old_value != new_value:
                progress_items.append("%s skill: %s -> %s." % (skill_name, old_value, new_value))

        old_uses = previous.get("skill_uses", {}) or {}
        new_uses = current.get("skill_uses", {}) or {}
        for skill_name in sorted(set(old_uses) | set(new_uses)):
            delta = new_uses.get(skill_name, 0) - old_uses.get(skill_name, 0)
            if delta > 0:
                progress_items.append("%s practice: +%s %s." % (skill_name, delta, "use" if delta == 1 else "uses"))

        old_traits = set(previous.get("traits", []) or [])
        new_traits = set(current.get("traits", []) or [])
        for trait_name in sorted(new_traits - old_traits):
            progress_items.append("Gained trait: %s." % trait_name)
        for trait_name in sorted(old_traits - new_traits):
            progress_items.append("Lost trait: %s." % trait_name)

        old_building = previous.get("assigned_building", "Unassigned")
        new_building = current.get("assigned_building", "Unassigned")
        if old_building != new_building:
            progress_items.append("Assignment: %s -> %s." % (old_building, new_building))

        metadata = {
            "worker_nsfw": bool(content_object_is_restricted(worker)),
            "content_classified": True,
        }
        restricted_metadata = dict(metadata)
        restricted_metadata["nsfw_content"] = True
        safe_stats = [item for item in stat_items if not worker_activity_text_is_restricted("stats", item)]
        restricted_stats = [item for item in stat_items if worker_activity_text_is_restricted("stats", item)]
        safe_progress = [item for item in progress_items if not worker_activity_text_is_restricted("progress", item)]
        restricted_progress = [item for item in progress_items if worker_activity_text_is_restricted("progress", item)]
        results = (
            add_worker_activity_items(worker, "stats", safe_stats, metadata),
            add_worker_activity_items(worker, "stats", restricted_stats, restricted_metadata),
            add_worker_activity_items(worker, "progress", safe_progress, metadata),
            add_worker_activity_items(worker, "progress", restricted_progress, restricted_metadata),
        )
        return any(results)

    def capture_all_worker_activity_changes():
        """Capture changes for the live roster without creating empty entries."""
        changed = 0
        for worker in (getattr(store, "workers", []) or []):
            if callable(getattr(store, "worker_is_in_franchise", None)) and worker_is_in_franchise(worker):
                worker["_activity_log_snapshot"] = build_worker_activity_snapshot(worker)
                continue
            if capture_worker_activity_changes(worker):
                changed += 1
        return changed

    def add_worker_moment(worker, category, text, metadata=None):
        """Compatibility wrapper: new moments are grouped into the worker history."""
        return add_worker_activity_items(worker, category, [text], metadata)

    def worker_moment_is_visible(moment):
        """Apply SFW filtering without mutating persisted worker history."""
        if getattr(persistent, "nsfw_enabled", False) or not hasattr(moment, "get"):
            return True
        metadata = moment.get("metadata", {}) or {}
        if metadata.get("nsfw_content", False) or metadata.get("worker_nsfw", False):
            return False
        if worker_activity_text_is_restricted(moment.get("category"), moment.get("text")):
            return False
        if moment.get("category") in ("work", "decision") and not metadata.get("content_classified", False):
            return False
        return True

    def get_worker_activity_entries(worker):
        """Return visible activity plus legacy moments, grouped by day without mutating saves."""
        if not worker or not hasattr(worker, "get"):
            return []
        grouped = {}
        for entry in (worker.get("activity_log", []) or []):
            if not hasattr(entry, "get"):
                continue
            try:
                day = int(entry.get("day", -1))
            except (TypeError, ValueError):
                continue
            target = grouped.setdefault(day, {
                "day": day,
                "date": str(entry.get("date", "Unknown date")),
                "items": [],
            })
            for item in (entry.get("items", []) or []):
                if hasattr(item, "get") and worker_moment_is_visible(item):
                    target["items"].append(dict(item))

        for moment in (worker.get("important_moments", []) or []):
            if not hasattr(moment, "get") or not worker_moment_is_visible(moment):
                continue
            try:
                day = int(moment.get("day", -1))
            except (TypeError, ValueError):
                continue
            target = grouped.setdefault(day, {
                "day": day,
                "date": str(moment.get("date", "Unknown date")),
                "items": [],
            })
            legacy_item = {
                "category": str(moment.get("category", "general")),
                "text": str(moment.get("text", "")),
            }
            if moment.get("metadata"):
                legacy_item["metadata"] = dict(moment.get("metadata") or {})
            if legacy_item["text"] and not any(
                item.get("category") == legacy_item["category"] and item.get("text") == legacy_item["text"]
                for item in target["items"] if hasattr(item, "get")
            ):
                target["items"].append(legacy_item)

        return [grouped[day] for day in sorted(grouped) if grouped[day]["items"]][-10:]

    def record_daily_report_moment(report_entry):
        if not report_entry or not hasattr(report_entry, "get"):
            return False
        worker = report_entry.get("worker")
        if not worker or not hasattr(worker, "get"):
            return False
        result = str(report_entry.get("result", "Result") or "Result").strip()
        earnings = int(report_entry.get("earnings", 0) or 0)
        role = str(report_entry.get("profession", "work") or "work")
        text = "Worked as %s: %s, earned $%s." % (role, result, earnings)
        metadata = {
            "result": result,
            "earnings": earnings,
            "building_type_id": report_entry.get("building_type_id"),
            "profession_id": report_entry.get("profession_id"),
            "nsfw_content": bool(report_entry.get("nsfw_content", False)),
            "worker_nsfw": bool(report_entry.get("worker_nsfw", False)),
            "content_classified": True,
        }
        return add_worker_activity_items(worker, "work", [text], metadata)

    def record_event_choice_moment(choice, event, worker, outcome):
        """Record worker involvement; event chaining remains in the existing event_flags schema."""
        if not worker:
            return False
        event_id = str((event or {}).get("id", "event"))
        option_text = str((choice or {}).get("option", "Decision"))
        metadata = {
            "event_id": event_id,
            "arc_id": (event or {}).get("arc_id"),
            "arc_stage": (event or {}).get("arc_stage"),
            "arc_kind": (event or {}).get("arc_kind"),
            "nsfw_content": bool(event_has_restricted_content(event, choice)),
            "worker_nsfw": bool(content_object_is_restricted(worker)),
            "content_classified": True,
        }
        text = "%s — %s (%s)." % (event_id.replace("_", " ").title(), option_text, outcome)
        return add_worker_activity_items(worker, "decision", [text], metadata)

    def auto_advance_day_completed_without_event(result):
        """process_next_day returns 'tavern' for an ordinary completed day."""
        return result in (None, "tavern")

    def auto_advance_day_was_processed(start_total_days, end_total_days):
        """An initial-bankruptcy return does not advance the calendar or produce a new report."""
        return int(end_total_days) > int(start_total_days)

    def initialize_auto_advance_summary(requested_days):
        store.auto_advance_day_reports = []
        store.auto_advance_summary = {
            "requested_days": int(requested_days),
            "days_processed": 0,
            "start_money": int(getattr(store, "money", 0) or 0),
            "end_money": int(getattr(store, "money", 0) or 0),
            "earnings": 0,
            "costs": 0,
            "critical_events": 0,
            "stop_reason": "Requested span completed",
        }
        return store.auto_advance_summary

    def capture_auto_advance_day():
        from fm_performance.reporting import copy_report_without_worker

        archive_index = len(getattr(store, "auto_advance_day_reports", []) or []) + 1
        archive_date = "%s/%s/%s" % (
            int(getattr(store, "current_day", 1) or 1),
            int(getattr(store, "current_month", 1) or 1),
            int(getattr(store, "current_year", 1) or 1),
        )
        reports = []
        for report in getattr(store, "daily_report", []) or []:
            if hasattr(report, "items"):
                source_worker = report.get("worker")
                used_skill = report.get("used_skill")
                used_skill_value = report.get("used_skill_value")
                if used_skill_value is None and source_worker and used_skill and used_skill != "N/A":
                    calculator = globals().get("calculate_skill_with_traits")
                    try:
                        if callable(calculator):
                            used_skill_value = int(calculator(source_worker, used_skill, include_libido=False))
                        else:
                            used_skill_value = int((source_worker.get("skills", {}) or {}).get(used_skill, 0) or 0)
                    except (TypeError, ValueError, KeyError):
                        used_skill_value = None
                # The stable name and skill snapshot are enough. Project the live
                # worker graph out before copying so its inventory/history is never traversed.
                archived_report = copy_report_without_worker(report)
                if used_skill_value is not None:
                    archived_report["used_skill_value"] = used_skill_value
                archived_report["_advance_day_index"] = archive_index
                archived_report["_advance_date"] = archive_date
                reports.append(archived_report)
        building_displays = {
            report.get("building"): report.get("building_display_name")
            for report in reports
            if report.get("building") and report.get("building_display_name")
        }
        building_type_ids = {
            report.get("building"): report.get("building_type_id")
            for report in reports
            if report.get("building") and report.get("building_type_id")
        }
        for building_name, building in (getattr(store, "available_buildings", {}) or {}).items():
            if not hasattr(building, "get"):
                continue
            is_owned = building.get("owned") is True or (building.get("owned") is not False and building_name in (getattr(store, "owned_buildings", []) or []))
            if not is_owned:
                continue
            btype_id = building.get("type")
            building_type_ids.setdefault(building_name, btype_id)
            if building_name in building_displays:
                continue
            btype = next((entry for entry in (globals().get("building_types_json", {}) or {}).get("building_types", []) if entry.get("id") == btype_id), None)
            type_name = (btype or {}).get("name", btype_id or "Building")
            parts = str(building_name).split("_")
            default_name = "Building %s" % parts[1] if len(parts) > 1 else str(building_name).replace("_", " ")
            custom_name = (getattr(store, "custom_names", {}) or {}).get(building_name, default_name)
            building_displays[building_name] = "%s: %s" % (type_name, custom_name)
        day_record = {
            "index": archive_index,
            "day": int(getattr(store, "current_day", 1) or 1),
            "month": int(getattr(store, "current_month", 1) or 1),
            "year": int(getattr(store, "current_year", 1) or 1),
            "date": archive_date,
            "reports": reports,
            "building_displays": building_displays,
            "building_type_ids": building_type_ids,
            "building_costs": {
                building_name: int(building.get("costs", 0) or 0)
                for building_name, building in (getattr(store, "available_buildings", {}) or {}).items()
                if hasattr(building, "get") and building.get("owned", False)
            },
        }
        archive = list(getattr(store, "auto_advance_day_reports", []) or [])
        archive.append(day_record)
        store.auto_advance_day_reports = archive
        return day_record

    def get_auto_advance_reports():
        reports = []
        for day_record in getattr(store, "auto_advance_day_reports", []) or []:
            reports.extend([report for report in (day_record.get("reports", []) or []) if hasattr(report, "get")])
        return reports

    def get_auto_advance_report_costs():
        costs = {}
        for day_record in getattr(store, "auto_advance_day_reports", []) or []:
            displays = day_record.get("building_displays", {}) or {}
            type_ids = day_record.get("building_type_ids", {}) or {}
            for building_name, amount in (day_record.get("building_costs", {}) or {}).items():
                raw_display = displays.get(building_name, building_name)
                resolver = globals().get("get_report_building_display")
                if callable(resolver):
                    display_name = resolver({
                        "building": building_name,
                        "building_type_id": type_ids.get(building_name),
                        "building_display_name": raw_display,
                    })
                else:
                    display_name = raw_display
                costs[display_name] = costs.get(display_name, 0) + int(amount or 0)
        return costs

    def get_auto_advance_report_title(days_processed):
        days = max(0, int(days_processed or 0))
        return "Advance Report: %s day%s" % (days, "" if days == 1 else "s")

    def update_auto_advance_summary():
        summary = store.auto_advance_summary
        summary["days_processed"] = int(summary.get("days_processed", 0)) + 1
        summary["end_money"] = int(getattr(store, "money", 0) or 0)
        summary["earnings"] = int(summary.get("earnings", 0)) + sum(int(report.get("earnings", 0) or 0) for report in (getattr(store, "daily_report", []) or []))
        summary["costs"] = int(summary.get("costs", 0)) + sum(int(building.get("costs", 0) or 0) for building in (getattr(store, "available_buildings", {}) or {}).values() if hasattr(building, "get") and building.get("owned", False))
        summary["critical_events"] = int(summary.get("critical_events", 0)) + len([report for report in (getattr(store, "daily_report", []) or []) if report.get("result") in ("Critical Success", "Failure", "Refused")])
        return summary
