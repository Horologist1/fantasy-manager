import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { referenceMetadata, catalogsFromFiles } from '../src/lib/reference.js';
import { categoryFor, parseJSON } from '../src/lib/contract.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const GAME_ROOT = process.env.FM_GAME_ROOT
  ? path.resolve(process.env.FM_GAME_ROOT)
  : path.resolve(__dirname, '../..');
const GAME_DATA = path.resolve(GAME_ROOT, 'game/data');
const IMAGES_WORKERS = path.resolve(GAME_ROOT, 'game/images/workers');
const OUT_DIR = path.resolve(__dirname, '../src/catalogs');
const NAMES_PATH = path.resolve(GAME_DATA, 'names.json');

async function main() {
  const baseFiles = {};
  async function visit(dir, prefix) {
    for (const entry of await fs.readdir(dir, {withFileTypes:true})) {
      const rel = prefix + '/' + entry.name;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) await visit(full, rel);
      else if (categoryFor(rel)) baseFiles[rel] = parseJSON(await fs.readFile(full, 'utf8'));
    }
  }
  await visit(GAME_DATA, 'data');
  const catalogs = catalogsFromFiles(baseFiles);
  const options = await fs.readFile(path.join(GAME_ROOT, 'game/scripts/core/options.rpy'), 'utf8');
  const gameVersion = options.match(/define config\.version\s*=\s*"([^"]+)"/)?.[1];
  if (!gameVersion) throw new Error('Cannot determine target game version.');
  const metadata = await referenceMetadata(baseFiles, gameVersion);

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
    JSON.stringify({ ...metadata, baked_at: new Date().toISOString() }, null, 2) + '\n',
  );
  await fs.writeFile(path.join(OUT_DIR, 'base_files.json'), JSON.stringify(baseFiles) + '\n');

  console.log(`Baked ${Object.keys(catalogs).length + 2} catalogs (+ meta) to ${OUT_DIR}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
