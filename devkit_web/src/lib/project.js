import { TYPES } from './content_types.js';
import { createMemoryFS, mergeDailyStoryExtension } from './fs.js';
import { validateEntry, validateDailyStoryTarget } from './validator.js';
import { catalogsFromFiles } from './reference.js';
import { LIMITS, categoryFor, supportsOverride, safePath, cloneJSON, requiredIdentity, characterErrors, imageValid, CHARACTER_CONTENT, PACK_ROOT, STORY_MERGE_MODE, scriptSafetyErrors } from './contract.js';
import { buildZip } from './zip.js';

export const PROJECT_MODES = { characters:'Character pack', override:'JSON override (experimental)', manual:'Manual JSON files (PC only)' };
const encoder = new TextEncoder();

export function rowsFor(type, root) {
  if (Array.isArray(root)) return root;
  if (!root || typeof root !== 'object') throw new Error('Expected a JSON catalog.');
  if (type.id === 'daily_stories') {
    const groups = root.daily_story_extensions ?? [root];
    return Array.isArray(groups) ? groups : [groups];
  }
  if (type.wrapper) {
    if (!Array.isArray(root[type.wrapper])) throw new Error('Expected ' + type.wrapper + ' array.');
    return root[type.wrapper];
  }
  if (type.id === 'traits' && Array.isArray(root.traits)) return root.traits;
  if (type.id === 'workers') return Array.isArray(root.workers) ? root.workers : [root];
  throw new Error('Expected an array of entries.');
}

function withRows(type, original, rows) {
  if (original === null) return type.id === 'daily_stories' ? {daily_story_extensions:rows} : type.wrapper ? {[type.wrapper]:rows} : rows;
  if (Array.isArray(original)) return rows;
  if (type.wrapper) return {...original, [type.wrapper]:rows};
  if (type.id === 'traits' && Array.isArray(original.traits)) return {...original, traits:rows};
  if (type.id === 'workers' && Array.isArray(original.workers)) return {...original, workers:rows};
  if (type.id === 'daily_stories' && 'daily_story_extensions' in original) return {...original, daily_story_extensions:rows};
  // Preserve single-object catalogs until adding a second entry requires an array.
  return rows.length === 1 ? rows[0] : rows;
}

export function identityFor(type, entry) {
  return typeof type.key === 'function' ? type.key(entry) : requiredIdentity(entry?.[type.key]);
}

export function projectFilename(name) {
  return String(name).replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 60) || 'mymod';
}

function bytesToBase64(bytes) {
  let binary = '';
  for (let i = 0; i < bytes.length; i += 16384) binary += String.fromCharCode(...bytes.subarray(i,i+16384));
  return btoa(binary);
}

// Identifiers the game already uses. Daily and recruitment events share one ID
// namespace in the importer; daily stories are unique across all jobs.
export function baseContentIds(reference) {
  const ids = {traits:new Set(), events:new Set(), stories:new Set()};
  for (const [path, value] of Object.entries(reference.files)) {
    const category = categoryFor(path), type = TYPES.find(t => t.id === category);
    let rows;
    try { rows = rowsFor(type, value); } catch { continue; }
    for (const row of rows) {
      if (!row || typeof row !== 'object') continue;
      if (category === 'traits' && typeof row.name === 'string') ids.traits.add(row.name);
      else if ((category === 'events' || category === 'recruit_events') && typeof row.id === 'string') ids.events.add(row.id);
      else if (category === 'daily_stories') for (const story of row.daily_stories || []) { if (typeof story?.id === 'string') ids.stories.add(story.id); }
      else if (category === 'buildings') for (const profession of row.professions || []) for (const story of profession?.daily_stories || []) { if (typeof story?.id === 'string') ids.stories.add(story.id); }
    }
  }
  return ids;
}

// Daily story groups in a character pack always append; write it explicitly.
function exportedContent(path, value) {
  if (categoryFor(path) !== 'daily_stories') return value;
  const groups = rowsFor(TYPES.find(t => t.id === 'daily_stories'), value);
  return {daily_story_extensions:groups.map(group => ({...group, merge_mode:STORY_MERGE_MODE}))};
}

