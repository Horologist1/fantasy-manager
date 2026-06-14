// Whoremaster batch importer UI: Source → Settings → Review → Import.
// Pure conversion logic lives in wm_xml_to_fm.js / wm_image_rename.js; this
// module only orchestrates the flow and the DOM.
import { parseWMGirlXML, convertWMToFMWorker, sanitizeFolderName } from './wm_xml_to_fm.js';
import { planRenames } from './wm_image_rename.js';
import { WM_IMAGE_EXTENSIONS } from './wm_mappings.js';
import { renderSummary } from '../lib/ui.js';
import { validateEntry } from '../lib/validator.js';
import { worker_schema } from '../schemas/worker.schema.js';

const RESOLUTIONS_KEY = 'fm_devkit_wm_trait_resolutions';

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

function loadResolutions() {
  try { return JSON.parse(localStorage.getItem(RESOLUTIONS_KEY)) || {}; } catch { return {}; }
}

function saveResolutions(map) {
  localStorage.setItem(RESOLUTIONS_KEY, JSON.stringify(map));
}

/** Similarity score for suggestion ranking: shared-prefix + substring bonus. */
function similarity(a, b) {
  const x = a.toLowerCase();
  const y = b.toLowerCase();
  if (x === y) return 100;
  if (y.includes(x) || x.includes(y)) return 80;
  let prefix = 0;
  while (prefix < Math.min(x.length, y.length) && x[prefix] === y[prefix]) prefix += 1;
  const common = new Set([...x].filter((ch) => y.includes(ch))).size;
  return prefix * 8 + common;
}

export function suggestTraits(wmTrait, allTraits, limit = 8) {
  return Array.from(allTraits)
    .map((t) => [t, similarity(wmTrait, t)])
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([t]) => t);
}

/**
 * runWMImporter(container, deps)
 * deps: { ctx() → validation ctx with catalogs, fs, hasGameFolder() → bool,
 *         getGameHandle() → FSA dir handle of <game>/game or null,
 *         modname, onDone() }
 */
