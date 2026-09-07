"""Structural pickle/rollback safety gate for touched Ren'Py code."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "game" / "scripts" / "core" / "screens.rpy"
TRAINING = ROOT / "game" / "scripts" / "workers" / "worker_training.rpy"
HELPERS = ROOT / "game" / "scripts" / "core" / "manager_inventory_helpers.rpy"


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _python_bodies(source: str, owner_kind: str, owner_names=None):
    """Yield Python block bodies belonging to selected screen/label owners; init blocks are excluded."""
    lines = source.splitlines()
    owner = None
    owner_name = None
    owner_indent = -1
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        indent = _indent(line)
        top = re.match(r"^(screen|label)\s+([A-Za-z0-9_]+)", line)
        if top:
            owner, owner_name, owner_indent = top.group(1), top.group(2), indent
        elif line and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
            owner = owner_name = None
        if owner == owner_kind and (owner_names is None or owner_name in owner_names) and stripped == "python:":
            block_indent = indent
            body = []
            i += 1
            while i < len(lines):
                candidate = lines[i]
                if candidate.strip() and _indent(candidate) <= block_indent:
                    i -= 1
                    break
                body.append(candidate)
                i += 1
            yield owner_name, body
        i += 1


def find_pickle_hazards(source: str, screen_names=("manager_inventory", "worker_details")):
    hazards = []
    for owner, body in _python_bodies(source, "screen", set(screen_names)):
        local_callables = set()
        for line in body:
            stripped = line.strip()
            match = re.match(r"(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
            if match:
                local_callables.add(match.group(1))
                hazards.append((owner, "screen-local-callable", stripped))
        for line in body:
            stripped = line.strip()
            assignment = re.match(r"store\.[A-Za-z_][A-Za-z0-9_]*\s*=\s*(.+)", stripped)
            if not assignment:
                continue
            rhs = assignment.group(1).strip()
            if rhs.startswith("lambda") or rhs in local_callables or re.search(r"\([^\n]*\bfor\b[^\n]*\)", rhs):
                hazards.append((owner, "persisted-callable-or-generator", stripped))

    for owner, body in _python_bodies(source, "label", None):
        for line in body:
            stripped = line.strip()
            if re.match(r"(?:from\s+\S+\s+)?import\s+", stripped) or stripped.startswith("import "):
                hazards.append((owner, "label-import", stripped))
            if re.match(r"(?:def|class)\s+", stripped):
                hazards.append((owner, "label-local-callable", stripped))
            if stripped.startswith("with "):
                hazards.append((owner, "label-context-manager", stripped))
            if re.match(r"store\.[A-Za-z_][A-Za-z0-9_]*\s*=\s*lambda\b", stripped):
                hazards.append((owner, "persisted-callable-or-generator", stripped))
            if re.match(r"store\.[A-Za-z_][A-Za-z0-9_]*\s*=\s*\([^\n]*\bfor\b", stripped):
                hazards.append((owner, "persisted-callable-or-generator", stripped))
    return hazards


def test_scanner_negative_controls_have_teeth():
    poisoned = '''
screen manager_inventory():
    python:
        def local_action():
            return 1
        store.bad_action = local_action

label poisoned_label:
    python:
        import os
        with renpy.file("x") as handle:
            store.bad_generator = (x for x in handle)
        store.bad_lambda = lambda: 1
'''
    hazards = find_pickle_hazards(poisoned)
    kinds = {kind for _, kind, _ in hazards}
    assert "screen-local-callable" in kinds
    assert "persisted-callable-or-generator" in kinds
    assert "label-import" in kinds
    assert "label-context-manager" in kinds


def test_touched_runtime_blocks_have_no_pickle_hazards():
    hazards = []
    hazards.extend(find_pickle_hazards(SCREENS.read_text(encoding="utf-8")))
    hazards.extend(find_pickle_hazards(TRAINING.read_text(encoding="utf-8")))
    assert hazards == []


def test_init_python_helpers_are_not_misclassified_as_runtime_locals():
    source = HELPERS.read_text(encoding="utf-8")
    assert "init python:" in source
    assert "def cycle_manager_inventory_right_worker" in source
    assert find_pickle_hazards(source) == []


def test_repeat_completion_marker_accepts_only_primitives():
    source = TRAINING.read_text(encoding="utf-8")
    marker = re.search(r"(?ms)^    def mark_training_outcome_complete\(.*?(?=^    def |^\S)", source)
    assert marker
    assert "isinstance(interaction_id, (str, int, float, bool))" in marker.group(0)
    assert "worker" not in marker.group(0)
    assert "interaction.get" not in marker.group(0)
