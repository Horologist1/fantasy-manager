// Builds dist/FantasyManagerDevkit.html — a single self-contained HTML file
// that runs from file:// with a plain double-click. No server, no .cmd, no
// antivirus surface: all ES modules are bundled into one inline script and
// all catalog JSONs are inlined (fetch() is unavailable over file://).
//
// The bundler is deliberately tiny and relies on this codebase's conventions:
// only named `export const X` / `export function X` / `export async function X`
// declarations, and only string-literal import paths. The integrity test in
// tests/offline_build.test.js guards those assumptions.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.resolve(__dirname, '../src');
const OUT_DIR = path.resolve(__dirname, '../dist');
const OUT_FILE = path.join(OUT_DIR, 'FantasyManagerDevkit.html');

const STATIC_IMPORT = /import\s*\{([\s\S]*?)\}\s*from\s*['"]([^'"]+)['"];?/g;
const DYNAMIC_IMPORT = /import\(\s*['"]([^'"]+)['"]\s*\)/g;
const EXPORT_DECL = /^export\s+(?:async\s+function|function|const|let|var|class)\s+([A-Za-z0-9_$]+)/gm;

function resolveId(fromId, spec) {
  const dir = path.posix.dirname(fromId);
  return path.posix.normalize(path.posix.join(dir, spec));
}

async function readModule(id) {
  return fs.readFile(path.join(SRC, id), 'utf8');
}

function depsOf(id, source) {
  const deps = [];
  for (const m of source.matchAll(STATIC_IMPORT)) deps.push(resolveId(id, m[2]));
  for (const m of source.matchAll(DYNAMIC_IMPORT)) deps.push(resolveId(id, m[1]));
  return deps;
}

function transform(id, source) {
  const exported = [...source.matchAll(EXPORT_DECL)].map((m) => m[1]);
  let code = source
    .replace(STATIC_IMPORT, (_, names, spec) =>
      `const {${names}} = __fm.get('${resolveId(id, spec)}');`)
    .replace(DYNAMIC_IMPORT, (_, spec) =>
      `Promise.resolve(__fm.get('${resolveId(id, spec)}'))`)
    .replace(/^export\s+(?=(?:async\s+function|function|const|let|var|class)\s)/gm, '');
  return [
    `__fm.define('${id}', async () => {`,
    code,
    `return { ${exported.join(', ')} };`,
    `});`,
  ].join('\n');
}

async function collectGraph(entry) {
  const order = [];
  const seen = new Set();
  async function visit(id) {
    if (seen.has(id)) return;
    seen.add(id);
    const source = await readModule(id);
    for (const dep of depsOf(id, source)) await visit(dep);
    order.push({ id, source });
  }
  await visit(entry);
  return order;
}

const RUNTIME = `
const __fm = {
  mods: Object.create(null),
  defs: [],
  define(id, fn) { this.defs.push([id, fn]); },
  get(id) {
    if (!(id in this.mods)) throw new Error('module not loaded: ' + id);
    return this.mods[id];
  },
  async boot() {
    for (const [id, fn] of this.defs) this.mods[id] = await fn();
  },
};`;

async function inlineCatalogs() {
  const dir = path.join(SRC, 'catalogs');
  const out = {};
  for (const f of await fs.readdir(dir)) {
    if (!f.endsWith('.json') || f === '_meta.json') continue;
    out[path.basename(f, '.json')] = JSON.parse(await fs.readFile(path.join(dir, f), 'utf8'));
  }
  return out;
}

export async function buildOfflineHTML() {
  const modules = await collectGraph('app.js');
  const css = await fs.readFile(path.join(SRC, 'styles.css'), 'utf8');
  const catalogs = await inlineCatalogs();

  const script = [
    `window.__FM_BUNDLED_CATALOGS = ${JSON.stringify(catalogs)};`,
    RUNTIME,
    ...modules.map(({ id, source }) => transform(id, source)),
    `await __fm.boot();`,
  ].join('\n\n');

  let html = await fs.readFile(path.join(SRC, 'index.html'), 'utf8');
  html = html.replace(
    '<link rel="stylesheet" href="styles.css">',
    `<style>\n${css}\n</style>`,
  );
  html = html.replace(
    '<script type="module" src="app.js"></script>',
    `<script type="module">\n${script.replace(/<\/script>/gi, '<\\/script>')}\n</script>`,
  );
  return html;
}

async function main() {
  const html = await buildOfflineHTML();
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.writeFile(OUT_FILE, html);
  console.log(`Built ${OUT_FILE} (${(html.length / 1024 / 1024).toFixed(1)} MB)`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
