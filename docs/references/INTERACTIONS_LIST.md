# Lista de Interacciones Disponibles

Este documento lista todas las interacciones del sistema organizadas por categoría, nivel y combinaciones de género.

---

## 📋 Estructura General

Cada categoría tiene **4 niveles**:
- **Nivel 1**: Siempre disponible
- **Nivel 2**: Desbloqueado tras 5 usos del Nivel 1
- **Nivel 3**: Desbloqueado tras 5 usos del Nivel 2
- **Nivel 4**: Desbloqueado tras 5 usos del Nivel 3 (farmeable, coste/beneficio óptimo)

Cada nivel tiene variantes para **4 combinaciones de género**:
- Lord (masculino) + Worker Femenino
- Lord (masculino) + Worker Masculino
- Lady (femenino) + Worker Femenino
- Lady (femenino) + Worker Masculino

---

## ⚔️ DISCIPLINE (Disciplina)

### Nivel 1 - Básico
**Coste:** 1 Energía | 0 Dinero

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `discipline_level1_lord_female` | Gentle Correction | Lord | Female | -3 rebelliousness, +1 relationship |
| `discipline_level1_lord_male` | Direct Talk | Lord | Male | -3 rebelliousness, +1 relationship |
| `discipline_level1_lady_female` | Kind Guidance | Lady | Female | -3 rebelliousness, +1 relationship |
| `discipline_level1_lady_male` | Respectful Reminder | Lady | Male | -3 rebelliousness, +1 relationship |

### Nivel 2 - Intermedio
**Coste:** 2 Energía | 10 Dinero

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `discipline_level2_lord_female` | Firm Training | Lord | Female | -5 rebelliousness, +2 relationship |
| `discipline_level2_lord_male` | Intensive Training | Lord | Male | -5 rebelliousness, +2 relationship |
| `discipline_level2_lady_female` | Structured Guidance | Lady | Female | -5 rebelliousness, +2 relationship |
| `discipline_level2_lady_male` | Rigorous Instruction | Lady | Male | -5 rebelliousness, +2 relationship |

### Nivel 3 - Avanzado
**Coste:** 3 Energía | 0 Dinero | ⚠️ NSFW

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `discipline_level3_lord_female` | Complete Submission | Lord | Female | -7 rebelliousness, +3 relationship, +2 romance |
| `discipline_level3_lord_male` | Alpha Dominance | Lord | Male | -7 rebelliousness, +3 relationship, +2 romance |
| `discipline_level3_lady_female` | Absolute Obedience | Lady | Female | -7 rebelliousness, +3 relationship, +2 romance |
| `discipline_level3_lady_male` | Total Submission | Lady | Male | -7 rebelliousness, +3 relationship, +2 romance |

**Requisitos:** relationship ≥ 20

### Nivel 4 - Farmeable
**Coste:** 2 Energía | 0 Dinero

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `discipline_level4_lord_female` | Perfect Discipline | Lord | Female | -6 rebelliousness, +3 relationship |
| `discipline_level4_lord_male` | Masterful Control | Lord | Male | -6 rebelliousness, +3 relationship |
| `discipline_level4_lady_female` | Elegant Authority | Lady | Female | -6 rebelliousness, +3 relationship |
| `discipline_level4_lady_male` | Refined Command | Lady | Male | -6 rebelliousness, +3 relationship |

**Requisitos:** relationship ≥ 30

---

## 💕 ROMANCE (Romance)

### Nivel 1 - Básico
**Coste:** 1 Energía | 0 Dinero

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `romance_level1_lord_female` | Charming Banter | Lord | Female | +3 romance, +1 relationship |
| `romance_level1_lord_male` | Charming Banter | Lord | Male | +3 romance, +1 relationship |
| `romance_level1_lady_female` | Playful Flirting | Lady | Female | +3 romance, +1 relationship |
| `romance_level1_lady_male` | Elegant Flirtation | Lady | Male | +3 romance, +1 relationship |

**Requisitos:** relationship ≥ 10 (Lord+Male/Female), relationship ≥ 15 (Lady+Female)

### Nivel 2 - Intermedio
**Coste:** 2 Energía | 20 Dinero

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `romance_level2_lord_female` | Private Connection | Lord | Female | +5 romance, +2 relationship |
| `romance_level2_lord_male` | Intimate Evening | Lord | Male | +5 romance, +2 relationship |
| `romance_level2_lady_female` | Intimate Evening | Lady | Female | +5 romance, +2 relationship |
| `romance_level2_lady_male` | Private Adventure | Lady | Male | +5 romance, +2 relationship |

**Requisitos:** romance ≥ 10, relationship ≥ 15 (Lord), relationship ≥ 20 (Lady+Female)

### Nivel 3 - Avanzado
**Coste:** 3 Energía | 12 Dinero | ⚠️ NSFW

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `romance_level3_lord_female` | Dominant Union | Lord | Female | +7 romance, +3 relationship, +2 joy |
| `romance_level3_lord_male` | Passionate Night | Lord | Male | +7 romance, +3 relationship, +2 joy |
| `romance_level3_lady_female` | Passionate Night | Lady | Female | +7 romance, +3 relationship, +2 joy |
| `romance_level3_lady_male` | Epic Adventure | Lady | Male | +7 romance, +3 relationship, +2 joy |

**Requisitos:** romance ≥ 20, relationship ≥ 25 (Lord), relationship ≥ 30 (Lady+Female)

### Nivel 4 - Farmeable
**Coste:** 2 Energía | 10 Dinero

