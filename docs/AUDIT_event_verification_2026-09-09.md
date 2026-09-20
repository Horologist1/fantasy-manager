# Verificación de eventos — auditoría del 9 de septiembre de 2026

Cierre realizado el 10 de septiembre. La auditoría de Claude fue el punto de
partida; sus conclusiones se contrastaron con el código y con Ren'Py
**8.3.7.25031702**, la versión real del SDK instalado.

Los defectos reproducidos están corregidos. Esta verificación cubre el catálogo
actual y los escenarios descritos abajo; no equivale a garantizar cualquier
modificación futura ni una instalación Android en un dispositivo físico.

## Correcciones

- Se conserva la corrección de estilos de Claude. Los contenedores de opciones
  tienen estilos propios y no heredan la posición absoluta del menú estándar.
  Las listas largas se desplazan sin reducir la letra; las cortas siguen centradas.
- **Fallo adicional reproducido:** `Return(None)` devolvía `True` al pasar un
  evento sin opciones disponibles. El caller podía intentar tratarlo como un
  diccionario. Ahora la cancelación devuelve `False` y el caller reconoce también
  sentinelas de pantallas anteriores. No aplica efectos ni completa el arco.
- La selección de trabajador usa la misma cancelación explícita. Un menú de
  reclutamiento sin opciones tiene una salida distinguible de volver de Examine.
- **Fallo adicional reproducido:** un alta duplicada podía sumar dinero o
  reputación antes de rechazar al trabajador. La validación del alta ocurre ahora
  antes de esos efectos, también para fallecidos, monstruos y ausencia de candidato.
  Una respuesta rechazada no anuncia éxito ni consume otra ocurrencia.
- Se revisaron las **46 transiciones de 23 arcos**, con las descripciones, opciones
  y resultados de éxito, fallo y rechazo. Se ajustaron textos de 42 eventos; parte
  de esos cambios elimina fechas exactas que el calendario no garantiza.
  Los IDs, requisitos, recompensas y condiciones de encadenado del JSON se conservan.

Entre los problemas de continuidad corregidos: recordar una actuación rechazada,
dar por capturado a quien escapó, disponer de un libro destruido, usar pruebas
que solo se obtienen en una rama, recordar regalos que el jugador nunca hizo,
y presentar como consolidado un acuerdo cuya negociación pudo fallar.

## Respuesta a los nueve puntos de la auditoría

| Punto | Resolución |
| --- | --- |
| 1. Cinco reescrituras | Lily y Rose conservan sus anclas concretas. Aspen admite el retorno de la amenaza después de las distintas precauciones. Florian presenta a Evren y su máscara antes de los resultados, y explica la compra posterior de la página. Se conserva la introducción de la plancha floral de Iris y se aclara la procedencia del cifrado. |
| 2. Cobertura narrativa | Ampliada a las 46 transiciones y todos sus resultados. Cada una tiene una nota editorial y huellas de su texto y sus condiciones en `tests/fixtures/event_arc_reviews.json`. Cambiar una frase posterior, un desenlace o un requisito invalida la revisión. **Las huellas no entienden inglés:** obligan a volver a leer, no certifican automáticamente la coherencia. |
| 3. Clics | El arnés pulsa coordenadas medidas por el motor. Para cada evento con opciones bloqueables usa dos distribuciones de bloqueos: cada fila se selecciona cuando está disponible y cada bloqueo recibe un clic que debe ser ignorado. Comprueba el valor exacto devuelto. |
| 4. Móvil | Barrido completo con `small touch`, comprobando que se aplicó la variante y que los botones miden 1860 px, frente a 1185 en escritorio. Incluye arrastre. No se ha probado un APK físico. `android_preflight.py` no está en este árbol: ese cruce corresponde al empaquetado Android. |
| 5. Margen de altura | Viewport de hasta 1000 px en el diseño 1920×1080, rueda, teclas, arrastre táctil y barra al desbordar. Se prueban listas artificialmente largas y motivos de bloqueo extensos hasta pulsar la última opción o la salida. |
| 6. PIL frente al motor | Eliminado el presupuesto basado en ajuste codicioso de PIL. La geometría y la entrada se verifican con el maquetador de Ren'Py. |
| 7. Contenedores | Se buscan herencias peligrosas de posiciones absolutas en todas las pantallas con prefijos del árbol de scripts. Las dos listas principales exigen estilos explícitos; también se nombran los contenedores de los cuatro menús finales de interacciones. La posición del menú estándar sigue siendo intencionada. |
| 8. Reclutamiento | Trabajador de prueba preparado por el juego, clic en contratar/rechazar, Examine y vuelta; 182 resoluciones del catálogo de reclutamiento con tiradas alta/baja, cantidades, mensajes, coste diario, asignación e integridad del candidato. Se usa el procesador real `process_recruitment_choice`; no existe otra función `process_advanced_recruitment_choice` en este árbol. Se añade regresión para altas rechazadas antes de los efectos. |
| 9. Versionado | Se habilita el versionado de los dos archivos del arnés y de este informe, manteniendo privadas las demás carpetas de documentación/herramientas. Pruebas y revisiones editoriales quedan bajo `tests/`. No se ha creado ningún commit. |

