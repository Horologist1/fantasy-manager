# Entrega editorial — 10 de septiembre de 2026

**Estado: `needs_review`.** No `ready_for_audit`: el inventario cubre
deliberadamente una capa del corpus, no el juego entero. Lo cubierto está
completo y verificado; lo no cubierto está listado abajo con nombre y cifra.

Spec aplicada: `docs/EDITORIAL_SPEC_2026-09-10_AMENDED.md`, que sustituye la §5
de `docs/AUTO_EDITORIAL_SPEC_2026-09-10.md`. El original se conserva intacto.

Baseline: commit `f569a02`, con 57 ficheros ya modificados en el worktree antes
de empezar. Todas las comparaciones son contra la copia con hash en `backups/`,
no contra Git, precisamente por eso.

---

## 1. Cifras

| | |
| --- | ---: |
| Unidades inventariadas | 188 |
| Editadas | 109 |
| Conservadas por decisión explícita | 79 |
| Campos de texto reescritos | 541 |
| Entradas de Journal reescritas | 16 objetivos + 16 títulos |
| Líneas de intro/endgame modernizadas | 35 |
| Señalizadores del Journal unificados | 11 |
| Presentaciones de personaje diferenciadas | 8 (de 4 parejas idénticas) |
| Eventos con plantilla compartida | 3 → 0 |
| Stories divididas por género | 18 → 36 variantes |
| Eventos corregidos por fidelidad numérica | 7 |
| Etiquetas `report` corregidas | 2 |
| Pesos, skills, efectos, fórmulas o imágenes modificados | **0** |

## 2. Lo que se ha arreglado

### 2.1 El registro explícito — la instrucción que faltaba

Es el motivo del encargo y lo que GPT declinó redactar. La reparación se apoya en
un hecho verificado en código: `content_object_is_restricted()` oculta el objeto
**entero** cuando lleva `nsfw`, y `brothel` y `governor_castle` lo llevan. Las
daily stories de esas profesiones **sólo las ve quien activó NSFW**. El modo SFW
no filtra texto: filtra el edificio. Ahí el eufemismo no protegía a nadie.

Registro fijado por el desarrollador: **posición 3, explícito con vocabulario
anatómico**, al servicio de la acción y sin degradación por defecto.

| | antes | ahora |
| --- | ---: | ---: |
| Abstracción evaluativa, núcleo NSFW (por 1.000 palabras) | 9,5 | **0,9** |
| Detalle físico concreto, núcleo NSFW | 16,5 | **22,4** |
| Stories sexuales **sin una sola palabra explícita** | 26 | **0** |
| Stories sexuales que nunca nombran anatomía | 44 | **2** (monster taming, no consumada) |
| Stories sexuales sin mencionar el clímax | 31 | **0** |
| Registro arcaico («ye olde fantasy poem»), daily stories | 2,3 | **0,7** |

Las `VIP / Special` dejan el **acto** sin nombrar por decisión tuya, pero ya no
esconden la **reacción**: orgasmos, cuentas y estado físico sí se describen. Y una
comprobación útil: los arcos VN (Yvara 0,0 / Lanista 0,2 /
`.rpy` 0,4) **ya estaban limpios** de tono arcaico. Esa crítica iba de las daily
stories, que es lo que se ha reescrito.

### 2.2 La división por género — el cambio estructural

La anatomía exige saber qué cuerpos hay en la habitación. 18 stories sexuales no
tenían `worker_gender_requirement` y por eso estaban condenadas a escribir
alrededor del acto: eran justo las que no tenían nada explícito.

El patrón ya existía en los datos (`anal`, `hand` y `homo` llevaban años
divididas male/female al mismo peso). Se ha extendido a las 18 que faltaban:
**36 variantes, cada una con el peso original**, y las genéricas eliminadas.

La distribución no cambia, y está probado: el motor filtra el género de forma
estricta antes de la selección ponderada, así que cada trabajador empareja con
exactamente una variante, al mismo peso que antes.
`tests/test_daily_story_gender_variants.py` fija las cuatro condiciones que lo
sostienen — incluida la crítica, que la original desaparezca en lugar de quedar
elegible junto a sus gemelas, que es el fallo que la spec nombra por su nombre.

Ficha completa: `proposals/gender_split_register3.md`.

### 2.3 Duplicación literal y una clase de bug

**18 de las 29 stories de `expert_attendant` eran byte a byte idénticas** a la de
`prostitute` del mismo nombre. Diferenciadas sobre la diferencia mecánica que los
datos ya declaran (`hard`, modificador −5, `50 + skill` frente a `100 + skill`):
una clientela premium más difícil de impresionar.

Repetición literal en todo el corpus de `descriptions`:

- **Antes:** 95 secuencias distintas de 7 palabras repetidas ≥4 veces.
- **Ahora:** **1**, y aparece en cuatro stories que no toqué.

Durante el pase yo mismo introduje tics tres veces (los `critical_success` de
`hand_client` convergieron; las cuatro variantes de `stripper_lapdance_escalation`
compartían 24 secuencias). El scan los detectó y los lotes 7, 9 y 13 los
deshicieron cambiando lo que ocurre, no los sinónimos.

