from pathlib import Path
sc = Path(r"C:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager\game\scripts\core\screens.rpy")
u = sc.read_text(encoding="utf-8")

def rpj_lines(indent, btype_expr, job_expr):
    pad = " " * indent
    return (
        pad + "_rpj = getattr(store, \"resolve_profession_for_job\", None)\n"
        + pad + "if callable(_rpj):\n"
        + pad + "    job_name, _pj_unused = _rpj(" + btype_expr + ", " + job_expr + ")\n"
        + pad + "else:\n"
        + pad + "    job_name = next((p[\"name\"] for p in " + btype_expr + ".get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == str(" + job_expr + ").strip().lower()), " + job_expr + ")\n"
    )

old_a = "                                    job_name = next((p[\"name\"] for p in btype.get(\"professions\", []) if p[\"id\"] == job_id), job_id)\n"
new_a = rpj_lines(36, "btype", "job_id")
count_a = u.count(old_a)
if count_a != 2:
    raise SystemExit("expected 2 occurrences of job_name=next..., got %d" % count_a)
u = u.replace(old_a, new_a)

old_c = (
    "                                    j_name = next((p[\"name\"] for p in b_type_def.get(\"professions\", []) if p[\"id\"] == j_id), \"ZZZ\")\n"
    "                                    j_def = next((p for p in b_type_def.get(\"professions\", []) if p[\"id\"] == j_id), None)\n"
)
new_c = (
    "                                    _rpj2 = getattr(store, \"resolve_profession_for_job\", None)\n"
    "                                    if callable(_rpj2):\n"
    "                                        j_name, j_def = _rpj2(b_type_def, j_id)\n"
    "                                    else:\n"
    "                                        jlow = str(j_id).strip().lower()\n"
    "                                        j_def = next((p for p in b_type_def.get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == jlow), None)\n"
    "                                        j_name = j_def.get(\"name\", \"ZZZ\") if j_def else (\"Rest\" if jlow == \"rest\" else \"ZZZ\")\n"
)
if old_c not in u:
    raise SystemExit("sort key block not found")
u = u.replace(old_c, new_c, 1)

old_d = "                                $ job_name = \"Unassigned\" if job_id.lower() == \"unassigned\" else (next((p[\"name\"] for p in btype.get(\"professions\", []) if p[\"id\"] == job_id), job_id) if btype else job_id)\n"
new_d = (
    "                                $ _rpj3 = getattr(store, \"resolve_profession_for_job\", None)\n"
    "                                $ job_name = \"Unassigned\" if job_id.lower() == \"unassigned\" else ((_rpj3(btype, job_id)[0] if callable(_rpj3) and btype else next((p[\"name\"] for p in btype.get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == str(job_id).strip().lower()), job_id)) if btype else job_id)\n"
)
if old_d not in u:
    raise SystemExit("job_name dollar block not found")
u = u.replace(old_d, new_d, 1)

old_e = "                                    $ profession = next((p for p in btype.get(\"professions\", []) if p[\"id\"] == job_id), None)\n"
new_e = (
    "                                    $ _rpj4 = getattr(store, \"resolve_profession_for_job\", None)\n"
    "                                    $ profession = ((_rpj4(btype, job_id)[1] if callable(_rpj4) else None) or next((p for p in btype.get(\"professions\", []) if str(p.get(\"id\", \"\")).strip().lower() == str(job_id).strip().lower()), None)) if btype else None\n"
)
if old_e not in u:
    raise SystemExit("profession block not found")
u = u.replace(old_e, new_e, 1)

old_f = "                                $ job_name_with_skill = job_name if avg_skill == 0 or job_id.lower() == \"unassigned\" or job_id == \"rest\" else f\"{job_name} ({avg_skill})\"\n"
new_f = "                                $ job_name_with_skill = job_name if avg_skill == 0 or job_id.lower() == \"unassigned\" or job_id.lower() == \"rest\" else f\"{job_name} ({avg_skill})\"\n"
if old_f not in u:
    raise SystemExit("job_name_with_skill block not found")
u = u.replace(old_f, new_f, 1)

sc.write_text(u, encoding="utf-8")
print("screens.rpy patched ok, occurrences A replaced:", count_a)
