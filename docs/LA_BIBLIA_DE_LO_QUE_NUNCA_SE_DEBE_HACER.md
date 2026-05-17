# La Biblia de lo que nunca se debe hacer

Documento de referencia para evitar bugs recurrentes en Fantasy Manager (Ren'Py).

---

## 1. Dict vs RevertableDict — El error más común

### El problema

En Ren'Py, muchas estructuras de datos (workers, buildings, items, etc.) **no son `dict` de Python puro**. Son `RevertableDict`, `RevertableList` y otras clases de Ren'Py para soportar rollback/save/load.

```python
# MAL — NUNCA hagas esto
if isinstance(w, dict):  # Siempre False para RevertableDict
    ...

workers = [w for w in store.workers if isinstance(w, dict)]  # Lista vacía
```

**Resultado:** Filtros que devuelven listas vacías, bucles que no iteran, pantallas en blanco.

### La solución

Usa **comportamiento dict-like**, no el tipo:

```python
# BIEN — Comprueba que tenga .get() y datos válidos
def _is_worker(w):
    return hasattr(w, "get") and w.get("name")

workers = [w for w in store.workers if _is_worker(w)]
```

Para listas dict-like:

```python
# BIEN — Para estructuras que actúan como dict
if hasattr(obj, "get") and obj.get("clave"):
    ...
```

### Dónde aplica

- `store.workers` → RevertableDict cada worker
- `store.available_buildings` → valores son RevertableDict
- `building["assigned_servants"]` → RevertableList de RevertableDict
- `worker["inventory"]` → RevertableList
- Cualquier dato que viene del store o se guarda/carga

### Regla de oro

> **Nunca uses `isinstance(x, dict)` ni `isinstance(x, list)` para datos del juego.  
> Usa `hasattr(x, "get")` para dict-like, `hasattr(x, "__iter__")` para list-like.**

---

## 2. Acceso seguro a claves

### El problema

```python
# MAL — KeyError si la clave no existe
total = building["skill"] + building["skill_bonus"]
```

### La solución

```python
# BIEN — .get() con valor por defecto
total = building.get("skill", 10) + building.get("skill_bonus", 0)
```

---

## 3. Comparación de claves de edificios

### El problema

En el juego coexisten formatos `"Building 1"` y `"Building_1"`. Si solo comparas uno, fallas en partidas cargadas o en ciertos flujos.

### La solución

Siempre acepta ambos formatos:

```python
_keys = [building_name]
if " " in building_name and building_name.startswith("Building "):
    _keys.append("Building_" + building_name.replace("Building ", "", 1).strip())
elif "_" in building_name and building_name.startswith("Building_"):
    _keys.append("Building " + building_name.split("_", 1)[1])

# Luego filtra con: w.get("assigned_building") in _keys
```

O usa `_norm_building_key()` si ya existe en el código.

---

## 4. Variables de pantalla y ámbito

### El problema

En pantallas Ren'Py, los bloques `python:` definen variables locales. Si hay problemas de timing, predicción o capas, esas variables pueden no estar disponibles donde las usas.

### La solución

- Para datos que deben existir antes del render: usa una **acción** (Function) que escriba en `store` y que la pantalla lea de `store`.
- Para listas calculadas: calcularlas en el mismo `python:` que las consume y en el mismo render, no depender de acciones `on show` que se ejecuten después.

---

## 5. Resumen rápido

| No hacer | Hacer en su lugar |
|----------|-------------------|
| `isinstance(x, dict)` | `hasattr(x, "get")` |
| `isinstance(x, list)` | `hasattr(x, "__iter__")` o `callable(getattr(x, "__iter__", None))` |
| `obj["clave"]` sin fallback | `obj.get("clave", default)` |
| Comparar solo `"Building 1"` | Aceptar `"Building 1"` y `"Building_1"` |
| Confiar en que `on show` corre antes del render | Calcular en la pantalla o guardar en store desde una acción fiable |
| `store.foo = local_fn` dentro de un `python:` block de un screen | Llamar directamente al closure hermano, o exponer la función desde `init python` (módulo). Ver §8 — rompe los saves de toda la sesión, incluso si luego lo borras (rollback log) |

---

## 6. Texto de training y Ren'Py

### Copy en datos, no en `.rpy`

- Todo el **texto jugable** del flujo de training (intros, resultados, etiquetas de menú, previews de stats en opciones) debe vivir en `game/data/interactions/interactions_training.json`.
- La fila meta `id: "_training_flow_copy"` agrega `training_flow_ui` y `training_stat_preview`; **no es una interacción**: se filtra en el menú y solo sirve de contenedor de strings compartidos.

### Sustitución y pantallas

- Los intros usan plantillas `{name}`, `{focus}`, `{subj}`, etc.; se resuelven en **Python** (`training_substitute_intro_tokens`) **antes** de pasar la cadena a la pantalla.
- `training_branch_narration` muestra el texto con `text "[_tbm_cap!q]"`: el modificador `!q` cita/escapa el contenido para que corchetes y llaves no disparen sustituciones Ren'Py accidentales. No metas en JSON secuencias tipo `[variable]` pensando que son del motor salvo que sepas cómo se escapan.

### Dict-like al leer JSON

- Las entradas cargadas con `json.load` son `dict` normales, pero el código que lee **workers** o **store** debe seguir la regla de la §1 (`hasattr(x, "get")`, no `isinstance(..., dict)`).

---

## 7. JSON.load dentro de bloques `python:` de story labels

### El problema

Confirmado empíricamente en mayo 2026 (ending dominion de Yvara). Aunque `json.loads`/`json.load` devuelve a nivel de módulo Python tipos planos (`dict`, `list`), **dentro de un bloque `python:` que corre durante un story label** los nombres `dict` y `list` no resuelven al builtin: resuelven a `RevertableDict`/`RevertableList`. Por tanto:

```python
python:
    import json
    with renpy.file("data/workers/yvara.json") as f:
        data = json.loads(f.read().decode("utf-8"))
    # data es una lista per repr (`type=list`), pero…
    item = data[0]
    isinstance(item, dict)  # → False  (compara contra RevertableDict, no contra dict builtin)
```

**Resultado:** ramas `if isinstance(...)` que parecen lógicas y nunca disparan, valores válidos rechazados, fallbacks que se activan sin razón aparente. Un `except` no se entera porque no hay excepción — solo silencio.

### La solución

Misma regla que §1, sin excepciones por origen del dato:

```python
python:
    import json
    with renpy.file("data/workers/yvara.json") as f:
        data = json.loads(f.read().decode("utf-8"))
    # Duck-typing — funciona para dict, RevertableDict, OrderedDict, etc.
    if hasattr(data, "get"):
        worker = data
    elif hasattr(data, "__iter__"):
        worker = next((e for e in data if hasattr(e, "get")), None)
```

### Diferencia clave con §6

§6 decía que las entradas cargadas con `json.load` son `dict` normales. **Eso solo es cierto en `init python:`** (donde `dict` es el builtin estándar). En bloques `python:` de story labels, `dict` está sombreado y `isinstance(plain_dict, dict)` falla porque está comprobando contra `RevertableDict` (subclase, no superclase).

### Regla ampliada

> Tanto si los datos vienen del store como si los acabas de parsear con `json.loads`, **nunca** uses `isinstance(x, dict/list)` dentro de un bloque `python:` de un story label. Usa `hasattr(x, "get")` o `hasattr(x, "__iter__")`.

---

## 8. NUNCA asignar funciones locales de un screen a `store.*`

### El problema

Cuando dentro del `python:` block de un `screen X:` haces algo como:

```renpy
screen manager_inventory:
    python:
        def foo():
            ...
        store._mi_foo = foo   # <-- ESTO ROMPE LOS SAVES PERMANENTEMENTE
```

Lo que parece inocuo destruye el sistema de saves de la sesión completa. Síntomas (todos reales, vistos en producción):

- El primer save funciona si la pantalla nunca se abrió antes.
- En cuanto la pantalla se abre **una sola vez**, los siguientes saves fallan con:
  ```
  _pickle.PicklingError: Can't pickle <function foo at 0x...>:
  attribute lookup foo on store failed
  ```
- El usuario ve solo un genérico "Snapshot save failed. Save cancelled."
- Recargar restaura saves temporalmente — hasta que la pantalla se vuelva a abrir.

### Por qué pasa (importante, porque condiciona el fix)

Ren'Py guarda dos cosas al hacer `FileSave`: `roots` (el store actual) **y el rollback log** (`renpy.game.log`). El rollback log contiene **deltas históricos** de cada mutación a `store.*`. Cuando hiciste `store._mi_foo = foo`, ese delta capturó la referencia a `foo`.

> Aunque después pongas `store._mi_foo = None` o hagas `del store._mi_foo`, **el delta histórico sigue en el rollback log y pickle lo intentará serializar**. Solución de "limpiar antes de guardar" → NO funciona.

Pickle busca la función por nombre (`foo.__name__ = "foo"`) en su módulo (`store`). La función es local del screen, no está en `store.foo` (solo en `store._mi_foo`), así que la búsqueda falla y revienta el save entero.

### Qué SÍ es seguro

- `Function(local_fn, ...)` como `action` de un widget. **Funciona** porque el árbol de displayables NO se serializa con la sesión — se reconstruye desde cero al cargar la partida (re-ejecutando los screens).
- Funciones definidas en `init python` (módulo) asignadas a `store.X` — son picklables porque pickle las encuentra como `store.X`.
- Llamar a una función hermana del mismo `python:` block **capturándola como default arg** (binding at def time):
  ```renpy
  screen X:
      python:
          def worker():
              ...
          # helper se define DESPUÉS y captura `worker` en sus defaults.
          # Late-binding directo NO funciona: los defs dentro de un screen
          # python: block tienen __globals__ = renpy.store, NO el scope del
          # screen, así que el nombre `worker` no es visible al llamar a helper.
          def helper(_w=worker):
              _w()
  ```
  **Anti-pattern: late-binding directo a sibling** (`def helper(): worker()` con `worker` definido más abajo) → `NameError` cuando se invoca via Function() action.

### Qué NO es seguro

- `store.foo = local_fn` cuando `local_fn` está dentro de un `python:` block de un screen.
- Cualquier patrón que persista una closure local en `store.*` (aunque la vuelvas a borrar luego — el rollback log la captura).

### Regla de oro

> Si una función está definida dentro del `python:` block de un screen, **JAMÁS** la asignes a `store.*`. Úsala como closure local (llamada directa) o pásala via `Function(local_fn, ...)` a un widget action. Si necesitas exponerla globalmente, define una versión en `init python` (módulo).

### Smoke test manual (30 segundos)

Cada vez que toques `screens.rpy`, `save_snapshot.rpy`, o cualquier `store.*` desde el cuerpo de un screen, antes de commit:

1. Cierra el juego (cierra el `.exe`, no solo reload — Ren'Py mantiene bytecode en memoria).
2. Abre fresh → empieza/carga partida.
3. **Pasa por el screen que modificaste al menos una vez** (este paso es crítico — el bug solo aparece tras renderizar el screen).
4. Abre el menú de save → Save slot 1 → debe completarse (no notify rojo).
5. Sin recargar nada, Save slot 1 OTRA VEZ → debe completarse.
6. Load slot 1 → save de nuevo → debe completarse.

Si los 3 saves pasan, el cambio no introdujo regresión de pickle/rollback. Si alguno falla, mira `log.txt` — la notify nueva incluye el tipo de excepción.

### Caso histórico (mayo 2026)

Commit `24aa071` ("9.5.5 wip", Apr 26) introdujo en el screen `manager_inventory` 4 bridges:

```renpy
store._mi_transfer_to_right = transfer_to_right
store._mi_transfer_to_left = transfer_to_left
store._mi_sell_item = sell_item
store._mi_buy_item_from_shop = buy_item_from_shop
```

para que el helper `handle_inventory_row_click` (también local del mismo screen) pudiera llamarlas vía `getattr(store, "_mi_*", None)`. Funcional en sesión, pero rompió los saves desde la primera apertura del inventario.

**Fix correcto** (mayo 2026, segunda iteración): borrar los 4 bridges Y mover la definición de `handle_inventory_row_click` a DESPUÉS de las cuatro funciones hermanas, capturándolas via default args (`def handle_inventory_row_click(..., _sell=sell_item, _buy=buy_item_from_shop, _to_right=transfer_to_right, _to_left=transfer_to_left)`). El primer intento (llamada directa con late-binding) crasheaba con `NameError: name 'buy_item_from_shop' is not defined` al hacer doble-click en la tienda — los defs dentro del screen python: block tienen `__globals__ = renpy.store`, no el scope del screen, así que sibling lookups fallan en runtime. Default args evalúan a def-time y bakean las referencias.

### Grep de verificación manual

Cuando edites cualquier `.rpy` con screens, antes de dar por bueno el cambio:

```
grep -nE "^      +store\.[_a-zA-Z][_a-zA-Z0-9]*[[:space:]]*=[[:space:]]*[a-z_][a-zA-Z0-9_]*[[:space:]]*$" game/scripts/core/screens.rpy game/scripts/**/*.rpy
```

Cualquier match con 6+ espacios de indent que asigne un identificador local a `store.*` es candidato a romper saves. Inspecciona: si el RHS es una función definida en el mismo `python:` block del screen, **MAL**. Si es una constante (True/False/None), un valor literal, o un identifier que apunta a una función definida en `init python`, OK.

---

## 9. `textbutton expr` con texto que viene de JSON

### El problema

Pattern peligroso visto en `screens.rpy:2969` (`random_event_choice`) y `screens.rpy:3256` (`recruitment_choice_screen`):

```renpy
textbutton choice["option"] action Return(choice)
```

Ren'Py evalúa la expresión Python, obtiene el string, y luego aplica `substitute()` sobre el resultado buscando `[...]` y `{...}` para interpolar. Si el string contiene cualquier `[algo]` literal — un placeholder no resuelto, un `[Nota: ...]` que el escritor metió en una descripción de option, o un `{tag}` malformado — Ren'Py intenta evaluar el contenido como Python expression / text tag y lanza:

```
SyntaxError: invalid syntax (<none>, line 1)
```

Confirmado en `traceback.txt` de v0.9.5.5t1 (May 2026).

El error es especialmente insidioso porque los placeholders válidos (`[player_title]`, `[event_worker]`, `[COST]`) se reemplazan ANTES de la pantalla, pero cualquier `[...]` que el código no anticipa pasa directo al `textbutton` y crashea.

### La solución

Envolver la expresión en una string interpolada con el modificador `!q` (quote):

```renpy
textbutton "[choice['option']!q]" action Return(choice)
```

`!q` aplica un quote pass sobre el resultado de la interpolación: `[` → `[[`, `{` → `{{`. Esto **inhibe la re-interpolación** del Text displayable. Cualquier `[Algo]` o `{tag}` residual aparece como texto literal en pantalla en vez de crashear.

### Cuándo `!q` es el patrón correcto

- Cualquier `textbutton`, `text`, o `say` que pase texto viniendo de:
  - JSON (events, workers, items)
  - Input del jugador (custom_names, custom player_title)
  - Mods
  - Saves antiguos que podrían contener strings con sintaxis no soportada por la versión actual

### Cuándo NO usar `!q`

- Strings hardcoded en `.rpy` con `[var]` legítimos que SÍ quieres interpolar — esos son control del programador, no riesgo de inyección.
- Strings con tags Ren'Py legítimos (`{b}`, `{i}`, `{color=}`) — `!q` los rompería. Si el JSON usa tags intencionalmente, sanitiza solo `[` por otro lado o haz un substitute manual antes.

### Cómo detectar el anti-pattern

```
grep -nE "textbutton [a-z_]+\[" game/scripts/**/*.rpy
```

Cualquier match es candidato. Reemplazar por `"[expr_aquí!q]"`.

---

*Última actualización: mayo 2026. Añade entradas nuevas cuando encuentres patrones problemáticos.*
