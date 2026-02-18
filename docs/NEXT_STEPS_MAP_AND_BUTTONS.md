# Integración NewMap – mapa y botones en gui/map

## Estado: integración hecha

Se usó la carpeta **NewMap** (en `SNS/NewMap`) y se integró así:

### 1. Mapa nuevo (map3 → map.png)

- **Origen:** `NewMap/map3.png`
- **Destino:** `game/images/map.png` (sustituido)
- El juego ya usa `map_bg = "images/map.png"` en `config.rpy`, así que el nuevo mapa se muestra sin cambiar código.

### 2. Botones "In development" (Murderhouse, Academy, Arena)

Archivos copiados de NewMap a `game/gui/map/` y enlazados en `map_screen()` con el mismo patrón que el resto de botones del mapa (`imagebutton`, `focus_mask True`, tooltip, etc.):

| Ubicación   | Idle              | Hover              | Acción           |
|------------|--------------------|--------------------|-------------------|
| N6 Murderhouse | `N6murderhousea.png` | `N6murderhousec.png` | Show("in_development") |
| N5 Academy     | `N5academya.png`     | `N5academyb.png`     | Show("in_development") |
| Arena          | `arenaa.png`         | `arenab.png`         | Show("in_development") |

- La pantalla `in_development()` muestra el mensaje y "Close".

### 3. Reemplazos estéticos (misma función)

Archivos de NewMap copiados a `game/gui/map/` con el mismo nombre que usaba el código; no se tocó código:

- **Castle:** `Castleb.png` → reemplazo del hover del Castillo.
- **N5Greenhouse:** `N5Greenhouseb.png` → reemplazo del hover (idle sigue con `get_map_button_idle_image("N5Greenhouse")`).
- **N5Tavern:** `N5Tavernb.png` → reemplazo del hover (idle con `get_map_button_idle_image("N5Tavern")`).

Convención del proyecto (en `script.rpy`): `get_map_button_idle_image(button_id)` devuelve `gui/map/{button_id}a.png` si no está comprado y `gui/map/{button_id}c.png` si está comprado; el hover es siempre `*b.png`.

### 4. Resumen de cambios en código

- **Pantalla "In development":** `screens.rpy` – `in_development()`.
- **Tres botones nuevos en `map_screen()`:** N6murderhouse, N5academy, Arena, con rutas exactas de NewMap y acción `Show("in_development")`.
- **Mapa:** solo reemplazo de `game/images/map.png` por `NewMap/map3.png`; `map_bg` sigue apuntando a `images/map.png`.
