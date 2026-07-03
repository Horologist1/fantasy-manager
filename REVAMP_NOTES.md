# Fantasy Manager — Revamp (2026-07-02)

Copia mejorada del proyecto, construida **al lado** del original (`fantasy-manager/` queda intacto).
Compatible con los mismos JSON de `game/data/` y los mismos assets de `game/images/`.

## Cómo ejecutar / verificar

- Ejecutar: `D:\renpy-8.3.4-sdk\renpy.exe "…\fantasy-manager-revamp"`
- Lint: `D:\renpy-8.3.4-sdk\renpy.exe "…\fantasy-manager-revamp" lint` → **limpio** (el original tenía 3 avisos; también resueltos aquí).
- Smoke test de arranque: 30 s en ejecución, partida nueva hasta la escena inicial, sin traceback.
- Repo git propio (sin historial del original). `game/images/` y los `.rpyc/.rpyb` generados no se versionan.

## Qué se excluyó de la copia

`.git` (608 MB), `game/cache/`, `game/saves/`, `*.rpyc/*.rpyb/*.rpymc/*.bak`, y los ficheros de ComfyUI
del raíz. `docs/` y `user_docs/` sí están. El devkit vive solo en el original.

## Crashes y bugs corregidos (motor)

- `after_date:` en condiciones: NameError silencioso hacía la condición falsa durante todo su año objetivo.
- `building_skill`: KeyError con choices sin `message_success/failure`; logging inseguro; eliminado el
  hack que sustituía cualquier failure con "Unknown" por un mensaje de incendio ajeno al evento.
- `process_choice` devolvía un string (no dict) con `worker_selection` desconocido → AttributeError en el caller.
- Choice con condición nula en evento `random`: fallaba SIEMPRE (0%); ahora enruta al camino sin check.
- `consume_item` no funcionaba nunca (unpack de 2 sobre tuplas de 3) y `grant_loot`+consume crasheaba.
- NameError si todos los eventos pesan 0; fallback de `exact_date` saltándose caps/flags (one-shots re-disparaban cada aniversario).
- **Starvation de guaranteed**: un evento guaranteed sin worker elegible bloqueaba TODOS los eventos del día.
- **Doble gate de priority**: los story/quest sin probabilidad explícita rodaban dos veces y con penalización
  de managers (contra el diseño). Ahora: una sola tirada por evento (su probabilidad, o 50 por defecto),
  sin managers; reducción de managers unificada a 10%/manager.
- 10 eventos con `worker_selection: "player"` (inválido): una choice nunca funcionaba y la otra crasheaba.
  Datos corregidos a `choose` + `threshold`, y el loader normaliza valores desconocidos.
- `basestring` (Py2), tecla **M** suelta que mataba la música (ahora Ctrl+M).

## El bug sistémico del call-stack (causa probable del "diálogo mezclado" de Yvara)

- 7 botones de hub usaban `Call()` hacia labels que nunca retornan → frames apilados para siempre
  (y guardados en los saves). Convertidos a `Jump()`.
- `yvara_check_stage_advance` hacía `jump` dentro de un label llamado desde ~58 sitios. Corregido
  (patrón de sus hermanos S5/S6).
- Los diálogos de objetivos 1-7 (llamados con `call`/`call_in_new_context`) terminaban en `jump` → ahora `return`.
- `label tavern_screen` limpia frames residuales al entrar (sanea también saves antiguos) y ya no puede
  hacer `return` sin caller.

## Features incompletas, ahora terminadas

- **Declinar → reaparecer**: el código de cooldown `{id}_passed` existía pero nada activaba los flags. Ahora
  cancelar un evento programa su reaparición.
- **Sabotaje del governor**: reducía `skill_bonus` "durante 3 días" pero jamás lo restauraba. Ahora se restaura
  (registrando la reducción real).
- **Duración de flags de workers**: 51 `duration` en los JSON sin ningún código que expirara nada. Implementado
  (los flags temporales expiran; los permanentes persisten; las 2 interacciones "Special" ya no se repiten a diario).
- **Skip de traits para workers únicos**: prometido en comentarios, no implementado — la Lanista recibía 2-4
  traits aleatorios al reclutarla. Implementado de verdad.
- **Motor de recruitment**: `player_gender_requirement` y `worker_filter` eran datos muertos (conectados),
  caps de ocurrencias respetados, floor de dificultad y skill-check central compartidos con el motor principal,
  bloques success/failure anidados ya no se pierden, "examine" ya no consume el intento del día, efecto `joy` aplicado.
