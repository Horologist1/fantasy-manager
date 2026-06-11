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

test('list_of_strings with catalog renders a browsable picker', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const catalogs = { all_traits: new Set(['Human', 'Elf', 'Orc', 'Charming']) };
  const f = renderField(
    { id: 'traits', type: 'list_of_strings', catalog: 'all_traits', label: 'Traits' },
    ['Human'],
    () => {},
    { catalogs },
  );
  assert.ok(f.element.querySelector('.catalog-picker'),
    'should render catalog-picker container');
  assert.ok(f.element.querySelector('[data-role="search"]'),
    'should render a search input');
  const items = f.element.querySelectorAll('[data-item]');
  assert.equal(items.length, 4, 'should render one item per catalog entry');
  const selectedItem = f.element.querySelector('[data-item="Human"]');
  assert.match(selectedItem.className, /selected/, 'pre-selected items show selected state');
});

test('catalog picker click toggles selection', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const catalogs = { all_traits: new Set(['Human', 'Elf']) };
  let captured = null;
  const f = renderField(
    { id: 'traits', type: 'list_of_strings', catalog: 'all_traits' },
    [],
    (v) => (captured = v),
    { catalogs },
  );
  f.element.querySelector('[data-item="Elf"]').click();
  assert.deepEqual(captured, ['Elf']);
  assert.deepEqual(f.getValue(), ['Elf']);
  f.element.querySelector('[data-item="Elf"]').click();
  assert.deepEqual(f.getValue(), []);
});

test('catalog picker search filters the list', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const catalogs = { all_traits: new Set(['Charming', 'Charismatic', 'Elegant']) };
  const f = renderField(
    { id: 'traits', type: 'list_of_strings', catalog: 'all_traits' },
    [],
    () => {},
    { catalogs },
  );
  const search = f.element.querySelector('[data-role="search"]');
  search.value = 'char';
  search.dispatchEvent(new window.Event('input'));
  const items = f.element.querySelectorAll('[data-item]');
  assert.equal(items.length, 2, 'only Charming and Charismatic should remain');
});

test('string field with catalog shows clickable suggestion chips', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const catalogs = { image_folders: new Set(['aelis', 'yvara', 'iris']) };
  let captured = null;
  const f = renderField(
    { id: 'folder', type: 'string', catalog: 'image_folders', label: 'Folder' },
    null,
    (v) => (captured = v),
    { catalogs },
  );
  const chips = f.element.querySelectorAll('[data-suggestion]');
  assert.equal(chips.length, 3);
  chips[0].click();
  assert.equal(captured, 'aelis');
  assert.equal(f.getValue(), 'aelis');
});

test('string field without catalog does not render suggestions', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField({ id: 'name', type: 'string' }, '', () => {});
  assert.equal(f.element.querySelector('[data-role="suggestions"]'), null);
});

test('catalog picker shows meta description in info panel', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const catalogs = { all_traits: new Set(['Magical', 'Charming']) };
  const meta = {
    trait_meta: {
      Magical: { description: 'Worker can cast spells.', nsfw: false },
      Charming: { description: 'Worker attracts customers.', nsfw: false },
    },
  };
  const f = renderField(
    { id: 'traits', type: 'list_of_strings', catalog: 'all_traits' },
    ['Magical'],
    () => {},
    { catalogs, meta },
  );
  const info = f.element.querySelector('[data-role="info"]');
  assert.ok(info, 'info panel should be present when meta is provided');
  assert.match(info.textContent, /Magical/);
  assert.match(info.textContent, /cast spells/);
});

test('enum with option_descriptions renders description below select', async () => {
  const { renderField } = await import('../src/lib/ui.js');
  const f = renderField(
    {
      id: 'skill_focus',
      type: 'enum',
      options: ['combat', 'magic'],
      option_descriptions: {
        combat: 'Combat 45, Agility 40.',
        magic: 'Craft 45, Clever 40.',
      },
    },
    'combat',
    () => {},
  );
  const desc = f.element.querySelector('[data-role="option-description"]');
  assert.ok(desc);
  assert.match(desc.textContent, /Combat 45/);
  f.setValue('magic');
  assert.match(desc.textContent, /Craft 45/);
});
