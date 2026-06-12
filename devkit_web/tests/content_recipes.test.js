// devkit_web/tests/content_recipes.test.js
// Every plan-2 recipe, fed synthetic answers, must produce JSON that validates
// clean against its schema using the real game catalogs.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { buildCatalogs } from '../src/lib/catalog_loader.js';
import { validateEntry } from '../src/lib/validator.js';

import { trait_schema } from '../src/schemas/trait.schema.js';
import { item_schema } from '../src/schemas/item.schema.js';
import { interaction_schema } from '../src/schemas/interaction.schema.js';
import { event_schema } from '../src/schemas/event.schema.js';
import { recruit_event_schema } from '../src/schemas/recruit_event.schema.js';
import { daily_story_schema } from '../src/schemas/daily_story.schema.js';
import { building_schema } from '../src/schemas/building.schema.js';
import { worker_schema } from '../src/schemas/worker.schema.js';

import { permanent_trait_recipe, temporary_trait_recipe } from '../src/recipes/traits.js';
import { consumable_item_recipe, equipment_item_recipe, quest_item_recipe } from '../src/recipes/items.js';
import {
  simple_interaction_recipe, trait_granting_interaction_recipe,
  worker_specific_interaction_recipe,
} from '../src/recipes/interactions.js';
import { daily_story_basic_recipe, daily_story_with_trait_roll_recipe } from '../src/recipes/daily_stories.js';
import {
  worker_specific_event_recipe, event_chain_2_steps_recipe,
  building_event_with_skill_check_recipe, recruitment_event_recipe,
} from '../src/recipes/events.js';
import { simple_building_type_recipe, add_profession_to_building_recipe } from '../src/recipes/buildings.js';
import { monster_worker_recipe, procedural_worker_template_recipe } from '../src/recipes/workers.js';

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

let _ctx = null;
async function realCtx() {
  if (_ctx) return _ctx;
  const catalogs = buildCatalogs({
    traits: await loadFolder('traits'),
    items: await loadFolder('items'),
    buildings: await loadFolder('buildings'),
    workers: await loadFolder('workers'),
    interactions: await loadFolder('interactions'),
    events: await loadFolder('events'),
  });
  catalogs.names_lists = new Set(
    Object.keys(JSON.parse(await fs.readFile(
      path.resolve(import.meta.dirname, '../../game/data/names.json'), 'utf8'))),
  );
  _ctx = { catalogs, image_exists: () => true, file: null, entry_index: 0 };
  return _ctx;
}

function assertClean(out, schema, ctx, label) {
  const entries = Array.isArray(out) ? out : [out];
  for (const e of entries) {
    const r = validateEntry(e, schema, ctx);
    assert.deepEqual(r.errors, [], `${label}: ${JSON.stringify(r.errors)}`);
  }
}

test('trait recipes build valid traits', async () => {
  const ctx = await realCtx();
  const answers = {
    name: 'Battle-Hardened', description: 'Seen too much.',
    skill_modifiers: { Combat: 5 }, earnings_multiplier: 0,
    conflicts: [], nsfw: false,
  };
  assertClean(permanent_trait_recipe.build(answers, ctx), trait_schema, ctx, 'permanent_trait');
  const temp = temporary_trait_recipe.build({ ...answers, duration: 5 }, ctx);
  assert.equal(temp.duration, 5);
  assertClean(temp, trait_schema, ctx, 'temporary_trait');
});

test('item recipes build valid items', async () => {
  const ctx = await realCtx();
  assertClean(consumable_item_recipe.build({
    name: 'Healing Brew', description: 'Restores health.', price: 50,
    effect_kind: 'health', effect_amount: 20, nsfw: false,
  }, ctx), item_schema, ctx, 'consumable');
  assertClean(equipment_item_recipe.build({
    name: 'Iron Sword', description: 'A blade.', type: 'weapon',
    skill_modifiers: { Combat: 5 }, price: 200, nsfw: false,
  }, ctx), item_schema, ctx, 'equipment');
  assertClean(quest_item_recipe.build({
    name: 'Old Key', description: 'Opens something.', obtain_hint: 'Governor quest.', nsfw: false,
  }, ctx), item_schema, ctx, 'quest');
});

