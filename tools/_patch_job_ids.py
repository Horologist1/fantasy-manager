from pathlib import Path

sr = Path(r"C:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager\game\scripts\script.rpy")
t = sr.read_text(encoding="utf-8")
if "def canonicalize_servant_job_id" in t:
    print("script.rpy already patched")
else:
    old = """    def sanitize_invalid_servant_job(building, worker_name, worker_obj=None):
        \"\"\"If servant_jobs has a profession id not defined for this building type, reset to unassigned.
        Prevents stale jobs after moves (e.g. 'service' from another building). Rest is always allowed.\"\"\"
        if not building or not worker_name:
            return
        jobs_map = building.get(\"servant_jobs\") or {}
        jid = jobs_map.get(worker_name)
        if jid is None:
            return
        jlow = str(jid).strip().lower()
        if jlow in (\"\", \"unassigned\"):
            return
        if jlow == \"rest\":
            return
        btype_id = building.get(\"type\")
        if not btype_id:
            return
        btype = next((bt for bt in building_types_json.get(\"building_types\", []) if bt.get(\"id\") == btype_id), None)
        if not btype:
            return
        valid = False
        for p in btype.get(\"professions\", []) or []:
            pid = p.get(\"id\")
            if pid is not None and str(pid).strip().lower() == jlow:
                valid = True
                break
        if valid:
            return
        building[\"servant_jobs\"][worker_name] = \"unassigned\"
"""
    new = """    def canonicalize_servant_job_id(building, job_id):
        \"\"\"Return canonical profession id for servant_jobs: always lowercase 'rest', else JSON id spelling.\"\"\"
        if job_id is None:
            return \"unassigned\"
        s = str(job_id).strip()
        if not s or s.lower() == \"unassigned\":
            return \"unassigned\"
        jlow = s.lower()
        if jlow == \"rest\":
            return \"rest\"
        btype_id = building.get(\"type\") if building else None
        if not btype_id:
            return s
        btype = next((bt for bt in building_types_json.get(\"building_types\", []) if bt.get(\"id\") == btype_id), None)
        if not btype:
            return s
        for p in btype.get(\"professions\", []) or []:
            pid = p.get(\"id\")
            if pid is not None and str(pid).strip().lower() == jlow:
                return str(pid).strip()
        return s

    def sanitize_invalid_servant_job(building, worker_name, worker_obj=None):
        \"\"\"If servant_jobs has a profession id not defined for this building type, reset to unassigned.
        Prevents stale jobs after moves (e.g. 'service' from another building). Rest is always allowed.
        Normalizes rest to lowercase 'rest' and profession ids to match JSON casing (fixes job filter duplicates).\"\"\"
        if not building or not worker_name:
            return
        jobs_map = building.get(\"servant_jobs\") or {}
        jid = jobs_map.get(worker_name)
        if jid is None:
            return
        jlow = str(jid).strip().lower()
        if jlow in (\"\", \"unassigned\"):
            return
        if jlow == \"rest\":
            if str(jid).strip() != \"rest\":
                building[\"servant_jobs\"][worker_name] = \"rest\"
                renpy.log(\"sanitize_invalid_servant_job: %s normalized rest job %r -> 'rest'\" % (worker_name, jid))
            return
        btype_id = building.get(\"type\")
        if not btype_id:
            return
        btype = next((bt for bt in building_types_json.get(\"building_types\", []) if bt.get(\"id\") == btype_id), None)
        if not btype:
            return
        canon = None
        for p in btype.get(\"professions\", []) or []:
            pid = p.get(\"id\")
            if pid is not None and str(pid).strip().lower() == jlow:
                canon = str(pid).strip()
                break
        if canon is not None:
            if str(jid).strip() != canon:
                building[\"servant_jobs\"][worker_name] = canon
                renpy.log(\"sanitize_invalid_servant_job: %s normalized job %r -> %r\" % (worker_name, jid, canon))
            return
        building[\"servant_jobs\"][worker_name] = \"unassigned\"
"""
    if old not in t:
        raise SystemExit("script.rpy: old sanitize block not found")
    t = t.replace(old, new, 1)
    old2 = """        building[\"servant_jobs\"][worker_name] = job_id if job_id is not None else \"unassigned\"
"""
    new2 = """        canon_job = canonicalize_servant_job_id(building, job_id if job_id is not None else \"unassigned\")
        building[\"servant_jobs\"][worker_name] = canon_job
"""
    if old2 not in t:
        raise SystemExit("script.rpy: set_worker_job tail not found")
    t = t.replace(old2, new2, 1)
    sr.write_text(t, encoding="utf-8")
    print("script.rpy patched")

