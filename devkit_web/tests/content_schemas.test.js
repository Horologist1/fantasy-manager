// devkit_web/tests/content_schemas.test.js
// Unit tests for the plan-2 content schemas (trait, item, interaction, event,
// recruit_event, daily_story, building).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateEntry } from '../src/lib/validator.js';
import { trait_schema } from '../src/schemas/trait.schema.js';
import { item_schema } from '../src/schemas/item.schema.js';
import { interaction_schema } from '../src/schemas/interaction.schema.js';
import { event_schema } from '../src/schemas/event.schema.js';
import { recruit_event_schema } from '../src/schemas/recruit_event.schema.js';
import { daily_story_schema } from '../src/schemas/daily_story.schema.js';
import { building_schema } from '../src/schemas/building.schema.js';

const ctx = () => ({
  catalogs: {
    all_traits: new Set(['Human', 'Strong', 'Lazy']),
    race_traits: new Set(['Human']),
    all_items: new Set(['potion_minor']),
    all_buildings: new Set(['tavern']),
    all_professions: new Set(['waitress']),
    all_skills: new Set(['Charm', 'Combat', 'Service']),
    all_worker_names: new Set(['Aelis']),
    all_worker_folders: new Set(['aelis']),
    all_event_flags: new Set(['quest_done']),
    names_lists: new Set(['western_female']),
  },
  image_exists: () => true,
  file: null,
  entry_index: 0,
});

// ---- trait ----

test('valid trait has no errors', () => {
  const t = {
    name: 'Brave',
    conflicts: ['Lazy'],
    removes_traits: [],
    modifiers: { skill_modifiers: { Combat: 5 }, earnings_multiplier: 1.1 },
    description: 'Never backs down.',
    nsfw: false,
  };
  assert.deepEqual(validateEntry(t, trait_schema, ctx()).errors, []);
});

test('trait without name errors', () => {
  const r = validateEntry({ description: 'x' }, trait_schema, ctx());
  assert.ok(r.errors.find((e) => e.field === 'name'));
});

test('trait with unknown conflict warns', () => {
  const t = { name: 'Brave', conflicts: ['NotATrait'] };
  const r = validateEntry(t, trait_schema, ctx());
  assert.ok(r.warnings.find((w) => w.rule === 'conflicts_exist'));
});

// ---- item ----

test('valid item has no errors', () => {
  const i = {
    id: 'sword_iron',
    name: 'Iron Sword',
    display_name: 'Iron Sword',
    type: 'weapon',
    effect: { custom: null, skill_modifiers: { Combat: 3 } },
    description: 'A sturdy blade.',
    durability: 0,
    price: 200,
    weight: 2,
    nsfw: false,
  };
  assert.deepEqual(validateEntry(i, item_schema, ctx()).errors, []);
});

test('item without id errors; unknown type warns', () => {
  const r = validateEntry({ name: 'X', type: 'spaceship' }, item_schema, ctx());
  assert.ok(r.errors.find((e) => e.field === 'id'));
  assert.ok(r.warnings.find((w) => w.rule === 'type_known'));
});

// ---- interaction ----

test('valid interaction has no errors', () => {
  const i = {
    id: 'pep_talk',
    name: 'Pep Talk',
    description: 'A short morale boost.',
    interaction_level: 1,
    interaction_type: null,
    cost_energy: 5,
    cost_money: 0,
    effect: { joy: 2, relationship: 1, flags: { pep_cooldown: { value: true, duration: 1 } } },
    categories: ['Social'],
    image: null,
    nsfw: false,
    stat_requirements: {},
    specific_workers: [],
    required_traits: [],
    excluded_traits: [],
    required_flags: {},
    excluded_flags: { pep_cooldown: true },
  };
  assert.deepEqual(validateEntry(i, interaction_schema, ctx()).errors, []);
});

test('interaction with unknown required trait errors', () => {
  const i = { id: 'x', name: 'X', required_traits: ['Nope'] };
  const r = validateEntry(i, interaction_schema, ctx());
  assert.ok(r.errors.find((e) => e.rule === 'traits_exist'));
});

// ---- event ----

const validEvent = () => ({
  id: 'tavern_brawl',
  description: 'A fight breaks out.',
  weight: 5,
  building_type: ['tavern'],
  worker_selection: 'random',
  choices: [
    {
      option: 'Step in',
      condition: 'Combat',
      threshold: 40,
      message_success: 'You win.',
      message_failure: 'You lose.',
      effect: { success: { money: 50 }, failure: { money: -20 } },
    },
  ],
});

test('valid event has no errors', () => {
  assert.deepEqual(validateEntry(validEvent(), event_schema, ctx()).errors, []);
});

test('event without choices errors', () => {
  const e = { ...validEvent(), choices: [] };
  const r = validateEntry(e, event_schema, ctx());
  assert.ok(r.errors.find((x) => x.rule === 'choices_present'));
});

