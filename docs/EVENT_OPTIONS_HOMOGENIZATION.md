# Homogenización de opciones de eventos

## Resumen

Se ha homogeneizado el formato de las opciones en todos los archivos de eventos para usar un estilo consistente basado en **Potential**, **Risk**, **Cost**, **Gain** y **Loss** (siempre con mayúscula inicial).

## Formato estándar

- **(Potential: X)** — cuando la opción ofrece beneficios si tiene éxito
- **(Risk: X)** — cuando existe riesgo de consecuencias negativas
- **(Cost: X)** — cuando hay un coste conocido (ej. dinero)
- **(Gain: X)** — cuando hay ganancia garantizada
- **(Loss: X)** — cuando hay pérdida conocida
- **(Neutral)** — cuando la opción no tiene efecto significativo o es de rechazo/pasar

Para opciones con requisitos de habilidad:
- **(Requires Skill X+; Potential: Y; Risk: Z)**

## Archivos modificados

### events_seasonal.json
- Convertido de números concretos ("+300 gold") a formato descriptivo ("Potential: Gold")
- Porcentajes ("65% chance: +1500 gold") → "(Risk: lesser reward; Potential: Gold)"

### events_building.json
- Capitalización de risk→Risk, potential→Potential, cost→Cost, gain→Gain, loss→Loss
- "(costs and reputation may vary)" → "(Risk: Money, Reputation; Potential: Reputation)"
- Consistencia en puntuación (punto antes del paréntesis)

### events_common.json
- "(risk/reward)" → "(Risk: Money, Reputation; Potential: Money, Reputation)"
- Opciones sin paréntesis actualizadas con formato estándar

### events_shops.json
- Añadido formato a opciones que solo tenían "Requires X" o descripción
- "(Requires Charm 70+; Potential: Reputation)"
- "(Cost: Money; Gain: Reputation)" para pagos
- "(Neutral)" para declinar/rechazar

### events_special.json / events_workers_aelis.json
- Aplicado formato inicial en opciones principales

## Notas

- Las opciones con **Requires** mantienen ese texto cuando hay requisito de habilidad; se añade Potential/Risk como información de resultado.
- Los mensajes (`message`, `message_success`, `message_failure`) no se han modificado; siguen mostrando los números concretos al jugador al ver el resultado.
- Opciones con efectos complejos o personalizados usan descripciones breves (ej. "Potential: Defuse", "Risk: Reputation if discovered").
