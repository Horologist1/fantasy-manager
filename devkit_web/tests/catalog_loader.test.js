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
