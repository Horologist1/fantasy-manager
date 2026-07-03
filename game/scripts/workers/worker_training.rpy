# worker_training.rpy — Manager training interactions (multi-step rolls + menus)

# Full-screen black under all training UI: shown once per flow, hidden in training_restore_ui_after_result.
# Nothing "replaces" it between narration/menu/result — new screens only stack above (no Fade on call screen).
screen training_cutscene_backdrop():
    zorder 90
    modal False
    $ _bbw, _bbh = config.screen_width, config.screen_height
    fixed:
        xfill True
        yfill True
        add Solid("#000000"):
            xsize _bbw
            ysize _bbh

# True only while a training flow is inside `call screen interaction_result` (reliable vs screen param on re-run).
default _training_interaction_result_active = False

init python:
    import os
    import re

    TRAINING_RESULT_ALIASES = {
        "trained": ("trained", "1", "Trained"),
        "leave_be_first": ("leave_be_first", "2", "Leavebe1", "leavebe1"),
        "trained_after_insist": ("trained_after_insist", "3", "Trained2", "trained2"),
        "leave_be_second": ("leave_be_second", "4", "Leavebe2", "leavebe2"),
        "punished": ("punished", "5", "Punished"),
        "learn_fail": ("learn_fail", "learn_fail", "6"),
    }

    TRAINING_TEXT_KEYS = (
        "trained",
        "leave_be_first",
        "leave_be_second",
        "punished",
        "trained_after_insist",
        "learn_fail",
    )

    # Click-through lines (training_branch_narration). Resolution order:
    # 1) interaction["training_intro_sequences"][key]  (list or string)
    # 2) interaction["training_texts"]["intro_*"]     (TRAINING_INTRO_FLAT_KEYS values)
    # No Python prose fallback: copy lives in JSON; empty list if missing.
    TRAINING_INTRO_FLAT_KEYS = {
        "first_refusal": "intro_first_refusal",
        "second_refusal": "intro_second_refusal",
        "learn_fail": "intro_learn_fail",
        "trained": "intro_trained",
        "punished": "intro_punished",
        "insist_accepted": "intro_insist_accepted",
    }

    TRAINING_FLOW_COPY_ID = "_training_flow_copy"
    _TRAINING_META_FLOW_UNSET = "_training_meta_flow_unset"

    # Set from JSON (`training_flow_ui.branch_prompt`) when a training flow starts.
    store.training_branch_choice_prompt = ""

    def training_resolve_worker(worker):
        """Canonical worker dict from store.workers by name (RevertableDict-safe)."""
        if not worker or not hasattr(worker, "get"):
            return None
        name = worker.get("name")
        if not name:
            return None
        if hasattr(store, "workers"):
            for w in store.workers:
                if hasattr(w, "get") and w.get("name") == name:
                    return w
        return worker

    def is_training_interaction(interaction):
        if not interaction or not hasattr(interaction, "get"):
            return False
        cats = interaction.get("categories") or []
        if "Training" not in cats:
            return False
        sk = interaction.get("training_skill")
        return bool(sk)

    def training_infer_pair_code(interaction):
        """
        Player/worker gender pair for art names: F=Female (Lady), M=Male (Lord).
        Returns 'FF', 'MM', 'MF', 'FM', or None.
        """
        if not interaction or not hasattr(interaction, "get"):
            return None
        explicit = interaction.get("training_pair")
        if explicit:
            s = str(explicit).strip().upper()
            if s in ("FF", "MM", "MF", "FM"):
                return s
        gf = interaction.get("gender_filter")
        wg = interaction.get("worker_gender")
        if gf is None or wg is None:
            return None
        pg = "M" if str(gf).lower() == "male" else ("F" if str(gf).lower() == "female" else None)
        wk = "M" if str(wg).lower() == "male" else ("F" if str(wg).lower() == "female" else None)
        if pg and wk:
            return pg + wk
        return None

    def training_interaction_primary_candidate_bases(worker, interaction):
        """
        Strict training CG stem(s) from JSON `image` only (matched by get_training_primary_image_matches).
        Roster skill art (sex, oral, … in worker folder — same as get_worker_image(worker, skill)) is chained
        in get_interaction_image after this list fails, not as a filename stem here.
        """
        ib = (interaction.get("image") or "").strip() if hasattr(interaction, "get") else ""
        if ib:
            return [ib]
        return []

    TRAINING_PRIMARY_MEDIA_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".webm", ".mp4")

    def get_training_primary_image_matches(base_folder, image_name, exclude_failure=False):
        """
        Files for JSON-declared training primary art: exact stem (any listed extension) or stem + ' (digits)' only
        (e.g. Foo.png, Foo (1).jpg). No other stem variants.
        """
        image_base = os.path.splitext(image_name)[0]
        ib_low = image_base.lower()
        variant_re = re.compile(r"^%s \(\d+\)$" % re.escape(ib_low))
        matches = []
        _gcfl = getattr(store, "get_cached_file_list", None)
        _all_files = _gcfl() if callable(_gcfl) else renpy.list_files()
        for f in _all_files:
            if not f.startswith(base_folder):
                continue
            filename = os.path.basename(f)
            file_base = os.path.splitext(filename)[0]
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in TRAINING_PRIMARY_MEDIA_EXTS:
                continue
            fb_low = file_base.lower()
            if fb_low != ib_low and not variant_re.match(fb_low):
                continue
            if exclude_failure and "failure" in filename.lower():
                continue
            matches.append(f)
        return matches

    def training_subject_pronoun(worker):
        g = (worker.get("gender") or "").lower() if hasattr(worker, "get") else ""
        if g == "male":
            return "He"
        return "She"

    TRAINING_RESULT_DEFAULTS = {
        "leave_be_first": {
            "skill_uses": 0,
            "effect": {"joy": 3},
        },
        "leave_be_second": {"skill_uses": 0, "effect": {}},
        "punished": {"skill_uses": 0, "effect": {"rebelliousness": -3, "joy": -5}},
        "trained": {"skill_uses": 1, "effect": {}},
        "trained_after_insist": {"skill_uses": 1, "effect": {}},
        "learn_fail": {"skill_uses": 0, "effect": {}},
    }

    TRAINING_PREVIEW_STAT_ORDER = (
        "money",
        "energy",
        "health",
        "joy",
        "romance",
        "relationship",
        "rebelliousness",
        "libido",
    )

    TRAINING_PREVIEW_STAT_LABELS = {
        "joy": "Joy",
        "rebelliousness": "Rebelliousness",
        "romance": "Romance",
        "relationship": "Relationship",
        "energy": "Energy",
        "health": "Health",
        "libido": "Libido",
        "money": "Money",
    }

    def training_meta_flow_entry():
        """Shared training UI strings: row `id` == TRAINING_FLOW_COPY_ID in interactions_training.json (dict-like)."""
        cached = getattr(store, "_training_meta_flow_entry", _TRAINING_META_FLOW_UNSET)
        if cached is not _TRAINING_META_FLOW_UNSET:
            return cached
        found = None
        for inter in load_interactions():
            if hasattr(inter, "get") and inter.get("id") == TRAINING_FLOW_COPY_ID:
                found = inter
                break
        store._training_meta_flow_entry = found
        return found

    def training_flow_ui_str(key, default=""):
        meta = training_meta_flow_entry()
        if not meta or not hasattr(meta, "get"):
            return default
        u = meta.get("training_flow_ui")
        if not u or not hasattr(u, "get"):
            return default
        v = u.get(key)
        if v is None:
            return default
        s = str(v).strip()
        return s if s else default

    def training_flow_ui_substitute(key, worker, interaction, default=""):
        """Shared menu copy from JSON with {name}/{skill}/{focus}/pronoun tokens filled."""
        raw = training_flow_ui_str(key, default)
        if not raw:
            return default
        w = training_resolve_worker(worker) if worker else None
        if w and interaction:
            return training_substitute_intro_tokens(raw, w, interaction)
        return raw

    def training_coerce_training_text_value(val):
        """Single training_texts value: string, or list of strings (pick one at random)."""
        if val is None:
            return None
        if isinstance(val, str):
            s = val.strip()
            return s if s else None
        if hasattr(val, "__iter__") and not isinstance(val, (str, bytes)):
            opts = []
            for x in val:
                if x is None:
                    continue
                s = str(x).strip()
                if s:
                    opts.append(s)
            if not opts:
                return None
            return renpy.random.choice(opts)
        s = str(val).strip()
        return s if s else None

    def training_stat_preview_config():
        meta = training_meta_flow_entry()
        if not meta or not hasattr(meta, "get"):
            return None
        c = meta.get("training_stat_preview")
        if c and hasattr(c, "get"):
            return c
        return None

    def training_preview_stat_label(stat):
        cfg = training_stat_preview_config()
        if cfg and hasattr(cfg, "get"):
            sl = cfg.get("stat_labels")
            if sl and hasattr(sl, "get"):
                lab = sl.get(stat)
                if lab is not None and str(lab).strip():
                    return str(lab)
        return TRAINING_PREVIEW_STAT_LABELS.get(stat, stat.replace("_", " ").title())

    def training_preview_fmt(key, default):
        cfg = training_stat_preview_config()
        if cfg and hasattr(cfg, "get"):
            v = cfg.get(key)
            if v is not None and str(v).strip():
                return str(v)
        return default

    def training_merge_static_effects(*dicts):
        """Sum numeric stat deltas from effect dicts (preview only; mirrors keys training_apply_effect_dict uses)."""
        out = {}
        for d in dicts:
            if not d or not hasattr(d, "get"):
                continue
            for k, v in d.items():
                if k in ("flags", "add_trait", "remove_trait", "trait_chance", "trait_remove_chance"):
                    continue
                try:
                    delta = int(v)
                except (TypeError, ValueError):
                    continue
                if delta == 0:
                    continue
                out[k] = out.get(k, 0) + delta
        return out

    def training_insist_effect_dict_only(interaction, branch):
        """Stat deltas from training_insist_effects[insist|command] (no mutation). Mirrors training_apply_insist_cost."""
        if not interaction or not hasattr(interaction, "get"):
            return {}
        b = (branch or "").strip().lower()
        if b not in ("insist", "command"):
            return {}
        ie = interaction.get("training_insist_effects")
        if ie and hasattr(ie, "get"):
            sub = ie.get(b) or ie.get(str(b))
            if not sub and b == "command":
                sub = ie.get("compliance")
            if sub and hasattr(sub, "get"):
                raw = sub.get("effect")
                d = raw if raw is not None else sub
                if hasattr(d, "get"):
                    return training_merge_static_effects(d)
        return {"rebelliousness": 1}

    def training_trait_chance_preview(entries):
        if not entries:
            return ""
        pair_fmt = training_preview_fmt("fmt_trait_chance", "%s (%d%%)")
        prefix = training_preview_fmt("prefix_chance", "Chance: ")
        bits = []
        for e in entries:
            if not e or not hasattr(e, "get"):
                continue
            name = e.get("trait") or e.get("name")
            try:
                p = int(e.get("chance_percent", e.get("percent", 0)) or 0)
            except (TypeError, ValueError):
                p = 0
            if name and p > 0:
                bits.append(pair_fmt % (name, p))
        if not bits:
            return ""
        return prefix + ", ".join(bits)

    def training_trait_remove_chance_preview(entries):
        if not entries:
            return ""
        pair_fmt = training_preview_fmt("fmt_trait_remove_chance", "%s (%d%%)")
        prefix = training_preview_fmt("prefix_remove_chance", "Remove chance: ")
        bits = []
        for e in entries:
            if not e or not hasattr(e, "get"):
                continue
            name = e.get("trait") or e.get("name")
            try:
                p = int(e.get("chance_percent", e.get("percent", 0)) or 0)
            except (TypeError, ValueError):
                p = 0
            if name and p > 0:
                bits.append(pair_fmt % (name, p))
        if not bits:
            return ""
        return prefix + ", ".join(bits)

    def training_format_merged_effects(merged, skill_uses=0, skill_name=None, trait_chance_list=None, trait_remove_chance_list=None):
        """
        Event-style suffix: (Gain: +3 Joy; Lose: 1 Romance; Chance: Masochist (1%))
        Format strings and stat labels come from interactions_training.json (`_training_flow_copy.training_stat_preview`).
        """
        fmt_gain = training_preview_fmt("fmt_gain_stat", "Gain: +%d %s")
        fmt_lose = training_preview_fmt("fmt_lose_stat", "Lose: %d %s")
        fmt_gmoney = training_preview_fmt("fmt_gain_money", "Gain: +$%d")
        fmt_cmoney = training_preview_fmt("fmt_cost_money", "Cost: $%d")
        fmt_uses = training_preview_fmt("fmt_training_uses", "+%d %s training")
        merged = merged or {}
        parts = []
        rest = dict(merged)
        for stat in TRAINING_PREVIEW_STAT_ORDER:
            if stat not in rest:
                continue
            dv = int(rest.pop(stat) or 0)
            if dv == 0:
                continue
            lab = training_preview_stat_label(stat)
            if stat == "money":
                if dv > 0:
                    parts.append(fmt_gmoney % dv)
                else:
                    parts.append(fmt_cmoney % abs(dv))
            elif dv > 0:
                parts.append(fmt_gain % (dv, lab))
            else:
                parts.append(fmt_lose % (abs(dv), lab))
        for stat in sorted(rest.keys()):
            dv = int(rest.get(stat) or 0)
            if dv == 0:
                continue
            lab = training_preview_stat_label(stat)
            if dv > 0:
                parts.append(fmt_gain % (dv, lab))
            else:
                parts.append(fmt_lose % (abs(dv), lab))
        try:
            su = int(skill_uses or 0)
        except (TypeError, ValueError):
            su = 0
        if su > 0 and skill_name:
            parts.append(fmt_uses % (su, skill_name))
        if trait_chance_list:
            th = training_trait_chance_preview(trait_chance_list)
            if th:
                parts.append(th)
        if trait_remove_chance_list:
            trh = training_trait_remove_chance_preview(trait_remove_chance_list)
            if trh:
                parts.append(trh)
        if not parts:
            return ""
        return " (Outcome: " + "; ".join(parts) + ")"

    def training_try_again_menu_caption(worker, interaction):
        """First refusal: insist/command path; same effect suffix pattern as Leave them be."""
        eff = training_insist_effect_dict_only(interaction, "command")
        prefix = training_flow_ui_substitute("command_retry", worker, interaction)
        return prefix + training_format_merged_effects(eff)

    def training_narrative_subject(worker):
        """(display_name, plural_verb): 'They' + True, or worker name + False for he/she/they name."""
        if worker and hasattr(worker, "get"):
            n = (worker.get("name") or "").strip()
            if n:
                return n, False
        return "They", True

    def training_narrative_skill_focus(interaction):
        if not interaction or not hasattr(interaction, "get"):
            return "this session"
        lab = (interaction.get("name") or "").strip()
        if lab:
            return lab
        sk = interaction.get("training_skill")
        if sk:
            return "%s training" % (sk,)
        return "this session"

    def training_coerce_intro_sequence(val):
        """Normalize JSON intro value to a list of non-empty strings, or None."""
        if val is None:
            return None
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return None
            parts = [p.strip() for p in s.split("\n\n") if p.strip()]
            if len(parts) > 1:
                return parts
            return [s]
        # list-like (plain list or Ren'Py RevertableList): never isinstance(..., list) for game data (see docs biblia §1).
        if hasattr(val, "__iter__") and not isinstance(val, (str, bytes)):
            lines = []
            for x in val:
                s = str(x).strip() if x is not None else ""
                if s:
                    lines.append(s)
            return lines or None
        return None

    def training_get_raw_intro_sequence(interaction, key):
        """Return list of template strings for key, or None if absent."""
        if not interaction or not hasattr(interaction, "get"):
            return None
        if key not in TRAINING_INTRO_FLAT_KEYS:
            return None
        seqs = interaction.get("training_intro_sequences")
        if seqs is not None and hasattr(seqs, "get"):
            chunk = seqs.get(key)
            if chunk is not None:
                got = training_coerce_intro_sequence(chunk)
                if got:
                    return got
        tx = interaction.get("training_texts")
        flat = TRAINING_INTRO_FLAT_KEYS.get(key)
        if tx is not None and hasattr(tx, "get") and flat:
            chunk = tx.get(flat)
            if chunk is not None:
                got = training_coerce_intro_sequence(chunk)
                if got:
                    return got
        return None

    def training_worker_pronoun_pack(worker):
        """(subj, Subj, obj, poss, refl) e.g. she, She, her, her, herself — for intro JSON."""
        g = (worker.get("gender") or "").lower() if worker and hasattr(worker, "get") else ""
        if g == "male":
            return ("he", "He", "him", "his", "himself")
        if g == "female":
            return ("she", "She", "her", "her", "herself")
        return ("they", "They", "them", "their", "themselves")

    def training_substitute_intro_tokens(text, worker, interaction):
        """Placeholders: {name}/{worker}, {focus}, {skill}, {pronoun}, {listen}, {try}, {follow}, {apply}, {subj}/{Subj}/{obj}/{poss}/{refl}."""
        if not text:
            return ""
        nm, pl = training_narrative_subject(worker)
        focus = training_narrative_skill_focus(interaction)
        sk = ""
        if interaction and hasattr(interaction, "get"):
            sk = str(interaction.get("training_skill") or "").strip()
        listen = "listen" if pl else "listens"
        try_v = "try" if pl else "tries"
        follow = "follow" if pl else "follows"
        apply_v = "apply" if pl else "applies"
        subj, Subj, obj, poss, refl = training_worker_pronoun_pack(worker)
        t = str(text)
        t = t.replace("{name}", nm)
        t = t.replace("{worker}", nm)
        t = t.replace("{focus}", focus)
        t = t.replace("{skill}", sk)
        t = t.replace("{pronoun}", training_subject_pronoun(worker))
        t = t.replace("{listen}", listen)
        t = t.replace("{try}", try_v)
        t = t.replace("{follow}", follow)
        t = t.replace("{apply}", apply_v)
        t = t.replace("{subj}", subj)
        t = t.replace("{Subj}", Subj)
        t = t.replace("{obj}", obj)
        t = t.replace("{poss}", poss)
        t = t.replace("{refl}", refl)
        return t

    def training_resolve_intro_lines(worker, interaction, key):
        """Resolve intro lines from JSON and substitute {name}/{focus}/pronoun tokens."""
        raw = training_get_raw_intro_sequence(interaction, key)
        if not raw:
            return []
        return [training_substitute_intro_tokens(s, worker, interaction) for s in raw]

    def training_branch_menu_intro_first_refusal_messages(worker, interaction):
        """Paragraph chunks before first refusal menu (JSON only)."""
        return training_resolve_intro_lines(worker, interaction, "first_refusal")

    def training_branch_menu_intro_second_refusal_messages(worker, interaction):
        return training_resolve_intro_lines(worker, interaction, "second_refusal")

    def training_learn_fail_intro_messages(worker, interaction):
        """Click-through lines before the learn_fail result (JSON only)."""
        return training_resolve_intro_lines(worker, interaction, "learn_fail")

    def training_trained_intro_messages(worker, interaction):
        """Optional preamble before success interaction_result; empty unless JSON provides intro_trained / sequences."""
        return training_resolve_intro_lines(worker, interaction, "trained")

    def training_punished_intro_messages(worker, interaction):
        """Click-through narration before the punished result screen (JSON only)."""
        return training_resolve_intro_lines(worker, interaction, "punished")

    def training_insist_accepted_intro_messages(worker, interaction):
        """Click-through transition when worker yields after insist (JSON only)."""
        return training_resolve_intro_lines(worker, interaction, "insist_accepted")

    def training_trait_chance_entry_name(entry):
        if not entry or not hasattr(entry, "get"):
            return None
        return entry.get("trait") or entry.get("name")

    def training_coerce_trait_roll_list(raw):
        """Coerce trait_chance/trait_remove_chance payload to list of dict-like entries."""
        if raw is None:
            return []
        if hasattr(raw, "get") and callable(getattr(raw, "get", None)):
            return [raw]
        if isinstance(raw, (str, bytes)):
            return []
        if hasattr(raw, "__iter__"):
            return list(raw)
        return []

    # training_results[...].trait_chance: list of { trait|name, chance_percent|percent, optional duration }.
    # If "duration" is omitted, uses the trait definition's "duration" (days; 0 = permanent). If present, overrides the def.

    def training_try_trait_chances(worker, entries, stat_changes, granted_list_key="traits_from_training", log_prefix="Training"):
        """Roll chance_percent for each entry; grant trait if not already present and rules allow."""
        worker = training_resolve_worker(worker)
        if not worker or not hasattr(worker, "get") or not entries:
            return
        if not hasattr(store, "add_trait_with_duration"):
            return
        get_tdef = getattr(store, "get_trait_definition", None)
        for entry in entries:
            name = training_trait_chance_entry_name(entry)
            if not name:
                continue
            try:
                pct = int(entry.get("chance_percent", entry.get("percent", 0)) or 0)
            except (TypeError, ValueError):
                pct = 0
            pct = min(100, max(0, pct))
            if pct <= 0:
                continue
            if renpy.random.randint(1, 100) > pct:
                continue
            cur = worker.get("traits") or []
            if name in cur:
                continue
            tdef = None
            if callable(get_tdef):
                try:
                    tdef = get_tdef(name)
                except Exception:
                    tdef = None
            if tdef and tdef.get("nsfw") and not getattr(persistent, "nsfw_enabled", False):
                continue
            if hasattr(entry, "__contains__") and "duration" in entry:
                try:
                    dur = int(entry.get("duration") or 0)
                except (TypeError, ValueError):
                    dur = 0
            else:
                try:
                    dur = int((tdef.get("duration", 0) if tdef else 0) or 0)
                except (TypeError, ValueError):
                    dur = 0
            store.add_trait_with_duration(worker, name, dur)
            if name not in (worker.get("traits") or []):
                renpy.log(
                    "%s: trait_chance roll hit for '%s' on %s but trait was not added (missing def, gender, etc.)"
                    % (log_prefix, name, worker.get("name", "?"))
                )
                continue
            stat_changes.setdefault(granted_list_key, []).append(name)
            if hasattr(store, "update_skill_levels"):
                store.update_skill_levels()
            renpy.log("%s: trait_chance granted '%s' to %s (duration=%s)" % (log_prefix, name, worker.get("name", "?"), dur))

    def _worker_has_trait_named(worker, name):
        """True if worker traits contains name (case-insensitive string match)."""
        if not worker or not hasattr(worker, "get") or not name:
            return False
        traits = worker.get("traits") or []
        if not traits:
            return False
        if name in traits:
            return True
        nl = str(name).lower()
        for t in traits:
            if isinstance(t, str) and t.lower() == nl:
                return True
        return False

    # trait_remove_chance: list of { trait|name, chance_percent|percent } — roll then remove if present.
    def training_try_trait_remove_chances(worker, entries, stat_changes, removed_list_key="traits_removed_by_chance", log_prefix="Training"):
        """Roll chance_percent for each entry; remove trait if worker currently has it."""
        worker = training_resolve_worker(worker)
        if not worker or not hasattr(worker, "get") or not entries:
            return
        rm = getattr(store, "remove_trait_safe", None)
        if not callable(rm):
            return
        for entry in entries:
            name = training_trait_chance_entry_name(entry)
            if not name:
                continue
            try:
                pct = int(entry.get("chance_percent", entry.get("percent", 0)) or 0)
            except (TypeError, ValueError):
                pct = 0
            pct = min(100, max(0, pct))
            if pct <= 0:
                continue
            if renpy.random.randint(1, 100) > pct:
                continue
            if not _worker_has_trait_named(worker, name):
                continue
            rm(worker, name)
            if _worker_has_trait_named(worker, name):
                renpy.log(
                    "%s: trait_remove_chance roll hit for '%s' on %s but trait was not removed"
                    % (log_prefix, name, worker.get("name", "?"))
                )
                continue
            stat_changes.setdefault(removed_list_key, []).append(name)
            if hasattr(store, "update_skill_levels"):
                store.update_skill_levels()
            renpy.log("%s: trait_remove_chance removed '%s' from %s" % (log_prefix, name, worker.get("name", "?")))

    def training_get_result_block(interaction, logical_key):
        """Resolve training_results entry by logical name or numeric/string aliases."""
        if not interaction or not hasattr(interaction, "get"):
            return {}
        tr = interaction.get("training_results")
        if not tr or not hasattr(tr, "get"):
            tr = {}
        for alias in TRAINING_RESULT_ALIASES.get(logical_key, (logical_key,)):
            if alias in tr and tr.get(alias) is not None:
                block = tr.get(alias)
                return block if hasattr(block, "get") else {}
        return dict(TRAINING_RESULT_DEFAULTS.get(logical_key, {}))

    def training_get_text(interaction, logical_key, default=""):
        if not interaction or not hasattr(interaction, "get"):
            return default
        tx = interaction.get("training_texts")
        if tx and hasattr(tx, "get") and tx.get(logical_key) is not None:
            picked = training_coerce_training_text_value(tx.get(logical_key))
            if picked:
                return picked
        flat = interaction.get("training_text_" + logical_key)
        if flat is not None:
            picked = training_coerce_training_text_value(flat)
            if picked:
                return picked
        return default

    TRAINING_OUTCOME_DEFAULT_UI_KEYS = {
        "leave_be_first": "default_leave_be_first",
        "leave_be_second": "default_leave_be_second",
        "punished": "default_punished",
        "learn_fail": "default_learn_fail",
        "trained": "default_trained",
        "trained_after_insist": "default_trained_after_insist",
    }

    def training_get_outcome_text(interaction, logical_key, worker=None):
        """Per-interaction training_texts first; then shared defaults from `_training_flow_copy` in JSON. Substitutes tokens when worker passed."""
        t = training_get_text(interaction, logical_key, "")
        if not t or not str(t).strip():
            dk = TRAINING_OUTCOME_DEFAULT_UI_KEYS.get(logical_key)
            t = training_flow_ui_str(dk) if dk else ""
        if not t:
            return ""
        w = training_resolve_worker(worker) if worker else None
        if w and interaction:
            return training_substitute_intro_tokens(str(t), w, interaction)
        return str(t)

    def training_resolved_training_description(worker, interaction):
        """interaction.description with {name}/{skill}/… tokens filled (category cards, results)."""
        if not interaction or not hasattr(interaction, "get"):
            return ""
        d = interaction.get("description")
        if not d:
            return ""
        w = training_resolve_worker(worker) if worker else None
        if not w:
            return str(d)
        return training_substitute_intro_tokens(str(d), w, interaction)

    def training_apply_effect_dict(worker, effects, stat_changes):
        """Apply outcome effect dict (joy, romance, relationship, rebelliousness, energy, health, libido, money)."""
        if not effects or not hasattr(effects, "get"):
            return
        for stat, change in effects.items():
            if stat in ("flags", "add_trait", "remove_trait", "trait_chance", "trait_remove_chance"):
                continue
            if change == 0:
                continue
            try:
                delta = int(change)
            except (TypeError, ValueError):
                continue
            if stat == "money":
                store.money = int(getattr(store, "money", 0) or 0) + delta
                stat_changes["money"] = stat_changes.get("money", 0) + delta
                continue
            if stat in ("rebelliousness", "joy", "romance", "relationship") and hasattr(store, "apply_attribute_change"):
                store.apply_attribute_change(worker, stat, delta)
                stat_changes[stat] = stat_changes.get(stat, 0) + delta
                continue
            if stat == "energy":
                old = int(worker.get("energy", 0) or 0)
                try:
                    mx_e = int(calculate_max_energy(worker))
                except Exception:
                    mx_e = 100
                worker["energy"] = max(0, min(mx_e, old + delta))
                stat_changes["energy"] = stat_changes.get("energy", 0) + (worker["energy"] - old)
                continue
            if stat == "health":
                oldh = int(worker.get("health", 0) or 0)
                try:
                    mx_h = int(calculate_max_health(worker))
                except Exception:
                    mx_h = 100
                worker["health"] = max(0, min(mx_h, oldh + delta))
                stat_changes["health"] = stat_changes.get("health", 0) + (worker["health"] - oldh)
                continue
            if stat == "libido" and getattr(persistent, "nsfw_enabled", False):
                oldl = int(worker.get("libido", 0) or 0)
                try:
                    mx = int(get_max_libido(worker))
                except Exception:
                    mx = 20
                worker["libido"] = max(0, min(mx, oldl + delta))
                stat_changes["libido"] = stat_changes.get("libido", 0) + (worker["libido"] - oldl)

    def training_add_skill_uses(worker, skill_name, amount):
        if not worker or not skill_name or amount <= 0:
            return
        worker.setdefault("skill_uses", {})
        try:
            cur = int(worker["skill_uses"].get(skill_name, 0) or 0)
        except (TypeError, ValueError):
            cur = 0
        worker["skill_uses"][skill_name] = cur + int(amount)
        # Only this worker gained uses; a full-roster pass here was pure waste.
        if hasattr(store, "update_skill_levels_for_worker"):
            store.update_skill_levels_for_worker(worker)
        elif hasattr(store, "update_skill_levels"):
            store.update_skill_levels()

    def training_apply_outcome(worker, interaction, logical_key, skill_name=None):
        """
        Apply training_results[logical_key]: skill_uses on interaction.training_skill (usually +1 on trained paths).
        Only block["effect"] is applied (per-entry JSON; no effect_by_winner merge).
        learn_fail: no stat effects or trait_chance (failed learning roll has no consequences).
        Returns stat_changes dict for UI.
        """
        stat_changes = {}
        block = training_get_result_block(interaction, logical_key)
        if logical_key == "learn_fail":
            block = dict(block) if hasattr(block, "get") else {}
            # Keep JSON-defined effects (energy cost, etc.) — only zero trait rolls
            block["trait_chance"] = []
            block["trait_remove_chance"] = []
        sk = skill_name or interaction.get("training_skill")
        try:
            uses = int(block.get("skill_uses", 0) or 0)
        except (TypeError, ValueError):
            uses = 0
        if uses > 0 and sk:
            training_add_skill_uses(worker, sk, uses)
            stat_changes["skill_uses_" + str(sk)] = uses
        training_apply_effect_dict(worker, block.get("effect") or {}, stat_changes)
        _tc = block.get("trait_chance") if block and hasattr(block, "get") else None
        training_try_trait_chances(worker, training_coerce_trait_roll_list(_tc), stat_changes)
        _trc = block.get("trait_remove_chance") if block and hasattr(block, "get") else None
        training_try_trait_remove_chances(worker, training_coerce_trait_roll_list(_trc), stat_changes)
        return stat_changes

    def training_apply_insist_cost(worker, interaction, branch, stat_changes):
        """Apply training_insist_effects for branch insist|command; default +1 rebelliousness if unset."""
        b = (branch or "").strip().lower()
        ie = interaction.get("training_insist_effects") if hasattr(interaction, "get") else None
        if ie and hasattr(ie, "get") and b in ("insist", "command"):
            sub = ie.get(b) or ie.get(str(b))
            if not sub and b == "command":
                sub = ie.get("compliance")
            if sub and hasattr(sub, "get"):
                training_apply_effect_dict(worker, sub.get("effect") or sub, stat_changes)
                return
        if hasattr(store, "apply_attribute_change"):
            store.apply_attribute_change(worker, "rebelliousness", 1)
            stat_changes["rebelliousness"] = stat_changes.get("rebelliousness", 0) + 1

    def training_sum_trait_skill_modifiers(worker, skill_name):
        total = 0
        best_trait = None
        best_val = None
        if not worker or not hasattr(worker, "get"):
            return 0, None
        for trait_name in worker.get("traits") or []:
            trait_def = next((t for t in traits_list if t.get("name") == trait_name), None)
            if not trait_def or "modifiers" not in trait_def:
                continue
            mods = trait_def["modifiers"].get("skill_modifiers") or {}
            try:
                v = int(mods.get(skill_name, 0) or 0)
            except (TypeError, ValueError):
                v = 0
            if v == 0:
                continue
            total += v
            if best_val is None or v > best_val or (v == best_val and (best_trait or "") < trait_name):
                best_val = v
                best_trait = trait_name
        return total, best_trait

    def training_learning_roll(worker, skill_name):
        base_skills = worker.get("skills") or {}
        try:
            base_s = int(base_skills.get(skill_name, 0) or 0)
        except (TypeError, ValueError):
            base_s = 0
        base_s = max(0, min(100, base_s))
        trait_sum, best_trait = training_sum_trait_skill_modifiers(worker, skill_name)
        difficulty = base_s - trait_sum
        difficulty = max(5, min(95, difficulty))
        roll = renpy.random.randint(1, 100)
        success = roll > difficulty
        return {
            "success": success,
            "roll": roll,
            "difficulty": difficulty,
            "base_skill": base_s,
            "trait_sum": trait_sum,
            "best_trait": best_trait,
        }

    def training_acceptance_raw_score(worker, interaction):
        """
        Single acceptance score: comfort bonus + (100 - rebelliousness). Higher => easier to accept.
        Romance/relationship are not used for this roll (JSON may still list them for other effects).
        """
        comfort = int(worker.get("comfort_level", 1) or 1)
        comfort = max(1, min(30, comfort))
        reb = int(worker.get("rebelliousness", 50) or 0)
        reb = max(0, min(100, reb))
        comfort_term = min(50, comfort * 2 + max(0, comfort - 10) * 2)
        return float(comfort_term + (100 - reb))

    def training_roll_acceptance_once(worker, interaction):
        """
        d100 acceptance: raw = comfort_term + (100 - rebelliousness) from training_acceptance_raw_score.
        Success if roll < need, with need = clamp(round(raw), 10, 98).

        The old linear map from raw in [42,138] into need crushed mid scores (e.g. reb 20 + low comfort:
        raw≈82 became need≈47 → ~46% accept). Using raw directly, reb 20 and comfort 1 gives need≈82 → ~81%.
        """
        raw = float(training_acceptance_raw_score(worker, interaction))
        need = int(round(raw))
        need = max(10, min(98, need))
        roll = renpy.random.randint(1, 100)
        success = roll < need
        return {"success": success, "raw_score": raw, "need": need, "roll": roll}

    def training_charge_slot_and_costs(worker, interaction):
        """Increment interaction count; energy/health/money costs apply only via training_results."""
        increment_manager_interaction_count()
        stat_changes = {}
        if getattr(persistent, "nsfw_enabled", False):
            effects = interaction.get("effect") or {}
            apply_interaction_libido_effect(worker, effects, stat_changes)
        return stat_changes

    def training_shallow_interaction_copy(interaction, **overrides):
        out = {}
        if hasattr(interaction, "keys"):
            for k in interaction.keys():
                out[k] = interaction[k]
        for k, v in overrides.items():
            out[k] = v
        return out

    def training_branch_image_skill_slug(interaction):
        """Filename token from interaction.training_skill (spaces -> underscores)."""
        if not interaction or not hasattr(interaction, "get"):
            return ""
        return str(interaction.get("training_skill") or "").strip().replace(" ", "_")

    def training_resolve_branch_media_pick(worker, image_base):
        """
        One stem under images/workers/<folder>/: same rules as other worker art — flexible extensions
        and numbered files like 'Stem (1).png' (get_image_matches_flexible). No _lord/_lady suffixes.
        """
        if not image_base:
            return None
        worker_name = worker.get("name", "unknown") if hasattr(worker, "get") else "unknown"
        cache_key = f"{worker_name}_training_branch_{image_base}"
        fallback = get_fallback_folder(worker)
        worker_folder = worker.get("folder", fallback) if hasattr(worker, "get") else fallback
        base_folder = f"images/workers/{worker_folder}/"
        matches = get_image_matches_flexible(base_folder, image_base)
        if matches:
            return get_cached_choice(matches, cache_key)
        return None

    def training_resolve_branch_image(worker, interaction, branch):
        """
        Branch CG for refused | punished. Put the full filename stem in JSON (training_branch_images).
        Fallback chain (each stem tried plain only): JSON stem, then Training_Refused_<skill> or
        Training_Punished_<skill>, then Training_Refused / Training_Punished, then obedience, then profile.
        """
        default_plain = "Training_Refused" if branch == "refused" else "Training_Punished"
        bases_to_try = []

        br = interaction.get("training_branch_images") if interaction and hasattr(interaction, "get") else None
        if br and hasattr(br, "get"):
            v = br.get(branch)
            if v is not None:
                picked = training_coerce_training_text_value(v)
                if picked:
                    s = str(picked).strip()
                    if s:
                        bases_to_try.append(s)

        sk = training_branch_image_skill_slug(interaction)
        if sk:
            bases_to_try.append("%s_%s" % (default_plain, sk))

        bases_to_try.append(default_plain)
        bases_to_try.append("obedience")

        seen = set()
        for b in bases_to_try:
            if not b or b in seen:
                continue
            seen.add(b)
            img = training_resolve_branch_media_pick(worker, b)
            if img:
                return img

        worker_name = worker.get("name", "unknown") if hasattr(worker, "get") else "unknown"
        cache_key = f"{worker_name}_training_branch_profile_{branch}"
        profile_image = get_worker_image(worker)
        get_cached_choice([profile_image], cache_key)
        return profile_image

    def training_restore_ui_after_result(worker_or_none):
        """
        After training ends (including interaction_result closed via Hide/ESC during call screen),
        drop stacked interaction UI and show worker_details again. Interact is only from roster
        worker_details today, so in_roster=True matches that path.
        Hides training_branch_menu if still up.
        """
        store._training_interaction_result_active = False
        renpy.hide_screen("training_cutscene_backdrop")
        w = training_resolve_worker(worker_or_none)
        if not w:
            return
        renpy.hide_screen("interaction_result")
        renpy.hide_screen("training_branch_menu")
        renpy.hide_screen("interaction_category")
        renpy.hide_screen("interaction_menu")
        renpy.show_screen("worker_details", worker=w, in_roster=True)
        store._last_interaction_changes = {}

    def training_resume_worker_details_after_context(worker):
        """
        training_interaction_menu_runner runs inside renpy.call_in_new_context. Screens shown there (including
        worker_details from training_restore_ui_after_result) disappear when the subcontext ends; the parent
        context still has interaction_menu underneath. Re-hide menus and show worker_details here.
        """
        renpy.hide_screen("interaction_menu")
        renpy.hide_screen("interaction_category")
        w = training_resolve_worker(worker) or worker
        if w:
            renpy.show_screen("worker_details", worker=w, in_roster=True)

    def training_primary_art_missing(worker, interaction):
        """
        True if neither JSON-declared training art nor roster skill art (training_skill) resolves.
        """
        if not worker or not interaction or not hasattr(worker, "get"):
            return True
        bases = [b for b in training_interaction_primary_candidate_bases(worker, interaction) if b]
        fallback = get_fallback_folder(worker)
        worker_folder = worker.get("folder", fallback) if hasattr(worker, "get") else fallback
        base_folder = f"images/workers/{worker_folder}/"
        for base in bases:
            matches = get_training_primary_image_matches(base_folder, base)
            if matches:
                return False
        sk = interaction.get("training_skill") if hasattr(interaction, "get") else None
        if sk and get_worker_image(worker, sk, outcome="success"):
            return False
        return True

    def training_build_learn_fail_text(interaction, worker, roll=None, diff=None):
        """
        learn_fail summary line only: no trait hints (failure is not a 'best trait' moment).
        JSON may still use {pronoun}, {roll}, {difficulty}.
        """
        base = training_get_outcome_text(interaction, "learn_fail", worker)
        if base and not base.lower().startswith("training failed"):
            base = "Training failed. " + base
        pn = training_subject_pronoun(worker)
        txt = base.replace("{pronoun}", pn)
        if roll is not None:
            txt = txt.replace("{roll}", str(roll))
        if diff is not None:
            txt = txt.replace("{difficulty}", str(diff))
        return txt

    # Daily story consequences and training share the same trait_chance list schema.
    store.apply_trait_chance_entries = training_try_trait_chances
    store.apply_trait_remove_chance_entries = training_try_trait_remove_chances


