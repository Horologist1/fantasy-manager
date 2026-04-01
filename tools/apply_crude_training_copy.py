# Regenerates ALL training strings in game/data/interactions/interactions_training.json.
# SOURCE OF TRUTH: see docs/writing/training_voice.md  |  Run: python tools/apply_crude_training_copy.py

from __future__ import annotations
import copy, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "game" / "data" / "interactions" / "interactions_training.json"

LF = "{pronoun} didn't get enough from this session—not ready for the floor tonight."

def tx(trained, leave1, leave2, punished, insist, learn_fail=LF):
    return {"trained": trained, "leave_be_first": leave1, "leave_be_second": leave2,
            "punished": punished, "trained_after_insist": insist, "learn_fail": learn_fail}


def _split_training_intro_pages(lines, max_chars=140):
    """One RenPy click per list entry; split long paragraphs at sentence boundaries, then by spaces."""
    if not lines:
        return []
    out = []
    sent_split = re.compile(r"(?<=[.!?])\s+")

    def hard_wrap(text):
        chunks = []
        rest = text.strip()
        while rest:
            if len(rest) <= max_chars:
                chunks.append(rest)
                break
            cut = rest.rfind(" ", 0, max_chars)
            if cut < 40:
                cut = max_chars
            chunks.append(rest[:cut].strip())
            rest = rest[cut:].strip()
        return [c for c in chunks if c]

    def pack_sentences(sentences):
        cur = ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            pieces = hard_wrap(sent) if len(sent) > max_chars else [sent]
            for piece in pieces:
                cand = (cur + " " + piece).strip() if cur else piece
                if len(cand) <= max_chars:
                    cur = cand
                else:
                    if cur:
                        out.append(cur)
                    cur = piece
        if cur:
            out.append(cur)

    for raw in lines:
        if raw is None:
            continue
        s = str(raw).strip()
        if not s:
            continue
        if len(s) <= max_chars:
            out.append(s)
            continue
        sents = [x.strip() for x in sent_split.split(s) if x.strip()]
        if not sents:
            out.extend(hard_wrap(s))
        elif len(sents) == 1:
            pack_sentences(sents)
        else:
            pack_sentences(sents)
    return out


def intro(first, second, fail):
    return {
        "first_refusal": _split_training_intro_pages(first),
        "second_refusal": _split_training_intro_pages(second),
        "learn_fail": _split_training_intro_pages(fail),
    }


# ---------------------------------------------------------------------------
# Descriptions
# ---------------------------------------------------------------------------
HAND_HOMO_FF_DESC = (
    "As manager you drill girl-on-girl hand skills for paid bookings: clit, lips, wetness, how hard to press, "
    "when to slow so a client doesn't go numb. You use your own body as the training piece—her fingers on you, "
    "then the rhythm she'll repeat on the next woman who pays for F+F. Manager-led {skill} training—hands-on, timed.")
HAND_HOMO_MM_DESC = (
    "As manager you drill handjobs for male clients: grip, stroke, spit or oil, keeping a john hard without rushing. "
    "Your cock is the practice dummy—reps until his hands earn what men pay for in the next room. "
    "Manager-led {skill} training—hands-on, timed.")
HAND_HET_LORD_DESC = (
    "You train her hands on your cock and balls—stroke, squeeze, pace—for the clients who buy hand relief. "
    "She stops treating your dick like costume jewelry and finishes the job like it hits the ledger. "
    "Manager-led {skill} training—hands-on, timed.")
HAND_HET_LADY_DESC = (
    "You train his hands on your tits, thighs, clit—pressure, circles, when to stop teasing and make you come—"
    "so male workers on the floor can get female clients off without fumbling like amateurs. "
    "Manager-led {skill} training—hands-on, timed.")
ORAL_HOMO_FF_DESC = (
    "You train cunnilingus for F+F bookings: tongue on clit, suction, breath, jaw—how long to stay when a client tries "
    "to crush her face from shame or want. Your pussy is the lesson bench until her mouth earns repeat customers. "
    "Manager-led {skill} training—hands-on, timed.")
ORAL_HOMO_MM_DESC = (
    "You train cock-sucking for male bookings: lips sealed, teeth gone, throat depth you set, hand on base, swallow or spit "
    "per establishment rule. Your dick is the training rod until his throat makes johns pay for round two. "
    "Manager-led {skill} training—hands-on, timed.")
ORAL_HET_F_DESC = (
    "You train her mouth on your cock—suck, tongue under the head, depth, gag control—for blowjobs clients actually rebuy. "
    "When she makes you come on command, she can sell the same finish upstairs. Manager-led {skill} training—hands-on, timed.")
ORAL_HET_M_DESC = (
    "You train his mouth on your pussy—clit, lips, tongue inside if you order—so men on staff can eat female clients out "
    "without humiliating the establishment. Manager-led {skill} training—hands-on, timed.")
HOMO_FF_DESC = (
    "You run this as manager-on-worker training for F+F sales: grinding clits together, thighs locked, mouths on tits and pussy, "
    "fingers where clients will pay to be touched. No toys required—this slot is trib, oral, and hand work until her body "
    "reads professional, not performative, in a paid hour. Manager-led {skill} training—hands-on, timed.")
HOMO_MM_DESC = (
    "You train him for M+M anal bookings: lube, stretch, breathing, taking cock deep without bracing like it's a joke. "
    "You're on top—you fuck his ass in this room so the next paying man who buys his hole gets a worker who knows how to open, "
    "take rhythm, and finish the session like a professional. Manager-led {skill} training—hands-on, timed.")
BDSM_DESC = (
    "You teach kink the way it's sold: hard limits, safeword, aftercare—then rope, cuffs, crops, clamps, toys, denial—whatever "
    "the premium room books. Pain and arousal stay on leash so paying sadists get a show that doesn't breach establishment rules. "
    "Manager-led {skill} training—hands-on, timed.")
