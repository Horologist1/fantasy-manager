# Referencia de Imágenes del Sistema de Skills

## 📋 Skills que el Sistema Busca

El sistema busca imágenes usando estos nombres de skills (en minúsculas):

### Skills Estándar:
1. **sex** - Busca directamente "sex"
2. **anal** - Busca directamente "anal"
3. **bdsm** - Busca directamente "bdsm"
4. **hand** - Busca directamente "hand"
5. **oral** - Busca directamente "oral"
6. **homo** - Busca **"les"** O **"gay"** (múltiples patrones)
7. **special** - Busca directamente "special"
8. **group** - Busca directamente "group"
9. **extreme** - Busca directamente "extreme"
10. **striptease** - Busca **"strip"** O **"striptease"** (múltiples patrones)
11. **combat** - Busca directamente "combat"
12. **clever** - Busca directamente "clever"
13. **charm** - Busca directamente "charm"
14. **wait** - Busca **"service"** O **"maid"** (múltiples patrones)
15. **agility** - Busca directamente "agility"
16. **magic** - Busca directamente "magic"
17. **Specialty 4-12** - Busca directamente el nombre (lowercase)

## 🏷️ Prefijos de Traits

El sistema busca imágenes con estos prefijos basados en los traits del worker:

### Prefijos Individuales:
- **pregnant_** - Si el worker tiene el trait "Pregnant"
- **futa_** - Si el worker tiene el trait "Futa"
- **transformed_** - Si el worker tiene el trait "Transformed"

### Prefijos Combinados (en orden de prioridad):
1. **transformed_futa_pregnant_** - Si tiene los 3 traits
2. **transformed_futa_** - Si tiene Transformed + Futa
3. **transformed_pregnant_** - Si tiene Transformed + Pregnant
4. **futa_pregnant_** - Si tiene Futa + Pregnant

**Nota:** El orden de prioridad es: Transformed > Futa > Pregnant

## 🔖 Sufijos de Outcome

### Sufijos de Resultado:
- **_failure** - Para resultados de fallo (outcome: "failure" o "mediocre")
- **(sin sufijo)** - Para resultados de éxito (outcome: "success" o "critical_success")

## 📁 Estructura de Búsqueda de Imágenes

El sistema busca imágenes en este orden de prioridad:

### Para Skills:
1. `{worker_folder}/{prefix}_{skill}_{suffix}`
2. `{worker_folder}/{prefix}_{skill}`
3. `{worker_folder}/{skill}_{suffix}`
4. `{worker_folder}/{skill}`
5. `images/workers/default/{prefix}_{skill}_{suffix}`
6. `images/workers/default/{prefix}_{skill}`
7. `images/workers/default/{skill}_{suffix}`
8. `images/workers/default/{skill}`

### Para Eventos (story_image):
1. `{worker_folder}/{prefix}_{story_image}_{suffix}`
2. `{worker_folder}/{prefix}_{story_image}`
3. `{worker_folder}/{story_image}_{suffix}`
4. `{worker_folder}/{story_image}`
5. `images/workers/default/{prefix}_{story_image}_{suffix}`
6. `images/workers/default/{prefix}_{story_image}`
7. `images/workers/default/{story_image}_{suffix}`
8. `images/workers/default/{story_image}`

## 📝 Ejemplos de Nombres de Archivo

### Ejemplos con Skills:
- `sex.png` - Imagen general de sex
- `sex_failure.png` - Imagen de fallo para sex
- `pregnant_sex.png` - Imagen de sex para workers pregnant
- `pregnant_sex_failure.png` - Imagen de fallo de sex para workers pregnant
- `futa_anal.png` - Imagen de anal para workers futa
- `transformed_futa_oral.png` - Imagen de oral para workers transformed + futa
- `les.png` o `gay.png` - Imágenes para skill "homo"
- `service.png` o `maid.png` - Imágenes para skill "wait"
- `strip.png` o `striptease.png` - Imágenes para skill "striptease"

### Ejemplos con Eventos:
- `brothel_success.png` - Imagen de éxito para evento brothel
- `brothel_failure.png` - Imagen de fallo para evento brothel
- `pregnant_brothel.png` - Imagen de brothel para workers pregnant
- `pregnant_brothel_failure.png` - Imagen de fallo de brothel para workers pregnant

## 🎯 Formato de Archivos Soportados

El sistema soporta estos formatos de imagen/video:
- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.webm` (video)
- `.mp4` (video)

## 🔍 Búsqueda Flexible

El sistema usa búsqueda flexible que:
- Es **case-insensitive** (no distingue mayúsculas/minúsculas)
- Busca el patrón **dentro del nombre del archivo** (no requiere coincidencia exacta)
- Soporta variaciones numeradas como `sex (2).png`, `sex (3).png`, etc.

## 📌 Notas Importantes

1. **Exclusión de prefijos:** Si un worker NO tiene un trait, el sistema excluye automáticamente archivos que empiecen con ese prefijo (ej: si no es pregnant, no busca `pregnant_*.png`)

2. **Profile images:** El sistema también busca imágenes de perfil con el patrón `profile.*` como fallback

3. **Caché:** El sistema usa caché para mantener consistencia visual durante el mismo Daily Report

4. **Skills especiales:** Algunos skills buscan múltiples patrones:
   - `homo` → busca "les" Y "gay"
   - `wait` → busca "service" Y "maid"
   - `striptease` → busca "strip" Y "striptease"

## 📊 Resumen de Patrones de Búsqueda

### Patrones Base por Skill:
```
sex, anal, bdsm, hand, oral, special, group, extreme, combat, clever, charm, agility, magic
les, gay (para homo)
service, maid (para wait)
strip, striptease (para striptease)
```

### Patrones con Prefijos:
```
pregnant_{skill}
futa_{skill}
transformed_{skill}
transformed_futa_{skill}
transformed_pregnant_{skill}
futa_pregnant_{skill}
transformed_futa_pregnant_{skill}
```

### Patrones con Sufijos:
```
{skill}_failure
{prefix}_{skill}_failure
```

### Patrones Completos:
```
{prefix}_{skill}
{prefix}_{skill}_failure
{skill}
{skill}_failure
```



