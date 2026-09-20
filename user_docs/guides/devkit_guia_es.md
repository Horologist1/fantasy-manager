# Guía rápida del devkit

El devkit trabaja sobre un proyecto de mod separado. Los archivos originales del
juego se utilizan como referencia y no se sobrescriben desde los editores.

La referencia incluida indica arriba la versión del juego. No necesitas instalar
el juego en el ordenador ni abrir un APK para crear un pack con esa referencia.

## Crear un pack de personajes

1. Selecciona **Character pack** y escribe el nombre del mod.
2. Abre **Unique Worker** y completa el asistente. El identificador de la carpeta
   de imágenes debe ser sencillo, por ejemplo `mira_storm`: letras, números,
   guiones y guiones bajos, con un máximo de 80 caracteres.
3. Pulsa **Save to project**. Luego abre **Manage character images**.
4. **Choose portrait** coloca la imagen elegida en la carpeta correcta y la nombra
   `profile.png`, `profile.jpg` o `profile.webp`. **Add other images** añade las
   restantes conservando sus nombres. Cada carpeta necesita un retrato incluido
   en el pack, aunque ya exista en tu instalación del juego.
5. Repite el proceso para otros personajes. Sus nombres deben ser únicos dentro
   del pack. Se admiten PNG, JPG y WebP; cada imagen puede ocupar hasta 32 MB.
6. Guarda una copia editable con **Save draft**. Después abre **Review & export
   ZIP**, corrige los errores y pulsa **Export ZIP**.

Este modo admite personajes normales. Las plantillas procedurales, los monstruos,
los eventos y los traits nuevos requieren otro proyecto compatible. Si añades un
JSON que contiene campos especiales, el editor muestra cuáles no se importarán y
permite retirarlos del borrador con confirmación. Revisa las consecuencias de
eliminar requisitos de reclutamiento u otras reglas.

## Ejemplo de override: cambiar el precio de Ironroot

1. Crea un proyecto vacío y elige **JSON override (experimental)**.
2. En Items, pulsa **Edit existing…** y selecciona
   `data/items/alchemy_ingredients.json`.
3. Elige Ironroot, cambia su precio y pulsa **Save draft to project**.
4. Guarda el borrador y revisa/exporta el ZIP.

El proyecto conserva el catálogo completo: cambiar Ironroot no elimina los demás
ingredientes. El override sustituye el archivo completo por su ruta exacta; no es
una fusión automática de entradas entre mods. Un asistente también puede añadir
una entrada nueva a un archivo existente, pero no crear una ruta nueva para el
importador de overrides.

Para modificar una historia diaria procedente de una extensión, elige su archivo
en `data/buildings/daily_story_extensions`. Esa extensión puede prevalecer sobre
la historia definida en el archivo del edificio.

## Instalar en PC o Android

1. Copia o descarga el ZIP exportado en el dispositivo, sin descomprimirlo.
2. Abre **Mods → Install mods** en el menú principal del juego.
3. Para personajes deja la casilla de override apagada. Para overrides, actívala,
   lee el aviso y selecciona el ZIP.
4. Revisa la vista previa, instala y reinicia el juego.
5. Para overrides, empieza una partida nueva y mantén los mismos packs durante
   esa partida. Para retirarlos usa **Uninstall** y vuelve a reiniciar.

Android lee el ZIP mediante su selector y guarda el contenido admitido en el
almacenamiento gestionado por el juego. No hay que abrir, modificar ni volver a
empaquetar el APK. Sí necesitas un APK con el importador de Mods correspondiente.
Los overrides de las plantillas de monstruos sin nombre y de las variantes
SFW/NSFW de Kar/Kara necesitan la corrección del juego incluida en esta
actualización; los APK anteriores pueden rechazarlos.

Si dos overrides cambian el mismo archivo, prevalece el instalado después. Quitar
un mod no deshace lo que ya haya quedado guardado en una partida.

## Borradores, referencias y límites

- **Save draft** descarga un `.fmproject.json` con los JSON y las imágenes para
  seguir trabajando. **Open draft** vuelve a abrirlo. Guarda primero los cambios
  del formulario en el proyecto. El ZIP instalable no sustituye a ese borrador.
- No dependas de cerrar y volver a abrir el navegador: conserva el archivo de
  borrador. El aviso al salir no sustituye una copia de seguridad.
- **Read PC game reference** lee una instalación de PC sin modificarla. Se usa
  desde un proyecto vacío; no lee los mods gestionados junto a las saves ni un APK.
- Los borradores deben coincidir con su referencia. Para una versión nueva del
  juego, traslada tus cambios a un proyecto nuevo basado en sus catálogos.
- **Remove from project** retira ese archivo del pack; no borra el original.
  Renombrar un identificador tampoco actualiza automáticamente otros eventos o
  condiciones que lo usen.
- El devkit admite hasta 1.000 personajes, 10.000 archivos y 128 MB de contenido
  sin comprimir. Cada JSON debe quedar por debajo de 4 MB. Divide los packs grandes.
- **Manual JSON files (PC only)** conserva la edición avanzada para instalación
  a mano. Haz backup antes de copiar su contenido al juego. Ese ZIP no está
  soportado por el importador del menú Mods, y Uninstall no retira archivos
  copiados manualmente.

El botón **User guide** contiene la guía completa en inglés, también disponible
en [Devkit user guide](devkit_user_guide.md). Las comprobaciones del devkit y del
instalador validan el formato; prueba los eventos y sus ramas de fallo en una
partida nueva antes de compartir un mod.
