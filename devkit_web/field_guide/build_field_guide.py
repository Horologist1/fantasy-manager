"""Build the Fantasy Manager Field Guide (a single self-contained HTML page).

Reads game/data/ for every image name the game looks for (daily stories, events,
interactions, training) and embeds it, together with the hand-written chapters in
this folder, into user_docs/guides/field_guide.html.

    npm run guide                      (from devkit_web/, also part of npm run check)
    python field_guide/build_field_guide.py [--out PATH]

The GitHub Pages workflow runs this on every push that touches game data, so the
image lists stay in sync with the game. The mechanics chapters (part_*.html) are
written by hand: update them when a formula changes. See README.md here.
"""
import argparse
import glob
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))  # devkit_web/field_guide -> repo root
GAME = os.path.join(REPO, "game")
DEFAULT_OUT = os.path.join(REPO, "user_docs", "guides", "field_guide.html")

# Visual-novel scenes are not part of the guide (their workers' daily art is).
VN_EVENT_FILES = {"events_workers_yvara.json", "events_workers_lanista.json"}

# Skill -> file names the image matcher accepts (events/event_visuals.rpy,
# get_skill_search_patterns). Keep in sync if aliases change.
SKILL_FILES = {
    "Combat": ["combat"], "Agility": ["agility"], "Clever": ["clever"], "Charm": ["charm"],
    "Craft": ["craft"], "Service": ["service", "wait", "maid"], "Striptease": ["strip", "striptease"],
    "Hand": ["hand"], "Oral": ["oral"], "Sex": ["sex"], "Anal": ["anal"], "Homo": ["les", "gay", "homo"],
    "Special": ["special", "titty"], "Group": ["group"], "BDSM": ["bdsm"], "Extreme": ["extreme", "beast"],
}
SFW_SKILLS = {"Combat", "Agility", "Clever", "Charm", "Craft", "Service"}

