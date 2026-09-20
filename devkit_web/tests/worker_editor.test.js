import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';
import { worker_editor_sections } from '../src/editors/worker_editor.js';
import { worker_schema, ALL_SKILLS } from '../src/schemas/worker.schema.js';

beforeEach(() => {
  const w = new Window();
  globalThis.document = w.document;
  globalThis.HTMLElement = w.HTMLElement;
  globalThis.Event = w.Event;
});

test('every schema field appears in exactly one editor section', () => {
  const seen = new Set();
  for (const section of worker_editor_sections) {
    for (const f of section.fields) {
      assert.equal(seen.has(f.id), false, `duplicate field ${f.id}`);
      seen.add(f.id);
    }
  }
  for (const fname of Object.keys(worker_schema.fields)) {
    assert.equal(seen.has(fname), true, `schema field ${fname} not in any section`);
  }
});

test('skills section uses dict_of_numbers field', () => {
  const skills = worker_editor_sections
    .flatMap((s) => s.fields)
    .find((f) => f.id === 'skills');
  assert.equal(skills.type, 'dict_of_numbers');
});
