import { buildCatalogs } from './catalog_loader.js';
import { categoryFor, cloneJSON, parseJSON, safePath } from './contract.js';

export function catalogsFromFiles(files, extras = {}) {
  const sources = {traits:[], items:[], buildings:[], workers:[], interactions:[], events:[], daily_stories:[]};
  for (const path of Object.keys(files).sort()) {
    const category = categoryFor(path);
    const key = category === 'recruit_events' ? 'events' : category;
    if (key && sources[key]) sources[key].push(files[path]);
  }
  const catalogs = buildCatalogs(sources);
  catalogs.names_lists = new Set(extras.names_lists || []);
  catalogs.image_folders = new Set(extras.image_folders || []);
  return catalogs;
}

export async function sha256(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}

export async function referenceMetadata(files, gameVersion, source = 'bundled') {
  const hashes = {};
  for (const path of Object.keys(files).sort()) hashes[path] = await sha256(JSON.stringify(files[path]));
  return { format: 1, game_version: gameVersion, data_revision: await sha256(JSON.stringify(hashes)), files: hashes, source };
}

export async function loadBundledReference() {
  const inline = globalThis.window?.__FM_BUNDLED_CATALOGS;
  const get = async name => {
    if (inline) {
      if (!(name in inline)) throw new Error('Missing bundled reference: ' + name);
      return cloneJSON(inline[name]);
    }
    const response = await fetch('./catalogs/' + name + '.json');
    if (!response.ok) throw new Error('Could not load game reference: ' + name);
    return parseJSON(await response.text());
  };
  const [files, meta, names_lists, image_folders] = await Promise.all(['base_files','_meta','names_lists','image_folders'].map(get));
  return {files, meta, names_lists, image_folders};
}

// Optional PC reference import only requests read access. No handles are passed
// to the project writer, and failures never turn into an empty reference.
export async function readGameReference(root) {
  let game = root;
  try { game = await root.getDirectoryHandle('game'); }
  catch (error) { if (error.name !== 'NotFoundError') throw error; }
  const data = await game.getDirectoryHandle('data');
  const files = {};
  async function visit(dir, prefix) {
    for await (const [name, entry] of dir.entries()) {
      const path = safePath(prefix + '/' + name);
      if (entry.kind === 'directory') await visit(entry, path);
      else if (categoryFor(path)) files[path] = parseJSON(await (await entry.getFile()).text());
    }
  }
  await visit(data, 'data');
  if (!Object.keys(files).length) throw new Error('No game catalogs found in that folder.');
  const names = parseJSON(await (await data.getFileHandle('names.json')).getFile().then(f => f.text()));
  let gameVersion = 'selected PC folder';
  try {
    const scripts = await game.getDirectoryHandle('scripts');
    const core = await scripts.getDirectoryHandle('core');
    const options = await (await core.getFileHandle('options.rpy')).getFile();
    gameVersion = (await options.text()).match(/define config\.version\s*=\s*"([^"]+)"/)?.[1] || gameVersion;
  } catch (error) { if (error.name !== 'NotFoundError') throw error; }
  return {files, names_lists:Object.keys(names), image_folders:[], meta:await referenceMetadata(files, gameVersion, 'selected PC folder')};
}
