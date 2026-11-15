# LIFEVERSE — Known Issues and Unresolved Tasks

_Last updated: 2026-11-15_

## Bugs

None recorded — there is no game code yet.

## Unverified in the development environment

These cannot be tested in the cloud container used for development and will need
checking on real hardware by the project owner once builds exist.

| ID | Item | Notes |
|---|---|---|
| U-1 | Audio | Container has no audio device (Godot falls back to a dummy driver). |
| U-2 | Real-GPU rendering and performance | Only software OpenGL (llvmpipe) is available. |
| U-3 | Touch, gamepad and "feel" of input | Scripted input only. |
| U-4 | Screen-reader behaviour | Accessibility API exists in 4.7.2; behaviour with real assistive tech untested. |
| U-5 | Windows / macOS / Android runtime | Only Linux can be launched here. |
| U-6 | Existing Unity prototype | Not opened or run; no Unity installation. |

## Unresolved tasks

| ID | Task | Needed by |
|---|---|---|
| T-1 | Owner review of architecture and open decisions (ROADMAP §7) | before M2 |
| T-2 | Export smoke test (templates ~1 GB download, export a trivial project, launch it) | M2 |
| T-3 | Decide fate of the Unity prototype in this repository | any time |
| T-4 | Decide target platforms and languages | before M2 UI work |
| T-5 | Name the fictional country, currency and hospital (working names in docs are placeholders for discussion) | M2–M3 |
| T-6 | Continuous integration (run `tools/run_tests.sh` on push) | M2 |
| T-7 | Blender installation and 3D decision | M7 decision point |
| T-8 | Android toolchain (SDK, signing) if Android is a target | when confirmed |

## Design questions still open

| ID | Question |
|---|---|
| Q-1 | How many shifts per month should the player be *invited* to play versus auto-resolve, so careers feel hands-on without stalling a 90-year life? To be tuned with a prototype in M4. |
| Q-2 | How much of an exam is interactive (preparation decisions only, or a knowledge mini-game)? Start with preparation decisions in M3; revisit. |
| Q-3 | Exact Tier A/B population budgets — to be set from soak-test measurements in M3. |
