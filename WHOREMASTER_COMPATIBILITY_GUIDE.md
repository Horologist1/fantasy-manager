# Guía de Compatibilidad: Whoremaster → Fantasy Manager

## Resumen Ejecutivo

Este documento analiza la compatibilidad entre **Whoremaster 7.2.2** y **Fantasy Manager**, proporcionando un mapeo completo de estructuras de datos y recomendaciones para la conversión.

---

## 📊 Comparación de Arquitecturas

### Formatos de Datos

| Aspecto | Whoremaster | Fantasy Manager |
|---------|-------------|-----------------|
| **Formato Personajes** | XML (.girlsx, .rgirlsx) | JSON |
| **Formato Items** | XML (.itemsx) | JSON |
| **Formato Traits** | XML (.traitsx) | JSON |
| **Formato Jobs** | XML | Ren'Py Scripts |
| **Imágenes** | Carpeta por personaje | Carpeta por personaje |

### Estructura de Personajes

#### Whoremaster (`.girlsx` - Único)
```xml
<Girl Name="Aeris Gainsborough" 
      Charisma="70" Intelligence="60" Agility="30" ...>
    <Trait Name="Cute" />
    <Trait Name="Strong Magic" />
</Girl>
```

#### Whoremaster (`.rgirlsx` - Random/Template)
```xml
<Girl Name="RgirlOrc" Desc="..." Human="No">
    <Stat Name="Charisma" Min="20" Max="70" />
    <Skill Name="Combat" Min="30" Max="50" />
    <Trait Name="Big Boobs" Percent="50" />
</Girl>
```

#### Fantasy Manager (JSON)
```json
{
  "name": "Elena",
  "folder": "tangirl",
  "cost": 1400,
  "nsfw": true,
  "unique": false,
  "skills": {
    "Sex": 23, "Combat": 40, "Charm": 45, ...
  },
  "traits": ["Human", "Beautiful"],
  "description": "...",
  "gender": "female",
  "comfort_desired": 4
}
```

---

## 🎯 Mapeo de Skills

### Skills Directos

| Whoremaster | Fantasy Manager | Notas |
|-------------|-----------------|-------|
| Combat | Combat | ✅ Directo |
| Service | Service | ✅ Directo |
| Anal | Anal | ✅ Directo |
| BDSM | BDSM | ✅ Directo |
| Group | Group | ✅ Directo |
| Strip | Striptease | ✅ Renombrado |

### Skills Sexuales

| Whoremaster | Fantasy Manager | Notas |
|-------------|-----------------|-------|
| NormalSex | Sex | ✅ Principal skill sexual |
| OralSex | Oral | ✅ Directo |
| Lesbian | Homo | ✅ Homosexual activities |
| Handjob | Hand | ✅ Directo |
| TittySex | Special | Combinado en Special |
| Footjob | Special | Combinado en Special |
| Beastiality | Extreme | Mapeado a Extreme |

### Skills No-Sexuales

| Whoremaster | Fantasy Manager | Notas |
|-------------|-----------------|-------|
| Magic | Craft | Habilidades mágicas → crafting |
| Medicine | Clever | Conocimiento médico → inteligencia |
| Performance | Charm | Actuación → carisma |
| Crafting | Craft | ✅ Directo |
| Farming | Service | Trabajo agrícola → servicio |
| Cooking | Service | Cocina → servicio |
| Herbalism | Craft | Herbalismo → crafting |
| Brewing | Clever | Destilación → inteligencia |
| AnimalHandling | Craft | Animales → crafting |

### Stats → Skills (Contribución)

| WM Stat | FM Skill | Factor |
|---------|----------|--------|
| Charisma | Charm | 50% |
| Intelligence | Clever | 50% |
| Agility | Agility | 100% |
| Strength | Combat | 30% |
| Constitution | Combat | 20% |
| Confidence | Charm | 30% |
| Beauty | Charm | 20% |
| Libido | Sex | 20% |

---

## 🏷️ Mapeo de Traits

### Traits de Personalidad

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| Agile | Agile |
| Brawler | Brawler |
| Clumsy | Clumsy |
| Delicate | Delicate |
| Strong | Strong |
| Tough | Tough |
| Open Minded | Open Minded |
| Shy | Shy |
| Nervous | Nervous |
| Optimist | Optimist |
| Pessimist | Pessimist |
| Quick Learner | Quick Learner |
| Slow Learner | Slow Learner |
| Sadistic | Sadistic |
| Fearless | Confident |
| Iron Will | Rebellious |
| Broken Will | Obedient |
| Dependant | Dependant |

