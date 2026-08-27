# Roadmap técnico — Trichon

Cada fase deja el proyecto **ejecutable**: backend arranca, tests pasan,
app compila.

## Fase 1 — Investigación y arquitectura ✅
- Inspección del repositorio existente (proyecto Unity preservado sin cambios).
- `01-ARCHITECTURE.md`, `02-MONETIZATION.md` (B1), `03-POSITIONING.md` (B5),
  `04-LEGAL-CHECKLIST.md` (B6), `06-DATA-MODEL.md`, `07-SCANNER-PIPELINE.md`,
  `08-EVIDENCE-POLICY.md` (B4), `09-CONTROLLED-LANGUAGE.md`, este roadmap y
  `00-PROGRESS.md`.

## Fase 2 — Foundation
- Backend: config, errores con `message_key`, modelos SQLAlchemy completos,
  Alembic, auth (Argon2id + JWT), abstracción de storage, i18n de claves.
- Dominio base: `Measured[T]`, fuentes, niveles de evidencia, motor de confianza,
  cargador de packs de reglas con validación estricta, glosario controlado ejecutable.
- Mobile: Expo + TS estricto, expo-router, design system por tokens, i18n es/en,
  TanStack Query + Zustand, cliente API generado del OpenAPI.

## Fase 3 — Experiencia principal
- Onboarding partido: **esencial (<3 min)** + profundización opcional por
  secciones con indicador de completitud (B3).
- Perfil capilar, mapa de 14 zonas editable, objetivos priorizados.
- Flujo de scan con validación de calidad en dispositivo y confirmación del usuario.
- Dashboard, generador de rutina, instrucciones por zona, inventario, journal.

## Fase 4 — Inteligencia
- Motor de reglas con `evidence_confidence` + `personal_confidence` y tamaño de
  muestra (A21/B4).
- Porosidad/densidad/diámetro/elasticidad estimadas multi-señal.
- Matching de producto explicable **con inventario primero** (A15).
- Análisis de rutina completa: redundancia, exceso de proteína, buildup probable.
- Cold start (B2): consenso general + perfiles de referencia etiquetados.
- Aprendizaje del journal: correlación ≠ causalidad, tamaño de muestra visible.
- Hair Digital Twin (A24) y motor experimental (A25).

## Fase 5 — Polish
- Animaciones sobrias, accesibilidad (tamaños, contraste, screen reader,
  reduced motion), dark mode real, responsive, estados vacío/error/carga.

## Fase 6 — Validación
- `ruff`, `mypy`, `pytest` (backend); `tsc`, `eslint`, `jest` (mobile).
- Tests de invariantes de producto: separación comercial del matching,
  glosario controlado, ausencia de strings hardcodeados.

## v2 / v3 (fuera de alcance de esta entrega, diseñado)
- B7: compartir experimentos de forma anónima y banco agregado por perfil,
  con consentimiento separado. Sin feed social, sin comparación pública, sin
  gamificación competitiva.
- Modelo de segmentación real que sustituya el `MockSegmenter` documentado.
- Trichon Pro (canal de estilistas).