**GPT encontró que `knights_honor_duel` anunciaba −10 Health con `health: -5` y lo
dio por caso único. Seguía vivo en 7 eventos más**, todos corregidos en el texto
y nunca en el efecto. `tests/test_event_text_effect_fidelity.py` cierra la clase;
comprobado por mutación.

### 2.4 El registro arcaico — retirado del Journal y la intro

El inglés de pastiche medieval era una petición deliberada, pensada para todo el
juego, que las reviews no recibieron bien. La decisión del desarrollador
(2026-09-10) es **retirarlo y priorizar que las cosas se entiendan rápido**.

Medido antes de tocar nada, sólo sobrevivía en **dos** superficies. Las otras 23
ya marcaban 0,0 arcaísmos/1.000 palabras: el resto del juego había migrado por su
cuenta a inglés moderno. Esto no rompe una voz de casa, la termina de unificar.

| Superficie | arcaico/1k antes | ahora | `shall`/1k antes | ahora |
| --- | ---: | ---: | ---: | ---: |
| Journal (objetivos, títulos, progreso, final) | 3,8 | **0,0** | 3,1 | **0,0** |
| Intro y endgame (`main_flow.rpy`) | 3,3 | **0,3** | 6,0 | **0,0** |

El Journal no es texto de ambientación: es la pantalla que dice qué hacer. Cada
objetivo abre ahora con la acción concreta — verbo, objeto, cifra — y sólo
después da el motivo. Se conservan la primera persona, el diario y el hilo de
venganza: eso es personaje y trama, no registro.

Ejemplo (objetivo 5, que además explica los días de varias tareas):

> **Antes:** «The time has come to master the arts of item management and the care
> of those who serve. I must procure an energy potion from the merchant's stall…»
>
> **Ahora:** «Buy an energy potion at the market, give it to one of my workers, and
> use it. / Work costs energy. A worker who runs out leaves the rest of the day's
> tasks undone…»

**El señalizador del Journal.** La línea que aparece al completar un objetivo no
es prosa: le dice al jugador que la cadena de quests sigue y dónde mirarla, así
que funciona por reconocimiento y tiene que ser idéntica siempre. No lo era —
había **tres redacciones distintas** antes de este pase y la primera pasada de
esta sesión añadió una cuarta:

| Antes | Veces |
| --- | ---: |
| «Let me consult my journal to discern the way ahead» | 1 |
| «My journal has been inscribed with the next duty» | 3 |
| «Journal has been updated with the next objective» | 3 |
| «There is a new entry in my journal» (mía) | 4 |

Unificadas en **«The next objective is in my Journal.»**, que nombra el botón que
el jugador pulsa («Journal») y el término que usa la pantalla de ayuda
(«objective»). Aquí la repetición es correcta: un cartel que cambia de redacción
cada vez es un cartel que nadie aprende a reconocer.

Además, en dos ramas del objetivo 9 el señalizador quedaba **enterrado a media
escena**, con otra frase después. Esas parejas se intercambiaron para que la
señal sea lo último que se lee.

También se puntuaron cuatro líneas de diálogo de Aelis que corrían dentro de la
narración sin comillas, una de ellas con verbo dicendi.

### 2.5 Revisión de los eventos

Hasta aquí los eventos sólo se habían **medido** y se les habían corregido las 7
cifras que no cuadraban. Esta sección es la lectura real de su prosa.

**Estructuralmente están sanos.** Sobre 269 eventos y 634 opciones:

| Comprobación | Resultado |
| --- | ---: |
| success y failure que abren igual | 2, ambos falsos positivos (comparten el arranque a propósito y luego divergen) |
| opciones con tirada y sin indicar riesgo/recompensa | 0 reales |
| promesas de dinero que el efecto no respalda | 0 reales |
| eventos con abstracción ≥ 8,0/1k | 9 de 269 |

**El defecto real estaba en el reclutamiento.** Cuatro parejas de personajes con
nombre propio compartían su presentación **palabra por palabra**, y el texto
compartido a menudo describía al otro: Laurel, cuya ficha dice *«never met a room
he couldn't work. Bright, fast-talking»*, se presentaba como *«a somewhat
effeminate young man… studied elegance»*, que es Florian.

Y no es repetición invisible: `worker_loader.rpy` sólo filtra cuando NSFW está
desactivado, así que **en modo NSFW los dos rosters se cargan a la vez** (23
workers en vez de 12) y el jugador conoce a las dos mitades de cada pareja. Eso
es literalmente la queja de yodyna: *«characters repeat, you see same looking ones
multiplied many times»*.

Los 24 tienen ahora presentación propia, escrita desde su descripción de ficha —
que ya era distinta y estaba bien escrita, simplemente no se usaba. **0
descripciones compartidas, 0 mensajes compartidos.**

