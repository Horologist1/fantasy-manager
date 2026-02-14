# rename_discipline_and_audit.py
# 1) Rename old discipline image names to new names in all worker folders (except succubus)
# 2) Full audit: list every file and check against expected interaction images

import os
import json

BASE = os.path.join(os.path.dirname(__file__), "..", "game", "images", "workers")
INTERACTIONS_JSON = os.path.join(os.path.dirname(__file__), "..", "game", "data", "interactions", "interactions_structured.json")

RENAMES = [
    ("discipline_level3_oral_discipline_lord.png", "discipline_oral_lord.png"),
    ("discipline_level3_oral_discipline_lady.png", "discipline_oral_lady.png"),
    ("discipline_level4_bdsm_conditioning_lord.png", "discipline_bdsm_lord.png"),
    ("discipline_level4_bdsm_conditioning_lady.png", "discipline_bdsm_lady.png"),
]

# All unique image names the game expects (from interactions_structured.json)
EXPECTED_IMAGES = {
    "discipline_etiquette", "discipline_inspection", "discipline_correction",
    "discipline_private_punishment", "discipline_discretion", "discipline_oral_lord",
    "discipline_oral_lady", "discipline_conditioning", "discipline_bdsm_lord",
    "discipline_bdsm_lady", "discipline_finale", "discipline_sell",
    "romance_flirt", "romance_intimate_dinner", "romance_private",
    "romance_passionate_night_lord_female", "romance_passionate_night_lord_male",
    "romance_passionate_night_lady_female", "romance_passionate_night_lady_male",
    "romance_quality_time_lord_female", "romance_quality_time_lord_male",
    "romance_quality_time_lady_female", "romance_quality_time_lady_male",
    "romance_perfect_night_lord_female", "romance_perfect_night_lord_male",
    "romance_perfect_night_lady_female", "romance_perfect_night_lady_male",
    "romance_confess_feelings_lord_female", "romance_confess_feelings_lord_male",
    "romance_confess_feelings_lady_female", "romance_confess_feelings_lady_male",
    "friendship_chat", "friendship_heart", "friendship_joy_gift", "friendship_perfect", "friendship_confidants",
    "joy_gift", "joy_celebration", "joy_festival", "joy_perfect",
    "romance_male", "romance_female", "joy_male", "joy_female", "friendship", "obedience",
}

def file_base_matches(fname, base):
    """Check if filename (without extension) equals base or starts with base + ' (' """
    name, _ = os.path.splitext(fname)
    name_lower = name.lower().strip()
    base_lower = base.lower()
    if name_lower == base_lower:
        return True
    if name_lower.startswith(base_lower + " ("):
        return True
    return False

def has_match(files, base):
    """True if any file in list matches the expected base name."""
    return any(file_base_matches(f, base) for f in files)

def main():
    if not os.path.isdir(BASE):
        print("Base dir not found:", BASE)
        return

    # List folders (exclude succubus)
    folders = [d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)) and d.lower() != "succubus"]
    folders.sort()

    print("=== 1) RENAMING old discipline files ===\n")
    for folder in folders:
        dirpath = os.path.join(BASE, folder)
        for old_name, new_name in RENAMES:
            oldpath = os.path.join(dirpath, old_name)
            if os.path.isfile(oldpath):
                newpath = os.path.join(dirpath, new_name)
                try:
                    os.rename(oldpath, newpath)
                    print(f"  {folder}: {old_name} -> {new_name}")
                except Exception as e:
                    print(f"  {folder}: ERROR renaming {old_name}: {e}")

    print("\n=== 2) FULL AUDIT: listing all files per folder ===\n")
    report_lines = []
    report_lines.append("# Auditoría completa de imágenes de interacciones")
    report_lines.append("# Carpeta base: game/images/workers/ (excl. succubus)\n")

    for folder in folders:
        dirpath = os.path.join(BASE, folder)
        try:
            all_files = os.listdir(dirpath)
        except Exception as e:
            report_lines.append(f"## {folder}\nError: {e}\n")
            continue
        all_files.sort()
        report_lines.append(f"## {folder} ({len(all_files)} archivos)")
        report_lines.append("")
        # Discipline
        disc_expected = [
            "discipline_etiquette", "discipline_inspection", "discipline_correction",
            "discipline_private_punishment", "discipline_discretion", "discipline_oral_lord",
            "discipline_oral_lady", "discipline_conditioning", "discipline_bdsm_lord",
            "discipline_bdsm_lady", "discipline_finale", "discipline_sell",
        ]
        missing_disc = [b for b in disc_expected if not has_match(all_files, b)]
        present_disc = [b for b in disc_expected if has_match(all_files, b)]
        report_lines.append("### Discipline")
        report_lines.append(f"- Presentes ({len(present_disc)}): " + ", ".join(present_disc))
        if missing_disc:
            report_lines.append(f"- **Faltan ({len(missing_disc)}):** " + ", ".join(missing_disc))
        report_lines.append("")
        # Romance (main bases)
        romance_bases = [
            "romance_flirt", "romance_intimate_dinner", "romance_private",
            "romance_passionate_night_lord_female", "romance_passionate_night_lord_male",
            "romance_passionate_night_lady_female", "romance_passionate_night_lady_male",
            "romance_quality_time_lord_female", "romance_quality_time_lord_male",
            "romance_quality_time_lady_female", "romance_quality_time_lady_male",
            "romance_perfect_night_lord_female", "romance_perfect_night_lord_male",
            "romance_perfect_night_lady_female", "romance_perfect_night_lady_male",
            "romance_confess_feelings_lord_female", "romance_confess_feelings_lord_male",
            "romance_confess_feelings_lady_female", "romance_confess_feelings_lady_male",
            "romance_male", "romance_female",
        ]
        missing_rom = [b for b in romance_bases if not has_match(all_files, b)]
        present_rom = [b for b in romance_bases if has_match(all_files, b)]
        report_lines.append("### Romance")
        report_lines.append(f"- Presentes ({len(present_rom)}): " + ", ".join(present_rom))
        if missing_rom:
            report_lines.append(f"- **Faltan ({len(missing_rom)}):** " + ", ".join(missing_rom))
        report_lines.append("")
        # Friendship
        friend_bases = ["friendship_chat", "friendship_heart", "friendship_joy_gift", "friendship_perfect", "friendship_confidants", "friendship"]
        missing_fr = [b for b in friend_bases if not has_match(all_files, b)]
        report_lines.append("### Friendship")
        report_lines.append(f"- Presentes: " + ", ".join(b for b in friend_bases if has_match(all_files, b)))
        if missing_fr:
            report_lines.append(f"- **Faltan:** " + ", ".join(missing_fr))
        report_lines.append("")
        # Joy
        joy_bases = ["joy_gift", "joy_celebration", "joy_festival", "joy_perfect", "joy_male", "joy_female"]
        missing_joy = [b for b in joy_bases if not has_match(all_files, b)]
        report_lines.append("### Joy")
        report_lines.append(f"- Presentes: " + ", ".join(b for b in joy_bases if has_match(all_files, b)))
        if missing_joy:
            report_lines.append(f"- **Faltan:** " + ", ".join(missing_joy))
        report_lines.append("")
        # Lista completa de archivos (solo nombres que contienen discipline, romance, friendship, joy, obedience)
        relevant = [f for f in all_files if any(x in f.lower() for x in ("discipline", "romance", "friendship", "joy", "obedience"))]
        report_lines.append("### Archivos relevantes en carpeta")
        for f in relevant:
            report_lines.append(f"  - {f}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "interaction_images_audit_full.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Report written to {out_path}")

if __name__ == "__main__":
    main()