test('event with unknown building errors', () => {
  const e = { ...validEvent(), building_type: ['casino_royale'] };
  const r = validateEntry(e, event_schema, ctx());
  assert.ok(r.errors.find((x) => x.rule === 'buildings_exist'));
});

test('skill choice without threshold warns', () => {
  const e = validEvent();
  delete e.choices[0].threshold;
  const r = validateEntry(e, event_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'skill_choice_needs_threshold'));
});

test('worker_gender_requirement on pool event warns', () => {
  const e = { ...validEvent(), worker_gender_requirement: 'female' };
  const r = validateEntry(e, event_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'worker_gender_ignored'));
});

test('choice legacy required_trait warns', () => {
  const e = validEvent();
  e.choices[0].required_trait = 'Strong';
  const r = validateEntry(e, event_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'choice_required_trait_legacy'));
});

test('choice with unknown required_traits errors', () => {
  const e = validEvent();
  e.choices[0].required_traits = ['Nope'];
  const r = validateEntry(e, event_schema, ctx());
  assert.ok(r.errors.find((x) => x.rule === 'traits_exist'));
});

// ---- recruit event ----

test('valid recruit event has no errors', () => {
  const e = {
    id: 'event_recruit_wanderer',
    description: 'A wanderer arrives.',
    dialogue: '"Looking for work."',
    weight: 10,
    unlimited: true,
    random_worker: true,
    always_available: true,
    worker_filter: {},
    choices: [
      { option: 'Hire', message: 'Hired.', effect: { recruit_worker: true } },
      { option: 'Decline', message: 'Declined.', outcome_override: 'failure', effect: {} },
    ],
  };
  assert.deepEqual(validateEntry(e, recruit_event_schema, ctx()).errors, []);
});

test('recruit event with no recruit_worker choice warns', () => {
  const e = {
    id: 'event_recruit_x',
    choices: [{ option: 'Chat', effect: {} }],
  };
  const r = validateEntry(e, recruit_event_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'has_recruit_choice'));
});

// ---- daily story ----

const validStory = () => ({
  id: 'tavern_song',
  weight: 4,
  report: 'Sang for the crowd',
  description: null,
  difficulty_modifier: 0,
  skill_options: ['Charm'],
  positive_traits: { Strong: 2 },
  negative_traits: {},
  required_traits: [],
  excluded_traits: [],
  stat_requirements: {},
  descriptions: {
    failure: '{worker_name} is booed.',
    mediocre: '{worker_name} gets polite applause.',
    success: '{worker_name} sings well.',
    critical_success: '{worker_name} brings the house down.',
  },
  earnings: { failure: '0', mediocre: '40', success: '80', critical_success: '120' },
  consequences: {
    failure: { joy: -2 },
    mediocre: {},
    success: { joy: 1 },
    critical_success: { joy: 3, trait_chance: [{ trait: 'Strong', chance_percent: 10 }] },
  },
});

test('valid daily story has no errors', () => {
  assert.deepEqual(validateEntry(validStory(), daily_story_schema, ctx()).errors, []);
});

test('daily story missing outcome branches warns', () => {
  const s = validStory();
  delete s.descriptions.critical_success;
  delete s.earnings.failure;
  const r = validateEntry(s, daily_story_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'description_branches'));
  assert.ok(r.warnings.find((x) => x.rule === 'earnings_branches'));
});

test('daily story with unknown trait_chance trait warns', () => {
  const s = validStory();
  s.consequences.success.trait_chance = [{ trait: 'Nope', chance_percent: 50 }];
  const r = validateEntry(s, daily_story_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'trait_chance_traits_exist'));
});

test('daily story with unknown required trait errors', () => {
  const s = { ...validStory(), required_traits: ['Nope'] };
  const r = validateEntry(s, daily_story_schema, ctx());
  assert.ok(r.errors.find((x) => x.rule === 'traits_exist'));
});

// ---- building ----

test('valid building has no errors', () => {
  const b = {
    id: 'bakery',
    name: 'Bakery',
    skill_name: 'Baking',
    skill_description: 'Baking skill determines bread quality.',
    nsfw: false,
    allowed_map_locations: ['market'],
    professions: [
      {
        id: 'baker',
        name: 'Baker',
        description: 'Bakes bread.',
        nsfw: false,
        difficulty: 'easy',
        skills: ['Service'],
        max_daily_workers: 2,
        daily_story_count: { base: 1, bonus_formula: '0' },
        daily_stories: [],
      },
    ],
  };
  assert.deepEqual(validateEntry(b, building_schema, ctx()).errors, []);
});

test('building overriding an existing id warns', () => {
  const b = { id: 'tavern', name: 'My Tavern', skill_name: 'Service', professions: [] };
  const r = validateEntry(b, building_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'overrides_existing'));
});

test('building without professions warns', () => {
  const b = { id: 'bakery', name: 'Bakery', skill_name: 'Baking', professions: [] };
  const r = validateEntry(b, building_schema, ctx());
  assert.ok(r.warnings.find((x) => x.rule === 'professions_present'));
});