const README_COUNTS = [['workers','Workers'], ['traits','Traits'], ['events','Events'], ['recruit_events','Recruitment events'], ['daily_stories','Daily stories']];

export function packReadme({name, mode, gameVersion, files, assetPaths}) {
  const counts = Object.fromEntries(README_COUNTS.map(([id]) => [id, 0]));
  const workerNames = [];
  for (const [path, value] of Object.entries(files)) {
    const category = categoryFor(path), type = TYPES.find(t => t.id === category);
    let rows;
    try { rows = rowsFor(type, value); } catch { continue; }
    if (category === 'daily_stories') counts.daily_stories += rows.reduce((n, group) => n + (Array.isArray(group?.daily_stories) ? group.daily_stories.length : 0), 0);
    else if (category in counts) counts[category] += rows.length;
    if (category === 'workers') workerNames.push(...rows.map(w => w?.name || w?.template_id).filter(Boolean));
  }
  const title = String(name || 'mymod').trim() || 'mymod';
  const root = mode === 'override' ? '' : PACK_ROOT;
  const listed = [...Object.keys(files), ...assetPaths].map(path => '  ' + root + path);
  const lines = [title, '='.repeat(Math.min(Array.from(title).length, 72)),
    PROJECT_MODES[mode] + ' for Fantasy Manager ' + (gameVersion || '') + ', made with the Fantasy Manager Devkit.', '', 'CONTENTS'];
  for (const [id, label] of README_COUNTS) if (counts[id]) lines.push('- ' + label + ': ' + counts[id] + (id === 'workers' ? ' (' + workerNames.join(', ') + ')' : ''));
  lines.push('- Images: ' + assetPaths.length, '');
  if (mode === 'override') {
    lines.push('INSTALL',
      'Install this ZIP ONLY through the game: main menu > Mods > Install mods, with',
      '"Import as JSON override" enabled. Restart the game, then start a new game.',
      'NEVER drag & drop or extract these files into the game folder: each file',
      'replaces a complete original game file.', '',
      'UNINSTALL',
      'Main menu > Mods > Install mods: find this pack in the list, press Uninstall,', 'then restart the game.', '',
      'FILES', ...listed);
  } else if (mode === 'manual') {
    lines.push('INSTALL (PC only, manual)',
      '1. Back up the game folder and your saves.',
      '2. Extract this ZIP and inspect the files inside the "game" folder.',
      '3. Drag the "game" folder onto the game\'s main folder (the folder that contains',
      '   Fantasy_Manager.exe) and merge the folders. Files with the same path REPLACE',
      '   the game\'s files.',
      '4. Restart the game and start a new game for testing.',
      'This ZIP is not for Mods > Install mods.', '',
      'UNINSTALL',
      'Delete these files from the game\'s main folder, restore any original files you',
      'replaced from your backup, then restart the game:', ...listed);
  } else {
    lines.push('INSTALL (choose ONE method)',
      'Method 1 - in-game installer (PC and Android, recommended):',
      '  Main menu > Mods > Install mods, choose this ZIP file and leave',
      '  "Import as JSON override" off. Confirm, then restart the game.',
      'Method 2 - manual (PC):',
      '  Extract this ZIP. Drag the "game" folder onto the game\'s main folder (the',
      '  folder that contains Fantasy_Manager.exe) and choose to merge the folders.',
      '  The pack only adds new files; it never replaces original game files.',
      '  Restart the game.', '',
      'Do not use both methods at once: the pack would be loaded twice.', '',
      'UNINSTALL',
      'Method 1: Main menu > Mods > Install mods: find this pack in the list, press', '  Uninstall, then restart the game.',
      'Method 2: delete these files from the game\'s main folder, then restart the game',
      '(delete an image folder only if it is empty afterwards):', ...listed);
  }
  return lines.join('\r\n') + '\r\n';
}

