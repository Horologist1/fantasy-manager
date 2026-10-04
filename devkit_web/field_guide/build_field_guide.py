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
                .replace("/*DATA*/", data))
    # template.html starts with <title>/<link>/<style>: they belong in <head>.
    head_end = page.index('<div class="wrap">')
    page = PAGE_HEAD + page[:head_end] + "</head>\n<body>\n" + page[head_end:] + "\n</body>\n</html>\n"

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"Field guide written to {args.out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
