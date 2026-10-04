# Fantasy Manager - User Docs Bundle

Esta carpeta se incluye en el build para usuarios/modders.

## Contenido

- `guides/modding_guide.md`: copia completa.
- `guides/game_guide_full.md`: copia completa.
- `guides/image_selection_guide.md`: copia completa.
- `guides/field_guide.html`: guía interactiva (mecánicas, fórmulas e imágenes), se abre en el navegador. Se genera con `python tools/field_guide/build_field_guide.py`; la versión online está en https://horologist1.github.io/fantasy-manager/guide/
- `templates/`: plantillas JSON listas para copiar y editar.

## Nota

- La carpeta `docs/` principal se excluye del build de distribucion.
- Este bundle esta pensado como version "publica/portable" de referencia.
- Cuando se actualicen docs base, conviene sincronizar tambien estos archivos.
