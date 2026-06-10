import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateEntry } from '../src/lib/validator.js';

const tinySchema = {
  fields: {
    name: { type: 'string', required: true },
    cost: { type: 'int', min: 0 },
    traits: { type: 'list_of_strings', catalog: 'all_traits' },
  },
  rules: [
    {
      id: 'trait_exists',
      check: (e, ctx) => e.traits.every((t) => ctx.catalogs.all_traits.has(t)),
      severity: 'error',
      message: 'unknown trait',
    },
    {
      id: 'cost_reasonable',
      check: (e) => e.cost <= 10000,
      severity: 'warning',
      message: 'unusually high cost',
    },
  ],
  legacy: {
    legacy_name: { migrates_to: 'name', as: (v) => String(v) },
  },
};

const ctx = () => ({
  catalogs: { all_traits: new Set(['Human', 'Elf']) },
  image_exists: () => true,
  file: null,
  entry_index: 0,
});

test('valid entry returns no errors/warnings', () => {
  const r = validateEntry({ name: 'Aelis', cost: 100, traits: ['Human'] }, tinySchema, ctx());
  assert.deepEqual(r.errors, []);
  assert.deepEqual(r.warnings, []);
});

test('missing required field returns error', () => {
  const r = validateEntry({ cost: 100, traits: [] }, tinySchema, ctx());
  assert.equal(r.errors.length, 1);
  assert.equal(r.errors[0].field, 'name');
});

test('bad field type returns error with field path', () => {
  const r = validateEntry({ name: 'X', cost: -5, traits: [] }, tinySchema, ctx());
  assert.ok(r.errors.find((e) => e.field === 'cost'));
});

test('rule violation returns error or warning with rule id', () => {
  const r = validateEntry({ name: 'X', cost: 100, traits: ['Goblin'] }, tinySchema, ctx());
  assert.ok(r.errors.find((e) => e.rule === 'trait_exists'));

  const r2 = validateEntry({ name: 'X', cost: 99999, traits: [] }, tinySchema, ctx());
  assert.ok(r2.warnings.find((w) => w.rule === 'cost_reasonable'));
});

test('legacy field detected and migration suggested', () => {
  const r = validateEntry({ legacy_name: 'X', cost: 0, traits: [] }, tinySchema, ctx());
  assert.ok(r.migrations.find((m) => m.from === 'legacy_name' && m.to === 'name'));
});

test('applyMigrations transforms entry', async () => {
  const { applyMigrations } = await import('../src/lib/validator.js');
  const out = applyMigrations({ legacy_name: 'X', cost: 0, traits: [] }, tinySchema);
  assert.equal(out.name, 'X');
  assert.equal(out.legacy_name, undefined);
});
