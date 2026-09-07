# lanista_complete.rpy — All Lanista content (Master of the Sands)
# Stages 1-6, debt/favor services, authentic Arena Program arc,
# wager/sponsor RNG, After the Crowd repeatable, three endings.

################################################################################
### LANISTA — DEFAULT VARIABLES
################################################################################

default lanista_gender = ""                 # "male" / "female" — set on first visit
default lanista_name = "The Lanista"         # migrated to Varro/Varra on first visit
default lanista_known_name = False
default lanista_devotion = 0
default lanista_dominion = 0
default lanista_affection = 0
default lanista_corruption = 0              # 0-100
default lanista_stage = 1
default lanista_visit_count = 0
default lanista_last_talk_total_days = None
default lanista_filler_talk_index = 0        # rotates the ambient filler-talk pool
default lanista_fillers_seen = []            # filler ids already told in full (repeat = short callback variant)
default lanista_last_story_total_days = None
default lanista_last_question_total_days = None
default lanista_last_gift_total_days = None
default lanista_night_visit_total_days = None
default lanista_gate_closed_total_days = None
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
default lanista_remark_choices = {}
default lanista_gifts_given = 0
default lanista_debt_finance_unlocked = False
default lanista_debt_finance_last_day = None
default lanista_donation_total = 0
default lanista_donation_highest_tier = 0
default lanista_favors_total = 0
default lanista_favor_highest_tier = 0
default lanista_favor_balance = 0
default lanista_favors_collected = 0
default lanista_collect_last_day = None
default lanista_monthly_purse_last_month = None
default lanista_spectacle_arc_step = 0       # 0 pre-A; 1 A; 2 B; 3 C; 4 D
default lanista_spectacle_arc_last_day = None
default lanista_arena_program_tier = 0       # 0 basic; 1 Bikini; 2 Oil & Chains; 3 Spectacle
default lanista_arena_program_last_day = None
default lanista_card_tier = 0               # legacy snapshot field; no active progression
default lanista_card_last_day = None        # legacy snapshot field
default lanista_pinup_unlocked = False      # gates arena_pinup_barbarian profession
default lanista_oilchains_unlocked = False  # gates arena_oil_chains profession
default lanista_spectacle_unlocked = False  # gates arena_spectacle profession
default lanista_spectacle_pitch_done = False # The Spectacle is a 2-step mini-arc; True once the nocturnal pitch scene has run (climax follows a later visit)
default lanista_wager_last_day = None
default lanista_wager_loss_streak = 0
default lanista_s2_gate_fired = False
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
default lanista_weekly_cut_last_day = None   # devotion perk: last day the champion's cut paid out
default lanista_wager_intro_done = False
default arena_successor_met = False
default arena_lanista_speaker_name = "The Lanista"
default arena_lanista_feedback_pending = None

################################################################################
### LANISTA — TRANSFORMS & SCENE RESET
################################################################################

transform lanista_bg_blur:
    blur 4.0

transform lanista_bg_night_fallback:
    blur 4.0
    matrixcolor TintMatrix("#68789c") * BrightnessMatrix(-0.28)

transform lanista_cg_fit:
    fit "contain"
    xalign 0.5
    yalign 0.5

transform lanista_bust_right:
    # Match Yvara's established right-side emotion framing.
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

label arena_restore_successor_scene:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena.png" if renpy.loadable("images/events/arena.png") else "images/event_bg.png")
    scene expression _arena_bg at lanista_bg_blur
    show black as lanista_bg_dim:
        alpha 0.35
    return

label lanista_show_night_interior:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ _arena_night_bg = "images/buildings/bg_arena_night.jpg"
    if not renpy.loadable(_arena_night_bg):
        $ _arena_night_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena.png" if renpy.loadable("images/events/arena.png") else "images/event_bg.png")
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _lanista_bust = "images/lanista/lanista_{}_neutral.png".format(_g) if renpy.loadable("images/lanista/lanista_{}_neutral.png".format(_g)) else None
    scene expression _arena_night_bg at lanista_bg_blur
    show black as lanista_bg_dim:
        alpha 0.15
    if _lanista_bust:
        show expression _lanista_bust as lanista_bust at lanista_bust_right
    with dissolve
    return

label lanista_show_night_cutscene:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ _arena_night_bg = "images/buildings/bg_arena_night.jpg"
    if not renpy.loadable(_arena_night_bg):
        $ _arena_night_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else ("images/events/arena.png" if renpy.loadable("images/events/arena.png") else "images/event_bg.png")
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _lanista_bust = "images/lanista/lanista_{}_neutral.png".format(_g) if renpy.loadable("images/lanista/lanista_{}_neutral.png".format(_g)) else None
    scene expression _arena_night_bg
    show black as lanista_bg_dim:
        alpha 0.15
    if _lanista_bust:
        show expression _lanista_bust as lanista_bust at lanista_bust_right
    with dissolve
    return

label lanista_show_night_exterior:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ _arena_night_exterior_bg = "images/buildings/arena_night.jpg"
    if renpy.loadable(_arena_night_exterior_bg):
        scene expression _arena_night_exterior_bg at lanista_bg_blur
    else:
        $ _arena_day_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else "images/event_bg.png"
        scene expression _arena_day_bg at lanista_bg_night_fallback
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _lanista_bust = "images/lanista/lanista_{}_neutral.png".format(_g) if renpy.loadable("images/lanista/lanista_{}_neutral.png".format(_g)) else None
    show black as lanista_bg_dim:
        alpha 0.15
    if _lanista_bust:
        show expression _lanista_bust as lanista_bust at lanista_bust_right
    with dissolve
    return

label lanista_show_emotion(emotion="neutral"):
    $ _social_emotions = ("neutral", "amused", "angry", "warm", "vulnerable", "yielding")
    $ _emotion = emotion if emotion in _social_emotions else "neutral"
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_{}.png".format(_g, _emotion)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
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
        if g6:
            store.lanista_stage = 7
        elif g5 and aff >= 110:
            store.lanista_stage = 6
        elif g4 and aff >= 91:
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

    def lanista_has_legacy_progress():
        """True when an old save already advanced the arc before gender existed.

        Paying the Arena permit alone does not count: those saves still deserve
        the identity choice when they properly visit the Lanista for the first time.
        """
        if int(getattr(store, "lanista_stage", 1) or 1) > 1:
            return True
        numeric_fields = (
            "lanista_visit_count", "lanista_devotion", "lanista_dominion",
            "lanista_affection", "lanista_corruption", "lanista_gifts_given",
            "lanista_donation_total", "lanista_favors_total", "lanista_card_tier",
        )
        if any(int(getattr(store, field, 0) or 0) > 0 for field in numeric_fields):
            return True
        scalar_fields = (
            "lanista_known_name", "lanista_debt_finance_unlocked",
            "lanista_s3_gate_fired", "lanista_s4_gate_fired",
            "lanista_s5_gate_fired", "lanista_s6_gate_fired",
            "lanista_ending_done", "lanista_ending_route",
            "lanista_last_talk_total_days", "lanista_last_question_total_days",
            "lanista_last_gift_total_days", "lanista_wager_last_day",
        )
        if any(bool(getattr(store, field, False)) for field in scalar_fields):
            return True
        list_fields = (
            "lanista_s1_talks_done", "lanista_s1_remarks_done",
            "lanista_s2_talks_done", "lanista_s2_remarks_done",
            "lanista_s3_talks_done", "lanista_s3_remarks_done",
            "lanista_s4_talks_done", "lanista_s4_remarks_done",
            "lanista_s5_talks_done", "lanista_s5_remarks_done",
            "lanista_s6_talks_done",
        )
        return any(bool(getattr(store, field, [])) for field in list_fields)

    def lanista_resolve_route():
        """Resolve the ending with Yvara's reachable +/-9 Mixed band."""
        dev = int(getattr(store, "lanista_devotion", 0) or 0)
        dom = int(getattr(store, "lanista_dominion", 0) or 0)
        diff = abs(dev - dom)
        if dev > dom and diff >= 10:
            return "devotion"
        if dom > dev and diff >= 10:
            return "dominion"
        return "mixed"

    def lanista_is_dominion_route():
        """Choose the binary pre-S6 content track from the current lean."""
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

    def lanista_personal_content_is_enabled():
        """Keep the relationship arc absent in restrictive mode."""
        return bool(getattr(persistent, "nsfw_enabled", False))

    def lanista_visit_is_closed_today():
        """A relationship gate ends personal access for the current day."""
        return getattr(store, "lanista_gate_closed_total_days", None) == calculate_total_days()

    def lanista_determine_ending():
        return lanista_resolve_route()

    def lanista_pronoun(kind):
        """kind: 'subj'/'obj'/'poss'/'poss_pron'/'refl'/'title'. Gender from lanista_gender."""
        male = (getattr(store, "lanista_gender", "male") or "male") != "female"
        table = {
            "subj": ("he", "she"), "obj": ("him", "her"),
            "poss": ("his", "her"), "poss_pron": ("his", "hers"),
            "refl": ("himself", "herself"),
            "title": ("the Master of the Sands", "the Master of the Sands"),
        }
        m, f = table.get(kind, ("they", "they"))
        return m if male else f

    def arena_uses_successor():
        return bool(
            getattr(store, "lanista_ending_dominion", False)
            and getattr(store, "lanista_is_worker", False)
        )

    def arena_prepare_lanista_speaker():
        if arena_uses_successor():
            store.arena_lanista_speaker_name = "The New Lanista"
        else:
            store.arena_lanista_speaker_name = getattr(store, "lanista_name", "The Lanista") or "The Lanista"
        return store.arena_lanista_speaker_name

    def lanista_record_remark_choice(choices, remark_id, tone):
        result = dict(choices) if hasattr(choices, "items") else {}
        remark_id = str(remark_id or "")
        tone = str(tone or "").lower()
        if remark_id and tone in ("devotion", "dominion"):
            result[remark_id] = tone
        return result

    def lanista_remark_choice(remark_id):
        choices = getattr(store, "lanista_remark_choices", {})
        if not hasattr(choices, "get"):
            return ""
        tone = str(choices.get(str(remark_id or ""), "") or "").lower()
        return tone if tone in ("devotion", "dominion") else ""

    def lanista_wager_card(total_days):
        """Return a deterministic two-fighter card and its visible form clue."""
        cards = (
            {
                "kind": "comeback", "left_name": "Orsen the Old", "right_name": "Caldr Quickhand", "favored": "left",
                "opening": "A veteran champion faces a younger blade who has never fought beyond the third round.",
                "clue": "Orsen wastes no motion in the warm-up. Caldr is already breathing through his mouth.",
                "win_detail": "{pick} lets the early fury spend itself, then ends the fourth exchange with one clean counter.",
                "loss_detail": "{pick} waits for a late opening that never comes; {other} keeps enough breath to force the count.",
            },
            {
                "kind": "comeback", "left_name": "Orsen the Old", "right_name": "Caldr Quickhand", "favored": "right",
                "opening": "The old champion returns against the fast challenger who nearly took the name last time.",
                "clue": "Orsen favors the scarred knee every time he turns. Caldr has noticed and keeps circling toward it.",
                "win_detail": "{pick} makes the damaged side the center of the bout and steals the deciding exchange.",
                "loss_detail": "{pick} misreads the damaged side; {other} uses that mistake to turn the rail into a trap.",
            },
            {
                "kind": "grudge", "left_name": "The Red Banner", "right_name": "The Ash Wolf", "favored": "left",
                "opening": "Two rivals meet without the customary salute, each carrying an old insult onto the sand.",
                "clue": "The Red Banner breathes slowly. The Ash Wolf spends the walk to the ring shouting at the crowd.",
                "win_detail": "{pick} refuses every insult and saves the anger for the one opening that settles the grudge.",
                "loss_detail": "{pick} answers the bait too soon; {other} turns the wild exchange into a clean finish.",
            },
            {
                "kind": "grudge", "left_name": "The Red Banner", "right_name": "The Ash Wolf", "favored": "right",
                "opening": "The Red Banner and the Ash Wolf return to settle what their last bout left unfinished.",
                "clue": "The Wolf is quiet tonight. The Banner's sword hand trembles whenever the old wound is mentioned.",
                "win_detail": "{pick} lets the silence tighten until {other} commits first, then answers without mercy.",
                "loss_detail": "{pick} mistakes stillness for fear; {other} breaks the measure with the steadier hand.",
            },
            {
                "kind": "styles", "left_name": "Maela Shieldborn", "right_name": "Torren Spearhand", "favored": "left",
                "opening": "A patient shield-bearer draws a long-reach spear fighter in a bout of opposed styles.",
                "clue": "Maela checks every strap twice. Torren keeps changing his grip and looking toward the shield edge.",
                "win_detail": "{pick} closes the distance one measured step at a time and wins where the long weapon cannot turn.",
                "loss_detail": "{pick} gives away the measure; {other} owns the distance and never yields it back.",
            },
            {
                "kind": "styles", "left_name": "Maela Shieldborn", "right_name": "Torren Spearhand", "favored": "right",
                "opening": "Shield and spear meet again, but neither fighter carries the same equipment as last time.",
                "clue": "A hairline split runs through Maela's shield rim. Torren has seen it and warms up with the butt strike.",
                "win_detail": "{pick} controls the broken rim instead of fighting around it, then takes the bout at close measure.",
                "loss_detail": "{pick} trusts the damaged guard once too often; {other} finds the same fault and drives through it.",
            },
            {
                "kind": "reach", "left_name": "Nera Foxknife", "right_name": "Hadrik Stonejaw", "favored": "left",
                "opening": "A knife fighter meets a heavy swordsman who means to end the bout in a single reach.",
                "clue": "Nera keeps low and loose. Hadrik's sword shoulder catches each time the blade rises above his head.",
                "win_detail": "{pick} stays beneath the heavy arc and cuts the distance down until only the quick hand matters.",
                "loss_detail": "{pick} enters half a beat too early; {other} catches the rush and ends it at full reach.",
            },
            {
                "kind": "reach", "left_name": "Nera Foxknife", "right_name": "Hadrik Stonejaw", "favored": "right",
                "opening": "Foxknife and Stonejaw return, speed against reach with fresh coin on both names.",
                "clue": "The strap on Nera's lead boot is loose. Hadrik tests the high guard without a hitch tonight.",
                "win_detail": "{pick} makes the first step decisive and forces {other} to fight from the wrong distance.",
                "loss_detail": "{pick} loses the footing at the rail; {other} takes the space before it can be recovered.",
            },
            {
                "kind": "grapple", "left_name": "Vessa Chainhand", "right_name": "Doran Ox", "favored": "left",
                "opening": "Two pit wrestlers meet bare-handed, one all leverage and one built to break holds by weight.",
                "clue": "Vessa's stance is square and patient. Three fingers on Doran's gripping hand are freshly bound.",
                "win_detail": "{pick} turns the first failed grip into a shoulder lock and keeps it until the sand is struck.",
                "loss_detail": "{pick} reaches for a hold that will not close; {other} rolls the weight through and takes the count.",
            },
            {
                "kind": "grapple", "left_name": "Vessa Chainhand", "right_name": "Doran Ox", "favored": "right",
                "opening": "Chainhand and the Ox return to the pit with no steel and nowhere to hide a weakness.",
                "clue": "Vessa protects the left ribs during every breakfall. Doran's bound hand is bare and closing cleanly.",
                "win_detail": "{pick} forces the clinch toward the guarded ribs and turns raw pressure into the deciding fall.",
                "loss_detail": "{pick} drives straight into the defense; {other} borrows the force and sends it into the sand.",
            },
            {
                "kind": "tempo", "left_name": "Ilyr Twinblade", "right_name": "Mara Blackhammer", "favored": "left",
                "opening": "Two quick blades face a war hammer in a bout decided by rhythm more than armor.",
                "clue": "Ilyr's blades land together on every drill mark. Mara is rushing the second swing before the first settles.",
                "win_detail": "{pick} owns the rhythm from the first clash and makes {other} answer one strike behind.",
                "loss_detail": "{pick} breaks rhythm chasing the finish; {other} claims the empty beat with both hands.",
            },
            {
                "kind": "tempo", "left_name": "Ilyr Twinblade", "right_name": "Mara Blackhammer", "favored": "right",
                "opening": "Twin blades and black hammer meet again after both fighters change their opening pattern.",
                "clue": "One of Ilyr's blades pulls low after each flourish. Mara waits through a full count before every swing.",
                "win_detail": "{pick} refuses the false tempo and lands only when {other} has spent the recovery.",
                "loss_detail": "{pick} commits to the old rhythm; {other} has counted it and meets the final beat first.",
            },
            {
                "kind": "debut", "left_name": "Lysa Firstblood", "right_name": "Bram Coalhand", "favored": "left",
                "opening": "Two unbeaten newcomers meet after very different roads through the provincial pits.",
                "clue": "Lysa watches the sand settle before moving. Bram cannot keep his sword hand from flexing.",
                "win_detail": "{pick} lets the first roar pass, finds the measure, and fights as though the great bowl were empty.",
                "loss_detail": "{pick} chases the crowd's approval; {other} ignores the noise and takes the cleaner opening.",
            },
            {
                "kind": "debut", "left_name": "Lysa Firstblood", "right_name": "Bram Coalhand", "favored": "right",
                "opening": "Firstblood and Coalhand return with one professional bout apiece and reputations growing faster than either purse.",
                "clue": "Lysa keeps touching the split over her eye. Bram's hands are still for the first time anyone remembers.",
                "win_detail": "{pick} makes patience look learned rather than borrowed and takes the debut rivalry in three exchanges.",
                "loss_detail": "{pick} guards the old damage too openly; {other} reads the fear and owns that side of the sand.",
            },
            {
                "kind": "southpaw", "left_name": "Jerek Southpaw", "right_name": "Sava Bellsteel", "favored": "left",
                "opening": "An awkward left-handed cutter meets a textbook duelist who has dismantled every ordinary stance put before her.",
                "clue": "Jerek's lead foot keeps stealing the outside line. Sava crosses her feet whenever she turns to follow him.",
                "win_detail": "{pick} keeps the wrong-handed angle and makes {other}'s perfect schooling answer the wrong question.",
                "loss_detail": "{pick} gives up the outside line; {other} straightens the geometry and wins on familiar ground.",
            },
            {
                "kind": "southpaw", "left_name": "Jerek Southpaw", "right_name": "Sava Bellsteel", "favored": "right",
                "opening": "Southpaw and Bellsteel meet again after a month spent studying the angle that decided their first bout.",
                "clue": "Jerek's left wrist is bound beneath the glove. Sava now pivots without letting her heels cross.",
                "win_detail": "{pick} closes the troublesome angle before it forms and forces {other} into a plain contest of speed.",
                "loss_detail": "{pick} trusts the injured hand to create the old puzzle; {other} breaks the pattern at its first turn.",
            },
            {
                "kind": "armor", "left_name": "Helma Ironcoat", "right_name": "Caius Lightstep", "favored": "left",
                "opening": "A fully armored marcher faces a light skirmisher who intends to win without being touched once.",
                "clue": "Every buckle on Helma's harness sits flat. Caius keeps stretching a calf that tightens when he changes direction.",
                "win_detail": "{pick} turns armor into advancing ground and takes away every lane {other} needs to stay untouched.",
                "loss_detail": "{pick} cannot force the turn quickly enough; {other} keeps one lane open and spends it at the rail.",
            },
            {
                "kind": "armor", "left_name": "Helma Ironcoat", "right_name": "Caius Lightstep", "favored": "right",
                "opening": "Ironcoat and Lightstep return, weight against movement, with the crowd arguing over which failed first last time.",
                "clue": "Helma's neck fastening will not sit flush. Caius changes direction cleanly on both legs in the warm-up.",
                "win_detail": "{pick} draws the heavy guard upward, changes level, and wins the open space beneath it.",
                "loss_detail": "{pick} stays too long inside the armored measure; {other} closes the gap and makes weight decisive.",
            },
            {
                "kind": "endurance", "left_name": "Runa Longwind", "right_name": "Marek Flint", "favored": "left",
                "opening": "Two attrition fighters meet in a long-card bout where neither expects the first exchanges to matter.",
                "clue": "Runa's breath keeps the same count through every drill. Sweat already darkens Marek's collar.",
                "win_detail": "{pick} yields the early ground, keeps the lungs, and takes the bout when {other}'s pace finally breaks.",
                "loss_detail": "{pick} spends too much proving patience; {other} banks enough early damage to survive the late count.",
            },
            {
                "kind": "endurance", "left_name": "Runa Longwind", "right_name": "Marek Flint", "favored": "right",
                "opening": "Longwind and Flint face a seven-round card after both swear the last result was a matter of preparation.",
                "clue": "Runa hides a cough behind her glove. Marek refuses every invitation to quicken the warm-up.",
                "win_detail": "{pick} keeps the promised pace, denies {other} a recovery round, and owns the final count.",
                "loss_detail": "{pick} accelerates when the cough seems to matter; {other} survives the test and punishes the wasted breath.",
            },
        )
        try:
            index = max(0, int(total_days)) % len(cards)
        except Exception:
            index = 0
        return dict(cards[index])

    def lanista_wager_pick_chance(card, pick):
        if not hasattr(card, "get"):
            return 0.30
        return 0.70 if str(pick) == str(card.get("favored")) else 0.30

    def lanista_wager_payout(chance):
        """Payout multiple on a winning stake. The long-odds risky read pays
        double the strong read, so backing the underdog is worth the danger."""
        return 2 if float(chance) > 0.50 else 4

    def lanista_wager_read_label(card, pick):
        chance = lanista_wager_pick_chance(card, pick)
        label = "Strong read" if chance > 0.50 else "Risky read"
        return "{} — {}%, pays {}x".format(label, int(round(chance * 100)), lanista_wager_payout(chance))

    def lanista_wager_result_text(card, pick, won):
        if not hasattr(card, "get"):
            return "The bout turns before the book can make sense of it."
        pick = "left" if str(pick) == "left" else "right"
        other = "right" if pick == "left" else "left"
        pick_name = str(card.get(pick + "_name", "Your fighter") or "Your fighter")
        other_name = str(card.get(other + "_name", "the opponent") or "the opponent")
        key = "win_detail" if won else "loss_detail"
        fallback = "{pick} takes the deciding exchange from {other}." if won else "{other} takes the deciding exchange from {pick}."
        template = str(card.get(key, fallback) or fallback)
        try:
            return template.format(pick=pick_name, other=other_name)
        except Exception:
            return fallback.format(pick=pick_name, other=other_name)

    def lanista_wager(stake, base_chance):
        """Resolve a money+RNG physical challenge. Returns (won_bool, delta_money).
        Deducts the stake up front. The payout scales inversely with the read:
        a strong read (chance > 0.5) returns 2x the stake (profit +500 on a 500
        stake), a long-odds risky read returns 4x (profit +1500). A third
        straight loss is blocked."""
        stake = max(0, int(stake))
        chance = max(0.05, min(0.95, float(base_chance)))
        payout = lanista_wager_payout(chance)
        store.money = int(getattr(store, "money", 0)) - stake
        loss_streak = max(0, int(getattr(store, "lanista_wager_loss_streak", 0) or 0))
        won = loss_streak >= 2 or renpy.random.random() < chance
        store.lanista_wager_loss_streak = 0 if won else loss_streak + 1
        winnings = int(stake * payout) if won else 0
        store.money = int(getattr(store, "money", 0)) + winnings
        return (won, winnings - stake)

    def lanista_finance_track_complete():
        # There is now a single creditor answer: paying the Arena's debts down
        # by taking over the markers. The books read as settled once every
        # marker has been carried to its end. The legacy donation column is
        # preserved for save compatibility but is no longer reachable.
        markers = int(getattr(store, "lanista_favor_highest_tier", 0) or 0)
        return markers >= 4

    def lanista_story_cooldown_active():
        """Keep one complete quiet day between authored story events."""
        last_story = getattr(store, "lanista_last_story_total_days", None)
        if last_story is None:
            return False
        try:
            elapsed_days = int(calculate_total_days()) - int(last_story)
            return 0 <= elapsed_days <= 1
        except (TypeError, ValueError):
            return False

    def lanista_mark_story_event():
        store.lanista_last_story_total_days = calculate_total_days()
        return store.lanista_last_story_total_days

    def lanista_wager_available():
        """The house book opens every second day, not daily. The first wager is
        always free; a future or garbage stamp is treated as available, mirroring
        the story cooldown's own defensive clamp."""
        last_day = getattr(store, "lanista_wager_last_day", None)
        if last_day is None:
            return True
        try:
            elapsed_days = int(calculate_total_days()) - int(last_day)
        except (TypeError, ValueError):
            return True
        if elapsed_days < 0:
            return True
        return elapsed_days >= 2

    def lanista_weekly_cut_available():
        """The champion's cut pays out once per week in the devotion ending only.
        The first visit after the ending always pays; a future or garbage stamp
        is treated as due, mirroring the wager cooldown's defensive clamp."""
        if not (bool(getattr(store, "lanista_ending_devotion", False))
                and bool(getattr(store, "lanista_ending_done", False))):
            return False
        last_day = getattr(store, "lanista_weekly_cut_last_day", None)
        if last_day is None:
            return True
        try:
            elapsed_days = int(calculate_total_days()) - int(last_day)
        except (TypeError, ValueError):
            return True
        if elapsed_days < 0:
            return True
        return elapsed_days >= 7

    def lanista_next_talk_state():
        """Return the single next Talk and whether it closes the personal visit."""
        stage = int(getattr(store, "lanista_stage", 1) or 1)
        if not bool(getattr(store, "lanista_s3_gate_fired", False)):
            eligible_stages = (
                (1, True),
                (2, stage >= 2),
                (3, stage >= 3),
            )
        else:
            eligible_stages = (
                (4, stage >= 4 and not bool(getattr(store, "lanista_s4_gate_fired", False))),
                (5, stage >= 5 and not bool(getattr(store, "lanista_s5_gate_fired", False))),
                (6, stage >= 6 and not bool(getattr(store, "lanista_s6_gate_fired", False))),
            )

        closing_talks = {
            "s3_t1", "s3_t3",
            "s4_t1", "s4_t2", "s4_t3",
            "s5_t1", "s5_t2", "s5_t3",
        }
        for talk_stage, eligible in eligible_stages:
            if not eligible:
                continue
            done = set(getattr(store, "lanista_s{}_talks_done".format(talk_stage), []) or [])
            for talk_number in range(1, 4):
                talk_id = "s{}_t{}".format(talk_stage, talk_number)
                if talk_id in done:
                    continue
                closes_visit = talk_id in closing_talks
                return {
                    "target": "lanista_s{}_talk_router".format(talk_stage),
                    "talk_id": talk_id,
                    "closes_visit": closes_visit,
                    "action": "Stay and talk. (Story — ends the visit)" if closes_visit else "Talk.",
                }

        return {
            "target": "lanista_talk_generic",
            "talk_id": None,
            "closes_visit": False,
            "action": "Talk.",
        }

    def lanista_story_state():
        """Return the next personal-story action and its first unmet requirement."""
        stage = int(getattr(store, "lanista_stage", 1) or 1)
        affection = int(getattr(store, "lanista_affection", 0) or 0)

        def _state(target, action, requirements, ready_reason):
            for met, reason in requirements:
                if not met:
                    return {"ready": False, "target": target, "action": action, "reason": reason}
            if lanista_story_cooldown_active():
                return {
                    "ready": False,
                    "target": target,
                    "action": action,
                    "reason": "A quiet day must pass before the next story event.",
                }
            return {"ready": True, "target": target, "action": action, "reason": ready_reason}

        def _talks_complete_through(last_stage):
            for talk_stage in range(1, last_stage + 1):
                done = set(getattr(store, "lanista_s{}_talks_done".format(talk_stage), []) or [])
                required = {"s{}_t{}".format(talk_stage, talk_number) for talk_number in range(1, 4)}
                if not required.issubset(done):
                    return False
            return True

        if not bool(getattr(store, "lanista_s2_gate_fired", False)):
            return _state(
                "lanista_s2_gate",
                "Stay for the Arena's answer. (Story — ends the visit)",
                (
                    (stage >= 2, "The relationship needs more time before the next answer."),
                    (_talks_complete_through(1), "There is more the Lanista means to discuss."),
                ),
                "The Lanista is ready to answer after the gates close.",
            )

        if not bool(getattr(store, "lanista_s3_gate_fired", False)):
            return _state(
                "lanista_s3_gate",
                "Stay when the gates close. (Story — ends the visit)",
                (
                    (stage >= 3, "The relationship needs more time before the next night."),
                    (_talks_complete_through(3), "There is more the Lanista means to discuss."),
                    (affection >= 50, "The distance between you has not closed enough yet."),
                ),
                "The Lanista will remain after the gates close.",
            )

        if not bool(getattr(store, "lanista_s4_gate_fired", False)):
            return _state(
                "lanista_s4_gate",
                "Stay after closing. (Story — ends the visit)",
                (
                    (stage >= 4, "The relationship needs more time before the next night."),
                    (_talks_complete_through(4), "There is more the Lanista means to discuss."),
                    (affection >= 80, "The distance between you has not closed enough yet."),
                ),
                "The Lanista has left the armory lamp burning for you.",
            )

        if not bool(getattr(store, "lanista_s5_gate_fired", False)):
            return _state(
                "lanista_s5_gate",
                "Answer the night without armor. (Story — ends the visit)",
                (
                    (stage >= 5, "The relationship needs more time before the next night."),
                    (_talks_complete_through(5), "There is more the Lanista means to discuss."),
                    (affection >= 100, "The distance between you has not closed enough yet."),
                ),
                "Nothing remains between you and the night armory door.",
            )

        if not bool(getattr(store, "lanista_s6_gate_fired", False)):
            return _state(
                "lanista_s6_gate",
                "Settle the final terms. (Story — ends the visit)",
                (
                    (stage >= 6, "The relationship needs more time before its final terms."),
                    (_talks_complete_through(6), "There is more the Lanista means to discuss."),
                    (affection >= 110, "The final certainty between you has not formed yet."),
                ),
                "The final terms are ready to be spoken.",
            )

        if not bool(getattr(store, "lanista_ending_done", False)):
            return _state(
                "lanista_ending_resolution",
                "Settle what remains. (Story — ending)",
                (),
                "The final choice is ready.",
            )

        return {"ready": False, "target": None, "action": "", "reason": "The story between you has reached its ending."}

    def lanista_main_story_closes_visit():
        """Reserve the visit's single closing slot for a gate or night Talk."""
        if bool(lanista_story_state().get("ready", False)):
            return True
        if lanista_story_cooldown_active():
            return False
        if getattr(store, "lanista_last_talk_total_days", None) == calculate_total_days():
            return False
        return bool(lanista_next_talk_state().get("closes_visit", False))

    def lanista_current_month_key():
        year = max(1, int(getattr(store, "current_year", 1) or 1))
        month = min(12, max(1, int(getattr(store, "current_month", 1) or 1)))
        return (year - 1) * 12 + month

    def lanista_monthly_purse_available():
        if int(getattr(store, "lanista_favor_highest_tier", 0) or 0) < 4:
            return False
        if int(getattr(store, "lanista_favor_balance", 0) or 0) >= 4:
            return False
        return getattr(store, "lanista_monthly_purse_last_month", None) != lanista_current_month_key()

    def lanista_finance_purchase_available():
        # A single creditor answer remains: paying the Arena's debts down by
        # taking over its markers. The finance topic stays open until every
        # marker has been bought.
        return int(getattr(store, "lanista_favor_highest_tier", 0) or 0) < 4

    def lanista_collect_service_is_unlocked(tier):
        tier = max(1, min(4, int(tier or 1)))
        if int(getattr(store, "lanista_favor_highest_tier", 0) or 0) < tier:
            return False
        if tier == 1:
            return bool(getattr(store, "lanista_s3_gate_fired", False))
        if tier == 2:
            return bool(getattr(store, "lanista_pinup_unlocked", False))
        if tier == 3:
            return int(getattr(store, "lanista_stage", 1) or 1) >= 5
        return bool(getattr(store, "lanista_s5_gate_fired", False))

    def lanista_arena_arc_next_step():
        # Pacing rule: the persuasion chain opens at the S3 gate and advances by
        # the daily arc cooldown (lanista_spectacle_arc_last_day), not by S4/S5
        # milestones. Step 2 (the real bout) and step 3 (the clothed Bikini
        # Bouts pitch on the slate) are both S3 content — the player gets genuine
        # corruption/dominion opportunities well before the finale. Step 4 is the
        # explicit nude reveal, so it stays gated behind the S4 gate.
        step = int(getattr(store, "lanista_spectacle_arc_step", 0) or 0)
        if step == 1 and bool(getattr(store, "lanista_s3_gate_fired", False)):
            return 2
        if step == 2 and bool(getattr(store, "lanista_s3_gate_fired", False)):
            return 3
        if (
            step == 3
            and bool(getattr(store, "lanista_s4_gate_fired", False))
            and bool(getattr(persistent, "nsfw_enabled", False))
        ):
            return 4
        return 0

    def lanista_arena_format_next_step():
        # The later program formats (Oil & Chains, The Spectacle) are explicit,
        # so they stay behind the S4 gate — but no further. Once Bikini Bouts
        # (tier 1) exists and the S4 gate has fired, each format opens spaced only
        # by the daily program cooldown (lanista_arena_program_last_day). This
        # lets the corruption program build through S4-S6 instead of funneling
        # every unlock into S5.
        if not bool(getattr(persistent, "nsfw_enabled", False)):
            return 0
        if not bool(getattr(store, "lanista_s4_gate_fired", False)):
            return 0
        tier = int(getattr(store, "lanista_arena_program_tier", 0) or 0)
        if tier == 1:
            return 2
        if tier == 2:
            # The Spectacle is a two-step mini-arc, unlike the single-scene Oil &
            # Chains: the nocturnal pitch (4) comes first and only sets up the
            # night, then the climax (3) runs once lanista_spectacle_pitch_done is
            # set. The daily program cooldown paces the two across separate visits.
            if not bool(getattr(store, "lanista_spectacle_pitch_done", False)):
                return 4
            return 3
        return 0

    def lanista_evening_state():
        """Return every optional scene competing for the visit's closing slot."""
        total_days = calculate_total_days()
        story_day_free = not lanista_story_cooldown_active()
        arc_next = lanista_arena_arc_next_step()
        format_next = lanista_arena_format_next_step()
        # Collect no longer carries its own daily cooldown — it depends only on
        # having an owed favor to spend. The cross-block with After the Crowd
        # stays (one intimate closing scene per night), so the two cannot stack.
        collect_available = bool(
            getattr(store, "arena_unlocked", False)
            and getattr(persistent, "nsfw_enabled", False)
            and getattr(store, "lanista_s3_gate_fired", False)
            and int(getattr(store, "lanista_favor_balance", 0) or 0) > 0
            and getattr(store, "lanista_aftercrowd_last_day", None) != total_days
        )
        aftercrowd_last = getattr(store, "lanista_aftercrowd_last_day", None)
        # Post-ending the relationship is settled, so ease the after-crowd cadence
        # (every 2 days instead of 3); in-arc it stays the slower 3-day cooldown.
        aftercrowd_cooldown = 2 if bool(getattr(store, "lanista_ending_done", False)) else 3
        aftercrowd_available = bool(
            getattr(store, "arena_unlocked", False)
            and getattr(persistent, "nsfw_enabled", False)
            and getattr(store, "lanista_s4_gate_fired", False)
            and getattr(store, "lanista_collect_last_day", None) != total_days
            and (total_days - (aftercrowd_last or 0)) >= aftercrowd_cooldown
        )
        return {
            "arena_arc": bool(
                story_day_free
                and getattr(store, "arena_unlocked", False)
                and arc_next in (2, 4)
                and getattr(store, "lanista_spectacle_arc_last_day", None) != total_days
            ),
            "arena_format": bool(
                story_day_free
                and getattr(store, "arena_unlocked", False)
                and format_next > 0
                and getattr(store, "lanista_arena_program_last_day", None) != total_days
            ),
            "collect": collect_available,
            "aftercrowd": aftercrowd_available,
        }

    def lanista_aftercrowd_relationship_tier():
        # Tiers track the story gates that unlock them, so completing a gate
        # immediately yields its tier's art. S6 fires at affection >= 110 (no
        # higher floor), so tier 4 (the dedicated cg_aftercrowd_* art) must key
        # off 110, not 125, or the finale's CG stays unreachable. S5 sets a floor
        # of max(affection, 100), so tier 3 keys off 100.
        affection = int(getattr(store, "lanista_affection", 0) or 0)
        if bool(getattr(store, "lanista_s6_gate_fired", False)) and affection >= 110:
            return 4
        if bool(getattr(store, "lanista_s5_gate_fired", False)) and affection >= 100:
            return 3
        if affection >= 91:
            return 2
        return 1

    def lanista_corruption_tier():
        # Each level maps to ONE bespoke trait (defined in traits_lanista.json),
        # rather than a stack of generic traits. Tier 4 keeps the player-facing
        # label Exhibitionist but uses the unique Arena Exhibitionist catalog key
        # so it cannot override the generic worker trait of the same name.
        corr = int(getattr(store, "lanista_corruption", 0) or 0)
        if corr < 20:
            return (0, "Unbroken", ["Unbroken"])
        if corr < 40:
            return (1, "Curious", ["Curious"])
        if corr < 55:
            return (2, "Open-Minded", ["Open-Minded"])
        if corr < 70:
            return (3, "Uninhibited", ["Uninhibited"])
        if corr < 85:
            return (4, "Exhibitionist", ["Arena Exhibitionist"])
        return (5, "Pin-Up Barbarian", ["Pin-Up Barbarian"])

    # Gift table: item_id -> (devotion_gain, dominion_gain, affection_gain).
    # A fighter measures a gift by its use. Blades and the care of the body
    # earn devotion; a chemical command of desire earns dominion and a sting.
    LANISTA_GIFTS = {
        # Personal gifts available from ordinary shops. Affection is capped at +2
        # on every gift so a full purse can no longer farm the relationship open.
        "champion_hand_wraps":       (3, 0, 2),
        "arena_whetstone":           (2, 0, 2),
        "iron_oath_chain":           (0, 3, 2),
        # Strong drink — shared comfort
        "fine_wine":                (2, 0, 2),
        # A blade for the craft — the rare ones land hardest. Story/quest blades
        # are deliberately excluded: obsidian_blade is an Objective-12 djinn key,
        # and enchanted_blade_malachar is a unique reward from the Malachar arc
        # (shop_available: false). Handing either to the Lanista as a trinket
        # would strip a key item out of its own questline.
        "training_sword":           (1, 0, 1),
        "iron_sword":               (2, 0, 2),
        "bronze_sword":             (2, 0, 2),
        "steel_sword":              (3, 0, 2),
        "silver_sword":             (3, 0, 2),
        "mithril_sword":            (4, 0, 2),
        "flame_dagger":             (3, 0, 2),
        # A salve for old wounds — care for the body behind the armor
        "health_potion":            (3, 0, 2),
        "potion_vitality":          (3, 0, 2),
        "stamina_elixir":           (2, 0, 2),
        # A draught to command desire — taken as the insult it is
        "elixir_passion":           (0, 2, -2),
    }

    # Item groups for the gift reaction lines (no per-item labels needed).
    LANISTA_GIFT_BLADES = {
        "training_sword", "iron_sword", "bronze_sword", "steel_sword",
        "silver_sword", "mithril_sword", "flame_dagger",
    }
    LANISTA_GIFT_SALVES = {"health_potion", "potion_vitality", "stamina_elixir"}

    def lanista_get_giftable_items():
        """Return [(item_id, display_name, qty)] from manager inventory the Lanista accepts.
        Mirrors yvara_get_giftable_items' store/global-inventory read."""
        inv_store = getattr(store, "manager_inventory", [])
        inv_global = manager_inventory if "manager_inventory" in globals() else []
        item_defs = items_json.get("items", []) if "items_json" in globals() and hasattr(items_json, "get") else []
        allowed = set(getattr(store, "LANISTA_GIFTS", LANISTA_GIFTS).keys())

        qty_by_id = {}
        inv = list(inv_store or [])
        if inv_global is not inv_store:
            inv += list(inv_global or [])
        for entry in inv:
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                continue
            iid = str(entry[0])
            try:
                qty = int(entry[1])
            except Exception:
                qty = 1
            if iid in allowed and qty > 0:
                qty_by_id[iid] = qty_by_id.get(iid, 0) + qty

        result = []
        for iid, qty in qty_by_id.items():
            item_data = next((i for i in item_defs if i.get("id") == iid), None)
            name = item_data.get("display_name") or item_data.get("name") if item_data else iid
            result.append((iid, name, qty))
        return result

    def lanista_remove_gift_item(item_id, quantity=1):
        """Remove a gift item from the manager inventory (store/global safe).
        Mirrors yvara_remove_gift_item; leans on the global remove_item_from_inventory."""
        try:
            _qty = max(1, int(quantity))
        except Exception:
            _qty = 1

        def _count_item(inv, target_id):
            total = 0
            try:
                for entry in list(inv or []):
                    if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                        continue
                    if str(entry[0]) != str(target_id):
                        continue
                    try:
                        total += max(0, int(entry[1]))
                    except Exception:
                        total += 1
            except Exception:
                return 0
            return total

        _store_inv = getattr(store, "manager_inventory", None)
        _global_inv = manager_inventory if "manager_inventory" in globals() else None

        if _store_inv is not None:
            try:
                _before = _count_item(_store_inv, item_id)
                if _before > 0:
                    remove_item_from_inventory(_store_inv, item_id, min(_qty, _before))
                    if _count_item(getattr(store, "manager_inventory", _store_inv), item_id) < _before:
                        return True
            except Exception:
                pass

        if _global_inv is not None and _global_inv is not _store_inv:
            try:
                _before = _count_item(_global_inv, item_id)
                if _before > 0:
                    remove_item_from_inventory(_global_inv, item_id, min(_qty, _before))
                    if _count_item(_global_inv, item_id) < _before:
                        return True
            except Exception:
                pass

        return False

    # Register the Lanista first-visit popup in the intro-popup registry that
    # core/screens.rpy defines at init -1 (this block is init 0, so it runs
    # after). Extending the store dict here keeps screens.rpy untouched.
    _lanista_popup_registry = getattr(store, "INTRO_POPUP_TEXTS", None)
    if _lanista_popup_registry is not None and hasattr(_lanista_popup_registry, "__setitem__"):
        _lanista_popup_registry["lanista_visit"] = {
            "title": "Lanista Romance Quest",
            "body": [
                "This is a visual novel style romance route. Progress comes from repeated visits, conversations, remarks, wagers, and gifts over multiple days.",
                "",
                "{u}Devotion{/u}: romantic progress (respect, trust, partnership). Higher devotion pushes scenes toward meeting the fighter as an equal.",
                "{u}Dominion{/u}: domination progress (debt, leverage, ownership). Higher dominion pushes scenes toward the Lanista answering to your hand.",
                "{u}Affection{/u}: overall closeness and route momentum. This is the main stage gate for both routes.",
                "{u}Corruption{/u}: how far the Lanista's old code has been eroded by coercion, ownership, and selling desire beside combat. Corruption is separate from how explicit a format is.",
                "{u}Arena Program{/u}: optional NSFW formats unlocked through authored conversations — Bikini Bouts, Oil & Chains, and The Spectacle. Every winner and yield remains authentic.",
                "{u}Owed favor{/u}: Dominion debt markers create a visible favor you may spend through {u}Collect{/u}. {u}After the crowd{/u} is ordinary intimacy and spends nothing.",
                "{u}Quick read{/u}: use {u}Take their measure{/u} during visits to see current totals and route direction in-character.",
            ],
        }

