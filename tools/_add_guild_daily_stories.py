# One-off / reusable: append Adventurer's Guild daily stories (Clever, Agility, Craft facets).
import json
from copy import deepcopy

path = "game/data/buildings/building_types.json"


def main():
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    def prof(guild, pid):
        for p in guild["professions"]:
            if p["id"] == pid:
                return p
        raise KeyError(pid)

    guild = next(b for b in data["building_types"] if b["id"] == "adventurers_guild")

    loot_small = {
        "bonus_items": [
            {"item_id": "amulet_wanderer", "chance": 0.01, "nsfw": False},
            {"item_id": "collar_endless_desire", "chance": 0.01, "nsfw": True},
        ]
    }

    p_adv = prof(guild, "adventurer")
    p_adv["skills"] = ["Combat", "Agility", "Clever", "Craft"]

    adventurer_stories = [
        {
            "id": "adventurer_guild_monster_study",
            "weight": 0.05,
            "report": "Guild brief: monster lore",
            "skill_options": ["Clever"],
            "trait_success": "{worker_name}'s careful {trait} shows in every page of notes.",
            "earnings": {
                "success": "200 + skill * 2",
                "critical_success": "200 + skill * 4",
                "mediocre": "100 + skill",
                "failure": "-(100 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} spends hours chasing rumors and bad ledgers. The notes contradict each other, key details stay missing, and the guild clerk sends the stack back with a tired sigh. Little of it will help anyone in the field.",
                "mediocre": "{worker_name} pulls together a workable sketch of the creature: habits, a few sightings, and one solid warning. It is not brilliant work, but it is honest, and it fills gaps the job board did not mention.",
                "success": "{worker_name} builds a clear brief from bestiaries, witness accounts, and recent contracts. Tracks, feeding patterns, and local names line up into something a party can actually use without guessing in the dark.",
                "critical_success": "{worker_name} turns scattered gossip into a dossier the guild quietly copies. Rare behaviors, likely lairs, and market prices for parts are laid out so cleanly that even veterans pause to read it twice.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": -1, "reputation": -3},
                "success": {"energy": -1, "joy": 1, "reputation": 4},
                "critical_success": {"energy": -1, "joy": 2, "reputation": 8},
            },
            "loot": deepcopy(loot_small),
            "nsfw_only": False,
            "positive_traits": {"Determined": 3, "Mystical": 3},
            "trait_msg_success": "{worker_name}'s careful {trait} shows in every page of notes.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help the archive shift today.",
            "negative_traits": {},
        },
        {
            "id": "adventurer_exploration_legwork",
            "weight": 0.05,
            "report": "Exploration legwork",
            "skill_options": ["Agility"],
            "trait_success": "{worker_name}'s {trait} keeps the pace sharp and the route honest.",
            "earnings": {
                "success": "200 + skill * 2",
                "critical_success": "200 + skill * 4",
                "mediocre": "100 + skill",
                "failure": "-(100 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} pushes too hard over broken ground and bad weather. Maps smear, landmarks blur, and the day ends with sore legs, no reliable markers, and a quiet understanding that the route is still unknown.",
                "mediocre": "{worker_name} covers the ground and comes back winded but upright. A few paths are ruled out, a couple of hazards are marked, and the guild gets enough to plan around—nothing flashy, nothing wasted.",
                "success": "{worker_name} runs the approach routes fast enough to matter and careful enough to count. Choke points, escape lines, and timing windows are noted in plain language, ready for whoever signs the next contract.",
                "critical_success": "{worker_name} returns with routes measured like a scout's boast: clean splits, clever shortcuts, and a sense of where speed actually wins treasure instead of trouble. The guild pins the notes where everyone can see them.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -2, "health": -2, "joy": -1, "reputation": -3},
                "success": {"energy": -1, "joy": 1, "reputation": 4},
                "critical_success": {"energy": -1, "joy": 2, "reputation": 8},
            },
            "loot": deepcopy(loot_small),
            "nsfw_only": False,
            "positive_traits": {"Agile": 3, "Determined": 3, "Robust": 3},
            "trait_msg_success": "{worker_name}'s {trait} keeps the pace sharp and the route honest.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help on the trail today.",
            "negative_traits": {},
        },
        {
            "id": "adventurer_expedition_kit_prep",
            "weight": 0.05,
            "report": "Expedition kit upkeep",
            "skill_options": ["Craft"],
            "trait_success": "{worker_name}'s {trait} shows in every strap, edge, and seal.",
            "earnings": {
                "success": "200 + skill * 2",
                "critical_success": "200 + skill * 4",
                "mediocre": "100 + skill",
                "failure": "-(100 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} misjudges oils, tension, or fittings. Something important is still loose when the bench clears, and the mistake will be obvious the moment the gear actually matters.",
                "mediocre": "{worker_name} gets the kit back to serviceable. Nothing gleams, nothing sings, but straps hold, edges bite, and the pack closes without a fight.",
                "success": "{worker_name} tunes the loadout like a craftsperson who has seen bad weather win once. Weapons seat clean, seams hold, spare parts sit where hands expect them, and the whole rack looks ready for a hard week.",
                "critical_success": "{worker_name} leaves the guild's rack looking unfairly good: balanced weight, smart repairs, and small fixes other adventurers quietly copy. Even picky quartermasters stop to nod.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": -1, "reputation": -3},
                "success": {"energy": -1, "joy": 1, "reputation": 4},
                "critical_success": {"energy": -1, "joy": 2, "reputation": 8},
            },
            "loot": deepcopy(loot_small),
            "nsfw_only": False,
            "positive_traits": {"Determined": 3, "Robust": 3, "Mystical": 2},
            "trait_msg_success": "{worker_name}'s {trait} shows in every strap, edge, and seal.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help at the workbench today.",
            "negative_traits": {},
        },
    ]

    p_th = prof(guild, "treasure_hunter")
    p_th["skills"] = ["Combat", "Agility", "Clever", "Craft"]

    th_stories = [
        {
            "id": "treasure_hunter_site_reading",
            "weight": 0.05,
            "report": "Site reading and maps",
            "skill_options": ["Clever"],
            "trait_success": "{worker_name}'s {trait} turns scraps of lore into a plan.",
            "earnings": {
                "success": "200 + skill * 2",
                "critical_success": "200 + skill * 4",
                "mediocre": "100 + skill",
                "failure": "-(100 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} chases dead symbols and copied mistakes. The notes look impressive until someone compares them to the real site, and the mismatch costs time nobody gets back.",
                "mediocre": "{worker_name} lines up a few credible clues: an old survey, a plausible entrance theory, and a list of what not to touch. It is enough to start, not enough to brag about.",
                "success": "{worker_name} reads the ruin like a language—layout, risks, and payoff line up. The guild files it as a brief that saves someone else a stupid first hour underground.",
                "critical_success": "{worker_name} spots the tell that everyone else walked past. Hidden seams, forgotten side texts, and a clean read on the builders' habits turn a messy ruin into a route with names.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": -1, "reputation": -3},
                "success": {"energy": -1, "joy": 1, "reputation": 4},
                "critical_success": {"energy": -1, "joy": 2, "reputation": 8},
            },
            "loot": {"rolls": 1, "bonus_items": deepcopy(loot_small["bonus_items"])},
            "nsfw_only": False,
            "positive_traits": {"Determined": 3, "Mystical": 3, "Optimist": 3},
            "trait_msg_success": "{worker_name}'s {trait} turns scraps of lore into a plan.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help the reading today.",
            "negative_traits": {},
        },
        {
            "id": "treasure_hunter_trap_kit_tuneup",
            "weight": 0.05,
            "report": "Tomb kit tune-up",
            "skill_options": ["Craft"],
            "trait_success": "{worker_name}'s {trait} shows in tools that actually fit the job.",
            "earnings": {
                "success": "200 + skill * 2",
                "critical_success": "200 + skill * 4",
                "mediocre": "100 + skill",
                "failure": "-(100 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} leaves a pry bar wrong, a line frayed, or a lamp badly seated. The mistake is small on a bench and huge in a dark corridor.",
                "mediocre": "{worker_name} replaces what was worn and oils what was sticking. The kit returns to baseline—no miracles, no surprises.",
                "success": "{worker_name} sets up a trap-kit that feels unfairly calm: picks seat true, cordage runs clean, and backups sit where panic will not have to search.",
                "critical_success": "{worker_name} builds a setup other hunters borrow without asking. Every piece has a reason, every repair has a story, and the whole pack looks ready for stone that bites back.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": -1, "reputation": -3},
                "success": {"energy": -1, "joy": 1, "reputation": 4},
                "critical_success": {"energy": -1, "joy": 2, "reputation": 8},
            },
            "loot": {"rolls": 1, "bonus_items": deepcopy(loot_small["bonus_items"])},
            "nsfw_only": False,
            "positive_traits": {"Determined": 3, "Optimist": 3},
            "trait_msg_success": "{worker_name}'s {trait} shows in tools that actually fit the job.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help at the bench today.",
            "negative_traits": {},
        },
        {
            "id": "treasure_hunter_pressure_run",
            "weight": 0.05,
            "report": "Timed site sweep",
            "skill_options": ["Agility"],
            "trait_success": "{worker_name}'s {trait} turns a narrow window into real ground gained.",
            "earnings": {
                "success": "200 + skill * 2",
                "critical_success": "200 + skill * 4",
                "mediocre": "100 + skill",
                "failure": "-(100 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} mistimes the approach. Doors shift, light changes, and the chance slips away with nothing secured but scrapes and a hard lesson about patience.",
                "mediocre": "{worker_name} gets in, grabs what the window allows, and gets out before the worst of it closes. The haul is modest, the body is still in one piece, and the map has a few new honest marks.",
                "success": "{worker_name} runs the sweep like the clock is an enemy worth respecting. The best chamber yields before the window shuts, and the exit feels practiced, not lucky.",
                "critical_success": "{worker_name} makes a pressured route look like choreography—clean entries, clean exits, and a haul that earns a whistle from the guild counter. Speed did the work; care kept it from becoming a story about bones.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -2, "joy": -1, "reputation": -3},
                "success": {"energy": -1, "joy": 1, "reputation": 4},
                "critical_success": {"energy": -1, "joy": 2, "reputation": 8},
            },
            "loot": {"rolls": 1, "bonus_items": deepcopy(loot_small["bonus_items"])},
            "nsfw_only": False,
            "positive_traits": {"Agile": 3, "Determined": 3, "Optimist": 3},
            "trait_msg_success": "{worker_name}'s {trait} turns a narrow window into real ground gained.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help on the run today.",
            "negative_traits": {},
        },
    ]

    p_boss = prof(guild, "boss_hunting")
    p_boss["skills"] = ["Combat", "Clever", "Agility", "Craft"]

    boss_stories = [
        {
            "id": "boss_hunting_mythic_research",
            "weight": 0.05,
            "report": "Mythic target research",
            "skill_options": ["Clever"],
            "trait_success": "{worker_name}'s {trait} shows in how calmly the myth is taken apart.",
            "earnings": {
                "success": "280 + skill * 3",
                "critical_success": "280 + skill * 6",
                "mediocre": "140 + skill * 2",
                "failure": "-(120 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} drowns in contradictory tales. The beast grows with every telling until the notes read like fiction, and the guild shelves the file with a warning nobody needed.",
                "mediocre": "{worker_name} separates a few hard facts from theater: range, appetite, and one credible weakness rumor. It is thin, but it is not theater.",
                "success": "{worker_name} builds a serious read on something that should not exist on paper—behaviors, known kills, and the kind of mistake that gets rookies killed if nobody writes it down.",
                "critical_success": "{worker_name} turns myth into something almost rude in its clarity: patterns, pressure points, and a timeline that makes veterans go quiet. The guild treats the pages like they cost blood.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": -1, "reputation": -4},
                "success": {"energy": -1, "joy": 2, "reputation": 8},
                "critical_success": {"energy": -1, "joy": 3, "reputation": 14},
            },
            "loot": {
                "rolls": 1,
                "bonus_items": [
                    {"item_id": "amulet_wanderer", "chance": 0.02, "nsfw": False},
                    {"item_id": "collar_endless_desire", "chance": 0.02, "nsfw": True},
                ],
            },
            "nsfw_only": False,
            "positive_traits": {"Determined": 3, "Mystical": 3, "Robust": 3, "Audacity": 2},
            "trait_msg_success": "{worker_name}'s {trait} shows in how calmly the myth is taken apart.",
            "trait_msg_failure": "{worker_name}'s {trait} did not sharpen the research today.",
            "negative_traits": {},
        },
        {
            "id": "boss_hunting_ritual_prep",
            "weight": 0.05,
            "report": "Boss-hunt gear preparation",
            "skill_options": ["Craft"],
            "trait_success": "{worker_name}'s {trait} shows in gear built for something too big for stories.",
            "earnings": {
                "success": "280 + skill * 3",
                "critical_success": "280 + skill * 6",
                "mediocre": "140 + skill * 2",
                "failure": "-(120 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} pushes metal and leather past honest limits. A seam fails on the bench, a proof-test snaps, and the rack goes back with apologies instead of confidence.",
                "mediocre": "{worker_name} brings the kit back to baseline: sharp enough, tough enough, honest enough. It will not win songs, but it will not betray the first swing.",
                "success": "{worker_name} prepares for weight and heat that do not forgive shortcuts. Anchors bite, bindings hold, and every piece has a reason that reads like respect, not hope.",
                "critical_success": "{worker_name} leaves a setup that makes quiet people stare. The work looks almost offensive in its care—like someone expected the legend to answer in person.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": -1, "reputation": -4},
                "success": {"energy": -2, "joy": 2, "reputation": 8},
                "critical_success": {"energy": -1, "joy": 3, "reputation": 14},
            },
            "loot": {
                "rolls": 1,
                "bonus_items": [
                    {"item_id": "amulet_wanderer", "chance": 0.02, "nsfw": False},
                    {"item_id": "collar_endless_desire", "chance": 0.02, "nsfw": True},
                ],
            },
            "nsfw_only": False,
            "positive_traits": {"Robust": 3, "Determined": 3, "Mystical": 3, "Audacity": 2},
            "trait_msg_success": "{worker_name}'s {trait} shows in gear built for something too big for stories.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help the forge bench today.",
            "negative_traits": {},
        },
        {
            "id": "boss_hunting_approach_recon",
            "weight": 0.05,
            "report": "Approach reconnaissance",
            "skill_options": ["Agility"],
            "trait_success": "{worker_name}'s {trait} keeps the approach honest and the exit real.",
            "earnings": {
                "success": "280 + skill * 3",
                "critical_success": "280 + skill * 6",
                "mediocre": "140 + skill * 2",
                "failure": "-(120 + roll)",
            },
            "descriptions": {
                "failure": "{worker_name} misreads the ground and pays for it in scrapes, lost time, and a route that ends where pride hoped it would not. The notes are more warning than help.",
                "mediocre": "{worker_name} maps the approach well enough to stop stupid mistakes. Peaks, washes, and blind corners are marked in plain ink—useful, unromantic, done.",
                "success": "{worker_name} returns with lines that respect gravity and weather. The approach reads like someone planned to run it twice—once to learn, once to survive.",
                "critical_success": "{worker_name} charts a path that feels unfairly clean: cover, timing, and retreat slots where panic will not have to invent them. Even cynics bookmark the page.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -2, "health": -4, "joy": -1, "reputation": -4},
                "success": {"energy": -1, "joy": 2, "reputation": 8},
                "critical_success": {"energy": -1, "joy": 3, "reputation": 14},
            },
            "loot": {
                "rolls": 1,
                "bonus_items": [
                    {"item_id": "amulet_wanderer", "chance": 0.02, "nsfw": False},
                    {"item_id": "collar_endless_desire", "chance": 0.02, "nsfw": True},
                ],
            },
            "nsfw_only": False,
            "positive_traits": {"Agile": 3, "Determined": 3, "Robust": 3, "Audacity": 3},
            "trait_msg_success": "{worker_name}'s {trait} keeps the approach honest and the exit real.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help the recon today.",
            "negative_traits": {},
        },
    ]

    p_mt = prof(guild, "monster_taming")
    p_mt["skills"] = ["Combat", "Extreme", "Clever", "Craft"]

    mt_stories = [
        {
            "id": "monster_taming_market_and_ethology",
            "weight": 0.05,
            "report": "Capture briefing: species and demand",
            "skill_options": ["Clever"],
            "trait_success": "{worker_name}'s {trait} shows in notes that buyers and beasts both respect.",
            "earnings": {
                "success": "10",
                "critical_success": "skill",
                "mediocre": "5",
                "failure": "-5",
            },
            "descriptions": {
                "failure": "{worker_name} chases rumors about rarity and price until the page reads like a tavern bet. The guild files it as a cautionary example instead of a plan.",
                "mediocre": "{worker_name} lines up what is legal enough, possible enough, and worth enough. It is not glamorous, but it stops someone from wasting a week on the wrong quarry.",
                "success": "{worker_name} maps habits, triggers, and the market's current appetite with cold patience. Handlers read it twice before they sign anything.",
                "critical_success": "{worker_name} turns messy intelligence into a brief that feels almost unfair: the right creature, the right bait logic, and the right buyer—without pretending any of it is tame.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": 0, "reputation": -1},
                "success": {"energy": -1, "joy": 0, "reputation": 1},
                "critical_success": {"energy": -1, "joy": 1, "reputation": 2},
            },
            "loot": {"rolls": 0, "bonus_items": []},
            "nsfw_only": False,
            "positive_traits": {"Determined": 3, "Audacity": 3, "Charming": 2},
            "trait_msg_success": "{worker_name}'s {trait} shows in notes that buyers and beasts both respect.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help the briefing today.",
            "negative_traits": {},
        },
        {
            "id": "monster_taming_capture_rig_prep",
            "weight": 0.05,
            "report": "Capture rig preparation",
            "skill_options": ["Craft"],
            "trait_success": "{worker_name}'s {trait} shows in knots, gates, and doses measured twice.",
            "earnings": {
                "success": "10",
                "critical_success": "skill",
                "mediocre": "5",
                "failure": "-5",
            },
            "descriptions": {
                "failure": "{worker_name} leaves a latch stiff, a line uneven, or a dose sloppy. The rig looks ready until stress proves it is not, and the guild sends it back to the bench.",
                "mediocre": "{worker_name} brings the rig back to honest function. Nothing sings, nothing snaps, and the next attempt starts without a stupid handicap.",
                "success": "{worker_name} builds capture gear that respects teeth, claws, and panic. Everything releases clean, everything tightens on purpose, and the work reads like patience with tools.",
                "critical_success": "{worker_name} assembles a setup other tamers copy without shame: clever tension, redundant safety, and small touches that keep blood off the contract line.",
            },
            "story_image": None,
            "consequences": {
                "failure": {"energy": -1, "joy": 0, "reputation": -1},
                "success": {"energy": -1, "joy": 0, "reputation": 1},
                "critical_success": {"energy": -1, "joy": 1, "reputation": 2},
            },
            "loot": {"rolls": 0, "bonus_items": []},
            "nsfw_only": False,
            "positive_traits": {"Determined": 3, "Robust": 3, "Audacity": 3},
            "trait_msg_success": "{worker_name}'s {trait} shows in knots, gates, and doses measured twice.",
            "trait_msg_failure": "{worker_name}'s {trait} did not help the rig work today.",
            "negative_traits": {},
        },
    ]

    def append_new(stories_list, new_items):
        existing = {s["id"] for s in stories_list}
        added = []
        for s in new_items:
            if s["id"] not in existing:
                stories_list.append(s)
                existing.add(s["id"])
                added.append(s["id"])
        return added

    a = append_new(p_adv["daily_stories"], adventurer_stories)
    b = append_new(p_th["daily_stories"], th_stories)
    c = append_new(p_boss["daily_stories"], boss_stories)
    d = append_new(p_mt["daily_stories"], mt_stories)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("adventurer:", a)
    print("treasure_hunter:", b)
    print("boss_hunting:", c)
    print("monster_taming:", d)


if __name__ == "__main__":
    main()