## Resultados comprobados

| Comprobación | Resultado |
| --- | --- |
| Batería completa, incluido el guardado con fixture anterior | **250 pruebas y 463 subcasos: pasan** |
| Ren'Py, escritorio | **2202 casos, 0 fallos** |
| Ren'Py, `small touch` | **2202 casos, 0 fallos** |
| Lint de producción en copia limpia | **0 errores y 0 avisos** |
| Guardado tras las pruebas de eventos | Dos archivos nativos nuevos por variante, comprobando que se escribieron bytes nuevos |
| Control del serializador | Un objeto de fichero introducido deliberadamente en las raíces de guardado es rechazado por el serializador real |
| Compatibilidad adicional | La batería de muerte/resurrección vuelve a pasar sus fases anterior, actual y proceso nuevo, incluidos guardados durante confirmaciones y progreso del templo |

Cada barrido contiene 1470 casos de geometría, 535 de entrada en eventos, cuatro
de entrada en reclutamiento, tres cancelaciones de selección de trabajador,
cuatro recorridos del evento real, 182 resoluciones de reclutamiento, un rechazo
duplicado y tres controles de guardado.

Los controles negativos reintroducen en **copias** el estilo que desplazaba los
botones, un retorno de opción incorrecto y la ausencia del límite de altura.
Deben fallar. Los informes conservan tanto esas reproducciones como los resultados
positivos; un fallo provocado no se presenta como una prueba positiva del juego.

El arrastre usa el ratón de pruebas del propio SDK. Este inyecta eventos SDL y
mantiene la posición virtual durante los temporizadores del motor, sin mover el
puntero del usuario y sin ejecutar directamente las acciones de los botones.

## Evidencia y reproducción

- [Backup previo de 106 archivos](../backups/event-audit-20260909-232728/before.zip)
  y [huellas originales](../backups/event-audit-20260909-232728/before.sha256.json).
- [Informe nativo de escritorio](../backups/choice-qa-20260910-000610-748053/saves/report.json).
- [Informe nativo móvil](../backups/choice-qa-20260910-000621-870445/saves/report.json).
- [Lint](../backups/event-audit-20260909-232728/lint.txt).
- [Guardado y compatibilidad de muerte/resurrección](../backups/death-resurrection-20260909-160949/runtime-20260909-235402/saves/life-qa.txt).
- [Revisión por transición](../tests/fixtures/event_arc_reviews.json).

En PowerShell, desde el proyecto:

```powershell
$env:RENPY_RUNTIME_REQUIRED = '1'
python -m pytest tests -q -p no:cacheprovider --basetemp backups/qa-event-tests-nuevo
python tools/qa_choice_layout.py --mode all
python tools/qa_choice_layout.py --mode all --variant "small touch"
python tools/qa_choice_layout.py --mode layout --limit 2 --fault locked-style
python tools/qa_choice_layout.py --mode clicks --limit 1 --fault wrong-return
python tools/qa_choice_layout.py --mode clicks --limit 1 --fault no-scroll
```

Los tres últimos comandos deben devolver fallo. Se puede indicar otro ejecutable
Ren'Py con `--sdk`. La prueba histórica de Storage/guardado también requiere su
fixture anterior, configurable mediante `FM_QA_BASELINE_ROOT`; si falta, falla
explícitamente. El arnés de eventos crea su propia copia y no depende de ese fixture.

No se ha cambiado el formato del snapshot, ni añadido estado persistente al juego.
Las copias de prueba aíslan `APPDATA`, `LOCALAPPDATA` y `savedir`. No se inyectan
scripts en el juego activo, ni se modifican las partidas o el persistent del jugador.

Para una futura modificación: volver a revisar las ramas afectadas, actualizar
sus notas editoriales y ejecutar los barridos. No regenerar las huellas a ciegas
para conseguir una batería verde.