################################################################################
### LANISTA — FIRST MEETING (gender choice)
################################################################################

label lanista_first_meeting:
    $ _arena_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else "images/event_bg.png"
    scene expression _arena_bg at lanista_bg_blur
    show black as lanista_bg_dim:
        alpha 0.35
    narrator "The practice yard is all iron and chalk dust. At its center a figure stands over two sparring recruits, correcting a guard with a single clipped word, unbothered by your arrival."
    if arena_lanista_paid:
        narrator "The Master of the Sands — the same iron voice that sold you your permit without once turning from the recruits to do it."
        narrator "This time they turn, and for the first time you see the Lanista plainly."
    else:
        narrator "The figure turns, and for the first time you see the Lanista plainly."
    menu:
        "A man: broad, close-cropped, still as a drawn blade.":
            $ lanista_gender = "male"
            $ lanista_name = "Varro"
        "A woman: broad, close-cropped, still as a drawn blade.":
            $ lanista_gender = "female"
            $ lanista_name = "Varra"
    narrator "A recruit calls across the yard, and the name carries cleanly over the ring of practice steel: [lanista_name]."
    call lanista_show_emotion("neutral") from _lanista_emotion_first_meeting
    lanista_npc "I keep this yard. If you came to count coin, keep clear of the fighters while you do it."
    $ lanista_known_name = False
    return

################################################################################
### LANISTA — CHARACTER DEFINE
################################################################################

define lanista_npc = DynamicCharacter("lanista_name", color="#c98a3a")
define arena_lanista_npc = DynamicCharacter("arena_lanista_speaker_name", color="#c98a3a")

################################################################################
### LANISTA — VISIT ENTRY
################################################################################

label lanista_visit:
    if arena_lanista_paid and not arena_unlocked:
        $ add_arena_building()
    if lanista_visit_is_closed_today():
        jump lanista_gate_closed_handoff
    if not getattr(store, "lanista_gender", ""):
        if lanista_has_legacy_progress():
            # Saves from before the identity choice used the original male Lanista.
            # Preserve their established arc instead of replaying a first meeting.
            $ lanista_gender = "male"
            $ lanista_name = "Varro"
            $ lanista_known_name = True
        else:
            call lanista_first_meeting from _lanista_first_meeting_call
    if not lanista_personal_content_is_enabled():
        if arena_lanista_paid:
            jump lanista_sfw_arena_handoff
        jump lanista_sfw_permit_menu
    if lanista_ending_dominion and lanista_is_worker:
        jump arena_successor_visit
    $ maybe_show_intro_popup("lanista_visit")
    # Save compatibility: older saves know the selected portrait but predate
    # the dynamic speaker name.
    $ lanista_name = "Varra" if lanista_gender == "female" else "Varro"
    $ lanista_visit_count += 1
    if lanista_spectacle_arc_step == 0 and "s2_t1" in lanista_s2_talks_done:
        $ lanista_spectacle_arc_step = 1
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
    $ arena_prepare_lanista_speaker()
    call arena_deliver_pending_feedback from _lanista_pending_arena_feedback
    if lanista_weekly_cut_available():
        call lanista_weekly_cut from _lanista_weekly_cut_call
    jump lanista_visit_menu

# ── Devotion perk: the champion's cut (once per week, does not close the visit)
label lanista_weekly_cut:
    $ _total_days = calculate_total_days()
    $ lanista_weekly_cut_last_day = _total_days
    call lanista_show_emotion("warm") from _lanista_emotion_weekly_cut
    # Two rotating variants, chosen by the parity of the paying day — no new
    # state var, matching the wager/aftercrowd variant convention.
    if _total_days % 2 == 0:
        narrator "Before you can say your piece, [lanista_name] crosses to the strongbox behind the whetstone and counts a stack of coin onto the bench between you."
        lanista_npc "The house had a good week on the sand. This is your share of the gate — the owner's cut, same as any other partner would take."
        narrator "[lanista_name] pushes it your way without ceremony, the way one settles an honest account."
    else:
        narrator "[lanista_name] sets the ledger aside the moment you arrive and slides a folded cloth of coin across to you first, business before greeting."
        lanista_npc "Your part of the takings. I keep the sands and the books, but the arena's profit was never mine alone — you'll have what's yours."
        narrator "The weight of it settles in your palm, warm from the counting-room and heavier than a week's polite affection."
    $ money += 150
    $ renpy.notify("The champion's cut: +150 coins (purse: {})".format(money))
    return

label arena_successor_visit:
    $ arena_prepare_lanista_speaker()
    call arena_restore_successor_scene from _arena_restore_successor_visit
    if not arena_successor_met:
        $ _former_name = "Varra" if lanista_gender == "female" else "Varro"
        narrator "The trophy shelf in the old office is still bare — that story ended before the handover. A new keeper waits behind the desk, appointed to hold the sands while the former master belongs elsewhere."
        arena_lanista_npc "[_former_name] left this ring in my keeping. The Arena answers to you; the fighters answer to me while they stand on its sand."
        $ arena_successor_met = True
    else:
        arena_lanista_npc "The sands are running. What do you need?"
    call arena_deliver_pending_feedback from _arena_successor_pending_feedback
    jump arena_successor_menu

label arena_successor_menu:
    menu:
        arena_lanista_npc "The Arena is in order."
        "Ask about special matches.":
            arena_lanista_npc "One special match each week. Read the opponent, call the exchanges, and choose a fighter you can afford to lose. Five victories earn the crown."
            jump arena_successor_menu
        "Leave.":
            hide lanista_bust
            hide lanista_bg_dim
            window hide
            $ renpy.show_screen("map_screen")
            $ renpy.show_screen("arena_menu")
            jump tavern_screen

label arena_deliver_pending_feedback:
    $ _arena_feedback = getattr(store, "arena_lanista_feedback_pending", None)
    if not hasattr(_arena_feedback, "get"):
        return
    $ arena_lanista_feedback_pending = None
    $ _crit = int(_arena_feedback.get("critical_successes", 0) or 0)
    $ _wins = int(_arena_feedback.get("successes", 0) or 0)
    $ _middling = int(_arena_feedback.get("mediocres", 0) or 0)
    $ _losses = int(_arena_feedback.get("failures", 0) or 0)
    $ _setbacks = _middling + _losses
    $ _standout = str(_arena_feedback.get("standout_worker", "") or "")
    $ _concern = str(_arena_feedback.get("concern_worker", "") or "")
    if _crit > 0 and _setbacks > 0:
        if _standout and _concern:
            arena_lanista_npc "[_standout] ruled the sand, but [_concern] gave me reason to worry."
        else:
            arena_lanista_npc "One fighter ruled the sand, but another exposed a weakness that still needs work."
    elif _crit > 0 and _standout:
        arena_lanista_npc "[_standout] ruled the sand yesterday. That was not merely a win; the crowd will remember the name."
    elif _wins > 0 and _losses == 0 and _middling == 0:
        arena_lanista_npc "Your fighters held the sand cleanly yesterday. Good footing, clear heads, no one carried out. Keep that standard."
    elif _losses > 0 and _concern:
        arena_lanista_npc "[_concern] broke badly yesterday. Some of your fighters held, but that weakness will draw blood again if you leave it untended."
    elif _middling > 0 and _concern:
        arena_lanista_npc "[_concern] survived the work yesterday, nothing more. The sand exposed what training still owes them."
    else:
        arena_lanista_npc "The latest bouts are accounted for. Your fighters did enough to leave the sand under their own power."
    return

################################################################################
### LANISTA — GATED VISIT MENU
################################################################################

label lanista_visit_menu:
    if lanista_visit_is_closed_today():
        jump lanista_gate_closed_handoff
    if not lanista_personal_content_is_enabled():
        if arena_lanista_paid:
            jump lanista_sfw_arena_handoff
        jump lanista_sfw_permit_menu
    call lanista_restore_visit_scene from _lanista_restore_menu
    $ _total_days = calculate_total_days()
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    if lanista_s4_gate_fired and not lanista_morning_after_done:
        $ lanista_morning_after_done = True
        jump lanista_morning_after
    $ _story = lanista_story_state()
    $ _story_ready = bool(_story.get("ready", False))
    $ _story_action = _story.get("action", "")
    $ _story_target = _story.get("target", None)
    $ _story_day_free = not lanista_story_cooldown_active()
    $ _talk = lanista_next_talk_state()
    $ _talk_action = _talk.get("action", "Talk.")
    $ _talk_target = _talk.get("target", "lanista_talk_generic")
    # Only closing/night talks obey the narrative day-of-silence. Daytime talks
    # (and the generic filler) stay available through the cooldown, gated solely
    # by the once-per-day talk clock.
    $ _talk_closes_visit = _talk.get("closes_visit", False)
    $ _talk_free = lanista_last_talk_total_days != _total_days and (not _talk_closes_visit or _story_day_free)
    # When the only pending Talk is a closing/night Talk held back by the
    # narrative cooldown, the day would otherwise have no conversation at all.
    # The ambient filler steps into that gap (once per day, never a closer), so
    # the quiet day still reads as lived-in instead of an empty visit.
    $ _filler_free = lanista_last_talk_total_days != _total_days and _talk_closes_visit and not _story_day_free and not _story_ready
    $ _remark_free = lanista_last_question_total_days != _total_days
    $ _evening = lanista_evening_state()
    $ _s1_rem = len(lanista_s1_remarks_done) < 3
    $ _s2_rem = not _s1_rem and lanista_stage >= 2 and len(lanista_s2_remarks_done) < 2
    $ _s3_rem = not _s1_rem and not _s2_rem and lanista_stage >= 3 and len(lanista_s3_remarks_done) < 2
    $ _s4_rem = not _s1_rem and not _s2_rem and not _s3_rem and lanista_stage >= 4 and len(lanista_s4_remarks_done) < 2
    $ _s5_rem = not _s1_rem and not _s2_rem and not _s3_rem and not _s4_rem and lanista_stage >= 5 and len(lanista_s5_remarks_done) < 2
    menu:
        lanista_npc "..."
        "Buy the Arena permit ([LANISTA_PERMIT_COST] coins)." if not arena_lanista_paid:
            jump lanista_buy_arena_permit
        "[_story_action]" if _story_ready:
            $ lanista_mark_story_event()
            jump expression _story_target
        "[_talk_action]" if _talk_free and not _story_ready:
            if _talk_closes_visit:
                $ lanista_mark_story_event()
            jump expression _talk_target
        "Talk." if _filler_free and not _story_ready:
            jump lanista_filler_talk
        "Talk." if not _talk_free and not _filler_free and not _story_ready:
            if _talk_closes_visit and lanista_story_cooldown_active():
                lanista_npc "Not today, [_ttl]. I've the house to run and the sand won't sweep itself. Come back tomorrow and we'll take it up where we left it."
            else:
                lanista_npc "I've given you words enough today. Come back when the sun's moved."
            if _evening.get("aftercrowd", False):
                call lanista_show_emotion("warm") from _lanista_emotion_talk_dismiss_aftercrowd
                lanista_npc "...Unless you've a mind to stay past the gate, once the work's done and the crowd's gone. That door I don't bar to you, [_ttl]."
                menu:
                    "Stay after the crowd. (ends the visit)":
                        jump lanista_aftercrowd
                    "Not tonight.":
                        lanista_npc "Then off with you before the gate-count starts."
                        jump lanista_visit_menu
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
        "About the Arena." if arena_unlocked:
            jump lanista_arena_topics
        "Bring a gift." if lanista_last_gift_total_days != _total_days:
            jump lanista_gift
        "Take their measure.":
            jump lanista_assess
        "Speak about the arrangement." if lanista_ending_mixed and lanista_ending_done:
            jump lanista_renegotiate_arrangement
        "Leave.":
            hide lanista_bust
            hide lanista_bg_dim
            window hide
            $ renpy.show_screen("map_screen")
            if arena_unlocked:
                $ renpy.show_screen("arena_menu")
            jump tavern_screen

label lanista_arena_topics:
    if lanista_visit_is_closed_today():
        jump lanista_gate_closed_handoff
    if not lanista_personal_content_is_enabled():
        jump lanista_sfw_arena_handoff
    if not arena_unlocked:
        jump lanista_visit_menu
    call lanista_restore_visit_scene from _lanista_restore_arena_topics
    $ _total_days = calculate_total_days()
    $ _evening = lanista_evening_state()
    $ _finance_avail = arena_unlocked and lanista_stage >= 4 and lanista_debt_finance_unlocked and lanista_finance_purchase_available()
    $ _monthly_purse_avail = arena_unlocked and money >= 1000 and lanista_monthly_purse_available()
    $ _arena_arc_next = lanista_arena_arc_next_step()
    # The daytime arc step (3) stays open through the menu without closing the
    # visit. The nocturnal arc steps (2 & 4) borrow lanista_evening_state's
    # availability, carry the " (ends the visit)" suffix, and mark the story
    # event. These side closers stay visible even while a gate/night Talk is
    # waiting: every one exits immediately via lanista_gate_exit_to_map, so the
    # player simply chooses one closer and the visit ends — no chaining is
    # possible, and the persuasion/format/collect arc is no longer starved of
    # days in S4/S5 when every pending Talk is itself a closer.
    $ _arc_daytime_avail = arena_unlocked and _arena_arc_next == 3 and lanista_spectacle_arc_last_day != _total_days
    $ _arc_nocturnal_avail = bool(_evening.get("arena_arc", False))
    $ _arc_avail = _arc_daytime_avail or _arc_nocturnal_avail
    $ _arc_ends_visit = _arc_nocturnal_avail
    $ _arc_label = "Discuss the Arena's future." + (" (ends the visit)" if _arc_ends_visit else "")
    $ _format_avail = bool(_evening.get("arena_format", False))
    $ _collect_avail = bool(_evening.get("collect", False))
    $ _wager_avail = arena_unlocked and not arena_uses_successor() and lanista_wager_available()
    menu:
        lanista_npc "The house, the book, the debt. Which part?"
        "Pay down the Arena's debts." if _finance_avail:
            jump lanista_debt_favor
        "Advance the Arena's monthly purse. (1000 coins)" if _monthly_purse_avail:
            jump lanista_monthly_purse
        "[_arc_label]" if _arc_avail:
            if _arc_ends_visit:
                $ lanista_mark_story_event()
            jump lanista_arena_arc
        "Expand the Arena program. (ends the visit)" if _format_avail:
            $ lanista_mark_story_event()
            jump lanista_arena_format
        "Collect a favor ([lanista_favor_balance] owed). (ends the visit)" if _collect_avail:
            jump lanista_collect
        "Back a fighter. (Wager)" if _wager_avail:
            jump lanista_wager_menu
        "Back.":
            jump lanista_visit_menu

label lanista_evening_topics:
    if lanista_visit_is_closed_today():
        jump lanista_gate_closed_handoff
    if not lanista_personal_content_is_enabled():
        jump lanista_sfw_arena_handoff
    if lanista_main_story_closes_visit():
        jump lanista_visit_menu
    call lanista_restore_visit_scene from _lanista_restore_evening_topics
    $ _evening = lanista_evening_state()
    if not any(_evening.values()):
        jump lanista_visit_menu
    menu:
        lanista_npc "Choose one; any option ends the visit."
        "Discuss the Arena's future." if _evening.get("arena_arc", False):
            $ lanista_mark_story_event()
            jump lanista_arena_arc
        "Expand the Arena program." if _evening.get("arena_format", False):
            $ lanista_mark_story_event()
            jump lanista_arena_format
        "Collect a favor ([lanista_favor_balance] owed)." if _evening.get("collect", False):
            jump lanista_collect
        "After the crowd." if _evening.get("aftercrowd", False):
            jump lanista_aftercrowd
        "Back.":
            jump lanista_visit_menu

label lanista_sfw_permit_menu:
    call lanista_restore_visit_scene from _lanista_restore_sfw_permit
    menu:
        lanista_npc "The Arena permit costs [LANISTA_PERMIT_COST] coins. Paper first; the opening trial follows on the sand."
        "Buy the Arena permit ([LANISTA_PERMIT_COST] coins).":
            jump lanista_buy_arena_permit
        "Leave.":
            hide lanista_bust
            hide lanista_bg_dim
            window hide
            $ renpy.show_screen("map_screen")
            jump tavern_screen

label lanista_sfw_arena_handoff:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ renpy.show_screen("map_screen")
    $ renpy.show_screen("arena_menu")
    jump tavern_screen

label lanista_gate_exit_to_map:
    $ lanista_gate_closed_total_days = calculate_total_days()
    # Every night closer (the eight talks, the gates, the night Arena scenes,
    # Collect and After the Crowd) funnels through here, so the deliberate
    # click-and-fade that ends the evening lives in one place.
    window hide
    scene black with Dissolve(0.6)
    pause
    hide lanista_bust
    hide lanista_bg_dim
    $ renpy.show_screen("map_screen")
    if arena_unlocked:
        $ renpy.show_screen("arena_menu")
    jump tavern_screen

label lanista_gate_closed_handoff:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ renpy.notify("The Lanista has finished receiving visitors for today. The Arena remains open.")
    $ renpy.show_screen("map_screen")
    if arena_unlocked:
        $ renpy.show_screen("arena_menu")
    jump tavern_screen

label lanista_buy_arena_permit:
    call lanista_restore_visit_scene from _lanista_restore_permit
    if arena_lanista_paid:
        if not lanista_personal_content_is_enabled():
            jump lanista_sfw_arena_handoff
        jump lanista_visit_menu
    if money < LANISTA_PERMIT_COST:
        lanista_npc "Your purse is too light. The permit costs [LANISTA_PERMIT_COST] coins. Fixed."
        lanista_npc "Come back when you can meet it."
        if not lanista_personal_content_is_enabled():
            jump lanista_sfw_permit_menu
        jump lanista_visit_menu
    $ money -= LANISTA_PERMIT_COST
    $ arena_lanista_paid = True
    $ arena_trial_completed = False
    $ add_arena_building()
    lanista_npc "Done. The coin is received; the ledger is satisfied."
    lanista_npc "Paper opens the gate. The Arena is yours to use."
    if not lanista_personal_content_is_enabled():
        lanista_npc "The opening trial waits on the sand. Pass it, and ordinary Arena operations are yours."
        jump lanista_sfw_arena_handoff
    lanista_npc "The opening trial waits on the sand when you are ready. Keep the combat business at the gate — this bench deals in other things."
    jump lanista_visit_menu

################################################################################
### LANISTA — STAGE ROUTERS & SCENES
################################################################################

