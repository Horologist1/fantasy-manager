# academy_library_quest.rpy — Academy library side quest (sealed training manual)
#
# Redesigned flow: Prologue + Act 1 (paper trail) + Act 2 (the seal) + Epilogue.
# Minimum 3 visits (prologue, act1, act2). Lattice item skips to seal from any point post-prologue.
# Token: MANAGE (6 letters). MANAGER accepted with corrective nudge.

default academy_lib_stage = 0
default academy_lib_last_visit_total_days = None
default academy_lib_seal_attempts_today = 0

default persistent.academy_lib_quest_completed_once = False

init python:
    store.ACADEMY_LIB_CIPHER_WORD = "MANAGE"

    def academy_lib_cipher_accept(guess):
        """
        True if the typed token opens the seal. MANAGER (7) is accepted with a nudge.
        Returns (accepted: bool, narrator_nudge: str|None).
        """
        g = (guess or "").strip().upper()
        if not g:
            return (False, None)
        key = getattr(store, "ACADEMY_LIB_CIPHER_WORD", "MANAGE")
        if g == key:
            return (True, None)
        if g == "MANAGER":
            return (True, "manager_not_manage")
        return (False, None)

    def academy_lib_has_cipher_lattice():
        inv = getattr(store, "manager_inventory", None) or []
        for it in inv:
            if isinstance(it, (list, tuple)) and len(it) >= 2 and it[0] == "cipher_lattice" and int(it[1] or 0) > 0:
                return True
        return False

    def academy_lib_ensure_event_flags():
        if not hasattr(store, "event_flags") or store.event_flags is None:
            store.event_flags = {}
        if not hasattr(store.event_flags, "get"):
            store.event_flags = {}

    def academy_lib_today():
        return int(calculate_total_days())

    def academy_lib_mark_visit_consumed():
        store.academy_lib_last_visit_total_days = academy_lib_today()

    def academy_lib_is_same_day():
        return (store.academy_lib_last_visit_total_days is not None) and (store.academy_lib_last_visit_total_days == academy_lib_today())

    def academy_lib_can_attempt_seal():
        """Post-prologue, quest not finished, not already decrypted."""
        if int(getattr(store, "academy_lib_stage", 0) or 0) < 1:
            return False
        if not getattr(store, "event_flags", None) or not hasattr(store.event_flags, "get"):
            return False
        if store.event_flags.get("academy_lib_manual_found"):
            return False
        if store.event_flags.get("academy_lib_decrypt_done"):
            return False
        return True

    def academy_lib_on_cipher_lattice_acquired():
        academy_lib_ensure_event_flags()
        first = not bool(store.event_flags.get("academy_lib_lattice_acquired"))
        store.event_flags["academy_lib_lattice_acquired"] = True
        if first:
            renpy.notify("Academy library: use this at the wax seal. The house token is six letters: MANAGE.")

    def academy_lib_migrate_old_saves():
        """Map old 7-stage quest to new 3-act structure for mid-quest saves. Runs once."""
        ef = store.event_flags
        if ef.get("academy_lib_manual_found"):
            return
        if ef.get("academy_lib_migrated_v2"):
            return
        old = int(getattr(store, "academy_lib_stage", 0) or 0)
        if old <= 0:
            return
        if old == 1:
            store.academy_lib_stage = 1
        elif old in (2, 3, 4):
            store.academy_lib_stage = 1
            ef["academy_lib_hint_a"] = True
        elif old >= 5:
            store.academy_lib_stage = 2
            ef["academy_lib_hint_a"] = True
            ef["academy_lib_hint_b"] = True
            ef["academy_lib_hint_c"] = True
            ef["academy_lib_ready_decrypt"] = True
        ef["academy_lib_migrated_v2"] = True


# ============================================================
#  ENTRY POINT
# ============================================================

label academy_lib_quest_return:
    $ renpy.show_screen("map_screen")
    $ renpy.show_screen("academy_menu")
    jump tavern_screen


