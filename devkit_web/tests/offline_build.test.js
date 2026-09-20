// Integrity tests for the single-file offline build.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { buildOfflineHTML } from '../scripts/build_offline.mjs';

let _html = null;
async function html() {
  if (!_html) _html = await buildOfflineHTML();
  return _html;
}

test('offline build contains all modules and no unresolved imports', async () => {
  const out = await html();
  // every src module reachable from app.js is defined
  for (const id of ['app.js', 'lib/fs.js', 'lib/ui.js', 'lib/validator.js',
    'lib/catalog_loader.js', 'recipes/_engine.js', 'editors/_engine.js',
    'schemas/event.schema.js', 'recipes/daily_stories.js']) {
    assert.ok(out.includes(`__fm.define('${id}'`), `missing module ${id}`);
  }
  // no leftover relative imports — they would fail over file://
  assert.doesNotMatch(out, /from\s+['"]\.\.?\//, 'unresolved static import remains');
  assert.doesNotMatch(out, /import\(\s*['"]/, 'unresolved dynamic import remains');
});

test('offline build inlines catalogs and styles', async () => {
  const out = await html();
  assert.ok(out.includes('__FM_BUNDLED_CATALOGS'), 'catalogs injected');
  assert.ok(out.includes('"Human"'), 'trait catalog content present');
  assert.ok(out.includes('building_professions'), 'meta catalogs present');
  assert.ok(out.includes('--accent'), 'styles inlined');
  assert.ok(!out.includes('<link rel="stylesheet"'), 'no external stylesheet');
  assert.ok(!out.includes('src="app.js"'), 'no external script');
});

test('source modules only use bundler-supported export forms', async () => {
  // The mini-bundler only understands named declaration exports. Guard against
  // someone adding `export default` or `export { ... }` re-exports later.
  const SRC = path.resolve(import.meta.dirname, '../src');
  async function walk(dir) {
    const out = [];
    for (const e of await fs.readdir(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) out.push(...await walk(p));
      else if (e.name.endsWith('.js')) out.push(p);
    }
    return out;
  }
  for (const file of await walk(SRC)) {
    const src = await fs.readFile(file, 'utf8');
    assert.doesNotMatch(src, /export\s+default/, `${file}: export default unsupported`);
    assert.doesNotMatch(src, /export\s*\{/, `${file}: export list unsupported`);
    assert.doesNotMatch(src, /import\s+[A-Za-z0-9_$]+\s+from/, `${file}: default import unsupported`);
  }
});