SEX_DESC = (
    "You train penetrative sex the way it's sold: foreplay that gets a cunt wet—mouth, hands, teasing—then vaginal fucking on the clock "
    "(ass only if the menu allows it), depth, angle, hip rhythm, dirty talk that doesn't embarrass the establishment. Pullout or finish inside per rule; "
    "aftercare still counts as labor. Bodies leave ready to repeat the same for paying strangers. "
    "Manager-led {skill} training—hands-on, timed.")
SPEC_DESC = (
    "You train whatever extra the client prepaid—anal prep, toy scenes, roleplay, pain, group rules—step by step with filthy-clear names, "
    "hygiene and limits first. You meet the worker in the training room and run the scene hands-on until they can sell the same booking without improvisation. "
    "Manager-led {skill} training—hands-on, timed.")
STRIP_DESC = (
    "You train stripping as floor work: peel stockings, bra, harness—hips rolling, cock or tits presented—eyes on the paying watcher "
    "who tips for the tease. Shame doesn't get to rush the beat; the clock and the client do. "
    "Manager-led {skill} training—hands-on, timed.")
SVC_DESC = (
    "You train operational service the way it matters: timing, spacing, anticipation—trays, doors, refills before anyone asks. "
    "Whether the floor is a tavern, a kitchen line, or a lord's hall, the drill is the same: fast, invisible, precise. "
    "Manager-led {skill} training—timed reps, no theater.")
AG_DESC = (
    "You drill the body for what the field demands: obstacle sprints, rolls, climbing, silent movement—the kind of agility "
    "that dodges a trap, scales a wall, and gets out of a dungeon alive. Sweat and bruises beat theory. "
    "Manager-led {skill} conditioning—no shortcuts, no excuses.")
CH_DESC = (
    "You train Charm as a working skill: reading a stranger in seconds, warmth that feels real, comebacks that sound lived-in, "
    "names remembered on the second visit. Whether it's a tavern guest or a noble at court, the craft is the same. "
    "Manager-led {skill} study—repetition until the charm stops looking like effort.")


# ---------------------------------------------------------------------------
# Intro sequences
# ---------------------------------------------------------------------------

HAND_HOMO_FF_INTRO = intro(
    [
        "You find {name} and suggest a {skill} session for the F+F rate card—tonight you guide {poss} fingers on your body: "
        "clit, lips, pressure, when to slow before a woman goes numb. You set up the lesson where it starts.",
        "{name} {listen}, cheeks warm—{subj} can't quite look at what {subj}'s touching, won't repeat the words back; "
        "after a quiet moment {subj} explains {subj}'d rather try this another day.",
        "Ease off, or insist once.",
    ],
    [
        "You try again; {name} still won't touch where the work is—{subj} keeps {poss} hands politely distant "
        "even knowing what the booking asks.",
        "{Subj} knows what this is and still won't do it.",
        "Let {obj} go, or make clear the floor doesn't pay for coy.",
    ],
    [
        "You run the drills anyway—pressure maps, circles, timing.",
        "{name} {try}, but {poss} hands stay timid; nothing a client would rebook.",
        "By the end it still feels like {subj} going through the motions—no real heat.",
    ],
)

HAND_HOMO_MM_INTRO = intro(
    [
        "You find {name} and lay out tonight's {skill} drill—{subj} learns what male hands sell for each other: "
        "grip, stroke, pace, reading the edge. You make {obj} start on you before theory can stall anything.",
        "{name} {listen}, jaw tight—{subj} won't commit the grip, stalls instead of starting; "
        "after some silence {subj} says {subj}'d rather come back to this another time.",
        "Let {obj} walk, or insist once.",
    ],
    [
        "You ask again; {name} still won't take the grip the booking asks for—{subj} knows what this is "
        "and keeps {poss} hands idle.",
        "{Subj} understands what you want and refuses it anyway.",
        "End it, or let the silence carry the consequence.",
    ],
    [
        "You run stroking drills anyway—pace, pressure, repetition.",
        "{name} {try}, but {poss} hand stays mechanical; no client would tip for what {subj} did tonight.",
        "By the end nothing earned—no real skill, no confidence to sell.",
    ],
)

HAND_HET_FWORKER_INTRO = intro(
    [
        "You find {name} for tonight's {skill} session and explain the work plainly—{poss} hands on you, "
        "learning stroke, pace, and finish, the same as what clients will pay for upstairs. "
        "You guide {poss} palm to where the lesson begins.",
        "{name} {listen}, hesitant—touching the manager sits wrong and {subj} doesn't hide it well; "
        "after a careful conversation {subj} says {subj}'d prefer to try this another day.",
        "Back off, or insist once.",
    ],
    [
        "You repeat the instruction; {name} still won't stroke like {subj} means it—{subj} knows what "
        "you're asking and keeps pulling back.",
        "{Subj} is refusing the actual work, not a misunderstanding.",
        "Walk away, or let silence say the rest.",
    ],
    [
        "You still make {obj} run the strokes—slow, fast, edge, repeat.",
        "{name} {try}, but {poss} wrist won't commit; you finish unsatisfied.",
        "It ends with no skill a client would tip for.",
    ],
)

HAND_HET_MWORKER_INTRO = intro(
    [
        "You find {name} and set up tonight's {skill} session—{poss} hands on your body, "
        "learning tits, thighs, clit, the pressure and timing that female clients pay for. "
        "You show {obj} the map on yourself and make {subj} start.",
        "{name} {listen}, uneasy—{subj} hovers near but won't press where you ask; "
        "after some hesitation {subj} explains {subj}'d rather come back to this another time.",
        "Give {obj} the pass, or insist once.",
    ],
    [
        "You repeat; {name} still won't put {poss} hands where they need to go—{subj} knows the lesson "
        "and avoids it anyway.",
        "{Subj} is refusing the work, not the words.",
        "Let it go, or freeze {obj} out.",
    ],
    [
        "You still drill contact—circles, pressure, pace.",
        "{name} {try}, but {poss} touch stays hollow; you don't come and {subj} doesn't learn.",
        "It finishes with nothing either of you can use.",
    ],
)

