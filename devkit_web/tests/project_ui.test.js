import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { Window } from 'happy-dom';
import { startDevkit } from '../src/project_app.js';
import { createProject } from '../src/lib/project.js';
import { unique_worker_recipe } from '../src/recipes/unique_worker.js';

const read=async name=>JSON.parse(await fs.readFile(new URL('../src/catalogs/'+name+'.json',import.meta.url),'utf8'));
const bundled={base_files:await read('base_files'),_meta:await read('_meta'),names_lists:await read('names_lists'),image_folders:await read('image_folders')};
const reference={files:bundled.base_files,meta:bundled._meta,names_lists:bundled.names_lists};
const png=new Uint8Array(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jO1sAAAAASUVORK5CYII=','base64'));
let w, downloads, originalURL;
beforeEach(async()=>{
  w=new Window();
  w.document.body.innerHTML=(await fs.readFile(new URL('../src/index.html',import.meta.url),'utf8')).match(/<body>([\s\S]*?)<script/)[1];
  globalThis.window=w; globalThis.document=w.document; globalThis.HTMLElement=w.HTMLElement; globalThis.Event=w.Event;
  w.__FM_BUNDLED_CATALOGS=structuredClone(bundled); w.confirm=()=>true;
  downloads=[]; originalURL=globalThis.URL;
  globalThis.URL={createObjectURL:blob=>{downloads.push(blob);return 'blob:fixture';},revokeObjectURL:()=>{}};
  // Downloads are observed as Blobs; no navigation or real filesystem writes.
  w.HTMLAnchorElement.prototype.click=function() {};
  await startDevkit();
});
afterEach(()=>{w.close(); globalThis.URL=originalURL;});
const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
async function until(check) { for(let i=0;i<100;i++){ if(check())return; await tick(); } assert.ok(check(),w.document.body.textContent.slice(-1800)); }
function click(text, root=w.document) {
  const button=[...root.querySelectorAll('button')].find(b=>b.textContent===text || b.textContent==='＋ '+text);
  assert.ok(button,'Missing button '+text); button.click(); return button;
}
function fill(selector,value) { const input=w.document.querySelector(selector); assert.ok(input,selector); input.value=value; input.dispatchEvent(new w.Event('input')); }
async function upload(input,file) { Object.defineProperty(input,'files',{configurable:true,value:[file]}); input.dispatchEvent(new w.Event('change')); await tick();await tick(); }
async function draft() { click('Save draft'); await tick(); return JSON.parse(await downloads.at(-1).text()); }
async function addWorker() {
  click('Unique Worker'); await tick();
  fill('[data-field="name"] input','UI Worker'); click('Next');
  fill('[data-field="folder"] input','ui_worker');
  while(w.document.querySelector('[data-step]:not([data-step="review"])')) click(w.document.querySelector('[data-action="next"]').textContent);
  click('Save to project'); await until(()=>w.document.querySelector('[data-action="save-project"]'));
}
test('character assistant → missing portrait gate → images → editable draft → ZIP',async()=>{
  await addWorker(); click('Review & export ZIP');
  assert.equal(w.document.querySelector('[data-action="export-pack"]').disabled,true);
  assert.match(w.document.body.textContent,/add profile/);
  click('Back to project'); click('Manage character images');
  const portrait=[...w.document.querySelectorAll('label')].find(l=>l.textContent.includes('Choose portrait')).querySelector('input');
  await upload(portrait,{name:'portrait.png',size:png.length,arrayBuffer:async()=>png.buffer});
  await until(()=>w.document.body.textContent.includes('images/workers/ui_worker/profile.png'));
  click('Back to project'); const saved=await draft();
  assert.equal(saved.images.length,1); assert.equal(Object.values(saved.files)[0][0].name,'UI Worker');
  click('Review & export ZIP'); assert.equal(w.document.querySelector('[data-action="export-pack"]').disabled,false);
  click('Export ZIP'); await tick();
  const bytes=new Uint8Array(await downloads.at(-1).arrayBuffer());
  assert.deepEqual([...bytes.slice(0,4)],[80,75,3,4]);
});
test('override editor preserves all other ingredients and allows a new price',async()=>{
  const mode=w.document.querySelector('[aria-label="Project mode"]'); mode.value='override'; mode.dispatchEvent(new w.Event('change')); await tick();
  click('Edit existing…',w.document.querySelector('[data-type="items"]'));
  click('data/items/alchemy_ingredients.json'); click('Ironroot');
  const sections=[...w.document.querySelectorAll('[data-tab]')];
  for(const tab of sections){ tab.click(); if(w.document.querySelector('[data-field="price"] input'))break; }
  fill('[data-field="price"] input','240'); click('Review'); click('Save draft to project');
  await until(()=>w.document.querySelector('[data-action="save-project"]'));
  const saved=await draft();
  const original=reference.files['data/items/alchemy_ingredients.json'];
  const output=saved.files['data/items/alchemy_ingredients.json'];
  assert.equal(output.items.length,original.items.length);
  assert.equal(output.items.find(i=>i.id==='alchemy_ironroot').price,240);
  assert.deepEqual(output.items.filter(i=>i.id!=='alchemy_ironroot'),original.items.filter(i=>i.id!=='alchemy_ironroot'));
  click('Review & export ZIP'); assert.equal(w.document.querySelector('[data-action="export-pack"]').disabled,false);
});
test('cancelled project-mode changes restore the selected mode and keep the draft',async()=>{
  await addWorker(); w.confirm=()=>false;
  const mode=w.document.querySelector('[aria-label="Project mode"]'); mode.value='override'; mode.dispatchEvent(new w.Event('change')); await tick();
  assert.equal(w.document.querySelector('[aria-label="Project mode"]').value,'characters');
  assert.equal(Object.values((await draft()).files)[0][0].name,'UI Worker');
});
test('opening a draft restores its images and in-app guide leaves the project intact',async()=>{
  const p=createProject(reference); const worker=unique_worker_recipe.build({name:'Restored',folder:'restored',gender:'female',race:'Human',nsfw:false});
  await p.stage('workers',worker,'data/workers/restored.json'); p.addImage('images/workers/restored/profile.png',png);
  const text=JSON.stringify(p.serialize());
  const input=[...w.document.querySelectorAll('label')].find(l=>l.textContent.startsWith('Open draft')).querySelector('input');
  await upload(input,{name:'restore.fmproject.json',size:text.length,text:async()=>text});
  await until(()=>w.document.body.textContent.includes('Draft opened'));
  w.document.getElementById('open-guide').click();
  assert.match(w.document.body.textContent,/do not open, unpack or modify the APK/);
  click('Back to project'); assert.deepEqual(await draft(),p.serialize());
});
test('a failed assistant save can be corrected and retried without losing its answers',async()=>{
  click('Unique Worker'); fill('[data-field="name"] input','Retry Worker'); click('Next'); fill('[data-field="folder"] input','retry_worker');
  while(w.document.querySelector('[data-step]:not([data-step="review"])'))click(w.document.querySelector('[data-action="next"]').textContent);
  fill('[data-action="filename"]','../bad.json'); click('Save to project'); await until(()=>w.document.querySelector('.val-error'));
  assert.ok(w.document.querySelector('[data-step="review"]'));
  fill('[data-action="filename"]','workers/retry.json'); click('Save to project'); await until(()=>w.document.querySelector('[data-action="save-project"]'));
  assert.equal((await draft()).files['data/workers/retry.json'][0].name,'Retry Worker');
});
