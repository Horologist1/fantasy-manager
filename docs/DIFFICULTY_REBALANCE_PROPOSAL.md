# Rebalanceo de dificultad – Fórmulas y tiers

## Objetivo
- **Normal**: el worker gana ~2× su coste diario con un éxito típico.
- **VIP**: ~3× coste diario.
- **Premium**: ~4–5× coste diario.
- Mantener dependencia de **skill** y **trait** (el bonus de trait se sigue aplicando en código).

## Variables en las fórmulas
- `skill`: skill efectiva del worker en la prueba.
- `level`: nivel del worker.
- `roll`: resultado del d100 (1–100). Útil en **failure** para que un fallo por poco (roll bajo) penalice menos que un fallo clamoroso (roll alto).

## Fórmulas estándar (tier **normal**)
| Resultado        | Fórmula           | Ejemplo (skill=50) |
|-----------------|-------------------|--------------------|
| success         | 200 + skill * 2   | 300                |
| mediocre        | 100 + skill       | 150                |
| critical_success| 200 + skill * 4   | 400                |
| failure         | -(100 + roll)     | -199 si roll=99    |

Así, un fallo con 99 resta 199; con 1 resta 101. El modificador de trait en éxito/crítico se suma después en código.

## Escalado VIP (~1.5× base)
| Resultado        | Fórmula           |
|-----------------|-------------------|
| success         | 300 + skill * 3   |
| mediocre        | 150 + skill       |
| critical_success| 300 + skill * 6   |
| failure         | -(150 + roll)     |

## Escalado Premium (~2× base, 4–5× coste)
| Resultado        | Fórmula           |
|-----------------|-------------------|
| success         | 400 + skill * 4   |
| mediocre        | 200 + skill * 2   |
| critical_success| 400 + skill * 8   |
| failure         | -(200 + roll)     |

## Clasificación por profesión / tipo de evento

### Tier NORMAL
- Prostitute: vanilla client, anal (ambos géneros), oral, hand (ambos).
- Stripper: regular client.
- Service (brothel y restaurant): atención básica.
- Manager (brothel, restaurant, tavern): gestión.
- Cook: cocinar para mesa normal (cook_story1).
- Waiter / Service restaurant: servicio a mesa.
- Guards (castillo): patrol (patrulla).
- Chamberlain: gestión castillo.
- Adventurer: contratos estándar (si hay solo uno, normal).
- Dealer (casino): croupier estándar.
- Guard casino: historia “Caught Disruptive Patron”.
- Entertainer tavern: historia estándar (no VIP).

### Tier VIP
- Prostitute: VIP client (Special), BDSM client.
- Pleasure servant: noble client.
- Stripper: private dance (lap dance), VIP client.
- Cook restaurant: “Cooked for a VIP” (cook_story2).
- Entertainer tavern: “Entertained VIPs”.
- Guards (castillo): capture intruder, capture criminal.
- Adventurer: monster hunting (alto riesgo/recompensa).
- Guard casino: “Caught Cheating Gambler”.

### Tier PREMIUM
- Prostitute: extreme client.

## Cambios en código (event_daily_exec.rpy)
- Se añade `roll` al `env` de `eval()` para que la fórmula de failure pueda usar `-(100 + roll)` (y variantes VIP/Premium).
- Se eliminan los multiplicadores 0.65 / 0.75 / ×2 sobre earnings; las fórmulas del JSON son el valor final (más el bonus de trait que ya aplica el código).

## Cambios aplicados
- **event_daily_exec.rpy**: Se añade `roll` al `env` de `eval()` y se eliminan los multiplicadores (0.65, 0.75, ×2 en fallo). El resultado del JSON es el valor final, más el bonus de trait que ya aplica el código.
- **building_types.json**: Todas las historias con earnings usan ya las fórmulas por tier (normal / VIP / premium) y failure con `-(100 + roll)`, `-(150 + roll)` o `-(200 + roll)`.

## Notas
- Rest, Prisoner y profesiones sin earnings no se tocan.
- Si en el futuro se añaden más eventos, usar la misma tabla de fórmulas según tier (normal / VIP / premium).
- **Adventurer story3** (encuentro peligroso inesperado) está en tier **premium** por el alto riesgo.
- **Prostitute group**, **Courtesan** (soiree, seduction, VIP chamber), **Monster tamer** (combat, seduction), **Guard casino** (atrapar tramposo) están en tier **VIP**.