label academy_library_quest:
    $ academy_lib_ensure_event_flags()
    $ academy_lib_migrate_old_saves()

    # --- Already completed ---
    if store.event_flags.get("academy_lib_manual_found"):
        narrator "You already recovered the sealed manual."
        narrator "The library shelves have nothing left to say on the matter — though the dust, as always, has opinions."
        jump academy_lib_quest_return

    # --- Day tracking ---
    $ _today = academy_lib_today()
    $ _same_day = academy_lib_is_same_day()
    $ _in_seal_phase = (academy_lib_stage >= 2) and (not store.event_flags.get("academy_lib_decrypt_done"))

    if _same_day and not _in_seal_phase:
        narrator "The clerk taps a laminated card without looking up. It reads: {i}One consultation per day. No exceptions. No tears.{/i}"
        jump academy_lib_quest_return

    # --- Background ---
    if renpy.loadable("images/buildings/academy.png"):
        $ _lib_bg = "images/buildings/academy.png"
    elif renpy.loadable("images/events/academy_director.png"):
        $ _lib_bg = "images/events/academy_director.png"
    else:
        $ _lib_bg = "images/event_bg.png"

    scene expression _lib_bg

    # --- Post-prologue: offer investigation vs seal attempt ---
    if academy_lib_can_attempt_seal():
        window hide
        menu:
            "Keep investigating.":
                pass
            "Attempt the seal.":
                jump academy_lib_seal_attempt
        window show

    # --- Stage router ---
    if academy_lib_stage == 0:
        jump academy_lib_prologue
    elif academy_lib_stage == 1:
        jump academy_lib_act1
    elif academy_lib_stage >= 2:
        jump academy_lib_act2
    else:
        jump academy_lib_prologue


# ============================================================
#  PROLOGUE — "The Gap"
# ============================================================

label academy_lib_prologue:
    narrator "The academy library smells of dust, varnish, and that particular brand of arrogance."
    narrator "It is the kind that ink develops when it outlives the hands that wrote it."

    narrator "You are not here for the atmosphere. The card catalog lists a circulating codex — a sealed manual of practical manager training."
    narrator "It covers drills, forms, and the exact phrasing senior stewards use."
    narrator "The kind they use when they turn a worker's bad habit into something teachable."

    narrator "The copy should sit on an open shelf."
    narrator "Between {i}Intermediate Ledger Etiquette{/i} and {i}So Your Workers Hate You: A Primer{/i}."

    narrator "It does not."

    narrator "Where the spine should be, there is a gap and a label that matches nothing in the room."
    narrator "Loan status: {i}perpetual{/i}. Possession: {i}ambiguous{/i}."

    narrator "You look at the clerk."
    narrator "The clerk looks at a point slightly above your head, the way people do when they have decided not to be helpful."

    narrator "After what feels like a diplomatic incident conducted entirely in sighs,"
    narrator "they slide a routing slip across the counter and tap it twice."

    narrator "The manual carries an embossed wax seal — six positions around a ring."
    narrator "Without the correct {i}spoken{/i} token, the binder stays shut."
    narrator "No amount of pulling, prying, or creative vocabulary will change this."

    narrator "On the margin of the slip, someone has penciled a single note in cramped handwriting:"
    narrator "{i}\"Position one is M. Confirmed. The rest will follow if you know where to look.\"{/i}"

    narrator "Below it, in different ink — shakier, more desperate:"
    narrator "{i}\"Day five. I have tried STEWARD, OVERSEER, and COMMANDER. None of these have six letters. I may need sleep.\"{/i}"

    narrator "A previous manager, it seems, walked this same path and did not finish it."

    narrator "If brute-forcing the cipher sounds beneath you, a few stationers stock ruled cryptographer's lattices — grids that align seal glyphs to their letters mechanically."
    narrator "The Elite Emporium on the city map sometimes carries them, at a price that could buy patience outright."

    $ store.event_flags["academy_lib_started"] = True
    $ store.event_flags["academy_lib_hint_a"] = True
    $ academy_lib_stage = 1
    $ academy_lib_mark_visit_consumed()
    window hide
    jump academy_lib_quest_return


# ============================================================
#  ACT 1 — "The Paper Trail"
# ============================================================

label academy_lib_act1:
    narrator "You return to the library."
    narrator "The clerk acknowledges your existence with the faintest possible nod — progress, by their standards."

    narrator "The catalog system here was designed by someone who believed finding information should be a character-building exercise."
    narrator "Cross-references lead to cross-references. Footnotes cite other footnotes."
    narrator "It is, in its way, a monument to bureaucratic spite."

    narrator "Still, the seal's pattern has to be documented somewhere. You need the remaining letter positions."

    window hide
    menu:
        "Work the archive desks.":
            jump academy_lib_act1_archive
        "Follow the margin notes.":
            jump academy_lib_act1_margins


label academy_lib_act1_archive:
    window show
    narrator "You spend the morning being sent to the wrong desk. Then the wrong floor."
    narrator "Then back to the first desk, where the same clerk pretends not to recognize you."

    narrator "By afternoon, a tired archivist lets you examine a corner of the seal rubric."
    narrator "The only person in the building who appears to actually {i}like{/i} books."

    narrator "It is written in a hand so precise it could have been typeset."
    narrator "Two more positions, named plainly: {i}the third tooth reads N, the fifth reads G{/i}."

    narrator "Whoever carved this seal wanted competent hands to succeed. Just not quickly."

    jump academy_lib_act1_vowel_clue


