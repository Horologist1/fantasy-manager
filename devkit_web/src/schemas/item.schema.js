// Item schema — game/data/items/*.json ({ items: [], excluded_from_shops: [] }).
import { allIn } from './_rules.js';

export const ITEM_TYPES = [
  'consumable', 'weapon', 'armor', 'accessory', 'clothing',
  'gift', 'quest_item', 'currency', 'misc',
];

export const item_schema = {
  id: 'item',
  fields: {
    id: { type: 'string', required: true, unique_in_file: true },
    name: { type: 'string', required: true },
    display_name: { type: ['string', 'null'] },
    type: { type: 'string', required: true },
    effect: {
      type: 'object',
      fields: {
        custom: { type: ['string', 'null'] },
        skill_modifiers: { type: 'dict_of_numbers', key_catalog: 'all_skills' },
        attribute_modifiers: { type: 'dict_of_numbers' },
        daily_effects: { type: 'dict_of_numbers' },
        health: { type: 'float' },
        energy: { type: 'float' },
        joy: { type: 'float' },
        romance: { type: 'float' },
        relationship: { type: 'float' },
        rebelliousness: { type: 'float' },
        libido: { type: 'float' },
        libido_max: { type: 'float' },
        libido_regeneration: { type: 'float' },
        money: { type: 'float' },
      },
    },
    description: { type: ['longtext', 'null'] },
    durability: { type: 'int' },
    price: { type: 'float', min: 0 },
    weight: { type: 'float' },
    nsfw: { type: 'bool' },
    image: { type: ['string', 'null'] },
    shop_available: { type: 'bool' },
    shop_chance: { type: 'float' },
    shop_only: { type: ['string', 'null'] },
    auto_consume_on_receive: { type: 'bool' },
    consume_on_purchase: { type: 'bool' },
    purchase_effect: { type: ['string', 'null'] },
    obtain_hint: { type: ['string', 'null'] },
  },
  rules: [
    {
      id: 'type_known',
      check: (e) => e.type == null || ITEM_TYPES.includes(e.type),
      severity: 'warning',
      message: `type is not one of the known item types (${ITEM_TYPES.join(', ')})`,
    },
    {
      id: 'effect_traits_exist',
      check: (e, ctx) => {
        const names = [];
        for (const k of ['add_trait', 'remove_trait']) {
          const v = e.effect?.[k];
          if (typeof v === 'string') names.push(v);
          else if (v && typeof v === 'object' && typeof v.name === 'string') names.push(v.name);
        }
        return allIn(ctx.catalogs.all_traits, names);
      },
      severity: 'warning',
      message: 'effect add_trait/remove_trait references a trait that does not exist',
    },
  ],
  legacy: {},
};
