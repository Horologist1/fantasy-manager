// devkit_web/tests/smoke.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';

test('smoke: node test runner works', () => {
  assert.equal(1 + 1, 2);
});
