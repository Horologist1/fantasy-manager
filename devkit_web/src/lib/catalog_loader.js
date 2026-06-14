import { RACE_TRAITS, ALL_SKILLS } from '../schemas/worker.schema.js';

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
  const trait_meta = {};
  for (const file of sources.traits || []) {
    for (const t of file) {
      if (t && t.name) {
        all_traits.add(t.name);
        trait_meta[t.name] = {
          description: t.description || '',
          nsfw: !!t.nsfw,
        };
      }
    }
  }

  const all_items = new Set();
  const item_meta = {};
  for (const file of sources.items || []) {
    const items = file.items || file;
    if (Array.isArray(items)) {
      for (const i of items) {
        if (!i || !i.id) continue;
        all_items.add(i.id);
        item_meta[i.id] = {
          name: i.display_name || i.name || i.id,
          description: i.description || '',
          type: i.type || '',
        };
      }
    }
  }

  const all_buildings = new Set();
  const all_professions = new Set();
  const all_skills = new Set(ALL_SKILLS);
  const all_map_locations = new Set();
  const building_meta = {};
  const building_professions = {};
  const building_full = {};
  for (const file of sources.buildings || []) {
    // Game files wrap the array as { building_types: [...] }; raw arrays are
    // accepted too for fixtures/legacy.
    const list = Array.isArray(file) ? file : (file && file.building_types) || [];
    for (const b of list) {
      if (!b || !b.id) continue;
      all_buildings.add(b.id);
      building_full[b.id] = JSON.parse(JSON.stringify(b));
      for (const loc of b.allowed_map_locations || []) all_map_locations.add(loc);
      if (b.skill_name) all_skills.add(b.skill_name);
      building_meta[b.id] = {
        name: b.name || b.id,
        skill_name: b.skill_name || '',
        skill_description: b.skill_description || '',
      };
      const profs = [];
      for (const p of b.professions || []) {
        if (!p || !p.id) continue;
        all_professions.add(p.id);
        profs.push({ id: p.id, name: p.name || p.id, description: p.description || '' });
      }
      building_professions[b.id] = { name: b.name || b.id, professions: profs };
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
    all_buildings, all_professions, all_skills, all_map_locations,
    all_worker_names, all_worker_folders,
    all_event_flags,
    names_lists: new Set(),
    meta: { trait_meta, item_meta, building_meta, building_professions, building_full },
  };
}
