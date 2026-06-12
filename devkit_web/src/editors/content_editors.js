// Section definitions for the generic editor engine, one per content type.
// (Workers have their own module: worker_editor.js.)
import { trait_schema } from '../schemas/trait.schema.js';
import { item_schema } from '../schemas/item.schema.js';
import { interaction_schema } from '../schemas/interaction.schema.js';
import { event_schema } from '../schemas/event.schema.js';
import { recruit_event_schema } from '../schemas/recruit_event.schema.js';
import { daily_story_schema } from '../schemas/daily_story.schema.js';
import { building_schema } from '../schemas/building.schema.js';

function field(schema, name, overrides = {}) {
  return { id: name, label: name, ...schema.fields[name], ...overrides };
}

export const trait_editor_sections = [
  {
    id: 'basic',
    label: 'Basic',
    fields: [
      field(trait_schema, 'name', { label: 'Name' }),
      field(trait_schema, 'description', { label: 'Description' }),
      field(trait_schema, 'nsfw', { label: 'NSFW' }),
      field(trait_schema, 'duration', { label: 'Duration (days, 0 = permanent)' }),
      field(trait_schema, 'gender_restriction', { label: 'Gender restriction' }),
    ],
  },
  {
    id: 'modifiers',
    label: 'Modifiers',
    fields: [field(trait_schema, 'modifiers', { label: 'Modifiers' })],
  },
  {
    id: 'relations',
    label: 'Trait relations',
    fields: [
      field(trait_schema, 'conflicts', { label: 'Conflicts with' }),
      field(trait_schema, 'removes_traits', { label: 'Removes traits' }),
      field(trait_schema, 'requires_traits', { label: 'Requires traits' }),
    ],
  },
];

export const item_editor_sections = [
  {
    id: 'basic',
    label: 'Basic',
    fields: [
      field(item_schema, 'id', { label: 'Id' }),
      field(item_schema, 'name', { label: 'Name' }),
      field(item_schema, 'display_name', { label: 'Display name' }),
      field(item_schema, 'type', { label: 'Type' }),
      field(item_schema, 'description', { label: 'Description' }),
      field(item_schema, 'nsfw', { label: 'NSFW' }),
    ],
  },
  {
    id: 'effect',
    label: 'Effect',
    fields: [field(item_schema, 'effect', { label: 'Effect' })],
  },
  {
    id: 'shop',
    label: 'Shop & misc',
    fields: [
      field(item_schema, 'price', { label: 'Price' }),
      field(item_schema, 'durability', { label: 'Durability' }),
      field(item_schema, 'weight', { label: 'Weight' }),
      field(item_schema, 'image', { label: 'Image id' }),
      field(item_schema, 'obtain_hint', { label: 'Obtain hint' }),
    ],
  },
];

export const interaction_editor_sections = [
  {
    id: 'basic',
    label: 'Basic',
    fields: [
      field(interaction_schema, 'id', { label: 'Id' }),
      field(interaction_schema, 'name', { label: 'Name' }),
      field(interaction_schema, 'description', { label: 'Description' }),
      field(interaction_schema, 'categories', { label: 'Categories' }),
      field(interaction_schema, 'interaction_level', { label: 'Interaction level' }),
      field(interaction_schema, 'image', { label: 'Image id' }),
      field(interaction_schema, 'nsfw', { label: 'NSFW' }),
    ],
  },
  {
    id: 'costs',
    label: 'Costs & effects',
    fields: [
      field(interaction_schema, 'cost_energy', { label: 'Energy cost' }),
      field(interaction_schema, 'cost_money', { label: 'Money cost' }),
      field(interaction_schema, 'effect', { label: 'Effect' }),
    ],
  },
  {
    id: 'requirements',
    label: 'Requirements',
    fields: [
      field(interaction_schema, 'stat_requirements', { label: 'Stat requirements' }),
      field(interaction_schema, 'required_traits', { label: 'Required traits' }),
      field(interaction_schema, 'excluded_traits', { label: 'Excluded traits' }),
      field(interaction_schema, 'specific_workers', { label: 'Specific workers' }),
      field(interaction_schema, 'specific_worker_images', { label: 'Specific worker folders' }),
      field(interaction_schema, 'worker_gender', { label: 'Worker gender' }),
      field(interaction_schema, 'gender_filter', { label: 'Manager gender filter' }),
      field(interaction_schema, 'required_flags', { label: 'Required flags' }),
      field(interaction_schema, 'excluded_flags', { label: 'Excluded flags' }),
    ],
  },
];

