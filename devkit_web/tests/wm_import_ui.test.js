// End-to-end UI test of the WM importer with a mocked File System Access
// directory handle: Source → Settings → Review → resolve unknown trait →
// Import (merged into a memory fs as the "game folder").
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';
import { createMemoryFS } from '../src/lib/fs.js';

let w;
beforeEach(() => {
  w = new Window();
  globalThis.window = w;
  globalThis.document = w.document;
  globalThis.localStorage = w.localStorage;
  globalThis.HTMLElement = w.HTMLElement;
  globalThis.Event = w.Event;
  globalThis.DOMParser = w.DOMParser;
  globalThis.alert = () => {};
  localStorage.clear();
});

const GIRL_XML = `<Girls>
  <Girl Name="Mira Stormcaller" FirstName="Mira" Desc="A storm mage." AskPrice="300"
        Magic="70" Combat="40">
    <Trait Name="Elf"/>
    <Trait Name="Storm Affinity"/>
  </Girl>
</Girls>`;

function fakeFile(name, content) {
  return {
    kind: 'file',
    async getFile() {
      return {
        async text() { return content; },
        async arrayBuffer() { return new ArrayBuffer(1); },
      };
    },
  };
}

function fakeDir(entries) {
  return {
    kind: 'directory',
    async* entries() {
      for (const [name, e] of Object.entries(entries)) yield [name, e];
    },
    async getFileHandle(name) {
      if (!entries[name]) throw new Error(`no file ${name}`);
      return entries[name];
    },
    async getDirectoryHandle(name) {
      if (!entries[name]) throw new Error(`no dir ${name}`);
      return entries[name];
    },
  };
}

function makeDeps(fs, overrides = {}) {
  return {
    ctx: () => ({
      catalogs: {
        all_traits: new Set(['Human', 'Elf', 'Strong Magic', 'Magical', 'Charming']),
        race_traits: new Set(['Human', 'Elf']),
        all_worker_names: new Set(['Aelis']),
        all_worker_folders: new Set(['aelis']),
        all_skills: new Set(), names_lists: new Set(),
      },
      meta: {},
      image_exists: () => true, file: null, entry_index: 0,
    }),
    fs,
    hasGameFolder: () => true,
    getGameHandle: () => null,
    modname: 'mymod',
    onDone: () => {},
    ...overrides,
  };
}

async function tick() {
  await new Promise((r) => setTimeout(r, 0));
}

test('suggestTraits ranks close names first', async () => {
  const { suggestTraits } = await import('../src/converters/wm_import_ui.js');
  const out = suggestTraits('Charming Person', new Set(['Charming', 'Strong', 'Obedient']));
  assert.equal(out[0], 'Charming');
});

test('full importer flow: scan, review, resolve, import', async () => {
  const { runWMImporter } = await import('../src/converters/wm_import_ui.js');
  const fs = createMemoryFS();
  const container = document.createElement('div');

  const wmFolder = fakeDir({
    'mira.girlsx': fakeFile('mira.girlsx', GIRL_XML),
    'Mira Stormcaller': fakeDir({ 'Portrait.png': fakeFile('Portrait.png', 'x') }),
  });
  w.showDirectoryPicker = async () => wmFolder;

  runWMImporter(container, makeDeps(fs));

  // 1 · Source
  container.querySelector('[data-action="pick-source"]').dispatchEvent(new Event('click'));
  await tick(); await tick();

  // 2 · Settings — shows the found character, keep defaults
  assert.match(container.textContent, /Found 1 characters/);
  container.querySelector('[data-action="next"]').dispatchEvent(new Event('click'));
  await tick();

  // 3 · Review — Mira present with unknown trait warning
  assert.ok(container.querySelector('[data-character="Mira"]'));
  const unknownBtn = container.querySelector('[data-unknown-trait="Storm Affinity"]');
  assert.ok(unknownBtn, 'unknown trait shows a resolve button');

  // resolve as a new stub trait
  unknownBtn.dispatchEvent(new Event('click'));
  await tick();
  container.querySelector('[data-action="new-trait"]').dispatchEvent(new Event('click'));
  await tick();

  // back on review: no more pending warnings, trait now applied
  assert.equal(container.querySelector('[data-unknown-trait]'), null);
  assert.match(container.textContent, /Storm Affinity/);

  // 4 · Import
  container.querySelector('[data-action="import"]').dispatchEvent(new Event('click'));
  await tick(); await tick(); await tick();

  const workers = await fs.readJSON('workers/workers_mymod_wm.json');
  assert.equal(workers.length, 1);
  assert.equal(workers[0].name, 'Mira');
  assert.equal(workers[0].unique, true);
  assert.equal(workers[0].comfort_desired, 2); // AskPrice 300
  assert.ok(workers[0].traits.includes('Elf'));
  assert.ok(workers[0].traits.includes('Storm Affinity'));
  assert.ok(!workers[0].traits.includes('Human'));
  assert.equal(workers[0].skills.Craft, 70); // Magic→Craft

  const stubs = await fs.readJSON('traits/traits_mymod_wm.json');
  assert.equal(stubs.length, 1);
  assert.equal(stubs[0].name, 'Storm Affinity');

  // resolution remembered for future imports
  const saved = JSON.parse(localStorage.getItem('fm_devkit_wm_trait_resolutions'));
  assert.equal(saved['Storm Affinity'], 'Storm Affinity');
});
