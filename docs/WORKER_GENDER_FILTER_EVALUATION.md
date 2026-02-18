# Evaluación de fallos posibles – Worker Gender Filter

Evaluación del sistema **Worker Gender** (About → Both / Only Male / Only Female) para anticipar fallos en tests.

---

## 1. Comportamiento actual (resumen)

- **Persistente:** `persistent.worker_gender_filter` ("both" | "male" | "female").
- **Al cargar pool de workers** (`load_workers`): se excluyen del JSON los del género no elegido (reclutamiento, Buy Servants, eventos que usan `load_workers`).
- **Al mostrar roster** (`workers_filtered_by_gender(store.workers)`): Manage Workers, popup de selección de worker, Prev/Next en worker details, elegir worker para evento, Storage por defecto.

---

## 2. Fallos posibles y casos límite

### 2.1 Workers sin campo `gender` o con valor raro

- **Comportamiento:** En loader y en `workers_filtered_by_gender` solo se excluye si `gender` es explícitamente `"male"` o `"female"`. Cualquier otro valor (vacío, `None`, typo, "other") **no** se filtra.
- **Efecto:** Esos workers aparecen tanto con "Only Male" como con "Only Female".
- **Riesgo:** Bajo. Si quieres que "other" no aparezca en Only Male/Only Female, habría que tratar ese caso (por ejemplo excluirlos cuando el modo no es "both").
- **Test:** Worker en JSON con `"gender": ""` o sin clave `gender` → debe verse en ambos modos.

---

### 2.2 Cambiar la opción global con partida ya cargada

- **Comportamiento:** El roster real (`store.workers`) no se modifica; solo cambia qué se **muestra** y qué se **carga** en el pool.
- **Efecto:** Si tenías "Both", contrataste a 5 hombres y 5 mujeres, y luego pones "Only Female", en Manage Workers solo ves las 5 mujeres. Los 5 hombres siguen en la partida, asignados a edificios, y siguen generando eventos/dinero.
- **Riesgo:** Bajo; es el comportamiento esperado (“como si no existieran” en la UI).
- **Test:** Contratar varios de ambos géneros → cambiar a Only Female → comprobar que solo se ven mujeres en Manage Workers y que el edificio sigue teniendo asignados a los hombres.

---

### 2.3 Manager de edificio: lista de workers asignados sin filtrar

- **Comportamiento:** La pantalla Manager usa `manager_servants = building["assigned_servants"]`. Esa lista **no** pasa por `workers_filtered_by_gender`.
- **Efecto:** Con "Only Female" puedes tener un hombre asignado a un edificio: **no** aparece en Manage Workers, pero **sí** en la lista de ese edificio al abrir Manager (nombre, nivel, skills, energía, etc.).
- **Riesgo:** Medio. Inconsistencia: “no existe” en una pantalla y sí en otra.
- **Opcional:** Aplicar `workers_filtered_by_gender` a la lista que se usa para dibujar las filas por profesión en Manager, para que solo se muestren workers del género elegido (los del otro género seguirían asignados en datos pero no visibles).
- **Test:** Only Female → asignar un male a un edificio desde Manage Workers (si en algún flujo se puede) o cargar partida que ya lo tenga → abrir Manager de ese edificio y comprobar si aparece.

---

### 2.4 Worker details abierto desde Manager (worker del “otro” género)

- **Comportamiento:** En worker_details, con `in_roster=True`, Prev/Next usan `_roster_list = workers_filtered_by_gender(store.workers)`. Si abres la ficha desde el **Manager** (clic en un worker de la lista del edificio), ese worker puede ser del género “oculto”. En ese caso no está en `_roster_list`, y `_roster_idx = next(..., 0)` devuelve 0.
- **Efecto:** Al dar a Prev/Next, se salta al primero de la lista filtrada (p. ej. primera mujer), no al “anterior/siguiente” del edificio. Puede desorientar.
- **Riesgo:** Bajo–medio si se usa mucho Manager con Only Male/Only Female.
- **Test:** Only Female, building con un male asignado → abrir Manager → abrir ficha del male → pulsar Next/Previous y comprobar que no crashea y que el salto es al primer worker de la lista filtrada.

---

### 2.5 Storage (Manager) con roster filtrado vacío

- **Comportamiento:**  
  `right_worker = (workers_filtered_by_gender(store.workers)[0] if workers_filtered_by_gender(store.workers) else False)`  
  Si la lista filtrada está vacía, no se hace `[0]` y se usa `False`.
- **Efecto:** Con "Only Female" y 0 mujeres en el roster, al pulsar Storage se abre el inventario con ningún worker seleccionado (right_worker = False). No hay IndexError.
- **Riesgo:** Bajo.
- **Test:** Only Female, partida sin mujeres → Manager → Storage → comprobar que abre sin error y sin worker por defecto.

