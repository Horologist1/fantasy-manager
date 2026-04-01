# Training voice & narrative spine (English in-game copy)

Spanish brainstorming is fine in design notes; **shipped strings** live in `game/data/interactions/interactions_training.json` (regenerated from `tools/apply_crude_training_copy.py` unless you hand-edit and skip the tool).

## Shared spine (every training interaction)

Each interaction should hit the same **beats** so the flow feels like one game, not random blurbs.

1. **Approach / setup** — You seek out `{name}` for a **`{skill}`** session (use `{skill}` in copy where it helps; intros already substitute it). You name what “done” looks like for *this* slot, in concrete verbs.
2. **First refusal narration** (`first_refusal`) — Readable **stall**: shame, limits, exhaustion, disbelief that it’s necessary, or body frozen. Conversation lands on “not tonight” / “another day” without poetry that hides the no.
3. **Player prompt** — Menu title from `_training_flow_copy.training_flow_ui.branch_prompt` (supports `{name}`, `{focus}`, `{skill}`, pronouns). Default tone: *`{name}` doesn’t want to train today — what do you do?* (`command_retry`, `leave_them_be`, and `show_disappointment` can use the same tokens if you want them personalized.)
4. **Second refusal** (`second_refusal`) — Harder no: hedging breaks, **disobedience** is obvious (won’t strip, won’t get into position, won’t repeat the order).
5. **Success without insist** (`trained`) — Cooperation: the work actually starts; corrections and rewards match the skill (see NSFW vs SFW).
6. **Success after insist** (`trained_after_insist`) — Tension first, then bodies comply; same teaching frame but rougher emotionally.
7. **Leave 1 / Leave 2** (`leave_be_first`, `leave_be_second`) — Between irritation and understanding: consolation, no escalation; second leave is a clean exit without turning it into a feud.
8. **Punish** (`punished`) — Authority forced; a concrete consequence; consent or submission to discipline; **per interaction id** in JSON. Optional: `punished` as a **list** of strings — the engine picks one at random.

## NSFW vs SFW framing

| Track | Skills / interactions | Setting & body | Clients / money |
|--------|------------------------|----------------|-----------------|
| **NSFW** | Hand, Oral, Sex, BDSM, Special, Striptease, Homo FF/MM | Skin, arousal, explicit acts as sold | Rate card, bookings, johns, establishment rules |
| **SFW — Service** | `training_sfw_service` | Floor distance, trays, timing, measurable tasks | Guests when it fits; focus on ops, not metaphor |
| **SFW — Agility** | `training_sfw_agility` | Aerobic / conditioning, laps, recovery | No sexual frame; exhaustion and “not convinced it’s worth it” refusals |
| **SFW — Charm** | `training_sfw_charm` | Desk drills: memory, reading cues, rehearsed lines | May de-emphasize “clients”; stress reflex, recall, wit as craft |

Do **not** force penetrative or strip-tease language into SFW entries.

## Style (tone)

- **Diegetic first:** setup and refusals read like a scene (approach, what you expect, doubt, conversation, "another day"), not like a glossary entry.
- **Do not use `({focus})` in `training_intro_sequences`.** `{focus}` is usually the card `name` (e.g. `Training: Sex`) and reads like UI pasted into fiction. Prefer `{skill}`, `{name}`, pronouns, or plain prose ("The work you named...", "You were explicit...").
- **`{name}` / pronouns** stay: one JSON row still covers many workers.
- **NSFW** can stay blunt and client/ledger aware; avoid repeating the same "definition" sentence shape in every skill.

## Branch CG (refused / punished)

- **`training_branch_images`**: full filename stem per branch (`refused`, `punished`) under `images/workers/<worker folder>/`. Lookup uses `get_image_matches_flexible` (allowed extensions + numbered variants like `Name (1).png`).
- **Fallback** (no `_lord` / `_lady` / gender suffixes on these steps): JSON stem → `Training_Refused_<skill>` or `Training_Punished_<skill>` (`training_skill` with spaces as `_`) → `Training_Refused` / `Training_Punished` → `obedience` → worker profile.


## Ren’Py & data rules

- **`training_intro_sequences` pagination:** Regenerating from `tools/apply_crude_training_copy.py`, `intro()` runs `_split_training_intro_pages` (~140 chars per page) so each `training_branch_narration` click fits the normal say textbox—no scroll or taller window. Hand-edit JSON if you need exact break points.
- Intros use `{name}`, `{skill}`, `{subj}`, etc.; `{focus}` is mainly for shared **menu** copy (`training_flow_ui`), not intros (see **Style (tone)**). Substitution runs in Python (`training_substitute_intro_tokens`) before `training_branch_narration` (`!q` on the screen avoids accidental Ren’Py `[` / `{` parsing).
- Prefer **dict-like** checks on game data (`hasattr(x, "get")`), not `isinstance(..., dict)` — see `docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md`.

## Regenerating JSON

```bash
python tools/apply_crude_training_copy.py
```

The row `id: "_training_flow_copy"` is preserved by the script; edit shared menu/stat strings there.
