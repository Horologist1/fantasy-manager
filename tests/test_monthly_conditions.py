import copy
import json
from pathlib import Path
import random
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'game/python-packages'))
from fm_monthly import conditions as m
from fm_mods.packs import _validate_override_json, PackError


def catalog():
    return m.validate_catalog(json.loads((ROOT / 'game/data/monthly_conditions/cards.json').read_text()))[0]


def active(card_id='cold_spell'):
    state = json.loads(m.initial(3))
    state['card'] = next(c for c in catalog() if c['id'] == card_id)
    state['experienced'] = True
    return m.encode(state)


def test_calendar_introduction_disable_cancel_reenable_and_year_rollover():
    rng = random.Random(37)
    raw = m.sync('', 0, catalog(), rng.random)
    for month in (0, 1, 2):
        raw = m.sync(raw, month, catalog(), rng.random)
        assert not m.decode(raw)['card']['effects']
    raw = m.sync(raw, 3, catalog(), rng.random)
    assert m.decode(raw)['card']['effects']
    assert m.sync(raw, 3, [], lambda: pytest.fail('reroll')) == raw
    assert m.toggle(m.toggle(raw)) == raw
    pending = m.toggle(raw)
    assert m.decode(pending)['enabled'] and not m.decode(pending)['requested']
    assert m.decode(pending)['card'] == m.decode(raw)['card']
    off = m.sync(pending, 4, catalog(), rng.random)
    assert not m.decode(off)['enabled'] and not m.decode(off)['card']['effects']
    on = m.sync(m.toggle(off), 5, catalog(), rng.random)
    assert m.decode(on)['enabled']
    for month in range(6, 25):
        previous = m.decode(on)['card']['id']
        on = m.sync(on, month, catalog(), rng.random)
        assert m.decode(on)['card']['id'] != previous


def test_legacy_and_reactivation_first_effect_and_neutral_only_catalog():
    raw = m.sync('', 16, catalog(), lambda: 0)
    assert not m.decode(raw)['card']['effects']
    raw = m.sync(m.toggle(raw), 17, catalog(), lambda: 0)
    assert not m.decode(raw)['enabled']
    raw = m.sync(m.toggle(raw), 18, catalog(), lambda: 0)
    assert m.decode(raw)['card']['effects']
    for cards in ([], [m.NEUTRAL]):
        assert not m.decode(m.sync(m.initial(3), 4, cards, lambda: 0))['card']['effects']


def test_scopes_clamps_and_no_permanent_mutation():
    raw = active()
    worker = {'Service': 40, 'Striptease': 3}
    before = dict(worker)
    assert m.skill_value(raw, 'restaurant', 'cook', 'Service', worker['Service']) == 45
    assert m.skill_value(raw, 'tavern', 'cook', 'Service', 40) == 40
    assert m.skill_value(raw, 'restaurant', 'service', 'Service', 40) == 40
    assert m.skill_value(raw, 'brothel', 'stripper', 'Striptease', 3) == 0
    assert worker == before
    assert (m.skill_value(raw,'restaurant','cook','Service',40) + m.skill_value(raw,'restaurant','cook','Charm',60)) // 2 == 52
    for value in (-99, 0, 1, 100):
        assert m.payout(active('visitors'), 'tavern', 'bartender', value) == (value if value <= 1 else 110)
        assert m.payout(active('visitors'), 'restaurant', 'cook', value) == value
    assert m.payout(active('harvest'), 'restaurant', 'cook', 100) == 95


def test_saved_card_survives_removal_no_accumulation_and_rollback_replay():
    raw = active()
    assert m.sync(raw, 3, [], lambda: pytest.fail('same month')) == raw
    next_month = m.sync(raw, 4, [m.NEUTRAL], lambda: 0)
    assert m.skill_value(next_month,'restaurant','cook','Service',40) == 40
    assert m.skill_value(raw,'restaurant','cook','Service',40) == 45
    assert m.valid_state(raw)
    assert not m.valid_state('{bad')


@pytest.mark.parametrize('change', [
    {'weight': float('nan')}, {'image': '../escape.png'}, {'effects': [{'type': 'execute'}]},
    {'effects': [{'type':'skill','value':99,'skills':['Service'],'buildings':['restaurant']}]},
    {'nsfw': 'yes'}, {'effects': [{'type':'earnings','value':1.1,'skills':['Service'],'buildings':['restaurant']}]},
])
def test_malformed_cards_rejected(change):
    card = copy.deepcopy(catalog()[1]);card.update(change)
    cards, errors = m.validate_catalog([card])
    assert errors and len(cards) == 1 and not cards[0]['effects']


def test_real_catalog_references_and_mod_import_validation():
    known = {'buildings':set(),'professions':set(),'skills':set()}
    buildings=json.loads((ROOT/'game/data/buildings/building_types.json').read_text(encoding='utf-8-sig'))
    for b in buildings['building_types']:
        known['buildings'].add(b['id'])
        for p in b['professions']:
            known['professions'].add(p['id']);known['skills'].update(p.get('skills') or [])
    data=json.loads((ROOT/'game/data/monthly_conditions/cards.json').read_text())
    assert not m.validate_catalog(data,known)[1]
    # Guard against a card silently appearing or vanishing. Update deliberately
    # when the catalogue grows: 7 at first authoring, 16 after the 2026-09-10
    # editorial pass added flavour, rarity weights and the six nsfw cards.
    assert len(m.validate_catalog(data,known)[0]) == 16
    # The nsfw dimension the engine already supported now has content, and every
    # card that carries it must be flagged so SFW players never draw it.
    assert sum(1 for c in m.validate_catalog(data,known)[0] if c['nsfw']) == 6
    assert _validate_override_json('data/monthly_conditions/cards.json',json.dumps(data).encode()) == data
    bad=copy.deepcopy(data);bad[1]['effects'][0]['skills']=['unknown']
    assert m.validate_catalog(bad,known)[1]
    with pytest.raises(PackError):
        _validate_override_json('data/monthly_conditions/cards.json',b'[{"id":"bad"}]')


def test_800_workers_use_contextual_adjustments_without_accumulation():
    from fm_roster.autofill import plan_autofill
    workers=[dict(name=str(i),Service=40,Charm=45) for i in range(800)]
    roles=[dict(job_id='cook',skills=['Service'],free_slots=400,skill_adjustments={'Service':5}),
           dict(job_id='service',skills=['Charm'],free_slots=400)]
    before=copy.deepcopy(workers)
    plan=plan_autofill(roles,workers,lambda w,s:w[s])
    assert len(plan['assignments']) == 800 and workers == before
