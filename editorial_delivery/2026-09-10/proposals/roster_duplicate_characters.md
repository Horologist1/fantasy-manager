# Personajes duplicados en el roster

Estado: **texto resuelto, mecánica abierta.** No requiere acción inmediata.

Este es el hallazgo con conexión más directa a una review concreta:

> «characters repeat, you see same looking ones multiplied many times which
> ruins immersion» — yodyna
>
> «after a while some of them can start to feel a little interchangeable»
> — Adamsomebody

## Lo que pasa

`worker_loader.rpy` filtra así:

```python
if not persistent.nsfw_enabled and content_object_is_restricted(worker):
    continue
```

Es decir: en modo SFW se descartan los workers NSFW, y **en modo NSFW no se
descarta nada**. Los dos rosters se cargan a la vez.

| | Roster visible |
| --- | ---: |
| Modo SFW | 12 workers únicos |
| Modo NSFW | **23** (los 12 SFW + los 11 NSFW) |

Y los ficheros `workers_sfw_unique.json` / `workers_nsfw_unique.json` contienen,
en buena medida, **las mismas personas dos veces**. Tres parejas son idénticas
en traits, skills y género:

| Pareja | Traits compartidos |
| --- | --- |
| **Fern / Violet** | Clever, Elegant, Graceful, Human, Sexy Air |
| **Primrose / Rose** | Clever, Elegant, Elf, Graceful, Sexy Air |
| **Jasmine / Iris** | Charismatic, Confident, Exotic, Human, Optimist |

Un jugador en modo NSFW contrata a Rose y a Primrose y obtiene, mecánicamente,
al mismo personaje dos veces con dos nombres.

## Lo que se ha hecho en este pase (texto)

Cuatro parejas compartían además **la presentación de reclutamiento palabra por
palabra** — lo primero que el jugador lee sobre un personaje con nombre propio:

- Aspen / Cedar
- Florian / Laurel
- Rose / Primrose
- Iris / Jasmine

Peor aún: el texto compartido a menudo describía **al otro**. Laurel, cuya ficha
dice *«never met a room he couldn't work. Bright, fast-talking, impossible to
fluster»*, se presentaba con el texto de Florian: *«a somewhat effeminate young
man… studied elegance»*.

Cada uno de los 24 tiene ahora su propia presentación, escrita **desde su propia
descripción de ficha**, que ya era distinta y estaba bien escrita. Verificable:

```
$ python scratchpad/recruit_dupes.py
DESCRIPCIONES compartidas por varios personajes: 0 grupos
MENSAJES de opcion compartidos: 0 grupos
personajes con introduccion propia: 24 de 24
```

Ninguna stat, trait, efecto ni opción se ha tocado.

**Nota importante:** Aspen/Cedar y Florian/Laurel **sí** tienen traits distintos
(Aspen es Aggressive + Assassin; Cedar es Clever + Optimist). En esos dos casos
el texto era el único problema y queda resuelto del todo.

## Lo que queda como decisión tuya

Las tres parejas mecánicamente idénticas. Ahora se leen distinto, pero siguen
jugándose igual. Opciones, sin recomendación firme porque es diseño y balance:

1. **Diferenciar traits/skills.** Que Rose y Primrose diverjan en dos o tres
   traits. Es el arreglo real, y cambia el balance del roster.
2. **Excluirse mutuamente.** Marcar cada pareja de modo que, si aparece una, la
   otra no entre en el pool. Conserva el balance y elimina el clon, a costa de
   reducir el roster NSFW de 23 a 20.
3. **Dejarlo.** Son las contrapartes SFW/NSFW del mismo arquetipo y quizá esa era
   la intención; con presentaciones distintas, el problema se reduce bastante.

**No se ha tocado nada de esto.** Cambiar traits o el pool altera la distribución
y el balance, que está fuera del alcance de un pase editorial — igual que la
diferencia de precio de Expert attendant, que ya quedó apuntada para la pasada de
balance.
