# Arena Mechanics – Design & Implementation Plan

## Objetivo

La Arena debe funcionar **como la Academy**: un edificio especial que el manager no “gestiona” directamente, al que se envían workers. Los workers participan en combates/espectáculos según su rol (nivel de riesgo), ganan dinero y reputación, entrenan Combat y pueden sufrir lesiones. Todo sin romper lo existente (trial de desbloqueo, pase de Lanista, add_arena_building).

---

## Inspiración histórica (resumen)

- **Roma**: munus, lanista, ludus; gladiadores como inversión (no siempre a muerte); rudis (espada de madera = libertad); tipos (murmillón, retiario, etc.); árbitro y reglas.
- **Medieval**: torneos por rondas, rescates, premios, requisitos de armadura/armas, grados de riesgo (justa, melee, a ultranza).

Se traduce en: **tiers de combate** (bajo/medio/alto riesgo), **apuestas/bolsas**, **requisito opcional de ítem/licencia** para tiers medios/altos, **consecuencias** (energía, salud, rasgos como Scarred).

---

## Sistema propuesto

### 1. Modelo del edificio (como Academy)

- **Arena** está en `available_buildings` con `owned: True` al desbloquearla (sin añadirla a `owned_buildings` para no pasarla por el bucle genérico de edificios).
- **show_in_manage_buildings**: `false` (como Academy), para que no aparezca en “gestionar edificios” como negocio que se sube de nivel.
- Los workers se asignan a **Arena** y eligen un **rol** = tier de combate (Exhibition / Proving / Championship).

### 2. Tres profesiones (tiers de combate)

Cada una es un “curso” al que se asigna al worker en la Arena:

