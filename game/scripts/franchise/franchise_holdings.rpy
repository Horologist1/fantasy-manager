# Aggregated Franchise Holdings: remote businesses outside normal building simulation.

default franchise_holdings = {}
default franchise_last_summary = {}

init python:
    from fm_franchise.holdings import (
        ESTABLISH_COST as FRANCHISE_ESTABLISH_COST,
        FRANCHISE_TYPES,
        MAX_LEVEL as FRANCHISE_MAX_LEVEL,
        daily_franchise_result,
        franchise_upgrade_cost,
        normalize_holdings,
        visible_franchise_types,
    )

    def _franchise_holdings_store():
        normalized = normalize_holdings(getattr(store, "franchise_holdings", {}))
        store.franchise_holdings = normalized
        return normalized

    def franchise_holdings_unlocked():
        """Remote holdings become available only after the final objective."""
        return bool(getattr(store, "objective_16_complete", False))

    def worker_is_in_franchise(worker):
        if not worker or not hasattr(worker, "get"):
            return False
        type_id = str(worker.get("franchise_id", "") or "").strip().lower()
        return type_id in _franchise_holdings_store()

    def franchise_type_is_visible(type_id):
        type_id = str(type_id or "").strip().lower()
        return type_id in visible_franchise_types(bool(getattr(persistent, "nsfw_enabled", False)))

    def franchise_workers(type_id=None):
        wanted = str(type_id or "").strip().lower() if type_id else None
        result = []
        for worker in (getattr(store, "workers", []) or []):
            if not hasattr(worker, "get"):
                continue
            assigned = str(worker.get("franchise_id", "") or "").strip().lower()
            if assigned and assigned in _franchise_holdings_store() and (wanted is None or assigned == wanted):
                result.append(worker)
        return result

    def get_franchise_worker_candidates():
        candidates = [
            worker for worker in (getattr(store, "workers", []) or [])
            if hasattr(worker, "get") and not worker_is_in_franchise(worker)
        ]
        try:
            candidates = workers_filtered_by_gender(candidates)
        except Exception:
            candidates = list(candidates)
        candidates = [
            worker for worker in candidates
            if getattr(persistent, "nsfw_enabled", False) or not content_object_is_restricted(worker)
        ]
        return sorted(candidates, key=lambda worker: str(worker.get("name", "")).casefold())

    def establish_franchise(type_id):
        if not franchise_holdings_unlocked():
            return False
        type_id = str(type_id or "").strip().lower()
        if type_id not in FRANCHISE_TYPES or not franchise_type_is_visible(type_id):
            return False
        holdings = _franchise_holdings_store()
        if type_id in holdings:
            return False
        if int(getattr(store, "money", 0) or 0) < FRANCHISE_ESTABLISH_COST:
            renpy.notify("Not enough money to establish this franchise.")
            return False
        holdings[type_id] = {"type": type_id, "level": 1}
        store.money = int(store.money) - FRANCHISE_ESTABLISH_COST
        renpy.notify("%s established." % FRANCHISE_TYPES[type_id]["name"])
        renpy.restart_interaction()
        return True

    def upgrade_franchise(type_id):
        type_id = str(type_id or "").strip().lower()
        holding = _franchise_holdings_store().get(type_id)
        if not holding or not franchise_type_is_visible(type_id):
            return False
        cost = franchise_upgrade_cost(holding.get("level", 1))
        if cost is None:
            return False
        if int(getattr(store, "money", 0) or 0) < cost:
            renpy.notify("Not enough money to upgrade this franchise.")
            return False
        store.money = int(store.money) - cost
        holding["level"] = min(FRANCHISE_MAX_LEVEL, int(holding.get("level", 1)) + 1)
        renpy.notify("%s upgraded to level %d." % (FRANCHISE_TYPES[type_id]["name"], holding["level"]))
        renpy.restart_interaction()
        return True

    def assign_worker_to_franchise(worker, type_id):
        type_id = str(type_id or "").strip().lower()
        if type_id not in _franchise_holdings_store() or not franchise_type_is_visible(type_id):
            return False
        if not worker or not hasattr(worker, "get"):
            return False
        worker_name = worker.get("name")
        canonical = next(
            (item for item in (getattr(store, "workers", []) or []) if hasattr(item, "get") and item.get("name") == worker_name),
            None,
        )
        if canonical is None or worker_is_in_franchise(canonical):
            return False
        unassign_worker(canonical)
        canonical["assigned_building"] = "Unassigned"
        canonical["franchise_id"] = type_id
        canonical["franchise_since_day"] = calculate_total_days()
        clear_worker_autorest_state(canonical)
        try:
            canonical["_activity_log_snapshot"] = build_worker_activity_snapshot(canonical)
        except Exception:
            pass
        renpy.notify("%s sent to %s." % (worker_name, FRANCHISE_TYPES[type_id]["name"]))
        renpy.restart_interaction()
        return True

    def return_worker_from_franchise(worker):
        if not worker or not hasattr(worker, "get"):
            return False
        worker_name = worker.get("name")
        canonical = next(
            (item for item in (getattr(store, "workers", []) or []) if hasattr(item, "get") and item.get("name") == worker_name),
            None,
        )
        if canonical is None or not worker_is_in_franchise(canonical):
            return False
        canonical.pop("franchise_id", None)
        canonical.pop("franchise_since_day", None)
        canonical["assigned_building"] = "Unassigned"
        clear_worker_autorest_state(canonical)
        try:
            canonical["_activity_log_snapshot"] = build_worker_activity_snapshot(canonical)
        except Exception:
            pass
        renpy.notify("%s returned to the active roster unassigned." % worker_name)
        renpy.restart_interaction()
        return True

    def return_all_hidden_franchise_workers():
        returned = 0
        for worker in list(franchise_workers()):
            type_id = str(worker.get("franchise_id", "") or "").strip().lower()
            if not franchise_type_is_visible(type_id) and return_worker_from_franchise(worker):
                returned += 1
        return returned

    def toggle_franchise_skill(type_id, skill_name):
        type_id = str(type_id or "").strip().lower()
        holding = _franchise_holdings_store().get(type_id)
        definition = FRANCHISE_TYPES.get(type_id)
        skill_name = str(skill_name or "")
        if not holding or not definition or skill_name not in definition["skills"] or not franchise_type_is_visible(type_id):
            return False
        enabled = list(holding.get("enabled_skills") or definition["skills"])
        if skill_name in enabled:
            if len(enabled) <= 1:
                renpy.notify("At least one service skill must remain enabled.")
                return False
            enabled.remove(skill_name)
        else:
            enabled.append(skill_name)
        holding["enabled_skills"] = [skill for skill in definition["skills"] if skill in enabled]
        renpy.restart_interaction()
        return True

    def franchise_projected_result(type_id, total_day=None):
        type_id = str(type_id or "").strip().lower()
        holding = _franchise_holdings_store().get(type_id)
        if not holding:
            return daily_franchise_result(type_id, 1, [], 0)
        if total_day is None:
            total_day = calculate_total_days()
        enabled = holding.get("enabled_skills")
        return daily_franchise_result(
            type_id,
            holding.get("level", 1),
            franchise_workers(type_id),
            total_day,
            enabled_skills=enabled,
            income_multiplier=1.0,
        )

    def process_franchise_holdings_day():
        """Run every remote business once and append exactly one aggregate report row."""
        holdings = _franchise_holdings_store()
        if not holdings:
            store.franchise_last_summary = {}
            return None
        total_day = calculate_total_days()
        try:
            management = getattr(store, "management_skills", {}) or {}
            income_multiplier = 1.0 + 0.1 * int(management.get("business_acumen", 0) or 0)
            income_multiplier *= float(get_difficulty_earnings_mult())
        except Exception:
            income_multiplier = 1.0

        total_income = 0
        total_workers = 0
        active_count = 0
        by_type = {}
        for type_id, holding in holdings.items():
            workers_here = franchise_workers(type_id)
            result = daily_franchise_result(
                type_id,
                holding.get("level", 1),
                workers_here,
                total_day,
                enabled_skills=holding.get("enabled_skills"),
                income_multiplier=income_multiplier,
            )
            by_type[type_id] = result
            if workers_here:
                active_count += 1
            total_income += int(result.get("income", 0) or 0)
            total_workers += int(result.get("worker_count", 0) or 0)
            for worker in workers_here:
                training = (result.get("worker_training", {}) or {}).get(worker.get("name"), {})
                for skill_name, uses in training.items():
                    if skill_name not in (worker.get("skills", {}) or {}):
                        continue
                    worker.setdefault("skill_uses", {})
                    worker["skill_uses"][skill_name] = int(worker["skill_uses"].get(skill_name, 0) or 0) + int(uses)
                try:
                    update_skill_levels_for_worker(
                        worker,
                        silent=True,
                        record_delta=False,
                        adjust_rebelliousness=False,
                    )
                except TypeError:
                    update_skill_levels_for_worker(worker)
                try:
                    worker["_activity_log_snapshot"] = build_worker_activity_snapshot(worker)
                except Exception:
                    pass

        summary = {
            "income": total_income,
            "workers": total_workers,
            "franchises": active_count,
            "by_type": by_type,
        }
        store.franchise_last_summary = summary
        if total_workers <= 0:
            return summary

        report_entry = {
            "worker_name": "Franchise Holdings",
            "profession": "Managed Enterprises",
            "building": "Franchise Holdings",
            "building_type": "franchise_holdings",
            "description": "%d %s generated $%d through %d remote workers." % (
                active_count,
                "franchise" if active_count == 1 else "franchises",
                total_income,
                total_workers,
            ),
            "result": "Success",
            "earnings": total_income,
            "used_skill": "Aggregated",
            "roll": "N/A",
            "trait_roll": None,
            "trait_success_messages": [],
            "group_event": True,
            "loot": [],
            "story_image": None,
            "franchise_summary": True,
            "content_classified": True,
            "nsfw_content": False,
        }
        daily_report.append(report_entry)
        return summary
