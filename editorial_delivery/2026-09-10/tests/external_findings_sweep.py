# -*- coding: utf-8 -*-
"""Turn each Codex finding into a repo-wide scan instead of a spot fix.

Codex reported single instances. Every one of them is a class: if
monster_taming_combat promises "no fee" while its formula pays, the question is
how many other outcomes do that. This finds the whole class for findings 1, 2, 3
and 5, so the pass fixes the defect rather than the example.
"""

import glob
import io
import json
import os
import re
import sys

ROOT = "C:/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager"
LADDER = ("failure", "mediocre", "success", "critical_success")


def stories():
    """Yield (source, building, profession, story) for every daily story."""
    path = os.path.join(ROOT, "game/data/buildings/building_types.json")
    data = json.load(io.open(path, encoding="utf-8-sig"))
    for b in data["building_types"]:
        for job in b.get("professions", []):
            for st in job.get("daily_stories", []):
                yield ("building_types.json", b["id"], job["id"], st)
    for f in sorted(glob.glob(os.path.join(
            ROOT, "game/data/buildings/daily_story_extensions/*.json"))):
        ext = json.load(io.open(f, encoding="utf-8-sig"))
        base = os.path.basename(f)
        for key, block in ext.items():
            if not isinstance(block, dict):
                continue
            for st in block.get("daily_stories", []) or []:
                yield (base, key, key, st)


ALL = list(stories())
print("historias analizadas: %d\n" % len(ALL))

# --- Finding 1: text denies or asserts payment against its own formula --------
# A failure formula of the shape -(roll - skill) is always a loss. A text that
# says the client paid and names no offsetting cost reads as a contradiction.
# The reverse case is worse: "no fee" on an outcome whose formula is positive.
DENY = re.compile(r"\bno (fee|pay|payment|coin|money|wage)\b|\bnothing (for|to show)\b"
                  # "not a copper OVER" is about the tip, not the fee: the client
                  # did pay. Only a denial that no money changed hands counts.
                  r"|\bnot a (copper|coin|penny)\b(?!\s+(over|more|extra))"
                  r"|\bwithout (a )?(fee|payment)\b", re.I)
PAYS = re.compile(r"\b(pays?|paid|paying|tips?|tipped|tipping|settles the bill|"
                  r"over the rate|the quoted rate|base fee|books|bought)\b", re.I)
COST = re.compile(r"\b(refund|refunds|refunded|compensat|makes good|writes off|"
                  r"write-off|bill|damages|healer|replace|loss|out of pocket|"
                  r"costs the house|the house eats|comps?)\b", re.I)

print("=" * 78)
print("HALLAZGO 1 - texto vs formula de ingresos")
print("=" * 78)
f1 = []
for src, b, j, st in ALL:
    earn = st.get("earnings") or {}
    for outcome in LADDER:
        text = (st.get("descriptions") or {}).get(outcome)
        if not text:
            continue
        formula = str(earn.get(outcome, ""))
        negative = formula.strip().startswith("-")
        positive = bool(formula) and not negative
        if DENY.search(text) and positive:
            f1.append(("NIEGA-PERO-PAGA", src, st["id"], outcome, formula,
                       DENY.search(text).group(0)))
        elif PAYS.search(text) and negative and not COST.search(text):
            f1.append(("AFIRMA-PAGO-EN-PERDIDA", src, st["id"], outcome, formula,
                       PAYS.search(text).group(0)))
for row in f1:
    print("  %-22s %-34s %-16s %-14s  <%s>" % (row[0], row[2], row[3], row[4], row[5]))
print("  total: %d  (graves: %d)"
      % (len(f1), sum(1 for r in f1 if r[0] == "NIEGA-PERO-PAGA")))

# --- Finding 2: durations that do not fit a one-day resolution ---------------
# Past-tense spans only. "next week" / "tomorrow" are forward-looking colour and
# Codex explicitly excluded them.
SPAN = re.compile(r"\b(two|three|four|five|several|a few|many)\s+"
                  r"(days|nights|weeks|mornings|evenings)\b", re.I)
FORWARD = re.compile(r"\b(next|coming|following|another|for the next|over the next|"
                     # aftermath is colour, not consumed working time
                     r"books|booked|will|would|promises|later|afterwards)\b", re.I)
print("\n" + "=" * 78)
print("HALLAZGO 2 - duraciones incompatibles con la resolucion diaria")
print("=" * 78)
f2 = []
for src, b, j, st in ALL:
    for outcome in LADDER:
        text = (st.get("descriptions") or {}).get(outcome)
        if not text:
            continue
        for match in SPAN.finditer(text):
            window = text[max(0, match.start() - 60):match.end() + 40]
            f2.append((src, st["id"], outcome, match.group(0),
                       bool(FORWARD.search(window)), window.strip()))
for row in f2:
    print("  %-34s %-16s %-14s %s" % (row[1], row[2], row[3],
                                      "(futuro, OK)" if row[4] else "<-- REVISAR"))
    if not row[4]:
        print("      ...%s..." % row[5])
print("  total: %d  (a revisar: %d)" % (len(f2), sum(1 for r in f2 if not r[4])))

