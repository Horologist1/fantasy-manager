"""Worker Orientation toggle rules: image remap + trait reconciliation.

Spec: docs/superpowers/specs/2026-08-24-orientation-forced-images-design.md

A worker whose Gay/Lesbian trait came from the toggle carries
worker["orientation_forced"] = "force" | "rolled". Marked workers search
homo/les art for sexual acts; authored workers (no marker) are untouched.
"""

# Sexual skills whose image lookup is remapped for marked workers.
# Striptease deliberately excluded (solo act, orientation-neutral);
# non-sexual skills (combat, clever, charm, service...) are never remapped.
REMAP_SKILLS = frozenset(
    {"sex", "anal", "bdsm", "hand", "oral", "special", "group", "extreme"}
)

# Marker values recorded in worker["orientation_forced"].
MARKER_FORCE = "force"    # granted by Force mode - reverts when the toggle drops
MARKER_ROLLED = "rolled"  # rolled at generation under "On" - permanent


def remap_image_skill(skill_name_for_search, gender, marker):
    """Return the (possibly remapped) skill name used for image pattern search.

    skill_name_for_search: lowercase name from get_skill_name_for_images.
    gender: worker gender ("male"/"female", any casing).
    marker: worker.get("orientation_forced") - None/""/falsy means unmarked.
    Identity for unmarked workers and non-remapped skills.
    """
    if not marker or not skill_name_for_search:
        return skill_name_for_search
    skill = str(skill_name_for_search).lower()
    if skill == "homo":
        # Hetero-client story on a marked worker: show the folder's real hetero art.
        return "sex"
    if skill in REMAP_SKILLS:
        return "les" if str(gender).strip().lower() == "female" else "gay"
    return skill_name_for_search


def toggle_action(mode, has_trait, marker):
    """Reconciliation decision for one worker against their gender's toggle mode.

    mode: "off" | "enable" | "force" (persistent orientation_*_mode).
    has_trait: worker currently has the orientation trait.
    marker: None | "force" | "rolled" (worker.get("orientation_forced")).
    Returns "add" (grant trait + force marker), "remove" (drop toggle-granted
    trait + clear marker), or None (no change). "rolled" is never removed.
    """
    if mode == "force" and not has_trait:
        return "add"
    if marker == MARKER_FORCE and mode != "force":
        return "remove"
    return None
