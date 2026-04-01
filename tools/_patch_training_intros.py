"""One-shot patch: add punished and insist_accepted intro sequences to interactions_training.json."""
import json
import os

path = os.path.join(os.path.dirname(__file__), "..", "game", "data", "interactions", "interactions_training.json")

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

new_intros = {
    # === HAND ===
    "training_homo_hand_ff": {
        "punished": [
            "You grab {poss} wrist and force {poss} fingers back onto your pussy.",
            "{Subj} flinches but you hold {poss} hand in place, pressing {poss} fingertips where they need to be.",
            "You set the rhythm yourself\u2014circles, pressure, speed\u2014using {poss} hand like a tool until it moves on its own."
        ],
        "insist_accepted": [
            "{name} swallows hard, then reaches between your legs without being told again.",
            "{poss} hand is stiff but {poss} fingers find the right spot. The lesson starts."
        ]
    },
    "training_homo_hand_mm": {
        "punished": [
            "You grab {poss} hand and wrap it around your cock yourself.",
            "{Subj} tries to pull away but you hold {poss} grip tight and set the stroke pace.",
            "You make {obj} repeat the motion\u2014base to tip, grip and twist\u2014until the hand moves without being forced."
        ],
        "insist_accepted": [
            "{name} exhales through {poss} teeth, then wraps {poss} hand around your cock.",
            "The grip is reluctant but it holds. You correct the angle and the lesson starts."
        ]
    },
    "training_hetero_hand_lord": {
        "punished": [
            "You take {poss} hand and wrap it around your cock, holding it there.",
            "{Subj} resists but you force the grip tight and make {poss} hand stroke at your pace.",
            "The technique drills itself into {poss} wrist through sheer repetition. You don't let go until it's automatic."
        ],
        "insist_accepted": [
            "{name} reaches for your cock with a clenched jaw. The hand closes around the shaft.",
            "The first stroke is stiff but {subj} doesn't pull away. You correct the grip and start the drill."
        ]
    },
    "training_hetero_hand_lady": {
        "punished": [
            "You grab {poss} wrist and shove {poss} fingers between your legs.",
            "{Subj} flinches but you pin {poss} hand on your clit and force the rhythm\u2014circles, pressure, pace.",
            "{poss} hand steadies under yours. When you let go, the fingers keep moving on their own."
        ],
        "insist_accepted": [
            "{name} sets {poss} jaw and puts {poss} hand between your legs without being asked again.",
            "The touch is stiff but {poss} fingers find your clit. You guide the first pass and the lesson begins."
        ]
    },
    # === ORAL ===
    "training_homo_oral_mm": {
        "punished": [
            "You hold the back of {poss} head and push your cock past {poss} lips.",
            "{Subj} gags but you don't let {obj} pull back. You hold the depth steady and set the breathing pace.",
            "The mouth learns to take it because you don't give it the choice to close."
        ],
        "insist_accepted": [
            "{name} opens {poss} mouth slowly, jaw trembling. You feed {obj} your cock at a controlled pace.",
            "The first pass is messy but {subj} doesn't pull away. The drill starts."
        ]
    },
    "training_homo_oral_ff": {
        "punished": [
            "You grab {poss} hair and pull {poss} face between your legs.",
            "{Subj} resists for a breath, then {poss} mouth opens against your pussy.",
            "You hold {obj} there, grinding into {poss} tongue, until the mouth starts working on its own."
        ],
        "insist_accepted": [
            "{name} leans in with visible reluctance, then puts {poss} mouth on your pussy.",
            "The tongue barely moves at first. You hold {poss} head and guide the angle. The drill starts."
        ]
    },
    "training_hetero_oral_lord": {
        "punished": [
            "You hold {poss} jaw open and slide your cock into {poss} mouth.",
            "{Subj} gags on the first push but you grip the back of {poss} head and set the rhythm.",
            "The mouth learns depth because you don't let it choose shallow."
        ],
        "insist_accepted": [
            "{name} kneels and opens {poss} mouth. Tears form before your cock even touches {poss} tongue.",
            "{Subj} takes the first inch. You hold steady and let {obj} adjust. The drill begins."
        ]
    },
    "training_hetero_oral_lady": {
        "punished": [
            "You grab {poss} hair and press {poss} face into your pussy.",
            "{Subj} tries to pull back but your thighs lock around {poss} head.",
            "The tongue starts moving out of necessity. You hold {obj} there until the rhythm is real."
        ],
        "insist_accepted": [
            "{name} leans in, jaw tight, and puts {poss} mouth on you.",
            "The first pass is reluctant but the tongue finds your clit. You guide {poss} head and start the drill."
        ]
    },
    # === HOMO ===
    "training_homo_homo_ff": {
        "punished": [
            "You pull {obj} against you and pin {poss} hips to yours, thighs locked.",
            "{Subj} resists but you hold the position\u2014clit to clit, skin against skin.",
            "You grind against {obj} until {poss} body stops fighting the contact and the hips start moving."
        ],
        "insist_accepted": [
            "{name} lets you pull {obj} close, body rigid. Your skin presses against {poss}.",
            "{poss} breathing is shallow but {subj} doesn't pull away. You guide {poss} hips and start."
        ]
    },
    "training_homo_homo_mm": {
        "punished": [
            "You push {obj} face-down on the bench, lube up, and enter {obj} without negotiation.",
            "{Subj} tenses and grips the bench but you hold the pace\u2014steady, controlled, not brutal.",
            "The body learns to open because you don't let it clench shut."
        ],
        "insist_accepted": [
            "{name} bends over the bench with every muscle braced. You lube up and position yourself.",
            "{Subj} exhales as you enter slow. The body is rigid but it doesn't fight. The drill starts."
        ]
    },
    # === SEX ===
    "training_hetero_sex_lord": {
        "punished": [
            "You push {obj} onto {poss} back and hold {poss} thighs apart.",
            "You enter {obj} at a steady pace. {Subj} gasps but you don't stop.",
            "The hips learn rhythm because you set it and hold it until {poss} body catches up."
        ],
        "insist_accepted": [
            "{name} lies back with a clenched jaw and spreads {poss} legs.",
            "You enter {obj} slow, giving {poss} body time to adjust. The first thrust is stiff but {subj} doesn't close up."
        ]
    },
    "training_hetero_sex_lady": {
        "punished": [
            "You pull {obj} on top of you and guide {poss} cock inside yourself.",
            "{Subj} freezes but you lock your legs around {obj} and set the rhythm with your hips.",
            "{poss} body learns to fuck because yours won't let {obj} stop."
        ],
        "insist_accepted": [
            "{name} positions {poss}self between your legs, hard but hesitant.",
            "{Subj} enters you slowly. The first thrust is stiff but the cock stays in. You guide {poss} hips and start."
        ]
    },
    # === BDSM ===
    "training_homo_bdsm_mm": {
        "punished": [
            "You cuff {poss} wrists to the bench and pick up the crop.",
            "The first strike lands across {poss} thighs. {Subj} jerks but the restraints hold.",
            "You work through the full sequence at your pace. The body accepts what the mouth refused."
        ],
        "insist_accepted": [
            "{name} holds out {poss} wrists with shaking hands. You close the cuffs.",
            "{Subj} flinches when you pick up the crop but stays in position. The drill begins."
        ]
    },
    "training_homo_bdsm_ff": {
        "punished": [
            "You tie {obj} to the bench and apply the clamps without warning.",
            "{Subj} cries out but the bindings hold. You run the crop across {poss} skin at your pace.",
            "The body stops fighting when the pain becomes rhythm instead of surprise."
        ],
        "insist_accepted": [
            "{name} extends {poss} wrists. You tie {obj} down while {subj}'s still trembling.",
            "The first clamp draws a gasp but {subj} holds position. You start the sequence."
        ]
    },
    "training_hetero_bdsm_lord": {
        "punished": [
            "You tie {obj} to the bench and pick up the crop.",
            "The first strike crosses {poss} thighs. {Subj} screams but the rope holds.",
            "You run the full impact sequence at your pace until the flinching stops and the body holds still."
        ],
        "insist_accepted": [
            "{name} holds out {poss} wrists, eyes on the crop. You cuff {obj} to the bench.",
            "The first light strike makes {obj} jerk. But {subj} stays. The session starts."
        ]
    },
    "training_hetero_bdsm_lady": {
        "punished": [
            "You cuff {poss} wrists and strip {obj}. The crop comes out.",
            "The first strike lands across {poss} chest. {Subj} grits {poss} teeth but the cuffs hold.",
            "A man who won't submit to a woman's tools learns through the tools themselves."
        ],
        "insist_accepted": [
            "{name} extends {poss} arms stiffly. You close the cuffs and {subj} doesn't pull back.",
            "The pride is still there, but the body complies. You pick up the crop and begin."
        ]
    },
    # === SPECIAL ===
    "training_hetero_special_lord": {
        "punished": [
            "You put {obj} in the position yourself, arranging {poss} body like a prop.",
            "{Subj} protests but you run the full routine over {obj}\u2014toy, position, sequence.",
            "If {subj} won't practice, {subj} learns by receiving. The routine finishes on your schedule."
        ],
        "insist_accepted": [
            "{name} takes the first position reluctantly, fumbling with the placement.",
            "You correct {poss} body and start the sequence. {Subj} follows, clumsy but present."
        ]
    },
    "training_hetero_special_lady": {
        "punished": [
            "You arrange {poss} body into the position and place the tools yourself.",
            "{Subj} protests but you run the special over {obj} without stopping to explain.",
            "The body learns the sequence by being put through it. Your timeline, not {poss}."
        ],
        "insist_accepted": [
            "{name} takes the position with a set jaw, body stiff.",
            "You place {poss} hands where they need to be and start the routine. {Subj} follows."
        ]
    },
    # === STRIPTEASE ===
    "training_striptease_ff": {
        "punished": [
            "You walk over and start undressing {obj} yourself\u2014piece by piece, on your timing.",
            "{Subj} stands rigid and exposed while your hands peel each layer away.",
            "The lesson: a client won't wait for {obj} to feel ready. The body learns to be seen."
        ],
        "insist_accepted": [
            "{name} takes a breath and reaches for {poss} first button. Hands still shaking.",
            "The first piece comes off too fast but {subj} keeps going. The routine starts."
        ]
    },
    "training_striptease_mm": {
        "punished": [
            "You walk over and start pulling {poss} clothes off yourself\u2014shirt, belt, trousers.",
            "{Subj} stands exposed while you strip {obj} at your pace. No input, no negotiation.",
            "When {subj}'s naked and still standing, the shame has been overruled. That's the lesson."
        ],
        "insist_accepted": [
            "{name} grabs {poss} shirt collar and pulls it off with one motion. No finesse, but it's moving.",
            "The belt follows. {Subj} isn't performing yet, but the clothes are coming off. You start coaching."
        ]
    },
    "training_striptease_mf": {
        "punished": [
            "You walk to {obj} and start peeling {poss} clothes off yourself\u2014slow, deliberate.",
            "{Subj} stands frozen while your hands unclasp {poss} bra and pull {poss} skirt down.",
            "Exposed and silent, {poss} body learns that the reveal happens on someone else's schedule."
        ],
        "insist_accepted": [
            "{name} reaches for {poss} top button with trembling fingers. It comes undone.",
            "The second follows. It's not a performance yet, but the body is moving. You start coaching pace."
        ]
    },
    "training_striptease_fm": {
        "punished": [
            "You walk over and pull {poss} shirt off {obj} yourself\u2014then the belt, then the trousers.",
            "{Subj} stands naked while a woman undresses {obj} on her terms. No say in the timing.",
            "When {poss} cock is out and {subj}'s still standing, the shame has been broken."
        ],
        "insist_accepted": [
            "{name} grabs {poss} top button and yanks it open. No style, but it's starting.",
            "{Subj} pulls the shirt off and reaches for the belt. You correct the pacing and begin coaching."
        ]
    },
    # === SFW ===
    "training_sfw_service": {
        "punished": [
            "You load a heavier tray and tell {obj} to run the full circuit\u2014twice, no breaks.",
            "{Subj} picks it up with a sour face but starts moving. The arms burn by the second lap.",
            "If {subj} won't practice the craft, {subj} earns the right to practice through labor."
        ],
        "insist_accepted": [
            "{name} picks up the tray with a resentful grip and starts the circuit.",
            "The first pass is sloppy but {subj} doesn't stop. You walk alongside and correct."
        ]
    },
    "training_sfw_agility": {
        "punished": [
            "You tell {obj} to run the course again\u2014three more laps, no walking, no quitting.",
            "{Subj} drags {poss}self through the first obstacle, legs shaking, lungs burning.",
            "By the third lap the form is ragged but the body moved when it wanted to die. That's enough."
        ],
        "insist_accepted": [
            "{name} stands up slowly, wiping sweat off {poss} face.",
            "{Subj} approaches the first obstacle and starts moving. Slow, but moving. You coach from the side."
        ]
    },
    "training_sfw_charm": {
        "punished": [
            "You run scenario after scenario without pausing\u2014rude guest, silent noble, testing flirt.",
            "{Subj} stumbles through each one, face burning, voice cracking.",
            "By the tenth repetition the responses start coming automatically instead of painfully."
        ],
        "insist_accepted": [
            "{name} straightens up and faces you. The smile is forced but it's there.",
            "You play the guest. {Subj} delivers the greeting. Wooden, but complete. The drill continues."
        ]
    },
}

for entry in data:
    eid = entry.get("id", "")
    if eid in new_intros:
        intro_seq = entry.setdefault("training_intro_sequences", {})
        intro_seq["punished"] = new_intros[eid]["punished"]
        intro_seq["insist_accepted"] = new_intros[eid]["insist_accepted"]

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Verify
count_p = sum(1 for e in data if "punished" in e.get("training_intro_sequences", {}))
count_i = sum(1 for e in data if "insist_accepted" in e.get("training_intro_sequences", {}))
print(f"Done: {count_p} punished intros, {count_i} insist_accepted intros added")
