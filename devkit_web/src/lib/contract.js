// Common authoring/pack boundaries. The Python importer remains authoritative.
export const LIMITS = { files: 10000, file: 32 * 1024 * 1024, json: 4 * 1024 * 1024, total: 128 * 1024 * 1024, workers: 1000 };
export const IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp'];
export const WORKER_FIELDS = ['name', 'folder', 'cost', 'skills', 'names_list', 'traits', 'description', 'gender', 'comfort_desired', 'nsfw', 'unique', 'encounter_only', 'monster', 'procedural'];

export function safePath(path) {
  if (typeof path !== 'string' || !path || path.includes('\\')) throw new Error('Use a relative path with forward slashes.');
  const parts = path.split('/');
  if (parts.some(p => !p || p === '.' || p === '..' || /[. ]$|[\x00-\x1f:<>"|?*]/.test(p) || /^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.|$)/i.test(p))) {
    throw new Error('Unsafe file path: ' + path);
  }
  return path;
}

export function assertJSON(value, depth = 0) {
  if (depth > 100) throw new Error('JSON is nested too deeply.');
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return;
  if (typeof value === 'number' && Number.isFinite(value)) return;
  if (typeof value !== 'object' || value === null) throw new Error('JSON contains an unsupported or non-finite value.');
  for (const v of Object.values(value)) assertJSON(v, depth + 1);
}

export function cloneJSON(value) {
  assertJSON(value);
  return JSON.parse(JSON.stringify(value));
}

export function parseJSON(text) {
  const value = JSON.parse(text.replace(/^\uFEFF/, ''));
  assertJSON(value);
  // JSON.parse accepts duplicate keys. Detect them before an editor could erase
  // the distinction and silently save a different document.
  const tokens = text.match(/"(?:\\.|[^"\\])*"|[{}\[\]:,]|[^\s{}\[\]:,]+/g) || [];
  const stack = [];
  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    if (token === '{' || token === '[') stack.push(token === '{' ? new Set() : null);
    else if (token === '}' || token === ']') stack.pop();
    else if (token.startsWith('"') && tokens[i + 1] === ':' && stack.at(-1) instanceof Set) {
      const key = JSON.parse(token);
      if (stack.at(-1).has(key)) throw new Error('Duplicate JSON key: ' + key);
      stack.at(-1).add(key);
    }
  }
  return value;
}

export function workerIdentity(entry) {
  return entry?.procedural_template === true ? 'template:' + requiredIdentity(entry.template_id) : 'name:' + JSON.stringify([requiredIdentity(entry?.name), entry.nsfw === true]);
}

export function requiredIdentity(value) {
  if (typeof value !== 'string' || !value.trim()) throw new Error('An entry is missing its identifier.');
  return value;
}

export function categoryFor(path) {
  if (path === 'data/monthly_conditions/cards.json') return 'monthly_conditions';
  if (/^data\/workers(?:\/[^/]+)?\.json$/.test(path)) return 'workers';
  if (/^data\/buildings\/daily_story_extensions\/[^/]+\.json$/.test(path)) return 'daily_stories';
  if (/^data\/events\/recruit\/[^/]+\.json$/.test(path)) return 'recruit_events';
  const match = /^data\/(items|traits|buildings|events|interactions)\/[^/]+\.json$/.exec(path);
  return match?.[1] || null;
}

export function supportsOverride(path) { return !!categoryFor(path) && categoryFor(path) !== 'interactions'; }

export function imageValid(path, bytes) {
  const extension = path.split('.').at(-1).toLowerCase();
  return (extension === 'png' && [137,80,78,71,13,10,26,10].every((b,i) => bytes[i] === b))
    || (['jpg','jpeg'].includes(extension) && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255)
    || (extension === 'webp' && String.fromCharCode(...bytes.slice(0,4)) === 'RIFF' && String.fromCharCode(...bytes.slice(8,12)) === 'WEBP');
}

export function characterErrors(worker) {
  const errors = [];
  const label = worker?.name || 'Worker';
  const fail = text => errors.push(label + ': ' + text);
  if (!worker || Array.isArray(worker) || typeof worker !== 'object') return ['Every worker must be an object.'];
  if (typeof worker.name !== 'string' || !worker.name.trim() || Array.from(worker.name).length > 100 || /[{}\[\]\r\n\x00]/.test(worker.name)) fail('use a plain-text name of 1–100 characters.');
  if (typeof worker.folder !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(worker.folder)) fail('image folder must use letters, numbers, underscores or hyphens (1–80 characters).');
  if (worker.procedural || worker.monster || worker.procedural_template || worker.event_recruit_only) fail('this pack mode supports regular characters only. Use an appropriate existing-file override for templates.');
  if (!['female','male'].includes(worker.gender)) fail('select a gender.');
  for (const key of ['nsfw','unique','encounter_only','monster','procedural']) if (key in worker && typeof worker[key] !== 'boolean') fail(key + ' must be true or false.');
  const number = (v, max) => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= max;
  if (!number(worker.cost ?? 0, 10000000)) fail('invalid cost.');
  if (!number(worker.comfort_desired ?? 1, 100)) fail('invalid desired comfort.');
  if (!worker.skills || Array.isArray(worker.skills) || typeof worker.skills !== 'object' || Object.values(worker.skills).some(v => !number(v, 100))) fail('skills must be numbers from 0 to 100.');
  if (!Array.isArray(worker.traits) || worker.traits.some(v => typeof v !== 'string' || Array.from(v).length > 100)) fail('traits must be a list of names.');
  for (const key of ['description','names_list']) if (worker[key] != null && (typeof worker[key] !== 'string' || Array.from(worker[key]).length > 10000)) fail('invalid ' + key + '.');
  const extra = Object.keys(worker).filter(k => !WORKER_FIELDS.includes(k));
  if (extra.length) fail('these fields are not imported in character packs: ' + extra.join(', ') + '.');
  return errors;
}
