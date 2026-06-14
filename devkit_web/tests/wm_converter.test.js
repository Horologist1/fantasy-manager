// Whoremaster converter — parity tests against the v6 Python logic.
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';

beforeEach(() => {
  const w = new Window();
  globalThis.DOMParser = w.DOMParser;
});

const GIRL_XML = `<?xml version="1.0" encoding="UTF-8"?>
<Girls>
  <Girl Name="Seraphina Moonwhisper The Wise" FirstName="Seraphina Moonwhisper The Wise"
        Desc="An elven sorceress of great renown."
        Charisma="80" Intelligence="90" Libido="40" AskPrice="750"
        NormalSex="35" Magic="88" Performance="60" Combat="20" Unknownskill="50">
    <Trait Name="Elf"/>
    <Trait Name="Strong Magic"/>
    <Trait Name="Cool Person"/>
    <Trait Name="Mysterious Aura"/>
  </Girl>
</Girls>`;

const RGIRL_XML = `<?xml version="1.0" encoding="UTF-8"?>
<Girls>
  <Girl Name="Farm Girl" Desc="A random farm hand.">
    <Stat Name="Charisma" Min="30" Max="70"/>
    <Skill Name="Farming" Min="40" Max="80"/>
    <Skill Name="NormalSex" Min="10" Max="30"/>
    <Trait Name="Strong" Percent="60"/>
    <Trait Name="Big Boobs" Percent="100"/>
  </Girl>
</Girls>`;

const fixedRng = () => 0.5; // deterministic: randint(a,b) → midpoint

test('parses a .girlsx unique character', async () => {
  const { parseWMGirlXML } = await import('../src/converters/wm_xml_to_fm.js');
  const d = parseWMGirlXML(GIRL_XML, 'seraphina.girlsx');
  assert.equal(d.is_random, false);
  // name longer than 15 chars → cut at first space
  assert.equal(d.name, 'Seraphina');
  assert.equal(d.xml_name, 'Seraphina Moonwhisper The Wise');
  assert.equal(d.description, 'An elven sorceress of great renown.');
  assert.equal(d.ask_price, 750);
  assert.equal(d.skills.Magic, 88);
  assert.deepEqual(d.traits, ['Elf', 'Strong Magic', 'Cool Person', 'Mysterious Aura']);
});

test('parses a .rgirlsx random template with min/max ranges', async () => {
  const { parseWMGirlXML } = await import('../src/converters/wm_xml_to_fm.js');
  const d = parseWMGirlXML(RGIRL_XML, 'farm_girl.rgirlsx');
  assert.equal(d.is_random, true);
  assert.deepEqual(d.skills.Farming, { min: 40, max: 80 });
  assert.deepEqual(d.traits[0], { name: 'Strong', percent: 60 });
});

test('converts a unique girl: flags, comfort, skills, races, requirements', async () => {
  const { parseWMGirlXML, convertWMToFMWorker } = await import('../src/converters/wm_xml_to_fm.js');
  const d = parseWMGirlXML(GIRL_XML, 'seraphina.girlsx');
  const { worker, unknownTraits, unknownSkills } = convertWMToFMWorker(d, {
    folderName: 'seraphina', rng: fixedRng,
  });

  assert.equal(worker.unique, true);
  assert.equal(worker.encounter_only, true);
  assert.equal(worker.procedural, false);
  assert.equal(worker.nsfw, true);
  assert.equal(worker.gender, 'female');
  assert.equal(worker.cost, 1300);
  assert.equal(worker.comfort_desired, 4); // AskPrice 750 → bucket 4
  assert.equal(worker.names_list, null);

  // skills: WM 0-100 → FM 0-100 direct; Magic→Craft, Performance→Charm
  assert.equal(worker.skills.Craft, 88);
  assert.equal(worker.skills.Charm, 60);
  assert.equal(worker.skills.Sex, 35);
  assert.equal(worker.skills.Combat, 20);
  // baseline fills every canonical skill
  assert.equal(Object.keys(worker.skills).length, 25);

  // Elf replaces Human; Strong Magic pulls in Magical first; Cool Person → Charming
  assert.ok(!worker.traits.includes('Human'));
  assert.ok(worker.traits.includes('Elf'));
  const magicalIdx = worker.traits.indexOf('Magical');
  const strongMagicIdx = worker.traits.indexOf('Strong Magic');
  assert.ok(magicalIdx >= 0 && strongMagicIdx > magicalIdx, 'Magical inserted before Strong Magic');
  assert.ok(worker.traits.includes('Charming'));

  // unknowns reported, not silently dropped (attribute case may vary by parser)
  assert.deepEqual(unknownTraits, ['Mysterious Aura']);
  assert.equal(unknownSkills.length, 1);
  assert.equal(unknownSkills[0].toLowerCase(), 'unknownskill');
});

