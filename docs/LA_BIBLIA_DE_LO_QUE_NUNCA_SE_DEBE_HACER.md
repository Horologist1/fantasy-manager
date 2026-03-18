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

---

*Última actualización: marzo 2026. Añade entradas nuevas cuando encuentres patrones problemáticos.*