### Traits de Apariencia

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| Cute | Cute |
| Exotic | Exotic |
| Beauty Mark | Beauty Mark |
| Cool Scars | Cool Scars |
| Small Scars / Horrific Scars | Scarred |
| Tattooed / Small Tattoos | Tattooed |
| Big Boobs / Busty Boobs / Giant Juggs | Large Breasts |
| Small Boobs / Petite Breasts | Small Breasts |
| Flat Chest | Flat Chest |
| Great Arse / Deluxe Derriere | Firm Ass |
| Plump Tush / Wide Bottom | Soft Ass |

### Traits de Especie/Raza

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| (default) | Human |
| Elf | Elf |
| Dwarf | Dwarf |
| Demon | Demon |
| Angel | Angel |
| Not Human | Transformed |
| Cat Girl / Cow Girl / Furry | Transformed |
| Succubus | Demon |
| Vampire | Vampire |
| Dryad | Elf |

### Traits Profesionales

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| Adventurer | Adventurer |
| Maid | Maid |
| Singer | Singer |
| Teacher | Teacher |
| Waitress | Waitress |
| Chef | Waitress |
| Doctor | Teacher |
| Hunter | Adventurer |

### Traits Sexuales y de Libido

| Whoremaster | Fantasy Manager | Notas |
|-------------|-----------------|-------|
| Nymphomaniac | Nymph-Touched | Femenino, libido alto, +Sex +Oral |
| (masculino hipersexual) | Beast Within | Masculino, libido alto, +Sex +Group |
| High Sex Drive | Burning Desire | Regeneración libido +4/día |
| Insatiable | Insatiable | +6 regen, +15 max, +Sex +Group |
| Chaste | Frigid Soul | Cap libido a 5, trabajo frío |
| (resistente) | Stamina of the Bull | +3 regen, +5 max, +5 health |
| (frágil) | Easily Spent | -3 regen, -5 max |
| (paciente) | Slow Burn | -2 regen, +BDSM +Special |
| Fast Orgasms | Sensitive | +Sex +Oral +BDSM |
| Slow Orgasms | Numb | +BDSM +Extreme |
| Deep Throat | Pierced | +Oral +Sex |
| Charismatic | Charismatic | +Charm |
| Charming | Charming | +Charm |
| Elegant | Elegant | +Charm +Striptease |

---

## 📦 Mapeo de Items

### Tipos de Item

| WM Type | FM Type |
|---------|---------|
| Ring, Necklace, Shoes, Boots, Hat, Glasses, Earring, Bracelet | accessory |
| Small Weapon, Large Weapon, Staff | weapon |
| Armor, Shield, Helmet | armor |
| Dress, Lingerie, Underwear, Outfit | clothing |
| Consumable, Food, Drug, Medicine, Makeup | consumable |
| Misc | accessory |

### Efectos de Item

| WM Effect | FM Effect |
|-----------|-----------|
| Skill: Combat | skill_modifiers.Combat |
| Stat: Charisma | skill_modifiers.Charm |
| Stat: Intelligence | skill_modifiers.Clever |
| Stat: Constitution | health |
| Stat: Tiredness | energy (invertido) |
| Stat: Libido | libido |
| Stat: Happiness | (no directo) |

---

## 📁 Estructura de Carpetas de Imágenes

### ✅ Buena Noticia: Alta Compatibilidad

**Fantasy Manager ya entiende la mayoría de nombres de imágenes de Whoremaster.**

El sistema de búsqueda de imágenes de FM es:
- **Case-insensitive** (no importan mayúsculas/minúsculas)
- **Busca múltiples patrones** para cada skill

### Nombres que FM Ya Entiende (sin renombrar):

| WM Name | FM Skill | Notas |
|---------|----------|-------|
| `les`, `lesbian` | Homo | FM busca "les" o "gay" |
| `gay` | Homo | ✅ Directo |
| `beast` | Extreme | FM busca "beast" o "extreme" |
| `strip` | Striptease | FM busca "strip" o "striptease" |
| `titty`, `tittysex` | Special | FM busca "titty" o "special" |
| `wait`, `maid` | Service | FM busca "wait", "service", "maid" |
| `sex`, `oral`, `anal`, `bdsm`, `group` | Directo | ✅ Nombres iguales |
| `combat`, `hand`, `charm` | Directo | ✅ Nombres iguales |

### Nombres que SÍ Necesitan Renombrar:

