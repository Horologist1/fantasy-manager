"""Patch special_buildings: Academy rest + Arena NSFW rest (idempotent)."""
import json
from pathlib import Path

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    p = root / "game" / "data" / "buildings" / "special_buildings.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    for bt in data.get("building_types", []) or []:
        if bt.get("id") == "academy":
            profs = bt.setdefault("professions", [])
            if not any(pr.get("id") == "rest" for pr in profs):
                profs.append({
                    "id": "rest",
                    "name": "Rest",
                    "description": "Student takes a day away from lectures and drills to sleep, eat, and recover. No classes today while strength returns.",
                    "nsfw": False,
                    "difficulty": "none",
                    "skills": [],
                    "training_skills_distribution": {},
                    "max_daily_workers": 99,
                    "daily_story_count": {"base": 1, "bonus_formula": "0"},
                    "daily_stories": [
                        {
                            "id": "rest_academy",
                            "weight": 1,
                            "description": "{worker_name} skips the formal routine for a recovery day—extra sleep, plain meals, and quiet corners of the campus. Tutors may mark an absence, but muscles and minds knit back together.",
                            "report": "Taking a Break",
                            "story_image": "rest_adventurer",
                            "consequences": {"success": {"energy": 3, "health": 3, "joy": 2}},
                            "nsfw_only": False,
                        },
                        {
                            "id": "rest_nsfw_relief_academy",
                            "weight": 1,
                            "report": "Private Relief",
                            "description": "{worker_name} finds a private moment away from scheduled drills and shared dorms—tension drains, breath evens, and tomorrow's ink looks a little less like a cage.",
                            "nsfw_only": True,
                            "stat_requirements": {"libido": 20},
                            "consequences": {"success": {"energy": 2, "health": 1, "joy": 1, "libido": -3}},
                            "story_image": "rest_libido",
                            "trait_roll_modifiers": {},
                        },
                    ],
                })
                print("Inserted Academy rest")
            else:
                print("Academy already has rest")
        if bt.get("id") == "arena":
            for pr in bt.get("professions", []) or []:
                if pr.get("id") != "rest":
                    continue
                stories = pr.setdefault("daily_stories", [])
                if not any(s.get("id") == "rest_nsfw_relief_arena" for s in stories):
                    stories.append({
                        "id": "rest_nsfw_relief_arena",
                        "weight": 1,
                        "report": "Private Relief",
                        "description": "{worker_name} slips away from the training yard crowd for private relief—muscles unclench, pulse settles, and the next bout feels one step farther from reckless.",
                        "nsfw_only": True,
                        "stat_requirements": {"libido": 20},
                        "consequences": {"success": {"energy": 2, "health": 1, "joy": 1, "libido": -3}},
                        "story_image": "rest_libido",
                        "trait_roll_modifiers": {},
                    })
                    print("Appended Arena NSFW rest")
                else:
                    print("Arena NSFW rest already present")
                break
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote", p)

if __name__ == "__main__":
    main()
