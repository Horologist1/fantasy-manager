// devkit_web/src/editors/_engine.js
import { renderField } from '../lib/ui.js';

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

export function runEditor({ sections, entry, schema, container, ctx, onSave, defaultFilename }) {
  const current = { ...entry };
  let activeId = sections[0].id;

  function paint() {
    container.innerHTML = '';
    const tabs = el('div', { class: 'tabs' });
    for (const s of sections) {
      tabs.appendChild(el('button', {
        type: 'button', 'data-tab': s.id,
        class: activeId === s.id ? 'tab active' : 'tab',
        onclick: () => { activeId = s.id; paint(); },
      }, s.label || s.id));
    }
    tabs.appendChild(el('button', {
      type: 'button', 'data-tab': 'review',
      class: activeId === 'review' ? 'tab active' : 'tab',
      onclick: () => { activeId = 'review'; paint(); },
    }, 'Review'));
    container.appendChild(tabs);

    if (activeId === 'review') {
      paintReview();
    } else {
      const section = sections.find((s) => s.id === activeId);
      paintSection(section);
    }
  }

  function paintSection(section) {
    const wrap = el('div', { 'data-section': section.id, class: 'editor-section' });
    for (const fdef of section.fields) {
      const field = renderField(fdef, current[fdef.id] ?? null, (v) => {
        current[fdef.id] = v;
      }, ctx);
      wrap.appendChild(field.element);
    }
    const nav = el('div', { class: 'nav' });
    const idx = sections.findIndex((s) => s.id === section.id);
    if (idx > 0) nav.appendChild(el('button', {
      type: 'button', 'data-action': 'back',
      onclick: () => { activeId = sections[idx - 1].id; paint(); },
    }, 'Back'));
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'next',
      onclick: () => {
        activeId = idx < sections.length - 1 ? sections[idx + 1].id : 'review';
        paint();
      },
    }, idx === sections.length - 1 ? 'Review' : 'Next'));
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  function paintReview() {
    const wrap = el('div', { 'data-section': 'review', class: 'editor-section' });
    const pre = el('pre', { class: 'json-preview' }, JSON.stringify(current, null, 2));
    wrap.appendChild(pre);

    const fnameLabel = el('label', {}, 'Filename');
    const fnameInput = el('input', { type: 'text', 'data-action': 'filename' });
    fnameInput.value = defaultFilename || '';
    wrap.appendChild(fnameLabel);
    wrap.appendChild(fnameInput);

    const nav = el('div', { class: 'nav' });
    nav.appendChild(el('button', {
      type: 'button', 'data-action': 'save',
      onclick: () => onSave(current, fnameInput.value || defaultFilename),
    }, 'Save'));
    wrap.appendChild(nav);
    container.appendChild(wrap);
  }

  paint();
}