| WM Name | FM Name | Motivo |
|---------|---------|--------|
| `Portrait` | `Profile` | FM busca "profile", no "portrait" |
| `Foot`, `Footjob` | `hand` | FM no busca "foot" |
| `Dildo`, `Mast` | `special` | No están en patrones FM |
| `Escort`, `Formal` | `charm` | No están en patrones FM |
| `Swim`, `Bath` | `rest` | Para imágenes de descanso |
| `Nurse`, `Shop` | `service` | Servicio genérico |
| `Magic`, `Fight` | `craft`, `combat` | Renombre simple |
| `Herd` | `extreme` | "beast" funciona, "herd" no |

### Estructura de Carpetas

```
Whoremaster:                          Fantasy Manager:
Resources/Characters/                 game/images/workers/
├── Aeris Gainsborough/              └── aeris_gainsborough/
│   ├── Portrait.jpg    ───→            ├── Profile.jpg (renombrar)
│   ├── Sex.jpg         ───→            ├── Sex.jpg (funciona directo)
│   ├── Les.jpg         ───→            ├── Les.jpg (funciona directo!)
│   ├── Strip.jpg       ───→            ├── Strip.jpg (funciona directo!)
│   ├── Beast.gif       ───→            ├── Beast.webm (convertir GIF)
│   └── ...                             └── ...
└── Aeris Gainsborough.girlsx        workers_wm.json (convertido)
```

### Videos en lugar de GIFs

**Importante**: Ren'Py no puede reproducir GIFs animados. Use el conversor para transformar GIFs a WebM:

```bash
python rename_wm_images.py "carpeta_personaje" --convert-gifs
```

FM soporta estos formatos de video: `.webm`, `.mp4`, `.ogv`

---

## 🔧 Uso de los Conversores

### Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `wm_to_fm_converter.py` | Convierte datos XML de personajes/items a JSON |
| `rename_wm_images.py` | Renombra imágenes y convierte GIFs a WebM |

### 1. Conversor de Datos (XML → JSON)

```bash
# Convertir personajes
python wm_to_fm_converter.py \
    --characters "C:/path/to/WM/Resources/Characters" \
    --output "workers_wm.json"

# Convertir con copia de imágenes
python wm_to_fm_converter.py \
    --characters "C:/path/to/WM/Resources/Characters" \
    --output "workers_wm.json" \
    --copy-images \
    --image-dest "C:/path/to/FM/game/images/workers"

# Convertir items
python wm_to_fm_converter.py \
    --items "C:/path/to/WM/Resources/Items" \
    --output "items_wm.json"
```

### 2. Conversor de Imágenes