| ID | Nombre | Jugador | Worker | Efectos |
|---|---|---|---|---|
| `romance_level4_lord_female` | Perfect Romance | Lord | Female | +6 romance, +3 relationship, +2 joy |
| `romance_level4_lord_male` | Masterful Romance | Lord | Male | +6 romance, +3 relationship, +2 joy |
| `romance_level4_lady_female` | Elegant Romance | Lady | Female | +6 romance, +3 relationship, +2 joy |
| `romance_level4_lady_male` | Refined Romance | Lady | Male | +6 romance, +3 relationship, +2 joy |

**Requisitos:** romance ≥ 30, relationship ≥ 30

---

## 🤝 FRIENDSHIP (Amistad)

*Nota: Las interacciones de Friendship aún no están implementadas en `interactions_structured.json`. Se pueden agregar siguiendo el mismo patrón.*

### Estructura Propuesta:

**Nivel 1:** Friendly Chat / Casual Conversation
- Coste: 1 Energía | 0 Dinero
- Efectos: +3 relationship

**Nivel 2:** Heart-to-Heart / Brotherhood Bond
- Coste: 2 Energía | 5-8 Dinero
- Efectos: +5 relationship, +2 joy

**Nivel 3:** Soul Sisters / Blood Brothers
- Coste: 3 Energía | 15-20 Dinero
- Efectos: +7 relationship, +3 joy, +2 romance

**Nivel 4:** Perfect Friendship (Farmeable)
- Coste: 2 Energía | 5-8 Dinero
- Efectos: +6 relationship, +3 joy

---

## 🎉 JOY (Alegría)

*Nota: Las interacciones de Joy aún no están implementadas en `interactions_structured.json`. Se pueden agregar siguiendo el mismo patrón.*

### Estructura Propuesta:

**Nivel 1:** Thoughtful Gift / Practical Present
- Coste: 1 Energía | 8-10 Dinero
- Efectos: +3 joy, +1 relationship

**Nivel 2:** Luxury Experience / Adventure Trip
- Coste: 2 Energía | 25-30 Dinero
- Efectos: +5 joy, +2 relationship, +1 romance

**Nivel 3:** Ultimate Fantasy / Epic Achievement
- Coste: 3 Energía | 50-60 Dinero
- Efectos: +7 joy, +3 relationship, +2 romance

**Nivel 4:** Perfect Joy (Farmeable)
- Coste: 2 Energía | 15-20 Dinero
- Efectos: +6 joy, +3 relationship, +2 romance

---

## 🎭 INTERACCIONES ESPECÍFICAS

Estas interacciones están diseñadas para trabajadores específicos o con traits especiales.

### Violet's Special Performance
- **ID:** `violet_special`
- **Categoría:** Romance
- **Worker Específico:** Violet
- **Coste:** 3 Energía | 0 Dinero
- **Efectos:** +30 romance, +15 relationship, +20 joy
- **Requisitos:** romance ≥ 0
- **Cooldown:** 5 días

### Enchanting Presence
- **ID:** `charming_beauty`
- **Categoría:** Romance
- **Traits Requeridos:** Beautiful, Charming
- **Coste:** 3 Energía | 0 Dinero
- **Efectos:** +35 romance, +20 joy, +15 relationship
- **Requisitos:** romance ≥ 15
- **Cooldown:** 4 días

---

## 📊 Resumen de Costes por Categoría

### Discipline
| Nivel | Energía | Dinero | Tipo |
|-------|---------|--------|------|
| 1 | 1 | 0 | Básico |
| 2 | 2 | 10 | Intermedio |
| 3 | 3 | 0 | Avanzado (NSFW) |
| 4 | 2 | 0 | Farmeable |

### Romance
| Nivel | Energía | Dinero | Tipo |
|-------|---------|--------|------|
| 1 | 1 | 0 | Básico |
| 2 | 2 | 20 | Intermedio |
| 3 | 3 | 12 | Avanzado (NSFW) |
| 4 | 2 | 10 | Farmeable |

### Friendship (Propuesto)
| Nivel | Energía | Dinero | Tipo |
|-------|---------|--------|------|
| 1 | 1 | 0 | Básico |
| 2 | 2 | 5-8 | Intermedio |
| 3 | 3 | 15-20 | Avanzado |
| 4 | 2 | 5-8 | Farmeable |

### Joy (Propuesto)
| Nivel | Energía | Dinero | Tipo |
|-------|---------|--------|------|
| 1 | 1 | 8-10 | Básico |
| 2 | 2 | 25-30 | Intermedio |
| 3 | 3 | 50-60 | Avanzado |
| 4 | 2 | 15-20 | Farmeable |

---

## 🔓 Sistema de Desbloqueo

El sistema rastrea automáticamente los usos de cada nivel usando flags:
- `{categoria}_uses_level_1`: Contador de usos del nivel 1
- `{categoria}_uses_level_2`: Contador de usos del nivel 2
- `{categoria}_uses_level_3`: Contador de usos del nivel 3

**Ejemplo:** Para desbloquear Romance Nivel 2, se necesitan 5 usos de Romance Nivel 1.

---

## 📝 Notas

- Todas las interacciones tienen cooldowns para evitar spam
- Las interacciones NSFW requieren que `persistent.nsfw_enabled` esté activado
- Las interacciones específicas aparecen solo para los trabajadores indicados
- Las interacciones con traits aparecen solo para trabajadores con esos traits
- El sistema es retrocompatible: interacciones sin `interaction_level` se muestran siempre

---

*Última actualización: Sistema de interacciones reorganizado con estructura de 4 niveles por categoría*

