# Política de evidencia (requisito B4)

## 1. Las cuatro etiquetas

Toda regla del motor y todo contenido educativo lleva **exactamente una** de estas
etiquetas. Es un campo obligatorio: una regla sin etiqueta no carga (el cargador
lanza error, no toma un valor por defecto).

| Etiqueta | Significado | Cómo se muestra al usuario |
|---|---|---|
| `SCIENTIFIC_EVIDENCE` | Respaldada por literatura revisada por pares sobre la fibra capilar, el cuero cabelludo o la formulación cosmética. | "Evidencia científica" |
| `PROFESSIONAL_CONSENSUS` | Amplio acuerdo entre fuentes formativas profesionales y de ciencia cosmética, sin un cuerpo experimental cerrado. | "Consenso profesional" |
| `EXTENDED_ANECDOTE` | Práctica muy extendida con resultados reportados consistentes, pero sin respaldo controlado. Puede funcionar para muchas personas y no para otras. | "Experiencia extendida" |
| `UNSUPPORTED_TREND` | Circula ampliamente y **no** se sostiene. Solo aparece en el detector de mitos, nunca como recomendación. | "Mito frecuente" |

## 2. Cómo se traduce a confianza

`evidence_confidence` deriva de la etiqueta, no se escribe a mano:

```
SCIENTIFIC_EVIDENCE   -> 0.90
PROFESSIONAL_CONSENSUS-> 0.70
EXTENDED_ANECDOTE     -> 0.45
UNSUPPORTED_TREND     -> 0.00  (nunca recomienda)
```

`personal_confidence` es independiente y se calcula del historial del usuario:
cuántas observaciones propias respaldan la regla, con qué consistencia y qué tan
recientes son. **Siempre acompañada del tamaño de muestra.**

Las dos **nunca se promedian en un solo número**. La UI muestra ambas. Un
promedio escondería exactamente la distinción que el producto existe para hacer.

## 3. Fuentes de consenso usadas (y la trampa a evitar)

Familias de fuentes que consideramos aceptables para `PROFESSIONAL_CONSENSUS`:

- Literatura de ciencia cosmética sobre tensioactivos, acondicionamiento
  catiónico, siliconas, humectantes y polímeros de fijación.
- Trabajo publicado sobre propiedades mecánicas de la fibra: hinchamiento
  higral, fatiga por peinado en húmedo, efecto de la temperatura.
- Documentación formativa profesional de peluquería y de cabello texturizado.
- Dermatología cosmética **solo** para el límite de derivación (qué NO es
  cosmético), nunca para diagnosticar.

**La trampa explícita:** no copiar un método único como verdad universal. El
Curly Girl Method es el caso más frecuente. Sus reglas ("nunca sulfatos", "nunca
siliconas", "nunca calor") se citan como ley y **no lo son**: dependen del tipo
de silicona (soluble o no), del tensioactivo concreto, de la porosidad y de la
rutina de lavado completa. En nuestro sistema:

- Cada afirmación de ese tipo se descompone en la regla real subyacente
  (p. ej. "las siliconas no solubles pueden acumularse si no se usa un
  tensioactivo capaz de retirarlas" — `PROFESSIONAL_CONSENSUS`), en vez de la
  prohibición absoluta (`UNSUPPORTED_TREND` como regla universal).
- Ninguna regla puede citar un método de marca o de autor como su única fuente.
  El campo `sources` de cada regla debe nombrar el mecanismo, no el método.

## 4. Obligación de procedimiento

Antes de implementar una regla cosmética con impacto en la rutina:
1. Se escribe en el pack de reglas con su etiqueta y su campo `mechanism`
   (por qué físicamente/químicamente ocurre).
2. Si no se puede escribir el mecanismo, la etiqueta máxima posible es
   `EXTENDED_ANECDOTE`.
3. Si la regla contradice otra ya existente, se resuelve explícitamente por
   condiciones (porosidad, daño, clima), no por prioridad arbitraria.
