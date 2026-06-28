# lanista_complete.rpy — All Lanista content (Master of the Sands)
# Stages 1-6, debt finance, Program the Card corruption ladder,
# wager/sponsor RNG, After the Crowd repeatable, three endings.

################################################################################
### LANISTA — DEFAULT VARIABLES
################################################################################

default lanista_gender = ""                 # "male" / "female" — set on first visit
default lanista_known_name = False
default lanista_devotion = 0
default lanista_dominion = 0
default lanista_affection = 0
default lanista_corruption = 0              # 0-100
default lanista_stage = 1
default lanista_visit_count = 0
default lanista_last_talk_total_days = None
default lanista_last_question_total_days = None
default lanista_last_gift_total_days = None
default lanista_s1_talks_done = []
default lanista_s1_remarks_done = []
default lanista_s2_talks_done = []
default lanista_s2_remarks_done = []
default lanista_s3_talks_done = []
default lanista_s3_remarks_done = []
default lanista_s4_talks_done = []
default lanista_s4_remarks_done = []
default lanista_s5_talks_done = []
default lanista_s5_remarks_done = []
default lanista_s6_talks_done = []
default lanista_gifts_given = 0
default lanista_debt_finance_unlocked = False
default lanista_debt_finance_last_day = None
default lanista_donation_total = 0
default lanista_donation_highest_tier = 0
default lanista_favors_total = 0
default lanista_favor_highest_tier = 0
default lanista_card_tier = 0               # 0-4 highest unlocked show format
default lanista_card_last_day = None
default lanista_pinup_unlocked = False      # gates arena_pinup_barbarian profession
default lanista_oilchains_unlocked = False  # gates arena_oil_chains profession
default lanista_spectacle_unlocked = False  # gates arena_spectacle profession
default lanista_wager_last_day = None
default lanista_s3_gate_fired = False
default lanista_s4_gate_fired = False
default lanista_morning_after_done = False
default lanista_s5_gate_fired = False
default lanista_s6_gate_fired = False
default lanista_aftercrowd_last_day = None
default lanista_aftercrowd_tier = 1
default lanista_aftercrowd_variant_index = 0
default lanista_ending_route = ""           # "devotion" / "dominion" / "mixed"
default lanista_ending_done = False
default lanista_is_worker = False
default lanista_ending_devotion = False     # flags for post-arc event gating
default lanista_ending_dominion = False
default lanista_ending_mixed = False
default lanista_post_arc_talk_index = 0
default lanista_arrangement_change_count = 0

################################################################################
### LANISTA — TRANSFORMS & SCENE RESET
################################################################################

transform lanista_bg_blur:
    blur 4.0

transform lanista_cg_fit:
    fit "contain"
    xalign 0.5
    yalign 0.5

transform lanista_bust_right:
    xpos 1.03
    ypos 1.0
    xanchor 1.0
    yanchor 1.0
    yoffset 40

label lanista_restore_visit_scene:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena.png" if renpy.loadable("images/events/arena.png") else "images/event_bg.png")
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _lanista_bust = "images/lanista/lanista_{}_neutral.png".format(_g) if renpy.loadable("images/lanista/lanista_{}_neutral.png".format(_g)) else None
    scene expression _arena_bg at lanista_bg_blur
    show black as lanista_bg_dim:
        alpha 0.35
    if _lanista_bust:
        show expression _lanista_bust as lanista_bust at lanista_bust_right
    return

################################################################################
### LANISTA — PYTHON HELPERS
################################################################################

