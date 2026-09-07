import json
import re
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
EVENTS_ROOT = ROOT / "game" / "data" / "events"
SCRIPTS_ROOT = ROOT / "game" / "scripts"


def load_events():
    events = []
    for path in sorted(EVENTS_ROOT.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list):
            continue
        for index, event in enumerate(payload):
            if isinstance(event, dict):
                events.append((path, index, event))
    return events


def walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def collect_event_flag_producers(events):
    producers = set()
    for _path, _index, event in events:
        completion_flag = event.get("completion_timestamp_flag")
        if isinstance(completion_flag, str) and completion_flag.strip():
            producers.add(completion_flag.strip())
        for mapping in walk_dicts(event):
            event_flags = mapping.get("event_flags")
            if isinstance(event_flags, dict):
                producers.update(
                    name for name, value in event_flags.items()
                    if isinstance(name, str) and value is not None
                )
            timestamp_flags = mapping.get("set_timestamp_flags")
            if isinstance(timestamp_flags, str):
                producers.add(timestamp_flags)
            elif isinstance(timestamp_flags, list):
                producers.update(
                    name for name in timestamp_flags if isinstance(name, str) and name
                )

    # Flags written directly by authored Ren'Py flows are valid producers too.
    for path in sorted(SCRIPTS_ROOT.rglob("*.rpy")):
        source = path.read_text(encoding="utf-8-sig")
        producers.update(re.findall(r'event_flags\s*\[\s*["\']([^"\']+)["\']\s*\]\s*=', source))
        for update_body in re.findall(r'event_flags\.update\s*\(\s*\{(.*?)\}\s*\)', source, re.DOTALL):
            producers.update(re.findall(r'["\']([^"\']+)["\']\s*:', update_body))
    return producers


def extract_init_function(path, function_name, namespace):
    lines = path.read_text(encoding="utf-8-sig").splitlines(True)
    marker = f"    def {function_name}("
    try:
        start = next(index for index, line in enumerate(lines) if line.startswith(marker))
    except StopIteration as exc:
        raise AssertionError(f"Missing live function: {function_name}") from exc
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("    def ")
        ),
        len(lines),
    )
    exec(textwrap.dedent("".join(lines[start:end])), namespace)
    return namespace[function_name]


class EventFlagContractTests(unittest.TestCase):
    def test_required_event_flags_have_a_real_event_flag_producer(self):
        events = load_events()
        producers = collect_event_flag_producers(events)
        missing = []
        for path, index, event in events:
            required_flags = event.get("required_flags") or {}
            if not isinstance(required_flags, dict):
                continue
            for flag_name in required_flags:
                if flag_name not in producers:
                    missing.append(
                        f"{path.relative_to(ROOT)}[{index}] {event.get('id')}: {flag_name}"
                    )

        self.assertEqual(
            [],
            missing,
            "required_flags read store.event_flags; every required key must have a "
            "writer in that same dictionary. Use an explicit store-value condition "
            "for normal store attributes. Missing producers:\n" + "\n".join(missing),
        )