export function createProject(reference, options = {}) {
  const mode = options.mode || 'characters';
  if (!Object.hasOwn(PROJECT_MODES, mode)) throw new Error('Unknown project mode.');
  let files = cloneJSON(options.files || {}), assets = new Map();
  let name = options.name || 'mymod';
  let revision = 0;
  const target = cloneJSON(reference.meta);

  function checkPath(path) {
    safePath(path);
    const category = categoryFor(path);
    if (!category) throw new Error('Unsupported JSON path: ' + path);
    if (mode === 'characters' && category !== 'workers' && !CHARACTER_CONTENT.includes(category)) throw new Error('Character packs contain workers, their images, traits, events, recruitment events and daily stories. Items, buildings, interactions and monthly conditions need a separate override or manual project.');
    if (mode === 'characters' && Object.hasOwn(reference.files, path)) throw new Error('This file name already exists in the game. Use a new file name so the pack only adds files: ' + path);
    if (mode === 'override' && (!supportsOverride(path) || !Object.hasOwn(reference.files, path))) throw new Error('Choose an existing, supported game file for this override: ' + path);
    return TYPES.find(t => t.id === category);
  }

  function catalogs() {
    const effective = {...reference.files};
    for (const [path, file] of Object.entries(files)) {
      // Character packs only add files: keep project files apart from base ones.
      if (mode === 'characters') effective['data/' + TYPES.find(t => t.id === categoryFor(path)).folder + '/__project_' + Object.keys(effective).length + '.json'] = file;
      else effective[path] = file;
    }
    return catalogsFromFiles(effective, reference);
  }

  function context() { return {catalogs:catalogs(), file:null, entry_index:0}; }

  function validate() {
    const errors = [], warnings = [];
    const paths = Object.keys(files).sort();
    if (!paths.length) errors.push('Add at least one JSON file to the project.');
    if (mode === 'override' && target.data_revision !== reference.meta.data_revision) errors.push('This override targets a different game reference. Create a new project using the current original files.');
    let ctx;
    try { ctx = context(); } catch (error) { return {errors:[error.message], warnings}; }
    const workers = [], foldedPaths = new Set();
    const taken = mode === 'characters' ? baseContentIds(reference) : null;
    const packIds = {traits:new Set(), events:new Set(), stories:new Set()};
    const claim = (kind, id, label) => {
      if (taken[kind].has(id)) errors.push(label + ' already exists in the game. Character packs can only add new ' + kind + '.');
      else if (packIds[kind].has(id)) errors.push(label + ' is used more than once in this pack.');
      packIds[kind].add(id);
    };
    let total = 0, contentRows = 0;
    for (const path of paths) {
      try {
        const type = checkPath(path);
        if (mode === 'override') {
          const root = files[path];
          if ((type.wrapper && (Array.isArray(root) || !Array.isArray(root?.[type.wrapper])))
              || (['events','recruit_events'].includes(type.id) && !Array.isArray(root))
              || (type.id === 'workers' && !Array.isArray(root) && Array.isArray(root?.workers))) throw new Error('This catalog wrapper is not supported by the override importer.');
        }
        if (foldedPaths.has(path.toLowerCase())) throw new Error('Duplicate path ignoring case.');
        foldedPaths.add(path.toLowerCase());
        const serialized = JSON.stringify(cloneJSON(files[path]), null, 2) + '\n';
        const size = encoder.encode(serialized).length;
        total += size;
        if (size > LIMITS.json) throw new Error('JSON file exceeds the 4 MB importer limit.');
        const rows = rowsFor(type, files[path]);
        if (mode === 'characters') for (const issue of scriptSafetyErrors(files[path])) errors.push(path + ': ' + issue);
        const seen = new Set();
        const check = (entry, schema, label) => {
          const result = validateEntry(entry, schema, ctx);
          for (const issue of result.errors) errors.push(path + ' / ' + label + ': ' + (issue.message || issue.field + ' ' + issue.error));
          for (const issue of result.warnings) warnings.push(path + ' / ' + label + ': ' + (issue.message || issue.error));
        };
        for (const row of rows) {
          if (!row || typeof row !== 'object' || Array.isArray(row)) throw new Error('Every entry must be an object.');
          if (mode === 'override' && type.id === 'workers' && row.procedural_template !== true && 'nsfw' in row && typeof row.nsfw !== 'boolean') throw new Error('Worker nsfw must be true or false when present.');
          if (type.id === 'daily_stories') {
            const group = requiredIdentity(row.building_id) + '/' + requiredIdentity(row.profession_id);
            if (seen.has(group)) throw new Error('Duplicate daily story target: ' + group);
            seen.add(group);
            if (!Array.isArray(row.daily_stories)) throw new Error('Expected a daily_stories array.');
            for (const issue of validateDailyStoryTarget(row, ctx)) errors.push(path + ' / ' + group + ': ' + issue.error);
            if (mode === 'characters') {
              if ('merge_mode' in row && row.merge_mode !== STORY_MERGE_MODE) errors.push(path + ' / ' + group + ': character packs can only add daily stories (merge_mode "append"); "' + row.merge_mode + '" would change the game’s own stories.');
              if (!row.daily_stories.length) errors.push(path + ' / ' + group + ': add at least one daily story.');
            }
            const stories = new Set();
            for (const story of row.daily_stories) {
              const id = requiredIdentity(story?.id);
              if (stories.has(id)) throw new Error('Duplicate story ID: ' + id);
              stories.add(id); check(story, type.schema, group + '/' + id);
              if (mode === 'characters') { contentRows++; claim('stories', id, path + ' / story ' + id); }
            }
          } else {
            const id = identityFor(type, row);
            if (seen.has(id)) throw new Error('Duplicate entry: ' + id);
            seen.add(id); check(row, type.schema, id);
            if (mode === 'characters' && type.id === 'workers') { workers.push(row); errors.push(...characterErrors(row)); }
            else if (mode === 'characters') {
              contentRows++;
              if (type.id === 'traits') claim('traits', id, path + ' / trait ' + id);
              else {
                if (type.id === 'events' && id.startsWith('event_recruit_')) errors.push(path + ' / ' + id + ': daily event ids must not start with event_recruit_ (the game keeps those out of the daily pool). Rename it, or move it to data/events/recruit/.');
                claim('events', id, path + ' / event ' + id);
              }
            }
          }
        }
      } catch (error) { errors.push(path + ': ' + error.message); }
    }
    if (mode === 'characters') {
      if ((!workers.length && !contentRows) || workers.length > LIMITS.workers) errors.push('A character pack needs 1–1,000 workers, or at least one trait, event or daily story.');
      const names = workers.map(w => String(w.name || '').trim().toUpperCase().toLowerCase());
      if (new Set(names).size !== names.length) errors.push('Worker names must be unique across the entire pack, ignoring case.');
      const baseNames = catalogsFromFiles(reference.files, reference).all_worker_names;
      const baseFolders = new Set(reference.image_folders || []);
      for (const worker of workers) {
        if (baseNames.has(worker.name)) warnings.push(worker.name + ': already exists in the base game; the game may skip this name.');
        if (baseFolders.has(worker.folder)) warnings.push(worker.name + ': the image folder ' + worker.folder + ' already exists in the game. A manual drag & drop install could replace its pictures that have the same names; choose a new folder name.');
        const prefix = 'images/workers/' + worker.folder + '/';
        if (![...assets.keys()].some(p => p.startsWith(prefix) && /^profile(?:[ _-]?\d+| \(\d+\))?\.(png|jpe?g|webp)$/i.test(p.slice(prefix.length)))) errors.push(worker.name + ': add profile.png, profile.jpg or profile.webp to ' + prefix);
      }
    }
    for (const [path, bytes] of assets) {
      total += bytes.length;
      if (mode === 'override') errors.push('Overrides import JSON only; remove images from this project.');
      if (!imageValid(path, bytes)) errors.push('Invalid image format: ' + path);
      if (mode === 'characters' && !workers.some(w => path.startsWith('images/workers/' + w.folder + '/'))) errors.push('Image has no matching worker: ' + path);
      if (foldedPaths.has(path.toLowerCase())) errors.push('Duplicate path: ' + path);
      foldedPaths.add(path.toLowerCase());
    }
    if (paths.length + assets.size > LIMITS.files || total > LIMITS.total) errors.push('Project exceeds the devkit limit (10,000 files / 128 MB). Split it into smaller packs.');
    return {errors:[...new Set(errors)], warnings:[...new Set(warnings)]};
  }

  const api = {
    get name() { return name; },
    set name(value) { name = String(value).slice(0,100) || 'mymod'; revision++; },
    mode, target,
    get revision() { return revision; },
    get files() { return cloneJSON(files); },
    get assetPaths() { return [...assets.keys()].sort(); },
    catalogs, context, validate,
    read(path, includeBase = true) {
      if (Object.hasOwn(files,path)) return cloneJSON(files[path]);
      if (includeBase && mode !== 'characters' && Object.hasOwn(reference.files,path)) return cloneJSON(reference.files[path]);
      return null;
    },
    async stage(typeId, payload, path, options = {}) {
      path = path.startsWith('data/') ? path : 'data/' + path;
      const type = checkPath(path);
      if (type.id !== typeId) throw new Error('The target file belongs to a different content type.');
      const original = api.read(path);
      const rows = original === null ? [] : rowsFor(type, original);
      const memory = createMemoryFS({'entries.json': typeId === 'daily_stories' ? {daily_story_extensions:rows} : rows});
      if (typeId === 'daily_stories') {
        const groups = rows.filter(g => g.building_id === payload.building_id && g.profession_id === payload.profession_id);
        if (groups.length > 1) throw new Error('Ambiguous daily story target.');
        if (!options.replaceExisting && options.originalKey == null && groups[0]?.daily_stories.some(s => s.id === payload.story.id)) throw new Error('That story already exists; open it for editing.');
        await mergeDailyStoryExtension(memory, 'entries.json', {...payload, originalKey:options.originalKey});
      } else {
        const incoming = Array.isArray(payload) ? payload : [payload];
        const seen = new Set();
        for (const entry of incoming) {
          const id = identityFor(type, entry);
          if (seen.has(id)) throw new Error('Duplicate identifiers in the new entries.');
          seen.add(id);
          if (!options.replaceExisting && options.originalKey == null && rows.some(r => identityFor(type,r) === id)) throw new Error('That identifier already exists; open the entry for editing.');
          await memory.mergeAndWrite('entries.json', entry, {key:type.key, originalKey:options.originalKey});
        }
      }
      const result = await memory.readJSON('entries.json');
      // Character packs can only add daily stories to the game's jobs.
      if (mode === 'characters' && typeId === 'daily_stories') for (const group of result.daily_story_extensions) {
        if (group.building_id === payload.building_id && group.profession_id === payload.profession_id) group.merge_mode = STORY_MERGE_MODE;
      }
      const updated = withRows(type, original, typeId === 'daily_stories' ? result.daily_story_extensions : result);
      files = {...files, [path]:cloneJSON(updated)};
      revision++;
    },
    importJSON(path, value) {
      checkPath(path); cloneJSON(value);
      if (mode === 'override') throw new Error('Start an override from the original catalog using Edit existing. This preserves the complete file.');
      if (Object.hasOwn(files,path)) throw new Error('This project already contains that file.');
      files = {...files, [path]:cloneJSON(value)}; revision++;
    },
    addImage(path, bytes, replace = false) {
      safePath(path);
      if (mode === 'override') throw new Error('JSON overrides do not import images.');
      if (!/^images\/workers\/[A-Za-z0-9][A-Za-z0-9_-]{0,79}\/.+\.(png|jpe?g|webp)$/i.test(path) || !imageValid(path, bytes)) throw new Error('Choose PNG, JPG or WebP worker images with matching file contents.');
      if (bytes.length > LIMITS.file) throw new Error('Image exceeds the 32 MB limit.');
      if (assets.has(path) && !replace) throw new Error('That image already exists in the project.');
      if ([...assets.keys()].some(p => p !== path && p.toLowerCase() === path.toLowerCase())) throw new Error('Image names must not differ only in letter case.');
      if ([...assets.values()].reduce((n,b) => n+b.length, 0) - (assets.get(path)?.length || 0) + bytes.length > LIMITS.total) throw new Error('Images exceed the 128 MB project limit.');
      assets.set(path, new Uint8Array(bytes)); revision++;
    },
    removeFile(path) { if (Object.hasOwn(files,path)) { delete files[path]; revision++; } },
    removeImage(path) { if (assets.delete(path)) revision++; },
    serialize() {
      return {format:'fm-devkit-project', version:1, name, mode, target:cloneJSON(target), files:cloneJSON(files), images:[...assets].map(([path, bytes]) => ({path, data:bytesToBase64(bytes)}))};
    },
    exportPack() {
      const result = validate();
      if (result.errors.length) throw new Error(result.errors.join('\n'));
      const root = mode === 'override' ? '' : PACK_ROOT;
      const output = Object.fromEntries(Object.keys(files).sort().map(path => [path, mode === 'characters' ? exportedContent(path, files[path]) : files[path]]));
      const entries = Object.keys(output).map(path => ({path:root + path, data:JSON.stringify(output[path],null,2)+'\n'}));
      for (const path of [...assets.keys()].sort()) entries.push({path:root + path, data:assets.get(path)});
      entries.push({path:'README.txt', data:packReadme({name, mode, gameVersion:target.game_version, files:output, assetPaths:[...assets.keys()].sort()})});
      return {bytes:buildZip(entries), filename:projectFilename(name) + (mode === 'override' ? '_override' : mode === 'manual' ? '_manual_pc' : '_characters') + '.zip', ...result};
    },
  };
  for (const path of Object.keys(files)) checkPath(path);
  return api;
}

