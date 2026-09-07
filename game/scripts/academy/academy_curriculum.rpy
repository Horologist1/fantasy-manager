# Directed Academy curriculum: runtime state and UI-safe adapters.
# The pure rule engine is loaded by core/python_package_preload.rpy.

init python:
    def _academy_building_type():
        return next(
            (entry for entry in (building_types_json.get("building_types", []) or [])
             if str(entry.get("id", "")).strip().lower() == "academy"),
            None,
        )

    def _academy_course(course_id):
        academy_type = _academy_building_type()
        if not academy_type:
            return None
        wanted = str(course_id or "").strip().lower()
        return next(
            (entry for entry in (academy_type.get("professions", []) or [])
             if str(entry.get("id", "")).strip().lower() == wanted),
            None,
        )

    def _academy_focus_store(create=False):
        academy = available_buildings.get("Academy")
        if not hasattr(academy, "get"):
            return None
        focuses = academy.get("training_focus")
        if not hasattr(focuses, "get"):
            if not create:
                return {}
            focuses = {}
            academy["training_focus"] = focuses
        return focuses

    def _academy_visible_skill_names():
        return [name for name in skill_order if is_skill_visible(name)]

    def _academy_allowed_focus_skills(profession):
        try:
            from fm_academy.curriculum import allowed_focus_skills
            return allowed_focus_skills(
                profession,
                visible_skills=_academy_visible_skill_names(),
            )
        except Exception as e:
            renpy.log("Academy curriculum choices unavailable: %r" % (e,))
            return []

    def get_academy_training_focus(course_id):
        """Return a validated focus for a course, or None for Flexible mode."""
        profession = _academy_course(course_id)
        focuses = _academy_focus_store(False) or {}
        raw_focus = focuses.get(str(course_id or ""), None)
        if not profession or not raw_focus:
            return None
        try:
            from fm_academy.curriculum import normalize_focus
            return normalize_focus(
                profession,
                raw_focus,
                _academy_allowed_focus_skills(profession),
            )
        except Exception as e:
            renpy.log("Academy curriculum validation failed for %s: %r" % (course_id, e))
            return None

    def get_academy_curriculum_rows():
        """Build render-only rows without mutating save state."""
        academy_type = _academy_building_type()
        if not academy_type:
            return []
        focuses = _academy_focus_store(False) or {}
        academy = available_buildings.get("Academy", {}) or {}
        jobs = academy.get("servant_jobs", {}) or {}
        rows = []
        for profession in academy_type.get("professions", []) or []:
            course_id = str(profession.get("id", ""))
            curriculum = profession.get("training_curriculum") or {}
            if not curriculum or not profession_is_visible(profession, academy_type):
                continue
            allowed = _academy_allowed_focus_skills(profession)
            raw = focuses.get(course_id, {}) or {}
            fixed_primary = str(curriculum.get("fixed_primary") or "").strip()
            primary = fixed_primary or str(raw.get("primary") or "").strip()
            secondary = str(raw.get("secondary") or "").strip()
            valid = get_academy_training_focus(course_id)
            students = sum(
                1 for job_id in jobs.values()
                if str(job_id or "").strip().lower() == course_id.lower()
            )
            rows.append({
                "id": course_id,
                "name": profession.get("name", course_id),
                "primary": primary if primary in allowed else "",
                "secondary": secondary if secondary in allowed and secondary != primary else "",
                "primary_fixed": bool(fixed_primary),
                "primary_uses": int(curriculum.get("primary_uses", 0) or 0),
                "secondary_uses": int(curriculum.get("secondary_uses", 0) or 0),
                "focused": bool(valid),
                "students": students,
            })
        return rows

    def get_academy_curriculum_skill_choices(course_id, slot):
        profession = _academy_course(course_id)
        if not profession or slot not in ("primary", "secondary"):
            return []
        curriculum = profession.get("training_curriculum") or {}
        if slot == "primary" and curriculum.get("fixed_primary"):
            return []
        allowed = _academy_allowed_focus_skills(profession)
        focuses = _academy_focus_store(False) or {}
        raw = focuses.get(str(course_id or ""), {}) or {}
        fixed_primary = str(curriculum.get("fixed_primary") or "").strip()
        other = fixed_primary if slot == "secondary" and fixed_primary else str(
            raw.get("secondary" if slot == "primary" else "primary") or ""
        ).strip()
        return [name for name in allowed if name != other]

    def set_academy_curriculum_skill(course_id, slot, skill_name):
        profession = _academy_course(course_id)
        if not profession or slot not in ("primary", "secondary"):
            return False
        curriculum = profession.get("training_curriculum") or {}
        if slot == "primary" and curriculum.get("fixed_primary"):
            return False
        allowed = _academy_allowed_focus_skills(profession)
        selected = next(
            (name for name in allowed if name.lower() == str(skill_name or "").strip().lower()),
            None,
        )
        if not selected:
            return False

        focuses = _academy_focus_store(True)
        if focuses is None:
            return False
        raw = dict(focuses.get(str(course_id), {}) or {})
        fixed_primary = str(curriculum.get("fixed_primary") or "").strip()
        if fixed_primary:
            raw["primary"] = fixed_primary
        raw[slot] = selected
        other_slot = "secondary" if slot == "primary" else "primary"
        if raw.get(other_slot) == selected:
            raw.pop(other_slot, None)
            if fixed_primary:
                raw["primary"] = fixed_primary
        focuses[str(course_id)] = raw

        valid = get_academy_training_focus(course_id)
        if valid:
            renpy.notify(
                "%s: %s +7 / %s +3" %
                (profession.get("name", "Course"), valid["primary"], valid["secondary"])
            )
        else:
            renpy.notify("Choose the other skill to complete this curriculum.")
        renpy.restart_interaction()
        return True

    def reset_academy_curriculum(course_id):
        focuses = _academy_focus_store(True)
        if focuses is None:
            return False
        focuses.pop(str(course_id or ""), None)
        profession = _academy_course(course_id)
        renpy.notify("%s returned to Flexible training." % ((profession or {}).get("name", "Course"),))
        renpy.restart_interaction()
        return True