# training_interaction_menu_runner: enter via renpy.call_in_new_context from interaction_category (see screens.rpy).
label training_interaction_menu_runner(worker, interaction):
    # Black base first (stays under all training screens), then peel UI — only new layers stack on top.
    $ store._training_interaction_result_active = False
    $ renpy.show_screen("training_cutscene_backdrop")
    $ renpy.hide_screen("interaction_category")
    $ renpy.hide_screen("interaction_menu")
    $ renpy.hide_screen("worker_details")
    $ renpy.hide_screen("training_branch_menu")
    call training_interaction_run(worker, interaction) from _call_training_interaction_run
    $ training_restore_ui_after_result(getattr(store, "_training_flow_worker", None) or worker)
    return


label training_interaction_run(worker, interaction):
    $ store._training_flow_worker = worker
    $ store._training_flow_interaction = interaction
    $ _tw = training_resolve_worker(store._training_flow_worker)
    if not _tw:
        return

    $ _ti = store._training_flow_interaction
    if not is_training_interaction(_ti):
        return

    python:
        store.training_branch_choice_prompt = training_flow_ui_substitute("branch_prompt", _tw, _ti)
        store._last_interaction_changes = training_charge_slot_and_costs(_tw, _ti)
        _acc = training_roll_acceptance_once(_tw, _ti)
        store._training_accept_ok = _acc["success"]
        store._training_insist_used = False
        store._training_skill = _ti.get("training_skill")

    # Use call/return instead of jump: jumping out of a call()ed label stacks badly with nested call screen + Return().
    if store._training_accept_ok:
        call _training_after_accept from _call__training_after_accept
    else:
        call _training_refused_menu from _call__training_refused_menu
    return

