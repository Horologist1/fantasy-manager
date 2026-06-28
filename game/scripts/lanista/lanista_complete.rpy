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
