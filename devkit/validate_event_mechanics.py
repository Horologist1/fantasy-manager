#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


SUPPORTED_WORKER_SELECTION = {"none", "random", "choose"}
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
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array of events.")
    return data


def validate(files: Iterable[Path]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    all_events: List[Dict] = []
    for fp in files:
        events = _load_events(fp)
        for ev in events:
            ev["_file"] = str(fp)
        all_events.extend(events)

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
            if isinstance(effect, dict) and "success_chance" in effect:
                if "success" not in effect or "failure" not in effect:
                    errors.append(
                        f"[{cwhere}] success_chance_requires_success_and_failure_blocks"
                    )
                if "message_success" not in ch or "message_failure" not in ch:
                    errors.append(
                        f"[{cwhere}] success_chance_requires_message_success_and_message_failure"
                    )

            cond_choice = (ch.get("conditions") or {})
            for key in ("start_when", "stop_when"):
                value = cond_choice.get(key)
                if isinstance(value, str) and value.strip() and not _looks_supported_condition(value):
                    warnings.append(
                        f"[{cwhere}] {key}_condition_maybe_unsupported: {value!r}"
                    )

    return errors, warnings


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