label _training_refused_menu:
    $ _tw = training_resolve_worker(store._training_flow_worker)
    $ _ti = store._training_flow_interaction
    python:
        _sk = store._training_skill or (_ti.get("training_skill") if _ti else None)
        _bf1 = training_get_result_block(_ti, "leave_be_first")
        _merged_leave1 = training_merge_static_effects(_bf1.get("effect") or {})
        _opt_leave1 = training_flow_ui_substitute("leave_them_be", _tw, _ti) + training_format_merged_effects(
            _merged_leave1,
            skill_uses=_bf1.get("skill_uses", 0),
            skill_name=_sk,
            trait_chance_list=training_coerce_trait_roll_list(_bf1.get("trait_chance")),
            trait_remove_chance_list=training_coerce_trait_roll_list(_bf1.get("trait_remove_chance")),
        )
        _opt_retry = training_try_again_menu_caption(_tw, _ti)
    $ _wimg = training_resolve_branch_image(_tw, _ti, "refused")
    $ store._training_branch_menu_image = _wimg
    $ _tbm_intro_lines = training_branch_menu_intro_first_refusal_messages(_tw, _ti)
    if _tbm_intro_lines:
        call screen training_branch_narration(lines=_tbm_intro_lines, bg_image=_wimg)
    $ store._training_branch_menu_title = store.training_branch_choice_prompt
    python:
        store._training_branch_menu_choices = [
            {"value": "leave_first", "text": _opt_leave1},
            {"value": "command", "text": _opt_retry},
        ]
    call screen training_branch_menu
    $ _tpick = _return

    if _tpick == "leave_first":
        python:
            _ch = training_apply_outcome(_tw, _ti, "leave_be_first")
            store._last_interaction_changes = _ch
        $ _fdesc = training_get_outcome_text(_ti, "leave_be_first", _tw)
        python:
            _br = _ti.get("training_branch_images") or {}
            _ref_img = _br.get("refused") if hasattr(_br, "get") else None
            _fi = training_shallow_interaction_copy(_ti, description=_fdesc, image=_ref_img or "Training_Refused")
        $ store._training_interaction_result_active = True
        call screen interaction_result(_tw, _fi, message_index=0, show_image_only=False, return_to_map=False, frozen_media=_wimg, from_call_screen=True)
        return

    elif _tpick == "command":
        python:
            _ins3 = {}
            training_apply_insist_cost(_tw, _ti, "command", _ins3)
            store._training_insist_used = True
            _acc3 = training_roll_acceptance_once(_tw, _ti)
            store._training_accept_ok = _acc3["success"]
            store._last_interaction_changes = _ins3
        if store._training_accept_ok:
            $ _insist_intro = training_insist_accepted_intro_messages(_tw, _ti)
            if _insist_intro:
                $ _wimg_ins = training_resolve_branch_image(_tw, _ti, "refused")
                call screen training_branch_narration(lines=_insist_intro, bg_image=_wimg_ins)
            call _training_after_accept from _call__training_after_accept_1
        else:
            call _training_refused_second_compliance from _call__training_refused_second_compliance
        return

    else:
        return

