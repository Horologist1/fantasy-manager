// devkit_web/tests/editor_engine.test.js
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';

beforeEach(() => {
  const w = new Window();
  globalThis.document = w.document;
  globalThis.HTMLElement = w.HTMLElement;
  globalThis.Event = w.Event;
});

const sections = [
  { id: 'basic', label: 'Basic', fields: [
    { id: 'name', type: 'string', label: 'Name' },
    { id: 'cost', type: 'int', label: 'Cost' },
  ]},
  { id: 'traits', label: 'Traits', fields: [
    { id: 'traits', type: 'list_of_strings', label: 'Traits' },
  ]},
];

test('editor renders first section by default', async () => {
  const { runEditor } = await import('../src/editors/_engine.js');
  const root = document.createElement('div');
  runEditor({
    sections,
    entry: { name: 'Aelis', cost: 1200, traits: ['Human'] },
    schema: { fields: {}, rules: [] },
    container: root,
    ctx: {},
    onSave: () => {},
  });
  assert.ok(root.querySelector('[data-section="basic"]'));
  assert.equal(root.querySelector('[data-field="name"] input').value, 'Aelis');
});

test('clicking a tab jumps to that section', async () => {
  const { runEditor } = await import('../src/editors/_engine.js');
  const root = document.createElement('div');
  runEditor({
    sections,
    entry: { name: 'A', cost: 0, traits: [] },
    schema: { fields: {}, rules: [] },
    container: root, ctx: {}, onSave: () => {},
  });
  root.querySelector('[data-tab="traits"]').click();
  assert.ok(root.querySelector('[data-section="traits"]'));
});

test('Save returns the edited entry', async () => {
  const { runEditor } = await import('../src/editors/_engine.js');
  const root = document.createElement('div');
  let saved = null;
  runEditor({
    sections,
    entry: { name: 'A', cost: 0, traits: [] },
    schema: { fields: {}, rules: [] },
    container: root, ctx: {},
    onSave: (e) => (saved = e),
  });
  const nameInput = root.querySelector('[data-field="name"] input');
  nameInput.value = 'B';
  nameInput.dispatchEvent(new Event('input'));
  root.querySelector('[data-tab="review"]').click();
  root.querySelector('[data-action="save"]').click();
  assert.equal(saved.name, 'B');
});

test('validation panel renders errors on Review', async () => {
  const { runEditor } = await import('../src/editors/_engine.js');
  const root = document.createElement('div');
  const tinySchema = {
    fields: { name: { type: 'string', required: true } },
    rules: [], legacy: {},
  };
  runEditor({
    sections: [{ id: 'b', label: 'B', fields: [{ id: 'name', type: 'string', label: 'Name' }] }],
    entry: { name: null },
    schema: tinySchema,
    container: root,
    ctx: {},
    onSave: () => {},
    validate: (e) => {
      // Synchronous validation: build the result inline using imported validateEntry.
      // We can't dynamically import inside this callback because runEditor calls it sync.
      // Instead we return a hand-crafted result mimicking what validateEntry would produce
      // for a missing required field. This test just asserts the panel renders.
      return {
        errors: [{ field: 'name', error: 'required', rule: null }],
        warnings: [],
        migrations: [],
      };
    },
  });
  root.querySelector('[data-tab="review"]').click();
  // panel should render with at least one .val-error
  assert.ok(root.querySelector('[data-section="review"]'));
  assert.ok(root.querySelector('.val-error'));
});

// --- Forward-compatibility: keys the editor has no field for must round-trip
// untouched on save. The game (or another mod) may add keys this build of the
// devkit doesn't know; editing an entry must never silently drop them.
// (Guards the copy-then-mutate behaviour in _engine.js + lib/ui.js renderers.)
const nestedSections = [
  { id: 'basic', label: 'Basic', fields: [
    { id: 'id', type: 'string', label: 'Id' },
  ]},
  { id: 'conditions', label: 'Conditions', fields: [
    { id: 'conditions', type: 'object', label: 'Conditions', fields: {
      start_when: { type: ['string', 'null'], label: 'Start when' },
      stop_when: { type: ['string', 'null'], label: 'Stop when' },
    }},
  ]},
  { id: 'choices', label: 'Choices', fields: [
    { id: 'choices', type: 'list_of_objects', label: 'Choices', item_label: 'Choice', item_fields: {
      text: { type: 'string', label: 'Text' },
      result: { type: ['string', 'null'], label: 'Result' },
    }},
  ]},
];

test('unknown top-level keys survive a save (no field renders them)', async () => {
  const { runEditor } = await import('../src/editors/_engine.js');
  const root = document.createElement('div');
  let saved = null;
  runEditor({
    sections: nestedSections,
    entry: {
      id: 'evt_1',
      conditions: { start_when: null, stop_when: null },
      choices: [],
      // No section/field declares these — they must round-trip untouched:
      outcome_override: { good: 'win', bad: 'lose' },
      worker_filter: 'mages',
    },
    schema: { fields: {}, rules: [] },
    container: root, ctx: {},
    onSave: (e) => (saved = e),
  });
  // Edit a known field so the entry is genuinely re-serialised on save.
  const idInput = root.querySelector('[data-field="id"] input');
  idInput.value = 'evt_2';
  idInput.dispatchEvent(new Event('input'));
  root.querySelector('[data-tab="review"]').click();
  root.querySelector('[data-action="save"]').click();
  assert.equal(saved.id, 'evt_2');
  assert.deepEqual(saved.outcome_override, { good: 'win', bad: 'lose' });
  assert.equal(saved.worker_filter, 'mages');
});

test('unknown keys inside an EDITED object field survive', async () => {
  const { runEditor } = await import('../src/editors/_engine.js');
  const root = document.createElement('div');
  let saved = null;
  runEditor({
    sections: nestedSections,
    entry: {
      id: 'evt_1',
      // legacy_extra is not in the object's declared fields:
      conditions: { start_when: 'day > 1', stop_when: null, legacy_extra: 'KEEP_ME' },
      choices: [],
    },
    schema: { fields: {}, rules: [] },
    container: root, ctx: {},
    onSave: (e) => (saved = e),
  });
  root.querySelector('[data-tab="conditions"]').click();
  const sw = root.querySelector('[data-field="conditions"] [data-field="start_when"] input');
  sw.value = 'day > 3';
  sw.dispatchEvent(new Event('input'));
  root.querySelector('[data-tab="review"]').click();
  root.querySelector('[data-action="save"]').click();
  assert.equal(saved.conditions.start_when, 'day > 3');
  assert.equal(saved.conditions.legacy_extra, 'KEEP_ME');
});

test('unknown keys inside an EDITED list_of_objects item survive', async () => {
  const { runEditor } = await import('../src/editors/_engine.js');
  const root = document.createElement('div');
  let saved = null;
  runEditor({
    sections: nestedSections,
    entry: {
      id: 'evt_1',
      conditions: { start_when: null, stop_when: null },
      // outcome_override is not in the item's declared item_fields:
      choices: [{ text: 'Fight', result: null, outcome_override: 'special' }],
    },
    schema: { fields: {}, rules: [] },
    container: root, ctx: {},
    onSave: (e) => (saved = e),
  });
  root.querySelector('[data-tab="choices"]').click();
  const textInput = root.querySelector('[data-field="choices"] [data-field="text"] input');
  textInput.value = 'Flee';
  textInput.dispatchEvent(new Event('input'));
  root.querySelector('[data-tab="review"]').click();
  root.querySelector('[data-action="save"]').click();
  assert.equal(saved.choices[0].text, 'Flee');
  assert.equal(saved.choices[0].outcome_override, 'special');
});
