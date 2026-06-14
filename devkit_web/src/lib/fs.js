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

async function mergeIntoFile(fsLike, p, entry, { key, wrapper }) {
  if (wrapper) {
    const root = (await fsLike.readJSON(p)) || { [wrapper]: [] };
    if (Array.isArray(root) || typeof root !== 'object' || root === null) {
      throw new Error(`mergeAndWrite expects object root with "${wrapper}" at ${p}`);
    }
    const arr = Array.isArray(root[wrapper]) ? [...root[wrapper]] : [];
    const idx = arr.findIndex((e) => e && e[key] === entry[key]);
    if (idx >= 0) arr[idx] = entry;
    else arr.push(entry);
    await fsLike.writeJSON(p, { ...root, [wrapper]: arr });
    return;
  }
  let arr = (await fsLike.readJSON(p)) || [];
  if (!Array.isArray(arr)) throw new Error(`mergeAndWrite expects array root at ${p}`);
  const idx = arr.findIndex((e) => e && e[key] === entry[key]);
  if (idx >= 0) arr[idx] = entry;
  else arr = [...arr, entry];
  await fsLike.writeJSON(p, arr);
}

/**
 * Daily story extensions: { daily_story_extensions: [ { building_id,
 * profession_id, merge_mode, daily_stories: [...] } ] }. Stories are upserted
 * by id inside the entry matching building_id+profession_id (the same merge
 * the game performs at load time).
 */
export async function mergeDailyStoryExtension(fsLike, p, { building_id, profession_id, story }) {
  const root = (await fsLike.readJSON(p)) || { daily_story_extensions: [] };
  const entries = Array.isArray(root.daily_story_extensions)
    ? [...root.daily_story_extensions]
    : [];
  let entry = entries.find(
    (e) => e && e.building_id === building_id && e.profession_id === profession_id,
  );
  if (!entry) {
    entry = { building_id, profession_id, merge_mode: 'upsert', daily_stories: [] };
    entries.push(entry);
  }
  const stories = Array.isArray(entry.daily_stories) ? [...entry.daily_stories] : [];
  const idx = stories.findIndex((s) => s && s.id === story.id);
  if (idx >= 0) stories[idx] = story;
  else stories.push(story);
  entry.daily_stories = stories;
  await fsLike.writeJSON(p, { ...root, daily_story_extensions: entries });
}

export function createMemoryFS(initial = {}) {
  const store = new Map(Object.entries(initial));
  return {
    async openRoot() {},
    async readJSON(p) {
      return store.has(p) ? JSON.parse(JSON.stringify(store.get(p))) : null;
    },
    async writeJSON(p, data) {
      store.set(p, JSON.parse(JSON.stringify(data)));
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
  async function walk(parts) {
    let h = rootHandle;
    for (let i = 0; i < parts.length - 1; i++) {
      h = await h.getDirectoryHandle(parts[i], { create: true });
    }
    return h;
  }
  return {
    async openRoot() {
      // already supplied via rootHandle
    },
    async readJSON(p) {
      const parts = p.split('/');
      try {
        const dir = await walk(parts);
        const fh = await dir.getFileHandle(parts.at(-1));
        const file = await fh.getFile();
        const txt = await file.text();
        return JSON.parse(txt);
      } catch {
        return null;
      }
    },
    async writeJSON(p, data) {
      const parts = p.split('/');
      const dir = await walk(parts);
      const fh = await dir.getFileHandle(parts.at(-1), { create: true });
      const w = await fh.createWritable();
      await w.write(JSON.stringify(data, null, 2) + '\n');
      await w.close();
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
