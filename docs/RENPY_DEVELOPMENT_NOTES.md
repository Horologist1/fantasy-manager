# Ren'Py Development Notes - Fantasy Manager

Este archivo contiene aprendizajes importantes para el desarrollo en Ren'Py.
**Este archivo NO se compila en el juego** (solo archivos .rpy/.rpyc).

> ⚠️ **Bug que rompe los saves de toda la sesión:** `store.foo = local_fn` dentro del `python:` block de un screen poisons el rollback log permanentemente. `Function(local_fn, ...)` en widget actions **sí** funciona (el árbol de displayables se reconstruye en load). Ver **`LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md` §8** para el detalle y el grep de verificación pre-commit.

---

## 1. Tipos de Datos en Ren'Py (CRÍTICO)

Ren'Py NO usa tipos Python estándar. Usa versiones "Revertable" para permitir rollback/undo.

### Nunca usar `isinstance()` con tipos básicos:

```python
# MAL - Siempre devuelve False para objetos Ren'Py
isinstance(worker, dict)   # False para RevertableDict
isinstance(items, list)    # False para RevertableList

# BIEN - Funciona con cualquier objeto tipo diccionario/lista
hasattr(worker, 'get')           # True para dict-like
hasattr(items, '__iter__')       # True para list-like
hasattr(items, 'append')         # True para list-like mutable
```

### Tipos Ren'Py equivalentes:
| Python Standard | Ren'Py Equivalent      |
|-----------------|------------------------|
| `dict`          | `RevertableDict`       |
| `list`          | `RevertableList`       |
| `set`           | `RevertableSet`        |
| `object`        | `RevertableObject`     |

### Acceso directo (preferido):
```python
# Si sabes que el objeto existe, accede directamente
ab = worker.get("assigned_building", "Unassigned")
name = worker.get("name")

# No necesitas verificar isinstance primero
```

---

## 2. Debugging en Ren'Py

### Siempre verificar tipos cuando algo falla:
```python
renpy.log("DEBUG: type=" + str(type(obj)))
renpy.log("DEBUG: has_get=" + str(hasattr(obj, 'get')))
```

### El log está en:
- Windows: `game/log.txt` o en la carpeta del proyecto
- También: `%APPDATA%/RenPy/[game_name]/log.txt`

### Forzar recompilación:
Borrar TODOS los `.rpyc` y archivos de cache cuando los cambios no se aplican:
```powershell
Get-ChildItem -Path "game/scripts" -Filter "*.rpyc" -Recurse | Remove-Item -Force
Remove-Item -Path "game/cache/*.rpyb" -Force
```

---

## 3. Sistema de Guardado - Fantasy Manager

### Arquitectura:
- El juego usa un sistema de **snapshot JSON** personalizado, NO el sistema nativo de Ren'Py
- Los snapshots están en: `game/saves/snapshot_X-X.json`
- `config.after_load_callbacks` NO se ejecuta para cargas de snapshot personalizadas

### Variables críticas de workers:
- `worker["assigned_building"]` - A qué edificio está asignado ("Building 1", "Unassigned")
- `building["assigned_servants"]` - Lista de workers asignados al edificio
- `building["servant_jobs"]` - Dict de worker_name -> job_type

### Sincronización:
La función `rebuild_assigned_servants()` en `screens.rpy` reconstruye `assigned_servants` desde los `assigned_building` de cada worker. Se llama al hacer clic en "Buildings".

---

## 4. Errores Comunes y Soluciones

### Error: "dictionary changed size during iteration"
```python
# MAL
for key in my_dict:
    if condition:
        del my_dict[key]  # Error!

# BIEN
keys_to_delete = [k for k in my_dict if condition]
for key in keys_to_delete:
    del my_dict[key]
```

### Error: Variables no actualizadas después de editar .rpy
- Borrar archivos `.rpyc` correspondientes
- Borrar `game/cache/*.rpyb`
- Reiniciar el juego completamente

### Error: `UnboundLocalError: local variable referenced before assignment`
- Asegurarse de inicializar variables ANTES de usarlas en condicionales
```python
# MAL
if condition:
    my_var = value
if my_var:  # Error si condition era False

# BIEN
my_var = None
if condition:
    my_var = value
if my_var:  # OK
```

---

## 5. Prioridades de Desarrollo (Usuario)

El usuario ha establecido estas prioridades:
1. **Seguridad** - El código debe ser robusto y no romper saves
2. **Performance** - Eficiencia, pero no a costa de seguridad
3. **Limpieza** - Código limpio, pero no a costa de los anteriores

---

## 6. Archivos Clave del Proyecto

| Archivo | Propósito |
|---------|-----------|
| `scripts/core/screens.rpy` | UI screens, incluye `rebuild_assigned_servants()` |
| `scripts/save_snapshot.rpy` | Sistema de guardado/carga de snapshots |
| `scripts/events/event_daily_exec.rpy` | Procesamiento de next-day, `_relink_assigned_servants_to_store_workers()` |
| `scripts/script.rpy` | Funciones core, callbacks |
| `scripts/workers/worker_*.rpy` | Lógica de workers |

---

## 7. Historial de Bugs Resueltos

### 2026-01-23: Workers desaparecen en Manage Buildings
**Síntoma**: Al cargar una partida, Manage Buildings mostraba 0 o 1 worker.
**Causa**: Uso de `isinstance(w, dict)` que fallaba con `RevertableDict`.
**Solución**: Cambiar a `hasattr(w, 'get')` y crear `rebuild_assigned_servants()`.

### 2026-01-23: Flags de interacciones no persisten entre cargas
**Síntoma**: Los flags de workers (progreso de interacciones) se perdían al cargar una partida.
**Causa**: Ren'Py restauraba su versión nativa de `workers` (sin flags actualizados) DESPUÉS de que el sistema de snapshot aplicara los datos correctos.
**Diagnóstico**: Los flags SÍ se guardaban correctamente en el snapshot JSON, pero Ren'Py los sobrescribía.
**Solución**: Añadir verificación de flags en el bloque `AFTER_LOAD` de `save_snapshot.rpy` que compara los flags del snapshot con los actuales y re-aplica los workers completos si hay diferencias.
**Ubicación**: `save_snapshot.rpy`, sección `AFTER_LOAD` (líneas ~1773-1808).

---

## 8. Patrones de Código Seguros

### Re-aplicar datos críticos después de load
Ren'Py puede sobrescribir variables `default` después de nuestros callbacks. Para datos críticos:

```python
# Dentro del bloque AFTER_LOAD, después de obtener 'snap' del archivo
if snap is not None:
    # 1. Obtener valor del snapshot
    data_val = snap.get("critical_field")
    if data_val is not None:
        # 2. Comparar con valor actual
        current_data = getattr(store, 'critical_field', default)
        if data_val != current_data:
            # 3. Re-aplicar con deepcopy
            store.critical_field = _cp.deepcopy(data_val)
            renpy.store.critical_field = store.critical_field
```

### Siempre dentro del bloque if snap
El código que accede a `snap` DEBE estar dentro del bloque `if snap is not None and _snapshot_matches_slot(snap, slot_name):` para evitar `NameError`.

---

*Última actualización: 2026-01-23*
