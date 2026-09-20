# JSON overrides experimentales — 10 de septiembre de 2026

Implementación deliberadamente limitada a sustituir archivos JSON completos, pensada para empezar una partida nueva con un conjunto estable de mods. No cambia los cargadores de cada catálogo ni el formato de los guardados.

## Uso

1. En el menú principal, abrir **Mods → Install mods**.
2. Marcar **Import as JSON override (experimental)**. Está desmarcada al arrancar y después de instalar. Antes de activarse muestra una advertencia; cancelar no la activa.
3. Elegir un ZIP o carpeta que conserve las rutas originales `data/...`. En Android, elegir un ZIP mediante el selector del sistema.
4. Revisar los archivos que se sustituirán y pulsar **Install JSON override**.
5. Cerrar y volver a abrir el juego; empezar una **partida nueva**.

La casilla selecciona el modo de la próxima importación. Desmarcarla no desactiva los overrides ya instalados: esos packs se retiran mediante **Uninstall**. La retirada, igual que la instalación, se aplica en el siguiente arranque. Puede cancelarse antes de reiniciar.

Sin marcarla se conserva el importador habitual de personajes e imágenes. No se cambia su comportamiento de añadir personajes ni su gestión de nombres repetidos.

## Qué significa sustituir

La coincidencia es por **ruta y nombre de archivo exactos**, incluyendo mayúsculas. No se buscan entradas con el mismo nombre o `id` en todo el juego. No se mezclan automáticamente campos.

Si el pack contiene `data/items/alchemy_ingredients.json`, ese archivo completo se usa en lugar del original. El autor debe conservar dentro todas las entradas que quiera mantener. Un archivo que contenga solo Ironroot omitiría los demás ingredientes definidos en el mismo archivo.

Si dos packs sustituyen la misma ruta, prevalece el instalado después. La vista previa avisa de las coincidencias con otros overrides instalados. La lista muestra la prioridad asignada. Reinstalar un pack idéntico no lo duplica ni cambia su prioridad. Al retirar el último y reiniciar reaparece la versión anterior, o la original si no queda ningún override.

Los cargadores conservan sus reglas internas: por ejemplo, las extensiones de historias diarias siguen aplicándose después de cargar los edificios. Para cambiar una historia procedente de una extensión, se debe sustituir su archivo de extensión. La prioridad entre packs no altera las reglas de resolución de identificadores entre archivos distintos.

## Archivos admitidos

Solo se admiten destinos que **ya existan en la versión instalada**:

| Catálogo | Rutas relativas |
| --- | --- |
| Workers | `data/workers/*.json`; `data/workers.json` si esa versión lo incluye |
| Items | `data/items/*.json` |
| Traits | `data/traits/*.json` |
| Buildings | `data/buildings/*.json` |
| Daily stories | `data/buildings/daily_story_extensions/*.json` |
| Eventos | `data/events/*.json` y `data/events/recruit/*.json` |

Puede haber una carpeta envolvente dentro del ZIP, por ejemplo `MiMod/game/data/...`, pero no varias raíces de juego. Las imágenes, scripts, ajustes y archivos de otras categorías se excluyen de este modo. No se añaden rutas de búsqueda de scripts ni se importan `.rpy`, `.rpyc` o `.py`.

Se comprueban rutas, límites de tamaño, enlaces, JSON mal formado, números no finitos, claves JSON repetidas, estructura principal e identificadores ausentes o repetidos dentro de un archivo. Esta comprobación **no demuestra que el contenido sea jugable**: el autor sigue siendo responsable de referencias, efectos, requisitos y continuidad de sus eventos. Usar únicamente mods de confianza.

## Instalación y límites

- Los archivos originales del juego y el ZIP/carpeta de origen no se modifican.
- Los overrides usan el almacenamiento gestionado `character_mods` junto a los packs aditivos; su manifiesto usa formato 2. Los packs de personajes existentes mantienen el formato 1.
- La copia se prepara por completo antes de publicar el pack. Un error de copia retira únicamente su instalación temporal.
- En el arranque se revisan estructura e integridad de los archivos instalados. Un pack dañado o con destinos que ya no existen no se activa.
- No hay migración de partidas previas, aplicación en caliente, fusión de campos, reordenación manual ni dependencias entre mods.
- Quitar un mod no deshace cambios que ya hayan quedado dentro de una partida. Para el alcance soportado, instalar los packs antes de empezar y mantenerlos durante esa partida.
- Android dispone ahora de un selector nativo de ZIP, comprobado en un dispositivo con Android 16. Usa el mismo importador y la misma lectura de datos; no necesita modificar el APK ni permisos de acceso general al almacenamiento. Compilación y pruebas: [Importación Android](ANDROID_MOD_IMPORT_2026-09-10.md).

