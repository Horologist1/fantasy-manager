// WM → FM image filename normalization. Port of rename_wm_images_in_folder
// from the v6 editor, with one improvement: trailing copy markers ("(2)",
// "_3") are stripped BEFORE applying the patterns, so "Nude_3.jpg" maps to
// "strip.jpg" instead of leaking through as "nude.jpg".
import { WM_IMAGE_RENAME_PATTERNS, WM_IMAGE_EXTENSIONS } from './wm_mappings.js';

function splitExt(filename) {
  const i = filename.lastIndexOf('.');
  if (i <= 0) return [filename, ''];
  return [filename.slice(0, i), filename.slice(i)];
}

export function renameWMImageName(filename) {
  const [stem, ext] = splitExt(filename);
  let name = stem
    .replace(/\s*\(\d+\)\s*/g, '')
    .replace(/_+\d+$/, '');
  for (const [pattern, replacement] of WM_IMAGE_RENAME_PATTERNS) {
    name = name.replace(new RegExp(pattern, 'i'), replacement);
  }
  name = name.toLowerCase()
    .replace(/\s*\(\d+\)\s*/g, '')
    .replace(/_+\d+$/, '')
    .replace(/[_\s]+/g, '_')
    .replace(/^_+|_+$/g, '');
  return name + ext.toLowerCase();
}

/**
 * Plans renames for a list of filenames. Non-image files and files whose name
 * does not change are omitted. Collisions get " (1)", " (2)" suffixes —
 * matching the v6 behavior.
 */
export function planRenames(filenames) {
  const plan = [];
  const taken = new Set(filenames.map((f) => f.toLowerCase()));
  for (const from of filenames) {
    const [, ext] = splitExt(from);
    if (!WM_IMAGE_EXTENSIONS.includes(ext.toLowerCase())) continue;
    let to = renameWMImageName(from);
    if (to === from) continue;
    if (taken.has(to.toLowerCase()) && to.toLowerCase() !== from.toLowerCase()) {
      const [stem, ext2] = splitExt(to);
      let counter = 1;
      while (taken.has(`${stem} (${counter})${ext2}`.toLowerCase())) counter += 1;
      to = `${stem} (${counter})${ext2}`;
    }
    taken.delete(from.toLowerCase());
    taken.add(to.toLowerCase());
    plan.push({ from, to });
  }
  return plan;
}