**Tres eventos de «visitante legendario»** (`archmage_apprentice`,
`high_priest_blessing`, `legendary_courtesan_visit`) corrían la misma escena: los
ojos del visitante se abren, dice *«Yes — this one»*, y el éxito era una
abstracción (*«not teaching but awakening — ancient words spoken into the mind»*).
Los tres encabezaban a la vez el ranking de abstracción y el de tics de
plantilla, dos medidas independientes coincidiendo. Reescritos para que cada uno
enseñe algo concreto: **de 3 eventos con plantilla compartida a 0.**

**Cuatro descripciones que decían no poder describir**: las tres de reclutamiento
genérico (*«something indefinable»*, tres veces) y la de Madame Celestine (*«No
obvious reason for the magnetism… something about her presence commands the
room»*).

## 3. Lo que se ha conservado, y por qué

79 unidades quedan intactas por decisión, no por omisión:

- **Toda la capa `daily_story_extensions/`** (308 stories, 44.642 palabras). Ya
  cumplía el estándar y sirvió de referencia de voz.
- **`monster_taming_seduction`** mantiene su registro y es la única story sexual
  que no nombra anatomía. Su `failure` ya describe a la criatura forzando al
  trabajador: hacer explícito el sexo consentido y hacer gráfica una agresión ya
  escrita son cosas distintas. Sus desenlaces positivos son además deliberadamente
  **no consumados** — la mecánica doma por negación, así que nombrar un acto ahí
  contradiría el diseño.
- **Campos sueltos que funcionaban**: `manager_brothel/critical_success`,
  `service_noble_dinner_restaurant/failure` y `/mediocre`,
  `chamberlain_manage_castle/success` y `/critical_success`.
- **`cook_story1_restaurant`** adopta la redacción del piloto que ya revisaste.

## 4. Verificación

| Prueba | Obligatoria | Resultado |
| --- | --- | --- |
| Contratos de eventos, nombres, presentación, opciones, fidelidad y variantes de género | sí | **83 passed, 69 subtests** |
| Integridad estructural | sí | **pass** — 0 ids preexistentes con metadatos alterados |
| Placeholders: ningún tipo perdido ni inventado | sí | **pass** — 0 y 0 |
| Repetición de 7-gramas | sí | **pass** — 95 → 1 |
| Devkit (esquema, editor, export/reimport real) | sí | **187 passed, 0 failed** |
| Suite completa | no | 369 passed, **1 failed** (ver abajo) |
| Recorrido nativo Ren'Py con guardado repetido | no | **not_run** |

Salidas reproducibles en `tests/`. Hashes SHA-256 en `backups/`.

### El fallo de la suite completa

`test_repeat_storage_save_runtime_isolated` falla. **No lo causan estos cambios**:

1. Falla en su **primera sentencia**, un guard de entorno
   (`RENPY_RUNTIME_REQUIRED != "1"`), antes de leer ningún dato del juego.
2. Ese fichero **ya estaba modificado en el worktree antes de empezar** — consta
   en `baseline_worktree_status.txt`. No lo he tocado.

No lo declaro PASS: queda como verificación pendiente.

### Por qué no se lanzó el recorrido nativo

No se ha modificado runtime: sólo texto y estructura en ficheros de datos, más
dos módulos de test. El riesgo real era de presentación, y se ha acotado: **el
campo reescrito más largo mide 379 caracteres frente a un máximo preexistente de
663 en el mismo corpus.** Además, lanzar Ren'Py aquí tiene coste conocido
(`game/saves` es siempre una segunda ubicación y `persistent` mezcla campo a
campo — el incidente de "Restricted Business"), lo que no parecía justificado
para un cambio de prosa.

## 5. Qué queda fuera

Nombrado, no escondido:

- **Arcos de personaje**: `events_character_arcs_sfw/nsfw.json`, Yvara (8.386
  palabras), Lanista (15.854), arcos de monstruos. Inventariados a nivel de
  fichero, **no leídos ni editados**. Su tono arcaico ya está medido y es bajo.
- **Guiones `.rpy`**: `yvara_complete.rpy` (6.389 líneas), `lanista_complete.rpy`
  (5.228), `academy_library_quest.rpy`. Sin tocar. La muestra de la biblioteca que
  proponía el piloto **no** se ha aplicado: es un cambio de voz narrativa que
  conviene decidir viendo la escena entera.
- **`events_building.json`** (72 eventos) y `events_common.json` (47): sólo los 7
  mensajes con desajuste numérico. Su prosa no se ha revisado.

## 6. Pendiente para ti

`proposals/expert_attendant_duplication.md`. El texto duplicado está resuelto; la
duplicación de **diseño** no: Expert attendant sigue ofreciendo los 18 bookings
básicos con el mismo `weight` que Prostitute pagando la mitad. Confirmaste que la
diferencia de precio es lo relevante y que va a la pasada de balance, así que no
se ha tocado nada.

---

**Estas notas son autoevaluación trazable, no una aprobación.** Las puntuaciones
de `report.json` son mías contra la rúbrica enmendada. `before_after.jsonl` trae
las 660 filas con localizador, texto original, texto propuesto y motivo, para
revisar sin fiarse de este resumen.
