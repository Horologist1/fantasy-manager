# skill_modifiers en eventos — IMPLEMENTADO

Los eventos pueden modificar skills (Charm, etc.) mediante `effect.skill_modifiers` en sus choices. Implementado en `apply_effects` (script.rpy).

## Uso

En el JSON del evento, en `effect`, `effect.success` o `effect.failure`:

```json
"skill_modifiers": { "Charm": 3 }
```

- Requiere que el evento tenga un worker asignado (worker_selection "random" o "choose" con worker_name).
- Usa `modify_base_skill` de worker_stats.rpy (cap 0–100).
- Muestra notificación cuando el cambio es distinto de cero.

## Eventos que lo usan

- Toda la cadena en `game/data/events/events_aelis_chain.json`.
