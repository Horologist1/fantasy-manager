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