function eventSections(schema, extraBasic = []) {
  return [
    {
      id: 'basic',
      label: 'Basic',
      fields: [
        field(schema, 'id', { label: 'Id' }),
        field(schema, 'description', { label: 'Event text' }),
        ...extraBasic,
        field(schema, 'weight', { label: 'Weight' }),
        field(schema, 'event_probability', { label: 'Event probability (%)' }),
        field(schema, 'guaranteed', { label: 'Guaranteed' }),
        field(schema, 'limited', { label: 'Limited' }),
        field(schema, 'max_occurrences', { label: 'Max occurrences' }),
        field(schema, 'cooldown_days', { label: 'Cooldown (days)' }),
        field(schema, 'nsfw', { label: 'NSFW' }),
      ],
    },
    {
      id: 'targeting',
      label: 'Targeting',
      fields: [
        // worker_name may be a string or a list in shipped data; render as text
        // (with name suggestions) so string values round-trip unchanged.
        field(schema, 'worker_name', { label: 'Worker name', type: 'string', catalog: 'all_worker_names' }),
        field(schema, 'specific_worker_images', { label: 'Worker image folders' }),
        field(schema, 'worker_selection', { label: 'Worker selection (none/choose/player/random)' }),
        field(schema, 'building_type', { label: 'Building types', type: 'list_of_strings', catalog: 'all_buildings' }),
        field(schema, 'requires_assigned_worker', { label: 'Requires assigned worker' }),
        field(schema, 'required_building_worker_traits', { label: 'Required worker traits (building)' }),
        field(schema, 'required_active_professions', { label: 'Required active professions' }),
        field(schema, 'forbidden_active_professions', { label: 'Forbidden active professions' }),
        field(schema, 'player_gender_requirement', { label: 'Player gender requirement' }),
      ],
    },
    {
      id: 'conditions',
      label: 'Conditions & flags',
      fields: [
        field(schema, 'conditions', {
          label: 'Conditions',
          fields: {
            start_when: { type: ['string', 'null'], label: 'Start when' },
            stop_when: { type: ['string', 'null'], label: 'Stop when' },
          },
        }),
        field(schema, 'required_flags', { label: 'Required flags' }),
        field(schema, 'excluded_flags', { label: 'Excluded flags' }),
      ],
    },
    {
      id: 'choices',
      label: 'Choices',
      fields: [field(schema, 'choices', { label: 'Choices', item_label: 'Choice' })],
    },
    {
      id: 'images',
      label: 'Images',
      fields: [
        field(schema, 'background_image', { label: 'Background image' }),
        field(schema, 'success_image', { label: 'Success image' }),
        field(schema, 'failure_image', { label: 'Failure image' }),
      ],
    },
  ];
}

export const event_editor_sections = eventSections(event_schema);

export const recruit_event_editor_sections = eventSections(recruit_event_schema, [
  field(recruit_event_schema, 'dialogue', { label: 'Applicant dialogue' }),
  field(recruit_event_schema, 'unlimited', { label: 'Unlimited' }),
  field(recruit_event_schema, 'always_available', { label: 'Always available' }),
  field(recruit_event_schema, 'random_worker', { label: 'Random worker' }),
]);

export const daily_story_editor_sections = [
  {
    id: 'basic',
    label: 'Basic',
    fields: [
      field(daily_story_schema, 'id', { label: 'Id' }),
      field(daily_story_schema, 'report', { label: 'Report line' }),
      field(daily_story_schema, 'weight', { label: 'Weight' }),
      field(daily_story_schema, 'skill_options', { label: 'Skills rolled' }),
      field(daily_story_schema, 'difficulty_modifier', { label: 'Difficulty modifier' }),
      field(daily_story_schema, 'nsfw_only', { label: 'NSFW only' }),
    ],
  },
  {
    id: 'requirements',
    label: 'Requirements',
    fields: [
      field(daily_story_schema, 'required_traits', { label: 'Required traits' }),
      field(daily_story_schema, 'excluded_traits', { label: 'Excluded traits' }),
      field(daily_story_schema, 'stat_requirements', { label: 'Stat requirements' }),
      field(daily_story_schema, 'worker_gender_requirement', { label: 'Worker gender' }),
      field(daily_story_schema, 'player_gender_requirement', { label: 'Player gender' }),
    ],
  },
  {
    id: 'traits',
    label: 'Trait weights',
    fields: [
      field(daily_story_schema, 'positive_traits', { label: 'Helpful traits (weight)' }),
      field(daily_story_schema, 'negative_traits', { label: 'Harmful traits (weight)' }),
      field(daily_story_schema, 'trait_msg_success', { label: 'Trait flavor (success)' }),
      field(daily_story_schema, 'trait_msg_failure', { label: 'Trait flavor (failure)' }),
    ],
  },
  {
    id: 'outcomes',
    label: 'Outcomes',
    fields: [
      field(daily_story_schema, 'descriptions', { label: 'Outcome texts' }),
      field(daily_story_schema, 'earnings', { label: 'Earnings formulas' }),
      field(daily_story_schema, 'consequences', { label: 'Consequences' }),
    ],
  },
  {
    id: 'extras',
    label: 'Images & loot',
    fields: [
      field(daily_story_schema, 'story_image', { label: 'Story image' }),
      field(daily_story_schema, 'failure_image', { label: 'Failure image' }),
      field(daily_story_schema, 'loot', { label: 'Loot' }),
    ],
  },
];

export const building_editor_sections = [
  {
    id: 'basic',
    label: 'Basic',
    fields: [
      field(building_schema, 'id', { label: 'Id' }),
      field(building_schema, 'name', { label: 'Name' }),
      field(building_schema, 'skill_name', { label: 'Building skill' }),
      field(building_schema, 'skill_description', { label: 'Skill description' }),
      field(building_schema, 'allowed_map_locations', { label: 'Allowed map locations', catalog: 'all_map_locations' }),
      field(building_schema, 'nsfw', { label: 'NSFW' }),
    ],
  },
  {
    id: 'professions',
    label: 'Jobs',
    fields: [
      field(building_schema, 'professions', { label: 'Jobs (professions)', item_label: 'Job' }),
    ],
  },
];
