// devkit_web/src/app.js
import { runRecipe } from './recipes/_engine.js';
import { runEditor } from './editors/_engine.js';
import { validateEntry } from './lib/validator.js';
import { createMemoryFS, createFSAFS, mergeDailyStoryExtension } from './lib/fs.js';

import { worker_schema, RACE_TRAITS } from './schemas/worker.schema.js';
import { trait_schema } from './schemas/trait.schema.js';
import { item_schema } from './schemas/item.schema.js';
import { interaction_schema } from './schemas/interaction.schema.js';
import { event_schema } from './schemas/event.schema.js';
import { recruit_event_schema } from './schemas/recruit_event.schema.js';
import { daily_story_schema } from './schemas/daily_story.schema.js';
import { building_schema } from './schemas/building.schema.js';

import { worker_editor_sections } from './editors/worker_editor.js';
import {
  trait_editor_sections, item_editor_sections, interaction_editor_sections,
  event_editor_sections, recruit_event_editor_sections,
  daily_story_editor_sections, building_editor_sections,
} from './editors/content_editors.js';

import { unique_worker_recipe } from './recipes/unique_worker.js';
import { monster_worker_recipe, procedural_worker_template_recipe } from './recipes/workers.js';
import { permanent_trait_recipe, temporary_trait_recipe } from './recipes/traits.js';
import { consumable_item_recipe, equipment_item_recipe, quest_item_recipe } from './recipes/items.js';
import {
  simple_interaction_recipe, trait_granting_interaction_recipe,
  worker_specific_interaction_recipe,
} from './recipes/interactions.js';
import { daily_story_basic_recipe, daily_story_with_trait_roll_recipe } from './recipes/daily_stories.js';
import {
  worker_specific_event_recipe, event_chain_2_steps_recipe,
  building_event_with_skill_check_recipe, recruitment_event_recipe,
} from './recipes/events.js';
import { simple_building_type_recipe, add_profession_to_building_recipe } from './recipes/buildings.js';
import { runWMImporter } from './converters/wm_import_ui.js';

const app = document.getElementById('app');
const folderStatus = document.getElementById('folder-status');
const selectBtn = document.getElementById('select-game-folder');

let fs = createMemoryFS();
let rootHandle = null;
let gameDirHandle = null;
let catalogs = await loadBundledCatalogs();
let modname = localStorage.getItem('fm_devkit_modname') || 'mymod';

/**
 * Content type registry. `folder` is the game/data subfolder; `wrapper` is the
 * root-object array key for non-array files; `key` is the merge key.
 */
const TYPES = [
  {
    id: 'workers', title: '👤 Workers',
    blurb: 'Hireable characters: unique, procedural, monsters.',
    folder: 'workers', key: 'name', wrapper: null,
    schema: worker_schema, sections: worker_editor_sections,
    recipes: [unique_worker_recipe, procedural_worker_template_recipe, monster_worker_recipe],
  },
  {
    id: 'traits', title: '✨ Traits',
    blurb: 'Character traits with skill and earnings modifiers.',
    folder: 'traits', key: 'name', wrapper: null,
    schema: trait_schema, sections: trait_editor_sections,
    recipes: [permanent_trait_recipe, temporary_trait_recipe],
  },
  {
    id: 'items', title: '🎒 Items',
    blurb: 'Consumables, equipment and quest items.',
    folder: 'items', key: 'id', wrapper: 'items',
    schema: item_schema, sections: item_editor_sections,
    recipes: [consumable_item_recipe, equipment_item_recipe, quest_item_recipe],
  },
  {
    id: 'interactions', title: '💬 Interactions',
    blurb: 'Talk/activity options in the worker menu.',
    folder: 'interactions', key: 'id', wrapper: null,
    schema: interaction_schema, sections: interaction_editor_sections,
    recipes: [
      simple_interaction_recipe, trait_granting_interaction_recipe,
      worker_specific_interaction_recipe,
    ],
  },
  {
    id: 'events', title: '⚡ Events',
    blurb: 'Story scenes with choices, skill checks and flags.',
    folder: 'events', key: 'id', wrapper: null,
    schema: event_schema, sections: event_editor_sections,
    recipes: [
      worker_specific_event_recipe, event_chain_2_steps_recipe,
      building_event_with_skill_check_recipe,
    ],
  },
  {
    id: 'recruit_events', title: '🤝 Recruitment Events',
    blurb: 'Applicants who show up looking for work.',
    folder: 'events/recruit', key: 'id', wrapper: null,
    schema: recruit_event_schema, sections: recruit_event_editor_sections,
    recipes: [recruitment_event_recipe],
  },
  {
    id: 'daily_stories', title: '📜 Daily Stories',
    blurb: 'Work-day stories for existing jobs (saved as extensions).',
    folder: 'buildings/daily_story_extensions', key: 'id', wrapper: null,
    schema: daily_story_schema, sections: daily_story_editor_sections,
    recipes: [daily_story_basic_recipe, daily_story_with_trait_roll_recipe],
  },
  {
    id: 'buildings', title: '🏠 Buildings',
    blurb: 'Building types with jobs and daily stories.',
    folder: 'buildings', key: 'id', wrapper: 'building_types',
    schema: building_schema, sections: building_editor_sections,
    recipes: [simple_building_type_recipe, add_profession_to_building_recipe],
  },
];

