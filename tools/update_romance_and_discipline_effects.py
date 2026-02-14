import json
import os


ROOT = r"c:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager"
INTERACTIONS_PATH = os.path.join(ROOT, "game", "data", "interactions", "interactions_structured.json")


def main() -> None:
    with open(INTERACTIONS_PATH, "r", encoding="utf-8") as f:
        interactions = json.load(f)

    romance_removed_relationship = 0
    discipline_removed_joy_penalty = 0

    for it in interactions:
        cats = it.get("categories") or []
        lvl = int(it.get("interaction_level", 1) or 1)
        effect = it.get("effect") or {}
        if not isinstance(effect, dict):
            continue

        # Romance: must not grant relationship
        if "Romance" in cats:
            if "relationship" in effect:
                del effect["relationship"]
                romance_removed_relationship += 1
            it["effect"] = effect

        # Discipline (rebelliousness actions): remove Joy penalty from level 4 onwards
        if "Discipline" in cats and lvl >= 4:
            joy_val = effect.get("joy")
            if isinstance(joy_val, (int, float)) and joy_val < 0:
                del effect["joy"]
                discipline_removed_joy_penalty += 1
            it["effect"] = effect

    tmp = INTERACTIONS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(interactions, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, INTERACTIONS_PATH)

    print(
        "OK:",
        "romance_removed_relationship=" + str(romance_removed_relationship),
        "discipline_removed_joy_penalty_L4plus=" + str(discipline_removed_joy_penalty),
    )


if __name__ == "__main__":
    main()

