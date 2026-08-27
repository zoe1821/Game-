# Arquitectura técnica — Trichon

> Documento vivo. Fase 1. Última actualización: ver `00-PROGRESS.md`.

## 0. Contexto del repositorio

Este repositorio contenía previamente un proyecto Unity (simulador hospitalario)
que **no se elimina ni se modifica**. La aplicación capilar vive de forma
aislada en `hairapp/` como un monorepo independiente:

```
hairapp/
  docs/       documentos estratégicos, arquitectura, roadmap y progreso
  backend/    API Python (FastAPI) + motor de dominio + datos de reglas
  mobile/     app React Native (Expo) TypeScript
```

## 1. Decisiones de stack (y por qué)

| Capa | Elección | Justificación |
|---|---|---|
| Mobile | **React Native + Expo (SDK 51+), TypeScript estricto, expo-router** | Una sola base para iOS/Android; cámara, filesystem, secure-store y notificaciones ya resueltos por el ecosistema Expo; expo-router da deep-linking y navegación tipada por archivos, necesario para "compartir con estilista" (A26) y para enlaces a pantallas de explicabilidad. Alternativa descartada: nativo doble (coste x2 sin ganancia para este producto) y Flutter (equipo/ecosistema de CV en JS/TS más maduro para nuestro caso, y el pipeline pesado corre en backend). |
| Backend | **Python 3.11 + FastAPI + Pydantic v2** | El núcleo del producto es un motor de reglas + análisis numérico + (a futuro) modelos de visión. Python es donde vive ese ecosistema. FastAPI da OpenAPI automático (el cliente TS se genera del schema) y validación estricta. |
| ORM / migraciones | **SQLAlchemy 2.0 (typed) + Alembic** | Modelo de datos amplio y muy relacional (zonas, scans, journal, productos); necesitamos migraciones versionadas desde el día 1. |
| DB | **PostgreSQL 15** (`JSONB`, índices GIN, `pgvector` opcional a futuro) | Datos mixtos: relacional estricto para perfil/inventario/journal, `JSONB` para observaciones de zona y payloads de análisis que evolucionan. SQLite se usa **solo** en tests. |
| Storage | **S3-compatible** (MinIO en dev, S3/R2 en prod) | Fotos nunca en la DB. URLs prefirmadas de corta vida; el backend nunca sirve la imagen directamente. |
| Cache/cola | **Redis** — sí aporta valor | (a) caché del pronóstico climático por celda geográfica (evita pegarle al proveedor por usuario), (b) cola de trabajos del pipeline de scan (análisis asíncrono), (c) rate limiting del asistente conversacional. |
| Auth | Email + contraseña (Argon2id) y OAuth opcional; JWT de acceso corto + refresh rotatorio en `expo-secure-store` | Ver `04-LEGAL-CHECKLIST.md` para consentimientos. |

**Regla de oro de dependencias:** el motor de dominio (`backend/app/domain/`) es
Python puro — sin FastAPI, sin SQLAlchemy, sin red. Se puede testear sin base de
datos y, a futuro, ejecutar dentro del dispositivo vía servidor local o port a TS
sin reescribir la lógica.

## 2. Capas del backend

```
app/
  domain/          <- Python puro. Sin I/O. 100% testeable.
    hair/          zonas, patrones, porosidad, densidad, daño, elasticidad
    evidence/      niveles de evidencia (B4) y lenguaje controlado (B6)
    confidence/    evidence_confidence vs personal_confidence (A21/B4)
    rules/         reglas cosméticas declarativas + cargador + motor
    routine/       generador de rutinas por zona (A8)
    products/      INCI, funciones, matching explicable, análisis de rutina
    twin/          hair digital twin (A24) y proyecciones
    experiments/   diseño y lectura estadística de experimentos (A25)
    climate/       interpretación de clima/dureza de agua (A12)
    learning/      correlaciones del journal + cold start (A13/B2)
  data/            packs de reglas y de ingredientes (YAML/JSON versionados)
  models/          SQLAlchemy
  schemas/         Pydantic (contratos de API)
  services/        orquestación: DB + dominio + storage
  api/v1/          routers HTTP finos
  core/            config, seguridad, errores, i18n
```

La dirección de dependencias es estrictamente `api -> services -> domain`.
`domain` no importa nada de las capas superiores.

## 3. Modelo de datos (resumen; detalle en `06-DATA-MODEL.md`)

Entidades núcleo:

- `User`, `Consent` (uno por propósito, versionado, con timestamp y revocación)
- `HairProfile` (1:1 con user) — nivel de profundidad elegido (B3), completitud
- `ScalpProfile`
- `HairZone` (14 zonas fijas por perfil) — patrón, diámetro, densidad, frizz,
  definición, daño, color, procesamiento, longitud, encogimiento, notas.
  **Cada campo estimado guarda `value`, `confidence`, `source`** (`ai`, `user`,
  `inferred`, `default`), donde `user` siempre gana sobre `ai` (A1.4).
