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