test('converts a random template to a procedural worker', async () => {
  const { parseWMGirlXML, convertWMToFMWorker } = await import('../src/converters/wm_xml_to_fm.js');
  const d = parseWMGirlXML(RGIRL_XML, 'farm_girl.rgirlsx');
  const { worker } = convertWMToFMWorker(d, { folderName: 'farm_girl', rng: fixedRng });

  assert.equal(worker.unique, false);
  assert.equal(worker.encounter_only, false);
  assert.equal(worker.procedural, true);
  assert.equal(worker.names_list, 'western_female');
  // rgirlsx skill = midpoint of min/max: Farming (40+80)/2=60 → Service
  assert.equal(worker.skills.Service, 60);
  assert.equal(worker.skills.Sex, 20); // (10+30)/2
  // traits: percent ignored at conversion (applied as fixed traits)
  assert.ok(worker.traits.includes('Strong'));
  assert.ok(worker.traits.includes('Large Breasts'));
  assert.ok(worker.traits.includes('Human')); // no race trait → Human stays
});

test('skill scale 70 rescales to 0-100', async () => {
  const { parseWMGirlXML, convertWMToFMWorker } = await import('../src/converters/wm_xml_to_fm.js');
  const d = parseWMGirlXML(GIRL_XML, 'x.girlsx');
  const { worker } = convertWMToFMWorker(d, {
    folderName: 'x', rng: fixedRng, skillScaleMax: 70,
  });
  assert.equal(worker.skills.Craft, 100); // 88/70 → clamped 100
  assert.equal(worker.skills.Combat, 29); // round(20*100/70)
});

test('extra trait mappings override and extend the defaults', async () => {
  const { parseWMGirlXML, convertWMToFMWorker } = await import('../src/converters/wm_xml_to_fm.js');
  const d = parseWMGirlXML(GIRL_XML, 'x.girlsx');
  const { worker, unknownTraits } = convertWMToFMWorker(d, {
    folderName: 'x', rng: fixedRng,
    extraTraitMappings: { 'Mysterious Aura': 'Exotic' },
  });
  assert.ok(worker.traits.includes('Exotic'));
  assert.deepEqual(unknownTraits, []);
});

test('sanitizeFolderName matches v6 behavior', async () => {
  const { sanitizeFolderName } = await import('../src/converters/wm_xml_to_fm.js');
  assert.equal(sanitizeFolderName('Seraphina Moonwhisper'), 'seraphina_moonwhisper');
  assert.equal(sanitizeFolderName("D'Arcy  von-Test!"), 'darcy_von-test');
});

// ---- image renaming ----

test('renameWMImageName applies patterns, lowercase, and cleanup', async () => {
  const { renameWMImageName } = await import('../src/converters/wm_image_rename.js');
  assert.equal(renameWMImageName('Portrait.png'), 'profile.png');
  assert.equal(renameWMImageName('PregSex (2).jpg'), 'pregnant_sex.jpg');
  assert.equal(renameWMImageName('Nude_3.JPG'), 'strip.jpg');
  assert.equal(renameWMImageName('Ecchi  Beach.png'), 'strip_beach.png');
  assert.equal(renameWMImageName('Magic.gif'), 'craft.gif');
  assert.equal(renameWMImageName('anal.png'), 'anal.png'); // already fine
});

test('planRenames suffixes collisions like v6', async () => {
  const { planRenames } = await import('../src/converters/wm_image_rename.js');
  const plan = planRenames(['Nude.png', 'Ecchi.png', 'Presented.png', 'notes.txt']);
  // all three map to strip.png → first wins, others get (1), (2)
  assert.deepEqual(plan, [
    { from: 'Nude.png', to: 'strip.png' },
    { from: 'Ecchi.png', to: 'strip (1).png' },
    { from: 'Presented.png', to: 'strip (2).png' },
  ]);
});
