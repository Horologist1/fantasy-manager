import { test } from 'node:test';
import assert from 'node:assert/strict';
import { unique_worker_recipe } from '../src/recipes/unique_worker.js';
import { validateEntry } from '../src/lib/validator.js';
import { worker_schema, ALL_SKILLS, RACE_TRAITS } from '../src/schemas/worker.schema.js';

const ctx = () => ({
  catalogs: {
    all_traits: new Set([...RACE_TRAITS, 'Graceful', 'Elegant', 'Charming']),
    race_traits: new Set(RACE_TRAITS),
    names_lists: new Set(['western_female']),
    all_worker_folders: new Set([]),
  },
  image_exists: () => true,
  file: null,
  entry_index: 0,
});

test('unique_worker build produces a valid worker JSON', () => {
  const json = unique_worker_recipe.build(
    {
      name: 'Lyra',
      folder: 'lyra',
      nsfw: false,
      gender: 'female',
      race: 'Elf',
      extra_traits: ['Graceful', 'Elegant'],
      skill_focus: 'social',
      description: 'A graceful elven dancer.',
    },
    ctx(),
  );

  assert.equal(json.name, 'Lyra');
  assert.equal(json.folder, 'lyra');
  assert.equal(json.unique, true);
  assert.equal(json.encounter_only, true);
  assert.equal(json.procedural, false);
  assert.deepEqual(Object.keys(json.skills).sort(), [...ALL_SKILLS].sort());
  assert.ok(json.traits.includes('Elf'));
  assert.ok(json.traits.includes('Graceful'));

  const r = validateEntry(json, worker_schema, ctx());
  assert.deepEqual(r.errors, []);
});

test('skill_focus=combat bumps combat-related skills', () => {
  const json = unique_worker_recipe.build(
    {
      name: 'Brawler',
      folder: 'brawler',
      nsfw: false,
      gender: 'female',
      race: 'Human',
      extra_traits: [],
      skill_focus: 'combat',
      description: '',
    },
    ctx(),
  );
  assert.ok(json.skills.Combat >= 40);
  assert.ok(json.skills.Agility >= 35);
});
