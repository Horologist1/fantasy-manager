# Revisión externa del pase editorial — 10 de septiembre de 2026

Estado: **needs_review**. Hay una mejora apreciable de legibilidad, pero quedan incoherencias concretas y la variedad narrativa no está demostrada por las métricas. No he modificado ni eliminado texto del juego ni el informe original.

## Alcance y comprobaciones

He contrastado el informe, el manifiesto, los cambios respecto a los backups, las filas finales de la entrega, los cambios de diálogo en los tres scripts y la selección de historias en el motor. Esta revisión se centra en la entrega editorial: no equivale a releer todos los arcos y textos no modificados del juego.

- Los 11 SHA-256 del manifiesto final coinciden con disco.
- `report.json` valida contra el esquema.
- Las 708 filas se distribuyen en 483 finales y 225 superadas. Las 483 finales encuentran su texto en la unidad declarada del JSON. Contienen **455 localizaciones distintas**, no 483 cambios distintos: hay 28 filas finales repetidas.
- Comparación independiente del JSON completo de edificios: eliminando las descripciones y aplicando exclusivamente la división prevista, coincide con el original. Las únicas diferencias previstas son los 18 IDs sustituidos por 36 variantes, los requisitos de género, el ajuste de exclusiones de orientación y dos títulos `report`. No aparecen cambios adicionales de pesos, fórmulas, efectos, imágenes ni configuración del edificio.
- Las 36 variantes conservan los tipos de placeholders del original. El verificador entregado solo compara los IDs comunes; esta comprobación adicional cubre los IDs sustituidos.
- Tests ejecutados: **24 passed, 53 subtests passed** en contratos de eventos, presentación, variantes y fidelidad numérica. Devkit: **187 passed, 0 failed**.
- No he repetido la suite completa ni un recorrido visual nativo en esta revisión. Un test estático de presentación no certifica que todas las escenas se vean bien en pantalla.

Evidencia reproducible: `backups/editorial-review-20260910/verify.py`, `independent.txt`, `contracts.txt` y `devkit-tests.txt`.

## Hallazgos

### 1. P2 — Un resultado anuncia que no hay pago, pero sí lo hay

`game/data/buildings/building_types.json:7366`, `monster_taming_combat`, `descriptions/mediocre` acaba en **“No creature, and no fee.”** Su fórmula `earnings.mediocre` es `skill` (línea 7361): con una habilidad positiva genera ingresos. No se ha cambiado la mecánica; el texto nuevo vuelve a contradecirla.

Otros fallos, como `prostitute_vanilla_client_female` (línea 122), describen el cobro de la tarifa acordada mientras la fórmula de fallo puede producir una pérdida. Cobro bruto y resultado neto podrían coexistir, pero aquí no se narra el coste que explicaría la diferencia. Es una inconsistencia de presentación, no prueba de un error de cálculo.

El nuevo test de fidelidad detecta cifras de estadísticas en opciones de eventos. No comprueba afirmaciones cualitativas como “no fee” ni las descripciones de daily stories. Su PASS no cubre este defecto.

### 2. P2 — Se introducen duraciones incompatibles con la resolución diaria

`boss_hunting_story1/success` (línea 7080) dedica dos días al reconocimiento antes del combate. `monster_taming_combat/mediocre` (línea 7366) también dedica dos días al rastreo. Ambas son historias resueltas dentro del trabajo de un día; no hay en esos datos una actividad que ocupe dos días. No confundir esto con una referencia al futuro o una reserva para la semana siguiente, que sí puede funcionar como ambientación.

### 3. P2 — Algunas reescrituras amplían la actividad, además de describirla mejor

`prostitute_hand_client_male/critical_success` (línea 446) añade una actividad oral a una historia cuyo `report` y única habilidad son manuales (`Hand`). El original de ese desenlace describía únicamente la actividad manual. Es una ampliación del contenido, no una corrección lingüística; contradice la regla A.3 de la spec enmendada que prohíbe cambiar la actividad declarada.

Las variantes `courtesan_vip_private_chamber_*` y los éxitos de `ea_prostitute_vip_client_*` también concretan actividades, aunque el informe afirma conservarlas sin nombrar en VIP/Special. Eso es una discrepancia entre la entrega y su descripción. **No propongo eliminar ese texto**: si se conserva, hay que reconocer la excepción y dejar de certificar que se cumplió ese límite en todas las VIP.

