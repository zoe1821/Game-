# Trichon

Ecosistema de análisis capilar personalizado por zonas.

> **Nota sobre este repositorio.** Este directorio es independiente del proyecto
> Unity que vive en la raíz (`Assets/`, `ProjectSettings/`), que no se ha
> modificado. Trichon es un monorepo aparte dentro del mismo repositorio.

## Qué es

Una app que analiza el cabello **zona por zona** (no "tu tipo de rizo"),
aprende de resultados reales, separa lo que sabe la cosmética de lo que sabe de
ti, y te dice qué hacer — y qué no hace falta comprar.

Los cuatro pilares y por qué constituyen una categoría distinta:
[`docs/03-POSITIONING.md`](docs/03-POSITIONING.md).

## Estructura

```
docs/       arquitectura, estrategia, roadmap y progreso
backend/    FastAPI + motor de dominio en Python puro
mobile/     React Native (Expo) + TypeScript
```

## Documentos de Fase 1

| Documento | Qué contiene |
|---|---|
| [`01-ARCHITECTURE.md`](docs/01-ARCHITECTURE.md) | Stack, capas, modelo de datos, pipeline del scanner |
| [`02-MONETIZATION.md`](docs/02-MONETIZATION.md) | Freemium, canal de estilistas, y por qué el motor de producto no toca los ingresos |
| [`03-POSITIONING.md`](docs/03-POSITIONING.md) | Competencia, diferenciación real, copy de producto |
| [`04-LEGAL-CHECKLIST.md`](docs/04-LEGAL-CHECKLIST.md) | **Borrador** legal/regulatorio pendiente de revisión profesional |
| [`08-EVIDENCE-POLICY.md`](docs/08-EVIDENCE-POLICY.md) | Las cuatro etiquetas de evidencia y cómo se aplican |
| [`09-CONTROLLED-LANGUAGE.md`](docs/09-CONTROLLED-LANGUAGE.md) | Glosario controlado (ejecutable, no decorativo) |
| [`00-PROGRESS.md`](docs/00-PROGRESS.md) | Estado entre sesiones |

## Backend en local

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q
```
