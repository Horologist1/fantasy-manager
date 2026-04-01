#!/usr/bin/env python3
"""Normalize daily story energy: failure/mediocre/success = -base, critical = -(base-1). See docstring in repo."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILES = [
    ROOT / "game" / "data" / "buildings" / "building_types.json",
    ROOT / "game" / "data" / "buildings" / "special_buildings.json",
]
WORK_OUTCOMES = ("failure", "mediocre", "success", "critical_success")


def difficulty_base(difficulty: Any) -> int:
    d = str(difficulty or "").lower().strip()
    if d in ("easy", "none", ""):
        return 3
    return 4


def iter_profession_stories(data: dict[str, Any]):
    for bt in data.get("building_types", []) or []:
        b_id = bt.get("id", "")
        for pr in bt.get("professions", []) or []:
            p_id = pr.get("id", "")
            base = difficulty_base(pr.get("difficulty"))
            for st in pr.get("daily_stories", []) or []:
                yield b_id, p_id, pr, base, st


def normalize_story_consequences(story: dict[str, Any], base: int, profession_id: str) -> int:
    if profession_id == "rest":
        return 0
    cons_root = story.get("consequences")
    if not isinstance(cons_root, dict):
        return 0
    changed = 0
    for outcome in WORK_OUTCOMES:
        block = cons_root.get(outcome)
        if not isinstance(block, dict):
            continue
        if "energy" not in block:
            continue
        ev = block.get("energy")
        if isinstance(ev, (int, float)) and ev > 0:
            continue
        new_v = -(base - 1) if outcome == "critical_success" else -base
        if block.get("energy") != new_v:
            block["energy"] = new_v
            changed += 1
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, action="append", dest="files")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    paths = list(args.files or DEFAULT_FILES)
    total = 0
    for path in paths:
        if not path.is_file():
            print("Skip missing:", path, file=sys.stderr)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        n = 0
        for _b_id, _p_id, pr, base, st in iter_profession_stories(data):
            n += normalize_story_consequences(st, base, str(pr.get("id", "")))
        print(path, "energy fields set:", n)
        total += n
        if not args.dry_run:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("TOTAL", total)
    if args.dry_run:
        print("Dry run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