init python:
    def lanista_recalculate_stage():
        aff = int(getattr(store, "lanista_affection", 0) or 0)
        g3 = bool(getattr(store, "lanista_s3_gate_fired", False))
        g4 = bool(getattr(store, "lanista_s4_gate_fired", False))
        g5 = bool(getattr(store, "lanista_s5_gate_fired", False))
        g6 = bool(getattr(store, "lanista_s6_gate_fired", False))
        card = int(getattr(store, "lanista_card_tier", 0) or 0)
        if g6:
            store.lanista_stage = 7
        elif g5 and aff >= 110:
            store.lanista_stage = 6
        elif g4 and card >= 4 and aff >= 91:
            store.lanista_stage = 5
        elif g4 and aff >= 80:
            store.lanista_stage = 4
        elif g3 and aff >= 64:
            store.lanista_stage = 4
        elif aff >= 39:
            store.lanista_stage = 3
        elif aff >= 20:
            store.lanista_stage = 2
        else:
            store.lanista_stage = 1

    def lanista_is_dominion_route():
        dev = int(getattr(store, "lanista_devotion", 0) or 0)
        dom = int(getattr(store, "lanista_dominion", 0) or 0)
        if dom != dev:
            return dom > dev
        favors = int(getattr(store, "lanista_favors_total", 0) or 0)
        donations = int(getattr(store, "lanista_donation_total", 0) or 0)
        if favors != donations:
            return favors > donations
        return False

    def lanista_is_devotion_route():
        return not lanista_is_dominion_route()

    def lanista_determine_ending():
        dev = int(getattr(store, "lanista_devotion", 0) or 0)
        dom = int(getattr(store, "lanista_dominion", 0) or 0)
        if dev > dom and (dev - dom) >= 10:
            return "devotion"
        if dom > dev and (dom - dev) >= 10:
            return "dominion"
        return "mixed"

    def lanista_pronoun(kind):
        """kind: 'subj'/'obj'/'poss'/'refl'/'title'. Gender from lanista_gender."""
        male = (getattr(store, "lanista_gender", "male") or "male") != "female"
        table = {
            "subj": ("he", "she"), "obj": ("him", "her"),
            "poss": ("his", "her"), "refl": ("himself", "herself"),
            "title": ("the Master of the Sands", "the Master of the Sands"),
        }
        m, f = table.get(kind, ("they", "they"))
        return m if male else f

    def lanista_wager(stake, base_chance):
        """Resolve a money+RNG physical challenge. Returns (won_bool, delta_money).
        Deducts stake up front; on win returns ~2x stake as winnings."""
        stake = max(0, int(stake))
        chance = max(0.05, min(0.95, float(base_chance)))
        store.money = int(getattr(store, "money", 0)) - stake
        won = renpy.random.random() < chance
        winnings = int(stake * 2) if won else 0
        store.money = int(getattr(store, "money", 0)) + winnings
        return (won, winnings - stake)

################################################################################
### LANISTA — FIRST MEETING (gender choice)
################################################################################

label lanista_first_meeting:
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else "images/event_bg.png"
    scene expression _arena_bg at lanista_bg_blur
    show black as lanista_bg_dim:
        alpha 0.35
    narrator "The practice yard is all iron and chalk dust. At its center a figure stands over two sparring recruits, correcting a guard with a single clipped word, unbothered by your arrival."
    narrator "The Master of the Sands — the Lanista who holds this Arena in one scarred fist."
    narrator "They turn, and for the first time you see them plainly."
    menu:
        "A man: broad, close-cropped, still as a drawn blade.":
            $ lanista_gender = "male"
        "A woman: broad, close-cropped, still as a drawn blade.":
            $ lanista_gender = "female"
    $ lanista_known_name = False
    return

################################################################################
### LANISTA — CHARACTER DEFINE
################################################################################

define lanista_npc = Character("The Lanista", color="#c98a3a")

################################################################################
### LANISTA — VISIT ENTRY
################################################################################

