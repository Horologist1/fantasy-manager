# Comparación máximos (y mínimos) – Antes vs Después del rebalanceo

## Traits en ambos sistemas

**En ANTES y en AHORA los traits se aplican igual** en el código (`event_daily_exec.rpy`):

- Solo en **Success** y **Critical Success** (nunca en Mediocre ni Failure).
- Con **50% de probabilidad** (trait_roll < 0.5).
- Si el worker tiene un trait que está en `relevant_traits` de la historia, se evalúa la fórmula `trait_bonus` del JSON (ej. `level * 100`) y se suma **× 0.3** a los earnings.
- Ese bonus se suma **después** de la fórmula de earnings (y en el sistema antiguo, después de los multiplicadores 0.65/0.75).

Por tanto, las columnas "**+ Trait**" en las tablas de abajo son las mismas en ambos sistemas: el valor del trait no ha cambiado; lo que cambia es la base (fórmula de earnings) a la que se suma. La comparación es correcta: en ambos casos se tienen en cuenta los traits.

---

Supuestos para la comparación:
- **Skill efectiva**: 0 (mínimo) y 100 (máximo razonable).
- **Level**: 10 (para el bonus de trait).
- **Trait**: Como arriba. Para "máximo" se asume que el trait aplica (ej. `level * 100` → +300, `level * 150` → +450, `level * 200` → +600).
- **Failure**: Antes el código multiplicaba la penalidad por 2. Ahora la fórmula incluye `roll` (1–100).

---

## 1. Tier NORMAL (ej. prostitute vanilla, stripper regular, service, manager, cook mesa)

### Antes (fórmulas típicas)
| Resultado       | Fórmula JSON (ej.) | Con skill 100 (base) | Multiplicador código | Resultado final (base) | + Trait (level×100, ×0.3) |
|-----------------|--------------------|----------------------|-----------------------|-------------------------|----------------------------|
| Success         | 120 + skill×5      | 620                  | ×0.75                 | **465**                 | ~765                       |
| Critical Success| 120 + skill×10     | 1120                 | ×0.65                 | **728**                 | ~1028                      |
| Mediocre        | 60 + skill×2       | 260                  | ×0.75                 | **195**                 | —                          |
| Failure         | -10 fijo           | -10                  | ×2                    | **-20**                 | —                          |

### Ahora
| Resultado       | Fórmula            | Con skill 100 (base) | Sin mult. | + Trait (ej. 300) |
|-----------------|--------------------|-----------------------|-----------|---------------------|
| Success         | 200 + skill×2      | 400                   | **400**   | ~700                |
| Critical Success| 200 + skill×4      | 600                   | **600**   | ~900                |
| Mediocre        | 100 + skill        | 200                   | **200**   | —                   |
| Failure         | -(100 + roll)      | roll 99               | **-199**  | —                   |

**Resumen tier normal**
- **Éxito**: Antes máx. ~1028 (crítico + trait); ahora ~900 (crítico + trait). Algo más bajo el pico, pero sin recorte del 0.65/0.75.
- **Mediocre**: Antes 195, ahora 200 (similar o algo mejor).
- **Fallo**: Antes -20 fijo; ahora entre -101 y -199 (depende del roll). Peor en fallos muy malos (roll alto), mejor en fallos por poco (roll bajo).

---

## 2. Tier VIP (ej. prostitute VIP/BDSM, stripper VIP, cook VIP, pleasure servant, guards capture)

### Antes (fórmulas típicas)
| Resultado       | Fórmula JSON (ej.) | Con skill 100 (base) | Multiplicador código | Resultado final (base) | + Trait (level×150, ×0.3) |
|-----------------|--------------------|----------------------|-----------------------|-------------------------|----------------------------|
| Success         | 300 + skill×8      | 1100                 | ×0.75                 | **825**                 | ~1275                      |
| Critical Success| 300 + skill×15     | 1800                 | ×0.65                 | **1170**                | ~1620                      |
| Mediocre        | 150 + skill×4      | 550                  | ×0.75                 | **412**                 | —                          |
| Failure         | -30 fijo           | -30                  | ×2                    | **-60**                 | —                          |

### Ahora
| Resultado       | Fórmula            | Con skill 100 (base) | Sin mult. | + Trait (ej. 450) |
|-----------------|--------------------|-----------------------|-----------|---------------------|
| Success         | 300 + skill×3      | 600                   | **600**   | ~1050               |
| Critical Success| 300 + skill×6      | 900                   | **900**   | ~1350               |
| Mediocre        | 150 + skill        | 250                   | **250**   | —                   |
| Failure         | -(150 + roll)     | roll 99               | **-249**  | —                   |

