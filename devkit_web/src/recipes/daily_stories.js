// Daily story recipes — saved as daily_story_extensions files, which the game
// merges into an existing building/profession at load time.
import { slug, OUTCOMES, neutralConsequences, buildingProfessionSteps } from './_helpers.js';

function requirementSteps() {
  return [
    { id: 'required_traits', type: 'list_of_strings', catalog: 'all_traits',
      label: 'Required traits (optional)', default: [],
      hint: 'Story only triggers for workers having all of these.' },
    { id: 'excluded_traits', type: 'list_of_strings', catalog: 'all_traits',
      label: 'Excluded traits', default: ['Gay', 'Lesbian'],
      hint: 'Story never triggers for workers having any of these. Defaults to Gay/Lesbian: '
        + 'straight-audience stories should not reach gay/lesbian workers, who get their own '
        + 'variants. Clear it for orientation-neutral stories (e.g. libido spikes, solo scenes), '
        + 'or when authoring a Gay/Lesbian variant itself (put the trait in Required instead).' },
    { id: 'worker_gender', type: 'enum', label: 'Worker gender requirement',
      options: ['any', 'female', 'male'], default: 'any' },
    { id: 'nsfw_only', type: 'bool', label: 'Only in NSFW mode?', default: false },
  ];
}

function storySteps() {
  return [
    ...buildingProfessionSteps(),
    { id: 'id', type: 'string', label: 'Story id', required: true,
      hint: 'Unique id, e.g. mymod_tavern_song' },
    { id: 'report', type: 'string', label: 'Report line', required: true,
      hint: 'Short label in the daily report, e.g. "Sang for the crowd".' },
    {
      id: 'skill', type: 'enum', label: 'Skill rolled',
      options: (ctx) => Array.from(ctx.catalogs?.all_skills || []).sort(),
      hint: 'The worker skill that decides success.',
    },
    { id: 'desc_failure', type: 'longtext', label: 'Text on failure', required: true,
      hint: 'Use {worker_name} for the worker’s name.' },
    { id: 'desc_mediocre', type: 'longtext', label: 'Text on mediocre result', required: true },
    { id: 'desc_success', type: 'longtext', label: 'Text on success', required: true },
    { id: 'desc_critical', type: 'longtext', label: 'Text on critical success', required: true },
    { id: 'base_pay', type: 'int', label: 'Money on success', default: 60, min: 0,
      hint: 'Failure pays 0, mediocre pays half, critical pays +50%.' },
    { id: 'weight', type: 'int', label: 'Story weight', default: 5, min: 1,
      hint: 'Higher weight = picked more often vs other stories of this job.' },
    { id: 'image_fallback_patterns', type: 'list_of_strings', label: 'Image fallback patterns (optional)', default: [],
      hint: 'If set (e.g. beast, extreme), the daily-report image falls back to these IN ORDER instead of the rolled skill. Leave empty to use the rolled skill.' },
    ...requirementSteps(),
  ];
}

export function buildStory(a) {
  const story = {
    id: slug(a.id),
    weight: a.weight ?? 5,
    report: a.report,
    description: null,
    difficulty_modifier: 0,
    worker_gender_requirement: a.worker_gender === 'any' || !a.worker_gender ? null : a.worker_gender,
    player_gender_requirement: null,
    nsfw_only: !!a.nsfw_only,
    skill_options: a.skill ? [a.skill] : [],
    event_image_skill_exclude: [],
    positive_traits: a.positive_traits || {},
    negative_traits: a.negative_traits || {},
    trait_msg_success: a.trait_msg_success || null,
    trait_msg_failure: a.trait_msg_failure || null,
    trait_success: null,
    required_traits: a.required_traits || [],
    excluded_traits: a.excluded_traits || [],
    stat_requirements: {},
    descriptions: {
      failure: a.desc_failure,
      mediocre: a.desc_mediocre,
      success: a.desc_success,
      critical_success: a.desc_critical,
    },
    earnings: {
      failure: '0',
      mediocre: String(Math.round((a.base_pay ?? 60) * 0.5)),
      success: String(a.base_pay ?? 60),
      critical_success: String(Math.round((a.base_pay ?? 60) * 1.5)),
    },
    consequences: neutralConsequences(),
    story_image: null,
    failure_image: null,
    image_fallback_patterns: a.image_fallback_patterns || [],
    loot: { rolls: 0, bonus_items: [] },
  };
  return story;
}

export const daily_story_basic_recipe = {
  id: 'daily_story_basic',
  title: 'Daily Story (basic)',
  description: 'A new work-day story for an existing job: pick building + job, write the four outcome texts, set pay.',
  kind: 'daily_story_extension',
  default_output: 'buildings/daily_story_extensions/<modname>_stories.json',
  steps: storySteps(),
  build: (a) => ({
    building_id: a.building,
    profession_id: a.profession,
    story: buildStory(a),
  }),
};

export const daily_story_with_trait_roll_recipe = {
  id: 'daily_story_with_trait_roll',
  title: 'Daily Story (trait roll)',
  description: 'A daily story where worker traits tilt the roll and can be earned on a critical success.',
  kind: 'daily_story_extension',
  default_output: 'buildings/daily_story_extensions/<modname>_stories.json',
  steps: [
    ...storySteps(),
    { id: 'positive_traits', type: 'dict_of_numbers', key_catalog: 'all_traits',
      label: 'Helpful traits (trait → weight)', default: {},
      hint: 'Workers with these traits roll better. Weight 1–5; higher = stronger.' },
    { id: 'negative_traits', type: 'dict_of_numbers', key_catalog: 'all_traits',
      label: 'Harmful traits (trait → weight)', default: {},
      hint: 'Workers with these traits roll worse.' },
    { id: 'trait_msg_success', type: 'longtext', label: 'Trait flavor on success',
      hint: 'Optional. Use {worker_name} and {trait}.' },
    { id: 'trait_msg_failure', type: 'longtext', label: 'Trait flavor on failure',
      hint: 'Optional. Use {worker_name} and {trait}.' },
    { id: 'reward_trait', type: 'list_of_strings', catalog: 'all_traits',
      label: 'Trait that can be earned on critical success', default: [],
      hint: 'Optional — pick at most one.' },
    { id: 'reward_chance', type: 'int', label: 'Chance to earn it (%)', default: 25,
      min: 1, max: 100 },
  ],
  build: (a) => {
    const story = buildStory(a);
    const reward = (a.reward_trait || [])[0];
    if (reward) {
      story.consequences.critical_success.trait_chance = [
        { trait: reward, chance_percent: a.reward_chance ?? 25 },
      ];
    }
    return {
      building_id: a.building,
      profession_id: a.profession,
      story,
    };
  },
};
