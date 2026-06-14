// Whoremaster .girlsx/.rgirlsx → Fantasy Manager worker conversion.
// Port of parse_wm_girl_xml / convert_wm_to_fm_worker from the v6 editor,
// with two deliberate additions: unknown traits/skills are reported (not
// silently dropped) so the UI can offer a resolution step, and procedural
// templates keep their pack name instead of a random one (identifiable in
// the editor; spawned copies are named from names_list at runtime anyway).
import { ALL_SKILLS } from '../schemas/worker.schema.js';
import {
  WM_SKILL_MAPPING, WM_TRAIT_MAPPING, TRAIT_REQUIREMENTS, WM_RACE_TRAITS,
} from './wm_mappings.js';

const MAX_NAME_LENGTH = 15;

const UNIQUE_STAT_ATTRS = [
  'Charisma', 'Intelligence', 'Agility', 'Strength', 'Constitution',
  'Beauty', 'Confidence', 'Obedience', 'Spirit', 'Libido', 'Mana',
];

const UNIQUE_SKILL_ATTRS = [
  'NormalSex', 'Anal', 'BDSM', 'OralSex', 'Group', 'Lesbian',
  'Combat', 'Magic', 'Service', 'Strip', 'Handjob', 'TittySex',
  'Footjob', 'Beastiality', 'Medicine', 'Performance', 'Crafting',
  'Farming', 'Cooking', 'Herbalism', 'Brewing', 'AnimalHandling', 'Card', 'Sport',
];

export function sanitizeFolderName(name) {
  return String(name || '')
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '_');
}

export function convertWMSkillValue(raw, scaleMax = 100) {
  if (scaleMax <= 0) return Math.min(100, Math.max(0, Math.trunc(raw)));
  return Math.min(100, Math.max(0, Math.round((raw * 100) / scaleMax)));
}

/** Parses one .girlsx / .rgirlsx XML string. Returns null when no <Girl>. */
export function parseWMGirlXML(xmlString, filename) {
  const doc = new DOMParser().parseFromString(xmlString, 'text/xml');
  const girl = doc.querySelector('Girl');
  if (!girl) return null;

  const isRandom = String(filename || '').toLowerCase().endsWith('.rgirlsx');
  const xmlName = girl.getAttribute('Name') || 'Unknown';
  const baseName = girl.getAttribute('FirstName') || xmlName;

  let preferredName = baseName;
  if (baseName.length > MAX_NAME_LENGTH) {
    const firstSpace = baseName.indexOf(' ');
    if (firstSpace > 0) preferredName = baseName.slice(0, firstSpace);
  }

  const data = {
    name: preferredName,
    xml_name: xmlName,
    description: girl.getAttribute('Desc') || '',
    is_random: isRandom,
    stats: {},
    skills: {},
    traits: [],
  };

  if (isRandom) {
    for (const stat of girl.querySelectorAll('Stat')) {
      data.stats[stat.getAttribute('Name')] = {
        min: parseInt(stat.getAttribute('Min') || '0', 10),
        max: parseInt(stat.getAttribute('Max') || '100', 10),
      };
    }
    for (const skill of girl.querySelectorAll('Skill')) {
      data.skills[skill.getAttribute('Name')] = {
        min: parseInt(skill.getAttribute('Min') || '0', 10),
        max: parseInt(skill.getAttribute('Max') || '100', 10),
      };
    }
    for (const trait of girl.querySelectorAll('Trait')) {
      data.traits.push({
        name: trait.getAttribute('Name'),
        percent: parseInt(trait.getAttribute('Percent') || '100', 10),
      });
    }
  } else {
    // Attribute names are matched case-insensitively and canonicalized:
    // real browsers preserve XML attribute case but happy-dom lowercases it,
    // and WM packs in the wild are not always consistent either.
    const statCanonical = new Map(UNIQUE_STAT_ATTRS.map((a) => [a.toLowerCase(), a]));
    const skillCanonical = new Map(UNIQUE_SKILL_ATTRS.map((a) => [a.toLowerCase(), a]));
    const meta = new Set(['name', 'firstname', 'desc', 'askprice']);
    for (const rawAttr of girl.getAttributeNames()) {
      const lc = rawAttr.toLowerCase();
      if (meta.has(lc)) continue;
      const n = parseInt(girl.getAttribute(rawAttr), 10);
      if (Number.isNaN(n)) continue;
      if (statCanonical.has(lc)) data.stats[statCanonical.get(lc)] = n;
      else data.skills[skillCanonical.get(lc) || rawAttr] = n;
    }
    const askPrice = girl.getAttribute('AskPrice') ?? girl.getAttribute('askprice');
    if (askPrice && !Number.isNaN(parseInt(askPrice, 10))) {
      data.ask_price = parseInt(askPrice, 10);
    }
    for (const trait of girl.querySelectorAll('Trait')) {
      data.traits.push(trait.getAttribute('Name'));
    }
  }
  return data;
}