---

### 2.6 Roster vacío y Manage Workers / Worker details

- **Manage Workers:** `_displayed_roster` vacío → tabla vacía, filtros de edificio/trabajo sin opciones útiles. No hay crash.
- **Worker details Prev/Next:** `len(_roster_list) > 0` es False → los botones no hacen nada. Correcto.
- **Riesgo:** Bajo.
- **Test:** Only Male en partida sin hombres → abrir Manage Workers y Worker details y pulsar Prev/Next.

---

### 2.7 Eventos que eligen worker (choose_event_worker_screen / choose_worker_for_event) — **RESUELTO**

- **choose_worker_for_event(skill_name, threshold):** Construye `eligible_workers` desde `workers_filtered_by_gender(store.workers)`. Correcto.
- **choose_event_worker_screen(eligible_workers):** Recibía la lista ya construida; si algún caller pasaba lista sin filtrar, se podrían listar workers del otro género.
- **Resolución (código):** Al inicio del `python` de la pantalla se aplica `eligible_workers = workers_filtered_by_gender(eligible_workers)`. Así, quien sea que llame a la pantalla, la lista mostrada siempre respeta Worker Gender.
- **Test:** Only Female → disparar un evento que pida elegir worker → solo deben salir mujeres.

---

### 2.8 Reclutamiento (recruitment) y Buy Servants

- **Reclutamiento:** Usa workers cargados con `load_workers(...)`, donde ya se aplica el filtro de género. Solo aparecen workers del género elegido.
- **Buy Servants:** `displayed_workers` se rellena vía `_ensure_buy_workers_loaded` / refresh, que deberían usar el resultado de `load_workers` (ya filtrado). Con Only Male/Only Female el filtro local (All/Male/Female) se oculta y se muestra la lista ya filtrada.
- **Riesgo:** Bajo si `displayed_workers` se alimenta siempre del pool que pasa por `load_workers`.
- **Test:** Only Male → Buy Servants y Reclutamiento → comprobar que solo aparecen hombres.

---

### 2.9 rebuild_assigned_servants y datos de edificios

- **Comportamiento:** Itera `store.workers` completo para reconstruir `assigned_servants` de cada edificio. No usa el filtro de género.
- **Efecto:** Correcto. Los asignados son todos los workers del save; el filtro es solo de visualización y de pool de reclutamiento.
- **Riesgo:** Nulo.

---

### 2.10 Guardar / cargar partida

- **Persistent:** `persistent.worker_gender_filter` se guarda en persistent, no en el save por slot. Al cargar otra partida se sigue usando la preferencia global.
- **Roster en el save:** Es la lista completa (todos los géneros). Al cargar, Manage Workers y el resto de pantallas aplican el filtro sobre ese roster.
- **Riesgo:** Bajo. Solo tener en cuenta que la opción es global: la misma para todas las partidas.
- **Test:** Guardar con Only Female → cargar partida → comprobar que el filtro sigue en Only Female y que las listas se ven bien.

---

### 2.11 Orden de carga y `persistent` no inicializado

- **Comportamiento:** En options.rpy se fuerza `persistent.worker_gender_filter = "both"` si no existe o no es uno de ("both", "male", "female"). En loader y en `workers_filtered_by_gender` se usa `getattr(persistent, "worker_gender_filter", "both")`.
- **Efecto:** Si por algún motivo persistent no está inicializado, se usa "both" y no hay crash.
- **Riesgo:** Bajo.

---

## 3. Resumen de prioridad para tests

| Prioridad | Qué probar |
|----------|------------|
| Alta | Only Female → Manage Workers solo muestra mujeres; Buy Servants y Reclutamiento solo ofrecen mujeres. |
| Alta | Only Male → mismo para hombres. |
| Media | Only Female → edificio con male asignado → abrir Manager y comprobar si el male aparece en la lista del edificio (y si se considera bug o no). |
| Media | Worker details abierto desde Manager para un worker del otro género → Prev/Next no crashea y el salto es coherente. |
| Media | Cambiar de Both a Only Female con roster mixto → solo se ven mujeres en Manage Workers. |
| Baja | Roster filtrado vacío → Storage, Manage Workers, Prev/Next sin errores. |
| Baja | Workers sin `gender` o con valor raro → aparecen en Only Male y Only Female. |

---

## 4. Mejora aplicada (consistencia Manager)

- **Hecho:** En la pantalla Manager se usa `_displayed_servants = workers_filtered_by_gender(manager_servants)` para el contador por profesión y para el bucle que dibuja cada worker. La lista mostrada es coherente con Manage Workers; los workers del otro género siguen en `assigned_servants` para lógica/eventos pero no se muestran en la UI.

Con esto tendrías una evaluación clara de fallos posibles y una guía para tus tests y, si quieres, una mejora opcional para el Manager.
