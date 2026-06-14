// Event recipes — worker-specific, 2-step chain, building skill check, recruitment.
import { slug, neutralEffect } from './_helpers.js';

function baseEvent(a) {
  return {
    id: slug(a.id),
    description: a.description || null,
    weight: a.weight ?? 5,
    limited: false,
    max_occurrences: 0,
    cooldown_days: 0,
    event_probability: 0,
    guaranteed: false,
    worker_name: null,
    specific_worker_images: [],
    worker_selection: 'random',
    worker_gender_requirement: null,
    player_gender_requirement: null,
    requires_assigned_worker: false,
    required_building_worker_traits: [],
    required_active_professions: [],
    forbidden_active_professions: [],
    required_building_worker_min_skill: null,
    required_building_worker_skill: null,
    building_type: [],
    background_image: null,
    success_image: null,
    failure_image: null,
    nsfw: !!a.nsfw,
    required_flags: {},
    excluded_flags: {},
    conditions: { start_when: null, stop_when: null },
    choices: [],
  };
}

function simpleChoice(option, message, effect = {}) {
  return {
    option,
    condition: null,
    threshold: 0,
    required_traits: [],
    excluded_traits: [],
    trait_visibility: 'hide',
    blocked_message: null,
    message,
    message_success: null,
    message_failure: null,
    required_flags: {},
    excluded_flags: {},
    effect: { ...neutralEffect(), ...effect },
  };
}

export const worker_specific_event_recipe = {
  id: 'worker_specific_event',
  title: 'Worker-Specific Event',
  description: 'A one-off scene that fires for one named worker (yours or a base-game one).',
  kind: 'event',
  default_output: 'events/events_<modname>.json',
  steps: [
    { id: 'worker_name', type: 'string', catalog: 'all_worker_names',
      label: 'Worker name', required: true,
      hint: 'Pick an existing worker or type the name of your own new worker.' },
    { id: 'id', type: 'string', label: 'Event id', required: true,
      hint: 'Unique id, e.g. mymod_aelis_gift' },
    { id: 'description', type: 'longtext', label: 'Event text', required: true,
      hint: 'The scene shown when the event fires.' },
    { id: 'option_text', type: 'string', label: 'Choice button text', default: 'Continue' },
    { id: 'message', type: 'longtext', label: 'Result text', required: true },
    { id: 'money', type: 'int', label: 'Money gained (or lost if negative)', default: 0 },
    { id: 'one_time', type: 'bool', label: 'Happens only once?', default: true },
    { id: 'nsfw', type: 'bool', label: 'NSFW event?', default: false },
  ],
  build: (a) => {
    const e = baseEvent(a);
    e.worker_name = a.worker_name;
    e.conditions.start_when = `has_worker:${a.worker_name}`;
    const choice = simpleChoice(a.option_text || 'Continue', a.message, { money: a.money ?? 0 });
    if (a.one_time) {
      const flag = `${slug(a.id)}_done`;
      e.excluded_flags = { [flag]: true };
      choice.effect.event_flags = { [flag]: true };
    }
    e.choices = [choice];
    return e;
  },
};

export const event_chain_2_steps_recipe = {
  id: 'event_chain_2_steps',
  title: 'Event Chain (2 steps)',
  description: 'Two linked events: the second only fires after the first happened. Each fires once.',
  kind: 'event',
  default_output: 'events/events_<modname>.json',
  steps: [
    { id: 'base_id', type: 'string', label: 'Chain id', required: true,
      hint: 'e.g. mymod_mystery — the events will be <id>_1 and <id>_2.' },
    { id: 'worker_name', type: 'string', catalog: 'all_worker_names',
      label: 'Worker (optional)',
      hint: 'Leave empty so any worker can star in the chain.' },
    { id: 'desc_1', type: 'longtext', label: 'Part 1 — event text', required: true },
    { id: 'option_1', type: 'string', label: 'Part 1 — choice text', default: 'Continue' },
    { id: 'message_1', type: 'longtext', label: 'Part 1 — result text', required: true },
    { id: 'desc_2', type: 'longtext', label: 'Part 2 — event text', required: true },
    { id: 'option_2', type: 'string', label: 'Part 2 — choice text', default: 'Continue' },
    { id: 'message_2', type: 'longtext', label: 'Part 2 — result text', required: true },
    { id: 'money_2', type: 'int', label: 'Money reward at the end', default: 100 },
    { id: 'nsfw', type: 'bool', label: 'NSFW chain?', default: false },
  ],
  build: (a) => {
    const base = slug(a.base_id);
    const f1 = `${base}_1_done`;
    const f2 = `${base}_2_done`;

    const e1 = baseEvent({ ...a, id: `${base}_1`, description: a.desc_1 });
    const e2 = baseEvent({ ...a, id: `${base}_2`, description: a.desc_2 });
    if (a.worker_name) {
      e1.worker_name = a.worker_name;
      e2.worker_name = a.worker_name;
      e1.conditions.start_when = `has_worker:${a.worker_name}`;
      e2.conditions.start_when = `has_worker:${a.worker_name}`;
    }
    e1.excluded_flags = { [f1]: true };
    const c1 = simpleChoice(a.option_1 || 'Continue', a.message_1);
    c1.effect.event_flags = { [f1]: true };
    e1.choices = [c1];

    e2.required_flags = { [f1]: true };
    e2.excluded_flags = { [f2]: true };
    const c2 = simpleChoice(a.option_2 || 'Continue', a.message_2, { money: a.money_2 ?? 0 });
    c2.effect.event_flags = { [f2]: true };
    e2.choices = [c2];

    return [e1, e2];
  },
};

