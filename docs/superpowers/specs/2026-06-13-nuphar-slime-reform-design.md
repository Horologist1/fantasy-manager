# Nuphar — Slime girl con reforma al morir (monster worker NSFW)

**Fecha:** 2026-06-13
**Estado:** Diseño pendiente de revisión del usuario

## Resumen

Nuevo personaje: **Nuphar**, una slime girl. Es una **monster worker exclusivamente NSFW**
(slime sin ropa). Su gracia mecánica es que, al ser "líquida", **no muere de verdad cuando
su vida llega a 0: se reforma de un charco**, pero vuelve débil y con resaca. El arte ya
existe en `game/images/workers/nuphar/`; falta el JSON del worker, dos traits nuevos y dos
enganches de código (reforma + caps de skill).

Además, se crea una **plantilla de slime genérica** (estilo Moss/Amanita) para que aparezcan
slimes capturables al azar (con nombre aleatorio), reusando el arte de Nuphar. Nuphar sigue
siendo la única especial (nombre fijo, `unique`).

## Decisiones tomadas (durante el brainstorming)

1. **Mecánica = "reforma con resaca"** (no resistencia a daño). Al morir, revive a vida baja
   y gana un trait temporal que le baja el rendimiento durante unos días. Ilimitada, pero
   cada muerte cuesta días flojos. Se eligió frente a la resistencia 50% porque es **más
   simple** (un único punto de enganche) y **mejor balanceada** (coste controlable).
2. **Muerte durante `Reforming` = muerte real.** Si la matan mientras aún se está recomponiendo,
   muere de verdad. Mantiene una ventana de riesgo genuino.
3. **`Reforming` (debuff) = −50% ganancias y −20 a todas las skills**, durante 3 días.
4. **Tope duro de Clever = 50.** Se implementa una **feature nueva de caps de skill** (ver
   componente 5). El sistema actual de `attribute_caps` NO capa skills.