test('interaction recipes build valid interactions', async () => {
  const ctx = await realCtx();
  assertClean(simple_interaction_recipe.build({
    name: 'Evening Stroll', description: 'A walk.', categories: ['Friendship'],
    cost_energy: 5, cost_money: 0,
    effects: { joy: 2, relationship: 1, romance: 0, rebelliousness: 0, libido: 0 },
    worker_gender: 'any', nsfw: false,
  }, ctx), interaction_schema, ctx, 'simple');

  const granting = trait_granting_interaction_recipe.build({
    name: 'Sparring Lesson', description: 'Train hard.', trait: ['Strong'],
    duration: 0, cost_energy: 10, required_traits: [], worker_gender: 'any', nsfw: false,
  }, ctx);
  assert.deepEqual(granting.effect.add_trait, { name: 'Strong', duration: 0 });
  assert.deepEqual(granting.excluded_traits, ['Strong']);
  assertClean(granting, interaction_schema, ctx, 'granting');

  assertClean(worker_specific_interaction_recipe.build({
    name: 'Tea with Aelis', description: 'A quiet tea.', specific_workers: ['Aelis'],
    cost_energy: 5, effects: { joy: 2, relationship: 1, romance: 1, rebelliousness: 0, libido: 0 },
    nsfw: false,
  }, ctx), interaction_schema, ctx, 'worker_specific');
});

test('daily story recipes build valid stories targeting real professions', async () => {
  const ctx = await realCtx();
  const buildingId = Object.keys(ctx.catalogs.meta.building_professions)[0];
  const profId = ctx.catalogs.meta.building_professions[buildingId].professions[0].id;
  const base = {
    building: buildingId, profession: profId,
    id: 'mymod_test_story', report: 'Did a thing',
    skill: 'Charm',
    desc_failure: '{worker_name} fails.', desc_mediocre: '{worker_name} is ok.',
    desc_success: '{worker_name} succeeds.', desc_critical: '{worker_name} excels.',
    base_pay: 60, weight: 5,
    required_traits: [], excluded_traits: [], worker_gender: 'any', nsfw_only: false,
  };
  const out = daily_story_basic_recipe.build(base, ctx);
  assert.equal(out.building_id, buildingId);
  assert.equal(out.profession_id, profId);
  assert.equal(out.story.earnings.mediocre, '30');
  assertClean(out.story, daily_story_schema, ctx, 'daily_story_basic');

  const out2 = daily_story_with_trait_roll_recipe.build({
    ...base,
    positive_traits: { Strong: 2 }, negative_traits: { Lazy: 2 },
    trait_msg_success: '{worker_name} uses raw strength.',
    trait_msg_failure: '{worker_name} slacks off.',
    reward_trait: ['Strong'], reward_chance: 25,
  }, ctx);
  assert.equal(out2.story.consequences.critical_success.trait_chance[0].trait, 'Strong');
  assertClean(out2.story, daily_story_schema, ctx, 'daily_story_trait_roll');
});

