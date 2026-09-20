import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {monthly_card_schema} from '../src/schemas/monthly_card.schema.js';
import {monthly_card_editor_sections} from '../src/schemas/monthly_card.schema.js';
import {runEditor} from '../src/editors/_engine.js';
import {Window} from 'happy-dom';
import {monthly_card_recipe} from '../src/recipes/monthly_cards.js';
import {validateEntry} from '../src/lib/validator.js';
import {createProject, restoreProject} from '../src/lib/project.js';
import {categoryFor, supportsOverride} from '../src/lib/contract.js';
import {catalogsFromFiles} from '../src/lib/reference.js';
const read = async name => JSON.parse(await fs.readFile(new URL('../src/catalogs/'+name+'.json',import.meta.url),'utf8'));
const reference = {files:await read('base_files'),meta:await read('_meta')};
const path = 'data/monthly_conditions/cards.json';
const card = () => ({id:'test_card',name:'Trade fair',description:'Visitors fill the tavern.',weight:2,effects:[{type:'earnings',value:1.1,buildings:['tavern']}]});
const ctx = {catalogs:catalogsFromFiles(reference.files)};
test('all shipped monthly cards match the runtime authoring contract', () => {
  assert.ok(reference.files[path]?.length);
  for (const row of reference.files[path]) assert.deepEqual(validateEntry(row,monthly_card_schema,ctx).errors,[],row.id);
});
test('only the actual monthly catalog path is accepted', () => {
  assert.equal(categoryFor(path),'monthly_conditions');
  assert.equal(supportsOverride(path),true);
  assert.equal(categoryFor('data/monthly_conditions/custom.json'),null);
});
test('monthly validation rejects invalid scopes, bounds and neutral effects', () => {
  const invalid = [
    {...card(),id:' '}, {...card(),description:'x'.repeat(501)}, {...card(),weight:null},
    {...card(),effects:null}, {...card(),nsfw:null}, {...card(),image:'../bad.png'},
    {...card(),id:'quiet_month'}, {...card(),effects:Array(4).fill(card().effects[0])},
    {...card(),effects:[{type:'earnings',value:1.16,buildings:['tavern']}]},
    {...card(),effects:[{type:'skill',value:11,skills:['Service'],buildings:['tavern']}]},
    {...card(),effects:[{type:'skill',value:5,buildings:['tavern']}]},
    {...card(),effects:[{type:'earnings',value:1.1}]},
    {...card(),effects:[{type:'earnings',value:1.1,buildings:['missing']}]},
    {...card(),effects:[{type:'earnings',value:1.1,buildings:['tavern'],skills:['Service']}]},
  ];
  for (const row of invalid) assert.ok(validateEntry(row,monthly_card_schema,ctx).errors.length,JSON.stringify(row));
});
test('adding and editing cards preserves existing content and exports the complete catalog', async () => {
  const project = createProject(reference,{mode:'override'});
  const original = structuredClone(reference.files[path]);
  await project.stage('monthly_conditions',card(),path);
  assert.deepEqual(project.files[path].slice(0,-1),original);
  await project.stage('monthly_conditions',{...card(),name:'Revised'},path,{originalKey:'test_card'});
  assert.equal(project.files[path].length,original.length+1);
  assert.deepEqual(reference.files[path],original);
  assert.deepEqual(project.validate().errors,[]);
  assert.ok(project.exportPack().bytes.length);
  const copy = restoreProject(reference,project.serialize());
  assert.deepEqual(copy.files,project.files);
  await assert.rejects(project.stage('monthly_conditions',card(),path));
});
test('card assistant creates a valid editable card', () => {
  assert.deepEqual(validateEntry(monthly_card_recipe.build({id:'new',name:'New',description:'A quiet interlude.'}),monthly_card_schema,ctx).errors,[]);
});
test('monthly editor renders its fields and preserves an existing card', () => {
  const w=new Window();
  globalThis.document=w.document; globalThis.HTMLElement=w.HTMLElement; globalThis.Event=w.Event;
  const container=document.createElement('div');
  const entry=structuredClone(reference.files[path][1]);
  const before=structuredClone(entry);
  runEditor({sections:monthly_card_editor_sections,entry,schema:monthly_card_schema,container,ctx,
    defaultFilename:path,validate:e=>validateEntry(e,monthly_card_schema,ctx),onSave:()=>{}});
  assert.ok(container.querySelector('.editor-section'));
  assert.ok(container.textContent.includes('Effects'));
  assert.deepEqual(entry,before);
  assert.deepEqual(new Set(monthly_card_editor_sections.flatMap(s=>s.fields.map(f=>f.id))),new Set(Object.keys(monthly_card_schema.fields)));
});