label _training_refused_second_compliance:
    $ _tw = training_resolve_worker(store._training_flow_worker)
    $ _ti = store._training_flow_interaction
    python:
        _sk2 = store._training_skill or (_ti.get("training_skill") if _ti else None)
        _bf_ls2 = training_get_result_block(_ti, "leave_be_second")
        _opt_leave2 = training_flow_ui_substitute("leave_them_be", _tw, _ti) + training_format_merged_effects(
            training_merge_static_effects(_bf_ls2.get("effect") or {}),
            skill_uses=_bf_ls2.get("skill_uses", 0),
            skill_name=_sk2,
            trait_chance_list=training_coerce_trait_roll_list(_bf_ls2.get("trait_chance")),
            trait_remove_chance_list=training_coerce_trait_roll_list(_bf_ls2.get("trait_remove_chance")),
        )
        _bf_pu = training_get_result_block(_ti, "punished")
        _opt_punish = training_flow_ui_substitute("show_disappointment", _tw, _ti) + training_format_merged_effects(
            training_merge_static_effects(_bf_pu.get("effect") or {}),
            skill_uses=_bf_pu.get("skill_uses", 0),
            skill_name=_sk2,
            trait_chance_list=training_coerce_trait_roll_list(_bf_pu.get("trait_chance")),
            trait_remove_chance_list=training_coerce_trait_roll_list(_bf_pu.get("trait_remove_chance")),
        )
    $ _wimg = training_resolve_branch_image(_tw, _ti, "refused")
    $ store._training_branch_menu_image = _wimg
    $ _tbm_intro_lines = training_branch_menu_intro_second_refusal_messages(_tw, _ti)
    if _tbm_intro_lines:
        call screen training_branch_narration(lines=_tbm_intro_lines, bg_image=_wimg)
    $ store._training_branch_menu_title = training_flow_ui_substitute("branch_prompt_second", _tw, _ti) or store.training_branch_choice_prompt
    python:
        store._training_branch_menu_choices = [
            {"value": "leave_second", "text": _opt_leave2},
            {"value": "punish", "text": _opt_punish},
        ]
    call screen training_branch_menu
    $ _tpick = _return

    if _tpick == "leave_second":
        python:
            _ch3 = training_apply_outcome(_tw, _ti, "leave_be_second")
            store._last_interaction_changes = _ch3
        $ _fdesc3 = training_get_outcome_text(_ti, "leave_be_second", _tw)
        $ _fi3 = training_shallow_interaction_copy(_ti, description=_fdesc3, image="Training_Refused")
        $ store._training_interaction_result_active = True
        call screen interaction_result(_tw, _fi3, message_index=0, show_image_only=False, return_to_map=False, frozen_media=_wimg, from_call_screen=True)
        return

    elif _tpick == "punish":
        $ _pimg = training_resolve_branch_image(_tw, _ti, "punished")
        $ _punish_intro = training_punished_intro_messages(_tw, _ti)
        if _punish_intro:
            call screen training_branch_narration(lines=_punish_intro, bg_image=_pimg)
        python:
            _ch4 = training_apply_outcome(_tw, _ti, "punished")
            store._last_interaction_changes = _ch4
        $ _fdesc4 = training_get_outcome_text(_ti, "punished", _tw)
        $ _fi4 = training_shallow_interaction_copy(_ti, description=_fdesc4, image="Training_Punished")
        $ store._training_interaction_result_active = True
        call screen interaction_result(_tw, _fi4, message_index=0, show_image_only=False, return_to_map=False, frozen_media=_pimg, from_call_screen=True)
        return

    else:
        return