La implementación inicial de overrides quedó en tres archivos: `fm_mods/packs.py`, `fm_mods/runtime.py` y `scripts/mods/character_mods.rpy`. El soporte Android añade un puente nativo y su módulo de acceso, documentados por separado. No se ha modificado ningún JSON del juego, cargador de catálogo, evento, sistema de guardado ni partida del usuario para añadir estas funciones.

## Verificación

Comprobaciones ejecutadas con Ren'Py **8.3.7.25031702** en copias desechables, con partidas y preferencias separadas:

- **277 pruebas y 463 subtests** de la batería general, incluidas las comprobaciones obligatorias de guardado del motor.
- **70 comprobaciones nativas en escritorio y 70 en variante `small touch`**. Cada ejecución recorre: juego original, dos overrides más un pack aditivo, guardar/cargar manteniendo los packs, retirar el último override, retirar todos los overrides y probar la interfaz.
- Los seis catálogos se verifican mediante los cargadores reales después de ejecutar el `label start` real. La herramienta automatiza únicamente la narración introductoria y la entrada de nombre/título; conserva el reinicio de estado, calendario, mercado y demás inicialización.
- Clics mediante el ratón virtual del SDK: casilla apagada, aviso, cancelar, aceptar, desmarcar, vista previa, instalar, cancelar desinstalación y confirmar desinstalación. Se comprueba que instalar espera al siguiente proceso.
- **12 guardados nativos nuevos y dos cargas entre procesos** entre las dos ejecuciones completas. No se han adaptado ni prometido compatibles partidas de otra configuración de mods.
- Control negativo: deshabilitar deliberadamente la lectura alternativa en la copia desechable hace fallar la comprobación del primer catálogo. La prueba detecta una instalación que aparece en la lista pero no se aplica.
- Inspección de capturas del aviso y la vista previa. Los contenidos largos permanecen dentro del área desplazable.
- Lint del proyecto de producción en una copia limpia: código de salida 0, sin errores ni avisos.

Evidencias:

- Escritorio: `backups/override-qa-20260910-012751-547271/report.json`.
- Variante móvil: `backups/override-qa-20260910-012846-642108/report.json`.
- Control negativo: `backups/override-qa-20260910-012847-202365/report.json` (fallo esperado).
- Batería general: `backups/json-overrides-20260910-010907/pytest-full-required`.
- Backup previo y entrega: `backups/json-overrides-20260910-010907/`.
- ZIP de ejemplo: `backups/json-overrides-20260910-010907/example-ironroot-price-override.zip`. Conserva el catálogo completo de ingredientes y cambia únicamente el precio de Ironroot a 240. No se ha instalado en el juego del usuario.

Durante el desarrollo de la herramienta, una pausa automática quedó retenida por un aviso modal; se corrigió la prueba usando pausas que permiten seguir automatizando modales. Otra ejecución de carga excedió el tiempo de espera sin diagnóstico; no volvió a reproducirse en las dos ejecuciones finales completas. Se añadió un límite de interacción con captura de diagnóstico. Las ejecuciones incompletas no se cuentan como verificaciones aprobadas.

Reproducción desde la raíz del proyecto:

```powershell
$env:RENPY_RUNTIME_REQUIRED = '1'
python -m pytest tests -q -p no:cacheprovider --basetemp backups/override-pytest-new-run
python tools/qa_json_overrides.py
python tools/qa_json_overrides.py --variant 'small touch'
python tools/qa_json_overrides.py --fault  # Debe fallar: control negativo.
```

Los informes parciales no equivalen a éxito: la herramienta exige que terminen todas las fases con código cero. Las copias de prueba redirigen las carpetas de guardado y preferencias, y no inyectan scripts en el proyecto de producción.
