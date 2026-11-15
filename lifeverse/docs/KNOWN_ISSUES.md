# LIFEVERSE — Known Issues and Unresolved Tasks

_Last updated: 2026-11-15_

## Bugs

None recorded — there is no game code yet.

## Unverified in the development environment

These cannot be tested in the cloud container used for development and will need
checking on real hardware by the project owner once builds exist.

| ID | Item | Notes |
|---|---|---|
| U-1 | Audio | Container has no audio device (Godot falls back to a dummy driver). Audio files can be generated and loaded, but **nothing can be heard**: every music and sound pass (requirement A6) needs an owner listening test. |
| U-2 | Real-GPU rendering and performance | Only software OpenGL (llvmpipe) is available. Blender is limited to Cycles on CPU here; EEVEE and viewport rendering are untested. |
| U-3 | Touch, gamepad and "feel" of input | Scripted input only. |
| U-4 | Screen-reader behaviour | Accessibility API exists in 4.7.2; behaviour with real assistive tech untested. |
| U-5 | Windows / macOS / Android runtime | Only Linux and Web (Chromium) builds can be launched here. Windows `.exe` and Android APK are produced and structurally verified but never executed. macOS/iOS exports not attempted (signing needs a Mac). |
| U-6 | Existing Unity prototype | Not opened or run; no Unity installation. |

## Unresolved tasks

| ID | Task | Needed by |
|---|---|---|
| T-1 | Owner review of architecture and open decisions (ROADMAP §7) | before M2 |
| T-2 | ~~Export smoke test~~ **Done 2026-11-15** with a trivial project (Linux, Windows, Web, Android). Repeat with the real project. | M2 |
| T-3 | Decide fate of the Unity prototype in this repository | any time |
| T-4 | Decide which build the owner will play on (language decided: Spanish primary) | before M2 UI work |
| T-5 | Name the fictional country, currency and hospital (working names in docs are placeholders for discussion) | M2–M3 |
| T-6 | Continuous integration (run `tools/run_tests.sh` on push) | M2 |
| T-7 | Decide whether to build optional 3D scenes (Blender 5.3.0 is installed and the export pipeline is verified) | M7 decision point |
| T-8 | ~~Android toolchain~~ **Installed 2026-11-15** (debug signing). Still needed for store release: the owner's own release keystore; a device or emulator test | before any public release |

| T-9 | `tools/build.sh`, packaging and CI workflow (requirement A9/A10: playable build per milestone) | M2 |
| T-10 | Decide audio sources: generated + CC0, or owner-supplied/commissioned (ROADMAP §7 #10) | before M3b |
| T-11 | Owner playtests at the end of M2, 3a, 3b, 5a, 6a, 7 | each |

## Design questions still open

| ID | Question |
|---|---|
| Q-1 | How many shifts per month should the player be *invited* to play versus auto-resolve, so careers feel hands-on without stalling a 90-year life? To be tuned with a prototype in M4. |
| Q-2 | How much of an exam is interactive (preparation decisions only, or a knowledge mini-game)? Start with preparation decisions in M3; revisit. |
| Q-3 | Exact Tier A/B population budgets — to be set from soak-test measurements in M3. |
| Q-4 | Which daily-life items, if any, should be Tier 1 interactive scenes rather than Tier 2 routines (ROADMAP §1.2, §7 #5)? |
| Q-5 | How much bilingual dialogue is enough for conversations not to feel repetitive? Needs a measured repetition metric from M3a. |
