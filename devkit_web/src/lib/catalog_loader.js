import { RACE_TRAITS } from '../schemas/worker.schema.js';

function collectEventFlags(events, acc) {
  if (events == null) return;
  if (Array.isArray(events)) {
    for (const e of events) collectEventFlags(e, acc);
    return;
  }
  if (typeof events !== 'object') return;
  for (const [k, v] of Object.entries(events)) {
    if (k === 'event_flags' || k === 'required_flags' || k === 'excluded_flags') {
      if (v && typeof v === 'object') for (const flag of Object.keys(v)) acc.add(flag);
    } else {
      collectEventFlags(v, acc);
    }
  }
}

export function buildCatalogs(sources) {
  const all_traits = new Set();
  const race_traits = new Set(RACE_TRAITS);
  for (const file of sources.traits || []) {
    for (const t of file) {
      if (t && t.name) all_traits.add(t.name);
    }
  }

  const all_items = new Set();
  for (const file of sources.items || []) {
    const items = file.items || file;
    if (Array.isArray(items)) for (const i of items) if (i.id) all_items.add(i.id);
  }

  const all_buildings = new Set();
  const all_professions = new Set();
  for (const file of sources.buildings || []) {
    const list = Array.isArray(file) ? file : Object.values(file);
    for (const b of list) {
      if (b && b.id) all_buildings.add(b.id);
      for (const p of b.professions || []) if (p.id) all_professions.add(p.id);
    }
  }

  const all_worker_names = new Set();
  const all_worker_folders = new Set();
  for (const file of sources.workers || []) {
    for (const w of file) {
      if (w.name) all_worker_names.add(w.name);
      if (w.folder) all_worker_folders.add(w.folder);
    }
  }

  const all_event_flags = new Set();
  collectEventFlags(sources.events || [], all_event_flags);
  collectEventFlags(sources.interactions || [], all_event_flags);

  return {
    all_traits, race_traits, all_items,
    all_buildings, all_professions,
    all_worker_names, all_worker_folders,
    all_event_flags,
    names_lists: new Set(),
  };
}
