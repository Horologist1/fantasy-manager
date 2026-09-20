# Arcos VN: lo revisado, lo arreglado y un hueco

Estado: **un defecto corregido, un hueco documentado, una observación mía retirada.**

Tu impresión era correcta: los arcos VN son lo mejor cuidado del juego. Medido:

| | Yvara | Lanista |
| --- | ---: | ---: |
| Palabras de diálogo | 25.598 | 26.828 |
| Arcaísmos | 0 | 0 |
| 7-gramas repetidos ≥4 veces | 0 reales* | **0** |
| Concreción (por 1.000 palabras) | 25,3 | 20,0 |

\* Los 14 que marcaba el escáner están todos en un panel de estadísticas
(`[yvara_devotion] [yvara_dominion] [yvara_affection]`), no en prosa.

**Cero secuencias repetidas en 26.828 palabras** (Lanista) es mejor que cualquier
otra superficie del juego. Para comparar: las daily stories tenían 95.

---

## 1. Corregido: una referencia a una escena que no existe

`yvara_s2_talk_2` abría así:

> **Yvara:** «You said something the last time you were here.»
> **Yvara:** «About how you make decisions under pressure. **You said you go quiet.**»

**El jugador nunca dice eso.** Buscando en las 6.389 líneas del arco, la línea
991 es la única aparición de «pressure» + «go quiet»; todos los demás «quiet» son
narración sobre Yvara. Para el jugador es idéntico al defecto de Lily
(«moonlit garden confession») que documenta **LA BIBLIA §16**.

No es un problema general del arco: *«I told you once that I had not decided what
kind of person you are»* (L1238) **sí** tiene anclas reales en L665, 674, 830 y
896. Ésta era la excepción.

**Arreglo**: pasa de cita a impresión propia de ella.

> **Yvara:** «I formed an impression of you early on.»
> **Yvara:** «That under pressure you go quiet. Withdraw, and wait for it to pass.»
> **Yvara:** «You do not. I have watched you. You go very still, and then you act.»

Se conservan todos los beats. La narración que sigue — *«she says it as a
correction, the same way she would correct a student's misread passage»* — encaja
incluso mejor: la lectura errónea que corrige es la suya. La opción del menú
(*«I did not think you were listening that carefully»*) sigue funcionando.

---

## 2. Hueco: Yvara y Lanista están fuera del gate de review

`tests/test_event_presentation_contracts.py::ArcBackreferenceContracts` exige una
review editorial documentada y con fingerprint para **cada transición de arco**, y
la invalida en cuanto cambia la premisa o alguna rama. Es la red construida
precisamente contra el defecto de arriba.

Cubre **69 eventos** — arcos de personaje SFW y NSFW, arcos de monstruo, Aelis,
especiales — porque busca eventos con `arc_id`.

**Yvara (16 eventos) y Lanista (30) no usan `arc_id`,** así que quedan fuera. Los
dos arcos más largos y con más peso narrativo son justo los que no tienen red. El
defecto del punto 1 lo confirma: apareció donde no había gate.

Opciones, sin recomendación firme porque toca estructura de datos:

1. Añadir `arc_id` / `arc_stage` a los eventos de Yvara y Lanista y generar sus
   reviews en `tests/fixtures/event_arc_reviews.json`. Los mete en el gate
   existente sin escribir código nuevo.
2. Un gate aparte para los `.rpy`, que compruebe que toda cita del pasado tenga
   ancla. Más trabajo, y cubriría también las escenas que no son eventos JSON.
3. Dejarlo y revisarlo a mano cuando se toquen esos arcos.

---

## 3. Retirado: la "asimetría" de dirección escénica no existe

Afirmé que Lanista tenía 131 llamadas de emoción y Yvara **0**. Era falso, y el
recuento correcto lo desmiente por completo:

| | cambios de retrato | por línea de diálogo | expresiones usadas |
| --- | ---: | ---: | ---: |
| Yvara | **113** | 1 cada 18 | **17** |
| Lanista | 130 | 1 cada 9 | 6 |

Los dos arcos dirigen el retrato; **están construidos de forma distinta**:

- **Lanista** llama a un helper con nombre de emoción:
  `call lanista_show_emotion("warm")`.
- **Yvara** asigna la ruta en línea y la muestra:
  `$ _emote = "images/yvara/yvara_formal_warm.png"` + `show expression _emote`.

Yo conté solo el patrón de Lanista, y después solo una de las **12** variables
que usa Yvara (`_emote`, `_emote2` … `_emote5`, `_bust`, `_bust_kiss`,
`_bust_vulnerable`, `_bust_topless`, `_bust_unbutton`, `_yvara_emote`,
`_yvara_bust`). De ahí salieron primero 0 y luego 13.

Yvara además usa una paleta **más rica** — 17 expresiones frente a 6 — y la mueve
la mitad de a menudo, lo cual es coherente con el personaje: una académica
contenida cambia de cara menos que un maestro de arena. Eso es caracterización,
no un defecto.

**No hay nada que arreglar aquí.** Tres recuentos equivocados seguidos en esta
misma zona (0 → 13 → 113) son motivo suficiente para no volver a proponer cambios
de dirección escénica sin verlos en pantalla.
