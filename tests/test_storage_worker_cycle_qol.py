"""Contracts for session-only Storage right-worker cycling (Tasks 5–6)."""

import re
import textwrap
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "game" / "scripts" / "core" / "manager_inventory_helpers.rpy"


def init_python_function(source: str, name: str) -> str:
    match = re.search(rf"(?ms)^    def {re.escape(name)}\(.*?(?=^    def |^\S)", source)
    if match is None:
        raise AssertionError(f"init python helper {name} not found")
    return textwrap.dedent(match.group(0))


def make_cycle_harness(workers, filtered_workers=None, visible_screens=(), **screen_vars):
    values = {
        "shop_mode": None,
        "is_transferring": False,
        "left_worker": None,
        "right_worker": False,
        "selected_manager_item": "old manager item",
        "selected_worker_item": "old worker item",
        "selected_manager_index": 3,
        "selected_worker_index": 4,
        "selected_description": "old description",
        "last_row_click_key": "old key",
        "last_row_click_ts": 123.0,
    }
    values.update(screen_vars)
    events = []

    class Store:
        def __init__(self):
            self.workers = workers

        @property
        def left_worker(self):
            return values["left_worker"]

        @property
        def right_worker(self):
            return values["right_worker"]

        @right_worker.setter
        def right_worker(self, value):
            values["right_worker"] = value

    def get_screen_variable(name, screen_name=None):
        return values.get(name)

    def set_screen_variable(name, value, screen_name=None):
        values[name] = value

    def get_screen(name):
        if name == "manager_inventory":
            return SimpleNamespace(scope=values)
        return object() if name in visible_screens else None

    renpy = SimpleNamespace(
        get_screen_variable=get_screen_variable,
        set_screen_variable=set_screen_variable,
        restart_interaction=lambda: events.append("restart"),
        get_screen=get_screen,
    )
    namespace = {
        "renpy": renpy,
        "store": Store(),
        "workers_filtered_by_gender": lambda pool: list(filtered_workers(pool) if callable(filtered_workers) else (filtered_workers if filtered_workers is not None else pool)),
    }
    source = HELPERS.read_text(encoding="utf-8")
    exec(init_python_function(source, "_clear_row_selection"), namespace)
    exec(init_python_function(source, "cycle_manager_inventory_right_worker"), namespace)
    return namespace["cycle_manager_inventory_right_worker"], values, events


def test_cycles_right_worker_forward_and_backward_in_visible_pool():
    a, b, c = ({"name": name} for name in ("A", "B", "C"))
    cycle, values, events = make_cycle_harness([a, b, c], right_worker=b)

    assert cycle(1) is True
    assert values["right_worker"] is c
    assert events == ["restart"]

    assert cycle(-1) is True
    assert values["right_worker"] is b
    assert cycle(-1) is True
    assert values["right_worker"] is a


def test_wraps_at_each_end_of_visible_pool():
    a, b, c = ({"name": name} for name in ("A", "B", "C"))
    cycle, values, _ = make_cycle_harness([a, b, c], right_worker=c)

    assert cycle(1) is True
    assert values["right_worker"] is a

    cycle, values, _ = make_cycle_harness([a, b, c], right_worker=a)
    assert cycle(-1) is True
    assert values["right_worker"] is c


def test_missing_or_filtered_current_selects_directional_end_of_pool():
    a, b, c = ({"name": name} for name in ("A", "B", "C"))
    missing = {"name": "Gone"}
    cycle, values, _ = make_cycle_harness([a, b, c], right_worker=missing)

    assert cycle(1) is True
    assert values["right_worker"] is a

    cycle, values, _ = make_cycle_harness([a, b, c], right_worker=missing)
    assert cycle(-1) is True
    assert values["right_worker"] is c


def test_empty_pool_sets_false_sentinel_even_from_stale_worker():
    stale = {"name": "Filtered Out"}
    cycle, values, events = make_cycle_harness([], right_worker=stale)

    assert cycle(1) is True
    assert values["right_worker"] is False
    assert values["selected_manager_item"] is None
    assert values["last_row_click_key"] is None
    assert events == ["restart"]


