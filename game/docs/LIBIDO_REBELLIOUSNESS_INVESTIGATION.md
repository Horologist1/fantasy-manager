# Investigación: ¿El EXCESO de libido (35/20) crea rebelliousness?

## Pregunta del reporte
El usuario reportó que "el exceso" de libido (p. ej. 35/20) estaba causando que la rebelliousness fuera imposible de bajar. Se quería comprobar si existe alguna ruta en el código donde el **exceso** (libido por encima del máximo) se convierta en rebelliousness.

## Conclusión: **NO existe esa ruta**

En el código actual **no hay ninguna lógica** que convierta el exceso de libido (valor por encima de `max_libido`) en rebelliousness. La única conversión libido → rebelliousness es cuando el libido **baja de 0** (valor negativo).

---

## Rutas revisadas

### 1. `worker_stats.rpy` — `apply_libido_overflow(worker, negative_libido)`
- **Solo se llama** cuando en `regenerate_libido` resulta `new_libido < 0`.
- El "overflow" es `abs(new_libido)` (cuánto se pasó por debajo de cero).
- **No** usa `(libido_actual - max_libido)` ni ningún "exceso" por encima del máximo.

### 2. `worker_traits.rpy` — `set_attribute_with_caps(worker, "libido", value)`
- **Si `value < 0`**: se trata como overflow: se suma `abs(value)` a rebelliousness y libido se pone a 0. Es la única rama que toca rebelliousness por libido.
- **Si `value > max_lib`** (líneas 273–281): solo se hace `value = max_lib` (clamp). **No** se suma `(value - max_lib)` a rebelliousness.
- Por tanto, el exceso sobre el máximo **nunca** se convierte en rebelliousness aquí.

### 3. `event_daily_exec.rpy` — efectos diarios
- `_DAILY_EFFECT_STATS = ("joy", "rebelliousness", "romance", "relationship")`.
- Libido **no** está en la lista; los `daily_effects` de traits/items solo afectan a esos cuatro stats.
- No hay efecto diario que calcule "exceso de libido" ni que sume rebelliousness por libido.

### 4. Otras modificaciones de rebelliousness
- Eventos: consecuencias con `rebelliousness` en JSON (cambios directos al stat).
- `process_next_day`: cuando romance > 80 y rebelliousness > 80 se fuerza rebelliousness a 20; cuando la trabajadora se niega a trabajar se aplica reducción por comfort.
- Ninguna de estas rutas usa "exceso de libido".

---

## Posible confusión del usuario

En el código y en los logs, la palabra **"overflow"** se usa solo para:
- **Libido por debajo de 0** → ese valor (en positivo) se suma a rebelliousness.

No se usa "overflow" para:
- Libido por encima del máximo (35/20). Eso solo se limita al máximo, sin tocar rebelliousness.

Si el usuario leyó "Libido overflow: +X rebelliousness" en un log, es porque ese día el libido **cayó por debajo de 0** (p. ej. por trabajo sexual y regen negativa), no porque tuviera "exceso" 35/20.

---

## Resumen

| Origen                         | ¿Afecta rebelliousness? | ¿Usa exceso (libido > max)? |
|--------------------------------|---------------------------|-----------------------------|
| Libido &lt; 0 (regenerate_libido) | Sí (+ overflow)           | No                          |
| Libido &lt; 0 (set_attribute_with_caps) | Sí (+ overflow)           | No                          |
| Libido &gt; max (set_attribute_with_caps) | No (solo clamp)            | No (solo se limita)         |
| daily_effects (traits/items)   | Solo si el efecto es "rebelliousness" | No (libido no en daily_effects) |
| Eventos / consecuencias        | Solo si el JSON lo indica | No                          |

**No es posible** en el código actual que el exceso (35−20=15) cree rebelliousness. Si la rebelliousness subía mucho, las causas plausibles son:
1. Overflow por libido **negativo** (regen negativa día a día).
2. Efectos diarios de traits/items que suben rebelliousness.
3. Consecuencias de eventos que suben rebelliousness.
