# LIFEVERSE — Development Log

Newest entry first. Each entry records what was done, what was verified and how,
what was decided and why, and what was left undone.

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
