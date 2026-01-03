# Cálculo de Usos Necesarios para Subir de Nivel

## Sistema de Nivelado

Para subir de nivel N a N+1, se necesitan **N usos** de esa habilidad.

**Excepción:** De nivel 0 a 1, se necesita **1 uso**.

---

## Ejemplo: Subir Sex de 42 a 100

### Cálculo paso a paso:

- Nivel 42 → 43: **42 usos**
- Nivel 43 → 44: **43 usos**
- Nivel 44 → 45: **44 usos**
- ...
- Nivel 98 → 99: **98 usos**
- Nivel 99 → 100: **99 usos**

### Fórmula:

Suma de 42 a 99 (inclusive):
```
Suma = 42 + 43 + 44 + ... + 99
```

Usando la fórmula de suma aritmética:
```
Suma = (cantidad de términos) × (primer término + último término) / 2
Suma = (99 - 42 + 1) × (42 + 99) / 2
Suma = 58 × 141 / 2
Suma = 58 × 70.5
Suma = 4,089
```

O usando la fórmula de suma de números consecutivos:
```
Suma de 1 a n = n × (n + 1) / 2
Suma de 1 a 99 = 99 × 100 / 2 = 4,950
Suma de 1 a 41 = 41 × 42 / 2 = 861
Suma de 42 a 99 = 4,950 - 861 = 4,089
```

---

## Resultado

**Para subir Sex de nivel 42 a nivel 100, se necesitan: 4,089 usos totales**

---

## Fórmula General

Para subir de nivel A a nivel B:
```
Total usos = Suma de A a (B-1)
Total usos = (B-1) × B / 2 - (A-1) × A / 2
Total usos = (B × (B-1) - A × (A-1)) / 2
```

**Ejemplo:** De 42 a 100:
```
Total = (100 × 99 - 42 × 41) / 2
Total = (9,900 - 1,722) / 2
Total = 8,178 / 2
Total = 4,089
```

---

## Tabla de Referencia Rápida

| Nivel Inicial | Nivel Final | Usos Totales |
|---------------|-------------|--------------|
| 0 | 10 | 45 |
| 0 | 20 | 190 |
| 0 | 50 | 1,225 |
| 0 | 100 | 4,950 |
| 10 | 20 | 145 |
| 20 | 50 | 1,035 |
| 42 | 100 | **4,089** |
| 50 | 100 | 3,725 |
| 75 | 100 | 2,175 |

