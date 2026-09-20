// Shared helpers for recipe build() functions.

/** "Healing Brew!" → "healing_brew" — safe id slug. */
export function slug(s) {
  return String(s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

export const OUTCOMES = ['failure', 'mediocre', 'success', 'critical_success'];

/** Full neutral consequence block (standardization rule: all keys present). */
export function neutralConsequence() {
  return {
    energy: 0, health: 0, joy: 0, rebelliousness: 0, romance: 0,
    relationship: 0, reputation: 0, libido: 0, obedience: 0,
    trait_chance: [], trait_remove_chance: [], give_item: null,
  };
}

export function neutralConsequences() {
  return Object.fromEntries(OUTCOMES.map((o) => [o, neutralConsequence()]));
}

/** Neutral event-effect payload (flat shape, no success/failure branches). */
export function neutralEffect() {
  return {
    money: 0, reputation: 0, custom: null, event_flags: {},
    item_id: null, loot_rolls: 0, skill_modifiers: {},
  };
}

/** Shared "pick a building, then one of its professions" steps. */
export function buildingProfessionSteps() {
  return [
    {
      id: 'building',
      type: 'enum',
      label: 'Building',
      required: true,
      options: (ctx) => Object.keys(ctx.catalogs?.meta?.building_professions || {}).sort(),
      option_descriptions: (ctx) => Object.fromEntries(
        Object.entries(ctx.catalogs?.meta?.building_professions || {})
          .map(([id, b]) => [id, b.name]),
      ),
    },
    {
      id: 'profession',
      type: 'enum',
      label: 'Profession (job)',
      required: true,
      options: (ctx, a) =>
        (ctx.catalogs?.meta?.building_professions?.[a.building]?.professions || [])
          .map((p) => p.id),
      option_descriptions: (ctx, a) => Object.fromEntries(
        (ctx.catalogs?.meta?.building_professions?.[a.building]?.professions || [])
          .map((p) => [p.id, p.description ? `${p.name} — ${p.description}` : p.name]),
      ),
    },
  ];
}
