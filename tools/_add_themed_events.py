"""One-shot: add 10 high-quality themed events to events_building.json."""
import json, os

path = os.path.join(os.path.dirname(__file__), "..", "game", "data", "events", "events_building.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

EVT = {
    "event_music": None, "event_type": None, "worker_name": None, "dialogue": None,
    "unlimited": False, "limited": False, "random_worker": False, "always_available": False,
    "worker_filter": {}, "player_gender_requirement": None
}
SC0 = {"success_chance": 0, "recruit_worker": False, "cost_modifier": 0, "relationship_bonus": 0}

def evt(base):
    e = dict(base)
    for k, v in EVT.items():
        e.setdefault(k, v)
    return e

new = [
    # ===== BROTHEL =====
    evt({
        "id": "brothel_body_oil_session",
        "description": "A repeat client sends word ahead: tonight he wants the full oil treatment\u2014warm pressed almond from neck to ankle, slow hands, low light, and a worker who knows how to make skin talk louder than words. He\u2019s paying triple the standard rate and expects his body handled like scripture. The kind of booking that builds a reputation\u2014if the hands doing the work are good enough.",
        "weight": 2, "cooldown_days": 10, "worker_selection": "player",
        "building_type": ["brothel"], "nsfw": True,
        "background_image": "brothel_oil", "success_image": "brothel_success", "failure_image": "brothel_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Assign a worker with skilled hands. (Requires Hand; Potential: Money, Reputation)",
                "condition": "Hand", "skill_check": 45,
                "message_success": "[acting_worker] warms the oil between both palms and starts at the shoulders\u2014long strokes that follow the grain of the muscle, thumbs pressing into the knots along the spine. The client\u2019s breathing slows within minutes. By the time hands reach the inner thighs, every touch reads deliberate: pressure where tension lives, featherweight where skin is thin. The client leaves loose-limbed, flushed, and already asking when he can book again.",
                "message_failure": "[acting_worker] starts well but loses the rhythm halfway through. Oil pools in the wrong places, pressure turns clumsy on the ribs, and the transition from back to thighs is abrupt enough that the client tenses instead of melting. He pays the base rate, says nothing, and doesn\u2019t rebook.",
                "effect": {"success": {"money": 800, "reputation": 8, "joy": 3}, "failure": {"money": 150, "reputation": -3, "joy": -2}, **SC0}
            },
            {
                "option": "Decline. The booking is too demanding for tonight\u2019s roster.",
                "message": "You send polite regrets. The client takes his coin and his expectations elsewhere. No loss, no gain\u2014but someone else\u2019s house earns the story tonight.",
                "effect": {"reputation": -2, **SC0, "joy": 0}
            }
        ]
    }),
    evt({
        "id": "brothel_couples_fantasy_night",
        "description": "A married couple arrives after midnight, nervous and electric. They\u2019ve saved for months. What they want is specific: a threesome with one of your workers\u2014someone who can read the room, move between two bodies without making either feel like a spectator, and keep the night about pleasure instead of awkwardness. They\u2019ve never done this before. The booking fee is generous, the pressure is real, and the wrong worker will turn fantasy into regret.",
        "weight": 1.5, "cooldown_days": 14, "worker_selection": "player",
        "building_type": ["brothel"], "nsfw": True,
        "background_image": "brothel_couple", "success_image": "brothel_success", "failure_image": "brothel_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Send someone who reads people. (Requires Charm; Potential: Money, Reputation)",
                "condition": "Charm", "skill_check": 50,
                "message_success": "[acting_worker] reads the couple within seconds\u2014who\u2019s bold, who\u2019s shy, who needs eye contact and who needs permission. The night starts slow: wine, conversation, a hand on a knee that nobody pulls away from. When clothes come off, [acting_worker] moves between them like the third voice in a chord\u2014never pushing, never absent. The wife cries afterward, not from sadness. They leave holding hands and whispering. The booking is one for the house ledger.",
                "message_failure": "[acting_worker] tries, but the dynamic never clicks. The husband freezes up, the wife overcompensates, and [acting_worker] can\u2019t find the rhythm that turns three strangers into something that works. The couple pays and leaves quietly. They won\u2019t be back.",
                "effect": {"success": {"money": 1000, "reputation": 12, "joy": 5}, "failure": {"money": 200, "reputation": -5, "joy": -3}, **SC0}
            },
            {
                "option": "Turn them away. Your house isn\u2019t set up for couples tonight.",
                "message": "You explain that the right worker isn\u2019t available and suggest they come back another night. They nod, disappointed but not offended. The coin stays in their pocket. The fantasy stays unresolved.",
                "effect": {**SC0, "joy": 0}
            }
        ]
    }),
    # ===== RESTAURANT =====
    evt({
        "id": "restaurant_rare_truffle_delivery",
        "description": "A forager stumbles through your kitchen door at dawn, mud to the elbows, cradling a cloth-wrapped bundle like a newborn. Inside: three black winter truffles the size of a fist\u2014the kind that don\u2019t appear on any market stall because anyone who finds them sells direct to noble houses. He\u2019s offering them to you first because he owes your cook a favor. The price is steep. The dishes you could build around them would be legend.",
        "weight": 1.5, "cooldown_days": 21, "worker_selection": "player",
        "building_type": ["restaurant"], "nsfw": False,
        "background_image": "restaurant_truffle", "success_image": "restaurant_success", "failure_image": "restaurant_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Buy the truffles and build a special menu. (Cost: Money; Requires Craft; Potential: Money, Reputation)",
                "condition": "Craft", "skill_check": 55,
                "message_success": "[acting_worker] shaves the first truffle over hand-cut pasta with brown butter and sage\u2014the smell alone stops conversation in the dining room. The second goes into a risotto that takes forty minutes and tastes like the forest floor after rain. The third becomes a sauce for seared venison that a visiting count calls the best thing he\u2019s eaten in two provinces. By week\u2019s end, the menu has a waiting list and your name is in conversations you didn\u2019t start.",
                "message_failure": "[acting_worker] slices the truffle too thick, drowns it in cream, and serves it over meat that fights the flavor instead of carrying it. The diners eat politely. No one asks for seconds. The remaining truffles are used competently but without the spark that justifies the price. You recoup costs, barely. The forager\u2019s favor was wasted.",
                "effect": {"success": {"money": 600, "reputation": 15}, "failure": {"money": -200, "reputation": -3}, **SC0}
            },
            {
                "option": "Pass. The price is too high for a gamble on truffles.",
                "message": "You thank the forager and send him on his way. He shrugs, wraps the bundle, and walks three doors down to your competitor. By evening the smell of truffle oil drifts across the street. Your cooks say nothing. They don\u2019t need to.",
                "effect": {"reputation": -2, **SC0, "joy": 0}
            }
        ]
    }),
    evt({
        "id": "restaurant_noble_poison_scare",
        "description": "Midway through the second course, a minor lord pushes back from the table, face white, hand on his stomach. His companion shouts the word every kitchen fears: poison. The dining room goes silent. Forks stop. Eyes turn to you. The lord may be ill from bad oysters, cheap wine, or genuine foul play\u2014but until you prove otherwise, every plate on every table is a suspect and your reputation is bleeding by the second.",
        "weight": 2, "cooldown_days": 14, "worker_selection": "player",
        "building_type": ["restaurant"], "nsfw": False,
        "background_image": "restaurant_poison", "success_image": "restaurant_success", "failure_image": "restaurant_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Have a worker taste-test the dish publicly. (Requires Service; Risk: Health; Potential: Reputation)",
                "condition": "Service", "skill_check": 40,
                "message_success": "[acting_worker] picks up the lord\u2019s plate, meets the room\u2019s eyes, and takes a full bite without hesitation. Chews. Swallows. Waits. Nothing happens. The lord\u2019s color returns\u2014bad oyster, not bad intent. [acting_worker] clears the plate with a bow, the kitchen sends a fresh course on the house, and by dessert the whole table is laughing about it. The story becomes an asset: the house where they\u2019ll eat from your plate to prove it\u2019s clean.",
                "message_failure": "[acting_worker] takes the bite but hesitates\u2014and the hesitation is louder than any reassurance. Two tables ask for their bill. The lord is fine by morning, but the image of a worker pausing before eating their own food lingers in the district\u2019s memory longer than the truth.",
                "effect": {"success": {"money": 200, "reputation": 12}, "failure": {"money": -300, "reputation": -8, "health": -5}, **SC0}
            },
            {
                "option": "Apologize, comp the meal, and move on. (Cost: Money)",
                "message": "You cover the lord\u2019s bill, send a bottle to his table, and have a quiet word with the kitchen about shellfish sourcing. The lord accepts graciously. The dining room resumes. No drama, no story\u2014which is exactly what you wanted.",
                "effect": {"money": -150, **SC0, "joy": 0}
            }
        ]
    }),
    # ===== CASINO =====
    evt({
        "id": "casino_card_counter_prodigy",
        "description": "Your pit boss pulls you aside with sweat on his lip. Table six\u2014the quiet one in the grey coat\u2014has been winning for three hours straight. Not flashy wins. Small, steady, relentless. The kind of pattern that says the cards aren\u2019t random to him anymore. He\u2019s counting, and he\u2019s better at it than anyone your dealers have ever faced. The house edge is bleeding. Other tables are watching.",
        "weight": 1.5, "cooldown_days": 14, "worker_selection": "player",
        "building_type": ["casino"], "nsfw": False,
        "background_image": "casino_counter", "success_image": "casino_success", "failure_image": "casino_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Send your best dealer to outplay him. (Requires Clever; Potential: Money, Reputation)",
                "condition": "Clever", "skill_check": 55,
                "message_success": "[acting_worker] takes over table six with fresh decks and a shuffle pattern the counter hasn\u2019t seen. The first hand breaks his rhythm. The second makes him doubt his numbers. By the fifth, he\u2019s betting scared instead of calculated, and [acting_worker] takes back the night\u2019s losses with the calm of someone sorting laundry. The counter cashes out at a modest loss, tips his hat, and leaves knowing this floor has teeth.",
                "message_failure": "[acting_worker] sits down but the counter adjusts within two hands. He reads the new shuffle, recalibrates, and keeps winning\u2014quieter now, but faster. By the time you pull [acting_worker] off the table, the damage is worse than before. The counter leaves with a fat purse and a smile that says he\u2019ll be back.",
                "effect": {"success": {"money": 900, "reputation": 10}, "failure": {"money": -600, "reputation": -8}, **SC0}
            },
            {
                "option": "Ask him to leave. House rules.",
                "message": "You approach table six and explain, quietly, that the house reserves the right to end any session. He nods\u2014no scene, no argument. He pockets his winnings, tips the waitress, and walks out. Clean exit, modest loss. But the regulars saw you blink first.",
                "effect": {"money": -200, "reputation": -3, **SC0, "joy": 0}
            }
        ]
    }),
    evt({
        "id": "casino_last_hand_desperation",
        "description": "A merchant who\u2019s been losing all night stands up from the table with nothing left. Then he puts his signet ring on the felt\u2014the kind that seals trade contracts across three provinces. He wants one last hand, everything on the line. Your dealer looks at you. The ring is worth more than the merchant lost tonight. If you take the bet and he wins, you owe double. If he loses, you own a piece of his commercial identity.",
        "weight": 1, "cooldown_days": 21, "worker_selection": "player",
        "building_type": ["casino"], "nsfw": False,
        "background_image": "casino_lasthand", "success_image": "casino_success", "failure_image": "casino_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Accept the bet. Let the cards decide. (Risk: Money; Potential: Money, Reputation)",
                "condition": "Clever", "skill_check": 50,
                "message_success": "[acting_worker] deals the hand clean. The merchant\u2019s face tells the story before the cards do\u2014he had nothing. The ring stays on your side of the felt. He stands, nods once, and walks out without a word. The room exhales. By morning, the story of the signet ring is in every gambling den in the district. You sell it back to him a week later for twice what he lost\u2014and he\u2019s grateful for the discretion.",
                "message_failure": "[acting_worker] deals the hand and the merchant turns over three queens. The room erupts. You pay out double from the house coffers while the merchant kisses his ring and walks out a legend. Your regulars love the story. Your accountant does not.",
                "effect": {"success": {"money": 1200, "reputation": 10}, "failure": {"money": -800, "reputation": 5}, **SC0}
            },
            {
                "option": "Refuse. The house doesn\u2019t take heirlooms.",
                "message": "You shake your head. The merchant stares, then laughs\u2014a bitter, exhausted sound. He takes his ring and leaves. The room respects the call. No spectacle, no legend. Just a clean floor and a house that knows where the line is.",
                "effect": {"reputation": 3, **SC0, "joy": 0}
            }
        ]
    }),
    # ===== TAVERN =====
    evt({
        "id": "tavern_legendary_drinking_contest",
        "description": "A mountain of a man kicks the door open and slams a barrel of dwarven stout on your bar. He bellows a challenge to the room: anyone who can outdrink him gets the barrel and his purse. If nobody lasts, he drinks free for a month and tells every tavern in the province that yours breeds lightweights. Three regulars are already rolling up their sleeves. The room wants blood\u2014or at least vomit.",
        "weight": 2, "cooldown_days": 14, "worker_selection": "player",
        "building_type": ["tavern"], "nsfw": False,
        "background_image": "tavern_drinking", "success_image": "tavern_success", "failure_image": "tavern_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Enter a worker in the contest. (Risk: Health; Potential: Money, Reputation)",
                "condition": "Service", "skill_check": 45,
                "message_success": "[acting_worker] sits down across from the giant, matches him mug for mug, and doesn\u2019t blink. Twelve rounds in, the challenger\u2019s eyes glaze. Fourteen, his hand misses the handle. Sixteen, his forehead hits the bar. [acting_worker] finishes the seventeenth standing, the room roars, and the barrel is yours. The story will be told in this tavern for years.",
                "message_failure": "[acting_worker] holds strong through eight rounds but the ninth hits like a wall. The challenger grins as [acting_worker] slides sideways off the stool. He claims his month of free drinks to thunderous applause. Your tavern just became famous\u2014for losing.",
                "effect": {"success": {"money": 400, "reputation": 10, "joy": 5}, "failure": {"money": -200, "reputation": -5, "health": -8}, **SC0}
            },
            {
                "option": "Decline. Your staff isn\u2019t for entertainment.",
                "message": "You wave the challenger off. He shrugs, drinks the barrel himself over the next three hours, pays his tab, and leaves. The regulars mutter about what could have been.",
                "effect": {**SC0, "joy": -2}
            }
        ]
    }),
    evt({
        "id": "tavern_ghost_story_night",
        "description": "The fire is low, the wind is howling, and a traveler at the corner table starts talking\u2014quietly at first, then louder as the room leans in. A ghost story. Real or not, the voice carries it like gospel. Then the traveler stops mid-sentence, looks at you, and says: \u2018Your turn. This room has its own ghosts\u2014I can feel them. Someone here knows the story.\u2019 Every eye turns to your staff.",
        "weight": 2, "cooldown_days": 10, "worker_selection": "player",
        "building_type": ["tavern"], "nsfw": False,
        "background_image": "tavern_ghost", "success_image": "tavern_success", "failure_image": "tavern_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Have a worker tell the tavern\u2019s story. (Requires Charm; Potential: Reputation)",
                "condition": "Charm", "skill_check": 40,
                "message_success": "[acting_worker] pulls a chair to the fire and starts talking. Not loud\u2014just enough to carry. A story about the cellar, a locked door nobody opens, footsteps on stairs that don\u2019t exist anymore. True or invented, it doesn\u2019t matter\u2014the room believes every word. When it ends, the silence lasts three full seconds before someone orders a round for the whole house. Your tavern just became the kind of place people tell other people about.",
                "message_failure": "[acting_worker] tries, but the delivery is flat\u2014too many details, wrong pacing, a punchline where the dread should be. The room drifts back to their drinks. The traveler finishes the tale themselves, and the crowd cheers for them instead.",
                "effect": {"success": {"reputation": 8, "joy": 3}, "failure": {"reputation": -2, "joy": -1}, **SC0}
            },
            {
                "option": "Let the traveler have the floor. It\u2019s their show.",
                "message": "You pour the traveler another drink and let the story run. The room loves it. They tip well and stay late. A good night, but the story belongs to someone who won\u2019t be back.",
                "effect": {"money": 100, **SC0, "joy": 0}
            }
        ]
    }),
    # ===== ADVENTURERS GUILD =====
    evt({
        "id": "guild_wounded_beast_trophy",
        "description": "A hunter staggers through the guild door dragging something behind him\u2014the severed head of a basilisk, stone eye still glowing faintly amber. He collapses before reaching the bounty board. The head is worth a fortune to the right alchemist, but the hunter is bleeding badly and the basilisk\u2019s mate is almost certainly still out there. The bounty board says dead or alive. The head says the job is half done.",
        "weight": 1.5, "cooldown_days": 14, "worker_selection": "player",
        "building_type": ["adventurers_guild"], "nsfw": False,
        "background_image": "guild_basilisk", "success_image": "guild_success", "failure_image": "guild_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Send a worker to finish the job. (Requires Combat; Risk: Health; Potential: Money, Reputation)",
                "condition": "Combat", "skill_check": 55,
                "message_success": "[acting_worker] tracks the mate to its den using the blood trail from the first kill. The fight is ugly\u2014stone gaze, whipping tail, jaws that crush plate\u2014but [acting_worker] keeps low, strikes between lunges, and takes the second head clean. Both trophies on the bounty board by nightfall. The guild earns its cut, the alchemist gets two specimens, and your name climbs the board.",
                "message_failure": "[acting_worker] finds the den but the basilisk is faster than expected. A glancing hit from the tail cracks ribs before [acting_worker] retreats. The second head stays attached to a very alive, very angry basilisk. You sell the first head for a reduced price. The bounty goes unclaimed.",
                "effect": {"success": {"money": 1000, "reputation": 12, "joy": 3}, "failure": {"money": 200, "reputation": -5, "health": -15}, **SC0}
            },
            {
                "option": "Sell the head and patch up the hunter. (Gain: Money)",
                "message": "You treat the hunter\u2019s wounds and sell the basilisk head to the alchemist for a fair price. No second hunt, no second risk. Practical, profitable, and nobody else bleeds today.",
                "effect": {"money": 400, **SC0, "joy": 0}
            }
        ]
    }),
    evt({
        "id": "guild_cursed_sword_client",
        "description": "A woman walks in carrying a longsword wrapped in chains and salt cloth. She sets it on the counter and steps back as if it might bite. The blade hums\u2014faintly, but enough to make the nearest candle gutter. She says it belonged to her father. Since he died, the sword has cut three people who touched it, always on the left hand, always the ring finger. She wants it identified, cleansed, or destroyed. She\u2019ll pay whatever it costs to stop dreaming about it.",
        "weight": 1, "cooldown_days": 21, "worker_selection": "player",
        "building_type": ["adventurers_guild"], "nsfw": False,
        "background_image": "guild_cursed", "success_image": "guild_success", "failure_image": "guild_failure",
        "worker_gender_requirement": None,
        "choices": [
            {
                "option": "Have a worker examine and cleanse the blade. (Requires Craft; Risk: Health; Potential: Money, Reputation)",
                "condition": "Craft", "skill_check": 50,
                "message_success": "[acting_worker] unwraps the blade with gloved hands and reads the runes along the fuller. Old binding script\u2014a jealousy curse, blood-linked to the father\u2019s wedding ring. The cleansing takes an hour of salt, fire, and a chant [acting_worker] learned from a witch three jobs ago. When it\u2019s done, the hum dies. The candles stop flickering. The woman lifts the sword and nothing happens. She weeps, pays double, and tells every adventurer she knows where to bring cursed steel.",
                "message_failure": "[acting_worker] identifies the curse but the cleansing goes wrong\u2014the sword screams, the salt circle breaks, and [acting_worker] catches a cut across the left hand before the blade is re-wrapped. The woman takes her sword back, white-faced. You patch [acting_worker] up and refund half the fee.",
                "effect": {"success": {"money": 700, "reputation": 10}, "failure": {"money": -100, "reputation": -3, "health": -10}, **SC0}
            },
            {
                "option": "Refuse. Cursed weapons are above your pay grade.",
                "message": "You tell the woman your guild handles bounties, not exorcisms. She wraps the sword back up, chains clinking, and carries it out. The hum fades. Your workers exchange relieved glances. Smart call\u2014probably.",
                "effect": {**SC0, "joy": 0}
            }
        ]
    }),
]

data.extend(new)

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Added {len(new)} events. Total: {len(data)}")
