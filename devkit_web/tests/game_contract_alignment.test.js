import { test } from 'node:test';
import assert from 'node:assert/strict';

import { validateEntry } from '../src/lib/validator.js';
import { CHOICE_FIELDS, event_schema } from '../src/schemas/event.schema.js';
import { daily_story_schema } from '../src/schemas/daily_story.schema.js';
import { recruit_event_schema } from '../src/schemas/recruit_event.schema.js';
import { trait_schema } from '../src/schemas/trait.schema.js';
import { worker_schema } from '../src/schemas/worker.schema.js';
import {
  daily_story_editor_sections,
  event_editor_sections,
  recruit_event_editor_sections,
  trait_editor_sections,
} from '../src/editors/content_editors.js';
import { worker_editor_sections } from '../src/editors/worker_editor.js';
import { monster_worker_recipe } from '../src/recipes/workers.js';

function ctx() {
  return {
    catalogs: {
      all_traits: new Set(['Goblin', 'Strong', 'Scarred']),
      race_traits: new Set(['Goblin']),
      all_items: new Set(['potion_minor']),
      all_buildings: new Set(['adventurers_guild']),
      all_professions: new Set(['monster_taming']),
      all_skills: new Set(['Combat', 'Charm']),
      all_worker_names: new Set(),
      all_worker_folders: new Set(['thorn_beast']),
      all_event_flags: new Set(['quest_done']),
      names_lists: new Set(['monster_goblin']),
    },
    image_exists: () => true,
    file: null,
    entry_index: 0,
  };
}

function editorFieldIds(sections) {
  return new Set(sections.flatMap((section) => section.fields.map((field) => field.id)));
}

test('worker schema accepts the current nameless procedural monster template contract', () => {
  const template = {
    template_id: 'monster_goblin',
    monster_archetype: 'goblin',
    procedural_template: true,
    unique: false,
    monster: true,
    procedural: false,
    encounter_only: true,
    recruitment_locked: true,
    folder: 'thorn_beast',
    cost: 1000,
    nsfw: true,
    gender: 'female',
    comfort_desired: 1,
    skills: { Combat: 40, Charm: 5 },
    traits: ['Goblin'],
    monster_secondary_traits: ['Strong'],
  };
  assert.deepEqual(validateEntry(template, worker_schema, ctx()).errors, []);
});

test('ordinary workers still require a display name', () => {
  const worker = {
    folder: 'thorn_beast',
    cost: 1000,
    nsfw: false,
    unique: false,
    monster: false,
    procedural: false,
    gender: 'female',
    comfort_desired: 1,
    skills: { Combat: 40, Charm: 5 },
    traits: ['Goblin'],
  };
  const result = validateEntry(worker, worker_schema, ctx());
  assert.ok(result.errors.some((error) => error.rule === 'worker_identity'));
});

test('worker schema and editor expose runtime recruitment and monster-template fields', () => {
  const expected = [
    'event_recruit_only', 'required_store_value', 'procedural_template',
    'monster_archetype', 'monster_secondary_traits',
  ];
  const editorFields = editorFieldIds(worker_editor_sections);
  for (const id of expected) {
    assert.ok(worker_schema.fields[id], `missing worker schema field ${id}`);
    assert.ok(editorFields.has(id), `missing worker editor field ${id}`);
  }
});

test('event schema exposes current character-arc, progress, page, and choice media contracts', () => {
  for (const id of [
    'arc_id', 'arc_stage', 'arc_kind', 'worker_progress',
    'completion_timestamp_flag', 'description_pages', 'required_store_value',
  ]) {
    assert.ok(event_schema.fields[id], `missing event schema field ${id}`);
  }
  for (const id of ['image_skill', 'success_image', 'message_pages']) {
    assert.ok(CHOICE_FIELDS[id], `missing choice schema field ${id}`);
  }
  assert.equal(CHOICE_FIELDS.effect.fields.success.type, 'object');
  assert.equal(CHOICE_FIELDS.effect.fields.failure.type, 'object');
  assert.equal(CHOICE_FIELDS.effect.fields.success.fields.skill_modifiers.type, 'dict_of_numbers');
  assert.equal(CHOICE_FIELDS.effect.fields.success.fields.event_flags.type, 'dict_of_scalars');
  for (const name of [
    'servant_health', 'chance', 'consume_item',
    'trait_chance', 'trait_remove_chance',
  ]) {
    assert.ok(CHOICE_FIELDS.effect.fields[name], `missing event effect field ${name}`);
  }
  const event = {
    id: 'arc_test',
    choices: [{
      option: 'Continue',
      effect: { success: { event_flags: { done: true, route: 'dominion', counter: 2 } } },
    }],
  };
  assert.deepEqual(validateEntry(event, event_schema, ctx()).errors, []);
});

