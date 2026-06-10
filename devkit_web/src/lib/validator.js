import { validateField } from '../schemas/_dsl.js';

export function validateEntry(entry, schema, ctx) {
  const errors = [];
  const warnings = [];
  const migrations = [];

  // 1. Field validation
  for (const [name, def] of Object.entries(schema.fields)) {
    if (!(name in entry)) {
      if (def.required) {
        errors.push({ field: name, error: 'required', rule: null });
      }
      continue;
    }
    const r = validateField(def, entry[name]);
    if (!r.valid) errors.push({ field: name, error: r.error, rule: null });
  }

  // 2. Legacy field detection
  if (schema.legacy) {
    for (const [legacyName, info] of Object.entries(schema.legacy)) {
      if (legacyName in entry) {
        migrations.push({ from: legacyName, to: info.migrates_to });
      }
    }
  }

  // 3. Rules
  for (const rule of schema.rules || []) {
    let passed = true;
    try {
      passed = rule.check(entry, ctx);
    } catch {
      passed = false;
    }
    if (!passed) {
      const out = { rule: rule.id, field: rule.field || null, message: rule.message };
      if (rule.severity === 'error') errors.push(out);
      else warnings.push(out);
    }
  }

  return { errors, warnings, migrations };
}

export function applyMigrations(entry, schema) {
  if (!schema.legacy) return { ...entry };
  const out = { ...entry };
  for (const [legacyName, info] of Object.entries(schema.legacy)) {
    if (legacyName in out) {
      const newVal = info.as(out[legacyName]);
      const target = info.migrates_to;
      if (Array.isArray(out[target])) {
        out[target] = [...out[target], ...(Array.isArray(newVal) ? newVal : [newVal])];
      } else {
        out[target] = newVal;
      }
      delete out[legacyName];
    }
  }
  return out;
}
