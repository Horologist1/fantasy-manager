// devkit_web/tests/ui.test.js
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';

let window;
beforeEach(() => {
  window = new Window();
  globalThis.document = window.document;
  globalThis.HTMLElement = window.HTMLElement;
});

test('text field round-trips value', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField({ id: 'name', type: 'string', label: 'Name' }, 'Aelis', () => {});
  assert.equal(f.getValue(), 'Aelis');
  f.setValue('Yvara');
  assert.equal(f.getValue(), 'Yvara');
});

test('text field fires onChange', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  let captured = null;
  const f = renderField({ id: 'name', type: 'string' }, '', (v) => (captured = v));
  const input = f.element.querySelector('input');
  input.value = 'Iris';
  input.dispatchEvent(new window.Event('input'));
  assert.equal(captured, 'Iris');
});

test('bool field uses a checkbox', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField({ id: 'nsfw', type: 'bool' }, true, () => {});
  assert.equal(f.element.querySelector('input').type, 'checkbox');
  assert.equal(f.getValue(), true);
});

test('int field clamps non-integers', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField({ id: 'cost', type: 'int' }, 100, () => {});
  f.setValue(3.7);
  assert.equal(f.getValue(), 3);
});

test('enum field uses a select with options', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField(
    { id: 'gender', type: 'enum', options: ['male', 'female'] },
    'female',
    () => {},
  );
  const sel = f.element.querySelector('select');
  assert.equal(sel.options.length, 2);
  assert.equal(f.getValue(), 'female');
});

test('list_of_strings renders chips and adds new on Enter', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField(
    { id: 'traits', type: 'list_of_strings' },
    ['Human'],
    () => {},
  );
  assert.deepEqual(f.getValue(), ['Human']);
  f.setValue(['Human', 'Elf']);
  assert.deepEqual(f.getValue(), ['Human', 'Elf']);
});

test('dict_of_numbers exposes key-value editor', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField(
    { id: 'skills', type: 'dict_of_numbers' },
    { Sex: 25, Combat: 30 },
    () => {},
  );
  assert.deepEqual(f.getValue(), { Sex: 25, Combat: 30 });
});

test('setError adds aria-invalid + error message', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField({ id: 'x', type: 'string' }, '', () => {});
  f.setError('required');
  assert.match(f.element.outerHTML, /required/);
});
