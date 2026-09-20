// Item recipes — consumable, equipment, quest item.
import { slug } from './_helpers.js';

function baseItem(a, type) {
  return {
    id: slug(a.name),
    name: a.name,
    display_name: a.name,
    type,
    effect: {
      custom: null,
      skill_modifiers: {},
      attribute_modifiers: {},
      daily_effects: {},
    },
    description: a.description || null,
    durability: 0,
    price: a.price ?? 0,
    weight: 0,
    nsfw: !!a.nsfw,
  };
}

export const consumable_item_recipe = {
  id: 'consumable_item',
  title: 'Consumable Item',
  description: 'A one-use item (potion, food, tonic) that restores or boosts a worker stat.',
  kind: 'item',
  default_output: 'items/items_<modname>.json',
  steps: [
    { id: 'name', type: 'string', label: 'Item name', required: true, hint: 'e.g. Healing Brew' },
    { id: 'description', type: 'longtext', label: 'Description' },
    { id: 'price', type: 'int', label: 'Shop price', default: 50, min: 0 },
    {
      id: 'effect_kind', type: 'enum', label: 'What does it affect?',
      options: ['health', 'energy', 'joy', 'libido', 'none'],
      option_descriptions: {
        health: 'Restores worker health when used.',
        energy: 'Restores worker energy when used.',
        joy: 'Raises worker joy when used.',
        libido: 'Restores libido (NSFW mode only).',
        none: 'No stat effect (flavor / gift item).',
      },
      default: 'health',
    },
    { id: 'effect_amount', type: 'int', label: 'Effect amount', default: 10 },
    { id: 'nsfw', type: 'bool', label: 'NSFW item?', default: false },
  ],
  build: (a) => {
    const item = baseItem(a, 'consumable');
    if (a.effect_kind && a.effect_kind !== 'none') {
      item.effect[a.effect_kind] = a.effect_amount ?? 0;
    }
    return item;
  },
};

export const equipment_item_recipe = {
  id: 'equipment_item',
  title: 'Equipment Item',
  description: 'A wearable item (weapon, armor, accessory, clothing) that modifies skills while equipped.',
  kind: 'item',
  default_output: 'items/items_<modname>.json',
  steps: [
    { id: 'name', type: 'string', label: 'Item name', required: true, hint: 'e.g. Iron Sword' },
    { id: 'description', type: 'longtext', label: 'Description' },
    {
      id: 'type', type: 'enum', label: 'Equipment slot',
      options: ['weapon', 'armor', 'accessory', 'clothing'],
      default: 'weapon',
    },
    { id: 'skill_modifiers', type: 'dict_of_numbers', key_catalog: 'all_skills',
      label: 'Skill bonuses while equipped',
      hint: 'Click a skill to add it, e.g. Combat +5.' },
    { id: 'price', type: 'int', label: 'Shop price', default: 200, min: 0 },
    { id: 'nsfw', type: 'bool', label: 'NSFW item?', default: false },
  ],
  build: (a) => {
    const item = baseItem(a, a.type || 'weapon');
    item.effect.skill_modifiers = a.skill_modifiers || {};
    return item;
  },
};

export const quest_item_recipe = {
  id: 'quest_item',
  title: 'Quest Item',
  description: 'A story item given by events; it has no shop price or stat effects.',
  kind: 'item',
  default_output: 'items/items_<modname>.json',
  steps: [
    { id: 'name', type: 'string', label: 'Item name', required: true },
    { id: 'description', type: 'longtext', label: 'Description' },
    { id: 'obtain_hint', type: 'string', label: 'How is it obtained?',
      hint: 'Shown to players as a hint, e.g. "Reward from the Governor questline."' },
    { id: 'nsfw', type: 'bool', label: 'NSFW item?', default: false },
  ],
  build: (a) => {
    const item = baseItem(a, 'quest_item');
    item.price = 0;
    if (a.obtain_hint) item.obtain_hint = a.obtain_hint;
    return item;
  },
};