label _training_after_accept:
    $ _tw = training_resolve_worker(store._training_flow_worker)
    $ _ti = store._training_flow_interaction
    $ _sk = store._training_skill or _ti.get("training_skill")
    python:
        _lr = training_learning_roll(_tw, _sk)
        store._training_learn_ok = _lr["success"]
        store._training_learn_roll = _lr["roll"]
        store._training_learn_diff = _lr["difficulty"]
        store._training_learn_trait = _lr["best_trait"]

    $ _mimg = get_interaction_image(_tw, _ti)

    if store._training_learn_ok:
        python:
            _ok_key = "trained_after_insist" if store._training_insist_used else "trained"
            _ch_ok = training_apply_outcome(_tw, _ti, _ok_key, skill_name=_sk)
            store._last_interaction_changes = _ch_ok
        $ _ok_intro = training_trained_intro_messages(_tw, _ti)
        if _ok_intro:
            call screen training_branch_narration(lines=_ok_intro, bg_image=_mimg)
        $ _okdesc = training_get_outcome_text(_ti, _ok_key, _tw) or training_get_outcome_text(_ti, "trained", _tw)
        $ _fok = training_shallow_interaction_copy(_ti, description=_okdesc)
        $ store._training_interaction_result_active = True
        call screen interaction_result(_tw, _fok, message_index=0, show_image_only=False, return_to_map=False, frozen_media=_mimg, from_call_screen=True)
        return

    python:
        _ch_f = training_apply_outcome(_tw, _ti, "learn_fail", skill_name=_sk)
        store._last_interaction_changes = _ch_f
    $ _lf_intro = training_learn_fail_intro_messages(_tw, _ti)
    if _lf_intro:
        call screen training_branch_narration(lines=_lf_intro, bg_image=_mimg)
    $ _faildesc = training_build_learn_fail_text(_ti, _tw, store._training_learn_roll, store._training_learn_diff)
    $ _ffail = training_shallow_interaction_copy(_ti, description=_faildesc)
    $ store._training_interaction_result_active = True
    call screen interaction_result(_tw, _ffail, message_index=0, show_image_only=False, return_to_map=False, frozen_media=_mimg, from_call_screen=True)
    return


