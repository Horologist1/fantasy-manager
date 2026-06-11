// devkit_web/src/app.js
import { runRecipe } from './recipes/_engine.js';
import { unique_worker_recipe } from './recipes/unique_worker.js';
import { runEditor } from './editors/_engine.js';
import { worker_editor_sections } from './editors/worker_editor.js';
import { worker_schema, RACE_TRAITS } from './schemas/worker.schema.js';
import { validateEntry } from './lib/validator.js';
import { createMemoryFS, createFSAFS } from './lib/fs.js';

const app = document.getElementById('app');
const folderStatus = document.getElementById('folder-status');
const selectBtn = document.getElementById('select-game-folder');

let fs = createMemoryFS();
let rootHandle = null;
let catalogs = await loadBundledCatalogs();
let modname = localStorage.getItem('fm_devkit_modname') || 'mymod';

selectBtn.addEventListener('click', async () => {
  if (!('showDirectoryPicker' in window)) {
    alert('File System Access API not available. Use Chrome/Edge/Brave.');
    return;
  }
  rootHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
  const gameHandle = await rootHandle.getDirectoryHandle('game').catch(() => rootHandle);
  const dataHandle = await gameHandle.getDirectoryHandle('data');
  fs = createFSAFS(dataHandle);
  catalogs = await loadLiveCatalogs(dataHandle, gameHandle);
  folderStatus.textContent = `Folder: ${rootHandle.name}`;
  folderStatus.classList.remove('muted');
  renderLanding();
});

async function loadBundledCatalogs() {
  const names = ['all_traits', 'race_traits', 'all_items', 'all_buildings',
    'all_professions', 'all_worker_names', 'all_worker_folders',
    'all_event_flags', 'names_lists', 'image_folders'];
  const out = {};
  for (const n of names) {
    try {
      const r = await fetch(`./catalogs/${n}.json`);
      out[n] = new Set(await r.json());
    } catch {
      out[n] = new Set(n === 'race_traits' ? RACE_TRAITS : []);
    }
  }
  out.meta = {};
  for (const m of ['trait_meta', 'item_meta', 'building_meta']) {
    try {
      const r = await fetch(`./catalogs/${m}.json`);
      out.meta[m] = await r.json();
    } catch {
      out.meta[m] = {};
    }
  }
  return out;
}

async function loadLiveCatalogs(dataHandle, gameHandle) {
  const { buildCatalogs } = await import('./lib/catalog_loader.js');
  const folders = ['traits', 'items', 'buildings', 'workers', 'interactions', 'events'];
  const sources = {};
  for (const f of folders) {
    sources[f] = [];
    try {
      const dir = await dataHandle.getDirectoryHandle(f);
      for await (const [name, entry] of dir.entries()) {
        if (entry.kind !== 'file' || !name.endsWith('.json')) continue;
        const file = await entry.getFile();
        try { sources[f].push(JSON.parse(await file.text())); } catch {}
      }
    } catch {}
  }
  const out = buildCatalogs(sources);

  // image_folders is scanned directly from game/images/workers/ — it isn't a
  // JSON data source so it lives outside buildCatalogs.
  out.image_folders = new Set();
  try {
    const imagesHandle = await gameHandle.getDirectoryHandle('images');
    const workersHandle = await imagesHandle.getDirectoryHandle('workers');
    for await (const [name, entry] of workersHandle.entries()) {
      if (entry.kind === 'directory') out.image_folders.add(name);
    }
  } catch {}

  // names_lists is read from game/data/names.json — buildCatalogs doesn't know
  // about it because it isn't one of the array-of-entries folders.
  try {
    const namesHandle = await dataHandle.getFileHandle('names.json');
    const namesFile = await namesHandle.getFile();
    const namesObj = JSON.parse(await namesFile.text());
    out.names_lists = new Set(Object.keys(namesObj));
  } catch {}

  return out;
}

