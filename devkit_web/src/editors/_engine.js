// devkit_web/src/editors/_engine.js
import { renderField, renderSummary } from '../lib/ui.js';

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

export function runEditor({
  sections, entry, schema, container, ctx, onSave,
  defaultFilename, validate,
}) {
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
    wrap.appendChild(renderSummary(current));
    const details = el('details', { class: 'raw-json' });
    details.appendChild(el('summary', {}, 'Show raw JSON'));
    details.appendChild(el('pre', { class: 'json-preview' }, JSON.stringify(current, null, 2)));
    wrap.appendChild(details);

    const fnameLabel = el('label', {}, 'Filename');
    const fnameInput = el('input', { type: 'text', 'data-action': 'filename' });
    fnameInput.value = defaultFilename || '';
    wrap.appendChild(fnameLabel);
    wrap.appendChild(fnameInput);

    if (validate) {
      const r = validate(current);
      if (r.errors.length || r.warnings.length) {
        const panel = el('div', { class: 'validation-panel' });
        panel.appendChild(el('h3', {}, `Errors: ${r.errors.length} · Warnings: ${r.warnings.length}`));
        for (const e of r.errors) {
          panel.appendChild(el('div', { class: 'val-error' }, `❌ ${e.field || e.rule}: ${e.error || e.message}`));
        }
        for (const w of r.warnings) {
          panel.appendChild(el('div', { class: 'val-warning' }, `⚠ ${w.rule}: ${w.message}`));
        }
        if (r.migrations.length) {
          const mig = el('button', {
            type: 'button',
            'data-action': 'migrate',
            onclick: async () => {
              const { applyMigrations } = await import('../lib/validator.js');
              const migrated = applyMigrations(current, schema);
              Object.assign(current, migrated);
              for (const m of r.migrations) delete current[m.from];
              paint();
            },
          }, `Apply ${r.migrations.length} legacy migration(s)`);
          panel.appendChild(mig);
        }
        wrap.appendChild(panel);
      }
    }

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
