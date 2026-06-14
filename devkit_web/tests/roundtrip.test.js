// devkit_web/tests/roundtrip.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { worker_schema } from '../src/schemas/worker.schema.js';
import { validateEntry } from '../src/lib/validator.js';
import { buildCatalogs } from '../src/lib/catalog_loader.js';

async function loadFolder(name) {
  const dir = path.resolve(import.meta.dirname, '../../game/data', name);
  const out = [];
  let entries;
  try { entries = await fs.readdir(dir); } catch { return []; }
  for (const f of entries) {
    if (!f.endsWith('.json')) continue;
    out.push(JSON.parse(await fs.readFile(path.join(dir, f), 'utf8')));
  }
  return out;
}

test('every shipped worker validates with no errors', async () => {
  const sources = {
    traits: await loadFolder('traits'),
    items: await loadFolder('items'),
    buildings: await loadFolder('buildings'),
    workers: await loadFolder('workers'),
    interactions: await loadFolder('interactions'),
    events: await loadFolder('events'),
  };
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };

  let totalErrors = 0;
  for (const file of sources.workers) {
    for (let i = 0; i < file.length; i++) {
      const w = file[i];
      const r = validateEntry(w, worker_schema, { ...ctx, entry_index: i });
      if (r.errors.length) {
        console.log(`worker ${w.name}: ${JSON.stringify(r.errors)}`);
        totalErrors += r.errors.length;
      }
    }
  }
  assert.equal(totalErrors, 0, `shipped workers have ${totalErrors} validation errors`);
});

// ---- plan 2: all content types round-trip ----

async function loadSources() {
  return {
    traits: await loadFolder('traits'),
    items: await loadFolder('items'),
    buildings: await loadFolder('buildings'),
    workers: await loadFolder('workers'),
    interactions: await loadFolder('interactions'),
    events: await loadFolder('events'),
  };
}

function reportErrors(label, errors) {
  if (errors.length) console.log(`${label}: ${JSON.stringify(errors)}`);
  return errors.length;
}

test('every shipped trait validates with no errors', async () => {
  const { trait_schema } = await import('../src/schemas/trait.schema.js');
  const sources = await loadSources();
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  let total = 0;
  for (const file of sources.traits) {
    for (const t of file) total += reportErrors(`trait ${t.name}`, validateEntry(t, trait_schema, ctx).errors);
  }
  assert.equal(total, 0);
});

test('every shipped item validates with no errors', async () => {
  const { item_schema } = await import('../src/schemas/item.schema.js');
  const sources = await loadSources();
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  let total = 0;
  for (const file of sources.items) {
    for (const i of file.items || []) total += reportErrors(`item ${i.id}`, validateEntry(i, item_schema, ctx).errors);
  }
  assert.equal(total, 0);
});

test('every shipped interaction validates with no errors', async () => {
  const { interaction_schema } = await import('../src/schemas/interaction.schema.js');
  const sources = await loadSources();
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  let total = 0;
  for (const file of sources.interactions) {
    for (const i of file) total += reportErrors(`interaction ${i.id}`, validateEntry(i, interaction_schema, ctx).errors);
  }
  assert.equal(total, 0);
});

test('every shipped pool event validates with no errors', async () => {
  const { event_schema } = await import('../src/schemas/event.schema.js');
  const sources = await loadSources();
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  let total = 0;
  for (const file of sources.events) {
    for (const e of file) total += reportErrors(`event ${e.id}`, validateEntry(e, event_schema, ctx).errors);
  }
  assert.equal(total, 0);
});

test('every shipped recruit event validates with no errors', async () => {
  const { recruit_event_schema } = await import('../src/schemas/recruit_event.schema.js');
  const sources = await loadSources();
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  const dir = path.resolve(import.meta.dirname, '../../game/data/events/recruit');
  let total = 0;
  for (const f of await fs.readdir(dir)) {
    if (!f.endsWith('.json')) continue;
    const file = JSON.parse(await fs.readFile(path.join(dir, f), 'utf8'));
    for (const e of file) total += reportErrors(`recruit ${e.id}`, validateEntry(e, recruit_event_schema, ctx).errors);
  }
  assert.equal(total, 0);
});

test('every shipped daily story validates with no errors', async () => {
  const { daily_story_schema } = await import('../src/schemas/daily_story.schema.js');
  const sources = await loadSources();
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  let total = 0;
  for (const file of sources.buildings) {
    for (const b of file.building_types || []) {
      for (const p of b.professions || []) {
        for (const s of p.daily_stories || []) {
          total += reportErrors(`story ${b.id}/${p.id}/${s.id}`, validateEntry(s, daily_story_schema, ctx).errors);
        }
      }
    }
  }
  const extDir = path.resolve(import.meta.dirname, '../../game/data/buildings/daily_story_extensions');
  let extFiles = [];
  try { extFiles = await fs.readdir(extDir); } catch {}
  for (const f of extFiles) {
    if (!f.endsWith('.json')) continue;
    const data = JSON.parse(await fs.readFile(path.join(extDir, f), 'utf8'));
    for (const entry of data.daily_story_extensions || []) {
      for (const s of entry.daily_stories || []) {
        total += reportErrors(`ext story ${s.id}`, validateEntry(s, daily_story_schema, ctx).errors);
      }
    }
  }
  assert.equal(total, 0);
});

test('every shipped building validates with no errors', async () => {
  const { building_schema } = await import('../src/schemas/building.schema.js');
  const sources = await loadSources();
  const catalogs = buildCatalogs(sources);
  const ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  let total = 0;
  for (const file of sources.buildings) {
    for (const b of file.building_types || []) {
      total += reportErrors(`building ${b.id}`, validateEntry(b, building_schema, ctx).errors);
    }
  }
  assert.equal(total, 0);
});
