// Executes the single-file offline bundle end-to-end: the inline module
// script must boot and render the landing page exactly like the served app.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Window } from 'happy-dom';
import { buildOfflineHTML } from '../scripts/build_offline.mjs';

test('offline bundle boots and renders the landing page', async () => {
  const html = await buildOfflineHTML();
  const w = new Window();
  w.document.body.innerHTML = html.match(/<body>([\s\S]*?)<script type="module">/)[1];
  globalThis.window = w;
  globalThis.document = w.document;
  globalThis.localStorage = w.localStorage;
  globalThis.HTMLElement = w.HTMLElement;
  globalThis.Event = w.Event;
  globalThis.alert = () => {};
  globalThis.confirm = () => true;

  const m = html.match(/<script type="module">\n([\s\S]*?)\n<\/script>/);
  assert.ok(m, 'inline module script found');
  const script = m[1].replace(/<\\\/script>/g, '</script>');
  const tmp = path.join(import.meta.dirname, '.tmp_bundle_exec.mjs');
  await fs.writeFile(tmp, script);
  try {
    await import(pathToFileURL(tmp).href);
  } finally {
    await fs.unlink(tmp).catch(() => {});
  }

  assert.equal(w.document.querySelectorAll('[data-type="workers"]').length, 1);
  assert.equal(w.document.querySelectorAll('[data-type="items"]').length, 0,
    'default character mode only offers compatible content');
  assert.ok(w.document.querySelector('[data-action="save-project"]'));
  assert.ok(w.document.querySelector('[data-action="review-pack"]'));
  assert.match(w.document.body.textContent, /Original game files stay unchanged/);
});
