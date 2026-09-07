"""Source contracts for truthful, positioned help pages (Task 6b)."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"


def screen_block(source: str, name: str) -> str:
    match = re.search(rf"(?m)^screen {re.escape(name)}\b[^\n]*:\n", source)
    assert match, f"screen {name} not found"
    following = re.search(r"(?m)^screen [A-Za-z0-9_]+", source[match.end():])
    end = match.end() + following.start() if following else len(source)
    return source[match.start():end]


def test_help_removes_rollback_and_documents_storage_and_scrolling():
    source = SCREENS.read_text(encoding="utf-8")
    keyboard = screen_block(source, "keyboard_help")
    mouse = screen_block(source, "mouse_help")

    assert "Rolls back" not in keyboard + mouse
    assert "Rolls forward" not in keyboard + mouse
    assert "Page Up" not in keyboard
    assert "Page Down" not in keyboard
    assert '(_("Ctrl+Left Arrow"), _("Previous button; previous worker in Storage."))' in keyboard
    assert '(_("Ctrl+Right Arrow"), _("Next button; next worker in Storage."))' in keyboard
    assert '(_("BackSpace"), _("Closes most game screens."))' in keyboard
    assert "Mouse Wheel Up" not in mouse
    assert "Mouse Wheel Down" not in mouse
    assert '(_("Mouse Wheel"), _("Scrolls lists and panels."))' in mouse


def test_help_uses_fixed_positioned_columns_and_compact_labels():
    source = SCREENS.read_text(encoding="utf-8")
    keyboard = screen_block(source, "keyboard_help")
    mouse = screen_block(source, "mouse_help")
    style = re.search(r"(?ms)^style help_label:\n(.*?)(?=^style |^screen |^#{5,})", source)
    assert style

    for block in (keyboard, mouse):
        assert "fixed:" in block
        assert "xsize 1600" in block
        assert "xpos 90" in block
        assert "xpos 0" not in block
        assert "xpos 770" in block
        assert "xalign 0.5" not in block
        assert "xoffset -110" not in block
    assert "xsize 240" in style.group(1)
    assert "right_padding 30" in style.group(1)
