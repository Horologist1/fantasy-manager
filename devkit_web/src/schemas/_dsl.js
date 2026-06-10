/**
 * Supported field types:
 *   "string", "longtext", "int", "float", "bool",
 *   "enum"           (requires options: string[])
 *   "list_of_strings"
 *   "list_of_objects" (requires schema: <schemaId>)
 *   "dict_of_numbers"
 *   "formula"         (validated as string at this layer)
 *   Array form: ["string", "list_of_strings", "null"] — union; valid if any member validates.
 */

export function neutralDefault(def) {
  const t = Array.isArray(def.type) ? def.type[0] : def.type;
  switch (t) {
    case 'string':
    case 'longtext':
    case 'formula':
    case 'enum':
      return null;
    case 'int':
    case 'float':
      return 0;
    case 'bool':
      return false;
    case 'list_of_strings':
    case 'list_of_objects':
      return [];
    case 'dict_of_numbers':
      return {};
    case 'null':
      return null;
    default:
      return null;
  }
}

function validateSingle(type, def, value) {
  if (value === null || value === undefined) {
    if (def.required) return { valid: false, error: 'required' };
    return { valid: type === 'null' || !def.required, error: null };
  }
  switch (type) {
    case 'null':
      return value === null
        ? { valid: true, error: null }
        : { valid: false, error: 'expected null' };
    case 'string':
    case 'longtext':
    case 'formula':
      return typeof value === 'string'
        ? { valid: true, error: null }
        : { valid: false, error: 'expected string' };
    case 'enum':
      return def.options?.includes(value)
        ? { valid: true, error: null }
        : { valid: false, error: `expected one of ${JSON.stringify(def.options)}` };
    case 'int':
      if (typeof value !== 'number' || !Number.isInteger(value)) {
        return { valid: false, error: 'expected integer' };
      }
      if (def.min != null && value < def.min) return { valid: false, error: `min ${def.min}` };
      if (def.max != null && value > def.max) return { valid: false, error: `max ${def.max}` };
      return { valid: true, error: null };
    case 'float':
      if (typeof value !== 'number' || Number.isNaN(value)) {
        return { valid: false, error: 'expected number' };
      }
      if (def.min != null && value < def.min) return { valid: false, error: `min ${def.min}` };
      if (def.max != null && value > def.max) return { valid: false, error: `max ${def.max}` };
      return { valid: true, error: null };
    case 'bool':
      return typeof value === 'boolean'
        ? { valid: true, error: null }
        : { valid: false, error: 'expected boolean' };
    case 'list_of_strings':
      if (!Array.isArray(value)) return { valid: false, error: 'expected array' };
      for (const item of value) {
        if (typeof item !== 'string') return { valid: false, error: 'expected string items' };
      }
      return { valid: true, error: null };
    case 'list_of_objects':
      if (!Array.isArray(value)) return { valid: false, error: 'expected array' };
      for (const item of value) {
        if (typeof item !== 'object' || item === null || Array.isArray(item)) {
          return { valid: false, error: 'expected object items' };
        }
      }
      return { valid: true, error: null };
    case 'dict_of_numbers':
      if (typeof value !== 'object' || value === null || Array.isArray(value)) {
        return { valid: false, error: 'expected object' };
      }
      for (const v of Object.values(value)) {
        if (typeof v !== 'number') return { valid: false, error: 'expected number values' };
      }
      return { valid: true, error: null };
    default:
      return { valid: false, error: `unknown type ${type}` };
  }
}

export function validateField(def, value) {
  const types = Array.isArray(def.type) ? def.type : [def.type];
  if (value === null || value === undefined) {
    if (def.required) return { valid: false, error: 'required' };
    return { valid: true, error: null };
  }
  let lastError = null;
  for (const t of types) {
    const r = validateSingle(t, def, value);
    if (r.valid) return r;
    lastError = r.error;
  }
  return { valid: false, error: lastError || 'no matching type' };
}