PAGE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
"""


def load(rel):
    with open(os.path.join(GAME, rel), encoding="utf-8") as f:
        return json.load(f)


def as_list(raw):
    if isinstance(raw, list):
        return raw
    return next((v for v in raw.values() if isinstance(v, list)), [])


def skill_fallback(skill):
    return SKILL_FILES.get(skill, [str(skill).lower()])[0]


def build_data():
    data = {"skills": [{"skill": k, "nsfw": k not in SFW_SKILLS, "files": v} for k, v in SKILL_FILES.items()]}

    # Interactions (deduplicated by category + image name)
    seen = {}
    for fn in ("interactions_structured.json", "interactions_special.json"):
        for i in load("data/interactions/" + fn):
            if not i.get("image"):
                continue
            cat = (i.get("categories") or ["Other"])[0]
            row = seen.setdefault((cat, i["image"]), {
                "cat": cat, "name": i["image"], "lvl": i.get("interaction_level"), "nsfw": False, "ids": [],
                "fb": {"Romance": "romance_lord / romance_lady", "Friendship": "friendship",
                       "Discipline": "obedience"}.get(cat, "profile")})
            row["ids"].append(i["id"])
            row["nsfw"] = row["nsfw"] or bool(i.get("nsfw"))
    data["interactions"] = list(seen.values())

    # Training
    data["training"], branches = [], {}
    for t in load("data/interactions/interactions_training.json"):
        if t.get("image"):
            data["training"].append({"name": t["image"], "skill": t.get("training_skill")})
            for kind, name in (t.get("training_branch_images") or {}).items():
                branches[name] = kind
    data["training_branches"] = [{"name": n, "kind": k} for n, k in branches.items()]

    # Daily stories: base buildings, special buildings, relationship extensions
    rows = []
    for rel in ("data/buildings/building_types.json", "data/buildings/special_buildings.json"):
        for b in load(rel)["building_types"]:
            for p in b.get("professions", []):
                for s in p.get("daily_stories", []):
                    rows.append((b.get("name", b["id"]), b["id"], p.get("name", p["id"]), p["id"], s, False))
    for path in sorted(glob.glob(os.path.join(GAME, "data/buildings/daily_story_extensions/*.json"))):
        with open(path, encoding="utf-8") as f:
            x = json.load(f)
        bname = next((r[0] for r in rows if r[1] == x["building_id"]), x["building_id"])
        pname = next((r[2] for r in rows if r[1] == x["building_id"] and r[3] == x["profession_id"]), x["profession_id"])
        for s in x.get("daily_stories", []):
            rows.append((bname, x["building_id"], pname, x["profession_id"], s, True))
    stories = []
    for bname, _bid, pname, pid, s, is_rel in rows:
        tags = []
        g = s.get("worker_gender_requirement")
        if g:
            tags.append("♂" if g == "male" else "♀")
        for stat, v in (s.get("stat_requirements") or {}).items():
            tags.append(f"{stat} ≥ {v}" if not isinstance(v, dict) else stat)
        tags += list(s.get("required_traits") or [])
        skills = s.get("skill_options") or []
        chain = s.get("story_image_fallback_patterns") or s.get("image_fallback_patterns")
        if chain:
            chain = list(chain)
        elif skills:
            chain = [skill_fallback(k) for k in skills]
        else:
            chain = ["rest"] if pid == "rest" else []
        stories.append({"b": bname, "p": pname, "id": s["id"], "rel": is_rel, "tags": tags,
                        "s": s.get("story_image") or "", "f": s.get("failure_image") or "",
                        "skills": skills, "fb": chain})
    data["stories"] = stories

    # Events (no visual novels)
    events = []
    files = sorted(glob.glob(os.path.join(GAME, "data/events/*.json"))) + \
        sorted(glob.glob(os.path.join(GAME, "data/events/recruit/*.json")))
    for path in files:
        fn = os.path.basename(path)
        if fn in VN_EVENT_FILES:
            continue
        with open(path, encoding="utf-8") as f:
            evs = as_list(json.load(f))
        for e in evs:
            if not isinstance(e, dict):
                continue
            imgs = []
            for k in ("background_image", "success_image", "failure_image"):
                if e.get(k):
                    imgs.append({"k": k.split("_")[0], "n": e[k]})
            for c in e.get("choices") or []:
                if isinstance(c, dict):
                    for k in ("success_image", "failure_image", "background_image"):
                        if c.get(k):
                            imgs.append({"k": "option " + k.split("_")[0], "n": c[k]})
            uniq = [i for n, i in enumerate(imgs) if i not in imgs[:n]]
            if uniq:
                conds = sorted({str(c["condition"]) for c in (e.get("choices") or [])
                                if isinstance(c, dict) and c.get("condition")})
                events.append({"file": fn[:-5], "id": e.get("id", "?"), "sel": e.get("worker_selection") or "",
                               "conds": conds, "imgs": uniq})
    data["events"] = events
    return data


# ---------------------------------------------------------------- traits list
#
# Defined in data/traits but granted by nothing in the game (checked 0.9.6.2t1):
# listing them would promise traits nobody can get.
NEVER_GRANTED = {"Expecting Visit", "Expecting Visit2", "Soul Wearied", "Cursed Vitality",
                 "Blade's Whisper", "Curse of Greed", "Vampire", "Furry"}


def _trait_tags(t):
    tags = []
    if t.get("nsfw") or t.get("nsfw_only"):
        tags.append('<span class="pill nsfw">NSFW</span>')
    g = t.get("gender_restriction")
    if g in ("male", "female"):
        tags.append('<span class="pill tag">%s only</span>' % g)
    if int(t.get("duration") or 0) > 0:
        tags.append('<span class="pill tag">%d days</span>' % int(t["duration"]))
    return " ".join(tags)


def build_traits_html():
    groups = {"races": [], "rolled": [], "story": []}
    seen = set()
    for path in sorted(glob.glob(os.path.join(GAME, "data/traits/*.json"))):
        with open(path, encoding="utf-8") as f:
            for t in as_list(json.load(f)):
                name = (t or {}).get("name") if isinstance(t, dict) else None
                if not name or name in seen or name in NEVER_GRANTED:
                    continue
                seen.add(name)  # first definition wins, like the game
                key = "races" if os.path.basename(path) == "traits_races.json" else (
                    "story" if t.get("only_assigned") else "rolled")
                groups[key].append(t)
    titles = {
        "races": ("Races", "Every worker has one race. Races are traits too."),
        "rolled": ("Traits workers can be born with",
                   "New workers roll their traits from this list."),
        "story": ("Story, status and reward traits",
                  "Never rolled at random: they come from events, recruitment choices, "
                  "interactions, the governor, the Arena or a character's story. "
                  "Temporary ones show how many days they last."),
    }
    out = []
    for key in ("races", "rolled", "story"):
        title, intro = titles[key]
        rows = sorted(groups[key], key=lambda t: t["name"].lower())
        out.append('<h3 id="p-traits-%s">%s (%d)</h3><p>%s</p>' % (key, html.escape(title), len(rows), html.escape(intro)))
        out.append('<div class="tw"><table><thead><tr><th>Trait</th><th>What it does</th></tr></thead><tbody>')
        for t in rows:
            out.append("<tr><td><b>%s</b> %s</td><td>%s</td></tr>" % (
                html.escape(t["name"]), _trait_tags(t), html.escape(t.get("description") or "")))
        out.append("</tbody></table></div>")
    return "\n".join(out)


# --------------------------------------------------------------- workers list
#
# Workers that join through a story, not through Recruit or the market.
# Facts verified against the code for 0.9.6.2t1 (see README).
WORKER_NOTES = {
    "Yvara": "Yvara's Academy story (NSFW): she joins on the Dominion or Mixed ending.",
    "Kar": "Recruit Workers, her own event only. SFW: once the Arena is unlocked. NSFW: after any "
           "ending of the Lanista's story with a female Lanista.",
    "Kara": "Recruit Workers, her own event only. SFW: once the Arena is unlocked. NSFW: after any "
            "ending of the Lanista's story with a male Lanista.",
}
LANISTA_NOTE = ("The Lanista's Arena story (NSFW): joins on the Dominion or Mixed ending. "
                "Varra or Varro, depending on the gender you choose at the first meeting.")


def build_workers_html():
    recruit_events = set()
    for path in sorted(glob.glob(os.path.join(GAME, "data/events/recruit/*.json"))):
        with open(path, encoding="utf-8") as f:
            for e in as_list(json.load(f)):
                if isinstance(e, dict) and e.get("worker_name"):
                    recruit_events.add(e["worker_name"])
    found = {}
    for path in sorted(glob.glob(os.path.join(GAME, "data/workers/*.json"))):
        base = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        workers = raw if isinstance(raw, list) else (raw.get("workers") if isinstance(raw.get("workers"), list) else [raw])
        for w in workers:
            # Monster templates have no name: the game names each capture.
            if not isinstance(w, dict) or not (w.get("name") or w.get("monster_archetype")):
                continue
            # encounter_only on a NON-unique sheet = only a template for generated
            # workers. Most uniques are encounter_only too: they come by recruitment.
            if w.get("encounter_only") and not w.get("unique") and not w.get("monster"):
                continue
            mode = "NSFW" if w.get("nsfw") else "SFW"
            if w.get("monster"):
                if not w.get("unique"):
                    name = "%s (any number)" % (w.get("monster_archetype") or w.get("name")).title()
                    how = "Captured with Monster Taming at the Adventurer's Guild; gets a new name each time."
                else:
                    name = w["name"]
                    how = "Captured with Monster Taming at the Adventurer's Guild (10–15% per successful story)."
                group = "monster"
            elif base.startswith("lanista_"):
                name, how, group = w["name"], LANISTA_NOTE, "story"
            elif w["name"] in WORKER_NOTES:
                name, how, group = w["name"], WORKER_NOTES[w["name"]], "story"
            elif w.get("unique"):
                name, group = w["name"], "recruit"
                pron = "his" if str(w.get("gender", "")).lower() == "male" else "her"
                how = ("Recruit Workers, with %s own recruitment event." % pron
                       if w["name"] in recruit_events else "Recruit Workers.")
            else:
                name, group = w["name"], "market"
                how = "Buy Servants, about $%s." % w.get("cost", "?")
            row = found.setdefault((group, name), {"name": name, "how": how, "modes": set(), "group": group})
            row["modes"].add(mode)
    labels = {"recruit": ("Recruited", "From the map: Recruit Workers, once a day. Unique workers only appear in "
                                       "the content mode their sheet belongs to (an SFW-only worker is never offered "
                                       "in NSFW mode, and the other way round). When every unique has been hired, "
                                       "Recruit Workers offers newly generated workers instead."),
              "market": ("Bought", "From the map: Buy Servants. Five offers a day; one free refresh, a second one "
                                   "for $2,500. NSFW-mode games can also be offered the SFW workers below."),
              "story": ("Joined through a story", ""),
              "monster": ("Monsters", "Only in NSFW mode: Monster Taming is an NSFW job.")}
    out = []
    for group in ("recruit", "market", "story", "monster"):
        rows = sorted((r for r in found.values() if r["group"] == group), key=lambda r: r["name"].lower())
        if not rows:
            continue
        title, intro = labels[group]
        out.append('<h3 id="p-get-%s">%s (%d)</h3>' % (group, html.escape(title), len(rows)))
        if intro:
            out.append("<p>%s</p>" % html.escape(intro))
        out.append('<div class="tw"><table><thead><tr><th>Worker</th><th>Mode</th><th>How to get</th></tr></thead><tbody>')
        for r in rows:
            mode = "SFW and NSFW" if len(r["modes"]) > 1 else next(iter(r["modes"]))
            out.append("<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (
                html.escape(r["name"]), mode, html.escape(r["how"])))
        out.append("</tbody></table></div>")
    return "\n".join(out)


def build_professions_html():
    """building_id / profession_id pairs a mod's daily stories can target."""
    rows = []
    for path in sorted(glob.glob(os.path.join(GAME, "data/buildings/*.json"))):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for b in raw.get("building_types", []) if isinstance(raw, dict) else []:
            profs = [p for p in b.get("professions", []) if isinstance(p, dict) and p.get("id")]
            if b.get("id") and profs:
                rows.append((b.get("name") or b["id"], b["id"], profs))
    out = ['<div class="tw"><table><thead><tr><th>building_id</th><th>profession_id</th></tr></thead><tbody>']
    for name, bid, profs in sorted(rows, key=lambda r: r[1]):
        jobs = "<br>".join("<code>%s</code> <span class=\"fb\">%s</span>" % (html.escape(p["id"]), html.escape(p.get("name") or p["id"])) for p in profs)
        out.append("<tr><td><code>%s</code><div class=\"sub-line\">%s</div></td><td>%s</td></tr>" % (html.escape(bid), html.escape(name), jobs))
    out.append("</tbody></table></div>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    def part(name):
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            return f.read()

    data = json.dumps(build_data(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = part("template.html")
    page = (page.replace("<!--PLAY-->", part("part_play.html"))
                .replace("<!--REF-->", part("part_ref.html"))
                .replace("<!--IMG-->", part("part_img.html"))
                .replace("<!--MODS-->", part("part_mods.html"))
                .replace("/*DATA*/", data))
    page = (page.replace("<!--TRAIT_LIST-->", build_traits_html())
                .replace("<!--WORKER_LIST-->", build_workers_html())
                .replace("<!--PROFESSION_LIST-->", build_professions_html()))
    # template.html starts with <title>/<link>/<style>: they belong in <head>.
    head_end = page.index('<div class="wrap">')
    page = PAGE_HEAD + page[:head_end] + "</head>\n<body>\n" + page[head_end:] + "\n</body>\n</html>\n"

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"Field guide written to {args.out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
