# Progreso — Trichon

Archivo de estado entre sesiones. Se actualiza al cerrar cada bloque de trabajo.

**Última actualización:** 2026-08-27 (segunda sesión)

## Estado por fase

| Fase | Estado | Notas |
|---|---|---|
| 1 — Investigación y arquitectura | ✅ Completa | Los tres documentos estratégicos (B1, B5, B6) + arquitectura, modelo de datos, pipeline, política de evidencia y glosario. |
| 2 — Foundation | ✅ Completa | Dominio, persistencia, API, auth, design system, i18n, cliente. |
| 3 — Experiencia principal | ✅ Completa | Onboarding partido, perfil, mapa de zonas, rutina, scan, inventario, diario, twin, privacidad. |
| 4 — Inteligencia | ✅ Completa | Reglas, confianza doble, matching, cold start, aprendizaje, twin, experimentos. |
| 5 — Polish | 🟡 Parcial | Accesibilidad, dark mode y estados vacío/error/carga hechos. Faltan animaciones y comparación fotográfica. |
| 6 — Validación | ✅ Completa | 174 tests backend + 59 mobile; ruff, mypy, tsc y eslint limpios; smoke test contra servidor real. |
| Monetización | ✅ Implementada | Derechos de uso, cupo, suscripción, verificación de recibo en servidor y precio por país. Faltan las credenciales de tienda. |
| LATAM | 🟡 En curso | Cronograma capilar, catálogo semilla y legal reenfocado. Falta portugués para Brasil. |

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

## Alcance de lanzamiento (decidido)

**LATAM con México como mercado principal, más EE. UU.** Consecuencias que ya
están reflejadas en el código y los documentos:

- El riesgo legal principal pasa a ser **BIPA (Illinois)** y las leyes de
  privacidad biométrica de EE. UU. con acción privada. Ver
  `04-LEGAL-CHECKLIST.md` §3.4.
- México exige aviso de privacidad propio bajo la LFPDPPP, no una traducción
  del europeo.
- El **cronograma capilar** es el vocabulario dominante en la región y ya es
  un concepto de primera clase del motor.
- Si se entra en Brasil hace falta portugués. La arquitectura i18n lo soporta;
  el catálogo no existe todavía.

## Calibración con fotos reales

Con 35 fotos reales se encontró y corrigió un fallo que rechazaba 16 de ellas.
La varianza del Laplaciano no es invariante a la escala y se medía sobre el
fotograma entero. Ahora se mide a resolución fija y por regiones. Rechazo
actual: 7 de 35, casi todas de baja resolución real.

Se descartó, con datos, la sospecha de sesgo por cabello oscuro: correlación
con la luminancia +0.01.

**Pendiente:** los umbrales están calibrados contra 35 fotos, que es poco. Con
unos cientos etiquetados como buena/mala se podrían ajustar bien.

## Siguiente

0. **Configurar credenciales de App Store y Google Play.** El código de
   verificación está y falla cerrado; sin las claves nadie puede activar una
   suscripción. `GET /billing/verification-status` dice exactamente qué falta.
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