ORAL_INTRO_HOMO_FF = intro(
    [
        "You find {name} for tonight's {skill} session and set the terms plainly—{subj} will go down on you: "
        "tongue, suction, breath, staying until you come or call halt. "
        "You position yourself so there's no ambiguity about where the lesson starts.",
        "{name} {listen}, frozen smile—{subj} won't lower {poss} face, laughs it off; "
        "after a quiet beat {subj} admits {subj}'d really rather try this another day.",
        "Let {obj} go, or insist once.",
    ],
    [
        "You ask again; {name} still won't put {poss} mouth where the booking needs it—{subj} knows "
        "what this is and steps back anyway.",
        "{Subj} knows where {subj}'s supposed to be and refuses to go there.",
        "End it, or punish with silence.",
    ],
    [
        "You run the drills anyway—pace, pressure, breathing.",
        "{name} {try}, but {poss} mouth stays uncertain; no orgasm, no result a client would pay for twice.",
        "By the end it still reads as reluctance, not skill.",
    ],
)

ORAL_INTRO_HOMO_MM = intro(
    [
        "You find {name} and lay out tonight's {skill} session—{subj} will work your cock: lips sealed, "
        "tongue under the head, depth as far as the menu allows. "
        "You unzip the lesson before {subj} can make it hypothetical.",
        "{name} {listen}, nerves showing—{subj} won't seal {poss} lips, won't take depth; "
        "after some hesitation {subj} says {subj}'d rather put this off another day.",
        "Release {obj}, or insist once.",
    ],
    [
        "You ask again; {name} won't commit {poss} mouth—{subj} understands what you want and won't do it.",
        "{Subj} knows what the booking asks and refuses it plainly.",
        "End it, or let the consequence show.",
    ],
    [
        "You run the reps anyway—depth, tongue, breathing.",
        "{name} {try}, but {poss} throat tightens or {subj} rushes; no finish, no skill clients pay for twice.",
        "By the end it's still amateur—bad for the floor.",
    ],
)

ORAL_INTRO_HET_F = intro(
    [
        "You find {name} for tonight's {skill} session and tell {obj} straight—{subj} will work your cock: "
        "lips, tongue, depth, gag control, the same finish men rebuy. "
        "You strip away what's in the way so there's no mistaking where the lesson starts.",
        "{name} {listen}, eyes averted—{subj} hesitates before the reality; "
        "after a conversation {subj} explains {subj} would prefer to try this another day.",
        "Ease off, or insist once.",
    ],
    [
        "You repeat; {name} still won't take {poss} mouth to where the work is—{subj} knows what "
        "you're asking and refuses it.",
        "{Subj} understands exactly what this is and still won't do it.",
        "Walk, or let silence do the work.",
    ],
    [
        "You run the drills anyway—hand-mouth, pace, breathing.",
        "{name} {try}, but {poss} technique stays toothy or shallow; you don't finish.",
        "It ends without either of you getting what the session was for.",
    ],
)

ORAL_INTRO_HET_M = intro(
    [
        "You find {name} and set up tonight's {skill} session—{subj} will go down on you: clit first, "
        "tongue where you steer, staying until you come or call stop. "
        "You get comfortable and make clear there's no theory-only version of this.",
        "{name} {listen}, asking 'are you sure' with {poss} whole body—{subj} won't lick where it matters; "
        "after some back-and-forth {subj} says {subj}'d rather try this another day.",
        "Back off, or insist once.",
    ],
    [
        "You repeat; {name} still won't put {poss} mouth where you need it—{subj} knows the job and avoids it.",
        "{Subj} understands what you're asking and still won't do it.",
        "End it, or punish with quiet.",
    ],
    [
        "You run the reps anyway—circles, suction, steady tongue.",
        "{name} {try}, but {poss} mouth stays useless; you stay frustrated.",
        "Nothing useful came from this—not for either of you.",
    ],
)

HOMO_FF_INTRO = intro(
    [
        "You find {name} and propose a {skill} session—tonight you work through what F+F bookings actually ask for: "
        "trib, oral, hands and fingers until the motion is professional, not performed. "
        "You get the room ready and make it plain that you'll be the practice.",
        "{name} {listen}, arms crossed—{subj} won't grind like {subj} means it, won't kiss on command; "
        "after a moment of awkward negotiation {subj} admits {subj}'d rather leave this for another day.",
        "Let {obj} keep {poss} distance, or insist once.",
    ],
    [
        "You press again; {name} still won't commit—{subj} wants to claim the work without "
        "the spread legs and honest friction.",
        "{Subj} knows what this is and still won't give it.",
        "End it, or let the establishment speak for you.",
    ],
    [
        "You run the physical reps anyway—grind, lick, reset.",
        "{name} {try}, but {subj} can't stay present; too much performance, not enough contact.",
        "By the end it still reads as mimicry—no surrender a paying client would feel.",
    ],
)

HOMO_MM_INTRO = intro(
    [
        "You find {name} and name the work—tonight you top {obj} so {poss} hole learns to take cock "
        "the way paying men expect: lube, angle, depth, breathing, no bracing off the rhythm. "
        "You put the lube on the table and start before the hesitation can calcify.",
        "{name} {listen}, jaw set—{subj} won't open, won't breathe through it; "
        "after a tense beat {subj} explains {subj}'d rather try this another day.",
        "Let {obj} walk, or insist once.",
    ],
    [
        "You repeat the order; {name} still won't take the work—{subj} wants what the booking offers "
        "without the part where {poss} ass gets used.",
        "{Subj} knows what's being asked and refuses it plainly.",
        "End it, or let disappointment do the teaching.",
    ],
    [
        "You run the reps anyway—stretch, prep, slow fuck.",
        "{name} {try}, but {subj} can't stay steady—too much bravado, too little follow-through.",
        "By the end it still reads as bravado—motion without nerve.",
    ],
)

