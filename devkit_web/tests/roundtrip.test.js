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
