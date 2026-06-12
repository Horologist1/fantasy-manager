// devkit_web/src/recipes/_engine.js
import { renderField } from '../lib/ui.js';

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

export function runRecipe(recipe, container, opts = {}) {
  const { modname = 'mymod', ctx = {} } = opts;
  const answers = {};
  for (const step of recipe.steps) {
    if ('default' in step) answers[step.id] = step.default;
  }
  let index = 0;

  return new Promise((resolve) => {
    function paint() {
      container.innerHTML = '';
      if (index < recipe.steps.length) {
        paintStep();
      } else {
        paintReview();
      }
    }

    function paintStep() {
      const step = recipe.steps[index];
      const wrap = el('div', { 'data-step': step.id, class: 'recipe-step' });
      wrap.appendChild(el('h2', {}, recipe.title));
      wrap.appendChild(el('div', { class: 'progress' },
        `Step ${index + 1} of ${recipe.steps.length}: ${step.label || step.id}`));

      // options / option_descriptions may depend on earlier answers
      // (e.g. profession list depends on the chosen building).
      const def = { ...step };
      if (typeof def.options === 'function') def.options = def.options(ctx, answers);
      if (typeof def.option_descriptions === 'function') {
        def.option_descriptions = def.option_descriptions(ctx, answers);
      }
      if (def.type === 'enum' && answers[def.id] == null && def.options?.length) {
        answers[def.id] = def.options[0];
      }

      const field = renderField(def, answers[step.id] ?? null, (v) => {
        answers[step.id] = v;
        field.setError('');
      }, ctx);
      wrap.appendChild(field.element);

      const nav = el('div', { class: 'nav' });
      if (index > 0) {
        nav.appendChild(el('button', {
          type: 'button',
          'data-action': 'back',
          onclick: () => { index--; paint(); },
        }, 'Back'));
      }
      nav.appendChild(el('button', {
        type: 'button',
        'data-action': 'next',
        onclick: () => {
          if (step.required && (answers[step.id] == null || answers[step.id] === '')) {
            field.setError('required');
            return;
          }
          index++;
          paint();
        },
      }, index === recipe.steps.length - 1 ? 'Review' : 'Next'));
      wrap.appendChild(nav);

      container.appendChild(wrap);
    }

    function paintReview() {
      const json = recipe.build(answers, ctx);
      const filename = recipe.default_output.replace('<modname>', modname);

      const wrap = el('div', { 'data-step': 'review', class: 'recipe-step' });
      wrap.appendChild(el('h2', {}, 'Review & save'));

      const pre = el('pre', { class: 'json-preview' }, JSON.stringify(json, null, 2));
      wrap.appendChild(pre);

      const fnameLabel = el('label', {}, 'Filename');
      const fnameInput = el('input', { type: 'text', 'data-action': 'filename' });
      fnameInput.value = filename;
      wrap.appendChild(fnameLabel);
      wrap.appendChild(fnameInput);

      const nav = el('div', { class: 'nav' });
      nav.appendChild(el('button', {
        type: 'button',
        'data-action': 'back',
        onclick: () => { index--; paint(); },
      }, 'Back'));
      nav.appendChild(el('button', {
        type: 'button',
        'data-action': 'save',
        onclick: () => {
          resolve({ json, filename: fnameInput.value || filename });
        },
      }, 'Save'));
      wrap.appendChild(nav);

      container.appendChild(wrap);
    }

    paint();
  });
}
