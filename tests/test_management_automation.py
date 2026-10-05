"""Independent automation controls and stable, scalable auto-fill planning."""
import copy
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import pytest

from test_storage_worker_cycle_qol import init_python_function

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_roster.autofill import plan_autofill


def automation_harness(size):
    workers = [dict(name="Worker %d" % i, auto_supply_potions=True,
                    auto_supply_potion_count=5, auto_equip=True, auto_rest=True,
                    auto_rest_entry_pct=45) for i in range(size)]
    calls = []
    env = {
        "store": SimpleNamespace(workers=workers),
        "persistent": SimpleNamespace(default_auto_supply_potions=False,
            default_auto_supply_potion_count=3, default_auto_equip=False,
            default_auto_rest=False, default_auto_rest_entry_pct=35),
        "renpy": SimpleNamespace(log=lambda *args: None,
                                  restart_interaction=lambda: calls.append("refresh")),
        "AUTO_REST_ENTRY_PCTS": (15, 25, 35, 45),
        "AUTO_SUPPLY_UI_CYCLE": [(False, 3)] + [(True, n) for n in range(1, 6)],
        "AUTO_REST_UI_CYCLE": [(False, None)] + [(True, n) for n in (15, 25, 35, 45)],
        "run_worker_auto_supply_potions": lambda w: calls.append("supply"),
        "run_worker_auto_equip": lambda w: calls.append("equip"),
    }
    source = (ROOT / "game/scripts/script.rpy").read_text(encoding="utf-8")
    for name in ("_normalize_persistent_worker_automation_defaults",
                 "apply_persistent_worker_automation_defaults_to_all_workers",
                 "cycle_persistent_default_auto_supply_compact",
                 "toggle_persistent_default_auto_equip",
                 "cycle_persistent_default_auto_rest_compact"):
        exec(init_python_function(source, name), env)
    return env, workers, calls


@pytest.mark.parametrize("size", [40, 200, 800])
@pytest.mark.parametrize("action,changed,side_effect", [
    ("cycle_persistent_default_auto_supply_compact",
     {"auto_supply_potions": True, "auto_supply_potion_count": 1}, "supply"),
    ("toggle_persistent_default_auto_equip", {"auto_equip": True}, "equip"),
    ("cycle_persistent_default_auto_rest_compact",
     {"auto_rest": True, "auto_rest_entry_pct": 15}, None),
])
def test_global_control_preserves_other_individual_policies(size, action, changed, side_effect):
    env, workers, calls = automation_harness(size)
    before = copy.deepcopy(workers)
    env[action]()
    for old, worker in zip(before, workers):
        assert worker == dict(old, **changed)
    assert calls.count("refresh") == 1
    assert calls.count("supply") == (size if side_effect == "supply" else 0)
    assert calls.count("equip") == (size if side_effect == "equip" else 0)


def test_explicit_apply_all_remains_compatible():
    env, workers, calls = automation_harness(2)
    env["apply_persistent_worker_automation_defaults_to_all_workers"](restart_ui=False)
    assert all(not w["auto_rest"] and not w["auto_equip"] and not w["auto_supply_potions"]
               for w in workers)
    assert not calls


def legacy_plan(professions, candidates, skill_fn):
    remaining = list(candidates)
    assignments, empty = [], {}
    for prof in professions:
        free = int(prof.get("free_slots", 0) or 0)
        filled = 0
        while filled < free and remaining:
            best = min(remaining, key=lambda w: (
                -sum(float(skill_fn(w, s) or 0) for s in prof.get("skills", [])),
                str(w.get("name", "")).strip().lower()))
            remaining.remove(best)
            assignments.append({"worker": best["name"], "job_id": prof["job_id"]})
            filled += 1
        empty[prof["job_id"]] = free - filled
    return {"assignments": assignments, "empty_slots": empty}


@pytest.mark.parametrize("size", [40, 200, 800])
def test_autofill_scores_once_per_candidate_and_profession(size):
    workers = [{"name": "W%04d" % i, "a": i % 100, "b": 100 - i % 100} for i in range(size)]
    calls = []
    def skill(w, s):
        calls.append((w["name"], s))
        return w[s]
    plan = plan_autofill([{"job_id": "service", "skills": ["a", "b"], "free_slots": size}], workers, skill)
    assert len(plan["assignments"]) == size
    assert len(calls) == size * 2