# One caption per click (same CG/textbox look as the menu; no narrator/say — safe under Call()).
# Text uses [_tbm_cap!q]: !q quotes the string so [, {, \ from JSON do not trigger Ren'Py text substitutions/tags.
screen training_branch_narration(lines, bg_image=None):
    zorder 100
    modal True
    default nidx = 0
    $ _tbm_last = len(lines) - 1 if lines else -1

    fixed:
        xfill True
        yfill True
        button:
            xfill True
            yfill True
            background None
            action If(
                nidx < _tbm_last,
                SetScreenVariable("nidx", nidx + 1),
                Return(),
            )

            fixed:
                xfill True
                yfill True

                if bg_image:
                    add bg_image:
                        xalign 0.5
                        yalign 0.5
                        fit "contain"
                        xysize (1920, 1080)

                $ _tbm_cap = lines[nidx] if lines and nidx < len(lines) else ""

                window:
                    style "say_window"
                    xalign 0.5
                    xfill True
                    yalign gui.textbox_yalign
                    ysize gui.textbox_height

                    fixed:
                        xfill True
                        yfill True
                        vbox:
                            xalign 0.5
                            yalign 0.5
                            text "[_tbm_cap!q]":
                                style "say_dialogue"
                                xsize gui.dialogue_width
                                xpos 0
                                ypos 0
                                text_align 0.0
                                adjust_spacing True


