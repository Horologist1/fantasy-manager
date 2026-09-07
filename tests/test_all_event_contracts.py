import json
import re
import textwrap
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
EVENTS_ROOT = ROOT / "game" / "data" / "events"
SCRIPTS_ROOT = ROOT / "game" / "scripts"


def load_events():
    rows = []
    for path in sorted(EVENTS_ROOT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list):
            raise AssertionError(f"{path}: event JSON root must be a list")
        for event in data:
            if isinstance(event, dict):
                rows.append((path, event))
    return rows


def iter_effect_blocks(effect):
    if not isinstance(effect, dict):
        return
    yield effect
    for branch in ("success", "failure"):
        nested = effect.get(branch)
        if isinstance(nested, dict):
            yield from iter_effect_blocks(nested)


def iter_conditions(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"condition", "start_when", "stop_when"} and isinstance(nested, str):
                yield nested
            yield from iter_conditions(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_conditions(nested)


def extract_init_function(path, function_name, namespace):
    source = path.read_text(encoding="utf-8-sig")
    marker = f"    def {function_name}("
    start = source.index(marker)
    remainder = source[start:]
    next_function = remainder.find("\n    def ", len(marker))
    block = remainder if next_function < 0 else remainder[:next_function]
    exec(textwrap.dedent(block), namespace)
    return namespace[function_name]


EVENT_ROWS = load_events()
EVENTS_BY_ID = {event["id"]: event for _path, event in EVENT_ROWS}
MAIN_ROWS = [(path, event) for path, event in EVENT_ROWS if "recruit" not in path.parts]
RECRUIT_ROWS = [(path, event) for path, event in EVENT_ROWS if "recruit" in path.parts]


class EventCatalogContractTests(unittest.TestCase):
    EVENT_KEYS = {
        "_disabled", "always_available", "arc_id", "arc_kind", "arc_stage", "stage",
        "days_after_previous", "background_image", "building_type", "choices",
        "completion_timestamp_flag", "conditions", "cooldown_days", "description",
        "description_pages", "dialogue", "event_music", "event_probability", "event_type",
        "excluded_flags", "failure_image", "forbidden_active_professions", "guaranteed",
        "id", "limited", "max_occurrences", "nsfw", "player_gender_requirement", "priority",
        "random_worker", "required_active_professions", "required_building_worker_min_skill",
        "required_building_worker_skill", "required_building_worker_traits", "required_flags",
        "required_store_value", "success_image", "unlimited", "weight", "worker_filter",
        "worker_gender_requirement", "worker_name", "worker_progress", "worker_selection",
        "event_progress",
        "specific_worker_images", "effect_worker_filter", "recovery_priority",
    }
    CHOICE_KEYS = {
        "blocked_message", "condition", "conditions", "effect", "effect_worker_filter",
        "image_skill", "message", "message_failure", "message_failure_worker_effect_skipped",
        "message_pages", "message_success", "option", "outcome_override", "required_trait",
        "required_traits", "excluded_traits", "restrict_worker_effects_to_filter",
        "success_image", "failure_image", "threshold", "trait_visibility",
    }

    def test_event_and_choice_keys_are_declared_not_silent_typos(self):
        errors = []
        for path, event in EVENT_ROWS:
            unknown_event_keys = sorted(set(event) - self.EVENT_KEYS)
            if unknown_event_keys:
                errors.append(f"{path.name}:{event.get('id')}: event keys {unknown_event_keys}")
            for choice_index, choice in enumerate(event.get("choices") or []):
                if not isinstance(choice, dict):
                    errors.append(f"{path.name}:{event.get('id')}: choice[{choice_index}] is not an object")
                    continue
                unknown_choice_keys = sorted(set(choice) - self.CHOICE_KEYS)
                if unknown_choice_keys:
                    errors.append(
                        f"{path.name}:{event.get('id')}:choice[{choice_index}]: keys {unknown_choice_keys}"
                    )
        self.assertFalse(errors, "\n".join(errors))

    def test_nested_gate_keys_are_declared_not_silent_typos(self):
        allowed = {
            "conditions": {"start_when", "stop_when"},
            "worker_filter": {"min_combat", "traits_required", "traits_excluded"},
            "worker_progress": {"min_level", "any_skills"},
            "event_progress": {"min_level", "any_skills"},
            "effect_worker_filter": {
                "required_active_professions", "forbidden_active_professions",
                "required_traits", "required_trait", "excluded_traits", "min_skill",
                "required_building_worker_min_skill", "skill_name",
                "required_building_worker_skill",
            },
        }
        errors = []
        for path, event in EVENT_ROWS:
            for key, valid_keys in allowed.items():
                value = event.get(key)
                if isinstance(value, dict):
                    unknown = sorted(set(value) - valid_keys)
                    if unknown:
                        errors.append(f"{path.name}:{event['id']}:{key}: {unknown}")
            for choice_index, choice in enumerate(event.get("choices") or []):
                if not isinstance(choice, dict):
                    continue
                for key in ("conditions", "effect_worker_filter"):
                    value = choice.get(key)
                    if isinstance(value, dict):
                        unknown = sorted(set(value) - allowed[key])
                        if unknown:
                            errors.append(
                                f"{path.name}:{event['id']}:choice[{choice_index}]:{key}: {unknown}"
                            )
        self.assertFalse(errors, "\n".join(errors))

    def test_all_event_files_are_lists_and_event_ids_are_global_unique(self):
        ids = defaultdict(list)
        for path in sorted(EVENTS_ROOT.rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(data, list):
                self.fail(f"{path}: event JSON root must be a list")
            for event in data:
                self.assertIsInstance(event, dict, path)
                event_id = event.get("id")
                self.assertIsInstance(event_id, str, path)
                self.assertTrue(event_id.strip(), path)
                ids[event_id].append(path.relative_to(EVENTS_ROOT).as_posix())
        duplicates = {event_id: paths for event_id, paths in ids.items() if len(paths) > 1}
        self.assertFalse(duplicates, duplicates)

    def test_event_json_objects_have_no_duplicate_keys(self):
        def reject_duplicates(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise AssertionError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        for path in sorted(EVENTS_ROOT.rglob("*.json")):
            with self.subTest(path=path.name):
                json.loads(
                    path.read_text(encoding="utf-8-sig"),
                    object_pairs_hook=reject_duplicates,
                )

    def test_main_event_selection_modes_and_numeric_gates_are_valid(self):
        errors = []
        for path, event in MAIN_ROWS:
            event_id = event["id"]
            if "required_store_value" in event:
                errors.append(
                    f"{path.name}:{event_id}: required_store_value is recruitment-only; "
                    "use conditions.start_when for normal events"
                )
            selection = event.get("worker_selection", "none")
            if selection not in {"none", "random", "choose"}:
                errors.append(f"{path.name}:{event_id}: worker_selection={selection!r}")
            probability = event.get("event_probability")
            if probability is not None and not (
                isinstance(probability, (int, float)) and 0 <= probability <= 100
            ):
                errors.append(f"{path.name}:{event_id}: event_probability={probability!r}")
            cooldown = event.get("cooldown_days", 3)
            if not isinstance(cooldown, (int, float)) or cooldown < 0:
                errors.append(f"{path.name}:{event_id}: cooldown_days={cooldown!r}")
            if event.get("limited"):
                maximum = event.get("max_occurrences")
                if not isinstance(maximum, int) or maximum < 1:
                    errors.append(f"{path.name}:{event_id}: invalid max_occurrences={maximum!r}")
            choices = event.get("choices")
            if not isinstance(choices, list) or not choices:
                errors.append(f"{path.name}:{event_id}: no executable choices")
        self.assertFalse(errors, "\n".join(errors))

    def test_event_conditions_use_parseable_supported_syntax(self):
        errors = []
        simple_prefixes = {
            "after_days": 1,
            "before_days": 1,
            "after_date": 3,
            "exact_date": 2,
            "has_item": 1,
            "has_flag": 1,
            "flag_value": 1,
            "random_under": 1,
            "event_passed": 1,
            "worker_gender": 1,
            "has_worker": 1,
            "not_has_worker": 1,
            "has_folder_worker": 1,
            "not_has_folder_worker": 1,
            "building_level": 2,
            "after_days_from_flag": 2,
        }

        def validate_atom(atom, location):
            atom = atom.strip()
            if atom in {"True", "False"}:
                return
            for boolean_op in (" AND ", " OR "):
                if boolean_op in atom:
                    for part in atom.split(boolean_op):
                        validate_atom(part, location)
                    return
            if ":" in atom:
                prefix, payload = atom.split(":", 1)
                if prefix not in simple_prefixes:
                    errors.append(f"{location}: unsupported condition prefix {prefix!r}")
                    return
                expected_parts = simple_prefixes[prefix]
                actual_parts = len(payload.split(","))
                if actual_parts != expected_parts:
                    errors.append(
                        f"{location}: {prefix} expects {expected_parts} values, got {payload!r}"
                    )
                return
            try:
                compile(atom, location, "eval")
            except SyntaxError as exc:
                errors.append(f"{location}: invalid expression {atom!r}: {exc.msg}")

        for path, event in EVENT_ROWS:
            for index, condition in enumerate(iter_conditions(event)):
                validate_atom(condition, f"{path.name}:{event['id']}:condition[{index}]")
        self.assertFalse(errors, "\n".join(errors))

    def test_character_arc_stages_are_contiguous_and_time_chained(self):
        arcs = defaultdict(list)
        for path, event in MAIN_ROWS:
            if event.get("arc_id"):
                arcs[event["arc_id"]].append((path, event))
        errors = []
        for arc_id, rows in arcs.items():
            ordered = sorted(rows, key=lambda row: row[1].get("arc_stage", -1))
            stages = [event.get("arc_stage") for _path, event in ordered]
            if stages != list(range(1, len(ordered) + 1)):
                errors.append(f"{arc_id}: non-contiguous stages {stages}")
                continue
            for previous, current in zip(ordered, ordered[1:]):
                expected_flag = previous[1].get("completion_timestamp_flag")
                start_when = str((current[1].get("conditions") or {}).get("start_when", ""))
                expected_pattern = (
                    rf"after_days_from_flag:{re.escape(str(expected_flag))},([0-9]+)"
                    if expected_flag else None
                )
                match = re.fullmatch(expected_pattern, start_when) if expected_pattern else None
                if not match or int(match.group(1)) <= 0:
                    errors.append(
                        f"{arc_id}:{current[1]['id']}: not time-chained exactly from {expected_flag!r}"
                    )
                    continue
                declared_delay = current[1].get("days_after_previous")
                if declared_delay is not None and int(declared_delay) != int(match.group(1)):
                    errors.append(
                        f"{arc_id}:{current[1]['id']}: delay {match.group(1)} != days_after_previous {declared_delay}"
                    )
        self.assertFalse(errors, "\n".join(errors))

    def test_exact_date_events_cannot_be_silently_preempted(self):
        by_date = defaultdict(list)
        errors = []
        for path, event in MAIN_ROWS:
            start_when = str((event.get("conditions") or {}).get("start_when", ""))
            if "exact_date:" in start_when and not start_when.startswith("exact_date:"):
                errors.append(
                    f"{path.name}:{event['id']}: exact_date must lead start_when for guaranteed selection"
                )
            for date_key in re.findall(r"exact_date:([0-9]+,[0-9]+)", start_when):
                by_date[date_key].append(f"{path.name}:{event['id']}")
                if not event.get("guaranteed") or event.get("event_probability") != 100:
                    errors.append(
                        f"{path.name}:{event['id']}: exact_date is not guaranteed at 100%"
                    )
                if not event.get("limited") or event.get("max_occurrences") != 1:
                    errors.append(f"{path.name}:{event['id']}: exact_date is not a one-shot")
        collisions = {date: events for date, events in by_date.items() if len(events) > 1}
        if collisions:
            errors.append(f"exact_date collisions can preempt each other: {collisions}")
        self.assertFalse(errors, "\n".join(errors))

    def test_recovery_priority_is_reserved_for_truly_guaranteed_events(self):
        errors = []
        for path, event in MAIN_ROWS:
            if not event.get("recovery_priority"):
                continue
            if not event.get("guaranteed") or event.get("event_probability", 0) < 100:
                errors.append(f"{path.name}:{event['id']}")
        self.assertFalse(errors, "Invalid recovery_priority:\n" + "\n".join(errors))


class EventEffectSchemaTests(unittest.TestCase):
    COMMON_EFFECT_KEYS = {
        "money", "reputation", "servant_energy", "servant_health", "health",
        "skill_modifiers", "event_flags", "set_timestamp_flags", "custom",
        "item_id", "chance", "consume_item", "loot_rolls", "random_worker",
        "worker_name", "add_trait", "trait_chance", "trait_remove_chance",
        "joy", "joy_worker_name", "building_worker_energy", "building_worker_joy",
        "success", "failure",
        "success_chance", "cost_modifier", "relationship_bonus", "recruit_worker",
    }
    RECRUIT_ONLY_EFFECT_KEYS = {"energy", "add_attribute", "amount"}

    def test_every_effect_key_has_an_explicit_runtime_contract(self):
        errors = []
        for path, event in EVENT_ROWS:
            recruit = "recruit" in path.parts
            allowed = set(self.COMMON_EFFECT_KEYS)
            if recruit:
                allowed |= self.RECRUIT_ONLY_EFFECT_KEYS
            for choice_index, choice in enumerate(event.get("choices") or []):
                effect = choice.get("effect") if isinstance(choice, dict) else None
                for block in iter_effect_blocks(effect):
                    unknown = sorted(set(block) - allowed)
                    if unknown:
                        errors.append(
                            f"{path.name}:{event['id']}:choice[{choice_index}]: {unknown}"
                        )
                    if not recruit:
                        for ignored_key in ("cost_modifier", "relationship_bonus", "recruit_worker"):
                            if block.get(ignored_key) not in (None, 0, 0.0, False):
                                errors.append(
                                    f"{path.name}:{event['id']}: non-recruit {ignored_key} is not neutral"
                                )
        self.assertFalse(errors, "\n".join(errors))

    def test_every_custom_action_has_a_runtime_handler_for_its_event_family(self):
        main_source = (ROOT / "game" / "scripts" / "script.rpy").read_text(
            encoding="utf-8-sig"
        )
        recruit_source = (
            ROOT / "game" / "scripts" / "events" / "recruitment_functions.rpy"
        ).read_text(encoding="utf-8-sig")
        main_handlers = set(re.findall(r'custom_action\s*==\s*"([^"]+)"', main_source))
        recruit_handlers = set(re.findall(r'custom_effect\s*==\s*"([^"]+)"', recruit_source))
        errors = []
        for path, event in EVENT_ROWS:
            recruit = "recruit" in path.parts
            allowed = recruit_handlers if recruit else main_handlers
            for choice in event.get("choices") or []:
                for block in iter_effect_blocks(choice.get("effect") if isinstance(choice, dict) else None):
                    action = block.get("custom")
                    if action is not None and action not in allowed:
                        errors.append(f"{path.name}:{event['id']}: custom={action!r}")
        self.assertFalse(errors, "\n".join(errors))

    def test_conditional_effects_do_not_hide_root_level_consequences(self):
        errors = []
        metadata = {"success", "failure", "success_chance", "cost_modifier", "relationship_bonus"}
        for path, event in EVENT_ROWS:
            for index, choice in enumerate(event.get("choices") or []):
                if not isinstance(choice, dict) or not choice.get("condition"):
                    continue
                effect = choice.get("effect") or {}
                root_consequences = {
                    key for key, value in effect.items()
                    if key not in metadata and value not in (None, 0, 0.0, False, {}, [])
                }
                if root_consequences:
                    errors.append(
                        f"{path.name}:{event['id']}:choice[{index}] ignored root keys {sorted(root_consequences)}"
                    )
        self.assertFalse(errors, "\n".join(errors))

    def test_worker_scoped_effects_have_a_resolvable_worker_context(self):
        worker_keys = {
            "servant_energy", "servant_health", "health", "skill_modifiers",
            "trait_chance", "trait_remove_chance", "joy",
        }
        errors = []
        for path, event in MAIN_ROWS:
            if event.get("worker_selection", "none") != "none":
                continue
            for index, choice in enumerate(event.get("choices") or []):
                if not isinstance(choice, dict) or choice.get("condition") == "building_skill":
                    continue
                for block in iter_effect_blocks(choice.get("effect")):
                    unresolved = {
                        key for key in worker_keys
                        if block.get(key) not in (None, 0, 0.0, False, {}, [])
                    }
                    if unresolved == {"joy"} and block.get("joy_worker_name"):
                        unresolved.clear()
                    if unresolved:
                        errors.append(
                            f"{path.name}:{event['id']}:choice[{index}] has no worker for {sorted(unresolved)}"
                        )
        self.assertFalse(errors, "\n".join(errors))


class EventFlagGraphTests(unittest.TestCase):
    def test_condition_flags_have_producers_in_the_correct_namespace_and_type(self):
        produced = set()
        timestamp_produced = set()
        for _path, event in EVENT_ROWS:
            completion_flag = event.get("completion_timestamp_flag")
            if completion_flag:
                produced.add(completion_flag)
                timestamp_produced.add(completion_flag)
            for choice in event.get("choices") or []:
                for block in iter_effect_blocks(choice.get("effect") if isinstance(choice, dict) else None):
                    for flag, value in (block.get("event_flags") or {}).items():
                        if value is not None:
                            produced.add(flag)
                            if isinstance(value, str) and "calculate_total_days" in value:
                                timestamp_produced.add(flag)
                    for flag in block.get("set_timestamp_flags") or []:
                        produced.add(flag)
                        timestamp_produced.add(flag)

        script_source = "\n".join(
            path.read_text(encoding="utf-8-sig", errors="replace")
            for path in SCRIPTS_ROOT.rglob("*.rpy")
        )
        produced.update(re.findall(r'event_flags\[\s*["\']([^"\']+)["\']\s*\]\s*=', script_source))
        for body in re.findall(r"event_flags\.update\(\s*\{(.*?)\}\s*\)", script_source, re.S):
            produced.update(re.findall(r'["\']([^"\']+)["\']\s*:', body))

        missing = []
        wrong_type = []
        for path, event in EVENT_ROWS:
            required = set((event.get("required_flags") or {}).keys())
            excluded = set((event.get("excluded_flags") or {}).keys())
            for flag in sorted(required | excluded):
                if flag not in produced:
                    missing.append(f"{path.name}:{event['id']}:{flag}")
            for condition in iter_conditions(event):
                for flag in re.findall(r"has_flag:([A-Za-z0-9_]+)", condition):
                    if flag not in produced:
                        missing.append(f"{path.name}:{event['id']}:{flag}")
                for flag in re.findall(r"after_days_from_flag:([A-Za-z0-9_]+),", condition):
                    if flag not in timestamp_produced:
                        wrong_type.append(f"{path.name}:{event['id']}:{flag}")
        self.assertFalse(missing, "Unproduced event flags:\n" + "\n".join(sorted(set(missing))))
        self.assertFalse(
            wrong_type,
            "after_days_from_flag requires timestamp producers:\n" + "\n".join(sorted(set(wrong_type))),
        )

    def test_event_flag_dependency_graph_has_no_dead_or_circular_chains(self):
        producers = defaultdict(set)
        for _path, event in EVENT_ROWS:
            completion_flag = event.get("completion_timestamp_flag")
            if completion_flag:
                producers[completion_flag].add(event["id"])
            for choice in event.get("choices") or []:
                for block in iter_effect_blocks(choice.get("effect") if isinstance(choice, dict) else None):
                    for flag, value in (block.get("event_flags") or {}).items():
                        if value is not None:
                            producers[flag].add(event["id"])
                    for flag in block.get("set_timestamp_flags") or []:
                        producers[flag].add(event["id"])

        script_source = "\n".join(
            path.read_text(encoding="utf-8-sig", errors="replace")
            for path in SCRIPTS_ROOT.rglob("*.rpy")
        )
        runtime_seeds = set(
            re.findall(r'event_flags\s*\[\s*["\']([^"\']+)["\']\s*\]\s*=', script_source)
        )
        for body in re.findall(
            r"event_flags\.update\s*\(\s*\{(.*?)\}\s*\)", script_source, re.S
        ):
            runtime_seeds.update(re.findall(r'["\']([^"\']+)["\']\s*:', body))

        dependencies = {}
        for _path, event in EVENT_ROWS:
            start_when = str((event.get("conditions") or {}).get("start_when", ""))
            flags = set((event.get("required_flags") or {}).keys())
            flags.update(re.findall(r"has_flag:([A-Za-z0-9_]+)", start_when))
            flags.update(
                re.findall(r"after_days_from_flag:([A-Za-z0-9_]+),", start_when)
            )
            dependencies[event["id"]] = flags

        reachable = {
            event_id
            for event_id, flags in dependencies.items()
            if not flags or flags <= runtime_seeds
        }
        changed = True
        while changed:
            changed = False
            for event_id, flags in dependencies.items():
                if event_id in reachable:
                    continue
                if all(
                    flag in runtime_seeds or bool(producers[flag] & reachable)
                    for flag in flags
                ):
                    reachable.add(event_id)
                    changed = True

        unreachable = {
            event_id: sorted(dependencies[event_id])
            for event_id in dependencies
            if event_id not in reachable
        }
        self.assertFalse(unreachable, unreachable)

    def test_flag_consumers_match_the_values_their_producers_write(self):
        writer_values = defaultdict(list)
        for path, event in EVENT_ROWS:
            for choice in event.get("choices") or []:
                for block in iter_effect_blocks(choice.get("effect") if isinstance(choice, dict) else None):
                    for flag, value in (block.get("event_flags") or {}).items():
                        if value is not None:
                            writer_values[flag].append((value, path.name, event["id"]))

        errors = []
        for path, event in EVENT_ROWS:
            for flag, required_value in (event.get("required_flags") or {}).items():
                authored_values = [value for value, _file, _event in writer_values[flag]]
                if authored_values and required_value not in authored_values:
                    errors.append(
                        f"{path.name}:{event['id']}: requires {flag}={required_value!r}, "
                        f"writers produce {authored_values!r}"
                    )
            for condition in iter_conditions(event):
                for flag in re.findall(r"has_flag:([A-Za-z0-9_]+)", condition):
                    false_writers = [
                        f"{file_name}:{event_id}"
                        for value, file_name, event_id in writer_values[flag]
                        if value is False
                    ]
                    if false_writers:
                        errors.append(
                            f"{path.name}:{event['id']}: has_flag:{flag} also accepts false from {false_writers}"
                        )
        self.assertFalse(errors, "\n".join(errors))


class EventCatalogReferenceTests(unittest.TestCase):
    @staticmethod
    def _load_catalogs():
        building_data = json.loads(
            (ROOT / "game" / "data" / "buildings" / "building_types.json").read_text(
                encoding="utf-8-sig"
            )
        )
        buildings = {
            entry["id"] for entry in building_data["building_types"]
        }
        professions = {
            profession["id"]
            for building in building_data["building_types"]
            for profession in building.get("professions", [])
        }

        traits = set()
        for path in (ROOT / "game" / "data" / "traits").rglob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            stack = [data]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    if isinstance(value.get("name"), str) and (
                        "description" in value or "effects" in value
                    ):
                        traits.add(value["name"])
                    stack.extend(value.values())
                elif isinstance(value, list):
                    stack.extend(value)

        items = set()
        for path in (ROOT / "game" / "data" / "items").rglob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            stack = [data]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    if isinstance(value.get("id"), str) and "price" in value:
                        items.add(value["id"])
                    stack.extend(value.values())
                elif isinstance(value, list):
                    stack.extend(value)

        workers = set()
        worker_folders = set()
        for path in (ROOT / "game" / "data" / "workers").rglob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            stack = [data]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    if isinstance(value.get("name"), str) and "skills" in value:
                        workers.add(value["name"])
                        if isinstance(value.get("folder"), str):
                            worker_folders.add(value["folder"])
                    stack.extend(value.values())
                elif isinstance(value, list):
                    stack.extend(value)

        script_source = (ROOT / "game" / "scripts" / "script.rpy").read_text(
            encoding="utf-8-sig"
        )
        skill_block = script_source.split("define skill_names = {", 1)[1].split("}", 1)[0]
        skills = set(re.findall(r'"([^"]+)"\s*:', skill_block))
        return buildings, professions, traits, items, workers, worker_folders, skills

    def test_all_catalog_backed_event_references_resolve(self):
        buildings, professions, traits, items, workers, worker_folders, skills = self._load_catalogs()
        errors = []

        def values(value):
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [item for item in value if isinstance(item, str)]
            if isinstance(value, dict):
                return [item for item in value if isinstance(item, str)]
            return []

        def walk(value, location):
            if isinstance(value, dict):
                for key, nested in value.items():
                    if key in {
                        "trait", "required_trait", "required_traits", "forbidden_traits", "excluded_traits",
                        "traits_required", "traits_excluded",
                        "required_building_worker_traits", "positive_traits",
                        "negative_traits",
                    }:
                        for trait in values(nested):
                            if trait not in traits:
                                errors.append(f"{location}: unknown trait {trait!r}")
                    elif key in {"skill", "required_building_worker_skill", "any_skills"}:
                        for skill in values(nested):
                            if skill not in skills:
                                errors.append(f"{location}: unknown skill {skill!r}")
                    elif key == "skill_modifiers" and isinstance(nested, dict):
                        for skill in nested:
                            if skill not in skills:
                                errors.append(f"{location}: unknown skill modifier {skill!r}")
                    elif key in {"required_active_professions", "forbidden_active_professions"}:
                        for profession in values(nested):
                            if profession not in professions:
                                errors.append(f"{location}: unknown profession {profession!r}")
                    elif key == "profession" and isinstance(nested, str):
                        if nested not in professions:
                            errors.append(f"{location}: unknown profession {nested!r}")
                    elif key in {"item_id", "consume_item"} and isinstance(nested, str):
                        if nested not in items:
                            errors.append(f"{location}: unknown item {nested!r}")
                    elif key in {"worker_name", "joy_worker_name"}:
                        for worker in values(nested):
                            if worker not in workers:
                                errors.append(f"{location}: unknown worker {worker!r}")
                    elif key == "specific_worker_images":
                        for folder in values(nested):
                            if folder not in worker_folders:
                                errors.append(f"{location}: unknown worker image folder {folder!r}")
                    elif key == "add_trait":
                        entries = nested if isinstance(nested, list) else [nested]
                        for entry in entries:
                            trait = entry.get("name") if isinstance(entry, dict) else entry
                            if isinstance(trait, str) and trait not in traits:
                                errors.append(f"{location}: unknown added trait {trait!r}")
                    walk(nested, location)
            elif isinstance(value, list):
                for nested in value:
                    walk(nested, location)

        for path, event in EVENT_ROWS:
            location = f"{path.name}:{event['id']}"
            for building in event.get("building_type") or []:
                if building != "all" and building not in buildings:
                    errors.append(f"{location}: unknown building type {building!r}")
            for condition in iter_conditions(event):
                for item in re.findall(r"has_item:([A-Za-z0-9_]+)", condition):
                    if item not in items:
                        errors.append(f"{location}: unknown condition item {item!r}")
                for worker in re.findall(r"(?:has_worker|not_has_worker):([^ ]+)", condition):
                    if worker not in workers:
                        errors.append(f"{location}: unknown condition worker {worker!r}")
                for building in re.findall(r"building_level:([A-Za-z0-9_]+),", condition):
                    if building not in buildings:
                        errors.append(f"{location}: unknown condition building {building!r}")
                for folder in re.findall(r"(?:has_folder_worker|not_has_folder_worker):([^ ]+)", condition):
                    if folder not in worker_folders:
                        errors.append(f"{location}: unknown condition worker folder {folder!r}")
            walk(event, location)

        self.assertFalse(errors, "\n".join(sorted(set(errors))))


class CharacterArcRuntimeContractTests(unittest.TestCase):
    def test_cancelled_arc_timestamp_is_removed_from_affected_saves(self):
        store = SimpleNamespace(
            event_flags={
                "cedar_personal_stage_2_at": 42,
                "cedar_personal_stage_2_passed": True,
            },
            event_occurrences={"cedar_personal_stage_2": 0},
        )
        reconcile = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "reconcile_cancelled_character_arc_timestamps",
            {"store": store},
        )
        event = {
            "id": "cedar_personal_stage_2",
            "arc_id": "cedar_personal",
            "completion_timestamp_flag": "cedar_personal_stage_2_at",
        }

        removed = reconcile([event])

        self.assertEqual(["cedar_personal_stage_2_at"], removed)
        self.assertNotIn("cedar_personal_stage_2_at", store.event_flags)

    def test_completed_arc_timestamp_is_preserved_even_if_it_was_declined_earlier(self):
        store = SimpleNamespace(
            event_flags={
                "cedar_personal_stage_2_at": 42,
                "cedar_personal_stage_2_passed": True,
            },
            event_occurrences={"cedar_personal_stage_2": 1},
        )
        reconcile = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "reconcile_cancelled_character_arc_timestamps",
            {"store": store},
        )
        event = {
            "id": "cedar_personal_stage_2",
            "arc_id": "cedar_personal",
            "completion_timestamp_flag": "cedar_personal_stage_2_at",
        }

        self.assertEqual([], reconcile([event]))
        self.assertEqual(42, store.event_flags["cedar_personal_stage_2_at"])

    def test_event_pool_reconciles_legacy_cancelled_arc_timestamps(self):
        source = (
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy"
        ).read_text(encoding="utf-8-sig")
        body = source.split("    def select_possible_events(", 1)[1].split(
            "\n    def ", 1
        )[0]
        self.assertIn("reconcile_cancelled_character_arc_timestamps(all_events)", body)

    def test_opening_an_arc_sets_cooldown_without_unlocking_its_next_stage(self):
        store = SimpleNamespace(event_flags={})
        stub = lambda *_args, **_kwargs: None
        record_fired = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "record_character_event_fired",
            {
                "store": store,
                "calculate_total_days": lambda: 42,
                "event_is_character_arc": lambda _event: True,
                "worker_matches_event_progress": stub,
                "filter_workers_for_event_progress": stub,
                "event_progress_is_satisfied": stub,
                "character_event_cooldown_ready": stub,
                "limit_character_arc_candidates": stub,
            },
        )
        event = {
            "id": "cedar_personal_stage_2",
            "arc_id": "cedar_personal",
            "completion_timestamp_flag": "cedar_personal_stage_2_at",
        }

        self.assertTrue(record_fired(event))

        self.assertEqual(42, store.character_event_last_day)
        self.assertNotIn("cedar_personal_stage_2_at", store.event_flags)

    def test_completing_an_arc_stamps_the_flag_that_unlocks_its_next_stage(self):
        store = SimpleNamespace(event_flags={})
        stub = lambda *_args, **_kwargs: None
        record_completed = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "record_character_event_completed",
            {
                "store": store,
                "calculate_total_days": lambda: 42,
                "event_is_character_arc": lambda _event: True,
                "worker_matches_event_progress": stub,
                "filter_workers_for_event_progress": stub,
                "event_progress_is_satisfied": stub,
                "character_event_cooldown_ready": stub,
                "limit_character_arc_candidates": stub,
                "record_character_event_fired": stub,
                "reconcile_cancelled_character_arc_timestamps": stub,
                "reconcile_shop_unlock_state": stub,
            },
        )
        event = {
            "id": "cedar_personal_stage_2",
            "arc_id": "cedar_personal",
            "completion_timestamp_flag": "cedar_personal_stage_2_at",
        }

        self.assertTrue(record_completed(event))

        self.assertEqual(42, store.event_flags["cedar_personal_stage_2_at"])

    def test_arc_completion_is_recorded_only_after_a_choice_resolves(self):
        source = (
            ROOT / "game" / "scripts" / "events" / "events.rpy"
        ).read_text(encoding="utf-8-sig")
        resolved_branch = source.split(
            'if event_status == "proceed_with_action":', 1
        )[1].split('elif event_status == "no_worker_available":', 1)[0]

        self.assertIn("process_choice(chosen_choice_data, event, final_worker)", resolved_branch)
        self.assertIn("record_character_event_completed(event)", resolved_branch)
        self.assertLess(
            resolved_branch.index("process_choice(chosen_choice_data, event, final_worker)"),
            resolved_branch.index("record_character_event_completed(event)"),
        )