test('event recipes build valid events', async () => {
  const ctx = await realCtx();
  const workerName = [...ctx.catalogs.all_worker_names][0];

  const e1 = worker_specific_event_recipe.build({
    worker_name: workerName, id: 'mymod_gift', description: 'A gift arrives.',
    option_text: 'Open it', message: 'It is lovely.', money: 0, one_time: true, nsfw: false,
  }, ctx);
  assert.equal(e1.conditions.start_when, `has_worker:${workerName}`);
  assert.deepEqual(e1.excluded_flags, { mymod_gift_done: true });
  assertClean(e1, event_schema, ctx, 'worker_specific_event');

  const chain = event_chain_2_steps_recipe.build({
    base_id: 'mymod_mystery', worker_name: null,
    desc_1: 'Something odd.', option_1: 'Investigate', message_1: 'A clue!',
    desc_2: 'The truth.', option_2: 'Confront', message_2: 'Solved.', money_2: 100, nsfw: false,
  }, ctx);
  assert.equal(chain.length, 2);
  assert.deepEqual(chain[1].required_flags, { mymod_mystery_1_done: true });
  assertClean(chain, event_schema, ctx, 'event_chain');

  const buildingId = [...ctx.catalogs.all_buildings][0];
  const e3 = building_event_with_skill_check_recipe.build({
    building: buildingId, id: 'mymod_check', description: 'A challenge.',
    option_text: 'Attempt it', threshold: 50,
    message_success: 'Won.', message_failure: 'Lost.',
    money_success: 100, money_failure: -20, nsfw: false,
  }, ctx);
  assert.equal(e3.choices[0].condition, 'building_skill');
  assert.equal(e3.choices[0].threshold, 50);
  assertClean(e3, event_schema, ctx, 'building_event');
});

test('recruitment recipe builds a valid recruit event', async () => {
  const ctx = await realCtx();
  const e = recruitment_event_recipe.build({
    id: 'mymod_wanderer', description: 'A wanderer arrives.',
    dialogue: '"Work, please."', hire_text: 'Hire them for [COST] per day.',
    negotiate: true, weight: 10, nsfw: false,
  }, ctx);
  assert.equal(e.id, 'event_recruit_mymod_wanderer');
  assert.equal(e.choices.length, 3);
  assert.ok(e.choices.some((c) => c.effect.recruit_worker));
  assertClean(e, recruit_event_schema, ctx, 'recruitment_event');
});

test('building recipes build valid buildings', async () => {
  const ctx = await realCtx();
  const b = simple_building_type_recipe.build({
    name: 'Bakery', skill_name: 'Baking', skill_description: 'Bread quality.',
    locations: ['tavern'], profession_name: 'Baker', profession_description: 'Bakes.',
    difficulty: 'easy', max_daily_workers: 2, base_pay: 60,
    report: 'Baked fresh bread', desc_success: null, nsfw: false,
  }, ctx);
  assert.equal(b.id, 'bakery');
  assert.equal(b.professions[0].daily_stories.length, 1);
  assert.equal(b.professions[0].daily_stories[0].earnings.success, '60');
  assertClean(b, building_schema, ctx, 'simple_building');

  const target = Object.keys(ctx.catalogs.meta.building_full)[0];
  const before = ctx.catalogs.meta.building_full[target].professions.length;
  const b2 = add_profession_to_building_recipe.build({
    building: target, profession_name: 'Night Guard', profession_description: 'Guards.',
    skill: 'Combat', difficulty: 'medium', max_daily_workers: 1, base_pay: 40,
    report: 'Stood guard', desc_success: null, nsfw: false,
  }, ctx);
  assert.equal(b2.id, target);
  assert.equal(b2.professions.length, before + 1);
  assertClean(b2, building_schema, ctx, 'add_profession');
  // the source catalog entry must not be mutated
  assert.equal(ctx.catalogs.meta.building_full[target].professions.length, before);
});

test('worker recipes build valid workers', async () => {
  const ctx = await realCtx();
  const m = monster_worker_recipe.build({
    name: 'Thorn Beast', folder: 'thorn_beast', gender: 'female', race: 'Transformed',
    extra_traits: [], combat_level: 50, description: 'Spiky.', nsfw: true,
  }, ctx);
  assert.equal(m.monster, true);
  assert.equal(m.encounter_only, true);
  assertClean(m, worker_schema, ctx, 'monster_worker');

  const namesList = [...ctx.catalogs.names_lists][0];
  const p = procedural_worker_template_recipe.build({
    name: 'Village Cook', folder: 'village_cook', gender: 'female',
    names_list: namesList, race: 'Human', extra_traits: [],
    cost: 1100, skill_level: 25, description: 'Cooks.', nsfw: false,
  }, ctx);
  assert.equal(p.procedural, true);
  assert.equal(p.names_list, namesList);
  assertClean(p, worker_schema, ctx, 'procedural_worker');
});
