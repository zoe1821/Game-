# LIFEVERSE — Project Status

_Last updated: 2026-11-15 (end of Milestone 1; additional requirements integrated)_

Resumen en español: [`docs/RESUMEN.md`](docs/RESUMEN.md).

## Summary

| | |
|---|---|
| Current milestone | **1 — Research, architecture, tooling: complete, awaiting owner review** |
| Next milestone | 2 — Playable foundation and production base (not started) |
| Playable build | **None.** No game code exists yet. |
| Requirements | Original brief (`B1`–`B15`) and additional requirements (`A1`–`A10`), both verbatim in `docs/requirements/` |
| Feature registry | [`docs/FEATURE_REGISTRY.md`](docs/FEATURE_REGISTRY.md) — 182 features: 170 PLANNED, 0 IN DEVELOPMENT, 3 IMPLEMENTED, 2 TESTED, 6 VERIFIED, 1 BLOCKED |
| Engine | Godot 4.7.2 stable (pinned) |
| Toolchain | Blender 5.3.0, export templates, Android SDK, lint tools — one command: `tools/setup_dev_env.sh --all` |
| Game tests | None yet (test runner is a Milestone 2 deliverable) |

Every VERIFIED entry in the registry is a piece of **tooling**. No game feature is
beyond PLANNED.

## What exists and has been verified

Reproducible checks (run them yourself):

| Command | What it proves | Last result |
|---|---|---|
| `tools/setup_dev_env.sh --all` | The whole toolchain installs from pinned downloads | Pass (2 min 47 s from clean; 1 s when present) |
| `tools/export_smoke_test.sh` | Export to Linux (run), Web (run in Chromium), Windows (structure only), Android (signature only) | 4 × PASS |
| `tools/blender_pipeline_test.sh` | Blender → glTF → Godot keeps mesh, material, animation | Pass |
| `tools/feature_registry.py selftest` / `check` | The registry rules are enforced; the registry is valid | Pass |

One-off spikes (throwaway code, not committed; results in `docs/ARCHITECTURE.md` §2):
JSON typing, RNG persistence, atomic writes, autoload availability, runtime plugin
loading, simulation cost, rendered UI capture, expansion-pack mounting, error
capture, live Spanish/English switching, generated audio loading, input rebinding.

Documents: architecture (25 sections), psychiatry and hospital design, UI direction,
roadmap, requirements, dev log, known issues, Spanish summary.

## What does not exist yet

No part of the game is implemented: no Godot game project, simulation, interface,
save system, events, daily life, dialogue, careers, psychiatry, hospital, world
simulation, animation, sound, content, game tests, CI or game build.

Not tested: running the Windows or Android builds, macOS/iOS export, any audio by
ear, real-GPU rendering, touch input, screen readers.

## Existing Unity prototype

Untouched. It was not opened or run (no Unity here), so its working state is taken
from its own README, not verified.

## Blocking on

Owner review of the architecture and the open decisions in `docs/ROADMAP.md` §7.
Defaults are stated there.

## Scope warning

With the additional requirements the estimated work roughly doubled (about 64,000
lines of game code and 3,400 bilingual content items; see `docs/ROADMAP.md` §1). The
combined scope is that of several commercial games. The roadmap delivers a cohesive
subset in verified steps; it does not deliver thirty finished professions.