class ShopUnlockRecoveryContractTests(unittest.TestCase):
    def test_legacy_ui_shop_unlock_restores_event_flag_and_timestamp(self):
        store = SimpleNamespace(
            unlocked_shops={"shop2": True, "shop3": False},
            event_flags={},
        )
        reconcile = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "reconcile_shop_unlock_state",
            {"store": store, "calculate_total_days": lambda: 90},
        )

        reconcile()

        self.assertTrue(store.event_flags["shop2_unlocked"])
        self.assertEqual(90, store.event_flags["shop2_unlock_timestamp"])

    def test_legacy_event_flag_restores_ui_unlock_without_relocking_progress(self):
        store = SimpleNamespace(
            unlocked_shops={"shop2": False, "shop3": False},
            event_flags={"shop2_unlocked": True, "shop2_unlock_timestamp": 70},
        )
        reconcile = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "reconcile_shop_unlock_state",
            {"store": store, "calculate_total_days": lambda: 90},
        )

        reconcile()

        self.assertTrue(store.unlocked_shops["shop2"])
        self.assertEqual(70, store.event_flags["shop2_unlock_timestamp"])

    def test_elite_emporium_unlock_is_reconciled_in_both_namespaces(self):
        store = SimpleNamespace(
            unlocked_shops={"shop2": True, "shop3": True},
            event_flags={"shop2_unlocked": True, "shop2_unlock_timestamp": 70},
        )
        reconcile = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "reconcile_shop_unlock_state",
            {"store": store, "calculate_total_days": lambda: 90},
        )

        reconcile()

        self.assertTrue(store.unlocked_shops["shop3"])
        self.assertTrue(store.event_flags["shop3_unlocked"])

    def test_event_pool_reconciles_shop_namespaces_before_filtering(self):
        source = (
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy"
        ).read_text(encoding="utf-8-sig")
        body = source.split("    def select_possible_events(", 1)[1].split(
            "\n    def ", 1
        )[0]
        self.assertIn("reconcile_shop_unlock_state()", body)

    def test_day_90_recovery_is_deterministic_not_another_random_roll(self):
        fallback = EVENTS_BY_ID["rescue_shop_owner_debt_fallback"]
        self.assertTrue(fallback.get("guaranteed"))
        self.assertEqual(100, fallback.get("event_probability"))
        self.assertTrue(fallback.get("recovery_priority"))
        self.assertTrue(EVENTS_BY_ID["shop_owner_expansion_guaranteed"].get("recovery_priority"))

    def test_recovery_priority_beats_generic_guaranteed_without_random_selection(self):
        class RandomMustNotRun:
            def uniform(self, *_args):
                raise AssertionError("recovery selection must not roll")

        choose = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "event_daily_exec.rpy",
            "choose_guaranteed_event_tuple",
            {"renpy": SimpleNamespace(random=RandomMustNotRun())},
        )
        generic = ({"id": "generic", "weight": 100}, None)
        recovery = (
            {"id": "recovery", "weight": 1, "recovery_priority": True},
            None,
        )

        selected = choose([generic, recovery], 7, 4)

        self.assertIs(selected, recovery)

    def test_exact_date_event_beats_persistent_recovery_on_its_only_valid_day(self):
        choose = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "event_daily_exec.rpy",
            "choose_guaranteed_event_tuple",
            {"renpy": SimpleNamespace(random=SimpleNamespace(uniform=lambda *_args: 0))},
        )
        recovery = ({"id": "recovery", "recovery_priority": True}, None)
        exact_today = (
            {"id": "seasonal", "conditions": {"start_when": "exact_date:7,4"}},
            None,
        )

        selected = choose([recovery, exact_today], 7, 4)

        self.assertIs(selected, exact_today)

    def test_daily_guaranteed_pool_uses_recovery_aware_selector(self):
        source = (
            ROOT / "game" / "scripts" / "events" / "event_daily_exec.rpy"
        ).read_text(encoding="utf-8-sig")
        self.assertIn(
            "chosen_tuple = choose_guaranteed_event_tuple(",
            source,
        )

    def test_day_90_fallback_crosses_the_live_parser_boundary(self):
        day = {"value": 89}
        store = SimpleNamespace(
            event_flags={},
            workers=[],
            current_day=6,
            current_month=4,
            current_year=1,
        )
        namespace = {
            "store": store,
            "initialize_calendar": lambda: None,
            "calculate_total_days": lambda: day["value"],
            "renpy": SimpleNamespace(log=lambda _message: None, random=SimpleNamespace(random=lambda: 0.0)),
        }
        evaluate_condition = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "evaluate_condition",
            namespace,
        )
        self.assertFalse(evaluate_condition("after_days:90"))
        day["value"] = 90
        store.current_day = 7
        self.assertTrue(evaluate_condition("after_days:90"))

    def test_after_date_does_not_fire_one_month_early(self):
        store = SimpleNamespace(
            event_flags={},
            workers=[],
            current_day=28,
            current_month=1,
            current_year=1,
        )
        namespace = {
            "store": store,
            "initialize_calendar": lambda: None,
            "calculate_total_days": lambda: 27,
            "renpy": SimpleNamespace(log=lambda _message: None),
        }
        evaluate_condition = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "evaluate_condition",
            namespace,
        )

        self.assertFalse(evaluate_condition("after_date:1,2,1"))
        store.current_day = 1
        store.current_month = 2
        self.assertTrue(evaluate_condition("after_date:1,2,1"))

    def test_day_90_fallback_is_eligible_in_the_live_daily_pool(self):
        fallback = EVENTS_BY_ID["rescue_shop_owner_debt_fallback"]
        day = {"value": 89}
        store = SimpleNamespace(
            workers=[],
            event_flags={},
            event_occurrences={},
            event_last_occurred={},
            current_day=6,
            current_month=4,
            current_year=1,
        )
        condition_namespace = {
            "store": store,
            "initialize_calendar": lambda: None,
            "calculate_total_days": lambda: day["value"],
            "renpy": SimpleNamespace(log=lambda _message: None, random=SimpleNamespace(random=lambda: 0.0)),
        }
        evaluate_condition = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "evaluate_condition",
            condition_namespace,
        )
        selector_namespace = {
            "store": store,
            "available_buildings": {},
            "calculate_total_days": lambda: day["value"],
            "event_is_visible_for_content_filter": lambda *_args, **_kwargs: True,
            "event_progress_is_satisfied": lambda *_args, **_kwargs: True,
            "event_uses_building_availability_gates": lambda _event: False,
            "get_content_visible_event_buildings": lambda *_args: [],
            "building_matches_random_event_availability": lambda *_args: True,
            "event_passes_player_gender_requirement": lambda _event: True,
            "get_player_manager_gender": lambda: "female",
            "evaluate_condition": evaluate_condition,
            "limit_character_arc_candidates": lambda events: events,
            "reconcile_cancelled_character_arc_timestamps": lambda _events: [],
            "reconcile_shop_unlock_state": lambda: [],
            "_event_filter_log": lambda _message: None,
            "renpy": SimpleNamespace(log=lambda _message: None),
        }
        select_possible_events = extract_init_function(
            ROOT / "game" / "scripts" / "events" / "events_logic.rpy",
            "select_possible_events",
            selector_namespace,
        )

        self.assertEqual([], select_possible_events([fallback], active_building_types=["tavern"]))
        day["value"] = 90
        store.current_day = 7
        selected = select_possible_events([fallback], active_building_types=["tavern"])
        self.assertEqual(["rescue_shop_owner_debt_fallback"], [event["id"] for event in selected])

    def test_day_90_fallback_choice_unlocks_and_timestamps_the_shop(self):
        fallback = EVENTS_BY_ID["rescue_shop_owner_debt_fallback"]
        effect = fallback["choices"][0]["effect"]
        building = {"type": "tavern", "base_level": 1, "reputation": 0}
        store = SimpleNamespace(
            event_flags={},
            unlocked_shops={"shop2": False, "shop3": False},
            workers=[],
            current_affected_building="Building 1",
        )
        namespace = {
            "store": store,
            "available_buildings": {"Building 1": building},
            "calculate_total_days": lambda: 90,
            "get_building_multipliers": lambda _building: {"money": 1.0, "reputation": 1.0},
            "apply_event_timestamp_flags": lambda _effect: None,
            "apply_building_workers_energy_effect": lambda *_args: {},
            "apply_building_workers_joy_effect": lambda *_args: {},
            "renpy": SimpleNamespace(log=lambda _message: None, notify=lambda _message: None),
        }
        apply_effects = extract_init_function(
            ROOT / "game" / "scripts" / "script.rpy",
            "apply_effects",
            namespace,
        )

        apply_effects(effect, building=building)

        self.assertTrue(store.unlocked_shops["shop2"])
        self.assertIs(store.event_flags["shop2_unlocked"], True)
        self.assertEqual(90, store.event_flags["shop2_unlock_timestamp"])

    def test_every_shop_unlock_effect_mirrors_the_persistent_event_flag(self):
        errors = []
        for path, event in MAIN_ROWS:
            for index, choice in enumerate(event.get("choices") or []):
                for block in iter_effect_blocks(choice.get("effect") if isinstance(choice, dict) else None):
                    action = block.get("custom")
                    if action not in {"unlock_shop2", "unlock_shop3"}:
                        continue
                    shop = action.removeprefix("unlock_")
                    if (block.get("event_flags") or {}).get(f"{shop}_unlocked") is not True:
                        errors.append(f"{path.name}:{event['id']}:choice[{index}] missing {shop}_unlocked")
                    if action == "unlock_shop2":
                        timestamps = set(block.get("set_timestamp_flags") or [])
                        timestamp_value = (block.get("event_flags") or {}).get(
                            "shop2_unlock_timestamp"
                        )
                        if (
                            "shop2_unlock_timestamp" not in timestamps
                            and not (
                                isinstance(timestamp_value, str)
                                and "calculate_total_days" in timestamp_value
                            )
                        ):
                            errors.append(
                                f"{path.name}:{event['id']}:choice[{index}] missing shop2_unlock_timestamp"
                            )
        self.assertFalse(errors, "\n".join(errors))

    def test_primary_shop_unlock_uses_journal_progress_not_an_event_flag_alias(self):
        event = EVENTS_BY_ID["rescue_shop_owner_debt"]
        start_when = (event.get("conditions") or {}).get("start_when", "")
        self.assertNotIn("objective_6_complete", event.get("required_flags") or {})
        self.assertIn("store.current_objective >= 7", start_when)


if __name__ == "__main__":
    unittest.main()
