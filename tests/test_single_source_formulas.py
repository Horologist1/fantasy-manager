"""Every shared game number has exactly one definition; screens and rules call it.

Two copies of the same formula agree today and drift tomorrow (the reputation
ceiling did: stories used the level cap, events clamped to 1000). This guard
lists each shared quantity, where it is defined, and asserts that no other
file re-derives it from literals.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted((ROOT / "game/scripts").rglob("*.rpy"))

# (description, regex that matches a re-derivation, the one file allowed to contain it)
SINGLE_SOURCES = [
    ("building upgrade cost", re.compile(r"\*\*\s*2\s*\*\s*1000"), "game/scripts/script.rpy"),
    ("servant sale refund", re.compile(r'\)\s*\*\s*500\b'), "game/scripts/workers/worker_management.rpy"),
    ("skill bonus upkeep", re.compile(r"//\s*10\)\s*\*\s*100"), "game/scripts/events/event_daily_exec.rpy"),
    ("reputation hard clamp", re.compile(r"reputation[^\n]*min\([^\n]*\b1000\)"), None),
    ("building level literal ceiling", re.compile(r'base_level[^\n]*(?:min\(|>=)\s*5\b'), None),
    ("skill bonus literal ceiling", re.compile(r'skill_bonus[^\n]*(?:<|min\()\s*50\b'), None),
]

ALLOWED_LITERALS = {
    # Brand-new building record: an initial value, not a ceiling applied to play.
    ("game/scripts/script.rpy", "reputation hard clamp"): ['"reputation": min(reputation, 1000)'],
    # The cap function's own components.
    ("game/scripts/buildings/building_logic.rpy", "reputation hard clamp"): ["min(1000, building_level * 200)", "min(1000, manager_level * 200)"],
    ("game/scripts/core/screens.rpy", "reputation hard clamp"): ["min(1000, manager_level * 200)"],
    # The Governor's Castle is created at max level on purpose.
    ("game/scripts/tutorial_system.rpy", "building level literal ceiling"): ['["base_level"] = 5'],
}


def test_shared_formulas_have_one_definition():
    offenders = []
    for path in SCRIPTS:
        rel = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or "renpy.log" in stripped:
                continue
            for name, pattern, home in SINGLE_SOURCES:
                if not pattern.search(line):
                    continue
                if home and rel == home:
                    continue
                if any(token in line for token in ALLOWED_LITERALS.get((rel, name), [])):
                    continue
                offenders.append("%s:%d [%s] %s" % (rel, number, name, stripped[:100]))
    assert offenders == [], "\n".join(offenders)


def test_home_files_still_define_each_formula_once():
    for name, pattern, home in SINGLE_SOURCES:
        if not home:
            continue
        text = (ROOT / home).read_text(encoding="utf-8")
        assert len(pattern.findall(text)) == 1, (name, home)
