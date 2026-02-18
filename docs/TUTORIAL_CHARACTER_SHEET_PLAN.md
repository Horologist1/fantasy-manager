# Plan: Añadir misión de hoja de personaje al tutorial

## Objetivo

Añadir una misión nueva sobre la hoja de personaje del manager, como una de las primeras etapas, **sin**:
- Desconfigurar flags de partidas antiguas
- Romper el progreso de otras partidas
- Romper ninguna parte del journal
- Hacer que código que lee por número de objetivo deje de coincidir (p. ej. `objective_5_complete` debe seguir siendo “poción”, no otra cosa)

---

## 1. Inventario del sistema actual

### 1.1 Dónde viven los objetivos (tutorial_system.rpy)

- **Variables de estado:**  
  `current_objective` (1..16), `objective_1_complete` .. `objective_16_complete`, `tutorial_active`, `tutorial_skipped`, y flags auxiliares (`potion_purchased`, `building_1_type_set`, etc.).
- **Contenido:**  
  `objective_titles` y `objective_descriptions` son diccionarios indexados por **número** (1..16).
- **Lógica de progreso:**  
  `get_current_objective_progress()` y `check_objective_completion()` usan `if current_objective == 1:` … `elif current_objective == 16:` (y `else`).  
  Las condiciones de “objetivo anterior completado” usan `getattr(store, f'objective_{obj_num - 1}_complete', False)` (números fijos).
- **Journal (pantalla):**  
  `journal_panel` tiene ramas `if current_objective == 1:` … `elif current_objective == 7:` (enlaces de tutorial) y `if current_objective == 8:` … `elif current_objective == 16:` (MARK AS COMPLETE / elección de camino).  
  También: `if current_objective < 8:` para “Skip Tutorial”.
- **Governor tension:**  
  `update_governor_attention()` usa `current_obj == 8`, `== 9`, … `>= 16`.  
  `process_governor_tension_event()` usa `current_objective < 10`, `> 16`, `event_flags.get("quest_complete")`.
- **Skip tutorial:**  
  Pone `objective_1_complete` … `objective_7_complete = True` y `current_objective = 8` (números fijos).
- **Final:**  
  Objetivo 16: al marcar completo se hace `objective_16_complete = True`, `tutorial_active = False` y salto al ending. No hay referencia a “último objetivo = 17”.

### 1.2 Snapshot (save_snapshot.rpy)

- **Guardado:**  
  `_build_snapshot()` guarda explícitamente `current_objective` y `objective_1_complete` … `objective_16_complete` (y el resto de flags de tutorial).
- **Carga:**  
  `_apply_snapshot()` restaura esos mismos campos por nombre (`snap.get("objective_5_complete", False)` etc.).  
  Si añadimos un objetivo nuevo, hay que añadir **solo** el nuevo campo (p. ej. `objective_17_complete`) en build y apply; los 1..16 no se tocan.

### 1.3 Referencias a números concretos fuera de tutorial_system

- **script.rpy:**  
  - Objetivo 1: `if store.current_objective == 1 and store.workers_hired == 3` → `check_tutorial_objective()`.  
  - Objetivo 5: comprobación de poción (comprar/usar) y `check_objective_completion()`.  
  - Objetivo 12: `_mark_objective_12_item_collected` en ítems (binding_gem, etc.).
- **event_daily_exec / otros:**  
  Uso de `check_objective_completion()` y a veces `current_objective` para lógica de eventos o diálogos.
- **screens.rpy:**  
  Referencias al journal y a `current_objective` para mostrar/ocultar cosas (p. ej. “Buy Buildings Abroad” si `not tutorial_active`).

Conclusión: **cualquier renumeración** (insertar un objetivo “hoja de personaje” como nuevo 2 y desplazar 2→3, …, 16→17) haría que:
- Partidas guardadas tengan `objective_5_complete = True` refiriéndose a “poción”, pero en el código nuevo `objective_5_complete` sería otra misión → **inconsistencia y bugs**.
- Todo el código que hace `current_objective == 5` o `objective_5_complete` tendría que reinterpretarse o renumberarse → **riesgo alto y muchas tocadas**.

Por tanto, **no se debe renumerar**. Solo hay dos enfoques seguros.

---

## 2. Estrategias seguras

