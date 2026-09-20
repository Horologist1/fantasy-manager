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

### Arquitectura (verificada el 2026-09-10):
- Cada guardado manual tiene un archivo **nativo de Ren'Py y un snapshot JSON**, emparejados por ranura, GUID y transacción. Ambos son necesarios; no escribir uno de ellos por separado.
- El directorio principal es `config.savedir` (también en Android). `game/saves` se consulta como ubicación heredada cuando procede.
- `SnapshotFileSave` valida que el snapshot sea cargable antes de escribir. Conserva la generación anterior en `.json.bak.previous.tmp` hasta confirmar el guardado nativo o su restauración. Este archivo puede ser la única recuperación tras una interrupción: no tratarlo como basura temporal.
- `CanonicalSnapshotFileLoad` valida la firma nativa **antes de deserializar**, selecciona MAIN/BACKUP/RECOVERY por identidad y reinicia el contexto. Aplica una sola fuente al store limpio y ejecuta una vez los callbacks restantes; excluye `_after_load_snapshot_callback` de ese recorrido.
- La versión JSON sigue siendo 3. Los nueve campos de `_SNAPSHOT_PROGRESS_DEFAULTS` son opcionales para mantener la compatibilidad. Se recuperan de raíces nativas verificadas si faltan en JSON; si tampoco existen allí, se aplican valores iniciales o pistas guardadas de la academia.
- Una nueva variable de progreso debe incluirse en captura, restauración y rollback. `test_snapshot_state_coverage.py` obliga a revisar cada `default` público; no clasificar progreso real como temporal para eludir la prueba.

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
**Solución histórica**: se añadieron pasadas de restauración en `AFTER_LOAD`. Este diagnóstico explica código heredado, pero no es el patrón para nuevas cargas. El recorrido manual actual reinicia el contexto y aplica un solo snapshot; ver sección 3.

---

## 8. Patrones de Código Seguros

### Restauración transaccional
Validar la fuente antes de reiniciar o modificar el store. Capturar todos los campos que se van a tocar, incluidos los opcionales ausentes en partidas antiguas, y restaurarlos si falla `_apply_snapshot`. Evitar aplicar MAIN y después mezclarlo con BACKUP, o añadir otra pasada de workers para ocultar un error de carga.

### Comprobaciones antes de entregar
Ejecutar la batería con `RENPY_RUNTIME_REQUIRED=1`. `test_general_save_runtime.py` comprueba guardados nativos, sobrescritura, carga de v3 con campos ausentes, recuperación tras interrupción y rollback de una carga fallida. `test_snapshot_recovery.py` provoca fallos de escritura/restauración. Los barridos de `tools/qa_choice_layout.py` comprueban los eventos y el guardado después de recorrer sus pantallas. Ver el informe `AUDIT_general_2026-09-10.md` para resultados y límites.

---

*Última actualización: 2026-09-10*
