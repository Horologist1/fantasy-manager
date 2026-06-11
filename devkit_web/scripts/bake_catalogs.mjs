import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildCatalogs } from '../src/lib/catalog_loader.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const GAME_DATA = path.resolve(__dirname, '../../game/data');
const IMAGES_WORKERS = path.resolve(__dirname, '../../game/images/workers');
const OUT_DIR = path.resolve(__dirname, '../src/catalogs');
const NAMES_PATH = path.resolve(GAME_DATA, 'names.json');

async function loadFolder(name) {
  const dir = path.join(GAME_DATA, name);
  let entries;
  try {
    entries = await fs.readdir(dir);
  } catch {
    return [];
  }
  const out = [];
  for (const f of entries) {
    if (!f.endsWith('.json')) continue;
    const raw = await fs.readFile(path.join(dir, f), 'utf8');
    try {
      out.push(JSON.parse(raw));
    } catch (e) {
      console.error(`skip ${name}/${f}: ${e.message}`);
    }
  }
  return out;
}

async function main() {
  const sources = {
    traits: await loadFolder('traits'),
    items: await loadFolder('items'),
    buildings: await loadFolder('buildings'),
    workers: await loadFolder('workers'),
    interactions: await loadFolder('interactions'),
    events: await loadFolder('events'),
  };
  const catalogs = buildCatalogs(sources);

  let names_lists = [];
  try {
    const names = JSON.parse(await fs.readFile(NAMES_PATH, 'utf8'));
    names_lists = Object.keys(names);
  } catch {}

  let image_folders = [];
  try {
    const entries = await fs.readdir(IMAGES_WORKERS, { withFileTypes: true });
    image_folders = entries.filter((e) => e.isDirectory()).map((e) => e.name);
  } catch {}

  await fs.mkdir(OUT_DIR, { recursive: true });
  for (const [key, val] of Object.entries(catalogs)) {
    if (key === 'meta') {
      // meta is a nested object map (trait_meta, item_meta, building_meta) —
      // serialise each as its own file so the bundled loader can fetch them
      // individually.
      for (const [metaKey, metaVal] of Object.entries(val)) {
        await fs.writeFile(
          path.join(OUT_DIR, `${metaKey}.json`),
          JSON.stringify(metaVal, null, 2) + '\n',
        );
      }
      continue;
    }
    const arr = Array.from(val).sort();
    await fs.writeFile(
      path.join(OUT_DIR, `${key}.json`),
      JSON.stringify(arr, null, 2) + '\n',
    );
  }
  await fs.writeFile(
    path.join(OUT_DIR, 'names_lists.json'),
    JSON.stringify(names_lists.sort(), null, 2) + '\n',
  );
  await fs.writeFile(
    path.join(OUT_DIR, 'image_folders.json'),
    JSON.stringify(image_folders.sort(), null, 2) + '\n',
  );
  await fs.writeFile(
    path.join(OUT_DIR, '_meta.json'),
    JSON.stringify({ baked_at: new Date().toISOString() }, null, 2) + '\n',
  );

  console.log(`Baked ${Object.keys(catalogs).length + 2} catalogs (+ meta) to ${OUT_DIR}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
