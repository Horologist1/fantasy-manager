# División por género de las daily stories sexuales

Estado: **aplicada**, con test de regresión. Documentada aquí porque es el único
cambio **estructural** del pase; todo lo demás fue texto.

## Por qué

El registro explícito (posición 3) exige nombrar anatomía. Una story sin
`worker_gender_requirement` no sabe qué cuerpos hay en la habitación, así que su
prosa está obligada a escribir *alrededor* del acto. Ése era exactamente el caso
de las stories que seguían sin una sola palabra explícita: `prostitute_vanilla_client`
(*"Client paid for Sex"*), `prostitute_oral_client`, `pleasure_servant_noble_client`…

El patrón ya existía en los datos. `prostitute_anal_client_male` y
`prostitute_anal_client_female` son **un acto dividido en dos stories, peso 3 cada
una**. Lo mismo `hand` y `homo`. Nunca se dividieron `vanilla`, `oral` ni las
`libido20`, y son precisamente las que se quedaron sin poder describir nada.

## Qué se ha hecho

18 stories genéricas → 36 variantes `_male` / `_female`. Cada variante conserva
**el peso original**, más skills, earnings, consequences, imágenes, traits y
modificadores. Sólo cambia el `id`, el filtro de género y el de orientación.

| | antes | después |
| --- | ---: | ---: |
| Stories en `building_types.json` | 174 | 192 |
| Stories sexuales sin género | 18 | **0** |
| Stories sexuales sin vocabulario explícito | 26 | **3** |

Las 3 restantes son las `VIP / Special`, que dejan el acto sin nombrar por
decisión tuya: el diseño lo deja a la imaginación del jugador.

## Por qué la distribución no cambia

`event_daily_exec.rpy:517` (y `:912` para la ruta de manager) filtra
`worker_gender_requirement` de forma estricta antes de la selección ponderada:

```python
gender_requirement = story.get("worker_gender_requirement")
if gender_requirement is not None and gender_requirement != worker_gender:
    continue
```

Para un trabajador concreto, exactamente **una** de las dos variantes sobrevive
al filtro, y lo hace con el peso que tenía la original. La probabilidad de que
ese trabajador vea ese acto es idéntica a la de antes.

La condición crítica es que **la original desaparezca**. Si se mantuviera
elegible junto a sus gemelas sumaría su peso otra vez y sesgaría el pool — que
es el fallo que la spec de GPT nombra explícitamente («No duplicar una story
compartida manteniendo también su original elegible»).

`tests/test_daily_story_gender_variants.py` fija las cuatro condiciones:

1. Ninguna de las 18 originales sigue en el pool.
2. Las 36 variantes existen.
3. Las gemelas de un mismo split conservan peso, skills, earnings, consequences,
   imágenes y traits idénticos.
4. Cada perfil de trabajador (masculino, femenino, Gay, Lesbian) empareja con
   **exactamente una** variante de cada split, nunca cero ni dos.

## Efectos colaterales resueltos

- `tools/audit_management_balance.py` citaba `prostitute_vanilla_client` como
  ejemplo. Actualizado a las dos variantes.
- `devkit_web/dist/` empaqueta una copia de `building_types.json` y estaba
  desfasado ya antes de esto. Reconstruido con `npm run bake` + `build:offline`;
  187 tests del devkit en verde.
- Las variantes conservan el `story_image` original, así que **no hace falta arte
  nuevo**: ambas reutilizan el asset que ya existía. La resolución real de imagen
  depende de la carpeta del trabajador, no del id de la story.

## Una etiqueta corregida de paso

`prostitute_oral_client` y `ea_prostitute_oral_client` reportaban *"Client paid
for a Blowjob"* también cuando el trabajador es masculino — en cuyo caso la
clienta es mujer y el acto no es ése. Renombrado a *"Client paid for Oral"* en
las variantes `_male`, siguiendo la convención que el par `hand` ya usaba
(*Fingering* para la variante masculina, *Handjob* para la femenina).

## Lo que NO se ha tocado

Pesos, fórmulas de ingresos, consecuencias, dificultad y pools siguen exactamente
igual. Este pase no rebalancea nada, y la diferencia de precio entre Prostitute y
Expert attendant sigue abierta para la pasada de balance.
