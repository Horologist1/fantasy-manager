# Lista de Imágenes Mínimas para un Worker

## 🎯 Imagen Mínima Absoluta (REQUERIDA)

Para que un worker funcione correctamente en el juego, necesita **al menos una imagen de perfil**:

### 1. Imagen de Perfil (Profile)
- **Nombre del archivo:** `Profile.png`, `Profile.jpg`, `Profile.jpeg`, `Profile.webp` (o variaciones con números como `Profile (1).jpg`)
- **Ubicación:** `game/images/workers/{folder_del_worker}/`
- **Descripción:** Esta es la imagen que se muestra en la pantalla de detalles del worker, en la lista de workers, y como fallback cuando no hay otras imágenes disponibles.
- **Formato:** Cualquier formato soportado (png, jpg, jpeg, webp, webm, mp4)
- **Requisito:** ✅ **OBLIGATORIA**

---

## 📸 Imágenes Opcionales (Recomendadas)

Aunque no son estrictamente necesarias, estas imágenes mejoran la experiencia del juego:

### 2. Imágenes de Habilidades (Skills)

El sistema busca imágenes basadas en las habilidades del worker. Si un worker tiene una habilidad alta, es recomendable tener imágenes para ella:

#### Skills Estándar:
- `sex.png` / `sex.jpg` - Para la habilidad "Sex"
- `anal.png` / `anal.jpg` - Para la habilidad "Anal"
- `bdsm.png` / `bdsm.jpg` - Para la habilidad "BDSM"
- `hand.png` / `hand.jpg` - Para la habilidad "Hand"
- `oral.png` / `oral.jpg` - Para la habilidad "Oral"
- `les.png` o `gay.png` - Para la habilidad "Homo"
- `special.png` / `special.jpg` - Para la habilidad "Special"
- `group.png` / `group.jpg` - Para la habilidad "Group"
- `extreme.png` o `beast.png` - Para la habilidad "Extreme"
- `strip.png` o `striptease.png` - Para la habilidad "Striptease"
- `combat.png` / `combat.jpg` - Para la habilidad "Combat"
- `clever.png` / `clever.jpg` - Para la habilidad "Clever"
- `charm.png` / `charm.jpg` - Para la habilidad "Charm"
- `service.png` o `maid.png` - Para la habilidad "Service"
- `agility.png` / `agility.jpg` - Para la habilidad "Agility"
- `craft.png` / `craft.jpg` - Para la habilidad "Craft"

#### Variantes de Resultado:
- `{skill}_failure.png` - Imagen cuando la habilidad falla (ej: `sex_failure.png`)
- `{skill}.png` (sin sufijo) - Imagen cuando la habilidad tiene éxito

**Nota:** Puedes tener múltiples variantes numeradas: `sex (1).png`, `sex (2).png`, `sex (3).png`, etc.

### 3. Imágenes de Interacciones (Opcional)

Si el worker participa en interacciones, estas imágenes pueden ser útiles:

- `romance_female.png` - Para interacciones románticas (workers femeninos)
- `romance_male.png` - Para interacciones románticas (workers masculinos)
- `friendship.png` - Para interacciones de amistad
- `joy_female.png` / `joy_male.png` - Para interacciones de alegría
- `obedience.png` - Para interacciones de disciplina

### 4. Imágenes de Eventos (Opcional)

Si el worker participa en eventos específicos, puedes crear imágenes para ellos:

- `{event_name}.png` - Imagen del evento (ej: `cook_story1_restaurant.png`)
- `{event_name}_failure.png` - Imagen de fallo del evento

### 5. Imágenes con Prefijos de Traits (Opcional)

Si el worker tiene traits especiales, puedes crear imágenes específicas:

#### Traits Individuales:
- `pregnant_{skill}.png` - Si el worker tiene el trait "Pregnant"
- `futa_{skill}.png` - Si el worker tiene el trait "Futa"
- `transformed_{skill}.png` - Si el worker tiene el trait "Transformed"
- `magical_{skill}.png` - Si el worker tiene el trait "Magical"

#### Traits Combinados:
- `transformed_magical_futa_pregnant_{skill}.png` - Si tiene los 4 traits
- `transformed_magical_futa_{skill}.png` - Si tiene Transformed + Magical + Futa
- `transformed_magical_pregnant_{skill}.png` - Si tiene Transformed + Magical + Pregnant
- `transformed_futa_pregnant_{skill}.png` - Si tiene Transformed + Futa + Pregnant
- `magical_futa_pregnant_{skill}.png` - Si tiene Magical + Futa + Pregnant
- `transformed_magical_{skill}.png` - Si tiene Transformed + Magical
- `transformed_futa_{skill}.png` - Si tiene Transformed + Futa
- `transformed_pregnant_{skill}.png` - Si tiene Transformed + Pregnant
- `magical_futa_{skill}.png` - Si tiene Magical + Futa
- `magical_pregnant_{skill}.png` - Si tiene Magical + Pregnant
- `futa_pregnant_{skill}.png` - Si tiene Futa + Pregnant

---

## 📋 Resumen Mínimo

### Estructura de Carpeta Mínima:
```
game/images/workers/{folder_del_worker}/
├── Profile.png (o Profile.jpg)  ← REQUERIDA
```

### Estructura de Carpeta Recomendada:
```
game/images/workers/{folder_del_worker}/
├── Profile.png (o Profile.jpg)  ← REQUERIDA
├── sex.png                      ← Opcional (si tiene habilidad Sex)
├── sex_failure.png              ← Opcional (variante de fallo)
├── anal.png                     ← Opcional (si tiene habilidad Anal)
├── oral.png                     ← Opcional (si tiene habilidad Oral)
└── ... (más imágenes según habilidades)
```

---

## 🎨 Formatos Soportados

El sistema soporta estos formatos de imagen/video:
- `.png` ✅
- `.jpg` ✅
- `.jpeg` ✅
- `.webp` ✅
- `.webm` (video) ✅
- `.mp4` (video) ✅

---

## 📝 Notas Importantes

1. **Búsqueda Flexible:** El sistema busca imágenes de forma flexible:
   - No distingue mayúsculas/minúsculas
   - Busca el patrón dentro del nombre del archivo
   - Soporta variaciones numeradas: `sex (1).png`, `sex (2).png`, etc.

2. **Fallback:** Si no se encuentra una imagen específica, el sistema usa la imagen de perfil como fallback.

3. **Caché:** El sistema usa caché para mantener consistencia visual durante el mismo Daily Report.

4. **Prioridad de Búsqueda:**
   - Primero busca en la carpeta del worker
   - Luego busca en la carpeta default (`images/workers/aspen/`)
   - Finalmente usa la imagen de perfil

---

## ✅ Checklist Mínimo para un Worker

- [ ] **Imagen de perfil** (`Profile.png` o `Profile.jpg`) en `game/images/workers/{folder}/`
- [ ] El campo `"folder"` en el JSON del worker coincide con el nombre de la carpeta
- [ ] La imagen está en un formato soportado (png, jpg, jpeg, webp)

**Con solo estos 3 requisitos, el worker funcionará correctamente en el juego.**