function comfortFromAskPrice(askPrice) {
  if (!askPrice || askPrice <= 0) return 3;
  if (askPrice <= 200) return 1;
  if (askPrice <= 400) return 2;
  if (askPrice <= 600) return 3;
  if (askPrice <= 800) return 4;
  return 5;
}

function randInt(rng, min, max) {
  return min + Math.floor(rng() * (max - min + 1));
}

/**
 * Converts parsed WM data to an FM worker.
 * Returns { worker, unknownTraits, unknownSkills }.
 */
export function convertWMToFMWorker(wmData, {
  folderName,
  allSkills = ALL_SKILLS,
  skillScaleMax = 100,
  defaultCost = 1300,
  costRange = [1200, 1400],
  rng = Math.random,
  extraTraitMappings = {},
  extraSkillMappings = {},
} = {}) {
  const isRandom = !!wmData.is_random;
  const unknownTraits = [];
  const unknownSkills = [];

  const worker = {
    name: wmData.name || 'Unknown',
    folder: folderName,
    cost: isRandom ? randInt(rng, costRange[0], costRange[1]) : defaultCost,
    nsfw: true,
    unique: !isRandom,
    encounter_only: !isRandom,
    monster: false,
    procedural: isRandom,
    skills: {},
    names_list: isRandom ? 'western_female' : null,
    traits: ['Human'],
    description: wmData.description || '',
    gender: 'female',
    comfort_desired: comfortFromAskPrice(wmData.ask_price),
  };

  // Baseline like game unique workers: main skills 20-30, specialties 18-32.
  for (const skill of allSkills) {
    worker.skills[skill] = skill.startsWith('Specialty ')
      ? randInt(rng, 18, 32)
      : randInt(rng, 20, 30);
  }

  // Overwrite only skills WM actually specifies.
  const skillMap = { ...WM_SKILL_MAPPING, ...extraSkillMappings };
  for (const [wmSkill, value] of Object.entries(wmData.skills || {})) {
    let fmSkill = skillMap[wmSkill];
    if (!fmSkill) {
      fmSkill = allSkills.includes(wmSkill)
        ? wmSkill
        : wmSkill.charAt(0).toUpperCase() + wmSkill.slice(1);
    }
    if (!allSkills.includes(fmSkill)) {
      unknownSkills.push(wmSkill);
      continue;
    }
    const raw = typeof value === 'object' && value !== null
      ? Math.floor(((value.min || 0) + (value.max ?? 100)) / 2)
      : Math.trunc(value);
    worker.skills[fmSkill] = convertWMSkillValue(raw, skillScaleMax);
  }

  // Traits: requirements first, race traits replace Human, dedupe.
  const traitMap = { ...WM_TRAIT_MAPPING, ...extraTraitMappings };
  let traits = ['Human'];
  for (const t of wmData.traits || []) {
    const wmName = typeof t === 'object' && t !== null ? t.name : t;
    const fmTrait = traitMap[wmName];
    if (!fmTrait) {
      unknownTraits.push(wmName);
      continue;
    }
    if (traits.includes(fmTrait)) continue;
    const required = TRAIT_REQUIREMENTS[fmTrait];
    if (required && !traits.includes(required)) traits.push(required);
    if (WM_RACE_TRAITS.includes(fmTrait)) {
      traits = traits.filter((x) => x !== 'Human');
    }
    traits.push(fmTrait);
  }
  worker.traits = traits;

  return { worker, unknownTraits, unknownSkills };
}