# --- Finding 3: narrated act vs the skill and the player-facing report --------
ACTS = {
    "Oral": r"\b(mouth|tongue|throat|licks?|licking|sucks?|sucking|swallow\w*|"
            r"goes down on|blow\w*|lips (?:close|around)|down her throat|"
            r"down his throat)\b",
    "Hand": r"\b(fingers?|fingering|fingered|hand ?job|strokes?|stroking|wrist|"
            r"palm|knuckles)\b",
    "Anal": r"\b(anal|arse|ass\b|behind\b.{0,20}\bin(to)?\b)",
    "Sex": r"\b(fucks?|fucking|rides?|riding|inside her|inside him|cock in|"
           r"thrust\w*|takes him deep|mounts)\b",
}
print("\n" + "=" * 78)
print("HALLAZGO 3 - acto narrado que el 'report' visible contradice")
print("=" * 78)
f3 = []
for src, b, j, st in ALL:
    skills = set(st.get("skill_options") or [])
    report = st.get("report", "")
    # only meaningful where the report names one act and the skill agrees
    for act, pattern in ACTS.items():
        if act in skills:
            continue
        if not re.search(r"\b%s\b" % act, report, re.I):
            pass
        for outcome in LADDER:
            text = (st.get("descriptions") or {}).get(outcome)
            if not text:
                continue
            hit = re.search(pattern, text, re.I)
            if hit and skills and skills.isdisjoint({act}):
                f3.append((src, st["id"], outcome, act, sorted(skills), report,
                           hit.group(0)))
# Codex's point is narrower than "any mismatch": the user has ruled that a
# disconnect is often fine. Only flag where the report string the player reads
# in the daily summary names a different act than the prose.
REPORT_ACT = {"Fingering": "Hand", "Handjob": "Hand", "a Handjob": "Hand",
              "Oral": "Oral", "Blowjob": "Oral", "Sex": "Sex", "Anal": "Anal"}
hard = []
for row in f3:
    for word, act in REPORT_ACT.items():
        if re.search(r"\b%s\b" % re.escape(word), row[5], re.I) and act != row[3]:
            hard.append(row)
            break
seen = set()
for row in hard:
    key = (row[1], row[2], row[3])
    if key in seen:
        continue
    seen.add(key)
    print("  %-38s %-16s report=%-26s narra=%-6s skills=%s"
          % (row[1], row[2], row[5], row[3], ",".join(row[4])))
    print("      <%s>" % row[6])
print("  mismatches totales: %d   tocan el report visible: %d" % (len(f3), len(seen)))
print("""
  NOTA: este contador NO es un recuento de defectos. El desarrollador ha
  establecido que el desajuste entre la actividad narrada y la skill evaluada es
  aceptable a veces: una escena de "Client paid for Sex" que empieza con la boca
  es preliminar, no contradiccion. Y comprobar la AUSENCIA del acto declarado da
  falsos positivos masivos, porque el acto se narra sin nombrarlo ("works him
  open", "takes the lady's strap"). Se deja como inventario para lectura humana.
  Ver AUDIT_REPORT.md seccion 12.3.""")

# --- Finding 5: grammar and shared constructions ------------------------------
print("\n" + "=" * 78)
print("HALLAZGO 5 - gramatica y construcciones compartidas")
print("=" * 78)
GRAMMAR = [
    (r"too much (teeth|hands|fingers|people|words)", "much->many"),
    (r"\bless (people|coins|clients|customers)\b", "less->fewer"),
    (r"\bamount of (people|clients|coins|customers)\b", "amount->number"),
    (r"\ba (hour|honest)\b", "a->an"),
    (r"\bcould of\b|\bwould of\b|\bshould of\b", "of->have"),
]
for src, b, j, st in ALL:
    for outcome in LADDER:
        text = (st.get("descriptions") or {}).get(outcome) or ""
        for pattern, label in GRAMMAR:
            for match in re.finditer(pattern, text, re.I):
                print("  %-38s %-16s %-14s <%s>"
                      % (st["id"], outcome, label, match.group(0)))

# shared multi-word constructions: the "ankles hooked behind him" family
print("\n  construcciones compartidas entre historias distintas (>=5 palabras):")
grams = {}
for src, b, j, st in ALL:
    for outcome in LADDER:
        text = (st.get("descriptions") or {}).get(outcome) or ""
        words = re.findall(r"[a-z']+", text.lower())
        for i in range(len(words) - 4):
            grams.setdefault(" ".join(words[i:i + 5]), set()).add(st["id"])
shared = {g: ids for g, ids in grams.items() if len(ids) >= 2}
# collapse overlapping n-grams belonging to the same story pair
seen_pairs = {}
for g, ids in sorted(shared.items(), key=lambda kv: -len(kv[1])):
    key = tuple(sorted(ids))
    seen_pairs.setdefault(key, []).append(g)
for key, gs in sorted(seen_pairs.items(), key=lambda kv: -len(kv[1]))[:18]:
    longest = max(gs, key=len)
    print("    %2d n-gramas  %-52s  %s" % (len(gs), '"%s"' % longest, ", ".join(key)[:80]))
print("  pares/grupos de historias que comparten texto literal: %d" % len(seen_pairs))
