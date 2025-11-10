# Sistema de Interacciones - Guía de Estructura

## Resumen del Sistema

El sistema de interacciones ha sido reorganizado para seguir una estructura clara y escalable:

### Estructura Base
- **4 Categorías**: Discipline, Romance, Friendship, Joy
- **4 Niveles por categoría**:
  - **Nivel 1**: Siempre disponible
  - **Nivel 2**: Desbloqueado tras 5 usos del Nivel 1
  - **Nivel 3**: Desbloqueado tras 5 usos del Nivel 2
  - **Nivel 4**: Desbloqueado tras 5 usos del Nivel 3 (farmeable, coste/beneficio óptimo)

### Combinaciones de Género
Cada interacción debe tener variantes para:
- **Jugador**: Lord (masculino) o Lady (femenino)
- **Worker**: Male (masculino) o Female (femenino)

**Total**: 4 categorías × 4 niveles × 4 combinaciones = **64 interacciones base**

## Estructura JSON

Cada interacción debe tener los siguientes campos:

```json
{
  "id": "categoria_levelN_generoJugador_generoWorker",
  "name": "Nombre de la Interacción",
  "description": "Descripción narrativa de lo que ocurre",
  "interaction_level": 1-4,
  "cost_energy": 1-4,
  "cost_money": 0-100,
  "effect": {
    "stat_name": valor,
    "flags": {
      "cooldown_flag": {
        "value": true,
        "duration": días
      }
    }
  },
  "gender_filter": "male" | "female" | null,
  "worker_gender": "male" | "female" | null,
  "categories": ["CategoryName"],
  "image": "nombre_imagen",
  "nsfw": true | false,
  "stat_requirements": {},
  "required_flags": {},
  "excluded_flags": {}
}
```

## Progresión de Costes y Efectos

### Nivel 1 (Básico)
- **Coste Energía**: 1
- **Coste Dinero**: 0-5
- **Efectos**: Pequeños (+2-5 en stats principales)

### Nivel 2 (Intermedio)
- **Coste Energía**: 2
- **Coste Dinero**: 10-15
- **Efectos**: Moderados (+5-12 en stats principales)

### Nivel 3 (Avanzado)
- **Coste Energía**: 3
- **Coste Dinero**: 25-35
- **Efectos**: Grandes (+15-25 en stats principales)
- **Nota**: Puede ser NSFW

### Nivel 4 (Farmeable)
- **Coste Energía**: 2 (optimizado)
- **Coste Dinero**: 15-20 (optimizado)
- **Efectos**: Buenos (+15-20 en stats principales)
- **Nota**: Diseñado para uso repetido con mejor coste/beneficio

## Sistema de Desbloqueo

El sistema rastrea automáticamente los usos de cada nivel usando flags:
- `{categoria}_uses_level_1`: Contador de usos del nivel 1
- `{categoria}_uses_level_2`: Contador de usos del nivel 2
- `{categoria}_uses_level_3`: Contador de usos del nivel 3

**Ejemplo**: Para desbloquear Romance Nivel 2, se necesitan 5 usos de Romance Nivel 1.

## Sistema de Visualización

Cuando se ejecuta una interacción:
1. Se muestra la **descripción** primero (texto narrativo)
2. Luego se muestra la **imagen** como "cutscene"
3. Se aplican los efectos y costes

## Archivos

- `interactions_structured.json`: Archivo con la nueva estructura (ejemplo completo de Discipline)
- `interactions_main.json`: Archivo original (mantener para compatibilidad o migrar)
- `interactions_special.json`: Interacciones especiales para workers específicos

## Notas de Implementación

1. El sistema de filtrado automáticamente:
   - Filtra por género del jugador (`gender_filter`)
   - Filtra por género del worker (`worker_gender`)
   - Filtra por nivel de desbloqueo (`interaction_level`)
   - Filtra por stats requeridos
   - Filtra por flags requeridos/excluidos

2. Las imágenes deben estar en:
   - `images/workers/{worker_folder}/` (prioridad)
   - `images/workers/default/` (fallback)

3. El sistema es retrocompatible: interacciones sin `interaction_level` se muestran siempre.

