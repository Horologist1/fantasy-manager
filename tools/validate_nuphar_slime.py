"""Validates the Nuphar / Slime data additions. Run from repo root: python tools/validate_nuphar_slime.py
Exits 0 if all checks pass, 1 otherwise. Safe to run after each data task to watch checks turn green."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)

def find(items, name):
    return next((x for x in items if x.get("name") == name), None)

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)

# --- Slime race trait ---
races = load("game/data/traits/traits_races.json")
slime = find(races, "Slime")
check(slime is not None, "Slime trait missing from traits_races.json")
if slime:
    check(slime.get("reform_on_death") is True, "Slime.reform_on_death must be true")
    check(slime.get("skill_caps", {}).get("Clever") == 50, "Slime.skill_caps.Clever must be 50")
    check(slime.get("nsfw") is True, "Slime.nsfw must be true")
    for race in ("Human", "Elf", "Demon"):
        check(race in slime.get("conflicts", []), f"Slime should conflict with {race}")

# --- Reforming debuff trait ---
core = load("game/data/traits/traits_core.json")
reforming = find(core, "Reforming")
check(reforming is not None, "Reforming trait missing from traits_core.json")
if reforming:
    check(reforming.get("duration") == 3, "Reforming.duration must be 3")
    check(reforming.get("modifiers", {}).get("earnings_multiplier") == 0.5, "Reforming earnings_multiplier must be 0.5")
    sm = reforming.get("modifiers", {}).get("skill_modifiers", {})
    check(all(sm.get(s) == -20 for s in ("Sex", "Combat", "Charm", "Agility")), "Reforming should give -20 to skills")

# --- Nuphar (unique) ---
uniq = load("game/data/workers/workers_nsfw_unique.json")
nuphar = find(uniq, "Nuphar")
check(nuphar is not None, "Nuphar missing from workers_nsfw_unique.json")
if nuphar:
    check(nuphar.get("unique") is True, "Nuphar.unique must be true")
    check(nuphar.get("monster") is True, "Nuphar.monster must be true")
    check(nuphar.get("encounter_only") is True, "Nuphar.encounter_only must be true")
    check(nuphar.get("nsfw") is True, "Nuphar.nsfw must be true")
    check("names_list" not in nuphar, "Nuphar must NOT have names_list (keeps her name)")
    check(nuphar.get("folder") == "nuphar", "Nuphar.folder must be 'nuphar'")
    nuphar_traits = nuphar.get("traits", [])
    check(nuphar_traits[:1] == ["Slime"] and len(nuphar_traits) == 5,
          "Nuphar.traits must start with 'Slime' and total 5 (fully-defined character)")
    check(nuphar.get("skills", {}).get("Clever") == 16, "Nuphar.Clever must be 16 (lowest in game)")

# --- Generic Slime template ---
other = load("game/data/workers/workers_nsfw_other.json")
gslime = find(other, "Slime")
check(gslime is not None, "Generic Slime template missing from workers_nsfw_other.json")
if gslime:
    check(gslime.get("unique") is False, "Generic Slime.unique must be false")
    check(gslime.get("monster") is True, "Generic Slime.monster must be true")
    check(gslime.get("encounter_only") is True, "Generic Slime.encounter_only must be true")
    check(gslime.get("names_list") == "fantasy_female", "Generic Slime needs names_list 'fantasy_female'")
    check(gslime.get("folder") == "nuphar", "Generic Slime.folder must be 'nuphar' (reuse art)")
    check(gslime.get("traits") == ["Slime"], "Generic Slime.traits must be ['Slime']")
    # worse than Nuphar in every skill they share
    if nuphar:
        for k, v in gslime.get("skills", {}).items():
            nv = nuphar.get("skills", {}).get(k)
            if nv is not None:
                check(v < nv, f"Generic Slime.{k} ({v}) must be worse than Nuphar ({nv})")

if errors:
    print("FAIL:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("All Nuphar/Slime data checks passed.")
