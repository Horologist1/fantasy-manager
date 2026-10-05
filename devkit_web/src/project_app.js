import { TYPES } from './lib/content_types.js';
import { loadBundledReference, readGameReference } from './lib/reference.js';
import { createProject, restoreProject, PROJECT_MODES, rowsFor, identityFor, projectFilename } from './lib/project.js';
import { categoryFor, supportsOverride, parseJSON, LIMITS, WORKER_FIELDS, characterErrors, CHARACTER_CONTENT, scriptSafetyErrors } from './lib/contract.js';
import { validateEntry, validateDailyStoryTarget } from './lib/validator.js';
import { runRecipe } from './recipes/_engine.js';
import { runEditor } from './editors/_engine.js';
import { runWMImporter } from './converters/wm_import_ui.js';
import { runGifToWebmTool } from './tools/gif_to_webm.js';
import { showGuide } from './user_guide.js';

export async function startDevkit() {
  const app = document.getElementById('app');
  let reference, project, savedRevision = 0, editing = false, busy = false;
  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key,value] of Object.entries(attrs)) {
      if (key.startsWith('on')) node.addEventListener(key.slice(2), async event => {
        try { await value(event); } catch (error) { message(error.message, true); }
      });
      else if (value !== false && value != null) node.setAttribute(key, value === true ? '' : value);
    }
    for (const child of children) if (child != null) node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
    return node;
  }
  const button = (text, action, attrs = {}) => el('button', {type:'button', onclick:action, ...attrs}, text);
  function message(text, error = false) {
    let box = document.getElementById('project-message');
    if (!box) { box = el('div', {id:'project-message', role:'status'}); app.prepend(box); }
    box.className = error ? 'banner val-error' : 'banner'; box.textContent = text;
    box.scrollIntoView?.({block:'nearest'});
  }
  function clear() { app.replaceChildren(); app.classList.remove('guide'); }
  function hasWork() { return Object.keys(project.files).length || project.assetPaths.length || editing; }
  function back() {
    if (editing && !window.confirm('Discard changes on this form? Entries already saved to the project will be kept.')) return false;
    editing = false; landing(); return true;
  }
  function download(data, name, mime) {
    const url = URL.createObjectURL(new Blob([data], {type:mime}));
    const link = el('a', {href:url, download:name});
    document.body.appendChild(link); link.click(); link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  async function readFile(file, max = LIMITS.json) {
    if (!file || file.size > max) throw new Error('File is missing or exceeds the size limit.');
    return parseJSON(await file.text());
  }
  function fileInput(accept, action, options = {}) {
    const owner = project;
    return el('input', {type:'file', accept, ...options, onchange:async event => {
      if (project !== owner) throw new Error('The project changed. Choose the file again in the current project.');
      if (busy) throw new Error('Please wait for the current file operation to finish.');
      const input = event.currentTarget;
      const files = [...input.files];
      if (!files.length) return;
      busy = true;
      try { await action(files); input.value = ''; }
      finally { busy = false; }
    }});
  }
  function stageValidation(type, entry, target) {
    const ctx = project.context();
    const result = validateEntry(entry, type.schema, ctx);
    if (project.mode === 'characters' && type.id === 'workers') result.errors.push(...characterErrors(entry).map(message=>({field:'Character pack',message})));
    if (project.mode === 'characters' && type.id !== 'workers') result.errors.push(...scriptSafetyErrors(entry).map(message=>({field:'Character pack',message})));
    if (target) result.errors.push(...validateDailyStoryTarget(target, ctx));
    return result;
  }
  function fileChoices(type) {
    const names = new Set(Object.keys(project.files));
    if (project.mode !== 'characters') for (const path of Object.keys(reference.files)) names.add(path);
    return [...names].filter(path => categoryFor(path) === type.id && (project.mode !== 'override' || supportsOverride(path))).sort();
  }
  function pick(title, choices, selected, cancel = landing) {
    clear();
    app.append(el('h2', {}, title));
    const search = el('input', {type:'search', placeholder:'Filter…', 'aria-label':'Filter choices'});
    const list = el('div', {class:'picker-list'});
    const paint = () => {
      list.replaceChildren();
      for (const choice of choices.filter(c => c.label.toLowerCase().includes(search.value.toLowerCase()))) {
        list.append(button(choice.label, () => selected(choice), {'data-choice':choice.key}));
      }
    };
    search.addEventListener('input', paint); paint();
    app.append(search, list, button('Back', cancel));
    if (!choices.length) app.append(el('p', {}, 'No matching files or entries. Create an entry first.'));
  }
  function newProject(mode) {
    if (busy) { landing(); throw new Error('Please wait for the current file operation to finish.'); }
    if (hasWork() && !window.confirm('Start a new project? Save your draft first if you want to keep this work.')) { landing(); return; }
    if (mode === 'override' && !window.confirm('JSON overrides replace whole game files. Install them before starting a new game and keep the same mods for that playthrough. Continue?')) { landing(); return; }
    project = createProject(reference, {mode, name:project.name}); savedRevision = 0; editing = false; landing();
  }
  function landing() {
    clear(); editing = false;
    document.getElementById('folder-status').textContent = 'Game ' + reference.meta.game_version + ' · ' + (reference.meta.source === 'bundled' ? 'bundled reference' : 'selected PC reference');
    const panel = el('section', {class:'project-panel'});
    panel.append(el('h2', {}, 'Your mod project'));
    const name = el('input', {type:'text', value:project.name, maxlength:'100', 'aria-label':'Mod name', oninput:event => { project.name = event.target.value; }});
    const mode = el('select', {'aria-label':'Project mode', onchange:event => newProject(event.target.value)});
    for (const [value,label] of Object.entries(PROJECT_MODES)) mode.append(el('option', {value, selected:project.mode === value}, label));
    panel.append(el('label', {class:'project-field'}, 'Mod name', name), el('label', {class:'project-field'}, 'Project mode', mode));
    const descriptions = {
      characters:'Add regular characters and their pictures, plus optional new traits, events and daily stories. Export one ZIP for Mods → Install mods on PC or Android, or drag its game folder onto a PC installation.',
      override:'Edit a copy of an existing catalog. The ZIP replaces each included file in full. Use a new game; images and scripts are not imported.',
      manual:'Advanced PC workflow. Export a game folder for manual installation. This mode is not supported by the in-game Mods installer.',
    };
    panel.append(el('p', {}, descriptions[project.mode]));
    panel.append(el('p', {class:'muted'}, 'Original game files stay unchanged. Save a draft to continue editing later; Export ZIP creates the installable pack.'));
    const actions = el('div', {class:'nav'});
    actions.append(button('Save draft', () => {
      download(JSON.stringify(project.serialize()), projectFilename(project.name)+'.fmproject.json', 'application/json');
      savedRevision = project.revision; message('Draft downloaded. Keep this .fmproject.json file to resume editing, including pictures.');
    }, {'data-action':'save-project'}));
    const openDraft = fileInput('.json', async ([file]) => {
      const restored = restoreProject(reference, await readFile(file, 200 * 1024 * 1024));
      if (hasWork() && !window.confirm('Replace the current project with this draft?')) return;
      project = restored; savedRevision = project.revision; landing(); message('Draft opened.');
    });
    actions.append(el('label', {class:'file-button'}, 'Open draft', openDraft));
    actions.append(button('Review & export ZIP', review, {'data-action':'review-pack'}));
    actions.append(button('New project', () => newProject(project.mode)));
    panel.append(actions); app.append(panel);

    const paths = Object.keys(project.files).sort();
    app.append(el('h3', {}, 'Project files ('+paths.length+') · Images ('+project.assetPaths.length+')'));
    for (const path of paths) {
      const row = el('div', {class:'project-file'});
      row.append(button(path, () => openFile(TYPES.find(t => t.id === categoryFor(path)), path)), button('Remove from project', () => {
        if (window.confirm('Remove this draft file? The original game file remains unchanged.')) { project.removeFile(path); landing(); }
      }, {class:'secondary'})); app.append(row);
    }
    if (!paths.length) app.append(el('p', {class:'muted'}, 'Start with an assistant below, or edit a copy of an existing file in override mode.'));
    if (project.mode !== 'override') app.append(button('Manage character images', imagePage, {'data-action':'images'}));

    for (const type of TYPES) {
      const characterType = type.id === 'workers' || CHARACTER_CONTENT.includes(type.id);
      if (project.mode === 'characters' && !characterType) continue;
      if (project.mode === 'override' && type.id === 'interactions') continue;
      const group = el('section', {class:'type-group', 'data-type':type.id});
      group.append(el('h2', {}, type.title), el('p', {class:'muted'}, project.mode === 'characters' && type.id === 'workers' ? 'Regular named characters with their own image folders.' : type.blurb));
      const actions = el('div', {class:'type-actions'});
      for (const recipe of type.recipes) {
        if (project.mode === 'characters' && type.id === 'workers' && recipe.id !== 'unique_worker') continue;
        actions.append(button('＋ '+recipe.title, () => startRecipe(type, recipe), {title:recipe.description}));
      }
      actions.append(button(project.mode === 'characters' ? (type.id === 'workers' ? 'Edit project workers' : 'Edit project entries') : 'Edit existing…', () => pick('Choose a file to edit', fileChoices(type).map(path => ({key:path,label:path})), choice => openFile(type, choice.key))));
      group.append(actions); app.append(group);
    }
    if (project.mode === 'characters') app.append(el('p', {class:'muted'}, 'Traits, events and daily stories in a character pack must be new (new names and IDs); daily stories are added to existing jobs. Procedural templates, monsters, items, buildings, interactions and monthly conditions need a separate override or manual PC project.'));
    if (project.mode !== 'override') {
      const tools = el('section', {class:'type-group'});
      tools.append(el('h2', {}, 'Tools'), button('Whoremaster importer', wmImport), button('GIF → WebM (PC file tool)', () => {
        clear(); runGifToWebmTool(app, {onDone:landing});
      })); app.append(tools);
    }
    if (project.mode !== 'override') {
      const imported = fileInput('.json', async ([file]) => {
        const data = await readFile(file);
        pick('What kind of JSON is this?', TYPES.filter(t => project.mode !== 'characters' || t.id === 'workers' || CHARACTER_CONTENT.includes(t.id)).map(t=>({key:t.id,label:t.title})), choice=>{
          const type=TYPES.find(t=>t.id===choice.key);
          project.importJSON(type.id === 'monthly_conditions' ? 'data/monthly_conditions/cards.json' : 'data/'+type.folder+'/'+file.name,data); landing(); message('JSON added as a draft. Review the pack before exporting.');
        });
      });
      app.append(el('label', {class:'file-button'}, 'Add existing JSON to project', imported));
    }
  }
  async function startRecipe(type, recipe) {
    clear(); editing = true;
    await runRecipe(recipe, app, {modname:projectFilename(project.name), ctx:project.context(), saveLabel:'Save to project', onCancel:back,
      onSubmit:async out => {
        let path = out.filename.startsWith('data/') ? out.filename : 'data/'+out.filename;
        if (project.mode === 'override') {
          const choice = await new Promise(resolve => pick('Choose the original file to include in this override', fileChoices(type).map(path => ({key:path,label:path})), resolve, ()=>resolve(null)));
          if (!choice) return false;
          path = choice.key;
        }
        if (out.edit) {
          edit(type,path,type.id === 'daily_stories' ? out.json.story : out.json,type.id === 'daily_stories' ? out.json : null,null);
          return true;
        }
        return storeRecipe(type,out,path);
      },
    });
  }
  async function storeRecipe(type, out, path) {
    const existing = project.read(path.startsWith('data/') ? path : 'data/'+path);
    let replacement = false;
    if (existing && type.id !== 'daily_stories') {
      const rows = rowsFor(type, existing);
      replacement = (Array.isArray(out.json) ? out.json : [out.json]).some(e => rows.some(r => identityFor(type,r) === identityFor(type,e)));
      if (replacement && !window.confirm('This identifier exists in the selected file. Replace that entry in the project copy? Other entries will be preserved.')) return false;
    }
    await project.stage(type.id, out.json, path, {replaceExisting:replacement});
    editing = false; landing(); message('Saved to the project. Review & export ZIP checks the whole pack.'); return true;
  }
  function openFile(type, path) {
    const data = project.read(path);
    const choices = [];
    for (const [index,entry] of rowsFor(type,data).entries()) {
      if (type.id === 'daily_stories') {
        for (const [storyIndex,story] of entry.daily_stories.entries()) choices.push({key:index+':'+storyIndex, label:entry.building_id+' / '+entry.profession_id+' — '+story.id, entry:story, target:entry});
      } else choices.push({key:String(index), label:(entry.name || entry.template_id || entry.id || 'Entry '+(index+1))+(type.id === 'workers' ? (entry.nsfw ? ' (NSFW)' : ' (SFW)') : ''), entry, target:null});
    }
    pick(path+' — choose an entry', choices, choice => edit(type,path,choice.entry,choice.target,identityFor(type,choice.entry)));
  }
  function edit(type, path, entry, target, originalKey) {
    clear(); editing = true;
    const regular = project.mode === 'characters' && type.id === 'workers';
    const unsupported = regular ? Object.keys(entry).filter(key=>!WORKER_FIELDS.includes(key)) : [];
    if (unsupported.length) {
      app.append(el('div', {class:'banner'}, 'This entry contains fields that character packs do not import: '+unsupported.join(', ')+'.',
        button('Remove unsupported fields from this draft', () => {
          if (!window.confirm('Remove those special fields from the draft? Recruitment rules and template settings in those fields will be lost. The source JSON stays unchanged.')) return;
          edit(type,path,Object.fromEntries(Object.entries(entry).filter(([key])=>WORKER_FIELDS.includes(key))),target,originalKey);
        })));
    }
    const container=el('div'); app.append(container);
    const sections=regular ? type.sections.map(s=>({...s,fields:s.fields.filter(f=>WORKER_FIELDS.includes(f.id))})).filter(s=>s.fields.length) : type.sections;
    runEditor({sections, entry, schema:type.schema, container, ctx:project.context(), defaultFilename:path,
      filenameEditable:false, saveLabel:'Save draft to project', allowInvalidDraft:true, onCancel:back,
      validate:value => stageValidation(type,value,target),
      onSave:async updated => {
        if (originalKey == null) { await storeRecipe(type, {json:target ? {...target,story:updated} : updated}, path); return; }
        await project.stage(type.id, target ? {...target,story:updated} : updated, path, {originalKey});
        editing = false; landing(); message('Draft saved. Validation errors, if any, must be fixed before export.');
      },
    });
  }
  function imagePage() {
    clear();
    app.append(el('h2', {}, 'Character images'), el('p', {}, 'Choose a portrait for each image folder, then add any other PNG, JPG or WebP pictures. Images are copied into the project.'));
    const workers = Object.entries(project.files).filter(([path])=>categoryFor(path)==='workers').flatMap(([,value])=>rowsFor(TYPES[0],value));
    const folders = new Set();
    for (const worker of workers) {
      if (!worker.folder || folders.has(worker.folder)) continue;
      folders.add(worker.folder);
      const group = el('section', {class:'project-panel'});
      group.append(el('h3', {}, worker.name || worker.template_id), el('p', {class:'muted'}, 'Image folder: '+worker.folder));
      const add = (portrait) => fileInput('.png,.jpg,.jpeg,.webp', async files => {
        for (const file of files) {
          if (file.size > LIMITS.file) throw new Error('Image exceeds 32 MB: '+file.name);
          const filename = portrait ? 'profile.'+file.name.split('.').at(-1).toLowerCase() : file.name;
          const path = 'images/workers/'+worker.folder+'/'+filename;
          const replace = project.assetPaths.includes(path);
          if (replace && !window.confirm('Replace '+filename+' in this project?')) continue;
          project.addImage(path, new Uint8Array(await file.arrayBuffer()), replace);
        }
        imagePage();
      }, portrait ? {} : {multiple:true});
      group.append(el('label', {class:'file-button'}, 'Choose portrait', add(true)), el('label', {class:'file-button'}, 'Add other images', add(false)));
      app.append(group);
    }
    if (!workers.length) app.append(el('p', {}, 'Create a worker and save it to the project first.'));
    for (const path of project.assetPaths) app.append(el('div', {class:'project-file'}, el('span', {}, path), button('Remove', () => { project.removeImage(path); imagePage(); }, {class:'secondary'})));
    app.append(button('Back to project', landing));
  }
  function review() {
    clear(); const result = project.validate();
    app.append(el('h2', {}, 'Review '+project.name), el('p', {}, PROJECT_MODES[project.mode]+' · Game '+project.target.game_version));
    const paths = Object.keys(project.files);
    app.append(el('p', {}, paths.length+' JSON file(s), '+project.assetPaths.length+' image(s).'));
    for (const path of paths) app.append(el('p', {class:'muted'}, path));
    if (project.mode === 'override') app.append(el('div', {class:'banner'}, 'Whole files will be replaced. Install before starting a new game, restart the game, and keep the same packs for that playthrough.'));
    app.append(el('h3', {}, result.errors.length+' error(s) · '+result.warnings.length+' warning(s)'));
    for (const error of result.errors) app.append(el('p', {class:'val-error'}, error));
    if (result.warnings.length) {
      const warnings = el('details', {}, el('summary', {}, 'Show warnings'));
      for (const warning of result.warnings) warnings.append(el('p', {class:'val-warning'}, warning));
      app.append(warnings);
    }
    app.append(button('Export ZIP', async () => {
      if (busy) return; busy = true;
      try {
        const pack = project.exportPack(); download(pack.bytes,pack.filename,'application/zip');
        message(project.mode === 'manual' ? 'ZIP downloaded for manual PC installation. Read README.txt inside the ZIP before copying files.' : 'ZIP downloaded. Open Mods → Install mods in the game'+(project.mode === 'override' ? ', enable JSON override, then select this ZIP.' : ' and select this ZIP. Leave JSON override off. README.txt inside the ZIP also explains manual installation.'));
      } finally { busy = false; }
    }, {disabled:result.errors.length > 0, 'data-action':'export-pack'}), button('Back to project', landing));
    app.append(el('p', {class:'muted'}, 'Acceptance by the installer checks the pack format. Test custom events and gameplay in a new game before sharing.'));
  }
  function wmImport() {
    clear(); editing = true;
    const owner = project;
    const checkOwner = () => { if (owner !== project) throw new Error('The project changed; restart the import.'); };
    runWMImporter(app, {
      ctx:()=>owner.context(), modname:projectFilename(owner.name), projectMode:owner.mode,
      fs:{ mergeAndWrite:async (path,entry) => { checkOwner(); await owner.stage(categoryFor('data/'+path),entry,path); } },
      hasGameFolder:()=>true, getGameHandle:()=>null,
      addImage:(path,bytes)=>{ checkOwner(); owner.addImage(path,bytes); },
      onDone:()=>{ checkOwner(); editing=false; landing(); },
    });
  }
  document.getElementById('select-game-folder').addEventListener('click', async () => {
    let loading = false;
    try {
      if (busy) throw new Error('Please wait for the current file operation to finish.');
      if (hasWork()) throw new Error('Save your draft and start an empty project before changing the game reference.');
      if (!window.showDirectoryPicker) throw new Error('Folder reference selection requires a compatible desktop browser. The bundled reference works without selecting a folder, including on Android.');
      busy = true; loading = true;
      const selected = await readGameReference(await window.showDirectoryPicker({mode:'read'}));
      reference = selected; project = createProject(reference, {mode:project.mode,name:project.name}); landing();
    } catch (error) { if (error.name !== 'AbortError') message(error.message,true); }
    finally { if (loading) busy = false; }
  });
  document.getElementById('open-guide').addEventListener('click', () => {
    if (editing && !window.confirm('Leave this form and discard its unsaved changes?')) return;
    editing=false; showGuide(app,landing);
  });
  window.addEventListener('beforeunload', event => {
    if (project && (editing || project.revision !== savedRevision)) { event.preventDefault(); event.returnValue = ''; }
  });
  try { reference = await loadBundledReference(); project = createProject(reference); landing(); }
  catch (error) { clear(); app.append(el('h2', {}, 'The game reference could not be loaded')); message(error.message+' Reopen the complete offline HTML or reload the hosted devkit.',true); }
}
