# Informe de auditoría — pase editorial Fantasy Manager, 2026-09-10

**Destinatario: un auditor automático.** Está escrito para ser verificado, no
creído. Cada afirmación numérica lleva el comando que la reproduce. Donde no hay
comando, se dice explícitamente que es un juicio y no una medición.

**Autor del pase:** Claude Opus 5. **Estado:** `needs_review`.

---

## 0. Cómo auditar esto rápido

```bash
cd <repo>
python tools/editorial_damage_check.py      # 0 defectos introducidos por la edición
python tools/editorial_structural_check.py  # qué cambió estructuralmente
python tools/editorial_text_metrics.py      # placeholders + repetición
python tools/editorial_layer_metrics.py \
    editorial_delivery/2026-09-10/backups/game__data__buildings__building_types.json \
    game/data/buildings/building_types.json
python -m pytest tests/ -q
"D:/renpy-8.3.4-sdk/renpy.exe" . lint
(cd devkit_web && npm test)
```

Salidas guardadas en `editorial_delivery/2026-09-10/tests/`.

**Advertencia previa (§9):** el repositorio tenía cambios locales ajenos antes de
empezar y recibió más **durante** el pase. No todo lo modificado es mío.

---

## 1. Encargo y de dónde viene

Origen: 20 reviews de F95Zone. La crítica textual central:

> «The AI dialogue is just awful. Wordy, vague, **shy to properly describe NSFW
> aspects** it quickly becomes intolerable to read as exactly the same "ye olde
> fantasy poem" style permeates the entire thing.» — SmaugTheDragon

El desarrollador encargó a otro modelo una especificación editorial
(`docs/AUTO_EDITORIAL_SPEC_2026-09-10.md`). Ese modelo **declinó redactar la
instrucción central** — pedir texto sexual más explícito — y su §5 quedó
diciendo lo contrario de lo encargado:

> «La intensidad del contenido corresponde al encargo de cada escena. No debe
> aumentarse automáticamente durante una revisión de estilo.»

Este pase parte de una spec enmendada, `docs/EDITORIAL_SPEC_2026-09-10_AMENDED.md`,
que **deroga esa §5** y la sustituye. El original se conserva intacto para que el
auditor compare.

**Decisiones del desarrollador durante el pase**, todas registradas:

| Decisión | Efecto |
| --- | --- |
| Registro **posición 3**: explícito con vocabulario anatómico | §A.2 de la spec enmendada |
| `VIP / Special` dejan el acto sin nombrar | §A.3 — **no se cumplió en todas**, ver §12.1 |
| …pero **sí** nombran la reacción (orgasmos) | corrección suya, lote 15 |
| Registro arcaico **retirado**, prioridad a entender rápido | lotes de Journal/intro |
| Duplicación de roster: no actuar, solo documentar | `proposals/` |

---

## 2. Cifras verificables

| Métrica | Valor | Cómo verificarlo |
| --- | ---: | --- |
| Filas de before/after | 708 | `wc -l before_after.jsonl` |
| — que describen el texto **actual** | 483 | filas con `"final": true` |
| — superadas por un lote posterior | 225 | filas con `"final": false` |
| Unidades narrativas distintas tocadas | 143 | `jq -r .unit before_after.jsonl \| sort -u \| wc -l` |
| Unidades en `report.json` (texto actual) | 135 | `jq '.units \| length' report.json` |
| Campos de `descriptions` cambiados | 268 | `tools/editorial_text_metrics.py` |
| Stories de `building_types.json` tocadas | 69 | ídem |
| Stories divididas por género | 18 → 36 | `tests/test_daily_story_gender_variants.py` |
| Eventos corregidos por cifra falsa | 7 | `tests/test_event_text_effect_fidelity.py` |

**Sobre las 225 filas superadas:** varias unidades se editaron más de una vez
(reescritas, luego divididas por género y reescritas de nuevo). Su `after`
intermedio ya no está en el fichero, y eso es correcto. El campo `final`
distingue rastro histórico de estado final; el script lo comprueba abriendo el
fichero declarado en cada fila.

