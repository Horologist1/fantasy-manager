# Auditoría general — 2026-09-10

Se han corregido fallos reproducidos en guardado/carga y eventos. Los cambios de ejecución se limitan a `save_snapshot.rpy` y `events.rpy`; se añaden pruebas y se actualiza la documentación técnica. Se conservan los cambios anteriores de templo, alquimia, mods y menús.

## Hallazgos corregidos

| Hallazgo | Consecuencia | Corrección y comprobación |
|---|---|---|
| Progreso omitido del snapshot | La carga con reinicio perdía etapa, visita e intentos de la biblioteca, introducción de la directora, plazo entre eventos, elección de venganza, contador de monstruos y marca de tutorial omitido. El juego podía repetir contenido o retroceder un puzzle sin lanzar una excepción. | Nueve campos opcionales de v3, con captura y restauración comunes. Los campos ausentes se recuperan de las raíces nativas verificadas. Una partida real creada antes de la corrección vuelve a cargar sus ocho valores de prueba correctamente. |
| Recuperación vulnerable a interrupciones | Se reemplazaban ambas copias JSON antes del guardado nativo; un fallo adicional al restaurar podía eliminar la última generación compatible. La limpieza temporal también podía borrarla. | Preservar la generación compatible antes de modificar los archivos. Mantenerla si falla la restauración y admitirla como RECOVERY, comprobando ranura, GUID y transacción. Solo se elimina tras confirmar el guardado o la restauración. |
| Excepción posterior al guardado nativo | El tratamiento de errores podía restaurar el JSON anterior aunque Ren'Py ya hubiera escrito la nueva partida. | Detectar el compromiso nativo y conservar su pareja JSON. Se prueban errores antes y después de la escritura, cancelaciones y cambios de fecha de archivo que no representan un guardado real. |
| Falta de validación completa antes de escribir | Un estado con dinero y trabajadores presentes podía guardarse aunque incumpliera otros requisitos de carga. | La escritura exige el mismo contrato que la carga. Una prueba nativa comprueba que un estado inválido no sobrescribe la partida válida. La restauración fallida revierte también los campos opcionales. |
| Firma nativa ignorada por la carga personalizada | Se deserializaba el archivo para leer su identidad sin pasar por la comprobación de confianza de Ren'Py. | Ejecutar `renpy.savetoken.check_load` antes de deserializar. Un rechazo impide tanto la lectura del pickle como el reinicio para cargar. |
| Nombres interpretados como instrucciones de sustitución | Un nombre como `Guest\Q` o `Guest\1` podía romper un evento al elegir trabajador. | Sustituir nombres como texto literal desde un helper de inicialización; conservar correctamente el plural «the workers». |

También se protege la ruta `SnapshotFileSave(confirm=True)`: la confirmación aplaza la transacción completa. Era un riesgo latente de esa API; los botones actuales ya usan una confirmación externa. La prueba comprueba que no se modifica ningún archivo antes de aceptar.

## Compatibilidad y prevención

- Se mantiene `snapshot_version = 3` y no se amplía la lista de claves obligatorias de las partidas antiguas. JSON sigue siendo la fuente principal; la recuperación nativa solo rellena las nueve claves permitidas cuando faltan y tienen un valor válido.
- Si un dato tampoco existe en el guardado nativo, se usa su valor inicial. La etapa de biblioteca se deduce únicamente cuando las pistas ya guardadas justifican ese avance. No se puede reconstruir una decisión que haya desaparecido de ambas fuentes.
- Una copia de otra ranura, GUID o transacción no puede servir de recuperación. Si no queda una pareja válida, el intento de sobrescritura se cancela conservando los archivos existentes.
- La prueba de cobertura exige revisar cada nuevo `default` público: debe guardarse o documentarse expresamente como presentación, constante o dato derivado. Se amplía a todos los scripts la búsqueda de patrones que pueden contaminar el estado serializable.
- La documentación técnica afirmaba que no se usaban guardados nativos y aconsejaba añadir pasadas de restauración. Se ha actualizado al recorrido actual de aplicación única sobre un contexto limpio.

La batería inicial pasó **285 pruebas y 463 subcasos**, pero no cubría la omisión de esos campos ni los fallos combinados de escritura y restauración. Se conserva la reproducción anterior: 19 de sus 20 comprobaciones fallaban. Las nuevas pruebas detectan específicamente esas rutas; no se han regenerado las huellas de revisión narrativa para ocultar cambios.

## Validación final

| Comprobación | Resultado |
|---|---|
| Batería completa, con motor obligatorio | **312 pruebas y 463 subcasos, todos correctos** |
| Nueva prueba nativa de guardados | **92 comprobaciones correctas**: sobrescritura, reinicio/carga, v3 con campos ausentes, recuperación, rechazo de estado inválido y rollback |
| Partida real creada antes de la corrección | **10 comprobaciones correctas**; archivo nativo y dos JSON originales conservados byte a byte |
| Eventos: escritorio | **2.202 casos, 0 fallos** |
| Eventos: variante `small touch` | **2.202 casos, 0 fallos**; controles de 1860 px frente a 1185 px en escritorio |
| Lint en copia de producción | **0 errores y 0 avisos** |

Los barridos de eventos incluyen geometría, clics, opciones bloqueadas, desplazamiento, selección de trabajador, reclutamiento, cuatro recorridos del evento real y guardado nativo después de sus pantallas. Se ha usado Ren'Py **8.3.7.25031702**. Todas las pruebas emplean copias aisladas, con directorios propios para partidas y preferencias.

Esto no certifica todas las combinaciones posibles de mods y partidas. La variante táctil se ha probado en el motor de escritorio: no se ha construido ni instalado un APK nuevo en esta auditoría. Las interrupciones de escritura se provocan mediante inyección de fallos; no mediante un corte físico de alimentación.

## Evidencias y reproducción

- [Backup previo de 263 archivos](../backups/general-audit-20260910-030242/before.zip) y [huellas originales](../backups/general-audit-20260910-030242/before.sha256.json).
- [Reproducción inicial](../backups/general-audit-20260910-030242/repro/report.json) y [fallos de recuperación antes del arreglo](../backups/general-audit-20260910-030242/recovery-red.txt).
- [Batería completa final](../backups/general-audit-20260910-030242/verified-tests.txt), [92 comprobaciones nativas](../backups/general-audit-20260910-030242/verified-tests/test_real_canonical_load_prese0/saves/report.json) y [carga de la partida anterior](../backups/general-audit-20260910-030242/historical-saves/report.json).
- [Barrido de escritorio](../backups/choice-qa-20260910-033254-284306/saves/report.json) y [barrido táctil](../backups/choice-qa-20260910-033729-432793/saves/report.json).
- [Lint](../backups/general-audit-20260910-030242/lint.txt).

```powershell
$env:RENPY_RUNTIME_REQUIRED = '1'
python -m pytest tests -q -p no:cacheprovider --basetemp backups/auditoria-nueva
python tools/qa_choice_layout.py --mode all
python tools/qa_choice_layout.py --mode all --variant 'small touch'
```

La prueba histórica de Storage requiere su fixture anterior (`FM_QA_BASELINE_ROOT`). La nueva prueba general de guardados crea sus propios datos y acepta la ubicación del motor en `RENPY_EXE`. Las copias de auditoría y partidas de prueba se excluyen de Git mediante `/backups/`.