- `ChemicalEvent` / `MechanicalEvent` — historial con fecha y zonas afectadas
- `Scan` -> `ScanPhoto` -> `ScanObservation` (por zona) -> `ScanInterpretation`
- `Goal` (múltiples, priorizados)
- `Routine` -> `RoutineStep` (por zona, con producto, cantidad, técnica, orden)
- `Product`, `Ingredient`, `ProductIngredient` (INCI + posición), `InventoryItem`
- `JournalEntry` -> `JournalResult` (día 1..N)
- `Experiment` -> `ExperimentArm` -> `ExperimentObservation`
- `TwinSnapshot` — estado estructurado del digital twin en el tiempo
- `EvidenceTag` no es tabla: es un enum en el dominio, embebido en cada regla.

Patrón transversal — **valor observado con procedencia**:

```python
Measured[T] = { value: T, confidence: float, source: Source, observed_at: date }
```

Sin ese envoltorio ningún dato estimado entra al sistema. Esto es lo que hace
posible A21 (explicabilidad) sin trabajo extra por pantalla.

## 4. Pipeline del scanner (A3) — modular y con mocks honestos

```
capture -> quality_validation -> segmentation -> zone_mapping ->
feature_extraction -> interpretation -> confidence_calibration ->
user_confirmation -> profile_update
```

Cada etapa es una clase con interfaz explícita y una implementación intercambiable:

| Etapa | Implementación v1 (real) | Estado |
|---|---|---|
| `quality_validation` | Real: varianza del Laplaciano (desenfoque), histograma (exposición), resolución mínima, detección de recorte/oclusión por cobertura. Corre **en el dispositivo** antes de subir. | Real |
| `segmentation` | Máscara de cabello. v1: `MockSegmenter` documentado + hueco para modelo real. | **Mock declarado** |
| `zone_mapping` | Geométrico: mapea la máscara a las 14 zonas por landmarks de cabeza. | Parcial (real geométrico, depende de segmentación) |
| `feature_extraction` | Métricas reales sobre píxeles: frecuencia de curva por autocorrelación, frizz por energía de bordes fuera de la máscara principal, uniformidad. | Real donde hay máscara |
| `interpretation` | Motor de reglas del dominio. Sin red neuronal. | Real |
| `confidence_calibration` | Calibración explícita: la confianza baja con mala calidad de foto, con conflicto entre fuentes y con falta de historial. | Real |
| `user_confirmation` | Obligatorio: nada entra al perfil sin que el usuario confirme o corrija. | Real |

**Compromiso anti-humo (regla crítica del brief):** ninguna etapa devuelve
valores aleatorios. Si un modelo no existe, la etapa devuelve
`Unavailable(reason)` y la app lo comunica ("esto lo estimamos con tus
respuestas, no con la foto"), en vez de inventar un número.

## 5. API

- Versionada: `/api/v1`. OpenAPI genera el cliente TypeScript.
- Errores con forma estable: `{code, message_key, details}` — `message_key` se
  resuelve en el cliente vía i18n (A18): el backend **no** manda texto de UI.
- Toda respuesta de recomendación incluye un bloque `explanation` con:
  `inputs_used`, `observations`, `evidence_level`, `evidence_confidence`,
  `personal_confidence`, `sample_size`, `uncertainty`, `alternatives`.
  Es parte del contrato, no un extra opcional.

## 6. Design system móvil (A19)

Tokens (no valores sueltos): escala tipográfica editorial (serif display +
sans de texto), espaciado 4pt, radios, elevación sutil, y **dos paletas reales**
light/dark definidas por tokens semánticos (`surface`, `surface-raised`,
`ink`, `ink-muted`, `accent`, `line`, `warn`, `positive`), nunca colores crudos
en componentes. Sin gradientes decorativos, sin emojis como iconografía, sin
rosa obligatorio, sin estética de dashboard.

## 7. Estado y datos en el cliente

- **TanStack Query** para todo lo servidor (caché, reintentos, offline-first
  parcial), **Zustand** para estado local de UI/flujos (scan en curso, borrador
  de onboarding), **MMKV/AsyncStorage** para persistencia local.
- El scan funciona sin conexión hasta la subida: fotos y validación de calidad
  son locales.

## 8. i18n (A18)

`i18n-js` + catálogos `es` / `en` desde el primer commit. Cero strings
hardcodeados: hay un test que falla si aparece texto literal en JSX.
El backend manda claves, no frases.

## 9. Seguridad y privacidad (A22)

- Fotos: bucket privado, cifrado en reposo, URLs prefirmadas de 5 min.
- Borrado real de cuenta y de fotos (hard delete + purga de storage), no soft flag.
- Consentimientos separados por propósito. **El consentimiento de entrenamiento
  de modelos es opt-in independiente y su ausencia es el estado por defecto.**
- Opción de recorte de rostro en el dispositivo antes de subir.
- Sin venta de datos; sin SDKs de publicidad de terceros (ver `02-MONETIZATION.md`).

## 10. Separación motor de recomendación / ingresos (requisito B1)

El ranking de productos se calcula en `domain/products/matching.py`, que **no
tiene acceso** a ninguna entidad comercial: ni `partner_id`, ni `commission`, ni
`is_sponsored`. Estos campos ni siquiera existen en el schema del catálogo. Un
test (`test_matching_has_no_commercial_inputs`) falla si aparecen. La
justificación de negocio está en `02-MONETIZATION.md` §4.