### Opción A: Nuevo objetivo al final (objetivo 17)

- **Qué es:**  
  Añadir un objetivo 17 (“La hoja del señor”, o similar) que se desbloquea después del 16 (o se muestra como “opcional/post-campaña”).  
  No se cambia el significado de 1..16; no se renumera nada.
- **Ventajas:**  
  Cero riesgo para partidas viejas y para todo el código que usa 1..16.  
  Implementación clara: un bloque más en títulos/descripciones, progreso, journal y snapshot.
- **Desventaja:**  
  No es “una de las primeras etapas”; es la última o extra.

Si se elige esta opción, habría que:
- Añadir `default objective_17_complete = False`.
- Añadir entradas `17` en `objective_titles` y `objective_descriptions`.
- En `get_current_objective_progress()`: `elif current_objective == 17:` con el texto que corresponda.
- En `check_objective_completion()`: ninguna auto-avance para 17 (o sí, si se quiere que al abrir la hoja se marque completo).
- En `journal_panel`: rama `elif current_objective == 17:` con instrucciones y, si aplica, “MARK AS COMPLETE” o lógica automática.
- En snapshot: una línea más para `objective_17_complete` en `_build_snapshot` y en `_apply_snapshot`.
- Governor tension: ya usa `current_obj >= 16` para atención máxima; 17 puede tratarse igual (o ignorarse para tensión).
- Final: el “fin del tutorial” sigue siendo objetivo 16 (y `tutorial_active = False` al completar 16). El 17 sería opcional o de cierre narrativo.

---

### Opción B: “Sub-etapa” entre objetivo 1 y 2 (sin nuevo número)

- **Qué es:**  
  No añadir `objective_17` ni renumerar. Añadir un **paso obligatorio** entre “completar objetivo 1” y “poder considerar objetivo 2 como desbloqueado”:  
  “Abrir la hoja de personaje del manager (clic en nombre en el mapa) y asignar el primer punto de management skill.”  
  Se usa un **flag por nombre**, por ejemplo `manager_character_sheet_tutorial_done` (o reutilizar `manager_start_skill_chosen` si ya existe y significa “ya asignó el punto inicial”).
- **Flujo:**  
  - Al completar objetivo 1, en vez de pasar directo a `current_objective = 2`, se puede:  
    - Dejar `current_objective = 1` y mostrar en el journal algo como: “Siguiente: abre tu hoja de personaje (tu nombre en el mapa) y asigna tu primera habilidad de gestión.”  
    - O avanzar a `current_objective = 2` pero en la **descripción/progreso del 2** indicar: “Primero: abre tu hoja de personaje y asigna tu primera habilidad.”  
  - Cuando el jugador abra la hoja y asigne el punto (o solo abra, según diseño), se pone `manager_character_sheet_tutorial_done = True` (o `manager_start_skill_chosen = True`).  
  - La condición para “completar objetivo 2” (elegir tipo de edificio) podría exigir además que `manager_character_sheet_tutorial_done` sea True; así la hoja de personaje es obligatoria entre 1 y 2, sin tocar números 1..16.
- **Partidas antiguas:**  
  Partidas que ya tienen `current_objective >= 2` o `objective_2_complete = True` no deben bloquearse. Por tanto:  
  - Si `current_objective > 1` o `objective_2_complete`, **no** exigir nunca `manager_character_sheet_tutorial_done`.  
  - Solo exigir este flag cuando `current_objective == 1` y estemos a punto de dar por válido el avance al 2 (o al mostrar el “siguiente paso” tras el 1).  
  Así, saves viejos siguen leyendo bien sus flags y su progreso.
- **Ventajas:**  
  La misión es “de las primeras” sin cambiar ningún número de objetivo ni ningún flag existente.  
  Compatibilidad total con guardados.
- **Desventajas:**  
  Lógica un poco más enredada (un paso más entre 1 y 2) y hay que documentar bien que el “número” del objetivo no cambia.