5. **Reclutamiento = exactamente como Amanita.** Vía el edificio **Monster Taming**, cuyo loot
   `monster_worker` filtra `{"monster": true, "encounter_only": true}` (chance ~10-15%) y llama a
   `loot_monster_worker`, que clona una plantilla al azar del pool. **Sin evento dedicado.**
   - **Nuphar:** `unique: true`, **sin `names_list`** → captura única que conserva el nombre "Nuphar".
   - **Slime genérica:** `unique: false`, **con `names_list`** → clones con nombre aleatorio (= "se
     genera un slime nuevo"), misma carpeta de arte. Igual que Amanita.
   - Ambas llevan `traits: ["Slime"]` y `folder: "nuphar"`.
   - *Nota de orden:* el pool elige al azar entre las plantillas no contratadas, así que "Nuphar la
     primera" no está garantizado literalmente (Amanita tampoco lo hace). Es una pulla única que sale
     en algún momento; forzarla a ser SIEMPRE la primera sería una regla extra de una línea — pendiente
     de confirmar si se quiere.
6. **Sin texto narrativo específico** para el caso de la Arena. El flujo genérico sirve; ella
   se reforma en el rollover del día siguiente igualmente.
7. **Plantilla de slime genérica = idéntica a Amanita**: worker `monster: true, unique: false,
   encounter_only: true` con `names_list` (nombre aleatorio al capturar) y `folder: "nuphar"` (reusa
   el arte de Nuphar). Lleva el trait `Slime`, así que las slimes genéricas también se reforman y
   tienen Clever capado. **Misma raza y mismo perfil de stats que Nuphar, pero peor en todas las
   skills** (derivada con rebaja ≈ −8). **No se toca el generador procedural** (`spawn_new_monster_worker`): al ser
   no-única, la plantilla siempre matchea, así que el fallback roto (carpeta `monsters`) nunca se
   alcanza para slimes.
8. **Clever base de Nuphar = 16** (el más bajo de cualquier worker del juego), no 8.

## Restricciones verificadas en el código

- **Punto único de muerte:** `check_worker_health()` (`script.rpy:4089`) es el único sitio que
  finaliza muertes (mete en `dead_worker_names` y hace `workers.remove`). Se llama solo desde
  el procesado diario (`event_daily_exec.rpy:1610`). La Arena **no** mata en el acto: pone
  `health = 0` (`script.rpy:8024`) y deja que el procesado del día lo resuelva ahí. → Interceptar
  en `check_worker_health` cubre eventos **y** Arena de un plumazo.
- **`SKILL_MAX = 100`** (`script.rpy:49` y `7377`). Las skills de worker se modifican vía helpers
  centrales **`modify_base_skill`** y **`set_base_skill`** (`worker_stats.rpy:518` / `526`), que
  hoy clampan solo a `SKILL_MAX`. El level-up orgánico ya pasa por `modify_base_skill`
  (`script.rpy:2841`). Hay 3 sitios que clampan **a mano** y habría que reencaminar:
  ítems (`script.rpy:1887`), entrenamiento (`worker_training.rpy:853`), elecciones de evento
  (`script.rpy:5722`). El `skills[skill_id] = current + 1` de `script.rpy:7293` es de **management
  skills**, no de worker → fuera de alcance.
- **`attribute_caps` NO capa skills.** Solo atributos secundarios (joy, rebelliousness, romance,
  relationship, comfort_level, comfort_desired, libido — `get_all_secondary_attributes`,
  `worker_stats.rpy:360`). Por eso el tope de Clever necesita la feature nueva.
- **No hay modifier de skills "global".** `skill_modifiers` es siempre dict por-skill, así que el
  −20 de `Reforming` se enumera skill a skill.
- **Traits temporales:** `add_trait_with_duration(worker, trait_name, duration, is_variant=False)`
  (`worker_traits.rpy:304`) ya existe (lo usa la Arena para `Scarred`). Se reutiliza para `Reforming`.
- **Captura de monstruos:** la dispara el loot `monster_worker` del edificio **Monster Taming**
  (`building_types.json`, filtro `{"monster": true, "encounter_only": true}`, chance ~0.1-0.15) en
  `event_daily_exec.rpy:1122-1136`. Llama a `loot_monster_worker(filters)` (`script.rpy:2638`), que
  coge una plantilla al azar del pool no contratado; si tiene `names_list`, **renombra** la instancia.
  Por eso Nuphar (única) **no** lleva `names_list` y la slime genérica **sí**. Amanita es exactamente
  este patrón (sin evento propio). El loader incluye unique + encounter_only + monster.
- **`Scarred`** está en `traits_core.json` **y** `traits_special.json`; confirmar el canónico para no
  duplicar `Reforming`.

## Componentes

### 1. Trait nuevo `Slime` (raza, NSFW) — en `traits_races.json`

Raza nueva, reutilizable. Sigue el esquema de las razas existentes (p.ej. `Demon`, ya `nsfw: true`).
La "tontería" la da el **cap de Clever** (no un modifier negativo, para no duplicar mecánica).

```json
{
  "name": "Slime",
  "conflicts": ["Human","Elf","Dwarf","Orc","Ogre","Demon","Angel","Goblin","Furry","Transformed"],
  "modifiers": {
    "skill_modifiers": { "Agility": 5, "Hand": 3, "Extreme": 3 },
    "health": 10,
    "health_regeneration": 1,
    "joy": 15,
    "rebelliousness": -10
  },
  "reform_on_death": true,
  "skill_caps": { "Clever": 50 },
  "nsfw": true,
  "description": "Una criatura gelatinosa: su cuerpo fluido encaja en cualquier forma, pero su mente apenas cuaja. Difícil de destruir de verdad — si la deshacen, vuelve a juntarse de un charco.",
  "attribute_caps": {},
  "daily_effects": {},
  "gender_restriction": null,
  "requires_traits": [],
  "attribute_minimums": {},
  "duration": 0,
  "on_expire": {},
  "only_assigned": false
}
```

- `reform_on_death: true` — campo nuevo a nivel de trait, leído por la lógica de reforma.
- `skill_caps: { "Clever": 50 }` — campo nuevo, leído por la feature de caps (componente 5).

### 2. Trait nuevo `Reforming` (debuff temporal) — junto a `Scarred`

La "resaca": −50% ganancias y −20 a todas las skills, 3 días, se quita sola.

```json
{
  "name": "Reforming",
  "conflicts": [],
  "modifiers": {
    "earnings_multiplier": 0.5,
    "skill_modifiers": {
      "Sex": -20, "Anal": -20, "BDSM": -20, "Hand": -20, "Oral": -20, "Homo": -20,
      "Special": -20, "Group": -20, "Extreme": -20, "Striptease": -20,
      "Combat": -20, "Clever": -20, "Charm": -20, "Service": -20, "Agility": -20, "Craft": -20
    }
  },
  "description": "Aún se está recomponiendo tras deshacerse. Lenta, blanda y de bajo rendimiento hasta que vuelve a cuajar.",
  "attribute_caps": {},
  "daily_effects": {},
  "gender_restriction": null,
  "requires_traits": [],
  "attribute_minimums": {},
  "duration": 3,
  "on_expire": {},
  "only_assigned": false
}
```

> Localización: los nombres de trait son internos/display y el repo está en inglés (`Human`,
> `Scarred`…). Se usan `Slime`/`Reforming`; si se quiere display en español, se cambia `name`.

### 3. Mecánica de reforma — en `check_worker_health()` (`script.rpy:4089`)

Helper nuevo `worker_can_reform(worker)`: recorre los traits del worker (con `.get`, duck-typing,
sin `isinstance` — ver LA BIBLIA) y devuelve `True` si alguna def de trait tiene `reform_on_death`.

En `check_worker_health`, cuando `worker["health"] <= 0`:

- **Si `worker_can_reform(worker)` y NO tiene ya el trait `Reforming`:**
  - NO se añade a `dead_worker_names`, NO se elimina del roster.
  - `worker["health"] = max(1, calculate_max_health(worker) // 4)` (vuelve a ~25%, no a 1 tic de
    re-muerte).
  - `add_trait_with_duration(worker, "Reforming", 3)`.
  - `renpy.notify(...)` genérico (p.ej. "{name} se reformó de un charco.").
  - Recalcular trait modifiers / max_health tras añadir el trait.
- **Si ya tiene `Reforming` (murió mientras se recomponía):** muere de verdad — flujo normal
  (unassign + remove + `add_to_dead_workers`).

### 4. Worker JSON `Nuphar`

En el set de workers **NSFW unique** (`workers_nsfw_unique.json`; confirmar archivo/loader al
implementar — alternativa: archivo propio tipo `aelis.json`/`yvara.json`). Esquema canónico completo.

```json
{
  "name": "Nuphar",
  "folder": "nuphar",
  "cost": 1500,
  "nsfw": true,
  "unique": true,
  "encounter_only": true,
  "monster": true,
  "procedural": false,
  "skills": {
    "Sex": 45, "Anal": 38, "BDSM": 25, "Hand": 44, "Oral": 42, "Homo": 30,
    "Special": 40, "Group": 40, "Extreme": 43, "Striptease": 33,
    "Combat": 32, "Clever": 16, "Charm": 28, "Service": 16, "Agility": 48, "Craft": 10,
    "Specialty 4": 24, "Specialty 5": 22, "Specialty 6": 26, "Specialty 7": 20,
    "Specialty 8": 24, "Specialty 9": 28, "Specialty 10": 22, "Specialty 11": 20, "Specialty 12": 24
  },
  "traits": ["Slime"],
  "description": "Una slime girl de cuerpo translúcido y mente simple. Lo que le falta de seso le sobra de aguante: por mucho que la deshagan, siempre vuelve a juntarse.",
  "gender": "female",
  "comfort_desired": 1
}
```

- **Sin `names_list`** (conserva "Nuphar" al capturarla).
- Clever 16 de base (el más bajo del juego) + cap 50 del trait → empieza la más tonta y nunca
  pasa de mitad de tabla.
- Alta en físico/sexual y Agility; Combat decente; Craft/Service flojos.

### 5. Feature nueva: caps de skill por trait

Permite que un trait limite el máximo de una skill por debajo de `SKILL_MAX`.

- **`get_skill_cap(worker, skill_name)`** (nuevo, en `worker_stats.rpy` o `worker_traits.rpy`):
  recorre los traits del worker, lee `skill_caps[skill_name]` de cada def, devuelve el **más
  restrictivo**; default `SKILL_MAX` (100). Duck-typing, `.get`, sin `isinstance`.
- **`modify_base_skill` y `set_base_skill`** (`worker_stats.rpy:518`/`526`): cambiar el clamp de
  `min(SKILL_MAX, …)` a `min(get_skill_cap(worker, skill), …)`. Como el level-up ya pasa por aquí,
  la progresión orgánica respeta el cap automáticamente.
- **Reencaminar los 3 sitios con clamp a mano** para que usen los helpers (y respeten el cap):
  - Ítems: `script.rpy:1887` (`min(SKILL_MAX, current + delta)`).
  - Entrenamiento: `worker_training.rpy:853` (`max(0, min(100, base_s))`).
  - Eventos: `script.rpy:5722` (aplica `skill_modifiers` a skills base).
- El cap aplica al **valor base almacenado** de la skill. Como Nuphar no tiene modifier positivo de
  Clever, su Clever efectivo tampoco pasará de 50.

### 6. Plantilla de slime genérica — en `workers_nsfw_other.json`

Misma idea que Amanita/Moss: un template de monster que entra al pool de captura y se clona con
nombre aleatorio. **Misma raza (`Slime`) y mismo perfil de stats que Nuphar** (alto físico/Agility,
bajo Clever/Craft/Service, Combat medio), pero **peor en TODAS las skills** — derivada de Nuphar con
una rebaja consistente (≈ −8 por skill, manteniendo la forma). Es la slime "del montón"; Nuphar es
la mejor de su especie. Reusa el arte de Nuphar (`folder: "nuphar"`); el trait `Slime` le da reforma
y Clever capado a 50 igual que a ella.

```json
{
  "name": "Slime",
  "folder": "nuphar",
  "cost": 1100,
  "nsfw": true,
  "unique": false,
  "encounter_only": true,
  "monster": true,
  "procedural": false,
  "skills": {
    "Sex": 37, "Anal": 30, "BDSM": 17, "Hand": 36, "Oral": 34, "Homo": 22,
    "Special": 32, "Group": 32, "Extreme": 35, "Striptease": 25,
    "Combat": 24, "Clever": 14, "Charm": 20, "Service": 12, "Agility": 40, "Craft": 8,
    "Specialty 4": 16, "Specialty 5": 14, "Specialty 6": 18, "Specialty 7": 12,
    "Specialty 8": 16, "Specialty 9": 20, "Specialty 10": 14, "Specialty 11": 12, "Specialty 12": 16
  },
  "names_list": "fantasy_female",
  "traits": ["Slime"],
  "description": "Una slime salvaje capturada de las ciénagas: dócil, simple y prácticamente indestructible.",
  "gender": "female",
  "comfort_desired": 1
}
```

- **Con `names_list: "fantasy_female"`** → al capturarla, `loot_monster_worker` le pone un nombre
  aleatorio (a diferencia de Nuphar). El `"name": "Slime"` es solo el identificador de la plantilla.
- Nuphar (unique, sin names_list) y la plantilla coexisten en el pool: captura única de Nuphar
  + slimes genéricas repetibles.

### 7. Limpieza

- Borrar `game/images/workers/nuphar/rgthree.compare._temp_gicaa_00046_.png` (basura de ComfyUI).

## Balance

- **Fuerza:** casi nunca la pierdes. La reforma es red de seguridad en eventos peligrosos y Arena
  — fuerte justo cuando el juego castiga. Aguante alto (health +10, regen +1).
- **Coste:** cada muerte = 3 días a −50% ganancias y −20 skills (`Reforming`); si la matan mientras
  se reforma, muere de verdad. Y es **tonta** (Clever 8 de base, tope 50) → nicho físico/sexual/
  aguante, nunca "cerebro".
- **Acceso:** solo por captura (recompensa), no es elección de día 1.

## Fuera de alcance (posibles iteraciones futuras)

- Evento de captura dedicado con narrativa propia.
- Línea de diálogo específica de la Arena para slimes.
- Resistencia a daño % (descartada a favor de la reforma).
- **Arreglar el generador procedural genérico** (`spawn_new_monster_worker` usa `folder: "monsters"`,
  que no existe → monstruos procedurales sin arte). Bug preexistente; NO afecta a slimes (el patrón
  Amanita nunca alcanza ese fallback). Anotado por si se quiere arreglar para otros monstruos.
- Regla para forzar a Nuphar como SIEMPRE la primera captura (el patrón Amanita no lo garantiza).

## Riesgos / gotchas

- **Caches de save:** init-python globals se serializan en saves; worker/trait nuevos pueden ser
  invisibles en saves viejos sin reset de caches al cargar. Probar con cache limpia
  (`game/cache/*.rpyb`, `game/scripts/**/*.rpyc`).
- **RevertableDict/List:** nada de `isinstance`; usar `.get()` y duck-typing.
- **Caps de skill — cobertura total:** asegurarse de que TODA subida de skill de worker pasa por
  `modify_base_skill`/`set_base_skill`; cualquier sitio con clamp a mano que se deje sin reencaminar
  permitiría saltarse el cap.
- **NSFW gating:** `Slime`/`Nuphar` son NSFW; filtrar con `persistent.nsfw_enabled`.
- **Validar JSON** antes de testear; esquema canónico (todas las claves presentes).
- **Definición duplicada de traits** (`Scarred` en dos archivos): no duplicar `Reforming`.

## Verificación / testing

1. JSON válido (Slime, Reforming, Nuphar) y carga sin errores con cache limpia.
2. Captura vía Monster Taming: Nuphar (única) se captura conservando "Nuphar"; la slime genérica se
   captura con nombre aleatorio (`names_list`) y carpeta `nuphar`. Ambas con trait `Slime`.
3. Forzar `health <= 0` (consola/Arena): se reforma a ~25% HP, gana `Reforming`, NO entra en
   `dead_worker_names`.
4. `Reforming` reduce ganancias (−50%) y skills (−20) y desaparece a los 3 días.
5. Morir otra vez mientras `Reforming` activo → muere de verdad.
6. **Cap de skill:** entrenar/usar ítems/eventos sobre Clever de Nuphar → se detiene en 50 por
   todas las vías (entrenamiento, level-up orgánico, ítems, eventos). Otros workers sin cap llegan a 100.
7. Modifiers del trait `Slime` (físicos, health/regen) aplicados correctamente.
