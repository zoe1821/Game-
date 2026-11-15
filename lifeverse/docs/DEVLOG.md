# LIFEVERSE — Development Log

Newest entry first. Each entry records what was done, what was verified and how,
what was decided and why, and what was left undone.

---

## 2026-11-15 — Additional requirements integrated

The project owner supplied ten further mandatory requirement groups (`A1`–`A10`):
daily life, social dialogue, complete professional workflow, expanded hospital
simulation, world simulation, audiovisual immersion, content expansion,
accessibility and languages, production quality, and a completion protocol.

### Done

- Stored both requirement sets verbatim under `docs/requirements/`.
- Spiked the engine mechanisms the new requirements depend on (all passed, results
  in ARCHITECTURE §2): mounting an exported `.pck` and running a script from it;
  capturing errors with a custom `Logger`; CSV translations with live es/en
  switching; a generated tone encoded to Ogg Vorbis and loaded; audio buses;
  runtime input rebinding; presence of the 2D lighting, particle, skeleton and
  interactive-audio classes.
- ARCHITECTURE Part II, §18–§25: daily life (three zoom levels over one
  simulation), conversation engine, world simulation, institution simulation,
  presentation, content packs, player options, production and verification.
  Amended §2, §4, §5.2, §6, §9.4, §9.5 (new), §16.
- PSYCHIATRY_DESIGN §12–§14: hospital operations, privacy and confidentiality
  mechanics, management play and private practice.
- ROADMAP rewritten: depth tiers, module entry gate, playable build in the
  definition of done, sub-milestones 3a/3b/3c, 5a/5b, 6a/6b/6c, revised estimate.
- Made earlier verifications reproducible: `tools/export_smoke_test.sh` and
  `tools/blender_pipeline_test.sh`, each with its small fixture.
- Feature registry: `docs/feature_registry.json` (182 features, each tied to
  requirement ids), `tools/feature_registry.py` (check, render, selftest),
  rendered `docs/FEATURE_REGISTRY.md`.

### Decisions

- **One conversation engine** for social dialogue, job interviews and clinical
  interviews; the `interview` kernel becomes a profile of it and moves to M3.
- **`org` kernel replaced by `institution`**, which runs without the player.
- **Daily life is Tier 2 (systemic) by default**: routines with consequences, any
  day playable by hand. Not a minigame per chore.
- **Spanish and English both complete at every milestone.**
- Only tooling is marked VERIFIED. Windows and Android exports stay TESTED because
  they have never been executed. macOS/iOS export is BLOCKED (no Mac).

### Honest gaps

- No game code. Everything in Part II is design.
- The estimate roughly doubled (≈64k lines, ≈3,400 bilingual content items, ≈57
  sessions); the combined scope exceeds what this roadmap can finish.
- Sound cannot be heard in development; no artist, composer or sound designer.
- `tools/build.sh`, CI and the game's own test runner do not exist yet (M2).

---

## 2026-11-15 — Full development toolchain installed; export pipeline verified

Owner instruction: install everything needed; and "en español".

### Done

- Godot 4.7.2 **export templates** installed (`tools/install_export_templates.sh`,
  SHA-256 pinned).
- **Android SDK** installed (`tools/install_android_sdk.sh`): command-line tools,
  platform-tools, build-tools 35.0.1, platform 35, debug keystore, at Godot's
  default paths. Package list taken from the Godot 4.7 Android export documentation.
- **gdtoolkit 4.5.0** and **jsonschema 4.26.0** (`tools/requirements-dev.txt`).
- `tools/setup_dev_env.sh` (`--all`) runs every installer. Tested by deleting every
  tool and running it: 2 min 47 s; second run 1 s.
- Export smoke test with a trivial portrait (720×1280, Compatibility renderer)
  project that writes and re-reads a `user://` JSON file and prints a check line:
  - Linux: binary launched, check line printed.
  - Web: served locally, loaded in headless Chromium, check line seen in console.
  - Windows: `.exe` produced, PE x86-64 header valid. Not executed.
  - Android: debug APK produced; signature and alignment verified; manifest read
    back (min SDK 24, target SDK 36, arm64-v8a + x86_64). Not run on a device.
- Recorded the language decision: Spanish is the primary authored language of the
  game. Added `RESUMEN.md`, a Spanish summary of status, decisions and plan.

### Findings worth remembering

- A hand-written `export_presets.cfg` must include `include_filter` and
  `exclude_filter` keys or the exporter logs errors (it still exports).
- The Android export logs an error when the project has no icon; the real project
  needs launcher icons before M2's Android build.
- The preinstalled JDK is 21; Godot's docs recommend 17 but accept newer, and the
  export succeeded.
- Web build size is dominated by the 39.5 MB engine `.wasm`.

### Not done / honest gaps

- Windows and Android builds have never been executed. macOS/iOS not attempted.
- Android NDK/CMake not installed (only for custom Gradle builds).
- Release signing for an app store needs the owner's own keystore; only a debug
  key exists, and it is machine-local, not in the repository.
- Export templates and the Android SDK are **not** in the cloud environment's
  automatic setup script (they add ~2.5 GB of downloads to every session start).
  They are installed on demand with `setup_dev_env.sh --all`.