export function runWMImporter(container, deps) {
  const state = {
    sourceHandle: null,
    characters: [],       // { filename, wmData, folderName, imageDirName|null }
    imageDirs: new Map(), // dirName → handle
    settings: {
      outputFile: `workers/workers_${deps.modname}_wm.json`,
      skillScaleMax: 100,
      copyImages: true,
      renameImages: true,
      makeTraitStubs: true,
    },
    resolutions: loadResolutions(), // wmTrait → fm trait name | '__skip__'
    stubTraits: new Set(),
    rows: [],             // computed per-character review rows
  };

  function paintSource() {
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, 'Import from Whoremaster — 1 · Source'));
    wrap.appendChild(el('p', { class: 'muted' },
      'Pick the Whoremaster "Characters" folder. It should contain .girlsx / .rgirlsx ',
      'files and (optionally) one image folder per character.'));
    wrap.appendChild(el('button', {
      type: 'button', 'data-action': 'pick-source',
      onclick: async () => {
        if (!('showDirectoryPicker' in window)) {
          alert('Folder picking needs Chrome, Edge, or Brave.');
          return;
        }
        state.sourceHandle = await window.showDirectoryPicker({ mode: 'read' });
        await scanSource();
        paintSettings();
      },
    }, '📂 Pick Whoremaster folder'));
    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'back', onclick: () => deps.onDone(),
    }, 'Back'));
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  async function scanSource() {
    state.characters = [];
    state.imageDirs = new Map();
    async function walk(dirHandle) {
      for await (const [name, entry] of dirHandle.entries()) {
        if (entry.kind === 'directory') {
          state.imageDirs.set(name, entry);
          await walk(entry);
        } else if (/\.r?girlsx$/i.test(name)) {
          try {
            const text = await (await entry.getFile()).text();
            const wmData = parseWMGirlXML(text, name);
            if (wmData) {
              state.characters.push({
                filename: name,
                wmData,
                folderName: sanitizeFolderName(wmData.name),
                imageDirName: null,
              });
            }
          } catch { /* unreadable file — skipped, reported via counts */ }
        }
      }
    }
    await walk(state.sourceHandle);
    // match image folders by WM convention: folder named after the XML Name
    for (const c of state.characters) {
      if (state.imageDirs.has(c.wmData.xml_name)) c.imageDirName = c.wmData.xml_name;
      else if (state.imageDirs.has(c.wmData.name)) c.imageDirName = c.wmData.name;
    }
  }

  function paintSettings() {
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, 'Import from Whoremaster — 2 · Settings'));
    const withImages = state.characters.filter((c) => c.imageDirName).length;
    wrap.appendChild(el('p', {},
      `Found ${state.characters.length} characters ` +
      `(${withImages} with an image folder).`));

    const fileRow = el('div', { class: 'field' });
    fileRow.appendChild(el('label', {}, 'Output file'));
    const fileInput = el('input', { type: 'text' });
    fileInput.value = state.settings.outputFile;
    fileInput.addEventListener('input', () => { state.settings.outputFile = fileInput.value; });
    fileRow.appendChild(fileInput);
    wrap.appendChild(fileRow);

    const scaleRow = el('div', { class: 'field' });
    scaleRow.appendChild(el('label', {}, 'WM skill scale'));
    const scaleSel = el('select');
    for (const v of ['100', '70']) scaleSel.appendChild(el('option', { value: v }, v));
    scaleSel.value = String(state.settings.skillScaleMax);
    scaleSel.addEventListener('change', () => {
      state.settings.skillScaleMax = parseInt(scaleSel.value, 10);
    });
    scaleRow.appendChild(scaleSel);
    wrap.appendChild(scaleRow);

    for (const [key, label] of [
      ['copyImages', 'Copy image folders into game/images/workers/'],
      ['renameImages', 'Rename images to FM conventions (Portrait→profile…)'],
      ['makeTraitStubs', 'Create stub traits for unknown WM traits you mark as "new"'],
    ]) {
      const row = el('div', { class: 'field' });
      row.appendChild(el('label', {}, label));
      const cb = el('input', { type: 'checkbox' });
      cb.checked = state.settings[key];
      cb.addEventListener('change', () => { state.settings[key] = cb.checked; });
      row.appendChild(cb);
      wrap.appendChild(row);
    }

    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'back', onclick: () => paintSource(),
    }, 'Back'));
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'next',
      onclick: () => { computeRows(); paintReview(); },
    }, 'Next'));
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  function effectiveMappings() {
    const extra = {};
    for (const [wm, fm] of Object.entries(state.resolutions)) {
      if (fm && fm !== '__skip__') extra[wm] = fm;
    }
    return extra;
  }

  function computeRows() {
    const ctx = deps.ctx();
    const extra = effectiveMappings();
    state.rows = state.characters.map((c) => {
      const { worker, unknownTraits, unknownSkills } = convertWMToFMWorker(c.wmData, {
        folderName: c.folderName,
        skillScaleMax: state.settings.skillScaleMax,
        extraTraitMappings: extra,
      });
      const pendingTraits = unknownTraits.filter((t) => !(t in state.resolutions));
      return {
        character: c,
        worker,
        unknownTraits,
        pendingTraits,
        unknownSkills,
        include: true,
        duplicateName: ctx.catalogs.all_worker_names?.has(worker.name) || false,
        duplicateFolder: ctx.catalogs.all_worker_folders?.has(worker.folder) || false,
      };
    });
  }

  function paintReview() {
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, 'Import from Whoremaster — 3 · Review'));
    const pending = state.rows.reduce((n, r) => n + r.pendingTraits.length, 0);
    if (pending > 0) {
      wrap.appendChild(el('p', { class: 'muted' },
        `${pending} unknown WM trait(s) need a decision — click each ⚠ to resolve.`));
    }

    for (const row of state.rows) {
      const card = el('div', { class: 'object-item', 'data-character': row.worker.name });
      const head = el('div', { class: 'object-item-head' });
      const cb = el('input', { type: 'checkbox', 'data-action': 'include' });
      cb.checked = row.include;
      cb.addEventListener('change', () => { row.include = cb.checked; });
      head.appendChild(cb);
      head.appendChild(el('strong', {}, ` ${row.worker.name} `));
      head.appendChild(el('span', { class: 'muted' },
        row.worker.procedural ? 'procedural template' : 'unique worker'));
      card.appendChild(head);

      const info = el('div', { class: 'muted' },
        `folder: ${row.worker.folder}` +
        (row.character.imageDirName ? ` (images: ${row.character.imageDirName})` : ' (no image folder found)'));
      card.appendChild(info);
      if (row.duplicateName) {
        card.appendChild(el('div', { class: 'val-warning' },
          `⚠ a worker named "${row.worker.name}" already exists — importing will merge/replace it in your mod file`));
      }
      if (row.duplicateFolder) {
        card.appendChild(el('div', { class: 'val-warning' },
          `⚠ image folder "${row.worker.folder}" already exists in the game`));
      }

      const traitsRow = el('div', { class: 'chips' });
      for (const t of row.worker.traits) traitsRow.appendChild(el('span', { class: 'chip' }, t));
      for (const t of row.unknownTraits) {
        const resolved = state.resolutions[t];
        if (resolved === '__skip__') {
          traitsRow.appendChild(el('span', { class: 'chip muted' }, `${t} (skipped)`));
        } else if (!resolved) {
          traitsRow.appendChild(el('button', {
            type: 'button', class: 'chip chip-warn', 'data-unknown-trait': t,
            onclick: () => paintResolve(t),
          }, `⚠ ${t}`));
        }
      }
      card.appendChild(traitsRow);
      if (row.unknownSkills.length) {
        card.appendChild(el('div', { class: 'muted' },
          `unmapped WM skills (ignored): ${row.unknownSkills.join(', ')}`));
      }

      const details = el('details', { class: 'raw-json' });
      details.appendChild(el('summary', {}, 'Preview worker'));
      details.appendChild(renderSummary(row.worker));
      card.appendChild(details);
      wrap.appendChild(card);
    }

    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'back', onclick: () => paintSettings(),
    }, 'Back'));
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'import',
      onclick: () => doImport(),
    }, `Import ${state.rows.filter((r) => r.include).length} characters`));
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  function paintResolve(wmTrait) {
    const ctx = deps.ctx();
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, `Resolve unknown trait: "${wmTrait}"`));
    wrap.appendChild(el('p', { class: 'muted' },
      'This Whoremaster trait has no Fantasy Manager equivalent yet. Map it to an ',
      'existing trait, create it as a new trait, or skip it. Your choice is ',
      'remembered for future imports.'));

    wrap.appendChild(el('h3', {}, 'Suggestions'));
    const sugg = el('div', { class: 'suggestion-row' });
    for (const t of suggestTraits(wmTrait, ctx.catalogs.all_traits || new Set())) {
      sugg.appendChild(el('button', {
        type: 'button', class: 'suggestion-chip', 'data-suggestion': t,
        onclick: () => resolveAs(wmTrait, t),
      }, t));
    }
    wrap.appendChild(sugg);

    wrap.appendChild(el('h3', {}, 'Or search all traits'));
    const search = el('input', { type: 'text', placeholder: 'Filter…' });
    const list = el('div', { class: 'suggestion-row' });
    const all = Array.from(ctx.catalogs.all_traits || []).sort();
    function paintList() {
      list.innerHTML = '';
      const q = search.value.toLowerCase();
      for (const t of all.filter((x) => x.toLowerCase().includes(q))) {
        list.appendChild(el('button', {
          type: 'button', class: 'suggestion-chip', 'data-trait': t,
          onclick: () => resolveAs(wmTrait, t),
        }, t));
      }
    }
    search.addEventListener('input', paintList);
    paintList();
    wrap.appendChild(search);
    wrap.appendChild(list);

    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'new-trait',
      onclick: () => {
        state.stubTraits.add(wmTrait);
        resolveAs(wmTrait, wmTrait);
      },
    }, `＋ Create "${wmTrait}" as a new trait`));
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'skip-trait',
      onclick: () => resolveAs(wmTrait, '__skip__'),
    }, 'Skip this trait'));
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'back',
      onclick: () => paintReview(),
    }, 'Back'));
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  function resolveAs(wmTrait, fmTrait) {
    state.resolutions[wmTrait] = fmTrait;
    saveResolutions(state.resolutions);
    computeRows();
    paintReview();
  }

  function stubTraitEntry(name) {
    return {
      name,
      conflicts: [],
      removes_traits: [],
      modifiers: {
        skill_modifiers: {}, attribute_caps: {}, attribute_minimums: {},
        daily_effects: {}, earnings_multiplier: 0, libido_max: 0, libido_regeneration: 0,
      },
      description: 'Imported from Whoremaster — fill in the modifiers.',
      nsfw: false,
    };
  }

  async function copyImagesFor(row, log) {
    const gameHandle = deps.getGameHandle();
    if (!gameHandle || !row.character.imageDirName) return;
    const srcDir = state.imageDirs.get(row.character.imageDirName);
    if (!srcDir) return;

    const imagesDir = await gameHandle.getDirectoryHandle('images', { create: true });
    const workersDir = await imagesDir.getDirectoryHandle('workers', { create: true });
    const destDir = await workersDir.getDirectoryHandle(row.worker.folder, { create: true });

    const names = [];
    for await (const [name, entry] of srcDir.entries()) {
      if (entry.kind === 'file') names.push(name);
    }
    const renamed = state.settings.renameImages
      ? new Map(planRenames(names).map((p) => [p.from, p.to]))
      : new Map();

    let copied = 0;
    for (const name of names) {
      const ext = name.slice(name.lastIndexOf('.')).toLowerCase();
      if (!WM_IMAGE_EXTENSIONS.includes(ext)) continue;
      const target = renamed.get(name) || name.toLowerCase();
      try {
        const srcFile = await (await srcDir.getFileHandle(name)).getFile();
        const fh = await destDir.getFileHandle(target, { create: true });
        const w = await fh.createWritable();
        await w.write(await srcFile.arrayBuffer());
        await w.close();
        copied += 1;
      } catch (e) {
        log(`  ! failed to copy ${name}: ${e.message}`);
      }
    }
    log(`  images: ${copied} copied into images/workers/${row.worker.folder}/`);
  }

  async function doImport() {
    const rows = state.rows.filter((r) => r.include);
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, 'Import from Whoremaster — 4 · Import'));
    const logBox = el('pre', { class: 'json-preview', 'data-role': 'import-log' });
    wrap.appendChild(logBox);
    container.appendChild(wrap);
    const log = (line) => { logBox.textContent += `${line}\n`; };

    if (!deps.hasGameFolder()) {
      // No game folder: produce a single downloadable workers file.
      const workers = rows.map((r) => r.worker);
      const blob = new Blob([JSON.stringify(workers, null, 2) + '\n'], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = state.settings.outputFile.split('/').pop();
      a.click();
      log(`Downloaded ${a.download} with ${workers.length} workers.`);
      log('Select your game folder next time to also copy image folders automatically.');
    } else {
      for (const row of rows) {
        log(`${row.worker.name} → ${state.settings.outputFile}`);
        await deps.fs.mergeAndWrite(state.settings.outputFile, row.worker, { key: 'name' });
        if (state.settings.copyImages) await copyImagesFor(row, log);
      }
      if (state.settings.makeTraitStubs && state.stubTraits.size > 0) {
        const stubFile = `traits/traits_${deps.modname}_wm.json`;
        for (const name of state.stubTraits) {
          await deps.fs.mergeAndWrite(stubFile, stubTraitEntry(name), { key: 'name' });
          log(`stub trait "${name}" → ${stubFile}`);
        }
      }
      const errors = rows.reduce(
        (n, r) => n + validateEntry(r.worker, worker_schema, deps.ctx()).errors.length, 0,
      );
      log(`Done: ${rows.length} workers imported${errors ? ` (${errors} validation errors — open them in the editor)` : ''}.`);
    }
    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'done', onclick: () => deps.onDone(),
    }, 'Finish'));
    wrap.appendChild(nav);
  }

  paintSource();
}