selectBtn.addEventListener('click', async () => {
  if (!('showDirectoryPicker' in window)) {
    alert('File System Access API not available. Use Chrome/Edge/Brave.');
    return;
  }
  rootHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
  const gameHandle = await rootHandle.getDirectoryHandle('game').catch(() => rootHandle);
  gameDirHandle = gameHandle;
  const dataHandle = await gameHandle.getDirectoryHandle('data');
  fs = createFSAFS(dataHandle);
  catalogs = await loadLiveCatalogs(dataHandle, gameHandle);
  folderStatus.textContent = `Folder: ${rootHandle.name}`;
  folderStatus.classList.remove('muted');
  renderLanding();
});

async function loadBundledCatalogs() {
  // The single-file offline build (dist/FantasyManagerDevkit.html) inlines all
  // catalog JSONs as window.__FM_BUNDLED_CATALOGS because fetch() does not
  // work over file://. The served version fetches them as usual.
  const inline = typeof window !== 'undefined' ? window.__FM_BUNDLED_CATALOGS : null;
  const names = ['all_traits', 'race_traits', 'all_items', 'all_buildings',
    'all_professions', 'all_skills', 'all_map_locations',
    'all_worker_names', 'all_worker_folders',
    'all_event_flags', 'names_lists', 'image_folders'];
  const out = {};
  for (const n of names) {
    if (inline) {
      out[n] = new Set(inline[n] || (n === 'race_traits' ? RACE_TRAITS : []));
      continue;
    }
    try {
      const r = await fetch(`./catalogs/${n}.json`);
      out[n] = new Set(await r.json());
    } catch {
      out[n] = new Set(n === 'race_traits' ? RACE_TRAITS : []);
    }
  }
  out.meta = {};
  for (const m of ['trait_meta', 'item_meta', 'building_meta',
    'building_professions', 'building_full']) {
    if (inline) {
      out.meta[m] = inline[m] || {};
      continue;
    }
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
  return {
    catalogs,
    meta: catalogs.meta || {},
    image_exists: () => true,
    file: null,
    entry_index: 0,
  };
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k.startsWith('on') && typeof v === 'function') {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (v !== undefined && v !== null) node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}

// ---------- landing ----------

function renderLanding() {
  app.innerHTML = '';

  const modnameRow = el('div', { class: 'modname-row' });
  modnameRow.appendChild(el('label', {}, 'Mod name (filename prefix): '));
  const mInput = el('input', { type: 'text' });
  mInput.value = modname;
  mInput.addEventListener('input', () => {
    modname = mInput.value || 'mymod';
    localStorage.setItem('fm_devkit_modname', modname);
  });
  modnameRow.appendChild(mInput);
  app.appendChild(modnameRow);

  if (!rootHandle) {
    app.appendChild(el('div', { class: 'banner' },
      'Working from bundled catalogs. Click "📂 Select game folder" (top right) to use ',
      'your installed game data and save files directly.'));
  }

  for (const type of TYPES) {
    const group = el('div', { class: 'type-group', 'data-type': type.id });
    group.appendChild(el('h2', {}, type.title));
    group.appendChild(el('p', { class: 'muted' }, type.blurb));
    const row = el('div', { class: 'type-actions' });
    for (const recipe of type.recipes) {
      row.appendChild(el('button', {
        type: 'button', class: 'recipe-btn', title: recipe.description,
        onclick: () => startRecipe(type, recipe),
      }, `＋ ${recipe.title}`));
    }
    row.appendChild(el('button', {
      type: 'button', class: 'edit-btn',
      onclick: () => openExisting(type),
    }, '✏ Edit existing…'));
    group.appendChild(row);
    app.appendChild(group);
  }

  const wmGroup = el('div', { class: 'type-group', 'data-type': 'wm_import' });
  wmGroup.appendChild(el('h2', {}, '🧳 Whoremaster Import'));
  wmGroup.appendChild(el('p', { class: 'muted' },
    'Batch-import .girlsx / .rgirlsx character packs: skills and traits are mapped, ',
    'unknown traits get a resolution step, and image folders are copied and renamed.'));
  const wmRow = el('div', { class: 'type-actions' });
  wmRow.appendChild(el('button', {
    type: 'button', class: 'recipe-btn', 'data-action': 'wm-import',
    onclick: () => {
      app.innerHTML = '';
      runWMImporter(app, {
        ctx,
        fs,
        hasGameFolder: () => !!rootHandle,
        getGameHandle: () => gameDirHandle,
        modname,
        onDone: () => renderLanding(),
      });
    },
  }, '🧳 Open importer'));
  wmGroup.appendChild(wmRow);
  app.appendChild(wmGroup);
}

// ---------- create with recipe ----------

async function startRecipe(type, recipe) {
  app.innerHTML = '';
  const out = await runRecipe(recipe, app, { modname, ctx: ctx() });
  if (out.edit) {
    openRecipeOutputInEditor(type, out);
    return;
  }
  const entries = entriesOf(type, out.json);
  let errorCount = 0;
  for (const e of entries) {
    errorCount += validateEntry(e, type.schema, ctx()).errors.length;
  }
  if (errorCount > 0 && !confirm(`${errorCount} validation errors. Save anyway?`)) {
    renderLanding();
    return;
  }
  await saveRecipeOutput(type, out);
  renderLanding();
}

/** "Fine-tune in editor" from a recipe review: load the built entry into the
 * type's section editor, then save through the same per-type dispatch. */
function openRecipeOutputInEditor(type, out) {
  const isExtension = type.id === 'daily_stories';
  const entry = isExtension ? out.json.story : out.json;
  app.innerHTML = '';
  runEditor({
    sections: type.sections,
    entry,
    schema: type.schema,
    container: app,
    ctx: ctx(),
    defaultFilename: out.filename,
    validate: (e) => validateEntry(e, type.schema, ctx()),
    onSave: async (updated, filename) => {
      const json = isExtension ? { ...out.json, story: updated } : updated;
      await saveRecipeOutput(type, { json, filename: filename || out.filename });
      renderLanding();
    },
  });
}

/** Entries to validate for a recipe/editor payload (handles arrays + extensions). */
function entriesOf(type, json) {
  if (type.id === 'daily_stories' && json && json.story) return [json.story];
  return Array.isArray(json) ? json : [json];
}

async function saveRecipeOutput(type, out) {
  const filename = out.filename;
  if (!rootHandle) {
    downloadJSON(standaloneFile(type, out.json), filename.split('/').pop());
    alert(
      `Downloaded ${filename.split('/').pop()}.\n\n` +
      `Drop it into your game's game/data/${filename.split('/').slice(0, -1).join('/')}/ folder, ` +
      `or click "📂 Select game folder" first to save directly next time.`,
    );
    return;
  }
  try {
    if (type.id === 'daily_stories') {
      await mergeDailyStoryExtension(fs, filename, out.json);
    } else {
      for (const entry of Array.isArray(out.json) ? out.json : [out.json]) {
        await fs.mergeAndWrite(filename, entry, { key: type.key, wrapper: type.wrapper });
      }
    }
    alert(`Saved to game/data/${filename}`);
  } catch (err) {
    alert(`Save failed: ${err.message}\n\nThe JSON will be downloaded instead.`);
    downloadJSON(standaloneFile(type, out.json), filename.split('/').pop());
  }
}

/** Wraps a recipe payload as a complete standalone file for download. */
function standaloneFile(type, json) {
  if (type.id === 'daily_stories') {
    return {
      daily_story_extensions: [{
        building_id: json.building_id,
        profession_id: json.profession_id,
        merge_mode: 'upsert',
        daily_stories: [json.story],
      }],
    };
  }
  const arr = Array.isArray(json) ? json : [json];
  if (type.wrapper) return { [type.wrapper]: arr };
  return arr;
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

// ---------- edit existing ----------

async function openExisting(type) {
  if (!rootHandle) {
    alert('Select your game folder first (top-right button).');
    return;
  }
  let files = [];
  try {
    files = (await fs.listDir(type.folder)).filter((f) => f.endsWith('.json'));
  } catch {}
  if (files.length === 0) {
    alert(`No JSON files found in game/data/${type.folder}/`);
    return;
  }
  pickFromList(`${type.title} — pick a file`, files, (file) => openFile(type, file));
}

async function openFile(type, file) {
  const relPath = `${type.folder}/${file}`;
  const data = await fs.readJSON(relPath);
  if (data == null) {
    alert(`Could not read ${relPath}.`);
    return;
  }

  if (type.id === 'daily_stories') {
    // Extension files hold entries, each with stories — flatten for picking.
    const flat = [];
    for (const entry of data.daily_story_extensions || []) {
      for (const story of entry.daily_stories || []) {
        flat.push({
          label: `${entry.building_id} / ${entry.profession_id} — ${story.id}`,
          entry, story,
        });
      }
    }
    if (flat.length === 0) {
      alert('No stories in this file.');
      return;
    }
    pickFromList(`${file} — pick a story`, flat.map((x) => x.label), (label) => {
      const found = flat.find((x) => x.label === label);
      editEntry(type, relPath, found.story, {
        building_id: found.entry.building_id,
        profession_id: found.entry.profession_id,
      });
    });
    return;
  }

  const list = type.wrapper ? data[type.wrapper] || [] : data;
  if (!Array.isArray(list) || list.length === 0) {
    alert('File has no entries (or is not in the expected format).');
    return;
  }
  const labels = list.map((e) => String(e?.[type.key] ?? '(unnamed)'));
  pickFromList(`${file} — pick an entry`, labels, (label) => {
    const entry = list.find((e) => String(e?.[type.key] ?? '(unnamed)') === label);
    editEntry(type, relPath, entry, null);
  });
}

function pickFromList(title, items, onPick) {
  app.innerHTML = '';
  const wrap = el('div', { class: 'picker' });
  wrap.appendChild(el('h2', {}, title));
  const list = el('div', { class: 'picker-list' });
  for (const item of items) {
    list.appendChild(el('button', {
      type: 'button', class: 'picker-item', 'data-item': item,
      onclick: () => onPick(item),
    }, item));
  }
  wrap.appendChild(list);
  const nav = el('div', { class: 'nav' });
  nav.appendChild(el('button', {
    type: 'button', 'data-action': 'back', onclick: () => renderLanding(),
  }, 'Back'));
  wrap.appendChild(nav);
  app.appendChild(wrap);
}

function editEntry(type, relPath, entry, extensionTarget) {
  app.innerHTML = '';
  runEditor({
    sections: type.sections,
    entry,
    schema: type.schema,
    container: app,
    ctx: ctx(),
    defaultFilename: relPath,
    validate: (e) => validateEntry(e, type.schema, ctx()),
    onSave: async (updated, filename) => {
      try {
        if (type.id === 'daily_stories') {
          await mergeDailyStoryExtension(fs, filename, {
            building_id: extensionTarget.building_id,
            profession_id: extensionTarget.profession_id,
            story: updated,
          });
        } else {
          await fs.mergeAndWrite(filename, updated, { key: type.key, wrapper: type.wrapper });
        }
        alert(`Saved to game/data/${filename}`);
        renderLanding();
      } catch (err) {
        alert(`Save failed: ${err.message}`);
      }
    },
  });
}

renderLanding();