label academy_lib_act1_margins:
    window show
    narrator "The previous manager's notes continue in the margins of a routing ledger, growing increasingly unhinged across the pages."

    narrator "{i}\"Asked the archivist directly. She laughed. Actually laughed.\"{/i}"
    narrator "{i}\"Then she said 'third is N, fifth is G' as if that were common knowledge.\"{/i}"
    narrator "{i}\"Perhaps it is. Perhaps I am the only person in this building who doesn't already know.\"{/i}"

    narrator "You copy the positions into your own notes, feeling a strange kinship with someone you have never met and who clearly needed a holiday."

    jump academy_lib_act1_vowel_clue


label academy_lib_act1_vowel_clue:
    narrator "Deeper in the restricted catalog, buried in a memo about non-circulating reserves,"
    narrator "someone has underlined one more detail: the seal's {i}closing{/i} tooth — position six — resolves to E."

    narrator "And a marginal note in different ink adds:"
    narrator "{i}\"Positions two and four carry the same vowel. Not a stutter — a mirror. The house uses it as a signature.\"{/i}"

    narrator "Your working strip now reads: M · {b}?{/b} · N · {b}?{/b} · G · E. Two gaps, and they must match."

    narrator "The question that remains is simple enough: which vowel?"

    $ store.event_flags["academy_lib_hint_b"] = True
    $ store.event_flags["academy_lib_hint_c"] = True

    jump academy_lib_act1_vowel_choice


label academy_lib_act1_vowel_choice:
    window hide

    # Build the menu dynamically based on which wrong answers have been eliminated
    $ _wrong_e = store.event_flags.get("academy_lib_vowel_wrong_e", False)
    $ _wrong_o = store.event_flags.get("academy_lib_vowel_wrong_o", False)

    menu:
        "The vowel is A.":
            jump academy_lib_act1_vowel_correct

        "The vowel is E." if not _wrong_e:
            window show
            narrator "You write it down with confidence. M-E-N-E-G-E. You say it aloud under your breath and it sounds like a sneeze."
            narrator "The catalog confirms nothing. The routing slip's annotations don't match. E sits at position six already — the house mirror wouldn't repeat the closing letter internally."
            narrator "A wasted afternoon, but at least you can cross one option off."
            $ store.event_flags["academy_lib_vowel_wrong_e"] = True
            $ academy_lib_mark_visit_consumed()
            window hide
            jump academy_lib_quest_return

        "The vowel is O." if not _wrong_o:
            window show
            narrator "M-O-N-O-G-E. You write it, stare at it, and realize it sounds like a disease you'd catch from handling old books."
            narrator "The pattern doesn't match any house token in the reference index."
            narrator "The archivist glances at your notes and looks away with what might be pity."
            narrator "Wrong vowel. But one fewer to consider next time."
            $ store.event_flags["academy_lib_vowel_wrong_o"] = True
            $ academy_lib_mark_visit_consumed()
            window hide
            jump academy_lib_quest_return


label academy_lib_act1_vowel_correct:
    window show
    narrator "M-A-N-A-G-E. You write it slowly, and something shifts."
    narrator "Not in the room, but in the way the word sits on the page."
    narrator "It looks {i}right{/i}. It looks like it belongs."

    narrator "You check it against the routing slip annotations."
    narrator "Position one, M. Two, A. Three, N. Four, A. Five, G. Six, E."
    narrator "Every clue you have gathered aligns."

    narrator "In the margin of the ledger you've been following, the previous manager's final note:"
    narrator "{i}\"I never got this far. If you're reading this, good luck with the wax. It doesn't bite, but it doesn't forgive either.\"{/i}"

    narrator "All that remains is the seal itself."

    $ store.event_flags["academy_lib_ready_decrypt"] = True
    $ academy_lib_stage = 2
    $ academy_lib_mark_visit_consumed()
    window hide
    jump academy_lib_quest_return


# ============================================================
#  ACT 2 — "The Seal"
# ============================================================

label academy_lib_seal_attempt:
    # Entry point when player chooses "Attempt the seal" from the recurring menu
    window show

    if academy_lib_has_cipher_lattice():
        narrator "You approach the proving desk with the ruled lattice in hand."
        narrator "The clerk's gaze drops to it, then back to the seal,"
        narrator "with the resigned expression of someone watching a puzzle solve itself."
        narrator "The lattice does not replace the seal's demand — it simply translates it. Six teeth, six letters, one breath."
    else:
        narrator "You steer toward the proving desk before the day's routine can scatter your resolve."
        narrator "The clerk's mouth tightens. The seal sits under the lamp, wax catching the light like something patient."
        narrator "Six letters. One word. No partial credit."

    # Set all hints as known (player is attempting directly)
    $ store.event_flags["academy_lib_started"] = True
    $ store.event_flags["academy_lib_hint_a"] = True

    jump academy_lib_act2_loop