Implementación mínima para Opción B:
- Variable: `default manager_character_sheet_tutorial_done = False` (o reutilizar `manager_start_skill_chosen`).
- Al completar objetivo 1 (en `check_objective_completion`): no pasar a 2 hasta que `manager_character_sheet_tutorial_done` sea True; mientras tanto, en `get_current_objective_progress()` para objetivo 1 (o en la descripción del “siguiente paso”) mostrar: “Abre tu hoja de personaje (clic en tu nombre en el mapa) y asigna tu primera habilidad de gestión.”
- En la pantalla `manager_character_sheet`: al abrir (o al confirmar el primer punto de skill), hacer `store.manager_character_sheet_tutorial_done = True` y opcionalmente `check_objective_completion()` para que, si ya tiene 3 workers, pase a objetivo 2.
- Snapshot: guardar y restaurar `manager_character_sheet_tutorial_done` (o depender solo de `manager_start_skill_chosen` si ya se guarda).
- Journal: en la rama `current_objective == 1` añadir un botón/enlace “Map > [Tu nombre] (hoja de personaje)” y el texto de “siguiente paso” anterior.
- No añadir `objective_17_complete` ni tocar 2..16.

---

## 3. Resumen de sitios a tocar (por estrategia)

### Si se usa Opción A (objetivo 17)

| Archivo / zona | Cambio |
|----------------|--------|
| tutorial_system.rpy | `default objective_17_complete = False`. Entradas 17 en `objective_titles` y `objective_descriptions`. |
| tutorial_system.rpy | `get_current_objective_progress()`: rama `elif current_objective == 17:`. |
| tutorial_system.rpy | `check_objective_completion()`: rama para 17 (auto o manual). |
| tutorial_system.rpy | `journal_panel`: rama `elif current_objective == 17:` (texto + botón / MARK AS COMPLETE). |
| tutorial_system.rpy | Governor: opcional tratar 17 como 16 para atención. |
| save_snapshot.rpy | En `_build_snapshot` añadir `"objective_17_complete": getattr(store, "objective_17_complete", False)`. |
| save_snapshot.rpy | En `_apply_snapshot` restaurar `objective_17_complete` igual que los otros. |
| Ningún otro | No cambiar referencias a 1..16. |

### Si se usa Opción B (sub-etapa 1 → 2)

| Archivo / zona | Cambio |
|----------------|--------|
| tutorial_system.rpy | `default manager_character_sheet_tutorial_done = False` (o reutilizar flag existente). |
| tutorial_system.rpy | Tras completar objetivo 1: no poner `current_objective = 2` hasta que `manager_character_sheet_tutorial_done` sea True; en progreso/descripción del 1 (o “siguiente paso”) indicar abrir hoja y asignar skill. |
| tutorial_system.rpy | `journal_panel` para `current_objective == 1`: añadir enlace “Map > [Tu nombre]” y texto del siguiente paso. |
| manager_character_sheet (screens.rpy) | Al abrir o al confirmar primer skill: `SetVariable("manager_character_sheet_tutorial_done", True)` y opcionalmente `Function(check_objective_completion)`. |
| save_snapshot.rpy | Incluir `manager_character_sheet_tutorial_done` en snapshot y restore (si no se reutiliza `manager_start_skill_chosen`). |
| Ningún otro | No tocar números 2..16 ni flags `objective_N_complete`. |

---

## 4. Qué evitar (riesgos)

- **No insertar** un nuevo objetivo “en medio” (p. ej. nuevo 2) y renumerar 2→3, …, 16→17: rompe guardados y todas las referencias por número.
- **No** usar un número ya existente para una misión nueva (p. ej. “objetivo 2 = hoja de personaje”): `objective_2_complete` y “Path Chosen” quedarían mezclados.
- **No** asumir que “el último objetivo es N” en código sin centralizarlo: si algún día se añade 17, comprobar `>= 16` o “último” en un solo sitio.
- Al añadir 17 (Opción A): asegurarse de que el final del juego y “Skip Tutorial” sigan usando 16 como “fin de la campaña principal” a menos que se decida explícitamente que 17 sea el cierre.

---

## 5. Recomendación

- Si la prioridad es **“misión de las primeras”** y no romper nada: **Opción B** (sub-etapa entre 1 y 2 con flag por nombre).
- Si la prioridad es **mínimo cambio y máxima seguridad** y se acepta que la misión sea “final/opcional”: **Opción A** (objetivo 17).

En ambos casos, no se renumera nada y los flags y números 1..16 conservan exactamente el mismo significado para partidas antiguas y para todo el código existente del journal y del tutorial.
