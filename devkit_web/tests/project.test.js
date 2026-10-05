import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createProject, restoreProject, identityFor } from '../src/lib/project.js';
import { createMemoryFS, createFSAFS } from '../src/lib/fs.js';
import { workerIdentity, parseJSON, supportsOverride, categoryFor, conditionError } from '../src/lib/contract.js';
import { catalogsFromFiles, referenceMetadata } from '../src/lib/reference.js';
import { unique_worker_recipe } from '../src/recipes/unique_worker.js';
import { worker_specific_event_recipe } from '../src/recipes/events.js';
import { daily_story_basic_recipe } from '../src/recipes/daily_stories.js';
import { GUIDE_SECTIONS } from '../src/user_guide.js';
import { TYPES } from '../src/lib/content_types.js';

const GAME_ROOT = process.env.FM_GAME_ROOT || path.resolve(import.meta.dirname, '../..');
const read = async name => JSON.parse(await fs.readFile(new URL('../src/catalogs/'+name+'.json', import.meta.url), 'utf8'));
const reference = {files:await read('base_files'), meta:await read('_meta'), names_lists:await read('names_lists')};
const png = new Uint8Array(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jO1sAAAAASUVORK5CYII=', 'base64'));
const worker = () => unique_worker_recipe.build({name:'Audit Worker', folder:'audit_worker', gender:'female', race:'Human', nsfw:false, skill_focus:'balanced'});
const workerPath = 'data/workers/workers_audit.json';
const imagePath = 'images/workers/audit_worker/profile.png';

function fakeDisk(text, error) {
  let writes = 0;
  const creates = [];
  const root = {
    async getDirectoryHandle(name, options) { creates.push(options?.create); return root; },
    async getFileHandle() { if (error) throw error; return {
      async getFile() { return {text:async()=>text}; },
      async createWritable() { return {write:async()=>writes++,close:async()=>{}}; },
    }; },
  };
  return {fs:createFSAFS(root), writes:()=>writes, creates};
}

test('failed or invalid existing reads cannot trigger a write or create directories', async () => {
  for (const source of [fakeDisk('[{"name":"Old"},'), fakeDisk('null'), fakeDisk('{}', Object.assign(new Error('denied'), {name:'NotAllowedError'}))]) {
    await assert.rejects(source.fs.mergeAndWrite('workers/a.json', {name:'New'}, {key:'name'}));
    assert.equal(source.writes(),0); assert.ok(source.creates.every(v=>v===false));
  }
});
test('only a NotFoundError is treated as a missing file', async () => {
  const source = fakeDisk('', Object.assign(new Error('missing'), {name:'NotFoundError'}));
  assert.equal(await source.fs.readJSON('workers/a.json'), null);
});
test('invalid wrappers and missing identities leave their data intact', async () => {
  const initial = {'a.json':{items:'broken', keep:42}, 'b.json':[{}]};
  const memory = createMemoryFS(initial);
  await assert.rejects(memory.mergeAndWrite('a.json',{id:'new'},{key:'id',wrapper:'items'}));
  await assert.rejects(memory.mergeAndWrite('b.json',{name:'new'},{key:'name'}));
  assert.deepEqual(await memory.readJSON('a.json'),initial['a.json']);
  assert.deepEqual(await memory.readJSON('b.json'),initial['b.json']);
});
test('distinct nameless templates are preserved; renames cannot overwrite another identity', async () => {
  const memory = createMemoryFS();
  const goblin={procedural_template:true,template_id:'goblin'}, orc={procedural_template:true,template_id:'orc'};
  await memory.mergeAndWrite('a.json',goblin,{key:workerIdentity});
  await memory.mergeAndWrite('a.json',orc,{key:workerIdentity});
  await assert.rejects(memory.mergeAndWrite('a.json',orc,{key:workerIdentity,originalKey:workerIdentity(goblin)}));
  assert.deepEqual(await memory.readJSON('a.json'),[goblin,orc]);
});
test('JSON parsing rejects duplicate escaped keys and non-finite numbers, preserving ordinary strings', () => {
  for (const text of ['{"a":1,"a":2}', '{"a":1,"\\u0061":2}', '{"a":1e400}']) assert.throws(()=>parseJSON(text));
  assert.deepEqual(parseJSON('{"a":{"a":"x:{\\\"a\\\":1}"},"b":2}'),{a:{a:'x:{"a":1}'},b:2});
});
test('editing one ingredient preserves the whole file, root metadata, other entries and base reference', async () => {
  const name='data/items/alchemy_ingredients.json';
  const custom=structuredClone(reference);
  custom.files[name].future_root={keep:true};
  custom.files[name].items[0].future_item={keep:true};
  const before=structuredClone(custom.files[name]);
  const p=createProject(custom,{mode:'override'});
  const edited={...before.items[0],price:240};
  await p.stage('items',edited,name,{originalKey:edited.id});
  assert.deepEqual(p.files[name],{...before,items:[edited,...before.items.slice(1)]});
  assert.deepEqual(custom.files[name],before);
  assert.deepEqual(p.validate().errors,[]);
});
test('rating variants remain independently editable', async () => {
  const name='data/workers/kar.json', source=reference.files[name];
  const p=createProject(reference,{mode:'override'});
  const edited={...source[1],cost:123};
  await p.stage('workers',edited,name,{originalKey:workerIdentity(source[1])});
  assert.deepEqual(p.files[name],[source[0],edited]);
  assert.deepEqual(p.validate().errors,[]);
});
test('override rating validation matches the game even when the general schema accepts null', () => {
  const p=createProject(reference,{mode:'override',files:{'data/workers/kar.json':[{...reference.files['data/workers/kar.json'][0],nsfw:null}]}});
  assert.match(p.validate().errors.join('\n'),/nsfw must be true or false/);
  assert.throws(()=>p.exportPack());
});
test('renaming a draft entry replaces its original identity rather than appending a copy', async () => {
  const p=createProject(reference); const initial=worker();
  await p.stage('workers',initial,workerPath);
  await p.stage('workers',{...initial,name:'Renamed'},workerPath,{originalKey:workerIdentity(initial)});
  assert.equal(p.files[workerPath].length,1); assert.equal(p.files[workerPath][0].name,'Renamed');
});
test('failed multi-entry staging is atomic', async () => {
  const p=createProject(reference); await p.stage('workers',worker(),workerPath);
  const before=p.files;
  await assert.rejects(p.stage('workers',[{...worker(),name:'First new'},worker()],workerPath));
  assert.deepEqual(p.files,before);
});
test('override targets are existing JSON paths and cannot import images or scripts', async () => {
  const p=createProject(reference,{mode:'override'});
  for (const path of ['data/items/items_new.json','data/interactions/a.json','../game/file.json','data/items/../x.json']) await assert.rejects(p.stage('items',{id:'x'},path));
  assert.throws(()=>p.addImage(imagePath,png));
  assert.deepEqual(p.files,{});
});
test('character mode rejects other categories and blocks procedural/unsupported worker exports', async () => {
  const p=createProject(reference);
  await assert.rejects(p.stage('items',{id:'x'},'data/items/new.json'),/override or manual/);
  assert.throws(()=>p.importJSON('data/buildings/new.json',{building_types:[]}),/override or manual/);
  assert.throws(()=>p.importJSON('data/interactions/new.json',[]),/override or manual/);
  assert.throws(()=>p.importJSON('data/monthly_conditions/cards.json',[]),/override or manual/);
  await p.stage('workers',{...worker(),procedural:true},workerPath);
  p.addImage(imagePath,png);
  assert.match(p.validate().errors.join('\n'),/regular characters only/);
  assert.throws(()=>p.exportPack());
});
test('a missing image folder, portrait or invalid skill blocks export', async () => {
  const p=createProject(reference); const data=worker(); delete data.folder;
  await p.stage('workers',data,workerPath);
  assert.match(p.validate().errors.join('\n'),/image folder/);
  await p.stage('workers',{...worker(),skills:{Combat:101}},workerPath,{originalKey:workerIdentity(data)});
  assert.match(p.validate().errors.join('\n'),/skills must|profile/);
  assert.throws(()=>p.exportPack());
});
test('draft round-trip preserves images and rejects incompatible references, unsafe paths and duplicate image names', async () => {
  const p=createProject(reference); await p.stage('workers',worker(),workerPath); p.addImage(imagePath,png);
  const draft=p.serialize(), restored=restoreProject(reference,JSON.parse(JSON.stringify(draft)));
  assert.deepEqual(restored.serialize(),draft);
  assert.deepEqual(restored.exportPack().bytes,p.exportPack().bytes);
  assert.throws(()=>restoreProject({...reference,meta:{...reference.meta,data_revision:'other'}},draft));
  assert.throws(()=>restoreProject(reference,{...draft,files:{'../oops.json':[]}}));
  assert.throws(()=>restoreProject(reference,{...draft,images:[...draft.images,...draft.images]}));
});
test('new project entries refresh cross references and nested event flags immediately', async () => {
  const p=createProject(reference,{mode:'manual'});
  const trait={name:'Audit Trait',nsfw:false};
  await p.stage('traits',trait,'data/traits/audit.json');
  assert.ok(p.catalogs().all_traits.has('Audit Trait'));
  await p.stage('workers',{...worker(),traits:['Human','Audit Trait']},workerPath);
  assert.ok(!p.validate().errors.some(e=>e.includes('trait')));
  const catalogs=catalogsFromFiles({'data/events/recruit/a.json':[{id:'r',required_flags:{test_recruit:true}}], 'data/buildings/daily_story_extensions/a.json':{daily_story_extensions:[{event_flags:{test_daily:true}}]}});
  assert.ok(catalogs.all_event_flags.has('test_recruit')); assert.ok(catalogs.all_event_flags.has('test_daily'));
});
test('bundled reference fingerprint matches all current authored game files and version', async () => {
  const actual=[];
  async function visit(dir,prefix) {
    for(const entry of await fs.readdir(dir,{withFileTypes:true})) {
      const rel=prefix+'/'+entry.name;
      if(entry.isDirectory())await visit(path.join(dir,entry.name),rel);
      else if(categoryFor(rel))actual.push(rel);
    }
  }
  await visit(path.join(GAME_ROOT,'game/data'),'data');
  assert.deepEqual(Object.keys(reference.files).sort(),actual.sort());
  const computed=await referenceMetadata(reference.files,reference.meta.game_version);
  assert.equal(computed.data_revision,reference.meta.data_revision);
  for (const [relative,data] of Object.entries(reference.files)) assert.deepEqual(JSON.parse(await fs.readFile(path.join(GAME_ROOT,'game',relative),'utf8')),data,relative);
  const ingredients=reference.files['data/items/alchemy_ingredients.json'].items;
  assert.equal(ingredients.length,6);
});
test('exported ZIPs pass real game inspection, installation and mounted-content integrity checks', async () => {
  const base=path.resolve(os.tmpdir()); const temporary=await fs.mkdtemp(path.join(base,'fm-devkit-test-'));
  assert.ok(path.resolve(temporary).startsWith(base+path.sep));
  try {
    const character=createProject(reference); await character.stage('workers',worker(),workerPath); character.addImage(imagePath,png);
    const override=createProject(reference,{mode:'override',files:Object.fromEntries(Object.entries(reference.files).filter(([p])=>supportsOverride(p)))});
    assert.deepEqual(override.validate().errors,[]);
    const content=await contentPack(); const contentOnly=await contentPack(false);
    for (const [mode,p,label] of [['characters',character,'worker'],['override',override,'override'],['characters',content,'content'],['characters',contentOnly,'content-only']]) {
      const pack=p.exportPack(), file=path.join(temporary,label+'_'+pack.filename); await fs.writeFile(file,pack.bytes);
      const result=JSON.parse(execFileSync(process.env.PYTHON || 'python',[path.resolve(import.meta.dirname,'../scripts/verify_export.py'),file,'--mode',mode,'--game-root',GAME_ROOT],{encoding:'utf8'}));
      assert.equal(result.accepted,true,label); assert.equal(result.installed,'installed',label);
      if (label==='worker') { assert.equal(result.workers,1); assert.equal(result.images,1); assert.deepEqual(result.warnings,[]); }
      else if (label==='override') assert.equal(result.files,Object.keys(override.files).length);
      else {
        assert.equal(result.workers,label==='content' ? 1 : 0,label); assert.deepEqual(result.warnings,[],label);
        assert.deepEqual(result.content,{traits:1,events:2,recruit:1,stories:1},label);
        assert.ok(result.content_paths.length>=4,label+': '+JSON.stringify(result.content_paths));
      }
    }
  } finally { await fs.rm(temporary,{recursive:true,force:true}); }
});

// Minimal reader for the devkit's stored (uncompressed) ZIP entries.
function unzip(bytes) {
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength), out={};
  for (let at=0; view.getUint32(at,true)===0x04034b50;) {
    const size=view.getUint32(at+18,true), nameLength=view.getUint16(at+26,true), extra=view.getUint16(at+28,true);
    const name=new TextDecoder().decode(bytes.subarray(at+30,at+30+nameLength));
    out[name]=bytes.subarray(at+30+nameLength+extra,at+30+nameLength+extra+size); at+=30+nameLength+extra+size;
  }
  return out;
}
const text=bytes=>new TextDecoder().decode(bytes);
const packEvent=(id='audit_pack_gift')=>worker_specific_event_recipe.build({worker_name:'Audit Worker',id,description:'Audit visits.',message:'Done.',one_time:true});
// Recipes leave unused conditions as null; the importer contract checks strings.
const withoutNullConditions=event=>({...event,conditions:Object.fromEntries(Object.entries(event.conditions).filter(([,v])=>v!==null))});
const story=(id='audit_pack_song')=>daily_story_basic_recipe.build({building:'tavern',profession:'bartender',id,report:'Sang a song',skill:'Service',desc_failure:'a',desc_mediocre:'b',desc_success:'c',desc_critical:'d'});
const recruit=id=>({id,description:'A wanderer asks for work.',weight:5,unlimited:true,random_worker:true,always_available:true,nsfw:false,worker_name:null,worker_filter:{},choices:[{option:'Hire',message:'Hired.',effect:{recruit_worker:true}}]});
async function contentPack(withWorker=true) {
  const p=createProject(reference,{name:withWorker ? 'Audit Content' : 'Audit Events Only'});
  if (withWorker) { await p.stage('workers',worker(),workerPath); p.addImage(imagePath,png); }
  const first=withWorker ? packEvent() : {...packEvent(),worker_name:'Aelis',conditions:{start_when:'has_worker:Aelis'}};
  const second={...packEvent('audit_pack_followup'),required_flags:{audit_pack_gift_done:true},conditions:{start_when:withWorker ? 'has_worker:Audit Worker AND money >= 100' : 'has_flag:audit_pack_gift_done'}};
  if (!withWorker) second.worker_name='Aelis';
  await p.stage('events',[withoutNullConditions(first),withoutNullConditions(second)],'data/events/audit_pack.json');
  await p.stage('traits',{name:'Audit Pack Trait',nsfw:false},'data/traits/audit_pack.json');
  await p.stage('recruit_events',recruit('event_recruit_audit_pack'),'data/events/recruit/audit_pack.json');
  await p.stage('daily_stories',story(),'data/buildings/daily_story_extensions/audit_pack.json');
  return p;
}
test('character and manual ZIPs put files under game/ with a README; overrides keep data/ paths and warn against drag & drop', async () => {
  const character=createProject(reference,{name:'Audit Pack'}); await character.stage('workers',worker(),workerPath); character.addImage(imagePath,png);
  const files=unzip(character.exportPack().bytes);
  assert.deepEqual(Object.keys(files).sort(),['README.txt','game/'+workerPath,'game/'+imagePath]);
  const readme=text(files['README.txt']);
  for (const part of [/^Audit Pack\r\n/,/Workers: 1 \(Audit Worker\)/,/Mods > Install mods/,/Drag the "game" folder/,/never replaces original game files/,/Do not use both methods at once/,/UNINSTALL/,/Uninstall/,new RegExp('  game/'+workerPath),new RegExp('  game/'+imagePath)]) assert.match(readme,part);
  const manual=createProject(reference,{mode:'manual'}); await manual.stage('traits',{name:'Audit Trait',nsfw:false},'data/traits/audit.json');
  const manualFiles=unzip(manual.exportPack().bytes);
  assert.deepEqual(Object.keys(manualFiles).sort(),['README.txt','game/data/traits/audit.json']);
  assert.match(text(manualFiles['README.txt']),/REPLACE/);
  const name='data/items/alchemy_ingredients.json';
  const override=createProject(reference,{mode:'override'}); await override.stage('items',{...reference.files[name].items[0],price:240},name,{originalKey:reference.files[name].items[0].id});
  const overrideFiles=unzip(override.exportPack().bytes);
  assert.deepEqual(Object.keys(overrideFiles).sort(),['README.txt',name]);
  assert.match(text(overrideFiles['README.txt']),/Import as JSON override/); assert.match(text(overrideFiles['README.txt']),/NEVER drag & drop/);
});
test('character packs accept new traits, events, recruitment events and daily stories, and content-only packs', async () => {
  const p=await contentPack();
  assert.deepEqual(p.validate().errors,[]);
  assert.ok(p.catalogs().all_traits.has('Audit Pack Trait'));
  const extension=p.files['data/buildings/daily_story_extensions/audit_pack.json'].daily_story_extensions[0];
  assert.equal(extension.merge_mode,'append');
  const files=unzip(p.exportPack().bytes);
  for (const name of ['data/events/audit_pack.json','data/traits/audit_pack.json','data/events/recruit/audit_pack.json','data/buildings/daily_story_extensions/audit_pack.json']) assert.ok(files['game/'+name],name);
  const readme=text(files['README.txt']);
  for (const part of [/Traits: 1/,/Events: 2/,/Recruitment events: 1/,/Daily stories: 1/]) assert.match(readme,part);
  const only=await contentPack(false);
  assert.deepEqual(only.validate().errors,[]);
  assert.ok(!Object.keys(unzip(only.exportPack().bytes)).some(n=>n.includes('data/workers')));
  const empty=createProject(reference);
  assert.match(empty.validate().errors.join('\n'),/Add at least one JSON file/);
});
test('character pack daily stories always append; a missing merge_mode is written as append on export', async () => {
  const group={building_id:'tavern',profession_id:'bartender',daily_stories:[story().story]};
  const p=createProject(reference,{files:{'data/buildings/daily_story_extensions/audit.json':{daily_story_extensions:[group]}}});
  assert.deepEqual(p.validate().errors,[]);
  const files=unzip(p.exportPack().bytes);
  assert.equal(JSON.parse(text(files['game/data/buildings/daily_story_extensions/audit.json'])).daily_story_extensions[0].merge_mode,'append');
  for (const mode of ['upsert','replace_all']) {
    const bad=createProject(reference,{files:{'data/buildings/daily_story_extensions/audit.json':[{...group,merge_mode:mode}]}});
    assert.match(bad.validate().errors.join('\n'),/merge_mode "append"/); assert.throws(()=>bad.exportPack());
  }
  const unknown=createProject(reference,{files:{'data/buildings/daily_story_extensions/audit.json':[{...group,building_id:'nowhere'}]}});
  assert.match(unknown.validate().errors.join('\n'),/unknown building/);
  const job=createProject(reference,{files:{'data/buildings/daily_story_extensions/audit.json':[{...group,profession_id:'nobody'}]}});
  assert.match(job.validate().errors.join('\n'),/unknown profession/);
});
test('character pack content must use new, unique identifiers and new file names', async () => {
  const baseStory=reference.files['data/buildings/building_types.json'].building_types.find(b=>b.id==='tavern').professions.find(j=>j.id==='bartender').daily_stories[0].id;
  const cases=[
    [{'data/traits/a.json':[{name:'Human'}]},/trait Human already exists in the game/],
    [{'data/traits/a.json':[{name:'Twice'}],'data/traits/b.json':{traits:[{name:'Twice'}]}},/used more than once/],
    [{'data/traits/a.json':[{nsfw:false}]},/missing its identifier/],
    [{'data/events/a.json':[{...withoutNullConditions(packEvent('knights_honor_duel')),worker_name:'Aelis'}]},/knights_honor_duel already exists/],
    [{'data/events/a.json':[{...withoutNullConditions(packEvent('event_recruit_audit')),worker_name:'Aelis'}]},/must not start with event_recruit_/],
    [{'data/events/recruit/a.json':[recruit('event_recruit_oak')]},/event_recruit_oak already exists/],
    [{'data/events/a.json':[{...withoutNullConditions(packEvent('same_id')),worker_name:'Aelis'}],'data/events/recruit/a.json':[recruit('same_id')]},/same_id is used more than once/],
    [{'data/buildings/daily_story_extensions/a.json':[{building_id:'tavern',profession_id:'bartender',daily_stories:[{...story().story,id:baseStory}]}]},/already exists in the game/],
    [{'data/buildings/daily_story_extensions/a.json':[{building_id:'tavern',profession_id:'bartender',daily_stories:[story().story]},{building_id:'tavern',profession_id:'entertainer',daily_stories:[story().story]}]},/used more than once/],
  ];
  for (const [files,pattern] of cases) assert.match(createProject(reference,{files}).validate().errors.join('\n'),pattern,JSON.stringify(Object.keys(files)));
  assert.throws(()=>createProject(reference,{files:{'data/traits/traits_core.json':[{name:'New one'}]}}),/already exists in the game/);
});
test('character pack conditions and event flags only use data the game does not evaluate as code', async () => {
  const allowed=['True','False','has_flag:a AND not_has_worker:Aelis','after_days_from_flag:x_at,5 OR exact_date:7,1','has_folder_worker:aelis','store.current_objective >= 7','money >= 50000','flag_value:x,1',"name == 'Aelis'",'gold != -1.5 AND x < None'];
  for (const start_when of allowed) assert.equal(conditionError(start_when),null,start_when);
  const rejected=['__import__("os")','money >= len(x)','store.__class__ == 1','store.x == [1]','open("x")','unknown_prefix:x','money >= other','','has_flag:a AND (b)'];
  for (const start_when of rejected) assert.ok(conditionError(start_when),start_when);
  const event=extra=>({...withoutNullConditions(packEvent('audit_safety')),worker_name:'Aelis',...extra});
  const errorsFor=value=>createProject(reference,{files:{'data/events/a.json':[value]}}).validate().errors.join('\n');
  assert.equal(errorsFor(event({conditions:{start_when:'has_worker:Aelis'}})),'');
  assert.match(errorsFor(event({conditions:{start_when:'store.x.__class__ == 1'}})),/unsupported condition/);
  assert.match(errorsFor(event({choices:[{option:'a',message:'b',effect:{event_flags:{when:'[random.randint(1, 9)]'}}}]})),/\[code\] value/);
  assert.match(errorsFor(event({choices:[{option:'a',message:'b',effect:{event_flags:{when:'[calculate_total_days() + 1]'}}}]})),/\[code\] value/);
  // The day stamp is the one allowed [code] value: it starts delayed chains.
  assert.equal(errorsFor(event({conditions:{start_when:'after_days_from_flag:audit_met_at,3'},choices:[{option:'a',message:'b',effect:{event_flags:{audit_met_at:'[calculate_total_days()]'}}}]})),'');
  assert.match(errorsFor(event({nested:{deeper:[{stop_when:'exec("x")'}]}})),/stop_when: unsupported condition/);
  const flagged={building_id:'tavern',profession_id:'bartender',daily_stories:[{...story('audit_flag_story').story,event_flags:{t:' [x] '}}]};
  assert.match(createProject(reference,{files:{'data/buildings/daily_story_extensions/a.json':[flagged]}}).validate().errors.join('\n'),/\[code\] value/);
  // Manual projects keep their existing behaviour.
  assert.ok(!createProject(reference,{mode:'manual',files:{'data/events/a.json':[event({conditions:{start_when:'money >= len(x)'}})]}}).validate().errors.some(e=>e.includes('unsupported condition')));
});
test('the guide’s pack-worker event example is a valid character pack', async () => {
  const section=GUIDE_SECTIONS.find(s=>s.title.startsWith('Adding events, traits and daily stories'));
  assert.ok(section?.code); assert.match(section.paragraphs.join(' '),/\[calculate_total_days\(\)\]/);
  assert.equal(GUIDE_SECTIONS[0].title,'Quick guide: a character pack in 5 steps'); assert.equal(GUIDE_SECTIONS[0].steps.length,5);
  const p=createProject(reference);
  await p.stage('workers',unique_worker_recipe.build({name:'Mira Storm',folder:'mira_storm',gender:'female',race:'Human',nsfw:false,skill_focus:'balanced'}),'data/workers/mira.json');
  p.addImage('images/workers/mira_storm/profile.png',png);
  p.importJSON('data/events/events_mira.json',parseJSON(section.code));
  assert.deepEqual(p.validate().errors,[]);
});
