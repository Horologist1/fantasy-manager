// GIF → WebM batch tool, powered by ffmpeg.wasm (lazy-loaded from jsDelivr on
// first use; ~31 MB once, then browser-cached). Same encoder settings as the
// v6 editor's convert_gif_to_webm. Single-threaded core on purpose: GitHub
// Pages sends no COOP/COEP headers, so SharedArrayBuffer (multithread) is
// unavailable there.
const FFMPEG_VERSION = '0.12.10';
const UTIL_VERSION = '0.12.1';
const CORE_VERSION = '0.12.6';
const CDN = 'https://cdn.jsdelivr.net/npm';

export const FFMPEG_ARGS = (input, output) => [
  '-i', input, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
  '-auto-alt-ref', '0', '-crf', '30', '-b:v', '0', '-an', output,
];

export function webmNameFor(gifName) {
  return gifName.replace(/\.gif$/i, '.webm');
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k.startsWith('on') && typeof v === 'function') {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (v !== undefined && v !== null) node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`failed to load ${src}`));
    document.head.appendChild(s);
  });
}

let _ffmpeg = null;

async function getFFmpeg(onProgress) {
  if (_ffmpeg) return _ffmpeg;
  await loadScript(`${CDN}/@ffmpeg/ffmpeg@${FFMPEG_VERSION}/dist/umd/ffmpeg.js`);
  await loadScript(`${CDN}/@ffmpeg/util@${UTIL_VERSION}/dist/umd/index.js`);
  const { FFmpeg } = window.FFmpegWASM;
  const { toBlobURL } = window.FFmpegUtil;
  const ffmpeg = new FFmpeg();
  // The class worker runs as type:"module", where importScripts() always
  // throws and the fallback is `(await import(coreURL)).default` — so the
  // core MUST be the ESM build (the UMD core has no default export).
  const base = `${CDN}/@ffmpeg/core@${CORE_VERSION}/dist/esm`;
  onProgress('Downloading ffmpeg core (~31 MB, one time)…');
  // Workers must be same-origin, so every script the loader spawns is passed
  // through toBlobURL: the class worker (814.ffmpeg.js) and the core pair.
  await ffmpeg.load({
    classWorkerURL: await toBlobURL(
      `${CDN}/@ffmpeg/ffmpeg@${FFMPEG_VERSION}/dist/umd/814.ffmpeg.js`, 'text/javascript'),
    coreURL: await toBlobURL(`${base}/ffmpeg-core.js`, 'text/javascript'),
    wasmURL: await toBlobURL(`${base}/ffmpeg-core.wasm`, 'application/wasm'),
  });
  _ffmpeg = ffmpeg;
  return ffmpeg;
}

/**
 * runGifToWebmTool(container, { onDone }) — pick a folder, convert every .gif
 * in it (recursively) to .webm written next to the original.
 */
export function runGifToWebmTool(container, { onDone }) {
  let folderHandle = null;
  let gifs = []; // { name, path, dirHandle }
  let deleteOriginals = false;

  function paintPick() {
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, 'GIF → WebM converter'));
    wrap.appendChild(el('p', { class: 'muted' },
      'Ren\'Py does not animate GIFs — convert them to WebM. Pick a folder ',
      '(e.g. images/workers/<your_worker>/); every .gif inside is converted and ',
      'the .webm saved next to it. Needs an internet connection the first time ',
      'to download the converter (~31 MB, cached afterwards).'));
    wrap.appendChild(el('button', {
      type: 'button', 'data-action': 'pick-gif-folder',
      onclick: async () => {
        if (!('showDirectoryPicker' in window)) {
          alert('Folder picking needs Chrome, Edge, or Brave.');
          return;
        }
        folderHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
        gifs = [];
        await scan(folderHandle, '');
        paintQueue();
      },
    }, '📂 Pick a folder with GIFs'));
    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'back', onclick: () => onDone(),
    }, 'Back'));
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  async function scan(dirHandle, prefix) {
    for await (const [name, entry] of dirHandle.entries()) {
      if (entry.kind === 'directory') await scan(entry, `${prefix}${name}/`);
      else if (/\.gif$/i.test(name)) gifs.push({ name, path: `${prefix}${name}`, dirHandle });
    }
  }

  function paintQueue() {
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, 'GIF → WebM converter'));
    if (gifs.length === 0) {
      wrap.appendChild(el('p', {}, 'No .gif files found in that folder.'));
    } else {
      wrap.appendChild(el('p', {}, `${gifs.length} GIF(s) found:`));
      const list = el('ul');
      for (const g of gifs) list.appendChild(el('li', {}, g.path));
      wrap.appendChild(list);
      const delRow = el('div', { class: 'field' });
      delRow.appendChild(el('label', {}, 'Delete original GIFs after converting'));
      const cb = el('input', { type: 'checkbox' });
      cb.addEventListener('change', () => { deleteOriginals = cb.checked; });
      delRow.appendChild(cb);
      wrap.appendChild(delRow);
    }
    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'back', onclick: () => paintPick(),
    }, 'Back'));
    if (gifs.length > 0) {
      nav.appendChild(el('button', {
        type: 'button', 'data-action': 'convert', onclick: () => convertAll(),
      }, `Convert ${gifs.length} GIF(s)`));
    }
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  async function convertAll() {
    container.innerHTML = '';
    const wrap = el('div', { class: 'recipe-step' });
    wrap.appendChild(el('h2', {}, 'Converting…'));
    const logBox = el('pre', { class: 'json-preview', 'data-role': 'convert-log' });
    wrap.appendChild(logBox);
    container.appendChild(wrap);
    const log = (line) => {
      logBox.textContent += `${line}\n`;
      logBox.scrollTop = logBox.scrollHeight;
    };

    let ffmpeg;
    try {
      ffmpeg = await getFFmpeg(log);
    } catch (e) {
      // ffmpeg.wasm sometimes rejects with plain strings, not Error objects
      log(`Could not load ffmpeg: ${String(e?.message ?? e)}`);
      log('Check your internet connection — or use the hosted devkit page, where this tool is most reliable.');
      finish(wrap);
      return;
    }

    let ok = 0;
    let failed = 0;
    for (const [i, g] of gifs.entries()) {
      log(`(${i + 1}/${gifs.length}) ${g.path}…`);
      try {
        const file = await (await g.dirHandle.getFileHandle(g.name)).getFile();
        await ffmpeg.writeFile('in.gif', new Uint8Array(await file.arrayBuffer()));
        await ffmpeg.exec(FFMPEG_ARGS('in.gif', 'out.webm'));
        const out = await ffmpeg.readFile('out.webm');
        if (!out || out.length === 0) throw new Error('empty output');
        const fh = await g.dirHandle.getFileHandle(webmNameFor(g.name), { create: true });
        const w = await fh.createWritable();
        await w.write(out);
        await w.close();
        if (deleteOriginals) await g.dirHandle.removeEntry(g.name);
        ok += 1;
        log(`  → ${webmNameFor(g.name)}`);
      } catch (e) {
        failed += 1;
        log(`  ! failed: ${String(e?.message ?? e)}`);
      }
    }
    log(`Done: ${ok} converted${failed ? `, ${failed} failed` : ''}.`);
    finish(wrap);
  }

  function finish(wrap) {
    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'done', onclick: () => onDone(),
    }, 'Finish'));
    wrap.appendChild(nav);
  }

  paintPick();
}
