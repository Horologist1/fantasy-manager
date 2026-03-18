#!/usr/bin/env python3
"""Migrate building_types: relevant_traits -> positive_traits (dict), negative_traits (dict), add trait_msg_success/failure."""
import json

with open("game/data/buildings/building_types.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for bt in data.get("building_types", []):
    for prof in bt.get("professions", []):
        for story in prof.get("daily_stories", []):
            # 1. Rename relevant_traits -> positive_traits (convert list to dict)
            if "relevant_traits" in story:
                rt = story.pop("relevant_traits")
                if isinstance(rt, list):
                    # prostitute_vanilla_client: variable weights
                    if story.get("id") == "prostitute_vanilla_client":
                        story["positive_traits"] = {"Beautiful": 6, "Graceful": 4, "Elegant": 4, "Sexy Air": 5}
                    else:
                        story["positive_traits"] = {t: 3 for t in rt}
                else:
                    story["positive_traits"] = rt

            # 2. Convert negative_traits list to dict
            if "negative_traits" in story:
                nt = story["negative_traits"]
                if isinstance(nt, list):
                    story["negative_traits"] = {t: 3 for t in nt} if nt else {}
                elif not isinstance(nt, dict):
                    story["negative_traits"] = {}
            elif "positive_traits" in story:
                story["negative_traits"] = {}

            # 3. Add trait_msg_success/failure if missing
            ts = story.get("trait_success", "")
            if "trait_msg_success" not in story and ts:
                story["trait_msg_success"] = ts
            if "trait_msg_failure" not in story and ts:
                story["trait_msg_failure"] = "{worker_name}'s {trait} didn't help this time."

            # 4. Remove old 6-key block
            for k in [
                "trait_msg_success_pos", "trait_msg_success_neg", "trait_msg_success_both",
                "trait_msg_failure_pos", "trait_msg_failure_neg", "trait_msg_failure_both",
            ]:
                story.pop(k, None)

with open("game/data/buildings/building_types.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Done: positive_traits (dict), negative_traits (dict), trait_msg_success/failure")
