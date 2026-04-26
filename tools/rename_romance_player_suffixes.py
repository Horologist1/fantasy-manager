#!/usr/bin/env python3
"""
Rename legacy romance player-suffix image names:
  romance_male*   -> romance_lord*
  romance_female* -> romance_lady*

Supports numbered variants like:
  romance_male (3).jpg -> romance_lord (3).jpg

By default this script runs in dry-run mode. Use --apply to perform renames.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


WORKERS_DIR = Path(__file__).resolve().parents[1] / "game" / "images" / "workers"
LEGACY_TO_NEW = {
    "romance_male": "romance_lord",
    "romance_female": "romance_lady",
}


def _map_name(name: str) -> str | None:
    lower = name.lower()
    for old, new in LEGACY_TO_NEW.items():
        if lower == old or lower.startswith(old + " ("):
            return new + name[len(old) :]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename legacy romance player suffix image names.")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Without this flag, only prints planned renames.")
    args = parser.parse_args()

    if not WORKERS_DIR.exists():
        print(f"Workers directory not found: {WORKERS_DIR}")
        return 1

    planned = []
    skipped_conflict = []

    for file_path in WORKERS_DIR.rglob("*"):
        if not file_path.is_file():
            continue
        stem = file_path.stem
        target_stem = _map_name(stem)
        if not target_stem:
            continue
        target = file_path.with_name(target_stem + file_path.suffix)
        if target.exists():
            skipped_conflict.append((file_path, target))
            continue
        planned.append((file_path, target))

    print(f"Planned renames: {len(planned)}")
    for src, dst in planned:
        print(f"- {src} -> {dst}")

    if skipped_conflict:
        print(f"\nSkipped due to existing target files: {len(skipped_conflict)}")
        for src, dst in skipped_conflict:
            print(f"- {src} (target exists: {dst})")

    if not args.apply:
        print("\nDry run only. Use --apply to perform renames.")
        return 0

    for src, dst in planned:
        os.rename(src, dst)

    print(f"\nApplied renames: {len(planned)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