| Tier | ID profesión | Nombre (UI) | Riesgo | Recompensa | Requisito sugerido |
|------|-----------------------------|-------------|--------|------------|---------------------|
| Bajo | `arena_exhibition` | Exhibition fighter | Sin muerte; poca salud | Poco dinero/rep; +Combat XP | Ninguno |
| Medio | `arena_proving` | Proving fighter | Posible lesión (health, Scarred) | Dinero/rep medio | Opcional: licencia o N victorias exhibition |
| Alto | `arena_championship` | Championship fighter | Riesgo alto (health bajo puede “caer”) | Mucho dinero/rep; posible loot | Combat alto o ítem (Arena Champion's Blade) |

- **Exhibition**: combate controlado, sin muerte, -energía, poco dinero, reputación baja, sube Combat (training_skills_distribution).
- **Proving**: combate serio, consecuencias failure/mediocre: -health, posibilidad de rasgo Scarred; success/critical: buena bolsa y reputación.
- **Championship**: bolsas y reputación altas; failure/critical_failure puede dejar al worker muy herido (health bajo) o “no se levanta” (sin muerte permanente si no se desea; se puede limitar a health=0 y rasgo Scarred).

### 3. Apuestas / bolsas

- **Dinero**: fórmula por resultado (success/critical_success/mediocre/failure), escalada por tier (exhibition &lt; proving &lt; championship). Ejemplo: exhibition 50–200, proving 200–600, championship 500–1500 (con crítico el doble o similar).
- **Reputación**: igual que otros edificios (success +5, critical +10, failure -5, etc.), aplicada al edificio Arena si se guarda `building["reputation"]` para la Arena en `available_buildings["Arena"]`.

### 4. Ítems y requisitos (opcional, fase 2)

- **Licencia de arena** (ej. `arena_licence` o “rudis”): ítem que permite o mejora el tier Proving (comprar en promotor o desbloquear tras X victorias en Exhibition).
- **Championship**: exigir Combat ≥ umbral (ej. 40) o poseer/equipar **Arena Champion's Blade** (ya existe). Si no cumple, no se puede asignar al rol Championship (o se fuerza Exhibition/Proving en la UI).

### 5. Prueba previa (opcional)

- “Prueba previa” puede ser:
  - El **trial actual** (un combate para desbloquear la Arena) — ya existe.
  - O un **requisito por tier**: por ejemplo, no poder entrar a Proving hasta N días en Exhibition o hasta tener la licencia. Esto se puede comprobar en la UI (job_selection) y en el bloque diario de Arena.

### 6. Flujo diario (como Academy)

- En `process_daily_events()` (event_daily_exec.rpy), **después del bloque de Academy**:
  1. Si `arena_unlocked` y `"Arena" in available_buildings`:
  2. Obtener `workers_by_building.get("Arena", [])`.
  3. Para cada worker, leer su job (`servant_jobs` del edificio Arena): `arena_exhibition`, `arena_proving` o `arena_championship`.
  4. Según el job, ejecutar **un** combate de ese tier:
     - Roll de Combat (misma lógica que `run_arena_trial`: skill + bonus, bands critical/success/mediocre/failure/critical_failure).
     - Aplicar consecuencias (energía, salud, joy, reputación, dinero).
     - En failure/mediocre en proving/championship: posibilidad de aplicar Scarred (add_trait_with_duration) o bajar health.
  5. Dar **Combat XP** (como Academy: `add_arena_combat_skill_uses(worker, tier)` o reutilizar lógica de training_skills_distribution).
  6. Añadir entrada a `daily_report` (building "Arena", profession name, worker, description, result, earnings, used_skill Combat, story_image si hay).

- **No** modificar el bucle principal de edificios para la Arena: o bien **no** se añade "Arena" a `owned_buildings`, o bien al inicio del bucle se hace `if building.get("type") == "arena": continue` para saltarla y procesarla solo en este bloque dedicado.

### 7. Datos en JSON (special_buildings.json)

- **Arena**: mantener `id`, `name`, `skill_name`, `skill_description`, `show_in_manage_buildings: false`, `allowed_map_locations: ["arena"]`.
- **Profesiones**: sustituir la única profesión actual por tres:
  - `arena_exhibition`: name "Exhibition fighter", description corta, `skills: ["Combat"]`, `training_skills_distribution: {"Combat": 10}`, `max_daily_workers`: 5 o 10, `daily_story_count: {"base": 1}`, y **daily_stories** mínimos (solo para compatibilidad si algo los lee; el contenido real lo genera el bloque Python).
  - `arena_proving`: igual con "Proving fighter".
  - `arena_championship`: "Championship fighter".

Si el bloque diario de Arena **no** usa los daily_stories del JSON (solo usa profession id y nombre), se pueden dejar 1 story stub por profesión para no romper ningún código que itere daily_stories.

### 8. UI (screens.rpy)

- **arena_menu** / **arena_training_menu**: actualizar texto y botones:
  - “Train workers” → lleva a asignar workers a Arena y elegir rol (Exhibition / Proving / Championship).
  - Descripciones por rol: riesgo, recompensas, requisitos (ej. “Championship: high Combat or Champion's Blade recommended”).
- **job_selection**: ya muestra profesiones del building type; al elegir Arena, deben aparecer las tres nuevas profesiones (arena_exhibition, arena_proving, arena_championship). Solo hace falta que `building_types_json` (con special_buildings mergeado) contenga esas profesiones en el tipo `arena`.

### 9. Qué no tocar

- **script.rpy**: `add_arena_building()`, `run_arena_trial()`, labels `arena_first_dialogue`, `arena_permit_menu`, `arena_combatant_menu`, `arena_do_trial`, `arena_run_trial_and_result` — no cambiar; solo se añade lógica nueva (bloque diario, profesiones en JSON).
- **Desbloqueo**: sigue siendo pago de Lanista + trial con un combatiente. Tras éxito, la Arena queda disponible y los workers pueden asignarse a los tres roles.
- **Ítems existentes**: Arena Champion's Blade se usa como requisito o bonus para Championship; no eliminar ni cambiar su id.

---

## Plan de implementación (orden seguro)

### Fase 1 – Base (sin romper nada)

1. **special_buildings.json**
   - Poner Arena con `show_in_manage_buildings: false`.
   - Añadir tres profesiones: `arena_exhibition`, `arena_proving`, `arena_championship` (nombres y descripciones; 1 daily_story stub por una si hace falta para compatibilidad).

2. **event_daily_exec.rpy**
   - En el bucle principal de edificios, al inicio del `for building_name in store.owned_buildings`, si `building.get("type") == "arena"`: `continue` (para no procesar Arena con la lógica genérica).  
   - O asegurarse de que "Arena" **nunca** esté en `owned_buildings` (add_arena_building no la añade; dejar así).
   - Después del bloque de Academy, añadir bloque **Arena**:
     - Condición: `getattr(store, "arena_unlocked", False) and "Arena" in available_buildings`.
     - Obtener `arena_workers = workers_by_building.get("Arena", [])` y sincronizar `available_buildings["Arena"]["assigned_servants"]`.
     - Por cada worker, leer job; si no es uno de los tres ids, skip.
     - Llamar a una función `run_arena_daily_bout(worker, tier)` que devuelva (outcome, earnings, reputation_change, description, consequences aplicados).
     - Aplicar consecuencias al worker y al edificio Arena; añadir entrada a `daily_report`.
     - Dar Combat XP (función tipo `add_arena_combat_skill_uses(worker)` o sumar uses a `worker["skill_uses"]["Combat"]` según tier).

3. **script.rpy** (init python)
   - Definir `run_arena_daily_bout(worker, tier)`:
     - tier in ("arena_exhibition", "arena_proving", "arena_championship").
     - Roll con Combat (misma fórmula que run_arena_trial o la de event_daily_exec: effective_skill, roll, bands).
     - Según tier y outcome: earnings, reputation_change, health/energy/joy, y en proving/championship failure: aplicar Scarred o health loss.
     - Devolver dict con outcome, earnings, reputation_change, description, y list de consecuencias ya aplicadas o a aplicar.

4. **screens.rpy**
   - Actualizar textos de **arena_menu** y **arena_training_menu**: descripción de la Arena y de los tres roles (Exhibition / Proving / Championship) con riesgo y recompensas.
   - El botón “Train workers” puede seguir abriendo la selección de workers y recordar que el rol se elige en Manage Workers → Arena → Assign role (ya soportado si las profesiones existen en el JSON).

### Fase 2 – Opcional

5. **Requisitos de tier**
   - En job_selection o en run_arena_daily_bout: si job es `arena_championship` y (Combat &lt; 40 y no tiene Champion's Blade), no ejecutar bout o degradar a Proving y mostrar mensaje.
   - Ítem **arena_licence**: añadir en items.json; en Proving, comprobar si tiene licencia para permitir o dar bonus; compra en “Visit promoter” (nueva pantalla o diálogo).

6. **Loot y premios**
   - En championship critical_success: posibilidad de loot (ej. objeto de arena) o dinero extra; ya se puede hacer dentro de `run_arena_daily_bout` y añadir a report_entry["loot"] y manager_inventory.

---

## Resumen de archivos a tocar

| Archivo | Cambios |
|---------|--------|
| `game/data/buildings/special_buildings.json` | Arena: show_in_manage_buildings false; 3 profesiones con ids y daily_story stub. |
| `game/scripts/events/event_daily_exec.rpy` | Bloque Arena después de Academy; opcional skip type=="arena" en bucle principal. |
| `game/scripts/script.rpy` | Función `run_arena_daily_bout(worker, tier)` y posiblemente `add_arena_combat_skill_uses(worker, tier)`. |
| `game/scripts/core/screens.rpy` | arena_menu y arena_training_menu: textos y listado de los 3 roles (Exhibition, Proving, Championship). |
| `game/data/items/items.json` | (Fase 2) Añadir arena_licence si se desea. |

Con esto la Arena queda alineada con la Academy (edificio especial, workers enviados, procesamiento diario dedicado), con tres niveles de apuestas/riesgo y espacio para ítems y requisitos sin romper el trial ni el pase de Lanista.
