import json
import os
from typing import Any, Dict, List


ROOT = r"c:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager"
INTERACTIONS_PATH = os.path.join(ROOT, "game", "data", "interactions", "interactions_structured.json")


def _cooldown(duration: int) -> Dict[str, Any]:
    return {"discipline_cooldown": {"value": True, "duration": duration}}


def build_new_discipline() -> List[Dict[str, Any]]:
    # NOTE: gender_filter/worker_gender are None -> shared interactions for all combos
    # NSFW interactions will be auto-hidden when NSFW mode is off (loader behavior).
    return [
        {
            "id": "discipline_level1_etiquette",
            "name": "House Etiquette",
            "description": (
                "I do not raise my voice. I do not need to. I correct every detail—how they stand, where their eyes "
                "belong, how they speak, and when they are allowed to speak at all. I make them repeat the rules until "
                "the old habits disappear: a bowed head, a quiet \"Yes, my lord/lady,\" hands kept still, steps measured, "
                "and silence when silence is expected. Discipline in this house begins with control of the smallest "
                "things, because the smallest things are what betray disobedience."
            ),
            "interaction_level": 1,
            "cost_energy": 0,
            "cost_money": 0,
            "effect": {"rebelliousness": -2, "joy": -1, "flags": _cooldown(1)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_etiquette",
            "nsfw": False,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level1_private_inspection",
            "name": "Private Inspection",
            "description": (
                "I summon them when the corridors are empty and the doors are closed. There is no audience—only judgment. "
                "I make them hold a posture that is uncomfortable on purpose, and I correct it again and again until their "
                "body learns faster than their pride. I check cleanliness, compliance, and the simple truth of ownership: "
                "whether they can endure scrutiny without excuses. The intimacy here is cold and controlled—close enough "
                "that they feel my presence, strict enough that they feel it as law."
            ),
            "interaction_level": 1,
            "interaction_type": "discipline",
            "cost_energy": 0,
            "cost_money": 0,
            "effect": {"rebelliousness": -3, "joy": -1, "flags": _cooldown(1)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_inspection",
            "nsfw": True,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level2_corrective_discipline",
            "name": "Corrective Discipline",
            "description": (
                "When rules are ignored, I respond with certainty—not anger. I make the correction brief, efficient, and "
                "memorable: a punishment measured to the offence, carried out without spectacle. I explain the standard "
                "once. Then I enforce it. They learn that in this house, obedience is not a suggestion and discretion is "
                "not a privilege—it is the price of being kept."
            ),
            "interaction_level": 2,
            "cost_energy": 0,
            "cost_money": 10,
            "effect": {"rebelliousness": -5, "joy": -2, "relationship": -1, "flags": _cooldown(2)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_correction",
            "nsfw": False,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level2_private_punishment",
            "name": "Private Punishment",
            "description": (
                "I keep it private. I always do. I correct them close enough that they cannot hide behind bravado, and I "
                "make them accept the lesson without noise. There is a quiet intimacy in how controlled it is: my hand "
                "guiding their breathing, my voice low, my rules absolute. It is not romance. It is training—made personal "
                "so it leaves a mark in the mind as much as in the body."
            ),
            "interaction_level": 2,
            "interaction_type": "discipline",
            "cost_energy": 0,
            "cost_money": 10,
            "effect": {"rebelliousness": -6, "joy": -1, "relationship": -1, "flags": _cooldown(2)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_private_punishment",
            "nsfw": True,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level3_discretion_training",
            "name": "Discretion Training",
            "description": (
                "Obedience is not only doing what I say. It is knowing what must never be said. I teach them the house "
                "rules of discretion: how to stand behind me without drawing eyes, how to answer without revealing, how to "
                "keep secrets even under pressure. I drill the small signals—when to speak, when to withdraw, when to "
                "pretend not to hear. A servant who cannot be discreet is a liability. I do not keep liabilities for long."
            ),
            "interaction_level": 3,
            "cost_energy": 0,
            "cost_money": 12,
            "effect": {"rebelliousness": -4, "joy": -1, "flags": _cooldown(5)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_discretion",
            "nsfw": False,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level3_oral_discipline",
            "name": "Oral Discipline",
            "description": (
                "I make the lesson private, quiet, and unmistakably intimate. There is no performance here—no audience, no "
                "games—only obedience under my hand and my voice. I set the pace, the rules, and the boundaries. I watch "
                "the moment their pride gives way to compliance, and I do not stop until they understand what it means to "
                "serve without hesitation. The intimacy does not soften the discipline. It sharpens it."
            ),
            "interaction_level": 3,
            "interaction_type": "discipline",
            "cost_energy": 0,
            "cost_money": 12,
            "effect": {"rebelliousness": -7, "joy": -1, "relationship": -1, "flags": _cooldown(5)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_oral",
            "nsfw": True,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level4_submission_conditioning",
            "name": "Submission Conditioning",
            "description": (
                "At this stage, I stop correcting mistakes one by one. I correct the habit that produces them. I set "
                "routines that grind disobedience down: posture held until it is natural, commands followed until delay "
                "feels impossible, silence maintained until it is instinct. It is hard, and it is methodical. The point is "
                "not cruelty. The point is reliability."
            ),
            "interaction_level": 4,
            "cost_energy": 0,
            "cost_money": 10,
            "effect": {"rebelliousness": -8, "joy": -3, "relationship": -2, "flags": _cooldown(1)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_conditioning",
            "nsfw": False,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level4_bdsm_conditioning",
            "name": "BDSM Conditioning",
            "description": (
                "I make the training explicit and controlled. Every restraint, every command, every moment of discomfort "
                "is used to shape the same outcome: obedience without bargaining. There can be intimacy in how close it "
                "is—breath, skin, the quiet certainty of my hands—but the purpose never changes. When I say stop, it "
                "stops. When I say endure, they endure. This is not play. This is conditioning."
            ),
            "interaction_level": 4,
            "interaction_type": "discipline",
            "cost_energy": 0,
            "cost_money": 10,
            "effect": {"rebelliousness": -10, "joy": -2, "relationship": -2, "flags": _cooldown(1)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_bdsm",
            "nsfw": True,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_cooldown": True},
        },
        {
            "id": "discipline_level5_finale",
            "name": "Assign Their Place",
            "description": (
                "By now, their obedience is not an argument—it is a pattern. I bring them to a quiet room where words "
                "carry weight and decisions do not get repeated. I lay out the truth plainly: in this house, everyone "
                "ends up with a place. Some are kept for pleasure. Some are kept for service. And some are kept only as "
                "long as they are profitable. I watch their face as they understand what this moment means. Then I decide "
                "where they belong."
            ),
            "interaction_level": 5,
            "cost_energy": 0,
            "cost_money": 0,
            "effect": {"rebelliousness": -2, "joy": -1, "flags": _cooldown(1)},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_finale",
            "nsfw": False,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {"discipline_final_done": {"value": True, "duration": -1}},
        },
        {
            "id": "discipline_level5_sell_specialty_buyer",
            "name": "Sell to a Specialty Buyer",
            "description": (
                "This is not a threat. It is a transaction. I consider what they cost me, what they have become, and what "
                "the market will pay for a servant trained to obey. A specialty buyer does not care about excuses or "
                "feelings—only quality. If I proceed, the sale is final."
            ),
            "interaction_level": 5,
            "cost_energy": 0,
            "cost_money": 0,
            "effect": {},
            "gender_filter": None,
            "worker_gender": None,
            "categories": ["Discipline"],
            "image": "discipline_sell",
            "nsfw": False,
            "stat_requirements": {},
            "required_flags": {},
            "excluded_flags": {},
        },
    ]


def main() -> None:
    with open(INTERACTIONS_PATH, "r", encoding="utf-8") as f:
        interactions = json.load(f)

    rest = [it for it in interactions if "Discipline" not in (it.get("categories") or [])]
    new_discipline = build_new_discipline()

    out = new_discipline + rest

    ids = [it.get("id") for it in out]
    dups = sorted({i for i in ids if i and ids.count(i) > 1})
    if dups:
        raise SystemExit("Duplicate interaction ids: " + ", ".join(dups[:20]))

    tmp = INTERACTIONS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, INTERACTIONS_PATH)

    print(f"OK: wrote {len(new_discipline)} Discipline interactions; total now {len(out)}")


if __name__ == "__main__":
    main()