- **Mecánicas de Yvara escritas pero inalcanzables** (`yvara_good_word`, `yvara_observed_lesson`): conectadas al menú.
- **Worker única "Daisy"** (workers_sfw_unique): irrecuperable por colisión de nombre con otras dos Daisy.
  Renombrada **Marigold** (folder `lily` intacto) y su evento de recruit + lore retargeteados.
- **Trait `Wounded`**: 3 eventos lo otorgaban y anunciaban sin existir. Definido (debuff temporal tipo Badly Burnt).
- **Endings dominion sin contenido post-arc**: +2 eventos ambient por arco (Yvara y Lanista).

## Mecánicas y balance

- Floor de éxito por dificultad en skill checks (nightmare 10% … story 50%) — antes un check sin threshold
  podía ser un 2%.
- `max_occurrences` autoral implica `limited` (el loader lo infiere; 20 one-shots marcados explícitos en datos).
- Lanista: apuestas con guard de dinero y EV no positivo; muro de regalos de S1-S3 reducido a la mitad
  (remarks +2, wager desde stage 1); ruta dominion ya no está en desventaja de afecto; Talk post-arc con
  gate diario; popup de introducción como el de Yvara.
- Salud/energía positivas se capan contra el máximo calculado (no contra 100 fijo).

## Escritura

- ~15 strings de `building_types.json` destrozados por un find-and-replace antiguo ("bereaches their peak",
  "undestined to fade…") reescritos.
- Outcomes de eventos de tiendas diferenciados por choice (antes las 3 opciones compartían texto idéntico).
- Critical success del manager único por edificio; ~60 frases-cliché de recruitment rotando 6 variantes.
- Clímax dominion S5/S6 de la Lanista reescritos para escalar de forma distinta; tic de "[_ttl]" reducido un tercio.
- Diálogos de objetivos 10-15 del tutorial condensados y con registro consistente; texto del objetivo 9
  corregido (decía "Magic", el check usa Craft); nota de la Academia con el gag de las seis letras ahora verídico.
- Comillas tipográficas normalizadas; "Accomodations" → "Accommodations".

## UI

- 12 pantallas muertas y 2 ficheros muertos eliminados (los estilos vivos `interaction_*` rescatados antes).
- Todos los puntos que renderizaban texto de JSON/usuario sin escapar (`!q`/pre-escape) — la clase de crash
  `SyntaxError` de la BIBLIA §9 queda cerrada; el input de renombrar edificios excluye `[]{}`.
- Efectos secundarios fuera del render path (auto-refill del mapa y sync de edificios a `on "show"`,
  seguros ante prediction).
- Rendimiento: caché de skills por render en la lista de workers (antes O(n²) y recálculo por hover),
  daily report memoizado por (día, filtros), fast-path de `font_size`.
- 405 colores hardcodeados centralizados en `gui.journal_*`; 58 refs de imagen con ruta explícita;
  viewport de workers 400→560 px; Quit con confirmación; botón Gallery (stub "Coming Soon") oculto;
  toggle NSFW refresca las cachés de traits/interacciones al instante.

## Sonido (antes: 2 ficheros, BGM sonaba una vez por sesión y silencio para siempre)

- BGM en bucle con pausa de respiración de 90 s; se auto-recupera tras cargar partida (`ensure_bgm_playing`).
- Eliminada la maquinaria muerta de BGM y el fallback a un fichero inexistente.
- Nuevo `core/audio.rpy` + 6 SFX procedurales en `game/audio/sfx/` (generados por script, WAV 16-bit):
  click global de botones, campanada de cambio de día, stingers de éxito/fracaso en eventos,
  y `coin`/`notify` listos para futuros hooks.

## Limpieza de código

- ~25 funciones/labels/clases muertos eliminados en script.rpy, main_flow, save_snapshot, config, workers,
  recruitment y tutorial.
- Deduplicados: automatización de inicio de día (5 copias → 1 helper), unlock del Castillo (3 copias
  divergentes → helper idempotente que no resetea upgrades), chunking de mensajes, level-ups por worker
  (el entrenamiento ya no recorre todo el roster por cada uso).
- Snapshot: listas de la Lanista restauradas con deepcopy como las de Yvara; `after_load` relee también
  desde la ruta legacy; stubs muertos fuera.

## Notas de compatibilidad

- **JSON y assets**: 100% compatibles; el motor sigue leyendo los mismos esquemas (y ahora tolera más errores).
- **Saves del original**: el sistema de snapshots es el mismo; la limpieza de call-stack sanea frames
  heredados al entrar a la taberna. Ojo: un save con la Daisy única reclutada (muy improbable: era
  inalcanzable) no encontrará su plantilla renombrada.
- **Persistent** compartido con el original (mismo save directory de Ren'Py).