# CG + choices; black comes from training_cutscene_backdrop (single persistent layer).
screen training_branch_menu():
    zorder 100
    modal True
    $ _tbm_img = store._training_branch_menu_image
    $ _tbm_choices = store._training_branch_menu_choices
    $ _tbm_title = store._training_branch_menu_title

    fixed:
        xfill True
        yfill True

        if _tbm_img:
            add _tbm_img:
                xalign 0.5
                yalign 0.5
                fit "contain"
                xysize (1920, 1080)

        vbox:
            style "choice_vbox"
            for _tbm_row in _tbm_choices:
                textbutton "[_tbm_row['text']!q]":
                    style "training_branch_choice_button"
                    text_style "training_branch_choice_button_text"
                    action Return(_tbm_row["value"])

        if _tbm_title:
            window:
                style "say_window"
                xalign 0.5
                xfill True
                yalign gui.textbox_yalign
                ysize gui.textbox_height

                fixed:
                    xfill True
                    yfill True
                    vbox:
                        xalign 0.5
                        yalign 0.5
                        text "[_tbm_title!q]":
                            style "say_dialogue"
                            xsize gui.dialogue_width
                            xpos 0
                            ypos 0
                            text_align 0.5
                            adjust_spacing True


# Training branch: use choice *hover* slab as the always-on background; hover only shifts text to gui.hover_color (#6b6528).
style training_branch_choice_button is choice_button:
    idle_background Frame("gui/button/choice_hover_background.png", gui.choice_button_borders, gui.choice_button_tile)
    hover_background Frame("gui/button/choice_hover_background.png", gui.choice_button_borders, gui.choice_button_tile)
    insensitive_background Frame("gui/button/choice_hover_background.png", gui.choice_button_borders, gui.choice_button_tile)

style training_branch_choice_button_text is choice_button_text:
    hover_color gui.hover_color
