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
    worker_filter: { type: 'object' },
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