---

## 3. Lo corregido, por clase de defecto

### 3.1 Registro explícito en contenido NSFW-gated

**Hecho estructural que lo habilita** (verificar en código, no fiarse):
`game/scripts/buildings/building_logic.rpy` → `content_object_is_restricted()`.
`brothel` y `governor_castle` llevan `nsfw: true` a nivel de edificio, luego sus
daily stories **sólo las ve quien activó NSFW**. El modo SFW no filtra texto:
filtra el edificio entero. El eufemismo allí no protegía a nadie.

| | antes | ahora |
| --- | ---: | ---: |
| Abstracción evaluativa, núcleo NSFW (/1k) | 9,5 | **0,9** |
| Detalle físico concreto, núcleo NSFW (/1k) | 16,5 | **23,1** |
| Stories sexuales sin vocabulario explícito | 26 | **0** |
| Stories sexuales que nunca nombran anatomía | 44 | **2** |
| Stories sexuales sin mencionar el clímax | 31 | **0** |

Las 2 restantes son `monster_taming_seduction_male/_female`: sus desenlaces
positivos son **deliberadamente no consumados** (la mecánica doma por negación),
y su `failure` ya contenía un beat no consentido preexistente que **no** se hizo
gráfico. Decisión documentada en §A.3 de la spec enmendada.

Comando: `tools/editorial_layer_metrics.py`, `tests/metric_explicitness.txt`.

### 3.2 División por género — único cambio estructural

18 stories sexuales carecían de `worker_gender_requirement`, así que su prosa
estaba obligada a escribir *alrededor* del acto. El patrón ya existía en los
datos (`anal`, `hand`, `homo` llevaban tiempo divididas male/female al mismo
peso); se extendió a las 18 que faltaban.

**Prueba de que la distribución no cambia:** `event_daily_exec.rpy:517` (y `:912`
en la ruta de manager) filtra `worker_gender_requirement` de forma estricta
*antes* de la selección ponderada. Cada trabajador empareja con exactamente una
variante, al peso original. La condición crítica es que la original desaparezca.

`tests/test_daily_story_gender_variants.py` fija cuatro invariantes:
1. ninguna de las 18 originales sigue en el pool;
2. las 36 variantes existen;
3. las gemelas de un split conservan peso, skills, earnings, consequences,
   imágenes y traits;
4. cada perfil (masculino, femenino, Gay, Lesbian) empareja con **exactamente
   una** variante, nunca cero ni dos.

Ficha: `proposals/gender_split_register3.md`.

**Nota para el auditor:** `tools/editorial_structural_check.py` devuelve
`STRUCTURE IDENTICAL: False`. Es **esperado y correcto** — refleja esta división
deliberada. Lo que debe seguir siendo cierto es que **ningún id preexistente
cambió de metadatos**; eso lo comprueba `tools/editorial_damage_check.py`
(paso 5: «156 stories comunes, 0 con deriva»).

### 3.3 Duplicación literal

| Defecto | Antes | Ahora |
| --- | ---: | ---: |
| 7-gramas repetidos ≥4 veces (corpus de stories) | 95 | **0** ¹ |
| Stories de `expert_attendant` idénticas a `prostitute` | 18 | **0** |
| Personajes con presentación compartida | 8 (4 parejas) | **0** |
| Eventos «visitante legendario» con plantilla compartida | 3 | **0** |

¹ La cifra original de este informe (**1**) excluía las variantes de orientación
por un error de método: daba por hecho que un jugador que ve la variante Gay
nunca ve la Lesbian, lo cual confunde **jugador** con **trabajador**. Una plantilla
puede tener ambos y un mismo reporte diario imprime las dos historias. Contando
todo, la cifra real era **12**, no 1. Corregido en `tools/editorial_text_metrics.py`
y en el propio texto: ver §12.2. El umbral ≥4 tampoco veía las frases compartidas
por 2 o 3 historias, que son la forma habitual del defecto; ahora se reporta la
distribución completa.

