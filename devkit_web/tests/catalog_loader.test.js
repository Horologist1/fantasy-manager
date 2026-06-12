import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { buildCatalogs } from '../src/lib/catalog_loader.js';

async function loadFixturesFor(folder) {
  const dir = path.join(import.meta.dirname, 'fixtures/tiny_game_data', folder);
  const files = await fs.readdir(dir).catch(() => []);
  const out = [];
  for (const f of files) {
    if (!f.endsWith('.json')) continue;
    out.push(JSON.parse(await fs.readFile(path.join(dir, f), 'utf8')));
  }
  return out;
}

test('buildCatalogs assembles traits, items, buildings, workers', async () => {
  const sources = {
    traits: await loadFixturesFor('traits'),
    items: await loadFixturesFor('items'),
    buildings: await loadFixturesFor('buildings'),
    workers: await loadFixturesFor('workers'),
    interactions: [],
    events: [],
  };
  const catalogs = buildCatalogs(sources);

  assert.ok(catalogs.all_traits.has('Human'));
  assert.ok(catalogs.all_traits.has('Graceful'));
  assert.ok(catalogs.race_traits.has('Human'));
  assert.ok(catalogs.race_traits.has('Elf'));
  assert.equal(catalogs.race_traits.has('Graceful'), false);

  assert.ok(catalogs.all_items.has('potion_minor'));
  assert.ok(catalogs.all_items.has('sword_basic'));

  assert.ok(catalogs.all_buildings.has('tavern'));
  assert.ok(catalogs.all_professions.has('waitress'));
  assert.ok(catalogs.all_professions.has('bartender'));

  assert.ok(catalogs.all_worker_names.has('Iris'));
  assert.ok(catalogs.all_worker_folders.has('iris'));
});

test('buildCatalogs returns meta.trait_meta with descriptions', async () => {
  const sources = {
    traits: await loadFixturesFor('traits'),
    items: [], buildings: [], workers: [], interactions: [], events: [],
  };
  const catalogs = buildCatalogs(sources);
  assert.ok(catalogs.meta, 'meta object should be present');
  assert.ok(catalogs.meta.trait_meta, 'trait_meta should be present');
  assert.equal(catalogs.meta.trait_meta.Human.description, 'race');
  assert.equal(catalogs.meta.trait_meta.Graceful.description, 'personality');
});

test('buildCatalogs returns meta.item_meta with display info', async () => {
  const sources = {
    traits: [], items: await loadFixturesFor('items'),
    buildings: [], workers: [], interactions: [], events: [],
  };
  const catalogs = buildCatalogs(sources);
  assert.equal(catalogs.meta.item_meta.potion_minor.name, 'Minor Potion');
  assert.equal(catalogs.meta.item_meta.potion_minor.type, 'consumable');
});

test('buildCatalogs scans events for event_flags', () => {
  const events = [
    [
      {
        id: 'e1',
        choices: [{ effect: { event_flags: { aelis_quest_done: true } } }],
      },
    ],
  ];
  const catalogs = buildCatalogs({
    traits: [],
    items: [],
    buildings: [],
    workers: [],
    interactions: [],
    events,
  });
  assert.ok(catalogs.all_event_flags.has('aelis_quest_done'));
});

test('buildCatalogs exposes all_skills (canonical + building skill_name)', () => {
  const buildings = [{
    building_types: [{
      id: 'tavern', name: 'Tavern', skill_name: 'Hospitality',
      professions: [{ id: 'waitress', name: 'Waitress' }],
    }],
  }];
  const catalogs = buildCatalogs({
    traits: [], items: [], buildings, workers: [], interactions: [], events: [],
  });
  assert.ok(catalogs.all_skills.has('Combat'));
  assert.ok(catalogs.all_skills.has('Charm'));
  assert.ok(catalogs.all_skills.has('Hospitality'));
});

test('buildCatalogs exposes building_professions meta', () => {
  const buildings = [{
    building_types: [{
      id: 'tavern', name: 'Tavern', skill_name: 'Service',
      professions: [
        { id: 'waitress', name: 'Waitress', description: 'Serves drinks.' },
        { id: 'bartender', name: 'Bartender' },
      ],
    }],
  }];
  const catalogs = buildCatalogs({
    traits: [], items: [], buildings, workers: [], interactions: [], events: [],
  });
  const bp = catalogs.meta.building_professions;
  assert.deepEqual(bp.tavern.name, 'Tavern');
  assert.deepEqual(bp.tavern.professions.map((p) => p.id), ['waitress', 'bartender']);
  assert.equal(bp.tavern.professions[0].description, 'Serves drinks.');
});
