/**
 * Common fs interface:
 *   - openRoot()                  → must be called once (browser only)
 *   - readJSON(relPath)           → parsed JSON or null
 *   - writeJSON(relPath, data)
 *   - listDir(relDir)             → [filename, ...]
 *   - mergeAndWrite(relPath, entry, { key, wrapper }) → append-or-replace by key.
 *     Without wrapper the file root is an array. With wrapper (e.g. "items",
 *     "building_types") the root is an object whose <wrapper> key holds the
 *     array; sibling root keys are preserved.
 */

import { cloneJSON, parseJSON, safePath, requiredIdentity } from './contract.js';

function mergeRows(rows, entry, key, originalKey) {
  if (!Array.isArray(rows)) throw new Error('Expected an array of entries; the file was not changed.');
  const identify = typeof key === 'function' ? key : e => requiredIdentity(e?.[key]);
  const ids = rows.map(identify);
  if (new Set(ids).size !== ids.length) throw new Error('Duplicate identifiers; the file was not changed.');
  const next = identify(entry);
  const old = originalKey ?? next;
  if (originalKey != null && !ids.includes(old)) throw new Error('The original entry no longer exists.');
  if (old !== next && ids.includes(next)) throw new Error('Another entry already uses that identifier.');
  const result = cloneJSON(rows);
  const index = ids.indexOf(old);
  if (index >= 0) result[index] = cloneJSON(entry);
  else result.push(cloneJSON(entry));
  return result;
}

async function mergeIntoFile(fsLike, p, entry, { key, wrapper, originalKey }) {
  if (wrapper) {
    const existing = await fsLike.readJSON(p);
    const root = existing === null ? { [wrapper]: [] } : existing;
    if (Array.isArray(root) || typeof root !== 'object' || root === null) {
      throw new Error(`mergeAndWrite expects object root with "${wrapper}" at ${p}`);
    }
    const arr = mergeRows(root[wrapper], entry, key, originalKey);
    await fsLike.writeJSON(p, { ...root, [wrapper]: arr });
    return;
  }
  const existing = await fsLike.readJSON(p);
  const arr = mergeRows(existing === null ? [] : existing, entry, key, originalKey);
  await fsLike.writeJSON(p, arr);
}

/**
 * Daily story extensions: { daily_story_extensions: [ { building_id,
 * profession_id, merge_mode, daily_stories: [...] } ] }. Stories are upserted
 * by id inside the entry matching building_id+profession_id (the same merge
 * the game performs at load time).
 */
export async function mergeDailyStoryExtension(fsLike, p, { building_id, profession_id, story, originalKey }) {
  requiredIdentity(building_id);
  requiredIdentity(profession_id);
  const existing = await fsLike.readJSON(p);
  const root = existing === null ? { daily_story_extensions: [] } : cloneJSON(existing);
  if (!Array.isArray(root?.daily_story_extensions)) throw new Error('Expected daily_story_extensions array; the file was not changed.');
  const entries = root.daily_story_extensions;
  let entry = entries.find(
    (e) => e && e.building_id === building_id && e.profession_id === profession_id,
  );
  if (!entry) {
    entry = { building_id, profession_id, merge_mode: 'upsert', daily_stories: [] };
    entries.push(entry);
  }
  entry.daily_stories = mergeRows(entry.daily_stories, story, 'id', originalKey);
  await fsLike.writeJSON(p, { ...root, daily_story_extensions: entries });
}

export function createMemoryFS(initial = {}) {
  const store = new Map(Object.entries(cloneJSON(initial)));
  return {
    async openRoot() {},
    async readJSON(p) {
      return store.has(p) ? cloneJSON(store.get(p)) : null;
    },
    async writeJSON(p, data) {
      safePath(p);
      store.set(p, cloneJSON(data));
    },
    async listDir(prefix) {
      const out = [];
      for (const key of store.keys()) {
        if (!key.startsWith(prefix + '/')) continue;
        const rest = key.slice(prefix.length + 1);
        if (!rest.includes('/')) out.push(rest);
      }
      return out;
    },
    async mergeAndWrite(p, entry, opts) {
      await mergeIntoFile(this, p, entry, opts);
    },
  };
}

export function createFSAFS(rootHandle) {
  async function walk(parts, create = false) {
    let h = rootHandle;
    for (let i = 0; i < parts.length - 1; i++) {
      h = await h.getDirectoryHandle(parts[i], { create });
    }
    return h;
  }
  return {
    async openRoot() {
      // already supplied via rootHandle
    },
    async readJSON(p) {
      const parts = safePath(p).split('/');
      try {
        const dir = await walk(parts);
        const fh = await dir.getFileHandle(parts.at(-1));
        const file = await fh.getFile();
        const txt = await file.text();
        const data = parseJSON(txt);
        if (data === null) throw new Error('Expected a JSON catalog, received null.');
        return data;
      } catch (error) {
        if (error.name === 'NotFoundError') return null;
        throw new Error(`Cannot read ${p}: ${error.message}. Nothing was written.`);
      }
    },
    async writeJSON(p, data) {
      const parts = safePath(p).split('/');
      const text = JSON.stringify(cloneJSON(data), null, 2) + '\n';
      const dir = await walk(parts, true);
      const fh = await dir.getFileHandle(parts.at(-1), { create: true });
      const w = await fh.createWritable();
      try { await w.write(text); await w.close(); }
      catch (error) { if (w.abort) await w.abort().catch(() => {}); throw error; }
    },
    async listDir(prefix) {
      const parts = prefix.split('/').filter(Boolean);
      let dir = rootHandle;
      for (const p of parts) dir = await dir.getDirectoryHandle(p);
      const out = [];
      for await (const [name, entry] of dir.entries()) {
        if (entry.kind === 'file') out.push(name);
      }
      return out;
    },
    async mergeAndWrite(p, entry, opts) {
      await mergeIntoFile(this, p, entry, opts);
    },
  };
}
