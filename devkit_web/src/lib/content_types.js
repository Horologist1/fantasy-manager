import { workerIdentity } from './contract.js';
import { monthly_card_schema, monthly_card_editor_sections } from '../schemas/monthly_card.schema.js';
import { monthly_card_recipe } from '../recipes/monthly_cards.js';
import { worker_schema, RACE_TRAITS } from '../schemas/worker.schema.js';
import { trait_schema } from '../schemas/trait.schema.js';
import { item_schema } from '../schemas/item.schema.js';
import { interaction_schema } from '../schemas/interaction.schema.js';
import { event_schema } from '../schemas/event.schema.js';
import { recruit_event_schema } from '../schemas/recruit_event.schema.js';
import { daily_story_schema } from '../schemas/daily_story.schema.js';
import { building_schema } from '../schemas/building.schema.js';

import { worker_editor_sections } from '../editors/worker_editor.js';
import {
  trait_editor_sections, item_editor_sections, interaction_editor_sections,
  event_editor_sections, recruit_event_editor_sections,
  daily_story_editor_sections, building_editor_sections,
} from '../editors/content_editors.js';

import { unique_worker_recipe } from '../recipes/unique_worker.js';
import { monster_worker_recipe, procedural_worker_template_recipe } from '../recipes/workers.js';
import { permanent_trait_recipe, temporary_trait_recipe } from '../recipes/traits.js';
import { consumable_item_recipe, equipment_item_recipe, quest_item_recipe } from '../recipes/items.js';
import {
  simple_interaction_recipe, trait_granting_interaction_recipe,
  worker_specific_interaction_recipe,
} from '../recipes/interactions.js';
import { daily_story_basic_recipe, daily_story_with_trait_roll_recipe } from '../recipes/daily_stories.js';
import {
  worker_specific_event_recipe, event_chain_2_steps_recipe,
  building_event_with_skill_check_recipe, recruitment_event_recipe,
} from '../recipes/events.js';
import { simple_building_type_recipe, add_profession_to_building_recipe } from '../recipes/buildings.js';
export const TYPES = [
  {
    id:'monthly_conditions', title:'🗓 Monthly conditions',
    blurb:'Monthly cards and activity modifiers. Export the complete cards.json catalog; keep the existing cards when adding new ones.',
    folder:'monthly_conditions', key:'id', wrapper:null,
    schema:monthly_card_schema, sections:monthly_card_editor_sections,
    recipes:[monthly_card_recipe],
  },
  {
    id: 'workers', title: '👤 Workers',
    blurb: 'Hireable characters: unique, procedural, monsters.',
    folder: 'workers', key: workerIdentity, wrapper: null,
    schema: worker_schema, sections: worker_editor_sections,
    recipes: [unique_worker_recipe, procedural_worker_template_recipe, monster_worker_recipe],
  },
  {
    id: 'traits', title: '✨ Traits',
    blurb: 'Character traits with skill and earnings modifiers.',
    folder: 'traits', key: 'name', wrapper: null,
    schema: trait_schema, sections: trait_editor_sections,
    recipes: [permanent_trait_recipe, temporary_trait_recipe],
  },
  {
    id: 'items', title: '🎒 Items',
    blurb: 'Consumables, equipment and quest items.',
    folder: 'items', key: 'id', wrapper: 'items',
    schema: item_schema, sections: item_editor_sections,
    recipes: [consumable_item_recipe, equipment_item_recipe, quest_item_recipe],
  },
  {
    id: 'interactions', title: '💬 Interactions',
    blurb: 'Talk/activity options in the worker menu.',
    folder: 'interactions', key: 'id', wrapper: null,
    schema: interaction_schema, sections: interaction_editor_sections,
    recipes: [
      simple_interaction_recipe, trait_granting_interaction_recipe,
      worker_specific_interaction_recipe,
    ],
  },
  {
    id: 'events', title: '⚡ Events',
    blurb: 'Story scenes with choices, skill checks and flags.',
    folder: 'events', key: 'id', wrapper: null,
    schema: event_schema, sections: event_editor_sections,
    recipes: [
      worker_specific_event_recipe, event_chain_2_steps_recipe,
      building_event_with_skill_check_recipe,
    ],
  },
  {
    id: 'recruit_events', title: '🤝 Recruitment Events',
    blurb: 'Applicants who show up looking for work.',
    folder: 'events/recruit', key: 'id', wrapper: null,
    schema: recruit_event_schema, sections: recruit_event_editor_sections,
    recipes: [recruitment_event_recipe],
  },
  {
    id: 'daily_stories', title: '📜 Daily Stories',
    blurb: 'Work-day stories for existing jobs (saved as extensions).',
    folder: 'buildings/daily_story_extensions', key: 'id', wrapper: null,
    schema: daily_story_schema, sections: daily_story_editor_sections,
    recipes: [daily_story_basic_recipe, daily_story_with_trait_roll_recipe],
  },
  {
    id: 'buildings', title: '🏠 Buildings',
    blurb: 'Building types with jobs and daily stories.',
    folder: 'buildings', key: 'id', wrapper: 'building_types',
    schema: building_schema, sections: building_editor_sections,
    recipes: [simple_building_type_recipe, add_profession_to_building_recipe],
  },
];

