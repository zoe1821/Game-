# Pipeline del scanner — qué es real y qué es mock

> Regla crítica del proyecto: **no fingir que un modelo de visión existe si no
> existe.** Este documento es el registro honesto de qué hace cada etapa hoy.

## Etapas

### 1. `quality_validation` — REAL
Corre en el dispositivo antes de subir y se re-verifica en backend.
- **Desenfoque**: varianza del Laplaciano sobre la imagen en escala de grises.
  Umbral calibrado por resolución.
- **Exposición**: fracción de píxeles saturados y análisis de histograma;
  detecta subexposición y quemado.
- **Resolución mínima**: lado corto ≥ 720 px.
- **Oclusión / encuadre**: fracción de la imagen cubierta por la región de interés.
- **Filtros / postprocesado**: detección de saturación anómala y de perfiles de
  color no naturales. Es una heurística; se declara como tal y solo advierte.

Salida: un `PhotoQualityReport` por foto con causas concretas. La app pide
repetir **solo** las fotos deficientes (A3), nunca todo el set.

### 2. `segmentation` — **MOCK DECLARADO**
Necesita un modelo de segmentación de cabello entrenado, que **no existe en este
repositorio**. La implementación actual (`MockSegmenter`) devuelve
`Unavailable(reason="no_segmentation_model")`.

Consecuencia real, no disimulada: sin máscara, las etapas 3 y 4 no producen
métricas de imagen. El sistema **no inventa valores**: cae a la ruta
"estimación a partir de tus respuestas" y la app lo dice explícitamente
("esto no lo estimamos con la foto"). La confianza se calcula en consecuencia.

Interfaz lista para sustituir por un modelo real sin tocar el resto del pipeline.

### 3. `zone_mapping` — REAL (geométrico), dependiente de la etapa 2
Mapea la máscara de cabello a las 14 zonas usando el ángulo declarado de la foto
y landmarks de cabeza. Sin máscara, no se ejecuta.

### 4. `feature_extraction` — REAL sobre píxeles
Cuando hay máscara, se calculan métricas reales, no clasificaciones:
- **frecuencia de curva**: autocorrelación 1-D sobre perfiles de intensidad a lo
  largo de la hebra → periodo dominante.
- **frizz**: energía de bordes fuera del cuerpo principal de la máscara,
  normalizada por perímetro.
- **uniformidad / clumping**: dispersión de los periodos detectados y tamaño de
  los agregados conectados.
- **definición**: contraste local dentro de la máscara.

Estas métricas son más útiles que el curl typing solo (A5) y son las que
alimentan la interpretación.

### 5. `interpretation` — REAL
Motor de reglas del dominio. Combina métricas de imagen (si existen), respuestas
del usuario e historial químico/mecánico. Produce `Measured` por zona.

### 6. `confidence_calibration` — REAL
La confianza **baja** explícitamente por: mala calidad de foto, ausencia de
métricas de imagen, conflicto entre señales, historial escaso, y antigüedad de
la observación. Nunca sube por encima del techo de su fuente.

### 7. `user_confirmation` — REAL y obligatoria
Ninguna estimación entra al perfil sin que el usuario la confirme o corrija.
La corrección se guarda con `source = USER` y es definitiva.

### 8. `profile_update` — REAL
Escribe en `hair_zones` conservando el histórico de estimaciones previas.