BDSM_INTRO = intro(
    [
        "You find {name} for tonight's {skill} session and set rules first—safeword, pain scale, "
        "what the scene includes: rope, crop, clamps, toys. "
        "You name each part while the room is still neutral, then make clear that today you run it on {obj} in person.",
        "{name} {listen}, arousal and nerves tangled—{subj} jokes the cuffs away, won't hold position; "
        "after a moment {subj} admits {subj} would rather try this another day.",
        "Release {obj}, or insist once.",
    ],
    [
        "You repeat the terms; {name} still won't submit to what the slot requires—"
        "{subj} wants the aesthetic without the surrender.",
        "{Subj} knows what being tied and marked means and refuses it.",
        "End it, or freeze {obj} out.",
    ],
    [
        "You run checks and positions anyway.",
        "{name} {try}, but {subj} safewords early or fakes it—the scene wobbles.",
        "It ends with shaky headspace and nothing a kink client would rebook.",
    ],
)

SEX_INTRO_LORD = intro(
    [
        "You find {name} and propose tonight's {skill} session—real foreplay first: mouth, hands, teasing "
        "until {subj} is ready, then penetration on the mattress, the same rhythm and depth men pay for upstairs. "
        "You make clear you're the practice, and start removing what's in the way.",
        "{name} {listen}, flushed and evasive—{subj} won't meet your eyes, won't spread, won't say yes; "
        "after a quiet conversation {subj} explains {subj}'d rather try this another day.",
        "Back off, or insist once—calm, final.",
    ],
    [
        "You repeat the order; {name} still won't comply—{subj} clamps {poss} thighs, "
        "won't give what the session asks for.",
        "{Subj} knows exactly what this is and still refuses to do it.",
        "End it, or let silence do the rest.",
    ],
    [
        "You still run the work—foreplay, then penetration, rhythm until it holds.",
        "{name} {try}, but {subj} tightens, dries up, starfishes, or rushes—no progress a john would pay for.",
        "It ends without anything either of you can bill for.",
    ],
)

SEX_INTRO_LADY = intro(
    [
        "You find {name} and set up tonight's {skill} session—{subj} will work you: mouth and hands "
        "until you're ready, then {poss} cock inside you on your angles and pace. "
        "You name the work plainly and get comfortable so the lesson has somewhere to go.",
        "{name} {listen}, eyes sliding—{subj} won't touch like {subj} means it, won't go where you ask; "
        "after some circling {subj} explains {subj} would rather come back to this another time.",
        "Give {obj} space, or insist once.",
    ],
    [
        "You repeat the order; {name} still won't deliver—{subj} goes soft, pulls back, "
        "stalls with excuses while you stay open and waiting.",
        "{Subj} knows what the session asks and refuses to do it like a worker.",
        "End it, or punish with cold silence.",
    ],
    [
        "You run the work anyway—{subj} eating and fingering, then fucking to the count you set.",
        "{name} {try}, but {subj} loses hardness or rushes; no skill a paying woman would rebook.",
        "It ends with nothing either of you can use.",
    ],
)

SPEC_INTRO = intro(
    [
        "You find {name} for tonight's {skill} session and name the work aloud—which toys, which hole, "
        "how hard the pain, what words {subj} has to say: the same checklist that will run again "
        "if {subj} freezes in a paid room. You make clear this is hands-on, today, in person.",
        "{name} {listen}, ears burning—{subj} flinches when you say the acts, won't repeat them, "
        "won't strip on command; after some careful words {subj} admits {subj}'d rather try this another day.",
        "Let {obj} go, or insist once.",
    ],
    [
        "You slow down and repeat; {name} still won't commit—{subj} hedges, laughs off the items, "
        "won't get into position.",
        "{Subj} knows what's on the voucher and still won't deliver it.",
        "End the session.",
    ],
    [
        "You still walk through prep—lube, cuffs, positions.",
        "{name} {try}, but nerves snap the scene; {subj} safewords early or freezes when it matters.",
        "It ends with nothing a kink client would rebook.",
    ],
)

STRIP_INTRO = intro(
    [
        "You find {name} and set up tonight's {skill} session—{subj} will undress on beat: skin out, "
        "hips rolling, hands moving like there's money watching. "
        "You start the music and make {obj} lose the first layer before the shyness has time to win.",
        "{name} {listen}, arms folded—{subj} won't show skin like {subj} means it; "
        "after a moment {subj} admits {subj}'d rather try this another day.",
        "Back off, or insist once.",
    ],
    [
        "You ask again; {name} still won't bare skin like it's a product—{subj} knows what the tip jar "
        "asks and refuses to give it.",
        "{Subj} understands the job and still won't do it.",
        "Close it.",
    ],
    [
        "You run counts and poses anyway.",
        "{name} {try}, but {subj} keeps covering up; no heat in the room.",
        "It still reads as shy, not deliberate enough to earn.",
    ],
)

