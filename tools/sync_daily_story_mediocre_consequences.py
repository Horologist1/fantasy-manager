#!/usr/bin/env python3
r"""Set consequences.mediocre = copy of consequences.failure for daily stories. See --help."""
from __future__ import annotations
import argparse, copy, json, sys
from pathlib import Path

def _sync(data: dict) -> tuple[int, int]:
    seen = upd = 0
    for bt in data.get("building_types", []) or []:
        for prof in bt.get("professions", []) or []:
            for story in prof.get("daily_stories", []) or []:
                seen += 1
                cons = story.get("consequences")
                if not isinstance(cons, dict) or "failure" not in cons:
                    continue
                nm = copy.deepcopy(cons["failure"])
                if cons.get("mediocre") != nm:
                    cons["mediocre"] = nm
                    upd += 1
    return seen, upd

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    defs = [
        root / "game/data/buildings/building_types.json",
        root / "game/data/buildings/special_buildings.json",
    ]
    ext = root / "game/data/buildings/daily_story_extensions"
    if ext.is_dir():
        defs.extend(sorted(ext.glob("*.json")))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    paths = list(a.files) if a.files else defs
    if not a.dry_run and not a.write:
        print("Specify --dry-run or --write", file=sys.stderr)
        return 2
    ts = tu = 0
    for p in paths:
        if not p.is_file():
            print("skip", p, file=sys.stderr)
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        s, u = _sync(data)
        ts += s
        tu += u
        print(f"{p.name}: daily_stories={s} mediocre_synced={u}")
        if a.write and u:
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TOTAL daily_stories_seen={ts} mediocre_updates={tu}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
