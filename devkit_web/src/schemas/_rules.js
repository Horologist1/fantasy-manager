// Shared rule helpers for content schemas.

/** true when every string in list exists in the catalog Set (missing catalog passes). */
export function allIn(catalogSet, list) {
  if (!catalogSet) return true;
  return (list || []).every((x) => typeof x !== 'string' || catalogSet.has(x));
}

/** Normalizes string-or-list-or-null to a list. */
export function asList(v) {
  if (v == null) return [];
  return Array.isArray(v) ? v : [v];
}

export const OUTCOMES = ['failure', 'mediocre', 'success', 'critical_success'];
