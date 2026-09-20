// Recruitment event schema — game/data/events/recruit/*.json (array files).
// Same base shape as pool events plus recruitment-specific keys.
import { EVENT_FIELDS, EVENT_RULES } from './event.schema.js';

export const recruit_event_schema = {
  id: 'recruit_event',
  fields: {
    ...EVENT_FIELDS,
    dialogue: { type: ['string', 'null'] },
    unlimited: { type: 'bool' },
    always_available: { type: 'bool' },
    random_worker: { type: 'bool' },
    worker_filter: {
      type: 'object',
      fields: {
        min_combat: { type: 'float', min: 0 },
        min_charm: { type: 'float', min: 0 },
        min_clever: { type: 'float', min: 0 },
        min_craft: { type: 'float', min: 0 },
        traits_required: { type: 'list_of_strings', catalog: 'all_traits' },
        traits_excluded: { type: 'list_of_strings', catalog: 'all_traits' },
      },
    },
  },
  rules: [
    ...EVENT_RULES,
    {
      id: 'has_recruit_choice',
      check: (e) => (e.choices || []).some((c) => c.effect && c.effect.recruit_worker),
      severity: 'warning',
      message: 'no choice sets effect.recruit_worker — this event cannot hire anyone',
    },
  ],
  legacy: {},
};
