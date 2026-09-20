"""Literal worker names must not act as regex replacement syntax in events."""
import re
import textwrap
from pathlib import Path

import pytest

SOURCE = (Path(__file__).resolve().parents[1] / "game/scripts/events/events.rpy").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["Aelis", r"Guest\Q", r"Guest\1", r"Guest\n", "[Guest] {friend}"])
def test_selected_worker_name_is_literal_and_does_not_mangle_plural(name):
    helper = re.search(r"(?ms)^    def event_text_with_selected_worker\(.*?(?=^    def )", SOURCE)
    env = {"re": re}
    exec(textwrap.dedent(helper.group()), env)
    assert env["event_text_with_selected_worker"](
        "the worker joins the workers. [event_worker] / [acting_worker]", name
    ) == f"{name} joins the workers. {name} / {name}"


def test_worker_selection_uses_literal_name_helper():
    assert "store.temp_narrator_text = event_text_with_selected_worker(store.temp_narrator_text, acting_worker_name)" in SOURCE