def team_score(plan, professions, workers):
    roles = {p['job_id']: p.get('skills', []) for p in professions}
    people = {w['name']: w for w in workers}
    return sum(sum(people[a['worker']][s] for s in roles[a['job_id']]) /
               max(1, len(roles[a['job_id']])) for a in plan['assignments'])


def test_autofill_improves_or_preserves_team_without_mutating_inputs():
    rng = random.Random(714)
    for _ in range(30):
        workers = [{"name": "W%03d" % i, "a": rng.randrange(5), "b": rng.randrange(5)} for i in range(40)]
        rng.shuffle(workers)
        professions = [{"job_id": str(i), "skills": skills, "free_slots": rng.randrange(25)}
                       for i, skills in enumerate((["a"], ["b"], ["a", "b"], []))]
        before = copy.deepcopy((workers, professions))
        skill = lambda w, s: w[s]
        plan = plan_autofill(professions, workers, skill)
        old = legacy_plan(professions, workers, skill)
        assert team_score(plan, professions, workers) >= team_score(old, professions, workers)
        assert plan['empty_slots'] == old['empty_slots']
        names = [a['worker'] for a in plan['assignments']]
        assert len(names) == len(set(names))
        assert plan == plan_autofill(professions, workers, skill)
        assert (workers, professions) == before


def test_autofill_keeps_scarce_cook_for_kitchen():
    workers = [dict(name='Alex', service=95, cooking=100),
               dict(name='Blair', service=90, cooking=10)]
    professions = [dict(job_id='service', skills=['service'], free_slots=1),
                   dict(job_id='cook', skills=['cooking'], free_slots=1)]
    plan = plan_autofill(professions, workers, lambda w, s: w[s])
    assert plan['assignments'] == [dict(worker='Blair', job_id='service'),
                                   dict(worker='Alex', job_id='cook')]


def test_multiskill_roles_do_not_get_artificial_priority_from_skill_count():
    workers = [dict(name='Alex', a=100, b=70, c=70),
               dict(name='Blair', a=80, b=55, c=55)]
    professions = [dict(job_id='multi', skills=['b', 'c'], free_slots=1),
                   dict(job_id='single', skills=['a'], free_slots=1)]
    plan = plan_autofill(professions, workers, lambda w, s: w[s])
    assert team_score(plan, professions, workers) == 155


def test_autofill_can_use_bench_without_changing_quota():
    workers = [dict(name='Alex', a=100, b=100),
               dict(name='Blair', a=99, b=0),
               dict(name='Casey', a=0, b=1)]
    professions = [dict(job_id='a', skills=['a'], free_slots=1),
                   dict(job_id='b', skills=['b'], free_slots=1),
                   dict(job_id='reserved', skills=['a'], free_slots=0)]
    plan = plan_autofill(professions, workers, lambda w, s: w[s])
    assert team_score(plan, professions, workers) == 199
    assert plan['empty_slots'] == dict(a=0, b=0, reserved=0)


def test_autofill_never_proposes_workers_away_in_a_franchise():
    """Found by the goal-driven autoplayer (2026-10-03): franchise staff read as
    "Unassigned", Auto-fill gave them seats in every building (even the
    Governor's Castle), the integrity pass then dropped those jobs and the
    seats stayed empty although free workers existed."""
    from fm_roster.autofill import reoptimization_candidates

    workers = [
        {"name": "Aspen", "assigned_building": "Unassigned", "franchise_id": "hospitality"},
        {"name": "Rose", "assigned_building": "Unassigned"},
        {"name": "Iris", "assigned_building": "Building 1"},
    ]
    resolve = lambda b: None if b in (None, "", "Unassigned") else b
    away = lambda w: bool(w.get("franchise_id"))

    names = [w["name"] for w in reoptimization_candidates(workers, "Building 1", {}, resolve, is_away=away)]
    assert "Aspen" not in names
    assert names == ["Rose", "Iris"]
    # Without the predicate the old behaviour is unchanged (callers opt in).
    assert "Aspen" in [w["name"] for w in reoptimization_candidates(workers, "Building 1", {}, resolve)]