`expert_attendant` se diferenció sobre la diferencia mecánica que los datos ya
declaran: `difficulty: hard`, `difficulty_modifier: -5`, `50 + skill` frente a
`100 + skill`. No se inventó nada.

En reclutamiento, el texto compartido a menudo describía **al otro**: Laurel,
cuya ficha dice *«never met a room he couldn't work. Bright, fast-talking»*, se
presentaba como *«a somewhat effeminate young man… studied elegance»*, que es
Florian. Las 24 presentaciones se reescribieron desde la ficha de cada uno.

### 3.4 Fidelidad texto ↔ efecto

La spec original citaba `knights_honor_duel` (−10 Health anunciado, `health: -5`
aplicado) como caso único ya corregido. **Era una clase, no un incidente:** el
mismo desajuste seguía vivo en 7 eventos.

Se corrigió el **texto**, nunca el efecto. `tests/test_event_text_effect_fidelity.py`
cierra la clase y está probado por mutación (reintroducir el −10 hace fallar el
test con el mensaje correcto).

### 3.5 Registro arcaico

Medido **antes** de tocar nada: sólo sobrevivía en **2** de 25 superficies. Las
otras 23 marcaban 0,0 arcaísmos/1.000 palabras.

| Superficie | antes | ahora | `shall`/1k antes | ahora |
| --- | ---: | ---: | ---: | ---: |
| Journal (objetivos, títulos, progreso, final) | 3,8 | **0,0** | 3,1 | **0,0** |
| Intro y endgame (`main_flow.rpy`) | 3,3 | **0,3** | 6,0 | **0,0** |

El Journal **no es ambientación**: es la pantalla que dice qué hacer. Cada
objetivo abre ahora con la acción concreta y sólo después da el motivo. Se
conservan primera persona, diario y trama de venganza.

### 3.6 Señalización funcional

La línea que aparece al completar un objetivo tenía **tres redacciones distintas
de origen**, y la primera pasada de este mismo trabajo añadió una cuarta.
Unificadas en **17 apariciones idénticas** de «The next objective is in my
Journal.», que nombra el botón que el jugador pulsa y el término del help screen.

Aquí la repetición **es correcta**: un cartel que cambia de redacción no se
reconoce. Además, en dos ramas quedaba enterrado a media escena con otra frase
después; esas parejas se intercambiaron.

Verificar: `grep -rc "The next objective is in my Journal" game/scripts/` → 11 + 6.

### 3.7 Otros

