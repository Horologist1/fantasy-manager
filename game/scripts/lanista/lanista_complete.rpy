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
    def profession_is_unlocked(prof):
        """A profession with no 'required_flag' is always shown. Otherwise the named
        store flag must be truthy. Safe for ALL buildings (default: unlocked)."""
        if not hasattr(prof, "get"):
            return True
        flag = prof.get("required_flag")
        if not flag:
            return True
        return bool(getattr(store, str(flag), False))

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

    def lanista_finance_track_complete():
        if lanista_is_dominion_route():
            return int(getattr(store, "lanista_favor_highest_tier", 0) or 0) >= 4
        return int(getattr(store, "lanista_donation_highest_tier", 0) or 0) >= 4

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
    if not lanista_s4_gate_fired and lanista_stage >= 4 and len(lanista_s4_talks_done) >= 3 and lanista_affection >= 80 and lanista_debt_finance_unlocked and lanista_finance_track_complete():
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
    if "s3_t1" not in lanista_s3_talks_done:
        jump lanista_s3_talk_1
    elif "s3_t2" not in lanista_s3_talks_done:
        jump lanista_s3_talk_2
    elif "s3_t3" not in lanista_s3_talks_done:
        jump lanista_s3_talk_3
    else:
        jump lanista_talk_generic

