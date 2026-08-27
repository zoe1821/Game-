# Progreso — Trichon

Archivo de estado entre sesiones. Se actualiza al cerrar cada bloque de trabajo.

**Última actualización:** 2026-08-27

## Estado por fase

| Fase | Estado | Notas |
|---|---|---|
| 1 — Investigación y arquitectura | ✅ Completa | Los tres documentos estratégicos (B1, B5, B6) + arquitectura, modelo de datos, pipeline, política de evidencia y glosario. |
| 2 — Foundation | ✅ Completa | Dominio, persistencia, API, auth, design system, i18n, cliente. |
| 3 — Experiencia principal | ✅ Completa | Onboarding partido, perfil, mapa de zonas, rutina, scan, inventario, diario, twin, privacidad. |
| 4 — Inteligencia | ✅ Completa | Reglas, confianza doble, matching, cold start, aprendizaje, twin, experimentos. |
| 5 — Polish | 🟡 Parcial | Accesibilidad, dark mode y estados vacío/error/carga hechos. Faltan animaciones y comparación fotográfica. |
| 6 — Validación | ✅ Completa | 149 tests backend + 59 mobile; ruff, mypy, tsc y eslint limpios; smoke test contra servidor real. |

## Contexto del repositorio

El repositorio contenía un proyecto Unity (simulador hospitalario) que **no se
ha tocado**. Trichon vive en `hairapp/` como monorepo aparte.

## Cómo ejecutarlo

```bash
# Backend
cd hairapp/backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q
TRICHON_DATABASE_URL="sqlite:///./dev.db" .venv/bin/python -c \
  "from app.db.base import Base,get_engine; import app.models; Base.metadata.create_all(get_engine())"
TRICHON_DATABASE_URL="sqlite:///./dev.db" .venv/bin/python -m uvicorn app.main:app --reload

# Mobile
cd hairapp/mobile
npm install
npm run typecheck && npm run lint && npm test
npm start
```

## Hecho

**Documentos de Fase 1**: arquitectura, monetización (B1), posicionamiento
(B5), checklist legal borrador (B6), política de evidencia (B4), glosario de
lenguaje controlado, modelo de datos, pipeline del scanner y roadmap.

**Dominio** (`backend/app/domain/`), Python puro verificado por test:
`Measured[T]` con procedencia; mapa de 15 zonas con cobertura honesta;
estimación multi-señal de porosidad, densidad, diámetro y elasticidad;
confianza doble que nunca se promedia; 36 reglas declarativas con etiqueta de
evidencia y mecanismo obligatorios; generador de rutinas por zona; catálogo e
INCI por función; matching con inventario primero; análisis de rutina
completa; clima por punto de rocío; aprendizaje del diario con degradación por
variables confundidas; cold start; digital twin y proyecciones; motor
experimental; pipeline de scan con validación de calidad real y segmentación
declarada como mock.

**Backend**: 19 tablas, migración Alembic verificada, auth Argon2id + JWT
rotatorio, consentimientos por propósito, borrado real que purga el storage,
45 endpoints, y confirmación de transacción **antes** de responder.

**Mobile**: design system por tokens con contraste WCAG verificado por test,
i18n es/en con paridad de claves obligada por tipos y glosario controlado
aplicado a la interfaz, cliente con refresco compartido, y las pantallas de
portada, onboarding, mapa, rutina, scan, inventario, diario, twin, educación y
privacidad.

## Siguiente

1. **Fase 5 restante**: animaciones sobrias respetando `reduceMotion`,
   comparación fotográfica con slider, hair timeline y growth tracker.
2. Reporte exportable para estilista (A26) y su flujo de consentimiento.
3. Asistente conversacional (A20) con contexto acotado, por el coste.
4. Sustituir `MockSegmenter` por un modelo real y recalibrar los umbrales de
   calidad de foto con fotos reales anotadas (ver `07-SCANNER-PIPELINE.md`).
5. v2/v3: banco agregado anónimo de experimentos (B7) y Trichon Pro.

## Bloqueantes antes de cualquier lanzamiento

Están en `04-LEGAL-CHECKLIST.md` §8 y ninguno es negociable. El principal:
**ese documento es un borrador generado con asistencia de IA y necesita
revisión de un profesional legal real.**

## Decisiones tomadas (no volver a discutir sin motivo nuevo)

- El dominio no importa infraestructura. Verificado por test.
- El motor de matching de producto no puede acceder a datos comerciales.
  Verificado por test que inspecciona el AST del módulo.
- Ninguna estimación entra al perfil sin confirmación de la persona usuaria, y
  una corrección manual no se sobrescribe nunca.
- Sin señales, el sistema dice que no sabe en vez de devolver un valor por
  defecto. Aplica a porosidad, dureza del agua, rasgos del twin y proyecciones.
- El mock de segmentación se declara como mock y degrada de forma visible.
- Las dos confianzas se muestran por separado y jamás se promedian.
