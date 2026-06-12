// devkit_web/src/lib/ui.js

/**
 * renderField(def, initialValue, onChange) → { element, getValue, setValue, setError }
 *
 * For catalog-backed fields (def.catalog), pass a ctx via renderField(def, val, onChange, ctx)
 * where ctx.catalogs[def.catalog] is a Set used for autocomplete (omitted in this MVP if absent).
 */

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k.startsWith('on') && typeof v === 'function') {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else if (v !== undefined && v !== null) {
      node.setAttribute(k, v);
    }
  }
  for (const c of children) {
    if (c == null) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}

function wrapField(def, inner, errorNode) {
  const wrap = el('div', { class: 'field', 'data-field': def.id });
  if (def.label) wrap.appendChild(el('label', {}, def.label));
  wrap.appendChild(inner);
  wrap.appendChild(errorNode);
  return wrap;
}

function makeError() {
  return el('div', { class: 'field-error' });
}

function setErr(errEl, wrap, msg) {
  errEl.textContent = msg || '';
  if (msg) wrap.setAttribute('aria-invalid', 'true');
  else wrap.removeAttribute('aria-invalid');
}

export function renderField(def, initial, onChange, ctx = null) {
  const type = Array.isArray(def.type) ? def.type[0] : def.type;
  switch (type) {
    case 'string':
    case 'longtext':
    case 'formula':
      return renderText(def, initial, onChange, ctx);
    case 'int':
    case 'float':
      return renderNumber(def, initial, onChange, type === 'int');
    case 'bool':
      return renderBool(def, initial, onChange);
    case 'enum':
      return renderEnum(def, initial, onChange);
    case 'list_of_strings':
      return renderListOfStrings(def, initial, onChange, ctx);
    case 'dict_of_numbers':
      return renderDictOfNumbers(def, initial, onChange, ctx);
    case 'dict_of_bools':
      return renderDictOfBools(def, initial, onChange, ctx);
    case 'object':
      return renderObject(def, initial, onChange, ctx);
    case 'list_of_objects':
      return renderListOfObjects(def, initial, onChange, ctx);
    case 'dict_of_objects':
      return renderDictOfObjects(def, initial, onChange, ctx);
    default:
      return renderText(def, initial == null ? '' : String(initial), onChange, ctx);
  }
}

// Shared "add key" row: text input + button, with optional clickable
// suggestions from ctx.catalogs[def.key_catalog].
function makeAddKeyRow(def, ctx, existing, onAdd) {
  const row = el('div', { class: 'add-key-row' });
  const input = el('input', { type: 'text', 'data-role': 'add-key', placeholder: 'Add key…' });
  const btn = el('button', { type: 'button', 'data-action': 'add-key' }, '+ Add');
  const commit = () => {
    const k = input.value.trim();
    if (!k || existing().includes(k)) return;
    input.value = '';
    onAdd(k);
  };
  btn.addEventListener('click', commit);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); commit(); }
  });
  row.appendChild(input);
  row.appendChild(btn);

  const wrap = el('div');
  wrap.appendChild(row);
  if (def.key_catalog && ctx?.catalogs?.[def.key_catalog]) {
    const sugg = el('div', { class: 'suggestion-row' });
    for (const item of Array.from(ctx.catalogs[def.key_catalog]).sort()) {
      sugg.appendChild(el('button', {
        type: 'button',
        class: 'suggestion-chip',
        'data-suggestion': item,
        onclick: () => { if (!existing().includes(item)) onAdd(item); },
      }, item));
    }
    wrap.appendChild(sugg);
  }
  return wrap;
}

