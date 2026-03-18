# Auditoría: Sistema de traits en daily stories

## Resumen

Revisión del código, mecánicas y datos del sistema `positive_traits` / `negative_traits` en daily stories.

---

## ✅ Funcionamiento correcto

1. **Parseo de pesos**: `_parse_trait_weights` admite lista y dict, con fallback a peso 3.
2. **Selección ponderada**: `_pick_weighted_trait` usa `random.choices` y `max(1, w)` para evitar pesos 0 inválidos.
3. **Roll**: `trait_modifier = sum(pos) - sum(neg)` se aplica correctamente a `adjusted_skill`.
4. **Mensajes**: Solo se muestran cuando hay traits aplicables; fallback a `trait_success` si falta `trait_msg_*`.
5. **Rest/Prisoner**: No usan traits; el flujo de rest no pasa por la tirada.
6. **Compatibilidad**: Se mantiene `relevant_traits` como fallback.
7. **Excepciones**: Errores en `format()` se capturan y se muestra un mensaje genérico.

---

## ⚠️ Posibles problemas

### 1. Peso numérico como string en JSON

**Ubicación**: `_parse_trait_weights`, línea 123.

**Problema**: Si el JSON tiene `"Beautiful": "6"` (string), `isinstance(w, (int, float))` es False y se usa `default_weight` en lugar de 6.

**Impacto**: Bajo; el JSON actual usa números. Solo falla si alguien escribe `"6"` en lugar de `6`.

**Recomendación**: Convertir con `try: int(float(w)) except: default_weight`.

### 2. Valores negativos en `negative_traits`

**Problema**: Si alguien pone `{"Shy": -3}` en negative_traits, la fórmula `sum(pos) - sum(neg)` hace `- (-3) = +3`, sumando skill en lugar de restar.

**Impacto**: Solo si hay un error de datos; el diseño esperado usa valores positivos.

**Recomendación**: Documentar que los valores deben ser positivos, o usar `abs()` al restar.

### 3. Caso "Success con solo negative traits"

**Problema**: Si el worker tiene solo traits negativos y aun así hace success (por skill alto), `matching_pos` está vacío y no se muestra mensaje. Los negativos “perdieron” pero no se reflejan.

**Impacto**: Bajo; es una decisión de diseño: solo se muestran traits que ayudaron (success) o perjudicaron (failure).

### 4. Caso "Failure con solo positive traits"

**Problema**: Si el worker tiene traits positivos pero falla, no hay `trait_msg` para “a pesar de X, falló”.

**Impacto**: Bajo; el diseño simplificado solo contempla success → positive, failure → negative.

### 5. Coincidencia de nombres de traits

**Problema**: La comparación `t in worker_traits` es exacta. Si el JSON usa `"Sexy Air"` y el worker tiene `"Sexy air"`, no hay match.

**Impacto**: Bajo; depende de la consistencia de los datos.

**Recomendación**: Normalizar a `.strip().lower()` si se detectan inconsistencias.

### 6. Sin tope en `trait_modifier`

**Problema**: Con muchos traits de peso alto, `adjusted_skill` puede pasar de 100 y hacer la tirada demasiado fácil.

**Impacto**: Bajo; es decisión de balance, no un bug.

---

## 🔧 Corrección recomendada

Solo la #1 merece un cambio de código para evitar fallos silenciosos con strings numéricos.