label lanista_visit:
    if not getattr(store, "lanista_gender", ""):
        call lanista_first_meeting from _lanista_first_meeting_call
    $ lanista_visit_count += 1
    $ lanista_recalculate_stage()
    call lanista_restore_visit_scene from _lanista_restore_on_visit
    if not lanista_known_name:
        narrator "The Lanista measures you with the flat attention of someone deciding whether you are worth the breath."
        lanista_npc "Coin-counter. Say your piece."
        $ lanista_known_name = True
    elif lanista_visit_count <= 2:
        narrator "The Lanista does not set down the blade being honed. The attention you get is the kind spared for weather."
        lanista_npc "Back again. The sand's where I left it. Say what you came to say."
    elif lanista_stage >= 3 and lanista_is_devotion_route():
        $ _emotion = "amused"
        $ _g = getattr(store, "lanista_gender", "male") or "male"
        $ _bust = "images/lanista/lanista_{}_{}.png".format(_g, _emotion)
        if renpy.loadable(_bust):
            show expression _bust as lanista_bust at lanista_bust_right
        narrator "The blade goes down when you cross the threshold. From someone who sets nothing down carelessly, that is its own kind of welcome."
        lanista_npc "[player_title]. Good — the day was getting honest and dull. Sit."
    elif lanista_stage >= 3:
        narrator "The Lanista marks your arrival with a short nod, the way one veteran grants another the room to cross the yard."
        lanista_npc "[player_title]. You've a habit of turning up. I've stopped minding it."
    elif lanista_stage >= 2 and lanista_is_devotion_route():
        narrator "The hard line of the Lanista's mouth eases by a hair — no more than that, but you have learned to read the small ground."
        lanista_npc "You. Still watching the craft and not the purse. Stay a while, [player_title]."
    elif lanista_stage >= 2:
        narrator "The Lanista looks up from the recruits, taking your measure again and finding it unchanged."
        lanista_npc "Coin-counter. You're persistent. I'll allow you that much."
    else:
        narrator "The Lanista's gaze flicks to you and away, back to the recruits where it prefers to rest."
        lanista_npc "Coin-counter. Say your piece, [player_title]."
    jump lanista_visit_menu

################################################################################
### LANISTA — GATED VISIT MENU
################################################################################

