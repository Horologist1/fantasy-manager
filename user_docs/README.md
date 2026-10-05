# Fantasy Manager - User Docs Bundle

Esta carpeta se incluye en el build para usuarios/modders.

## Contenido

- `guides/character_pack_quickstart.md`: guía rápida (5 pasos) para crear un pack de personaje.
- `guides/character_pack_guide.md`: guía completa de packs de personaje (personaje, traits, eventos, reclutamiento, historias diarias; instalación con el importador o arrastrando la carpeta).
- `guides/modding_guide.md`: copia completa.
- `guides/game_guide_full.md`: copia completa.
- `guides/image_selection_guide.md`: copia completa.
- `guides/field_guide.html`: guía interactiva (mecánicas, fórmulas e imágenes), se abre en el navegador. Fuente en `devkit_web/field_guide/` (`npm run guide` desde `devkit_web/`); la versión online está en https://horologist1.github.io/fantasy-manager/guide/
- `templates/`: plantillas JSON listas para copiar y editar. Incluye `templates/character_pack/`, un pack de ejemplo completo (Mira) que pasa el importador.

## Nota

- La carpeta `docs/` principal se excluye del build de distribucion.
- Este bundle esta pensado como version "publica/portable" de referencia.
- Cuando se actualicen docs base, conviene sincronizar tambien estos archivos.