label lanista_s2_gate:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ lanista_night_visit_total_days = calculate_total_days()
    $ _s2_bridge_bg = "images/buildings/bg_arena_night.jpg"
    if not renpy.loadable(_s2_bridge_bg):
        $ _s2_bridge_bg = "images/buildings/arena.png" if renpy.loadable("images/buildings/arena.png") else "images/event_bg.png"
    scene expression _s2_bridge_bg
    show black as lanista_bg_dim:
        alpha 0.15
    with dissolve
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _s2_bridge_bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_s2_bridge_bust):
        show expression _s2_bridge_bust as lanista_bust at lanista_bust_right
    window show
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The last practice bout ends, but no clerk comes to hurry you from the yard. For the first time, the closing gate falls behind you rather than between you and the Arena."
    narrator "[lanista_name] dismisses the recruits, hangs the practice blade on its peg, and leaves a second cup beside the bench without asking whether you intend to stay."
    if lanista_remark_choice("s1_r1") == "devotion":
        lanista_npc "You counted my scars as lessons, not prices. I remembered that."
    elif lanista_remark_choice("s1_r1") == "dominion":
        lanista_npc "You called my scars a ledger and looked for the weak seam. I remembered that too."
    else:
        lanista_npc "You kept your counsel about the scars. I noticed the silence too."
    lanista_npc "You were meant to be another purse at the rail, [_ttl]. A visitor with figures in the head and no sand in the blood."
    call lanista_show_emotion("warm") from _lanista_emotion_s2_gate_warm
    lanista_npc "But you keep coming back after the count is done. You watch the hands, the feet, the craft. So hear the answer I would not give you before."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s2_gate_vuln
    lanista_npc "The seal you saw was one lender. The Arena owes three."
    lanista_npc "I will not open the ledger tonight. First you will hear what those debts are making me sell on the sand, and what this sand has already taken from me."
    lanista_npc "After that, I will put every figure in front of you."
    narrator "It is not trust. Not yet. It is the deliberate opening of ground that was closed before — one fighter conceding that you may stand inside the circle."
    $ lanista_s2_gate_fired = True
    jump lanista_gate_exit_to_map

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
    call lanista_show_emotion("amused") from _lanista_emotion_s1_t1
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
            call lanista_show_emotion("neutral") from _lanista_emotion_s1_t1_dom
            lanista_npc "A coin-counter who's done the counting. Of course."
            lanista_npc "The seats are my concern, [_ttl]. Keep your arithmetic to your own ledger."
    $ lanista_s1_talks_done = list(lanista_s1_talks_done) + ["s1_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_s1_talk_2:
    call lanista_show_emotion("angry") from _lanista_emotion_s1_t2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Below, an honest bout runs its course — two journeymen, evenly matched, trading nothing pretty, only true. In the stands whole rows sit empty. The good seats fill for the maimings, not for this."
    lanista_npc "Look at that. Two of the finest blades in the province, and the benches are bare."
    lanista_npc "They'd be packed shoulder to shoulder if I'd promised a cripple by sundown."
    menu:
        "\"A full house forgets you by morning. Honor outlasts it.\"":
            $ lanista_devotion += 2
            $ lanista_affection += 2
            narrator "The Lanista watches the bout a moment longer before answering, as if checking your words against the men on the sand."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s1_t2_dev
            lanista_npc "Outlasts it. Aye. I've buried fighters the crowd once cheered for, only to see those same names forgotten within a week."
            lanista_npc "You've sat in cheaper seats than your purse suggests, [_ttl]. I'll grant you that."
        "\"The crowd pays for blood, not virtue. Sell them blood.\"":
            $ lanista_dominion += 2
            $ lanista_affection += 2
            $ lanista_corruption += 2
            narrator "The Lanista turns from the fight to you. No anger in it — something colder. The look of a fighter who has heard the truth and dislikes the mouth it came from."
            call lanista_show_emotion("neutral") from _lanista_emotion_s1_t2_dom
            lanista_npc "Spoken like someone who's never had to wash the sand after."
            lanista_npc "You're not wrong, [_ttl]. That's the trouble with you. You're not wrong."
    $ lanista_s1_talks_done = list(lanista_s1_talks_done) + ["s1_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_s1_talk_3:
    call lanista_show_emotion("angry") from _lanista_emotion_s1_t3
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A clerk leaves a stack of papers on the bench by the weapons rack and hurries off at a barked order. The top sheet has slid loose."
    narrator "You catch the press of a seal in the wax — a moneylender's mark, the kind that does not send its letters twice."
    lanista_npc "..."
    narrator "The Lanista follows your eyes to the page. For half a breath, the whole room seems to brace around it. Then a broad hand turns the sheet face-down without hurry."
    lanista_npc "That page is Arena business, [_ttl] — and none of yours. Keep your eyes on the sand."
    menu:
        "\"Fair enough. But debt is my trade — if that seal ever wants a second pair of eyes, my door is open.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "The hand stays flat on the paper. The Lanista studies you the way one studies an unfamiliar guard — hunting the feint inside the open stance."
            call lanista_show_emotion("neutral") from _lanista_emotion_s1_t3_dev
            lanista_npc "A second pair of eyes. Everyone offers eyes, [_ttl]. Then the bill comes due in something that isn't coin."
            lanista_npc "...I'll remember the offer, [_ttl]. That is not the same as taking it. But I'll remember."
        "\"If that debt can close the Arena, it matters to anyone considering its future. How deep does it run?\"":
            $ lanista_dominion += 3
            $ lanista_affection += 1
            narrator "The question makes your interest plain: not sympathy, but the price and future of the Arena itself. [lanista_name] hears both parts."
            lanista_npc "There it is. Not curiosity — valuation. You're looking at my walls and wondering what a lender could force me to sell."
            lanista_npc "You haven't earned the whole number yet, [_ttl]. Keep coming back, and perhaps I'll decide whether showing it to you is safer than hiding it."
    $ lanista_debt_finance_unlocked = True
    $ lanista_s1_talks_done = list(lanista_s1_talks_done) + ["s1_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
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
    call lanista_show_emotion("angry") from _lanista_emotion_s2_t1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You wait for a lull between bouts and lay the idea out plainly. Give the crowd a story to follow: a rivalry, a near-loss, a turn they can feel coming."
    narrator "Real steel underneath, but the shape agreed before either fighter touches the sand."
    lanista_npc "Staged."
    narrator "The word lands flat. The Lanista sets down the whetstone and looks at you as a smith studies the first crack through good metal."
    lanista_npc "I sell true bouts. The fighter who falls, falls because the other was better. That is the whole of what people trust about this place."
    lanista_npc "You're asking me to score the iron and call it craft."
    lanista_npc "Fix one fall and the stink does not stay on that night. The crowd looks backward. Every honest victory becomes a question. Every dead champion becomes a possible liar."
    lanista_npc "And before you cheat a single spectator, you cheat the fighter. Order someone to fall and you steal their name, their judgment, their mastery. You turn a life of training into your cue."
    menu:
        "\"The steel stays real. The story only teaches the crowd where to look.\"":
            $ lanista_devotion += 2
            $ lanista_affection += 2
            narrator "You try to preserve the bout by separating the frame from the result. The Lanista does not grant you the distinction."
            lanista_npc "If the turn is promised, the fighter is serving the promise. The steel may bite, but the mastery is counterfeit."
        "\"The men holding your debt don't care how honest the seats were when they sat empty.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            narrator "That stops the breath in the yard. The debt bites, but it does not move the line drawn across the Lanista's face."
            lanista_npc "Low, [_ttl]. Accurate, and low."
            lanista_npc "Let the lenders own my sleep. They do not get to own a fighter's fall through me."
    lanista_npc "The answer is no. Bring me a way to fill the benches without telling the sand what truth it must produce, and I will hear it. Not this."
    narrator "You have no clean answer. The whetstone returns to the blade, and the line remains where the Lanista drew it."
    $ lanista_spectacle_arc_step = max(lanista_spectacle_arc_step, 1)
    $ lanista_spectacle_arc_last_day = calculate_total_days()
    $ lanista_s2_talks_done = list(lanista_s2_talks_done) + ["s2_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_s2_talk_2:
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s2_t2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The Lanista favors one leg crossing the yard — a small hitch, easy to miss, never absent. You ask about it, and for once the question is not turned aside."
    lanista_npc "Eleven seasons on this sand. Champion for six of them. People forget that, looking at the rag and the whetstone."
    lanista_npc "There was a Nordmark brute they shipped down to end my run. Reach like a gate-beam, patient as winter. We went three turns of the glass. Longest bout this Arena ever sold out twice over."
    narrator "A hand drifts to the bad knee without the Lanista seeming to notice — the body remembering what the voice keeps level."
    lanista_npc "I won. Put him down clean. His last swing drove the knee sideways. The bone knitted, but the joint never held true again."
    lanista_npc "You don't fight on a knee that folds. So you teach. You manage. You learn to love the count."
    menu:
        "\"Three turns of the glass against a giant. That isn't luck. That's mastery.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "The Lanista holds your eye, hunting the flattery in it, and does not find the shape expected."
            lanista_npc "Mastery. Aye, it was. I don't say it loud — said loud, it's just an old fighter grieving the young one they buried."
            lanista_npc "You'd have liked the fighter I was, [_ttl]. Some days I think you'd have liked them better than what's left."
        "\"The leg healed, but the crown didn't. That has to gnaw at you.\"":
            $ lanista_dominion += 2
            $ lanista_affection += 2
            narrator "Something shutters behind the Lanista's face — you have set a thumb on the old bruise, and you have done it on purpose, and you are both aware of it."
            call lanista_show_emotion("neutral") from _lanista_emotion_s2_t2_dom
            lanista_npc "Gnaw. There's a word. You went looking for the soft place and found it on the first try."
            lanista_npc "It gnaws, [_ttl]. Every step. Now you know where to press. And I know that you went looking."
    $ lanista_s2_talks_done = list(lanista_s2_talks_done) + ["s2_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_s2_talk_3:
    call lanista_show_emotion("neutral") from _lanista_emotion_s2_t3
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "This time the Lanista does not turn the page over. The ledger lies open on the bench, and you are not waved off when you step close enough to read it."
    narrator "You already knew the number: three lenders. The open ledger gives each one a name, a date, and a claim against the Arena."
    narrator "The number is familiar. Its shape is not — three separate hands closing around the same failing house, each preserved in the Lanista's cramped, honest script."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s2_t3_open
    lanista_npc "Now you've seen it. The whole of it. Not the polite version — the one that keeps me awake."
    lanista_npc "I let you read it because I am tired of being the only set of eyes on it. Make of that what you will."
    menu:
        "\"Then you're not the only set of eyes anymore. We carry it together — shoulder to shoulder.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "The Lanista looks from the book to you, and the stillness this time is not a wall. It is the pause before setting down a weight carried too long alone."
            call lanista_show_emotion("warm") from _lanista_emotion_s2_t3_dev
            lanista_npc "Together. You say it like it's simple. It never is."
            lanista_npc "...But you're standing on my side of the bench to say it. Nobody's done that in a long while, [_ttl]. Stay on this side, then. There's room on the bench."
        "\"Then let me buy in. My coin clears those columns — and my voice sits at this bench from now on.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 3
            $ lanista_corruption += 1
            narrator "The offer is clean, and the price folded inside it is clean too. The Lanista reads both at once — the rope thrown, and the hand that will hold the other end of it ever after."
            call lanista_show_emotion("neutral") from _lanista_emotion_s2_t3_dom
            lanista_npc "Your coin. Your voice. The columns clear, and a piece of the sand answers to you instead of me."
            lanista_npc "It's a fair trade. That's what makes it dangerous. ...I hear you, [_ttl]. We're not done settling the shape of it — but I hear you."
    $ lanista_s2_talks_done = list(lanista_s2_talks_done) + ["s2_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
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
    call lanista_show_night_exterior from _lanista_night_exterior_s3_t1
    call lanista_show_emotion("angry") from _lanista_emotion_s3_t1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The last torch-bearers have gone. The Arena sits empty under a low moon, the sand raked smooth, the benches a pale ring of nothing."
    narrator "The night's gate-count was thin — you watched the Lanista's jaw set tighter with every bare row, and tonight there were many."
    narrator "You expect to be waved off with the rest. Instead the Lanista says nothing, and the silence is permission to stay."
    lanista_npc "Eleven seasons I've stood in this bowl. Heard it roar. Heard it like this."
    lanista_npc "There's a number the lenders want by the turn of the season. Tonight's take didn't move it. Neither did last night's."
    narrator "The Lanista looks out across the empty tiers — and for the space of a breath, the stillness isn't control. It's a fighter on a ledge, measuring the drop."
    lanista_npc "I have buried fighters and not flinched. The thought of locking that gate for the last time — that one I flinch at. I'll say it once, here, where no one's counting but you."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s3_t1_confess
    menu:
        "\"Then I'll stand here with you. No pitch, no terms. Just here.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "You say nothing else. You only stay — shoulder to the same cold air, watching the same empty seats. The Lanista doesn't thank you. The shoulders ease a fraction, and that is louder than thanks."
            call lanista_show_emotion("warm") from _lanista_emotion_s3_t1_dev
            lanista_npc "...No agenda. You came all this way to a dying house and brought no agenda."
            lanista_npc "Stay, then, [_ttl]. The company's better than the arithmetic."
        "\"This place doesn't have to fall. I can move that number — and you'll know who moved it.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            narrator "The Lanista turns from the empty tiers to you, and the ledge-look folds back into something harder. You have offered a rope, and let them see the hand that holds the far end of it."
            call lanista_show_emotion("angry") from _lanista_emotion_s3_t1_dom
            lanista_npc "You'd move it. And every season after, I'd hear the sound of your coin under the cheering."
            lanista_npc "...The gate stays open either way. That's the part I can't argue with. I hear you, [_ttl]. I hear exactly what you're offering."
    $ lanista_s3_talks_done = list(lanista_s3_talks_done) + ["s3_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_s3_talk_2:
    call lanista_show_emotion("warm") from _lanista_emotion_s3_t2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The whetstone goes quiet. The Lanista works a knot in one shoulder, winces, and then makes a decision."
    narrator "The collar pulls aside to reveal the pale rope of a scar, thick as a finger and old as the crown that came with it."
    lanista_npc "The Nordmark gave me this one. Third turn of the glass. Had me against the boards, and the blade went in here."
    narrator "A scarred hand takes yours before you think to offer it, and lays your fingers along the seam of it. The skin is warm, the ridge of it strange under your touch."
    narrator "Neither of you moves for a breath too long to be an accident."
    lanista_npc "I kept my feet. Bled half the sand red and kept my feet. That's the whole secret of this craft. You stay standing when the body's begging you to fall."
    menu:
        "\"You've carried enough alone. You don't have to stand for me.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "You don't pull your hand back. You let it rest, gentle, over the worst of the scar — not measuring it now, only holding it."
            narrator "The Lanista goes very still, the way one does at the edge of something that can't be taken back."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s3_t2_dev
            lanista_npc "...That's a dangerous thing to offer a fighter, [_ttl]. We don't know how to be carried. We only know how to stand."
            lanista_npc "But I felt that. I'll not pretend I didn't."
        "\"And you're still standing. Let's see if the strength's still in it.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            narrator "You close your hand on the scarred shoulder and press — testing, challenging, the way one fighter sizes another. The Lanista meets it, muscle going hard under your palm, jaw set, refusing the inch."
            narrator "The air between you draws tight as a bowstring."
            call lanista_show_emotion("angry") from _lanista_emotion_s3_t2_dom
            lanista_npc "Still here. Push all you like. This shoulder's outlasted better hands than yours."
            lanista_npc "...Though you've nerve, laying hands on me like that. Most don't dare. I find I don't mind that you did, [_ttl]."
    $ lanista_s3_talks_done = list(lanista_s3_talks_done) + ["s3_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_s3_talk_3:
    call lanista_show_night_interior from _lanista_night_s3_t3
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s3_t3
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You've come too many evenings now for it to be business. The Lanista sets the rag down — folds it, even, which is not a thing done idly — and faces you square across the bench."
    lanista_npc "I'm going to name a thing, and you're going to tell me which it is. I've earned plain dealing, even if I've forgotten how to ask for it."
    lanista_npc "You keep turning up. A purse like yours doesn't haunt a failing Arena for the sport. So which is it, [_ttl] — charity, appetite, or leverage?"
    narrator "The question hangs in the lamplight. The Lanista's gaze doesn't waver, and for once there's no armor in it."
    narrator "Only the want to know, and the readiness to take any of the three answers like a blow already braced for."
    menu:
        "\"I want you. Not the Arena. You.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "The word lands and the Lanista takes it standing, the way every blow on that sand was taken."
            narrator "But the breath goes out slow, and something behind the eyes that has been clenched for years unclenches by a fraction."
            lanista_npc "Me. Not the sand, not the craft, not the crown I used to wear. ...You picked the one answer I had no guard against."
            lanista_npc "Say it again sometime, when I've the nerve to hear it. You said it first, [_ttl]. That's a debt I don't mind carrying."
        "\"I want both. The Arena and the one who holds it. And I can have both.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 3
            $ lanista_corruption += 1
            narrator "No flinch. The Lanista weighs the answer the way a fighter weighs an opponent who's just shown they fight to win — wary, and not entirely displeased to have found a worthy one."
            call lanista_show_emotion("neutral") from _lanista_emotion_s3_t3_dom
            lanista_npc "Both. The honest answer and the dangerous one. You want the house and the one standing in it, and you don't see a line between."
            lanista_npc "...Most would dress that up softer. You didn't. I'll give you this — I'd rather a clean blade than a kind lie. Come closer, then, [_ttl]. Let's see what you can hold."
    $ lanista_s3_talks_done = list(lanista_s3_talks_done) + ["s3_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

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
    call lanista_show_night_interior from _lanista_night_s4_t1
    call lanista_show_emotion("angry") from _lanista_emotion_s4_t1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "The Lanista is alone in the night armory when you find [_them], a slip of paper in one hand, the night's card already spread across the workbench."
    narrator "One name on that card shouldn't be there, and you both know it — a young fighter with a knee that never set right since the spring."
    narrator "Matched against a Nordmark bruiser who will find that knee inside three passes."
    lanista_npc "Don't. Whatever you came to say. I can read a card better than you, and I'm the one who wrote this one."
    narrator "The Lanista sets the slip down with a care that plainly costs something. There is a taste in the room like a blade left out in salt air — and it is on the Lanista's face, not yours."
    lanista_npc "The lenders want bodies the crowd will pay to watch bleed. The boy draws a house. A sound fighter who'd win clean doesn't fill a bench. So I put the lame one on the sand and I call it a card."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s4_t1_confess
    lanista_npc "Eleven seasons I never sold a bout I knew the end of. Tonight I priced one. ...That's the first cut that's gone all the way through. I wanted you to hear it from me, before you heard it from the cheering."
    menu:
        "\"Then I'll carry the weight of it with you. No judgment — just here.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You don't tell the Lanista it was wrong. [_They] already knows. You only step in close and take a measure of that weight onto your own shoulders."
            narrator "Where [_they] can see you hold it. The breath that goes out of [_them] is ragged at the edge."
            lanista_npc "No sermon. ...I braced for a sermon and you handed me a shoulder instead. I don't rightly know what to do with that."
            lanista_npc "Stay near tonight, [_ttl]. When the boy goes down, I'd sooner not be standing in it alone."
            jump lanista_s4_boy_vigil_devotion
        "\"It was necessary. The gate stays open. And there will be more like it — that's the trade now.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            $ lanista_corruption += 3
            narrator "You name the thing without softening it, and the Lanista hears the truth of it land like a verdict already passed. The slip lies on the bench between you. You do not pick it up. You don't have to."
            narrator "You let [_them] see that you would have written the same name."
            call lanista_show_emotion("angry") from _lanista_emotion_s4_t1_dom
            lanista_npc "More like it. You say it plain — the way I couldn't. ...The way I'll have to learn to."
            lanista_npc "You're right, and I hate that you're right. I'll do it again next month, and you'll be standing there when I do. That's the shape of us now, [_ttl]. I'm done pretending otherwise."
            jump lanista_s4_boy_vigil_dominion

label lanista_s4_boy_vigil_devotion:
    call lanista_show_night_cutscene from _lanista_night_s4_boy_vigil_devotion
    call lanista_show_emotion("angry") from _lanista_emotion_s4_boy_vigil_devotion
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    narrator "The roar arrives before the boy does. The crowd has understood the card and wants the ending it was promised."
    narrator "On the third pass the Nordmark bruiser stamps across the damaged knee. The boy folds hard enough that the whole front rank rises."
    narrator "The Lanista grips the rail. For one breath [_they] looks ready to vault it, old champion's law stronger than debt or office."
    narrator "Then the referee reaches ten. The healers pull the boy clear, breathing, white-faced, and unable to put weight on the leg."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s4_boy_vigil_devotion_grief
    lanista_npc "Alive. That's the word I am meant to call mercy tonight."
    narrator "You remain beside [_them] while the cheering spends itself. You offer no absolution and do not let [_them] stand alone inside the cost."
    narrator "The Lanista sends the winner's purse to the boy's surgeon before the count reaches the ledger. It will not undo the card. It is still done."
    lanista_npc "You stayed. I asked for no more than that because no more could make it clean."
    call lanista_show_emotion("yielding") from _lanista_emotion_s4_boy_vigil_devotion_rest
    narrator "When the lamps finally die, [_their] shoulder rests against yours for three quiet breaths before the old armor returns."
    lanista_npc "Go home, [_ttl]. Tomorrow I open the same gate. Tonight, at least, you saw what it cost."
    jump lanista_s4_boy_vigil_end

label lanista_s4_boy_vigil_dominion:
    call lanista_show_night_cutscene from _lanista_night_s4_boy_vigil_dominion
    call lanista_show_emotion("angry") from _lanista_emotion_s4_boy_vigil_dominion
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    narrator "The crowd recognizes the sacrifice before the boy reaches the sand. They chant for the bad knee as if pain were a fighter's second name."
    narrator "The Nordmark bruiser finds it on the third pass. The boy crumples, and the benches erupt exactly as the card promised they would."
    narrator "The Lanista moves toward the rail. Your hand closes over [_their] wrist before the old champion can interfere with the new trade."
    narrator "The referee counts ten. Healers carry the boy out breathing, his damaged leg hanging still between them."
    lanista_npc "There. A full house. You were right about the arithmetic."
    narrator "You make [_them] watch the clerks stack the night's gate beside the card. The profit is real; refusing to look would only purchase hypocrisy."
    narrator "The Lanista gives the order for another purse to the surgeon, then signs the ledger under your hand. Neither gesture erases the other."
    lanista_npc "I will remember which sound kept these gates open. Not the bell. The crowd when he fell."
    narrator "The lamps burn down with [_them] beside you, furious enough to shake and disciplined enough not to step away."
    lanista_npc "You said this was the trade. Tonight you made me stand at the counter. Do not ask me to pretend I learned nothing."
    jump lanista_s4_boy_vigil_end

label lanista_s4_boy_vigil_end:
    $ lanista_s4_talks_done = list(lanista_s4_talks_done) + ["s4_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_s4_talk_2:
    call lanista_show_night_interior from _lanista_night_s4_t2
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s4_t2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _themself = lanista_pronoun("refl")
    narrator "You find the Lanista with a cup gone cold and a tally of the last season spread across the bench — not coin this time, but bouts."
    narrator "A scarred finger moves down the column, stopping here and there, the way one counts old wounds to learn which ones still ache."
    lanista_npc "I kept a code once. Plain things. No fixed bouts. No fighter on the sand who can't be carried off it again. No spectacle I'd be ashamed to name to the dead."
    narrator "The finger stops on a line near the bottom. The Lanista doesn't read it aloud. [_They] doesn't need to. You were there for that one."
    lanista_npc "I told myself the line was the lame boy. That I'd cross that and go no further. I crossed it a month ago, and there's a new line drawn now, further down, and I can already feel the season pushing me toward it."
    lanista_npc "That's how a code dies, [_ttl]. Not in one clean blow. In small honest steps, each one swearing the next is the last. I'm taking stock of how far I've walked. The country out here isn't one I know."
    menu:
        "\"You're still you. A code that bends to keep your people fed isn't a code that broke.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You set a hand flat over the tally, covering the worst of the lines, and make the Lanista look at you instead of the column."
            narrator "There is a long quiet while [_they] weighs whether to let [_themself] believe you."
            lanista_npc "Bends, not breaks. ...You make it sound like a thing a body survives. Like I might still be standing at the end of it, and still be someone I'd shake hands with."
            lanista_npc "I needed that said, and meant. You meant it — I could tell. I'll hold to it on the nights I can't find my own face in the glass, [_ttl]."
        "\"The code was always a luxury you couldn't afford. Let it go — I'm freeing you of it.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            $ lanista_corruption += 3
            narrator "You sweep the tally aside — bouts, lines, the whole accounting of a conscience — and the Lanista watches the gesture the way a drowning fighter watches a thrown rope land just within reach."
            narrator "Lighter and more dangerous, both in the same breath."
            call lanista_show_emotion("angry") from _lanista_emotion_s4_t2_dom
            lanista_npc "A luxury. ...Half a life I wore it like armor, and you call it a thing I couldn't afford. Damn you for it. You might be right."
            lanista_npc "It is lighter without it. I'll grant you that, and I'll loathe myself for granting it, and I'll keep walking the way you're pointing all the same. You've the weight now, [_ttl]. Mind you carry it better than I did."
    $ lanista_s4_talks_done = list(lanista_s4_talks_done) + ["s4_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_s4_talk_3:
    call lanista_show_night_interior from _lanista_night_s4_t3
    call lanista_show_emotion("warm") from _lanista_emotion_s4_t3
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _theirs = lanista_pronoun("poss_pron")
    narrator "Tomorrow the Arena opens its gates to a spectacle it has never dared before — oiled bodies and thin pretense, more flesh than fight, the card that fills benches and empties the last of the old pride."
    narrator "The card is set. The new banners are sewn. There is nothing left to ready tonight, and so there is only the two of you, the lamp, and a silence stretched to the strain of breaking."
    narrator "The Lanista stands close — closer than the bench requires — and for once makes no pretense that it's about the debt, or the card."
    narrator "Or anything but the charge that has built between you across a whole season and has, tonight, nowhere left to go."
    lanista_npc "After tomorrow this house is something else. So am I. Whatever I was holding back for the sake of the fighter I used to be — there's no sense left in holding it."
    menu:
        "\"Then whatever tomorrow makes of this place, we face it together. Starting now.\"":
            $ lanista_devotion += 5
            $ lanista_affection += 4
            narrator "You close the last of the distance and the Lanista lets you — the scarred hands, that have only ever known how to stand and how to strike, learning a third thing now, slow and unsure."
            narrator "Which is how to hold. There is no crowd. There is no count. There is only this, and it is enough, and it is [_theirs] to give and yours to keep."
            lanista_npc "Together. ...Eleven seasons I stood in that bowl alone and called it strength. This is better. I'm not too proud tonight to say it's better."
            lanista_npc "Whatever the morning brings, [_ttl], it finds us already standing in it. Shoulder to shoulder. That's the one thing I'll let no lender lay a hand on."
        "\"After tomorrow the Arena is mine, and you work for me. Let's see if the old champion still knows how to take an order.\"":
            $ lanista_dominion += 5
            $ lanista_affection += 4
            $ lanista_corruption += 2
            narrator "You say it without a tremor, the way a deal is closed. The Lanista has spent a season being claimed inch by inch."
            narrator "The words meet no flinch — only the champion's jaw tightening once, the reflex of a fighter told to stand where [_they] is put."
            narrator "The hand that takes yours is a champion's hand, and it yields the grip to you knowing exactly what it yields."
            call lanista_show_emotion("yielding") from _lanista_emotion_s4_t3_dom
            lanista_npc "Work for you. ...Eleven seasons I gave the orders on that sand, and no one living ever handed me one and kept the hand."
            lanista_npc "And here you are, saying it flat, and I'm still on my feet. Still listening. That ought to trouble me more than it does, [_ttl]."
            lanista_npc "So give it — the order. I spent a life learning to hold a line. Let's both see whether I can stand on the wrong side of one and mean it."
    $ lanista_s4_talks_done = list(lanista_s4_talks_done) + ["s4_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

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
    call lanista_show_night_interior from _lanista_night_s5_t1
    call lanista_show_emotion("angry") from _lanista_emotion_s5_t1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "You find the Lanista at the bench with nothing in [_their] hands — no blade, no tally, no cup."
    narrator "Only a single sheet of heavy vellum, the Governor's wax seal broken at its foot. The room holds the particular stillness that comes before a bout one fighter already knows the end of."
    lanista_npc "Sit down, [_ttl]. You'll want to be sitting for this number."
    narrator "[_They] slides the vellum across the wood. You don't need to read the whole of it. The figure at the bottom does the talking, and beside it a date — a fortnight off."
    narrator "And the Governor's plain word for what happens when it goes unmet. The license. The gates. The name over the door. Struck from the rolls."
    lanista_npc "There it is. The real number. Not the piece of it I've fed you all season to keep your face from doing what it's doing now."
    lanista_npc "A fortnight. Pay the purse in full, or the Governor takes the Arena off the rolls and turns a life's work into an empty stable yard. I've cut my way out of worse corners than this. ...No. That's the old lie, and I'm done telling it."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s5_t1_v
    lanista_npc "There's no worse corner than this one. This is the last of the sand."
    menu:
        "\"Then we stand in it together. I'm not walking out that gate — whatever the number is, it's ours now.\"":
            $ lanista_devotion += 5
            $ lanista_affection += 4
            narrator "You don't flinch from the figure and you don't flinch from [_them]. You only set your hand flat on the vellum, over the worst of it, and stay."
            narrator "Close enough that [_they] has to look at you instead of the date."
            narrator "The breath that leaves [_them] shakes on the way out, the way a held guard shakes when it finally drops."
            lanista_npc "Ours. ...You look at the number that ends me and you call it ours. Nobody shares a sinking, [_ttl]. They get clear of it."
            lanista_npc "You're not getting clear. I can see that you mean it, and I've no armor left to argue. A fortnight, then — and you in it with me. That's more than I had an hour ago. That's more than I've had in eleven seasons."
        "\"The debt was mine the day I started covering it. This doesn't end on the Governor's date. It ends how I decide it ends.\"":
            $ lanista_dominion += 5
            $ lanista_affection += 3
            $ lanista_corruption = min(100, lanista_corruption + 2)
            narrator "You pick the vellum up, read the figure once, and set it down again without a tremor — the way a buyer prices a thing already half-owned. The Governor's date means nothing in your hand."
            narrator "You let the Lanista watch you understand that, and watch you decide it changes nothing you don't allow it to."
            call lanista_show_emotion("yielding") from _lanista_emotion_s5_t1_dom
            lanista_npc "How you decide. ...The Governor sets a date on my whole life, and you wave it off like a bad call from the stands. The maddening part is you've the standing to do it."
            lanista_npc "It's your debt. It's been your debt. I stopped owning it somewhere back there and never marked the day. So decide, then. I've nothing left to lay on the sand but the deciding, and you've taken even that."
            lanista_npc "Tell me how this ends, [_ttl]. I'll stand where you put me."
    $ lanista_s5_talks_done = list(lanista_s5_talks_done) + ["s5_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_s5_talk_2:
    call lanista_show_night_interior from _lanista_night_s5_t2
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s5_t2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _themself = lanista_pronoun("refl")
    narrator "The high shelf behind the rack is bare. The victor's wreaths, the bronze tokens, the grey-dusted glory of fighters who mattered."
    narrator "Gone, sold off in a lot to a collector who paid in the kind of coin a fortnight demands. The Lanista stands looking at the empty board where eleven seasons used to sit."
    lanista_npc "Sold the trophies this morning. Didn't dent the number. Funny thing — it didn't hurt going. I thought it would. I think I'd used it all up grieving on the road to the buyer's door."
    narrator "[_They] turns, and the look on the hard face is one you haven't seen there — not the iron, not the dry cut of the wit. Something quieter."
    narrator "A fighter standing over a body and recognizing the face."
    lanista_npc "There was someone who held this place once. Eleven seasons unbeaten in the manner that mattered — never a sold bout, never a fighter on the sand who couldn't be carried off it. That one would have spat on the cards I run now."
    lanista_npc "That fighter would have put a fist through the new banners."
    lanista_npc "That one's dead, [_ttl]. I'm what's standing in the armor after. And I miss them. The way you miss a friend you had to leave on the field, because carrying them would have got you both killed."
    menu:
        "\"It wasn't a fall. It was survival. And I still see the fighter under the armor — they're not as gone as you think.\"":
            $ lanista_devotion += 5
            $ lanista_affection += 4
            narrator "You take the hard jaw in your hand and make [_them] hold your eye, the way [_they] once reset a recruit's grip."
            narrator "Patient, exact. You tell [_them] you see it. Not the lanista who sells the sand. The fighter underneath, who hated every cut it took to keep the house standing."
            narrator "The breath [_they] lets go is ragged at its very edge."
            lanista_npc "Still there. ...You say it like you've laid eyes on them. Like they didn't go in the ground with the code."
            lanista_npc "Maybe that's the cruelest mercy you've shown me yet — telling me the one I buried still draws breath under all this. I'll not unhear it now. I'll go looking for that face in the glass, on the bad nights."
            lanista_npc "And I'll be looking because of you, [_ttl]."
        "\"The code was dead weight from the start. You're lighter without it — and you know exactly who cut it loose.\"":
            $ lanista_dominion += 5
            $ lanista_affection += 3
            $ lanista_corruption += 2
            narrator "You don't grieve the champion with [_them]. You bury the body plainly, and you name the gravedigger."
            narrator "The code was a stone [_they] had carried for years because no one had ever told [_them] to set it down."
            narrator "You told [_them]. You watch the truth of it land — and watch the awful relief come in behind it."
            narrator "The relief [_they] will hate [_themself] for feeling."
            lanista_npc "Dead weight. ...You'll stand over the corpse of the only thing I was proud of and call it a load I'm well shut of. And the hell of it is the load's gone and I can breathe."
            lanista_npc "You cut it loose. I'll not pretend it was my hand on the knife — it was yours, and I held still for it. Lighter. Freer. Worse, by every measure that one would have used."
            lanista_npc "But that one's gone, and you're here, and I'd sooner be your creature than their ghost. There's the bottom of me, [_ttl]. You dug it up."
    $ lanista_s5_talks_done = list(lanista_s5_talks_done) + ["s5_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_s5_talk_3:
    call lanista_show_night_exterior from _lanista_night_exterior_s5_t3
    call lanista_show_emotion("angry") from _lanista_emotion_s5_t3
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "The fortnight has burned down to its last days. There's nothing left to sell, no card clever enough, no crowd large enough."
    narrator "The two of you stand in the empty bowl with the Governor's date hanging over it like a blade on a fraying cord — and you came tonight not to talk around the thing, but to make your move."
    narrator "The Lanista reads it in your face before you've said a word."
    lanista_npc "You've the look of someone who's decided something. I've faced that look across a sand from better fighters than the Governor. Say it, [_ttl]. I'd rather take it standing."
    menu:
        "\"I'll save the Arena. No conditions, no ledger. But I want you — in my life. Not as a transaction. As the thing it turns out I can't do without.\"":
            $ lanista_devotion += 8
            $ lanista_affection += 5
            narrator "You say it plainly, and you say the hard half of it — that the coin comes free and clear, that there's no hook hidden in it."
            narrator "That the one thing you're asking for is the one thing a debt could never buy and you'd never try to."
            narrator "The Lanista stands very still, the way [_they] stands when a blow lands that the body hasn't decided yet how to feel."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s5_t3_dev
            lanista_npc "No conditions. You'll lift the whole weight off this house and ask nothing back but — me. Not the Arena. Not the sand. Me."
            lanista_npc "Eleven seasons I've been a thing that gets bought, traded, leaned on, collected. You're the first to want the part of me that was never for sale. ...Yes."
            lanista_npc "The answer's yes, before you've finished asking, and it frightens me how little I had to weigh it. Save the house if you like, [_ttl]. But know it was the second thing I'd have said yes to. You were the first."
        "\"I can make all of it disappear. The number, the Governor, the date — gone by morning. You know what it costs. You've always known.\"":
            $ lanista_dominion += 8
            $ lanista_affection += 5
            $ lanista_corruption = min(100, lanista_corruption + 2)
            narrator "You don't list the price. You don't have to. It's been understood between you for a season, in every yielded inch and every debt called in."
            narrator "The last fortress, the one thing not yet formally handed over. You let the silence carry it, and you watch the Lanista arrive at the same place you already stand."
            call lanista_show_emotion("yielding") from _lanista_emotion_s5_t3_dom
            lanista_npc "Disappear. By morning. You could, too — I've seen the length of your reach. One word from you and the Governor's date is so much ash, the purse is so much ash, and the only thing left standing in the wreck of it is the bill."
            lanista_npc "And I know the figure on that bill. It's been written between us since the first count came up short. ...Pay it. I'll meet it. Take the number off my life and put it on my body, where it's been heading all along."
            lanista_npc "I'd sooner owe the whole of myself to you than a single copper to them. Make it disappear, [_ttl]. And come collect."
    $ lanista_s5_talks_done = list(lanista_s5_talks_done) + ["s5_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_s6_talk_router:
    if "s6_t1" not in lanista_s6_talks_done:
        jump lanista_s6_talk_1
    elif "s6_t2" not in lanista_s6_talks_done:
        jump lanista_s6_talk_2
    elif "s6_t3" not in lanista_s6_talks_done:
        jump lanista_s6_talk_3
    else:
        jump lanista_talk_generic

label lanista_s6_talk_1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _themself = lanista_pronoun("refl")
    $ _route = lanista_determine_ending()
    call lanista_show_emotion("yielding" if _route == "dominion" else "warm") from _lanista_emotion_s6_t1
    if _route == "dominion":
        narrator "The new order arrives at your establishment the way a fighter reports to the sand — on time, in good order, awaiting the day's word."
        narrator "The Arena runs under your name now; so, by the terms of the one bill that was never written down, does the one who keeps it."
        narrator "[_They] presents [_themself] at your door and waits to be told the shape of the service."
        lanista_npc "First day under the new arrangement. I've set the yard to the second and come where I'm kept. Name the work and I'll do it well — I do everything well, it's the one habit they never beat out of me. Only tell me my marks."
        lanista_npc "I'd sooner know them than guess them."
    elif _route == "mixed":
        narrator "The new order comes to your door by appointment — half a fighter reporting for duty, half a lover arriving for the evening, and the Lanista [_themself] could not tell you, honestly."
        narrator "Where the one leaves off and the other starts. [_They] negotiated the terms of tonight as carefully as a card."
        narrator "And crossed the city to keep them as eagerly as any tryst. One foot in each world, and standing, somehow, square."
        lanista_npc "Here I am, then — on the terms we struck, and gladder of them than the terms quite account for. Half of me's come to be useful to you. The other half just wanted to come. Don't ask me to sort which is which at the door."
        lanista_npc "I've given up trying."
    else:
        narrator "The new order has no ceremony to it, and that is the wonder of it. The Lanista simply comes."
        narrator "Crosses the city of an evening when the yard is shut and the count is done, and arrives at your door unsummoned, unowed, because the wanting carried [_them] the distance."
        narrator "Years chained to one bowl of sand, and the first free use [_they] makes of a free evening is to spend it on you."
        lanista_npc "Don't look so surprised. The gate's mine to walk through now, in either direction, and I find it leads here. No debt drove me across that city tonight. Only that I'd rather be where you are than anywhere the map still offers me."
    menu:
        "\"You came because you wanted to. That's all I ever want from you — the choice, freely made.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "You don't take the visit as service and you don't take it as your due. You take it for what it is — a person who could be anywhere choosing your door."
            narrator "And you tell [_them] so, and you watch the plain truth of it land somewhere the iron used to stand guard."
            lanista_npc "Freely made. ...You'll have the one thing this life swore I'd never own again — my own choosing — and then ask for nothing but that I keep spending it on you. There's no cage in that, [_ttl]."
            lanista_npc "I didn't know an arrangement could be built without one. You're teaching me."
        "\"Good. Report here at the close of each day. The Arena is yours to run; you are mine to keep.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 3
            narrator "You set the terms of the new order in two clean lines, the way a buyer sets the terms of a thing acquired, and you watch the proud frame take the instruction without a flinch."
            narrator "File it, accept it, stand the straighter for having its marks named."
            lanista_npc "Each day at the close. Yours to keep. ...You say it plain, so I'll answer it plain — yes, [_ttl]. The yard by day, your door by night, and the whole of me on your books either way. I asked for my marks. You've given them."
            lanista_npc "A fighter sleeps better knowing them, even marks like these."
    $ lanista_s6_talks_done = list(lanista_s6_talks_done) + ["s6_t1"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_s6_talk_2:
    call lanista_show_emotion("angry") from _lanista_emotion_s6_t2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "You catch the Lanista between the two halves of the new life and see, for half a heartbeat before the guard comes up, exactly what it costs."
    narrator "The Arena still wants a full day's blood and craft — the cards, the counts, the recruits who don't grow themselves. And now there is you, and your door, and the city to cross between the two."
    narrator "The shadows under the hard eyes are a thing the iron is working hard to deny."
    lanista_npc "I'm well. Don't furnish me with that look. I ran a failing house for years on less sleep than this and never let a card slip. Two lives is one more than I had, not one too many. I'll carry it."
    narrator "[_They] says it the way a fighter calls 'no hit' on a wound already bleeding through the linen."
    narrator "Not to deceive you, exactly, but because owning the cut has never once made it close faster, and the habit of standing is the only habit [_they] fully trusts."
    menu:
        "\"Then carry more. If you can run the Arena and still cross the city for me, you can give me the parts of you still holding back.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 3
            narrator "You don't ease the load; you add to it, deliberately, and you watch [_them] rise to it because rising is the only answer [_their] pride has ever permitted."
            narrator "There's something in the proud jaw that's almost gratitude — you've refused to treat [_them] as breakable, and a fighter would sooner be worked than pitied."
            lanista_npc "More, then. ...You'll not let me set the weight down, and gods help me, that's the one kindness I know how to take. Pity would've finished what the Governor started."
            lanista_npc "This — being made to stand and deliver — this I understand. Push, [_ttl]. I'll not break before you do."
        "\"Sit. The Arena can hold a night without you, and so can I. You don't have to stand for me — that was never the price.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "You take the weight out of [_their] hands before pride can refuse the relief."
            narrator "You sit [_them] down and send the night's demands away. Here, with you, [_they] is not required to perform."
            narrator "For a moment, the guard does not lower so much as forget it was ever raised."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s6_t2_dev
            lanista_npc "...Sit. You'd have me sit. All this time, and no one's once told me I could stop and meant it for my sake instead of theirs. I don't know the shape of an evening with nothing owed in it."
            lanista_npc "Teach me that one too, slowly, [_ttl]. I'm a poor student of rest."
    $ lanista_s6_talks_done = list(lanista_s6_talks_done) + ["s6_t2"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_s6_talk_3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _theirs = lanista_pronoun("poss_pron")
    $ _route = lanista_determine_ending()
    call lanista_show_emotion("yielding" if _route == "dominion" else "warm") from _lanista_emotion_s6_t3
    if _route == "dominion":
        narrator "Tomorrow the arrangement settles into its final shape. Tonight the Lanista comes to you composed, accounts squared."
        narrator "And speaks of the thing [_they] has made [_their] peace with."
        narrator "The place [_they] holds now, and the one mercy that makes the place bearable."
        lanista_npc "I've taken my own measure, the way I'd measure a fighter — honestly, no flattery in it. I'm a kept thing now. I'll not dress it up finer than that. But there's kept and there's kept."
        lanista_npc "A creature can be owned with contempt or owned with care, and the difference is the whole of what's left to it. You've never once made me feel the contempt. I notice it nightly. It's the hinge the rest of me swings on."
    elif _route == "mixed":
        narrator "Tomorrow the two lives stop being a thing you're testing and become a thing you simply are."
        narrator "Tonight the Lanista comes to you and says the both-things-at-once [_they] has stopped trying to untangle, and the saying of it is the closest to peace you've seen the hard face hold."
        lanista_npc "Here's the truth of me before it all sets, and it's two truths that won't lie down together. I love you — that's not the arrangement talking, it's under the arrangement and older than it."
        lanista_npc "And I serve you, and there's a part of me that needs the serving near as much as the loving. Both real. Both mine. I stopped grieving that they don't match. A person can be more than one thing and still be true to all of it."
    else:
        narrator "Tomorrow the thing settles into whatever it's going to be — the new order made permanent, the shape of the rest of it set."
        narrator "Tonight the Lanista finds you of [_their] own accord and stands a while in your quiet, and when [_they] speaks it's without the dry armor."
        narrator "Plainly, the way [_they] has learned [_they] can with you."
        lanista_npc "I've been a transaction my whole life. Bought in, sold on, leaned against, collected from. I knew the shape of every one of those."
        lanista_npc "This is the first thing I've stood inside that I can't price — and I've tried, the merchant in me's tried hard, and the figure won't come. That's how I know it's real. Nothing real ever did add up."
    menu:
        "\"It's real. Whatever else this is, that's the part that lasts — and I'll spend the rest of it proving the word.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 4
            narrator "You don't argue the merchant down with bigger words; you answer the doubt with the only thing that ever closes it."
            narrator "The promise to keep showing up, past the point where any transaction would have settled and walked away. [_They] hears it."
            narrator "The merchant, at last, stops counting."
            lanista_npc "Proving it. ...You'll not say it once and let it stand on its own, you'll pay it out daily, in the one coin no debt was ever settled in. I believe you, [_ttl]."
            lanista_npc "It's taken me eleven seasons and a ruined house to learn how, but I believe you. That's what remains. That's the whole of what remains, and it's more than I was ever owed."
        "\"Then I'll keep you well. The place is yours as long as you hold to it — and I do not deal in contempt. You've earned the manner of your keeping.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 4
            narrator "You name the terms of the keeping as plainly as you once named the debt."
            narrator "That the place is [_theirs], the care is real, the dignity guaranteed by your hand and not [_their] hope."
            narrator "The proud frame settles into it the way a fighter settles into a good stance: this, at least, is ground [_they] can hold."
            lanista_npc "Kept well. The manner guaranteed. ...You'd give me in writing the one thing I'd given up asking for — that the owning come without the shaming."
            lanista_npc "I'll hold to my place, [_ttl], and hold it gladly, knowing the hand that keeps it. That's what remains to me. A kept thing, kept with care. I've watched free folk fare worse. I'll not waste it."
    $ lanista_s6_talks_done = list(lanista_s6_talks_done) + ["s6_t3"]
    $ lanista_last_talk_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    pause
    jump lanista_visit_menu

label lanista_filler_talk:
    # Ambient, repeatable filler that carries the days the authored arc leaves
    # empty — a narrative cooldown holding back a closing Talk, or a run with no
    # authored Talk left pending. It consumes the day's single conversation
    # (stamps lanista_last_talk_total_days) and nudges affection by at most +1,
    # but never marks a story event and never closes the visit. The index rotates
    # so the same piece never lands twice in a row.
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _filler_count = 5
    $ _idx = int(getattr(store, "lanista_filler_talk_index", 0) or 0) % _filler_count
    $ store.lanista_filler_talk_index = (_idx + 1) % _filler_count
    $ lanista_last_talk_total_days = calculate_total_days()
    if _idx == 0:
        jump lanista_filler_dawn
    elif _idx == 1:
        jump lanista_filler_prospect
    elif _idx == 2:
        jump lanista_filler_ledger
    elif _idx == 3:
        jump lanista_filler_seasons
    jump lanista_filler_wraps

label lanista_filler_dawn:
    if "dawn" in lanista_fillers_seen:
        call lanista_show_emotion("neutral") from _lanista_filler_emotion_dawn_repeat
        narrator "[lanista_name] is at the lines again when you arrive, the rake moving in the same slow, even passes you've watched before."
        lanista_npc "Same lines, same hand. A thing you'd trust your feet to doesn't get more true for my having explained it once, [_ttl]. It gets more true for my drawing it again."
        $ lanista_affection += 1
        jump lanista_filler_exit
    $ lanista_fillers_seen = list(lanista_fillers_seen) + ["dawn"]
    call lanista_show_emotion("neutral") from _lanista_filler_emotion_dawn
    narrator "You find [lanista_name] already on the sand at first light, dragging a wide wooden rake in slow, even passes that leave the floor combed flat as a made bed."
    lanista_npc "The crowd never sees this part. Rake at dawn, or the blood from last night's bouts sets into ruts, and a rut is where an ankle goes."
    lanista_npc "Then the lines — quicklime, drawn fresh every morning. They go grey by noon and gone by dusk. A boundary you can't see is one the fighters stop respecting."
    narrator "The rake never stops moving while [lanista_name] talks. The work is a habit older than the words."
    lanista_npc "Eleven seasons, and I still lay my own lines, [_ttl]. A thing you'd trust your feet to, you draw with your own hand."
    $ lanista_affection += 1
    jump lanista_filler_exit

label lanista_filler_prospect:
    if "prospect" in lanista_fillers_seen:
        call lanista_show_emotion("amused") from _lanista_filler_emotion_prospect_repeat
        narrator "The young fighter is still on the pells, still glancing over between exchanges for the approval [lanista_name] won't spend."
        lanista_npc "You remember him — all speed, no patience. He's not stopped looking to me yet. The day he does, I card him. You'll know it happened before I say a word."
        $ lanista_affection += 1
        jump lanista_filler_exit
    $ lanista_fillers_seen = list(lanista_fillers_seen) + ["prospect"]
    call lanista_show_emotion("amused") from _lanista_filler_emotion_prospect
    narrator "[lanista_name] tips a chin toward a young fighter working the pells across the yard — fast hands, clean feet, a body that already moves like it knows what it's for."
    lanista_npc "That one has everything the sand asks for but the thing it can't teach. Patience. He wins the first exchange, then spends the next three trying to win it again."
    lanista_npc "A crowd loves him. A veteran will feed him his own speed inside a month. So I keep him on the pells and off the card until wanting-it-now burns down to wanting-it-right."
    narrator "The fighter lands a bright flurry, glances over for approval, and gets a flat stare for his trouble."
    lanista_npc "See that? He looked for me. The day he stops looking, he's ready."
    $ lanista_affection += 1
    jump lanista_filler_exit

label lanista_filler_ledger:
    if "ledger" in lanista_fillers_seen:
        call lanista_show_emotion("neutral") from _lanista_filler_emotion_ledger_repeat
        narrator "The clerk's three stacks are on the bench again. [lanista_name] taps the tall middle one — the beer money — without troubling to count it."
        lanista_npc "You know this sum by now, [_ttl]. Not the great bouts. This. Watch what a house earns while nothing special happens — I'll not say it twice, but I'll keep proving it true."
        $ lanista_affection += 1
        jump lanista_filler_exit
    $ lanista_fillers_seen = list(lanista_fillers_seen) + ["ledger"]
    call lanista_show_emotion("neutral") from _lanista_filler_emotion_ledger
    narrator "A clerk sets three short stacks of coin on the bench and waits. [lanista_name] sorts them without looking up — gate, cups, and the book at the door."
    lanista_npc "People think a house lives on the great bouts. It lives on the small trade. Copper at the gate, the cups of thin beer between fights, the door-side wagers the clerks skim a tenth from."
    lanista_npc "One championship night pays the roof. The cups pay the fighters — every ordinary week, whether the roof needs paying or not."
    narrator "The middle stack, the beer money, is the tallest of the three. [lanista_name] taps it once, satisfied."
    lanista_npc "Watch what a house earns while nothing special is happening, [_ttl]. That number tells you whether it lives through a bad month."
    $ lanista_affection += 1
    jump lanista_filler_exit

label lanista_filler_seasons:
    if "seasons" in lanista_fillers_seen:
        call lanista_show_emotion("warm") from _lanista_filler_emotion_seasons_repeat
        narrator "The belt on its peg catches [lanista_name]'s eye again, and two scarred fingers flex once against the palm — the old break testing itself out of long habit."
        lanista_npc "The hand still remembers what it cost. You've had that tale once, [_ttl]; I'll not stretch it twice. It held to the last bout. That's the whole of what the belt has ever meant to me."
        $ lanista_affection += 1
        jump lanista_filler_exit
    $ lanista_fillers_seen = list(lanista_fillers_seen) + ["seasons"]
    call lanista_show_emotion("warm") from _lanista_filler_emotion_seasons
    narrator "The champion's belt on its peg has caught [lanista_name]'s eye, and for once the guard is down far enough to follow the look with a story."
    lanista_npc "My seventh season. Broke two fingers in the opening exchange, with eight bouts still to fight before the purse cleared. Splinted them to the next finger and kept the grip narrow."
    lanista_npc "Won six. Lost two, honestly, to better fighters. Nobody in the stands ever knew the hand was ruined. That's the craft — not never breaking. Never letting the crowd read where."
    menu:
        "\"Eight bouts of pain for one purse.\"":
            call lanista_show_emotion("amused") from _lanista_filler_emotion_seasons_reply
            lanista_npc "It was. And I'd pay it twice over. The pain's long gone, [_ttl]. The seasons stayed."
    $ lanista_affection += 1
    jump lanista_filler_exit

label lanista_filler_wraps:
    if "wraps" in lanista_fillers_seen:
        call lanista_show_emotion("warm") from _lanista_filler_emotion_wraps_repeat
        narrator "The linen is already going round one scarred hand — between the fingers, twice about the wrist — [lanista_name] not once glancing down at the work."
        lanista_npc "Wrap, then stone. You've seen the whole order of it now, [_ttl]. I'll not narrate a habit twice. But sit, if you like. That part I've never once tired of."
        $ lanista_affection += 1
        jump lanista_filler_exit
    $ lanista_fillers_seen = list(lanista_fillers_seen) + ["wraps"]
    call lanista_show_emotion("neutral") from _lanista_filler_emotion_wraps
    narrator "[lanista_name] sits with a long strip of linen and winds it around one scarred hand — between the fingers, across the knuckles, twice about the wrist — without once glancing down."
    lanista_npc "A fighter who wraps his own hands never argues with the surgeon after. Too loose and the knuckle splits. Too tight and the hand's dead by the third round."
    narrator "The whetstone comes next, a short blade drawn along it in slow, patient strokes, the sound steady as breathing."
    lanista_npc "Wrap, then stone. Same order every night for twenty years. The body learns the evening's coming and settles for it."
    call lanista_show_emotion("warm") from _lanista_filler_emotion_wraps_warm
    lanista_npc "You've caught me at it more than once now, [_ttl]. I don't mind. It's a quiet thing, to be watched doing."
    $ lanista_affection += 1
    jump lanista_filler_exit

label lanista_filler_exit:
    # Shared close for every ambient filler talk (full + repeat variants). When the
    # after-crowd scene is available tonight, Varra folds an invitation into the
    # quiet talk so the late-game night can begin organically instead of only from
    # the visit-menu button. Declining here never touches the after-crowd cooldown.
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    if lanista_evening_state().get("aftercrowd", False):
        call lanista_show_emotion("warm") from _lanista_filler_exit_emotion
        narrator "[lanista_name]'s eyes drift to the yard door and the low light beyond it, then come back to you."
        if lanista_is_devotion_route():
            lanista_npc "The crowd empties soon. Stay past the gate tonight, if you've a mind — I'd not mind the company."
        else:
            lanista_npc "The crowd empties soon. Stay past the gate tonight, if you've a mind."
        menu:
            "Stay after the crowd. (ends the visit)":
                jump lanista_aftercrowd
            "Not tonight.":
                lanista_npc "Then off with you before the gate-count starts."
                pause
                jump lanista_visit_menu
    pause
    jump lanista_visit_menu

label lanista_talk_generic:
    call lanista_show_emotion("neutral") from _lanista_emotion_talk_generic
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    if not lanista_ending_done:
        # In-arc, the flat "nothing new" filler is replaced by the rotating
        # ambient pool so the quiet days still read as lived-in.
        jump lanista_filler_talk
    $ _route = getattr(store, "lanista_ending_route", "") or lanista_determine_ending()
    call lanista_show_emotion("yielding" if _route == "dominion" else "warm") from _lanista_emotion_talk_post_arc
    $ _idx = int(getattr(store, "lanista_post_arc_talk_index", 0) or 0) % 3
    # Day-gate post-arc Talk like every other talk (mirrors yvara_talk_post_arc,
    # which stamps yvara_last_talk_total_days); the menu's _talk_free check
    # then hides the option for the rest of the day.
    $ lanista_last_talk_total_days = calculate_total_days()
    if _route == "devotion":
        if _idx == 0:
            lanista_npc "The pits ran clean today — two good bouts, a house full enough, and an evening with nowhere it has to be but here. A year ago I'd not have called that a life, [_ttl]. It's the best one I've had."
        elif _idx == 1:
            lanista_npc "A recruit asked me why the Master of the Sands keeps crossing the city most nights. I told him a fighter who finds the one thing worth going to doesn't waste it on a cold cot. He didn't take my meaning. You do."
        else:
            lanista_npc "I chose this. That's the part I keep turning over. No debt drove me to your door tonight, no lender, no card — the gate swung your way and I let it. Don't look so pleased, [_ttl]. ...Aye, all right. Be pleased."
    elif _route == "dominion":
        if _idx == 0:
            lanista_npc "The pits are run, the books are squared, and I'm here as you keep me, [_ttl]. I'll not pretend I'm free of you. I'll only say you've never made me feel the collar where the neighbours could see it."
            lanista_npc "A fighter remembers that kind of keeping."
        elif _idx == 1:
            lanista_npc "Eleven seasons I answered to no one. Now I answer to you, and the strange part is the bearing held. You took the freedom and left me the spine. Most owners haven't the wit to know the difference. Tell me where you want me."
        else:
            lanista_npc "They still call me Master of the Sands at the gate. Inside these walls we both know whose hand I work under. It's an honest arrangement, [_ttl], and you keep your end with care."
            lanista_npc "I've worn worse than a fair owner — far worse, and for less."
    else:
        if _idx == 0:
            lanista_npc "Half my day on the sand, half my evening in your halls, and I'm damned if I can tell you which I'd give up first. So I don't. I keep both and let them grind against each other. It's a crooked life, [_ttl]. It's mine."
        elif _idx == 1:
            lanista_npc "Some mornings the pits have me and some nights your house does, and a body learns to be two things at once or be torn between them. I chose the first. The days I can't manage it, I come find you. That's the arrangement."
        else:
            lanista_npc "Master by day, kept by evening, unwilling to sever either — you knew what you were taking on, [_ttl], and you took it anyway. So did I. We're neither of us tidy. The crowd never once paid for tidy."
    $ store.lanista_post_arc_talk_index = (_idx + 1) % 3
    jump lanista_visit_menu

label lanista_s1_remark_router:
    if "s1_r1" not in lanista_s1_remarks_done:
        jump lanista_s1_remark_1
    elif "s1_r2" not in lanista_s1_remarks_done:
        jump lanista_s1_remark_2
    elif "s1_r3" not in lanista_s1_remarks_done:
        jump lanista_s1_remark_3
    else:
        jump lanista_visit_menu

label lanista_s1_remark_1:
    call lanista_show_emotion("neutral") from _lanista_emotion_s1_r1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You let your gaze travel the old wounds the Lanista wears like a second armor — the seam across one forearm, the notch missing from an ear, the pale rope of scar that vanishes under the collar."
    menu:
        "\"You kept count of those the hard way.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s1_r1", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 2
            narrator "You name the scars without trying to price them, giving each mark the dignity of a lesson survived."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s1_r1_dev
            lanista_npc "Each one is a lesson I was slow to learn. The slow ones leave the deepest marks."
        "\"Scars are a ledger. I could learn where you still break.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s1_r1", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 2
            narrator "Your gaze lingers where old wounds might still answer pressure, and the Lanista notices exactly what you are measuring."
            call lanista_show_emotion("angry") from _lanista_emotion_s1_r1_dom
            lanista_npc "Looking for the weak seam already, coin-counter? Careful. Knowing where to press is not the same as having the strength."
        "Say nothing.":
            jump lanista_visit_menu
    $ lanista_s1_remarks_done = list(lanista_s1_remarks_done) + ["s1_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s1_remark_2:
    call lanista_show_emotion("warm") from _lanista_emotion_s1_r2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A recruit fumbles the haft of a practice spear. The Lanista crosses the yard, closes a scarred hand over the recruit's, and resets each finger without a word."
    narrator "Patient, exact, the way one might tune an instrument."
    menu:
        "\"You could just shout at the lad.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s1_r2", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 2
            narrator "The tease is light, but the respect beneath it is not. You have seen the patience others miss."
            lanista_npc "Shouting teaches him to flinch. The hand teaches the hand. He'll keep this long after he's forgotten my voice."
        "\"A flinch is useful, if you decide what they fear.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s1_r2", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 2
            narrator "You turn instruction into leverage with a sentence, and the correcting hand goes still around the recruit's grip."
            call lanista_show_emotion("neutral") from _lanista_emotion_s1_r2_dom
            lanista_npc "Fear makes quick servants and poor fighters. You'd know the difference eventually. They would pay for the lesson first."
        "Say nothing.":
            jump lanista_visit_menu
    $ lanista_s1_remarks_done = list(lanista_s1_remarks_done) + ["s1_r2"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s1_remark_3:
    call lanista_show_emotion("neutral") from _lanista_emotion_s1_r3
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Along a high shelf behind the rack sits a row of victor's wreaths and bronze tokens, grey under a skin of chalk dust. Trophies of fighters who mattered, on days the crowd has long since spent."
    menu:
        "\"Nobody dusts those.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s1_r3", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 2
            narrator "You say it without mockery. The neglect reads less like indifference than a private refusal to polish grief."
            call lanista_show_emotion("warm") from _lanista_emotion_s1_r3_dev
            lanista_npc "Glory's cheap to win and cheaper to keep. The names matter to me. The shine never did."
        "\"Dead champions are wasted capital. Sell the lot.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s1_r3", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 2
            narrator "You reduce the shelf to weight and price. The Lanista's eyes harden, but they do not leave yours."
            call lanista_show_emotion("angry") from _lanista_emotion_s1_r3_dom
            lanista_npc "Those names bought this house more than once. Touch the trophies when you own the walls, not before."
        "Say nothing.":
            jump lanista_visit_menu
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
        jump lanista_visit_menu

label lanista_s2_remark_1:
    call lanista_show_emotion("neutral") from _lanista_emotion_s2_r1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A champion's belt hangs on a peg by the weapons rack, the leather gone dark and supple with old wear, the bronze plate at its center worn bright by a thumb that no longer touches it."
    narrator "Close enough to see from the bench. Too far to be worn."
    menu:
        "\"You keep it where you'll look at it, but not where you'll reach for it.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s2_r1", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 2
            narrator "You leave room for the loss inside the observation, neither flattering the old champion nor dismissing what remains."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s2_r1_dev
            lanista_npc "It fit a fighter who could carry it. I keep it honest about which of us is still standing."
        "\"Put it on. I want to see how much of the champion still obeys.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s2_r1", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 2
            narrator "The words land as an instruction, not a kindness. A scarred thumb presses once against the worn bronze."
            call lanista_show_emotion("angry") from _lanista_emotion_s2_r1_dom
            lanista_npc "You do enjoy giving orders before you've earned the ground beneath them. One day I may make you test that courage."
        "Say nothing.":
            jump lanista_visit_menu
    $ lanista_s2_remarks_done = list(lanista_s2_remarks_done) + ["s2_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s2_remark_2:
    call lanista_show_emotion("angry") from _lanista_emotion_s2_r2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Before the gates open the Lanista stands at the mouth of the tunnel and counts the house as it fills — not the heads that come, you realize, but the benches that stay bare."
    narrator "With each empty row the jaw sets a fraction harder, a tally kept in muscle."
    menu:
        "\"You count the empty seats because you're afraid of who leaves with them.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s2_r2", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 2
            narrator "You look past the lost coin to the fighters, clerks, and history the Arena keeps under one roof."
            lanista_npc "A closed gate scatters more than a crowd. Good. You understand what the number has its hand around."
        "\"You count the seats nobody took.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s2_r2", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 2
            narrator "You follow the same cold arithmetic and make it plain that you can read the pressure tightening around the house."
            lanista_npc "Full rows lie. The empty ones tell the truth, and the truth is what I owe by month's end. You learn quickly."
        "Say nothing.":
            jump lanista_visit_menu
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
        jump lanista_visit_menu

label lanista_s3_remark_1:
    call lanista_show_emotion("neutral") from _lanista_emotion_s3_r1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Between bouts the Lanista sits and winds a strip of linen around one fist — over the knuckles, between the fingers, the wrap of a fighter readying for the sand. There's no fight tonight."
    narrator "The hands haven't thrown a real blow in years. They wind the tape anyway, slow and exact, and the eyes above them are somewhere far off."
    menu:
        "\"Old habit dies hard.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s3_r1", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 1
            narrator "You grant the ritual its dignity, treating the remembered fighter as something living rather than pathetic."
            call lanista_show_emotion("warm") from _lanista_emotion_s3_r1_dev
            lanista_npc "The hands remember before the head does. For a moment I'm twenty and unbeaten. The moment's worth the linen."
        "\"The hands still obey. Good. I may have work for them.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s3_r1", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 1
            narrator "You turn memory into utility. The wrapped fist closes once, testing itself against the shape of your claim."
            lanista_npc "Still measuring what use you could make of me. At least you've stopped pretending otherwise."
        "Say nothing.":
            jump lanista_visit_menu
    $ lanista_s3_remarks_done = list(lanista_s3_remarks_done) + ["s3_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s3_remark_2:
    call lanista_show_emotion("angry") from _lanista_emotion_s3_r2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The night's coin comes up from the gate in a strapped wooden box. The Lanista doesn't open it, doesn't count it aloud."
    narrator "Only sets a hand flat on the lid and reads its weight the way a fighter reads an opponent's stance, knowing the answer before the latch is ever thrown. The jaw tells you the number."
    narrator "The mouth says nothing."
    menu:
        "\"You don't have to weigh the bad nights alone.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s3_r2", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 1
            narrator "You set your hand beside the Lanista's on the lid, sharing the answer without asking for the number."
            call lanista_show_emotion("warm") from _lanista_emotion_s3_r2_dev
            lanista_npc "Careful, [_ttl]. Stand beside a burden often enough and one day you find half of it has learned your shoulders."
        "\"You already know what's in it.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s3_r2", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 1
            narrator "You name the instinct you intend to use: a house read through the hand of the one desperate to keep it."
            lanista_npc "To the copper. Tonight's light. And now you know which silence means the walls are cheapest."
        "Say nothing.":
            jump lanista_visit_menu
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
        jump lanista_visit_menu

label lanista_s4_remark_1:
    call lanista_show_emotion("warm") from _lanista_emotion_s4_r1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The champion's belt is off its peg for the first time you've seen it. The Lanista works oil into the old leather with slow circles of a rag, coaxing the dark suppleness back into it."
    narrator "Thumbing the bronze plate until it answers the lamplight. Tended like a thing that matters. And when it's done, set down on the bench — not buckled on."
    menu:
        "\"You've brought it back to life, and you still won't wear it.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s4_r1", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 1
            narrator "You let the care speak for itself. Whatever the Lanista claims, the old fighter has not been discarded."
            lanista_npc "Oiling it is respect. Wearing it is a claim. Maybe I'm only keeping it ready for whoever can make that claim honestly."
        "\"If you won't wear it, I should decide who does.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s4_r1", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 1
            narrator "Your hand settles on the belt between you, laying claim not to the old victory but to the right to assign its meaning."
            lanista_npc "The belt is not yours yet. But you say 'yet' without speaking it, and gods help me, I hear it."
        "Say nothing.":
            jump lanista_visit_menu
    $ lanista_s4_remarks_done = list(lanista_s4_remarks_done) + ["s4_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s4_remark_2:
    call lanista_show_emotion("angry") from _lanista_emotion_s4_r2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Workers haul new banners up the gate-poles — vast painted things, all bright dye and bared skin, a far cry from the plain crossed-swords sigil that had flown there for eleven seasons."
    narrator "They sell a promise of flesh, not steel, and the crowd already gathering below points up at them and grins."
    narrator "The old sigil lies folded in the dust by the wall, where someone set it down and no one thought to lift it."
    menu:
        "\"Those colors aren't yours. You don't have to pretend they are.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s4_r2", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 1
            narrator "You acknowledge the compromise without confusing it for the person forced to make it."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s4_r2_dev
            lanista_npc "No. They aren't mine. It matters more than it should that someone can still tell the difference."
        "\"New colors over the gate.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s4_r2", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 1
            $ lanista_corruption += 1
            narrator "You admire the brighter promise and the larger house it buys, letting the old sigil remain where it fell."
            lanista_npc "They draw coin. Respect never satisfied a lender. If this is the trade, I will at least count the take honestly."
        "Say nothing.":
            jump lanista_visit_menu
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
        jump lanista_visit_menu

label lanista_s5_remark_1:
    call lanista_show_emotion("angry") from _lanista_emotion_s5_r1
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "A fresh notice is nailed to the great gate, square in the center where every fighter and every patron must pass beneath it."
    narrator "The Governor's seal sits heavy at its foot — red wax and a pressed crest, official as a verdict already passed. The crowd reads it on the way in and lowers their voices."
    narrator "The Lanista hasn't torn it down — has left it hanging where it bites hardest, the way one leaves a wound undressed to keep the lesson of the blow."
    menu:
        "\"You could take that down.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s5_r1", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 1
            narrator "You offer to spare the house the public wound, not because the threat is unreal but because dignity still matters."
            lanista_npc "And the Governor nails up another by noon. No. Let them read what I'm fighting. But I know why you offered."
        "\"Leave it up. Fear is useful when everyone can read it.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s5_r1", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 1
            narrator "You read the humiliation as an instrument: pressure on the house, pressure on its keeper, pressure that can be directed."
            lanista_npc "Useful. Aye. You look at a blade over my neck and wonder whose hand might take the hilt."
        "Say nothing.":
            jump lanista_visit_menu
    $ lanista_s5_remarks_done = list(lanista_s5_remarks_done) + ["s5_r1"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_s5_remark_2:
    call lanista_show_emotion("angry") from _lanista_emotion_s5_r2
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "Past midnight the lamps should be dead and the bowl empty. Instead there's the dry scuff of footwork on sand, the same combination drilled over and over to nothing."
    narrator "The Lanista is alone at the center, stripped to the linen, throwing blows at an opponent eleven years in the ground — not training. Wearing the body out past the point where the mind can keep talking."
    menu:
        "\"You're not sleeping.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s5_r2", "devotion")
            $ lanista_devotion += 1
            $ lanista_affection += 1
            narrator "You do not dress concern as command. You simply stand where the Lanista can no longer pretend the exhaustion is invisible."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_s5_r2_dev
            lanista_npc "The number sits up whether I lie down or not. Still... stay until I stop. It may be easier to stop with someone here."
        "\"Good. Exhaustion makes pride easier to bargain with.\"":
            $ lanista_remark_choices = lanista_record_remark_choice(lanista_remark_choices, "s5_r2", "dominion")
            $ lanista_dominion += 1
            $ lanista_affection += 1
            narrator "The next blow dies halfway through. The Lanista turns, breathing hard, and understands that you have been counting weakness as carefully as coin."
            lanista_npc "Then bargain, [_ttl]. But remember: a tired fighter still knows where to put a fist."
        "Say nothing.":
            jump lanista_visit_menu
    $ lanista_s5_remarks_done = list(lanista_s5_remarks_done) + ["s5_r2"]
    $ lanista_last_question_total_days = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_debt_finance:
    menu:
        lanista_npc "Both columns are open. Choose which burden you mean to lift — and which claim you mean to own."
        "Clear a creditor's claim." if lanista_donation_highest_tier < 4:
            jump lanista_debt_donate
        "Purchase a creditor's claim." if lanista_favor_highest_tier < 4:
            jump lanista_debt_favor
        "Back.":
            jump lanista_visit_menu

label lanista_debt_donate:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    menu:
        lanista_npc "You came to cover what I can't. I won't pretend that sits well."
        "Cover a creditor's note. (800 coins)" if lanista_donation_highest_tier == 0 and money >= 800:
            $ money -= 800
            $ lanista_devotion += 2
            $ lanista_affection += 3
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 1)
            narrator "You meet the creditor's clerk at the Arena gate and pay the smallest sealed note in full. The clerk cuts the wax mark from the page before leaving."
            lanista_npc "One less paper on my desk. Don't make it a thing."
            narrator "[lanista_name] folds the cleared note twice and keeps it instead of burning it. The gesture has landed, however firmly pride denies it."
        "Clear the month's interest. (1600 coins)" if lanista_donation_highest_tier == 1 and money >= 1600:
            $ money -= 1600
            $ lanista_devotion += 3
            $ lanista_affection += 4
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 2)
            narrator "You clear every interest charge due this month. For once, the day's gate money can pay fighters and smiths instead of feeding a number that never shrinks."
            lanista_npc "This buys the sand another month. That's all."
            narrator "The answer is curt, but the ledger closes without the usual white-knuckled grip on its cover."
        "Buy back a lien. (2800 coins)" if lanista_donation_highest_tier == 2 and money >= 2800:
            $ money -= 2800
            $ lanista_devotion += 4
            $ lanista_affection += 5
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 3)
            narrator "The lien on the armory changes hands, then disappears under your seal. By dusk, no creditor can strip the racks or claim the fighters' equipment."
            lanista_npc "I counted the papers. Every blade stays where it belongs. Don't expect me to say more."
            narrator "[lanista_name] spends the next hour checking each rack anyway, touching the hilts as if confirming the room is still real."
        "Settle the principal. (4000 coins)" if lanista_donation_highest_tier == 3 and money >= 4000:
            $ money -= 4000
            $ lanista_devotion += 5
            $ lanista_affection += 6
            $ lanista_donation_total += 1
            $ lanista_donation_highest_tier = max(lanista_donation_highest_tier, 4)
            narrator "Your payment erases the principal. The creditor's final receipt lies beside a ledger whose bottom line reads zero for the first time in years."
            lanista_npc "The books are clear. I can open the gate tomorrow without owing the sound of it to anyone."
            narrator "[lanista_name] tries to return the receipt, then stops and presses it into your hand instead."
            lanista_npc "Keep it, [_ttl]. I will never say what this cost you often enough. Consider it said now."
        "Not today.":
            jump lanista_visit_menu
    $ lanista_debt_finance_last_day = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_debt_favor:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    call lanista_show_emotion("warm") from _lanista_emotion_debt_favor
    menu:
        lanista_npc "You mean to buy the notes off my creditors. Better your hand holds them than theirs — I'll not pretend otherwise."
        "Take over the first marker. (800 coins)" if lanista_favor_highest_tier == 0 and money >= 800:
            $ money -= 800
            $ lanista_devotion += 2
            $ lanista_affection += 3
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 1)
            $ lanista_favor_balance = min(4, lanista_favor_balance + 1)
            $ renpy.notify("Owed favor gained. Favors owed: {}".format(lanista_favor_balance))
            narrator "You buy the smallest note off the creditor before a harsher lender can. The old seal is struck out and yours set above the amount, the debt drawn out of hands you chose over the ones still circling."
            lanista_npc "Out of their reach and into yours. That's a mercy today. What it becomes is a thing we both hold now."
            narrator "The old seal leaves the Arena; your copy stays open on the bench between you, a kindness that has quietly become a claim."
        "Put your name on the second marker. (1600 coins)" if lanista_favor_highest_tier == 1 and money >= 1600:
            $ money -= 1600
            $ lanista_devotion += 3
            $ lanista_affection += 4
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 2)
            $ lanista_favor_balance = min(4, lanista_favor_balance + 1)
            $ renpy.notify("Owed favor gained. Favors owed: {}".format(lanista_favor_balance))
            narrator "You take the month's interest off the lender's books and onto your own, so no stranger holds it over [lanista_name] again. The creditor bows to you before leaving and never once looks [lanista_name]'s way."
            lanista_npc "My debt, your name. No jackal at the gate for it now — only you. I know the difference, and I know it isn't nothing."
            narrator "[lanista_name] sets the pen beside your signature with exact care, as though disturbing the page might alter the balance you have quietly assumed."
        "Buy the third marker yourself. (2800 coins)" if lanista_favor_highest_tier == 2 and money >= 2800:
            $ money -= 2800
            $ lanista_devotion += 4
            $ lanista_affection += 5
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 3)
            $ lanista_favor_balance = min(4, lanista_favor_balance + 1)
            $ renpy.notify("Owed favor gained. Favors owed: {}".format(lanista_favor_balance))
            narrator "The armory lien would have let a stranger strip the racks bare. You buy it out from under them instead. Every blade and harness stays where it belongs — held safe under your seal now, not theirs."
            lanista_npc "You kept the steel on the wall. It answers to you tonight, and I'd sooner that were you than any of them."
            narrator "[lanista_name] looks around the armory after saying it, measuring familiar possessions kept whole by an unfamiliar hand."
        "Own the final marker outright. (4000 coins)" if lanista_favor_highest_tier == 3 and money >= 4000:
            $ money -= 4000
            $ lanista_devotion += 5
            $ lanista_affection += 6
            $ lanista_favors_total += 1
            $ lanista_favor_highest_tier = max(lanista_favor_highest_tier, 4)
            $ lanista_favor_balance = min(4, lanista_favor_balance + 1)
            $ renpy.notify("Owed favor gained. Favors owed: {}".format(lanista_favor_balance))
            narrator "You buy the last of the debt out of every other hand at once. The creditors leave with full purses and no further reach into the Arena; every note, seal, and claim against it rests beneath yours instead."
            lanista_npc "No lender left to knock. Only you hold the paper now. It's the safest that column has been in years — and I have not forgotten whose hand made it so."
            narrator "[lanista_name] closes the gate personally, then returns to stand across from you and the papers without pretending the room is unchanged."
            call lanista_show_emotion("vulnerable") from _lanista_emotion_debt_favor_t4
            lanista_npc "You did not have to spend a coin of it, [_ttl]. You put yourself between me and worse men, and I watched you do it."
        "Not today.":
            jump lanista_visit_menu
    $ lanista_debt_finance_last_day = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_monthly_purse:
    if money < 1000 or not lanista_monthly_purse_available():
        lanista_npc "Not this month. The purse is either covered already or your claim is full."
        jump lanista_visit_menu
    $ money -= 1000
    $ lanista_favor_balance = min(4, lanista_favor_balance + 1)
    $ lanista_monthly_purse_last_month = lanista_current_month_key()
    $ renpy.notify("Owed favor gained. Favors owed: {}".format(lanista_favor_balance))
    narrator "You place a thousand coins in the Arena's purse before wages, steel, or creditors can touch it."
    narrator "The Lanista records the advance under your name. No new debt changes hands, but one fresh obligation now sits in your column."
    lanista_npc "One favor, then. The month is funded and the entry is clean. Spend it when you mean to."
    jump lanista_visit_menu

label lanista_arena_arc:
    $ _arena_arc_next = lanista_arena_arc_next_step()
    if _arena_arc_next == 2:
        jump lanista_arena_arc_b
    elif _arena_arc_next == 3:
        jump lanista_arena_arc_c
    elif _arena_arc_next == 4:
        jump lanista_arena_arc_d
    jump lanista_visit_menu

label lanista_arena_arc_b:
    call lanista_show_night_exterior from _lanista_night_arena_arc_b
    call lanista_show_emotion("angry") from _lanista_emotion_arena_arc_b
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You stand with the Lanista above a real bout: shield against bare hands, neither fighter promised so much as the next breath."
    narrator "The shield strap tears in the third exchange. One shoulder comes bare, slick with oil and sweat, and the front rows rise before the fighter has even recovered the guard."
    narrator "The roar deepens when the bodies close. It sharpens at the first pin, goes hungry when the trapped fighter breathes through fear, then breaks clean when strength turns the hold."
    narrator "The pinned fighter escapes and wins two exchanges later. The crowd cheers the victory, but both of you heard what drew them forward first."
    menu:
        "\"They were watching the craft and the bodies that made it visible. We can honor both.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 2
            narrator "You name the fighter's body as part of the achievement rather than something that cheapens it. The Lanista keeps watching the victor's scarred shoulder."
        "\"They wanted the shoulder, the oil, the fear before the pin. We should sell what they already came to buy.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 2
            narrator "You refuse to perfume the appetite in the stands. The Lanista dislikes the arithmetic, but cannot deny that the crowd supplied the figures."
    narrator "You set the new terms without softening them. No fixed winner. No ordered fall. No false injury, no promised comeback."
    narrator "Only the light, the equipment, the pairings, and the right kind of attention. The fighters decide the bout; the result stays true."
    lanista_npc "True result. A fighter keeps the name earned on the sand. That clears the line I drew."
    lanista_npc "It opens another. Once we teach the benches to desire the body, some fool will think the price of admission bought a piece of it."
    lanista_npc "The craft gave fighters honor where other pits saw meat. I will not preserve the result only to make them meat with a purse attached."
    narrator "The old objection has moved, not vanished. The crowd files out still talking about the exposed shoulder."
    $ lanista_spectacle_arc_step = 2
    $ lanista_spectacle_arc_last_day = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_arena_arc_c:
    call lanista_restore_visit_scene from _lanista_restore_arena_arc_c
    call lanista_show_emotion("angry") from _lanista_emotion_arena_arc_c
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The next count is worse than the last. Bare benches face an open ledger while smiths and fighters wait for wages the Arena cannot yet promise."
    narrator "You put a new format on the slate: Bikini Bouts. Real exhibition combat in deliberately spare armor, staged for the eye but never for the result."
    lanista_npc "Spare armor means exposed ribs, exposed joints, and a crowd trained to treat the danger as decoration."
    lanista_npc "And do not tell me they will volunteer as if that settles it. Hunger can force a yes as surely as a hand at the throat."
    if lanista_is_dominion_route():
        if lanista_favor_highest_tier > 0:
            narrator "You tap the markers now held under your name. The Lanista's purity survives because your coin has bought it room to breathe."
            lanista_npc "There is the leverage, then. You paid for the right to make refusal expensive, and you mean me to hear every coin in it."
        else:
            narrator "You point to the empty seats and the deed beneath your hand. The Arena is yours; necessity does not wait for the keeper's blessing."
            lanista_npc "Ownership can order the gate open. It cannot make coercion honest merely because the order came from above."
        $ lanista_dominion += 3
        $ lanista_affection += 2
    else:
        narrator "You offer rules with the proposal: volunteers only, blunted exhibition steel, a richer purse, and no loss of ordinary work for anyone who refuses."
        narrator "The Lanista would keep authority over equipment, pairings, and the right to stop a bout before presentation becomes injury."
        $ lanista_devotion += 3
        $ lanista_affection += 2
    lanista_npc "Better terms matter. They do not answer the whole question."
    lanista_npc "Why should I ask a fighter to sell skin, scars, and pride for this house when I would not sell myself the same way?"
    narrator "The challenge holds. You would ask others to display what the Lanista would not personally sell, and neither of you pretends the contradiction is small."
    narrator "Bikini Bouts remain chalk on a slate. No costume is cut; no fighter is called."
    $ lanista_spectacle_arc_step = 3
    $ lanista_spectacle_arc_last_day = calculate_total_days()
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_arena_arc_d:
    call lanista_show_night_cutscene from _lanista_night_arena_arc_d
    call lanista_show_emotion("angry") from _lanista_emotion_arena_arc_d
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    narrator "After the gate bars, you return the Lanista's challenge. If the keeper would not ask a fighter to do what the keeper would not do, then the keeper will test the proposal first."
    narrator "No crowd. No purse. No promised conclusion. Only the two of you, an empty strip of sand, and the question left open between you."
    narrator "The Lanista sets the weapon belt aside. Steel touches the bench with deliberate care."
    if lanista_is_dominion_route():
        narrator "At your word, the cloak comes free and is folded rather than dropped."
        narrator "At the next, the gauntlets are pulled loose finger by finger and placed beside the belt."
        narrator "You make the pause last before ordering the armor opened. Buckles answer one at a time; the breastplate joins the growing line on the bench."
    else:
        narrator "The Lanista removes the cloak without prompting, folds it, and waits to see whether you understand that the pace remains a choice."
        narrator "The gauntlets follow, each drawn off with a fighter's economy. Bare, scarred hands settle at the belt."
        narrator "Then the armor is unbuckled and lifted away. The Lanista sets it down personally, accepting the test without surrendering command of it."
    narrator "The underlayer shows the body the iron edited out: old cuts across the ribs, a shoulder built around healed damage, the damaged knee held a fraction too carefully."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_arena_arc_d_confess
    lanista_npc "The crowd paid to watch the champion kill. Not to inspect what survived after the knee failed."
    lanista_npc "You'd have liked the fighter I was. Some days I think you'd have liked that one better than what's left."
    narrator "You hold the scarred gaze and answer the old confession at last."
    narrator "I would have liked the fighter you were. I want the one standing here."
    narrator "This body is not the ruin of the craft. It is the surviving record of eleven honest seasons, the one result no fixed bout could counterfeit."
    $ _nude_bust = "images/lanista/lanista_{}_nude.png".format(_g)
    if not renpy.loadable(_nude_bust):
        $ _nude_bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if lanista_is_dominion_route():
        jump lanista_arena_arc_d_dominion
    jump lanista_arena_arc_d_devotion

label lanista_arena_arc_d_devotion:
    call lanista_show_emotion("vulnerable") from _lanista_emotion_arena_arc_d_devotion
    lanista_npc "You've seen me armored. Not like this. Sit, [_ttl]. Watch what you proposed, and do not mistake permission for possession."
    narrator "The Lanista loosens the linen personally, then stops. The pause is long enough to remain a decision."
    $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "The last fastenings open. Scar by scar, the old champion controls what you are allowed to see and how long you are made to wait for it."
    narrator "Only then does the final layer fall. The Lanista stands clear-eyed rather than covered, weight set to protect the knee without hiding it."
    if renpy.loadable(_nude_bust):
        show expression _nude_bust as lanista_bust at lanista_bust_right
    narrator "A slow turn presents the back, the flank, the ruined line of the joint. The pose remains martial even as the display becomes unmistakably erotic."
    lanista_npc "Volunteer fighters. Extra purse. Exhibition steel. A refusal costs them nothing, and I stop any bout that turns appetite into injury."
    lanista_npc "Under those rules, the flesh does not make the fighter false. It makes the work visible. Bikini Bouts can stand on my sand."
    $ lanista_devotion += 5
    $ lanista_affection += 4
    jump lanista_arena_arc_d_end

label lanista_arena_arc_d_dominion:
    $ _markers = int(getattr(store, "lanista_favor_highest_tier", 0) or 0)
    $ lanista_corruption = min(100, lanista_corruption + 8)
    call lanista_show_emotion("yielding") from _lanista_emotion_arena_arc_d_dominion
    if _markers >= 4:
        narrator "You own every marker. You order the next layer removed as one more item in a column already transferred in full."
    elif _markers >= 3:
        narrator "Three markers answer to your hand. You invoke each one by name before ordering the next layer opened."
    else:
        narrator "Two markers were enough to bring the house this far. You use their weight now and order the next layer opened."
    $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "The Lanista obeys one fastening at a time. You control the interval between concessions; the cold eyes count every one."
    narrator "You order the linen lowered. The scarred body emerges by degrees, never passive, never confused about whose pace has made it a product."
    if renpy.loadable(_nude_bust):
        show expression _nude_bust as lanista_bust at lanista_bust_right
    narrator "Bared at last, the Lanista turns when told and settles into a fighter's stance, making discipline itself part of the display."
    lanista_npc "The body is true. The result will be true. What changed is who may set the terms of being seen."
    lanista_npc "Bikini Bouts, then. Real winners, safer steel, and enough skin to fill your benches. I know exactly which part of me bought the lesson."
    $ lanista_dominion += 5
    $ lanista_affection += 3
    jump lanista_arena_arc_d_end

label lanista_arena_arc_d_end:
    $ lanista_pinup_unlocked = True
    $ lanista_arena_program_tier = max(lanista_arena_program_tier, 1)
    $ lanista_spectacle_arc_step = 4
    $ lanista_spectacle_arc_last_day = calculate_total_days()
    $ renpy.notify("Bikini Bouts unlocked for the Arena.")
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_arena_format:
    $ _arena_format_next = lanista_arena_format_next_step()
    if _arena_format_next == 2:
        jump lanista_arena_format_oil_chains
    elif _arena_format_next == 4:
        jump lanista_arena_format_spectacle_pitch
    elif _arena_format_next == 3:
        jump lanista_arena_format_spectacle
    jump lanista_visit_menu

label lanista_arena_format_oil_chains:
    call lanista_show_night_exterior from _lanista_night_arena_format_oil
    call lanista_show_emotion("neutral") from _lanista_emotion_arena_format_oil
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "The next proposal begins with oil, short chains, and a submission bout stripped down to leverage, breath, and control."
    lanista_npc "Then the rule must survive the appetite. The pin is won. The yield is real. Neither fighter carries an order about who leaves standing."
    call lanista_show_emotion("angry") from _lanista_emotion_oil_resist
    lanista_npc "And oil? Chains? That is not leverage, that is the crowd's mouth already watering. Where does the bout end and the show begin?"
    narrator "You draw the line for her: the chains are short enough only to test a hold, the oil only to keep the struggle honest and hard to fake."
    lanista_npc "Say it plainer. The winner is decided by the pin, not by whichever body the benches would rather watch lose."
    narrator "You agree. Only after the winner earns it does the display begin: the hold sustained safely, the chain drawn taut, surrender made visible without rewriting who achieved it."
    if lanista_is_dominion_route():
        narrator "You place two experienced fighters on the empty sand. The Lanista must choreograph the fighters while you choose the holds, the angles, and how long each concession is displayed."
        narrator "The old mastery remains exact. What changes is the hand above it: every adjustment serves the product you have ordered."
        call lanista_show_emotion("angry") from _lanista_emotion_oil_dominion
        lanista_npc "I can make restraint legible without making defeat false. Do not mistake how well I do it for forgetting whose appetite now directs the lesson."
        $ lanista_dominion += 5
        $ lanista_affection += 3
        $ lanista_corruption = min(100, lanista_corruption + 10)
    else:
        narrator "The Lanista refuses to turn another fighter into a first draft. Instead, you become the willing partner on the empty sand."
        narrator "A scarred forearm settles beneath your jaw; a knee controls the hip without touching the injured joint. Every hold is taught before it is tightened."
        call lanista_show_emotion("warm") from _lanista_emotion_oil_devotion
        lanista_npc "This is the line. Win the position honestly. Hear the yield. Then, if both fighters consent, hold the shape for the crowd without adding injury or stealing the result."
        narrator "The lesson ends with you safely pinned and the Lanista's breath warm at your ear, craft and desire occupying the same hold without confusing their terms."
        $ lanista_devotion += 5
        $ lanista_affection += 4
        $ lanista_corruption = min(100, lanista_corruption + 2)
    jump lanista_arena_format_oil_chains_end

label lanista_arena_format_oil_chains_end:
    $ lanista_oilchains_unlocked = True
    $ lanista_arena_program_tier = max(lanista_arena_program_tier, 2)
    $ lanista_arena_program_last_day = calculate_total_days()
    $ renpy.notify("Oil & Chains unlocked for the Arena.")
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_arena_format_spectacle_pitch:
    # Step 1 of the two-part Spectacle: the pitch. This is the biggest ask of the
    # whole program, so it does not unlock anything — it only wins the argument and
    # sets lanista_spectacle_pitch_done so the climax can fall on a later visit.
    call lanista_show_night_cutscene from _lanista_night_arena_format_spectacle_pitch
    call lanista_show_emotion("neutral") from _lanista_emotion_arena_format_spectacle_pitch
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You lay the last card face-up beneath the dark stands."
    narrator "One full night: the steel, the submission, and the body's display bound together into a single ordered spectacle."
    call lanista_show_emotion("angry") from _lanista_emotion_spectacle_pitch_resist
    lanista_npc "No. Every other format kept a wall between the win and the wanting. This one tears it down."
    lanista_npc "You are asking me to sell the last thing the sand left me whole."
    narrator "You tell her the wall was never the code. The true result was, and it always will be."
    narrator "Bind the wanting to a bout only after the sand has spoken, and the truth stands untouched."
    lanista_npc "Eleven seasons I never let the crowd past the fight. Now you want them past me."
    lanista_npc "Then say every limit out loud, here, or there is no such night at all."
    if lanista_is_dominion_route():
        call lanista_show_emotion("angry") from _lanista_emotion_spectacle_pitch_dominion
        lanista_npc "Then you set the pairings and the pace. I set what may never happen on my sand."
        lanista_npc "I will hand you the display. I will not hand you a false result to go with it."
        $ lanista_dominion += 4
        $ lanista_affection += 2
        $ lanista_corruption = min(100, lanista_corruption + 6)
    else:
        call lanista_show_emotion("vulnerable") from _lanista_emotion_spectacle_pitch_devotion
        lanista_npc "You hold the limits, and I will trust you with the rest of it."
        lanista_npc "No fighter forced past a yes. That is the last faith I have left to hand you."
        $ lanista_devotion += 4
        $ lanista_affection += 3
        $ lanista_corruption = min(100, lanista_corruption + 2)
    narrator "The terms settle into place: two consents, one word that stops everything, no purse lost for a fighter who wins and walks away."
    narrator "The night is agreed between you. It is not yet run."
    $ lanista_spectacle_pitch_done = True
    $ lanista_arena_program_last_day = calculate_total_days()
    $ renpy.notify("The Spectacle is agreed. The night itself comes later.")
    jump lanista_gate_exit_to_map

label lanista_arena_format_spectacle:
    call lanista_show_night_cutscene from _lanista_night_arena_format_spectacle
    call lanista_show_emotion("neutral") from _lanista_emotion_arena_format_spectacle
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "You draw the final card together beneath the empty stands. The Spectacle will bind steel, submission, and erotic display into one full Arena night."
    narrator "The opening exchanges remain combat. The decisive hold remains competitive. The result remains the one thing neither of you may purchase, predict, or command."
    narrator "After the victor is declared, both fighters may choose to continue into the pageant: armor surrendered, the earned hierarchy displayed, desire offered as a second truth rather than a false result."
    if lanista_is_dominion_route():
        narrator "You reserve final authority over pairings, presentation, and the length of every post-bout concession. The Lanista writes the safe limits beneath your design."
        call lanista_show_emotion("angry") from _lanista_emotion_spectacle_dominion
        lanista_npc "I set down every boundary clear-eyed, every inch. I know which truths remain mine and which you have taught this house to sell."
        lanista_npc "The winner will be real. So will each surrender after. That distinction is the last piece of my code you have allowed me to keep."
        $ lanista_dominion += 6
        $ lanista_affection += 3
        $ lanista_corruption = min(100, lanista_corruption + 12)
    else:
        narrator "The Lanista writes the compact personally: two consents, two purses, one right to stop, and no penalty for a fighter who wins the bout and refuses the pageant."
        call lanista_show_emotion("warm") from _lanista_emotion_spectacle_devotion
        lanista_npc "Eleven seasons I served a code, and you've gone and handed me a faith instead."
        lanista_npc "Not faith that desire is clean, or coin is kind. Faith that fighters can choose what their strength means after the sand has told the truth."
        $ lanista_devotion += 6
        $ lanista_affection += 4
        $ lanista_corruption = min(100, lanista_corruption + 4)
    call lanista_show_emotion("vulnerable") from _lanista_emotion_spectacle_climax
    narrator "The first Spectacle night runs exactly as the compact swore: the bout is real, the pin is real, the victor is nobody's choice but the sand's."
    narrator "Then the pageant opens over the won ground, armor set aside, the earned order shown, the wanting offered as its own second truth."
    lanista_npc "There. The last line I drew across eleven seasons, crossed in the open, with my own hand steady on where it must never go too far."
    narrator "The final slate is sealed. The Arena has not abandoned real combat; it has decided how much of the body may stand beside that truth."
    jump lanista_arena_format_spectacle_end

label lanista_arena_format_spectacle_end:
    $ lanista_spectacle_unlocked = True
    $ lanista_arena_program_tier = max(lanista_arena_program_tier, 3)
    $ lanista_arena_program_last_day = calculate_total_days()
    $ renpy.notify("The Spectacle unlocked for the Arena.")
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_wager_menu:
    if not arena_unlocked or arena_uses_successor():
        jump lanista_visit
    call lanista_restore_visit_scene from _lanista_restore_wager
    call lanista_show_emotion("amused") from _lanista_emotion_wager_menu
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    if not lanista_wager_intro_done:
        $ lanista_wager_intro_done = True
        narrator "A clerk sets a battered ledger on the bench beside the whetstone — narrow columns, small sums, and names you recognize from tonight's card."
        lanista_npc "The house runs a book on its own sand. Always has. The crowd bets at the gate; the owners bet with me."
        lanista_npc "The terms are plain. You back a fighter, I hold the coin, the sand decides. Your read holds, you walk out with double. It doesn't, the book keeps it."
        lanista_npc "And backing's not a seat in the stands. Your coin rides the fighter's name; by old custom of the sand, their purse answers to yours for the bout."
        lanista_npc "And here's the part the clerk won't say: I watch what an owner does with a win. What they do with a loss tells me more."
    $ _wager_card = lanista_wager_card(calculate_total_days())
    $ _wager_kind = _wager_card["kind"]
    $ _wager_left = _wager_card["left_name"]
    $ _wager_right = _wager_card["right_name"]
    $ _wager_opening = _wager_card["opening"]
    $ _wager_clue = _wager_card["clue"]
    $ _wager_left_read = lanista_wager_read_label(_wager_card, "left")
    $ _wager_right_read = lanista_wager_read_label(_wager_card, "right")
    # Devotion's freed partner covers half your seat at the book: the stake drops
    # to 250 (payouts still scale 2x/4x off the real stake). Everyone else pays
    # the full 500. Resolve it once here and thread it through every branch so
    # the guard, the labels, the wager call and the claim refund all agree.
    $ _wager_reduced = bool(lanista_ending_devotion and lanista_ending_done)
    $ _wager_stake = 250 if _wager_reduced else 500
    narrator "[_wager_opening]"
    if money < _wager_stake:
        lanista_npc "The smallest place in the book is [_wager_stake] coins. Come back with a purse worth opening."
        jump lanista_visit_menu
    if _wager_reduced:
        lanista_npc "The house covers half your seat now, [_ttl]. Old champions get a shorter reach into their partner's purse — [_wager_stake] opens the book for you."
    menu:
        lanista_npc "My read: [_wager_clue]\nBack the fighter your eyes believe."
        "Back [_wager_left]. ([_wager_left_read], stake [_wager_stake])":
            $ _wager_pick = "left"
            $ _wager_chance = lanista_wager_pick_chance(_wager_card, _wager_pick)
            $ _won, _delta = lanista_wager(_wager_stake, _wager_chance)
            jump lanista_wager_resolve
        "Back [_wager_right]. ([_wager_right_read], stake [_wager_stake])":
            $ _wager_pick = "right"
            $ _wager_chance = lanista_wager_pick_chance(_wager_card, _wager_pick)
            $ _won, _delta = lanista_wager(_wager_stake, _wager_chance)
            jump lanista_wager_resolve
        "Back out.":
            jump lanista_visit_menu

label lanista_wager_resolve:
    $ lanista_wager_last_day = calculate_total_days()
    # The menu always sets _wager_stake before jumping here; default defensively
    # to the full stake so a direct entry (or a stale session) still balances the
    # loss notify and the claim refund against the coin the wager actually took.
    $ _wager_stake = int(getattr(store, "_wager_stake", 500) or 500)
    $ _wager_profit = abs(int(_delta))
    $ _wager_pick_name = _wager_card["left_name"] if _wager_pick == "left" else _wager_card["right_name"]
    $ _wager_other_name = _wager_card["right_name"] if _wager_pick == "left" else _wager_card["left_name"]
    $ _wager_detail = lanista_wager_result_text(_wager_card, _wager_pick, _won)
    narrator "[_wager_pick_name] takes the sand opposite [_wager_other_name]. The clue is there in the opening exchanges, but steel always keeps a vote."
    narrator "[_wager_detail]"
    if _won:
        narrator "The clerk returns your stake with [_wager_profit] coins of profit."
    else:
        narrator "The clerk closes the book over your [_wager_profit]-coin stake."
    call lanista_show_emotion("amused" if _won else "angry") from _lanista_emotion_wager_result
    if _won:
        $ _wager_split = int(_wager_profit) // 2
        lanista_npc "Your read held, [_ttl]. Now show me what sort of winner it made."
        menu:
            "Split the profit with the fighter. The risk was theirs.":
                call lanista_show_emotion("warm") from _lanista_emotion_wager_win_share
                $ lanista_devotion += 2
                $ lanista_affection += 1
                $ money -= _wager_split
                $ renpy.notify("Profit shared: -{} coins (purse: {})".format(_wager_split, money))
                narrator "You send half the profit below before the sweat has dried. [lanista_name] watches the fighter receive it, then gives you a short nod meant for equals."
                lanista_npc "You remembered who stood on the sand. Good. A purse spends quickly; being valued lasts longer."
            "Stack every coin on the ledger. A win belongs to its backer.":
                call lanista_show_emotion("angry") from _lanista_emotion_wager_win_keep
                $ lanista_dominion += 2
                $ lanista_affection += 1
                $ renpy.notify("Wager won: +{} coins (purse: {})".format(_wager_profit, money))
                narrator "You count the full profit into your own purse while the fighter is still taking the crowd's applause. [lanista_name]'s eyes follow every coin."
                lanista_npc "The hand that risks the purse claims the return. Cold arithmetic, but honest. You do prefer the whole reward when you win."
    else:
        lanista_npc "The sand answered you. What you do with the answer matters more than the missing coin."
        menu:
            "My read was wrong. The fighter owes me nothing.":
                call lanista_show_emotion("warm") from _lanista_emotion_wager_loss_waive
                $ lanista_devotion += 1
                $ lanista_affection += 1
                $ renpy.notify("Wager lost: -{} coins (purse: {})".format(_wager_stake, money))
                narrator "You leave the loss where it fell. Word goes below that the backer waives the claim, and the fighter finally lets the held breath go."
                lanista_npc "A clean loss, admitted cleanly. Most owners punish the nearest body rather than their own judgment. Yours will fight the harder for you, knowing you don't."
            "Invoke the backer's claim. Their purse answers for my stake.":
                call lanista_show_emotion("angry") from _lanista_emotion_wager_loss_claim
                $ lanista_dominion += 2
                $ lanista_affection += 1
                $ lanista_corruption = min(100, lanista_corruption + 1)
                $ money += _wager_stake
                $ renpy.notify("Claim invoked: stake recovered (purse: {})".format(money))
                narrator "The book notes your claim before the fighter has washed off the sand. By the old custom, your lost stake becomes a debt on someone else's ledger."
                lanista_npc "The clerk counts your [_wager_stake] back into your purse from the fighter's own. So the risk runs downward and the profit runs up. The house will learn your arithmetic quickly, [_ttl]."
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_collect:
    if lanista_favor_balance <= 0 or lanista_aftercrowd_last_day == calculate_total_days():
        lanista_npc "Not today. A marker is spent once, and the night keeps one account at a time."
        jump lanista_visit_menu
    menu:
        lanista_npc "One favor. Choose what you mean to take, and spend it cleanly."
        "Collect a kiss." if lanista_collect_service_is_unlocked(1):
            $ _collect_tier = 1
            jump lanista_collect_spend
        "Order a private striptease." if lanista_collect_service_is_unlocked(2):
            $ _collect_tier = 2
            jump lanista_collect_spend
        "Demand oral service." if lanista_collect_service_is_unlocked(3):
            $ _collect_tier = 3
            jump lanista_collect_spend
        "Collect in full." if lanista_collect_service_is_unlocked(4):
            $ _collect_tier = 4
            jump lanista_collect_spend
        "Keep the favor.":
            jump lanista_visit_menu

label lanista_collect_spend:
    if lanista_favor_balance <= 0 or not lanista_collect_service_is_unlocked(_collect_tier):
        jump lanista_visit_menu
    $ lanista_favor_balance -= 1
    $ lanista_favors_collected += 1
    # Calling in a marker is the transactional act: it spends the debt you hold
    # over the Arena. The affection you earned by paying the debt down is the
    # very thing you now cash in, so the gain is CONVERTED — Devotion drops
    # (floored at zero) and the same amount presses the Dominion side, staining
    # the corruption along the way.
    $ _gain = 3 if _collect_tier >= 3 else 2
    $ lanista_dominion += _gain
    $ lanista_devotion = max(0, lanista_devotion - _gain)
    $ lanista_corruption = min(100, lanista_corruption + 1)
    $ lanista_collect_last_day = calculate_total_days()
    # Save/rollback compatibility: the historical t3/t4 labels are crossed.
    # Tier 3 is oral (t4); tier 4 is full service with the Dominion S4 CG (t3).
    # Do not rename or reorder these destinations without compatibility aliases.
    python:
        _collect_destination = {
            1: "lanista_collect_dom_t1",
            2: "lanista_collect_dom_t2",
            3: "lanista_collect_dom_t4",
            4: "lanista_collect_dom_t3",
        }.get(_collect_tier, "lanista_collect_dom_t1")
    $ renpy.notify("Favor collected: devotion turned to dominion. Favors owed: {}".format(lanista_favor_balance))
    call lanista_show_night_interior from _lanista_night_collect
    jump expression _collect_destination

label lanista_aftercrowd:
    $ _total_days = calculate_total_days()
    $ lanista_aftercrowd_last_day = _total_days
    $ _tier = lanista_aftercrowd_relationship_tier()
    $ lanista_aftercrowd_tier = _tier
    $ _vi = int(getattr(store, "lanista_aftercrowd_variant_index", 0) or 0)
    $ store.lanista_aftercrowd_variant_index = _vi + 1
    if _tier <= 3:
        call lanista_show_night_interior from _lanista_night_aftercrowd
    else:
        call lanista_restore_visit_scene from _lanista_restore_aftercrowd
    if lanista_is_devotion_route():
        jump expression "lanista_aftercrowd_dev_t{}".format(_tier)
    else:
        jump expression "lanista_aftercrowd_dom_intimate_t{}".format(_tier)

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
        narrator "The last torch is doused and the gate barred, and the Lanista opens the night armory before you can think to leave."
        narrator "Weapons and armor lie across the workbenches. Beyond the open bay, the empty bowl has gone quiet."
    else:
        narrator "The count is locked away and the great bowl stands empty, and [_they] catches your wrist at the armory door."
        narrator "Not hard, only sure, before leading you inside — the grip of someone who has decided the night isn't finished with you yet."
    lanista_npc "Stay a moment. This old room keeps better company when you're in it. I've stopped being ashamed to say so."
    $ _bust = "images/lanista/lanista_{}_kiss.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Then [_their] mouth is on yours, unhurried, the heat of the whole night's work still coming off [_them]."
    narrator "Hands settle at your back and hold — nothing unfastened, no hurry in it, only the long warm press of a fighter who has learned [_they] is allowed this."
    lanista_npc "There. That's the thing I bar the gate for now. Not the coin. This. Come back when the days have turned, [_ttl] — I'll be here."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

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
        narrator "The gate's barred and the torch in the night armory is guttering, and the Lanista doesn't wait for the dark to do the asking tonight."
        narrator "[_they] crosses to you with the night's heat still on [_them] and hands that already know the way."
    else:
        narrator "You're barely alone in the armory before [_they] has you backed against the cool stone wall, the want plain on [_them] now."
        narrator "No season of caution left to spend on hiding it."
    lanista_npc "I've thought of this the whole damned card. Counting the rounds till the gate could close on the rest of the world."
    $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "[_Their] mouth finds your throat as [_their] hands work the fastenings of your clothes loose, sure and unhurried, and you return the favor."
    narrator "The worn leather and linen coming open under your fingers, baring the banked heat of a body that no longer braces when you touch it."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You learn each other by hand and mouth in the dark, the last of the cloth fallen away, every breath shared and shaking."
    narrator "And [_they] holds you both to the edge of more and, with a low rough laugh, no further."
    lanista_npc "Not all of it tonight. ...Let me keep the wanting a while longer, [_ttl]. It's a finer thing than I knew, the wanting. Come back, and we'll spend the rest."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

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
        narrator "The gate is barred and the count is done, and [_they] walks you up the tunnel to the night armory without a word wasted."
        narrator "The question that hovered the first night long since answered, and answered yes."
    else:
        narrator "The armory holds only torchlight, long workbenches, and the two of you, and [_they] pulls you in close with the night's heat still on [_them]."
        narrator "Wanting you with none of the old careful hesitation."
    lanista_npc "No need to be clear-eyed about it anymore. I know the shape of what this is. Come here."
    $ _scene = "aftercrowd"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "He takes you down onto the broad bench without the old hesitation now and comes astride you the way he has learned to, and when he takes you into himself it is sure and slow and known."
        narrator "The sounds he once would have died before letting you hear spent freely into the space above your face."
    elif lanista_gender == "male":
        narrator "He braces up over you on locked arms, the way he did that first night — but there is nothing uncertain left in it now."
        narrator "He moves into you unhurried and sure, jaw set hard, and the strain in that face has stopped being disbelief."
        narrator "It is a man deliberately holding himself back, because he has finally learned there is no hurry and nobody is going to take this from him at dawn."
    elif _pt == "lord":
        narrator "She takes the deciding off you the way she always does now — a knee across, a slow settle, and she has you, upright and unhurried and entirely in charge of the pace."
        narrator "Her arms hang loose at her sides; there is nothing here she needs to hold on to. Her head goes back, chin high, eyes half shut on something far above and beyond you."
        narrator "And the soft broken breath she lets out when she takes you is a thing she stopped rationing seasons ago."
    else:
        narrator "She comes over you in the cooling dark the way she does now without thinking about it — braced above you, thigh locked across yours."
        narrator "Taking what she wants with not a trace of the old flinch left anywhere in her. Her face stays up where you can see it. Every sound she gives is familiar by now, and freely spent."
    lanista_npc "Stay till the lamp gutters, [_ttl]. We've the dark, and no one in it but us. It's grown to be my favorite hour of the whole count."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_aftercrowd_dev_t4:
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
        narrator "The gate is barred before the last of the crowd has cleared the road, and [_they] is on you the moment it falls."
        narrator "No patience left to spend, no part of [_them] still kept back."
        narrator "The whole long armored season of [_their] life burned down to wanting you and not caring who could see it."
    else:
        narrator "[_They] doesn't wait for the dark or the quiet tonight. [_Their] hands are in your clothes before the torches gutter out."
        narrator "The hunger plain and shameless on [_them], a fighter who has forgotten entirely how to brace."
    lanista_npc "I've nothing left to keep behind the guard. You took it all, and I let you, and I'd let you again tonight and every night the gate will bar. Come here. All of it. Now."
    $ _scene = "aftercrowd"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_aftercrowd_{}_{}_{}.png".format(_route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "There is nothing held back in him tonight — no armor to lower, because it is long gone, and gladly."
        narrator "He takes you astride under the open sky with the whole of his weight behind it, arms locked and carrying himself above your chest, mouth open on every sound he has and not one of them swallowed."
        narrator "A man wholly undone and no longer frightened to be seen so."
    elif lanista_gender == "male":
        narrator "He comes apart over you without a shred of the old fear, moving into you deep and greedy and unguarded, his breath wrecked against your hair."
        narrator "Every season of iron burned clean away in the heat of having you and meaning to keep on having you."
    elif _pt == "lord":
        narrator "She gives you all of it now, every gate flung wide — taking you into her with a hunger she stopped hiding seasons ago and breaking open under you quietly, mouth shut on it."
        narrator "The way she goes quiet at the things too large to make a noise about. Her arms stay folded up over her own breast, the last old reflex of a body that spent eleven seasons covering itself."
        narrator "And it fools neither of you: everything under them is yours, and she is looking straight up at you while she gives it."
    else:
        narrator "She abandons herself to you completely — comes down astride you and rides you shameless under the window."
        narrator "The proud body that once kept the world a blade away now spending itself with a low unguarded cry and a grin she doesn't bother hiding."
        narrator "Every wall she ever owned long since handed willingly into your keeping."
    lanista_npc "I don't brace for the morning anymore. ...You did that, [_ttl]. Stay. There's nothing left in me that wants you gone — there hasn't been for a long while now."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_aftercrowd_dom_intimate_t1:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    call lanista_show_emotion("angry") from _lanista_emotion_aftercrowd_dom_intimate_t1
    narrator "The armory lamp is already lit when you enter. The Lanista stands beside it with the day's armor still fastened and irritation arranged carefully across the face."
    lanista_npc "I waited for you. There — the humiliating truth, said before you could drag it out of me."
    narrator "You ask whether you were summoned. The hard mouth tightens."
    lanista_npc "No. If I had sent for you, I could pretend your presence was obedience. You came on your own. I find that matters."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_kiss.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "The kiss begins like an argument and ends with a scarred hand gripping your coat to prevent even an inch of retreat."
    lanista_npc "Go before I make a habit of expecting you, [_ttl]. Come back before I prove that was a lie."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_aftercrowd_dom_intimate_t2:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    call lanista_show_emotion("yielding") from _lanista_emotion_aftercrowd_dom_intimate_t2
    narrator "You find the Lanista seated on the armory's broad bench, gauntlets off, both scarred hands open on the knees as if resisting the urge to reach first."
    lanista_npc "I want you here. Not above me, not beneath me, and not because the house requires it. Here. That is an inconvenient distinction."
    narrator "You stand between those open knees. The Lanista draws you closer by the hips, pride intact and need no longer disguised as duty."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Your fingers work the laces of the worn jerkin loose, and [_they] lets you — the collar falling open to bare the scarred shoulder to the torchlight and your mouth both."
    narrator "Your mouth finds the old scar on that uncovered skin. The answering grip tightens until possession and fear of loss become impossible to separate."
    lanista_npc "Do not ask what this makes us. Stay until I stop needing the question."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_aftercrowd_dom_intimate_t3:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    call lanista_show_emotion("yielding") from _lanista_emotion_aftercrowd_dom_intimate_t3
    narrator "The gate falls. The Lanista catches your hand before the echo dies and pulls you into the night armory with no audience left to impress."
    lanista_npc "I hate the quiet when you leave. I spent eleven seasons guarding solitude as if it were strength, and now it sounds like absence."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_kiss.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "The confession costs more than the sudden kiss that follows it. You feel that cost in the fierce grip at your back and the breath breaking against your throat."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Clothes open by mutual impatience. On the broad bench the Lanista still fights for the upper hand, then clings after pleasure makes the contest meaningless."
    $ _scene = "aftercrowd"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_aftercrowd_{}_{}_{}.png".format(_route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    lanista_npc "You have made loneliness feel like losing. I despise you a little for that. Hold me while I decide how much."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_aftercrowd_dom_intimate_t4:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    call lanista_show_emotion("warm") from _lanista_emotion_aftercrowd_dom_intimate_t4
    narrator "There is no summons and no contest tonight. The Lanista closes the armory door, takes your face between both scarred hands, and looks for the refusal neither of you expects."
    lanista_npc "Stay because I asked. Not because I yielded, and not because you won. Stay because the night is poorer when you are elsewhere."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_kiss.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You answer by remaining. The old champion kisses you with the same fierce certainty once reserved for defending the sand."
    $ _scene = "aftercrowd"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_aftercrowd_{}_{}_{}.png".format(_route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    narrator "The night armory takes you both — the proud old champion spending its fierce certainty on you and not once looking away from what it is choosing to want."
    narrator "Later, tangled together beneath the low lamp, the Lanista keeps one hand over your pulse as though guarding proof that you have not vanished."
    lanista_npc "I can belong beside you without becoming less myself. That truth took me longer to learn than any hold."
    $ lanista_affection += 2
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_collect_dom_t1:
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
        narrator "You send word down the tunnel after the gate is barred, and the Lanista comes to the night armory — unhurried, composed, the cold dignity worn like the day's armor still buckled on."
        narrator "[_They] knows precisely why [_they] was summoned. [_They] comes anyway."
    else:
        narrator "The benches are empty and the night's coin is yours by every reckoning that matters. You wait in the armory."
        narrator "The Lanista finds you there, because both of you know that is how this goes now."
    lanista_npc "You've a use for me past the count, then. ...Say it plain. I'll not be summoned for nothing."
    $ _bust = "images/lanista/lanista_{}_kiss.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You take the proud jaw in your hand and bring that cold mouth to yours, and [_they] yields it the way [_they] yields everything to you."
    narrator "Without a sound of surrender, the composure flawless, the breath beneath it already gone uneven."
    lanista_npc "...There. You've collected. Keep your hands warm, [_ttl] — the body's the only part of me that ever answers you first. Go on. Come back when the days have turned."
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_collect_dom_t2:
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
        narrator "You keep [_them] back in the night armory when the gate is barred, a hand flat on [_their] chest."
        narrator "And the Lanista holds the cold composure while you take [_their] measure at your leisure."
        narrator "Both of you aware the stillness is a thing [_they] offers, not a thing [_they] feels."
    else:
        narrator "The night's coin is counted and yours, and you've a mind to collect the rest."
        narrator "[_They] comes when you bid [_them] to the armory, chin level, the champion's dignity buckled on."
        narrator "And underneath it, already, the body that has stopped keeping its secrets from you."
    lanista_npc "Collecting again. ...Go on, then. Take your measure of me. I'll keep my face. We both know that's all I'll manage to keep."
    $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You strip the worn leather from [_them] slow, [_their] eyes never leaving yours."
    narrator "The proud line of [_them] conceding nothing aloud — while the body under your hands answers every touch before the pride can think to forbid it."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_unbutton.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Bared, [_they] holds the champion's stillness to the last, breath gone uneven."
    narrator "The want coming off [_them] in waves [_they] will not name."
    narrator "And you take [_them] to the brink of more and stop there, deliberate, leaving the wanting to do its work."
    lanista_npc "...You'd leave it there. Cruel, [_ttl] — and well-judged. You know I'll come to the gate sooner for it. Go. I'll be counting the days I'll not admit to counting."
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_collect_dom_t3:
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
        narrator "The gate is barred and the house is yours. You wait in the night armory, the both of you long past pretending otherwise."
        narrator "You bid the Lanista to you, and [_they] comes with the cold dignity intact and the body beneath it already half lost to you."
    else:
        narrator "The armory door closes. You take the proud face in your hand the way you did at the first gate — but there is no stopping now, no terms to set, only the familiar reckoning."
        narrator "[_They] meets your eye, level and composed, a fighter who chose this ground seasons ago and returns to it still calling it a loss."
    lanista_npc "You'll have what you came for. ...You always do. Spare me the asking. Take it."
    $ _scene = "s4_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "He keeps the cold stare to the last, but his body has long stopped pretending — hard and ready before you've half undressed him."
        narrator "And when you set the pace the iron in his face holds while everything under it gives, breath by ragged breath, the surrender practiced now and still never once spoken."
    elif lanista_gender == "male":
        narrator "The composure stays nailed in place, the proud jaw unmoving — and then you point, and he kneels to it. No protest, no comment, because that is the shape of the collection now."
        narrator "He serves you with the same grim competence he brings to everything, eyes up the whole while, the bout lost on the same silent terms as every time before."
    elif _pt == "lord":
        narrator "She reaches for the champion's stillness out of habit and does not quite reach it — the head goes back, the teeth set, the colour climbs her throat."
        narrator "And her body answers you long before the pride can object, clenching and shuddering under the pace you set. Not one word of it crosses her lips. That much, at least, she still manages."
    else:
        narrator "She holds the cold dignity like a stance she has run a hundred times — right up until you draw her down between your thighs, and she goes."
        narrator "And sets that hard mouth to the work with the thoroughness she gives every duty she has ever hated and never once performed badly. The glare she keeps on you never softens by a single degree."
        narrator "It is the whole of the protest she has left, and she spends it, and serves you anyway, and neither of you has called that a contradiction in a long while."
    lanista_npc "...You'll get no words for it, [_ttl]. You never do. But you felt the answer, same as always. Let that stand as your receipt."
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_collect_dom_t4:
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
        narrator "You no longer summon [_them]; [_they] is already there when the gate falls, where [_they] is always now."
        narrator "The cold dignity is the last thing left standing in [_them] — a costume worn over a body schooled, season by season, to want your hand before you raise it."
    else:
        narrator "The gate bars on the richest night the house has ever known, and the Lanista comes to you composed as ever — chin level, gaze steady."
        narrator "And you both know the composure is the only thing [_they] still owns outright."
        narrator "And that you let [_them] keep it because it pleases you to."
    lanista_npc "The face is mine. ...Everything under it answers to you, and we've both long stopped pretending otherwise. Collect. I'm trained to it."
    if lanista_gender == "male":
        narrator "And he proves it before you have asked for anything: takes the studded harness down off its peg and buckles it on himself, straps drawn across the jaw, the beard pushed out of true."
        narrator "Unhurried, exact, the same hands and the same care he once gave the wrapping of his own knuckles. Then he stands and waits. Trained to it, as he said."
        narrator "The gear is his own doing, and that is precisely how he keeps the pride."
    else:
        narrator "And she proves it before you have asked for anything: takes the studded collar down off its peg, buckles it at her own throat, and settles the ring straight with one finger."
        narrator "Unhurried, exact, the same hands and the same care she once gave the wrapping of her own knuckles. Then she stands and waits. Trained to it, as she said."
        narrator "The gear is her own doing, and that is precisely how she keeps the pride."
    $ _scene = "aftercrowd"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_aftercrowd_{}_{}_{}.png".format(_route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "He has been trained to this, and to you, and it shows in every line of him. He lowers himself onto the thin bedroll at your feet without being placed there."
        narrator "A mat thrown down on bare flags, an old iron cuff lying forgotten against the wall a pace away, no other comfort in the room and none asked for."
        narrator "And takes you in his mouth around the straps, patient and thorough and entirely composed, the cold eyes never once leaving yours."
        narrator "The proud frame gives you exactly the pace you set and exactly the pleasure you allow it, like the well-broke thing it has become for you alone."
    elif lanista_gender == "male":
        narrator "The dignity is reflex now, a habit worn paper-thin over a body that belongs to you in every way that matters."
        narrator "He goes down between your thighs before you have finished settling back, mouth to you through the buckled leather, breath hot and even."
        narrator "Working with the flat professional patience of a man who has been given a task and has never in his life done one badly."
        narrator "The surrender needs no words and gets none — only the ragged proof, by the end, of how thoroughly he is yours."
    elif _pt == "lord":
        narrator "She wears the champion's composure like a costume now, both of you knowing what's underneath it. She kneels to your lap on the bare stone without waiting to be told."
        narrator "The ring swinging once at her throat as she settles, and sets to it thorough and unhurried, giving you the whole of it and none of the feeling."
        narrator "You raise a hand — to steady her, to grip, you don't finish deciding — and let it fall short, because she doesn't need steering and you both know it."
        narrator "Owned down to the breath, and far past pretending otherwise."
    else:
        narrator "Her pride is a formality between you now, the cold stare held over a body you have trained to your hand season by season."
        narrator "She settles between your thighs the moment you lie back, tongue and mouth and that steady terrible attention, the collar dark under her jaw, her eyes rolled up to hold yours through the whole of it."
        narrator "She serves you until you tell her to stop and not one breath longer. The silence isn't defiance anymore, only the last small thing she keeps."
    lanista_npc "Collected in full, as ever. ...Don't look so pleased, [_ttl]. We both know whose hand I answer to now. Go — before I forget I once didn't."
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_gift:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _total_days = calculate_total_days()
    $ _items = lanista_get_giftable_items()
    if not _items:
        narrator "You take stock of what you have on hand to offer, and come up short — nothing in your stores a fighter who measures everything by its use would thank you for."
        lanista_npc "Empty hands, [_ttl]? No shame in it. Come back when you've a thing worth the carrying. I'm not going anywhere."
        jump lanista_visit_menu
    python:
        # NOTE: renpy.display_menu treats a None value as a non-selectable
        # caption, so the cancel option uses an explicit sentinel string.
        _choices = []
        for _iid, _name, _qty in _items:
            _choices.append(("{} (x{})".format(_name, _qty), _iid))
        _choices.append(("Never mind — keep what I have.", "__cancel__"))
        _picked = renpy.display_menu(_choices)
    if _picked is None or _picked == "__cancel__":
        jump lanista_visit_menu
    $ _removed = lanista_remove_gift_item(_picked, 1)
    if not _removed:
        narrator "You reach for it and find it already gone from your stores."
        jump lanista_visit_menu
    $ store.manager_inventory = list(getattr(store, "manager_inventory", manager_inventory))
    $ _gdata = LANISTA_GIFTS.get(_picked, (1, 0, 1))
    $ lanista_devotion += _gdata[0]
    $ lanista_dominion += _gdata[1]
    $ lanista_affection += _gdata[2]
    $ lanista_last_gift_total_days = _total_days
    $ lanista_gifts_given += 1
    call lanista_show_emotion("warm") from _lanista_emotion_gift_base
    if _picked == "champion_hand_wraps":
        narrator "[lanista_name] runs a thumb along the fresh linen, testing the weave, then winds one strip around a scarred hand with practiced care."
        lanista_npc "Cut to the right width. Strong enough to hold, soft enough not to bite. You noticed what my hands need, [_ttl]. That is rarer than flattery."
    elif _picked == "arena_whetstone":
        narrator "[lanista_name] draws the whetstone from its case and tests one corner against a practice blade. The steel answers with a clean, even whisper."
        lanista_npc "Good grain. No painted crest pretending to make poor stone better. You brought me a tool, not a decoration. Sit; you can watch me put it to use."
    elif _picked == "iron_oath_chain":
        narrator "The black chain hangs between you from [lanista_name]'s fist, the Arena's crest turning once in the lamplight before the links go still."
        lanista_npc "A promise made into iron. You do like your meanings plain. I'll keep it, [_ttl], but don't mistake acceptance for ignorance. I know which hand you expect to hold the other end."
    elif _picked == "elixir_passion":
        narrator "The Lanista turns the little bottle to the lamplight, reads what it is, and sets it down on the bench very precisely — the way one sets down a thing one would rather throw."
        call lanista_show_emotion("angry") from _lanista_emotion_gift_elixir
        lanista_npc "A draught to make a body want. ...You've had every want I've got, [_ttl], and not one drop of it came from a bottle. Don't bring me this again. We'll say no more on it."
    elif _picked == "fine_wine":
        narrator "The Lanista works the cork loose with a thumb, sniffs once, and grants it the grunt that passes for approval."
        lanista_npc "Strong, and honest about being so. Eleven seasons I drank what the cot provided and called it luck when it didn't blind me. This is better, [_ttl]. Sit. We'll halve it."
    elif _picked in LANISTA_GIFT_SALVES:
        narrator "The Lanista weighs the vial, understanding at once what it's for — and that you chose it knowing exactly where the old wounds sit."
        lanista_npc "A salve for the knee. ...You watched me cross the yard and you counted the hitch. Most don't. Fewer still do anything about it. My thanks, [_ttl]. I'll not waste it on pride."
    elif _picked in LANISTA_GIFT_BLADES:
        narrator "The Lanista takes the blade across both palms, sights down the edge, and tests the balance with a slow turn of the wrist — reading it the way another would read a letter from home."
        lanista_npc "Now this is a thing chosen by someone who knows what I am. Good steel, balanced true. You could have brought me silk and scent. You brought me a blade. You see me clear, [_ttl]. That's the rarer gift of the two."
    else:
        narrator "The Lanista accepts it with a short nod, turning it over once before setting it aside."
        lanista_npc "Thoughtful of you, [_ttl]. I'll find a use for it. I find a use for most things."
    if _picked != "elixir_passion":
        $ _gift_route = getattr(store, "lanista_ending_route", "") or lanista_determine_ending()
        if _gift_route == "dominion":
            lanista_npc "You keep a fair ledger, [_ttl]. I'll remember which column this one's entered under."
        elif _gift_route == "mixed":
            lanista_npc "Half thanks and half tally, [_ttl] — and I'll not sort the two tonight. That's the arrangement."
        else:
            lanista_npc "A gift with no bill behind it. I'd near forgotten the shape of one. My thanks, [_ttl]."
    $ lanista_recalculate_stage()
    jump lanista_visit_menu

label lanista_assess:
    $ lanista_recalculate_stage()
    $ _story = lanista_story_state()
    $ _story_reason = _story.get("reason", "")
    $ _route = getattr(store, "lanista_ending_route", "") or lanista_determine_ending()
    $ _corr = int(getattr(store, "lanista_corruption", 0) or 0)
    $ _corr_tier = lanista_corruption_tier()
    $ _corr_label = _corr_tier[1]
    $ _corr_traits_str = ", ".join(_corr_tier[2]) if _corr_tier[2] else "none"
    $ _program = max(0, min(3, int(getattr(store, "lanista_arena_program_tier", 0) or 0)))
    $ _program_name = ["Basic combat only", "Bikini Bouts", "Oil & Chains", "The Spectacle"][_program]
    $ _route_pretty = {"devotion": "Your Partner", "dominion": "Broken Champion", "mixed": "Reluctant Gladiator"}.get(_route, _route or "Undecided")
    if lanista_devotion > lanista_dominion:
        narrator "When [lanista_name] looks at you, the guard eases before pride brings it back. Trust is winning ground, and your presence no longer feels like a threat."
    elif lanista_dominion > lanista_devotion:
        narrator "[lanista_name] watches your hands, your purse, and every pause before you speak. Resistance remains, but so does the relief of knowing you will decide."
    else:
        narrator "[lanista_name]'s attention lingers without settling into trust or surrender. The feeling is there, guarded and unresolved, waiting on what you choose next."
    if not lanista_ending_done:
        narrator "[_story_reason]"
        if lanista_debt_finance_unlocked and not lanista_finance_track_complete():
            narrator "The Arena's creditors remain unsettled."
        if _route == "mixed":
            narrator "Neither lead has pulled far enough ahead to name the ending yet. Held that way to the last, the terms settle as the Reluctant Gladiator's."
            narrator "A life kept half in your hands — by your choosing, not by indecision."
    if lanista_ending_done:
        if _route == "devotion":
            narrator "The old vigilance has softened into certainty. [lanista_name] meets you as a partner and no longer searches your kindness for a hidden price."
        elif _route == "dominion":
            narrator "The pride remains, but it rests inside the order you set. [lanista_name] knows where to stand, and the certainty has become its own kind of peace."
        else:
            narrator "Love and service pull at [lanista_name] in equal measure. Neither feeling has won, and neither is false; the strain shows, but so does the choice to keep both."
        narrator "Devotion [lanista_devotion] | Dominion [lanista_dominion] | Affection [lanista_affection]."
        narrator "Corruption [_corr]/100 ([_corr_label]) | Arena Program [_program]/3: [_program_name]."
        narrator "Traits: [_corr_traits_str]."
        narrator "Owed favors [lanista_favor_balance] | Ending: [_route_pretty]."
    else:
        narrator "Stage [lanista_stage] | Devotion [lanista_devotion] | Dominion [lanista_dominion] | Affection [lanista_affection]."
        narrator "Corruption [_corr]/100 ([_corr_label]) | Arena Program [_program]/3: [_program_name]."
        narrator "Traits: [_corr_traits_str]."
        narrator "Owed favors [lanista_favor_balance] | Outlook: [_route_pretty]."
    jump lanista_visit_menu

label lanista_s3_gate:
    call lanista_show_night_cutscene from _lanista_night_s3_gate
    if lanista_remark_choice("s2_r1") == "devotion":
        lanista_npc "You understood why the old belt stays close without asking me to wear it. Few ever understood the difference."
    elif lanista_remark_choice("s2_r1") == "dominion":
        lanista_npc "You once ordered me to wear the old belt so you could measure what still obeyed. I have not forgotten the order."
    else:
        lanista_npc "You never asked me to explain the old belt. Some silences have weight of their own."
    if lanista_is_dominion_route():
        jump lanista_s3_gate_dominion
    else:
        jump lanista_s3_gate_devotion

label lanista_s3_gate_devotion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "The gates are barred for the night. The armory torch burns low, and the stars hang over the empty bowl beyond the open bay. You are the only living things left in the house."
    narrator "You came to talk numbers. The numbers have run out, and what's left in the quiet is something neither of you has dared to name in daylight."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "Eleven seasons I've kept everyone the length of a blade away. It's how you stay standing. You let no one close enough to land the killing one."
    lanista_npc "And here you are. Inside my guard. I let you walk in, and I haven't the will to put you back out."
    narrator "The Lanista steps in — close, closer than the craft allows, close enough that you feel the heat coming off bare skin under the worn harness, skin that's known nothing but distance for years."
    narrator "A scarred hand rises and stops, hovering at your jaw, asking the question it won't say."
    $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You answer it. You close the last of the distance yourself, and the kiss is nothing like the iron the Lanista wears all day."
    narrator "It's tentative, almost startled, a fighter discovering a thing no amount of training ever taught."
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "And when your hand falls away from his jaw he catches it — catches it the way a man catches something he is afraid of dropping — and holds it there between you, and does not give it back."
    else:
        narrator "And then the whole weight of [_them] comes with it, and you are going backwards — the bench, the gate-post, it hardly matters which."
        narrator "And [_they] plants a scarred hand down on either side of you and stops there, braced, caging you in the moonlight. Not touching."
        narrator "Only close, and breathing like someone who has run a long way to arrive."
    $ _scene = "s3_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    if lanista_gender == "male" and _pt == "lord":
        narrator "Then he turns it over and sets his mouth to the back of it — beard rough, eyes never once leaving yours. A fighter's homage, offered to the one who stayed, in an empty house with nobody left to witness it."
        narrator "It costs him more than the kiss did, and you both know it."
    else:
        narrator "Then [_they] stills there above you, holding [_their] own weight off you by main strength."
        narrator "And lets you look your fill at what the iron has been covering all season."
    narrator "And it is the Lanista who breaks it — a hand flat on your chest, gentle, setting a hand's breadth of cold air back between you."
    narrator "The breath that follows is ragged in a way you've never heard from that iron throat."
    lanista_npc "Not like this. Not tonight."
    lanista_npc "Not with the lenders' number hanging over us both and me half able to tell what's want and what's drowning. When I take you — if I take you — it'll be clear-eyed. You're worth a clear head. I'll not give you less."
    call lanista_show_night_cutscene from _lanista_night_s3_gate_dev_menu
    call lanista_show_emotion("warm") from _lanista_emotion_s3_gate_dev_menu
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
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "The gates are barred and stars hang over the empty bowl beyond the armory. The night's count came up short again, and you both know whose coin stands between this Arena and the dark."
    narrator "You've spent weeks letting that truth settle over the bench like dust. Tonight you stop letting it settle. You step in close, and you let the Lanista feel the full weight of what's owed."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "So that's the way of it. The purse comes to collect, and what it wants isn't coin."
    lanista_npc "I've put down bigger than you on that sand. Don't mistake the debt for a leash."
    narrator "But the jaw is set too hard, and you both know the books don't lie. You hold the Lanista's eye and don't look away, and the silence does the arguing for you."
    narrator "Slowly — every inch of it a fighter's surrender, ceded and not given — the distance closes."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You take the Lanista's jaw in your hand and turn that proud face to yours. The kiss is yours to take, and you take it."
    narrator "And the Lanista yields it with a cold, furious dignity, mouth answering yours, arms up and locked and nowhere near you, corded to the shoulder, hands that will not, will not close on you first."
    narrator "No begging. Not a sound of it. Only the hard breath in the moonlight, the iron control bending one degree at a time."
    narrator "The spectacle of a champion who has decided to lose this bout on terms of [_their] own choosing."
    $ _scene = "s3_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    narrator "Then you're the one who steps back — because taking it all tonight would be too easy, and easy isn't the same as owned."
    narrator "The Lanista watches you put the distance back between you with a flicker of confusion, as though the body has not understood the retreat. Beneath it, the heat remains, drawn taut across the space you have left."
    narrator "You leave the Lanista standing there, breath uneven, the proud line of the shoulders the only thing still holding."
    lanista_npc "...That's enough. You've made your point."
    lanista_npc "You'll have the rest when I decide it, not when the ledger does. I yielded the bout. I didn't hand you the whole sand. Remember the difference."
    call lanista_show_night_cutscene from _lanista_night_s3_gate_dom_menu
    call lanista_show_emotion("yielding") from _lanista_emotion_s3_gate_dom_menu
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
    jump lanista_gate_exit_to_map

label lanista_s4_gate:
    call lanista_show_night_cutscene from _lanista_night_s4_gate
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    narrator "The last creditor leaves with a receipt, a marker, or the promise of another payment. The gate bars behind the day's final bout."
    narrator "Nothing has been solved between the two of you. Enough has been survived that neither of you can pretend the pull is merely business."
    narrator "The Lanista sets the lamp on the night armory's scarred workbench. A broad bench waits nearby, with the empty bowl visible beyond the open bay."
    narrator "Silence follows when two people stop finding reasons to leave."
    if lanista_remark_choice("s3_r2") == "devotion":
        lanista_npc "You put your hand beside mine on the coin box and asked for nothing. That kindness followed me here."
    elif lanista_remark_choice("s3_r2") == "dominion":
        lanista_npc "You told me I knew the box's weight. You were right, and you learned how much that truth could move me."
    else:
        lanista_npc "You left the coin box unremarked. It did not make the weight inside it any lighter."
    if lanista_is_dominion_route():
        jump lanista_s4_gate_dominion
    jump lanista_s4_gate_devotion

label lanista_s4_gate_devotion:
    call lanista_show_emotion("vulnerable") from _lanista_emotion_s4_gate_devotion
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    lanista_npc "Eleven seasons I kept everyone a blade away. Tonight I have no wish to send you back across that distance."
    narrator "The Lanista crosses it first and places a scarred hand against your jaw, steady enough for combat and uncertain only here."
    narrator "The kiss is long, deliberate, and fully clothed. When it ends, neither of you retreats."
    menu:
        "\"Stay. Nothing else has to happen tonight.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 4
            narrator "You remove the demand from the invitation. The relief in the hard face is small, unmistakable, and more intimate than haste would have been."
            lanista_npc "Stay without taking the rest. ...You make patience feel less like mercy and more like trust."
        "\"Let me inside the guard. Only as far as you choose.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 4
            narrator "The Lanista sets your hand over the old scar at the shoulder, choosing the boundary and permitting you to remain within it."
            lanista_npc "There. No farther tonight. It is farther than anyone has stood in years."
    $ _scene = "s4_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    narrator "You remain together on the broad bench until the lamp gutters, shoulder against shoulder, the old armor still fastened and no longer serving as distance."
    jump lanista_s4_gate_end

label lanista_s4_gate_dominion:
    call lanista_show_emotion("yielding") from _lanista_emotion_s4_gate_dominion
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    lanista_npc "The day's account is closed. You did not come here for another column. Say what you expect."
    narrator "You order the Lanista to remain when the lamp burns low. The chin stays level; the door stays shut."
    narrator "You take the proud jaw in your hand and claim a kiss slowly enough that refusal would still have room to exist. None comes."
    menu:
        "\"Keep your armor. Give me the night.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 3
            narrator "You leave every buckle closed and take the rarer concession: the Lanista stays because you told [_them] to stay."
            lanista_npc "The night, then. Do not mistake restraint for a lack of appetite. It is the last courtesy either of us has left."
        "\"Hands on the bench. Look at me while you stay.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 3
            narrator "The command is obeyed without theatrical surrender. Scarred hands settle on the wood, and the cold gaze remains locked on yours."
            lanista_npc "You have the obedience you asked for. The rest still waits on a harder bargain."
    $ _scene = "s4_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    narrator "The lamp gutters with the two of you still clothed and still measuring the distance that remains. Neither pretends the night was innocent."
    jump lanista_s4_gate_end

label lanista_s4_gate_end:
    $ lanista_s4_gate_fired = True
    $ lanista_night_visit_total_days = None
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_morning_after:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    narrator "Morning comes in low and gold through the open shutter, laying a long bar of light across the scarred table and across the two of you. For a while neither of you moves."
    narrator "The house beyond the door is silent in a way it never is by day — no crowd, no count, no craft to keep. Only the light, and the warmth, and the slow rise and fall of breath."
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Then the Lanista rises and sits at the edge of the broad bench, back half-turned to you, and reaches for the long strips of linen."
    narrator "[_They] begins to wrap [_their] hands — the same ritual that comes before every bout, knuckle and wrist."
    narrator "The old habit of a body readying itself to be hit."
    narrator "But slower than you have ever seen it done. No snap to the linen, no economy in it."
    narrator "[_They] does not look at you while [_their] hands find the familiar work, and the not-looking says all the thing the wrapping is meant to hide."
    narrator "That the iron has somewhere been breached, and the body is reaching, by old reflex, for the only armor it has ever owned."
    lanista_npc "...Don't say anything yet, [_ttl]. Let me get my hands wrapped first."
    call lanista_show_emotion("vulnerable") from _lanista_emotion_morning_after
    narrator "When the last strip is tucked and tied, [_they] finally turns and looks at you — and the look, for all the linen, is not armored at all."
    jump lanista_visit_menu

label lanista_s5_gate:
    call lanista_show_night_cutscene from _lanista_night_s5_gate
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "It is done. The Governor's number is met — cleared in full, the date struck, the notice torn from the gate as though it never bit there."
    narrator "Whether the coin came as a gift with no hook in it, or as the closing of a debt that was always going to be settled in flesh, the Arena opens its gates tomorrow under its own name."
    narrator "Tonight it answers to no lender, no Governor, and no count."
    narrator "The great bowl stands empty and barred. The last torch gutters at the tunnel mouth. There's nothing left standing between you now — no debt, no code, no armor worth the name."
    narrator "Only the thing a whole season has been driving toward, with nowhere left to go but the body."
    narrator "The Lanista has taken the lamp and walked you up the tunnel without a word, into the night armory."
    narrator "The armory waits beyond: scarred workbench, broad bench, weapons and armor left in the torchlight, and the empty bowl under the stars."
    narrator "The door is pulled to. Out there the house is a ruin saved. In here it is only the two of you."
    if lanista_remark_choice("s4_r2") == "devotion":
        lanista_npc "You said the new colors were not mine and let me keep the old ones in your eyes. I needed that more than I admitted."
    elif lanista_remark_choice("s4_r2") == "dominion":
        lanista_npc "You watched the new colors rise and left the old sigil in the dust. You knew which Arena you meant to keep."
    else:
        lanista_npc "You said nothing about the colors over the gate. I had to decide for myself what still belonged beneath them."
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
    lanista_npc "You saved it asking nothing. I've turned that over a hundred times and still can't make it balance — because it doesn't. It was never a trade. Whatever I am now, I'm it with you and not for you."
    lanista_npc "There's a world of difference, and you're the one who taught it to me."
    narrator "The Lanista crosses the little room to you, and there's no iron left in the approach — no fighter's economy, no held guard."
    narrator "[_They] comes the way the grief and the wanting come, together and unhidden, a body that has stood armored against the whole world for eleven seasons walking out with the armor laid."
    narrator "Down in the dust behind."
    $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "[_They] reaches for the fastenings of [_their] own clothes, then stops, and lets you do it instead."
    narrator "Lets you bare [_them] slow, the worn leather and linen falling away, the scarred map of the body given over to your hands with nothing held back."
    narrator "[_They] does not brace this time. There's no blow coming, and [_they] knows it."
    narrator "And the knowing is the thing that undoes [_them]."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Where [_they] once braced for the strike, [_they] finds your mouth, your hands, the slow warmth of being wanted with no ledger behind it."
    narrator "Something in [_them] breaks open at that — quiet and enormous."
    narrator "And the breath [_they] lets go is the sound of a guard wholly, finally lowered."
    menu:
        "\"Grieve it here, then. The fighter, the code, all of it. I've got you while you do.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You don't tell [_them] the grief is misplaced. You only open your arms to it and let [_them] bring the whole weight."
            narrator "The dead champion, the buried code, eleven seasons of standing alone — and set it down against you in the dark."
            narrator "[_They] shakes once, hard, and then [_their] hands find you and do not let go."
            lanista_npc "Here, then. With you. ...I buried the best of me this season and never let myself mourn it. You hand me the leave to, and a shoulder to do it on. I'll waste neither."
        "\"No more armor. Not tonight. Just you, and me, and nothing owed in either direction.\"":
            $ lanista_affection += 4
            $ lanista_devotion += 2
            narrator "You say it like the simple truth it is, and you watch [_them] decide to believe it."
            narrator "The last of the iron going out of the proud frame, the body in your hands braced for nothing now but you. Nothing owed. Nothing collected. Only this."
            lanista_npc "Nothing owed. ...Eleven seasons every touch came with a bill behind it, mine or theirs. You strip even that away. There's nothing left of me to defend, and I find I don't want to. Take me as I am. There's no other version left."
    $ _scene = "s5_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "He comes down over you in the moonlight, and there's nothing of the champion in it — only the man, scarred and grieving and wanting, learning your body the way he once learned the only craft he had."
        narrator "He settles astride you and takes you into himself, slow and shaking and certain, holding his own weight off you on arms that will not stop trembling."
        narrator "And the low sound he spends is grief and relief in one breath: a man who has set down a weight he carried half a lifetime and found something waiting underneath to hold him up."
    elif lanista_gender == "male":
        narrator "He gathers you in against the warm, scarred bulk of him, and the hands that have only ever known the grip of a weapon move over you as if afraid you'll prove a dream."
        narrator "Then he works his way down you, unhurried, and settles between your thighs, and puts that hard mouth to the tenderest service a fighter ever learned."
        narrator "Patient, reverent, taking his whole time about it, eyes coming up to find yours every so often as though to check you are still real. The iron is wholly gone from him."
        narrator "There is only a man grieving and wanting and, for the first time in his life, permitted."
    elif _pt == "lord":
        narrator "She comes apart under you by slow degrees — the iron set of her loosening, the proud strength gone warm and pliant and willing."
        narrator "When you take her thighs in your hands and move into her she meets you with a low, broken sound and then folds both arms up behind her own head, elbows wide."
        narrator "Offering you the whole unguarded length of her: throat, breast, ribs, every place a fighter spends a lifetime keeping covered. Nothing held back and nothing defended."
        narrator "She gives you every sound she has, and she gives them all unarmored."
    else:
        narrator "Tonight there is no learning left to do; there is only being let in. She comes down over you and puts her forehead to yours first and stays there a beat too long."
        narrator "A fighter making certain of the ground before she trusts her weight to it. Then she gives you all of it at once, with none of the careful ordering of that first night."
        narrator "Hands, mouth, the whole grieving heat of her, taking and being taken in the same breath because she could not tonight tell you which she needs the more of."
        narrator "She spends every sound she has and does not once apologise for the shaking."
    narrator "After, the two of you lie tangled in the cooling dark, and the Lanista holds on to you the way a fighter holds the ground they've bled for."
    narrator "Not afraid of losing it now, only unwilling, after so long alone, to let it go a moment before [_they] must."
    lanista_npc "Whatever I was, [_ttl] — I grieved it tonight, and I'll not grieve it again. What's left, you've seen the whole of. The armor's off, and it stays off, for you. That's the bargain, and I've never struck a truer one. Stay till morning."
    lanista_npc "I find I can sleep when you're here."
    jump lanista_s5_gate_end

label lanista_s5_gate_dominion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _theirs = lanista_pronoun("poss_pron")
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
    lanista_npc "It's done, then. The number's gone, the Governor's date is ash, and the whole of it sits on the one bill we never wrote down. I came to pay it. Don't expect me to come cheaply — a debt this size, a body settles slow."
    narrator "[_They] crosses the little room to you with the champion's bearing fully intact — chin level, shoulders square, every step the measured advance of a fighter who has chosen the ground."
    narrator "The price is understood. [_They] has come to pay it in full, on [_their] feet, with the one thing the debt could never strip away held high: the manner of the paying."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You strip the worn leather from [_them], and [_they] lets you."
    narrator "Every fastening a fortress ceded on terms, the cold dignity never once leaving [_their] face."
    narrator "The body answers your hands long before the pride will allow it, and [_they] makes no move to hide the fact and none to confess it."
    narrator "This is the bargain: you take, [_they] pays, and the pride keeps its feet through the whole of the transaction."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Bared, [_they] holds the stillness of a fighter at the center of the bowl."
    narrator "Even so, want comes off [_them] in waves [_they] will not name."
    narrator "The composure is a final stance held against everything [_their] body has already decided. [_They] will pay every copper of this."
    narrator "[_They] will not, to the last breath, be caught in the act of wanting to."
    menu:
        "\"Pay it in full. I'll take every copper. You may keep the one thing you brought — your pride.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            narrator "You name the one mercy in the whole transaction, and you name it plainly — that the pride is [_theirs] to keep, the only line of credit you'll extend."
            narrator "Something flickers behind the cold eyes, caught and refusing to own it, and the proud jaw sets all the harder, which tells you everything the mouth will not."
            lanista_npc "My pride. You'll take the whole of the rest and leave me that. ...You're a thorough collector, and a stranger sort of merciful one. Have your full measure, then."
            lanista_npc "I'll pay it standing, I'll keep my feet, and we'll both call that the bargain."
        "\"Your terms for the manner, mine for the taking. Settle it like that and we both walk away square.\"":
            $ lanista_affection += 3
            $ lanista_dominion += 2
            narrator "The cold composure holds, but something behind it eases — you've left the pride its footing even as you claim the rest."
            narrator "And a fighter knows to the copper the worth of being allowed to settle a debt standing up."
            lanista_npc "My manner, your taking. ...You'd grant me that, with the whole of me already on your books. The one creditor who lets the debtor keep their bearing through the paying. Small wonder I stopped trying to be rid of you."
            lanista_npc "Square it, then — on those terms. I'll meet you copper for copper."
    $ _scene = "s5_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "There is no ceremony, and he permits none. He undresses like a man stripping for the scales — exact, itemized, nothing lingered over."
        narrator "Then he turns from you, lays himself face-down across the scarred table, and spreads his arms flat on the wood to either side, the way goods are laid out to be weighed."
        narrator "When you take him from behind and set the pace of the settling, he renders what the terms demand and not a breath more."
        narrator "Strength, heat and shudder are counted out on the boards like coin on a counting-table. Once, only once, his head turns back over his shoulder — not for mercy."
        narrator "He wants you to know he is watching the sum come off him. It is thorough and exact."
        narrator "It is the coldest, most complete payment you have ever collected, and when the ledger closes you both hear it."
    elif lanista_gender == "male":
        narrator "No first-night disbelief tonight, and no armor either — armor is for bouts, and this is commerce. He presents the account the way a merchant presents a bill: squarely, itemized, due."
        narrator "Then he goes down between your thighs and pays it with his mouth — each installment rendered as it falls, the tongue as exact as the hand that used to chalk the card."
        narrator "Nothing offered the terms don't require and nothing withheld that they do. He keeps his eyes on yours through the whole settlement. Nothing is given. Everything is paid."
        narrator "The distinction is the whole of his pride now, and he keeps it to the last copper."
    elif _pt == "lord":
        narrator "She has priced the night already; you can see the arithmetic sitting behind the level eyes. She neither braces nor softens."
        narrator "She opens the account and lets you draw against it. When you reach for the bed, she shakes her head once and goes down onto the bare flags instead, palms flat to the cold stone, hips raised."
        narrator "A debt is paid where the creditor stands, and comfort was never in the terms. When you take her from behind and set the pace, she meets it like an obligation squarely met."
        narrator "The clench, the shudder, the heat rendered up on schedule, the face turned back over her shoulder to watch you collect — a creditor's receipt recording the sum and none of the feeling."
        narrator "Only at the very end does the count slip — one breath, badly kept — and she folds even that back into the books as a debt to settle later."
    else:
        narrator "She undresses like a woman itemizing collateral and stands to be appraised without a flicker. This is commerce, and she has decided to be good at it."
        narrator "Then she kneels between your thighs and pays out the account with her mouth, with a bookkeeper's precision."
        narrator "Enough to satisfy the terms, delivered on time and in full, nothing in it that could ever be mistaken for a gift."
        narrator "She holds your eye from down there the entire time, and that is the part that costs her, and she does not look away. It is colder than the first surrender, and more absolute."
        narrator "That night her body betrayed her. Tonight she has signed the betrayal over in advance, and files it under settlement."
    narrator "After, [_they] lies back in the dark and lets the composure reassemble itself piece by piece."
    narrator "Slower than [_they] would wish, and you both know precisely why. The debt is paid. The dignity is kept."
    narrator "Nothing else in the bowl belongs to [_them] now, and [_they] has known that for a season."
    lanista_npc "There. Paid in full, [_ttl] — and you'll mark that I paid it with my pride intact."
    lanista_npc "That's the last of me that was ever mine to keep, and I kept it, and I'd thank you not to price it for less than it cost. The rest is yours. It's been yours."
    lanista_npc "Tonight only made the books agree with the truth."
    jump lanista_s5_gate_end

label lanista_s5_gate_end:
    $ lanista_s5_gate_fired = True
    $ lanista_night_visit_total_days = None
    $ lanista_affection = max(lanista_affection, 100)
    $ lanista_corruption = min(100, lanista_corruption + 5)
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

label lanista_s6_gate:
    hide lanista_bust
    hide lanista_bg_dim
    window hide
    $ _s6_study_bg = "images/buildings/study_night.png" if renpy.loadable("images/buildings/study_night.png") else "images/event_bg.png"
    scene expression _s6_study_bg
    show black as lanista_bg_dim:
        alpha 0.15
    with dissolve
    if lanista_remark_choice("s5_r2") == "devotion":
        lanista_npc "You stayed while I threw punches at the dead and asked for nothing but that I stop. I remember who made stopping possible."
    elif lanista_remark_choice("s5_r2") == "dominion":
        lanista_npc "You saw me exhausted and called it bargaining ground. I remember exactly what you chose to measure."
    else:
        lanista_npc "You let the dead keep their silence. I had to decide alone when I was finished fighting them."
    # Lock the route at scene entry so the gate shown == the ending recorded
    # (mid-scene menu nudges can't flip a borderline player between scene and gate_end).
    $ lanista_ending_route = lanista_determine_ending()
    if lanista_ending_route == "dominion":
        jump lanista_s6_gate_dominion
    elif lanista_ending_route == "mixed":
        jump lanista_s6_gate_mixed
    else:
        jump lanista_s6_gate_devotion

label lanista_s6_gate_devotion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    narrator "The new order is not made by a contract or a coin; it is made by this, and you both know it."
    narrator "The yard is shut, the city is dark, and the Lanista has crossed the distance again."
    narrator "Not summoned, not owed, the way [_they] will come a thousand evenings hence. But tonight is the one that sets the shape of all of them."
    narrator "Tonight you stop testing the thing and simply begin to live inside it."
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "I kept waiting for the catch in it. Eleven seasons taught me everything good arrives with a hook set in the soft of it. And here you are, hookless, season on season, and I've finally stopped reaching for the line. There isn't one."
    lanista_npc "You're just mine, and I'm yours, and the gate swings both ways and neither of us is leaving through it."
    narrator "[_They] crosses to you without an ounce of the fighter's economy left in the step — not the measured advance of the bowl, not the careful approach of a body braced for the next blow."
    narrator "[_They] comes the way you come home. The scarred hands that have only ever known the grip of a weapon find your face first, and hold it, and the holding is its own slow language."
    $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You undress [_them] the way you have learned to — slow, sure, the worn leather and linen going one fastening at a time, and [_they] lets you, watches you."
    narrator "The hard face open in the lamplight in a way the bowl would never have permitted. There is no grief in it tonight and no debt."
    narrator "Only the plain, astonishing ease of being wanted by someone who will still be here in the morning, and the morning after, and every one the map still offers."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_vulnerable.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Bared, [_they] does not stand to be assessed and does not kneel to be kept."
    narrator "[_They] simply gathers you in, the warm scarred bulk of [_them] against you."
    narrator "And the breath that goes out of [_them] is not the broken sound of a guard dropping — that was a season ago."
    narrator "This is the easier sound that comes after: the sound of a body that has learned it is safe, and has stopped, at last, expecting to be proven wrong."
    menu:
        "\"Say it's forever. I want the word, not the arrangement — the one no debt could ever sign.\"":
            $ lanista_devotion += 4
            $ lanista_affection += 3
            narrator "You ask for the one vow a transaction can't contain, and you watch [_them] give it without weighing it."
            narrator "The merchant in [_them] silent for once, the fighter's caution wholly set down. [_They] says it against your mouth, and means it past the reach of any ledger."
            lanista_npc "Forever. There — I've said it, and the sky didn't ask my collateral. ...You're the only thing I've ever pledged the whole of myself to and felt richer for the pledging. Forever. Hold me to it. I'll not need the holding."
        "\"No words. Just stay. Let me show you what the rest of it looks like.\"":
            $ lanista_affection += 4
            $ lanista_devotion += 2
            narrator "You don't ask [_them] for a vow; you give [_them] the thing the vow only points at."
            narrator "Your hands, your warmth, the whole of an evening with nothing owed in either direction. [_They] takes it the way the parched take water, and asks for nothing beyond this, and this."
            narrator "And this."
            lanista_npc "No words, then. ...Good. I've spent enough of them defending a thing that needs no defense. Show me. I'm done talking my way out of being happy."
    $ _scene = "s6_gate"
    $ _route = "devotion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "There's no grief in him tonight and no debt — only knowing, the deep ease of a body that has learned yours by heart and means to learn it again anyway."
        narrator "He lies back on the pillow and opens for you without being asked, arms up and easy behind his head, that whole scarred bulk offered plain in the lamplight."
        narrator "And when you take him it's slow and certain and unhurried, his eyes never leaving your face. The low sound he spends is not the broken thing of that first night but its opposite."
        narrator "A man wholly at home in being loved, and unafraid, for once, of how much he wants it to last."
    elif lanista_gender == "male":
        narrator "He comes over you with a tenderness all that iron never managed to kill, only bury. When he moves it is deep and slow and sure, and there's nothing held in reserve."
        narrator "No guard, no ledger, no part of him kept back against some coming loss. He says your title once, low, like the answer to a question he'd long since stopped asking."
        narrator "And loves you the way a man loves the one good thing he never thought the world would let him keep."
    elif _pt == "lord":
        narrator "She comes to you not by surrender now but by trust — the proud strength gone willing and warm because it has chosen to, season on season, and chooses it again tonight."
        narrator "She mounts you without a word spent on it, sits up tall, carries her own weight the way she carries everything."
        narrator "And you lift your palms clear in the moonlight and let her run the whole of it at whatever pace pleases her. The sound she gives has no grief left in it at all."
        narrator "And when you look up, the Master of the Sands is grinning down at you — openly, teeth and all — like a woman who has finally stopped counting the cost of being happy."
    else:
        narrator "She braces above you and lets you have her from underneath — the short dark hair falling forward around her face, that whole warm weight coming down to meet you by inches."
        narrator "Nothing careful left in any of it and nothing owed. This is the plain generosity of a body that has stopped waiting for the floor to give way."
        narrator "She stays close enough that you feel her heart going hard against your own, and lets you feel it, and holds there in the cool of the moonlight, and would not have it any other way."
        narrator "Whatever she once kept from the world, she has visibly stopped keeping back from you."
    narrator "After, the two of you lie tangled in the warm dark, and there's none of the old vigilance in the way [_they] holds you."
    narrator "No fighter guarding bled-for ground, only a body settled where it means to stay. Somewhere in the city the Arena sleeps under its own name."
    narrator "Here, the new order is just two people and the quiet, and it is the most ordinary miracle either of you has ever been handed."
    lanista_npc "This is the order I'll keep, [_ttl] — not the one on the rolls, this one. Yours, freely, and glad of it, every season the gods are fool enough to grant us. I spent eleven seasons certain I'd die owing somebody."
    lanista_npc "Turns out the only debt I'll carry out the gate is the one no one ever regretted — what I owe you for this. Stay. I sleep, with you here. I told you that once. It's only gotten truer."
    jump lanista_s6_gate_end

label lanista_s6_gate_dominion:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _theirs = lanista_pronoun("poss_pron")
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    narrator "The new order has a night that seals it, and this is the night. The Arena runs under your name, the Lanista keeps it under your hand."
    narrator "And the one bill that was never written down comes due not once but as a standing account — payable, from tonight, whenever you choose to call it."
    narrator "[_They] has come to your chambers to make the first payment of the rest of [_their] life."
    narrator "And [_they] has dressed for it, and [_they] has left nothing of the pride at the door but the choice to be elsewhere."
    $ _bust = "images/lanista/lanista_{}_angry.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "So this is the shape of it, going forward. Not a debt to be cleared but a debt that renews with the dawn — owed fresh each day, paid fresh each night."
    lanista_npc "...I've run the sum a hundred times and it comes out the same every count."
    lanista_npc "I'm yours to call. The only figure left to settle is the manner, and I'll fight you for that one to the last copper. Let me keep my feet, and I'll pay you anything."
    narrator "[_They] crosses to you with the champion's bearing fully intact — chin level, shoulders square, the measured advance of a fighter who has lost the war."
    narrator "[_They] means to lose none of that bearing. This is the whole negotiation now; you own the rest."
    narrator "The manner of the paying is the one fortress [_they] still garrisons."
    narrator "And [_they] holds it the way [_they] once held the bowl: unbeaten in the only way that was ever [_theirs] to keep."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You strip the worn leather from [_them] and [_they] lets you — every fastening a position ceded on terms, the cold dignity never once leaving the hard face."
    narrator "The body answers your hands well before the pride will license it, and [_they] neither hides the fact nor confesses it."
    narrator "This is the standing account: you take, [_they] pays, and the bearing holds through the whole transaction."
    narrator "Without that bearing, [_they] has nothing left at all."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Stripped to whatever you leave [_them] — linen, or nothing at all — [_they] holds still like a fighter at the center of the bowl while the whole house watches."
    narrator "Want comes off [_them] in waves [_they] will not name."
    narrator "The composure a last stance held against everything the body has already conceded. [_They] will pay this account every night the gods grant."
    narrator "[_They] will not, to the last breath, be caught wanting to."
    narrator "Then you take the studded leather out — plain, dark, a workmanlike thing with no ceremony anywhere in it — and tonight it is your hands that buckle it on and not [_theirs]."
    narrator "That is the whole of the difference, and [_they] reads it at once."
    narrator "[_they] looks at it a long moment, and then lifts [_their] chin for you without being asked."
    narrator "The buckle goes home. [_They] does not touch it afterwards, does not test it, does not so much as swallow against it."
    narrator "It is simply on, the way the arrangement is simply on, and it will be worn indoors and never once past that door."
    menu:
        "\"This is the standing order now. Each night the account renews — and each night you may keep your pride. That clause does not expire.\"":
            $ lanista_dominion += 4
            $ lanista_affection += 2
            narrator "You make the cruelty and the mercy a single permanent law — the owning total, the dignity guaranteed in the same breath."
            narrator "And you watch the proud jaw take the sentence and refuse, to the end, to soften at the one kindness folded inside it."
            lanista_npc "Renewing nightly. The pride exempt in perpetuity. ...You'd bind me forever and write my one freedom into the same contract. A thorough collector and a stranger merciful one, as I've said before. Have your standing order."
            lanista_npc "I'll pay it on my feet every night you call, and we'll both go on naming that the bargain."
        "\"Your terms for the manner, mine for the rest — for good, this time. Settle into it, and we'll both keep what matters.\"":
            $ lanista_affection += 3
            $ lanista_dominion += 2
            narrator "You make the season's unspoken truce permanent in two lines, and something behind the cold composure eases at the permanence of it."
            narrator "A fighter knows to the copper the worth of a treaty that does not have to be re-won each dawn."
            lanista_npc "Permanent, then. My manner, your rest. ...You'd let me keep my bearing not for a night but for the whole of what's left. The one creditor who'd sooner a debtor stand than crawl. I stopped trying to be free of you seasons ago."
            lanista_npc "Settle it like this and I'll stop wishing it, besides."
    $ _scene = "s6_gate"
    $ _route = "dominion"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "There is no bout left in it. He comes to your hand the way the yard comes to his — drilled, ordered, sure of its marks — and the long war between his face and his body has been decommissioned."
        narrator "Both of them serve now. He lowers himself to your lap without waiting to be placed there and works that strapped mouth down over you, the studded leather creaking once as he settles to it."
        narrator "He keeps it the way he keeps the day's card: known, held, executed to the second. The surrender is not torn from him anymore. It is scheduled."
        narrator "And somewhere inside that perfect discipline — the breath spent on your count, the strength spent where you point it — is a fighter who sleeps sounder under standing orders than he ever did free."
    elif lanista_gender == "male":
        narrator "Nothing in him resists, because nothing in him remembers how the resisting went. The composure is no longer a wall; it is a uniform, worn because you permit it."
        narrator "He goes down between your thighs at a look — no word required, none given — and pays the account with his mouth, keeping your time the way he once kept the turning of the glass."
        narrator "Habitual, exact, incapable of doing the thing badly. He spends his breath when you call for it and banks it when you don't, and the hard eyes never leave yours over the collar."
        narrator "It is absolute, and it is calm, and the calm is the remarkable part: the account has stood open so long that paying it is simply what this body is for."
    elif _pt == "lord":
        narrator "She no longer chooses the ground; the ground was ceded seasons ago, and the flag over it has long since stopped meaning anything but you."
        narrator "She comes down over your lap with her back arched and her hips still high — the stance of a fighter who has never in her life knelt badly."
        narrator "And takes you in her mouth on your schedule, the collar sitting plain above the linen you left her. What she renders arrives complete, without comment, already smoothed over for the next night."
        narrator "And the stillness of her face is not defiance now, nor even pride. It is peace, of a strange kind."
        narrator "The settled quiet of a champion who knows her marks, holds them nightly, and has stopped imagining the bout ending any other way."
    else:
        narrator "There is nothing left to break, and neither of you pretends otherwise. She settles between your thighs and serves you with the deep unhurried thoroughness of ritual."
        narrator "The same rite each night, because you set it, and order is the one language her body has ever wholly trusted."
        narrator "She works you apart on your count, silently, completely, and reassembles herself without being told, the collar dark under her jaw the whole while. The silence is not her last possession anymore."
        narrator "It is her offering, laid down nightly on the altar of the arrangement — and the arrangement is the whole of the world now, and she keeps it beautifully."
    narrator "After, [_they] lies back in the dark and lets the composure rebuild itself piece by deliberate piece."
    narrator "Slower than [_they] would wish, and you both know exactly why. The collar stays on."
    narrator "[_They] has not been told to take it off, and [_they] will not presume. The account is open now, and will be open every dawn hereafter. The dignity is kept."
    narrator "Nothing else in the bowl, or out of it, belongs to [_them] anymore."
    narrator "And [_they] long ago stopped pretending otherwise."
    lanista_npc "There's your standing order opened, [_ttl] — and you'll mark, as ever, that I paid it standing."
    lanista_npc "That's the last of me that was ever mine, and you've let me keep it, night on night, when a lesser hand would've taken even that for the pleasure of the taking. I'll not call this love. I gave up the right to such soft words."
    lanista_npc "But I'll call it the best terms a kept thing was ever offered, and I'll meet them, copper for copper, till the gods close the account themselves."
    jump lanista_s6_gate_end

label lanista_s6_gate_mixed:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _Their = _their.capitalize()
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    narrator "The new order has a night that seals it, and this is the night — and like everything else between you now, it refuses to be only one thing."
    narrator "Even the room refuses: the Lanista has come to the roofed gallery off your chambers, where the shutters are folded all the way back and the night comes in whole under a moon the size of a shield."
    narrator "Neither properly indoors nor properly out. [_They] has come half as a lover keeping a tryst and half as a kept thing keeping an account."
    narrator "The truth that has stopped troubling [_them] is that [_they] cannot tell you, hand on heart, where the one leaves off and the other starts."
    narrator "Both brought [_them] across the city tonight. Both will keep bringing [_them]."
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    lanista_npc "Don't ask me to pick a lane at the door. I've tried — gods know I've tried to sort the loving from the owing and lay them in separate ledgers, and they will not stay sorted."
    lanista_npc "I love you and I'm kept by you and tonight both halves want the same thing of you. ...I've stopped calling that a wound. It's only the shape of me now. Take the whole of it or none."
    narrator "[_They] crosses to you and the step itself can't decide what it is — half the easy homecoming of a body that wants to be here, half the measured advance of one that has been called."
    narrator "The scarred hands find your face the way a lover's would, and then still, for a breath, the way a fighter stills before the bout."
    narrator "Both true. [_They] has stopped trying to make them lie down together."
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "You get [_them] halfway out of the red and no further, and the letting is its own divided thing."
    narrator "The open heat of a body that wants this, threaded through with the practiced yielding of one that has learned to be taken well."
    narrator "The hard face in the moonlight holds passion and performance in the same expression. You can no longer fully part the gift from the service."
    narrator "Neither, anymore, can [_they]. That is the bittersweet of it."
    $ _bust = "images/lanista/lanista_{}_undress.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "Half-undressed, [_they] neither simply gathers you in nor simply stands to be kept."
    narrator "The red is still half on [_them] and whatever fastenings there were never quite came undone — neither of you thought to finish the job, and neither of you minds."
    narrator "It seems fitting that even the clothes should end up unable to decide. [_They] does both things by turns and in the same breath, a body loving you and serving you at once."
    narrator "At last, [_they] is at peace with being unable to choose. The want and the performance are both real."
    narrator "Tonight, for once, [_they] lets you see both without flinching from either."
    menu:
        "\"I know which half I love. Whatever else this is, the loving is the true part — let that be the half that leads.\"":
            $ lanista_devotion += 3
            $ lanista_affection += 3
            narrator "You reach past the performance for the part of [_them] that crossed the city because it wanted to, and you name that the truer half."
            narrator "And you watch the relief and the grief arrive in [_them] together — grief that you had to choose, relief that you chose the lover."
            lanista_npc "The loving leads. ...You'd reach through all the rest and pull that one to the front. It is the true part — I'll not pretend the other isn't real, but if you're asking which I'd haul from a fire, it was never the ledger. Let it lead, then."
            lanista_npc "The rest of me will follow it across any city you like."
        "\"Both halves, then. I'll keep the one and love the other — and I'll never ask you to choose between them.\"":
            $ lanista_dominion += 3
            $ lanista_affection += 3
            narrator "You don't make [_them] sever the thing in two; you take the whole divided truth of it as offered, the loving and the owing both, and you promise never to demand the impossible sorting."
            narrator "The proud frame eases at that the way it never eased at any single answer."
            narrator "You've let [_them] be more than one thing, and that, it turns out, is the mercy [_they] needed most."
            lanista_npc "Both, and no choosing. ...That's the one offer I never let myself hope for — that I could be kept and beloved and not made to murder half of myself to square it. You'll take me whole and crooked."
            lanista_npc "I'll come to you both ways till the gods run out of evenings, and call myself, against every odd, a fortunate creature."
    $ _scene = "s6_gate"
    $ _route = "mixed"
    python:
        _g = getattr(store, "lanista_gender", "male") or "male"
        _t = (getattr(store, "player_title", "") or "").strip().lower()
        _t = "lady" if _t == "lady" else "lord"
        _candidates = [
            "images/lanista/cg_{}_{}_{}_{}.png".format(_scene, _route, _g, _t),
        ]
        _cg = next((c for c in _candidates if renpy.loadable(c)), None)
    if _cg:
        window hide
        scene expression _cg at lanista_cg_fit
        pause
        window show
    # Normalise exactly as the CG suffix does (_t below): anything that isn't
    # "lady" resolves to "lord". player_title defaults to "" and main_flow clears
    # it, so without this the prose took the female-player branch while the CG
    # loaded the _lord art.
    $ _pt = "lady" if (getattr(store, "player_title", "") or "").strip().lower() == "lady" else "lord"
    if lanista_gender == "male" and _pt == "lord":
        narrator "He braces over you with the red still hanging open off his shoulders, swinging between you, and you feel the two of him in the same motion."
        narrator "The man who wants this and the kept thing who has come to give it, neither winning, both true."
        narrator "When he sinks into you it's passionate and practiced at once, the homecoming and the service threaded so close you stop trying to part them, and the low sound he spends carries both."
        narrator "A man loving you with his whole divided heart, and a creature paying an account he's stopped resenting, and unable, beautifully, to tell you which is which."
    elif lanista_gender == "male":
        narrator "He gathers you in with a passion that is wholly real and a care that is partly performance, and the bittersweet of it is that you can no longer feel the seam between them."
        narrator "When he settles over you and moves, deep and giving, half of him is loving the one good thing he kept and half is serving the one who keeps him, and he has made his peace with being both at once."
        narrator "He murmurs your title like an endearment and like an answer to a call, in the same breath, and means it entirely, both ways."
    elif _pt == "lord":
        narrator "She comes to you as two women in one body — the lover who chose this and the kept thing who was called to it, and she has stopped grieving that they don't separate cleanly."
        narrator "She settles astride you with the red rucked up over her hips and takes you with a sound half surrender and half homecoming."
        narrator "And then she turns her face away, off into the dark past the arches, and keeps it there. Not shame. Not distance either."
        narrator "Only that meeting your eye while both halves of her answer at once is more weight than she can carry tonight. Her hands stay at her sides."
        narrator "Every sound she gives is doubled, true twice over, and the bittersweet of it is the most honest thing she owns."
    else:
        narrator "She pushes the robe off her shoulders and no further — the belt still fast at her waist, the skirt of it spread across your thighs."
        narrator "And takes you astride under a moon the size of a shield, and the body above you is loving you and serving you in the same motion, the same breath, no longer at war over which it's allowed to be."
        narrator "Her brows draw together and her mouth comes open on something that is not quite pleasure and not quite grief, and she doesn't hide it from you, and that is the gift."
        narrator "The woman who could not for a season tell the gift from the transaction has stopped needing to."
        narrator "She gives you both, freely and as owed at once, and the two truths braided together are sweeter and sadder than either alone would ever have been."
    narrator "After, the two of you lie tangled in the lamplight, and even now the holding can't decide what it is."
    narrator "The loose ease of a lover, threaded through with the faint readiness of a body that knows it is kept. Both true."
    narrator "Somewhere the Arena sleeps under your name, and here the new order is two people and a quiet that has made room, at last, for more than one truth at a time."
    lanista_npc "This is the order I'll keep, [_ttl] — the crooked one, the one that won't add up. I love you and I'm yours to call and I've quit demanding the two of them reconcile. Most folk get one true thing if they're lucky."
    lanista_npc "I've two that don't match, and I'd not trade the pair of them for a single clean answer. Stay. Both halves of me sleep better with you here — and that, at least, the both of them agree on."
    jump lanista_s6_gate_end

label lanista_s6_gate_end:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    lanista_npc "One thing more, [_ttl], before you go. This isn't the last word between us — there's a settling still owed, the kind that fixes a thing in place instead of leaving it to the heat of a night like this."
    lanista_npc "Come back when the day's turned. What's left to settle deserves its own hour."
    $ lanista_s6_gate_fired = True
    $ lanista_night_visit_total_days = None
    # Preserve the route locked at scene entry; fall back only if somehow unset.
    $ lanista_ending_route = lanista_ending_route or lanista_determine_ending()
    $ lanista_recalculate_stage()
    jump lanista_gate_exit_to_map

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ENDING RESOLUTION                                                          ║
# ║                                                                            ║
# ║  Called on next visit after the S6 gate fires (lanista_visit_menu).         ║
# ║  Final state: NPC partner (devotion), full worker (dominion),               ║
# ║  or part-time worker (mixed). Mirrors yvara_ending_resolution.              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

label lanista_ending_resolution:
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    $ _route = getattr(store, "lanista_ending_route", "") or lanista_determine_ending()
    $ store.lanista_ending_route = _route
    if _route == "dominion":
        jump lanista_ending_dominion
    elif _route == "mixed":
        jump lanista_ending_mixed
    else:
        jump lanista_ending_devotion

# ── Devotion Ending: free partner, keeps the Arena, NPC (no roster add) ──────
label lanista_ending_devotion:
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "The Arena keeps the Lanista's name on its gate, and that is how it stays."
    lanista_npc "I'll not be kept, [_ttl], and you'll not ask me to be. But I'll come when the gate swings — and it swings your way more nights than not."
    narrator "[_They] holds the whole of [_their] own keeping and offers you the better part of it freely. No debt. No collar."
    narrator "Only the choosing, made fresh each evening [_they] crosses the city to find you."
    narrator "The Master of the Sands runs the sands. And loves you in the one column no ledger ever reached."

    $ lanista_ending_devotion = True
    $ lanista_ending_done = True
    python:
        if not hasattr(store, "event_flags") or not hasattr(store.event_flags, "__setitem__"):
            store.event_flags = {}
        store.event_flags["lanista_ending_devotion"] = True

    narrator "{b}Ending: Master of the Sands — Your Partner{/b}."
    narrator "The Lanista remains free and runs the Arena independently. [_They] is your partner, not your worker."
    narrator "And will turn up across your buildings when it suits [_them], which is often."
    jump lanista_visit_menu

# ── Dominion Ending: owned worker, replaced at the Arena, Broken Champion ────
label lanista_ending_dominion:
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _bust = "images/lanista/lanista_{}_yielding.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "The Arena answers to your name now, and the Lanista answers to your hand. The office will pass to another keeper; [_they] reports to your house alone, on whatever schedule you set."
    lanista_npc "You own the sand and you own me, [_ttl]. Put another keeper in the chair. Tell me where to stand, and I will stand there well."
    narrator "The champion who answered to no one now answers to you. The bearing is intact. The freedom is not."

    python:
        # Mirror yvara_ending_dominion's worker-add mechanism exactly.
        # LA BIBLIA §1: duck-type (hasattr 'get'/'__setitem__'); never isinstance(x, dict/list)
        # in story-label python blocks — json.loads values fail against Ren'Py Revertable types.
        # Resolve the chosen gender first: each gender ships its own sheet so it
        # gets its own folder (and therefore its own template_id and image set).
        _gen = getattr(store, "lanista_gender", "male") or "male"
        _gen = "female" if _gen == "female" else "male"
        _lw = None
        try:
            # I/O is function-local; binding a file here would poison later saves.
            _lw = _load_worker_json_entry("data/workers/lanista_%s.json" % _gen)
        except Exception as _e:
            renpy.log("Lanista dominion: failed to load lanista_%s.json - %s" % (_gen, str(_e)))

        # Inline fallback if JSON load failed entirely (file missing/corrupt).
        if not (_lw is not None and hasattr(_lw, "get") and hasattr(_lw, "__setitem__")):
            renpy.log("Lanista dominion: using inline fallback dict")
            _lw = {
                "name": "Varra" if _gen == "female" else "Varro",
                "folder": "varra" if _gen == "female" else "varro",
                "cost": 0,
                "nsfw": True,
                "unique": True,
                "recruitment_locked": True,
                "encounter_only": False,
                "monster": False,
                "procedural": False,
                "skills": {
                    "Sex": 60, "Anal": 38, "BDSM": 48, "Hand": 46, "Oral": 46,
                    "Homo": 40, "Special": 35, "Group": 42, "Extreme": 40,
                    "Striptease": 62, "Combat": 68, "Clever": 38, "Charm": 50,
                    "Service": 30, "Agility": 55, "Craft": 25
                },
                "names_list": "western_female" if _gen == "female" else "western_male",
                "traits": ["Human", "Strong", "Tall", "Tough", "Great Figure", "Cool Scars"],
                "description": "The Master of the Sands. A scarred Arena champion who runs the fighting pits by day and answers to your house by arrangement.",
                "gender": _gen,
                "comfort_desired": 2
            }

        # Belt and braces: the sheet already carries these, but pin them so a
        # hand-edited or stale JSON can never hand the roster the wrong gender.
        # The arc keeps calling them "The Lanista" in dialogue; the roster gets
        # the personal name. Only one gender ever exists in a given playthrough,
        # so the two sheets can carry different names — which is also what keeps
        # the worker loader (it dedupes by name) from dropping one of them.
        _lw["name"] = "Varra" if _gen == "female" else "Varro"
        _lw["gender"] = _gen
        _lw["names_list"] = "western_female" if _gen == "female" else "western_male"
        _lw["description"] = "The former Master of the Sands. A scarred Arena champion removed from the fighting pits and taken into your establishment as an owned worker."
        # Compare against the resolved sheet, never a hardcoded string, so the
        # guard cannot drift out of sync with the JSON again.
        if not any(w.get("name") == _lw["name"] for w in store.workers):
            try:
                ensure_worker_defaults(_lw)
                # Mirror Yvara's call, but skip random-trait backfill for this UNIQUE
                # worker (worker_defaults §"Unique workers should not get random traits").
                # Yvara's call is a no-op only because she ships 5 traits; the Lanista ships 1.
                _emt = getattr(store, "_ensure_worker_min_traits", None)
                if callable(_emt) and not _lw.get("unique", False):
                    _emt(_lw)
                _stid = getattr(store, "_stamp_template_id_from_json", None)
                if callable(_stid):
                    _stid(_lw)
                # Finalize like a normal recruit (recruit_worker in script.rpy):
                # a worker appended straight to the roster otherwise misses the
                # fields the recruit flow sets, and reads as "not recruited".
                _lw["is_servant"] = False
                _lw["source"] = "recruited"
                _lw.setdefault("assigned_building", "Unassigned")
                store.workers.append(_lw)
                renpy.store.workers = store.workers
                renpy.notify("%s has joined your roster." % _lw["name"])
                # Seed the relationship so the recruited Lanista already "knows"
                # you, scaled to the route. Set AFTER ensure_worker_defaults so the
                # defaults (rebelliousness 50 / romance 0 / relationship 10+comfort)
                # do not overwrite these. Dominion: owned and obedient — high
                # relationship, low romance, near-zero rebelliousness.
                _lw["relationship"] = 100
                _lw["romance"] = 50
                _lw["rebelliousness"] = 10
                add_trait_with_duration(_lw, "Broken Champion", 0)
                _corr_tier = lanista_corruption_tier()
                for _ct in _corr_tier[2]:
                    add_trait_with_duration(_lw, _ct, 0)
            except Exception as _e:
                renpy.log("Lanista dominion: append failed - %s" % str(_e))

        store.lanista_ending_dominion = True
        store.lanista_is_worker = True
        store.lanista_ending_done = True
        store.arena_successor_met = False
        if not hasattr(store, "event_flags") or not hasattr(store.event_flags, "__setitem__"):
            store.event_flags = {}
        store.event_flags["lanista_ending_dominion"] = True

    narrator "{b}Ending: Broken Champion{/b}."
    narrator "The Lanista is now a worker at your establishment. Assign [_them] where you wish."
    narrator "A successor takes the Arena office. [lanista_name] belongs to your roster now, not the sands."
    jump arena_successor_visit

# ── Mixed Ending: part-time worker, Arena keeps some days, Reluctant Gladiator
label lanista_ending_mixed:
    $ _g = getattr(store, "lanista_gender", "male") or "male"
    $ _they = lanista_pronoun("subj")
    $ _them = lanista_pronoun("obj")
    $ _their = lanista_pronoun("poss")
    $ _They = _they.capitalize()
    $ _bust = "images/lanista/lanista_{}_warm.png".format(_g)
    if not renpy.loadable(_bust):
        $ _bust = "images/lanista/lanista_{}_neutral.png".format(_g)
    if renpy.loadable(_bust):
        show expression _bust as lanista_bust at lanista_bust_right
    narrator "The Arena stays the Lanista's by day. The evenings, more often than not, are yours."
    lanista_npc "I keep the sands and you get the rest, [_ttl] — the nights I can spare and the parts of me the pits don't claim. It's a crooked arrangement. I've made peace with crooked."
    narrator "Half master, half kept thing, and unwilling to sever the two. [_They] works your halls when the Arena lets [_them] go."
    narrator "And goes back to the pits when it calls [_them] home."

    python:
        # Mirror yvara_ending_mixed's worker-add mechanism exactly (see dominion note above).
        # Resolve the chosen gender first: each gender ships its own sheet so it
        # gets its own folder (and therefore its own template_id and image set).
        _gen = getattr(store, "lanista_gender", "male") or "male"
        _gen = "female" if _gen == "female" else "male"
        _lw = None
        try:
            # I/O is function-local; binding a file here would poison later saves.
            _lw = _load_worker_json_entry("data/workers/lanista_%s.json" % _gen)
        except Exception as _e:
            renpy.log("Lanista mixed: failed to load lanista_%s.json - %s" % (_gen, str(_e)))

        if not (_lw is not None and hasattr(_lw, "get") and hasattr(_lw, "__setitem__")):
            renpy.log("Lanista mixed: using inline fallback dict")
            _lw = {
                "name": "Varra" if _gen == "female" else "Varro",
                "folder": "varra" if _gen == "female" else "varro",
                "cost": 0,
                "nsfw": True,
                "unique": True,
                "recruitment_locked": True,
                "encounter_only": False,
                "monster": False,
                "procedural": False,
                "skills": {
                    "Sex": 60, "Anal": 38, "BDSM": 48, "Hand": 46, "Oral": 46,
                    "Homo": 40, "Special": 35, "Group": 42, "Extreme": 40,
                    "Striptease": 62, "Combat": 68, "Clever": 38, "Charm": 50,
                    "Service": 30, "Agility": 55, "Craft": 25
                },
                "names_list": "western_female" if _gen == "female" else "western_male",
                "traits": ["Human", "Strong", "Tall", "Tough", "Great Figure", "Cool Scars"],
                "description": "The Master of the Sands. A scarred Arena champion who runs the fighting pits by day and answers to your house by arrangement.",
                "gender": _gen,
                "comfort_desired": 2
            }

        # Belt and braces (see the dominion ending for the rationale).
        # The arc keeps calling them "The Lanista" in dialogue; the roster gets
        # the personal name. Only one gender ever exists in a given playthrough,
        # so the two sheets can carry different names — which is also what keeps
        # the worker loader (it dedupes by name) from dropping one of them.
        _lw["name"] = "Varra" if _gen == "female" else "Varro"
        _lw["gender"] = _gen
        _lw["names_list"] = "western_female" if _gen == "female" else "western_male"
        # Compare against the resolved sheet, never a hardcoded string, so the
        # guard cannot drift out of sync with the JSON again.
        if not any(w.get("name") == _lw["name"] for w in store.workers):
            try:
                ensure_worker_defaults(_lw)
                _emt = getattr(store, "_ensure_worker_min_traits", None)
                if callable(_emt) and not _lw.get("unique", False):
                    _emt(_lw)
                _stid = getattr(store, "_stamp_template_id_from_json", None)
                if callable(_stid):
                    _stid(_lw)
                # Finalize like a normal recruit (recruit_worker in script.rpy):
                # a worker appended straight to the roster otherwise misses the
                # fields the recruit flow sets, and reads as "not recruited".
                _lw["is_servant"] = False
                _lw["source"] = "recruited"
                _lw.setdefault("assigned_building", "Unassigned")
                store.workers.append(_lw)
                renpy.store.workers = store.workers
                renpy.notify("%s has joined your roster." % _lw["name"])
                # Seed the relationship so the recruited Lanista already "knows"
                # you, scaled to the route. Set AFTER ensure_worker_defaults so the
                # defaults (rebelliousness 50 / romance 0 / relationship 10+comfort)
                # do not overwrite these. Mixed: freely chosen partner-of-sorts —
                # high relationship, high romance, low rebelliousness.
                _lw["relationship"] = 100
                _lw["romance"] = 80
                _lw["rebelliousness"] = 20
                add_trait_with_duration(_lw, "Reluctant Gladiator", 0)
                _corr_tier = lanista_corruption_tier()
                for _ct in _corr_tier[2]:
                    add_trait_with_duration(_lw, _ct, 0)
            except Exception as _e:
                renpy.log("Lanista mixed: append failed - %s" % str(_e))

        store.lanista_ending_mixed = True
        store.lanista_is_worker = True
        store.lanista_ending_done = True
        if not hasattr(store, "event_flags") or not hasattr(store.event_flags, "__setitem__"):
            store.event_flags = {}
        store.event_flags["lanista_ending_mixed"] = True

    narrator "{b}Ending: Reluctant Gladiator{/b}."
    narrator "The Lanista works for you of [_their] own choosing, but the Arena still claims [_their] days."
    narrator "Assign [_them] as any worker; on Arena days you will find [_them] at the pits instead."
    jump lanista_visit_menu

################################################################################
### LANISTA — POST-ARC RENEGOTIATION (mixed ending only)
################################################################################
# A daytime conversation, modelled on yvara_post_arc_change_arrangement. Only
# reachable while the arrangement is still the crooked half-and-half of the
# mixed ending. Two of the three exits are irreversible: once Varra/Varro is a
# free partner or a full-time worker, the arrangement is no longer "mixed" and
# this option disappears from the visit menu for good.

label lanista_renegotiate_arrangement:
    call lanista_restore_visit_scene from _lanista_restore_renegotiate
    call lanista_show_emotion("neutral") from _lanista_emotion_renegotiate
    $ _ttl = getattr(store, "player_title", "") or "stranger"
    narrator "[lanista_name] reads the shape of the question before you have finished framing it — the same eye that reads a fighter's guard before the first exchange."
    lanista_npc "You've the look of someone come to redraw the lines, [_ttl]. The arrangement's crooked, I know it. Say which way you'd straighten it."
    menu:
        lanista_npc "Speak plainly. I've made peace with crooked, but I'll not pretend it's the only shape on offer."
        "Leave it as it stands. The crooked arrangement suits us both.":
            call lanista_show_emotion("warm") from _lanista_emotion_renegotiate_keep
            lanista_npc "Then we leave it crooked, and neither of us pretends otherwise. The sands by day, you by the nights I can spare. It holds."
            narrator "[lanista_name] returns to the whetstone, and the matter is set down as gently as it was raised."
            jump lanista_visit_menu
        "Buy back all your days. Run the sands free — and be mine only by choosing.":
            jump lanista_renegotiate_to_devotion
        "Take the rest of your days too. Full-time, in my house.":
            jump lanista_renegotiate_to_dominion_warn

label lanista_renegotiate_to_devotion:
    call lanista_show_emotion("warm") from _lanista_emotion_renegotiate_dev
    lanista_npc "..."
    lanista_npc "You'd give the sands back to me whole. Buy out my days and ask nothing owned in return."
    narrator "You tell [lanista_name] that the arena was never yours to hold in the first place, and that a partner who comes freely is worth more than one who answers a ledger."
    lanista_npc "Then I run my own pits, on my own name, and I cross the city on the nights I choose you. No half about it. No collar either."
    narrator "[lanista_name] buys back the seat at your table with the one currency the arena never minted — the freedom to keep turning up anyway."

    python:
        # Inverse of the ending's worker-add: search by the resolved personal
        # name (duck-typed .get, never isinstance — LA BIBLIA §1) and lift the
        # roster entry back out. Only one gender ever exists per playthrough.
        _target_name = "Varra" if (getattr(store, "lanista_gender", "male") or "male") == "female" else "Varro"
        _vw = next((w for w in store.workers if w.get("name") == _target_name), None)
        if _vw is not None:
            try:
                remove_worker_from_building(_vw)
            except Exception:
                pass
        store.workers = [w for w in store.workers if w.get("name") != _target_name]
        renpy.store.workers = store.workers
        store.lanista_is_worker = False
        store.lanista_ending_mixed = False
        store.lanista_ending_devotion = True
        store.lanista_ending_route = "devotion"
        store.lanista_arrangement_change_count = int(getattr(store, "lanista_arrangement_change_count", 0) or 0) + 1
        if not hasattr(store, "event_flags") or not hasattr(store.event_flags, "__setitem__"):
            store.event_flags = {}
        store.event_flags["lanista_ending_devotion"] = True
        if "lanista_ending_mixed" in store.event_flags:
            del store.event_flags["lanista_ending_mixed"]

    narrator "{b}The arrangement has changed: Your Partner{/b}."
    narrator "[lanista_name] no longer works your halls. [lanista_name] runs the Arena freely and comes to you by choosing — and will set aside your share of the gate each week."
    jump lanista_visit_menu

label lanista_renegotiate_to_dominion_warn:
    call lanista_show_emotion("neutral") from _lanista_emotion_renegotiate_dom_warn
    $ _former_name = "Varra" if lanista_gender == "female" else "Varro"
    lanista_npc "..."
    lanista_npc "All of them. Not the spare nights — the days too, the ones the sand still owns."
    narrator "[lanista_name] is quiet a moment, weighing what the words actually cost."
    lanista_npc "Understand what you're asking, [_ttl]. If I give you the days, I give up the chair. Someone else keeps the sand for you after tonight — I'll not be the Master any longer, only yours."
    menu:
        lanista_npc "So. Say it knowing that. Do you want the whole of me, and a stranger behind that desk?"
        "Yes. After tonight, let another keep the sand. I want all of you.":
            jump lanista_renegotiate_to_dominion_commit
        "No — not at that price. Leave it as it stands.":
            call lanista_show_emotion("warm") from _lanista_emotion_renegotiate_dom_abort
            lanista_npc "Then the chair stays under me, and you keep the nights I can spare. Wiser, maybe. The sand would miss my hand."
            jump lanista_visit_menu

label lanista_renegotiate_to_dominion_commit:
    call lanista_show_emotion("yielding") from _lanista_emotion_renegotiate_dom
    lanista_npc "Then it's done. Put another keeper in the chair and tell me where to stand. I'll stand there well."
    narrator "[lanista_name] sets the whetstone down for the last time as the arena's master. What answers to you now is the champion, not the office."

    python:
        # Replicate lanista_ending_dominion's FINAL worker-state without replaying
        # its scene: the mixed worker is already on the roster carrying "Reluctant
        # Gladiator"; swap that for "Broken Champion" and the dominion description,
        # exactly as the dominion ending stamps a freshly-added worker.
        _target_name = "Varra" if (getattr(store, "lanista_gender", "male") or "male") == "female" else "Varro"
        _vw = next((w for w in store.workers if w.get("name") == _target_name), None)
        if _vw is not None:
            try:
                _trs = _vw.get("traits", []) or []
                _filtered = []
                for _t in _trs:
                    _tname = _t.get("name") if hasattr(_t, "get") else _t
                    if _tname != "Reluctant Gladiator":
                        _filtered.append(_t)
                _vw["traits"] = _filtered
                add_trait_with_duration(_vw, "Broken Champion", 0)
                _vw["description"] = "The former Master of the Sands. A scarred Arena champion removed from the fighting pits and taken into your establishment as an owned worker."
            except Exception as _e:
                renpy.log("Lanista renegotiate->dominion: trait/description update failed - %s" % str(_e))
        store.lanista_is_worker = True
        store.lanista_ending_mixed = False
        store.lanista_ending_dominion = True
        store.lanista_ending_route = "dominion"
        store.arena_successor_met = False
        store.lanista_arrangement_change_count = int(getattr(store, "lanista_arrangement_change_count", 0) or 0) + 1
        if not hasattr(store, "event_flags") or not hasattr(store.event_flags, "__setitem__"):
            store.event_flags = {}
        store.event_flags["lanista_ending_dominion"] = True
        if "lanista_ending_mixed" in store.event_flags:
            del store.event_flags["lanista_ending_mixed"]

    narrator "{b}The arrangement has changed: Broken Champion{/b}."
    narrator "[lanista_name] belongs to your roster full-time now. A successor takes the Arena office; from tomorrow you will find [lanista_name] where you assign them, not on the sand."
    # This branch carries real weight: it retires the personal visits for good
    # (the next visit routes to arena_successor_visit), so it closes the day.
    jump lanista_gate_exit_to_map

label lanista_check_stage_advance:
    return
