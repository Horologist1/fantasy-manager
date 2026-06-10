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