function renderText(def, initial, onChange, ctx = null) {
  const errEl = makeError();
  const input = def.type === 'longtext'
    ? el('textarea', { rows: 4 })
    : el('input', { type: 'text' });
  if (initial != null) input.value = initial;
  input.addEventListener('input', () => onChange(input.value === '' ? null : input.value));
  if (def.hint) {
    input.setAttribute('placeholder', def.hint);
    input.setAttribute('title', def.hint);
  }
  const wrap = wrapField(def, input, errEl);

  // Catalog-backed string: show clickable suggestion chips below the input so
  // the user can browse instead of guessing names from memory.
  if (def.catalog && ctx?.catalogs?.[def.catalog]) {
    const items = Array.from(ctx.catalogs[def.catalog]).sort();
    if (items.length > 0) {
      const block = el('div', { class: 'string-suggestions', 'data-role': 'suggestions' });
      block.appendChild(el('span', { class: 'muted' },
        `Available (${items.length}) — click to use:`));
      const row = el('div', { class: 'suggestion-row' });
      for (const item of items) {
        const chip = el('button', {
          type: 'button',
          class: 'suggestion-chip',
          'data-suggestion': item,
          onclick: () => {
            input.value = item;
            onChange(item);
          },
        }, item);
        row.appendChild(chip);
      }
      block.appendChild(row);
      wrap.appendChild(block);
    }
  }

  return {
    element: wrap,
    getValue: () => (input.value === '' ? null : input.value),
    setValue: (v) => (input.value = v == null ? '' : String(v)),
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderNumber(def, initial, onChange, isInt) {
  const errEl = makeError();
  const input = el('input', { type: 'number' });
  input.value = initial == null ? '' : String(initial);
  const parse = (s) => {
    if (s === '') return 0;
    const n = isInt ? parseInt(s, 10) : parseFloat(s);
    return Number.isNaN(n) ? 0 : n;
  };
  input.addEventListener('input', () => onChange(parse(input.value)));
  const wrap = wrapField(def, input, errEl);
  return {
    element: wrap,
    getValue: () => parse(input.value),
    setValue: (v) => (input.value = v == null ? '' : String(isInt ? Math.trunc(v) : v)),
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderBool(def, initial, onChange) {
  const errEl = makeError();
  const input = el('input', { type: 'checkbox' });
  input.checked = !!initial;
  input.addEventListener('change', () => onChange(input.checked));
  input.addEventListener('click', () => onChange(input.checked));
  const wrap = wrapField(def, input, errEl);
  return {
    element: wrap,
    getValue: () => input.checked,
    setValue: (v) => (input.checked = !!v),
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderEnum(def, initial, onChange) {
  const errEl = makeError();
  const sel = el('select');
  for (const opt of def.options || []) sel.appendChild(el('option', { value: opt }, opt));
  if (initial) sel.value = initial;

  const descs = def.option_descriptions || null;
  const descEl = descs
    ? el('div', { class: 'enum-option-description', 'data-role': 'option-description' })
    : null;

  function paintDesc() {
    if (!descEl) return;
    const v = sel.value;
    const text = descs[v];
    if (text) {
      descEl.textContent = text;
      descEl.classList.remove('muted-empty');
    } else {
      descEl.textContent = 'Pick an option to see what it does.';
      descEl.classList.add('muted-empty');
    }
  }

  sel.addEventListener('change', () => {
    onChange(sel.value);
    paintDesc();
  });

  const wrap = wrapField(def, sel, errEl);
  if (descEl) {
    wrap.appendChild(descEl);
    paintDesc();
  }

  return {
    element: wrap,
    getValue: () => sel.value,
    setValue: (v) => {
      sel.value = v == null ? '' : v;
      paintDesc();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderListOfStrings(def, initial, onChange, ctx) {
  // Catalog-backed: render a visible browsable picker so the user can discover
  // valid values instead of guessing them from memory. Without a catalog we
  // fall back to a free-text chip input.
  if (def.catalog && ctx?.catalogs?.[def.catalog]) {
    const meta = ctx.meta?.[`${catalogToMetaKey(def.catalog)}`] || null;
    return renderCatalogPicker(def, initial, ctx.catalogs[def.catalog], onChange, meta);
  }

  const errEl = makeError();
  let values = Array.isArray(initial) ? [...initial] : [];
  const container = el('div', { class: 'chips' });
  const input = el('input', { type: 'text', placeholder: 'Add…' });

  function paint() {
    container.innerHTML = '';
    for (const v of values) {
      const chip = el('span', { class: 'chip' }, v, ' ');
      const x = el('button', { type: 'button', class: 'chip-x' }, '×');
      x.addEventListener('click', () => {
        values = values.filter((y) => y !== v);
        paint();
        onChange(values);
      });
      chip.appendChild(x);
      container.appendChild(chip);
    }
    container.appendChild(input);
  }

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && input.value.trim()) {
      e.preventDefault();
      values.push(input.value.trim());
      input.value = '';
      paint();
      onChange(values);
    }
  });

  paint();
  const wrap = wrapField(def, container, errEl);
  return {
    element: wrap,
    getValue: () => [...values],
    setValue: (v) => {
      values = Array.isArray(v) ? [...v] : [];
      paint();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function catalogToMetaKey(catalogName) {
  // Maps e.g. "all_traits" → "trait_meta", "all_items" → "item_meta",
  // "all_buildings" → "building_meta". Falls back to <name>_meta otherwise.
  const known = {
    all_traits: 'trait_meta',
    race_traits: 'trait_meta',
    all_items: 'item_meta',
    all_buildings: 'building_meta',
  };
  return known[catalogName] || `${catalogName}_meta`;
}

function metaDescription(meta, item) {
  if (!meta) return '';
  const m = meta[item];
  if (!m) return '';
  if (typeof m === 'string') return m;
  return m.description || m.name || '';
}

function renderCatalogPicker(def, initial, catalogSet, onChange, meta = null) {
  const errEl = makeError();
  let values = Array.isArray(initial) ? [...initial] : [];
  let filterText = '';
  let focusedItem = null;
  const items = Array.from(catalogSet).sort();

  const root = el('div', { class: 'catalog-picker' });
  const selectedRow = el('div', { class: 'catalog-picker-selected', 'data-role': 'selected' });
  const search = el('input', {
    type: 'text',
    class: 'catalog-picker-search',
    'data-role': 'search',
    placeholder: `Search ${items.length} options…`,
  });
  const list = el('div', { class: 'catalog-picker-list', 'data-role': 'list' });
  const info = el('div', { class: 'catalog-picker-info', 'data-role': 'info' });

  function paintSelected() {
    selectedRow.innerHTML = '';
    if (values.length === 0) {
      selectedRow.appendChild(el('span', { class: 'muted' }, 'None selected'));
      return;
    }
    for (const v of values) {
      const chip = el('span', { class: 'chip' }, v, ' ');
      const desc = metaDescription(meta, v);
      if (desc) chip.setAttribute('title', desc);
      const x = el('button', { type: 'button', class: 'chip-x' }, '×');
      x.addEventListener('click', () => {
        values = values.filter((y) => y !== v);
        paintSelected();
        paintList();
        paintInfo();
        onChange(values);
      });
      chip.appendChild(x);
      selectedRow.appendChild(chip);
    }
  }

  function paintList() {
    list.innerHTML = '';
    const lc = filterText.toLowerCase();
    const filtered = lc ? items.filter((i) => i.toLowerCase().includes(lc)) : items;
    if (filtered.length === 0) {
      list.appendChild(el('div', { class: 'muted' }, 'No matches.'));
      return;
    }
    for (const item of filtered) {
      const isSelected = values.includes(item);
      const desc = metaDescription(meta, item);
      const itemEl = el('button', {
        type: 'button',
        class: isSelected ? 'catalog-picker-item selected' : 'catalog-picker-item',
        'data-item': item,
        'aria-pressed': isSelected ? 'true' : 'false',
        title: desc || undefined,
        onclick: () => {
          if (values.includes(item)) values = values.filter((x) => x !== item);
          else values = [...values, item];
          focusedItem = item;
          paintSelected();
          paintList();
          paintInfo();
          onChange(values);
        },
      }, item);
      itemEl.addEventListener('mouseenter', () => {
        focusedItem = item;
        paintInfo();
      });
      itemEl.addEventListener('focus', () => {
        focusedItem = item;
        paintInfo();
      });
      list.appendChild(itemEl);
    }
  }

  function paintInfo() {
    info.innerHTML = '';
    if (!meta) {
      info.style.display = 'none';
      return;
    }
    info.style.display = '';
    const subject = focusedItem || values[values.length - 1] || null;
    if (!subject) {
      info.appendChild(el('span', { class: 'muted' },
        'Hover or click an item to see its description.'));
      return;
    }
    const desc = metaDescription(meta, subject);
    info.appendChild(el('strong', {}, subject));
    if (desc) {
      info.appendChild(el('span', { class: 'muted' }, ' — '));
      info.appendChild(el('span', {}, desc));
    } else {
      info.appendChild(el('span', { class: 'muted' }, ' — no description available'));
    }
  }

  search.addEventListener('input', () => {
    filterText = search.value;
    paintList();
  });

  root.appendChild(selectedRow);
  root.appendChild(search);
  root.appendChild(list);
  root.appendChild(info);
  paintSelected();
  paintList();
  paintInfo();

  const wrap = wrapField(def, root, errEl);
  return {
    element: wrap,
    getValue: () => [...values],
    setValue: (v) => {
      values = Array.isArray(v) ? [...v] : [];
      paintSelected();
      paintList();
      paintInfo();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

// ---- human-readable summary for review screens ----

function isNeutral(v) {
  if (v === null || v === undefined || v === false) return true;
  if (v === 0 || v === '') return true;
  if (Array.isArray(v)) return v.length === 0;
  if (typeof v === 'object') return Object.values(v).every(isNeutral);
  return false;
}

function summaryValue(v) {
  if (typeof v === 'boolean') return el('span', { class: 'summary-bool' }, v ? 'yes' : 'no');
  if (typeof v === 'string' || typeof v === 'number') {
    return el('span', { class: 'summary-scalar' }, String(v));
  }
  if (Array.isArray(v)) {
    if (v.every((x) => typeof x !== 'object' || x === null)) {
      const row = el('span', { class: 'summary-chips' });
      for (const x of v) row.appendChild(el('span', { class: 'chip' }, String(x)));
      return row;
    }
    const wrap = el('div', { class: 'summary-items' });
    v.forEach((item, i) => {
      const block = el('div', { class: 'summary-item' });
      block.appendChild(el('div', { class: 'summary-item-head' }, `#${i + 1}`));
      block.appendChild(summaryValue(item));
      wrap.appendChild(block);
    });
    return wrap;
  }
  if (typeof v === 'object' && v !== null) {
    const dl = el('dl', { class: 'summary summary-nested' });
    appendSummaryEntries(dl, v);
    return dl;
  }
  return el('span', {}, String(v));
}

function appendSummaryEntries(dl, obj) {
  for (const [k, v] of Object.entries(obj)) {
    if (isNeutral(v)) continue;
    dl.appendChild(el('dt', {}, k.replace(/_/g, ' ')));
    const dd = el('dd');
    dd.appendChild(summaryValue(v));
    dl.appendChild(dd);
  }
}

/**
 * renderSummary(json) → readable element for review screens. Neutral values
 * (null / [] / {} / 0 / false / "") are hidden — they are still saved, but the
 * summary shows only what the user actually configured.
 */
export function renderSummary(json) {
  const root = el('div', { class: 'summary-root', 'data-role': 'summary' });
  const dl = el('dl', { class: 'summary' });
  appendSummaryEntries(dl, json || {});
  if (dl.children.length === 0) {
    root.appendChild(el('p', { class: 'muted' },
      'All fields use neutral defaults — nothing extra configured.'));
    return root;
  }
  root.appendChild(dl);
  return root;
}

function renderDictOfNumbers(def, initial, onChange, ctx = null) {
  const errEl = makeError();
  let map = { ...(initial || {}) };
  const root = el('div', { class: 'dict-editor' });
  const table = el('table', { class: 'dict' });

  function paint() {
    table.innerHTML = '';
    for (const [k, v] of Object.entries(map)) {
      const row = el('tr');
      row.appendChild(el('td', {}, k));
      const ni = el('input', { type: 'number' });
      ni.value = String(v);
      ni.addEventListener('input', () => {
        map[k] = parseInt(ni.value, 10) || 0;
        onChange({ ...map });
      });
      const td = el('td');
      td.appendChild(ni);
      row.appendChild(td);
      const rmTd = el('td');
      rmTd.appendChild(el('button', {
        type: 'button', class: 'chip-x',
        'data-action': 'remove-key', 'data-key': k,
        onclick: () => {
          delete map[k];
          paint();
          onChange({ ...map });
        },
      }, '×'));
      row.appendChild(rmTd);
      table.appendChild(row);
    }
  }
  paint();
  root.appendChild(table);
  root.appendChild(makeAddKeyRow(def, ctx, () => Object.keys(map), (k) => {
    map[k] = 0;
    paint();
    onChange({ ...map });
  }));
  const wrap = wrapField(def, root, errEl);
  return {
    element: wrap,
    getValue: () => ({ ...map }),
    setValue: (v) => {
      map = { ...(v || {}) };
      paint();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderDictOfBools(def, initial, onChange, ctx = null) {
  const errEl = makeError();
  let map = { ...(initial || {}) };
  const root = el('div', { class: 'dict-editor' });
  const table = el('table', { class: 'dict' });

  function paint() {
    table.innerHTML = '';
    for (const [k, v] of Object.entries(map)) {
      const row = el('tr');
      row.appendChild(el('td', {}, k));
      const cb = el('input', { type: 'checkbox' });
      cb.checked = !!v;
      cb.addEventListener('change', () => {
        map[k] = cb.checked;
        onChange({ ...map });
      });
      const td = el('td');
      td.appendChild(cb);
      row.appendChild(td);
      const rmTd = el('td');
      rmTd.appendChild(el('button', {
        type: 'button', class: 'chip-x',
        'data-action': 'remove-key', 'data-key': k,
        onclick: () => {
          delete map[k];
          paint();
          onChange({ ...map });
        },
      }, '×'));
      row.appendChild(rmTd);
      table.appendChild(row);
    }
  }
  paint();
  root.appendChild(table);
  root.appendChild(makeAddKeyRow(def, ctx, () => Object.keys(map), (k) => {
    map[k] = true;
    paint();
    onChange({ ...map });
  }));
  const wrap = wrapField(def, root, errEl);
  return {
    element: wrap,
    getValue: () => ({ ...map }),
    setValue: (v) => {
      map = { ...(v || {}) };
      paint();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderObject(def, initial, onChange, ctx = null) {
  const errEl = makeError();
  const value = { ...(initial || {}) };
  const box = el('div', { class: 'object-fields' });
  const subFields = {};
  for (const [name, subDef] of Object.entries(def.fields || {})) {
    const sub = renderField(
      { id: name, label: subDef.label || name, ...subDef },
      value[name] ?? null,
      (v) => {
        value[name] = v;
        onChange({ ...value });
      },
      ctx,
    );
    subFields[name] = sub;
    box.appendChild(sub.element);
  }
  const wrap = wrapField(def, box, errEl);
  return {
    element: wrap,
    getValue: () => ({ ...value }),
    setValue: (v) => {
      const next = v || {};
      for (const [name, sub] of Object.entries(subFields)) {
        value[name] = next[name] ?? null;
        sub.setValue(next[name] ?? null);
      }
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderListOfObjects(def, initial, onChange, ctx = null) {
  const errEl = makeError();
  let items = Array.isArray(initial) ? initial.map((x) => ({ ...x })) : [];
  const root = el('div', { class: 'list-of-objects' });

  function neutralItem() {
    const out = {};
    for (const [name, subDef] of Object.entries(def.item_fields || {})) {
      out[name] = subNeutral(subDef);
    }
    return out;
  }

  function subNeutral(subDef) {
    const t = Array.isArray(subDef.type) ? subDef.type[0] : subDef.type;
    switch (t) {
      case 'int': case 'float': return 0;
      case 'bool': return false;
      case 'list_of_strings': case 'list_of_objects': return [];
      case 'dict_of_numbers': case 'dict_of_bools': case 'dict_of_objects': case 'object': return {};
      default: return null;
    }
  }

  function paint() {
    root.innerHTML = '';
    items.forEach((item, i) => {
      const card = el('div', { class: 'object-item', 'data-index': String(i) });
      const head = el('div', { class: 'object-item-head' },
        el('strong', {}, `${def.item_label || 'Item'} ${i + 1}`));
      head.appendChild(el('button', {
        type: 'button', class: 'chip-x',
        'data-action': 'remove-item', 'data-index': String(i),
        onclick: () => {
          items.splice(i, 1);
          paint();
          onChange(items.map((x) => ({ ...x })));
        },
      }, '×'));
      card.appendChild(head);
      for (const [name, subDef] of Object.entries(def.item_fields || {})) {
        const sub = renderField(
          { id: name, label: subDef.label || name, ...subDef },
          item[name] ?? null,
          (v) => {
            item[name] = v;
            onChange(items.map((x) => ({ ...x })));
          },
          ctx,
        );
        card.appendChild(sub.element);
      }
      root.appendChild(card);
    });
    root.appendChild(el('button', {
      type: 'button', 'data-action': 'add-item',
      onclick: () => {
        items.push(neutralItem());
        paint();
        onChange(items.map((x) => ({ ...x })));
      },
    }, `+ Add ${def.item_label || 'item'}`));
  }
  paint();
  const wrap = wrapField(def, root, errEl);
  return {
    element: wrap,
    getValue: () => items.map((x) => ({ ...x })),
    setValue: (v) => {
      items = Array.isArray(v) ? v.map((x) => ({ ...x })) : [];
      paint();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderDictOfObjects(def, initial, onChange, ctx = null) {
  const errEl = makeError();
  let map = {};
  for (const [k, v] of Object.entries(initial || {})) map[k] = { ...v };
  const root = el('div', { class: 'dict-editor' });
  const body = el('div');

  function neutralItem() {
    const out = {};
    for (const [name, subDef] of Object.entries(def.item_fields || {})) {
      const t = Array.isArray(subDef.type) ? subDef.type[0] : subDef.type;
      out[name] = t === 'int' || t === 'float' ? 0 : t === 'bool' ? false : null;
    }
    return out;
  }

  function paint() {
    body.innerHTML = '';
    for (const [k, item] of Object.entries(map)) {
      const card = el('div', { class: 'object-item', 'data-key': k });
      const head = el('div', { class: 'object-item-head' }, el('strong', {}, k));
      head.appendChild(el('button', {
        type: 'button', class: 'chip-x',
        'data-action': 'remove-key', 'data-key': k,
        onclick: () => {
          delete map[k];
          paint();
          emit();
        },
      }, '×'));
      card.appendChild(head);
      for (const [name, subDef] of Object.entries(def.item_fields || {})) {
        const sub = renderField(
          { id: name, label: subDef.label || name, ...subDef },
          item[name] ?? null,
          (v) => {
            item[name] = v;
            emit();
          },
          ctx,
        );
        card.appendChild(sub.element);
      }
      body.appendChild(card);
    }
  }
  function emit() {
    const out = {};
    for (const [k, v] of Object.entries(map)) out[k] = { ...v };
    onChange(out);
  }
  paint();
  root.appendChild(body);
  root.appendChild(makeAddKeyRow(def, ctx, () => Object.keys(map), (k) => {
    map[k] = neutralItem();
    paint();
    emit();
  }));
  const wrap = wrapField(def, root, errEl);
  return {
    element: wrap,
    getValue: () => {
      const out = {};
      for (const [k, v] of Object.entries(map)) out[k] = { ...v };
      return out;
    },
    setValue: (v) => {
      map = {};
      for (const [k, item] of Object.entries(v || {})) map[k] = { ...item };
      paint();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}