label lanista_s3_talk_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The last torch-bearers have gone. The Arena sits empty under a low moon, the sand raked smooth, the benches a pale ring of nothing. The night's gate-count was thin — you watched the Lanista's jaw set tighter with every bare row, and tonight there were many."
    narrator "You expect to be waved off with the rest. Instead the Lanista says nothing, and the silence is permission to stay."
    lanista_npc "Eleven seasons I've stood in this bowl. Heard it roar. Heard it like this."
    lanista_npc "There's a number the lenders want by the turn of the season. Tonight's take didn't move it. Neither did last night's."
    narrator "The Lanista looks out across the empty tiers — and for the space of a breath, the stillness isn't control. It's a fighter on a ledge, measuring the drop."
    lanista_npc "I have buried fighters and not flinched. The thought of locking that gate for the last time — that one I flinch at. I'll say it once, here, where no one's counting but you."
    menu:
        "\"Then I'll stand here with you. No pitch, no terms. Just here.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "You say nothing else. You only stay — shoulder to the same cold air, watching the same empty seats. The Lanista doesn't thank you. The shoulders ease a fraction, and that is louder than thanks."
            lanista_npc "...No agenda. You came all this way to a dying house and brought no agenda."
            lanista_npc "Stay, then, [_ttl]. The company's better than the arithmetic."
        "\"This place doesn't have to fall. I can move that number — and you'll know who moved it.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            narrator "The Lanista turns from the empty tiers to you, and the ledge-look folds back into something harder. You have offered a rope, and let them see the hand that holds the far end of it."
            lanista_npc "You'd move it. And every season after, I'd hear the sound of your coin under the cheering."
            lanista_npc "...The gate stays open either way. That's the part I can't argue with. I hear you, [_ttl]. I hear exactly what you're offering."
    $ lanista_s3_talks_done = list(lanista_s3_talks_done) + ["s3_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s3_talk_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The whetstone goes quiet. The Lanista works a knot in one shoulder, winces, and then — deciding something — pulls the collar aside to show you the pale rope of scar that runs down from it, thick as a finger, old as the crown that came with it."
    lanista_npc "The Nordmark gave me this one. Third turn of the glass. Had me against the boards, and the blade went in here —"
    narrator "A scarred hand takes yours before you think to offer it, and lays your fingers along the seam of it. The skin is warm, the ridge of it strange under your touch. Neither of you moves for a breath too long to be an accident."
    lanista_npc "— and I kept my feet. Bled half the sand red and kept my feet. That's the whole secret of this craft. You stay standing when the body's begging you to fall."
    menu:
        "\"You've carried enough alone. You don't have to stand for me.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "You don't pull your hand back. You let it rest, gentle, over the worst of the scar — not measuring it now, only holding it. The Lanista goes very still, the way one does at the edge of something that can't be taken back."
            lanista_npc "...That's a dangerous thing to offer a fighter, [_ttl]. We don't know how to be carried. We only know how to stand."
            lanista_npc "But I felt that. I'll not pretend I didn't."
        "\"And you're still standing. Let's see if the strength's still in it.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            narrator "You close your hand on the scarred shoulder and press — testing, challenging, the way one fighter sizes another. The Lanista meets it, muscle going hard under your palm, jaw set, refusing the inch. The air between you draws tight as a bowstring."
            lanista_npc "Still here. Push all you like. This shoulder's outlasted better hands than yours."
            lanista_npc "...Though you've nerve, laying hands on me like that. Most don't dare. I find I don't mind that you did, [_ttl]."
    $ lanista_s3_talks_done = list(lanista_s3_talks_done) + ["s3_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s3_talk_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You've come too many evenings now for it to be business. The Lanista sets the rag down — folds it, even, which is not a thing done idly — and faces you square across the bench."
    lanista_npc "I'm going to name a thing, and you're going to tell me which it is. I've earned plain dealing, even if I've forgotten how to ask for it."
    lanista_npc "You keep turning up. A purse like yours doesn't haunt a failing Arena for the sport. So which is it, [_ttl] — charity, appetite, or leverage?"
    narrator "The question hangs in the lamplight. The Lanista's gaze doesn't waver, and for once there's no armor in it — only the want to know, and the readiness to take any of the three answers like a blow already braced for."
    menu:
        "\"I want you. Not the Arena. You.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "The word lands and the Lanista takes it standing, the way every blow on that sand was taken — but the breath goes out slow, and something behind the eyes that has been clenched for eleven seasons unclenches by a fraction."
            lanista_npc "Me. Not the sand, not the craft, not the crown I used to wear. ...You picked the one answer I had no guard against."
            lanista_npc "Say it again sometime, when I've the nerve to hear it. I'll not forget you said it first, [_ttl]."
        "\"I want both. The Arena and the one who holds it. And I can have both.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 3
            $ lanista_corruption += 1
            narrator "No flinch. The Lanista weighs the answer the way a fighter weighs an opponent who's just shown they fight to win — wary, and not entirely displeased to have found a worthy one."
            lanista_npc "Both. The honest answer and the dangerous one. You want the house and the one standing in it, and you don't see a line between."
            lanista_npc "...Most would dress that up softer. You didn't. I'll give you this — I'd rather a clean blade than a kind lie. Come closer, then, [_ttl]. Let's see what you can hold."
    $ lanista_s3_talks_done = list(lanista_s3_talks_done) + ["s3_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s4_talk_router:
    if "s4_t1" not in lanista_s4_talks_done:
        jump lanista_s4_talk_1
    elif "s4_t2" not in lanista_s4_talks_done:
        jump lanista_s4_talk_2
    elif "s4_t3" not in lanista_s4_talks_done:
        jump lanista_s4_talk_3
    else:
        jump lanista_talk_generic

label lanista_s4_talk_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The Lanista is alone in the armory when you find them, a slip of paper in one hand, the night's card already chalked on the slate behind. One name on that card shouldn't be there, and you both know it — a young fighter with a knee that never set right since the spring, matched against a Nordmark bruiser who will find that knee inside three passes."
    lanista_npc "Don't. Whatever you came to say. I can read a card better than you, and I'm the one who wrote this one."
    narrator "The Lanista sets the slip down with a care that plainly costs something. There is a taste in the room like a blade left out in salt air — and it is on the Lanista's face, not yours."
    lanista_npc "The lenders want bodies the crowd will pay to watch bleed. The boy draws a house. A sound fighter who'd win clean doesn't fill a bench. So I put the lame one on the sand and I call it a card."
    lanista_npc "Eleven seasons I never sold a bout I knew the end of. Tonight I priced one. ...That's the first cut that's gone all the way through. I wanted you to hear it from me, before you heard it from the cheering."
    menu:
        "\"Then I'll carry the weight of it with you. No judgment — just here.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You don't tell the Lanista it was wrong. They already know. You only step in close and take a measure of that weight onto your own shoulders, where they can see you hold it. The breath that goes out of them is ragged at the edge."
            lanista_npc "No sermon. ...I braced for a sermon and you handed me a shoulder instead. I don't rightly know what to do with that."
            lanista_npc "Stay near tonight, [_ttl]. When the boy goes down, I'd sooner not be standing in it alone."
        "\"It was necessary. The gate stays open. And there will be more like it — that's the trade now.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            $ lanista_corruption += 3
            narrator "You name the thing without softening it, and the Lanista hears the truth of it land like a verdict already passed. The slip lies on the bench between you. You do not pick it up. You don't have to. You let them see that you would have written the same name."
            lanista_npc "More like it. You say it plain — the way I couldn't. ...The way I'll have to learn to."
            lanista_npc "You're right, and I hate that you're right, and I'll do it again come next month, and you'll be standing there when I do. That's the shape of us now, [_ttl]. I'm done pretending otherwise."
    $ lanista_s4_talks_done = list(lanista_s4_talks_done) + ["s4_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s4_talk_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You find the Lanista with a cup gone cold and a tally of the last season spread across the bench — not coin this time, but bouts. A scarred finger moves down the column, stopping here and there, the way one counts old wounds to learn which ones still ache."
    lanista_npc "I kept a code once. Plain things. No fixed bouts. No fighter on the sand who can't be carried off it again. No spectacle I'd be ashamed to name to the dead."
    narrator "The finger stops on a line near the bottom. The Lanista doesn't read it aloud. They don't need to. You were there for that one."
    lanista_npc "I told myself the line was the lame boy. That I'd cross that and go no further. I crossed it a month ago, and there's a new line drawn now, further down, and I can already feel the season pushing me toward it."
    lanista_npc "That's how a code dies, [_ttl]. Not in one clean blow. In small honest steps, each one swearing the next is the last. I'm taking stock of how far I've walked. The country out here isn't one I know."
    menu:
        "\"You're still you. A code that bends to keep your people fed isn't a code that broke.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You set a hand flat over the tally, covering the worst of the lines, and make the Lanista look at you instead of the column. There is a long quiet while they weigh whether to let themselves believe you."
            lanista_npc "Bends, not breaks. ...You make it sound like a thing a body survives. Like I might still be standing at the end of it, and still be someone I'd shake hands with."
            lanista_npc "I needed that said, and meant. You meant it — I could tell. I'll hold to it on the nights I can't find my own face in the glass, [_ttl]."
        "\"The code was always a luxury you couldn't afford. Let it go — I'm freeing you of it.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            $ lanista_corruption += 3
            narrator "You sweep the tally aside — bouts, lines, the whole accounting of a conscience — and the Lanista watches the gesture the way a drowning fighter watches a thrown rope land just within reach. Lighter and more dangerous, both in the same breath."
            lanista_npc "A luxury. ...Eleven years I wore it like armor, and you call it a thing I couldn't afford. Damn you for it. You might be right."
            lanista_npc "It is lighter without it. I'll grant you that, and I'll loathe myself for granting it, and I'll keep walking the way you're pointing all the same. You've the weight now, [_ttl]. Mind you carry it better than I did."
    $ lanista_s4_talks_done = list(lanista_s4_talks_done) + ["s4_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s4_talk_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Tomorrow the Arena opens its gates to a spectacle it has never dared before — oiled bodies and thin pretense, more flesh than fight, the card that fills benches and empties the last of the old pride. The slate is chalked. The new banners are sewn. There is nothing left to ready tonight, and so there is only the two of you, the lamp, and a silence stretched to the strain of breaking."
    narrator "The Lanista stands close — closer than the bench requires — and for once makes no pretense that it's about the debt, or the card, or anything but the charge that has built between you across a whole season and has, tonight, nowhere left to go."
    lanista_npc "After tomorrow this house is something else. So am I. Whatever I was holding back for the sake of the fighter I used to be — there's no sense left in holding it."
    menu:
        "\"Then whatever tomorrow makes of this place, we face it together. Starting now.\"":
            $ lanista_devotion += 5
            $ lanista_affection += 4
            narrator "You close the last of the distance and the Lanista lets you — the scarred hands, that have only ever known how to stand and how to strike, learning a third thing now, slow and unsure, which is how to hold. There is no crowd. There is no count. There is only this, and it is enough, and it is theirs to give and yours to keep."
            lanista_npc "Together. ...Eleven seasons I stood in that bowl alone and called it strength. This is better. I'm not too proud tonight to say it's better."
            lanista_npc "Whatever the morning brings, [_ttl], it finds us already standing in it. Shoulder to shoulder. That's the one thing I'll let no lender lay a hand on."
        "\"After tonight, the Arena is mine. And so are you — in every way that matters.\"":
            $ lanista_dominion += 5
            $ lanista_affection += 4
            $ lanista_corruption += 2
            narrator "You say it without a tremor, the way a deal is closed, and the Lanista — who has spent a season being claimed inch by inch — meets the words without flinching, with something near to relief at no longer having to pretend otherwise. The hand that takes yours is a champion's hand, and it yields the grip to you knowing exactly what it yields."
            lanista_npc "Yours. The house, the sand, the name over the gate. ...And the one who built it. You leave nothing unclaimed, do you, [_ttl]."
            lanista_npc "Take it, then. All of it. After tonight there's no line left between the Arena and me, and you'll hold both. I find I'd sooner be held by you than free of you. So be it."
    $ lanista_s4_talks_done = list(lanista_s4_talks_done) + ["s4_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s5_talk_router:
    if "s5_t1" not in lanista_s5_talks_done:
        jump lanista_s5_talk_1
    elif "s5_t2" not in lanista_s5_talks_done:
        jump lanista_s5_talk_2
    elif "s5_t3" not in lanista_s5_talks_done:
        jump lanista_s5_talk_3
    else:
        jump lanista_talk_generic

label lanista_s5_talk_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You find the Lanista at the bench with nothing in their hands — no blade, no tally, no cup. Only a single sheet of heavy vellum, the Governor's wax seal broken at its foot. The room holds the particular stillness that comes before a bout one fighter already knows the end of."
    lanista_npc "Sit down, [_ttl]. You'll want to be sitting for this number."
    narrator "They slide the vellum across the wood. You don't need to read the whole of it. The figure at the bottom does the talking, and beside it a date — a fortnight off — and the Governor's plain word for what happens when it goes unmet. The license. The gates. The name over the door. Struck from the rolls."
    lanista_npc "There it is. The real number. Not the piece of it I've fed you all season to keep your face from doing what it's doing now."
    lanista_npc "A fortnight. Pay the purse in full, or the Governor takes the Arena off the rolls and turns eleven seasons into an empty stable yard. I've cut my way out of worse corners than this. ...No. That's the old lie, and I'm done telling it. There's no worse corner than this one. This is the last of the sand."
    menu:
        "\"Then we stand in it together. I'm not walking out that gate — whatever the number is, it's ours now.\"":
            $ lanista_devotion += 5
            $ lanista_affection += 4
            narrator "You don't flinch from the figure and you don't flinch from them. You only set your hand flat on the vellum, over the worst of it, and stay — close enough that they have to look at you instead of the date. The breath that leaves them shakes on the way out, the way a held guard shakes when it finally drops."
            lanista_npc "Ours. ...You look at the number that ends me and you call it ours. Nobody shares a sinking, [_ttl]. They get clear of it."
            lanista_npc "You're not getting clear. I can see that you mean it, and I've no armor left to argue. A fortnight, then — and you in it with me. That's more than I had an hour ago. That's more than I've had in eleven years."
        "\"The debt was mine the day I started covering it. This doesn't end on the Governor's date. It ends how I decide it ends.\"":
            $ lanista_dominion += 5
            $ lanista_affection += 3
            narrator "You pick the vellum up, read the figure once, and set it down again without a tremor — the way a buyer prices a thing already half-owned. The Governor's date means nothing in your hand. You let the Lanista watch you understand that, and watch you decide it changes nothing you don't allow it to."
            lanista_npc "How you decide. ...The Governor sets a date on my whole life, and you wave it off like a bad call from the stands. The maddening part is you've the standing to do it."
            lanista_npc "It's your debt. It's been your debt. I stopped owning it somewhere back there and never marked the day. So decide, then. I've nothing left to lay on the sand but the deciding, and you've taken even that. Tell me how this ends, [_ttl]. I'll stand where you put me."
    $ lanista_s5_talks_done = list(lanista_s5_talks_done) + ["s5_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s5_talk_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The high shelf behind the rack is bare. The victor's wreaths, the bronze tokens, the grey-dusted glory of fighters who mattered — gone, sold off in a lot to a collector who paid in the kind of coin a fortnight demands. The Lanista stands looking at the empty board where eleven seasons used to sit."
    lanista_npc "Sold the trophies this morning. Didn't dent the number. Funny thing — it didn't hurt going. I thought it would. I think I'd used it all up grieving on the road to the buyer's door."
    narrator "They turn, and the look on the hard face is one you haven't seen there — not the iron, not the dry cut of the wit. Something quieter. A fighter standing over a body and recognizing the face."
    lanista_npc "There was someone who held this place once. Eleven seasons unbeaten in the manner that mattered — never a sold bout, never a fighter on the sand who couldn't be carried off it. That one would have spat on the cards I run now. Would have put a fist through the new banners."
    lanista_npc "That one's dead, [_ttl]. I'm what's standing in the armor after. And I miss them. The way you miss a friend you had to leave on the field, because carrying them would have got you both killed."
    menu:
        "\"It wasn't a fall. It was survival. And I still see the fighter under the armor — they're not as gone as you think.\"":
            $ lanista_devotion += 5
            $ lanista_affection += 4
            narrator "You take the hard jaw in your hand and make them hold your eye, the way they once reset a recruit's grip — patient, exact. You tell them you see it. Not the lanista who sells the sand. The fighter underneath, who hated every cut it took to keep the house standing. The breath they let go is ragged at its very edge."
            lanista_npc "Still there. ...You say it like you've laid eyes on them. Like they didn't go in the ground with the code."
            lanista_npc "Maybe that's the cruelest mercy you've shown me yet — telling me the one I buried still draws breath under all this. I'll not unhear it now. I'll go looking for that face in the glass, on the bad nights. And I'll be looking because of you, [_ttl]."
        "\"The code was dead weight from the start. You're lighter without it — and you know exactly who cut it loose.\"":
            $ lanista_dominion += 5
            $ lanista_affection += 3
            $ lanista_corruption += 2
            narrator "You don't grieve the champion with them. You bury the body plainly, and you name the gravedigger. The code was a stone they'd carried eleven seasons because no one had ever told them to set it down. You told them. You watch the truth of it land — and watch the awful relief come in behind it, the relief they will hate themselves for feeling."
            lanista_npc "Dead weight. ...You'll stand over the corpse of the only thing I was proud of and call it a load I'm well shut of. And the hell of it is the load's gone and I can breathe."
            lanista_npc "You cut it loose. I'll not pretend it was my hand on the knife — it was yours, and I held still for it. Lighter. Freer. Worse, by every measure that one would have used. But that one's gone, and you're here, and I'd sooner be your creature than their ghost. There's the bottom of me, [_ttl]. You dug it up."
    $ lanista_s5_talks_done = list(lanista_s5_talks_done) + ["s5_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s5_talk_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The fortnight has burned down to its last days. There's nothing left to sell, no card clever enough, no crowd large enough. The two of you stand in the empty bowl with the Governor's date hanging over it like a blade on a fraying cord — and you came tonight not to talk around the thing, but to make your move. The Lanista reads it in your face before you've said a word."
    lanista_npc "You've the look of someone who's decided something. I've faced that look across a sand from better fighters than the Governor. Say it, [_ttl]. I'd rather take it standing."
    menu:
        "\"I'll save the Arena. No conditions, no ledger. But I want you — in my life. Not as a transaction. As the thing it turns out I can't do without.\"":
            $ lanista_devotion += 8
            $ lanista_affection += 5
            narrator "You say it plainly, and you say the hard half of it — that the coin comes free and clear, that there's no hook hidden in it, that the one thing you're asking for is the one thing a debt could never buy and you'd never try to. The Lanista stands very still, the way they stand when a blow lands that the body hasn't decided yet how to feel."
            lanista_npc "No conditions. You'll lift the whole weight off this house and ask nothing back but — me. Not the Arena. Not the sand. Me."
            lanista_npc "Eleven seasons I've been a thing that gets bought, traded, leaned on, collected. You're the first to want the part of me that was never for sale. ...Yes. The answer's yes, before you've finished asking, and it frightens me how little I had to weigh it. Save the house if you like, [_ttl]. But know it was the second thing I'd have said yes to. You were the first."
        "\"I can make all of it disappear. The number, the Governor, the date — gone by morning. You know what it costs. You've always known.\"":
            $ lanista_dominion += 8
            $ lanista_affection += 5
            narrator "You don't list the price. You don't have to. It's been understood between you for a season, in every yielded inch and every debt called in — the last fortress, the one thing not yet formally handed over. You let the silence carry it, and you watch the Lanista arrive at the same place you already stand."
            lanista_npc "Disappear. By morning. You could, too — I've seen the length of your reach. One word from you and the Governor's date is so much ash, the purse is so much ash, and the only thing left standing in the wreck of it is the bill."
            lanista_npc "And I know the figure on that bill. It's been written between us since the first count came up short. ...Pay it. I'll meet it. Take the number off my life and put it on my body, where it's been heading all along. I'd sooner owe the whole of myself to you than a single copper to them. Make it disappear, [_ttl]. And come collect."
    $ lanista_s5_talks_done = list(lanista_s5_talks_done) + ["s5_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
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
    if "s3_r1" not in lanista_s3_remarks_done:
        jump lanista_s3_remark_1
    elif "s3_r2" not in lanista_s3_remarks_done:
        jump lanista_s3_remark_2
    else:
        jump lanista_talk_generic

label lanista_s3_remark_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Between bouts the Lanista sits and winds a strip of linen around one fist — over the knuckles, between the fingers, the wrap of a fighter readying for the sand. There's no fight tonight. The hands haven't thrown a real blow in years. They wind the tape anyway, slow and exact, eyes somewhere far off."
    narrator "\"Old habit dies hard,\" you say quietly."
    lanista_npc "The hands remember before the head does. I wrap them and for a moment I'm twenty and unbeaten. ...Then I look down and I'm not. But the moment's worth the linen."
    $ lanista_affection += 1
    $ lanista_devotion += 1
    $ lanista_s3_remarks_done = list(lanista_s3_remarks_done) + ["s3_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s3_remark_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The night's coin comes up from the gate in a strapped wooden box. The Lanista doesn't open it, doesn't count it aloud — only sets a hand flat on the lid and reads its weight the way a fighter reads an opponent's stance, knowing the answer before the latch is ever thrown. The jaw tells you the number. The mouth says nothing."
    narrator "\"You already know what's in it,\" you observe."
    lanista_npc "To the copper. I've felt a winning house and a losing one through that lid for eleven years. Tonight's light. ...No sense saying so. The box doesn't argue back, and neither do I."
    $ lanista_affection += 1
    $ lanista_dominion += 1
    $ lanista_s3_remarks_done = list(lanista_s3_remarks_done) + ["s3_r2"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s4_remark_router:
    if "s4_r1" not in lanista_s4_remarks_done:
        jump lanista_s4_remark_1
    elif "s4_r2" not in lanista_s4_remarks_done:
        jump lanista_s4_remark_2
    else:
        jump lanista_talk_generic

label lanista_s4_remark_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The champion's belt is off its peg for the first time you've seen it. The Lanista works oil into the old leather with slow circles of a rag, coaxing the dark suppleness back into it, thumbing the bronze plate until it answers the lamplight. Tended like a thing that matters. And when it's done, set down on the bench — not buckled on."
    narrator "\"You've brought it back to life,\" you say, \"and you still won't wear it.\""
    lanista_npc "Oiling it I can do. It's earned that much, whatever I've let myself become. Wearing it is another matter — that's a claim, and I'm not the fighter who could make it now. Maybe I'm only keeping it ready. For whoever can."
    $ lanista_affection += 1
    $ lanista_devotion += 1
    $ lanista_s4_remarks_done = list(lanista_s4_remarks_done) + ["s4_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s4_remark_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Workers haul new banners up the gate-poles — vast painted things, all bright dye and bared skin, a far cry from the plain crossed-swords sigil that flew there eleven years. They sell a promise of flesh, not steel, and the crowd already gathering below points up at them and grins. The old sigil lies folded in the dust by the wall, where someone set it down and no one thought to lift it."
    narrator "\"New colors over the gate,\" you observe."
    lanista_npc "They draw a bigger house. The crossed swords drew respect, and respect doesn't satisfy a lender. ...Don't look for me to like it. Look for me to count the take after. That's the trade I made, and I'll keep my eyes on the only part of it that's still mine to keep."
    $ lanista_affection += 1
    $ lanista_dominion += 1
    $ lanista_corruption += 1
    $ lanista_s4_remarks_done = list(lanista_s4_remarks_done) + ["s4_r2"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s5_remark_router:
    if "s5_r1" not in lanista_s5_remarks_done:
        jump lanista_s5_remark_1
    elif "s5_r2" not in lanista_s5_remarks_done:
        jump lanista_s5_remark_2
    else:
        jump lanista_talk_generic

label lanista_s5_remark_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A fresh notice is nailed to the great gate, square in the center where every fighter and every patron must pass beneath it. The Governor's seal sits heavy at its foot — red wax and a pressed crest, official as a verdict already passed. The crowd reads it on the way in and lowers their voices. The Lanista hasn't torn it down. They've left it where it bites hardest, the way one leaves a wound undressed to keep the lesson of the blow."
    narrator "\"You could take that down,\" you say."
    lanista_npc "And the Governor nails up another by noon, and I've taught the whole house I can be made to flinch. No. Let it hang. Let them all read what I'm fighting. A bout's only worth the watching when the crowd knows what's on the sand."
    $ lanista_affection += 1
    $ lanista_devotion += 1
    $ lanista_s5_remarks_done = list(lanista_s5_remarks_done) + ["s5_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s5_remark_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Past midnight the lamps should be dead and the bowl empty. Instead there's the dry scuff of footwork on sand, the same combination drilled over and over to nothing. The Lanista is alone at the center, stripped to the linen, throwing blows at an opponent eleven years in the ground — not training. Wearing the body out past the point where the mind can keep talking."
    narrator "\"You're not sleeping,\" you observe."
    lanista_npc "Sleep's a luxury, and you've watched me learn what I can't afford. The number sits up for me whether I lie down or not. Better to meet it on my feet, drilling, than on my back staring at the dark. The sand never lies to me. Some nights that's worth more than rest."
    $ lanista_affection += 1
    $ lanista_dominion += 1
    $ lanista_s5_remarks_done = list(lanista_s5_remarks_done) + ["s5_r2"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_debt_donate:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    menu:
        lanista_npc "You came to cover what I can't. I won't pretend that sits well."
        "Cover a creditor's note. (800 coins)" if money >= 800:
            $ money -= 800
            $ lanista_devotion += 2
            $ lanista_affection += 3
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 1)
            narrator "A creditor's note, paid. No ceremony."
            lanista_npc "One less paper on my desk. Don't make it a thing."
        "Clear the month's interest. (1600 coins)" if money >= 1600:
            $ money -= 1600
            $ lanista_devotion += 3
            $ lanista_affection += 4
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 2)
            narrator "The month's bleeding slows by a measure."
            lanista_npc "Interest cleared. This buys the sand another month. That's all."
        "Buy back a lien. (2800 coins)" if money >= 2800:
            $ money -= 2800
            $ lanista_devotion += 4
            $ lanista_affection += 5
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 3)
            narrator "A lien, lifted. One hand off the Arena's throat."
            lanista_npc "You bought back the lien. I counted the papers. Don't expect me to say more."
        "Settle the principal. (4000 coins)" if money >= 4000:
            $ money -= 4000
            $ lanista_devotion += 5
            $ lanista_affection += 6
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 4)
            narrator "Principal settled. The columns run clean for the first time in years."
            lanista_npc "The books are clear. ...I'll remember who did that, and I'll never say it plainly. Consider it said now."
        "Not today.":
            jump lanista_visit_menu
    $ lanista_debt_finance_last_day = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_debt_favor:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    menu:
        lanista_npc "You're here to call the markers. I know the ledger as well as you do."
        "Call in a marker. (800 coins)" if money >= 800:
            $ money -= 800
            $ lanista_dominion += 2
            $ lanista_affection += 2
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 1)
            $ lanista_corruption = min(100, lanista_corruption + 1)
            narrator "A marker called, the Lanista's name off a note — yours on instead."
            lanista_npc "One marker. You're counting. So am I."
        "Put your name on the note. (1600 coins)" if money >= 1600:
            $ money -= 1600
            $ lanista_dominion += 3
            $ lanista_affection += 3
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 2)
            $ lanista_corruption = min(100, lanista_corruption + 1)
            narrator "Your name goes on the paper. The Lanista sets the pen down without looking at it."
            lanista_npc "My debt, your name. I know the shape of what that means."
        "Buy the lien yourself. (2800 coins)" if money >= 2800:
            $ money -= 2800
            $ lanista_dominion += 4
            $ lanista_affection += 4
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 3)
            $ lanista_corruption = min(100, lanista_corruption + 1)
            narrator "The lien transfers. The Arena owes you something it won't forget."
            lanista_npc "You own the lien. Say it plainly — I'm listening."
        "Own the debt outright. (4000 coins)" if money >= 4000:
            $ money -= 4000
            $ lanista_dominion += 5
            $ lanista_affection += 5
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 4)
            $ lanista_corruption = min(100, lanista_corruption + 1)
            narrator "The debt is yours. The Arena, to the last nail, answers to your ledger now."
            lanista_npc "Outright. ...You've the whole column. I'll not pretend you didn't earn the right to hold it."
        "Not today.":
            jump lanista_visit_menu
    $ lanista_debt_finance_last_day = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_program_card:
    if lanista_card_tier >= 4:
        lanista_npc "There's nothing left of the old card to change, [player_title]. The sand is yours. It's already forgotten what it used to be."
        jump lanista_visit_menu
    jump expression "lanista_card_tier_{}".format(lanista_card_tier + 1)

label lanista_card_tier_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "You find the Lanista at the slate, chalking the night's pairings — clean matches, fighter against fighter, the way the craft says they should be. You lay your idea over the top of it. Call them Crowd Pleasers. Bouts built like stories: the slow start, the near-loss, the turn at the end the benches will come to their feet for. Not lies. Shaped truths. A fight that knows where it's going."
    lanista_npc "Shaped truths. You've a coin-counter's gift for naming a thing so it stops smelling like what it is."
    lanista_npc "A bout isn't a tale you tell, [_ttl]. It's two people and the sand and whatever's true between them. You start writing the turn at the end, you're not a Master of the Sands anymore. You're a puppeteer."
    narrator "But [_their] eye drifts to the benches as [_they] says it — half of them bare wood, no body to warm them — and the rest of the sentence dies in [_their] throat."
    menu:
        "\"You're not writing the ending. You're framing the fight so the crowd feels what you already feel watching it.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "You don't argue the code. You tell the Lanista the truth — that [_they] has stood in that bowl eleven seasons because a good bout is the finest story there is, and a Crowd Pleaser only hands the benches the eyes to see it. Something shifts behind the scarred face. Reluctant. Real."
            lanista_npc "The slow start. The turn at the end. I've felt every one of those without ever once arranging them."
            lanista_npc "And now you've put it in my head that arranging them might be a kindness more than a sin. Damn you, [_ttl]. I want to try it. That's the part that worries me."
        "\"The benches are bare. Crowd Pleasers fill them. That's the whole of the arithmetic, and you've already done it.\"":
            $ lanista_dominion += 3
            $ lanista_corruption += 2
            narrator "You don't dress it up. You set the empty benches and the lenders' number side by side and let the Lanista count, because [_they] is the only one who can. The jaw works. The sum comes out the way it always does when you hold the chalk."
            lanista_npc "Bare benches don't pay the iron-smith. I know the column, [_ttl]. I knew it before you said it."
            lanista_npc "So we shape the bouts. We give them their Crowd Pleasers. And I'll name the price out loud so neither of us pretends it was free — tonight's the last night I stand here and call every fight honest. Mark it. I do."
    $ lanista_card_tier = max(lanista_card_tier, 1)
    $ lanista_corruption = min(100, lanista_corruption + 5)
    $ lanista_card_last_day = calculate_total_days()
    # tier 1: the first scratch on the code — no profession unlock
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_card_tier_2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "You come back with the next rung already drawn. Pin-up Barbarians. The fighters stripped to half their armor and less — furs cut for the eye, skin oiled to catch the torchlight, the bout dressed up as much for wanting as for winning. You've seen how the front rows lean when a champion's shoulder comes bare. You propose the Arena lean back."
    lanista_npc "Half their armor. ...You know what armor is for, [_ttl]. It's the difference between a scar and a grave."
    lanista_npc "And now you'd have me cut it away so the front row can ogle the dying. That's a different country than rigging a turn at the end. That's selling the flesh, not the fight."
    narrator "Yet [_they] doesn't say no. [_They] turns it over the way [_they] reads a map of country [_they] already suspects [_they] will have to cross."
    menu:
        "\"Half-clothed isn't half-skilled. Let them be beautiful and lethal both — and own that you'd watch too.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You make the Lanista admit the thing under the code — that a body which has fought eleven seasons is worth looking at, and there's no shame in a crowd that knows it. The flush that climbs the scarred neck isn't all anger. [_They] catches you seeing it, and for once doesn't look away."
            lanista_npc "Beautiful and lethal. ...You'd dress my fighters like that and dare the benches to forget they can kill."
            lanista_npc "I'd watch. There — the quiet part, the way you're always pulling it out of me. Pin-up Barbarians. Gods help me, I can already see how I'd light it, [_ttl]."
        "\"The body sells what the bout can't. You need the purse, and the purse wants skin. Name it and bank it.\"":
            $ lanista_dominion += 4
            $ lanista_corruption += 3
            narrator "You put it to the Lanista as a transaction, because that's what it is, and [_they] respects the lack of perfume on it even as it costs [_them]. [_They] does the sum — the skin against the silver, the dignity against the debt — and the answer is the answer."
            lanista_npc "Skin sells. I'd be a fool to pretend the books say otherwise. They don't."
            lanista_npc "So we oil them and strip them and call it Pin-up Barbarians. And here's the price, named plain — a year ago I'd have broken the jaw of anyone who asked it. Now I draw the costume myself. You bought that, [_ttl]. Don't think I've forgotten the coin it came on."
    $ lanista_card_tier = max(lanista_card_tier, 2)
    $ lanista_corruption = min(100, lanista_corruption + 8)
    $ lanista_card_last_day = calculate_total_days()
    $ lanista_pinup_unlocked = True
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_card_tier_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "The next format you bring has teeth. Oil & Chains. The bouts fought to the submission and held there — the pin drawn out, the yield made into the show, irons and oil and the slow theater of one body bending another for the benches to feast on. Not a fight that ends in a winner. A fight that ends in a surrender, and lingers on it."
    lanista_npc "Hold the pin. Draw out the yield. ...You're not describing a bout anymore, [_ttl]. You're describing the one thing I've spent my life teaching fighters never to do — hand the crowd the surrender as the prize."
    narrator "[_They] turns a length of chain over in [_their] hands as [_they] speaks — testing the weight of it, the link of it, the way [_they] tests everything before [_they] decides whether [_they] can live with it."
    menu:
        "\"A surrender given on purpose, beautifully, is the bravest thing in that bowl. Make it art — with me.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You don't let the Lanista call it degradation. You call it choreography — a yield offered with the whole body, harder to perform than any clean kill — and you tell [_them] no one alive could stage it like [_they] could. The chain stills in [_their] hands. [_They] believes you. Worse — [_they] wants to be right about it."
            lanista_npc "Art. You'd call Oil & Chains art and make me half believe it, standing here."
            lanista_npc "A surrender, given. Performed. ...I know how to make a body yield, [_ttl] — I've just never made it beautiful on purpose. With you behind it, I think I could. That should frighten me more than it does."
        "\"You know how to make a body yield. The crowd will pay to watch it. Do the math and put the irons on.\"":
            $ lanista_dominion += 4
            $ lanista_corruption += 3
            narrator "You set the ledger against the Lanista's pride one more time, and this time there's barely a contest left in it. [_They] has been doing this arithmetic for a whole season now, and [_they] knows the carry by heart. The chains, the oil, the held surrender — it all comes out in coin, and the coin is what keeps the gate."
            lanista_npc "Make a body yield for silver. I've sold a great many things to keep this sand. Now I sell the yielding itself."
            lanista_npc "Oil & Chains, then. And your price, spoke plain — there used to be a line I'd not cross for any purse, and you've just watched me chalk over the last of it. I yield the bout, [_ttl]. I always tell you which part I'm yielding. That's the dignity I've got left, and I keep it."
    $ lanista_card_tier = max(lanista_card_tier, 3)
    $ lanista_corruption = min(100, lanista_corruption + 10)
    $ lanista_card_last_day = calculate_total_days()
    $ lanista_oilchains_unlocked = True
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_card_tier_4:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "There's one rung left and you both know its name before you say it. The Spectacle. Not a bout dressed as wanting, not a yield held for the eye — the whole thing given over, combat and flesh fused into one show with no pretense of sport left standing in it. The last card. The one the old Lanista would have burned the Arena down before allowing."
    lanista_npc "The Spectacle. You needn't pitch it, [_ttl]. I've watched it coming since the night I chalked a lame boy's name on this slate and called it a card."
    lanista_npc "There's no code left to scrape against. We sanded it away a rung at a time, you and I. What you're asking for now isn't a compromise. It's the place all the compromises were always walking toward."
    narrator "[_They] looks at the slate — clean, waiting — and then at you, and there's no fight left in it. Only the question of how [_they] gives the last of it away."
    menu:
        "\"Then we build something new on the bones of the old code. The Spectacle, made by us, believed in by us.\"":
            $ lanista_devotion += 5
            $ lanista_affection += 4
            narrator "You don't mourn the code with the Lanista. You hand [_them] a new thing to stand for — a house that worships the body and the bout as one, made beautiful on purpose, made together. The grief goes out of the scarred face and something fierce and converted comes up behind it. [_They] doesn't yield to The Spectacle. [_They] takes up its banner."
            lanista_npc "Believed in. ...Eleven seasons I served a code, and you've gone and handed me a faith instead."
            lanista_npc "The Spectacle. Ours. I'll build it so fine the dead I swore my old oath to would forgive me for it — because there's nothing shameful in worship, [_ttl], and that's what this will be. I see it now. I see all of it. Lead on."
        "\"The code's gone. The Arena's mine, and The Spectacle is what it stages now. Say the price and we're done.\"":
            $ lanista_dominion += 5
            $ lanista_corruption += 3
            narrator "You don't pretend it's a partnership. You state it like a deed of sale, because the Lanista has earned a creditor who won't lie to [_them]. [_They] hears the whole of it — the house, the sand, the last of the code — pass over the bench into your column, and [_they] receives it standing, the way a champion takes the count [_they] can't beat."
            lanista_npc "The Arena stages what its owner says it stages. And its owner is you. I'll not insult either of us by arguing the obvious."
            lanista_npc "The Spectacle, then, and the final price named out loud — there's nothing left of the old card to defend, because there's nothing left of the old code to defend it with. You've the whole column, [_ttl]. The sand. The show. The one who runs it. I yielded it clear-eyed, every inch. Remember that I named each one."
    $ lanista_card_tier = max(lanista_card_tier, 4)
    $ lanista_corruption = min(100, lanista_corruption + 12)
    $ lanista_card_last_day = calculate_total_days()
    $ lanista_spectacle_unlocked = True
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_wager_menu:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _corrupt_on_win = 0
    menu:
        lanista_npc "Put coin on the sand. Back your read — if it holds, you walk out twice what you brought."
        "Bankroll an exhibition comeback. (Stake 500)":
            $ _won, _delta = lanista_wager(500, 0.6)
            jump lanista_wager_resolve
        "Wager on a grudge match. (Stake 1500)":
            $ _won, _delta = lanista_wager(1500, 0.5)
            jump lanista_wager_resolve
        "Sponsor a beast-fight spectacle. (Stake 3000)" if lanista_card_tier >= 2:
            $ _corrupt_on_win = 3
            $ _won, _delta = lanista_wager(3000, 0.4)
            jump lanista_wager_resolve
        "Back out.":
            jump lanista_visit_menu

label lanista_wager_resolve:
    $ lanista_wager_last_day = calculate_total_days()
    if _won:
        $ lanista_affection += 2
        $ lanista_corruption = min(100, lanista_corruption + int(getattr(store, "_corrupt_on_win", 0) or 0))
        narrator "The crowd finds its throat. Your fighter earns the sand and your stake comes back twice over — the Lanista's eye cuts to you, measuring, as if the result has said something about you worth recording."
        lanista_npc "Your eye held, [_ttl]. The sand said so, and the sand doesn't flatter. Come back when the luck's still on you."
    else:
        $ lanista_dominion += 1
        narrator "The sand drinks the bout and takes your coin with it. The Lanista watches you absorb the loss from across the yard — no pity in it, and no contempt either. Just the flat attention of someone who has stood on the losing side of the count and knows there's nothing to say about it."
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd:
    $ _total_days = calculate_total_days()
    $ lanista_aftercrowd_last_day = _total_days
    $ _tier = 1
    if lanista_card_tier >= 4 or lanista_corruption >= 60:
        $ _tier = 4
    elif lanista_card_tier >= 3 or lanista_corruption >= 40:
        $ _tier = 3
    elif lanista_card_tier >= 2 or lanista_corruption >= 20:
        $ _tier = 2
    $ lanista_aftercrowd_tier = _tier
    $ _vi = int(getattr(store, "lanista_aftercrowd_variant_index", 0) or 0)
    $ store.lanista_aftercrowd_variant_index = _vi + 1
    call lanista_restore_visit_scene from _lanista_restore_aftercrowd
    if lanista_is_devotion_route():
        jump expression "lanista_aftercrowd_dev_t{}".format(_tier)
    else:
        jump expression "lanista_aftercrowd_dom_t{}".format(_tier)

label lanista_aftercrowd_dev_t1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "The last torch is doused and the gate barred, and the Lanista comes to find you in the empty dark before you can think to leave — crossing the cooling sand the way [_they] crosses to a thing [_they] wants and has stopped pretending not to."
    else:
        narrator "The count is locked away and the great bowl stands empty, and [_they] catches your wrist as you turn to go — not hard, only sure, the grip of someone who has decided the night isn't finished with you yet."
    lanista_npc "Stay a moment. The sand keeps better company when you're in it, [_ttl]. I've stopped being ashamed to say so."
    $ _bust = "images/lanista/lanista_{}_kiss.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Then [_their] mouth is on yours, unhurried, the heat of the whole night's work still coming off [_them]. Hands settle at your back and hold — nothing unfastened, no hurry in it, only the long warm press of a fighter who has learned [_they] is allowed this."
    lanista_npc "There. That's the thing I bar the gate for now. Not the coin. This. Come back when the days have turned, [_ttl] — I'll be here."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd_dev_t2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "The gate's barred and the lamps are guttering, and the Lanista doesn't wait for the dark to do the asking tonight — [_they] crosses to you with the night's heat still on [_them] and hands that already know the way."
    else:
        narrator "You're barely alone before [_they] has you backed against the cool stone of the tunnel mouth, the want plain on [_them] now, no season of caution left to spend on hiding it."
    lanista_npc "I've thought of this the whole damned card, [_ttl]. Counting the rounds till the gate could close on the rest of the world."
    $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "[_Their] mouth finds your throat as [_their] hands work the fastenings of your clothes loose, sure and unhurried, and you return the favor — the worn leather and linen coming open under your fingers, baring the banked heat of a body that no longer braces when you touch it."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You learn each other by hand and mouth in the dark, the last of the cloth fallen away, every breath shared and shaking — and [_they] holds you both to the edge of more and, with a low rough laugh, no further."
    lanista_npc "Not all of it tonight. ...Let me keep the wanting a while longer, [_ttl]. It's a finer thing than I knew, the wanting. Come back, and we'll spend the rest."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd_dev_t3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "The gate is barred and the count is done, and [_they] draws you down onto the bench in the warm dark without a word wasted — the question that hovered the first night long since answered, and answered yes."
    else:
        narrator "The empty bowl holds nothing but the two of you and the guttering lamps, and [_they] pulls you in close, the night's heat still on [_them], wanting you with none of the old careful hesitation."
    lanista_npc "No need to be clear-eyed about it anymore, [_ttl]. I know the shape of what this is. Come here."
    $ _scene = "s4_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "He takes you down into the warm dark without the old hesitation now, and when he sinks into you it is sure and slow and known, his mouth at your throat spending the low sounds he once would have died before letting you hear."
    elif lanista_gender == "male":
        narrator "He gathers you under him like a thing he has finally stopped bracing to lose, and when he moves into you it is unhurried and certain, that first night's disbelief worn down now to a deep and wordless ease."
    elif _pt == "lord":
        narrator "She pulls you down to her with none of the old caution, the iron long since set aside between you, and when you move into her she takes you with a soft broken breath and arms that lock you close, holding the way she's learned she's allowed to hold."
    else:
        narrator "She draws you to her in the cooling dark and lets you learn her all over again, the proud body arching up into your hands without a trace of the old flinch, every sound she gives you familiar now and freely spent."
    lanista_npc "Stay till the lamp gutters, [_ttl]. We've the dark, and no one in it but us. It's grown to be my favorite hour of the whole count."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd_dev_t4:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "The gate is barred before the last of the crowd has cleared the road, and [_they] is on you the moment it falls — no patience left to spend, no part of [_them] still kept back, the whole long armored season of [_their] life burned down to wanting you and not caring who could see it."
    else:
        narrator "[_They] doesn't wait for the dark or the quiet tonight. [_Their] hands are in your clothes before the torches gutter out, the hunger plain and shameless on [_them], a fighter who has forgotten entirely how to brace."
    lanista_npc "I've nothing left to keep behind the guard, [_ttl]. You took it all, and I let you, and I'd let you again tonight and every night the gate will bar. Come here. All of it. Now."
    $ _scene = "aftercrowd"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_aftercrowd_{}_{}_{}.png".format(_route, _g, _t),
            "images/lanista/cg_aftercrowd_{}_{}.png".format(_route, _g),
            "images/lanista/cg_aftercrowd_{}.png".format(_route),
            "images/lanista/cg_s4_gate_{}_{}.png".format(_route, _g),
            "images/lanista/cg_s4_gate_{}.png".format(_route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "There is nothing held back in him tonight — no armor to lower because it is long gone, gladly. He takes you with his whole weight and his whole want, mouth open against your skin, spending every sound he has into the dark of the empty bowl, a man wholly undone and no longer frightened to be seen it."
    elif lanista_gender == "male":
        narrator "He comes apart over you without a shred of the old fear, moving into you deep and greedy and unguarded, his breath wrecked against your hair, every season of iron burned clean away in the heat of having you and meaning to keep on having you."
    elif _pt == "lord":
        narrator "She gives you all of it now, every gate flung wide — pulling you into her with a hunger she stopped hiding seasons ago, breaking open under you with a cry she no longer bites back, arms locked across your back as if she means never to let the dark take you from her."
    else:
        narrator "She abandons herself to you completely, the proud body that once kept the world a blade away now arching greedy and shameless into every touch, taking you and being taken with a low unguarded cry, every wall she ever owned long since handed willingly into your keeping."
    lanista_npc "I don't brace for the morning anymore. ...You did that, [_ttl]. Stay. There's nothing left in me that wants you gone — there hasn't been for a long while now."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd_dom_t1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "You send word down the tunnel after the gate is barred, and the Lanista comes — unhurried, composed, the cold dignity worn like the day's armor still buckled on. [_They] knows precisely why [_they] was summoned. [_They] comes anyway."
    else:
        narrator "The benches are empty and the night's coin is yours by every reckoning that matters. You do not rise to leave. You wait, and the Lanista crosses the sand to you, because both of you know that is how this goes now."
    lanista_npc "You've a use for me past the count, then. ...Say it plain, [_ttl]. I'll not be summoned for nothing."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You take the proud jaw in your hand and bring that cold mouth to yours, and [_they] yields it the way [_they] yields everything to you — without a sound of surrender, the composure flawless, the breath beneath it already gone uneven."
    lanista_npc "...There. You've collected. Keep your hands warm, [_ttl] — the body's the only part of me that ever answers you first. Go on. Come back when the days have turned."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd_dom_t2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "You keep [_them] back a moment when the gate is barred, a hand flat on [_their] chest, and the Lanista holds the cold composure while you take [_their] measure at your leisure — both of you aware the stillness is a thing [_they] offers, not a thing [_they] feels."
    else:
        narrator "The night's coin is counted and yours, and you've a mind to collect the rest. [_They] comes when you bid [_them], chin level, the champion's dignity buckled on — and underneath it, already, the body that has stopped keeping its secrets from you."
    lanista_npc "Collecting again. ...Go on, then, [_ttl]. Take your measure of me. I'll keep my face. We both know that's all I'll manage to keep."
    $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You strip the worn leather from [_them] slow, [_their] eyes never leaving yours, the proud line of [_them] conceding nothing aloud — while the body under your hands answers every touch before the pride can think to forbid it."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Bared, [_they] holds the champion's stillness to the last, breath gone uneven, the want coming off [_them] in waves [_they] will not name — and you take [_them] to the brink of more and stop there, deliberate, leaving the wanting to do its work."
    lanista_npc "...You'd leave it there. Cruel, [_ttl] — and well-judged. You know I'll come to the gate sooner for it. Go. I'll be counting the days I'll not admit to counting."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd_dom_t3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "The gate is barred and the house is yours, the both of you long past pretending otherwise. You bid the Lanista to you, and [_they] comes with the cold dignity intact and the body beneath it already half lost to you."
    else:
        narrator "You take the proud face in your hand the way you did at the first gate — but there is no stopping now, no terms to set, only the familiar reckoning. [_They] meets your eye, level and composed, a fighter who chose this ground seasons ago and returns to it still calling it a loss."
    lanista_npc "You'll have what you came for. ...You always do, [_ttl]. Spare me the asking. Take it."
    $ _scene = "s4_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "He keeps the cold stare to the last, but his body has long stopped pretending — hard and ready before you've half undressed him, and when you set the pace the iron in his face holds while everything under it gives, breath by ragged breath, the surrender practiced now and still never once spoken."
    elif lanista_gender == "male":
        narrator "The composure stays nailed in place, the proud jaw unmoving, and it fools neither of you anymore — not with him already wanting under your hands, his breath tearing loose the instant you take him and set the rhythm, the bout lost on the same silent terms as every time before."
    elif _pt == "lord":
        narrator "She gives you the champion's stillness out of habit now, chin high, conceding nothing aloud, and her body answers you before the pride can object — slick and ready, clenching and shuddering under the pace you set while not one word of it crosses her lips."
    else:
        narrator "She holds the cold dignity like a stance she has run a hundred times, and her body breaks from it just as surely, arching into your mouth and hands, the helpless catch of her breath the only confession the proud throat will ever make."
    lanista_npc "...You'll get no words for it, [_ttl]. You never do. But you felt the answer, same as always. Let that stand as your receipt."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_aftercrowd_dom_t4:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    $ _vi = int(getattr(store, "_vi", 0) or 0)
    if _vi % 2 == 0:
        narrator "You no longer summon [_them]; [_they] is already there when the gate falls, where [_they] is always now. The cold dignity is the last thing left standing in [_them] — a costume worn over a body schooled, season by season, to want your hand before you raise it."
    else:
        narrator "The gate bars on the richest house in eleven seasons, and the Lanista comes to you composed as ever — chin level, gaze steady — and you both know the composure is the only thing [_they] still owns outright, and that you let [_them] keep it because it pleases you to."
    lanista_npc "The face is mine. ...Everything under it answers to you, and we've both long stopped pretending otherwise. Collect, [_ttl]. I'm trained to it."
    $ _scene = "aftercrowd"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_aftercrowd_{}_{}_{}.png".format(_route, _g, _t),
            "images/lanista/cg_aftercrowd_{}_{}.png".format(_route, _g),
            "images/lanista/cg_aftercrowd_{}.png".format(_route),
            "images/lanista/cg_s4_gate_{}_{}.png".format(_route, _g),
            "images/lanista/cg_s4_gate_{}.png".format(_route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "He has been trained to this, and to you, and it shows in every line of him — the cold face composed even now while his body answers your hand before you ask, hard and ready and yours, the proud frame taking the pace you set and the pleasure you allow it like the well-broke thing it has become for you alone."
    elif lanista_gender == "male":
        narrator "The dignity is reflex now, a habit worn paper-thin over a body that belongs to you in every way that matters — wanting before you touch him, breaking the instant you take him, the surrender so practiced it needs no words and gets none, only the ragged proof of how thoroughly he is yours."
    elif _pt == "lord":
        narrator "She wears the champion's composure like a costume now, both of you knowing what's underneath it — a body schooled to your every want, slick and ready at a look, taking the rhythm you set and giving back the helpless shudder, owned down to the breath and far past pretending otherwise."
    else:
        narrator "Her pride is a formality between you now, the cold stare held over a body you have trained to your hand season by season — arching to meet you before you ask, clenching and breaking on the pace you choose, surrendered so completely the silence isn't defiance anymore, only the last small thing she keeps."
    lanista_npc "Collected in full, as ever. ...Don't look so pleased, [_ttl]. We both know whose hand I answer to now. Go — before I forget I once didn't."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_gift:
    lanista_npc "A gift. I won't ask what you want for it."
    jump lanista_visit_menu

label lanista_assess:
    lanista_npc "Measuring me, are you? Go ahead."
    jump lanista_visit_menu

label lanista_s3_gate:
    if lanista_is_dominion_route():
        jump lanista_s3_gate_dominion
    else:
        jump lanista_s3_gate_devotion

label lanista_s3_gate_devotion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The gates are barred for the night. The lamps burn low along the tunnel mouth, and the two of you are the only living things left in the great stone bowl. You came to talk numbers. The numbers have run out, and what's left in the quiet is something neither of you has dared to name in daylight."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "Eleven seasons I've kept everyone the length of a blade away. It's how you stay standing. You let no one close enough to land the killing one."
    lanista_npc "And here you are. Inside my guard. I let you walk in, and I haven't the will to put you back out."
    narrator "The Lanista steps in — close, closer than the craft allows, close enough that you feel the warmth coming off skin that's known nothing but distance for years. A scarred hand rises and stops, hovering at your jaw, asking the question it won't say."
    $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You answer it. You close the last of the distance yourself, and the kiss is nothing like the iron the Lanista wears all day — it's tentative, almost startled, a fighter discovering a thing no amount of training ever taught."
    narrator "Hands find your back, your shoulders, careful and unsteady at once. Breath catches between you. For a long moment the great empty Arena holds nothing but this — the two of you, and the dark, and the warmth neither of you fled."
    $ _scene = "s3_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    narrator "Then the Lanista breaks it — a hand flat on your chest, gentle, setting a hand's breadth of cold air back between you. The breath that follows is ragged in a way you've never heard from that iron throat."
    lanista_npc "Not like this, [_ttl]. Not tonight."
    lanista_npc "Not with the lenders' number hanging over us both and me half able to tell what's want and what's drowning. When I take you — if I take you — it'll be clear-eyed. You're worth a clear head. I'll not give you less."
    call lanista_restore_visit_scene from _lanista_restore_s3_gate_dev
    menu:
        "\"Clear-eyed, then. I'll wait as long as it takes.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "The Lanista lets out a slow breath, and for the first time you've seen, something like ease settles over the hard features."
            lanista_npc "You'll wait. ...Nobody waits, [_ttl]. They take, or they leave. You stand there and tell me you'll wait."
            lanista_npc "Go on, before I change my mind about tonight. But come back. That's not a thing I ask twice — so hear it."
        "\"Then let me clear the number first. One less thing standing between us.\"":
            $ lanista_affection += 3
            $ lanista_devotion += 2
            narrator "The Lanista studies you a long moment, and the want in it is plain now, no longer armored over."
            lanista_npc "Clear the number. You'd do that, and call it making room — not buying a thing."
            lanista_npc "...I believe you mean it that way. That's the part that undoes me. Go, [_ttl]. Come back soon."
    jump lanista_s3_gate_end

label lanista_s3_gate_dominion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The gates are barred. The night's count came up short again, and you both know whose coin stands between this Arena and the dark. You've spent weeks letting that truth settle over the bench like dust. Tonight you stop letting it settle. You step in close, and you let the Lanista feel the full weight of what's owed."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "So that's the way of it. The purse comes to collect, and what it wants isn't coin."
    lanista_npc "I've put down bigger than you on that sand, [_ttl]. Don't mistake the debt for a leash."
    narrator "But the jaw is set too hard, and you both know the books don't lie. You hold the Lanista's eye and don't look away, and the silence does the arguing for you. Slowly — every inch of it a fighter's surrender, ceded and not given — the distance closes."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You take the Lanista's jaw in your hand and turn that proud face to yours. The kiss is yours to take, and you take it — and the Lanista yields to it with a cold, furious dignity, mouth answering yours, hands fisted at sides that will not, will not reach for you first."
    narrator "No begging. Not a sound of it. Only the hard breath, the iron control bending one degree at a time, the spectacle of a champion who has decided to lose this bout on terms of their own choosing."
    $ _scene = "s3_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    narrator "Then you're the one who steps back — because taking it all tonight would be too easy, and easy isn't the same as owned. You leave the Lanista standing there, breath uneven, the proud line of the shoulders the only thing still holding."
    lanista_npc "...That's enough. You've made your point, [_ttl]."
    lanista_npc "You'll have the rest when I decide it, not when the ledger does. I yielded the bout. I didn't hand you the whole sand. Remember the difference."
    call lanista_restore_visit_scene from _lanista_restore_s3_gate_dom
    menu:
        "\"You yielded because you wanted to. We both felt that.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            narrator "The Lanista's eyes flash, and the denial dies behind them unspoken — because it would be a lie, and a fighter does not bother with lies that won't hold."
            lanista_npc "Wanted to. ...Careful, [_ttl]. You start naming what I want, and you'll have a leash on more than the debt."
            lanista_npc "Go. Before I decide whether that frightens me. Come back when the count comes in."
        "\"The rest, when you decide it. I can be patient with what I already own.\"":
            $ lanista_affection += 2
            $ lanista_dominion += 2
            narrator "Something in the Lanista's face goes very still — you've matched the cold dignity with patience of your own, and it lands harder than any grab could have."
            lanista_npc "Patient. The worst kind of creditor. The one who knows the debt isn't going anywhere."
            lanista_npc "...You've a fighter's timing, [_ttl]. Go. The sand will keep. So, it seems, will I."
    jump lanista_s3_gate_end

label lanista_s3_gate_end:
    $ lanista_s3_gate_fired = True
    $ lanista_debt_finance_unlocked = True
    $ lanista_affection = max(lanista_affection, 50)
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s4_gate:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The first spectacle is spent. The benches the old card never filled were packed tonight, rim to rim, for oiled bodies and the thinnest pretense of a fight — and the night's take is the richest this house has counted in eleven seasons. The crowd has bled away into the dark. The torches gutter low along the tunnel mouth. The coin is locked in the box, and the box, now, no longer matters."
    narrator "Whatever the Arena sold tonight, it sold for the both of you. And now the gates are barred, the great stone bowl stands empty, and the charge that has been building between you across a whole season has, at last, nowhere left to go but here."
    if lanista_is_dominion_route():
        jump lanista_s4_gate_dominion
    else:
        jump lanista_s4_gate_devotion

label lanista_s4_gate_devotion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "I held this back for the fighter I used to be. That one took the night's count and walked out the gate with the crowd. Whatever's left standing in this bowl with you isn't him — isn't armored, isn't careful. I'm done being careful with you, [_ttl]."
    narrator "The Lanista crosses the last of the distance and does not stop this time — no scarred hand that halts at your jaw to ask the question it won't say. [_Their] hands find the fastenings of your clothes with the same sure economy [_they] brings to a blade, and under the iron of it there is a tremor [_they] cannot quite still."
    $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You undo the worn leather and linen in turn, and the Lanista lets you — lets you bare the body that has stood armored against the whole world for eleven seasons. [_They] holds very still while you do it, jaw tight, eyes never once leaving your face, as if bracing for a blow that has always, until now, come."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "What comes instead is your mouth, your hands — gentleness where [_they] braced for the strike. Something in [_them] breaks open at that, quiet and enormous, and the breath [_they] lets go is the sound of a guard wholly, finally lowered."
    menu:
        "\"Let me see all of you. I'm not going anywhere.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You hold [_their] gaze while you say it, and the want in [_their] face is unarmored now, plain as a wound left open on purpose."
            lanista_npc "Not going anywhere. ...You keep saying impossible things to me as if they cost you nothing. Here, then. All of it. I've nothing left worth keeping back."
        "\"Tonight you're not made of iron. Just here. With me.\"":
            $ lanista_affection += 4
            $ lanista_devotion += 2
            narrator "The hard line of [_their] shoulders eases at that, by a degree no one else has ever been let close enough to see."
            lanista_npc "Just here. ...Eleven years I've been iron, because iron is the thing that stays standing. You make me want to learn what's under it. A dangerous thing to want, [_ttl]. I find I want it anyway."
    $ _scene = "s4_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "His body, bared, is a map of the sand — old scars, banked heat, hard muscle gone tender under your hands for the first time in its life. He gathers you against the broad warmth of him, and when he finally works his way into you it is slow, watchful, a man who has only ever known how to strike learning, breath by careful breath, how to give instead. Every sound he spends against your throat is one he has never let another living soul hear."
    elif lanista_gender == "male":
        narrator "His body is all old war — scarred, heavy with banked heat, hands that have known only the grip of a weapon learning the far gentler grip of you. When he settles over you and at last moves, sinking deep and slow, it is certain and disbelieving in the same breath, and the low broken sound he gives against your hair is one no crowd in eleven seasons ever drew out of him."
    elif _pt == "lord":
        narrator "She comes apart by degrees beneath your hands — the iron set of her loosening, the scarred strength of her going warm and pliant and willing. When you move into her she takes you with a low, broken sound, arms locking hard across your back, holding on the way a fighter holds the one thing in the world worth not letting fall."
    else:
        narrator "She lets you bare her, lets you learn the hard and beautiful country of her with hands and mouth, and the proud body that has kept the whole world a blade's length away for eleven seasons arches up into you instead of away. Mouth to mouth, breath to breath, you take each other apart by slow degrees, and every sound she gives you is one she has never once surrendered to the dark."
    narrator "After, the two of you lie tangled in the cooling dark of the empty bowl, and for a long while the Lanista will not let go of you — as though [_they] has only just understood that [_they] is allowed to hold a thing without it being torn away."
    lanista_npc "...I didn't know it could be that. Eleven seasons, and I didn't know. Stay till the lamp burns out, [_ttl]. That's the whole of what I'll ask. Just till then."
    jump lanista_s4_gate_end

label lanista_s4_gate_dominion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "The house made its best count in eleven seasons tonight — on flesh and pretense, because you willed it so. Don't think I've missed the shape of it. You've remade the Arena. And now you've come to collect the last thing standing in it that still dares call itself mine."
    narrator "You take the proud face in your hand the way you did at the first gate — but tonight you do not stop at the kiss. [_Their] jaw is iron under your fingers, [_their] eyes level and cold, and beneath that flawless composure [_they] is already answering: a fighter who has chosen the ground on which to lose."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You strip the worn leather from [_them] slow, and [_they] lets you — every fastening a fortress ceded and never once surrendered. The cold dignity does not leave [_their] face for an instant. But the body under your hands has made its own decision, and it has not thought to consult the pride."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Bared, [_they] holds the champion's stillness — chin high, gaze steady, not a single sound surrendered. And the want comes off [_them] in waves [_they] will not name. [_They] will make you take it. [_They] will not, to the last, be caught in the act of giving it."
    menu:
        "\"Keep your face as still as you like. I'll have what the rest of you is already offering.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            narrator "Something flickers behind the cold eyes — caught, and refusing to own it — and the proud jaw sets all the harder, which tells you everything the mouth will not."
            lanista_npc "Have it, then. ...You read a body the way you read a ledger, [_ttl]. Damn you for it. Take your collection. I'll keep my silence, you'll keep your prize, and we'll both call that a fair exchange."
        "\"Yield it on your terms. I'll take it on mine. We both win that bargain.\"":
            $ lanista_affection += 3
            $ lanista_dominion += 2
            narrator "The cold composure holds, but something behind it eases — you have left the pride its footing even as you claim the rest, and a fighter knows the worth of being allowed to lose standing up."
            lanista_npc "My terms, your taking. ...You'd grant me that much, with the whole of me already in your hand. The one creditor who lets the debtor keep their feet. Small wonder I can't be rid of you."
    $ _scene = "s4_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "He holds his pride like a shield to the very last — jaw set, stare level, not a sound conceded. His body keeps no such discipline. He is hard against you before you have half undressed him, and when you draw him into you and set the pace yourself, the iron in his face never breaks while everything beneath it does — the breath torn ragged, the scarred hands fisting in the bench, the whole proud frame yielding the bout and refusing, to the end, to say so."
    elif lanista_gender == "male":
        narrator "He keeps the cold dignity to the last — the level stare, the proud jaw that will not bend a degree. His body betrays every line of it. He is hard and wanting long before he will own to it, and when you take him into you and set the rhythm yourself, riding the composure clean out of him, the only confession he makes is the breath that tears loose and the hands that grip and ungrip the bench and never, ever reach to beg."
    elif _pt == "lord":
        narrator "She holds the champion's composure like a final stance — chin high, gaze steady, conceding exactly as much as she has decided to concede and not a hair more. Her body argues otherwise. She is slick and ready well before the proud mouth will allow it, and when you move into her and make her take the pace you set, the carved stone of her face never alters while the rest of her clenches and shudders and gives, and not one word of surrender ever crosses her lips."
    else:
        narrator "She gives you the cold stare to the very end — every inch the champion who chose to lose this on terms of her own choosing. Her body holds no such line. Slick and wanting under your hands, she arches into your mouth, your fingers, the rhythm you set, and the proud throat lets slip everything but the words — the catch of breath, the helpless shudder, the surrender she would bite through her own tongue before naming. You take what the pride will not give, and the pride lets you, and stays silent, and breaks."
    narrator "After, [_they] lies back in the dark with [_their] breathing slow to even out, the composure reassembling itself piece by piece — but slower than [_they] would wish, and you both know precisely why."
    lanista_npc "...You'll not hear me say it. Not tonight, not ever. But you were there. You felt the thing the words would only cheapen. Let that be enough, [_ttl] — it's more than I've handed anyone living."
    jump lanista_s4_gate_end

label lanista_s4_gate_end:
    $ lanista_s4_gate_fired = True
    $ lanista_corruption = min(100, lanista_corruption + 5)
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_morning_after:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "Morning comes in low and gold through the tunnel mouth, laying a long bar of light across the cooling sand and across the two of you. For a while neither of you moves. The great bowl is silent in a way it never is by day — no crowd, no count, no craft to keep. Only the light, and the warmth, and the slow rise and fall of breath."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Then the Lanista rises and sits at the bench's edge, back half-turned to you, and reaches for the long strips of linen. [_They] begins to wrap [_their] hands — the same ritual that comes before every bout, knuckle and wrist, the old habit of a body readying itself to be hit."
    narrator "But slower than you have ever seen it done. No snap to the linen, no economy in it. [_They] does not look at you while [_their] hands find the familiar work, and the not-looking says all the thing the wrapping is meant to hide — that the iron has somewhere been breached, and the body is reaching, by old reflex, for the only armor it has ever owned."
    lanista_npc "...Don't say anything yet, [_ttl]. Let me get my hands wrapped first."
    narrator "When the last strip is tucked and tied, [_they] finally turns and looks at you — and the look, for all the linen, is not armored at all."
    jump lanista_visit_menu

label lanista_s5_gate:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "It is done. The Governor's number is met — cleared in full, the date struck, the notice torn from the gate as though it never bit there. Whether the coin came as a gift with no hook in it, or as the closing of a debt that was always going to be settled in flesh, the Arena opens its gates tomorrow under its own name. Tonight it answers to no lender, no Governor, and no count."
    narrator "The great bowl stands empty and barred. The last torch gutters at the tunnel mouth. There's nothing left standing between you now — no debt, no code, no armor worth the name. Only the thing a whole season has been driving toward, with nowhere left to go but the body."
    if lanista_is_dominion_route():
        jump lanista_s5_gate_dominion
    else:
        jump lanista_s5_gate_devotion

label lanista_s5_gate_devotion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "You saved it asking nothing. I've turned that over a hundred times and still can't make it balance — because it doesn't. It was never a trade. Whatever I am now, [_ttl], I'm it with you and not for you. There's a world of difference, and you're the one who taught it to me."
    narrator "The Lanista crosses the sand to you, and there's no iron left in the approach — no fighter's economy, no held guard. [_They] comes the way the grief and the wanting come, together and unhidden, a body that has stood armored against the whole world for eleven seasons walking out with the armor laid down in the dust behind."
    $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "[_They] reaches for the fastenings of [_their] own clothes, then stops, and lets you do it instead — lets you bare [_them] slow, the worn leather and linen falling away, the scarred map of the body given over to your hands with nothing held back. [_They] does not brace this time. There's no blow coming, and [_they] knows it, and the knowing is the thing that undoes [_them]."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Where [_they] once braced for the strike, [_they] finds your mouth, your hands, the slow warmth of being wanted with no ledger behind it. Something in [_them] breaks open at that — quiet and enormous — and the breath [_they] lets go is the sound of a guard wholly, finally lowered."
    menu:
        "\"Grieve it here, then. The fighter, the code, all of it. I've got you while you do.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You don't tell [_them] the grief is misplaced. You only open your arms to it and let [_them] bring the whole weight — the dead champion, the buried code, eleven seasons of standing alone — and set it down against you in the dark. [_They] shakes once, hard, and then [_their] hands find you and do not let go."
            lanista_npc "Here, then. With you. ...I buried the best of me this season and never let myself mourn it. You hand me the leave to, and a shoulder to do it on. I'll waste neither, [_ttl]."
        "\"No more armor. Not tonight. Just you, and me, and nothing owed in either direction.\"":
            $ lanista_affection += 4
            $ lanista_devotion += 2
            narrator "You say it like the simple truth it is, and you watch [_them] decide to believe it — the last of the iron going out of the proud frame, the body in your hands braced for nothing now but you. Nothing owed. Nothing collected. Only this."
            lanista_npc "Nothing owed. ...Eleven years every touch came with a bill behind it, mine or theirs. You strip even that away. There's nothing left of me to defend, and I find I don't want to. Take me as I am, [_ttl]. There's no other version left."
    $ _scene = "s5_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "He comes down over you in the dark, and there's nothing of the champion in it — only the man, scarred and grieving and wanting, learning your body the way he once learned the only craft he had. When he finally sinks into you it's slow and shaking and certain, and the low sound he spends against your throat is grief and relief in the same breath: a man who has set down a weight he carried eleven years and found arms waiting underneath."
    elif lanista_gender == "male":
        narrator "He gathers you in against the warm, scarred bulk of him, and the hands that have only ever known the grip of a weapon move over you as if afraid you'll prove a dream. When he settles over you and at last moves, deep and unhurried, the iron is wholly gone from him — there's only the broken sound against your hair, the breath that catches and tears, a man grieving and wanting and held, all at once, for the first time in his life."
    elif _pt == "lord":
        narrator "She comes apart over you by slow degrees — the iron set of her loosening, the proud strength gone warm and pliant and willing under your hands. When you draw her down and move into her she takes you with a low, broken sound, arms locked hard across your back, holding the way the grieving hold the one thing left they're allowed to keep. Every sound she gives you is unarmored, and she gives them all."
    else:
        narrator "She lets you bare her and learn her, the hard and beautiful country of her gone soft for once beneath your mouth and hands, and the body that kept the whole world a blade's length away for eleven seasons arches up into you instead of away. Mouth to mouth, breath to breath, grief and wanting tangled past telling apart, you take each other slowly down into the dark, and not one sound she spends is one she has ever surrendered before."
    narrator "After, the two of you lie tangled in the cooling dark, and the Lanista holds on to you the way a fighter holds the ground they've bled for — not afraid of losing it now, only unwilling, after so long alone, to let it go a moment before [_they] must."
    lanista_npc "Whatever I was, [_ttl] — I grieved it tonight, and I'll not grieve it again. What's left, you've seen the whole of. The armor's off, and it stays off, for you. That's the bargain, and I've never struck a truer one. Stay till morning. I find I sleep, with you here."
    jump lanista_s5_gate_end

label lanista_s5_gate_dominion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "It's done, then. The number's gone, the Governor's date is ash, and the whole of it sits on the one bill we never wrote down. I came to pay it. Don't expect me to come cheaply, [_ttl] — a debt this size, a body settles slow."
    narrator "[_They] crosses the sand to you with the champion's bearing fully intact — chin level, shoulders square, every step the measured advance of a fighter who has chosen the ground. The price is understood. [_They] has come to pay it in full, on [_their] feet, with the one thing the debt could never strip away held high: the manner of the paying."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You strip the worn leather from [_them], and [_they] lets you — every fastening a fortress ceded on terms, the cold dignity never once leaving [_their] face. The body answers your hands long before the pride will allow it, and [_they] makes no move to hide the fact and none to confess it. This is the bargain: you take, [_they] pays, and the pride keeps its feet through the whole of the transaction."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Bared, [_they] holds the stillness of a fighter at the center of the bowl — the want coming off [_them] in waves [_they] will not name, the composure a final stance held against everything [_their] body has already decided. [_They] will pay every copper of this. [_They] will not, to the last breath, be caught in the act of wanting to."
    menu:
        "\"Pay it in full. I'll take every copper. You may keep the one thing you brought — your pride.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            narrator "You name the one mercy in the whole transaction, and you name it plainly — that the pride is [_theirs] to keep, the only line of credit you'll extend. Something flickers behind the cold eyes, caught and refusing to own it, and the proud jaw sets all the harder, which tells you everything the mouth will not."
            lanista_npc "My pride. You'll take the whole of the rest and leave me that. ...You're a thorough collector, [_ttl], and a stranger sort of merciful one. Have your full measure, then. I'll pay it standing, I'll keep my feet, and we'll both call that the bargain."
        "\"Your terms for the manner, mine for the taking. Settle it like that and we both walk away square.\"":
            $ lanista_affection += 3
            $ lanista_dominion += 2
            narrator "The cold composure holds, but something behind it eases — you've left the pride its footing even as you claim the rest, and a fighter knows to the copper the worth of being allowed to settle a debt standing up."
            lanista_npc "My manner, your taking. ...You'd grant me that, with the whole of me already on your books. The one creditor who lets the debtor keep their bearing through the paying. Small wonder I stopped trying to be rid of you. Square it, then — on those terms. I'll meet you copper for copper, [_ttl]."
    $ _scene = "s5_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
            "images/lanista/cg_{}_{}_{}.png".format(_scene, _route, _g),
            "images/lanista/cg_{}_{}.png".format(_scene, _route),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    $ _pt = (getattr(store, "player_title", "") or "").strip().lower()
    if lanista_gender == "male" and _pt == "lord":
        narrator "He pays the debt on his feet to the very last — jaw set, stare level, not a copper conceded that he doesn't choose to. His body keeps no such books. He's hard against you long before he'll own to it, and when you take him into you and set the pace of the settling yourself, the iron in his face never cracks while everything beneath it does — the breath torn loose, the scarred hands fisting in the bench, the whole proud frame paying in full and refusing, to the end, to call it anything but a debt discharged."
    elif lanista_gender == "male":
        narrator "He keeps the champion's composure like coin he won't spend — the level stare, the proud jaw bent not a degree. His body settles the account the mouth won't speak of. He's wanting and ready well before the pride permits it, and when you draw him into you and set the rhythm yourself, riding the discipline clean out of him, the only confession he makes is the breath that tears and the hands that grip the bench and never, not once, reach to ask for more."
    elif _pt == "lord":
        narrator "She pays in full and pays on her feet — chin high, gaze steady, conceding exactly what she's decided to concede and not a hair beyond it. Her body keeps a different ledger. She's slick and ready well before the proud mouth will allow, and when you move into her and make her take the pace you set, the carved stone of her face never alters while the rest of her clenches and shudders and gives — the debt settled to the last copper, the word for it never once crossing her lips."
    else:
        narrator "She gives you the cold composure to the very end — every inch the champion paying a debt on terms of her own choosing. Her body settles otherwise. Slick and wanting under your hands, she arches into your mouth, your fingers, the rhythm you set, and the proud throat spends everything but the naming of it — the catch of breath, the helpless shudder, the surrender she'd bite through her own tongue before speaking aloud. You take the full price, and she pays it, and keeps her pride, and breaks, all at once, in the dark."
    narrator "After, [_they] lies back in the dark and lets the composure reassemble itself piece by piece — slower than [_they] would wish, and you both know precisely why. The debt is paid. The dignity is kept. Nothing else in the bowl belongs to [_them] now, and [_they] has known that for a season."
    lanista_npc "There. Paid in full, [_ttl] — and you'll mark that I paid it standing. That's the last of me that was ever mine to keep, and I kept it, and I'd thank you not to price it for less than it cost. The rest is yours. It's been yours. Tonight only made the books agree with the truth."
    jump lanista_s5_gate_end

label lanista_s5_gate_end:
    $ lanista_s5_gate_fired = True
    $ lanista_affection = max(lanista_affection, 100)
    $ lanista_corruption = min(100, lanista_corruption + 5)
    $ lanista_recalculate_stage()
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
