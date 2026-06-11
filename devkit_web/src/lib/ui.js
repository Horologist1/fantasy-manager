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
      return renderDictOfNumbers(def, initial, onChange);
    default:
      return renderText(def, initial == null ? '' : String(initial), onChange, ctx);
  }
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
  sel.addEventListener('change', () => onChange(sel.value));
  const wrap = wrapField(def, sel, errEl);
  return {
    element: wrap,
    getValue: () => sel.value,
    setValue: (v) => (sel.value = v == null ? '' : v),
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderListOfStrings(def, initial, onChange, ctx) {
  // Catalog-backed: render a visible browsable picker so the user can discover
  // valid values instead of guessing them from memory. Without a catalog we
  // fall back to a free-text chip input.
  if (def.catalog && ctx?.catalogs?.[def.catalog]) {
    return renderCatalogPicker(def, initial, ctx.catalogs[def.catalog], onChange);
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

function renderCatalogPicker(def, initial, catalogSet, onChange) {
  const errEl = makeError();
  let values = Array.isArray(initial) ? [...initial] : [];
  let filterText = '';
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

  function paintSelected() {
    selectedRow.innerHTML = '';
    if (values.length === 0) {
      selectedRow.appendChild(el('span', { class: 'muted' }, 'None selected'));
      return;
    }
    for (const v of values) {
      const chip = el('span', { class: 'chip' }, v, ' ');
      const x = el('button', { type: 'button', class: 'chip-x' }, '×');
      x.addEventListener('click', () => {
        values = values.filter((y) => y !== v);
        paintSelected();
        paintList();
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
      const itemEl = el('button', {
        type: 'button',
        class: isSelected ? 'catalog-picker-item selected' : 'catalog-picker-item',
        'data-item': item,
        'aria-pressed': isSelected ? 'true' : 'false',
        onclick: () => {
          if (values.includes(item)) values = values.filter((x) => x !== item);
          else values = [...values, item];
          paintSelected();
          paintList();
          onChange(values);
        },
      }, item);
      list.appendChild(itemEl);
    }
  }

  search.addEventListener('input', () => {
    filterText = search.value;
    paintList();
  });

  root.appendChild(selectedRow);
  root.appendChild(search);
  root.appendChild(list);
  paintSelected();
  paintList();

  const wrap = wrapField(def, root, errEl);
  return {
    element: wrap,
    getValue: () => [...values],
    setValue: (v) => {
      values = Array.isArray(v) ? [...v] : [];
      paintSelected();
      paintList();
    },
    setError: (m) => setErr(errEl, wrap, m),
  };
}

function renderDictOfNumbers(def, initial, onChange) {
  const errEl = makeError();
  let map = { ...(initial || {}) };
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
      table.appendChild(row);
    }
  }
  paint();
  const wrap = wrapField(def, table, errEl);
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
