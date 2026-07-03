# Fantasy Manager — Revamp · Release Notes

**Qué es:** copia mejorada del juego en carpeta propia. Mismos JSON, mismos assets, tus saves cargan.

## Corregido
- ~35 bugs, incluidos 10 eventos de edificio rotos (crasheaban o nunca funcionaban), eventos guaranteed que bloqueaban todos los demás, y el bug de call-stack causante de diálogos mezclados y saves corruptos a largo plazo.
- Los checks de habilidad ya no pueden ser imposibles: mínimo de éxito según dificultad (10–50%).
- Los one-shots ya no se repiten; declinar un evento ahora lo pospone unos días en vez de perderlo para siempre.

## Completado (estaba a medias)
- El sabotaje del Governor ahora se recupera a los 3 días, como prometía.
- Los efectos temporales de interacciones expiran de verdad.
- Recruitment: filtros de worker, requisito de género, límites de aparición y efecto joy — todo funcionaba a medias o nada.
- Yvara: 2 mecánicas terminadas pero inaccesibles ("Send a worker for tutoring" y "Observe a session") ya están en su menú.
- Lanista: sin traits aleatorios indebidos, apuestas justas (y con guard de dinero), la mitad de grind en stages 1–3, ruta dominion viable, popup de introducción.
- Nueva worker única **Marigold** (existía como "Daisy" pero era inalcanzable), trait **Wounded** creado, y 4 eventos post-final nuevos para los endings dominion.

## Sonido (antes casi no había)
- La música ya no suena una vez y muere: bucle con pausas, y se recupera al cargar partida.
- Sonidos nuevos: click en botones, campanada al cambiar de día, acordes de éxito/fracaso en eventos.

## UI
- Lista de workers más alta (~4 filas más), confirmación al salir, botón "Coming Soon" retirado.
- Pantallas densas (workers, daily report) notablemente más fluidas.
- El toggle NSFW aplica al instante, sin reiniciar.
- Cerrada toda una clase de crashes al renombrar edificios o con textos con corchetes.

## Escritura
- ~100 textos reescritos: prosa corrupta por un buscar-y-reemplazar antiguo, resultados de tiendas idénticos entre opciones, frases repetidas de recruitment, clímax duplicados del arco Lanista, tutorial más ágil.

## Interno
- ~25 funciones/pantallas muertas eliminadas, lógica duplicada unificada, lint limpio, arranque verificado.
