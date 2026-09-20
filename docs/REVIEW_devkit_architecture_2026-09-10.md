# Revisión de arquitectura del devkit — 10 de septiembre de 2026

## Dictamen

La base modular es adecuada para mantener el editor, pero el devkit todavía no está preparado como herramienta de creación de packs para el menú Mods actual. Se pueden conservar los esquemas, asistentes, editores, conversores y distribución web/offline. Hace falta completar la gestión del proyecto, la exportación y el contrato con el importador; además hay fallos de escritura y validación que conviene corregir antes de publicar una actualización.

El diseño original de junio excluía expresamente un gestor de mods dentro del juego y se apoyaba en copiar JSON a `game/data`. El juego ahora tiene otro punto de entrada: packs gestionados de personajes y overrides de archivos completos. El devkit no se ha adaptado a ese cambio. No se necesita modificar las saves para resolverlo.

## Alcance y estado comprobado

- Código local revisado: `C:/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager-devkit-web/devkit_web`. Vive en otro worktree y contiene cambios sin publicar. La copia actual del juego utilizada como referencia es `C:/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager`.
- Se consultaron también siete archivos de la [web publicada](https://horologist1.github.io/fantasy-manager/devkit/). Esto permite comparar esos componentes; no equivale a probar toda la aplicación desplegada.
- Backup previo: `backups/devkit-audit-20260910-034955/source-before.zip`, con manifiesto de hashes. Pruebas en una copia desechable, sin instalar mods, modificar partidas ni escribir en el devkit original.
- **163 pruebas existentes aprobadas**, ninguna omitida, utilizando los datos del juego actual mediante `FM_GAME_ROOT`.
- Reproducciones adicionales del editor y almacenamiento con DOM/handles simulados y comprobaciones con los **inspectores Python reales** de packs. Los controles positivos aceptan un personaje normal correctamente empaquetado y un override completo de una ruta existente.
- No se han modificado ni publicado el devkit o el juego. No se ha realizado una prueba visual completa del devkit ni una instalación nueva en Android durante esta revisión.

## Hallazgos por prioridad

### 1. Alta: un error de lectura puede acabar sobrescribiendo un archivo

En [fs.js](C:/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager-devkit-web/devkit_web/src/lib/fs.js:97), `readJSON` devuelve `null` tanto si falta el archivo como si contiene JSON inválido o falla su lectura. `mergeIntoFile`, en las líneas 15 y 26, interpreta ese resultado como un archivo vacío y escribe la nueva entrada.

**Reproducción:** un handle simulado devuelve un archivo existente con JSON truncado. Al guardar otro personaje se realiza una escritura y el resultado contiene únicamente el personaje nuevo. No se comunica el fallo de lectura. Este módulo coincide con el publicado.

El riesgo se amplifica porque `openExisting` permite abrir archivos originales y `editEntry` guarda por defecto sobre la misma ruta; no limita la escritura a archivos del mod ni crea backup. Eso contradice la protección prevista en el diseño original.

**Corrección propuesta:** distinguir ausencia, JSON inválido y error de acceso; bloquear la escritura si no se ha podido leer un archivo existente; validar también la estructura del contenedor; editar en un proyecto separado y exportar una copia. Si se mantiene la edición directa como opción avanzada, añadir copia recuperable y detectar cambios externos antes de reemplazar el archivo.

### 2. Alta para integrar Mods: falta un formato de salida compatible con el instalador

[app.js](C:/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager-devkit-web/devkit_web/src/app.js:364) descarga JSON individuales, sin reunir imágenes ni generar un ZIP. Con carpeta seleccionada escribe directamente en `game/data`.

| Salida / caso | Resultado con el importador actual |
| --- | --- |
| JSON descargado por el asistente de personaje | Rechazado como entrada: el selector espera ZIP o carpeta |
| El mismo personaje normal, en `data/workers/…json` y con `images/workers/<folder>/profile.png` | Aceptado, sin avisos |
| Personaje procedural o monstruo generado por su asistente, con imágenes | Rechazado por el modo de personajes; está fuera de su alcance |
| `data/items/items_audit.json`, nombre nuevo generado por el asistente | Rechazado como override: el destino no existe en el juego |
| Catálogo completo en `data/items/alchemy_ingredients.json` | Aceptado como override |

Los overrides actuales sustituyen **archivos completos por ruta exacta**. No son una fusión de entradas por nombre o ID. Cambiar solo el nombre de la descarga a uno existente sería peligroso: exportar una única entrada eliminaría del catálogo efectivo las restantes entradas de ese archivo.

**Corrección propuesta:** dos perfiles explícitos de exportación, ambos a ZIP: personajes admitidos más sus imágenes, y overrides sobre copias completas de archivos originales existentes. Cada perfil debe mostrar sus límites y validar con ellos. Interactions no está admitido por los overrides actuales; los asistentes de categorías no instalables pueden mantenerse para edición manual, identificando ese alcance.

### 3. Media: la validación no es una condición común de guardado

En [el editor](C:/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager-devkit-web/devkit_web/src/editors/_engine.js:120), Save llama a `onSave` aunque Review muestre errores. Las rutas de guardado de `app.js` no aplican una validación general final. El asistente sí pregunta si se quiere guardar pese a errores; el editor no utiliza esa misma protección.

**Reproducción:** Review muestra un error por ausencia de un campo requerido y el clic en Save ejecuta igualmente el guardado. Además, un personaje normal sin `folder` recibe cero errores y cero avisos del esquema local, pero el importador real lo rechaza.

**Corrección propuesta:** una única operación final que valide entrada, archivo y pack conforme al perfil elegido. Guardar un borrador incompleto puede permitirse dentro del proyecto; exportarlo como pack válido o escribirlo en el juego debe exigir que supere esas comprobaciones. No conviene endurecer todos los esquemas indiscriminadamente: algunas entradas del juego base son válidas para edición manual y están fuera del alcance del importador aditivo.

### 4. Media: la identidad de las entradas no está modelada por tipo

Workers usa siempre `name` como clave en [app.js](C:/Users/Usuario/Desktop/SNS/FantasyManager/fantasy-manager-devkit-web/devkit_web/src/app.js:58). Sin embargo, el esquema local reconoce plantillas procedurales de monstruos sin nombre, identificadas por `template_id`.

**Reproducción:** guardar consecutivamente las plantillas reales `monster_goblin` y `monster_orc` en memoria con esa clave deja solo `monster_orc`: ambos nombres son `undefined`. Al abrir el catálogo existente, la selección también compara etiquetas `(unnamed)` y siempre encuentra la primera entrada.

**Corrección propuesta:** definir identidad y etiqueta por tipo de entrada, mantener la identidad original durante una edición y distinguir reemplazo, renombrado y creación. No usar el texto de un botón como identidad interna.

**Límite adicional del juego:** el inspector de overrides también exige `name` a todos los workers. Rechaza una copia sin modificar del propio `data/workers/workers_monster_templates.json`. Si se quiere cubrir ese catálogo, debe alinearse ese contrato en el importador y añadirse su prueba; mientras tanto el devkit debe indicarlo como no compatible. No basta con corregir su selector.

### 5. Media: catálogos y publicación pueden quedar desalineados con el juego

| Fuente | Fecha declarada de generación | Items catalogados | Items actuales ausentes |
| --- | --- | ---: | ---: |
| Web publicada | 4 de julio de 2026 | 175 | 26 |
| Devkit local | 2 de septiembre de 2026 | 195 | 6 |
| Juego actual | Referencia de esta revisión | 201 | — |

Entre los seis ausentes de la copia local están todos los ingredientes nuevos de alquimia. La fecha corresponde al catálogo, no demuestra por sí sola cuándo se desplegó toda la web. También difieren `app.js`, el validador y el esquema de workers entre la web y la copia local.

La metadata solo declara `baked_at`; no identifica la versión/commit del juego. El flujo de publicación permite desplegar desde dos ramas y ejecuta los tests antes de regenerar los catálogos. No hay una prueba que tome un pack exportado y lo pase al importador real.

La lectura de catálogos desde la carpeta tampoco representa todos los datos efectivos: recorre solo archivos inmediatos de las categorías, sin los subdirectorios de reclutamiento/extensiones ni los packs gestionados fuera de la instalación. Tras guardar tampoco se reconstruye el catálogo para reflejar las nuevas entradas del mismo proyecto.

**Corrección propuesta:** vincular cada distribución al juego de referencia mediante versión y huella de datos; regenerar antes de verificar el artefacto final; probar los ZIP exportados con el importador real. Para las referencias durante la edición, combinar el catálogo base con los cambios del proyecto y actualizarlo cuando estos cambien.

## Arquitectura mínima recomendada

Conservar la aplicación estática y la separación actual entre esquemas, asistentes, editores y conversores. Añadir una capa pequeña de **proyecto de mod** entre los formularios y la escritura: modo de instalación, versión objetivo, archivos, imágenes y cambios pendientes. Los formularios modifican ese proyecto; una operación común lo valida y produce el ZIP.

Para overrides, importar la copia completa del archivo base al proyecto y preservar sus entradas y campos desconocidos. Para personajes, reunir los JSON y las imágenes requeridas. El manifiesto interno de instalación debe seguir siendo responsabilidad del juego; no hace falta exigir a los autores que fabriquen ese manifiesto.

La batería de integración debe comprobar generación → exportación → inspección real, con controles negativos para destino inexistente, imágenes ausentes, identidad duplicada, JSON inválido y perfiles incompatibles. La validación semántica de eventos —referencias, condiciones y continuidad— necesita además las comprobaciones del juego: que el instalador acepte el ZIP no garantiza que el evento sea jugable.

Orden propuesto: corregir escritura/identidad/validación; incorporar proyecto y exportación conforme a los dos modos existentes; alinear catálogos y publicación; verificar el paquete final. Este trabajo puede quedar acotado al devkit y sus contratos de importación, sin rediseñar el sistema de guardado.

## Evidencias reproducibles

En `backups/devkit-audit-20260910-034955/`:

- `source-before.zip` y `source-before.sha256.json`: copia previa del devkit.
- `devkit-tests.txt`: 163 pruebas existentes aprobadas.
- `devkit_web/architecture-probes.mjs` y `architecture-probes.json`: reproducciones de escritura, identidad, editor y validación.
- `importer-probes.py` y `importer-probes.json`: resultados con importadores reales y diferencia de catálogos.
- `importer-fixtures/`: archivos temporales usados por las pruebas; no instalados.
- `published/manifest.json`: comparación y hashes de los siete archivos consultados en la web.

Desde la raíz del juego se pueden repetir las reproducciones con `node backups/devkit-audit-20260910-034955/devkit_web/architecture-probes.mjs` y `python backups/devkit-audit-20260910-034955/importer-probes.py`. Sus aserciones documentan el comportamiento defectuoso observado en la copia previa; no deben interpretarse como pruebas de que esos fallos ya están corregidos.
