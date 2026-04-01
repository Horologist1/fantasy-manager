#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


SUPPORTED_WORKER_SELECTION = {"none", "random", "choose"}
SUPPORTED_PLAYER_GENDER_REQUIREMENT = {"male", "female", "lord", "lady"}
SUPPORTED_PREFIXES = (
    "has_flag:",
    "flag_value:",
    "after_days_from_flag:",
    "exact_date:",
    "has_worker:",
    "not_has_worker:",
    "after_date:",
    "before_days:",
    "after_days:",
)
COMPARATORS = ("==", "!=", ">=", "<=", ">", "<")


def _looks_supported_condition(expr: str) -> bool:
    expr = (expr or "").strip()
    if not expr:
        return True
    if " AND " in expr:
        return all(_looks_supported_condition(p) for p in expr.split(" AND "))
    if " OR " in expr:
        return all(_looks_supported_condition(p) for p in expr.split(" OR "))
    if expr in ("True", "False"):
        return True
    if any(expr.startswith(p) for p in SUPPORTED_PREFIXES):
        return True
    return any(op in expr for op in COMPARATORS)


def _load_events(path: Path) -> List[Dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [v for v in data.values() if isinstance(v, dict)]
    raise ValueError(f"{path} must contain a JSON array or dict of events.")


def _validate_all_events(all_events: List[Dict]) -> Tuple[List[str], List[str]]:
    """Core validation logic on a list of events (each should have _file)."""
    errors: List[str] = []
    warnings: List[str] = []

    ids = [e.get("id") for e in all_events if e.get("id")]
    dup_ids = [k for k, v in Counter(ids).items() if v > 1]
    for dup in dup_ids:
        errors.append(f"[global] duplicate_event_id: {dup}")

    for ev in all_events:
        ev_id = ev.get("id", "<missing-id>")
        where = f"{ev.get('_file')}::{ev_id}"

        if not ev.get("id"):
            errors.append(f"[{where}] missing_event_id")

        worker_selection = ev.get("worker_selection", "none")
        if worker_selection not in SUPPORTED_WORKER_SELECTION:
            errors.append(
                f"[{where}] invalid_worker_selection: {worker_selection!r}"
            )

        pgr = ev.get("player_gender_requirement", None)
        if pgr is not None:
            if not isinstance(pgr, str) or not str(pgr).strip():
                errors.append(
                    f"[{where}] player_gender_requirement_must_be_non_empty_string_or_null"
                )
            elif str(pgr).strip().lower() not in SUPPORTED_PLAYER_GENDER_REQUIREMENT:
                errors.append(
                    f"[{where}] invalid_player_gender_requirement: {pgr!r} "
                    f"(expected one of {sorted(SUPPORTED_PLAYER_GENDER_REQUIREMENT)})"
                )

        if ev.get("worker_gender_requirement", None) is not None:
            warnings.append(
                f"[{where}] worker_gender_requirement_on_event_ignored: "
                "not applied by random/building event pool (select_possible_events); "
                "use daily story worker_gender_requirement or interaction worker_gender instead"
            )

        choices = ev.get("choices")
        if not isinstance(choices, list) or not choices:
            errors.append(f"[{where}] choices_missing_or_empty")
            choices = []

        if ev.get("limited", False):
            max_occ = ev.get("max_occurrences")
            if not isinstance(max_occ, int) or max_occ < 1:
                errors.append(
                    f"[{where}] limited_true_requires_positive_max_occurrences"
                )

        if "cooldown_days" not in ev:
            warnings.append(f"[{where}] cooldown_days_missing (engine default applies)")
        elif not isinstance(ev.get("cooldown_days"), int) or ev.get("cooldown_days") < 0:
            errors.append(f"[{where}] cooldown_days_must_be_non_negative_int")

        if "required_building_traits" in ev:
            warnings.append(
                f"[{where}] required_building_traits_removed: key ignored/removed; use worker/profession gates instead"
            )

        rap = ev.get("required_active_professions")
        if rap is not None and not isinstance(rap, list):
            errors.append(f"[{where}] required_active_professions_must_be_list")
        elif isinstance(rap, list) and not all(isinstance(x, str) and x.strip() for x in rap):
            errors.append(f"[{where}] required_active_professions_must_be_non_empty_strings")

        fap = ev.get("forbidden_active_professions")
        if fap is not None and not isinstance(fap, list):
            errors.append(f"[{where}] forbidden_active_professions_must_be_list")
        elif isinstance(fap, list) and not all(isinstance(x, str) and x.strip() for x in fap):
            errors.append(f"[{where}] forbidden_active_professions_must_be_non_empty_strings")

        if isinstance(rap, list) and isinstance(fap, list):
            rset = {str(x).strip().lower() for x in rap if isinstance(x, str) and x.strip()}
            fset = {str(x).strip().lower() for x in fap if isinstance(x, str) and x.strip()}
            if rset & fset:
                warnings.append(
                    f"[{where}] required_active_professions_overlaps_forbidden_active_professions: {sorted(rset & fset)}"
                )

        if "required_building_worker_min_skill" in ev:
            m = ev.get("required_building_worker_min_skill")
            if m is not None and not isinstance(m, int):
                errors.append(f"[{where}] required_building_worker_min_skill_must_be_int_or_null")
            elif isinstance(m, int) and m < 0:
                errors.append(f"[{where}] required_building_worker_min_skill_must_be_non_negative")

        sk = ev.get("required_building_worker_skill")
        if sk is not None and (not isinstance(sk, str) or not sk.strip()):
            errors.append(f"[{where}] required_building_worker_skill_must_be_non_empty_string_or_null")

        cond_root = (ev.get("conditions") or {})
        for key in ("start_when", "stop_when"):
            value = cond_root.get(key)
            if isinstance(value, str) and value.strip() and not _looks_supported_condition(value):
                warnings.append(f"[{where}] {key}_condition_maybe_unsupported: {value!r}")

        for idx, ch in enumerate(choices):
            cwhere = f"{where}::choice[{idx}]"
            cond = ch.get("condition")
            if cond and worker_selection == "none" and cond != "building_skill":
                errors.append(
                    f"[{cwhere}] condition_requires_worker_but_worker_selection_none: {cond!r}"
                )

            if cond and ("message_success" not in ch or "message_failure" not in ch):
                warnings.append(
                    f"[{cwhere}] condition_without_explicit_success_failure_messages"
                )

            effect = ch.get("effect", {})
            # Align with script.rpy process_choice: success_chance only triggers a probability roll when
            # effect contains a "success" and/or "failure" branch. Many events keep success_chance: 0 as
            # schema metadata alongside flat keys only; the engine ignores it for rolls in that case.
            if isinstance(effect, dict) and "success_chance" in effect:
                has_s = "success" in effect
                has_f = "failure" in effect
                if has_s and has_f:
                    if "message_success" not in ch or "message_failure" not in ch:
                        errors.append(
                            f"[{cwhere}] success_chance_requires_message_success_and_message_failure"
                        )
                elif has_s or has_f:
                    warnings.append(
                        f"[{cwhere}] success_chance_with_single_branch: has success_chance but only one of success/failure; engine still rolls and uses missing branch as {{}}"
                    )
                    if "message_success" not in ch or "message_failure" not in ch:
                        warnings.append(
                            f"[{cwhere}] success_chance_single_branch_missing_messages"
                        )

            cond_choice = (ch.get("conditions") or {})
            for key in ("start_when", "stop_when"):
                value = cond_choice.get(key)
                if isinstance(value, str) and value.strip() and not _looks_supported_condition(value):
                    warnings.append(
                        f"[{cwhere}] {key}_condition_maybe_unsupported: {value!r}"
                    )

            rwf = ch.get("restrict_worker_effects_to_filter")
            if rwf is not None and not isinstance(rwf, bool):
                errors.append(f"[{cwhere}] restrict_worker_effects_to_filter_must_be_bool_or_null")

            ewf = ch.get("effect_worker_filter")
            if ewf is not None and not isinstance(ewf, dict):
                errors.append(f"[{cwhere}] effect_worker_filter_must_be_object_or_null")
            elif isinstance(ewf, dict):
                for list_key in (
                    "required_active_professions",
                    "forbidden_active_professions",
                    "required_traits",
                    "excluded_traits",
                ):
                    lv = ewf.get(list_key)
                    if lv is not None and not isinstance(lv, list):
                        errors.append(f"[{cwhere}] effect_worker_filter.{list_key}_must_be_list")
                    elif isinstance(lv, list) and not all(isinstance(x, str) and x.strip() for x in lv):
                        errors.append(
                            f"[{cwhere}] effect_worker_filter.{list_key}_must_be_list_of_non_empty_strings"
                        )
                for int_key in ("min_skill", "required_building_worker_min_skill"):
                    iv = ewf.get(int_key)
                    if iv is not None and not isinstance(iv, int):
                        errors.append(f"[{cwhere}] effect_worker_filter.{int_key}_must_be_int_or_null")
                    elif isinstance(iv, int) and iv < 0:
                        errors.append(f"[{cwhere}] effect_worker_filter.{int_key}_must_be_non_negative")
                for str_key in ("skill_name", "required_building_worker_skill", "required_trait"):
                    sv = ewf.get(str_key)
                    if sv is not None and (not isinstance(sv, str) or not str(sv).strip()):
                        errors.append(
                            f"[{cwhere}] effect_worker_filter.{str_key}_must_be_non_empty_string_or_null"
                        )

            mfs = ch.get("message_failure_worker_effect_skipped")
            if mfs is not None and not isinstance(mfs, str):
                errors.append(f"[{cwhere}] message_failure_worker_effect_skipped_must_be_string_or_null")

    return errors, warnings


def validate(files: Iterable[Path]) -> Tuple[List[str], List[str]]:
    """Load events from files and validate."""
    all_events: List[Dict] = []
    load_errors: List[str] = []
    for fp in files:
        if not fp.exists():
            continue
        try:
            events = _load_events(fp)
            for ev in events:
                ev["_file"] = str(fp)
            all_events.extend(events)
        except Exception as e:
            load_errors.append(f"[{fp}] load_error: {e}")
    errs, warns = _validate_all_events(all_events)
    return (load_errors + errs, warns)


def validate_events_list(events: List[Dict], source_name: str = "memory") -> Tuple[List[str], List[str]]:
    """Validate a list of event dicts (e.g. from editor memory)."""
    for ev in events:
        ev["_file"] = source_name
    return _validate_all_events(events)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate event mechanics for common/building random events."
    )
    parser.add_argument(
        "--files",
        nargs="+",
        default=[
            "game/data/events/events_common.json",
            "game/data/events/events_building.json",
            "game/data/events/events_seasonal.json",
            "game/data/events/events_shops.json",
            "game/data/events/events_special.json",
            "game/data/events/recruit/event_recruit_advanced_example.json",
        ],
        help="Event JSON files to validate.",
    )
    args = parser.parse_args()

    files = [Path(f) for f in args.files]
    errors, warnings = validate(files)

    print("Event mechanics validation")
    print(f"- files: {', '.join(str(f) for f in files)}")
    print(f"- errors: {len(errors)}")
    print(f"- warnings: {len(warnings)}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
