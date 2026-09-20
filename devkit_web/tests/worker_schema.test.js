import { test } from 'node:test';
import assert from 'node:assert/strict';
import { worker_schema, ALL_SKILLS, RACE_TRAITS } from '../src/schemas/worker.schema.js';
import { validateEntry } from '../src/lib/validator.js';

const aelis = {
  name: 'Aelis',
  folder: 'aelis',
  cost: 1200,
  nsfw: true,
  unique: true,
  encounter_only: false,
  monster: false,
  procedural: false,
  skills: Object.fromEntries(ALL_SKILLS.map((s) => [s, 30])),
  names_list: 'western_female',
  traits: ['Human', 'Graceful', 'Elegant'],
  description: 'A graceful, observant lady.',
  gender: 'female',
  comfort_desired: 4,
};

const ctx = () => ({
  catalogs: {
    all_traits: new Set(['Human', 'Graceful', 'Elegant']),
    race_traits: new Set(RACE_TRAITS),
    names_lists: new Set(['western_female', 'fantasy_female']),
    all_worker_folders: new Set(['aelis']),
  },
  image_exists: () => true,
  file: null,
  entry_index: 0,
});

test('valid Aelis-shaped worker has no errors', () => {
  const r = validateEntry(aelis, worker_schema, ctx());
  assert.deepEqual(r.errors, []);
});

test('worker without race trait warns', () => {
  const w = { ...aelis, traits: ['Graceful'] };
  const r = validateEntry(w, worker_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'race_trait_present'));
});

test('worker with unknown trait errors', () => {
  const w = { ...aelis, traits: ['Human', 'NotARealTrait'] };
  const r = validateEntry(w, worker_schema, ctx());
  assert.ok(r.errors.find((x) => x.rule === 'traits_exist'));
});

test('spawn-template worker without names_list warns', () => {
  // the game clones every non-unique worker; without a pool the clone used to
  // land on the roster literally called "Unknown"
  const w = { ...aelis, unique: false, names_list: null };
  const r = validateEntry(w, worker_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'spawnable_needs_names_list'));
});

test('unique worker may omit names_list', () => {
  const w = { ...aelis, names_list: null };
  const r = validateEntry(w, worker_schema, ctx());
  assert.ok(!r.warnings.find((x) => x.rule === 'spawnable_needs_names_list'));
});

test('skills missing required keys warns', () => {
  const w = { ...aelis, skills: { Sex: 30 } };
  const r = validateEntry(w, worker_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'skills_complete'));
});

test('cost out of sane range warns', () => {
  const w = { ...aelis, cost: 100000 };
  const r = validateEntry(w, worker_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'cost_in_range'));
});
