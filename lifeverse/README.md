# LIFEVERSE

An advanced life and career simulation built with Godot 4 and GDScript: live a whole
life, and actually *do* your profession — starting with a deep psychiatry career.

**Status: Milestone 1 (research and architecture) complete, awaiting review.
There is no playable game yet.** See [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Documents

| Document | Contents |
|---|---|
| [`docs/RESUMEN.md`](docs/RESUMEN.md) | **Resumen en español** del estado, las decisiones y el plan |
| [`docs/requirements/`](docs/requirements/) | The original brief and the additional requirements, verbatim |
| [`docs/FEATURE_REGISTRY.md`](docs/FEATURE_REGISTRY.md) | Every feature with its state (PLANNED … VERIFIED) and evidence |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Environment findings, technology decisions, layers, data models, events, careers, saves, UI, testing, risks; Part II: daily life, conversation, world, institutions, presentation, content packs, options, production |
| [`docs/PSYCHIATRY_DESIGN.md`](docs/PSYCHIATRY_DESIGN.md) | Design of the first deep career module |
| [`docs/UI_DIRECTION.md`](docs/UI_DIRECTION.md) | Interface reference, what is and is not taken from it, original visual direction, layouts |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Milestones, acceptance criteria, workload estimate, open decisions |
| [`docs/DEVLOG.md`](docs/DEVLOG.md) | Development log |
| [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) | Known bugs, unverified items, unresolved tasks |

## Engine

Godot **4.7.2 stable**, pinned. On Linux x86_64:

```bash
lifeverse/tools/install_godot.sh     # downloads, checksum-verifies, links `godot`
```

On Windows/macOS, download the same version from <https://godotengine.org/download/archive/>.

Everything else a developer machine needs, in one command:

```bash
lifeverse/tools/setup_dev_env.sh          # core: Godot + lint tools (enough to run and test)
lifeverse/tools/setup_dev_env.sh --all    # + Blender 5.3.0, export templates, Android SDK
```

| Script | Installs | Needed for |
|---|---|---|
| `install_godot.sh` | Godot 4.7.2 editor | running, testing |
| `install_blender.sh` | Blender 5.3.0 (~400 MB) | authoring 3D assets only |
| `install_export_templates.sh` | Godot export templates (~1.2 GB) | producing builds |
| `install_android_sdk.sh` | Android SDK packages + debug keystore (needs a JDK) | Android APKs |
| `requirements-dev.txt` | `gdtoolkit`, `jsonschema` | linting |

Reproducible checks: `tools/export_smoke_test.sh`, `tools/blender_pipeline_test.sh`,
`tools/feature_registry.py check`.

The Godot project will live in `lifeverse/game/` from Milestone 2.

## Relationship to the rest of this repository

The repository root contains an earlier, separate Unity prototype
("Psychiatric Hospital Simulator"). LIFEVERSE does not modify or depend on it; see
`docs/ARCHITECTURE.md` §3.
