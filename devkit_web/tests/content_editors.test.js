// Sanity: every editor section field maps to a real schema field, and the
// editor engine can render each content editor with a real entry.
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';

beforeEach(() => {
  const w = new Window();
  globalThis.document = w.document;
  globalThis.HTMLElement = w.HTMLElement;
  globalThis.Event = w.Event;
});

const CASES = [
  ['trait_editor_sections', 'trait.schema.js', 'trait_schema', { name: 'X' }],
  ['item_editor_sections', 'item.schema.js', 'item_schema', { id: 'x', name: 'X', type: 'misc' }],
  ['interaction_editor_sections', 'interaction.schema.js', 'interaction_schema', { id: 'x', name: 'X' }],
  ['event_editor_sections', 'event.schema.js', 'event_schema', { id: 'x', choices: [{ option: 'Go' }] }],
  ['recruit_event_editor_sections', 'recruit_event.schema.js', 'recruit_event_schema', { id: 'x', choices: [{ option: 'Hire', effect: { recruit_worker: true } }] }],
  ['daily_story_editor_sections', 'daily_story.schema.js', 'daily_story_schema', { id: 'x' }],
  ['building_editor_sections', 'building.schema.js', 'building_schema', { id: 'x', name: 'X', skill_name: 'S', professions: [] }],
];

test('editor sections only reference schema fields', async () => {
  const editors = await import('../src/editors/content_editors.js');
  for (const [sectionsName, schemaFile, schemaName] of CASES) {
    const schema = (await import(`../src/schemas/${schemaFile}`))[schemaName];
    for (const section of editors[sectionsName]) {
      for (const f of section.fields) {
        assert.ok(f.id in schema.fields,
          `${sectionsName}/${section.id}: field "${f.id}" not in ${schemaName}`);
      }
    }
  }
});

test('editor engine renders every content editor', async () => {
  const editors = await import('../src/editors/content_editors.js');
  const { runEditor } = await import('../src/editors/_engine.js');
  const { validateEntry } = await import('../src/lib/validator.js');
  const ctx = {
    catalogs: {
      all_traits: new Set(['Human']), all_skills: new Set(['Charm']),
      all_buildings: new Set(['tavern']), all_professions: new Set(['waitress']),
      all_worker_names: new Set(['Aelis']), all_worker_folders: new Set(['aelis']),
      all_event_flags: new Set(), all_map_locations: new Set(['tavern']),
      race_traits: new Set(['Human']), names_lists: new Set(),
    },
    meta: {},
    image_exists: () => true, file: null, entry_index: 0,
  };
  for (const [sectionsName, schemaFile, schemaName, entry] of CASES) {
    const schema = (await import(`../src/schemas/${schemaFile}`))[schemaName];
    const container = document.createElement('div');
    runEditor({
      sections: editors[sectionsName],
      entry,
      schema,
      container,
      ctx,
      defaultFilename: 'x.json',
      validate: (e) => validateEntry(e, schema, ctx),
      onSave: () => {},
    });
    assert.ok(container.querySelector('.tabs'), `${sectionsName}: tabs rendered`);
    assert.ok(container.querySelector('.editor-section'), `${sectionsName}: section rendered`);
  }
});
