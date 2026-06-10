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
