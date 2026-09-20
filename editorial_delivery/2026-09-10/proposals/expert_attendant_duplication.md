# Propuesta — Duplicación estructural entre Prostitute y Expert attendant

Estado: **resuelta en texto, abierta en diseño.** No requiere acción inmediata.

## El hallazgo

18 de las 29 daily stories de `expert_attendant` eran **byte a byte idénticas**
a la story de `prostitute` con el mismo nombre. Sus ids sólo se distinguían por
el prefijo `ea_`:

```
prostitute_vanilla_client        <-> ea_prostitute_vanilla_client
prostitute_anal_client_male      <-> ea_prostitute_anal_client_male
prostitute_oral_client           <-> ea_prostitute_oral_client
... 15 más, incluidas todas las variantes gay/lesbian
```

Un jugador que tuviera trabajadoras en ambas profesiones leía literalmente el
mismo párrafo bajo dos puestos distintos. Esto es una parte medible de lo que
la review describe como *"exactly the same style permeates the entire thing"*.

## Lo que se ha hecho en este pase

Las 18 se han diferenciado, ancladas en la diferencia mecánica que **los datos ya
declaran** — no en una invención:

| | `prostitute` | `expert_attendant` |
| --- | --- | --- |
| `difficulty` | medium | **hard** |
| `difficulty_modifier` (booking básico) | +5 | **−5** |
| `earnings.success` | `100 + skill` | **`50 + skill`** |
| `skills` | 5 | **9** (añade BDSM, Special, Group, Extreme) |
| `description` | "specialty and extreme requests belong to expert attendants" | "Higher expectations: each booking is harder to ace than standard floor work" |

De ahí sale la voz: en Expert attendant el mismo acto lo compra una clientela que
paga un recargo, es más difícil de impresionar y se queja antes. El `failure`
menciona el recargo; el `mediocre` es "esto lo tenía en la planta baja por la
mitad". Ninguna id, peso, skill, imagen, efecto ni fórmula se ha tocado.

Verificación: `python tools/editorial_text_metrics.py` — 0 campos compartidos
entre las dos profesiones tras el pase.

## Lo que queda como decisión tuya

La duplicación de **texto** está resuelta. La duplicación de **diseño** no, y no
es algo que deba resolver una revisión editorial:

1. **¿Debe Expert attendant ofrecer los bookings básicos?** Hoy tiene copia de
   los 18 actos corrientes *además* de su menú propio (BDSM, Group, VIP, Extreme,
   11 stories exclusivas). Si su valor es la especialidad, una alternativa es
   dejarle sólo el menú especial y que los básicos caigan siempre en Prostitute.
   Eso eliminaría 18 stories del pool y simplificaría el mantenimiento futuro:
   cada acto nuevo hoy hay que escribirlo dos veces.

2. **Si se mantienen, ¿debería el peso reflejar la rareza?** Un Expert attendant
   con un booking vanilla tiene hoy el mismo `weight: 4` que en Prostitute, así
   que la profesión cara tira actos corrientes con la misma frecuencia que la
   barata, pagando `50 + skill` en vez de `100 + skill`. Puede ser deliberado
   (el especialista pierde dinero haciendo trabajo de planta) o un descuido.

**No se ha tocado ninguna de las dos cosas.** Cambiar el pool o los pesos altera
la distribución de eventos y el balance económico, que está fuera del alcance de
un pase de texto y contradiría explícitamente la spec. Queda documentado para que
lo decidas tú.