export const building_event_with_skill_check_recipe = {
  id: 'building_event_with_skill_check',
  title: 'Building Event (skill check)',
  description: 'An event in one of your buildings where a worker rolls the building skill to succeed.',
  kind: 'event',
  default_output: 'events/events_<modname>.json',
  steps: [
    {
      id: 'building', type: 'enum', label: 'Building', required: true,
      options: (ctx) => Array.from(ctx.catalogs?.all_buildings || []).sort(),
      option_descriptions: (ctx) => Object.fromEntries(
        Object.entries(ctx.catalogs?.meta?.building_meta || {})
          .map(([id, b]) => [id, `${b.name}${b.skill_name ? ` — rolls ${b.skill_name}` : ''}`]),
      ),
    },
    { id: 'id', type: 'string', label: 'Event id', required: true },
    { id: 'description', type: 'longtext', label: 'Event text', required: true },
    { id: 'option_text', type: 'string', label: 'Choice button text', default: 'Attempt it' },
    { id: 'threshold', type: 'int', label: 'Difficulty threshold', default: 50, min: 1, max: 100,
      hint: 'Roll-under d100 against the worker’s building skill. Higher = easier.' },
    { id: 'message_success', type: 'longtext', label: 'Success text', required: true },
    { id: 'message_failure', type: 'longtext', label: 'Failure text', required: true },
    { id: 'money_success', type: 'int', label: 'Money on success', default: 100 },
    { id: 'money_failure', type: 'int', label: 'Money on failure (negative = loss)', default: 0 },
    { id: 'nsfw', type: 'bool', label: 'NSFW event?', default: false },
  ],
  build: (a) => {
    const e = baseEvent(a);
    e.building_type = [a.building];
    e.requires_assigned_worker = true;
    const choice = simpleChoice(a.option_text || 'Attempt it', null);
    choice.condition = 'building_skill';
    choice.threshold = a.threshold ?? 50;
    choice.message = null;
    choice.message_success = a.message_success;
    choice.message_failure = a.message_failure;
    choice.effect.success = { ...neutralEffect(), money: a.money_success ?? 0 };
    choice.effect.failure = { ...neutralEffect(), money: a.money_failure ?? 0 };
    e.choices = [choice];
    return e;
  },
};

export const recruitment_event_recipe = {
  id: 'recruitment_event',
  title: 'Recruitment Event',
  description: 'A random applicant shows up looking for work; the player can hire, negotiate, or decline.',
  kind: 'recruit_event',
  default_output: 'events/recruit/event_recruit_<modname>.json',
  steps: [
    { id: 'id', type: 'string', label: 'Event id', required: true,
      hint: 'e.g. mymod_wanderer — saved as event_recruit_<id>.' },
    { id: 'description', type: 'longtext', label: 'Scene text', required: true,
      hint: 'How the applicant approaches. Use [event_worker] for their name.' },
    { id: 'dialogue', type: 'longtext', label: 'Applicant dialogue',
      hint: 'Optional opening line, e.g. "I\'m [event_worker], looking for work."' },
    { id: 'hire_text', type: 'string', label: 'Hire option text',
      default: 'Hire them for [COST] per day.' },
    { id: 'negotiate', type: 'bool', label: 'Add a negotiate option (20% discount)?',
      default: true },
    { id: 'weight', type: 'int', label: 'Weight', default: 10, min: 1,
      hint: 'How often this applicant appears vs other recruitment events.' },
    { id: 'nsfw', type: 'bool', label: 'NSFW event?', default: false },
  ],
  build: (a) => {
    const id = slug(a.id);
    const e = {
      id: id.startsWith('event_recruit_') ? id : `event_recruit_${id}`,
      description: a.description,
      dialogue: a.dialogue || null,
      weight: a.weight ?? 10,
      unlimited: true,
      random_worker: true,
      always_available: true,
      background_image: null,
      success_image: null,
      failure_image: null,
      nsfw: !!a.nsfw,
      worker_name: null,
      worker_filter: {},
      player_gender_requirement: null,
      choices: [
        {
          option: a.hire_text || 'Hire them for [COST] per day.',
          message: 'You seal the deal at [actual_cost]. [event_worker] starts work at once.',
          effect: { recruit_worker: true },
        },
      ],
    };
    if (a.negotiate) {
      e.choices.push({
        option: 'Negotiate a lower wage.',
        message: 'After some back-and-forth you settle at [actual_cost] — a 20% discount.',
        effect: { recruit_worker: true, cost_modifier: 0.8 },
      });
    }
    e.choices.push({
      option: 'Politely decline.',
      message: 'You thank [event_worker] for their interest, but you are not hiring right now.',
      outcome_override: 'failure',
      effect: {},
    });
    return e;
  },
};
