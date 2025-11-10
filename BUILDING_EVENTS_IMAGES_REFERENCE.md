# Referencia de Imágenes de Eventos de Buildings

## 📋 Tipos de Imágenes en Eventos

El sistema de eventos de buildings busca 4 tipos de imágenes:
1. **background_image** - Imagen de fondo del evento
2. **success_image** - Imagen de éxito (outcome: "success" o "critical_success")
3. **failure_image** - Imagen de fallo (outcome: "failure" o "mediocre")
4. **story_image** - Imagen de historia (para trabajos diarios en buildings)

## 🏛️ Background Images (Fondos de Eventos)

### Eventos Específicos de Buildings:
- **brothel_caution** - Evento de precaución en brothel
- **brothel_health** - Evento de chequeo de salud en brothel
- **restaurant_shortage** - Evento de escasez en restaurant
- **restaurant_banquet** - Evento de banquete en restaurant
- **guild_dragon** - Evento de dragón en guild
- **guild_raid** - Evento de raid en guild
- **tavern_brawl** - Evento de pelea en tavern
- **tavern_wine** - Evento de crisis de vino en tavern
- **casino_rumors** - Evento de rumores en casino
- **casino_fraud** - Evento de fraude en casino

### Eventos Comunes:
- **duel_arena** - Duelo de caballeros
- **mystic_tent** - Tienda de místico
- **guild_rivalry** - Rivalidad de guilds
- **lost_heirloom** - Heirloom perdido
- **kitchen_chaos** - Caos en cocina
- **casino_table** - Mesa de casino
- **brothel_private** - Cliente privado en brothel
- **brothel_gift** - Regalo secreto en brothel
- **brothel_dance** - Baile en brothel
- **tavern_bard** - Bardo en tavern
- **restaurant_panic** - Pánico en restaurant

### Genéricos:
- **event_bg** - Fondo genérico para eventos (usado como fallback)

## ✅ Success Images (Imágenes de Éxito)

### Específicas por Building:
- **brothel_success** - Éxito en brothel
- **restaurant_success** - Éxito en restaurant
- **guild_success** - Éxito en guild
- **tavern_success** - Éxito en tavern
- **casino_success** - Éxito en casino

### Eventos Específicos:
- **duel_success** - Éxito en duelo
- **mystic_success** - Éxito con místico
- **heirloom_success** - Éxito encontrando heirloom
- **kitchen_success** - Éxito en cocina

### Genéricos:
- **generic_success** - Éxito genérico (usado como fallback)

## ❌ Failure Images (Imágenes de Fallo)

### Específicas por Building:
- **brothel_failure** - Fallo en brothel
- **restaurant_failure** - Fallo en restaurant
- **guild_failure** - Fallo en guild
- **tavern_failure** - Fallo en tavern
- **casino_failure** - Fallo en casino

### Eventos Específicos:
- **duel_failure** - Fallo en duelo
- **mystic_failure** - Fallo con místico
- **heirloom_failure** - Fallo encontrando heirloom
- **kitchen_failure** - Fallo en cocina

### Genéricos:
- **generic_failure** - Fallo genérico (usado como fallback)

## 📖 Story Images (Imágenes de Historias Diarias)

Estas imágenes se usan para los trabajos diarios de workers en buildings:

### Brothel - Prostitute:
- **prostitute_vanilla** / **prostitute_vanilla_failure**
- **prostitute_anal** / **prostitute_anal_failure**
- **prostitute_bdsm** / **prostitute_bdsm_failure**
- **prostitute_oral** / **prostitute_oral_failure**
- **prostitute_hand** / **prostitute_hand_failure**
- **prostitute_homo** / **prostitute_homo_failure**
- **prostitute_group** / **prostitute_group_failure**
- **prostitute_vip** / **prostitute_vip_failure**

### Brothel - Stripper:
- **stripper_regular** / **stripper_regular_failure**
- **stripper_private** / **stripper_private_failure**
- **stripper_vip** / **stripper_vip_failure**

### Restaurant - Service:
- **service_story1** / **service_story1_failure**
- **service_story1_restaurant** / **service_story1_restaurant_failure**
- **Profile.jpg** (fallback, sin failure)

### Restaurant - Cook:
- **cook_story1** / **cook_story1_failure**
- **cook_story2** / **cook_story2_failure**
- **Profile.jpg** (fallback, sin failure)

### Adventurers Guild - Quest:
- **solo_quest** / **solo_quest_failure**
- **party_quest** / **party_quest_failure**
- **monster_capture** / **monster_capture_failure**
- **rest_adventurer** (sin failure)

### Tavern - Bartender:
- **bartender_story1** / **bartender_story1_failure**

### Tavern - Performer:
- **performer_story1_tavern** / **performer_story1_tavern_failure**
- **performer_story2_tavern** / **performer_story2_tavern_failure**
- **Profile** (fallback, sin failure)

### Casino - Guard:
- **guard_story1_casino** / **guard_story1_casino_failure**
- **guard_story2_casino** / **guard_story2_casino_failure**
- **rest_casino** (sin failure)