sc = Path(r"C:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager\game\scripts\core\screens.rpy")
u = sc.read_text(encoding="utf-8")

def rpj_block(btype_var, job_var, fallback_expr):
    return (
        "_rpj = getattr(store, \"resolve_profession_for_job\", None)\n"
        "                                    if callable(_rpj):\n"
        "                                        job_name, _pj_unused = _rpj(%s, %s)\n"
        "                                    else:\n"
        "                                        job_name = %s\n"
    ) % (btype_var, job_var, fallback_expr)

# 1) unique_jobs loop ~9315
old_a = """                                    job_name = next((p[\"name\"] for p in btype.get(\"professions\", []) if p[\"id\"] == job_id), job_id)
"""
new_a = """                                    """ + rpj_block("btype", "job_id", "next((p[\"name\"] for p in btype.get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == str(job_id).strip().lower()), job_id)") + """
"""
if old_a not in u:
    raise SystemExit("screens block A not found")
u = u.replace(old_a, new_a, 1)

old_b = """                                        job_name = next((p[\"name\"] for p in btype.get(\"professions\", []) if p[\"id\"] == job_id), job_id)
"""
if old_b not in u:
    raise SystemExit("screens block B not found")
u = u.replace(old_b, new_b, 1)

old_c = """                                    j_name = next((p[\"name\"] for p in b_type_def.get(\"professions\", []) if p[\"id\"] == j_id), \"ZZZ\")
                                    j_def = next((p for p in b_type_def.get(\"professions\", []) if p[\"id\"] == j_id), None)
"""
new_c = """                                    _rpj2 = getattr(store, \"resolve_profession_for_job\", None)
                                    if callable(_rpj2):
                                        j_name, j_def = _rpj2(b_type_def, j_id)
                                    else:
                                        jlow = str(j_id).strip().lower()
                                        j_def = next((p for p in b_type_def.get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == jlow), None)
                                        j_name = j_def.get(\"name\", \"ZZZ\") if j_def else (\"Rest\" if jlow == \"rest\" else \"ZZZ\")
"""
if old_c not in u:
    raise SystemExit("screens block C not found")
u = u.replace(old_c, new_c, 1)

old_d = """                                $ job_name = \"Unassigned\" if job_id.lower() == \"unassigned\" else (next((p[\"name\"] for p in btype.get(\"professions\", []) if p[\"id\"] == job_id), job_id) if btype else job_id)
"""
new_d = """                                $ _rpj3 = getattr(store, \"resolve_profession_for_job\", None)
                                $ job_name = \"Unassigned\" if job_id.lower() == \"unassigned\" else ((_rpj3(btype, job_id)[0] if callable(_rpj3) and btype else next((p[\"name\"] for p in btype.get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == str(job_id).strip().lower()), job_id)) if btype else job_id)
"""
if old_d not in u:
    raise SystemExit("screens block D not found")
u = u.replace(old_d, new_d, 1)

old_e = """                                    $ profession = next((p for p in btype.get(\"professions\", []) if p[\"id\"] == job_id), None)
"""
new_e = """                                    $ _rpj4 = getattr(store, \"resolve_profession_for_job\", None)
                                    $ profession = (_rpj4(btype, job_id)[1] if callable(_rpj4) and btype else None) or next((p for p in btype.get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == str(job_id).strip().lower()), None)
"""
if old_e not in u:
    raise SystemExit("screens block E not found")
u = u.replace(old_e, new_e, 1)

old_f = """                                $ job_name_with_skill = job_name if avg_skill == 0 or job_id.lower() == \"unassigned\" or job_id == \"rest\" else f\"{job_name} ({avg_skill})\"
"""
new_f = """                                $ job_name_with_skill = job_name if avg_skill == 0 or job_id.lower() == \"unassigned\" or job_id.lower() == \"rest\" else f\"{job_name} ({avg_skill})\"
"""
if old_f not in u:
    raise SystemExit("screens block F not found")
u = u.replace(old_f, new_f, 1)

sc.write_text(u, encoding="utf-8")
print("screens.rpy patched")
