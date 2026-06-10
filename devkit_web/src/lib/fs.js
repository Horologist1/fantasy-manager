/**
 * Common fs interface:
 *   - openRoot()                  → must be called once (browser only)
 *   - readJSON(relPath)           → parsed JSON or null
 *   - writeJSON(relPath, data)
 *   - listDir(relDir)             → [filename, ...]
 *   - mergeAndWrite(relPath, entry, { key }) → append-or-replace into array file
 */

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
    async mergeAndWrite(p, entry, { key }) {
      let arr = (await this.readJSON(p)) || [];
      if (!Array.isArray(arr)) {
        throw new Error(`mergeAndWrite expects array root at ${p}`);
      }
      const idx = arr.findIndex((e) => e && e[key] === entry[key]);
      if (idx >= 0) arr[idx] = entry;
      else arr = [...arr, entry];
      await this.writeJSON(p, arr);
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
    async mergeAndWrite(p, entry, { key }) {
      let arr = (await this.readJSON(p)) || [];
      if (!Array.isArray(arr)) throw new Error(`mergeAndWrite expects array root at ${p}`);
      const idx = arr.findIndex((e) => e && e[key] === entry[key]);
      if (idx >= 0) arr[idx] = entry;
      else arr = [...arr, entry];
      await this.writeJSON(p, arr);
    },
  };
}
