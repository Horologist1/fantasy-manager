// Whoremaster → Fantasy Manager mapping tables, ported verbatim from
// devkit/fantasy_manager_editor_v6.py. Kept as plain data so the UI can let
// modders extend them (resolved mappings are merged in at runtime).

export const WM_SKILL_MAPPING = {
  NormalSex: 'Sex', OralSex: 'Oral', Lesbian: 'Homo', Handjob: 'Hand',
  TittySex: 'Special', Footjob: 'Special', Beastiality: 'Extreme',
  Strip: 'Striptease', Magic: 'Craft', Medicine: 'Clever',
  Performance: 'Charm', Crafting: 'Craft', Farming: 'Service',
  Cooking: 'Service', Herbalism: 'Craft', Brewing: 'Clever', AnimalHandling: 'Craft',
  Card: 'Clever', Sport: 'Agility',
  Anal: 'Anal', BDSM: 'BDSM', Group: 'Group', Service: 'Service', Combat: 'Combat',
};

export const WM_TRAIT_MAPPING = {
  'Nymphomaniac': 'Nymph-Touched', 'Chaste': 'Frigid Soul', 'Frigid': 'Frigid Soul',
  'High Sex Drive': 'Burning Desire', 'Slut': 'Insatiable', 'Big Boobs': 'Large Breasts',
  'Busty Boobs': 'Large Breasts', 'Small Boobs': 'Small Breasts', 'Flat Chest': 'Flat Chest',
  'Great Arse': 'Firm Ass', 'Plump Tush': 'Soft Ass', 'Not Human': 'Transformed',
  'Cat Girl': 'Transformed', 'Cow Girl': 'Transformed', 'Iron Will': 'Rebellious',
  'Broken Will': 'Obedient', 'Fearless': 'Confident', 'Deep Throat': 'Pierced',
  'Fast Orgasms': 'Sensitive', 'Slow Orgasms': 'Numb', 'Cute': 'Cute', 'Beautiful': 'Beautiful',
  'Charming': 'Charming', 'Charismatic': 'Charismatic', 'Elegant': 'Elegant', 'Agile': 'Agile',
  'Strong': 'Strong', 'Tough': 'Tough', 'Clumsy': 'Clumsy', 'Adventurer': 'Adventurer',
  'Maid': 'Maid', 'Singer': 'Singer', 'Teacher': 'Teacher', 'Waitress': 'Waitress',
  'Elf': 'Elf', 'Dwarf': 'Dwarf', 'Demon': 'Demon', 'Angel': 'Angel',
  'Vampire': 'Vampire', 'Orc': 'Orc', 'Goblin': 'Goblin',
  'Quick Learner': 'Quick Learner', 'Dependant': 'Dependant', 'Optimist': 'Optimist',
  'Open Minded': 'Open Minded', 'Cool Scars': 'Cool Scars', 'Nervous': 'Nervous',
  'Sadistic': 'Sadistic', 'Exotic': 'Exotic', 'Flexible': 'Flexible', 'Brawler': 'Brawler',
  'Tomboy': 'Tomboy', 'Tattooed': 'Tattooed', 'Pessimist': 'Pessimist',
  'Cool Person': 'Charming',
  // v6 declared TRAIT_REQUIREMENTS for these but never mapped them, making
  // that code unreachable; the game ships all three traits, so map them.
  'Strong Magic': 'Strong Magic',
  'Powerful Magic': 'Powerful Magic',
  'Psychic': 'Psychic',
  'Small Scars': 'Cool Scars',
  'Heavily Tattooed': 'Tattooed',
  'Horrific Scars': 'Scarred',
  'Retarded': 'Dumb',
  'Mind Fucked': 'Crazy',
};

// Traits that only work when the worker also has a prerequisite trait.
export const TRAIT_REQUIREMENTS = {
  'Strong Magic': 'Magical',
  'Powerful Magic': 'Magical',
  'Psychic': 'Magical',
};

// Race traits replace the default "Human" when mapped.
export const WM_RACE_TRAITS = [
  'Elf', 'Dwarf', 'Demon', 'Angel', 'Vampire', 'Orc', 'Goblin', 'Transformed',
];

// Image rename patterns [regexSource, replacement] — applied in order,
// case-insensitive, on the basename without extension.
export const WM_IMAGE_RENAME_PATTERNS = [
  ['^Portrait', 'profile'],
  ['^Preg(Sex|Anal|Oral|Group|BDSM|Hand|Strip|Special|Extreme|Combat|Service|Charm|Craft|Striptease|Homo)', 'pregnant_$1'],
  ['^Preg(Les|Gay)', 'pregnant_$1'],
  ['^PregNude', 'pregnant_strip'],
  ['^PregBeast', 'pregnant_extreme'],
  ['^PregProfile', 'pregnant_profile'],
  ['^Preg\\b', 'pregnant_profile'],
  ['^Preggo(Sex|Anal|Oral|Group|BDSM|Hand|Strip|Special|Extreme|Combat|Service|Charm|Craft|Striptease|Homo)', 'pregnant_$1'],
  ['^Preggo(Les|Gay)', 'pregnant_$1'],
  ['^PreggoProfile', 'pregnant_profile'],
  ['^Preggo\\b', 'pregnant_profile'],
  ['^Foot\\b', 'hand'],
  ['^Footjob\\b', 'hand'],
  ['^Dildo\\b', 'special'],
  ['^Mast\\b', 'special'],
  ['^Escort\\b', 'charm'],
  ['^Formal\\b', 'charm'],
  ['^Swim\\b', 'rest'],
  ['^Bath\\b', 'rest'],
  ['^Nurse\\b', 'service'],
  ['^Ecchi\\b', 'strip'],
  ['^Presented\\b', 'strip'],
  ['^Nude\\b', 'strip'],
  ['^Bunny\\b', 'charm'],
  ['^Dancer\\b', 'charm'],
  ['^Sing\\b', 'charm'],
  ['^Dom\\b', 'bdsm'],
  ['^Torture\\b', 'bdsm'],
  ['^Lick\\b', 'oral'],
  ['^Jail\\b', 'combat_failure'],
  ['^Refuse\\b', 'charm_failure'],
  ['^Bed\\b', 'rest'],
  ['^Magic\\b', 'craft'],
  ['^Fight\\b', 'combat'],
  ['^Shop\\b', 'service'],
  ['^Death\\b', 'combat_failure'],
  ['^Cook\\b', 'service'],
  ['^Blacksmith\\b', 'craft'],
  ['^Card\\b', 'charm'],
  ['^Dance\\b', 'charm'],
  ['^Doctor\\b', 'service'],
  ['^Farm\\b', 'service'],
  ['^Eatout\\b', 'oral'],
  ['^Deepthroat\\b', 'oral'],
  ['^Futa\\b', 'futa_sex'],
  ['^Sub\\b', 'bdsm'],
  ['^Study\\b', 'clever'],
  ['^Work1\\b', 'service'],
  ['^Maid3\\b', 'service'],
  ['^Matron3\\b', 'service'],
];

export const WM_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.webm', '.mp4'];