SVC_INTRO = intro(
    [
        "You find {name} and walk {obj} through tonight's {skill} drill—floor map, timed steps, "
        "the full routine: entries, spacing, refills before they're asked, anticipating what the room needs. "
        "You start the first round while {subj} is still listening.",
        "{name} {listen}, shoulders tense—{subj} says nobody notices these things, or {subj} is already tired, "
        "or {subj} just doesn't see the urgency tonight. "
        "After some back-and-forth {subj} admits {subj}'d rather do this another day.",
        "Ease off, or insist once.",
    ],
    [
        "You repeat the standards, slower; {name} still won't commit—{subj} rolls eyes, drags feet, "
        "won't pick up the pace.",
        "{Subj} knows what you're asking and refuses to do it.",
        "End the session.",
    ],
    [
        "You run the drills anyway—entries, timing, spacing.",
        "{name} {try}, but {subj} misses the cues or gets in the way.",
        "The habit stays unlearned—still sloppy where it shows.",
    ],
)

AG_INTRO = intro(
    [
        "You find {name} and lay out tonight's {skill} block—obstacle runs, rolls, climbing drills, "
        "recovery under pressure. You've already chalked the course on the wall. "
        "You name the stations and start the clock before {subj} can negotiate.",
        "{name} {listen}, already tired in {poss} posture—{subj} says the next job won't need this, "
        "or the bruises aren't worth it, or {subj} doesn't see the point of training for traps "
        "and corridors right now. {Subj} asks to postpone.",
        "Give {obj} the pass, or insist once.",
    ],
    [
        "You tighten the count; {name} still cheats the obstacles, won't finish the course, won't hit pace.",
        "{Subj} knows what's being asked and refuses to do it.",
        "Stop the session.",
    ],
    [
        "You run the drills anyway—obstacles, sprints, recovery rolls.",
        "{name} {try}, but {subj} trips on the same habit; still slow where it counts.",
        "The block ends with nothing improved.",
    ],
)

CH_INTRO = intro(
    [
        "You find {name} and sit {obj} down with tonight's {skill} exercises—"
        "reading a stranger in three lines, warmth that doesn't feel rehearsed, remembering names and details. "
        "You start the first round before {subj} can decide it's optional.",
        "{name} {listen}, knuckles pale—{subj} calls it fake, or says this isn't what {subj} was hired for, "
        "or {subj} just doesn't want to perform tonight. {Subj} asks to come back to it another day.",
        "Soften, or insist once.",
    ],
    [
        "You repeat the drill; {name} still won't commit—{subj} smirks, deflects, drops the warmth.",
        "{Subj} understands what you want and refuses to do it.",
        "Close it.",
    ],
    [
        "You run the scenarios anyway—prompts, callbacks, silence drills.",
        "{name} {try}, but {subj} slips into sarcasm or laughs it away; nothing lands.",
        "Still forgettable—no warmth anyone would remember.",
    ],
)


# ---------------------------------------------------------------------------
# Shared outcome helpers
# ---------------------------------------------------------------------------
LEAVE1 = "Deciding between exasperation and understanding, you smile and offer comfort. She accepts it gratefully."
LEAVE1_M = "Deciding between exasperation and understanding, you nod and offer comfort. He accepts it gratefully."
LEAVE1_THEY = "Deciding between exasperation and understanding, you smile and offer comfort. They accept it gratefully."
LEAVE2 = "You decide not to turn the situation into a conflict and leave quietly."

def _punished_f(skill_area):
    return [
        "You decide to force the situation and impose your authority. After some reflection, you choose the punishment, "
        "and she eventually consents. You're not sure she's learned much about how to serve %s clients, "
        "but she's certainly absorbed a lesson in obedience and discipline." % skill_area,
        "You impose your authority and settle on a consequence. She accepts it—tears, nodding. "
        "Whether the %s technique improved tonight is unclear, but the lesson in discipline was received." % skill_area,
    ]

def _punished_m(skill_area):
    return [
        "You decide to force the situation and impose your authority. After some reflection, you choose the punishment, "
        "and he eventually consents. You're not sure he's learned much about serving %s clients, "
        "but he's certainly absorbed a lesson in obedience and discipline." % skill_area,
        "You impose your authority and settle on a consequence. He accepts it in the end. "
        "Whether the %s technique improved tonight is unclear, but the lesson in discipline was received." % skill_area,
    ]

def _punished_they(skill_area):
    return [
        "You decide to force the situation and impose your authority. After some reflection, you choose the punishment, "
        "and they eventually consent. You're not sure they've learned much about %s, "
        "but they've certainly absorbed a lesson in obedience and discipline." % skill_area,
        "You impose your authority and settle on a consequence. They accept it in the end. "
        "Whether the %s skill improved tonight is unclear, but the lesson in discipline was received." % skill_area,
    ]


