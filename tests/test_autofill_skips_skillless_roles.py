"""Auto-fill must not fill roles that earn nothing.

The goal-driven autoplayer saw the Governor's Castle end-game staffed with 13
"Prisoner" workers (9 seats + 4 from level 5): a role with no skills and no
earnings, filled first-come by Auto-fill and paying comfort every day.
"""
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "game/scripts/core/gameplay_improvements.rpy").read_text(encoding="utf-8")


def test_autofill_role_list_skips_roles_without_skills():
    head = 'if pid in ("manager", "rest") or pname.strip().lower() in ("manager", "rest"):'
    assert head in SOURCE, "the Auto-fill role loop moved; update this contract"
    after = SOURCE.split(head, 1)[1][:600]
    assert 'if not (p.get("skills") or []):' in after, (
        "Auto-fill no longer skips skill-less roles: castle Prisoner seats get filled again")
