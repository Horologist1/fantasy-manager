# Propuesta: traits físicos positivos para pociones de alquimia

Las pociones de alquimia (craft-only) pueden otorgar **un trait permanente** al worker que la usa. Esta lista propone todos los traits que son **claramente físicos (o cuerpo/apariencia) y positivos** y tienen sentido como efecto de una poción. Tú corriges o recortas lo que no quieras.

---

## Ya implementados (pociones existentes)

| Trait           | Poción              | NSFW |
|-----------------|---------------------|------|
| Strong          | Elixir of Strength  | No   |
| Tough           | Elixir of Toughness | No   |
| Transformed     | Elixir of Transformation | No |
| Magical         | Elixir of Magic     | No   |
| Large Breasts   | Potion of the Bust  | Sí (female) |
| Troll Blood     | **Troll Blood** (poción) | No – trait +10 Health Regen/día, no acumulable |

---

## Propuesta: SFW (tienen sentido como poción “física” o de apariencia)

| Trait        | Efecto del trait | Notas |
|-------------|-------------------|--------|
| **Robust**  | +10 Health, +2 Health Regen | Cuerpo robusto, muy físico. |
| **Energetic** | +10 Energy | Vitalidad / energía; encaja como poción. |
| **Agile**   | +1 Agility, +1 Striptease | Cuerpo ágil. |
| **Great Figure** | +20% $, +2 Charm, +1 Striptease | Figura excepcional. |
| **Long Legs** | +10% $, +2 Agility, +2 Striptease | Piernas largas. |
| **Exotic**  | +25% $ | Apariencia inusual/cautivadora. |
| **Beautiful** | +20% $ | Belleza (apariencia). |
| **Nice Tan** | +10% $ | Bronceado (apariencia física). |
| **Tomboy**   | +2 Combat, +1 Agility | Estilo físico / actitud física. |
| **Radiant** | +20% $, +1 Health Regen, +10 Joy | Brillo/radiancia. |
| **Graceful** | +10% $, +2 Charm, +1 Clever | Gracia física. |
| **Elegant** | +15% $, +1 Striptease, +1 Charm | Elegancia de presencia. |

Opcionales (menos claros como “poción física”):

- **Confident** (+2 Charm, +1 Striptease) – más mental que corporal.
- **Cool Scars** (+5% $, +1 Combat) – tiene sentido temático pero una poción que “da cicatrices” es rara; incluir solo si te encaja.

---

## Propuesta: NSFW (solo si `persistent.nsfw_enabled`)

| Trait           | Efecto del trait | Notas |
|-----------------|-------------------|--------|
| **Small Breasts** | +5% $, +1 Agility, +1 Charm | Female. |
| **Firm Ass**    | +15% $, +2 Anal, +1 Striptease, +1 Agility | |
| **Soft Ass**   | +10% $, +1 Anal, +1 Charm | |
| **Large Hips** | +15% $, +2 Sex | Female. |
| **Deluxe Derriere** | +20% $, +3 Anal, +1 Striptease | |
| **Large Penis** | +30% $, +3 Sex, +2 Anal, +2 Homo | Male. |
| **Tight**      | +20% $, +2 Sex, +2 Anal | |
| **Sensitive**  | +10% $, +1 Sex, +1 Oral, +1 BDSM | Sensibilidad corporal. |

No incluido en la propuesta (aunque sea “físico”):

- **Flat Chest**: tiene -5% $; es más un cambio de tipo que un buff claro.
- **Small Penis**, **Loose**, **Numb**: son “físicos” pero con connotación negativa o de nicho; se pueden añadir después si quieres.

---

## Resumen para que me corrijas

1. **SFW**: de la lista SFW, ¿cuáles quieres que tengan poción? (Strong, Tough, Transformed, Magical ya la tienen; Robust, Energetic, Agile, Great Figure, Long Legs, Exotic, Beautiful, Nice Tan, Tomboy, Radiant, Graceful, Elegant, y opcionales Confident / Cool Scars.)
2. **NSFW**: de la lista NSFW, ¿cuáles quieres? (Large Breasts ya tiene; Small Breasts, Firm Ass, Soft Ass, Large Hips, Deluxe Derriere, Large Penis, Tight, Sensitive.)
3. **Troll Blood**: ya está como poción **sin trait**, solo **+1 max Health** y **+1 Health Regen** por uso, **acumulativo**.

Cuando me digas los que quieres (o los que quitas), añado solo esas pociones en `items.json` y en `apply_alchemy_result` en `script.rpy`.
