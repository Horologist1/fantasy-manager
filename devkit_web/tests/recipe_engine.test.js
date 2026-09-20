// devkit_web/tests/recipe_engine.test.js
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';

beforeEach(() => {
  const w = new Window();
  globalThis.document = w.document;
  globalThis.HTMLElement = w.HTMLElement;
  globalThis.Event = w.Event;
});

const fakeRecipe = {
  id: 'fake',
  title: 'Fake Recipe',
  default_output: 'workers/workers_<modname>_test.json',
  steps: [
    { id: 'name', type: 'string', label: 'Name', required: true },
    { id: 'nsfw', type: 'bool', label: 'NSFW?', default: false },
  ],
  build: (answers) => ({ name: answers.name, nsfw: answers.nsfw }),
};

test('engine renders the first step', async () => {
  const { runRecipe } = await import('../src/recipes/_engine.js');
  const root = document.createElement('div');
  runRecipe(fakeRecipe, root, { modname: 'mymod' });
  assert.ok(root.querySelector('[data-field="name"]'));
  assert.equal(root.querySelectorAll('[data-step]').length, 1);
});

test('engine collects answers across Next clicks', async () => {
  const { runRecipe } = await import('../src/recipes/_engine.js');
  const root = document.createElement('div');
  const promise = runRecipe(fakeRecipe, root, { modname: 'mymod' });

  root.querySelector('[data-field="name"] input').value = 'Aelis';
  root.querySelector('[data-field="name"] input').dispatchEvent(new Event('input'));
  root.querySelector('[data-action="next"]').click();

  root.querySelector('[data-field="nsfw"] input').click();
  root.querySelector('[data-action="next"]').click();

  // now on review
  const filenameInput = root.querySelector('[data-action="filename"]');
  assert.equal(filenameInput.value, 'workers/workers_mymod_test.json');
  root.querySelector('[data-action="save"]').click();

  const out = await promise;
  assert.deepEqual(out.json, { name: 'Aelis', nsfw: true });
  assert.equal(out.filename, 'workers/workers_mymod_test.json');
});

test('required field blocks Next until filled', async () => {
  const { runRecipe } = await import('../src/recipes/_engine.js');
  const root = document.createElement('div');
  runRecipe(fakeRecipe, root, { modname: 'mymod' });
  const next = root.querySelector('[data-action="next"]');
  next.click();
  // still on step 1
  assert.ok(root.querySelector('[data-field="name"][aria-invalid="true"]'));
});

test('step options can be a function of (ctx, answers)', async () => {
  const { runRecipe } = await import('../src/recipes/_engine.js');
  const recipe = {
    id: 'r',
    title: 'R',
    default_output: 'x/<modname>.json',
    steps: [
      { id: 'building', type: 'enum', options: ['tavern', 'farm'], default: 'tavern' },
      {
        id: 'profession',
        type: 'enum',
        options: (ctx, answers) => (answers.building === 'tavern' ? ['waitress'] : ['farmhand']),
      },
    ],
    build: (a) => a,
  };
  const container = document.createElement('div');
  const p = runRecipe(recipe, container, { modname: 'm', ctx: {} });

  // step 1: building (default tavern) → next
  container.querySelector('[data-action="next"]').dispatchEvent(new Event('click'));
  // step 2: profession options resolved from answers.building
  const sel = container.querySelector('select');
  const opts = [...sel.options].map((o) => o.value);
  assert.deepEqual(opts, ['waitress']);
  container.querySelector('[data-action="next"]').dispatchEvent(new Event('click'));
  container.querySelector('[data-action="save"]').dispatchEvent(new Event('click'));
  const out = await p;
  assert.equal(out.json.building, 'tavern');
});

test('review shows summary, collapsed JSON, and edit handoff', async () => {
  const { runRecipe } = await import('../src/recipes/_engine.js');
  const recipe = {
    id: 'r2', title: 'R2', default_output: 'traits/traits_<modname>.json',
    steps: [{ id: 'name', type: 'string', label: 'Name' }],
    build: (a) => ({ name: a.name, nsfw: false }),
  };
  const container = document.createElement('div');
  const p = runRecipe(recipe, container, { modname: 'm', ctx: {} });
  const input = container.querySelector('input[type="text"]');
  input.value = 'Brave';
  input.dispatchEvent(new Event('input'));
  container.querySelector('[data-action="next"]').dispatchEvent(new Event('click'));

  assert.ok(container.querySelector('[data-role="summary"]'), 'summary shown');
  assert.ok(container.querySelector('details .json-preview'), 'raw JSON collapsed in details');
  const editBtn = container.querySelector('[data-action="edit"]');
  assert.ok(editBtn, 'edit button present for object output');
  editBtn.dispatchEvent(new Event('click'));
  const out = await p;
  assert.equal(out.edit, true);
  assert.equal(out.json.name, 'Brave');
});

test('review hides edit button for array outputs', async () => {
  const { runRecipe } = await import('../src/recipes/_engine.js');
  const recipe = {
    id: 'r3', title: 'R3', default_output: 'events/e_<modname>.json',
    steps: [{ id: 'x', type: 'string', label: 'X' }],
    build: () => [{ id: 'a' }, { id: 'b' }],
  };
  const container = document.createElement('div');
  runRecipe(recipe, container, { modname: 'm', ctx: {} });
  container.querySelector('[data-action="next"]').dispatchEvent(new Event('click'));
  assert.equal(container.querySelector('[data-action="edit"]'), null);
  assert.ok(container.querySelector('[data-action="save"]'));
});
