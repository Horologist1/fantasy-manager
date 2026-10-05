#!/usr/bin/env python3
"""Android pre-release checks for Fantasy Manager.

Run this BEFORE packaging an Android build:

    python android_preflight.py

It statically verifies every "[prefix_]" image pattern in game/**/*.rpy
(button backgrounds, bar/slider parts, check/radio foregrounds) against
Ren'Py's real prefix fallback chains, using EXACT-case file matching.
Windows' case-insensitive filesystem and the empty desktop quick_menu
screen both hide this class of bug on PC; on Android it crashes with:

    Exception: DynamicImage 'gui/button/...[prefix_]...': could not find image.

This caught the v0.9.5.6 crash: "quick_[prefix_]_background.png" (stray
underscore after the bracket -> expanded to quick_idle__background.png).

Static check limitation: names defined via `image` statements are not
considered, only real files under game/. All current [prefix_] patterns
point at gui/ files, so that is fine.

Final gate before packaging is a live touch-variant smoke test on PC:

    $env:RENPY_VARIANT = "touch small mobile android"
    & "D:\renpy-8.3.4-sdk\renpy.exe" . --warp scripts/main_flow.rpy:515

then play a few interactions (quick menu, a choice menu, prefs screen)
and confirm no exception screen / no fresh traceback.txt.
"""

import os
import re
import sys

# Extracted from renpy.styledata.stylesets.prefix_search (Ren'Py 8.3.x).
# For each displayable state, [prefix_] is substituted with each value in
# order; the first candidate that exists as a loadable file is used. If
# none exists, the game raises at runtime.
PREFIX_SEARCH = {
    "insensitive_": ["insensitive_", "", "idle_"],
    "idle_": ["idle_", ""],
    "hover_": ["hover_", ""],
    "selected_insensitive_": [
        "selected_insensitive_", "insensitive_", "selected_", "",
        "selected_idle_", "idle_",
    ],
    "selected_idle_": ["selected_idle_", "selected_", "", "idle_"],
    "selected_hover_": ["selected_hover_", "hover_", "selected_", ""],
}

PATTERN_RE = re.compile(r'"([^"]*\[prefix_\][^"]*)"')


def game_file_set(game_dir):
    """All files under game/, as forward-slash relative paths, exact case."""
    files = set()
    for root, _dirs, names in os.walk(game_dir):
        rel_root = os.path.relpath(root, game_dir)
        for name in names:
            rel = name if rel_root == "." else rel_root + "/" + name
            files.add(rel.replace("\\", "/"))
    return files


def find_prefix_patterns(game_dir):
    """Yield (rpy_relpath, line_no, pattern) for every [prefix_] string."""
    for root, _dirs, names in os.walk(game_dir):
        for name in names:
            if not name.endswith(".rpy"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, game_dir).replace("\\", "/")
            with open(path, encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    for match in PATTERN_RE.finditer(line):
                        yield rel, line_no, match.group(1)


def check_pattern(pattern, files):
    """Return list of (state, candidates) that cannot resolve to a file."""
    failures = []
    for state, chain in PREFIX_SEARCH.items():
        candidates = [pattern.replace("[prefix_]", p) for p in chain]
        # Anything still containing [ has another substitution we cannot
        # expand statically; skip rather than report a false failure.
        if any("[" in c for c in candidates):
            return []
        if not any(c in files for c in candidates):
            failures.append((state, candidates))
    return failures


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    game_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, "game")
    if not os.path.isdir(game_dir):
        print(f"ERROR: game directory not found: {game_dir}")
        return 2

    files = game_file_set(game_dir)
    checked = 0
    bad = 0
    for rel, line_no, pattern in find_prefix_patterns(game_dir):
        checked += 1
        for state, candidates in check_pattern(pattern, files):
            bad += 1
            print(f"FAIL {rel}:{line_no}")
            print(f"     pattern:  {pattern}")
            print(f"     state:    {state}  (no candidate file exists)")
            print(f"     tried:    {', '.join(c or '(empty)' for c in candidates)}")

    print(f"\nChecked {checked} [prefix_] pattern occurrences.")
    if bad:
        print(f"RESULT: FAIL - {bad} unresolvable state(s). "
              "This WILL crash on Android (case-sensitive, touch variant).")
        return 1
    print("RESULT: PASS - every state of every pattern resolves to a real file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