- **Ruptura de voz:** una frase en segunda persona pegada en 5 descripciones de
  disciplina escritas en primera («**You** put the servant's collar on them»).
- **Elección hueca:** `discipline_level5_finale_harem_member` y `_house_servant`
  eran byte a byte idénticas en descripción, efecto e imagen, pese a aplicar
  traits distintos vía `screens.rpy::_apply_discipline_final_and_close`.
- **Diálogo sin comillas:** 4 líneas de Aelis corrían dentro de la narración sin
  marcar, una con verbo dicendi.
- **Referencia a escena inexistente (BIBLIA §16):** `yvara_s2_talk_2` citaba al
  jugador diciendo *«you go quiet»* bajo presión; esa frase **no existe** en las
  6.389 líneas del arco. Corregida a impresión propia de ella.

---

## 4. Lo que se conservó, y por qué

No todo lo medido como «abstracto» estaba mal. Conservado deliberadamente:

- **Capa de relaciones** (`daily_story_extensions/`, 308 stories, 44.642
  palabras): ya cumplía el estándar; sirvió de referencia de voz.
- **Arcos VN Yvara y Lanista** (89.347 palabras): Lanista tiene **0** 7-gramas
  repetidos en 26.828 palabras, mejor que cualquier otra superficie. Ambos 0
  arcaísmos.
- **`events_building.json`** (72 eventos): 0 repeticiones entre eventos, 0
  campos vacíos, prosa leída y buena. **No se tocó salvo 2 campos.**
- **Campos sueltos que funcionaban:** `manager_brothel/critical_success`,
  `chamberlain_manage_castle/success` y `/critical_success`,
  `service_noble_dinner_restaurant/failure` y `/mediocre`.
- **`cook_story1_restaurant`** adopta la redacción del piloto que el
  desarrollador ya había revisado, en vez de una versión nueva.

---

## 5. Errores que cometí durante el pase

Un auditor debe saber dónde falló el ejecutor. Todos fueron detectados y
corregidos, tres de ellos **por el desarrollador, no por mí**.

| # | Error | Cómo se detectó | Estado |
| --- | --- | --- | --- |
| 1 | Escribí LF en ficheros CRLF; el diff pasó de 7 a miles de líneas | diff contra mi propio backup | corregido |
| 2 | Afirmé mojibake en el corpus; era el terminal, no el fichero | comprobación en el JSON parseado | retirado |
| 3 | Introduje mis propios tics 3 veces (4 `critical_success` convergidos; 24 secuencias en las 4 variantes de stripper) | mi scan de 7-gramas | corregido (lotes 7, 9, 13) |
| 4 | Apliqué de menos «no nombrar el acto ≠ ocultar la reacción» en VIP | **corregido por el desarrollador** | lote 15 |
| 5 | Volví a aplicarlo de menos en los maestros místicos | **corregido por el desarrollador** | lote 24 |
| 6 | Reporté escenas VN «sin retrato»; mi escáner reseteaba estado en cada `label`, pero el sprite sobrevive al `jump` | **corregido por el desarrollador** | retirado |
| 7 | Al arreglarlo, confundí un fondo (`_academy_bg`) con un retrato | revisión propia | retirado |
| 8 | Afirmé «Yvara 0 cambios de emoción vs Lanista 131»; el real es **113**, con 12 nombres de variable distintos | **corregido por el desarrollador** | retirado, §3 de `vn_arcs_gaps.md` |
| 9 | Mi lista de arcaísmos no incluía *perchance/hath*: dio **0,0 al Journal**, el peor sitio del juego | lectura directa del fichero | corregido |
| 10 | Apliqué el índice de concreción a tooltips de traits/items, donde no significa nada | lectura directa | descartado |
| 11 | Unifiqué 11 señalizadores del Journal y dejé **6 sin tocar** en otro fichero | `tools/editorial_damage_check.py` | corregido |
| 12 | Mi verificador de daño reportó 23 falsos positivos, luego quedó roto (sin `\b`) reportando limpio, luego no detectaba `{actual_money}` roto | prueba por mutación | corregido y probado |

**Conclusión metodológica:** las métricas de este pase fallaron cinco veces
(#2, #6, #7, #8, #9, #10). Cuando la medición y la lectura discreparon, la
lectura tuvo razón. El auditor debería **releer** cualquier conclusión que
dependa sólo de un número.

---

## 6. Verificación

| Prueba | Obligatoria | Resultado |
| --- | --- | --- |
| Contratos de eventos, nombres, presentación, opciones, fidelidad, variantes | sí | **83 passed, 69 subtests** |
| `tools/editorial_damage_check.py` | sí | **0 defectos introducidos** |
| Placeholders: tipos perdidos / inventados | sí | **0 / 0** |
| Repetición 7-gramas (≥4, contando variantes) | sí | 95 → **12** → **0/2** tras §12 |
| Deriva estructural en ids preexistentes | sí | **0** |
| `renpy lint` | sí | **0 errores, 0 warnings** |
| Devkit (esquema, editor, export/reimport real) | sí | **187 passed, 0 failed** |
| Suite Python completa | no | 369 passed, **1 failed** (§7) |
| Recorrido nativo Ren'Py con guardado repetido | no | **not_run** (§7) |

El devkit empaqueta una copia de los JSON y se reconstruyó al final
(`npm run bake && npm run build:offline`); estaba desfasado dos veces durante el
pase.

---

## 7. Limitaciones declaradas

1. **`test_repeat_storage_save_runtime` falla.** Falla en su **primera
   sentencia**, un guard de entorno (`RENPY_RUNTIME_REQUIRED != "1"`), antes de
   leer dato alguno, y ese fichero **ya estaba modificado en el worktree antes de
   empezar** (`baseline_worktree_status.txt`). No es causado por este pase y **no
   se declara PASS**.

2. **No se lanzó el recorrido nativo.** No se modificó runtime: sólo texto y
   estructura en ficheros de datos, más dos módulos de test. El riesgo real era
   de presentación y se acotó estáticamente: el campo reescrito más largo mide
   **688 caracteres** (`brothel_couples_fantasy_night`) frente a un máximo
   preexistente de **1.129** en el corpus. Los **379** que decía la versión
   anterior de este informe eran sólo el máximo de `building_types.json`, no de
   toda la entrega, y usarlos como garantía general era incorrecto (§12.3). Además, lanzar Ren'Py tiene coste conocido (`game/saves` es siempre
   una segunda ubicación y `persistent` mezcla campo a campo).

3. **La dirección escénica no es auditable estáticamente.** El estado de sprites
   depende del flujo de control, no del orden del fichero. Tres intentos, tres
   resultados equivocados (§5, #6-#8). Requiere ver la pantalla.

4. **Las puntuaciones de `report.json` son autoevaluación**, no una auditoría
   externa.

5. **Superficies no leídas:** ver `tests/coverage_map.txt`. Las mayores son la
   capa de relaciones (44.642 palabras, medida y conservada) y los arcos VN
   (89.347, auditados a nivel de texto pero no leídos línea a línea).

---

## 8. Pendiente para el desarrollador

| Ficha | Asunto |
| --- | --- |
| `proposals/expert_attendant_duplication.md` | Expert attendant ofrece los 18 bookings básicos al mismo `weight` que Prostitute con fórmulas de pago más bajas. «La mitad» era una simplificación incorrecta: `50 + skill` frente a `100 + skill` son 150 vs 200 con skill 100, y las historias manuales comparadas tienen incluso la misma fórmula (§12.3). Confirmado que va a la pasada de balance. |
| `proposals/roster_duplicate_characters.md` | En modo NSFW se cargan los dos rosters (23 workers): 3 parejas idénticas en traits y skills. Texto resuelto; mecánica abierta por decisión suya. |
| `proposals/gender_split_register3.md` | Ficha del único cambio estructural. |
| `proposals/vn_arcs_gaps.md` | **Yvara (16 eventos) y Lanista (30) no usan `arc_id`**, luego quedan fuera de `ArcBackreferenceContracts`, el gate que protege a los otros 69. El defecto §3.7 apareció exactamente ahí. |

---

## 9. Advertencia sobre el estado del repositorio

**El repositorio tiene trabajo concurrente que no es de este pase.**

- Al empezar había **58 rutas ya modificadas** en el worktree
  (`baseline_worktree_status.txt`). Por eso todas las comparaciones se hacen
  contra copias con SHA-256 en `backups/`, **no contra Git**.
- **Durante** el pase aparecieron ficheros que este pase no creó:
  `game/data/monthly_conditions/`, `game/python-packages/fm_monthly/`,
  `game/scripts/core/monthly_conditions.rpy`, `tests/test_monthly_conditions.py`,
  `tests/test_monthly_runtime.py` (mtime 19:18–19:20; el último fichero de este
  pase es de 19:16).

**Consecuencia para el auditor:** el recuento «369 tests» incluye tests que este
pase no escribió. Los ficheros efectivamente tocados aquí son:

```
game/data/buildings/building_types.json
game/data/events/events_common.json                  (ya modificado antes)
game/data/events/events_building.json
game/data/events/events_character_arcs_nsfw.json     (ya modificado antes)
game/data/events/recruit/event_recruit_aelis.json
game/data/events/recruit/event_recruit_unique_workers.json
game/data/interactions/interactions_structured.json
game/scripts/main_flow.rpy
game/scripts/tutorial_system.rpy
game/scripts/yvara/yvara_complete.rpy
tests/fixtures/event_arc_reviews.json                (re-sellado, §10)
tests/test_event_text_effect_fidelity.py             (nuevo)
tests/test_daily_story_gender_variants.py            (nuevo)
tools/editorial_layer_metrics.py                     (nuevo)
tools/editorial_text_metrics.py                      (nuevo)
tools/editorial_structural_check.py                  (nuevo)
tools/editorial_damage_check.py                      (nuevo)
tools/audit_management_balance.py                    (una referencia actualizada)
docs/EDITORIAL_SPEC_2026-09-10_AMENDED.md            (nuevo)
devkit_web/ (regenerado)
```

---

## 10. Sobre el gate de arcos

`worker_violet_last_secret` está bajo `ArcBackreferenceContracts`. Editar su
prosa **invalidó su fingerprint a propósito** — el gate existe para forzar una
relectura de todas las ramas cuando el texto se mueve.

En vez de esquivarlo: se releyeron ambas ramas, se actualizó
`tests/fixtures/event_arc_reviews.json` con el nuevo sha y una nota que registra
qué cambió y qué **no** (participantes, consentimiento y recompensa intactos; la
rama de fallo sin tocar y todavía alcanzable).

El fingerprint se recalcula **importando la función del propio test**, no
replicándola: la primera réplica de `effect_text` era incorrecta y el gate lo
detectó.

---

## 11. Qué debería comprobar el auditor con más escepticismo

Por orden de riesgo:

1. **Que las 36 variantes de género no alteren la distribución.** Es el único
   cambio estructural. El test lo fija, pero el test lo escribí yo: conviene
   releer su lógica contra `event_daily_exec.rpy:517`.
2. **Que el registro explícito no haya cruzado los límites de §A.3** — actos o
   participantes no declarados, coerción nueva, anatomía inferida del género.
   Eso **no lo mide ninguna herramienta**; requiere leer `before_after.jsonl`.
3. **Las 483 filas con `final: true`** son el estado actual. Leerlas es la
   auditoría editorial real; todo lo demás es andamiaje.
4. **Que la repetición no haya vuelto por otra vía.** Mis propios tics
   aparecieron tres veces y sólo los cazó un scan sistemático.
5. **Las 2 stories sin anatomía** son decisión explícita del desarrollador, no
   omisión. La afirmación paralela sobre las VIP era falsa: varias sí nombran el
   acto. Ver §12.1 y verificar contra §A.3.

---

## 12. Respuesta a la revisión externa (Codex, 2026-09-10)

`EXTERNAL_REVIEW_CODEX.md` verificó el manifiesto, comparó el JSON de edificios
de forma independiente y encontró **siete hallazgos**. Seis eran correctos.
Esta sección dice qué se cambió, qué se corrigió en este informe y qué se
rechazó, con la evidencia de cada cosa.

### 12.1 Hallazgos aceptados y corregidos en el texto

| # | Hallazgo | Alcance real medido | Acción |
| --- | --- | --- | --- |
| 1 | «No creature, and no fee» contra una fórmula que paga | Barrido de las 192 stories: **1** caso real. Los otros que mi propio scan marcó («not a copper **over**», «nothing **more**») hablan de la propina, no del pago: falsos positivos | `monster_taming_combat/mediocre` reescrito: la cofradía paga la tarifa de reconocimiento |
| 2 | Duraciones de varios días en una resolución diaria | **4** casos. Uno (`entertainer_story1_tavern`, «still talking about it two days later») es secuela posterior, no jornada consumida: se conserva. De los otros tres, dos los introdujo este pase y uno (`ambassador_diplomatic_alliance`) era preexistente | 3 reescritos a una jornada |
| 4 | El Journal afirmaba «A strong earner in the wrong job earns nothing» | Falso: `mediocre` y `success` pagan positivo | Reescrito: «still bring something in — just a fraction of what they would make where their skills fit» |
| 5a | «too much teeth» | **3** ocurrencias | «too many teeth», y el marcador añadido a `editorial_damage_check.py` |
| 5b | Participante ambiguo entre dos hombres | 3 historias compartían la misma coreografía **y** la misma construcción ambigua («flat on his back with X's ankles hooked behind him») | Las 3 reescritas con posiciones distintas y agente explícito |
| 5c | Registro solemne conviviendo con el modernizado | Muy por encima de lo que citó la revisión: los milestones **11-15**, el mensaje de finalización y **ambos finales** estaban intactos en el registro antiguo. Es decir, la última hora de juego | ~60 líneas reescritas en `main_flow.rpy` y `tutorial_system.rpy` |

### 12.2 Hallazgo 6: la métrica estaba mal, y lo que tapaba

La objeción es correcta y era un error de método, no de cálculo:
`tools/editorial_text_metrics.py` excluía las variantes de orientación diciendo
que un jugador que ve la Gay nunca ve la Lesbian. Eso confunde **jugador** con
**trabajador**. La herramienta ya no excluye nada y reporta la distribución
completa.

Al recontar, el peor foco de repetición estaba donde el pase **no había mirado**:

| Familia | 7-gramas compartidos antes |
| --- | ---: |
| `bartender_last_call_nsfw_tavern` + `_lesbian` | 177 |
| `server_champagne_room_nsfw_casino` + `_lesbian` | 167 |
| `dealer_winners_reward_nsfw_casino` + `_gay` + `_lesbian` | 124 |
| `entertainer_private_performance_nsfw_tavern` + `_gay` + `_lesbian` | 118 |
| `service_generous_tipper_nsfw_restaurant` + `_lesbian` | 73 |
| `monster_taming_seduction_male` / `_female` | 82 |

Eran la misma escena con los sustantivos cambiados, y además seguían en el
registro retirado («increasingly intense sex», «drive the whole room wild»,
«dripping with sweat and satisfaction»). **14 historias, 50 campos** reescritos
como escenas distintas, no como sustituciones.

Se conservan a propósito: la severidad de cada desenlace, el escenario, la
skill, el `report` visible, la dirección del pago, y el compás de no-consenso
preexistente en `monster_taming_seduction/failure` — escrito más llano, ni
suavizado ni hecho más gráfico (§A.3).

| 7-gramas en ≥N historias distintas | Antes del pase | Informe original (mal contado) | Ahora |
| --- | ---: | ---: | ---: |
| 2 historias | 2.537 | — | **837** |
| 3 historias | 474 | — | **56** |
| ≥4 historias | 94 | «1» | **2** |

Los 2 restantes son variantes de una misma historia base. Cruces entre historias
no emparentadas con ≥4 apariciones: **0**.

**Expert Attendant frente a Prostitute.** Separando los dos tipos de solape que
la métrica mezclaba:

| Tipo de solape | 7-gramas | Juicio |
| --- | ---: | --- |
| Entre variantes `_male`/`_female`/`_gay`/`_lesbian` de **una misma historia** | 534 | **Por diseño.** Es el split de género que pidió el desarrollador: el mismo trabajo, la anatomía correcta. Hacerlas escenas distintas rompería justo lo que se buscaba |
| Entre **historias distintas** | 513 → **323** | Defecto. Y todos los mayores son pares `ea_prostitute_X` / `prostitute_X`, exactamente la cercanía que señaló la revisión |

De esos pares se midió la similitud campo a campo y se reescribieron los **11
campos** que estaban entre el **60% y el 99%** idénticos — uno de ellos,
`hetero_client_lesbian/critical_success`, al **99%**. Se tocó sólo el lado
Expert Attendant, que es el que tiene una premisa propia desde la que escribir:
un encargo con instrucciones, un recargo, y un cliente que paga precisamente
para que decida otro.

| | Antes | Después |
| --- | ---: | ---: |
| Similitud de los 11 campos | 0,60 – **0,99** | 0,00 – **0,18** |

Los desenlaces que quedaban por debajo del 60% **no se han tocado**: comparten
aperturas y modismos, y reescribirlos sería la reescritura masiva que la
revisión desaconseja. El defecto **mecánico** de Expert Attendant (mismos
`weight`, fórmulas distintas) sigue aparcado para la pasada de balance, como
decidió el desarrollador.

El segundo scan de este lote encontró que **yo había vuelto a introducir mis
propios tics**: diez colisiones nuevas entre los textos recién escritos
(cierres reutilizados entre una variante y su hermana, y «spends the rest of
the…», que ya colisionaba con cuatro historias ajenas). Corregidas. Es la cuarta
vez en el pase que ocurre lo mismo, y las cuatro las cazó el scan, no la
lectura.

### 12.3 Hallazgos aceptados como corrección **de este informe**, sin tocar el juego

- **Hallazgo 3 — actos ampliados en VIP/Special.** El desarrollador ha decidido
  que el desajuste entre actividad narrada y skill evaluada **es aceptable a
  veces**, así que el texto se conserva. Lo que era falso es la afirmación de
  este informe de que las VIP dejan el acto sin nombrar: **no se cumplió en
  todas**. Corregido en §1 y §11. `prostitute_hand_client_male/critical_success`
  se conserva: entrega la actividad manual que su `report` anuncia, y el añadido
  es adicional, no sustitutivo.
- **Hallazgo 7 — cifras con el alcance mal declarado.** Los **379 caracteres**
  eran el máximo de `building_types.json`; el de toda la entrega es **688**
  (`brothel_couples_fantasy_night`), contra un máximo preexistente de **1.129**
  en el corpus. Sigue sin ser prueba de desbordamiento, pero 379 no servía como
  garantía general. «Expert Attendant paga la mitad» tampoco era una regla:
  `50 + skill` frente a `100 + skill` son 150 vs 200 con skill 100, y las
  historias manuales comparadas comparten fórmula.

### 12.4 Rechazado, con motivo

- **Hallazgo 1, segunda parte** («el fallo cobra la tarifa mientras la fórmula
  puede dar pérdida»). Afecta a **72 desenlaces** y es una **convención
  preexistente**, no algo que introdujera el pase: en el baseline ya eran 34 de
  174 historias. La tarifa bruta y el resultado neto de la casa pueden coexistir
  — habitación perdida, compensación, reputación — y la propia revisión lo
  califica de inconsistencia de presentación, no de error de cálculo. Reescribir
  72 textos por esto sería la reescritura masiva que la revisión desaconseja. Lo
  que sí se corrigió es el caso duro, donde el texto **niega** que haya pago.
  Queda anotado como decisión, no como descuido.

### 12.5 Verificación de este lote

| Comprobación | Resultado |
| --- | --- |
| `tools/editorial_damage_check.py` | **0 defectos**; marcadores de registro grandilocuente añadidos y **probados por mutación** en los 3 ficheros |
| Contratos de eventos, presentación, variantes, fidelidad, monthly | **84 passed, 69 subtests** |
| `renpy lint` | **0 errores, 0 warnings** |
| Placeholders perdidos / inventados | **0 / 0** |
| Barrido de los hallazgos 1, 2, 3 y 5 sobre las 192 historias | ver arriba |

Lo que este lote **no** hace: releer los arcos VN, la academia ni la iglesia.
El estado sigue siendo `needs_review` por la misma razón que antes.