class EventEffectContractTests(unittest.TestCase):
    def test_building_wide_energy_effect_changes_only_workers_in_that_building(self):
        events = {
            event.get("id"): event
            for _path, _index, event in load_events()
            if event.get("id")
        }
        effect = events["brothel_discreet_noble_party"]["choices"][0]["effect"]
        workers = [
            {"name": "A", "assigned_building": "Building 2", "energy": 40},
            {"name": "B", "assigned_building": "Building 2", "energy": 5},
            {"name": "C", "assigned_building": "Building 1", "energy": 30},
        ]
        namespace = {"store": SimpleNamespace(workers=workers)}
        apply_effect = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "apply_building_workers_energy_effect",
            namespace,
        )

        applied = apply_effect(effect, "Building 2")

        self.assertEqual([30, 0, 30], [worker["energy"] for worker in workers])
        self.assertEqual(
            {"building_worker_energy": -10, "building_worker_energy_count": 2},
            applied,
        )

    def test_building_energy_uses_object_identity_when_buildings_have_equal_data(self):
        building_one = {"type": "brothel"}
        building_two = {"type": "brothel"}
        workers = [
            {"name": "A", "assigned_building": "Building 1", "energy": 50},
            {"name": "B", "assigned_building": "Building 2", "energy": 50},
        ]
        store = SimpleNamespace(workers=workers, current_affected_building=None)
        apply_effect = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "apply_building_workers_energy_effect",
            {
                "store": store,
                "available_buildings": {
                    "Building 1": building_one,
                    "Building 2": building_two,
                },
            },
        )

        apply_effect({"building_worker_energy": -10}, building_two)

        self.assertEqual([50, 40], [worker["energy"] for worker in workers])

    def test_building_energy_accepts_space_and_underscore_key_aliases(self):
        building = {"type": "brothel"}
        worker = {"name": "A", "assigned_building": "Building 2", "energy": 50}
        store = SimpleNamespace(workers=[worker], current_affected_building=None)
        apply_effect = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "apply_building_workers_energy_effect",
            {"store": store, "available_buildings": {"Building_2": building}},
        )

        apply_effect({"building_worker_energy": -10}, building)

        self.assertEqual(40, worker["energy"])

    def test_apply_effects_routes_building_worker_energy_to_its_handler(self):
        source = (ROOT / "game" / "scripts" / "script.rpy").read_text(
            encoding="utf-8-sig"
        )
        apply_effects_body = source.split("    def apply_effects(", 1)[1].split(
            "\n    def ", 1
        )[0]
        self.assertIn(
            "apply_building_workers_energy_effect(effect_dict, building)",
            apply_effects_body,
        )

    def test_building_wide_joy_effect_changes_only_workers_in_that_building(self):
        event = next(
            event
            for _path, _index, event in load_events()
            if event.get("id") == "brothel_exotic_oils_merchant"
        )
        effect = event["choices"][0]["effect"]
        workers = [
            {"name": "A", "assigned_building": "Building 2", "joy": 20},
            {"name": "B", "assigned_building": "Building 2", "joy": 98},
            {"name": "C", "assigned_building": "Building 1", "joy": 40},
        ]
        store = SimpleNamespace(workers=workers, current_affected_building="Building 2")
        apply_building_workers_joy_effect = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "apply_building_workers_joy_effect",
            {"store": store, "available_buildings": {}},
        )

        applied = apply_building_workers_joy_effect(effect)

        self.assertEqual([25, 100, 40], [worker["joy"] for worker in workers])
        self.assertEqual(
            {"building_worker_joy": 5, "building_worker_joy_count": 2},
            applied,
        )

    def test_building_joy_uses_object_identity_when_buildings_have_equal_data(self):
        building_one = {"type": "brothel"}
        building_two = {"type": "brothel"}
        workers = [
            {"name": "A", "assigned_building": "Building 1", "joy": 20},
            {"name": "B", "assigned_building": "Building 2", "joy": 20},
        ]
        store = SimpleNamespace(workers=workers, current_affected_building=None)
        apply_effect = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "apply_building_workers_joy_effect",
            {
                "store": store,
                "available_buildings": {
                    "Building 1": building_one,
                    "Building 2": building_two,
                },
            },
        )

        apply_effect({"building_worker_joy": 5}, building_two)

        self.assertEqual([20, 25], [worker["joy"] for worker in workers])

    def test_building_joy_accepts_space_and_underscore_key_aliases(self):
        building = {"type": "brothel"}
        worker = {"name": "A", "assigned_building": "Building 2", "joy": 20}
        store = SimpleNamespace(workers=[worker], current_affected_building=None)
        apply_effect = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "apply_building_workers_joy_effect",
            {"store": store, "available_buildings": {"Building_2": building}},
        )

        apply_effect({"building_worker_joy": 5}, building)

        self.assertEqual(25, worker["joy"])

    def test_apply_effects_routes_building_worker_joy_to_its_handler(self):
        source = (ROOT / "game" / "scripts" / "script.rpy").read_text(
            encoding="utf-8-sig"
        )
        apply_effects_body = source.split("    def apply_effects(", 1)[1].split(
            "\n    def ", 1
        )[0]
        self.assertIn(
            "apply_building_workers_joy_effect(effect_dict, building)",
            apply_effects_body,
        )


class RecruitmentEventContractTests(unittest.TestCase):
    def test_dead_unique_workers_can_reenter_until_resurrection_exists(self):
        dead_unique = {
            "name": "Dead Unique",
            "unique": True,
            "monster": False,
            "recruitment_locked": False,
            "nsfw": False,
            "gender": "female",
        }
        generated = {
            "name": "Generated Replacement",
            "procedural": True,
            "gender": "female",
        }
        store = SimpleNamespace(workers=[])
        namespace = {
            "store": store,
            "persistent": SimpleNamespace(
                worker_gender_filter="both",
                nsfw_enabled=False,
            ),
            "load_workers": lambda **_kwargs: [dead_unique],
            "worker_recruit_state_ok": lambda _worker: True,
            "content_object_is_restricted": lambda _worker: False,
            "is_worker_dead": lambda name: name == "Dead Unique",
            "spawn_new_worker": lambda **_kwargs: dict(generated),
            "ensure_worker_defaults": lambda _worker: None,
            "renpy": SimpleNamespace(log=lambda _message: None),
        }
        load_recruit_workers = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "load_recruit_workers",
            namespace,
        )

        candidates = load_recruit_workers()

        self.assertEqual(
            ["Dead Unique"],
            [w["name"] for w in candidates],
        )


if __name__ == "__main__":
    unittest.main()