**Resumen tier VIP**
- **Éxito**: Antes máx. ~1620 (crítico + trait); ahora ~1350. Máximos más bajos que antes.
- **Mediocre**: Antes 412, ahora 250 (ahora más bajo).
- **Fallo**: Antes -60 fijo; ahora -151 a -249. Penalización mayor en fallos muy malos.

---

## 3. Tier PREMIUM (ej. prostitute extreme, adventurer story3)

### Antes (fórmulas típicas)
| Resultado       | Fórmula JSON (ej.) | Con skill 100 (base) | Multiplicador código | Resultado final (base) | + Trait (level×200, ×0.3) |
|-----------------|--------------------|----------------------|-----------------------|-------------------------|----------------------------|
| Success         | 500 + skill×15     | 2000                 | ×0.75                 | **1500**                | ~2100                      |
| Critical Success| 500 + skill×25     | 3000                 | ×0.65                 | **1950**                | ~2550                      |
| Mediocre        | 250 + skill×8      | 1050                 | ×0.75                 | **787**                 | —                          |
| Failure         | -50 fijo           | -50                  | ×2                    | **-100**                | —                          |

### Ahora
| Resultado       | Fórmula            | Con skill 100 (base) | Sin mult. | + Trait (ej. 600) |
|-----------------|--------------------|-----------------------|-----------|---------------------|
| Success         | 400 + skill×4      | 800                   | **800**   | ~1400               |
| Critical Success| 400 + skill×8      | 1200                  | **1200**  | ~1800               |
| Mediocre        | 200 + skill×2      | 400                   | **400**   | —                   |
| Failure         | -(200 + roll)     | roll 99               | **-299**  | —                   |

**Resumen tier premium**
- **Éxito**: Antes máx. ~2550 (crítico + trait); ahora ~1800. Máximos claramente más bajos.
- **Mediocre**: Antes 787, ahora 400 (más bajo).
- **Fallo**: Antes -100 fijo; ahora -201 a -299. Penalización mayor en fallos muy malos.

---

## 4. Tabla resumen rápida (base sin trait, skill 100)

| Tier    | Resultado       | Antes (base) | Ahora (base) | Diferencia   |
|---------|-----------------|--------------|--------------|--------------|
| Normal  | Critical Success| 728          | 600          | -128 (~-18%) |
| Normal  | Success         | 465          | 400          | -65 (~-14%)  |
| Normal  | Mediocre        | 195          | 200          | +5           |
| Normal  | Failure         | -20          | -101 a -199  | Más variable |
| VIP     | Critical Success| 1170         | 900          | -270 (~-23%) |
| VIP     | Success         | 825          | 600          | -225 (~-27%) |
| VIP     | Mediocre        | 412          | 250          | -162         |
| VIP     | Failure         | -60          | -151 a -249  | Peor en malos|
| Premium | Critical Success| 1950         | 1200         | -750 (~-38%) |
| Premium | Success         | 1500         | 800          | -700 (~-47%) |
| Premium | Mediocre        | 787          | 400          | -387         |
| Premium | Failure         | -100         | -201 a -299  | Peor en malos|

---

## 5. Conclusión

- **Traits**: En ambos casos (antes y después) el bonus de trait se aplica igual; las diferencias de máximos vienen solo de la base (fórmula de earnings), no del trait.
- **Máximos**: En todos los tiers los máximos son **menores ahora** (sobre todo en VIP y Premium), porque se quitaron fórmulas muy altas y los multiplicadores 0.65/0.75 ya no recortan un número enorme, sino uno más controlado.
- **Normal**: La diferencia es moderada; el crítico pasa de ~728 a 600 (base). Mediocre mejora un poco (200 vs 195).
- **VIP y Premium**: La reducción es fuerte en éxito/crítico y mediocre, alineada con el objetivo de que un worker gane ~2×/3×/4–5× su coste diario en lugar de picos muy altos.
- **Failure**: Antes penalizaciones fijas y pequeñas (-20 a -100); ahora dependen del roll y pueden ser mayores (-101 a -299), haciendo que el fallo pese más, sobre todo cuando el roll es alto.

Si quieres, el siguiente paso puede ser subir un poco las bases o los coeficientes de skill en algún tier concreto para acercar los máximos actuales a los anteriores (sin volver a los números descontrolados).
