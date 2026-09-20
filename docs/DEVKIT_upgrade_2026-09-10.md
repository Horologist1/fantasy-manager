# Devkit 0.2 — implementación y verificación

## Resultado

Se ha incorporado `devkit_web/` a la copia actual del juego, conservando la versión
previa del otro worktree. Los esquemas, asistentes y editores existentes siguen
siendo la base. La nueva capa de proyecto separa la edición del almacenamiento
del juego y genera packs comprobados contra sus importadores.

La entrega incluye:

- Proyectos de personajes, overrides experimentales y edición manual avanzada de
  PC, con alcance diferenciado en la interfaz.
- Borradores `.fmproject.json` que conservan JSON e imágenes, con reapertura y
  comprobación de la referencia del juego.
- Exportación ZIP de personajes con retratos obligatorios y de overrides con
  archivos completos en rutas originales existentes.
- Edición de copias del catálogo completo, preservando otras entradas y campos
  desconocidos. La selección opcional de una instalación pide acceso de lectura.
- Validación final de archivos, entradas, imágenes, nombres y límites antes de
  exportar. Un borrador incompleto no se presenta como un pack válido.
- Errores de lectura, JSON inválido, claves repetidas y números no finitos que
  detienen la operación; no se convierten en un archivo vacío para sobrescribirlo.
- Identidades diferenciadas para plantillas sin nombre y variantes SFW/NSFW.
  Renombrar una entrada editada conserva su identidad original para reemplazarla
  y no permite pisar otra entrada.
- Actualización inmediata de las referencias con los cambios del proyecto y
  catálogo completo generado desde el juego actual, con versión y hashes.
- Guía integrada en web y HTML offline, documentación completa en inglés y guía
  rápida en español. La documentación inglesa se genera de la misma fuente que
  la ayuda de la aplicación.
- Flujo de GitHub Pages preparado para main: generar catálogos y documentación,
  ejecutar pruebas con el importador real, compilar y publicar el resultado.
- Ajustes de interfaz para pantallas estrechas y protección frente a cancelar,
  reintentar un guardado fallido o terminar una lectura después de cambiar de
  proyecto. El servidor local también rechaza escapes de directorio y URLs mal
  formadas.

## Cambio acotado en el juego

En `game/python-packages/fm_mods/packs.py`, la identidad de un worker en un
override contempla `template_id` para las plantillas y `name` más el indicador
SFW/NSFW para los personajes. Esto permite reemplazar los catálogos originales
de monstruos y Kar/Kara sin confundir entradas válidas ni relajar la detección
de duplicados dentro de una misma variante.

El importador aditivo continúa exigiendo nombres únicos en todo el pack y solo
admite personajes normales. No se cambia el formato de los packs instalados ni
el de los guardados. No se han modificado eventos o scripts de guardado como
parte de esta actualización.

## Verificación terminada

- **187 pruebas del devkit aprobadas**, ninguna omitida: esquemas, catálogos,
  asistentes, editores, errores de lectura, identidades, borradores con imágenes,
  ZIP, protección de rutas y ejecución del bundle offline.
- Los flujos de interfaz comprueban crear un personaje, bloquear la exportación
  por falta de retrato, añadir imágenes, guardar/reabrir un borrador, conservar el
  proyecto al cancelar y corregir/reintentar un guardado fallido. El ejemplo de
  Ironroot confirma que los demás ingredientes permanecen iguales.
- El ZIP de personajes se inspecciona, instala y monta con el código Python real
  del juego en almacenamiento temporal, comprobando sus imágenes. Se hace lo
  mismo con un ZIP que incluye los **62 catálogos actuales admitidos para
  overrides**, conservando los bytes de todos ellos tras la instalación.
- **319 pruebas del juego y 463 subtests aprobados**, con
  `RENPY_RUNTIME_REQUIRED=1`, incluyendo las comprobaciones existentes que exigen
  el motor para guardados. Los archivos de pruebas y saves temporales están
  separados de los del usuario.
- Revisión visual de la página principal en el navegador del equipo; apertura
  del HTML compilado y de su guía mediante un servidor local. La ejecución del
  script integrado y la ausencia de imports relativos sin resolver se comprueban
  también mediante las pruebas del bundle.
- La huella del catálogo se contrasta con todos los archivos actuales del juego,
  incluyendo los seis ingredientes de alquimia.
- Los hashes de los **89 archivos de la versión previa** del otro worktree siguen
  intactos.

Durante el desarrollo, las pruebas detectaron y ayudaron a corregir el fixture
del encabezado antiguo, el acceso a un evento DOM después de finalizar su
callback y las diferencias de identidad de las variantes SFW/NSFW. Los resultados
anteriores son los de las ejecuciones finales, no los intentos intermedios.

## Archivos de entrega y backups

- `devkit_web/dist/FantasyManagerDevkit.html`: aplicación offline, aproximadamente
  2,8 MiB, con referencias y guía incluidas.
- `devkit_web/USER_GUIDE.md` y `user_docs/guides/devkit_user_guide.md`: guía completa.
- `user_docs/guides/devkit_guia_es.md`: guía rápida en español.
- `devkit_web/README.md`: arquitectura, desarrollo, comprobaciones y límites.
- `backups/devkit-upgrade-20260910-040508/before.zip`: copia previa.
- `backups/devkit-upgrade-20260910-040508/delivery.zip`: archivos de la entrega.
- `backups/devkit-upgrade-20260910-040508/devkit-check.txt`: pruebas y compilación.
- `backups/devkit-upgrade-20260910-040508/pytest-full.txt`: batería del juego.
- `backups/devkit-upgrade-20260910-040508/delivery-report.json`: resumen y hash del
  HTML compilado.

Para repetir la comprobación del devkit: `npm --prefix devkit_web run check`.
La guía se regenera con `npm --prefix devkit_web run docs`.

## Estado de publicación y límites

La entrega está aplicada y compilada **localmente**. No se ha publicado una nueva
versión en GitHub Pages, realizado un push/commit ni compilado/instalado otro APK
en este turno. El HTML offline permite utilizar ya el devkit actualizado.

Los APK anteriores pueden rechazar overrides de las plantillas sin nombre y de
las variantes Kar/Kara; necesitan la corrección del importador incluida en el
proyecto. El formato de los packs de personajes normales y de los demás
overrides se mantiene.

No se ha repetido una prueba física en Android ni se ha comprobado visualmente
en un móvil esta interfaz del devkit. Sus packs se verifican contra el importador
compartido del juego. Pasar esa validación no demuestra todos los resultados de
un evento; los autores deben probar su contenido en una partida nueva antes de
distribuirlo. La resolución automática de dependencias entre mods y la migración
de partidas existentes siguen fuera del alcance.
