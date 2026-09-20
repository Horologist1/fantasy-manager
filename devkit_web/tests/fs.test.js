import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createMemoryFS } from '../src/lib/fs.js';

test('memory fs reads what was written', async () => {
  const fs = createMemoryFS();
  await fs.writeJSON('workers/workers_mymod.json', [{ name: 'A' }]);
  const out = await fs.readJSON('workers/workers_mymod.json');
  assert.deepEqual(out, [{ name: 'A' }]);
});

test('memory fs returns null for missing files', async () => {
  const fs = createMemoryFS();
  assert.equal(await fs.readJSON('nope.json'), null);
});

test('mergeAndWrite appends a new entry to an array file', async () => {
  const fs = createMemoryFS();
  await fs.writeJSON('workers/workers_mymod.json', [{ name: 'A' }]);
  await fs.mergeAndWrite('workers/workers_mymod.json', { name: 'B' }, { key: 'name' });
  const out = await fs.readJSON('workers/workers_mymod.json');
  assert.deepEqual(out, [{ name: 'A' }, { name: 'B' }]);
});

test('mergeAndWrite replaces an entry with the same key', async () => {
  const fs = createMemoryFS();
  await fs.writeJSON('workers/workers_mymod.json', [{ name: 'A', cost: 100 }]);
  await fs.mergeAndWrite('workers/workers_mymod.json', { name: 'A', cost: 200 }, { key: 'name' });
  const out = await fs.readJSON('workers/workers_mymod.json');
  assert.deepEqual(out, [{ name: 'A', cost: 200 }]);
});

test('mergeAndWrite creates the file if missing', async () => {
  const fs = createMemoryFS();
  await fs.mergeAndWrite('workers/new.json', { name: 'A' }, { key: 'name' });
  const out = await fs.readJSON('workers/new.json');
  assert.deepEqual(out, [{ name: 'A' }]);
});

test('listDir returns names', async () => {
  const fs = createMemoryFS();
  await fs.writeJSON('events/a.json', []);
  await fs.writeJSON('events/b.json', []);
  const names = await fs.listDir('events');
  assert.deepEqual(names.sort(), ['a.json', 'b.json']);
});

// ---- wrapper-object files (plan 2) ----

test('mergeAndWrite with wrapper creates {wrapper: [entry]} when file missing', async () => {
  const fs = createMemoryFS();
  await fs.mergeAndWrite('items/items_mymod.json', { id: 'potion' }, { key: 'id', wrapper: 'items' });
  const out = await fs.readJSON('items/items_mymod.json');
  assert.deepEqual(out, { items: [{ id: 'potion' }] });
});

test('mergeAndWrite with wrapper merges by key inside the wrapper array', async () => {
  const fs = createMemoryFS();
  await fs.writeJSON('items/items_mymod.json', {
    items: [{ id: 'potion', price: 10 }],
    excluded_from_shops: ['potion'],
  });
  await fs.mergeAndWrite('items/items_mymod.json', { id: 'potion', price: 99 }, { key: 'id', wrapper: 'items' });
  await fs.mergeAndWrite('items/items_mymod.json', { id: 'sword' }, { key: 'id', wrapper: 'items' });
  const out = await fs.readJSON('items/items_mymod.json');
  assert.deepEqual(out.items, [{ id: 'potion', price: 99 }, { id: 'sword' }]);
  // sibling root keys are preserved
  assert.deepEqual(out.excluded_from_shops, ['potion']);
});

test('mergeDailyStoryExtension creates extension file with one entry', async () => {
  const { mergeDailyStoryExtension } = await import('../src/lib/fs.js');
  const fs = createMemoryFS();
  await mergeDailyStoryExtension(fs, 'buildings/daily_story_extensions/mymod.json', {
    building_id: 'tavern',
    profession_id: 'entertainer',
    story: { id: 's1', weight: 4 },
  });
  const out = await fs.readJSON('buildings/daily_story_extensions/mymod.json');
  assert.deepEqual(out, {
    daily_story_extensions: [{
      building_id: 'tavern',
      profession_id: 'entertainer',
      merge_mode: 'upsert',
      daily_stories: [{ id: 's1', weight: 4 }],
    }],
  });
});

test('mergeDailyStoryExtension upserts story by id within matching entry', async () => {
  const { mergeDailyStoryExtension } = await import('../src/lib/fs.js');
  const fs = createMemoryFS();
  const file = 'buildings/daily_story_extensions/mymod.json';
  await mergeDailyStoryExtension(fs, file, {
    building_id: 'tavern', profession_id: 'entertainer', story: { id: 's1', weight: 4 },
  });
  await mergeDailyStoryExtension(fs, file, {
    building_id: 'tavern', profession_id: 'entertainer', story: { id: 's1', weight: 9 },
  });
  await mergeDailyStoryExtension(fs, file, {
    building_id: 'tavern', profession_id: 'entertainer', story: { id: 's2', weight: 1 },
  });
  await mergeDailyStoryExtension(fs, file, {
    building_id: 'farm', profession_id: 'farmhand', story: { id: 's3', weight: 2 },
  });
  const out = await fs.readJSON(file);
  assert.equal(out.daily_story_extensions.length, 2);
  const tavern = out.daily_story_extensions.find((e) => e.building_id === 'tavern');
  assert.deepEqual(tavern.daily_stories, [{ id: 's1', weight: 9 }, { id: 's2', weight: 1 }]);
  const farm = out.daily_story_extensions.find((e) => e.building_id === 'farm');
  assert.deepEqual(farm.daily_stories, [{ id: 's3', weight: 2 }]);
});