label lanista_visit_menu:
    call lanista_restore_visit_scene from _lanista_restore_menu
    $ _total_days = calculate_total_days()
    if not lanista_s3_gate_fired and lanista_stage >= 3 and len(lanista_s3_talks_done) >= 3 and lanista_affection >= 50:
        jump lanista_s3_gate
    if not lanista_s4_gate_fired and lanista_stage >= 4 and len(lanista_s4_talks_done) >= 3 and lanista_affection >= 80 and lanista_debt_finance_unlocked:
        jump lanista_s4_gate
    if lanista_s4_gate_fired and not lanista_morning_after_done:
        $ lanista_morning_after_done = True
        jump lanista_morning_after
    if not lanista_s5_gate_fired and lanista_stage >= 5 and len(lanista_s5_talks_done) >= 3 and lanista_affection >= 100:
        jump lanista_s5_gate
    if not lanista_s6_gate_fired and lanista_s5_gate_fired and lanista_stage >= 6 and len(lanista_s6_talks_done) >= 3 and lanista_affection >= 110:
        jump lanista_s6_gate
    if lanista_s6_gate_fired and not lanista_ending_done:
        jump lanista_ending_resolution
    $ _talk_free = lanista_last_talk_total_days != _total_days
    $ _remark_free = lanista_last_question_total_days != _total_days
    $ _s1_talk = lanista_stage == 1 and len(lanista_s1_talks_done) < 3
    $ _s2_talk = lanista_stage == 2 and len(lanista_s2_talks_done) < 3
    $ _s3_talk = not lanista_s3_gate_fired and lanista_stage >= 3 and len(lanista_s3_talks_done) < 3
    $ _s4_talk = not lanista_s4_gate_fired and lanista_stage >= 4 and len(lanista_s4_talks_done) < 3
    $ _s5_talk = not lanista_s5_gate_fired and lanista_stage >= 5 and len(lanista_s5_talks_done) < 3
    $ _s6_talk = not lanista_s6_gate_fired and lanista_stage >= 6 and len(lanista_s6_talks_done) < 3
    $ _s1_rem = lanista_stage == 1 and len(lanista_s1_remarks_done) < 3
    $ _s2_rem = lanista_stage == 2 and len(lanista_s2_remarks_done) < 2
    $ _s3_rem = not lanista_s3_gate_fired and lanista_stage >= 3 and len(lanista_s3_remarks_done) < 2
    $ _s4_rem = not lanista_s4_gate_fired and lanista_stage >= 4 and len(lanista_s4_remarks_done) < 2
    $ _s5_rem = not lanista_s5_gate_fired and lanista_stage >= 5 and len(lanista_s5_remarks_done) < 2
    $ _finance_avail = lanista_stage >= 4 and not lanista_s4_gate_fired and lanista_debt_finance_unlocked and lanista_debt_finance_last_day != _total_days
    $ _finance_dom = lanista_is_dominion_route()
    $ _card_avail = lanista_s3_gate_fired and lanista_card_tier < 4 and lanista_card_last_day != _total_days
    $ _wager_avail = lanista_stage >= 2 and lanista_wager_last_day != _total_days
    $ _aftercrowd_avail = lanista_s4_gate_fired and (_total_days - (lanista_aftercrowd_last_day or 0)) >= 3
    menu:
        lanista_npc "..."
        "Talk." if _talk_free and _s1_talk:
            jump lanista_s1_talk_router
        "Talk." if _talk_free and _s2_talk:
            jump lanista_s2_talk_router
        "Talk." if _talk_free and _s3_talk:
            jump lanista_s3_talk_router
        "Talk." if _talk_free and _s4_talk:
            jump lanista_s4_talk_router
        "Talk." if _talk_free and _s5_talk:
            jump lanista_s5_talk_router
        "Talk." if _talk_free and _s6_talk:
            jump lanista_s6_talk_router
        "Talk." if _talk_free and not (_s1_talk or _s2_talk or _s3_talk or _s4_talk or _s5_talk or _s6_talk):
            jump lanista_talk_generic
        "Talk." if not _talk_free:
            lanista_npc "I've given you words enough today. Come back when the sun's moved."
            jump lanista_visit_menu
        "Make a remark." if _remark_free and _s1_rem:
            jump lanista_s1_remark_router
        "Make a remark." if _remark_free and _s2_rem:
            jump lanista_s2_remark_router
        "Make a remark." if _remark_free and _s3_rem:
            jump lanista_s3_remark_router
        "Make a remark." if _remark_free and _s4_rem:
            jump lanista_s4_remark_router
        "Make a remark." if _remark_free and _s5_rem:
            jump lanista_s5_remark_router
        "Cover the Arena's debts." if _finance_avail and not _finance_dom:
            jump lanista_debt_donate
        "Call in what they owe you." if _finance_avail and _finance_dom:
            jump lanista_debt_favor
        "Program the card." if _card_avail:
            jump lanista_program_card
        "Back a fighter. (Wager)" if _wager_avail:
            jump lanista_wager_menu
        "After the crowd." if _aftercrowd_avail:
            jump lanista_aftercrowd
        "Bring a gift." if lanista_last_gift_total_days != _total_days:
            jump lanista_gift
        "Take their measure.":
            jump lanista_assess
        "Leave.":
            hide lanista_bust
            hide lanista_bg_dim
            window hide
            $ renpy.show_screen("map_screen")
            $ renpy.show_screen("arena_menu")
            jump tavern_screen

################################################################################
### LANISTA — STUB LABELS (replaced by later tasks)
################################################################################

label lanista_s1_talk_router:
    if "s1_t1" not in lanista_s1_talks_done:
        jump lanista_s1_talk_1
    elif "s1_t2" not in lanista_s1_talks_done:
        jump lanista_s1_talk_2
    elif "s1_t3" not in lanista_s1_talks_done:
        jump lanista_s1_talk_3
    else:
        jump lanista_talk_generic

