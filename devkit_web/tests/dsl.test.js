import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validateField, neutralDefault } from '../src/schemas/_dsl.js';

test('string field rejects non-string', () => {
  const r = validateField({ type: 'string' }, 42);
  assert.equal(r.valid, false);
  assert.match(r.error, /string/);
});

test('string field accepts null when not required', () => {
  const r = validateField({ type: 'string' }, null);
  assert.equal(r.valid, true);
});

test('required string rejects null', () => {
  const r = validateField({ type: 'string', required: true }, null);
  assert.equal(r.valid, false);
});

test('int field accepts integers in range', () => {
  assert.equal(validateField({ type: 'int', min: 0, max: 100 }, 50).valid, true);
  assert.equal(validateField({ type: 'int', min: 0, max: 100 }, 150).valid, false);
  assert.equal(validateField({ type: 'int' }, 3.14).valid, false);
});

test('bool field accepts true/false only', () => {
  assert.equal(validateField({ type: 'bool' }, true).valid, true);
  assert.equal(validateField({ type: 'bool' }, 'yes').valid, false);
});

test('list_of_strings rejects non-array', () => {
  assert.equal(validateField({ type: 'list_of_strings' }, 'foo').valid, false);
});

test('list_of_strings rejects array with non-strings', () => {
  assert.equal(validateField({ type: 'list_of_strings' }, ['a', 2]).valid, false);
});

test('dict_of_numbers accepts {string: number}', () => {
  assert.equal(validateField({ type: 'dict_of_numbers' }, { Sex: 25 }).valid, true);
  assert.equal(validateField({ type: 'dict_of_numbers' }, { Sex: 'high' }).valid, false);
});

test('enum field accepts values from options', () => {
  const def = { type: 'enum', options: ['male', 'female'] };
  assert.equal(validateField(def, 'male').valid, true);
  assert.equal(validateField(def, 'other').valid, false);
});

test('union type accepts any of the listed types', () => {
  const def = { type: ['string', 'list_of_strings', 'null'] };
  assert.equal(validateField(def, 'Aelis').valid, true);
  assert.equal(validateField(def, ['Aelis', 'Yvara']).valid, true);
  assert.equal(validateField(def, null).valid, true);
  assert.equal(validateField(def, 42).valid, false);
});

test('neutralDefault returns the right neutral per type', () => {
  assert.equal(neutralDefault({ type: 'string' }), null);
  assert.equal(neutralDefault({ type: 'int' }), 0);
  assert.equal(neutralDefault({ type: 'bool' }), false);
  assert.deepEqual(neutralDefault({ type: 'list_of_strings' }), []);
  assert.deepEqual(neutralDefault({ type: 'dict_of_numbers' }), {});
});

// ---- nested types (plan 2) ----

test('object type validates subfields recursively', () => {
  const def = {
    type: 'object',
    fields: {
      start_when: { type: ['string', 'null'] },
      stop_when: { type: ['string', 'null'] },
    },
  };
  assert.equal(validateField(def, { start_when: null, stop_when: 'day>3' }).valid, true);
  assert.equal(validateField(def, { start_when: 42 }).valid, false);
  assert.equal(validateField(def, 'not an object').valid, false);
});

test('object type reports missing required subfields', () => {
  const def = { type: 'object', fields: { id: { type: 'string', required: true } } };
  const r = validateField(def, {});
  assert.equal(r.valid, false);
  assert.match(r.error, /id/);
});

test('list_of_objects validates each item against item_fields', () => {
  const def = {
    type: 'list_of_objects',
    item_fields: {
      trait: { type: 'string', required: true },
      chance_percent: { type: 'int', min: 1, max: 100 },
    },
  };
  assert.equal(validateField(def, [{ trait: 'Strong', chance_percent: 50 }]).valid, true);
  assert.equal(validateField(def, [{ chance_percent: 50 }]).valid, false);
  assert.equal(validateField(def, [{ trait: 'Strong', chance_percent: 500 }]).valid, false);
});

test('list_of_objects without item_fields only checks object shape', () => {
  const def = { type: 'list_of_objects' };
  assert.equal(validateField(def, [{ anything: 1 }]).valid, true);
  assert.equal(validateField(def, ['nope']).valid, false);
});

test('dict_of_bools accepts {string: bool} only', () => {
  assert.equal(validateField({ type: 'dict_of_bools' }, { flag_a: true }).valid, true);
  assert.equal(validateField({ type: 'dict_of_bools' }, { flag_a: 'yes' }).valid, false);
  assert.equal(validateField({ type: 'dict_of_bools' }, []).valid, false);
});

test('dict_of_objects validates each value against item_fields', () => {
  const def = {
    type: 'dict_of_objects',
    item_fields: {
      value: { type: 'bool' },
      duration: { type: 'int' },
    },
  };
  assert.equal(validateField(def, { cooldown: { value: true, duration: 3 } }).valid, true);
  assert.equal(validateField(def, { cooldown: { value: 'yes' } }).valid, false);
  assert.equal(validateField(def, { cooldown: 'nope' }).valid, false);
});

test('neutralDefault for nested types', () => {
  assert.deepEqual(neutralDefault({ type: 'dict_of_bools' }), {});
  assert.deepEqual(neutralDefault({ type: 'dict_of_objects' }), {});
  assert.deepEqual(
    neutralDefault({
      type: 'object',
      fields: { a: { type: 'int' }, b: { type: 'list_of_strings' } },
    }),
    { a: 0, b: [] },
  );
});
