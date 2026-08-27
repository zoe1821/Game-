# Progreso — Trichon

Archivo de estado entre sesiones. Se actualiza al cerrar cada bloque de trabajo.

**Última actualización:** 2026-08-27

## Estado por fase

| Fase | Estado | Notas |
|---|---|---|
| 1 — Investigación y arquitectura | ✅ Completa | Los tres documentos estratégicos entregados (B1, B5, B6) + arquitectura, modelo de datos, pipeline y roadmap. |
| 2 — Foundation | 🟡 En curso | Dominio puro completo y testeado. Falta persistencia, API y app móvil. |
| 3 — Experiencia principal | ⬜ Pendiente | |
| 4 — Inteligencia | 🟡 En curso | Motor de reglas, confianza doble y generador de rutinas ya funcionan. Falta producto/inventario, cold start, twin y experimentos. |
| 5 — Polish | ⬜ Pendiente | |
| 6 — Validación | 🟡 Parcial | 55 tests del dominio en verde. |

## Contexto del repositorio

El repositorio contenía un proyecto Unity (simulador hospitalario) que **no se
ha tocado**. Trichon vive en `hairapp/` como monorepo aparte.

## Hecho

- **Documentos de Fase 1**: arquitectura, monetización (B1), posicionamiento
  (B5), checklist legal borrador (B6), política de evidencia (B4), glosario de
  lenguaje controlado, modelo de datos, pipeline del scanner, roadmap.
- **Dominio puro** (`backend/app/domain/`), sin dependencias de red ni de DB:
  - `Measured[T]` con procedencia y techos de confianza por fuente. La
    corrección manual gana siempre (A1.4).
  - Mapa de 15 zonas con cobertura honesta por ángulo de foto.
  - Vocabulario capilar completo; curl typing tratado como descriptivo.
  - Estimación multi-señal de porosidad, densidad, diámetro y elasticidad,
    con penalización real por conflicto entre señales y sin `float test`.
  - Sistema de confianza doble: `evidence_confidence` y `personal_confidence`
    nunca se promedian; el tamaño de muestra siempre viaja.
  - Glosario de lenguaje controlado **ejecutable** con test que falla el build.
  - Packs de reglas declarativos (36 reglas) con etiqueta de evidencia y
    mecanismo obligatorios; el loader rechaza reglas sin ellos y rechaza que un
    método de marca sea la única fuente.
  - Motor de reglas con resolución determinista de conflictos y parada total
    ante señales de derivación (A23).
  - Cantidades inteligentes con referencia visual (A10).
  - Biblioteca de técnicas con nivel de evidencia y temporizadores (A9).
  - Generador de rutinas **por zona** (A8) con explicación completa por paso,
    temperatura por estado de la fibra, y modos rápidos que declaran qué omiten.

## Siguiente

1. Catálogo de productos e ingredientes + matching explicable con inventario
   primero (A11, A15) y test de separación comercial (B1 §4).
2. Clima y dureza del agua (A12), aprendizaje del journal y cold start (B2).
3. Hair Digital Twin (A24) y motor experimental (A25).
4. Pipeline del scanner con validación de calidad real y mock declarado.
5. Persistencia (SQLAlchemy + Alembic), API FastAPI, auth.
6. App móvil Expo: design system, i18n, navegación, pantallas.

## Decisiones tomadas (no volver a discutir sin motivo nuevo)

- El dominio no importa FastAPI ni SQLAlchemy. Verificado por test.
- El motor de matching de producto no puede acceder a datos comerciales.
- Ninguna estimación entra al perfil sin confirmación de la persona usuaria.
- Sin señales, el sistema dice que no sabe en vez de devolver un valor por defecto.
- El mock de segmentación se declara como mock y degrada de forma visible.