La mayoría de imágenes de WM funcionan directamente en FM. Este script solo:
- Renombra imágenes que FM no reconoce (Portrait→Profile, etc.)
- Convierte GIFs animados a WebM (Ren'Py no soporta GIF)

```bash
# Ver qué se haría (sin cambiar nada)
python rename_wm_images.py "../game/images/workers/aeris" --dry-run

# Renombrar solo
python rename_wm_images.py "../game/images/workers/aeris"

# Renombrar + Convertir GIFs a WebM (requiere ffmpeg)
python rename_wm_images.py "../game/images/workers/aeris" --convert-gifs

# Procesar TODAS las carpetas de workers
python rename_wm_images.py "../game/images/workers" --all --convert-gifs
```

**Nota**: Para conversión de GIFs, necesitas [ffmpeg](https://ffmpeg.org/) instalado y en PATH.

### Ejemplo Práctico Completo

```bash
cd "C:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager\devkit"

# 1. Convertir datos de personajes
python wm_to_fm_converter.py ^
    --characters "..\..\WM-7.2.2-win64 - copia\Resources\Characters" ^
    --output "..\game\data\workers\workers_wm.json" ^
    --copy-images ^
    --image-dest "..\game\images\workers"

# 2. Procesar imágenes (renombrar + GIF→WebM)
python rename_wm_images.py "..\game\images\workers" --all --convert-gifs
```

---

## 💡 Propuestas de Mejoras para Fantasy Manager

### 1. Sistema de Libido Expandido

**Estado Actual**: FM tiene `libido` como un entero simple (0-20) que afecta principalmente el éxito en trabajos sexuales.

**Propuesta Mejorada**: Expandir libido para crear más dinamismo en el gameplay:

```python
# En worker_defaults.rpy
worker.setdefault("libido", {
    "base": 10,          # Nivel base del personaje (permanente)
    "current": 10,       # Nivel actual (fluctúa)
    "max": 20,           # Máximo posible
    "regen_rate": 2,     # Regeneración por día sin trabajo sexual
    "decay_rate": 3,     # Reducción por trabajo sexual intenso
})
```

**Mecánicas sugeridas**:
- **Trabajos NSFW reducen libido**: Cada trabajo sexual reduce `current` según intensidad
  - Sex, Oral: -1 a -2
  - Group, Extreme: -3 a -4
  - BDSM, Anal: -2 a -3
- **Libido bajo = Menor rendimiento**: Si `current < base * 0.5`, penalización en skills sexuales
- **Libido alto = Bonus**: Si `current > base * 1.5`, bonus a earnings y satisfacción
- **Regeneración**: +`regen_rate` por día de descanso o trabajo no-sexual
- **Traits afectan libido** (ya implementados):
  - "Burning Desire": +4 regen, +8 max
  - "Nymph-Touched" / "Beast Within": +5 regen, +12 max, min 10
  - "Insatiable": +6 regen, +15 max, min 8
  - "Frigid Soul": cap a 5
  - "Stamina of the Bull": +3 regen, +5 max
  - "Easily Spent": -3 regen, -5 max
  - "Slow Burn": -2 regen (pero +BDSM)
- **Items**: Pociones de libido (afrodisíacos) podrían aumentar temporalmente

**Implementación simplificada (alternativa)**:
```python
# Si no quieres complejidad, simplemente:
worker.setdefault("libido_base", 10)  # Permanente
worker.setdefault("libido_current", 10)  # Fluctúa con el trabajo

# Regeneración en end_day
if worker["libido_current"] < worker["libido_base"]:
    worker["libido_current"] = min(
        worker["libido_base"], 
        worker["libido_current"] + 2
    )
```

### 2. Sistema de Crafting de Items

WM tiene sistema de crafting. FM podría añadir:

```python
item = {
    "id": "silver_ring",
    "crafting": {
        "required_skill": "Craft",
        "required_level": 20,
        "materials": ["silver_ore", "mana_crystal"],
        "craft_time": 2  # días
    }
}
```

### 3. Conversión GIF → WebM (Video)

Ren'Py **no puede reproducir GIFs animados**, pero **sí soporta videos** (WebM, MP4).
El conversor incluye funcionalidad para convertir GIFs a WebM automáticamente:

```bash
# Convertir carpeta de imágenes con GIFs
python rename_wm_images.py "../game/images/workers/aeris" --convert-gifs
```

Requiere **ffmpeg** instalado y en PATH.

### 4. Sistema de Embarazo/Fertilidad (Futuro)

WM tiene sistema completo de fertilidad/embarazo que podría añadirse a FM en futuras versiones.

---

## ⚠️ Limitaciones de la Conversión

1. **Traits sin equivalente directo**: Algunos traits de WM no tienen equivalente en FM y se pierden o mapean a alternativas.

2. **Sistema de Embarazo**: WM tiene sistema de fertilidad/embarazo que FM no implementa aún.

3. **Sistema de Enfermedades**: WM tiene STDs (AIDS, Herpes, etc.) que FM no tiene.

4. **GIFs Animados**: Ren'Py no soporta GIFs. Usar conversor para transformar a WebM.

5. **Jobs vs Buildings**: WM usa sistema de Jobs, FM usa sistema de Buildings con diferentes mecánicas.

6. **Stats WM vs Traits FM**: 
   - WM tiene stats separados (Constitution, Beauty, Intelligence)
   - FM usa traits para representar estos conceptos (Strong, Beautiful, Clever)
   - La conversión no crea nuevos stats, sino que asigna traits equivalentes

---

## 📋 Checklist de Conversión

### Paso 1: Convertir Datos
- [ ] Ejecutar `wm_to_fm_converter.py` con `--copy-images`
- [ ] Verificar JSON generado (workers_wm.json)
- [ ] Verificar que las carpetas de imágenes se copiaron

### Paso 2: Procesar Imágenes
- [ ] Ejecutar `rename_wm_images.py --dry-run` para previsualizar
- [ ] Ejecutar `rename_wm_images.py --convert-gifs` para aplicar
- [ ] Verificar que GIFs se convirtieron a WebM

### Paso 3: Verificación
- [ ] Verificar que cada personaje tiene imagen Profile
- [ ] Verificar que traits se mapearon correctamente
- [ ] Ajustar skills manualmente si necesario
- [ ] Probar personajes en el juego

### Paso 4: Items (Opcional)
- [ ] Ejecutar conversor en Items
- [ ] Merge items convertidos con items.json existente

---

## 🔄 Actualizaciones Futuras

Este documento se actualizará conforme:
- Se añadan nuevos traits a Fantasy Manager
- Se implementen nuevos sistemas (embarazo, enfermedades, etc.)
- Se mejore el conversor con más opciones

**Última actualización**: Diciembre 2024
**Versión del Conversor**: 1.0