export function restoreProject(reference, data) {
  if (data?.format !== 'fm-devkit-project' || data.version !== 1 || typeof data.name !== 'string' || !data.files || typeof data.files !== 'object' || Array.isArray(data.files) || !Array.isArray(data.images)) throw new Error('Choose a devkit project file (.fmproject.json), not an installable ZIP.');
  if (!data.target || data.target.data_revision !== reference.meta.data_revision) throw new Error('This project was created for different game data. Open it with the matching devkit/reference; port overrides into a fresh project for this version.');
  if (Object.keys(data.files).length + data.images.length > LIMITS.files) throw new Error('Too many project files.');
  // Restoring a draft preserves its full file contents; export still validates it.
  // Use a private restore hook via per-file draft creation, never import into game.
  for (const [path, value] of Object.entries(data.files)) {
    const type = categoryFor(safePath(path));
    if (!type || (data.mode === 'override' && (!supportsOverride(path) || !Object.hasOwn(reference.files,path)))) throw new Error('Unsupported project path: ' + path);
    if (encoder.encode(JSON.stringify(cloneJSON(value))).length > LIMITS.json) throw new Error('Oversized project JSON: ' + path);
  }
  // A separate builder accepts already-materialised catalogs from our versioned
  // draft format while keeping new override authoring tied to base files.
  const project = createProject(reference, {mode:data.mode, name:data.name, files:data.files});
  let bytesTotal = 0;
  for (const item of data.images) {
    if (typeof item.data !== 'string' || item.data.length > Math.ceil(LIMITS.file / 3) * 4) throw new Error('Oversized project image.');
    const binary = atob(item.data);
    bytesTotal += binary.length;
    if (bytesTotal > LIMITS.total) throw new Error('Project is too large.');
    project.addImage(item.path, Uint8Array.from(binary, c => c.charCodeAt(0)));
  }
  return project;
}
