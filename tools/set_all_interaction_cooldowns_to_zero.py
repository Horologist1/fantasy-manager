import json
import os


ROOT = r"c:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager"
INTERACTIONS_PATH = os.path.join(ROOT, "game", "data", "interactions", "interactions_structured.json")


def main() -> None:
    with open(INTERACTIONS_PATH, "r", encoding="utf-8") as f:
        interactions = json.load(f)

    changed = 0
    for it in interactions:
        effect = it.get("effect") or {}
        flags = effect.get("flags") or {}
        if not isinstance(flags, dict):
            continue

        for flag_name, flag_value in list(flags.items()):
            if not isinstance(flag_name, str):
                continue
            if not flag_name.endswith("_cooldown"):
                continue
            if not isinstance(flag_value, dict):
                continue
            if "duration" in flag_value and flag_value.get("duration") != 0:
                flag_value["duration"] = 0
                changed += 1

    tmp = INTERACTIONS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(interactions, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, INTERACTIONS_PATH)

    print(f"OK: set duration=0 for {changed} *_cooldown flags")


if __name__ == "__main__":
    main()

