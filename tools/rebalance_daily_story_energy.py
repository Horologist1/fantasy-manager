#!/usr/bin/env python3
# NOTE: For tiered energy (-3/-4, crit -1), use normalize_daily_story_energy.py.
r"""Scale negative energy in daily story consequences. See repo tools/."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILES = [
    ROOT / "game" / "data" / "buildings" / "building_types.json",
    ROOT / "game" / "data" / "buildings" / "special_buildings.json",
]

def iter_stories(data: dict[str, Any]):
    for bt in data.get("building_types", []) or []:
        b_id = bt.get("id", "")
        for pr in bt.get("professions", []) or []:
            p_id = pr.get("id", "")
            for st in pr.get("daily_stories", []) or []:
                yield b_id, p_id, st

def scale_negative_energy(consequences: dict[str, Any], factor: float, cap: int) -> int:
    changed = 0
    for _outcome, cons in consequences.items():
        if not isinstance(cons, dict):
            continue
        v = cons.get("energy")
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)) and v < 0:
            nv = -int(round(abs(float(v)) * factor))
            if cap > 0:
                nv = max(nv, -cap)
            if nv != int(v):
                cons["energy"] = nv
                changed += 1
    return changed

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, action="append", dest="files")
    ap.add_argument("--factor", type=float, default=2.0)
    ap.add_argument("--max-drain", type=int, default=24)
    ap.add_argument("--academy-success-energy", type=int, default=-3)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    paths = list(args.files or DEFAULT_FILES)
    total_scale = total_acad = 0
    for path in paths:
        if not path.is_file():
            print("Skip missing:", path, file=sys.stderr)
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        fs = fa = 0
        for b_id, _p_id, st in iter_stories(data):
            cons_root = st.get("consequences")
            if not isinstance(cons_root, dict):
                continue
            fs += scale_negative_energy(cons_root, args.factor, args.max_drain)
            if b_id == "academy":
                succ = cons_root.get("success")
                if isinstance(succ, dict):
                    ev = succ.get("energy", 0)
                    if ev == 0 or ev is None:
                        succ["energy"] = int(args.academy_success_energy)
                        fa += 1
        print(path, "scaled", fs, "academy", fa)
        total_scale += fs
        total_acad += fa
        if not args.dry_run:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("TOTAL", total_scale, total_acad)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