# ---------------------------------------------------------------------------
def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    by = {x["id"]: x for x in data}

    # ===== HAND =====

    by["training_homo_hand_ff"].update(
        description=HAND_HOMO_FF_DESC,
        training_texts=tx(
            "As the shyness lifts she follows your lead and undresses. You place her fingers on your body and begin "
            "the drill—clit, pressure, rhythm, when to ease off before things go numb. You correct what misses with "
            "quiet words and reward what works with warmth, rocking your hips into good contact. You walk her through "
            "what paying women look for and how to read the signals in their breathing; by the end her hands can "
            "deliver what a booked hour actually demands.",
            LEAVE1, LEAVE2,
            _punished_f("hand"),
            "You insist, and after a moment she convinces herself. You undress together and begin—her fingers on you, "
            "learning pressure and rhythm under your direction. You correct and reward with contact and patience; "
            "you explain what clients want and how to spot it. By the end the reluctance is gone and something real stays.",
        ),
        training_intro_sequences=copy.deepcopy(HAND_HOMO_FF_INTRO),
    )

    by["training_homo_hand_mm"].update(
        description=HAND_HOMO_MM_DESC,
        training_texts=tx(
            "Once the posturing drops he follows your lead and strips. You put his hand on your cock and start the work—"
            "grip, stroke, pace, reading the tension as it builds. You correct with nudges and friction, reward what "
            "lands with small sounds and permission to keep going. You explain what johns signal when they're close "
            "and how to read it before they say a word; by the end his hand can deliver what the next booking needs.",
            LEAVE1_M, LEAVE2,
            _punished_m("hand"),
            "You insist; he convinces himself and strips beside you. You put his hand where it belongs and drill—"
            "grip, stroke, pace. You correct what misses and reward what lands. You explain what johns need; "
            "by the end something real stays in his wrist.",
        ),
        training_intro_sequences=copy.deepcopy(HAND_HOMO_MM_INTRO),
    )

    by["training_hetero_hand_lord"].update(
        description=HAND_HET_LORD_DESC,
        training_texts=tx(
            "Seeing you start to undo the excess clothing, she follows—a timid but willing look as she settles close. "
            "You guide her hand onto your cock and begin: stroke, squeeze, pace, thumb placement. You correct what "
            "misses with murmured words and reward good moments with warmth and quiet sounds that tell her she's "
            "getting it right. You explain what male clients signal when they're close and how to read it in seconds; "
            "by the end her hands can deliver what men pay for.",
            LEAVE1, LEAVE2,
            _punished_f("hand"),
            "You insist; she convinces herself and wraps your cock like it's the job she chose. You correct grip "
            "and tempo, reward the good strokes with warmth. You explain how to read a man's body when he's close; "
            "by the end she can finish what clients rebuy.",
        ),
        training_intro_sequences=copy.deepcopy(HAND_HET_FWORKER_INTRO),
    )

    by["training_hetero_hand_lady"].update(
        description=HAND_HET_LADY_DESC,
        training_texts=tx(
            "His nerves settle as you guide him into position. You place his hands on your body and start the drill: "
            "tits, thighs, clit—pressure, circles, when to stay still. You correct what misses and reward what "
            "lands with warmth and small sounds that guide him. You explain what female clients signal and how to "
            "read a woman's breathing in seconds; by the end his hands know what they're doing.",
            LEAVE1_M, LEAVE2,
            _punished_m("hand"),
            "You insist; he convinces himself and puts his hands where told, properly this time. You guide the "
            "drill—circles, pressure, pace—correcting and rewarding with warmth. You explain what a woman's body "
            "is asking for; by the end he understands.",
        ),
        training_intro_sequences=copy.deepcopy(HAND_HET_MWORKER_INTRO),
    )

    # ===== ORAL =====

    by["training_homo_oral_ff"].update(
        description=ORAL_HOMO_FF_DESC,
        training_texts=tx(
            "Once the reluctance breaks she follows your lead and settles between your thighs. You steer with hips "
            "and words as her tongue finds the right places—clit, suction, breath, staying where it counts. You "
            "correct angle and pressure, reward what works with slow rolls and quiet praise. You explain how to read "
            "a woman's thighs and what the signals mean when they change; by the end her mouth can deliver what "
            "the rate card promises.",
            LEAVE1, LEAVE2,
            _punished_f("oral"),
            "You insist; she convinces herself and lowers her face where you pointed. You steer tongue and pressure, "
            "correct what misses, reward with warmth. You explain what paying women signal; by the end her mouth "
            "can do the work.",
        ),
        training_intro_sequences=copy.deepcopy(ORAL_INTRO_HOMO_FF),
    )

    by["training_homo_oral_mm"].update(
        description=ORAL_HOMO_MM_DESC,
        training_texts=tx(
            "He kneels once the pride drops and takes your cock in his mouth. You coach lips, tongue, and depth—"
            "when to hold, when to breathe, how to use his hand at the base. You correct with taps and words, "
            "reward good rhythm with slow thrusts and rough praise. You explain what johns signal when they want "
            "more and how to read it without being told; by the end his mouth can do what the menu sells.",
            LEAVE1_M, LEAVE2,
            _punished_m("oral"),
            "You insist; he kneels and commits his mouth to the work. You coach depth and rhythm, correct what "
            "misses with patience. You explain what johns need; by the end suction turns serious—jaw, tongue, "
            "the rhythm a paying man would rebook.",
        ),
        training_intro_sequences=copy.deepcopy(ORAL_INTRO_HOMO_MM),
    )

    by["training_hetero_oral_lord"].update(
        description=ORAL_HET_F_DESC,
        training_texts=tx(
            "She kneels and takes you in her mouth—hand and lips together, learning depth, tongue, no teeth. "
            "You correct what misses with quiet words and small adjustments, reward what works with slow thrusts "
            "and sounds that tell her she's doing it right. You explain what a satisfied man signals and how to "
            "read the difference between close and done; by the end she can finish what johns pay to rebook.",
            LEAVE1, LEAVE2,
            _punished_f("oral"),
            "You insist; she convinces herself and takes you deep enough to matter. You correct rhythm and depth, "
            "reward what works with patience and warmth. You explain how to read a man's body; by the end she can "
            "deliver what clients pay for.",
        ),
        training_intro_sequences=copy.deepcopy(ORAL_INTRO_HET_F),
    )

    by["training_hetero_oral_lady"].update(
        description=ORAL_HET_M_DESC,
        training_texts=tx(
            "He settles between your thighs and finds the right angle—tongue on clit, steady pressure, staying "
            "where you steer him. You guide with your hips and words, correcting technique and rewarding what "
            "works with sounds and warmth. You explain how to read a woman's breathing like a clock and what to "
            "do when the rhythm changes; by the end his mouth can do what female bookings pay for.",
            LEAVE1_M, LEAVE2,
            _punished_m("oral"),
            "You insist; he settles between your thighs and stays where your clit is. You correct rhythm and "
            "pressure, reward with warmth. You explain what a woman's body signals; by the end his mouth can do "
            "the work.",
        ),
        training_intro_sequences=copy.deepcopy(ORAL_INTRO_HET_M),
    )

    # ===== HOMO FF (trib + oral + hands) =====

    by["training_homo_homo_ff"].update(
        description=HOMO_FF_DESC,
        training_texts=tx(
            "As the shyness breaks she undresses and follows you to the mattress—bodies close, warmth building. "
            "You work through what F+F bookings actually ask for: trib, grinding, tongue, fingers inside where "
            "they count. You correct her movements with hands and whispered words, reward the right contact with "
            "praise and pace. You explain what makes a repeat F+F client come back and how to read desire versus "
            "performance; by the end her body moves like the booking matters.",
            LEAVE1, LEAVE2,
            _punished_f("F+F"),
            "You insist; she convinces herself and drops the distance. You undress and work through the positions—"
            "grind, tongue, hands. You correct and reward; by the end she moves like repeat clients matter.",
            "{pronoun} couldn't stay present—technique stayed performative when it needed to be real.",
        ),
        training_intro_sequences=copy.deepcopy(HOMO_FF_INTRO),
    )

    # ===== HOMO MM (anal, manager tops) =====

    by["training_homo_homo_mm"].update(
        description=HOMO_MM_DESC,
        training_texts=tx(
            "He strips and gets into position once the bravado drops. You prep with lube and patience, then push "
            "in—slow, teaching him to breathe through it, adjust angles, take depth without bracing. You correct "
            "what tightens with steady words, reward what opens with rhythm and contact. You explain what paying "
            "tops expect and how to read their pace; by the end his body can do the job without improvisation.",
            LEAVE1_M, LEAVE2,
            _punished_m("M+M anal"),
            "You insist; he convinces himself and holds the position. You prep and push in—slow at first, teaching "
            "breathing and depth. You correct and reward; by the end his body is trained for paying tops.",
            "{pronoun} couldn't stay steady—useless for paying tops tonight.",
        ),
        training_intro_sequences=copy.deepcopy(HOMO_MM_INTRO),
    )

    # ===== BDSM =====

    for bid in ("training_homo_bdsm_mm", "training_homo_bdsm_ff",
                "training_hetero_bdsm_lord", "training_hetero_bdsm_lady"):
        wg = by[bid]["worker_gender"]
        if wg == "female":
            ttb = tx(
                "Once she settles you run the scene—rope first, then clamps, then toys where the voucher says. "
                "You walk her through pain scale and breathing, adjust tightness and position between strikes. "
                "You correct what flinches with steady words, reward what holds with controlled touch and warmth. "
                "You explain what kink clients pay to see and how to read when pain crosses into genuine distress; "
                "by the end the booking could close without improvisation.",
                LEAVE1, LEAVE2,
                _punished_f("BDSM"),
                "You insist; she convinces herself and holds position through the sting. You run the scene—rope, "
                "pain, toys—correcting and rewarding. By the end she can deliver what the booking asked for.",
            )
        else:
            ttb = tx(
                "He strips and submits once the nerves settle—bound, edged, cock straining while the scene runs. "
                "You walk him through pain scale and breathing, adjust tightness between strikes. You correct what "
                "braces with steady words, reward what holds with controlled relief and permission. You explain "
                "what sadists pay to see and how to stay inside the rules; by the end the booking could close clean.",
                LEAVE1_M, LEAVE2,
                _punished_m("BDSM"),
                "You insist; he submits and takes the scene—bound, marked, staying hard through the sting. "
                "You correct and reward; by the end his body can do what the voucher demands.",
            )
        by[bid].update(description=BDSM_DESC, training_texts=ttb,
                       training_intro_sequences=copy.deepcopy(BDSM_INTRO))

    # ===== SEX hetero =====

    by["training_hetero_sex_lord"].update(
        description=SEX_DESC,
        training_texts=tx(
            "Seeing the first pieces of clothing fall, she follows you to the mattress—a shy smile, a flicker of "
            "anticipation. You start with real foreplay: mouth, hands, teasing until she's wet and ready. Then you "
            "slide inside her and fuck with the depth and pace men pay for, correcting what she does with her hips "
            "and rewarding the right responses with slow thrusts, caresses, and warmth. You explain what clients "
            "signal when they're close and how to read it in seconds to keep them satisfied.",
            LEAVE1, LEAVE2,
            _punished_f("sex"),
            "You insist; she convinces herself, and you undress together. You run real foreplay first, then slide "
            "inside her and fuck with what the floor sells—correcting, rewarding with slow thrusts and warmth. "
            "You explain what a man's body tells you when he's close and how to respond.",
        ),
        training_intro_sequences=copy.deepcopy(SEX_INTRO_LORD),
    )

    by["training_hetero_sex_lady"].update(
        description=SEX_DESC,
        training_texts=tx(
            "He follows your lead as you settle into the session—mouth and hands on you first until you're ready, "
            "then his cock inside you on your angles and pace. You correct his rhythm with words and nails, reward "
            "what works with warmth and the sounds that tell him he's doing it right. You explain what female "
            "clients signal and how to read a woman's body to adjust without being told; by the end he can deliver "
            "what a paid hour demands.",
            LEAVE1_M, LEAVE2,
            _punished_m("sex"),
            "You insist; he convinces himself and works you the way you named—mouth and hands first, then cock "
            "inside you on your pace. You correct rhythm and reward what works. You explain what a woman's body "
            "asks for; by the end he can answer it.",
        ),
        training_intro_sequences=copy.deepcopy(SEX_INTRO_LADY),
    )

    # ===== SPECIAL =====

    by["training_hetero_special_lord"].update(
        description=SPEC_DESC,
        training_texts=tx(
            "She undresses and gets into position for the scene—toys laid out, the checklist from the voucher "
            "between you both. You walk her through each item hands-on: which hole, which toy, how hard, what "
            "words to say. You correct what flinches with patience and reward what she delivers with steadiness "
            "and warmth. You explain what kink clients expect and how to read when the scene needs adjustment; "
            "by the end she can close the booking without improvisation.",
            LEAVE1, LEAVE2,
            _punished_f("special bookings"),
            "You insist; she convinces herself and stops flinching at the checklist. You walk the items—toys, "
            "positions, words—correcting and rewarding. By the end she can deliver what was prepaid.",
        ),
        training_intro_sequences=copy.deepcopy(SPEC_INTRO),
    )

    by["training_hetero_special_lady"].update(
        description=SPEC_DESC,
        training_texts=tx(
            "He undresses and gets into position—the voucher items laid out between you both. You walk him through "
            "each entry hands-on: toys, pain, position, the words the booking asks for. You correct what freezes "
            "with patience and reward what he delivers with steadiness. You explain what the client prepaid and "
            "how to read when the scene needs adjustment; by the end he can close the booking without freezing.",
            LEAVE1_M, LEAVE2,
            _punished_m("special bookings"),
            "You insist; he convinces himself and runs the scene without freezing. You walk the items—toys, "
            "positions, words—correcting and rewarding. By the end he can deliver what was prepaid.",
        ),
        training_intro_sequences=copy.deepcopy(SPEC_INTRO),
    )

    # ===== STRIPTEASE =====

    for sid in ("training_striptease_ff", "training_striptease_mm",
                "training_striptease_mf", "training_striptease_fm"):
        wg = by[sid]["worker_gender"]
        if wg == "female":
            ttb = tx(
                "As the first layer drops she follows the count—skin out, hips rolling, hands on herself like "
                "there's money in the room. You correct her timing with clicks and words, reward what lands with "
                "nods and pace. You explain what a paying eye wants to see and how to hold the tease without "
                "rushing; by the end the strip reads as deliberate, not apologetic.",
                LEAVE1, LEAVE2,
                _punished_f("striptease"),
                "You insist; she convinces herself and stops hiding behind hair and hands. You correct timing and "
                "posture, reward what sells. By the end the strip reads as product—something a paying eye would "
                "tip for.",
            )
        else:
            ttb = tx(
                "He finds the beat once the self-consciousness lifts—cover dropped, hips rolling, cock out when "
                "told, eyeline where it belongs. You correct his timing with words and nods, reward what sells "
                "with pace and approval. You explain what paying watchers tip for and how to hold the tease; "
                "by the end the show reads as deliberate, not awkward.",
                LEAVE1_M, LEAVE2,
                _punished_m("striptease"),
                "You insist; he convinces himself and quits covering. You correct timing and posture, reward "
                "what lands. By the end the show sells—something worth tipping for.",
            )
        by[sid].update(description=STRIP_DESC, training_texts=ttb,
                       training_intro_sequences=copy.deepcopy(STRIP_INTRO))

    # ===== SFW — Service =====

    by["training_sfw_service"].update(
        description=SVC_DESC,
        training_texts=tx(
            "They start the first drill—entries, spacing, timing—and you walk beside them correcting "
            "live: too close, too slow, refill late, wrong read on what the room needs. You reward what "
            "clicks with nods and repeat the good reps until the movement looks natural, not rehearsed. "
            "You explain what people notice first—a drink that arrives before it's asked for, a door "
            "held at the right second—and how to stay invisible while being present. By the end they "
            "can read a room and serve it without thinking.",
            LEAVE1_THEY, LEAVE2,
            _punished_they("service"),
            "You insist; they stop stalling and run the drill for real. You correct live and reward "
            "what clicks. By the end the movement looks natural—someone who belongs on the floor.",
            "{pronoun} still fumbles the timing—not ready for the floor tonight.",
        ),
        training_intro_sequences=copy.deepcopy(SVC_INTRO),
    )

    # ===== SFW — Agility =====

    by["training_sfw_agility"].update(
        description=AG_DESC,
        training_texts=tx(
            "Once the complaining stops they run the real course—obstacle sprints, rolls, wall climbs, "
            "recovery under load. You call transitions and correct form live: faster off the mark, lower "
            "through the gap, land quiet, recover without wasting a breath. You reward clean reps with water "
            "and pacing. You explain what the field actually demands—how to spot a trap trigger, scale "
            "a crumbling wall, move through a dungeon corridor without making a sound—and by the end "
            "they've covered real ground.",
            LEAVE1_THEY, LEAVE2,
            _punished_they("agility"),
            "You insist; they stop negotiating and run the course for real. You correct form live, reward "
            "clean reps. By the end the work got done—the body moves the way fieldwork needs it to.",
            "{pronoun} stayed slow—same habit, no progress tonight.",
        ),
        training_intro_sequences=copy.deepcopy(AG_INTRO),
    )

    # ===== SFW — Charm =====

    by["training_sfw_charm"].update(
        description=CH_DESC,
        training_texts=tx(
            "Once the defensiveness settles they run the real work—reading a stranger in seconds, "
            "compliments that land, names recalled from a single meeting. You correct cadence and word "
            "choice live, reward what works with a nod that means keep going. You explain what makes "
            "warmth feel genuine instead of performed—the pause before a name, the detail nobody "
            "expected you to remember—and by the end something real starts to show through the "
            "practiced surface.",
            LEAVE1_THEY, LEAVE2,
            _punished_they("charm"),
            "You insist; they stop deflecting and run the exercises for real. You correct live and "
            "reward what lands. By the end something breaks open—warmth that isn't rehearsed.",
            "{pronoun} still can't sell a compliment—flat, forgettable.",
        ),
        training_intro_sequences=copy.deepcopy(CH_INTRO),
    )

    for row in by.values():
        if hasattr(row, "pop"):
            row.pop("training_branch_stems", None)

    out = [by[x["id"]] for x in data]
    JSON_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Updated", JSON_PATH)


if __name__ == "__main__":
    main()