function ctx() {
  return { catalogs, image_exists: () => true, file: null, entry_index: 0 };
}

function renderLanding() {
  app.innerHTML = '';
  const tiles = document.createElement('div');
  tiles.className = 'tiles';

  const recipeTile = tile('Create with recipe',
    'Guided wizard. Currently available: Unique Worker.', () => startRecipe(unique_worker_recipe));
  const editTile = tile('Edit existing worker JSON',
    'Open a workers_*.json file and edit entries.', () => openExistingWorkers());

  tiles.appendChild(recipeTile);
  tiles.appendChild(editTile);

  const modnameRow = document.createElement('div');
  modnameRow.style.marginTop = '1.5rem';
  modnameRow.innerHTML = `<label>Mod name (filename prefix): </label>`;
  const mInput = document.createElement('input');
  mInput.type = 'text';
  mInput.value = modname;
  mInput.addEventListener('input', () => {
    modname = mInput.value || 'mymod';
    localStorage.setItem('fm_devkit_modname', modname);
  });
  modnameRow.appendChild(mInput);

  app.appendChild(tiles);
  app.appendChild(modnameRow);
}

function tile(title, desc, onClick) {
  const t = document.createElement('div');
  t.className = 'tile';
  t.innerHTML = `<h3>${title}</h3><p>${desc}</p>`;
  t.addEventListener('click', onClick);
  return t;
}

async function startRecipe(recipe) {
  app.innerHTML = '';
  const out = await runRecipe(recipe, app, { modname, ctx: ctx() });
  const r = validateEntry(out.json, worker_schema, ctx());
  if (r.errors.length) {
    if (!confirm(`${r.errors.length} validation errors. Save anyway?`)) {
      renderLanding();
      return;
    }
  }
  if (!rootHandle) {
    // No game folder selected: download the JSON as a file so the user can
    // drop it into their game manually. (Memory FS writes would be silent.)
    const basename = out.filename.split('/').pop();
    downloadJSON(out.json, basename);
    alert(
      `Downloaded ${basename}.\n\n` +
      `Drop it into your game's game/data/${out.filename.split('/').slice(0, -1).join('/')}/ folder, ` +
      `or click "📂 Select game folder" first to save directly next time.`,
    );
  } else {
    try {
      await fs.mergeAndWrite(out.filename, out.json, { key: 'name' });
      alert(`Saved to game/data/${out.filename}`);
    } catch (err) {
      alert(`Save failed: ${err.message}\n\nThe JSON will be downloaded instead.`);
      downloadJSON(out.json, out.filename.split('/').pop());
    }
  }
  renderLanding();
}

function downloadJSON(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2) + '\n'], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function openExistingWorkers() {
  if (!rootHandle) {
    alert('Select your game folder first (top-right button).');
    return;
  }
  const list = await fs.listDir('workers');
  const choice = prompt(`Workers files:\n${list.join('\n')}\n\nEnter filename:`, list[0] || '');
  if (!choice) return;
  const entries = await fs.readJSON(`workers/${choice}`);
  if (!Array.isArray(entries) || entries.length === 0) {
    alert('File is empty or not an array.');
    return;
  }
  const nameChoice = prompt(`Worker names in file:\n${entries.map((e) => e.name).join('\n')}\n\nEnter name to edit:`, entries[0].name);
  const entry = entries.find((e) => e.name === nameChoice);
  if (!entry) return;
  app.innerHTML = '';
  runEditor({
    sections: worker_editor_sections,
    entry,
    schema: worker_schema,
    container: app,
    ctx: ctx(),
    defaultFilename: `workers/${choice}`,
    validate: (e) => validateEntry(e, worker_schema, ctx()),
    onSave: async (updated, filename) => {
      await fs.mergeAndWrite(filename, updated, { key: 'name' });
      alert(`Saved to ${filename}`);
      renderLanding();
    },
  });
}

renderLanding();