## 🏷️ Prefijos y Sufijos Aplicables

### Prefijos de Traits (igual que en skills):
Los mismos prefijos de traits se aplican a las imágenes de eventos:
- **pregnant_** - Si el worker tiene el trait "Pregnant"
- **futa_** - Si el worker tiene el trait "Futa"
- **transformed_** - Si el worker tiene el trait "Transformed"
- **transformed_futa_**, **transformed_pregnant_**, **futa_pregnant_**, **transformed_futa_pregnant_** (combinaciones)

### Sufijos de Outcome:
- **_failure** - Para resultados de fallo
- **(sin sufijo)** - Para resultados de éxito

## 📁 Estructura de Búsqueda

El sistema busca imágenes en este orden de prioridad:

### Para Eventos (background_image, success_image, failure_image, story_image):
1. `{worker_folder}/{prefix}_{image_name}_{suffix}`
2. `{worker_folder}/{prefix}_{image_name}`
3. `{worker_folder}/{image_name}_{suffix}`
4. `{worker_folder}/{image_name}`
5. `images/workers/default/{prefix}_{image_name}_{suffix}`
6. `images/workers/default/{prefix}_{image_name}`
7. `images/workers/default/{image_name}_{suffix}`
8. `images/workers/default/{image_name}`

### Para Backgrounds:
Los backgrounds se buscan directamente con `renpy.loadable()`:
- `images/{background_image}.png` (o cualquier extensión válida)

## 📝 Ejemplos de Nombres de Archivo

### Background Images:
- `brothel_caution.png` - Fondo de evento de precaución
- `guild_dragon.png` - Fondo de evento de dragón
- `tavern_brawl.png` - Fondo de pelea en tavern

### Success/Failure Images:
- `brothel_success.png` - Éxito en brothel
- `brothel_failure.png` - Fallo en brothel
- `pregnant_brothel_success.png` - Éxito en brothel para workers pregnant
- `pregnant_brothel_failure.png` - Fallo en brothel para workers pregnant

### Story Images:
- `prostitute_vanilla.png` - Historia de prostitute vanilla (éxito)
- `prostitute_vanilla_failure.png` - Historia de prostitute vanilla (fallo)
- `pregnant_prostitute_anal.png` - Historia de prostitute anal para workers pregnant
- `cook_story1.png` - Historia de cocinero
- `cook_story1_failure.png` - Historia de cocinero (fallo)

## 🎯 Formato de Archivos Soportados

El sistema soporta estos formatos:
- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.webm` (video)
- `.mp4` (video)

## 📊 Resumen Completo

### Background Images (Total: 12 únicos):
```
brothel_caution, brothel_health
restaurant_shortage, restaurant_banquet, restaurant_panic
guild_dragon, guild_raid, guild_rivalry
tavern_brawl, tavern_wine, tavern_bard
casino_rumors, casino_fraud, casino_table
duel_arena, mystic_tent, lost_heirloom, kitchen_chaos
brothel_private, brothel_gift, brothel_dance
event_bg (genérico)
```

### Success Images (Total: 9 únicos):
```
brothel_success, restaurant_success, guild_success
tavern_success, casino_success
duel_success, mystic_success, heirloom_success, kitchen_success
generic_success (genérico)
```

### Failure Images (Total: 9 únicos):
```
brothel_failure, restaurant_failure, guild_failure
tavern_failure, casino_failure
duel_failure, mystic_failure, heirloom_failure, kitchen_failure
generic_failure (genérico)
```

### Story Images (Total: 20 únicos):
```
prostitute_vanilla, prostitute_anal, prostitute_bdsm
prostitute_oral, prostitute_hand, prostitute_homo
prostitute_group, prostitute_vip
stripper_regular, stripper_private, stripper_vip
service_story1, service_story1_restaurant
cook_story1, cook_story2
solo_quest, party_quest, monster_capture, rest_adventurer
bartender_story1
performer_story1_tavern, performer_story2_tavern
guard_story1_casino, guard_story2_casino, rest_casino
Profile.jpg / Profile (fallback)
```

## 🔍 Notas Importantes

1. **Backgrounds vs Worker Images:**
   - Los `background_image` se buscan en `images/` directamente
   - Las `success_image`, `failure_image`, y `story_image` se buscan en `images/workers/{folder}/` o `images/workers/default/`

2. **Sufijos automáticos:**
   - Si el outcome es "failure" o "mediocre", busca `{image}_failure`
   - Si el outcome es "success" o "critical_success", busca `{image}` (sin _failure)

3. **Prefijos de traits:**
   - Se aplican igual que en skills: `pregnant_`, `futa_`, `transformed_`, y combinaciones

4. **Fallbacks:**
   - Si no encuentra imagen específica, usa `generic_success` o `generic_failure`
   - Si no encuentra story_image, usa `Profile.jpg` o `Profile`

5. **Búsqueda flexible:**
   - Case-insensitive
   - Busca el patrón dentro del nombre del archivo
   - Soporta variaciones numeradas como `brothel_success (2).png`