### 4. P2 — El Journal introduce una explicación mecánica demasiado absoluta

`game/scripts/tutorial_system.rpy:119` añade **“A strong earner in the wrong job earns nothing.”** Asignar una profesión poco adecuada reduce las probabilidades y el rendimiento, pero no establece automáticamente ingresos cero. Las fórmulas incluyen pagos positivos por éxito y por algunos resultados mediocres. Un tutorial debe distinguir peor rendimiento de ausencia de pago.

### 5. P3 — Quedan errores de inglés y referentes ambiguos

- `building_types.json:959`, `:1613` y `:1799`: **“too much teeth”**. La corrección gramatical mínima es **“too many teeth”**. No requiere cambiar el contenido de las escenas.
- En `prostitute_vanilla_client_gay/success` (línea 701) y `courtesan_seduction_nsfw_gay/success` (línea 11306), la sucesión de pronombres y la posición descrita dejan ambiguo qué participante realiza cada acción. Son precisamente casos donde separar por género no resuelve la claridad entre dos participantes del mismo género.
- En el Journal y las transiciones conviven frases nuevas muy coloquiales con frases conservadas de tono solemne. Por ejemplo, `main_flow.rpy` conserva “From this moment forth” y la imaginería de almas, semillas e imperios alrededor de intervenciones modernizadas. No es un fallo gramatical, pero impide considerar terminada la uniformidad del registro.

Estas correcciones quedan señaladas; no se han aplicado al texto.

### 6. P2 de auditoría — La medición de repetición subestima lo que puede leer el jugador

`tools/editorial_text_metrics.py:17-19` afirma que un jugador que ve una variante Gay nunca puede ver una Lesbian. Eso confunde **jugador** con **trabajador**. Una plantilla puede contener ambos, y un mismo reporte puede incluir sus historias.

El resultado reproducible es **1 secuencia de siete palabras repetida al menos cuatro veces fuera del grupo excluido, más 11 secuencias excluidas por pertenecer a variantes**. No equivale a una única repetición visible en toda la experiencia. El umbral tampoco detecta una frase compartida dos o tres veces ni una escena repetida con sinónimos.

Juicio de lectura: hay menos grandilocuencia vacía y más acciones concretas, pero sigue repitiéndose una estructura: fallo por prisa o mala lectura, resultado mediocre correcto e impersonal, éxito atento y desenlace excepcional con una reserva fija. La cercanía entre Prostitute y Expert Attendant sigue siendo clara en familias como las variantes `hetero_client_lesbian`, aunque ya no sean copias exactas. No hace falta eliminar escenas; hace falta no confundir diferencia literal con variedad narrativa.

### 7. P3 de auditoría — Hay cifras y conclusiones que necesitan acotar su alcance

- Los **379 caracteres** del máximo reescrito son el máximo de las filas finales de `building_types.json`, no de toda la entrega. `brothel_couples_fantasy_night` tiene 688 y `worker_violet_last_secret` 656. Esto no prueba desbordamiento, pero invalida usar 379 como garantía general de presentación.
- “Expert Attendant paga la mitad” tampoco es una regla general: `50 + skill` frente a `100 + skill` son 150 frente a 200 con skill 100; las historias manuales comparadas tienen incluso las mismas fórmulas. Los multiplicadores posteriores no convierten esa afirmación en una proporción fija. El informe mezcla ingresos de la casa con una supuesta tarifa comercial premium que el texto inventa como explicación.
- La cobertura entregada declara más de 132.000 palabras sin revisar, incluidos arcos VN, academia e iglesia. El estado `needs_review` es apropiado; “todo el diálogo resuelto” no lo sería.

## Valoración

El pase mejora claramente las descripciones más genéricas: cocina, servicio y varias introducciones de reclutamiento muestran situaciones reconocibles y personajes mejor diferenciados. Los objetivos del Journal son más fáciles de localizar. La separación por género está bien contenida técnicamente.

La siguiente pasada debería ser pequeña y dirigida: coherencia con pagos y tiempo, fidelidad de la actividad, gramática y claridad de participantes; después, variedad entre historias realmente cercanas. No recomiendo otra reescritura masiva ni cambiar el balance para justificar frases nuevas.

Esta auditoría no acredita ausencia total de bugs. Sí acredita que el manifiesto es correcto y que no he detectado una deriva mecánica adicional en la división del JSON de edificios.
