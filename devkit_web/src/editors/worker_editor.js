import { worker_schema } from '../schemas/worker.schema.js';

function copyField(name, overrides = {}) {
  return { id: name, ...worker_schema.fields[name], ...overrides };
}

export const worker_editor_sections = [
  {
    id: 'basic',
    label: 'Basic',
    fields: [
      copyField('name', { label: 'Name' }),
      copyField('folder', { label: 'Image folder' }),
      copyField('gender', { label: 'Gender' }),
      copyField('cost', { label: 'Cost' }),
      copyField('comfort_desired', { label: 'Comfort desired (1–5)' }),
      copyField('description', { label: 'Description' }),
    ],
  },
  {
    id: 'flags',
    label: 'Flags',
    fields: [
      copyField('nsfw', { label: 'NSFW' }),
      copyField('unique', { label: 'Unique' }),
      copyField('encounter_only', { label: 'Encounter only' }),
      copyField('monster', { label: 'Monster' }),
      copyField('procedural', { label: 'Procedural' }),
      copyField('recruit_only', { label: 'Recruit only (not in buy-workers shop)' }),
      copyField('recruitment_locked', { label: 'Recruitment locked (quest/story worker)' }),
      copyField('event_recruit_only', { label: 'Specific recruit event only' }),
      copyField('required_store_value', { label: 'Required game-state values' }),
      copyField('names_list', { label: 'Names list (procedural)' }),
      copyField('template_id', { label: 'Template id (internal)' }),
      copyField('procedural_template', { label: 'Procedural monster template' }),
      copyField('monster_archetype', { label: 'Monster archetype' }),
    ],
  },
  {
    id: 'traits',
    label: 'Traits',
    fields: [
      copyField('traits', { label: 'Traits' }),
      copyField('monster_secondary_traits', { label: 'Random monster secondary traits' }),
    ],
  },
  {
    id: 'skills',
    label: 'Skills',
    fields: [
      copyField('skills', { label: 'Skills (0–100)', key_catalog: 'all_skills' }),
    ],
  },
];