- Technical documents are still in English.

---

## 2026-11-15 — UI reference received; direction recorded

The project owner supplied two BitLife store screenshots (birth/stat screen and the
main life-log screen) as a guide for the menus, to be followed by our own designs
when the interface is built.

### Done

- Wrote `UI_DIRECTION.md`: which structural patterns we learn from the reference,
  what is explicitly not reused (name, logo, colours, avatar style, icons, wording),
  where LIFEVERSE differs because of its design, a proposed original identity, and
  portrait and wide layouts.
- Changed the layout baseline in ARCHITECTURE §12.4 from 1280×720 landscape to
  **portrait-first** with a wide re-flow, and updated open decision 2 in ROADMAP §7.

### Decisions

- Reference = structure and flow. Visual identity = original, validated with real
  screenshots in Milestone 2 before being recorded as settled.
- The reference images are not committed to the repository.

### Not done

- No screens, theme, icons or portraits exist. Nothing visual has been validated.

---

## 2026-11-15 — Blender installed and asset pipeline verified

Requested by the project owner after the Milestone 1 review package.

### Done

- Installed Blender **5.3.0** (current release on download.blender.org) and wrote
  `tools/install_blender.sh`, pinned to the official SHA-256. Tested from a clean
  state and re-run for idempotence.
- Verified the integration instead of assuming it: a headless Blender Python script
  created a mesh with a material and a keyframe animation and exported `.glb`;
  Godot 4.7.2 imported it and reported the mesh, the material by name and the
  animation. A Cycles CPU render to PNG also succeeded.
- Updated ARCHITECTURE §2/§4/§12.5/§14, PROJECT_STATUS, KNOWN_ISSUES, ROADMAP.

### Decisions

- Asset pipeline when 3D is used: `.blend` source → scripted headless export →
  committed `.glb`. Running and testing the game will never require Blender.
- 3D remains optional and scheduled for the Milestone 7 decision point; installing
  the tool does not change the roadmap order.

### Not done / honest gaps

- No 3D asset has been made for the game. The spike files were not committed.
- No GPU in the container: EEVEE and viewport rendering are untested.
- Godot's direct `.blend` import (editor setting pointing at Blender) was not tested;
  the plan does not rely on it.

---

## 2026-11-15 — Milestone 1: research and architecture

### Done

- Inspected the repository and development environment before designing anything.
- Found that the repository already contains a Unity 2022.3 C# prototype
  ("Psychiatric Hospital Simulator" V0.2). Read its README, DESIGN.md, entry point
  and data files. Left it completely untouched; LIFEVERSE lives under `lifeverse/`.
- Determined the current stable Godot from the official download page (4.7.2),
  installed it, and wrote `tools/install_godot.sh` with a pinned SHA-256.
- Ran technical spikes in a scratch directory (not committed):
  1. JSON number fidelity → ints become floats; 64-bit precision lost.
  2. RNG state persistence → corrupt as JSON number, exact as string.
  3. Typed model round-trip through explicit `from_dict`.
  4. Atomic write via rename; ZSTD-compressed file round-trip.
  5. Autoload availability → absent in `--script` mode, present in scene mode.
  6. Rendered Control scene with tween under xvfb/OpenGL → PNG captured and viewed.
  7. Runtime plugin loading from a JSON manifest; typed Callable registries.
  8. Cost of 2,000 NPC records × 80 ticks (38 ms) and serialising them (6 ms).
  9. Engine API presence checks via `ClassDB`/`ProjectSettings` (strict-typing
     warnings, accessibility methods, stretch settings).
- Checked reachability: Godot export templates (reachable, not downloaded), Blender
  downloads (reachable, not installed), third-party GitHub addons (blocked, 403).
- Wrote `ARCHITECTURE.md`, `PSYCHIATRY_DESIGN.md`, `ROADMAP.md`,
  `PROJECT_STATUS.md`, `KNOWN_ISSUES.md`, this log.

### Decisions (rationale in ARCHITECTURE §4)

- Godot 4.7.2 pinned; GDScript with strict typing; Compatibility renderer.
- Simulation core is pure `RefCounted` logic with no autoload/UI dependency.
- JSON content with schema validation; explicit typed serialization; JSON+ZSTD saves
  with atomic writes and migrations; no SQLite for now.
- Zero third-party dependencies; in-repo test runner.
- One `Person` class for player, NPCs and patients; the player is an ID, enabling
  generational continuation.
- Opinions derived from decaying, memory-linked modifiers.
- One condition language and one effect language shared by all data-driven systems.
- Career plugins behind a `CareerModule` contract; auto-resolved shifts run the same
  simulation as played shifts.
- 336-day calendar; Continue-until-interrupt time model.
- 3D/Blender deferred to a Milestone 7 decision point.

### Not done / honest gaps

- No game code, no tests, no build. Milestone 1 was scoped as research and design.
- Research relied on direct tests against the pinned engine rather than a survey of
  external articles; no third-party architecture references were consulted.
- Export pipeline untested. Blender not installed (at the time of this entry; see
  the entry above). Unity prototype not run.
- Workload figures in ROADMAP §1 are estimates, not measurements.

### Next

Milestone 2 after owner review of the architecture and the open decisions in
ROADMAP §7.
