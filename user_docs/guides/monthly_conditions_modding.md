# Monthly conditions / Condiciones mensuales

## Qué cambia

El calendario conserva sus meses de 28 días. Los tres primeros son tranquilos.
El cuarto introduce una tarjeta con efectos si el sistema está activado. El check
de la tarjeta cambia la preferencia para el próximo mes; volver a cambiarlo cancela
la solicitud. No reasigna trabajadores. La fecha subrayada de la taberna abre la tarjeta.

Las partidas anteriores permanecen neutrales durante su mes actual. El tutorial
usa los popups existentes y respeta su preferencia global y su registro de vistos.
El juego tiene rollback desactivado; el estado se reemplaza atómicamente para
mantener también un comportamiento coherente si un desarrollador lo habilita.

## Archivo y override

### Editarlas en el devkit

1. Abre un proyecto **JSON override (experimental)**.
2. En **Monthly conditions**, usa **Edit existing…** y elige `data/monthly_conditions/cards.json`.
3. Edita una tarjeta o usa **Monthly condition** para añadir una. Abre después la nueva tarjeta para configurar `effects`.
4. Cada efecto indica `type`, `value` y los filtros `buildings`, `professions` y `skills`. Los filtros rellenos deben coincidir a la vez. `earnings: 1.10` significa +10 %, no diez monedas.
5. Usa **Review & export ZIP**. Se conserva el catálogo completo al añadir o editar tarjetas; instalarlo sustituye el archivo completo.

El editor valida un máximo de tres efectos: habilidades de -10 a +10, e ingresos
de 0.90 a 1.15. Los efectos de habilidad necesitan habilidades explícitas; los de
ingresos no admiten filtro de habilidad. Todos necesitan edificio o profesión.
`quiet_month` debe conservarse sin efectos. La descripción admite 500 caracteres.
El campo `image` es opcional y referencia un recurso existente del juego: este
override no instala ilustraciones nuevas. El check `nsfw` mantiene el filtrado de
contenido del juego. No incluyas estas cartas en un pack de personajes.

`game/data/monthly_conditions/cards.json` es un array JSON. Se admite como override
de archivo completo mediante el importador existente de Mods, en PC y en la ruta
de importación Android. Esto no equivale a una prueba física de Android.

Estructura del ZIP:

```text
data/
  monthly_conditions/
    cards.json
```

Instalar desde Mods con la opción de override. Reiniciar el juego para montar el
archivo, como cualquier otro override. El último override instalado para esa ruta
tiene prioridad. Conservar las tarjetas existentes al añadir otras: no se fusionan
arrays entre packs.

Una tarjeta activa conserva su copia validada dentro del save hasta finalizar el
mes, aunque cambie el catálogo o se desinstale su pack. Las nuevas selecciones usan
el catálogo montado. Nunca se vuelve a sortear por cargar o cambiar el check.

```json
[
  {
    "id": "quiet_month",
    "name": "Quiet month",
    "description": "No special conditions this month.",
    "weight": 1,
    "effects": []
  },
  {
    "id": "local_food_fair",
    "name": "Local food fair",
    "description": "Local kitchens welcome a busy month.",
    "weight": 1,
    "nsfw": false,
    "image": "",
    "effects": [
      {
        "type": "skill",
        "value": 5,
        "buildings": ["restaurant"],
        "professions": ["cook"],
        "skills": ["Service"]
      },
      {
        "type": "earnings",
        "value": 1.1,
        "buildings": ["restaurant"],
        "professions": ["cook"]
      }
    ]
  }
]
```

**Cooking no es un identificador de habilidad de este juego:** los cocineros usan
`Service`. Revisar los catálogos reales antes de escribir efectos.

## Contrato de datos

- `id`, `name`, `description`: cadenas no vacías. Identificadores únicos.
- `weight`: número finito entre 0 y 10000. Cero excluye la tarjeta del sorteo.
- `effects`: máximo tres. `quiet_month` no admite efectos y se añade como fallback
  seguro si falta.
- `type`: únicamente `skill` o `earnings`; no hay expresiones ejecutables.
- `value`: para habilidad, de -10 a +10; para ingresos, de 0.90 a 1.15.
- `buildings`, `professions`, `skills`: arrays de identificadores exactos. Dentro
  de cada array se acepta cualquiera; entre arrays se exige cumplir todos.
- Una actividad debe limitarse por edificio o profesión. Los efectos `skill`
  requieren habilidades explícitas. `earnings` no acepta selector de habilidades.
- Los efectos coincidentes se combinan, con límites agregados de -10/+10 por
  habilidad y 0.90/1.15 para ingresos. Evitar efectos solapados: sus líneas describen
  cada entrada, mientras el informe muestra el modificador agregado aplicado.
- `image`: opcional, vacío o ruta existente bajo `images/`, PNG/JPEG/WebP.
  Ausente o no cargable: se omite. **El importador de overrides sigue siendo de
  JSON; no instala imágenes nuevas.** Para distribuir ilustraciones adicionales
  se necesita un mecanismo de assets compatible o integrarlas en el juego.
- `nsfw`: booleano opcional. Las tarjetas marcadas no se seleccionan en SFW.
  Si una tarjeta ya activa está marcada y se cambia a SFW, su nombre, descripción
  e imagen se ocultan; se mantienen los modificadores numéricos del mes.

Las descripciones numéricas se generan desde los efectos, no desde prosa del autor.
Los nombres de edificios/profesiones se resuelven desde los catálogos del juego. No se interpretan etiquetas de texto del mod.

El importador valida estructura y límites. El juego valida además referencias
contra los edificios, profesiones y habilidades cargados. Las entradas inválidas
se omiten con diagnóstico en el log. Un catálogo inutilizable produce Mes tranquilo.

## Orden de cálculo

Habilidad con traits → modificador mensual por habilidad → media de habilidades
de la story → penalización de dificultad y reglas existentes → modificadores de
story, especialización, personal y política → límites de la tirada.

No se cambia lo aprendido ni se limita artificialmente a 100 una habilidad que
ya recibía bonos; el umbral final mantiene su límite existente.

Ingresos de story → traits/Business Acumen → personal del edificio → dificultad
→ protección existente de pago válido → multiplicador mensual solo si es positivo
→ reglas existentes de pérdidas y contabilización. No modifica cero, pérdidas,
compras, ventas, loot ni recompensas fijas de eventos.

El motor avanza primero la fecha y después resuelve las actividades de esa nueva
fecha. La condición se sincroniza en ese mismo punto. Se conserva esta semántica:
el informe de día 1 usa la condición nueva, el informe de día 28 usa la anterior.

La estimación de éxito de trabajos y Auto-fill consideran los modificadores de
habilidad mensuales. Auto-fill sigue siendo una heurística de habilidades, no un
optimizador de beneficio monetario. No se ejecuta al cambiar de mes.

## Auditoría

Pruebas: `tests/test_monthly_conditions.py`, `tests/test_monthly_runtime.py` y
`tests/test_json_overrides.py`. El test de motor crea una copia aislada, captura
tarjeta activa/desactivada/pendiente, usa controles reales y guarda/carga con el
sistema canónico. Los recursos originales no se modifican durante las pruebas.
