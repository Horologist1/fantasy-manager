#!/usr/bin/env python3
"""
Rebalance daily story earnings in game/data/buildings/building_types.json.

Standard tier:
  mediocre: skill
  success: 50 + skill
  critical_success: 50 + skill * 2
  failure: -roll

Premium tier (higher-paying jobs in legacy data):
  mediocre: skill
  success: 50 + skill * 2
  critical_success: 50 + skill * 3
  failure: -roll

Skips stories whose failure formula does not reference `roll` (fixed cash / atypical).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "game" / "data" / "buildings" / "building_types.json"

REQUIRED_KEYS = ("failure", "mediocre", "success", "critical_success")

STANDARD = {
    "mediocre": "skill",
    "success": "50 + skill",
    "critical_success": "50 + skill * 2",
    "failure": "-(roll - skill)",
}

PREMIUM = {
    "mediocre": "skill",
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3",
    "failure": "-(roll - skill)",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").lower())


def is_rebalanceable(earnings: dict[str, Any]) -> bool:
    if not isinstance(earnings, dict):
        return False
    for k in REQUIRED_KEYS:
        v = earnings.get(k)
        if not isinstance(v, str) or not v.strip():
            return False
    failure = earnings["failure"]
    if "roll" not in failure.lower():
        return False
    return True


def classify_premium_legacy(earnings: dict[str, str]) -> bool:
    """Heuristic from pre-rebalance formulas (bases and skill multipliers)."""
    s = _norm(earnings.get("success", ""))
    c = _norm(earnings.get("critical_success", ""))
    m = _norm(earnings.get("mediocre", ""))

    # Critical skill multiplier >= 5 (legacy *5, *6, *8, ...)
    if re.search(r"skill\*([5-9]|\d{2,})", c):
        return True

    # Success uses skill * 3 or higher
    if re.search(r"skill\*([3-9]|\d{2,})", s):
        return True

    # Large success base (VIP / elite lines)
    mo = re.match(r"^(\d+)\+", s)
    if mo and int(mo.group(1)) >= 280:
        return True

    # Mediocre tier clearly above standard 100+skill
    if m.startswith("150+") or m.startswith("200+"):
        return True

    return False


def resolve_tier(earnings: dict[str, str]) -> str:
    """
    Return 'standard' or 'premium'. Exact match to post-rebalance formulas wins
    so the script stays idempotent (legacy heuristics alone mis-read new crit *3).
    """
    if all(isinstance(earnings.get(k), str) and earnings.get(k) == STANDARD[k] for k in REQUIRED_KEYS):
        return "standard"
    if all(isinstance(earnings.get(k), str) and earnings.get(k) == PREMIUM[k] for k in REQUIRED_KEYS):
        return "premium"
    return "premium" if classify_premium_legacy(earnings) else "standard"


def iter_stories(data: dict[str, Any]):
    for bt in data.get("building_types", []) or []:
        b_id = bt.get("id", "")
        for pr in bt.get("professions", []) or []:
            p_id = pr.get("id", "")
            for st in pr.get("daily_stories", []) or []:
                yield b_id, p_id, st


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_PATH,
        help="Path to building_types.json",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report only; do not write file",
    )
    args = ap.parse_args()
    path: Path = args.file

    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)

    skipped: list[tuple[str, str, str, dict]] = []
    changed: list[tuple[str, str, str, str, dict, dict]] = []

    for b_id, p_id, st in iter_stories(data):
        e = st.get("earnings")
        if not isinstance(e, dict):
            continue
        sid = str(st.get("id", ""))
        if not is_rebalanceable(e):
            skipped.append((b_id, p_id, sid, dict(e)))
            continue
        tier = resolve_tier(e)
        target = PREMIUM if tier == "premium" else STANDARD
        before = {k: e.get(k) for k in REQUIRED_KEYS}
        if all(isinstance(e.get(k), str) and e[k] == target[k] for k in REQUIRED_KEYS):
            continue
        for k in REQUIRED_KEYS:
            e[k] = target[k]
        changed.append((b_id, p_id, sid, tier, before, dict(target)))

    print(f"File: {path}")
    print(f"Stories skipped (no roll in failure or missing keys): {len(skipped)}")
    for b_id, p_id, sid, ed in skipped:
        print(f"  SKIP  {b_id}/{p_id}/{sid}  earnings={ed}")
    print(f"Stories updated: {len(changed)}")
    for b_id, p_id, sid, tier, before, after in changed:
        print(f"  {tier.upper():8} {b_id}/{p_id}/{sid}")
        for k in REQUIRED_KEYS:
            if before.get(k) != after.get(k):
                print(f"    {k}: {before.get(k)!r} -> {after.get(k)!r}")

    if args.dry_run:
        print("\nDry run: no file written.")
        return 0

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"\nWrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
