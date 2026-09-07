# building_logic.rpy
# Building logic and helpers. Building types are loaded in script.rpy (merge by id + daily_story_extensions).

init python:

    # Arena and Academy are map-only systems with dedicated interfaces. They
    # remain owned for save/state logic but never belong to generic building UI.
    SPECIAL_MAP_ONLY_BUILDING_TYPES = frozenset(("arena", "academy"))

    def is_standard_managed_building(building_name, building=None):
        """Return whether a building belongs in generic management lists."""
        normalized_name = str(building_name or "").strip().lower().replace(" ", "_")
        type_id = ""
        if hasattr(building, "get"):
            type_id = str(building.get("type", "") or "").strip().lower()
        return normalized_name not in SPECIAL_MAP_ONLY_BUILDING_TYPES and type_id not in SPECIAL_MAP_ONLY_BUILDING_TYPES

    def get_building(worker):
        """Returns the building object for a worker, or None if unassigned."""
        building_name = worker.get("assigned_building", "Unassigned")
        if building_name != "Unassigned":
            # Resolver accepts both "Building 1" and "Building_1" key formats
            building, _key = _resolve_building_by_name(building_name)
            return building
        return None

    def _resolve_building_by_name(building_name):
        """Find building in available_buildings by exact key or normalized match. Returns (building, actual_key) or (None, None)."""
        ab = getattr(store, "available_buildings", {})
        target_norm = _norm_building_key(building_name) if building_name else ""
        if not target_norm:
            return (None, None)
        # Try exact key first
        b = ab.get(building_name)
        if b and hasattr(b, "get"):
            return (b, building_name)
        # Search by normalized name (handles Building 1/2/3 vs Building_1/2/3, any format)
        for key, data in ab.items():
            if data and hasattr(data, "get") and _norm_building_key(key) == target_norm:
                return (data, key)
        return (None, None)

    store._resolve_building_by_name = _resolve_building_by_name

    # get_building_servants lives in script.rpy.

    def _norm_building_key(key):
        """Normalize for matching: Building 1 <-> Building_1."""
        if not key:
            return ""
        s = str(key).strip()
        if "_" in s:
            parts = s.split("_")
            if len(parts) >= 2 and parts[0].lower() == "building":
                return "Building " + parts[1]
        return s

    store._norm_building_key = _norm_building_key

    # sync_assigned_servants_for_building, validate_and_sync_buildings,
    # sync_building_assignments_from_workers all live in script.rpy.

    def content_object_is_restricted(value):
        """Classify one data object without consulting or mutating runtime state."""
        if not value or not hasattr(value, "get"):
            return False
        if value.get("nsfw", False) or value.get("nsfw_only", False) or value.get("nsfw_content", False):
            return True
        # Recurse only through explicit provenance containers. Traversing arbitrary
        # children would incorrectly classify mixed events by one restricted choice.
        for metadata_key in ("metadata", "content_metadata", "provenance"):
            metadata = value.get(metadata_key)
            if hasattr(metadata, "get") and content_object_is_restricted(metadata):
                return True
            if metadata and not hasattr(metadata, "strip") and hasattr(metadata, "__iter__"):
                if any(content_object_is_restricted(entry) for entry in metadata):
                    return True
        return False

    def building_type_is_visible(btype):
        """True when a building type may be exposed by the current content filter."""
        if not btype or not hasattr(btype, "get"):
            return True
        return bool(getattr(persistent, "nsfw_enabled", False) or not content_object_is_restricted(btype))

    def profession_is_visible(profession, btype=None):
        """True when both the parent building and profession are visible."""
        if not building_type_is_visible(btype):
            return False
        if not profession or not hasattr(profession, "get"):
            return True
        return bool(getattr(persistent, "nsfw_enabled", False) or not content_object_is_restricted(profession))

    def building_type_display_name(btype, fallback="Unassigned"):
        if not btype or not hasattr(btype, "get"):
            return fallback
        if not building_type_is_visible(btype):
            return "Restricted Business"
        return btype.get("name", fallback)

    def building_skill_display_name(btype, fallback="Skill"):
        if not btype or not hasattr(btype, "get") or not building_type_is_visible(btype):
            return fallback
        return btype.get("skill_name", fallback)

    def profession_display_name(profession, btype=None, fallback="Unassigned"):
        if not profession or not hasattr(profession, "get"):
            return fallback
        if not profession_is_visible(profession, btype):
            return "Hidden Role"
        return profession.get("name", fallback)

    def _resolve_report_content_context(report):
        """Resolve old report building aliases and infer profession ownership after type changes."""
        building_name = report.get("building") if hasattr(report, "get") else None
        building, _actual_key = _resolve_building_by_name(building_name) if building_name else (None, None)
        building = building or {}
        stored_btype_id = report.get("building_type_id") if hasattr(report, "get") else None
        btype_id = stored_btype_id or (building.get("type") if hasattr(building, "get") else None)
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        stored_profession_id = report.get("profession_id") if hasattr(report, "get") else None
        raw_name = str(stored_profession_id or report.get("profession", "")).strip().lower() if hasattr(report, "get") else ""
        matches = []
        story_matches = []
        event = (report.get("event_data", {}) or {}) if hasattr(report, "get") else {}
        event_id = str(event.get("id", "")).strip().lower() if hasattr(event, "get") else ""
        event_report = str(event.get("report", "")).strip().lower() if hasattr(event, "get") else ""
        candidate_types = [btype] if stored_btype_id and btype else building_types_json.get("building_types", [])
        for candidate_btype in candidate_types:
            for profession in candidate_btype.get("professions", []) or []:
                if raw_name and (str(profession.get("id", "")).strip().lower() == raw_name or str(profession.get("name", "")).strip().lower() == raw_name):
                    matches.append((candidate_btype, profession))
                for story in profession.get("daily_stories", []) or []:
                    story_id = str(story.get("id", "")).strip().lower()
                    story_report = str(story.get("report", "")).strip().lower()
                    if (event_id and story_id == event_id) or (event_report and story_report == event_report):
                        story_matches.append((candidate_btype, profession))
        return btype, matches, story_matches

    def _report_context_is_visible(report, btype, matches, story_matches):
        if not building_type_is_visible(btype):
            return False
        if report.get("building_type_id"):
            return not matches or any(profession_is_visible(profession, owner_btype) for owner_btype, profession in matches)
        evidence = story_matches if story_matches else matches
        if evidence:
            return all(profession_is_visible(profession, owner_btype) for owner_btype, profession in evidence)
        raw_name = str(report.get("profession", "")).strip().lower()
        return raw_name in ("", "n/a", "rest", "unassigned")

    def _resolve_report_worker(report):
        """Resolve a report's canonical worker without mutating legacy report data."""
        if not hasattr(report, "get"):
            return None
        embedded = report.get("worker")
        if hasattr(embedded, "get") and embedded:
            return embedded
        worker_name = str(report.get("worker_name", "") or "").strip()
        if not worker_name:
            return None
        for candidate in (getattr(store, "workers", []) or []):
            if hasattr(candidate, "get") and str(candidate.get("name", "")).strip() == worker_name:
                return candidate
        return None

    def get_report_profession_display(report):
        """Mask profession names in stored reports when their content is currently hidden."""
        raw_name = report.get("profession", "N/A") if hasattr(report, "get") else "N/A"
        if not hasattr(report, "get"):
            return raw_name
        if getattr(persistent, "nsfw_enabled", False):
            return raw_name
        if content_object_is_restricted(report) or report.get("worker_nsfw", False):
            return "Hidden Role"
        if content_object_is_restricted(_resolve_report_worker(report)):
            return "Hidden Role"
        btype, matches, story_matches = _resolve_report_content_context(report)
        if not _report_context_is_visible(report, btype, matches, story_matches):
            return "Hidden Role"
        return raw_name

    def get_report_building_display(report):
        """Prefer the immutable building label captured with the report; keep legacy fallback lazy."""
        if not hasattr(report, "get"):
            return str(report or "Unknown Building")
        if not getattr(persistent, "nsfw_enabled", False):
            if content_object_is_restricted(report):
                return "Restricted Business"
        archived_type_id = report.get("building_type_id")
        archived_type = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == archived_type_id), None)
        if archived_type and not building_type_is_visible(archived_type):
            return "Restricted Business"
        archived_display = report.get("building_display_name")
        if archived_display:
            return str(archived_display)
        building_name = report.get("building", "Unknown Building")
        building, actual_key = _resolve_building_by_name(building_name)
        building = building or {}
        resolved_name = actual_key or building_name
        btype_id = report.get("building_type_id") or building.get("type")
        btype = next((entry for entry in building_types_json.get("building_types", []) if entry.get("id") == btype_id), None)
        type_name = building_type_display_name(btype, "Unassigned" if btype_id is None else btype_id)
        parts = str(resolved_name).replace("_", " ").split()
        default_name = "Building %s" % parts[1] if len(parts) > 1 and parts[0].lower() == "building" else str(resolved_name).replace("_", " ")
        custom_names = getattr(store, "custom_names", {}) or {}
        display_name = custom_names.get(resolved_name, custom_names.get(building_name, default_name))
        return "%s: %s" % (type_name, display_name)

    def report_content_is_visible(report):
        """Protect stored daily reports when the content filter changes after generation."""
        if not hasattr(report, "get") or getattr(persistent, "nsfw_enabled", False):
            return True
        if content_object_is_restricted(report) or report.get("worker_nsfw", False):
            return False
        if content_object_is_restricted(_resolve_report_worker(report)):
            return False
        btype, matches, story_matches = _resolve_report_content_context(report)
        if not _report_context_is_visible(report, btype, matches, story_matches):
            return False
        event = report.get("event_data", {}) or {}
        if content_object_is_restricted(event):
            return False
        return True

    def report_worker_details_allowed(report):
        """Prevent a restricted report from becoming a navigation leak."""
        return bool(report_content_is_visible(report))

    def get_report_worker_display(report):
        """Return a neutral worker label while retaining the canonical reference."""
        if not hasattr(report, "get"):
            return "Unknown"
        if not report_worker_details_allowed(report):
            return "Hidden Worker"
        worker = report.get("worker", {}) or {}
        if hasattr(worker, "get") and worker.get("name"):
            return str(worker.get("name"))
        return str(report.get("worker_name", "Unknown"))

    store.content_object_is_restricted = content_object_is_restricted
    store.building_type_is_visible = building_type_is_visible
    store.profession_is_visible = profession_is_visible
    store.building_type_display_name = building_type_display_name
    store.building_skill_display_name = building_skill_display_name
    store.profession_display_name = profession_display_name
    store.get_report_profession_display = get_report_profession_display
    store.get_report_building_display = get_report_building_display
    store.report_content_is_visible = report_content_is_visible
    store.get_report_worker_display = get_report_worker_display
    store.report_worker_details_allowed = report_worker_details_allowed

    def resolve_profession_for_job(btype, job_id):
        """Match profession by id case-insensitively. Returns (display_name, profession_dict_or_None).
        Rest is recognized even when the building type omits a rest profession (e.g. Arena)."""
        if job_id is None:
            return ("Unassigned", None)
        jid = str(job_id).strip()
        jlow = jid.lower()
        if jlow in ("", "unassigned"):
            return ("Unassigned", None)
        if btype and not building_type_is_visible(btype):
            profession = next((p for p in btype.get("professions", []) if str(p.get("id", "")).strip().lower() == jlow), None)
            return ("Hidden Role", profession)
        if jlow == "rest":
            return ("Rest", None)
        if not btype:
            return (jid, None)
        for p in btype.get("professions", []) or []:
            pid = p.get("id")
            if pid is not None and str(pid).strip().lower() == jlow:
                return (profession_display_name(p, btype, jid), p)
        return (jid, None)

    store.resolve_profession_for_job = resolve_profession_for_job

    def get_worker_profession_and_building_display(worker):
        """Returns a string like 'Prostitute - Brothel: Building 1' or 'Unassigned'."""
        if not worker or not hasattr(worker, 'get'):
            return "Unassigned"
        building_name = worker.get("assigned_building", "Unassigned")
        if not building_name or building_name == "Unassigned":
            return "Unassigned"
        # Resolver accepts both "Building 1" and "Building_1"; keep the actual key
        # so custom_names / default_name lookups below use the canonical name.
        building, _actual_key = _resolve_building_by_name(building_name)
        if not building:
            return "Unassigned"
        building_name = _actual_key
        btype_id = building.get("type")
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        if not btype:
            parts = building_name.split('_')
            default_name = "Building " + parts[1] if len(parts) > 1 else building_name
            custom_names = getattr(store, 'custom_names', {}) or {}
            display_name = custom_names.get(building_name, default_name)
            return display_name
        parts = building_name.split('_')
        default_name = "Building " + parts[1] if len(parts) > 1 else building_name
        custom_names = getattr(store, 'custom_names', {}) or {}
        display_name = custom_names.get(building_name, default_name)
        type_name = building_type_display_name(btype, btype_id)
        building_display = type_name + ": " + display_name
        jobs = building.get("servant_jobs", {})
        job_id = jobs.get(worker.get("name", ""), "")
        if not job_id:
            return building_display
        prof_display, _ = resolve_profession_for_job(btype, job_id)
        return prof_display + " - " + building_display

    def change_building_type(building_name):
        building = available_buildings.get(building_name)
        if building:
            # Full reset to base state
            building.update({
                "base_level": 1,
                "skill": 10,  # base_level * 10
                "skill_bonus": 0,
                "reputation": 0,
                "type": None,
                "max_workers": {},
                "costs": 0,
                "autofill_quotas": {}  # per-profession auto-fill plan is type-specific
            })
            
            # Unassign all workers
            for worker in list(building["assigned_servants"]):
                unassign_worker(worker)
            
            # Clear all servant jobs
            building["servant_jobs"].clear()

    def get_building_reputation_cap(building):
        """Cap = building level * 200 + manager level * 200 (additive, each max 1000).
        Need level 2 + 400 rep to reach building ceiling; manager adds on top."""
        if not building:
            return 200
        building_level = building.get("base_level", 1)
        building_cap = min(1000, building_level * 200)
        jobs = building.get("servant_jobs", {})
        manager_level = 0
        for w in building.get("assigned_servants", []):
            job = str(jobs.get(w.get("name", ""), "")).lower()
            if "manager" in job:
                manager_level = max(manager_level, w.get("level", 1))
        manager_cap = min(1000, manager_level * 200) if manager_level else 0
        return building_cap + manager_cap

    def get_effective_reputation_for_events(building):
        """Effective reputation for bonus events: min(rep, level*200) + manager level*200.
        Requires BOTH building level AND reputation; manager adds on top.
        E.g. level 2 + 400 rep = 400 from building; manager level 2 adds 400 more."""
        if not building:
            return 0
        building_level = building.get("base_level", 1)
        reputation = building.get("reputation", 0)
        building_contribution = min(reputation, min(1000, building_level * 200))
        jobs = building.get("servant_jobs", {})
        manager_level = 0
        for w in building.get("assigned_servants", []):
            job = str(jobs.get(w.get("name", ""), "")).lower()
            if "manager" in job:
                manager_level = max(manager_level, w.get("level", 1))
        manager_contribution = min(1000, manager_level * 200) if manager_level else 0
        return building_contribution + manager_contribution

    def calculate_reputation(building_name):
        building = available_buildings.get(building_name)
        if not building:
            return 0
        cap = get_building_reputation_cap(building)
        # Use stored reputation if present, otherwise calculate base
        total_reputation = building.get("reputation", building.get("base_level", 1) * 10)
        for worker in building.get("assigned_servants", []):
            total_reputation -= 5
            # default=0 covers workers with an empty/missing skills dict
            highest_skill = max((int(skill) for skill in worker.get("skills", {}).values()), default=0)
            total_reputation += highest_skill // 10
        # Store and clamp to level-based cap (no growth above cap until level up)
        building["reputation"] = max(0, min(total_reputation, cap))
        return building["reputation"]

    def get_reputation_tier(reputation):
        """Returns the reputation tier name (matches dist build)."""
        rep = int(reputation)
        if rep < 50:
            return "Unknown"
        elif rep < 100:
            return "New"
        elif rep < 200:
            return "Recognized"
        elif rep < 300:
            return "Respected"
        elif rep < 400:
            return "Well-Known"
        elif rep < 500:
            return "Popular"
        elif rep < 600:
            return "Famous"
        elif rep < 700:
            return "Highly Regarded"
        elif rep < 800:
            return "Prestigious"
        elif rep < 900:
            return "Elite"
        else:
            return "Master"

    def get_reputation_bonus_stories(reputation, bonus_formula):
        """Calculate bonus stories per profession per day based on reputation and formula."""
        if not bonus_formula or bonus_formula == "0":
            return 0
        try:
            bonus = int(eval(bonus_formula, {"__builtins__": None}, {"reputation": int(reputation)}))
            return bonus
        except Exception:
            return 0

    def update_reputation_from_events(building_name, event_result):
        """Adjust building reputation based on event outcome."""
        building = available_buildings[building_name]
        # Get base reputation
        calculate_reputation(building_name)  # Updates building["reputation"]
        # Apply event-based adjustment
        reputation_change = {
            "critical success": 10,
            "success": 5,
            "mediocre": 0,
            "failure": -5
        }.get(event_result.lower(), 0)
        cap = get_building_reputation_cap(building)
        # Update and clamp to level cap (no growth above cap until level up)
        building["reputation"] = max(0, min(building["reputation"] + reputation_change, cap))

    def _get_first_profession_id_for_building(building):
        """Primera profesión del edificio que no sea Rest (para fallback en partidas antiguas sin previous_profession)."""
        if not building:
            return None
        btype_id = building.get("type")
        if not btype_id:
            return None
        btype = next((bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id), None)
        if not btype:
            return None
        for prof in btype.get("professions", []):
            pid = prof.get("id", "")
            if pid and "rest" not in str(pid).lower():
                return pid
        return None

    def _autorest_target_has_capacity(building, jobs, workers_here, profession_id):
        """Check active occupancy only; the resting worker already owns a reservation."""
        btype_id = (building or {}).get("type")
        btype = next(
            (bt for bt in building_types_json.get("building_types", []) if bt.get("id") == btype_id),
            None,
        )
        profession = next(
            (
                prof for prof in ((btype or {}).get("professions", []) or [])
                if str(prof.get("id", "")).strip().lower() == str(profession_id or "").strip().lower()
            ),
            None,
        )
        if not profession:
            return False
        from fm_autorest.capacity import can_restore_reserved_job
        return can_restore_reserved_job(
            jobs,
            workers_here,
            profession_id,
            get_max_daily_workers(building, profession),
        )

    def process_manager_auto_rest(restore_only=False):
        """Sistema robusto: Usa store.workers como única fuente de verdad."""
        _norm_pct = getattr(store, "normalize_auto_rest_entry_pct_for_worker", None)
        if not callable(_norm_pct):
            _norm_pct = lambda ww: 35

        # Agrupar por clave normalizada: acepta "Building 1" y "Building_1" (resolver)
        workers_by_building = {}
        for w in store.workers:
            b_name = w.get("assigned_building", "Unassigned")
            if b_name != "Unassigned":
                b_key = _norm_building_key(b_name)
                if b_key not in workers_by_building:
                    workers_by_building[b_key] = []
                workers_by_building[b_key].append(w)

        for b_name in store.owned_buildings:
            building, _key = _resolve_building_by_name(b_name)
            workers_here = workers_by_building.get(_norm_building_key(b_name), [])
            if not building or not workers_here:
                continue
            
            if "servant_jobs" not in building:
                building["servant_jobs"] = {}
            jobs = building["servant_jobs"]
            
            for w in workers_here:
                name = w.get("name")
                if not name:
                    continue
                current_job_raw = jobs.get(name, "")
                current_job_norm = str(current_job_raw).lower()
                
                if not current_job_raw or current_job_norm == "unassigned":
                    continue

                try:
                    energy = int(float(w.get("energy", 0) or 0))
                except (TypeError, ValueError):
                    energy = 0
                try:
                    max_e = int(calculate_max_energy(w))
                except (TypeError, ValueError):
                    continue
                if max_e <= 0:
                    continue

                try:
                    health = int(float(w.get("health", 0) or 0))
                except (TypeError, ValueError):
                    health = 0
                try:
                    max_h = int(calculate_max_health(w))
                except (TypeError, ValueError):
                    max_h = 0
                if max_h < 0:
                    max_h = 0

                entry_pct = _norm_pct(w)
                try:
                    pct_frac = float(entry_pct) / 100.0
                except (TypeError, ValueError):
                    pct_frac = 0.35

                rest_threshold_e = max_e * pct_frac
                restore_threshold_e = max_e * 0.95
                rest_threshold_h = max_h * pct_frac if max_h > 0 else None
                restore_threshold_h = max_h * 0.95 if max_h > 0 else None

                auto_on = bool(w.get("auto_rest", False))

                if not restore_only and auto_on and "rest" not in current_job_norm:
                    need_e = energy < rest_threshold_e
                    need_h = (rest_threshold_h is not None) and (health < rest_threshold_h)
                    if need_e or need_h:
                        w["previous_profession"] = current_job_raw
                        jobs[name] = "rest"
                        renpy.log(
                            f"AUTOREST: {name} puesto a descansar (E {energy}/{max_e}, H {health}/{max_h if max_h > 0 else 'N/A'}, umbral entrada {entry_pct}%)"
                        )

                elif "rest" in current_job_norm:
                    if auto_on:
                        energy_ok = energy >= restore_threshold_e
                        health_ok = (restore_threshold_h is None) or (health >= restore_threshold_h)
                        can_restore = energy_ok and health_ok
                    else:
                        can_restore = energy >= restore_threshold_e

                    if can_restore:
                        prev = w.get("previous_profession") or w.get("previous_job")
                        if not prev:
                            # Old saves and the former manual-Rest path could lose
                            # this field. Preserve the historical fallback, but
                            # migrate it into a reservation before restoring.
                            prev = _get_first_profession_id_for_building(building)
                            if prev:
                                w["previous_profession"] = prev
                        if prev and _autorest_target_has_capacity(building, jobs, workers_here, prev):
                            jobs[name] = prev
                            w.pop("previous_profession", None)
                            w.pop("previous_job", None)
                            renpy.log(f"AUTOREST: {name} vuelve a {jobs[name]} (Energía {energy}/{max_e}, Salud {health}/{max_h if max_h > 0 else 'N/A'})")
                        elif prev:
                            renpy.log(f"AUTOREST: {name} sigue descansando; {prev} está completo")

    # clear_worker_autorest_state and set_worker_job live in script.rpy.

    def _fmt_staffing_mult(value):
        try:
            v = float(value)
            if v == int(v):
                return str(int(v))
            s = "%g" % v
            return s
        except (TypeError, ValueError):
            return "?"

    def profession_mechanics_summary(prof):
        """UI hint: Essential; Bonus staffed if >1; Synergy only if presence_roll_bonus != 0 (positive / negative)."""
        if not prof or not hasattr(prof, "get"):
            return ""
        _ess = "#8b5a2a"
        _bon = "#7a6230"
        _syn = "#3d6470"
        _syn_neg = "#6b3d3d"
        lines = []
        has_pen = "staffing_penalty" in prof
        has_bon = "staffing_bonus" in prof
        if has_pen or has_bon:
            try:
                empty_m = float(prof.get("staffing_penalty", 1.0))
                staffed_m = float(prof.get("staffing_bonus", 1.0))
                if empty_m <= 0:
                    empty_m = 1.0
                if staffed_m <= 0:
                    staffed_m = 1.0
                if has_pen and abs(empty_m - 1.0) > 1e-9:
                    lines.append(
                        "{{color={0}}}Essential:{{/color}} ×{1} earnings if this job is empty.".format(
                            _ess,
                            _fmt_staffing_mult(empty_m),
                        )
                    )
                if staffed_m > 1.0:
                    lines.append(
                        "{{color={0}}}Bonus:{{/color}} ×{1} earnings if at least 1 worker is doing this job.".format(
                            _bon,
                            _fmt_staffing_mult(staffed_m),
                        )
                    )
            except (TypeError, ValueError):
                pass
        if "presence_roll_bonus" in prof:
            try:
                x = int(float(prof.get("presence_roll_bonus")))
                if x > 0:
                    lines.append(
                        "{{color={0}}}Synergy:{{/color}} +{1} skill bonus per worker to other jobs.".format(_syn, x)
                    )
                elif x < 0:
                    lines.append(
                        "{{color={0}}}Negative synergy:{{/color}} this role hinders other professions by −{1} to the skill check per worker in this job.".format(
                            _syn_neg,
                            abs(x),
                        )
                    )
                # x == 0: no synergy line (key may exist for schema completeness)
            except (TypeError, ValueError):
                pass
        return "\n".join(lines) if lines else ""
