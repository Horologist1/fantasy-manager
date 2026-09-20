# Importación de mods en Android — 10 de septiembre de 2026

El menú **Mods → Install mods** permite importar ZIP desde el selector de documentos de Android. Sirve para packs de personajes e imágenes y para el modo experimental de sustitución de JSON. Se conserva el importador de ZIP/carpetas de escritorio.

## Uso

**Mods** está en la esquina inferior derecha del menú principal, encima de la versión. **Create Mods** abre el [devkit web](https://horologist1.github.io/fantasy-manager/devkit/) y **Install mods** abre el importador. El consejo sobre Discord/F95 aparece al pie de este menú. No hay accesos a mods desde Opciones ni desde la navegación de partida.

1. Guardar el ZIP en Descargas, o elegirlo desde otro proveedor de documentos.
2. En el menú principal del juego, abrir **Mods → Install mods → Choose ZIP**.
3. Elegir el ZIP y revisar la vista previa. La copia y la comprobación no instalan automáticamente el pack.
4. Pulsar **Install this pack**, o la variante que conserva ambos nombres si hay coincidencias.
5. Cerrar completamente y volver a abrir el juego para activar el pack.

Para sustituir JSON, activar primero **Import as JSON override (experimental)** y aceptar su advertencia. La casilla comienza desactivada y se desactiva al terminar la instalación. Instalar los overrides antes de comenzar una partida nueva y mantener el mismo conjunto durante esa partida. Se sustituyen archivos completos por ruta exacta; no hay fusión de campos. Véase [el contrato de overrides](JSON_OVERRIDES_2026-09-10.md).

**Uninstall** prepara la retirada para el siguiente arranque. Puede cancelarse antes de reiniciar. No borra el ZIP original ni las partidas. Quitar un pack de personajes deja sin sus imágenes a los personajes de ese pack que permanezcan en un guardado. Quitar overrides requiere empezar otra partida para volver a las definiciones restantes.

En Android se importan ZIP, no carpetas completas. Los documentos de proveedores remotos dependen de que esos proveedores puedan entregar el archivo; un ZIP ya descargado ofrece el recorrido más sencillo. Los archivos se copian al almacenamiento propio de la aplicación: nunca se abren ni reescriben los archivos del APK.

## Implementación

- `tools/android/ModImportActivity.java`: actividad privada, no exportada, añadida al APK durante la compilación. Abre `ACTION_OPEN_DOCUMENT` con `CATEGORY_OPENABLE` y recibe el URI. Usa `ContentResolver.openInputStream`, sin convertir un `content://` en ruta de disco.
- El selector permite documentos con tipos MIME distintos porque algunos proveedores etiquetan los ZIP como datos genéricos. El importador exige que el contenido sea realmente un ZIP válido.
- Copia por bloques de 64 KiB a una carpeta aleatoria propia en `cache/fm-mod-import`. Impone un límite de 1 GiB sobre los bytes realmente leídos, aunque el proveedor no indique tamaño. Las validaciones existentes añaden límites sobre archivos, JSON, contenido descomprimido, imágenes y rutas.
- La lectura del documento ocurre en un hilo; la actividad conserva el permiso temporal mientras está abierto el stream. Muestra progreso y permite cancelar. No solicita permisos generales de almacenamiento ni conserva permisos persistentes sobre documentos.
- Los resultados y el archivo temporal permanecen en el módulo Python y en campos estáticos Java, fuera del `store`, `persistent`, guardados y rollback de Ren'Py. No se guardan objetos JNI, streams, hilos o actividades.
- `game/python-packages/fm_mods/android_picker.py` accede al puente mediante Pyjnius exclusivamente al usar Android. Se importa antes de la predicción de pantallas, pero no carga clases Android en escritorio.
- `fm_mods/runtime.py` conduce el estado de selección, copia, validación e instalación. Retiene la copia mientras exista una vista previa válida, para permitir la segunda comprobación de integridad durante la instalación. La libera al instalar, descartar la vista previa, cambiar de modo o rechazar el archivo.
- Los residuos de una copia interrumpida por la muerte del proceso se limpian al abrir otro selector. Solo se consideran las carpetas privadas de staging del puente, nunca documentos de Descargas ni carpetas de partidas/mods instalados.
- `character_mods.rpy` conserva la misma pantalla, advertencia y confirmación que escritorio; en Android abre el selector nativo. Se mantiene la restricción de instalar/desinstalar desde el menú principal.

La actividad independiente también evita un fallo del SDK usado: `PythonSDLActivity.onActivityResult` llama a `resultData.toString()` sin comprobar `null`. Cancelar un selector podía hacer fallar esa ruta. Este puente recibe sus propios resultados, incluido el resultado nulo de cancelación; no modifica `PythonSDLActivity` ni usa callbacks de Kivy que este motor no garantiza.

## Compilación reproducible

El puente Java debe estar dentro del APK. Copiar solamente los `.rpy` y `.py` a una compilación Android antigua no lo añade. Usar:

```powershell
# APK separado, firmado con clave de depuración y paquete fantasy.manager.modqa:
python tools/build_android_mods.py

# APK normal, fantasy.manager, firmado con el android.keystore existente:
python tools/build_android_mods.py --release
```

La herramienta usa una copia desechable del juego y del SDK en `backups/android-build-FECHA/`. Añade la clase y la declaración de actividad a esa copia de RAPT. No altera el SDK original, no genera claves de publicación nuevas y no instala ni reemplaza aplicaciones automáticamente. `--release` usa la configuración estándar de firma de Ren'Py y requiere la clave existente del proyecto.

Parámetros disponibles: `--sdk`, `--android-sdk`, `--jdk`, `--gradle-cache`. La compilación usa las dependencias Gradle ya descargadas, en modo offline. Si faltan, falla en vez de actualizar automáticamente las herramientas del sistema.

Para reintentar una compilación preparada:

```powershell
python tools/build_android_mods.py --resume backups/android-build-FECHA
# Si los assets ya están preparados y solo falló Gradle:
python tools/build_android_mods.py --resume backups/android-build-FECHA --gradle-only
```

La salida `apk/verification.json` comprueba el identificador dentro del APK y registra SHA-256 y tamaño. `source-manifest.json` registra los `.rpy`, `.py` y JSON utilizados. No distribuye documentación, tests, backups, herramientas ni claves privadas dentro del APK.

Herramientas utilizadas: Ren'Py **8.3.7.25031702** (directorio local denominado `renpy-8.3.4-sdk`), RAPT del SDK, Java 21, Android SDK 35, Gradle 8.5. En esta sesión fue necesario ejecutar Gradle fuera del aislamiento de herramientas de Codex: el aislamiento impedía cerrar un JAR de su propia caché. La compilación siguió usando sus directorios de trabajo separados.

## Verificación

- **285 pruebas y 463 subpruebas aprobadas**, con `RENPY_RUNTIME_REQUIRED=1` y guardados reales del motor.
- **70 comprobaciones nativas de escritorio y 70 en `small touch`**, repetidas tras integrar Android. Incluyen los seis catálogos, arranque de partida nueva, guardado, carga entre procesos, retirada de overrides y botones reales del menú.
- Ocho pruebas nuevas del ciclo Android: selección cancelada, doble pulsación, error de copia, puente ausente, ZIP rechazado, instalación normal, override, conservación y liberación de la copia temporal.
- APK de pruebas instalado en **OnePlus CPH2653, Android 16, páginas de memoria de 4 KiB**, como `fantasy.manager.modqa` / **FM Mod QA**. La aplicación previa `fantasy.manager` se conserva.
- Apertura real del selector de documentos, cancelación mediante Atrás y nueva selección correctas.
- Importación real mediante el selector del pack adjunto **Varied Girls**: **28 personajes, 1.438 imágenes, 153,4 MiB** de imágenes. La vista previa identifica los tres nombres coincidentes y la instalación conserva ambas versiones. La copia temporal se elimina al terminar.
- Importación mediante el selector del ZIP **Ironroot-override**, con activación explícita de la casilla y revisión de los archivos. Ambos packs se activan al reiniciar el proceso.
- Comprobación en la consola de desarrollo del APK: aparecen las **1.438 imágenes virtuales** y el JSON servido por `renpy.file` devuelve **Ironroot a 240**, frente a 200 en el archivo original.
- Partida nueva **AndroidQA**, con ambos packs activos y NSFW desactivado. El usuario completó personalmente el aviso de edad. Guardado desde el botón real de la primera ranura y carga desde **Load** después de cerrar y volver a abrir el proceso: se recuperan nombre, día 1 y 6.000 de oro. Capturas `28-saved.png`, `30-load-menu.png` y `31-loaded.png`.
- Retirada del override desde **Uninstall**, cancelación de esa retirada pendiente, nueva confirmación y reinicio. Desaparece de la lista y `renpy.file` devuelve otra vez **Ironroot a 200**; Varied Girls continúa activo con sus **1.438 imágenes virtuales**. Capturas 34–37 y `38-removal-log.txt`.
- APK normal `fantasy.manager` generado con la clave existente y firma v1/v2 verificada. Su código fuente está registrado en el manifiesto de esa compilación. Conserva la etiqueta `0.9.6.1` del proyecto, con un nuevo código de versión Android; no se ha cambiado la numeración del juego.

La prueba en un teléfono no garantiza todos los proveedores remotos, versiones de Android o dispositivos. No se han migrado partidas entre configuraciones de mods. Las pruebas automatizadas de escritorio con interfaz pequeña no se presentan como sustitutas de las pruebas realizadas en el teléfono.

Evidencias de esta sesión:

- Backup previo: `backups/android-mod-import-20260910-013723/before.zip` y `before.sha256.json`.
- Capturas y comprobaciones del dispositivo: `backups/android-mod-import-20260910-013723/device/`.
- Resultado final del dispositivo y límites de la comprobación: `backups/android-mod-import-20260910-013723/device/report.json`.
- Pruebas generales: `backups/android-mod-import-20260910-013723/full-suite-final/`.
- Escritorio: `backups/override-qa-20260910-015055-935019/report.json`.
- Pantalla pequeña: `backups/override-qa-20260910-015631-456440/report.json`.
- APK separado: `backups/android-build-20260910-014729/apk/FantasyManager-current-ModQA-20260910.apk`.
- APK normal: `backups/android-build-20260910-020627/apk/FantasyManager-current-Android.apk`.

Los ZIP de prueba se copiaron por USB a `Download/FantasyManager-QA-20260910`. Fue necesario notificar al índice de documentos de Android que había archivos nuevos: es una particularidad de la copia por ADB usada en la prueba; un usuario que descarga o guarda un documento normalmente pasa por el gestor de archivos del sistema.

Estado dejado en el teléfono: **FM Mod QA** en el menú principal, Varied Girls activo y el override de prueba retirado. Los dos ZIP se conservan en Descargas. La ranura AndroidQA es una evidencia de pruebas, creada con el override activo; para jugar después de retirarlo hay que empezar una partida nueva. La aplicación anterior `fantasy.manager` sigue en **0.9.6.3 / 1787609178** y no se ha actualizado ni desinstalado. El APK normal se entrega como archivo; solo se instaló la aplicación separada de pruebas.

Referencias de plataforma: [Ren'Py en Android](https://www.renpy.org/doc/html/android.html), [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files).

## Revisión estética del menú

El acceso lateral **Mods**, las opciones **Create Mods** e **Install mods**, y la retirada de accesos desde Opciones se comprobaron con letra normal/grande y navegación real del motor entre menús. Lint sin incidencias. Backup y capturas: `backups/mods-menu-20260910-024506/`.

El APK actualizado `backups/android-build-20260910-014729/apk/FantasyManager-current-ModQA.apk` se instaló correctamente sobre **FM Mod QA**, conservando sus datos. El teléfono dejó de aparecer por USB inmediatamente después; la comprobación del recorrido de vuelta se completó en escritorio. El APK normal listado arriba corresponde a la compilación anterior a esta revisión estética.