label lanista_s1_talk_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The recruits break for water. The Lanista cleans a practice blade with a rag, in no hurry, not looking at you."
    lanista_npc "You're not here to fight. You don't stand like someone who's been hit."
    lanista_npc "So you're here to buy something. They always are."
    menu:
        "\"I came to watch a craft done well.\"":
            $ lanista_devotion += 2
            $ lanista_affection += 2
            narrator "Something shifts at the corner of the Lanista's mouth. Not a smile. The place a smile would go."
            lanista_npc "Craft. Most call it blood and call it a day."
            lanista_npc "Watch, then, [_ttl]. The sand doesn't lie, even when everyone standing on it does."
        "\"Empty seats don't pay for sand.\"":
            $ lanista_dominion += 2
            $ lanista_affection += 2
            $ lanista_corruption += 1
            narrator "The rag stops moving. For the first time the Lanista looks at you directly — flat, measuring, unimpressed and unsurprised at once."
            lanista_npc "A coin-counter who's done the counting. Of course."
            lanista_npc "The seats are my concern, [_ttl]. Keep your arithmetic to your own ledger."
    $ lanista_s1_talks_done = list(lanista_s1_talks_done) + ["s1_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s1_talk_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Below, an honest bout runs its course — two journeymen, evenly matched, trading nothing pretty, only true. In the stands whole rows sit empty. The good seats fill for the maimings, not for this."
    lanista_npc "Look at that. Two of the finest blades in the province, and the benches are bare."
    lanista_npc "They'd be packed shoulder to shoulder if I'd promised a cripple by sundown."
    menu:
        "\"A full house forgets you by morning. Honor outlasts it.\"":
            $ lanista_devotion += 2
            $ lanista_affection += 2
            narrator "The Lanista watches the bout a moment longer before answering, as if checking your words against the men on the sand."
            lanista_npc "Outlasts it. Aye. I've buried fighters the crowd cheered, and the crowd forgot them inside a week."
            lanista_npc "You've sat in cheaper seats than your purse suggests, [_ttl]. I'll grant you that."
        "\"The crowd pays for blood, not virtue. Sell them blood.\"":
            $ lanista_dominion += 2
            $ lanista_affection += 2
            $ lanista_corruption += 2
            narrator "The Lanista turns from the fight to you. No anger in it — something colder. The look of a fighter who has heard the truth and dislikes the mouth it came from."
            lanista_npc "Spoken like someone who's never had to wash the sand after."
            lanista_npc "You're not wrong, [_ttl]. That's the trouble with you. You're not wrong."
    $ lanista_s1_talks_done = list(lanista_s1_talks_done) + ["s1_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s1_talk_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A clerk leaves a stack of papers on the bench by the weapons rack and hurries off at a barked order. The top sheet has slid loose. You catch the press of a seal in the wax — a moneylender's mark, the kind that does not send its letters twice."
    lanista_npc "..."
    narrator "The Lanista follows your eyes to the page, and for half a breath the stillness becomes a different stillness. Then a broad hand turns the sheet face-down without hurry."
    lanista_npc "The Arena's accounts are the Arena's. You saw a seal. You saw nothing."
    menu:
        "\"Let me help. Quietly. No strings, no ledger.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "The hand stays flat on the paper. The Lanista studies you the way one studies an unfamiliar guard — hunting the feint inside the open stance."
            lanista_npc "No strings. Everyone says no strings. Then the bill comes due in something that isn't coin."
            lanista_npc "...I'll remember the offer, [_ttl]. That is not the same as taking it. But I'll remember."
        "\"A debt like that is worth knowing. I'll file it away.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 1
            narrator "The Lanista's expression does not change, and that is the answer. You have shown a card. The Lanista has shown one too."
            lanista_npc "There it is. The counting eyes. I wondered when they'd open."
            lanista_npc "File it where you like, [_ttl]. Just know the sands remember who reaches for a throat — and who reaches for an open hand."
    $ lanista_debt_finance_unlocked = True
    $ lanista_s1_talks_done = list(lanista_s1_talks_done) + ["s1_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s2_talk_router:
    if "s2_t1" not in lanista_s2_talks_done:
        jump lanista_s2_talk_1
    elif "s2_t2" not in lanista_s2_talks_done:
        jump lanista_s2_talk_2
    elif "s2_t3" not in lanista_s2_talks_done:
        jump lanista_s2_talk_3
    else:
        jump lanista_talk_generic

label lanista_s2_talk_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You wait for a lull between bouts and lay the idea out plainly. Give the crowd a story to follow. Two fighters with a grudge between them — invented, dressed up, sold to the stands. A champion who looks finished, then claws upright at the last breath. Drama, staged and certain, with real steel underneath."
    lanista_npc "Staged."
    narrator "The word lands flat. The Lanista sets down the whetstone and looks at you the way a smith studies a crack running through good metal — the first one, the one all the others follow."
    lanista_npc "I sell true bouts. The fighter who falls, falls because the other was better. That is the whole of what people trust about this place."
    lanista_npc "You're asking me to score the iron and call it craft."
    menu:
        "\"The steel stays real. The story's only how you seat them around it.\"":
            $ lanista_devotion += 2
            $ lanista_affection += 2
            $ lanista_corruption += 2
            narrator "The Lanista is quiet a long moment. Down on the sand a recruit takes a fall, gets up. The argument is being weighed — and that is further than it would have gone a month ago."
            lanista_npc "Real steel. A real grudge they happen to have read about first. ...It isn't a lie if the wound's true. That's the kind of thing a clever mouth says."
            lanista_npc "I'll think on it, [_ttl]. That is all. I'll think on it."
        "\"The men holding your debt don't care how honest the seats were when they sat empty.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            $ lanista_corruption += 3
            narrator "That stops the breath in the yard. The Lanista's jaw works once. The truth of it is the part that bites — there is no answer on the sand for a creditor waiting at the gate with a sealed note."
            lanista_npc "Low, [_ttl]. Accurate, and low."
            lanista_npc "...No. They don't care. That's the trouble with the men I owe. They never learned to love the craft, only the count."
            lanista_npc "Say no more today. I heard you the first time."
    $ lanista_s2_talks_done = list(lanista_s2_talks_done) + ["s2_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s2_talk_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The Lanista favors one leg crossing the yard — a small hitch, easy to miss, never absent. You ask about it, and for once the question is not turned aside."
    lanista_npc "Eleven seasons on this sand. Champion for six of them. People forget that, looking at the rag and the whetstone."
    lanista_npc "There was a Nordmark brute they shipped down to end my run. Reach like a gate-beam, patient as winter. We went three turns of the glass. Longest bout this Arena ever sold out twice over."
    narrator "A hand drifts to the bad knee without the Lanista seeming to notice — the body remembering what the voice keeps level."
    lanista_npc "I won. Put him down clean. And his last swing took the leg out from under the rest of my life. You don't fight on a knee that folds. So you teach. You manage. You learn to love the count."
    menu:
        "\"Three turns of the glass against a giant. That isn't luck. That's mastery.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "The Lanista holds your eye, hunting the flattery in it, and does not find the shape expected."
            lanista_npc "Mastery. Aye, it was. I don't say it loud — said loud, it's just an old fighter grieving the young one they buried."
            lanista_npc "You'd have liked the fighter I was, [_ttl]. Some days I think you'd have liked them better than what's left."
        "\"A wound that took the leg and the crown both. That has to gnaw at you.\"":
            $ lanista_dominion += 2
            $ lanista_affection += 2
            narrator "Something shutters behind the Lanista's face — you have set a thumb on the old bruise, and you have done it on purpose, and you are both aware of it."
            lanista_npc "Gnaw. There's a word. You went looking for the soft place and found it on the first try."
            lanista_npc "It gnaws, [_ttl]. Every step. Now you know where to press. I'll remember that you wanted to know."
    $ lanista_s2_talks_done = list(lanista_s2_talks_done) + ["s2_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s2_talk_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "This time the Lanista does not turn the page over. The ledger lies open on the bench, and you are not waved off when you step close enough to read it. Column after column in a cramped, honest hand — and at the foot of each, a number that has stopped pretending."
    narrator "It is worse than the seal suggested. The seal was one lender. The book holds three."
    lanista_npc "Now you've seen it. The whole of it. Not the polite version — the one that keeps me awake."
    lanista_npc "I let you read it because I am tired of being the only set of eyes on it. Make of that what you will."
    menu:
        "\"Then you're not the only set of eyes anymore. We carry it together — shoulder to shoulder.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "The Lanista looks from the book to you, and the stillness this time is not a wall. It is the pause before setting down a weight carried too long alone."
            lanista_npc "Together. You say it like it's simple. It never is."
            lanista_npc "...But you're standing on my side of the bench to say it. Nobody's done that in a long while, [_ttl]. I'll not forget who did."
        "\"Then let me buy in. My coin clears those columns — and my voice sits at this bench from now on.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 3
            $ lanista_corruption += 1
            narrator "The offer is clean, and the price folded inside it is clean too. The Lanista reads both at once — the rope thrown, and the hand that will hold the other end of it ever after."
            lanista_npc "Your coin. Your voice. The columns clear, and a piece of the sand answers to you instead of me."
            lanista_npc "It's a fair trade. That's what makes it dangerous. ...I hear you, [_ttl]. We're not done settling the shape of it — but I hear you."
    $ lanista_s2_talks_done = list(lanista_s2_talks_done) + ["s2_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s3_talk_router:
    lanista_npc "Nothing new under this sun, coin-counter."
    jump lanista_visit_menu

label lanista_s4_talk_router:
    lanista_npc "Nothing new under this sun, coin-counter."
    jump lanista_visit_menu

label lanista_s5_talk_router:
    lanista_npc "Nothing new under this sun, coin-counter."
    jump lanista_visit_menu

label lanista_s6_talk_router:
    lanista_npc "Nothing new under this sun, coin-counter."
    jump lanista_visit_menu

label lanista_talk_generic:
    lanista_npc "Nothing new under this sun, coin-counter."
    jump lanista_visit_menu

label lanista_s1_remark_router:
    if "s1_r1" not in lanista_s1_remarks_done:
        jump lanista_s1_remark_1
    elif "s1_r2" not in lanista_s1_remarks_done:
        jump lanista_s1_remark_2
    elif "s1_r3" not in lanista_s1_remarks_done:
        jump lanista_s1_remark_3
    else:
        jump lanista_talk_generic

label lanista_s1_remark_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You let your gaze travel the old wounds the Lanista wears like a second armor — the seam across one forearm, the notch missing from an ear, the pale rope of scar that vanishes under the collar."
    narrator "\"You kept count of those the hard way,\" you say."
    lanista_npc "Every one's a lesson I was slow to learn. The slow ones leave the deepest marks."
    $ lanista_affection += 1
    $ lanista_devotion += 1
    $ lanista_s1_remarks_done = list(lanista_s1_remarks_done) + ["s1_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s1_remark_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A recruit fumbles the haft of a practice spear. The Lanista crosses the yard, closes a scarred hand over the recruit's, and resets each finger without a word — patient, exact, the way one might tune an instrument."
    narrator "\"You could just shout at the lad,\" you observe."
    lanista_npc "Shouting teaches him to flinch. The hand teaches the hand. He'll keep this long after he's forgotten my voice."
    $ lanista_affection += 1
    $ lanista_devotion += 1
    $ lanista_s1_remarks_done = list(lanista_s1_remarks_done) + ["s1_r2"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s1_remark_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Along a high shelf behind the rack sits a row of victor's wreaths and bronze tokens, grey under a skin of chalk dust. Trophies of fighters who mattered, on days the crowd has long since spent."
    narrator "\"Nobody dusts those,\" you note."
    lanista_npc "Glory's cheap to win and cheaper to keep. The names matter to me. The shine never did."
    $ lanista_affection += 1
    $ lanista_dominion += 1
    $ lanista_s1_remarks_done = list(lanista_s1_remarks_done) + ["s1_r3"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s2_remark_router:
    if "s2_r1" not in lanista_s2_remarks_done:
        jump lanista_s2_remark_1
    elif "s2_r2" not in lanista_s2_remarks_done:
        jump lanista_s2_remark_2
    else:
        jump lanista_talk_generic

label lanista_s2_remark_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A champion's belt hangs on a peg by the weapons rack, the leather gone dark and supple with old wear, the bronze plate at its center worn bright by a thumb that no longer touches it. Close enough to see from the bench. Too far to be worn."
    narrator "\"You keep it where you'll look at it,\" you say, \"but not where you'll reach for it.\""
    lanista_npc "It fit a fighter who could carry it. I keep it honest about which of us is still standing."
    $ lanista_affection += 1
    $ lanista_devotion += 1
    $ lanista_s2_remarks_done = list(lanista_s2_remarks_done) + ["s2_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s2_remark_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Before the gates open the Lanista stands at the mouth of the tunnel and counts the house as it fills — not the heads that come, you realize, but the benches that stay bare. With each empty row the jaw sets a fraction harder, a tally kept in muscle."
    narrator "\"You count the seats nobody took,\" you observe."
    lanista_npc "Full rows lie to you. They cheer, and you think you've won. The empty ones tell the truth, and the truth is what I owe by month's end."
    $ lanista_affection += 1
    $ lanista_dominion += 1
    $ lanista_s2_remarks_done = list(lanista_s2_remarks_done) + ["s2_r2"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s3_remark_router:
    lanista_npc "You have sharp eyes. I'll grant you that."
    jump lanista_visit_menu

label lanista_s4_remark_router:
    lanista_npc "You have sharp eyes. I'll grant you that."
    jump lanista_visit_menu

label lanista_s5_remark_router:
    lanista_npc "You have sharp eyes. I'll grant you that."
    jump lanista_visit_menu

label lanista_debt_donate:
    lanista_npc "Generosity. I'll remember which purse it came from."
    jump lanista_visit_menu

label lanista_debt_favor:
    lanista_npc "Bold of you to collect. I don't forget debts either."
    jump lanista_visit_menu

label lanista_program_card:
    lanista_npc "The card changes things. You understand that."
    jump lanista_visit_menu

label lanista_wager_menu:
    lanista_npc "Pick your fighter. Sand doesn't lie."
    jump lanista_visit_menu

label lanista_aftercrowd:
    lanista_npc "The crowd is gone. It's quieter now."
    jump lanista_visit_menu

label lanista_gift:
    lanista_npc "A gift. I won't ask what you want for it."
    jump lanista_visit_menu

label lanista_assess:
    lanista_npc "Measuring me, are you? Go ahead."
    jump lanista_visit_menu

label lanista_s3_gate:
    lanista_npc "You've earned a different kind of conversation."
    $ lanista_s3_gate_fired = True
    jump lanista_visit_menu

label lanista_s4_gate:
    lanista_npc "Things shift between us. You feel it too."
    $ lanista_s4_gate_fired = True
    jump lanista_visit_menu

label lanista_morning_after:
    lanista_npc "Don't read too much into last night."
    jump lanista_visit_menu

label lanista_s5_gate:
    lanista_npc "We are past the point of pretending this is business."
    $ lanista_s5_gate_fired = True
    jump lanista_visit_menu

label lanista_s6_gate:
    lanista_npc "Whatever comes next — you chose it."
    $ lanista_s6_gate_fired = True
    jump lanista_visit_menu

label lanista_ending_resolution:
    lanista_npc "Every arrangement finds its end. This one is ours."
    $ lanista_ending_done = True
    jump tavern_screen

label lanista_check_stage_advance:
    return