label academy_lib_act2:
    narrator "The proving desk waits for you."
    narrator "The seal sits under a brass lamp, wax softened just enough by the heat to show its fine lines."
    narrator "Six teeth around a ring, each one a position."

    if store.event_flags.get("academy_lib_ready_decrypt"):
        narrator "You know all six letters."
        narrator "The question is no longer {i}what{/i} to say, but whether you can say it correctly."
        narrator "One word, no hesitation, spoken as if you meant it."
    else:
        narrator "You have clues, but not all of them. Still, the seal only cares about the right answer, not how you found it."

    jump academy_lib_act2_loop


label academy_lib_act2_loop:
    # Reset attempt counter if this is a new day
    if not academy_lib_is_same_day():
        $ store.academy_lib_seal_attempts_today = 0
        $ academy_lib_mark_visit_consumed()

    window hide
    menu:
        "Use the lattice." if academy_lib_has_cipher_lattice():
            window show
            narrator "You slide the ruled transparency over the wax ring. The grid aligns each tooth to its letter with mechanical precision — no guesswork, no drama."
            narrator "The house token assembles itself beneath the lattice like a word that was always there."
            narrator "Waiting for someone with the right tool and the good sense to buy it."
            jump academy_lib_seal_success

        "Speak the token.":
            $ _guess = renpy.input("Six letters, one word — speak the house token:", default="", length=16)
            $ _acc, _nudge = academy_lib_cipher_accept(_guess)
            if _acc:
                if _nudge == "manager_not_manage":
                    window show
                    narrator "The wax catches — then resists. Seven letters won't sit on six teeth."
                    narrator "You trim the last letter. The house form is MANAGE, not the longer title. Close enough that the seal forgives the overshoot."
                jump academy_lib_seal_success
            # --- Failure ---
            $ store.academy_lib_seal_attempts_today += 1
            if store.academy_lib_seal_attempts_today == 1:
                window show
                narrator "The wax doesn't reject you dramatically. It simply doesn't open, which is worse."
                narrator "You can try again."
                jump academy_lib_act2_loop
            elif store.academy_lib_seal_attempts_today == 2:
                window show
                narrator "Wrong again."
                narrator "The seal sits there with the serene indifference of something"
                narrator "that has all the time in the world and knows you don't."
                narrator "It occurs to you that the Elite Emporium sells cryptographer's lattices. Ruled grids that do this sort of work for people who value their afternoons."
                jump academy_lib_act2_loop
            else:
                window show
                narrator "The clerk reaches across the desk and slides the seal away from you with one finger."
                narrator "They do not speak. They do not need to."
                narrator "A small card appears where the seal was. It reads: {i}\"Tomorrow.\"{/i}"
                narrator "You have been dismissed by a piece of stationery."
                window hide
                jump academy_lib_quest_return

        "Step back.":
            window show
            narrator "You leave the seal for another day. It will still be here. It has nowhere else to be."
            window hide
            jump academy_lib_quest_return


# ============================================================
#  SEAL SUCCESS + EPILOGUE
# ============================================================

label academy_lib_seal_success:
    narrator "The fit is correct."
    narrator "Something inside the binder clicks — not loudly, not dramatically,"
    narrator "but with the quiet certainty of a lock that has been waiting for the right word."

    narrator "The latch yields. Inside: not spells, not secrets — {i}protocol{/i}."
    narrator "Pages dense with practical instruction, margins crowded with the kind of knowledge"
    narrator "that senior house managers swear they {i}just know{/i}, as if competence were atmospheric and not learned."

    $ store.event_flags["academy_lib_decrypt_done"] = True
    $ academy_lib_stage = 3
    jump academy_lib_epilogue


label academy_lib_epilogue:
    narrator "You slip the codex into your coat like contraband — which, in a sense, it is."
    narrator "Practical knowledge has always been the most closely guarded kind."

    narrator "On the last page, tucked into the binding, a final note from your predecessor:"
    narrator "{i}\"If you're reading this, you're better than me. Or richer. Either way, do something useful with it.\"{/i}"

    narrator "From now on, when you sit down with your workers, you can structure real training sessions."
    narrator "With the confidence of someone who finally owns the terminology and isn't afraid to use it."

    $ store.event_flags["academy_lib_manual_found"] = True
    $ persistent.academy_lib_quest_completed_once = True
    $ academy_lib_mark_visit_consumed()
    $ renpy.notify("Manager training interactions unlocked (worker interactions menu).")
    window hide
    jump academy_lib_quest_return
