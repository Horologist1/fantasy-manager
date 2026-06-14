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
  w.document.body.innerHTML = [
    '<header><div class="header-actions">',
    '<button id="select-game-folder"></button>',
    '<span id="folder-status" class="muted"></span>',
    '</div></header><main id="app"></main>',
  ].join('');
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

  assert.equal(w.document.querySelectorAll('.type-group').length, 9,
    '8 content groups + tools group render');
  assert.equal(w.document.querySelectorAll('.recipe-btn').length, 21,
    '19 recipes + WM importer + GIF tool render');
});
