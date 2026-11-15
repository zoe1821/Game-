# LIFEVERSE — Project Status

_Last updated: 2026-11-15 (end of Milestone 1; full development toolchain installed and verified)_

Resumen en español: [`docs/RESUMEN.md`](docs/RESUMEN.md).

## Summary

| | |
|---|---|
| Current milestone | **1 — Research and architecture: complete, awaiting owner review** |
| Next milestone | 2 — Playable life-simulation foundation (not started) |
| Playable build | **None.** No game code exists yet. |
| Engine | Godot 4.7.2 stable (pinned; `tools/install_godot.sh`) |
| 3D authoring tool | Blender 5.3.0 (pinned; `tools/install_blender.sh`) — installed, not yet used for any game asset |
| Export | Templates 4.7.2 + Android SDK installed; Linux / Windows / Web / Android export verified with a trivial project |
| One-command setup | `tools/setup_dev_env.sh --all` (tested from a clean state: 2 min 47 s) |
| Automated tests | None yet (test runner is a Milestone 2 deliverable) |

## What exists and has been verified

| Item | State | How verified |
|---|---|---|
| Environment inspection | Done | Commands run in the dev container; results in `docs/ARCHITECTURE.md` §2 |
| Pinned Godot install script | Working | Ran from a clean state and again (idempotent); `godot --version` → 4.7.2 |
| Headless Godot execution | Working | Spike scripts executed |
| Pinned Blender install script | Working | Ran from a clean state and again (idempotent); `blender --version` → 5.3.0 |
| Blender → glTF → Godot pipeline | Working | Scripted mesh + material + animation exported headless to `.glb`; Godot import reported 1 mesh, material `Wood`, animation `DeskAction`. Cycles CPU render produced a PNG. |
| Export: Linux | Working | Exported binary launched headless and printed the expected check line after a `user://` write/read |
| Export: Web | Working | Loaded in headless Chromium (WebGL 2); same check line seen in the browser console |
| Export: Windows | Produced, **not executed** | Valid PE x86-64 file; no Windows machine here |
| Export: Android | Produced, **not run on a device** | Debug APK; `apksigner verify` OK (v2/v3), `zipalign -c` OK, package/ABIs read back with `aapt` |
| GDScript linter (`gdlint` 4.5.0) | Working | Parsed 4.7 syntax incl. typed dictionaries and reported a real line-length finding |
| `setup_dev_env.sh --all` | Working | Removed every tool, ran it (2 min 47 s), re-ran (1 s, no-op), then repeated all four exports |
| Rendered UI capture (xvfb + OpenGL) | Working | Spike scene rendered and saved to PNG, inspected |
| Technical spikes (JSON typing, RNG persistence, atomic writes, plugin loading, performance, API checks) | Done | Throwaway projects; results recorded in ARCHITECTURE §2. Spike code was intentionally not committed. |
| Architecture document | Written | `docs/ARCHITECTURE.md` |
| Psychiatry module design | Written | `docs/PSYCHIATRY_DESIGN.md` |
| Roadmap and workload estimate | Written | `docs/ROADMAP.md` |
| UI direction (reference analysis, original identity proposal, layouts) | Written — direction only, no screens built | `docs/UI_DIRECTION.md` |
| Dev log, known issues | Started | `docs/DEVLOG.md`, `docs/KNOWN_ISSUES.md` |

## What does not exist yet (everything else)

No part of the game is implemented: no Godot project, no simulation core, no UI, no
save system, no events, no careers, no psychiatry module, no content, no tests, no
exported build. The documents describe intended design only.

Not tested: running the Windows or Android builds, macOS/iOS export, audio,
real-GPU rendering (including Blender EEVEE), touch input, screen readers. Not
installed: Android NDK/CMake (not needed), Wine, any emulator. No 3D assets exist.

## Existing Unity prototype

The repository's Unity project ("Psychiatric Hospital Simulator" V0.2) is untouched.
It was not opened or run (no Unity in this environment), so its working state is
taken from its own README, not verified here.

## Blocking on

Owner review of the architecture and the open decisions in `docs/ROADMAP.md` §7.
Defaults are stated there and will be used where no preference is given.

## Feature status matrix

Legend: ⬜ not started · 🟨 in progress · ✅ implemented and tested

| Area | Status | Milestone |
|---|---|---|
| Simulation core, time, commands | ⬜ | 2 |
| Person model, generation, aging, death | ⬜ | 2 |
| Event engine v1 | ⬜ | 2 |
| Save/load, autosave, determinism | ⬜ | 2 |
| Core UI (menu, creation, dashboard, events, timeline) | ⬜ | 2 |
| Relationships, memories, reputation | ⬜ | 3 |
| Family, marriage, children, succession | ⬜ | 3 |
| NPC agents | ⬜ | 3 / 6 |
| Education and university | ⬜ | 3 |
| Economy | ⬜ | 3 / 4 |
| Storylines and long-term consequences | ⬜ | 3 |
| Career framework | ⬜ | 4 |
| Psychiatry module (clinical ranks, adult) | ⬜ | 5 |
| Psychiatry management ranks and other specializations | ⬜ | 6 |
| Additional careers | ⬜ | 6+ |
| Accessibility, localization, polish | ⬜ | 7 |
| Optional 3D / Blender | ⬜ (tooling verified; content undecided) | 7 |
| Release build | ⬜ | 8 |