test('recruit event editor exposes the worker filter consumed by recruitment', () => {
  const fields = recruit_event_schema.fields.worker_filter.fields;
  for (const name of [
    'min_combat', 'min_charm', 'min_clever', 'min_craft',
    'traits_required', 'traits_excluded',
  ]) {
    assert.ok(fields?.[name], `missing recruit worker_filter field ${name}`);
  }
  assert.ok(editorFieldIds(recruit_event_editor_sections).has('worker_filter'));
});

test('daily story schema exposes every active current story, consequence, and loot contract', () => {
  for (const id of [
    'used_skill', 'story_image_fallback_patterns',
    'profile_before_image_fallback_patterns', 'no_fail',
  ]) {
    assert.ok(daily_story_schema.fields[id], `missing daily story field ${id}`);
  }
  const consequence = daily_story_schema.fields.consequences.fields.success.fields;
  assert.ok(consequence.give_item, 'give_item must be configurable');
  assert.ok(consequence.trait_chance.item_fields, 'trait_chance entries must be structured');
  assert.ok(consequence.trait_remove_chance.item_fields, 'trait_remove_chance entries must be structured');
  const loot = daily_story_schema.fields.loot.fields;
  assert.ok(loot.bonus_items.item_fields, 'bonus_items entries must be structured');
  assert.equal(loot.monster_worker.fields.filters.fields.encounter_only.type, 'bool');
});

test('trait schema exposes active aliases, expiry, and runtime modifier fields', () => {
  assert.equal(trait_schema.fields.aliases.type, 'list_of_strings');
  assert.ok(trait_schema.fields.on_expire.fields.add_trait, 'on_expire.add_trait must be configurable');
  const modifiers = trait_schema.fields.modifiers.fields;
  for (const id of [
    'joy', 'energy', 'health', 'romance', 'relationship', 'comfort_desired',
    'libido', 'health_regeneration', 'energy_regeneration', 'health_max',
    'energy_max', 'health_max_cap', 'energy_max_cap',
  ]) {
    assert.equal(modifiers[id].type, 'float', `missing trait modifier ${id}`);
  }
});

test('requested editors surface their active schema contracts', () => {
  const cases = [
    [trait_editor_sections, [
      'aliases', 'only_assigned', 'on_expire', 'attribute_caps',
      'attribute_minimums', 'daily_effects',
    ]],
    [event_editor_sections, [
      'worker_gender_requirement', 'required_building_worker_min_skill',
      'required_building_worker_skill', 'arc_id', 'arc_stage', 'arc_kind',
      'worker_progress', 'completion_timestamp_flag', 'description_pages',
      'event_music', 'event_type', 'required_store_value',
    ]],
    [daily_story_editor_sections, [
      'description', 'relevant_traits', 'trait_success', 'used_skill',
      'story_image_fallback_patterns', 'profile_before_image_fallback_patterns',
    ]],
  ];
  for (const [sections, expected] of cases) {
    const fields = editorFieldIds(sections);
    for (const id of expected) assert.ok(fields.has(id), `missing editor field ${id}`);
  }
});

test('monster worker recipe creates a unique capture-compatible authored monster', () => {
  const worker = monster_worker_recipe.build({
    name: 'Thorn Beast',
    folder: 'thorn_beast',
    gender: 'female',
    monster_archetype: 'goblin',
    extra_traits: ['Strong'],
    combat_level: 50,
    description: 'Spiky.',
    nsfw: true,
  }, ctx());
  assert.equal(worker.unique, true);
  assert.equal(worker.procedural, false);
  assert.equal(worker.monster, true);
  assert.equal(worker.encounter_only, true);
  assert.equal(worker.recruitment_locked, true);
  assert.equal(worker.monster_archetype, 'goblin');
  assert.equal(worker.template_id, 'monster_unique_thorn_beast');
  assert.deepEqual(validateEntry(worker, worker_schema, ctx()).errors, []);
});