def test_left_worker_is_never_a_right_panel_destination():
    a, b, c = ({"name": name} for name in ("A", "B", "C"))
    cycle, values, _ = make_cycle_harness([a, b, c], left_worker=a, right_worker=c)

    assert cycle(1) is True
    assert values["right_worker"] is b


def test_visible_pool_is_recalculated_on_every_keypress():
    a, b, c = ({"name": name} for name in ("A", "B", "C"))
    visible = [[a, b], [b, c]]
    calls = []

    def current_pool(pool):
        calls.append(pool)
        return visible.pop(0)

    cycle, values, _ = make_cycle_harness([a, b, c], filtered_workers=current_pool, right_worker=a)
    assert cycle(1) is True
    assert values["right_worker"] is b
    assert cycle(1) is True
    assert values["right_worker"] is c
    assert calls == [[a, b, c], [a, b, c]]


def test_real_change_clears_selection_and_double_click_state_before_publish():
    a, b = ({"name": name} for name in ("A", "B"))
    cycle, values, _ = make_cycle_harness([a, b], right_worker=a)

    assert cycle(1) is True
    assert values["right_worker"] is b
    for name in ("selected_manager_item", "selected_worker_item", "selected_manager_index", "selected_worker_index", "last_row_click_key"):
        assert values[name] is None
    assert values["selected_description"] == ""
    assert values["last_row_click_ts"] == 0.0


def test_shop_transfer_and_child_modal_are_noops():
    a, b = ({"name": name} for name in ("A", "B"))
    blocked = [{"shop_mode": "shop"}, {"is_transferring": True}]
    blocked.extend({"visible_screens": (name,)} for name in (
        "worker_selection_popup",
        "inventory_filter_popup",
        "screen_intro_popup",
        "confirm",
        "error_popup",
    ))
    for kwargs in blocked:
        cycle, values, events = make_cycle_harness([a, b], right_worker=a, **kwargs)
        assert cycle(1) is False
        assert values["right_worker"] is a
        assert events == []

def test_single_worker_pool_does_not_reset_or_restart():
    a = {"name": "A"}
    cycle, values, events = make_cycle_harness([a], right_worker=a)

    assert cycle(1) is False
    assert values["right_worker"] is a
    assert values["selected_manager_item"] == "old manager item"
    assert events == []


def test_keymap_and_final_screen_keys_use_named_events():
    helpers = HELPERS.read_text(encoding="utf-8")
    screens = (ROOT / "game" / "scripts" / "core" / "screens.rpy").read_text(encoding="utf-8")
    assert 'config.keymap.setdefault("fm_storage_prev", ["ctrl_K_LEFT"])' in helpers
    assert 'config.keymap.setdefault("fm_storage_next", ["ctrl_K_RIGHT"])' in helpers
    cycle_source = init_python_function(helpers, "cycle_manager_inventory_right_worker")
    assert "left_worker = store.left_worker" in cycle_source
    assert 'inventory_screen = renpy.get_screen("manager_inventory")' in cycle_source
    assert 'screen_scope.get("shop_mode")' in cycle_source
    assert 'get_screen_variable("shop_mode"' not in cycle_source
    assert "right_worker = store.right_worker" in cycle_source
    assert "store.right_worker = next_worker" in cycle_source
    assert 'get_screen_variable("left_worker"' not in cycle_source
    assert 'get_screen_variable("right_worker"' not in cycle_source
    assert '_clear_row_selection("manager_inventory")' in cycle_source
    assert 'set_screen_variable("right_worker"' not in cycle_source
    manager = re.search(r"(?s)screen manager_inventory\b.*?(?=^screen worker_selection_popup)", screens, re.M).group(0)
    assert manager.rstrip().endswith('key "fm_storage_next" action Function(cycle_manager_inventory_right_worker, 1)')
    assert 'key "fm_storage_prev" action Function(cycle_manager_inventory_right_worker, -1)' in manager


def test_global_escape_reads_manager_inventory_parameters_from_live_scope():
    helpers = HELPERS.read_text(encoding="utf-8")
    close_source = init_python_function(helpers, "close_manager_inventory")
    assert 'inventory_screen = renpy.get_screen("manager_inventory")' in close_source
    assert 'screen_scope.get("return_to_worker")' in close_source
    assert 'get_screen_variable("return_to_worker"' not in close_source
